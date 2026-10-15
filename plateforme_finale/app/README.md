# app/ — application « Gestion des stages PFE/PFA »

Application **Django** (Python), en pages rendues par le serveur. Choix et raisons : `../docs/06-Architecture-et-stack.md`.

## Installer (une seule fois), dans PowerShell
```
cd C:\Users\wsaad\Documents\PROJETGestionStage\app
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py creer_comptes_demo
```
La dernière commande crée des comptes **fictifs** (`@example.test`) et affiche leurs mots de passe **une seule fois**. Relancez-la pour en obtenir de nouveaux.

## Lancer
```
.venv\Scripts\python manage.py runserver
```
Puis ouvrir http://127.0.0.1:8000 dans le navigateur. Arrêter avec `Ctrl+C`.
Si le terminal affiche « You have unapplied migration(s) » (après une mise à jour du code), lancer une fois :
```
.venv\Scripts\python manage.py migrate
```

## Tester automatiquement
```
.venv\Scripts\python manage.py test
```

## Organisation du code
| Dossier | Rôle |
|---|---|
| `config/` | réglages généraux (`settings.py`) et table des adresses (`urls.py`) |
| `comptes/` | utilisateurs (connexion par e-mail), rôles (`roles.py`), commande `creer_comptes_demo` |
| `espaces/` | accueil et une page par rôle, avec contrôle d'accès |
| `stages/` | promotions, affectations, fiches de stage, validation, historique (`models.py`, `services.py`, `views.py`) |
| `templates/` | pages HTML (gabarits) |

## Rôles
Étudiant, Encadrant, Coordinateur de promotion, Service Stages (Career Center), Jury. Ce sont des **groupes** Django : une personne peut en avoir plusieurs. Le Career Center gère les comptes, promotions et inscriptions dans `/admin/`.

