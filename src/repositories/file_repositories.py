from typing import List, Optional
from sqlalchemy.orm import Session
from src.schemas.file import FileUpload, FileType
from src.service.s3 import delete_object


class FileUploadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        file_url: str,
        file_type: FileType,
        associated_id: int,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
    ) -> FileUpload:
        """Create a new file upload record"""
        file_upload = FileUpload(
            filename=filename,
            file_url=file_url,
            file_type=file_type,
            associated_id=associated_id,
            file_size=file_size,
            content_type=content_type,
        )
        self.db.add(file_upload)
        self.db.commit()
        self.db.refresh(file_upload)
        return file_upload

    def get_by_id(self, file_id: int) -> Optional[FileUpload]:
        """Get file upload by ID"""
        return self.db.query(FileUpload).filter(FileUpload.file_id == file_id).first()

    def get_by_associated_id(
        self,
        associated_id: int,
        file_type: FileType,
    ) -> List[FileUpload]:
        """Get all files associated with a product or service"""
        return self.db.query(FileUpload).filter(
            FileUpload.associated_id == associated_id,
            FileUpload.file_type == file_type,
        ).all()

    def delete(self, file_id: int) -> bool:
        """Delete a file upload record and also the file in S3"""
        file = self.get_by_id(file_id)
        if not file:
            return False
        
        # 1. Delete from S3
        delete_object(file.file_url)
        
        # 2. Delete from DB
        self.db.delete(file)
        self.db.commit()
        return True

    def list_by_product(self, product_id: int) -> List[FileUpload]:
        """List all images for a product"""
        return self.get_by_associated_id(product_id, FileType.PRODUCT)

    def list_by_service(self, service_id: int) -> List[FileUpload]:
        """List all images for a service"""
        return self.get_by_associated_id(service_id, FileType.SERVICE)
