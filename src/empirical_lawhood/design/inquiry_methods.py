# SPDX-License-Identifier: MPL-2.0
"""Explicit author and dependent-assessment operands for registered domain methods.

These immutable records grant no access, independence, execution or qualification.
The selected domain validates original source membership and the scientific joins
through the existing recursive scientific and inquiry hooks.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.experiments.experimental_design import UnitAllocation
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ScientificConditionScope, ScientificRequirementSpec
from empirical_lawhood.science.identity.references import NamedDecimal, QuantityBound
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.science.models.time import AvailabilitySpec, CausalPhase, ClockCoordinate, InformationCutoff

from empirical_lawhood.design.response_algebra import MultiplicitySpec
from empirical_lawhood.design.study_authoring import CapabilitySelection


PREFIX = "empirical-lawhood/planning/inquiry-methods"
MAX_OPPORTUNITIES = 256
MAX_UNITS = 32
MAX_INPUTS = 32


def _typed(value, kind):
    if type(value) is not kind:
        raise TypeError("inquiry method requires exact " + kind.__name__)
    value.__post_init__()


def _identities(values, *, label, maximum=MAX_INPUTS):
    if type(values) is not tuple or len(values) > maximum:
        raise ValueError(label + " exceeds its explicit tuple bound")
    for value in values:
        _typed(value, ObjectIdentity)
    require_sorted_unique_ids(values, attribute="object_id", field_name=label)


def _cutoff(value):
    _typed(value, InformationCutoff)
    if value.coordinate is None:
        raise ValueError("inquiry method requires an exact finite cutoff coordinate")


class InquiryAuthoringMode(StrEnum):
    INVESTIGATOR_RECIPE = "INVESTIGATOR_RECIPE"
    INTERNAL_SELECTION = "INTERNAL_SELECTION"
    INTERNAL_SPECIFICATION = "INTERNAL_SPECIFICATION"
    PROCEDURE_CONSTRUCTION = "PROCEDURE_CONSTRUCTION"


class InquiryEvidenceRole(StrEnum):
    ACTOR_INPUT = "ACTOR_INPUT"
    EVALUATOR_DIAGNOSTIC = "EVALUATOR_DIAGNOSTIC"
    AUTHORIZED_LATER_RELEASE = "AUTHORIZED_LATER_RELEASE"


@dataclass(frozen=True, slots=True)
class InquiryMethodEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/evidence"
    record: ObjectIdentity
    role: InquiryEvidenceRole
    availability: AvailabilitySpec
    release: ObjectIdentity | None = None

    def __post_init__(self):
        _typed(self.record, ObjectIdentity)
        _typed(self.availability, AvailabilitySpec)
        if type(self.role) is not InquiryEvidenceRole or self.availability.available_at is None:
            raise ValueError("method evidence requires an explicit role and actual availability time")
        if self.role is InquiryEvidenceRole.AUTHORIZED_LATER_RELEASE:
            _typed(self.release, ObjectIdentity)
        elif self.release is not None:
            raise ValueError("only a later-release input can name a release record")

    @property
    def evidence_id(self):
        return self.record.object_id


def require_actor_evidence(evidence, cutoff):
    """Check declared causality; the application must still authenticate live access."""
    _typed(evidence, InquiryMethodEvidence)
    _cutoff(cutoff)
    availability = evidence.availability
    if (evidence.role is InquiryEvidenceRole.EVALUATOR_DIAGNOSTIC
            or availability.outcome_access not in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.DEVELOPMENT_VISIBLE)
            or not cutoff.allows(availability)
            or availability.available_at > cutoff.coordinate
            or (availability.available_at == cutoff.coordinate and not cutoff.includes_coordinate)):
        raise ValueError("author input violates its actor role, actual cutoff or evidence access")


@dataclass(frozen=True, slots=True)
class FrozenInquiryConsumer(CanonicalRecord):
    """Exact consumer plus a code-owned parameter rule, not current admission."""

    SCHEMA: ClassVar[str] = PREFIX + "/frozen-consumer"
    consumer: ObjectIdentity
    parameter_rule: ObjectIdentity
    parameter_bounds: tuple[QuantityBound, ...]

    def __post_init__(self):
        _typed(self.consumer, ObjectIdentity)
        _typed(self.parameter_rule, ObjectIdentity)
        if type(self.parameter_bounds) is not tuple or len(self.parameter_bounds) > 16:
            raise ValueError("consumer parameter bounds exceed the explicit sixteen-coordinate limit")
        for bound in self.parameter_bounds:
            _typed(bound, QuantityBound)
            if bound.lower is None or bound.upper is None:
                raise ValueError("permitted parameters need two finite bounds")
        require_sorted_unique_ids(self.parameter_bounds, attribute="quantity_id", field_name="parameter_bounds")

    def require_parameters(self, parameters):
        if (type(parameters) is not tuple or any(type(p) is not NamedDecimal for p in parameters)
                or tuple(p.value_id for p in parameters) != tuple(b.quantity_id for b in self.parameter_bounds)):
            raise ValueError("consumer parameters change the complete permitted coordinate census")
        for parameter, bound in zip(parameters, self.parameter_bounds, strict=True):
            parameter.__post_init__()
            if parameter.unit != bound.native_unit or not bound.lower <= parameter.value <= bound.upper:
                raise ValueError("consumer parameter violates its original units or permitted rule")


@dataclass(frozen=True, slots=True)
class InquiryAuthorContract(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/author-contract"
    contract_id: str
    mode: InquiryAuthoringMode
    author: CapabilitySelection
    output_specification: ObjectIdentity
    method_family_id: str
    permitted_methods: tuple[CapabilitySelection, ...]
    maximum_composed_operations: int
    missing_conditions: tuple[ObjectIdentity, ...]
    inputs: tuple[InquiryMethodEvidence, ...]
    cutoff: InformationCutoff
    activation: ClockCoordinate
    activation_phase: CausalPhase
    frozen_consumer: FrozenInquiryConsumer

    def __post_init__(self):
        validate_stable_id(self.contract_id)
        validate_stable_id(self.method_family_id)
        if type(self.mode) is not InquiryAuthoringMode:
            raise TypeError("authoring mode must distinguish recipe, selection, specification and construction")
        _typed(self.author, CapabilitySelection)
        _typed(self.output_specification, ObjectIdentity)
        _typed(self.frozen_consumer, FrozenInquiryConsumer)
        if (type(self.permitted_methods) is not tuple or not 1 <= len(self.permitted_methods) <= 16
                or type(self.maximum_composed_operations) is not int
                or not 1 <= self.maximum_composed_operations <= 16):
            raise ValueError("author method family needs explicit finite composition bounds")
        for method in self.permitted_methods:
            _typed(method, CapabilitySelection)
        require_sorted_unique_ids(self.permitted_methods, attribute="selection_id", field_name="permitted_methods")
        _identities(self.missing_conditions, label="missing_conditions")
        if any(p.object_schema != ScientificRequirementSpec.SCHEMA for p in self.missing_conditions):
            raise ValueError("author hypotheses must retain their exact missing scientific requirements")
        if type(self.inputs) is not tuple or not 1 <= len(self.inputs) <= MAX_INPUTS:
            raise ValueError("author input census must be explicit and bounded")
        require_sorted_unique_ids(self.inputs, attribute="evidence_id", field_name="inputs")
        _cutoff(self.cutoff)
        for evidence in self.inputs:
            require_actor_evidence(evidence, self.cutoff)
        _typed(self.activation, ClockCoordinate)
        if (type(self.activation_phase) is not CausalPhase
                or self.activation.clock_id != self.cutoff.clock_id
                or self.activation.coordinate < self.cutoff.coordinate
                or not self.cutoff.phase.precedes_or_equals(self.activation_phase)):
            raise ValueError("activation cannot precede its author cutoff or silently change clocks")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.contract_id, self)


@dataclass(frozen=True, slots=True)
class FrozenInquiryProcedure(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/frozen-procedure"
    procedure_id: str
    author_contract: InquiryAuthorContract
    selected_methods: tuple[CapabilitySelection, ...]
    parameters: tuple[NamedDecimal, ...]

    def __post_init__(self):
        validate_stable_id(self.procedure_id)
        _typed(self.author_contract, InquiryAuthorContract)
        if (type(self.selected_methods) is not tuple
                or not 1 <= len(self.selected_methods) <= self.author_contract.maximum_composed_operations
                or any(method not in self.author_contract.permitted_methods for method in self.selected_methods)):
            raise ValueError("procedure changes its permitted method family or composition bound")
        self.author_contract.frozen_consumer.require_parameters(self.parameters)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.procedure_id, self)


@dataclass(frozen=True, slots=True)
class AssignedInquiryOpportunity(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/assigned-opportunity"
    opportunity_id: str
    dependence_root: ObjectIdentity
    independent_unit_id: str
    nested_view_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.opportunity_id)
        validate_stable_id(self.independent_unit_id)
        _typed(self.dependence_root, ObjectIdentity)
        require_sorted_unique_strings(self.nested_view_ids, field_name="nested_view_ids")
        if len(self.nested_view_ids) > 16 or self.independent_unit_id in self.nested_view_ids:
            raise ValueError("nested views cannot become independent units")


@dataclass(frozen=True, slots=True)
class FixedOpportunityStopping(CanonicalRecord):
    """A fixed assigned census; interruption retains all unobserved assignments."""

    SCHEMA: ClassVar[str] = PREFIX + "/fixed-stopping"
    stopping_id: str
    opportunity_ids: tuple[str, ...]
    assessment_cutoff: InformationCutoff
    rule: str = "FIXED_ASSIGNED_CENSUS_NO_OUTCOME_STOPPING"

    def __post_init__(self):
        validate_stable_id(self.stopping_id)
        require_sorted_unique_strings(self.opportunity_ids, field_name="opportunity_ids", allow_empty=False)
        if len(self.opportunity_ids) > MAX_OPPORTUNITIES or self.rule != "FIXED_ASSIGNED_CENSUS_NO_OUTCOME_STOPPING":
            raise ValueError("fixed opportunity stopping cannot select outcomes or exceed its census limit")
        _cutoff(self.assessment_cutoff)


class MissingOpportunityRule(StrEnum):
    RETAIN_OUTCOME_BOUNDS = "RETAIN_OUTCOME_BOUNDS"
    UNEVALUABLE = "UNEVALUABLE"


@dataclass(frozen=True, slots=True)
class DependentAssessmentContract(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/dependent-assessment"
    contract_id: str
    method: CapabilitySelection
    estimand: ObjectIdentity
    scope: ScientificConditionScope
    outcome_bound: QuantityBound
    allocation: UnitAllocation
    opportunities: tuple[AssignedInquiryOpportunity, ...]
    inputs: tuple[InquiryMethodEvidence, ...]
    stopping: FixedOpportunityStopping
    multiplicity: MultiplicitySpec
    missingness: MissingOpportunityRule
    frozen_consumer: FrozenInquiryConsumer

    def __post_init__(self):
        validate_stable_id(self.contract_id)
        for value, kind in ((self.method, CapabilitySelection), (self.estimand, ObjectIdentity),
                            (self.scope, ScientificConditionScope), (self.outcome_bound, QuantityBound),
                            (self.allocation, UnitAllocation), (self.stopping, FixedOpportunityStopping),
                            (self.multiplicity, MultiplicitySpec), (self.frozen_consumer, FrozenInquiryConsumer)):
            _typed(value, kind)
        if (type(self.missingness) is not MissingOpportunityRule
                or self.outcome_bound.lower is None or self.outcome_bound.upper is None
                or (self.outcome_bound.quantity_id, self.outcome_bound.native_unit)
                not in zip(self.scope.quantity_ids, self.scope.native_units, strict=True)
                or self.scope.information_cutoff != self.stopping.assessment_cutoff
                or self.scope.clock_id != self.stopping.assessment_cutoff.clock_id):
            raise ValueError("assessment changes outcome units, exact cutoff or missingness rule")
        if len(self.allocation.units) > MAX_UNITS:
            raise ValueError("assessment exceeds its thirty-two independent-unit limit")
        if (type(self.opportunities) is not tuple
                or tuple(o.opportunity_id for o in self.opportunities) != self.stopping.opportunity_ids):
            raise ValueError("assessment must retain every assigned opportunity exactly once")
        roots, used_units = {}, set()
        for opportunity in self.opportunities:
            _typed(opportunity, AssignedInquiryOpportunity)
            unit = self.allocation.unit(opportunity.independent_unit_id)
            if unit is None or not set(opportunity.nested_view_ids).issubset(unit.numerical_view_ids):
                raise ValueError("opportunity substitutes its independent unit or nested views")
            root = opportunity.dependence_root
            content_key = (root.object_schema, root.object_version, root.object_fingerprint)
            previous = roots.setdefault(content_key, opportunity.independent_unit_id)
            if previous != opportunity.independent_unit_id:
                raise ValueError("one dependence root cannot become several independent units through labels")
            used_units.add(opportunity.independent_unit_id)
        if used_units != set(self.allocation.unit_ids()):
            raise ValueError("opportunity assignment must preserve the complete allocation denominator")
        if type(self.inputs) is not tuple or not 1 <= len(self.inputs) <= MAX_INPUTS:
            raise ValueError("assessment requires a bounded exact evidence census")
        require_sorted_unique_ids(self.inputs, attribute="evidence_id", field_name="inputs")
        for evidence in self.inputs:
            _typed(evidence, InquiryMethodEvidence)
            cutoff = self.stopping.assessment_cutoff
            availability = evidence.availability
            if (availability.clock_id != cutoff.clock_id
                    or not availability.phase.precedes_or_equals(cutoff.phase)
                    or availability.available_at > cutoff.coordinate
                    or (availability.available_at == cutoff.coordinate and not cutoff.includes_coordinate)):
                raise ValueError("assessment input lies beyond its actual observation cutoff")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.contract_id, self)

    def require_procedure(self, procedure):
        _typed(procedure, FrozenInquiryProcedure)
        if self.frozen_consumer != procedure.author_contract.frozen_consumer:
            raise ValueError("unchanged-package assessment substitutes the frozen consumer or parameter rule")
        if (procedure.author_contract.activation.clock_id != self.scope.clock_id
                or procedure.author_contract.activation.coordinate > self.stopping.assessment_cutoff.coordinate):
            raise ValueError("procedure was not active at the declared assessment boundary")
