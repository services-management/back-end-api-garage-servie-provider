from typing import Optional
import os
from pathlib import Path
# from io import BytesIO
# from jinja2 import Environment, FileSystemLoader
#from weasyprint import HTML
import boto3
from botocore.exceptions import ClientError

from src.config.settings import settings

# SECURITY: Allowed file types and size limits
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.gif', '.webp'}
ALLOWED_CONTENT_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class S3Service:
    """Service for managing S3/MinIO uploads."""

    def __init__(self):
        """Initialize S3 client with MinIO configuration."""
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET

    def _sanitize_s3_key(self, s3_key: str) -> str:
        """Sanitize S3 key to prevent path traversal attacks."""
        # Remove path traversal attempts
        s3_key = s3_key.replace('..', '').replace('//', '/')
        # Ensure key doesn't start with /
        s3_key = s3_key.lstrip('/')
        return s3_key

    def _validate_file(self, file_path: str, content_type: str) -> None:
        """Validate file before upload.
        
        Raises:
            ValueError: If file is invalid
        """
        # Check file exists
        if not os.path.exists(file_path):
            raise ValueError("File not found")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Validate content type
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Invalid content type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}")
        
        # Validate file extension
        ext = Path(file_path).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    def upload_file(
        self, file_path: str, s3_key: str, content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """Upload a file to S3/MinIO.

        Args:
            file_path: Local file path to upload
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file

        Returns:
            The S3 URL of the uploaded file, or None if upload failed
        """
        try:
            # SECURITY: Sanitize and validate
            s3_key = self._sanitize_s3_key(s3_key)
            self._validate_file(file_path, content_type)
            
            self.s3_client.upload_file(
                file_path,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )

            # Construct the URL
            url = f"{settings.S3_ENDPOINT_URL}/{self.bucket}/{s3_key}"
            return url
        except (ClientError, ValueError) as e:
            print(f"Error uploading file to S3: {e}")
            return None

    def upload_file_from_bytes(
        self, file_bytes: bytes, s3_key: str, content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """Upload file from bytes to S3/MinIO.

        Args:
            file_bytes: File content as bytes
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file

        Returns:
            The S3 URL of the uploaded file, or None if upload failed
        """
        try:
            # SECURITY: Sanitize s3_key
            s3_key = self._sanitize_s3_key(s3_key)
            
            # Validate content type
            if content_type not in ALLOWED_CONTENT_TYPES:
                raise ValueError(f"Invalid content type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}")
            
            # Validate file size
            if len(file_bytes) > MAX_FILE_SIZE:
                raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB")
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
            )

            # Construct the URL
            url = f"{settings.S3_ENDPOINT_URL}/{self.bucket}/{s3_key}"
            return url
        except (ClientError, ValueError) as e:
            print(f"Error uploading file to S3: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3/MinIO.

        Args:
            s3_key: S3 object key (path in bucket)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False

    # def generate_invoice_pdf(booking_data) -> bytes:
    #     # 1. Load your HTML template
    #     env = Environment(loader=FileSystemLoader('templates'))
    #     template = env.get_template('invoice_template.html')
        
    #     # 2. Fill it with data
    #     html_out = template.render(booking=booking_data)
        
    #     # 3. Render to bytes
    #     pdf_bytes = BytesIO()
    #     HTML(string=html_out).write_pdf(pdf_bytes)
    #     return pdf_bytes.getvalue()
    
    # s3_service = S3Service()
    # def handle_invoice_upload(booking):
    #     # Generate the digital file
    #     pdf_content = generate_invoice_pdf(booking)
        
    #     # Path inside your S3 bucket
    #     s3_key = f"invoices/booking_{booking.booking_id}.pdf"
        
    #     # Upload using your existing class!
    #     invoice_url = S3_service.upload_file_from_bytes(
    #         file_bytes=pdf_content,
    #         s3_key=s3_key,
    #         content_type="application/pdf"
    #     )
    #     return invoice_url