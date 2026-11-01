import random
from typing import Dict, List, Tuple


class ACOService:

    def __init__(
        self,
        n_ants: int = 20,
        n_iterations: int = 30,
        alpha: float = 1.0,
        beta: float = 2.0,
        evaporation_rate: float = 0.3,
        random_seed: int = 42,
    ):
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.random_seed = random_seed

    def optimize(
        self,
        interventions: List[str],
        intervention_scores: Dict[str, float],
        transition_scores: Dict[Tuple[str, str], float],
        path_length: int = 3,
    ) -> dict:

        if not interventions:
            return {
                "best_path": [],
                "best_score": 0.0,
            }

        random.seed(self.random_seed)

        # Phéromones sur les transitions dirigées.
        pheromones = {}

        for source in interventions:
            for target in interventions:
                if source != target:
                    pheromones[(source, target)] = 1.0

        # Phéromones pour le choix de la première intervention.
        start_pheromones = {
            intervention: 1.0
            for intervention in interventions
        }

        best_path = []
        best_score = float("-inf")

        for _ in range(self.n_iterations):

            iteration_results = []

            for _ in range(self.n_ants):

                available = interventions.copy()
                path = []

                # -----------------------------
                # Choix de la première intervention
                # -----------------------------
                start_weights = []

                for intervention in available:

                    heuristic = max(
                        intervention_scores.get(intervention, 0.01),
                        0.01,
                    )

                    weight = (
                        start_pheromones[intervention] ** self.alpha
                    ) * (
                        heuristic ** self.beta
                    )

                    start_weights.append(weight)

                first = random.choices(
                    available,
                    weights=start_weights,
                    k=1,
                )[0]

                path.append(first)
                available.remove(first)

                # -----------------------------
                # Construction du reste du parcours
                # -----------------------------
                while (
                    len(path) < path_length
                    and available
                ):

                    current = path[-1]

                    weights = []

                    for candidate in available:

                        node_score = intervention_scores.get(
                            candidate,
                            0.01,
                        )

                        transition_score = transition_scores.get(
                            (current, candidate),
                            3.0,
                        )

                        # Qualité immédiate de la transition.
                        heuristic = (
                            0.6 * node_score
                            + 0.4 * transition_score
                        )

                        heuristic = max(heuristic, 0.01)

                        pheromone = pheromones[
                            (current, candidate)
                        ]

                        weight = (
                            pheromone ** self.alpha
                        ) * (
                            heuristic ** self.beta
                        )

                        weights.append(weight)

                    selected = random.choices(
                        available,
                        weights=weights,
                        k=1,
                    )[0]

                    path.append(selected)
                    available.remove(selected)

                # -----------------------------
                # Score du parcours complet
                # -----------------------------
                node_scores = [
                    intervention_scores.get(item, 0.0)
                    for item in path
                ]

                mean_node_score = (
                    sum(node_scores) / len(node_scores)
                )

                path_transition_scores = []

                for i in range(len(path) - 1):
                    transition = (
                        path[i],
                        path[i + 1],
                    )

                    path_transition_scores.append(
                        transition_scores.get(
                            transition,
                            3.0,
                        )
                    )

                if path_transition_scores:
                    mean_transition_score = (
                        sum(path_transition_scores)
                        / len(path_transition_scores)
                    )
                else:
                    mean_transition_score = 0.0

                # 60 % qualité individuelle
                # 40 % qualité de l'enchaînement
                score = (
                    0.6 * mean_node_score
                    + 0.4 * mean_transition_score
                )

                iteration_results.append(
                    (path, score)
                )

                if score > best_score:
                    best_score = score
                    best_path = path.copy()

            # -----------------------------
            # Évaporation
            # -----------------------------
            for edge in pheromones:
                pheromones[edge] *= (
                    1 - self.evaporation_rate
                )

            for intervention in start_pheromones:
                start_pheromones[intervention] *= (
                    1 - self.evaporation_rate
                )

            # -----------------------------
            # Renforcement
            # -----------------------------
            for path, score in iteration_results:

                if score <= 0:
                    continue

                start_pheromones[path[0]] += score

                for i in range(len(path) - 1):
                    edge = (
                        path[i],
                        path[i + 1],
                    )

                    pheromones[edge] += score

        return {
            "best_path": best_path,
            "best_score": round(best_score, 4),
            "pheromones": pheromones,
            "start_pheromones": start_pheromones,
        }