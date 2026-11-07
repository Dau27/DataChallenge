"""Select private diagnostic DEV examples. Selection is not human review or labeling."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import Settings
from backend.app.db import Conversation, Database
from sqlalchemy import select


if __name__ == "__main__":
    db = Database(Settings.from_env().database_path)
    with db.sessions() as session:
        records = list(session.scalars(select(Conversation).where(Conversation.group_id == "DEV").order_by(Conversation.source_id, Conversation.revision.desc())))
        latest = {}
        for row in records:
            latest.setdefault(row.source_id, row)
        selected = []
        for language in ["RU", "KZ", "EN"]:
            group = [row for row in latest.values() if row.snapshot["language"] == language]
            calls = [row for row in group if row.snapshot["channel"] == "voice call"]
            chats = [row for row in group if row.snapshot["channel"] == "agent chat"]
            development = calls[:1]
            development += chats[:3 - len(development)]
            development += [row for row in group if row not in development][:3 - len(development)]
            remaining = [row for row in group if row not in development]
            holdout = [row for row in remaining if row.snapshot["channel"] == "voice call"][:1]
            holdout += [row for row in remaining if row not in holdout][:2 - len(holdout)]
            for split, rows in [("development", development), ("holdout", holdout)]:
                selected.extend({"source_id": row.source_id, "conversation_revision_id": row.id, "language": language,
                                 "channel": row.snapshot["channel"], "split": split, "human_reviewed": False, "labels": None} for row in rows)
    report = {"purpose": "Small diagnostic selection, not a statistical benchmark", "records": selected}
    output = Settings.from_env().database_path.parent / "reference_selection.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"selected": len(selected), "development": sum(r["split"] == "development" for r in selected),
                      "holdout": sum(r["split"] == "holdout" for r in selected), "calls": sum(r["channel"] == "voice call" for r in selected),
                      "human_reviewed": False}))
    db.engine.dispose()
