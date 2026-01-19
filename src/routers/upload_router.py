from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from src.service.s3 import upload_bytes
from src.dependency.auth import get_current_admin_user

router = APIRouter(prefix="/upload", tags=["File Uploads"])


@router.post("/image", dependencies=[Depends(get_current_admin_user)])
async def upload_image(file: UploadFile = File(...)):
    # Basic validation for images
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        url = upload_bytes(data, file_name=file.filename, content_type=file.content_type)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
