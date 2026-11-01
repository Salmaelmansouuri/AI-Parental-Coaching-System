from pathlib import Path
import re

templates = [
    Path("backend/app/templates/coach_dashboard.html"),
    Path("backend/app/templates/coach_path_detail.html"),
    Path("backend/app/templates/parent_dashboard.html"),
    Path("backend/app/templates/path_detail.html"),
    Path("backend/app/templates/login.html"),
]

logo = '<img src="/static/images/logo.png" alt="Logo Coach parental IA">'

for path in templates:
    text = path.read_text(encoding="utf-8")

    text = re.sub(
        r'<div class="chat-brand-logo">\s*(?:CP|<img[^>]*>)\s*</div>',
        f'<div class="chat-brand-logo">{logo}</div>',
        text
    )

    text = re.sub(
        r'<div class="modern-login-logo">\s*(?:CP|<img[^>]*>)\s*</div>',
        f'<div class="modern-login-logo">{logo}</div>',
        text
    )

    # Force le navigateur à recharger le CSS
    text = re.sub(
        r'href="/static/css/style\.css(?:\?v=\d+)?"',
        'href="/static/css/style.css?v=10"',
        text
    )

    path.write_text(text, encoding="utf-8")

css_path = Path("backend/app/static/css/style.css")
css = css_path.read_text(encoding="utf-8")

marker = "/* ===== CORRECTION FINALE LOGO ===== */"

if marker not in css:
    css += r'''

/* ===== CORRECTION FINALE LOGO ===== */

.chat-brand-logo {
    width: 56px !important;
    height: 56px !important;
    min-width: 56px !important;
    max-width: 56px !important;
    min-height: 56px !important;
    max-height: 56px !important;
    flex: 0 0 56px !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    border-radius: 14px !important;
    background: #ffffff !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
}

.modern-login-logo {
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    max-width: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    flex: 0 0 46px !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    border-radius: 14px !important;
    background: #ffffff !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
}

.chat-brand-logo img,
.modern-login-logo img,
img[src="/static/images/logo.png"] {
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    min-width: 0 !important;
    min-height: 0 !important;
    object-fit: cover !important;
    display: block !important;
    position: static !important;
    inset: auto !important;
    transform: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
'''

css_path.write_text(css, encoding="utf-8")

print("Logo corrigé.")
