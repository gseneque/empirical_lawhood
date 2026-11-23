# SPDX-License-Identifier: MPL-2.0
"""Select original inputs and read the retained matched-waveform population."""

import json
from pathlib import Path

from empirical_lawhood.api.finite_operands import original_f_operand_import
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.design.experiment_inputs import (
    ExperimentInputBinding,
    ExperimentInputSelection,
)
from empirical_lawhood.domains.matrix.finite_response_law.authoring.rerun_input import (
    FiniteResponseLawCurrentExposure,
)
from empirical_lawhood.domains.matrix.waveform_preparation.bindings import read_operand
from empirical_lawhood.domains.matrix.waveform_preparation.design import configurations
from empirical_lawhood.domains.matrix.waveform_preparation.experiment import bind_inputs
from empirical_lawhood.domains.matrix.waveform_preparation.records import (
    PROTOCOL_ID,
    WaveformOperation,
    WaveformProduct,
    WaveformSpecification,
)
from empirical_lawhood.execution.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def _retained_cohort(specification, instance, report, products, plan):
    if (
        type(specification) is not WaveformSpecification
        or instance.specification != specification.identity
    ):
        raise PermissionError(
            "Waveform reader requires the original scientific definition"
        )
    configs = configurations(specification)
    if {t.task_id for t in plan.tasks} != {c.node_id for c in configs} or report[
        "run_id"
    ] != plan.source_plan.object_id:
        raise PermissionError("Waveform reader changed the original plan or population")
    terminal = None
    for c in configs:
        receipt = products["receipts"].get(c.node_id)
        if (
            receipt is None
            or receipt.operational_status is not OperationalStatus.SUCCEEDED
        ):
            return None
        if (receipt.task_id, receipt.run_id) != (c.node_id, report["run_id"]):
            raise PermissionError("Waveform reader received a foreign receipt")
        row = products["records"].get(c.node_id, {}).get(c.node_id + ".product")
        if type(row) is not WaveformProduct or row.config != c:
            raise PermissionError("Waveform reader substituted a scientific product")
        if c.phase == "cohort":
            terminal = read_operand(row)
    return terminal


def _development_parent(directory, service):
    from empirical_lawhood.api.recursive_execution import (
        _read_recursive_wave_with_retained_roots,
    )

    selected = []

    def consume(*, payloads, report, products, plan, **unused):
        spec = decode_canonical_bytes(
            payloads["experiment-specification.json"],
            WaveformSpecification,
            maximum_bytes=None,
        )
        instance = decode_canonical_bytes(
            payloads["experiment-instance.json"],
            ExperimentInstanceBinding,
            maximum_bytes=None,
        )
        record = _retained_cohort(spec, instance, report, products, plan)
        if (
            record is None
            or record.role != "development"
            or record.disposition != "ENTER_CONFIRMATION"
        ):
            raise ValueError(
                "Waveform confirmation is closed without a complete passing original development screen"
            )
        selected.append(record)
        return {"disposition": record.disposition}

    _read_recursive_wave_with_retained_roots(
        directory=Path(directory),
        artifact_writer=service.artifact_writer,
        include_products=True,
        terminal_product_format="references",
        _scientific_consumer=consume,
    )
    (parent,) = selected
    return parent


def create_inputs(
    *,
    project_root,
    output_directory,
    original_f_directory,
    exposure_path,
    role,
    master_seed,
    bootstrap_seed,
    parent_directory=None,
    parent_service=None,
):
    """Prepare the complete D32 or gated E128 through its original source and data."""
    if (
        (
            role == "development"
            and (parent_directory is not None or parent_service is not None)
        )
        or (
            role == "evaluation"
            and (parent_directory is None or parent_service is None)
        )
        or role not in ("development", "evaluation")
    ):
        raise ValueError(
            "Select development or confirmation with its authenticated parent workspace"
        )
    law_dir = Path(original_f_directory)
    lower = original_f_operand_import(
        law_dir / "original-f.canonical.json", source_directory=law_dir
    )
    raw = read_bounded_bytes(Path(exposure_path), maximum_bytes=64 * 1024**2)
    exposure = decode_canonical_bytes(
        raw, FiniteResponseLawCurrentExposure, maximum_bytes=len(raw)
    )
    source = implementation_binding(Path(project_root))
    parent = (
        None
        if role == "development"
        else _development_parent(parent_directory, parent_service)
    )
    spec = WaveformSpecification(
        f"specification.waveform-preparation.{role}.{master_seed:032x}",
        role,
        master_seed,
        bootstrap_seed,
        lower.identity,
        source.code_sources_sha256,
        source.dependency_lock_sha256,
        source.fingerprint(),
        exposure.identity,
        None if parent is None else parent.identity,
    )
    records = {"lower": lower, "exposure": exposure}
    if parent is not None:
        records["development"] = parent
    bind_inputs(spec, records)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    bindings = []
    for name, record in sorted(records.items()):
        raw = record.canonical_bytes()
        path = output / (name + ".json")
        path.write_bytes(raw)
        bindings.append(
            ExperimentInputBinding(name, record.identity, path.name, len(raw))
        )
    selection = ExperimentInputSelection(
        "inputs." + spec.fingerprint(), PROTOCOL_ID, tuple(bindings)
    )
    for name, record in (
        ("specification", spec),
        ("sources", selection),
        ("source-snapshot", source),
    ):
        (output / (name + ".json")).write_bytes(record.canonical_bytes())
    return {
        "specification": str(output / "specification.json"),
        "sources": str(output / "sources.json"),
        "source_snapshot": str(output / "source-snapshot.json"),
        "assigned_waveforms": spec.count,
    }


def _root_readout(row):
    return {
        "root": row.draw.unit_id,
        "observation": row.fingerprint(),
        "complete": row.complete,
        "covered_pairs": list(row.measured.covered_counts),
        "false_admissions": list(row.measured.false_admissions),
        "conjuncts": list(row.measured.conjuncts),
        "native_intervals": row.native_intervals,
        "primary_margin": None if row.primary.margin is None else str(row.primary.margin),
        "signed_port_two": [None if value is None else str(value) for value in row.signed_port_two],
        "failures": list(row.failures),
    }


def read_result(
    *,
    directory,
    artifact_writer,
    specification,
    instance,
    payloads,
    report,
    products,
    draft,
    plan,
    allow_partial=False,
):
    base = {
        "role": specification.role,
        "assigned_waveforms": specification.count,
        "new_native_acquisitions": 0,
        "scientific_reconstruction_performed": False,
        "framework_evidence_ceiling": "NON_PROMOTABLE",
    }
    if allow_partial or report.get("typed_product_validation") == "DEFERRED":
        return dict(base, scientific_completion="DEFERRED")
    result = _retained_cohort(specification, instance, report, products, plan)
    if result is None:
        return dict(base, scientific_completion="INCOMPLETE")
    terminal = WaveformOperation(specification, "cohort", None)
    return dict(
        base,
        scientific_completion="COMPLETED",
        disposition=result.disposition,
        statistics=json.loads(result.statistics_json),
        cohort=result.identity.to_document(),
        cohort_task=terminal.node_id,
        cohort_receipt=products["receipts"][terminal.node_id].receipt_id,
        roots=[_root_readout(row) for row in result.rows],
    )
