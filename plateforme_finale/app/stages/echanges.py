"""
Échanges de fichiers avec WebAurion et Moodle (Lot 4).

WebAurion et Moodle n'ont pas d'API : on échange par fichiers CSV (voir csv_outils.py).
- importer_webaurion : crée les comptes et les inscriptions à partir d'une liste exportée de WebAurion (US-08)
- exporter_conventions_signees : fichier à importer dans WebAurion (US-07)
- importer_moodle : marque « rendus » les livrables remis sur Moodle

Les colonnes exactes des fichiers du Career Center ne sont pas connues : les formats ci-dessous sont
des HYPOTHÈSES (voir docs/08-Decisions-ouvertes.md), écrites pour être faciles à adapter.
"""

import io
import os
import re
import secrets
import zipfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from comptes import roles

from .csv_outils import ErreurCSV, ecrire_csv, lire_csv, normaliser, trouver_colonne
from .models import Convention, Inscription, Livrable, Promotion
from .services import marquer_rendu


class Rapport:
    """Compte rendu d'un import, affiché au Career Center."""

    def __init__(self, simulation):
        self.simulation = simulation   # vrai : rien n'a été enregistré, on a seulement vérifié
        self.faits = []                # (ligne, texte) : ce qui a été fait (ou le serait, en simulation)
        self.ignorees = []             # (ligne, texte) : lignes sans effet, sans que ce soit une erreur
        self.erreurs = []              # (ligne, texte) : lignes refusées
        self.comptes = []              # (e-mail, nom, mot de passe provisoire) des comptes créés

    @property
    def nb_total(self):
        return len(self.faits) + len(self.ignorees) + len(self.erreurs)


class ErreurLigne(Exception):
    """Une ligne du fichier est refusée (le message dit pourquoi) ; les autres continuent."""


# ---------------------------------------------------------------------------
# Import des étudiants et encadrants depuis WebAurion (US-08)
# ---------------------------------------------------------------------------

# Code de groupe WebAurion, ex. « INGE_4_FISE_CA_2627_S7 » : 4e année, cursus FISE, campus Casablanca,
# année universitaire 2026-2027. Les suffixes (_S7, _TDA…) sont ignorés.
MOTIF_GROUPE = re.compile(r"INGE[_ ](\d)[_ ][A-Z]+[_ ]CA[_ ](\d{2})(\d{2})", re.IGNORECASE)

ROLES_IMPORTABLES = {"": roles.ETUDIANT, "etudiant": roles.ETUDIANT, "eleve": roles.ETUDIANT,
                     "encadrant": roles.ENCADRANT}


def promotion_depuis_groupe(texte):
    """Année d'études et année universitaire lues dans un ou plusieurs codes de groupe.
    Renvoie (4, "2026-2027"), ou None si aucun code reconnu."""
    for annee_etudes, debut, fin in MOTIF_GROUPE.findall(texte or ""):
        debut, fin = int(debut), int(fin)
        if 1 <= int(annee_etudes) <= 5 and fin == debut + 1:
            return int(annee_etudes), f"20{debut:02d}-20{fin:02d}"
    return None


def importer_webaurion(contenu, simuler=False):
    """Importe une liste d'étudiants (et d'encadrants) exportée de WebAurion.

    Colonnes reconnues (peu importent les majuscules et les accents) :
      Nom ; Prénom ; E-mail (ou Mail, Courriel) ; Code.Groupe (étudiants : donne l'année d'études et
      l'année universitaire) ; Rôle (facultatif : « Étudiant » par défaut, ou « Encadrant »).

    - un compte qui existe déjà n'est jamais recréé ni modifié (pas de doublon) ;
    - un étudiant déjà inscrit cette année dans la même promotion est ignoré ;
    - chaque ligne est traitée seule : une ligne en erreur n'empêche pas les autres ;
    - `simuler=True` fait tout le travail puis annule : on voit le rapport sans rien enregistrer.
    Lève ErreurCSV si le fichier est inexploitable."""
    en_tetes, lignes = lire_csv(contenu)
    col_nom = trouver_colonne(en_tetes, exacts=("nom", "nom de famille"))
    col_prenom = trouver_colonne(en_tetes, exacts=("prenom",))
    col_email = trouver_colonne(en_tetes, contient=("mail", "courriel"))
    col_groupe = trouver_colonne(en_tetes, contient=("groupe",))
    col_role = trouver_colonne(en_tetes, exacts=("role", "profil"))
    manquantes = [nom for nom, col in (("Nom", col_nom), ("Prénom", col_prenom), ("E-mail", col_email)) if not col]
    if manquantes:
        raise ErreurCSV("Colonne(s) introuvable(s) : " + ", ".join(manquantes)
                        + ". Titres attendus : Nom, Prénom, E-mail, Code.Groupe, Rôle (facultatif).")

    rapport = Rapport(simulation=simuler)
    deja_vus = {}
    with transaction.atomic():
        for numero, d in lignes:
            email = d.get(col_email, "").lower()
            if email in deja_vus:
                rapport.ignorees.append((numero, f"{email} : déjà traité à la ligne {deja_vus[email]}."))
                continue
            deja_vus[email] = numero
            try:
                with transaction.atomic():  # si cette ligne échoue, ses changements sont annulés seuls
                    _traiter_ligne(d, email, col_nom, col_prenom, col_groupe, col_role, numero, rapport)
            except ErreurLigne as erreur:
                rapport.erreurs.append((numero, f"{email or '(sans e-mail)'} : {erreur}"))
        if simuler:
            transaction.set_rollback(True)
    return rapport


