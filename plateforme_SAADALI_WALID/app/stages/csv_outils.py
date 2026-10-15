"""
Outils pour lire et écrire des fichiers CSV (échanges avec WebAurion et Moodle).

Un CSV est un fichier tableur en texte : une ligne par enregistrement, des colonnes séparées par
un point-virgule (Excel en français) ou une virgule. Les fichiers qui viennent de l'extérieur
sont imprévisibles : encodage (UTF-8, avec ou sans BOM, ou Windows-1252), séparateur, titres de
colonnes avec accents ou majuscules. Ce module absorbe ces différences.
"""

import csv
import io
import re
import unicodedata

TAILLE_MAX_CSV = 2 * 1024 * 1024  # 2 Mo : largement assez pour une promotion entière


class ErreurCSV(ValueError):
    """Le fichier n'est pas un CSV exploitable (message lisible par l'utilisateur)."""


def normaliser(texte):
    """« Complément d'information », « E-mail », « Code.Groupe » -> « complement d information »,
    « e mail », « code groupe » : sans accents, en minuscules, ponctuation remplacée par des espaces."""
    texte = unicodedata.normalize("NFKD", str(texte or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", texte).strip()


def _decoder(contenu):
    for encodage in ("utf-8-sig", "cp1252"):
        try:
            return contenu.decode(encodage)
        except UnicodeDecodeError:
            continue
    raise ErreurCSV("Encodage du fichier non reconnu : exportez-le en « CSV UTF-8 ».")


def lire_csv(contenu):
    """Lit un CSV (octets). Renvoie (en-têtes normalisés, lignes).

    Chaque ligne est un couple (numéro de ligne dans le fichier, dictionnaire en-tête -> valeur).
    Les lignes entièrement vides sont ignorées."""
    if len(contenu) > TAILLE_MAX_CSV:
        raise ErreurCSV(f"Fichier trop gros (maximum {TAILLE_MAX_CSV // (1024 * 1024)} Mo).")
    texte = _decoder(contenu)
    premiere = texte.split("\n", 1)[0]
    separateur = max(";,\t", key=premiere.count)
    if premiere.count(separateur) == 0:
        raise ErreurCSV("Le fichier ne ressemble pas à un CSV (aucun séparateur dans la première ligne).")

    lecteur = csv.reader(io.StringIO(texte), delimiter=separateur)
    en_tetes = None
    lignes = []
    for ligne in lecteur:
        if not any(cellule.strip() for cellule in ligne):
            continue
        if en_tetes is None:
            en_tetes = [normaliser(c) for c in ligne]
            continue
        valeurs = {en_tetes[i]: ligne[i].strip() for i in range(min(len(en_tetes), len(ligne)))}
        lignes.append((lecteur.line_num, valeurs))
    if en_tetes is None:
        raise ErreurCSV("Le fichier est vide.")
    return en_tetes, lignes


def trouver_colonne(en_tetes, *, exacts=(), contient=()):
    """Nom (normalisé) de la première colonne qui correspond, ou None.
    `exacts` : titres acceptés tels quels ; `contient` : morceaux de titre (ex. « mail », « courriel »)."""
    for titre in en_tetes:
        if titre in exacts:
            return titre
    for titre in en_tetes:
        if any(morceau in titre for morceau in contient):
            return titre
    return None


def _sans_formule(valeur):
    """Excel exécute une cellule qui commence par = + - @ (« injection de formule »). Les textes
    saisis par les utilisateurs (sujet de stage…) sont donc précédés d'une apostrophe."""
    texte = "" if valeur is None else str(valeur)
    return "'" + texte if texte[:1] in ("=", "+", "-", "@", "\t", "\r") else texte


def ecrire_csv(colonnes, lignes):
    """Fabrique un CSV (octets) au format qu'Excel ouvre directement : UTF-8 avec BOM, séparateur
    « ; », fins de ligne Windows. `lignes` est une liste de listes de valeurs."""
    sortie = io.StringIO()
    ecrivain = csv.writer(sortie, delimiter=";", lineterminator="\r\n")
    ecrivain.writerow(colonnes)
    for ligne in lignes:
        ecrivain.writerow([_sans_formule(v) for v in ligne])
    return sortie.getvalue().encode("utf-8-sig")
