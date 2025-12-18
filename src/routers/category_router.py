
# src/api/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.controller.category_controller import CategoryControll
from src.models.category_model import CategoryCreate, CategoryResponse
from src.dependency.auth import get_current_admin_user, get_current_user_admin_or_technical

router = APIRouter(
    prefix="/category", tags=["Category Management"]
)

@router.post(
    "",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_admin_user)]
)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    svc = CategoryControll(db)
    try:
        return svc.create_category(name=payload.name, description=payload.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_user_admin_or_technical)]
)
def get_category(category_id: int, db: Session = Depends(get_db)):
    svc = CategoryControll(db)
    category = svc.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category

@router.get(
    "",
    response_model=List[CategoryResponse],
    dependencies=[Depends(get_current_user_admin_or_technical)]
)
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    svc = CategoryControll(db)
    try:
        return svc.list_category(skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_admin_user)]
)
def update_category(category_id: int, payload: CategoryResponse, db: Session = Depends(get_db)):
    svc = CategoryControll(db)
    try:
        return svc.update_category(category_id, name=payload.name, description=payload.description)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{category_id}",
    response_model=bool,
    dependencies=[Depends(get_current_admin_user)]
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    svc = CategoryControll(db)
    deleted = svc.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found.")
    return True
