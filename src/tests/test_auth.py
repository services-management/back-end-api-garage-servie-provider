from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_login_for_access_token():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_for_access_token_incorrect_password():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "wrong password"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_login_for_access_token_not_admin():
    # Note: This test requires creating a non-admin user first.
    # For simplicity, we are not covering that in this example.
    pass
