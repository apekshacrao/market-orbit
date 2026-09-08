from types import SimpleNamespace

from app.services.storage_service import StorageService


class FakeDB:
    def __init__(self):
        self.added = None
        self.committed = False
        self.refreshed = None

    def add(self, obj):
        self.added = obj

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed = obj


def test_upload_creates_dataset():
    db = FakeDB()

    file = SimpleNamespace(
        filename="campaigns.csv"
    )

    user = SimpleNamespace(
        id="user-1"
    )

    result = __import__("asyncio").run(
        StorageService.save_upload(
            file,
            user,
            db,
        )
    )

    assert result["filename"] == "campaigns.csv"
    assert result["status"] == "PENDING"
    assert result["message"] == "File uploaded successfully"

    assert db.added is not None
    assert db.added.user_id == "user-1"
    assert db.added.filename == "campaigns.csv"
    assert db.added.status == "PENDING"
    assert db.added.row_count == 0

    assert db.committed is True
    assert db.refreshed is db.added