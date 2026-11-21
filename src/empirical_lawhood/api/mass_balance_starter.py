# SPDX-License-Identifier: MPL-2.0
"""Copied exposed input preparation and retained results without recalculation."""

from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.methods.mass_balance_starter import design, experiment
from empirical_lawhood.methods.mass_balance_starter.records import MAX_BYTES, NAMESPACE, PROTOCOL_ID, MassAssessment, MassEvidence, MassForecast, MassSpecification
from empirical_lawhood.methods.mass_balance_starter.science import prediction_config
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection


def create_inputs(*, evidence_path, tolerance_kg, project_root, output_directory):
    """Freeze exact supplied bytes and derive their pins through typed owners."""
    from empirical_lawhood.api.recursive_authoring import implementation_binding

    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError("starter inputs require a new explicit destination")
    raw = read_bounded_bytes(Path(evidence_path), maximum_bytes=MAX_BYTES)
    evidence = decode_canonical_bytes(raw, MassEvidence, maximum_bytes=MAX_BYTES)
    specification = MassSpecification("specification." + NAMESPACE + "." + evidence.fingerprint(),
        evidence.identity, evidence.scope, evidence.independent_unit_ids, Decimal(tolerance_kg))
    experiment.bind_inputs(specification, {"evidence": evidence})
    source = implementation_binding(project_root)
    sources = ExperimentInputSelection("inputs." + NAMESPACE + "." + specification.fingerprint(), PROTOCOL_ID,
        (ExperimentInputBinding("evidence", evidence.identity, "evidence.json", len(raw)),))
    payloads = {"evidence.json": raw, "specification.json": specification.canonical_bytes(),
                "sources.json": sources.canonical_bytes(), "source-snapshot.json": source.canonical_bytes()}
    destination.mkdir(parents=True, exist_ok=False)
    for name, payload in sorted(payloads.items()):
        with (destination / name).open("xb") as stream:
            stream.write(payload)
    return {"specification": str(destination / "specification.json"), "sources": str(destination / "sources.json"),
            "source_snapshot": str(destination / "source-snapshot.json"), "evidence": evidence.identity.to_document(),
            "qualification": "NOT_ESTABLISHED", "native_contact_count": 0}


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Present original authenticated findings without calling either scientific calculation."""
    if type(specification) is not MassSpecification or instance.specification != specification.identity:
        raise PermissionError("starter read substitutes its original specification")
    count = len(specification.independent_unit_ids)
    base = {"namespace": NAMESPACE, "calculation": specification.calculation,
            "assigned_units": count, "independent_unit_ids": specification.independent_unit_ids,
            "qualification": "NOT_ESTABLISHED", "evidence_scope": "EXPOSED_DEVELOPMENT",
            "scientific_reconstruction_performed": False, "native_acquisition_performed": False}
    if allow_partial or report.get("typed_product_validation") == "DEFERRED":
        return {**base, "scientific_completion": "DEFERRED"}
    name = "experiment-source-" + sha256(specification.evidence.object_id.encode()).hexdigest() + ".json"
    evidence = decode_canonical_bytes(payloads[name], MassEvidence, maximum_bytes=MAX_BYTES)
    experiment.bind_inputs(specification, {"evidence": evidence})
    config = design.config_for(specification, evidence)
    selected = (config, prediction_config(config))
    tasks = {t.task_id: t for t in plan.tasks}
    if set(tasks) != {c.node_id for c in selected} or report.get("run_id") != plan.source_plan.object_id:
        raise PermissionError("starter read changes the complete original task or run census")
    found = {}
    for c in selected:
        receipt = products["receipts"].get(c.node_id)
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            continue
        kind = MassAssessment if c.phase == "assess" else MassForecast
        value = products["records"].get(c.node_id, {}).get(c.node_id + ".product")
        if (type(value) is not kind or value.config != c
                or (receipt.run_id, receipt.task_id) != (plan.source_plan.object_id, c.node_id)):
            raise PermissionError("starter read substitutes a typed original producing result")
        value.__post_init__()
        found[c.phase] = value
    if "assess" not in found:
        return {**base, "scientific_completion": "INCOMPLETE", "completed_operations": len(found), "findings": ()}
    assessment = found["assess"]
    if "predict" not in found or assessment.forecast != found["predict"].identity:
        raise PermissionError("starter read loses its exact retained forecast predecessor")
    counts = {key: sum(r.disposition == key for r in assessment.rows) for key in ("SATISFIED", "FALSIFIED", "UNEVALUABLE")}
    return {**base, "scientific_completion": "COMPLETED", "completed_operations": len(found),
        "claim_disposition": "FALSIFIED" if counts["FALSIFIED"] else "UNEVALUABLE" if counts["UNEVALUABLE"] else "SATISFIED",
        "forecast_supply_disposition": "SATISFIED", "counts": counts, "tolerance_kg": str(config.tolerance_kg),
        "assessment": assessment.identity.to_document(), "forecast": assessment.forecast.to_document(),
        "findings": tuple({"unit_id": r.unit_id, "predicted_kg": str(r.predicted_kg),
            "observed_kg": None if r.observed_kg is None else str(r.observed_kg),
            "absolute_error_kg": None if r.absolute_error_kg is None else str(r.absolute_error_kg),
            "disposition": r.disposition, "reason_codes": r.reason_codes} for r in assessment.rows)}
