"""
Tests automatiques des espaces par rôle. Lancer : python manage.py test
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from comptes import roles


def creer(email, *liste_roles):
    """Crée un utilisateur de test avec les rôles donnés."""
    u = get_user_model().objects.create_user(email, "MotDePasse-123")
    u.groups.set(Group.objects.filter(name__in=liste_roles))
    return u


class AccesTests(TestCase):
    def test_visiteur_non_connecte_renvoye_vers_connexion(self):
        reponse = self.client.get("/etudiant/")
        self.assertEqual(reponse.status_code, 302)
        self.assertIn("/connexion/", reponse["Location"])

    def test_etudiant_voit_son_espace(self):
        self.client.force_login(creer("etu@example.test", roles.ETUDIANT))
        self.assertEqual(self.client.get("/etudiant/").status_code, 200)

    def test_etudiant_refuse_dans_espace_encadrant(self):
        self.client.force_login(creer("etu@example.test", roles.ETUDIANT))
        self.assertEqual(self.client.get("/encadrant/").status_code, 403)
        self.assertEqual(self.client.get("/service-stages/").status_code, 403)

    def test_encadrant_jury_voit_ses_deux_espaces(self):
        self.client.force_login(creer("prof@example.test", roles.ENCADRANT, roles.JURY))
        self.assertEqual(self.client.get("/encadrant/").status_code, 200)
        self.assertEqual(self.client.get("/jury/").status_code, 200)
        self.assertEqual(self.client.get("/etudiant/").status_code, 403)

    def test_accueil_liste_uniquement_mes_espaces(self):
        self.client.force_login(creer("prof@example.test", roles.ENCADRANT, roles.JURY))
        page = self.client.get("/").content.decode()
        self.assertIn("Espace encadrant", page)
        self.assertIn("Espace jury", page)
        self.assertNotIn("Espace étudiant", page)

    def test_page_de_connexion_accessible(self):
        self.assertEqual(self.client.get("/connexion/").status_code, 200)
