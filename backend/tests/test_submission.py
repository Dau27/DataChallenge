"""Synthetic stored-result fixtures; no model call or independent accuracy claim."""
from copy import deepcopy
import json
from pathlib import Path
import socket

import pytest

from backend.app.db import ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import Assessment, Checklist, content_hash
from backend.app.services.scoring import score
from backend.app.services.submission import (
    CRITERIA, SubmissionError, build_submission, read_submission, validate_saved_submission, validate_submission,
)
from backend.tests.conftest import full_assessment
from backend.tests.test_saved_inspection import db_rows
from scripts.export_submission import main


@pytest.fixture
def batch(tmp_path, checklist):
    db = Database(tmp_path / 'SYNTHETIC.sqlite3')
    assessment = full_assessment(checklist, 'm0003')
    calculated = score(checklist, assessment, ['m0001','m0002','m0003'])
    with db.transaction() as session:
        session.add(ChecklistVersion(id=1, content_hash=content_hash(checklist), snapshot=checklist.model_dump(mode='json')))
        session.flush()
        for i in range(10):
            source_id = f'SYNTHETIC_{i:02d}'
            snapshot = {'conversation_id':source_id, 'language':'EN', 'channel':'agent chat', 'audio_url':None,
                'transcript':[{'id':'m0001','speaker':'client','timestamp':'00:00','text':'SYNTHETIC question'},
                    {'id':'m0002','speaker':'bot','timestamp':'00:01','text':'SYNTHETIC context'},
                    {'id':'m0003','speaker':'operator','timestamp':'00:02','text':'SYNTHETIC answer'}]}
            session.add(Conversation(id=f'source_{i}',group_id='SYNTHETIC_TEST_ONLY',source_id=source_id,revision=1,
                content_hash=content_hash(snapshot),snapshot=snapshot))
            session.flush()
            session.add(Evaluation(id=f'run_{i}',conversation_id=f'source_{i}',checklist_id=1,cache_key='SYNTHETIC',
                state='succeeded',completeness='complete',original=assessment.model_dump(mode='json'),
                effective=assessment.model_dump(mode='json'),original_score=calculated,effective_score=calculated,
                # Represents the saved-LIVE metadata contract, entirely synthetic in this test.
                meta={'model':'SYNTHETIC_MODEL','mode':'LIVE','provider':'openai-responses'},attempts=[],
                created_at='2026-01-01T00:00:00Z'))
    yield db, checklist
    db.engine.dispose()


def build(batch, **kwargs):
    return build_submission(batch[0].engine.url.database,'SYNTHETIC_TEST_ONLY','prod','Vector Field',**kwargs)


def test_build_maps_ids_raw_anchors_full_transcript_positions_and_preserves_db(batch, monkeypatch):
    before = db_rows(batch[0])
    def forbidden(*args,**kwargs):
        pytest.fail('Submission export attempted database initialization or network')
    monkeypatch.setattr(Database,'__init__',forbidden)
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    packet = build(batch)
    assert packet['model'] == {'mode':'external_api','name':'SYNTHETIC_MODEL'}
    assert packet['schema_version']=='1.0' and packet['team_name']=='Vector Field'
    first = packet['results'][0]
    assert first['conversation_id']=='SYNTHETIC_00' and first['score']=={'final_score':100.0,'critical_flag':False}
    assert [c['criterion_id'] for c in first['criteria']]==list(CRITERIA.values())
    assert all(c['evidence_turns']==[3] for c in first['criteria'])
    assert first['criteria'][5]['value']==10
    assert db_rows(batch[0])==before


def test_effective_na_critical_review_and_ranges_use_same_weighting_without_rewriting_original(batch):
    db, checklist = batch
    with db.transaction() as session:
        run = session.get(Evaluation,'run_0')
        changed = deepcopy(run.effective)
        changed['results']['needs'].update(disposition='not_applicable',value=None,na_reason='SYNTHETIC initially sufficient')
        changed['results']['identification'].update(disposition='not_applicable',value=None,na_reason='SYNTHETIC general question')
        changed['results']['consultation']['value']=15
        changed['results']['dialogue_management']['value']=7
        changed['results']['critical_errors']['value']=True
        changed['results']['contact']['evidence']=[{'kind':'support','start_message_id':'m0001','end_message_id':'m0003'},
            {'kind':'context','start_message_id':'m0002','end_message_id':'m0003'}]
        run.effective=changed
        run.effective_score=score(checklist,Assessment.model_validate(changed),['m0001','m0002','m0003'])
    first = build(batch)['results'][0]
    assert first['score']=={'final_score':85.38,'critical_flag':True}
    assert first['criteria'][1]['value'] is None and 'N/A:' in first['criteria'][1]['rationale']
    assert first['criteria'][0]['evidence_turns']==[1,2,3]
    with db.sessions() as session:
        assert session.get(Evaluation,'run_0').original_score['total']=='100.00'


