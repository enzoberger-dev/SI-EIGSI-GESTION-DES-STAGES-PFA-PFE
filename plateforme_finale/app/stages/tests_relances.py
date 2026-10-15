"""
Tests des relances automatiques et de la configuration des e-mails (Lot 5). Lancer : python manage.py test
"""

from datetime import date, timedelta
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Convention, Historique, ParametresEcole, Relance, Stage
from .pilotage import tableau_de_bord
from .relances import envoyer_relances
from .services import soumettre_stage
from .tests import LivrableBase


class RelancesBase(LivrableBase):
    def setUp(self):
        super().setUp()
        self.jour0 = timezone.localdate()   # jour où la fiche est soumise
        self.stage = self.stage_valide(self.etu3, self.p3, date(2027, 6, 1), date(2027, 7, 27))
        self.stage.statut = Stage.Statut.BROUILLON
        self.stage.save()
        self.assertEqual(soumettre_stage(self.stage, par=self.etu3), [])  # le coordinateur Karim est prévenu
        mail.outbox.clear()

    def dans(self, jours):
        return self.jour0 + timedelta(days=jours)

    def relancer(self, jours):
        return envoyer_relances(self.dans(jours))

    def messages_a(self, adresse):
        return [m for m in mail.outbox if adresse in m.to]


class RelanceValidationTests(RelancesBase):
    def test_aucune_relance_avant_le_premier_delai(self):
        self.relancer(2)
        self.assertEqual(mail.outbox, [])

    def test_relance_du_valideur_avec_lien_direct_et_recapitulatif(self):
        resultat = self.relancer(3)
        self.assertEqual(len(resultat["envoyes"]), 1)
        envoyes = self.messages_a("coord@example.test")
        self.assertEqual(len(envoyes), 1)
        self.assertIn("Adam", envoyes[0].subject)
        self.assertIn("3 jours", envoyes[0].body)
        self.assertIn("http://127.0.0.1:8000" + reverse("stages_a_valider"), envoyes[0].body)
        recap = self.messages_a("stages@example.test")
        self.assertEqual(len(recap), 1)
        self.assertIn("Récapitulatif", recap[0].subject)
        self.assertEqual(Relance.objects.count(), 1)

    @override_settings(SITE_URL="https://stages.ecole.test/")
    def test_le_lien_suit_le_reglage_site_url(self):
        self.relancer(3)
        self.assertIn("https://stages.ecole.test" + reverse("stages_a_valider"),
                      self.messages_a("coord@example.test")[0].body)

    def test_jamais_deux_fois_la_meme_relance(self):
        self.relancer(3)
        mail.outbox.clear()
        self.relancer(3)
        self.relancer(5)
        self.assertEqual(mail.outbox, [])
        self.relancer(7)   # le délai suivant
        self.assertEqual(len(self.messages_a("coord@example.test")), 1)
        self.assertEqual(Relance.objects.count(), 2)

    def test_un_seul_message_de_rattrapage_si_la_commande_n_a_pas_tourne(self):
        self.relancer(20)
        self.assertEqual(len(self.messages_a("coord@example.test")), 1)
        self.assertEqual(Relance.objects.count(), 2)   # les deux délais sont marqués comme faits
        mail.outbox.clear()
        self.relancer(21)
        self.assertEqual(mail.outbox, [])

    def test_arret_des_que_le_valideur_a_decide(self):
        self.stage.statut = Stage.Statut.VALIDE
        self.stage.save()
        self.relancer(30)
        self.assertEqual(mail.outbox, [])

    def test_nouveau_cycle_apres_refus_et_nouvelle_soumission(self):
        self.relancer(3)
        self.stage.statut = Stage.Statut.REFUSE
        self.stage.save()
        soumettre_stage(self.stage, par=self.etu3)   # nouvelle soumission : l'attente repart de zéro
        mail.outbox.clear()
        self.relancer(3)
        self.assertEqual(len(self.messages_a("coord@example.test")), 1)
        self.assertEqual(Relance.objects.count(), 2)  # une relance par cycle

    def test_delais_personnalises(self):
        ecole = ParametresEcole.actuels()
        ecole.relances_delais = "1, 2"
        ecole.save()
        self.assertEqual(ecole.delais_relances(), [1, 2])
        self.relancer(1)
        self.assertEqual(len(self.messages_a("coord@example.test")), 1)

    def test_aucun_valideur_prevenir_le_career_center(self):
        stage5 = self.stage_valide(self.etu5, self.p5, date(2027, 2, 1), date(2027, 7, 30))   # 5e : pas d'encadrant
        stage5.statut = Stage.Statut.SOUMIS
        stage5.save()
        mail.outbox.clear()
        resultat = self.relancer(10)
        self.assertEqual(resultat["sans_destinataire"], [stage5])
        self.assertEqual(Relance.objects.filter(stage=stage5).count(), 0)
        textes = " ".join(m.body for m in self.messages_a("stages@example.test"))
        self.assertIn("personne à relancer pour Yasmine", textes)

    def test_un_envoi_en_echec_est_retente_au_passage_suivant(self):
        with mock.patch("stages.relances.send_mail", side_effect=OSError("serveur injoignable")):
            resultat = self.relancer(3)
        self.assertEqual(resultat["erreurs"], 1)
        self.assertEqual(Relance.objects.count(), 0)   # rien d'enregistré
        self.relancer(3)
        self.assertEqual(Relance.objects.count(), 1)
        self.assertEqual(len(self.messages_a("coord@example.test")), 1)


