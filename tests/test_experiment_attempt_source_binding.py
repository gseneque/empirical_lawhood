# SPDX-License-Identifier: MPL-2.0
"""Retained public preparation preserves closed implementation inputs."""
from hashlib import sha256
import json

import pytest
from typer.testing import CliRunner

from empirical_lawhood.cli.app import app
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_experiment_preparation_public import _copied_input


def _binding(kind):
    if kind == 'recursive':
        sources = (('src/disclosed_software_control.py', 'a' * 64),)
        return RecursiveImplementationBinding(sources, sha256(canonical_json_bytes(sources)).hexdigest(),
            'b' * 64, 'c' * 40, True)
    return ImplementationSourceClosure('source.disclosed-control', SourceClosureKind.CLEAN_GIT_COMMIT,
        'c' * 40, 'a' * 64, 'b' * 64, True)


@pytest.mark.parametrize('kind', ('recursive', 'issued'))
@pytest.mark.parametrize('command', ('experiment-explain', 'experiment-prepare'))
@pytest.mark.parametrize('damaged', (False, True))
def test_retained_preparation_uses_original_typed_source_binding(tmp_path, kind, command, damaged):
    _, specification_path = _copied_input(tmp_path)
    binding = _binding(kind)
    document = binding.to_document()
    if damaged:
        document['value']['code_sources_sha256' if kind == 'recursive' else 'implementation_commit'] = 'd' * 64
    raw = canonical_json_document_bytes(document)
    source = tmp_path / 'implementation.json'
    source.write_bytes(raw)
    attempt = tmp_path / 'retained-attempt'
    output = tmp_path / 'preparation.json'
    args = ['campaign', command, '--input', str(specification_path),
        '--source-snapshot', str(source), '--environment-id', 'software.locked',
        '--workers', '1', '--attempt-dir', str(attempt)]
    if command == 'experiment-prepare':
        args += ['--output', str(output)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == (2 if damaged else 0), result.stdout + result.stderr + repr(result.exception)
    invocation = json.loads((attempt / 'invocation.json').read_bytes())
    row, = (row for row in invocation['inputs'] if row['role'] == 'implementation-snapshot')
    assert row['locator'] == str(source) and row['sha256'] == sha256(raw).hexdigest()
    assert row['bytes'] == len(raw) and row['used_snapshot'] is False
    assert row['identity_scope'] == 'observed_before_operation' and 'retained_file' not in row
    assert source.read_bytes() == raw
    assert not (attempt / 'input-001.json').exists()
    if damaged:
        assert not output.exists() and not invocation['operation_completed']
        assert 'unknown configuration schema' not in result.stderr
        assert ('implementation source digest' if kind == 'recursive' else 'Git SHA-1') in result.stderr
    else:
        report = json.loads(result.stdout)
        assert report['execution']['source_snapshot'] == ObjectIdentity.from_record(
            'recursive-member.implementation', binding).to_document()
        assert report['scientific_authority'] == 'NONE' and not report['scientific_execution_performed']
        assert report['native_contact'] == 'NONE' and not report['executable']
        assert report['qualification'] == 'NOT_ESTABLISHED' and report['dependencies']
        assert invocation['operation_completed']
        assert json.loads((attempt / 'report.json').read_bytes()) == report


def test_retained_source_binding_refuses_undeclared_schema_at_its_owner(tmp_path):
    _, specification_path = _copied_input(tmp_path)
    source = tmp_path / 'implementation.json'
    source.write_bytes(canonical_json_document_bytes({'schema': 'empirical-lawhood/testing/unselected-source',
        'version': '1.0.0', 'value': {}}))
    attempt = tmp_path / 'retained-attempt'
    result = CliRunner().invoke(app, ['campaign', 'experiment-explain', '--input', str(specification_path),
        '--source-snapshot', str(source), '--attempt-dir', str(attempt)])
    assert result.exit_code == 2
    assert 'experiment source snapshot lacks a supported exact implementation record' in result.stderr
    assert not json.loads((attempt / 'invocation.json').read_bytes())['operation_completed']
