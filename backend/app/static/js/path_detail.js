const token = localStorage.getItem("access_token");
const storedUser = localStorage.getItem("current_user");
const pathId = Number(window.PATH_ID);

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


function protectPage() {
    if (!token || !currentUser) {
        window.location.href = "/web/login";
        return false;
    }

    if (currentUser.role !== "parent") {
        window.location.href = "/web/coach";
        return false;
    }

    return true;
}

function applyUserIdentity() {
    const firstName =
        currentUser?.first_name
        || "Parent";

    const greeting =
        document.getElementById(
            "chat-greeting"
        );

    if (greeting) {
        greeting.textContent =
            `Bonjour ${firstName}`;
    }

    const userName =
        document.getElementById(
            "sidebar-user-name"
        );

    if (userName) {
        userName.textContent =
            firstName;
    }

    const avatar =
        document.getElementById(
            "sidebar-user-avatar"
        );

    if (avatar) {
        avatar.textContent =
            firstName
                .charAt(0)
                .toUpperCase();
    }
}

function goBackToDashboard() {
    window.location.href = "/web/parent";
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
        throw new Error("Session expir\u00E9e.");
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
        } else if (Array.isArray(data?.detail)) {
            errorMessage = data.detail
                .map((error) => {
                    const field = error.loc
                        ?.filter((item) => item !== "body")
                        .join(" \u2192 ");

                    return `${field || "Champ"} : ${error.msg}`;
                })
                .join(" | ");
        }

        throw new Error(errorMessage);
    }

    return data;
}


function escapeHtml(value) {
    const element = document.createElement("div");

    element.textContent = value || "";

    return element.innerHTML;
}


