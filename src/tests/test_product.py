from fastapi.testclient import TestClient


# Test creating a product
def test_create_product_success(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.post(
        "/product/",
        json={
            "name": "Test Product",
            "selling_price": 10.0,
            "unit_cost": 5.0,
            "category_name": "Test Category",
            "description": "A product for testing",
            "image_url": "http://example.com/image.png",
            "status": "active",
            "initial_stock": 100,
            "min_stock_level": 10,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["selling_price"] == 10.0
    assert "product_id" in data

def test_create_product_invalid_price(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.post(
        "/product/",
        json={
            "name": "Test Product Invalid",
            "selling_price": -10.0,
            "unit_cost": 5.0,
            "category_name": "Test Category",
            "description": "A product for testing",
            "image_url": "http://example.com/image.png",
            "status": "active",
            "initial_stock": 100,
            "min_stock_level": 10,
        },
    )
    assert response.status_code == 422 # pydantic validation error

def test_create_product_unauthenticated(client: TestClient):
    response = client.post(
        "/product/",
        json={
            "name": "Test Product Unauthenticated",
            "selling_price": 10.0,
            "unit_cost": 5.0,
            "category_name": "Test Category",
            "description": "A product for testing",
            "image_url": "http://example.com/image.png",
            "status": "active",
            "initial_stock": 100,
            "min_stock_level": 10,
        },
    )
    assert response.status_code == 401

def test_create_product_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.post(
        "/product/",
        json={
            "name": "Test Product as Technical",
            "selling_price": 10.0,
            "unit_cost": 5.0,
            "category_name": "Test Category",
            "description": "A product for testing",
            "image_url": "http://example.com/image.png",
            "status": "active",
            "initial_stock": 100,
            "min_stock_level": 10,
        },
    )
    assert response.status_code == 403 # Forbidden


# Test getting a product
def test_get_product_success(client: TestClient, authenticated_admin_client: TestClient):
    # Create a product first
    create_response = authenticated_admin_client.post(
        "/product/",
        json={
            "name": "Product to Get",
            "selling_price": 20.0,
            "unit_cost": 10.0,
            "category_name": "Get Category",
            "description": "A product for getting",
            "image_url": "http://example.com/get.png",
            "status": "active",
            "initial_stock": 50,
            "min_stock_level": 5,
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]

    # Get the product
    get_response = client.get(f"/product/{product_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["name"] == "Product to Get"
    assert data["product_id"] == product_id

def test_get_product_not_found(client: TestClient):
    response = client.get("/product/999999")
    assert response.status_code == 404

# Test getting all products
def test_get_all_products(client: TestClient):
    response = client.get("/product/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test updating a product
def test_update_product_success(authenticated_admin_client: TestClient):
    # Create a product
    create_response = authenticated_admin_client.post(
        "/product/",
        json={
            "name": "Product to Update",
            "selling_price": 30.0,
            "unit_cost": 15.0,
            "category_name": "Update Category",
            "description": "A product for updating",
            "image_url": "http://example.com/update.png",
            "status": "active",
            "initial_stock": 20,
            "min_stock_level": 2,
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]

    # Update the product
    update_response = authenticated_admin_client.put(
        f"/product/{product_id}",
        json={"name": "Updated Product Name", "selling_price": 35.0},
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Product Name"
    assert data["selling_price"] == 35.0

def test_update_product_not_found(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.put(
        "/product/999999",
        json={"name": "Won't Update"},
    )
    assert response.status_code == 404

def test_update_product_unauthenticated(client: TestClient):
    response = client.put(
        "/product/1",
        json={"name": "Won't Update"},
    )
    assert response.status_code == 401

def test_update_product_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.put(
        "/product/1",
        json={"name": "Won't Update"},
    )
    assert response.status_code == 403

# Test deleting a product
def test_delete_product_success(authenticated_admin_client: TestClient):
    # Create a product
    create_response = authenticated_admin_client.post(
        "/product/",
        json={
            "name": "Product to Delete",
            "selling_price": 40.0,
            "unit_cost": 20.0,
            "category_name": "Delete Category",
            "description": "A product for deleting",
            "image_url": "http://example.com/delete.png",
            "status": "active",
            "initial_stock": 10,
            "min_stock_level": 1,
        },
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]

    # Delete the product
    delete_response = authenticated_admin_client.delete(f"/product/{product_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = authenticated_admin_client.get(f"/product/{product_id}")
    assert get_response.status_code == 404

def test_delete_product_not_found(authenticated_admin_client: TestClient):
    response = authenticated_admin_client.delete("/product/999999")
    assert response.status_code == 404

def test_delete_product_unauthenticated(client: TestClient):
    response = client.delete("/product/1")
    assert response.status_code == 401

def test_delete_product_as_technical_user(authenticated_technical_client: TestClient):
    response = authenticated_technical_client.delete("/product/1")
    assert response.status_code == 403
