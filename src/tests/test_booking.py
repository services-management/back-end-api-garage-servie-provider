import pytest
from datetime import date, time, timedelta
from src.dependency.auth import get_current_customer
from src.models.user_model import UserResponse
from uuid import uuid4
from datetime import datetime, timezone

def test_create_guest_booking_schema_validation(client, test_service):
    """
    Focus: API Contract
    Verifies that a guest can hit the endpoint and the response follows the schema.
    """
    booking_data = {
        "phone": "+1234567890",
        "full_name": "Guest User",
        "car_make": "Toyota",
        "car_model": "Camry",
        "car_year": 2022,
        "items": [{"service_id": test_service.service_id, "quantity": 1}],
        "appointment_date": str(date.today() + timedelta(days=1)),
        "start_time": "10:00:00",
        "service_location": "123 Test St",
        "source": "Web"
    }
    
    response = client.post("/bookings/", json=booking_data)
    assert response.status_code == 201
    data = response.json()
    assert "booking" in data
    assert "telegram_link" in data

def test_create_booking_missing_fields(client):
    """Focus: Validation Error (Missing car_make)"""
    booking_data = {
        "phone": "+1234567890",
        "items": [{"service_id": 1, "quantity": 1}],
        "appointment_date": str(date.today() + timedelta(days=1)),
        "start_time": "10:00:00",
        "service_location": "123 Test St",
        "source": "Web"
    }
    response = client.post("/bookings/", json=booking_data)
    assert response.status_code == 422

def test_get_booking_history_unauthorized(client):
    """Focus: Auth Guard"""
    from src.app.app import app
    # Ensure no override exists
    if get_current_customer in app.dependency_overrides:
        del app.dependency_overrides[get_current_customer]
    
    response = client.get("/bookings/history")
    assert response.status_code == 401

def test_get_booking_history_success(client, db_session):
    """Focus: Auth Routing"""
    from src.app.app import app
    from src.schemas.booking import User, UserStatus
    
    user_id = uuid4()
    db_user = User(user_id=user_id, phone="+9998887776", role=UserStatus.ACTIVE, is_active=True)
    db_session.add(db_user)
    db_session.commit()

    app.dependency_overrides[get_current_customer] = lambda: UserResponse(
        user_id=user_id, phone="+9998887776", full_name="Auth User", 
        is_active=True, created_at=datetime.now(timezone.utc), last_login=None
    )
    
    try:
        response = client.get("/bookings/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.clear()

def test_create_booking_past_date(client, test_service):
    """Focus: Business Rule Validation (Pydantic level)"""
    booking_data = {
        "phone": "+1234567890",
        "car_make": "Toyota",
        "car_model": "Camry",
        "items": [{"service_id": test_service.service_id, "quantity": 1}],
        "appointment_date": str(date.today() - timedelta(days=1)),
        "start_time": "10:00:00",
        "service_location": "123 Test St",
        "source": "Web"
    }
    response = client.post("/bookings/", json=booking_data)
    assert response.status_code == 422
    assert "Date must be today or in the future" in response.text
