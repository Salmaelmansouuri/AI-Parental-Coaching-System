from functools import lru_cache
from pathlib import Path
import json
import os
import faiss
import numpy as np
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer
from backend.app.services.aco_service import ACOService


load_dotenv()


VECTOR_FOLDER = Path("data/vector_store")
INDEX_FILE = VECTOR_FOLDER / "pet_faiss.index"
METADATA_FILE = VECTOR_FOLDER / "pet_metadata.json"
CONFIG_FILE = VECTOR_FOLDER / "pet_index_config.json"

GEMINI_MODEL = "gemini-3.5-flash-lite"
TOP_K = 4

ACO_INTERVENTIONS = {
    "active_listening": (
        "Ã‰coute active : comprendre les Ã©motions de l'enfant, "
        "reformuler ce qu'il ressent et l'aider Ã  exprimer son problÃ¨me."
    ),
    "i_message": (
        "Message-je : le parent exprime son besoin, son ressenti "
        "et l'effet du comportement sans accuser l'enfant."
    ),
    "problem_ownership": (
        "PropriÃ©tÃ© du problÃ¨me : dÃ©terminer si le problÃ¨me appartient "
        "au parent ou Ã  l'enfant afin de choisir une intervention adaptÃ©e."
    ),
    "method_iii": (
        "MÃ©thode III : rechercher avec l'enfant une solution "
        "gagnant-gagnant lorsqu'il existe un conflit de besoins."
    ),
}


ACO_TRANSITION_SCORES = {
    ("problem_ownership", "active_listening"): 4.9,
    ("active_listening", "method_iii"): 4.8,

    ("problem_ownership", "i_message"): 4.4,
    ("i_message", "method_iii"): 4.5,

    ("active_listening", "i_message"): 4.0,
    ("i_message", "active_listening"): 3.6,

    ("method_iii", "active_listening"): 3.2,
    ("method_iii", "problem_ownership"): 2.8,

    ("active_listening", "problem_ownership"): 3.5,
    ("i_message", "problem_ownership"): 3.4,

    ("problem_ownership", "method_iii"): 4.3,
    ("method_iii", "i_message"): 3.4,
}

QUERY_EXPANSIONS = {
    "conflit": (
        "conflict resolution Method III no-lose method "
        "mutually acceptable solution"
    ),
    "besoins opposÃ©s": (
        "conflicting needs parent child Method III "
        "no-lose conflict resolution"
    ),
    "Ã©coute active": (
        "active listening reflect feelings empathy"
    ),
    "colÃ¨re": (
        "anger strong feelings active listening empathy"
    ),
    "tablette": (
        "screen time conflict parent child active listening "
        "Method III no-lose conflict resolution"
    ),
}


def expand_query(question: str) -> str:
    normalized_question = question.lower()
    expansions = []

    for keyword, expansion in QUERY_EXPANSIONS.items():
        if keyword in normalized_question:
            expansions.append(expansion)

    if not expansions:
        return question

    return question + " " + " ".join(expansions)


@lru_cache
def load_rag_resources():
    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Index FAISS introuvable : {INDEX_FILE}"
        )

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"MÃ©tadonnÃ©es introuvables : {METADATA_FILE}"
        )

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration introuvable : {CONFIG_FILE}"
        )

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    with CONFIG_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = json.load(file)

    embedding_model = SentenceTransformer(
        config["model_name"]
    )

    return (
        index,
        metadata,
        embedding_model,
    )


