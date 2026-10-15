"""
Sauvegarde et restauration (Lot 7).

Une sauvegarde est une archive ZIP datée qui contient la base de données ET les fichiers déposés
(conventions PDF, scans signés) : l'un sans l'autre ne permet pas de tout retrouver.
- SQLite (sur le PC) : copie cohérente du fichier, même si le site tourne ;
- PostgreSQL (en ligne) : « pg_dump » (l'outil doit être installé sur le serveur).

Une sauvegarde qui reste sur la même machine que le site ne protège pas d'une panne de cette machine :
en ligne, copier régulièrement le dossier des sauvegardes ailleurs (voir docs/12-Mise-en-ligne.md).
"""

import os
import shutil
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from contextlib import closing
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connection

MOTIF_SAUVEGARDE = "sauvegarde-*.zip"
BASE_SQLITE = "base.sqlite3"
BASE_POSTGRES = "base.dump"


class ErreurSauvegarde(Exception):
    """Message lisible par l'utilisateur : ce qui a échoué et quoi faire."""


def _exporter_base(dossier, delai):
    """Écrit une copie de la base dans `dossier` et renvoie son chemin. SQLite : abandonne après `delai`
    secondes si la base reste verrouillée (sans cela, la copie attendrait indéfiniment)."""
    if connection.vendor == "sqlite":
        connection.ensure_connection()
        cible = Path(dossier) / BASE_SQLITE
        copie = sqlite3.connect(cible)
        limite = time.monotonic() + delai

        def verifier_delai(etat, restant, total):
            if time.monotonic() > limite:
                raise ErreurSauvegarde(
                    f"La base est restée verrouillée plus de {delai} s : sauvegarde abandonnée. Réessayez dans un moment."
                )

        try:
            connection.connection.backup(copie, progress=verifier_delai)   # copie cohérente, même pendant que le site écrit
        finally:
            copie.close()
        return cible
    if connection.vendor == "postgresql":
        pg_dump = shutil.which("pg_dump")
        if pg_dump is None:
            raise ErreurSauvegarde(
                "L'outil « pg_dump » est introuvable : installez les outils clients PostgreSQL sur le serveur."
            )
        base = settings.DATABASES["default"]
        cible = Path(dossier) / BASE_POSTGRES
        commande = [pg_dump, "--format=custom", "--no-owner", "--file", str(cible),
                    "--host", base.get("HOST") or "localhost", "--username", base.get("USER") or "",
                    "--dbname", base["NAME"]]
        if base.get("PORT"):
            commande += ["--port", str(base["PORT"])]
        env = {**os.environ, "PGPASSWORD": base.get("PASSWORD") or ""}   # le mot de passe ne passe jamais en argument
        resultat = subprocess.run(commande, env=env, capture_output=True, text=True)
        if resultat.returncode != 0:
            raise ErreurSauvegarde("pg_dump a échoué : " + (resultat.stderr.strip().splitlines() or ["erreur inconnue"])[-1])
        return cible
    raise ErreurSauvegarde(f"Type de base non géré pour la sauvegarde : {connection.vendor}.")


def _fichiers_deposes():
    """Chemins (absolus, relatifs) de tous les fichiers de MEDIA_ROOT (conventions, scans)."""
    racine = Path(settings.MEDIA_ROOT)
    if not racine.is_dir():
        return []
    return [(f, f.relative_to(racine)) for f in sorted(racine.rglob("*")) if f.is_file()]


