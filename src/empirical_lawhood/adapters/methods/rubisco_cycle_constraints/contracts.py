# SPDX-License-Identifier: MPL-2.0
"""Exact mechanism provenance and conditional model products, never microrate data."""
from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, AssessmentPhase, ScientificConditionScope
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from .science import BranchRates, BranchObservables, JointNecessities, CommonReleaseResponse
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import Candidate

D = Decimal
NAMESPACE = 'rubisco-cycle-constraints'
UNIT = NAMESPACE + '.exposed-mathematical-analysis'
QUESTION = 'Which conditional gas-cycle assumptions permit joint endpoint gains, and which candidate evidence is still missing?'
CUTOFF = 'exposed-through-2026-10-11-mechanism-audit'
TOPOLOGY = 'gas-ready-X-plus-gas-reversible-C-reversible-P-release-X-v1'
ASSUMPTIONS = ('activation-fixed', 'gas-ready-enzyme-census-normalized', 'hypothetical-microrates-not-inferred',
               'product-concentrations-fixed', 'rubp-enolization-fixed', 'same-release-multiplier-both-branches')
SOURCE_MEMBERS = (
    ('cummins2018-primary.xml', 246858, '4ee8089ef298ee9cc5989c3535cf89aa961decf32734d59f3f437529b68f196d'),
    ('cummins2019-response.html', 147570, '5b5c6b6303f53a661daac6512a9b0d82b7d8320c60b74e1e4da0513782f6d8f7'),
)


def identity(record):
    name = next(name for name in ('product_id', 'input_id', 'config_id', 'check_id', 'instance_id', 'assessment_id', 'design_id')
                if hasattr(record, name))
    return ObjectIdentity.from_record(getattr(record, name), record)


