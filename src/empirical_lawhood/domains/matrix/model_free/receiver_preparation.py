# SPDX-License-Identifier: MPL-2.0
"""Causal source64 instruments and paired ORIGINAL/EARLY handoffs on fresh streams."""

from dataclasses import replace
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
import json
import math
from types import MappingProxyType
from time import process_time
import zlib

import numpy as np

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Design
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import receiver_matrix
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import brownian_bridge_split
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import validate_sha256
from . import native

ARMS = ("ORIGINAL", "EARLY")
REFINEMENTS = (1, 2, 4)
ORIGINAL_IDENTITY = {
    "packet_sha256": "332addc38d13dd63a5a7a84d4e77c0ebafd686d2990fc9c30cc138d63470001b",
    "sci02c_study_sha256": "425065a5cfd3386f64aca06dbee109c0dc5e44ae47f29fe87d1194d419f488c2",
    "physical_design_sha256": "3b7251c3bc50adbf49ada774570872153134c4e8f16989d524af7010449f3130",
}


def instrument_operands(selection):
    if type(selection) is not dict:
        raise ValueError("Bind the original assay with model_free_receiver_inputs.py before authoring")
    return _decode_instrument(json.dumps(selection, sort_keys=True, separators=(",", ":"), allow_nan=False))


@lru_cache(maxsize=2)
def _decode_instrument(canonical):
    value = json.loads(canonical)
    if set(value) != {
        "packet_sha256",
        "sci02c_study_sha256",
        "physical_design",
        "physical_design_sha256",
        "template_hex",
        "template_members",
    }:
        raise ValueError("Incomplete original assay selection")
    for key, expected in ORIGINAL_IDENTITY.items():
        validate_sha256(value[key])
        if value[key] != expected:
            raise ValueError(
                "Receiver-study instrument substitutes another original packet, study or physical design"
            )
    raw = value["physical_design"].encode()
    design = decode_canonical_bytes(raw, Sci02Design, maximum_bytes=1024**2)
    if design.fingerprint() != value["physical_design_sha256"] or design.canonical_bytes() != raw:
        raise ValueError("Original physical design digest changed")
    artifact = design.assay.template_artifact
    encoded = bytes.fromhex(value["template_hex"])
    if len(encoded) != artifact.size_bytes or sha256(encoded).hexdigest() != artifact.sha256:
        raise ValueError("Original instrument template bytes changed")
    if set(value["template_members"]) != {m.name for m in design.assay.template_members}:
        raise ValueError("Incomplete original instrument member census")
    arrays = {}
    for member in design.assay.template_members:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(bytes.fromhex(value["template_members"][member.name]), member.size_bytes + 1)
        if (
            len(raw) != member.size_bytes
            or not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
            or sha256(raw).hexdigest() != member.sha256
        ):
            raise ValueError("Decoded instrument member differs from the typed original")
        arrays[member.name] = np.frombuffer(raw, dtype=member.dtype).reshape(member.shape)
    return design, MappingProxyType(arrays)


def _instrument(design, templates, states):
    observed = {}
    for name, state in zip(("primary", "fine"), states, strict=True):
        observed[name + "_positions"] = state.positions[None]
        observed[name + "_momenta"] = state.momenta[None]
        observed[name + "_ticks"] = np.asarray([state.step_index])
        observed[name + "_alpha_tilde"] = np.asarray([[state.alpha_tilde_x, state.alpha_tilde_y]])
    result = sci02_science.fixed_instrument(design, observed, templates)
    if result.disposition != "AVAILABLE":
        return {"status": "UNAVAILABLE", "reason": list(result.reasons)}
    forces = np.column_stack([native.native_position_coordinates(f) for f in result.arrays["forces"]])
    output = receiver_matrix(result.arrays["receivers"])
    roles = [action.role for action in design.assay.actions]
    factor = forces[:, roles.index("FACTOR")]
    weights = output[:, 96:] @ factor
    if np.linalg.norm(output[:, 96:].T @ weights - factor) > 1e-10 or abs(np.linalg.norm(factor) - 1.0) > 1e-10:
        raise ValueError("Signed FACTOR direction is outside the original momentum receiver")
    return {
        "status": "COMPLETED",
        "source_tick": 64,
        "force_roles": roles,
        "forces": forces.tolist(),
        "receivers": output.tolist(),
        "momentum_weights": weights.tolist(),
        "source_factor_admitted": bool(result.arrays["source_factor_admitted"][0]),
    }


def service_origin(c, state):
    """Use the physical time-zero quench for the first prospective Hessian."""
    return replace(state, alpha_tilde_x=float(c["target_x"]), alpha_tilde_y=float(c["target_y"]))


