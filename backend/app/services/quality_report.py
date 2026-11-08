"""Offline reference comparison of explicit saved originals. Never initializes a DB.

References are supplied separately and their declared origin is not verified here.
Missing labels stay unlabeled; reviews/effective answers are never references.
"""
from collections import Counter
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import re
import sqlite3
from typing import Annotated, Any, Literal
from urllib.parse import quote

from pydantic import AfterValidator, Field, StrictInt, StringConstraints, ValidationError, field_validator, model_validator

from backend.app.domain import Assessment, Checklist, Contract, SourceConversation, canonical_json, content_hash, validate_assessment
from backend.app.services.scoring import score

LIMIT = 200
MANIFEST_BYTES = 2 * 1024 * 1024
def _identifier(value):
    if value.lower().startswith(('sk-', 'nvapi-', 'bearer')):
        raise ValueError('A credential is not an identifier')
    return value


Identifier = Annotated[str, StringConstraints(strict=True, pattern=r'^[A-Za-z0-9_-]{1,200}$'), AfterValidator(_identifier)]
Digest = Annotated[str, StringConstraints(strict=True, pattern=r'^[a-f0-9]{64}$')]


class QualityReportError(ValueError):
    """Safe diagnostic: no source, reference text, credential, SQL or path content."""


class Versioned(Contract):
    format_version: StrictInt

    @field_validator('format_version')
    @classmethod
    def version(cls, value):
        if value != 1:
            raise ValueError('Only format_version 1 is supported')
        return value


class RunSelection(Versioned):
    evaluation_ids: list[Identifier] = Field(min_length=1, max_length=LIMIT)

    @field_validator('evaluation_ids')
    @classmethod
    def unique(cls, values):
        if len(set(values)) != len(values):
            raise ValueError('Select unique evaluation IDs')
        return values


class ReferenceAnswer(Contract):
    disposition: Literal['assessed', 'not_applicable', 'unresolved']
    value: Any


class ReferenceCase(Contract):
    evaluation_id: Identifier
    conversation_id: Identifier
    source_content_hash: Digest
    checklist_content_hash: Digest
    judgments: dict[str, ReferenceAnswer] = Field(max_length=64)


class ReferenceManifest(Versioned):
    reference_set_id: Identifier
    declared_origin: Literal['independent_human', 'working_reference', 'synthetic']
    cases: list[ReferenceCase] = Field(max_length=LIMIT)

    @model_validator(mode='after')
    def unique(self):
        if len({case.evaluation_id for case in self.cases}) != len(self.cases):
            raise ValueError('One reference case per selected evaluation is required')
        return self


def _strict_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result

    def constant(_):
        raise ValueError('Nonfinite JSON value')

    return json.loads(body, object_pairs_hook=pairs, parse_constant=constant, parse_float=Decimal)


def read_manifest(path, model):
    """Bound size, require a regular file and reject duplicate/nonfinite JSON."""
    try:
        path = Path(path).resolve(strict=True)
        if not path.is_file():
            raise ValueError('Not a file')
        with path.open('rb') as handle:
            body = handle.read(MANIFEST_BYTES + 1)
        if len(body) > MANIFEST_BYTES:
            raise ValueError('Too large')
        return model.model_validate(_strict_json(body))
    except (OSError, ValueError, TypeError, RecursionError):
        raise QualityReportError('Manifest is missing, oversized or invalid; use the documented version 1 contract') from None


@contextmanager
def _readonly(path):
    try:
        path = Path(path).resolve(strict=True)
        if not path.is_file():
            raise ValueError('Not a file')
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=30)
    except (OSError, ValueError, sqlite3.Error):
        raise QualityReportError('An existing readable SQLite database is required; no replacement was created') from None
    try:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        yield db
    finally:
        db.close()


def _recorded_identifier(value):
    if (isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,149}', value)
            and '://' not in value and not value.lower().startswith(('sk-', 'nvapi-', 'bearer'))):
        return value
    return None


def _decimal_token(number):
    return format(number.normalize(), 'f') if number else '0'


