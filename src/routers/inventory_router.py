# src/api/routes/inventory.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.controller.inventory_controller import InventoryControll
from src.models.inventory_model import InventoryUpdate, InventoryOut
from src.dependency.auth import get_current_user_admin_or_technical, get_current_admin_user

router = APIRouter(
    prefix="/inventory", tags=["Inventory Management"]
)

@router.patch(
    "/{product_id}/stock",
    response_model=InventoryOut,
    dependencies=[Depends(get_current_admin_user)]
)
def set_current_stock(product_id: int, payload: InventoryUpdate, db: Session = Depends(get_db)):
    """
    Overwrite current stock to a specific value (admin-only).
    """
    if payload.current_stock is None:
        raise HTTPException(status_code=400, detail="current_stock is required for this endpoint.")
    svc = InventoryControll(db)
    try:
        # Overwrite, not add
        return svc.set_current_stock(product_id=product_id, new_stock=payload.current_stock)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/{product_id}",
    response_model=InventoryOut,
    dependencies=[Depends(get_current_user_admin_or_technical)]
)
def update_inventory_fields(product_id: int, payload: InventoryUpdate, db: Session = Depends(get_db)):
    """
    Update selected inventory fields (partial update).
    """
    svc = InventoryControll(db)
    inv = svc.inventory_repo.update(
        product_id=product_id,
        current_stock=payload.current_stock,
        min_stock_level=payload.min_stock_level,
        last_restock_data=payload.last_restock_data,  # ensure consistent field name
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return inv

@router.get(
    "/reorder",
    response_model=List[int],
    dependencies=[Depends(get_current_user_admin_or_technical)]
)
def check_for_reorder(db: Session = Depends(get_db)):
    svc = InventoryControll(db)
    return svc.check_for_reorder()

