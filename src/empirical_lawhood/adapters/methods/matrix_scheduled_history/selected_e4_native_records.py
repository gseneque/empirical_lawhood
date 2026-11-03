# SPDX-License-Identifier: MPL-2.0
"""Additive issued selected E4 CAL/CONF native records.

These distinct protected schemas preserve historical scheduled records. The original
physical source, streams, clock, response instrument and fitted E3 parameters
remain their existing typed records. No original calibration scores occur here.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import model_predictors
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterCoordinate, METHODS as HISTORY_METHODS, MatrixParameterHistoryControl, MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactWriteResult

from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationSpec, ScientificSourceQualificationResult
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

from .continuation import ScheduledFullArrays, ScheduledFullHistory, validate_full_native_evidence
from .forecast import ScheduledForecastFeature, ScheduledPublicSource
from .programme_reduction import ScheduledProgrammeNativeDisposition, ScheduledProgrammeReceiptReference
from .programme_records import ScheduledProgrammeWave
from .selected_e3_e4_records import SelectedE3E4ForecastDesign
from . import selected_e4_programme as p
from .records import (ScheduledArrays, ScheduledCheckpoint, ScheduledCausalPrefix, ScheduledFrameAssessment, ScheduledNativeEvidence,
    ScheduledPrefixHistory, ScheduledPrefixPolicy, ScheduledPrefixTrace, ScheduledPrefixWitness, ScheduledSource, _validate_prefix_native_evidence, identity)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryReadoutSelection,
)

from .response_records import ScheduledResponseArrays, ScheduledResponseForecast, ScheduledResponseNative, ScheduledResponseScore, branch_census

NAMESPACE = "matrix-selected-e4-protected"
POINT_ONLY = "PRIMARY_FIT_POINT_ONLY_NO_E4_CALIBRATION_OR_TRANSPORT_WARRANT"
BLIND, SEALED, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE
POPULATIONS = ("CALIBRATION", "CONFIRMATION")


def pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)

def exact_pin(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("selected E3/E4 substitutes an exact versioned scientific operand")
    value.__post_init__()

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedArrays(ScheduledArrays):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-arrays"

    def __post_init__(self):
        from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute="name", field_name="protected array members")
        require_sorted_unique_ids(self.producers, attribute="object_id", field_name="protected array producers")
        if ((self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION) or self.role not in ("PREFIX", "PREFIX_DIAGNOSTICS", "CAUSAL_STATE")
                or not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != "application/x-npz" or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(value.size_bytes for value in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.outcome_access is not BLIND or self.visibility_ceiling is not PROSPECTIVE):
            raise ValueError("selected E4 arrays change original complete members or protected phase classification")

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedPrefixHistory(ScheduledPrefixHistory):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-prefix-history"
    arrays: SelectedE4ProtectedArrays

    def __post_init__(self):
        validate_stable_id(self.history_id)
        if (type(self.arrays) is not SelectedE4ProtectedArrays or self.arrays.role != "PREFIX" or self.source != self.arrays.source
                or type(self.checkpoint) is not ScheduledCheckpoint or self.checkpoint.source != self.source
                or type(self.native) is not ScheduledNativeEvidence):
            raise ValueError("selected E4 prefix loses its complete original checkpoint/native evidence")

    def validate_source(self, source, *, config=None):
        if config is None:
            raise PermissionError("selected E4 prefix validation requires its actual installed compact configuration")
        from .selected_e4_native_bindings import native_contract
        configuration, parent_task, operation, sources = native_contract(config, source,
            recorded_operation=self.native.definition.operation_id)
        self.checkpoint.validate_source(source, self.arrays)
        _validate_prefix_native_evidence(self, source, configuration=configuration, parent_task=parent_task,
            operation=operation, native_sources=set(sources), output_access=BLIND, output_visibility=PROSPECTIVE)

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedNumericalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-numerical-assessment"
    assessment_id: str
    phase: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        kind = SelectedE4ProtectedPrefixHistory if self.phase == "prefix" else SelectedE4ProtectedFullHistory if self.phase == "full" else None
        if (kind is None or self.history.object_schema != kind.SCHEMA or (self.source.object_schema,self.source.object_version) != (ScheduledSource.SCHEMA,ScheduledSource.VERSION)
                or type(self.controls) is not tuple or any(type(value) is not MatrixParameterHistoryControl for value in self.controls)
                or tuple(value.control_id for value in self.controls) != HISTORY_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(value.disposition == "SATISFIED" for value in self.controls)):
            raise ValueError("selected E4 numerical assessment loses full original paired transition controls")
        n = self.controls[0].denominator_steps
        if tuple((value.denominator_steps, value.denominator_real_coordinates) for value in self.controls) != (
                (n, 192), (2 * n, 192), (n, 192), (n, 96)):
            raise ValueError("selected E4 numerical assessment changes original complete transition denominators")

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedWitness(ScheduledPrefixWitness):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-prefix-witness"
    arrays: SelectedE4ProtectedArrays

    def __post_init__(self):
        validate_stable_id(self.product_id)
        exact_pin(self.history, SelectedE4ProtectedPrefixHistory)
        exact_pin(self.numerical, SelectedE4ProtectedNumericalAssessment)
        if (type(self.arrays) is not SelectedE4ProtectedArrays or self.arrays.role != "PREFIX_DIAGNOSTICS"
                or self.arrays.source != self.source or type(self.traces) is not tuple or any(type(value) is not ScheduledPrefixTrace for value in self.traces)
                or tuple((value.view, value.sector) for value in self.traces) !=
                    (("PRIMARY", "X"), ("PRIMARY", "Y"), ("FINE", "X"), ("FINE", "Y"))):
            raise ValueError("selected E4 witness drops its actual causal lattice, complete traces or diagnostic members")

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedFrames(ScheduledFrameAssessment):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-frame-assessment"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact_pin(self.witness, SelectedE4ProtectedWitness)
        if (tuple(value.method for value in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(value.disposition in ("SATISFIED", "NOT_APPLICABLE") for value in self.controls)):
            raise ValueError("selected E4 frame assessment loses independent original eigenpair controls")
        n = len(self.controls[0].measured_errors)
        if (tuple(len(value.measured_errors) for value in self.controls) != (n, 15 * n, n, n, n, n)
                or tuple(value.denominator_real_coordinates for value in self.controls) != (225, 15, 225, 225, 48, 1)):
            raise ValueError("selected E4 frame assessment thins original paired eigenpair denominators")

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedCausalPrefix(ScheduledCausalPrefix):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-causal-prefix"
    arrays: SelectedE4ProtectedArrays

    def __post_init__(self):
        validate_stable_id(self.prefix_id)
        for value, kind in ((self.history, SelectedE4ProtectedPrefixHistory), (self.numerical, SelectedE4ProtectedNumericalAssessment),
                (self.witness, SelectedE4ProtectedWitness), (self.frame_assessment, SelectedE4ProtectedFrames)):
            exact_pin(value, kind)
        if (type(self.arrays) is not SelectedE4ProtectedArrays or self.arrays.role != "CAUSAL_STATE" or self.arrays.source != self.source
                or self.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION) or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE")
                or (self.disposition == "AVAILABLE") != (self.frame_sha256 is not None and self.reason is None)
                or self.disposition != "AVAILABLE" and self.reason is None):
            raise ValueError("selected E4 causal delivery changes source/frame/cutoff availability")

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedFeature(ScheduledForecastFeature):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-causal-feature"

    VERSION: ClassVar[str] = "2.0.0"
    physical_forecast: ObjectIdentity | None = None
    fine_response_defect: Decimal | None = None

    def __post_init__(self):
        from .selected_e3_e4_records import validate_selected_causal_feature
        validate_selected_causal_feature(self, SelectedE4ProtectedCausalPrefix, SelectedE4ProtectedMechanicalForecast)

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedAccountSeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-account-seal"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    design: ObjectIdentity
    source: ObjectIdentity
    prefix: ObjectIdentity
    feature: SelectedE4ProtectedFeature
    original_package: ObjectIdentity
    original_calibration: ObjectIdentity
    original_summary: p.SelectedE4OriginalCalibrationSummary
    log_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    revision: p.SelectedE4ForecastSeal | None
    decision: ObjectIdentity
    calibration: ObjectIdentity | None
    uncertainty_status: str = POINT_ONLY

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.decision, p.SelectedE4PublicRevisionDecision)
        if self.calibration is not None:
            exact_pin(self.calibration, p.SelectedE4PublicCalibration)
        if self.revision is not None:
            if (type(self.revision) is not p.SelectedE4ForecastSeal or self.revision.source != self.source
                    or self.revision.case_id != self.feature.root_id):
                raise ValueError("protected E4 account changes exact before-future revision seal")
            self.revision.__post_init__()
        exact_pin(self.design, SelectedE3E4ForecastDesign)
        exact_pin(self.prefix, SelectedE4ProtectedCausalPrefix)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import validate_selected_package_calibration
        validate_selected_package_calibration(self.original_package, self.original_calibration)
        if (type(self.original_summary) is not p.SelectedE4OriginalCalibrationSummary
                or self.original_summary.calibration != self.original_calibration
                or self.original_summary.original_package != self.original_package):
            raise ValueError("selected E4 account substitutes original calibration radius/rank or original-only scope")
        self.original_summary.__post_init__()
        from .selected_e3_e4_records import validate_selected_point_curves
        if (type(self.feature) is not SelectedE4ProtectedFeature or self.feature.source != self.source
                or self.feature.prefix != self.prefix or self.uncertainty_status != POINT_ONLY):
            raise ValueError('selected E4 seal changes its original causal inputs or point-only meaning')
        self.feature.__post_init__()
        validate_selected_point_curves(self.log_points, self.feature.disposition,
            matched=self.feature.physical_forecast is not None)

    @property
    def identity(self):
        return pin(self)

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedFullHistory(ScheduledFullHistory):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-full-history"

    def __post_init__(self):
        validate_stable_id(self.history_id)
        exact_pin(self.prefix, SelectedE4ProtectedPrefixHistory)
        exact_pin(self.forecast, SelectedE4ProtectedAccountSeal)
        exact_pin(self.checkpoint, ScheduledCheckpoint)
        if self.physical_forecast is not None:
            exact_pin(self.physical_forecast, SelectedE4ProtectedMechanicalForecast)
        if (type(self.arrays) is not ScheduledFullArrays or self.arrays.source != self.source or type(self.native) is not ScheduledNativeEvidence
                or type(self.completed_primary_steps) is not int or self.completed_primary_steps < 1
                or self.completed_fine_steps != 2 * self.completed_primary_steps
                or self.arrays.outcome_access is not SEALED or self.arrays.visibility_ceiling is not PROSPECTIVE):
            raise ValueError("selected E4 continuation changes complete original paired clock/native history")

    def validate_source(self, source, prefix, causal, seal, physical, *, config, prefix_config):
        from .selected_e4_native_bindings import native_contract
        prefix.validate_source(source, config=prefix_config)
        configuration, parent_task, operation, sources = native_contract(config, source,
            recorded_operation=self.native.definition.operation_id)
        validate_full_native_evidence(self, source, prefix, causal, seal, physical, configuration=configuration,
            parent_task=parent_task, operation=operation, shared_sources=sources)

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedMechanicalForecast(ScheduledResponseForecast):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-mechanical-forecast"

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        exact_pin(self.causal_prefix, SelectedE4ProtectedCausalPrefix)
        if (type(self.arrays) is not ScheduledResponseArrays or self.arrays.role != "FORECAST" or self.arrays.source != self.source
                or self.arrays.outcome_access is not BLIND or self.arrays.visibility_ceiling is not PROSPECTIVE
                or tuple((view, predictor) for view, predictor, _, _ in self.dispositions) != tuple((view, predictor) for view in ("PRIMARY", "FINE") for predictor in model_predictors(self.mechanical_model))
                or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")):
            raise ValueError("selected E4 mechanical forecast drops complete selected paired method instrument")

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedResponses(ScheduledResponseNative):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-native-responses"

    def validate_source(self, source, history, causal, physical, error, *, config, prefix_config):
        from .selected_e4_native_bindings import native_contract
        from .response_records import validate_response_native_evidence
        history.validate_source(source, config=prefix_config)
        protocol, panels = config.protocol, config.panels
        protocol.public_source.validate_source(source)
        if (self.source != identity(source) or self.causal_prefix != identity(causal)
                or self.physical_forecast != identity(physical) or self.error_forecast != error.identity
                or self.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or self.branch_ids != tuple(value[0] for value in branch_census(protocol, panels))
                or self.arrays.outcome_access is not SEALED or self.arrays.visibility_ceiling is not PROSPECTIVE):
            raise ValueError("selected E4 responses substitute actual source/cutoff/seals/complete48branch menu")
        if not self.native:
            if causal.disposition == "AVAILABLE" and physical.disposition == "AVAILABLE":
                raise ValueError("selected E4 cannot hide an available required native pulse collection")
            return
        configuration, parent_task, operation, sources = native_contract(config, source,
            recorded_operation=self.native[0].definition.operation_id)
        validate_response_native_evidence(self, source, config.response_selection, history, causal, physical, error,
            configuration=configuration, parent_task=parent_task, operation=operation, shared_sources=sources, panels=panels, protocol=protocol,
            native_sources=(*sources, identity(history), identity(history.checkpoint), identity(causal), identity(error), identity(physical))
                if operation.endswith(".direct-operands.v2") else None)

@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedNativeSource(CanonicalRecord):
    """Bounded native transport; its own bytes never impersonate the subject.

    Only the parent derives this record from the complete authenticated bank.
    Child arithmetic names the actual bounded reference as its scientific source.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-native-source"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    descriptor: ScheduledSource
    public: ScheduledPublicSource
    policy: ScheduledPrefixPolicy
    numerical_design: MatrixParameterNumericalDesign
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
        from .records import ScheduledPrefixPolicy
        validate_stable_id(self.record_id)
        exact_pin(self.programme, p.SelectedE4PhaseProgramme)
        exact_pin(self.bank, p.SelectedE4PhaseBank)
        for value, kind in ((self.descriptor, ScheduledSource), (self.public, ScheduledPublicSource),
                (self.policy, ScheduledPrefixPolicy), (self.numerical_design, MatrixParameterNumericalDesign),
                (self.provenance, NumericalProducingProvenance)):
            if type(value) is not kind:
                raise TypeError("selected E4 native transport requires exact original local operands")
            value.__post_init__()
        if (self.descriptor.identity != self.public.source or self.descriptor.root.root != self.public.root
                or self.descriptor.root.coordinate != ObjectIdentity.from_record(self.public.coordinate.coordinate_id, self.public.coordinate)
                or self.descriptor.provenance != self.provenance.identity or self.public.policy != self.policy
                or (self.public.allocation, self.public.reservation) != (self.descriptor.allocation, self.descriptor.reservation)
                or self.public.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)):
            raise ValueError("selected E4 local transport changes exact original root/policy/provenance")

    @classmethod
    def from_bank(cls, programme, bank, descriptor, *, index):
        if descriptor not in bank.sources or programme.bank != pin(bank, "bank_id"):
            raise ValueError("selected E4 native transport is outside its authenticated whole programme")
        source = bank.source(descriptor.root_id,index=index)
        return cls("native." + source.source_id, programme.identity, pin(bank, "bank_id"), descriptor,
            ScheduledPublicSource.from_source(source), source.policy, source.numerical_design, source.provenance)

    @property
    def identity(self):
        return pin(self)

    @property
    def reference(self):
        return self.descriptor

    @property
    def root(self):
        return self.descriptor.root

    @property
    def root_id(self):
        return self.descriptor.root_id

    @property
    def coordinate(self):
        return self.public.coordinate

    @property
    def evidence_role(self):
        return "ELIGIBLE_UNENTERED_CANDIDATE"



