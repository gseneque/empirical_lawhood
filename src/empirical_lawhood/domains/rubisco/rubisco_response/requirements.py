# SPDX-License-Identifier: MPL-2.0
"""Backward scientific requirements for the combined Rubisco milestone.

This graph is separate from the executable transform/assess DAG. A conditional
mathematical connection cannot discharge its biological or benefit ancestors.
"""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentPhase, ConditionRole, ContributionRole, RequirementSupplyAssessment, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.design.recursive_authoring import validate_selected_requirement_graph
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy

PHASES = (AssessmentPhase.PROCEDURE, AssessmentPhase.INSTANCE, AssessmentPhase.ADMISSION, AssessmentPhase.JOINED)
CONNECTION_QUESTIONS = (
    "The conditional method preserves the declared four-state, gas, clock and event meanings.",
    "Every selected case, alternative, joint parameter point and source is present with exact identity.",
    "Independent balance, flux, endpoint and sensitivity checks pass for every retained point.",
    "Joint support is used with its original denominator, paired context and frozen candidate criterion.",
)


@dataclass(frozen=True, slots=True)
class ScientificConnectionAssessmentPlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/connection-assessment-plan"
    connection: ObjectIdentity
    phases: tuple[AssessmentPhase, ...] = PHASES
    questions: tuple[str, ...] = CONNECTION_QUESTIONS

    def __post_init__(self):
        exact(self.connection, ObjectIdentity)
        if (self.connection.object_schema != ScientificConnectionSpec.SCHEMA
                or self.connection.object_version != ScientificConnectionSpec.VERSION
                or self.phases != PHASES or self.questions != CONNECTION_QUESTIONS):
            raise ValueError("selected connection must retain procedure, instance, admission and joined-use assessments")


@dataclass(frozen=True, slots=True)
class RubiscoRequirementGraph(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/requirement-graph"
    graph_id: str
    study: ObjectIdentity
    root_requirement_id: str
    conditional_requirement_id: str
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    connection_assessment_plans: tuple[ScientificConnectionAssessmentPlan, ...]

    def __post_init__(self):
        validate_stable_id(self.graph_id)
        for name in (self.root_requirement_id, self.conditional_requirement_id):
            validate_stable_id(name)
        exact(self.study, ObjectIdentity)
        if self.study.object_schema != RubiscoResponseStudy.SCHEMA or self.study.object_version != RubiscoResponseStudy.VERSION:
            raise ValueError("scientific requirement graph changes its exact selected study")
        if type(self.requirements) is not tuple or not self.requirements:
            raise ValueError("scientific requirement graph must be complete and nonempty")
        require_sorted_unique_ids(self.requirements, attribute="requirement_id", field_name="requirements")
        for requirement in self.requirements:
            exact(requirement, ScientificRequirementSpec)
        validate_selected_requirement_graph(requirements=self.requirements, maximum_depth=16)
        by_id = {row.requirement_id: row for row in self.requirements}
        if self.root_requirement_id not in by_id or self.conditional_requirement_id not in by_id:
            raise ValueError("scientific graph loses a selected target")
        reachable, waiting = set(), [self.root_requirement_id]
        while waiting:
            name = waiting.pop()
            if name not in reachable:
                reachable.add(name)
                waiting.extend(by_id[name].further_requirement_ids)
        if reachable != set(by_id):
            raise ValueError("scientific graph hides requirements outside the complete target ancestry")
        if type(self.connections) is not tuple or not self.connections:
            raise ValueError("scientific graph must retain its selected assessed connection")
        require_sorted_unique_ids(self.connections, attribute="connection_id", field_name="connections")
        for connection in self.connections:
            exact(connection, ScientificConnectionSpec)
            requirement = by_id.get(connection.requirement_id)
            if (requirement is None or requirement.assessment_operation_id != connection.assessment_operation_id
                    or connection.evidence_role not in requirement.permitted_roles):
                raise ValueError("selected connection changes the owning requirement or evidence role")
        if (type(self.connection_assessment_plans) is not tuple
                or tuple(row.connection for row in self.connection_assessment_plans)
                != tuple(ObjectIdentity.from_record(row.connection_id, row) for row in self.connections)):
            raise ValueError("scientific graph omits a selected connection assessment plan")
        for plan in self.connection_assessment_plans:
            exact(plan, ScientificConnectionAssessmentPlan)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.graph_id, self)


