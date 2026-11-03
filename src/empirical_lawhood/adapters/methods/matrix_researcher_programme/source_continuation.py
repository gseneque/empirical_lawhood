# SPDX-License-Identifier: MPL-2.0
"""A source change before TRAIN, preserving original E1/E2 and all allocations.

These are metadata selections and lineage, not completion or entry authority.
The continuation owner must authenticate the original complete execution census
and prove that TRAIN and every dependent phase remain unentered.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decimal_context_key
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id, validate_sha256
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from .known_inputs import MatrixProgrammePublishedInput
from .selection import MatrixContinuedProgrammeSpecification, MatrixResearchProgrammePlan

PROTOCOL_ID = 'matrix.programme.source-continuation'
OUTPUT_PROTOCOL_ID = 'matrix.programme.output-allowance-continuation'
CONTINUATION_FILENAME = 'source-continuation.json'
RETAINED_PHASES = ('e1', 'e2')
COMPLETED_PHASES = ('e1', 'e2', 'train', 'e3')
COMPLETED_E4_PHASES = (*COMPLETED_PHASES, 'e4.development')
_source_rebindings = ContextVar('matrix_programme_source_rebindings', default=None)


@contextmanager
def source_rebinding_scope(maximum_bytes):
    """Retain bounded pure projections for one owning input-read lifetime.

    This contains no source admission, custody or access verdict. Nested
    readers still compare their complete actual inputs with each projection.
    """
    if type(maximum_bytes) is not int or maximum_bytes < 1:
        raise ValueError('source rebinding reuse requires a positive byte bound')
    if _source_rebindings.get() is not None:
        yield
        return
    token = _source_rebindings.set({'records': {}, 'bytes': 0, 'maximum_bytes': maximum_bytes})
    try:
        yield
    finally:
        _source_rebindings.reset(token)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeSourceContinuationSpecification(CanonicalRecord):
    """Select one original programme and a separate new programme home."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/source-continuation-specification'
    specification_id: str
    predecessor: MatrixProgrammePublishedInput
    directory: str

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_relative_locator(self.directory)
        if type(self.predecessor) is not MatrixProgrammePublishedInput:
            raise TypeError('source continuation requires the exact original published programme plan')
        self.predecessor.__post_init__()
        self.predecessor.require_kind(MatrixResearchProgrammePlan)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeOutputContinuationSpecification(MatrixProgrammeSourceContinuationSpecification):
    """Select a finite response-score allowance for unentered later phases."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/output-allowance-continuation-specification'
    output_bytes: int

    def __post_init__(self):
        super(MatrixProgrammeOutputContinuationSpecification, self).__post_init__()
        if type(self.output_bytes) is not int or not 0 < self.output_bytes <= 256 * 1024**2:
            raise ValueError('future PURE output allowance must be a positive integer within 256 MiB')


def continued_operations(original, specification, *, completed_phases):
    """Change only future PURE score output ceilings after complete E4 DEV."""
    from .operations import MatrixProgrammeOperations
    if type(original) is not MatrixProgrammeOperations:
        raise TypeError('continuation requires the exact original operational selection')
    original.__post_init__()
    if type(specification) is MatrixProgrammeSourceContinuationSpecification:
        return original
    if type(specification) is not MatrixProgrammeOutputContinuationSpecification:
        raise TypeError('continuation requires an exact supported operational selection')
    specification.__post_init__()
    if completed_phases != COMPLETED_E4_PHASES:
        raise PermissionError('future output selection requires complete original E4 development and structure')

    def score_budget(resources):
        rows = dict(resources.phase_budgets)
        before = rows['response-score']
        if (type(before.output_bytes) is not int or type(before.memory_bytes) is not int
                or specification.output_bytes < before.output_bytes
                or specification.output_bytes > before.memory_bytes):
            raise ValueError('future PURE output selection cannot lower the allowance or exceed original memory')
        rows['response-score'] = replace(before, output_bytes=specification.output_bytes)
        return replace(resources, phase_budgets=tuple(sorted(rows.items())))

    if original.e4 is None or original.prepared is None:
        raise ValueError('future PURE output selection requires the original E4 and prepared-phase resources')
    selected = replace(original,
        e4=replace(original.e4, native_budgets=score_budget(original.e4.native_budgets)),
        prepared=replace(original.prepared,
            opportunity_resources=score_budget(original.prepared.opportunity_resources),
            protected_resources=score_budget(original.prepared.protected_resources)))
    if selected == original:
        raise ValueError('future PURE output selection must increase an original response-score allowance')
    return selected


@dataclass(frozen=True, slots=True)
class MatrixProgrammeSourceContinuation(CanonicalRecord):
    """Immutable source handoff, with actual original execution locators."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/source-continuation'
    record_id: str
    specification: MatrixProgrammeSourceContinuationSpecification
    target_plan: MatrixResearchProgrammePlan
    predecessor_bindings: tuple[tuple[str, ObjectIdentity], ...]
    predecessor_terminals: tuple[tuple[str, ObjectIdentity], ...]
    unentered_training_packet: ObjectIdentity

    def __post_init__(self):
        from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
        from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
        from .selection import MatrixProgrammePhaseBinding
        validate_stable_id(self.record_id)
        if (type(self.specification) is not MatrixProgrammeSourceContinuationSpecification
                or type(self.target_plan) is not MatrixResearchProgrammePlan):
            raise TypeError('source continuation requires exact original selection and target plan')
        self.specification.__post_init__()
        self.target_plan.__post_init__()
        if self.target_plan.specification.directory != self.specification.directory:
            raise ValueError('source continuation changes its selected target home')
        target = self.target_plan.specification
        if (type(target) is not MatrixContinuedProgrammeSpecification or target.predecessor != self.specification.predecessor
                or target.continuation_request != self.specification.identity):
            raise ValueError('source continuation target omits its exact required original lineage')
        for rows in (self.predecessor_bindings, self.predecessor_terminals):
            if (type(rows) is not tuple or tuple(phase for phase, _ in rows) != RETAINED_PHASES
                    or any(type(pin) is not ObjectIdentity for _, pin in rows)):
                raise ValueError('source continuation requires exactly the original E1 and E2 census')
            for _, pin in rows:
                pin.__post_init__()
        if any((pin.object_schema, pin.object_version) != (MatrixProgrammePhaseBinding.SCHEMA,
                MatrixProgrammePhaseBinding.VERSION) for _, pin in self.predecessor_bindings):
            raise ValueError('source continuation changes its original phase binding types')
        for (_, pin), kind in zip(self.predecessor_terminals,
                (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent), strict=True):
            if (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('source continuation changes its original execution terminal types')
        pin = self.unentered_training_packet
        if (type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version)
                != (AuthoredRecursiveWave.SCHEMA, AuthoredRecursiveWave.VERSION)):
            raise TypeError('source continuation requires its exact original unentered TRAIN packet')
        pin.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeCompletedSourceContinuation(CanonicalRecord):
    """Source handoff after completed E3, preserving every actual producer.

    The original pre-TRAIN format remains unchanged. This format records a
    completed frontier instead of an unentered TRAIN packet; it carries no
    permission to execute any retained phase again.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/completed-source-continuation'
    RETAINED_PHASES: ClassVar[tuple[str, ...]] = COMPLETED_PHASES
    SPECIFICATION_TYPE: ClassVar[type] = MatrixProgrammeSourceContinuationSpecification
    record_id: str
    specification: MatrixProgrammeSourceContinuationSpecification
    target_plan: MatrixResearchProgrammePlan
    predecessor_bindings: tuple[tuple[str, ObjectIdentity], ...]
    predecessor_terminals: tuple[tuple[str, ObjectIdentity], ...]

    def __post_init__(self):
        from .selection import MatrixProgrammePhaseBinding
        from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
        from empirical_lawhood.runtime.retained_e3_repair import (
            RetainedE3RepairTerminalEvent, RetainedE3ContinuedRepairTerminalEvent,
        )
        validate_stable_id(self.record_id)
        if (type(self.specification) is not self.SPECIFICATION_TYPE
                or type(self.target_plan) is not MatrixResearchProgrammePlan):
            raise TypeError('completed source continuation requires exact selection and target plan')
        self.specification.__post_init__()
        self.target_plan.__post_init__()
        target = self.target_plan.specification
        if (type(target) is not MatrixContinuedProgrammeSpecification
                or target.directory != self.specification.directory
                or target.predecessor != self.specification.predecessor
                or target.continuation_request != self.specification.identity):
            raise ValueError('completed source continuation changes its required original lineage')
        for rows in (self.predecessor_bindings, self.predecessor_terminals):
            if (type(rows) is not tuple or tuple(phase for phase, _ in rows) != self.RETAINED_PHASES
                    or any(type(pin) is not ObjectIdentity for _, pin in rows)):
                raise ValueError('completed source continuation requires the complete E1/E2/TRAIN/E3 frontier')
        for _, pin in self.predecessor_bindings:
            if (pin.object_schema, pin.object_version) != (MatrixProgrammePhaseBinding.SCHEMA, MatrixProgrammePhaseBinding.VERSION):
                raise ValueError('completed source continuation changes its original phase binding contract')
        allowed = ((RunRecoveryTerminalEvent,), (DevelopmentRunRecoveryTerminalEvent,),
            (DevelopmentRunRecoveryTerminalEvent,),
            (RunRecoveryTerminalEvent, RetainedE3RepairTerminalEvent, RetainedE3ContinuedRepairTerminalEvent))
        if self.RETAINED_PHASES == COMPLETED_E4_PHASES:
            from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairTerminalEvent
            from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairTerminalEvent
            from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationTerminalEvent
            allowed = (*allowed, (DevelopmentRunRecoveryTerminalEvent, DevelopmentOutputRepairTerminalEvent,
                DevelopmentControllerRepairTerminalEvent, DevelopmentNativeContinuationTerminalEvent))
        for (_, pin), kinds in zip(self.predecessor_terminals, allowed, strict=True):
            if (pin.object_schema, pin.object_version) not in {(kind.SCHEMA, kind.VERSION) for kind in kinds}:
                raise ValueError('completed source continuation changes its actual terminal contract')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeCompletedE4SourceContinuation(MatrixProgrammeCompletedSourceContinuation):
    """Retain completed E4 DEV acquisition and its required structural child.

    Every original task remains under its actual producer. Only later,
    unentered phases can use the new source selection.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/completed-e4-source-continuation'
    RETAINED_PHASES: ClassVar[tuple[str, ...]] = COMPLETED_E4_PHASES
    completed_e4_structure_terminal: ObjectIdentity

    def __post_init__(self):
        super(MatrixProgrammeCompletedE4SourceContinuation, self).__post_init__()
        from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryTerminalEvent
        from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairTerminalEvent
        from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairTerminalEvent
        from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationTerminalEvent
        pin = self.completed_e4_structure_terminal
        kinds = (DevelopmentRunRecoveryTerminalEvent, DevelopmentOutputRepairTerminalEvent, DevelopmentControllerRepairTerminalEvent,
            DevelopmentNativeContinuationTerminalEvent)
        if (type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version)
                not in {(kind.SCHEMA, kind.VERSION) for kind in kinds}):
            raise TypeError('completed E4 handoff requires its actual structural development terminal')
        pin.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixProgrammeCompletedE4OutputContinuation(MatrixProgrammeCompletedE4SourceContinuation):
    """Preserve completed E4 and bind the explicit future operational change."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/completed-e4-output-allowance-continuation'
    SPECIFICATION_TYPE: ClassVar[type] = MatrixProgrammeOutputContinuationSpecification
    specification: MatrixProgrammeOutputContinuationSpecification


@dataclass(frozen=True, slots=True)
class MatrixProgrammeUnenteredE4SourceContinuation(MatrixProgrammeCompletedSourceContinuation):
    """Preserve an authored E4 child whose run has only partial input custody.

    Its original binding, plan and namespace remain immutable. The successor
    is authored normally under the repaired source; this record grants neither
    retry of an entered task nor permission to reuse an uncertain native call.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/unentered-e4-source-continuation'
    unentered_e4_binding: ObjectIdentity
    unentered_e4_packet: ObjectIdentity
    unentered_e4_plan: ObjectIdentity
    unentered_e4_run_id: str
    unentered_e4_inputs_sha256: str

    def __post_init__(self):
        super(MatrixProgrammeUnenteredE4SourceContinuation, self).__post_init__()
        from .selection import MatrixProgrammePhaseBinding
        from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
        from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
        for pin, kind in ((self.unentered_e4_binding, MatrixProgrammePhaseBinding),
                (self.unentered_e4_packet, AuthoredRecursiveWave), (self.unentered_e4_plan, DevelopmentExecutionPlan)):
            if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError('unentered E4 handoff requires exact original binding, packet and development plan')
            pin.__post_init__()
        validate_stable_id(self.unentered_e4_run_id)
        validate_sha256(self.unentered_e4_inputs_sha256)


