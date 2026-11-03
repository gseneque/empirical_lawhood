# SPDX-License-Identifier: MPL-2.0
"""Exact original native controls and banks for a declared primary amendment."""
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity


def _record(writer, publication, kind):
    authenticate_published_materialization(writer, publication)
    physical = publication.materialization
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)
    value = decode_canonical_bytes(raw, kind, maximum_bytes=physical.size_bytes)
    if (value.canonical_bytes() != raw or value.fingerprint() != publication.logical.content_sha256
            or value.fingerprint() != physical.physical_sha256):
        raise PermissionError("primary amendment original native publication changes exact bytes")
    return value



def _entry_product(writer, binding):
    """Join one exact original entry receipt to its stored authored native plan."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.api.recursive_operations import development_output_contracts, operation_catalog
    from empirical_lawhood.api.native_training_banks import _receipt_product
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import entry_task_id
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    locator = binding.native_training_locator
    directory = writer.root.resolve(locator.authored_directory, for_write=False)
    packet, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    raw = payloads["experiment-instance.json"]
    instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
    amendment = binding.amendment
    if (type(plan) is not DevelopmentExecutionPlan or ObjectIdentity.from_record(packet.packet_id, packet) != locator.packet
            or ObjectIdentity.from_record(plan.execution_plan_id, plan) != locator.execution_plan or run.run_plan_id != locator.run_id
            or instance.specification != amendment.original_native_specification
            or instance.sources != (amendment.original_native_request,)
            or draft.development_study is None or draft.prospective_draft is not None
            or not {amendment.original_candidate.identity, amendment.original_native_request,
                amendment.original_native_specification} <= set(draft.development_study.scientific_operands)):
        raise PermissionError("primary amendment changes original native authored plan or candidate operands")
    development_output_contracts(plan, operation_catalog()[2])
    task_id = entry_task_id(amendment.original_native_specification)
    receipt = ExternalTaskReceiptStore(writer).read_by_receipt_id(run.run_plan_id, task_id, binding.entry_receipt.object_id)
    if (receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != binding.entry_receipt
            or receipt.implementation_commit != plan.implementation_commit):
        raise PermissionError("primary amendment changes its actual original native entry receipt")
    manifest = writer.read_manifest(binding.acquisition_publication.materialization.relative_path)
    if (manifest.logical, manifest.materialization) != (binding.acquisition_publication.logical, binding.acquisition_publication.materialization):
        raise PermissionError("primary amendment substitutes its original receipted seal publication")
    products = {"receipts": {task_id: receipt}, "outputs": {manifest.logical.logical_artifact_id: manifest}}
    seal, _ = _receipt_product(writer, products, plan, task_id, native.NativeTrainingAcquisitionSeal)
    return seal


def authenticate_primary_amendment(*, writer, selection):
    """No default amendment; authenticate actual original seal and unchanged banks."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
        ConfiguredProtectedE3LoweringInputs, configured_preparation_types,
    )
    if type(selection) not in (ConfiguredProtectedE3LoweringInputs, *configured_preparation_types()):
        return None
    selection.__post_init__()
    binding = selection.primary_amendment
    if binding is None:
        return None
    amendment = binding.amendment
    specification = _record(writer, binding.native_specification_publication, native.NativeTrainingAcquisitionSpecification)
    seal = _record(writer, binding.acquisition_publication, native.NativeTrainingAcquisitionSeal)
    if _entry_product(writer, binding) != seal:
        raise PermissionError("primary amendment changes its genuine original receipted native seal")
    reservation = ObjectIdentity.from_record(selection.manifest.reservation.reservation_id, selection.manifest.reservation)
    if (specification.identity != amendment.original_native_specification
            or specification.candidate != amendment.original_candidate.identity
            or specification.measurement != amendment.original_candidate.measurement
            or specification.future_reservation != reservation
            or seal.identity != binding.acquisition or seal.specification != specification.identity
            or seal.request != amendment.original_native_request or seal.candidate != amendment.original_candidate.identity
            or seal.future_reservation != reservation or seal.allocation != selection.training_allocation.identity
            or selection.training_allocation.sources != (amendment.original_native_request,)):
        raise PermissionError("primary amendment substitutes original candidate, native seal, source, allocation or reservation")
    banks = tuple(_record(writer, publication, kind) for publication, kind in
        zip(binding.native_bank_publications, native.native_training_bank_types(), strict=True))
    if (any(bank.acquisition != seal.identity for bank in banks)
            or any(row.source_manifest != amendment.original_native_request for bank in banks for row in bank.rows)):
        raise PermissionError("primary amendment native banks substitute their exact original acquisition or request")
    native.validate_native_training_banks(amendment.original_candidate, selection.training_allocation, *banks)
    native.validate_native_training_banks(amendment.candidate, selection.training_allocation, *banks)
    return binding.identity
