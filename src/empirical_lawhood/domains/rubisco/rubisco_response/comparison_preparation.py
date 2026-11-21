# SPDX-License-Identifier: MPL-2.0
"""Complete comparison selections and no-contact native-entry prerequisites.

The existing conditional preparer owns its installed draft. This additional
selection derives the comparison census; it cannot fabricate native tasks or
promote exposed inputs into a prospective scientific installation.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.execution.experiment_preparation import DependencyKind as K, ExecutionSelection, ExperimentDependency, ExperimentPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_preparation import ResponseExperimentInputs, prepare_response_experiment
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import RubiscoResponseExperimentSpecification, select_response_study
from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import FiniteResponsePolicy
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_preparation import MolecularPreparationCensus
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_error import SupplierComparisonParity
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_target import ReductionTargetAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy

ARMS = ("reference", "conventional", "reduced")
COST_ARMS = ("conventional", "reduced")


@dataclass(frozen=True, slots=True)
class ComparisonWorkAllocation(CanonicalRecord):
    """Frozen cost treatment of exact work returned by supported authoring.

    Every attempt at that work, including failure or uncertain contact, inherits
    this treatment. A shared event has a full charge in each selected arm and
    one physical charge in the campaign. The declaration is not measured cost.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-work-allocation"
    work: ScientificInquiryWork
    phase: str
    charged_arms: tuple[str, ...]

    def __post_init__(self):
        exact(self.work, ScientificInquiryWork)
        if self.phase not in {"SETUP", "USE", "AUDIT"}:
            raise ValueError("comparison cost must retain setup, use or audit meaning")
        if (type(self.charged_arms) is not tuple or not self.charged_arms
                or self.charged_arms != tuple(arm for arm in COST_ARMS if arm in self.charged_arms)):
            raise ValueError("comparison work needs its complete unique charged-arm selection")
        if self.phase == "AUDIT" and self.charged_arms != COST_ARMS:
            raise ValueError("common validation audit must carry the same burden in both comparison arms")


@dataclass(frozen=True, slots=True)
class ComparisonCasePlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-case-plan"
    case: ObjectIdentity
    policy: FiniteResponsePolicy | None
    parity: SupplierComparisonParity | None

    def __post_init__(self):
        exact(self.case, ObjectIdentity)
        if self.policy is not None:
            exact(self.policy, FiniteResponsePolicy)
            if self.policy.case_id != self.case.object_id:
                raise ValueError("comparison policy substitutes another paired case")
        if self.parity is not None:
            exact(self.parity, SupplierComparisonParity)
            if self.parity.case != self.case:
                raise ValueError("comparison parity substitutes another paired case")


@dataclass(frozen=True, slots=True)
class ComparisonAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-assignment"
    unit_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    scenario_id: str
    point_id: str | None
    original_scenario_state: str
    arm: str
    method: ObjectIdentity | None

    def __post_init__(self):
        for value in (self.unit_id, self.scenario_id):
            validate_stable_id(value)
        for value in (self.case, self.context):
            exact(value, ObjectIdentity)
        if self.point_id is not None:
            validate_stable_id(self.point_id)
        if self.method is not None:
            exact(self.method, ObjectIdentity)
        if self.original_scenario_state not in {"AVAILABLE", "FAILED", "UNKNOWN"} or self.arm not in ARMS:
            raise ValueError("comparison assignment changes its original scenario or comparison arm")

    @property
    def identity(self):
        return ObjectIdentity.from_record("assignment.rubisco-response." + self.fingerprint(), self)

    @property
    def point_key(self):
        return self.case.object_id, self.scenario_id, self.point_id


