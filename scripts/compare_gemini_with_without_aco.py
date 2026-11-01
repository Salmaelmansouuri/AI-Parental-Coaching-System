import json

from backend.app.services.rag_service import (
    generate_parental_coach_response,
)


COMMON_ARGS = {
    "child_age": 10,
    "child_gender": "Garçon",
    "family_context": None,
    "additional_information": None,
    "trigger_message": (
        "Mon fils de 10 ans se met en colère "
        "lorsque je lui demande d'arrêter la tablette."
    ),
    "messages": [],
}


results = {}


print("\n=== GENERATION SANS ACO ===")

without_aco = generate_parental_coach_response(
    **COMMON_ARGS,
    use_aco=False,
)

results["without_aco"] = without_aco

print(without_aco["content"])


print("\n" + "=" * 70)


print("\n=== GENERATION AVEC ACO ===")
try:
    without_aco = generate_parental_coach_response(
        **COMMON_ARGS,
        use_aco=False,
    )

    results["without_aco"] = without_aco

    print(without_aco["content"])

except Exception as e:
    print(
        "Sans ACO impossible :",
        e
    )
    
try:

    with_aco = generate_parental_coach_response(
        **COMMON_ARGS,
        use_aco=True,
    )

    results["with_aco"] = with_aco

    print(with_aco["content"])

    print("\nParcours ACO :")

    print(
        " -> ".join(
            with_aco["aco"]["path"]
        )
    )

except Exception as e:

    print(
        "ACO génération impossible pour le moment :",
        e,
    )


with open(
    "data/aco_gemini_comparison.json",
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2,
    )


print(
    "\nRésultat sauvegardé dans "
    "data/aco_gemini_comparison.json"
)