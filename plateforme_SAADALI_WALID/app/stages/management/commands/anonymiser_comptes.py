"""
Commande : python manage.py anonymiser_comptes [--annees 10] [--oui]

Anonymise les comptes d'étudiants dont la dernière inscription date de plus de N années (10 par défaut, comme
la durée de conservation de la convention) : nom et e-mail remplacés, compte désactivé, coordonnées du tuteur,
texte du PV et fichiers de convention effacés. C'est IRRÉVERSIBLE : sans --oui, la commande liste seulement les
comptes concernés. Faites une sauvegarde avant (manage.py sauvegarder). À lancer une fois par an environ.
"""

from django.core.management.base import BaseCommand

from stages.donnees import DUREE_CONSERVATION_ANS, anciens_comptes, anonymiser


class Command(BaseCommand):
    help = "Anonymise les comptes d'étudiants dont le dossier a dépassé la durée de conservation."

    def add_arguments(self, parser):
        parser.add_argument("--annees", type=int, default=DUREE_CONSERVATION_ANS,
                            help=f"Durée de conservation en années ({DUREE_CONSERVATION_ANS} par défaut).")
        parser.add_argument("--oui", action="store_true", help="Confirme l'anonymisation (irréversible).")

    def handle(self, *args, **options):
        comptes = anciens_comptes(options["annees"])
        if not comptes:
            self.stdout.write(f"Aucun compte à anonymiser (dernière inscription de plus de {options['annees']} ans).")
            return
        self.stdout.write(f"{len(comptes)} compte(s) dont la dernière inscription date de plus de {options['annees']} ans :")
        for compte in comptes:
            self.stdout.write(f"  - {compte.email}")
        if not options["oui"]:
            self.stdout.write("Simulation : rien n'a été modifié. Pour anonymiser vraiment (irréversible) : ajoutez --oui "
                              "(après une sauvegarde).")
            return
        fichiers = sum(anonymiser(compte) for compte in comptes)
        self.stdout.write(self.style.SUCCESS(f"{len(comptes)} compte(s) anonymisé(s), {fichiers} fichier(s) supprimé(s)."))
