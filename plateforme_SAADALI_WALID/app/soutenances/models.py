"""
Tables des soutenances (Lot 6) : salles, campagnes, disponibilités des membres du jury, soutenances
(créneau, jury, PV et note) et relances des jurys qui n'ont pas répondu.

Hypothèses (à confirmer, voir docs/08-Decisions-ouvertes.md #32) : une soutenance par stage ;
jury de 2 membres par défaut ; seuls les stages des années d'études choisies dans la campagne
(5e année par défaut) ont une soutenance.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from stages.models import Stage, annee_universitaire_courante


class Salle(models.Model):
    """Une salle de soutenance. Gérée par le Career Center dans l'administration."""

    nom = models.CharField(max_length=60, unique=True)
    active = models.BooleanField(default=True, help_text="Une salle inactive n'est plus proposée au planning.")

    class Meta:
        verbose_name = "salle"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Campagne(models.Model):
    """Une période de soutenances : les jurys indiquent leurs disponibilités, puis le planning est
    proposé, validé et les convocations envoyées."""

    class Statut(models.TextChoices):
        OUVERTE = "OUVERTE", "Disponibilités en cours de collecte"
        PLANIFIEE = "PLANIFIEE", "Planning proposé, à valider"
        VALIDEE = "VALIDEE", "Planning validé, convocations envoyées"

    nom = models.CharField(max_length=120, help_text="Ex. : Soutenances PFE, septembre 2027")
    annee_universitaire = models.CharField("année universitaire", max_length=9, default=annee_universitaire_courante)
    annees_concernees = models.CharField(
        "années d'études concernées", max_length=20, default="5",
        help_text="Années dont les stages ont une soutenance, séparées par des virgules. Ex. : 5 ou 4,5",
    )
    date_debut = models.DateField("premier jour de soutenances")
    date_fin = models.DateField("dernier jour de soutenances")
    duree_minutes = models.PositiveSmallIntegerField("durée d'une soutenance (minutes)", default=45)
    heure_debut = models.TimeField("début de journée", default=time(9, 0))
    heure_fin = models.TimeField("fin de journée", default=time(17, 0))
    pause_debut = models.TimeField("début de pause", default=time(12, 0))
    pause_fin = models.TimeField("fin de pause", default=time(14, 0))
    taille_jury = models.PositiveSmallIntegerField("membres du jury par soutenance", default=2)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.OUVERTE)
    ouverte_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "campagne de soutenances"
        verbose_name_plural = "campagnes de soutenances"
        ordering = ["-date_debut"]

    def __str__(self):
        return self.nom

    def annees(self):
        """Années d'études concernées, en nombres."""
        return sorted({int(x) for x in self.annees_concernees.replace(" ", "").split(",") if x.isdigit()})

    def creneaux(self):
        """Tous les débuts de créneau possibles (heure locale), du lundi au vendredi, hors pause,
        sans dépasser la fin de journée."""
        duree = timedelta(minutes=self.duree_minutes)
        creneaux = []
        jour = self.date_debut
        while jour <= self.date_fin:
            if jour.weekday() < 5:
                debut = datetime.combine(jour, self.heure_debut)
                fin_journee = datetime.combine(jour, self.heure_fin)
                pause_debut = datetime.combine(jour, self.pause_debut)
                pause_fin = datetime.combine(jour, self.pause_fin)
                while debut + duree <= fin_journee:
                    if debut < pause_fin and debut + duree > pause_debut:
                        debut = pause_fin  # le créneau toucherait la pause : on repart après
                        continue
                    creneaux.append(timezone.make_aware(debut))
                    debut += duree
            jour += timedelta(days=1)
        return creneaux


class ReponseJury(models.Model):
    """Un membre du jury a répondu au sondage de disponibilités (même s'il n'est libre à aucun créneau)."""

    campagne = models.ForeignKey(Campagne, on_delete=models.CASCADE, related_name="reponses")
    membre = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    repondu_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "réponse de jury"
        constraints = [models.UniqueConstraint(fields=["campagne", "membre"], name="une_reponse_par_jury")]


class Disponibilite(models.Model):
    """Un créneau (début) où un membre du jury est disponible."""

    campagne = models.ForeignKey(Campagne, on_delete=models.CASCADE, related_name="disponibilites")
    membre = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    debut = models.DateTimeField()

    class Meta:
        verbose_name = "disponibilité"
        constraints = [models.UniqueConstraint(fields=["campagne", "membre", "debut"], name="une_dispo_par_creneau")]


class Soutenance(models.Model):
    """La soutenance d'un stage : créneau, salle, jury, puis PV et note."""

    class Statut(models.TextChoices):
        A_PLANIFIER = "A_PLANIFIER", "À planifier"
        PROPOSEE = "PROPOSEE", "Créneau proposé, à valider"
        CONVOQUEE = "CONVOQUEE", "Convocations envoyées"
        PV_SAISI = "PV_SAISI", "PV saisi, à valider"
        NOTEE = "NOTEE", "PV et note validés"

    stage = models.OneToOneField(Stage, on_delete=models.CASCADE, related_name="soutenance")
    campagne = models.ForeignKey(Campagne, on_delete=models.PROTECT, related_name="soutenances")
    debut = models.DateTimeField(null=True, blank=True)
    fin = models.DateTimeField(null=True, blank=True)
    salle = models.ForeignKey(Salle, on_delete=models.PROTECT, null=True, blank=True, related_name="soutenances")
    jury = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="soutenances_jury")
    statut = models.CharField(max_length=12, choices=Statut.choices, default=Statut.A_PLANIFIER)

    note = models.DecimalField("note sur 20", max_digits=4, decimal_places=2, null=True, blank=True)
    pv = models.TextField("procès-verbal", blank=True)
    pv_saisi_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="+")
    pv_saisi_le = models.DateTimeField(null=True, blank=True)
    pv_valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="+")
    pv_valide_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "soutenance"
        ordering = ["debut", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(note__isnull=True) | (Q(note__gte=Decimal("0")) & Q(note__lte=Decimal("20"))),
                name="note_entre_0_et_20",
            ),
        ]

    def __str__(self):
        return f"Soutenance de {self.stage.etudiant.get_full_name() or self.stage.etudiant.email}"

    @property
    def planifiee(self):
        return self.debut is not None


class RelanceJury(models.Model):
    """Trace d'une relance envoyée à un membre du jury qui n'a pas répondu au sondage : jamais deux fois."""

    campagne = models.ForeignKey(Campagne, on_delete=models.CASCADE, related_name="relances")
    membre = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    delai = models.SmallIntegerField(help_text="Jours d'attente qui ont déclenché cette relance")
    envoye_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "relance de jury"
        verbose_name_plural = "relances de jury"
        constraints = [models.UniqueConstraint(fields=["campagne", "membre", "delai"], name="une_relance_jury_par_delai")]
