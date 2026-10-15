"""
Actions métier du suivi des stages. Elles sont regroupées ici (et non dans
les vues) pour être réutilisables et faciles à tester.
"""

import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage, send_mail
from django.db import transaction
from django.utils import timezone

from .convention_pdf import generer_pdf
from .models import (
    Affectation, Convention, Historique, Livrable, ModeleLivrable, ParametresEcole, Rappel, Stage,
    annee_universitaire_courante,
)


@transaction.atomic  # tout réussit ou rien n'est enregistré
def affecter_encadrant(etudiant, encadrant, par, annee=None):
    """Affecte (ou change) l'encadrant d'un étudiant pour une année universitaire.

    - désactive l'éventuelle affectation précédente (elle reste dans l'historique),
    - crée la nouvelle affectation,
    - l'inscrit dans l'historique du stage de l'année s'il existe déjà,
    - prévient l'encadrant et l'étudiant par e-mail.
    Renvoie la nouvelle affectation.
    """
    annee = annee or annee_universitaire_courante()

    ancienne = Affectation.objects.filter(
        etudiant=etudiant, annee_universitaire=annee, active=True
    ).first()
    if ancienne and ancienne.encadrant_id == encadrant.id:
        return ancienne  # rien ne change
    if ancienne:
        ancienne.active = False
        ancienne.save(update_fields=["active"])

    affectation = Affectation.objects.create(
        etudiant=etudiant, encadrant=encadrant, annee_universitaire=annee, affecte_par=par
    )

    stage = Stage.objects.filter(etudiant=etudiant, promotion__annee_universitaire=annee).first()
    if stage:
        Historique.objects.create(
            stage=stage, auteur=par, action=Historique.Action.AFFECTATION,
            commentaire=f"Encadrant : {encadrant.get_full_name() or encadrant.email}",
        )

    nom_etudiant = etudiant.get_full_name() or etudiant.email
    nom_encadrant = encadrant.get_full_name() or encadrant.email
    send_mail(
        "Nouvel étudiant à encadrer",
        f"Bonjour,\n\nLe Career Center vous a affecté l'étudiant {nom_etudiant} "
        f"pour l'année {annee}.\n",
        None,  # expéditeur par défaut (réglage DEFAULT_FROM_EMAIL)
        [encadrant.email],
    )
    send_mail(
        "Votre encadrant de stage",
        f"Bonjour,\n\nVotre encadrant pour l'année {annee} est {nom_encadrant}. "
        f"Vous pouvez maintenant lui soumettre votre fiche de stage.\n",
        None,
        [etudiant.email],
    )
    return affectation


# Statuts dans lesquels l'étudiant peut encore modifier et soumettre sa fiche
STATUTS_MODIFIABLES = {Stage.Statut.BROUILLON, Stage.Statut.REFUSE}


@transaction.atomic
def soumettre_stage(stage, par):
    """US-01 : l'étudiant soumet sa fiche à son valideur (encadrant ou coordinateur).

    Renvoie la liste des problèmes qui empêchent la soumission (vide = soumise).
    En cas de succès : statut SOUMIS, ligne d'historique, e-mail au valideur.
    """
    if stage.statut not in STATUTS_MODIFIABLES:
        return ["Cette fiche a déjà été soumise."]
    erreurs = stage.erreurs_soumission()
    if erreurs:
        return erreurs

    stage.statut = Stage.Statut.SOUMIS
    stage.save(update_fields=["statut", "modifie_le"])
    Historique.objects.create(stage=stage, auteur=par, action=Historique.Action.SOUMISSION)

    valideur = stage.valideur()
    nom_etudiant = stage.etudiant.get_full_name() or stage.etudiant.email
    send_mail(
        "Fiche de stage à valider",
        f"Bonjour,\n\n{nom_etudiant} a soumis sa fiche de stage « {stage.type_stage} » "
        f"chez {stage.entreprise}. Elle attend votre décision sur la plateforme.\n",
        None,
        [valideur.email],
    )
    return []


@transaction.atomic
def decider_stage(stage, par, valider, motif=""):
    """US-02 : le valideur (encadrant ou coordinateur) valide ou refuse la fiche soumise.

    Renvoie la liste des problèmes qui empêchent la décision (vide = décision enregistrée).
    En cas de succès : nouveau statut, ligne d'historique (avec le motif), e-mail à l'étudiant.
    """
    motif = (motif or "").strip()
    if stage.statut != Stage.Statut.SOUMIS:
        return ["Cette fiche n'est pas en attente de décision."]
    if stage.valideur() != par:
        return ["Vous n'êtes pas le valideur de ce stage."]
    if not valider and not motif:
        return ["Un refus doit être accompagné d'un motif."]

    if valider:
        stage.statut = Stage.Statut.VALIDE
        action = Historique.Action.VALIDATION
    else:
        stage.statut = Stage.Statut.REFUSE
        action = Historique.Action.REFUS
    stage.save(update_fields=["statut", "modifie_le"])
    Historique.objects.create(stage=stage, auteur=par, action=action, commentaire=motif)

    nom_valideur = par.get_full_name() or par.email
    if valider:
        sujet = "Votre stage est validé"
        texte = (f"Bonjour,\n\n{nom_valideur} a validé votre stage chez {stage.entreprise}. "
                 f"La prochaine étape est la convention de stage.\n")
    else:
        sujet = "Votre fiche de stage est à corriger"
        texte = (f"Bonjour,\n\n{nom_valideur} a refusé votre fiche de stage pour le motif suivant :\n"
                 f"« {motif} »\n\nCorrigez-la sur la plateforme puis soumettez-la de nouveau.\n")
    if motif and valider:
        texte += f"\nCommentaire : « {motif} »\n"
    send_mail(sujet, texte, None, [stage.etudiant.email])
    return []


# ---------------------------------------------------------------------------
# Convention (Lot 2)
# ---------------------------------------------------------------------------

EXTENSIONS_SCAN = {".pdf": b"%PDF", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".png": b"\x89PNG"}


def prochain_numero(annee=None):
    """Numéro de convention suivant, ex. « 2026-0007 » (une suite par année civile)."""
    annee = annee or timezone.localdate().year
    existants = Convention.objects.filter(numero__startswith=f"{annee}-").values_list("numero", flat=True)
    dernier = max((int(n.split("-")[1]) for n in existants), default=0)
    return f"{annee}-{dernier + 1:04d}"


def convention_en_vigueur(stage):
    """La convention du stage qui n'a pas été remplacée (ou None)."""
    return stage.conventions.exclude(statut=Convention.Statut.REMPLACEE).first()


@transaction.atomic
def generer_convention(stage, par):
    """Génère le PDF de la convention d'un stage VALIDÉ.

    Si une convention existe déjà (non signée), une nouvelle VERSION est créée et l'ancienne
    est marquée « remplacée » : rien n'est écrasé. Une convention signée est verrouillée.
    Renvoie (convention, erreurs).
    """
    if stage.statut != Stage.Statut.VALIDE:
        return None, ["Le stage doit d'abord être validé par son valideur."]
    actuelle = convention_en_vigueur(stage)
    if actuelle and actuelle.statut == Convention.Statut.SIGNEE:
        return None, ["La convention est déjà signée : elle est verrouillée."]

    if actuelle:
        numero, version = actuelle.numero, actuelle.version + 1
        actuelle.statut = Convention.Statut.REMPLACEE
        actuelle.save(update_fields=["statut"])
    else:
        numero, version = prochain_numero(), 1

    convention = Convention.objects.create(stage=stage, numero=numero, version=version, genere_par=par)
    convention.fichier_pdf.save(
        f"convention-{numero}-v{version}.pdf", ContentFile(generer_pdf(convention)), save=True
    )
    Historique.objects.create(
        stage=stage, auteur=par, action=Historique.Action.CONVENTION_GENEREE,
        commentaire=f"n° {numero}, version {version}",
    )
    return convention, []


@transaction.atomic
def marquer_envoyee(convention, par):
    """Le directeur des études a signé la convention (sur papier) : le Career Center l'envoie
    à l'étudiant, qui la fait signer par l'entreprise puis dépose le scan."""
    if convention.statut != Convention.Statut.GENEREE:
        return ["Cette convention n'est pas en attente d'envoi."]
    convention.statut = Convention.Statut.ENVOYEE
    convention.envoyee_le = timezone.now()
    convention.save(update_fields=["statut", "envoyee_le"])
    Historique.objects.create(
        stage=convention.stage, auteur=par, action=Historique.Action.CONVENTION_ENVOYEE,
        commentaire=f"n° {convention.numero}",
    )
    message = EmailMessage(
        f"Votre convention de stage n° {convention.numero}",
        "Bonjour,\n\nVotre convention de stage, signée par l'école, est disponible sur la plateforme "
        "(et jointe à ce message). Faites-la signer par l'entreprise, signez-la, puis déposez le "
        "scan de la convention signée sur la plateforme.\n",
        None, [convention.stage.etudiant.email],
    )
    convention.fichier_pdf.open("rb")
    message.attach(os.path.basename(convention.fichier_pdf.name), convention.fichier_pdf.read(), "application/pdf")
    convention.fichier_pdf.close()
    message.send()
    return []


