# SPDX-License-Identifier: MPL-2.0
"""Derive paired prefix nodes and complete inputs through shared authoring."""

from dataclasses import dataclass
from hashlib import sha256
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
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import UNIT, capability_for, input_artifact_id, node_id, operands, operation_declaration, resource_budget
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_translation import input_selections as relaxation_input_selections


def validate_configs(configs):
    if type(configs) is not tuple or len(configs) != 2:
        raise ValueError('preparation prefix requires both originally assigned M1 materials')
    for config in configs:
        capability_for(config)
    first = configs[0]
    if (tuple(c.original.model_name for c in configs) != ('m1-i95m', 'm1-wt')
            or any(c.prefix != first.prefix or c.original.plan != first.original.plan
                   or c.scientific_context != first.scientific_context
                   or c.original.implementation != first.original.implementation
                   or hasattr(c, 'continuation') != hasattr(first, 'continuation')
                   or c.ACCELERATED != first.ACCELERATED or resource_budget(c) != resource_budget(first) for c in configs)
            or len({c.original.work_directory for c in configs}) != 2):
        raise ValueError('preparation prefix changes paired source, allowance or separate work custody')
    return first


def input_selections(config):
    context = config.scientific_context
    continuation = getattr(config, 'continuation', None)
    if continuation is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_prefix_config
        first = original_prefix_config(config)
    return tuple(sorted((*relaxation_input_selections(config.original),
        ('native-prefix-selection', config.prefix.identity, config.prefix.canonical_size_bytes()),
        ('native-relaxation-selection', config.original.identity, config.original.canonical_size_bytes()),
        *((('native-continuation', continuation.identity, continuation.canonical_size_bytes()),
           ('native-original-prefix-config', first.identity, first.canonical_size_bytes()),
           ('original-prefix-assessment', continuation.readout.identity, continuation.readout.canonical_size_bytes()),
           ('native-continuation-archive', continuation.archive_identity, continuation.archive.materialization.size_bytes))
          if continuation is not None else ()),
        *((('native-response-context', context.identity, context.canonical_size_bytes()),
           ('original-root-assessment', context.original_root.identity, context.original_root.canonical_size_bytes()))
           if context is not None else ())), key=lambda r: r[0]))


def external_id(config, name):
    suffix = '' if name in {'native-plan', 'native-prefix-selection', 'native-conditional-selection',
                           'native-response-context', 'original-root-assessment'} else '.' + config.original.model_name
    return 'external.active-prefix.' + name + suffix


def native_external_inputs(configs):
    validate_configs(configs)
    rows = {}
    for config in configs:
        for name, pin, size in input_selections(config):
            key = external_id(config, name)
            parent = (config.scientific_context.parent if name == 'original-root-assessment' else
                      config.continuation.parent if name == 'original-prefix-assessment' else None)
            row = RecursiveExternalInput(key, input_artifact_id(config, name, pin),
                pin.object_schema, 'application/gzip' if name == 'native-continuation-archive' else 'application/json', size, OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY, pin.object_fingerprint, 'SOURCE' if parent is None else 'HISTORY')
            if key in rows and rows[key] != row:
                raise ValueError('preparation prefix substitutes a shared original input')
            rows[key] = row
    return tuple(rows[key] for key in sorted(rows))


def native_input_links(configs):
    return tuple(sorted((RecursiveInputLink('edge.' + node_id(config) + '.' + name, node_id(config), name,
        external_input_id=external_id(config, name), scientific_role='HISTORY' if
            name == 'original-root-assessment' or name == 'original-prefix-assessment' and config.continuation.parent is not None else 'SOURCE')
        for config in configs for name, _, _ in input_selections(config)), key=lambda row: row.edge_id))


def development_root(configs, *, study_id):
    base = validate_configs(configs)
    views = tuple(sorted('view.active-prefix.' + c.original.model_name + '.' + position
                         for c in configs for position in ('initial', 'later')))
    claim = ClaimSpec('claim.active-prefix.preparation', 'world.periodic-gp-preparation-prefix',
        'population.one-source-assembly-matched-chemical-starts',
        'Which initial and later accepted preparation states are available within the original paired purchase?',
        'One assigned matched construction; four nested state positions and zero independent biological replicates. '
        'The original four materials, 32 sites and 384 starting hypotheses remain in their complete denominator.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'A finite preparation prefix establishes no stationary endpoint, equilibrium population, physical time or kinetic contrast.',
        ('assumption.selected-periodic-qmmm-reference-potential',), numerical_view_ids=views)
    sources = tuple(sorted({pin for c in configs for pin in operands(c)}, key=lambda p: p.object_id))
    return DevelopmentStudySpec(study_id, claim.proposition, base.prefix.identity, claim.world_id,
        WorldKind.NUMERICAL_SIMULATOR, (UNIT,), views, (claim,), sources)


@dataclass(frozen=True, slots=True, eq=False)
class PrefixRootPreparation:
    batch: RecursiveScientificRootPreparationContext
    configs: object


