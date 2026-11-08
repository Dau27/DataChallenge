"""Organizer Results JSON 1.0 from saved effective results. No app, env or inference."""
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP
import json
import math
from pathlib import Path
import re
import sqlite3
from urllib.parse import parse_qsl, urlsplit

from backend.app.domain import Assessment, Checklist, validate_assessment
from backend.app.services.scoring import score

CRITERIA = {'contact': 'contact', 'needs': 'discovery', 'identification': 'identification',
            'consultation': 'consultation', 'empathy': 'empathy', 'dialogue_management': 'dialogue',
            'closing': 'closure', 'critical_errors': 'critical'}
WEIGHTS = dict(zip(list(CRITERIA.values())[:-1], (10, 15, 20, 20, 15, 15, 5)))
SCALES = {'consultation': {0, 5, 10, 15, 20}, 'dialogue': {0, 4, 7, 10}}
NULLABLE = {'discovery', 'identification', 'consultation', 'closure'}
COUNTS = {'dev': 65, 'prod': 10}
MAX_JSON_BYTES = 32 * 1024 * 1024


class SubmissionError(ValueError):
    """Safe errors never include source text, credentials, SQL or private URLs."""


def require(condition, message):
    if not condition:
        raise SubmissionError(message)


@contextmanager
def _readonly(database):
    db = None
    try:
        path = Path(database).resolve(strict=True)
        require(path.is_file(), 'An existing SQLite database is required')
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        yield db
    except (OSError, sqlite3.Error):
        raise SubmissionError('Saved database is unavailable or incompatible; no replacement was created') from None
    finally:
        if db is not None:
            db.close()


def _sources(db, group_id, split):
    require(split in COUNTS, 'Split must be dev or prod')
    rows = db.execute('SELECT * FROM conversation_revisions WHERE group_id=? ORDER BY revision DESC,id DESC', (group_id,))
    selected = {}
    for row in rows:
        selected.setdefault(row['source_id'], dict(row))
    require(len(selected) == COUNTS[split], 'Dataset count does not match the required split; no placeholder records were created')
    for source_id, row in selected.items():
        snapshot = json.loads(row['snapshot'])
        require(snapshot.get('conversation_id') == source_id, 'Stored source identity is inconsistent')
        require(isinstance(snapshot.get('transcript'), list) and snapshot['transcript'], 'Stored transcript is unavailable')
        row['snapshot'] = snapshot
    return selected


def _safe_text(text, audio_url=None):
    require(isinstance(text, str) and bool(text.strip()), 'A nonempty rationale is required')
    if audio_url:
        text = text.replace(audio_url, '[REDACTED RECORDING URL]')
    text = re.sub(r'\b(?:sk-[A-Za-z0-9_-]{12,}|nvapi-[A-Za-z0-9_-]{12,}|Bearer\s+\S+)', '[REDACTED]', text, flags=re.I)
    def url(match):
        value = match.group()
        try:
            parsed = urlsplit(value)
            hidden = parsed.username or parsed.password or any(re.search(
                r'token|signature|credential|secret|api.?key|authorization|^sig$|^key$', key, re.I) for key, _ in parse_qsl(parsed.query))
        except ValueError:
            hidden = True
        return '[REDACTED URL]' if hidden else value
    return re.sub(r'https?://[^\s<>"\']+', url, text)