def erreur_scan(fichier):
    """Vérifie un scan déposé : extension, taille, et contenu réel (pas seulement le nom).
    Renvoie un message d'erreur, ou None si le fichier est accepté."""
    extension = os.path.splitext(fichier.name)[1].lower()
    if extension not in EXTENSIONS_SCAN:
        return "Format refusé : déposez un PDF, un JPG ou un PNG."
    if fichier.size > settings.TAILLE_MAX_SCAN:
        return f"Fichier trop gros (maximum {settings.TAILLE_MAX_SCAN // (1024 * 1024)} Mo)."
    debut = fichier.read(8)
    fichier.seek(0)
    if not debut.startswith(EXTENSIONS_SCAN[extension]):
        return "Le contenu du fichier ne correspond pas à son format."
    return None


@transaction.atomic
def deposer_scan(convention, fichier, par):
    """L'étudiant dépose le scan de la convention signée par les trois parties.
    Il peut le redéposer tant que le Career Center ne l'a pas validé."""
    if convention.statut != Convention.Statut.ENVOYEE:
        return ["Le scan ne peut être déposé qu'une fois la convention envoyée, et avant sa validation."]
    probleme = erreur_scan(fichier)
    if probleme:
        return [probleme]

    if convention.scan_signe:
        convention.scan_signe.delete(save=False)  # remplace l'ancien scan
    extension = os.path.splitext(fichier.name)[1].lower()
    convention.scan_signe.save(f"scan-{convention.numero}-v{convention.version}{extension}", fichier, save=False)
    convention.scan_depose_le = timezone.now()
    convention.save(update_fields=["scan_signe", "scan_depose_le"])
    Historique.objects.create(
        stage=convention.stage, auteur=par, action=Historique.Action.SCAN_DEPOSE,
        commentaire=f"convention n° {convention.numero}",
    )
    nom = convention.stage.etudiant.get_full_name() or convention.stage.etudiant.email
    send_mail(
        f"Scan à vérifier : convention n° {convention.numero}",
        f"{nom} a déposé le scan de sa convention signée. Vérifiez-le sur la plateforme.\n",
        None, [ParametresEcole.actuels().email_contact],
    )
    return []


@transaction.atomic
def valider_signature(convention, par):
    """Le Career Center a vérifié le scan : la convention est signée par toutes les parties
    (elle est alors verrouillée)."""
    if convention.statut != Convention.Statut.ENVOYEE or not convention.scan_signe:
        return ["Il n'y a pas de scan à valider pour cette convention."]
    convention.statut = Convention.Statut.SIGNEE
    convention.signee_le = timezone.now()
    convention.save(update_fields=["statut", "signee_le"])
    Historique.objects.create(
        stage=convention.stage, auteur=par, action=Historique.Action.CONVENTION_SIGNEE,
        commentaire=f"n° {convention.numero}",
    )
    creer_livrables(convention.stage)  # la convention signée ouvre le suivi du stage (Lot 3)
    send_mail(
        f"Convention n° {convention.numero} signée",
        "Bonjour,\n\nVotre convention de stage est signée par toutes les parties. "
        "Vous pouvez commencer votre stage à la date prévue.\n",
        None, [convention.stage.etudiant.email],
    )
    return []