@dataclass(frozen=True, slots=True)
class ResponseComparisonDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/comparison-design"
    design_id: str
    original_study: RubiscoResponseStudy
    specification: RubiscoResponseExperimentSpecification
    cases: tuple[ComparisonCasePlan, ...]
    false_admission_denominator: str
    scale: str
    cost_work: tuple[ComparisonWorkAllocation, ...] = ()
    reference_audit: str = "ALL_ASSIGNED_CASES_INCLUDING_REFUSALS"
    evidence_scope: str = "EXPOSED_RETAINED_COMPARISON_NOT_PROSPECTIVE_QUALIFICATION"

    def __post_init__(self):
        validate_stable_id(self.design_id)
        exact(self.original_study, RubiscoResponseStudy)
        exact(self.specification, RubiscoResponseExperimentSpecification)
        study = self.study
        if type(self.cases) is not tuple or tuple(row.case for row in self.cases) != tuple(case.identity for case in study.cases.cases):
            raise ValueError("comparison selection drops or reorders a candidate, control or processing view")
        for row, supply in zip(self.cases, study.supplies, strict=True):
            exact(row, ComparisonCasePlan)
            if row.policy is not None and row.policy.study != study:
                raise ValueError("comparison policy changes frozen sources, criteria, uncertainty or finite allowance")
            if row.parity is not None:
                if (row.parity.context != supply.context.identity or row.parity.reference_method != study.acceptance.reference_method
                        or row.parity.conventional_method != study.acceptance.conventional_baseline):
                    raise ValueError("comparison parity changes selected context, reference or competent baseline")
        suppliers = {row.policy.selected_supplier for row in self.cases if row.policy is not None}
        if len(suppliers) > 1:
            raise ValueError("comparison must retain one selected supplier across its complete case census")
        if self.false_admission_denominator not in {"ALL_ASSIGNED_UNITS", "ADMITTED_UNITS"} or self.scale not in {"RAW", "ANCHORED"}:
            raise ValueError("comparison needs frozen error scale and false-admission denominator")
        if type(self.cost_work) is not tuple:
            raise ValueError("comparison needs immutable complete selected cost treatments")
        for row in self.cost_work:
            exact(row, ComparisonWorkAllocation)
            operands = set(row.work.scientific_operands)
            sources = {study.cases.identity, study.allocation.identity, *(supply.identity for supply in study.supplies)}
            if study.identity not in operands and not sources <= operands:
                raise ValueError("comparison cost work lacks its complete selected scientific operands")
        keys = tuple(row.work.fingerprint() for row in self.cost_work)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("comparison repeats or reorders an exact scientific cost opportunity")
        if (self.reference_audit != "ALL_ASSIGNED_CASES_INCLUDING_REFUSALS"
                or self.evidence_scope != "EXPOSED_RETAINED_COMPARISON_NOT_PROSPECTIVE_QUALIFICATION"):
            raise ValueError("exposed preparation cannot create held assignment or omit refused reference audits")

    @property
    def study(self):
        return select_response_study(self.specification, self.original_study)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.design_id, self)

    @property
    def assignments(self):
        study = self.study
        result = []
        for case_plan, supply in zip(self.cases, study.supplies, strict=True):
            unit, = (row.unit_id for row in study.allocation.units if supply.case.case_id in row.numerical_view_ids)
            methods = (study.acceptance.reference_method, study.acceptance.conventional_baseline,
                None if case_plan.parity is None else case_plan.parity.approximation_method)
            for scenario in supply.scenarios:
                for point_id in tuple(row.point_id for row in scenario.points) or (None,):
                    result.extend(ComparisonAssignment(unit, supply.case.identity, supply.context.identity,
                        scenario.scenario_id, point_id, scenario.original_state, arm, method)
                        for arm, method in zip(ARMS, methods, strict=True))
        return tuple(result)

    @property
    def log_tolerances(self):
        acceptance = self.study.acceptance
        return (*acceptance.absolute_log_endpoint_tolerances, *acceptance.absolute_log_endpoint_tolerances,
                *acceptance.paired_log_endpoint_tolerances)


def comparison_design(original_study, specification, *, design_id, policies=(), parities=(), cost_work=(),
                      false_admission_denominator, scale):
    """Derive all case and outcome assignments from the ordinary source selection."""
    study = select_response_study(specification, original_study)
    if type(policies) is not tuple or type(parities) is not tuple:
        raise ValueError("comparison selections require immutable original policy/parity tuples")
    for value in policies:
        exact(value, FiniteResponsePolicy)
    for value in parities:
        exact(value, SupplierComparisonParity)
    by_policy = {row.case_id: row for row in policies}
    by_parity = {row.case.object_id: row for row in parities}
    expected = {case.case_id for case in study.cases.cases}
    if len(by_policy) != len(policies) or len(by_parity) != len(parities) or not (by_policy.keys() | by_parity.keys()) <= expected:
        raise ValueError("comparison selection duplicates or introduces a foreign case")
    cases = tuple(ComparisonCasePlan(case.identity, by_policy.get(case.case_id), by_parity.get(case.case_id)) for case in study.cases.cases)
    return ResponseComparisonDesign(design_id, original_study, specification, cases, false_admission_denominator, scale, cost_work)


