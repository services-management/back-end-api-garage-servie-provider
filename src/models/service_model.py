from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class ServiceProductAssociationEmbedded(BaseModel):
    product_id: int = Field(..., example=1)
    quantity_required: int = Field(..., gt=0, example=2)
    is_optional: bool = Field(False, example=False)

    class Config:
        from_attributes = True


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Oil Change")
    description: Optional[str] = Field(
        None,
        example="Standard oil change service.",
        description="Detailed description of the service."
    )
    image_url: str = Field(..., max_length=250, description="URL to the service image.")
    price: Decimal = Field(..., gt=Decimal("0"), description="Price of the service")
    duration_minutes: int = Field(..., gt=0, description="Typical duration of the service in minutes.")
    is_available: bool = Field(True, example=True, description="Indicates if the service is currently available.")

    class Config:
        from_attributes = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=250)
    price: Optional[Decimal] = Field(None, gt=Decimal("0"))
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None

    class Config:
        from_attributes = True


class ServiceResponse(ServiceBase):
    service_id: int = Field(..., example=123)
    associations: List[ServiceProductAssociationEmbedded] = Field(default_factory=list)
