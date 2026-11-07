"""Explicitly synthetic reference labels; no independent-accuracy claim or inference."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import socket

import pytest

from backend.app.db import ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import content_hash
from backend.app.services.quality_report import (
    MANIFEST_BYTES, QualityReportError, ReferenceManifest, RunSelection, build_quality_report, read_manifest,
)
from backend.app.services.scoring import score
from backend.tests.conftest import full_assessment
from backend.tests.test_saved_inspection import saved, db_rows
from backend.tests.test_workflow import synthetic_payload
from scripts.quality_report import main


def selection(*ids):
    return {'format_version': 1, 'evaluation_ids': list(ids or ('left',))}


def reference(saved, run_id='left', **judgments):
    _, db, _, _, _ = saved
    with db.sessions() as session:
        run = session.get(Evaluation, run_id)
        source = session.get(Conversation, run.conversation_id)
        version = session.get(ChecklistVersion, run.checklist_id)
        answers = {key: {'disposition': answer['disposition'], 'value': answer['value']}
                   for key, answer in run.original['results'].items()} if run.original else {}
        return {'evaluation_id': run_id, 'conversation_id': run.conversation_id,
                'source_content_hash': source.content_hash, 'checklist_content_hash': version.content_hash,
                'judgments': judgments or answers}


def manifest(*cases):
    return {'format_version': 1, 'reference_set_id': 'SYNTHETIC_TEST_ONLY', 'declared_origin': 'synthetic', 'cases': list(cases)}


def report(saved, refs=None, ids=None):
    _, db, _, _, _ = saved
    return build_quality_report(Path(db.engine.url.database), ids or selection(), refs)


def test_no_reference_stays_unlabeled_and_has_criterion_language_channel_provenance_coverage(saved, monkeypatch):
    before = db_rows(saved[1])
    def forbidden(*args, **kwargs):
        pytest.fail('Offline reporting attempted network or database initialization')
    monkeypatch.setattr(Database, '__init__', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    data = report(saved)
    assert data['status'] == 'unlabeled' and data['metrics'] is None
    assert data['basis'] == 'original'
    assert data['coverage']['selected_judgments'] == data['coverage']['unlabeled_or_abstained_judgments'] == 8
    assert data['coverage']['definitively_labeled_judgments'] == 0
    assert {g['kind'] for g in data['groups']} == {'criterion', 'language', 'channel', 'provenance'}
    assert len([g for g in data['groups'] if g['kind'] == 'criterion']) == 8
    assert all(g['metrics'] is None and g['selected_runs'] == 1 for g in data['groups'])
    assert db_rows(saved[1]) == before


def test_known_errors_keep_denominators_na_scale_critical_score_bias_and_review_links(saved):
    case = reference(saved)
    case['judgments']['contact']['value'] = False
    case['judgments']['needs'] = {'disposition': 'not_applicable', 'value': None}
    case['judgments']['consultation']['value'] = 15
    case['judgments']['critical_errors']['value'] = True
    data = report(saved, manifest(case))
    metrics = data['metrics']
    assert metrics['labeled_judgments'] == metrics['observed_predictions'] == 8
    assert metrics['exact_matches'] == 4 and metrics['agreement_all_labeled'] == '0.500000'
    assert metrics['na_matrix']['reference_na_prediction_applicable'] == 1
    assert metrics['scale'] == {'comparable_assessed_pairs': 2, 'anchor_unit_count': 2,
        'mean_absolute_anchor_error': None, 'mean_absolute_fraction_of_saved_maximum': '0.125000'}
    consultation = next(g for g in data['groups'] if g['kind']=='criterion' and g['key']=='consultation')
    assert consultation['metrics']['scale']['mean_absolute_anchor_error']=='5.000000'
    assert metrics['critical']['fn'] == 1 and metrics['critical']['recall_all_reference_positive'] == '0.000000'
    assert metrics['critical']['precision_observed'] is None
    assert data['cases'][0]['saved_original_total'] == '100.00'
    assert data['cases'][0]['computed_reference_total'] == '82.35'
    assert metrics['total']['mean_absolute_error'] == '17.650000'
    assert metrics['total']['mean_signed_prediction_minus_reference'] == '17.650000'
    assert {d['criterion_id'] for d in data['disagreements']} == {'contact', 'needs', 'consultation', 'critical_errors'}
    assert all(d['review_path'].startswith(data['cases'][0]['review_path'] + '&criterion=') for d in data['disagreements'])
    assert data['references']['declared_origin'] == 'synthetic'
    assert data['references']['origin_independently_verified'] is False


def test_partial_labels_and_reference_abstentions_do_not_become_na_or_complete_totals(saved):
    case = reference(saved, contact={'disposition': 'unresolved', 'value': None},
                     consultation={'disposition': 'assessed', 'value': 20})
    data = report(saved, manifest(case))
    assert data['coverage']['reference_abstentions'] == 1
    assert data['coverage']['definitively_labeled_judgments'] == 1
    assert data['coverage']['unlabeled_or_abstained_judgments'] == 7
    assert data['metrics']['exact_matches'] == 1
    assert data['metrics']['total']['comparable_complete_cases'] == 0
    assert data['cases'][0]['computed_reference_total'] is None
    case['judgments'] = {'contact': {'disposition': 'unresolved', 'value': None}}
    empty = report(saved, manifest(case))
    assert empty['status'] == 'unlabeled' and empty['metrics'] is None
    assert empty['cases'][0]['reference_status'] == 'no_definitive_labels'


@pytest.mark.parametrize('critical_positive', [False, True])
def test_failed_prediction_counts_as_missing_not_wrong_observed_or_zero_score(saved, critical_positive):
    case = reference(saved)
    case['judgments']['critical_errors']['value'] = critical_positive
    with saved[1].transaction() as session:
        run = session.get(Evaluation, 'left')
        run.state = 'failed'; run.original = None; run.original_score = None
    before = db_rows(saved[1])
    data = report(saved, manifest(case))
    assert data['coverage']['run_not_succeeded'] == 1
    assert data['metrics']['missing_or_unresolved_predictions'] == 8
    assert data['metrics']['agreement_all_labeled'] == '0.000000'
    assert data['metrics']['agreement_observed_only'] is None
    assert data['metrics']['critical']['missing_positive' if critical_positive else 'missing_negative'] == 1
    assert data['metrics']['critical']['recall_all_reference_positive'] == ('0.000000' if critical_positive else None)
    assert data['metrics']['na_matrix']['reference_applicable_prediction_missing'] == 8
    assert data['metrics']['total']['mean_absolute_error'] is None
    assert data['cases'][0]['saved_original_total'] is None
    assert db_rows(saved[1]) == before


def test_unresolved_original_does_not_become_false_na_or_zero_and_original_ignores_reviewed_effective(saved):
    case = reference(saved)
    client, db, checklist, _, _ = saved
    with db.transaction() as session:
        run = session.get(Evaluation, 'left')
        original = full_assessment(checklist)
        original.results['contact'].disposition = 'needs_review'
        original.results['contact'].value = None
        original.results['contact'].review_reason = 'SYNTHETIC missing authority'
        run.original = original.model_dump(mode='json'); run.original_score = score(checklist, original)
        # Deliberately different effective snapshot. The reporter must never use it.
        run.effective = full_assessment(checklist).model_dump(mode='json')
        run.effective_score = score(checklist, full_assessment(checklist))
    before = db_rows(db)
    data = report(saved, manifest(case))
    assert data['metrics']['exact_matches'] == 7
    assert data['metrics']['missing_or_unresolved_predictions'] == 1
    assert data['metrics']['agreement_all_labeled'] == '0.875000'
    assert data['metrics']['agreement_observed_only'] == '1.000000'
    assert data['cases'][0]['saved_original_total'] is None
    assert data['metrics']['total']['comparable_complete_cases'] == 0
    assert db_rows(db) == before


@pytest.mark.parametrize('field,value', [('conversation_id', 'WRONG_REVISION'), ('source_content_hash', 'f'*64), ('checklist_content_hash', 'e'*64)])
def test_references_for_other_source_or_rubric_are_rejected_without_metrics(saved, field, value):
    case = reference(saved); case[field] = value
    data = report(saved, manifest(case))
    assert data['status'] == 'unlabeled' and data['metrics'] is None
    assert data['coverage']['rejected_reference_cases'] == 1
    assert len(data['rejected_references']) == 1


@pytest.mark.parametrize('criterion,answer', [
    ('contact', {'disposition': 'assessed', 'value': 1}),
    ('contact', {'disposition': 'not_applicable', 'value': None}),
    ('consultation', {'disposition': 'assessed', 'value': True}),
    ('consultation', {'disposition': 'assessed', 'value': 13}),
    ('needs', {'disposition': 'not_applicable', 'value': False}),
    ('UNKNOWN', {'disposition': 'assessed', 'value': True}),
    ('contact', {'disposition': 'unresolved', 'value': True}),
])
def test_reference_answers_respect_types_anchors_na_and_abstention_contract(saved, criterion, answer):
    data = report(saved, manifest(reference(saved, **{criterion: answer})))
    assert data['metrics'] is None and data['coverage']['rejected_reference_cases'] == 1


@pytest.mark.parametrize('ids', [[], ['left', 'left'], ['left']*201, [True], ['bad/id'], ['sk-SYNTHETIC-CREDENTIAL']])
def test_invalid_selection_is_not_silently_repaired(saved, ids):
    with pytest.raises(QualityReportError, match='Invalid selection'):
        report(saved, ids={'format_version': 1, 'evaluation_ids': ids})


def test_missing_id_and_duplicate_source_runs_refuse_report_instead_of_inflating_denominators(saved):
    with pytest.raises(QualityReportError, match='missing'):
        report(saved, ids=selection('MISSING'))
    with pytest.raises(QualityReportError, match='one evaluation per exact source'):
        report(saved, ids=selection('left', 'right'))


def test_duplicate_references_extra_keys_and_noninteger_versions_are_invalid(saved):
    case = reference(saved)
    for data in (manifest(case, case), {**manifest(case), 'unexpected': True}, {**manifest(case), 'format_version': True},
                 {**manifest(case), 'declared_origin': 'official_truth'}, {**manifest(case), 'reference_set_id': 'sk-SYNTHETIC-SECRET'}):
        with pytest.raises(QualityReportError, match='Invalid selection'):
            report(saved, data)


def test_cached_run_and_unknown_provenance_are_explicit_and_secret_text_is_not_output(saved):
    with saved[1].transaction() as session:
        run = session.get(Evaluation, 'left')
        run.cached_from = 'right'
        raw = deepcopy(run.original)
        raw['results']['contact']['explanation'] = 'SYNTHETIC PRIVATE SOURCE https://example.invalid/?token=SECRET'
        run.original = raw
        run.meta = {'model': 'sk-SYNTHETIC-SECRET', 'prompt_version': [], 'api_key': 'PRIVATE_TEST_SECRET'}
    data = report(saved)
    serialized = json.dumps(data)
    assert data['coverage']['cached_runs'] == 1
    profile = next(g for g in data['groups'] if g['kind'] == 'provenance')['recorded']
    assert profile['model'] is None and profile['prompt_version'] is None
    for value in ('PRIVATE SOURCE', 'PRIVATE_TEST_SECRET', 'token=SECRET', 'sk-SYNTHETIC-SECRET'):
        assert value not in serialized


def test_saved_score_damage_is_an_explicit_missing_prediction_and_never_repaired(saved):
    refs = manifest(reference(saved))
    with saved[1].transaction() as session:
        run = session.get(Evaluation, 'left')
        run.original_score = {**run.original_score, 'total': '12.34'}
    before = db_rows(saved[1])
    data = report(saved, refs)
    assert data['coverage']['invalid_or_missing_original'] == 1
    assert data['metrics']['missing_or_unresolved_predictions'] == 8
    assert data['cases'][0]['saved_original_total'] is None
    assert db_rows(saved[1]) == before


def test_multilingual_groups_keep_exact_recorded_profiles_separate(saved):
    client, db, checklist, _, _ = saved
    cases = [reference(saved)]
    ids = ['left']
    for language in ('RU', 'KZ'):
        cid = client.post('/api/import/json', json=synthetic_payload(language=language, source_id='SYNTHETIC_'+language)).json()['conversation_ids'][0]
        run_id = 'SYNTHETIC_RUN_'+language
        answer = full_assessment(checklist)
        with db.transaction() as session:
            session.add(Evaluation(id=run_id, conversation_id=cid, checklist_id=1, state='succeeded', cache_key='SYNTHETIC',
                original=answer.model_dump(mode='json'), original_score=score(checklist, answer),
                meta={'model': 'SYNTHETIC_'+language, 'prompt_version': 'SYNTHETIC_v2'}, attempts=[]))
        ids.append(run_id); cases.append(reference(saved, run_id))
    data = report(saved, manifest(*cases), selection(*ids))
    assert {g['key'] for g in data['groups'] if g['kind'] == 'language'} == {'RU', 'KZ', 'EN'}
    assert len([g for g in data['groups'] if g['kind'] == 'provenance']) == 3
    assert all(g['metrics']['labeled_judgments'] == 8 for g in data['groups'] if g['kind'] == 'language')
    assert data['metrics']['total']['comparable_complete_cases'] == 3
    assert data['metrics']['total']['mean_absolute_error'] == '0.000000'


@pytest.mark.parametrize('change', ['source_hash', 'checklist_hash', 'source_text'])
def test_inconsistent_saved_identity_refuses_reporting(saved, change):
    with saved[1].transaction() as session:
        row = session.get(Conversation, saved[3])
        if change == 'source_hash':row.content_hash = 'f'*64
        elif change == 'source_text':
            source = deepcopy(row.snapshot); source['transcript'][0]['text'] += ' altered'; row.snapshot = source
        else:session.get(ChecklistVersion, 1).content_hash = 'f'*64
    with pytest.raises(QualityReportError, match='incompatible'):
        report(saved)


def test_mixed_dataset_or_checklist_versions_refused(saved):
    _, db, checklist, cid, _ = saved
    for mode in ('dataset', 'checklist'):
        run_id = 'SYNTHETIC_'+mode
        with db.transaction() as session:
            source_id = cid; version_id = 1
            if mode == 'dataset':
                source = deepcopy(session.get(Conversation, cid).snapshot)
                raw = {**source, 'transcript': [{k:v for k,v in m.items() if k!='id'} for m in source['transcript']]}
                conversation = Conversation(group_id='OTHER', source_id=source['conversation_id'], revision=1,
                    content_hash=content_hash({'group_id':'OTHER', **raw}), snapshot=source)
                session.add(conversation);session.flush();source_id=conversation.id
            else:
                rubric = checklist.model_copy(deep=True);rubric.name='SYNTHETIC other rubric'
                version = ChecklistVersion(content_hash=content_hash(rubric), snapshot=rubric.model_dump(mode='json'))
                session.add(version);session.flush();version_id=version.id
            answer = full_assessment(checklist)
            session.add(Evaluation(id=run_id, conversation_id=source_id, checklist_id=version_id, cache_key='SYNTHETIC',
                original=answer.model_dump(mode='json'), original_score=score(checklist, answer), meta={}, attempts=[]))
        with pytest.raises(QualityReportError, match='one exact dataset and checklist'):
            report(saved, ids=selection('left', run_id))


@pytest.mark.parametrize('body', [b'{"format_version":1,"format_version":1,"evaluation_ids":["left"]}',
    b'{"format_version":NaN,"evaluation_ids":["left"]}', b'[]', b'not JSON'])
def test_manifest_parser_refuses_duplicate_keys_nonfinite_and_invalid_json(tmp_path, body):
    path=tmp_path/'selection.json';path.write_bytes(body)
    with pytest.raises(QualityReportError, match='Manifest'):
        read_manifest(path, RunSelection)


def test_oversized_manifest_missing_database_and_empty_references_remain_safe(saved, tmp_path):
    path=tmp_path/'large.json';path.write_bytes(b' '*(MANIFEST_BYTES+1))
    with pytest.raises(QualityReportError):read_manifest(path, RunSelection)
    absent=tmp_path/'absent.sqlite3'
    with pytest.raises(QualityReportError, match='no replacement'):
        build_quality_report(absent, selection())
    assert not absent.exists()
    assert report(saved, manifest())['status']=='unlabeled'


def test_cli_cold_reread_no_overwrite_safe_error_and_no_provider_or_database_initialization(saved, tmp_path, capsys, monkeypatch):
    def forbidden(*args, **kwargs):pytest.fail('CLI attempted network or database initialization')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(Database, '__init__', forbidden)
    choose=tmp_path/'selection.json';choose.write_text(json.dumps(selection()))
    output=tmp_path/'report.json'
    args=['--database',str(saved[1].engine.url.database),'--selection',str(choose),'--output',str(output)]
    before=db_rows(saved[1])
    assert main(args)==0
    assert json.loads(capsys.readouterr().out)['status']=='unlabeled'
    body=output.read_bytes()
    assert json.loads(body)['metrics'] is None
    assert main(args)==1
    assert output.read_bytes()==body and 'PRIVATE' not in capsys.readouterr().err
    choose.write_text('{"SYNTHETIC_PRIVATE_SECRET":')
    assert main([*args[:-1],str(tmp_path/'other.json')])==1
    assert 'SYNTHETIC_PRIVATE_SECRET' not in capsys.readouterr().err
    assert not (tmp_path/'other.json').exists()
    assert db_rows(saved[1])==before


def test_cli_with_explicit_reference_file_outputs_only_declared_comparison(saved, tmp_path, capsys):
    choose=tmp_path/'selection.json';choose.write_text(json.dumps(selection()))
    references=tmp_path/'references.json';references.write_text(json.dumps(manifest(reference(saved))))
    output=tmp_path/'report.json'
    before=db_rows(saved[1])
    assert main(['--database',str(saved[1].engine.url.database),'--selection',str(choose),
                 '--references',str(references),'--output',str(output)])==0
    assert json.loads(capsys.readouterr().out)['labeled_judgments']==8
    data=json.loads(output.read_text())
    assert data['status']=='reference_comparison'
    assert data['metrics']['agreement_all_labeled']=='1.000000'
    assert data['references']['origin_independently_verified'] is False
    assert db_rows(saved[1])==before


def test_unused_reference_ids_are_not_silently_joined_to_a_different_prediction(saved):
    data=report(saved,manifest(reference(saved,'right')))
    assert data['status']=='unlabeled' and data['metrics'] is None
    assert data['references']['unused_reference_evaluation_ids']==['right']


def test_malformed_optional_provenance_is_unknown_without_rewriting_or_hiding_original(saved):
    with saved[1].engine.begin() as db:
        db.exec_driver_sql("UPDATE evaluations SET meta='not-json' WHERE id='left'")
    before=db_rows(saved[1])
    data=report(saved)
    assert data['coverage']['valid_original']==1
    profile=next(g for g in data['groups'] if g['kind']=='provenance')['recorded']
    assert profile['model'] is None
    assert db_rows(saved[1])==before


@pytest.mark.parametrize('predicted,expected,key', [(False,False,'tn'), (False,True,'fn'), (True,False,'fp'), (True,True,'tp')])
def test_critical_confusion_never_becomes_a_total_penalty(saved, predicted, expected, key):
    _,db,checklist,_,_=saved
    with db.transaction() as session:
        answer=full_assessment(checklist);answer.results['critical_errors'].value=predicted
        row=session.get(Evaluation,'left');row.original=answer.model_dump(mode='json');row.original_score=score(checklist,answer)
    case=reference(saved);case['judgments']['critical_errors']['value']=expected
    data=report(saved,manifest(case))
    assert data['metrics']['critical'][key]==1
    assert data['cases'][0]['saved_original_total']==data['cases'][0]['computed_reference_total']=='100.00'
    assert data['metrics']['total']['mean_absolute_error']=='0.000000'


@pytest.mark.parametrize('reference_na', [True,False])
def test_predicted_na_is_distinct_from_false_and_reference_missing(saved, reference_na):
    _,db,checklist,_,_=saved
    with db.transaction() as session:
        answer=full_assessment(checklist);item=answer.results['needs']
        item.disposition='not_applicable';item.value=None
        item.na_reason='SYNTHETIC sufficient initial details under this saved condition'
        row=session.get(Evaluation,'left');row.original=answer.model_dump(mode='json');row.original_score=score(checklist,answer)
    case=reference(saved)
    if not reference_na:case['judgments']['needs']={'disposition':'assessed','value':True}
    data=report(saved,manifest(case))
    key='reference_na_prediction_na' if reference_na else 'reference_applicable_prediction_na'
    assert data['metrics']['na_matrix'][key]==1
    assert data['metrics']['exact_matches']==(8 if reference_na else 7)
    assert data['metrics']['missing_or_unresolved_predictions']==0
    assert data['cases'][0]['computed_reference_total']=='100.00'


def test_custom_scale_reference_total_uses_saved_maximum_and_weight(saved):
    _,_,checklist,_,add=saved
    custom=checklist.model_copy(deep=True)
    custom.criteria[3].scale=[anchor.model_copy(update={'value':Decimal(value)}) for anchor,value in zip(custom.criteria[3].scale[:3],('0','3','5'))]
    add('CUSTOM',rubric=custom,assessment=full_assessment(custom))
    case=reference(saved,'CUSTOM');case['judgments']['consultation']['value']=3
    data=report(saved,manifest(case),selection('CUSTOM'))
    assert data['cases'][0]['computed_reference_total']=='92.00'
    assert data['metrics']['total']['mean_absolute_error']=='8.000000'


@pytest.mark.parametrize('different', ['prompt_hash', 'schema_hash', 'generation', 'response_model'])
def test_provenance_groups_distinguish_hashes_generation_and_recorded_response_models(saved, different):
    client,db,checklist,_,_=saved
    other=client.post('/api/import/json',json=synthetic_payload(source_id='SYNTHETIC_OTHER')).json()['conversation_ids'][0]
    metadata={'provider':'SYNTHETIC','model':'SAME_MODEL','prompt_version':'SAME_VERSION','schema_version':'SAME_SCHEMA',
              'evidence_validation_version':'SAME_VALIDATION','scoring_version':score(checklist,full_assessment(checklist))['scoring_version'],
              'prompt_hash':'a'*64,'schema_hash':'b'*64,'mode':'TEST/MOCK',
              'generation':{'max_output_tokens':6000,'temperature':0,'store':False,'truncation':'disabled'}}
    changed=deepcopy(metadata)
    if different in {'prompt_hash','schema_hash'}:changed[different]='c'*64
    elif different=='generation':changed['generation']['max_output_tokens']=16000
    with db.transaction() as session:
        left=session.get(Evaluation,'left');left.meta=metadata;left.attempts=[{'response_model':'SYNTHETIC_1'}]
        answer=full_assessment(checklist)
        session.add(Evaluation(id='OTHER',conversation_id=other,checklist_id=1,state='succeeded',cache_key='SYNTHETIC',
            original=answer.model_dump(mode='json'),original_score=score(checklist,answer),meta=changed,
            attempts=[{'response_model':'SYNTHETIC_2' if different=='response_model' else 'SYNTHETIC_1'}]))
    data=report(saved,ids=selection('left','OTHER'))
    profiles=[g for g in data['groups'] if g['kind']=='provenance']
    assert len(profiles)==2
    assert all(g['recorded']['request_identity_available'] for g in profiles)


def test_signed_numeric_zero_is_the_same_saved_anchor_not_false_or_na(saved):
    _,db,checklist,_,_=saved
    with db.transaction() as session:
        answer=full_assessment(checklist);answer.results['consultation'].value=0
        row=session.get(Evaluation,'left');row.original=answer.model_dump(mode='json');row.original_score=score(checklist,answer)
    case=reference(saved,consultation={'disposition':'assessed','value':-0.0})
    data=report(saved,manifest(case))
    assert data['metrics']['exact_matches']==1
    assert data['disagreements']==[]
    assert data['metrics']['scale']['mean_absolute_anchor_error']=='0.000000'
