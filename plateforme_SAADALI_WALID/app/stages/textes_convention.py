"""
Textes fixes de la convention de stage (articles 2 et 4 à 13).

Ils reprennent le texte d'une convention « Stage Technicien » EIGSICA (2026). Le texte juridique
officiel reste celui de l'école : s'il change, ce fichier est le seul à modifier.

Format : chaque article est une liste de « blocs » :
  - une chaîne            -> un paragraphe
  - ("liste", [..])       -> une liste à puces
  - ("sous", "6.1 …")     -> un sous-titre souligné
Variables remplacées à la génération : {ecole_nom}, {ecole_sigle}, {email_contact}, {directeur_suffixe}.
(Les noms de personnes ne sont jamais écrits ici : ils viennent des « Paramètres de l'école ».)
"""

NOTA = (
    "Nota : la présente convention doit être complétée et signée par l'Organisme d'accueil "
    "<u>avant le début du stage</u> : dans le cas contraire, {ecole_nom} se dégage de toute "
    "responsabilité en cas d'incidents dans l'Organisme d'accueil."
)

OBJECTIF = [
    "Le stage a pour objectif essentiel de consolider les compétences du futur diplômé et de le "
    "préparer à son entrée dans la vie professionnelle. Il permet également au stagiaire "
    "d'approfondir sa connaissance du fonctionnement d'un Organisme d'accueil.",
    "Le référentiel de compétences de l'ingénieur EIGSI / EIGSICA se décline comme suit :",
    ("liste", [
        "Connaissance et compréhension d'un large champ de sciences fondamentales et capacité d'analyse "
        "et de synthèse qui leur est associée,",
        "Aptitude à mobiliser les ressources d'un champ scientifique et technique liées à une spécialité,",
        "Maîtrise des méthodes et des outils de l'ingénieur : identification et résolution de problèmes, "
        "en faisant appel à l'expérimentation, l'innovation et la recherche, la collecte et "
        "l'interprétation de données, l'utilisation des outils informatiques, l'analyse et la conception "
        "de systèmes,",
        "Capacité à s'intégrer dans une organisation, à l'animer et à la faire évoluer : connaissance de "
        "soi, esprit d'équipe, engagement et leadership, management de projets, maîtrise d'ouvrage, "
        "communication avec des spécialistes comme avec des non-spécialistes,",
        "Aptitude à prendre en compte des enjeux professionnels : esprit d'Organisme d'accueil, "
        "compétitivité et productivité, innovation, propriété intellectuelle et industrielle, respect des "
        "procédures qualité, sécurité, santé et sécurité au travail,",
        "Aptitude à travailler en contexte international : maîtrise de plusieurs langues étrangères, "
        "ouverture culturelle, expérience internationale, renseignement économique,",
        "Aptitude à mettre en œuvre les principes du développement durable : environnement, économie, "
        "social et gouvernance,",
        "Aptitude à prendre en compte et à faire respecter des valeurs sociétales : appropriation des "
        "valeurs sociales, de responsabilité, d'éthique, de sécurité et de santé,",
        "Capacité à opérer ses choix professionnels et à s'insérer dans la vie professionnelle,",
        "Capacité à intégrer et à savoir-relier : transfert de connaissances, résolution de problèmes "
        "complexes.",
    ]),
    "L'objet du stage est établi d'un commun accord entre l'Organisme d'accueil et l'Ecole selon les "
    "objectifs pédagogiques formulés par l'Ecole. Toute modification substantielle de l'objet du stage "
    "suppose l'accord de l'Ecole. Le stagiaire doit remettre à l'Ecole un descriptif du stage avant "
    "signature de la convention.",
]

# Article 3 : prolongation, puis règles de présence (la période, la durée hebdomadaire, les horaires
# et les cas particuliers sont insérés par convention_pdf.py à partir de la fiche de stage)
MODALITES_PROLONGATION = (
    "Un avenant à la convention pourra éventuellement être établi en cas de prolongation de stage faite "
    "à la demande de l'Organisme d'accueil et de l'élève stagiaire. Les prolongations seront soumises "
    "aux obligations du programme concerné et dans la limite de 6 mois."
)
MODALITES_PRESENCE = (
    "La présence du stagiaire dans l'organisme d'accueil suit les règles applicables aux salariés de "
    "l'organisme pour ce qui a trait : aux durées maximales quotidienne et hebdomadaire de présence, à la "
    "présence de nuit, au repos quotidien, au repos hebdomadaire et aux jours fériés. Il est interdit de "
    "confier au stagiaire des tâches dangereuses pour sa santé ou sa sécurité. Si le stagiaire doit être "
    "présent dans l'Organisme d'accueil la nuit, le dimanche ou un jour férié l'Organisme d'accueil doit "
    "indiquer ci-dessous les cas particuliers :"
)

