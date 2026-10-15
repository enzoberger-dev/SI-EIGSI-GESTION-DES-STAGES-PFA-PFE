"""
Actions métier des soutenances (Lot 6), regroupées ici pour être réutilisables et faciles à tester.

Parcours : le Career Center ouvre une campagne (les jurys sont prévenus) → les jurys cochent leurs
disponibilités (US-12) → le planning est proposé automatiquement (US-13) → le Career Center le valide
et les convocations partent (US-14) → le jury saisit le PV et la note, le Career Center les valide (US-15)
→ export des notes (US-16).
"""

from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import formats, timezone

from comptes import roles
from stages.csv_outils import ecrire_csv
from stages.models import Convention, Historique, ParametresEcole, Stage
from stages.services import aujourdhui

from .models import Campagne, Disponibilite, RelanceJury, ReponseJury, Salle, Soutenance

# Un créneau ne peut pas être placé avant la fin du stage de l'étudiant (hypothèse, #32).
EXIGER_FIN_DE_STAGE = True


def _lien(nom_de_page, *args):
    """Adresse complète d'une page pour un e-mail (SITE_URL est réglé dans settings.py)."""
    return settings.SITE_URL.rstrip("/") + reverse(nom_de_page, args=args)


def _nom(utilisateur):
    return utilisateur.get_full_name() or utilisateur.email


def membres_du_jury():
    """Les personnes qui ont le rôle Jury (et un compte actif)."""
    return get_user_model().objects.filter(groups__name=roles.JURY, is_active=True).distinct().order_by("last_name", "first_name")


def _quand(debut):
    """« lundi 14 septembre 2027 à 09:00 » (heure locale)."""
    local = timezone.localtime(debut)
    return f"{formats.date_format(local, 'l j F Y')} à {local:%H:%M}"


# ---------------------------------------------------------------------------
# Campagne et disponibilités du jury (US-12)
# ---------------------------------------------------------------------------

def ouvrir_campagne(campagne):
    """Prévient chaque membre du jury par e-mail (avec le lien du sondage de disponibilités).
    Renvoie le nombre de personnes prévenues."""
    membres = list(membres_du_jury())
    for membre in membres:
        send_mail(
            f"Vos disponibilités pour les soutenances : {campagne.nom}",
            f"Bonjour,\n\nMerci d'indiquer vos disponibilités pour les soutenances du "
            f"{campagne.date_debut:%d/%m/%Y} au {campagne.date_fin:%d/%m/%Y}.\n\n"
            f"Répondre au sondage : {_lien('jury_disponibilites', campagne.pk)}\n",
            None, [membre.email],
        )
    return len(membres)


@transaction.atomic
def enregistrer_disponibilites(campagne, membre, debuts):
    """Enregistre les créneaux cochés par un membre du jury (remplace sa réponse précédente).
    `debuts` : datetimes. Seuls les créneaux réels de la campagne sont retenus.
    Renvoie la liste des problèmes (vide = enregistré)."""
    if campagne.statut != Campagne.Statut.OUVERTE:
        return ["Le sondage de disponibilités est clos pour cette campagne."]
    if not membre.a_le_role(roles.JURY):
        return ["Seuls les membres du jury répondent au sondage."]
    valides = set(campagne.creneaux())
    choisis = {d for d in debuts if d in valides}
    Disponibilite.objects.filter(campagne=campagne, membre=membre).delete()
    Disponibilite.objects.bulk_create([Disponibilite(campagne=campagne, membre=membre, debut=d) for d in sorted(choisis)])
    ReponseJury.objects.update_or_create(campagne=campagne, membre=membre)
    return []


def jurys_sans_reponse(campagne):
    """Membres du jury qui n'ont pas encore répondu au sondage."""
    ont_repondu = ReponseJury.objects.filter(campagne=campagne).values_list("membre_id", flat=True)
    return membres_du_jury().exclude(pk__in=ont_repondu)


