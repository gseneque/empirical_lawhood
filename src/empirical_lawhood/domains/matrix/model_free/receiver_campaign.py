# SPDX-License-Identifier: MPL-2.0
"""Root custody and decision accounting for the receiver-specific matrix experiments."""

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from time import perf_counter, process_time

from .records import MODULES, PREREQUISITES

REVISION = "matrix-receiver-study.v2"
WORK = (
    "native_force_evaluations",
    "native_hessian_actions",
    "native_energy_evaluations",
)


def owner(module):
    if module in ("M0", "M1", "M2"):
        from . import receiver_observations

        return receiver_observations
    if module in ("M3", "M4"):
        from . import receiver_response

        return receiver_response
    if module == "M5":
        from . import receiver_population

        return receiver_population
    from . import receiver_equilibrium_events

    return receiver_equilibrium_events


def decimal_value(value, name, *, minimum=Decimal(0), maximum=None, strict=True):
    """Preserve the operator's decimal text, rejecting booleans and binary floats."""
    if type(value) is not str:
        raise ValueError(f"{name} requires an exact decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{name} requires an exact decimal string") from error
    if (
        not number.is_finite()
        or number < minimum
        or strict
        and number == minimum
        or maximum is not None
        and number > maximum
    ):
        raise ValueError(f"{name} is outside its declared range")
    return number


def normalise_receiver_study(value, base):
    if (
        type(value) is not dict
        or value.get("revision") != REVISION
        or "instrument" not in value
        or set(value) - {"revision", "instrument", *MODULES}
    ):
        raise ValueError(
            "Select an explicit receiver-study revision and declared modules"
        )
    from .receiver_preparation import instrument_operands

    instrument = value.get("instrument")
    if instrument is not None:
        instrument_operands(instrument)
    resolved = {"revision": REVISION, "instrument": deepcopy(instrument)}
    for module in MODULES:
        implementation = owner(module)
        defaults = implementation.DEFAULTS[module]
        choices = value.get(module, {})
        if type(choices) is not dict or set(choices) - set(defaults):
            raise ValueError(f"Unknown {module} receiver-study selection")
        selection = deepcopy(defaults)
        selection.update(deepcopy(choices))
        implementation.validate(module, selection, base)
        resolved[module] = selection
    return resolved


def _check_cases(settings, module, cases):
    ids = [case["case_id"] for case in cases]
    expected = owner(module).case_ids(settings, module)
    if (
        len(set(ids)) != len(ids)
        or set(ids) != set(expected)
        or any(case.get("status") not in ("COMPLETED", "UNAVAILABLE") for case in cases)
    ):
        raise ValueError(
            f"{module} receiver-study result changes its assigned cases or status"
        )


