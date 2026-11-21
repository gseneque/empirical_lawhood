# SPDX-License-Identifier: MPL-2.0
"""Readable and complete tabular integrated findings with exact unknown states."""

import csv
import io

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_cost import FIELDS
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import ARMS
from empirical_lawhood.domains.rubisco.rubisco_response.integrated_report import IntegratedResponseReport
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import OUTPUTS
from empirical_lawhood.domains.rubisco.rubisco_response.report_rendering import _csv, render_endpoint_csv, render_parameter_csv


def _value(value):
    return "UNKNOWN" if value is None else str(value.fraction) if type(value) is Exact else str(value)


def _bounds(values):
    return "UNDEFINED_NO_ADMISSIONS" if values is None else "[" + ", ".join(_value(value) for value in values) + "]"


def _arm_csv(report, renderer, *, parameter=False):
    exact(report, IntegratedResponseReport)
    template = csv.DictReader(io.StringIO(renderer(report.reference)))
    fields = tuple(template.fieldnames)
    result = []
    for arm in report.comparison.arms:
        if arm.report is not None:
            rows = csv.DictReader(io.StringIO(renderer(arm.report)))
            result.extend((arm.arm, *(row[key] for key in fields)) for row in rows)
        else:
            for assignment in report.comparison.design.assignments:
                if assignment.arm != arm.arm:
                    continue
                supply = next(row for row in report.reference.study.supplies if row.case.identity == assignment.case)
                scenario = next(row for row in supply.scenarios if row.scenario_id == assignment.scenario_id)
                for binding in scenario.ledger.bindings if parameter else (None,):
                    values = dict.fromkeys(fields, "UNKNOWN")
                    values.update(case_id=assignment.case.object_id, scenario_id=assignment.scenario_id,
                        original_state="UNKNOWN", point_id=_value(assignment.point_id), reason_codes="ORIGINAL_ARM_NOT_SUPPLIED")
                    if binding is not None:
                        values.update(parameter=binding.parameter, unit=binding.native_unit,
                            remaining_requirement_ids=";".join(binding.unresolved_requirement_ids))
                    result.append((arm.arm, *(values[key] for key in fields)))
    return _csv(("arm", *fields), result)


def render_integrated_endpoints(report):
    return _arm_csv(report, render_endpoint_csv)


def render_integrated_parameters(report):
    return _arm_csv(report, render_parameter_csv, parameter=True)


def render_comparison_csv(report):
    exact(report, IntegratedResponseReport)
    rows = []
    for point in report.comparison.points:
        for arm in ARMS[1:]:
            term = None if point.error is None else point.error.total if arm == "reduced" else point.error.conventional_error
            for index, output in enumerate(OUTPUTS):
                logs = (None, None) if term is None or term.signed_log_bounds is None else term.signed_log_bounds[index]
                error = (None, None) if term is None or term.normalized_absolute_error_bounds is None else term.normalized_absolute_error_bounds[index]
                rows.append((point.case.object_id, point.scenario_id, _value(point.point_id), arm, output,
                    point.original_scenario_state, dict(point.original_arm_states)[arm], dict(point.method_gates)[arm].value,
                    dict(point.arithmetic_gates)[arm].value, point.reference_usable, point.joint_error(arm),
                    *map(_value, logs), *map(_value, error), ";".join(point.reason_codes)))
    return _csv(("case_id", "scenario_id", "point_id", "arm", "output", "original_scenario_state", "original_arm_state",
        "producer_method_gate", "arithmetic_gate", "conditional_reference_usable", "joint_error",
        "reference_minus_arm_log_lower", "reference_minus_arm_log_upper", "normalized_absolute_lower", "normalized_absolute_upper", "reason_codes"), rows)


def render_decision_csv(report):
    exact(report, IntegratedResponseReport)
    rows = []
    for case in report.comparison.cases:
        for index, decision in enumerate(case.decisions or (None,)):
            if decision is None:
                rows.append((case.case.object_id, "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
                    "UNKNOWN", case.causal_order.value, ";".join(case.causal_reason_codes), "MISSING_ORIGINAL_DECISION"))
            else:
                rows.append((case.case.object_id, index, decision.identity.object_id, decision.identity.object_fingerprint,
                    decision.action, decision.decision.selected_alternative_id, ";".join(row.alternative_id for row in decision.menu.alternatives),
                    ";".join(decision.decision.unresolved_target_requirement_ids), case.causal_order.value,
                    ";".join(case.causal_reason_codes), decision.decision.reason))
    return _csv(("case_id", "checkpoint_index", "decision_id", "decision_fingerprint", "actual_action", "selected_alternative",
        "complete_alternatives", "remaining_requirement_ids", "causal_order", "causal_reason_codes", "decision_reason"), rows)


