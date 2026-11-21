# SPDX-License-Identifier: MPL-2.0
"""Verify the selected developer file against the documented one-cell RC contract.

This explicitly executes trusted local Python. It is separate from installed
extension discovery and supplies no source admission or scientific authority.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

from empirical_lawhood.domains.circuits.rc_ladder_numerical_comparison.contracts import ResistorCapacitorLadderEvaluationConfig
from empirical_lawhood.domains.circuits.rc_ladder import campaign
from empirical_lawhood.domains.circuits.rc_ladder.contracts import ResistorCapacitorLadderNativePanel, ResistorCapacitorLadderStudyConfig
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _roundtrip(record, record_type):
    _require(type(record) is record_type, "selected file returned the wrong canonical record type")
    raw = record.canonical_bytes()
    recovered = decode_canonical_bytes(raw, record_type, maximum_bytes=512 * 1024)
    _require(recovered == record, "selected record changed during canonical round trip")
    return raw


def _no_native(*args, **kwargs):
    raise RuntimeError("evaluation-only verification attempted another native source call")


def verify_selected_file(module_path: Path, output_dir: Path) -> dict:
    """Prepare the selected model once, then verify and retain its actual outputs."""
    module_path = module_path.resolve(strict=True)
    _require(module_path.is_file(), "select a regular developer module")
    with module_path.open("rb") as stream:
        source = stream.read(256 * 1024 + 1)
    _require(len(source) <= 256 * 1024, "selected developer module exceeds 256 KiB")
    output_dir = output_dir.absolute()
    output_dir.mkdir(parents=True, exist_ok=False)
    checksum = sha256(source).hexdigest()
    report = {
        "status": "FAILED", "module_path": str(module_path), "module_sha256": checksum,
        "output_dir": str(output_dir), "model_preparation_calls": 0,
        "scope": "Disclosed one-cell numerical development check; no physical qualification or execution authority.",
    }
    module_name = "_selected_worked_rc_" + checksum
    module = ModuleType(module_name)
    module.__file__ = str(module_path)
    sys.modules[module_name] = module
    try:
        # Compile the selected bytes directly: do not create a bytecode cache
        # beside the contributor's file or load a stale cached implementation.
        exec(compile(source, str(module_path), "exec"), module.__dict__)
        _require(callable(getattr(module, "local_study", None))
                 and callable(getattr(module, "local_panels", None)),
                 "selected module must define local_study and local_panels")
        report["model_preparation_calls"] = 1
        study = module.local_study()
        study_bytes = _roundtrip(study, ResistorCapacitorLadderStudyConfig)
        _require(study.model.scale_cells == 1, "the worked check requires the declared one-cell model")
        (output_dir / "study.json").write_bytes(study_bytes)
        panels = module.local_panels(study)
        _require(type(panels) is tuple and len(panels) == 2,
                 "selected file must return the two declared nested solver views")
        _require({panel.view_id for panel in panels} == set(campaign.VIEWS),
                 "selected panels change the declared solver-view census")
        for panel in panels:
            raw = _roundtrip(panel, ResistorCapacitorLadderNativePanel)
            _require(panel.unit_id == study.unit_id and panel.times_seconds == study.model.output_times_seconds,
                     "selected panel changes its independent unit or clock grid")
            allowance = 1e-12 if panel.view_id == "matrix-exponential" else 2e-4
            for clock, row in zip(panel.times_seconds, panel.node_voltages_volts, strict=True):
                expected = (1 - math.exp(-2 * float(clock))) / 2
                _require(len(row) == 1 and abs(float(row[0]) - expected) <= allowance,
                         "selected output fails the independent circuit equation dV/dt = 1 - 2V")
                _require(Decimal(0) <= row[0] < Decimal("0.5"), "selected output violates the declared voltage bound")
            (output_dir / f"{panel.view_id}.json").write_bytes(raw)

        with ExitStack() as stack:
            stack.enter_context(patch.object(module, "local_panels", _no_native))
            if hasattr(module, "run_native_view"):
                stack.enter_context(patch.object(module, "run_native_view", _no_native))
            for target in (
                "campaign.run_native_view", "campaign.solve_matrix_exponential", "campaign.solve_backward_euler",
                "matrix_exponential.solve_matrix_exponential", "refinement.solve_backward_euler",
            ):
                stack.enter_context(patch("empirical_lawhood.domains.circuits.rc_ladder." + target, _no_native))
            config = ResistorCapacitorLadderEvaluationConfig("rc-worked.evaluation-config", study, True)
            _roundtrip(config, ResistorCapacitorLadderEvaluationConfig)
            result = campaign.check_native_views(study, panels)
            _require(result.converged and result.independent_unit_count == 1 and result.nested_view_count == 2,
                     "selected result does not meet the declared numerical check and unit census")
            negative = campaign.check_native_views(replace(study, maximum_view_defect_volts=Decimal("1e-8")), panels)
            _require(not negative.converged and "VOLTAGE_VIEW_DEFECT_ABOVE_FROZEN_LIMIT" in negative.reason_codes,
                     "the tighter tolerance must retain its negative numerical result")
            try:
                replace(study.model, capacitances_farads=(Decimal(0),))
            except ValueError as error:
                _require("must be positive" in str(error), "zero capacitance refused for an unexpected reason")
            else:
                raise ValueError("zero capacitance was accepted")
            (output_dir / "method-check.json").write_bytes(_roundtrip(result, type(result)))
            (output_dir / "negative-check.json").write_bytes(_roundtrip(negative, type(negative)))

        _require(module_path.read_bytes() == source, "selected module changed during verification")
        report.update(status="PASSED", independent_unit_count=1, nested_view_count=2,
                      checks=["canonical-round-trips", "independent-circuit-equation", "method-only-no-contact",
                              "negative-tolerance", "zero-capacitance-refusal"])
        return report
    except Exception as error:
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        sys.modules.pop(module_name, None)
        (output_dir / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True, help="Trusted local Python file to execute and verify")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for selected-file records and report")
    args = parser.parse_args()
    try:
        report = verify_selected_file(args.module, args.output_dir)
    except Exception as error:
        print(f"Selected-file verification failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
