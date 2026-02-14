from typing import List, Optional # Ensure List and Optional are imported here
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controller.product_controller import ProductController
from src.dependency.auth import get_current_admin_user, get_optional_user
from src.models.product_model import (  # Adjusted import path
    ProductCreate, ProductResponse, ProductUpdate,ProductOut)
from src.core.enums import VehicleType, FuelType, DriveType, TransmissionType # Import Vehicle enums
from src.repositories.product_vehicle_repository import ProductVehicleRepository
from src.service.s3_service import S3Service
# from src.models.vehicle_model import VehicleFilter


router = APIRouter(
    prefix="/product", tags=["Product Management"]
)

# --- Routes ---

@router.post("/", response_model= ProductResponse,
             status_code=201,
             dependencies=[Depends(get_current_admin_user)],
             )
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    svc = ProductController(db)
    try:
        product = svc.create_product(
            name=payload.name,
            selling_price=payload.selling_price,
            unit_cost=payload.unit_cost,
            category_name=payload.category_name,
            description=payload.description,  # ADDED
            image_url=payload.image_url,      # ADDED
            status=payload.status,            # ADDED
            initial_stock=payload.initial_stock,
            min_stock_level=payload.min_stock_level,
        )
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{product_id}/image",
             status_code=200,
             dependencies=[Depends(get_current_admin_user)],
             tags=["Product Management"])
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image for a product and update the image_url."""
    svc = ProductController(db)
    product = svc.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Read file content
        content = file.file.read()

        # Generate unique S3 key
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"products/{product_id}/{uuid.uuid4()}.{file_ext}"

        # Upload to S3
        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content,
            s3_key,
            content_type=file.content_type or "image/jpeg"
        )

        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        # Update product with new image URL
        updated = svc.update_product(
            product_id=product_id,
            image_url=image_url
        )

        return {"product_id": product_id, "image_url": image_url, "product": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.put("/{product_id}/image",
            status_code=200,
            dependencies=[Depends(get_current_admin_user)],
            tags=["Product Management"])
def update_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Update/replace the image for a product."""
    svc = ProductController(db)
    product = svc.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Read file content
        content = file.file.read()

        # Generate unique S3 key
        file_ext = file.filename.split('.')[-1] if file.filename else 'jpg'
        s3_key = f"products/{product_id}/{uuid.uuid4()}.{file_ext}"

        # Upload to S3
        s3_service = S3Service()
        image_url = s3_service.upload_file_from_bytes(
            content,
            s3_key,
            content_type=file.content_type or "image/jpeg"
        )

        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        # Update product with new image URL
        updated = svc.update_product(
            product_id=product_id,
            image_url=image_url
        )

        return {"product_id": product_id, "image_url": image_url, "product": updated, "message": "Product image updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")

@router.get("/filter-by-vehicle",response_model=List[ProductOut])
def get_product_by_vehicle(
    make: str = Query(..., min_length=1, example="Toyota"),
    model: str = Query(..., min_length=1, example="Camry"),
    year: int = Query(..., ge=1900, le=2100, example=2022),
    vehicle_type: Optional[VehicleType] = Query(None),
    fuel_type: Optional[FuelType] = Query(None),
    drive_type: Optional[DriveType] = Query(None),
    transmission: Optional[TransmissionType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search for products that are compatible with a specific vehicle.
    Example: /products/filter-by-vehicle?make=Toyota&model=Camry&year=2022"""
    try:
        controller = ProductController(db)
        products = controller.filter_products_by_vehicle(
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
        return products
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{product_id}",
            response_model= ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)):
    svc = ProductController(db)
    product = svc.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    svc = ProductController(db)
    if current_user:
        print(f"User {current_user.id} ({current_user.role}) is viewing products.")
    else:
        print("A Guest is viewing products.")
    return svc.list_product(skip=skip, limit=limit)

@router.get("/by-category/{category_id}",
            response_model=List[ProductResponse],
            dependencies=[Depends(get_optional_user)]
           )
def list_products_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    svc = ProductController(db)
    # Optional: Logic to see what categories are popular with guests vs admins
    # if current_user:
    #     print(f"User {current_user.id} is filtering by category {category_id}")
    try:
        return svc.list_product_by_category(category_id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{product_id}",
            response_model= ProductResponse,
            dependencies=[Depends(get_current_admin_user)],)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db)
):
    svc = ProductController(db)
    try:
        updated = svc.update_product(
            product_id=product_id,
            name=payload.name,
            selling_price=payload.selling_price,
            unit_cost=payload.unit_cost,
            category_name=payload.category_name,
            description=payload.description,  # ADDED
            image_url=payload.image_url,      # ADDED
            status=payload.status,            # ADDED
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{product_id}",
               status_code=204,
               dependencies=[Depends(get_current_admin_user)],)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    svc = ProductController(db)
    deleted = svc.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return None

@router.post("/{product_id}/vehicle/{vehicle_id}",
             status_code=201,
             dependencies=[Depends(get_current_admin_user)])
def link_product_to_vehicle(
    product_id: int,
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    """Link a product to a vehicle."""
    repo = ProductVehicleRepository(db)
    link = repo.link_product_to_vehicle(product_id=product_id, vehicle_id=vehicle_id)
    if not link:
        raise HTTPException(status_code=404, detail="Product or Vehicle not found")
    return {"message": "Product linked to vehicle successfully"}
