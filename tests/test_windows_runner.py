"""Contract/negative controls; real Windows execution has separate live evidence."""
import importlib.util
import io
import json
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/windows_runner.py"
spec = importlib.util.spec_from_file_location("windows_runner", HELPER)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    vmx = tmp_path / 'VM with spaces.vmx'
    vmx.write_text('displayName = "Test"\n')
    profile = {'schema_version': 1, 'vm': {'vmx_path': str(vmx)},
               'guest': {'os_arch': 'ARM64'},
               'runner': {'id': 7, 'name': 'chosen', 'labels': ['invocation-label'],
                          'scope_type': 'repository', 'scope_url': 'https://github.com/o/r'}}
    runner = {'id': 7, 'name': 'chosen', 'status': 'online', 'busy': False,
              'labels': [{'name': 'invocation-label'}]}
    monkeypatch.setattr(w.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=0, stdout=f'Total running VMs: 1\n{vmx}\n'))
    class API:
        def __init__(self): self.calls = []
        def remaining(self): return 10
        def pages(self, endpoint, key): return [runner]
        def api(self, endpoint, **kwargs):
            self.calls.append((endpoint, kwargs))
            if '/commits/' in endpoint: return {'sha': 'a'*40}
            if '/workflows/' in endpoint: return {'id': 1, 'state': 'active', 'path': '.github/workflows/diagnostic.yml'}
            return {'full_name': 'o/r'}
    args = SimpleNamespace(repository='o/r', architecture='ARM64', vmrun='/vmrun',
                           receipt=str(tmp_path/'receipt.json'), workflow='diagnostic.yml', ref='branch',
                           selection=None, dry_run=False, yes=True)
    return profile, runner, API(), args


@pytest.mark.parametrize('busy,status,expected', [(False,'online','ready'),(True,'online','busy'),(False,'offline','offline')])
def test_survey_readiness_is_observation_only(fixture, busy, status, expected):
    profile, runner, api, _ = fixture
    runner.update(busy=busy, status=status)
    assert w.survey(profile,'o/r','ARM64',api,'/vmrun')['state'] == expected
    assert all(not kwargs for _, kwargs in api.calls)


def test_architecture_mismatch_cannot_dispatch(fixture):
    profile, _, api, args = fixture
    args.architecture='X64'
    with pytest.raises(w.Failure, match='incompatible'):
        w.dispatch(args,api,profile)
    assert not Path(args.receipt).exists()


def test_missing_registration_is_not_offline(fixture):
    profile, _, api, _ = fixture
    api.pages=lambda *_: []
    assert w.survey(profile,'o/r','ARM64',api,'/vmrun')['state']=='unregistered'


@pytest.mark.parametrize('field,value', [('name','different'),('labels',[])])
def test_changed_identity_or_labels_refused(fixture,field,value):
    profile, runner, api, _ = fixture
    runner[field]=value
    with pytest.raises(w.Failure): w.survey(profile,'o/r','ARM64',api,'/vmrun')


def test_power_and_online_identity_conflict_refused(fixture,monkeypatch):
    profile, _, api, _ = fixture
    monkeypatch.setattr(w.subprocess,'run',lambda *_a,**_k: SimpleNamespace(returncode=0,stdout='Total running VMs: 0\n'))
    with pytest.raises(w.Failure,match='online while'): w.survey(profile,'o/r','ARM64',api,'/vmrun')


def test_private_credential_configuration_is_rejected(fixture,tmp_path):
    profile, _, _, _ = fixture
    profile['credentials']={'password':'dummy-test-secret'}
    path=tmp_path/'profile.json';path.write_text(json.dumps(profile))
    with pytest.raises(w.Failure,match='secret-free'): w.handoff(path,'o/r')


def test_scope_mismatch_is_rejected_before_network(fixture,tmp_path):
    profile, _, _, _ = fixture
    path=tmp_path/'profile.json';path.write_text(json.dumps(profile))
    with pytest.raises(w.Failure,match='exact configured'): w.handoff(path,'other/repo')


def test_dry_run_writes_nothing_and_never_posts(fixture):
    profile, _, api, args = fixture;args.dry_run=True
    assert w.dispatch(args,api,profile)['dry_run']
    assert not Path(args.receipt).exists()
    assert not any(k.get('method')=='POST' for _,k in api.calls)


def test_intent_is_durable_before_ambiguous_dispatch(fixture):
    profile, _, api, args = fixture
    original=api.api
    def call(endpoint,**kwargs):
        if kwargs.get('method')=='POST':
            assert json.loads(Path(args.receipt).read_text())['status']=='dispatch_intent'
            raise w.Failure('request_timeout','uncertain')
        return original(endpoint,**kwargs)
    api.api=call
    with pytest.raises(w.Failure,match='uncertain'): w.dispatch(args,api,profile)
    with pytest.raises(w.Failure,match='existing invocation'): w.dispatch(args,api,profile)