def sauvegarder(dossier=None, garder=14, maintenant=None, delai=120):
    """Crée une sauvegarde datée dans `dossier` (par défaut settings.BACKUP_DIR) et ne garde que les
    `garder` plus récentes. Renvoie le chemin de l'archive. Lève ErreurSauvegarde en cas de problème."""
    if garder < 1:
        raise ErreurSauvegarde("Il faut garder au moins 1 sauvegarde.")
    dossier = Path(dossier or settings.BACKUP_DIR)
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = (maintenant or datetime.now()).strftime("%Y%m%d-%H%M%S")
    cible = dossier / f"sauvegarde-{horodatage}.zip"
    compteur = 1
    while cible.exists():   # deux sauvegardes dans la même seconde : on ne remplace jamais une existante
        compteur += 1
        cible = dossier / f"sauvegarde-{horodatage}-{compteur}.zip"

    brouillon = cible.with_suffix(".zip.tmp")   # l'archive n'apparaît qu'une fois complète
    try:
        with tempfile.TemporaryDirectory() as tmp:
            base = _exporter_base(tmp, delai)
            with zipfile.ZipFile(brouillon, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.write(base, base.name)
                for fichier, relatif in _fichiers_deposes():
                    archive.write(fichier, "uploads/" + relatif.as_posix())
                archive.writestr(
                    "LISEZMOI.txt",
                    f"Sauvegarde du {horodatage}. Contenu : {base.name} (la base de données) et uploads/ "
                    f"(conventions et scans). Restauration : voir docs/12-Mise-en-ligne.md.\r\n",
                )
        brouillon.replace(cible)
    finally:
        brouillon.unlink(missing_ok=True)

    anciennes = sorted(dossier.glob(MOTIF_SAUVEGARDE))   # le nom contient la date : l'ordre alphabétique est chronologique
    for ancienne in anciennes[:-garder]:
        ancienne.unlink()
    return cible


def restaurer_sqlite(archive, chemin_base, dossier_uploads, dossier_securite):
    """Restaure une sauvegarde SQLite : remplace le fichier de base et remet les fichiers déposés.

    Avant d'écraser quoi que ce soit : l'archive et la base qu'elle contient sont vérifiées, et la base
    actuelle est copiée dans `dossier_securite` (« avant-restauration-… »). Les fichiers déposés sont
    ajoutés ou remplacés (ceux qui ne sont pas dans l'archive ne sont pas supprimés).
    Renvoie (chemin de la copie de sécurité ou None, nombre de fichiers remis)."""
    archive, chemin_base = Path(archive), Path(chemin_base)
    dossier_uploads, dossier_securite = Path(dossier_uploads), Path(dossier_securite)
    try:
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise ErreurSauvegarde("L'archive est abîmée : restauration annulée.")
            if BASE_SQLITE not in z.namelist():
                raise ErreurSauvegarde(f"« {BASE_SQLITE} » est absent de l'archive : ce n'est pas une sauvegarde SQLite.")
            with tempfile.TemporaryDirectory() as tmp:
                extraite = Path(tmp) / BASE_SQLITE
                extraite.write_bytes(z.read(BASE_SQLITE))
                try:
                    with closing(sqlite3.connect(extraite)) as verification:   # toujours fermée (Windows verrouille les fichiers ouverts)
                        resultat = verification.execute("PRAGMA integrity_check").fetchone()
                except sqlite3.DatabaseError:
                    resultat = None
                if not resultat or resultat[0] != "ok":
                    raise ErreurSauvegarde("La base contenue dans l'archive est abîmée : restauration annulée.")

                racine = dossier_uploads.resolve()
                a_ecrire = []
                for nom in z.namelist():
                    if not nom.startswith("uploads/") or nom.endswith("/"):
                        continue
                    destination = (racine / nom[len("uploads/"):]).resolve()
                    if racine not in destination.parents:   # « ../ » dans l'archive : jamais écrire en dehors
                        raise ErreurSauvegarde(f"Chemin dangereux dans l'archive ({nom}) : restauration annulée.")
                    a_ecrire.append((nom, destination))

                copie_securite = None
                if chemin_base.exists():
                    dossier_securite.mkdir(parents=True, exist_ok=True)
                    copie_securite = dossier_securite / f"avant-restauration-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
                    shutil.copy2(chemin_base, copie_securite)
                try:
                    shutil.copy2(extraite, chemin_base)
                except PermissionError:
                    raise ErreurSauvegarde("Impossible de remplacer la base : arrêtez le site avant de restaurer.")
                for nom, destination in a_ecrire:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(z.read(nom))
    except zipfile.BadZipFile:
        raise ErreurSauvegarde("Ce fichier n'est pas une archive ZIP valide.")
    return copie_securite, len(a_ecrire)
