# SPDX-License-Identifier: MPL-2.0
"""Original preparation evidence, scoped contributions and inquiry work semantics."""

from hashlib import sha256

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole, ScientificConditionScope
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import ActivePreparationPrefixResult, node_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_translation import contribution_parents, selected_configs, selection_scope


def prefix_scope(configs):
    return selected_prefix_scope(configs[0].prefix)


def selected_prefix_scope(prefix):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_selection import ActivePreparationPrefixSelection
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    exact(prefix, ActivePreparationPrefixSelection)
    return ScientificConditionScope(prefix.plan.object_id, 'world.periodic-gp-preparation-prefix',
        prefix.identity.object_id, ('accepted-preparation-state',), ('complete-Cartesian-state',),
        'receiver.rubisco.accepted-preparation-state', 'clock.rubisco.preparation-information-order',
        'Two M1 materials and two nested state positions per material within one ten-return preparation purchase. '
        'Original four materials, 32 sites and 384 chemical starts remain assigned; no independent biological replicate.',
        source_config_sha256=prefix.fingerprint(), instance_id=prefix.selection_id,
        population_id='population.one-matched-construction-no-biological-replicates', uncertainty_contract=prefix.identity)


def endpoint_validator(draft, endpoint):
    if endpoint != prefix_scope(selected_configs(draft)):
        raise ValueError('preparation inquiry substitutes its exact original state scope')


def record_identity(record):
    if type(record) not in (ActivePreparationPrefixResult, ActivePreparationPrefixReadout):
        raise TypeError('preparation inquiry requires its actual original product or independent readout')
    return record.identity


def actual_products(draft, products):
    """Join both original products to their actual task receipt and materializations."""
    rows = []
    configs = selected_configs(draft)
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_configuration
    for config in configs:
        task = node_id(config)
        records = products['records'].get(task, {})
        if not records:
            continue
        if set(records) != {task + '.product', task + '.assessment'}:
            raise ValueError('preparation inquiry omits the original result or independent assessment')
        result, assessed = records[task + '.product'], records[task + '.assessment']
        if (type(result) is not ActivePreparationPrefixResult or type(assessed) is not ActivePreparationPrefixReadout
                or result.configuration != original_configuration(config) or result.prefix != config.prefix
                or result.model_name != config.original.model_name or assessed.original_result != result):
            raise ValueError('preparation inquiry substitutes its original selected molecular outcome')
        receipt = products['receipts'].get(task)
        if receipt is None or receipt.task_id != task or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError('preparation scientific output lacks its completed publishing receipt')
        for name, record in (('product', result), ('assessment', assessed)):
            logicals = [r for r in receipt.output_logical_artifacts if r.payload_schema == record.SCHEMA
                        and r.content_sha256 == record.fingerprint()]
            if len(logicals) != 1:
                raise ValueError('preparation output lacks its unique original receipt binding')
            logical, = logicals
            artifact = products['outputs'].get(logical.logical_artifact_id)
            if (artifact is None or artifact.logical != logical or artifact.materialization not in receipt.output_materializations
                    or artifact.materialization.size_bytes != record.canonical_size_bytes()
                    or artifact.materialization.physical_sha256 != record.fingerprint()):
                raise ValueError('preparation inquiry substitutes its actual complete output bytes')
            rows.append((task, name, record, receipt, artifact))
    return tuple(rows)


