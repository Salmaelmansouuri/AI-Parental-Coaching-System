const token = localStorage.getItem("access_token");
const storedUser = localStorage.getItem("current_user");
const pathId = Number(window.PATH_ID);

let currentUser = null;
const coachMessageRatings = {};

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


function goBackToCoachDashboard() {
    window.location.href = "/web/coach";
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

    const coachName =
        document.getElementById("coach-name");

    const coachEmail =
        document.getElementById("coach-email");

    const coachAvatar =
        document.getElementById("coach-avatar");

    if (coachName) {
        coachName.textContent =
            fullName || "Coach";
    }

    if (coachEmail) {
        coachEmail.textContent =
            currentUser.email || "";
    }

    if (coachAvatar) {
        coachAvatar.textContent =
            firstName.charAt(0).toUpperCase();
    }
}


function formatDate(dateValue) {
    if (!dateValue) {
        return "";
    }

    return new Intl.DateTimeFormat(
        "fr-FR",
        {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        }
    ).format(new Date(dateValue));
}


async function loadCoachPath() {
    const path = await apiRequest(
        `/coach/paths/${pathId}`
    );

    document.getElementById(
        "coach-path-title"
    ).textContent =
        `Parcours n° ${path.id}`;

    document.getElementById(
        "coach-path-parent"
    ).textContent =
        `Enfant n° ${path.child_id}`;

    document.getElementById(
        "coach-path-status"
    ).textContent =
        path.status === "termine"
            ? "Terminé"
            : "En attente d’évaluation";

    document.getElementById(
        "coach-trigger-message"
    ).textContent =
        path.trigger_message;

    document.getElementById(
        "coach-parent-conclusion"
    ).textContent =
        path.parent_conclusion
        || "Aucune conclusion.";
}
async function loadMlPrediction() {
    const container =
        document.getElementById(
            "ml-prediction-content"
        );

    if (!container) {
        return;
    }

    try {
        const result = await apiRequest(
            `/coach/paths/${pathId}/ml-prediction`
        );

        if (!result.available) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>
                        ${escapeHtml(
                            result.reason
                            || "Estimation ML indisponible."
                        )}
                    </p>

                    <small>
                        Parcours d'apprentissage disponibles :
                        ${Number(
                            result.training_samples ?? 0
                        )}
                    </small>
                </div>
            `;

            return;
        }

        const prediction =
            result.prediction;

        container.innerHTML = `
            <div class="simple-stat-line">
                <span>Pertinence</span>
                <strong>
                    ${Number(
                        prediction.relevance_score
                    ).toFixed(2)} / 5
                </strong>
            </div>

            <div class="simple-stat-line">
                <span>Sécurité</span>
                <strong>
                    ${Number(
                        prediction.safety_score
                    ).toFixed(2)} / 5
                </strong>
            </div>

            <div class="simple-stat-line">
                <span>Personnalisation</span>
                <strong>
                    ${Number(
                        prediction.personalization_score
                    ).toFixed(2)} / 5
                </strong>
            </div>

            <div class="simple-stat-line">
                <span>Fidélité PET</span>
                <strong>
                    ${Number(
                        prediction.document_fidelity_score
                    ).toFixed(2)} / 5
                </strong>
            </div>

            <div class="simple-stat-line">
                <span>Note globale estimée</span>
                <strong>
                    ${Number(
                        prediction.global_score
                    ).toFixed(2)} / 5
                </strong>
            </div>

            <p
                style="
                    margin-top: 14px;
                    font-size: 13px;
                    opacity: 0.7;
                "
            >
                ${escapeHtml(result.algorithm)}
                · ${Number(result.neighbors_used)}
                voisins
                · ${Number(result.training_samples)}
                parcours historiques
            </p>
        `;

    } catch (error) {
        container.innerHTML = `
            <div class="error-box">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


function renderMessages(messages) {
    const container =
        document.getElementById(
            "coach-messages-container"
        );

    if (!messages.length) {
        container.innerHTML = `
            <div class="empty-state">
                Aucun message.
            </div>
        `;

        return;
    }

    container.innerHTML = messages
        .map((message) => {
            const isAi =
                message.sender === "llm";

            const senderClass =
                isAi
                    ? "coach-review-ai"
                    : "coach-review-parent";

            const senderLabel =
                isAi
                    ? "Coach IA"
                    : "Parent";

            const typeLabel =
                message.message_type
                === "question_clarification"
                    ? "Question de clarification"
                    : "Intervention";

            return `
                <article
                    class="coach-review-message ${senderClass}"
                >

                    <div class="coach-review-message-meta">

                        <strong>
                            ${senderLabel}
                        </strong>

                        <span>
                            ${formatDate(message.created_at)}
                        </span>

                    </div>

                    <div class="coach-review-message-content">
                        ${escapeHtml(message.content)}
                    </div>

                    ${
                        isAi
                            ? `
                                <div class="coach-message-bottom-row">

                                    <span class="coach-message-type">
                                        ${typeLabel}
                                    </span>

                                    <div
                                        class="coach-message-reactions"
                                        data-message-id="${message.id}"
                                    >
                                        <button
                                            type="button"
                                            class="coach-reaction-button positive"
                                            data-value="positive"
                                            onclick="handleCoachReaction(${message.id}, 'positive')"
                                            title="Réponse utile"
                                            aria-label="Réaction positive"
                                        >
                                            👍
                                        </button>

                                        <button
                                            type="button"
                                            class="coach-reaction-button negative"
                                            data-value="negative"
                                            onclick="handleCoachReaction(${message.id}, 'negative')"
                                            title="Réponse à améliorer"
                                            aria-label="Réaction négative"
                                        >
                                            👎
                                        </button>
                                    </div>

                                </div>
                            `
                            : ""
                    }

                </article>
            `;
        })
        .join("");
}


function updateCoachReactionButtons(messageId) {
    const container =
        document.querySelector(
            `.coach-message-reactions[data-message-id="${messageId}"]`
        );

    if (!container) {
        return;
    }

    const currentValue =
        coachMessageRatings[messageId] || null;

    container
        .querySelectorAll(".coach-reaction-button")
        .forEach((button) => {
            button.classList.toggle(
                "selected",
                button.dataset.value === currentValue
            );
        });
}


async function loadCoachMessageRating(messageId) {
    const response = await fetch(
        `/coach/messages/${messageId}/rating`,
        {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }
        }
    );

    if (response.status === 401) {
        logout();
        return;
    }

    if (response.status === 404) {
        coachMessageRatings[messageId] = null;
        updateCoachReactionButtons(messageId);
        return;
    }

    if (!response.ok) {
        return;
    }

    const rating = await response.json();

    coachMessageRatings[messageId] =
        rating.value;

    updateCoachReactionButtons(messageId);
}


async function deleteCoachMessageRating(messageId) {
    const response = await fetch(
        `/coach/messages/${messageId}/rating`,
        {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }
        }
    );

    if (response.status === 401) {
        logout();
        return;
    }

    if (
        !response.ok
        && response.status !== 404
    ) {
        throw new Error(
            "Impossible de supprimer la réaction."
        );
    }
}


async function handleCoachReaction(
    messageId,
    value
) {
    const previousValue =
        coachMessageRatings[messageId] || null;

    const container =
        document.querySelector(
            `.coach-message-reactions[data-message-id="${messageId}"]`
        );

    if (container) {
        container
            .querySelectorAll("button")
            .forEach((button) => {
                button.disabled = true;
            });
    }

    try {
        if (previousValue === value) {
            await deleteCoachMessageRating(
                messageId
            );

            coachMessageRatings[messageId] =
                null;

        } else {
            const rating = await apiRequest(
                `/coach/messages/${messageId}/rating`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        value: value,
                        comment: null
                    })
                }
            );

            coachMessageRatings[messageId] =
                rating.value;
        }

        updateCoachReactionButtons(messageId);

    } catch (error) {
        console.error(
            "Erreur réaction coach :",
            error
        );

    } finally {
        if (container) {
            container
                .querySelectorAll("button")
                .forEach((button) => {
                    button.disabled = false;
                });
        }
    }
}


async function loadCoachMessages() {
    const messages = await apiRequest(
        `/coach/paths/${pathId}/messages`
    );

    renderMessages(messages);

    const aiMessages =
        messages.filter(
            (message) =>
                message.sender === "llm"
        );

    await Promise.all(
        aiMessages.map(
            (message) =>
                loadCoachMessageRating(
                    message.id
                )
        )
    );
}


