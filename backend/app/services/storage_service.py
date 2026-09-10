from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.db.models.campaign import Campaign

from app.services.validation_service import ValidationService

from app.services.campaign_service import CampaignService

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

        try:
            db.flush()

            CampaignService.import_campaigns(
                str(file_path),
                dataset.id,
                db,
            )

            db.commit()
            db.refresh(dataset)

        except Exception:
            db.rollback()
            file_path.unlink(missing_ok=True)
            raise

        return {
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "status": dataset.status,
            "message": "File uploaded successfully",
        }

    @staticmethod
    def get_dataset_status(
        dataset_id: str,
        current_user_id: str,
        db: Session,
    ):
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        if dataset.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this dataset",
            )

        return {
            "dataset_id": dataset.id,
            "status": dataset.status,
        }

    @staticmethod
    def get_user_datasets(
        current_user_id: str,
        db: Session,
    ):
        return (
            db.query(Dataset)
            .filter(Dataset.user_id == current_user_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )

    @staticmethod
    def get_dataset_campaigns(
        dataset_id: str,
        current_user_id: str,
        db: Session,
    ):
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        if dataset.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this dataset",
            )

        return (
            db.query(Campaign)
            .filter(Campaign.dataset_id == dataset_id)
            .order_by(Campaign.created_at.asc())
            .all()
        )