@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedNativeSourceReference(CanonicalRecord):
    """Bounded source reference; full provenance is a separate exact input.

    Only the parent derives this record from the complete authenticated bank.
    Child arithmetic names the actual bounded reference as its scientific source.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-native-source-reference"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    descriptor: ScheduledSource
    public: ScheduledPublicSource
    policy: ScheduledPrefixPolicy
    numerical_design: MatrixParameterNumericalDesign
    provenance: ObjectIdentity
    provenance_size_bytes: int

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
        from .records import ScheduledPrefixPolicy
        validate_stable_id(self.record_id)
        exact_pin(self.programme, p.SelectedE4PhaseProgramme)
        exact_pin(self.bank, p.SelectedE4PhaseBank)
        for value, kind in ((self.descriptor, ScheduledSource), (self.public, ScheduledPublicSource),
                (self.policy, ScheduledPrefixPolicy), (self.numerical_design, MatrixParameterNumericalDesign),
                (self.provenance, ObjectIdentity)):
            if type(value) is not kind:
                raise TypeError("selected E4 native transport requires exact original local operands")
            value.__post_init__()
        exact_pin(self.provenance, NumericalProducingProvenance)
        if (type(self.provenance_size_bytes) is not int or self.provenance_size_bytes < 1
                or self.descriptor.identity != self.public.source or self.descriptor.root.root != self.public.root
                or self.descriptor.root.coordinate != ObjectIdentity.from_record(self.public.coordinate.coordinate_id, self.public.coordinate)
                or self.descriptor.provenance != self.provenance or self.public.policy != self.policy
                or (self.public.allocation, self.public.reservation) != (self.descriptor.allocation, self.descriptor.reservation)
                or self.public.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)):
            raise ValueError("selected E4 local transport changes exact original root/policy/provenance")

    @classmethod
    def from_bank(cls, programme, bank, descriptor, *, index):
        if descriptor not in bank.sources or programme.bank != pin(bank, "bank_id"):
            raise ValueError("selected E4 native transport is outside its authenticated whole programme")
        source = bank.source(descriptor.root_id,index=index)
        return cls("native." + source.source_id, programme.identity, pin(bank, "bank_id"), descriptor,
            ScheduledPublicSource.from_source(source), source.policy, source.numerical_design, source.provenance.identity, len(source.provenance.canonical_bytes()))

    @property
    def identity(self):
        return pin(self)

    @property
    def reference(self):
        return self.descriptor

    @property
    def root(self):
        return self.descriptor.root

    @property
    def root_id(self):
        return self.descriptor.root_id

    @property
    def coordinate(self):
        return self.public.coordinate

    @property
    def evidence_role(self):
        return "ELIGIBLE_UNENTERED_CANDIDATE"

@dataclass(frozen=True, slots=True)
class SelectedE4DevelopmentProduct(CanonicalRecord):
    """Original DEV producer locator; no issued or reveal authority is invented."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/development-product"
    record: ObjectIdentity
    authored_directory: str
    run_id: str
    execution_plan: ObjectIdentity
    task_id: str
    receipt: ObjectIdentity
    publication: ArtifactWriteResult

    def __post_init__(self):
        from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
        from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
        from empirical_lawhood.runtime.artifacts import validate_relative_locator
        validate_relative_locator(self.authored_directory)
        for value in (self.run_id, self.task_id):
            validate_stable_id(value)
        for value, kind in ((self.execution_plan, DevelopmentExecutionPlan), (self.receipt, CanonicalTaskReceipt)):
            exact_pin(value, kind)
        if type(self.publication) is not ArtifactWriteResult or type(self.record) is not ObjectIdentity:
            raise TypeError("selected DEV locator retains exact published original custody")
        if (self.record.object_schema, self.record.object_fingerprint) != (
                self.publication.logical.payload_schema, self.publication.logical.content_sha256):
            raise ValueError("selected DEV locator changes original canonical bytes")


