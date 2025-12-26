from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from src.repositories.base_repositories import BaseRepository
from src.schemas.product import Service


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
            .where(Service.is_available == True)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        name: str,
        image_url: str,
        price: Decimal,
        duration_minutes: int,
        description: Optional[str] = None,
        is_available: bool = True,
    ) -> Service:
        service = Service(
            name=name,
            description=description,
            image_url=image_url,
            price=price,
            duration_minutes=duration_minutes,
            is_available=is_available,
        )
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def update(
        self,
        service_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        price: Optional[Decimal] = None,
        duration_minutes: Optional[int] = None,
        is_available: Optional[bool] = None,
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
        if price is not None:
            service.price = price
        if duration_minutes is not None:
            service.duration_minutes = duration_minutes
        if is_available is not None:
            service.is_available = is_available

        self.db.commit()
        self.db.refresh(service)
        return service

    def delete(self, service_id: int) -> bool:
        service = self.get_by_id(service_id)
        if not service:
            return False
        self.db.delete(service)
        self.db.commit()
        return True