def test_receipt_reservation_never_overwrites_another_invocation(tmp_path):
    path=tmp_path/'receipt.json'
    w.write_json(path,{'invocation':'first'},reserve=True)
    with pytest.raises(w.Failure,match='another invocation'): w.write_json(path,{'invocation':'second'},reserve=True)
    assert json.loads(path.read_text())['invocation']=='first'


def evidence():
    receipt={'schema_version':1,'repository':'o/r','workflow_id':2,'invocation':'c'*32,
             'runner_id':7,'runner_name':'chosen','architecture':'ARM64','commit':'a'*40,
             'inputs':{'test_ids':'["test-one"]'},'run_id':11,'run_attempt':1}
    report={'schema_version':1,'invocation':'c'*32,'runner_name':'chosen','architecture':'ARM64',
            'commit':'a'*40,'is_administrator':False,'run_id':11,'run_attempt':1,
            'operating_system':'Windows','native_architecture':'ARM64','process_architecture':'ARM64',
            'tests':[{'id':'test-one','status':'passed'}],'status':'passed'}
    job={'id':12,'name':'Windows diagnostic','runner_id':7,'runner_name':'chosen',
         'status':'completed','conclusion':'success','html_url':'https://example.test/job'}
    return receipt,report,job


@pytest.mark.parametrize('key,value',[('commit','b'*40),('runner_name','other'),('run_attempt',2),
                                    ('native_architecture','X64'),('process_architecture','X64'),
                                    ('operating_system','Linux'),('is_administrator',True)])
def test_report_cannot_substitute_identity_or_platform(key,value):
    receipt,report,job=evidence();report[key]=value
    with pytest.raises(w.Failure): w.validate_report(report,receipt,job)


@pytest.mark.parametrize('tests',[[],[{'id':'other','status':'passed'}],
                                [{'id':'test-one','status':'passed'},{'id':'test-one','status':'passed'}]])
def test_zero_wrong_or_duplicate_tests_are_not_a_pass(tests):
    receipt,report,job=evidence();report['tests']=tests
    with pytest.raises(w.Failure): w.validate_report(report,receipt,job)


def test_failure_is_verified_evidence_without_becoming_success():
    receipt,report,job=evidence()
    report.update(status='failed',tests=[{'id':'test-one','status':'failed'}]);job['conclusion']='failure'
    assert w.validate_report(report,receipt,job)==('failed',1)


def test_recollection_invalidates_success_when_attempt_changes(tmp_path):
    receipt,_,_=evidence()
    receipt.update(evidence_verified=True,diagnostic_outcome='passed',tests_executed=1)
    path=tmp_path/'receipt.json';path.write_text(json.dumps(receipt))
    run={'id':11,'display_title':'Windows diagnostic '+'c'*32,'run_attempt':2}
    api=SimpleNamespace(pages=lambda *_:[run])
    with pytest.raises(w.Failure,match='rerun'): w.collect(SimpleNamespace(receipt=str(path),repository='o/r'),api)
    saved=json.loads(path.read_text())
    assert saved['evidence_verified'] is False
    assert 'diagnostic_outcome' not in saved


def test_collect_saves_failed_job_log_before_missing_artifact(tmp_path):
    receipt,_,job=evidence();job['conclusion']='failure'
    path=tmp_path/'receipt.json';path.write_text(json.dumps(receipt))
    run={'id':11,'display_title':'Windows diagnostic '+'c'*32,'run_attempt':1,
         'head_sha':'a'*40,'html_url':'https://example.test/run','status':'completed'}
    def pages(_,key):return {'workflow_runs':[run],'jobs':[job],'artifacts':[]}[key]
    api=SimpleNamespace(pages=pages,api=lambda *_a,**_k:b'failed-job-log')
    with pytest.raises(w.Failure,match='artifact'):w.collect(SimpleNamespace(receipt=str(path),repository='o/r'),api)
    assert path.with_suffix('.job.log').read_bytes()==b'failed-job-log'
    assert json.loads(path.read_text())['conclusion']=='failure'


def test_complete_collection_binds_report_job_and_attempt(tmp_path):
    receipt,report,job=evidence()
    path=tmp_path/'receipt.json';path.write_text(json.dumps(receipt))
    run={'id':11,'display_title':'Windows diagnostic '+'c'*32,'run_attempt':1,
         'head_sha':'a'*40,'html_url':'https://example.test/run','status':'completed'}
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w') as zipped:zipped.writestr('windows-diagnostic.json',json.dumps(report))
    def pages(_,key):return {'workflow_runs':[run],'jobs':[job],
                            'artifacts':[{'id':10,'name':'windows-diagnostic-'+'c'*32,'expired':False}]}[key]
    def api(endpoint,**kwargs):
        if endpoint.endswith('/zip'):return archive.getvalue()
        if endpoint.endswith('/logs'):return b'test-one passed'
        return run
    result=w.collect(SimpleNamespace(receipt=str(path),repository='o/r'),SimpleNamespace(pages=pages,api=api))
    assert result['evidence_verified'] and result['tests_executed']==1


