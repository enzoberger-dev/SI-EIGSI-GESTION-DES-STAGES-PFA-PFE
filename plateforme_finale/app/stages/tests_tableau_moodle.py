"""
Tests du tableau de bord (US-11) et de l'import Moodle. Lancer : python manage.py test
"""

import io
import zipfile
from datetime import date

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .csv_outils import ErreurCSV
from .echanges import dossier_zip, importer_moodle
from .models import Convention, Historique, Inscription, Livrable, Stage
from .pilotage import etape_du_stage, tableau_de_bord
from .services import creer_livrables
from .tests import LivrableBase


class TableauDeBordTests(LivrableBase):
    def etapes(self, annee=None):
        donnees = tableau_de_bord(annee or self.annee)
        return {e["code"]: e["total"] for e in donnees["etapes"]}

    def test_etudiants_sans_fiche(self):
        self.assertEqual(self.etapes()["SANS_FICHE"], 2)
        donnees = tableau_de_bord(self.annee)
        self.assertEqual(donnees["nb_etudiants"], 2)
        self.assertEqual(donnees["annees_etudes"], [3, 5])

    def test_chaque_etudiant_n_est_compte_qu_une_fois(self):
        self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        self.assertEqual(sum(self.etapes().values()), 2)

    def test_etapes_du_parcours(self):
        stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        suite = [
            (Stage.Statut.BROUILLON, "BROUILLON"), (Stage.Statut.SOUMIS, "SOUMIS"),
            (Stage.Statut.REFUSE, "REFUSE"), (Stage.Statut.VALIDE, "A_GENERER"),
        ]
        for statut, attendu in suite:
            stage.statut = statut
            self.assertEqual(etape_du_stage(stage, None, []), attendu)
        stage.statut = Stage.Statut.VALIDE
        c = Convention(stage=stage, numero="2026-0001", statut=Convention.Statut.GENEREE)
        self.assertEqual(etape_du_stage(stage, c, []), "A_FAIRE_SIGNER")
        c.statut = Convention.Statut.ENVOYEE
        self.assertEqual(etape_du_stage(stage, c, []), "CHEZ_ETUDIANT")
        c.scan_signe = "conventions/1/scan.pdf"
        self.assertEqual(etape_du_stage(stage, c, []), "SCAN_A_VERIFIER")
        c.statut = Convention.Statut.SIGNEE
        self.assertEqual(etape_du_stage(stage, c, []), "EN_SUIVI")
        rendu = Livrable(stage=stage, nom="R", date_limite=date(2027, 9, 15), statut=Livrable.Statut.RENDU)
        a_rendre = Livrable(stage=stage, nom="P", date_limite=date(2027, 9, 15))
        self.assertEqual(etape_du_stage(stage, c, [rendu, a_rendre]), "EN_SUIVI")
        self.assertEqual(etape_du_stage(stage, c, [rendu]), "TERMINE")

    def test_chiffres_a_traiter_et_retards(self):
        stage3 = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        Convention.objects.create(stage=stage3, numero="2026-0001", statut=Convention.Statut.SIGNEE)
        creer_livrables(stage3)
        stage5 = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 30))
        stage5.statut = Stage.Statut.SOUMIS
        stage5.save()
        Livrable.objects.filter(stage=stage3).update(date_limite=date(2020, 1, 1))  # en retard
        donnees = tableau_de_bord(self.annee)
        self.assertEqual(donnees["livrables"], {"total": 1, "rendus": 0, "a_rendre": 0, "en_retard": 1})
        self.assertEqual(len(donnees["livrables_en_retard"]), 1)
        self.assertEqual(len(donnees["fiches_soumises"]), 1)
        self.assertEqual([e.pk for e in donnees["sans_encadrant"]], [self.etu5.pk])  # 5e année sans encadrant
        etapes = {e["code"]: e["par_annee"] for e in donnees["etapes"]}
        self.assertEqual(etapes["EN_SUIVI"], [1, 0])      # 3e année : 1 ; 5e année : 0
        self.assertEqual(etapes["SOUMIS"], [0, 1])

    def test_ecran_reserve_au_career_center_et_changement_d_annee(self):
        self.assertEqual(self.client.get(reverse("tableau_de_bord")).status_code, 302)
        for utilisateur in (self.etu3, self.encadrant, self.coordinateur):
            self.client.force_login(utilisateur)
            self.assertEqual(self.client.get(reverse("tableau_de_bord")).status_code, 403)
        self.client.force_login(self.career)
        reponse = self.client.get(reverse("tableau_de_bord"))
        self.assertContains(reponse, "Tableau de bord des stages")
        self.assertContains(reponse, 'http-equiv="refresh"')   # mise à jour automatique
        self.assertContains(reponse, "Pas encore de fiche de stage")
        # année inconnue ou tentative d'injection : on retombe sur l'année en cours
        reponse = self.client.get(reverse("tableau_de_bord"), {"annee": "<script>"})
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, "<script>")
        reponse = self.client.get(reverse("tableau_de_bord"), {"annee": "1999-2000"})
        self.assertContains(reponse, self.annee)

    def test_annee_sans_etudiant(self):
        self.assertEqual(tableau_de_bord("2020-2021")["nb_etudiants"], 0)
        self.client.force_login(self.career)
        Inscription.objects.all().delete()
        self.assertContains(self.client.get(reverse("tableau_de_bord")), "Aucun étudiant inscrit")


