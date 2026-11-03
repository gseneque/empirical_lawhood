# SPDX-License-Identifier: MPL-2.0
"""New parameter response identities; historical contracts remain unchanged.

Source checks authenticate typed operands and receipt joins. Infrastructure
authenticates their actual bytes. Exposed derived history is conditional reuse;
an absent original enclosing return never becomes a successful original task.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorStream
from empirical_lawhood.adapters.methods.matrix_factor_response.records import (
    ACTION_ROLES, EXPOSED, PREDICTORS, SIGNS, MatrixFactorAction, MatrixFactorResponseScore,
)
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    MatrixParameterFactorAssessment, MatrixParameterFactorProduct, MatrixParameterFactorSource,
    MatrixParameterFactorSupply, identity as factor_identity,
    native_metadata_identity,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    MatrixParameterAllocation, MatrixParameterHistorySource, coordinate_identity,
    identity as history_identity,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import (
    MatrixIntegratorKind, MatrixPrecision, SixMatrixResponseNumericalView,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition,
)

CONTINUATION = 'CONTINUE_FROZEN_AUTONOMOUS_COUPLINGS_FOR_DECLARED_ASSAY_DURATION'


def identity(record):
    for name in ('source_id', 'allocation_id', 'design_id', 'selection_id', 'origin_id', 'forecast_id',
                 'response_id', 'assessment_id', 'operand_id', 'config_id', 'model_id', 'frontier_id', 'census_id',
                 'product_id', 'history_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('parameter response record lacks its declared identity')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/root'
    original: MatrixProgrammeRoot
    streams: tuple[MatrixFactorStream, ...]

    def __post_init__(self):
        require_sorted_unique_ids(self.streams, attribute='purpose_id', field_name='future streams')
        if (type(self.original) is not MatrixProgrammeRoot or self.original.role is not MatrixProgrammeRole.DEVELOPMENT
                or tuple(sorted(s.role for s in self.streams)) != ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                or len({s.panel_id for s in self.streams}) != 2 or len({s.seed for s in self.streams}) != 2):
            raise ValueError('parameter response root changes development or future-only two-panel allocation')

    @property
    def root_id(self):
        return self.original.root_id

    @property
    def independent_group_id(self):
        return self.original.independent_group_id

    @property
    def clock_id(self):
        return self.original.clock_id

    @property
    def coordinate_id(self):
        return self.original.coordinate_id

    def stream_identity(self, stream):
        if stream not in self.streams:
            raise ValueError('response stream outside selected root')
        return ObjectIdentity.from_record('stream.' + self.root_id + '.' + stream.purpose_id, stream)


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/allocation'
    allocation_id: str
    original_allocation: MatrixParameterAllocation
    roots: tuple[MatrixParameterResponseRoot, ...]
    prior_effective_seeds: tuple[int, ...]
    initial_state_sha256s: tuple[tuple[str, str], ...]
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        original = self.original_allocation
        if (type(original) is not MatrixParameterAllocation or self.exposure != EXPOSED
                or tuple(r.original for r in self.roots) != tuple(r.root for r in original.roots)
                or tuple(r for r, _ in self.initial_state_sha256s) != tuple(r.root_id for r in self.roots)
                or self.prior_effective_seeds != tuple(sorted(set(self.prior_effective_seeds)))
                or any(type(s) is not int or not 0 <= s < 2**128 for s in self.prior_effective_seeds)):
            raise ValueError('response allocation thins original coordinate/root/group census')
        initial_groups = {}
        for root, (_, fingerprint) in zip(self.roots, self.initial_state_sha256s, strict=True):
            validate_sha256(fingerprint)
            if initial_groups.setdefault(root.independent_group_id, fingerprint) != fingerprint:
                raise ValueError('matched parameter group substitutes its authenticated initial state')
        excluded = {*self.prior_effective_seeds, *original.prior_effective_seeds,
                    *(s.effective_seed for r in original.roots for s in r.streams)}
        owners = {}
        for r in self.roots:
            for s in r.streams:
                if s.effective_seed in excluded:
                    raise ValueError('response allocation collides with consumed/exposed historical128bits')
                owner = r.independent_group_id, s.role
                if owners.setdefault(s.effective_seed, owner) != owner:
                    raise ValueError('response future streams collide across groups/purposes')

    def root(self, root_id):
        return next(r for r in self.roots if r.root_id == root_id)


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/design'
    design_id: str
    coordinate: MatrixParameterCoordinate
    rule: FactorEventSpec
    view: SixMatrixResponseNumericalView
    origin_tick: int
    actual_alpha_hex: tuple[str, str]
    actions: tuple[MatrixFactorAction, ...]
    horizon_steps: tuple[int, ...]
    receiver_count: int
    hessian_difference_step: Decimal
    potential_difference_step: Decimal
    generic_gap_minimum: Decimal
    spectral_gap_minimum: Decimal
    native_reference_tolerance: Decimal
    hessian_reference_tolerance: Decimal
    forecast_reference_tolerance: Decimal
    instrument_reference_tolerance: Decimal
    weak_response_minimum: Decimal
    model: ObjectIdentity
    evaluator: ObjectIdentity
    instrument: ObjectIdentity
    receiver: ObjectIdentity
    factor_sector: str
    ramp_boundary: str
    continuation: str = CONTINUATION

    def __post_init__(self):
        validate_stable_id(self.design_id)
        c, v = self.coordinate, self.view
        fields = ('integrator', 'timestep', 'time_unit', 'friction_gamma', 'bath_temperature', 'precision', 'checkpoint_interval_steps')
        require_sorted_unique_ids(self.actions, attribute='action_id', field_name='actions')
        if (type(c) is not MatrixParameterCoordinate or type(self.rule) is not FactorEventSpec
                or type(v) is not SixMatrixResponseNumericalView or v.view_id == c.primary_view.view_id
                or any(getattr(v, f) != getattr(c.primary_view, f) for f in fields)
                or v.rng_algorithm != 'PCG64' or v.rng_version != '1.0.0'
                or v.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN
                or v.precision is not MatrixPrecision.COMPLEX128
                or self.rule.primary_dt != v.timestep or self.factor_sector not in self.rule.sectors
                or self.origin_tick not in self.rule.lattice or self.origin_tick < self.rule.risk_start_tick
                or self.origin_tick > c.total_ticks or self.origin_tick < c.ramp_ticks
                or self.ramp_boundary not in ('AT_RAMP_END', 'STRICTLY_AFTER_RAMP')
                or self.ramp_boundary == 'STRICTLY_AFTER_RAMP' and self.origin_tick <= c.ramp_ticks
                or self.continuation != CONTINUATION
                or self.actual_alpha_hex != tuple(x.hex() for x in c.couplings(self.origin_tick))
                or tuple(sorted(a.role for a in self.actions)) != ACTION_ROLES
                or len({a.force_norm for a in self.actions}) != 1
                or self.receiver_count != 48 or type(self.receiver_count) is not int
                or not self.horizon_steps or self.horizon_steps != tuple(sorted(set(self.horizon_steps)))
                or any(type(h) is not int or h < 1 for h in self.horizon_steps)
                or any(a.pulse_steps > self.horizon_steps[-1] for a in self.actions)):
            raise ValueError('parameter response design substitutes actual view/clock/constant realization/task')
        for name in ('hessian_difference_step', 'potential_difference_step', 'native_reference_tolerance',
                     'hessian_reference_tolerance', 'forecast_reference_tolerance', 'instrument_reference_tolerance'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if getattr(self, name) == 0:
                raise ValueError('response numerical tolerance must be explicitly positive')
        for name in ('generic_gap_minimum', 'spectral_gap_minimum', 'weak_response_minimum'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for tick in range(self.origin_tick, c.total_ticks + 1):
            if tuple(x.hex() for x in c.couplings(tick)) != self.actual_alpha_hex:
                raise ValueError('selected response origin remains in a ramping schedule')
        size = 24 * ((3 * self.horizon_steps[-1] + 2) * 2 * 3 * 4 * 4 * 16
                     + (self.horizon_steps[-1] + 1) * 24)
        if size + 24 * 5 * 10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError('complete selected response requires an explicit chunked successor')

    @property
    def member(self):
        return self.coordinate.member

    @property
    def alpha_x(self):
        return Decimal.from_float(float.fromhex(self.actual_alpha_hex[0]))

    @property
    def alpha_y(self):
        return Decimal.from_float(float.fromhex(self.actual_alpha_hex[1]))

    @property
    def cutoff(self):
        return self.origin_tick * self.view.timestep

    @property
    def end_time(self):
        return self.cutoff + self.horizon_steps[-1] * self.view.timestep


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseCausalSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/causal-source'
    source_id: str
    root: MatrixProgrammeRoot
    design: MatrixParameterResponseDesign
    history_source: ObjectIdentity
    history_product: ObjectIdentity
    history_assessment: ObjectIdentity
    factor_source: ObjectIdentity
    factor_product: ObjectIdentity
    factor_assessment: ObjectIdentity
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if (type(self.root) is not MatrixProgrammeRoot or self.root.role is not MatrixProgrammeRole.DEVELOPMENT
                or type(self.design) is not MatrixParameterResponseDesign or self.exposure != EXPOSED
                or self.root.coordinate_id != self.design.coordinate.coordinate_id
                or self.root.clock_id != self.design.coordinate.clock_id
                or self.history_source.object_schema != MatrixParameterHistorySource.SCHEMA
                or self.factor_source.object_schema != MatrixParameterFactorSource.SCHEMA
                or self.factor_product.object_schema != MatrixParameterFactorProduct.SCHEMA
                or self.factor_assessment.object_schema != MatrixParameterFactorAssessment.SCHEMA):
            raise ValueError('causal response source changes actual development source/coordinate/clock')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/arrays'
    operand_id: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='array members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='array producers')
        if (not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz'
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('response arrays lose supported complete member/custody boundary')


def _receipt_output(receipts, record, artifact):
    matching = tuple(r for r in receipts if any(o.payload_schema == record.SCHEMA
        and o.content_sha256 == record.fingerprint() for o in r.output_logical_artifacts))
    if len(matching) != 1 or matching[0].operational_status is not OperationalStatus.SUCCEEDED:
        raise ValueError('response requires an actual successful ordinary supplier receipt')
    receipt = matching[0]
    if artifact is not None:
        logical = tuple(o for o in receipt.output_logical_artifacts if o.payload_schema == artifact.payload_schema
                        and o.content_sha256 == artifact.sha256)
        if len(logical) != 1 or not any(m.logical_artifact_id == logical[0].logical_artifact_id
                                      and m.size_bytes == artifact.size_bytes for m in receipt.output_materializations):
            raise ValueError('response supplier receipt omits exact supported raw publication')
    return receipt


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/source'
    source_id: str
    causal: MatrixParameterResponseCausalSource
    allocation: MatrixParameterResponseAllocation
    history_supply: ObjectIdentity
    history_arrays: ArtifactIdentity
    factor_arrays: ArtifactIdentity
    factor_receipts: tuple[CanonicalTaskReceipt, ...]
    instrument_arrays: MatrixParameterResponseArrays
    provenance: NumericalProducingProvenance
    historical_enclosing_return: str

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if (type(self.causal) is not MatrixParameterResponseCausalSource
                or type(self.allocation) is not MatrixParameterResponseAllocation
                or self.root.original != self.causal.root
                or self.history_supply.object_schema != MatrixParameterFactorSupply.SCHEMA
                or self.history_arrays.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.factor_arrays.payload_schema != MATRIX_ARRAY_SCHEMA
                or len(self.factor_receipts) != 2
                or self.historical_enclosing_return not in ('ABSENT_CONDITIONAL_DERIVED_HISTORY', 'REFUSED_CONDITIONAL_DERIVED_HISTORY', 'AUTHENTIC_ORIGINAL_ORDINARY_RETURN')
                or type(self.provenance) is not NumericalProducingProvenance):
            raise ValueError('response source substitutes original conditional custody/allocation/provenance')

    @property
    def root(self):
        return self.allocation.root(self.causal.root.root_id)

    @property
    def design(self):
        return self.causal.design

    def validate_operands(self, parameter, supply, factor_source, product, assessment):
        supply.validate_source(parameter)
        product_id, assessment_id = factor_identity(product), factor_identity(assessment)
        c = self.causal
        if (history_identity(parameter) != c.history_source or factor_identity(supply) != self.history_supply
                or history_identity(supply.product) != c.history_product
                or history_identity(supply.assessment) != c.history_assessment
                or parameter.allocation != self.allocation.original_allocation
                or parameter.root.root != self.root.original or parameter.coordinate != self.design.coordinate
                or factor_identity(factor_source) != c.factor_source
                or product_id != c.factor_product or assessment_id != c.factor_assessment
                or supply.state != 'COMPLETED' or supply.assessment.numerical_pass is not True
                or factor_source.parameter_source != c.history_source or factor_source.supply != self.history_supply
                or factor_source.rule != self.design.rule.identity or product.source != c.factor_source
                or product.root_id != self.root.root_id or product.independent_group_id != self.root.independent_group_id
                or product.coordinate != coordinate_identity(self.design.coordinate)
                or assessment.source != c.factor_source or assessment.product != product_id or not assessment.numerical_pass
                or supply.product.arrays.array_artifact != self.history_arrays or product.arrays.array_artifact != self.factor_arrays):
            raise ValueError('response substitutes actual independently assessed history/factor/root/coordinate operands')
        measured = _receipt_output(self.factor_receipts, product, self.factor_arrays)
        assessed = _receipt_output(self.factor_receipts, assessment, None)
        required = {m.materialization_id for m in measured.output_materializations}
        if not required <= set(assessed.input_materialization_ids):
            raise ValueError('response factor assessment is not joined to actual ordinary supplier outputs')
        if self.historical_enclosing_return == 'AUTHENTIC_ORIGINAL_ORDINARY_RETURN':
            raise ValueError('this conditional source edition has no original ordinary-history return operand')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseOriginSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/origin-selection'
    selection_id: str
    source: ObjectIdentity
    root_id: str
    independent_group_id: str
    coordinate: ObjectIdentity
    source_state: str
    disposition: str
    tick: int | None
    cutoff: Decimal | None
    frame_sha256: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        for value in (self.selection_id, self.root_id, self.independent_group_id):
            validate_stable_id(value)
        require_sorted_unique_strings(self.reason_codes, field_name='selection reasons', allow_empty=False)
        if (self.source.object_schema != MatrixParameterResponseCausalSource.SCHEMA
                or self.disposition not in ('SELECTED', 'NO_CAUSAL_ORIGIN', 'REFUSED', 'UNKNOWN', 'NOT_ENTERED')
                or (self.disposition == 'SELECTED') != (self.tick is not None and self.cutoff is not None and self.frame_sha256 is not None)):
            raise ValueError('response selection loses negative/unknown or selected origin boundary')
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseOrigin(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/origin'
    origin_id: str
    source: ObjectIdentity
    design: MatrixParameterResponseDesign
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: MatrixParameterResponseArrays
    frame_sha256: str
    selection: MatrixParameterResponseOriginSelection
    scientific_admission: str = 'UNASSESSED'

    def __post_init__(self):
        validate_stable_id(self.origin_id)
        validate_sha256(self.frame_sha256)
        if (self.source.object_schema != MatrixParameterResponseCausalSource.SCHEMA
                or self.selection.source != self.source or self.selection.disposition != 'SELECTED'
                or (self.root_id, self.independent_group_id) != (self.selection.root_id, self.selection.independent_group_id)
                or (self.design.origin_tick, self.design.cutoff, self.frame_sha256) != (self.selection.tick, self.selection.cutoff, self.selection.frame_sha256)
                or self.clock_id != self.design.coordinate.clock_id or self.scientific_admission != 'UNASSESSED'):
            raise ValueError('response origin changes public causal source/selection/frame/admission')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/forecast'
    forecast_id: str
    origin: ObjectIdentity
    model: ObjectIdentity
    cutoff: Decimal
    arrays: MatrixParameterResponseArrays
    dispositions: tuple[tuple[str, str, str | None], ...]

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        if (self.origin.object_schema != MatrixParameterResponseOrigin.SCHEMA
                or tuple(n for n, _, _ in self.dispositions) != PREDICTORS
                or any(s not in ('AVAILABLE', 'UNRESOLVED') or (reason is None) != (s == 'AVAILABLE')
                       for _, s, reason in self.dispositions)):
            raise ValueError('response forecast drops model or availability/uncertainty denominator')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseNativeEvent(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/native-event'
    branch_id: str
    definition: NativeSubworkDefinition
    begin: NativeSubworkBegin
    contact: NativeSubworkContact
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        validate_stable_id(self.branch_id)
        if (self.begin.definition != self.definition.identity or self.completion.definition != self.definition.identity
                or self.contact.begin != native_metadata_identity(self.definition, self.begin, 'begin')
                or self.completion.contact != native_metadata_identity(self.definition, self.contact, 'contact')
                or self.receipt.operational_status != self.completion.operational_status
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.consumed_streams != self.definition.streams
                or self.completion.omitted_output_ids or self.completion.output_ids != ('arrays',)):
            raise ValueError('response native event substitutes actual known completed child lineage')


@dataclass(frozen=True, slots=True)
class MatrixParameterNativeResponses(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/native-responses'
    response_id: str
    source: ObjectIdentity
    origin: ObjectIdentity
    forecast: ObjectIdentity
    branch_ids: tuple[str, ...]
    arrays: MatrixParameterResponseArrays
    events: tuple[MatrixParameterResponseNativeEvent, ...]

    def __post_init__(self):
        validate_stable_id(self.response_id)
        if (self.source.object_schema != MatrixParameterResponseSource.SCHEMA
                or self.origin.object_schema != MatrixParameterResponseOrigin.SCHEMA
                or self.forecast.object_schema != MatrixParameterResponseForecast.SCHEMA
                or len(self.branch_ids) != 2 * 4 * len(SIGNS) or self.branch_ids != tuple(sorted(set(self.branch_ids)))
                or tuple(e.branch_id for e in self.events) != self.branch_ids):
            raise ValueError('response native product drops complete24 known child/source/commitment census')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/control'
    control_id: str
    source: ObjectIdentity
    branch_id: str | None
    error: Decimal | None
    tolerance: Decimal
    method: str
    disposition: str
    denominator_steps: int
    denominator_real_coordinates: int
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self):
        if self.error is not None:
            validate_decimal(self.error, field_name='control residual', minimum=Decimal(0))
        validate_decimal(self.tolerance, field_name='control tolerance', minimum=Decimal(0))
        if (self.source.object_schema != MatrixParameterResponseSource.SCHEMA
                or self.error is not None and self.disposition != ('SATISFIED' if self.error <= self.tolerance else 'VIOLATED')
                or self.error is None and (self.disposition not in ('UNASSESSED', 'NOT_APPLICABLE') or not self.reason_codes)
                or type(self.denominator_steps) is not int or self.denominator_steps < 1
                or type(self.denominator_real_coordinates) is not int or self.denominator_real_coordinates < 1):
            raise ValueError('response control hides numerical failure or full step/coordinate denominator')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/assessment'
    assessment_id: str
    source: ObjectIdentity
    origin: ObjectIdentity
    forecast: ObjectIdentity
    native: ObjectIdentity
    scores: tuple[MatrixFactorResponseScore, ...]
    controls: tuple[MatrixParameterResponseControl, ...]
    native_reference_pass: bool
    requested_original_roots: int = 1
    requested_panels: int = 2
    requested_actions: int = 4
    requested_signs: int = 3
    requested_predictors: int = 5
    numerical_convergence: str = 'UNASSESSED'
    noise_scope: str = 'CONDITIONAL_AUTHENTICATED_PANEL_NOISE'
    inference: str = 'FINITE_DT_EXPOSED_NO_QUALIFICATION_OR_USE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != MatrixParameterResponseSource.SCHEMA
                or (self.requested_original_roots, self.requested_panels, self.requested_actions,
                    self.requested_signs, self.requested_predictors) != (1, 2, 4, 3, 5)
                or len({c.control_id for c in self.controls}) != len(self.controls)
                or len(tuple(c for c in self.controls if c.branch_id is not None)) != 24
                or any(c.source != self.source for c in self.controls)
                or self.native_reference_pass != all(c.disposition == 'SATISFIED' for c in self.controls)
                or self.numerical_convergence != 'UNASSESSED'
                or self.noise_scope not in ('CONDITIONAL_AUTHENTICATED_PANEL_NOISE', 'REGENERATED_SELECTED_PCG64_STREAMS')
                or self.inference != 'FINITE_DT_EXPOSED_NO_QUALIFICATION_OR_USE_ADMISSION'):
            raise ValueError('response assessment changes complete native controls or invents qualification')
