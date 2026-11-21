# SPDX-License-Identifier: MPL-2.0
"""Separate SCI02-B records preserve original SCI02 identities and reservations."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history_segments import ParameterGeneratorState
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays, Sci02Design, Sci02NativeHistory, Sci02Root, Sci02Selection, pin

PROTOCOL_ID = 'matrix.paired-description-reuse.h64'
NAMESPACE = 'matrix-sci02b'
NATIVE_PHASES = ('prefix', 'completion', 'baseline', 'reference')
ROOT_PHASES = (*NATIVE_PHASES, 'source-state', 'instrument', 'handoff', 'origin', 'observation', 'refresh', 'prediction', 'assess', 'reduce')
PHASES = (*ROOT_PHASES, 'diagnose', 'fit', 'calibrate', 'confirm')
COMMON = ('prefix', 'source-state', 'instrument', 'prediction', 'reduce', 'diagnose', 'fit', 'calibrate', 'confirm')
SCOPE = 'MATRIX_PAIRED_DESCRIPTION_REUSE_NONPROMOTABLE_NO_MOLECULAR_QUALIFICATION'


def decimals(values):
    for value in values:
        validate_decimal(value, field_name='SCI02-B exact numerical operand')


@dataclass(frozen=True, slots=True)
class Sci02BDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/design'
    record_id: str
    original_selection: ObjectIdentity
    physical: Sci02Design
    protocol_document_sha256: str
    candidate_dimensions: tuple[int, ...] = (24, 32)
    primary_pair: tuple[str, ...] = ('ORIGINAL', 'EARLY')
    scope: str = SCOPE
    representation_rule: str = 'PHYSICAL_HESSIAN_BLOCK_ARNOLDI_TWO_REORTHOGONALIZATIONS_FIXED_BASIS_UPDATE32'
    description_rule: str = 'BASE_QP_NORMS_STRUCTURE_PRIMARY_OPERATOR_DRIFT_AND_OMITTED_ACTION'
    ridge_penalty: Decimal = Decimal(1)
    calibration_rank: int = 8
    confirmation_count: int = 32
    paired_error_tolerance: Decimal = Decimal('.01')
    forecast_win_margin: Decimal = Decimal('.05')
    forecast_critical_wins: int = 22
    required_reduced_deliveries: int = 24
    finite_workloads: tuple[int, ...] = (32, 128, 1024)

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.protocol_document_sha256)
        if (type(self.original_selection) is not ObjectIdentity or self.original_selection.object_schema != Sci02Selection.SCHEMA
                or type(self.physical) is not Sci02Design or self.candidate_dimensions != (24, 32)
                or self.primary_pair != ('ORIGINAL', 'EARLY') or self.scope != SCOPE
                or self.representation_rule != 'PHYSICAL_HESSIAN_BLOCK_ARNOLDI_TWO_REORTHOGONALIZATIONS_FIXED_BASIS_UPDATE32'
                or self.description_rule != 'BASE_QP_NORMS_STRUCTURE_PRIMARY_OPERATOR_DRIFT_AND_OMITTED_ACTION'
                or self.ridge_penalty != 1 or self.calibration_rank != 8 or self.confirmation_count != 32
                or self.paired_error_tolerance != Decimal('.01') or self.forecast_win_margin != Decimal('.05')
                or self.forecast_critical_wins != 22 or self.required_reduced_deliveries != 24 or self.finite_workloads != (32, 128, 1024)):
            raise ValueError('SCI02-B changes its exact selected successor protocol')
        self.original_selection.__post_init__()
        self.physical.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02BRetainedCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/retained-case'
    record_id: str
    root: Sci02Root
    design: Sci02Design
    original_plan: ObjectIdentity
    original_products: tuple[ObjectIdentity, ...]
    original_receipts: tuple[ObjectIdentity, ...]
    arrays: Sci02Arrays
    original_read_sha256: str
    exposure: str = 'ORIGINAL_SCI02_DEV8_EXPOSED_NO_NEW_NATIVE_ACQUISITION'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.original_read_sha256)
        if (type(self.root) is not Sci02Root or self.root.bank != 'DEV' or not 0 <= self.root.ordinal < 8
                or type(self.design) is not Sci02Design or type(self.arrays) is not Sci02Arrays
                or not self.original_products or not self.original_receipts
                or self.exposure != 'ORIGINAL_SCI02_DEV8_EXPOSED_NO_NEW_NATIVE_ACQUISITION'):
            raise ValueError('SCI02-B retained case changes original development scope or custody')
        for values in (self.original_products, self.original_receipts):
            if tuple(v.object_id for v in values) != tuple(sorted({v.object_id for v in values})):
                raise ValueError('SCI02-B retained custody changes its exact source census')
            for value in values: value.__post_init__()
        for value in (self.root, self.design, self.original_plan, self.arrays): value.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02BFrozenDescription(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/frozen-description'
    record_id: str
    study: ObjectIdentity
    dimension: int
    training_roots: tuple[Sci02Root, ...]
    diagnosis_products: tuple[ObjectIdentity, ...]
    feature_mean: tuple[Decimal, ...]
    feature_scale: tuple[Decimal, ...]
    coefficients: tuple[tuple[Decimal, ...], ...]
    intercepts: tuple[Decimal, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.study.object_schema != Sci02BDesign.SCHEMA or self.dimension not in (24, 32)
                or len(self.training_roots) != 8 or tuple(r.ordinal for r in self.training_roots) != tuple(range(8))
                or any(r.bank != 'DEV' for r in self.training_roots) or len({r.selection for r in self.training_roots}) != 1
                or len(self.diagnosis_products) != 8 or len(self.feature_mean) != 4 or len(self.feature_scale) != 4
                or len(self.coefficients) != 3 or any(len(row) != 4 for row in self.coefficients)
                or len(self.intercepts) != 3 or any(value <= 0 for value in self.feature_scale)
                or any(self.coefficients[0]) or any(self.coefficients[1][2:])):
            raise ValueError('SCI02-B frozen account changes its actual eight-root fit or exact feature roles')
        self.study.__post_init__()
        for value in (*self.training_roots, *self.diagnosis_products): value.__post_init__()
        decimals((*self.feature_mean, *self.feature_scale, *self.intercepts, *(v for row in self.coefficients for v in row)))

    @property
    def identity(self): return pin(self)

    def numerical_arrays(self):
        import numpy as np
        return {key: np.asarray(getattr(self, key), dtype='<f8')
            for key in ('feature_mean', 'feature_scale', 'coefficients', 'intercepts')}


@dataclass(frozen=True, slots=True)
class Sci02BCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/calibration'
    record_id: str
    study: ObjectIdentity
    model: ObjectIdentity
    roots: tuple[Sci02Root, ...]
    assessments: tuple[ObjectIdentity, ...]
    scores: tuple[Decimal | None, ...]
    radius: Decimal | None
    admitted_calibration_roots: int
    measured_policy_cpu_seconds: Decimal | None
    measured_native_cpu_seconds: Decimal | None
    continue_confirmation: bool

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.study.object_schema != Sci02BDesign.SCHEMA or self.model.object_schema != Sci02BFrozenDescription.SCHEMA
                or len(self.roots) != 8 or tuple(r.ordinal for r in self.roots) != tuple(range(8, 16))
                or any(r.bank != 'DEV' for r in self.roots) or len({r.selection for r in self.roots}) != 1
                or len(self.assessments) != 8 or len(self.scores) != 8
                or self.radius != (None if any(v is None for v in self.scores) else max(self.scores))
                or not 0 <= self.admitted_calibration_roots <= 8):
            raise ValueError('SCI02-B calibration changes its complete original eight-root rank')
        for value in (*self.roots, *self.assessments, self.study, self.model): value.__post_init__()
        for value in (*self.scores, self.radius, self.measured_policy_cpu_seconds, self.measured_native_cpu_seconds):
            if value is not None:
                decimals((value,))
                if value < 0: raise ValueError('SCI02-B calibration changes its nonnegative cost or residual')
        expected = (self.radius is not None and self.admitted_calibration_roots > 0
            and self.measured_policy_cpu_seconds is not None and self.measured_native_cpu_seconds is not None
            and self.measured_policy_cpu_seconds < self.measured_native_cpu_seconds)
        if type(self.continue_confirmation) is not bool or self.continue_confirmation != expected:
            raise ValueError('SCI02-B continuation differs from its frozen necessary opportunity checks')

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02BConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/operation-config'
    config_id: str
    study: Sci02BDesign
    roots: tuple[Sci02Root, ...]
    phase: str
    recipe: str
    provenance: ObjectIdentity
    retained_cases: tuple[ObjectIdentity, ...] = ()
    model: Sci02BFrozenDescription | None = None
    calibration: Sci02BCalibration | None = None
    candidate_dimension: int = 0

    def __post_init__(self):
        pooled = self.phase in ('fit', 'calibrate', 'confirm')
        count = 32 if self.phase == 'confirm' else 8 if pooled else 1
        if (type(self.study) is not Sci02BDesign or len(self.roots) != count or self.phase not in PHASES
                or self.recipe not in ('COMMON', 'ORIGINAL', 'EARLY', 'DELAYED')
                or (self.recipe == 'COMMON') != (self.phase in COMMON)
                or self.config_id != 'config.' + self.node_id
                or self.provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or (self.candidate_dimension not in (24, 32) if self.phase == 'diagnose' else self.candidate_dimension != 0)
                or any(r.selection != self.study.original_selection for r in self.roots)
                or tuple(r.ordinal for r in self.roots) != tuple(sorted({r.ordinal for r in self.roots}))):
            raise ValueError('SCI02-B operation changes its exact source, scope or phase census')
        self.study.__post_init__()
        self.provenance.__post_init__()
        for root in self.roots: root.__post_init__()
        if self.phase in ('diagnose', 'fit'):
            if (any(r.bank != 'DEV' or r.ordinal >= 8 for r in self.roots)
                    or len(self.retained_cases) != count or self.model is not None or self.calibration is not None):
                raise ValueError('SCI02-B development must reuse the exposed original DEV8 only')
        else:
            if self.retained_cases or self.model is None or self.model.study != self.study.identity:
                raise ValueError('SCI02-B new acquisition lacks its original frozen description')
            self.model.__post_init__()
            if any(r.bank == 'DEV' and r.ordinal < 8 for r in self.roots):
                raise ValueError('SCI02-B cannot reacquire an original exposed development root')
            held = self.roots[0].bank == 'HOLDOUT'
            if any((r.bank == 'HOLDOUT') != held for r in self.roots):
                raise ValueError('SCI02-B mixes calibration and confirmation independent units')
            if held and (self.calibration is None or not self.calibration.continue_confirmation):
                raise ValueError('SCI02-B confirmation lacks its assessed calibration continuation')
            if not held and self.calibration is not None:
                raise ValueError('SCI02-B calibration cannot consume its own future bound')
            if self.calibration is not None:
                self.calibration.__post_init__()
                if (self.calibration.model, self.calibration.study) != (self.model.identity, self.study.identity):
                    raise ValueError('SCI02-B substitutes an earlier model or calibration')
        for value in self.retained_cases:
            if value.object_schema != Sci02BRetainedCase.SCHEMA:
                raise ValueError('SCI02-B development changes its original retained operands')
            value.__post_init__()

    @property
    def root(self):
        if len(self.roots) != 1: raise ValueError('SCI02-B pooled operation has no single root')
        return self.roots[0]

    @property
    def design(self): return self.study.physical

    @property
    def node_id(self):
        unit = self.roots[0].group_id if len(self.roots) == 1 else 'pool.' + self.phase
        candidate = f'.d{self.candidate_dimension}' if self.phase == 'diagnose' else ''
        return f'{NAMESPACE}.{self.study.fingerprint()[:16]}.{unit}.{self.recipe.lower()}{candidate}.{self.phase}'

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02BProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/product'
    record_id: str
    config: Sci02BConfig
    predecessors: tuple[ObjectIdentity, ...]
    arrays: Sci02Arrays
    disposition: str
    reasons: tuple[str, ...]
    measurements: tuple[tuple[str, Decimal | None], ...] = ()
    generators: tuple[tuple[int, ParameterGeneratorState], ...] = ()
    native: tuple[Sci02NativeHistory, ...] = ()
    frozen_description: Sci02BFrozenDescription | None = None
    calibration_result: Sci02BCalibration | None = None

    def __post_init__(self):
        if (self.record_id != 'product.' + self.config.node_id or type(self.arrays) is not Sci02Arrays
                or self.disposition not in ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE')
                or self.reasons != tuple(sorted(set(self.reasons)))
                or self.disposition == 'UNAVAILABLE' and not self.reasons
                or tuple(v.object_id for v in self.predecessors) != tuple(sorted({v.object_id for v in self.predecessors}))
                or tuple(k for k, _ in self.measurements) != tuple(sorted({k for k, _ in self.measurements}))
                or len(self.native) > 1 or self.config.phase not in NATIVE_PHASES and (self.native or self.generators)
                or self.frozen_description is not None and self.config.phase != 'fit'
                or self.calibration_result is not None and self.config.phase != 'calibrate'):
            raise ValueError('SCI02-B product changes its exact scientific or custody census')
        for value in (self.config, self.arrays, *self.predecessors, *self.native): value.__post_init__()
        for _, value in self.measurements:
            if value is not None: decimals((value,))
        if self.config.phase in NATIVE_PHASES and self.disposition == 'AVAILABLE':
            count = {'prefix': 64, 'completion': 256, 'baseline': 32, 'reference': 64}[self.config.phase]
            purpose = 'preparation' if self.config.phase in ('prefix', 'completion') else 'autonomous'
            panels = (0,) if purpose == 'preparation' else (0, 1)
            expected = tuple((p, purpose + '-' + suffix) for p in panels for suffix in ('coarse-driver', 'fine-bridge'))
            if (len(self.native) != 1 or tuple((p, s.purpose) for p, s in self.generators) != expected
                    or any(s.completed_noise_matrices != count for _, s in self.generators)):
                raise ValueError('SCI02-B native result loses exact original continuation custody')
        for _, state in self.generators: state.__post_init__()
        if self.frozen_description is not None:
            self.frozen_description.__post_init__()
            if self.frozen_description.study != self.config.study.identity:
                raise ValueError('SCI02-B fit product substitutes its selected study')
        if self.calibration_result is not None:
            self.calibration_result.__post_init__()
            if self.calibration_result.study != self.config.study.identity:
                raise ValueError('SCI02-B calibration product substitutes its selected study')

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02BNativeCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/native-checkpoint'
    record_id: str
    config: ObjectIdentity
    arrays: Sci02Arrays
    generators: tuple[tuple[int, ParameterGeneratorState], ...]
    measurements: tuple[tuple[str, Decimal | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.config.object_schema != Sci02BConfig.SCHEMA or type(self.arrays) is not Sci02Arrays or not self.generators
                or tuple((p, s.purpose) for p, s in self.generators) != tuple(sorted({(p, s.purpose) for p, s in self.generators}))):
            raise ValueError('SCI02-B native checkpoint changes its original continuation operands')
        self.config.__post_init__()
        self.arrays.__post_init__()
        for _, state in self.generators: state.__post_init__()
        for _, value in self.measurements:
            if value is not None: decimals((value,))
