
# src/api/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.controller.category_controller import CategoryController  # fixed name
from src.models.category_model import CategoryCreate, CategoryResponse, CategoryUpdate  # use schemas, not models
from src.dependency.auth import get_current_admin_user, get_current_user_admin_or_technical

router = APIRouter(
    prefix="/category",
    tags=["Category Management"],  # fixed spelling
)

# Dependency provider for the controller
def get_category_controller(db: Session = Depends(get_db)) -> CategoryController:
    return CategoryController(db)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin_user)],
)
def create_category(
    payload: CategoryCreate,
    ctrl: CategoryController = Depends(get_category_controller),
):
    try:
        category = ctrl.create_category(name=payload.name, description=payload.description)
        return category
    except ValueError as e:
        # Business rule validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_user_admin_or_technical)],
)
def get_category(
    category_id: int,
    ctrl: CategoryController = Depends(get_category_controller),
):
    try:
        return ctrl.get_category(category_id)
    except ValueError as e:
        # Controller raises ValueError("... not found.")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=List[CategoryResponse],
    dependencies=[Depends(get_current_user_admin_or_technical)],
)
def list_categories(
    skip: int = 0,
    limit: int = 100,
    ctrl: CategoryController = Depends(get_category_controller),
):
    try:
        return ctrl.list_category(skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_admin_user)],
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,  # use a dedicated update schema
    ctrl: CategoryController = Depends(get_category_controller),
):
    try:
        return ctrl.update_category(category_id, name=payload.name, description=payload.description)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        # Duplicate name or invalid name → 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{category_id}",
    response_model=bool,
    dependencies=[Depends(get_current_admin_user)],
)
def delete_category(
    category_id: int,
    ctrl: CategoryController = Depends(get_category_controller),
):
    try:
        deleted = ctrl.delete_category(category_id)
        if not deleted:
            # If repo returns False (not found), return 404
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        return True
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
