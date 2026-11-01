from pathlib import Path

path = Path("backend/app/static/css/style.css")
css = path.read_text(encoding="utf-8")

marker = "/* ===== MISE EN PAGE ESTIMATION ML ===== */"

if marker not in css:
    css += """

/* ===== MISE EN PAGE ESTIMATION ML ===== */

#ml-prediction-box {
    overflow: hidden !important;
}

/* En-tête Machine Learning */
#ml-prediction-box > div:first-child {
    padding: 22px 22px 16px !important;
    margin: 0 !important;
}

#ml-prediction-box .coach-simple-eyebrow {
    margin: 0 0 6px 0 !important;
}

#ml-prediction-box h3 {
    margin: 0 0 6px 0 !important;
}

#ml-prediction-box > div:first-child p:last-child {
    margin: 0 !important;
}

/* Lignes des prédictions */
#ml-prediction-content .simple-stat-line {
    padding-left: 22px !important;
    padding-right: 22px !important;
}

/* Ligne KNN regression / voisins / historique */
#ml-prediction-content > p:last-child {
    margin: 0 !important;
    padding: 14px 22px 16px !important;
    line-height: 1.5 !important;
}
"""

    path.write_text(css, encoding="utf-8")
    print("Mise en page ML corrigée.")
else:
    print("Correction ML déjà présente.")