def render_integrated_attempts(report):
    exact(report, IntegratedResponseReport)
    costs = report.comparison.costs
    events = {row.attempt_id: row for row in costs.events}
    bindings = {row.attempt_id: row for row in costs.work_bindings}
    rows = []
    for attempt in costs.attempts:
        work = bindings[attempt.attempt_id].work
        rows.append((attempt.attempt_id, attempt.status.value, attempt.operation.object_id,
            "UNKNOWN" if work is None else work.method.object_id, attempt.receipt.object_id, attempt.receipt.object_fingerprint,
            *(_value(getattr(events[attempt.attempt_id].cost, key)) for key in FIELDS),
            attempt.attempt_id in costs.unclassified_attempt_ids, ";".join(row.object_id for row in attempt.products), attempt.reason))
    return _csv(("attempt_id", "status", "operation_id", "method_id", "receipt_id", "receipt_fingerprint", *FIELDS,
        "unclassified_cost", "product_ids", "reason"), rows)


def render_cost_csv(report):
    exact(report, IntegratedResponseReport)
    costs = report.comparison.costs
    rows = [("complete_selected_campaign", "all", "NOT_APPLICABLE", *(_value(getattr(costs.complete_campaign, key)) for key in FIELDS))]
    for arm in costs.arms:
        for account in ("setup", "incremental_use", "equivalent_audit", "frozen_policy_use", "amortized_total", "amortized_per_use"):
            rows.append((account, arm.arm, arm.planned_reuse_count,
                *(_value(getattr(getattr(arm, account), key)) for key in FIELDS)))
    return _csv(("account", "arm", "planned_reuse_count", *FIELDS), rows)


def render_requirement_csv(report):
    exact(report, IntegratedResponseReport)
    entries = {"requirement." + row.code: row for row in report.native_entry_prerequisites}
    rows = []
    for key in report.remaining_requirement_ids:
        entry = entries.get(key)
        rows.append((key, "UNRESOLVED", "SCIENTIFIC_EVIDENCE" if entry is None else entry.kind.value,
            ";".join(row.component for row in report.milestone.components if key in row.remaining_requirement_ids),
            "See original source-bound finding in readout.json" if entry is None else entry.detail))
    return _csv(("requirement_id", "state", "kind", "milestone_components", "detail"), rows)


