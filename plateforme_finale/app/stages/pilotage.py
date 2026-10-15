"""
Calculs du tableau de bord du Career Center (US-11).

Chaque étudiant inscrit est rangé dans UNE étape du parcours (voir ETAPES), de « pas encore de fiche »
jusqu'à « stage terminé ». Les chiffres sont recalculés à chaque affichage : le tableau est toujours à jour.
"""

from collections import Counter
from datetime import timedelta

from django.utils import timezone

from .models import (
    Affectation, Convention, Inscription, Livrable, Promotion, Relance, Stage, annee_universitaire_courante,
)
from soutenances.models import Soutenance

from .services import aujourdhui
from .views import etudiants_a_encadrer

# (code, libellé, ce que le Career Center doit faire — vide si rien à faire à ce stade)
ETAPES = [
    ("SANS_FICHE", "Pas encore de fiche de stage", ""),
    ("BROUILLON", "Fiche en brouillon", ""),
    ("SOUMIS", "Fiche soumise, en attente de validation", "Relancer le valideur si besoin"),
    ("REFUSE", "Fiche refusée, à corriger par l'étudiant", ""),
    ("A_GENERER", "Stage validé, convention à générer", "Générer la convention"),
    ("A_FAIRE_SIGNER", "Convention générée, à faire signer par l'école", "Faire signer, puis l'envoyer"),
    ("CHEZ_ETUDIANT", "Convention chez l'étudiant (signatures en cours)", ""),
    ("SCAN_A_VERIFIER", "Scan déposé, à vérifier", "Vérifier le scan"),
    ("EN_SUIVI", "Convention signée, stage et livrables en cours", ""),
    ("TERMINE", "Tous les livrables rendus", ""),
    ("SOUTENANCE_PLANIFIEE", "Soutenance planifiée (convocations envoyées)", ""),
    ("PV_A_VALIDER", "PV saisi, à valider", "Valider le PV et la note"),
    ("NOTE_VALIDEE", "Soutenance passée, note validée", ""),
]
LIBELLES = {code: libelle for code, libelle, _ in ETAPES}


def etape_du_stage(stage, convention, livrables, soutenance=None):
    """Étape d'un stage (None = l'étudiant n'a pas encore de fiche)."""
    if stage is None:
        return "SANS_FICHE"
    if stage.statut == Stage.Statut.BROUILLON:
        return "BROUILLON"
    if stage.statut == Stage.Statut.SOUMIS:
        return "SOUMIS"
    if stage.statut == Stage.Statut.REFUSE:
        return "REFUSE"
    if convention is None:
        return "A_GENERER"
    if convention.statut == Convention.Statut.GENEREE:
        return "A_FAIRE_SIGNER"
    if convention.statut == Convention.Statut.ENVOYEE:
        return "SCAN_A_VERIFIER" if convention.scan_signe else "CHEZ_ETUDIANT"
    if soutenance is not None:  # la soutenance prime sur le suivi des livrables
        suite = {"CONVOQUEE": "SOUTENANCE_PLANIFIEE", "PV_SAISI": "PV_A_VALIDER", "NOTEE": "NOTE_VALIDEE"}
        if soutenance.statut in suite:
            return suite[soutenance.statut]
    if livrables and all(l.statut == Livrable.Statut.RENDU for l in livrables):
        return "TERMINE"
    return "EN_SUIVI"


def annees_disponibles():
    """Années universitaires qui ont au moins une promotion, la plus récente d'abord."""
    annees = list(Promotion.objects.order_by("-annee_universitaire").values_list("annee_universitaire", flat=True).distinct())
    courante = annee_universitaire_courante()
    return annees if courante in annees else [courante, *annees]


def tableau_de_bord(annee):
    """Toutes les données du tableau de bord pour une année universitaire.

    Renvoie un dictionnaire : étapes (avec le nombre d'étudiants par année d'études), conventions et
    fiches à traiter, étudiants sans encadrant, livrables en retard et résumé des livrables."""
    inscriptions = list(
        Inscription.objects.filter(annee_universitaire=annee).select_related("etudiant", "promotion")
    )
    stages = {
        s.etudiant_id: s
        for s in Stage.objects.filter(promotion__annee_universitaire=annee).select_related(
            "entreprise", "promotion", "etudiant")
    }
    conventions = {}
    for c in Convention.objects.filter(stage__promotion__annee_universitaire=annee).exclude(
            statut=Convention.Statut.REMPLACEE).select_related("stage__etudiant"):
        conventions[c.stage_id] = c
    livrables_par_stage = {}
    for livrable in Livrable.objects.filter(stage__promotion__annee_universitaire=annee).select_related(
            "stage__etudiant"):
        livrables_par_stage.setdefault(livrable.stage_id, []).append(livrable)

    soutenances = {s.stage_id: s for s in Soutenance.objects.filter(stage__promotion__annee_universitaire=annee)}

    # Étape de chaque étudiant, comptée par année d'études
    annees_etudes = sorted({i.promotion.annee_etudes for i in inscriptions})
    compteurs = {code: Counter() for code, _, _ in ETAPES}
    etape_par_stage = {}
    for inscription in inscriptions:
        stage = stages.get(inscription.etudiant_id)
        code = etape_du_stage(
            stage, conventions.get(stage.pk) if stage else None, livrables_par_stage.get(stage.pk, []) if stage else [],
            soutenances.get(stage.pk) if stage else None,
        )
        if stage:
            etape_par_stage[stage.pk] = code
        compteurs[code][inscription.promotion.annee_etudes] += 1
    etapes = [
        {
            "code": code, "libelle": libelle, "action": action,
            "par_annee": [compteurs[code][a] for a in annees_etudes],
            "total": sum(compteurs[code].values()),
        }
        for code, libelle, action in ETAPES
    ]

    # Ce qui attend le Career Center
    aujourdhui_ = aujourdhui()
    livrables = [l for liste in livrables_par_stage.values() for l in liste]
    a_rendre = [l for l in livrables if l.statut == Livrable.Statut.A_RENDRE]
    en_retard = sorted((l for l in a_rendre if l.date_limite < aujourdhui_), key=lambda l: l.date_limite)
    avec_encadrant = set(
        Affectation.objects.filter(annee_universitaire=annee, active=True).values_list("etudiant_id", flat=True)
    )
    sans_encadrant = [
        etudiant for etudiant in etudiants_a_encadrer(annee).order_by("last_name", "first_name")
        if etudiant.pk not in avec_encadrant
    ]
    return {
        "annee": annee,
        "annees_etudes": annees_etudes,
        "nb_etudiants": len(inscriptions),
        "etapes": etapes,
        "fiches_soumises": [s for s in stages.values() if etape_par_stage.get(s.pk) == "SOUMIS"],
        "a_generer": [s for s in stages.values() if etape_par_stage.get(s.pk) == "A_GENERER"],
        "conventions_en_attente": [
            c for c in conventions.values() if c.statut in (Convention.Statut.GENEREE, Convention.Statut.ENVOYEE)
        ],
        "scans_a_verifier": [
            c for c in conventions.values() if c.statut == Convention.Statut.ENVOYEE and c.scan_signe
        ],
        "sans_encadrant": sans_encadrant,
        "pv_a_valider": [s for s in soutenances.values() if s.statut == "PV_SAISI"],
        "livrables": {
            "total": len(livrables),
            "rendus": len(livrables) - len(a_rendre),
            "a_rendre": len(a_rendre) - len(en_retard),
            "en_retard": len(en_retard),
        },
        "livrables_en_retard": en_retard,
        # relances automatiques envoyées ces 7 derniers jours (pour cette année universitaire)
        "relances_recentes": list(
            Relance.objects.filter(
                stage__promotion__annee_universitaire=annee, envoye_le__gte=timezone.now() - timedelta(days=7)
            ).select_related("stage__etudiant")[:20]
        ),
    }
