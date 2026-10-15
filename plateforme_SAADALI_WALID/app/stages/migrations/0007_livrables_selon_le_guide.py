"""
Remet les livrables en conformité avec la réalité : ils sont rendus sur Moodle.

1. Les statuts de l'ancienne version (déposé / validé / à corriger) deviennent « rendu » ou « à rendre ».
2. Les modèles de livrables par type de stage sont refaits d'après le « Guide des stages et des
   expériences professionnelles 2025-2026 » (livret 1) et les indications de Walid :
   - le rapport de stage est dû le 15 septembre de l'année du stage (le guide indique le 14 septembre
     pour 2026 ; la date est modifiable dans l'administration) ;
   - 4e année : plan directeur 3 semaines après le début ; évaluation des compétences (signée par
     l'entreprise) en même temps que le rapport ;
   - 5e année : plan directeur 4 semaines après le début ; évaluation des compétences avec le rapport.
   Le plan et le support de soutenance de 5e année dépendent de la date de soutenance (Lot 6).
Les noms sont recopiés ici : une migration doit rester identique dans le temps.
"""

from django.db import migrations

# (type de stage, nom, est_rapport, calcul, mois, jour, jours, ordre)
MODELES = [
    ("Découverte", "Rapport de stage", True, "FIXE", 9, 15, 0, 1),
    ("Initiative personnelle", "Rapport de stage", True, "FIXE", 9, 15, 0, 1),
    ("Technicien", "Rapport de stage", True, "FIXE", 9, 15, 0, 1),
    ("Assistant-Ingénieur", "Plan directeur", False, "DEBUT", None, None, 21, 1),
    ("Assistant-Ingénieur", "Rapport de stage", True, "FIXE", 9, 15, 0, 2),
    ("Assistant-Ingénieur", "Évaluation des compétences (tuteur entreprise)", False, "FIXE", 9, 15, 0, 3),
    ("Fin d'Études", "Plan directeur", False, "DEBUT", None, None, 28, 1),
    ("Fin d'Études", "Rapport de stage", True, "FIXE", 9, 15, 0, 2),
    ("Fin d'Études", "Évaluation des compétences (tuteur entreprise)", False, "FIXE", 9, 15, 0, 3),
]


def convertir(apps, schema_editor):
    Livrable = apps.get_model("stages", "Livrable")
    Livrable.objects.filter(statut__in=["DEPOSE", "VALIDE"]).update(statut="RENDU")
    Livrable.objects.filter(statut__in=["A_DEPOSER", "A_CORRIGER"]).update(statut="A_RENDRE")

    ModeleLivrable = apps.get_model("stages", "ModeleLivrable")
    ModeleLivrable.objects.all().delete()  # les anciens modèles étaient des valeurs de départ
    for type_stage, nom, est_rapport, calcul, mois, jour, jours, ordre in MODELES:
        ModeleLivrable.objects.create(
            type_stage=type_stage, nom=nom, est_rapport=est_rapport, calcul=calcul,
            mois=mois, jour=jour, jours=jours, ordre=ordre,
        )


def ne_rien_faire(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("stages", "0006_remove_evaluationrapport_evaluateur_and_more"),
    ]

    operations = [
        migrations.RunPython(convertir, ne_rien_faire),
    ]
