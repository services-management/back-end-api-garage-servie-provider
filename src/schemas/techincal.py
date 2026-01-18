
from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.config.database import Base
from datetime import datetime

TechnicalStatusEnum = Enum("free", "busy", "off_duty", name="technical_status_enum")


class TechnicalModel(Base):
    """SQLAlchemy model for Technical accounts"""
    __tablename__ = "technical"

    # Primary key
    technical_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Login Credentials (must be unique for authentication)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    # Contact
    phone_number = Column(String, unique=True, nullable=False)

    # Identification
    name = Column(String, nullable=False)

    # Role
    role = Column(String, default="technical", nullable=False)

    # Operational Fields
    team_id = Column(
        UUID(as_uuid=True),
        ForeignKey("technical_team.team_id", name="fk_technical_team"),
        nullable=True,
    )

    status = Column(TechnicalStatusEnum, default="free", nullable=False)

    # Each technical belongs to one team (nullable allowed)
    team = relationship(
        "TechnicalTeam",
        back_populates="members",
        foreign_keys=[team_id],
        uselist=False,
        # Optional explicit join for readability:
        # primaryjoin="TechnicalModel.team_id == TechnicalTeam.team_id",
    )


class TechnicalTeam(Base):
    """SQLAlchemy model for Technical Teams"""
    __tablename__ = "technical_team"

    # Primary Key
    team_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Team Information
    team_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Team Lead/Manager
    team_lead_id = Column(UUID(as_uuid=True), ForeignKey("technical.technical_id"), nullable=True)

    # Operational Fields
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team_lead = relationship(
        "TechnicalModel",
        foreign_keys=[team_lead_id],
        backref="led_teams",
        uselist=False,
    )

    # Members are technicals whose team_id points to this team’s team_id
    members = relationship(
        "TechnicalModel",
        back_populates="team",
        foreign_keys=[TechnicalModel.team_id], 
    )

    # If you have a Booking model with a FK to technical_team.team_id:
    # bookings = relationship("Booking", back_populates="assigned_team")
