# SPDX-License-Identifier: MPL-2.0
"""Real input-publication readers with synthetic metadata, no issue or worker runs.

Recovery/grant metadata below are explicit unit doubles. They establish no issued
execution or qualification. Actual guarded files, manifest validation and reader
identity/census predicates remain in use; no input port or TRAIN data is read.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import current_task_custody as current
from empirical_lawhood.api import recursive_qualified_parents as parents
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactStreamWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityRequirement
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificStage
from empirical_lawhood.runtime.recovery import RecoveryTerminalAttempt, RecoveryTerminalDisposition
from tests.runtime_platform.test_execution_scheduler import _plane

RUN = 'run.synthetic.custody-readers'
LOGICAL = 'input.synthetic.control'


@dataclass(frozen=True, slots=True)
class Control(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/custody-reader-control'
    control_id: str = 'control.synthetic'
    value: str = 'exposed metadata only'


@dataclass(frozen=True, slots=True)
class GrantMetadata(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/custody-reader-grant-metadata'
    authorization_id: str = 'authorization.synthetic'
    authority_id: str = 'authority.synthetic'


class Unread:
    bytes_read = 0

    def read(self, size=-1):
        pytest.fail('input custody metadata reader consumed a worker/TRAIN port')

    def close(self):
        pass


def _write(plane, layout, *, logical=LOGICAL, record=None, lineage=()):
    record = record or Control()
    raw = record.canonical_bytes()
    root = f'runs/{RUN}/inputs'
    token = sha256(logical.encode()).hexdigest()
    relative = f'{root}/{logical}.bin' if layout == 'legacy' else f'{root}/{token[:2]}/{token}.bin'
    scope = root if layout == 'legacy' else f'{root}/{token[:2]}'
    return plane.write_stream(ArtifactStreamWriteRequest(
        logical_artifact_id=logical, relative_path=relative,
        publication_scope_id=f'campaign-inputs.{RUN}' + ('' if layout == 'legacy' else '.' + token[:2]),
        publication_scope_relative_root=scope, payload_schema=record.SCHEMA,
        profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', chunks=(raw,),
        maximum_bytes=len(raw), maximum_chunk_bytes=len(raw), expected_size_bytes=len(raw),
        expected_physical_sha256=sha256(raw).hexdigest(), visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in lineage),
        outcome_access=OutcomeAccess.OUTCOME_BLIND, lineage_parents=lineage,
    ))


def _selected(publication):
    logical, material = publication.logical, publication.materialization
    spec = ExternalInputSpec('input.control', logical.logical_artifact_id, logical.content_sha256,
        logical.payload_schema, logical.media_type, material.size_bytes,
        logical.visibility_ceiling, logical.outcome_access, None)
    binding = WorkerInputBinding.from_verified(VerifiedArtifactInput(logical, material), kind=WorkerInputKind.EXTERNAL)
    context = SimpleNamespace(run_id=RUN, task_id='task.synthetic', dependency_receipts=(),
        dependency_receipt_ids=(), input_bindings=(binding,), input_ports=(WorkerInputPort(binding, Unread()),))
    config = CapabilityConfigRef('config.synthetic.control', logical.payload_schema, '0' * 64,
        logical.content_sha256, logical.logical_artifact_id)
    capability = CapabilityRequirement('synthetic.custody-reader', '1.0.0', CapabilityKind.REPORTER,
        config, (logical.payload_schema,), (logical.payload_schema,), (), EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.OUTCOME_BLIND, ResourceBudget(1, None, 0, None, None, None))
    output = ArtifactOutputSpec('output.control', 'output.synthetic.control', 'outputs/control.json',
        logical.payload_schema, logical.profile, logical.media_type, logical.visibility_ceiling,
        (logical.visibility_ceiling,), logical.outcome_access)
    task = ExecutionTask(context.task_id, ScientificStage.REPORT, capability, '0' * 64, (),
        (spec,), (output,), (), BarrierKind.NONE, 1, ('obligation.synthetic',), scientific_inputs=())
    return context, task


def _closure(plane, publication, context, task, monkeypatch, *, foreign_input=False):
    """Drive the actual closure loop; only original completion metadata is doubled."""
    parent = ArtifactLineageParent(ObjectIdentity.from_record(
        publication.logical.logical_artifact_id, publication.logical),
        publication.logical.visibility_ceiling, publication.logical.outcome_access)
    output = _write(plane, 'sharded', logical='output.synthetic.control', lineage=(parent,))
    logical, material = output.logical, output.materialization
    task = replace(task, outputs=(replace(task.outputs[0], relative_path=material.relative_path),))
    receipt = CanonicalTaskReceipt('receipt.synthetic', RUN, task.task_id, 'attempt.synthetic', 'a' * 40,
        ('materialization.foreign',) if foreign_input else (publication.materialization.materialization_id,),
        (material,), (logical,), (), OperationalStatus.SUCCEEDED, ())
    grant = GrantMetadata()
    package = SimpleNamespace(package_id='package.synthetic', scientific_approval=grant, execution_authority=grant)
    plan = SimpleNamespace(source_plan=SimpleNamespace(object_id=RUN), implementation_commit='a' * 40, tasks=(task,))
    index = object()
    row = RecoveryTerminalAttempt(receipt.attempt_id, task.task_id, 1,
        RecoveryTerminalDisposition.SUCCEEDED, None, receipt.receipt_id, receipt.fingerprint())
    terminal = SimpleNamespace(operational_status='SUCCEEDED', completed_task_ids=(task.task_id,),
        failed_task_ids=(), blocked_task_ids=(), attempts=(row,))

    class RecoveryMetadata:
        def __init__(self, writer):
            assert writer is plane

        def read_index(self, path, *, expected_schema):
            assert path == f'runs/{RUN}/recovery/wave.package.synthetic/envelope-run-recovery-index.json'
            return index

        def read_terminal(self, selected):
            assert selected is index
            return terminal

    class ReceiptMetadata:
        def __init__(self, writer):
            assert writer is plane

        def read_by_receipt_id(self, run, task_id, receipt_id):
            assert (run, task_id, receipt_id) == (RUN, task.task_id, receipt.receipt_id)
            return receipt

    monkeypatch.setattr(parents, 'ExternalRunRecoveryStore', RecoveryMetadata)
    monkeypatch.setattr(parents, 'ExternalTaskReceiptStore', ReceiptMetadata)
    monkeypatch.setattr(parents, 'build_run_recovery_index', lambda *args, **kwargs: index)
    result = parents._collect_receipt_closure(package, plan, plane, grant, ('synthetic.',))
    assert parents._verify_receipt_closure(plane, result) == {task.task_id: receipt}
    return result


def _read(reader, plane, publication, context, task, monkeypatch, **kwargs):
    if reader == 'current':
        _, controls = current.CurrentIssuedTaskCustody(writer=plane).task_inputs(context, task)
        return current.CurrentIssuedTaskCustody(writer=plane).control_record(controls[LOGICAL], Control, 4096)
    return _closure(plane, publication, context, task, monkeypatch, **kwargs)


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
@pytest.mark.parametrize('reader', ('current', 'closure'))
def test_actual_input_readers_accept_exact_published_control(tmp_path, monkeypatch, layout, reader):
    plane = _plane(tmp_path)
    publication = _write(plane, layout)
    context, task = _selected(publication)
    _read(reader, plane, publication, context, task, monkeypatch)
    assert all(port.bytes_read == 0 for port in context.input_ports)


@pytest.mark.parametrize('layout', ('legacy', 'sharded'))
@pytest.mark.parametrize('reader', ('current', 'closure'))
@pytest.mark.parametrize('missing', ('payload', 'sidecar'))
def test_partial_original_pair_is_refused_without_falling_through(tmp_path, monkeypatch, layout, reader, missing):
    plane = _plane(tmp_path)
    publication = _write(plane, layout)
    context, task = _selected(publication)
    relative = publication.materialization.relative_path + ('.manifest.json' if missing == 'sidecar' else '')
    plane.root.resolve(relative, for_write=False).unlink()
    with pytest.raises((ArtifactPlaneError, FileNotFoundError)):
        _read(reader, plane, publication, context, task, monkeypatch)
    token = sha256(LOGICAL.encode()).hexdigest()
    alternative = (f'runs/{RUN}/inputs/{token[:2]}/{token}.bin' if layout == 'legacy'
        else f'runs/{RUN}/inputs/{LOGICAL}.bin')
    assert not (tmp_path / alternative).exists()


@pytest.mark.parametrize('reader', ('current', 'closure'))
def test_dual_layout_refuses_even_equal_control_bytes(tmp_path, monkeypatch, reader):
    plane = _plane(tmp_path)
    publication = _write(plane, 'legacy')
    _write(plane, 'sharded')
    context, task = _selected(publication)
    with pytest.raises(ArtifactPlaneError, match='ambiguous legacy and sharded'):
        _read(reader, plane, publication, context, task, monkeypatch)


@pytest.mark.parametrize('reader', ('current', 'closure'))
def test_foreign_frozen_input_metadata_refuses(tmp_path, monkeypatch, reader):
    plane = _plane(tmp_path)
    publication = _write(plane, 'sharded')
    context, task = _selected(publication)
    task = replace(task, external_inputs=(replace(task.external_inputs[0], expected_content_sha256='0' * 64),))
    with pytest.raises(PermissionError, match='exact current external input|exact frozen external input'):
        _read(reader, plane, publication, context, task, monkeypatch)


@pytest.mark.parametrize('reader', ('current', 'closure'))
def test_foreign_actual_input_materialization_refuses(tmp_path, monkeypatch, reader):
    plane = _plane(tmp_path)
    publication = _write(plane, 'sharded')
    context, task = _selected(publication)
    if reader == 'current':
        context.input_bindings = (replace(context.input_bindings[0], materialization_id='materialization.foreign'),)
    with pytest.raises(PermissionError, match='complete actual current task input bindings|complete actual input census'):
        _read(reader, plane, publication, context, task, monkeypatch, foreign_input=True)


def test_actual_protected_fit_callback_reaches_original_publication_gate_with_sharded_config(tmp_path, monkeypatch):
    """The real callback reads sharded config; its next scientific gate still refuses.

    Current issued-task authority is a named unit double, not a genuine issue.
    The installed callback and exact config/publication reader remain unchanged.
    """
    from empirical_lawhood.api.domain_composition.matrix_protected_response import runtime as e3
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_statistical_bindings as fit
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_composition import outcome_task_id
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase, InformationCutoff

    plane = _plane(tmp_path)
    publication = _write(plane, 'sharded', logical='publication.synthetic.fit')

    def pin(name, kind):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())

    specification, allocation = pin('specification.synthetic', MatrixResponseErrorSpecification), pin('allocation.synthetic', UnitAllocation)
    record = fit.ProtectedE3FitConfig('config.' + fit.statistical_task_id(specification, allocation, 'fit'),
        specification, allocation, (('calibration', 1), ('evaluation', 1)),
        pin('manifest.synthetic', ProtectedE3NativeSourceManifest), allocation,
        InformationCutoff('cutoff.synthetic', 'clock.synthetic', CausalPhase.PREPARATION, Decimal(1)),
        tuple((name, publication, AvailabilitySpec('clock.synthetic', CausalPhase.PREPARATION,
            OutcomeAccess.OUTCOME_BLIND, Decimal(0))) for name in fit.PUBLICATION_KEYS))
    config_publication = _write(plane, 'sharded', record=record)
    context, task = _selected(config_publication)
    context.config = SimpleNamespace(artifact_id=LOGICAL, content_sha256=record.fingerprint())
    root = SimpleNamespace(source_materializations=())
    package = SimpleNamespace(issued_study=SimpleNamespace(materialization_qualifications=(),
        candidate=SimpleNamespace(authoring_package=SimpleNamespace(base=SimpleNamespace(draft=root)))))
    calls = []
    monkeypatch.setattr(current.CurrentIssuedTaskCustody, 'current_task',
        lambda self, selected, runner: (package, None, task))

    def original_gate(writer, selected):
        assert writer is plane and selected == record
        calls.append('original-publication-gate')
        raise PermissionError('original scientific-publication gate retained')

    monkeypatch.setattr(e3, 'authenticate_protected_e3_fit_config', original_gate)
    supplier = e3.ProtectedE3RuntimeInputSupplier(None, writer=plane, root=root, fit_config=record,
        qualifications=(), selection=None)
    runner = fit.ProtectedE3StatisticalRunner('fit', None, outcome_task_id)
    with pytest.raises(PermissionError, match='original scientific-publication gate retained'):
        supplier.prepare_protected_e3_fit(context, runner)
    assert calls == ['original-publication-gate']
    assert all(port.bytes_read == 0 for port in context.input_ports)
