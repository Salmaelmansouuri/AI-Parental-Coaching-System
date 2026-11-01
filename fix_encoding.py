from pathlib import Path

files = [
    Path("backend/app/templates/coach_dashboard.html"),
    Path("backend/app/templates/coach_path_detail.html"),
    Path("backend/app/templates/login.html"),
    Path("backend/app/templates/parent_dashboard.html"),
    Path("backend/app/templates/path_detail.html"),
]

for path in files:
    text = path.read_text(encoding="utf-8")
    new_lines = []

    for line in text.splitlines(keepends=True):
        if any(mark in line for mark in ["Ã", "Â", "â"]):
            try:
                line = line.encode("cp1252").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass

        new_lines.append(line)

    path.write_text("".join(new_lines), encoding="utf-8")
    print("Corrigé :", path)

print("TERMINÉ")
