from sqlalchemy.orm import Session
from src.repositories.product_repository import ProductRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.inventory_repository import InventoryRepository
from src.schemas.product import Product
from src.schemas.product import ProductCreate, ProductUpdate
from typing import Optional, List

class ProductControll:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.inventory_repo = InventoryRepository(db)
        # Note: It does NOT directly initialize InventoryService or InventoryRepository

    def create_product(self, 
                       name: str, 
                       selling_price: float, 
                       unit_cost: Optional[float] = None, 
                       category_id: Optional[int] = None,
                       initial_stock: float = 0) -> Product: # Inventory logic passed to Repo

        # 1. Business Logic: Name Check
        if self.product_repo.get_by_name(name):
            raise ValueError(f"Product with name '{name}' already exists.")

        # 2. Validation: Category Existence
        if category_id is not None and not self.category_repo.get_by_id(category_id):
            raise ValueError(f"Category with ID {category_id} does not exist.")

        # 3. Repository Call: ProductRepository handles the commit and auto-creation of Inventory
        
        new_product = self.product_repo.create(
            name=name,
            selling_price=selling_price,
            unit_cost=unit_cost,
            category_id=category_id,
            initial_stock=initial_stock,
        )
        return new_product

    # --- Other methods (get, list, update, delete) remain the same ---
    # The 'delete' method in ProductRepository is responsible for deleting the inventory first.
    
    def get_product(self, product_id: int):
        '''retrieve a product by ID.
            return: Product or None if not found'''
        return self.product_repo.get_by_id(product_id)

    def list_product(self, skip:int = 0, limit:int = 100) -> list[Product]:
        '''List product with pagination 
           :param skip Number of records to skip (offset)
           :param limit: Max number of records to return'''
        return self.product_repo.list(skip=skip, limit=limit)
    
    def list_product_by_category(self, category_id:int, skip:int=0, limit:int=100) -> List[Product]:
        '''list products filtered by category with pagination.
            :raise valueError: if category does not exist'''
        if not self.category_repo.get_by_id(category_id):
            raise ValueError(f'Category with ID {category_id} does not exist. ')
        return self.product_repo.list_by_category(category_id, skip=skip, limit=limit)
    
    
    def update_product(
            self,
            product_id: int,
            name: Optional[str] = None,
            selling_price: Optional[float] = None,
            unit_cost: Optional[float] = None,
            category_id: Optional[int] = None,
        ) -> Optional[Product]:
        '''Update a product's fields.
            Business rules :
            - if name change, it must remain unique
            - if category_id change, category must exist.
            
            :raise ValueError: on invalid category or duplicate name
            :return : Update Product or None if not found '''
        Product = self.product_repo.get_by_id(product_id)

        if not Product:
            return None
        
        # Name uniqueness (only if name is provide and different)
        if name is not None and name != Product.name:
            if self.product_repo.get_by_name(name):
                raise ValueError(f'Product with name {name} already exists.')
            
        if category_id is not None and not self.category_repo.get_by_id(category_id):
            raise ValueError(f'Category with ID {category_id} does not exist')
        update = self.product_repo.update(
            product_id=product_id,
            name = name,
            selling_price=selling_price,
            unit_cost=unit_cost,
            category_id=category_id,
        )
        return update
    
    def delete_product (self, product_id:int) -> bool:
        '''Delete a product. The repository will delete inventory first 
           : return: True when delete, False if product not found.'''
        return self.product_repo.delete(product_id)
