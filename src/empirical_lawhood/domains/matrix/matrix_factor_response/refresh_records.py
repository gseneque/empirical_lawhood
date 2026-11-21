# SPDX-License-Identifier: MPL-2.0
"""Separately identified SCI01 retained comparison; no native entry authority."""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from typing import ClassVar

from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id

from empirical_lawhood.domains.matrix.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS

REFRESH_METHODS = ('FULL', 'FULL_REFRESH32', 'INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32', 'FACTOR')
REFRESH_PROTOCOL_ID = 'matrix.sci01.retained-refresh32.v1'


@dataclass(frozen=True, slots=True)
class MatrixRefreshRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/refresh-rule'
    VERSION: ClassVar[str] = '1.0.0'
    methods: tuple[str, ...] = REFRESH_METHODS
    checkpoint_primary_tick: int = 32
    primary_horizon: int = 64
    secondary_horizon: int = 128
    actuator_error_tolerance: Decimal = Decimal('.01')
    paired_view_tolerance: Decimal = Decimal('.0001')
    reconstruction_tolerance: Decimal = Decimal('1e-10')
    information_rule: str = 'PANEL_HOLD32_AFTER_COMPLETED_STEP_FIXED_BASIS_INSTRUMENT_OWN_STATE_NO_RESET'
    scoring_rule: str = 'ORIGIN_CUMULATIVE_ORIGINAL_29_CHECKS_ALL_ACTIONS_PANELS_HS24_BLOCKS'
    finite_pair_rule: str = 'EXACT_TRACE_GENERIC_FORCES_NOMINAL_GROUP_RECEIVER_RAW_NATIVE_PHASE_ENDPOINTS'
    weak_channel_rule: str = 'RETAIN_SIGNALS_ERRORS_AND_CANCELLATION_NO_MOLECULAR_TOLERANCE_TRANSFER'
    cost_rule: str = 'CHARGE_OBSERVATION_OPERATOR_AND_UNAVAILABLE_BASELINE_PREFIX_INCLUDING_CACHED_INFORMATION'
    stopping_rule: str = 'COMPLETE_RETAINED_COMPARISON_RETURN_SCOPED_METHOD_REQUIREMENTS_NO_NEW_ACQUISITION_OR_FITS'

    def __post_init__(self):
        exact = {
            'methods': REFRESH_METHODS, 'checkpoint_primary_tick': 32,
            'primary_horizon': 64, 'secondary_horizon': 128,
            'actuator_error_tolerance': Decimal('.01'), 'paired_view_tolerance': Decimal('.0001'),
            'reconstruction_tolerance': Decimal('1e-10'),
            'information_rule': 'PANEL_HOLD32_AFTER_COMPLETED_STEP_FIXED_BASIS_INSTRUMENT_OWN_STATE_NO_RESET',
            'scoring_rule': 'ORIGIN_CUMULATIVE_ORIGINAL_29_CHECKS_ALL_ACTIONS_PANELS_HS24_BLOCKS',
            'finite_pair_rule': 'EXACT_TRACE_GENERIC_FORCES_NOMINAL_GROUP_RECEIVER_RAW_NATIVE_PHASE_ENDPOINTS',
            'weak_channel_rule': 'RETAIN_SIGNALS_ERRORS_AND_CANCELLATION_NO_MOLECULAR_TOLERANCE_TRANSFER',
            'cost_rule': 'CHARGE_OBSERVATION_OPERATOR_AND_UNAVAILABLE_BASELINE_PREFIX_INCLUDING_CACHED_INFORMATION',
            'stopping_rule': 'COMPLETE_RETAINED_COMPARISON_RETURN_SCOPED_METHOD_REQUIREMENTS_NO_NEW_ACQUISITION_OR_FITS',
        }
        if any(type(getattr(self, key)) is not type(value) or getattr(self, key) != value
               for key, value in exact.items()):
            raise ValueError('SCI01 changes its fixed causal continuation, criteria or stopping rule')


REFRESH_RULE = MatrixRefreshRule()