def scientific_scope(study):
    exact(study, RubiscoResponseStudy)
    return ScientificConditionScope(study.cases.selection_id, "world.rubisco-response.conditional",
        study.study_id, ("delta-log-kcat-c", "delta-log-specificity", "log-kcat-c", "log-specificity"),
        ("1", "1", "1", "1"), "rubisco-response.assess", "clock.rubisco.physical-seconds",
        "Joint absolute and paired log endpoints; active-site events; full selected case and alternative census",
        source_config_sha256=study.fingerprint(), instance_id=study.study_id,
        population_id="population.rubisco-response.exposed-analytical", uncertainty_contract=study.acceptance.identity)


def response_requirement_graph(study):
    """Build from the final claims backward; do not infer positive evidence."""
    exact(study, RubiscoResponseStudy)
    prefix = "requirement." + study.study_id + "."
    scope = scientific_scope(study)
    records = {}

    def add(name, condition, falsifier, parents=(), role=ConditionRole.EVIDENTIAL, *, absolute=False, case=None):
        key = name if absolute else prefix + name
        row = ScientificRequirementSpec(key, "rubisco-response.assess", role,
            "Validated joint prediction and independently measured computational benefit",
            condition, scope if case is None else replace(scope, instance_id=case),
            "rubisco-response.assess", falsifier, (ContributionRole.RETAINED_ANALYSIS_INPUT,),
            tuple(sorted(set(parents))))
        previous = records.setdefault(key, row)
        if previous != row:
            raise ValueError("scientific requirement identifier aliases different selected conditions")
        return key

    nominated = add("prediction-nomination", "The sourced candidate prediction is separate from thresholds and donor effects.",
        "A donor estimate or favorable witness replaces an absent nominated effect.")
    criteria = add("criteria", "Joint tolerances, service, false-admission, cost and finite stopping criteria are admitted for their purpose.",
        "The selected criterion lacks its source or a required independent admission.",
        study.acceptance.criterion_admission_requirement_ids)
    for name in study.acceptance.criterion_admission_requirement_ids:
        add(name, "The selected acceptance criterion has its outstanding independent admission.",
            "The criterion is unsupported for the declared next action.", absolute=True)
    conditional = add("conditional-connection",
        "The declared paired rate support is transformed and assessed exactly under the selected conditional model.",
        "A balance, endpoint, context, source, denominator or joint-use check fails.", role=ConditionRole.TASK)
    case_requirements = []
    for supply in study.supplies:
        case_prefix = supply.case.case_id + "."
        site = add(case_prefix + "active-state",
            "Both complete molecular endpoints have independently admitted coordinates, parameters and all-eight-site active chemistry.",
            "A material, contact, Hamiltonian, ligand, protonation or finite-mutation correspondence fails.",
            tuple(sorted(set(supply.context.chemistry.unresolved_requirement_ids))), role=ConditionRole.PHYSICAL, case=supply.case.case_id)
        for name in supply.context.chemistry.unresolved_requirement_ids:
            add(name, "The selected all-site chemical prerequisite is independently supplied.",
                "Its state or source admission is missing or incompatible.", absolute=True)
        rates = []
        for scenario in supply.scenarios:
            for binding in scenario.ledger.bindings:
                pending = tuple(sorted(set(binding.unresolved_requirement_ids)))
                key = case_prefix + scenario.scenario_id + ".rate." + binding.parameter
                rates.append(add(key,
                    "The " + binding.transition + " rate support has a compatible source, physical clock, dependence and independent assessment.",
                    "A declared rate, imposed invariance or support bound lacks its stated applicability.",
                    pending, case=supply.case.case_id))
                for name in pending:
                    add(name, "The selected rate supplier prerequisite is independently supplied.",
                        "Rate evidence remains missing, unassessed or outside scope.", absolute=True)
            for name in scenario.unresolved_requirement_ids:
                add(name, "The original failed or unknown scenario receives an independently admitted conservative supply.",
                    "Failure is dropped, replaced by a point guess or relabelled as adverse support.", absolute=True)
                rates.append(name)
        for name in supply.prerequisite_requirement_ids:
            add(name, "The selected paired-supply prerequisite is independently supplied.",
                "A consequential supply prerequisite remains missing.", absolute=True)
        case_requirements.append(add(case_prefix + "kinetic-validity",
            "The molecular-to-kinetic closure, joint uncertainty and context are valid for this exact paired material.",
            "An untested closure or parameter alternative changes the joint candidate conclusion.",
            (site, conditional, *rates, *supply.prerequisite_requirement_ids), case=supply.case.case_id))
    validation = []
    for name in study.acceptance.predictive_evidence_requirement_ids:
        validation.append(add(name,
            "Independent experimental validation tests both endpoints without reusing design or calibration exposure.",
            "Held-out coverage, units, paired dependence or endpoint completeness fails.", absolute=True))
    gp = add(study.acceptance.gp_applicability_requirement_id,
        "The validated evidence supports transfer to the selected Gp materials and processing views.",
        "Related donor evidence is substituted for Gp applicability.", absolute=True)
    prediction = add("validated-prediction",
        "Both absolute and paired endpoints meet the declared predictive accuracy with assessed Gp applicability.",
        "Mathematical conformance or reference agreement is reported as biological prediction.",
        (nominated, criteria, gp, *case_requirements, *validation))
    matrix = add(study.acceptance.matrix_handoff_requirement_id,
        "An eligible completed E1–E6 report supplies supported, adverse and unresolved transfer propositions.",
        "Unfinished Matrix evidence or favorable-only selection substitutes for the scientific handoff.", absolute=True)
    policy = add("prospective-policy",
        "Committed adequacy decisions meet useful-service and false-admission criteria on the full denominator.",
        "Always-abstain behavior, future-outcome access or optional-stopping error passes validation.", (criteria,))
    cost = add("prospective-cost",
        "Reference, conventional baseline and selected reduced method retain all construction, validation, fallback and amortized costs.",
        "Failures, unresolved attempts, offline cost or reference work is omitted from the declared comparison.", (criteria, policy))
    benefit = add("computational-benefit",
        "Measured benefit survives the actual reference, conventional baseline and prospective service constraints.",
        "Conditional accuracy, elapsed-time anecdotes or omitted costs substitute for measured benefit.", (matrix, cost, policy))
    root = add("combined-milestone",
        "Validated joint kinetic prediction and Matrix-informed computational benefit are both established.",
        "An early conditional forecast closes either missing half of the combined milestone.", (prediction, benefit))
    connection = ScientificConnectionSpec("connection." + study.study_id + ".conditional", conditional,
        "rubisco-response.predict", "product", "prediction", "rubisco-response.assess",
        "claim." + study.study_id + ".conditional", ContributionRole.RETAINED_ANALYSIS_INPUT,
        records[conditional].falsifier)
    return RubiscoRequirementGraph("graph." + study.study_id, study.identity, root, conditional,
        tuple(records[key] for key in sorted(records)), (connection,),
        (ScientificConnectionAssessmentPlan(ObjectIdentity.from_record(connection.connection_id, connection)),))


def validate_connection_assessment_census(graph, assessments):
    """Require every selected phase and original scoped identity; no outcome coercion."""
    exact(graph, RubiscoRequirementGraph)
    if type(assessments) is not tuple:
        raise TypeError("connection assessment census must be immutable")
    expected = tuple((connection.connection_id, phase) for connection in graph.connections for phase in PHASES)
    actual = []
    requirements = {row.requirement_id: row for row in graph.requirements}
    connections = {row.connection_id: row for row in graph.connections}
    for assessment in assessments:
        exact(assessment, RequirementSupplyAssessment)
        connection = connections.get(assessment.connection.object_id)
        if (connection is None or assessment.connection != ObjectIdentity.from_record(connection.connection_id, connection)
                or assessment.requirement != ObjectIdentity.from_record(connection.requirement_id, requirements[connection.requirement_id])
                or assessment.instance_id != graph.study.object_id):
            raise ValueError("connection assessment substitutes its requirement, connection or instance")
        actual.append((connection.connection_id, assessment.phase))
    if tuple(actual) != expected:
        raise ValueError("selected connection lacks its complete four-phase assessment census")