@dataclass(frozen=True, slots=True)
class SelectedE4SourceQualification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/source-qualification"
    record_id: str
    specification: ScientificSourceQualificationSpec
    result: ScientificSourceQualificationResult
    pipeline: MatrixSourcePipelineEvidence
    executions: tuple[RecursivePriorExecutionBinding, ...]
    publications: tuple[tuple[ObjectIdentity, ArtifactWriteResult], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, ScientificSourceQualificationSpec),
                (self.result, ScientificSourceQualificationResult), (self.pipeline, MatrixSourcePipelineEvidence)):
            if type(value) is not kind:
                raise TypeError("protected E4 source requires exact original qualifier inputs")
            value.__post_init__()
        if (type(self.executions) is not tuple or any(type(v) is not RecursivePriorExecutionBinding for v in self.executions)
                or tuple(v.record.object_id for v in self.executions) != tuple(sorted({v.record.object_id for v in self.executions}))
                or type(self.publications) is not tuple
                or any(type(v) is not tuple or len(v) != 2 or type(v[0]) is not ObjectIdentity or type(v[1]) is not ArtifactWriteResult for v in self.publications)
                or tuple(v[0].object_id for v in self.publications) != tuple(sorted({v[0].object_id for v in self.publications}))):
            raise ValueError("protected E4 qualification aliases original executions/publications")

    @property
    def identity(self):
        return pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-evidence"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    upstream_products: tuple[MatrixSelectedOriginalProduct, ...]
    development_nomination: SelectedE4DevelopmentProduct
    development_freeze: SelectedE4DevelopmentProduct
    source: SelectedE4SourceQualification
    calibration_product: MatrixSelectedOriginalProduct | None
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.programme, p.SelectedE4PhaseProgramme)
        if (type(self.upstream_products) is not tuple or len(self.upstream_products) != 4
                or any(type(v) is not MatrixSelectedOriginalProduct for v in self.upstream_products)
                or tuple(v.record.object_id for v in self.upstream_products) != tuple(sorted({v.record.object_id for v in self.upstream_products}))
                or type(self.development_nomination) is not SelectedE4DevelopmentProduct
                or type(self.development_freeze) is not SelectedE4DevelopmentProduct
                or type(self.source) is not SelectedE4SourceQualification
                or self.calibration_product is not None and type(self.calibration_product) is not MatrixSelectedOriginalProduct):
            raise TypeError("protected E4 entry requires complete original issued E3, DEV and source custody")
        for v in (*self.upstream_products,self.development_nomination,self.development_freeze,self.source):
            v.__post_init__()
        if self.calibration_product is not None:
            self.calibration_product.__post_init__()
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents
        validate_produced_input_parents(self.produced_input_parents)
        expected = {pin for value in self.upstream_products for pin in (value.record, value.prior_execution.receipt)}
        expected.update(pin for value in (self.development_nomination, self.development_freeze)
            for pin in (value.record, value.receipt))
        if self.calibration_product is not None:
            expected.update((self.calibration_product.record, self.calibration_product.prior_execution.receipt))
        if {value.identity for value in self.produced_input_parents} != expected:
            raise ValueError("selected E4 protected evidence changes its complete actual produced-parent census")

    @property
    def identity(self):
        return pin(self)


