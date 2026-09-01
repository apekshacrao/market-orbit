from pydantic import BaseModel
from typing import Optional, List

class FileUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    status: str
    message: str

class DatasetResponse(BaseModel):
    id: str
    filename: str
    status: str
    row_count: int

    class Config:
        from_attributes = True

class ValidationErrorDetail(BaseModel):
    row: Optional[int] = None
    column: Optional[str] = None
    message: str
