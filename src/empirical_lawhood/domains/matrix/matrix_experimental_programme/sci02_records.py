# SPDX-License-Identifier: MPL-2.0
"""SCI02 successor contracts, distinct from the unchanged E3--E6 protocols."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.matrix.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.domains.matrix.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.domains.matrix.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history_segments import ParameterGeneratorState
from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkCompletion, require_native_completion_receipt

from empirical_lawhood.domains.matrix.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.domains.matrix.matrix_experimental_programme.preparation_records import MatrixCouplingRecipe, exact_decimal, original_schedule_recipe

PROTOCOL_ID = 'matrix.preparation-shortcut.h64'
NAMESPACE = 'matrix-sci02'
RECIPES = ('ORIGINAL', 'EARLY', 'DELAYED')
METHODS = ('FACTOR', 'FULL', 'FULL_REFRESH32', 'INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32')
POLICY_METHODS = ('INPUT_KRYLOV48', 'INPUT_KRYLOV48_REFRESH32')
NATIVE_PHASES = ('prefix', 'completion', 'response-prefix', 'response-suffix')
PHASES = (*NATIVE_PHASES, 'source-state', 'shadow', 'handoff', 'origin', 'observation', 'refresh', 'assess', 'reduce')
SCOPE = 'MATRIX_PREPARATION_STUDY_NO_MOLECULAR_ADMISSION_OR_QUALIFICATION'


def pin(record):
    for key in ('record_id', 'config_id', 'specification_id'):
        if hasattr(record, key):
            return ObjectIdentity.from_record(getattr(record, key), record)
    raise TypeError('SCI02 requires its named canonical record')


@dataclass(frozen=True, slots=True)
class Sci02Design(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/design'
    record_id: str
    inherited_design: ObjectIdentity
    coordinate: MatrixParameterCoordinate
    assay: MatrixPreparedAssayMethod
    factor_rule: E1FactorRule
    molecular_requirement: str
    protocol_document_sha256: str
    scope: str = SCOPE
    source_tick: int = 64
    handoff_tick: int = 256
    refresh_tick: int = 32
    response_horizon: int = 64
    checks: tuple[int, ...] = tuple(range(16, 65))
    error_tolerance: Decimal = Decimal('.01')
    view_tolerance: Decimal = Decimal('.0001')
    signal_minimum: Decimal = Decimal('.10')
    reconstruction_tolerance: Decimal = Decimal('1e-10')
    basis_rule: str = 'INHERITED_INPUT_KRYLOV48_H128_WHITENING_AND_128_256_CONSTRUCTION'
    chart_rule: str = 'PRIMARY_Y_SOURCE64_CHART_DISTINCT_FROM_INSTANT_FACTOR_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.protocol_document_sha256)
        if (type(self.inherited_design) is not ObjectIdentity or type(self.coordinate) is not MatrixParameterCoordinate
                or type(self.assay) is not MatrixPreparedAssayMethod or type(self.factor_rule) is not E1FactorRule
                or not self.molecular_requirement or self.scope != SCOPE):
            raise ValueError('SCI02 requires exact inherited physics, instrument, factor rule and named molecular requirement')
        for value in (self.inherited_design, self.coordinate, self.assay, self.factor_rule):
            value.__post_init__()
        c = self.coordinate
        if (c.q != 2 or c.family_id != 'matrix-history.joint-decreasing-coupling'
                or c.ramp_ticks != 256 or c.total_ticks < 320 or c.decreasing_start != 8
                or c.member.mass_x != Decimal('.5') or c.member.mass_y != Decimal('.5')
                or c.member.cross_coupling_gamma != 1 or c.primary_view.bath_temperature != 1
                or c.primary_view.friction_gamma != 1 or c.primary_view.timestep != Decimal('.001')
                or c.fine_view.timestep != Decimal('.0005')
                or any((a.amplitude, a.force_norm, a.pulse_steps) != (Decimal('.01'), Decimal(1), 16) for a in self.assay.actions)
                or (self.source_tick, self.handoff_tick, self.refresh_tick, self.response_horizon) != (64, 256, 32, 64)
                or self.checks != tuple(range(16, 65))
                or (self.error_tolerance, self.view_tolerance, self.signal_minimum, self.reconstruction_tolerance)
                    != (Decimal('.01'), Decimal('.0001'), Decimal('.10'), Decimal('1e-10'))
                or self.basis_rule != 'INHERITED_INPUT_KRYLOV48_H128_WHITENING_AND_128_256_CONSTRUCTION'
                or self.chart_rule != 'PRIMARY_Y_SOURCE64_CHART_DISTINCT_FROM_INSTANT_FACTOR_ADMISSION'):
            raise ValueError('SCI02 changes its selected nominal physics, clocks, instrument, thresholds or inherited basis')

    @property
    def identity(self): return pin(self)

    def recipe(self, name):
        """Derive the exact half-tick continuation, preserving ORIGINAL bytes."""
        if name not in RECIPES:
            raise ValueError('SCI02 recipe is outside its three fixed completions')
        original = original_schedule_recipe(self.coordinate, 256,
            recipe_id='recipe.sci02.original.' + self.fingerprint(), effort_unit='coupling-total-variation')
        if name == 'ORIGINAL': return original
        start, target = original.half_tick_couplings[128], original.half_tick_couplings[-1]
        from fractions import Fraction
        values = list(original.half_tick_couplings[:129])
        for half_tick in range(129, 513):
            u = Fraction(half_tick - 128, 384)
            weight = min(2 * u, 1) if name == 'EARLY' else max(2 * u - 1, 0)
            values.append(tuple(exact_decimal(Fraction(a) + (Fraction(b) - Fraction(a)) * weight)
                for a, b in zip(start, target, strict=True)))
        return MatrixCouplingRecipe('recipe.sci02.' + name.lower() + '.' + self.fingerprint(), 'FIXED_COUPLING',
            256, tuple(values), 'HALF_TICK_COUPLING_TOTAL_VARIATION_L1', 'coupling-total-variation')


@dataclass(frozen=True, slots=True)
class Sci02Selection(CanonicalRecord):
    """Committed stream allocation; never passed to a predictor port."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/selection'
    record_id: str
    design: Sci02Design
    streams: SelectedE4StreamRecipe
    exposure_census: ObjectIdentity
    reserved_development_roots: int = 16
    reserved_holdout_roots: int = 32

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.design) is not Sci02Design or type(self.streams) is not SelectedE4StreamRecipe
                or type(self.exposure_census) is not ObjectIdentity
                or (self.reserved_development_roots, self.reserved_holdout_roots) != (16, 32)):
            raise ValueError('SCI02 allocation changes the fixed DEV16/held32 whole-root cap')
        self.design.__post_init__(); self.streams.__post_init__(); self.exposure_census.__post_init__()

    @property
    def identity(self): return pin(self)

    def root(self, bank, ordinal):
        if bank not in ('DEV', 'HOLDOUT') or type(ordinal) is not int or not 0 <= ordinal < (16 if bank == 'DEV' else 32):
            raise ValueError('SCI02 root is outside its original finite allocation')
        group = f'sci02.{self.fingerprint()}.{bank.lower()}.{ordinal:02d}'
        rows = tuple((panel, self.streams.streams(group, future=bool(panel))) for panel in (0, 1))
        pins = tuple((panel, tuple(ObjectIdentity.from_record(f'stream.{group}.p{panel}.{v.purpose}', v)
            for v in values)) for panel, values in rows)
        return Sci02Root('root.' + group, self.identity, group, bank, ordinal, pins)


