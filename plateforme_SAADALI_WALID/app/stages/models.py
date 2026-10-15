"""
Tables du suivi des stages (Lot 1) : promotions, inscriptions, affectations
des encadrants, entreprises, fiches de stage et historique.

Modèle décrit dans docs/05-Donnees-MCD.md (« Modèle proposé v2 »).
Les règles marquées « hypothèse » sont à confirmer avec le prof.
"""

from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import Q


def annee_universitaire_courante(jour=None):
    """Renvoie l'année universitaire, par exemple « 2026-2027 ».
    Elle change le 1er septembre."""
    jour = jour or date.today()
    debut = jour.year if jour.month >= 9 else jour.year - 1
    return f"{debut}-{debut + 1}"


# --- Types de stage (règlement des études EIGSI 2026-2027, § III.8) --------
# Le type se déduit de l'année d'études de l'étudiant.
TYPE_PAR_ANNEE = {
    1: "Découverte",
    2: "Initiative personnelle",   # hypothèse : stage facultatif de 2e année
    3: "Technicien",
    4: "Assistant-Ingénieur",
    5: "Fin d'Études",
}
DUREE_MIN_SEMAINES = {1: 4, 2: 4, 3: 6, 4: 12, 5: 24}

# Hypothèse : à partir de la 4e année, c'est l'encadrant qui valide ;
# avant, c'est le coordinateur de promotion.
ANNEE_VALIDATION_PAR_ENCADRANT = 4


class Promotion(models.Model):
    """Une année d'études pour une année universitaire, ex. « 3e année 2026-2027 »."""

    ANNEES = [(n, f"{n}{'re' if n == 1 else 'e'} année") for n in range(1, 6)]

    annee_etudes = models.PositiveSmallIntegerField("année d'études", choices=ANNEES)
    annee_universitaire = models.CharField(
        "année universitaire", max_length=9, default=annee_universitaire_courante,
        help_text="Format : 2026-2027",
    )
    coordinateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="promotions_coordonnees", verbose_name="coordinateur de promotion",
    )
    volume_horaire = models.PositiveIntegerField(
        "volume horaire de l'année (heures)", null=True, blank=True,
        help_text="Repris dans la convention.",
    )

    class Meta:
        verbose_name = "promotion"
        ordering = ["-annee_universitaire", "annee_etudes"]
        constraints = [
            models.UniqueConstraint(
                fields=["annee_etudes", "annee_universitaire"], name="promotion_unique_par_annee"
            )
        ]

    def __str__(self):
        return f"{self.get_annee_etudes_display()} {self.annee_universitaire}"

    @property
    def type_stage(self):
        return TYPE_PAR_ANNEE[self.annee_etudes]

    @property
    def duree_min_semaines(self):
        return DUREE_MIN_SEMAINES[self.annee_etudes]

    @property
    def validation_par_encadrant(self):
        return self.annee_etudes >= ANNEE_VALIDATION_PAR_ENCADRANT


class Inscription(models.Model):
    """Un étudiant inscrit dans une promotion (une seule par année universitaire)."""

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inscriptions"
    )
    promotion = models.ForeignKey(Promotion, on_delete=models.PROTECT, related_name="inscriptions")
    # Recopiée depuis la promotion, pour pouvoir interdire 2 inscriptions la même année
    annee_universitaire = models.CharField(max_length=9, editable=False)

    class Meta:
        verbose_name = "inscription"
        constraints = [
            models.UniqueConstraint(
                fields=["etudiant", "annee_universitaire"], name="une_inscription_par_an"
            )
        ]

    def save(self, *args, **kwargs):
        self.annee_universitaire = self.promotion.annee_universitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.etudiant} — {self.promotion}"


