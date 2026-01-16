from fastapi.testclient import TestClient

def test_technical_login_success(client, technical_user):
    """Test successful technical staff login."""
    response = client.post(
        "/technical/login",
        json={"username": "tech_staff_1", "password": "techpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_read_technical_me_unauthorized(client):
    """Test access to a secured technical endpoint without a token."""
    response = client.get("/technical/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_read_technical_me_success(authenticated_technical_client, technical_user):
    """Test access to the secured technical 'me' endpoint."""
    response = authenticated_technical_client.get("/technical/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == technical_user.username
    assert data["role"] == "technical"
    assert data["status"] == "free"
    assert "technical_id" in data

def test_update_technical_details_success(authenticated_technical_client):
    """Test updating the name and phone number of the technical user."""
    update_data = {
        "name": "Tech Staff Updated",
        "phone_number": "+98765432100",
    }
    response = authenticated_technical_client.put("/technical/me", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tech Staff Updated"
    assert data["phone_number"] == "+98765432100"

def test_update_technical_status_success(authenticated_technical_client):
    """Test updating only the operational status."""
    status_data = {"status": "busy"}
    response = authenticated_technical_client.patch("/technical/me/status", json=status_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "busy"

def test_admin_cannot_update_technical_status(authenticated_admin_client):
    """Check that the Admin can't use this route (Authorization Test)"""
    status_data = {"status": "off_duty"}
    response = authenticated_admin_client.patch("/technical/me/status", json=status_data)
    assert response.status_code in [401, 403]