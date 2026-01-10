from pydantic import BaseModel,Field,ConfigDict
from typing import Optional
from datetime import date
from decimal import Decimal
# --- Nested Inventory Schema ---

class InventoryBase(BaseModel):
    # Using Decimal to match SQLAlchemy Numeric(10,2)
    current_stock: Decimal = Field(default=Decimal("0.0"), ge=0)
    min_stock_level: Optional[Decimal] = Field(None, ge=0) 
    last_restock_date: Optional[date] = None # Ensure this matches your DB column exactly
    model_config = ConfigDict(from_attributes=True)


class InventoryCreate(InventoryBase):
    product_id:Optional[int] = None
    # name: Optional[str] = None
    current_stock: float = Field(0, ge=0)

class InventorySnapshot(InventoryBase):
    """Represents the current stock level data attached to a Product response."""
    pass


class InventoryUpdate(BaseModel):
    current_stock: Optional[float] = Field(None, ge=0)
    min_stock_level: Optional[float] = Field(None, ge=0)
    last_restock_date: Optional[date] = None

class InventoryOut(InventoryBase):
    # name: str

    class Config:
        from_attributes = True