class Affectation(models.Model):
    """Le Career Center affecte un encadrant à un étudiant (4e et 5e année).
    Un changement d'encadrant désactive l'ancienne ligne : l'historique est gardé."""

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="affectations"
    )
    encadrant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="etudiants_encadres"
    )
    annee_universitaire = models.CharField(max_length=9, default=annee_universitaire_courante)
    affecte_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="affectations_faites",
    )
    date_affectation = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "affectation"
        ordering = ["-date_affectation"]
        constraints = [
            # Une seule affectation ACTIVE par étudiant et par année
            models.UniqueConstraint(
                fields=["etudiant", "annee_universitaire"], condition=Q(active=True),
                name="une_affectation_active_par_an",
            )
        ]

    def __str__(self):
        etat = "" if self.active else " (ancienne)"
        return f"{self.etudiant} → {self.encadrant} ({self.annee_universitaire}){etat}"


class Entreprise(models.Model):
    """Organisme d'accueil. Réutilisé d'un stage à l'autre : il forme l'annuaire des entreprises."""

    raison_sociale = models.CharField(max_length=150, unique=True)
    adresse = models.CharField(max_length=255, blank=True)
    code_postal = models.CharField(max_length=10, blank=True)
    ville = models.CharField(max_length=80, blank=True)
    pays = models.CharField(max_length=60, default="Maroc")
    telephone = models.CharField(max_length=30, blank=True)
    email_contact = models.EmailField("e-mail de contact", blank=True)

    class Meta:
        verbose_name = "entreprise"
        ordering = ["raison_sociale"]

    def __str__(self):
        return self.raison_sociale


