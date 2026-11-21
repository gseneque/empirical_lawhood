# SPDX-License-Identifier: MPL-2.0
"""Separate joint decisions over the original conditional initial model.

The request keeps the original material, evidence and positive-ratio contracts.
Domain limitations describe unresolved inputs; they never supply physical data.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, ScientificConditionScope
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialContrastReview, InitialJointSupportReview, InitialModelEvidence, InitialModelSelection, interval
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import RATIO_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import roster


OUTCOMES = ('SUPPORTED', 'CONTRADICTED', 'UNRESOLVED')
POLICIES = ('UNIFORM_PHYSICAL_CONCLUSION', 'ROBUST_FOR_EVERY_SELECTED_ALTERNATIVE')
CRITERIA = ('FAVOURABLE', 'ADVERSE', 'INCONCLUSIVE', 'UNEVALUABLE')
SCOPE = 'CONDITIONAL_INITIAL_MODEL_JOINT_DECISION_NOT_BIOLOGICAL_VALIDATION'


def _identity(pin, kind):
    exact(pin, ObjectIdentity)
    if (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError('initial root substitutes its exact selected record revision')


def _outcome(value):
    if value not in OUTCOMES:
        raise ValueError('initial root requires a supported, contradicted or unresolved outcome')


@dataclass(frozen=True, slots=True)
class InitialRootDomainLimit(CanonicalRecord):
    """An explicit input-domain stop outside the existing positive ratio model."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-domain-limit'
    case_id: str
    alternative_id: str
    contrast: str
    reason: str
    requirement_id: str
    original_source: ObjectIdentity | None = None

    def __post_init__(self):
        for name in ('case_id', 'alternative_id', 'requirement_id'):
            validate_stable_id(getattr(self, name))
        if self.contrast not in RATIO_ORDER or self.reason not in {
                'ZERO_MUTANT_RATE', 'ABSENT_CHANNEL', 'ZERO_WT_REFERENCE', 'UNDEFINED_EFFECTIVE_RATIO'}:
            raise ValueError('initial root domain limit must name its actual unresolved ratio domain')
        if self.original_source is not None:
            exact(self.original_source, ObjectIdentity)


@dataclass(frozen=True, slots=True)
class InitialRootRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-request'
    request_id: str
    model: ObjectIdentity
    alternative_policy: str
    processing_policy: str
    domain_limits: tuple[InitialRootDomainLimit, ...] = ()
    turnover_criterion: str = 'STRICTLY_GREATER_THAN_ONE'
    specificity_criterion: str = 'GREATER_THAN_OR_EQUAL_TO_ONE'
    uncertainty_policy: str = 'ORIGINAL_SIMULTANEOUS_SUPPORT_NO_SAMPLE_COVERAGE_PROMOTION'
    closure_policy: str = 'RETAIN_ORIGINAL_APPLICABILITY_REQUIREMENTS'
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.request_id)
        _identity(self.model, InitialModelSelection)
        if self.alternative_policy not in POLICIES or self.processing_policy not in POLICIES:
            raise ValueError('initial root requires explicit alternative and processing quantifiers')
        if type(self.domain_limits) is not tuple:
            raise TypeError('initial root domain limits must be an immutable complete selection')
        keys = []
        for row in self.domain_limits:
            exact(row, InitialRootDomainLimit)
            keys.append((row.case_id, row.alternative_id, row.contrast))
        if keys != sorted(set(keys)):
            raise ValueError('initial root repeats or reorders an input-domain limitation')
        if (self.turnover_criterion != 'STRICTLY_GREATER_THAN_ONE'
                or self.specificity_criterion != 'GREATER_THAN_OR_EQUAL_TO_ONE'
                or self.uncertainty_policy != 'ORIGINAL_SIMULTANEOUS_SUPPORT_NO_SAMPLE_COVERAGE_PROMOTION'
                or self.closure_policy != 'RETAIN_ORIGINAL_APPLICABILITY_REQUIREMENTS'
                or self.scope != SCOPE):
            raise ValueError('initial root changes the owner criterion, evidence ceiling or original applicability')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.request_id, self)


