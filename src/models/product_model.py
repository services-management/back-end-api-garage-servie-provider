
# src/schemas/product.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

from src.models.category_model import CategoryResponse  # fixed import
from src.models.inventory_model import InventorySnapshot  # fixed import


# --- Product Base Schemas ---
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, example="Brake Pad", description="Unique name of the product/part.")
    selling_price: Decimal = Field(..., gt=Decimal("0"), example=Decimal("19.99"), description="Price charged to the customer.")
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0"), example=Decimal("12.50"), description="Internal cost of the product.")
    category_id: Optional[int] = Field(None, example=1, description="ID of the category this product belongs to.")

    @validator("name")
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Product name cannot be blank.")
        return v

    @validator("unit_cost", "selling_price", pre=True)
    def to_decimal(cls, v):
        # Allow float/str inputs but convert to Decimal safely
        if v is None:
            return v
        return Decimal(str(v))

    class Config:
        from_attributes = True


# Input Schema for creating a Product (POST)
class ProductCreate(ProductBase):
    # If category_id must be present, make it non-optional here:
    # category_id: int = Field(..., example=1, description="Required category ID")

    initial_stock: Decimal = Field(Decimal("0.0"), ge=Decimal("0"), example=Decimal("50.0"),
                                   description="Starting quantity for the inventory.")
    min_stock_level: Optional[Decimal] = Field(None, ge=Decimal("0"), example=Decimal("10.0"),
                                               description="Reorder point for inventory.")

    @validator("initial_stock", "min_stock_level", pre=True)
    def to_decimal_create(cls, v):
        if v is None:
            return v
        return Decimal(str(v))

    @validator("unit_cost", always=True)
    def cost_not_exceed_price(cls, v, values):
        # Optional business rule: unit_cost should not exceed selling_price
        sp = values.get("selling_price")
        if v is not None and sp is not None and v > sp:
            raise ValueError("Unit cost cannot exceed selling price.")
        return v


# Input Schema for updating a Product (PUT/PATCH)
class ProductUpdate(BaseModel):
    # All fields optional for partial updates
    name: Optional[str] = Field(None, min_length=1, example="Brake Pad - Premium")
    selling_price: Optional[Decimal] = Field(None, gt=Decimal("0"), example=Decimal("21.99"))
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0"), example=Decimal("13.00"))
    category_id: Optional[int] = Field(None, example=2)

    @validator("name")
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Product name cannot be blank.")
        return v

    @validator("selling_price", "unit_cost", pre=True)
    def to_decimal_update(cls, v):
        if v is None:
            return v
        return Decimal(str(v))

    @validator("unit_cost")
    def cost_not_exceed_price_on_update(cls, v, values):
        sp = values.get("selling_price")
        # Only validate if both are provided in the same update payload
        if v is not None and sp is not None and v > sp:
            raise ValueError("Unit cost cannot exceed selling price.")
        return v


# Output Schema for API responses
class ProductResponse(ProductBase):
    product_id: int = Field(..., example=123)

    # Nested relationships: The ORM can populate these
    category: Optional[CategoryResponse] = None
    inventory: Optional[InventorySnapshot] = None

    class Config:
        from_attributes = True
