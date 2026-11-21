# SPDX-License-Identifier: MPL-2.0
"""Disclosed service selections; no native tasks, live source or qualification."""

from dataclasses import replace
from functools import wraps
from pathlib import Path
import runpy

import pytest

from empirical_lawhood.api.extension_conformance import run_extension_conformance
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate
from empirical_lawhood.execution.extension_conformance import ConformanceCall as Call, ConformanceCase as Case, ConformanceProfile as Profile, ExtensionConformanceSelection, inspect_extension_contracts
from tests.test_knowledge_certificates import disclosed as disclosed, produce


ROOT = Path(__file__).resolve().parents[2]


def selection(name):
    return runpy.run_path(str(ROOT / 'scripts/examples' / (name + '_conformance.py')))['CONFORMANCE_SELECTION']


def execute(selected):
    return run_extension_conformance(selected, source={'fixture': 'disclosed-service-contracts'})


@pytest.mark.parametrize('name', ('continuing_source', 'dependent_assessment', 'knowledge_store'))
def test_editable_profiles_execute_original_owning_calls_and_keep_limits(name):
    selected = selection(name)
    report = execute(selected)
    assert report['status'] == 'PASSED_SELECTED_CHECKS', report
    assert not report['contact_attempts'] and not report['full_installed_lifecycle']
    assert report['scientific_authority'] == 'NONE' and report['qualification'] == 'NOT_ESTABLISHED'
    assert {row['status'] for row in report['checks']} == {'PASSED', 'PASSED_EXPECTED_REFUSAL'}
    if name == 'dependent_assessment':
        assert any(row.get('observed', {}).get('count') == 4 for row in report['checks'])
    elif name == 'continuing_source':
        assert len(report['contracts']['callback_forms']) == 4
    else:
        positive = report['checks'][1]['observed']
        assert positive['count'] == 3 and positive['canonical_census_sha256']


@pytest.mark.parametrize('name', ('continuing_source', 'dependent_assessment', 'knowledge_store'))
def test_profile_cannot_pass_with_only_codec_or_positive_cases(name):
    selected = selection(name)
    report = execute(replace(selected, cases=tuple(case for case in selected.cases if case.refusal_contains is None)))
    assert report['status'] == 'FAILED' and not report['checks']
    assert 'positive case and explicit refusal' in report['failure']['message']


@pytest.mark.parametrize('method', ('require_owner', 'require_actor', 'submit', 'observe'))
def test_wrong_source_method_signature_refuses_before_any_owner_call(method):
    selected = selection('continuing_source')
    calls = []
    def misspelled(*, wrong_argument):
        calls.append('entered')
    port = selected.source_access if method.startswith('require') else selected.effect_ports[0][1]
    setattr(port, method, misspelled)
    report = execute(selected)
    assert report['status'] == 'FAILED' and not report['checks'] and not calls
    assert method in report['failure']['message']


@pytest.mark.parametrize('method', ('dependencies', 'verify'))
def test_wrong_registered_type_callback_signature_refuses_without_invocation(method):
    selected = selection('knowledge_store')
    calls = []
    def invalid(*, wrong_keyword):
        calls.append('entered')
    descriptor = replace(selected.knowledge_types[0], **{method: invalid})
    report = execute(replace(selected, knowledge_types=(descriptor, *selected.knowledge_types[1:])))
    assert report['status'] == 'FAILED' and not report['checks'] and not calls


def test_static_service_inspection_never_calls_effect_or_descriptor_methods():
    for name in ('continuing_source', 'knowledge_store'):
        selected = selection(name)
        report = inspect_extension_contracts(selected)
        assert report['executed_callbacks'] == 0 and report['operations'] == []


@pytest.mark.parametrize('damage', ('profile', 'codec', 'port', 'keyword'))
def test_invalid_later_case_prevents_all_live_validation(damage, monkeypatch):
    from empirical_lawhood.execution import continuing_source
    selected = selection('continuing_source')
    calls = []
    original = continuing_source.require_live_application
    @wraps(original)
    def tracked(*args, **kwargs):
        calls.append('entered')
        return original(*args, **kwargs)
    monkeypatch.setattr(continuing_source, 'require_live_application', tracked)
    if damage == 'profile':
        selected = replace(selected, profile=Profile.KNOWLEDGE_STORE_CONTRACTS)
    elif damage == 'codec':
        selected = replace(selected, imported_record_types=selected.imported_record_types[1:])
    elif damage == 'port':
        selected = replace(selected, effect_ports=(('other', selected.effect_ports[0][1]),))
    else:
        last = selected.cases[-1]
        selected = replace(selected, cases=(*selected.cases[:-1], replace(last,
            arguments={'previous_sequence': 3, 'evnets': last.arguments['events']})))
    report = execute(selected)
    assert report['status'] == 'FAILED' and not calls and not report['contact_attempts']


def test_caught_selected_source_contact_still_fails_the_case(monkeypatch):
    from empirical_lawhood.execution import continuing_source
    selected = selection('continuing_source')
    original = continuing_source.require_live_application
    @wraps(original)
    def contact(*args, **kwargs):
        try:
            selected.effect_ports[0][1].submit(args, b'')
        except PermissionError:
            pass
        return original(*args, **kwargs)
    monkeypatch.setattr(continuing_source, 'require_live_application', contact)
    report = execute(selected)
    assert report['status'] == 'FAILED'
    assert report['checks'][1]['status'] == 'FAILED_CONTACT_ATTEMPT'
    assert report['contact_attempts'] == ['UnavailableEffect.submit'] * 3