def _traiter_ligne(d, email, col_nom, col_prenom, col_groupe, col_role, numero, rapport):
    try:
        validate_email(email)
    except ValidationError:
        raise ErreurLigne("adresse e-mail absente ou invalide.")

    role = ROLES_IMPORTABLES.get(normaliser(d.get(col_role, "")) if col_role else "")
    if role is None:
        raise ErreurLigne(f"rôle inconnu « {d.get(col_role)} » (attendu : Étudiant ou Encadrant).")

    promotion_lue = None
    if role == roles.ETUDIANT:
        promotion_lue = promotion_depuis_groupe(d.get(col_groupe, "") if col_groupe else "")
        if promotion_lue is None:
            raise ErreurLigne("code de groupe absent ou non reconnu (attendu : INGE_4_FISE_CA_2627…).")

    Utilisateur = get_user_model()
    compte = Utilisateur.objects.filter(email__iexact=email).first()
    actions = []
    if compte is None:
        nom, prenom = d.get(col_nom, ""), d.get(col_prenom, "")
        if not nom or not prenom:
            raise ErreurLigne("nom ou prénom manquant.")
        mot_de_passe = secrets.token_urlsafe(9)  # provisoire, affiché une seule fois au Career Center
        compte = Utilisateur.objects.create_user(email, mot_de_passe, first_name=prenom, last_name=nom)
        rapport.comptes.append((email, f"{prenom} {nom}", mot_de_passe))
        actions.append("compte créé")

    if not compte.a_le_role(role):
        compte.groups.add(Group.objects.get(name=role))
        if not actions:  # pour un compte tout juste créé, « compte créé » suffit
            actions.append(f"rôle « {role} » ajouté")

    if promotion_lue is not None:
        annee_etudes, annee_univ = promotion_lue
        existante = Inscription.objects.filter(etudiant=compte, annee_universitaire=annee_univ).select_related("promotion").first()
        if existante and existante.promotion.annee_etudes != annee_etudes:
            raise ErreurLigne(f"déjà inscrit en {existante.promotion} (groupe du fichier : {annee_etudes}e année).")
        if existante is None:
            promotion, _ = Promotion.objects.get_or_create(annee_etudes=annee_etudes, annee_universitaire=annee_univ)
            Inscription.objects.create(etudiant=compte, promotion=promotion)
            actions.append(f"inscrit en {promotion}")

    if actions:
        rapport.faits.append((numero, f"{email} : " + ", ".join(actions) + "."))
    else:
        rapport.ignorees.append((numero, f"{email} : existe déjà, rien à faire."))


# ---------------------------------------------------------------------------
# Export des conventions signées vers WebAurion (US-07)
# ---------------------------------------------------------------------------

# Colonnes du suivi des stages de WebAurion (relevées sur l'écran « Suivre la validation de mes demandes
# d'expériences professionnelles »), précédées de l'identité de l'étudiant et du n° de convention, qui
# permettent de rattacher chaque ligne à la bonne personne.
COLONNES_CONVENTIONS = [
    "Nom", "Prénom", "E-mail", "N° convention",
    "Début", "Fin", "Libellé.Type de stage", "Entreprise", "Sujet de stage", "Sujet du stage (en anglais)",
    "Complement d'information ou motif de refus entreprise.Stage", "Validation service entreprise",
    "Complement d'information ou motif de refus mission.Stage", "Validation pédagogique",
    "Validation du Stage", "Convention validée reçue le",
]

# Type de stage de la plateforme -> libellé WebAurion. « Stage Ouvrier » (1re année) et « Stage Technicien »
# (3e année) ont été relevés dans WebAurion ; les trois autres sont des HYPOTHÈSES à confirmer.
LIBELLE_WEBAURION = {
    "Découverte": "Stage Ouvrier",
    "Initiative personnelle": "Stage Initiative Personnelle",
    "Technicien": "Stage Technicien",
    "Assistant-Ingénieur": "Stage Assistant Ingénieur",
    "Fin d'Études": "Stage Fin d'Etudes",
}


def _date(jour):
    return f"{jour:%d/%m/%Y}" if jour else ""


def exporter_conventions_signees(annee):
    """CSV des conventions signées par toutes les parties pour une année universitaire (« 2026-2027 »).

    Une ligne par stage, au format du suivi des stages de WebAurion. « Validation service entreprise » et
    « Validation pédagogique » valent « Validé » (c'est une condition pour être signée) ; « Validation du
    Stage » reste vide : l'école la donne après le stage. Renvoie (octets du CSV, nombre de lignes)."""
    conventions = (
        Convention.objects.filter(statut=Convention.Statut.SIGNEE, stage__promotion__annee_universitaire=annee)
        .select_related("stage__etudiant", "stage__entreprise", "stage__promotion")
        .order_by("numero")
    )
    lignes = []
    for c in conventions:
        stage, etudiant = c.stage, c.stage.etudiant
        lignes.append([
            etudiant.last_name, etudiant.first_name, etudiant.email, c.numero,
            _date(stage.date_debut), _date(stage.date_fin),
            LIBELLE_WEBAURION.get(stage.type_stage, stage.type_stage),
            stage.entreprise.raison_sociale if stage.entreprise else "",
            " ".join(stage.sujet.split()),  # pas de retour à la ligne dans une cellule
            "", "", "Validé", "", "Validé", "", _date(c.signee_le),
        ])
    return ecrire_csv(COLONNES_CONVENTIONS, lignes), len(lignes)


# ---------------------------------------------------------------------------
# Import de l'état des rendus depuis Moodle
# ---------------------------------------------------------------------------

def _est_remis(statut):
    """Vrai si le statut Moodle d'un devoir veut dire « rendu » : « Remis pour évaluation » (français)
    ou « Submitted for grading » (anglais). « Brouillon (non remis) » et « Aucun travail remis »
    ne comptent pas. HYPOTHÈSE sur le libellé exact utilisé par le Moodle de l'école."""
    statut = normaliser(statut)
    return statut.startswith("remis") or statut.startswith("submitted")


def importer_moodle(contenu, nom_livrable, par, simuler=False):
    """Marque « rendus » les livrables déposés sur Moodle, d'après l'export d'un devoir Moodle.

    `nom_livrable` est le livrable de la plateforme auquel le devoir correspond (ex. « Rapport de
    stage »). Le fichier doit contenir une colonne d'adresse e-mail (« Adresse de courriel ») et une
    colonne « Statut ». Chaque étudiant est retrouvé par son e-mail ; ceux dont le livrable est déjà
    « rendu », qui n'ont rien remis, ou qui sont inconnus sont comptés « sans effet ».
    `simuler=True` montre le résultat sans rien enregistrer. Lève ErreurCSV si le fichier est inexploitable."""
    en_tetes, lignes = lire_csv(contenu)
    col_email = trouver_colonne(en_tetes, contient=("mail", "courriel"))
    col_statut = trouver_colonne(en_tetes, exacts=("statut", "status", "etat"))
    if not col_email or not col_statut:
        raise ErreurCSV("Colonnes introuvables : il faut une adresse e-mail (« Adresse de courriel ») et un « Statut ».")

    # Le livrable de chaque étudiant (le plus récent s'il en a eu plusieurs, d'une année à l'autre)
    par_email = {}
    for livrable in Livrable.objects.filter(nom=nom_livrable).select_related("stage__etudiant").order_by(
            "stage__promotion__annee_universitaire"):
        par_email[livrable.stage.etudiant.email.lower()] = livrable

    rapport = Rapport(simulation=simuler)
    with transaction.atomic():
        for numero, d in lignes:
            email = d.get(col_email, "").lower()
            statut = d.get(col_statut, "")
            livrable = par_email.get(email)
            if livrable is None:
                rapport.ignorees.append((numero, f"{email or '(sans e-mail)'} : aucun livrable « {nom_livrable} » pour cet e-mail."))
            elif not _est_remis(statut):
                rapport.ignorees.append((numero, f"{email} : pas remis sur Moodle (statut : {statut or 'vide'})."))
            elif livrable.statut == Livrable.Statut.RENDU:
                rapport.ignorees.append((numero, f"{email} : déjà marqué comme rendu."))
            else:
                erreurs = marquer_rendu(livrable, par=par)
                if erreurs:
                    rapport.erreurs.append((numero, f"{email} : {erreurs[0]}"))
                else:
                    rapport.faits.append((numero, f"{email} : « {nom_livrable} » marqué comme rendu, les rappels s'arrêtent."))
        if simuler:
            transaction.set_rollback(True)
    return rapport


