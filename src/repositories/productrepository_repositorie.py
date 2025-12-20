from sqlalchemy.orm import Session
from src.schemas.product import Product
from src.repositories.baserepository_repositorie import BaseRepository
from src.repositories.inventoryrepository_repositorie import InventoryRepository
from src.repositories.categoryrepository_repositorie import CategoryRepository
from typing import Optional
from typing import List
class ProductRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Product)
        self.inventory_repo = InventoryRepository(db)
        self.category_repo = CategoryRepository(db)

    # --- Get by product ID ---
    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.product_id == product_id).first()

    # --- Get by name ---
    def get_by_name(self, name: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.name == name).first()

    # --- List products with optional pagination ---
    def list(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.db.query(Product).offset(skip).limit(limit).all()

    # --- List products by category ---
    def list_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        return (
            self.db.query(Product)
            .filter(Product.category_id == category_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    # --- Create product + auto-create inventory ---
    def create(self, name: str, selling_price: float, 
               unit_cost: Optional[float] = None, 
               category_id: Optional[int] = None,
               initial_stock: float = 0) -> Product:
        if category_id is not None:
            if not self.category_repo.get_by_id(category_id):
                raise ValueError(f"Category with ID {category_id} does not exist.")
            
        product = Product(
            name = name,
            selling_price = selling_price,
            unit_cost = unit_cost,
            category_id = category_id
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        self.inventory_repo.create(product_id=product.product_id, current_stock = initial_stock)

        return product
    # --- Update product ---
    def update(self, product_id: int,
               name: Optional[str] = None,
               selling_price: Optional[float] = None,
               unit_cost: Optional[float] = None,
               category_id: Optional[int] = None) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        # 1. Category Validation (if category_id is being updated)
        if category_id is not None:
            if not self.category_repo.get_by_id(category_id):
                # Handle this validation error (e.g., raise an exception)
                raise ValueError(f"Category with ID {category_id} does not exist.") 
        
        # 2. Product Update
        if name is not None:
            product.name = name
        if selling_price is not None:
            product.selling_price = selling_price
        if unit_cost is not None:
            product.unit_cost = unit_cost
        if category_id is not None:
            product.category_id = category_id
            
        self.db.commit()
        self.db.refresh(product)
        return product

    # --- Delete product + inventory ---
    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False
        # Delete inventory first
        self.inventory_repo.delete(product_id)
        # Delete product
        self.db.delete(product)
        self.db.commit()
        return True
