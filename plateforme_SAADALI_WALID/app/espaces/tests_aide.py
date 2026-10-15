"""Tests de la page « À propos et aide » (lot 8) : réservée aux personnes connectées, et chacun ne voit que son rôle."""

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from comptes import roles
from comptes.models import Utilisateur
from stages.models import ParametresEcole


def utilisateur(email, *noms_roles):
    u = Utilisateur.objects.create_user(email=email, password="x", first_name="Test", last_name="Aide")
    for nom in noms_roles:
        u.groups.add(Group.objects.get_or_create(name=nom)[0])
    return u


class AideTests(TestCase):
    def test_reservee_aux_personnes_connectees(self):
        reponse = self.client.get(reverse("aide"))
        self.assertEqual(reponse.status_code, 302)
        self.assertIn(reverse("connexion"), reponse["Location"])

    def test_etudiant_ne_voit_que_l_aide_etudiant(self):
        self.client.force_login(utilisateur("e@example.test", roles.ETUDIANT))
        reponse = self.client.get(reverse("aide"))
        self.assertContains(reponse, "Passer votre soutenance")          # étape propre à l'étudiant
        self.assertNotContains(reponse, "Organiser les soutenances")     # étape du Career Center
        self.assertNotContains(reponse, "Saisir le PV")                  # étape du jury
        self.assertNotContains(reponse, "Examiner les fiches soumises")  # étape de l'encadrant

    def test_career_center_voit_ses_etapes_avec_des_liens_qui_marchent(self):
        self.client.force_login(utilisateur("c@example.test", roles.SERVICE_STAGES))
        reponse = self.client.get(reverse("aide"))
        self.assertContains(reponse, "Organiser les soutenances")
        self.assertContains(reponse, reverse("conventions"))
        self.assertNotContains(reponse, "Passer votre soutenance")   # étape de l'étudiant

    def test_plusieurs_roles_donnent_plusieurs_sections(self):
        self.client.force_login(utilisateur("p@example.test", roles.ENCADRANT, roles.JURY))
        reponse = self.client.get(reverse("aide"))
        self.assertContains(reponse, "Examiner les fiches soumises")
        self.assertContains(reponse, "Saisir le PV")

    def test_sans_role_on_oriente_vers_le_service_stages(self):
        self.client.force_login(utilisateur("s@example.test"))
        self.assertContains(self.client.get(reverse("aide")), "Aucun rôle ne vous est encore attribué")

    def test_contact_vient_des_parametres_de_l_ecole(self):
        parametres = ParametresEcole.actuels()
        parametres.email_contact = "carriere@example.test"
        parametres.save()
        self.client.force_login(utilisateur("e2@example.test", roles.ETUDIANT))
        self.assertContains(self.client.get(reverse("aide")), "mailto:carriere@example.test")

    def test_lien_dans_le_menu(self):
        self.client.force_login(utilisateur("m@example.test", roles.ETUDIANT))
        self.assertContains(self.client.get(reverse("accueil")), 'href="/aide/"')
