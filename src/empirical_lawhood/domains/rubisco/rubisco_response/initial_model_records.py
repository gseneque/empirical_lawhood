# SPDX-License-Identifier: MPL-2.0
"""A separately scoped, source-conditioned four-contrast model.

These records identify selected physical assumptions and supplied joint support.
They do not manufacture rate evidence, independent units or source authority.
The complete-rate supplier and its eight required rate roles remain unchanged.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext, validate_paired_chemical_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import RATIO_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import roster


CLOSURE = 'FOUR_STATE_SATURATING_CARBON_TURNOVER_AND_BRANCH_SPECIFICITY'
INTERPRETATION = 'SOURCE_CONDITIONED_EFFECTIVE_CONTRASTS_NOT_BIOLOGICAL_VALIDATION'
ENDPOINT_DEPENDENCIES = (('turnover', ('a', 'r_c')), ('specificity', ('c_over_o', 'chi_c_over_chi_o')))


@dataclass(frozen=True, slots=True)
class InitialSourceDocument(CanonicalRecord):
    """Exact public source or model text; text custody is not scientific support."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-source-document'
    source_id: str
    source_locator: str
    raw_utf8: str
    role: str

    def __post_init__(self):
        validate_stable_id(self.source_id)
        validate_nonempty(self.source_locator, field_name='source_locator')
        # Original source bytes commonly include a final newline or leading
        # indentation. Preserve them instead of requiring a trimmed rewrite.
        if type(self.raw_utf8) is not str or not self.raw_utf8.strip():
            raise ValueError('initial source text must contain original nonempty UTF-8 text')
        if self.role not in {'PUBLIC_SOURCE', 'MODEL_SPECIFICATION', 'RETAINED_SOURCE_ASSESSMENT'}:
            raise ValueError('initial source text cannot masquerade as a molecular contrast assessment')
        if len(self.raw_utf8.encode('utf-8')) > 512 * 1024:
            raise ValueError('initial source text exceeds its bounded document allocation')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.source_id, self)


def interval(values, *, positive=True):
    if type(values) is not tuple or len(values) != 2:
        raise ValueError('initial model requires both exact interval endpoints')
    for value in values:
        exact(value, Exact)
        if positive and value.fraction <= 0:
            raise ValueError('a missing contrast cannot become a zero or negative ratio')
    if values[0].fraction > values[1].fraction:
        raise ValueError('initial model reverses its interval endpoints')


@dataclass(frozen=True, slots=True)
class InitialContrastDependency(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-contrast-dependency'
    contrast: str
    inherited_evidence: tuple[ObjectIdentity, ...]
    transfer_assumptions: tuple[str, ...]
    targeted_quantities: tuple[str, ...]
    supplier_route: str
    applicability_limits: tuple[str, ...]
    native_unit: str = '1'

    def __post_init__(self):
        if self.contrast not in RATIO_ORDER or self.native_unit != '1':
            raise ValueError('initial model changes its four dimensionless contrast meanings')
        identities(self.inherited_evidence)
        for field in ('transfer_assumptions', 'targeted_quantities', 'applicability_limits'):
            require_sorted_unique_strings(getattr(self, field), field_name=field, allow_empty=False)
        validate_nonempty(self.supplier_route, field_name='supplier_route')


@dataclass(frozen=True, slots=True)
class InitialModelCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-model-case'
    case_id: str
    case: RubiscoPairedCase
    context: RubiscoAssayContext
    focal_site_id: str
    state_selection: ObjectIdentity
    expected_alternative_ids: tuple[str, ...]
    dependencies: tuple[InitialContrastDependency, ...]
    preparation_sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.case_id)
        validate_stable_id(self.focal_site_id)
        exact(self.case, RubiscoPairedCase)
        exact(self.context, RubiscoAssayContext)
        validate_paired_chemical_selection(self.case, self.context.chemistry)
        if self.focal_site_id not in {s.site_id for s in self.context.chemistry.sites}:
            raise ValueError('initial model substitutes its focal site')
        exact(self.state_selection, ObjectIdentity)
        require_sorted_unique_strings(self.expected_alternative_ids, field_name='expected_alternative_ids', allow_empty=False)
        for name in self.expected_alternative_ids:
            validate_stable_id(name)
        if type(self.dependencies) is not tuple or tuple(d.contrast for d in self.dependencies) != RATIO_ORDER:
            raise ValueError('initial model drops a required contrast from its dependency map')
        for row in self.dependencies:
            exact(row, InitialContrastDependency)
        identities(self.preparation_sources, allow_empty=True)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name='unresolved_requirement_ids')


