# SPDX-License-Identifier: MPL-2.0
"""Consumer-specific SCI02-C contracts on the unchanged original reservation."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.matrix.six_matrix_response.parameter_history_segments import ParameterGeneratorState
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays, Sci02Design, Sci02NativeHistory, Sci02Root, Sci02Selection, pin
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import Sci02BRetainedCase, decimals

PROTOCOL_ID = 'matrix.consumer-directed-prediction.h64'
NAMESPACE = 'matrix-sci02c'
NATIVE_PHASES = ('prefix', 'completion', 'baseline', 'reference')
ROOT_PHASES = ('prefix', 'source-state', 'instrument', 'completion', 'handoff', 'baseline', 'observation', 'history-observation',
    'basic', 'request', 'history', 'decision', 'reference', 'assess', 'reduce')
PHASES = (*ROOT_PHASES, 'diagnose', 'fit', 'calibrate', 'confirm')
COMMON = ('prefix', 'source-state', 'instrument', 'basic', 'request', 'history', 'decision', 'reduce',
    'diagnose', 'fit', 'calibrate', 'confirm')
POOLED = ('fit', 'calibrate', 'confirm')
SCOPE = 'MATRIX_CONSUMER_PREDICTION_FINITE_RESERVATION_NO_MOLECULAR_QUALIFICATION'
AUDIT_SEED = '7ecaa4b702656ff297db10deec07b04a6fe236c4708c027261dad94739e82b60'


@dataclass(frozen=True, slots=True)
class Sci02CDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/design'
    record_id: str
    original_selection: ObjectIdentity
    physical: Sci02Design
    protocol_document_sha256: str
    dimension: int = 24
    primary_pair: tuple[str, ...] = ('ORIGINAL', 'EARLY')
    scope: str = SCOPE
    receiver_rule: str = 'FACTOR_FORCE_PROJECTED_ODD_MOMENTUM_H64_PANEL_MEAN_ORIGINAL_MINUS_EARLY'
    history_rule: str = 'FIXED_HANDOFF_BASIS_H0_THEN_H16_THEN_H32_OWN_STATE'
    precision: Decimal = Decimal('.001')
    view_tolerance: Decimal = Decimal('.0001')
    ridge_penalty: Decimal = Decimal(1)
    forecast_win_margin: Decimal = Decimal('.0001')
    forecast_critical_wins: int = 22
    required_reduced_deliveries: int = 24
    finite_workloads: tuple[int, ...] = (32, 128, 1024)
    audit_seed: str = AUDIT_SEED

    def __post_init__(self):
        validate_stable_id(self.record_id); validate_sha256(self.protocol_document_sha256)
        if (type(self.original_selection) is not ObjectIdentity or self.original_selection.object_schema != Sci02Selection.SCHEMA
                or type(self.physical) is not Sci02Design or self.dimension != 24 or self.primary_pair != ('ORIGINAL', 'EARLY')
                or self.scope != SCOPE or self.receiver_rule != 'FACTOR_FORCE_PROJECTED_ODD_MOMENTUM_H64_PANEL_MEAN_ORIGINAL_MINUS_EARLY'
                or self.history_rule != 'FIXED_HANDOFF_BASIS_H0_THEN_H16_THEN_H32_OWN_STATE'
                or (self.precision, self.view_tolerance, self.ridge_penalty, self.forecast_win_margin)
                    != (Decimal('.001'), Decimal('.0001'), Decimal(1), Decimal('.0001'))
                or (self.forecast_critical_wins, self.required_reduced_deliveries, self.finite_workloads) != (22, 24, (32, 128, 1024))
                or self.audit_seed != AUDIT_SEED):
            raise ValueError('SCI02-C changes its frozen consumer, supplier, fit, precision or audit rule')
        self.original_selection.__post_init__(); self.physical.__post_init__()

    @property
    def identity(self): return pin(self)

    @property
    def audit_ordinals(self):
        import random
        return tuple(sorted(random.Random(int(self.audit_seed, 16)).sample(range(32), 8)))


@dataclass(frozen=True, slots=True)
class Sci02CRetainedCase(Sci02BRetainedCase):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/retained-case'


@dataclass(frozen=True, slots=True)
class Sci02CFrozenDescription(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/frozen-description'
    record_id: str
    study: ObjectIdentity
    training_roots: tuple[Sci02Root, ...]
    diagnosis_products: tuple[ObjectIdentity, ...]
    feature_mean: tuple[tuple[Decimal, ...], ...]
    feature_scale: tuple[tuple[Decimal, ...], ...]
    coefficients: tuple[tuple[tuple[Decimal, ...], ...], ...]
    intercepts: tuple[tuple[Decimal, ...], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.study.object_schema != Sci02CDesign.SCHEMA or len(self.training_roots) != 8
                or tuple(r.ordinal for r in self.training_roots) != tuple(range(8))
                or any(r.bank != 'DEV' for r in self.training_roots) or len({r.selection for r in self.training_roots}) != 1
                or len(self.diagnosis_products) != 8 or len({p.object_id for p in self.diagnosis_products}) != 8
                or any(len(v) != 2 for v in (self.feature_mean, self.feature_scale, self.coefficients, self.intercepts))):
            raise ValueError('SCI02-C fit loses the original eight roots or two fixed routes')
        for route in range(2):
            mean, scale, coef, intercept = (getattr(self, k)[route] for k in ('feature_mean', 'feature_scale', 'coefficients', 'intercepts'))
            if (len(mean) != 4 or len(scale) != 4 or any(s <= 0 for s in scale)
                    or len(coef) != 3 or any(len(c) != 4 for c in coef) or len(intercept) != 3
                    or any(coef[0]) or any(coef[1][2:])):
                raise ValueError('SCI02-C fit changes its signed residual accounts or feature roles')
            decimals((*mean, *scale, *intercept, *(v for row in coef for v in row)))
        for v in (self.study, *self.training_roots, *self.diagnosis_products): v.__post_init__()

    @property
    def identity(self): return pin(self)

    def numerical_arrays(self):
        import numpy as np
        return {k: np.asarray(getattr(self, k), dtype='<f8') for k in ('feature_mean', 'feature_scale', 'coefficients', 'intercepts')}


@dataclass(frozen=True, slots=True)
class Sci02CCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/calibration'
    record_id: str
    study: ObjectIdentity
    model: ObjectIdentity
    roots: tuple[Sci02Root, ...]
    assessments: tuple[ObjectIdentity, ...]
    scores: tuple[tuple[tuple[Decimal | None, ...], ...], ...]
    radii: tuple[tuple[Decimal | None, ...], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.study.object_schema != Sci02CDesign.SCHEMA or self.model.object_schema != Sci02CFrozenDescription.SCHEMA
                or len(self.roots) != 8 or tuple(r.ordinal for r in self.roots) != tuple(range(8, 16))
                or any(r.bank != 'DEV' for r in self.roots) or len({r.selection for r in self.roots}) != 1
                or len(self.assessments) != 8 or len(self.scores) != 8 or len(self.radii) != 2
                or any(len(row) != 2 or any(len(v) != 3 for v in row) for row in self.scores)
                or any(len(v) != 3 for v in self.radii)):
            raise ValueError('SCI02-C calibration changes its complete rank-eight population')
        for route in range(2):
            for account in range(3):
                values = tuple(s[route][account] for s in self.scores)
                expected = None if any(v is None for v in values) else max(values)
                if self.radii[route][account] != expected:
                    raise ValueError('SCI02-C calibration changes the frozen maximum-score rule')
                for value in (*values, self.radii[route][account]):
                    if value is not None:
                        decimals((value,))
                        if value < 0: raise ValueError('SCI02-C negative absolute calibration score')
        for v in (self.study, self.model, *self.roots, *self.assessments): v.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02CConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/operation-config'
    config_id: str
    study: Sci02CDesign
    roots: tuple[Sci02Root, ...]
    phase: str
    recipe: str
    provenance: ObjectIdentity
    retained_cases: tuple[ObjectIdentity, ...] = ()
    model: Sci02CFrozenDescription | None = None
    calibration: Sci02CCalibration | None = None

    def __post_init__(self):
        count = 32 if self.phase == 'confirm' else 8 if self.phase in POOLED else 1
        if (type(self.study) is not Sci02CDesign or len(self.roots) != count or self.phase not in PHASES
                or self.recipe not in ('COMMON', 'ORIGINAL', 'EARLY', 'DELAYED')
                or (self.recipe == 'COMMON') != (self.phase in COMMON)
                or self.config_id != 'config.' + self.node_id
                or self.provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or any(r.selection != self.study.original_selection for r in self.roots)
                or tuple(r.ordinal for r in self.roots) != tuple(sorted({r.ordinal for r in self.roots}))):
            raise ValueError('SCI02-C operation changes its exact scientific source or phase census')
        for v in (self.study, self.provenance, *self.roots): v.__post_init__()
        if self.phase in ('diagnose', 'fit'):
            if (any(r.bank != 'DEV' or r.ordinal >= 8 for r in self.roots) or len(self.retained_cases) != count
                    or self.model is not None or self.calibration is not None):
                raise ValueError('SCI02-C training must reuse all original exposed DEV8')
        else:
            if (self.retained_cases or type(self.model) is not Sci02CFrozenDescription or self.model.study != self.study.identity
                    or any(r.bank == 'DEV' and r.ordinal < 8 for r in self.roots)):
                raise ValueError('SCI02-C new acquisition lacks its exact frozen account or enters exposed roots')
            self.model.__post_init__()
            held = self.roots[0].bank == 'HOLDOUT'
            if any((r.bank == 'HOLDOUT') != held for r in self.roots):
                raise ValueError('SCI02-C mixes calibration and confirmation units')
            if held != (self.calibration is not None):
                raise ValueError('SCI02-C confirmation requires its exact calibration; calibration cannot consume itself')
            if self.phase in POOLED and self.phase != ('confirm' if held else 'calibrate'):
                raise ValueError('SCI02-C pooled assessment changes its reserved bank')
            if self.calibration is not None:
                self.calibration.__post_init__()
                if (self.calibration.model, self.calibration.study) != (self.model.identity, self.study.identity):
                    raise ValueError('SCI02-C substitutes a frozen fit or calibration')
        for p in self.retained_cases:
            if p.object_schema != Sci02CRetainedCase.SCHEMA:
                raise ValueError('SCI02-C diagnosis changes its authenticated history export')
            p.__post_init__()

    @property
    def root(self):
        if len(self.roots) != 1: raise ValueError('SCI02-C pooled operation has no single root')
        return self.roots[0]

    @property
    def design(self): return self.study.physical

    @property
    def node_id(self):
        unit = self.roots[0].group_id if len(self.roots) == 1 else 'pool.' + self.phase
        return f'{NAMESPACE}.{self.study.fingerprint()[:16]}.{unit}.{self.recipe.lower()}.{self.phase}'

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02CProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/product'
    record_id: str
    config: Sci02CConfig
    predecessors: tuple[ObjectIdentity, ...]
    arrays: Sci02Arrays
    disposition: str
    reasons: tuple[str, ...]
    measurements: tuple[tuple[str, Decimal | None], ...] = ()
    generators: tuple[tuple[int, ParameterGeneratorState], ...] = ()
    native: tuple[Sci02NativeHistory, ...] = ()
    frozen_description: Sci02CFrozenDescription | None = None
    calibration_result: Sci02CCalibration | None = None

    def __post_init__(self):
        if (self.record_id != 'product.' + self.config.node_id or type(self.arrays) is not Sci02Arrays
                or self.disposition not in ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE')
                or self.reasons != tuple(sorted(set(self.reasons))) or self.disposition == 'UNAVAILABLE' and not self.reasons
                or tuple(v.object_id for v in self.predecessors) != tuple(sorted({v.object_id for v in self.predecessors}))
                or tuple(k for k, _ in self.measurements) != tuple(sorted({k for k, _ in self.measurements}))
                or len(self.native) > 1 or self.config.phase not in NATIVE_PHASES and (self.native or self.generators)
                or self.frozen_description is not None and self.config.phase != 'fit'
                or self.calibration_result is not None and self.config.phase != 'calibrate'):
            raise ValueError('SCI02-C product changes scientific or custody boundaries')
        for v in (self.config, self.arrays, *self.predecessors, *self.native): v.__post_init__()
        if self.config.phase in NATIVE_PHASES and self.disposition == 'AVAILABLE':
            count = {'prefix': 64, 'completion': 256, 'baseline': 32, 'reference': 64}[self.config.phase]
            purpose = 'preparation' if self.config.phase in ('prefix', 'completion') else 'autonomous'
            expected = tuple((p, purpose + '-' + s) for p in ((0,) if purpose == 'preparation' else (0, 1))
                for s in ('coarse-driver', 'fine-bridge'))
            if (len(self.native) != 1 or tuple((p, s.purpose) for p, s in self.generators) != expected
                    or any(s.completed_noise_matrices != count for _, s in self.generators)):
                raise ValueError('SCI02-C native result loses original continuation custody')
        for _, state in self.generators: state.__post_init__()
        for _, value in self.measurements:
            if value is not None: decimals((value,))
        for v in (self.frozen_description, self.calibration_result):
            if v is not None:
                v.__post_init__()
                if v.study != self.config.study.identity: raise ValueError('SCI02-C result changes its selected study')

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class Sci02CNativeCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/native-checkpoint'
    record_id: str
    config: ObjectIdentity
    arrays: Sci02Arrays
    generators: tuple[tuple[int, ParameterGeneratorState], ...]
    measurements: tuple[tuple[str, Decimal | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.config.object_schema != Sci02CConfig.SCHEMA or type(self.arrays) is not Sci02Arrays or not self.generators
                or tuple((p, s.purpose) for p, s in self.generators) != tuple(sorted({(p, s.purpose) for p, s in self.generators}))):
            raise ValueError('SCI02-C native checkpoint changes exact continuation operands')
        self.config.__post_init__(); self.arrays.__post_init__()
        for _, state in self.generators: state.__post_init__()
        for _, value in self.measurements:
            if value is not None: decimals((value,))
