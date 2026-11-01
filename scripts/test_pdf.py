from pathlib import Path
from pypdf import PdfReader


PDF_FOLDER = Path("data/pet_documents")


def extract_pdf_text(pdf_path: Path) -> tuple[int, int]:
    reader = PdfReader(str(pdf_path))
    full_text = ""

    for page in reader.pages:
        text = page.extract_text() or ""
        full_text += text

    return len(reader.pages), len(full_text.strip())


def main() -> None:
    pdf_files = sorted(PDF_FOLDER.rglob("*.pdf"))

    if not pdf_files:
        print("Aucun PDF trouvé.")
        return

    print(f"{len(pdf_files)} PDF trouvés.\n")

    for pdf_path in pdf_files:
        try:
            pages, characters = extract_pdf_text(pdf_path)

            print(f"OK : {pdf_path.name}")
            print(f"Pages : {pages}")
            print(f"Caractères extraits : {characters}")

            if characters == 0:
                print("ATTENTION : aucun texte extrait.")

            print()

        except Exception as error:
            print(f"ERREUR : {pdf_path.name}")
            print(error)
            print()


if __name__ == "__main__":
    main()