@dataclass(frozen=True, slots=True)
class MechanismSourceBytes(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/mechanism-source-bytes'
    source_id: str
    size_bytes: int
    source_sha256: str
    raw_utf8: str

    def __post_init__(self):
        raw = self.raw_utf8.encode('utf-8')
        if ((self.source_id, self.size_bytes, self.source_sha256) not in SOURCE_MEMBERS
                or len(raw) != self.size_bytes or sha256(raw).hexdigest() != self.source_sha256):
            raise ValueError('cycle mechanism source bytes, member or digest substitution')


@dataclass(frozen=True, slots=True)
class MechanismSourceAudit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/mechanism-source-audit'
    input_id: str
    sources: tuple[MechanismSourceBytes, ...]
    cutoff: str = CUTOFF

    def __post_init__(self):
        validate_stable_id(self.input_id, field_name='input_id')
        if self.cutoff != CUTOFF or tuple((row.source_id, row.size_bytes, row.source_sha256) for row in self.sources) != SOURCE_MEMBERS:
            raise ValueError('cycle mechanism source census or exposure cutoff substitution')
        for row in self.sources:
            MechanismSourceBytes(row.source_id, row.size_bytes, row.source_sha256, row.raw_utf8)


def source_audit_from_bytes(raw_sources, *, input_id='input.rubisco-cycle.mechanism-audit'):
    if set(raw_sources) != {row[0] for row in SOURCE_MEMBERS}:
        raise ValueError('cycle source requires the complete exact primary mechanism census')
    return MechanismSourceAudit(input_id, tuple(MechanismSourceBytes(name, size, digest, raw_sources[name].decode('utf-8'))
                                               for name, size, digest in SOURCE_MEMBERS))


@dataclass(frozen=True, slots=True)
class CycleDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/model-design'
    design_id: str
    source: ObjectIdentity
    source_members: tuple[tuple[str, int, str], ...] = SOURCE_MEMBERS
    topology: str = TOPOLOGY
    assumptions: tuple[str, ...] = ASSUMPTIONS
    cutoff: str = CUTOFF

    def __post_init__(self):
        if (self.design_id != 'design.rubisco-cycle.conditional-gas-branch'
                or self.source.object_schema != MechanismSourceAudit.SCHEMA
                or self.source_members != SOURCE_MEMBERS or self.topology != TOPOLOGY
                or self.assumptions != ASSUMPTIONS or self.cutoff != CUTOFF):
            raise ValueError('cycle design changes mechanism source, topology, assumptions or cutoff')


def design_from_source(source):
    MechanismSourceAudit(source.input_id, source.sources, source.cutoff)
    return CycleDesign('design.rubisco-cycle.conditional-gas-branch', identity(source))


def scope(design):
    return ScientificConditionScope('system.rubisco-cycle.conditional-gas-branch', 'world.rubisco-cycle.analytic',
        design.source.object_id, ('specificity-multiplier', 'turnover-multiplier'), ('dimensionless', 'dimensionless'),
        'receiver.conditional-macro-endpoint-constraints', 'clock.exposed-mechanism-analysis',
        'Hypothetical X+gas reversible C reversible P releases X; activation/RuBP/enolization fixed. Published mechanism sources motivate a declared countermodel, not fitted biological microrates or candidate qualification.',
        source_config_sha256=identity(design).object_fingerprint, instance_id=UNIT)


@dataclass(frozen=True, slots=True)
class BalanceProbe(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/balance-probe'
    probe_id: str
    rates: BranchRates
    gas_um: Decimal


def selected_probes():
    """The complete declared mathematical falsifier denominator; no biological units."""
    return tuple(BalanceProbe(f'probe.{index}.{gas}', BranchRates(D('.2'), D(off), D(a), D(b), D(release)), D(gas))
                 for index, (a, b, release, off) in enumerate(((3, 0, 7, 2), (3, 5, 7, 2), (7, 2, 1, 0), (1, 20, 4, 13)))
                 for gas in ('0', '0.01', '1', '100'))


@dataclass(frozen=True, slots=True)
class BalanceResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/balance-result'
    probe: BalanceProbe
    observables: BranchObservables
    occupancy_x: Decimal
    occupancy_c: Decimal
    occupancy_p: Decimal
    independent_flux_s_inv: Decimal
    predicted_flux_s_inv: Decimal
    maximum_balance_residual_s_inv: Decimal
    absolute_flux_discrepancy_s_inv: Decimal
    passed: bool


@dataclass(frozen=True, slots=True)
class CycleProcedureAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/procedure-assessment'
    check_id: str
    results: tuple[BalanceResult, ...]
    irreversible_release_cancellation: bool
    reverse_capture_release_dependence: bool
    tolerance: Decimal
    disposition: AssessmentDisposition
    release_checks: tuple['ReleaseBalanceResult', ...] = ()
    phase: AssessmentPhase = AssessmentPhase.PROCEDURE

    def __post_init__(self):
        if (self.check_id != 'check.rubisco-cycle.normalized-state-balance' or self.tolerance != D('1e-12')
                or self.phase is not AssessmentPhase.PROCEDURE):
            raise ValueError('cycle independent assessment changes its scientific tolerance')
        if tuple(row.probe for row in self.results) != selected_probes():
            raise ValueError('cycle independent assessment changes complete probe census')
        if tuple((row.scenario, row.multiplier) for row in self.release_checks) != tuple(
                (scenario, multiplier) for scenario in DEFAULT_SCENARIOS for multiplier in RELEASE_MULTIPLIERS):
            raise ValueError('cycle procedure drops declared conditional witness denominator')
        passed = (all(row.passed for row in self.results) and all(row.passed for row in self.release_checks)
                  and self.irreversible_release_cancellation and self.reverse_capture_release_dependence)
        expected = AssessmentDisposition.SATISFIED if passed else AssessmentDisposition.FALSIFIED
        if self.disposition is not expected:
            raise ValueError('cycle procedure disposition contradicts independent checks')


@dataclass(frozen=True, slots=True)
class CycleSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/model-supply'
    product_id: str
    design: CycleDesign
    check: CycleProcedureAssessment
    scope: ScientificConditionScope
    disposition: AssessmentDisposition

    def __post_init__(self):
        if (self.product_id != 'product.rubisco-cycle.assessed-conditional-model'
                or self.scope != scope(self.design) or self.disposition is not self.check.disposition):
            raise ValueError('cycle supply changes original scope or actual procedure assessment')


@dataclass(frozen=True, slots=True)
class LatentScenario(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/latent-scenario'
    scenario_id: str
    carbon_v: Decimal
    carbon_u: Decimal
    oxygen_u: Decimal

    def __post_init__(self):
        from .science import common_release_response
        validate_stable_id(self.scenario_id, field_name='scenario_id')
        common_release_response(carbon_v=self.carbon_v, carbon_u=self.carbon_u, oxygen_u=self.oxygen_u, release_multiplier=D(1))


DEFAULT_SCENARIOS = tuple(LatentScenario(f'scenario.v{v}.c{u}.o{o}', D(v), D(u), D(o))
                          for v in ('1', '4', '10') for u in ('0', '0.5', '1', '5') if D(u) < D(v)
                          for o in ('0', '0.5', '1', '5'))
RELEASE_MULTIPLIERS = tuple(map(D, ('1', '2', '5', '10', '20', '100')))
REFERENCE_IDS = ('coupled', 'radiometric')
FINALIST_IDS = ('gp.wt', 'nt.a369.t391i', 'potato.ps3', 'potato.pst', 'wilson2017-row17')


@dataclass(frozen=True, slots=True)
class ReleaseBalanceResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/release-balance-result'
    scenario: LatentScenario
    multiplier: Decimal
    maximum_relative_discrepancy: Decimal
    passed: bool

    def __post_init__(self):
        if (not self.maximum_relative_discrepancy.is_finite() or self.maximum_relative_discrepancy < 0
                or self.passed != (self.maximum_relative_discrepancy <= D('1e-12'))):
            raise ValueError('cycle conditional witness check contradicts actual discrepancy')


@dataclass(frozen=True, slots=True)
class CycleInstanceInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/instance'
    instance_id: str
    macro_source: ObjectIdentity
    candidate_ids: tuple[str, ...] = FINALIST_IDS
    reference_ids: tuple[str, ...] = REFERENCE_IDS
    scenarios: tuple[LatentScenario, ...] = DEFAULT_SCENARIOS
    release_multipliers: tuple[Decimal, ...] = RELEASE_MULTIPLIERS

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import require_sorted_unique_strings
        from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import SourceAudit
        validate_stable_id(self.instance_id, field_name='instance_id')
        require_sorted_unique_strings(self.candidate_ids, field_name='candidate_ids', allow_empty=False)
        require_sorted_unique_strings(self.reference_ids, field_name='reference_ids', allow_empty=False)
        if (self.macro_source.object_schema != SourceAudit.SCHEMA or not set(self.reference_ids) <= set(REFERENCE_IDS)
                or self.scenarios != DEFAULT_SCENARIOS or self.release_multipliers != RELEASE_MULTIPLIERS):
            raise ValueError('cycle instance changes source role or complete selected latent/reference census')


@dataclass(frozen=True, slots=True)
class ScenarioSample(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/scenario-sample'
    response: CommonReleaseResponse
    joint_conditional_pass: bool


@dataclass(frozen=True, slots=True)
class CycleScenarioResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/scenario-result'
    scenario: LatentScenario
    necessities: JointNecessities
    irreversible_route_excluded: bool
    samples: tuple[ScenarioSample, ...]
    minimum_release_multiplier: Decimal | None
    maximum_release_multiplier: Decimal | None


def finite_release_interval(scenario, required_k, required_s):
    """Independent affine inequalities for the exact admissible lambda >= 1 interval."""
    with localcontext() as ctx:
        ctx.prec = 50
        v, c, o = scenario.carbon_v, scenario.carbon_u, scenario.oxygen_u
        coefficient = 1 + v - required_k
        if coefficient <= 0:
            return None, None
        lower = max(D(1), required_k * v / coefficient)
        coefficient_s = (1+c) - required_s*(1+o)
        bound_s = required_s*(1+o)*c - (1+c)*o
        upper = None
        if coefficient_s > 0:
            lower = max(lower, bound_s/coefficient_s)
        elif coefficient_s < 0:
            upper = bound_s/coefficient_s
            if upper < lower:
                return None, None
        elif bound_s > 0:
            return None, None
        return lower, upper


@dataclass(frozen=True, slots=True)
class CycleAnchorResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/anchor-result'
    candidate: Candidate
    reference: tuple[str, Decimal, Decimal]
    scenarios: tuple[CycleScenarioResult, ...]


UNKNOWN_REASONS = ('ACTUAL_MICROSCOPIC_RATES_UNIDENTIFIED', 'BIOLOGICAL_CANDIDATE_EFFECT_NOT_PREDICTED',
                   'MATCHED_CANDIDATE_BACKGROUND_TARGET_ASSAYS_MISSING', 'MODEL_TOPOLOGY_NOT_BIOLOGICALLY_QUALIFIED')


@dataclass(frozen=True, slots=True)
class CycleUseProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/instance-assessment'
    product_id: str
    supplier: ObjectIdentity
    model: CycleSupply
    instance: CycleInstanceInput
    anchors: tuple[CycleAnchorResult, ...]
    scope: ScientificConditionScope
    disposition: AssessmentDisposition
    biological_disposition: AssessmentDisposition = AssessmentDisposition.UNEVALUABLE
    reason_codes: tuple[str, ...] = UNKNOWN_REASONS

    def __post_init__(self):
        validate_stable_id(self.product_id, field_name='product_id')
        if (self.supplier.object_schema not in {CycleSupply.SCHEMA, self.SCHEMA}
                or self.scope != self.model.scope or self.biological_disposition is not AssessmentDisposition.UNEVALUABLE
                or self.reason_codes != UNKNOWN_REASONS or self.disposition is not self.model.disposition):
            raise ValueError('cycle use cannot change model scope, assessed adequacy or manufacture biological admission')
        expected = tuple((candidate, reference) for candidate in self.instance.candidate_ids for reference in self.instance.reference_ids)
        if tuple((row.candidate.candidate_id, row.reference[0]) for row in self.anchors) != expected:
            raise ValueError('cycle use changes complete actual candidate/reference denominator')
        from .science import common_release_response, joint_necessities
        for anchor in self.anchors:
            if anchor.candidate.turnover_s_inv is None or anchor.candidate.specificity_dimensionless is None:
                raise ValueError('cycle use cannot substitute hypothetical microscopic rates for unknown macro endpoints')
            if tuple(row.scenario for row in anchor.scenarios) != self.instance.scenarios:
                raise ValueError('cycle use drops adverse latent scenarios')
            for row in anchor.scenarios:
                sc = row.scenario
                needed = joint_necessities(parent_turnover=anchor.candidate.turnover_s_inv,
                    parent_specificity=anchor.candidate.specificity_dimensionless, target_turnover=anchor.reference[1],
                    target_specificity=anchor.reference[2], carbon_v=sc.carbon_v, carbon_u=sc.carbon_u, oxygen_u=sc.oxygen_u)
                if row.necessities != needed or row.irreversible_route_excluded != (
                        sc.carbon_u == 0 and sc.oxygen_u == 0 and needed.minimum_specificity_multiplier > 1):
                    raise ValueError('cycle use changes necessary constraints or irreversible exclusion')
                interval = finite_release_interval(sc, needed.minimum_turnover_multiplier, needed.minimum_specificity_multiplier)
                if ((row.minimum_release_multiplier, row.maximum_release_multiplier) != interval
                        or (interval[0] is not None) != needed.finite_release_can_meet_joint_targets):
                    raise ValueError('cycle use changes independent finite release interval')
                if tuple(value.response.release_multiplier for value in row.samples) != self.instance.release_multipliers:
                    raise ValueError('cycle use changes complete release sensitivity denominator')
                for value in row.samples:
                    response = common_release_response(carbon_v=sc.carbon_v, carbon_u=sc.carbon_u, oxygen_u=sc.oxygen_u,
                                                       release_multiplier=value.response.release_multiplier)
                    passed = (response.turnover_multiplier >= needed.minimum_turnover_multiplier
                              and response.specificity_multiplier >= needed.minimum_specificity_multiplier)
                    if value.response != response or value.joint_conditional_pass != passed:
                        raise ValueError('cycle use changes actual conditional response or joint endpoint decision')


@dataclass(frozen=True, slots=True)
class CycleOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-cycle-constraints/operation-config'
    config_id: str
    operation: str
    design: CycleDesign
    operands: tuple[ObjectIdentity, ...]
    successor: CycleInstanceInput | None = None
    reuse_successor: CycleInstanceInput | None = None

    def __post_init__(self):
        if self.operation not in {'supply', 'use', 'reuse'} or self.config_id != f'config.{NAMESPACE}.{self.operation}':
            raise ValueError('cycle operation/config identity substitution')
        require_sorted_unique_ids(self.operands, attribute='object_id', field_name='operands')
        from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import SourceAudit
        schemas = ((MechanismSourceAudit.SCHEMA,) if self.operation == 'supply' else
                   (CycleSupply.SCHEMA if self.operation == 'use' else CycleUseProduct.SCHEMA, SourceAudit.SCHEMA, CycleInstanceInput.SCHEMA))
        if (len(self.operands) != len(schemas) or sorted(row.object_schema for row in self.operands) != sorted(schemas)
                or (self.operation == 'supply' and self.operands != (self.design.source,))):
            raise ValueError('cycle config changes complete typed operand census or mechanism source')
        if self.reuse_successor is not None and (self.operation != 'supply' or self.successor is None):
            raise ValueError('cycle later query must follow an explicitly declared first supplier use')