def validate_evidence(evidence, programme, bank, decision, models, calibration):
    from empirical_lawhood.planning.metatheory import MetatheoryAggregateDisposition, MetatheoryApplicability
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateKind
    p.validate_selected_phase_bank(programme, bank)
    if type(evidence) is not SelectedE4ProtectedEvidence or type(decision) is not p.SelectedE4PublicRevisionDecision:
        raise TypeError("protected E4 requires exact evidence and bounded public revision decision")
    evidence.__post_init__()
    decision.__post_init__()
    package = bank.forecast_design.package
    expected = {identity(package.models),identity(package.model_freeze),package.calibration,identity(package.calibrated_freeze)}
    if (evidence.programme != programme.identity or {v.record for v in evidence.upstream_products} != expected
            or evidence.development_nomination.record != decision.nomination or evidence.development_freeze.record != decision.frozen
            or (models is None) != (not decision.fit_available)):
        raise ValueError("protected E4 changes original E3 products or enters an untriggered calibration")
    if models is not None:
        if (type(models) is not p.SelectedE4PublicModels or (models.development,models.nomination,models.frozen,
                models.revision_model.identity,models.baseline_model.identity) !=
                (decision.development,decision.nomination,decision.frozen,decision.revision_model,decision.baseline_model)):
            raise ValueError("protected E4 substitutes actual frozen public revision/baseline")
        models.__post_init__()
        if ((models.development_design.factors,models.development_design.confidence) != (programme.factors,programme.confidence)
                or models.target.criterion != programme.criterion
                or decision.relation_fit != (None if models.relation_fit is None else models.relation_fit.identity)):
            raise ValueError("protected E4 changes original frozen factor grid or confidence")
    if programme.mode == "E4_CONFIRMATION" and models is not None:
        if type(calibration) is not p.SelectedE4PublicCalibration or evidence.calibration_product is None or evidence.calibration_product.record != calibration.original:
            raise ValueError("triggered confirmation needs actual original sealed E4 calibration producer")
        calibration.__post_init__()
        if (calibration.specification.development_programme,calibration.specification.nomination,calibration.specification.frozen_models,
                calibration.revision_model,calibration.baseline_model) != (
                decision.development,decision.nomination,decision.frozen,decision.revision_model,decision.baseline_model):
            raise ValueError("confirmation substitutes matched E4 calibration/model lineage")
        if set(calibration.group_ids).intersection(programme.group_ids):
            raise ValueError("confirmation reuses original E4 CAL groups")
        if calibration.relation_fit != decision.relation_fit:
            raise ValueError('confirmation changes its original fitted relation identity')
    elif calibration is not None or evidence.calibration_product is not None:
        raise ValueError("non-confirmation or untriggered revision cannot invent an E4 calibration")
    spec,result = evidence.source.specification,evidence.source.result
    # Every validated compact subject binds the bank's same specification;
    # ScheduledSource.numerical_design delegates to this shared typed owner.
    numerical = identity(bank.specification.selection.numerical_design)
    if (spec.source_identity != bank.identity or spec.preparation != identity(bank.reservation)
            or spec.observation_operator != bank.response_selection.identity or spec.numerical_view != numerical
            or spec.maximum_ordinary_evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
            or spec.physical_unit_ids != programme.group_ids or spec.expected_physical_unit_count != len(programme.group_ids)
            or spec.outcome_access is not BLIND or spec.visibility_ceiling is not PROSPECTIVE
            or result.qualification_spec != pin(spec,"spec_id")
            or spec.source_pipeline_qualification != pin(evidence.source.pipeline.receipt,"receipt_id")
            or result.source_pipeline_qualification != spec.source_pipeline_qualification
            or result.disposition is not MetatheoryAggregateDisposition.SUPPORTED
            or result.complete_physical_unit_count != len(programme.group_ids)
            or result.eligible_physical_unit_count != len(programme.group_ids) or result.invalid_physical_unit_count != 0):
        raise ValueError("protected E4 source qualification changes whole-group/preparation/assay/numerical scope")
    required = set(ScientificSourceGateKind)-{ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE}
    gates={v.gate_kind:v for v in spec.gates}
    if any(gates[k].applicability is not MetatheoryApplicability.REQUIRED or bank.identity not in gates[k].required_operands for k in required):
        raise ValueError("protected E4 source lacks independent original complete required gate scopes")
    if (identity(bank.reservation) not in gates[ScientificSourceGateKind.PREPARATION].required_operands
            or bank.response_selection.identity not in gates[ScientificSourceGateKind.OBSERVATION_OPERATOR].required_operands
            or numerical not in gates[ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY].required_operands):
        raise ValueError("protected E4 source gates omit actual scientific premises")


