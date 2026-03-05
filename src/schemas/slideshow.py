from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from src.config.database import Base
from src.core.enums import ServiceType

class Slideshow(Base):
    __tablename__ = "slideshows"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), nullable=False)
    service_type = Column(SQLEnum(ServiceType, native_enum=False), nullable=False)
