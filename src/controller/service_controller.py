from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session

from src.repositories.service_repositories import ServiceRepository
from src.repositories.product_repositories import ProductRepository
from src.repositories.file_repositories import FileUploadRepository
from src.schemas.product import Service


class ServiceController:
    def __init__(self, db: Session):
        self.db = db
        self.service_repo = ServiceRepository(db)
        self.product_repo = ProductRepository(db)
        self.file_repo = FileUploadRepository(db)
    def create_service(
        self,
        name: str,
        price: Decimal,
        duration_minutes: int,
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
            price=price,
            duration_minutes=duration_minutes,
            is_available=is_available,
            associations=resolved_associations,
        )
        return service

    def get_service(self, service_id: int) -> Optional[Service]:
        service = self.service_repo.get_by_id(service_id)
        if service:
            service.images = self.file_repo.list_by_service(service_id)
            # Fetch images for each associated product
            if hasattr(service, "associations") and service.associations:
                for assoc in service.associations:
                    if assoc.product:
                        assoc.product.images = self.file_repo.list_by_product(assoc.product_id)
        return service

    def get_service_with_associations(self, service_id: int) -> Optional[Service]:
        service = self.service_repo.get_by_id_with_relations(service_id)
        if service:
            service.images = self.file_repo.list_by_service(service_id)
            # Fetch images for each associated product
            if service.associations:
                for assoc in service.associations:
                    if assoc.product:
                        assoc.product.images = self.file_repo.list_by_product(assoc.product_id)
        return service

    def list_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        services = self.service_repo.list(skip=skip, limit=limit)
        for s in services:
            s.images = self.file_repo.list_by_service(s.service_id)
            if hasattr(s, "associations") and s.associations:
                for assoc in s.associations:
                    if assoc.product:
                        assoc.product.images = self.file_repo.list_by_product(assoc.product_id)
        return services

    def list_services_with_associations(self, skip: int = 0, limit: int = 100) -> List[Service]:
        services = self.service_repo.list_with_relations(skip=skip, limit=limit)
        for s in services:
            s.images = self.file_repo.list_by_service(s.service_id)
            if s.associations:
                for assoc in s.associations:
                    if assoc.product:
                        assoc.product.images = self.file_repo.list_by_product(assoc.product_id)
        return services

    def list_available_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        services = self.service_repo.list_available(skip=skip, limit=limit)
        for s in services:
            s.images = self.file_repo.list_by_service(s.service_id)
            if hasattr(s, "associations") and s.associations:
                for assoc in s.associations:
                    if assoc.product:
                        assoc.product.images = self.file_repo.list_by_product(assoc.product_id)
        return services

    def update_service(
        self,
        service_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[Decimal] = None,
        duration_minutes: Optional[int] = None,
        is_available: Optional[bool] = None,
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
            price=price,
            duration_minutes=duration_minutes,
            is_available=is_available,
            associations=resolved_associations,
        )

    def delete_service(self, service_id: int) -> bool:
        existing = self.service_repo.get_by_id(service_id)
        if not existing:
            raise ValueError(f"Service with ID {service_id} not found.")
        return self.service_repo.delete(service_id)
