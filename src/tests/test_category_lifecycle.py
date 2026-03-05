
def test_category_lifecycle(authenticated_admin_client):
    # 1. Create
    create_resp = authenticated_admin_client.post(
        "/category/",
        json={"name": "Lifecycle Category", "description": "Testing category lifecycle"}
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.json()["categoryID"]

    # 2. Get
    get_resp = authenticated_admin_client.get(f"/category/{cat_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Lifecycle Category"

    # 3. List
    list_resp = authenticated_admin_client.get("/category/")
    assert list_resp.status_code == 200
    assert any(c["categoryID"] == cat_id for c in list_resp.json())

    # 4. Patch (Update)
    patch_resp = authenticated_admin_client.patch(
        f"/category/{cat_id}",
        json={"name": "Updated Category", "description": "Updated description"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Category"

    # 5. Delete
    del_resp = authenticated_admin_client.delete(f"/category/{cat_id}")
    assert del_resp.status_code == 200 # Router returns bool for delete
    
    # 6. Verify Delete
    get_after_del = authenticated_admin_client.get(f"/category/{cat_id}")
    assert get_after_del.status_code == 404

def test_product_lifecycle(authenticated_admin_client, test_category, db_session):
    # Ensure category is bound to session
    db_session.add(test_category)
    
    # 1. Create
    payload = {
        "name": "Lifecycle Product",
        "selling_price": 100.0,
        "category_name": test_category.name,
        "initial_stock": 10.0
    }
    create_resp = authenticated_admin_client.post("/product/", json=payload)
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["product_id"]

    # 2. Get
    get_resp = authenticated_admin_client.get(f"/product/{prod_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Lifecycle Product"

    # 3. Put (Update)
    update_payload = {
        "name": "Updated Product",
        "selling_price": 120.0,
        "category_name": test_category.name
    }
    update_resp = authenticated_admin_client.put(f"/product/{prod_id}", json=update_payload)
    assert update_resp.status_code == 200
    # API returns decimal as string "120.00"
    assert float(update_resp.json()["selling_price"]) == 120.0

    # 4. List by Category
    cat_list_resp = authenticated_admin_client.get(f"/product/by-category/{test_category.categoryID}")
    assert cat_list_resp.status_code == 200
    assert any(p["product_id"] == prod_id for p in cat_list_resp.json())

    # 5. Delete
    del_resp = authenticated_admin_client.delete(f"/product/{prod_id}")
    assert del_resp.status_code == 204

    # 6. Verify Delete (should not be in public list)
    list_resp = authenticated_admin_client.get("/product/")
    assert not any(p["product_id"] == prod_id for p in list_resp.json())

def test_product_filter_by_vehicle(authenticated_admin_client, test_product, test_vehicle_camry_2022, db_session):
    # Use add instead of refresh to avoid InvalidRequestError if it's already detached
    db_session.add(test_product)
    db_session.add(test_vehicle_camry_2022)

    # 1. Link product to vehicle
    link_resp = authenticated_admin_client.post(
        f"/product/{test_product.product_id}/vehicle/{test_vehicle_camry_2022.vehicle_id}",
        params={"quantity_required": 1, "unit": "unit"}
    )
    assert link_resp.status_code == 201

    # 2. Filter
    params = {
        "make": "Toyota",
        "model": "Camry",
        "year": 2022
    }
    filter_resp = authenticated_admin_client.get("/product/filter-by-vehicle", params=params)
    assert filter_resp.status_code == 200
    data = filter_resp.json()
    assert len(data) >= 1
    assert any(p["product_id"] == test_product.product_id for p in data)
