import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool  # Import StaticPool

# Set test mode BEFORE importing app
os.environ["TESTING"] = "True"

from src.app.app import app
from src.config.database import Base, get_db
from src.utils.hash_password import hash_password

# Import models
from src.schemas.admin import adminModel
from src.schemas.product import Product, Category
from src.schemas.techincal import TechnicalModel


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)



# ---------- FastAPI TestClient Fixture ----------
@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with in-memory database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ---------- Admin Fixtures ----------
@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user in the test database."""
    
    # Based on the Pydantic warning, the attribute is 'email_phone' (lowercase)
    admin = adminModel(
        username="testadmin",
        password=hash_password("securepassword"),
        role="admin",
        email_phone="admin@example.com"  # lowercase 'e'
    )
    
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    return admin


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """Get admin JWT token."""
    response = client.post("/admin/login", json={
        "username": "testadmin", 
        "password": "securepassword"
    })
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="function")
def authenticated_admin_client(client, admin_token):
    """Test client with admin authentication."""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client


# ---------- Technical Fixtures ----------
@pytest.fixture(scope="function")
def technical_user(db_session):
    """Create a technical user in the test database."""
    
    tech = TechnicalModel(
        username="tech_staff_1",
        password=hash_password("techpass"),
        name="Tech One",
        phone_number="+12345678900",
        role="technical",
        status="free"
    )
    
    db_session.add(tech)
    db_session.commit()
    db_session.refresh(tech)
    
    return tech


@pytest.fixture(scope="function")
def technical_token(client, technical_user):
    """Get technical user JWT token."""
    response = client.post("/technical/login", json={
        "username": "tech_staff_1",
        "password": "techpass"
    })
    assert response.status_code == 200
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="function")
def authenticated_technical_client(client, technical_token):
    """Test client with technical user authentication."""
    client.headers["Authorization"] = f"Bearer {technical_token}"
    return client

# ---------- Product Test Data Fixtures ----------

@pytest.fixture(scope="function")
def test_category(db_session):
    """Create a test category."""
    
    category = Category(
        name="Test Category",
        description="Test category for products"
    )
    
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    
    return category


@pytest.fixture(scope="function")
def test_product(db_session, test_category):
    """Create a test product."""
    
    product = Product(
        name="Test Product",
        selling_price=29.99,
        unit_cost=19.99,
        category_id=test_category.category_id,
        description="A test product",
        status="active",
        initial_stock=100.0,
        current_stock=100.0,
        min_stock_level=10.0
    )
    
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    
    return product


@pytest.fixture(scope="function")
def multiple_test_products(db_session, test_category):
    """Create multiple test products."""
    
    products = []
    for i in range(5):
        product = Product(
            name=f"Test Product {i}",
            selling_price=10.00 + i,
            unit_cost=5.00 + i,
            category_id=test_category.category_id,
            description=f"Test product {i}",
            status="active",
            initial_stock=50.0,
            current_stock=50.0,
            min_stock_level=5.0
        )
        db_session.add(product)
        products.append(product)
    
    db_session.commit()
    for product in products:
        db_session.refresh(product)
    
    return products