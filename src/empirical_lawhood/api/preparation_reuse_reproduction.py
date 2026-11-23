# SPDX-License-Identifier: MPL-2.0
"""Reproduce the five closed preparation-and-reuse studies from their public operands."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
from multiprocessing import get_context
from os import sched_getaffinity
from pathlib import Path

from threadpoolctl import threadpool_limits

from .preparation_reuse_operands import open_released_operands


def _boundary(data):
    from empirical_lawhood.domains.matrix.constructed_preparation_applicability.config import (
        ConstructedPreparationStage,
    )
    from empirical_lawhood.domains.matrix.constructed_preparation_applicability.records import (
        ConstructedPreparationLowerSeal,
        ConstructedPreparationMeasuredRoot,
        ConstructedPreparationReport,
    )
    from empirical_lawhood.domains.matrix.constructed_preparation_applicability.reproduction import (
        historical_boundary,
        replay_boundary_phase,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.original_f import OriginalFiniteResponseLaw

    lower = data.record("lower", OriginalFiniteResponseLaw)
    result = {"interrupted_qualification": data.document("interrupted")}
    for phase, count in (("Q", 8), ("E", 32)):
        stage = data.record(phase + "/stage", ConstructedPreparationStage)
        if (
            len(stage.root_ids) != count
            or stage.source.object_fingerprint != data.members[phase + "/source"]["sha256"]
        ):
            raise ValueError("Released constructor stage changes the assigned source or census")
        data.raw(phase + "/source")
        roots = [
            (
                data.record(f"{phase}/{i:03d}/measurement", ConstructedPreparationMeasuredRoot),
                data.record(f"{phase}/{i:03d}/seal", ConstructedPreparationLowerSeal),
                data.document(f"{phase}/{i:03d}/boundary"),
            )
            for i in range(count)
        ]
        result[phase] = replay_boundary_phase(
            stage,
            lower,
            roots,
            data.record(phase + "/report", ConstructedPreparationReport),
            data.context["diagnostic_bootstrap"][phase],
        )
    result["historical"] = historical_boundary([data.document(f"historical/{i:03d}") for i in range(32)])
    return result


def _verify_sealed(assignment, *, directory, label, qualification, lower):
    from empirical_lawhood.domains.matrix.finite_response_law.control_closeout import (
        FiniteResponseLawRootSealedControl,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.control_reveal import (
        FiniteResponseLawProspectiveRootEvaluation,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.sealed_evaluation_reproduction import (
        sealed_root_readout,
    )

    i, operand, views = assignment
    prefix = f"{label}/{i:03d}"
    with open_released_operands(directory, "r24") as data, threadpool_limits(limits=1):
        seal = data.record(prefix + "/seal", FiniteResponseLawRootSealedControl)
        reveal = data.record(prefix + "/reveal", FiniteResponseLawProspectiveRootEvaluation)
        original = data.document(prefix)
        current = sealed_root_readout(
            seal=seal, reveal=reveal, views=views, lower=lower, qualification=qualification, inference=operand
        )
        stored = {k: v for k, v in original.items() if k not in ("original_receipts", "input_receipts")}
        if json.loads(json.dumps(current, default=str)) != stored:
            raise ValueError(
                "Original seals and revealed assays do not recover the published root " + operand.root_id
            )
        return operand.root_id


def _evaluation(data, *, directory, from_seals, workers):
    from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import (
        FiniteResponseLawAssignedCalibrationNativeEvaluation,
        FiniteResponseLawAssignedEvaluationNativeCompletion,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.evaluation_reproduction import (
        historical_handoff_errors,
        replay_evaluation,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.evaluation_results import (
        FiniteResponseLawEvaluationCohort,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.law_payloads import (
        FiniteResponseLawLowerPayload,
    )
    from empirical_lawhood.domains.matrix.finite_response_law.method_records import (
        FiniteResponseLawAssignedQualificationReport,
    )
    from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord

    qualification = data.record("qualification", FiniteResponseLawAssignedQualificationReport)
    lower = data.record("lower", FiniteResponseLawLowerPayload)
    interrupted = data.document("interrupted")
    if len(interrupted) != 64 or any(r["evaluable_service_episodes"] for r in interrupted):
        raise ValueError("Interrupted evaluation requires the original 64 unevaluable assignments")
    result = {
        "interrupted": {"roots": interrupted, "dispositions": Counter(r["disposition"] for r in interrupted)}
    }
    calibration = data.record("calibration/native", FiniteResponseLawAssignedCalibrationNativeEvaluation)
    calibration_roots = [unit.stage_unit for unit in calibration.config.projection.native_spec.roots]
    if len(calibration_roots) != 32 or len(calibration.views) != 64:
        raise ValueError("Incomplete native calibration roster")
    result["calibration"] = {
        "roots": calibration_roots,
        "numerical_views": len(calibration.views),
        "native_sha256": calibration.fingerprint(),
        "qualification_sha256": qualification.fingerprint(),
        "evaluation_eligible": qualification.eligible_for_prospective_evaluation,
        "joint_opportunities": dict(qualification.calibration.joint_opportunities),
    }
    units = {r["physical_unit"] for r in interrupted}
    for label in ("retained", "disjoint"):
        cohort = data.record(label + "/cohort", FiniteResponseLawEvaluationCohort)
        native = data.record(label + "/native", FiniteResponseLawAssignedEvaluationNativeCompletion)
        terminal = data.record(label + "/terminal", ScientificAdjudicationRecord)
        rows = (data.document(f"{label}/{i:03d}") for i in range(64))
        result[label] = replay_evaluation(cohort, native, qualification, lower, rows)
        if from_seals:
            lookup = {(v.root.stage_unit, v.refinement): v for v in native.views}
            tasks = [
                (i, operand, (lookup[operand.root_id, 1], lookup[operand.root_id, 2]))
                for i, operand in enumerate(cohort.operands)
            ]
            check = partial(
                _verify_sealed, directory=directory, label=label, qualification=qualification, lower=lower
            )
            if workers == 1:
                verified = list(map(check, tasks))
            else:
                with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn")) as pool:
                    verified = list(pool.map(check, tasks, chunksize=1))
            if verified != [r.root_id for r in cohort.operands]:
                raise ValueError("Sealed root verification lost an assigned physical unit")
        result[label]["issued_decision"] = terminal.scientific_status.value
        result[label]["run"] = terminal.run_id
        units.update(r["physical_unit"] for r in result[label]["roots"])
    result["historical"] = historical_handoff_errors(
        [data.document(f"historical/{i:03d}") for i in range(64)]
    )
    if len(units) != 192:
        raise ValueError("Interrupted, retained and disjoint evaluation assignments overlap")
    return result


def _closed_origin(science):
    return {
        key: science[key]
        for key in (
            "source_run",
            "source",
            "source_terminal_status",
            "source_terminal_sha256",
            "framework_evidence_ceiling",
            "preserved_original_refusals",
            "reconstructed_products",
        )
    }


def _waveforms(data):
    from empirical_lawhood.domains.matrix.preparation_applicability.waveform_evaluation import WaveformCohort
    from empirical_lawhood.domains.matrix.waveform_preparation.reproduction import replay_waveforms

    original = data.document("closeout")
    cohort = data.record("cohort", WaveformCohort)
    if original["analysis_files"]["cohort.canonical.json"] != cohort.fingerprint():
        raise ValueError("Closed waveform panel differs from its published independent reduction")
    return dict(
        replay_waveforms(cohort, data.document("ordinary")), original_operation=_closed_origin(original)
    )


def _handoffs(data):
    from empirical_lawhood.domains.matrix.model_free.handoff_reproduction import replay_handoffs

    original = data.document("closeout")
    if original["analysis_files"]["assigned-roots.json"] != data.members["roots"]["sha256"]:
        raise ValueError("Closed handoff panels differ from their published independent reduction")
    result = replay_handoffs(
        data.document("definition"), data.document("roots"), original, data.document("handoffs")
    )
    return dict(result, original_operation=_closed_origin(original))


def _screen(data):
    from empirical_lawhood.domains.matrix.finite_response_law.historical_preparation_screen import (
        replay_historical_screen,
    )
    from .finite_operands import load_original_f_operand

    lower = load_original_f_operand(payload_id="released.preparation-screen.lower")
    panels = [(data.members[f"panel/{i:03d}"]["sha256"], data.document(f"panel/{i:03d}")) for i in range(24)]
    index = data.document("receipt-index")
    for name, member in data.members.items():
        if member["source"] == "tier2" and index[member["path"]]["sha256"] != member["sha256"]:
            raise ValueError("Historical screen operand differs from the original receipt index")
    freeze = data.document("upper-freeze")
    if (
        freeze["value"]["screen_result"]["value"]["object_fingerprint"]
        != data.members["screen-result"]["sha256"]
    ):
        raise ValueError("Historical upper freeze belongs to a different screen")
    return dict(
        replay_historical_screen(
            panels,
            lower,
            data.document("screen-result"),
            data.document("scientific-adjudication"),
            freeze,
            data.document("original-fit-audit"),
        ),
        provenance=data.context,
    )


def reproduce_preparation_reuse(
    *, study: str, operand_directory: Path, from_seals: bool = False, workers: int = 1
):
    """Re-execute the analyses on revealed operands. Requires no authority or new native acquisition."""
    if type(workers) is not int or workers < 1:
        raise ValueError("Select a positive worker count")
    if from_seals and study != "r24":
        raise ValueError("Optional sealed-control reconstruction applies to R24")
    if from_seals and min(64, workers) > len(sched_getaffinity(0)):
        raise ValueError("Select available CPUs for the sealed-control read")
    evaluation = partial(_evaluation, directory=operand_directory, from_seals=from_seals, workers=workers)
    with open_released_operands(operand_directory, study) as data, threadpool_limits(limits=1):
        result = {"r23": _boundary, "r24": evaluation, "r25": _waveforms, "r26": _handoffs, "r27": _screen}[
            study
        ](data)
        return {
            "study": study,
            "scope": "EXPOSED_NUMERICAL_REPRODUCTION",
            "new_native_acquisitions": 0,
            "new_qualification": False,
            "result": result,
        }