@transaction.atomic
def refuser_scan(convention, par, motif):
    """Le scan est illisible ou incomplet : l'étudiant est prévenu et doit le redéposer."""
    motif = (motif or "").strip()
    if convention.statut != Convention.Statut.ENVOYEE or not convention.scan_signe:
        return ["Il n'y a pas de scan à refuser pour cette convention."]
    if not motif:
        return ["Un refus doit être accompagné d'un motif."]
    convention.scan_signe.delete(save=False)
    convention.scan_depose_le = None
    convention.save(update_fields=["scan_signe", "scan_depose_le"])
    Historique.objects.create(
        stage=convention.stage, auteur=par, action=Historique.Action.SCAN_REFUSE, commentaire=motif,
    )
    send_mail(
        f"Scan de la convention n° {convention.numero} à redéposer",
        f"Bonjour,\n\nVotre scan a été refusé pour le motif suivant :\n« {motif} »\n\n"
        "Déposez-le de nouveau sur la plateforme.\n",
        None, [convention.stage.etudiant.email],
    )
    return []


# ---------------------------------------------------------------------------
# Livrables rendus sur Moodle : suivi et rappels automatiques (Lot 3 bis)
# ---------------------------------------------------------------------------

def aujourdhui():
    """Date du jour (une fonction à part pour pouvoir la figer dans les tests)."""
    return timezone.localdate()


def creer_livrables(stage):
    """Crée les livrables attendus d'un stage (selon son type), avec leurs dates limites.
    Sans danger si on l'appelle deux fois : ceux qui existent déjà ne sont pas recréés.
    Si aucun modèle n'existe pour ce type, un « Rapport de stage » est créé au 15 septembre."""
    modeles = list(ModeleLivrable.objects.filter(type_stage=stage.type_stage))
    if not modeles:
        modeles = [ModeleLivrable(type_stage=stage.type_stage, nom="Rapport de stage", est_rapport=True,
                                  calcul=ModeleLivrable.Calcul.FIXE, mois=9, jour=15)]
    crees = []
    for modele in modeles:
        date_limite = modele.date_limite(stage)
        if date_limite is None:
            continue
        livrable, cree = Livrable.objects.get_or_create(
            stage=stage, nom=modele.nom,
            defaults={"modele": modele if modele.pk else None, "est_rapport": modele.est_rapport,
                      "date_limite": date_limite},
        )
        if cree:
            crees.append(livrable)
            if livrable.est_rapport and not stage.date_limite_rapport:
                stage.date_limite_rapport = date_limite
                stage.save(update_fields=["date_limite_rapport"])
    return crees


@transaction.atomic
def marquer_rendu(livrable, par):
    """Le Career Center constate sur Moodle que le livrable est rendu : les rappels s'arrêtent."""
    if livrable.statut == Livrable.Statut.RENDU:
        return ["Ce livrable est déjà marqué comme rendu."]
    livrable.statut = Livrable.Statut.RENDU
    livrable.rendu_le = timezone.now()
    livrable.rendu_par = par
    livrable.save(update_fields=["statut", "rendu_le", "rendu_par"])
    Historique.objects.create(
        stage=livrable.stage, auteur=par, action=Historique.Action.LIVRABLE_RENDU, commentaire=livrable.nom,
    )
    return []


@transaction.atomic
def annuler_rendu(livrable, par):
    """Correction d'une erreur : le livrable repasse « à rendre » (et les rappels reprennent)."""
    if livrable.statut != Livrable.Statut.RENDU:
        return ["Ce livrable n'est pas marqué comme rendu."]
    livrable.statut = Livrable.Statut.A_RENDRE
    livrable.rendu_le = None
    livrable.rendu_par = None
    livrable.save(update_fields=["statut", "rendu_le", "rendu_par"])
    Historique.objects.create(
        stage=livrable.stage, auteur=par, action=Historique.Action.LIVRABLE_ANNULE, commentaire=livrable.nom,
    )
    return []


@transaction.atomic
def prolonger_livrable(livrable, nouvelle_date, par):
    """Le Career Center repousse la date limite d'un livrable (cas particulier d'un étudiant).
    Les rappels déjà envoyés pour ce livrable sont remis à zéro : le nouveau calendrier repart."""
    if livrable.statut == Livrable.Statut.RENDU:
        return ["Ce livrable est déjà rendu."]
    if nouvelle_date <= livrable.date_limite:
        return ["La nouvelle date doit être postérieure à la date limite actuelle."]
    ancienne = livrable.date_limite
    livrable.date_limite = nouvelle_date
    livrable.save(update_fields=["date_limite"])
    livrable.rappels.all().delete()
    if livrable.est_rapport:
        Stage.objects.filter(pk=livrable.stage_id).update(date_limite_rapport=nouvelle_date)
    Historique.objects.create(
        stage=livrable.stage, auteur=par, action=Historique.Action.DELAI_PROLONGE,
        commentaire=f"{livrable.nom} : du {ancienne:%d/%m/%Y} au {nouvelle_date:%d/%m/%Y}",
    )
    send_mail(
        f"Nouvelle date limite : {livrable.nom}",
        f"Bonjour,\n\nLa date limite de « {livrable.nom} » est repoussée au {nouvelle_date:%d/%m/%Y}.\n",
        None, [livrable.stage.etudiant.email],
    )
    return []


