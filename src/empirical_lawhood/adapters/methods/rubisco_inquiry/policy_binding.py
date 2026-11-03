# SPDX-License-Identifier: MPL-2.0
"""Wilson analytic policy contracts; conditional arithmetic leaves biology open."""

from dataclasses import replace

from empirical_lawhood.adapters.methods.compact_inquiry_policy import (
    bind_assessed_use, bind_policy_campaign, compact_input_origins, compact_policy_menu,
    compact_policy_specification, compact_scientific_work, connection_contracts, project_analytic_connection,
)
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.recursive_inquiry import identity
from .operation_bindings import NAMESPACE, InquiryOperationConfig, record_identity, supported_development_root
from .recursive_translation import supply_draft, use_draft
from .science import RubiscoAssessment, RubiscoSupply


def contracts(scope, parent=None):
    return connection_contracts(namespace=NAMESPACE, scope=scope, parent=parent,
        application_condition="Both specified turnover and specificity endpoints in one enzyme under declared compatible assay conditions; biological preparation and the paired assay bridge remain unresolved by Wilson conditional arithmetic.")


def policy_supply_draft(article, genbank, *, draft_id="draft.rubisco-inquiry.policy-supply"):
    draft = supply_draft(article, genbank, draft_id=draft_id)
    requirements, connection = contracts(draft_scope(draft))
    return bind_policy_campaign(replace(draft, requirements=requirements, connections=(connection,)), draft_scope(draft))


def draft_scope(draft):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from .operation_bindings import InquiryOperationConfig
    from .science import scope
    config = decode_canonical_bytes(draft.operations[0].config_payload.encode(), InquiryOperationConfig, maximum_bytes=None)
    return scope(config.scientific_design)


def assessed_use_draft(supplier, candidate=None, *, parent, draft_id="draft.rubisco-inquiry.assessed-use"):
    requirements, connection = contracts(supplier.scope, parent)
    return bind_assessed_use(use_draft(supplier, candidate, parent=parent, draft_id=draft_id),
                             requirements=requirements, connection=connection)


def inquiry_specification(source_draft, *, specification_id, stage, parent=None,
                          previous=None, assessed_draft=None):
    """Freeze the paired enzyme target and this exact conditional prerequisite."""
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    if len(source_draft.operations) != 1 or source_draft.selected_operation_ids != (source_draft.operations[0].node_id,):
        raise ValueError("Rubisco policy needs its exact selected supplier operation")
    config = decode_canonical_bytes(source_draft.operations[0].config_payload.encode(), InquiryOperationConfig,
                                   maximum_bytes=None)
    requirements, connection = contracts(draft_scope(source_draft), parent)
    if (config.operation != "supply" or not supported_development_root(config, source_draft.development_study)
            or source_draft.requirements != requirements):
        raise ValueError("Rubisco policy changes its original source or scientific requirements")
    return compact_policy_specification(namespace=NAMESPACE, source_draft=source_draft,
        specification_id=specification_id, stage=stage, requirements=requirements, connection=connection,
        previous=previous, assessed_draft=assessed_draft)


def inquiry_menu(specification, state, *, stage, record=None, next_draft=None, parent=None, assessments=()):
    """Use the held conditional verdict while retaining the biological bridge."""
    expected = None if stage == "origin" else RubiscoSupply if stage == "later" else RubiscoAssessment
    if ((record is not None if expected is None else type(record) is not expected)
            or (record is not None and record.scope != specification.endpoint)
            or (specification.requirements, specification.connections) != (
                contracts(specification.endpoint, parent)[0], (contracts(specification.endpoint, parent)[1],))):
        raise ValueError("Rubisco menu changes its typed source, candidate or connection")
    if stage in {"origin", "later"}:
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        if next_draft is None or len(next_draft.operations) != 1:
            raise ValueError("Rubisco menu needs its exact selected stage operation")
        config = decode_canonical_bytes(next_draft.operations[0].config_payload.encode(), InquiryOperationConfig,
            maximum_bytes=None)
        if config.operation != ("supply" if stage == "origin" else "use"):
            raise ValueError("Rubisco menu changes its exact supply/independent-use stage")
    outcome = ("initial" if record is None else "useful-supply"
        if record.disposition is AssessmentDisposition.SATISFIED else "unresolved"
        if record.disposition is AssessmentDisposition.UNEVALUABLE else "scoped-failure")
    return compact_policy_menu(namespace=NAMESPACE, specification=specification, state=state,
        stage=stage, outcome_id=outcome, record_identity=record_identity, record=record,
        next_draft=next_draft, parent=parent, assessments=assessments, work_projector=scientific_work)


def scientific_work(draft, operation_id):
    """Exact Wilson design/assembly/endpoint operation; config labels grant no novelty."""
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from .operation_bindings import operation_registrations
    from .science import scope
    selected = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    if len(selected) != 1 or selected[0].node_id != operation_id:
        raise ValueError("Rubisco work needs its complete single selected operation")
    operation = selected[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), InquiryOperationConfig, maximum_bytes=None)
    if (operation.config_identity != identity(config, config.config_id)
            or not any(row.selection == operation.selection for row in operation_registrations())
            or not supported_development_root(config, draft.development_study)
            or operation.node_id != f"{NAMESPACE}.{config.operation}"):
        raise ValueError("Rubisco work substitutes exact configuration/code/scientific root")
    return compact_scientific_work(namespace=NAMESPACE, operation=operation, config=config,
        scope=scope(config.scientific_design), output_type=RubiscoSupply if config.operation == "supply" else RubiscoAssessment,
        scientific_design=identity(config.scientific_design, config.scientific_design.science_id))


input_origins = compact_input_origins


def assessment_projector(record, requirement, connection):
    if type(record) is not RubiscoAssessment:
        raise ValueError("Rubisco independent connection assessment requires its typed consumer result")
    if requirement != contracts(record.scope)[0][-1]:
        raise ValueError("Rubisco assessment changes the complete declared conditional requirement")
    # The separately supplied candidate/held-label endpoints are tested by two
    # noncompensating ratios. Constructor producer validation is not the oracle.
    admission = (record.disposition if record.disposition in {
        AssessmentDisposition.REFUSED, AssessmentDisposition.UNEVALUABLE,
    } else AssessmentDisposition.SATISFIED)
    return project_analytic_connection(namespace=NAMESPACE, record=record,
        requirement=requirement, connection=connection, record_identity=record_identity,
        admission=admission, joined=record.disposition, reason_codes=record.reason_codes,
        instance_id=record.candidate.candidate_id)
