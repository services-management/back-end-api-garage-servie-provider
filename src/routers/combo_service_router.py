from typing import List
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controller.combo_service_controller import ComboServiceController
from src.dependency.auth import get_current_admin_user, get_optional_user
from src.models.service_model import ComboServiceCreate, ComboServiceResponse, ComboServiceUpdate
from src.service.s3_service import S3Service

router = APIRouter(
    prefix="/service/combo",
    tags=["Combo Service Management"]
)


@router.post(
    "/",
    response_model=ComboServiceResponse,
    status_code=201,
    dependencies=[Depends(get_current_admin_user)],
)
def create_combo_service(payload: ComboServiceCreate, db: Session = Depends(get_db)):
    """Create a new combo service by combining multiple services (Admin only)"""
    svc = ComboServiceController(db)
    try:
        combo = svc.create_combo_service(
            name=payload.name,
            service_ids=None,
            service_names=payload.service_names,
            description=payload.description,
            image_url=payload.image_url,
            is_available=payload.is_available,
        )
        
        # Calculate total price and duration
        total_price, total_duration = svc.calculate_combo_price_and_duration(combo.combo_service_id)
        
        return {
            "combo_service_id": combo.combo_service_id,
            "name": combo.name,
            "description": combo.description,
            "image_url": combo.image_url,
            "is_available": combo.is_available,
            "total_price": total_price,
            "total_duration_minutes": total_duration,
            "services": combo.services,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{combo_service_id}",
    response_model=ComboServiceResponse,
    dependencies=[Depends(get_optional_user)],
)
def get_combo_service(combo_service_id: int, db: Session = Depends(get_db)):
    """Get a combo service by ID"""
    svc = ComboServiceController(db)
    combo = svc.get_combo_service(combo_service_id)
    
    if not combo:
        raise HTTPException(status_code=404, detail="Combo service not found")
    
    total_price, total_duration = svc.calculate_combo_price_and_duration(combo_service_id)
    
    return {
        "combo_service_id": combo.combo_service_id,
        "name": combo.name,
        "description": combo.description,
        "image_url": combo.image_url,
        "is_available": combo.is_available,
        "total_price": total_price,
        "total_duration_minutes": total_duration,
        "services": combo.services,
    }


@router.get(
    "/",
    response_model=List[ComboServiceResponse],
    dependencies=[Depends(get_optional_user)],
)
def list_combo_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all combo services"""
    svc = ComboServiceController(db)
    combos = svc.list_combo_services(skip=skip, limit=limit)
    
    result = []
    for combo in combos:
        total_price, total_duration = svc.calculate_combo_price_and_duration(combo.combo_service_id)
        result.append({
            "combo_service_id": combo.combo_service_id,
            "name": combo.name,
            "description": combo.description,
            "image_url": combo.image_url,
            "is_available": combo.is_available,
            "total_price": total_price,
            "total_duration_minutes": total_duration,
            "services": combo.services,
        })
    
    return result


@router.get(
    "/available/",
    response_model=List[ComboServiceResponse],
    dependencies=[Depends(get_optional_user)],
)
def list_available_combo_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List only available combo services"""
    svc = ComboServiceController(db)
    combos = svc.list_available_combo_services(skip=skip, limit=limit)
    
    result = []
    for combo in combos:
        total_price, total_duration = svc.calculate_combo_price_and_duration(combo.combo_service_id)
        result.append({
            "combo_service_id": combo.combo_service_id,
            "name": combo.name,
            "description": combo.description,
            "image_url": combo.image_url,
            "is_available": combo.is_available,
            "total_price": total_price,
            "total_duration_minutes": total_duration,
            "services": combo.services,
        })
    
    return result


@router.put(
    "/{combo_service_id}",
    response_model=ComboServiceResponse,
    dependencies=[Depends(get_current_admin_user)],
)
def update_combo_service(
    combo_service_id: int,
    payload: ComboServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update a combo service (Admin only)"""
    svc = ComboServiceController(db)
    try:
        combo = svc.update_combo_service(
            combo_service_id=combo_service_id,
            name=payload.name,
            description=payload.description,
            image_url=payload.image_url,
            is_available=payload.is_available,
            service_ids=None,
            service_names=payload.service_names,
        )
        
        if not combo:
            raise HTTPException(status_code=404, detail="Combo service not found")
        
        total_price, total_duration = svc.calculate_combo_price_and_duration(combo_service_id)
        
        return {
            "combo_service_id": combo.combo_service_id,
            "name": combo.name,
            "description": combo.description,
            "image_url": combo.image_url,
            "is_available": combo.is_available,
            "total_price": total_price,
            "total_duration_minutes": total_duration,
            "services": combo.services,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{combo_service_id}/image",
    status_code=200,
    dependencies=[Depends(get_current_admin_user)],
)
def upload_combo_service_image(
    combo_service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image for a combo service and update the image_url."""
    svc = ComboServiceController(db)
    combo = svc.get_combo_service(combo_service_id)
    
    if not combo:
        raise HTTPException(status_code=404, detail="Combo service not found")
    
    try:
        # Read file content
        content = file.file.read()
        
        # Generate unique S3 key
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"combo-services/{combo_service_id}/{uuid.uuid4()}.{file_ext}"
        
        # Upload to S3
        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content, 
            s3_key, 
            content_type=file.content_type or "image/jpeg"
        )
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        # Update combo service with new image URL
        updated = svc.update_combo_service(
            combo_service_id=combo_service_id,
            image_url=image_url
        )
        
        total_price, total_duration = svc.calculate_combo_price_and_duration(combo_service_id)
        
        return {
            "combo_service_id": updated.combo_service_id,
            "name": updated.name,
            "description": updated.description,
            "image_url": updated.image_url,
            "is_available": updated.is_available,
            "total_price": total_price,
            "total_duration_minutes": total_duration,
            "services": updated.services,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


@router.put(
    "/{combo_service_id}/image",
    status_code=200,
    dependencies=[Depends(get_current_admin_user)],
)
def update_combo_service_image(
    combo_service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Update/replace the image for a combo service."""
    svc = ComboServiceController(db)
    combo = svc.get_combo_service(combo_service_id)
    
    if not combo:
        raise HTTPException(status_code=404, detail="Combo service not found")
    
    try:
        # Read file content
        content = file.file.read()
        
        # Generate unique S3 key
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"combo-services/{combo_service_id}/{uuid.uuid4()}.{file_ext}"
        
        # Upload to S3
        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content, 
            s3_key, 
            content_type=file.content_type or "image/jpeg"
        )
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        # Update combo service with new image URL
        updated = svc.update_combo_service(
            combo_service_id=combo_service_id,
            image_url=image_url
        )
        
        total_price, total_duration = svc.calculate_combo_price_and_duration(combo_service_id)
        
        return {
            "combo_service_id": updated.combo_service_id,
            "name": updated.name,
            "description": updated.description,
            "image_url": updated.image_url,
            "is_available": updated.is_available,
            "total_price": total_price,
            "total_duration_minutes": total_duration,
            "services": updated.services,
            "message": "Combo service image updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")


@router.delete(
    "/{combo_service_id}",
    status_code=204,
    dependencies=[Depends(get_current_admin_user)],
)
def delete_combo_service(combo_service_id: int, db: Session = Depends(get_db)):
    """Delete a combo service (Admin only)"""
    svc = ComboServiceController(db)
    success = svc.delete_combo_service(combo_service_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Combo service not found")
    
    return None
