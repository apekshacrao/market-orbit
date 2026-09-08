from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.services.validation_service import ValidationService


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:

    @staticmethod
    async def save_upload(file, user, db: Session):
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported",
            )

        file_id = str(uuid4())

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        file_path = UPLOAD_DIR / f"{file_id}.csv"

        contents = await file.read()
        file_path.write_bytes(contents)

        validation = ValidationService.validate_dataset_format(
            str(file_path)
        )

        if not validation["is_valid"]:
            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Invalid CSV file",
                    "errors": validation["errors"],
                },
            )

        dataset = Dataset(
            id=file_id,
            user_id=user.id,
            filename=file.filename,
            file_path=str(file_path),
            status="PENDING",
            row_count=0,
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return {
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "status": dataset.status,
            "message": "File uploaded successfully",
        }

    @staticmethod
    def get_dataset_status(dataset_id: str):
        return {
            "dataset_id": dataset_id,
            "status": "COMPLETED",
        }