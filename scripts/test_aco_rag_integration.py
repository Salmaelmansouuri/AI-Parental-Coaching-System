from backend.app.services.rag_service import build_aco_guidance


question = (
    "Mon fils de 10 ans se met en colère "
    "lorsque je lui demande d'arrêter la tablette."
)

result = build_aco_guidance(question)

print("\n=== TEST ACO DANS LE RAG ===")

print(
    "Parcours choisi :",
    " -> ".join(result["path"])
)

print(
    "Score ACO :",
    result["score"]
)

print("\nScores des interventions :")

for name, score in result["intervention_scores"].items():
    print(
        f"{name}: {score:.3f}"
    )