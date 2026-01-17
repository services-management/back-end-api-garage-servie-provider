import uuid


def test_admin_login_success(client, admin_user):
    """Test successful admin login."""
    response = client.post(
        "/admin/login",
        json={"username": "testadmin", "password": "securepassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_admin_login_incorrect_password(client, admin_user):
    """Test login failure with incorrect password."""
    response = client.post(
        "/admin/login",
        json={"username": "testadmin", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_admin_login_non_existent_user(client):
    """Test login failure with a non-existent username."""
    response = client.post(
        "/admin/login",
        json={"username": "ghost_admin_12345", "password": "securepassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_read_admin_me_unauthorized(client):
    """Test access to a secured endpoint without a token."""
    response = client.get("/admin/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_read_admin_me_success(authenticated_admin_client, admin_user):
    """Test access to a secured endpoint with a valid token."""
    response = authenticated_admin_client.get("/admin/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == admin_user.username
    assert data["role"] == "admin"
    assert "admin_id" in data

def test_create_new_admin_success(authenticated_admin_client):
    """Test creating a new admin account."""
    new_admin_data = {
        "username": "new_test_admin",
        "password": "newsecurepass",
        "email_phone": "new@example.com",
    }
    response = authenticated_admin_client.post("/admin/create", json=new_admin_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_test_admin"
    assert data["role"] == "admin"
    assert uuid.UUID(data["admin_id"])

def test_create_new_admin_conflict(authenticated_admin_client):
    """Test creating an admin with an existing username."""
    # First, create an admin to create a conflict
    new_admin_data = {
        "username": "conflict_admin",
        "password": "anypassword",
        "email_phone": "unique@example.com",
    }
    response = authenticated_admin_client.post("/admin/create", json=new_admin_data)
    assert response.status_code == 201

    # Now, try to create it again
    response = authenticated_admin_client.post("/admin/create", json=new_admin_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken."

def test_update_admin_success(authenticated_admin_client):
    """Test updating the details of the newly created admin."""
    # First, create an admin to update
    new_admin_data = {
        "username": "admin_to_update",
        "password": "password",
        "email_phone": "update@example.com",
    }
    response = authenticated_admin_client.post("/admin/create", json=new_admin_data)
    assert response.status_code == 201
    admin_id = response.json()["admin_id"]

    # Now, update it
    update_data = {
        "username": "updated_test_admin",
        "email_phone": "updated@example.com",
    }
    response = authenticated_admin_client.put(f"/admin/{admin_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updated_test_admin"
    assert data["email_phone"] == "updated@example.com"

def test_provision_technical_account_success(authenticated_admin_client):
    """Test creating a new technical account via the admin endpoint."""
    tech_data = {
        "username": "tech_staff_1",
        "password": "techpass",
        "name": "Tech One",
        "phone_number": "+12345678900",
    }
    response = authenticated_admin_client.post("/admin/technical", json=tech_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "tech_staff_1"
    assert data["role"] == "technical"
    assert data["status"] == "free"
    assert "technical_id" in data

def test_provision_technical_account_conflict(authenticated_admin_client, admin_user):
    """Test creating a technical account using an existing admin username."""
    conflict_data = {
        "username": admin_user.username,
        "password": "pass",
        "name": "Conflict",
        "phone_number": "+11122233344",
    }
    response = authenticated_admin_client.post("/admin/technical", json=conflict_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Username taken."