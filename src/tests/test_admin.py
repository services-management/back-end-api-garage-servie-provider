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
    assert response.status_code == 403
    # assert response.json()["detail"] == "Not authenticated"


def test_read_admin_me_success(authenticated_admin_client, admin_user):
    """Test access to a secured endpoint with a valid token."""
    response = authenticated_admin_client.get("/admin/me")
    assert response.status_code == 200
    data = response.json()
    # admin_user might be a SQLAlchemy model or a dict - handle both
    username = admin_user.username if hasattr(admin_user, 'username') else admin_user['username']
    assert data["username"] == username
    assert data["role"] == "admin"
    assert "admin_id" in data


def test_create_new_admin_success(authenticated_admin_client):
    """Test creating a new admin account."""
    new_admin_data = {
        "username": "new_test_admin",
        "password": "newsecurepass",
        "email_phone": "new@example.com",
    }
    response = authenticated_admin_client.post("/admin/", json=new_admin_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_test_admin"
    assert data["role"] == "admin"
    assert uuid.UUID(data["admin_id"])


def test_create_new_admin_conflict(authenticated_admin_client):
    """Test creating an admin with an existing username."""
    # Create first admin
    new_admin_data = {
        "username": "conflict_admin",
        "password": "anypassword",
        "email_phone": "unique@example.com",
    }
    response = authenticated_admin_client.post("/admin/", json=new_admin_data)
    assert response.status_code == 201

    # Try to create again - should conflict
    response = authenticated_admin_client.post("/admin/", json=new_admin_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken."


def test_update_admin_success(authenticated_admin_client):
    """Test updating the details of the newly created admin."""
    # Create an admin to update
    new_admin_data = {
        "username": "admin_to_update",
        "password": "password",
        "email_phone": "update@example.com",
    }
    response = authenticated_admin_client.post("/admin/", json=new_admin_data)
    assert response.status_code == 201
    admin_id = response.json()["admin_id"]  

    # Update it
    update_data = {
        "username": "updated_test_admin",
        "email_phone": "updated@example.com",
    }
    response = authenticated_admin_client.put(f"/admin/{admin_id}", json=update_data)
    if response.status_code == 405:
        response = authenticated_admin_client.patch(f"/admin/{admin_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updated_test_admin"
    assert data["email_phone"] == "updated@example.com"


def test_update_admin_not_found(authenticated_admin_client):
    """Test updating a non-existent admin."""
    fake_admin_id = str(uuid.uuid4())
    update_data = {
        "username": "updated_test_admin",
        "email_phone": "updated@example.com",
    }
    response = authenticated_admin_client.put(f"/admin/{fake_admin_id}", json=update_data)
    assert response.status_code == 404
    # assert response.json()["detail"] == "Admin not found"


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


def test_provision_technical_account_conflict(authenticated_admin_client):
    """Test creating a technical account using an existing username."""
    # First create a technical user
    tech_data = {
        "username": "conflict_tech",
        "password": "techpass",
        "name": "Conflict Tech",
        "phone_number": "+11122233344",
    }
    response = authenticated_admin_client.post("/admin/technical", json=tech_data)
    assert response.status_code == 201

    # Try to create again with same username
    response = authenticated_admin_client.post("/admin/technical", json=tech_data)
    assert response.status_code == 409
    # assert response.json()["detail"] == "Username taken."