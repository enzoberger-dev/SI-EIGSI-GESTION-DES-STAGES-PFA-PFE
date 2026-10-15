"""
Commande : python manage.py sauvegarder [--garder N] [--dossier CHEMIN]

Crée une archive ZIP datée de la base de données et des fichiers déposés (conventions, scans), dans le
dossier des sauvegardes (réglage DJANGO_BACKUP_DIR, par défaut app/sauvegardes/), et ne garde que les N plus
récentes (14 par défaut). À lancer chaque jour, comme envoyer_rappels (voir app/README.md). Pensez à copier
régulièrement ce dossier sur une AUTRE machine : une sauvegarde au même endroit que le site ne protège pas
d'une panne de la machine.
"""

from django.core.management.base import BaseCommand, CommandError

from stages.sauvegarde import ErreurSauvegarde, sauvegarder


class Command(BaseCommand):
    help = "Sauvegarde la base de données et les fichiers déposés dans une archive ZIP datée."

    def add_arguments(self, parser):
        parser.add_argument("--garder", type=int, default=14, help="Nombre de sauvegardes à conserver (14 par défaut).")
        parser.add_argument("--dossier", help="Dossier où ranger l'archive (par défaut : réglage DJANGO_BACKUP_DIR).")

    def handle(self, *args, **options):
        try:
            archive = sauvegarder(dossier=options["dossier"], garder=options["garder"])
        except ErreurSauvegarde as erreur:
            raise CommandError(str(erreur))
        taille = archive.stat().st_size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde créée : {archive} ({taille:.1f} Mo)."))
