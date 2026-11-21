# SPDX-License-Identifier: MPL-2.0
"""Frozen physical selection, independent streams and complete SCI02-D products."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays, pin
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkCompletion, require_native_completion_receipt

PROTOCOL_ID = 'matrix.paired-equilibrium-bridge.sci02d'
NAMESPACE = 'matrix-sci02d'
SCOPE = 'FINITE_HAMILTONIAN_EQUILIBRIUM_ESTIMATION_NO_MOLECULAR_QUALIFICATION'
PHASES = ('controls', 'sample', 'assess', 'fit', 'confirm')
METHODS = ('NATIVE', 'COORDINATE', 'STRUCTURE')
BANK_COUNTS = {'TRAINING': 16, 'CONFIRMATION': 64, 'REFERENCE': 8}


@dataclass(frozen=True, slots=True)
class BridgeNativeHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/native-history'
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt

    def __post_init__(self):
        require_native_completion_receipt(self.completion, self.receipt)
        if (self.completion.definition != self.definition.identity
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.output_ids != ('arrays', 'checkpoint', 'gradients', 'positions')
                or self.completion.omitted_output_ids or self.completion.consumed_streams != self.definition.streams
                or self.completion.unconsumed_streams or self.completion.unknown_streams
                or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                or not set(self.definition.input_materialization_ids) <= set(self.receipt.input_materialization_ids)):
            raise ValueError('SCI02-D requires its known original native completion and complete receipted shards')


@dataclass(frozen=True, slots=True)
class BridgeDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/design'
    record_id: str
    protocol_document_sha256: str
    q: int = 2
    alpha_x: Decimal = Decimal('0.6666666666666666666666666667')
    alpha_y: Decimal = Decimal('7.333333333333333333333333334')
    potential_mass: Decimal = Decimal('.5')
    couplings: tuple[Decimal, ...] = (Decimal('.5'), Decimal('2'))
    temperature: Decimal = Decimal('1')
    friction: Decimal = Decimal('1')
    timestep: Decimal = Decimal('.001')
    stiffness: Decimal = Decimal('32')
    centers: tuple[Decimal, ...] = tuple(Decimal(i)/10 for i in range(8, 13))
    burn_steps: int = 8192
    production_steps: int = 16384
    sample_stride: int = 64
    block_samples: int = 32
    reference_multiplier: int = 4
    ridge_fraction: Decimal = Decimal('.01')
    target_error: Decimal = Decimal('.01')
    numerical_allowance: Decimal = Decimal('.002')
    quadrature_allowance: Decimal = Decimal('.002')
    preparation_allowance: Decimal = Decimal('.002')
    minimum_saving: Decimal = Decimal('.20')
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id); validate_sha256(self.protocol_document_sha256)
        if any(type(getattr(self, name)) is not int for name in ('q', 'burn_steps', 'production_steps', 'sample_stride', 'block_samples', 'reference_multiplier')):
            raise ValueError('SCI02-D requires exact integer dimensions and clocks')
        expected = (2, Decimal('0.6666666666666666666666666667'), Decimal('7.333333333333333333333333334'),
            Decimal('.5'), (Decimal('.5'), Decimal('2')), Decimal(1), Decimal(1), Decimal('.001'), Decimal(32),
            tuple(Decimal(i)/10 for i in range(8, 13)), 8192, 16384, 64, 32, 4, Decimal('.01'), Decimal('.01'),
            Decimal('.002'), Decimal('.002'), Decimal('.002'), Decimal('.20'), SCOPE)
        actual = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name not in ('SCHEMA', 'record_id', 'protocol_document_sha256'))
        if actual != expected: raise ValueError('SCI02-D changes its frozen physical, sampling or assessment selection')
        if any(type(v) is not Decimal or not v.is_finite() for v in (*self.couplings, *self.centers,
                self.alpha_x, self.alpha_y, self.potential_mass, self.temperature, self.friction, self.timestep,
                self.stiffness, self.ridge_fraction, self.target_error, self.numerical_allowance,
                self.quadrature_allowance, self.preparation_allowance, self.minimum_saving)):
            raise ValueError('SCI02-D requires exact finite Decimal operands')

    @property
    def identity(self): return pin(self)

    def grid(self, bank):
        if bank not in BANK_COUNTS: raise ValueError('unknown SCI02-D bank')
        return tuple(Decimal(i)/20 for i in range(16, 25)) if bank == 'REFERENCE' else self.centers


@dataclass(frozen=True, slots=True)
class BridgeStream(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/stream'
    record_id: str
    seed_sha256: str
    purpose: str

    def __post_init__(self):
        validate_stable_id(self.record_id); validate_sha256(self.seed_sha256)
        if self.purpose not in ('INITIAL_MOMENTUM', 'COARSE_INNOVATION', 'FINE_BRIDGE'):
            raise ValueError('SCI02-D random stream changes its purpose')

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class BridgeSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/selection'
    record_id: str
    design: BridgeDesign
    seed_sha256: str
    exposure: str = 'NEW_NONPROMOTABLE_NUMERICAL_STUDY_NOT_PREVIOUS_SCI02_RESERVATION'

    def __post_init__(self):
        validate_stable_id(self.record_id); validate_sha256(self.seed_sha256)
        if type(self.design) is not BridgeDesign or self.exposure != 'NEW_NONPROMOTABLE_NUMERICAL_STUDY_NOT_PREVIOUS_SCI02_RESERVATION':
            raise ValueError('SCI02-D source selection changes its evidence role')
        self.design.__post_init__()

    @property
    def identity(self): return pin(self)

    def streams(self, bank, ordinal):
        if bank not in BANK_COUNTS or type(ordinal) is not int or not 0 <= ordinal < BANK_COUNTS[bank]:
            raise ValueError('SCI02-D root is outside its committed allocation')
        group = f'sci02d.{self.fingerprint()}.{bank.lower()}.{ordinal:02d}'
        return tuple(BridgeStream('stream.' + group + '.' + purpose.lower(),
            sha256((self.seed_sha256 + ':' + group + ':' + purpose).encode()).hexdigest(), purpose)
            for purpose in ('COARSE_INNOVATION', 'FINE_BRIDGE', 'INITIAL_MOMENTUM'))

    def root(self, bank, ordinal):
        streams = self.streams(bank, ordinal)
        group = f'sci02d.{self.fingerprint()}.{bank.lower()}.{ordinal:02d}'
        return BridgeRoot('root.' + group, self.identity, group, bank, ordinal, tuple(v.identity for v in streams))


@dataclass(frozen=True, slots=True)
class BridgeRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/root'
    record_id: str
    selection: ObjectIdentity
    group_id: str
    bank: str
    ordinal: int
    streams: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if (self.selection.object_schema != BridgeSelection.SCHEMA or self.bank not in BANK_COUNTS
                or type(self.ordinal) is not int or not 0 <= self.ordinal < BANK_COUNTS[self.bank]
                or self.group_id != f'sci02d.{self.selection.object_fingerprint}.{self.bank.lower()}.{self.ordinal:02d}'
                or self.record_id != 'root.' + self.group_id or len(self.streams) != 3
                or any(v.object_schema != BridgeStream.SCHEMA for v in self.streams)
                or tuple(v.object_id for v in self.streams) != tuple(sorted({v.object_id for v in self.streams}))):
            raise ValueError('SCI02-D root loses its complete original random allocation')
        for v in (self.selection, *self.streams): v.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class BridgeFit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/frozen-fit'
    record_id: str
    study: ObjectIdentity
    training: tuple[ObjectIdentity, ...]
    coefficients: tuple[tuple[Decimal, ...], ...]
    sampling_fractions: tuple[Decimal, ...]

    def __post_init__(self):
        if (self.study.object_schema != BridgeDesign.SCHEMA or len(self.training) != 16
                or len({v.object_id for v in self.training}) != 16 or len(self.coefficients) != 3
                or any(len(v) != 4 for v in self.coefficients) or any(self.coefficients[0])
                or any(self.coefficients[1][1:]) or len(self.sampling_fractions) != 3
                or self.sampling_fractions[0] != 1
                or any(v not in (Decimal('.25'), Decimal('.5'), Decimal(1)) for v in self.sampling_fractions)):
            raise ValueError('SCI02-D fit changes its original training census or bounded estimator menu')
        validate_stable_id(self.record_id)
        for row in self.coefficients:
            if any(type(v) is not Decimal or not v.is_finite() for v in row): raise ValueError('nonfinite SCI02-D coefficient')
        for p in (self.study, *self.training): p.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class BridgeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/operation-config'
    config_id: str
    design: BridgeDesign
    selection: ObjectIdentity
    roots: tuple[BridgeRoot, ...]
    phase: str
    provenance: ObjectIdentity
    fitted: BridgeFit | None = None

    def __post_init__(self):
        if (type(self.design) is not BridgeDesign or self.selection.object_schema != BridgeSelection.SCHEMA
                or self.phase not in PHASES or self.provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or self.config_id != 'config.' + self.node_id
                or any(r.selection != self.selection for r in self.roots)
                or tuple(r.group_id for r in self.roots) != tuple(sorted({r.group_id for r in self.roots}))):
            raise ValueError('SCI02-D operation changes its scientific operands')
        n = 0 if self.phase == 'controls' else 16 if self.phase == 'fit' else 72 if self.phase == 'confirm' else 1
        if len(self.roots) != n: raise ValueError('SCI02-D operation changes its complete assigned census')
        expected = () if self.phase == 'controls' else ('TRAINING',) if self.phase == 'fit' else ('CONFIRMATION', 'REFERENCE') if self.phase == 'confirm' else (self.roots[0].bank,)
        if tuple(sorted({r.bank for r in self.roots})) != expected: raise ValueError('SCI02-D operation mixes bank roles')
        trained = any(r.bank != 'TRAINING' for r in self.roots)
        if trained != (self.fitted is not None): raise ValueError('SCI02-D evaluation requires its frozen training fit')
        if self.fitted is not None:
            self.fitted.__post_init__()
            if self.fitted.study != self.design.identity: raise ValueError('SCI02-D fit belongs to another target')
        for p in (self.design, self.selection, self.provenance, *self.roots): p.__post_init__()

    @property
    def node_id(self):
        unit = self.roots[0].group_id if len(self.roots) == 1 else 'pool'
        return f'{NAMESPACE}.{self.design.fingerprint()[:16]}.{unit}.{self.phase}'

    @property
    def root(self):
        if len(self.roots) != 1: raise ValueError('SCI02-D pooled operation has no single root')
        return self.roots[0]

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class BridgeProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/product'
    record_id: str
    config: BridgeConfig
    predecessors: tuple[ObjectIdentity, ...]
    arrays: Sci02Arrays
    disposition: str
    reasons: tuple[str, ...]
    measurements: tuple[tuple[str, Decimal | None], ...] = ()
    native: tuple[BridgeNativeHistory, ...] = ()
    fit: BridgeFit | None = None
    shards: tuple[Sci02Arrays, ...] = ()

    def __post_init__(self):
        if (self.record_id != 'product.' + self.config.node_id or type(self.arrays) is not Sci02Arrays
                or self.disposition not in ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE')
                or self.reasons != tuple(sorted(set(self.reasons)))
                or self.disposition == 'UNAVAILABLE' and not self.reasons
                or tuple(v.object_id for v in self.predecessors) != tuple(sorted({v.object_id for v in self.predecessors}))
                or tuple(k for k, _ in self.measurements) != tuple(sorted({k for k, _ in self.measurements}))
                or len(self.native) != (1 if self.config.phase == 'sample' else 0)
                or len(self.shards) != (2 if self.config.phase == 'sample' else 0)
                or self.fit is not None and self.config.phase != 'fit'):
            raise ValueError('SCI02-D product changes its original custody or complete findings')
        for value in (self.config, self.arrays, *self.shards, *self.predecessors, *self.native): value.__post_init__()
        if self.shards and (tuple(tuple(m.name for m in a.members) for a in self.shards) != (('positions',), ('gradients',))
                or len({a.array_artifact.artifact_id for a in (self.arrays, *self.shards)}) != 3):
            raise ValueError('SCI02-D sample product changes its exact position/force shard contracts')
        for _, value in self.measurements:
            if value is not None and (type(value) is not Decimal or not value.is_finite()): raise ValueError('SCI02-D nonfinite measurement')
        if self.fit is not None: self.fit.__post_init__()

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class BridgeCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/native-checkpoint'
    record_id: str
    config: ObjectIdentity
    arrays: Sci02Arrays
    measurements: tuple[tuple[str, Decimal | None], ...]
    shards: tuple[Sci02Arrays, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if self.config.object_schema != BridgeConfig.SCHEMA: raise ValueError('SCI02-D checkpoint changes its original task')
        self.config.__post_init__(); self.arrays.__post_init__()
        if len(self.shards) != 2: raise ValueError('SCI02-D native checkpoint loses complete position and force shards')
        for value in self.shards: value.__post_init__()
        if tuple(tuple(m.name for m in a.members) for a in self.shards) != (('positions',), ('gradients',)):
            raise ValueError('SCI02-D checkpoint changes its exact position/force shard contracts')