def bind_inputs(specification, records, **kwargs):
    if type(specification) not in (MatrixProgrammeSourceContinuationSpecification, MatrixProgrammeOutputContinuationSpecification):
        raise TypeError('source continuation requires its exact copied specification')
    specification.__post_init__()
    if records or kwargs.get('files'):
        raise ValueError('source continuation derives all science from the original programme; no replacement operands')
    return PreparedExperimentInputs({}, None)


def prepare(specification, *, execution, **_kwargs):
    bind_inputs(specification, {})
    execution.__post_init__()
    detail = ('Use experiment-derive-inputs to authenticate completed E4 development and structure before changing future PURE output allowances.'
        if type(specification) is MatrixProgrammeOutputContinuationSpecification else
        'Use experiment-derive-inputs to authenticate completed E1/E2, unentered TRAIN and unchanged original allocations.')
    missing = [ExperimentDependency('matrix.continuation.original-custody', DependencyKind.EXTERNAL_INPUT, detail)]
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            missing.append(ExperimentDependency('matrix.continuation.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + ' for the new source-bound programme.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(missing, key=lambda row: row.code)), execution=execution, specification_record=specification)


def require_separate_home(original, selected):
    previous, target = PurePosixPath(original), PurePosixPath(selected)
    if target.is_relative_to(previous) or previous.is_relative_to(target):
        raise ValueError('source continuation requires disjoint original and new programme directories')


