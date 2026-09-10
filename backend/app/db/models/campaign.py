from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, func
from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(
        String,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False
    )
    campaign_name = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(12, 2), default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Numeric(12, 2), default=0)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )