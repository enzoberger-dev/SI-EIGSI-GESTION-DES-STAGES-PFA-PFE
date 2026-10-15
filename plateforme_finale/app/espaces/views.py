"""
Pages d'accueil de chaque rôle.

- /            : accueil, avec un lien vers chaque espace auquel la personne a droit
- /etudiant/, /encadrant/, /service-stages/, /jury/ : un espace par rôle

Règle de sécurité : on vérifie le rôle sur CHAQUE page. Une personne qui
tape l'adresse d'un espace qui n'est pas le sien reçoit un refus (erreur 403).
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from comptes import roles
from comptes.decorateurs import role_requis
from stages.models import ParametresEcole

from . import assistant as assistant_ia
from .aide import AIDE, INTRODUCTION

# Description des espaces : adresse -> (rôle exigé, titre, phrase d'accueil)
ESPACES = {
    "etudiant": (roles.ETUDIANT, "Espace étudiant",
                 "Ici, vous déclarerez votre stage et suivrez votre dossier."),
    "encadrant": (roles.ENCADRANT, "Espace encadrant",
                  "Ici, vous validerez les stages de vos étudiants et suivrez leurs livrables."),
    "coordinateur": (roles.COORDINATEUR, "Espace coordinateur de promotion",
                     "Ici, vous validerez les stages des étudiants de votre promotion (1re à 3e année)."),
    "service-stages": (roles.SERVICE_STAGES, "Espace Service Stages",
                       "Ici, vous affecterez les encadrants et émettrez les conventions."),
    "jury": (roles.JURY, "Espace jury",
             "Ici, vous indiquerez vos disponibilités et saisirez les PV de soutenance."),
}

# Liens proposés dans chaque espace : adresse de l'espace -> [(texte, nom de la page)]
LIENS = {
    "etudiant": [("Mon stage", "mon_stage")],
    "encadrant": [("Stages à valider", "stages_a_valider")],
    "coordinateur": [("Stages à valider", "stages_a_valider")],
    "service-stages": [("Tableau de bord", "tableau_de_bord"), ("Affecter les encadrants", "affectations"), ("Conventions", "conventions"),
                       ("Suivi des stages et livrables", "suivi"),
                       ("Importer depuis WebAurion", "import_webaurion"),
                       ("Importer les rendus depuis Moodle", "import_moodle"),
                       ("Soutenances", "soutenances")],
    "jury": [("Mes soutenances et disponibilités", "jury_accueil")],
}


@login_required
def accueil(request):
    """Liste les espaces auxquels la personne connectée a droit."""
    mes_espaces = [
        {"adresse": adresse, "titre": titre, "phrase": phrase}
        for adresse, (role, titre, phrase) in ESPACES.items()
        if request.user.a_le_role(role)
    ]
    return render(request, "espaces/accueil.html", {"mes_espaces": mes_espaces})


@login_required
def espace(request, adresse):
    """Affiche l'espace demandé, seulement si la personne a le rôle correspondant."""
    role, titre, phrase = ESPACES[adresse]
    if not request.user.a_le_role(role):
        raise PermissionDenied("Cet espace est réservé au rôle : " + role)
    liens = [(texte, reverse(nom)) for texte, nom in LIENS.get(adresse, [])]
    return render(request, "espaces/espace.html", {
        "titre": titre, "phrase": phrase, "role": role, "liens": liens,
    })


@login_required
def aide(request):
    """À propos et aide : à quoi sert le site et comment s'en servir. Chacun ne voit QUE les explications
    de ses propres rôles (un étudiant n'a pas à lire ce que fait un encadrant)."""
    sections = []
    for role in roles.TOUS_LES_ROLES:
        if role not in AIDE or not request.user.a_le_role(role):
            continue
        contenu = AIDE[role]
        etapes = []
        for etape in contenu["etapes"]:
            lien = etape.get("lien")
            etapes.append({**etape, "lien": (lien[0], reverse(lien[1])) if lien else None})
        sections.append({"role": role, "resume": contenu["resume"], "etapes": etapes, "faq": contenu["faq"]})
    return render(request, "espaces/aide.html", {
        "introduction": INTRODUCTION,
        "sections": sections,
        "contact": ParametresEcole.actuels().email_contact,
    })


@login_required
@require_POST
def assistant_question(request):
    """Assistant IA (bulle en bas à droite de chaque page) : répond à une question sur le site, à partir de l'aide
    du rôle de la personne. Renvoie du JSON ; rien n'est enregistré (voir docs/15-IA.md)."""
    return JsonResponse(assistant_ia.repondre(request.POST.get("question", ""), request.user))


@role_requis(roles.ETUDIANT)
@require_POST
def assistant_relecture(request):
    """Relecture du sujet de stage (appelée par le bouton de la fiche). Renvoie du JSON ; n'enregistre rien."""
    return JsonResponse(assistant_ia.relire_sujet(request.POST.get("sujet", ""), request.user))


def protection_donnees(request):
    """Page publique (sans connexion) : quelles données la plateforme conserve, pourquoi, combien de temps,
    et comment exercer ses droits. Les informations de l'école viennent des « Paramètres de l'école »."""
    return render(request, "espaces/protection_donnees.html", {"ecole": ParametresEcole.actuels()})