class Stage(models.Model):
    """La fiche de stage remplie par l'étudiant. Ses champs reprennent ceux de la convention.
    Un brouillon peut être incomplet ; la soumission exige les champs obligatoires."""

    class Statut(models.TextChoices):
        BROUILLON = "BROUILLON", "Brouillon"
        SOUMIS = "SOUMIS", "Soumis, en attente de validation"
        VALIDE = "VALIDE", "Validé"
        REFUSE = "REFUSE", "Refusé, à corriger"

    class Origine(models.TextChoices):
        RESEAU = "RESEAU", "Réseau personnel"
        SITE_EMPLOI = "SITE_EMPLOI", "Site d'emploi (Indeed, JobTeaser…)"
        CAREER_CENTER = "CAREER_CENTER", "Career Center"
        OFFRE_PARTENAIRE = "OFFRE_PARTENAIRE", "Offre d'une entreprise partenaire"

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stages"
    )
    promotion = models.ForeignKey(Promotion, on_delete=models.PROTECT, related_name="stages")
    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.PROTECT, null=True, blank=True, related_name="stages"
    )
    origine = models.CharField(max_length=20, choices=Origine.choices, blank=True)

    # Sujet et lieu
    sujet = models.TextField("sujet de stage, activités confiées", blank=True)
    lieu_si_different = models.TextField("lieu du stage (si différent de l'adresse)", blank=True)

    # Personnes côté entreprise
    representant_nom = models.CharField("représentant de l'entreprise", max_length=120, blank=True)
    representant_fonction = models.CharField("fonction du représentant", max_length=80, blank=True)
    tuteur_nom = models.CharField("tuteur (nom)", max_length=120, blank=True)
    tuteur_email = models.EmailField("tuteur (e-mail)", blank=True)
    tuteur_telephone = models.CharField("tuteur (téléphone)", max_length=30, blank=True)

    # Modalités (article 3 de la convention)
    date_debut = models.DateField("date de début", null=True, blank=True)
    date_fin = models.DateField("date de fin", null=True, blank=True)
    heures_max_semaine = models.PositiveSmallIntegerField(
        "durée hebdomadaire maximale (heures)", null=True, blank=True
    )
    horaires = models.CharField("horaires de présence", max_length=150, blank=True)
    cas_particuliers = models.TextField("présence la nuit, le dimanche ou un jour férié", blank=True)

    # Gratification (article 5, facultative)
    gratification_montant = models.DecimalField(
        "gratification (MAD par mois)", max_digits=8, decimal_places=2, null=True, blank=True
    )
    gratification_modalites = models.CharField("modalités de versement", max_length=150, blank=True)
    avantages_nature = models.TextField("avantages en nature", blank=True)

    # Suivi
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.BROUILLON)
    date_limite_rapport = models.DateField("date limite du rapport", null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    # Champs à remplir avant de pouvoir soumettre la fiche
    CHAMPS_OBLIGATOIRES = [
        "entreprise", "origine", "sujet", "representant_nom", "representant_fonction",
        "tuteur_nom", "tuteur_email", "date_debut", "date_fin", "heures_max_semaine",
    ]

    class Meta:
        verbose_name = "stage"
        ordering = ["-modifie_le"]
        constraints = [
            # Un seul stage par étudiant et par promotion (donc par année)
            models.UniqueConstraint(fields=["etudiant", "promotion"], name="un_stage_par_an"),
        ]

    def __str__(self):
        entreprise = self.entreprise or "entreprise à préciser"
        return f"{self.etudiant.get_full_name() or self.etudiant} — {self.type_stage} — {entreprise}"

    # --- Informations calculées ------------------------------------------
    @property
    def type_stage(self):
        return self.promotion.type_stage

    @property
    def duree_semaines(self):
        """Durée du stage en semaines (avec une décimale), ou None si les dates manquent."""
        if self.date_debut and self.date_fin:
            return round((self.date_fin - self.date_debut).days / 7, 1)
        return None

    def valideur(self):
        """Qui doit valider ce stage : l'encadrant (4e, 5e) ou le coordinateur (1re à 3e).
        Renvoie None s'il n'y a encore personne (pas d'affectation, pas de coordinateur)."""
        if self.promotion.validation_par_encadrant:
            affectation = Affectation.objects.filter(
                etudiant=self.etudiant,
                annee_universitaire=self.promotion.annee_universitaire,
                active=True,
            ).first()
            return affectation.encadrant if affectation else None
        return self.promotion.coordinateur

    # --- Règles avant soumission -----------------------------------------
    def erreurs_soumission(self):
        """Liste des problèmes qui empêchent de soumettre la fiche (vide = tout va bien)."""
        erreurs = []
        manquants = [
            self._meta.get_field(nom).verbose_name
            for nom in self.CHAMPS_OBLIGATOIRES
            if getattr(self, nom) in (None, "")
        ]
        if manquants:
            erreurs.append("Champs obligatoires à remplir : " + ", ".join(manquants) + ".")
        if self.date_debut and self.date_fin:
            if self.date_fin <= self.date_debut:
                erreurs.append("La date de fin doit être après la date de début.")
            elif self.duree_semaines < self.promotion.duree_min_semaines:
                erreurs.append(
                    f"Un stage « {self.type_stage} » doit durer au moins "
                    f"{self.promotion.duree_min_semaines} semaines "
                    f"(ici : {self.duree_semaines} semaines)."
                )
        if self.valideur() is None:
            if self.promotion.validation_par_encadrant:
                erreurs.append("Aucun encadrant ne vous est encore affecté : contactez le Career Center.")
            else:
                erreurs.append("Votre promotion n'a pas encore de coordinateur : contactez le Career Center.")
        return erreurs


class ParametresEcole(models.Model):
    """Informations de l'école reprises dans la convention. Une seule ligne, modifiable
    par le Career Center dans l'administration (rien n'est écrit en dur dans le code)."""

    nom = models.CharField("nom de l'école", max_length=150, default="EIGSI Casablanca")
    sigle = models.CharField("sigle", max_length=20, default="EIGSICA")
    adresse = models.CharField(max_length=255, default="282, route de l'Oasis, 20410 Casablanca - Maroc")
    site_web = models.CharField(max_length=100, blank=True, default="www.eigsica.ma")
    representant = models.CharField("représentant (directeur du campus)", max_length=120, blank=True)
    directeur_etudes = models.CharField("directeur des études et de la recherche", max_length=120, blank=True)
    email_contact = models.EmailField("e-mail du Career Center", default="stages@example.test")
    telephone = models.CharField(max_length=30, blank=True)
    cursus = models.CharField(max_length=100, default="Ingénieur généraliste EIGSI")
    # Calendrier des rappels automatiques (Lot 3 bis) : nombre de jours avant / après la date limite
    rappels_avant = models.CharField(
        "rappels avant la date limite (jours)", max_length=40, default="7,3,1",
        help_text="Jours avant la date limite, séparés par des virgules. Ex. : 7,3,1",
    )
    rappels_apres = models.CharField(
        "rappels après la date limite (jours)", max_length=40, default="1,7", blank=True,
        help_text="Jours de retard, séparés par des virgules. Ex. : 1,7",
    )

    def decalages_rappels(self):
        """Liste des décalages en jours : +7 = 7 jours avant l'échéance, -1 = 1 jour après."""
        def lire(texte):
            return [int(x) for x in texte.replace(" ", "").split(",") if x.isdigit()]
        return sorted(set(lire(self.rappels_avant)) | {-n for n in lire(self.rappels_apres)}, reverse=True)

    # Relances automatiques (Lot 5) : jours d'attente avant chaque relance
    relances_delais = models.CharField(
        "relances après (jours d'attente)", max_length=40, default="3,7",
        help_text="Un valideur qui n'a pas décidé, ou un étudiant qui n'a pas déposé son scan, est relancé "
                  "après ce nombre de jours d'attente. Ex. : 3,7",
    )

    def delais_relances(self):
        """Liste triée des délais de relance, en jours."""
        return sorted({int(x) for x in self.relances_delais.replace(" ", "").split(",") if x.isdigit()})

    class Meta:
        verbose_name = "paramètres de l'école"
        verbose_name_plural = "paramètres de l'école"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        self.pk = 1  # une seule ligne
        super().save(*args, **kwargs)

    @classmethod
    def actuels(cls):
        """Les paramètres de l'école (créés avec les valeurs par défaut s'ils n'existent pas)."""
        return cls.objects.get_or_create(pk=1)[0]


def dossier_convention(convention, nom_fichier):
    """Chemin de rangement d'un fichier de convention (hors des pages publiques)."""
    return f"conventions/{convention.stage_id}/{nom_fichier}"


class Convention(models.Model):
    """Convention de stage d'un stage validé. Une correction crée une nouvelle VERSION :
    l'ancienne reste conservée, marquée REMPLACEE."""

    class Statut(models.TextChoices):
        GENEREE = "GENEREE", "Générée (à faire signer par l'école)"
        ENVOYEE = "ENVOYEE", "Envoyée à l'étudiant (signée par l'école)"
        SIGNEE = "SIGNEE", "Signée par toutes les parties"
        REMPLACEE = "REMPLACEE", "Remplacée par une nouvelle version"

    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="conventions")
    numero = models.CharField("numéro", max_length=20, db_index=True)  # ex. 2026-0001
    version = models.PositiveSmallIntegerField(default=1)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.GENEREE)
    fichier_pdf = models.FileField(upload_to=dossier_convention, blank=True)
    scan_signe = models.FileField("scan signé", upload_to=dossier_convention, blank=True)
    genere_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    envoyee_le = models.DateTimeField("signée par l'école / envoyée le", null=True, blank=True)
    scan_depose_le = models.DateTimeField(null=True, blank=True)
    signee_le = models.DateTimeField("signée par toutes les parties le", null=True, blank=True)

    class Meta:
        verbose_name = "convention"
        ordering = ["-cree_le"]
        constraints = [
            models.UniqueConstraint(fields=["stage", "version"], name="une_version_par_stage"),
            # Une seule convention EN VIGUEUR (non remplacée) par stage
            models.UniqueConstraint(
                fields=["stage"], condition=~Q(statut="REMPLACEE"), name="une_convention_en_vigueur"
            ),
        ]

    def __str__(self):
        return f"Convention n° {self.numero} (v{self.version})"

    @property
    def en_vigueur(self):
        return self.statut != self.Statut.REMPLACEE


