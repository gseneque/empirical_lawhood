# SPDX-License-Identifier: MPL-2.0
"""Scoped CLI authoring and instrumentation; services are explicit software mocks."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def load_cli():
    path=Path(__file__).parents[1]/'scripts/examples/model_free_matrix.py'
    spec=importlib.util.spec_from_file_location('model_free_cli_control',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module,path


def workspace_fixture(module,tmp_path,monkeypatch):
    root=tmp_path/'selected'; scratch=root/'scratch'; scratch.mkdir(parents=True)
    workspace=SimpleNamespace(profile_path=root/'operator-storage.json',artifact_root=root/'artifacts',scratch_root=scratch)
    monkeypatch.setattr(module,'create_local_workspace',lambda *a,**k:workspace)
    monkeypatch.setattr(module,'prepare_investigation',lambda *a,**k:SimpleNamespace(executable=True))
    monkeypatch.setattr(module,'experiment_preparation_report',lambda value:{'executable':value.executable})
    return root,scratch


@pytest.mark.parametrize('operation,creator', [('confirm','create_successor_inputs'),('reanalyse','create_reanalysis_inputs'),
    ('deploy-population', 'create_population_deployment_inputs')])
def test_prepare_only_authenticates_and_authors_successor_without_execution(tmp_path,monkeypatch,operation,creator):
    module,path=load_cli(); root,scratch=workspace_fixture(module,tmp_path,monkeypatch)
    observed=[]
    def make_inputs(**kwargs):
        observed.append(('authenticated_parent',kwargs['parent_directory']))
        return {'specification':str(scratch/'specification.json'),'sources':str(scratch/'sources.json')}
    def author(**kwargs):
        observed.append(('author',kwargs['output_dir']))
        return {'status':'AUTHORED'}
    def no_execute(**kwargs):
        pytest.fail('prepare-only must not execute, read a new outcome, or recover')
    service=SimpleNamespace(author=author,run=no_execute,read=no_execute,recover=no_execute)
    monkeypatch.setattr(module,creator,make_inputs)
    monkeypatch.setattr(module,'create_investigation_service',lambda **kwargs:service)
    metrics=tmp_path/'metrics'/f'{operation}.json'
    assert module.main(['--operation',operation,'--prepare-only','--project-root',str(path.parents[2]),
        '--workspace',str(root),'--definition',str(tmp_path/'definition.json'),'--parent-workspace',str(tmp_path/'parent'),
        '--metrics-json',str(metrics),'--no-progress'])==0
    assert [r[0] for r in observed]==['authenticated_parent','author']
    assert (scratch/'authoring.json').is_file()
    assert not (scratch/'execution.json').exists()
    report=json.loads(metrics.read_text())
    assert report['prepare_only'] is True and report['operation']==operation
    assert report['scientific_result'] is None and report['exit_code']==0
    assert report['operation_elapsed_seconds']>=0


@pytest.mark.parametrize('operation', ('read','execute','recover'))
def test_metrics_hash_exact_existing_readout_without_repeated_scientific_read(tmp_path,monkeypatch,operation):
    module,path=load_cli(); root,scratch=workspace_fixture(module,tmp_path,monkeypatch)
    calls=[]
    scientific={'unicode':'μ','scientific_completion':'COMPLETED','nested':[1,.5]}
    def selected(**kwargs):
        calls.append(operation)
        return {'status':'SUCCEEDED','scientific_result':scientific}
    def unexpected(**kwargs):
        pytest.fail('instrumentation must reuse the already returned readout')
    service=SimpleNamespace(read=selected if operation=='read' else unexpected,
        run=selected if operation=='execute' else unexpected,recover=selected if operation=='recover' else unexpected)
    monkeypatch.setattr(module,'create_investigation_service',lambda **kwargs:service)
    report_path=tmp_path/'metrics.json'
    assert module.main(['--operation',operation,'--project-root',str(path.parents[2]),'--workspace',str(root),
        '--metrics-json',str(report_path),'--no-progress'])==0
    assert calls==[operation]
    report=json.loads(report_path.read_text())
    expected=b'{"nested":[1,0.5],"scientific_completion":"COMPLETED","unicode":"\\u03bc"}\n'
    assert report['scientific_result']['sha256']==sha256(expected).hexdigest()
    assert report['scientific_result']['canonical_json_bytes']==len(expected)
    assert report['scientific_result']['source'].endswith('NO_EXTRA_READ_OR_REPLAY')
    assert 'NOT_ADDITIVE' in report['memory_scope']
    assert 'DO_NOT_VERIFY_NATIVE_CALL_COUNTS' in report['scientific_scope']
    assert json.loads((scratch/'result.json').read_text())['scientific_result']==scientific


def test_metrics_requires_a_fresh_absolute_path_before_workspace_or_service_contact(tmp_path,monkeypatch):
    module,path=load_cli()
    monkeypatch.setattr(module,'create_investigation_service',lambda **kwargs:pytest.fail('invalid metrics path contacted the service'))
    options=['--operation','read','--project-root',str(path.parents[2]),'--workspace',str(tmp_path/'selected')]
    with pytest.raises(SystemExit):
        module.main(options+['--metrics-json','relative.json'])
    used=tmp_path/'used.json'; used.write_text('original')
    with pytest.raises(SystemExit):
        module.main(options+['--metrics-json',str(used)])
    assert used.read_text()=='original'
