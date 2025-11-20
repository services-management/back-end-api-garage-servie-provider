from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/app")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Fixing Service API"}


def test_db_connection():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Database connection successful!"}