@dataclass(frozen=True, slots=True)
class MatrixRefreshCaseSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/original-case'
    VERSION: ClassVar[str] = '1.0.0'
    case_index: int
    root_id: str
    group_id: str
    source: ObjectIdentity
    response_protocol: ObjectIdentity
    causal_prefix: ObjectIdentity
    physical_forecast: ObjectIdentity
    native_response: ObjectIdentity
    score: ObjectIdentity
    original_availability: str
    numerical_usable: bool
    temperature_friction_coupling: tuple[Decimal, ...]
    panel_ids: tuple[str, ...]

    def __post_init__(self):
        for name in ('root_id', 'group_id'):
            validate_stable_id(getattr(self, name))
        if (type(self.case_index) is not int or not 0 <= self.case_index < 144
                or self.original_availability not in ('FINITE', 'NO_ORIGIN')
                or type(self.numerical_usable) is not bool
                or self.numerical_usable != (self.original_availability == 'FINITE')
                or type(self.temperature_friction_coupling) is not tuple
                or len(self.temperature_friction_coupling) != 3
                or type(self.panel_ids) is not tuple or len(self.panel_ids) != 2
                or self.panel_ids != tuple(sorted(set(self.panel_ids)))):
            raise ValueError('SCI01 original case changes its retained availability, coordinate or panels')
        for value in self.temperature_friction_coupling:
            validate_decimal(value, field_name='SCI01 physical coordinate', minimum=Decimal(0))
        for value in self.panel_ids:
            validate_stable_id(value)
        for name in ('source', 'response_protocol', 'causal_prefix', 'physical_forecast', 'native_response', 'score'):
            if type(getattr(self, name)) is not ObjectIdentity:
                raise TypeError('SCI01 requires exact original scientific identities')


@dataclass(frozen=True, slots=True)
class MatrixRefreshProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/retained-protocol'
    VERSION: ClassVar[str] = '1.0.0'
    original_programme: ObjectIdentity
    original_execution_plan: ObjectIdentity
    original_entry_evidence: ObjectIdentity
    original_run_id: str
    cases: tuple[MatrixRefreshCaseSource, ...]
    public_specification_sha256: str
    rule: MatrixRefreshRule = REFRESH_RULE
    protocol_id: str = REFRESH_PROTOCOL_ID
    evidence_role: str = 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'

    def __post_init__(self):
        validate_stable_id(self.original_run_id)
        validate_sha256(self.public_specification_sha256)
        finite = tuple(row for row in self.cases if row.original_availability == 'FINITE')
        if (self.protocol_id != REFRESH_PROTOCOL_ID or self.rule != REFRESH_RULE
                or type(self.rule) is not MatrixRefreshRule
                or self.evidence_role != 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'
                or type(self.cases) is not tuple or any(type(row) is not MatrixRefreshCaseSource for row in self.cases)
                or tuple(row.case_index for row in self.cases) != tuple(range(144))
                or len({row.root_id for row in self.cases}) != 144
                or sorted(Counter(row.group_id for row in self.cases).values()) != [9] * 16
                or len(finite) != 36 or sorted(Counter(row.group_id for row in finite).values()) != [9] * 4):
            raise ValueError('SCI01 requires the original 144/36/108 cases and four usable independent groups')
        for value in (self.original_programme, self.original_execution_plan, self.original_entry_evidence):
            if type(value) is not ObjectIdentity:
                raise TypeError('SCI01 requires its actual original programme, plan and entry evidence')
        coordinates = set(product((Decimal('.5'), Decimal(2)), repeat=3)) | {(Decimal(1),) * 3}
        if any({row.temperature_friction_coupling for row in self.cases if row.group_id == group} != coordinates
               for group in {row.group_id for row in self.cases}):
            raise ValueError('SCI01 changes its original nested corners and nominal receiver case')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)


