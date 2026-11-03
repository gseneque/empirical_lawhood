# SPDX-License-Identifier: MPL-2.0
"""Partition portable checks without changing the complete portable selector."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest


# Reviewed bounded contracts. New modules default to integration until reviewed.
CI_FILES = frozenset({
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
    'tests/test_configuration.py',
    'tests/test_configuration_schemas.py',
    'tests/test_import_boundaries.py',
    'tests/test_operational_configuration.py',
    'tests/test_release_candidate_check.py',
    'tests/test_release_check.py',
    'tests/test_release_portable_evidence.py',
    'tests/test_release_selected_source.py',
    'tests/test_release_source_archive.py',
    'tests/test_release_wheel_source.py',
    'tests/test_source_origin_module_shapes.py',
    'tests/test_workflow_discovery.py',
})
# Explicit large populations, payloads, memory probes and compiler scaling.
SCALE_FILES = frozenset({
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


def selection_record(nodeids: list[str], profile: str, index: int = 0, count: int = 1) -> dict:
    if profile not in PARTITION_PROFILES:
        raise ValueError("unknown portable partition profile")
    validate_shard(profile, index, count)
    if len(nodeids) != len(set(nodeids)):
        raise ValueError("test collection contains duplicate node IDs")
    selected = sorted(nodeid for nodeid in nodeids
                      if profile_for(nodeid) == profile and module_shard(nodeid, count) == index)
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


def pytest_addoption(parser):
    group = parser.getgroup("portable test profiles")
    group.addoption("--test-profile", choices=PARTITION_PROFILES)
    group.addoption("--test-shard-index", type=int, default=0)
    group.addoption("--test-shard-count", type=int, default=1)
    group.addoption("--test-selection-output", type=Path)


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


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    # Wrap the ordinary marker selector so native/held cases are already excluded.
    yield
    if any(item.get_closest_marker(name) for item in items for name in ("native", "held")):
        raise pytest.UsageError("portable partition contains a native or held case")
    record = selection_record([item.nodeid for item in items], config.getoption("test_profile"),
                              config.getoption("test_shard_index"), config.getoption("test_shard_count"))
    destination = config.getoption("test_selection_output")
    if destination is not None:
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    selected = set(record["selected_nodeids"])
    deselected = [item for item in items if item.nodeid not in selected]
    items[:] = [item for item in items if item.nodeid in selected]
    config.hook.pytest_deselected(items=deselected)
