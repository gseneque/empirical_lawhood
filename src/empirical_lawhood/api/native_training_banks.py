# SPDX-License-Identifier: MPL-2.0
"""Publish complete native TRAIN banks from actual public development custody.

This exporter starts no task and creates no completion, issue, sampling or
qualification receipt. The fresh acquisition's ordinary receipts remain the
producers; these publications retain their complete source and nonuse census.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import (
    entry_task_id, export_training_banks, task_id,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_request
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
from empirical_lawhood.api.recursive_operations import development_output_contracts, operation_catalog
from empirical_lawhood.api.recursive_qualified_parents import _output_payload
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult, lineage_parent_sort_key
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding


@dataclass(frozen=True, slots=True)
class NativeTrainingBankExport:
    """Actual records and their ordinary immutable publication handles."""
    allocation: UnitAllocation
    features: records.NativeTrainingFeatureBank
    outcomes: records.NativeTrainingOutcomeBank
    publications: tuple[ArtifactWriteResult, ...]
    run_id: str
    acquisition: records.NativeTrainingAcquisitionSeal | None = None
    acquisition_publication: ArtifactWriteResult | None = None
    acquisition_receipt: ObjectIdentity | None = None
    validation_origin: str = "FULL_ARRAY_REPLAY"
    locator: MatrixFiniteDtTrainingLocator | None = None


def _read_instance(payloads):
    required = ("experiment-specification.json", "experiment-instance.json")
    if any(name not in payloads for name in required):
        raise PermissionError("native TRAIN export needs its actual public experiment instance")
    raw = payloads[required[0]]
    specification = decode_canonical_bytes(raw, records.NativeTrainingAcquisitionSpecification,
        maximum_bytes=len(raw))
    raw = payloads[required[1]]
    instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
    matches = tuple(value for value in instance.sources if (value.object_schema, value.object_version) ==
        (records.NativeTrainingAcquisitionRequest.SCHEMA, records.NativeTrainingAcquisitionRequest.VERSION))
    if len(matches) != 1 or instance.specification != specification.identity:
        raise PermissionError("native TRAIN export substitutes its exact acquisition specification/request")
    reference, = matches
    name = "experiment-source-" + sha256(reference.object_id.encode()).hexdigest() + ".json"
    if name not in payloads:
        raise PermissionError("native TRAIN export omits its retained original request")
    raw = payloads[name]
    request = decode_canonical_bytes(raw, records.NativeTrainingAcquisitionRequest, maximum_bytes=len(raw))
    if ObjectIdentity.from_record(reference.object_id, request) != reference:
        raise PermissionError("native TRAIN export changes its selected canonical request")
    records.validate_request(specification, request)
    return specification, request, instance


def _receipt_product_binding(products, plan, selected_task_id, kind, label="product"):
    """Join one exact winning receipt to its declared canonical product."""
    tasks = tuple(value for value in plan.tasks if value.task_id == selected_task_id)
    receipt = products["receipts"].get(selected_task_id)
    if (len(tasks) != 1 or receipt is None or receipt.task_id != selected_task_id
            or receipt.run_id != plan.source_plan.object_id
            or receipt.operational_status is not OperationalStatus.SUCCEEDED):
        raise PermissionError("native TRAIN export lacks its actual successful producing receipt")
    task, = tasks
    outputs = tuple(value for value in task.outputs if value.output_id == selected_task_id + "." + label
        and value.payload_schema == kind.SCHEMA)
    if len(outputs) != 1:
        raise PermissionError("native TRAIN export changes its exact declared product/schema")
    output, = outputs
    logicals = tuple(value for value in receipt.output_logical_artifacts
        if value.logical_artifact_id == output.logical_artifact_id)
    if len(logicals) != 1:
        raise PermissionError("native TRAIN export omits its exact receipted logical product")
    logical, = logicals
    materials = tuple(value for value in receipt.output_materializations
        if value.logical_artifact_id == output.logical_artifact_id)
    retained = products["outputs"].get(output.logical_artifact_id)
    if (len(materials) != 1 or retained is None
            or (retained.logical, retained.materialization) != (logical, materials[0])
            or logical.payload_schema != kind.SCHEMA or logical.profile is not ArtifactProfile.CANONICAL_JSON
            or logical.media_type != "application/json"
            or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise PermissionError("native TRAIN export changes original product custody or exposure lane")
    return receipt, logical, materials[0]


def _receipt_product(writer, products, plan, selected_task_id, kind, label="product"):
    """Decode one exact already authenticated producing task's product."""
    receipt, logical, material = _receipt_product_binding(products, plan, selected_task_id, kind, label)
    raw = _output_payload(writer, receipt, logical, material.size_bytes)
    value = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    if value.canonical_bytes() != raw or value.fingerprint() != logical.content_sha256:
        raise PermissionError("native TRAIN export changes its actual canonical scientific product")
    return value, receipt


