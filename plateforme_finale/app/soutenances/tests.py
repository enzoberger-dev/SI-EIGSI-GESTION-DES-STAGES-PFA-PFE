"""
Tests des soutenances (Lot 6). Lancer : python manage.py test
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes import roles
from stages.models import Convention, Historique, Inscription, ParametresEcole, Stage
from stages.tests import LivrableBase, creer

from .forms import CampagneForm
from .models import Campagne, Disponibilite, RelanceJury, ReponseJury, Salle, Soutenance
from .services import (
    deplacer_soutenance, enregistrer_disponibilites, envoyer_relances_jury, exporter_notes, generer_soutenances,
    jurys_sans_reponse, lire_note, ouvrir_campagne, proposer_planning, refuser_pv, saisir_pv, valider_pv,
    valider_planning,
)


def aware(jour, heure, minute=0):
    return timezone.make_aware(datetime(jour.year, jour.month, jour.day, heure, minute))


class SoutenancesBase(LivrableBase):
    """Une campagne du lundi 6 au vendredi 10 septembre 2027, 3 membres du jury, 2 salles, 2 étudiants de
    5e année dont le stage est validé et la convention signée."""

    def setUp(self):
        super().setUp()
        self.jury = [creer(f"jury{i}@example.test", roles.JURY, prenom=f"Jury{i}") for i in (1, 2, 3)]
        self.salle_a = Salle.objects.create(nom="Salle A")
        self.salle_b = Salle.objects.create(nom="Salle B")
        self.campagne = Campagne.objects.create(
            nom="PFE 2027", annee_universitaire=self.annee, annees_concernees="5",
            date_debut=date(2027, 9, 6), date_fin=date(2027, 9, 10),
        )
        self.stage_yasmine = self.stage_signe(self.etu5, self.p5, date(2027, 7, 30))
        self.etu5b = creer("hugo@example.test", roles.ETUDIANT, prenom="Hugo")
        Inscription.objects.create(etudiant=self.etu5b, promotion=self.p5)
        self.stage_hugo = self.stage_signe(self.etu5b, self.p5, date(2027, 8, 15))
        mail.outbox.clear()

    def stage_signe(self, etudiant, promotion, fin):
        stage = self.stage_valide(etudiant, promotion, date(2027, 2, 1), fin)
        Convention.objects.create(stage=stage, numero=f"2026-{etudiant.pk:04d}", statut=Convention.Statut.SIGNEE)
        return stage

    def tout_le_monde_disponible(self, membres=None):
        for membre in membres or self.jury:
            enregistrer_disponibilites(self.campagne, membre, self.campagne.creneaux())

    def messages_a(self, adresse):
        return [m for m in mail.outbox if adresse in m.to]

    def planifier_et_valider(self):
        self.tout_le_monde_disponible()
        proposer_planning(self.campagne)
        self.assertEqual(valider_planning(self.campagne, self.career), [])
        mail.outbox.clear()
        return Soutenance.objects.get(stage=self.stage_yasmine)


class CreneauxEtFormulaireTests(TestCase):
    def campagne(self, **champs):
        base = dict(nom="C", annee_universitaire="2026-2027", date_debut=date(2027, 9, 6), date_fin=date(2027, 9, 12))
        return Campagne(**{**base, **champs})

    def test_creneaux_hors_pause_et_hors_week_end(self):
        creneaux = self.campagne().creneaux()
        assert all(c.weekday() < 5 for c in creneaux)   # pas de samedi ni de dimanche
        lundi = [timezone.localtime(c).strftime("%H:%M") for c in creneaux if c.date() == date(2027, 9, 6)]
        self.assertEqual(lundi, ["09:00", "09:45", "10:30", "11:15", "14:00", "14:45", "15:30", "16:15"])
        self.assertEqual(len(creneaux), 5 * 8)

    def test_un_creneau_ne_depasse_pas_la_fin_de_journee(self):
        self.assertTrue(all(timezone.localtime(c).hour * 60 + timezone.localtime(c).minute + 45 <= 17 * 60
                            for c in self.campagne().creneaux()))

    def test_formulaire_valide_et_refus(self):
        donnees = {"nom": "PFE", "annee_universitaire": "2026-2027", "annees_concernees": "5", "date_debut": "2027-09-06",
                   "date_fin": "2027-09-10", "duree_minutes": 45, "heure_debut": "09:00", "heure_fin": "17:00",
                   "pause_debut": "12:00", "pause_fin": "14:00", "taille_jury": 2}
        self.assertTrue(CampagneForm(donnees).is_valid())
        for champ, valeur in [("annee_universitaire", "2026-2028"), ("annees_concernees", "6"), ("duree_minutes", 5),
                              ("taille_jury", 0), ("date_fin", "2027-09-01"), ("heure_fin", "08:00")]:
            self.assertFalse(CampagneForm({**donnees, champ: valeur}).is_valid(), champ)
        # week-end seulement : aucun créneau
        self.assertFalse(CampagneForm({**donnees, "date_debut": "2027-09-11", "date_fin": "2027-09-12"}).is_valid())


class DisponibilitesTests(SoutenancesBase):
    def test_ouverture_previent_chaque_membre_du_jury(self):
        self.assertEqual(ouvrir_campagne(self.campagne), 3)
        envoyes = self.messages_a("jury1@example.test")
        self.assertEqual(len(envoyes), 1)
        self.assertIn(reverse("jury_disponibilites", args=[self.campagne.pk]), envoyes[0].body)
        self.assertEqual(self.messages_a("sara@example.test"), [])   # un encadrant n'est pas du jury

    def test_enregistrement_remplace_et_ignore_les_faux_creneaux(self):
        creneaux = self.campagne.creneaux()
        faux = aware(date(2027, 9, 6), 3)   # 03:00 n'est pas un créneau
        self.assertEqual(enregistrer_disponibilites(self.campagne, self.jury[0], [creneaux[0], creneaux[1], faux]), [])
        self.assertEqual(Disponibilite.objects.filter(membre=self.jury[0]).count(), 2)
        enregistrer_disponibilites(self.campagne, self.jury[0], [creneaux[5]])
        self.assertEqual(list(Disponibilite.objects.filter(membre=self.jury[0]).values_list("debut", flat=True)), [creneaux[5]])

    def test_repondre_sans_aucune_disponibilite_compte_comme_une_reponse(self):
        enregistrer_disponibilites(self.campagne, self.jury[0], [])
        self.assertNotIn(self.jury[0], jurys_sans_reponse(self.campagne))
        self.assertIn(self.jury[1], jurys_sans_reponse(self.campagne))

    def test_refus_si_clos_ou_si_pas_du_jury(self):
        self.assertTrue(enregistrer_disponibilites(self.campagne, self.encadrant, []))
        self.campagne.statut = Campagne.Statut.PLANIFIEE
        self.campagne.save()
        self.assertTrue(enregistrer_disponibilites(self.campagne, self.jury[0], []))

    def test_relances_des_jurys_sans_reponse(self):
        jour0 = timezone.localdate()
        enregistrer_disponibilites(self.campagne, self.jury[0], [])   # jury1 a répondu
        self.assertEqual(envoyer_relances_jury(jour0 + timedelta(days=2)), 0)
        self.assertEqual(envoyer_relances_jury(jour0 + timedelta(days=3)), 2)   # jury2 et jury3
        self.assertEqual(self.messages_a("jury1@example.test"), [])
        mail.outbox.clear()
        self.assertEqual(envoyer_relances_jury(jour0 + timedelta(days=3)), 0)   # jamais deux fois
        self.assertEqual(envoyer_relances_jury(jour0 + timedelta(days=7)), 2)   # délai suivant
        self.assertEqual(RelanceJury.objects.count(), 4)
        enregistrer_disponibilites(self.campagne, self.jury[1], [])
        mail.outbox.clear()
        self.assertEqual(envoyer_relances_jury(jour0 + timedelta(days=20)), 0)   # tous les délais sont déjà passés

    def test_pas_de_relance_une_fois_la_campagne_planifiee(self):
        self.campagne.statut = Campagne.Statut.PLANIFIEE
        self.campagne.save()
        self.assertEqual(envoyer_relances_jury(timezone.localdate() + timedelta(days=30)), 0)


class PlanningTests(SoutenancesBase):
    def verifier_sans_conflit(self):
        """Un jury, une salle et un étudiant par créneau : aucune paire de soutenances ne se chevauche."""
        planifiees = list(Soutenance.objects.exclude(debut=None).prefetch_related("jury"))
        for i, a in enumerate(planifiees):
            for b in planifiees[i + 1:]:
                if a.debut < b.fin and b.debut < a.fin:
                    self.assertNotEqual(a.salle_id, b.salle_id)
                    self.assertFalse(set(a.jury.all()) & set(b.jury.all()))
                    self.assertNotEqual(a.stage.etudiant_id, b.stage.etudiant_id)

    def test_generation_seulement_des_stages_concernes(self):
        stage3 = self.stage_signe(self.etu3, self.p3, date(2027, 7, 30))   # 3e année : pas concernée
        self.assertEqual(generer_soutenances(self.campagne), 2)
        self.assertEqual(generer_soutenances(self.campagne), 0)   # sans doublon
        self.assertFalse(Soutenance.objects.filter(stage=stage3).exists())

    def test_stage_sans_convention_signee_exclu(self):
        Convention.objects.filter(stage=self.stage_hugo).update(statut=Convention.Statut.ENVOYEE)
        generer_soutenances(self.campagne)
        self.assertEqual(Soutenance.objects.count(), 1)

    def test_proposition_complete_et_sans_conflit(self):
        self.tout_le_monde_disponible()
        resultat = proposer_planning(self.campagne)
        self.assertEqual(resultat["planifiees"], 2)
        self.assertEqual(resultat["non_planifiables"], [])
        for s in Soutenance.objects.all():
            self.assertEqual(s.statut, Soutenance.Statut.PROPOSEE)
            self.assertEqual(s.jury.count(), 2)
            self.assertEqual(s.fin - s.debut, timedelta(minutes=45))
            self.assertIn(s.salle, (self.salle_a, self.salle_b))
        self.verifier_sans_conflit()
        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.statut, Campagne.Statut.PLANIFIEE)
        self.assertEqual(mail.outbox, [])   # rien n'est envoyé avant la validation

    def test_seuls_les_jurys_disponibles_sont_choisis(self):
        self.tout_le_monde_disponible(self.jury[:2])   # jury3 n'a rien coché
        proposer_planning(self.campagne)
        for s in Soutenance.objects.all():
            self.assertNotIn(self.jury[2], s.jury.all())

    def test_pas_assez_de_jurys_disponibles_ensemble(self):
        creneaux = self.campagne.creneaux()
        enregistrer_disponibilites(self.campagne, self.jury[0], [creneaux[0]])
        enregistrer_disponibilites(self.campagne, self.jury[1], [creneaux[1]])   # jamais libres en même temps
        resultat = proposer_planning(self.campagne)
        self.assertEqual(resultat["planifiees"], 0)
        self.assertEqual(len(resultat["non_planifiables"]), 2)

    def test_jamais_avant_la_fin_du_stage(self):
        Stage.objects.filter(pk=self.stage_yasmine.pk).update(date_fin=date(2027, 9, 8))
        self.tout_le_monde_disponible()
        proposer_planning(self.campagne)
        soutenance = Soutenance.objects.get(stage=self.stage_yasmine)
        self.assertGreaterEqual(timezone.localtime(soutenance.debut).date(), date(2027, 9, 8))

    def test_charge_equilibree_entre_les_jurys(self):
        creneaux_par_jour = 8
        self.tout_le_monde_disponible()
        proposer_planning(self.campagne)
        charges = [m.soutenances_jury.count() for m in self.jury]
        self.assertEqual(sum(charges), 4)          # 2 soutenances x 2 membres
        self.assertLessEqual(max(charges) - min(charges), 1)

    def test_erreurs_sans_salle_ou_sans_assez_de_jurys(self):
        Salle.objects.update(active=False)
        self.assertTrue(proposer_planning(self.campagne)["erreurs"])
        Salle.objects.update(active=True)
        self.campagne.taille_jury = 5
        self.assertTrue(proposer_planning(self.campagne)["erreurs"])

    def test_nouvelle_proposition_remplace_les_propositions_mais_pas_les_convocations(self):
        soutenance = self.planifier_et_valider()           # Yasmine et Hugo sont convoqués
        creneau_avant = soutenance.debut
        stage3 = self.stage_signe(self.etu3, self.p3, date(2027, 7, 30))
        self.campagne.annees_concernees = "3,5"
        self.campagne.save()
        proposer_planning(self.campagne)                    # le nouveau venu est placé, les autres ne bougent pas
        soutenance.refresh_from_db()
        self.assertEqual(soutenance.debut, creneau_avant)
        self.assertEqual(soutenance.statut, Soutenance.Statut.CONVOQUEE)
        nouveau = Soutenance.objects.get(stage=stage3)
        self.assertEqual(nouveau.statut, Soutenance.Statut.PROPOSEE)
        self.verifier_sans_conflit()


class DeplacementEtConvocationsTests(SoutenancesBase):
    def setUp(self):
        super().setUp()
        self.tout_le_monde_disponible()
        proposer_planning(self.campagne)
        self.s_y = Soutenance.objects.get(stage=self.stage_yasmine)
        self.s_h = Soutenance.objects.get(stage=self.stage_hugo)
        mail.outbox.clear()

    def test_validation_envoie_les_convocations_a_l_etudiant_et_au_jury(self):
        self.assertEqual(valider_planning(self.campagne, self.career), [])
        self.s_y.refresh_from_db()
        self.assertEqual(self.s_y.statut, Soutenance.Statut.CONVOQUEE)
        recu = self.messages_a("yasmine@example.test")
        self.assertEqual(len(recu), 1)
        self.assertIn("Convocation", recu[0].subject)
        self.assertIn(str(self.s_y.salle), recu[0].body)
        self.assertIn(f"{timezone.localtime(self.s_y.debut):%H:%M}", recu[0].body)
        for membre in self.s_y.jury.all():
            self.assertTrue(any("yasmine" in m.body.lower() or "Yasmine" in m.body for m in self.messages_a(membre.email)))
        self.assertEqual(len(mail.outbox), 2 * 3)   # 2 soutenances x (1 étudiant + 2 jurés)
        self.campagne.refresh_from_db()
        self.assertEqual(self.campagne.statut, Campagne.Statut.VALIDEE)
        self.assertTrue(self.stage_yasmine.historique.filter(action=Historique.Action.SOUTENANCE_CONVOQUEE).exists())

    def test_rien_a_valider(self):
        valider_planning(self.campagne, self.career)
        self.assertTrue(valider_planning(self.campagne, self.career))

    def test_deplacement_manuel_valide(self):
        debut = aware(date(2027, 9, 9), 10, 30)
        self.assertEqual(deplacer_soutenance(self.s_y, debut, self.salle_b, self.jury[:2], self.career), [])
        self.s_y.refresh_from_db()
        self.assertEqual(self.s_y.debut, debut)
        self.assertEqual(self.s_y.fin, debut + timedelta(minutes=45))
        self.assertEqual(mail.outbox, [])   # pas encore convoquée : pas de mise à jour

    def test_conflits_refuses(self):
        debut = self.s_h.debut
        erreurs = deplacer_soutenance(self.s_y, debut, self.s_h.salle, list(self.s_h.jury.all()), self.career)
        self.assertIn("Cette salle est déjà occupée à ce moment.", erreurs)
        self.assertIn("Un membre du jury a déjà une soutenance à ce moment.", erreurs)
        # chevauchement partiel (décalé de 15 minutes) : toujours refusé
        self.assertTrue(deplacer_soutenance(self.s_y, debut + timedelta(minutes=15), self.s_h.salle,
                                            list(self.s_h.jury.all())[:1], self.career))
        # même créneau mais salle et jurys différents : accepté
        libre = next(s for s in (self.salle_a, self.salle_b) if s != self.s_h.salle)
        autres = [m for m in self.jury if m not in self.s_h.jury.all()]
        self.assertEqual(deplacer_soutenance(self.s_y, debut, libre, autres, self.career), [])

    def test_jury_vide_ou_non_jury_refuses(self):
        debut = aware(date(2027, 9, 9), 9)
        self.assertTrue(deplacer_soutenance(self.s_y, debut, self.salle_a, [], self.career))
        self.assertTrue(deplacer_soutenance(self.s_y, debut, self.salle_a, [self.encadrant], self.career))

    def test_deplacer_une_soutenance_convoquee_envoie_une_mise_a_jour(self):
        valider_planning(self.campagne, self.career)
        self.s_y.refresh_from_db()
        mail.outbox.clear()
        debut = aware(date(2027, 9, 10), 14)
        self.assertEqual(deplacer_soutenance(self.s_y, debut, self.salle_b, self.jury[:2], self.career), [])
        recu = self.messages_a("yasmine@example.test")
        self.assertEqual(len(recu), 1)
        self.assertIn("MISE À JOUR", recu[0].subject)
        self.assertIn("remplacent", recu[0].body)
        self.assertEqual(len(mail.outbox), 3)
        self.s_y.refresh_from_db()
        self.assertEqual(self.s_y.statut, Soutenance.Statut.CONVOQUEE)

    def test_deplacement_impossible_apres_le_pv(self):
        valider_planning(self.campagne, self.career)
        self.s_y.refresh_from_db()
        self.assertEqual(saisir_pv(self.s_y, self.s_y.jury.first(), "12", "PV"), [])
        self.s_y.refresh_from_db()
        self.assertTrue(deplacer_soutenance(self.s_y, aware(date(2027, 9, 10), 9), self.salle_a, self.jury[:2], self.career))


class PvEtNotesTests(SoutenancesBase):
    def setUp(self):
        super().setUp()
        self.s = self.planifier_et_valider()
        self.membre = self.s.jury.first()
        self.intrus = next(m for m in self.jury if m not in self.s.jury.all()) if self.s.jury.count() < 3 else None

    def test_lecture_de_la_note(self):
        self.assertEqual(lire_note("14,5"), Decimal("14.50"))
        self.assertEqual(lire_note(" 14.25 "), Decimal("14.25"))
        self.assertEqual(lire_note("20"), Decimal("20.00"))
        self.assertEqual(lire_note("0"), Decimal("0.00"))
        for mauvais in ("20,01", "-1", "abc", "", "NaN", "1e3"):
            self.assertIsNone(lire_note(mauvais), mauvais)

    def test_saisie_par_un_membre_du_jury(self):
        self.assertEqual(saisir_pv(self.s, self.membre, "15,5", "Très bonne soutenance."), [])
        self.s.refresh_from_db()
        self.assertEqual((self.s.statut, self.s.note, self.s.pv_saisi_par), (Soutenance.Statut.PV_SAISI, Decimal("15.50"), self.membre))
        self.assertEqual(len(self.messages_a("stages@example.test")), 1)   # le Career Center est prévenu
        self.assertTrue(self.s.stage.historique.filter(action=Historique.Action.PV_SAISI).exists())

    def test_note_et_pv_obligatoires(self):
        self.assertTrue(saisir_pv(self.s, self.membre, "", "PV"))
        self.assertTrue(saisir_pv(self.s, self.membre, "21", "PV"))
        self.assertTrue(saisir_pv(self.s, self.membre, "12", "   "))
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Soutenance.Statut.CONVOQUEE)
        self.assertIsNone(self.s.note)

    def test_seuls_les_membres_du_jury_de_la_soutenance(self):
        autre = creer("jury9@example.test", roles.JURY)
        self.assertTrue(saisir_pv(self.s, autre, "12", "PV"))
        self.assertTrue(saisir_pv(self.s, self.encadrant, "12", "PV"))

    def test_pv_modifiable_jusqu_a_la_validation_puis_verrouille(self):
        saisir_pv(self.s, self.membre, "12", "Premier jet")
        self.assertEqual(saisir_pv(self.s, self.membre, "13", "Version corrigée"), [])
        self.s.refresh_from_db()
        self.assertEqual((self.s.note, self.s.pv), (Decimal("13.00"), "Version corrigée"))
        self.assertEqual(valider_pv(self.s, self.career), [])
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Soutenance.Statut.NOTEE)
        self.assertEqual(self.s.pv_valide_par, self.career)
        self.assertTrue(saisir_pv(self.s, self.membre, "20", "Tentative"))   # verrouillé
        self.assertTrue(valider_pv(self.s, self.career))                    # déjà validé
        self.assertTrue(self.s.stage.historique.filter(action=Historique.Action.NOTE_VALIDEE).exists())

    def test_valider_sans_pv_impossible(self):
        self.assertTrue(valider_pv(self.s, self.career))

    def test_renvoi_du_pv_avec_motif(self):
        saisir_pv(self.s, self.membre, "12", "PV")
        self.assertTrue(refuser_pv(self.s, self.career, "  "))   # motif obligatoire
        mail.outbox.clear()
        self.assertEqual(refuser_pv(self.s, self.career, "Appréciation manquante"), [])
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Soutenance.Statut.CONVOQUEE)
        self.assertEqual(self.s.pv, "PV")   # le brouillon est conservé
        for m in self.s.jury.all():
            self.assertIn("Appréciation manquante", self.messages_a(m.email)[0].body)

    def test_export_des_notes_validees_seulement(self):
        saisir_pv(self.s, self.membre, "14,5", "PV")
        self.assertEqual(exporter_notes(self.annee)[1], 0)   # pas encore validée
        valider_pv(self.s, self.career)
        octets, nb = exporter_notes(self.annee)
        self.assertEqual(nb, 1)
        texte = octets.decode("utf-8-sig")
        self.assertIn("Note /20", texte)
        self.assertIn(";14,50;", texte)           # virgule décimale
        self.assertIn("yasmine@example.test", texte)
        self.assertNotIn("hugo@example.test", texte)
        self.assertEqual(exporter_notes("2020-2021")[1], 0)


class EcransTests(SoutenancesBase):
    def donnees_campagne(self, **champs):
        return {"nom": "Nouvelle", "annee_universitaire": self.annee, "annees_concernees": "5", "date_debut": "2027-09-13",
                "date_fin": "2027-09-17", "duree_minutes": 45, "heure_debut": "09:00", "heure_fin": "17:00",
                "pause_debut": "12:00", "pause_fin": "14:00", "taille_jury": 2, **champs}

    def test_pages_du_career_center_reservees(self):
        pages = [reverse("soutenances"), reverse("soutenances_campagne", args=[self.campagne.pk]), reverse("export_notes")]
        for page in pages:
            self.assertEqual(self.client.get(page).status_code, 302)   # non connecté
        for utilisateur in (self.etu5, self.encadrant, self.jury[0]):
            self.client.force_login(utilisateur)
            for page in pages:
                self.assertEqual(self.client.get(page).status_code, 403, page)
        self.client.force_login(self.career)
        for page in pages:
            self.assertEqual(self.client.get(page).status_code, 200, page)

    def test_actions_post_refusees_aux_autres_et_en_get(self):
        s = Soutenance.objects.create(stage=self.stage_yasmine, campagne=self.campagne)
        actions = [reverse("soutenances_proposer", args=[self.campagne.pk]), reverse("soutenances_valider", args=[self.campagne.pk]),
                   reverse("soutenance_deplacer", args=[s.pk]), reverse("soutenance_pv_valider", args=[s.pk]),
                   reverse("soutenance_pv_refuser", args=[s.pk])]
        self.client.force_login(self.jury[0])
        for action in actions:
            self.assertEqual(self.client.post(action).status_code, 403)
        self.client.force_login(self.career)
        for action in actions:
            self.assertEqual(self.client.get(action).status_code, 405)

    def test_creation_de_campagne_previent_les_jurys(self):
        self.client.force_login(self.career)
        reponse = self.client.post(reverse("soutenances"), self.donnees_campagne())
        self.assertEqual(reponse.status_code, 302)
        self.assertEqual(Campagne.objects.count(), 2)
        self.assertEqual(len(self.messages_a("jury1@example.test")), 1)
        invalide = self.client.post(reverse("soutenances"), self.donnees_campagne(date_fin="2027-09-01"))
        self.assertContains(invalide, "Le dernier jour doit être après le premier")
        self.assertEqual(Campagne.objects.count(), 2)

    def test_parcours_complet_par_les_ecrans(self):
        # 1. les jurys répondent
        for membre in self.jury:
            self.client.force_login(membre)
            page = reverse("jury_disponibilites", args=[self.campagne.pk])
            self.assertContains(self.client.get(page), "Mes disponibilités")
            cles = [timezone.localtime(c).strftime("%Y-%m-%dT%H:%M") for c in self.campagne.creneaux()][:12]
            self.assertEqual(self.client.post(page, {"creneau": cles + ["2000-01-01T00:00"]}).status_code, 302)
            self.assertEqual(Disponibilite.objects.filter(membre=membre).count(), 12)
        # 2. le Career Center propose puis valide
        self.client.force_login(self.career)
        self.client.post(reverse("soutenances_proposer", args=[self.campagne.pk]))
        page = self.client.get(reverse("soutenances_campagne", args=[self.campagne.pk]))
        self.assertContains(page, "Valider (2) et envoyer les convocations")
        self.client.post(reverse("soutenances_valider", args=[self.campagne.pk]))
        s = Soutenance.objects.get(stage=self.stage_yasmine)
        self.assertEqual(s.statut, Soutenance.Statut.CONVOQUEE)
        # 3. l'étudiant voit sa soutenance
        self.client.force_login(self.etu5)
        self.assertContains(self.client.get(reverse("mon_stage")), "Ma soutenance")
        # 4. un juré saisit le PV, le Career Center valide
        membre = s.jury.first()
        self.client.force_login(membre)
        self.assertContains(self.client.get(reverse("jury_accueil")), "Saisir le PV")
        url_pv = reverse("jury_pv", args=[s.pk])
        self.assertContains(self.client.post(url_pv, {"note": "25", "pv": "x"}), "La note doit être")
        self.assertEqual(self.client.post(url_pv, {"note": "16", "pv": "Excellent"}).status_code, 302)
        self.client.force_login(self.career)
        self.assertContains(self.client.get(reverse("soutenances_campagne", args=[self.campagne.pk])), "Excellent")
        self.client.post(reverse("soutenance_pv_valider", args=[s.pk]))
        s.refresh_from_db()
        self.assertEqual(s.statut, Soutenance.Statut.NOTEE)
        # 5. export des notes
        reponse = self.client.get(reverse("export_notes"))
        self.assertRegex(reponse["Content-Disposition"], r'notes-soutenances-.*\.csv')
        self.assertIn("16,00", reponse.content.decode("utf-8-sig"))

    def test_l_etudiant_ne_voit_pas_un_creneau_seulement_propose(self):
        self.tout_le_monde_disponible()
        proposer_planning(self.campagne)
        self.client.force_login(self.etu5)
        self.assertNotContains(self.client.get(reverse("mon_stage")), "Ma soutenance")

    def test_pv_reserve_aux_membres_du_jury_de_la_soutenance(self):
        s = self.planifier_et_valider()
        url = reverse("jury_pv", args=[s.pk])
        autre = creer("jury9@example.test", roles.JURY)
        self.client.force_login(autre)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"note": "10", "pv": "x"}).status_code, 403)
        self.client.force_login(self.etu5)
        self.assertEqual(self.client.get(url).status_code, 403)
        s.refresh_from_db()
        self.assertEqual(s.statut, Soutenance.Statut.CONVOQUEE)

    def test_deplacement_par_formulaire_et_erreurs_lisibles(self):
        s = self.planifier_et_valider()
        self.client.force_login(self.career)
        url = reverse("soutenance_deplacer", args=[s.pk])
        jury_ids = [m.pk for m in self.jury[:2]]
        self.client.post(url, {"debut": "pas une date", "salle": self.salle_a.pk, "jury": jury_ids})
        self.client.post(url, {"debut": "2027-09-10T09:00", "salle": 9999, "jury": jury_ids})
        s.refresh_from_db()
        self.assertNotEqual(timezone.localtime(s.debut).strftime("%Y-%m-%dT%H:%M"), "2027-09-10T09:00")
        self.client.post(url, {"debut": "2027-09-10T09:00", "salle": self.salle_a.pk, "jury": jury_ids})
        s.refresh_from_db()
        self.assertEqual(timezone.localtime(s.debut).strftime("%Y-%m-%dT%H:%M"), "2027-09-10T09:00")
        self.assertEqual(len(self.messages_a("yasmine@example.test")), 1)   # mise à jour envoyée

    def test_disponibilites_close_apres_planification(self):
        self.campagne.statut = Campagne.Statut.PLANIFIEE
        self.campagne.save()
        self.client.force_login(self.jury[0])
        reponse = self.client.get(reverse("jury_disponibilites", args=[self.campagne.pk]))
        self.assertContains(reponse, "Le sondage est clos")
        self.client.post(reverse("jury_disponibilites", args=[self.campagne.pk]), {"creneau": ["2027-09-06T09:00"]})
        self.assertFalse(ReponseJury.objects.exists())

    def test_espace_jury_et_liens(self):
        self.client.force_login(self.jury[0])
        reponse = self.client.get(reverse("espace-jury"))
        self.assertContains(reponse, reverse("jury_accueil"))
        self.client.force_login(self.career)
        self.assertContains(self.client.get(reverse("espace-service-stages")), reverse("soutenances"))


class IntegrationTests(SoutenancesBase):
    def test_jury_de_3_membres_au_maximum(self):
        donnees = {"nom": "PFE", "annee_universitaire": "2026-2027", "annees_concernees": "5", "date_debut": "2027-09-06",
                   "date_fin": "2027-09-10", "duree_minutes": 45, "heure_debut": "09:00", "heure_fin": "17:00",
                   "pause_debut": "12:00", "pause_fin": "14:00"}
        self.assertTrue(CampagneForm({**donnees, "taille_jury": 3}).is_valid())
        self.assertFalse(CampagneForm({**donnees, "taille_jury": 4}).is_valid())

    def test_archive_du_dossier_avec_le_pv_valide_seulement(self):
        import io
        import zipfile
        from stages.echanges import dossier_zip
        s = self.planifier_et_valider()
        saisir_pv(s, s.jury.first(), "14,5", "Soutenance claire.\nBon travail.")
        stage = Stage.objects.get(pk=s.stage_id)
        noms = zipfile.ZipFile(io.BytesIO(dossier_zip(stage))).namelist()
        self.assertNotIn("soutenance-pv.txt", noms)           # PV pas encore validé
        valider_pv(s, self.career)
        stage = Stage.objects.get(pk=s.stage_id)
        archive = zipfile.ZipFile(io.BytesIO(dossier_zip(stage)))
        pv = archive.read("soutenance-pv.txt").decode()
        self.assertIn("14.50/20", pv)
        self.assertIn("Bon travail.", pv)
        self.assertIn("Soutenance :", archive.read("fiche-de-stage.txt").decode())

    def test_tableau_de_bord_suit_la_soutenance(self):
        from stages.pilotage import tableau_de_bord
        s = self.planifier_et_valider()
        etapes = lambda: {e["code"]: e["total"] for e in tableau_de_bord(self.annee)["etapes"]}   # noqa: E731
        self.assertEqual(etapes()["SOUTENANCE_PLANIFIEE"], 2)
        saisir_pv(s, s.jury.first(), "12", "PV")
        donnees = tableau_de_bord(self.annee)
        self.assertEqual({e["code"]: e["total"] for e in donnees["etapes"]}["PV_A_VALIDER"], 1)
        self.assertEqual(len(donnees["pv_a_valider"]), 1)
        valider_pv(s, self.career)
        self.assertEqual(etapes()["NOTE_VALIDEE"], 1)
        self.client.force_login(self.career)
        self.assertContains(self.client.get(reverse("tableau_de_bord")), "PV de soutenance à valider")

    def test_commande_quotidienne_relance_aussi_les_jurys(self):
        from io import StringIO
        from django.core.management import call_command
        sortie = StringIO()
        call_command("envoyer_relances", "--date", (timezone.localdate() + timedelta(days=3)).isoformat(), stdout=sortie)
        self.assertIn("3 relance(s) de jury", sortie.getvalue())
        self.assertEqual(len(self.messages_a("jury1@example.test")), 1)
