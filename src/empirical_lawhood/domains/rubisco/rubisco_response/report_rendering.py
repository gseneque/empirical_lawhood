# SPDX-License-Identifier: MPL-2.0
"""Deterministic human and tabular projections of the full retained report."""

import csv
import io

from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import ReferenceFindingReport
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


def _value(value):
    return "UNKNOWN" if value is None else str(value)


def _bounds(values):
    return "[" + ", ".join(str(value) for value in values) + "]"


def _optional(value):
    return "NOT_SELECTED" if value is None else str(value)


def _rational(value):
    return "UNKNOWN" if value is None else str(value.fraction)


def _csv(fields, rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(fields)
    writer.writerows(rows)
    return output.getvalue()


def render_endpoint_csv(report):
    exact(report, ReferenceFindingReport)
    fields = ("case_id", "scenario_id", "original_state", "point_id", "numerical_assessment",
        "wt_kcat_c_s_inv", "wt_specificity", "mutant_kcat_c_s_inv", "mutant_specificity",
        "anchor_wt_kcat_c_s_inv", "anchor_wt_specificity", "anchored_mutant_kcat_c_s_inv", "anchored_mutant_specificity",
        "turnover_ratio", "specificity_ratio", "log_turnover_lower", "log_turnover_upper",
        "log_specificity_lower", "log_specificity_upper", "reason_codes")
    rows = []
    for row in report.endpoints:
        value = row.retained_value
        endpoints = (None,) * 4 if value is None else (value.wild_type, value.mutant, value.anchor_wild_type, value.anchored_mutant)
        coordinates = tuple("NOT_SELECTED" if index >= 2 and pair is None and value is not None
            else _rational(None if pair is None else getattr(pair, name))
            for index, pair in enumerate(endpoints) for name in ("kcat_c_s_inv", "specificity"))
        ratios = ("UNKNOWN",) * 2 if value is None else tuple(map(str, (value.turnover_ratio, value.specificity_ratio)))
        logs = ("UNKNOWN",) * 4 if row.paired_log_bounds is None else tuple(str(value) for pair in row.paired_log_bounds for value in pair)
        rows.append((row.case_id, row.scenario_id, row.original_state, _value(row.point_id), row.numerical_assessment.value,
                     *coordinates, *ratios, *logs, ";".join(row.reason_codes)))
    return _csv(fields, rows)


def render_parameter_csv(report):
    exact(report, ReferenceFindingReport)
    fields = ("case_id", "scenario_id", "original_state", "point_id", "parameter", "unit", "wt_value", "mutant_value",
        "wt_lower", "wt_upper", "mutant_lower", "mutant_upper", "evidence_kind", "supplier_route",
        "mutation_dependence", "dependence_group", "source_ids", "remaining_requirement_ids")
    rows = []
    for supply in report.study.supplies:
        for scenario in supply.scenarios:
            for point in scenario.points or (None,):
                for binding in scenario.ledger.bindings:
                    bounds = tuple(_value(value) for pair in (binding.wild_type_bounds, binding.mutant_bounds)
                                   for value in (pair if pair is not None else (None, None)))
                    values = tuple(_value(None if point is None else getattr(getattr(point, arm), binding.parameter))
                                   for arm in ("wild_type", "mutant"))
                    rows.append((supply.case.case_id, scenario.scenario_id, scenario.original_state,
                        "UNKNOWN" if point is None else point.point_id, binding.parameter, binding.native_unit,
                        *values, *bounds, binding.evidence_kind, binding.supplier_route, binding.mutation_dependence,
                        binding.dependence_group_id, ";".join(row.object_id for row in binding.sources),
                        ";".join(binding.unresolved_requirement_ids)))
    return _csv(fields, rows)


def render_attempt_csv(report):
    exact(report, ReferenceFindingReport)
    fields = ("attempt_id", "status", "operation_id", "method_id", "receipt_id", "receipt_fingerprint",
              "cpu_seconds", "wall_seconds", "retained_bytes", "product_ids")
    rows = []
    if report.work_state is not None:
        events = {row.attempt_id: row for row in report.work_state.cost_events}
        work = {row.attempt_id: row.work for row in report.work_state.attempt_work_bindings}
        for attempt in report.work_state.operational_census:
            cost = events[attempt.attempt_id].cost
            method = None if work[attempt.attempt_id] is None else work[attempt.attempt_id].method.object_id
            rows.append((attempt.attempt_id, attempt.status.value, attempt.operation.object_id, _value(method),
                attempt.receipt.object_id, attempt.receipt.object_fingerprint,
                *(_value(getattr(cost, key)) for key in ("cpu_seconds", "wall_seconds", "retained_bytes")),
                ";".join(row.object_id for row in attempt.products)))
    return _csv(fields, rows)


def render_reference_report(report):
    """Readable scope first; exact fractions and explicit unknowns throughout."""
    exact(report, ReferenceFindingReport)
    action, study = report.action, report.study
    lines = [f"At the declared conditional rate-support scope, the candidate action is {action.conditional_action}; "
             f"biological action is {action.biological_action} and the combined milestone is {report.milestone.status}.", "",
        "The forecast uses finite joint support, without biological calibration or new native execution.",
        "An adverse candidate finding is distinct from a failed prediction method.",
        "Exact fractions below preserve original values. Log bounds enclose arithmetic rounding only; they are not confidence bounds.",
        "", "NOMINATED PREDICTION AND CANDIDATE ACTION"]
    for finding in report.conditional_assessment.nomination_findings:
        lines.append(f"{finding.case_id}: direction={finding.joint_direction}; nominated magnitude={finding.nominated_magnitude}; "
                     f"original nomination={finding.nominated_prediction.object_id}@{finding.nominated_prediction.object_fingerprint}.")
    for selected, assessed in zip(study.decisions, study.supplies, strict=True):
        finding = next((row for row in report.conditional_assessment.cases if row.supply == assessed.identity), None)
        label = "conditional action" if assessed.case.case_role == "CANDIDATE" else "comparison against candidate thresholds"
        lines.append(f"{assessed.case.case_id} ({assessed.case.case_role}): {label}={finding.conditional_action if finding else 'HOLD'}; "
            f"turnover ratio {'>' if selected.strict_turnover_increase else '>='} {selected.minimum_turnover_ratio}; "
            f"specificity ratio >= {selected.minimum_specificity_ratio}; decision scale={selected.endpoint_view}; "
            f"absolute floors=({_optional(selected.absolute_turnover_floor_s_inv)} s^-1, {_optional(selected.absolute_specificity_floor)}); "
            f"specificity claim={selected.specificity_claim}; next action={selected.next_action}.")
        if assessed.case.case_role == "NO_CHANGE":
            values = tuple(row.retained_value for row in report.endpoints if row.case_id == assessed.case.case_id)
            equal = bool(values) and all(row is not None and row.turnover_ratio == row.specificity_ratio == 1 for row in values)
            accepted = finding is not None and finding.disposition.value == "SATISFIED"
            lines.append("  No-change equality control: " + ("MATCHED" if equal and accepted else "UNRESOLVED_OR_CONTRADICTED") + ".")
    lines += ["", "EXACT CASES AND EXPOSURE"]
    for supply in study.supplies:
        case, context = supply.case, supply.context
        lines += [f"{case.case_id} ({case.case_role}, {case.parent.organism}, processing={case.parent.processing_view}):",
            f"  WT={case.parent.material_id}@{case.parent.fingerprint()}; mutant={case.mutant.material_id}@{case.mutant.fingerprint()}.",
            f"  Finite substitutions={len(case.substitutions)}; original exposure={case.exposure_group}; biological units=0.",
            f"  Assay={context.context_id}; temperature={context.temperature_k} K; pH={_bounds(context.ph_interval)}; chemistry={context.chemistry.protocol_id}.",
            f"  CO2={supply.query.co2_um} uM; O2={supply.query.o2_um} uM; active-site event normalization; physical clock=s."]
    lines += ["", "ENDPOINTS AND COMPLETE SCENARIOS"]
    for row in report.endpoints:
        lines.append(f"{row.case_id} / {row.scenario_id} / {_value(row.point_id)}: original={row.original_state}, numerical={row.numerical_assessment.value}.")
        value = row.retained_value
        if value is None:
            lines.append("  Endpoints=UNKNOWN; reasons=" + "; ".join(row.reason_codes) + ".")
            continue
        lines += [f"  WT: kcat_C={_rational(value.wild_type.kcat_c_s_inv)} s^-1; specificity={_rational(value.wild_type.specificity)} (dimensionless).",
            f"  Mutant: kcat_C={_rational(value.mutant.kcat_c_s_inv)} s^-1; specificity={_rational(value.mutant.specificity)} (dimensionless).",
            f"  Paired ratios: turnover={value.turnover_ratio}; specificity={value.specificity_ratio}.",
            f"  Paired log bounds: turnover={_bounds(row.paired_log_bounds[0])}; specificity={_bounds(row.paired_log_bounds[1])}."]
        if value.anchor_wild_type is not None:
            lines += [f"  WT anchor: kcat_C={_rational(value.anchor_wild_type.kcat_c_s_inv)} s^-1; specificity={_rational(value.anchor_wild_type.specificity)}.",
                f"  Anchored mutant: kcat_C={_rational(value.anchored_mutant.kcat_c_s_inv)} s^-1; specificity={_rational(value.anchored_mutant.specificity)}.",
                "  Shared anchor dependence is retained; anchoring supplies no independent validation."]
        if row.reason_codes:
            lines.append("  Reasons=" + "; ".join(row.reason_codes) + ".")
    unexpected = sorted(set(row.support.case.object_id for row in report.predictions.predictions)
                        - {case.case_id for case in study.cases.cases})
    lines.append("Unexpected retained prediction cases: " + (", ".join(unexpected) or "none") + ".")
    lines += ["", "MECHANISM, ROBUSTNESS AND BIOLOGICAL APPLICABILITY"]
    for reference in report.references:
        for scenario, finding in reference.mechanism_findings:
            lines.append(f"{reference.supply.case.case_id}/{scenario}: {finding}.")
        for row in reference.sensitivities:
            values = "UNKNOWN" if row.maximum_absolute_elasticities is None else ", ".join(_rational(value) for value in row.maximum_absolute_elasticities)
            lines.append(f"  {row.parameter}: maximum absolute endpoint elasticities=({values}); zero-rate endpoint count={_value(row.zero_rate_endpoint_count)}.")
    for row in report.biological_support.cases:
        lines.append(row.case.object_id + ": " + "; ".join(row.assay_flags) + ".")
    lines += ["", "COMPLETE WORK AND COST CENSUS"]
    if report.work_state is None:
        lines.append("Original operational work/cost census=NOT_SUPPLIED; this report is a pure exposed assessment.")
    else:
        for attempt in report.work_state.operational_census:
            lines.append(f"{attempt.attempt_id}: {attempt.status.value}; original witness={attempt.receipt.object_id}@{attempt.receipt.object_fingerprint}; {attempt.reason}")
        cost = report.cost_census.total
        lines.append(f"Original analysis work: CPU={_value(cost.cpu_seconds)} s; summed task wall windows={_value(cost.wall_seconds)} s; retained bytes={_value(cost.retained_bytes)}.")
        lines.append("Prior policy-decision identities: " + (", ".join(row.object_id for row in report.work_state.previous_decisions) or "none retained") + ".")
    lines += ["Comparative campaign, frozen-policy use-time and amortized molecular costs=NOT_ASSESSED.",
        "No supplier speedup, useful-service rate or false-admission rate follows from conditional task expense.",
        "", "COMBINED SCIENTIFIC MILESTONE"]
    for row in report.milestone.components:
        lines += [f"{row.component}: {row.disposition.value}.", "  Criterion: " + row.frozen_criterion,
            "  Evidence: " + (", ".join(value.object_id + "@" + value.object_fingerprint for value in row.evidence) or "not supplied"),
            "  Remaining: " + ", ".join(row.remaining_requirement_ids)]
    lines += ["", "ORIGINAL EVIDENCE AND REPRODUCIBILITY", f"Study: {study.study_id}@{study.fingerprint()}.",
        f"Predictions: {report.predictions.prediction_id}@{report.predictions.fingerprint()}.",
        f"Allocation: {study.allocation.allocation_id}@{study.allocation.fingerprint()}; exposed analytical units={len(study.allocation.units)}; independent biological units=0.",
        f"Frozen acceptance: {study.acceptance.acceptance_id}@{study.acceptance.fingerprint()}."]
    for receipt in report.producing_receipts:
        lines.append(f"Receipt: {receipt.receipt_id}@{receipt.fingerprint()}; producer commit={receipt.implementation_commit}; status={receipt.operational_status.value}.")
        for member in receipt.output_materializations:
            lines.append(f"  Original product: {member.storage_root_id}:{member.relative_path}; SHA256={member.physical_sha256}; bytes={member.size_bytes}.")
    lines += ["No new native calls or biological units were created by this readout.",
        "Machine-readable readout.json retains full sources, rates, scenarios, decisions, exposure, assessments and original work records.",
        "endpoints.csv, parameters.csv and attempts.csv preserve exact values and the complete selected denominators.",
        "", "REMAINING SCIENTIFIC REQUIREMENTS", *report.action.remaining_requirement_ids]
    return "\n".join(lines) + "\n"