class RelanceScanTests(RelancesBase):
    def setUp(self):
        super().setUp()
        self.stage.statut = Stage.Statut.VALIDE
        self.stage.save()
        self.convention = Convention.objects.create(
            stage=self.stage, numero="2026-0001", statut=Convention.Statut.ENVOYEE, envoyee_le=timezone.now())

    def test_l_etudiant_est_relance_pour_le_scan(self):
        self.relancer(3)
        envoyes = self.messages_a("adam@example.test")
        self.assertEqual(len(envoyes), 1)
        self.assertIn("scan", envoyes[0].subject)
        self.assertIn(reverse("mon_stage"), envoyes[0].body)

    def test_arret_des_que_le_scan_est_depose(self):
        self.convention.scan_signe = "conventions/1/scan.pdf"
        self.convention.save()
        self.relancer(30)
        self.assertEqual(self.messages_a("adam@example.test"), [])

    def test_pas_de_relance_pour_une_convention_signee(self):
        self.convention.statut = Convention.Statut.SIGNEE
        self.convention.save()
        self.relancer(30)
        self.assertEqual(mail.outbox, [])


class CommandesEtTableauTests(RelancesBase):
    def test_commande_envoyer_relances(self):
        sortie = StringIO()
        call_command("envoyer_relances", "--date", self.dans(3).isoformat(), stdout=sortie)
        self.assertIn("1 relance(s) envoyée(s)", sortie.getvalue())
        with self.assertRaises(CommandError):
            call_command("envoyer_relances", "--date", "pas-une-date")

    def test_tableau_de_bord_montre_les_relances_recentes(self):
        self.relancer(3)
        self.assertEqual(len(tableau_de_bord(self.annee)["relances_recentes"]), 1)
        self.client.force_login(self.career)
        reponse = self.client.get(reverse("tableau_de_bord"))
        self.assertContains(reponse, "Relances automatiques")
        self.assertContains(reponse, "coord@example.test")

    def test_commande_tester_email_mode_console(self):
        sortie = StringIO()
        call_command("tester_email", "essai@example.test", stdout=sortie)
        self.assertEqual(len(self.messages_a("essai@example.test")), 1)
        self.assertIn("Message envoyé", sortie.getvalue())

    def test_commande_tester_email_echec_lisible(self):
        with mock.patch("stages.management.commands.tester_email.send_mail", side_effect=OSError("refusé")):
            with self.assertRaises(CommandError) as erreur:
                call_command("tester_email", "essai@example.test", stdout=StringIO())
        self.assertIn("Échec de l'envoi", str(erreur.exception))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="smtp.ecole.test",
                       EMAIL_HOST_PASSWORD="secret-qui-ne-doit-pas-sortir")
    def test_tester_email_n_affiche_jamais_le_mot_de_passe(self):
        sortie = StringIO()
        with mock.patch("stages.management.commands.tester_email.send_mail"):
            call_command("tester_email", "essai@example.test", stdout=sortie)
        self.assertIn("SMTP (smtp.ecole.test", sortie.getvalue())
        self.assertNotIn("secret-qui-ne-doit-pas-sortir", sortie.getvalue())