def envoyer_relances_jury(jour=None):
    """Relance les membres du jury qui n'ont pas répondu au sondage d'une campagne ouverte, aux mêmes
    délais que les autres relances (« Paramètres de l'école »). Jamais deux fois la même.
    Renvoie le nombre de relances envoyées."""
    jour = jour or aujourdhui()
    delais = ParametresEcole.actuels().delais_relances()
    envoyees = 0
    for campagne in Campagne.objects.filter(statut=Campagne.Statut.OUVERTE):
        attente = (jour - timezone.localtime(campagne.ouverte_le).date()).days
        dus = [d for d in delais if attente >= d]
        if not dus:
            continue
        for membre in jurys_sans_reponse(campagne):
            deja = set(RelanceJury.objects.filter(campagne=campagne, membre=membre).values_list("delai", flat=True))
            nouveaux = [d for d in dus if d not in deja]
            if not nouveaux:
                continue
            try:
                with transaction.atomic():
                    for d in nouveaux:
                        RelanceJury.objects.create(campagne=campagne, membre=membre, delai=d)
                    send_mail(
                        f"Rappel : vos disponibilités pour les soutenances ({campagne.nom})",
                        f"Bonjour,\n\nVous n'avez pas encore indiqué vos disponibilités ({attente} jours). "
                        f"Répondre au sondage : {_lien('jury_disponibilites', campagne.pk)}\n",
                        None, [membre.email],
                    )
            except Exception:  # un e-mail en échec ne bloque pas les autres
                continue
            envoyees += 1
    return envoyees


# ---------------------------------------------------------------------------
# Planning (US-13)
# ---------------------------------------------------------------------------

def stages_a_soutenir(campagne):
    """Stages qui ont droit à une soutenance dans cette campagne : validés, convention signée, année
    d'études concernée, même année universitaire."""
    return Stage.objects.filter(
        statut=Stage.Statut.VALIDE,
        promotion__annee_universitaire=campagne.annee_universitaire,
        promotion__annee_etudes__in=campagne.annees(),
        conventions__statut=Convention.Statut.SIGNEE,
    ).distinct().select_related("etudiant", "promotion", "entreprise")


def generer_soutenances(campagne):
    """Crée la soutenance de chaque stage concerné qui n'en a pas encore. Renvoie le nombre créé."""
    crees = 0
    for stage in stages_a_soutenir(campagne):
        _, cree = Soutenance.objects.get_or_create(stage=stage, defaults={"campagne": campagne})
        crees += cree
    return crees


def _se_chevauchent(debut_a, fin_a, debut_b, fin_b):
    return debut_a < fin_b and debut_b < fin_a


def _occupations(exclure_pk=None):
    """Soutenances déjà placées : (début, fin, salle, membres du jury, étudiant)."""
    qs = Soutenance.objects.filter(debut__isnull=False).select_related("stage").prefetch_related("jury")
    if exclure_pk:
        qs = qs.exclude(pk=exclure_pk)
    return [(s.debut, s.fin, s.salle_id, {m.pk for m in s.jury.all()}, s.stage.etudiant_id) for s in qs]


def _conflits(occupations, debut, fin, salle_id, membres_ids, etudiant_id):
    """Messages décrivant les conflits d'un créneau avec les soutenances déjà placées."""
    messages = set()
    for d, f, salle, membres, etudiant in occupations:
        if not _se_chevauchent(debut, fin, d, f):
            continue
        if salle_id is not None and salle == salle_id:
            messages.add("Cette salle est déjà occupée à ce moment.")
        if membres & set(membres_ids):
            messages.add("Un membre du jury a déjà une soutenance à ce moment.")
        if etudiant_id is not None and etudiant == etudiant_id:
            messages.add("Cet étudiant a déjà une soutenance à ce moment.")
    return sorted(messages)


def _vider(soutenance):
    soutenance.debut = soutenance.fin = soutenance.salle = None
    soutenance.statut = Soutenance.Statut.A_PLANIFIER
    soutenance.save(update_fields=["debut", "fin", "salle", "statut"])
    soutenance.jury.clear()