## Parcours de démonstration (Lot 1)
Après `creer_comptes_demo` : Adam (3e année, validé par le coordinateur Karim), Yasmine (5e année, encadrée par Sara), Nadia (Career Center).
1. **Adam** : Mon stage → Déclarer → Soumettre.
2. **Karim** : Stages à valider → Examiner → Refuser avec un motif, puis Adam corrige et soumet de nouveau, puis Karim valide.
3. Même chose avec **Yasmine** et **Sara**.
4. **Nadia** : Affecter les encadrants (changer l'encadrant de Yasmine pour Omar).
Les e-mails s'affichent dans le terminal du serveur.

## Parcours de démonstration (Lot 2 : convention)
Une fois le stage d'Adam validé par Karim :
1. **Nadia** (Career Center) : Conventions → « Générer la convention » → télécharger le PDF → « Envoyer à l'étudiant » (le directeur des études a signé sur papier).
2. **Adam** : Mon stage → télécharger la convention, puis déposer un scan (PDF, JPG ou PNG, 10 Mo maximum).
3. **Nadia** : Conventions → voir le scan → « Valider : signée par tous » (ou refuser le scan avec un motif).
4. Dans `/admin/`, **Paramètres de l'école** : y saisir le nom du représentant et du directeur des études (repris dans le PDF).
## Livrables et rappels automatiques (Lot 3 bis)
**Les livrables (rapport, plan directeur…) sont rendus sur Moodle, pas sur cette plateforme.** Elle les suit et envoie les rappels que le Career Center faisait à la main.
- Quand la convention est signée, les livrables du stage sont créés avec leur date limite (valeurs de départ tirées du guide des expériences professionnelles : rapport au 15 septembre ; 4e et 5e année : plan directeur et évaluation des compétences en plus). Tout se règle dans `/admin/` → **Modèles de livrables** (dates, lien du devoir Moodle).
- **Nadia** (Career Center) : « Suivi des stages et livrables » → marquer un livrable **rendu** après vérification sur Moodle (les rappels s'arrêtent), prolonger une date, voir les retards.
- **Adam** : « Mon stage » → « Mes livrables » (dates, lien Moodle, statut).
- **Rappels** : la commande `envoyer_rappels` envoie un e-mail 7, 3 et 1 jour avant la date limite, puis 1 et 7 jours de retard (réglable dans `/admin/` → Paramètres de l'école). Un même rappel n'est jamais envoyé deux fois ; le Career Center reçoit un récapitulatif des retards.
```
.venv\Scripts\python manage.py envoyer_rappels
.venv\Scripts\python manage.py envoyer_rappels --date 2027-09-08   (pour simuler une date)
```
**À lancer une fois par jour, avec une seule commande : `taches_quotidiennes`** (elle lance `envoyer_rappels` puis `envoyer_relances` ; si l'une échoue, l'autre tourne quand même). Sur Windows : *Planificateur de tâches* → nouvelle tâche quotidienne → action « Démarrer un programme » : `C:\Users\wsaad\Documents\PROJETGestionStage\app\.venv\Scripts\python.exe`, arguments `manage.py taches_quotidiennes`, dossier de départ `C:\Users\wsaad\Documents\PROJETGestionStage\app`. En ligne : une tâche planifiée (cron) du serveur. Les e-mails n'arrivent dans de vraies boîtes qu'une fois le serveur d'e-mails réglé (mise en ligne).

## Relances automatiques et e-mails (Lot 5)
- **`envoyer_relances`** : relance les valideurs qui n'ont pas décidé une fiche soumise et les étudiants qui n'ont pas déposé le scan de leur convention (après 3 puis 7 jours, réglable dans `/admin/` → Paramètres de l'école). Une relance n'est jamais envoyée deux fois et s'arrête dès que l'action est faite. À lancer **chaque jour** : c'est déjà inclus dans `taches_quotidiennes` (voir ci-dessus), inutile de la planifier séparément.
```
.venv\Scripts\python manage.py envoyer_relances
.venv\Scripts\python manage.py envoyer_relances --date 2026-10-20   (pour simuler une date)
```
- **Vrais e-mails** : par défaut ils s'affichent dans le terminal. Pour les envoyer, définir ces variables d'environnement (jamais dans Git), puis tester avec `manage.py tester_email vous@exemple.ma` : `DJANGO_EMAIL_HOST` (active le mode SMTP), `DJANGO_EMAIL_PORT` (587 par défaut), `DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD`, `DJANGO_EMAIL_USE_TLS` (1 par défaut) ou `DJANGO_EMAIL_USE_SSL=1` (port 465), `DJANGO_DEFAULT_FROM_EMAIL`, et `DJANGO_SITE_URL` (adresse publique du site, pour les liens des e-mails).

Les fichiers de conventions sont rangés dans `app/uploads/` (jamais dans Git) et ne se téléchargent que par l'étudiant concerné et le Career Center.

## Pilotage et échanges (Lot 4)
Tout est dans l'espace **Service Stages** (Nadia). Des exemples fictifs sont dans `exemples/`.
- **Tableau de bord** : étudiants par étape et par année, fiches et conventions à traiter, retards (se recharge seul chaque minute).
- **Importer depuis WebAurion** : déposer un CSV (*Nom, Prénom, E-mail, Code.Groupe*, et *Rôle* facultatif). Cocher « simulation » d'abord pour voir le rapport sans rien enregistrer. Les mots de passe provisoires des comptes créés ne s'affichent **qu'une fois** : les noter. Essai : `exemples/webaurion_etudiants.csv`.
- **Importer les rendus depuis Moodle** : choisir le livrable, déposer l'export du devoir (colonnes *Adresse de courriel* et *Statut*) : les « Remis pour évaluation » passent « rendus ». Essai : `exemples/moodle_devoir_rapport.csv`.
- **Conventions** → « Exporter les conventions signées (CSV pour WebAurion) » et « Dossier complet (zip) » pour chaque convention signée.
Les formats de colonnes sont des hypothèses : `../docs/08-Decisions-ouvertes.md` #27.

## Soutenances (Lot 6)
- **Préparation** : le Career Center ajoute les salles dans `/admin/` → Salles (« Salle A » et « Salle B » existent en démo). Les membres du jury sont les comptes qui ont le rôle **Jury** (Sara et Omar en démo : un encadrant peut être jury).
- **Nadia** (Career Center) → « Soutenances » → créer une campagne (dates, durée, taille du jury : 2 par défaut, 3 au maximum) : les jurys sont prévenus par e-mail.
- **Sara et Omar** → « Mes soutenances et disponibilités » → cocher leurs créneaux.
- **Nadia** → « Proposer le planning » : seuls les stages de 5e année **validés avec convention signée** ont une soutenance ; un créneau n'est jamais placé avant la fin du stage. Elle peut corriger un créneau à la main, puis « Valider et envoyer les convocations ».
- **Jury** → « Saisir le PV » (note de 0 à 20, obligatoire) ; **Nadia** valide ou renvoie le PV (motif obligatoire), puis exporte les notes (CSV). L'étudiant voit sa soutenance dans « Mon stage ».
- La commande quotidienne `envoyer_relances` relance aussi les jurys qui n'ont pas répondu au sondage.

## Sauvegardes, mots de passe et protection des données (Lot 7)
- **Sauvegarder** : `.venv\Scripts\python manage.py sauvegarder` crée `sauvegardes/sauvegarde-AAAAMMJJ-HHMMSS.zip` (base + conventions et scans ; les 14 dernières sont gardées). **Restaurer** : `manage.py restaurer fichier.zip` (simulation), puis avec `--oui` (arrêter le site avant ; l'ancienne base est mise de côté). Copier le dossier `sauvegardes/` ailleurs régulièrement.
- **Mot de passe** : « Mon mot de passe » en haut de chaque page ; « Mot de passe oublié ? » sur la page de connexion (le lien arrive par e-mail ; en démo, il s'affiche dans le terminal du serveur).
- **Données personnelles** : page publique `/protection-des-donnees/` ; `manage.py donnees_personnelles adresse` (droit d'accès) ; `manage.py anonymiser_comptes` (comptes de plus de 10 ans ; simulation par défaut, `--oui` pour de bon).
- **Mise en ligne** : tout est décrit dans `../docs/12-Mise-en-ligne.md` (réglages, installation, nginx, tâches planifiées). Le site refuse de démarrer en ligne (`DJANGO_DEBUG=0`) sans clé secrète, hôtes autorisés et adresse `https://`.

## Sécurité
- Aucun secret dans Git : en ligne, définir `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` et `DJANGO_ALLOWED_HOSTS`.
- `db.sqlite3`, `.venv/` et `uploads/` ne vont jamais dans Git (voir `../.gitignore`).