def render_integrated_report(report):
    exact(report, IntegratedResponseReport)
    comparison, reference = report.comparison, report.reference
    service, costs = comparison.service, comparison.costs
    lines = [f"Conditional candidate action: {reference.action.conditional_action}. Biological action: {reference.action.biological_action}.",
        f"Combined scientific milestone: {report.milestone.status}. Native entry: {report.native_entry_status}.",
        "", "This is an exposed retained-input integration report. It establishes no native, prospective or biological qualification.",
        "Conditional fidelity and service findings below retain failures and unknowns at their stated scope.",
        "Exact fractions preserve arithmetic; missing-truth bounds are not population confidence intervals.",
        "", "NOMINATION AND REFERENCE FINDINGS"]
    for row in reference.conditional_assessment.nomination_findings:
        lines.append(f"{row.case_id}: nominated direction={row.joint_direction}; nominated magnitude={row.nominated_magnitude}.")
    lines += ["The companion reference-report.txt retains the complete original conditional readout and its narrower scope.",
        "endpoints.csv and parameters.csv include all arms, with explicit UNKNOWN rows for missing originals.",
        "", "COMPLETE COMPARISON CENSUS",
        f"Assignments={len(comparison.design.assignments)}; cases={len(comparison.cases)}; exposure groups={len(service.units)}; biological units=0.",
        f"Selected error scale={comparison.design.scale}; conditional reduced fidelity={comparison.reduced_conditional_fidelity.value}; "
        f"conditional conventional fidelity={comparison.conventional_conditional_fidelity.value}."]
    for row in comparison.points:
        lines.append(f"{row.case.object_id}/{row.scenario_id}/{_value(row.point_id)}: source={row.original_scenario_state}; "
            + "; ".join(f"{arm}={dict(row.original_arm_states)[arm]},method={dict(row.method_gates)[arm].value},arithmetic={dict(row.arithmetic_gates)[arm].value}" for arm in ARMS)
            + f"; joint reduced error={row.joint_error()}; conventional error={row.joint_error('conventional')}.")
        if row.error is not None:
            lines.append("  Signed intermediate stages: " + "; ".join(stage.role + "=" + stage.original_state for stage in row.error.stages) + ".")
    lines += ["", "ORIGINAL POLICY AND SERVICE"]
    for row in comparison.cases:
        lines.append(f"{row.case.object_id}: action={row.action}; retained checkpoints={len(row.decisions)}; causal order={row.causal_order.value}; "
            + "; ".join(row.causal_reason_codes) + ".")
    lines += [f"Useful reduced service={_bounds(service.useful_service_bounds)}; criterion={service.useful_service_disposition.value}.",
        f"False admission, all assigned groups={_bounds(service.false_admission_assigned_bounds)}; admitted groups={_bounds(service.false_admission_conditional_bounds)}.",
        f"Selected false-admission denominator={comparison.design.false_admission_denominator}; criterion={service.false_admission_disposition.value}.",
        f"Fallback={_bounds(service.fallback_bounds)}; complete reference audit={service.reference_coverage_disposition.value}."]
    for unit in service.units:
        lines.append(f"{unit.unit_id}: nested cases=" + ", ".join(unit.case_ids)
            + f"; useful={unit.useful_service}; admitted={unit.admitted}; false={unit.false_admission}; fallback={unit.fallback}; reference complete={unit.reference_complete}.")
    lines += ["", "COMPLETE SELECTED WORK AND THREE COST ACCOUNTS",
        f"Retained attempts={len(costs.attempts)}; physical events={len(costs.events)}; unclassified attempts={len(costs.unclassified_attempt_ids)}; missing planned work={len(costs.missing_work_fingerprints)}.",
        "Complete selected campaign: " + "; ".join(key + "=" + _value(getattr(costs.complete_campaign, key)) for key in FIELDS) + "."]
    for attempt in costs.attempts:
        lines.append(f"{attempt.attempt_id}: {attempt.status.value}; {attempt.reason}")
    for arm in costs.arms:
        lines.append(f"{arm.arm}: complete classification={arm.complete_classification}; reuse count={arm.planned_reuse_count}.")
        for account in ("setup", "incremental_use", "equivalent_audit", "frozen_policy_use", "amortized_total", "amortized_per_use"):
            lines.append("  " + account + ": " + "; ".join(key + "=" + _value(getattr(getattr(arm, account), key)) for key in FIELDS) + ".")
    lines += [f"Conditional cost criterion={costs.conditional_cost_criterion.value}; sustained break-even reuse count={_value(costs.break_even_reuse_count)}.",
        costs.break_even_interpretation + ".", "Unmeasured: " + ", ".join(costs.unmeasured_metric_ids) + ".",
        "Campaign totals cover the supplied original work states. External development or prior supplier expense is not inferred.",
        "Task wall windows are summed, not campaign elapsed time. Reuse costs assume repeated use and audit; no simulator speedup follows.",
        "", "REDUCTION TARGET AND SCIENTIFIC MILESTONE", report.target_assessment.disposition + "."]
    for row in report.target_assessment.candidates:
        lines.append(f"{row.case_id}/{row.scenario_id}/{row.parameter}: original={row.original_scenario_state}; {row.local_meaning}.")
    for row in report.milestone.components:
        lines += [f"{row.component}: {row.disposition.value}.", "  Frozen criterion: " + row.frozen_criterion,
            "  Remaining: " + ", ".join(row.remaining_requirement_ids)]
    lines += ["", "NATIVE ENTRY PREREQUISITES"]
    for row in report.native_entry_prerequisites:
        lines.append(f"{row.code} [{row.kind.value}]: {row.detail}")
    lines += ["", "ORIGINAL CUSTODY"]
    for arm in comparison.arms:
        if arm.report is None:
            lines.append(arm.arm + ": original custody NOT_SUPPLIED.")
        else:
            lines.append(arm.arm + ": " + arm.report.report_id + "@" + arm.report.fingerprint())
            for receipt in arm.report.producing_receipts:
                lines.append(f"  {receipt.receipt_id}@{receipt.fingerprint()}; producing commit={receipt.implementation_commit}; {receipt.operational_status.value}.")
                for material in receipt.output_materializations:
                    lines.append(f"    {material.storage_root_id}:{material.relative_path}; SHA256={material.physical_sha256}; bytes={material.size_bytes}.")
    for decision in comparison.decisions:
        lines.append(f"Decision: {decision.identity.object_id}@{decision.identity.object_fingerprint}; packet={decision.packet.packet_id}@{decision.packet.fingerprint()}.")
    lines += ["", "REMAINING REQUIREMENTS", *report.remaining_requirement_ids,
        "", "The canonical readout preserves complete original reports, policies, attempts, source bindings and scientific findings.",
        "This read/export created zero native calls and zero biological units."]
    return "\n".join(lines) + "\n"
