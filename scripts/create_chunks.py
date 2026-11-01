from pathlib import Path
import json
import re


INPUT_FILE = Path("data/processed/pet_documents.json")
OUTPUT_FILE = Path("data/processed/pet_chunks.json")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    text = normalize_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]

        if end < len(text):
            last_separator = max(
                chunk.rfind(". "),
                chunk.rfind("? "),
                chunk.rfind("! "),
                chunk.rfind("; "),
            )

            if last_separator > chunk_size // 2:
                end = start + last_separator + 1
                chunk = text[start:end]

        chunk = chunk.strip()

        if chunk and len(chunk) >= 80:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def main() -> None:
    if not INPUT_FILE.exists():
        print(f"Fichier introuvable : {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        documents = json.load(file)

    all_chunks = []
    chunk_id = 1

    for document in documents:
        document_name = document["document_name"]

        for page in document["pages"]:
            page_number = page["page_number"]
            page_text = page["text"]

            page_chunks = split_text(page_text)

            for position, chunk_text in enumerate(page_chunks, start=1):
                all_chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "document_name": document_name,
                        "page_number": page_number,
                        "chunk_position": position,
                        "text": chunk_text,
                        "characters": len(chunk_text),
                    }
                )

                chunk_id += 1

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Fichier créé : {OUTPUT_FILE}")
    print(f"Nombre total de chunks : {len(all_chunks)}")

    if all_chunks:
        lengths = [chunk["characters"] for chunk in all_chunks]

        print(f"Taille minimale : {min(lengths)} caractères")
        print(f"Taille maximale : {max(lengths)} caractères")
        print(
            f"Taille moyenne : "
            f"{sum(lengths) / len(lengths):.1f} caractères"
        )


if __name__ == "__main__":
    main()