from src.schemas.product import Inventory
from sqlalchemy.orm import Session
from src.repositories.baserepository_repositorie import BaseRepository
from datetime import date
from typing import Optional

class InventoryRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Inventory)

    # --- Get by product ID ---
    def get_by_product_id(self, product_id: int) -> Optional[Inventory]:
        return self.db.query(Inventory).filter(Inventory.product_id == product_id).first()

    # --- Create inventory ---
    def create(self, product_id: int, current_stock: float = 0, 
               min_stock_level: Optional[float] = None, 
               last_restock_data: Optional[date] = None) -> Inventory:
        new_inventory = Inventory(
            product_id=product_id,
            current_stock=current_stock,
            min_stock_level=min_stock_level,
            last_restock_data=last_restock_data
        )
        self.db.add(new_inventory)
        self.db.commit()
        self.db.refresh(new_inventory)
        return new_inventory

    # --- Update inventory fields ---
    def update(self, product_id: int, current_stock: Optional[float] = None, 
               min_stock_level: Optional[float] = None, 
               last_restock_data: Optional[date] = None) -> Optional[Inventory]:
        inventory = self.get_by_product_id(product_id)
        if not inventory:
            return None
        if current_stock is not None:
            inventory.current_stock = current_stock
        if min_stock_level is not None:
            inventory.min_stock_level = min_stock_level
        if last_restock_data is not None:
            inventory.last_restock_data = last_restock_data
        self.db.commit()
        self.db.refresh(inventory)
        return inventory

    # --- Update stock only ---
    def update_stock(self, product_id: int, new_stock: float) -> Optional[Inventory]:
        return self.update(product_id, current_stock=new_stock)

    # --- Delete inventory ---
    def delete(self, product_id: int) -> bool:
        inventory = self.get_by_product_id(product_id)
        if not inventory:
            return False
        self.db.delete(inventory)
        self.db.commit()
        return True
