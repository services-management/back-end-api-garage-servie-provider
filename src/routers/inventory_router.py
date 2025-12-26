from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.controller.inventory_controller import InventoryController
from src.repositories.inventory_repositories import InventoryRepository
from src.models.inventory_model import InventoryOut, InventoryUpdate, InventorySnapshot
from src.dependency.auth import get_current_user_admin_or_technical, get_current_admin_user
router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Management"],
)

@router.get("/{product_id}", 
            response_model=InventoryOut,
            dependencies=[Depends(get_current_user_admin_or_technical)])
def get_inventory_by_product(product_id: int, db: Session = Depends(get_db)):
    """Fetch the inventory details for a specific product."""
    controller = InventoryRepository(db)
    inventory = controller.get_by_product_id(product_id)
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No inventory record found for product ID {product_id}"
        )
    return inventory

@router.patch("/{product_id}/stock", 
              response_model=InventoryOut,
              dependencies=[Depends(get_current_admin_user)])
def set_stock_level(product_id: int, update_data: InventoryUpdate, db: Session = Depends(get_db)):
    """Directly set the current stock level."""
    if update_data.current_stock is None:
        raise HTTPException(status_code=400, detail="current_stock is required for this operation")
    
    try:
        controller = InventoryController(db)
        return controller.set_current_stock(product_id, update_data.current_stock)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{product_id}/restock", 
             response_model=InventoryOut,
             dependencies=[Depends(get_current_admin_user)])
def add_incoming_stock(product_id: int, quantity: float, db: Session = Depends(get_db)):
    """Add to existing stock (e.g., after receiving a shipment)."""
    try:
        controller = InventoryController(db)
        return controller.record_incoming_stock(product_id, quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{product_id}/deduct", 
             response_model=InventoryOut,
             dependencies=[Depends(get_current_user_admin_or_technical)])
def deduct_stock_level(product_id: int, quantity: float, db: Session = Depends(get_db)):
    """Deduct stock (e.g., after a sale or usage)."""
    try:
        controller = InventoryController(db)
        return controller.process_stock_deduction(product_id, quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/alerts/low-stock", 
            response_model=List[int],
            dependencies=[Depends(get_current_user_admin_or_technical)])
def get_low_stock_product_ids(db: Session = Depends(get_db)):
    """Get a list of Product IDs where stock is at or below the minimum level."""
    controller = InventoryController(db)
    return controller.check_for_reorder()