# Article 4 (le titre complet est écrit dans convention_pdf.py)
ENCADREMENT = [
    "Le stagiaire, pendant la durée de son stage dans l'Organisme d'accueil, demeure élève de l'Ecole ; "
    "il est suivi par un tuteur de l'Ecole (référent école). L'Organisme d'accueil désigne un Tuteur "
    "(indiqué à l'article 1 de la présente convention), chargé d'assurer le suivi technique et "
    "d'optimiser les conditions de réalisation du stage. Le Tuteur de l'Organisme d'accueil est membre "
    "du jury de soutenance de stage, le cas échéant.",
    "Le stagiaire et l'Organisme d'accueil s'engagent à respecter les <b>procédures d'évaluation des "
    "stages</b> en vigueur à l'{ecole_sigle}.",
]

# Précisions propres à un type de stage (clé : nom du type, voir stages/models.py TYPE_PAR_ANNEE).
# Seul le texte du stage « Technicien » est connu ; les autres types sont à fournir par l'école.
ENCADREMENT_PAR_TYPE = {
    "Technicien": (
        "Modalités concernant le Stage Technicien : le stagiaire s'engage à respecter les jalonnements "
        "de diffusion de l'autoévaluation intermédiaire et du rapport. Le rapport est soumis "
        "obligatoirement pour avis au Tuteur de l'Organisme d'accueil, avant diffusion au service des "
        "Stages. Un contact téléphonique pourra être établi par l'Enseignant référent à l'issue de "
        "l'autoévaluation."
    ),
}

# Article 5 : [0] avant le montant, [1] après les modalités de versement
GRATIFICATION = [
    "La rémunération du stagiaire n'est pas obligatoire.",
    "Les frais de déplacement et d'hébergement engagés par le stagiaire à la demande de l'Organisme "
    "d'accueil, ainsi que les frais de formation éventuellement nécessités par le stage, seront "
    "intégralement pris en charge par celui-ci selon les modalités en vigueur dans l'Organisme d'accueil.",
]

# Article 6 (la case « couverture maladie OUI / NON » est insérée après le 6.1)
COUVERTURE_6_1 = [
    ("sous", "6.1. Couverture maladie et santé"),
    "Couverture fournie par l'Organisme d'accueil :",
    "L'Organisme d'accueil doit cocher la case appropriée ci-dessous pour indiquer s'il fournira la "
    "couverture médicale maladie et santé pour le stagiaire, conformément aux règlements locaux.",
]
COUVERTURE_SUITE = [
    ("sous", "6.2. Couverture de l'assurance pour les accidents survenus en milieu de travail durant "
             "le stage (dont la durée ne doit pas dépasser 6 mois, toutes extensions comprises)"),
    "La couverture pour les accidents survenus durant la période de stage et sur le lieu de travail "
    "inclut les accidents qui se produisent :",
    ("liste", [
        "Dans le périmètre du lieu de travail et pendant les heures de travail ;",
        "Sur le trajet aller ou retour entre le lieu de résidence actuel du stagiaire et le lieu de travail ;",
        "Sur le trajet aller ou retour entre le lieu de résidence officiel du stagiaire et le lieu de travail ;",
        "Sur une affectation externe du stagiaire par l'Organisme d'accueil, couverte par une autorisation écrite.",
    ]),
    "L'Organisme d'accueil s'engage à couvrir le stagiaire contre les risques d'accident sur le lieu de "
    "travail, les risques d'accident sur le trajet aller ou retour entre le lieu de résidence et le lieu "
    "de travail, et le risque de maladies, professionnelles ou non, et s'engage à prendre toutes les "
    "mesures et faire toutes les déclarations en temps utile si l'une quelconque des conditions énoncées "
    "au paragraphe ci-dessus n'est pas remplie.",
    "La déclaration d'accident sur le lieu de travail est de la responsabilité de l'Ecole. L'Organisme "
    "d'accueil doit informer l'{ecole_sigle} <b>par écrit</b> au plus tard 48 heures après l'accident "
    "(mail à {email_contact}). L'école se chargera de le déclarer auprès de sa compagnie d'assurance.",
    "En toutes circonstances,",
    ("liste", [
        "L'Organisme d'accueil doit immédiatement aviser l'Ecole si le stagiaire est victime d'un "
        "accident sur le lieu de travail pendant le stage ;",
        "L'Organisme d'accueil doit fournir les données complètes pour la couverture d'assurance du "
        "stagiaire s'il lui est demandé d'entreprendre des missions à l'extérieur du périmètre du lieu "
        "de travail.",
    ]),
    "Chaque fois que les conditions requises ne sont pas remplies, l'Organisme d'accueil s'engage à "
    "entreprendre l'ensemble des démarches nécessaires pour assurer la protection et la couverture du "
    "stagiaire, et à faire toute déclaration nécessaire en cas d'accident sur le lieu de travail.",
    ("sous", "6.3. Les déplacements"),
    "En cas de déplacement, il appartient à l'Organisme d'accueil d'établir, dans tous les cas, un "
    "descriptif nominatif de la nature du déplacement et d'en informer l'{ecole_sigle}. Lorsque ces "
    "conditions ne sont pas remplies, l'Organisme d'accueil s'engage à cotiser pour la protection de "
    "l'élève stagiaire et à faire les déclarations nécessaires en cas d'accident du travail.",
]

