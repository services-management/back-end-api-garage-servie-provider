from pydantic import BaseModel, Field
from src.core.enums import ServiceType

class SlideshowBase(BaseModel):
    image_url: str = Field(..., example="http://example.com/slide1.jpg")
    service_type: ServiceType = Field(..., example=ServiceType.HOME)

class SlideshowCreate(SlideshowBase):
    pass

class SlideshowResponse(SlideshowBase):
    id: int

    class Config:
        from_attributes = True
