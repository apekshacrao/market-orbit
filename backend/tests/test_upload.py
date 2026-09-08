from pathlib import Path

from backend.app.services.storage_service import StorageService


class FakeDB:
    def __init__(self):
        self.added = None
        self.committed = False

    def add(self, obj):
        self.added = obj

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass


class FakeUser:
    id = "user-123"


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

    result = await_save(FakeFile(), FakeUser(), db)

    assert result["filename"] == "campaigns.csv"
    assert result["status"] == "PENDING"
    assert db.added.filename == "campaigns.csv"
    assert db.added.user_id == "user-123"
    assert db.added.status == "PENDING"
    assert db.added.row_count == 0
    assert Path(db.added.file_path).exists()
    assert db.committed is True


def test_reject_non_csv_file(tmp_path):
    class FakeFile:
        filename = "campaigns.xlsx"

    db = FakeDB()

    try:
        await_save(FakeFile(), FakeUser(), db)
        assert False
    except Exception as exc:
        assert exc.status_code == 400


def await_save(file, user, db):
    import asyncio

    return asyncio.run(
        StorageService.save_upload(file, user, db)
    )

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
        await_save(FakeFile(), FakeUser(), db)
        assert False
    except Exception as exc:
        assert exc.status_code == 422

    assert db.added is None
    assert db.committed is False
    assert not list(upload_dir.glob("*"))