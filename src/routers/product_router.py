
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.config.database import get_db
from src.controller.product_controller import ProductController
from src.models.product_model import ProductCreate, ProductUpdate , ProductResponse # ORM model (for response via orm_mode)
from pydantic import BaseModel
from src.dependency.auth import get_current_admin_user ,get_optional_user
router = APIRouter(
    prefix="/product", tags=["Product Management"]
)

# --- Routes ---

@router.post("/", response_model= ProductResponse, 
             status_code=201,
             dependencies=[Depends(get_current_admin_user)],
             )
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    svc = ProductController(db)
    try:
        product = svc.create_product(
            name=payload.name,
            selling_price=payload.selling_price,
            unit_cost=payload.unit_cost,
            category_id=payload.category_id,
            initial_stock=payload.initial_stock,
        )
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}", 
            response_model= ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)):
    svc = ProductController(db)
    product = svc.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    svc = ProductController(db)
    if current_user:
        print(f"User {current_user.id} ({current_user.role}) is viewing products.")
    else:
        print("A Guest is viewing products.")
    return svc.list_product(skip=skip, limit=limit)

@router.get("/by-category/{category_id}", 
            response_model=List[ProductResponse],
            dependencies=[Depends(get_optional_user)]
           )
def list_products_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    svc = ProductController(db)
    # Optional: Logic to see what categories are popular with guests vs admins
    # if current_user:
    #     print(f"User {current_user.id} is filtering by category {category_id}")
    try:
        return svc.list_product_by_category(category_id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{product_id}", 
            response_model= ProductResponse,
            dependencies=[Depends(get_current_admin_user)],)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db)
):
    svc = ProductController(db)
    try:
        updated = svc.update_product(
            product_id=product_id,
            name=payload.name,
            selling_price=payload.selling_price,
            unit_cost=payload.unit_cost,
            category_id=payload.category_id,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{product_id}", 
               status_code=204,
               dependencies=[Depends(get_current_admin_user)],)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    svc = ProductController(db)
    deleted = svc.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return None

