"""
Adresses des soutenances (incluses dans config/urls.py).
"""

from django.urls import path

from . import views

urlpatterns = [
    # Career Center
    path("service-stages/soutenances/", views.liste, name="soutenances"),
    path("service-stages/soutenances/export-notes/", views.export_notes, name="export_notes"),
    path("service-stages/soutenances/<int:pk>/", views.campagne, name="soutenances_campagne"),
    path("service-stages/soutenances/<int:pk>/proposer/", views.proposer, name="soutenances_proposer"),
    path("service-stages/soutenances/<int:pk>/valider/", views.valider, name="soutenances_valider"),
    path("service-stages/soutenance/<int:pk>/deplacer/", views.deplacer, name="soutenance_deplacer"),
    path("service-stages/soutenance/<int:pk>/pv-valider/", views.pv_valider, name="soutenance_pv_valider"),
    path("service-stages/soutenance/<int:pk>/pv-refuser/", views.pv_refuser, name="soutenance_pv_refuser"),
    # Jury
    path("jury/soutenances/", views.jury_accueil, name="jury_accueil"),
    path("jury/disponibilites/<int:pk>/", views.jury_disponibilites, name="jury_disponibilites"),
    path("jury/soutenance/<int:pk>/pv/", views.jury_pv, name="jury_pv"),
]
