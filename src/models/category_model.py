# src/schemas/category.py

from pydantic import BaseModel, Field
from typing import Optional

# Base Schema: Shared fields for request/response
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the product category.")
    description: Optional[str] = Field(None, description="Optional detailed description.")

# Input Schema for creating a Category (POST)
class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass
# Output Schema for API responses (Includes database-generated ID)
class CategoryResponse(CategoryBase):
    categoryID: int

    # Config tells Pydantic to read data from the ORM object (required for SQLAlchemy)
    class Config:
        from_attributes = True