
from sqlalchemy.orm import Session
from typing import List, Optional

from src.repositories.base_repositories import BaseRepository
from src.repositories.category_repositories import CategoryRepository
from src.repositories.inventory_repositories import InventoryRepository
from src.schemas.product import Product, ProductVehicleCompatibility 
from src.schemas.vehicle import Vehicle


class ProductVehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def link_product_to_vehicle(self, product_id: int, vehicle_id: int):
        # Check if the link already exists to avoid duplicates
        existing = self.db.query(ProductVehicleCompatibility).filter_by(
            product_id=product_id, 
            vehicle_id=vehicle_id
        ).first()
        
        if existing:
            return existing

        # Create the new association
        new_link = ProductVehicleCompatibility(
            product_id=product_id,
            vehicle_id=vehicle_id
        )
        self.db.add(new_link)
        self.db.commit()
        self.db.refresh(new_link)
        return new_link