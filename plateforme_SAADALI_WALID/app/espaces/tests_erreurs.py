"""Tests des pages d'erreur et du cadre commun (lot 8)."""

from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.test import TestCase

from comptes import roles
from comptes.models import Utilisateur


class PagesErreurTests(TestCase):
    def test_404_visiteur_non_connecte(self):
        reponse = self.client.get("/cette-page-n-existe-pas/")
        self.assertEqual(reponse.status_code, 404)
        self.assertContains(reponse, "Page introuvable", status_code=404)
        self.assertContains(reponse, "Se connecter", status_code=404)   # bandeau public, pas de menu

    def test_gabarit_500_est_autonome(self):
        html = render_to_string("500.html")
        self.assertIn("Un problème est survenu", html)
        self.assertIn("eigsi.css", html)


class MenuTests(TestCase):
    def setUp(self):
        self.etudiant = Utilisateur.objects.create_user(email="e@example.test", password="x", first_name="Eva", last_name="Test")
        self.etudiant.groups.add(Group.objects.get_or_create(name=roles.ETUDIANT)[0])

    def test_menu_montre_seulement_les_espaces_du_role(self):
        self.client.force_login(self.etudiant)
        reponse = self.client.get("/")
        self.assertContains(reponse, "Espace étudiant")
        self.assertNotContains(reponse, "Espace Service Stages")
        self.assertNotContains(reponse, "Administration du site")

    def test_page_active_est_signalee(self):
        self.client.force_login(self.etudiant)
        reponse = self.client.get("/etudiant/mon-stage/")
        self.assertContains(reponse, 'aria-current="page"')

    def test_lien_pour_aller_au_contenu(self):
        self.client.force_login(self.etudiant)
        self.assertContains(self.client.get("/"), 'href="#contenu"')
