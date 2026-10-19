import sys
from pathlib import Path
import pytest

root_dir = str(Path(__file__).resolve().parents[2])
backend_dir = str(Path(__file__).resolve().parents[1])

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings


@pytest.fixture(autouse=True)
def offline_groq_for_backend_tests(monkeypatch):
    """
    Ensure backend tests never make live Groq API calls unless explicitly configured.
    Isolates tests from developer's local .env file.
    """
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr("dotenv.dotenv_values", lambda p: {})
