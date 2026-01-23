from typing import Optional

import boto3
from botocore.exceptions import ClientError

from src.config.settings import Settings

settings = Settings()


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
            self.s3_client.upload_file(
                file_path,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )

            # Construct the URL
            url = f"{settings.S3_ENDPOINT_URL}/{self.bucket}/{s3_key}"
            return url
        except ClientError as e:
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
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
            )

            # Construct the URL
            url = f"{settings.S3_ENDPOINT_URL}/{self.bucket}/{s3_key}"
            return url
        except ClientError as e:
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
