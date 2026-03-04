from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator


from src.core.enums import ServiceType


class ServiceProductAssociationEmbedded(BaseModel):
    product_name: str = Field(..., example="oil")
    quantity_required: int = Field(..., gt=0, example=2)
    is_optional: bool = Field(False, example=False)

    class Config:
        from_attributes = True
class ServiceProductAssociationResponse(ServiceProductAssociationEmbedded):
    product_id: Optional[int] = Field(None, example=1)
    @model_validator(mode='before')
    @classmethod
    def get_name_from_relationship(cls, data: Any) -> Any:
        """
        Extraction logic: If the SQLAlchemy object has a 'product' relationship,
        extract the name from it.
        """
        if hasattr(data, "product") and data.product:
            data.product_name = data.product.name
        return data

class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Oil Change")
    description: Optional[str] = Field(
        None,
        example="Standard oil change service.",
        description="Detailed description of the service."
    )
    image_url: str = Field(..., max_length=250, description="URL to the service image.")
    garage_price: Decimal = Field(..., gt=Decimal("0"), description="Labor price at the garage")
    home_price: Decimal = Field(..., gt=Decimal("0"), description="Labor price for home service")
    duration_minutes: int = Field(..., gt=0, description="Typical duration of the service in minutes.")
    is_available: bool = Field(True, example=True, description="Indicates if the service is currently available.")
    service_type: ServiceType = Field(default=ServiceType.GARAGE)

    class Config:
        from_attributes = True


class ServiceCreate(ServiceBase):
    associations: Optional[List[ServiceProductAssociationEmbedded]] = Field(default_factory=list)


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=250)
    garage_price: Optional[Decimal] = Field(None, gt=Decimal("0"))
    home_price: Optional[Decimal] = Field(None, gt=Decimal("0"))
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None
    associations: Optional[List[ServiceProductAssociationEmbedded]] = None

    class Config:
        from_attributes = True


class ServiceResponse(ServiceBase):
    service_id: int = Field(..., example=123)
    associations: List[ServiceProductAssociationResponse] = Field(default_factory=list)


class ServiceProductEstimate(BaseModel):
    product_id: int
    product_name: str
    price_per_unit: Decimal
    quantity_required: Decimal
    total_product_price: Decimal


class ServiceEstimateResponse(BaseModel):
    service_id: int
    service_name: str
    service_type: ServiceType
    base_labor_price: Decimal
    products: List[ServiceProductEstimate]
    total_estimated_price: Decimal
    total_duration_minutes: int

    class Config:
        from_attributes = True


class ComboServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Oil Change + Filter Replacement")
    description: Optional[str] = Field(
        None,
        example="Complete oil and filter service package.",
        description="Detailed description of the combo service."
    )
    image_url: Optional[str] = Field(None, max_length=250, description="URL to the combo service image.")
    is_available: bool = Field(True, example=True, description="Indicates if the combo is available.")

    class Config:
        from_attributes = True


class ComboServiceCreate(ComboServiceBase):
    service_names: List[str] = Field(
        ...,
        min_items=2,
        example=["Oil Change", "Filter Replacement"],
        description="List of service names to combine"
    )


class ComboServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=250)
    is_available: Optional[bool] = None
    service_names: Optional[List[str]] = Field(None, min_items=2)

    class Config:
        from_attributes = True


class ComboServiceResponse(ComboServiceBase):
    combo_service_id: int = Field(..., example=1)
    total_price: Decimal = Field(..., example=Decimal("100.00"), description="Total price of all combined services")
    total_duration_minutes: int = Field(..., example=120, description="Total duration of all services combined")
    services: List[ServiceResponse] = Field(default_factory=list)


class UnifiedCatalogResponse(BaseModel):
    individual_services: List[ServiceEstimateResponse]
    combo_services: List[ComboServiceResponse]
