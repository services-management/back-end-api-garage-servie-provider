from src.repositories.admin_repositery import AdminRepository
from src.schemas.admin_shema import AdminLogin, AdminCreate
from src.utils.hash_password import hash_password
from src.utils.verify_password import verify_password
from src.models.admin_model import adminModel
from fastapi import HTTPException, status # <-- IMPORT ADDED HERE
from src.models.technical_model import TechnicalModel
from src.schemas.technical_shema import TechnicalCreate
from src.repositories.technical_repository import TechnicalRepository

class Admincontroller:
    '''handles the business logic for admin authentication and management'''

    def __init__(self, admin_repo: AdminRepository,tech_repo: TechnicalRepository):
        '''The repository is injected here (dependency Injection)'''
        self.admin_repo = admin_repo
        self.tech_repo = tech_repo
    def authentication_admin(self, admin_in: AdminLogin) -> adminModel | None:
        '''Handle the admin login process: retieves user and verifies password.'''
        
        # 1. Data Access: Retrieve user record using the repository
        admin = self.admin_repo.get_by_username(admin_in.username)

        if not admin:
            # User not found (Will result in "Invalid credentials" from the API route)
            return None
        
        # 2. Business Logic: Verify the hash password
        if not verify_password(admin_in.password, admin.password):
            # Password mismatch (Will result in "Invalid credentials" from the API route)
            return None
        
        return admin
    
    def create_admin(self, admin_in: AdminCreate) -> adminModel:
        '''handle creation of a new admin account'''

        # 1. BUSINESS VALIDATION: Check if username already exists
        if self.admin_repo.get_by_username(admin_in.username):
            # 💡 FIX: Raise HTTPException for proper 409 Conflict API response
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken."
            )
        # Check if email/phone already exists (Requires new repo method)
        if self.admin_repo.get_by_email_phone(admin_in.email_phone):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email/Phone is already linked to an Admin account."
            )
        
        # 2. Hashing the password
        hashed_password = hash_password(admin_in.password)

        # 3. Call Repository's 'create' method
        new_admin = self.admin_repo.create(admin_in, hashed_password)

        # The repository handles commit/refresh
        return new_admin
    
    def create_technical_account(self, tech_in: TechnicalCreate) -> TechnicalModel:
        '''Handles creation of a new technical account by an administrator, checking for cross-table conflicts.'''

        # 1. BUSINESS VALIDATION: Check for username conflict across BOTH Admin and Technical tables
        if self.admin_repo.get_by_username(tech_in.username) or self.tech_repo.get_by_username(tech_in.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken by an Admin or Technical user."
            )
        
        # 2. BUSINESS VALIDATION: Check for phone number conflict across the Technical table
        #    (The phone number constraint is specific to the Technical model in your design)
        if self.tech_repo.get_by_phone_number(tech_in.phone_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already linked to another Technical account."
            )
        
        if self.admin_repo.get_by_email_phone(tech_in.phone_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already linked to another Technical account."
            )
        
        # 3. Hashing the password
        hashed_password = hash_password(tech_in.password)

        # 4. Call Repository's 'create' method
        #    The TechnicalRepository handles setting the role="technical" default.
        new_tech_account = self.tech_repo.create(tech_in, hashed_password)

        # The repository handles commit/refresh
        return new_tech_account