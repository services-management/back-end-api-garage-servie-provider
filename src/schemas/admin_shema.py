from pydantic import BaseModel,Field
from typing import Optional
import uuid
# Schema for creating a new admin
class AdminCreate(BaseModel):
    '''
    Define the required field and validation for create admin.
    '''
    # Match the username field in the Adminmodel
    username: str = Field(min_length=4, max_length=50)
    # Password must be validation before hashing and storge 
    password: str = Field(min_length=8)
    # Match the email_phone field in the AdminModel
    email_phone: str = Field(description="Email or phone number required for contact/recovery.")

    # configuration for validation and serialization
    class Config:
        from_attributes = True

# Shema for returning Admin data
class AdminOut(BaseModel):

   '''Defines the structure for safe Admin output (excluding the password hash).'''
   admin_id : uuid.UUID
   username : str
   email_phone : Optional[str]
   role: str
   class Config:
        from_attributes = True


# Schema for loggin in 
class AdminLogin(BaseModel):
    '''define the input structure for an admin to login request'''
    username:str
    password:str

# Schema for returning a secure token upon successful login 
class Token(BaseModel):
    '''Defines the structure of the authentication token returned to the client.'''
    access_token : str
    token_type : str = 'bearer'