def validate_submission(packet, turn_counts, split, team_name=None):
    """Validate exact wire fields/types, original ID coverage, evidence and arithmetic."""
    require(split in COUNTS and type(packet) is dict, 'Invalid submission document')
    require(set(packet) == {'schema_version', 'team_name', 'model', 'results'}, 'Submission envelope fields do not match JSON 1.0')
    require(packet['schema_version'] == '1.0', 'schema_version must be the string 1.0')
    require(isinstance(packet['team_name'], str) and bool(packet['team_name'].strip()), 'team_name is required')
    require(team_name is None or packet['team_name'] == team_name, 'Registered team name does not match')
    model = packet['model']
    require(type(model) is dict and set(model) == {'mode', 'name'}, 'Invalid model disclosure')
    require(type(model['mode']) is str and model['mode'] in {'local', 'external_api', 'hybrid'}, 'Invalid model mode')
    require(isinstance(model['name'], str) and bool(model['name'].strip()), 'Actual recorded model name is required')
    rows = packet['results']
    require(type(rows) is list and len(rows) == len(turn_counts) == COUNTS[split], 'Missing or extra dataset records')
    seen, ok, failed = set(), 0, 0
    for row in rows:
        require(type(row) is dict, 'Invalid result record')
        source_id = row.get('conversation_id')
        require(type(source_id) is str and source_id in turn_counts and source_id not in seen, 'Unknown, internal or duplicate conversation ID')
        seen.add(source_id)
        if row.get('status') == 'error':
            require(set(row) == {'conversation_id', 'status', 'criteria', 'score', 'error'}, 'Invalid error record fields')
            require(row['criteria'] == [] and row['score'] is None and isinstance(row['error'], str) and bool(row['error'].strip()), 'Errors need empty criteria, null score and a reason')
            failed += 1
            continue
        require(row.get('status') == 'ok' and set(row) == {'conversation_id', 'status', 'criteria', 'score'}, 'Invalid success record fields/status')
        criteria = row['criteria']
        require(type(criteria) is list and len(criteria) == 8, 'Each ok result needs exactly eight criteria')
        values = {}
        for item in criteria:
            require(type(item) is dict and set(item) == {'criterion_id', 'value', 'rationale', 'evidence_turns'}, 'Invalid criterion fields')
            cid, value = item['criterion_id'], item['value']
            require(type(cid) is str and cid in CRITERIA.values() and cid not in values, 'Unknown or duplicate official criterion ID')
            values[cid] = value
            if value is None:
                require(cid in NULLABLE, 'N/A is not allowed for this criterion')
            elif cid in SCALES:
                require(type(value) in {int, float} and value in SCALES[cid], 'Scale value must be a raw allowed anchor')
            else:
                require(type(value) is bool, 'Binary/critical values must be booleans')
            require(isinstance(item['rationale'], str) and bool(item['rationale'].strip()), 'Criterion rationale is required')
            turns = item['evidence_turns']
            require(type(turns) is list and bool(turns) and all(type(n) is int and 1 <= n <= turn_counts[source_id] for n in turns), 'Evidence must use one-based original transcript positions')
            require(len(set(turns)) == len(turns), 'Duplicate evidence turn positions')
        calculated = row['score']
        require(type(calculated) is dict and set(calculated) == {'final_score', 'critical_flag'}, 'Invalid score fields')
        total = calculated['final_score']
        require(type(total) in {int, float} and 0 <= total <= 100 and math.isfinite(total), 'final_score must be a finite number from 0 to 100')
        require(type(calculated['critical_flag']) is bool and calculated['critical_flag'] == values['critical'], 'Critical flag does not match its criterion')
        numerator = denominator = Decimal(0)
        for cid, weight in WEIGHTS.items():
            if values[cid] is None:
                continue
            denominator += weight
            fraction = Decimal(str(values[cid])) / max(SCALES[cid]) if cid in SCALES else Decimal(int(values[cid]))
            numerator += weight * fraction
        expected = (100 * numerator / denominator).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        require(Decimal(str(total)) == expected, 'final_score does not match the checklist calculation')
        ok += 1
    require(seen == set(turn_counts), 'Dataset coverage does not match original IDs')
    return {'records': len(rows), 'ok': ok, 'error': failed}


def _compatible(checklist):
    require({c.id for c in checklist.criteria} == set(CRITERIA), 'Select an eight-criterion checklist compatible with the organizer format')
    for criterion in checklist.criteria:
        official = CRITERIA[criterion.id]
        require(criterion.na_allowed == (official in NULLABLE), 'Selected checklist N/A rules differ from the official format')
        require(criterion.weight == WEIGHTS.get(official), 'Selected checklist weights differ from the official format')
        expected_type = 'flag' if official == 'critical' else 'scale' if official in SCALES else 'binary'
        require(criterion.answer_type == expected_type, 'Selected checklist answer types differ from the official format')
        if official in SCALES:
            require({a.value for a in criterion.scale} == SCALES[official], 'Selected checklist scale differs from the official format')


