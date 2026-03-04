from fastapi.testclient import TestClient
from decimal import Decimal
from src.core.enums import ServiceType
from src.schemas.product import Service, Product, ServiceProductAssociation, ProductVehicleCompatibility, ServiceVehicleCompatibility

def test_intelligent_pricing_catalog(authenticated_admin_client: TestClient, db_session, test_vehicle_camry_2022):
    # 1. Create a product with price_adjustment
    product = Product(
        name="Castrol Edge 5W-30",
        selling_price=Decimal("10.00"),
        price_adjustment=Decimal("2.00"), # +$2 per unit for home service
        description="Premium Oil"
    )
    db_session.add(product)
    db_session.flush()

    # 2. Create a service with home/garage labor prices
    service = Service(
        name="Oil Change",
        description="Standard Oil Change",
        image_url="http://example.com/oil.jpg",
        garage_price=Decimal("30.00"),
        home_price=Decimal("50.00"),
        duration_minutes=30,
        is_available=True,
        service_type=ServiceType.HOME # This service is available for HOME
    )
    db_session.add(service)
    db_session.flush()

    # 3. Link product to service
    assoc = ServiceProductAssociation(
        service_id=service.service_id,
        product_id=product.product_id,
        quantity_required=1, # Base quantity
    )
    db_session.add(assoc)

    # 4. Define car-specific quantity (4.5L)
    compat = ProductVehicleCompatibility(
        product_id=product.product_id,
        vehicle_id=test_vehicle_camry_2022.vehicle_id,
        quantity_required="4.5L"
    )
    db_session.add(compat)

    # 5. Make service compatible with this vehicle
    svc_compat = ServiceVehicleCompatibility(
        service_id=service.service_id,
        vehicle_id=test_vehicle_camry_2022.vehicle_id
    )
    db_session.add(svc_compat)
    db_session.commit()

    # 6. Test the Catalog Endpoint for HOME service
    params = {
        "model_id": test_vehicle_camry_2022.model_id,
        "year": test_vehicle_camry_2022.year,
        "engine": test_vehicle_camry_2022.engine,
        "service_type": "Home"
    }
    response = authenticated_admin_client.get("/service/catalog", params=params)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    estimate = data[0]

    # Math Check:
    # Labor (Home): 50.00
    # Product (Home): (10.00 + 2.00) * 4.5 = 12.00 * 4.5 = 54.00
    # Total: 50.00 + 54.00 = 104.00
    assert Decimal(str(estimate["base_labor_price"])) == Decimal("50.00")
    assert Decimal(str(estimate["total_estimated_price"])) == Decimal("104.00")
    assert float(estimate["products"][0]["quantity_required"]) == 4.5

def test_admin_creation_magic_link(authenticated_admin_client: TestClient):
    payload = {
        "username": "newadmin_test",
        "password": "securepassword123",
        "email_phone": "newadmin@example.com"
    }
    response = authenticated_admin_client.post("/admin/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "telegram_magic_link" in data
    assert "start=admin_" in data["telegram_magic_link"]

def test_technical_creation_magic_link(authenticated_admin_client: TestClient):
    payload = {
        "username": "tech_test_user",
        "password": "techpassword123",
        "name": "John Technician",
        "phone_number": "+19998887776"
    }
    response = authenticated_admin_client.post("/admin/technical", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "telegram_magic_link" in data
    assert "start=tech_" in data["telegram_magic_link"]

def test_slideshow_workflow(authenticated_admin_client: TestClient, client: TestClient, db_session):
    # 1. Create a slide (Admin)
    payload = {
        "image_url": "http://example.com/garage_banner.jpg",
        "service_type": "Garage"
    }
    response = authenticated_admin_client.post("/slideshow/", json=payload)
    assert response.status_code == 201
    slide_id = response.json()["id"]

    # 2. Get slides (Public)
    get_response = client.get("/slideshow/Garage")
    assert get_response.status_code == 200
    data = get_response.json()
    assert len(data) >= 1
    assert any(s["image_url"] == "http://example.com/garage_banner.jpg" for s in data)

    # 3. Create slide unauthorized (Public should fail)
    from src.app.app import app
    from src.config.database import get_db
    # Create a fresh client and MANUALLY ensure it uses the test DB but has NO other overrides
    unauth_client = TestClient(app)
    unauth_client.app.dependency_overrides[get_db] = lambda: db_session
    
    # We must ENSURE get_current_admin_user is NOT overridden for this specific client instance
    # but since dependency_overrides is GLOBAL to the 'app' object, we temporarily clear it
    from src.dependency.auth import get_current_admin_user
    original_override = app.dependency_overrides.get(get_current_admin_user)
    if get_current_admin_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_admin_user]
    
    try:
        fail_response = unauth_client.post("/slideshow/", json=payload)
        assert fail_response.status_code == 401
    finally:
        # Restore for other tests
        if original_override:
            app.dependency_overrides[get_current_admin_user] = original_override

    # 4. Delete slide (Admin)
    del_response = authenticated_admin_client.delete(f"/slideshow/{slide_id}")
    assert del_response.status_code == 204

    # 5. Verify deleted
    after_del = client.get("/slideshow/Garage")
    assert not any(s["id"] == slide_id for s in after_del.json())
