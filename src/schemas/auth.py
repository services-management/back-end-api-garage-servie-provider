from pydantic import BaseModel


class Token(BaseModel):
    """Schema for the JWT access token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int