def rebound_responses(phase, provenance, assay):
    """Change source identities through the owning source and assay constructors.

    Allocations, histories, future panels, numerical settings and assay bytes
    remain their original values. No allocator or random generator is involved.
    """
    memo = _source_rebindings.get()
    operands = (phase.reservation, phase.native_specification, phase.responses, provenance, assay)
    reusable = memo is not None and all(isinstance(value, CanonicalRecord) and value._is_cacheable()
        for value in operands)
    if reusable:
        # Keep the original objects alive with the projection, so ids cannot
        # alias another decoded body. Small source/assay pins also permit an
        # independently decoded but byte-identical provenance to use it.
        key = (*map(id, operands[:3]), provenance.identity, assay.identity, decimal_context_key())
        previous = memo['records'].get(key)
        if previous is not None:
            originals, result = previous
            if all(a is b for a, b in zip(originals[:3], operands[:3], strict=True)):
                return result
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    index = ScheduledSourceIndex.from_shared(reservation=phase.reservation,
        specification=phase.native_specification, provenances=(provenance,))
    protocols = []
    for original in phase.responses.protocols:
        source = index.resolve(index.reference(source_id=original.public_source.source.object_id,
            root_id=original.public_source.root.root_id, provenance=provenance.identity))
        protocol = assay.bind(source, protocol_id=original.protocol_id)
        if replace(protocol, public_source=original.public_source, templates=original.templates) != original:
            raise PermissionError('source continuation changes original response mathematics')
        protocols.append(protocol)
    result = replace(phase.responses, protocols=tuple(protocols))
    if reusable and result._is_cacheable():
        size = result.canonical_size_bytes()
        if memo['bytes'] + size <= memo['maximum_bytes']:
            memo['records'][key] = operands, result
            memo['bytes'] += size
    return result


