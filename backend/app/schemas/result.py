from typing import Dict, Any, List, Optional

from pydantic import BaseModel


class KpiResponse(BaseModel):
    total_spend: float
    total_conversions: Optional[int] = 0
    total_clicks: Optional[int] = 0
    total_impressions: Optional[int] = 0
    total_revenue: Optional[float] = None

    cpa: Optional[float] = None
    cpc: Optional[float] = None
    conversion_rate: Optional[float] = None
    ctr: Optional[float] = None
    roas: Optional[float] = None
    roi: Optional[float] = None

    # Backward-compatible aliases
    avg_cpa: Optional[float] = None
    avg_cpc: Optional[float] = None
    avg_conversion_rate: Optional[float] = None
    overall_roas: Optional[float] = None


class AnalysisResultResponse(BaseModel):
    dataset_id: str
    kpis: Dict[str, Any]
    rankings: Dict[str, Any]
    trends: Dict[str, Any]
    ai_recommendations: List[Dict[str, Any]]