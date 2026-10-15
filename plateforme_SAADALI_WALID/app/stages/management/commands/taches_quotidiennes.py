"""
Commande : python manage.py taches_quotidiennes [--date AAAA-MM-JJ]

Lance en une fois les deux tâches du jour : les rappels de livrables (envoyer_rappels), puis les relances
(envoyer_relances). C'est la SEULE commande à planifier une fois par jour :
- sur le PC : « Planificateur de tâches » de Windows (voir app/README.md) ;
- en ligne : une tâche planifiée du serveur (cron).
Sans danger si elle est lancée plusieurs fois : un même message n'est jamais envoyé deux fois.
Si une des deux tâches échoue, l'autre est quand même lancée, et la commande se termine en erreur
(le planificateur peut alors le signaler).
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

TACHES = ("envoyer_rappels", "envoyer_relances")


class Command(BaseCommand):
    help = "Envoie les rappels de livrables puis les relances du jour."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Simuler une autre date (AAAA-MM-JJ), pour tester.")

    def handle(self, *args, **options):
        echecs = []
        for nom in TACHES:
            self.stdout.write(f"== {nom}")
            arguments = {"date": options["date"]} if options["date"] else {}
            try:
                call_command(nom, stdout=self.stdout, **arguments)
            except Exception as erreur:  # une tâche en panne ne doit pas empêcher l'autre
                echecs.append(nom)
                self.stderr.write(f"{nom} : échec ({erreur})")
        if echecs:
            raise CommandError("Tâche(s) en échec : " + ", ".join(echecs))
