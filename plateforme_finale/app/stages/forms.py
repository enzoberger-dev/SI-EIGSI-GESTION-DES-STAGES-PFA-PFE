"""
Formulaires du suivi des stages.
"""

from django import forms
from django.contrib.auth import get_user_model

from comptes import roles

from .models import Entreprise, Stage


class AffectationForm(forms.Form):
    """Choix d'un encadrant pour un étudiant (écran du Career Center)."""

    etudiant = forms.ModelChoiceField(queryset=get_user_model().objects.none(), widget=forms.HiddenInput)
    encadrant = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(groups__name=roles.ENCADRANT),
        empty_label="— choisir un encadrant —",
    )

    def __init__(self, *args, etudiants_possibles=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Seuls les étudiants listés à l'écran (4e et 5e année) sont acceptés
        if etudiants_possibles is not None:
            self.fields["etudiant"].queryset = etudiants_possibles


class DecisionForm(forms.Form):
    """Décision du valideur sur une fiche soumise (US-02)."""

    decision = forms.ChoiceField(
        label="Décision",
        choices=[("valider", "Valider le stage"), ("refuser", "Refuser (l'étudiant devra corriger)")],
        widget=forms.RadioSelect,
    )
    motif = forms.CharField(
        label="Motif / commentaire", required=False, widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Obligatoire en cas de refus. Il sera envoyé à l'étudiant.",
    )

    def clean(self):
        donnees = super().clean()
        if donnees.get("decision") == "refuser" and not donnees.get("motif", "").strip():
            self.add_error("motif", "Un refus doit être accompagné d'un motif.")
        return donnees


def _date():
    # Calendrier du navigateur ; la valeur est échangée au format AAAA-MM-JJ
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class StageForm(forms.ModelForm):
    """Fiche de stage de l'étudiant (US-01). Les champs suivent la convention EIGSICA.

    Ici, tous les champs sont facultatifs pour pouvoir enregistrer un brouillon.
    Les champs obligatoires sont vérifiés au moment de la soumission
    (Stage.erreurs_soumission) et signalés par une étoile.
    """

    # L'entreprise est saisie en clair ; elle est retrouvée ou créée à l'enregistrement
    entreprise_nom = forms.CharField(label="Raison sociale", max_length=150, required=False)
    entreprise_adresse = forms.CharField(label="Adresse", max_length=255, required=False)
    entreprise_code_postal = forms.CharField(label="Code postal", max_length=10, required=False)
    entreprise_ville = forms.CharField(label="Ville", max_length=80, required=False)
    entreprise_pays = forms.CharField(label="Pays", max_length=60, required=False, initial="Maroc")
    entreprise_telephone = forms.CharField(label="Téléphone de l'entreprise", max_length=30, required=False)
    entreprise_email = forms.EmailField(label="E-mail de l'entreprise", required=False)

    CHAMPS_ENTREPRISE = ["adresse", "code_postal", "ville", "pays", "telephone"]

    class Meta:
        model = Stage
        fields = [
            "origine", "sujet", "lieu_si_different",
            "representant_nom", "representant_fonction",
            "tuteur_nom", "tuteur_email", "tuteur_telephone",
            "date_debut", "date_fin", "heures_max_semaine", "horaires", "cas_particuliers",
            "gratification_montant", "gratification_modalites", "avantages_nature",
        ]
        widgets = {
            "date_debut": _date(),
            "date_fin": _date(),
            "sujet": forms.Textarea(attrs={"rows": 3}),
            "lieu_si_different": forms.Textarea(attrs={"rows": 2}),
            "cas_particuliers": forms.Textarea(attrs={"rows": 2}),
            "avantages_nature": forms.Textarea(attrs={"rows": 2}),
        }

    # Rubriques de l'écran, dans l'ordre de la convention
    RUBRIQUES = [
        ("Organisme d'accueil", ["entreprise_nom", "entreprise_adresse", "entreprise_code_postal",
                                 "entreprise_ville", "entreprise_pays", "entreprise_telephone",
                                 "entreprise_email", "lieu_si_different"]),
        ("Personnes dans l'entreprise", ["representant_nom", "representant_fonction",
                                         "tuteur_nom", "tuteur_email", "tuteur_telephone"]),
        ("Le stage", ["origine", "sujet", "date_debut", "date_fin"]),
        ("Modalités", ["heures_max_semaine", "horaires", "cas_particuliers"]),
        ("Gratification (facultative)", ["gratification_montant", "gratification_modalites",
                                         "avantages_nature"]),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir l'entreprise déjà choisie
        entreprise = self.instance.entreprise if self.instance.pk else None
        if entreprise:
            self.initial["entreprise_nom"] = entreprise.raison_sociale
            self.initial["entreprise_email"] = entreprise.email_contact
            for champ in self.CHAMPS_ENTREPRISE:
                self.initial[f"entreprise_{champ}"] = getattr(entreprise, champ)
        # Étoile sur les champs obligatoires pour soumettre
        obligatoires = set(Stage.CHAMPS_OBLIGATOIRES) | {"entreprise_nom"}
        for nom, champ in self.fields.items():
            if nom in obligatoires:
                champ.label = f"{champ.label} *"

    def clean(self):
        donnees = super().clean()
        debut, fin = donnees.get("date_debut"), donnees.get("date_fin")
        if debut and fin and fin <= debut:
            self.add_error("date_fin", "La date de fin doit être après la date de début.")
        return donnees

    def rubriques(self):
        """Champs regroupés par rubrique, pour l'affichage."""
        return [(titre, [self[nom] for nom in noms]) for titre, noms in self.RUBRIQUES]

    def save(self, commit=True):
        stage = super().save(commit=False)
        nom = self.cleaned_data.get("entreprise_nom", "").strip()
        if nom:
            # Entreprise déjà connue (sans tenir compte des majuscules) : on la réutilise
            # telle quelle. Sinon on la crée avec les informations saisies.
            # Comparaison faite en Python : la recherche « sans majuscules » de SQLite
            # ignore les lettres accentuées (É ≠ é), ce qui créerait des doublons.
            cle = nom.casefold()
            entreprise = next(
                (e for e in Entreprise.objects.only("id", "raison_sociale") if e.raison_sociale.casefold() == cle),
                None,
            )
            if entreprise is None:
                entreprise = Entreprise.objects.create(
                    raison_sociale=nom,
                    email_contact=self.cleaned_data.get("entreprise_email", ""),
                    **{c: self.cleaned_data.get(f"entreprise_{c}", "") for c in self.CHAMPS_ENTREPRISE},
                )
                if not entreprise.pays:
                    entreprise.pays = "Maroc"
                    entreprise.save(update_fields=["pays"])
            stage.entreprise = entreprise
        else:
            stage.entreprise = None
        if commit:
            stage.save()
        return stage
