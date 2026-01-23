from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Boolean
from sqlalchemy.orm import relationship

from src.config.database import Base


# Association table for many-to-many relationship between ComboService and Service
combo_service_association = Table(
    'combo_service_association',
    Base.metadata,
    Column('combo_service_id', Integer, ForeignKey('combo_services.combo_service_id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.service_id'), primary_key=True),
)


class ComboService(Base):
    """ORM model for combo services (combination of multiple services)."""
    __tablename__ = "combo_services"

    combo_service_id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(100), unique=True, nullable=False, index=True)
    description: Optional[str] = Column(String(500), nullable=True)
    image_url: Optional[str] = Column(String(250), nullable=True)
    is_available: bool = Column(Boolean, default=True)

    # Many-to-many relationship with Service (without back_populates)
    services = relationship(
        "Service",
        secondary=combo_service_association
    )

    def __repr__(self):
        return f"<ComboService(combo_service_id={self.combo_service_id}, name='{self.name}')>"
