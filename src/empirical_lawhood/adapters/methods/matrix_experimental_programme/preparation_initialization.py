# SPDX-License-Identifier: MPL-2.0
"""Public declared initialization inputs, separate from historical observations."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from bisect import bisect_left
from dataclasses import dataclass
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, ScheduledSpecification, _publication
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from .preparation_records import MatrixPreparationInitialStateV2
from .protected_preparation_records import MatrixProtectedSourceClosure
from .selected_original_commitments import MatrixPreparedOriginalCommitments
from .selected_development_product import MatrixSelectedDevelopmentProduct
from .selected_revision_development_product import MatrixRevisionDevelopmentProduct

PROTOCOL_ID = "matrix.preparation-initialization.inputs"
PHASES = ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER")


def pin(value, field="record_id"):
    return ObjectIdentity.from_record(getattr(value, field), value)


@dataclass(frozen=True, slots=True)
class MatrixPreparationInitializationSources(CanonicalRecord):
    """Exact original source closure before its initial-state operands exist."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/initialization-sources"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    reservation: ScheduledReservation
    specification: ScheduledSpecification
    provenances: tuple[NumericalProducingProvenance, ...]
    descriptors: tuple[ScheduledSource, ...]
    audit: ScheduledExposureAudit
    audit_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.reservation, ScheduledReservation), (self.specification, ScheduledSpecification),
                (self.audit, ScheduledExposureAudit), (self.audit_publication, ArtifactWriteResult)):
            if type(value) is not kind:
                raise TypeError("initialization requires exact original reservation, source selection and audit")
            value.__post_init__()
        if (type(self.descriptors) is not tuple or not self.descriptors
                or any(type(row) is not ScheduledSource for row in self.descriptors)
                or tuple(row.root_id for row in self.descriptors) != tuple(sorted({row.root_id for row in self.descriptors}))
                or type(self.provenances) is not tuple or not self.provenances
                or any(type(value) is not NumericalProducingProvenance for value in self.provenances)
                or tuple(value.fingerprint() for value in self.provenances) != tuple(sorted({value.fingerprint() for value in self.provenances}))
                or {row.provenance for row in self.descriptors} != {value.identity for value in self.provenances}):
            raise ValueError("initialization drops complete unique original roots or producing provenance")
        _publication(self.audit_publication, self.audit)
        index = self.source_index()
        index.require_roster(self.descriptors, expected_root_ids=tuple(value.root_id for value in self.descriptors))
        self.audit.validate_source(index.resolve(self.descriptors[0]))

    def source_index(self):
        return ScheduledSourceIndex.from_shared(reservation=self.reservation, specification=self.specification,
            provenances=self.provenances)

    def source(self, descriptor, *, index):
        if type(descriptor) is not ScheduledSource:
            raise TypeError("initialization requires the current bounded source")
        position = bisect_left(self.descriptors, descriptor.root_id, key=lambda value: value.root_id)
        if position == len(self.descriptors) or self.descriptors[position] != descriptor:
            raise ValueError("initialization selects an uncommitted original descriptor")
        return index.resolve(descriptor)

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class MatrixPreparationInitializationRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/initialization-request"
    record_id: str
    namespace: str
    phase: str
    sources: MatrixPreparationInitializationSources
    original_commitments: MatrixPreparedOriginalCommitments
    exposure_support: tuple[tuple[ArtifactIdentity, ArtifactWriteResult | ExperimentFileInputBinding], ...]
    development_product: MatrixSelectedDevelopmentProduct | MatrixRevisionDevelopmentProduct | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id); validate_stable_id(self.namespace)
        if (self.phase not in PHASES or type(self.sources) is not MatrixPreparationInitializationSources
                or type(self.original_commitments) is not MatrixPreparedOriginalCommitments):
            raise TypeError("initialization selects one exact phase, source closure and original commitment owner")
        self.sources.__post_init__(); self.original_commitments.__post_init__()
        role = {"E5_OPPORTUNITY": MatrixProgrammeRole.DEVELOPMENT, "E5_CONFIRMATION": MatrixProgrammeRole.CONFIRMATION,
            "E6_TRANSFER": MatrixProgrammeRole.WITHHELD_TRANSFER}[self.phase]
        index = self.sources.source_index()
        rows = tuple(self.sources.source(value, index=index) for value in self.sources.descriptors)
        if any(source.root.root.role is not role for source in rows):
            raise ValueError("initialization cannot change actual protected/development source roles")
        groups = tuple(source.root.root.independent_group_id for source in rows)
        if len(set(groups)) != len(groups):
            raise ValueError("initialization requires one actual shared start per assigned independent group")
        if (self.phase == "E5_CONFIRMATION") != (self.development_product is not None):
            raise ValueError("only CONF initialization requires the actual complete separate E5 DEV locator")
        if self.development_product is not None:
            if type(self.development_product) not in (MatrixSelectedDevelopmentProduct, MatrixRevisionDevelopmentProduct):
                raise TypeError("CONF initialization requires its actual ordinary DEV product owner")
            self.development_product.__post_init__()
        required = {artifact for artifact, _ in current_exposure_support(self.sources.audit)}
        if (type(self.exposure_support) is not tuple or len(required) != 1
                or tuple(artifact.artifact_id for artifact, _ in self.exposure_support) != tuple(sorted(artifact.artifact_id for artifact in required))
                or {artifact for artifact, _ in self.exposure_support} != required):
            raise ValueError("initialization needs the exact current census publication")
        for artifact, custody in self.exposure_support:
            if type(artifact) is not ArtifactIdentity or type(custody) not in (ArtifactWriteResult, ExperimentFileInputBinding):
                raise TypeError("initialization support requires exact existing FILE/publication custody")
            artifact.__post_init__(); custody.__post_init__()
            if type(custody) is ExperimentFileInputBinding:
                valid = custody.identity == artifact
            else:
                valid = (artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes) == (
                    custody.logical.logical_artifact_id, custody.logical.payload_schema, custody.logical.content_sha256,
                    custody.logical.media_type, custody.materialization.size_bytes)
            if not valid: raise ValueError("initialization support changes its exact original byte binding")

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class MatrixPreparationInitializationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/initialization-specification"
    specification_id: str
    request: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.request) is not ObjectIdentity or (self.request.object_schema, self.request.object_version) != (
                MatrixPreparationInitializationRequest.SCHEMA, MatrixPreparationInitializationRequest.VERSION):
            raise TypeError("initialization specification requires its exact request edition")
        self.request.__post_init__()

    @property
    def identity(self): return pin(self, "specification_id")