def acquire(settings, seed, module, prerequisites, sampling, assigned_modules):
    from .science import settings_fingerprint

    required = set(PREREQUISITES.get(module, ()))
    if set(prerequisites) != required:
        raise ValueError(f"{module} requires its original receiver-study inputs")
    for name, operand in prerequisites.items():
        if (
            operand.get("seed"),
            operand.get("module"),
            operand.get("receiver_revision"),
        ) != (seed, name, REVISION):
            raise ValueError(
                "Receiver study substitutes another seed, module or definition"
            )
    start = perf_counter()
    data = owner(module).acquire(
        settings,
        seed,
        module,
        prerequisites,
        sampling,
        tuple(assigned_modules or (module,)),
    )
    if module == "M1" and set(assigned_modules or ()) & {"M3", "M5"}:
        from .receiver_preparation import prepare_pairs

        selected = {"nominal"}
        for downstream in ("M3", "M4"):
            if downstream in assigned_modules:
                selected.update(owner(downstream).case_ids(settings, downstream))
        coordinates = [
            row for row in settings["native"]["coordinates"] if row["id"] in selected
        ]
        before_cpu = process_time()
        refinements = (1, 2, 4) if "M3" in assigned_modules else (1, 2)
        pair = prepare_pairs(settings, seed, coordinates, refinements=refinements)
        pair["cpu_seconds"] = process_time() - before_cpu
        data["response_preparation"] = pair
        if not settings["receiver_study"]["M1"]["structural_service"]:
            case, = data["cases"]
            case["instrument_status"] = pair["instrument"]["status"]
            case["coordinates"] = {
                name: {"status": entry["status"], "reason": entry["reason"]}
                for name, entry in pair["coordinates"].items()
            }
            case["status"] = (
                "COMPLETED" if case["instrument_status"] == "COMPLETED"
                and all(entry["status"] == "COMPLETED" for entry in case["coordinates"].values())
                else "UNAVAILABLE"
            )
        for key in WORK:
            data["work_accounting"][key] += pair["work_accounting"][key]
        data["work_accounting"]["counts_are_lower_bounds"] |= pair["work_accounting"][
            "counts_are_lower_bounds"
        ]
    _check_cases(settings, module, data["cases"])
    work = data["work_accounting"]
    if (
        any(type(work.get(key)) is not int or work[key] < 0 for key in WORK)
        or type(work.get("counts_are_lower_bounds")) is not bool
    ):
        raise ValueError(
            f"{module} must account for native work and incomplete attempts"
        )
    elapsed = perf_counter() - start
    return {
        **data,
        "schema": "matrix-model-free-acquisition.v1",
        "receiver_revision": REVISION,
        "settings_sha256": settings_fingerprint(settings),
        "seed": seed,
        "module": module,
        "assigned_case_count": len(data["cases"]),
        "independent_units": 1,
        "status": "COMPLETED"
        if all(case["status"] == "COMPLETED" for case in data["cases"])
        else "PARTIAL",
        "acquisition_seconds": elapsed,
        "evidence_scope": settings["evidence_scope"],
        "work_accounting": {
            **work,
            "wall_seconds": elapsed,
            "scope": "THIS_OPERATION_ONLY_SHARED_INPUTS_CHARGED_TO_PRODUCER",
        },
    }


def analyse(settings, payload, acquisition_settings, changed, retained):
    from .science import settings_fingerprint

    module = payload["module"]
    if payload.get("receiver_revision") == REVISION:
        _check_cases(acquisition_settings, module, payload["cases"])
    elif (
        retained
        and module == "M2"
        and "receiver_revision" not in payload
        and "receiver_study" not in acquisition_settings
    ):
        from .science import _validate_acquisition_census

        _validate_acquisition_census(acquisition_settings, payload)
        cases = [
            {**case, "case_id": case["coordinate"]["id"]} for case in payload["cases"]
        ]
        _check_cases(settings, module, cases)
        payload = {**payload, "cases": cases}
    else:
        raise ValueError(
            "Receiver-study analysis requires its original acquisition revision"
        )
    data = owner(module).analyse(settings, module, payload)
    _check_cases(settings, module, data["cases"])
    return {
        **data,
        "schema": "matrix-model-free-analysis.v1",
        "receiver_revision": REVISION,
        "module": module,
        "seed": payload["seed"],
        "settings_sha256": settings_fingerprint(settings),
        "retained_acquisition_settings_sha256": payload["settings_sha256"],
        "analysis_settings_changed": changed,
        "assessment_exposure": "EXPOSED_REANALYSIS" if retained else "AS_AUTHORED",
        "assigned_case_count": len(data["cases"]),
        "status": payload["status"],
        "independent_units": 1,
        "evidence_scope": settings["evidence_scope"],
        "acquisition_seconds": payload["acquisition_seconds"],
        "work_accounting": payload["work_accounting"],
        "native_work_provenance": "ORIGINAL_RETAINED_ACQUISITION"
        if retained
        else "CURRENT_ACQUISITION",
    }


def synthesise(settings, module, roots, alpha):
    for root in roots:
        if root.get("receiver_revision") != REVISION:
            raise ValueError("Receiver-study synthesis mixes scientific revisions")
        _check_cases(settings, module, root["cases"])
    return {
        "receiver_revision": REVISION,
        **owner(module).synthesise(settings, module, roots, alpha),
    }
