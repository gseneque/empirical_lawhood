# SPDX-License-Identifier: MPL-2.0
"""Copied-input and reviewed-entry controls; no native tasks or scientific claims."""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest
from empirical_lawhood.api import application_rc, configuration


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def draft():
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.science import default_chain_config
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
    selected = default_chain_config()
    return rc_recursive_draft(selected, unit_ids=(selected.units[6].unit_id,), include_summary=False)


def test_unsaved_decimal_edits_use_the_same_file_consumer_and_preserve_exact_bytes(tmp_path):
    source = ROOT / 'programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json'
    document = json.loads(source.read_bytes())
    exact = '0.00123456789012345678901234567890123456789'
    document['value']['capacitances_farads'][0] = {'decimal': exact}
    raw = (json.dumps(document, indent=2)+'\n').encode()
    copied = tmp_path/'copied.json'; copied.write_bytes(raw)
    with localcontext() as context:
        context.prec = 6
        assert configuration.validate_configuration_bytes(raw, format='.json', consumer='rc-ladder-model') == configuration.validate_configuration(copied, consumer='rc-ladder-model')
        report = configuration.prepare_configuration_bytes(raw, tmp_path/'new.json', format='.json', consumer='rc-ladder-model')
        record = configuration.load_configuration_bytes((tmp_path/'new.json').read_bytes(), format='.json', consumer='rc-ladder-model')
    assert record.capacitances_farads[0].as_tuple() == Decimal(exact).as_tuple()
    assert copied.read_bytes() == raw and report['authority_granted'] is False
    with pytest.raises(configuration.ConfigurationError, match='new file'):
        configuration.prepare_configuration_bytes(raw, tmp_path/'new.json', format='.json', consumer='rc-ladder-model')


def test_invalid_unsaved_input_and_noneditable_consumer_cannot_prepare(tmp_path):
    with pytest.raises(configuration.ConfigurationError):
        configuration.prepare_configuration_bytes(b'{"schema":', tmp_path/'invalid.json', format='.json', consumer='recursive-inquiry')
    assert not (tmp_path/'invalid.json').exists()
    profile = ROOT/'programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/assumptions.json'
    with pytest.raises(configuration.ConfigurationError, match='only declared editable'):
        configuration.validate_configuration_bytes(profile.read_bytes(), format='.json', consumer='rubisco-kinetic-assumptions')


@pytest.fixture
def inputs(tmp_path, monkeypatch, draft):
    root = tmp_path/'selected';root.mkdir()
    path = root/'copied.json';path.write_bytes(draft.canonical_bytes())
    context = ApplicationContext('rc.test', 'Disclosed RC input control', Path(sys.executable).absolute(),
        project_root=ROOT, input_root=root)
    # Storage contract composition is separately accepted. This fixture exercises
    # actual no-follow input I/O, exact typed config and exclusive publication.
    plane = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path=str(root))))
    monkeypatch.setattr(application_rc, 'application_storage', lambda *a, **k:(ROOT, SimpleNamespace(maximum_parallel_tasks=1),plane))
    return context, path, root


def request(context, operation, **parameters):
    return ApplicationRequest('request', context.context_id, operation, tuple(parameters.items()))


def test_reviewed_original_and_edit_digests_refuse_stale_preparation_without_writes(inputs):
    context,path,root = inputs
    raw = path.read_bytes(); pin=sha256(raw).hexdigest()
    parameters=dict(input=str(path),expected_input_sha256=pin,text=raw.decode(),expected_edit_sha256=pin,output_file=str(root/'prepared.json'))
    result=execute_application(context, request(context,'configuration.prepare',**(parameters|{'expected_edit_sha256':'f'*64})))
    assert result.reason_codes == ('REVIEWED_EDITS_CHANGED',)
    path.write_bytes(raw+b' ')
    result=execute_application(context,request(context,'configuration.prepare',**parameters))
    assert result.reason_codes == ('REVIEWED_INPUT_CHANGED',)
    assert not (root/'prepared.json').exists()