@dataclass(frozen=True, slots=True)
class MatrixPreparationInitializationBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/initialization-bank"
    record_id: str
    request: MatrixPreparationInitializationRequest
    states: tuple[tuple[str, MatrixPreparationInitialStateV2], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.request) is not MatrixPreparationInitializationRequest:
            raise TypeError("initialization bank requires its exact original request")
        self.request.__post_init__()
        if (type(self.states) is not tuple or tuple(root_id for root_id, _ in self.states) !=
                tuple(row.root_id for row in self.request.sources.descriptors)):
            raise ValueError("initialization bank omits an assigned original group")
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
        index = self.request.sources.source_index()
        for descriptor, (_, state) in zip(self.request.sources.descriptors, self.states, strict=True):
            source = self.request.sources.source(descriptor, index=index)
            if (type(state) is not MatrixPreparationInitialStateV2 or state.original != ScheduledPublicSource.from_source(source)
                    or state.root != source.root):
                raise ValueError("initialization bank substitutes an original source, clock or root streams")
            state.__post_init__()

    @property
    def identity(self): return pin(self)

    def prepared_closure(self, *, record_id, numerical_scope):
        sources = self.request.sources
        return MatrixProtectedSourceClosure(record_id, sources.reservation, sources.specification, sources.provenances,
            sources.descriptors, sources.audit, sources.audit_publication, self.states, numerical_scope)


def input_record_types():
    return MatrixPreparationInitializationRequest, MatrixPreparationInitializationBank


def bind_inputs(specification, records, *, files=None):
    if set(records) not in (set(), {"request"}, {"request", "initial-states"}):
        raise ValueError("initialization accepts its exact request and optional generated bank")
    request = records.get("request")
    if request is None:
        if files: raise ValueError("initialization cannot select files without its actual request")
        return PreparedExperimentInputs({}, (None, None))
    if type(request) is not MatrixPreparationInitializationRequest or request.identity != specification.request:
        raise ValueError("initialization substitutes its original request")
    request.__post_init__()
    bank = records.get("initial-states")
    if bank is not None and (type(bank) is not MatrixPreparationInitializationBank or bank.request != request):
        raise ValueError("initialization substitutes its generated bank")
    if bank is not None: bank.__post_init__()
    expected = {} if bank is None else {"initial-state." + root: state.array_artifact for root, state in bank.states}
    selected = {} if files is None else files
    if set(selected) != set(expected) or any(selected[key].identity != expected[key] for key in selected):
        raise ValueError("initialization changes the complete exact generated NPZ FILE census")
    return PreparedExperimentInputs({}, (request, bank))


def prepare(specification, *, execution, method_inputs=None, **kwargs):
    specification.__post_init__(); execution.__post_init__()
    request, bank = (None, None) if method_inputs is None else method_inputs
    dependencies = []
    if request is None:
        dependencies.append(ExperimentDependency("initialization.request", DependencyKind.EXTERNAL_INPUT,
            "Supply the exact original source and commitment-bearing initialization request.", "request"))
    elif request.identity != specification.request:
        raise ValueError("initialization preparation changes its exact request")
    elif bank is None:
        dependencies.append(ExperimentDependency("initialization.derive", DependencyKind.EXTERNAL_INPUT,
            "Use experiment-derive-inputs to authenticate originals and publish deterministic initial-state operands.", "request"))
    groups = 0 if request is None else len(request.sources.descriptors)
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((("initial-state", groups),), (("initial-state", 0 if bank is None else groups),), (), (), 0),
        tuple(dependencies), execution=execution, specification_record=specification)


def example_inputs():
    """Explicit missing-input copy, never an original scientific record."""
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
    request = ObjectIdentity("request.replace-with-original-initialization", MatrixPreparationInitializationRequest.SCHEMA,
        MatrixPreparationInitializationRequest.VERSION, "0" * 64)
    return (MatrixPreparationInitializationSpecification("specification.matrix-initialization.copied", request),
        ExperimentFileInputSelection("sources.matrix-initialization.copied", PROTOCOL_ID, (), ()))