def _provenance(meta, attempts):
    meta = meta if isinstance(meta, dict) else {}
    result = {key: _recorded_identifier(meta.get(key)) for key in (
        'provider', 'model', 'prompt_version', 'schema_version', 'evidence_validation_version', 'mode', 'scoring_version')}
    for key in ('prompt_hash', 'schema_hash'):
        value = meta.get(key)
        result[key] = value if isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}', value) else None
    generation = meta.get('generation')
    normalized = {}
    if isinstance(generation, dict):
        for key in ('temperature', 'max_output_tokens', 'top_p'):
            value = generation.get(key)
            if key in generation and type(value) in {int, float, Decimal}:
                number = Decimal(str(value))
                if number.is_finite() and abs(number.adjusted()) <= 308:
                    normalized[key] = _decimal_token(number)
        if type(generation.get('store')) is bool:
            normalized['store'] = generation['store']
        if isinstance(generation.get('truncation'), str) and generation['truncation'] in {'disabled', 'auto'}:
            normalized['truncation'] = generation['truncation']
        reasoning = generation.get('reasoning')
        if (isinstance(reasoning, dict) and set(reasoning) == {'effort'} and isinstance(reasoning['effort'], str)
                and reasoning['effort'] in {'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'}):
            normalized['reasoning'] = {'effort': reasoning['effort']}
    result['generation'] = normalized
    result['request_identity_available'] = bool(
        all(result[key] for key in ('provider', 'model', 'prompt_version', 'schema_version',
            'evidence_validation_version', 'scoring_version', 'prompt_hash', 'schema_hash'))
        and isinstance(generation, dict) and set(normalized) == set(generation)
        and 'max_output_tokens' in normalized and Decimal(normalized['max_output_tokens']) > 0)
    result['response_models'] = sorted({value for attempt in attempts if isinstance(attempt, dict)
        and (value := _recorded_identifier(attempt.get('response_model'))) is not None}) if isinstance(attempts, list) else []
    return result


def _decision(criterion, answer):
    disposition, value = answer.disposition, answer.value
    if disposition in {'unresolved', 'needs_review'}:
        if value is not None:
            raise ValueError('Abstention requires null')
        return None
    if disposition == 'not_applicable':
        if not criterion.na_allowed or value is not None:
            raise ValueError('Invalid N/A')
        return {'disposition': disposition, 'value': None}
    if disposition != 'assessed':
        raise ValueError('Invalid disposition')
    if criterion.answer_type == 'scale':
        if type(value) not in {int, float, Decimal}:
            raise ValueError('A numeric anchor is required')
        number = Decimal(str(value))
        if not number.is_finite() or number not in {a.value for a in criterion.scale}:
            raise ValueError('Invalid anchor')
        value = _decimal_token(number)
    elif type(value) is not bool:
        raise ValueError('A strict boolean is required')
    return {'disposition': disposition, 'value': value}


def _empty_metrics():
    return {'labeled': 0, 'observed': 0, 'matches': 0, 'missing': 0, 'na_matrix': Counter(),
            'scale_count': 0, 'scale_error': Decimal(0), 'scale_normalized_error': Decimal(0), 'scale_units': set(), 'critical': Counter(),
            'total_count': 0, 'total_error': Decimal(0), 'total_squared_error': Decimal(0), 'total_bias': Decimal(0)}


def _ratio(a, b):
    return str((Decimal(a) / b).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)) if b else None


def _mean(value, count):
    return str((value / count).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)) if count else None


def _finish(metrics):
    if not metrics['labeled']:
        return None
    critical = {key: metrics['critical'][key] for key in ('tp', 'fp', 'fn', 'tn', 'missing_positive', 'missing_negative')}
    return {'labeled_judgments': metrics['labeled'], 'observed_predictions': metrics['observed'],
            'exact_matches': metrics['matches'], 'missing_or_unresolved_predictions': metrics['missing'],
            'agreement_all_labeled': _ratio(metrics['matches'], metrics['labeled']),
            'agreement_observed_only': _ratio(metrics['matches'], metrics['observed']),
            'prediction_coverage': _ratio(metrics['observed'], metrics['labeled']),
            'na_matrix': {key: metrics['na_matrix'][key] for key in (
                'reference_na_prediction_na', 'reference_na_prediction_applicable', 'reference_na_prediction_missing',
                'reference_applicable_prediction_na', 'reference_applicable_prediction_applicable', 'reference_applicable_prediction_missing')},
            'scale': {'comparable_assessed_pairs': metrics['scale_count'], 'anchor_unit_count': len(metrics['scale_units']),
                      'mean_absolute_anchor_error': _mean(metrics['scale_error'], metrics['scale_count']) if len(metrics['scale_units']) == 1 else None,
                      'mean_absolute_fraction_of_saved_maximum': _mean(metrics['scale_normalized_error'], metrics['scale_count'])},
            'critical': {**critical, 'precision_observed': _ratio(critical['tp'], critical['tp'] + critical['fp']),
                         'recall_observed': _ratio(critical['tp'], critical['tp'] + critical['fn']),
                         'recall_all_reference_positive': _ratio(critical['tp'], critical['tp'] + critical['fn'] + critical['missing_positive'])},
            'total': {'comparable_complete_cases': metrics['total_count'],
                      'mean_absolute_error': _mean(metrics['total_error'], metrics['total_count']),
                      'mean_signed_prediction_minus_reference': _mean(metrics['total_bias'], metrics['total_count']),
                      'root_mean_squared_error': _mean((metrics['total_squared_error'] / metrics['total_count']).sqrt(), 1) if metrics['total_count'] else None}}


