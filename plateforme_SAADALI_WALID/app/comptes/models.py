"""
Utilisateurs de la plateforme.

On remplace l'utilisateur standard de Django pour se connecter avec son
e-mail (pas d'identifiant). Les rôles ne sont PAS une colonne : ce sont des
« groupes » Django (voir roles.py), ce qui permet à une même personne d'avoir
plusieurs rôles (par exemple Encadrant et Jury).
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UtilisateurManager(BaseUserManager):
    """Sait créer des utilisateurs à partir d'un e-mail (au lieu d'un identifiant)."""

    use_in_migrations = True

    def _creer(self, email, password, **champs):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        utilisateur = self.model(email=email, **champs)
        utilisateur.set_password(password)  # le mot de passe est chiffré, jamais stocké en clair
        utilisateur.save(using=self._db)
        return utilisateur

    def create_user(self, email, password=None, **champs):
        champs.setdefault("is_staff", False)
        champs.setdefault("is_superuser", False)
        return self._creer(email, password, **champs)

    def create_superuser(self, email, password=None, **champs):
        champs.setdefault("is_staff", True)
        champs.setdefault("is_superuser", True)
        return self._creer(email, password, **champs)


class Utilisateur(AbstractUser):
    """Une personne qui se connecte : étudiant, encadrant, agent du Service Stages, jury."""

    username = None  # pas d'identifiant : on se connecte avec l'e-mail
    email = models.EmailField("adresse e-mail", unique=True)

    USERNAME_FIELD = "email"   # champ utilisé pour se connecter
    REQUIRED_FIELDS = []       # champs demandés en plus lors de createsuperuser

    objects = UtilisateurManager()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        nom = self.get_full_name()
        return f"{nom} <{self.email}>" if nom else self.email

    def a_le_role(self, role):
        """Vrai si la personne appartient au groupe de ce rôle (voir roles.py)."""
        return self.groups.filter(name=role).exists()

    def roles(self):
        """Liste des noms de rôles de la personne, par ordre alphabétique."""
        return list(self.groups.order_by("name").values_list("name", flat=True))
