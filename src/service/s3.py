import os
import uuid
from typing import Optional

import boto3
from botocore.client import Config

from src.config.settings import settings


_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(s3={"addressing_style": "virtual"}),
        )
    return _s3_client


def _public_url(bucket: str, key: str, region: Optional[str] = None) -> str:
    region = region or settings.AWS_REGION
    # us-east-1 has a legacy global endpoint, but the regional form works for GETs.
    if region == "us-east-1":
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def upload_bytes(
    data: bytes,
    *,
    file_name: str,
    content_type: Optional[str] = None,
    prefix: str = "images",
) -> str:
    """Upload raw bytes to S3 and return the public URL.

    The object key is generated as: {prefix}/{uuid4}-{sanitized_name}
    """
    bucket = settings.AWS_BUCKET_NAME
    if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and bucket):
        raise RuntimeError("Missing AWS S3 configuration. Check environment variables.")

    safe_name = os.path.basename(file_name).replace(" ", "_")
    key = f"{prefix}/{uuid.uuid4()}-{safe_name}"

    client = get_s3_client()
    extra = {"ACL": "public-read"}
    if content_type:
        extra["ContentType"] = content_type

    client.put_object(Bucket=bucket, Key=key, Body=data, **extra)
    return _public_url(bucket, key, settings.AWS_REGION)