# ---------------------------------------------------------------------------
# Archivage du dossier d'un stage (US-16, partie archivage)
# ---------------------------------------------------------------------------

def dossier_zip(stage):
    """Archive ZIP du dossier d'un stage : fiche de stage, historique complet, toutes les versions de la
    convention (PDF et scan signé) et, une fois validé, le PV de soutenance avec la note. Renvoie les octets
    du ZIP. Le rapport final est rendu sur Moodle : il n'est pas dans le dossier (voir LISEZMOI)."""
    etudiant = stage.etudiant
    fiche = [
        f"Étudiant : {etudiant.get_full_name()} <{etudiant.email}>",
        f"Promotion : {stage.promotion}",
        f"Type de stage : {stage.type_stage}",
        f"Entreprise : {stage.entreprise or ''}",
        f"Dates : du {stage.date_debut or '?'} au {stage.date_fin or '?'}",
        f"Tuteur : {stage.tuteur_nom} <{stage.tuteur_email}>",
        f"Statut de la fiche : {stage.get_statut_display()}",
        f"Sujet : {' '.join(stage.sujet.split())}",
        "",
        "Livrables (rendus sur Moodle) :",
        *[f"- {l.nom} : {l.get_statut_display()}, date limite {l.date_limite:%d/%m/%Y}" for l in stage.livrables.all()],
    ]
    lisezmoi = ("Dossier archivé depuis la plateforme de gestion des stages.\r\n"
                "Le rapport final est déposé sur Moodle : il ne figure pas dans cette archive. Le procès-verbal "
                "de soutenance y figure une fois validé par le Career Center.\r\n")
    soutenance = getattr(stage, "soutenance", None)  # None si le stage n'a pas (encore) de soutenance
    if soutenance is not None and soutenance.debut:
        fiche += ["", f"Soutenance : {timezone.localtime(soutenance.debut):%d/%m/%Y %H:%M}, salle {soutenance.salle}",
                  "Jury : " + ", ".join(m.get_full_name() or m.email for m in soutenance.jury.all())]
    historique = [
        [f"{h.date:%d/%m/%Y %H:%M}", h.auteur.get_full_name() if h.auteur else "", h.get_action_display(), h.commentaire]
        for h in stage.historique.select_related("auteur")
    ]
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("LISEZMOI.txt", lisezmoi)
        archive.writestr("fiche-de-stage.txt", "\r\n".join(fiche) + "\r\n")
        if soutenance is not None and soutenance.statut == "NOTEE":  # le PV n'est archivé qu'une fois validé
            archive.writestr("soutenance-pv.txt", (
                f"Note : {soutenance.note}/20\r\nPV validé le {timezone.localtime(soutenance.pv_valide_le):%d/%m/%Y}\r\n\r\n"
                + soutenance.pv.replace("\n", "\r\n") + "\r\n"))
        archive.writestr("historique.csv", ecrire_csv(["Date", "Auteur", "Action", "Commentaire"], historique))
        for convention in stage.conventions.order_by("version"):
            for fichier in (convention.fichier_pdf, convention.scan_signe):
                if not fichier:
                    continue
                try:
                    with fichier.open("rb") as f:
                        archive.writestr(f"conventions/{os.path.basename(fichier.name)}", f.read())
                except FileNotFoundError:  # fichier effacé du disque : on archive le reste
                    continue
    return tampon.getvalue()
