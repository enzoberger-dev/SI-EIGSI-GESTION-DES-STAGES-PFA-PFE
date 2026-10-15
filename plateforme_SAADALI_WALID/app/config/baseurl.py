"""
Lecture de l'adresse de la base de données (variable d'environnement DATABASE_URL).

Exemples :
    postgres://utilisateur:mot_de_passe@serveur:5432/nom_de_la_base
    postgres://utilisateur:mot_de_passe@serveur/nom?sslmode=require
    sqlite:///C:/chemin/vers/db.sqlite3

Le mot de passe peut contenir des caractères spéciaux s'ils sont « encodés » (@ devient %40, / devient %2F…).
Sans DATABASE_URL, settings.py garde SQLite (le fichier db.sqlite3 du PC de développement).
"""

from urllib.parse import parse_qsl, unquote, urlsplit

MOTEURS = {
    "postgres": "django.db.backends.postgresql",
    "postgresql": "django.db.backends.postgresql",
    "sqlite": "django.db.backends.sqlite3",
}


def lire_url_base(url):
    """Transforme une adresse de base de données en réglage Django (DATABASES['default']).
    Lève ValueError avec un message clair si l'adresse est invalide."""
    adresse = urlsplit(url)
    moteur = MOTEURS.get(adresse.scheme)
    if moteur is None:
        raise ValueError(
            f"DATABASE_URL : type de base « {adresse.scheme} » non géré (attendu : postgres:// ou sqlite://)."
        )
    if adresse.scheme == "sqlite":
        # Règle habituelle : 3 barres = chemin relatif (sqlite:///db.sqlite3), 4 barres = chemin absolu
        # (sqlite:////var/db.sqlite3). Sous Windows, le disque suffit : sqlite:///C:/dossier/db.sqlite3
        chemin = unquote(adresse.path)[1:]
        if not chemin:
            raise ValueError("DATABASE_URL : chemin du fichier SQLite manquant.")
        return {"ENGINE": moteur, "NAME": chemin}

    nom = unquote(adresse.path.lstrip("/"))
    if not adresse.hostname or not nom:
        raise ValueError("DATABASE_URL : serveur ou nom de base manquant (attendu : postgres://utilisateur:mot_de_passe@serveur/nom).")
    reglage = {
        "ENGINE": moteur,
        "NAME": nom,
        "USER": unquote(adresse.username or ""),
        "PASSWORD": unquote(adresse.password or ""),
        "HOST": adresse.hostname,
        "PORT": str(adresse.port or ""),
        "CONN_MAX_AGE": 60,         # garde la connexion ouverte 60 s : plus rapide qu'une connexion par page
        "CONN_HEALTH_CHECKS": True,  # vérifie qu'elle fonctionne encore avant de la réutiliser
    }
    options = dict(parse_qsl(adresse.query))  # ex. sslmode=require
    if options:
        reglage["OPTIONS"] = options
    return reglage
