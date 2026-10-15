"""
Formulaires des soutenances (Lot 6).
"""

import re

from django import forms

from .models import Campagne


class CampagneForm(forms.ModelForm):
    """Création d'une campagne de soutenances par le Career Center."""

    class Meta:
        model = Campagne
        fields = ["nom", "annee_universitaire", "annees_concernees", "date_debut", "date_fin", "duree_minutes",
                  "heure_debut", "heure_fin", "pause_debut", "pause_fin", "taille_jury"]
        widgets = {
            "date_debut": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "date_fin": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "heure_debut": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "heure_fin": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "pause_debut": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "pause_fin": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def clean_annee_universitaire(self):
        annee = self.cleaned_data["annee_universitaire"].strip()
        if not re.fullmatch(r"\d{4}-\d{4}", annee) or int(annee[5:]) != int(annee[:4]) + 1:
            raise forms.ValidationError("Format attendu : 2026-2027.")
        return annee

    def clean_annees_concernees(self):
        valeur = self.cleaned_data["annees_concernees"]
        annees = [x for x in valeur.replace(" ", "").split(",") if x]
        if not annees or any(a not in {"1", "2", "3", "4", "5"} for a in annees):
            raise forms.ValidationError("Indiquez des années d'études de 1 à 5, séparées par des virgules. Ex. : 5 ou 4,5")
        return ",".join(annees)

    def clean_duree_minutes(self):
        duree = self.cleaned_data["duree_minutes"]
        if not 15 <= duree <= 240:
            raise forms.ValidationError("La durée doit être comprise entre 15 et 240 minutes.")
        return duree

    def clean_taille_jury(self):
        taille = self.cleaned_data["taille_jury"]
        if not 1 <= taille <= 3:
            raise forms.ValidationError("Un jury compte 2 membres en général, 3 au maximum.")
        return taille

    def clean(self):
        donnees = super().clean()
        debut, fin = donnees.get("date_debut"), donnees.get("date_fin")
        if debut and fin and fin < debut:
            self.add_error("date_fin", "Le dernier jour doit être après le premier.")
        h_debut, h_fin = donnees.get("heure_debut"), donnees.get("heure_fin")
        if h_debut and h_fin and h_fin <= h_debut:
            self.add_error("heure_fin", "La fin de journée doit être après le début.")
        p_debut, p_fin = donnees.get("pause_debut"), donnees.get("pause_fin")
        if p_debut and p_fin and p_fin <= p_debut:
            self.add_error("pause_fin", "La fin de pause doit être après son début.")
        if not self.errors and not Campagne(**donnees).creneaux():
            raise forms.ValidationError("Ces réglages ne donnent aucun créneau (vérifiez les dates et les heures).")
        return donnees
