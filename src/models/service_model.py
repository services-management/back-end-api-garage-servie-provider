from pydantic import BaseModel, Field,model_validator
from typing import Optional, List,Any
from decimal import Decimal
from src.models.file_model import FileUploadResponse


class ServiceProductAssociationEmbedded(BaseModel):
    product_name: str = Field(..., example="oil")
    quantity_required: int = Field(..., gt=0, example=2)
    is_optional: bool = Field(False, example=False)

    class Config:
        from_attributes = True
class ServiceProductAssociationResponse(ServiceProductAssociationEmbedded):
    product_id: Optional[int] = Field(None, example=1)
    file_url: Optional[str] = Field(None, example="http://minio:9000/garas-fixing/images/product.jpg")
    @model_validator(mode='before')
    @classmethod
    def get_name_from_relationship(cls, data: Any) -> Any:
        """
        Extraction logic: If the SQLAlchemy object has a 'product' relationship,
        extract the name and image_url from it.
        """
        if hasattr(data, "product") and data.product:
            data.product_name = data.product.name
            # If the product has images loaded (e.g. via controller), use the first one
            if hasattr(data.product, "images") and data.product.images:
                data.file_url = data.product.images[0].file_url
        return data

class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Oil Change")
    description: Optional[str] = Field(
        None,
        example="Standard oil change service.",
        description="Detailed description of the service."
    )
    price: Decimal = Field(..., gt=Decimal("0"), description="Price of the service")
    duration_minutes: int = Field(..., gt=0, description="Typical duration of the service in minutes.")
    is_available: bool = Field(True, example=True, description="Indicates if the service is currently available.")

    class Config:
        from_attributes = True


class ServiceCreate(ServiceBase):
    associations: Optional[List[ServiceProductAssociationEmbedded]] = Field(default_factory=list)


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=Decimal("0"))
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None
    associations: Optional[List[ServiceProductAssociationEmbedded]] = None

    class Config:
        from_attributes = True


class ServiceResponse(ServiceBase):
    service_id: int = Field(..., example=123)
    associations: List[ServiceProductAssociationResponse] = Field(default_factory=list)
    images: Optional[List[FileUploadResponse]] = None
