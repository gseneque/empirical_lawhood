# SPDX-License-Identifier: MPL-2.0
"""Receiver-first requirements for the conditional root, using shared contracts.

Only the decision's actual unresolved requirements are mandatory at the root.
Alternative supplier branches retain their own prerequisites and are unselected.
The broader response-study/Matrix/comparative-benefit graph is unchanged.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentPhase, ConditionRole, ContributionRole, RequirementSupplyAssessment, ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.design.recursive_authoring import SupplierProposal, validate_selected_requirement_graph
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import assess_initial_root, calculate_initial_root
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootAssessment, InitialRootResult, InitialRootScopedAssessment, InitialRootScopedResult
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

CALCULATE = 'rubisco-response.initial-root-calculate'
ASSESS = 'rubisco-response.initial-root-assess'
USE = 'rubisco-response.initial-root-use'
TARGET = 'rubisco-response.initial-root-target'
QUESTION = 'Does I95M have turnover ratio > 1 and specificity ratio >= 1 under the selected paired conditional model?'


def analysis_arguments(analysis):
    exact(analysis, InitialRootAnalysisInputs)
    return dict(request=analysis.request, selection=analysis.model, evidence=analysis.inputs,
        reviews=analysis.reviews.contrast_reviews, joint_reviews=analysis.reviews.joint_reviews)


def initial_root_scope(analysis):
    exact(analysis, InitialRootAnalysisInputs)
    return ScientificConditionScope(analysis.model.selection_id, 'world.rubisco.initial-conditional',
        analysis.identity.object_id, ('specificity-ratio', 'turnover-ratio'), ('1', '1'),
        'receiver.rubisco.initial-joint-criterion', 'clock.rubisco.declared-rate-closure',
        'Same paired materials, processing/chemical alternatives, assay conditions and joint support; no biological validation.',
        source_config_sha256=analysis.fingerprint(), instance_id=analysis.request.request_id,
        population_id='population.rubisco.original-exposure-groups', uncertainty_contract=analysis.request.identity)


def analytic_units(analysis):
    return tuple(sorted({case.case.exposure_group for case in analysis.model.cases}))


def nested_views(analysis):
    return tuple(sorted({case.case.parent.processing_view for case in analysis.model.cases}))


@dataclass(frozen=True, slots=True)
class InitialRootRequirementGraph(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-requirement-graph'
    analysis: ObjectIdentity
    result: ObjectIdentity
    root_requirement_id: str
    numerical_requirement_id: str
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    suppliers: tuple[SupplierProposal, ...]

    def __post_init__(self):
        for pin, kind in ((self.analysis, InitialRootAnalysisInputs), (self.result, InitialRootResult)):
            exact(pin, ObjectIdentity)
            if (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('initial root graph changes its exact analysis or decision revision')
        for name in ('root_requirement_id', 'numerical_requirement_id'):
            validate_stable_id(getattr(self, name))
        for values, kind, attribute in ((self.requirements, ScientificRequirementSpec, 'requirement_id'),
                (self.connections, ScientificConnectionSpec, 'connection_id'), (self.suppliers, SupplierProposal, 'proposal_id')):
            if type(values) is not tuple:
                raise TypeError('initial root graph requires immutable typed rosters')
            require_sorted_unique_ids(values, attribute=attribute, field_name=attribute)
            for row in values:
                exact(row, kind)
        by_id = {row.requirement_id: row for row in self.requirements}
        if not {self.root_requirement_id, self.numerical_requirement_id}.issubset(by_id):
            raise ValueError('initial root graph loses its target or numerical assessment')
        validate_selected_requirement_graph(requirements=self.requirements, suppliers=self.suppliers, maximum_depth=8)
        if any(row.requirement_id not in by_id for row in (*self.connections, *self.suppliers)):
            raise ValueError('initial root graph has an unbound supplier or connection')

    @property
    def identity(self):
        return ObjectIdentity.from_record('initial-root-graph.' + self.fingerprint(), self)


def _missing_meaning(key):
    if key == 'initial-model.actual-paired-physical-preparation':
        return ('Admit the actual paired physical state required by the selected receiver; retained construction is insufficient.',
            'Use active_relaxation.assess_matched_active_relaxation or independently justify why that receiver needs no new preparation.')
    if key == 'initial-model.chemical-model-and-closure-applicability':
        return ('Assess selected chemical alternatives and the limiting kinetic closure for the original paired assay.',
            'Supply the physical/kinetic applicability review; numerical controls and source text cannot supply it.')
    if '.contrast.' in key or 'mutation-contrast' in key:
        return ('Supply jointly supported relative operands, or an independently sufficient bound for the selected endpoint decision.',
            'Use initial_contributions and initial_model contrast/joint reviews with exact material, context, state and dependence.')
    if 'simultaneous-support' in key or 'assessed-joint-support' in key:
        return ('Supply a simultaneous support region at the actual dependence and coverage scope.',
            'An exposed sample or separate marginal intervals cannot establish joint coverage.')
    if 'decision-margin' in key:
        return ('Narrow or bound only the unresolved strict turnover inequality or inclusive specificity inequality.',
            'Use the exact waiting threshold or joint product bound; do not impose an illustrative numerical tolerance.')
    if 'resolution' in key:
        return ('Resolve the consequential physical alternative or processing view under the selected aggregation policy.',
            'Do not average incompatible alternatives or erase an adverse case to force a uniform conclusion.')
    return ('Supply the exact original unresolved condition: ' + key + '.',
        'Use its original source and domain assessor; a label, implementation receipt or supplied number is insufficient.')


def initial_root_requirement_graph(analysis, *, result=None, parent=None):
    """Derive a finite graph from the actual decision, without entering suppliers."""
    arguments = analysis_arguments(analysis)
    expected = calculate_initial_root(**arguments)
    if result is None:
        result = expected
    if result != expected:
        raise ValueError('initial root graph substitutes its exact source-conditioned decision')
    scope = initial_root_scope(analysis)
    prefix = 'requirement.' + analysis.request.request_id + '.'
    numerical = prefix + 'exact-joint-decision'
    root_id = prefix + 'conditional-endpoint-target'
    assessment_operation = ASSESS if parent is None else USE
    requirements = {}
    def add(key, condition, falsifier, *, further=(), role=ConditionRole.EVIDENTIAL, selected=False):
        row = ScientificRequirementSpec(key, assessment_operation if selected else TARGET, role, QUESTION,
            condition, scope, assessment_operation, falsifier, (ContributionRole.RETAINED_ANALYSIS_INPUT,),
            tuple(sorted(set(further))))
        previous = requirements.setdefault(key, row)
        if previous != row:
            raise ValueError('initial root prerequisite label aliases different scientific conditions')
        return key
    add(numerical, 'Independently reconstruct the complete frozen conditional decision, including justified adverse and unresolved outcomes.',
        'Any exact operand, source, support, criterion, denominator, balance or joint-decision mismatch.', selected=True, role=ConditionRole.TASK)
    for key in result.decision_requirement_ids:
        condition, falsifier = _missing_meaning(key)
        add(key, condition, falsifier)
    add(root_id, 'The selected turnover and specificity conjunction has an admitted conclusion at its declared physical scope.',
        'One admitted adverse endpoint contradicts the conjunction; a missing consequential condition leaves it unresolved.',
        further=(numerical, *result.decision_requirement_ids), role=ConditionRole.PHYSICAL)

    # These branches are alternatives, not mandatory additions to the root.
    # Their prerequisite records make the cost of a selected future supplier explicit.
    branch_specs = (
        ('retained-inputs', 'Reuse exact original evidence through its source reader and destination review.', (),
            (CALCULATE, ASSESS), (), 'Existing original-source analysis; adds no native observations.'),
        ('relative-operand-supply', 'Supply the decision-relevant relative contrast or sufficient endpoint bound.',
            ('physical-applicability', 'joint-support'), (), ('ACTUAL_RELATIVE_OPERANDS_OR_BOUND_MISSING',),
            'Existing initial_contributions/paired_endpoint_bounds consume supplied operands; native supply remains separate.'),
        ('paired-integral-bound', 'Assess a signed paired receiver bound before selecting a native integral.',
            ('receiver-definition', 'restraint-and-domain', 'activation-connection'), (), ('PHYSICAL_BOUND_PREMISES_MISSING',),
            'Reuse paired_receiver_bound; geometry, stiffness, grid, remainder and activation admission are actual inputs.'),
        ('retained-response-actions', 'Assess reuse of a complete operator action for the actual physical input direction.',
            ('receiver-definition', 'compatible-states', 'direction-action-interface'), (), ('PHYSICAL_VECTOR_ACTION_INTERFACE_REQUIRED',),
            'Extend existing periodic control owners only after a selected response requirement; this root does not require the extension.'),
        ('physical-preparation', 'Prepare only the state or history required by the selected receiving calculation.',
            ('receiver-definition', 'compatible-states', 'durable-preparation-state'), (), ('RECEIVER_AND_RECOVERY_REQUIREMENTS_UNRESOLVED',),
            'Reuse active-relaxation selection and native-subwork custody; long preparation needs an authentic safe-state contract.'),
    )
    prerequisite_text = {
        'physical-applicability': 'Admit the material, assay, chemical alternative and kinetic closure at this receiver.',
        'joint-support': 'Supply actual joint values/bounds and the assessment of their simultaneous dependence and coverage.',
        'receiver-definition': 'Select the signed quantity, physical clock/measure, accuracy allowance, causal cutoff and allowed preparation freedoms.',
        'restraint-and-domain': 'Supply actual stiffness, centres, weights, physical domain and valid quadrature/remainder bounds.',
        'activation-connection': 'Supply the consequential correction from a restrained paired integral to the requested rate or endpoint.',
        'compatible-states': 'Authenticate actual coordinates, topology, full operator, numerical environment and any receiver-required history.',
        'direction-action-interface': 'Implement the missing generic physical-vector/full-force action interface with mass/constraint semantics and error assessment.',
        'durable-preparation-state': 'Implement/authenticate the needed safe coordinates, momenta or optimizer continuation state before a selected long preparation.',
    }
    proposals = []
    for name, condition, prerequisites, operations, unavailable, explanation in branch_specs:
        keys = tuple(prefix + 'supplier-prerequisite.' + value for value in prerequisites)
        for key, value in zip(keys, prerequisites, strict=True):
            add(key, prerequisite_text[value], 'The supplier cannot provide its selected scientific product without this exact prerequisite.')
        branch = add(prefix + 'supplier.' + name, condition,
            'Missing inputs, incompatible original evidence or an unimplemented connection prevent this supplier from answering the receiver.', further=keys)
        proposals.append(SupplierProposal('proposal.' + analysis.request.request_id + '.' + name,
            branch, tuple(sorted(operations)), tuple(sorted(keys)), False, explanation, tuple(sorted(unavailable))))
    if parent is None:
        connection = ScientificConnectionSpec('connection.' + analysis.request.request_id + '.decision', numerical,
            CALCULATE, 'product', 'result', ASSESS, 'claim.' + analysis.request.request_id + '.conditional',
            ContributionRole.RETAINED_ANALYSIS_INPUT, requirements[numerical].falsifier)
    else:
        scoped = InitialRootScopedResult(analysis.identity, scope, result)
        products = tuple(row for row in parent.products if row.record == scoped.identity)
        if len(products) != 1 or parent.scope != scope or products[0].role is not ContributionRole.RETAINED_ANALYSIS_INPUT:
            raise ValueError('initial root reuse changes original contribution, complete result or destination scope')
        product, = products
        connection = ScientificConnectionSpec('connection.' + analysis.request.request_id + '.decision', numerical,
            None, None, 'result', USE, 'claim.' + analysis.request.request_id + '.conditional',
            ContributionRole.RETAINED_ANALYSIS_INPUT, requirements[numerical].falsifier,
            ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id, 'external.' + USE + '.result')
    return InitialRootRequirementGraph(analysis.identity, result.identity, root_id, numerical,
        tuple(requirements[key] for key in sorted(requirements)), (connection,), tuple(sorted(proposals, key=lambda row: row.proposal_id)))


def project_initial_root_connection(record, requirement, connection):
    """A correct unresolved decision supplies the numerical procedure only."""
    exact(record, InitialRootScopedAssessment)
    if (requirement.requirement_id != 'requirement.' + record.request.object_id + '.exact-joint-decision'
            or connection.requirement_id != requirement.requirement_id
            or connection.claim_id != 'claim.' + record.request.object_id + '.conditional'
            or connection.assessment_operation_id not in (ASSESS, USE)
            or requirement.consumer_operation_id != connection.assessment_operation_id
            or connection.consumer_input_id != 'result'
            or connection.evidence_role is not ContributionRole.RETAINED_ANALYSIS_INPUT
            or connection.falsifier != requirement.falsifier or requirement.scope != record.scope):
        raise ValueError('initial root connection changes its independent numerical assessment scope')
    evidence = (record.identity,)
    return tuple(RequirementSupplyAssessment('assessment.' + record.fingerprint() + '.' + phase.value.lower(),
        ObjectIdentity.from_record(requirement.requirement_id, requirement),
        ObjectIdentity.from_record(connection.connection_id, connection), phase, record.numerical_disposition,
        record.request.object_id, evidence, record.findings,
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
        for phase in sorted(AssessmentPhase, key=lambda row: row.value))


def reconstruct_assessment(analysis, result, assessment):
    exact(result, InitialRootResult)
    exact(assessment, InitialRootAssessment)
    expected = assess_initial_root(result=result, **analysis_arguments(analysis))
    if assessment != expected:
        raise ValueError('initial root assessment differs from its independent frozen-input reconstruction')
    return expected
