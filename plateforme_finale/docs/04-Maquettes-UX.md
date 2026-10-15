# 04 — Maquettes UX

Retour : [[Accueil]] · Besoins : [[03-Besoins-et-backlog]]

Le rapport S2 contient **six maquettes basse fidélité** (structure et parcours, pas de charte graphique), une par rôle du BPMN TO-BE. Les images sont dans le PDF du rapport S2 ; il n'existe pas de fichiers séparés (Figma, Excalidraw…). Les valeurs affichées sont des exemples.

| Écran | Rôle | User stories | Schéma TO-BE |
|---|---|---|---|
| E1 · Déclarer mon stage | Étudiant | US-01 | 1 |
| E2 · Vérifier la conformité du stage | Encadrant | US-02 | 1 |
| E3 · Suivre mon stage | Étudiant | US-03, US-09, US-17 | 1 à 3 |
| E4 · Valider une convention *(obsolète, à refaire : émission par le Service Stages)* | ~~Encadrant, Service Stages, Responsable~~ Service Stages | US-04 | 2 |
| E5 · Planifier les soutenances | Service Stages | US-13, US-14 | 4 |
| E6 · Piloter les stages (tableau de bord) | ~~Responsable~~ Service Stages | US-11 | 3 |

> 2026-10-12 : le rôle Responsable n'existe pas (voir [[02-Processus-BPMN]]). Écrans à ajouter : affectation des encadrants (US-23), espace entreprise / tuteur (avec compte), connexion.

**Non maquettés** : l'espace Jury (sondage de disponibilités, saisie du PV : US-12, US-15) et le module d'offres partenaires (US-20 à US-22).

## Principes d'interface à respecter
- Chaque rôle ne voit que ses écrans (les couloirs du BPMN).
- Un champ obligatoire vide bloque l'envoi ; un refus exige un motif.
- L'historique des décisions est toujours visible (validations, dépôts de rapport).
- Interface responsive et simple, en français.

## À faire pour la vraie version
- Redessiner ou affiner les écrans dans l'outil de son choix avant de coder (la démo Copilot a ses propres écrans, plus nombreux : voir [[07-MVP-demo-Copilot]]).
- Maquetter l'espace Jury et, si le module est retenu, les offres.