@pytest.mark.parametrize('problem',['unresolved','failed','missing','bad_score','bad_evidence','bad_model','mock'])
def test_incomplete_records_stay_present_as_errors_without_fabricated_totals(batch,problem):
    db, checklist = batch
    with db.transaction() as session:
        run=session.get(Evaluation,'run_0')
        if problem=='missing':
            session.delete(run)
        elif problem=='failed':
            run.state='failed'
        elif problem=='bad_score':
            changed=deepcopy(run.effective_score);changed['total']='0.00';run.effective_score=changed
        elif problem=='bad_model':
            run.meta={'model':'https://example.invalid/private?token=hidden'}
        elif problem=='mock':
            run.meta={**run.meta,'mode':'TEST/MOCK'}
        else:
            changed=deepcopy(run.effective)
            if problem=='unresolved':
                changed['results']['contact'].update(disposition='needs_review',value=None,review_reason='SYNTHETIC unclear recording')
            else:
                changed['results']['contact']['evidence'][0]['start_message_id']='missing'
            run.effective=changed
            if problem=='unresolved':
                run.effective_score=score(checklist,Assessment.model_validate(changed),['m0001','m0002','m0003'])
    rows=build(batch)['results']
    assert len(rows)==10
    assert rows[0]['status']=='error' and rows[0]['criteria']==[] and rows[0]['score'] is None and rows[0]['error']
    assert sum(r['status']=='ok' for r in rows)==9


def test_latest_failure_is_not_hidden_by_an_older_success_and_explicit_selection_can_freeze_runs(batch):
    db,_=batch
    with db.transaction() as session:
        session.add(Evaluation(id='new_failure',conversation_id='source_0',checklist_id=1,cache_key='SYNTHETIC',state='failed',
            meta={'model':'SYNTHETIC_NEW_MODEL'},attempts=[],created_at='2026-01-02T00:00:00Z'))
    automatic=build(batch)
    assert automatic['results'][0]['status']=='error'
    assert 'SYNTHETIC_NEW_MODEL' not in automatic['model']['name']  # No recorded request for this failed job.
    frozen=build(batch,selection=[f'run_{i}' for i in range(10)])
    assert all(r['status']=='ok' for r in frozen['results'])
    assert frozen['model']['name']=='SYNTHETIC_MODEL'


def test_failed_recorded_requests_disclose_the_attempted_model_without_inventing_a_score(batch):
    db,_=batch
    with db.transaction() as session:
        run=session.get(Evaluation,'run_0');run.state='failed'
        run.meta={'model':'SYNTHETIC_ATTEMPTED_MODEL'}
        run.attempts=[{'number':1,'status':'error'}]
    packet=build(batch)
    assert packet['results'][0]['status']=='error'
    assert 'SYNTHETIC_ATTEMPTED_MODEL' in packet['model']['name']


def test_latest_source_revision_does_not_reuse_an_older_assessment(batch):
    db,_=batch
    with db.transaction() as session:
        old=session.get(Conversation,'source_0')
        session.add(Conversation(id='revised',group_id=old.group_id,source_id=old.source_id,revision=2,
            content_hash='SYNTHETIC_NEW_HASH',snapshot=deepcopy(old.snapshot)))
    assert build(batch)['results'][0]['status']=='error'
    with pytest.raises(SubmissionError):
        build(batch,selection=[f'run_{i}' for i in range(10)])


@pytest.mark.parametrize('selection', [['run_0']*10,['absent']+[f'run_{i}' for i in range(1,10)]])
def test_bad_explicit_selections_are_not_guessed_or_silently_deduplicated(batch,selection):
    with pytest.raises(SubmissionError):build(batch,selection=selection)


def test_missing_group_count_or_model_and_incompatible_rubric_fail_before_output(batch,tmp_path):
    db,_=batch
    with pytest.raises(SubmissionError):build_submission(db.engine.url.database,'ABSENT','prod','Vector Field')
    with pytest.raises(SubmissionError):build_submission(db.engine.url.database,'SYNTHETIC_TEST_ONLY','dev','Vector Field')
    with db.transaction() as session:
        for run in session.query(Evaluation):run.meta={}
    with pytest.raises(SubmissionError,match='model provenance'):build(batch)
    with db.transaction() as session:
        version=session.get(ChecklistVersion,1);rubric=deepcopy(version.snapshot)
        rubric['criteria'][0]['weight']=11;version.snapshot=rubric
    with pytest.raises(SubmissionError,match='weights'):build(batch)


