"""Exact Tier 1 calibration roster preflight, without native acquisition."""

from __future__ import annotations
from empirical_lawhood.domains.matrix.finite_response_law.authoring.native_input import FiniteResponseLawCalibrationInput as _science_FiniteResponseLawCalibrationInput

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters._strict_json import loads_external_json
from empirical_lawhood.domains.matrix.finite_response_law.authoring.assignment import FiniteResponseLawCohortAssignment, assigned_native_seed_ids
from empirical_lawhood.domains.matrix.finite_response_law.authoring.exposure import native_seed_ids, native_seed_collisions
from empirical_lawhood.adapters.composition.prepared_response.native_authoring import _read_external, _read_plan
from empirical_lawhood.domains.matrix.finite_response_law.science import FiniteResponseLawScienceSpec
from empirical_lawhood.adapters.simulators.finite_response_law.calibration.discovery import SOURCE_CAPABILITY
from empirical_lawhood.domains.matrix.finite_response_law.fresh_contracts import FiniteResponseLawCalibrationConfig, calibration_invocations
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import require_sorted_unique_strings, validate_stable_id




def _census(raw: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    document = loads_external_json(raw)
    if not isinstance(document, dict) or not isinstance(document.get("schema"), str):
        raise TypeError("finite response-law exposure is not a typed document")
    if (
        document["schema"].split("/", 1)[-1]
        != 'methods/finite-response-law/native-exposure-metadata'
    ):
        raise ValueError("finite response-law exposure has another contract")
    result = []
    for names in (
        ("excluded_unit_ids", "proposed_unit_ids"),
        ("excluded_seed_ids", "proposed_seed_ids"),
    ):
        combined: set[str] = set()
        for name in names:
            values = document.get(name)
            if not isinstance(values, list):
                raise TypeError(f'finite response-law exposure lacks {name}')
            selected = tuple(values)
            require_sorted_unique_strings(selected, field_name=name)
            for entry in selected:
                validate_stable_id(entry, field_name=name)
            combined.update(selected)
        if not combined:
            raise ValueError("finite response-law exposure lacks a prior census")
        result.append(tuple(sorted(combined)))
    return result[0], result[1]


def check_finite_calibration_input(
    config: _science_FiniteResponseLawCalibrationInput,
    *,
    source_root: Path | None,
    plan: Path | None,
    prior_exposure: Path | None,
    assignment: FiniteResponseLawCohortAssignment | None = None,
) -> dict[str, object]:
    "Check the retained calibration cohort roster against a selected held census."

    if source_root is None:
        raise ValueError("FINITE_RESPONSE_LAW_SOURCE_ROOT_REQUIRED")
    if plan is None:
        raise ValueError("FINITE_RESPONSE_LAW_PLAN_REQUIRED")
    if prior_exposure is None:
        raise ValueError("FINITE_RESPONSE_LAW_PRIOR_EXPOSURE_REQUIRED")
    plan_sha = sha256(_read_plan(plan)).hexdigest()
    science = FiniteResponseLawScienceSpec()
    if plan_sha != science.plan_sha256:
        raise ValueError("FINITE_RESPONSE_LAW_PLAN_MISMATCH: plan differs from frozen science")
    prior_raw, _ = _read_external(source_root, prior_exposure, 128 * 1024**2)
    excluded_units, excluded_seeds = _census(prior_raw)
    if assignment is not None:
        if (
            assignment.stage != config.stage
            or assignment.science_plan_sha256 != plan_sha
        ):
            raise ValueError("FINITE_RESPONSE_LAW_ASSIGNMENT_MISMATCH: stage or frozen plan")
        units = assignment.physical_unit_ids
        seeds = assigned_native_seed_ids(assignment)
        unit_collisions = set(units) & set(excluded_units)
        seed_collisions = native_seed_collisions(seeds, excluded_seeds)
        if unit_collisions or seed_collisions:
            raise ValueError(
                "FINITE_RESPONSE_LAW_EXPOSED_ASSIGNED_ROSTER: "
                f"{len(unit_collisions)} units, {len(seed_collisions)} streams"
            )
        return {
            "config_id": config.config_id,
            "stage": config.stage,
            "assignment_sha256": assignment.fingerprint(),
            "cohort_namespace": assignment.cohort_namespace,
            "native_plan_sha256": plan_sha,
            "prior_exposure_sha256": sha256(prior_raw).hexdigest(),
            "prior_custody_authenticated": False,
            "independent_units": len(units),
            "streams_reserved": len(seeds),
            "binding_selected": 'FiniteResponseLawCalibrationSourceFactory',
            "provider_built": False,
            "source_contract_compatible": True,
            "missing_port_keys": [],
            "native_task_budget": 640,
            "native_updates_budget": 751104,
            "native_tasks_planned": 0,
            "native_tasks_executed": 0,
            "campaign_candidate_compiled": False,
            "campaign_issued": False,
            "status": "FINITE_RESPONSE_LAW_ASSIGNMENT_RESERVED_USE_STAGE_SELECTOR",
            "evidence_role": config.evidence_role,
        }
    source = FiniteResponseLawCalibrationConfig(
        "calibration",
        science,
        ObjectIdentity.from_record(SOURCE_CAPABILITY.capability_key, SOURCE_CAPABILITY),
        None,
        (),
    )
    units = tuple(sorted(root.physical_unit_id for root in source.roots))
    seeds = native_seed_ids(source)
    unit_collisions = set(units) & set(excluded_units)
    seed_collisions = native_seed_collisions(seeds, excluded_seeds)
    if unit_collisions or seed_collisions:
        raise ValueError(
            "FINITE_RESPONSE_LAW_EXPOSED_CALIBRATION_ROSTER: "
            f"{len(unit_collisions)} units, {len(seed_collisions)} streams"
        )
    tasks = calibration_invocations(source)
    return {
        "config_id": config.config_id,
        "stage": config.stage,
        "native_plan_sha256": plan_sha,
        "prior_exposure_sha256": sha256(prior_raw).hexdigest(),
        "prior_custody_authenticated": False,
        "independent_units": len(units),
        "native_tasks_planned": len(tasks),
        "native_updates_planned": sum(task.maximum_native_updates for task in tasks),
        "streams_reserved": len(seeds),
        "native_tasks_executed": 0,
        "campaign_candidate_compiled": False,
        "campaign_issued": False,
        "status": "FINITE_RESPONSE_LAW_PARENT_CUSTODY_REQUIRED",
        "evidence_role": config.evidence_role,
    }


__all__ = ['check_finite_calibration_input']
