# -*- coding: utf-8 -*-

from pathlib import Path
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import html
import re

INPUT = Path(
    "data/incoming_professor_docs/P01_Gordon_PET_Official.html"
)

OUTPUT = Path(
    "data/pet_documents/01_principes_pet/"
    "PET_19_Gordon_Official_PET_Page.pdf"
)

raw_html = INPUT.read_text(
    encoding="utf-8",
    errors="ignore"
)

soup = BeautifulSoup(raw_html, "html.parser")

# Supprimer les éléments non utiles au contenu
for tag in soup([
    "script",
    "style",
    "noscript",
    "svg",
    "form",
    "nav",
    "footer",
    "header"
]):
    tag.decompose()

# Privilégier le contenu principal si disponible
main = (
    soup.find("main")
    or soup.find("article")
    or soup.body
    or soup
)

text = main.get_text("\n")

lines = []

for line in text.splitlines():
    line = html.unescape(line)
    line = re.sub(r"\s+", " ", line).strip()

    if len(line) < 3:
        continue

    lines.append(line)

# Éliminer les lignes répétées successives
clean_lines = []

EXCLUDED_PHRASES = [
    "did you know that we offer p.e.t. online",
    "visit our p.e.t. events page",
    "current schedule",
    "parenting channel on youtube",
    "youtube",
    "how do you decide which one is right for you",
    "here is a comparison of the most well-known programs",
]

for line in lines:
    lower_line = line.lower()

    if any(phrase in lower_line for phrase in EXCLUDED_PHRASES):
        continue

    if not clean_lines or clean_lines[-1] != line:
        clean_lines.append(line)

    text = "\n".join(clean_lines)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(
    TTFont("Arial", r"C:\Windows\Fonts\arial.ttf")
)

pdfmetrics.registerFont(
    TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf")
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitlePET",
    parent=styles["Title"],
    fontName="Arial-Bold",
    fontSize=17,
    leading=21,
    spaceAfter=15,
)

body_style = ParagraphStyle(
    "BodyPET",
    parent=styles["BodyText"],
    fontName="Arial",
    fontSize=10,
    leading=14,
    spaceAfter=7,
)

source_style = ParagraphStyle(
    "SourcePET",
    parent=body_style,
    fontSize=9,
)

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=2 * cm,
    rightMargin=2 * cm,
    topMargin=1.8 * cm,
    bottomMargin=1.8 * cm,
)

story = []

story.append(
    Paragraph(
        "Parent Effectiveness Training (P.E.T.) — Gordon Training International",
        title_style,
    )
)

story.append(
    Paragraph(
        "Source : Gordon Training International — page officielle du programme "
        "Parent Effectiveness Training (P.E.T.).",
        source_style,
    )
)

story.append(Spacer(1, 10))

for line in clean_lines:
    safe_line = (
        line.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    story.append(
        Paragraph(safe_line, body_style)
    )

doc.build(story)

print("PDF créé :", OUTPUT)
print("Nombre de lignes conservées :", len(clean_lines))
print("Nombre de caractères :", len(text))
print()
print("APERÇU :")
print(text[:1500])