@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedEntrySeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-entry-seal"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    forecast_design: ObjectIdentity
    evidence: ObjectIdentity
    groups: tuple[str,...]
    sources: tuple[ObjectIdentity,...]
    population_phase: str
    wave_id: str | None
    wave_evidence: ObjectIdentity | None
    decision: ObjectIdentity
    models: ObjectIdentity | None
    calibration: ObjectIdentity | None

    secondary_readout: ObjectIdentity

    def __post_init__(self):
        exact_pin(self.secondary_readout, MatrixE4SecondaryReadoutSelection)
        validate_stable_id(self.record_id)
        for value,kind in ((self.programme,p.SelectedE4PhaseProgramme),(self.bank,p.SelectedE4PhaseBank),
                (self.forecast_design,SelectedE3E4ForecastDesign),(self.evidence,SelectedE4ProtectedEvidence),
                (self.decision,p.SelectedE4PublicRevisionDecision)):
            exact_pin(value,kind)
        if (self.population_phase not in POPULATIONS or type(self.groups) is not tuple or not self.groups
                or self.groups != tuple(sorted(set(self.groups))) or type(self.sources) is not tuple
                or len(self.sources) != 9*len(self.groups) or tuple(v.object_id for v in self.sources) != tuple(sorted({v.object_id for v in self.sources}))):
            raise ValueError("protected E4 entry changes complete declared whole-group census")
        if (self.wave_id is None)!=(self.wave_evidence is not None):
            raise ValueError("selected E4 entry cannot substitute a wave for complete phase custody")
        if self.wave_id is not None:validate_stable_id(self.wave_id)
        if self.wave_evidence is not None:exact_pin(self.wave_evidence,SelectedE4PhaseCollectionEvidence)
        if self.models is not None:exact_pin(self.models,p.SelectedE4PublicModels)
        if self.calibration is not None:exact_pin(self.calibration,p.SelectedE4PublicCalibration)

    @property
    def identity(self):
        return pin(self)


def entry_seal(config,evidence,*,bank):
    validate_evidence(evidence,config.programme,bank,config.decision,config.models,config.calibration)
    return SelectedE4ProtectedEntrySeal("entry."+config.programme.programme_id+("" if config.wave_id is None else "."+config.wave_id),config.programme.identity,config.programme.bank,
        config.programme.forecast_design,evidence.identity,config.scope_group_ids,tuple(v.source for v in config.scope_cases),
        config.declaration.bank_phase,config.wave_id,config.wave_evidence,config.decision.identity,None if config.models is None else config.models.identity,
        None if config.calibration is None else config.calibration.identity, config.secondary_readout.identity)


