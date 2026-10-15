"""
Table des adresses du site : quelle adresse affiche quelle page.
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

from espaces import views as espaces_views
from stages import views as stages_views
from stages import views_pilotage as pilotage_views

urlpatterns = [
    # Career Center : affectation des encadrants (US-23)
    path("service-stages/affectations/", stages_views.affectations, name="affectations"),
    # Étudiant : déclarer et suivre son stage (US-01)
    path("etudiant/mon-stage/", stages_views.mon_stage, name="mon_stage"),
    path("etudiant/mon-stage/modifier/", stages_views.modifier_mon_stage, name="modifier_mon_stage"),
    # Convention (Lot 2) : Career Center, dépôt du scan par l'étudiant, téléchargement protégé
    path("service-stages/conventions/", stages_views.conventions, name="conventions"),
    path("service-stages/conventions/generer/<int:stage_pk>/", stages_views.convention_generer, name="convention_generer"),
    path("service-stages/conventions/<int:pk>/envoyer/", stages_views.convention_envoyer, name="convention_envoyer"),
    path("service-stages/conventions/<int:pk>/valider/", stages_views.convention_valider, name="convention_valider"),
    path("service-stages/conventions/<int:pk>/refuser-scan/", stages_views.convention_refuser_scan, name="convention_refuser_scan"),
    path("etudiant/convention/scan/", stages_views.deposer_scan_convention, name="deposer_scan_convention"),
    path("convention/<int:pk>/<str:quoi>/", stages_views.telecharger_convention, name="telecharger_convention"),
    # Suivi du stage (Lot 3) : livrables et rapport final
    path("service-stages/suivi/", stages_views.suivi, name="suivi"),
    path("service-stages/suivi/<int:pk>/rendu/", stages_views.livrable_rendu, name="livrable_rendu"),
    path("service-stages/suivi/<int:pk>/prolonger/", stages_views.livrable_prolonger, name="livrable_prolonger"),
    # Pilotage et échanges (Lot 4) : imports et exports CSV, tableau de bord
    path("service-stages/import-webaurion/", pilotage_views.import_webaurion, name="import_webaurion"),
    path("service-stages/tableau-de-bord/", pilotage_views.tableau, name="tableau_de_bord"),
    path("service-stages/import-moodle/", pilotage_views.import_moodle, name="import_moodle"),
    path("service-stages/dossier/<int:stage_pk>/", pilotage_views.dossier_stage, name="dossier_stage"),
    path("service-stages/export-conventions/", pilotage_views.export_conventions, name="export_conventions"),
    # Soutenances (Lot 6) : campagnes, planning, PV et notes, espace du jury
    path("", include("soutenances.urls")),
    # Encadrant ou coordinateur : valider ou refuser les fiches (US-02)
    path("validation/", stages_views.stages_a_valider, name="stages_a_valider"),
    path("validation/<int:pk>/", stages_views.decider, name="decider"),

    # Interface d'administration (Service Stages)
    path("admin/", admin.site.urls),

    # Connexion / déconnexion (écrans fournis par Django, gabarits dans templates/registration/)
    path("connexion/", auth_views.LoginView.as_view(), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),

    # Mot de passe : changer le sien (connecté) ou en demander un nouveau par e-mail (oublié). Les pages sont
    # fournies par Django, les gabarits sont dans templates/registration/. Le lien de l'e-mail utilise SITE_URL.
    path("mon-mot-de-passe/", auth_views.PasswordChangeView.as_view(success_url=reverse_lazy("password_change_done")),
         name="password_change"),
    path("mon-mot-de-passe/fait/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("mot-de-passe-oublie/",
         auth_views.PasswordResetView.as_view(extra_email_context={"site_url": settings.SITE_URL.rstrip("/")}),
         name="password_reset"),
    path("mot-de-passe-oublie/envoye/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reinitialisation/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path("reinitialisation/terminee/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Page publique d'information sur les données personnelles (loi 09-08)
    path("protection-des-donnees/", espaces_views.protection_donnees, name="protection_donnees"),
    path("aide/", espaces_views.aide, name="aide"),   # à propos et aide, selon le rôle (après connexion)

    # Accueil et espaces par rôle
    path("", espaces_views.accueil, name="accueil"),
]

# Une adresse par espace : /etudiant/, /encadrant/, /service-stages/, /jury/
for adresse in espaces_views.ESPACES:
    urlpatterns.append(
        path(f"{adresse}/", espaces_views.espace, {"adresse": adresse}, name=f"espace-{adresse}")
    )
