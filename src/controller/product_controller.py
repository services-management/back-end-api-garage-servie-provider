
# src/controller/product.py

from typing import Optional, List, Any
from decimal import Decimal
from datetime import date # Added import

from sqlalchemy.orm import Session

from src.repositories.product_repositories import ProductRepository
from src.repositories.category_repositories import CategoryRepository
from src.repositories.file_repositories import FileUploadRepository
from src.schemas.product import Product  # use ORM model, not schema


class ProductController:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.file_repo = FileUploadRepository(db)
        # Inventory operations are handled inside ProductRepository (atomic create + delete)

    def create_product(
        self,
        name: str,
        selling_price: Decimal | float,
        unit_cost: Optional[Decimal | float] = None,
        category_name: Optional[str] = None,
        description: Optional[str] = None,
        status: Any = None,
        initial_stock: Decimal | float = Decimal("0"),
        min_stock_level: Optional[Decimal | float] = None,
        last_restock_date: Optional["date"] = None,
    ) -> Product:
        # 1) Name uniqueness

        if self.product_repo.get_by_name(name):
            raise ValueError(f"Product with name '{name}' already exists.")

         # 2) Lookup Category ID by Name
        category_id = None
        if category_name:
            category = self.category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category with name '{category_name}' does not exist.")
            category_id = category.categoryID

        # 3) Delegate to repository (atomic product + inventory creation inside repo)
        # NOTE: Call the actual method name your repo defines.
        product = self.product_repo.create(
            name=name,
            selling_price=selling_price,
            unit_cost=unit_cost,
            category_id=category_id,
            description=description,
            status=status,
            initial_stock=initial_stock,
            min_stock_level=min_stock_level,
            last_restock_date=last_restock_date,
        )
        return product

    def get_product(self, product_id: int) -> Optional[Product]:
        """Retrieve a product by ID."""
        product = self.product_repo.get_by_id(product_id)
        if product:
            product.images = self.file_repo.list_by_product(product_id)
        return product

    def list_product(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """List products with pagination."""
        products = self.product_repo.list(skip=skip, limit=limit)
        for p in products:
            p.images = self.file_repo.list_by_product(p.product_id)
        return products

    def list_product_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """List products filtered by category with pagination."""
        if not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")
        products = self.product_repo.list_by_category(category_id, skip=skip, limit=limit)
        for p in products:
            p.images = self.file_repo.list_by_product(p.product_id)
        return products

    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        selling_price: Optional[Decimal | float] = None,
        unit_cost: Optional[Decimal | float] = None,
        category_name: Optional[str] = None,
        description: Optional[str] = None,
        status: Any = None,
        current_stock: Optional[Decimal | float] = None,
        min_stock_level: Optional[Decimal | float] = None,
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

                # Resolve category ID from name
        resolved_category_id = product.category_id
        if category_name is not None:
            category = self.category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category with name '{category_name}' does not exist.")
            resolved_category_id = category.categoryID


        # Delegate to repository update
        updated = self.product_repo.update(
            product_id=product_id,
            name=name.strip() if isinstance(name, str) else name,
            selling_price=selling_price,
            unit_cost=unit_cost,
            category_id=resolved_category_id,
            description=description,
            status=status,
            current_stock=current_stock,
            min_stock_level=min_stock_level
        )
        return updated

    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product. Repository handles deleting inventory first.
        Returns True when deleted, False if product not found.
        """
        return self.product_repo.delete(product_id)
