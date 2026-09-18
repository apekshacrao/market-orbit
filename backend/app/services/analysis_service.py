from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.db.models.campaign import Campaign
from app.db.models.analysis_result import AnalysisResult

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
        # Check whether dataset exists
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

        # Check dataset ownership
        if dataset.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this dataset",
            )

        # Return existing analysis result if already generated
        existing_result = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.dataset_id == dataset_id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )

        if existing_result:
            return {
                "dataset_id": dataset_id,
                "kpis": existing_result.kpis or {},
                "rankings": existing_result.rankings or {},
                "trends": existing_result.trends or {},
                "ai_recommendations": (
                    existing_result.ai_recommendations or []
                ),
            }

        # Fetch campaigns belonging to the dataset
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.dataset_id == dataset_id)
            .order_by(Campaign.created_at.asc())
            .all()
        )

        # Convert database records into analytics input
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
                "date": campaign.date,
                "location": campaign.location,
                "age_group": campaign.age_group,
                "customer_segment": campaign.customer_segment,
                "device": campaign.device,
            }
            for campaign in campaigns
        ]

        # Clean and prepare data
        df = clean_dataset(campaign_data)

        # Calculate analytics
        kpis = calculate_kpis(df)
        rankings = rank_campaigns(df)
        trends = analyze_trends(df)

        # Generate recommendations
        groq_client = GroqClient()

        recommendations = groq_client.generate_recommendations(
            kpis,
            rankings,
        )

        # Store analysis result
        analysis_result = AnalysisResult(
            id=str(uuid4()),
            dataset_id=dataset_id,
            kpis=kpis,
            rankings=rankings,
            trends=trends,
            ai_recommendations=recommendations,
        )

        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)

        # Return complete analysis
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