function getStatusLabel(status) {
    const labels = {
        ouvert: "Ouvert",
        en_attente_retour_parent:
            "En attente du parent",
        en_attente_evaluation_coach:
            "En attente du coach",
        termine: "Termin\u00E9",
        annule: "Annul\u00E9"
    };

    return labels[status] || status;
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


async function loadPath() {
    const path = await apiRequest(
        `/coaching-paths/${pathId}`
    );

    const child = await apiRequest(
        `/children/${path.child_id}`
    );

    document.getElementById(
        "path-title"
    ).textContent =
        `Parcours n\u00B0 ${path.id}`;

    document.getElementById(
        "path-child"
    ).textContent =
        `${child.alias} \u00B7 ${child.age} ans`;

    const statusElement =
        document.getElementById(
            "path-status"
        );

    statusElement.textContent =
        getStatusLabel(path.status);

    statusElement.className =
        `status-badge status-${path.status}`;

    document.getElementById(
        "trigger-message"
    ).textContent =
        path.trigger_message;

    const conclusionCard =
        document.getElementById(
            "parent-conclusion-card"
        );

    const conclusionDisplay =
        document.getElementById(
            "parent-conclusion-display"
        );

    if (
        path.parent_conclusion
        && conclusionCard
        && conclusionDisplay
    ) {
        conclusionDisplay.textContent =
            path.parent_conclusion;

        conclusionCard.classList.remove(
            "hidden"
        );
    }

    if (
        path.status === "termine"
        || path.status === "annule"
        || path.status
            === "en_attente_evaluation_coach"
    ) {
        disableConversationForm();
    }

    if (path.status === "termine") {
        await loadCoachEvaluation();
    }
}

async function loadCoachEvaluation() {
    const evaluationCard =
        document.getElementById(
            "coach-evaluation-card"
        );

    try {
        const evaluation = await apiRequest(
            `/coaching-paths/${pathId}/evaluation`
        );

        document.getElementById(
            "evaluation-relevance"
        ).textContent =
            `${evaluation.relevance_score} / 5`;

        document.getElementById(
            "evaluation-safety"
        ).textContent =
            `${evaluation.safety_score} / 5`;

        document.getElementById(
            "evaluation-personalization"
        ).textContent =
            `${evaluation.personalization_score} / 5`;

        document.getElementById(
            "evaluation-fidelity"
        ).textContent =
            `${evaluation.document_fidelity_score} / 5`;

        document.getElementById(
            "evaluation-global"
        ).textContent =
            `${evaluation.global_score} / 5`;

        const decisionElement =
            document.getElementById(
                "evaluation-decision"
            );

        if (evaluation.validated) {
            decisionElement.textContent =
                "Parcours valid\u00E9";
        } else {
            decisionElement.textContent =
                "Parcours non valid\u00E9";
        }

        const commentBox =
            document.getElementById(
                "coach-comment-box"
            );

        if (evaluation.comment) {
            document.getElementById(
                "evaluation-comment"
            ).textContent =
                evaluation.comment;

            commentBox.classList.remove(
                "hidden"
            );
        }

        evaluationCard.classList.remove(
            "hidden"
        );

    } catch (error) {
        console.log(
            "Evaluation coach non disponible :",
            error.message
        );
    }
}


function getMessageLabel(message) {
    if (message.sender === "llm") {
        return "Coach IA";
    }

    return "Parent";
}

function renderSources(message) {
    if (
        message.sender !== "llm"
        || !Array.isArray(message.sources)
        || message.sources.length === 0
    ) {
        return "";
    }

    const sourcesHtml = message.sources
        .map((source, index) => {
            return `
                <div class="source-item">
                    <div class="source-header">
                        <strong>
                            Source ${index + 1}
                        </strong>

                        <span>
                            ${escapeHtml(source.document_name)}
                            \u00B7 page ${source.page_number}
                        </span>
                    </div>

                    <p class="source-extract">
                        ${escapeHtml(source.text)}
                    </p>
                </div>
            `;
        })
        .join("");

    return `
        <div class="message-sources">
            <button
                type="button"
                class="sources-toggle"
                onclick="toggleSources(${message.id})"
            >
                \uD83D\uDCC4 Afficher les sources
                <span class="sources-count">
                    ${message.sources.length}
                </span>
            </button>

            <div
                id="sources-${message.id}"
                class="sources-panel hidden"
            >
                ${sourcesHtml}
            </div>
        </div>
    `;
}


function toggleSources(messageId) {
    const panel = document.getElementById(
        `sources-${messageId}`
    );

    if (!panel) {
        return;
    }

    panel.classList.toggle("hidden");
}

function renderMessages(messages) {
    const container =
        document.getElementById(
            "messages-container"
        );

    if (!messages.length) {
        container.innerHTML = `
            <div class="empty-state">
                Aucun message dans ce parcours.
            </div>
        `;

        return;
    }

    container.innerHTML = messages
        .map((message) => {
            const senderClass =
                message.sender === "llm"
                    ? "ai-message"
                    : "parent-message";

            return `
                <article
                    class="conversation-message ${senderClass}"
                >

                    <div class="message-metadata">
                        <strong>
                            ${getMessageLabel(message)}
                        </strong>

                        <span>
                            ${formatDate(message.created_at)}
                        </span>
                    </div>

                    <p>
                        ${escapeHtml(message.content)}
                    </p>

                    ${renderSources(message)}

                    ${
                        message.sender === "llm"
                            ? `
                                <div
                                    class="message-type-label"
                                >
                                    ${
                                        message.message_type
                                        === "question_clarification"
                                            ? "Question de clarification"
                                            : "Intervention"
                                    }
                                </div>

                                <div class="rating-actions">
                                    <span>
                                        Cette r\u00E9ponse vous a-t-elle aid\u00E9 ?
                                    </span>

                                    <button
                                        type="button"
                                        class="rating-button"
                                        onclick="rateMessage(
                                            ${message.id},
                                            'positive'
                                        )"
                                    >
                                        \uD83D\uDC4D
                                    </button>

                                    <button
                                        type="button"
                                        class="rating-button"
                                        onclick="rateMessage(
                                            ${message.id},
                                            'negative'
                                        )"
                                    >
                                        \uD83D\uDC4E
                                    </button>
                                </div>

                                <p
                                    id="rating-message-${message.id}"
                                    class="rating-result"
                                ></p>
                            `
                            : ""
                    }

                </article>
            `;
        })
        .join("");

    container.scrollTop =
        container.scrollHeight;
}


async function rateMessage(
    messageId,
    value
) {
    const resultElement =
        document.getElementById(
            `rating-message-${messageId}`
        );

    try {
        await apiRequest(
            `/messages/${messageId}/rating`,
            {
                method: "PUT",
                body: JSON.stringify({
                    value: value,
                    comment: null
                })
            }
        );

        if (value === "positive") {
            resultElement.textContent =
                "Merci pour votre retour positif.";
        } else {
            resultElement.textContent =
                "Merci pour votre retour.";
        }

        resultElement.className =
            "rating-result success";

    } catch (error) {
        resultElement.textContent =
            error.message;

        resultElement.className =
            "rating-result error";
    }
}


async function loadMessages() {
    const messages = await apiRequest(
        `/coaching-paths/${pathId}/messages`
    );

    renderMessages(messages);
}


async function sendParentMessage(event) {
    event.preventDefault();

    const textarea =
        document.getElementById(
            "parent-message"
        );

    const submitButton =
        document.getElementById(
            "message-submit-button"
        );

    const formMessage =
        document.getElementById(
            "message-form-message"
        );

    const content =
        textarea.value.trim();

    if (!content) {
        return;
    }

    submitButton.disabled = true;
    submitButton.textContent =
        "Envoi...";

    formMessage.textContent = "";
    formMessage.className =
        "form-message";

    try {
        await apiRequest(
            `/coaching-paths/${pathId}/messages`,
            {
                method: "POST",
                body: JSON.stringify({
                    content: content,
                    message_type:
                        "reponse_parent"
                })
            }
        );

        textarea.value = "";

        formMessage.textContent =
            "Message envoy\u00E9.";

        formMessage.className =
            "form-message success";

        await loadMessages();

    } catch (error) {
        formMessage.textContent =
            error.message;

        formMessage.className =
            "form-message error";

    } finally {
        submitButton.disabled = false;
        submitButton.textContent =
            "Envoyer";
    }
}


