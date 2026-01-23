from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.models.combo_service_model import ComboService
from src.repositories.base_repositories import BaseRepository


class ComboServiceRepository(BaseRepository[ComboService]):
    def __init__(self, db: Session):
        super().__init__(db, ComboService)

    def get_by_id(self, combo_service_id: int) -> Optional[ComboService]:
        """Get combo service by ID."""
        return self.db.get(ComboService, combo_service_id)

    def get_by_id_with_services(self, combo_service_id: int) -> Optional[ComboService]:
        """Get combo service with related services."""
        stmt = (
            select(ComboService)
            .options(joinedload(ComboService.services))
            .where(ComboService.combo_service_id == combo_service_id)
        )
        return self.db.execute(stmt).scalars().first()

    def get_by_name(self, name: str) -> Optional[ComboService]:
        """Get combo service by name."""
        stmt = select(ComboService).where(ComboService.name == name)
        return self.db.execute(stmt).scalars().first()

    def list(self, skip: int = 0, limit: int = 100) -> List[ComboService]:
        """List all combo services with pagination."""
        stmt = select(ComboService).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def list_with_services(self, skip: int = 0, limit: int = 100) -> List[ComboService]:
        """List combo services with their related services."""
        stmt = (
            select(ComboService)
            .options(joinedload(ComboService.services))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().unique().all())

    def list_available(self, skip: int = 0, limit: int = 100) -> List[ComboService]:
        """List only available combo services."""
        stmt = (
            select(ComboService)
            .where(ComboService.is_available)
            .options(joinedload(ComboService.services))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().unique().all())

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        is_available: bool = True,
        services: Optional[List] = None,
    ) -> ComboService:
        """Create a new combo service."""
        combo = ComboService(
            name=name,
            description=description,
            image_url=image_url,
            is_available=is_available,
            services=services or []
        )
        self.db.add(combo)
        self.db.commit()
        self.db.refresh(combo)
        return combo

    def update(
        self,
        combo_service_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        is_available: Optional[bool] = None,
        services: Optional[List] = None,
    ) -> Optional[ComboService]:
        """Update a combo service."""
        combo = self.get_by_id(combo_service_id)
        if not combo:
            return None

        if name is not None:
            combo.name = name
        if description is not None:
            combo.description = description
        if image_url is not None:
            combo.image_url = image_url
        if is_available is not None:
            combo.is_available = is_available
        if services is not None:
            combo.services = services

        self.db.commit()
        self.db.refresh(combo)
        return combo

    def delete(self, combo_service_id: int) -> bool:
        """Delete a combo service."""
        combo = self.get_by_id(combo_service_id)
        if not combo:
            return False

        self.db.delete(combo)
        self.db.commit()
        return True
