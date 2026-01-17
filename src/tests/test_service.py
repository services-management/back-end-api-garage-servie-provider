from fastapi.testclient import TestClient

# Test creating a service
def test_create_service_success(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Test Service",
            "description": "A service for testing",
            "image_url": "http://example.com/service.png",
            "price": 100.0,
            "duration_minutes": 60,
            "is_available": True,
            "associations": [],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Service"
    assert data["price"] == 100.0
    assert "service_id" in data

def test_create_service_invalid_price(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Test Service Invalid",
            "description": "A service for testing",
            "image_url": "http://example.com/service.png",
            "price": -100.0,
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
            "price": 100.0,
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
            "price": 100.0,
            "duration_minutes": 60,
            "is_available": True,
            "associations": [],
        },
    )
    assert response.status_code == 403  # Forbidden


# Test getting a service
def test_get_service_success(client: TestClient, authenticated_admin_client: TestClient):
    # Create a service first
    create_response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Service to Get",
            "description": "A service for getting",
            "image_url": "http://example.com/get_service.png",
            "price": 200.0,
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
    assert data["name"] == "Service to Get"
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

# Test updating a service
def test_update_service_success(authenticated_admin_client: TestClient):
    # Create a service
    create_response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Service to Update",
            "description": "A service for updating",
            "image_url": "http://example.com/update_service.png",
            "price": 300.0,
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
        json={"name": "Updated Service Name", "price": 350.0},
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Service Name"
    assert data["price"] == 350.0

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

def test_update_service_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.put(
        "/service/1",
        json={"name": "Won't Update"},
    )
    assert response.status_code == 403

# Test deleting a service
def test_delete_service_success(authenticated_admin_client: TestClient):
    # Create a service
    create_response = authenticated_admin_client.post(
        "/service/",
        json={
            "name": "Service to Delete",
            "description": "A service for deleting",
            "image_url": "http://example.com/delete_service.png",
            "price": 400.0,
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

    # Verify it's gone
    get_response = authenticated_admin_client.get(f"/service/{service_id}")
    assert get_response.status_code == 404

def test_delete_service_not_found(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.delete("/service/999999")
    assert response.status_code == 404

def test_delete_service_unauthenticated(client: TestClient):
    response = client.delete("/service/1")
    assert response.status_code == 401

def test_delete_service_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.delete("/service/1")
    assert response.status_code == 403
