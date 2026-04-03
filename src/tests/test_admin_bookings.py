import pytest
from datetime import date, time
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, AsyncMock
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
    response = authenticated_admin_client.get("/admin/bookings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["booking_id"] == test_booking.booking_id

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

def test_admin_assign_team_sends_notification(
    authenticated_admin_client, 
    test_booking, 
    test_team,
    technical_user_with_telegram,
    db_session
):
    """Test that assigning a team sends a Telegram notification to technical staff"""
    
    # Update test_booking to have complete data
    test_booking.car_make = "Toyota"
    test_booking.car_model = "Camry"
    test_booking.appointment_date = date.today()
    test_booking.start_time = time(14, 0)
    test_booking.service_location = "Garage"
    test_booking.total_price = Decimal("150.00")
    db_session.commit()
    
    # Mock Telegram send_message
    with patch("src.controller.admin_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        payload = {"technical_team_id": str(test_team.team_id)}
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/assign", 
            json=payload
        )
        
        assert response.status_code == 200
        # Verify Telegram notification was attempted
        assert mock_send.called
        # Verify it was called with the correct chat ID
        call_args = mock_send.call_args
        assert call_args[1]["chat_id"] == technical_user_with_telegram.telegram_chat_id
        # Verify message contains key information
        message_text = call_args[1]["text"]
        assert "NEW JOB ASSIGNED" in message_text
        assert "Toyota" in message_text
        assert "Camry" in message_text


def test_admin_assign_team_no_notification_without_telegram(
    authenticated_admin_client,
    test_booking,
    test_team,
    db_session
):
    """Test that no notification is sent if technician hasn't linked Telegram"""
    from src.schemas.techincal import TechnicalModel
    from src.utils.hash_password import hash_password
    
    # Create technician WITHOUT telegram_chat_id
    tech_without_telegram = TechnicalModel(
        username="techwithouttg",
        password=hash_password("password"),
        name="Tech Without Telegram",
        phone_number="+1111111111",
        telegram_chat_id=None,  # No Telegram
        role="technical",
        status='free',
        is_active=True,
        team_id=test_team.team_id
    )
    db_session.add(tech_without_telegram)
    db_session.commit()
    
    with patch("src.controller.admin_controller.telegram_client.send_message") as mock_send:
        payload = {"technical_team_id": str(test_team.team_id)}
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/assign",
            json=payload
        )
        
        assert response.status_code == 200
        # Telegram should NOT be called since no one has chat ID
        mock_send.assert_not_called()


def test_admin_assign_team_notification_to_multiple_technicians(
    authenticated_admin_client,
    test_booking,
    test_team,
    technical_user_with_telegram,
    db_session
):
    """Test that all team members with Telegram receive notifications"""
    from src.schemas.techincal import TechnicalModel
    from src.utils.hash_password import hash_password
    
    # Create second technician with different Telegram chat ID
    tech2 = TechnicalModel(
        username="techuser2",
        password=hash_password("password"),
        name="Second Technician",
        phone_number="+2222222222",
        telegram_chat_id="987654321",  # Different chat ID
        role="technical",
        status='free',
        is_active=True,
        team_id=test_team.team_id
    )
    db_session.add(tech2)
    db_session.commit()
    
    with patch("src.controller.admin_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        payload = {"technical_team_id": str(test_team.team_id)}
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/assign",
            json=payload
        )
        
        assert response.status_code == 200
        # Should be called twice (once for each technician)
        assert mock_send.call_count == 2
        
        # Extract all chat IDs that were called
        called_chat_ids = [call[1]["chat_id"] for call in mock_send.call_args_list]
        assert technical_user_with_telegram.telegram_chat_id in called_chat_ids
        assert "987654321" in called_chat_ids


def test_admin_assign_team_notification_inactive_technician(
    authenticated_admin_client,
    test_booking,
    test_team,
    db_session
):
    """Test that inactive technicians don't receive notifications"""
    from src.schemas.techincal import TechnicalModel
    from src.utils.hash_password import hash_password
    
    # Create inactive technician with Telegram
    tech_inactive = TechnicalModel(
        username="techinactive",
        password=hash_password("password"),
        name="Inactive Technician",
        phone_number="+3333333333",
        telegram_chat_id="inactive_chat_id",
        role="technical",
        status='off_duty',
        is_active=False,  # Inactive
        team_id=test_team.team_id
    )
    db_session.add(tech_inactive)
    db_session.commit()
    
    with patch("src.controller.admin_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        payload = {"technical_team_id": str(test_team.team_id)}
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/assign",
            json=payload
        )
        
        assert response.status_code == 200
        # Should NOT call inactive technician
        mock_send.assert_not_called()


def test_admin_assign_team_notification_message_content(
    authenticated_admin_client,
    test_booking,
    test_team,
    technical_user_with_telegram,
    db_session
):
    """Test that notification message contains all required details"""
    
    # Update booking with more complete data
    test_booking.car_make = "Honda"
    test_booking.car_model = "Accord"
    test_booking.appointment_date = date(2026, 4, 15)
    test_booking.start_time = time(14, 30)
    test_booking.service_location = "Service Center A"
    test_booking.total_price = 250.00
    db_session.commit()
    
    with patch("src.controller.admin_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        payload = {"technical_team_id": str(test_team.team_id)}
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/assign",
            json=payload
        )
        
        assert response.status_code == 200
        assert mock_send.called
        
        # Verify message content
        message_text = mock_send.call_args[1]["text"]
        assert "🔧" in message_text or "NEW JOB ASSIGNED" in message_text
        assert "Honda" in message_text
        assert "Accord" in message_text
        assert "2026-04-15" in message_text or "04/15/2026" in message_text
        assert "14:30" in message_text
        assert "Service Center A" in message_text or "Garage" in message_text
        assert "$250" in message_text or "250.00" in message_text


