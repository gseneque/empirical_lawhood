# SPDX-License-Identifier: MPL-2.0
"""Exact authored TRAIN operands without acquisition or scientific qualification."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.api import matrix_programme_e4_inputs as operands
from empirical_lawhood.api import recursive_authoring
from empirical_lawhood.api.experiment_execution_read import load_development_execution_controls
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
from tests.test_matrix_native_training_public_lifecycle import ROOT, _actual_case, _copied_preparation


@pytest.fixture(scope='module')
def authored_training(tmp_path_factory):
    """Publish the ordinary eleven-task exposed fixture; execute no task."""
    directory = tmp_path_factory.mktemp('unentered-training-operands')
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(LocalProcessExecutor, 'execute',
            lambda *_a, **_kw: pytest.fail('operand control entered a worker'))
        case = _actual_case(directory, patch)
        preparation = _copied_preparation(case, directory / 'copied')
        root = Path(case.plane.root.contract.canonical_path)
        home = root / 'unentered-training'
        report = author_prepared_experiment(preparation=preparation, project_root=ROOT,
            artifact_writer=case.plane, output_dir=home)
        assert report['task_count'] == 11 and report['native_contact'] == 'none'
        packet, run, plan, _, _, _ = load_development_execution_controls(
            directory=home, artifact_writer=case.plane)
        locator = MatrixFiniteDtTrainingLocator(home.relative_to(root).as_posix(), run.run_plan_id,
            ObjectIdentity.from_record(packet.packet_id, packet),
            ObjectIdentity.from_record(plan.execution_plan_id, plan))
        yield SimpleNamespace(case=case, directory=home, locator=locator, packet=packet)
        assert not (root / 'runs' / run.run_plan_id).exists()


def _context(value, writer, *, commitment=None):
    # Only the outer programme directory selection is a disclosed seam. The
    # child, request, packet and both plans come from the real public author.
    selected = value.case.request.input_commitments if commitment is None else commitment
    origin = SimpleNamespace(child_directory=lambda phase: value.directory,
        plan=SimpleNamespace(specification=SimpleNamespace(input_commitments=selected)))
    return MatrixProgrammeProjectionContext(SimpleNamespace(artifact_writer=writer), None, None,
        value.directory.parent, {}, {}, phase_origins={'train': origin})


def test_actual_member_label_differs_from_the_exact_plan_identity(authored_training):
    value = authored_training
    member, = (row for row in value.packet.members if row.filename == 'execution-plan.json')
    assert member.identity.object_id == 'recursive-member.execution-plan'
    assert member.identity.object_id != value.locator.execution_plan.object_id
    assert member.identity.object_fingerprint == value.locator.execution_plan.object_fingerprint
    specification, request = operands._recorded_training_operands(value.case.plane, value.locator)
    assert (specification, request) == (value.case.specification, value.case.request)


def test_publication_writer_reuses_training_only_through_the_owning_read(authored_training, monkeypatch):
    value = authored_training
    with retained_e3_evidence_context(value.case.plane) as read:
        first = operands._recorded_training_operands(value.case.plane, value.locator)
        monkeypatch.setattr(operands, '_read_instance',
            lambda *_a, **_kw: pytest.fail('publication decoded the same TRAIN request again'))
        assert operands._recorded_training_operands(value.case.plane, value.locator) is first
        assert operands._recorded_training_operands(read.writer, value.locator) is first


@pytest.mark.parametrize('mode', ('off', 'full'))
def test_locator_joins_the_same_actual_controls_in_both_modes(authored_training, monkeypatch, mode):
    value = authored_training
    calls = []
    original = recursive_authoring.load_authored_wave

    def full(*args, **kwargs):
        assert mode == 'full', 'default operand consumption reconstructed the TRAIN graph'
        calls.append('full')
        return original(*args, **kwargs)

    monkeypatch.setattr(recursive_authoring, 'load_authored_wave', full)
    with scientific_reconstruction_operation(mode), retained_e3_evidence_context(value.case.plane) as read:
        assert _context(value, read.writer).native_training_locator() == value.locator
    assert calls == (['full'] if mode == 'full' else [])


@pytest.mark.parametrize('changed', ('plan-id', 'plan-hash', 'packet-id', 'run-id'))
def test_foreign_locator_refuses_before_request_consumption(authored_training, monkeypatch, changed):
    value = authored_training
    locator = value.locator
    if changed == 'plan-id':
        locator = replace(locator, execution_plan=replace(locator.execution_plan, object_id='execution.foreign'))
    elif changed == 'plan-hash':
        locator = replace(locator, execution_plan=replace(locator.execution_plan, object_fingerprint='f' * 64))
    elif changed == 'packet-id':
        locator = replace(locator, packet=replace(locator.packet, object_id='packet.foreign'))
    else:
        locator = replace(locator, run_id='run.foreign')
    monkeypatch.setattr(operands, '_read_instance',
        lambda *_a, **_kw: pytest.fail('foreign locator consumed the TRAIN request'))
    with pytest.raises(PermissionError, match='original TRAIN'):
        operands._recorded_training_operands(value.case.plane, locator)


@pytest.mark.parametrize('mode', ('off', 'full'))
def test_original_commitment_substitution_refuses(authored_training, mode):
    value = authored_training
    with scientific_reconstruction_operation(mode), pytest.raises(PermissionError, match='original C publication'):
        _context(value, value.case.plane, commitment=object()).native_training_locator()


@pytest.mark.parametrize('changed', ('execution-plan.json', 'experiment-instance.json', 'access'))
@pytest.mark.parametrize('publishing', (False, True))
def test_cached_operands_keep_final_bytes_and_current_access_guards(authored_training, changed, publishing):
    value = authored_training
    allowed = [True]
    path = value.directory / (changed if changed != 'access' else 'execution-plan.json')
    before = path.read_bytes()

    def current(_manifest):
        if not allowed[0]:
            raise PermissionError('disclosed current TRAIN access revoked')

    try:
        with pytest.raises((ArtifactIdentityConflict, PermissionError)):
            with value.case.plane.read_context(before_member=current) as writer:
                with retained_e3_evidence_context(writer):
                    selected = value.case.plane if publishing else writer
                    operands._recorded_training_operands(selected, value.locator)
                    if changed == 'access':
                        allowed[0] = False
                    else:
                        path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
                    operands._recorded_training_operands(selected, value.locator)
    finally:
        allowed[0] = True
        if changed != 'access':
            path.write_bytes(before)