def _export_authored_preflight(*, directory, artifact_writer, expected_locator):
    root = Path(artifact_writer.root.contract.canonical_path)
    def validate_authored(*, packet, draft, source, payloads, run, plan, index):
        specification, request, instance = _read_instance(payloads)
        if expected_locator is not None:
            from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
            if type(expected_locator) is not MatrixFiniteDtTrainingLocator:
                raise TypeError('native TRAIN export substitutes its exact authored locator')
            expected_locator.__post_init__()
            actual_directory = Path(directory).resolve(strict=True).relative_to(root).as_posix()
            if (expected_locator.authored_directory != actual_directory or expected_locator.run_id != run.run_plan_id
                    or expected_locator.packet != ObjectIdentity.from_record(packet.packet_id, packet)
                    or expected_locator.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)):
                raise PermissionError('native TRAIN export changes original authored packet, run or complete execution plan')
        authenticate_request(artifact_writer, request)
        _, _, codecs = operation_catalog()
        development_output_contracts(plan, codecs)
        return specification, request, instance
    return validate_authored


def _collect_export_records(*, writer, products, plan, specification, get_product=None, acquisition_publication=None):
    if get_product is None:
        get_product = lambda task, kind, label="product": _receipt_product(writer, products, plan, task, kind, label)
    acquisition, receipt = get_product(entry_task_id(specification),
        records.NativeTrainingAcquisitionSeal)
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput
    logical, = (value for value in receipt.output_logical_artifacts if value.payload_schema == records.NativeTrainingAcquisitionSeal.SCHEMA)
    retained = products["outputs"][logical.logical_artifact_id]
    # The generic reader projects receipt-bound logical/materialized identities;
    # its projection does not carry the actual batch publication binding. Load
    # that binding fresh without weakening full retained-manifest comparisons.
    if acquisition_publication is None:
        acquisition_publication = _publication_from_manifest(writer,
            VerifiedArtifactInput(retained.logical, retained.materialization))
    acquisition_receipt = ObjectIdentity.from_record(receipt.receipt_id, receipt)
    receipts = [receipt]
    features, outcomes = [], []
    for root_id in specification.root_ids:
        feature, receipt = get_product(task_id(root_id, "feature"),
            records.NativeTrainingFeature)
        features.append(feature)
        receipts.append(receipt)
        outcome, receipt = get_product(task_id(root_id, "response-score"),
            records.NativeTrainingOutcome)
        outcomes.append(outcome)
        receipts.append(receipt)
    return acquisition, acquisition_publication, acquisition_receipt, receipts, tuple(features), tuple(outcomes)


