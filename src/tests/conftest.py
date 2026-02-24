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
from src.schemas.product import Product, Category, ProductVehicleCompatibility
from src.schemas.vehicle import Make, Model, Vehicle, VehicleType, FuelType, DriveType, TransmissionType
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
        category_id=test_category.categoryID,
        description="A test product",
        status="active"
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
            category_id=test_category.categoryID,
            description=f"Test product {i}",
            status="active"
        )
        db_session.add(product)
        products.append(product)
    
    db_session.commit()
    for product in products:
        db_session.refresh(product)
    
    return products

# ---------- Vehicle Test Data Fixtures ----------

@pytest.fixture(scope="function")
def test_make_toyota(db_session):
    make = Make(name="Toyota", is_active=True)
    db_session.add(make)
    db_session.commit()
    db_session.refresh(make)
    return make

@pytest.fixture(scope="function")
def test_model_camry(db_session, test_make_toyota):
    model = Model(name="Camry", make_id=test_make_toyota.id, make=test_make_toyota, is_active=True)
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model

@pytest.fixture(scope="function")
def test_vehicle_camry_2022(db_session, test_model_camry):
    vehicle = Vehicle(
        model_id=test_model_camry.id,
        year=2022,
        engine="2.5L I4",
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.GASOLINE,
        drive_type=DriveType.FWD,
        transmission=TransmissionType.AUTOMATIC,
        is_active=True,
        model=test_model_camry
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle

@pytest.fixture(scope="function")
def test_product_compatible_with_camry(db_session, test_product, test_vehicle_camry_2022):
    # Ensure test_product has been created
    db_session.refresh(test_product)

    compatibility = ProductVehicleCompatibility(
        product_id=test_product.product_id,
        vehicle_id=test_vehicle_camry_2022.vehicle_id,
        quantity_required="1 unit",
        note="Perfect fit"
    )
    db_session.add(compatibility)
    db_session.commit()
    db_session.refresh(compatibility)
    return compatibility

@pytest.fixture(scope="function")
def test_make_honda(db_session):
    make = Make(name="Honda", is_active=True)
    db_session.add(make)
    db_session.commit()
    db_session.refresh(make)
    return make

@pytest.fixture(scope="function")
def test_model_civic(db_session, test_make_honda):
    model = Model(name="Civic", make_id=test_make_honda.id, make=test_make_honda, is_active=True)
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model

@pytest.fixture(scope="function")
def test_vehicle_civic_2023(db_session, test_model_civic):
    vehicle = Vehicle(
        model_id=test_model_civic.id,
        year=2023,
        engine="1.5L Turbo",
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.GASOLINE,
        drive_type=DriveType.FWD,
        transmission=TransmissionType.CVT,
        is_active=True,
        model=test_model_civic
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle

@pytest.fixture(scope="function")
def another_test_product(db_session, test_category):
    product = Product(
        name="Honda Specific Part",
        selling_price=50.00,
        unit_cost=25.00,
        category_id=test_category.categoryID,
        description="A part for Honda vehicles",
        status="active"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product

@pytest.fixture(scope="function")
def test_product_compatible_with_civic(db_session, another_test_product, test_vehicle_civic_2023):
    db_session.refresh(another_test_product)
    compatibility = ProductVehicleCompatibility(
        product_id=another_test_product.product_id,
        vehicle_id=test_vehicle_civic_2023.vehicle_id,
        quantity_required="1 unit",
        note="Specific to Civic"
    )
    db_session.add(compatibility)
    db_session.commit()
    db_session.refresh(compatibility)
    return compatibility