@dataclass(frozen=True, slots=True)
class InitialModelSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-model-selection'
    selection_id: str
    protocol: ObjectIdentity
    cases: tuple[InitialModelCase, ...]
    closure_source: ObjectIdentity
    closure_assumptions: tuple[str, ...]
    source_evidence: tuple[ObjectIdentity, ...]
    maximum_analysis_bytes: int
    interpretation: str = INTERPRETATION
    closure: str = CLOSURE
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        for pin in (self.protocol, self.closure_source):
            exact(pin, ObjectIdentity)
        roster(self.cases, InitialModelCase, 'case_id')
        if len({c.case.identity for c in self.cases}) != len(self.cases):
            raise ValueError('initial model duplicates an original paired case')
        require_sorted_unique_strings(self.closure_assumptions, field_name='closure_assumptions', allow_empty=False)
        identities(self.source_evidence)
        required = {self.protocol, self.closure_source}
        for case in self.cases:
            required.update((case.state_selection, *case.preparation_sources))
            required.update(s for row in case.dependencies for s in row.inherited_evidence)
        if not required.issubset(self.source_evidence):
            raise ValueError('initial model loses a selected original source')
        if (type(self.maximum_analysis_bytes) is not int or not 0 < self.maximum_analysis_bytes <= 64 * 2**20
                or self.interpretation != INTERPRETATION or self.closure != CLOSURE
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError('initial model changes its bounded conditional evidence scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class InitialContrastEvidence(CanonicalRecord):
    """One sourced interval within a declared joint realization or enclosure.

An independent applicability review must support the *mutation contrast* in
the selected context. A paper, absolute WT rate, numerical check or imposed
invariance alone cannot discharge that requirement. The reader authenticates
the exact supplied review; it does not convert a review label into validation.
"""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-contrast-evidence'
    contrast: str
    bounds: tuple[Exact, Exact] | None
    evidence_kind: str
    sources: tuple[ObjectIdentity, ...]
    applicability_review: ObjectIdentity | None
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        if self.contrast not in RATIO_ORDER:
            raise ValueError('initial evidence changes its effective contrast')
        if self.evidence_kind not in {'SOURCE_CONDITIONED', 'COMPUTED', 'DERIVED_BOUND', 'IMPOSED_ASSUMPTION', 'UNIDENTIFIED', 'FAILED', 'DISCLOSED_CONTROL'}:
            raise ValueError('initial evidence loses its source interpretation')
        identities(self.sources, allow_empty=self.bounds is None)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name='unresolved_requirement_ids')
        if self.bounds is not None:
            interval(self.bounds)
        if self.applicability_review is not None:
            exact(self.applicability_review, ObjectIdentity)
            if self.applicability_review not in self.sources:
                raise ValueError('contrast review is absent from its original source closure')
        unavailable = self.evidence_kind in {'UNIDENTIFIED', 'FAILED'}
        if unavailable != (self.bounds is None):
            raise ValueError('missing or failed contrast cannot acquire supplied bounds')
        if (unavailable or self.evidence_kind in {'IMPOSED_ASSUMPTION', 'DISCLOSED_CONTROL'}
                or self.applicability_review is None) and not self.unresolved_requirement_ids:
            raise ValueError('unsupported contrast must retain its missing scientific requirement')

    @property
    def conditionally_supported(self):
        return (self.bounds is not None and self.evidence_kind in {'SOURCE_CONDITIONED', 'COMPUTED', 'DERIVED_BOUND'}
            and self.applicability_review is not None and not self.unresolved_requirement_ids)


@dataclass(frozen=True, slots=True)
class InitialContrastReview(CanonicalRecord):
    """Original scientific review of a particular sourced conditional interval.

The exact evidence, interpretation and applicable context remain inspectable.
This is a review record, not a synthetic signer, experimental authorization,
automatic verification of a physical model, or a source of new observations.
"""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-contrast-review'
    review_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    state_selection: ObjectIdentity
    contrast: str
    covered_bounds: tuple[Exact, Exact]
    supporting_sources: tuple[ObjectIdentity, ...]
    scientific_argument: str
    conditional_support: A
    unresolved_requirement_ids: tuple[str, ...]
    scope: str = 'ORIGINAL_REVIEW_OF_SELECTED_MUTATION_CONTRAST_WITH_DECLARED_TRANSFER_ASSUMPTIONS'

    def __post_init__(self):
        validate_stable_id(self.review_id)
        for pin in (self.case, self.context, self.state_selection):
            exact(pin, ObjectIdentity)
        if self.contrast not in RATIO_ORDER:
            raise ValueError('contrast review changes the selected physical quantity')
        interval(self.covered_bounds)
        identities(self.supporting_sources)
        validate_nonempty(self.scientific_argument, field_name='scientific_argument')
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name='unresolved_requirement_ids')
        if type(self.conditional_support) is not A:
            raise TypeError('contrast review needs its actual scientific finding')
        if (self.conditional_support is A.SATISFIED and self.unresolved_requirement_ids
                or self.conditional_support is not A.SATISFIED and not self.unresolved_requirement_ids
                or self.scope != 'ORIGINAL_REVIEW_OF_SELECTED_MUTATION_CONTRAST_WITH_DECLARED_TRANSFER_ASSUMPTIONS'):
            raise ValueError('contrast review cannot prune missing support or grant biological validity')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.review_id, self)


