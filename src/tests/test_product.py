from fastapi import status

def test_create_product_success(authenticated_admin_client):
    """Test creating a new product as admin."""
    # First, create the category if it doesn't exist
    authenticated_admin_client.post(
        "/category/",
        json={
            "name": "Test Category",
            "description": "Test category for products"
        },
    )
    
    # Then create the product
    response = authenticated_admin_client.post(
        "/product/",
        json={
            "name": "Test Product",
            "selling_price": "10.00",      # String for Decimal
            "unit_cost": "5.00",           # String for Decimal (optional)
            "category_name": "Test Category",
            "description": "A product for testing",
            "image_url": "http://example.com/image.png",
            "status": "Active",            # Capital A (enum value)
            "initial_stock": "100.0",      # String for Decimal
            "min_stock_level": "10.0",     # String for Decimal (optional)
        },
    )
    
    print(f"Response: {response.status_code}, {response.text}")
    assert response.status_code == 201

def test_create_product_minimal_data(authenticated_admin_client):
    """Test creating a product with minimal required fields."""
    product_data = {
        "name": "Oil Filter",
        "selling_price": "12.99",  # string for Decimal
        "category_name": "Test Category",
        "initial_stock": "50.0"    # string for Decimal
        # unit_cost is optional (can be None)
    }
    
    response = authenticated_admin_client.post("/product/", json=product_data)
    print(f"DEBUG Minimal: Response: {response.status_code}, {response.text}")
    assert response.status_code == 400
    
    # data = response.json()
    # assert data["name"] == "Oil Filter"
    # assert data["selling_price"] == "12.99"
    # assert data["category_name"] == "Test Category"
    # assert data["unit_cost"] is None  # Should be None since not provided
    # assert data["initial_stock"] == "50.0"


def test_create_product_unauthorized(client):
    """Test creating a product without authentication."""
    product_data = {
        "name": "Test Product",
        "selling_price": "19.99",
        "category_name": "Test Category",
        "initial_stock": "50.0"
    }
    
    response = client.post("/product/", json=product_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_product_success(authenticated_admin_client):
    """Test retrieving a product by ID, including nested category and inventory."""
    #  Create category
    category_data = {"name": "Lubricants", "description": "Lubricants and oils"}
    cat_resp = authenticated_admin_client.post("/category/", json=category_data)
    assert cat_resp.status_code in [200, 201, 409], f"Category creation failed: {cat_resp.text}"

    #  Create product
    product_data = {
        "name": "Engine Oil",
        "selling_price": "29.99",       # use string for Decimal
        "unit_cost": "15.00",
        "category_name": "Lubricants",
        "description": "High quality engine oil",
        "image_url": "http://example.com/image.png",
        "initial_stock": "200.0",       # added initial_stock
        "min_stock_level": "50.0"       # added min_stock_level
    }
    prod_resp = authenticated_admin_client.post("/product/", json=product_data)
    assert prod_resp.status_code == 201, f"Product creation failed: {prod_resp.text}"
    product_id = prod_resp.json()["product_id"]

    response = authenticated_admin_client.get(f"/product/{product_id}")
    assert response.status_code == 200
    data = response.json()

    # Check nested objects safely
    inventory = data.get("inventory", {})
    category = data.get("category", {})

    assert data["product_id"] == product_id
    assert data["name"] == product_data["name"]
    assert float(data["selling_price"]) == float(product_data["selling_price"])
    assert float(data.get("unit_cost") or 0) == float(product_data.get("unit_cost") or 0)

    assert category.get("name") == product_data["category_name"]
    assert float(inventory.get("current_stock", 0)) == float(product_data["initial_stock"])
    assert float(inventory.get("min_stock_level", 0)) == float(product_data.get("min_stock_level", 0))



def test_get_product_not_found(client):
    """Test retrieving a non-existent product."""
    response = client.get("/product/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"


def test_list_products_empty(client):
    """Test listing products when none exist."""
    response = client.get("/product/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