ARTICLES_SUIVANTS = [
    ("Article 7 : Assurance Responsabilité Civile", [
        "Si l'Organisme d'accueil met un véhicule à moteur à la disposition du stagiaire, il convient de "
        "s'assurer que la police d'assurance pour le déplacement couvre son usage par le stagiaire. Si, "
        "dans le cadre de son stage, le stagiaire se sert de son propre véhicule ou d'un véhicule prêté "
        "par un tiers, il doit le déclarer à l'assureur du véhicule et payer tout complément d'assurance.",
    ]),
    ("Article 8 : Discipline", [
        "Durant son séjour dans l'Organisme d'accueil, le stagiaire est soumis à la discipline et au "
        "règlement intérieur de l'Organisme d'accueil, notamment en ce qui concerne les horaires, les "
        "visites médicales obligatoires et les règles d'hygiène et de sécurité en vigueur dans "
        "l'Organisme d'accueil. Toute sanction disciplinaire ne peut être décidée que par l'Ecole. Dans "
        "ce cas, l'Organisme d'accueil informe l'Ecole des manquements et lui fournit éventuellement les "
        "éléments constitutifs. En cas de manquement grave à la discipline, le responsable d'Organisme "
        "d'accueil se réserve le droit de mettre fin au stage de l'élève fautif, tout en respectant les "
        "dispositions fixées à l'article 9 de la présente convention.",
    ]),
    ("Article 9 : Interruption du stage", [
        ("sous", "9.1 Interruption temporaire"),
        "L'organisme d'accueil a le devoir de signaler toute absence du stagiaire par email au référent "
        "de l'{ecole_sigle}.",
        "Pour les stages d'une durée supérieure à 2 mois et dans la limite de la durée maximale, le "
        "stagiaire pourra bénéficier de congés suivant les règles de l'Organisme d'accueil. Dans le cas "
        "d'une interruption pour congés non indemnisés, un avenant à la présente convention devra être "
        "signé par les cocontractants au moins 5 jours ouvrés avant le départ en congés du stagiaire.",
        "Pour toute autre interruption temporaire du stage (maladie, absence injustifiée...), "
        "l'Organisme d'accueil appréciera, en fonction du degré de gravité, le besoin d'en avertir le "
        "service Stages de l'Ecole.",
        ("sous", "9.2 Interruption définitive"),
        "En cas d'interruption définitive du stage du fait de l'organisme d'accueil ou du stagiaire, "
        "l'{ecole_sigle} devra être informée <u>au moins 10 jours ouvrés avant la date proposée de "
        "l'interruption du stage</u>. Cette communication sera faite officiellement par le demandeur "
        "soit par courrier déposé contre décharge soit par courrier postal en recommandé à l'attention "
        "du Directeur des Etudes{directeur_suffixe}.",
        "Les raisons invoquées seront examinées par l'Ecole en étroite concertation avec l'organisme "
        "d'accueil ou le stagiaire. La décision définitive concernant l'interruption ou non du stage ne "
        "sera prise qu'à l'issue de cette phase de concertation.",
    ]),
    ("Article 10 : Devoir de réserve et confidentialité / Propriété intellectuelle", [
        "Le secret professionnel est de rigueur absolue. Le stagiaire prend donc l'engagement de "
        "n'utiliser en aucun cas les informations recueillies par eux pour en faire l'objet de "
        "publication, communication à des tiers sans accord écrit préalable de la Direction de "
        "l'Organisme d'accueil, y compris le rapport de stage. Cet engagement vaudra non seulement pour "
        "la durée du stage mais également après son expiration. Le stagiaire s'engage à ne conserver, "
        "emporter, ou prendre copie d'aucun document ou logiciel, de quelque nature que ce soit, "
        "appartenant à l'Organisme d'accueil, sauf accord écrit de ce dernier.",
        "Il est rappelé que l'Etudiant(e) stagiaire n'étant pas un salarié de l'{ecole_sigle} et "
        "conformément à la législation en vigueur, les droits de propriété intellectuelle découlant de "
        "la réalisation de son stage lui appartiennent. L'Organisme d'accueil ou l'Organisme public fera "
        "par conséquent son affaire des modalités éventuelles de cession et d'exploitation des droits de "
        "l'Etudiant(e) stagiaire conformément aux dispositions du Code de la propriété intellectuelle.",
    ]),
    ("Article 11 : Recrutement", [
        "S'il advenait qu'un contrat de travail prenant effet avant la date de fin du stage soit signé "
        "avec l'Organisme d'accueil, la présente convention deviendrait caduque et le stagiaire ne "
        "relèverait plus de la responsabilité de l'Ecole. Ce dernier devrait impérativement en être "
        "averti avant signature du contrat.",
    ]),
    ("Article 12 : Clauses diverses", [
        "Le stagiaire ne peut pas s'attendre à bénéficier de services informatiques fournis par l'école "
        "pour des activités liées à son placement au sein de l'organisme d'accueil.",
    ]),
    ("Article 13 : Gestion des données personnelles", [
        "Les informations personnelles recueillies dans le présent document et relatives à l'organisme "
        "d'accueil, à l'{ecole_sigle} et à l'étudiant stagiaire sont enregistrées dans un fichier "
        "informatisé sécurisé sous la responsabilité du responsable du traitement, représenté par le "
        "Directeur des Etudes.",
        "Les finalités de ce traitement sont la gestion des stages des apprenants ainsi que "
        "l'établissement d'une liste recensant toutes les entreprises au sein desquelles les anciens "
        "étudiants ont effectué un stage afin de faciliter la recherche de stage des nouveaux étudiants.",
        "Conformément au cadre réglementaire, le consentement est de fait car le traitement entre dans le "
        "cadre de l'exécution d'un contrat auquel les différentes parties concernées sont parties "
        "prenantes. Les données collectées seront communiquées aux seuls destinataires suivants : les "
        "personnels chargés de la gestion des stages des apprenants et les étudiants de l'{ecole_sigle} "
        "pour ce qui est des données personnelles concernant les entreprises susceptibles d'accueillir des "
        "stagiaires. Dans le cadre de ce traitement, les données seront conservées pendant 10 ans.",
        "L'étudiant stagiaire peut exercer un droit d'accès à tout moment à toutes les données le "
        "concernant pour les consulter, les copier, les rectifier ou exercer son droit à la portabilité "
        "de ses données (un mail peut être adressé directement à {email_contact}).",
        "S'agissant des organismes d'accueil qui acceptent d'apparaître sur la liste à destination des "
        "actuels apprenants, le droit d'accès et/ou de rectification des données peut s'exercer à tout "
        "moment. De même que pour des raisons légitimes, le droit d'opposition pourra être mis en œuvre "
        "(un mail peut être adressé directement à {email_contact}).",
    ]),
]