@dataclass(frozen=True, slots=True)
class Sci02Root(CanonicalRecord):
    """Public root identity exposes stream pins, never future stream values."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/root'
    record_id: str
    selection: ObjectIdentity
    group_id: str
    bank: str
    ordinal: int
    streams: tuple[tuple[int, tuple[ObjectIdentity, ...]], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id); validate_stable_id(self.group_id)
        if (type(self.selection) is not ObjectIdentity or self.selection.object_schema != Sci02Selection.SCHEMA
                or self.bank not in ('DEV', 'HOLDOUT') or type(self.ordinal) is not int
                or not 0 <= self.ordinal < (16 if self.bank == 'DEV' else 32)
                or tuple(p for p, _ in self.streams) != (0, 1)
                or any(len(values) != 4 or any(v.object_schema != MatrixHistorySeed.SCHEMA for v in values) for _, values in self.streams)
                or self.group_id != f'sci02.{self.selection.object_fingerprint}.{self.bank.lower()}.{self.ordinal:02d}'
                or self.record_id != 'root.' + self.group_id):
            raise ValueError('SCI02 root changes its bank, independent unit or exact stream scope')
        for panel, values in self.streams:
            for purpose, value in zip(HISTORY_PURPOSES, values, strict=True):
                value.__post_init__()
                if value.object_id != f'stream.{self.group_id}.p{panel}.{purpose}':
                    raise ValueError('SCI02 stream pin changes its original purpose or panel')

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02Config(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/operation-config'
    config_id: str
    design: Sci02Design
    root: Sci02Root
    phase: str
    recipe: str
    provenance: ObjectIdentity

    def __post_init__(self):
        if (type(self.design) is not Sci02Design or type(self.root) is not Sci02Root or self.phase not in PHASES
                or self.recipe not in (*RECIPES, 'COMMON')
                or self.recipe == 'COMMON' and self.phase not in ('prefix', 'source-state', 'shadow', 'reduce')
                or self.phase in ('prefix', 'source-state', 'shadow', 'reduce') and self.recipe != 'COMMON'
                or type(self.provenance) is not ObjectIdentity or self.provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or self.config_id != 'config.' + self.node_id):
            raise ValueError('SCI02 operation changes its exact source, phase or recipe')
        self.design.__post_init__(); self.root.__post_init__(); self.provenance.__post_init__()

    @property
    def node_id(self):
        return f'{NAMESPACE}.{self.root.group_id}.{self.recipe.lower()}.{self.phase}'

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02Arrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/arrays'
    record_id: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        a = self.array_artifact
        if (type(a) is not ArtifactIdentity or a.payload_schema != MATRIX_ARRAY_SCHEMA or a.media_type != 'application/x-npz'
                or not 0 < a.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES or not 1 <= len(self.members) <= 256
                or tuple(v.name for v in self.members) != tuple(sorted({v.name for v in self.members}))
                or any(type(v) is not MatrixArrayMember or not v.finite_required for v in self.members)
                or sum(v.size_bytes for v in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('SCI02 arrays lose their bounded complete finite member contract')
        a.__post_init__()
        for value in self.members: value.__post_init__()

    @property
    def outcome_access(self):
        from empirical_lawhood.science.evidence.evidence import OutcomeAccess
        return OutcomeAccess.DEVELOPMENT_VISIBLE

    @property
    def visibility_ceiling(self):
        from empirical_lawhood.science.evidence.evidence import VisibilityCeiling
        return VisibilityCeiling.DEVELOPMENT_ONLY


@dataclass(frozen=True, slots=True)
class Sci02NativeHistory(CanonicalRecord):
    """Two original child outputs; the historical one-output contract stays fixed."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/native-history'
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        require_native_completion_receipt(self.completion, self.receipt)
        if (self.completion.definition != self.definition.identity
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.output_ids != ('arrays', 'checkpoint') or self.completion.omitted_output_ids
                or self.completion.consumed_streams != self.definition.streams
                or self.completion.unconsumed_streams or self.completion.unknown_streams
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids) <= set(self.receipt.input_materialization_ids)):
            raise ValueError('SCI02 requires a known original native completion and both receipted outputs')


