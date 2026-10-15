"""Tests de la commande `preparer_demo` (lot 8) : parcours variés, mot de passe unique, refus en ligne, relançable."""

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from comptes.models import Utilisateur
from soutenances.models import Soutenance
from stages.models import Convention, Stage


@override_settings(DEBUG=True)
class PreparerDemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("preparer_demo", stdout=StringIO())

    def statut(self, prenom):
        return Stage.objects.get(etudiant__first_name=prenom).statut

    def test_un_parcours_different_par_etudiant(self):
        self.assertEqual(self.statut("Hamza"), "BROUILLON")
        self.assertEqual(self.statut("Imane"), "SOUMIS")
        self.assertEqual(self.statut("Salma"), "REFUSE")
        self.assertEqual(self.statut("Reda"), "VALIDE")
        self.assertFalse(Stage.objects.filter(etudiant__first_name="Nour").exists())
        self.assertEqual(Convention.objects.get(stage__etudiant__first_name="Yasmine").statut, "ENVOYEE")
        self.assertEqual(Convention.objects.get(stage__etudiant__first_name="Adam").statut, "SIGNEE")
        self.assertFalse(Convention.objects.filter(stage__etudiant__first_name="Reda").exists())

    def test_soutenances_a_chaque_etape(self):
        mehdi = Soutenance.objects.get(stage__etudiant__first_name="Mehdi")
        kenza = Soutenance.objects.get(stage__etudiant__first_name="Kenza")
        self.assertEqual(mehdi.statut, "PV_SAISI")
        self.assertEqual(kenza.statut, "CONVOQUEE")
        self.assertEqual(kenza.jury.count(), 2)
        self.assertIsNotNone(kenza.debut)

    def test_adam_a_un_livrable_rendu(self):
        statuts = set(Stage.objects.get(etudiant__first_name="Adam").livrables.values_list("statut", flat=True))
        self.assertIn("RENDU", statuts)

    def test_meme_mot_de_passe_pour_tous_les_comptes(self):
        for compte in Utilisateur.objects.filter(email__endswith="@example.test"):
            self.assertTrue(compte.check_password("Demo-EIGSI-2026"), compte.email)

    def test_on_peut_se_connecter_avec_un_compte_de_demo(self):
        self.assertTrue(self.client.login(username="nadia.alaoui@example.test", password="Demo-EIGSI-2026"))

    def test_relancer_ne_cree_rien_en_double(self):
        avant = (Stage.objects.count(), Soutenance.objects.count(), Utilisateur.objects.count())
        call_command("preparer_demo", stdout=StringIO())
        self.assertEqual((Stage.objects.count(), Soutenance.objects.count(), Utilisateur.objects.count()), avant)


class PreparerDemoSecuriteTests(TestCase):
    @override_settings(DEBUG=False)
    def test_refuse_de_tourner_en_ligne(self):
        with self.assertRaises(CommandError):
            call_command("preparer_demo", stdout=StringIO())
        self.assertFalse(Utilisateur.objects.filter(email__endswith="@example.test").exists())
