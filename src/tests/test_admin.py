from fastapi.testclient import TestClient
from src.app.app import app
from src.dependency import get_db, get_admin_controller
from src.controller.admin_controller import AdminController
import uuid

# A fixture/function that yields a test database session
def override_get_db():
    try:
        # Assuming you have a test session defined somewhere
        db = TestingSessionLocal() 
        yield db
    finally:
        db.close()

# The function to override the controller dependency
def override_get_admin_controller():
    # We call the override_get_db function to get a test session
    for db in override_get_db():
        # Instantiate the controller correctly and yield it
        yield AdminController(db) 

# Apply the override to the FastAPI app for the duration of the tests
app.dependency_overrides[get_admin_controller] = override_get_admin_controller

client = TestClient(app)

# --- GLOBAL VARIABLES FOR TESTING ---

# A known good user for authentication
TEST_ADMIN_USERNAME = "testadmin"
TEST_ADMIN_PASSWORD = "securepassword" 
# A variable to store the JWT after successful login
AUTH_TOKEN = None 
# A variable to store the ID of an admin created during tests
CREATED_ADMIN_ID = None

# --- UTILITY FUNCTION ---
def get_auth_header():
    """Returns the Authorization header dictionary."""
    if AUTH_TOKEN is None:
        raise ValueError("AUTH_TOKEN is not set. Run the login test first.")
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}


# =========================================================================
# 1. AUTHENTICATION TESTS (Public Endpoints)
# =========================================================================

def test_1_admin_login_success():
    """Test successful admin login and store the token globally."""
    global AUTH_TOKEN
    response = client.post(
        "/admin/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Store the token for subsequent tests
    AUTH_TOKEN = data["access_token"]


def test_2_admin_login_incorrect_password():
    """Test login failure with incorrect password."""
    response = client.post(
        "/admin/login",
        json={"username": TEST_ADMIN_USERNAME, "password": "wrong password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password" # Match your controller error message


def test_3_admin_login_non_existent_user():
    """Test login failure with a non-existent username (should also return 401)."""
    response = client.post(
        "/admin/login",
        json={"username": "ghost_admin_12345", "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


# =========================================================================
# 2. SECURED ADMIN MANAGEMENT TESTS
# =========================================================================

def test_4_read_admin_me_unauthorized():
    """Test access to a secured endpoint without a token."""
    response = client.get("/admin/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_5_read_admin_me_success():
    """Test access to a secured endpoint with a valid token."""
    response = client.get("/admin/me", headers=get_auth_header())
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == TEST_ADMIN_USERNAME
    assert data["role"] == "admin"
    assert "admin_id" in data


def test_6_create_new_admin_success():
    """Test creating a new admin account."""
    global CREATED_ADMIN_ID
    new_admin_data = {
        "username": "new_test_admin",
        "password": "newsecurepass",
        "email_phone": "new@example.com"
    }
    
    response = client.post("/admin/create", json=new_admin_data, headers=get_auth_header())
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_test_admin"
    assert data["role"] == "admin"
    assert uuid.UUID(data["admin_id"]) # Check if it's a valid UUID
    
    CREATED_ADMIN_ID = data["admin_id"] # Store ID for update/cleanup tests


def test_7_create_new_admin_conflict():
    """Test creating an admin with an existing username."""
    existing_admin_data = {
        "username": "new_test_admin", # Use the username created in test_6
        "password": "anypassword",
        "email_phone": "unique@example.com"
    }
    
    response = client.post("/admin/create", json=existing_admin_data, headers=get_auth_header())
    
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken."


def test_8_update_admin_success():
    """Test updating the details of the newly created admin."""
    update_data = {
        "username": "updated_test_admin",
        "email_phone": "updated@example.com"
    }
    
    response = client.put(
        f"/admin/{CREATED_ADMIN_ID}", 
        json=update_data, 
        headers=get_auth_header()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updated_test_admin"
    assert data["email_phone"] == "updated@example.com"

# =========================================================================
# 3. TECHNICAL ACCOUNT PROVISIONING TESTS
# =========================================================================

def test_9_provision_technical_account_success():
    """Test creating a new technical account via the admin endpoint."""
    tech_data = {
        "username": "tech_staff_1",
        "password": "techpass",
        "name": "Tech One",
        "phone_number": "+12345678900"
    }
    
    response = client.post("/admin/technical", json=tech_data, headers=get_auth_header())
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "tech_staff_1"
    assert data["role"] == "technical"
    assert data["status"] == "free" # Assuming 'free' is the default status
    assert "technical_id" in data


def test_10_provision_technical_account_conflict():
    """Test creating a technical account using an existing admin username."""
    conflict_data = {
        "username": TEST_ADMIN_USERNAME, # Use existing admin username
        "password": "pass",
        "name": "Conflict",
        "phone_number": "+11122233344"
    }
    
    response = client.post("/admin/technical", json=conflict_data, headers=get_auth_header())
    
    assert response.status_code == 409
    assert response.json()["detail"] == "Username taken."