@transaction.atomic
def proposer_planning(campagne):
    """Propose automatiquement un créneau, une salle et un jury à chaque soutenance non figée.

    Règle simple (pas un solveur) : les étudiants sont pris dans l'ordre de fin de stage ; chacun reçoit le
    premier créneau où une salle est libre et où assez de membres du jury sont disponibles et libres, en
    choisissant ceux qui ont le moins de soutenances. Un jury, une salle et un étudiant par créneau.
    Les soutenances déjà convoquées (ou passées) ne bougent pas ; une nouvelle proposition remplace les
    anciennes propositions non validées.
    Renvoie {"planifiees": n, "non_planifiables": [soutenances], "erreurs": [textes]}."""
    resultat = {"planifiees": 0, "non_planifiables": [], "erreurs": []}
    salles = list(Salle.objects.filter(active=True))
    jury_ids = set(membres_du_jury().values_list("pk", flat=True))
    if not salles:
        resultat["erreurs"].append("Aucune salle active : ajoutez-en dans l'administration (« Salles »).")
    if len(jury_ids) < campagne.taille_jury:
        resultat["erreurs"].append(
            f"Il faut au moins {campagne.taille_jury} membres du jury (rôle « Jury »), il y en a {len(jury_ids)}.")
    if resultat["erreurs"]:
        return resultat

    generer_soutenances(campagne)
    for proposee in campagne.soutenances.filter(statut=Soutenance.Statut.PROPOSEE):
        _vider(proposee)

    dispo = defaultdict(set)
    for d in Disponibilite.objects.filter(campagne=campagne):
        dispo[d.debut].add(d.membre_id)
    occupations = _occupations()
    charge = Counter()
    for _, _, _, membres, _ in occupations:
        charge.update(membres)
    duree = timedelta(minutes=campagne.duree_minutes)
    creneaux = campagne.creneaux()

    a_planifier = campagne.soutenances.filter(statut=Soutenance.Statut.A_PLANIFIER).select_related(
        "stage__etudiant").order_by("stage__date_fin", "stage__etudiant__last_name", "pk")
    for soutenance in a_planifier:
        stage = soutenance.stage
        place = False
        for creneau in creneaux:
            if EXIGER_FIN_DE_STAGE and stage.date_fin and timezone.localtime(creneau).date() < stage.date_fin:
                continue
            fin = creneau + duree
            candidats = sorted(
                (m for m in dispo[creneau] if m in jury_ids and m != stage.etudiant_id),
                key=lambda m: (charge[m], m),
            )
            libres = [m for m in candidats if not _conflits(occupations, creneau, fin, None, [m], None)]
            if len(libres) < campagne.taille_jury:
                continue
            salle = next((s for s in salles if not _conflits(occupations, creneau, fin, s.pk, [], None)), None)
            if salle is None:
                continue
            choisis = libres[:campagne.taille_jury]
            soutenance.debut, soutenance.fin, soutenance.salle = creneau, fin, salle
            soutenance.statut = Soutenance.Statut.PROPOSEE
            soutenance.save(update_fields=["debut", "fin", "salle", "statut"])
            soutenance.jury.set(choisis)
            occupations.append((creneau, fin, salle.pk, set(choisis), stage.etudiant_id))
            charge.update(choisis)
            resultat["planifiees"] += 1
            place = True
            break
        if not place:
            resultat["non_planifiables"].append(soutenance)

    if campagne.statut == Campagne.Statut.OUVERTE:
        campagne.statut = Campagne.Statut.PLANIFIEE
        campagne.save(update_fields=["statut"])
    return resultat


@transaction.atomic
def deplacer_soutenance(soutenance, debut, salle, membres, par):
    """Le Career Center fixe ou corrige à la main le créneau, la salle et le jury d'une soutenance.
    Refuse les conflits (salle, jury, étudiant). Si les convocations sont déjà parties, une mise à jour
    est envoyée. Renvoie la liste des problèmes (vide = enregistré)."""
    if soutenance.statut in (Soutenance.Statut.PV_SAISI, Soutenance.Statut.NOTEE):
        return ["Cette soutenance a déjà eu lieu (PV saisi) : on ne peut plus la déplacer."]
    membres = list(membres)
    if not membres:
        return ["Choisissez au moins un membre du jury."]
    if any(not m.a_le_role(roles.JURY) for m in membres):
        return ["Seuls les membres du jury peuvent faire partie du jury."]
    fin = debut + timedelta(minutes=soutenance.campagne.duree_minutes)
    conflits = _conflits(
        _occupations(exclure_pk=soutenance.pk), debut, fin, salle.pk, [m.pk for m in membres], soutenance.stage.etudiant_id)
    if conflits:
        return conflits

    deja_convoquee = soutenance.statut == Soutenance.Statut.CONVOQUEE
    soutenance.debut, soutenance.fin, soutenance.salle = debut, fin, salle
    if soutenance.statut == Soutenance.Statut.A_PLANIFIER:
        soutenance.statut = Soutenance.Statut.PROPOSEE
    soutenance.save(update_fields=["debut", "fin", "salle", "statut"])
    soutenance.jury.set(membres)
    if deja_convoquee:
        Historique.objects.create(
            stage=soutenance.stage, auteur=par, action=Historique.Action.SOUTENANCE_CONVOQUEE,
            commentaire=f"Déplacée : {_quand(debut)}, {salle}",
        )
        _envoyer_convocations(soutenance, mise_a_jour=True)
    return []


