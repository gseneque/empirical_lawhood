# SPDX-License-Identifier: MPL-2.0
"""Authenticate current target findings through installed assessment owners."""

from pathlib import Path

from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition


def project_wave_claim_assessments(*, specification, draft, products, requested=None, factories=None):
    """Apply the existing exact receipt/configuration checks to one read wave.

    Callers must obtain products through the ordinary current custody reader.
    A certificate uses the same installed domain projector as an inquiry.
    """
    from empirical_lawhood.api.recursive_inquiry import _scientific_product_identity
    from empirical_lawhood.api.recursive_operations import operation_factories

    factories = ({factory.registration.selection: factory for factory in operation_factories()}
                 if factories is None else factories)
    operations = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    callbacks = {}
    for operation in operations:
        factory = factories[operation.selection]
        callback = factory.inquiry_claim_assessment_projector
        if callback is not None:
            callbacks.setdefault(callback, []).append((operation, factory))
    assessments = {}
    for callback, owners in callbacks.items():
        projected = callback(draft, specification, products)
        if type(projected) is not tuple or any(type(row) is not InquiryClaimAssessment for row in projected):
            raise ValueError("registered target assessor returned an invalid projection")
        for row in projected:
            row.__post_init__()
            key = row.claim_identity, row.assessment
            if requested is not None and key not in requested:
                continue
            matched = [(op, factory) for op, factory in owners if op.config_identity == row.assessment_contract]
            if len(matched) != 1:
                raise ValueError("target assessor substitutes its selected assessment contract")
            operation, factory = matched[0]
            receipt = products["receipts"].get(operation.node_id)
            outputs = products["records"].get(operation.node_id, {})
            if (receipt is None or row.producing_receipt != identity(receipt, receipt.receipt_id)
                    or not any(row.assessment == _scientific_product_identity(draft, operation.node_id, record)
                               for record in outputs.values())):
                raise ValueError("target assessor substitutes its actual receipt-bound result")
            if (row.evidence_ceiling, row.outcome_access, row.visibility_ceiling) != (
                    factory.manifest.maximum_evidence_ceiling, factory.registration.outcome_access,
                    factory.registration.visibility_ceiling):
                raise ValueError("target assessor changes its registered evidence ceiling")
            if key in assessments and assessments[key] != row:
                raise ValueError("target claim has conflicting authenticated assessments")
            assessments[key] = row
    return tuple(assessments[key] for key in sorted(assessments, key=lambda value: (
        value[0].object_id, value[1].object_id)))


def project_target_claim_assessments(*, specification, sources, menu, artifact_writer, _reading=None):
    """Reconstruct exact semantic witnesses; raw sources have no assessor.

    Neither the request nor a persisted packet can supply these projections.
    All selected results are read through the ordinary current custody owner.
    The same function serves commitment and current decision readback.
    """
    from empirical_lawhood.api.recursive_inquiry import _inquiry_history_sources, read_recursive_wave
    from empirical_lawhood.api.recursive_operations import operation_factories

    requested = {(finding.claim, finding.assessment) for finding in menu.frontier.claim_findings
                 if finding.disposition is not AssessmentDisposition.NOT_ATTEMPTED}
    if not requested:
        return ()
    root = Path(artifact_writer.root.contract.canonical_path)
    _, waves = _inquiry_history_sources(sources=sources, root=root, artifact_writer=artifact_writer)
    factories = {factory.registration.selection: factory for factory in operation_factories()}
    assessments = {}
    for source in waves:
        if not source.include_products:
            continue
        if _reading is None:
            _, products, draft, _ = read_recursive_wave(directory=root / source.relative_path,
                artifact_writer=artifact_writer, include_products=True)
        else:
            original = _reading.wave(directory=root / source.relative_path,
                include_products=True, expected=source.packet)
            products, draft = original.products, original.draft
        for row in project_wave_claim_assessments(specification=specification, draft=draft,
                products=products, requested=requested, factories=factories):
            key = row.claim_identity, row.assessment
            if key in assessments and assessments[key] != row:
                raise ValueError("target claim has conflicting authenticated assessments")
            assessments[key] = row
    if assessments.keys() != requested:
        raise ValueError("target claim lacks an applicable registered independent assessor")
    return tuple(assessments[key] for key in sorted(assessments, key=lambda value: (
        value[0].object_id, value[1].object_id)))
