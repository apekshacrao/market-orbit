from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset


class StorageService:

    @staticmethod
    async def save_upload(file, user, db: Session):
        dataset = Dataset(
            id=str(uuid4()),
            user_id=user.id,
            filename=file.filename,
            file_path="",
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