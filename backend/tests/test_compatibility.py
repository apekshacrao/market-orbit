import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from fastapi import HTTPException

try:
    from app.services.campaign_service import CampaignService
    from app.services.analysis_service import AnalysisService
except ImportError:
    from backend.app.services.campaign_service import CampaignService
    from backend.app.services.analysis_service import AnalysisService

from analytics.schemas.campaign_schema import CampaignInputRecord
from analytics.preprocessing.validators import validate_dataset
from analytics.preprocessing.cleaner import clean_dataset
from analytics.kpi.metrics import calculate_kpis


class FakeQuery:
    def __init__(self, data):
        self.data = data

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return self.data if not isinstance(self.data, list) else (self.data[0] if self.data else None)

    def all(self):
        return self.data if isinstance(self.data, list) else [self.data]


class FakeDB:
    def __init__(self, dataset, campaigns=None):
        self.dataset = dataset
        self.campaigns = campaigns or []
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, items):
        self.added.extend(items)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "Dataset":
            return FakeQuery(self.dataset)
        elif name == "AnalysisResult":
            return FakeQuery(None)
        elif name == "Campaign":
            return FakeQuery(self.campaigns)
        return FakeQuery(None)


def test_end_to_end_compatibility_with_sqlalchemy_date(tmp_path):
    """Verifies that campaigns imported by CampaignService and mapped by AnalysisService
    are fully compatible with CampaignInputRecord, clean_dataset, and calculate_kpis."""
    csv_file = tmp_path / "campaigns.csv"
    csv_file.write_text(
        "campaign_name,channel,impressions,clicks,spend,conversions,revenue,date,location,age_group,customer_segment,device\n"
        "Alpha Campaign,Google,10000,500,1000.0,50,3000.0,2026-09-18,Bengaluru,18-24,Tech,Mobile\n"
        "Beta Campaign,Meta,5000,200,500.0,20,,2026-09-19,Mumbai,25-34,Finance,Desktop\n",
        encoding="utf-8",
    )

    dataset = SimpleNamespace(id="ds-1", user_id="user-1", row_count=0)
    db = FakeDB(dataset)

    # 1. Ingest via CampaignService
    campaigns = CampaignService.import_campaigns(str(csv_file), dataset.id, db)
    assert len(campaigns) == 2
    assert isinstance(campaigns[0].date, datetime.date)
    assert campaigns[0].revenue == Decimal("3000.0")
    assert campaigns[1].revenue is None

    # 2. Map via AnalysisService
    db.campaigns = campaigns
    captured = {}

    def capture_clean_dataset(data):
        captured["data"] = data
        return clean_dataset(data)

    with patch("app.services.analysis_service.clean_dataset", side_effect=capture_clean_dataset):
        results = AnalysisService.get_results("ds-1", "user-1", db)

    mapped_rows = captured["data"]
    assert len(mapped_rows) == 2

    # Date must be serialized string YYYY-MM-DD
    assert mapped_rows[0]["date"] == "2026-09-18"
    assert isinstance(mapped_rows[0]["date"], str)
    assert mapped_rows[1]["date"] == "2026-09-19"
    assert isinstance(mapped_rows[1]["date"], str)

    # 3. Compatible with CampaignInputRecord
    record1 = CampaignInputRecord(**mapped_rows[0])
    assert record1.date == "2026-09-18"
    assert record1.revenue == 3000.0

    record2 = CampaignInputRecord(**mapped_rows[1])
    assert record2.date == "2026-09-19"
    assert record2.revenue is None

    # 4. Compatible with validate_dataset
    val_res = validate_dataset(mapped_rows)
    assert val_res["is_valid"] is True

    # 5. Compatible with calculate_kpis
    kpis = results["kpis"]
    assert kpis["total_spend"] == 1500.0
    assert kpis["total_conversions"] == 70
    assert kpis["total_revenue"] == 3000.0
    assert kpis["roas"] == 2.0


def test_missing_revenue_kpi_compatibility(tmp_path):
    """Verifies that missing revenue yields None for total_revenue, roas, and roi."""
    csv_file = tmp_path / "no_rev.csv"
    csv_file.write_text(
        "campaign_name,channel,impressions,clicks,spend,conversions\n"
        "Lead Gen,LinkedIn,2000,80,400.0,15\n",
        encoding="utf-8",
    )

    dataset = SimpleNamespace(id="ds-2", user_id="user-1", row_count=0)
    db = FakeDB(dataset)

    campaigns = CampaignService.import_campaigns(str(csv_file), dataset.id, db)
    db.campaigns = campaigns

    results = AnalysisService.get_results("ds-2", "user-1", db)
    kpis = results["kpis"]

    assert kpis["total_spend"] == 400.0
    assert kpis["total_revenue"] is None
    assert kpis["roas"] is None
    assert kpis["roi"] is None


def test_explicit_zero_revenue_kpi_compatibility(tmp_path):
    """Verifies that explicit zero revenue yields 0.0 for total_revenue, 0.0 for roas, and -100.0 for roi."""
    csv_file = tmp_path / "zero_rev.csv"
    csv_file.write_text(
        "campaign_name,channel,impressions,clicks,spend,conversions,revenue\n"
        "Zero Rev,Meta,1000,50,200.0,5,0.0\n",
        encoding="utf-8",
    )

    dataset = SimpleNamespace(id="ds-3", user_id="user-1", row_count=0)
    db = FakeDB(dataset)

    campaigns = CampaignService.import_campaigns(str(csv_file), dataset.id, db)
    db.campaigns = campaigns

    results = AnalysisService.get_results("ds-3", "user-1", db)
    kpis = results["kpis"]

    assert kpis["total_spend"] == 200.0
    assert kpis["total_revenue"] == 0.0
    assert kpis["roas"] == 0.0
    assert kpis["roi"] == -100.0
