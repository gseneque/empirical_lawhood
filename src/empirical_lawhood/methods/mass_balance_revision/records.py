# SPDX-License-Identifier: MPL-2.0
"""An exact gram derivative keeps its original kg forecast and assessment custody."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.methods.mass_balance_starter.records import MAX_BYTES as MAX_BYTES, PREFIX, MassAssessment, MassForecast, MassScope, mass
from empirical_lawhood.methods.mass_balance_starter.science import prediction_config
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.execution.plans import DevelopmentExecutionPlan
from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding

NAMESPACE = 'mass-balance'
PROTOCOL_ID = 'mass-balance.forecast-upgrade'
WORKFLOW_ID = 'mass-balance-record-upgrade'
CONVERSION = 'exact-kg-to-g'
MAX_SOURCE_BYTES = 64 * 1024


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def require_reference(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError('forecast upgrade changes an exact original record revision')


@dataclass(frozen=True, slots=True)
class ForecastUpgradeSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + '/forecast-upgrade-source'
    record_id: str
    forecast: MassForecast
    assessment: MassAssessment
    producing_receipts: tuple[CanonicalTaskReceipt, ...]
    original_packet: ObjectIdentity
    original_execution_plan: ObjectIdentity
    original_implementation: ObjectIdentity
    evidence_scope: str = 'EXPOSED_DEVELOPMENT'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.forecast) is not MassForecast or type(self.assessment) is not MassAssessment:
            raise TypeError('forecast upgrade requires the complete original version-1 forecast and assessment')
        self.forecast.__post_init__()
        self.assessment.__post_init__()
        if (self.assessment.forecast != self.forecast.identity
                or prediction_config(self.assessment.config) != self.forecast.config
                or self.evidence_scope != 'EXPOSED_DEVELOPMENT'):
            raise ValueError('forecast upgrade changes original scientific scope, complete census or exposure')
        for reference, kind in ((self.original_packet, AuthoredRecursiveWave),
                (self.original_execution_plan, DevelopmentExecutionPlan),
                (self.original_implementation, RecursiveImplementationBinding)):
            require_reference(reference, kind)
        if (type(self.producing_receipts) is not tuple or len(self.producing_receipts) != 2
                or any(type(row) is not CanonicalTaskReceipt for row in self.producing_receipts)
                or tuple(row.receipt_id for row in self.producing_receipts)
                != tuple(sorted({row.receipt_id for row in self.producing_receipts}))
                or len({row.run_id for row in self.producing_receipts}) != 1):
            raise ValueError('forecast upgrade requires both original sorted producing receipts')
        for product in (self.forecast, self.assessment):
            matches = tuple(row for row in self.producing_receipts if row.task_id == product.config.node_id)
            if len(matches) != 1 or matches[0].operational_status is not OperationalStatus.SUCCEEDED:
                raise ValueError('forecast upgrade lacks an original successful producing receipt')
            receipt = matches[0]
            receipt.__post_init__()
            if len(receipt.output_logical_artifacts) != 1 or len(receipt.output_materializations) != 1:
                raise ValueError('forecast upgrade changes the original complete one-product receipt')
            logical, physical = receipt.output_logical_artifacts[0], receipt.output_materializations[0]
            if (logical.payload_schema != product.SCHEMA or logical.content_sha256 != product.fingerprint()
                    or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'
                    or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                    or physical.logical_artifact_id != logical.logical_artifact_id
                    or physical.physical_sha256 != product.fingerprint() or physical.compression != 'none'
                    or physical.partition_selector is not None or physical.size_bytes != product.canonical_size_bytes()):
                raise ValueError('forecast upgrade changes original exact canonical bytes or their exposed custody')
        if self.canonical_size_bytes() > MAX_SOURCE_BYTES:
            raise ValueError('forecast upgrade source exceeds its declared 64 KiB input bound')

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class ForecastUpgradeSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + '/forecast-upgrade-specification'
    record_id: str
    source: ObjectIdentity
    scope: MassScope
    independent_unit_ids: tuple[str, ...]
    conversion: str = CONVERSION

    def __post_init__(self):
        validate_stable_id(self.record_id)
        require_reference(self.source, ForecastUpgradeSource)
        if type(self.scope) is not MassScope:
            raise TypeError('forecast upgrade requires the original exact kg source scope')
        self.scope.__post_init__()
        require_sorted_unique_strings(self.independent_unit_ids, field_name='independent_unit_ids', allow_empty=False)
        if len(self.independent_unit_ids) > 16 or self.conversion != CONVERSION:
            raise ValueError('forecast upgrade supports only exact kg-to-g conversion of at most sixteen original units')

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class ForecastUpgradeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + '/forecast-upgrade-config'
    config_id: str
    specification: ForecastUpgradeSpecification

    def __post_init__(self):
        if type(self.specification) is not ForecastUpgradeSpecification:
            raise TypeError('forecast upgrade requires its exact selected specification')
        self.specification.__post_init__()
        if self.config_id != 'config.mass-balance.upgrade.' + self.specification.fingerprint():
            raise ValueError('forecast upgrade changes its code-derived operation identity')

    @property
    def node_id(self):
        return self.config_id.removeprefix('config.')


@dataclass(frozen=True, slots=True)
class GramPrediction(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + '/gram-prediction'
    unit_id: str
    original_kg: Decimal
    final_g: Decimal
    units: str = 'g'

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        mass(self.original_kg, Decimal('2e9'))
        mass(self.final_g, Decimal('2e12'))
        if self.units != 'g' or Fraction(self.final_g) != 1000 * Fraction(self.original_kg):
            raise ValueError('gram prediction fails its independent exact unit-conversion check')


@dataclass(frozen=True, slots=True)
class MassForecastV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = MassForecast.SCHEMA
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    config: ForecastUpgradeConfig
    original_source: ForecastUpgradeSource
    rows: tuple[GramPrediction, ...]

    def __post_init__(self):
        if type(self.config) is not ForecastUpgradeConfig or type(self.original_source) is not ForecastUpgradeSource:
            raise TypeError('version-2 forecast requires its exact derivative configuration and original custody')
        self.config.__post_init__()
        self.original_source.__post_init__()
        specification = self.config.specification
        original = self.original_source.forecast
        if (self.record_id != self.config.node_id + '.product' or specification.source != self.original_source.identity
                or specification.scope != original.config.scope
                or specification.independent_unit_ids != original.config.independent_unit_ids
                or type(self.rows) is not tuple
                or tuple(row.unit_id for row in self.rows) != original.config.independent_unit_ids):
            raise ValueError('version-2 forecast changes its original source, scope or complete independent-unit census')
        for row, old in zip(self.rows, original.rows, strict=True):
            if type(row) is not GramPrediction or row.original_kg != old.final_kg:
                raise ValueError('version-2 forecast changes an original kg prediction')
            row.__post_init__()

    @property
    def identity(self):
        return identity(self)
