"""
Commande : python manage.py envoyer_rappels [--date AAAA-MM-JJ]

Envoie les rappels de livrables (à rendre sur Moodle) dus aujourd'hui. À lancer UNE fois par jour :
- sur le PC : avec le « Planificateur de tâches » de Windows (voir app/README.md) ;
- en ligne : avec une tâche planifiée du serveur (cron).
Sans danger si elle est lancée plusieurs fois : un même rappel n'est jamais envoyé deux fois.
Le calendrier (ex. 7, 3 et 1 jours avant ; 1 et 7 jours de retard) se règle dans l'administration,
rubrique « Paramètres de l'école ».
"""

import datetime

from django.core.management.base import BaseCommand, CommandError

from stages.services import envoyer_rappels


class Command(BaseCommand):
    help = "Envoie les rappels de livrables dus aujourd'hui (une fois chacun)."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Simuler une autre date (AAAA-MM-JJ), pour tester.")

    def handle(self, *args, **options):
        jour = None
        if options["date"]:
            try:
                jour = datetime.date.fromisoformat(options["date"])
            except ValueError:
                raise CommandError("Date invalide : utilisez le format AAAA-MM-JJ.")
        resultat = envoyer_rappels(jour)
        self.stdout.write(
            f"{resultat['envoyes']} rappel(s) envoyé(s), {len(resultat['retards'])} en retard, "
            f"{resultat['erreurs']} erreur(s)."
        )
