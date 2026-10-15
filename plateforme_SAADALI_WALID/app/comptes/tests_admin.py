"""Tests de l'interface d'administration (lot 8) : langue, fiche unique des paramètres, accès aux rôles, fiche de stage."""

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from comptes.models import Utilisateur
from stages.models import ParametresEcole


class AdministrationTests(TestCase):
    def setUp(self):
        self.admin = Utilisateur.objects.create_superuser(email="root@example.test", password="x")
        # Un membre du Career Center : accès à l'administration, mais pas administrateur
        self.career = Utilisateur.objects.create_user(email="cc@example.test", password="x", is_staff=True)
        self.career.user_permissions.add(*Permission.objects.filter(
            codename__in=["view_utilisateur", "change_utilisateur", "view_parametresecole", "change_parametresecole"]))

    def test_administration_toujours_en_francais(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(reverse("admin:index"), headers={"accept-language": "en"})
        self.assertContains(reponse, "Gérer les données de la plateforme")
        self.assertNotContains(reponse, "Site administration")

    def test_parametres_ouvrent_directement_la_fiche(self):
        parametres = ParametresEcole.actuels()
        self.client.force_login(self.career)
        reponse = self.client.get(reverse("admin:stages_parametresecole_changelist"))
        self.assertRedirects(reponse, reverse("admin:stages_parametresecole_change", args=[parametres.pk]))

    def test_roles_reserves_a_l_administrateur(self):
        self.client.force_login(self.career)
        self.assertNotContains(self.client.get(reverse("admin:index")), "/admin/auth/group/")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("admin:index")), "/admin/auth/group/")

    def test_fiche_de_stage_decoupee_en_sections(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(reverse("admin:stages_stage_add"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Représentant et tuteur")
        self.assertContains(reponse, "Durée et horaires")

    def test_habillage_eigsi_charge(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(reverse("admin:index"))
        self.assertContains(reponse, "admin-eigsi.css")
        self.assertContains(reponse, "logo-eigsi.png")
