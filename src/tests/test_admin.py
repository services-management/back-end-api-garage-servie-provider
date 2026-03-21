import uuid
from sqlalchemy.orm import Session
from src.repositories.admin_repositories import AdminRepository
from src.models.admin_model import AdminCreate

# --- Repository Unit Tests ---

def test_repo_create_default_admin_is_active(db_session: Session):
    """Unit test: Verify create_default_admin sets is_active=True."""
    repo = AdminRepository(db_session)
    username = "super_admin_test_repo"
    password = "password123"
    email = "super_repo@test.com"
    
    admin = repo.create_default_admin(username, password, email)
    
    assert admin is not None
    assert admin.username == username
    assert admin.is_active is True

def test_repo_create_new_admin_is_active(db_session: Session):
    """Unit test: Verify the regular create method sets is_active=True."""
    repo = AdminRepository(db_session)
    admin_in = AdminCreate(
        username="new_admin_repo_test",
        password="securepassword123",
        email_phone="newadmin_repo@test.com"
    )
    hashed_password = "mock_hashed_password"
    
    admin = repo.create(admin_in, hashed_password)
    
    assert admin is not None
    assert admin.username == "new_admin_repo_test"
    assert admin.is_active is True

# --- Authentication & Login Tests ---

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
    assert "telegram_magic_link" in data
    assert "admin" in data["telegram_magic_link"]
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

    # Update it
    update_data = {
        "username": "updated_test_admin",
        "email_phone": "updated@example.com",
    }
    response = authenticated_admin_client.put("/admin/me", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updated_test_admin"
    assert data["email_phone"] == "updated@example.com"


# def test_update_admin_not_found(authenticated_admin_client):
#     """Test updating a non-existent admin."""
#     fake_admin_id = str(uuid.uuid4())
#     update_data = {
#         "username": "updated_test_admin",
#         "email_phone": "updated@example.com",
#     }
#     response = authenticated_admin_client.put(f"/admin/{fake_admin_id}", json=update_data)
#     assert response.status_code == 404
#     # assert response.json()["detail"] == "Admin not found"


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
    assert "telegram_magic_link" in data
    assert "tech" in data["telegram_magic_link"]
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


# --- Technical Team Management Tests ---

def test_create_technical_team_success(authenticated_admin_client):
    """Test creating a new technical team."""
    team_data = {
        "team_name": "Alpha Team",
        "description": "Specialized in engine repair"
    }
    response = authenticated_admin_client.post("/admin/teams", json=team_data)
    assert response.status_code == 201
    data = response.json()
    assert data["team_name"] == "Alpha Team"
    assert data["description"] == "Specialized in engine repair"
    assert "team_id" in data
    assert data["is_active"] is True


def test_list_technical_teams(authenticated_admin_client):
    """Test listing all technical teams."""
    # Create a team first
    team_data = {
        "team_name": "Gamma Team",
        "description": "Test team for listing"
    }
    authenticated_admin_client.post("/admin/teams", json=team_data)

    # List teams
    response = authenticated_admin_client.get("/admin/teams")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check that our created team is in the list
    team_names = [t["team_name"] for t in data]
    assert "Gamma Team" in team_names


def test_add_member_to_team(authenticated_admin_client):
    """Test adding a technical staff member to a team."""
    # 1. Create a team
    team_data = {
        "team_name": "Team With Members",
        "description": "Team for member testing"
    }
    team_response = authenticated_admin_client.post("/admin/teams", json=team_data)
    assert team_response.status_code == 201
    team_id = team_response.json()["team_id"]

    # 2. Create a technical staff member
    tech_data = {
        "username": "tech_for_team",
        "password": "techpassword123",
        "name": "Team Member Tech",
        "phone_number": "+19998887770"
    }
    tech_response = authenticated_admin_client.post("/admin/technical", json=tech_data)
    assert tech_response.status_code == 201
    technical_id = tech_response.json()["technical_id"]

    # 3. Add member to team
    response = authenticated_admin_client.post(f"/admin/teams/{team_id}/members/{technical_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["technical_id"] == technical_id
    assert data["team_id"] == team_id


def test_remove_member_from_team(authenticated_admin_client):
    """Test removing a technical staff member from a team."""
    # 1. Create a team
    team_data = {
        "team_name": "Team For Removal",
        "description": "Team for removal testing"
    }
    team_response = authenticated_admin_client.post("/admin/teams", json=team_data)
    assert team_response.status_code == 201
    team_id = team_response.json()["team_id"]

    # 2. Create a technical staff member
    tech_data = {
        "username": "tech_to_remove",
        "password": "techpassword123",
        "name": "Tech To Remove",
        "phone_number": "+19998887771"
    }
    tech_response = authenticated_admin_client.post("/admin/technical", json=tech_data)
    assert tech_response.status_code == 201
    technical_id = tech_response.json()["technical_id"]

    # 3. Add member to team first
    add_response = authenticated_admin_client.post(f"/admin/teams/{team_id}/members/{technical_id}")
    assert add_response.status_code == 200

    # 4. Remove member from team
    response = authenticated_admin_client.delete(f"/admin/teams/members/{technical_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["technical_id"] == technical_id
    # After removal, team_id should be None
    assert data["team_id"] is None


def test_add_member_to_team_not_found(authenticated_admin_client):
    """Test adding a non-existent member to a team returns 404."""
    # Create a team first
    team_data = {
        "team_name": "Team For Not Found",
        "description": "Team for not found testing"
    }
    team_response = authenticated_admin_client.post("/admin/teams", json=team_data)
    team_id = team_response.json()["team_id"]

    # Try to add non-existent technical
    fake_technical_id = "00000000-0000-0000-0000-000000000000"
    response = authenticated_admin_client.post(f"/admin/teams/{team_id}/members/{fake_technical_id}")
    assert response.status_code == 404