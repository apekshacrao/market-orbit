from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from app.db.base import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    kpis = Column(JSON, nullable=True)
    rankings = Column(JSON, nullable=True)
    trends = Column(JSON, nullable=True)
    ai_recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
