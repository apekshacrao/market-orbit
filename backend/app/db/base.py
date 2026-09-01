from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for Alembic/metadata discovery
from app.db.models.user import User  # noqa: F401
from app.db.models.dataset import Dataset  # noqa: F401
from app.db.models.campaign import Campaign  # noqa: F401
from app.db.models.analysis_result import AnalysisResult  # noqa: F401
from app.db.models.application_log import ApplicationLog  # noqa: F401