class Historique(models.Model):
    """Le fil du dossier : qui a fait quoi, et quand. Une seule table pour toutes les actions."""

    class Action(models.TextChoices):
        CREATION = "CREATION", "Fiche créée"
        SOUMISSION = "SOUMISSION", "Fiche soumise"
        VALIDATION = "VALIDATION", "Stage validé"
        REFUS = "REFUS", "Stage refusé"
        AFFECTATION = "AFFECTATION", "Encadrant affecté"
        CONVENTION_GENEREE = "CONVENTION_GENEREE", "Convention générée"
        CONVENTION_ENVOYEE = "CONVENTION_ENVOYEE", "Convention signée par l'école et envoyée"
        SCAN_DEPOSE = "SCAN_DEPOSE", "Scan de la convention signée déposé"
        SCAN_REFUSE = "SCAN_REFUSE", "Scan refusé, à redéposer"
        LIVRABLE_RENDU = "LIVRABLE_RENDU", "Livrable marqué comme rendu (Moodle)"
        LIVRABLE_ANNULE = "LIVRABLE_ANNULE", "Livrable remis « à rendre »"
        DELAI_PROLONGE = "DELAI_PROLONGE", "Date limite prolongée"
        CONVENTION_SIGNEE = "CONVENTION_SIGNEE", "Convention signée par toutes les parties"
        SOUTENANCE_CONVOQUEE = "SOUTENANCE_CONVOQUEE", "Soutenance planifiée, convocations envoyées"
        PV_SAISI = "PV_SAISI", "PV de soutenance et note saisis par le jury"
        PV_REFUSE = "PV_REFUSE", "PV renvoyé au jury pour correction"
        NOTE_VALIDEE = "NOTE_VALIDEE", "PV et note validés par le Career Center"

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="historique")
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=25, choices=Action.choices)
    commentaire = models.TextField(blank=True, help_text="Obligatoire pour un refus (motif).")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "événement d'historique"
        verbose_name_plural = "historique"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date:%d/%m/%Y %H:%M} — {self.get_action_display()}"