def retrieve_pet_sources(
    question: str,
    top_k: int = TOP_K,
) -> list[dict]:
    (
        index,
        metadata,
        embedding_model,
    ) = load_rag_resources()

    expanded_question = expand_query(
        question
    )

    embedding = embedding_model.encode(
        [expanded_question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embedding = np.asarray(
        embedding,
        dtype="float32",
    )

    candidate_k = min(
        index.ntotal,
        max(top_k * 10, 40),
    )

    scores, positions = index.search(
        embedding,
        candidate_k,
    )

    results = []
    question_lower = question.lower()

    autism_context = any(
        keyword in question_lower
        for keyword in {
            "autisme",
            "autiste",
            "asperger",
            "trouble du spectre autistique",
            "tsa",
        }
    )

    for score, position in zip(
        scores[0],
        positions[0],
    ):
        if position < 0:
            continue

        chunk = metadata[position]

        document_name = (
            chunk["document_name"].lower()
        )

        if (
            "autism" in document_name
            and not autism_context
        ):
            continue

        results.append(
            {
                "score": float(score),
                "document_name": chunk["document_name"],
                "page_number": chunk["page_number"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
            }
        )

        if len(results) >= top_k:
            break

    return results

def build_sources_text(
    sources: list[dict],
) -> str:
    blocks = []

    for number, source in enumerate(
        sources,
        start=1,
    ):
        blocks.append(
            (
                f"SOURCE {number}\n"
                f"Document : "
                f"{source['document_name']}\n"
                f"Page : "
                f"{source['page_number']}\n"
                f"Score : "
                f"{source['score']:.4f}\n"
                f"Extrait :\n"
                f"{source['text']}"
            )
        )

    return "\n\n".join(blocks)


def build_conversation_text(
    messages: list[dict],
) -> str:
    lines = []

    for message in messages:
        lines.append(
            f"{message['sender']} "
            f"({message['message_type']}) : "
            f"{message['content']}"
        )

    return "\n".join(lines)

def build_aco_guidance(
    question: str,
) -> dict:
    (
        _,
        _,
        embedding_model,
    ) = load_rag_resources()

    intervention_names = list(
        ACO_INTERVENTIONS.keys()
    )

    intervention_texts = [
        ACO_INTERVENTIONS[name]
        for name in intervention_names
    ]

    intervention_embeddings = (
        embedding_model.encode(
            intervention_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    )

    question_embedding = (
        embedding_model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]
    )

    similarities = np.dot(
        intervention_embeddings,
        question_embedding,
    )

    intervention_scores = {}

    for name, similarity in zip(
        intervention_names,
        similarities,
    ):
        similarity = float(similarity)

        semantic_score = (
            1.0
            + 4.0
            * max(
                0.0,
                min(1.0, similarity),
            )
        )

        intervention_scores[name] = (
            semantic_score
        )

    aco = ACOService(
        n_ants=20,
        n_iterations=30,
        alpha=1.0,
        beta=2.0,
        evaporation_rate=0.3,
        random_seed=42,
    )

    result = aco.optimize(
        interventions=intervention_names,
        intervention_scores=intervention_scores,
        transition_scores=ACO_TRANSITION_SCORES,
        path_length=3,
    )

    return {
        "path": result["best_path"],
        "score": result["best_score"],
        "intervention_scores": (
            intervention_scores
        ),
    }

def generate_parental_coach_response(
    *,
    child_age: int,
    child_gender: str,
    family_context: str | None,
    additional_information: str | None,
    trigger_message: str,
    messages: list[dict],
    use_aco: bool = False,
) -> dict:
    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY est absente "
            "du fichier .env."
        )
    latest_parent_message = None

    for message in reversed(messages):
        if message["sender"] == "parent":
            latest_parent_message = message["content"]
            break

    if (
        latest_parent_message
        and latest_parent_message.strip()
        != trigger_message.strip()
    ):
        search_question = (
            trigger_message
            + " "
            + latest_parent_message
        )
    else:
        search_question = trigger_message

    sources = retrieve_pet_sources(
        search_question
    )

    sources_text = build_sources_text(
        sources
    )

    conversation_text = (
        build_conversation_text(
            messages
        )
    )

    aco_result = None
    aco_guidance_text = (
        "ACO non activÃ© pour cette gÃ©nÃ©ration."
    )

    intervention_rule = (
        "Pour une intervention, explique une seule action principale."
    )

    if use_aco:
        aco_result = build_aco_guidance(
            search_question
        )

        path = aco_result["path"]

        path_descriptions = [
            (
                f"{index}. {name} : "
                f"{ACO_INTERVENTIONS[name]}"
            )
            for index, name in enumerate(
                path,
                start=1,
            )
        ]

        aco_guidance_text = "\n".join(
            path_descriptions
        )

        intervention_rule = (
            "Pour une intervention, suis l'ordre du parcours "
            "de coaching proposÃ© ci-dessous. PrÃ©sente les Ã©tapes "
            "de maniÃ¨re naturelle et concise, sans mentionner ACO "
            "ni les noms techniques des stratÃ©gies au parent."
        )

    prompt = f"""
Tu es un assistant de coaching parental basÃ© sur la mÃ©thode
Parent Effectiveness Training (P.E.T.).

Tu dois dÃ©cider si le contexte est suffisant pour proposer une
intervention ou s'il faut d'abord poser des questions de clarification.

RÃˆGLES OBLIGATOIRES

1. Utilise uniquement les informations du parcours et les sources PET.
2. Ne pose aucun diagnostic mÃ©dical ou psychologique.
3. Ne conseille aucune violence, humiliation, menace ou punition.
4. Adapte la rÃ©ponse Ã  l'Ã¢ge de l'enfant.
5. Ne pose pas plus de trois questions de clarification.
6. Si des informations essentielles manquent, choisis :
   "question_clarification".
7. Si le contexte est suffisant, choisis :
   "intervention".
8. {intervention_rule}
9. N'affiche aucune rÃ©fÃ©rence, aucun nom de document et aucun numÃ©ro de page dans le contenu de la rÃ©ponse. Les sources sont gÃ©rÃ©es sÃ©parÃ©ment par l'application.
10. RÃ©ponds uniquement avec un objet JSON valide.

PROFIL DE L'ENFANT

Ã‚ge : {child_age}
Sexe : {child_gender}
Contexte familial : {family_context or "Non renseignÃ©"}
Informations complÃ©mentaires :
{additional_information or "Aucune"}

DÃ‰CLENCHEUR

{trigger_message}

HISTORIQUE DU PARCOURS

{conversation_text}

PARCOURS DE COACHING PROPOSÃ‰ PAR L'OPTIMISATION

{aco_guidance_text}

SOURCES PET

{sources_text}

FORMAT JSON OBLIGATOIRE

{{
    "message_type": "question_clarification ou intervention",
    "content": "RÃ©ponse complÃ¨te en franÃ§ais"
}}
""".strip()

    client = genai.Client(
        api_key=api_key
    )

    response = None

    for attempt in range(3):

        try:

            response = (
                client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema={
                            "type": "object",
                            "properties": {
                                "message_type": {
                                    "type": "string",
                                    "enum": [
                                        "question_clarification",
                                        "intervention",
                                    ],
                                },
                                "content": {
                                    "type": "string",
                                },
                            },
                            "required": [
                                "message_type",
                                "content",
                            ],
                        },
                    ),
                )
            )

            break

        except Exception as e:

            error_text = str(e)

            print(
                f"Tentative Gemini {attempt + 1}/3 Ã©chouÃ©e : {error_text}"
            )

            # 429 = quota dÃ©passÃ© :
            # inutile de rÃ©essayer immÃ©diatement
            if "429" in error_text:
                raise

            # 503 = indisponibilitÃ© temporaire :
            # on peut rÃ©essayer
            if "503" in error_text:
                time.sleep(15)
                continue

            # Autre erreur : on arrÃªte
            raise

    if response is None:
        raise RuntimeError(
            "Gemini indisponible aprÃ¨s plusieurs tentatives."
        )

    if not response.text:
        raise ValueError(
            "Gemini n'a retournÃ© "
            "aucune rÃ©ponse."
        )

    parsed_response = json.loads(
        response.text
    )

    if (
        parsed_response.get(
            "message_type"
        )
        not in {
            "question_clarification",
            "intervention",
        }
    ):
        raise ValueError(
            "Type de message Gemini invalide."
        )

    if not parsed_response.get(
        "content"
    ):
        raise ValueError(
            "La rÃ©ponse Gemini "
            "ne contient aucun contenu."
        )

    parsed_response["sources"] = (
        sources
    )
    
    parsed_response["aco_used"] = use_aco

    if aco_result is not None:
        parsed_response["aco"] = {
            "path": aco_result["path"],
            "score": aco_result["score"],
        }
    else:
        parsed_response["aco"] = None

    return parsed_response
