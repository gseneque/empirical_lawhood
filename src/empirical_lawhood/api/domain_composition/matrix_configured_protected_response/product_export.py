# SPDX-License-Identifier: MPL-2.0
"""Publish exact configured E3 downstream products after a full protected read."""

from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_exports import ConfiguredProtectedE3ProductExportSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
from empirical_lawhood.api.codecs import MAX_CAMPAIGN_PACKAGE_BYTES
from empirical_lawhood.api.current_result_custody import _current_control
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, derived_outcome_access, lineage_parent_sort_key,
)
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding


_PRODUCTS = (("models", "fit", ""), ("model-freeze", "freeze", "model"),
    ("calibration", "calibrate", ""), ("calibrated-freeze", "freeze", "calibration"))
_FILENAMES = ("package.json", *(name + ".locator.json" for name, _, _ in _PRODUCTS))


def _identity(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _original_product(read, selection, name, operation, mode):
    """Keep the original task, receipt, logical product and grant identities."""
    record = getattr(read, name.replace("-", "_"))
    task_id = statistical_task_id(read.specification.identity, read.allocation.identity, operation, mode=mode)
    package, plan, receipts, reveal = (read.product_source(task_id) if hasattr(read, 'product_source') else
        (read.package, read.execution_plan, read.receipts, read.reveal_authority))
    tasks = tuple(task for task in plan.tasks if task.task_id == task_id)
    receipt = receipts.get(task_id)
    if (len(tasks) != 1 or receipt is None or receipt.run_id != package.run_plan_id
            or receipt.task_id != task_id or receipt.operational_status is not OperationalStatus.SUCCEEDED):
        raise PermissionError("configured E3 export requires its exact original successful product receipt")
    outputs = tuple(output for output in tasks[0].outputs if output.output_id == task_id + ".product"
        and output.payload_schema == record.SCHEMA)
    if len(outputs) != 1:
        raise PermissionError("configured E3 export requires its original declared product output")
    logicals = tuple(value for value in receipt.output_logical_artifacts
        if value.logical_artifact_id == outputs[0].logical_artifact_id)
    materials = tuple(value for value in receipt.output_materializations
        if value.logical_artifact_id == outputs[0].logical_artifact_id)
    if (len(logicals) != 1 or len(materials) != 1
            or (logicals[0].payload_schema, logicals[0].content_sha256, logicals[0].profile, logicals[0].media_type) !=
                (record.SCHEMA, record.fingerprint(), ArtifactProfile.CANONICAL_JSON, "application/json")):
        raise PermissionError("configured E3 export substitutes its original receipted scientific product")
    logical = logicals[0]
    additional = (ConfiguredProtectedE3PreFitJoin.SCHEMA,) if name == "models" else ()
    binding = RecursivePriorExecutionBinding(
        selection.record_id + "." + name, _identity(package.issued_study, "issue_id"),
        _identity(package.execution_authority, "authority_id"), _identity(package, "package_id"),
        _identity(plan, "execution_plan_id"), package.run_plan_id, task_id,
        _identity(receipt, "receipt_id"), logical.logical_artifact_id, _identity(record),
        additional_output_schema_ids=additional, scope_output_schema_ids=additional)
    locator = MatrixSelectedOriginalProduct(binding, reveal)
    parents = tuple(ArtifactLineageParent(pin, logical.visibility_ceiling, logical.outcome_access)
        for pin in (binding.record, binding.receipt))
    return locator, parents


def _write_request(selection, filename, record, parents, *, logical_id):
    parents = tuple(sorted(set(parents), key=lineage_parent_sort_key))
    access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(row.outcome_access for row in parents))
    ceilings = tuple(row.visibility_ceiling for row in parents)
    return ArtifactWriteRequest(logical_id, selection.output_relative_path + "/" + filename,
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", selection.record_id,
        selection.output_relative_path, record.canonical_bytes(), inherited_visibility(ceilings, access),
        ceilings, access, lineage_parents=parents)


def export_configured_protected_e3_products(*, directory, selected, project_root, artifact_writer,
        selection_path):
    """Read, validate and publish without scheduling, repairing or issuing work."""
    from .scientific_read import read_protected_e3_original_products

    path = Path(selection_path)
    if any(value.is_symlink() for value in (path, *path.parents)):
        raise ValueError("configured E3 export refuses a linked selection")
    raw = read_bounded_bytes(path, maximum_bytes=1024**2)
    selection = decode_canonical_bytes(raw, ConfiguredProtectedE3ProductExportSelection, maximum_bytes=len(raw))
    if raw != selection.canonical_bytes():
        raise ValueError("configured E3 export requires unchanged canonical selected bytes")
    for filename in _FILENAMES:
        artifact_writer.root.resolve(selection.output_relative_path + "/" + filename, for_write=True)
    package = _current_control(writer=artifact_writer, run_id=selection.run_id, name="campaign-package",
        record_type=ExperimentPackage, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    if _identity(package, "package_id") != selection.original_package:
        raise PermissionError("configured E3 export substitutes its selected original issued package")
    with read_protected_e3_original_products(selected=selected, artifact_writer=artifact_writer,
            run_id=selection.run_id, expected_package=package, reveal_authority_id=selection.reveal_authority_id) as read:
        full = ConfiguredMatrixSelectedFrozenPackage(selection.frozen_package_record_id,
            read.specification, read.allocation, read.prefit, read.models, read.model_freeze,
            read.calibration, read.calibrated_freeze,
            tuple(sorted((*read.allocation.unit_ids("calibration"), *read.allocation.unit_ids("evaluation")))))
        public = ConfiguredMatrixSelectedPublicPackage.from_package(full)
        products = tuple((name, *_original_product(read, selection, name, operation, mode))
            for name, operation, mode in _PRODUCTS)
        parents = tuple(parent for _, _, rows in products for parent in rows)
        # These locators form one scientific export package. Give every member
        # the complete package lineage and inherited access class, preserving
        # irreversible exposure and atomic publication across all products.
        writes = (_write_request(selection, "package.json", public, parents, logical_id=public.record_id),
            *(_write_request(selection, name + ".locator.json", locator, parents,
                logical_id=locator.prior_execution.binding_id) for name, locator, _ in products))
        # Canonicalization precedes the final live source, custody and grant
        # check. Atomic publication retains exact replay/foreign-path refusal.
        read.require_current()
        publications = artifact_writer.write_batch(writes)
        report = {"selection": selection.identity.to_document(), "run_id": selection.run_id,
            "original_package": selection.original_package.to_document(),
            "frozen_package": full.identity.to_document(), "public_package": public.identity.to_document(),
            "products": {name: locator.to_document() for name, locator, _ in products},
            "scientific_result": dict(read.report), "native_contact": "none",
            "paths": {name: str(artifact_writer.root.resolve(selection.output_relative_path + "/" + filename, for_write=False))
                for name, filename in (("package", "package.json"),
                    *((name, name + ".locator.json") for name, _, _ in products))},
            "publications": [publication.to_document() for publication in publications]}
    return report
