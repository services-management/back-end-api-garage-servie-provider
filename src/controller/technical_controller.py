from src.repositories.technical_repository import TechnicalRepository
from src.schemas.technical_shema import TechincalLogin
from src.utils.verify_password import verify_password
from src.models.technical_model import TechnicalModel
from typing import Optional

class TechnicalController:
    """handle the business logic for user authentication and management"""

    def __init__(self, tech_repo:TechnicalRepository):
        '''The Technical Repository is injected here'''
        self.tech_repo = tech_repo

    def authenticate_technical(self,tech_in:TechincalLogin) -> Optional[TechnicalModel]:
        '''handle the technical user login process: retrieves user and verifies password'''

        # 1. Data Access: Retrieve user record using the repository
        technical_user = self.tech_repo.get_by_username(tech_in.username)

        if not technical_user:
            # User not found
            return None
        
        # 2. Business Logic: Verify the hashed password
        # Note: 'technical_user.password' is the hashed password from the DB
        if not verify_password(tech_in.password, technical_user.password):
            # Password mismatch
            return None
        
        # 3. Success: Return the full TechnicalModel object (which includes the 'role' field)
        return technical_user
        