@dataclass(frozen=True,slots=True)
class SelectedE4NativeCaseResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/native-case-result"
    VERSION: ClassVar[str] = "3.0.0"
    root_id:str
    source:ObjectIdentity
    group_id:str
    disposition:str
    numerical_disposition:str
    score_disposition:str
    paired_log_targets:tuple[Decimal|None,...]
    original_log_points:tuple[tuple[str,tuple[Decimal|None,...]],...]
    forecast:ObjectIdentity|None
    score:ObjectIdentity|None
    full_assessment:ObjectIdentity|None
    ordinary_receipts:tuple[ScheduledProgrammeReceiptReference,...]
    native:tuple[ScheduledProgrammeNativeDisposition,...]
    reason_codes:tuple[str,...]
    causal_prefix:p.SelectedE4PrefixProjection|None
    score_projection:p.SelectedE4ScoreProjection|None
    revision_seal:p.SelectedE4ForecastSeal|None
    coordinate:MatrixParameterCoordinate
    target_contract:str = "PAIRED15"
    causal_feature:p.SelectedE4CausalFeatureProjection|None = None

    def __post_init__(self):
        from .programme_reduction import NATIVE_PHASES,NUMERICAL_DISPOSITIONS,DISPOSITIONS
        for v in (self.root_id,self.group_id):validate_stable_id(v)
        exact_pin(self.source,ScheduledSource)
        from .selected_e3_e4_records import selected_target_shape
        methods, point_count, target_count = selected_target_shape(self.target_contract)
        if type(self.coordinate) is not MatrixParameterCoordinate:raise TypeError("selected E4 case retains actual original coordinate")
        self.coordinate.__post_init__()
        if (self.disposition not in DISPOSITIONS or self.numerical_disposition not in NUMERICAL_DISPOSITIONS
                or type(self.paired_log_targets) is not tuple or len(self.paired_log_targets)!=target_count
                or type(self.original_log_points) is not tuple or tuple(k for k,_ in self.original_log_points)!=methods
                or any(type(v) is not tuple or len(v)!=point_count for _,v in self.original_log_points)
                or type(self.native) is not tuple or tuple(v.phase for v in self.native)!=NATIVE_PHASES
                or type(self.ordinary_receipts) is not tuple or any(type(v) is not ScheduledProgrammeReceiptReference for v in self.ordinary_receipts)
                or tuple(v.receipt_id for v in self.ordinary_receipts)!=tuple(sorted({v.receipt_id for v in self.ordinary_receipts}))
                or type(self.reason_codes) is not tuple or self.reason_codes!=tuple(sorted(set(self.reason_codes)))):
            raise ValueError("protected E4 result loses actual complete adverse/endpoint/native/receipt census")
        for v,k in ((self.forecast,SelectedE4ProtectedAccountSeal),(self.score,ScheduledResponseScore),(self.full_assessment,SelectedE4ProtectedNumericalAssessment)):
            if v is not None:exact_pin(v,k)
        for v in (*self.paired_log_targets,*(v for _,vs in self.original_log_points for v in vs)):
            if v is not None:validate_decimal(v,field_name="actual cumulative endpoint",minimum=Decimal(0))
        if self.score_projection is not None:
            self.score_projection.__post_init__()
            if self.score_projection.target_contract != self.target_contract:
                raise ValueError("protected E4 collector changes the original target contract")
            if (self.score_projection.original,self.score_projection.source,self.score_projection.root_id,self.score_projection.independent_group_id,
                    self.score_projection.error_forecast,self.score_projection.paired_log_targets)!=(self.score,self.source,self.root_id,self.group_id,self.forecast,self.paired_log_targets):
                raise ValueError("protected E4 collector substitutes actual score projection")
        if self.causal_prefix is not None:
            self.causal_prefix.__post_init__()
            if self.causal_prefix.source!=self.source or self.causal_prefix.root.root_id!=self.root_id:
                raise ValueError("protected E4 collector substitutes actual causal prefix")
        if self.revision_seal is not None:
            self.revision_seal.__post_init__()
            if (self.revision_seal.source,self.revision_seal.case_id,self.revision_seal.independent_group_id)!=(self.source,self.root_id,self.group_id):
                raise ValueError("protected E4 collector substitutes actual revision forecast")
        if self.target_contract == 'MATCHED_FACTOR58':
            if (self.forecast is None) != (self.causal_feature is None):
                raise ValueError('matched E4 collector loses its actual sealed causal features')
            if self.causal_feature is not None:
                if type(self.causal_feature) is not p.SelectedE4CausalFeatureProjection:
                    raise TypeError('matched E4 collector requires the original typed feature projection')
                self.causal_feature.__post_init__()
                if ((self.causal_feature.original_account, self.causal_feature.source, self.causal_feature.root_id,
                        self.causal_feature.independent_group_id) != (self.forecast, self.source, self.root_id, self.group_id)
                        or self.causal_prefix is None or self.causal_feature.prefix != self.causal_prefix.original):
                    raise ValueError('matched E4 collector substitutes original causal account lineage')
        elif self.causal_feature is not None:
            raise ValueError('closed E4 collector invents a matched causal projection')

    @property
    def revision_forecast(self):
        return None if self.revision_seal is None else self.revision_seal.identity


@dataclass(frozen=True,slots=True)
class SelectedE4NativeReduction(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/native-reduction"
    VERSION: ClassVar[str] = '2.0.0'
    record_id:str
    programme:ObjectIdentity
    bank:ObjectIdentity
    cases:tuple[SelectedE4NativeCaseResult,...]
    group_ids:tuple[str,...]
    wave_id:str|None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.programme,p.SelectedE4PhaseProgramme)
        exact_pin(self.bank,p.SelectedE4PhaseBank)
        if (type(self.cases) is not tuple or any(type(v) is not SelectedE4NativeCaseResult for v in self.cases)
                or tuple(v.root_id for v in self.cases)!=tuple(sorted({v.root_id for v in self.cases}))
                or type(self.group_ids) is not tuple or self.group_ids!=tuple(sorted({v.group_id for v in self.cases}))
                or not self.group_ids or len(self.cases)!=9*len(self.group_ids)
                or any(sum(v.group_id==g for v in self.cases)!=9 for g in self.group_ids)):
            raise ValueError("protected E4 reduction drops a declared whole group or coordinate")
        for v in self.cases:v.__post_init__()

    @property
    def identity(self):
        return pin(self)


