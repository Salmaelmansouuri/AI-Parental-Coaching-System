from backend.app.services.aco_service import ACOService


interventions = [
    "active_listening",
    "i_message",
    "problem_ownership",
    "method_iii",
]


# Qualité individuelle des interventions.
scores = {
    "active_listening": 4.8,
    "i_message": 4.0,
    "problem_ownership": 4.4,
    "method_iii": 4.6,
}


# Scores temporaires uniquement pour tester
# si l'ACO prend bien l'ordre en compte.
transition_scores = {

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


aco = ACOService(
    n_ants=20,
    n_iterations=30,
    alpha=1.0,
    beta=2.0,
    evaporation_rate=0.3,
    random_seed=42,
)


result = aco.optimize(
    interventions=interventions,
    intervention_scores=scores,
    transition_scores=transition_scores,
    path_length=3,
)


print("\n=== RESULTAT ACO AVEC ORDRE ===")

print(
    "Meilleur parcours :",
    " -> ".join(result["best_path"])
)

print(
    "Score global :",
    result["best_score"]
)

print("\nPhéromones principales :")

sorted_pheromones = sorted(
    result["pheromones"].items(),
    key=lambda item: item[1],
    reverse=True,
)

for (source, target), value in sorted_pheromones[:8]:

    print(
        f"{source} -> {target}: "
        f"{value:.2f}"
    )