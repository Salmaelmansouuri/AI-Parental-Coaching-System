const loginForm =
    document.getElementById("login-form");

const loginButton =
    document.getElementById("login-button");

const loginMessage =
    document.getElementById("login-message");


const registerForm =
    document.getElementById("register-form");

const registerButton =
    document.getElementById("register-button");

const registerMessage =
    document.getElementById("register-message");


const loginView =
    document.getElementById("login-view");

const registerView =
    document.getElementById("register-view");


const showRegisterButton =
    document.getElementById(
        "show-register-button"
    );

const showLoginButton =
    document.getElementById(
        "show-login-button"
    );


function showLoginMessage(
    message,
    type = "error"
) {
    loginMessage.textContent = message;

    loginMessage.className =
        `form-message modern-login-message ${type}`;
}


function showRegisterMessage(
    message,
    type = "error"
) {
    registerMessage.textContent = message;

    registerMessage.className =
        `form-message modern-login-message ${type}`;
}


function showLoginView() {

    registerView.hidden = true;
    loginView.hidden = false;

    showRegisterMessage("");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function showRegisterView() {

    loginView.hidden = true;
    registerView.hidden = false;

    showLoginMessage("");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


async function getCurrentUser(token) {

    const response = await fetch(
        "/users/me",
        {
            method: "GET",

            headers: {
                "Authorization":
                    `Bearer ${token}`,

                "Accept":
                    "application/json"
            }
        }
    );


    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }


    if (!response.ok) {

        throw new Error(
            data?.detail
            || "Impossible de récupérer les informations du compte."
        );
    }


    return data;
}


async function authenticateUser(
    email,
    password
) {

    const formData =
        new URLSearchParams();


    formData.append(
        "username",
        email
    );

    formData.append(
        "password",
        password
    );


    const response = await fetch(
        "/auth/login",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            },

            body: formData
        }
    );


    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }


    if (!response.ok) {

        throw new Error(
            data?.detail
            || "Adresse e-mail ou mot de passe incorrect."
        );
    }


    const token =
        data.access_token;


    if (!token) {

        throw new Error(
            "Le serveur n'a pas retourné de jeton d'accès."
        );
    }


    const user =
        await getCurrentUser(token);


    if (
        user.role !== "parent"
        && user.role !== "coach"
    ) {

        throw new Error(
            "Rôle utilisateur non reconnu."
        );
    }


    localStorage.setItem(
        "access_token",
        token
    );


    localStorage.setItem(
        "current_user",
        JSON.stringify(user)
    );


    return user;
}


function redirectUser(user) {

    if (user.role === "coach") {

        window.location.href =
            "/web/coach";

    } else {

        window.location.href =
            "/web/parent";
    }
}


/* =========================
   CONNEXION
   ========================= */

loginForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        const email =
            document
                .getElementById("email")
                .value
                .trim();


        const password =
            document
                .getElementById("password")
                .value;


        loginButton.disabled = true;

        loginButton.textContent =
            "Connexion...";


        showLoginMessage("");


        try {

            const user =
                await authenticateUser(
                    email,
                    password
                );


            showLoginMessage(
                "Connexion réussie. Redirection...",
                "success"
            );


            redirectUser(user);


        } catch (error) {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "current_user"
            );


            showLoginMessage(
                error.message
                || "Une erreur est survenue.",
                "error"
            );


        } finally {

            loginButton.disabled = false;

            loginButton.textContent =
                "Se connecter";
        }
    }
);


/* =========================
   INSCRIPTION
   ========================= */

registerForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        const firstName =
            document
                .getElementById(
                    "register-first-name"
                )
                .value
                .trim();


        const lastName =
            document
                .getElementById(
                    "register-last-name"
                )
                .value
                .trim();


        const email =
            document
                .getElementById(
                    "register-email"
                )
                .value
                .trim();


        const password =
            document
                .getElementById(
                    "register-password"
                )
                .value;


        const passwordConfirm =
            document
                .getElementById(
                    "register-password-confirm"
                )
                .value;


        showRegisterMessage("");


        /* Vérification des deux mots de passe */

        if (password !== passwordConfirm) {

            showRegisterMessage(
                "Les deux mots de passe ne correspondent pas.",
                "error"
            );

            return;
        }


        registerButton.disabled = true;

        registerButton.textContent =
            "Création...";


        try {

            const response = await fetch(
                "/users/register",
                {
                    method: "POST",

                    headers: {
                        "Accept":
                            "application/json",

                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        first_name: firstName,
                        last_name: lastName,
                        email: email,
                        password: password,
                        role: "parent"
                    })
                }
            );


            let data = null;


            try {
                data = await response.json();
            } catch {
                data = null;
            }


            if (!response.ok) {

                let message =
                    "Impossible de créer le compte.";


                if (
                    typeof data?.detail
                    === "string"
                ) {

                    message =
                        data.detail;
                }


                throw new Error(message);
            }


            /*
             * Le compte est créé.
             * On NE connecte PAS automatiquement
             * le nouvel utilisateur.
             */

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "current_user"
            );


            /*
             * On vide le formulaire
             * d'inscription.
             */

            registerForm.reset();


            /*
             * Retour à l'écran
             * de connexion.
             */

            showLoginView();


            /*
             * On garde seulement l'e-mail
             * déjà rempli.
             */

            document
                .getElementById("email")
                .value = email;


            document
                .getElementById("password")
                .value = "";


            /*
             * Message affiché sur
             * la connexion.
             */

            showLoginMessage(
                "Compte créé avec succès. Vous pouvez maintenant vous connecter.",
                "success"
            );


            /*
             * Curseur dans le mot de passe.
             */

            document
                .getElementById("password")
                .focus();


        } catch (error) {

            showRegisterMessage(
                error.message
                || "Une erreur est survenue.",
                "error"
            );


        } finally {

            registerButton.disabled =
                false;

            registerButton.textContent =
                "Créer mon compte";
        }
    }
);


/* =========================
   CHANGEMENT DE VUE
   ========================= */

showRegisterButton.addEventListener(
    "click",
    showRegisterView
);


showLoginButton.addEventListener(
    "click",
    showLoginView
);