# SPDX-License-Identifier: MPL-2.0
"""Partition portable checks without changing the complete portable selector."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest


# These bounded modules run on every CI event; reviewed low-cost changes can supplement them.
CI_FILES = frozenset({
    'tests/test_owned_output_publication.py',
    'tests/test_publication_memory_lifetime.py',
    'tests/test_operational_progress_lifecycle.py',
    'tests/test_artifact_sidecar_reuse.py',
    'tests/test_recursive_ancestry_metadata_cache.py',
    'tests/test_recursive_validation_lifetime.py',
    'tests/test_rubisco_periodic_mm_revisions.py',
    'tests/test_rubisco_retained_analysis_inspection.py',
    'tests/test_electrostatics.py',
    'tests/test_quantum_burnin_native_operators.py',
    'tests/test_reduced_artifact_verification.py',
    'tests/test_rubisco_preparation_environment.py',
    'tests/test_rubisco_preparation_response_decisions.py',
    'tests/runtime_platform/test_remote_sizing.py',
    'tests/test_v1_retained_diagnostics.py',
    'tests/test_v1_scope_process_boundary.py',
    'tests/test_v1_scientific_ownership.py',
    'tests/test_coverage_inventory.py',
    'tests/test_test_purposes.py',
    'tests/test_exact_binomial_recurrence.py',
    'tests/test_retained_gaussian_response.py',
    'tests/test_joint_response_methods.py',
    'tests/test_classical_series_aggregate.py',
    'tests/test_classical_matrix_capstones.py',
    'tests/test_classical_series_science.py',
    'tests/test_classical_series_workflow.py',
    'tests/test_classical_series_cli.py',
    'tests/test_matrix_model_free_science.py',
    'tests/test_model_free_authoring.py',
    'tests/test_model_free_cli.py',
    'tests/test_model_free_equilibrium_suppliers.py',
    'tests/test_model_free_paired_estimators.py',
    'tests/test_model_free_protocol_work.py',
    'tests/test_model_free_receiver_authoring.py',
    'tests/test_model_free_receiver_equilibrium_events.py',
    'tests/test_model_free_receiver_observations.py',
    'tests/test_model_free_receiver_response.py',
    'tests/test_model_free_response_failures.py',
    'tests/test_model_free_comparators.py',
    'tests/test_model_free_native_correctness.py',
    'tests/test_model_free_response.py',
    'tests/test_model_free_statistics.py',
    'tests/test_model_free_workflow.py',
    'tests/test_parameter_relations.py',
    'tests/test_retained_analysis_custody.py',
    'tests/test_matrix_history_science.py',
    'tests/test_v1_capacity.py',
    'tests/test_v1_diagnostics.py',
    'tests/test_v1_calculation.py',
    'tests/test_v1_investigations.py',
    'tests/kernel/test_authoring_parse_reuse.py',
    'tests/kernel/test_canonical_encoding_storage.py',
    'tests/kernel/test_decimal_custody_characterization.py',
    'tests/kernel/test_decoder_policy_corpus.py',
    'tests/kernel/test_decoding_bounds.py',
    'tests/kernel/test_evidence_and_time.py',
    'tests/kernel/test_resource_budget.py',
    'tests/kernel/test_scoped_record_validation.py',
    'tests/kernel/test_serialization.py',
    'tests/kernel/test_time_validation.py',
    'tests/test_cli_contracts.py',
    'tests/test_changed_test_acceptance.py',
    'tests/test_configuration.py',
    'tests/test_configuration_schemas.py',
    'tests/test_import_boundaries.py',
    'tests/test_operational_configuration.py',
    'tests/test_arb_context.py',
    'tests/test_recursive_inquiry_policy.py',
    'tests/test_recursive_multiple_parents.py',
    'tests/test_recursive_public_service.py',
    'tests/test_recursive_target_assessment.py',
    'tests/test_release_candidate_check.py',
    'tests/test_release_check.py',
    'tests/test_release_portable_evidence.py',
    'tests/test_release_selected_source.py',
    'tests/test_release_source_archive.py',
    'tests/test_release_wheel_source.py',
    'tests/test_source_origin_module_shapes.py',
    'tests/test_robust_inquiry_service.py',
    'tests/test_workflow_discovery.py',
})

# These positive and refusal cases must survive collection and marker filtering.
# Whole bounded modules above remain the partition unit; this floor prevents a
# renamed or newly optional critical case from silently leaving push/PR CI.
CI_REQUIRED_CASES = frozenset({
    'tests/test_v1_investigations.py::test_public_authoring_accepts_complete_native_study_without_external_operands',
    'tests/test_retained_analysis_custody.py::test_unlimited_consuming_allowance_retains_committed_extent_and_digest',
    'tests/test_classical_series_aggregate.py::test_authored_settings_preserve_cells_when_every_root_readout_is_missing',
    'tests/test_classical_series_workflow.py::test_real_native_supplier_stays_sealed_through_wrapper_and_conf_commitment',
    'tests/test_recursive_validation_lifetime.py::test_retained_parent_finishes_before_main_read_pool_closes[True-inquiry_authoring_read]',
    'tests/test_recursive_validation_lifetime.py::test_copied_context_after_close_gets_a_fresh_cpu_pool',
    'tests/test_rubisco_retained_analysis_inspection.py::test_default_read_keeps_original_results_without_running_analysis',
    'tests/test_rubisco_retained_analysis_inspection.py::test_original_bytes_are_checked_after_publication_closing_checks',
    'tests/test_v1_scope_process_boundary.py::test_fork_with_parent_thread_holding_ledger_lock_authenticates_child_afresh',
    'tests/test_v1_scope_process_boundary.py::test_fork_with_parent_thread_holding_record_store_lock_decodes_child_afresh',
    'tests/test_v1_scope_process_boundary.py::test_fork_refuses_inherited_callback_lock_and_accepts_child_owned_plane',
    'tests/test_arb_context.py::test_rank_and_battery_keep_their_precision_until_conversion[roots]',
    'tests/test_arb_context.py::test_rank_and_battery_keep_their_precision_until_conversion[assessment]',
    'tests/test_arb_context.py::test_rank_and_battery_keep_their_precision_until_conversion[preparation]',
    'tests/test_arb_context.py::test_nested_precision_restores_after_success_and_exceptions',
    'tests/test_recursive_inquiry_policy.py::test_target_completion_requires_all_claims_and_all_four_scientific_supply_phases',
    'tests/test_recursive_multiple_parents.py::test_multiple_exact_receipt_parents_author_run_export_and_relocate',
    'tests/test_recursive_multiple_parents.py::test_parent_collection_is_complete_canonical_census_without_two_parent_limit',
    'tests/test_recursive_public_service.py::test_public_service_preserves_adverse_census_and_recovers_without_native[default-serial]',
    'tests/test_recursive_public_service.py::test_public_service_preserves_adverse_census_and_recovers_without_native[detected-parallel]',
    'tests/test_recursive_public_service.py::test_public_service_preserves_adverse_census_and_recovers_without_native[explicit-parallel]',
    'tests/test_recursive_target_assessment.py::test_actual_independent_assessment_satisfies_only_its_exact_analytic_target',
    'tests/test_recursive_target_assessment.py::test_public_commit_refuses_unsupported_target_before_publication[raw-source]',
    'tests/test_recursive_target_assessment.py::test_public_commit_refuses_unsupported_target_before_publication[wrong-claim]',
    'tests/test_recursive_target_assessment.py::test_public_commit_refuses_unsupported_target_before_publication[wrong-scope]',
    'tests/test_recursive_target_assessment.py::test_public_commit_refuses_unsupported_target_before_publication[falsified-disposition]',
    'tests/test_recursive_target_assessment.py::test_public_commit_refuses_unsupported_target_before_publication[physical-target]',
    'tests/test_recursive_target_assessment.py::test_current_read_rejects_old_unassessed_success_and_preserves_archive',
    'tests/test_recursive_target_assessment.py::test_current_read_requires_the_registered_assessor_again',
    'tests/test_robust_inquiry_service.py::test_missing_target_persists_v3_hold_with_unentered_frontier',
})
CI_NUMERICAL_REQUIRED_CASES = frozenset({
    'tests/test_joint_response_methods.py::test_complex_joint_krylov_residual_and_reused_prefixes',
    'tests/test_joint_response_methods.py::test_exact_finite_grid_anchor_variance_bridge_is_not_continuum_endpoint',
    'tests/test_classical_matrix_capstones.py::test_frozen_forecast_supplies_actual_prepared_descriptor_to_fixed_coefficients',
    'tests/test_quantum_burnin_native_operators.py::test_two_site_action_and_cutoff_follow_analytic_rabi_clock',
    'tests/test_rubisco_preparation_environment.py::test_common_direction_preserves_mutant_sign_and_receiver_atom_exclusion',
    'tests/test_rubisco_preparation_response_decisions.py::test_signed_decimal_contrast_does_not_depend_on_ambient_precision',
    'tests/test_exact_binomial_recurrence.py::test_large_denominator_and_unattainable_threshold_remain_exact',
    'tests/test_retained_gaussian_response.py::test_pasted_quartic_against_original_two_dimensional_partition_functions',
    'tests/test_retained_gaussian_response.py::test_equal_equilibrium_geometry_has_distinct_history_and_correct_preparation_force',
    'tests/test_matrix_history_science.py::test_positive_gram_matches_independent_kronecker_oracle',
    'tests/test_matrix_history_science.py::test_noncommuting_midpoint_in_y_against_independent_ode',
    'tests/test_v1_scientific_ownership.py::test_signed_native_join_has_independent_analytic_control',
})
CI_REQUIRED_CASES |= CI_NUMERICAL_REQUIRED_CASES
# Explicit large populations, payloads, memory probes and compiler scaling.
SCALE_FILES = frozenset({
    'tests/test_retained_native_records.py',
    'tests/test_generic_profile_volume.py',
    'tests/test_operational_capacity_transport.py',
    'tests/api/test_execution_plan_capacity.py',
    'tests/infrastructure/test_catalog_memory_concurrency.py',
    'tests/runtime_platform/test_prospective_source_companion_capacity.py',
    'tests/runtime_platform/test_qualified_parent_read_scaling.py',
    'tests/runtime_platform/test_study_issue_large_population.py',
    'tests/test_current_result_capacity.py',
    'tests/test_finite_response_rerun_authoring.py',
    'tests/test_finite_response_rerun_integrity.py',
    'tests/test_finite_response_rerun_latency.py',
    'tests/test_integration_recursive_handoff_capacity.py',
    'tests/test_matrix_e3_protected_scaling.py',
    'tests/test_matrix_e4_full_factor_root_scaling.py',
    'tests/test_matrix_experiment_scaling.py',
    'tests/test_matrix_geometry_integration.py',
    'tests/test_matrix_selected_e4_record_capacity.py',
    'tests/test_metadata_memory_override.py',
    'tests/test_metadata_memory_reclamation.py',
    'tests/test_reactor_public_lifecycle.py',
    'tests/test_recursive_custody_memory.py',
    'tests/test_recursive_prospective_bounded_capacity.py',
    'tests/test_recursive_typed_custody_memory.py',
    'tests/test_unrestricted_artifact_custody.py',
    'tests/test_unrestricted_source_resolution.py',
})
PARTITION_PROFILES = ("ci", "integration", "scale")


def validate_shard(profile: str, index: int, count: int) -> None:
    if type(index) is not int or type(count) is not int or not 0 <= index < count:
        raise ValueError("test shard requires integer 0 <= index < count")
    if profile not in ("integration", "scale") and (index, count) != (0, 1):
        raise ValueError("only integration and scale profiles support shards")


def validate_declarations(root: Path) -> None:
    if CI_FILES & SCALE_FILES:
        raise ValueError("CI and scale declarations overlap")
    missing = sorted(name for name in CI_FILES | SCALE_FILES if not (root / name).is_file())
    if missing:
        raise ValueError(f"test profile declarations name missing modules: {missing}")


def profile_for(nodeid: str) -> str:
    module = nodeid.split("::", 1)[0]
    if module in CI_FILES:
        return "ci"
    return "scale" if module in SCALE_FILES else "integration"


def module_shard(nodeid: str, count: int) -> int:
    """Keep all cases and module fixtures together, independent of test order."""
    module = nodeid.split("::", 1)[0]
    return int.from_bytes(hashlib.sha256(module.encode()).digest(), "big") % count


def selection_record(nodeids: list[str], profile: str, index: int = 0, count: int = 1, *, extra_nodeids=()) -> dict:
    if profile not in PARTITION_PROFILES:
        raise ValueError("unknown portable partition profile")
    validate_shard(profile, index, count)
    if len(nodeids) != len(set(nodeids)):
        raise ValueError("test collection contains duplicate node IDs")
    extra = set(extra_nodeids)
    if extra and (profile != "ci" or not extra <= set(nodeids)):
        raise ValueError("changed bounded cases must belong to the current eligible CI census")
    selected = sorted(nodeid for nodeid in nodeids
                      if nodeid in extra or profile_for(nodeid) == profile and module_shard(nodeid, count) == index)
    encoded = ("\n".join(selected) + "\n").encode()
    census = ("\n".join(sorted(nodeids)) + "\n").encode()
    return {
        "schema": "empirical-lawhood/tests/portable-partition",
        "profile": profile, "shard_index": index, "shard_count": count,
        "eligible_collected_cases": len(nodeids),
        "eligible_nodeids_sha256": hashlib.sha256(census).hexdigest(),
        "profile_case_counts": dict(sorted(Counter(map(profile_for, nodeids)).items())),
        "selected_cases": len(selected), "selected_nodeids": selected,
        "selected_nodeids_sha256": hashlib.sha256(encoded).hexdigest(),
        "scope": "Collected portable cases after pytest marker selection; collection is not execution or acceptance.",
    }


def require_ci_contracts(record: dict) -> None:
    if record["profile"] == "ci":
        missing = sorted(CI_REQUIRED_CASES - set(record["selected_nodeids"]))
        if missing:
            raise ValueError(f"CI is missing required recursive contract cases: {missing}")
        if "verification_purposes" in record:
            required = CI_NUMERICAL_REQUIRED_CASES & CI_REQUIRED_CASES
            invalid = sorted(node for node in required
                             if record["verification_purposes"].get(node, {}).get("purpose") != "numerical")
            if invalid:
                raise ValueError(
                    "CI is missing required independent numerical references; load "
                    f"scripts.test_purposes and retain each oracle declaration: {invalid}")


def pytest_addoption(parser):
    group = parser.getgroup("portable test profiles")
    group.addoption("--test-profile", choices=PARTITION_PROFILES)
    group.addoption("--test-shard-index", type=int, default=0)
    group.addoption("--test-shard-count", type=int, default=1)
    group.addoption("--test-selection-output", type=Path)
    group.addoption("--test-execution-output", type=Path)
    group.addoption("--bounded-changes-since")
    group.addoption("--changed-tests-base")
    group.addoption("--changed-test-evidence", type=Path, action="append", default=[])


def pytest_configure(config):
    profile = config.getoption("test_profile")
    if profile is None:
        raise pytest.UsageError("select --test-profile when loading scripts.test_profiles")
    try:
        validate_shard(profile, config.getoption("test_shard_index"), config.getoption("test_shard_count"))
        validate_declarations(config.rootpath)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error
    if config.option.markexpr != "not native and not held" or config.option.keyword:
        raise pytest.UsageError("portable partitions require -m 'not native and not held' without -k")
    if config.args != ["tests"]:
        raise pytest.UsageError("portable partitions require the complete tests directory")
    review = config.getoption("changed_tests_base")
    bounded = config.getoption("bounded_changes_since")
    if (review and bounded) or (config.getoption("changed_test_evidence") and not review):
        raise pytest.UsageError("select one change comparison; evidence requires --changed-tests-base")
    if (review or bounded) and profile != "ci":
        raise pytest.UsageError("changed-test supplementation belongs to the ci profile")
    config._el_execution = _ExecutionCensus(config)
    config.pluginmanager.register(config._el_execution, "test-execution-census")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    # Wrap the ordinary marker selector so native/held cases are already excluded.
    all_cases = [(item.nodeid, tuple(marker.name for marker in item.iter_markers())) for item in items]
    config._el_execution.collected = len(all_cases)
    yield
    if any(item.get_closest_marker(name) for item in items for name in ("native", "held")):
        raise pytest.UsageError("portable partition contains a native or held case")
    eligible = [item.nodeid for item in items]
    extra, changed = (), None
    review = config.getoption("changed_tests_base")
    base = review or config.getoption("bounded_changes_since")
    if base:
        if __package__:
            from .test_change_policy import changed_test_selection
        else:
            from test_change_policy import changed_test_selection
        try:
            extra, changed = changed_test_selection(config.rootpath, base, all_cases, eligible, profile_for, CI_FILES,
                evidence_paths=config.getoption("changed_test_evidence"), audit=bool(review))
        except (ValueError, OSError, KeyError) as error:
            raise pytest.UsageError(str(error)) from error
    record = selection_record(eligible, config.getoption("test_profile"),
                              config.getoption("test_shard_index"), config.getoption("test_shard_count"), extra_nodeids=extra)
    purposes = getattr(config, "_el_test_purposes", {})
    selected_purposes = {node: purposes[node] for node in record["selected_nodeids"] if node in purposes}
    record["verification_purposes"] = selected_purposes
    record["verification_purpose_counts"] = dict(sorted(Counter(
        row["purpose"] for row in selected_purposes.values()).items()))
    record["verification_purpose_scope"] = (
        "Numerical cases name independent references; other cases claim software conformance only. "
        "Purpose is independent of cost, native/held selection, execution outcome and scientific qualification.")
    if changed is not None:
        record["changed_tests"] = changed
    destination = config.getoption("test_selection_output")
    if destination is not None:
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    try:
        require_ci_contracts(record)
        if changed is not None and changed["errors"]:
            raise ValueError("changed-test acceptance refused: " + "; ".join(changed["errors"]))
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error
    selected = set(record["selected_nodeids"])
    config._el_execution.selected = selected
    config._el_execution.changed = changed
    deselected = [item for item in items if item.nodeid not in selected]
    items[:] = [item for item in items if item.nodeid in selected]
    config.hook.pytest_deselected(items=deselected)


class _ExecutionCensus:
    def __init__(self, config):
        self.config, self.collected = config, 0
        self.selected, self.reports, self.changed = set(), {}, None
        self.collection_failures = 0

    def pytest_collectreport(self, report):
        self.collection_failures += int(report.failed)

    def pytest_runtest_logreport(self, report):
        purpose = getattr(self.config, "_el_test_purposes", {}).get(report.nodeid, {})
        row = self.reports.setdefault(report.nodeid, {
            "executed": False, "failed": False, "skipped": False, **purpose})
        row["executed"] |= report.when == "call"
        row["failed"] |= report.failed
        row["skipped"] |= report.skipped or "Required release-profile check skipped:" in str(report.longrepr)

    def pytest_sessionfinish(self, session, exitstatus):
        destination = self.config.getoption("test_execution_output")
        if destination is None:
            return
        drift = []
        for row in (self.changed or {}).get("changes", []):
            if "sha256" in row:
                path = self.config.rootpath / row["path"]
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                    drift.append(row["path"])
        if drift:
            session.exitstatus = 1
        value = {"schema": "empirical-lawhood/tests/execution-census-v1", "profile": self.config.getoption("test_profile"),
                 "collected": self.collected, "selected": len(self.selected),
                 "deselected": self.collected - len(self.selected),
                 "executed": sum(row["executed"] for row in self.reports.values()),
                 "skipped": sum(row["skipped"] for row in self.reports.values()),
                 "failed": sum(row["failed"] for row in self.reports.values()),
                 "passed": sum(row["executed"] and not row["failed"] and not row["skipped"] for row in self.reports.values()),
                 "collection_failures": self.collection_failures,
                 "collection_only": bool(self.config.option.collectonly), "exit_code": int(session.exitstatus),
                 "changed_test_drift": drift, "cases": self.reports,
                 "scope": "Actual test-body execution; collection and explicit exclusions are not passes."}
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
