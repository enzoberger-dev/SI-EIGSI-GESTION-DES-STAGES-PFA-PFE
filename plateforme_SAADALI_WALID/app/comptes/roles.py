"""
Liste officielle des rôles de la plateforme.

Chaque rôle est un « groupe » Django du même nom. Une personne peut appartenir
à plusieurs groupes (par exemple un encadrant qui est aussi membre du jury).
Le directeur des études et les entreprises (liens uniques ou comptes : décision
#16 de docs/08-Decisions-ouvertes.md) seront ajoutés dans un lot suivant.
"""

ETUDIANT = "Étudiant"
ENCADRANT = "Encadrant"
SERVICE_STAGES = "Service Stages"
JURY = "Jury"
COORDINATEUR = "Coordinateur de promotion"  # valide les stages de 1re à 3e année (hypothèse)

# Tous les rôles, dans l'ordre d'affichage
TOUS_LES_ROLES = [ETUDIANT, ENCADRANT, COORDINATEUR, SERVICE_STAGES, JURY]
