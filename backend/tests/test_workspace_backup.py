"""Recovery on explicitly synthetic data; no app, jobs, environment or provider."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from backend.app.db import ChecklistVersion, Database, Evaluation
from backend.app.domain import ImportEnvelope, content_hash
from backend.app.services.importer import import_payload
from backend.app.services.reviews import decide, submit_appeal
from backend.app.services.scoring import score
from backend.app.services import workspace_backup as recovery
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import synthetic_payload


@pytest.fixture
def database(tmp_path, checklist):
    path = tmp_path / "active.sqlite3"
    db = Database(path)
    cid = import_payload(db, ImportEnvelope.model_validate(synthetic_payload()))["conversation_ids"][0]
    original = full_assessment(checklist).model_dump(mode="json")
    calculated = score(checklist, full_assessment(checklist))
    with db.transaction() as session:
        version = ChecklistVersion(snapshot=checklist.model_dump(mode="json"), content_hash=content_hash(checklist))
        session.add(version)
        session.flush()
        session.add(Evaluation(id="synthetic-saved", conversation_id=cid, checklist_id=version.id,
            state="succeeded", cache_key="SYNTHETIC", completeness=calculated["completeness"],
            original=original, original_score=calculated, effective=deepcopy(original), effective_score=deepcopy(calculated)))
    appeal = submit_appeal(db, "synthetic-saved", "contact", "Synthetic correction")
    with db.read_snapshot() as session:
        updated = session.get(Evaluation, "synthetic-saved").updated_at
    judgment = full_assessment(checklist).results["contact"].model_copy(update={"value": False})
    decide(db, appeal, "replace", "Synthetic review", judgment, updated)
    db.engine.dispose()
    return path


def update(path, sql, params=()):
    with sqlite3.connect(path) as db:
        db.execute(sql, params)


def test_roundtrip_preserves_all_rows_schema_reviews_and_index(database, tmp_path):
    before = recovery.inspect_database(database)
    bundle = tmp_path / "private-bundle"
    assert recovery.create_backup(database, bundle) == before
    assert recovery.verify_backup(bundle) == before
    target = tmp_path / "recovered.sqlite3"
    assert recovery.restore_backup(bundle, target, active_database=database) == before
    assert recovery.inspect_database(database) == before
    assert before["replayed_originals"] == 1
    assert before["derived_index"]["status"] == "current"
    assert before["current_contract_warnings"] == {"checklists": 0, "assessments": 0}
    assert sorted(p.name for p in bundle.iterdir()) == ["database.sqlite3", "manifest.json"]
    assert not list(tmp_path.glob(".cqa-restore-*"))
    manifest = (bundle / "manifest.json").read_text()
    assert "ignore the checklist" not in manifest and str(database) not in manifest


def test_backup_includes_committed_wal_without_checkpoint(database, tmp_path):
    live = sqlite3.connect(database)
    try:
        live.execute("PRAGMA journal_mode=WAL")
        live.execute("CREATE TABLE synthetic_wal (value TEXT)")
        live.execute("INSERT INTO synthetic_wal VALUES ('committed WAL')")
        live.commit()
        assert Path(str(database) + "-wal").stat().st_size > 0
        bundle = tmp_path / "wal-bundle"
        report = recovery.create_backup(database, bundle)
        assert report["fingerprint"]["tables"]["synthetic_wal"]["rows"] == 1
        assert recovery.verify_backup(bundle) == report
    finally:
        live.close()


@pytest.mark.parametrize("suffix", ["", "-wal", "-shm", "-journal"])
def test_existing_target_or_sidecar_is_never_overwritten(database, tmp_path, suffix):
    bundle = tmp_path / "bundle"
    recovery.create_backup(database, bundle)
    target = tmp_path / "existing.sqlite3"
    occupied = Path(str(target) + suffix)
    occupied.write_bytes(b"preserve me")
    with pytest.raises(recovery.BackupError, match="already exists"):
        recovery.restore_backup(bundle, target, active_database=database)
    assert occupied.read_bytes() == b"preserve me"
    if suffix:
        assert not target.exists()


def test_active_and_default_paths_refused_even_when_missing(database, tmp_path, monkeypatch):
    nonexistent = tmp_path / "reserved-active.sqlite3"
    monkeypatch.setattr(recovery, "DEFAULT_DATABASE", nonexistent)
    for target, active in [(database, database), (nonexistent, database), (nonexistent, nonexistent)]:
        with pytest.raises(recovery.BackupError, match="active/default"):
            recovery.restore_backup(tmp_path / "unused-bundle", target, active_database=active)


def test_backup_existing_destination_is_preserved(database, tmp_path):
    folder = tmp_path / "existing"
    folder.mkdir()
    (folder / "keep.txt").write_text("original")
    with pytest.raises(recovery.BackupError, match="already exists"):
        recovery.create_backup(database, folder)
    assert (folder / "keep.txt").read_text() == "original"


@pytest.mark.parametrize("damage", ["truncate", "checksum", "logical", "schema", "format", "path", "missing_manifest", "bad_json", "missing_database"])
def test_tampered_bundle_is_refused_before_restore(database, tmp_path, damage):
    folder = tmp_path / "bundle"
    recovery.create_backup(database, folder)
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    artifact = folder / "database.sqlite3"
    if damage == "truncate":
        artifact.write_bytes(artifact.read_bytes()[:100])
    elif damage == "checksum":
        manifest["database_sha256"] = "0" * 64
    elif damage == "logical":
        manifest["fingerprint"]["tables"]["evaluations"]["sha256"] = "0" * 64
    elif damage == "schema":
        manifest["fingerprint"]["schema_sha256"] = "0" * 64
    elif damage == "format":
        manifest["format_version"] = 999
    elif damage == "path":
        manifest["database_file"] = "../active.sqlite3"
    elif damage == "missing_manifest":
        manifest_path.unlink()
    elif damage == "bad_json":
        manifest_path.write_text("invalid JSON")
    elif damage == "missing_database":
        artifact.unlink()
    if damage not in {"missing_manifest", "bad_json"}:
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(recovery.BackupError):
        recovery.restore_backup(folder, tmp_path / "never-created.sqlite3", active_database=database)
    assert not (tmp_path / "never-created.sqlite3").exists()
    assert not list(tmp_path.glob(".cqa-restore-*"))


@pytest.mark.parametrize("damage,reason", [
    ("source", "Source identity"), ("checklist", "Checklist identity"),
    ("replay", "Original-plus-review"), ("score", "Saved effective score"),
    ("foreign_key", "foreign-key"), ("review_identity", "Review/appeal identity"),
])
def test_semantic_preservation_damage_fails(database, damage, reason):
    if damage == "source":
        update(database, "UPDATE conversation_revisions SET content_hash='invalid'")
    elif damage == "checklist":
        update(database, "UPDATE checklist_versions SET content_hash='invalid'")
    elif damage == "replay":
        update(database, "UPDATE evaluations SET effective=original")
    elif damage == "score":
        update(database, "UPDATE evaluations SET effective_score=original_score")
    elif damage == "foreign_key":
        update(database, "UPDATE evaluations SET checklist_id=999999")
    else:
        update(database, "UPDATE review_decisions SET criterion_id='closing'")
    with pytest.raises(recovery.BackupError, match=reason):
        recovery.inspect_database(database)


@pytest.mark.parametrize("damage", ["stale_stamp", "stale_message", "missing"])
def test_derived_index_issues_are_reported_without_repair(database, tmp_path, damage):
    if damage == "stale_stamp":
        update(database, "UPDATE transcript_index_state SET version='old'")
    elif damage == "stale_message":
        update(database, "UPDATE transcript_messages SET folded_text='stale derived text'")
    else:
        update(database, "DROP TABLE transcript_index_state")
    before = recovery.inspect_database(database)
    assert before["derived_index"]["status"] == ("missing" if damage == "missing" else "stale")
    bundle = tmp_path / "bundle"
    recovery.create_backup(database, bundle)
    assert recovery.verify_backup(bundle) == before
    assert recovery.inspect_database(database) == before


def test_atomic_publish_race_does_not_overwrite_new_target(database, tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    recovery.create_backup(database, bundle)
    target = tmp_path / "raced.sqlite3"
    real_link = os.link
    def race(source, destination):
        target.write_bytes(b"concurrent file")
        return real_link(source, destination)
    monkeypatch.setattr(os, "link", race)
    with pytest.raises(recovery.BackupError, match="no existing target"):
        recovery.restore_backup(bundle, target, active_database=database)
    assert target.read_bytes() == b"concurrent file"
    assert not list(tmp_path.glob(".cqa-restore-*"))


def test_bundle_changed_during_copy_is_refused(database, tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    recovery.create_backup(database, bundle)
    real_copy = recovery.shutil.copyfileobj
    def corrupt(source, output):
        real_copy(source, output)
        output.write(b"changed")
    monkeypatch.setattr(recovery.shutil, "copyfileobj", corrupt)
    with pytest.raises(recovery.BackupError, match="changed during recovery"):
        recovery.restore_backup(bundle, tmp_path / "target.sqlite3", active_database=database)
    assert not (tmp_path / "target.sqlite3").exists()


def test_cli_returns_real_report_and_safe_failures(database, tmp_path):
    command = [sys.executable, "scripts/workspace_backup.py"]
    bundle = tmp_path / "cli-bundle"
    created = subprocess.run([*command, "create", "--database", str(database), "--destination", str(bundle)], capture_output=True, text=True)
    assert created.returncode == 0, created.stderr
    assert json.loads(created.stdout)["replayed_originals"] == 1
    restored = subprocess.run([*command, "restore", "--bundle", str(bundle), "--target", str(database), "--active-database", str(database)], capture_output=True, text=True)
    assert restored.returncode == 1
    assert "active/default" in json.loads(restored.stderr)["error"]


def test_non_database_and_missing_schema_are_rejected(tmp_path):
    path = tmp_path / "invalid.sqlite3"
    path.write_text("not a database")
    with pytest.raises(recovery.BackupError, match="corrupt or incompatible"):
        recovery.inspect_database(path)
    path.unlink()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE arbitrary (id INTEGER)")
    with pytest.raises(recovery.BackupError, match="Unsupported database schema"):
        recovery.inspect_database(path)


def test_historical_contract_warning_does_not_rewrite_original(database, tmp_path):
    with sqlite3.connect(database) as db:
        raw = json.loads(db.execute("SELECT original FROM evaluations").fetchone()[0])
        raw["results"]["critical_errors"].update(disposition="needs_review", value=None,
            review_reason="N/A", evidence=[])
        effective = deepcopy(raw)
        judgment = json.loads(db.execute("SELECT judgment FROM review_decisions").fetchone()[0])
        effective["results"]["contact"] = judgment
        db.execute("UPDATE evaluations SET original=?, effective=?", (json.dumps(raw), json.dumps(effective)))
    before = recovery.inspect_database(database)
    assert before["current_contract_warnings"]["assessments"] == 2
    bundle = tmp_path / "legacy-bundle"
    recovery.create_backup(database, bundle)
    recovered = recovery.restore_backup(bundle, tmp_path / "historical.sqlite3", active_database=database)
    assert recovered == before


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_bundle_with_sidecars_is_not_a_standalone_backup(database, tmp_path, suffix):
    bundle = tmp_path / "bundle"
    recovery.create_backup(database, bundle)
    Path(str(bundle / "database.sqlite3") + suffix).write_bytes(b"unexpected sidecar")
    with pytest.raises(recovery.BackupError, match="standalone"):
        recovery.verify_backup(bundle)


def test_empty_environment_file_is_not_copied(database, tmp_path):
    (database.parent / ".env").write_text("SYNTHETIC_PRIVATE_SETTING=not-a-real-credential")
    bundle = tmp_path / "bundle"
    recovery.create_backup(database, bundle)
    assert not (bundle / ".env").exists()
    assert "SYNTHETIC_PRIVATE_SETTING" not in (bundle / "manifest.json").read_text()


def test_directory_target_and_hard_link_alias_are_refused(database, tmp_path):
    directory = tmp_path / "occupied"
    directory.mkdir()
    alias = tmp_path / "active-alias.sqlite3"
    os.link(database, alias)
    for target in (directory, alias):
        with pytest.raises(recovery.BackupError, match="already exists"):
            recovery.restore_backup(tmp_path / "unused-bundle", target, active_database=database)


def test_missing_parent_does_not_create_target_directories(database, tmp_path):
    with pytest.raises(recovery.BackupError, match="parent must already exist"):
        recovery.restore_backup(tmp_path / "unused-bundle", tmp_path / "absent" / "recovered.sqlite3", active_database=database)
    assert not (tmp_path / "absent").exists()