@dataclass(frozen=True, slots=True)
class Sci02Product(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/product'
    record_id: str
    config: Sci02Config
    predecessors: tuple[ObjectIdentity, ...]
    arrays: Sci02Arrays
    disposition: str
    reasons: tuple[str, ...]
    generators: tuple[tuple[int, ParameterGeneratorState], ...] = ()
    native: tuple[Sci02NativeHistory, ...] = ()
    measurements: tuple[tuple[str, Decimal | None], ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.config) is not Sci02Config or type(self.arrays) is not Sci02Arrays
                or self.disposition not in ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE')
                or self.reasons != tuple(sorted(set(self.reasons)))
                or self.disposition == 'UNAVAILABLE' and not self.reasons
                or self.record_id != 'product.' + self.config.node_id
                or tuple(v.object_id for v in self.predecessors) != tuple(sorted({v.object_id for v in self.predecessors}))
                or len(self.native) > 1 or self.config.phase not in NATIVE_PHASES and (self.native or self.generators)
                or tuple(k for k, _ in self.measurements) != tuple(sorted({k for k, _ in self.measurements}))):
            raise ValueError('SCI02 product changes its exact source, custody or measured census')
        self.config.__post_init__(); self.arrays.__post_init__()
        for predecessor in self.predecessors:
            if type(predecessor) is not ObjectIdentity or predecessor.object_schema != self.SCHEMA:
                raise TypeError('SCI02 product requires exact original predecessor products')
            predecessor.__post_init__()
        for event in self.native:
            if type(event) is not Sci02NativeHistory:
                raise TypeError('SCI02 continuation requires its two-output native history owner')
            event.__post_init__()
        if self.config.phase in NATIVE_PHASES:
            if self.disposition == 'AVAILABLE':
                count = {'prefix': 64, 'completion': 256, 'response-prefix': 32, 'response-suffix': 64}[self.config.phase]
                purpose = 'preparation' if self.config.phase in ('prefix', 'completion') else 'autonomous'
                panels = (0,) if purpose == 'preparation' else (0, 1)
                expected = tuple((p, purpose + '-' + s) for p in panels for s in ('coarse-driver', 'fine-bridge'))
                if (len(self.native) != 1 or tuple((p, s.purpose) for p, s in self.generators) != expected
                        or any(s.completed_noise_matrices != count for _, s in self.generators)):
                    raise ValueError('SCI02 successful native product loses its original exact continuation census')
            elif self.native or self.generators:
                raise ValueError('SCI02 nonentry cannot invent a consumed native checkpoint')
        for _, value in self.measurements:
            if value is not None: validate_decimal(value, field_name='SCI02 retained measurement')
        for panel, state in self.generators:
            if panel not in (0, 1) or type(state) is not ParameterGeneratorState:
                raise ValueError('SCI02 generator continuation changes its panel or original typed cursor')
            state.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02NativeCheckpoint(CanonicalRecord):
    """Receipt-retained continuation metadata, published with native arrays."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/native-checkpoint'
    record_id: str
    config: ObjectIdentity
    arrays: Sci02Arrays
    generators: tuple[tuple[int, ParameterGeneratorState], ...]
    measurements: tuple[tuple[str, Decimal | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.config) is not ObjectIdentity or self.config.object_schema != Sci02Config.SCHEMA
                or type(self.arrays) is not Sci02Arrays or not self.generators
                or tuple((p, s.purpose) for p, s in self.generators) != tuple(sorted({(p, s.purpose) for p, s in self.generators}))):
            raise ValueError('SCI02 checkpoint changes its exact native config or generator census')
        self.config.__post_init__(); self.arrays.__post_init__()
        for p, state in self.generators:
            if p not in (0, 1) or type(state) is not ParameterGeneratorState:
                raise TypeError('SCI02 checkpoint changes its actual stream continuation owner')
            state.__post_init__()
        for _, value in self.measurements:
            if value is not None: validate_decimal(value, field_name='SCI02 actual native measurement')
