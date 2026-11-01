from pathlib import Path
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.app.services.rag_service import (
    GEMINI_MODEL,
    build_sources_text,
    generate_parental_coach_response,
)

load_dotenv()

TEST_SET_FILE = Path("data/evaluation/rag_test_set_v3.json")
RESULTS_FILE = Path("data/evaluation/rag_generation_results_v3.json")

TEST_PROFILES = {
    1: {"child_age": 9, "child_gender": "garÃ§on"},
    2: {"child_age": 8, "child_gender": "fille"},
    3: {"child_age": 15, "child_gender": "garÃ§on"},
    4: {"child_age": 7, "child_gender": "non_prÃ©cisÃ©"},
    5: {"child_age": 11, "child_gender": "garÃ§on"},
    6: {"child_age": 10, "child_gender": "fille"},
    7: {"child_age": 10, "child_gender": "non_prÃ©cisÃ©"},
    8: {"child_age": 16, "child_gender": "non_prÃ©cisÃ©"},
    9: {"child_age": 9, "child_gender": "non_prÃ©cisÃ©"},
    10: {"child_age": 9, "child_gender": "non_prÃ©cisÃ©"},
}


def load_test_set() -> dict:
    if not TEST_SET_FILE.exists():
        raise FileNotFoundError(f"Jeu de test introuvable : {TEST_SET_FILE}")
    return json.loads(TEST_SET_FILE.read_text(encoding="utf-8"))


def load_existing_results() -> dict:
    if not RESULTS_FILE.exists():
        return {
            "evaluation": {
                "judge_type": "LLM-as-a-judge",
                "judge_model": GEMINI_MODEL,
                "generation_model": GEMINI_MODEL,
                "number_of_questions": 0,
            },
            "summary": {},
            "questions": [],
        }

    try:
        return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "evaluation": {
                "judge_type": "LLM-as-a-judge",
                "judge_model": GEMINI_MODEL,
                "generation_model": GEMINI_MODEL,
                "number_of_questions": 0,
            },
            "summary": {},
            "questions": [],
        }


def save_results(results: dict) -> None:
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    completed = results["questions"]

    if completed:
        mean_faithfulness = sum(
            item["faithfulness"] for item in completed
        ) / len(completed)

        mean_relevancy = sum(
            item["answer_relevancy"] for item in completed
        ) / len(completed)

        results["summary"] = {
            "faithfulness": round(mean_faithfulness, 4),
            "answer_relevancy": round(mean_relevancy, 4),
        }

    results["evaluation"]["number_of_questions"] = len(completed)

    RESULTS_FILE.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def evaluate_with_gemini(
    *,
    question: str,
    answer: str,
    sources: list[dict],
) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY est absente du fichier .env.")

    sources_text = build_sources_text(sources)

    prompt = f"""
Tu es un Ã©valuateur indÃ©pendant d'un systÃ¨me RAG de coaching parental
basÃ© sur des documents P.E.T. (Parent Effectiveness Training).

Ã‰value deux dimensions sÃ©parÃ©ment.

1. FAITHFULNESS
Mesure dans quelle mesure les affirmations, recommandations et
explications de la rÃ©ponse sont soutenues par les SOURCES PET fournies.
- 1.0 = entiÃ¨rement soutenu.
- 0.5 = partiellement soutenu.
- 0.0 = largement inventÃ©, contradictoire ou non soutenu.
Une question de clarification peut obtenir une bonne note si elle
n'introduit pas de faits ou recommandations non soutenus.

2. ANSWER RELEVANCY
Mesure dans quelle mesure la rÃ©ponse rÃ©pond directement et utilement Ã 
la situation du parent.
- 1.0 = trÃ¨s directement liÃ©e au problÃ¨me.
- 0.5 = partiellement utile mais vague ou incomplÃ¨te.
- 0.0 = hors sujet.

IMPORTANT
- Ã‰value uniquement Ã  partir de la question, des sources et de la rÃ©ponse.
- Ne rÃ©compense pas une rÃ©ponse simplement parce qu'elle semble plausible.
- Les deux notes doivent Ãªtre comprises entre 0 et 1.
- Donne une justification courte pour chaque note.
- Retourne uniquement du JSON valide.

QUESTION DU PARENT

{question}

SOURCES PET

{sources_text}

RÃ‰PONSE DU COACH IA

{answer}

FORMAT JSON

{{
    "faithfulness": 0.0,
    "answer_relevancy": 0.0,
    "faithfulness_reason": "raison courte",
    "answer_relevancy_reason": "raison courte"
}}
""".strip()

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "faithfulness": {"type": "number"},
                    "answer_relevancy": {"type": "number"},
                    "faithfulness_reason": {"type": "string"},
                    "answer_relevancy_reason": {"type": "string"},
                },
                "required": [
                    "faithfulness",
                    "answer_relevancy",
                    "faithfulness_reason",
                    "answer_relevancy_reason",
                ],
            },
        ),
    )

    if not response.text:
        raise ValueError("Gemini Ã©valuateur n'a retournÃ© aucune rÃ©ponse.")

    evaluation = json.loads(response.text)
    evaluation["faithfulness"] = clamp_score(evaluation["faithfulness"])
    evaluation["answer_relevancy"] = clamp_score(
        evaluation["answer_relevancy"]
    )
    return evaluation


