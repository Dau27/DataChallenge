"""Rebuild derived search data without evaluating or changing source/results."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db import Database
from backend.app.services.transcript_index import ensure_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    args = parser.parse_args()
    path = args.database.resolve()
    if not path.is_file():
        raise SystemExit('Existing database not found; no empty replacement was created.')
    db = Database(path)
    try:
        print(json.dumps(ensure_index(db.engine, force=True)))
    finally:
        db.engine.dispose()


if __name__ == '__main__':
    main()
