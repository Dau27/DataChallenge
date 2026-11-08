"""Private SQLite recovery bundles. Never constructs the app or contacts a provider."""
from contextlib import closing, contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

from pydantic import ValidationError

from backend.app.domain import Assessment, Checklist, content_hash, validate_assessment
from backend.app.services.search import folded
from backend.app.services.transcript_index import INDEX_VERSION


FORMAT_VERSION = 1
DATABASE_FILE = "database.sqlite3"
MANIFEST_FILE = "manifest.json"
DEFAULT_DATABASE = Path(__file__).resolve().parents[3] / "local_data/cqa.sqlite3"
REQUIRED = {
    "conversation_revisions": {"id", "group_id", "source_id", "content_hash", "snapshot"},
    "checklist_versions": {"id", "content_hash", "snapshot"},
    "evaluations": {"id", "conversation_id", "checklist_id", "original", "effective", "original_score", "effective_score"},
    "appeals": {"id", "evaluation_id", "criterion_id"},
    "review_decisions": {"id", "appeal_id", "evaluation_id", "criterion_id", "judgment", "resulting_score"},
}


class BackupError(ValueError):
    """A safe diagnostic without database contents, SQL or secret configuration."""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _quoted(name):
    return '"' + name.replace('"', '""') + '"'


def _exists(path):
    # Includes dangling symlinks, directories and other non-regular entries.
    return os.path.lexists(path)


@contextmanager
def _readonly(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise BackupError("Database must be an existing regular file")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=30)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        yield db
    finally:
        db.close()


