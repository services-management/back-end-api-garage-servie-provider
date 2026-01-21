import os
import uuid
from typing import Optional
from urllib.parse import urlparse

import boto3

from src.config.settings import settings


_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            verify=settings.S3_VERIFY_SSL,
        )
    return _s3_client


def _public_url(bucket: str, key: str, endpoint: str) -> str:
    """Build public URL for MinIO object"""
    # Parse endpoint to build the URL
    parsed = urlparse(endpoint)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc
    return f"{scheme}://{netloc}/{bucket}/{key}"


def upload_bytes(
    data: bytes,
    *,
    file_name: str,
    content_type: Optional[str] = None,
    prefix: str = "images",
) -> str:
    """Upload raw bytes to MinIO and return the public URL.

    The object key is generated as: {prefix}/{uuid4}-{sanitized_name}
    """
    bucket = settings.S3_BUCKET_NAME
    if not (settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY and bucket):
        raise RuntimeError("Missing MinIO S3 configuration. Check environment variables.")

    safe_name = os.path.basename(file_name).replace(" ", "_")
    key = f"{prefix}/{uuid.uuid4()}-{safe_name}"

    client = get_s3_client()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type

    client.put_object(Bucket=bucket, Key=key, Body=data, **extra)
    return _public_url(bucket, key, settings.S3_ENDPOINT_URL)


def delete_object(url: str) -> bool:
    """Delete an object from MinIO given its public URL."""
    try:
        bucket = settings.S3_BUCKET_NAME
        # Extract the key from the URL
        # URL format: http://endpoint/bucket/prefix/uuid-name
        parsed = urlparse(url)
        # path is /bucket/prefix/uuid-name, so we skip the first 2 parts (/bucket/)
        path_parts = parsed.path.lstrip("/").split("/")
        if len(path_parts) < 2:
            return False
        
        # The first part is the bucket name, the rest is the key
        key = "/".join(path_parts[1:])
        
        client = get_s3_client()
        client.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Error deleting from S3: {e}")
        return False
