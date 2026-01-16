import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.app import app
from src.config.database import Base, get_db
from src.repositories.admin_repositories import AdminRepository
from src.utils.hash_password import hash_password

# Define a test database URL
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create a test database engine
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a test session class
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    db.begin_nested()  # start SAVEPOINT
    try:
        yield db
    finally:
        db.rollback()  # revert test changes
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """
    def override_get_db_for_client():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db_for_client
    with TestClient(app) as test_client:
        yield test_client
    # remove the override
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def admin_user(db_session):
    admin_repo = AdminRepository(db_session)
    user = admin_repo.create_admin(
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
    user = tech_repo.create_technical(
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