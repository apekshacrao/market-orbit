try:
    from app.services.campaign_service import CampaignService
except ImportError:
    from backend.app.services.campaign_service import CampaignService


class FakeQuery:
    def __init__(self, dataset):
        self.dataset = dataset

    def filter(self, *args):
        return self

    def first(self):
        return self.dataset


class FakeDB:
    def __init__(self, dataset):
        self.dataset = dataset
        self.added_campaigns = []
        self.committed = False

    def add_all(self, campaigns):
        self.added_campaigns = campaigns

    def query(self, model):
        return FakeQuery(self.dataset)


class FakeDataset:
    def __init__(self):
        self.id = "dataset-123"
        self.row_count = 0


def test_import_campaigns(tmp_path):
    csv_file = tmp_path / "campaigns.csv"

    csv_file.write_text(
        "campaign_name,channel,impressions,clicks,spend,conversions,revenue\n"
        "Summer Sale,Google,10000,500,1000,50,3500\n"
        "Winter Sale,Meta,8000,400,800,35,2500\n",
        encoding="utf-8",
    )

    dataset = FakeDataset()
    db = FakeDB(dataset)

    result = CampaignService.import_campaigns(
        str(csv_file),
        "dataset-123",
        db,
    )

    assert len(result) == 2
    assert len(db.added_campaigns) == 2
    assert dataset.row_count == 2

    assert result[0].campaign_name == "Summer Sale"
    assert result[0].channel == "Google"
    assert result[0].impressions == 10000
    assert result[0].clicks == 500
    assert result[0].spend == 1000
    assert result[0].conversions == 50
    assert result[0].revenue == 3500
    assert result[0].dataset_id == "dataset-123"


def test_import_campaigns_with_optional_columns(tmp_path):
    csv_file = tmp_path / "campaigns.csv"

    csv_file.write_text(
        "campaign_name,channel,impressions,clicks,spend,conversions,"
        "revenue,date,location,age_group,customer_segment,device\n"
        "Summer Sale,Google,10000,500,1000,50,3500,"
        "2026-09-18,Bengaluru,18-24,New Customers,Mobile\n",
        encoding="utf-8",
    )

    dataset = FakeDataset()
    db = FakeDB(dataset)

    result = CampaignService.import_campaigns(
        str(csv_file),
        "dataset-123",
        db,
    )

    assert len(result) == 1

    campaign = result[0]

    assert campaign.date.year == 2026
    assert campaign.date.month == 9
    assert campaign.date.day == 18

    assert campaign.location == "Bengaluru"
    assert campaign.age_group == "18-24"
    assert campaign.customer_segment == "New Customers"
    assert campaign.device == "Mobile"


def test_import_campaigns_with_optional_columns_missing(tmp_path):
    csv_file = tmp_path / "campaigns.csv"

    csv_file.write_text(
        "campaign_name,channel,spend\n"
        "Summer Sale,Google,1000\n",
        encoding="utf-8",
    )

    dataset = FakeDataset()
    db = FakeDB(dataset)

    result = CampaignService.import_campaigns(
        str(csv_file),
        "dataset-123",
        db,
    )

    assert len(result) == 1

    assert result[0].impressions == 0
    assert result[0].clicks == 0
    assert result[0].conversions == 0

    assert result[0].revenue is None
    assert result[0].date is None
    assert result[0].location is None
    assert result[0].age_group is None
    assert result[0].customer_segment is None
    assert result[0].device is None

    assert dataset.row_count == 1


def test_import_campaigns_file_not_found():
    dataset = FakeDataset()
    db = FakeDB(dataset)

    try:
        CampaignService.import_campaigns(
            "does-not-exist.csv",
            "dataset-123",
            db,
        )
        assert False
    except Exception as exc:
        assert exc.status_code == 404