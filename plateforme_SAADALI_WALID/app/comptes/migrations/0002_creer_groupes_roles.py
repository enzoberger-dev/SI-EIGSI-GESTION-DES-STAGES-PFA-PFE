"""
Crée un groupe Django pour chaque rôle de la plateforme (voir comptes/roles.py).

Les noms sont recopiés ici (et non importés) : une migration doit rester
identique dans le temps, même si roles.py change plus tard.
"""

from django.db import migrations

ROLES = ["Étudiant", "Encadrant", "Service Stages", "Jury"]


def creer_groupes(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nom in ROLES:
        Group.objects.get_or_create(name=nom)


def supprimer_groupes(apps, schema_editor):
    # Retour en arrière : on retire seulement les groupes créés ici
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("comptes", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(creer_groupes, supprimer_groupes),
    ]
