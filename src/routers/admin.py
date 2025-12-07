from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.schemas.admin_shema import AdminLogin,AdminCreate,AdminOut,Token
from src.controller.admin_controller import Admincontroller
from src.repositories.admin_repositery import AdminRepository
from src.schemas.technical_shema import TechnicalCreate, TechnicalOut
from src.repositories.technical_repository import TechnicalRepository

router = APIRouter(prefix='/admin', tags=['Admin Auth'])

# Dependency that creates and returns the AdminController instance for the request

def get_admin_controller(db:Session = Depends(get_db)):
    # 1. Instantiate Repositories
    admin_repo = AdminRepository(db)
    tech_repo = TechnicalRepository(db) 

    # 2. Instantiate the Controller, injecting ALL required Repositories
    controller_instance = Admincontroller(
        admin_repo=admin_repo,
        tech_repo=tech_repo # ✅ Inject Technical Repository
    ) 
    
    return controller_instance

@router.post('/login', response_model=Token, summary="Authenticate Admin user")
def admin_login(
    admin_in : AdminLogin,
    controller : Admincontroller = Depends(get_admin_controller)
):
    admin = controller.authentication_admin(admin_in)

    if not admin:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = f'JWT_TOKEN_FOR_ADMIN_{admin.admin_id}'

    return{'access_token':access_token, 'token_type':'bearer'}

@router.post('/create',response_model=AdminOut,status_code=status.HTTP_201_CREATED , summary='Create a new Admin account')
def create_admin_account(
    admin_in:AdminCreate,
    controller : Admincontroller = Depends(get_admin_controller)
):
    try:
        new_admin = controller.create_admin(admin_in)

        return AdminOut.model_validate(new_admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=str(e))
    

@router.post('/create_tech', 
             response_model=TechnicalOut, 
             status_code=status.HTTP_201_CREATED, 
             summary='Admin creates a new Technical Account')
def admin_create_technical_account(
    tech_in: TechnicalCreate,
    controller: Admincontroller = Depends(get_admin_controller)
):
    # The AdminController handles all logic, validation, and creation.
    new_tech_account = controller.create_technical_account(tech_in)

    return TechnicalOut.model_validate(new_tech_account)

