"""Read-only local access report. Never prints credentials or private endpoints."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import Settings

if __name__ == "__main__":
    settings = Settings.from_env()
    print(json.dumps({**settings.public_access(), "database_exists": settings.database_path.exists()}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if settings.provider_ready else 1)
