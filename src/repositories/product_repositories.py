
# src/repositories/product_repository.py

from datetime import date
from decimal import Decimal
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.repositories.base_repositories import BaseRepository
from src.repositories.category_repositories import CategoryRepository
from src.repositories.inventory_repositories import InventoryRepository
from src.schemas.product import Product,ProductStatus  


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(db, Product)
        self.inventory_repo = InventoryRepository(db)
        self.category_repo = CategoryRepository(db)

    # --- Get by product ID ---
    def get_by_id(self, product_id: int) -> Optional[Product]:
        # Prefer Session.get for PK lookups
        return self.db.get(Product, product_id)

    # Optionally with eager loading of relationships:
    def get_by_id_with_relations(self, product_id: int) -> Optional[Product]:
        stmt = (
            select(Product)
            .options(
                joinedload(Product.category),  # eager load category
                joinedload(Product.inventory)  # eager load inventory (one-to-one)
            )
            .where(Product.product_id == product_id)
        )
        return self.db.execute(stmt).scalars().first()

    # --- Get by name ---
    def get_by_name(self, name: str) -> Optional[Product]:
        stmt = select(Product).where(Product.name == name)
        return self.db.execute(stmt).scalars().first()

    # --- List products with optional pagination ---
    def list(self, skip: int = 0, limit: int = 100) -> List[Product]:
        stmt = select(Product).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
    
    def list_active(self, skip: int = 0, limit: int = 100) -> List[Product]:
        stmt = select(Product).where(Product.status == ProductStatus.ACTIVE).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    # Optional: list with eager loading (useful for API responses)
    def list_with_relations(self, skip: int = 0, limit: int = 100) -> List[Product]:
        stmt = (
            select(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.inventory)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    # --- List products by category ---
    def list_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        stmt = (
            select(Product)
            .where(Product.category_id == category_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def filter_by_vehicle(
        self,
        make_name: str,
        model_name: str,
        year: int,
        vehicle_type: Optional[Any] = None,
        fuel_type: Optional[Any] = None,
        drive_type: Optional[Any] = None,
        transmission: Optional[Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        from src.schemas.vehicle import Make, Model, Vehicle
        from src.schemas.product import ProductVehicleCompatibility
        
        stmt = (
            select(Product)
            .join(ProductVehicleCompatibility, Product.product_id == ProductVehicleCompatibility.product_id)
            .join(Vehicle, ProductVehicleCompatibility.vehicle_id == Vehicle.vehicle_id)
            .join(Model, Vehicle.model_id == Model.id)
            .join(Make, Model.make_id == Make.id)
            .where(
                Make.name == make_name,
                Model.name == model_name,
                Vehicle.year == year,
                Product.status == ProductStatus.ACTIVE
            )
        )
        
        if vehicle_type:
            stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)
        if fuel_type:
            stmt = stmt.where(Vehicle.fuel_type == fuel_type)
        if drive_type:
            stmt = stmt.where(Vehicle.drive_type == drive_type)
        if transmission:
            stmt = stmt.where(Vehicle.transmission == transmission)
            
        stmt = stmt.options(
            joinedload(Product.category),
            joinedload(Product.inventory),
            joinedload(Product.vehicle_links)
        ).offset(skip).limit(limit)
        
        return list(self.db.execute(stmt).scalars().unique().all())

    # --- Create product + auto-create inventory (atomic) ---
    def create(
        self,
        name: str,
        selling_price: Decimal | float,
        unit_cost: Optional[Decimal | float] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None, # Added
        image_url: Optional[str] = None,   # Added
        status: Any = None,                # Added (ProductStatus Enum)
        initial_stock: Decimal | float = Decimal("0"),
        min_stock_level: Optional[Decimal | float] = None,
        last_restock_date: Optional["date"] = None,  # if you want to set it initially
    ) -> Product:
        # Validate category if provided
        if category_id is not None and not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")

        # Normalize money/stock to Decimal for precision
        def to_dec(v):
            if v is None:
                return None
            return v if isinstance(v, Decimal) else Decimal(str(v))

       # 1. Start a single atomic transaction block
        try:
            # We don't necessarily need 'with' if we manage the session externally,
            # but for a repo 'create', we want to ensure both happen or none.

            product = Product(
                name=name,
                selling_price=to_dec(selling_price),
                unit_cost=to_dec(unit_cost),
                category_id=category_id,
                description=description,
                image_url=image_url,
                status=status
            )

            self.db.add(product)
            # FLUSH is key: It sends the INSERT to the DB and gets the product_id
            # WITHOUT ending the transaction yet.
            self.db.flush()

            # 2. Use the ID from the flushed product to create Inventory
            self.inventory_repo.create_inventory(
                product_id=product.product_id,
                current_stock=to_dec(initial_stock) or Decimal("0"),
                min_stock_level=to_dec(min_stock_level),
                last_restock_date=last_restock_date,
            )

            # 3. Commit EVERYTHING at once
            self.db.commit()
            self.db.refresh(product)
            return product

        except Exception as e:
            # If ANY part fails, undo everything (Product + Inventory)
            self.db.rollback()
            raise e

    # --- Update product ---
    def update(
        self,
        product_id: int,
        name: Optional[str] = None,
        selling_price: Optional[Decimal | float] = None,
        unit_cost: Optional[Decimal | float] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None, # Added
        image_url: Optional[str] = None,   # Added
        status: Any = None,               # Added (ProductStatus Enum)
    ) -> Optional[Product]:
        # Category validation if provided
        if category_id is not None and not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")

        # Prepare safe scalar update dict for BaseRepository.update
        def to_dec(v):
            if v is None:
                return None
            return v if isinstance(v, Decimal) else Decimal(str(v))

        update_data = {}
        if name is not None:
            update_data["name"] = name.strip() if isinstance(name, str) else name
        if selling_price is not None:
            update_data["selling_price"] = to_dec(selling_price)
        if unit_cost is not None:
            update_data["unit_cost"] = to_dec(unit_cost)
        if category_id is not None:
            update_data["category_id"] = category_id
        if description is not None:
            update_data["description"] = description
        if image_url is not None:
            update_data["image_url"] = image_url
        if status is not None:
            update_data["status"] = status
        # Use BaseRepository.update(id, data) which commits & refreshes
        return super().update(product_id, update_data)

    # --- soft delete product ---
    def delete(self, product_id: int) -> bool:
        # Delete inventory first (inventory PK == product_id)
        stmt =  self.db.get(Product, product_id)
        if not stmt:
            return False
        
        update_product = self.update(product_id=product_id,status=ProductStatus.INACTIVE)

        return update_product is not None