def test_dependent_profile_cannot_replace_its_registered_method_or_census():
    selected = selection('dependent_assessment')
    for call in (Call.ASSESSMENT_CONTRACT, Call.ASSESS):
        cases = []
        for case in selected.cases:
            if case.call is call:
                args = dict(case.arguments)
                if call is Call.ASSESSMENT_CONTRACT:
                    args['method'] = replace(args['method'], implementation_sha256='f' * 64)
                else:
                    args['registrations'] = args['registrations'][:-1]
                case = replace(case, arguments=args)
            cases.append(case)
        report = execute(replace(selected, cases=tuple(cases)))
        assert report['status'] == 'FAILED' and len(report['checks']) == 1


def test_portable_profile_uses_original_verifier_and_selected_identity(disclosed):
    expected = produce('unevaluable', 'conformance', disclosed)
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.records.serialization import canonical_json_bytes
    identity = decode_canonical_bytes(canonical_json_bytes(expected['certificate_identity']), ObjectIdentity, maximum_bytes=4096)
    arguments = dict(directory=disclosed.root / 'conformance', artifact_writer=disclosed.plane, expected_certificate=identity)
    selected = ExtensionConformanceSelection('knowledge', 'empirical-lawhood/knowledge/', (),
        imported_record_types=(KnowledgeAssessmentCertificate,), profile=Profile.PORTABLE_CERTIFICATE_READ,
        cases=(Case('certificate.original', Call.CERTIFICATE_READ, arguments, expected),
            Case('certificate.changed', Call.CERTIFICATE_READ,
                {**arguments, 'expected_certificate': replace(identity, object_fingerprint='f' * 64)},
                'ValueError', 'substitutes its exact original record')))
    report = execute(selected)
    assert report['status'] == 'PASSED_SELECTED_CHECKS', report
    observed = report['checks'][1]['observed']['report']
    assert observed['original_disposition'] == 'UNEVALUABLE'
    assert observed['consumer_admission'] == 'NOT_EVALUATED' and observed['authorship'] == 'NOT_ATTESTED'
    for changes in ({'expected_certificate': None}, {'allow_incomplete': True}):
        case = replace(selected.cases[0], arguments={**arguments, **changes})
        refused = execute(replace(selected, cases=(case, selected.cases[1])))
        assert refused['status'] == 'FAILED' and len(refused['checks']) == 1


def test_actual_mount_inspector_keeps_current_checks_inside_nested_contact_guards(tmp_path, monkeypatch):
    import json
    import os
    import subprocess
    from types import SimpleNamespace
    from empirical_lawhood.storage import artifacts
    from empirical_lawhood.execution.local.bounded_process import BoundedProcessResult
    from empirical_lawhood.storage.extension_conformance import ConformanceContactRefused, forbid_conformance_contact

    launched = []
    monkeypatch.setattr(subprocess, 'Popen', lambda command, **options: launched.append((command, options)))
    monkeypatch.setattr(os.path, 'ismount', lambda path: True)
    target = str(tmp_path)
    contract = SimpleNamespace(canonical_path=target, required_mount_path=target)
    observations = [{'source': '/dev/disclosed-first', 'fstype': 'ext4', 'uuid': 'first', 'target': target},
                    {'source': '/dev/disclosed-replaced', 'fstype': 'ext4', 'uuid': 'replaced', 'target': target}]

    def bounded(command, **limits):
        assert limits == dict(timeout_seconds=5, maximum_stdout_bytes=64*1024, maximum_stderr_bytes=16*1024)
        subprocess.Popen(tuple(command), cwd=None, env=None, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, start_new_session=os.name == 'posix')
        return BoundedProcessResult(0, json.dumps({'filesystems': [observations.pop(0)]}).encode(), b'')
    monkeypatch.setattr(artifacts, 'run_bounded_command', bounded)
    inspector = artifacts.LocalFilesystemInspector()
    with forbid_conformance_contact() as outer:
        with forbid_conformance_contact() as inner:
            first, second = inspector.inspect(contract), inspector.inspect(contract)
            assert (first.volume_identity, second.volume_identity) == ('first', 'replaced')
        assert not outer and not inner and len(outer.storage_diagnostics) == len(inner.storage_diagnostics) == 2
        with pytest.raises(ConformanceContactRefused, match='subprocess.Popen'):
            subprocess.Popen(launched[0][0], **launched[0][1])
    assert outer == ['subprocess.Popen'] and len(launched) == 2


@pytest.mark.parametrize('alteration', ('command', 'environment', 'shell'))
def test_mount_diagnostic_scope_does_not_admit_another_process(tmp_path, monkeypatch, alteration):
    import os
    import subprocess
    from types import SimpleNamespace
    from empirical_lawhood.storage import artifacts
    from empirical_lawhood.storage.extension_conformance import ConformanceContactRefused, forbid_conformance_contact

    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('changed diagnostic reached process creation'))
    def changed(command, **limits):
        options = dict(cwd=None, env=None, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, start_new_session=os.name == 'posix')
        if alteration == 'command':
            command = ['python', '-c', 'raise AssertionError("must not execute")']
        elif alteration == 'environment':
            options['env'] = {'PATH': '/disclosed/alternate'}
        else:
            options['shell'] = True
        subprocess.Popen(tuple(command), **options)
    monkeypatch.setattr(artifacts, 'run_bounded_command', changed)
    with forbid_conformance_contact() as contacts:
        with pytest.raises((ConformanceContactRefused, artifacts.ExternalRootUnavailable)):
            artifacts.LocalFilesystemInspector().inspect(SimpleNamespace(
                canonical_path=str(tmp_path), required_mount_path=str(tmp_path)))
    assert contacts == ['subprocess.Popen'] and not contacts.storage_diagnostics