def csv_moodle(*lignes):
    entete = "Identifiant;Nom complet;Adresse de courriel;Statut;Note"
    return ("\r\n".join([entete, *lignes]) + "\r\n").encode("utf-8-sig")


class ImportMoodleTests(LivrableBase):
    def setUp(self):
        super().setUp()
        self.stage3 = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        self.stage5 = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 30))
        creer_livrables(self.stage3)
        creer_livrables(self.stage5)
        self.rapport3 = Livrable.objects.get(stage=self.stage3, est_rapport=True)
        self.nom = self.rapport3.nom

    def test_les_remis_passent_rendus_les_autres_non(self):
        rapport = importer_moodle(csv_moodle(
            "u1;Adam;adam@example.test;Remis pour évaluation;-",
            "u2;Yasmine;yasmine@example.test;Brouillon (non remis);-",
        ), self.nom, par=self.career)
        self.rapport3.refresh_from_db()
        self.assertEqual(self.rapport3.statut, Livrable.Statut.RENDU)
        self.assertEqual(self.rapport3.rendu_par, self.career)
        self.assertEqual(len(rapport.faits), 1)
        self.assertEqual(len(rapport.ignorees), 1)
        self.assertEqual(Livrable.objects.get(stage=self.stage5, nom=self.nom).statut, Livrable.Statut.A_RENDRE)
        self.assertTrue(self.stage3.historique.filter(action="LIVRABLE_RENDU").exists())  # trace gardée

    def test_statuts_et_cas_particuliers(self):
        rapport = importer_moodle(csv_moodle(
            "u1;Inconnu;personne@example.test;Remis pour évaluation;-",
            "u2;Adam;ADAM@example.test;Aucun travail remis;-",
            "u3;Adam;;Remis pour évaluation;-",
        ), self.nom, par=self.career)
        self.assertEqual(len(rapport.faits), 0)
        self.assertEqual(len(rapport.ignorees), 3)
        self.rapport3.refresh_from_db()
        self.assertEqual(self.rapport3.statut, Livrable.Statut.A_RENDRE)

    def test_statut_en_anglais_et_deux_imports_de_suite(self):
        contenu = csv_moodle("u1;Adam;adam@example.test;Submitted for grading;-")
        self.assertEqual(len(importer_moodle(contenu, self.nom, par=self.career).faits), 1)
        rapport = importer_moodle(contenu, self.nom, par=self.career)
        self.assertEqual((len(rapport.faits), len(rapport.ignorees)), (0, 1))
        self.assertEqual(self.stage3.historique.filter(action="LIVRABLE_RENDU").count(), 1)

    def test_simulation(self):
        rapport = importer_moodle(csv_moodle("u1;Adam;adam@example.test;Remis pour évaluation;-"),
                                  self.nom, par=self.career, simuler=True)
        self.assertEqual(len(rapport.faits), 1)
        self.rapport3.refresh_from_db()
        self.assertEqual(self.rapport3.statut, Livrable.Statut.A_RENDRE)
        self.assertFalse(self.stage3.historique.filter(action="LIVRABLE_RENDU").exists())

    def test_colonnes_manquantes(self):
        with self.assertRaises(ErreurCSV):
            importer_moodle(b"Nom;Note\nA;12\n", self.nom, par=self.career)

    def test_ecran(self):
        url = reverse("import_moodle")
        self.client.force_login(self.etu3)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.career)
        self.assertContains(self.client.get(url), self.nom)
        fichier = SimpleUploadedFile("moodle.csv", csv_moodle("u1;Adam;adam@example.test;Remis pour évaluation;-"))
        reponse = self.client.post(url, {"fichier": fichier, "livrable": self.nom})   # import réel
        self.assertContains(reponse, "Résultat de l")
        self.rapport3.refresh_from_db()
        self.assertEqual(self.rapport3.statut, Livrable.Statut.RENDU)
        fichier = SimpleUploadedFile("moodle.csv", csv_moodle("u1;Adam;adam@example.test;Remis;-"))
        self.assertContains(self.client.post(url, {"fichier": fichier, "livrable": "Inventé"}),
                            "Choisissez le livrable")


