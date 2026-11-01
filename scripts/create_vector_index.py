from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


INPUT_FILE = Path("data/processed/pet_chunks.json")

VECTOR_FOLDER = Path("data/vector_store")
INDEX_FILE = VECTOR_FOLDER / "pet_faiss.index"
METADATA_FILE = VECTOR_FOLDER / "pet_metadata.json"
CONFIG_FILE = VECTOR_FOLDER / "pet_index_config.json"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 32


def load_chunks() -> list[dict]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Le fichier est introuvable : {INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    if not chunks:
        raise ValueError("Le fichier ne contient aucun chunk.")

    return chunks


def main() -> None:
    VECTOR_FOLDER.mkdir(parents=True, exist_ok=True)

    print("Chargement des chunks...")
    chunks = load_chunks()

    texts = [chunk["text"] for chunk in chunks]

    print(f"Nombre de chunks : {len(texts)}")
    print(f"Chargement du modèle : {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Création des embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    vector_dimension = embeddings.shape[1]

    print(f"Forme des embeddings : {embeddings.shape}")
    print(f"Dimension d'un vecteur : {vector_dimension}")

    index = faiss.IndexFlatIP(vector_dimension)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_FILE))

    metadata = []

    for chunk in chunks:
        metadata.append(
            {
                "chunk_id": chunk["chunk_id"],
                "document_name": chunk["document_name"],
                "page_number": chunk["page_number"],
                "chunk_position": chunk["chunk_position"],
                "text": chunk["text"],
                "characters": chunk["characters"],
            }
        )

    with METADATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    config = {
        "model_name": MODEL_NAME,
        "number_of_vectors": int(index.ntotal),
        "vector_dimension": int(vector_dimension),
        "similarity": "cosine_similarity_via_normalized_inner_product",
        "index_type": "IndexFlatIP",
    }

    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Indexation terminée.")
    print(f"Index FAISS créé : {INDEX_FILE}")
    print(f"Métadonnées créées : {METADATA_FILE}")
    print(f"Configuration créée : {CONFIG_FILE}")
    print(f"Vecteurs enregistrés : {index.ntotal}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("ERREUR pendant la création de l'index :")
        print(error)