def describe_contributions(draft, authenticated_products):
    configs = selected_configs(draft)
    rows = actual_products(draft, authenticated_products)
    if len(rows) != 4:
        return ()  # The missing material remains in the paired denominator.
    products, assessments = [], []
    for task, name, record, receipt, artifact in rows:
        products.append(ContributionProduct('product.' + task + '.' + name, record.identity,
            ArtifactIdentity(artifact.logical.logical_artifact_id, 'original-preparation-' + name,
                record.SCHEMA, record.fingerprint(), 'application/json', artifact.materialization.size_bytes),
            ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.RETAINED_ANALYSIS_INPUT,
            EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
        if name == 'assessment':
            assessments.append(record.identity)
    context = configs[0].scientific_context
    return (ContributionManifest('contribution.active-prefix.' + draft.fingerprint(), draft.question,
        'Original paired prefix and independently read state positions, including missing or rejected checkpoints. '
        'No endpoint convergence, population, physical time or kinetic contrast is inferred.', prefix_scope(configs),
        tuple(sorted(products, key=lambda p: p.product_id)), tuple(sorted(assessments, key=lambda p: p.object_id)),
        () if context is None else context.parent.remaining_requirements,
        tuple(ObjectIdentity.from_record(p.contribution_id, p) for p in contribution_parents(configs[0]))),)


def outcome_projector(draft, specification, products):
    configs = selected_configs(draft)
    if not any(r.scope == prefix_scope(configs) for r in specification.requirements):
        raise ValueError('preparation outcome is outside the exact selected inquiry')
    if specification.distinguishing_assessment not in {c.identity for c in configs}:
        raise ValueError('preparation inquiry substitutes its selected original assessor')
    rows = actual_products(draft, products)
    if len(rows) != 4:
        return 'unresolved'
    readouts = [record for _, name, record, _, _ in rows if name == 'assessment']
    if any(r.assessment is None or any(p.disposition == 'UNAVAILABLE' for p in r.assessment.positions) for r in readouts):
        return 'unresolved'
    return 'contradicted' if any(p.disposition == 'REJECTED' for r in readouts for p in r.assessment.positions) else 'supported'


def evidence_projector(draft, payloads, products=None):
    configs = selected_configs(draft)
    scope = prefix_scope(configs)
    views = draft.development_study.numerical_view_ids
    bindings = []
    for external in draft.external_inputs:
        suffix = '.gz' if external.media_type == 'application/gzip' else '.json'
        path = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        if sha256(payloads[path]).hexdigest() != external.expected_content_sha256:
            raise ValueError('preparation inquiry changes an exact original input')
        historical = external.scientific_role == 'HISTORY'
        if historical:
            inherited = tuple((parent, product) for parent in contribution_parents(configs[0])
                for product in parent.products if product.artifact.artifact_id == external.logical_artifact_id
                and product.artifact.sha256 == external.expected_content_sha256)
            if len(inherited) != 1:
                raise ValueError('preparation inquiry requires one exact original contribution product')
            parent, product = inherited[0]
        bindings.append(InquiryEvidenceBinding(external.input_id, external.expected_content_sha256,
            parent.scope if historical else scope,
            product.role if historical else ContributionRole.DESIGN_OPERAND,
            (), () if historical else views))
    if products is not None:
        for task, name, record, _, _ in actual_products(draft, products):
            bindings.append(InquiryEvidenceBinding(task + '.' + name, record.fingerprint(), scope,
                ContributionRole.INSTANCE_PRODUCT, (), views))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))


def scientific_work(draft, operation_id):
    from empirical_lawhood.methods.compact_inquiry_policy import CompactScientificMethod
    configs = selected_configs(draft)
    config = next((c for c in configs if node_id(c) == operation_id), None)
    if config is None:
        raise ValueError('preparation work is not in its complete original paired draft')
    operation = next(row for row in draft.operations if row.node_id == operation_id)
    original = config.original
    # Invocation labels, work paths and the downstream receiver context do not
    # make the same molecular prefix a new native effect.
    operands = tuple(sorted({config.prefix.identity, original.preparation, original.raw_sources,
        original.prototype.identity, original.plan.settings.identity,
        *((config.continuation.readout.identity, config.continuation.identity) if hasattr(config, 'continuation') else ())},
        key=lambda pin: pin.object_id))
    scope = prefix_scope(configs)
    method = CompactScientificMethod('rubisco-active-prefix', 'acquire', operation.selection.capability_key,
        operation.selection.capability_version, operation.selection.implementation_sha256,
        original.prototype.identity, config.prefix.identity, operands, scope,
        ActivePreparationPrefixReadout.SCHEMA, ActivePreparationPrefixReadout.VERSION)
    return ScientificInquiryWork(ObjectIdentity.from_record('method.rubisco.active-prefix', method), operands, scope,
                                 ObjectIdentity.from_record('observation.rubisco.active-prefix', method))


def inquiry_hooks():
    return RecursiveInquiryHooks(contribution_describer=describe_contributions,
        inquiry_endpoint_validator=endpoint_validator, inquiry_evidence_projector=evidence_projector,
        inquiry_outcome_projector=outcome_projector, inquiry_record_identity=record_identity,
        inquiry_work_projector=scientific_work, inquiry_selection_scope=selection_scope)
