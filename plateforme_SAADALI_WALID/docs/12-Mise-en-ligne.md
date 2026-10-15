# 12 — Mise en ligne (guide pour le service informatique)

Retour : [[Accueil]] · Données personnelles : [[11-Protection-des-donnees]] · Décisions : [[08-Decisions-ouvertes]]

> **Où en est-on ?** Le code est prêt pour être installé sur un serveur (Lot 7). **Rien n'est installé en ligne** : il faut un serveur, un nom de domaine, un certificat HTTPS, une base PostgreSQL et un serveur d'e-mails, que seule l'école peut fournir ([[08-Decisions-ouvertes]] #20 et #31). Ce guide n'a **pas été testé sur un vrai serveur** : les réglages de sécurité, la base PostgreSQL et le service des fichiers ont été vérifiés par des tests, mais pas l'installation complète. Prévoir une première mise en route accompagnée.

## 1. Ce que l'école doit fournir
| Besoin | Détail |
|---|---|
| Un serveur Linux | Ubuntu 22.04 ou plus récent (ou équivalent), 2 Go de mémoire suffisent pour une école |
| Python | 3.11 ou plus récent |
| PostgreSQL | version 14 ou plus récente, une base et un utilisateur dédiés |
| Nom de domaine + certificat HTTPS | ex. `stages.ecole.ma` (certificat de l'école ou Let's Encrypt) |
| Serveur d'e-mails (SMTP) | adresse du serveur, port, identifiant et mot de passe d'un compte d'envoi |
| Stockage de sauvegardes | **un autre disque ou une autre machine** que le serveur du site |
| Un serveur web frontal | nginx (exemple ci-dessous) ou Apache, qui gère le HTTPS |

## 2. Réglages (variables d'environnement)
Aucun secret n'est écrit dans le code. Ils sont fournis par l'environnement du serveur (fichier lisible seulement par le compte du site).

