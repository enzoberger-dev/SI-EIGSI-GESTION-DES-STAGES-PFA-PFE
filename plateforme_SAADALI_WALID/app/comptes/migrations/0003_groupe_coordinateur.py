"""
Ajoute le rôle « Coordinateur de promotion » (Lot 1).
Le coordinateur valide les stages de 1re, 2e et 3e année (hypothèse à confirmer).
"""

from django.db import migrations

NOM = "Coordinateur de promotion"


def creer_groupe(apps, schema_editor):
    apps.get_model("auth", "Group").objects.get_or_create(name=NOM)


def supprimer_groupe(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=NOM).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("comptes", "0002_creer_groupes_roles"),
    ]

    operations = [
        migrations.RunPython(creer_groupe, supprimer_groupe),
    ]
