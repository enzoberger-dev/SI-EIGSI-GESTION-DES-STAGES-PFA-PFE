"""
Génération du PDF de la convention de stage avec ReportLab.

La mise en page suit celle d'une convention EIGSICA réelle : titre selon le type de stage,
article 1 (parties), articles 2 à 13, puis le cadre des signatures sur 3 colonnes :
  - colonne 1 : le directeur de l'entreprise, et en dessous le tuteur de l'organisme d'accueil ;
  - colonne 2 : le directeur des études (signe en premier) ;
  - colonne 3 : le stagiaire.
Les informations viennent de la fiche de stage (Stage) et des paramètres de l'école
(ParametresEcole). Les textes fixes sont dans textes_convention.py.
"""

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from . import textes_convention as textes
from .models import ParametresEcole

POINTS = "…………………………"


def _texte(valeur, defaut=POINTS):
    """Texte sûr pour ReportLab (les caractères < > & sont neutralisés)."""
    return escape(str(valeur)) if valeur not in (None, "") else defaut


def _date(d):
    return d.strftime("%d/%m/%Y") if d else "…………"


def _virgule(nombre):
    return str(nombre).replace(".", ",")


def _canvas_avec_pied_de_page(numero):
    """Canvas qui écrit « Convention n° … » et « Page x sur y » en bas de chaque page."""

    class CanvasNumerote(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._etats = []

        def showPage(self):
            self._etats.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._etats)
            for etat in self._etats:
                self.__dict__.update(etat)
                self.setFont("Helvetica", 8)
                self.drawString(2 * cm, 1.2 * cm, f"Convention n° {numero}")
                self.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {self._pageNumber} sur {total}")
                super().showPage()
            super().save()

    return CanvasNumerote


