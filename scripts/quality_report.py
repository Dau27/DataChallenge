"""Compare explicit saved originals with optional references, offline and read-only."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.services.quality_report import QualityReportError, ReferenceManifest, RunSelection, build_quality_report, read_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True, help='Existing private SQLite file; never initialized')
    parser.add_argument('--selection', type=Path, required=True, help='Version 1 manifest of 1-200 exact saved evaluation IDs')
    parser.add_argument('--references', type=Path, help='Optional explicit reference manifest; absent means unlabeled')
    parser.add_argument('--output', type=Path, required=True, help='New private JSON file in an existing directory; never overwrite')
    args = parser.parse_args(argv)
    try:
        selection = read_manifest(args.selection, RunSelection)
        references = read_manifest(args.references, ReferenceManifest) if args.references else None
        result = build_quality_report(args.database, selection, references)
        body = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(body + '\n')
        print(json.dumps({'ok': True, 'status': result['status'], 'selected_runs': result['coverage']['selected_runs'],
                          'labeled_judgments': result['coverage']['definitively_labeled_judgments'],
                          'new_assessment': False, 'added_inference_usd': '0.00'}))
        return 0
    except (QualityReportError, OSError, ValueError):
        error = sys.exception()
        message = str(error) if isinstance(error, QualityReportError) else 'Report output failed; use a fresh private JSON path in an existing directory'
        print(json.dumps({'ok': False, 'error': message}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
