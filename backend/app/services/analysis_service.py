from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset


class AnalysisService:

    @staticmethod
    def get_results(
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
            "dataset_id": dataset_id,
            "kpis": {
                "total_spend": 10000,
                "total_revenue": 35000,
                "overall_roas": 3.5,
            },
            "rankings": {
                "top": [],
                "bottom": [],
            },
            "trends": {},
            "ai_recommendations": [],
        }

    @staticmethod
    def get_kpis(dataset_id: str):
        return {
            "total_spend": 10000.0,
            "total_revenue": 35000.0,
            "overall_roas": 3.5,
            "avg_conversion_rate": 0.045,
            "avg_cpa": 22.50,
        }