class DossierArchiveTests(LivrableBase):
    def setUp(self):
        super().setUp()
        self.stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        self.convention = Convention.objects.create(stage=self.stage, numero="2026-0001", statut=Convention.Statut.SIGNEE)
        self.convention.fichier_pdf.save("convention-2026-0001-v1.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
        self.convention.scan_signe.save("scan-2026-0001-v1.pdf", ContentFile(b"%PDF-1.4 scan"), save=True)
        Historique.objects.create(stage=self.stage, auteur=self.career, action=Historique.Action.CONVENTION_SIGNEE)
        creer_livrables(self.stage)

    def tearDown(self):
        for fichier in (self.convention.fichier_pdf, self.convention.scan_signe):
            if fichier:
                fichier.delete(save=False)  # ne laisse pas de fichiers de test dans uploads/

    def conventions_de(self, archive):
        """Noms des fichiers de convention de l'archive (Django peut ajouter un suffixe au nom si un
        fichier de même nom existe déjà dans uploads/, d'où la recherche par début de nom)."""
        return [n for n in archive.namelist() if n.startswith("conventions/")]

    def test_contenu_de_l_archive(self):
        archive = zipfile.ZipFile(io.BytesIO(dossier_zip(self.stage)))
        noms = archive.namelist()
        for attendu in ("fiche-de-stage.txt", "historique.csv", "LISEZMOI.txt"):
            self.assertIn(attendu, noms)
        fichiers = self.conventions_de(archive)
        self.assertEqual(len(fichiers), 2)
        scan = [n for n in fichiers if "/scan-" in n][0]
        self.assertEqual(archive.read(scan), b"%PDF-1.4 scan")
        self.assertTrue(any("/convention-2026-0001-v1" in n for n in fichiers))
        fiche = archive.read("fiche-de-stage.txt").decode()
        self.assertIn("Atlas Énergies", fiche)
        self.assertIn("Rapport de stage", fiche)
        self.assertIn("Convention signée", archive.read("historique.csv").decode("utf-8-sig"))

    def test_fichier_manquant_sur_le_disque_n_empeche_pas_l_archive(self):
        self.convention.scan_signe.storage.delete(self.convention.scan_signe.name)
        fichiers = self.conventions_de(zipfile.ZipFile(io.BytesIO(dossier_zip(self.stage))))
        self.assertEqual(len(fichiers), 1)
        self.assertIn("/convention-2026-0001-v1", fichiers[0])

    def test_telechargement_reserve_au_career_center(self):
        url = reverse("dossier_stage", args=[self.stage.pk])
        self.client.force_login(self.etu3)   # même le propriétaire du dossier : réservé au Career Center
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.career)
        reponse = self.client.get(url)
        self.assertEqual(reponse["Content-Type"], "application/zip")
        self.assertIn(f"dossier-adam-utilisateur-{self.annee}.zip", reponse["Content-Disposition"])
        self.assertEqual(self.client.get(reverse("dossier_stage", args=[99999])).status_code, 404)
