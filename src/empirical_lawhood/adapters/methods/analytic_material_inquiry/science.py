# SPDX-License-Identifier: MPL-2.0
"""Exposed static transverse SI procedure, restricted to the selected two slabs."""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.analytic_contracts import UniformElectronGasAnalyticCheck, UniformElectronGasAnalyticPanel
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.analytic_science import check_analytic_panel, generate_analytic_panel
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, ScientificConditionScope
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

D = Decimal
SOURCE_SHA256 = '372f5cca86988e8dccdeb7ffddccc582ddf3380543d8fb9f9d4a97a07abeaad5'
QUESTION = 'Does the source-scoped static transverse SI response and receiver procedure admit the selected changed slab?'
UNIT = 'analytic-material-inquiry.exposed-slabs'


def validate_source(source):
    if type(source) is not UniformElectronGasAnalyticReferenceConfig or source.fingerprint() != SOURCE_SHA256:
        raise ValueError('analytic material source/configuration substitution')


def later_config(source):
    validate_source(source)
    return replace(source, config_id='empirical-lawhood-uniform-electron-gas-response-analytic-reuse',
        independent_unit_id='unit.empirical-lawhood-uniform-electron-gas-response-analytic-reuse-001',
        slab_thickness_m=D('0.000001'))


def _scope(source_id, source_sha256):
    return ScientificConditionScope('system.analytic-material-inquiry', 'world.analytic-material-inquiry.exposed',
        source_id, ('current-density', 'penetration-depth'), ('A/m^2', 'm'),
        'receiver.static-transverse-y-current', 'clock.requested0-accepted1-applied2-receiver3',
        'Static transverse SI response at exact signed q/action chart and two selected slabs; twenty nested analytic views, zero physical independent units; no physical H_PATH or 300 K admission.',
        source_config_sha256=source_sha256, instance_id=UNIT)


def scope(source):
    return _scope(source.config_id, source.fingerprint())


def source_scope(source_identity):
    """Original frozen source meaning without a worker, source read or asked endpoint."""
    if (type(source_identity) is not ObjectIdentity
            or source_identity.object_schema != UniformElectronGasAnalyticReferenceConfig.SCHEMA
            or source_identity.object_id != 'empirical-lawhood-uniform-electron-gas-response-analytic-development'
            or source_identity.object_version != UniformElectronGasAnalyticReferenceConfig.VERSION
            or source_identity.object_fingerprint != SOURCE_SHA256):
        raise ValueError('material inquiry changes exact frozen source identity')
    return _scope(source_identity.object_id, source_identity.object_fingerprint)


@dataclass(frozen=True, slots=True)
class MaterialSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/analytic-material-inquiry/supply'
    product_id: str
    source: UniformElectronGasAnalyticReferenceConfig
    panel: UniformElectronGasAnalyticPanel
    check: UniformElectronGasAnalyticCheck
    scope: ScientificConditionScope
    disposition: AssessmentDisposition

    def __post_init__(self):
        validate_stable_id(self.product_id, field_name='product_id')
        validate_source(self.source)
        if (self.panel != generate_analytic_panel(self.source) or self.check != check_analytic_panel(self.source, self.panel)
                or not self.check.passed or self.scope != scope(self.source)
                or self.disposition is not AssessmentDisposition.SATISFIED):
            raise ValueError('material supplier changes source-scoped procedure, assessment or receiver')


@dataclass(frozen=True, slots=True)
class MaterialInstance(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/analytic-material-inquiry/instance'
    instance_id: str
    config: UniformElectronGasAnalyticReferenceConfig
    panel: UniformElectronGasAnalyticPanel

    def __post_init__(self):
        validate_stable_id(self.instance_id, field_name='instance_id')


@dataclass(frozen=True, slots=True)
class MaterialAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/analytic-material-inquiry/assessment'
    assessment_id: str
    supplier: ObjectIdentity
    scope: ScientificConditionScope
    instance: MaterialInstance
    check: UniformElectronGasAnalyticCheck
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.assessment_id, field_name='assessment_id')
        if (self.check != check_analytic_panel(self.instance.config, self.instance.panel)
                or self.disposition is not (AssessmentDisposition.SATISFIED if self.check.passed else AssessmentDisposition.FALSIFIED)
                or self.reason_codes != self.check.reason_codes):
            raise ValueError('material assessment changes its independently checked instance verdict')


def supply(source):
    validate_source(source)
    panel = generate_analytic_panel(source)
    return MaterialSupply('product.analytic-material-inquiry.supply', source, panel,
                          check_analytic_panel(source, panel), scope(source), AssessmentDisposition.SATISFIED)


def compatible_instance(supplier):
    config = later_config(supplier.source)
    return MaterialInstance('instance.analytic-material-inquiry.reuse', config, generate_analytic_panel(config))


def assess(supplier, instance):
    validate_source(supplier.source)
    MaterialSupply(supplier.product_id, supplier.source, supplier.panel, supplier.check, supplier.scope, supplier.disposition)
    if instance.config != later_config(supplier.source):
        raise ValueError('material consumer substitutes the exact selected config diff')
    check = check_analytic_panel(instance.config, instance.panel)
    return MaterialAssessment('assessment.analytic-material-inquiry.use', ObjectIdentity.from_record(supplier.product_id, supplier),
        supplier.scope, instance, check, AssessmentDisposition.SATISFIED if check.passed else AssessmentDisposition.FALSIFIED, check.reason_codes)
