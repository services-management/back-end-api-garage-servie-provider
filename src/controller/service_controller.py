from decimal import Decimal
from typing import List, Optional, Any

from sqlalchemy.orm import Session

from src.repositories.product_repositories import ProductRepository
from src.repositories.service_repositories import ServiceRepository
from src.repositories.vehicle_repository import VehicleRepository
from src.schemas.product import Service, ProductStatus
from src.core.enums import ServiceType


class ServiceController:
    def __init__(self, db: Session):
        self.db = db
        self.service_repo = ServiceRepository(db)
        self.product_repo = ProductRepository(db)
        self.vehicle_repo = VehicleRepository(db)
    def create_service(
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
        # Check name uniqueness
        if self.service_repo.get_by_name(name):
            raise ValueError(f"Service with name '{name}' already exists.")
         # Resolve product names to IDs in associations
        resolved_associations = []
        if associations:
            for assoc in associations:
                product_name = assoc.get("product_name")
                if product_name:
                    product = self.product_repo.get_by_name(product_name)
                    if not product:
                        raise ValueError(f"Product '{product_name}' not found.")
                    # Backend maps name to the database ID
                    assoc["product_id"] = product.product_id
                resolved_associations.append(assoc)

        service = self.service_repo.create(
            name=name,
            description=description,
            image_url=image_url,
            garage_price=garage_price,
            home_price=home_price,
            duration_minutes=duration_minutes,
            is_available=is_available,
            service_type=service_type,
            associations=resolved_associations,
        )
        return service

    def get_service(self, service_id: int) -> Optional[Service]:
        return self.service_repo.get_by_id(service_id)

    def get_service_with_associations(self, service_id: int) -> Optional[Service]:
        service = self.service_repo.get_by_id_with_relations(service_id)
        if not service or service.status == ProductStatus.DELETED:
            return None
        return service

    def list_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        return self.service_repo.list(skip=skip, limit=limit)

    def list_services_with_associations(self, skip: int = 0, limit: int = 100) -> List[Service]:
        return self.service_repo.list_with_relations(skip=skip, limit=limit)

    def list_available_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        return self.service_repo.list_available(skip=skip, limit=limit)

    def filter_services_by_vehicle(
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
        """
        Filters services based on compatible vehicle information.
        """
        return self.service_repo.filter_by_vehicle(
            make_name=make_name,
            model_name=model_name,
            year=year,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            drive_type=drive_type,
            transmission=transmission,
            skip=skip,
            limit=limit
        )

    def get_service_estimates(
        self,
        vehicle_id: int,
        service_type: ServiceType
    ) -> List[dict]:
        """
        Calculates dynamic price estimates for services based on a specific vehicle.
        """
        return self.service_repo.get_service_estimates(vehicle_id, service_type)

    def get_catalog_for_vehicle(
        self,
        model_id: int,
        year: int,
        engine: str,
        service_type: ServiceType
    ) -> List[dict]:
        """
        Finds the vehicle_id first, then calculates service estimates.
        """
        vehicle_id = self.vehicle_repo.get_vehicle_id(model_id, year, engine)
        if not vehicle_id:
            raise ValueError(f"No vehicle configuration found for Model ID {model_id}, Year {year}, Engine {engine}")
        
        return self.get_service_estimates(vehicle_id, service_type)

    def update_service(
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
        # Check if service exists
        existing = self.service_repo.get_by_id(service_id)
        if not existing:
            return None

        # Check name uniqueness if updating name
        if name is not None and name != existing.name:
            if self.service_repo.get_by_name(name):
                raise ValueError(f"Service with name '{name}' already exists.")
        resolved_associations = None
        if associations is not None:
            resolved_associations = []
            for assoc in associations:
                product_name = assoc.get("product_name")
                if product_name:
                    product = self.product_repo.get_by_name(product_name)
                    if not product:
                        raise ValueError(f"Product '{product_name}' not found.")
                    assoc["product_id"] = product.product_id
                resolved_associations.append(assoc)

        return self.service_repo.update(
            service_id=service_id,
            name=name,
            description=description,
            image_url=image_url,
            garage_price=garage_price,
            home_price=home_price,
            duration_minutes=duration_minutes,
            is_available=is_available,
            service_type=service_type,
            associations=resolved_associations,
        )

    def delete_service(self, service_id: int) -> bool:
        existing = self.service_repo.get_by_id(service_id)
        if not existing:
            raise ValueError(f"Service with ID {service_id} not found.")
        return self.service_repo.delete(service_id)
