"""Authenticated evaluator access to the measured force face and matched child panels."""

from empirical_lawhood.domains.matrix.constructed_preparation_applicability.diagnostic_records import PreparationDiagnosticPhaseInput
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.phase_records import ConstructedPreparationPanel, ConstructedPreparationPrefix
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.records import ConstructedPreparationMeasuredRoot, ConstructedPreparationReport
from empirical_lawhood.domains.matrix.preparation_applicability.boundary_observations import measured_boundary_observations
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane

from .constructed_preparation_applicability import _authenticate
from .preparation_diagnostics import _phase_access, _phase_metadata
from .preparation_inputs import _retained_output
from .preparation_result_access import preparation_output_reader


def read_preparation_boundary_observations(
    phase: PreparationDiagnosticPhaseInput, *, artifact_writer: ExternalArtifactPlane,
) -> dict:
    """Read every assigned Q or E root under its exact issued execution and reveal grants."""
    if type(phase) is not PreparationDiagnosticPhaseInput:
        raise TypeError("Select the original receipt-bound preparation diagnostic phase")
    current = _phase_access(phase, artifact_writer=artifact_writer)
    plan, receipts, _ = _phase_metadata(phase, artifact_writer=artifact_writer, authenticated_access=current)
    output_writer = preparation_output_reader(artifact_writer, plan, receipts["ap.report"].output_logical_artifacts[0])

    def checked_access(*, context, receipt, logical, writer):
        if (
            context is not phase.result_access or writer is not output_writer
            or receipts.get(receipt.task_id) is not receipt or logical not in receipt.output_logical_artifacts
        ):
            raise PermissionError("The requested measurement falls outside this authenticated phase")

    def read(task, kind):
        record, _ = _retained_output(plane=output_writer, receipt=receipts[task], kind=kind,
                                     result_access=phase.result_access, access_authenticator=checked_access)
        return record

    try:
        stage = phase.selection.stage
        _authenticate(phase.selection, artifact_writer, artifact_writer)
        lower = next(item.record for item in phase.selection.upstream_records if item.key == "lower")
        summary = read("ap.report", ConstructedPreparationReport)
        if (
            summary.phase != stage.phase or summary.root_ids != stage.root_ids
            or summary.allocation_sha256 != stage.allocation.fingerprint()
            or summary.source_sha256 != stage.source.object_fingerprint
            or summary.design_sha256 != stage.design.fingerprint()
            or summary.lower_sha256 != stage.upstream[0].artifact.sha256
        ):
            raise ValueError("Retained report differs from the selected phase or its source and lower law")
        rows = []
        for root_id, expected in zip(summary.root_ids, summary.measurement_sha256s, strict=True):
            measured = read(f"ap.measure.{root_id}", ConstructedPreparationMeasuredRoot)
            if measured.root_id != root_id or measured.fingerprint() != expected:
                raise ValueError("The original report selected another root measurement")
            rows.append(measured_boundary_observations(
                prefix=read(f"ap.prefix.{root_id}", ConstructedPreparationPrefix),
                panel=read(f"ap.assay.{root_id}", ConstructedPreparationPanel), measured=measured, lower=lower,
            ))
    finally:
        if _phase_access(phase, artifact_writer=artifact_writer) != current:
            raise PermissionError("Execution or reveal authority changed while reading the phase")
    return {
        "phase": summary.phase, "run_id": phase.result_access.run_id,
        "phase_input_sha256": phase.fingerprint(), "report_receipt": phase.report_receipt_id,
        "report_sha256": summary.fingerprint(), "disposition": summary.disposition,
        "assigned": len(rows), "new_native_acquisitions": 0, "rows": rows,
    }
