from pathlib import Path
import json
import re

from pypdf import PdfReader


PDF_FOLDER = Path("data/pet_documents")
OUTPUT_FOLDER = Path("data/processed")
OUTPUT_FILE = OUTPUT_FOLDER / "pet_documents.json"


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_pdf(pdf_path: Path) -> dict:
    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned_text = clean_text(raw_text)

        pages.append(
            {
                "page_number": page_number,
                "text": cleaned_text,
                "characters": len(cleaned_text),
            }
        )

    return {
        "document_name": pdf_path.name,
        "relative_path": str(pdf_path),
        "number_of_pages": len(reader.pages),
        "pages": pages,
    }


def main() -> None:
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(PDF_FOLDER.rglob("*.pdf"))

    if not pdf_files:
        print("Aucun PDF trouvé.")
        return

    documents = []

    for pdf_path in pdf_files:
        try:
            document = extract_pdf(pdf_path)
            documents.append(document)

            total_characters = sum(
                page["characters"] for page in document["pages"]
            )

            print(
                f"OK : {pdf_path.name} | "
                f"{document['number_of_pages']} pages | "
                f"{total_characters} caractères"
            )

        except Exception as error:
            print(f"ERREUR : {pdf_path.name}")
            print(error)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Fichier créé : {OUTPUT_FILE}")
    print(f"Documents enregistrés : {len(documents)}")


if __name__ == "__main__":
    main()