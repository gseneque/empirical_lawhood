# SPDX-License-Identifier: MPL-2.0
"""Derive the selected complete response stage through shared recursive authoring."""

from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursiveScientificRootPreparationContext
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_effects
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import UNIT, capability_for, design_input_name, diagnostic_input_name, node_id, operands, operation_declaration, resource_budget, selected_request


def validate_configs(configs):
    if type(configs) is not tuple or not configs:
        raise ValueError('response stage requires its complete prospectively selected effect census')
    for config in configs:
        capability_for(config)
    first = configs[0]
    if (tuple(c.point.effect for c in configs) != response_effects(first.protocol, first.point.effect.stage)
            or any(c.protocol != first.protocol or c.preparation_parent != first.preparation_parent
                or c.diagnostic != first.diagnostic or c.diagnostic_parent != first.diagnostic_parent
                or c.original.implementation != first.original.implementation or c.ACCELERATED != first.ACCELERATED
                or resource_budget(c) != resource_budget(first) for c in configs)):
        raise ValueError('response stage changes its complete effect census, source or allocation')
    for model in ('m1-i95m', 'm1-wt'):
        rows = [c for c in configs if c.center.model_name == model]
        if any(c.original != rows[0].original or c.frame != rows[0].frame for c in rows):
            raise ValueError('response stage changes a genotype operator or fixed initial chemical frame')
        for position in {c.center.position for c in rows}:
            centers = [c.center for c in rows if c.center.position == position]
            if any(c != centers[0] for c in centers):
                raise ValueError('response stage changes an originally selected checkpoint')
    if len({c.original.work_directory for c in configs}) != 2:
        raise ValueError('response stage requires separate native work directories for both genotypes')
    return first


def input_selections(config):
    original = config.original
    rows = (('native-arrays', config.center.arrays.identity, config.center.arrays.canonical_size_bytes()),
        ('native-center', config.center.identity, config.center.canonical_size_bytes()),
        ('native-checkpoint', config.center.checkpoint.identity, config.center.checkpoint.canonical_size_bytes()),
        ('native-center-bytes', config.center.center_bytes, config.center.arrays.size_bytes),
        (design_input_name(config), config.protocol.identity, config.protocol.canonical_size_bytes()),
        ('native-frame', config.frame.identity, config.frame.canonical_size_bytes()),
        ('native-model', original.selection.representation, original.representation_size_bytes),
        ('native-point', config.point.identity, config.point.canonical_size_bytes()),
        ('native-prototype', original.selection.identity, original.selection.canonical_size_bytes()),
        ('native-provenance', original.provenance.identity, original.provenance.canonical_size_bytes()),
        ('native-request', selected_request(config).identity, selected_request(config).canonical_size_bytes()),
        ('native-source', original.raw_sources, original.raw_source_size_bytes),
        ('original-preparation-assessment', config.center.original_readout.identity, config.center.original_readout.canonical_size_bytes()),
        *(((diagnostic_input_name(config), config.diagnostic.identity, config.diagnostic.canonical_size_bytes()),)
            if config.diagnostic is not None else ()))
    return tuple(sorted(rows, key=lambda row: row[0]))


def external_id(config, name):
    pin = next(pin for role, pin, _ in input_selections(config) if role == name)
    return 'external.preparation-response.' + name + '.' + pin.object_fingerprint


def native_external_inputs(configs):
    validate_configs(configs)
    rows = {}
    for config in configs:
        for name, pin, size in input_selections(config):
            key = external_id(config, name)
            parent = history_parent(config, name)
            original = parent is not None
            product = next(p for p in parent.products if p.record == pin) if original else None
            rows[key] = RecursiveExternalInput(key, pin.object_id if product is None else product.artifact.artifact_id,
                pin.object_schema, 'application/octet-stream' if name == 'native-center-bytes' else 'application/json', size,
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, pin.object_fingerprint,
                'HISTORY' if original else 'SOURCE')
    return tuple(rows[key] for key in sorted(rows))


def native_input_links(configs):
    return tuple(sorted((RecursiveInputLink('edge.' + node_id(c) + '.' + name, node_id(c), name,
        external_input_id=external_id(c, name), scientific_role='HISTORY' if history_parent(c, name) is not None else 'SOURCE')
        for c in configs for name, _, _ in input_selections(c)), key=lambda row: row.edge_id))


def history_parent(config, name):
    if name == 'original-preparation-assessment':
        return config.preparation_parent
    if name == diagnostic_input_name(config):
        return config.diagnostic_parent
    return None


def contribution_parents(config):
    return tuple(sorted((p for p in (config.preparation_parent, config.diagnostic_parent) if p is not None),
        key=lambda p: p.contribution_id))