@pytest.mark.parametrize('problem',['duplicate_id','internal_id','wrong_id','bool_number','weighted_anchor','contact_na',
    'zero_index','operator_only_index','boolean_index','critical_mismatch','string_total','wrong_total','unknown_status',
    'error_score','duplicate_criterion','empty_reason','schema_number','extra_field','infinite_total','huge_total','bad_model_mode'])
def test_validator_rejects_submission_contract_corruption(batch,problem):
    packet=build(batch);row=packet['results'][0];criterion=row['criteria'][0]
    if problem=='duplicate_id':packet['results'][1]['conversation_id']=row['conversation_id']
    elif problem=='internal_id':row['conversation_id']='source_0'
    elif problem=='wrong_id':row['criteria'][1]['criterion_id']='needs'
    elif problem=='bool_number':criterion['value']=1
    elif problem=='weighted_anchor':row['criteria'][5]['value']=10.5
    elif problem=='contact_na':criterion['value']=None
    elif problem=='zero_index':criterion['evidence_turns']=[0]
    elif problem=='operator_only_index':criterion['evidence_turns']=[4]
    elif problem=='boolean_index':criterion['evidence_turns']=[True]
    elif problem=='critical_mismatch':row['score']['critical_flag']=True
    elif problem=='string_total':row['score']['final_score']='100.00'
    elif problem=='wrong_total':row['score']['final_score']=50
    elif problem=='unknown_status':row['status']='needs_review'
    elif problem=='error_score':row.update(status='error',criteria=[],error='SYNTHETIC error')
    elif problem=='duplicate_criterion':row['criteria'][1]['criterion_id']='contact'
    elif problem=='empty_reason':criterion['rationale']=' '
    elif problem=='schema_number':packet['schema_version']=1.0
    elif problem=='extra_field':packet['api_key']='SYNTHETIC_HIDDEN'
    elif problem=='infinite_total':row['score']['final_score']=float('inf')
    elif problem=='huge_total':row['score']['final_score']=10**500
    elif problem=='bad_model_mode':packet['model']['mode']=[]
    with pytest.raises(SubmissionError):
        validate_submission(packet,{f'SYNTHETIC_{i:02d}':3 for i in range(10)},'prod','Vector Field')


def test_rationale_redacts_credentials_and_recording_signatures(batch):
    db,_=batch
    secret='sk-'+'X'*32
    with db.transaction() as session:
        run=session.get(Evaluation,'run_0');changed=deepcopy(run.effective)
        changed['results']['contact']['explanation']=f'SYNTHETIC {secret} https://example.invalid/a?sig=PRIVATE_TOKEN'
        run.effective=changed
    rationale=build(batch)['results'][0]['criteria'][0]['rationale']
    assert secret not in rationale and 'PRIVATE_TOKEN' not in rationale and '[REDACTED' in rationale


def test_cli_atomic_export_validate_utf8_and_refuses_overwrite(batch,tmp_path,capsys):
    database=batch[0].engine.url.database
    base=['--database',database,'--group-id','SYNTHETIC_TEST_ONLY','--split','prod','--team-name','Vector Field']
    target=tmp_path/'new'/'results.json'
    assert main(['export',*base,'--output',str(target)])==0
    summary=json.loads(capsys.readouterr().out)
    assert summary['ok'] is True and summary['ok_records']==10 and summary['error_records']==0
    body=target.read_bytes();assert not body.startswith(b'\xef\xbb\xbf')
    assert json.loads(body)['team_name']=='Vector Field'
    assert main(['validate',*base,'--file',str(target)])==0
    assert main(['export',*base,'--output',str(target)])==1
    assert target.read_bytes()==body and not list(target.parent.glob('.cqa-results-*.tmp'))


@pytest.mark.parametrize('body',['{"a":1,"a":2}','{"x":NaN}','{"x":Infinity}','not json','\ufeff{}'])
def test_strict_json_reader_rejects_duplicate_nonfinite_or_invalid_utf8_json(tmp_path,body):
    path=tmp_path/'invalid.json';path.write_text(body,encoding='utf-8')
    with pytest.raises(SubmissionError):read_submission(path)


def test_no_missing_database_is_created(tmp_path):
    path=tmp_path/'absent.sqlite3'
    with pytest.raises(SubmissionError):build_submission(path,'TEST','prod','Vector Field')
    assert not path.exists()
