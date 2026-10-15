"""
Tests automatiques des comptes. Lancer : python manage.py test
"""

from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from comptes import roles


class UtilisateurTests(TestCase):
    def test_les_quatre_roles_existent(self):
        # Créés par la migration 0002
        for role in roles.TOUS_LES_ROLES:
            self.assertTrue(Group.objects.filter(name=role).exists(), role)

    def test_connexion_par_email(self):
        get_user_model().objects.create_user("test@example.test", "MotDePasse-123")
        self.assertTrue(self.client.login(username="test@example.test", password="MotDePasse-123"))

    def test_mot_de_passe_jamais_stocke_en_clair(self):
        u = get_user_model().objects.create_user("test@example.test", "MotDePasse-123")
        self.assertNotEqual(u.password, "MotDePasse-123")

    def test_plusieurs_roles(self):
        u = get_user_model().objects.create_user("prof@example.test", "MotDePasse-123")
        u.groups.add(Group.objects.get(name=roles.ENCADRANT), Group.objects.get(name=roles.JURY))
        self.assertTrue(u.a_le_role(roles.ENCADRANT))
        self.assertTrue(u.a_le_role(roles.JURY))
        self.assertFalse(u.a_le_role(roles.ETUDIANT))


class CommandeDemoTests(TestCase):
    def test_cree_les_comptes_avec_leurs_roles(self):
        call_command("creer_comptes_demo", stdout=StringIO())
        sara = get_user_model().objects.get(email="sara.bennani@example.test")
        self.assertEqual(sara.roles(), [roles.ENCADRANT, roles.JURY])
        nadia = get_user_model().objects.get(email="nadia.alaoui@example.test")
        self.assertTrue(nadia.is_staff)

    def test_relancer_ne_cree_pas_de_doublon(self):
        call_command("creer_comptes_demo", stdout=StringIO())
        call_command("creer_comptes_demo", stdout=StringIO())
        self.assertEqual(get_user_model().objects.filter(email__endswith="@example.test").count(), 6)

    def test_cree_les_donnees_du_lot_1(self):
        from stages.models import Affectation, Inscription
        call_command("creer_comptes_demo", stdout=StringIO())
        call_command("creer_comptes_demo", stdout=StringIO())  # relancer ne crée pas de doublon
        adam = get_user_model().objects.get(email="adam.elamrani@example.test")
        self.assertEqual(Inscription.objects.get(etudiant=adam).promotion.annee_etudes, 3)
        affectation = Affectation.objects.get(etudiant__email="yasmine.benali@example.test", active=True)
        self.assertEqual(affectation.encadrant.email, "sara.bennani@example.test")
        nadia = get_user_model().objects.get(email="nadia.alaoui@example.test")
        self.assertTrue(nadia.has_perm("stages.change_promotion"))
