# SPDX-License-Identifier: MPL-2.0
"""Actual outer CLI controls with disclosed pre-freeze scientific-entry inputs.

Input construction previews the real E1 scientific draft before the final
selector is published. All public programme operations then run unmodified.
These exposed populations and formal-entry fixtures establish software behavior.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json

import pytest
from typer.testing import CliRunner

from empirical_lawhood.cli.app import app
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_whole_public import ROOT, copied_whole_inputs


def complete_e1_entry(case, copied, specification):
    """Construct explicit fixture entry inputs before freezing the outer plan."""
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings, compact_preparation
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_assembly import MatrixProgrammeE1AssemblySpecification
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from tests.experiment_entry_support import standard_authoring_for_draft

    implementation = implementation_binding(ROOT)
    root = Path(case.plane.root.contract.canonical_path)
    directory = root / specification.directory / 'derived/e1/produced'
    namespace = case.committed.commitments.namespace
    selection = specification.operations.e1
    assembly = MatrixProgrammeE1AssemblySpecification('assembly.' + namespace + '.e1',
        selection.identity, specification.input_commitments)
    request = copied / 'e1-entry-request'
    request.mkdir()
    sources = ExperimentFileInputSelection('sources.' + namespace + '.e1-entry-review',
        'matrix.programme.e1-input-assembly',
        (ExperimentInputBinding('selection', selection.identity, 'selection.json', len(selection.canonical_bytes())),), ())
    for name, record in (('specification', assembly), ('selection', selection), ('sources', sources)):
        (request / (name + '.json')).write_bytes(record.canonical_bytes())
    review = directory / 'entry-review'
    invoke(copied, 'experiment-derive-inputs', '--input', str(request / 'specification.json'),
        '--sources', str(request / 'sources.json'), '--source-snapshot', str(copied / 'source-snapshot.json'),
        '--environment-id', 'main-locked', '--workers', '4', '--metadata-directory', str(directory),
        '--output-selection', str(review / 'sources.json'))
    target = decode_canonical_bytes((review / 'specification.json').read_bytes(),
        compact_preparation.E1CompactExperimentSpecification, maximum_bytes=None)
    selected = decode_canonical_bytes((review / 'selection.json').read_bytes(),
        compact_preparation.E1CompactExperimentSelectionV2, maximum_bytes=None)
    assert selected.entry_package is selected.formal_methods is None
    assert not (directory / 'selection.json').exists()
    draft, _, _ = compact_preparation._derive(target, selected)
    registrations, registry, codecs = operation_catalog()
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=implementation.observed_git_head,
        implementation_sha256=implementation.code_sources_sha256, qualifications=selected.qualifications,
        known_design_inputs=selected.known_design_inputs, output_codecs=codecs)
    assert compilation.candidate_draft == selected.root
    standard, formal = standard_authoring_for_draft(selected.root, compilation.candidate_context,
        formal_method_capability_key=compact_bindings.KEY)
    selection = replace(selection, entry_package=standard.entry_package,
        formal_methods=formal.formal_methods, formal_source_inventories=formal.source_inventories)
    specification = replace(specification, operations=replace(specification.operations, e1=selection))
    (copied / 'specification.json').write_bytes(specification.canonical_bytes())
    return specification


def invoke(copied, command, *arguments, authoring_dir=None, checker_trust=None):
    global_arguments = ['--project-root', str(ROOT), '--operator-profile', str(copied / 'operator-profile.json'),
        '--catalog-relative-path', 'whole-programme.sqlite3']
    if authoring_dir is None:
        global_arguments += ['--artifact-root-contract', str(copied / 'artifact-root.json')]
    else:
        global_arguments += ['--authoring-dir', str(authoring_dir)]
    if checker_trust is not None:
        global_arguments += ['--approval-checker-trust', str(checker_trust)]
    returned = CliRunner().invoke(app, global_arguments + ['campaign', command, *arguments])
    assert returned.exit_code == 0, returned.output + repr(returned.exception)
    return json.loads(returned.output)


def authored_initial_inputs(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source

    def forbidden(*_args, **_kwargs):
        pytest.fail('metadata/authoring entered native execution')

    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    monkeypatch.setattr(LocalProcessExecutor, 'execute_deadline_free', forbidden)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', forbidden)
    case, copied, specification = copied_whole_inputs(tmp_path)
    specification = complete_e1_entry(case, copied, specification)
    root = Path(case.plane.root.contract.canonical_path)
    directory = root / specification.directory
    review = directory / 'derived/e1/produced/entry-review'
    review_bytes = {path: sha256(path.read_bytes()).hexdigest() for path in review.rglob('*') if path.is_file()}
    execution = ['--source-snapshot', str(copied / 'source-snapshot.json'),
        '--environment-id', 'main-locked', '--workers', '4']
    invoke(copied, 'experiment-derive-inputs', '--input', str(copied / 'specification.json'),
        '--sources', str(copied / 'sources.json'), '--metadata-directory', str(directory),
        '--output-selection', str(directory / 'sources.json'), *execution)
    report = invoke(copied, 'experiment-author', '--input', str(directory / 'specification.json'),
        '--sources', str(directory / 'sources.json'), '--output-dir', str(directory), *execution)
    assert report['state'] == 'IN_PROGRESS'
    assert {path.name for path in (directory / 'children').iterdir()} == {'e1', 'e2', 'train'}
    assert not (root / 'runs').exists()
    assert review_bytes == {path: sha256(path.read_bytes()).hexdigest() for path in review.rglob('*') if path.is_file()}
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_preparation import E1CompactExperimentSelectionV2
    before = decode_canonical_bytes((review / 'selection.json').read_bytes(), E1CompactExperimentSelectionV2, maximum_bytes=None)
    after = decode_canonical_bytes((review.parent / 'selection.json').read_bytes(), E1CompactExperimentSelectionV2, maximum_bytes=None)
    assert after.root == before.root and after.manifest == before.manifest
    assert after.qualifications == before.qualifications and after.source_configs == before.source_configs
    assert after.entry_package == specification.operations.e1.entry_package

    return case, copied, specification, directory


def test_actual_outer_cli_authors_all_initial_children_without_native_entry(tmp_path, monkeypatch):
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans

    case, copied, _specification, directory = authored_initial_inputs(tmp_path, monkeypatch)
    _, draft, _, payloads = load_authored_wave(directory=directory / 'children/e2',
        artifact_writer=case.plane, lazy_payloads=True)
    run, _, _ = _retained_plans(payloads, draft)
    run_path = Path(case.plane.root.contract.canonical_path) / 'runs' / run.run_plan_id
    run_path.mkdir(parents=True)
    report = invoke(copied, 'experiment-read', '--authoring-dir', str(directory))
    assert report['scientific_reconstruction'] == 'off'
    assert report['scientific_qualification'] == 'NOT_ESTABLISHED'
    assert all(not phase['scientific_read_completed'] for phase in report['phases'])
    assert not tuple(run_path.iterdir())


def test_actual_outer_cli_issues_and_reopens_initial_protected_child_without_native_entry(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
        MatrixProgrammeAuthoritySelection, MatrixProgrammeOperationSelection, MatrixResearchProgrammePlan,
    )
    from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from tests.prospective_public_controls import issue_public_child
    from tests.test_matrix_whole_public import _profile

    case, copied, specification, directory = authored_initial_inputs(tmp_path, monkeypatch)
    selected = load_prepared_prospective_experiment(directory=directory / 'children/e1', project_root=ROOT,
        storage_profile=_profile(case.plane), artifact_writer=case.plane)
    control = issue_public_child(copied=copied, writer=case.plane, selected=selected,
        namespace='software.whole.e1', invoke=invoke)
    plan = decode_canonical_bytes((directory / 'matrix-programme.json').read_bytes(),
        MatrixResearchProgrammePlan, maximum_bytes=None)
    authority = MatrixProgrammeAuthoritySelection(control.package_path.relative_to(
        case.plane.root.contract.canonical_path).as_posix(), control.reveal.authority_id)
    operation = MatrixProgrammeOperationSelection('operation.software.whole.e1', plan.identity, (authority,))
    request = copied / 'operation-e1.json'
    request.write_bytes(operation.canonical_bytes())
    report = invoke(copied, 'experiment-read', '--authoring-dir', str(directory),
        '--programme-request', str(request), checker_trust=control.checker_trust)
    assert report['state'] == 'IN_PROGRESS'
    assert not any(row['operational_completion'] for row in report['phases'])
    assert not (Path(case.plane.root.contract.canonical_path) / 'runs').exists()
