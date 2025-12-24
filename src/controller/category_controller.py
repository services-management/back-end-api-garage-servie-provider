
# src/controllers/category_controller.py

from typing import Optional, List
from sqlalchemy.orm import Session
from src.repositories.category_repositories import CategoryRepository
from src.schemas.product import Category  # ORM model


class CategoryController:
    def __init__(self, db: Session):
        self.category_repo = CategoryRepository(db)

    def create_category(self, name: str, description: Optional[str] = None) -> Category:
        # 1) Validation
        if not name or not name.strip():
            raise ValueError("Category name is required.")
        name = name.strip()

        # 2) Duplicate check
        if self.category_repo.get_by_name(name):
            raise ValueError(f"Category with name '{name}' already exists.")

        # 3) Create via repository
        return self.category_repo.create(name=name, description=description)

    def get_category(self, category_id: int) -> Category:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found.")
        return category

    def list_category(self, skip: int = 0, limit: int = 100) -> List[Category]:
        return self.category_repo.list(skip=skip, limit=limit)

    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Category:
        # Ensure category exists (will raise if not)
        category = self.get_category(category_id)

        # Validate name change and check duplicates
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Category name cannot be blank.")
            if name != category.name and self.category_repo.get_by_name(name):
                raise ValueError(f"Category with name '{name}' already exists.")

        # Call repository's update (method name must match your repo)
        updated = self.category_repo.update(
            category_id=category_id,
            name=name,
            description=description
        )
        if not updated:
            # Shouldn't happen because we validated existence earlier
            raise ValueError(f"Failed to update category ID {category_id}.")
        return updated

    def delete_category(self, category_id: int) -> bool:
        # Ensure category exists before delete to provide a clear error
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found.")

        # Use repository delete (expects an ID)
        return self.category_repo.delete(category_id)