def _observe(metrics, criterion, reference, prediction):
    metrics['labeled'] += 1
    metrics['observed' if prediction is not None else 'missing'] += 1
    metrics['matches'] += int(prediction == reference)
    ref_state = 'na' if reference['disposition'] == 'not_applicable' else 'applicable'
    pred_state = 'missing' if prediction is None else 'na' if prediction['disposition'] == 'not_applicable' else 'applicable'
    metrics['na_matrix'][f'reference_{ref_state}_prediction_{pred_state}'] += 1
    if criterion.answer_type == 'scale' and ref_state == pred_state == 'applicable':
        maximum = max(anchor.value for anchor in criterion.scale)
        error = abs(Decimal(prediction['value']) - Decimal(reference['value']))
        metrics['scale_count'] += 1
        metrics['scale_error'] += error
        metrics['scale_normalized_error'] += error / maximum
        metrics['scale_units'].add((criterion.id, str(maximum)))
    if criterion.answer_type == 'flag':
        actual = reference['value']
        if prediction is None:
            key = 'missing_positive' if actual else 'missing_negative'
        else:
            predicted = prediction['value']
            key = 'tp' if actual and predicted else 'fn' if actual else 'fp' if predicted else 'tn'
        metrics['critical'][key] += 1


def _reference_total(criteria, answers):
    if set(answers) != {c.id for c in criteria} or any(answer is None for answer in answers.values()):
        return None
    applicable = [c for c in criteria if c.answer_type != 'flag' and answers[c.id]['disposition'] != 'not_applicable']
    denominator = sum((c.weight for c in applicable), Decimal(0))
    if not denominator:
        return None
    subtotal = sum((c.weight * (Decimal(int(answers[c.id]['value'])) if c.answer_type == 'binary'
        else Decimal(answers[c.id]['value']) / max(a.value for a in c.scale)) for c in applicable), Decimal(0))
    return (100 * subtotal / denominator).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def _load_case(db, evaluation_id):
    row = db.execute('''SELECT e.id,e.conversation_id,e.checklist_id,e.state,e.original,e.original_score,e.meta,e.attempts,e.cached_from,
        c.group_id,c.source_id,c.content_hash AS source_hash,c.snapshot AS source,
        v.content_hash AS checklist_hash,v.snapshot AS checklist
        FROM evaluations e LEFT JOIN conversation_revisions c ON c.id=e.conversation_id
        LEFT JOIN checklist_versions v ON v.id=e.checklist_id WHERE e.id=?''', (evaluation_id,)).fetchone()
    if row is None:
        return None
    row = dict(row)
    checklist = Checklist.model_validate(_strict_json(row['checklist']))
    source = _strict_json(row['source'])
    original_source = {**source, 'transcript': [{k: v for k, v in m.items() if k != 'id'} for m in source['transcript']]}
    SourceConversation.model_validate(original_source)
    ids = [m['id'] for m in source['transcript']]
    if (source['conversation_id'] != row['source_id']
            or ids != [f'm{i:04d}' for i in range(1, len(ids) + 1)]
            or content_hash({'group_id': row['group_id'], **original_source}) != row['source_hash']
            or content_hash(checklist) != row['checklist_hash']):
        raise ValueError('Saved identity mismatch')
    row['checklist'], row['source'] = checklist, source
    try:
        meta = _strict_json(row['meta'])
    except (ValueError, TypeError, RecursionError):
        meta = {}
    try:
        attempts = _strict_json(row['attempts'])
    except (ValueError, TypeError, RecursionError):
        attempts = []
    row['provenance'] = _provenance(meta, attempts)
    row['predictions'], row['total'] = {}, None
    row['original_status'] = 'run_not_succeeded' if row['state'] != 'succeeded' else 'invalid_or_missing_original'
    if row['state'] == 'succeeded':
        try:
            assessment = Assessment.model_validate(_strict_json(row['original']))
            validate_assessment(checklist, assessment, ids)
            stored_score = _strict_json(row['original_score'])
            if canonical_json(score(checklist, assessment, ids)) != canonical_json(stored_score):
                raise ValueError('Saved arithmetic mismatch')
            row['predictions'] = {c.id: _decision(c, assessment.results[c.id]) for c in checklist.criteria}
            row['total'] = Decimal(stored_score['total']) if stored_score['total'] is not None else None
            row['original_status'] = 'valid_original'
        except (ValueError, TypeError, KeyError, ArithmeticError):
            pass
    return row


