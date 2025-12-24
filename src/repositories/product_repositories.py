
# src/repositories/product_repository.py

from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from src.repositories.base_repositories import BaseRepository
from src.repositories.inventory_repositories import InventoryRepository
from src.repositories.category_repositories import CategoryRepository
from src.schemas.product import Product  # <-- ORM model, not schema


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

    # --- Create product + auto-create inventory (atomic) ---
    def create(
        self,
        name: str,
        selling_price: Decimal | float,
        unit_cost: Optional[Decimal | float] = None,
        category_id: Optional[int] = None,
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

        product = Product(
            name=name,
            selling_price=to_dec(selling_price),
            unit_cost=to_dec(unit_cost),
            category_id=category_id,
        )

        # Atomic transaction: product + inventory
        try:
            with self.db.begin_nested():  
                self.db.add(product)
                # After flush, product_id will be available
                self.db.flush()  # assign PK

                # Create inventory with initial stock
                self.inventory_repo.create_inventory(
                    product_id=product.product_id,
                    current_stock=to_dec(initial_stock) or Decimal("0"),
                    min_stock_level=to_dec(min_stock_level),
                    last_restock_data=last_restock_date,
                )

            # The outer transaction (managed by FastAPI) will handle the final .commit()
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception:
            # session.begin() rolls back automatically on exception
            raise

    # --- Update product ---
    def update(
        self,
        product_id: int,
        name: Optional[str] = None,
        selling_price: Optional[Decimal | float] = None,
        unit_cost: Optional[Decimal | float] = None,
        category_id: Optional[int] = None,
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

        # Use BaseRepository.update(id, data) which commits & refreshes
        return super().update(product_id, update_data)

    # --- Delete product + inventory ---
    def delete(self, product_id: int) -> bool:
        # Delete inventory first (inventory PK == product_id)
        self.inventory_repo.delete_inventory(product_id)
        # Then delete product via BaseRepository
        return super().delete(product_id)
