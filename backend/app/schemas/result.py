from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class KpiResponse(BaseModel):
    totalSpend: float
    totalRevenue: Optional[float] = None
    overallRoas: Optional[float] = None
    avgConversionRate: Optional[float] = None
    avgCpa: Optional[float] = None


class CampaignPerformanceResponse(BaseModel):
    campaignName: str
    spend: float
    revenue: Optional[float] = None
    roas: Optional[float] = None


class TrendResponse(BaseModel):
    date: str
    spend: float
    revenue: Optional[float] = None
    conversions: int


class AnalysisResultResponse(BaseModel):
    dataset_id: str
    kpis: KpiResponse
    performance: List[CampaignPerformanceResponse]
    topCampaigns: List[CampaignPerformanceResponse]
    bottomCampaigns: List[CampaignPerformanceResponse]
    trends: List[TrendResponse]
    recommendations: List[Dict[str, Any]]
    segmentation: Optional[Dict[str, Any]] = None
    forecasting: Optional[Dict[str, Any]] = None
