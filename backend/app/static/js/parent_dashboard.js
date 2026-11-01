const token = localStorage.getItem("access_token");
const storedUser = localStorage.getItem("current_user");

let currentUser = null;
let cachedChildren = [];

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


function protectParentPage() {
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
        } else if (Array.isArray(data?.detail)) {
            errorMessage = data.detail
                .map((error) => {
                    const field = error.loc
                        ?.filter((item) => item !== "body")
                        .join(" → ");

                    return `${field || "Champ"} : ${error.msg}`;
                })
                .join(" | ");
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


function displayUserInformation() {
    const fullName = [
        currentUser.first_name,
        currentUser.last_name
    ]
        .filter(Boolean)
        .join(" ");

    const firstName =
        currentUser.first_name || "Parent";

    const parentName =
        document.getElementById("parent-name");

    const parentEmail =
        document.getElementById("parent-email");

    const welcomeName =
        document.getElementById("welcome-name");

    const parentAvatar =
        document.getElementById("parent-avatar");

    if (parentName) {
        parentName.textContent =
            fullName || "Parent";
    }

    if (parentEmail) {
        parentEmail.textContent =
            currentUser.email || "";
    }

    if (welcomeName) {
        welcomeName.textContent =
            firstName;
    }

    if (parentAvatar) {
        parentAvatar.textContent =
            firstName.charAt(0).toUpperCase();
    }
}


function showParentView(viewName) {
    const view =
        document.getElementById(
            `${viewName}-view`
        );

    if (!view) {
        return;
    }

    document
        .querySelectorAll(".parent-view")
        .forEach((element) => {
            element.classList.remove("active");
        });

    view.classList.add("active");

    document
        .querySelectorAll(
            ".chat-sidebar-link[data-view]"
        )
        .forEach((button) => {
            button.classList.toggle(
                "active",
                button.dataset.view === viewName
            );
        });

    if (viewName === "home") {
        setTimeout(() => {
            document
                .getElementById(
                    "quick-trigger-message"
                )
                ?.focus();
        }, 50);
    }
}


function updateStatistic(id, value) {
    const element =
        document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


async function loadStatistics() {
    try {
        const statistics =
            await apiRequest(
                "/statistics/parent"
            );

        updateStatistic(
            "stat-total-paths",
            statistics.total_paths
        );

        updateStatistic(
            "stat-active-paths",
            statistics.active_paths
        );

        updateStatistic(
            "stat-completed-paths",
            statistics.completed_paths
        );

        updateStatistic(
            "stat-satisfaction",
            `${statistics.satisfaction_rate}%`
        );

        updateStatistic(
            "stat-waiting-review",
            statistics.waiting_coach_review
        );

        updateStatistic(
            "stat-positive-ratings",
            statistics.positive_ratings
        );

        updateStatistic(
            "stat-negative-ratings",
            statistics.negative_ratings
        );

    } catch (error) {
        console.error(
            "Erreur statistiques :",
            error
        );
    }
}


function getChildInitials(child) {
    return (
        child.alias?.charAt(0)
        || "?"
    ).toUpperCase();
}


function getGenderLabel(gender) {
    const labels = {
        "garçon": "Garçon",
        "fille": "Fille",
        "autre": "Autre",
        "non_précisé": "Non précisé"
    };

    return labels[gender]
        || "Non renseigné";
}


function populateQuickChildSelect(children) {
    const select =
        document.getElementById(
            "quick-child-select"
        );

    if (!select) {
        return;
    }

    if (!children.length) {
        select.innerHTML = `
            <option value="">
                Aucun enfant enregistré
            </option>
        `;

        select.disabled = true;
        return;
    }

    select.disabled = false;

    select.innerHTML = children
        .map((child) => `
            <option value="${child.id}">
                ${escapeHtml(child.alias)}
                · ${child.age} ans
            </option>
        `)
        .join("");
}


function renderChildren(children) {
    const container =
        document.getElementById(
            "children-list"
        );

    const childrenCount =
        document.getElementById(
            "children-count"
        );

    if (childrenCount) {
        childrenCount.textContent =
            `${children.length} enfant(s)`;
    }

    if (!container) {
        return;
    }

    if (!children.length) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>Aucun enfant enregistré</h3>

                <p>
                    Ajoutez un enfant pour commencer
                    votre premier parcours.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML = children
        .map((child) => `
            <article class="child-card">

                <div class="child-avatar">
                    ${getChildInitials(child)}
                </div>

                <div class="child-information">

                    <h3>
                        ${escapeHtml(child.alias)}
                    </h3>

                    <p>
                        ${child.age} ans ·
                        ${getGenderLabel(child.gender)}
                    </p>

                    <span>
                        ${
                            escapeHtml(
                                child.family_context
                                || "Contexte familial non renseigné"
                            )
                        }
                    </span>

                </div>

                <button
                    class="small-action-button"
                    type="button"
                    onclick="startPathForChild(${child.id})"
                >
                    Nouveau parcours
                </button>

            </article>
        `)
        .join("");
}


async function loadChildren() {
    const container =
        document.getElementById(
            "children-list"
        );

    try {
        const children =
            await apiRequest("/children");

        cachedChildren = children;

        renderChildren(children);
        populateQuickChildSelect(children);

    } catch (error) {
        if (container) {
            container.innerHTML = `
                <div class="error-box">
                    ${escapeHtml(error.message)}
                </div>
            `;
        }
    }
}


function getStatusLabel(status) {
    const labels = {
        ouvert: "Ouvert",
        en_attente_retour_parent:
            "En attente du parent",
        en_attente_evaluation_coach:
            "En attente du coach",
        termine: "Terminé",
        annule: "Annulé"
    };

    return labels[status] || status;
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


function renderPaths(paths) {
    const container =
        document.getElementById(
            "paths-list"
        );

    if (!container) {
        return;
    }

    if (!paths.length) {
        container.innerHTML = `
            <div class="empty-state">

                <h3>Aucun parcours</h3>

                <p>
                    Commencez une nouvelle conversation
                    depuis l’accueil.
                </p>

            </div>
        `;

        return;
    }

    const sortedPaths = [...paths]
        .sort(
            (first, second) =>
                new Date(second.created_at)
                - new Date(first.created_at)
        );

    container.innerHTML = sortedPaths
        .map((path) => `
            <article class="path-row">

                <div class="path-main-content">

                    <div class="path-icon">
                        P
                    </div>

                    <div>

                        <h3>
                            ${escapeHtml(path.trigger_message)}
                        </h3>

                        <p>
                            ${formatDate(path.created_at)}
                        </p>

                    </div>

                </div>


                <div class="path-actions">

                    <span
                        class="status-badge status-${path.status}"
                    >
                        ${getStatusLabel(path.status)}
                    </span>

                    <button
                        class="text-button"
                        type="button"
                        onclick="openPath(${path.id})"
                    >
                        Ouvrir
                    </button>

                </div>

            </article>
        `)
        .join("");
}


async function loadPaths() {
    const container =
        document.getElementById(
            "paths-list"
        );

    try {
        const paths =
            await apiRequest(
                "/coaching-paths"
            );

        renderPaths(paths);

    } catch (error) {
        if (container) {
            container.innerHTML = `
                <div class="error-box">
                    ${escapeHtml(error.message)}
                </div>
            `;
        }
    }
}


function openAddChildMessage() {
    const modal =
        document.getElementById(
            "child-modal"
        );

    const form =
        document.getElementById(
            "child-form"
        );

    const message =
        document.getElementById(
            "child-form-message"
        );

    form.reset();

    message.textContent = "";
    message.className = "form-message";

    modal.classList.remove("hidden");

    document
        .getElementById(
            "child-first-name"
        )
        .focus();
}


function closeChildModal() {
    document
        .getElementById(
            "child-modal"
        )
        ?.classList
        .add("hidden");
}


async function createChild(event) {
    event.preventDefault();

    const submitButton =
        document.getElementById(
            "child-submit-button"
        );

    const message =
        document.getElementById(
            "child-form-message"
        );

    const childData = {
        alias: document
            .getElementById(
                "child-first-name"
            )
            .value
            .trim(),

        age: Number(
            document
                .getElementById(
                    "child-age"
                )
                .value
        ),

        gender: document
            .getElementById(
                "child-gender"
            )
            .value,

        family_context: document
            .getElementById(
                "child-family-context"
            )
            .value
            .trim() || null,

        additional_information: document
            .getElementById(
                "child-additional-information"
            )
            .value
            .trim() || null
    };

    submitButton.disabled = true;
    submitButton.textContent = "Ajout...";

    message.textContent = "";
    message.className = "form-message";

    try {
        await apiRequest(
            "/children",
            {
                method: "POST",
                body: JSON.stringify(
                    childData
                )
            }
        );

        message.textContent =
            "L’enfant a été ajouté.";

        message.className =
            "form-message success";

        await loadChildren();

        setTimeout(() => {
            closeChildModal();
        }, 600);

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "form-message error";

    } finally {
        submitButton.disabled = false;
        submitButton.textContent =
            "Ajouter l’enfant";
    }
}


function startPathForChild(childId) {
    const modal =
        document.getElementById(
            "path-modal"
        );

    const childIdInput =
        document.getElementById(
            "path-child-id"
        );

    const selectedChildName =
        document.getElementById(
            "selected-child-name"
        );

    const triggerMessage =
        document.getElementById(
            "path-trigger-message"
        );

    const formMessage =
        document.getElementById(
            "path-form-message"
        );

    const child =
        cachedChildren.find(
            (item) =>
                item.id === childId
        );

    childIdInput.value =
        childId;

    selectedChildName.textContent =
        child?.alias
        || `Enfant ${childId}`;

    triggerMessage.value = "";

    formMessage.textContent = "";
    formMessage.className =
        "form-message";

    modal.classList.remove("hidden");
    triggerMessage.focus();
}


function closePathModal() {
    document
        .getElementById(
            "path-modal"
        )
        ?.classList
        .add("hidden");
}


async function createCoachingPath(event) {
    event.preventDefault();

    const submitButton =
        document.getElementById(
            "path-submit-button"
        );

    const formMessage =
        document.getElementById(
            "path-form-message"
        );

    const childId = Number(
        document
            .getElementById(
                "path-child-id"
            )
            .value
    );

    const triggerMessage =
        document
            .getElementById(
                "path-trigger-message"
            )
            .value
            .trim();

    submitButton.disabled = true;
    submitButton.textContent =
        "Création...";

    formMessage.textContent = "";
    formMessage.className =
        "form-message";

    try {
        const createdPath =
            await apiRequest(
                "/coaching-paths",
                {
                    method: "POST",
                    body: JSON.stringify({
                        child_id: childId,
                        trigger_message:
                            triggerMessage
                    })
                }
            );

        openPath(createdPath.id);

    } catch (error) {
        formMessage.textContent =
            error.message;

        formMessage.className =
            "form-message error";

    } finally {
        submitButton.disabled = false;
        submitButton.textContent =
            "Créer le parcours";
    }
}


async function createQuickPath(event) {
    event.preventDefault();

    const childSelect =
        document.getElementById(
            "quick-child-select"
        );

    const textarea =
        document.getElementById(
            "quick-trigger-message"
        );

    const submitButton =
        document.getElementById(
            "quick-path-submit"
        );

    const message =
        document.getElementById(
            "quick-path-message"
        );

    const childId =
        Number(childSelect.value);

    const triggerMessage =
        textarea.value.trim();

    message.textContent = "";
    message.className =
        "form-message quick-home-message";

    if (!childId) {
        message.textContent =
            "Ajoutez ou sélectionnez d’abord un enfant.";

        message.classList.add(
            "error"
        );

        return;
    }

    submitButton.disabled = true;

    try {
        const createdPath =
            await apiRequest(
                "/coaching-paths",
                {
                    method: "POST",
                    body: JSON.stringify({
                        child_id: childId,
                        trigger_message:
                            triggerMessage
                    })
                }
            );

        message.textContent =
            "Ouverture du parcours...";

        message.classList.add(
            "success"
        );

        openPath(createdPath.id);

    } catch (error) {
        message.textContent =
            error.message;

        message.classList.add(
            "error"
        );

    } finally {
        submitButton.disabled = false;
    }
}


function openPath(pathId) {
    window.location.href =
        `/web/parent/paths/${pathId}`;
}


async function initializeDashboard() {
    if (!protectParentPage()) {
        return;
    }

    displayUserInformation();

    await Promise.all([
        loadStatistics(),
        loadChildren(),
        loadPaths()
    ]);
}


const childForm =
    document.getElementById(
        "child-form"
    );

if (childForm) {
    childForm.addEventListener(
        "submit",
        createChild
    );
}


const pathForm =
    document.getElementById(
        "path-form"
    );

if (pathForm) {
    pathForm.addEventListener(
        "submit",
        createCoachingPath
    );
}


const quickPathForm =
    document.getElementById(
        "quick-path-form"
    );

if (quickPathForm) {
    quickPathForm.addEventListener(
        "submit",
        createQuickPath
    );
}


const childModal =
    document.getElementById(
        "child-modal"
    );

if (childModal) {
    childModal.addEventListener(
        "click",
        (event) => {
            if (
                event.target
                === childModal
            ) {
                closeChildModal();
            }
        }
    );
}


const pathModal =
    document.getElementById(
        "path-modal"
    );

if (pathModal) {
    pathModal.addEventListener(
        "click",
        (event) => {
            if (
                event.target
                === pathModal
            ) {
                closePathModal();
            }
        }
    );
}


document.addEventListener(
    "keydown",
    (event) => {
        if (event.key === "Escape") {
            closeChildModal();
            closePathModal();
        }
    }
);


initializeDashboard();