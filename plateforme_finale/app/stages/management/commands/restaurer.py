"""
Commande : python manage.py restaurer ARCHIVE.zip [--oui]

Remet une sauvegarde en place (base de données SQLite et fichiers déposés). ATTENTION : cela REMPLACE la base
actuelle. Sans --oui, la commande dit seulement ce qu'elle ferait. Avant d'écraser, elle vérifie l'archive et
copie la base actuelle dans le dossier des sauvegardes (« avant-restauration-… »). Arrêtez le site avant.
Pour PostgreSQL, la restauration se fait avec « pg_restore » (voir docs/12-Mise-en-ligne.md).
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from stages.sauvegarde import ErreurSauvegarde, restaurer_sqlite


class Command(BaseCommand):
    help = "Restaure une sauvegarde (SQLite et fichiers déposés). Remplace la base actuelle."

    def add_arguments(self, parser):
        parser.add_argument("archive", help="Chemin de l'archive ZIP créée par « sauvegarder ».")
        parser.add_argument("--oui", action="store_true", help="Confirme le remplacement de la base actuelle.")

    def handle(self, *args, **options):
        base = settings.DATABASES["default"]
        if not base["ENGINE"].endswith("sqlite3"):
            raise CommandError(
                "La restauration automatique ne concerne que SQLite. Pour PostgreSQL : décompressez l'archive, "
                "arrêtez le site, puis lancez « pg_restore --clean --no-owner --dbname NOM_DE_LA_BASE base.dump » "
                "et recopiez le dossier uploads/ (voir docs/12-Mise-en-ligne.md)."
            )
        chemin_base = str(base["NAME"])
        if not options["oui"]:
            self.stdout.write(
                f"Simulation : la base « {chemin_base} » serait remplacée par celle de « {options['archive']} » et les "
                f"fichiers déposés remis dans « {settings.MEDIA_ROOT} ». Rien n'a été modifié.\n"
                "Pour le faire vraiment (site arrêté) : ajoutez --oui."
            )
            return
        try:
            copie, nb = restaurer_sqlite(options["archive"], chemin_base, settings.MEDIA_ROOT, settings.BACKUP_DIR)
        except ErreurSauvegarde as erreur:
            raise CommandError(str(erreur))
        if copie:
            self.stdout.write(f"Ancienne base conservée dans : {copie}")
        self.stdout.write(self.style.SUCCESS(f"Restauration terminée : base remplacée, {nb} fichier(s) déposé(s) remis."))
