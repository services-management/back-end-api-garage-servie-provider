
# src/controller/inventory.py
from sqlalchemy.orm import Session
from typing import List, Optional
from src.repositories.inventoryrepository_repositorie import InventoryRepository

class InventoryControll:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)

    def set_current_stock(self, product_id: int, new_stock: float):
        """
        Overwrites current stock to an explicit value (admin correction).
        """
        if new_stock is None:
            raise ValueError("new_stock must be provided.")
        if new_stock < 0:
            raise ValueError("new_stock cannot be negative.")

        inventory = self.inventory_repo.get_by_product_id(product_id)
        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        return self.inventory_repo.update_stock(product_id, new_stock)

    def record_incoming_stock(self, product_id: int, quantity: float):
        """
        Adds stock to inventory (increment).
        """
        if quantity is None or quantity <= 0:
            raise ValueError("Quantity must be positive.")

        inventory = self.inventory_repo.get_by_product_id(product_id)
        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        new_stock = inventory.current_stock + quantity
        return self.inventory_repo.update_stock(product_id, new_stock)

    def process_stock_deduction(self, product_id: int, quantity: float):
        """
        Deducts stock (e.g., from sale/loss).
        """
        if quantity is None or quantity <= 0:
            raise ValueError("Quantity must be positive.")

        inventory = self.inventory_repo.get_by_product_id(product_id)
        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        new_stock = inventory.current_stock - quantity
        if new_stock < 0:
            raise ValueError(
                f"Insufficient stock (Current: {inventory.current_stock}) to deduct {quantity}."
            )

        updated_inventory = self.inventory_repo.update_stock(product_id, new_stock)

        # Reorder check
        if (
            updated_inventory.min_stock_level is not None
            and updated_inventory.current_stock <= updated_inventory.min_stock_level
        ):
            # TODO: integrate real notifier
            print(f"ALERT: Product {product_id} is at or below reorder point!")

        return updated_inventory

    def check_for_reorder(self) -> List[int]:
        """
        Returns product_ids at or below min_stock_level.
        """
        low_stock_products: List[int] = []
        for inv in self.inventory_repo.list():
            if inv.min_stock_level is not None and inv.current_stock <= inv.min_stock_level:
                low_stock_products.append(inv.product_id)
        return low_stock_products

