# SPDX-License-Identifier: MPL-2.0
"""Derived v2 capability and graph ports over the retained nine-stage declaration.

Only changed compiler/receiver payloads and explicit canonical custody are
projected here. Scientific stages, obligations, permissions, barriers, resource
budgets and all ordinary model/source ports retain their original owners.
"""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.candidate_compiler import CandidateGraphEdge, CandidateGraphExternalInput, ScientificInputRole, ContentIdentityPolicy
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.plans import OutputTemplate

from . import protocol as original_protocol
from . import records as old
from .config_v2 import VirtualCellPipelineSelectionV2
from .contracts import ProvenanceBoundVirtualCellPipelineConfig
from .correction_records_v2 import OfficialMetricSetV2
from .custody_transport_v2 import CanonicalEvidenceV2, MAXIMUM_CUSTODY_BYTES_V2
from .records_v2 import ModelDevelopmentRecordV2, ModelSelectionRecordV2, PredictionFreezeRecordV2, OfficialEvaluationRecordV2, RAW_PREDICTION_DELTAS_SCHEMA
from .registry import virtual_cell_capability_registry

CAPABILITY_VERSION_V2 = "2.0.0"
ORIGINAL_CONFIG_INPUT_ID_V2 = "input.virtual-cell-2025-original-config-v1"
CONFIG_SCHEMA_SHA256_V2 = sha256(VirtualCellPipelineSelectionV2.SCHEMA.encode()).hexdigest()

SCHEMA_SUCCESSORS_V2 = {
    old.ModelDevelopmentRecord.SCHEMA: ModelDevelopmentRecordV2.SCHEMA,
    old.ModelSelectionRecord.SCHEMA: ModelSelectionRecordV2.SCHEMA,
    old.PredictionFreezeRecord.SCHEMA: PredictionFreezeRecordV2.SCHEMA,
    old.OfficialEvaluationRecord.SCHEMA: OfficialEvaluationRecordV2.SCHEMA,
    old.OFFICIAL_METRICS_TABLE_SCHEMA: OfficialMetricSetV2.SCHEMA,
    old.PREDICTED_MEAN_TABLE_SCHEMA: RAW_PREDICTION_DELTAS_SCHEMA,
}


def virtual_cell_capability_registry_v2(implementation_sha256_by_key):
    original = virtual_cell_capability_registry(implementation_sha256_by_key)
    capabilities = []
    for manifest in original.capabilities:
        inputs = {SCHEMA_SUCCESSORS_V2.get(value, value) for value in manifest.input_schema_ids}
        inputs.update((CanonicalEvidenceV2.SCHEMA, ProvenanceBoundVirtualCellPipelineConfig.SCHEMA))
        outputs = {SCHEMA_SUCCESSORS_V2.get(value, value) for value in manifest.output_schema_ids}
        outputs.add(CanonicalEvidenceV2.SCHEMA)
        capabilities.append(replace(manifest, capability_version=CAPABILITY_VERSION_V2,
            config_schema=VirtualCellPipelineSelectionV2.SCHEMA, config_schema_sha256=CONFIG_SCHEMA_SHA256_V2,
            input_schema_ids=tuple(sorted(inputs)), output_schema_ids=tuple(sorted(outputs))))
    return CapabilityRegistry(original.registry_id + "-v2", tuple(capabilities))


def virtual_cell_config_ref_v2(selection):
    return CapabilityConfigRef(selection.selection_id, selection.SCHEMA, CONFIG_SCHEMA_SHA256_V2,
        selection.fingerprint(), original_protocol.CONFIG_ARTIFACT_ID)


def project_protocol_v2(protocol, *, selection):
    """Derive changed ports and retain every scientific stage/permission."""
    selection.__post_init__()
    original_steps = {value.step_id: value for value in protocol.steps}
    steps = []
    for step in protocol.steps:
        ancestors = set()
        pending = list(step.dependency_step_ids)
        while pending:
            ancestor = pending.pop()
            if ancestor not in ancestors:
                ancestors.add(ancestor)
                pending.extend(original_steps[ancestor].dependency_step_ids)
        outputs = []
        for output in step.outputs:
            schema = SCHEMA_SUCCESSORS_V2.get(output.payload_schema, output.payload_schema)
            if output.payload_schema == old.OFFICIAL_METRICS_TABLE_SCHEMA:
                output = replace(output, payload_schema=schema, profile=ArtifactProfile.CANONICAL_JSON,
                    media_type="application/json", filename_suffix=".json")
            elif output.payload_schema == old.PREDICTED_MEAN_TABLE_SCHEMA:
                output = replace(output, output_id="predicted-deltas", payload_schema=schema,
                    profile=ArtifactProfile.RAW_SOURCE_BYTES, media_type="application/octet-stream", filename_suffix=".bin")
            else:
                output = replace(output, payload_schema=schema)
            outputs.append(output)
        outputs.append(OutputTemplate("custody-evidence", CanonicalEvidenceV2.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        steps.append(replace(step, capability_version=CAPABILITY_VERSION_V2,
            config=virtual_cell_config_ref_v2(selection), dependency_step_ids=tuple(sorted(ancestors)),
            outputs=tuple(sorted(outputs, key=lambda row: row.output_id))))
    return replace(protocol, template_id=protocol.template_id + "-v2", template_version=CAPABILITY_VERSION_V2,
        steps=tuple(steps))


def project_graph_v2(graph, *, protocol, registry, original_config, selection):
    """Derive new schema and exact dependency sidecar bindings from one graph.

    Earlier canonical records travel through referenced sidecars. Every
    descendant receives each ancestor's sidecar once; completed array/model
    artifacts continue through the original, separately authenticated ports.
    """
    selection.validate_original(original_config)
    steps = {value.step_id: value for value in protocol.steps}
    if set(steps) != {value.node_id for value in graph.nodes}:
        raise ValueError("corrected graph and protocol differ on scientific stages")
    nodes = []
    for node in graph.nodes:
        step = steps[node.node_id]
        manifest = registry.resolve(step.capability_key, step.capability_version)
        nodes.append(replace(node, capability_version=CAPABILITY_VERSION_V2,
            implementation_sha256=manifest.implementation_sha256, protocol_step_sha256=step.fingerprint()))
    edges = [replace(edge, payload_schema=SCHEMA_SUCCESSORS_V2.get(edge.payload_schema, edge.payload_schema),
        media_type=("application/json" if edge.payload_schema == old.OFFICIAL_METRICS_TABLE_SCHEMA else edge.media_type))
        for edge in graph.edges]
    original_external = CandidateGraphExternalInput(ORIGINAL_CONFIG_INPUT_ID_V2,
        ScientificInputRole.MODEL, ORIGINAL_CONFIG_INPUT_ID_V2,
        ContentIdentityPolicy.EXACT_SHA256, original_config.fingerprint(), original_config.SCHEMA,
        "application/json", len(original_config.canonical_bytes()), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    for step in protocol.steps:
        edges.append(CandidateGraphEdge("edge.original-config." + step.step_id, None, None,
            ORIGINAL_CONFIG_INPUT_ID_V2, step.step_id, "original-config-v1", ScientificInputRole.MODEL,
            ORIGINAL_CONFIG_INPUT_ID_V2, original_config.SCHEMA, "application/json", len(original_config.canonical_bytes()),
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, step.barrier))
        pending = list(step.dependency_step_ids)
        ancestors = set()
        while pending:
            ancestor = pending.pop()
            if ancestor not in ancestors:
                ancestors.add(ancestor)
                pending.extend(steps[ancestor].dependency_step_ids)
        for ancestor in sorted(ancestors):
            source = steps[ancestor]
            edges.append(CandidateGraphEdge("edge.custody." + ancestor + "." + step.step_id,
                ancestor, "custody-evidence", None, step.step_id, "custody-" + ancestor, ScientificInputRole.QUALIFICATION,
                "artifact." + ancestor + ".custody-evidence", CanonicalEvidenceV2.SCHEMA, "application/json",
                MAXIMUM_CUSTODY_BYTES_V2, source.requested_outcome_access, source.visibility_ceiling, step.barrier))
    return replace(graph, graph_id=graph.graph_id + "-v2",
        external_inputs=tuple(sorted((*graph.external_inputs, original_external), key=lambda row: row.input_id)),
        nodes=tuple(nodes), edges=tuple(sorted(edges, key=lambda row: row.edge_id)))


def project_template_v2(template, *, registry, original_config, selection):
    """Bind the corrected declaration through the existing StudyTemplate type."""
    protocol = project_protocol_v2(template.protocol, selection=selection)
    graph = project_graph_v2(template.graph, protocol=protocol, registry=registry,
        original_config=original_config, selection=selection)
    incoming = {step.step_id: tuple(sorted(edge.edge_id for edge in graph.edges
        if edge.consumer_node_id == step.step_id)) for step in protocol.steps}
    coverage = replace(template.coverage, coverage_id=template.coverage.coverage_id + "-v2",
        bindings=tuple(replace(value,
            required_output_id=("predicted-deltas" if value.required_output_id == "predicted-means" else value.required_output_id),
            contributor_edge_ids=incoming[value.proof_owner_node_id]) for value in template.coverage.bindings))
    return replace(template, template_key=template.template_key + "-v2", template_version=CAPABILITY_VERSION_V2,
        protocol=protocol, graph=graph, coverage=coverage)
