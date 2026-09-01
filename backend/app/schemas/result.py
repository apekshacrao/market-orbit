from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class KpiResponse(BaseModel):
    total_spend: float
    total_revenue: float
    overall_roas: float
    avg_conversion_rate: float
    avg_cpa: float

class AnalysisResultResponse(BaseModel):
    dataset_id: str
    kpis: Dict[str, Any]
    rankings: Dict[str, Any]
    trends: Dict[str, Any]
    ai_recommendations: List[Dict[str, Any]]
