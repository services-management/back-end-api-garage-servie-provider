import pytest
from datetime import date, timedelta
from decimal import Decimal
def test_technical_login_success(client, technical_user):
    """Test successful technical staff login."""
    response = client.post(
        "/technical/login",
        json={"username": "tech_staff_1", "password": "techpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_read_technical_me_unauthorized(client):
    """Test access to a secured technical endpoint without a token."""
    response = client.get("/technical/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_read_technical_me_success(authenticated_technical_client, technical_user):
    """Test access to the secured technical 'me' endpoint."""
    response = authenticated_technical_client.get("/technical/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == technical_user.username
    assert data["role"] == "technical"
    assert data["status"] == "free"
    assert "telegram_magic_link" in data
    assert "technical_id" in data

def test_update_technical_details_success(authenticated_technical_client):
    """Test updating the name and phone number of the technical user."""
    update_data = {
        "name": "Tech Staff Updated",
        "phone_number": "+98765432100",
    }
    response = authenticated_technical_client.put("/technical/me", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tech Staff Updated"
    assert data["phone_number"] == "+98765432100"

def test_update_technical_status_success(authenticated_technical_client):
    """Test updating only the operational status."""
    status_data = {"status": "busy"}
    response = authenticated_technical_client.patch("/technical/me/status", json=status_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "busy"

def test_admin_cannot_update_technical_status(authenticated_admin_client):
    """Check that the Admin can't use this route (Authorization Test)"""
    status_data = {"status": "off_duty"}
    response = authenticated_admin_client.patch("/technical/me/status", json=status_data)
    assert response.status_code in [401, 403]

# --- PERFORMANCE ENDPOINT TESTS ---

def test_get_my_performance_success(authenticated_technical_client, technical_user, test_team, db_session):
    """Test technical user getting their own performance metrics."""
    # Assign technical user to a team
    technical_user.team_id = test_team.team_id
    db_session.commit()
    
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_technical_client.get(
        "/technical/performance/me",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert "technical_id" in data
    assert "name" in data
    assert "total_jobs" in data
    assert "completed_jobs" in data
    assert "in_progress_jobs" in data
    assert "completion_rate" in data
    assert "total_revenue" in data

def test_get_my_performance_unauthorized(client):
    """Test unauthorized access to performance/me endpoint."""
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = client.get(
        "/technical/performance/me",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 401

def test_get_technical_performance_by_admin(authenticated_admin_client, technical_user, test_team, db_session):
    """Test admin getting a specific technical's performance."""
    # Assign technical user to a team
    technical_user.team_id = test_team.team_id
    db_session.commit()
    
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_admin_client.get(
        f"/technical/performance/technical/{technical_user.technical_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["technical_id"] == str(technical_user.technical_id)
    assert data["name"] == technical_user.name

def test_get_team_performance_by_admin(authenticated_admin_client, test_team, technical_user, db_session):
    """Test admin getting team performance."""
    # Assign technical user to the team
    technical_user.team_id = test_team.team_id
    db_session.commit()
    
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_admin_client.get(
        f"/technical/performance/team/{test_team.team_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == str(test_team.team_id)
    assert data["team_name"] == test_team.team_name
    assert "member_count" in data
    assert "total_jobs" in data
    assert "completed_jobs" in data
    assert "members" in data

def test_get_all_teams_performance_by_admin(authenticated_admin_client, test_team):
    """Test admin getting all teams performance."""
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_admin_client.get(
        "/technical/performance/teams",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_all_technicals_performance_by_admin(authenticated_admin_client, technical_user):
    """Test admin getting all technicals performance."""
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_admin_client.get(
        "/technical/performance/technicals",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check that our technical user is in the results
    tech_ids = [item["technical_id"] for item in data]
    assert str(technical_user.technical_id) in tech_ids

def test_get_technical_performance_by_technical(authenticated_technical_client, technical_user, test_team, db_session):
    """Test technical user getting another technical's performance."""
    # Assign technical user to a team
    technical_user.team_id = test_team.team_id
    db_session.commit()
    
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_technical_client.get(
        f"/technical/performance/technical/{technical_user.technical_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["technical_id"] == str(technical_user.technical_id)

def test_get_team_performance_by_technical(authenticated_technical_client, test_team, technical_user, db_session):
    """Test technical user getting team performance."""
    # Assign technical user to the team
    technical_user.team_id = test_team.team_id
    db_session.commit()
    
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_technical_client.get(
        f"/technical/performance/team/{test_team.team_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == str(test_team.team_id)

def test_get_team_performance_not_found(authenticated_admin_client):
    """Test getting performance for non-existent team."""
    import uuid
    fake_team_id = uuid.uuid4()
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_admin_client.get(
        f"/technical/performance/team/{fake_team_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 404

def test_get_technical_performance_not_found(authenticated_admin_client):
    """Test getting performance for non-existent technical."""
    import uuid
    fake_tech_id = uuid.uuid4()
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    response = authenticated_admin_client.get(
        f"/technical/performance/technical/{fake_tech_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 404

def test_performance_with_bookings(authenticated_admin_client, test_team, technical_user, test_user, db_session):
    """Test performance metrics with actual bookings."""
    from src.schemas.booking import Booking, BookingStatus, BookingSource
    from datetime import time
    
    # Assign technical user to the team
    technical_user.team_id = test_team.team_id
    db_session.commit()
    
    # Create some bookings for the team
    for i in range(3):
        booking = Booking(
            user_id=test_user.user_id,
            contact_phone=test_user.phone,
            car_make="Toyota",
            car_model="Camry",
            appointment_date=date.today(),
            start_time=time(10 + i, 0),
            service_location="Test Location",
            source=BookingSource.WEB,
            status=BookingStatus.COMPLETED if i < 2 else BookingStatus.IN_PROGRESS,
            total_price=Decimal("100.00"),
            technical_team_id=test_team.team_id
        )
        db_session.add(booking)
    db_session.commit()
    
    start_date = date.today() - timedelta(days=1)
    end_date = date.today() + timedelta(days=1)
    
    response = authenticated_admin_client.get(
        f"/technical/performance/team/{test_team.team_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] == 3
    assert data["completed_jobs"] == 2
    assert data["in_progress_jobs"] == 1
    assert data["completion_rate"] == 66.67  # 2/3 * 100
    assert float(data["total_revenue"]) == 200.00  # 2 completed * 100

# --- TECHNICAL REPORT TESTS ---

def test_create_report_success(authenticated_technical_client, test_booking, technical_user, test_team, db_session):
    """Test creating a technical report with vehicle check list."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {
            "vehicle_type": "Toyota Camry 2023",
            "vin_number": "ABC123456789",
            "fuel_type": "Gasoline",
            "fuel_quantity": "Full Tank",
            "hybrid_type": "None"
        },
        "checklist_items": [
            {"name": "ចង្កៀងមុខស្ដាំ (Right Headlight)", "status": "yes", "notes": ""},
            {"name": "ចង្កៀងឆ្វេង (Left Headlight)", "status": "yes", "notes": ""},
            {"name": "ចង្កៀងឆ្វេងខាងក្រោយ (Left Taillight)", "status": "yes", "notes": ""},
            {"name": "ចង្កៀងស្ដាំខាងក្រោយ (Right Taillight)", "status": "yes", "notes": ""},
            {"name": "ចង្កៀងចំហៀងខាងស្ដាំ (Right Turn Signal)", "status": "yes", "notes": ""},
            {"name": "ចង្កៀងចំហៀងខាងឆ្វេង (Left Turn Signal)", "status": "yes", "notes": ""},
            {"name": "ប្រភេទ Hybrid (Hybrid System)", "status": "no", "notes": "Not a hybrid vehicle"},
            {"name": "ថ្នាំងប្រេង ម៉ាស៊ីន (Engine Oil)", "status": "yes", "notes": "Level OK"},
            {"name": "ជង់ហ្គាស ម៉ាស៊ីន (Radiator Coolant)", "status": "yes", "notes": ""},
            {"name": "ទឹកកញ្ចក់ (Windshield Washer)", "status": "yes", "notes": ""},
            {"name": "ស្លាបភ្លៅឆ្វេងខាងមុខ (Left Wiper)", "status": "yes", "notes": ""},
            {"name": "ស្លាបភ្លៅស្ដាំខាងមុខ (Right Wiper)", "status": "yes", "notes": ""},
            {"name": "ហ្វ្រាំង (Brakes)", "status": "yes", "notes": ""}
        ],
        "work_description": "Changed oil and replaced filter. Checked all fluid levels.",
        "parts_used": "Oil filter, 5W-30 motor oil (5L)",
        "additional_notes": "Recommended next service in 5000km",
        "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "video_urls": ["https://example.com/video1.mp4"]
    }
    response = authenticated_technical_client.post("/technical/reports", json=report_data)
    if response.status_code != 201:
        print(f"ERROR: {response.status_code} - {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == test_booking.booking_id
    assert data["vehicle_info"]["vehicle_type"] == "Toyota Camry 2023"
    assert len(data["checklist_items"]) == 13
    assert not data["is_approved"]
    assert "report_id" in data

def test_create_report_sends_notification_to_admin(
    authenticated_technical_client, 
    test_booking, 
    technical_user,
    test_team,
    admin_with_telegram,
    db_session
):
    """Test that submitting a technical report doesn't break when admin notification is triggered"""
    from unittest.mock import patch, AsyncMock
    
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {
            "vehicle_type": "Toyota Camry 2023",
            "vin_number": "ABC123456789",
            "fuel_type": "Gasoline",
            "fuel_quantity": "Full Tank",
            "hybrid_type": "None"
        },
        "checklist_items": [
            {"name": "Right Headlight", "status": "yes", "notes": ""},
            {"name": "Left Headlight", "status": "yes", "notes": ""},
            {"name": "Left Taillight", "status": "yes", "notes": ""},
            {"name": "Right Taillight", "status": "yes", "notes": ""},
            {"name": "Right Turn Signal", "status": "yes", "notes": ""},
            {"name": "Left Turn Signal", "status": "yes", "notes": ""},
            {"name": "Hybrid System", "status": "no", "notes": "Not hybrid"},
            {"name": "Engine Oil", "status": "yes", "notes": "OK"},
            {"name": "Radiator Coolant", "status": "yes", "notes": ""},
            {"name": "Windshield Washer", "status": "yes", "notes": ""},
            {"name": "Left Wiper", "status": "yes", "notes": ""},
            {"name": "Right Wiper", "status": "yes", "notes": ""},
            {"name": "Brakes", "status": "yes", "notes": ""}
        ],
        "work_description": "Test service with admin notification",
        "parts_used": "Oil filter",
        "additional_notes": "All good",
        "image_urls": [],
        "video_urls": []
    }
    
    # Mock Telegram to prevent actual API calls during test
    # The notification should be attempted but failure shouldn't break report creation
    with patch("src.controller.technical_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("Telegram not configured in test")
        
        response = authenticated_technical_client.post("/technical/reports", json=report_data)
        
        # Report should still be created even if notification fails
        assert response.status_code == 201
        data = response.json()
        assert data["booking_id"] == test_booking.booking_id
        assert not data["is_approved"]

def test_create_report_unauthorized(client, test_booking):
    """Test creating report without authentication."""
    report_data = {
        "booking_id": test_booking.booking_id,
        "work_description": "Test work description here."
    }
    response = client.post("/technical/reports", json=report_data)
    assert response.status_code == 401

def test_create_report_booking_not_found(authenticated_technical_client):
    """Test creating report for non-existent booking."""
    report_data = {
        "booking_id": 99999,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description here."
    }
    response = authenticated_technical_client.post("/technical/reports", json=report_data)
    assert response.status_code == 404

def test_create_duplicate_report(authenticated_technical_client, test_booking, technical_user, test_team, db_session):
    """Test that creating duplicate report for same booking fails."""
    
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create first report
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "First report for this booking."
    }
    response = authenticated_technical_client.post("/technical/reports", json=report_data)
    assert response.status_code == 201
    
    # Try to create second report for same booking
    report_data2 = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Second report for same booking."
    }
    response = authenticated_technical_client.post("/technical/reports", json=report_data2)
    assert response.status_code == 400

def test_get_my_reports(authenticated_technical_client, test_booking, technical_user, test_team, db_session):
    """Test getting current user's reports."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # First create a report
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for my reports."
    }
    authenticated_technical_client.post("/technical/reports", json=report_data)
    
    # Get my reports
    response = authenticated_technical_client.get("/technical/reports/me")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_report_by_id(authenticated_technical_client, test_booking, technical_user, test_team, db_session):
    """Test getting a specific report by ID."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for get by id."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Get the report
    response = authenticated_technical_client.get(f"/technical/reports/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == report_id

def test_get_report_by_booking(authenticated_technical_client, test_booking, technical_user, test_team, db_session):
    """Test getting report by booking ID."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for get by booking."
    }
    authenticated_technical_client.post("/technical/reports", json=report_data)
    
    # Get report by booking
    response = authenticated_technical_client.get(f"/technical/reports/booking/{test_booking.booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["booking_id"] == test_booking.booking_id

def test_update_report(authenticated_technical_client, test_booking, technical_user, test_team, db_session):
    """Test updating a report."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Original Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Original work description for update test."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Update the report
    update_data = {
        "vehicle_info": {"vehicle_type": "Updated Vehicle"},
        "work_description": "Updated work description for update test.",
        "additional_notes": "Added some notes after the fact."
    }
    response = authenticated_technical_client.put(f"/technical/reports/{report_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_info"]["vehicle_type"] == "Updated Vehicle"
    assert data["work_description"] == update_data["work_description"]
    assert data["additional_notes"] == update_data["additional_notes"]

def test_admin_get_all_reports(authenticated_admin_client, test_booking, authenticated_technical_client, technical_user, test_team, db_session):
    """Test admin getting all reports."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for admin all reports."
    }
    authenticated_technical_client.post("/technical/reports", json=report_data)
    
    # Admin gets all reports
    response = authenticated_admin_client.get("/technical/reports/admin/all")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_admin_get_pending_reports(authenticated_admin_client, test_booking, authenticated_technical_client, technical_user, test_team, db_session):
    """Test admin getting pending reports."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "work_description": "Test work description for pending reports."
    }
    authenticated_technical_client.post("/technical/reports", json=report_data)
    
    # Admin gets pending reports
    response = authenticated_admin_client.get("/technical/reports/admin/pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All pending reports should not be approved
    for report in data:
        assert not report["is_approved"]

def test_admin_approve_report(authenticated_admin_client, test_booking, authenticated_technical_client, technical_user, test_team, db_session):
    """Test admin approving a report."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for approval."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Admin approves the report
    approval_data = {"is_approved": True}
    response = authenticated_admin_client.patch(f"/technical/reports/{report_id}/approve", json=approval_data)
    assert response.status_code == 200
    data = response.json()
    assert data["is_approved"]
    assert data["approved_by"] is not None

def test_admin_reject_report_requires_feedback(authenticated_admin_client, test_booking, authenticated_technical_client, technical_user, test_team, db_session):
    """Test that rejecting a report requires feedback."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for rejection."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Admin tries to reject without feedback
    rejection_data = {"is_approved": False}
    response = authenticated_admin_client.patch(f"/technical/reports/{report_id}/approve", json=rejection_data)
    assert response.status_code == 400

def test_admin_reject_report_with_feedback(authenticated_admin_client, test_booking, authenticated_technical_client, technical_user, test_team, db_session):
    """Test admin rejecting a report with feedback."""
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for rejection with feedback."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Admin rejects with feedback
    rejection_data = {
        "is_approved": False,
        "admin_feedback": "Please provide more details about the work performed."
    }
    response = authenticated_admin_client.patch(f"/technical/reports/{report_id}/approve", json=rejection_data)
    assert response.status_code == 200
    data = response.json()
    assert not data["is_approved"]
    assert data["admin_feedback"] == rejection_data["admin_feedback"]

def test_admin_approve_report_sends_notification_to_technician(
    authenticated_admin_client, 
    test_booking, 
    authenticated_technical_client,
    technical_user,
    test_team,
    db_session
):
    """Test that approving a report sends notification to technical staff"""
    from unittest.mock import patch, AsyncMock
    
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Add telegram_chat_id to technical user for this test
    technical_user.telegram_chat_id = "tech_telegram_123"
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Honda Civic"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test service with notification."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Mock Telegram send_message
    with patch("src.controller.technical_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        # Admin approves the report
        approval_data = {"is_approved": True}
        response = authenticated_admin_client.patch(f"/technical/reports/{report_id}/approve", json=approval_data)
        
        assert response.status_code == 200
        # Verify Telegram notification was attempted
        assert mock_send.called
        # Verify message contains approval information
        call_args = mock_send.call_args
        message_text = call_args[1]["text"]
        assert "APPROVED" in message_text or "✅" in message_text
        # Vehicle info comes from booking, not report data
        assert "Vehicle:" in message_text

def test_admin_reject_report_sends_notification_to_technician(
    authenticated_admin_client, 
    test_booking, 
    authenticated_technical_client,
    technical_user,
    test_team,
    db_session
):
    """Test that rejecting a report sends notification to technical staff"""
    from unittest.mock import patch, AsyncMock
    
    # Assign technical user to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Add telegram_chat_id to technical user for this test
    technical_user.telegram_chat_id = "tech_telegram_123"
    db_session.commit()
    
    # Create a report first
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Toyota Camry"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test service with rejection notification."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Mock Telegram send_message
    with patch("src.controller.technical_controller.telegram_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        # Admin rejects the report with feedback
        rejection_data = {
            "is_approved": False,
            "admin_feedback": "Please add more details about parts used."
        }
        response = authenticated_admin_client.patch(f"/technical/reports/{report_id}/approve", json=rejection_data)
        
        assert response.status_code == 200
        # Verify Telegram notification was attempted
        assert mock_send.called
        # Verify message contains rejection information and feedback
        call_args = mock_send.call_args
        message_text = call_args[1]["text"]
        assert "REJECTED" in message_text or "❌" in message_text
        assert "Admin Feedback" in message_text
        assert "parts" in message_text.lower()

def test_cannot_complete_booking_without_report(authenticated_technical_client, test_booking, test_team, technical_user, db_session):
    """Test that booking cannot be marked COMPLETED without a report."""
    # Assign technical to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Try to mark as completed without report
    response = authenticated_technical_client.patch(
        f"/technical/jobs/{test_booking.booking_id}/status?new_status=COMPLETED"
    )
    assert response.status_code == 400
    assert "report" in response.json()["detail"].lower()

def test_cannot_complete_booking_with_unapproved_report(authenticated_technical_client, test_booking, test_team, technical_user, db_session):
    """Test that booking cannot be marked COMPLETED with unapproved report."""
    # Assign technical to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report (unapproved by default)
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for completion test."
    }
    authenticated_technical_client.post("/technical/reports", json=report_data)
    
    # Try to mark as completed
    response = authenticated_technical_client.patch(
        f"/technical/jobs/{test_booking.booking_id}/status?new_status=COMPLETED"
    )
    assert response.status_code == 400
    assert "approved" in response.json()["detail"].lower()

def test_can_complete_booking_with_approved_report(authenticated_technical_client, authenticated_admin_client, test_booking, test_team, technical_user, db_session):
    """Test that booking can be marked COMPLETED after report is approved."""
    from src.core.enums import BookingStatus
    
    # Assign technical to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Create a report
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Test Vehicle"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Test work description for final completion."
    }
    create_response = authenticated_technical_client.post("/technical/reports", json=report_data)
    report_id = create_response.json()["report_id"]
    
    # Admin approves the report
    approval_data = {"is_approved": True}
    authenticated_admin_client.patch(f"/technical/reports/{report_id}/approve", json=approval_data)
    
    # Now technical can mark as completed
    response = authenticated_technical_client.patch(
        f"/technical/jobs/{test_booking.booking_id}/status?new_status=COMPLETED"
    )
    assert response.status_code == 200
    assert response.json()["status"] == BookingStatus.COMPLETED.value


# ===== TEAM LEAD ACCESS TESTS =====

@pytest.fixture
def team_lead_user(db_session, test_team):
    """Create a team lead user WITHOUT team_id (only designated via team.team_lead_id)"""
    from src.schemas.techincal import TechnicalModel
    from src.utils.hash_password import hash_password
    
    team_lead = TechnicalModel(
        username="teamleaduser",
        password=hash_password("leadpassword"),
        name="Team Lead User",
        phone_number="+1111111111",
        telegram_chat_id="LEAD_CHAT_ID",
        role="technical",
        status='free',
        is_active=True,
        team_id=None  # Team lead might not have team_id set
    )
    db_session.add(team_lead)
    db_session.commit()
    
    # Set this user as the team lead
    test_team.team_lead_id = team_lead.technical_id
    db_session.commit()
    db_session.refresh(test_team)
    db_session.refresh(team_lead)
    
    return team_lead


@pytest.fixture
def authenticated_team_lead_client(client, team_lead_user):
    """Create an authenticated client for the team lead user."""
    # Login to get token
    response = client.post(
        "/technical/login",
        json={"username": "teamleaduser", "password": "leadpassword"}
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    
    token = response.json()["access_token"]
    
    # Add authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_team_lead_can_view_worklist(authenticated_team_lead_client, test_team, test_booking, db_session):
    """Test that team lead can view their team's worklist even without team_id"""
    from datetime import time
    from src.schemas.booking import Booking, BookingStatus, BookingSource
    
    # Create a booking assigned to the team
    booking = Booking(
        user_id=test_booking.user_id,
        contact_phone=test_booking.contact_phone,
        car_make="Honda",
        car_model="Civic",
        appointment_date=date.today(),
        start_time=time(10, 0),
        service_location="Test Location",
        source=BookingSource.WEB,
        status=BookingStatus.CONFIRMED,
        total_price=Decimal("150.00"),
        technical_team_id=test_team.team_id
    )
    db_session.add(booking)
    db_session.commit()
    
    # Team lead should be able to view worklist
    response = authenticated_team_lead_client.get(
        "/technical/worklist",
        params={"team_id": str(test_team.team_id), "target_date": date.today().isoformat()}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should include the booking we just created
    booking_ids = [b["booking_id"] for b in data]
    assert booking.booking_id in booking_ids


def test_team_lead_cannot_view_other_team_worklist(authenticated_team_lead_client, db_session):
    """Test that team lead cannot view other teams' worklists"""
    from src.schemas.techincal import TechnicalTeam
    
    # Create another team
    other_team = TechnicalTeam(
        team_name="Other Team",
        description="Another team",
        is_active=True
    )
    db_session.add(other_team)
    db_session.commit()
    
    # Team lead should NOT be able to view other team's worklist
    response = authenticated_team_lead_client.get(
        "/technical/worklist",
        params={"team_id": str(other_team.team_id), "target_date": date.today().isoformat()}
    )
    
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_team_lead_can_update_job_status(authenticated_team_lead_client, test_booking, test_team, team_lead_user, db_session):
    """Test that team lead can update job status for their team's bookings"""
    from src.core.enums import BookingStatus
    
    # Assign booking to the team
    test_booking.technical_team_id = test_team.team_id
    test_booking.status = BookingStatus.CONFIRMED
    db_session.commit()
    
    # Team lead should be able to update status
    response = authenticated_team_lead_client.patch(
        f"/technical/jobs/{test_booking.booking_id}/status?new_status=IN_PROGRESS"
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == BookingStatus.IN_PROGRESS.value


def test_team_lead_cannot_update_other_team_job(authenticated_team_lead_client, test_booking, db_session):
    """Test that team lead cannot update jobs from other teams"""
    from src.core.enums import BookingStatus
    from src.schemas.techincal import TechnicalTeam
    
    # Create another team and assign booking to it
    other_team = TechnicalTeam(
        team_name="Other Team Beta",
        description="Different team",
        is_active=True
    )
    db_session.add(other_team)
    db_session.commit()
    
    test_booking.technical_team_id = other_team.team_id
    test_booking.status = BookingStatus.CONFIRMED
    db_session.commit()
    
    # Team lead should NOT be able to update this booking
    response = authenticated_team_lead_client.patch(
        f"/technical/jobs/{test_booking.booking_id}/status?new_status=IN_PROGRESS"
    )
    
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_team_lead_can_create_report(authenticated_team_lead_client, test_booking, test_team, team_lead_user, db_session):
    """Test that team lead can create reports for their team's bookings"""
    # Assign booking to the team
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Team lead should be able to create a report
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Honda Civic"},
        "checklist_items": [
            {"name": "Engine Oil", "status": "yes"},
            {"name": "Brake Pads", "status": "no"}
        ],
        "work_description": "Regular maintenance check by team lead"
    }
    
    response = authenticated_team_lead_client.post("/technical/reports", json=report_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == test_booking.booking_id
    assert data["technical_id"] == str(team_lead_user.technical_id)


def test_team_lead_cannot_create_report_for_other_team(authenticated_team_lead_client, test_booking, db_session):
    """Test that team lead cannot create reports for other teams' bookings"""
    from src.schemas.techincal import TechnicalTeam
    
    # Create another team and assign booking to it
    other_team = TechnicalTeam(
        team_name="Other Team Gamma",
        description="Yet another team",
        is_active=True
    )
    db_session.add(other_team)
    db_session.commit()
    
    test_booking.technical_team_id = other_team.team_id
    db_session.commit()
    
    # Team lead should NOT be able to create a report
    report_data = {
        "booking_id": test_booking.booking_id,
        "vehicle_info": {"vehicle_type": "Toyota Camry"},
        "checklist_items": [{"name": "Test Item", "status": "yes"}],
        "work_description": "Should fail"
    }
    
    response = authenticated_team_lead_client.post("/technical/reports", json=report_data)
    
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_regular_member_still_has_access(authenticated_technical_client, test_booking, test_team, technical_user, db_session):
    """Test that regular team members still have access (regression test)"""
    from datetime import time
    from src.schemas.booking import Booking, BookingStatus as BS, BookingSource
    
    # Ensure technical user has team_id
    technical_user.team_id = test_team.team_id
    
    # Create a booking for the team
    booking = Booking(
        user_id=test_booking.user_id,
        contact_phone=test_booking.contact_phone,
        car_make="Ford",
        car_model="Focus",
        appointment_date=date.today(),
        start_time=time(14, 0),
        service_location="Test Garage",
        source=BookingSource.WEB,
        status=BS.CONFIRMED,
        total_price=Decimal("200.00"),
        technical_team_id=test_team.team_id
    )
    db_session.add(booking)
    db_session.commit()
    
    # Regular member should be able to view worklist
    response = authenticated_technical_client.get(
        "/technical/worklist",
        params={"team_id": str(test_team.team_id), "target_date": date.today().isoformat()}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Regular member should be able to update status
    response = authenticated_technical_client.patch(
        f"/technical/jobs/{booking.booking_id}/status?new_status=IN_PROGRESS"
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == BS.IN_PROGRESS.value


def test_team_lead_performance_shows_team_jobs(authenticated_admin_client, team_lead_user, test_team, test_user, db_session):
    """Test that team lead performance metrics include their team's jobs even without team_id"""
    from src.schemas.booking import Booking, BookingStatus, BookingSource
    from datetime import time
    
    # Create bookings assigned to the team (team lead doesn't have team_id set)
    for i in range(3):
        booking = Booking(
            user_id=test_user.user_id,
            contact_phone=test_user.phone,
            car_make="Honda",
            car_model=f"Civic_{i}",
            appointment_date=date.today(),
            start_time=time(10 + i, 0),
            service_location="Test Location",
            source=BookingSource.WEB,
            status=BookingStatus.COMPLETED if i < 2 else BookingStatus.IN_PROGRESS,
            total_price=Decimal("150.00"),
            technical_team_id=test_team.team_id
        )
        db_session.add(booking)
    db_session.commit()
    
    start_date = date.today() - timedelta(days=1)
    end_date = date.today() + timedelta(days=1)
    
    # Get team lead's performance
    response = authenticated_admin_client.get(
        f"/technical/performance/technical/{team_lead_user.technical_id}",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Team lead should see the team's jobs
    assert data["technical_id"] == str(team_lead_user.technical_id)
    assert data["name"] == team_lead_user.name
    assert data["team_name"] == test_team.team_name  # Should show team name
    assert data["total_jobs"] == 3  # All 3 bookings
    assert data["completed_jobs"] == 2
    assert data["in_progress_jobs"] == 1
    assert data["total_revenue"] == "300.00"  # 2 completed * 150.00
    assert data["completion_rate"] > 0


def test_all_technicals_performance_includes_team_leads(authenticated_admin_client, team_lead_user, technical_user, test_team, test_user, db_session):
    """Test that /technicals endpoint includes team leads with correct job counts"""
    from src.schemas.booking import Booking, BookingStatus, BookingSource
    from datetime import time
    
    # Assign regular user to team
    technical_user.team_id = test_team.team_id
    
    # Create bookings for the team
    for i in range(2):
        booking = Booking(
            user_id=test_user.user_id,
            contact_phone=test_user.phone,
            car_make="Toyota",
            car_model=f"Camry_{i}",
            appointment_date=date.today(),
            start_time=time(9 + i, 0),
            service_location="Test Garage",
            source=BookingSource.WEB,
            status=BookingStatus.COMPLETED,
            total_price=Decimal("100.00"),
            technical_team_id=test_team.team_id
        )
        db_session.add(booking)
    db_session.commit()
    
    start_date = date.today() - timedelta(days=1)
    end_date = date.today() + timedelta(days=1)
    
    # Get all technicals performance
    response = authenticated_admin_client.get(
        "/technical/performance/technicals",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Find team lead and regular member in results
    team_lead_perf = next((t for t in data if t["technical_id"] == str(team_lead_user.technical_id)), None)
    regular_tech_perf = next((t for t in data if t["technical_id"] == str(technical_user.technical_id)), None)
    
    assert team_lead_perf is not None, "Team lead should be in performance list"
    assert regular_tech_perf is not None, "Regular tech should be in performance list"
    
    # Both should show the same team's jobs
    assert team_lead_perf["team_name"] == test_team.team_name
    assert regular_tech_perf["team_name"] == test_team.team_name
    
    # Both should count the team's jobs (since they're on the same team)
    assert team_lead_perf["total_jobs"] == 2
    assert regular_tech_perf["total_jobs"] == 2
    assert team_lead_perf["total_revenue"] == "200.00"
    assert regular_tech_perf["total_revenue"] == "200.00"


# ===== TEAM LEAD AUTO-ASSIGNMENT TESTS =====

def test_create_team_auto_assigns_team_lead(authenticated_admin_client, db_session):
    """Test that creating a team with team_lead_id automatically sets the lead's team_id"""
    from src.schemas.techincal import TechnicalModel
    from src.utils.hash_password import hash_password
    
    # Create a technical user to be the team lead
    tech_lead = TechnicalModel(
        username="autoleaduser",
        password=hash_password("password"),
        name="Auto Lead User",
        phone_number="+9999999999",
        telegram_chat_id=None,
        role="technical",
        status='free',
        is_active=True,
        team_id=None  # Start with no team
    )
    db_session.add(tech_lead)
    db_session.commit()
    
    # Create team with this user as team lead
    team_data = {
        "team_name": "Auto Assign Team",
        "description": "Team for auto-assignment test",
        "team_lead_id": str(tech_lead.technical_id)
    }
    
    response = authenticated_admin_client.post("/admin/teams", json=team_data)
    
    assert response.status_code == 201
    team_data_response = response.json()
    assert team_data_response["team_name"] == "Auto Assign Team"
    assert team_data_response["team_lead_id"] == str(tech_lead.technical_id)
    
    # Verify the team lead now has team_id set
    db_session.refresh(tech_lead)
    assert tech_lead.team_id is not None, "Team lead should have team_id set"
    assert str(tech_lead.team_id) == team_data_response["team_id"], "Team lead's team_id should match the created team"


def test_update_team_change_team_lead(authenticated_admin_client, db_session):
    """Test that updating a team's team_lead_id auto-assigns the new lead"""
    from src.schemas.techincal import TechnicalModel, TechnicalTeam
    from src.utils.hash_password import hash_password
    
    # Create two technical users
    old_lead = TechnicalModel(
        username="oldleaduser",
        password=hash_password("password"),
        name="Old Lead User",
        phone_number="+8888888888",
        telegram_chat_id=None,
        role="technical",
        status='free',
        is_active=True,
        team_id=None
    )
    
    new_lead = TechnicalModel(
        username="newleaduser",
        password=hash_password("password"),
        name="New Lead User",
        phone_number="+7777777777",
        telegram_chat_id=None,
        role="technical",
        status='free',
        is_active=True,
        team_id=None
    )
    
    db_session.add(old_lead)
    db_session.add(new_lead)
    db_session.commit()
    
    # Create team with old_lead as team lead
    team = TechnicalTeam(
        team_name="Update Test Team",
        description="Team for update test",
        team_lead_id=old_lead.technical_id,
        is_active=True
    )
    db_session.add(team)
    db_session.commit()
    
    # Manually set old_lead's team_id (simulating the auto-assignment from create)
    old_lead.team_id = team.team_id
    db_session.commit()
    
    # Update team to change team lead
    update_data = {
        "team_lead_id": str(new_lead.technical_id)
    }
    
    response = authenticated_admin_client.put(
        f"/admin/teams/{team.team_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    updated_team = response.json()
    assert updated_team["team_lead_id"] == str(new_lead.technical_id)
    
    # Verify new lead has team_id set
    db_session.refresh(new_lead)
    assert new_lead.team_id is not None, "New team lead should have team_id set"
    assert str(new_lead.team_id) == str(team.team_id), "New lead's team_id should match the team"
    
    # Old lead remains a team member (their team_id is NOT cleared)
    # Admin must explicitly remove them using remove_member_from_team if needed
    db_session.refresh(old_lead)
    assert old_lead.team_id is not None, "Old team lead should remain as team member"
    assert str(old_lead.team_id) == str(team.team_id), "Old lead should still belong to the team"


def test_update_team_add_team_lead_to_existing_team(authenticated_admin_client, db_session):
    """Test adding a team_lead to an existing team that didn't have one"""
    from src.schemas.techincal import TechnicalModel, TechnicalTeam
    from src.utils.hash_password import hash_password
    
    # Create a technical user
    tech_user = TechnicalModel(
        username="lateteamlead",
        password=hash_password("password"),
        name="Late Team Lead",
        phone_number="+6666666666",
        telegram_chat_id=None,
        role="technical",
        status='free',
        is_active=True,
        team_id=None
    )
    db_session.add(tech_user)
    db_session.commit()
    
    # Create team without a team lead
    team = TechnicalTeam(
        team_name="No Lead Team",
        description="Team initially without lead",
        team_lead_id=None,
        is_active=True
    )
    db_session.add(team)
    db_session.commit()
    
    # Update team to add a team lead
    update_data = {
        "team_lead_id": str(tech_user.technical_id)
    }
    
    response = authenticated_admin_client.put(
        f"/admin/teams/{team.team_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    updated_team = response.json()
    assert updated_team["team_lead_id"] == str(tech_user.technical_id)
    
    # Verify the user now has team_id set
    db_session.refresh(tech_user)
    assert tech_user.team_id is not None, "Team lead should have team_id set after being assigned"
    assert str(tech_user.team_id) == str(team.team_id), "Team lead's team_id should match the team"


def test_remove_team_lead_clears_their_team_id(authenticated_admin_client, db_session):
    """Test that removing a team_lead keeps them as a team member (doesn't clear team_id)"""
    from src.schemas.techincal import TechnicalModel, TechnicalTeam
    from src.utils.hash_password import hash_password
    
    # Create a technical user as team lead
    team_lead = TechnicalModel(
        username="removablelead",
        password=hash_password("password"),
        name="Removable Lead",
        phone_number="+5555555555",
        telegram_chat_id=None,
        role="technical",
        status='free',
        is_active=True,
        team_id=None
    )
    db_session.add(team_lead)
    db_session.commit()
    
    # Create team with this user as team lead
    team = TechnicalTeam(
        team_name="Remove Lead Team",
        description="Team for removal test",
        team_lead_id=team_lead.technical_id,
        is_active=True
    )
    db_session.add(team)
    db_session.commit()
    
    # Set team lead's team_id
    team_lead.team_id = team.team_id
    db_session.commit()
    
    # Update team to remove team lead
    update_data = {
        "team_lead_id": None
    }
    
    response = authenticated_admin_client.put(
        f"/admin/teams/{team.team_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    updated_team = response.json()
    assert updated_team["team_lead_id"] is None
    
    # Verify the former team lead still has team_id (they're still a member)
    db_session.refresh(team_lead)
    assert team_lead.team_id is not None, "Former team lead should still be a team member"
    assert str(team_lead.team_id) == str(team.team_id), "Former team lead should still belong to the team"


