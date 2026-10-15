"""
Tests de la protection des données personnelles (Lot 7). Lancer : python manage.py test
"""

import json
import tempfile
from datetime import date
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from comptes import roles
from soutenances.models import Campagne, Soutenance

from .donnees import anciens_comptes, anonymiser, donnees_personnelles
from .models import Convention, Entreprise, Inscription, Promotion, Stage, annee_universitaire_courante
from .tests import creer


class DonneesBase(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        reglage = override_settings(MEDIA_ROOT=Path(self.tmp.name))
        reglage.enable()
        self.addCleanup(reglage.disable)
        self.annee = annee_universitaire_courante()
        self.vieille_promotion = Promotion.objects.create(annee_etudes=3, annee_universitaire="2015-2016")
        self.promotion_actuelle = Promotion.objects.create(annee_etudes=3, annee_universitaire=self.annee)
        self.ancien = creer("ancien@example.test", roles.ETUDIANT, prenom="Amine", nom="Ancien")
        Inscription.objects.create(etudiant=self.ancien, promotion=self.vieille_promotion)
        self.stage = Stage.objects.create(
            etudiant=self.ancien, promotion=self.vieille_promotion,
            entreprise=Entreprise.objects.create(raison_sociale="Atlas Énergies"), sujet="Optimisation d'un réseau",
            representant_nom="M. Directeur", representant_fonction="Gérant", tuteur_nom="Mme Tutrice",
            tuteur_email="tutrice@example.test", tuteur_telephone="0600000000",
            date_debut=date(2016, 6, 1), date_fin=date(2016, 7, 30), statut=Stage.Statut.VALIDE)
        self.convention = Convention.objects.create(stage=self.stage, numero="2016-0001", statut=Convention.Statut.SIGNEE)
        self.convention.fichier_pdf.save("c.pdf", ContentFile(b"%PDF-1.4 convention"), save=True)
        self.convention.scan_signe.save("s.pdf", ContentFile(b"%PDF-1.4 scan"), save=True)
        campagne = Campagne.objects.create(nom="Ancienne", annee_universitaire="2015-2016", date_debut=date(2016, 9, 5),
                                           date_fin=date(2016, 9, 9))
        self.soutenance = Soutenance.objects.create(stage=self.stage, campagne=campagne, statut="NOTEE", note=15,
                                                    pv="Amine Ancien a bien présenté son travail.")


class AccesTests(DonneesBase):
    def test_toutes_les_donnees_detenues_sur_une_personne(self):
        donnees = donnees_personnelles(self.ancien)
        self.assertEqual(donnees["compte"]["email"], "ancien@example.test")
        self.assertEqual(donnees["compte"]["roles"], [roles.ETUDIANT])
        stage = donnees["stages"][0]
        self.assertEqual(stage["entreprise"], "Atlas Énergies")
        self.assertEqual(stage["tuteur"]["email"], "tutrice@example.test")
        self.assertEqual(stage["conventions"][0], {"numero": "2016-0001", "version": 1, "statut": "Signée par toutes les parties",
                                                  "pdf": True, "scan_signe": True})
        self.assertEqual(stage["soutenance"]["note"], "15.00")
        json.dumps(donnees, default=str)   # sérialisable

    def test_un_membre_du_jury_voit_ses_soutenances(self):
        juge = creer("juge@example.test", roles.JURY)
        self.soutenance.jury.add(juge)
        donnees = donnees_personnelles(juge)
        self.assertEqual(donnees["soutenances_comme_membre_du_jury"][0]["etudiant"], "Amine Ancien")
        self.assertEqual(donnees["stages"], [])

    def test_commande(self):
        sortie = StringIO()
        call_command("donnees_personnelles", " ANCIEN@example.test ", stdout=sortie)
        self.assertEqual(json.loads(sortie.getvalue())["compte"]["prenom"], "Amine")
        with self.assertRaises(CommandError):
            call_command("donnees_personnelles", "inconnu@example.test")


class AnonymisationTests(DonneesBase):
    def test_seuls_les_anciens_etudiants_sont_candidats(self):
        recent = creer("recent@example.test", roles.ETUDIANT)
        Inscription.objects.create(etudiant=recent, promotion=self.promotion_actuelle)
        mixte = creer("mixte@example.test", roles.ETUDIANT)   # ancienne inscription ET inscription récente
        Inscription.objects.create(etudiant=mixte, promotion=self.vieille_promotion)
        Inscription.objects.create(etudiant=mixte, promotion=self.promotion_actuelle)
        encadrant = creer("encadrant@example.test", roles.ETUDIANT, roles.ENCADRANT)   # a un autre rôle
        Inscription.objects.create(etudiant=encadrant, promotion=self.vieille_promotion)
        creer("sansinscription@example.test", roles.ETUDIANT)
        self.assertEqual(anciens_comptes(), [self.ancien])

    def test_duree_et_annee_de_reference(self):
        # dernière inscription en 2015-2016 : fin 2016 ; +10 ans = 2026 ; l'année 2025-2026 est la dernière « trop tôt »
        self.assertEqual(anciens_comptes(annee_courante="2025-2026"), [])
        self.assertEqual(anciens_comptes(annee_courante="2026-2027"), [self.ancien])
        self.assertEqual(anciens_comptes(annees=20), [])

    def test_anonymisation(self):
        chemins = [Path(self.convention.fichier_pdf.path), Path(self.convention.scan_signe.path)]
        self.assertTrue(all(c.exists() for c in chemins))
        self.assertEqual(anonymiser(self.ancien), 2)
        self.ancien.refresh_from_db()
        self.assertEqual(self.ancien.email, f"anonyme-{self.ancien.pk}@anonyme.invalid")
        self.assertEqual((self.ancien.first_name, self.ancien.is_active), ("Ancien", False))
        self.assertFalse(self.ancien.has_usable_password())
        self.stage.refresh_from_db()
        self.assertEqual((self.stage.tuteur_nom, self.stage.tuteur_email, self.stage.tuteur_telephone), ("", "", ""))
        self.assertEqual(self.stage.representant_nom, "(supprimé)")
        self.assertEqual(self.stage.entreprise.raison_sociale, "Atlas Énergies")   # statistiques conservées
        self.convention.refresh_from_db()
        self.assertEqual(self.convention.numero, "2016-0001")
        self.assertFalse(self.convention.fichier_pdf or self.convention.scan_signe)
        self.assertFalse(any(c.exists() for c in chemins))   # fichiers effacés du disque
        self.soutenance.refresh_from_db()
        self.assertEqual((self.soutenance.pv, self.soutenance.note), ("(supprimé)", 15))
        self.assertFalse(self.client.login(username="ancien@example.test", password="MotDePasse-123"))

    def test_un_compte_anonymise_n_est_plus_candidat(self):
        anonymiser(self.ancien)
        self.assertEqual(anciens_comptes(), [])

    def test_commande_simulation_puis_reelle(self):
        sortie = StringIO()
        call_command("anonymiser_comptes", stdout=sortie)
        self.assertIn("ancien@example.test", sortie.getvalue())
        self.assertIn("Simulation", sortie.getvalue())
        self.ancien.refresh_from_db()
        self.assertEqual(self.ancien.email, "ancien@example.test")   # rien n'a changé
        sortie = StringIO()
        call_command("anonymiser_comptes", "--oui", stdout=sortie)
        self.assertIn("1 compte(s) anonymisé(s), 2 fichier(s) supprimé(s)", sortie.getvalue())
        sortie = StringIO()
        call_command("anonymiser_comptes", "--oui", stdout=sortie)
        self.assertIn("Aucun compte à anonymiser", sortie.getvalue())


class PageInformationTests(TestCase):
    def test_page_publique_avec_les_coordonnees_de_l_ecole(self):
        reponse = self.client.get(reverse("protection_donnees"))   # sans être connecté
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "09-08")
        self.assertContains(reponse, "EIGSI Casablanca")
        self.assertContains(reponse, "stages@example.test")
        self.assertContains(reponse, "10 ans")

    def test_lien_en_bas_de_chaque_page(self):
        self.assertContains(self.client.get(reverse("connexion")), reverse("protection_donnees"))
        utilisateur = get_user_model().objects.create_user("x@example.test", "MotDePasse-123")
        self.client.force_login(utilisateur)
        self.assertContains(self.client.get(reverse("accueil")), reverse("protection_donnees"))
