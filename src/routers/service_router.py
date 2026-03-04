from typing import List
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controller.service_controller import ServiceController
from src.dependency.auth import (get_current_admin_user,
                                 get_optional_user)
from src.models.service_model import (ServiceCreate, ServiceResponse,
                                      ServiceUpdate, ServiceEstimateResponse)
from src.service.s3_service import S3Service
from src.core.enums import TransmissionType, FuelType, DriveType, VehicleType, ServiceType
from typing import Optional

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
            garage_price=payload.garage_price,
            home_price=payload.home_price,
            duration_minutes=payload.duration_minutes,
            service_type=payload.service_type,
            is_available=payload.is_available,
            associations=[a.dict() for a in payload.associations] if payload.associations else []
        )
        return service
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/filter-by-vehicle", response_model=List[ServiceResponse])
def filter_services_by_vehicle(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    year: int = Query(..., ge=1900, le=2100),
    vehicle_type: Optional[VehicleType] = Query(None),
    fuel_type: Optional[FuelType] = Query(None),
    drive_type: Optional[DriveType] = Query(None),
    transmission: Optional[TransmissionType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Search for services compatible with a specific vehicle."""
    svc = ServiceController(db)
    return svc.filter_services_by_vehicle(
        make_name=make,
        model_name=model,
        year=year,
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        drive_type=drive_type,
        transmission=transmission,
        skip=skip,
        limit=limit
    )


@router.get("/estimate-prices", response_model=List[ServiceEstimateResponse])
def get_service_price_estimates(
    vehicle_id: int = Query(..., description="The ID of the car configuration"),
    service_type: ServiceType = Query(..., description="Home or Garage service"),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """
    Get dynamic price estimates for services based on a specific car.
    Matches products and calculates total cost (Labor + Parts).
    """
    svc = ServiceController(db)
    return svc.get_service_estimates(vehicle_id, service_type)


@router.get("/catalog", response_model=List[ServiceEstimateResponse])
def get_service_catalog(
    model_id: int = Query(...),
    year: int = Query(...),
    engine: str = Query(...),
    service_type: ServiceType = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """
    User-friendly catalog endpoint. 
    Input car details and get back a list of services with calculated prices.
    """
    svc = ServiceController(db)
    try:
        return svc.get_catalog_for_vehicle(
            model_id=model_id,
            year=year,
            engine=engine,
            service_type=service_type
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
            garage_price=payload.garage_price,
            home_price=payload.home_price,
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
