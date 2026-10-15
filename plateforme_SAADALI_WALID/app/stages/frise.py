"""
Frise des étapes de la page « Mon stage » (lot 8) : où en est l'étudiant, et quelle est sa prochaine action.

Pas de base de données ici : on reçoit les objets déjà chargés et on renvoie des données simples
pour le gabarit. C'est ce qui rend la logique facile à tester (voir stages/tests_frise.py).
Les 5 étapes suivent le processus décidé (docs/02-Processus-BPMN.md).
"""

from dataclasses import dataclass

LIBELLES = ["Fiche de stage", "Validation", "Convention", "Suivi et livrables", "Soutenance"]


@dataclass
class Etape:
    libelle: str
    etat: str   # "fait", "courant", "refus" ou "a-venir"
    indice: int  # 1, 2, 3... (sert au décalage des animations)


@dataclass
class ProchaineAction:
    titre: str
    texte: str
    ok: bool = False          # vrai = tout est en ordre (bandeau vert)
    bouton: str = ""          # texte du bouton, vide = pas de bouton
    nom_url: str = ""         # nom de la page vers laquelle pointe le bouton ("#ancre" = lien dans la page)


def _toutes_rendues(livrables):
    return bool(livrables) and all(l.statut == "RENDU" for l in livrables)


def calculer(stage, convention, livrables, soutenance):
    """Renvoie (liste d'étapes, prochaine action). `stage` peut être None (pas encore déclaré)."""
    livrables = list(livrables or [])
    courant = 0          # numéro (0 à 4) de l'étape en cours ; 5 = tout est terminé
    refus = False

    statut = stage.statut if stage else None
    if statut == "REFUSE":
        refus = True
    elif statut == "SOUMIS":
        courant = 1
    elif statut == "VALIDE":
        courant = 2
        if convention is not None and convention.statut == "SIGNEE":
            courant = 3
            if _toutes_rendues(livrables):
                courant = 4
                if soutenance is not None and soutenance.statut == "NOTEE":
                    courant = 5

    etapes = []
    for i, libelle in enumerate(LIBELLES):
        if i < courant:
            etat = "fait"
        elif i == courant:
            etat = "refus" if refus else "courant"
        else:
            etat = "a-venir"
        etapes.append(Etape(libelle, etat, i + 1))

    return etapes, _action(stage, convention, courant, refus, soutenance)


def _action(stage, convention, courant, refus, soutenance):
    if stage is None:
        return ProchaineAction("Déclarez votre stage",
                               "Renseignez l'entreprise, le sujet et les dates : c'est la première étape.",
                               bouton="Déclarer mon stage", nom_url="modifier_mon_stage")
    if refus:
        return ProchaineAction("Votre fiche a été refusée",
                               "Lisez le motif dans l'historique plus bas, corrigez, puis soumettez de nouveau.",
                               bouton="Corriger ma fiche", nom_url="modifier_mon_stage")
    if courant == 0:
        return ProchaineAction("Terminez et soumettez votre fiche",
                               "Votre brouillon est enregistré. Soumettez-le quand il est complet.",
                               bouton="Modifier ma fiche", nom_url="modifier_mon_stage")
    if courant == 1:
        return ProchaineAction("Votre fiche est en cours de validation",
                               "Votre encadrant l'examine. Vous serez prévenu de sa décision par e-mail.")
    if courant == 2:
        if convention is None:
            return ProchaineAction("Stage validé : la convention se prépare",
                                   "Le Career Center prépare votre convention. Rien à faire pour l'instant.")
        if convention.statut == "ENVOYEE":
            return ProchaineAction("Signez votre convention",
                                   "Téléchargez-la, faites-la signer par l'entreprise et signez-la, puis déposez le scan.",
                                   bouton="Déposer le scan", nom_url="#convention")
        return ProchaineAction("Votre convention est en cours de signature",
                               "Le Career Center la fait signer par le directeur des études, puis vous l'envoie.")
    if courant == 3:
        return ProchaineAction("Votre stage est en cours",
                               "Rendez vos livrables sur Moodle avant les dates limites indiquées plus bas.")
    if courant == 4:
        if soutenance is not None and soutenance.debut and soutenance.statut in ("CONVOQUEE", "PV_SAISI"):
            return ProchaineAction("Préparez votre soutenance",
                                   "Votre créneau est confirmé : retrouvez la date, la salle et le jury plus bas.")
        return ProchaineAction("Tous vos livrables sont rendus",
                               "Il reste à planifier votre soutenance. Vous serez convoqué par e-mail.")
    return ProchaineAction("Dossier terminé",
                           "Votre soutenance est notée. Félicitations pour votre stage.", ok=True)