| Variable | Obligatoire en ligne | Rôle |
|---|---|---|
| `DJANGO_DEBUG` | oui, valeur `0` | passe en mode « en ligne » (sécurité renforcée) |
| `DJANGO_SECRET_KEY` | oui | clé secrète, 50 caractères au moins (le site refuse de démarrer sinon). Fabriquer : `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"` |
| `DJANGO_ALLOWED_HOSTS` | oui | nom de domaine du site, ex. `stages.ecole.ma` |
| `DJANGO_SITE_URL` | oui | adresse publique en `https://`, ex. `https://stages.ecole.ma` (liens des e-mails) |
| `DATABASE_URL` | oui | `postgres://utilisateur:mot_de_passe@serveur:5432/gestion_stages` (caractères spéciaux du mot de passe « encodés » : `@` → `%40`) |
| `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`, `DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD` | oui | serveur SMTP (le mode SMTP s'active dès que `DJANGO_EMAIL_HOST` est défini). `DJANGO_EMAIL_USE_TLS=1` (défaut) ou `DJANGO_EMAIL_USE_SSL=1` pour le port 465 |
| `DJANGO_DEFAULT_FROM_EMAIL` | oui | expéditeur des e-mails, ex. `stages@ecole.ma` |
| `DJANGO_BEHIND_PROXY` | si nginx/Apache | `1` : fait confiance à l'en-tête `X-Forwarded-Proto` envoyé par le serveur web frontal |
| `DJANGO_HSTS_SECONDS` | non | durée HSTS, 3600 (1 h) par défaut. **Augmenter à 31536000 (1 an) quand tout fonctionne en HTTPS** |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | non | autres adresses de confiance, séparées par des virgules |
| `DJANGO_SSL_REDIRECT` | non | `0` seulement si le serveur web frontal fait déjà la redirection HTTP → HTTPS |
| `DJANGO_BACKUP_DIR` | conseillé | dossier des sauvegardes (hors du dossier du site, idéalement un autre disque) |

## 3. Installation (Linux)
```bash
# 1. Récupérer le code dans /srv/stages (le dossier app/ contient manage.py), créer l'environnement Python
cd /srv/stages/app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Réglages : placer les variables du §2 dans /etc/stages.env (droits 600, propriétaire = compte du site)
set -a; . /etc/stages.env; set +a

# 3. Vérifier la configuration : doit répondre « no issues » (1 vérification volontairement ignorée : le « preload » HSTS)
.venv/bin/python manage.py check --deploy

# 4. Créer les tables, rassembler les fichiers statiques
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput

# 5. Premier compte (Career Center) : créer un superutilisateur, puis dans /admin/ lui donner le groupe « Service Stages »
.venv/bin/python manage.py createsuperuser

# 6. Tester l'envoi d'e-mails
.venv/bin/python manage.py tester_email votre.adresse@ecole.ma
```
⚠️ **Ne jamais lancer `creer_comptes_demo` en ligne** : cette commande crée des comptes de démonstration et réinitialise leurs mots de passe.

### Lancer le site (gunicorn, géré par systemd)
Fichier `/etc/systemd/system/stages.service` :
```ini
[Unit]
Description=Plateforme de gestion des stages
After=network.target postgresql.service

[Service]
User=stages
WorkingDirectory=/srv/stages/app
EnvironmentFile=/etc/stages.env
ExecStart=/srv/stages/app/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 60
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
Puis : `systemctl enable --now stages`. (`gunicorn` ne fonctionne pas sous Windows : il est installé seulement sur Linux.)

### Serveur web frontal (exemple nginx)
```nginx
server {
    listen 80;
    server_name stages.ecole.ma;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name stages.ecole.ma;
    ssl_certificate     /chemin/vers/certificat.pem;
    ssl_certificate_key /chemin/vers/cle.pem;
    client_max_body_size 12m;            # les scans de convention vont jusqu'à 10 Mo
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
    # IMPORTANT : ne JAMAIS publier le dossier uploads/ (conventions, scans) : le site les sert lui-même,
    # après avoir vérifié les droits de chaque personne.
}
```
Avec cette configuration, définir `DJANGO_BEHIND_PROXY=1`.

## 4. Tâches planifiées (cron)
À lancer avec les variables d'environnement du §2, dans `/srv/stages/app` :
```cron
# tous les jours à 7 h : rappels de livrables et relances (valideurs, étudiants, jurys)
0 7 * * *  cd /srv/stages/app && set -a && . /etc/stages.env && .venv/bin/python manage.py envoyer_rappels && .venv/bin/python manage.py envoyer_relances
# tous les jours à 2 h : sauvegarde (14 dernières conservées)
0 2 * * *  cd /srv/stages/app && set -a && . /etc/stages.env && .venv/bin/python manage.py sauvegarder
```
Et **copier le dossier des sauvegardes sur une autre machine** (rsync, partage réseau, outil de sauvegarde de l'école) : une sauvegarde qui reste sur le serveur ne protège pas d'une panne du serveur.
Une fois par an, avant la rentrée : `manage.py sauvegarder` puis `manage.py anonymiser_comptes` (affiche la liste ; ajouter `--oui` pour anonymiser, voir [[11-Protection-des-donnees]]).

## 5. Sauvegarde et restauration
- **Sauvegarder** : `manage.py sauvegarder` crée `sauvegarde-AAAAMMJJ-HHMMSS.zip` (base `base.dump` + dossier `uploads/`). Elle utilise `pg_dump` : les outils clients PostgreSQL doivent être installés sur le serveur.
- **Restaurer (PostgreSQL)** : arrêter le site (`systemctl stop stages`), décompresser l'archive, puis :
  ```bash
  pg_restore --clean --no-owner --dbname "$DATABASE_URL" base.dump
  cp -r uploads/. /srv/stages/app/uploads/
  systemctl start stages
  ```
- **Restaurer (SQLite, PC de développement)** : `manage.py restaurer archive.zip` (simulation), puis `--oui` pour de bon : l'ancienne base est mise de côté avant d'être remplacée.
- **Faire un essai de restauration** sur une base vide au moins une fois, avant d'en avoir besoin.

## 6. Mettre à jour le site
```bash
cd /srv/stages && git pull          # nouveau code
cd app && .venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py sauvegarder     # filet de sécurité
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
systemctl restart stages
```

## 7. Ce qui n'est pas fait (à savoir)
- **Pas de limitation des tentatives de connexion** (un mot de passe peut être deviné par essais répétés) : à ajouter si le service informatique ne le fait pas en amont (par exemple `django-axes` ou une règle du pare-feu).
- **Pas de double authentification** ni de connexion unique (SSO) : à voir avec l'école.
- **Mots de passe provisoires** : un compte importé garde son mot de passe provisoire tant que la personne ne le change pas elle-même (« Mon mot de passe »). Aucun changement obligatoire à la première connexion.
- **Pas de surveillance** (disponibilité, espace disque) ni de journal d'audit des consultations.
- **Docker** : non fourni (choix de Walid : sans Docker pour l'instant). À ajouter si l'école l'exige.
- **Installation non testée sur un vrai serveur** (voir le début de cette note).