# ---------------------------------------------------------------------------
# Convocations (US-14)
# ---------------------------------------------------------------------------

def _envoyer_convocations(soutenance, mise_a_jour):
    """E-mail à l'étudiant et à chaque membre du jury : date, heure, salle (et jury)."""
    etudiant = soutenance.stage.etudiant
    jury = list(soutenance.jury.all())
    lieu = (f"{_quand(soutenance.debut)} (durée {soutenance.campagne.duree_minutes} min), "
            f"salle {soutenance.salle}")
    noms_jury = ", ".join(_nom(m) for m in jury)
    debut_sujet = "MISE À JOUR : convocation" if mise_a_jour else "Convocation"
    send_mail(
        f"{debut_sujet} à votre soutenance de stage",
        f"Bonjour,\n\nVotre soutenance de stage a lieu {lieu}.\nJury : {noms_jury}.\n"
        + ("\nAttention : ces informations remplacent celles envoyées précédemment.\n" if mise_a_jour else "")
        + f"\nDétails : {_lien('mon_stage')}\n",
        None, [etudiant.email],
    )
    for membre in jury:
        send_mail(
            f"{debut_sujet} : soutenance de {_nom(etudiant)}",
            f"Bonjour,\n\nVous êtes membre du jury de la soutenance de {_nom(etudiant)} "
            f"({soutenance.stage.type_stage}, {soutenance.stage.entreprise}) : {lieu}.\n"
            f"Jury : {noms_jury}.\n"
            + ("\nAttention : ces informations remplacent celles envoyées précédemment.\n" if mise_a_jour else "")
            + f"\nVos soutenances : {_lien('jury_accueil')}\n",
            None, [membre.email],
        )


@transaction.atomic
def valider_planning(campagne, par):
    """Le Career Center valide les créneaux proposés : les soutenances passent « convoquées » et les
    convocations partent. Renvoie la liste des problèmes (vide = validé)."""
    proposees = list(campagne.soutenances.filter(statut=Soutenance.Statut.PROPOSEE).select_related(
        "stage__etudiant", "stage__entreprise", "salle").prefetch_related("jury"))
    if not proposees:
        return ["Il n'y a aucun créneau proposé à valider."]
    for soutenance in proposees:
        soutenance.statut = Soutenance.Statut.CONVOQUEE
        soutenance.save(update_fields=["statut"])
        Historique.objects.create(
            stage=soutenance.stage, auteur=par, action=Historique.Action.SOUTENANCE_CONVOQUEE,
            commentaire=f"{_quand(soutenance.debut)}, salle {soutenance.salle}",
        )
        _envoyer_convocations(soutenance, mise_a_jour=False)
    campagne.statut = Campagne.Statut.VALIDEE
    campagne.save(update_fields=["statut"])
    return []


# ---------------------------------------------------------------------------
# PV et note (US-15)
# ---------------------------------------------------------------------------

