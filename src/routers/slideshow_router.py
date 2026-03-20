from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
import uuid
from src.config.database import get_db
from src.models.slideshow_model import SlideshowCreate, SlideshowResponse
from src.controller.slideshow_controller import SlideshowController
from src.service.s3_service import S3Service
from src.core.enums import ServiceType
from src.dependency.auth import get_current_admin_user

router = APIRouter(
    prefix="/slideshow",
    tags=["Slideshow"]
)

@router.get("/{service_type}", response_model=List[SlideshowResponse])
def get_slideshow(service_type: ServiceType, db: Session = Depends(get_db)):
    """Public endpoint to get slideshow images for Home or Garage."""
    controller = SlideshowController(db)
    return controller.get_slides_by_type(service_type)

@router.post("/", response_model=SlideshowResponse, status_code=status.HTTP_201_CREATED)
def create_slide(
    payload: SlideshowCreate, 
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin_user)
):
    """Admin only: Add a new image to a slideshow."""
    controller = SlideshowController(db)
    return controller.add_slide(payload.image_url, payload.service_type)

@router.post("/{slide_id}/image", response_model=SlideshowResponse)
def upload_slide_image(
    slide_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin_user)
):
    """Admin only: Upload an image for a slideshow slide."""
    controller = SlideshowController(db)
    slide = controller.repo.get(slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    try:
        content = file.file.read()
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"slideshow/{slide_id}/{uuid.uuid4()}.{file_ext}"

        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content,
            s3_key,
            content_type=file.content_type or "image/jpeg"
        )

        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        return controller.update_slide(slide_id, image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.delete("/{slide_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slide(
    slide_id: int, 
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin_user)
):
    """Admin only: Remove an image from a slideshow."""
    controller = SlideshowController(db)
    if not controller.delete_slide(slide_id):
        raise HTTPException(status_code=404, detail="Slide not found")
    return None
