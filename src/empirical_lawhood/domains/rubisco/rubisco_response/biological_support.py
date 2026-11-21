# SPDX-License-Identifier: MPL-2.0
"""Independent construct, assay, anchoring and predictive-support assessment.

This reader consumes retained exposed sources. A fresh eligible validation
package needs its own source, allocation, cutoff and current-access assessment;
changing a field on an exposed record cannot supply those facts.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_portfolio_inquiry.science import Candidate
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import EndpointValues
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.acceptance import ResponseAcceptance
from empirical_lawhood.domains.rubisco.rubisco_response.biological_sources import ExposedBiologicalSources
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext, validate_paired_chemical_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, RubiscoPairedCase, exact


@dataclass(frozen=True, slots=True)
class BiologicalAnchorUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/biological-anchor-use"
    source: ObjectIdentity
    values: EndpointValues

    def __post_init__(self):
        exact(self.source, ObjectIdentity)
        exact(self.values, EndpointValues)


@dataclass(frozen=True, slots=True)
class BiologicalSupportSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/biological-support-selection"
    selection_id: str
    cases: RubiscoCaseSet
    acceptance: ResponseAcceptance
    contexts: tuple[RubiscoAssayContext | None, ...]
    anchor_uses: tuple[tuple[BiologicalAnchorUse, ...], ...]

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.cases, RubiscoCaseSet)
        exact(self.acceptance, ResponseAcceptance)
        if (type(self.contexts) is not tuple or type(self.anchor_uses) is not tuple
                or len(self.contexts) != len(self.cases.cases) or len(self.anchor_uses) != len(self.cases.cases)):
            raise ValueError("biological selection must retain every case, context and anchor use")
        for case, context, uses in zip(self.cases.cases, self.contexts, self.anchor_uses, strict=True):
            if context is not None:
                exact(context, RubiscoAssayContext)
                validate_paired_chemical_selection(case, context.chemistry)
            if type(uses) is not tuple or len(uses) > 256:
                raise ValueError("anchor uses require a bounded complete tuple")
            for use in uses:
                exact(use, BiologicalAnchorUse)
        requirements = self.acceptance.predictive_evidence_requirement_ids + (self.acceptance.gp_applicability_requirement_id,)
        if len(set(requirements)) != len(requirements):
            raise ValueError("predictive validation and Gp applicability must remain distinct requirements")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def selection_from_study(study):
    from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
    exact(study, RubiscoResponseStudy)
    return BiologicalSupportSelection("biology.selection." + study.fingerprint()[:24], study.cases, study.acceptance,
        tuple(supply.context for supply in study.supplies),
        tuple(tuple(BiologicalAnchorUse(point.anchor_source, point.anchor_wild_type)
            for scenario in supply.scenarios for point in scenario.points if point.anchor_wild_type is not None)
            for supply in study.supplies))


def _material_rows(material, sources):
    if sources is None:
        return ()
    lsu = {row.sequence for row in material.chains if row.subunit == "LSU"}
    ssu = {row.sequence for row in material.chains if row.subunit == "SSU"}
    if len(lsu) != 1 or len(ssu) != 1:
        return ()
    # Exact sequences establish a source-recipe join, never actual processing or assembly.
    return tuple(row for row in sources.candidates if row.lsu_sequence in lsu
        and any(sequence in ssu for _, sequence in row.ssu_sequence_views))


def _ratios(parent, mutant):
    if parent is None or mutant is None:
        return None
    pairs = ((parent.turnover_s_inv, mutant.turnover_s_inv),
             (parent.specificity_dimensionless, mutant.specificity_dimensionless))
    if any(left is None or right is None for left, right in pairs):
        return None
    return tuple(Exact.of(Fraction(right) / Fraction(left)) for left, right in pairs)


def _assay_flags(context, row):
    if row is None:
        return ("SOURCE_ASSAY_ABSENT",)
    flags = {"ACTUAL_PROCESSING_AND_ASSEMBLY_UNRESOLVED", "ACTIVE_CHEMISTRY_AND_NORMALIZATION_JOIN_UNRESOLVED",
             "ENDPOINT_PAIRING_AND_JOINT_UNCERTAINTY_UNRESOLVED", "MUTATION_DEPENDENT_DISCREPANCY_UNBOUNDED"}
    if context is None:
        flags.add("TARGET_ASSAY_CONTEXT_NOT_SELECTED")
        return tuple(sorted(flags))
    # All rows in the closed original source owner are quoted at 25 C. This is
    # a numerical temperature comparison, not an assay-compatibility admission.
    if context.temperature_k != Decimal("298.15"):
        flags.add("REPORTED_TEMPERATURE_MISMATCH")
    if row.background == "te":
        for endpoint, ph in (("TURNOVER", Decimal("8.05")), ("SPECIFICITY", Decimal("8.1"))):
            if not context.ph_interval[0] <= ph <= context.ph_interval[1]:
                flags.add("REPORTED_" + endpoint + "_PH_OUTSIDE_TARGET_INTERVAL")
        flags.add("TURNOVER_SOLUBLE_EXTRACT_SPECIFICITY_PURIFIED_NOT_PAIRED")
    elif row.background == "gp":
        flags.add("CATALOGUE_QUOTATION_NOT_MATCHED_ASSAY")
        flags.add("WT_UNCERTAINTY_NOT_REPORTED")
        if not context.ph_interval[0] <= Decimal(8) <= context.ph_interval[1]:
            flags.add("CATALOGUE_PH_OUTSIDE_TARGET_INTERVAL")
    else:
        flags.add("TARGET_PH_JOIN_UNRESOLVED")
    return tuple(sorted(flags))


@dataclass(frozen=True, slots=True)
class BiologicalAnchorAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/biological-anchor-assessment"
    use: BiologicalAnchorUse
    exact_source_mean_join: A
    independent_validation: A = A.UNEVALUABLE

    def __post_init__(self):
        exact(self.use, BiologicalAnchorUse)
        if type(self.exact_source_mean_join) is not A or self.independent_validation is not A.UNEVALUABLE:
            raise ValueError("an anchor mean join cannot create independent validation")


def _anchor(use, parent):
    state = A.UNEVALUABLE
    if parent is not None:
        source = ObjectIdentity.from_record(parent.candidate_id, parent)
        if use.source != source:
            state = A.FALSIFIED
        elif parent.turnover_s_inv is not None and parent.specificity_dimensionless is not None:
            expected = EndpointValues(Exact.of(Fraction(parent.turnover_s_inv)), Exact.of(Fraction(parent.specificity_dimensionless)))
            state = A.SATISFIED if use.values == expected else A.FALSIFIED
    return BiologicalAnchorAssessment(use, state)


@dataclass(frozen=True, slots=True)
class BiologicalCaseFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/biological-case-finding"
    case: ObjectIdentity
    parent_source: Candidate | None
    mutant_source: Candidate | None
    source_mean_ratios: tuple[Exact, Exact] | None
    contrast_scope: str
    assay_flags: tuple[str, ...]
    anchors: tuple[BiologicalAnchorAssessment, ...]
    predictive_eligibility: A = A.UNEVALUABLE
    independent_biological_unit_count: int | None = None

    def __post_init__(self):
        exact(self.case, ObjectIdentity)
        if self.case.object_schema != RubiscoPairedCase.SCHEMA or self.case.object_version != RubiscoPairedCase.VERSION:
            raise ValueError("biological finding substitutes its exact paired case")
        for row in (self.parent_source, self.mutant_source):
            if row is not None:
                exact(row, Candidate)
        if self.source_mean_ratios != _ratios(self.parent_source, self.mutant_source):
            raise ValueError("descriptive ratios differ from retained original means")
        expected = "ENDPOINTS_ABSENT" if self.source_mean_ratios is None else (
            "SELF_COMPARISON_NOT_MUTATION_EVIDENCE" if self.parent_source == self.mutant_source
            else "REPORTED_MEAN_RATIO_NOT_JOINT_UNCERTAINTY_OR_GP_TRANSFER")
        if self.contrast_scope != expected:
            raise ValueError("descriptive contrast changes its source evidence scope")
        require_sorted_unique_strings(self.assay_flags, field_name="assay_flags", allow_empty=False)
        if type(self.anchors) is not tuple:
            raise ValueError("biological finding needs its complete anchor-use tuple")
        for anchor in self.anchors:
            exact(anchor, BiologicalAnchorAssessment)
            if anchor != _anchor(anchor.use, self.parent_source):
                raise ValueError("anchor assessment substitutes its exact source means")
        if self.predictive_eligibility is not A.UNEVALUABLE or self.independent_biological_unit_count is not None:
            raise ValueError("exposed source rows, simulation seeds or nested views cannot become validation units")


def _case_finding(case, context, uses, sources):
    matched = tuple(_material_rows(material, sources) for material in (case.parent, case.mutant))
    parent, mutant = (rows[0] if len(rows) == 1 else None for rows in matched)
    flags = set(_assay_flags(context, parent)) | set(_assay_flags(context, mutant))
    if any(len(rows) > 1 for rows in matched):
        flags.add("SOURCE_CONSTRUCT_JOIN_AMBIGUOUS")
    if parent is None or mutant is None:
        flags.add("COMPLETE_SOURCE_RECIPE_JOIN_ABSENT")
    if sources is not None:
        flags.add("EXPOSED_DEVELOPMENT_SOURCE_NOT_INDEPENDENT_VALIDATION")
    if uses:
        flags.add("ANCHOR_REUSE_NOT_INDEPENDENT_VALIDATION")
    ratios = _ratios(parent, mutant)
    scope = "ENDPOINTS_ABSENT" if ratios is None else (
        "SELF_COMPARISON_NOT_MUTATION_EVIDENCE" if parent == mutant else "REPORTED_MEAN_RATIO_NOT_JOINT_UNCERTAINTY_OR_GP_TRANSFER")
    return BiologicalCaseFinding(case.identity, parent, mutant, ratios, scope, tuple(sorted(flags)),
        tuple(_anchor(use, parent) for use in uses))


@dataclass(frozen=True, slots=True)
class PredictiveRequirementFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/predictive-requirement-finding"
    requirement_id: str
    case_ids: tuple[str, ...]
    disposition: A
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.requirement_id)
        require_sorted_unique_strings(self.case_ids, field_name="case_ids", allow_empty=False)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes", allow_empty=False)
        if self.disposition is not A.UNEVALUABLE:
            raise ValueError("exposed observations cannot establish or statistically falsify independent prediction validity")


def _requirements(selection, findings, sources):
    case_ids = tuple(case.case_id for case in selection.cases.cases)
    reasons = {"ELIGIBLE_INDEPENDENT_BIOLOGICAL_VALIDATION_ABSENT", "COMPLETE_JOINT_ENDPOINT_ERROR_ASSESSMENT_ABSENT",
               "FROZEN_ACCURACY_AND_UNCERTAINTY_REQUIREMENTS_UNASSESSED"}
    if sources is not None:
        reasons.add("SOURCE_AND_NOMINATION_ALREADY_EXPOSED")
    if any(row.anchors for row in findings):
        reasons.add("WT_ANCHOR_USE_SEPARATE_FROM_VALIDATION")
    if any(row.source_mean_ratios is None for row in findings):
        reasons.add("MATCHED_MUTATION_ENDPOINTS_ABSENT")
    if any(anchor.exact_source_mean_join is A.FALSIFIED for row in findings for anchor in row.anchors):
        reasons.add("CLAIMED_ANCHOR_SOURCE_OR_VALUE_CONTRADICTED")
    rows = [PredictiveRequirementFinding(key, case_ids, A.UNEVALUABLE, tuple(sorted(reasons)))
        for key in selection.acceptance.predictive_evidence_requirement_ids]
    rows.append(PredictiveRequirementFinding(selection.acceptance.gp_applicability_requirement_id, case_ids, A.UNEVALUABLE,
        ("ACTUAL_GP_PROCESSING_AND_ASSAY_COMPATIBILITY_UNRESOLVED", "GP_MUTATION_DEPENDENT_DISCREPANCY_UNBOUNDED",
         "MATCHED_TE_DONOR_DOES_NOT_ESTABLISH_GP_TRANSPORT")))
    return tuple(sorted(rows, key=lambda row: row.requirement_id))


@dataclass(frozen=True, slots=True)
class PredictiveSupportAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/predictive-support-assessment"
    assessment_id: str
    selection: BiologicalSupportSelection
    sources: ExposedBiologicalSources | None
    cases: tuple[BiologicalCaseFinding, ...]
    requirements: tuple[PredictiveRequirementFinding, ...]
    remaining_requirement_ids: tuple[str, ...]
    claim_ceiling: str = "SOURCE_DESCRIPTIONS_AND_CONDITIONAL_ANALYSIS_ONLY_NO_VALIDATED_GP_FORECAST"
    biological_candidate_action: str = "HOLD"
    combined_milestone: str = "OPEN"
    new_biological_units: int = 0
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.selection, BiologicalSupportSelection)
        if self.sources is not None:
            exact(self.sources, ExposedBiologicalSources)
        expected = tuple(_case_finding(case, context, uses, self.sources) for case, context, uses in zip(
            self.selection.cases.cases, self.selection.contexts, self.selection.anchor_uses, strict=True))
        if self.cases != expected:
            raise ValueError("biological assessment changes complete source, construct, assay or anchor joins")
        requirements = _requirements(self.selection, expected, self.sources)
        if self.requirements != requirements or self.remaining_requirement_ids != tuple(row.requirement_id for row in requirements):
            raise ValueError("biological assessment drops a frozen predictive or Gp requirement")
        if (self.claim_ceiling != "SOURCE_DESCRIPTIONS_AND_CONDITIONAL_ANALYSIS_ONLY_NO_VALIDATED_GP_FORECAST"
                or self.biological_candidate_action != "HOLD" or self.combined_milestone != "OPEN"
                or type(self.new_biological_units) is not int or self.new_biological_units != 0
                or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("retained evidence assessment cannot create validation, native execution or milestone completion")


def assess_predictive_support(selection, sources=None, *, assessment_id):
    """Assess every frozen requirement and every case, retaining absent/contradictory inputs."""
    exact(selection, BiologicalSupportSelection)
    if sources is not None:
        exact(sources, ExposedBiologicalSources)
    findings = tuple(_case_finding(case, context, uses, sources) for case, context, uses in zip(
        selection.cases.cases, selection.contexts, selection.anchor_uses, strict=True))
    requirements = _requirements(selection, findings, sources)
    return PredictiveSupportAssessment(assessment_id, selection, sources, findings, requirements,
                                       tuple(row.requirement_id for row in requirements))