def lire_note(texte):
    """Note saisie (« 14,5 » ou « 14.5 ») -> Decimal à 2 décimales, ou None si invalide / hors de 0 à 20."""
    try:
        note = Decimal(str(texte).strip().replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    # « NaN » et « Infinity » sont acceptés par Decimal : on les écarte avant de comparer
    return note if note.is_finite() and Decimal("0") <= note <= Decimal("20") else None


@transaction.atomic
def saisir_pv(soutenance, par, note, pv):
    """Un membre du jury de la soutenance saisit (ou corrige) le PV et la note. Tant que le Career Center
    ne les a pas validés, ils restent modifiables. Renvoie la liste des problèmes (vide = enregistré)."""
    if not soutenance.jury.filter(pk=par.pk).exists():
        return ["Seuls les membres du jury de cette soutenance peuvent saisir le PV."]
    if soutenance.statut not in (Soutenance.Statut.CONVOQUEE, Soutenance.Statut.PV_SAISI):
        return ["Le PV ne peut être saisi qu'après la convocation, et avant sa validation."]
    note = lire_note(note)
    if note is None:
        return ["La note doit être un nombre de 0 à 20."]
    pv = (pv or "").strip()
    if not pv:
        return ["Le procès-verbal est obligatoire."]

    soutenance.note, soutenance.pv = note, pv
    soutenance.pv_saisi_par, soutenance.pv_saisi_le = par, timezone.now()
    soutenance.statut = Soutenance.Statut.PV_SAISI
    soutenance.save(update_fields=["note", "pv", "pv_saisi_par", "pv_saisi_le", "statut"])
    Historique.objects.create(stage=soutenance.stage, auteur=par, action=Historique.Action.PV_SAISI)
    etudiant = soutenance.stage.etudiant
    send_mail(
        f"PV à valider : soutenance de {_nom(etudiant)}",
        f"{_nom(par)} a saisi le PV et la note de la soutenance de {_nom(etudiant)}. "
        f"Vérifiez-les : {_lien('soutenances_campagne', soutenance.campagne_id)}\n",
        None, [ParametresEcole.actuels().email_contact],
    )
    return []


@transaction.atomic
def valider_pv(soutenance, par):
    """Le Career Center valide le PV et la note : la soutenance est notée, le PV est verrouillé."""
    if soutenance.statut != Soutenance.Statut.PV_SAISI:
        return ["Il n'y a pas de PV à valider pour cette soutenance."]
    soutenance.statut = Soutenance.Statut.NOTEE
    soutenance.pv_valide_par, soutenance.pv_valide_le = par, timezone.now()
    soutenance.save(update_fields=["statut", "pv_valide_par", "pv_valide_le"])
    Historique.objects.create(
        stage=soutenance.stage, auteur=par, action=Historique.Action.NOTE_VALIDEE, commentaire=f"{soutenance.note}/20",
    )
    return []


@transaction.atomic
def refuser_pv(soutenance, par, motif):
    """Le PV est incomplet : il repasse au jury pour correction, avec le motif."""
    motif = (motif or "").strip()
    if soutenance.statut != Soutenance.Statut.PV_SAISI:
        return ["Il n'y a pas de PV à renvoyer pour cette soutenance."]
    if not motif:
        return ["Un renvoi doit être accompagné d'un motif."]
    soutenance.statut = Soutenance.Statut.CONVOQUEE
    soutenance.save(update_fields=["statut"])
    Historique.objects.create(stage=soutenance.stage, auteur=par, action=Historique.Action.PV_REFUSE, commentaire=motif)
    etudiant = soutenance.stage.etudiant
    for membre in soutenance.jury.all():
        send_mail(
            f"PV de la soutenance de {_nom(etudiant)} à corriger",
            f"Bonjour,\n\nLe PV a été renvoyé pour le motif suivant :\n« {motif} »\n\n"
            f"Corrigez-le ici : {_lien('jury_accueil')}\n",
            None, [membre.email],
        )
    return []


# ---------------------------------------------------------------------------
# Export des notes vers WebAurion (US-16)
# ---------------------------------------------------------------------------

COLONNES_NOTES = ["Nom", "Prénom", "E-mail", "Année universitaire", "Type de stage", "Entreprise",
                  "Date de soutenance", "Note /20", "N° convention"]


def exporter_notes(annee):
    """CSV des notes VALIDÉES (soutenances « notées ») d'une année universitaire. Note avec virgule
    décimale (Excel français). Renvoie (octets du CSV, nombre de lignes). Format : hypothèse (#32)."""
    soutenances = Soutenance.objects.filter(
        statut=Soutenance.Statut.NOTEE, stage__promotion__annee_universitaire=annee,
    ).select_related("stage__etudiant", "stage__entreprise", "stage__promotion").order_by(
        "stage__etudiant__last_name", "stage__etudiant__first_name")
    lignes = []
    for s in soutenances:
        convention = s.stage.conventions.filter(statut=Convention.Statut.SIGNEE).first()
        etudiant = s.stage.etudiant
        lignes.append([
            etudiant.last_name, etudiant.first_name, etudiant.email, annee, s.stage.type_stage,
            s.stage.entreprise.raison_sociale if s.stage.entreprise else "",
            f"{timezone.localtime(s.debut):%d/%m/%Y}" if s.debut else "",
            str(s.note).replace(".", ","), convention.numero if convention else "",
        ])
    return ecrire_csv(COLONNES_NOTES, lignes), len(lignes)
