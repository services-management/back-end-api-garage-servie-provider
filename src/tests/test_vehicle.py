import pytest
from src.schemas.vehicle import Make, Model, VehicleType, FuelType, DriveType, TransmissionType

@pytest.fixture
def test_make(db_session):
    make = Make(name="BMW", is_active=True)
    db_session.add(make)
    db_session.commit()
    db_session.refresh(make)
    return make

@pytest.fixture
def test_model(db_session, test_make):
    model = Model(name="X5", make_id=test_make.id, is_active=True)
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model

def test_get_makes_public(client, test_make):
    response = client.get("/vehicles/makes")
    assert response.status_code == 200
    assert any(m["name"] == "BMW" for m in response.json())

def test_get_models_by_make_public(client, test_make, test_model):
    response = client.get(f"/vehicles/makes/{test_make.id}/models")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "X5"

def test_search_vehicles_public(client, test_vehicle_camry_2022, test_vehicle_civic_2023):
    # Search by model_id
    response = client.get(f"/vehicles/search?model_id={test_vehicle_camry_2022.model_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["year"] == 2022
    assert response.json()[0]["img_url"] == "http://example.com/camry.jpg"

    # Search by make_id (Camry belongs to Toyota)
    toyota_make_id = test_vehicle_camry_2022.model.make_id
    response = client.get(f"/vehicles/search?make_id={toyota_make_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["model"]["make"]["name"] == "Toyota"

    # Search by year
    response = client.get("/vehicles/search?year=2023")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["year"] == 2023

    # Search by engine (partial match)
    response = client.get("/vehicles/search?engine=Turbo")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "Turbo" in response.json()[0]["engine"]

    # Search by multiple criteria
    response = client.get(f"/vehicles/search?year=2022&vehicle_type={VehicleType.SEDAN.value}")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_create_make_admin(authenticated_admin_client):
    payload = {"name": "Audi"}
    response = authenticated_admin_client.post("/vehicles/make", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Audi"

def test_create_model_admin(authenticated_admin_client, test_make):
    payload = {"name": "Q7", "make": {"name": test_make.name}}
    response = authenticated_admin_client.post("/vehicles/model", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Q7"

def test_create_vehicle_admin(authenticated_admin_client, test_model):
    payload = {
        "model_id": test_model.id,
        "year": 2024,
        "engine": "3.0L V6",
        "img_url": "http://example.com/x5_2024.jpg",
        "vehicle_type": VehicleType.SUV.value,
        "fuel_type": FuelType.GASOLINE.value,
        "drive_type": DriveType.AWD.value,
        "transmission": TransmissionType.AUTOMATIC.value
    }
    response = authenticated_admin_client.post("/vehicles/", json=payload)
    assert response.status_code == 201
    assert response.json()["img_url"] == "http://example.com/x5_2024.jpg"
    assert response.json()["year"] == 2024

def test_get_all_vehicles_admin(authenticated_admin_client, test_vehicle_camry_2022):
    response = authenticated_admin_client.get("/vehicles/all")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    # Check if img_url is present in the list
    assert any(v["img_url"] == "http://example.com/camry.jpg" for v in response.json())

def test_update_make_admin(authenticated_admin_client, test_make):
    payload = {"name": "BMW Updated"}
    response = authenticated_admin_client.patch(f"/vehicles/make/{test_make.id}", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "BMW Updated"

def test_update_model_admin(authenticated_admin_client, test_model):
    payload = {"name": "X5 M"}
    response = authenticated_admin_client.patch(f"/vehicles/model/{test_model.id}", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "X5 M"

def test_delete_model_admin(authenticated_admin_client, test_model):
    response = authenticated_admin_client.delete(f"/vehicles/model/{test_model.id}")
    assert response.status_code == 204

def test_delete_make_admin(authenticated_admin_client, test_make):
    response = authenticated_admin_client.delete(f"/vehicles/make/{test_make.id}")
    assert response.status_code == 204

def test_update_vehicle_admin(authenticated_admin_client, test_vehicle_camry_2022):
    """Test updating vehicle details with partial data."""
    payload = {
        "year": 2023,
        "engine": "2.5L Turbo",
        "img_url": "http://example.com/camry_updated.jpg"
    }
    response = authenticated_admin_client.patch(
        f"/vehicles/{test_vehicle_camry_2022.vehicle_id}", 
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2023
    assert data["engine"] == "2.5L Turbo"
    assert data["img_url"] == "http://example.com/camry_updated.jpg"
    # Verify other fields remain unchanged
    assert data["vehicle_type"] == test_vehicle_camry_2022.vehicle_type.value
    assert data["model_id"] == test_vehicle_camry_2022.model_id

def test_update_vehicle_partial_fields(authenticated_admin_client, test_vehicle_civic_2023):
    """Test updating only one field of a vehicle."""
    payload = {"fuel_type": FuelType.HYBRID.value}
    response = authenticated_admin_client.patch(
        f"/vehicles/{test_vehicle_civic_2023.vehicle_id}", 
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fuel_type"] == FuelType.HYBRID.value
    # Verify other fields remain unchanged
    assert data["year"] == test_vehicle_civic_2023.year
    assert data["engine"] == test_vehicle_civic_2023.engine

def test_update_vehicle_not_found(authenticated_admin_client):
    """Test updating a non-existent vehicle."""
    payload = {"year": 2024}
    response = authenticated_admin_client.patch("/vehicles/99999", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_update_vehicle_empty_payload(authenticated_admin_client, test_vehicle_camry_2022):
    """Test updating vehicle with empty payload."""
    response = authenticated_admin_client.patch(
        f"/vehicles/{test_vehicle_camry_2022.vehicle_id}", 
        json={}
    )
    assert response.status_code == 400
    assert "no fields" in response.json()["detail"].lower()