def test_copied_input_and_output_cannot_follow_links_or_escape_selection(inputs, tmp_path):
    context,path,root=inputs
    link=root/'linked.json';link.symlink_to(path)
    assert not execute_application(context,request(context,'configuration.open',input=str(link))).succeeded
    raw=path.read_bytes();pin=sha256(raw).hexdigest()
    result=execute_application(context,request(context,'configuration.prepare',input=str(path),expected_input_sha256=pin,
        text=raw.decode(),expected_edit_sha256=pin,output_file=str(tmp_path/'escape.json')))
    assert result.reason_codes == ('INPUT_DESTINATION_REFUSED',)
    assert not (tmp_path/'escape.json').exists()


def test_config_and_advisory_outputs_refuse_another_device_before_creation(inputs):
    _context,path,root=inputs
    from empirical_lawhood.storage.progress import OperationalProgressReporter
    with pytest.raises(configuration.ConfigurationError,match='new file'):
        configuration.prepare_configuration_bytes(path.read_bytes(),root/'foreign.json',format='.json',
            consumer='recursive-inquiry',expected_parent_device=-1)
    with pytest.raises(OSError,match='storage device'):
        OperationalProgressReporter(root/'progress.json','disclosed.control',expected_parent_device=-1)
    assert not (root/'foreign.json').exists() and not (root/'progress.json').exists()


def test_reviewer_pins_and_worker_selection_are_required_before_handler(inputs, monkeypatch):
    context,path,_root=inputs
    from empirical_lawhood.api import recursive_execution
    monkeypatch.setattr(recursive_execution,'run_recursive_wave',lambda **k:pytest.fail('unreviewed target entered execution'))
    result=execute_application(context,request(context,'recursive.run',directory=str(path.parent),expected_packet_sha256=None))
    assert result.reason_codes == ('INVALID_REVIEW_PIN',)
    result=execute_application(replace(context,maximum_parallel_tasks=2),request(context,'rc.prepare',input=str(path),expected_input_sha256=sha256(path.read_bytes()).hexdigest()))
    assert result.reason_codes == ('WORKER_SELECTION_EXCEEDS_PROFILE',)


def test_authoring_owner_rejects_changed_reviewed_source_before_compilation_or_publication(tmp_path, draft, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as owner
    from empirical_lawhood.execution import recursive_compiler
    from tests.test_rubisco_gas_contrast import _real_plane
    plane=_real_plane(tmp_path/'artifacts')
    monkeypatch.setattr(owner,'implementation_binding',lambda *a,**k:SimpleNamespace(fingerprint=lambda:'a'*64))
    monkeypatch.setattr(recursive_compiler,'compile_recursive_wave',lambda **k:pytest.fail('stale source reached compilation'))
    with pytest.raises(PermissionError,match='reviewed preparation'):
        owner.author_recursive_wave(draft=draft,project_root=ROOT,artifact_writer=plane,
            output_dir=tmp_path/'artifacts/authored',expected_implementation_sha256='b'*64)
    assert not (tmp_path/'artifacts/authored').exists()


def test_execution_owner_rejects_changed_reviewed_packet_before_source_capture_or_task_entry(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_execution as owner
    from empirical_lawhood.storage import run_source_admission
    monkeypatch.setattr(owner,'load_authored_wave',lambda **k:(SimpleNamespace(fingerprint=lambda:'a'*64),None,None,None))
    monkeypatch.setattr(owner,'_retained_plans',lambda *a:pytest.fail('stale packet reached plan admission'))
    monkeypatch.setattr(run_source_admission,'_capture_source',lambda *a:pytest.fail('stale packet reached source entry'))
    with pytest.raises(PermissionError,match='reviewed authoring packet'):
        owner.run_recursive_wave(directory=tmp_path,project_root=ROOT,artifact_writer=None,expected_packet_sha256='b'*64)