def prepare_root(batch):
    if type(batch) is not RecursiveScientificRootPreparationContext or type(batch.root) is not DevelopmentStudySpec:
        raise ValueError('preparation prefix requires its complete original development graph')
    configs = tuple(row.record for row in batch.config_inputs)
    validate_configs(configs)
    if (tuple(row.node_id for row in batch.config_inputs) != tuple(node_id(c) for c in configs)
            or batch.root != development_root(configs, study_id=batch.root.study_id)
            or batch.external_inputs != native_external_inputs(configs) or batch.links != native_input_links(configs)
            or batch.requirements or batch.connections
            or any(units != (UNIT,) for units in batch.selected_unit_ids_by_selection.values())):
        raise ValueError('preparation prefix changes the selected paired graph or complete native denominator')
    return PrefixRootPreparation(batch, MappingProxyType({node_id(c): c for c in configs}))


def validate_root(config, context):
    selected = context.scientific_preparation
    if (type(selected) is not PrefixRootPreparation or selected.configs.get(context.node_id) is not config
            or context.root is not selected.batch.root or context.config_inputs is not selected.batch.config_inputs
            or context.links is not selected.batch.links or context.external_inputs is not selected.batch.external_inputs
            or context.requirements is not selected.batch.requirements or context.connections is not selected.batch.connections
            or context.node_id != node_id(config) or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('preparation prefix changes its original scientific task scope')


def active_preparation_prefix_draft(configs, *, draft_id=None):
    base = validate_configs(configs)
    continued = hasattr(base, 'continuation')
    if draft_id is None:
        draft_id = ('draft.continued-active-prefix.' + sha256(''.join(c.fingerprint() for c in configs).encode()).hexdigest()
                    if continued else 'draft.active-prefix.' + base.prefix.fingerprint())
    root = development_root(configs, study_id='study.' + draft_id)
    budget = resource_budget(base)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ('gate.local-nonactuating-development',), frozenset(), budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.' + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('decision-right.' + draft_id, AuthorityAction.SIMULATION_EXECUTION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    selection = operation_declaration(accelerated=base.ACCELERATED, continuation=continued).registration().selection
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node_id(c), selection=selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.' + node_id(c) + '.complete-original-prefix',),
        resource_budget=resource_budget(c), resource_lock_ids=('gp-periodic-force-native-worker',), maximum_attempts=1) for c in configs)
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), operations,
        native_external_inputs(configs), native_input_links(configs), tuple(node_id(c) for c in configs), development_study=root,
        contribution_parents=contribution_parents(base))


def contribution_parents(config):
    parents = [] if config.scientific_context is None else [config.scientific_context.parent]
    continuation = getattr(config, 'continuation', None)
    if continuation is not None and continuation.parent is not None:
        parents.append(continuation.parent)
    return tuple(sorted(set(parents), key=lambda p: p.contribution_id))


def _selection_preparation():
    from empirical_lawhood.execution.recursive_inquiry_selection import InquirySelectionPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_type
    return InquirySelectionPreparation(_decode_selected_configs, tuple(config_type(flag, continuation=continued)
        for flag in (False, True) for continued in (False, True)),
        (validate_configs, active_preparation_prefix_draft))


def selection_scope(draft):
    return _selection_preparation().scope(draft)


def selected_configs(draft):
    return _selection_preparation().read(draft)


def _decode_selected_configs(draft):
    from empirical_lawhood.science.records.decoded_record_store import decode_scoped_canonical_bytes
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_type
    rows = []
    for operation in draft.operations:
        kinds = [config_type(flag, continuation=continued) for flag in (False, True) for continued in (False, True)]
        kind = next((kind for kind in kinds if operation.config_identity.object_schema == kind.SCHEMA), None)
        if kind is None:
            raise ValueError('preparation inquiry changes its registered prefix operation')
        rows.append(decode_scoped_canonical_bytes(operation.config_payload.encode(), kind, maximum_bytes=64 * 2**20))
    configs = tuple(rows)
    validate_configs(configs)
    if draft != active_preparation_prefix_draft(configs, draft_id=draft.draft_id):
        raise ValueError('preparation inquiry changes its original complete paired graph')
    return configs


def prefix_input_origins(draft):
    from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    base = selected_configs(draft)[0]
    rows = []
    for external in draft.external_inputs:
        if external.scientific_role == 'HISTORY':
            parent, product = next((parent, p) for parent in contribution_parents(base)
                for p in parent.products if p.artifact.artifact_id == external.logical_artifact_id)
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.CONTRIBUTION,
                product.record.object_fingerprint, product.role.value,
                ObjectIdentity.from_record(parent.contribution_id, parent), product.product_id, product.producing_receipt))
        else:
            rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.SOURCE,
                external.expected_content_sha256, external.scientific_role))
    origins = RecursiveInputOrigins(tuple(rows))
    origins.validate_draft(draft)
    return origins
