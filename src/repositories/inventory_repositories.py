
# src/repositories/inventory_repository.py

from typing import Optional, Dict, Any
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.repositories.base_repositories import BaseRepository
from src.schemas.product import Inventory  # <-- use the SQLAlchemy model


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self, db: Session):
        super().__init__(db, Inventory)

    # --- Get by product ID (Primary Key of inventory table) ---
    def get_by_product_id(self, product_id: int) -> Optional[Inventory]:
        # Since product_id is the PK for Inventory, Session.get is ideal
        return self.db.get(Inventory, product_id)

    # --- Create inventory ---
    def create_inventory(
        self,
        product_id: int,
        current_stock: Decimal | float = Decimal("0"),
        min_stock_level: Optional[Decimal | float] = None,
        last_restock_date: Optional[date] = None,  # fixed name
    ) -> Inventory:
        # Convert floats to Decimal for precision (matches Numeric(10,2))
        def to_decimal(v: Decimal | float | None) -> Optional[Decimal]:
            if v is None:
                return None
            return v if isinstance(v, Decimal) else Decimal(str(v))

        new_inventory = Inventory(
            product_id=product_id,
            current_stock=to_decimal(current_stock) or Decimal("0"),
            min_stock_level=to_decimal(min_stock_level),
            last_restock_data=last_restock_date,
        )
        self.db.add(new_inventory)
        self.db.flush()  # Syncs with DB and gets IDs without committing
        
        return new_inventory

    # --- Update inventory fields (safe scalar update via BaseRepository) ---
    def update_inventory_fields(self, product_id: int, **kwargs: Any) -> Optional[Inventory]:
        """
        Updates scalar columns only using BaseRepository.update(id, data).
        Any relationship fields will be ignored by BaseRepository's mapper-safe logic.
        """
        numeric_keys = {"current_stock", "min_stock_level"}
        for k in list(kwargs.keys()):
            if k in numeric_keys and kwargs[k] is not None:
                kwargs[k] = Decimal(str(kwargs[k]))

        # 2. CRITICAL FIX: Map 'date' (from controller/schema) to 'data' (in Model)
        # We want to make sure we are sending 'last_restock_data' to the BaseRepository
        if "last_restock_date" in kwargs:
            kwargs["last_restock_data"] = kwargs.pop("last_restock_date")
        
        # Optional: If your controller sometimes sends it correctly as 'last_restock_data'
        # but the old code was renaming it to 'date', remove that old renaming logic!

        return super().update(product_id, kwargs)

    # --- Update stock only ---
    def update_stock(self, product_id: int, new_stock: Decimal | float) -> Optional[Inventory]:
        return self.update_inventory_fields(product_id, current_stock=new_stock)

    # --- Delete inventory ---
    def delete_inventory(self, product_id: int) -> bool:
        # BaseRepository.delete expects an ID (not an object)
        return super().delete(product_id)

