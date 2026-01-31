from typing import List
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controller.service_controller import ServiceController
from src.dependency.auth import (get_current_admin_user,
                                 get_optional_user)
from src.models.service_model import (ServiceCreate, ServiceResponse,
                                      ServiceUpdate)
from src.service.s3_service import S3Service

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
            associations=[a.dict() for a in payload.associations] if payload.associations else []
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(get_optional_user)],
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
    dependencies=[Depends(get_optional_user)],
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
            associations=[a.dict() for a in payload.associations] if payload.associations is not None else None
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{service_id}/image",
    status_code=200,
    dependencies=[Depends(get_current_admin_user)],
)
def upload_service_image(
    service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image for a service and update the image_url."""
    svc = ServiceController(db)
    service = svc.get_service_with_associations(service_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        # Read file content
        content = file.file.read()
        
        # Generate unique S3 key
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"services/{service_id}/{uuid.uuid4()}.{file_ext}"
        
        # Upload to S3
        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content, 
            s3_key, 
            content_type=file.content_type or "image/jpeg"
        )
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        # Update service with new image URL
        updated = svc.update_service(
            service_id=service_id,
            image_url=image_url
        )
        
        return {"service_id": service_id, "image_url": image_url, "service": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@router.put(
    "/{service_id}/image",
    status_code=200,
    dependencies=[Depends(get_current_admin_user)],
)
def update_service_image(
    service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Update/replace the image for a service."""
    svc = ServiceController(db)
    service = svc.get_service_with_associations(service_id)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        # Read file content
        content = file.file.read()
        
        # Generate unique S3 key
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"services/{service_id}/{uuid.uuid4()}.{file_ext}"
        
        # Upload to S3
        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content, 
            s3_key, 
            content_type=file.content_type or "image/jpeg"
        )
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        # Update service with new image URL
        updated = svc.update_service(
            service_id=service_id,
            image_url=image_url
        )
        
        return {"service_id": service_id, "image_url": image_url, "service": updated, "message": "Service image updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")


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
