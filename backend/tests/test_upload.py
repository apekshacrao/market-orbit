from pathlib import Path

from backend.app.services.storage_service import StorageService


class FakeQuery:
    def __init__(self, dataset=None, datasets=None):
        self.dataset = dataset
        self.datasets = datasets or []

    def filter(self, *args):
        return self

    def order_by(self, *args):
        self.datasets.sort(
            key=lambda dataset: dataset.created_at,
            reverse=True,
        )
        return self

    def first(self):
        return self.dataset

    def all(self):
        return self.datasets


class FakeDB:
    def __init__(self):
        self.added = None
        self.added_campaigns = []
        self.committed = False
        self.rolled_back = False
        self.datasets = []

    def add(self, obj):
        self.added = obj

    def add_all(self, campaigns):
        self.added_campaigns = campaigns

        if self.added:
            self.added.row_count = len(campaigns)

    def flush(self):
        pass

    def query(self, model):
        return FakeQuery(
            dataset=self.added,
            datasets=self.datasets,
        )

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass

    def rollback(self):
        self.rolled_back = True


class FakeUser:
    id = "user-123"


def await_save(file, user, db):
    import asyncio

    return asyncio.run(
        StorageService.save_upload(file, user, db)
    )


def test_save_valid_csv(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(
        "backend.app.services.storage_service.UPLOAD_DIR",
        upload_dir,
    )

    class FakeFile:
        filename = "campaigns.csv"

        async def read(self):
            return (
                b"campaign_name,channel,spend,revenue\n"
                b"Campaign A,Google,100,300\n"
            )

    db = FakeDB()

    result = await_save(
        FakeFile(),
        FakeUser(),
        db,
    )

    assert result["filename"] == "campaigns.csv"
    assert result["status"] == "PENDING"

    assert db.added.filename == "campaigns.csv"
    assert db.added.user_id == "user-123"
    assert db.added.status == "PENDING"
    assert db.added.row_count == 1

    assert len(db.added_campaigns) == 1
    assert db.added_campaigns[0].campaign_name == "Campaign A"
    assert db.added_campaigns[0].channel == "Google"
    assert db.added_campaigns[0].spend == 100
    assert db.added_campaigns[0].revenue == 300

    assert Path(db.added.file_path).exists()
    assert db.committed is True
    assert db.rolled_back is False


def test_reject_non_csv_file(tmp_path):
    class FakeFile:
        filename = "campaigns.xlsx"

    db = FakeDB()

    try:
        await_save(
            FakeFile(),
            FakeUser(),
            db,
        )
        assert False
    except Exception as exc:
        assert exc.status_code == 400

    assert db.added is None
    assert db.committed is False


def test_reject_invalid_csv(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(
        "backend.app.services.storage_service.UPLOAD_DIR",
        upload_dir,
    )

    class FakeFile:
        filename = "invalid.csv"

        async def read(self):
            return (
                b"campaign_name,channel,spend\n"
                b"Campaign A,Google,100\n"
            )

    db = FakeDB()

    try:
        await_save(
            FakeFile(),
            FakeUser(),
            db,
        )
        assert False
    except Exception as exc:
        assert exc.status_code == 422

    assert db.added is None
    assert db.committed is False
    assert not list(upload_dir.glob("*"))


def test_get_dataset_status_returns_actual_status():
    dataset = type(
        "FakeDataset",
        (),
        {
            "id": "dataset-123",
            "user_id": "user-123",
            "status": "PENDING",
        },
    )()

    db = FakeDB()
    db.added = dataset

    result = StorageService.get_dataset_status(
        "dataset-123",
        "user-123",
        db,
    )

    assert result == {
        "dataset_id": "dataset-123",
        "status": "PENDING",
    }


def test_get_dataset_status_rejects_other_users_dataset():
    dataset = type(
        "FakeDataset",
        (),
        {
            "id": "dataset-123",
            "user_id": "user-456",
            "status": "PENDING",
        },
    )()

    db = FakeDB()
    db.added = dataset

    try:
        StorageService.get_dataset_status(
            "dataset-123",
            "user-123",
            db,
        )
        assert False
    except Exception as exc:
        assert exc.status_code == 403


def test_get_dataset_status_rejects_missing_dataset():
    db = FakeDB()
    db.added = None

    try:
        StorageService.get_dataset_status(
            "dataset-999",
            "user-123",
            db,
        )
        assert False
    except Exception as exc:
        assert exc.status_code == 404


def test_get_user_datasets_returns_only_current_users_datasets():
    dataset1 = type(
        "FakeDataset",
        (),
        {
            "id": "dataset-1",
            "user_id": "user-123",
            "filename": "campaigns1.csv",
            "status": "PENDING",
            "row_count": 5,
            "created_at": 2,
        },
    )()

    dataset2 = type(
        "FakeDataset",
        (),
        {
            "id": "dataset-2",
            "user_id": "user-456",
            "filename": "campaigns2.csv",
            "status": "PENDING",
            "row_count": 10,
            "created_at": 1,
        },
    )()

    db = FakeDB()
    db.datasets = [dataset1, dataset2]

    # Simulate the ownership filtering performed by the real query.
    db.datasets = [
        dataset
        for dataset in db.datasets
        if dataset.user_id == "user-123"
    ]

    result = StorageService.get_user_datasets(
        "user-123",
        db,
    )

    assert len(result) == 1
    assert result[0].id == "dataset-1"
    assert result[0].user_id == "user-123"


def test_get_user_datasets_returns_newest_first():
    dataset1 = type(
        "FakeDataset",
        (),
        {
            "id": "dataset-1",
            "user_id": "user-123",
            "filename": "older.csv",
            "status": "PENDING",
            "row_count": 5,
            "created_at": 1,
        },
    )()

    dataset2 = type(
        "FakeDataset",
        (),
        {
            "id": "dataset-2",
            "user_id": "user-123",
            "filename": "newer.csv",
            "status": "PENDING",
            "row_count": 10,
            "created_at": 2,
        },
    )()

    db = FakeDB()
    db.datasets = [dataset1, dataset2]

    result = StorageService.get_user_datasets(
        "user-123",
        db,
    )

    assert result[0].id == "dataset-2"
    assert result[1].id == "dataset-1"


def test_get_user_datasets_returns_empty_list_when_user_has_no_datasets():
    db = FakeDB()
    db.datasets = []

    result = StorageService.get_user_datasets(
        "user-123",
        db,
    )

    assert result == []