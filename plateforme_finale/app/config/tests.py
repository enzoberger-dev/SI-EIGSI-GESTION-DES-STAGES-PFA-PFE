"""
Tests de la configuration (Lot 7) : adresse de la base de données et règles de mise en ligne.
Lancer : python manage.py test
"""

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

from .baseurl import lire_url_base

BASE_DIR = Path(__file__).resolve().parent.parent
CLE = "cle-de-test-" + "x" * 60   # 70 caractères, jamais utilisée ailleurs


class AdresseBaseTests(SimpleTestCase):
    def test_postgres_complet(self):
        r = lire_url_base("postgres://stages:p%40ss%2Fword@db.ecole.test:5433/gestion?sslmode=require")
        self.assertEqual(r["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual((r["NAME"], r["USER"], r["HOST"], r["PORT"]), ("gestion", "stages", "db.ecole.test", "5433"))
        self.assertEqual(r["PASSWORD"], "p@ss/word")          # caractères spéciaux décodés
        self.assertEqual(r["OPTIONS"], {"sslmode": "require"})
        self.assertEqual(r["CONN_MAX_AGE"], 60)

    def test_postgres_sans_port_ni_options(self):
        r = lire_url_base("postgresql://u:p@localhost/ma_base")
        self.assertEqual((r["PORT"], r["NAME"]), ("", "ma_base"))
        self.assertNotIn("OPTIONS", r)

    def test_sqlite(self):
        self.assertEqual(lire_url_base("sqlite:///C:/donnees/db.sqlite3")["NAME"], "C:/donnees/db.sqlite3")
        self.assertEqual(lire_url_base("sqlite:////var/lib/stages/db.sqlite3")["NAME"], "/var/lib/stages/db.sqlite3")

    def test_adresses_invalides(self):
        for url in ("mysql://u:p@h/db", "postgres://u:p@/db", "postgres://u:p@h", "sqlite://", "pas une adresse"):
            with self.assertRaises(ValueError, msg=url):
                lire_url_base(url)


class ReglesDeMiseEnLigneTests(SimpleTestCase):
    """Chaque test lance « manage.py » dans un processus séparé avec ses propres variables d'environnement."""

    def lancer(self, *arguments, **variables):
        env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_") and k != "DATABASE_URL"}
        env.update(variables)
        return subprocess.run([sys.executable, "manage.py", *arguments], cwd=BASE_DIR, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def en_ligne(self, **modifs):
        base = {"DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": CLE, "DJANGO_ALLOWED_HOSTS": "stages.ecole.test",
                "DJANGO_SITE_URL": "https://stages.ecole.test"}
        base.update(modifs)
        return {k: v for k, v in base.items() if v is not None}

    def test_sur_le_pc_rien_n_est_exige(self):
        self.assertEqual(self.lancer("check").returncode, 0)

    def test_en_ligne_avec_une_configuration_complete_aucune_alerte(self):
        resultat = self.lancer("check", "--deploy", **self.en_ligne(DATABASE_URL="postgres://u:p@localhost/db"))
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("no issues", resultat.stdout + resultat.stderr)

    def test_refus_sans_cle_secrete_ou_avec_la_cle_de_developpement(self):
        for cle in (None, "dev-uniquement-cle-non-securisee-ne-pas-utiliser-en-ligne", "trop-courte"):
            resultat = self.lancer("check", **self.en_ligne(DJANGO_SECRET_KEY=cle))
            self.assertNotEqual(resultat.returncode, 0, cle)
            self.assertIn("DJANGO_SECRET_KEY", resultat.stderr)

    def test_refus_sans_hotes_autorises(self):
        resultat = self.lancer("check", **self.en_ligne(DJANGO_ALLOWED_HOSTS=None))
        self.assertNotEqual(resultat.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", resultat.stderr)

    def test_refus_d_une_adresse_du_site_sans_https(self):
        for adresse in (None, "http://stages.ecole.test"):
            resultat = self.lancer("check", **self.en_ligne(DJANGO_SITE_URL=adresse))
            self.assertNotEqual(resultat.returncode, 0, adresse)
            self.assertIn("DJANGO_SITE_URL", resultat.stderr)

    def test_adresse_de_base_invalide_donne_une_erreur_claire(self):
        resultat = self.lancer("check", DATABASE_URL="mysql://u:p@h/db")
        self.assertNotEqual(resultat.returncode, 0)
        self.assertIn("DATABASE_URL", resultat.stderr)
