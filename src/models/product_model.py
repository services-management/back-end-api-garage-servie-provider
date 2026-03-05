
# src/schemas/product.py
from decimal import Decimal
from typing import Optional,List
from pydantic import BaseModel, Field, validator,field_validator,ConfigDict

from src.models.category_model import CategoryResponse  # fixed import
from src.models.inventory_model import InventorySnapshot  # fixed import
from src.schemas.product import ProductStatus
from src.models.vehicle_model import VehicleBase
# --- Product Base Schemas ---
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, example="Brake Pad", description="Unique name of the product/part.")
    selling_price: Decimal = Field(..., gt=Decimal("0"), example=Decimal("19.99"), description="Price charged to the customer.")
    price_adjustment: Decimal = Field(Decimal("0.00"), description="Optional price adjustment for specific vehicle fitments.")
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0"), example=Decimal("12.50"), description="Internal cost of the product.")
    description :Optional[str] = Field(None,max_length=255)
    image_url :Optional[str] = Field(None,description="image of the product")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, example="Active")
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )

    @validator("name")
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Product name cannot be blank.")
        return v

    @field_validator("unit_cost", "selling_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v

# Input Schema for creating a Product (POST)
class ProductCreate(ProductBase):
    category_name: Optional[str] = Field(None, example="Oil", description="Name of the category this product belongs to.")
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
        sp = values.get("selling_price")
        if v is not None and sp is not None and v > sp:
            raise ValueError("Unit cost cannot exceed selling price.")
        return v


# Input Schema for updating a Product (PUT/PATCH)
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, example="Brake Pad - Premium")
    selling_price: Optional[Decimal] = Field(None, gt=Decimal("0"), example=Decimal("21.99"))
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0"), example=Decimal("13.00"))
    description :Optional[str] = Field(None,min_length=1,max_length=255)
    category_name: Optional[str] = Field(None, example="oil")
    image_url: Optional[str] = Field(None)
    status: Optional[ProductStatus] = None

    model_config = ConfigDict(
        use_enum_values=True
    )

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
        if v is not None and sp is not None and v > sp:
            raise ValueError("Unit cost cannot exceed selling price.")
        return v

# Output Schema for API responses
class ProductResponse(ProductBase):
    product_id: int = Field(..., example=123)
    category_id: Optional[int] = Field(None,example=1)
    category: Optional[CategoryResponse] = None
    inventory: Optional[InventorySnapshot] = None

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )

class ProductVehicleLink(BaseModel):
    product_id: int
    vehicle_id: int
    note: Optional[str] = None
    # This now matches the DB column:
    quantity_required: Optional[str] = Field(None, example="4.5L")
    note: Optional[str] = Field(None, description="Fitment advice (e.g. 'Use with new washer')")
    vehicle: Optional[VehicleBase] = None
    class Config:
        from_attributes = True

class ProductOut(BaseModel):
    product_id: int = Field(..., example=123)
    name: Optional[str] = Field(None, min_length=1, example="Brake Pad - Premium")
    selling_price: Optional[Decimal] = Field(None, gt=Decimal("0"), example=Decimal("21.99"))
    description :Optional[str] = Field(None,min_length=1,max_length=255)
    image_url: Optional[str] = Field(None)
    status: Optional[ProductStatus] = None
    category: Optional[CategoryResponse] = None # Include Category details
    inventory: Optional[InventorySnapshot] = None # Include Inventory details
    vehicle_links: List[ProductVehicleLink] = [] # List of linked vehicles
    @validator("name")
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Product name cannot be blank.")
        return v

    @validator("selling_price", pre=True)
    def to_decimal_update(cls, v):
        if v is None:
            return v
        return Decimal(str(v))

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
