from fastapi import APIRouter, UploadFile, File, Depends
from app.schemas.upload import FileUploadResponse
from app.services.storage_service import StorageService
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=FileUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    return await StorageService.save_upload(file, current_user)

@router.get("/{dataset_id}/status")
def get_status(dataset_id: str, current_user = Depends(get_current_user)):
    return StorageService.get_dataset_status(dataset_id)
