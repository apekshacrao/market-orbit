from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from app.db.base import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    row_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
