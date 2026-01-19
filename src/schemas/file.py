from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.config.database import Base
import enum


class FileType(str, enum.Enum):
    PRODUCT = "product"
    SERVICE = "service"


class FileUpload(Base):
    __tablename__ = "file_uploads"

    file_id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False, index=True)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    
    # Association type: product or service
    file_type = Column(SQLEnum(FileType), nullable=False)
    
    # Foreign key (can be product_id or service_id depending on file_type)
    associated_id = Column(Integer, nullable=False)
    
    # Metadata
    uploaded_at = Column(DateTime, default=func.now(), index=True)
    
    def __repr__(self):
        return f"<FileUpload(id={self.file_id}, type={self.file_type}, url={self.file_url})>"