def test_api_subprocess_timeout_is_bounded_and_does_not_repost(monkeypatch):
    monkeypatch.setattr(w.shutil,'which',lambda _: '/gh')
    calls=[]
    def run(args,**kwargs):
        calls.append((args,kwargs));raise subprocess.TimeoutExpired(args,kwargs['timeout'])
    monkeypatch.setattr(w.subprocess,'run',run)
    api=w.GitHub('/gh',10)
    with pytest.raises(w.Failure,match='uncertain'):api.api('repos/o/r/test',method='POST',body={})
    assert len(calls)==1 and 0 < calls[0][1]['timeout'] <= 10


@pytest.mark.parametrize('key', ['api_key', 'client_secret', 'cookie', 'authorization', 'accessKey'])
def test_common_secret_keys_are_rejected_recursively(fixture, tmp_path, key):
    profile, _, _, _ = fixture
    profile['observations'] = [{'extra': {key: 'fixture-secret'}}]
    path = tmp_path/'handoff.json'
    path.write_text(json.dumps(profile))
    with pytest.raises(w.Failure, match='secret-free'):
        w.handoff(path, 'o/r')


def test_label_drift_or_nonexclusive_routing_cannot_dispatch(fixture):
    profile, runner, api, args = fixture
    runner['labels'].append({'name': 'unexpected'})
    with pytest.raises(w.Failure, match='labels'):
        w.dispatch(args, api, profile)
    runner['labels'].pop()
    api.pages = lambda *_: [runner, dict(runner, id=8, name='other')]
    with pytest.raises(w.Failure, match='exclusive'):
        w.dispatch(args, api, profile)
    assert not Path(args.receipt).exists()
    assert not any(kw.get('method') == 'POST' for _, kw in api.calls)


def test_first_collection_cannot_accept_a_rerun(tmp_path):
    receipt, _, _ = evidence()
    del receipt['run_id'], receipt['run_attempt']
    path = tmp_path/'receipt.json'
    path.write_text(json.dumps(receipt))
    run = {'id': 11, 'display_title': 'Windows diagnostic '+'c'*32, 'run_attempt': 2}
    with pytest.raises(w.Failure, match='rerun'):
        w.collect(SimpleNamespace(receipt=str(path), repository='o/r'), SimpleNamespace(pages=lambda *_: [run]))
    assert json.loads(path.read_text())['evidence_verified'] is False


@pytest.mark.parametrize('wrong_runner', [False, True])
def test_oversized_failed_log_is_saved_even_for_wrong_runner(tmp_path, monkeypatch, wrong_runner):
    receipt, _, job = evidence()
    job.update(conclusion='failure', runner_id=8 if wrong_runner else 7)
    path = tmp_path/'receipt.json'
    path.write_text(json.dumps(receipt))
    run = {'id': 11, 'display_title': 'Windows diagnostic '+'c'*32, 'run_attempt': 1,
           'head_sha': 'a'*40, 'html_url': 'https://example.test/run', 'status': 'completed'}
    monkeypatch.setattr(w.shutil, 'which', lambda _: '/gh')
    raw = b'failed log\n' + b'x' * (17 * w.MAX_JSON)
    monkeypatch.setattr(w.subprocess, 'run', lambda *_a, **_k: SimpleNamespace(returncode=0, stdout=raw))
    api = w.GitHub('/gh', 10)
    api.pages = lambda _, key: {'workflow_runs': [run], 'jobs': [job], 'artifacts': []}[key]
    with pytest.raises(w.Failure, match='different runner' if wrong_runner else 'artifact'):
        w.collect(SimpleNamespace(receipt=str(path), repository='o/r'), api)
    saved = json.loads(path.read_text())
    assert path.with_suffix('.job.log').read_bytes() == raw[:16*w.MAX_JSON]
    assert saved['job_log_truncated'] is True and saved['evidence_verified'] is False


def test_log_publication_cannot_follow_a_raced_symlink(tmp_path, monkeypatch):
    receipt, _, job = evidence()
    path = tmp_path/'receipt.json'
    path.write_text(json.dumps(receipt))
    target = tmp_path/'unrelated-file'
    target.write_bytes(b'preserve this file')
    log = path.with_suffix('.job.log')
    run = {'id': 11, 'display_title': 'Windows diagnostic '+'c'*32, 'run_attempt': 1,
           'head_sha': 'a'*40, 'html_url': 'https://example.test/run', 'status': 'completed'}
    original = Path.is_symlink
    raced = False
    def is_symlink(candidate):
        nonlocal raced
        if candidate == log and not raced:
            raced = True
            candidate.symlink_to(target)
            return False  # The replacement raced the completed check.
        return original(candidate)
    monkeypatch.setattr(Path, 'is_symlink', is_symlink)
    api = SimpleNamespace(pages=lambda _, key: {'workflow_runs': [run], 'jobs': [job], 'artifacts': []}[key],
                          api=lambda *_a, **_k: b'private job log')
    with pytest.raises(w.Failure, match='artifact'):
        w.collect(SimpleNamespace(receipt=str(path), repository='o/r'), api)
    assert target.read_bytes() == b'preserve this file'
    assert not log.is_symlink() and log.read_bytes() == b'private job log'
    assert log.stat().st_mode & 0o777 == 0o600
