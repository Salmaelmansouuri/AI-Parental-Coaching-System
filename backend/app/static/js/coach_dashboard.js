const token = localStorage.getItem("access_token");
const storedUser = localStorage.getItem("current_user");

let currentUser = null;

try {
    currentUser = storedUser
        ? JSON.parse(storedUser)
        : null;
} catch {
    currentUser = null;
}


function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("current_user");

    window.location.href = "/web/login";
}


function protectCoachPage() {
    if (!token || !currentUser) {
        window.location.href = "/web/login";
        return false;
    }

    if (currentUser.role !== "coach") {
        window.location.href = "/web/parent";
        return false;
    }

    return true;
}


async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Authorization": `Bearer ${token}`,
            "Accept": "application/json",
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    if (response.status === 401) {
        logout();
        throw new Error("Session expirée.");
    }

    const contentType =
        response.headers.get("content-type") || "";

    let data = null;

    if (contentType.includes("application/json")) {
        data = await response.json();
    }

    if (!response.ok) {
        let errorMessage = "Une erreur est survenue.";

        if (typeof data?.detail === "string") {
            errorMessage = data.detail;
        }

        throw new Error(errorMessage);
    }

    return data;
}


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function displayCoachInformation() {
    const fullName = [
        currentUser.first_name,
        currentUser.last_name
    ]
        .filter(Boolean)
        .join(" ");

    const firstName =
        currentUser.first_name || "Coach";

    document.getElementById(
        "coach-name"
    ).textContent = fullName || "Coach";

    document.getElementById(
        "coach-email"
    ).textContent = currentUser.email || "";

    document.getElementById(
        "welcome-coach-name"
    ).textContent = firstName;

    document.getElementById(
        "coach-avatar"
    ).textContent =
        firstName.charAt(0).toUpperCase();
}


function showCoachView(viewName) {
    const target =
        document.getElementById(
            `${viewName}-view`
        );

    if (!target) {
        return;
    }

    document
        .querySelectorAll(".coach-view")
        .forEach((view) => {
            view.classList.remove("active");
        });

    target.classList.add("active");

    document
        .querySelectorAll(
            ".chat-sidebar-link[data-coach-view]"
        )
        .forEach((button) => {
            button.classList.toggle(
                "active",
                button.dataset.coachView === viewName
            );
        });
}


async function loadCoachStatistics() {
    const statistics = await apiRequest(
        "/statistics/coach"
    );

    document.getElementById(
        "coach-pending-paths"
    ).textContent =
        statistics.pending_paths;

    document.getElementById(
        "coach-evaluated-paths"
    ).textContent =
        statistics.evaluated_paths;

    document.getElementById(
        "coach-validated-paths"
    ).textContent =
        statistics.validated_paths;

    document.getElementById(
        "coach-average-score"
    ).textContent =
        Number(
            statistics.average_global_score
        ).toFixed(1);
            document.getElementById(
        "coach-rag-precision"
    ).textContent =
        Number(
            statistics.rag_precision_at_4 ?? 0
        ).toFixed(2);

    document.getElementById(
        "coach-rag-recall"
    ).textContent =
        Number(
            statistics.rag_recall_at_4_pool ?? 0
        ).toFixed(2);

    document.getElementById(
        "coach-rag-mrr"
    ).textContent =
        Number(
            statistics.rag_mrr ?? 0
        ).toFixed(2);

    document.getElementById(
        "coach-rag-faithfulness"
    ).textContent =
        Number(
            statistics.rag_faithfulness ?? 0
        ).toFixed(2);

    document.getElementById(
        "coach-rag-answer-relevancy"
    ).textContent =
        Number(
            statistics.rag_answer_relevancy ?? 0
        ).toFixed(2);
            document.getElementById(
        "coach-knn-samples"
    ).textContent =
        statistics.knn_samples ?? 0;


    document.getElementById(
        "coach-knn-warning-samples"
    ).textContent =
        statistics.knn_samples ?? 0;


    document.getElementById(
        "coach-knn-mae-global"
    ).textContent =
        Number(
            statistics.knn_mae_global ?? 0
        ).toFixed(2);


    document.getElementById(
        "coach-knn-rmse-global"
    ).textContent =
        Number(
            statistics.knn_rmse_global ?? 0
        ).toFixed(2);


    document.getElementById(
        "coach-knn-mae-relevance"
    ).textContent =
        Number(
            statistics.knn_mae_relevance ?? 0
        ).toFixed(2);


    document.getElementById(
        "coach-knn-mae-safety"
    ).textContent =
        Number(
            statistics.knn_mae_safety ?? 0
        ).toFixed(2);


    document.getElementById(
        "coach-knn-mae-personalization"
    ).textContent =
        Number(
            statistics.knn_mae_personalization ?? 0
        ).toFixed(2);


    document.getElementById(
        "coach-knn-mae-fidelity"
    ).textContent =
        Number(
            statistics.knn_mae_document_fidelity ?? 0
        ).toFixed(2);
    }


function formatDate(dateValue) {
    if (!dateValue) {
        return "Date inconnue";
    }

    return new Intl.DateTimeFormat(
        "fr-FR",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    ).format(new Date(dateValue));
}


function renderPendingPaths(paths) {
    const container =
        document.getElementById(
            "coach-paths-list"
        );

    const counter =
        document.getElementById(
            "pending-count"
        );

    counter.textContent =
        `${paths.length} parcours`;

    if (!paths.length) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>Aucun parcours en attente</h3>

                <p>
                    Tous les parcours disponibles
                    ont été évalués.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML = paths
        .map((path) => `
            <article class="coach-simple-path-row">

                <div class="coach-simple-path-main">

                    <div class="path-icon">
                        C
                    </div>

                    <div>
                        <h3>
                            ${escapeHtml(path.trigger_message)}
                        </h3>

                        <p>
                            Parcours ${path.id}
                            · ${formatDate(path.created_at)}
                        </p>
                    </div>

                </div>


                <div class="coach-simple-path-actions">

                    <span
                        class="status-badge
                        status-en_attente_evaluation_coach"
                    >
                        À évaluer
                    </span>

                    <button
                        type="button"
                        class="parent-panel-action"
                        onclick="openCoachPath(${path.id})"
                    >
                        Ouvrir
                    </button>

                </div>

            </article>
        `)
        .join("");
}


async function loadPendingPaths() {
    const paths = await apiRequest(
        "/coach/paths/pending"
    );

    renderPendingPaths(paths);
}


function openCoachPath(pathId) {
    window.location.href =
        `/web/coach/paths/${pathId}`;
}


async function initializeCoachDashboard() {
    if (!protectCoachPage()) {
        return;
    }

    displayCoachInformation();

    try {
        await Promise.all([
            loadCoachStatistics(),
            loadPendingPaths()
        ]);

    } catch (error) {
        document.getElementById(
            "coach-paths-list"
        ).innerHTML = `
            <div class="error-box">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


initializeCoachDashboard();