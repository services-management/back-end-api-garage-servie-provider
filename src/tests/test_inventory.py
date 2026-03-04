
def test_get_inventory_success(authenticated_admin_client, test_product):
    """Test fetching inventory for a product."""
    product_id = test_product.product_id
    response = authenticated_admin_client.get(f"/inventory/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert "current_stock" in data

def test_set_stock_level(authenticated_admin_client, test_product):
    """Test directly setting the stock level."""
    product_id = test_product.product_id
    payload = {"current_stock": 50.5}
    response = authenticated_admin_client.patch(f"/inventory/{product_id}/stock", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert float(data["current_stock"]) == 50.5

def test_restock_product(authenticated_admin_client, test_product):
    """Test adding to existing stock."""
    product_id = test_product.product_id
    # First set to 10
    authenticated_admin_client.patch(f"/inventory/{product_id}/stock", json={"current_stock": 10})
    
    # Add 5
    response = authenticated_admin_client.post(f"/inventory/{product_id}/restock?quantity=5.5")
    assert response.status_code == 200
    data = response.json()
    assert float(data["current_stock"]) == 15.5

def test_deduct_stock(authenticated_admin_client, test_product):
    """Test deducting from stock."""
    product_id = test_product.product_id
    # First set to 20
    authenticated_admin_client.patch(f"/inventory/{product_id}/stock", json={"current_stock": 20})
    
    # Deduct 7
    response = authenticated_admin_client.post(f"/inventory/{product_id}/deduct?quantity=7")
    assert response.status_code == 200
    data = response.json()
    assert float(data["current_stock"]) == 13.0

def test_deduct_stock_insufficient(authenticated_admin_client, test_product):
    """Test deducting more than available stock."""
    product_id = test_product.product_id
    # First set to 5
    authenticated_admin_client.patch(f"/inventory/{product_id}/stock", json={"current_stock": 5})
    
    # Try to deduct 10
    response = authenticated_admin_client.post(f"/inventory/{product_id}/deduct?quantity=10")
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

def test_low_stock_alerts(authenticated_admin_client, test_product, db_session):
    """Test low stock alert endpoint."""
    product_id = test_product.product_id
    
    # Set min_stock_level to 10 and current_stock to 5
    payload = {"current_stock": 5.0, "min_stock_level": 10.0}
    update_resp = authenticated_admin_client.patch(f"/inventory/{product_id}/stock", json=payload)
    assert update_resp.status_code == 200
    
    # Debug check
    check_resp = authenticated_admin_client.get(f"/inventory/{product_id}")
    print(f"DEBUG: Inventory after patch: {check_resp.json()}")
    
    response = authenticated_admin_client.get("/inventory/alerts/low-stock")
    assert response.status_code == 200
    data = response.json()
    print(f"DEBUG: Alerts returned: {data}")
    assert product_id in data

def test_inventory_permissions(client, test_product, authenticated_technical_client, db_session):
    """Test permissions for inventory endpoints."""
    product_id = test_product.product_id
    
    # 1. Unauthenticated (Guest)
    from fastapi.testclient import TestClient
    from src.app.app import app
    guest_client = TestClient(app)

    resp = guest_client.get(f"/inventory/{product_id}")
    assert resp.status_code == 401

    # 2. Technical staff should be able to GET and DEDUCT but NOT SET or RESTOCK
    from src.repositories.inventory_repositories import InventoryRepository
    inv_repo = InventoryRepository(db_session)
    inv_repo.update_stock(product_id, 10.0)

    assert authenticated_technical_client.get(f"/inventory/{product_id}").status_code == 200
    assert authenticated_technical_client.post(f"/inventory/{product_id}/deduct?quantity=1").status_code == 200
    
    # Technical staff setting stock level (Admin only)
    assert authenticated_technical_client.patch(f"/inventory/{product_id}/stock", json={"current_stock": 10.0}).status_code == 401
    
    # Technical staff restocking (Admin only)
    assert authenticated_technical_client.post(f"/inventory/{product_id}/restock?quantity=10.0").status_code == 401
