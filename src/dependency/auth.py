# src/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

# --- Project Imports ---
from src.config.database import get_db # Your database session dependency
from src.repositories.admin_repository import AdminRepository # The repo to fetch the admin
from src.models.admin_model import AdminOut # The secure output Pydantic model
from src.service.auth import decode_token # The utility we just created
from src.repositories.technical_repository import TechnicalRepository 
from src.models.technical_model import TechnicalOut
# Define the OAuth2 scheme. FastAPI uses the URL provided here for documentation.
security = HTTPBearer()

def get_current_technical_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TechnicalOut:
    token = credentials.credentials
    """
    Decodes the JWT token, verifies the 'technical' role, and fetches the 
    corresponding Technical user record from the database.
    If anything fails, it raises a 401 Unauthorized exception.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials for Technical staff",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decode and validate the token signature
    try:
        payload = decode_token(token)
    except HTTPException:
        raise
    
    # 2. Extract ID (sub) and verify role is 'technical'
    tech_id_str = payload.get("sub")
    token_role = payload.get("role")
    
    # CRITICAL CHECK: Ensure the token belongs to a technical user
    if not tech_id_str or token_role != "technical":
        raise credentials_exception
        
    # 3. Convert ID to UUID (since your DB uses UUID)
    try:
        technical_id = UUID(tech_id_str)
    except ValueError:
        raise credentials_exception
        
    # 4. Fetch user from repository
    tech_repo = TechnicalRepository(db)
    # NOTE: Your TechnicalRepository.get() must accept a UUID as input!
    technical_model = tech_repo.get(technical_id) 

    if technical_model is None:
        raise credentials_exception
        
    # 5. Return the Pydantic output model
    return TechnicalOut.model_validate(technical_model)

def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminOut:
    token = credentials.credentials
    """
    Decodes the JWT token, validates the Admin ID, and fetches the Admin object.
    If anything fails, it raises a 401 Unauthorized exception.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decode and validate the token signature
    try:
        payload = decode_token(token)
    except HTTPException:
        # decode_token already handles the 401, so we re-raise it
        raise

    # 2. Extract Admin ID (stored as 'sub') and check role
    admin_id_str = payload.get("sub")
    token_role = payload.get("role")
    
    if not admin_id_str or token_role != "admin":
        raise credentials_exception
        
    # 3. Convert ID to UUID (since your DB uses UUID)
    try:
        admin_id = UUID(admin_id_str)
    except ValueError:
        raise credentials_exception
        
    # 4. Fetch user from repository
    admin_repo = AdminRepository(db)
    # NOTE: Your AdminRepository.get() must accept a UUID as input!
    admin_model = admin_repo.get_by_id(admin_id) 

    if admin_model is None:
        raise credentials_exception
        
    # 5. Return the Pydantic output model
    return AdminOut.model_validate(admin_model)

def get_current_user_admin_or_technical(
        credentials : HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)

    role = str(payload.get("role") or "").lower()
    sub = payload.get("sub")

    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token payload")
    
    try:
        user_id = UUID(sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid subject format")
    
    if role == "admin":
        admin = AdminRepository(db).get_by_id(user_id)

        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin user not found")
        
        return AdminOut.model_validate(admin)
    
    
    if role == "technical":
        technical = TechnicalRepository(db).get_by_id(user_id)
        if not technical:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Technical user not found")
        return TechnicalOut.model_validate(technical)
    
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
