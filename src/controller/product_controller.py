
# src/controller/product.py

from typing import Optional, List
from decimal import Decimal

from sqlalchemy.orm import Session

from src.repositories.product_repositories import ProductRepository
from src.repositories.category_repositories import CategoryRepository
from src.schemas.product import Product  # use ORM model, not schema


class ProductController:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        # Inventory operations are handled inside ProductRepository (atomic create + delete)

    def create_product(
        self,
        name: str,
        selling_price: Decimal | float,
        unit_cost: Optional[Decimal | float] = None,
        category_id: Optional[int] = None,
        initial_stock: Decimal | float = Decimal("0"),
        min_stock_level: Optional[Decimal | float] = None,
        last_restock_date: Optional["date"] = None,
    ) -> Product:
        # 1) Name uniqueness
        if self.product_repo.get_by_name(name):
            raise ValueError(f"Product with name '{name}' already exists.")

        # 2) Category existence (if provided)
        if category_id is not None and not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")

        # 3) Delegate to repository (atomic product + inventory creation inside repo)
        # NOTE: Call the actual method name your repo defines.
        product = self.product_repo.create(
            name=name,
            selling_price=selling_price,
            unit_cost=unit_cost,
            category_id=category_id,
            initial_stock=initial_stock,
            min_stock_level=min_stock_level,
            last_restock_date=last_restock_date,
        )
        return product

    def get_product(self, product_id: int) -> Optional[Product]:
        """Retrieve a product by ID."""
        return self.product_repo.get_by_id(product_id)

    def list_product(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """List products with pagination."""
        return self.product_repo.list(skip=skip, limit=limit)

    def list_product_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """List products filtered by category with pagination."""
        if not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")
        return self.product_repo.list_by_category(category_id, skip=skip, limit=limit)

    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        selling_price: Optional[Decimal | float] = None,
        unit_cost: Optional[Decimal | float] = None,
        category_id: Optional[int] = None,
    ) -> Optional[Product]:
        """
        Update a product's fields.
        Rules:
          - name must remain unique if changed
          - category_id must refer to an existing category if changed
        Returns updated product or None if not found.
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None

        # Name uniqueness check (only if provided and changed)
        if name is not None:
            name_stripped = name.strip()
            if not name_stripped:
                raise ValueError("Product name cannot be blank.")
            if name_stripped != product.name and self.product_repo.get_by_name(name_stripped):
                raise ValueError(f"Product with name '{name_stripped}' already exists.")

        # Category existence check
        if category_id is not None and not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")

        # Delegate to repository update
        updated = self.product_repo.update(
            product_id=product_id,
            name=name.strip() if isinstance(name, str) else name,
            selling_price=selling_price,
            unit_cost=unit_cost,
            category_id=category_id,
        )
        return updated

    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product. Repository handles deleting inventory first.
        Returns True when deleted, False if product not found.
        """
        return self.product_repo.delete(product_id)
