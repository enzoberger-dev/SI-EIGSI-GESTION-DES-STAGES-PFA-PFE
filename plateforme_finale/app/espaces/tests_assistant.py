"""Tests de l'assistant IA (lot 9). AUCUN test n'appelle le vrai service : tout appel réseau fait échouer le test."""

import io
import json
import tempfile
import urllib.error
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from comptes import roles
from comptes.models import Utilisateur

from . import assistant


def utilisateur(email, *noms_roles):
    u = Utilisateur.objects.create_user(email=email, password="x", first_name="Test", last_name="IA")
    for nom in noms_roles:
        u.groups.add(Group.objects.get_or_create(name=nom)[0])
    return u


class BaseTest(TestCase):
    def setUp(self):
        cache.clear()
        # Filet de sécurité : si un test oublie de simuler l'IA, il échoue au lieu d'appeler Google avec la vraie clé
        interdit = mock.patch("espaces.assistant.urllib.request.urlopen",
                              side_effect=AssertionError("appel réseau interdit pendant les tests"))
        interdit.start()
        self.addCleanup(interdit.stop)

    def sans_cle(self):
        p = mock.patch("espaces.assistant.lire_cle", return_value=None)
        p.start()
        self.addCleanup(p.stop)

    def avec_ia(self, texte="Réponse simulée."):
        p = mock.patch("espaces.assistant.lire_cle", return_value="cle-de-test")
        p.start()
        self.addCleanup(p.stop)
        q = mock.patch("espaces.assistant.appeler_gemini", return_value=texte)
        self.appel = q.start()
        self.addCleanup(q.stop)


class AnonymisationTests(TestCase):
    def test_efface_email_telephone_et_longs_nombres(self):
        texte = assistant.anonymiser("Écrire à jean.dupont@example.com ou au 06 12 34 56 78, dossier 20260001234.")
        self.assertNotIn("jean.dupont", texte)
        self.assertNotIn("06 12", texte)
        self.assertNotIn("20260001234", texte)

    def test_limite_la_longueur(self):
        self.assertEqual(len(assistant.anonymiser("a" * 5000)), assistant.LONGUEUR_MAX)


class NettoyageTests(TestCase):
    def test_retire_la_mise_en_forme_markdown(self):
        propre = assistant.nettoyer("Voici :\n\n* **Précision :** détaillez.\n* Outils\n## Titre\n\n\n\nFin")
        self.assertNotIn("**", propre)
        self.assertNotIn("##", propre)
        self.assertIn("- Précision : détaillez.", propre)
        self.assertNotIn("\n\n\n", propre)


class CleTests(TestCase):
    def test_cle_dans_le_fichier_avec_ou_sans_nom(self):
        for contenu in ("abc123\n", "GEMINI_API_KEY=abc123\n", 'GEMINI_API_KEY="abc123"'):
            with tempfile.TemporaryDirectory() as dossier:
                (Path(dossier) / "cle_gemini.txt").write_text(contenu, encoding="utf-8")
                with override_settings(BASE_DIR=Path(dossier)), mock.patch.dict("os.environ", {}, clear=True):
                    self.assertEqual(assistant.lire_cle(), "abc123", contenu)

    def test_variable_d_environnement_prioritaire(self):
        with tempfile.TemporaryDirectory() as dossier:
            (Path(dossier) / "cle_gemini.txt").write_text("dans-le-fichier", encoding="utf-8")
            with override_settings(BASE_DIR=Path(dossier)), mock.patch.dict("os.environ", {"GEMINI_API_KEY": "dans-l-env"}):
                self.assertEqual(assistant.lire_cle(), "dans-l-env")

    def test_pas_de_cle(self):
        with tempfile.TemporaryDirectory() as dossier, override_settings(BASE_DIR=Path(dossier)), \
                mock.patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(assistant.lire_cle())


