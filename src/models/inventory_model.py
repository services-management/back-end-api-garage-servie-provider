from pydantic import BaseModel,Field
from typing import Optional
from datetime import date

# --- Nested Inventory Schema ---
class InventorySnapshot(BaseModel):
    """Represents the current stock level data attached to a Product response."""
    current_stock: float = Field(0.0, ge=0)
    min_stock_level: Optional[float] = Field(None, ge=0)
    
    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    current_stock: float = Field(..., ge=0, description="Current stock level")
    min_stock_level: Optional[float] = Field(None, ge=0, description="Reorder point")
    last_restock_data: Optional[date] = None


class InventoryCreate(InventoryBase):
    current_stock: float = Field(0, ge=0)



class InventoryUpdate(BaseModel):
    current_stock: Optional[float] = Field(None, ge=0)
    min_stock_level: Optional[float] = Field(None, ge=0)
    last_restock_data: Optional[date] = None


class InventoryOut(InventoryBase):
    product_id: int

    class Config:
        from_attributes = True