def prepare_pairs(settings, seed, rows, *, refinements=REFINEMENTS):
    """Spend the nominal source prefix once and share its fixed physical ports across destinations."""
    design, templates = instrument_operands(settings["receiver_study"]["instrument"])
    c = settings["native"]
    if refinements not in ((1, 2), REFINEMENTS):
        raise ValueError("The signed assay requires primary/fine views, with an optional quarter-step audit")
    physical = design.coordinate
    nominal = next((row for row in rows if row["id"] == "nominal"), None)
    if (
        nominal is None
        or any(
            Decimal(c[key]) != expected
            for key, expected in (
                ("timestep", physical.primary_view.timestep),
                ("mass", physical.member.mass_x),
                ("mass", physical.member.mass_y),
                ("decreasing_start", physical.decreasing_start),
                ("target_x", physical.target_x),
                ("target_y", physical.target_y),
            )
        )
        or any(
            Decimal(nominal[key]) != expected
            for key, expected in (
                ("temperature", physical.primary_view.bath_temperature),
                ("friction", physical.primary_view.friction_gamma),
                ("cross_coupling", physical.member.cross_coupling_gamma),
            )
        )
        or any(
            action.amplitude != Decimal(c["amplitude"]) or action.pulse_steps != c["pulse_ticks"]
            for action in design.assay.actions
        )
        or (design.source_tick, design.handoff_tick, design.response_horizon, design.refresh_tick)
        != (64, 256, 64, 32)
    ):
        raise ValueError(
            "Receiver study changes a bound nominal physical parameter, pulse or observation clock"
        )
    schedules = {arm: np.asarray(design.recipe(arm).half_tick_couplings, dtype=float) for arm in ARMS}
    work = {
        "native_force_evaluations": 0,
        "native_hessian_actions": 0,
        "native_energy_evaluations": 0,
        "counts_are_lower_bounds": False,
    }
    pairs = {}
    instrument = {"status": "UNAVAILABLE", "reason": "NOMINAL_SOURCE64_UNAVAILABLE"}
    for row in rows:
        started = process_time()
        views_used = (
            refinements if row["id"] in settings["receiver_study"]["M3"]["signed_coordinates"] else (1,)
        )
        coord = native.coordinate(c, row, "joint-decreasing")
        views = {r: replace(coord.primary_view, timestep=coord.primary_view.timestep / r) for r in views_used}
        state = native.initial_parameter_state(coord)
        states = {r: state for r in views_used}
        generators = [native.rng(seed, purpose) for purpose in (501, 502, 503)]
        costs, jumps = [], []

        def caches():
            result = {r: (native.BAOABGradientCache(), native.protocol_work_account()) for r in views_used}
            costs.extend(v[0] for v in result.values())
            jumps.extend(v[1] for v in result.values())
            return result

        def advance(current, arm, tick, innovations, ledger):
            for refinement, noises in zip(views_used, innovations, strict=True):
                for substep, noise in enumerate(noises, 1):
                    half = 2 * tick + 2 * substep / refinement
                    left = int(half)
                    table = schedules[arm]
                    alpha = table[left] if left == half else (table[left] + table[left + 1]) / 2
                    cache, account = ledger[refinement]
                    current[refinement] = native.step(
                        current[refinement],
                        coord,
                        noise,
                        numerical=views[refinement],
                        cache=cache,
                        protocol_work=account,
                        couplings=tuple(alpha),
                    )
                    native.guard(current[refinement], c)

        prefix_cost = caches()
        active = {}
        arm_costs = {}
        failure = None
        try:
            for tick in range(design.handoff_tick):
                coarse = native.hermitian_noise(rng=generators[0], q=2)
                innovations = [(coarse,)]
                if 2 in views_used:
                    halves = native.split_parameter_innovations(
                        coord, coarse, native.hermitian_noise(rng=generators[1], q=2)
                    )
                    innovations.append(halves)
                if 4 in views_used:
                    innovations.append(
                        tuple(
                            value
                            for half in halves
                            for value in brownian_bridge_split(
                                coarse_noise=half,
                                bridge_noise=native.hermitian_noise(rng=generators[2], q=2),
                                half_decay=math.exp(-float(row["friction"]) * float(c["timestep"]) / 4),
                            )
                        )
                    )
                if tick < design.source_tick:
                    advance(states, "ORIGINAL", tick, innovations, prefix_cost)
                    if tick + 1 == design.source_tick:
                        if row["id"] == "nominal":
                            instrument = _instrument(design, templates, [states[1], states[2]])
                        active = {arm: dict(states) for arm in ARMS}
                        arm_costs = {arm: caches() for arm in ARMS}
                else:
                    for arm in ARMS:
                        advance(active[arm], arm, tick, innovations, arm_costs[arm])
        except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
            failure = str(error)
            work["counts_are_lower_bounds"] = True
        pairs[row["id"]] = {
            "coordinate": row,
            "status": "UNAVAILABLE" if failure else "COMPLETED",
            "preparation_cpu_seconds": process_time() - started,
            "reason": failure,
            "origins": {}
            if failure
            else {arm: {str(r): native.checkpoint(active[arm][r]) for r in views_used} for arm in ARMS},
            "signed_work_by_arm_view": {
                arm: {str(r): entry[1].summary(complete=failure is None) for r, entry in ledger.items()}
                for arm, ledger in arm_costs.items()
            },
            "common_prefix_work_by_view": {
                str(r): entry[1].summary(complete=failure is None) for r, entry in prefix_cost.items()
            },
        }
        work["native_force_evaluations"] += sum(cache.completed_evaluations for cache in costs)
        work["native_energy_evaluations"] += sum(account.potential_evaluations_completed for account in jumps)
    return {
        "instrument": instrument,
        "coordinates": pairs,
        "physical_design_sha256": design.fingerprint(),
        "native_clock_convention": "ORIGINAL_REFINEMENT_STEP_INDEX",
        "work_accounting": work,
    }
