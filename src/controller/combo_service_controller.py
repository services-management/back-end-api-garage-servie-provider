from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.combo_service_model import ComboService
from src.repositories.combo_service_repositories import ComboServiceRepository
from src.repositories.service_repositories import ServiceRepository
from src.schemas.product import Service


class ComboServiceController:
    """Controller for combo service operations."""

    def __init__(self, db: Session):
        self.db = db
        self.combo_repo = ComboServiceRepository(db)
        self.service_repo = ServiceRepository(db)

    def create_combo_service(
        self,
        name: str,
        service_names: List[str],
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        is_available: bool = True,
        service_ids: Optional[List[int]] = None,
    ) -> ComboService:
        """Create a new combo service from multiple services.
        
        Args:
            name: Name of the combo service
            service_names: List of service names to combine (minimum 2)
            description: Optional description
            image_url: Optional image URL
            is_available: Whether the combo is available
            service_ids: Deprecated - kept for backward compatibility
            
        Returns:
            Created ComboService instance
            
        Raises:
            ValueError: If name already exists, fewer than 2 services, or service not found
        """
        # Resolve services from names
        services = self._resolve_services(service_ids=None, service_names=service_names)

        # Check name uniqueness
        if self.combo_repo.get_by_name(name):
            raise ValueError(f"Combo service with name '{name}' already exists")

        # Create combo service
        combo = self.combo_repo.create(
            name=name,
            description=description,
            image_url=image_url,
            is_available=is_available,
            services=services
        )
        return combo

    def get_combo_service(self, combo_service_id: int) -> Optional[ComboService]:
        """Get a combo service by ID."""
        return self.combo_repo.get_by_id_with_services(combo_service_id)

    def list_combo_services(self, skip: int = 0, limit: int = 100) -> List[ComboService]:
        """List all combo services."""
        return self.combo_repo.list_with_services(skip=skip, limit=limit)

    def list_available_combo_services(self, skip: int = 0, limit: int = 100) -> List[ComboService]:
        """List only available combo services."""
        return self.combo_repo.list_available(skip=skip, limit=limit)

    def update_combo_service(
        self,
        combo_service_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        is_available: Optional[bool] = None,
        service_names: Optional[List[str]] = None,
        service_ids: Optional[List[int]] = None,
    ) -> Optional[ComboService]:
        """Update a combo service.
        
        Args:
            combo_service_id: ID of combo service to update
            name: New name (optional)
            description: New description (optional)
            image_url: New image URL (optional)
            is_available: New availability status (optional)
            service_names: New list of service names (optional, must have at least 2)
            service_ids: Deprecated - kept for backward compatibility
            
        Returns:
            Updated ComboService or None if not found
            
        Raises:
            ValueError: If name taken, fewer than 2 services, or service not found
        """
        combo = self.combo_repo.get_by_id(combo_service_id)
        if not combo:
            return None

        # Validate and fetch services if provided
        services = None
        if service_names is not None:
            services = self._resolve_services(service_ids=None, service_names=service_names)

        # Check name uniqueness if changing name
        if name and name != combo.name:
            if self.combo_repo.get_by_name(name):
                raise ValueError(f"Combo service with name '{name}' already exists")

        return self.combo_repo.update(
            combo_service_id=combo_service_id,
            name=name,
            description=description,
            image_url=image_url,
            is_available=is_available,
            services=services,
        )

    def _resolve_services(
        self,
        service_names: Optional[List[str]] = None,
        service_ids: Optional[List[int]] = None,
    ) -> List[Service]:
        """Resolve services from names ensuring minimum count and existence."""
        if not service_names:
            raise ValueError("Provide at least two service names")

        if len(service_names) < 2:
            raise ValueError("Combo service must include at least 2 services")

        resolved_services: List[Service] = []

        for service_name in service_names:
            service = self.service_repo.get_by_name(service_name)
            if not service:
                raise ValueError(f"Service with name '{service_name}' not found")
            resolved_services.append(service)

        return resolved_services

    def delete_combo_service(self, combo_service_id: int) -> bool:
        """Delete a combo service."""
        return self.combo_repo.delete(combo_service_id)

    def calculate_combo_price_and_duration(self, combo_service_id: int) -> tuple:
        """Calculate total price and duration for a combo service.
        
        Returns:
            Tuple of (total_price: Decimal, total_duration: int)
        """
        combo = self.get_combo_service(combo_service_id)
        if not combo:
            raise ValueError(f"Combo service with ID {combo_service_id} not found")

        total_price = Decimal("0")
        total_duration = 0

        for service in combo.services:
            total_price += Decimal(str(service.price))
            total_duration += service.duration_minutes

        return total_price, total_duration
