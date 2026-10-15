"""
Assistant IA de la plateforme (lot 9) : répond aux questions sur l'utilisation du site et relit les sujets de stage.

Principes (voir docs/15-IA.md) :
- L'IA PROPOSE, l'humain DÉCIDE : l'assistant ne valide ni ne refuse rien et n'enregistre rien.
- Aucune donnée personnelle ne part chez le fournisseur : les e-mails, numéros de téléphone et longs nombres sont
  effacés avant l'envoi, et le texte est limité en longueur. Le contenu des questions n'est JAMAIS journalisé.
- Le service marche sans IA : sans clé, sans Internet, ou en cas d'erreur / de quota dépassé, on répond avec les
  textes de la page d'aide (« mode démonstration ») et la réponse l'indique clairement.
- La clé d'API n'est jamais dans le code ni dans Git : variable d'environnement GEMINI_API_KEY, ou fichier
  cle_gemini.txt (une ligne) à la racine de app/, ignoré par Git.
- Aucune bibliothèque en plus : l'appel passe par urllib (bibliothèque standard de Python).
"""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

from comptes import roles

from .aide import AIDE, INTRODUCTION

# « -latest » : alias qui suit le modèle Lite actuel (Google retire régulièrement les anciens modèles : « gemini-2.5-* »
# n'est déjà plus proposé aux nouveaux comptes). On peut en imposer un autre avec la variable IA_MODELE.
MODELE_PAR_DEFAUT = "gemini-flash-lite-latest"
ADRESSE_API = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
LONGUEUR_MAX = 600          # caractères envoyés au modèle, au maximum
QUESTIONS_PAR_HEURE = 30    # plafond par personne (évite d'épuiser le quota gratuit)
DELAI_SECONDES = 15


class IAIndisponible(Exception):
    """Pas de clé, pas d'Internet, quota dépassé ou erreur du service : on passe en mode de secours."""


# ---------------------------------------------------------------- clé et réglages

def lire_cle():
    """Clé d'API : variable d'environnement, sinon fichier cle_gemini.txt (« clé » ou « NOM=clé »). None si absente."""
    cle = os.environ.get("GEMINI_API_KEY") or os.environ.get("IA_CLE_API")
    if not cle:
        fichier = Path(settings.BASE_DIR) / "cle_gemini.txt"
        try:
            cle = fichier.read_text(encoding="utf-8-sig").strip()
        except OSError:
            return None
    if "=" in cle:
        cle = cle.split("=", 1)[1]
    cle = cle.strip().strip("\"'")
    return cle or None


def modele():
    return os.environ.get("IA_MODELE") or MODELE_PAR_DEFAUT


# ---------------------------------------------------------------- protection des données

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_TELEPHONE = re.compile(r"(?:\+|00)?\d[\d .-]{7,}\d")
_LONG_NOMBRE = re.compile(r"\d{6,}")


def anonymiser(texte):
    """Efface e-mails, téléphones et longs nombres, et limite la longueur : seul ce texte part chez le fournisseur."""
    texte = (texte or "").strip()
    texte = _EMAIL.sub("[e-mail effacé]", texte)
    texte = _TELEPHONE.sub("[numéro effacé]", texte)
    texte = _LONG_NOMBRE.sub("[nombre effacé]", texte)
    return texte[:LONGUEUR_MAX]


# ---------------------------------------------------------------- limite par personne

def verifier_plafond(utilisateur):
    """Compte la question dans l'heure en cours. Renvoie False si la personne a dépassé son plafond."""
    cle = f"assistant-ia-{utilisateur.pk}"
    n = cache.get(cle, 0)
    if n >= QUESTIONS_PAR_HEURE:
        return False
    cache.set(cle, n + 1, timeout=3600)
    return True


# ---------------------------------------------------------------- appel au modèle