def rebound_e6_policy(original, phases):
    """Rebind the original E6 policy to source-adjusted pre-TRAIN protocols."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import build_e6_transport_policy
    selected = {phase.role: phase for phase in phases}
    roles = (('CALIBRATION', 'e3.calibration'), ('EVALUATION', 'e3.confirmation'),
        ('TRANSFER_NEARBY', 'e6.nearby'), ('TRANSFER_SHIFTED', 'e6.shifted'))
    return build_e6_transport_policy(record_id=original.e6_policy.record_id,
        candidate_specification=original.scientific_design.e3,
        future_reservation=original.phase('e3.calibration').reservation,
        future_response_selections=tuple((role, selected[phase].responses) for role, phase in roles),
        availability=(original.commitments.availability.record, original.availability),
        criterion=original.scientific_design.e6_policy.criterion)


def validate_continued_inputs(original, continued):
    """Prove the complete change is source provenance and its derived bindings."""
    before, after = original.commitments, continued.commitments
    if replace(after, record_id=before.record_id, producing_provenance=before.producing_provenance,
            phases=before.phases, e6_policy=before.e6_policy) != before:
        raise PermissionError('source continuation changes original D, exposure, folds, streams, availability or support custody')
    if (original.scientific_design != continued.scientific_design or original.exposure_census != continued.exposure_census
            or original.exposure_audit != continued.exposure_audit or original.scalar_definitions != continued.scalar_definitions
            or original.availability != continued.availability):
        raise PermissionError('source continuation changes the original non-source input bodies')
    for previous, current in zip(original.phases, continued.phases, strict=True):
        if (current.role, current.reservation, current.native_specification) != (
                previous.role, previous.reservation, previous.native_specification):
            raise PermissionError('source continuation reallocates an original group or changes native selections')
        original_handle, current_handle = before.phase(previous.role), after.phase(previous.role)
        if replace(current_handle, responses=original_handle.responses) != original_handle:
            raise PermissionError('source continuation changes original reservation or native-selection publications')
        if previous.responses is None:
            if current.responses is not None or current_handle != original_handle:
                raise PermissionError('source continuation changes the original E1 reservation')
            continue
        assay = original.scientific_design.e2.assay if previous.role == 'e2' else original.scientific_design.training_assay
        if current.responses != rebound_responses(previous, continued.producing_provenance, assay):
            raise PermissionError('source continuation changes original response panels or mathematical settings')
    if continued.e6_policy != rebound_e6_policy(original, continued.phases):
        raise PermissionError('source continuation changes the original pre-TRAIN E6 policy')