@dataclass(frozen=True, slots=True)
class MatrixRefreshArrays(CanonicalRecord):
    """The existing bounded array transport with a SCI01 source/case binding."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/retained-arrays'
    VERSION: ClassVar[str] = '1.0.0'
    operand_id: str
    protocol: ObjectIdentity
    original_case: MatrixRefreshCaseSource
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        if (type(self.protocol) is not ObjectIdentity or self.protocol.object_schema != MatrixRefreshProtocol.SCHEMA
                or type(self.original_case) is not MatrixRefreshCaseSource
                or self.original_case.original_availability != 'FINITE'
                or tuple(row.name for row in self.members) != refresh_array_names()
                or any(type(row) is not MatrixArrayMember or not row.finite_required for row in self.members)
                or sum(row.size_bytes for row in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz'
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('SCI01 changes its exact complete finite array or original-case contract')


@dataclass(frozen=True, slots=True)
class MatrixRefreshMethodAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/method-assessment'
    VERSION: ClassVar[str] = '1.0.0'
    method: str
    primary_curve: tuple[Decimal, ...]
    fine_curve: tuple[Decimal, ...]
    original_numerical_usable: bool

    def __post_init__(self):
        if (self.method not in REFRESH_METHODS or type(self.original_numerical_usable) is not bool
                or any(type(curve) is not tuple or len(curve) != len(DENSE_RESPONSE_HORIZONS)
                       for curve in (self.primary_curve, self.fine_curve))):
            raise ValueError('SCI01 assessment requires both complete origin-cumulative curves')
        for curve in (self.primary_curve, self.fine_curve):
            for value in curve:
                validate_decimal(value, field_name='SCI01 cumulative error', minimum=Decimal(0))
            if tuple(sorted(curve)) != curve:
                raise ValueError('SCI01 cannot erase accumulated response error after refresh')

    def paired_discrepancy(self, horizon):
        stop = DENSE_RESPONSE_HORIZONS.index(horizon) + 1
        return max(abs(left - right) for left, right in zip(
            self.primary_curve[:stop], self.fine_curve[:stop], strict=True))

    def adequate(self, horizon):
        if not self.original_numerical_usable or self.paired_discrepancy(horizon) > REFRESH_RULE.paired_view_tolerance:
            return None
        index = DENSE_RESPONSE_HORIZONS.index(horizon)
        return max(self.primary_curve[index], self.fine_curve[index]) <= REFRESH_RULE.actuator_error_tolerance


@dataclass(frozen=True, slots=True)
class MatrixRefreshCaseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/case-assessment'
    VERSION: ClassVar[str] = '1.0.0'
    original_case: MatrixRefreshCaseSource
    methods: tuple[MatrixRefreshMethodAssessment, ...]
    construction_failure: str | None = None

    def __post_init__(self):
        expected = () if self.original_case.original_availability == 'NO_ORIGIN' or self.construction_failure else REFRESH_METHODS
        if (tuple(value.method for value in self.methods) != expected
                or any(type(value) is not MatrixRefreshMethodAssessment for value in self.methods)
                or self.original_case.original_availability == 'NO_ORIGIN' and self.construction_failure is not None
                or self.construction_failure is not None and not self.construction_failure):
            raise ValueError('SCI01 decision drops a method or changes an original missing case')

    @property
    def decision(self):
        if self.original_case.original_availability == 'NO_ORIGIN':
            return 'NO_ORIGIN'
        if self.construction_failure:
            return 'CONSTRUCTION_UNAVAILABLE'
        m = {row.method: row.adequate(64) for row in self.methods}
        if m['FULL'] and m['INPUT_KRYLOV48']:
            return 'FROZEN_RESPONSE'
        if any(m[name] is None for name in ('FULL_REFRESH32', 'INPUT_KRYLOV48_REFRESH32')):
            return 'NUMERICALLY_UNEVALUABLE'
        if m['FULL_REFRESH32'] and m['INPUT_KRYLOV48_REFRESH32']:
            return 'ONE_REFRESH'
        if m['FULL_REFRESH32']:
            return 'INADEQUATE_RETENTION'
        if m['INPUT_KRYLOV48_REFRESH32']:
            return 'CANCELLATION_REQUIRES_ASSESSMENT'
        return 'REFERENCE_CALCULATION'


@dataclass(frozen=True, slots=True)
class MatrixRefreshDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci01/independent-decision'
    VERSION: ClassVar[str] = '1.0.0'
    decision_id: str
    protocol: MatrixRefreshProtocol
    calculation_completion: ObjectIdentity
    cases: tuple[MatrixRefreshCaseAssessment, ...]
    molecular_admission: str = 'NONE_MATRIX_DEVELOPMENT_ONLY'
    acquisition_authority: str = 'NONE_SCI02_AND_RUB03_REQUIRE_SEPARATE_SELECTION'

    def __post_init__(self):
        validate_stable_id(self.decision_id)
        if (type(self.protocol) is not MatrixRefreshProtocol
                or tuple(row.original_case for row in self.cases) != self.protocol.cases
                or any(type(row) is not MatrixRefreshCaseAssessment for row in self.cases)
                or self.calculation_completion.object_schema != 'empirical-lawhood/runtime/retained-analysis-completion'
                or self.molecular_admission != 'NONE_MATRIX_DEVELOPMENT_ONLY'
                or self.acquisition_authority != 'NONE_SCI02_AND_RUB03_REQUIRE_SEPARATE_SELECTION'):
            raise ValueError('SCI01 independent decision changes census, custody or molecular authority')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.decision_id, self)

    @property
    def decision_counts(self):
        return tuple(sorted(Counter(row.decision for row in self.cases).items()))


def refresh_array_names():
    names = {'forces', 'receivers', 'scales'}
    for view in ('primary', 'fine'):
        names.update((view + '.h0', view + '.state_ticks'))
        for method in ('FULL', 'INPUT_KRYLOV48', 'FACTOR'):
            names.update(view + '.' + kind + '.' + method for kind in ('basis', 'state', 'prediction'))
        for pi in range(2):
            prefix = f'{view}.p{pi}'
            names.update(prefix + '.' + kind for kind in ('checkpoint.position', 'checkpoint.alpha', 'h32',
                'native', 'native.phase.endpoints', 'hold', 'signal'))
            for method in ('FULL_REFRESH32', 'INPUT_KRYLOV48_REFRESH32'):
                names.update(prefix + '.' + kind + '.' + method for kind in ('state', 'prediction'))
            for method in REFRESH_METHODS:
                names.update(prefix + '.' + kind + '.' + method for kind in ('error', 'error_norm'))
            for method in ('FACTOR', 'INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32'):
                names.update(prefix + '.' + kind + '.' + method for kind in ('signed', 'squares', 'cross'))
    return tuple(sorted(name.lower() for name in names))


def refresh_columns():
    """Public meanings for every retained array axis and signed convention."""
    return {
        'methods': REFRESH_METHODS,
        'array_method_suffixes': 'Lowercase method labels, as required by the shared array contract',
        'views': ('primary', 'fine'), 'panels': 'Original sorted panel IDs, p0 and p1',
        'actions': 'Original response-protocol action order; never label-based instrument matching',
        'state_axes': ('action', 'origin_checkpoint32_H64_H128_at_each_native_clock', 'q_then_p_in_fixed_basis'),
        'response_axes': ('action', 'primary_tick_1_to_128', 'original_q24_then_p24_receiver'),
        'signed_axes': ('native_minus_hold_hold_minus_full_full_minus_model', 'action',
                        'primary_tick_1_to_128', 'q_p', 'receiver_component_0_to_23'),
        'cross_axes': ('twice_dot_01_02_12', 'action', 'primary_tick_1_to_128', 'q_p'),
        'full_intermediate': 'FULL_REFRESH32 for INPUT_KRYLOV48_REFRESH32; FULL otherwise',
        'scales': 'Original nominal actuator q/p scales at each physical tick; basis whitening stays at H128',
        'endpoint_phase_axes': ('action', 'H64_H128', 'native_q96_then_p96'),
        'checkpoint': 'HOLD observation after native step 32 or 64; first changed model step is 33 or 65',
        'signed_error': 'native minus estimate, without division by pulse amplitude',
        'native_acquisition': 0, 'statistical_fits': 0,
    }