@dataclass(frozen=True, slots=True)
class InitialJointRealization(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-joint-realization'
    realization_id: str
    dependence_group_id: str
    joint_support_source: ObjectIdentity
    support_kind: str
    contrasts: tuple[InitialContrastEvidence, ...]
    wild_type_formation_wait_fraction: tuple[Exact, Exact]
    waiting_fraction_evidence: ObjectIdentity | None

    def __post_init__(self):
        for name in ('realization_id', 'dependence_group_id'):
            validate_stable_id(getattr(self, name))
        exact(self.joint_support_source, ObjectIdentity)
        if self.support_kind not in {'FIXED_JOINT_REALIZATION', 'JOINT_SAMPLE', 'JOINT_ENCLOSURE'}:
            raise ValueError('marginal intervals cannot become joint support or confidence coverage')
        if type(self.contrasts) is not tuple or tuple(c.contrast for c in self.contrasts) != RATIO_ORDER:
            raise ValueError('joint realization drops a required or missing contrast')
        for row in self.contrasts:
            exact(row, InitialContrastEvidence)
            if (self.support_kind != 'JOINT_ENCLOSURE' and row.bounds is not None
                    and row.bounds[0] != row.bounds[1]):
                raise ValueError('a joint point or sample cannot conceal an interval region')
        interval(self.wild_type_formation_wait_fraction, positive=False)
        low, high = (v.fraction for v in self.wild_type_formation_wait_fraction)
        if not 0 <= low <= high <= 1 or (low, high) in {(0, 0), (1, 1)}:
            raise ValueError('WT waiting enclosure must retain positive finite-rate meaning')
        if self.waiting_fraction_evidence is not None:
            exact(self.waiting_fraction_evidence, ObjectIdentity)
        if (low, high) != (0, 1) and self.waiting_fraction_evidence is None:
            raise ValueError('a narrowed WT waiting split needs its own evidence')


@dataclass(frozen=True, slots=True)
class InitialJointSupportReview(CanonicalRecord):
    """An original review of simultaneous support, never inferred from marginals."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-joint-support-review'
    review_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    state_selection: ObjectIdentity
    realization_id: str
    dependence_group_id: str
    support_kind: str
    covered_contrasts: tuple[tuple[Exact, Exact] | None, ...]
    waiting_fraction: tuple[Exact, Exact]
    supporting_sources: tuple[ObjectIdentity, ...]
    scientific_argument: str
    conditional_support: A
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        for name in ('review_id','realization_id','dependence_group_id'):
            validate_stable_id(getattr(self,name))
        for pin in (self.case,self.context,self.state_selection):
            exact(pin,ObjectIdentity)
        if self.support_kind not in {'FIXED_JOINT_REALIZATION','JOINT_SAMPLE','JOINT_ENCLOSURE'}:
            raise ValueError('joint review cannot turn marginal support into simultaneous coverage')
        if type(self.covered_contrasts) is not tuple or len(self.covered_contrasts)!=len(RATIO_ORDER):
            raise ValueError('joint review drops a supplied or missing contrast')
        for bounds in self.covered_contrasts:
            if bounds is not None:
                interval(bounds)
        interval(self.waiting_fraction,positive=False)
        if not 0<=self.waiting_fraction[0].fraction<=self.waiting_fraction[1].fraction<=1:
            raise ValueError('joint review changes its WT waiting allocation')
        identities(self.supporting_sources)
        validate_nonempty(self.scientific_argument,field_name='scientific_argument')
        require_sorted_unique_strings(self.unresolved_requirement_ids,field_name='unresolved_requirement_ids')
        if (type(self.conditional_support) is not A
                or self.conditional_support is A.SATISFIED and self.unresolved_requirement_ids
                or self.conditional_support is not A.SATISFIED and not self.unresolved_requirement_ids):
            raise ValueError('joint review prunes unavailable simultaneous support')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.review_id,self)


@dataclass(frozen=True, slots=True)
class InitialChemicalAlternative(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-chemical-alternative'
    alternative_id: str
    expected_realization_ids: tuple[str, ...]
    realizations: tuple[InitialJointRealization, ...]
    original_state: str
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.alternative_id)
        require_sorted_unique_strings(self.expected_realization_ids, field_name='expected_realization_ids')
        roster(self.realizations, InitialJointRealization, 'realization_id', allow_empty=True)
        if tuple(r.realization_id for r in self.realizations) != self.expected_realization_ids:
            raise ValueError('initial alternative prunes a failed, unknown or adverse joint realization')
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name='unresolved_requirement_ids')
        if self.original_state not in {'AVAILABLE', 'UNKNOWN', 'FAILED'}:
            raise ValueError('initial alternative changes its original completion state')
        if self.original_state != 'AVAILABLE' and (self.realizations or not self.unresolved_requirement_ids):
            raise ValueError('unavailable alternative must retain its requirements without invented realizations')
        if self.original_state == 'AVAILABLE' and not self.realizations:
            raise ValueError('available alternative needs its complete declared joint support')


@dataclass(frozen=True, slots=True)
class InitialCaseEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-case-evidence'
    case_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    state_selection: ObjectIdentity
    alternatives: tuple[InitialChemicalAlternative, ...]

    def __post_init__(self):
        validate_stable_id(self.case_id)
        for value in (self.case, self.context, self.state_selection):
            exact(value, ObjectIdentity)
        roster(self.alternatives, InitialChemicalAlternative, 'alternative_id')


@dataclass(frozen=True, slots=True)
class InitialModelEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-model-evidence'
    evidence_id: str
    selection: ObjectIdentity
    cases: tuple[InitialCaseEvidence, ...]
    interpretation: str = INTERPRETATION

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        exact(self.selection, ObjectIdentity)
        if (self.selection.object_schema, self.selection.object_version) != (InitialModelSelection.SCHEMA, InitialModelSelection.VERSION):
            raise ValueError('initial evidence changes its selected model schema or revision')
        roster(self.cases, InitialCaseEvidence, 'case_id')
        if self.interpretation != INTERPRETATION:
            raise ValueError('initial evidence cannot become biological validation')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)


def validate_initial_model_inputs(selection, evidence):
    exact(selection, InitialModelSelection)
    exact(evidence, InitialModelEvidence)
    if evidence.selection != selection.identity or tuple(c.case_id for c in evidence.cases) != tuple(c.case_id for c in selection.cases):
        raise ValueError('initial evidence changes the selected model or complete paired-case census')
    for case, supplied in zip(selection.cases, evidence.cases, strict=True):
        if ((supplied.case, supplied.context, supplied.state_selection) != (case.case.identity, case.context.identity, case.state_selection)
                or tuple(a.alternative_id for a in supplied.alternatives) != case.expected_alternative_ids):
            raise ValueError('initial evidence changes a material, assay, preparation or chemical alternative')
        if case.case.case_role == 'NO_CHANGE':
            for alternative in supplied.alternatives:
                for realization in alternative.realizations:
                    if any(c.bounds is not None and not c.bounds[0].fraction <= 1 <= c.bounds[1].fraction for c in realization.contrasts):
                        raise ValueError('no-change initial model excludes the identity contrast')
    if selection.canonical_size_bytes() + evidence.canonical_size_bytes() > selection.maximum_analysis_bytes:
        raise ValueError('initial model exceeds its declared complete analysis allocation')
