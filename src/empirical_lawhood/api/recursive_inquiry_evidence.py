# SPDX-License-Identifier: MPL-2.0
"""Authenticate complete code-owned scientific meanings without endpoint stamping."""
from hashlib import sha256

from empirical_lawhood.api.recursive_operations import operation_factories
from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding


def project_wave_evidence_bindings(*, draft, payloads, products=None):
    """Return exact source/product meanings; custody owner retains origin authority.

    No requested endpoint is an argument. Code-owned domain callbacks must supply
    original scientific meanings even for initial sources and failed/no-product
    attempts. Contributed inputs retain their already authenticated parent role
    and scope rather than acquiring the successor's requested meaning.
    """
    selections = {operation.selection.selection_id for operation in draft.operations
                  if operation.node_id in draft.selected_operation_ids}
    callbacks = {factory.inquiry_evidence_projector for factory in operation_factories()
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
        filename = 'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json'
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
                if declared_scope is not None and binding.scope != declared_scope:
                    raise ValueError('inquiry evidence changes the product original declared scope')
    if set(bindings) != expected:
        raise ValueError('inquiry evidence meanings change the complete original input/product census')
    return bindings
