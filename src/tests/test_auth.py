
import pytest

from src.repositories.admin_repositories import AdminRepository
from src.utils.hash_password import hash_password


@pytest.fixture(scope="function")
def admin_user(db_session):
    admin_repo = AdminRepository(db_session)
    user = admin_repo.create(
        username="testadmin",
        password=hash_password("securepassword"),
        email_phone="admin@example.com",
    )
    return user

@pytest.fixture
def authenticated_admin_client(client, admin_user):
    response = client.post(
        "/admin/login",
        json={"username": "testadmin", "password": "securepassword"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture
def technical_user(db_session):
    from src.repositories.technical_repositorie import TechnicalRepository
    tech_repo = TechnicalRepository(db_session)
    user = tech_repo.create(
        username="tech_staff_1",
        password=hash_password("techpass"),
        name="Tech One",
        phone_number="+12345678900",
    )
    return user

@pytest.fixture
def authenticated_technical_client(client, technical_user):
    response = client.post(
        "/technical/login",
        json={"username": "tech_staff_1", "password": "techpass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client

# ==================== OTP Authentication Tests ====================

@pytest.fixture
def otp_user(db_session):
    """Create a user for OTP testing."""
    from src.repositories.user_respositories import UserRepository
    user_repo = UserRepository(db_session)
    user = user_repo.create_shadow_account(
        phone="+1234567890",
        full_name="OTP Test User"
    )
    return user

def test_request_otp_success(client, otp_user):
    """Test requesting OTP for a valid user."""
    response = client.post(
        "/auth/otp/request",
        json={"phone": "+1234567890"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "OTP sent successfully."

def test_request_otp_user_not_found(client):
    """Test requesting OTP for non-existent user."""
    response = client.post(
        "/auth/otp/request",
        json={"phone": "+9999999999"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_verify_otp_success(client, db_session):
    """Test verifying correct OTP within time limit."""
    from src.schemas.otp import OTP as OTPModel
    from src.repositories.user_respositories import UserRepository
    
    # Create a fresh user for this test
    user_repo = UserRepository(db_session)
    user_repo.create_shadow_account(
        phone="+1111111111",
        full_name="OTP Verify Test User"
    )
    
    # Request OTP first
    response = client.post(
        "/auth/otp/request",
        json={"phone": "+1111111111"}
    )
    assert response.status_code == 200
    
    # Get the OTP from database
    otp_record = db_session.query(OTPModel).filter(
        OTPModel.phone == "+1111111111",
        OTPModel.is_used.is_(False)
    ).order_by(OTPModel.created_at.desc()).first()
    
    assert otp_record is not None, "OTP should exist in database"
    
    # Verify the OTP
    response = client.post(
        "/auth/otp/verify",
        json={
            "phone": "+1111111111",
            "otp_code": otp_record.otp_code
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_verify_otp_invalid_code(client, otp_user):
    """Test verifying with wrong OTP code."""
    # Request OTP
    client.post(
        "/auth/otp/request",
        json={"phone": "+1234567890"}
    )
    
    # Try wrong OTP
    response = client.post(
        "/auth/otp/verify",
        json={
            "phone": "+1234567890",
            "otp_code": "000000"
        }
    )
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()

def test_verify_otp_already_used(client, db_session):
    """Test that OTP cannot be reused."""
    from src.schemas.otp import OTP as OTPModel
    from src.repositories.user_respositories import UserRepository
    
    # Create a fresh user for this test
    user_repo = UserRepository(db_session)
    user_repo.create_shadow_account(
        phone="+2222222222",
        full_name="OTP Reuse Test User"
    )
    
    # Request OTP
    client.post(
        "/auth/otp/request",
        json={"phone": "+2222222222"}
    )
    
    # Get OTP from database
    otp_record = db_session.query(OTPModel).filter(
        OTPModel.phone == "+2222222222",
        OTPModel.is_used.is_(False)
    ).order_by(OTPModel.created_at.desc()).first()
    
    assert otp_record is not None, "OTP should exist"
    
    # First verification - should succeed
    response1 = client.post(
        "/auth/otp/verify",
        json={
            "phone": "+2222222222",
            "otp_code": otp_record.otp_code
        }
    )
    assert response1.status_code == 200, f"First verification failed: {response1.json()}"
    
    # Second verification with same OTP - should fail
    response2 = client.post(
        "/auth/otp/verify",
        json={
            "phone": "+2222222222",
            "otp_code": otp_record.otp_code
        }
    )
    assert response2.status_code == 400
    assert "invalid or expired" in response2.json()["detail"].lower()