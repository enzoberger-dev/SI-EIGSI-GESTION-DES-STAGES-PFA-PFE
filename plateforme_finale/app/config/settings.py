"""
Réglages généraux de l'application « Gestion des stages PFE/PFA ».

Les valeurs sensibles (clé secrète, mode debug, adresses autorisées) sont lues
dans des variables d'environnement. Les valeurs par défaut ci-dessous ne
conviennent QUE pour développer sur son PC.
"""

import os
import sys
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .baseurl import lire_url_base

# Dossier app/ (là où se trouve manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent


# --- Sécurité ---------------------------------------------------------------
# Clé secrète : sert à signer les sessions et les jetons. En ligne, elle DOIT
# être fournie par la variable d'environnement DJANGO_SECRET_KEY.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-uniquement-cle-non-securisee-ne-pas-utiliser-en-ligne",
)

# Mode debug : affiche les erreurs détaillées. Activé par défaut sur le PC,
# à désactiver en ligne (DJANGO_DEBUG=0).
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# Adresses (noms de domaine) autorisées à servir le site, séparées par des virgules.
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# --- Applications -----------------------------------------------------------
INSTALLED_APPS = [
    # Briques fournies par Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Nos applications
    "comptes",   # utilisateurs (connexion par e-mail) et rôles
    "espaces",   # pages d'accueil de chaque rôle
    "stages",    # promotions, affectations, fiches de stage, historique
    "soutenances",  # campagnes de soutenances, planning, PV et notes (Lot 6)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Pas de LocaleMiddleware : la plateforme est uniquement en français. Avec lui, l'administration changeait
    # de langue selon le navigateur (anglais pour un navigateur en anglais). LANGUAGE_CODE suffit.
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # protection des formulaires
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not DEBUG:
    # En ligne, WhiteNoise sert les fichiers statiques (CSS de l'administration). Sur le PC, c'est « runserver ».
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Dossier commun des gabarits (pages HTML) : app/templates/
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "espaces.navigation.menu",  # menu latéral selon les rôles (lot 8)
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Base de données --------------------------------------------------------
# Sur le PC : SQLite (le fichier db.sqlite3 n'est jamais mis dans Git). En ligne : PostgreSQL, en
# définissant DATABASE_URL (voir config/baseurl.py), par exemple
#   postgres://utilisateur:mot_de_passe@serveur:5432/gestion_stages
DATABASES = {
    "default": lire_url_base(os.environ["DATABASE_URL"]) if os.environ.get("DATABASE_URL") else {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --- Utilisateurs et connexion ---------------------------------------------
# Notre propre modèle d'utilisateur (connexion par e-mail), défini dans comptes/models.py.
AUTH_USER_MODEL = "comptes.Utilisateur"

# Où aller pour se connecter, et après connexion / déconnexion
LOGIN_URL = "connexion"
LOGIN_REDIRECT_URL = "accueil"
LOGOUT_REDIRECT_URL = "connexion"

# Règles de mot de passe (longueur, mots trop courants, etc.)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Pendant les tests seulement : chiffrement rapide des mots de passe (les tests passent
# de 70 à quelques secondes). Jamais utilisé en vrai : le chiffrement normal reste actif.
if len(sys.argv) > 1 and sys.argv[1] == "test":
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


# --- Langue et heure --------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True


# --- E-mails -----------------------------------------------------------------
# Par défaut (sur le PC), les e-mails ne partent pas : ils s'affichent dans le terminal du serveur.
# Pour un vrai envoi, il suffit de définir DJANGO_EMAIL_HOST (le serveur SMTP fourni par l'école) :
# le mode SMTP s'active alors tout seul. Aucun identifiant n'est écrit ici : ils viennent de variables
# d'environnement (voir app/README.md). Vérification : python manage.py tester_email adresse
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND") or (
    "django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "1") == "1"    # port 587 (STARTTLS)
EMAIL_USE_SSL = os.environ.get("DJANGO_EMAIL_USE_SSL", "0") == "1"    # port 465, à la place de TLS
if EMAIL_USE_SSL:
    EMAIL_USE_TLS = False
EMAIL_TIMEOUT = 15  # secondes : un serveur muet ne bloque pas la plateforme
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "stages@example.test")

# Adresse du site, pour les liens placés dans les e-mails (relances). En ligne : l'adresse publique.
SITE_URL = os.environ.get("DJANGO_SITE_URL", "http://127.0.0.1:8000")


# --- Fichiers statiques (CSS, images) --------------------------------------
STATIC_URL = "static/"
# Nos propres fichiers de style, script et images (logo) : app/static/
STATICFILES_DIRS = [BASE_DIR / "static"]
# En ligne : « manage.py collectstatic » les rassemble dans staticfiles/ (jamais dans Git), WhiteNoise les sert.
STATIC_ROOT = BASE_DIR / "staticfiles"
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# --- Sauvegardes (commande « manage.py sauvegarder ») -----------------------
# Dossier des archives ZIP (base de données + fichiers déposés). Jamais dans Git. En ligne : un dossier
# sur un autre disque ou une copie régulière vers un autre serveur, sinon la sauvegarde ne protège de rien.
BACKUP_DIR = Path(os.environ.get("DJANGO_BACKUP_DIR") or BASE_DIR / "sauvegardes")

# --- Fichiers déposés ou générés (conventions, scans) ----------------------
# Rangés dans app/uploads/, JAMAIS servis directement : il n'y a volontairement
# pas de MEDIA_URL. Chaque téléchargement passe par une vue qui vérifie les droits.
MEDIA_ROOT = Path(os.environ["DJANGO_MEDIA_ROOT"]) if os.environ.get("DJANGO_MEDIA_ROOT") else BASE_DIR / "uploads"
if "test" in sys.argv:
    # Les tests ne doivent pas déposer leurs PDF dans le vrai dossier uploads/ (il s'y accumulait un fichier par test).
    MEDIA_ROOT = Path(tempfile.gettempdir()) / "stages-tests-uploads"
# Taille maximale d'un scan déposé (en octets) : 10 Mo
TAILLE_MAX_SCAN = 10 * 1024 * 1024

# Type des identifiants automatiques des tables
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Mots de passe oubliés ---------------------------------------------------
# Le lien envoyé par e-mail (« Mot de passe oublié ») reste valable 24 heures.
PASSWORD_RESET_TIMEOUT = 24 * 3600


# --- Mise en ligne (DJANGO_DEBUG=0) -------------------------------------------
# Ces règles ne s'appliquent QU'EN LIGNE. Le site refuse de démarrer si un réglage indispensable manque :
# mieux vaut une erreur claire qu'un site en ligne avec une clé secrète publique. Le guide complet est
# dans docs/12-Mise-en-ligne.md.
if not DEBUG:
    if SECRET_KEY.startswith("dev-uniquement") or len(SECRET_KEY) < 50:
        raise ImproperlyConfigured(
            "En ligne (DJANGO_DEBUG=0), DJANGO_SECRET_KEY doit être une vraie clé secrète d'au moins 50 "
            "caractères. Pour en fabriquer une : python -c \"from django.core.management.utils import "
            "get_random_secret_key as g; print(g())\""
        )
    if "DJANGO_ALLOWED_HOSTS" not in os.environ:
        raise ImproperlyConfigured("En ligne (DJANGO_DEBUG=0), DJANGO_ALLOWED_HOSTS est obligatoire (ex. stages.ecole.ma).")
    if not SITE_URL.startswith("https://"):
        raise ImproperlyConfigured("En ligne (DJANGO_DEBUG=0), DJANGO_SITE_URL est obligatoire et doit commencer par https://")

    # HTTPS obligatoire : redirection automatique, cookies de session et de formulaire jamais envoyés en clair
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SSL_REDIRECT", "1") == "1"   # 0 si le serveur web frontal s'en charge
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_AGE = 12 * 3600   # une session dure 12 heures au plus
    # Demande aux navigateurs de n'utiliser que HTTPS pour ce site. Durée prudente au début (1 heure) :
    # à augmenter (31536000 = 1 an) une fois que tout fonctionne en HTTPS.
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_REFERRER_POLICY = "same-origin"
    # Derrière un serveur web frontal (nginx, Apache) qui gère le HTTPS : il doit transmettre l'en-tête
    # X-Forwarded-Proto. À activer seulement dans ce cas (DJANGO_BEHIND_PROXY=1).
    if os.environ.get("DJANGO_BEHIND_PROXY") == "1":
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = [SITE_URL.rstrip("/")] + [
        o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
    ]
    # Le « preload » (inscription du site dans la liste des navigateurs) est un engagement long : non demandé.
    SILENCED_SYSTEM_CHECKS = ["security.W021"]

    # Les erreurs du site sont écrites dans la sortie d'erreur du serveur (lue par gunicorn / systemd / Docker)
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s : %(message)s"}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
        "root": {"handlers": ["console"], "level": "WARNING"},
    }
