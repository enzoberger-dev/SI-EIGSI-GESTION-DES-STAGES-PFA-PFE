"""Test de la commande `taches_quotidiennes` (lot 8) : elle lance les deux tâches et signale un échec sans arrêter l'autre."""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class TachesQuotidiennesTests(TestCase):
    def test_lance_rappels_puis_relances(self):
        sortie = StringIO()
        call_command("taches_quotidiennes", stdout=sortie)
        texte = sortie.getvalue()
        self.assertIn("== envoyer_rappels", texte)
        self.assertIn("== envoyer_relances", texte)
        self.assertLess(texte.index("envoyer_rappels"), texte.index("envoyer_relances"))

    def test_date_simulee_acceptee(self):
        call_command("taches_quotidiennes", "--date", "2026-10-20", stdout=StringIO())

    def test_une_tache_en_echec_n_arrete_pas_l_autre(self):
        appels = []

        def faux_appel(nom, *args, **options):
            appels.append(nom)
            if nom == "envoyer_rappels":
                raise RuntimeError("panne simulée")

        with mock.patch("stages.management.commands.taches_quotidiennes.call_command", faux_appel):
            with self.assertRaises(CommandError):
                call_command("taches_quotidiennes", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(appels, ["envoyer_rappels", "envoyer_relances"])   # la seconde a bien tourné