def development_root(configs, *, study_id):
    first = validate_configs(configs)
    views = tuple(sorted('view.' + c.point.effect.effect_id for c in configs))
    claim = ClaimSpec('claim.preparation-response.' + first.point.effect.stage, 'world.periodic-gp-preparation-response',
        'population.one-matched-construction-no-biological-replicates',
        'Does allowed preparation improve the finite signed formation-force prediction, and which limitation is consequential?',
        'One matched M1 construction, four nested positions, zero biological replicates; four materials, 32 sites and 384 starts remain assigned.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Numerical comparisons and actual finite challenges do not establish a rigorous derivative enclosure, ensemble, population or kinetic contrast.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    pins = tuple(sorted({pin for c in configs for pin in operands(c)}, key=lambda p: p.object_id))
    return DevelopmentStudySpec(study_id, claim.proposition, first.protocol.identity, claim.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), views, (claim,), pins)


@dataclass(frozen=True, slots=True, eq=False)
class ResponseRootPreparation:
    batch: RecursiveScientificRootPreparationContext
    configs: object


def prepare_root(batch):
    if type(batch) is not RecursiveScientificRootPreparationContext or type(batch.root) is not DevelopmentStudySpec:
        raise ValueError('response stage requires its original development root')
    configs = tuple(row.record for row in batch.config_inputs)
    validate_configs(configs)
    if (tuple(row.node_id for row in batch.config_inputs) != tuple(node_id(c) for c in configs)
            or batch.root != development_root(configs, study_id=batch.root.study_id)
            or batch.external_inputs != native_external_inputs(configs) or batch.links != native_input_links(configs)
            or batch.requirements or batch.connections
            or any(units != (UNIT,) for units in batch.selected_unit_ids_by_selection.values())):
        raise ValueError('response stage changes its selected original graph or scientific census')
    return ResponseRootPreparation(batch, MappingProxyType({node_id(c): c for c in configs}))


def validate_root(config, context):
    selected = context.scientific_preparation
    if (type(selected) is not ResponseRootPreparation or selected.configs.get(context.node_id) is not config
            or context.root is not selected.batch.root or context.config_inputs is not selected.batch.config_inputs
            or context.links is not selected.batch.links or context.external_inputs is not selected.batch.external_inputs
            or context.requirements is not selected.batch.requirements or context.connections is not selected.batch.connections
            or context.node_id != node_id(config) or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('response point changes its prepared original task scope')


def preparation_response_draft(configs, *, draft_id=None):
    first = validate_configs(configs)
    draft_id = ('draft.preparation-response.' + first.point.effect.stage + '.' + first.protocol.fingerprint()
                if draft_id is None else draft_id)
    root = development_root(configs, study_id='study.' + draft_id)
    budget = resource_budget(first)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.' + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.' + draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    selection = operation_declaration(accelerated=first.ACCELERATED).registration().selection
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node_id(c), selection=selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.' + node_id(c) + '.complete-original-response',),
        resource_budget=resource_budget(c), resource_lock_ids=('gp-periodic-force-native-worker',), maximum_attempts=1) for c in configs)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), operations, native_external_inputs(configs),
        native_input_links(configs), tuple(node_id(c) for c in configs), development_study=root,
        contribution_parents=contribution_parents(first))


def _selection_preparation():
    from empirical_lawhood.execution.recursive_inquiry_selection import InquirySelectionPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import config_type
    return InquirySelectionPreparation(_decode_selected_configs, tuple(config_type(flag) for flag in (False, True)),
        (validate_configs, preparation_response_draft))


def selection_scope(draft):
    return _selection_preparation().scope(draft)


def selected_configs(draft):
    return _selection_preparation().read(draft)


def _decode_selected_configs(draft):
    from empirical_lawhood.science.records.decoded_record_store import decode_scoped_canonical_bytes
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import config_type
    kinds = tuple(config_type(flag) for flag in (False, True))
    rows = []
    for operation in draft.operations:
        kind = next((k for k in kinds if operation.config_identity.object_schema == k.SCHEMA), None)
        if kind is None:
            raise ValueError('response inquiry changes its registered operation or revision')
        rows.append(decode_scoped_canonical_bytes(operation.config_payload.encode(), kind, maximum_bytes=64 * 2**20))
    configs = tuple(rows)
    validate_configs(configs)
    if draft != preparation_response_draft(configs, draft_id=draft.draft_id):
        raise ValueError('response inquiry changes its original complete stage graph')
    return configs


def response_input_origins(draft):
    from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    parents = contribution_parents(selected_configs(draft)[0])
    rows = []
    for external in draft.external_inputs:
        if external.scientific_role == 'HISTORY':
            parent, product = next((parent, p) for parent in parents for p in parent.products
                if p.artifact.artifact_id == external.logical_artifact_id)
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.CONTRIBUTION,
                product.record.object_fingerprint, product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent),
                product.product_id, product.producing_receipt))
        else:
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.SOURCE,
                external.expected_content_sha256, external.scientific_role))
    result = RecursiveInputOrigins(tuple(rows))
    result.validate_draft(draft)
    return result
