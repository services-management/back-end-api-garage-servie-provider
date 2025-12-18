from sqlalchemy.orm import Session
from src.repositories.category_repository import CategoryRepository
from typing import Optional, List

class CategoryControll:
    def __init__(self,db:Session):
        self.category_repo = CategoryRepository(db)

    def create_category(self,name:str, description: Optional[str] = None):
        
        
        if not name or not name.strip():
            raise ValueError("Category name is required.")
        name = name.strip()

        if self.category_repo.get_by_name(name):
            raise ValueError(f"Category with name '{name} already exists.")
        
        return self.category_repo.create(name=name, description=description)
    
    def get_category(self, category_id:int):
        return self.category_repo.get_by_id(category_id)
    
    def list_category(self,skip:int = 0 , limit: int = 100):
        return self.category_repo.list(skip=skip, limit=limit)

    def update_category(self,category_id:int, name:Optional[str]=None, description: Optional[str] = None):
        category = self.get_category(category_id)

        if not category:
            raise ValueError(f"Category with ID {category_id} not found.")
        
        if name and name != category.name:
            if self.category_repo.get_by_name(name):
                raise ValueError(f"Category with name '{name}' already exists.")
            
        return self.category_repo.update(category_id,name=name, description=description) # Assuming a generic update method
    
    def delete_category(self, category_id: int) -> bool:
        """
        Deletes a category. Returns True if deletion occurred, False if not found.
        """
        category = self.get_category(category_id)
        if not category:
            return False
        return self.category_repo.delete(category_id)
