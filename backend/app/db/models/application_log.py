from sqlalchemy import Column, String, DateTime, Text, func
from app.db.base import Base


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    id = Column(String, primary_key=True, index=True)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    context = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )