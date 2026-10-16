from uuid import uuid4
from collections import defaultdict
from datetime import date as date_type

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.db.models.campaign import Campaign
from app.db.models.analysis_result import AnalysisResult

from typing import Optional

from analytics.preprocessing.cleaner import clean_dataset
from analytics.kpi.metrics import calculate_kpis
from analytics.performance.ranking import rank_campaigns
from analytics.trends.customer_trends import analyze_trends
from analytics.segmentation.cohorts import classify_campaign_cohorts
from analytics.segmentation.portfolio import profile_segment_portfolio
from analytics.forecasting.service import run_forecasting_analysis
from analytics.ai.service import RecommendationService


class AnalysisService:

    @staticmethod
    def _contract_response(
        dataset_id,
        kpis,
        rankings,
        campaign_data,
        recommendations,
        segmentation=None,
        forecasting=None,
    ):
        """Adapt stored or freshly calculated analytics to the frontend contract."""
        def complete_revenue(rows):
            if not rows or any(row.get("revenue") is None for row in rows):
                return None
            return round(sum(float(row["revenue"]) for row in rows), 2)

        by_campaign = defaultdict(list)
        by_date = defaultdict(list)
        for row in campaign_data:
            by_campaign[row["campaign_name"]].append(row)
            if row.get("date"):
                try:
                    date_type.fromisoformat(row["date"])
                except (TypeError, ValueError):
                    continue
                by_date[row["date"]].append(row)

        ranking_roas = {
            item.get("campaign_name"): item.get("roas")
            for item in rankings.get("top", []) + rankings.get("bottom", [])
            if isinstance(item, dict)
        }

        def campaign_shape(item):
            name = item.get("campaign_name", item.get("campaignName"))
            rows = by_campaign.get(name, [])
            revenue = complete_revenue(rows) if rows else item.get("revenue")
            return {
                "campaignName": name,
                "spend": item.get("spend"),
                "revenue": revenue,
                "roas": (
                    item.get("roas", ranking_roas.get(name))
                    if revenue is not None
                    else None
                ),
            }

        performance = []
        for name, rows in by_campaign.items():
            spend = round(sum(float(row.get("spend") or 0) for row in rows), 2)
            revenue = complete_revenue(rows)
            performance.append({
                "campaignName": name,
                "spend": spend,
                "revenue": revenue,
                "roas": round(revenue / spend, 2) if revenue is not None and spend > 0 else None,
            })

        trends = []
        for date in sorted(by_date):
            rows = by_date[date]
            trends.append({
                "date": date,
                "spend": round(sum(float(row.get("spend") or 0) for row in rows), 2),
                "revenue": complete_revenue(rows),
                "conversions": sum(int(row.get("conversions") or 0) for row in rows),
            })

        return {
            "dataset_id": dataset_id,
            "kpis": {
                "totalSpend": kpis.get("total_spend", 0),
                "totalRevenue": kpis.get("total_revenue"),
                "overallRoas": kpis.get("overall_roas", kpis.get("roas")),
                "avgConversionRate": kpis.get("avg_conversion_rate", kpis.get("conversion_rate")),
                "avgCpa": kpis.get("avg_cpa", kpis.get("cpa")),
            },
            "performance": performance,
            "topCampaigns": [campaign_shape(item) for item in rankings.get("top", [])],
            "bottomCampaigns": [campaign_shape(item) for item in rankings.get("bottom", [])],
            "trends": trends,
            "recommendations": recommendations or [],
            "segmentation": segmentation,
            "forecasting": forecasting,
        }

    @staticmethod
    def _campaign_data(campaigns):
        return [
            {
                "campaign_name": campaign.campaign_name,
                "channel": campaign.channel,
                "impressions": campaign.impressions,
                "clicks": campaign.clicks,
                "spend": float(campaign.spend or 0),
                "conversions": campaign.conversions,
                "revenue": float(campaign.revenue) if campaign.revenue is not None else None,
                "date": (
                    campaign.date.isoformat()
                    if hasattr(campaign.date, "isoformat")
                    else str(campaign.date) if campaign.date else None
                ),
                "location": campaign.location,
                "age_group": campaign.age_group,
                "customer_segment": campaign.customer_segment,
                "device": campaign.device,
            }
            for campaign in campaigns
        ]

    @staticmethod
    def get_results(
        dataset_id: str,
        current_user_id: str,
        db: Session,
        recommendation_service: Optional[RecommendationService] = None,
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
            campaigns = db.query(Campaign).filter(
                Campaign.dataset_id == dataset_id
            ).order_by(Campaign.created_at.asc()).all()
            campaign_data = AnalysisService._campaign_data(campaigns)
            stored_trends = existing_result.trends
            if stored_trends is None:
                stored_trends = {}
            elif not isinstance(stored_trends, dict):
                raise TypeError("Stored analysis trends must be a JSON object")
            else:
                stored_trends = dict(stored_trends)

            segmentation = stored_trends.get("segmentation")
            forecasting = stored_trends.get("forecasting")
            if segmentation is None or forecasting is None:
                df = clean_dataset(campaign_data)
                if segmentation is None:
                    segmentation = {
                        "cohorts": classify_campaign_cohorts(df),
                        "segment_portfolio": profile_segment_portfolio(df),
                    }
                    stored_trends["segmentation"] = segmentation
                if forecasting is None:
                    forecasting = run_forecasting_analysis(df)
                    stored_trends["forecasting"] = forecasting

                # Assign a fresh object so SQLAlchemy detects the JSONB update.
                existing_result.trends = stored_trends
                try:
                    db.commit()
                    db.refresh(existing_result)
                except Exception:
                    db.rollback()
                    raise

            return AnalysisService._contract_response(
                dataset_id,
                existing_result.kpis or {},
                existing_result.rankings or {},
                campaign_data,
                existing_result.ai_recommendations or [],
                segmentation,
                forecasting,
            )

        # Fetch campaigns belonging to the dataset
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.dataset_id == dataset_id)
            .order_by(Campaign.created_at.asc())
            .all()
        )

        # Convert database records into analytics input
        campaign_data = AnalysisService._campaign_data(campaigns)

        # Clean and prepare data
        df = clean_dataset(campaign_data)

        # Calculate analytics
        kpis = calculate_kpis(df)
        rankings = rank_campaigns(df)
        trends = analyze_trends(df)
        segmentation = {
            "cohorts": classify_campaign_cohorts(df),
            "segment_portfolio": profile_segment_portfolio(df),
        }
        forecasting = run_forecasting_analysis(df)

        # Generate recommendations using unified RecommendationService
        service = recommendation_service or RecommendationService()
        recommendations = service.get_recommendation_list(
            kpis=kpis,
            rankings=rankings,
            trends=trends,
            df=df,
            dataset_id=dataset_id,
        )

        # Store analysis result
        persisted_trends = {
            **trends,
            "segmentation": segmentation,
            "forecasting": forecasting,
        }
        analysis_result = AnalysisResult(
            id=str(uuid4()),
            dataset_id=dataset_id,
            kpis=kpis,
            rankings=rankings,
            trends=persisted_trends,
            ai_recommendations=recommendations,
        )

        try:
            db.add(analysis_result)
            db.commit()
            db.refresh(analysis_result)
        except Exception:
            db.rollback()
            raise

        return AnalysisService._contract_response(
            dataset_id,
            kpis,
            rankings,
            campaign_data,
            recommendations,
            segmentation,
            forecasting,
        )

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