def build_submission(database, group_id, split, team_name, checklist_id=1, selection=None):
    require(isinstance(team_name, str) and bool(team_name.strip()), 'Registered team name is required')
    with _readonly(database) as db:
        sources = _sources(db, group_id, split)
        version = db.execute('SELECT snapshot FROM checklist_versions WHERE id=?', (checklist_id,)).fetchone()
        require(version is not None, 'Selected checklist does not exist')
        try:
            checklist = Checklist.model_validate_json(version['snapshot'])
        except ValueError:
            raise SubmissionError('Selected checklist is invalid') from None
        _compatible(checklist)
        runs = list(db.execute('''SELECT e.* FROM evaluations e JOIN conversation_revisions c ON c.id=e.conversation_id
            WHERE c.group_id=? AND e.checklist_id=? ORDER BY e.created_at DESC,e.id DESC''', (group_id, checklist_id)))
        current_ids = {s['id'] for s in sources.values()}
        selected = {}
        if selection is not None:
            require(len(selection) == len(set(selection)) == len(sources), 'Explicit run selection must cover every current source once')
            wanted = set(selection)
            runs = [r for r in runs if r['id'] in wanted]
            require({r['id'] for r in runs} == wanted, 'Selected run is absent or belongs to another group/checklist')
        for run in runs:
            if run['conversation_id'] in current_ids:
                selected.setdefault(run['conversation_id'], run)
        if selection is not None:
            require(set(selected) == current_ids, 'Selected runs do not cover the latest source revisions exactly')
        output, models = [], set()
        for source_id, source in sorted(sources.items()):
            run = selected.get(source['id'])
            error = 'No saved assessment exists for this source revision and checklist.'
            if run is not None:
                meta = json.loads(run['meta'])
                meta = meta if isinstance(meta, dict) else {}
                name = meta.get('model')
                valid_model = isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,149}', name) and '://' not in name and not name.lower().startswith(('sk-', 'nvapi-', 'bearer'))
                recorded_attempts = json.loads(run['attempts'])
                mock_mode = meta.get('mode') in ('TEST/MOCK', 'TEST_ONLY', 'MOCK')
                if valid_model and not mock_mode and (run['state'] == 'succeeded' or bool(recorded_attempts) or run['cached_from']):
                    models.add(name)
                error = 'The latest saved attempt did not produce a complete exportable assessment.'
            row = {'conversation_id': source_id, 'status': 'error', 'criteria': [], 'score': None, 'error': error}
            if run is not None and run['state'] == 'succeeded' and run['effective'] and run['effective_score']:
                try:
                    snapshot = source['snapshot']
                    positions = {m['id']: i+1 for i,m in enumerate(snapshot['transcript'])}
                    require(len(positions) == len(snapshot['transcript']), 'Invalid saved source message identity')
                    assessment = Assessment.model_validate_json(run['effective'])
                    require(valid_model, 'Saved model provenance is unavailable; no model name was invented')
                    validate_assessment(checklist, assessment, list(positions))
                    calculated = score(checklist, assessment, list(positions))
                    require(calculated == json.loads(run['effective_score']), 'Stored score is inconsistent with the assessment')
                    require(calculated['total'] is not None and calculated['completeness'] == 'complete', 'Reviewed assessment remains unresolved; final score is withheld')
                    require(meta.get('mode') not in {'TEST/MOCK', 'TEST_ONLY', 'MOCK'}, 'Mock output cannot be submitted as a real assessment')
                    criteria = []
                    for internal, official in CRITERIA.items():
                        answer = assessment.results[internal]
                        rationale = answer.explanation + (' N/A: ' + answer.na_reason if answer.disposition == 'not_applicable' else '')
                        turns = set()
                        for evidence in answer.evidence:
                            first, last = positions[evidence.start_message_id], positions[evidence.end_message_id]
                            require(first <= last, 'Saved evidence range is invalid')
                            turns.update(range(first,last+1))
                        value = answer.value
                        criteria.append({'criterion_id': official, 'value': int(value) if official in SCALES and value is not None else value,
                            'rationale': _safe_text(rationale, snapshot.get('audio_url')), 'evidence_turns': sorted(turns)})
                    row = {'conversation_id': source_id, 'status': 'ok', 'criteria': criteria,
                        'score': {'final_score': float(calculated['total']), 'critical_flag': assessment.results['critical_errors'].value}}
                except SubmissionError as exc:
                    row['error'] = str(exc)
                except (ValueError, KeyError, TypeError):
                    row['error'] = 'Saved assessment or evidence is incompatible; no score was fabricated.'
            output.append(row)
        require(bool(models), 'No usable recorded model provenance; no model name was invented')
        packet = {'schema_version': '1.0', 'team_name': team_name, 'model': {'mode': 'external_api', 'name': ', '.join(sorted(models))}, 'results': output}
        validate_submission(packet, {sid:len(s['snapshot']['transcript']) for sid,s in sources.items()}, split, team_name)
        return packet


def validate_saved_submission(database, group_id, split, packet, team_name=None):
    with _readonly(database) as db:
        sources = _sources(db, group_id, split)
        return validate_submission(packet, {sid:len(s['snapshot']['transcript']) for sid,s in sources.items()}, split, team_name)


def read_submission(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate key')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('Nonfinite number')
    try:
        with Path(path).open('rb') as handle:
            body = handle.read(MAX_JSON_BYTES + 1)
        require(len(body) <= MAX_JSON_BYTES, 'Submission JSON exceeds the size safeguard')
        return json.loads(body.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (OSError, ValueError, RecursionError):
        raise SubmissionError('Submission JSON is missing, oversized or invalid UTF-8/JSON') from None
