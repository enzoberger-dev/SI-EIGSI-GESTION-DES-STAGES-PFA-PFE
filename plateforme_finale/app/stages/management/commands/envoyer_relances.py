"""
Commande : python manage.py envoyer_relances [--date AAAA-MM-JJ]

Relance les valideurs qui n'ont pas décidé une fiche de stage, et les étudiants qui n'ont pas déposé le
scan de leur convention signée, et les membres du jury qui n'ont pas répondu au sondage de
disponibilités des soutenances (délais réglés dans l'administration, « Paramètres de l'école »).
À lancer UNE fois par jour, comme envoyer_rappels (voir app/README.md). Sans danger si elle est lancée
plusieurs fois : une même relance n'est jamais envoyée deux fois.
"""

import datetime

from django.core.management.base import BaseCommand, CommandError

from soutenances.services import envoyer_relances_jury
from stages.relances import envoyer_relances


class Command(BaseCommand):
    help = "Envoie les relances dues aujourd'hui (une fois chacune)."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Simuler une autre date (AAAA-MM-JJ), pour tester.")

    def handle(self, *args, **options):
        jour = None
        if options["date"]:
            try:
                jour = datetime.date.fromisoformat(options["date"])
            except ValueError:
                raise CommandError("Date invalide : utilisez le format AAAA-MM-JJ.")
        resultat = envoyer_relances(jour)
        relances_jury = envoyer_relances_jury(jour)  # jurys qui n'ont pas répondu au sondage de disponibilités
        self.stdout.write(
            f"{len(resultat['envoyes'])} relance(s) envoyée(s), "
            f"{len(resultat['sans_destinataire'])} sans destinataire, {resultat['erreurs']} erreur(s) ; "
            f"{relances_jury} relance(s) de jury."
        )
