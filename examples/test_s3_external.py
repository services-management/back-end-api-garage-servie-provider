import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.service.s3 import upload_bytes, get_s3_client
from src.config.settings import settings

def test_s3_connection():
    print(f"Testing S3 Connection to: {settings.S3_ENDPOINT_URL}")
    print(f"Bucket: {settings.S3_BUCKET_NAME}")
    
    try:
        client = get_s3_client()
        # Try to list objects in the bucket
        response = client.list_objects_v2(Bucket=settings.S3_BUCKET_NAME, MaxKeys=1)
        print("✅ S3 Connection successful! (Bucket exists and is accessible)")
        return True
    except Exception as e:
        print(f"❌ S3 Connection failed: {e}")
        return False

def test_upload():
    print("\nTesting File Upload...")
    dummy_data = b"Hello, this is a test file for S3 upload via https://fsgw.itedev.online."
    file_name = "test_upload_external.txt"
    content_type = "text/plain"
    
    try:
        url = upload_bytes(dummy_data, file_name=file_name, content_type=content_type)
        print(f"✅ Upload successful!")
        print(f"🔗 Public URL: {url}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    if test_s3_connection():
        test_upload()
    else:
        print("\nSkipping upload test due to connection failure.")
