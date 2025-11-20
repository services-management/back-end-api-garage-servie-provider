from pydantic import BaseModel, Field
from uuid import uuid4, UUID

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str
    password: str
    is_admin: bool = True
