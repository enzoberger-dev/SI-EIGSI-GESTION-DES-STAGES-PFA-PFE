# Gestion des stages PFE/PFA — EIGSI Casablanca

Projet du cours **« Système d'information et transformation digitale »** (EIGSI Casablanca, septembre-octobre 2026) : une **plateforme web de gestion des stages PFA/PFE**, de la déclaration du stage jusqu'à la soutenance.

## Le problème
Aujourd'hui, le suivi des stages passe par des e-mails, des saisies manuelles et des relances à la main entre l'étudiant, l'encadrant, le Service Stages (Career Center), le tuteur en entreprise et le jury. Les informations se perdent, les délais sont dépassés, et personne ne voit clairement où en est chaque dossier.

## Notre réponse
Une plateforme où **chacun voit où en est le dossier et ce qu'il doit faire** :

- l'**étudiant** déclare son stage, suit son dossier étape par étape, dépose sa convention signée et voit ses livrables et sa soutenance ;
- l'**encadrant** ou le **coordinateur** valide ou refuse la fiche de stage (avec un motif) ;
- le **Career Center** affecte les encadrants, génère les conventions en PDF, suit les livrables et organise les soutenances ;
- le **jury** indique ses disponibilités et saisit le PV et la note ;
- des **rappels automatiques** par e-mail, des droits propres à chaque rôle, et le respect de la protection des données (loi 09-08).

## Essayer la version finale
La version finale se trouve dans [`plateforme_finale/`](plateforme_finale/) (Django, plus de 270 tests automatiques).
Sous Windows, avec Python 3.10 ou plus : ouvrir `plateforme_finale/app/` puis **double-clic sur `LANCER_LA_DEMO.bat`**. Le navigateur s'ouvre avec des comptes fictifs. Le détail est dans [`plateforme_finale/README.md`](plateforme_finale/README.md).

## Contenu du dépôt
| Élément | Contenu |
|---|---|
| `S1_Rapport_Gestion_des_stages_PFE_PFA.pdf` | Séance 1 — cadrage : SWOT, alignement stratégique, BPMN AS-IS, matrice MoSCoW, KPI SMART |
| `S2_Rapport_Gestion_des_stages_PFE_PFA.pdf`, `BPMN_TO-BE.pdf` | Séance 2 — conception : user stories, maquettes, modèle de données, architecture, BPMN TO-BE |
| `mvp_SAADALI_WALID/` | Séance 3 — MVP de démonstration (VS Code et GitHub Copilot, mode Auto) |
| `Demo/` | Vidéos de démonstration des MVP |
| `démo wajih.zip` | MVP de Wajih |
| [`plateforme_finale/`](plateforme_finale/) | Version finale de la plateforme : code, conception, démonstration |

## Équipe
SAADALI Walid · ADAWI Wael · BERGER Enzo · SAMIT Wajih
