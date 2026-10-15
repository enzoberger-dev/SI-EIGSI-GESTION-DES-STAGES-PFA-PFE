"""
Menu latéral : prépare, pour chaque page, la liste des liens auxquels la personne a droit.

C'est un « processeur de contexte » Django : une fonction appelée automatiquement avant l'affichage
de chaque page, qui ajoute la variable `menu` à tous les gabarits (voir config/settings.py).
On réutilise la liste des espaces et des liens de espaces/views.py : une seule source de vérité,
donc le menu ne peut pas montrer un lien auquel la personne n'a pas droit.
"""

from django.urls import reverse


def menu(request):
    """Variable `menu` : liste de groupes {titre, liens: [{texte, adresse, actif}]}. Vide si pas connecté."""
    utilisateur = getattr(request, "user", None)
    if utilisateur is None or not utilisateur.is_authenticated:
        return {"menu": [], "initiales": "", "assistant_ia_active": False}

    # Import ici (et non en haut du fichier) pour éviter un import circulaire au démarrage
    from .views import ESPACES, LIENS

    def lien(texte, adresse):
        return {"texte": texte, "adresse": adresse, "actif": request.path == adresse}

    groupes = [{"titre": "", "liens": [lien("Accueil", reverse("accueil"))]}]
    for cle, (role, titre, _phrase) in ESPACES.items():
        if not utilisateur.a_le_role(role):
            continue
        liens = [lien(texte, reverse(nom)) for texte, nom in LIENS.get(cle, [])]
        if not liens:
            liens = [lien(titre, reverse("espace-" + cle))]
        groupes.append({"titre": titre, "liens": liens})
    groupes.append({"titre": "Aide", "liens": [lien("À propos et aide", reverse("aide"))]})
    if utilisateur.is_staff:
        groupes.append({"titre": "Administration", "liens": [lien("Administration du site", reverse("admin:index"))]})

    nom = utilisateur.get_full_name() or utilisateur.email or ""
    morceaux = [m for m in nom.replace("@", " ").replace(".", " ").split() if m]
    initiales = "".join(m[0] for m in morceaux[:2]).upper()
    from . import assistant as assistant_ia   # import ici : même raison que ci-dessus
    return {"menu": groupes, "initiales": initiales,
            "assistant_ia_active": assistant_ia.lire_cle() is not None}
