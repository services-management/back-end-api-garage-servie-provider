from fastapi.testclient import TestClient

# Test creating a service
def test_create_service_success(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Test Service New",
            "description": "A service for testing",
            "image_url": "http://example.com/service.png",
            "garage_price": 100.0,
            "home_price": 150.0,
            "duration_minutes": 60,
            "is_available": True,
            "service_type": "Garage",
            "associations": [],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Service New"
    assert data["garage_price"] == "100.00"
    assert data["home_price"] == "150.00"
    assert "service_id" in data

def test_create_service_invalid_price(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Test Service Invalid",
            "description": "A service for testing",
            "image_url": "http://example.com/service.png",
            "garage_price": -100.0,
            "home_price": 150.0,
            "duration_minutes": 60,
            "is_available": True,
            "associations": [],
        },
    )
    assert response.status_code == 422  # pydantic validation error

def test_create_service_unauthenticated(client: TestClient):
    response = client.post(
        "/service/",
        json={
            "name": "Test Service Unauthenticated",
            "description": "A service for testing",
            "image_url": "http://example.com/service.png",
            "garage_price": 100.0,
            "home_price": 150.0,
            "duration_minutes": 60,
            "is_available": True,
            "associations": [],
        },
    )
    assert response.status_code == 401

def test_create_service_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.post(
        "/service/",
        json={
            "name": "Test Service as Technical",
            "description": "A service for testing",
            "image_url": "http://example.com/service.png",
            "garage_price": 100.0,
            "home_price": 150.0,
            "duration_minutes": 60,
            "is_available": True,
            "associations": [],
        },
    )
    assert response.status_code == 401  # Forbidden


# Test getting a service
def test_get_service_success(client: TestClient, authenticated_admin_client: TestClient):
    # Create a service first
    create_response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Service to Get Unique",
            "description": "A service for getting",
            "image_url": "http://example.com/get_service.png",
            "garage_price": 200.0,
            "home_price": 250.0,
            "duration_minutes": 120,
            "is_available": True,
            "associations": [],
        },
    )
    assert create_response.status_code == 201
    service_id = create_response.json()["service_id"]

    # Get the service
    get_response = authenticated_admin_client.get(f"/service/{service_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["name"] == "Service to Get Unique"
    assert data["service_id"] == service_id

def test_get_service_not_found(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.get("/service/999999")
    assert response.status_code == 404

# Test getting all services
def test_get_all_services(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.get("/service/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test getting available services
def test_get_available_services(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.get("/service/available/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    for service in response.json():
        assert service["is_available"] is True

def test_filter_services_by_vehicle(authenticated_admin_client: TestClient, db_session):
    from src.schemas.vehicle import Make, Model, Vehicle
    from src.schemas.product import Service, ServiceVehicleCompatibility
    from src.core.enums import VehicleType, FuelType, DriveType, TransmissionType
    from decimal import Decimal

    # Setup: Create a make, model, vehicle, service, and link them
    make = Make(name="TestMakeFilter")
    db_session.add(make)
    db_session.flush()

    model = Model(name="TestModelFilter", make_id=make.id)
    db_session.add(model)
    db_session.flush()

    vehicle = Vehicle(
        model_id=model.id,
        year=2024,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.GASOLINE,
        drive_type=DriveType.FWD,
        transmission=TransmissionType.AUTOMATIC
    )
    db_session.add(vehicle)
    db_session.flush()

    service = Service(
        name="Filterable Service Unique",
        description="Filterable",
        image_url="http://example.com/img.png",
        garage_price=Decimal("50.00"),
        home_price=Decimal("70.00"),
        duration_minutes=30,
        is_available=True
    )
    db_session.add(service)
    db_session.flush()

    link = ServiceVehicleCompatibility(service_id=service.service_id, vehicle_id=vehicle.vehicle_id)
    db_session.add(link)
    db_session.commit()

    # Test the filter
    params = {
        "make": "TestMakeFilter",
        "model": "TestModelFilter",
        "year": 2024
    }
    response = authenticated_admin_client.get("/service/filter-by-vehicle", params=params)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "Filterable Service Unique"

# Test updating a service
def test_update_service_success(authenticated_admin_client: TestClient):
    # Create a service
    create_response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Service to Update Unique",
            "description": "A service for updating",
            "image_url": "http://example.com/update_service.png",
            "garage_price": 300.0,
            "home_price": 350.0,
            "duration_minutes": 180,
            "is_available": True,
            "associations": [],
        },
    )
    assert create_response.status_code == 201
    service_id = create_response.json()["service_id"]

    # Update the service
    update_response = authenticated_admin_client.put(
        f"/service/{service_id}",
        json={"name": "Updated Service Name Unique", "garage_price": 350.0},
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Service Name Unique"
    assert data["garage_price"] == "350.00"

def test_update_service_not_found(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.put(
        "/service/999999",
        json={"name": "Won't Update"},
    )
    assert response.status_code == 404

def test_update_service_unauthenticated(client: TestClient):
    response = client.put(
        "/service/1",
        json={"name": "Won't Update"},
    )
    assert response.status_code == 401


# Test deleting a service
def test_delete_service_success(authenticated_admin_client: TestClient):
    # Create a service
    create_response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Service to Delete Unique",
            "description": "A service for deleting",
            "image_url": "http://example.com/delete_service.png",
            "garage_price": 400.0,
            "home_price": 450.0,
            "duration_minutes": 240,
            "is_available": True,
            "associations": [],
        },
    )
    assert create_response.status_code == 201
    service_id = create_response.json()["service_id"]

    # Delete the service
    delete_response = authenticated_admin_client.delete(f"/service/{service_id}")
    assert delete_response.status_code == 204

    # Verify it's soft deleted (status=Deleted, is_available=False)
    get_response = authenticated_admin_client.get(f"/service/{service_id}")
    # Depending on your controller, get_service might still return it or hide it.
    # If it's 404, then it's hidden. 
    assert get_response.status_code == 404

def test_delete_service_not_found(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.delete("/service/999999")
    assert response.status_code == 404

def test_delete_service_unauthenticated(client: TestClient):
    response = client.delete("/service/1")
    assert response.status_code == 401

def test_delete_service_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.delete("/service/1")
    assert response.status_code == 401
