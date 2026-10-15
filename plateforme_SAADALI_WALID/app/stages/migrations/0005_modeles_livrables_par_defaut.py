"""
Livrables attendus par type de stage (valeurs de départ, HYPOTHÈSES à confirmer avec le
« guide des expériences professionnelles » de l'école). Le Career Center peut les modifier
dans l'administration (Modèles de livrables).

Les noms sont recopiés ici : une migration doit rester identique dans le temps.
"""

from django.db import migrations

# (type de stage, nom, est_rapport, calcul, jours, ordre)
MODELES = [
    ("Découverte", "Rapport de stage", True, "FIN", 14, 1),
    ("Initiative personnelle", "Rapport de stage", True, "FIN", 14, 1),
    ("Technicien", "Autoévaluation intermédiaire", False, "MILIEU", 0, 1),
    ("Technicien", "Rapport de stage", True, "FIN", 14, 2),
    ("Assistant-Ingénieur", "Rapport de stage", True, "FIN", 14, 1),
    ("Fin d'Études", "Plan directeur", False, "MILIEU", 0, 1),
    ("Fin d'Études", "Rapport de stage", True, "FIN", 14, 2),
]


def creer_modeles(apps, schema_editor):
    ModeleLivrable = apps.get_model("stages", "ModeleLivrable")
    for type_stage, nom, est_rapport, calcul, jours, ordre in MODELES:
        ModeleLivrable.objects.get_or_create(
            type_stage=type_stage, nom=nom,
            defaults={"est_rapport": est_rapport, "calcul": calcul, "jours": jours, "ordre": ordre},
        )


def supprimer_modeles(apps, schema_editor):
    ModeleLivrable = apps.get_model("stages", "ModeleLivrable")
    for type_stage, nom, *_ in MODELES:
        ModeleLivrable.objects.filter(type_stage=type_stage, nom=nom).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("stages", "0004_alter_historique_action_livrable_depotlivrable_and_more"),
    ]

    operations = [
        migrations.RunPython(creer_modeles, supprimer_modeles),
    ]