def _native_dependencies(design, molecular, target):
    study = design.study
    required = [ExperimentDependency("rubisco.comparison." + code, kind, detail) for code, kind, detail in (
        ("actual-entry-authority", K.AUTHORITY, "Obtain actual source access, approval, issue, execution and outcome access at their separate boundaries."),
        ("actual-source-admission", K.EXTERNAL_INPUT, "Authenticate original supplier inputs and current-use admission before contact."),
        ("actual-specialist-environment", K.ENVIRONMENT, "Preflight the selected specialist interpreter, backend and exact producing source."),
        ("actual-resource-capacity", K.ENVIRONMENT, "Admit the operator profile, affinity, memory and full finite-graph capacity."),
        ("actual-storage", K.STORAGE, "Verify the selected mount, write access, capacity and disjoint scratch/custody destinations."),
        ("installed-native-lowering", K.SOFTWARE, "A justified supplier needs its registered scientific operations, native subwork and complete output codecs."),
        ("installed-settled-source-acceptance", K.SOFTWARE, "Accept the exact installed source and freeze it before dependent native work."),
        ("justified-supplier", K.SCIENTIFIC_EVIDENCE, "Independently justify the consequential reduction target from actual supplier cost or uncertainty and receiver sensitivity."),
        ("active-state-and-reference", K.SCIENTIFIC_EVIDENCE, "Admit matched physical/chemical states, clock, rates and reference validity at the selected supplier scope."),
        ("indicator-and-sequential-validity", K.SCIENTIFIC_EVIDENCE, "Assess the frozen joint error set, nonlinear allowances and conditional sequential bounds."),
        ("native-parity", K.SCIENTIFIC_EVIDENCE, "Independently assess the selected model, dynamics, preparation and verification parity for all three arms."),
        ("matrix-transfer", K.SCIENTIFIC_EVIDENCE, "Resolve the eligible scientific Matrix handoff without dropping adverse or unresolved transfer findings."),
    )]
    for case in design.cases:
        for suffix, missing, detail in (
            ("policy-selection", case.policy is None, "Select the finite policy for this original case without changing its complete study."),
            ("parity-selection", case.parity is None, "Select exact shared comparison operands and all three methods for this original case."),
            ("supplier-selection", case.policy is None or case.policy.selected_supplier is None, "The justified production supplier is not selected."),
        ):
            if missing:
                required.append(ExperimentDependency("rubisco.comparison." + case.case.object_id + "." + suffix,
                    K.SCIENTIFIC_EVIDENCE, detail))
    if molecular is None:
        required.append(ExperimentDependency("rubisco.comparison.preparation-census", K.EXTERNAL_INPUT,
            "Supply the complete original matched molecular-preparation census, including failed and unentered members."))
    else:
        exact(molecular, MolecularPreparationCensus)
        if molecular.selection.cases != study.cases:
            raise ValueError("comparison substitutes another molecular preparation case census")
        if any(supply.context.temperature_k != molecular.selection.temperature_k
               or supply.context.chemistry not in molecular.selection.chemistries for supply in study.supplies):
            raise ValueError("comparison changes selected molecular chemistry or physical temperature")
    if target is None:
        required.append(ExperimentDependency("rubisco.comparison.target-assessment", K.EXTERNAL_INPUT,
            "Supply the independent retained target assessment at this exact selected study scope."))
    else:
        exact(target, ReductionTargetAssessment)
        if target.reference_report.study != study:
            raise ValueError("comparison borrows a target assessment from different scientific selections")
    return tuple(sorted(required, key=lambda row: row.code))


@dataclass(frozen=True, slots=True)
class PreparedResponseComparison:
    design: ResponseComparisonDesign
    conditional_preparation: ExperimentPreparation
    assignments: tuple[ComparisonAssignment, ...]
    native_entry_prerequisites: tuple[ExperimentDependency, ...]
    molecular_preparation: MolecularPreparationCensus | None
    target_assessment: ReductionTargetAssessment | None
    native_entry_status: str = "NOT_READY"
    new_native_calls: int = 0

    def __post_init__(self):
        exact(self.design, ResponseComparisonDesign)
        exact(self.conditional_preparation, ExperimentPreparation)
        if self.conditional_preparation.specification != self.design.specification.identity:
            raise ValueError("comparison preparation changes the ordinary conditional specification")
        if self.assignments != self.design.assignments:
            raise ValueError("comparison preparation drops a complete arm/scenario/point assignment")
        if self.native_entry_prerequisites != _native_dependencies(self.design, self.molecular_preparation, self.target_assessment):
            raise ValueError("comparison preparation hides an actual native entry boundary")
        if self.native_entry_status != "NOT_READY" or type(self.new_native_calls) is not int or self.new_native_calls != 0:
            raise ValueError("exposed preparation cannot authorize or enter native work")


    @property
    def remaining_requirement_ids(self):
        return tuple(sorted({*(row.requirement_id for row in response_requirement_graph(self.design.study).requirements),
            *(() if self.molecular_preparation is None else self.molecular_preparation.unresolved_requirement_ids),
            *(() if self.target_assessment is None else self.target_assessment.remaining_requirement_ids)}))


def prepare_response_comparison(design, *, execution, molecular_preparation=None, target_assessment=None):
    """Use the installed conditional preparer; expose separate actual entry gaps."""
    exact(design, ResponseComparisonDesign)
    exact(execution, ExecutionSelection)
    ordinary = prepare_response_experiment(design.specification,
        scientific_inputs={"study": design.original_study.allocation}, execution=execution,
        method_inputs=ResponseExperimentInputs(design.original_study))
    return PreparedResponseComparison(design, ordinary, design.assignments,
        _native_dependencies(design, molecular_preparation, target_assessment), molecular_preparation, target_assessment)