@dataclass(frozen=True, slots=True)
class InitialRootReviewInputs(CanonicalRecord):
    """Frozen original review bytes for an exposed calculation, never authority.

    The public capture service reads these through every original publication
    guard. Subsequent ordinary execution freezes this exact input as it does
    other exposed source records. Original custody is independently readable.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-review-inputs'
    model: ObjectIdentity
    inputs: ObjectIdentity
    original_sources: tuple[ObjectIdentity, ...]
    contrast_reviews: tuple[InitialContrastReview, ...]
    joint_reviews: tuple[InitialJointSupportReview, ...]
    scope: str = 'FROZEN_EXPOSED_SOURCE_CONDITIONED_REVIEW_DATA_NOT_AUTHORITY'

    def __post_init__(self):
        _identity(self.model, InitialModelSelection)
        _identity(self.inputs, InitialModelEvidence)
        identities(self.original_sources)
        roster(self.contrast_reviews, InitialContrastReview, 'review_id', allow_empty=True)
        roster(self.joint_reviews, InitialJointSupportReview, 'review_id', allow_empty=True)
        expected = tuple(pin for pin in self.original_sources if pin.object_schema in
            (InitialContrastReview.SCHEMA, InitialJointSupportReview.SCHEMA))
        actual = tuple(sorted((row.identity for row in (*self.contrast_reviews, *self.joint_reviews)), key=lambda pin: pin.object_id))
        if expected != actual or any(not set(row.supporting_sources).issubset(self.original_sources)
                for row in (*self.contrast_reviews, *self.joint_reviews)):
            raise ValueError('initial root review inputs change exact original reviews or supporting sources')
        if self.scope != 'FROZEN_EXPOSED_SOURCE_CONDITIONED_REVIEW_DATA_NOT_AUTHORITY':
            raise ValueError('initial root review inputs cannot grant current source access or qualification')

    @property
    def identity(self):
        return ObjectIdentity.from_record('initial-root-reviews.' + self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class InitialRootAnalysisInputs(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-analysis-inputs'
    request: InitialRootRequest
    model: InitialModelSelection
    inputs: InitialModelEvidence
    reviews: InitialRootReviewInputs

    def __post_init__(self):
        from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import required_initial_sources
        for value, kind in ((self.request, InitialRootRequest), (self.model, InitialModelSelection),
                (self.inputs, InitialModelEvidence), (self.reviews, InitialRootReviewInputs)):
            exact(value, kind)
        if (self.request.model != self.model.identity
                or (self.reviews.model, self.reviews.inputs) != (self.model.identity, self.inputs.identity)
                or self.reviews.original_sources != required_initial_sources(self.model, self.inputs)):
            raise ValueError('initial root analysis changes its exact source, consumer or complete review census')

    @property
    def identity(self):
        return ObjectIdentity.from_record('initial-root-analysis.' + self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class InitialWaitingCondition(CanonicalRecord):
    """An exact sufficient inequality in the actual WT waiting fraction."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-waiting-condition'
    formation_ratio: Exact
    processing_ratio: Exact
    coefficient: Exact
    right_hand_side: Exact
    comparison: str
    equivalent_relation: str
    threshold: Exact | None

    def __post_init__(self):
        for name in ('formation_ratio', 'processing_ratio', 'coefficient', 'right_hand_side'):
            exact(getattr(self, name), Exact)
        if min(self.formation_ratio.fraction, self.processing_ratio.fraction) <= 0:
            raise ValueError('waiting condition cannot divide by a zero or undefined rate ratio')
        if self.comparison not in ('LT', 'GE') or self.equivalent_relation not in ('LT', 'GT', 'LE', 'GE', 'ALL', 'NONE'):
            raise ValueError('waiting condition changes its exact strict or inclusive inequality')
        if (self.equivalent_relation in ('ALL', 'NONE')) != (self.threshold is None):
            raise ValueError('waiting condition loses its threshold or constant disposition')
        if self.threshold is not None:
            exact(self.threshold, Exact)


