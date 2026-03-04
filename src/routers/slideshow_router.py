from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.slideshow_model import SlideshowCreate, SlideshowResponse
from src.controller.slideshow_controller import SlideshowController
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
