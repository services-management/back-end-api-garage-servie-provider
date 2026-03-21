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

def test_create_report_success(authenticated_technical_client, test_booking, technical_user):
    """Test creating a technical report with vehicle check list."""
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
    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == test_booking.booking_id
    assert data["vehicle_info"]["vehicle_type"] == "Toyota Camry 2023"
    assert len(data["checklist_items"]) == 13
    assert not data["is_approved"]
    assert "report_id" in data

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

def test_create_duplicate_report(authenticated_technical_client, test_booking, db_session):
    """Test that creating duplicate report for same booking fails."""
    
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

def test_get_my_reports(authenticated_technical_client, test_booking):
    """Test getting current user's reports."""
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

def test_get_report_by_id(authenticated_technical_client, test_booking):
    """Test getting a specific report by ID."""
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

def test_get_report_by_booking(authenticated_technical_client, test_booking):
    """Test getting report by booking ID."""
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

def test_update_report(authenticated_technical_client, test_booking):
    """Test updating a report."""
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

def test_admin_get_all_reports(authenticated_admin_client, test_booking, authenticated_technical_client):
    """Test admin getting all reports."""
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

def test_admin_get_pending_reports(authenticated_admin_client, test_booking, authenticated_technical_client):
    """Test admin getting pending reports."""
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

def test_admin_approve_report(authenticated_admin_client, test_booking, authenticated_technical_client):
    """Test admin approving a report."""
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

def test_admin_reject_report_requires_feedback(authenticated_admin_client, test_booking, authenticated_technical_client):
    """Test that rejecting a report requires feedback."""
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

def test_admin_reject_report_with_feedback(authenticated_admin_client, test_booking, authenticated_technical_client):
    """Test admin rejecting a report with feedback."""
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

def test_cannot_complete_booking_without_report(authenticated_technical_client, test_booking, test_team, technical_user, db_session):
    """Test that booking cannot be marked COMPLETED without a report."""
    # Assign technical to team and booking to the same team
    technical_user.team_id = test_team.team_id
    test_booking.technical_team_id = test_team.team_id
    db_session.commit()
    
    # Try to mark as completed without report
    response = authenticated_technical_client.patch(
        f"/technical/jobs/{test_booking.booking_id}/status?status=COMPLETED"
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
        f"/technical/jobs/{test_booking.booking_id}/status?status=COMPLETED"
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
        f"/technical/jobs/{test_booking.booking_id}/status?status=COMPLETED"
    )
    assert response.status_code == 200
    assert response.json()["status"] == BookingStatus.COMPLETED.value