@dataclass(frozen=True, slots=True)
class InitialRootEndpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-endpoint'
    endpoint: str
    ratio_bounds: tuple[Exact, Exact] | None
    arithmetic_criterion: str
    conditional_criterion: str
    remaining_requirement_ids: tuple[str, ...]
    balance_residuals: tuple[Exact, ...]

    def __post_init__(self):
        if self.endpoint not in ('turnover', 'specificity'):
            raise ValueError('initial root changes the two selected endpoints')
        if self.ratio_bounds is not None:
            interval(self.ratio_bounds)
        if self.arithmetic_criterion not in CRITERIA or self.conditional_criterion not in CRITERIA:
            raise ValueError('initial root changes an original endpoint disposition')
        require_sorted_unique_strings(self.remaining_requirement_ids, field_name='remaining_requirement_ids')
        if type(self.balance_residuals) is not tuple:
            raise TypeError('endpoint balances must retain their exact immutable residuals')
        for row in self.balance_residuals:
            exact(row, Exact)


@dataclass(frozen=True, slots=True)
class InitialRootRealization(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-realization'
    realization_id: str
    dependence_group_id: str
    support_kind: str
    endpoints: tuple[InitialRootEndpoint, ...]
    joint_outcome: str
    diagnostic_joint_outcome: str
    decisive_endpoints: tuple[str, ...]
    support_waiting_condition: InitialWaitingCondition | None
    contradiction_waiting_condition: InitialWaitingCondition | None
    omitted_operands: tuple[str, ...]
    decision_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.realization_id)
        validate_stable_id(self.dependence_group_id)
        if self.support_kind not in ('FIXED_JOINT_REALIZATION', 'JOINT_SAMPLE', 'JOINT_ENCLOSURE'):
            raise ValueError('initial root changes its original joint support kind')
        if type(self.endpoints) is not tuple or tuple(row.endpoint for row in self.endpoints) != ('turnover', 'specificity'):
            raise ValueError('initial root drops or reorders an endpoint')
        for row in self.endpoints:
            exact(row, InitialRootEndpoint)
        _outcome(self.joint_outcome)
        _outcome(self.diagnostic_joint_outcome)
        for name in ('decisive_endpoints', 'omitted_operands', 'decision_requirement_ids'):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if not set(self.decisive_endpoints).issubset({'turnover', 'specificity'}):
            raise ValueError('initial root invents a decisive endpoint')
        for condition in (self.support_waiting_condition, self.contradiction_waiting_condition):
            if condition is not None:
                exact(condition, InitialWaitingCondition)


@dataclass(frozen=True, slots=True)
class InitialRootAlternative(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-alternative'
    alternative_id: str
    original_state: str
    realizations: tuple[InitialRootRealization, ...]
    joint_outcome: str
    decision_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.alternative_id)
        if self.original_state not in ('AVAILABLE', 'UNKNOWN', 'FAILED'):
            raise ValueError('initial root changes an original alternative state')
        roster(self.realizations, InitialRootRealization, 'realization_id', allow_empty=True)
        _outcome(self.joint_outcome)
        require_sorted_unique_strings(self.decision_requirement_ids, field_name='decision_requirement_ids')


@dataclass(frozen=True, slots=True)
class InitialRootCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-case'
    case_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    state_selection: ObjectIdentity
    processing_view: str
    alternatives: tuple[InitialRootAlternative, ...]
    joint_outcome: str
    decision_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.case_id)
        for pin in (self.case, self.context, self.state_selection):
            exact(pin, ObjectIdentity)
        validate_stable_id(self.processing_view)
        roster(self.alternatives, InitialRootAlternative, 'alternative_id')
        _outcome(self.joint_outcome)
        require_sorted_unique_strings(self.decision_requirement_ids, field_name='decision_requirement_ids')


