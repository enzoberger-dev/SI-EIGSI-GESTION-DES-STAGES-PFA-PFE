"""
Tests de la sauvegarde et de la restauration (Lot 7). Lancer : python manage.py test
"""

import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase, override_settings

from .sauvegarde import BASE_SQLITE, ErreurSauvegarde, restaurer_sqlite, sauvegarder


def requete(chemin, sql):
    """Lit une base SQLite puis ferme la connexion (sous Windows, un fichier ouvert ne peut pas être supprimé)."""
    with closing(sqlite3.connect(chemin)) as connexion:
        return connexion.execute(sql).fetchall()


class SauvegardeBase(TransactionTestCase):
    """Sans transaction englobante (TransactionTestCase) : comme en vrai, la commande de sauvegarde lit une
    base dont les données sont enregistrées. Ces tests passent donc après les autres."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        racine = Path(self.tmp.name)
        self.media = racine / "uploads"
        self.dossier = racine / "sauvegardes"
        (self.media / "conventions" / "7").mkdir(parents=True)
        (self.media / "conventions" / "7" / "convention.pdf").write_bytes(b"%PDF-1.4 une convention")
        reglages = override_settings(MEDIA_ROOT=self.media, BACKUP_DIR=self.dossier)
        reglages.enable()
        self.addCleanup(reglages.disable)
        get_user_model().objects.create_user("a@example.test", "x", first_name="Alice")
        get_user_model().objects.create_user("b@example.test", "x", first_name="Bob")


class SauvegarderTests(SauvegardeBase):
    def test_archive_avec_la_base_et_les_fichiers_deposes(self):
        archive = sauvegarder()
        self.assertEqual(archive.parent, self.dossier)
        self.assertRegex(archive.name, r"^sauvegarde-\d{8}-\d{6}\.zip$")
        with zipfile.ZipFile(archive) as z:
            noms = z.namelist()
            self.assertIn(BASE_SQLITE, noms)
            self.assertIn("uploads/conventions/7/convention.pdf", noms)
            self.assertIn("LISEZMOI.txt", noms)
            self.assertEqual(z.read("uploads/conventions/7/convention.pdf"), b"%PDF-1.4 une convention")
            copie = Path(self.tmp.name) / "copie.sqlite3"
            copie.write_bytes(z.read(BASE_SQLITE))
        emails = {e for (e,) in requete(copie, "SELECT email FROM comptes_utilisateur")}
        self.assertEqual(emails, {"a@example.test", "b@example.test"})   # la base sauvegardée contient bien nos comptes

    def test_aucun_fichier_temporaire_ne_reste(self):
        sauvegarder()
        self.assertEqual([p.suffix for p in self.dossier.iterdir()], [".zip"])

    def test_deux_sauvegardes_la_meme_seconde_ne_s_ecrasent_pas(self):
        instant = datetime(2027, 1, 1, 12, 0, 0)
        premiere = sauvegarder(maintenant=instant)
        seconde = sauvegarder(maintenant=instant)
        self.assertNotEqual(premiere, seconde)
        self.assertTrue(premiere.exists() and seconde.exists())

    def test_rotation_garde_les_plus_recentes_et_ne_touche_pas_aux_autres_fichiers(self):
        self.dossier.mkdir()
        (self.dossier / "notes-importantes.txt").write_text("à garder")
        for jour in range(1, 6):
            sauvegarder(maintenant=datetime(2027, 1, jour, 3, 0, 0), garder=3)
        restantes = sorted(p.name for p in self.dossier.glob("sauvegarde-*.zip"))
        self.assertEqual(restantes, ["sauvegarde-20270103-030000.zip", "sauvegarde-20270104-030000.zip",
                                     "sauvegarde-20270105-030000.zip"])
        self.assertTrue((self.dossier / "notes-importantes.txt").exists())

    def test_garder_zero_refuse(self):
        with self.assertRaises(ErreurSauvegarde):
            sauvegarder(garder=0)

    def test_sans_fichiers_deposes(self):
        with override_settings(MEDIA_ROOT=Path(self.tmp.name) / "inexistant"):
            with zipfile.ZipFile(sauvegarder()) as z:
                self.assertEqual(sorted(z.namelist()), ["LISEZMOI.txt", BASE_SQLITE])

    def test_commande_sauvegarder(self):
        sortie = StringIO()
        call_command("sauvegarder", "--garder", "2", stdout=sortie)
        self.assertIn("Sauvegarde créée", sortie.getvalue())
        with self.assertRaises(CommandError):
            call_command("sauvegarder", "--garder", "0")


class RestaurerTests(SauvegardeBase):
    def preparer_archive(self, membres):
        archive = Path(self.tmp.name) / "a-restaurer.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for nom, contenu in membres.items():
                z.writestr(nom, contenu)
        return archive

    def base_sqlite(self, valeur):
        chemin = Path(self.tmp.name) / f"modele-{valeur}.sqlite3"
        connexion = sqlite3.connect(chemin)
        connexion.execute("CREATE TABLE t (v TEXT)")
        connexion.execute("INSERT INTO t VALUES (?)", (valeur,))
        connexion.commit()
        connexion.close()
        return chemin.read_bytes()

    def test_aller_retour_complet(self):
        archive = sauvegarder()
        cible = Path(self.tmp.name) / "restauree.sqlite3"
        cible.write_bytes(self.base_sqlite("ancienne"))
        autre_media = Path(self.tmp.name) / "uploads-restaures"
        copie, nb = restaurer_sqlite(archive, cible, autre_media, self.dossier)
        self.assertEqual(nb, 1)
        self.assertEqual((autre_media / "conventions" / "7" / "convention.pdf").read_bytes(), b"%PDF-1.4 une convention")
        emails = {e for (e,) in requete(cible, "SELECT email FROM comptes_utilisateur")}
        self.assertEqual(emails, {"a@example.test", "b@example.test"})
        # l'ancienne base a été mise de côté avant d'être remplacée
        self.assertTrue(copie.exists())
        self.assertEqual(requete(copie, "SELECT v FROM t")[0], ("ancienne",))

    def test_les_fichiers_existants_non_presents_dans_l_archive_ne_sont_pas_supprimes(self):
        archive = self.preparer_archive({BASE_SQLITE: self.base_sqlite("x"), "uploads/a.pdf": b"A"})
        dossier = Path(self.tmp.name) / "up"
        dossier.mkdir()
        (dossier / "autre.pdf").write_bytes(b"B")
        restaurer_sqlite(archive, Path(self.tmp.name) / "b.sqlite3", dossier, self.dossier)
        self.assertEqual((dossier / "autre.pdf").read_bytes(), b"B")
        self.assertEqual((dossier / "a.pdf").read_bytes(), b"A")

    def test_chemin_dangereux_refuse_sans_rien_ecraser(self):
        archive = self.preparer_archive({BASE_SQLITE: self.base_sqlite("neuve"), "uploads/../../evil.txt": b"X"})
        cible = Path(self.tmp.name) / "base.sqlite3"
        cible.write_bytes(self.base_sqlite("ancienne"))
        with self.assertRaises(ErreurSauvegarde):
            restaurer_sqlite(archive, cible, self.media, self.dossier)
        self.assertEqual(requete(cible, "SELECT v FROM t")[0], ("ancienne",))
        self.assertFalse((Path(self.tmp.name).parent / "evil.txt").exists())

    def test_archives_invalides_refusees_sans_rien_ecraser(self):
        cible = Path(self.tmp.name) / "base.sqlite3"
        cible.write_bytes(self.base_sqlite("ancienne"))
        mauvais = {
            "pas un zip": None,
            "sans base": {"uploads/a.pdf": b"A"},
            "base abîmée": {BASE_SQLITE: b"ceci n'est pas une base SQLite" * 50},
        }
        for nom, membres in mauvais.items():
            if membres is None:
                archive = Path(self.tmp.name) / "faux.zip"
                archive.write_bytes(b"pas un zip")
            else:
                archive = self.preparer_archive(membres)
            with self.assertRaises(ErreurSauvegarde, msg=nom):
                restaurer_sqlite(archive, cible, self.media, self.dossier)
            self.assertEqual(requete(cible, "SELECT v FROM t")[0], ("ancienne",), nom)

    def test_commande_sans_oui_ne_modifie_rien(self):
        sortie = StringIO()
        call_command("restaurer", "n-importe-quoi.zip", stdout=sortie)
        self.assertIn("Rien n'a été modifié", sortie.getvalue())

    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "x"}})
    def test_commande_postgres_explique_la_marche_a_suivre(self):
        with self.assertRaises(CommandError) as erreur:
            call_command("restaurer", "a.zip", "--oui")
        self.assertIn("pg_restore", str(erreur.exception))


class BaseVerrouilleeTests(TestCase):
    def test_une_base_verrouillee_fait_echouer_la_sauvegarde_au_lieu_de_l_attendre_indefiniment(self):
        # TestCase garde une transaction ouverte sur la base : la copie ne peut pas se terminer
        get_user_model().objects.create_user("c@example.test", "x")
        with tempfile.TemporaryDirectory() as tmp, override_settings(BACKUP_DIR=Path(tmp)):
            with self.assertRaises(ErreurSauvegarde) as erreur:
                sauvegarder(delai=1)
        self.assertIn("verrouillée", str(erreur.exception))