class RepondreTests(BaseTest):
    def test_sans_cle_reponse_tiree_de_l_aide_pour_son_role(self):
        self.sans_cle()
        reponse = assistant.repondre("Comment déposer le scan de ma convention ?", utilisateur("e@example.test", roles.ETUDIANT))
        self.assertEqual(reponse["mode"], "secours")
        self.assertIn("scan", reponse["texte"].lower())

    def test_avec_ia_mode_ia_et_texte_anonymise_envoye(self):
        self.avec_ia("Allez dans « Mon stage ».")
        u = utilisateur("e2@example.test", roles.ETUDIANT)
        reponse = assistant.repondre("Mon mail est a.b@example.test, où déposer le scan ?", u)
        self.assertEqual(reponse, {"texte": "Allez dans « Mon stage ».", "mode": "ia", "raison": ""})
        consigne, question = self.appel.call_args.args
        self.assertNotIn("a.b@example.test", question)
        self.assertIn("Signer la convention", consigne)                  # l'aide de SON rôle est dans la consigne
        self.assertNotIn("Organiser les soutenances", consigne)         # pas celle du Career Center

    def test_service_en_panne_ou_quota_depasse_donne_le_mode_de_secours(self):
        u = utilisateur("e3@example.test", roles.ETUDIANT)
        erreur = urllib.error.HTTPError("http://x", 429, "quota", {}, io.BytesIO(b""))
        with mock.patch("espaces.assistant.lire_cle", return_value="cle"), \
                mock.patch("espaces.assistant.urllib.request.urlopen", side_effect=erreur):
            reponse = assistant.repondre("Où déposer le scan ?", u)
        self.assertEqual(reponse["mode"], "secours")
        self.assertIn("429", reponse["raison"])

    def test_reponse_inattendue_du_service_donne_le_mode_de_secours(self):
        u = utilisateur("e4@example.test", roles.ETUDIANT)
        faux = mock.MagicMock()
        faux.__enter__.return_value = io.BytesIO(json.dumps({"inattendu": True}).encode())
        with mock.patch("espaces.assistant.lire_cle", return_value="cle"), \
                mock.patch("espaces.assistant.urllib.request.urlopen", return_value=faux):
            self.assertEqual(assistant.repondre("Où déposer le scan ?", u)["mode"], "secours")

    def test_plafond_par_heure(self):
        self.avec_ia()
        u = utilisateur("e5@example.test", roles.ETUDIANT)
        for _ in range(assistant.QUESTIONS_PAR_HEURE):
            self.assertEqual(assistant.repondre("Où déposer le scan ?", u)["mode"], "ia")
        depasse = assistant.repondre("Où déposer le scan ?", u)
        self.assertEqual(depasse["mode"], "secours")
        self.assertIn("Plafond", depasse["raison"])

    def test_question_vide(self):
        self.assertEqual(assistant.repondre("   ", utilisateur("e6@example.test", roles.ETUDIANT))["mode"], "secours")


class RelectureTests(BaseTest):
    def test_secours_signale_un_sujet_trop_court(self):
        self.sans_cle()
        reponse = assistant.relire_sujet("Un stage en entreprise", utilisateur("e7@example.test", roles.ETUDIANT))
        self.assertEqual(reponse["mode"], "secours")
        self.assertIn("court", reponse["texte"])

    def test_secours_content_d_un_sujet_complet(self):
        self.sans_cle()
        sujet = ("Concevoir et développer un tableau de bord Python de suivi de la production d'un parc solaire, "
                 "avec un prototype livré à la fin du stage et un rapport sur les résultats obtenus.")
        self.assertIn("complet", assistant.relire_sujet(sujet, utilisateur("e8@example.test", roles.ETUDIANT))["texte"])

    def test_avec_ia(self):
        self.avec_ia("- Précisez les outils.")
        reponse = assistant.relire_sujet("Développer une application de suivi des stages", utilisateur("e9@example.test", roles.ETUDIANT))
        self.assertEqual(reponse["mode"], "ia")


class PagesTests(BaseTest):
    def test_page_reservee_aux_personnes_connectees(self):
        self.assertEqual(self.client.get(reverse("assistant")).status_code, 302)

    def test_page_en_mode_demonstration_sans_cle(self):
        self.sans_cle()
        self.client.force_login(utilisateur("p1@example.test", roles.ETUDIANT))
        self.assertContains(self.client.get(reverse("assistant")), "Mode démonstration")

    def test_question_et_reponse_affichees_avec_mention(self):
        self.avec_ia("Voici la réponse.")
        self.client.force_login(utilisateur("p2@example.test", roles.ETUDIANT))
        page = self.client.post(reverse("assistant"), {"question": "Où déposer le scan ?"})
        self.assertContains(page, "Voici la réponse.")
        self.assertContains(page, "Généré par une IA")

    def test_la_reponse_de_l_ia_n_est_jamais_interpretee_comme_du_html(self):
        self.avec_ia("<script>alert('x')</script>")
        self.client.force_login(utilisateur("p3@example.test", roles.ETUDIANT))
        page = self.client.post(reverse("assistant"), {"question": "test"})
        self.assertNotContains(page, "<script>alert")

    def test_lien_dans_le_menu(self):
        self.client.force_login(utilisateur("p4@example.test", roles.ETUDIANT))
        self.assertContains(self.client.get(reverse("accueil")), 'href="/assistant/"')

    def test_relecture_reservee_aux_etudiants_et_en_post(self):
        self.sans_cle()
        etudiant = utilisateur("p5@example.test", roles.ETUDIANT)
        encadrant = utilisateur("p6@example.test", roles.ENCADRANT)
        self.client.force_login(encadrant)
        self.assertEqual(self.client.post(reverse("assistant_relecture"), {"sujet": "x" * 50}).status_code, 403)
        self.client.force_login(etudiant)
        self.assertEqual(self.client.get(reverse("assistant_relecture")).status_code, 405)
        reponse = self.client.post(reverse("assistant_relecture"), {"sujet": "Un sujet de stage assez court"})
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json()["mode"], "secours")
