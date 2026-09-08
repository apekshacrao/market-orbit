from pathlib import Path

from backend.app.services.storage_service import StorageService


class FakeQuery:
    def __init__(self, dataset):
        self.dataset = dataset

    def filter(self, *args):
        return self

    def first(self):
        return self.dataset


class FakeDB:
    def __init__(self):
        self.added = None
        self.added_campaigns = []
        self.committed = False
        self.rolled_back = False

    def add(self, obj):
        self.added = obj

    def add_all(self, campaigns):
        self.added_campaigns = campaigns

        if self.added:
            self.added.row_count = len(campaigns)

    def flush(self):
        pass

    def query(self, model):
        return FakeQuery(self.added)

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