from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FileUploadBase(BaseModel):
    filename: str = Field(..., example="image.jpg")
    image_url: str = Field(..., example="http://minio:9000/garas-fixing/images/...", alias="file_url")
    content_type: Optional[str] = Field(None, example="image/jpeg")


class FileUploadCreate(FileUploadBase):
    file_type: str = Field(..., example="product")  # "product" or "service"
    associated_id: int = Field(..., example=1)
    file_size: Optional[int] = None


class FileUploadResponse(FileUploadBase):
    file_id: int
    file_type: str
    associated_id: int
    file_size: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
