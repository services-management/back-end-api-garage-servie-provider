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