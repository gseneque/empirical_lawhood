# SPDX-License-Identifier: MPL-2.0
"""Exact source guard counterexamples; synthetic qualification records only."""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
from empirical_lawhood.runtime.candidate_compiler import ContentIdentityPolicy, _source_diagnostics
from empirical_lawhood.runtime.capabilities import CapabilityPermission
from empirical_lawhood.runtime.plans import ScientificInputRole
from tests.runtime_platform.test_candidate_compiler import _fixture


def retained_history_source(*, visibility=VisibilityCeiling.PROSPECTIVE, development_permission=True):
    draft, context = _fixture()
    template = context.templates[0]
    original = template.graph.external_inputs[0]
    external = replace(original, scientific_role=ScientificInputRole.HISTORY,
        content_identity_policy=ContentIdentityPolicy.EXACT_SHA256, expected_content_sha256=context.qualifications[0].content_sha256,
        outcome_access=OutcomeAccess.EVALUATION_SEALED, visibility_ceiling=visibility)
    consumers = {edge.consumer_node_id for edge in template.graph.edges if edge.external_input_id == original.input_id}
    permissions = {CapabilityPermission.READ_SEALED_OUTCOMES}
    if visibility is VisibilityCeiling.DEVELOPMENT_ONLY and development_permission:
        permissions.add(CapabilityPermission.READ_DEVELOPMENT)
    protocol = replace(template.protocol, steps=tuple(replace(step,
        required_permissions=tuple(sorted({*step.required_permissions, *permissions})))
        if step.step_id in consumers else step for step in template.protocol.steps))
    steps = {step.step_id: step for step in protocol.steps}
    graph = replace(template.graph, external_inputs=(external,),
        nodes=tuple(replace(node, protocol_step_sha256=steps[node.node_id].fingerprint()) for node in template.graph.nodes),
        edges=tuple(replace(edge, scientific_role=ScientificInputRole.HISTORY,
            outcome_access=OutcomeAccess.EVALUATION_SEALED, visibility_ceiling=visibility)
            if edge.external_input_id == original.input_id else edge for edge in template.graph.edges))
    template = replace(template, protocol=protocol, graph=graph)
    materialization = replace(draft.source_materializations[0].materialization, object_schema=external.payload_schema)
    qualification = replace(context.qualifications[0], materialization=materialization,
        outcome_access=external.outcome_access, visibility_ceiling=visibility)
    source = replace(draft.source_materializations[0], role=SourceMaterializationRole.RETAINED_HISTORY,
        materialization=materialization, qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification))
    return replace(draft, source_materializations=(source,)), replace(context,
        qualifications=(qualification,), templates=(template,)), template


@pytest.mark.parametrize('visibility', (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY))
def test_exact_qualified_retained_history_preserves_its_history_role(visibility):
    draft, context, template = retained_history_source(visibility=visibility)
    diagnostics, accepted = _source_diagnostics(draft, context, template)
    assert diagnostics == []
    assert accepted == (draft.source_materializations[0].qualification_receipt,)
    assert template.graph.external_inputs[0].scientific_role is ScientificInputRole.HISTORY
    assert context.qualifications[0].visibility_ceiling is visibility


def test_retained_sealed_development_history_requires_both_consumer_permissions():
    draft, context, template = retained_history_source(
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY, development_permission=False)
    diagnostics, _ = _source_diagnostics(draft, context, template)
    assert any(row.field_path.endswith('.sealed-model') for row in diagnostics)


@pytest.mark.parametrize('visibility', (VisibilityCeiling.OUTCOME_VISIBLE,
    VisibilityCeiling.PRIVILEGED_TRUTH, VisibilityCeiling.UNBOUND_HISTORICAL))
def test_retained_sealed_history_cannot_reseal_exposed_or_unbound_ancestry(visibility):
    draft, context, template = retained_history_source(visibility=visibility)
    diagnostics, _ = _source_diagnostics(draft, context, template)
    assert any(row.field_path.endswith('.sealed-model') for row in diagnostics)


@pytest.mark.parametrize('mutation', ('qualification', 'model-label', 'hash', 'schema', 'unbounded',
                                    'weak-identity', 'visibility', 'consumer-permission', 'binary'))
def test_retained_sealed_source_needs_exact_scope_qualification_and_consumer_contract(mutation):
    draft, context, template = retained_history_source()
    source = draft.source_materializations[0]
    external = template.graph.external_inputs[0]
    if mutation == 'qualification':
        context = replace(context, qualifications=())
    elif mutation == 'model-label':
        draft = replace(draft, source_materializations=(replace(source, role=SourceMaterializationRole.NUMERICAL_CONFIGURATION),))
    elif mutation == 'hash':
        draft = replace(draft, source_materializations=(replace(source, content_sha256='b'*64),))
    elif mutation == 'schema':
        draft = replace(draft, source_materializations=(replace(source,
            materialization=replace(source.materialization, object_schema='empirical-lawhood/tests/foreign-history')),))
    elif mutation == 'consumer-permission':
        protocol = replace(template.protocol, steps=tuple(replace(step,
            required_permissions=tuple(value for value in step.required_permissions
                if value is not CapabilityPermission.READ_SEALED_OUTCOMES)) for step in template.protocol.steps))
        steps = {step.step_id: step for step in protocol.steps}
        template = replace(template, protocol=protocol, graph=replace(template.graph,
            nodes=tuple(replace(node, protocol_step_sha256=steps[node.node_id].fingerprint()) for node in template.graph.nodes)))
    elif mutation == 'binary':
        external = replace(external, media_type='application/x-npz')
        template = replace(template, graph=replace(template.graph, external_inputs=(external,),
            edges=tuple(replace(edge, media_type=external.media_type)
                if edge.external_input_id == external.input_id else edge for edge in template.graph.edges)))
    else:
        external = replace(external, **({'maximum_size_bytes': None} if mutation == 'unbounded' else
            {'content_identity_policy': ContentIdentityPolicy.RECEIPT_BOUND, 'expected_content_sha256': None}
            if mutation == 'weak-identity' else {'visibility_ceiling': VisibilityCeiling.DEVELOPMENT_ONLY}))
        graph = replace(template.graph, external_inputs=(external,), edges=tuple(replace(edge,
            maximum_size_bytes=external.maximum_size_bytes, visibility_ceiling=external.visibility_ceiling)
            if edge.external_input_id == external.input_id else edge for edge in template.graph.edges))
        template = replace(template, graph=graph)
    diagnostics, _ = _source_diagnostics(draft, context, template)
    assert diagnostics


def test_original_untagged_history_source_contract_is_not_reclassified():
    draft, context, template = retained_history_source()
    draft = replace(draft, source_materializations=())
    external = replace(template.graph.external_inputs[0], outcome_access=OutcomeAccess.OUTCOME_BLIND)
    template = replace(template, graph=replace(template.graph, external_inputs=(external,),
        edges=tuple(replace(edge, outcome_access=OutcomeAccess.OUTCOME_BLIND)
            if edge.external_input_id == external.input_id else edge for edge in template.graph.edges)))
    diagnostics, accepted = _source_diagnostics(draft, context, template)
    assert diagnostics == [] and accepted == ()
