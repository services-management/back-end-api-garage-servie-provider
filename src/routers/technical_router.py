# src/routers/technical_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.technical_shema import TechincalLogin,Token # Input schema
from src.schemas.admin_shema import Token # Reusable output schema
from src.controller.technical_controller import TechnicalController
from src.repositories.technical_repository import TechnicalRepository

router = APIRouter(prefix='/technical', tags=['Technical Auth'])

# Dependency that creates and returns the TechnicalController instance
def get_technical_controller(db: Session = Depends(get_db)):
    # 1. Instantiate the Repository
    tech_repo = TechnicalRepository(db)
    
    # 2. Instantiate the Controller, injecting the Repository
    controller_instance = TechnicalController(tech_repo=tech_repo)
    
    # 3. Return the Controller instance
    return controller_instance

@router.post('/login', response_model=Token, summary="Authenticate Technical user")
def technical_login(
    tech_in: TechincalLogin,
    controller: TechnicalController = Depends(get_technical_controller)
):
    # 1. Authenticate user using the Controller
    technical_user = controller.authenticate_technical(tech_in)

    if not technical_user:
        # Raise HTTP 401 Unauthorized error for invalid credentials
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Generate the Secure JWT
    # The payload MUST include the role for authorization checks later!
    
    #  Placeholder for actual JWT creation:
    access_token = f'JWT_TOKEN_FOR_TECHNICAL_{technical_user.technical_id}'
    

    # 3. Return the standard Token response
    return {'access_token': access_token, 'token_type': 'bearer'}