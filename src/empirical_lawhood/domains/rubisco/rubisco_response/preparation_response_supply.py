# SPDX-License-Identifier: MPL-2.0
"""Destination admission of original preparation and six-question contributions.

This is a non-native scientific consumer. It distinguishes usable checkpoints,
an answered local question (which can be adverse), and the unchanged missing
kinetic or population requirements. Original molecular assessors own the values.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A, AssessmentPhase, ConditionRole, ContributionRole, RequirementSupplyAssessment, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import EnvironmentalPreparationResponseAssessment, PreparationResponseAssessment, require_response_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, EnvironmentalPreparationResponseDesign, PreparationResponseDesign, is_environmental, require_response_design, response_scope

CAPABILITY = 'rubisco-response.admit-preparation-response'
CLAIM = 'claim.preparation-response.local-supply'
UNIT = 'unit.one-matched-preparation-response-investigation'


@dataclass(frozen=True, slots=True)
class PreparationSupplySelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-supply-selection'
    design: PreparationResponseDesign | EnvironmentalPreparationResponseDesign
    prefixes: tuple[ActivePreparationPrefixReadout, ...]
    response: PreparationResponseAssessment | EnvironmentalPreparationResponseAssessment | None
    parents: tuple[ContributionManifest, ...]

    def __post_init__(self):
        require_response_design(self.design)
        if type(self.prefixes) is not tuple or len(self.prefixes) != 2:
            raise ValueError('local supply retains both originally assigned preparation results')
        for model, record in zip(MODELS, self.prefixes, strict=True):
            exact(record, ActivePreparationPrefixReadout)
            if record.original_result.prefix != self.design.prefix or record.original_result.model_name != model:
                raise ValueError('local supply substitutes the original paired preparation')
        if self.response is not None:
            require_response_assessment(self.response)
            if self.response.design != self.design:
                raise ValueError('local supply substitutes the original six-question design')
            from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import UNAVAILABLE_PREFIX_DECISION, assess_unavailable_preparation, response_supplier_decision
            if self.response.next_supplier_decision != response_supplier_decision(self.response):
                raise ValueError('local supply changes the original outcome-dependent consequence')
            if self.response.next_supplier_decision == UNAVAILABLE_PREFIX_DECISION:
                original = assess_unavailable_preparation(design=self.design, readouts=self.prefixes,
                    assessor_source=self.response.assessor_source, assessment_id=self.response.assessment_id)
                # Earlier records used UNAVAILABLE for all six rows. Their
                # quantities, original readout identities and costs still bind.
                if (self.response.quantities != original.quantities or
                        any((q.evidence, q.quantities) != (r.evidence, r.quantities)
                            for q, r in zip(self.response.questions, original.questions, strict=True))):
                    raise ValueError('unavailable response changes its original paired prefix evidence or costs')
        if (type(self.parents) is not tuple or not self.parents
                or tuple(p.contribution_id for p in self.parents) != tuple(sorted({p.contribution_id for p in self.parents}))):
            raise ValueError('local supply requires distinct ordered original contributions')
        for parent in self.parents:
            exact(parent, ContributionManifest)
        used = set()
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import selected_prefix_scope
        for record in self.records:
            parent, product = self.product(record)
            expected = selected_prefix_scope(self.design.prefix) if type(record) is ActivePreparationPrefixReadout else response_scope(self.design)
            if (parent.scope != expected or product.role is not ContributionRole.RETAINED_ANALYSIS_INPUT
                    or product.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                    or product.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or product.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                    or product.artifact.sha256 != record.fingerprint()
                    or product.artifact.size_bytes != record.canonical_size_bytes()):
                raise ValueError('local supply changes original contribution scope, bytes or evidence ceiling')
            used.add(parent.contribution_id)
        if used != {p.contribution_id for p in self.parents}:
            raise ValueError('local supply adds an unrelated contribution')

    @property
    def records(self):
        return (*self.prefixes, *((self.response,) if self.response is not None else ()))

    def product(self, record):
        matches = [(parent, product) for parent in self.parents for product in parent.products if product.record == record.identity]
        if len(matches) != 1:
            raise ValueError('local supply requires each exact original contribution product once')
        return matches[0]

    @property
    def identity(self):
        return ObjectIdentity.from_record('selection.preparation-supply.' + self.fingerprint(), self)

    @property
    def scope(self):
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import selected_prefix_scope
        return selected_prefix_scope(self.design.prefix) if self.response is None else response_scope(self.design)


def source_name(record):
    if type(record) is ActivePreparationPrefixReadout:
        return 'prefix.' + record.original_result.model_name
    require_response_assessment(record)
    return 'response-environment' if type(record) is EnvironmentalPreparationResponseAssessment else 'response'


def external_id(record):
    return 'external.preparation-supply.' + source_name(record)


def supply_graph(selection):
    """One real contribution edge for each destination condition.

    Revisions include the destination scope and original product fingerprint.
    Reusing a checkpoint at a response destination never changes its earlier
    preparation-admission requirement or the original contribution scope.
    """
    requirements, connections = [], []
    for record in selection.records:
        prefix = type(record) is ActivePreparationPrefixReadout
        name = source_name(record)
        key = name + '.' + selection.scope.fingerprint() + '.' + record.fingerprint()
        requirement = ScientificRequirementSpec('requirement.preparation-supply.' + key, CAPABILITY, ConditionRole.EVIDENTIAL,
            'Admit the exact original local operand without admitting the wider physical or kinetic claim.',
            ('Both initial and later accepted states of this assigned material are independently usable for the selected diagnostic.'
             if prefix else 'All six local response questions have complete independently assessable comparisons, including adverse findings.'),
            # This is the destination's usability condition. The original
            # contribution keeps its own scope, checked by the selection.
            selection.scope, CAPABILITY,
            'A changed source, missing state, rejected geometry, incomplete comparison or unresolved numerical attribution.',
            (ContributionRole.RETAINED_ANALYSIS_INPUT,))
        parent, product = selection.product(record)
        connection = ScientificConnectionSpec('connection.preparation-supply.' + key, requirement.requirement_id,
            None, None, name, CAPABILITY, CLAIM, ContributionRole.RETAINED_ANALYSIS_INPUT, requirement.falsifier,
            ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id, external_id(record))
        requirements.append(requirement)
        connections.append(connection)
    return tuple(sorted(requirements, key=lambda r: r.requirement_id)), tuple(sorted(connections, key=lambda r: r.connection_id))


def checkpoint_disposition(readout):
    assessment = readout.assessment
    if assessment is None or not assessment.complete_native_return_ledger:
        return A.UNEVALUABLE
    dispositions = {row.disposition for row in assessment.positions}
    if 'REJECTED' in dispositions:
        return A.FALSIFIED
    return A.SATISFIED if dispositions == {'AVAILABLE'} else A.UNEVALUABLE


def response_disposition(response):
    """A fully assessed adverse response answers a question, without endorsing it."""
    if any(q.assessable_comparisons != q.assigned_comparisons
           or q.disposition in {'UNAVAILABLE', 'NUMERICALLY_UNRESOLVED', 'OBSERVED_FINITE_MISMATCH_INCOMPLETE'}
           for q in response.questions):
        return A.UNEVALUABLE
    return A.SATISFIED


@dataclass(frozen=True, slots=True)
class PreparationSupplyResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-supply-result'
    result_id: str
    selection: PreparationSupplySelection
    checkpoint_dispositions: tuple[tuple[str, A], ...]
    response_disposition: A | None
    next_supplier_decision: str

    def __post_init__(self):
        validate_stable_id(self.result_id)
        exact(self.selection, PreparationSupplySelection)
        if (self.checkpoint_dispositions != tuple((m, checkpoint_disposition(r)) for m, r in zip(MODELS, self.selection.prefixes, strict=True))
                or self.response_disposition != (None if self.selection.response is None else response_disposition(self.selection.response))
                or self.next_supplier_decision != supply_consequence(self.selection)):
            raise ValueError('local destination assessment differs from its complete original findings')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


def supply_consequence(selection):
    if any(checkpoint_disposition(r) is not A.SATISFIED for r in selection.prefixes):
        return 'DECLINE_DIAGNOSTIC_WITHOUT_THE_COMPLETE_USABLE_PAIRED_HANDOFF'
    if selection.response is None:
        return ('ASSESS_SELECTED_EIGHT_INITIAL_PRIMARY_RETURNS_WITH_CURRENT_SPENDING_SUPERVISION'
            if is_environmental(selection.design) else
            'ASSESS_SELECTED_TWENTY_RETURN_DIAGNOSTIC_WITH_CURRENT_SPENDING_SUPERVISION')
    return selection.response.next_supplier_decision


def assess_supply(selection):
    exact(selection, PreparationSupplySelection)
    return PreparationSupplyResult('assessment.preparation-supply.' + selection.fingerprint(), selection,
        tuple((m, checkpoint_disposition(r)) for m, r in zip(MODELS, selection.prefixes, strict=True)),
        None if selection.response is None else response_disposition(selection.response), supply_consequence(selection))


def project_supply_assessments(record, requirement, connection):
    exact(record, PreparationSupplyResult)
    requirements, connections = supply_graph(record.selection)
    if requirement not in requirements or connection not in connections or connection.requirement_id != requirement.requirement_id:
        raise ValueError('local supply changes its actual source-to-destination connection')
    source = next(r for r in record.selection.records if source_name(r) == connection.consumer_input_id)
    disposition = checkpoint_disposition(source) if type(source) is ActivePreparationPrefixReadout else response_disposition(source)
    return tuple(RequirementSupplyAssessment(
        'assessment.local-supply.' + record.fingerprint() + '.' + source_name(source) + '.' + phase.value.lower(),
        ObjectIdentity.from_record(requirement.requirement_id, requirement),
        ObjectIdentity.from_record(connection.connection_id, connection), phase,
        A.SATISFIED if phase is AssessmentPhase.PROCEDURE else disposition,
        record.selection.design.identity.object_id, (record.identity,),
        ('complete-original-local-assessment-without-kinetic-admission',) if disposition is A.SATISFIED else
        ('original-local-supply-' + disposition.value.lower(),)) for phase in sorted(AssessmentPhase, key=lambda p: p.value))
