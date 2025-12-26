from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.controller.service_controller import ServiceController
from src.models.service_model import ServiceCreate, ServiceUpdate, ServiceResponse
from src.dependency.auth import get_current_admin_user, get_current_user_admin_or_technical

router = APIRouter(
    prefix="/service",
    tags=["Service Management"]
)


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=201,
    dependencies=[Depends(get_current_admin_user)],
)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    """Create a new service (Admin only)"""
    svc = ServiceController(db)
    try:
        service = svc.create_service(
            name=payload.name,
            description=payload.description,
            image_url=payload.image_url,
            price=payload.price,
            duration_minutes=payload.duration_minutes,
            is_available=payload.is_available,
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(get_current_user_admin_or_technical)],
)
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get a service by ID"""
    svc = ServiceController(db)
    service = svc.get_service_with_associations(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.get(
    "/",
    response_model=List[ServiceResponse],
    dependencies=[Depends(get_current_user_admin_or_technical)],
)
def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all services with pagination"""
    svc = ServiceController(db)
    return svc.list_services_with_associations(skip=skip, limit=limit)


@router.get(
    "/available/",
    response_model=List[ServiceResponse],
    dependencies=[Depends(get_current_user_admin_or_technical)],
)
def list_available_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List only available services"""
    svc = ServiceController(db)
    return svc.list_available_services(skip=skip, limit=limit)


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(get_current_admin_user)],
)
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update a service (Admin only)"""
    svc = ServiceController(db)
    try:
        service = svc.update_service(
            service_id=service_id,
            name=payload.name,
            description=payload.description,
            image_url=payload.image_url,
            price=payload.price,
            duration_minutes=payload.duration_minutes,
            is_available=payload.is_available,
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{service_id}",
    status_code=204,
    dependencies=[Depends(get_current_admin_user)],
)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Delete a service (Admin only)"""
    svc = ServiceController(db)
    try:
        svc.delete_service(service_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
