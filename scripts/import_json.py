"""Import a private saved organizer payload through the same validated parser as the API."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import Settings
from backend.app.db import Database
from backend.app.domain import ImportEnvelope
from backend.app.services.importer import import_payload
from pydantic import ValidationError

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    settings = Settings.from_env()
    db = Database(settings.database_path)
    try:
        envelope = ImportEnvelope.model_validate_json(args.path.read_bytes())
        result = import_payload(db, envelope)
        print(json.dumps({k: v for k, v in result.items() if k != "conversation_ids"}, ensure_ascii=False, indent=2))
    except ValidationError as error:
        print(json.dumps({"invalid_payload": [{"location": e["loc"], "message": e["msg"]} for e in error.errors()]}, ensure_ascii=False))
        raise SystemExit(1)
    finally:
        db.engine.dispose()