# ---------------------------------------------------------------------------
# Lot 3 bis : suivi des livrables et rappels automatiques
#
# Les livrables (rapport, plan directeur…) sont RENDUS SUR MOODLE, pas sur cette plateforme.
# La plateforme ne garde donc que : la liste des livrables attendus, leur date limite, un statut
# « à rendre / rendu » (mis à jour par le Career Center) et les rappels envoyés aux étudiants.
# ---------------------------------------------------------------------------

class ModeleLivrable(models.Model):
    """Livrable attendu pour un type de stage, avec la façon de calculer sa date limite.
    Modifiable par le Career Center dans l'administration. Valeurs de départ tirées du « Guide des
    stages et des expériences professionnelles » (livret 1) et de Walid."""

    class Calcul(models.TextChoices):
        FIXE = "FIXE", "Date fixe de l'année du stage (jour et mois)"
        DEBUT = "DEBUT", "Début du stage + jours"
        FIN = "FIN", "Fin du stage + jours"

    type_stage = models.CharField(
        "type de stage", max_length=30, choices=[(nom, nom) for nom in TYPE_PAR_ANNEE.values()]
    )
    nom = models.CharField(max_length=120)
    est_rapport = models.BooleanField("c'est le rapport final", default=False)
    calcul = models.CharField("date limite calculée à partir de", max_length=10, choices=Calcul.choices,
                              default=Calcul.FIXE)
    mois = models.PositiveSmallIntegerField("mois (date fixe)", null=True, blank=True)
    jour = models.PositiveSmallIntegerField("jour (date fixe)", null=True, blank=True)
    jours = models.SmallIntegerField("jours à ajouter (début ou fin du stage)", default=0)
    lien_moodle = models.URLField("lien du devoir sur Moodle", blank=True,
                                  help_text="Repris dans les rappels envoyés aux étudiants.")
    ordre = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "modèle de livrable"
        verbose_name_plural = "modèles de livrables"
        ordering = ["type_stage", "ordre"]
        constraints = [models.UniqueConstraint(fields=["type_stage", "nom"], name="un_modele_par_nom_et_type")]

    def __str__(self):
        return f"{self.type_stage} : {self.nom}"

    def date_limite(self, stage):
        """Date limite pour ce stage (None si les dates du stage ou du modèle manquent)."""
        from datetime import timedelta
        if not (stage.date_debut and stage.date_fin):
            return None
        if self.calcul == self.Calcul.DEBUT:
            return stage.date_debut + timedelta(days=self.jours)
        if self.calcul == self.Calcul.FIN:
            return stage.date_fin + timedelta(days=self.jours)
        if not (self.mois and self.jour):
            return None
        fixe = date(stage.date_fin.year, self.mois, self.jour)
        # Si la date fixe tombe avant la fin du stage, on laisse 14 jours après la fin
        return fixe if fixe >= stage.date_fin else stage.date_fin + timedelta(days=14)


