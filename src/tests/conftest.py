import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

# 1. Set test mode and mock slow startup logic BEFORE importing the app
os.environ["TESTING"] = "True"

from src.app.app import app
from src.config.database import Base, get_db
from src.schemas.admin import adminModel
from src.schemas.product import Product, Category, Service, Inventory
from src.schemas.vehicle import Make, Model, Vehicle, VehicleType, FuelType, DriveType, TransmissionType
from src.schemas.techincal import TechnicalModel, TechnicalTeam
from src.schemas.booking import User, UserStatus, Booking, BookingStatus, BookingSource

# We mock the startup events to prevent network calls to Telegram and DB init during tests
@pytest.fixture(scope="session", autouse=True)
def mock_app_startup():
    with patch("src.app.app.init_db"), \
         patch("httpx.AsyncClient.post") as mock_post:
        # Mock Telegram webhook response
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"ok": True}
        yield

# 2. Mock slow bcrypt hashing (Huge speedup)
@pytest.fixture(scope="session", autouse=True)
def mock_bcrypt():
    with patch("bcrypt.hashpw", side_effect=lambda pw, salt: pw), \
         patch("bcrypt.checkpw", side_effect=lambda pw, hashed: pw == hashed), \
         patch("bcrypt.gensalt", return_value=b"salt"):
        yield

# 3. Optimized Database Setup
@pytest.fixture(scope="session")
def engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine, tables):
    """Transaction-based session: very fast as it rolls back instead of recreating tables."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with injected test session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# --- Re-use existing fixtures for Admin/Technical/Data ---
@pytest.fixture(scope="function")
def admin_user(db_session):
    from src.utils.hash_password import hash_password
    admin = adminModel(
        username="testadmin", 
        password=hash_password("securepassword"), 
        role="admin", 
        email_phone="admin@example.com",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    response = client.post("/admin/login", json={"username": "testadmin", "password": "securepassword"})
    return response.json()["access_token"]

@pytest.fixture(scope="function")
def authenticated_admin_client(client, admin_token):
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client

@pytest.fixture(scope="function")
def technical_user(db_session):
    from src.utils.hash_password import hash_password
    tech = TechnicalModel(
        username="tech_staff_1", 
        password=hash_password("techpass"), 
        name="Tech One", 
        phone_number="+12345678900", 
        role="technical", 
        status="free",
        is_active=True
    )
    db_session.add(tech)
    db_session.commit()
    db_session.refresh(tech)
    return tech

@pytest.fixture(scope="function")
def technical_token(client, technical_user):
    response = client.post("/technical/login", json={"username": "tech_staff_1", "password": "techpass"})
    return response.json()["access_token"]

@pytest.fixture(scope="function")
def authenticated_technical_client(client, technical_token):
    client.headers["Authorization"] = f"Bearer {technical_token}"
    return client

@pytest.fixture(scope="function")
def test_category(db_session):
    category = Category(name="Test Category", description="Test category")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category

@pytest.fixture(scope="function")
def test_product(db_session, test_category):
    from src.schemas.product import ProductStatus
    from decimal import Decimal
    from datetime import date
    product = Product(
        name="Test Product",
        selling_price=Decimal("29.99"),
        unit_cost=Decimal("19.99"),
        category_id=test_category.categoryID,
        description="A test product",
        status=ProductStatus.ACTIVE
    )
    db_session.add(product)
    db_session.flush()
    
    # Create inventory for the product to avoid 404 in inventory tests
    inventory = Inventory(
        product_id=product.product_id,
        current_stock=Decimal("50.0"),
        min_stock_level=Decimal("10.0"),
        last_restock_date=date.today()
    )
    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(product)
    return product

@pytest.fixture(scope="function")
def test_service(db_session):
    from decimal import Decimal
    service = Service(
        name="Oil Change Test",
        description="Desc",
        image_url="http://ex.com/img.jpg",
        garage_price=Decimal("50.00"),
        home_price=Decimal("70.00"),
        duration_minutes=60,
        is_available=True
    )

    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service

@pytest.fixture(scope="function")
def test_team(db_session):
    team = TechnicalTeam(team_name="Test Team Alpha", description="Test Description", is_active=True)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team

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
def test_user(db_session):
    user = User(
        phone="+1234567890", 
        full_name="Test User", 
        role=UserStatus.ACTIVE, 
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_booking(db_session, test_user):
    from decimal import Decimal
    from datetime import date, time
    booking = Booking(
        user_id=test_user.user_id,
        contact_phone=test_user.phone,
        car_make="Toyota",
        car_model="Camry",
        appointment_date=date.today(),
        start_time=time(10, 0),
        service_location="Test Location",
        source=BookingSource.WEB,
        status=BookingStatus.PENDING,
        total_price=Decimal("50.00")
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking
