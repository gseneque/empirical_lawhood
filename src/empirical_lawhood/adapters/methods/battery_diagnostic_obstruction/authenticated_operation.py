# SPDX-License-Identifier: MPL-2.0
"""One declared PURE reassessment with current original-custody authentication.

Scientific computation and output bytes remain owned by the historical assessor.
The old capability remains the reader for its already retained C5 attempt.
"""

from dataclasses import replace

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveInquiryHooks
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput

from . import contracts as c, operation_bindings as old, recursive_translation as translation, science
from .experiment_specification import AUTHENTICATED_NODE as NODE, AuthenticatedObstructionConfig
from .source_custody import authenticate_registered_source_custody


ORIGINAL_CUSTODY_REQUIREMENT = RegisteredPublicationRequirement(
    "battery.obstruction.complete-original-custody-and-current-unknown", authenticate_registered_source_custody)


def lower_authenticated_obstruction(source, parent, custody, *, draft_id):
    config = AuthenticatedObstructionConfig("config." + NODE, c.ObstructionOperationConfig("config." + old.NODE, source), custody)
    draft = translation.obstruction_draft_from_parent(source, parent=parent, draft_id=draft_id,
        config=config, registration=operation_declaration().registration(), node_id=NODE)
    expected = expected_external_inputs(config)
    actual = tuple(replace(row, maximum_size_bytes=None) for row in draft.external_inputs)
    if actual != tuple(replace(row, maximum_size_bytes=None) for row in expected):
        raise ValueError("authenticated obstruction parent changes the exact original native input artifact contract")
    return replace(draft, external_inputs=expected)


def expected_external_inputs(config):
    source = config.source
    science.validate_source(source)
    original, = (row for row in source.input_manifests if row.logical.payload_schema == source.prior_supply.object_schema
        and row.logical.content_sha256 == source.prior_supply.object_fingerprint)
    if (original.logical.profile is not ArtifactProfile.CANONICAL_JSON or original.logical.media_type != old.MEDIA
            or original.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or original.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("authenticated obstruction loses its exact original MODEL media, profile or exposed access")
    return (
        RecursiveExternalInput("external." + NODE + ".obstruction-source", source.source_id, source.SCHEMA, old.MEDIA,
            len(source.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
            source.fingerprint(), "SOURCE"),
        RecursiveExternalInput("external." + NODE + ".prior", original.logical.logical_artifact_id,
            source.prior_supply.object_schema, old.MEDIA, original.materialization.size_bytes,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
            source.prior_supply.object_fingerprint, "MODEL"),
    )


def _projection():
    return {"node_id": NODE, "config_type": AuthenticatedObstructionConfig,
        "registration": operation_declaration().registration()}


def scientific_root_validator(config, context):
    if (type(config) is not AuthenticatedObstructionConfig
            or context.root != translation.obstruction_development_root(config, study_id=context.root.study_id, node_id=NODE)
            or context.node_id != NODE or context.stage is not ScientificStage.FALSIFY
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.unit_ids != (c.UNIT,) or context.selected_unit_ids != (c.UNIT,) or context.complete_unit_census
            or context.qualifications or context.known_design_inputs
            or tuple((row.node_id, row.record) for row in context.config_inputs) != ((NODE, config),)
            or len(context.requirements) != 1 or len(context.connections) != 1):
        raise ValueError("authenticated obstruction changes its complete scientific root, source, stage or unit census")
    config.__post_init__()
    if context.external_inputs != expected_external_inputs(config):
        raise ValueError("authenticated obstruction changes its complete exact external source/MODEL contracts")
    requirement, connection = context.requirements[0], context.connections[0]
    if (requirement.requirement_id != "requirement." + NODE + ".prior-conditional-outcome"
            or requirement.consumer_operation_id != NODE or requirement.condition_role is not ConditionRole.EVIDENTIAL
            or requirement.purpose != old.QUESTION or requirement.condition != old.CONDITION
            or requirement.scope != science.scope(config.source) or requirement.assessment_operation_id != NODE
            or requirement.falsifier != old.FALSIFIER or requirement.permitted_roles != (ContributionRole.DESIGN_OPERAND,)
            or connection.connection_id != "connection." + NODE + ".prior-conditional-outcome"
            or connection.requirement_id != requirement.requirement_id or connection.supplier_operation_id is not None
            or connection.supplier_output_id is not None or connection.consumer_input_id != "prior"
            or connection.assessment_operation_id != NODE or connection.claim_id != "claim." + NODE
            or connection.evidence_role is not ContributionRole.DESIGN_OPERAND or connection.falsifier != old.FALSIFIER
            or connection.external_input_id != "external." + NODE + ".prior"
            or connection.supplier_contribution is None or connection.supplier_product_id is None):
        raise ValueError("authenticated obstruction changes its exact original MODEL requirement or parent connection")
    links = tuple(context.links)
    if (len(links) != len(old.PORTS) or {row.consumer_input_id for row in links} != {name for name, _ in old.PORTS}
            or any(row.consumer_node_id != NODE or row.external_input_id != "external." + NODE + "." + row.consumer_input_id
                or row.edge_id != "edge." + NODE + "." + row.consumer_input_id or row.producer_node_id is not None
                or row.scientific_role != ("MODEL" if row.consumer_input_id == "prior" else "SOURCE")
                or row.requirement_id != (requirement.requirement_id if row.consumer_input_id == "prior" else None)
                or row.connection_id != (connection.connection_id if row.consumer_input_id == "prior" else None)
                for row in links)):
        raise ValueError("authenticated obstruction changes SOURCE versus MODEL input roles or their complete graph")


def project_assessments(record, requirement, connection):
    return old.project_assessments(record, requirement, connection, node_id=NODE)


def describe_contributions(draft, products):
    return translation.describe_contributions(draft, products, **_projection())


def next_wave_builder(draft, manifest, products):
    if describe_contributions(draft, products) != (manifest,):
        raise ValueError("authenticated obstruction successor substitutes its actual retained history")
    return None


def inquiry_endpoint_validator(draft, endpoint):
    return translation.inquiry_endpoint_validator(draft, endpoint, **_projection())


def inquiry_outcome_projector(draft, specification, products):
    return translation.inquiry_outcome_projector(draft, specification, products, **_projection())


def inquiry_evidence_projector(draft, payloads, products=None):
    return translation.inquiry_evidence_projector(draft, payloads, products, **_projection())


class AuthenticatedObstructionRunner:
    @property
    def manifest(self):
        return operation_declaration().manifest()

    def execute(self, context):
        try:
            expected = {kind.SCHEMA: kind for kind in (AuthenticatedObstructionConfig, *(kind for _, kind in old.PORTS))}
            if (context.task_id != NODE or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != old.BUDGET
                    or len(context.input_ports) != len(expected) or {port.payload_schema for port in context.input_ports} != set(expected)):
                raise ValueError("authenticated obstruction changes its exact PURE task/config/input/resource census")
            records = {}
            for port in context.input_ports:
                if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type != old.MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("authenticated obstruction substitutes its original exposed canonical input contract")
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError("authenticated obstruction loses exact worker materialization bytes")
                records[port.payload_schema] = decode_canonical_bytes(raw, expected[port.payload_schema], maximum_bytes=len(raw))
            config = records[AuthenticatedObstructionConfig.SCHEMA]
            if ((context.config.config_id, context.config.config_schema, context.config.content_sha256) != (
                    config.config_id, config.SCHEMA, config.fingerprint())):
                raise ValueError("authenticated obstruction substitutes its full immutable scientific/custody configuration")
            inputs = {name: records[kind.SCHEMA] for name, kind in old.PORTS}
            if tuple(sorted((c.identity(record) for record in inputs.values()), key=lambda row: row.object_id)) != config.operands:
                raise ValueError("authenticated obstruction substitutes the exact original source or MODEL")
            product = science.assess(inputs["obstruction-source"], inputs["prior"])
            if (len(context.output_ports) != 1 or (context.output_ports[0].output_id, context.output_ports[0].payload_schema,
                    context.output_ports[0].profile, context.output_ports[0].media_type) != (
                    NODE + ".product", c.ObstructionAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, old.MEDIA)):
                raise ValueError("authenticated obstruction substitutes its unchanged complete history output contract")
            return RunnerResult((TaskOutputPayload(NODE + ".product", product.canonical_bytes()),),
                (ReceiptCheck("exact-authenticated-original-obstruction-history", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration():
    original = old.operation_manifests()[0]
    return RecursiveOperationDeclaration(NODE, "1.0.0", "original-custody-authenticated-retained-history-v1",
        CapabilityKind.ANALYSIS, AuthenticatedObstructionConfig, ScientificStage.FALSIFY,
        tuple(RecursivePortContract(name, kind.SCHEMA, old.MEDIA, None) for name, kind in old.PORTS),
        (OutputTemplate("product", c.ObstructionAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, old.MEDIA, ".json"),),
        original.permissions, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, old.BUDGET,
        ("complete-original-custody-and-current-unknown", "exact-source-model-roles", "unchanged-original-independent-assessor"),
        AuthenticatedObstructionRunner,
        {kind.SCHEMA: kind for kind in (AuthenticatedObstructionConfig, c.ObstructionAssessment, *(kind for _, kind in old.PORTS))},
        scientific_hooks=RecursiveScientificHooks(assessment_projector=project_assessments,
            scientific_operand_sha256s=old.scientific_operand_sha256s, scientific_unit_ids=old.scientific_unit_ids,
            scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions, next_wave_builder=next_wave_builder,
            inquiry_outcome_projector=inquiry_outcome_projector, inquiry_evidence_projector=inquiry_evidence_projector,
            inquiry_endpoint_validator=inquiry_endpoint_validator),
        publication_requirements=(ORIGINAL_CUSTODY_REQUIREMENT,),
        input_record_types=tuple(kind for _, kind in old.PORTS))
