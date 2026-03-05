from decimal import Decimal
from typing import List, Optional, Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.repositories.base_repositories import BaseRepository
from src.schemas.product import Service, ServiceCategoryAssociation, ProductVehicleCompatibility, ProductStatus, Product
from src.core.enums import ServiceType
import re


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, db: Session):
        super().__init__(db, Service)

    def get_by_id(self, service_id: int) -> Optional[Service]:
        return self.db.get(Service, service_id)

    def get_by_id_with_relations(self, service_id: int) -> Optional[Service]:
        stmt = (
            select(Service)
            .options(joinedload(Service.associations).joinedload(ServiceCategoryAssociation.category))
            .where(Service.service_id == service_id)
        )
        return self.db.execute(stmt).scalars().first()

    def get_by_name(self, name: str) -> Optional[Service]:
        stmt = select(Service).where(Service.name == name)
        return self.db.execute(stmt).scalars().first()

    def list(self, skip: int = 0, limit: int = 100) -> List[Service]:
        stmt = (
            select(Service)
            .where(Service.status != ProductStatus.DELETED)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_with_relations(self, skip: int = 0, limit: int = 100) -> List[Service]:
        stmt = (
            select(Service)
            .options(joinedload(Service.associations).joinedload(ServiceCategoryAssociation.category))
            .where(Service.status != ProductStatus.DELETED)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().unique().all())

    def list_available(self, skip: int = 0, limit: int = 100) -> List[Service]:
        stmt = (
            select(Service)
            .where(Service.is_available)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def filter_by_vehicle(
        self,
        make_name: str,
        model_name: str,
        year: int,
        engine: Optional[str] = None,
        vehicle_type: Optional[Any] = None,
        fuel_type: Optional[Any] = None,
        drive_type: Optional[Any] = None,
        transmission: Optional[Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Service]:
        # Logic: Services are universal. We return all active services.
        # The 'vehicle' parameters are used later in estimation to find correct parts.
        stmt = (
            select(Service)
            .where(
                Service.is_available,
                Service.status != ProductStatus.DELETED
            )
            .options(
                joinedload(Service.associations).joinedload(ServiceCategoryAssociation.category)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_service_estimates(
        self,
        vehicle_id: int,
        service_type: ServiceType
    ) -> List[dict]:
        # 1. Get all active services (no longer joining ServiceVehicleCompatibility)
        stmt = (
            select(Service)
            .where(
                Service.is_available,
                Service.status != ProductStatus.DELETED
            )
            .options(joinedload(Service.associations).joinedload(ServiceCategoryAssociation.category))
        )
        services = self.db.execute(stmt).scalars().unique().all()
        
        estimates = []
        for service in services:
            labor_price = Decimal(str(service.home_price if service_type == ServiceType.HOME else service.garage_price))
            service_total = labor_price
            product_estimates = []
            
            for assoc in service.associations:
                category = assoc.category
                # Find a product in this category that is compatible with this specific vehicle
                product_stmt = (
                    select(Product)
                    .join(ProductVehicleCompatibility, Product.product_id == ProductVehicleCompatibility.product_id)
                    .where(
                        Product.category_id == category.categoryID,
                        ProductVehicleCompatibility.vehicle_id == vehicle_id,
                        Product.status == ProductStatus.ACTIVE
                    )
                )
                product = self.db.execute(product_stmt).scalars().first()
                
                if not product:
                    # If no compatible product is found for this category, we might want to skip or handle it
                    continue

                compat_stmt = select(ProductVehicleCompatibility).where(
                    ProductVehicleCompatibility.product_id == product.product_id,
                    ProductVehicleCompatibility.vehicle_id == vehicle_id
                )
                compat = self.db.execute(compat_stmt).scalars().first()
                
                qty = Decimal("1") # Default
                if compat and compat.quantity_required:
                    match = re.search(r"(\d+\.?\d*)", compat.quantity_required)
                    if match:
                        qty = Decimal(match.group(1))
                
                base_unit_price = Decimal(str(product.selling_price))
                if service_type == ServiceType.HOME:
                    final_unit_price = base_unit_price + Decimal(str(product.price_adjustment))
                else:
                    final_unit_price = base_unit_price
                    
                total_product_price = final_unit_price * qty
                service_total += total_product_price
                
                product_estimates.append({
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "price_per_unit": final_unit_price,
                    "quantity_required": qty,
                    "total_product_price": total_product_price
                })
                
            estimates.append({
                "service_id": service.service_id,
                "service_name": service.name,
                "service_type": service_type,
                "base_labor_price": labor_price,
                "products": product_estimates,
                "total_estimated_price": service_total,
                "total_duration_minutes": service.duration_minutes
            })
            
        return estimates

    def create(
        self,
        name: str,
        image_url: str,
        garage_price: Decimal,
        home_price: Decimal,
        duration_minutes: int,
        description: Optional[str] = None,
        is_available: bool = True,
        associations: Optional[List[dict]] = None,
    ) -> Service:
        service = Service(
            name=name,
            description=description,
            image_url=image_url,
            garage_price=garage_price,
            home_price=home_price,
            duration_minutes=duration_minutes,
            is_available=is_available
        )
        self.db.add(service)
        self.db.flush()

        if associations:
            for assoc_data in associations:
                assoc = ServiceCategoryAssociation(
                    service_id=service.service_id,
                    category_id=assoc_data["category_id"]
                )
                self.db.add(assoc)

        self.db.commit()
        self.db.refresh(service)
        return service

    def update(
        self,
        service_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        garage_price: Optional[Decimal] = None,
        home_price: Optional[Decimal] = None,
        duration_minutes: Optional[int] = None,
        is_available: Optional[bool] = None,
        associations: Optional[List[dict]] = None,
    ) -> Optional[Service]:
        service = self.get_by_id(service_id)
        if not service:
            return None

        if name is not None:
            service.name = name
        if description is not None:
            service.description = description
        if image_url is not None:
            service.image_url = image_url
        if garage_price is not None:
            service.garage_price = garage_price
        if home_price is not None:
            service.home_price = home_price
        if duration_minutes is not None:
            service.duration_minutes = duration_minutes
        if is_available is not None:
            service.is_available = is_available

        if associations is not None:
            # By assigning a new list, SQLAlchemy's delete-orphan cascade 
            # will automatically delete the old records from the table.
            service.associations = [
                ServiceCategoryAssociation(
                    service_id=service_id,
                    category_id=assoc_data["category_id"]
                )
                for assoc_data in associations
            ]

        self.db.commit()
        self.db.refresh(service)
        return service

    def delete(self, service_id: int) -> bool:
        service = self.get_by_id(service_id)
        if not service:
            return False
        
        # Soft delete by setting status to DELETED
        service.status = ProductStatus.DELETED
        service.is_available = False
        self.db.commit()
        return True
