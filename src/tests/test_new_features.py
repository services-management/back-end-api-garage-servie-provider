from fastapi.testclient import TestClient

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
