# src/schemas/product.py

from pydantic import BaseModel, Field
from typing import Optional
from src.models.category_model import CategoryResponse # Import nested schema

# --- Nested Inventory Schema ---
class InventorySnapshot(BaseModel):
    """Represents the current stock level data attached to a Product response."""
    current_stock: float = Field(0.0, ge=0)
    min_stock_level: Optional[float] = Field(None, ge=0)
    
    class Config:
        from_attributes = True

# --- Product Base Schemas ---
class ProductBase(BaseModel):
    name: str = Field(..., description="Unique name of the product/part.")
    selling_price: float = Field(..., gt=0, description="Price charged to the customer.")
    unit_cost: Optional[float] = Field(None, ge=0, description="Internal cost of the product.")
    category_id: Optional[int] = Field(None, description="ID of the category this product belongs to.")

# Input Schema for creating a Product (POST)
class ProductCreate(ProductBase):
    # These fields are used by the service to create the initial inventory record
    initial_stock: float = Field(0.0, ge=0, description="Starting quantity for the inventory.")
    min_stock_level: Optional[float] = Field(None, ge=0, description="Reorder point for inventory.")

# Input Schema for updating a Product (PUT/PATCH)
class ProductUpdate(BaseModel):
    # All fields are optional because updates can be partial
    name: Optional[str] = None
    selling_price: Optional[float] = None
    unit_cost: Optional[float] = None
    category_id: Optional[int] = None
    
# Output Schema for API responses
class ProductResponse(ProductBase):
    product_id: int

    # Nested relationships: The ORM will automatically populate these
    category: Optional[CategoryResponse] = None
    inventory: Optional[InventorySnapshot] = None
    
    class Config:
        from_attributes = True