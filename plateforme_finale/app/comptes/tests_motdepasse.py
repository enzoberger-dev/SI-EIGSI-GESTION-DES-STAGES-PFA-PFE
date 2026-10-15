"""
Tests du changement et de l'oubli de mot de passe (Lot 7). Lancer : python manage.py test
"""

import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

ANCIEN = "Ancien-motdepasse-731"
NOUVEAU = "Nouveau-motdepasse-958"


class MotDePasseBase(TestCase):
    def setUp(self):
        self.utilisateur = get_user_model().objects.create_user("lea@example.test", ANCIEN, first_name="Léa")


class ChangerSonMotDePasseTests(MotDePasseBase):
    def test_il_faut_etre_connecte(self):
        reponse = self.client.get(reverse("password_change"))
        self.assertEqual(reponse.status_code, 302)
        self.assertIn(reverse("connexion"), reponse["Location"])

    def test_changement_reussi_et_la_session_reste_ouverte(self):
        self.client.force_login(self.utilisateur)
        reponse = self.client.post(reverse("password_change"), {
            "old_password": ANCIEN, "new_password1": NOUVEAU, "new_password2": NOUVEAU})
        self.assertRedirects(reponse, reverse("password_change_done"))
        self.assertEqual(self.client.get(reverse("accueil")).status_code, 200)   # pas déconnecté
        self.client.logout()
        self.assertFalse(self.client.login(username="lea@example.test", password=ANCIEN))
        self.assertTrue(self.client.login(username="lea@example.test", password=NOUVEAU))

    def test_ancien_mot_de_passe_faux_ou_nouveau_trop_faible(self):
        self.client.force_login(self.utilisateur)
        reponse = self.client.post(reverse("password_change"), {
            "old_password": "faux", "new_password1": NOUVEAU, "new_password2": NOUVEAU})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "erreur")
        for faible in ("abc", "12345678", "password"):
            reponse = self.client.post(reverse("password_change"), {
                "old_password": ANCIEN, "new_password1": faible, "new_password2": faible})
            self.assertEqual(reponse.status_code, 200, faible)
        self.utilisateur.refresh_from_db()
        self.assertTrue(self.utilisateur.check_password(ANCIEN))   # rien n'a changé

    def test_lien_dans_l_en_tete_pour_un_utilisateur_connecte(self):
        self.client.force_login(self.utilisateur)
        self.assertContains(self.client.get(reverse("accueil")), reverse("password_change"))


class MotDePasseOublieTests(MotDePasseBase):
    def demander(self, email, **extra):
        return self.client.post(reverse("password_reset"), {"email": email}, **extra)

    def lien_recu(self):
        self.assertEqual(len(mail.outbox), 1)
        trouve = re.search(r"https?://\S+(/reinitialisation/\S+/)", mail.outbox[0].body)
        self.assertIsNotNone(trouve, mail.outbox[0].body)
        return trouve.group(1)

    def test_page_de_connexion_propose_le_lien(self):
        self.assertContains(self.client.get(reverse("connexion")), reverse("password_reset"))

    def test_parcours_complet(self):
        self.assertRedirects(self.demander("lea@example.test"), reverse("password_reset_done"))
        self.assertEqual(mail.outbox[0].to, ["lea@example.test"])
        self.assertIn("Réinitialisation", mail.outbox[0].subject)
        chemin = self.lien_recu()
        # le lien est construit avec l'adresse du site réglée (SITE_URL), pas avec l'en-tête de la requête
        self.assertIn(settings.SITE_URL.rstrip("/") + chemin, mail.outbox[0].body)
        reponse = self.client.get(chemin, follow=True)   # Django remplace le jeton par une adresse « set-password »
        self.assertContains(reponse, "Choisir un nouveau mot de passe")
        reponse = self.client.post(reponse.redirect_chain[-1][0], {"new_password1": NOUVEAU, "new_password2": NOUVEAU})
        self.assertRedirects(reponse, reverse("password_reset_complete"))
        self.assertTrue(self.client.login(username="lea@example.test", password=NOUVEAU))

    def test_le_lien_ne_sert_qu_une_fois(self):
        self.demander("lea@example.test")
        chemin = self.lien_recu()
        premiere = self.client.get(chemin, follow=True)
        self.client.post(premiere.redirect_chain[-1][0], {"new_password1": NOUVEAU, "new_password2": NOUVEAU})
        self.client.logout()
        deuxieme = self.client.get(chemin, follow=True)
        self.assertContains(deuxieme, "Lien invalide")

    def test_adresse_inconnue_meme_reponse_et_aucun_e_mail(self):
        reponse = self.demander("personne@example.test")
        self.assertRedirects(reponse, reverse("password_reset_done"))   # on ne révèle pas quels comptes existent
        self.assertEqual(mail.outbox, [])

    def test_compte_desactive_ou_sans_mot_de_passe_ne_recoit_rien(self):
        self.utilisateur.is_active = False
        self.utilisateur.save()
        self.demander("lea@example.test")
        self.utilisateur.is_active = True
        self.utilisateur.set_unusable_password()
        self.utilisateur.save()
        self.demander("lea@example.test")
        self.assertEqual(mail.outbox, [])

    def test_lien_falsifie_refuse(self):
        self.demander("lea@example.test")
        chemin = self.lien_recu()
        falsifie = chemin[:-2] + ("a" if chemin[-2] != "a" else "b") + "/"
        self.assertContains(self.client.get(falsifie, follow=True), "Lien invalide")

    def test_lien_valable_24_heures(self):
        self.assertEqual(settings.PASSWORD_RESET_TIMEOUT, 24 * 3600)

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_l_adresse_du_lien_ne_depend_pas_de_l_en_tete_de_la_requete(self):
        self.demander("lea@example.test", HTTP_HOST="pirate.example.test")
        self.assertNotIn("pirate", mail.outbox[0].body)
        self.assertIn(settings.SITE_URL.rstrip("/"), mail.outbox[0].body)
