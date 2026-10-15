# Plateforme de gestion des stages PFA/PFE — EIGSI Casablanca

Version « réelle » de la plateforme, construite après le MVP de démonstration (`../mvp_SAADALI_WALID/`) en s'appuyant sur la conception des séances 1 et 2 (processus, besoins, base de données). **Auteur : Walid SAADALI**, dans le cadre du projet du cours *Système d'information et transformation digitale*.

## Ce que fait la plateforme
Elle suit chaque stage de la **déclaration jusqu'à la soutenance** et remplace les e-mails, les saisies à la main et les relances entre étudiants, encadrants, Service Stages (Career Center) et jury :

- l'**étudiant** déclare et soumet sa fiche de stage, suit son dossier (frise des étapes), dépose le scan de sa convention et voit ses livrables et sa soutenance ;
- l'**encadrant** (4e et 5e année) ou le **coordinateur** (1re à 3e année) valide ou refuse la fiche, avec un motif ;
- le **Career Center** affecte les encadrants, génère les conventions (PDF), vérifie les signatures, suit les livrables, importe les listes (WebAurion, Moodle) et organise les soutenances ;
- le **jury** indique ses disponibilités et saisit le PV et la note ;
- des **rappels et relances automatiques** par e-mail ; des **droits par rôle** ; la protection des données (loi 09-08).

23 user stories (17 *Must*, 3 *Should*, 3 *Could*) → [`docs/03-Besoins-et-backlog.md`](docs/03-Besoins-et-backlog.md).

## Essayer la démo (Windows, 5 minutes)
1. Installer **Python 3.10 ou plus** (<https://www.python.org/downloads/>, cocher *Add python.exe to PATH*).
2. Télécharger ce dépôt (*Code → Download ZIP*) ou le cloner, puis ouvrir le dossier `plateforme_SAADALI_WALID/app/`.
3. **Double-clic sur `LANCER_LA_DEMO.bat`**. Le premier lancement installe tout (2 à 5 minutes, Internet nécessaire) ; ensuite c'est instantané.
4. Le navigateur s'ouvre sur <http://localhost:8000/>. Comptes fictifs `…@example.test`, **mot de passe commun : `Demo-EIGSI-2026`**.

Les comptes, les situations de chaque étudiant et un déroulé de présentation sont dans [`docs/13-Demo-presentation.md`](docs/13-Demo-presentation.md). La démo utilise sa propre base (`demo.sqlite3`) : aucune vraie donnée.

## Technique
- **Django 5.2** (pages rendues par le serveur), SQLite en développement, PostgreSQL en ligne, PDF avec ReportLab, aucune bibliothèque externe côté navigateur.
- **275 tests automatiques** : `cd app` puis `.venv\Scripts\python manage.py test`.
- Documentation du code et des commandes : [`app/README.md`](app/README.md). Mise en ligne : [`docs/12-Mise-en-ligne.md`](docs/12-Mise-en-ligne.md).

## Organisation
```
plateforme_SAADALI_WALID/
├── app/    le code (Django) : applications comptes, stages, soutenances, espaces
└── docs/   la conception et les décisions (notes Obsidian)
```
Les comptes et entreprises de démonstration sont **fictifs**. Aucun mot de passe réel, aucune base de données ni fichier déposé n'est dans ce dépôt.
