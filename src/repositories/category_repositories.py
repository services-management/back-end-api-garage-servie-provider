from src.schemas.product import Category
from sqlalchemy.orm import Session
from src.repositories.base_repositories import BaseRepository

class CategoryRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Category)

    # --- Get by ID ---
    def get_by_id(self, category_id: int) -> Category | None:
        return self.db.query(Category).filter(Category.categoryID == category_id).first()

    # --- Get by Name ---
    def get_by_name(self, name: str) -> Category | None:
        return self.db.query(Category).filter(Category.name == name).first()

    # --- List all with optional pagination ---
    def list(self, skip: int = 0, limit: int = 100) -> list[Category]:
        return self.db.query(Category).offset(skip).limit(limit).all()

    # --- Create category ---
    def create(self, name: str, description: str | None = None) -> Category:
        new_category = Category(name=name, description=description)
        self.db.add(new_category)
        self.db.commit()
        self.db.refresh(new_category)
        return new_category

    # --- Update category ---
    def update(self, category_id: int, name: str | None = None, description: str | None = None) -> Category | None:
        category = self.get_by_id(category_id)
        if not category:
            return None
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        self.db.commit()
        self.db.refresh(category)
        return category

    # --- Delete category ---
    def delete(self, category_id: int) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False
        self.db.delete(category)
        self.db.commit()
        return True
