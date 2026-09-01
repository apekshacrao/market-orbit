from typing import Dict, Any, List
from pydantic import BaseModel

class AnalyticsOutput(BaseModel):
    kpis: Dict[str, Any]
    rankings: Dict[str, Any]
    trends: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
