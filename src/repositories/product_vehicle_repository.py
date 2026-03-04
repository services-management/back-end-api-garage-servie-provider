
from typing import Optional
from sqlalchemy.orm import Session

from src.schemas.product import ProductVehicleCompatibility 


class ProductVehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def link_product_to_vehicle(self, product_id: int, vehicle_id: int, quantity_required: Optional[str] = None, note: Optional[str] = None):
        # Check if the link already exists to avoid duplicates
        existing = self.db.query(ProductVehicleCompatibility).filter_by(
            product_id=product_id, 
            vehicle_id=vehicle_id
        ).first()

        if existing:
            # Update existing link if new data provided
            if quantity_required is not None:
                existing.quantity_required = quantity_required
            if note is not None:
                existing.note = note
            self.db.commit()
            return existing

        # Create the new association
        new_link = ProductVehicleCompatibility(
            product_id=product_id,
            vehicle_id=vehicle_id,
            quantity_required=quantity_required,
            note=note
        )
        self.db.add(new_link)
        self.db.commit()
        self.db.refresh(new_link)
        return new_link