@dataclass(frozen=True,slots=True)
class SelectedE4NativeBudgets(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/native-budgets"
    record_id:str
    phase_budgets:tuple[tuple[str,ResourceBudget],...]
    collector_budget:ResourceBudget

    def __post_init__(self):
        from .selected_e4_native_bindings import PHASES
        from .operation_bindings import BUDGET
        validate_stable_id(self.record_id)
        if (type(self.phase_budgets) is not tuple or any(type(v) is not tuple or len(v)!=2 for v in self.phase_budgets)
                or tuple(k for k,_ in self.phase_budgets)!=tuple(sorted(PHASES))
                or any(type(v) is not ResourceBudget or not BUDGET.contains(v) for _,v in self.phase_budgets)
                or type(self.collector_budget) is not ResourceBudget or not BUDGET.contains(self.collector_budget)):
            raise ValueError("selected E4 needs every explicit actual native phase budget and collector budget")
        for v in (*[value for _,value in self.phase_budgets],self.collector_budget):
            v.__post_init__()
            if (v.wall_time_seconds is not None or v.gpu_devices!=0
                    or any(type(x) is not int or x<0 for x in (v.memory_bytes,v.source_scan_bytes,v.output_bytes))
                    or v.memory_bytes==0):
                raise ValueError("selected E4 native budgets require explicit finite memory/source/output and no clock deadline")
        self.collector_budget.__post_init__()

    @property
    def identity(self):
        return pin(self)


@dataclass(frozen=True,slots=True)
class SelectedE4NativeProgrammeDeclaration(CanonicalRecord):
    """Full frozen scientific membership and planned budgets before any wave."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/native-programme-declaration"
    VERSION:ClassVar[str]="2.0.0"
    record_id:str
    programme:p.SelectedE4PhaseProgramme
    bank:ObjectIdentity
    bank_publication:ArtifactWriteResult
    root:StudyDraft
    evidence:ObjectIdentity
    decision:p.SelectedE4PublicRevisionDecision
    models:p.SelectedE4PublicModels|None
    calibration:p.SelectedE4PublicCalibration|None
    budgets:SelectedE4NativeBudgets
    maximum_parallel_tasks:int
    original_summary:p.SelectedE4OriginalCalibrationSummary
    produced_input_parents:tuple[ArtifactLineageParent,...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents
        validate_produced_input_parents(self.produced_input_parents)
        if type(self.programme) is not p.SelectedE4PhaseProgramme:
            raise TypeError("selected E4 declaration needs actual whole programme")
        self.programme.__post_init__()
        exact_pin(self.bank,p.SelectedE4PhaseBank)
        if (self.programme.bank!=self.bank or type(self.bank_publication) is not ArtifactWriteResult
                or (self.bank_publication.logical.payload_schema,self.bank_publication.logical.content_sha256)!=(self.bank.object_schema,self.bank.object_fingerprint)):
            raise ValueError("selected E4 declaration changes original source bank publication")
        validate_stable_id(self.record_id)
        exact_pin(self.evidence,SelectedE4ProtectedEvidence)
        if (type(self.root) is not StudyDraft or self.root.system is None or self.root.experiment is None
                or self.root.campaign is None or self.root.development_unit_ids or self.root.evaluation_unit_ids!=self.programme.group_ids
                or self.root.experiment.information_cutoffs!=tuple(v.information_cutoff for v in self.programme.cases)
                or self.root.unresolved_decisions or type(self.maximum_parallel_tasks) is not int or self.maximum_parallel_tasks<1
                or type(self.budgets) is not SelectedE4NativeBudgets):
            raise ValueError("selected E4 declaration changes complete frozen phase/root/worker selection")
        self.root.__post_init__()
        self.budgets.__post_init__()
        if type(self.original_summary) is not p.SelectedE4OriginalCalibrationSummary:
            raise TypeError("selected E4 full declaration needs actual original E3 calibration summary")
        self.original_summary.__post_init__()
        required={self.programme.identity,self.bank,self.programme.reservation,self.programme.allocation,
            self.programme.specification,self.programme.forecast_design,self.programme.response_selection,self.programme.criterion,
            self.evidence,self.decision.identity,self.original_summary.identity,*self.programme.source_census}
        if self.models is not None:required.add(self.models.identity)
        if self.calibration is not None:required.add(self.calibration.identity)
        if not required<={v.object_identity for v in self.root.design_inputs}:
            raise ValueError("selected E4 full declaration omits actual frozen source, model or scientific design")
        if self.decision.fit_available!=(self.models is not None):
            raise ValueError("selected E4 declaration invents or omits frozen revision models")

    @property
    def identity(self):
        return pin(self)

    @property
    def bank_phase(self):return "CALIBRATION" if self.programme.mode=="E4_REVISION_CALIBRATION" else "CONFIRMATION"

    def wave(self,wave_id):
        rows=tuple(v for v in self.programme.waves if v.wave_id==wave_id)
        if len(rows)!=1:raise ValueError("selected E4 wave is outside the full frozen programme")
        return rows[0]

    @property
    def planned_task_budgets(self):
        from .selected_e4_native_bindings import PHASES,global_node,local_node
        selected=dict(self.budgets.phase_budgets)
        result=[]
        for wave in self.programme.waves:
            result.extend((global_node(self.programme,phase,wave.wave_id),selected[phase]) for phase in ("entry","reduce"))
            result.append((global_node(self.programme,"adjudicate",wave.wave_id),self.budgets.collector_budget))
            result.extend((local_node(root,phase),selected[phase]) for root in wave.root_ids for phase in PHASES if phase not in ("entry","reduce"))
        result.extend(((global_node(self.programme,"phase-entry"),selected["entry"]),
            (global_node(self.programme,"phase-collect"),self.budgets.collector_budget)))
        return tuple(sorted(result))


@dataclass(frozen=True,slots=True)
class SelectedE4WaveScope(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/wave-scope"
    declaration:ObjectIdentity
    programme:p.SelectedE4PhaseProgramme
    wave:ScheduledProgrammeWave
    global_root:StudyDraft

    def __post_init__(self):
        exact_pin(self.declaration,SelectedE4NativeProgrammeDeclaration)
        if type(self.programme) is not p.SelectedE4PhaseProgramme or self.wave not in self.programme.waves or type(self.global_root) is not StudyDraft:
            raise ValueError("selected E4 component changes its frozen full programme or declared whole-group wave")

    @property
    def acquisition_id(self):return "acquisition."+self.wave.wave_id
    @property
    def identity(self):return pin(self,"acquisition_id")
    @property
    def global_root_identity(self):return pin(self.global_root,"draft_id")
    @property
    def global_experiment_identity(self):return pin(self.global_root.experiment,"experiment_id")


@p._decimal_context_cache
def phase_root(declaration):
    from dataclasses import replace
    from empirical_lawhood.planning.study_authoring import DesignInputRecord,DesignInputRole
    root=declaration.root
    if not root.design_inputs or len({v.information_cutoff for v in root.design_inputs})!=1:
        raise ValueError("selected E4 declaration needs exact pre-entry design cutoff")
    first=root.design_inputs[0]
    item=DesignInputRecord("design."+declaration.record_id+".full-native-declaration",declaration.identity,declaration.fingerprint(),
        first.information_cutoff,DesignInputRole.READINESS_METADATA,BLIND,PROSPECTIVE,first.operator_id)
    designs=tuple(sorted((*root.design_inputs,item),key=lambda v:v.input_id))
    from .selected_e4_method_bindings import method_node
    operations = (("revision-calibrate",) if declaration.bank_phase == "CALIBRATION"
        else ("confirmation-assess", "downstream-nominate"))
    experiment = replace(root.experiment, reveal_barrier=replace(root.experiment.reveal_barrier,
        sealed_outcome_artifact_ids=tuple(sorted("scientific." + method_node(declaration.programme.identity, operation)
            + ".product" for operation in operations))))
    previous = pin(root.experiment,"experiment_id")
    current = pin(experiment,"experiment_id")
    campaign = replace(root.campaign, nodes=tuple(replace(value,
        object_identity=current if value.object_identity == previous else value.object_identity) for value in root.campaign.nodes))
    return replace(root,experiment=experiment,campaign=campaign,design_inputs=designs,
        design_origin=replace(root.design_origin,declared_input_ids=tuple(v.input_id for v in designs)))


@p._decimal_context_cache
def wave_root(declaration,wave_id,*,views):
    from .programme_acquisition import _local_root
    declaration.__post_init__()
    wave=declaration.wave(wave_id)
    scope=SelectedE4WaveScope(declaration.identity,declaration.programme,wave,phase_root(declaration))
    local=_local_root(scope,views)
    # The original neutral data-root builder supplies no native mathematics.
    # Bind its operational references to these actual additive producers.
    from dataclasses import replace
    from .selected_e4_native_bindings import NAMESPACE,global_node
    old=local.experiment
    claims=tuple(replace(v,estimand=v.estimand.replace("fifteen-endpoint","complete-paired-endpoint")) for v in old.claims)
    experiment=replace(old,claims=claims,controls=tuple(replace(v,capability_key=NAMESPACE+".mechanical") for v in old.controls),
        obligations=replace(old.obligations,falsifiers=tuple(replace(v,capability_key=NAMESPACE+".full-numerical")
            for v in old.obligations.falsifiers)),
        precision_goals=tuple(replace(v,stopping_rule=v.stopping_rule.replace("fifteen endpoint","declared paired endpoint"))
            for v in old.precision_goals),
        reveal_barrier=replace(old.reveal_barrier,sealed_outcome_artifact_ids=(
            "scientific."+global_node(declaration.programme,"reduce",wave_id)+".product",)))
    substitutions={pin(old,"experiment_id"):pin(experiment,"experiment_id")}
    substitutions.update((pin(before,"claim_id"),pin(after,"claim_id")) for before,after in zip(old.claims,claims,strict=True))
    campaign=replace(local.campaign,nodes=tuple(replace(v,object_identity=substitutions.get(v.object_identity,v.object_identity))
        for v in local.campaign.nodes))
    return replace(local,experiment=experiment,campaign=campaign)


@dataclass(frozen=True,slots=True)
class SelectedE4WaveLocator(CanonicalRecord):
    """Actual issued wave metadata; no completion or success assertion."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/wave-locator"
    wave_id:str
    run_id:str
    package:ObjectIdentity
    issued_study:ObjectIdentity
    execution_authority:ObjectIdentity
    reveal_authority:ObjectIdentity
    execution_plan:ObjectIdentity

    def __post_init__(self):
        from empirical_lawhood.runtime.plans import ExecutionPlan
        for v in (self.wave_id,self.run_id):validate_stable_id(v)
        if self.package.object_schema!="empirical-lawhood/api/experiment-package":raise ValueError("selected wave changes actual experiment package schema")
        exact_pin(self.execution_plan,ExecutionPlan)
        for v in (self.issued_study,self.execution_authority,self.reveal_authority):
            if type(v) is not ObjectIdentity:raise TypeError("selected wave requires actual original issue/grant pins")
            v.__post_init__()


@dataclass(frozen=True,slots=True)
class SelectedE4WaveObservation(CanonicalRecord):
    """Bounded observation of a complete original terminal, including failure."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/wave-observation"
    record_id:str
    declaration:ObjectIdentity
    wave_id:str
    execution_plan:ObjectIdentity
    terminal:ObjectIdentity
    cases:tuple[SelectedE4NativeCaseResult,...]
    operational_events:tuple[ObjectIdentity,...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.wave_id)
        exact_pin(self.declaration,SelectedE4NativeProgrammeDeclaration)
        if (type(self.cases) is not tuple or not self.cases or any(type(v) is not SelectedE4NativeCaseResult for v in self.cases)
                or tuple(v.root_id for v in self.cases)!=tuple(sorted({v.root_id for v in self.cases}))
                or type(self.operational_events) is not tuple or tuple(v.object_id for v in self.operational_events)!=tuple(sorted({v.object_id for v in self.operational_events}))):
            raise ValueError("selected E4 wave observation loses original assigned cases or operational events")
        for v in self.cases:v.__post_init__()

    @property
    def identity(self):return pin(self)


@dataclass(frozen=True,slots=True)
class SelectedE4WaveInput(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/wave-input"
    locator:SelectedE4WaveLocator
    observation:ObjectIdentity
    size_bytes:int

    def __post_init__(self):
        if type(self.locator) is not SelectedE4WaveLocator:raise TypeError("selected E4 phase requires actual original wave locator")
        self.locator.__post_init__()
        exact_pin(self.observation,SelectedE4WaveObservation)
        if type(self.size_bytes) is not int or not 0<self.size_bytes<=64*1024**2:
            raise ValueError("selected E4 wave projection changes exact bounded original observation")


@dataclass(frozen=True,slots=True)
class SelectedE4PhaseCollectionEvidence(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/phase-collection-evidence"
    record_id:str
    declaration:ObjectIdentity
    waves:tuple[SelectedE4WaveInput,...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_pin(self.declaration,SelectedE4NativeProgrammeDeclaration)
        if (type(self.waves) is not tuple or not self.waves or any(type(v) is not SelectedE4WaveInput for v in self.waves)
                or tuple(v.locator.wave_id for v in self.waves)!=tuple(sorted({v.locator.wave_id for v in self.waves}))
                or len({v.locator.run_id for v in self.waves})!=len(self.waves)):
            raise ValueError("selected E4 phase collection aliases original wave/issued-run census")
        for v in self.waves:v.__post_init__()

    @property
    def identity(self):return pin(self)
