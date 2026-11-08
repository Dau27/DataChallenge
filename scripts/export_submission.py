"""Export/validate the organizer's exact Results JSON 1.0 without inference."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.services.submission import SubmissionError, build_submission, read_submission, validate_saved_submission
from backend.app.services.quality_report import RunSelection, QualityReportError, read_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('export', 'validate'):
        sub = commands.add_parser(command)
        sub.add_argument('--database', type=Path, required=True)
        sub.add_argument('--group-id', required=True, help='Exact already imported organizer group; never guessed or fetched')
        sub.add_argument('--split', choices=('dev', 'prod'), required=True)
        sub.add_argument('--team-name', required=True)
        if command == 'export':
            sub.add_argument('--checklist-id', type=int, default=1)
            sub.add_argument('--selection', type=Path, help='Optional format_version 1 manifest of exact saved evaluation IDs')
            sub.add_argument('--output', type=Path, required=True, help='NEW JSON path; existing files are never replaced')
        else:
            sub.add_argument('--file', type=Path, required=True)
    args = parser.parse_args(argv)
    temporary = None
    try:
        if args.command == 'export':
            selection = read_manifest(args.selection, RunSelection).evaluation_ids if args.selection else None
            packet = build_submission(args.database, args.group_id, args.split, args.team_name, args.checklist_id, selection)
            body = (json.dumps(packet, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix='.cqa-results-', suffix='.tmp', dir=args.output.parent)
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(body); handle.flush(); os.fsync(handle.fileno())
            # Atomic no-overwrite publication, including when another writer creates the target.
            os.link(temporary, args.output)
            summary = {'records': len(packet['results']), 'ok': sum(r['status'] == 'ok' for r in packet['results']),
                'error': sum(r['status'] == 'error' for r in packet['results'])}
        else:
            packet = read_submission(args.file)
            summary = validate_saved_submission(args.database, args.group_id, args.split, packet, args.team_name)
        print(json.dumps({'ok': True, 'operation': args.command, 'split': args.split, 'records': summary['records'],
            'ok_records': summary['ok'], 'error_records': summary['error'],
            'basis': 'effective', 'new_assessment': False, 'added_inference_usd': '0.00'}))
        return 0
    except (SubmissionError, QualityReportError, OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        message = str(error) if isinstance(error, (SubmissionError, QualityReportError)) else 'Submission operation failed; check the documented contract and use a new output path'
        print(json.dumps({'ok': False, 'error': message}), file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())
