
# src/controller/inventory.py
from typing import List, Optional
from decimal import Decimal
from datetime import date

from sqlalchemy.orm import Session
from src.repositories.inventory_repositories import InventoryRepository


class InventoryController:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)

    def set_current_stock(self, product_id: int, new_stock: float | Decimal):
        # Validate input
        if new_stock is None:
            raise ValueError("new_stock must be provided.")
        # Normalize to Decimal to avoid float precision issues
        new_stock_dec = new_stock if isinstance(new_stock, Decimal) else Decimal(str(new_stock))
        if new_stock_dec < Decimal("0"):
            raise ValueError("new_stock must be a non-negative number.")

        inventory = self.inventory_repo.get_by_product_id(product_id)
        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        # Update stock via repository
        return self.inventory_repo.update_stock(product_id, new_stock_dec)

    def record_incoming_stock(self, product_id: int, quantity: float | Decimal, set_restock_date: bool = True):
        if quantity is None:
            raise ValueError("Quantity to add must be provided.")
        qty_dec = quantity if isinstance(quantity, Decimal) else Decimal(str(quantity))
        if qty_dec <= Decimal("0"):
            raise ValueError("Quantity to add must be positive.")

        inventory = self.inventory_repo.get_by_product_id(product_id)
        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        new_stock = (inventory.current_stock or Decimal("0")) + qty_dec

        # Optionally update last_restock_date
        if set_restock_date:
            return self.inventory_repo.update_inventory_fields(
                product_id,
                current_stock=new_stock,
                last_restock_date=date.today(),
            )
        else:
            return self.inventory_repo.update_stock(product_id, new_stock)

    def process_stock_deduction(self, product_id: int, quantity: float | Decimal):
        if quantity is None:
            raise ValueError("Quantity to deduct must be provided.")
        qty_dec = quantity if isinstance(quantity, Decimal) else Decimal(str(quantity))
        if qty_dec <= Decimal("0"):
            raise ValueError("Quantity to deduct must be positive.")

        inventory = self.inventory_repo.get_by_product_id(product_id)
        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        current = inventory.current_stock or Decimal("0")
        if current < qty_dec:
            raise ValueError(f"Insufficient stock (Current: {current}) to deduct {qty_dec}.")

        new_stock = current - qty_dec
        updated_inventory = self.inventory_repo.update_stock(product_id, new_stock)

        # Reorder Alert Logic
        if (
            updated_inventory.min_stock_level is not None
            and updated_inventory.current_stock is not None
            and updated_inventory.current_stock <= updated_inventory.min_stock_level
        ):
            # Replace with your notifier (email, webhook, etc.)
            print(f"NOTIFICATION: Product {product_id} reached reorder level.")

        return updated_inventory

    def check_for_reorder(self) -> List[int]:
        """Returns product_ids that need restocking."""
        all_inventory = self.inventory_repo.list()
        return [
            inv.product_id
            for inv in all_inventory
            if inv.min_stock_level is not None
            and inv.current_stock is not None
            and inv.current_stock <= inv.min_stock_level
        ]
