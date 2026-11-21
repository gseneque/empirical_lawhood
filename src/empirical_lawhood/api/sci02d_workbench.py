# SPDX-License-Identifier: MPL-2.0
"""Selected SCI02-D recorded views and explicit full owning reconstruction."""

from collections import Counter
from decimal import Decimal
import math
import struct

from empirical_lawhood.api.application_contracts import ApplicationError
from empirical_lawhood.api.application_projections import projection


def _exact_values(value):
    """Transport binary64 values without JavaScript rounding or JSON NaNs."""
    if type(value) is float:
        return Decimal.from_float(value) if math.isfinite(value) else {"binary64_bits": struct.pack("!d", value).hex()}
    if isinstance(value, dict):
        return {key: _exact_values(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_exact_values(item) for item in value)
    return value


def _selected_context(payloads, draft):
    from empirical_lawhood.api.experiment_scientific_read import _development_runtime_context
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.experiment import BridgeSpecification
    selected = _development_runtime_context(payloads=payloads, draft=draft, callback_name="read_development_result")
    if selected is None or type(selected[1]) is not BridgeSpecification:
        raise ApplicationError("UNSUPPORTED_SCI02D_SELECTION", "Select an original SCI02-D training or confirmation wave.")
    return selected


def _consume_recorded(**kwargs):
    from empirical_lawhood.api.matrix_sci02d import read_recorded_result
    _binding, specification, instance = _selected_context(kwargs["payloads"], kwargs["draft"])
    return read_recorded_result(specification=specification, instance=instance, **kwargs)


def read_sci02d(*, directory, plane, reconstruct=False):
    """Bind the exact family before the ordinary complete custody read."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    if type(reconstruct) is not bool:
        raise TypeError("SCI02-D reconstruction needs an explicit boolean")
    with plane.read_context() as reader:
        _packet, draft, _source, payloads = load_authored_wave(directory=directory, artifact_writer=reader, lazy_payloads=True)
        _selected_context(payloads, draft)
        report, _roots = _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=reader,
            terminal_product_format="documents" if reconstruct else "references",
            expected_specification_bytes=payloads["experiment-specification.json"],
            _scientific_consumer=None if reconstruct else _consume_recorded)
        reader.require_verification_snapshot()
    return _exact_values(report)


def sci02d_projection(report, *, request, parameters):
    """Keep historical availability, scientific uncertainty and execution separate."""
    report = _exact_values(report)
    science = report["scientific_result"]
    if science.get("read_scope") != "AUTHENTICATED_HISTORICAL_SCI02D_FINDINGS":
        raise ValueError("Recorded SCI02-D projection requires its actual historical read scope")
    rows = science["root_findings"]
    summary = {"execution_status": report["status"], "assigned_tasks": report["task_count"],
        "assigned_roots": science["assigned_roots"], "tranche": science["tranche"],
        "bank_census": dict(sorted(Counter(row["bank"] for row in rows).items())),
        "recorded_dispositions": dict(sorted(Counter(row.get("disposition", "UNKNOWN") for row in rows).items())),
        "scientific_completion": science["scientific_completion"], "qualification": science["qualification"],
        "equilibrium_state_coverage": science["equilibrium_state_coverage"],
        "molecular_requirement": science["molecular_requirement"],
        "new_native_contacts_this_read": report["new_native_contact_count"],
        "original_completed_native_contacts": science["original_completed_native_contacts"],
        "inquiry_outcome": "NOT_SUPPLIED_BY_THIS_WAVE_READ", "claim_assessment": "NOT_SUPPLIED_BY_THIS_WAVE_READ"}
    aggregate = {key: science[key] for key in ("pooled_product", "pooled_disposition", "pooled_reasons",
        "pooled_measurements", "frozen_fit") if key in science}
    # Retain compact uncertainty and complete count arrays. The explicit full
    # read owns the complete array report; ordinary pages never export it.
    aggregate["uncertainty_and_counts"] = {key: value for key, value in science.get("pooled_arrays", {}).items()
        if key in ("reference_mean_half", "reference_nine_mean_half", "bias_half", "view_mean_half",
            "preparation_mean_half", "chronological_mean_half", "quadrature_mean_half", "variance_ratios",
            "coverage_counts", "coverage_binomial_intervals", "conservative_coverage_counts",
            "individual_sampling_precision_counts", "reference_adjusted_point_error_counts", "diagnostic_passes")}
    return projection(request=request, kind="sci02d", title=report["run_id"],
        identity={key: report[key] for key in ("packet_sha256", "draft_sha256", "execution_plan_sha256")},
        scope=science["read_scope"], summary=summary, records=rows, parameters=parameters,
        aggregate=aggregate, design=science["design"], selection=science["selection"],
        costs={"components": science["cost_components"], "scope": science["cost_scope"],
            "this_read_cpu_seconds": science["read_cpu_seconds"], "this_read_wall_seconds": science["read_wall_seconds"]},
        provenance={key: report[key] for key in ("packet_sha256", "draft_sha256", "execution_plan_sha256",
            "producing_code_sha256", "dependency_lock_sha256", "observed_producing_git_head", "producing_provenance_sha256")},
        value_semantics="Authenticated historical products and their original arrays. Independent force, transition and fit reconstruction was not performed. Root banks and nested views retain their original denominators. Finite binary64 values use exact Decimal images; nonfinite values retain their IEEE bits.")
