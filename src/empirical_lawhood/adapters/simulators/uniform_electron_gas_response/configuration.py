"""External path selection and strict electron-gas configuration loading.

Scientific value objects remain in the electron-gas domain.
SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations
from empirical_lawhood._required_inputs import required_external_path
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Final, Mapping, Sequence
from empirical_lawhood.science.records.serialization import validate_decimal, validate_sha256, validate_stable_id

from empirical_lawhood.domains.materials.electron_gas.contracts import PLAN_ID, CAMPAIGN_ID, CONFIG_SCHEMA, CONFIG_VERSION, EXTERNAL_ROOT, MAXIMUM_CONFIG_BYTES, MAXIMUM_PANEL_BYTES, EvidenceLane, TruthCase, UniformElectronGasTransverseScreenConfig


_REFERENCE_GAPS: Final = (
    "gap.algebra.falsifier-preservation",
    "gap.algebra.homogeneity",
    "gap.algebra.signed-opposition",
    "gap.calculus.dose-scaling",
    "gap.calculus.finite-difference-generator-convergence",
    "gap.calculus.numerical-view-convergence",
    "gap.calculus.odd-even-susceptibility",
    "gap.calculus.remainder-regularity",
    "gap.calculus.uncertainty-propagation",
    "gap.dynamics.causal-cones-clock-transport",
    "gap.dynamics.preservation-barriers",
    "gap.geometry.admission-margins",
    "gap.geometry.reachability-viability",
    "gap.geometry.support-charts-atlas",
    "gap.geometry.symmetry-gauge",
    "gap.geometry.tangent-rank",
)


_OUT_OF_SCOPE_GAPS: Final = (
    "gap.algebra.associativity-defect",
    "gap.algebra.cross-context-recurrence",
    "gap.algebra.identity-inverse-repetition",
    "gap.algebra.order-commutator",
    "gap.algebra.quotient-lumpability",
    "gap.algebra.restriction-gluing-transport",
    "gap.algebra.semigroup-embedding",
    "gap.algebra.sequential-composition",
    "gap.algebra.simultaneous-composition",
    "gap.calculus.curvature-hessian",
    "gap.calculus.local-jacobian-rank",
    "gap.calculus.mixed-port-volterra",
    "gap.calculus.nonsmooth-directional-derivative",
    "gap.calculus.time-scaling",
    "gap.dynamics.controllability-observability",
    "gap.dynamics.delay-relaxation",
    "gap.dynamics.gramians",
    "gap.dynamics.hysteresis-return",
    "gap.dynamics.koopman-operator",
    "gap.dynamics.local-evolution-operator",
    "gap.dynamics.nonnormal-amplification",
    "gap.dynamics.recurrence-stationarity",
    "gap.dynamics.sparse-evolution",
    "gap.dynamics.stability-transient",
    "gap.dynamics.state-closure-memory",
    "gap.geometry.boundary-strata",
    "gap.geometry.cohomology",
    "gap.geometry.decision-quotients",
    "gap.geometry.information-geometry",
    "gap.geometry.metric-structure",
    "gap.geometry.receiver-fibers",
    "gap.geometry.topology-restriction",
)


def _decimal(value: object, *, field_name: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a decimal string")
    result = Decimal(value)
    validate_decimal(result, field_name=field_name)
    return result


def _integer(value: object, *, field_name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field_name} must be an integer >= {minimum}")
    return value


def _mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{field_name} must be an object with string keys")
    return value


def _require_keys(value: Mapping[str, object], expected: Sequence[str], *, field_name: str) -> None:
    expected_set = set(expected)
    if set(value) != expected_set:
        missing = sorted(expected_set - set(value))
        unknown = sorted(set(value) - expected_set)
        raise ValueError(f"{field_name} fields differ: missing={missing}, unknown={unknown}")


def _string_tuple(value: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a string list")
    return tuple(value)


def _decimal_tuple(value: object, *, field_name: str) -> tuple[Decimal, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a decimal-string list")
    return tuple(
        _decimal(item, field_name=f"{field_name}[{index}]") for index, item in enumerate(value)
    )


def _reject_binary_floats(value: object, *, field_name: str = "config") -> None:
    if isinstance(value, float):
        raise ValueError(f"{field_name} contains a binary float")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_binary_floats(item, field_name=f"{field_name}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_binary_floats(item, field_name=f"{field_name}[{index}]")


def decode_config(document: Mapping[str, object], *, payload_sha256: str) -> UniformElectronGasTransverseScreenConfig:
    """Decode only the exact closed transverse-screen config schema."""

    validate_sha256(payload_sha256, field_name="payload_sha256")
    _reject_binary_floats(document)
    _require_keys(
        document,
        (
            "action",
            "authority",
            "denominator",
            "formal_gap_dispositions",
            "geometry",
            "identity",
            "lifecycle",
            "receiver",
            "resources",
            "source_dispositions",
            "storage",
            "tasks",
            "thresholds",
            "truth_known",
        ),
        field_name="config",
    )
    identity = _mapping(document["identity"], field_name="identity")
    _require_keys(identity, ("campaign_id", "plan_id", "schema", "version"), field_name="identity")
    if identity != {
        "campaign_id": CAMPAIGN_ID,
        "plan_id": PLAN_ID,
        "schema": CONFIG_SCHEMA,
        "version": CONFIG_VERSION,
    }:
        raise ValueError("uniform electron gas config identity differs from frozen transverse-screen configuration")

    lifecycle = _mapping(document["lifecycle"], field_name="lifecycle")
    _require_keys(lifecycle, ("freeze_id", "frozen_at_utc", "state"), field_name="lifecycle")
    if lifecycle["state"] != "FROZEN":
        raise ValueError("uniform electron gas transverse-screen config must be frozen")
    if not isinstance(lifecycle["freeze_id"], str) or not isinstance(
        lifecycle["frozen_at_utc"], str
    ):
        raise ValueError("freeze identity and time must be strings")
    validate_stable_id(lifecycle["freeze_id"], field_name="freeze_id")

    denominator = _mapping(document["denominator"], field_name="denominator")
    _require_keys(
        denominator,
        (
            "background",
            "dimension",
            "electron_charge_model",
            "electron_mass_model",
            "particle_dispersion",
            "r_s",
            "temperature_K",
        ),
        field_name="denominator",
    )
    if (
        denominator["background"] != "neutralizing-jellium"
        or denominator["dimension"] != 3
        or denominator["particle_dispersion"] != "free-electron-parabolic"
        or denominator["electron_charge_model"] != "CODATA-elementary-charge"
        or denominator["electron_mass_model"] != "CODATA-electron-mass"
    ):
        raise ValueError("physical denominator differs from frozen transverse-screen configuration")
    r_s = _decimal(denominator["r_s"], field_name="r_s")
    temperature = _decimal(denominator["temperature_K"], field_name="temperature_K")
    if r_s != Decimal("4") or temperature != Decimal("300"):
        raise ValueError("r_s or temperature differs from frozen transverse-screen configuration")

    action = _mapping(document["action"], field_name="action")
    _require_keys(
        action,
        (
            "accepted_clock",
            "applied_clock",
            "coordinate",
            "direction",
            "field_ceiling_T",
            "q_direction",
            "q_over_kf",
            "receiver_clock",
            "requested_clock",
            "u0",
            "u_values",
        ),
        field_name="action",
    )
    if action["coordinate"] != "u=e*v_F*A_T/E_F":
        raise ValueError("action coordinate differs from frozen transverse-screen configuration")
    u0 = _decimal(action["u0"], field_name="action.u0")
    u_values = _decimal_tuple(action["u_values"], field_name="action.u_values")
    q_values = _decimal_tuple(action["q_over_kf"], field_name="action.q_over_kf")
    a_direction = _decimal_tuple(action["direction"], field_name="action.direction")
    q_direction = _decimal_tuple(action["q_direction"], field_name="action.q_direction")
    if (
        u0 != Decimal("5e-7")
        or u_values
        != (
            Decimal("-5e-7"),
            Decimal("-2.5e-7"),
            Decimal("0"),
            Decimal("2.5e-7"),
            Decimal("5e-7"),
        )
        or q_values
        != (
            Decimal("0.015625"),
            Decimal("0.03125"),
            Decimal("0.046875"),
            Decimal("0.0625"),
        )
        or a_direction != (Decimal("0"), Decimal("1"), Decimal("0"))
        or q_direction != (Decimal("1"), Decimal("0"), Decimal("0"))
    ):
        raise ValueError("action chart differs from frozen transverse-screen configuration")
    clocks = tuple(
        _integer(action[key], field_name=f"action.{key}")
        for key in ("requested_clock", "accepted_clock", "applied_clock", "receiver_clock")
    )
    if clocks != (0, 1, 2, 3):
        raise ValueError("action/receiver clocks differ from frozen transverse-screen configuration")

    geometry = _mapping(document["geometry"], field_name="geometry")
    _require_keys(
        geometry,
        ("analytic_profile_points", "calibration", "slab_thickness_m"),
        field_name="geometry",
    )
    if geometry["calibration"] != "parallel-field-simply-connected-slab":
        raise ValueError("calibration geometry differs from frozen transverse-screen configuration")
    slab_thickness = _decimal(geometry["slab_thickness_m"], field_name="slab_thickness_m")
    profile_points = _integer(
        geometry["analytic_profile_points"],
        field_name="analytic_profile_points",
        minimum=3,
    )
    if slab_thickness != Decimal("5e-7") or profile_points != 101:
        raise ValueError("slab geometry differs from frozen transverse-screen configuration")

    thresholds_document = _mapping(document["thresholds"], field_name="thresholds")
    threshold_keys = (
        "action_realization_relative",
        "amplitude_locality_relative",
        "baseline_relative",
        "even_remainder_floor_multiplier",
        "even_remainder_response_relative",
        "normal_cancellation_relative",
        "order_preservation_fraction",
        "q_intercept_stability_relative",
        "response_floor_relative_to_diamagnetic",
        "shielding_score_minimum",
        "slab_fit_relative",
        "transverse_dot_relative",
        "view_k0_agreement_relative",
        "ward_residual",
    )
    _require_keys(thresholds_document, threshold_keys, field_name="thresholds")
    thresholds = tuple(
        sorted(
            (key, _decimal(thresholds_document[key], field_name=f"thresholds.{key}"))
            for key in threshold_keys
        )
    )
    expected_thresholds = {
        "action_realization_relative": Decimal("1e-12"),
        "amplitude_locality_relative": Decimal("0.05"),
        "baseline_relative": Decimal("1e-12"),
        "even_remainder_floor_multiplier": Decimal("5"),
        "even_remainder_response_relative": Decimal("0.02"),
        "normal_cancellation_relative": Decimal("1e-3"),
        "order_preservation_fraction": Decimal("0.95"),
        "q_intercept_stability_relative": Decimal("0.10"),
        "response_floor_relative_to_diamagnetic": Decimal("1e-6"),
        "shielding_score_minimum": Decimal("0.50"),
        "slab_fit_relative": Decimal("0.01"),
        "transverse_dot_relative": Decimal("1e-12"),
        "view_k0_agreement_relative": Decimal("0.05"),
        "ward_residual": Decimal("1e-6"),
    }
    if dict(thresholds) != expected_thresholds:
        raise ValueError("threshold family differs from frozen transverse-screen configuration")

    truth = _mapping(document["truth_known"], field_name="truth_known")
    _require_keys(
        truth,
        (
            "cases",
            "deterministic_kernel_relative_error",
            "positive_penetration_depth_m",
            "privileged_oracle_separate",
            "views",
        ),
        field_name="truth_known",
    )
    case_values = _string_tuple(truth["cases"], field_name="truth_known.cases")
    if tuple(sorted(case_values)) != case_values or set(case_values) != {
        value.value for value in TruthCase
    }:
        raise ValueError("truth-known case roster differs from frozen transverse-screen configuration")
    views = _string_tuple(truth["views"], field_name="truth_known.views")
    if views != ("base", "refined") or truth["privileged_oracle_separate"] is not True:
        raise ValueError("truth-known view/oracle contract differs from frozen transverse-screen configuration")

    gaps = _mapping(document["formal_gap_dispositions"], field_name="formal gaps")
    _require_keys(gaps, ("out_of_scope", "reference_conformance_only"), field_name="formal gaps")
    reference_gaps = _string_tuple(
        gaps["reference_conformance_only"], field_name="reference_conformance_only"
    )
    out_gaps = _string_tuple(gaps["out_of_scope"], field_name="out_of_scope")
    if reference_gaps != _REFERENCE_GAPS or out_gaps != _OUT_OF_SCOPE_GAPS:
        raise ValueError("formal-gap dispositions differ from frozen transverse-screen configuration")
    if len(set(reference_gaps) | set(out_gaps)) != 48 or set(reference_gaps) & set(out_gaps):
        raise ValueError("formal-gap dispositions must partition all 48 registered gaps")

    source = _mapping(document["source_dispositions"], field_name="source_dispositions")
    _require_keys(
        source,
        ("paper_rpa", "target_gauge_closed_roster", "vertex_reference"),
        field_name="source_dispositions",
    )
    if source["target_gauge_closed_roster"] != []:
        raise ValueError("transverse-screen target gauge-closed roster must be empty")
    for key, source_identity in (
        ("paper_rpa", "arxiv:2511.00625v3"),
        ("vertex_reference", "arxiv:2512.19382v2"),
    ):
        value = _mapping(source[key], field_name=f"source_dispositions.{key}")
        _require_keys(value, ("identity", "lane", "status"), field_name=key)
        if value != {
            "identity": source_identity,
            "lane": EvidenceLane.TC_CLOSURE_DIAGNOSTIC.value,
            "status": "CLOSURE_ONLY_SOURCE",
        }:
            raise ValueError(f"{key} source disposition differs from transverse receiver screen source assessment")

    tasks = _mapping(document["tasks"], field_name="tasks")
    _require_keys(tasks, ("conformance-truth-known", "development-law-commitment", "evaluation-target-reveal", "qualification-target-source", "supplementary-closure-diagnostic", "terminal-closeout"), field_name="tasks")
    if tasks != {
        "conformance-truth-known": "ENTERED_TRUTH_KNOWN_CONFORMANCE",
        "development-law-commitment": "NOT_ATTEMPTED_PREREQUISITE_TARGET_SOURCE",
        "evaluation-target-reveal": "NOT_ATTEMPTED_PREREQUISITE_TARGET_SOURCE",
        "qualification-target-source": "NOT_ATTEMPTED_PREREQUISITE_TARGET_SOURCE",
        "supplementary-closure-diagnostic": "NOT_ATTEMPTED_PREREQUISITE_EXACT_CLOSURE_BINDING",
        "terminal-closeout": "ENTER_AFTER_TRUTH_KNOWN_CONFORMANCE",
    }:
        raise ValueError("task entry/nonattempt contract differs from frozen transverse-screen configuration")

    receiver = _mapping(document["receiver"], field_name="receiver")
    _require_keys(
        receiver,
        (
            "current_direction",
            "current_unit",
            "kernel_unit",
            "limit_order",
            "penetration_depth_unit",
            "projection",
            "static_frequency_rad_s",
        ),
        field_name="receiver",
    )
    if (
        receiver["current_direction"] != ["0", "1", "0"]
        or receiver["current_unit"] != "A/m^2"
        or receiver["kernel_unit"] != "A/(T*m^3)"
        or receiver["penetration_depth_unit"] != "m"
        or receiver["projection"] != "dot(J_T,A_hat)"
        or receiver["static_frequency_rad_s"] != "0"
        or receiver["limit_order"] != "omega=0-after-source-convergence;finite-q-fit-then-q-to-zero"
    ):
        raise ValueError("receiver contract differs from frozen transverse-screen configuration")

    storage = _mapping(document["storage"], field_name="storage")
    _require_keys(
        storage,
        ("external_root", "minimum_free_bytes", "storage_root"),
        field_name="storage",
    )
    if storage["external_root"] != EXTERNAL_ROOT or storage["storage_root"] != (
        str(required_external_path("EMPIRICAL_LAWHOOD_ELECTRON_GAS_EXTERNAL_ROOT"))
    ):
        raise ValueError("storage route differs from frozen transverse-screen configuration")

    resources_document = _mapping(document["resources"], field_name="resources")
    resource_keys = (
        "cpu_cores",
        "gpu_devices",
        "maximum_all_inputs_bytes",
        "maximum_one_panel_bytes",
        "memory_bytes",
        "network_required",
        "output_bytes",
        "scratch_bytes",
        "wall_time_seconds",
    )
    _require_keys(resources_document, resource_keys, field_name="resources")
    resources: list[tuple[str, int | bool]] = []
    for key in resource_keys:
        resource_value = resources_document[key]
        if key == "network_required":
            if not isinstance(resource_value, bool):
                raise ValueError("network_required must be boolean")
        else:
            resource_value = _integer(resource_value, field_name=f"resources.{key}")
        resources.append((key, resource_value))
    expected_resources: dict[str, int | bool] = {
        "cpu_cores": 2,
        "gpu_devices": 0,
        "maximum_all_inputs_bytes": 32 * 1024**2,
        "maximum_one_panel_bytes": MAXIMUM_PANEL_BYTES,
        "memory_bytes": 2 * 1024**3,
        "network_required": False,
        "output_bytes": 64 * 1024**2,
        "scratch_bytes": 256 * 1024**2,
        "wall_time_seconds": 600,
    }
    if dict(resources) != expected_resources:
        raise ValueError("resource envelope differs from frozen transverse-screen configuration")

    authority = _mapping(document["authority"], field_name="authority")
    _require_keys(
        authority,
        (
            "accountable_owner",
            "authorization_basis",
            "external_scientific_write",
            "implementation",
            "public_web_source_screen",
            "reveal",
            "source_acquisition",
            "truth_known_execution",
        ),
        field_name="authority",
    )
    if (
        authority["accountable_owner"] != "project-owner"
        or authority["implementation"] != "OWNER_AUTHORIZED"
        or authority["truth_known_execution"] != "OWNER_AUTHORIZED"
        or authority["external_scientific_write"] != "OWNER_AUTHORIZED"
        or authority["source_acquisition"] != "NOT_ENTERED"
        or authority["reveal"] != "OWNER_AUTHORIZED_SEPARATE_EVALUATOR_ACT"
        or not isinstance(authority["authorization_basis"], str)
    ):
        raise ValueError("authority scope differs from frozen transverse-screen configuration")

    return UniformElectronGasTransverseScreenConfig(
        payload_sha256=payload_sha256,
        campaign_id=CAMPAIGN_ID,
        freeze_id=lifecycle["freeze_id"],
        frozen_at_utc=lifecycle["frozen_at_utc"],
        r_s=r_s,
        temperature_K=temperature,
        u0=u0,
        u_values=u_values,
        q_over_kf=q_values,
        action_direction=(a_direction[0], a_direction[1], a_direction[2]),
        q_direction=(q_direction[0], q_direction[1], q_direction[2]),
        requested_clock=clocks[0],
        accepted_clock=clocks[1],
        applied_clock=clocks[2],
        receiver_clock=clocks[3],
        field_ceiling_T=_decimal(action["field_ceiling_T"], field_name="field_ceiling_T"),
        slab_thickness_m=slab_thickness,
        analytic_profile_points=profile_points,
        thresholds=thresholds,
        truth_cases=tuple(TruthCase(value) for value in case_values),
        views=views,
        positive_penetration_depth_m=_decimal(
            truth["positive_penetration_depth_m"],
            field_name="positive_penetration_depth_m",
        ),
        deterministic_kernel_relative_error=_decimal(
            truth["deterministic_kernel_relative_error"],
            field_name="deterministic_kernel_relative_error",
        ),
        storage_root=storage["storage_root"],
        external_root=EXTERNAL_ROOT,
        minimum_free_bytes=_integer(
            storage["minimum_free_bytes"], field_name="minimum_free_bytes", minimum=1
        ),
        resources=tuple(sorted(resources)),
        reference_conformance_gaps=reference_gaps,
        out_of_scope_gaps=out_gaps,
    )


def decode_config_bytes(payload: bytes) -> UniformElectronGasTransverseScreenConfig:
    if not isinstance(payload, bytes) or len(payload) > MAXIMUM_CONFIG_BYTES:
        raise ValueError("uniform electron gas config bytes are absent or oversized")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("uniform electron gas config is not strict JSON") from error
    if not isinstance(document, dict):
        raise ValueError("uniform electron gas config root must be an object")
    return decode_config(document, payload_sha256=sha256(payload).hexdigest())


def load_config(path: Path) -> tuple[UniformElectronGasTransverseScreenConfig, bytes]:
    payload = path.read_bytes()
    return decode_config_bytes(payload), payload