function calculateGlobalScore() {
    const scoreIds = [
        "relevance-score",
        "safety-score",
        "personalization-score",
        "document-fidelity-score"
    ];

    const scores = scoreIds.map(
        (id) => Number(
            document.getElementById(id)?.value
        )
    );

    const display =
        document.getElementById(
            "global-score-value"
        );

    if (!display) {
        return null;
    }

    const allScoresSelected =
        scores.every(
            (score) =>
                Number.isFinite(score)
                && score >= 1
                && score <= 5
        );

    if (!allScoresSelected) {
        display.textContent = "—";
        return null;
    }

    const globalScore =
        scores.reduce(
            (sum, score) => sum + score,
            0
        ) / scores.length;

    display.textContent =
        globalScore.toFixed(2);

    return globalScore;
}


function initializeAutomaticGlobalScore() {
    const scoreIds = [
        "relevance-score",
        "safety-score",
        "personalization-score",
        "document-fidelity-score"
    ];

    scoreIds.forEach((id) => {
        document
            .getElementById(id)
            ?.addEventListener(
                "change",
                calculateGlobalScore
            );
    });

    calculateGlobalScore();
}


async function submitCoachEvaluation(event) {
    event.preventDefault();

    const button =
        document.getElementById(
            "coach-evaluation-submit"
        );

    const message =
        document.getElementById(
            "coach-evaluation-message"
        );

    const evaluationData = {
        relevance_score: Number(
            document.getElementById(
                "relevance-score"
            ).value
        ),

        safety_score: Number(
            document.getElementById(
                "safety-score"
            ).value
        ),

        personalization_score: Number(
            document.getElementById(
                "personalization-score"
            ).value
        ),

        document_fidelity_score: Number(
            document.getElementById(
                "document-fidelity-score"
            ).value
        ),

        comment:
            document.getElementById(
                "coach-comment"
            ).value.trim() || null,

        validated:
            document.getElementById(
                "validated"
            ).value === "true"
    };

    button.disabled = true;
    button.textContent =
        "Enregistrement...";

    message.textContent = "";
    message.className = "form-message";

    try {
        await apiRequest(
            `/coach/paths/${pathId}/evaluation`,
            {
                method: "PUT",
                body: JSON.stringify(
                    evaluationData
                )
            }
        );

        message.textContent =
            "Évaluation enregistrée avec succès.";

        message.className =
            "form-message success";

        setTimeout(() => {
            window.location.href =
                "/web/coach";
        }, 1000);

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "form-message error";

    } finally {
        button.disabled = false;

        button.textContent =
            "Enregistrer l’évaluation";
    }
}


async function initializeCoachPathPage() {
    if (!protectCoachPage()) {
        return;
    }

    displayCoachInformation();

   try {
    await Promise.all([
        loadCoachPath(),
        loadCoachMessages(),
        loadMlPrediction()
    ]);

} 
catch (error) {
    document.getElementById(
        "coach-messages-container"
    ).innerHTML = `
        <div class="error-box">
            ${escapeHtml(error.message)}
        </div>
    `;
}
    
}


const evaluationForm =
    document.getElementById(
        "coach-evaluation-form"
    );

if (evaluationForm) {
    evaluationForm.addEventListener(
        "submit",
        submitCoachEvaluation
    );
}


initializeAutomaticGlobalScore();
initializeCoachPathPage();