def evaluate_generation() -> dict:
    test_set = load_test_set()
    results = load_existing_results()

    completed_ids = {
        item["id"] for item in results["questions"]
    }

    print()
    print("=" * 62)
    print("Ã‰VALUATION DE LA GÃ‰NÃ‰RATION RAG AVEC GEMINI")
    print("=" * 62)
    print()
    print("Les rÃ©sultats sont sauvegardÃ©s aprÃ¨s chaque question.")
    print("En cas de quota, relance simplement la mÃªme commande.")
    print()

    for item in test_set["questions"]:
        question_id = item["id"]

        if question_id in completed_ids:
            print(f"Question {question_id} dÃ©jÃ  Ã©valuÃ©e : ignorÃ©e.")
            continue

        profile = TEST_PROFILES[question_id]
        question = item["question"]

        print("-" * 62)
        print(f"Question {question_id}")
        print(question)
        print()
        print("1/2 GÃ©nÃ©ration de la rÃ©ponse...")

        generated = generate_parental_coach_response(
            child_age=profile["child_age"],
            child_gender=profile["child_gender"],
            family_context=(
                "Contexte familial non prÃ©cisÃ© pour ce scÃ©nario d'Ã©valuation."
            ),
            additional_information=None,
            trigger_message=question,
            messages=[],
        )

        answer = generated["content"]
        sources = generated["sources"]

        print("   RÃ©ponse gÃ©nÃ©rÃ©e.")
        print("2/2 Ã‰valuation par Gemini...")

        evaluation = evaluate_with_gemini(
            question=question,
            answer=answer,
            sources=sources,
        )

        result = {
            "id": question_id,
            "question": question,
            "profile": profile,
            "message_type": generated["message_type"],
            "answer": answer,
            "source_chunk_ids": [
                source["chunk_id"] for source in sources
            ],
            "faithfulness": round(evaluation["faithfulness"], 4),
            "answer_relevancy": round(
                evaluation["answer_relevancy"], 4
            ),
            "faithfulness_reason": evaluation["faithfulness_reason"],
            "answer_relevancy_reason": evaluation[
                "answer_relevancy_reason"
            ],
        }

        results["questions"].append(result)
        save_results(results)

        print(f"   Faithfulness     : {result['faithfulness']:.2f}")
        print(f"   Answer Relevancy : {result['answer_relevancy']:.2f}")
        print()

        time.sleep(1)

    results["questions"] = sorted(
        results["questions"],
        key=lambda item: item["id"],
    )

    save_results(results)

    print()
    print("=" * 62)
    print("MOYENNES")
    print("=" * 62)

    if results["questions"]:
        print(
            f"Faithfulness     : "
            f"{results['summary']['faithfulness']:.2f}"
        )
        print(
            f"Answer Relevancy : "
            f"{results['summary']['answer_relevancy']:.2f}"
        )
        print()

    print(f"RÃ©sultats enregistrÃ©s dans : {RESULTS_FILE}")
    print()

    return results


if __name__ == "__main__":
    evaluate_generation()
