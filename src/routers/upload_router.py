from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.service.s3 import upload_bytes
from src.dependency.auth import get_current_admin_user
from src.config.database import get_db
from src.repositories.file_repositories import FileUploadRepository
from src.schemas.file import FileType
from src.models.file_model import FileUploadResponse

router = APIRouter(prefix="/upload", tags=["File Uploads"])


@router.post("/product/{product_id}/image", response_model=FileUploadResponse)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin_user),
):
    """Upload image and associate with product"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        url = upload_bytes(data, file_name=file.filename, content_type=file.content_type)
        file_repo = FileUploadRepository(db)
        file_upload = file_repo.create(
            filename=file.filename,
            file_url=url,
            file_type=FileType.PRODUCT,
            associated_id=product_id,
            file_size=len(data),
            content_type=file.content_type,
        )

        return file_upload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.post("/service/{service_id}/image", response_model=FileUploadResponse)
async def upload_service_image(
    service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin_user),
):
    """Upload image and associate with service"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        url = upload_bytes(data, file_name=file.filename, content_type=file.content_type)
        file_repo = FileUploadRepository(db)
        file_upload = file_repo.create(
            filename=file.filename,
            file_url=url,
            file_type=FileType.SERVICE,
            associated_id=service_id,
            file_size=len(data),
            content_type=file.content_type,
        )
        return file_upload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("/product/{product_id}/images", response_model=List[FileUploadResponse])
async def get_product_images(
    product_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin_user),
):
    """Get all images for a product"""
    file_repo = FileUploadRepository(db)
    return file_repo.list_by_product(product_id)


@router.get("/service/{service_id}/images", response_model=List[FileUploadResponse])
async def get_service_images(
    service_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin_user),
):
    """Get all images for a service"""
    file_repo = FileUploadRepository(db)
    return file_repo.list_by_service(service_id)


@router.put("/{file_id}", response_model=FileUploadResponse)
async def update_image(
    file_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin_user),
):
    """Update an existing image (Admin only)"""
    file_repo = FileUploadRepository(db)
    old_file = file_repo.get_by_id(file_id)
    if not old_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        # 1. Upload new image
        new_url = upload_bytes(data, file_name=file.filename, content_type=file.content_type)
        
        # 2. Delete old image from S3
        from src.service.s3 import delete_object
        delete_object(old_file.file_url)

        # Update the record
        old_file.filename = file.filename
        old_file.file_url = new_url
        old_file.file_size = len(data)
        old_file.content_type = file.content_type
        
        db.commit()
        db.refresh(old_file)

        return old_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")


@router.delete("/{file_id}", status_code=204)
async def delete_image(
    file_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin_user),
):
    """Delete an image from S3 and DB (Admin only)"""
    file_repo = FileUploadRepository(db)
    
    # Delete from S3 and DB
    if not file_repo.delete(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    
    return None
