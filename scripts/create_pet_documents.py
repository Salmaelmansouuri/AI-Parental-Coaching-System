# -*- coding: utf-8 -*-

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUTPUT_DIR = Path("data/pet_documents/05_documents_synthetiques")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(
    TTFont("Arial", r"C:\Windows\Fonts\arial.ttf")
)

pdfmetrics.registerFont(
    TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf")
)

styles = getSampleStyleSheet()

title = ParagraphStyle(
    "TitlePET",
    parent=styles["Title"],
    fontName="Arial-Bold",
    fontSize=18,
    leading=22,
    alignment=TA_CENTER,
    spaceAfter=16,
)

h1 = ParagraphStyle(
    "H1PET",
    parent=styles["Heading1"],
    fontName="Arial-Bold",
    fontSize=14,
    leading=18,
    spaceBefore=10,
    spaceAfter=7,
)

body = ParagraphStyle(
    "BodyPET",
    parent=styles["BodyText"],
    fontName="Arial",
    fontSize=10.5,
    leading=15,
    spaceAfter=8,
)

note = ParagraphStyle(
    "NotePET",
    parent=styles["BodyText"],
    fontName="Arial",
    fontSize=9,
    leading=12,
    spaceAfter=8,
)


def create_pdf(filename, document_title, sections):
    path = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    story = [
        Paragraph(document_title, title),
        Paragraph(
            "<b>Document synthétique destiné au corpus RAG du projet "
            "Coach parental intelligent.</b>",
            note,
        ),
        Paragraph(
            "Cette synthèse s'appuie sur les ressources P.E.T. intégrées "
            "au corpus du projet. Les situations pratiques sont des exemples "
            "illustratifs destinés à faciliter la recherche sémantique.",
            note,
        ),
        Spacer(1, 8),
    ]

    for section_title, paragraphs in sections:
        story.append(Paragraph(section_title, h1))

        for paragraph in paragraphs:
            story.append(Paragraph(paragraph, body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Sources principales", h1))

    story.append(
        Paragraph(
            "Thomas Gordon, <i>A Theory of Parent Effectiveness</i>.",
            note,
        )
    )

    story.append(
        Paragraph(
            "Larissa Dann, <i>Parent Effectiveness Training (P.E.T.): "
            "Forging Strong Families - the Best Prevention</i>.",
            note,
        )
    )

    story.append(
        Paragraph(
            "Ressources Parent Effectiveness Training intégrées au corpus du projet.",
            note,
        )
    )

    doc.build(story)

    print(f"PDF créé : {path}")


# ============================================================
# PET 14 - THEORIE GENERALE
# ============================================================

create_pdf(
    "PET_14_Theorie_Generale_PET.pdf",
    "Théorie générale du Parent Effectiveness Training (P.E.T.)",
    [
        (
            "1. Présentation générale",
            [
                "Le Parent Effectiveness Training, ou P.E.T., est une approche "
                "de communication parent-enfant développée par le psychologue "
                "Thomas Gordon. Elle vise à améliorer la relation entre le "
                "parent et l'enfant grâce à des compétences d'écoute, "
                "d'expression des besoins et de résolution des conflits.",

                "L'approche considère que le parent et l'enfant possèdent tous "
                "les deux des besoins légitimes. L'objectif n'est donc pas de "
                "chercher systématiquement un gagnant et un perdant, mais de "
                "favoriser une relation respectueuse et des solutions acceptables "
                "pour les personnes concernées.",
            ],
        ),
        (
            "2. Acceptation et comportement",
            [
                "Dans le modèle de Gordon, un comportement peut être acceptable "
                "pour un parent dans une situation et devenir difficilement "
                "acceptable dans une autre. L'analyse doit donc tenir compte "
                "du contexte, du parent, de l'enfant et de l'environnement.",

                "Le comportement doit être distingué de la personnalité de "
                "l'enfant. Décrire ce qui se passe est généralement préférable "
                "à utiliser des étiquettes comme « paresseux », « méchant » "
                "ou « désobéissant ».",
            ],
        ),
        (
            "3. À qui appartient le problème ?",
            [
                "Une étape centrale consiste à identifier la personne qui "
                "rencontre le problème. Lorsque l'enfant rencontre une difficulté, "
                "l'écoute active est particulièrement adaptée.",

                "Lorsque le comportement de l'enfant empêche le parent de "
                "satisfaire un besoin important, le parent peut exprimer son "
                "expérience à l'aide d'un message-je.",

                "Lorsque les besoins du parent et de l'enfant sont incompatibles, "
                "une démarche de résolution de conflit gagnant-gagnant peut être "
                "utilisée.",
            ],
        ),
        (
            "4. Les principales stratégies P.E.T.",
            [
                "<b>Écoute active :</b> aider l'enfant à exprimer son expérience "
                "sans jugement ni solution imposée.",

                "<b>Message-je :</b> exprimer un problème du parent en décrivant "
                "le comportement, son effet concret et le besoin ou ressenti associé.",

                "<b>Method III :</b> rechercher ensemble une solution qui prend "
                "en compte les besoins du parent et ceux de l'enfant.",
            ],
        ),
        (
            "5. Exemple global",
            [
                "Un adolescent rentre de l'école très en colère après une dispute. "
                "Dans un premier temps, le parent peut utiliser l'écoute active : "
                "« Tu sembles vraiment énervé par ce qui s'est passé. »",

                "Plus tard, si l'adolescent met la musique très fort alors que "
                "le parent travaille, le parent peut utiliser un message-je : "
                "« Quand la musique est très forte pendant mon travail, j'ai du "
                "mal à me concentrer et j'ai besoin de calme. »",

                "Si l'adolescent souhaite écouter sa musique tandis que le parent "
                "a besoin de calme, les deux peuvent rechercher ensemble une "
                "solution acceptable.",
            ],
        ),
    ],
)


# ============================================================
# PET 15 - ECOUTE ACTIVE
# ============================================================

create_pdf(
    "PET_15_Ecoute_Active_Detaillee.pdf",
    "Écoute active dans l'approche P.E.T.",
    [
        (
            "1. Définition",
            [
                "L'écoute active est une compétence de communication utilisée "
                "lorsque l'enfant rencontre une difficulté ou possède le problème. "
                "Elle consiste à écouter avec attention et à reformuler le sens "
                "ou le sentiment exprimé par l'enfant.",

                "L'objectif n'est pas de résoudre immédiatement le problème à la "
                "place de l'enfant. Le parent montre qu'il cherche à comprendre "
                "l'expérience vécue et encourage l'enfant à poursuivre sa réflexion.",
            ],
        ),
        (
            "2. Attitudes utiles",
            [
                "Le parent peut laisser à l'enfant le temps de parler, éviter "
                "les interruptions et essayer de comprendre ce que l'enfant "
                "ressent derrière ses paroles.",

                "La reformulation doit rester une hypothèse. Le parent peut dire "
                "par exemple : « Tu as l'air déçu », « Tu sembles inquiet » ou "
                "« J'ai l'impression que cette situation t'a beaucoup énervé ».",
            ],
        ),
        (
            "3. Obstacles à la communication",
            [
                "Lorsque l'enfant possède un problème, certaines réponses peuvent "
                "interrompre la communication : donner immédiatement des ordres, "
                "menacer, moraliser, critiquer, juger ou chercher trop rapidement "
                "à expliquer ce que l'enfant devrait faire.",

                "Même un conseil bien intentionné peut être reçu comme une absence "
                "d'écoute si l'enfant souhaite d'abord exprimer ce qu'il ressent.",
            ],
        ),
        (
            "4. Exemple : conflit à l'école",
            [
                "<b>Enfant :</b> « Je ne veux plus jouer avec Youssef, il se moque "
                "toujours de moi. »",

                "<b>Réponse d'écoute active :</b> « Tu es blessé parce que tu as "
                "l'impression qu'il ne te respecte pas. »",

                "Cette réponse permet à l'enfant de confirmer, corriger ou "
                "approfondir ce qu'il ressent.",
            ],
        ),
        (
            "5. Exemple : mauvaise note",
            [
                "<b>Enfant :</b> « Je suis nul, j'ai encore raté mon contrôle. »",

                "<b>Réponse possible :</b> « Tu es vraiment déçu de ta note et "
                "tu commences à douter de toi. »",

                "Après avoir été écouté, l'enfant peut devenir plus disponible "
                "pour réfléchir lui-même aux solutions possibles.",
            ],
        ),
        (
            "6. Quand ne pas utiliser uniquement l'écoute active",
            [
                "Si le comportement de l'enfant crée directement un problème "
                "important pour le parent, l'écoute active seule n'est pas "
                "forcément suffisante. Le parent doit également pouvoir exprimer "
                "son propre besoin.",

                "De même, lorsqu'un véritable conflit de besoins persiste, une "
                "démarche de résolution de conflit peut devenir nécessaire.",
            ],
        ),
    ],
)


# ============================================================
# PET 16 - I MESSAGES
# ============================================================

create_pdf(
    "PET_16_I_Messages_Detailles.pdf",
    "Les I-Messages ou messages-je dans l'approche P.E.T.",
    [
        (
            "1. Objectif du message-je",
            [
                "Le message-je est principalement utilisé lorsque le parent "
                "possède le problème. Il permet d'exprimer l'impact d'un "
                "comportement sans transformer le message en jugement contre "
                "la personnalité de l'enfant.",

                "Le parent parle de son expérience, de ses besoins et des "
                "conséquences concrètes du comportement.",
            ],
        ),
        (
            "2. Structure pratique",
            [
                "Un message-je peut comporter trois éléments : le comportement "
                "observable, l'effet concret de ce comportement et le ressenti "
                "ou besoin du parent.",

                "Exemple : « Quand les chaussures restent au milieu du passage, "
                "je risque de trébucher et j'ai besoin que le passage reste libre. »",
            ],
        ),
        (
            "3. Décrire plutôt que juger",
            [
                "Dire « Tu es irresponsable » décrit la personne et peut provoquer "
                "une réaction défensive.",

                "Dire « Quand les affaires restent sur le sol, je dois les déplacer "
                "pour pouvoir passer » décrit une situation concrète et laisse "
                "davantage de place à la discussion.",
            ],
        ),
        (
            "4. Exemple : musique trop forte",
            [
                "Situation : le parent travaille et l'enfant écoute de la musique "
                "à un volume très élevé.",

                "Message accusateur : « Tu ne respectes jamais personne. »",

                "Message-je possible : « Quand la musique est aussi forte pendant "
                "que je travaille, je n'arrive plus à me concentrer et j'ai besoin "
                "de calme. »",
            ],
        ),
        (
            "5. Exemple : retard",
            [
                "Situation : un adolescent rentre beaucoup plus tard que l'heure "
                "annoncée sans prévenir.",

                "Message-je possible : « Quand tu rentres beaucoup plus tard sans "
                "m'envoyer de message, je m'inquiète parce que je ne sais pas si "
                "tu es en sécurité. »",
            ],
        ),
        (
            "6. Après le message-je",
            [
                "L'enfant peut réagir, expliquer son point de vue ou manifester "
                "une émotion. Le parent peut alors revenir à l'écoute active.",

                "Cette alternance entre expression claire du parent et écoute "
                "de l'enfant est importante dans une communication respectueuse.",
            ],
        ),
    ],
)


# ============================================================
# PET 17 - PROBLEM OWNERSHIP
# ============================================================

create_pdf(
    "PET_17_Problem_Ownership_Behavior_Window.pdf",
    "Problem Ownership et Behavior Window dans l'approche P.E.T.",
    [
        (
            "1. Pourquoi identifier le propriétaire du problème ?",
            [
                "Le choix de la stratégie dépend de la personne dont les besoins "
                "sont affectés. Identifier le propriétaire du problème évite "
                "d'utiliser automatiquement la même technique dans toutes les "
                "situations parentales.",

                "Cette distinction est particulièrement utile dans un système "
                "de coaching parental car elle permet de sélectionner une "
                "intervention cohérente avec la situation.",
            ],
        ),
        (
            "2. L'enfant possède le problème",
            [
                "L'enfant rencontre une difficulté mais son comportement ne "
                "porte pas directement atteinte aux besoins du parent.",

                "Exemples : conflit avec un camarade, peur d'un examen, tristesse "
                "après une déception ou inquiétude concernant l'école.",

                "Stratégie privilégiée : écoute active et accompagnement de "
                "l'expression des émotions.",
            ],
        ),
        (
            "3. Le parent possède le problème",
            [
                "Le comportement de l'enfant empêche directement le parent de "
                "satisfaire un besoin.",

                "Exemples : bruit pendant le travail, objets dangereux laissés "
                "dans un passage, interruption répétée d'une conversation importante.",

                "Stratégie privilégiée : message-je permettant d'exprimer clairement "
                "le problème et le besoin du parent.",
            ],
        ),
        (
            "4. Zone sans problème",
            [
                "De nombreuses interactions quotidiennes ne correspondent à "
                "aucun problème particulier. Le parent et l'enfant peuvent "
                "simplement échanger, collaborer et partager des activités.",

                "Cette zone est importante car la relation parent-enfant ne doit "
                "pas être réduite aux conflits et aux corrections de comportement.",
            ],
        ),
        (
            "5. Conflit de besoins",
            [
                "Un conflit apparaît lorsque le besoin du parent et celui de "
                "l'enfant semblent incompatibles.",

                "Exemple : l'adolescent veut recevoir des amis tard le soir alors "
                "que le parent a besoin de dormir pour travailler le lendemain.",

                "Lorsque l'écoute et l'expression des besoins ne suffisent pas, "
                "la Method III peut être utilisée pour rechercher une solution "
                "acceptable pour les deux.",
            ],
        ),
    ],
)


# ============================================================
# PET 18 - METHOD III
# ============================================================

create_pdf(
    "PET_18_Method_III_Resolution_Conflits.pdf",
    "Method III : résolution de conflits sans perdant dans le P.E.T.",
    [
        (
            "1. Principe général",
            [
                "La Method III est une approche de résolution de conflit dans "
                "laquelle ni le parent ni l'enfant ne doivent être désignés "
                "comme le gagnant ou le perdant.",

                "L'objectif est d'identifier les besoins importants pour les "
                "deux parties puis de rechercher une solution mutuellement acceptable.",
            ],
        ),
        (
            "2. Identifier clairement le problème",
            [
                "Le parent et l'enfant décrivent la situation et cherchent à "
                "comprendre les besoins qui se trouvent derrière leurs positions.",

                "Deux personnes peuvent demander des choses opposées tout en ayant "
                "des besoins qui peuvent être satisfaits autrement.",
            ],
        ),
        (
            "3. Générer plusieurs solutions",
            [
                "Plusieurs idées peuvent être proposées sans les juger immédiatement. "
                "Cette phase permet d'éviter de réduire le conflit à seulement deux "
                "possibilités : imposer la volonté du parent ou céder à celle de l'enfant.",
            ],
        ),
        (
            "4. Évaluer les solutions",
            [
                "Les solutions proposées sont ensuite examinées ensemble. Chaque "
                "personne peut expliquer ce qui lui convient ou non.",

                "Une solution qui répond uniquement aux besoins d'une seule partie "
                "ne correspond pas à l'objectif gagnant-gagnant de la Method III.",
            ],
        ),
        (
            "5. Choisir et appliquer une solution",
            [
                "Le parent et l'enfant choisissent une solution qu'ils considèrent "
                "tous les deux comme acceptable, précisent comment elle sera appliquée "
                "puis peuvent vérifier plus tard si elle fonctionne réellement.",
            ],
        ),
        (
            "6. Exemple : temps d'écran",
            [
                "Situation : l'enfant souhaite continuer à jouer alors que le parent "
                "veut que les devoirs soient terminés.",

                "Besoins possibles de l'enfant : détente, terminer une partie, "
                "maintenir une activité avec ses amis.",

                "Besoins possibles du parent : devoirs terminés, organisation de "
                "la soirée et heure de coucher raisonnable.",

                "Une solution peut être construite ensemble, par exemple terminer "
                "la partie en cours puis consacrer une période définie aux devoirs, "
                "avec un accord clair sur la suite de la soirée.",
            ],
        ),
        (
            "7. Exemple : sortie d'un adolescent",
            [
                "L'adolescent souhaite rentrer tard pour profiter d'une sortie. "
                "Le parent souhaite garantir sa sécurité et pouvoir dormir sans "
                "rester inquiet.",

                "La discussion peut porter sur une heure de retour, un moyen de "
                "transport sécurisé, un message à envoyer en cas de changement "
                "et les conditions permettant de satisfaire au mieux les besoins "
                "des deux personnes.",
            ],
        ),
        (
            "8. Rôle de l'écoute active",
            [
                "L'écoute active et les messages-je peuvent continuer à être "
                "utilisés pendant une résolution de conflit. Ils permettent de "
                "comprendre les besoins réels avant de choisir une solution.",

                "La Method III n'est donc pas isolée des autres compétences P.E.T. ; "
                "elle s'appuie sur une communication respectueuse entre le parent "
                "et l'enfant.",
            ],
        ),
    ],
)

print()
print("Les 5 documents synthétiques PET ont été générés.")
