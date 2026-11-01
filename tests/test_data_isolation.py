from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import pytest

from backend.app.core.security import create_access_token
from backend.app.database import Base, get_database
from backend.app.main import app

from backend.app.models.user import User, UserRole
from backend.app.models.child import Child, ChildGender
from backend.app.models.coaching_path import (
    CoachingPath,
    CoachingPathStatus,
)

# Ces imports enregistrent aussi les autres tables
# dans Base.metadata.
import backend.app.models.message
import backend.app.models.rating
import backend.app.models.coach_evaluation


test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_database():
    database = TestingSessionLocal()

    try:
        yield database
    finally:
        database.close()

client = TestClient(app)


@pytest.fixture(autouse=True)
def use_test_database():
    app.dependency_overrides[
        get_database
    ] = override_get_database

    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    yield

    app.dependency_overrides.pop(
        get_database,
        None,
    )

    Base.metadata.drop_all(
        bind=test_engine
    )

def reset_database():
    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )


def create_test_data():
    database = TestingSessionLocal()

    parent_a = User(
        first_name="Parent",
        last_name="A",
        email="parent-a@test.com",
        password_hash="test",
        role=UserRole.PARENT,
        is_active=True,
    )

    parent_b = User(
        first_name="Parent",
        last_name="B",
        email="parent-b@test.com",
        password_hash="test",
        role=UserRole.PARENT,
        is_active=True,
    )

    database.add_all([
        parent_a,
        parent_b,
    ])

    database.flush()

    child_a = Child(
        parent_id=parent_a.id,
        alias="Enfant A",
        age=8,
        gender=ChildGender.GIRL,
        family_context=None,
        additional_information=None,
    )

    child_b = Child(
        parent_id=parent_b.id,
        alias="Enfant B",
        age=9,
        gender=ChildGender.BOY,
        family_context=None,
        additional_information=None,
    )

    database.add_all([
        child_a,
        child_b,
    ])

    database.flush()

    path_a = CoachingPath(
        parent_id=parent_a.id,
        child_id=child_a.id,
        trigger_message=(
            "Situation du parent A."
        ),
        status=CoachingPathStatus.OPEN,
    )

    path_b = CoachingPath(
        parent_id=parent_b.id,
        child_id=child_b.id,
        trigger_message=(
            "Situation du parent B."
        ),
        status=CoachingPathStatus.OPEN,
    )

    database.add_all([
        path_a,
        path_b,
    ])

    database.commit()

    data = {
        "parent_a_email":
            parent_a.email,
        "parent_b_email":
            parent_b.email,
        "child_a_id":
            child_a.id,
        "child_b_id":
            child_b.id,
        "path_a_id":
            path_a.id,
        "path_b_id":
            path_b.id,
    }

    database.close()

    return data


def auth_headers(email):
    token = create_access_token(
        email
    )

    return {
        "Authorization":
            f"Bearer {token}"
    }


def test_parent_peut_voir_son_enfant():
    reset_database()
    data = create_test_data()

    response = client.get(
        f"/children/{data['child_a_id']}",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code == 200

    assert (
        response.json()["id"]
        == data["child_a_id"]
    )


def test_parent_ne_peut_pas_voir_enfant_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.get(
        f"/children/{data['child_b_id']}",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code in (
        403,
        404,
    )


def test_parent_peut_voir_son_parcours():
    reset_database()
    data = create_test_data()

    response = client.get(
        f"/coaching-paths/{data['path_a_id']}",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code == 200

    assert (
        response.json()["id"]
        == data["path_a_id"]
    )


def test_parent_ne_peut_pas_voir_parcours_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.get(
        f"/coaching-paths/{data['path_b_id']}",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code in (
        403,
        404,
    )


def test_liste_enfants_est_isolee():
    reset_database()
    data = create_test_data()

    response = client.get(
        "/children",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code == 200

    child_ids = [
        child["id"]
        for child
        in response.json()
    ]

    assert data["child_a_id"] in child_ids
    assert data["child_b_id"] not in child_ids


def test_liste_parcours_est_isolee():
    reset_database()
    data = create_test_data()

    response = client.get(
        "/coaching-paths",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code == 200

    path_ids = [
        path["id"]
        for path
        in response.json()
    ]

    assert data["path_a_id"] in path_ids
    assert data["path_b_id"] not in path_ids

def test_parent_ne_peut_pas_modifier_enfant_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.patch(
        f"/children/{data['child_b_id']}",
        headers=auth_headers(
            data["parent_a_email"]
        ),
        json={
            "alias": "Tentative modification"
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Profil enfant introuvable."
    )


def test_parent_ne_peut_pas_supprimer_enfant_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.delete(
        f"/children/{data['child_b_id']}",
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Profil enfant introuvable."
    )

    # Vérifie que l'enfant B existe toujours
    database = TestingSessionLocal()

    child_b = database.get(
        Child,
        data["child_b_id"],
    )

    assert child_b is not None

    database.close()


def test_parent_ne_peut_pas_conclure_parcours_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.patch(
        (
            f"/coaching-paths/"
            f"{data['path_b_id']}/conclusion"
        ),
        headers=auth_headers(
            data["parent_a_email"]
        ),
        json={
            "parent_conclusion":
                "Tentative de conclusion."
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Parcours de coaching introuvable."
    )


def test_parent_ne_peut_pas_annuler_parcours_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.patch(
        (
            f"/coaching-paths/"
            f"{data['path_b_id']}/cancel"
        ),
        headers=auth_headers(
            data["parent_a_email"]
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Parcours de coaching introuvable."
    )


def test_parent_ne_peut_pas_creer_parcours_pour_enfant_autre_parent():
    reset_database()
    data = create_test_data()

    response = client.post(
        "/coaching-paths",
        headers=auth_headers(
            data["parent_a_email"]
        ),
        json={
            "child_id": data["child_b_id"],
            "trigger_message":
                "Tentative avec enfant du parent B."
        },
    )

    assert response.status_code == 404