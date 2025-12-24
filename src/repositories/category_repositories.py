
# src/repositories/category_repository.py

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.repositories.base_repositories import BaseRepository
from src.schemas.product import Category  # <-- use the SQLAlchemy model


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)

    # --- Get by ID (use BaseRepository.get) ---
    def get_by_id(self, category_id: int) -> Optional[Category]:
        return super().get(category_id)

    # --- Get by Name ---
    def get_by_name(self, name: str) -> Optional[Category]:
        stmt = select(Category).where(Category.name == name)
        return self.db.execute(stmt).scalars().first()

    # --- List all with optional pagination ---
    def list(self, skip: int = 0, limit: int = 100) -> List[Category]:
        # Uses SQLAlchemy 2.0 select/scalars pattern
        stmt = select(Category).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    # --- Create category ---
    def create(self, name: str, description: Optional[str] = None) -> Category:
        new_category = Category(name=name, description=description)
        return super().add(new_category)

    # --- Update category ---
    def update(self, category_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Category]:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        # BaseRepository.update expects (id, data)
        return super().update(category_id, update_data)

    # --- Delete category ---
    def delete(self, category_id: int) -> bool:
        # BaseRepository.delete expects (id)
        return super().delete(category_id)