def generer_pdf(convention):
    """Renvoie le PDF (en octets) de la convention."""
    stage = convention.stage
    ecole = ParametresEcole.actuels()
    entreprise = stage.entreprise
    etudiant = stage.etudiant
    promotion = stage.promotion

    # Variables des textes fixes (échappées : elles sont insérées dans du balisage)
    variables = {
        "ecole_nom": escape(ecole.nom),
        "ecole_sigle": escape(ecole.sigle),
        "email_contact": escape(ecole.email_contact),
        "directeur_suffixe": f", {escape(ecole.directeur_etudes)}" if ecole.directeur_etudes else "",
    }

    styles = getSampleStyleSheet()
    titre = ParagraphStyle("titre", parent=styles["Title"], fontSize=17, spaceAfter=6)
    nota = ParagraphStyle("nota", parent=styles["Italic"], fontSize=8.5, spaceAfter=8)
    # keepWithNext : un titre n'est jamais seul en bas d'une page
    article = ParagraphStyle("article", parent=styles["Heading3"], fontSize=11, spaceBefore=10,
                             spaceAfter=4, keepWithNext=1)
    courant = ParagraphStyle("courant", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=4)
    sous_titre = ParagraphStyle("sous", parent=courant, spaceBefore=4, keepWithNext=1)
    cadre = ParagraphStyle("cadre", parent=courant, fontSize=9.5, leading=13)
    centre = ParagraphStyle("centre", parent=cadre, alignment=1)

    def paragraphe(texte):
        """Un paragraphe de texte fixe (le balisage <b>, <u> du texte est conservé)."""
        return Paragraph(texte.format(**variables), courant)

    def rendre(blocs):
        """Transforme une liste de blocs (voir textes_convention.py) en éléments du PDF."""
        elements = []
        for bloc in blocs:
            if isinstance(bloc, str):
                elements.append(paragraphe(bloc))
            elif bloc[0] == "liste":
                elements.append(ListFlowable(
                    [ListItem(paragraphe(item), leftIndent=14) for item in bloc[1]],
                    bulletType="bullet", start="•", bulletFontSize=8, leftIndent=14,
                ))
            elif bloc[0] == "sous":
                elements.append(Paragraph(f"<u><b>{escape(bloc[1])}</b></u>", sous_titre))
        return elements

    def encadre(lignes, style=cadre):
        tableau = Table([[Paragraph(ligne, style)] for ligne in lignes], colWidths=[17 * cm])
        tableau.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return tableau

    histoire = [Paragraph(f"CONVENTION Stage {_texte(stage.type_stage)}", titre),
                Paragraph(textes.NOTA.format(**variables), nota)]

    # --- Article 1 : parties signataires ---------------------------------
    histoire.append(Paragraph("ARTICLE 1 : Parties signataires", article))
    histoire.append(Paragraph("La présente convention régit les rapports entre <b>l'organisme d'accueil</b> :", courant))
    adresse = ", ".join(p for p in [entreprise.adresse, f"{entreprise.code_postal} {entreprise.ville}".strip(),
                                    entreprise.pays] if p)
    histoire.append(encadre([
        f"<b>Raison Sociale :</b> {_texte(entreprise.raison_sociale)}",
        f"<b>Adresse :</b> {_texte(adresse)}",
        f"<b>Lieu du Stage si différent :</b> {_texte(stage.lieu_si_different, '')}",
        f"<b>Représenté par :</b> {_texte(stage.representant_nom)}",
        f"<b>Fonction :</b> {_texte(stage.representant_fonction)}",
        f"<b>Tuteur Organisme d'accueil :</b> {_texte(stage.tuteur_nom)}",
    ]))
    histoire.append(Spacer(1, 6))
    histoire.append(Paragraph("Et <b>l'établissement d'enseignement supérieur</b> :", courant))
    representant = (f"<b>{_texte(ecole.representant)}</b>, Directeur du campus {_texte(ecole.sigle)}"
                    if ecole.representant else f"le Directeur du campus {_texte(ecole.sigle)}")
    contact = f"<b>{_texte(ecole.email_contact)}" + (f" – Tél. {_texte(ecole.telephone)}" if ecole.telephone else "") + "</b>"
    histoire.append(encadre([
        f"<b>{_texte(ecole.nom)}</b> ci-après nommé <b>{_texte(ecole.sigle)}</b>",
        f"Représentée par {representant},",
        f"{_texte(ecole.adresse)}" + (f" ({_texte(ecole.site_web)})" if ecole.site_web else ""),
        contact,
    ], style=centre))
    histoire.append(Spacer(1, 6))
    histoire.append(Paragraph("Et <b>l'étudiant</b> :", courant))
    lignes_etudiant = [
        f"<b>{_texte(etudiant.get_full_name() or etudiant.email)} étudiant(e) de "
        f"{promotion.annee_etudes}{'ère' if promotion.annee_etudes == 1 else 'ème'} année</b>",
        f"Cursus suivi au sein de l'établissement d'enseignement supérieur : {_texte(ecole.cursus)}",
    ]
    if promotion.volume_horaire:
        lignes_etudiant.append(f"Volume horaire : {promotion.volume_horaire} heures pour l'année d'enseignement")
    histoire.append(encadre(lignes_etudiant))
    histoire.append(Spacer(1, 8))
    histoire.append(Paragraph(f"<b>Sujet de stage, activités confiées :</b> {_texte(stage.sujet)}", courant))

    # --- Article 2 : objectif ---------------------------------------------
    histoire.append(Paragraph("ARTICLE 2 : Objectif du stage", article))
    histoire.extend(rendre(textes.OBJECTIF))

    # --- Article 3 : modalités --------------------------------------------
    histoire.append(Paragraph("ARTICLE 3 : Modalités du stage", article))
    histoire.append(Paragraph("Période de stage", courant))
    histoire.append(Paragraph(
        f"<b>Le stage aura lieu du {_date(stage.date_debut)} au {_date(stage.date_fin)}</b>", courant))
    if stage.date_debut and stage.date_fin:
        mois = round((stage.date_fin - stage.date_debut).days / 30, 2)
        histoire.append(Paragraph(f"<b>Soit {_virgule(mois)} mois</b> ({_virgule(stage.duree_semaines)} semaines)", courant))
    histoire.append(paragraphe(textes.MODALITES_PROLONGATION))
    histoire.append(Paragraph(
        f"La <b>durée hebdomadaire maximale</b> de présence du stagiaire dans l'Organisme d'accueil sera de "
        f"<b>{_texte(stage.heures_max_semaine, '…')} heures</b>.", courant))
    histoire.append(Paragraph(f"» Horaires de présence du stagiaire : {_texte(stage.horaires)}", courant))
    histoire.append(paragraphe(textes.MODALITES_PRESENCE))
    histoire.append(Paragraph(_texte(stage.cas_particuliers, "néant"), courant))

    # --- Article 4 : encadrement ------------------------------------------
    histoire.append(Paragraph(
        "ARTICLE 4 : Statut du stagiaire – Accueil et encadrement (soutenance, évaluation, fin de stage)", article))
    histoire.extend(rendre(textes.ENCADREMENT))
    precision = textes.ENCADREMENT_PAR_TYPE.get(stage.type_stage)
    if precision:
        histoire.append(Paragraph(escape(precision), courant))

    # --- Article 5 : gratification ----------------------------------------
    histoire.append(Paragraph("ARTICLE 5 : Gratification – Avantages en nature – Remboursement de frais", article))
    histoire.append(Paragraph(textes.GRATIFICATION[0], courant))
    montant = f"{_virgule(stage.gratification_montant)} MAD par mois" if stage.gratification_montant else "………"
    histoire.append(Paragraph(f"La gratification est fixée à : <b>{montant}</b>", courant))
    histoire.append(Paragraph(
        f"<u>Modalités de versement de la gratification</u> : {_texte(stage.gratification_modalites)}", courant))
    histoire.append(Paragraph(textes.GRATIFICATION[1], courant))
    histoire.append(Paragraph(f"Liste des avantages en nature : {_texte(stage.avantages_nature)}", courant))

    # --- Article 6 : couverture sociale -----------------------------------
    histoire.append(Paragraph("ARTICLE 6 : Couverture sociale", article))
    histoire.extend(rendre(textes.COUVERTURE_6_1))
    histoire.append(Paragraph("[   ]  OUI          [   ]  NON", courant))
    histoire.extend(rendre(textes.COUVERTURE_SUITE))

    # --- Articles 7 à 13 --------------------------------------------------
    for titre_article, blocs in textes.ARTICLES_SUIVANTS:
        histoire.append(Paragraph(escape(titre_article.replace("Article", "ARTICLE", 1)), article))
        histoire.extend(rendre(blocs))

    # --- Signatures (sur papier), mêmes positions que la convention de référence ---
    def bloc_signature(entete, hauteur_signature):
        tableau = Table(
            [[Paragraph(entete, cadre)], ["Date :"], ["Signature :"]],
            colWidths=[5.3 * cm], rowHeights=[1.5 * cm, 0.7 * cm, hauteur_signature],
        )
        tableau.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.6, colors.black), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return tableau

    nom_directeur = f"<br/>{_texte(ecole.directeur_etudes)}" if ecole.directeur_etudes else ""
    colonne_entreprise = [
        bloc_signature("<b>Le Directeur de l'Entreprise</b><br/>(ou son représentant)", 1.8 * cm),
        Spacer(1, 6),
        bloc_signature("<b>Le Tuteur de l'organisme d'accueil,</b>", 1.8 * cm),
    ]
    colonne_ecole = bloc_signature(
        f"<b>Directeur des Etudes et de la Recherche</b>{nom_directeur}", 6.0 * cm)
    colonne_etudiant = bloc_signature(
        f"<b>Le stagiaire,</b><br/>{_texte(etudiant.get_full_name() or etudiant.email)}", 6.0 * cm)
    signatures = Table([[colonne_entreprise, colonne_ecole, colonne_etudiant]], colWidths=[5.67 * cm] * 3)
    signatures.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    histoire.append(Spacer(1, 14))
    histoire.append(KeepTogether([signatures]))

    memoire = io.BytesIO()
    document = SimpleDocTemplate(
        memoire, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
        title=f"Convention de stage n° {convention.numero}", author=ecole.nom,
    )
    document.build(histoire, canvasmaker=_canvas_avec_pied_de_page(convention.numero))
    return memoire.getvalue()
