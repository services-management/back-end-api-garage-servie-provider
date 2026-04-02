from typing import List, Optional # Ensure List and Optional are imported here
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controller.product_controller import ProductController
from src.dependency.auth import get_current_admin_user, get_optional_user
from src.models.product_model import (  # Adjusted import path
    ProductCreate, ProductResponse, ProductUpdate, ProductOut)
from src.models.admin_model import AdminOut
from src.repositories.product_vehicle_repository import ProductVehicleRepository
from src.service.s3_service import S3Service
from src.core.enums import TransmissionType, FuelType, DriveType, VehicleType
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
            price_adjustment=payload.price_adjustment,
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

@router.get("/all", response_model=List[ProductResponse])
def list_products_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    svc = ProductController(db)
    if current_user:
        print(f"User {current_user.admin_id} ({current_user.role}) is viewing products.")
    else:
        print("A Guest is viewing products.")
    return svc.list_product(skip=skip, limit=limit)

@router.get("/",response_model=List[ProductResponse])
def list_products_active(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    svc = ProductController(db) 
    return svc.list_product_active(skip=skip, limit=limit)

@router.get("/filter-by-vehicle", response_model=List[ProductOut])
def filter_products_by_vehicle(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    year: int = Query(..., ge=1900, le=2100),
    engine: Optional[str] = Query(None, min_length=1),
    vehicle_type: Optional[VehicleType] = Query(None),
    fuel_type: Optional[FuelType] = Query(None),
    drive_type: Optional[DriveType] = Query(None),
    transmission: Optional[TransmissionType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Search for products compatible with a specific vehicle."""
    svc = ProductController(db)
    return svc.filter_products_by_vehicle(
        make_name=make,
        model_name=model,
        year=year,
        engine=engine,
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        drive_type=drive_type,
        transmission=transmission,
        skip=skip,
        limit=limit
    )

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
            price_adjustment=payload.price_adjustment,
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
    quantity_required: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Link a product to a vehicle."""
    repo = ProductVehicleRepository(db)
    # If unit is provided, we can append it to quantity or note. 
    # The tests pass quantity_required=1 and unit='unit'.
    full_qty = quantity_required
    if quantity_required and unit:
        full_qty = f"{quantity_required} {unit}"
    
    link = repo.link_product_to_vehicle(
        product_id=product_id, 
        vehicle_id=vehicle_id,
        quantity_required=full_qty
    )
    if not link:
        raise HTTPException(status_code=404, detail="Product or Vehicle not found")
    return {"message": "Product linked to vehicle successfully"}


@router.patch("/{product_id}/vehicle/{vehicle_id}",
              dependencies=[Depends(get_current_admin_user)])
def update_product_vehicle_link(
    product_id: int,
    vehicle_id: int,
    quantity_required: Optional[str] = Query(None),
    note: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Update a product-vehicle compatibility link."""
    repo = ProductVehicleRepository(db)
    link = repo.update_link(
        product_id=product_id,
        vehicle_id=vehicle_id,
        quantity_required=quantity_required,
        note=note
    )
    if not link:
        raise HTTPException(status_code=404, detail="Product-Vehicle link not found")
    return {
        "message": "Product-vehicle link updated successfully",
        "product_id": link.product_id,
        "vehicle_id": link.vehicle_id,
        "quantity_required": link.quantity_required,
        "note": link.note
    }


@router.delete("/{product_id}/vehicle/{vehicle_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(get_current_admin_user)])
def delete_product_vehicle_link(
    product_id: int,
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    """Delete a product-vehicle compatibility link."""
    repo = ProductVehicleRepository(db)
    deleted = repo.delete_link(product_id, vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product-Vehicle link not found")
    return None


@router.get("/{product_id}/vehicles", response_model=List[dict])
def get_vehicles_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Get all vehicles compatible with a specific product."""
    from src.schemas.product import ProductVehicleCompatibility, Product
    from src.schemas.vehicle import Vehicle
    
    # Check product exists
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all vehicle links with vehicle details
    links = db.query(ProductVehicleCompatibility, Vehicle).join(
        Vehicle, ProductVehicleCompatibility.vehicle_id == Vehicle.vehicle_id
    ).filter(ProductVehicleCompatibility.product_id == product_id).all()
    
    result = []
    for link, vehicle in links:
        result.append({
            "vehicle_id": vehicle.vehicle_id,
            "model_id": vehicle.model_id,
            "year": vehicle.year,
            "engine": vehicle.engine,
            "vehicle_type": vehicle.vehicle_type.value if vehicle.vehicle_type else None,
            "fuel_type": vehicle.fuel_type.value if vehicle.fuel_type else None,
            "drive_type": vehicle.drive_type.value if vehicle.drive_type else None,
            "transmission": vehicle.transmission.value if vehicle.transmission else None,
            "is_active": vehicle.is_active,
            "quantity_required": link.quantity_required,
            "note": link.note
        })
    
    return result
