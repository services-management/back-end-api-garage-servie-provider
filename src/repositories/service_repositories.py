from decimal import Decimal
from typing import List, Optional, Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.repositories.base_repositories import BaseRepository
from src.schemas.product import Service, ServiceProductAssociation, ProductVehicleCompatibility, ProductStatus
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
            .options(joinedload(Service.associations))
            .where(Service.service_id == service_id)
        )
        return self.db.execute(stmt).scalars().first()

    def get_by_name(self, name: str) -> Optional[Service]:
        stmt = select(Service).where(Service.name == name)
        return self.db.execute(stmt).scalars().first()

    def list(self, skip: int = 0, limit: int = 100) -> List[Service]:
        stmt = select(Service).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def list_with_relations(self, skip: int = 0, limit: int = 100) -> List[Service]:
        stmt = (
            select(Service)
            .options(joinedload(Service.associations))
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
        vehicle_type: Optional[Any] = None,
        fuel_type: Optional[Any] = None,
        drive_type: Optional[Any] = None,
        transmission: Optional[Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Service]:
        from src.schemas.vehicle import Make, Model, Vehicle
        from src.schemas.product import ServiceVehicleCompatibility
        
        stmt = (
            select(Service)
            .join(ServiceVehicleCompatibility, Service.service_id == ServiceVehicleCompatibility.service_id)
            .join(Vehicle, ServiceVehicleCompatibility.vehicle_id == Vehicle.vehicle_id)
            .join(Model, Vehicle.model_id == Model.id)
            .join(Make, Model.make_id == Make.id)
            .where(
                Make.name == make_name,
                Model.name == model_name,
                Vehicle.year == year,
                Service.is_available
            )
        )
        
        if vehicle_type:
            stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)
        if fuel_type:
            stmt = stmt.where(Vehicle.fuel_type == fuel_type)
        if drive_type:
            stmt = stmt.where(Vehicle.drive_type == drive_type)
        if transmission:
            stmt = stmt.where(Vehicle.transmission == transmission)
            
        stmt = stmt.options(
            joinedload(Service.associations)
        ).offset(skip).limit(limit)
        
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_service_estimates(
        self,
        vehicle_id: int,
        service_type: ServiceType
    ) -> List[dict]:
        from src.schemas.product import ServiceVehicleCompatibility
        
        # 1. Get services compatible with this vehicle
        # Note: We filter by service_type to only show relevant services for the selected mode
        stmt = (
            select(Service)
            .join(ServiceVehicleCompatibility, Service.service_id == ServiceVehicleCompatibility.service_id)
            .where(
                ServiceVehicleCompatibility.vehicle_id == vehicle_id,
                Service.service_type == service_type,
                Service.is_available
            )
            .options(joinedload(Service.associations).joinedload(ServiceProductAssociation.product))
        )
        services = self.db.execute(stmt).scalars().unique().all()
        
        estimates = []
        for service in services:
            # Labor price depends on service type
            labor_price = Decimal(str(service.home_price if service_type == ServiceType.HOME else service.garage_price))
            service_total = labor_price
            product_estimates = []
            
            for assoc in service.associations:
                product = assoc.product
                # Find product quantity for THIS specific vehicle
                compat_stmt = select(ProductVehicleCompatibility).where(
                    ProductVehicleCompatibility.product_id == product.product_id,
                    ProductVehicleCompatibility.vehicle_id == vehicle_id
                )
                compat = self.db.execute(compat_stmt).scalars().first()
                
                # Parse quantity (e.g., "4.5L" -> 4.5)
                qty = Decimal("1") # Default
                if compat and compat.quantity_required:
                    match = re.search(r"(\d+\.?\d*)", compat.quantity_required)
                    if match:
                        qty = Decimal(match.group(1))
                
                # Product price calculation:
                # Garage: selling_price * qty
                # Home: (selling_price + price_adjustment) * qty
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
                "service_type": service.service_type,
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
        service_type: ServiceType,
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
            is_available=is_available,
            service_type=service_type
        )
        self.db.add(service)
        self.db.flush()

        if associations:
            for assoc_data in associations:
                assoc = ServiceProductAssociation(
                    service_id=service.service_id,
                    product_id=assoc_data["product_id"],
                    quantity_required=assoc_data["quantity_required"],
                    is_optional=assoc_data.get("is_optional", False)
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
        service_type: Optional[ServiceType] = None,
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
        if service_type is not None:
            service.service_type = service_type

        if associations is not None:
            # Clear existing associations
            stmt = select(ServiceProductAssociation).where(ServiceProductAssociation.service_id == service_id)
            existing_assocs = self.db.execute(stmt).scalars().all()
            for assoc in existing_assocs:
                self.db.delete(assoc)
            
            # Add new associations
            for assoc_data in associations:
                assoc = ServiceProductAssociation(
                    service_id=service_id,
                    product_id=assoc_data["product_id"],
                    quantity_required=assoc_data["quantity_required"],
                    is_optional=assoc_data.get("is_optional", False)
                )
                self.db.add(assoc)

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
