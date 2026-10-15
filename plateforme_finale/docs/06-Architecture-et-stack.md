# 06 — Architecture et stack

Retour : [[Accueil]] · Schéma : `reference/arch.png` · Décision à prendre : [[08-Decisions-ouvertes]]

## Architecture logique (commune à toutes les pistes)
Application web à trois couches : **interface → API → base de données**, avec des services techniques appelés par l'API.
- Les rôles (Étudiant, Encadrant, Service Stages, Jury, Tuteur entreprise ; le directeur des études signe pour l'école) s'authentifient et ne voient que les écrans de leur couloir BPMN. *(2026-10-12 : le rôle Responsable est supprimé.)*
- ~~Les entreprises n'ont pas de compte : liens uniques par e-mail~~ *(2026-10-12 : les entreprises auront un compte, détails à préciser.)*
- **Objectif fixé le 2026-10-12** : une **vraie mise en ligne à l'école**. La stack est **libre** : on choisit la plus adaptée, pas forcément celle du schéma. Option ajoutée par Claude : **Django** (pages serveur), pour sa connexion, ses rôles et son interface d'administration déjà inclus. Choix reporté.
- Services : génération de PDF (convention) avec QR code, e-mails, relances automatiques planifiées, stockage des fichiers (rapports, livrables) côté serveur avec le chemin en base, import/export CSV pour WebAurion (pas d'API disponible).
- Signature simple : horodatage + empreinte SHA-256, **sans certificat qualifié** (à faire valider par l'école).

## ✅ Stack retenue le 2026-10-12 : Django (pages rendues par le serveur)
| Couche | Choix |
|---|---|
| Application | **Django** (Python) : pages HTML générées par le serveur (gabarits Django), pas de front séparé |
| Connexion, rôles | système d'utilisateurs, de groupes et de permissions de Django (une personne peut avoir plusieurs rôles) |
| Back-office Service Stages | interface d'administration de Django, complétée par des écrans dédiés |
| Base | SQLite sur le PC pour développer ; PostgreSQL proposé en ligne (à confirmer avec l'hébergement) |
| PDF (convention) | ReportLab |
| E-mails, relances | e-mails de Django (SMTP) + une commande planifiée lancée chaque jour (pas de Celery) |
| Import / export WebAurion | fichiers CSV |
| Qualité | tests automatiques dès la 1re fonctionnalité ; une seule personne responsable des modèles et des migrations |

Les sections ci-dessous gardent l'historique des options étudiées.

## Trois versions de la stack — attention aux contradictions
| | Rapport S2 (PDF rendu) | Schéma d'architecture actuel (tableau blanc du groupe) | Démo Copilot (jetable) |
|---|---|---|---|
| Interface | React + Vite + Tailwind | **Vue.js** (écrans par rôle, formulaires validés, tableau de bord, responsive) | pages HTML rendues par Express |
| API | Node.js + Express, JWT | **Python + Flask** (API REST) | Node.js + Express, sessions |
| Base | PostgreSQL | **MySQL** (12 tables) ; le tableau blanc disait « MySQL ou Oracle » | SQLite (19 tables) |
| PDF | PDFKit | ReportLab + QR code | PDFKit |
| E-mails / relances | Nodemailer + node-cron | Flask-Mail (SMTP) + APScheduler | — |
| Autres | Docker Compose | API Google (usage à préciser) ; **IA : API Gemini** (conformité du PDF + du formulaire) ; WebAurion en CSV | Multer pour l'envoi de PDF |
| Statut | **dépassé** : le texte du rapport n'a pas été mis à jour | **proposé**, en attente de validation du groupe et de Wael | démo seulement |

`reference/arch.png` montre la colonne centrale. `reference/gestion_stages.sql` est écrit pour MySQL.

## Trois pistes pour la vraie version (au choix de Walid)
1. **Pages rendues par le serveur** (ex. Flask + modèles Jinja, ou Express) — le plus simple pour un débutant : un seul projet, un seul langage, peu de pièces. Moins « moderne », interface moins dynamique.
2. **Front séparé + API** (Vue + Flask, c'est le schéma du tableau blanc) — séparation propre, bon pour montrer une architecture à trois couches ; plus de pièces à faire tenir ensemble.
3. **Refaire la démo en mieux** (même stack Node/Express/SQLite, en plus propre) — on garde ce qu'on connaît déjà ; mais ce n'est pas la stack proposée à l'école.

Walid a dit qu'il ne sait pas encore s'il veut « une application web » au sens large : à clarifier en premier. Claude peut proposer un comparatif plus détaillé sur demande.

## Points techniques à ne pas oublier quelle que soit la piste
- Mots de passe hachés, sessions ou jetons, contrôle des rôles sur **chaque** route.
- Accès aux fichiers privés (rapports, conventions) limité aux personnes concernées.
- Base de données et `uploads/` jamais dans Git.
- Cibles de qualité (KPI) : requêtes en moins de 10 s, rappels limités, maintenance peu coûteuse.
