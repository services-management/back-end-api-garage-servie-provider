import pytest
import uuid

def test_list_admins_success(authenticated_admin_client):
    """Test listing all admin accounts."""
    response = authenticated_admin_client.get("/admin/accounts/admins")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "admin_id" in data[0]
    assert "is_active" in data[0]

def test_list_technicals_success(authenticated_admin_client):
    """Test listing all technical accounts."""
    # First provision a technical account
    tech_data = {
        "username": f"tech_{uuid.uuid4().hex[:8]}",
        "password": "techpassword",
        "name": "Test Tech",
        "phone_number": f"+{uuid.uuid4().int % 10**10}",
    }
    authenticated_admin_client.post("/admin/technical", json=tech_data)
    
    response = authenticated_admin_client.get("/admin/accounts/technicals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "technical_id" in data[0]
    assert "is_active" in data[0]

def test_deactivate_technical_success(authenticated_admin_client):
    """Test deactivating a technical account."""
    # 1. Create technical account
    tech_data = {
        "username": f"tech_{uuid.uuid4().hex[:8]}",
        "password": "techpassword",
        "name": "Deactivate Me",
        "phone_number": f"+{uuid.uuid4().int % 10**10}",
    }
    create_resp = authenticated_admin_client.post("/admin/technical", json=tech_data)
    tech_id = create_resp.json()["technical_id"]
    
    # 2. Deactivate it
    deactivate_resp = authenticated_admin_client.put(f"/admin/accounts/technicals/{tech_id}/deactivate")
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

def test_deactivate_admin_success(authenticated_admin_client):
    """Test deactivating an admin account."""
    # 1. Create another admin
    admin_data = {
        "username": f"admin_{uuid.uuid4().hex[:8]}",
        "password": "adminpassword",
        "email_phone": f"{uuid.uuid4().hex[:8]}@test.com",
    }
    create_resp = authenticated_admin_client.post("/admin/", json=admin_data)
    admin_id = create_resp.json()["admin_id"]
    
    # 2. Deactivate it
    deactivate_resp = authenticated_admin_client.put(f"/admin/accounts/admins/{admin_id}/deactivate")
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

def test_deactivate_self_failure(authenticated_admin_client):
    """Test that an admin cannot deactivate themselves."""
    me_resp = authenticated_admin_client.get("/admin/me")
    my_id = me_resp.json()["admin_id"]
    
    response = authenticated_admin_client.put(f"/admin/accounts/admins/{my_id}/deactivate")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot deactivate your own account."

def test_deactivated_admin_login_failure(client, authenticated_admin_client):
    """Test that a deactivated admin cannot log in."""
    # 1. Create another admin
    username = f"admin_{uuid.uuid4().hex[:8]}"
    password = "adminpassword"
    admin_data = {
        "username": username,
        "password": password,
        "email_phone": f"{uuid.uuid4().hex[:8]}@test.com",
    }
    create_resp = authenticated_admin_client.post("/admin/", json=admin_data)
    admin_id = create_resp.json()["admin_id"]
    
    # 2. Deactivate it
    authenticated_admin_client.put(f"/admin/accounts/admins/{admin_id}/deactivate")
    
    # 3. Try to login
    login_resp = client.post("/admin/login", json={"username": username, "password": password})
    assert login_resp.status_code == 403
    assert login_resp.json()["detail"] == "Account is deactivated"

def test_deactivated_admin_access_denied(client, authenticated_admin_client):
    """Test that a deactivated admin's token becomes invalid for secured endpoints."""
    # 1. Create another admin
    username = f"admin_{uuid.uuid4().hex[:8]}"
    password = "adminpassword"
    admin_data = {
        "username": username,
        "password": password,
        "email_phone": f"{uuid.uuid4().hex[:8]}@test.com",
    }
    authenticated_admin_client.post("/admin/", json=admin_data)
    
    # 2. Login to get token
    login_resp = client.post("/admin/login", json={"username": username, "password": password})
    token = login_resp.json()["access_token"]
    
    # 3. Deactivate it using the MAIN admin
    admin_id = authenticated_admin_client.get("/admin/accounts/admins").json()[-1]["admin_id"]
    authenticated_admin_client.put(f"/admin/accounts/admins/{admin_id}/deactivate")
    
    # 4. Try to use the token
    auth_headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/admin/me", headers=auth_headers)
    assert me_resp.status_code == 403
    assert me_resp.json()["detail"] == "Admin account is deactivated"