async function generateAiResponse() {
    const button =
        document.getElementById(
            "generate-button"
        );

    const formMessage =
        document.getElementById(
            "message-form-message"
        );

    button.disabled = true;

    button.textContent =
        "\u0047\u00E9n\u00E9ration de la r\u00E9ponse..."

    formMessage.textContent =
        "Le coach IA analyse la situation.";

    formMessage.className =
        "form-message";

    try {
        await apiRequest(
            `/coaching-paths/${pathId}/generate-response`,
            {
                method: "POST"
            }
        );

        formMessage.textContent =
            "\u004C\u0061 r\u00E9ponse du coach IA a \u00E9t\u00E9 g\u00E9n\u00E9r\u00E9e."

        formMessage.className =
            "form-message success";

        await loadMessages();

    } catch (error) {
        formMessage.textContent =
            error.message;

        formMessage.className =
            "form-message error";

    } finally {
        button.disabled = false;

        button.textContent =
            "Demander une r\u00E9ponse IA";
    }
}


function disableConversationForm() {
    const textarea =
        document.getElementById(
            "parent-message"
        );

    const sendButton =
        document.getElementById(
            "message-submit-button"
        );

    const generateButton =
        document.getElementById(
            "generate-button"
        );

    const conclusionButton =
        document.getElementById(
            "conclusion-button"
        );

    if (textarea) {
        textarea.disabled = true;

        textarea.placeholder =
            "Ce parcours ne peut plus \u00EAtre modifi\u00E9.";
    }

    if (sendButton) {
        sendButton.disabled = true;
    }

    if (generateButton) {
        generateButton.disabled = true;
    }

    if (conclusionButton) {
        conclusionButton.disabled = true;
    }
}


function openConclusionModal() {
    const modal =
        document.getElementById(
            "conclusion-modal"
        );

    const textarea =
        document.getElementById(
            "parent-conclusion"
        );

    const message =
        document.getElementById(
            "conclusion-form-message"
        );

    if (!modal || !textarea || !message) {
        return;
    }

    textarea.value = "";

    message.textContent = "";
    message.className =
        "form-message";

    modal.classList.remove("hidden");

    textarea.focus();
}


function closeConclusionModal() {
    const modal =
        document.getElementById(
            "conclusion-modal"
        );

    if (modal) {
        modal.classList.add("hidden");
    }
}


async function submitConclusion(event) {
    event.preventDefault();

    const textarea =
        document.getElementById(
            "parent-conclusion"
        );

    const button =
        document.getElementById(
            "conclusion-submit-button"
        );

    const message =
        document.getElementById(
            "conclusion-form-message"
        );

    const parentConclusion =
        textarea.value.trim();

    if (!parentConclusion) {
        return;
    }

    button.disabled = true;

    button.textContent =
        "Enregistrement...";

    message.textContent = "";

    message.className =
        "form-message";

    try {
        await apiRequest(
            `/coaching-paths/${pathId}/conclusion`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    parent_conclusion:
                        parentConclusion
                })
            }
        );

        message.textContent =
            "Parcours termin\u00E9. Il sera maintenant \u00E9valu\u00E9 par un coach.";

        message.className =
            "form-message success";

        await loadPath();

        setTimeout(() => {
            closeConclusionModal();
        }, 1000);

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "form-message error";

    } finally {
        button.disabled = false;

        button.textContent =
            "Terminer le parcours";
    }
}

async function initializePathPage() {
    if (!protectPage()) {
        return;
    }

    applyUserIdentity();
    
    try {
       await Promise.all([
            loadPath(),
            loadMessages()
        ]);

    } catch (error) {
        document.getElementById(
            "messages-container"
        ).innerHTML = `
            <div class="error-box">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


const messageForm =
    document.getElementById(
        "message-form"
    );

if (messageForm) {
    messageForm.addEventListener(
        "submit",
        sendParentMessage
    );
}


const conclusionForm =
    document.getElementById(
        "conclusion-form"
    );

if (conclusionForm) {
    conclusionForm.addEventListener(
        "submit",
        submitConclusion
    );
}


const conclusionModal =
    document.getElementById(
        "conclusion-modal"
    );

if (conclusionModal) {
    conclusionModal.addEventListener(
        "click",
        (event) => {
            if (
                event.target
                === conclusionModal
            ) {
                closeConclusionModal();
            }
        }
    );
}


document.addEventListener(
    "keydown",
    (event) => {
        if (event.key === "Escape") {
            closeConclusionModal();
        }
    }
);


initializePathPage();

