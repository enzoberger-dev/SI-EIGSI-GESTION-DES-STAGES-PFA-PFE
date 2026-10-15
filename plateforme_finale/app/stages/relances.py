"""
Relances automatiques (Lot 5, US-06) : remplacent les relances que le Career Center faisait à la main.

Deux attentes sont surveillées :
- une fiche de stage SOUMISE que le valideur (encadrant ou coordinateur) n'a pas encore décidée ;
- une convention ENVOYÉE à l'étudiant dont le scan signé n'a pas encore été déposé.

Une relance part quand l'attente atteint un des délais réglés dans « Paramètres de l'école » (ex. 3 et 7 jours).
Elle s'arrête d'elle-même dès que l'action est faite (la condition n'est plus vraie) et n'est jamais envoyée
deux fois (table Relance). Le Career Center reçoit un récapitulatif.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Convention, Historique, ParametresEcole, Relance, Stage
from .services import aujourdhui


def lien(nom_de_page):
    """Adresse complète d'une page, pour la mettre dans un e-mail (SITE_URL est réglé dans settings.py)."""
    return settings.SITE_URL.rstrip("/") + reverse(nom_de_page)


def _attentes():
    """Toutes les attentes en cours : (type, stage, début de l'attente, destinataire ou None, page du lien)."""
    attentes = []
    soumis = Stage.objects.filter(statut=Stage.Statut.SOUMIS).select_related("etudiant", "promotion", "entreprise")
    for stage in soumis:
        derniere = stage.historique.filter(action=Historique.Action.SOUMISSION).order_by("-date").first()
        depuis = derniere.date if derniere else stage.modifie_le
        attentes.append((Relance.Type.VALIDATION, stage, depuis, stage.valideur(), "stages_a_valider"))
    envoyees = Convention.objects.filter(statut=Convention.Statut.ENVOYEE, scan_signe="").select_related(
        "stage__etudiant", "stage__promotion")
    for convention in envoyees:
        depuis = convention.envoyee_le or convention.cree_le
        attentes.append((Relance.Type.SCAN, convention.stage, depuis, convention.stage.etudiant, "mon_stage"))
    return attentes


def _texte(type_, stage, jours, page):
    nom = stage.etudiant.get_full_name() or stage.etudiant.email
    if type_ == Relance.Type.VALIDATION:
        sujet = f"Rappel : fiche de stage de {nom} en attente de votre décision"
        corps = (f"Bonjour,\n\nLa fiche de stage de {nom} ({stage.type_stage}) attend votre décision depuis "
                 f"{jours} jour{'s' if jours > 1 else ''}.\n")
    else:
        sujet = "Rappel : déposez le scan de votre convention de stage signée"
        corps = (f"Bonjour,\n\nVotre convention de stage vous a été envoyée il y a {jours} jour{'s' if jours > 1 else ''}. "
                 f"Faites-la signer par l'entreprise, signez-la, puis déposez le scan sur la plateforme.\n")
    return sujet, corps + f"\nAccès direct : {lien(page)}\n"


def envoyer_relances(jour=None):
    """Envoie les relances dues à la date donnée (par défaut aujourd'hui).

    - une relance par délai atteint, jamais deux fois la même (même si la commande est relancée) ;
      si la commande n'a pas tourné pendant plusieurs jours, un seul message rattrape le retard ;
    - un e-mail qui échoue ne bloque pas les autres : il sera retenté au prochain passage ;
    - le Career Center reçoit un récapitulatif, y compris des attentes sans destinataire.
    Renvoie {"envoyes": [(type, stage, jours, destinataire)], "sans_destinataire": [stage], "erreurs": n}."""
    jour = jour or aujourdhui()
    ecole = ParametresEcole.actuels()
    delais = ecole.delais_relances()
    resultat = {"envoyes": [], "sans_destinataire": [], "erreurs": 0}

    for type_, stage, depuis, destinataire, page in _attentes():
        jours = (jour - timezone.localtime(depuis).date()).days
        dus = [d for d in delais if jours >= d]
        if not dus:
            continue
        deja = set(Relance.objects.filter(stage=stage, type=type_, depuis=depuis).values_list("delai", flat=True))
        nouveaux = [d for d in dus if d not in deja]
        if not nouveaux:
            continue
        if destinataire is None:  # aucun valideur : personne à relancer, le Career Center est prévenu
            resultat["sans_destinataire"].append(stage)
            continue
        sujet, corps = _texte(type_, stage, jours, page)
        try:
            with transaction.atomic():  # si l'envoi échoue, rien n'est enregistré : il sera retenté
                for d in nouveaux:
                    Relance.objects.create(stage=stage, type=type_, depuis=depuis, delai=d,
                                           destinataire=destinataire.email)
                send_mail(sujet, corps, None, [destinataire.email])
        except Exception:
            resultat["erreurs"] += 1
            continue
        resultat["envoyes"].append((type_, stage, jours, destinataire))

    if resultat["envoyes"] or resultat["sans_destinataire"]:
        lignes = [
            f"- {Relance.Type(t).label} : {s.etudiant.get_full_name() or s.etudiant.email}, "
            f"{j} jour(s) d'attente, relance envoyée à {d.get_full_name() or d.email}"
            for t, s, j, d in resultat["envoyes"]
        ] + [
            f"- ATTENTION, personne à relancer pour {s.etudiant.get_full_name() or s.etudiant.email} "
            f"(aucun valideur désigné)" for s in resultat["sans_destinataire"]
        ]
        send_mail("Récapitulatif des relances", "Bonjour,\n\n" + "\n".join(lignes) + "\n",
                  None, [ecole.email_contact])
    return resultat