def export_native_training_banks(*, directory, artifact_writer, output_directory, record_id, expected_locator=None):
    """Read a complete fresh public acquisition and publish its new bank edition.

    The selected authored specification/request alone determine the population.
    Output publication is last, after complete custody and pure scientific joins.
    Original scientific products, task receipts and source bytes remain exact.
    """
    from empirical_lawhood.kernel.serialization import validate_stable_id
    validate_stable_id(record_id)
    target = Path(output_directory)
    if not target.is_absolute() or target != target.resolve(strict=False):
        raise ValueError("native TRAIN bank export requires an explicit canonical absolute destination")
    root = Path(artifact_writer.root.contract.canonical_path)
    try:
        relative = target.relative_to(root).as_posix()
    except ValueError as error:
        raise ValueError("native TRAIN bank export must use its selected guarded artifact plane") from error
    if relative in ("", "."):
        raise ValueError("native TRAIN bank export needs a separate selected output directory")
    # Resolve every output before reading a potentially expensive acquisition.
    for name in ("allocation", "features", "outcomes"):
        artifact_writer.root.resolve(relative + "/" + name + ".json", for_write=True)
    from contextlib import nullcontext
    from .recursive_execution import _read_only_custody_policy
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    bounded = (type(artifact_writer) is ExternalArtifactPlane
        and _read_only_custody_policy(artifact_writer) is not None)
    scope = artifact_writer.read_context() if bounded else nullcontext(artifact_writer)
    # The read view spans original preflight, arrays, reduction and publication.
    # Publication uses the original writer; the final read guard retains custody.
    with scope as writer:
        validate_authored = _export_authored_preflight(directory=directory, artifact_writer=writer,
            expected_locator=expected_locator)
        result, roots, (specification, request, instance) = _read_recursive_wave_with_roots(directory=directory,
            artifact_writer=writer, include_products=True, terminal_product_format="documents",
            allow_partial=False, validate_authored=validate_authored)
        report, products, actual_draft, actual_plan = result
        packet, draft, _, run, plan, _ = roots
        if (actual_draft != draft or actual_plan != plan or report["run_id"] != run.run_plan_id
                or report["packet_sha256"] != packet.fingerprint() or report["status"] != "SUCCEEDED"
                or set(products["receipts"]) != {value.task_id for value in plan.tasks}
                or report.get("scientific_result", {}).get("scientific_completion") != "COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY"):
            raise PermissionError("native TRAIN bank export requires its unchanged complete successful acquisition")
        acquisition, acquisition_publication, acquisition_receipt, receipts, features, outcomes = _collect_export_records(
            writer=writer, products=products, plan=plan, specification=specification)
        allocation, feature_bank, outcome_bank = export_training_banks(specification, request,
            acquisition=acquisition, features=tuple(features), outcomes=tuple(outcomes), record_id=record_id)
        if allocation.identity != instance.allocation:
            raise PermissionError("native TRAIN bank export changes its original complete authored allocation")
        references = (ObjectIdentity.from_record(packet.packet_id, packet), specification.identity,
            request.identity, acquisition.identity, *(ObjectIdentity.from_record(value.receipt_id, value) for value in receipts))
        parents = tuple(sorted((ArtifactLineageParent(value, VisibilityCeiling.DEVELOPMENT_ONLY,
            OutcomeAccess.DEVELOPMENT_VISIBLE) for value in set(references)), key=lineage_parent_sort_key))
        writes = tuple(ArtifactWriteRequest(value.identity.object_id, relative + "/" + name + ".json", value.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", record_id, relative, value.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, tuple(value.visibility_ceiling for value in parents),
            OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=parents)
            for name, value in (("allocation", allocation), ("features", feature_bank), ("outcomes", outcome_bank)))
        # Existing atomic batch publication handles exact replay and refuses foreign
        # destinations without leaving a navigable partial export.
        if bounded:
            writer.require_verification_snapshot()
        publications = artifact_writer.write_batch(writes)
        locator = MatrixFiniteDtTrainingLocator(Path(directory).resolve(strict=True).relative_to(root).as_posix(),
            run.run_plan_id, ObjectIdentity.from_record(packet.packet_id, packet),
            ObjectIdentity.from_record(plan.execution_plan_id, plan))
        exported = NativeTrainingBankExport(allocation, feature_bank, outcome_bank, publications, run.run_plan_id,
            acquisition, acquisition_publication, acquisition_receipt, locator=locator)
        return exported


def export_selected_native_training_banks(*, directory, artifact_writer, selection_path):
    """Public registered export transition over the ordinary authenticated owner."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_exports import NativeTrainingBankExportSelection
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    path = Path(selection_path)
    if any(value.is_symlink() for value in (path,*path.parents)):
        raise ValueError('native TRAIN export refuses a linked selection')
    raw = read_bounded_bytes(path, maximum_bytes=1024**2)
    selection = decode_canonical_bytes(raw, NativeTrainingBankExportSelection, maximum_bytes=len(raw))
    if raw != selection.canonical_bytes():
        raise ValueError('native TRAIN export requires unchanged canonical selected bytes')
    selected_root = Path(artifact_writer.root.contract.canonical_path)
    output = artifact_writer.root.resolve(selection.output_relative_path,for_write=True)
    result = export_native_training_banks(directory=directory,artifact_writer=artifact_writer,
        output_directory=output,record_id=selection.bank_record_id)
    return {'selection':selection.identity.to_document(),'run_id':result.run_id,
        'native_training_locator':result.locator.to_document(),
        'allocation':result.allocation.identity.to_document(),'features':result.features.identity.to_document(),
        'outcomes':result.outcomes.identity.to_document(),'assigned_units':len(result.allocation.units),
        'publications':tuple(value.to_document() for value in result.publications),
        'paths':tuple(str(selected_root/value.materialization.relative_path) for value in result.publications),
        'native_contact':'NONE','scientific_qualification':'NOT_ESTABLISHED',
        'freshness':'NOT_INFERRED_FROM_EXPORT'}
