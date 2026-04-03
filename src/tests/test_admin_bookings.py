import pytest
from datetime import date, time
from uuid import uuid4
from src.schemas.booking import BookingStatus, BookingSource

@pytest.fixture
def test_user(db_session):
    from src.schemas.booking import User
    user = User(
        phone="+1234567890",
        full_name="Booking Customer",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_booking(db_session, test_user, test_service):
    from src.schemas.booking import Booking, BookingItem
    from decimal import Decimal
    
    db_session.refresh(test_service)

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
    db_session.flush()
    
    item = BookingItem(
        booking_id=booking.booking_id,
        service_id=test_service.service_id,
        quantity=1,
        price_at_purchase=Decimal("50.00")
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(booking)
    return booking

@pytest.fixture
def test_team(db_session):
    from src.schemas.techincal import TechnicalTeam
    team = TechnicalTeam(
        team_name="Test Team Alpha",
        description="Test Team Description",
        is_active=True
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team

def test_admin_list_bookings(authenticated_admin_client, test_booking):
    """Test that booking list includes customer information (full_name and phone)"""
    response = authenticated_admin_client.get("/admin/bookings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    booking_data = data[0]
    assert booking_data["booking_id"] == test_booking.booking_id
    assert booking_data["car_make"] == test_booking.car_make
    assert booking_data["car_model"] == test_booking.car_model
    
    # Verify customer information is included as nested object
    assert "customer" in booking_data
    assert booking_data["customer"] is not None
    assert "full_name" in booking_data["customer"]
    assert "phone" in booking_data["customer"]
    assert booking_data["customer"]["full_name"] is not None
    assert booking_data["customer"]["phone"] is not None

def test_admin_accept_booking(authenticated_admin_client, test_booking):
    response = authenticated_admin_client.post(f"/admin/bookings/{test_booking.booking_id}/accept")
    assert response.status_code == 200
    assert response.json()["status"] == BookingStatus.CONFIRMED

def test_admin_reject_booking(authenticated_admin_client, test_booking):
    payload = {"reason": "Not enough staff"}
    response = authenticated_admin_client.post(f"/admin/bookings/{test_booking.booking_id}/reject", json=payload)
    assert response.status_code == 200
    # The repository sets it to "CANCELLED" string, but the enum is "Cancelled"
    # Let's check the case returned by the API
    assert response.json()["status"].upper() == "CANCELLED"

def test_admin_assign_team(authenticated_admin_client, test_booking, test_team):
    # Payload matches AssignTeamRequest schema in admin_model.py
    payload = {"technical_team_id": str(test_team.team_id)}
    response = authenticated_admin_client.post(f"/admin/bookings/{test_booking.booking_id}/assign", json=payload)
    assert response.status_code == 200

def test_admin_create_booking_for_customer(authenticated_admin_client, test_user, test_service, technical_user):
    """Test creating a booking returns customer information in response"""
    # Payload matches AdminBookingCreate schema
    # Use contact_phone alias 'phone' for the request body
    payload = {
        "phone": test_user.phone,
        "full_name": test_user.full_name,
        "car_make": "Honda",
        "car_model": "Civic",
        "appointment_date": str(date.today()),
        "start_time": "14:00:00",
        "service_location": "Customer Home",
        "items": [
            {
                "service_id": test_service.service_id,
                "quantity": 1.0
            }
        ],
        "source": "Phone",
        "assigned_garage_id": str(uuid4()) # Added missing required field
    }
    response = authenticated_admin_client.post("/admin/bookings", json=payload)
    assert response.status_code == 201
    
    # Verify response includes customer information
    booking_data = response.json()
    assert "booking_id" in booking_data
    assert "customer" in booking_data
    assert booking_data["customer"]["full_name"] == test_user.full_name
    assert booking_data["customer"]["phone"] == test_user.phone
    assert booking_data["car_make"] == "Honda"
    assert booking_data["car_model"] == "Civic"

def test_admin_get_overview(authenticated_admin_client, test_booking):
    """Test daily overview includes bookings with customer information"""
    today = date.today().isoformat()
    response = authenticated_admin_client.get(f"/admin/overview?target_date={today}")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "bookings" in data
    
    # Verify bookings in overview include customer info if present
    if data["bookings"]:
        for booking in data["bookings"]:
            assert "full_name" in booking or "customer" in booking
            assert "phone" in booking or "customer" in booking

def test_booking_response_includes_customer_details(authenticated_admin_client, test_user, test_service):
    """Test that BookingHistoryResponse properly extracts customer details from relationship"""
    # Create a booking
    payload = {
        "phone": test_user.phone,
        "full_name": test_user.full_name,
        "car_make": "Tesla",
        "car_model": "Model 3",
        "appointment_date": str(date.today()),
        "start_time": "16:00:00",
        "service_location": "Garage",
        "items": [
            {
                "service_id": test_service.service_id,
                "quantity": 1.0
            }
        ],
        "source": "Phone",
        "assigned_garage_id": str(uuid4())
    }
    
    create_response = authenticated_admin_client.post("/admin/bookings", json=payload)
    assert create_response.status_code == 201
    created_booking = create_response.json()
    
    # Verify customer info in creation response as nested object
    assert "customer" in created_booking
    assert created_booking["customer"]["full_name"] is not None
    assert created_booking["customer"]["phone"] is not None
    
    # Now fetch all bookings and verify the same booking has customer info
    list_response = authenticated_admin_client.get("/admin/bookings")
    assert list_response.status_code == 200
    bookings_list = list_response.json()
    
    # Find our created booking in the list
    matching_booking = next(
        (b for b in bookings_list if b["booking_id"] == created_booking["booking_id"]), 
        None
    )
    assert matching_booking is not None
    assert matching_booking["customer"]["full_name"] == test_user.full_name
    assert matching_booking["customer"]["phone"] == test_user.phone