def appeler_gemini(consigne, question):
    """Envoie une consigne et une question à Gemini. Renvoie le texte de la réponse, ou lève IAIndisponible."""
    cle = lire_cle()
    if not cle:
        raise IAIndisponible("pas de clé")
    corps = {
        "systemInstruction": {"parts": [{"text": consigne}]},
        "contents": [{"role": "user", "parts": [{"text": question}]}],
        "generationConfig": {"maxOutputTokens": 500, "temperature": 0.3},
    }
    requete = urllib.request.Request(
        ADRESSE_API.format(modele=modele()), data=json.dumps(corps).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": cle},
    )
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_SECONDES) as reponse:
            donnees = json.load(reponse)
        texte = donnees["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as erreur:      # 429 = quota dépassé, 400/403 = clé refusée…
        raise IAIndisponible(f"HTTP {erreur.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError):
        raise IAIndisponible("service injoignable ou réponse inattendue") from None
    texte = nettoyer(texte)
    if not texte:
        raise IAIndisponible("réponse vide")
    return texte


def nettoyer(texte):
    """L'écran affiche du texte brut : on retire la mise en forme Markdown (gras, puces à étoile, titres)."""
    texte = texte.replace("**", "").replace("__", "")
    lignes = []
    for ligne in texte.splitlines():
        ligne = re.sub(r"^\s*[*•]\s+", "- ", ligne)
        ligne = re.sub(r"^\s*#+\s*", "", ligne)
        lignes.append(ligne.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lignes)).strip()


# ---------------------------------------------------------------- questions sur le site

def _sections_de(utilisateur):
    return [(role, AIDE[role]) for role in roles.TOUS_LES_ROLES if role in AIDE and utilisateur.a_le_role(role)]


def consigne_assistant(utilisateur):
    """Consigne donnée au modèle : ce qu'il peut dire, avec l'aide des rôles de la personne comme seul contenu."""
    morceaux = [
        "Tu es l'assistant de la plateforme de gestion des stages PFA/PFE de l'EIGSI Casablanca.",
        "Réponds en français, en vouvoyant (« vous », jamais « tu »), en 5 phrases au maximum, simplement, uniquement à partir du contenu "
        "ci-dessous. Écris en texte brut, sans gras, sans titres ni astérisques.",
        "Si la réponse n'y figure pas, dis-le et invite à contacter le Career Center. N'invente jamais une règle.",
        "Tu ne valides, ne refuses ni ne modifies rien. Ne demande jamais de données personnelles.",
        "", "PRÉSENTATION : " + INTRODUCTION,
    ]
    for role, contenu in _sections_de(utilisateur):
        morceaux.append(f"\nRÔLE « {role} » : {contenu['resume']}")
        for etape in contenu["etapes"]:
            morceaux.append(f"- {etape['titre']} : {etape['texte']}")
        for question, reponse in contenu["faq"]:
            morceaux.append(f"Question fréquente : {question} Réponse : {reponse}")
    return "\n".join(morceaux)


def _mots(texte):
    return {m for m in re.findall(r"\w{4,}", texte.lower())}


def reponse_de_secours(question, utilisateur):
    """Sans IA : cherche, dans l'aide des rôles de la personne, le passage qui ressemble le plus à la question."""
    mots = _mots(question)
    meilleur, score = None, 0
    for _role, contenu in _sections_de(utilisateur):
        candidats = [(q + " " + r, r) for q, r in contenu["faq"]]
        candidats += [(e["titre"] + " " + e["texte"], f"{e['titre']} : {e['texte']}") for e in contenu["etapes"]]
        for texte, reponse in candidats:
            commun = len(mots & _mots(texte))
            if commun > score:
                meilleur, score = reponse, commun
    if meilleur:
        return meilleur
    return ("Je n'ai pas trouvé de réponse dans l'aide. Consultez la page « À propos et aide » "
            "ou contactez le Career Center.")


def repondre(question, utilisateur):
    """Répond à une question sur le site. Renvoie {"texte", "mode"} avec mode = "ia" ou "secours" (+ "raison")."""
    texte = anonymiser(question)
    if not texte:
        return {"texte": "Posez votre question en quelques mots.", "mode": "secours", "raison": "vide"}
    if not verifier_plafond(utilisateur):
        return {"texte": reponse_de_secours(texte, utilisateur), "mode": "secours",
                "raison": "Plafond de questions atteint pour cette heure : réponse tirée de l'aide."}
    try:
        return {"texte": appeler_gemini(consigne_assistant(utilisateur), texte), "mode": "ia", "raison": ""}
    except IAIndisponible as erreur:
        return {"texte": reponse_de_secours(texte, utilisateur), "mode": "secours", "raison": str(erreur)}


# ---------------------------------------------------------------- relecture du sujet de stage

CONSIGNE_RELECTURE = (
    "Tu aides un étudiant ingénieur à améliorer le sujet de son stage avant de le soumettre à son encadrant. "
    "Réponds en français, en vouvoyant l'étudiant (écris « vous », « votre », jamais « tu », « ton »), par 3 à 5 remarques courtes sous forme de liste à tirets : "
    "précision du sujet, activités confiées, outils ou technologies, livrable attendu, adéquation avec une formation "
    "d'ingénieur. Sois bienveillant et concret. Ne réécris pas le sujet entier. Écris en texte brut, sans gras, "
    "sans titres ni astérisques. Ne valide ni ne refuse rien : c'est l'encadrant qui décide."
)


def relecture_de_secours(sujet):
    """Sans IA : quelques règles simples et honnêtes sur le texte du sujet."""
    remarques = []
    if len(sujet) < 60:
        remarques.append("Le sujet est très court : détaillez le contexte et le problème à résoudre.")
    if not re.search(r"\b(développ|concev|conçu|analys|mettre en place|mise en place|réalis|automatis|optimis|"
                     r"modélis|intégr|déploi|migr|étudi|audit)\w*", sujet.lower()):
        remarques.append("Aucune activité n'apparaît clairement : dites ce que vous ferez (concevoir, développer, analyser…).")
    if not re.search(r"\b(python|java|sql|excel|power ?bi|sap|cloud|api|logiciel|outil|plateforme|machine|données|réseau|"
                     r"capteur|process|qualité|norme)\w*", sujet.lower()):
        remarques.append("Précisez les outils, technologies ou méthodes utilisés.")
    if not re.search(r"\b(livrable|rapport|prototype|tableau de bord|application|maquette|cahier|résultat|objectif)\w*",
                     sujet.lower()):
        remarques.append("Indiquez ce que vous livrerez à la fin (prototype, rapport, tableau de bord…).")
    return "\n".join("- " + r for r in remarques) or "- Le sujet semble complet : activités, outils et livrable sont mentionnés."


def relire_sujet(sujet, utilisateur):
    """Relit un sujet de stage. Renvoie {"texte", "mode", "raison"} ; n'enregistre rien."""
    texte = anonymiser(sujet)
    if len(texte) < 10:
        return {"texte": "Écrivez d'abord votre sujet dans le champ, puis relancez la relecture.",
                "mode": "secours", "raison": "vide"}
    if not verifier_plafond(utilisateur):
        return {"texte": relecture_de_secours(texte), "mode": "secours",
                "raison": "Plafond atteint pour cette heure : remarques simples."}
    try:
        return {"texte": appeler_gemini(CONSIGNE_RELECTURE, texte), "mode": "ia", "raison": ""}
    except IAIndisponible as erreur:
        return {"texte": relecture_de_secours(texte), "mode": "secours", "raison": str(erreur)}