class Livrable(models.Model):
    """Un livrable à rendre sur Moodle pour un stage (créé quand la convention est signée)."""

    class Statut(models.TextChoices):
        A_RENDRE = "A_RENDRE", "À rendre"
        RENDU = "RENDU", "Rendu"

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="livrables")
    modele = models.ForeignKey(ModeleLivrable, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    nom = models.CharField(max_length=120)
    est_rapport = models.BooleanField(default=False)
    date_limite = models.DateField()
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.A_RENDRE)
    rendu_le = models.DateTimeField(null=True, blank=True)
    rendu_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="+")

    class Meta:
        verbose_name = "livrable"
        ordering = ["date_limite", "id"]
        constraints = [models.UniqueConstraint(fields=["stage", "nom"], name="un_livrable_par_nom_et_stage")]

    def __str__(self):
        return f"{self.nom} — {self.stage}"

    @property
    def lien_moodle(self):
        return self.modele.lien_moodle if self.modele_id else ""


class Rappel(models.Model):
    """Trace d'un rappel envoyé à un étudiant : il garantit qu'un même rappel n'est jamais envoyé
    deux fois, même si la commande quotidienne est lancée plusieurs fois le même jour."""

    livrable = models.ForeignKey(Livrable, on_delete=models.CASCADE, related_name="rappels")
    decalage = models.SmallIntegerField(help_text="+7 = 7 jours avant l'échéance ; -1 = 1 jour de retard")
    destinataire = models.EmailField()
    envoye_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "rappel envoyé"
        verbose_name_plural = "rappels envoyés"
        ordering = ["-envoye_le"]
        constraints = [models.UniqueConstraint(fields=["livrable", "decalage"], name="un_rappel_par_decalage")]

    def __str__(self):
        return f"Rappel {self.decalage:+d} j — {self.livrable}"


class Relance(models.Model):
    """Trace d'une relance envoyée pour une attente en cours (Lot 5). Elle garantit qu'une même relance
    n'est jamais envoyée deux fois : la clé est (stage, type, début de l'attente, délai)."""

    class Type(models.TextChoices):
        VALIDATION = "VALIDATION", "Fiche en attente de décision du valideur"
        SCAN = "SCAN", "Scan de la convention signée à déposer par l'étudiant"

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="relances")
    type = models.CharField(max_length=12, choices=Type.choices)
    depuis = models.DateTimeField(help_text="Début de l'attente (soumission de la fiche, envoi de la convention)")
    delai = models.SmallIntegerField(help_text="Jours d'attente qui ont déclenché cette relance")
    destinataire = models.EmailField()
    envoye_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "relance envoyée"
        verbose_name_plural = "relances envoyées"
        ordering = ["-envoye_le"]
        constraints = [
            models.UniqueConstraint(fields=["stage", "type", "depuis", "delai"], name="une_relance_par_attente_et_delai")
        ]

    def __str__(self):
        return f"Relance {self.get_type_display()} ({self.delai} j) — {self.stage}"


def dossier_livrable(depot, nom_fichier):
    """Conservée UNIQUEMENT parce que l'ancienne migration 0004 (dépôt de livrables, abandonné) la
    référence. Elle ne sert plus à rien : les livrables sont rendus sur Moodle."""
    return nom_fichier
