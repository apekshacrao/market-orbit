from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.db.models.campaign import Campaign

from analytics.preprocessing.cleaner import clean_dataset
from analytics.kpi.metrics import calculate_kpis

from analytics.performance.ranking import rank_campaigns
from analytics.trends.customer_trends import analyze_trends
from analytics.ai.groq_client import GroqClient

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

        campaigns = (
            db.query(Campaign)
            .filter(Campaign.dataset_id == dataset_id)
            .order_by(Campaign.created_at.asc())
            .all()
        )

        campaign_data = [
            {
                "campaign_name": campaign.campaign_name,
                "channel": campaign.channel,
                "impressions": campaign.impressions,
                "clicks": campaign.clicks,
                "spend": float(campaign.spend or 0),
                "conversions": campaign.conversions,
                "revenue": (
                    float(campaign.revenue)
                    if campaign.revenue is not None
                    else None
                ),
            }
            for campaign in campaigns
        ]

        df = clean_dataset(campaign_data)
        kpis = calculate_kpis(df)
        rankings = rank_campaigns(df)
        trends = analyze_trends(df)

        groq_client = GroqClient()
        recommendations = groq_client.generate_recommendations(
            kpis,
            rankings,
        )

        return {
            "dataset_id": dataset_id,
            "kpis": kpis,
            "rankings": rankings,
            "trends": trends,
            "ai_recommendations": recommendations,
        }
    @staticmethod
    def get_kpis(
        dataset_id: str,
        current_user_id: str,
        db: Session,
    ):
        result = AnalysisService.get_results(
            dataset_id,
            current_user_id,
            db,
        )

        return result["kpis"]