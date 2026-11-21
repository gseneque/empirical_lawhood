# SPDX-License-Identifier: MPL-2.0
"""Authenticate complete code-owned scientific meanings without endpoint stamping."""
from hashlib import sha256

from empirical_lawhood.api.recursive_operations import selected_operation_factories
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ScientificConditionScope
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding


def binary_product_identity(*, draft, products, task_id, output_id):
    """Bind an already authenticated binary output to its producing declaration.

    The original full reader verifies body, receipt and selected storage codec.
    Inquiry preserves that artifact's identity without inventing a decoded
    scientific record or passing opaque bytes to a canonical-record callback.
    """
    if output_id in products['records'].get(task_id, {}):
        raise ValueError('a decoded inquiry product cannot be relabelled as binary')
    entries = [row for row in products.get('product_index', ())
        if (row['task_id'], row['output_id']) == (task_id, output_id)]
    operations = [row for row in draft.operations if row.node_id == task_id and task_id in draft.selected_operation_ids]
    if len(entries) != 1 or len(operations) != 1:
        raise ValueError('binary inquiry output lacks its unique original selected producer')
    entry, operation = entries[0], operations[0]
    manifest = products['outputs'].get(entry['logical_artifact_id'])
    receipt = products['receipts'].get(task_id)
    if (manifest is None or receipt is None or manifest.logical not in receipt.output_logical_artifacts
            or manifest.materialization not in receipt.output_materializations
            or receipt.task_id != task_id or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or entry['producing_receipt'] != ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document()
            or (entry['schema'], entry['sha256'], entry['size_bytes'], entry['relative_path']) !=
            (manifest.logical.payload_schema, manifest.logical.content_sha256,
                manifest.materialization.size_bytes, manifest.materialization.relative_path)):
        raise ValueError('binary inquiry output changes its original receipt or complete artifact')
    factories = [factory for factory in selected_operation_factories((operation.selection.selection_id,))
        if factory.registration.selection == operation.selection]
    if len(factories) != 1:
        raise ValueError('binary inquiry output lacks its original installed operation')
    from empirical_lawhood.storage.contracts.recursive_storage_codecs import resolve_storage_codec
    logical = manifest.logical
    codec = resolve_storage_codec(factories[0].registration.storage_codecs,
        payload_schema=logical.payload_schema, profile=logical.profile, media_type=logical.media_type)
    if codec is None:
        raise ValueError('an undecoded inquiry output needs its exact producing storage codec')
    return ObjectIdentity(logical.logical_artifact_id, logical.payload_schema, codec.record_version, logical.content_sha256)


def project_wave_evidence_bindings(*, draft, payloads, products=None):
    """Return exact source/product meanings; custody owner retains origin authority.

    No requested endpoint is an argument. Code-owned domain callbacks must supply
    original scientific meanings even for initial sources and failed/no-product
    attempts. Contributed inputs retain their already authenticated parent role
    and scope rather than acquiring the successor's requested meaning.
    """
    selections = {operation.selection.selection_id for operation in draft.operations
                  if operation.node_id in draft.selected_operation_ids}
    callbacks = {factory.inquiry_evidence_projector for factory in selected_operation_factories(selections)
                 if factory.registration.selection.selection_id in selections}
    if None in callbacks or len(callbacks) != 1:
        raise ValueError('inquiry evidence requires one registered domain meaning projector')
    rows = next(iter(callbacks))(draft, payloads, products)
    if (not isinstance(rows, tuple) or any(type(row) is not InquiryEvidenceBinding for row in rows)
            or tuple(sorted({row.binding_id for row in rows})) != tuple(row.binding_id for row in rows)):
        raise ValueError('inquiry evidence meanings require a sorted unique typed census')
    bindings = {row.binding_id: row for row in rows}
    selected_inputs = {link.external_input_id for link in draft.links
                       if link.consumer_node_id in draft.selected_operation_ids and link.external_input_id is not None}
    expected = set(selected_inputs)
    for external in draft.external_inputs:
        if external.input_id not in selected_inputs:
            continue
        from empirical_lawhood.api.recursive_authoring import _external_storage_contract
        _, suffix = _external_storage_contract(payload_schema=external.payload_schema, media_type=external.media_type)
        filename = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        raw = payloads[filename]
        binding = bindings.get(external.input_id)
        if binding is None or binding.content_sha256 != sha256(raw).hexdigest() or binding.content_sha256 != external.expected_content_sha256:
            raise ValueError('inquiry evidence meaning substitutes exact selected source bytes')
        parent_digest_matches = tuple(product for parent in draft.contribution_parents for product in parent.products
                                      if product.artifact.sha256 == external.expected_content_sha256)
        if parent_digest_matches and not any(product.artifact.artifact_id == external.logical_artifact_id for product in parent_digest_matches):
            raise ValueError('inquiry evidence changes exact contributed artifact identity')
        inherited = tuple(product for parent in draft.contribution_parents for product in parent.products
                          if product.artifact.artifact_id == external.logical_artifact_id
                          and product.artifact.sha256 == external.expected_content_sha256)
        if inherited:
            if len(inherited) != 1:
                raise ValueError('inquiry evidence has ambiguous contribution ownership')
            product = inherited[0]
            parents = tuple(parent for parent in draft.contribution_parents if product in parent.products)
            if binding.scope != parents[0].scope or binding.role is not product.role:
                raise ValueError('inquiry evidence changes the original contribution scope or allowed role')
    if products is not None:
        for task_id, outputs in products['records'].items():
            if task_id not in draft.selected_operation_ids:
                raise ValueError('inquiry evidence adds an unselected producing operation')
            for output_id, record in outputs.items():
                expected.add(output_id)
                binding = bindings.get(output_id)
                if binding is None or binding.content_sha256 != record.fingerprint():
                    raise ValueError('inquiry evidence lacks exact code-owned product meaning')
                declared_scope = getattr(record, 'scope', None)
                # Some original records retain a closed descriptive scope
                # label. Only the typed condition is a scientific declaration;
                # the registered projector owns the other records' meaning.
                if isinstance(declared_scope, ScientificConditionScope) and binding.scope != declared_scope:
                    raise ValueError('inquiry evidence changes the product original declared scope')
        for row in products.get('product_index', ()):
            task_id, output_id = row['task_id'], row['output_id']
            if output_id in products['records'].get(task_id, {}):
                continue
            product = binary_product_identity(draft=draft, products=products, task_id=task_id, output_id=output_id)
            expected.add(output_id)
            binding = bindings.get(output_id)
            if binding is None or binding.content_sha256 != product.object_fingerprint:
                raise ValueError('inquiry evidence lacks exact code-owned binary product meaning')
    if set(bindings) != expected:
        raise ValueError('inquiry evidence meanings change the complete original input/product census')
    return bindings