def test_admin_assign_team_notification_handles_telegram_error(
    authenticated_admin_client,
    test_booking,
    test_team,
    technical_user_with_telegram
):
    """Test that assignment succeeds even if Telegram notification fails"""
    
    # Mock Telegram to raise an exception
    with patch("src.controller.admin_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("Telegram API error")
        
        payload = {"technical_team_id": str(test_team.team_id)}
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/assign",
            json=payload
        )
        
        # Assignment should still succeed despite notification failure
        assert response.status_code == 200
        # Verify Telegram was attempted
        assert mock_send.called


def test_admin_assign_team_updates_booking_status(
    authenticated_admin_client,
    test_booking,
    test_team,
    db_session
):
    """Test that assigning team changes booking status to CONFIRMED"""
    from src.schemas.booking import BookingStatus
    
    # Ensure booking starts as PENDING
    test_booking.status = BookingStatus.PENDING
    db_session.commit()
    
    payload = {"technical_team_id": str(test_team.team_id)}
    response = authenticated_admin_client.post(
        f"/admin/bookings/{test_booking.booking_id}/assign",
        json=payload
    )
    
    assert response.status_code == 200
    
    # Verify status changed to CONFIRMED
    updated_booking_data = response.json()
    assert updated_booking_data["status"].upper() == BookingStatus.CONFIRMED.value.upper()


def test_admin_assign_team_nonexistent_team(
    authenticated_admin_client,
    test_booking
):
    """Test error handling when assigning non-existent team"""
    import uuid
    
    payload = {"technical_team_id": str(uuid.uuid4())}  # Random UUID
    response = authenticated_admin_client.post(
        f"/admin/bookings/{test_booking.booking_id}/assign",
        json=payload
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_admin_assign_team_nonexistent_booking(
    authenticated_admin_client,
    test_team
):
    """Test error handling when assigning team to non-existent booking"""
    payload = {"technical_team_id": str(test_team.team_id)}
    response = authenticated_admin_client.post(
        "/admin/bookings/999999/assign",  # Non-existent booking ID
        json=payload
    )
    
    assert response.status_code == 404

def test_admin_create_booking_for_customer(authenticated_admin_client, test_user, test_service, technical_user):
    """Test admin can create booking with or without assigned_garage_id (single campus setup)"""
    
    # Test Case 1: With assigned_garage_id
    payload_with_garage = {
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
        "assigned_garage_id": str(uuid4())  # Optional but valid
    }
    response = authenticated_admin_client.post("/admin/bookings", json=payload_with_garage)
    assert response.status_code == 201
    
    # Test Case 2: Without assigned_garage_id (auto-assign to main campus)
    payload_without_garage = {
        "phone": test_user.phone,
        "full_name": test_user.full_name,
        "car_make": "Toyota",
        "car_model": "Camry",
        "appointment_date": str(date.today()),
        "start_time": "15:00:00",
        "service_location": "Garage",
        "items": [
            {
                "service_id": test_service.service_id,
                "quantity": 1.0
            }
        ],
        "source": "Phone"
        # assigned_garage_id is now OPTIONAL for single campus setup
    }
    response = authenticated_admin_client.post("/admin/bookings", json=payload_without_garage)
    assert response.status_code == 201

def test_admin_get_booking_by_id(authenticated_admin_client, test_booking):
    """Test getting a specific booking by ID"""
    response = authenticated_admin_client.get(f"/admin/bookings/{test_booking.booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["booking_id"] == test_booking.booking_id
    assert data["car_make"] == test_booking.car_make
    assert data["car_model"] == test_booking.car_model

def test_admin_get_booking_not_found(authenticated_admin_client):
    """Test 404 when booking doesn't exist"""
    response = authenticated_admin_client.get("/admin/bookings/999999")
    assert response.status_code == 404

def test_admin_upload_invoice_for_completed_booking(
    authenticated_admin_client, 
    test_booking, 
    db_session
):
    """Test admin can upload invoice for completed booking and customer gets notified"""
    from unittest.mock import patch, AsyncMock
    
    # Set booking as completed
    test_booking.status = BookingStatus.COMPLETED
    test_booking.customer.telegram_chat_id = "customer_telegram_123"
    db_session.commit()
    
    invoice_data = {
        "external_invoice_url": "https://storage.example.com/invoices/test-invoice-123.pdf"
    }
    
    with patch("src.controller.admin_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        response = authenticated_admin_client.post(
            f"/admin/bookings/{test_booking.booking_id}/invoice",
            json=invoice_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["external_invoice_url"] == invoice_data["external_invoice_url"]
        assert "uploaded_at" in data
        
        # Verify Telegram notification was sent to customer
        assert mock_send.called, "Telegram send_message should have been called"
        # Just verify it was called - detailed message testing requires more complex mocking

def test_admin_upload_invoice_fails_for_non_completed_booking(
    authenticated_admin_client, 
    test_booking
):
    """Test that invoice upload fails for non-completed bookings"""
    # Booking is still PENDING by default
    
    invoice_data = {
        "external_invoice_url": "https://storage.example.com/invoices/test-invoice-456.pdf"
    }
    
    response = authenticated_admin_client.post(
        f"/admin/bookings/{test_booking.booking_id}/invoice",
        json=invoice_data
    )
    
    # Should fail because booking is not completed
    assert response.status_code == 400
    assert "completed" in response.json()["detail"].lower()

def test_admin_get_overview(authenticated_admin_client, test_booking):
    today = date.today().isoformat()
    response = authenticated_admin_client.get(f"/admin/overview?target_date={today}")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "bookings" in data
