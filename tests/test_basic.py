from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }


def test_route_inexistante():
    response = client.get(
        "/route-qui-nexiste-pas"
    )

    assert response.status_code == 404


def test_route_protegee_sans_authentification():
    response = client.get("/children")

    assert response.status_code == 401


def test_mauvais_identifiants():
    response = client.post(
        "/auth/login",
        data={
            "username": "utilisateur-inexistant@example.com",
            "password": "MauvaisMotDePasse123",
        },
    )

    assert response.status_code == 401


def test_hash_password_argon2():
    password = "MotDePasseTest123"

    hashed_password = hash_password(
        password
    )

    assert hashed_password.startswith(
        "$argon2"
    )

    assert verify_password(
        password,
        hashed_password,
    )

    assert not verify_password(
        "MauvaisMotDePasse",
        hashed_password,
    )


def test_jwt():
    token = create_access_token(
        "test@example.com"
    )

    subject = decode_access_token(
        token
    )

    assert subject == "test@example.com"


def test_jwt_invalide():
    subject = decode_access_token(
        "token-invalide"
    )

    assert subject is None

def auth_headers(email: str) -> dict[str, str]:
    token = create_access_token(email)

    return {
        "Authorization": f"Bearer {token}"
    }


def test_parent_ne_peut_pas_acceder_aux_routes_coach():
    response = client.get(
        "/coach/paths/pending",
        headers=auth_headers(
            "salma@example.com"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Cette action est réservée aux coachs humains."
    )


def test_coach_ne_peut_pas_gerer_les_enfants():
    response = client.get(
        "/children",
        headers=auth_headers(
            "coach@example.com"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Seul un parent peut gérer les profils enfants."
    )


def test_parent_ne_peut_pas_acceder_aux_stats_coach():
    response = client.get(
        "/statistics/coach",
        headers=auth_headers(
            "salma@example.com"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Cette action est réservée aux coachs humains."
    )


def test_coach_ne_peut_pas_acceder_aux_stats_parent():
    response = client.get(
        "/statistics/parent",
        headers=auth_headers(
            "coach@example.com"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Cette action est réservée aux parents."
    )
def test_coach_ne_peut_pas_acceder_evaluation_parent():
    response = client.get(
        "/coaching-paths/7/evaluation",
        headers=auth_headers(
            "coach@example.com"
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Seul un parent peut gérer ses parcours de coaching."
    )