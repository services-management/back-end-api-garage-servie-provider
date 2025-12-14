from fastapi.testclient import TestClient
from src.app.app import app
# --- NEW GLOBAL VARIABLE FOR TECHNICAL STAFF ---

client = TestClient(app)
TECH_AUTH_TOKEN = None 
TECH_USERNAME = "tech_staff_1" # Must match the user created in test_9
TECH_PASSWORD = "techpass"     # Must match the password used in test_9

# --- UTILITY FUNCTION ---
def get_tech_auth_header():
    """Returns the Authorization header dictionary for the Technical user."""
    if TECH_AUTH_TOKEN is None:
        raise ValueError("TECH_AUTH_TOKEN is not set. Run the technical login test first.")
    return {"Authorization": f"Bearer {TECH_AUTH_TOKEN}"}

# ... (Continue from Test 10 in the Admin section) ...
# =========================================================================
# 4. TECHNICAL AUTHENTICATION & SELF-MANAGEMENT TESTS
# =========================================================================

def test_11_technical_login_success():
    """Test successful technical staff login and store the token."""
    global TECH_AUTH_TOKEN
    response = client.post(
        "/technical/login", # Use the correct technical login route
        json={"username": TECH_USERNAME, "password": TECH_PASSWORD},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Store the token for subsequent technical tests
    TECH_AUTH_TOKEN = data["access_token"]


def test_12_read_technical_me_unauthorized():
    """Test access to a secured technical endpoint without a token."""
    response = client.get("/technical/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_13_read_technical_me_success():
    """Test access to the secured technical 'me' endpoint."""
    response = client.get("/technical/me", headers=get_tech_auth_header())
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == TECH_USERNAME
    assert data["role"] == "technical"
    assert data["status"] == "free" # Default status check
    assert "technical_id" in data


def test_14_update_technical_details_success():
    """Test updating the name and phone number of the technical user."""
    update_data = {
        "name": "Tech Staff Updated",
        "phone_number": "+98765432100", # New valid phone number
        # Note: Username/Password/Status can also be tested here if allowed
    }
    
    response = client.put(
        "/technical/me", # Using the /me route for self-update
        json=update_data, 
        headers=get_tech_auth_header()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tech Staff Updated"
    assert data["phone_number"] == "+98765432100"


def test_15_update_technical_status_success():
    """Test updating only the operational status."""
    status_data = {"status": "busy"} # Valid status from your Enum
    
    response = client.patch(
        "/technical/me/status", # Using the dedicated status update route
        json=status_data,
        headers=get_tech_auth_header()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "busy"
    
    # Check that the Admin can't use this route (Authorization Test)
    response_admin = client.patch(
        "/technical/me/status",
        json={"status": "off_duty"},
        headers=get_auth_header() # Using the Admin's token
    )
    # The technical endpoint should typically reject an admin token (403 or 401)
    # If your security dependency 'get_current_technical_user' checks the role, 
    # this will correctly fail with a 401/403.
    assert response_admin.status_code in [401, 403]