@dataclass(frozen=True, slots=True)
class InitialRootResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-result'
    result_id: str
    request: ObjectIdentity
    model: ObjectIdentity
    inputs: ObjectIdentity
    cases: tuple[InitialRootCase, ...]
    joint_outcome: str
    decision_requirement_ids: tuple[str, ...]
    original_remaining_requirement_ids: tuple[str, ...]
    scope: str = SCOPE
    new_native_calls: int = 0
    independent_biological_units: int = 0
    biological_predictive_validity: str = 'UNEVALUABLE'

    def __post_init__(self):
        validate_stable_id(self.result_id)
        for pin, kind in ((self.request, InitialRootRequest), (self.model, InitialModelSelection), (self.inputs, InitialModelEvidence)):
            _identity(pin, kind)
        roster(self.cases, InitialRootCase, 'case_id')
        _outcome(self.joint_outcome)
        for name in ('decision_requirement_ids', 'original_remaining_requirement_ids'):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if (self.scope != SCOPE or type(self.new_native_calls) is not int or self.new_native_calls != 0
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0
                or self.biological_predictive_validity != 'UNEVALUABLE'):
            raise ValueError('initial root cannot manufacture native work, biological units or predictive validity')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


@dataclass(frozen=True, slots=True)
class InitialRootAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-assessment'
    assessment_id: str
    request: ObjectIdentity
    result: ObjectIdentity
    numerical_disposition: AssessmentDisposition
    joint_outcome: str
    findings: tuple[str, ...]
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        _identity(self.request, InitialRootRequest)
        _identity(self.result, InitialRootResult)
        if self.numerical_disposition not in (AssessmentDisposition.SATISFIED, AssessmentDisposition.FALSIFIED):
            raise ValueError('initial root numerical assessment requires an actual checked disposition')
        _outcome(self.joint_outcome)
        require_sorted_unique_strings(self.findings, field_name='findings')
        if ((self.numerical_disposition is AssessmentDisposition.SATISFIED) != (not self.findings)
                or self.scope != SCOPE):
            raise ValueError('initial root assessment hides a failed check or changes scientific scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


@dataclass(frozen=True, slots=True)
class InitialRootScopedResult(CanonicalRecord):
    """Recursive transport with typed scope; original closed result stays unchanged."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-scoped-result'
    analysis: ObjectIdentity
    scope: ScientificConditionScope
    result: InitialRootResult

    def __post_init__(self):
        _identity(self.analysis, InitialRootAnalysisInputs)
        exact(self.scope, ScientificConditionScope)
        exact(self.result, InitialRootResult)
        if (self.scope.source_config_sha256 != self.analysis.object_fingerprint
                or self.scope.instance_id != self.result.request.object_id
                or self.scope.system_id != self.result.model.object_id
                or self.scope.uncertainty_contract != self.result.request):
            raise ValueError('recursive root result changes its complete original analysis or consumer scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record('initial-root-scoped-result.' + self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class InitialRootScopedAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-scoped-assessment'
    analysis: ObjectIdentity
    scope: ScientificConditionScope
    assessment: InitialRootAssessment

    def __post_init__(self):
        _identity(self.analysis, InitialRootAnalysisInputs)
        exact(self.scope, ScientificConditionScope)
        exact(self.assessment, InitialRootAssessment)
        if (self.scope.source_config_sha256 != self.analysis.object_fingerprint
                or self.scope.instance_id != self.assessment.request.object_id
                or self.scope.uncertainty_contract != self.assessment.request):
            raise ValueError('recursive root assessment changes its complete original analysis or consumer scope')

    @property
    def request(self):
        return self.assessment.request

    @property
    def numerical_disposition(self):
        return self.assessment.numerical_disposition

    @property
    def findings(self):
        return self.assessment.findings

    @property
    def joint_outcome(self):
        return self.assessment.joint_outcome

    @property
    def identity(self):
        return ObjectIdentity.from_record('initial-root-scoped-assessment.' + self.fingerprint(), self)