def _fingerprint(db):
    tables = {}
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        rows = [_json([{"blob_hex": v.hex()} if isinstance(v, bytes) else v for v in row])
                for row in db.execute("SELECT * FROM " + _quoted(name))]
        tables[name] = {"rows": len(rows), "sha256": hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()}
    schema = [tuple(row) for row in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")]
    return {"tables": tables, "schema_sha256": hashlib.sha256(_json(schema).encode()).hexdigest()}


def _identities(db):
    sources = {}
    for row in db.execute("SELECT * FROM conversation_revisions"):
        snapshot = json.loads(row["snapshot"])
        original = deepcopy(snapshot)
        original["transcript"] = [{k: v for k, v in m.items() if k != "id"} for m in original["transcript"]]
        ids = [m["id"] for m in snapshot["transcript"]]
        if (content_hash({"group_id": row["group_id"], **original}) != row["content_hash"]
                or snapshot["conversation_id"] != row["source_id"] or len(ids) != len(set(ids))):
            raise BackupError("Source identity verification failed")
        sources[row["id"]] = (snapshot, row["content_hash"])
    checklists = {}
    unsupported_checklists = 0
    for row in db.execute("SELECT * FROM checklist_versions"):
        snapshot = json.loads(row["snapshot"])
        if content_hash(snapshot) != row["content_hash"]:
            raise BackupError("Checklist identity verification failed")
        try:
            checklists[row["id"]] = Checklist.model_validate(snapshot)
        except ValidationError:
            checklists[row["id"]] = None
            unsupported_checklists += 1
    appeals = {r["id"]: r for r in db.execute("SELECT * FROM appeals")}
    reviews = {}
    for row in db.execute("SELECT * FROM review_decisions ORDER BY id"):
        appeal = appeals.get(row["appeal_id"])
        if appeal is None or any(appeal[k] != row[k] for k in ("evaluation_id", "criterion_id")):
            raise BackupError("Review/appeal identity verification failed")
        reviews.setdefault(row["evaluation_id"], []).append(row)
    replayed = unsupported_assessments = 0
    for row in db.execute("SELECT * FROM evaluations"):
        history = reviews.get(row["id"], [])
        original = json.loads(row["original"]) if row["original"] else None
        effective = json.loads(row["effective"]) if row["effective"] else None
        if original is None:
            if history or effective is not None:
                raise BackupError("Saved result has no original assessment")
            continue
        replay = deepcopy(original)
        for review in history:
            if review["criterion_id"] not in replay["results"]:
                raise BackupError("Review criterion is absent from its original assessment")
            replay["results"][review["criterion_id"]] = json.loads(review["judgment"])
        if replay != effective:
            raise BackupError("Original-plus-review replay differs from the saved effective result")
        expected_score = history[-1]["resulting_score"] if history else row["original_score"]
        if (json.loads(expected_score) if expected_score else None) != (json.loads(row["effective_score"]) if row["effective_score"] else None):
            raise BackupError("Saved effective score differs from its recorded original/review basis")
        replayed += 1
        # Historical snapshots remain recoverable when today's stricter contract
        # rejects them. Report this separately; never rewrite or regrade them.
        for assessment in (original, effective):
            try:
                checklist = checklists[row["checklist_id"]]
                if checklist is None:
                    raise ValueError("Unsupported historical checklist")
                ids = [m["id"] for m in sources[row["conversation_id"]][0]["transcript"]]
                validate_assessment(checklist, Assessment.model_validate(assessment), ids)
            except (ValidationError, ValueError):
                unsupported_assessments += 1
    return sources, {"sources": len(sources), "checklists": len(checklists), "replayed_originals": replayed,
                     "current_contract_warnings": {"checklists": unsupported_checklists, "assessments": unsupported_assessments}}


def _index_status(db, sources, tables):
    if not {"transcript_index_state", "transcript_messages"} <= tables.keys():
        return {"status": "missing", "fts_present": "transcript_fts" in tables,
                "checked_sources": len(sources), "current_sources": 0}
    states = {r["conversation_id"]: r for r in db.execute("SELECT * FROM transcript_index_state")}
    messages = {}
    for row in db.execute("SELECT * FROM transcript_messages ORDER BY conversation_id,ordinal"):
        messages.setdefault(row["conversation_id"], []).append(row)
    current = 0
    for key, (snapshot, digest) in sources.items():
        state = states.get(key)
        expected = [(m["id"], i, m["speaker"], folded(m["text"]), "\x00" not in folded(m["text"]))
                    for i, m in enumerate(snapshot["transcript"])]
        actual = [(r["message_id"], r["ordinal"], r["speaker"], r["folded_text"], bool(r["fts_safe"])) for r in messages.get(key, [])]
        current += bool(state and state["content_hash"] == digest and state["version"] == INDEX_VERSION and actual == expected)
    extras = len(set(states) - set(sources)) + len(set(messages) - set(sources))
    return {"status": "current" if current == len(sources) and not extras else "stale",
            "checked_sources": len(sources), "current_sources": current, "orphan_sources": extras,
            "fts_present": "transcript_fts" in tables,
            "fts_postings": "not independently validated; SQLite integrity and artifact hashes checked",
            "maintenance": "Use scripts/rebuild_transcript_index.py explicitly on a recovered copy if needed; no automatic repair"}


def inspect_database(path):
    """One read snapshot, including every table/FTS shadow row. No schema writes."""
    try:
        with _readonly(path) as db:
            if [r[0] for r in db.execute("PRAGMA integrity_check")] != ["ok"]:
                raise BackupError("SQLite integrity verification failed")
            if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise BackupError("SQLite foreign-key verification failed")
            fingerprint = _fingerprint(db)
            for table, columns in REQUIRED.items():
                found = {r[1] for r in db.execute("PRAGMA table_info(" + _quoted(table) + ")")}
                if not columns <= found:
                    raise BackupError("Unsupported database schema; required recovery columns are missing")
            sources, identities = _identities(db)
            return {"fingerprint": fingerprint, "integrity": "ok", "foreign_keys": "ok", **identities,
                    "derived_index": _index_status(db, sources, fingerprint["tables"])}
    except BackupError:
        raise
    except (sqlite3.Error, OSError, KeyError, TypeError, ValueError):
        raise BackupError("Database inspection failed; file is unreadable, corrupt or incompatible") from None


def create_backup(database, destination):
    """Consistent online SQLite backup into a new, private directory only."""
    source = Path(database).resolve(strict=True)
    destination = Path(destination).absolute()
    if _exists(destination):
        raise BackupError("Backup destination already exists; choose a new directory")
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    artifact = destination / DATABASE_FILE
    try:
        with _readonly(source) as db, closing(sqlite3.connect(artifact)) as target:
            # SQLite's backup API includes committed WAL pages, unlike file copy.
            db.backup(target)
            # Only the NEW artifact changes journal mode. A portable bundle must
            # be self-contained; opening it read-only must not need WAL/SHM files.
            target.execute("PRAGMA journal_mode=DELETE")
        report = inspect_database(artifact)
        manifest = {"format_version": FORMAT_VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
                    "database_file": DATABASE_FILE, "database_sha256": _sha(artifact),
                    "fingerprint": report["fingerprint"],
                    "privacy": "Private unencrypted database; contains source text and recording URL references. Not a shareable export. No environment files copied."}
        with (destination / MANIFEST_FILE).open("x", encoding="utf-8") as stream:
            stream.write(_json(manifest) + "\n")
        return report
    except (sqlite3.Error, OSError) as error:
        raise BackupError("Backup failed; incomplete destination retained, never use without successful verification") from None


def verify_backup(bundle):
    """Checksums detect damage, not malicious replacement of the whole bundle."""
    bundle = Path(bundle).resolve(strict=True)
    try:
        manifest_path = bundle / MANIFEST_FILE
        artifact = bundle / DATABASE_FILE
        if manifest_path.is_symlink() or artifact.is_symlink() or manifest_path.stat().st_size > 2_000_000:
            raise BackupError("Invalid backup bundle files")
        if any(_exists(Path(str(artifact) + suffix)) for suffix in ("-wal", "-shm", "-journal")):
            raise BackupError("Backup must be standalone; unexpected SQLite sidecars present")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("format_version") != FORMAT_VERSION or manifest.get("database_file") != DATABASE_FILE:
            raise BackupError("Unsupported backup format")
        before = _sha(artifact)
        if before != manifest.get("database_sha256"):
            raise BackupError("Backup database checksum mismatch")
        report = inspect_database(artifact)
        if report["fingerprint"] != manifest.get("fingerprint") or _sha(artifact) != before:
            raise BackupError("Backup logical fingerprint mismatch or file changed during verification")
        return report
    except BackupError:
        raise
    except (OSError, TypeError, ValueError, AttributeError):
        raise BackupError("Backup manifest or database is missing, unreadable or invalid") from None


def _fresh_target(target, active_database):
    raw = Path(target).absolute()
    resolved = raw.resolve()
    if resolved in {Path(active_database).resolve(), DEFAULT_DATABASE.resolve()}:
        raise BackupError("Restore refuses the active/default database; use a new recovery target")
    if any(_exists(Path(str(raw) + suffix)) for suffix in ("", "-wal", "-shm", "-journal")):
        raise BackupError("Restore target or SQLite sidecar already exists; nothing overwritten")
    if not resolved.parent.is_dir():
        raise BackupError("Restore target parent must already exist")
    return resolved


def restore_backup(bundle, target, *, active_database):
    """Verify privately staged bytes, then publish with an atomic no-overwrite link."""
    target = _fresh_target(target, active_database)
    expected = verify_backup(bundle)
    fd, name = tempfile.mkstemp(prefix=".cqa-restore-", suffix=".sqlite3", dir=target.parent)
    stage = Path(name)
    try:
        with os.fdopen(fd, "wb") as output, (Path(bundle) / DATABASE_FILE).open("rb") as source:
            shutil.copyfileobj(source, output)
            output.flush()
            os.fsync(output.fileno())
        manifest = json.loads((Path(bundle) / MANIFEST_FILE).read_text(encoding="utf-8"))
        if _sha(stage) != manifest["database_sha256"]:
            raise BackupError("Backup changed during recovery")
        recovered = inspect_database(stage)
        if recovered["fingerprint"] != expected["fingerprint"]:
            raise BackupError("Recovered data differs from the verified backup")
        _fresh_target(target, active_database)
        # os.replace/rename can overwrite on some platforms; link cannot.
        os.link(stage, target)
        return recovered
    except BackupError:
        raise
    except (OSError, KeyError, ValueError):
        raise BackupError("Recovery failed; no existing target was overwritten") from None
    finally:
        stage.unlink(missing_ok=True)