def _texte_rappel(livrable, ecart):
    """Sujet et corps de l'e-mail de rappel (ecart > 0 : jours restants ; < 0 : jours de retard)."""
    date_limite = f"{livrable.date_limite:%d/%m/%Y}"
    if ecart > 1:
        quand, sujet = f"dans {ecart} jours (le {date_limite})", f"Rappel : « {livrable.nom} » à rendre avant le {date_limite}"
    elif ecart == 1:
        quand, sujet = f"demain (le {date_limite})", f"Rappel : « {livrable.nom} » à rendre demain"
    elif ecart == 0:
        quand, sujet = f"aujourd'hui ({date_limite})", f"Dernier jour : « {livrable.nom} » à rendre aujourd'hui"
    else:
        quand = f"le {date_limite}, soit {-ecart} jour{'s' if ecart < -1 else ''} de retard"
        sujet = f"RETARD : « {livrable.nom} » n'a pas été rendu"
    corps = (f"Bonjour,\n\nVotre livrable « {livrable.nom} » ({livrable.stage.type_stage}) est à rendre sur "
             f"Moodle avant {quand}.\n")
    if livrable.lien_moodle:
        corps += f"\nLien du devoir sur Moodle : {livrable.lien_moodle}\n"
    corps += ("\nS'il est déjà rendu, ce message est envoyé avant que le Career Center ne l'ait enregistré : "
              "vous n'avez rien à faire de plus.\n")
    return sujet, corps


def envoyer_rappels(jour=None):
    """Envoie les rappels de livrables dus à la date donnée (par défaut aujourd'hui).

    - un livrable « rendu » ne reçoit plus rien ;
    - chaque rappel (ex. « 3 jours avant ») est envoyé UNE seule fois, même si la commande est
      relancée ; si elle n'a pas tourné pendant plusieurs jours, un seul message rattrape le retard ;
    - le Career Center reçoit un récapitulatif des nouveaux retards.
    Renvoie un dictionnaire : {"envoyes": n, "retards": [livrables], "erreurs": n}."""
    jour = jour or aujourdhui()
    ecole = ParametresEcole.actuels()
    decalages = ecole.decalages_rappels()
    resultat = {"envoyes": 0, "retards": [], "erreurs": 0}

    livrables = Livrable.objects.filter(statut=Livrable.Statut.A_RENDRE).select_related(
        "stage__etudiant", "stage__promotion", "modele")
    for livrable in livrables:
        ecart = (livrable.date_limite - jour).days
        dus = [d for d in decalages if ecart <= d]
        deja_envoyes = set(livrable.rappels.values_list("decalage", flat=True))
        nouveaux = [d for d in dus if d not in deja_envoyes]
        if not nouveaux:
            continue
        sujet, corps = _texte_rappel(livrable, ecart)
        destinataire = livrable.stage.etudiant.email
        try:
            with transaction.atomic():  # si l'envoi échoue, rien n'est enregistré : il sera retenté
                for d in nouveaux:
                    Rappel.objects.create(livrable=livrable, decalage=d, destinataire=destinataire)
                send_mail(sujet, corps, None, [destinataire])
        except Exception:  # un e-mail en échec ne doit pas bloquer les autres étudiants
            resultat["erreurs"] += 1
            continue
        resultat["envoyes"] += 1
        if ecart < 0:
            resultat["retards"].append(livrable)

    if resultat["retards"]:
        lignes = "\n".join(
            f"- {l.stage.etudiant.get_full_name() or l.stage.etudiant.email} ({l.stage.type_stage}) : "
            f"« {l.nom} », date limite {l.date_limite:%d/%m/%Y}" for l in resultat["retards"])
        send_mail("Livrables en retard", f"Bonjour,\n\nNouveaux retards constatés :\n{lignes}\n",
                  None, [ecole.email_contact])
    return resultat