def build_quality_report(database, selection, references=None):
    """One bounded read snapshot; same dataset/checklist, one run per exact source."""
    try:
        selection = RunSelection.model_validate(selection)
        references = ReferenceManifest.model_validate(references) if references is not None else None
    except (ValidationError, ValueError, TypeError, RecursionError):
        raise QualityReportError('Invalid selection or reference manifest; no comparison was performed') from None
    try:
        with localcontext() as context, _readonly(database) as db:
            context.prec = 800
            return _report(db, selection, references)
    except QualityReportError:
        raise
    except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, ArithmeticError, RecursionError):
        raise QualityReportError('Saved data is unreadable or incompatible; no record was modified') from None


def _report(db, selection, references):
    refs = {case.evaluation_id: case for case in references.cases} if references else {}
    overall = _empty_metrics()
    groups = {}
    cases, differences, rejected = [], [], []
    counts = Counter()
    scope = None
    seen_sources = set()
    for evaluation_id in selection.evaluation_ids:
        row = _load_case(db, evaluation_id)
        if row is None:
            raise QualityReportError('A selected saved evaluation is missing; refresh the exact selection before reporting')
        identity = (row['group_id'], row['checklist_id'], row['checklist_hash'])
        if scope is not None and identity != scope:
            raise QualityReportError('Select one exact dataset and checklist version per report; do not pool incompatible runs')
        scope = identity
        if row['conversation_id'] in seen_sources:
            raise QualityReportError('Select one evaluation per exact source revision; repeated runs are not independent cases')
        seen_sources.add(row['conversation_id'])
        counts['found_runs'] += 1
        counts[row['original_status']] += 1
        counts['cached_runs'] += int(row['cached_from'] is not None)
        criteria = {c.id: c for c in row['checklist'].criteria}
        counts['selected_judgments'] += len(criteria)
        base = {'evaluation_id': evaluation_id, 'conversation_id': row['conversation_id'],
                'source_content_hash': row['source_hash'], 'checklist_content_hash': row['checklist_hash'],
                'original_status': row['original_status'], 'cached': row['cached_from'] is not None,
                'language': row['source']['language'], 'channel': row['source']['channel'], 'reference_status': 'not_supplied',
                'review_path': f'#conversation/{quote(row["conversation_id"], safe="")}?evaluation={quote(evaluation_id, safe="")}',
                'saved_original_total': str(row['total']) if row['total'] is not None else None, 'computed_reference_total': None}
        cases.append(base)
        cohort_key = content_hash({'recorded': row['provenance'],
            'unknown_identity_run': evaluation_id if not row['provenance']['request_identity_available'] else None})
        keys = [('language', row['source']['language']), ('channel', row['source']['channel']), ('provenance', cohort_key)]
        for kind, key in keys:
            groups.setdefault((kind, key), {'metrics': _empty_metrics(), 'selected_runs': 0, 'recorded': row['provenance'] if kind == 'provenance' else None})['selected_runs'] += 1
        for criterion_id in criteria:
            groups.setdefault(('criterion', criterion_id), {'metrics': _empty_metrics(), 'selected_runs': 0, 'recorded': None})['selected_runs'] += 1
        reference = refs.get(evaluation_id)
        if reference is None:
            continue
        try:
            if (reference.conversation_id != row['conversation_id'] or reference.source_content_hash != row['source_hash']
                    or reference.checklist_content_hash != row['checklist_hash']):
                raise ValueError('identity')
            if not set(reference.judgments) <= set(criteria):
                raise ValueError('criteria')
            answers = {key: _decision(criteria[key], answer) for key, answer in reference.judgments.items()}
        except (ValueError, TypeError, ArithmeticError):
            counts['rejected_reference_cases'] += 1
            base['reference_status'] = 'incompatible_or_invalid'
            rejected.append({'evaluation_id': evaluation_id, 'reason': 'Reference identity, criterion or answer does not match the saved source/checklist'})
            continue
        counts['compatible_reference_cases'] += 1
        base['reference_status'] = 'compared' if any(value is not None for value in answers.values()) else 'no_definitive_labels'
        counts['reference_abstentions'] += sum(value is None for value in answers.values())
        for criterion_id, expected in answers.items():
            if expected is None:
                continue
            criterion = criteria[criterion_id]
            predicted = row['predictions'].get(criterion_id)
            criterion_group = groups[('criterion', criterion_id)]
            for metrics in [overall, criterion_group['metrics'], *(groups[key]['metrics'] for key in keys)]:
                _observe(metrics, criterion, expected, predicted)
            if predicted != expected:
                differences.append({'evaluation_id': evaluation_id, 'criterion_id': criterion_id,
                    'reference': expected, 'prediction': predicted,
                    'prediction_state': 'missing_or_unresolved' if predicted is None else 'observed',
                    'review_path': base['review_path'] + '&criterion=' + quote(criterion_id, safe='')})
        reference_total = _reference_total(list(criteria.values()), answers)
        base['computed_reference_total'] = str(reference_total) if reference_total is not None else None
        if row['total'] is not None and reference_total is not None:
            error = row['total'] - reference_total
            for metrics in [overall, *(groups[key]['metrics'] for key in keys)]:
                metrics['total_count'] += 1
                metrics['total_error'] += abs(error)
                metrics['total_squared_error'] += error**2
                metrics['total_bias'] += error
    return {'report_schema_version': 1, 'basis': 'original',
        'status': 'reference_comparison' if overall['labeled'] else 'unlabeled',
        'scope': {'selection': selection.model_dump(mode='json'),
                  'dataset_group_id': _recorded_identifier(scope[0]) if scope else None,
                  'dataset_group_hash': content_hash(scope[0]) if scope else None,
                  'checklist_id': scope[1] if scope else None, 'checklist_content_hash': scope[2] if scope else None},
        'references': {'reference_set_id': references.reference_set_id if references else None,
                       'declared_origin': references.declared_origin if references else None,
                       'origin_independently_verified': False,
                       'unused_reference_evaluation_ids': sorted(set(refs) - set(selection.evaluation_ids))},
        'coverage': {**{key: counts[key] for key in ('found_runs', 'missing_runs', 'valid_original', 'invalid_or_missing_original',
            'run_not_succeeded', 'cached_runs', 'selected_judgments', 'compatible_reference_cases', 'rejected_reference_cases', 'reference_abstentions')},
            'selected_runs': len(selection.evaluation_ids), 'definitively_labeled_judgments': overall['labeled'],
            'unlabeled_or_abstained_judgments': counts['selected_judgments'] - overall['labeled']},
        'metrics': _finish(overall),
        'groups': [{'kind': kind, 'key': key, 'selected_runs': value['selected_runs'], 'recorded': value['recorded'],
                    'metrics': _finish(value['metrics'])} for (kind, key), value in sorted(groups.items())],
        'cases': cases, 'disagreements': differences, 'rejected_references': rejected,
        'policy': {'no_new_assessment': True, 'reference_origin_is_declared_only': True,
                   'effective_answers_or_reviews_used_as_references': False, 'source_text_or_recording_urls_included': False,
                   'original_validation': 'Schema, source message IDs and deterministic arithmetic replay; not semantic certification.',
                   'provenance_groups': 'Recorded hashes, request settings and response model IDs; incomplete request identities are kept separate per run. No current defaults are substituted.',
                   'agreement_denominator': 'Definitively supplied compatible labels; missing/unresolved predictions count as nonmatches. Observed-only rate and coverage are separate.',
                   'total_error_denominator': 'Complete compatible reference cases with a validated saved original total; no fabricated zeros.',
                   'computed_metric_rounding': 'Rates and errors: six decimal places, half up. Stored operator totals/answers remain unchanged. Cross-criterion scale error uses fractions of each saved maximum; mixed raw units are withheld.',
                   'interpretation': 'Saved historical runs, not current-configuration accuracy or an official grade. Agreement does not establish reference truth.'}}
