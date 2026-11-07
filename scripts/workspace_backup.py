"""Create, verify or recover a private SQLite bundle, with no app/provider startup."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.services.workspace_backup import BackupError, create_backup, restore_backup, verify_backup


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="Consistent backup to a NEW private directory")
    create.add_argument("--database", type=Path, required=True)
    create.add_argument("--destination", type=Path, required=True)
    verify = sub.add_parser("verify", help="Verify checksum, all tables/schema, identities and review replay")
    verify.add_argument("--bundle", type=Path, required=True)
    restore = sub.add_parser("restore", help="Verify and recover to a NEW file only; never replaces an active DB")
    restore.add_argument("--bundle", type=Path, required=True)
    restore.add_argument("--target", type=Path, required=True)
    restore.add_argument("--active-database", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            report = create_backup(args.database, args.destination)
        elif args.command == "verify":
            report = verify_backup(args.bundle)
        else:
            report = restore_backup(args.bundle, args.target, active_database=args.active_database)
    except (BackupError, OSError):
        # Do not expose raw SQLite errors or file contents in terminal logs.
        error = sys.exception()
        message = str(error) if isinstance(error, BackupError) else "Filesystem operation failed; check paths and permissions"
        print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "operation": args.command, **report}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
