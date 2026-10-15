"""
Commande : python manage.py donnees_personnelles adresse@exemple.ma

Affiche (en JSON) tout ce que la plateforme détient sur une personne : à utiliser pour répondre à une demande
d'accès (loi 09-08). La sortie contient des données personnelles : à transmettre uniquement à la personne
concernée, après avoir vérifié son identité (voir docs/11-Protection-des-donnees.md).
"""

import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from stages.donnees import donnees_personnelles


class Command(BaseCommand):
    help = "Affiche toutes les données détenues sur une personne (droit d'accès)."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Adresse e-mail du compte.")

    def handle(self, *args, **options):
        utilisateur = get_user_model().objects.filter(email__iexact=options["email"].strip()).first()
        if utilisateur is None:
            raise CommandError("Aucun compte avec cette adresse e-mail.")
        self.stdout.write(json.dumps(donnees_personnelles(utilisateur), ensure_ascii=False, indent=2, default=str))
