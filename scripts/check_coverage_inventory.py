# SPDX-License-Identifier: MPL-2.0
"""Check coverage source paths and the explicitly claimed measured owners."""

from __future__ import annotations

import argparse
from configparser import ConfigParser
import json
from pathlib import Path


CRITICAL_MEASURED_MODULES = frozenset({
    'src/empirical_lawhood/api/domain_composition/rubisco_response/native_analysis_export.py',
    'src/empirical_lawhood/science/records/decoded_record_store.py',
    'src/empirical_lawhood/storage/artifacts.py',
    'src/empirical_lawhood/storage/owned_output.py',
    'src/empirical_lawhood/storage/artifact_verification.py',
    'src/empirical_lawhood/storage/parallel_verification.py',
    'src/empirical_lawhood/storage/canonical_record_read.py',
    'src/empirical_lawhood/methods/retained_gaussian_response.py',
    'src/empirical_lawhood/domains/rubisco/rubisco_response/preparation_response_environment.py',
    'src/empirical_lawhood/domains/rubisco/rubisco_response/preparation_response_assessment.py',
    'src/empirical_lawhood/domains/circuits/rc_prerequisite_chain/scientific_binding.py',
    'src/empirical_lawhood/domains/battery/battery_recursive_construction/scientific_binding.py',
    'src/empirical_lawhood/domains/circuits/rc_prerequisite_chain/operation_bindings.py',
    'src/empirical_lawhood/api/recursive_authoring.py',
    'src/empirical_lawhood/api/recursive_inquiry.py',
    'src/empirical_lawhood/api/recursive_inquiry_evidence.py',
    'src/empirical_lawhood/api/recursive_execution.py',
    'src/empirical_lawhood/api/recursive_contributions.py',
    'src/empirical_lawhood/api/recursive_prospective_authoring.py',
    'src/empirical_lawhood/api/recursive_qualified_parents.py',
    'src/empirical_lawhood/science/inquiry/recursive_requirements.py',
    'src/empirical_lawhood/science/inquiry/recursive_inquiry.py',
    'src/empirical_lawhood/science/inquiry/recursive_inquiry_policy.py',
    'src/empirical_lawhood/science/inquiry/scientific_contributions.py',
    'src/empirical_lawhood/design/recursive_authoring.py',
    'src/empirical_lawhood/design/recursive_input_origins.py',
    'src/empirical_lawhood/design/recursive_inquiry.py',
    'src/empirical_lawhood/design/recursive_inquiry_policy.py',
    'src/empirical_lawhood/execution/recursive_compiler.py',
    'src/empirical_lawhood/execution/recursive_inquiry.py',
    'src/empirical_lawhood/execution/recursive_handoff.py',
    'src/empirical_lawhood/execution/recursive_prospective.py',
    'src/empirical_lawhood/execution/recursive_qualified_parents.py',
    'src/empirical_lawhood/execution/recursive_provider.py',
    'src/empirical_lawhood/execution/native_effects.py',
    'src/empirical_lawhood/storage/contracts/artifacts.py',
    'src/empirical_lawhood/execution/native_subwork.py',
    'src/empirical_lawhood/storage/native_effect_custody.py',
    'src/empirical_lawhood/storage/native_subwork.py',
    'src/empirical_lawhood/execution/local/native_subwork_ipc.py',
    'src/empirical_lawhood/storage/file_locks.py',
    'src/empirical_lawhood/storage/recursive_custody.py',
    'src/empirical_lawhood/storage/recursive_prospective_inputs.py',

    "src/empirical_lawhood/storage/development_native_custody.py",
    "src/empirical_lawhood/api/rc_prerequisite_chain.py",
    "src/empirical_lawhood/domains/circuits/rc_prerequisite_chain/contracts.py",
    "src/empirical_lawhood/domains/circuits/rc_prerequisite_chain/science.py",

    "src/empirical_lawhood/api/codecs.py",
    "src/empirical_lawhood/api/current_result_custody.py",
    "src/empirical_lawhood/api/integration_proof.py",
    "src/empirical_lawhood/api/matrix_numerical_provenance.py",
    "src/empirical_lawhood/science/identity/numerical_provenance.py",
    "src/empirical_lawhood/science/records/parsed_nodes.py",
    "src/empirical_lawhood/execution/native_time_grid.py",
    "src/empirical_lawhood/science/records/serialization.py",
    "src/empirical_lawhood/science/records/decoding.py",
    "src/empirical_lawhood/adapters/_bounded_files.py",
    "src/empirical_lawhood/storage/bounded_io.py",
    "src/empirical_lawhood/storage/artifact_validation.py",
    "src/empirical_lawhood/adapters/matrix_storage/matrix_array_io.py",
    "src/empirical_lawhood/api/facade.py",
    "src/empirical_lawhood/storage/sql/database.py",
    "src/empirical_lawhood/storage/sql/migrations/versions/initial_catalog.py",
})


def validate_configuration(checkout: Path) -> None:
    config = ConfigParser()
    if not config.read(checkout / ".coveragerc"):
        raise ValueError("coverage configuration is missing")
    patterns = config.get("run", "include").split()
    if not patterns:
        raise ValueError("coverage source inventory is empty")
    selected = set()
    for pattern in patterns:
        matches = {path.relative_to(checkout).as_posix() for path in checkout.glob(pattern) if path.is_file()}
        if not matches:
            raise ValueError(f"coverage include has no source match: {pattern}")
        selected.update(matches)
    missing = sorted(CRITICAL_MEASURED_MODULES - selected)
    if missing:
        raise ValueError(f"required coverage owners excluded by configuration: {missing}")


def validate_measured_inventory(checkout: Path, coverage_json: Path) -> None:
    root = checkout.resolve()
    measured = set()
    unexecuted = set()
    report = json.loads(coverage_json.read_text())
    for filename, details in report["files"].items():
        path = Path(filename)
        if not path.is_absolute():
            path = root / path
        try:
            selected = path.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        measured.add(selected)
        if selected in CRITICAL_MEASURED_MODULES:
            lines = details.get("executed_lines") if isinstance(details, dict) else None
            summary = details.get("summary") if isinstance(details, dict) else None
            covered = summary.get("covered_lines") if isinstance(summary, dict) else None
            if (not isinstance(lines, list) or not lines
                    or any(type(line) is not int or line <= 0 for line in lines)
                    or type(covered) is not int or covered <= 0):
                unexecuted.add(selected)
    missing = sorted(CRITICAL_MEASURED_MODULES - measured)
    if missing:
        raise ValueError(f"required measured coverage owners missing: {missing}")
    if unexecuted:
        raise ValueError(f"required coverage owners have no executed statements: {sorted(unexecuted)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--coverage-json", type=Path)
    args = parser.parse_args()
    validate_configuration(args.checkout)
    if args.coverage_json is not None:
        validate_measured_inventory(args.checkout, args.coverage_json)
    print("coverage source inventory verified" + (
        f"; {len(CRITICAL_MEASURED_MODULES)} required owners with executed statements"
        if args.coverage_json is not None else ""))


if __name__ == "__main__":
    main()
