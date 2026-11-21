"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from hashlib import sha256
import numpy as np
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.config import CONTEXTS, GUARD, FrontierDesign, assignment
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import CAUSAL_FIELDS, NATIVE_FIELDS, FrontierContext, FrontierPreparation, FrontierPrivate
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalArrayPayload
from empirical_lawhood.domains.reactor.reactor_regime_response.causal_preparation import causal_delivery_prefix
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.domains.reactor.reactor_causal_response.design import draw_scenario
from empirical_lawhood.domains.reactor.reactor_regime_response.panel import select_anchors
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorAssignedScenario
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_config import FrontierNativeConfig

def pack_preparation(
    config: FrontierNativeConfig,
    root: str,
    episodes: tuple[NativeEpisode, ...],
    *,
    native_calls: int,
    retained_parents: tuple[ObjectIdentity, ...] = (),
    reasons: tuple[str, ...] = (),
) -> tuple[FrontierPreparation, FrontierPrivate]:
    """Cut each policy input independently; complete tapes/grids stay private."""
    anchors = (
        {a.name: a for a in select_anchors(episodes[0], config.prepared_domain)}
        if len(episodes) == 2 and all(e.complete for e in episodes)
        else {}
    )
    contexts = []
    for name in CONTEXTS:
        anchor = anchors.get(name)
        callback = None if anchor is None else anchor.callback
        ca = {}
        failures = list(reasons)
        if callback is not None:
            nominal = episodes[0]
            if not causal_delivery_prefix(
                nominal.observations,
                nominal.requests,
                nominal.stages,
                nominal.exposure,
                callback,
                1.0,
            ):
                failures.append("INVALID_CAUSAL_DELIVERY_PREFIX")
            for field in CAUSAL_FIELDS:
                ca[field] = getattr(nominal, field)[
                    : callback + int(field == "observations")
                ].copy()
        else:
            failures.append("NO_CAUSAL_CONTACT")
        contexts.append(
            FrontierContext(
                root, name, callback, LocalArrayPayload.pack(ca), tuple(sorted(set(failures)))
            )
        )
    data = {}
    for view, episode in enumerate(episodes):
        if episode.root != root or episode.dt != (1.0 if view == 0 else 0.5):
            raise ValueError("preparation changed its physical root or numerical view")
        data.update({f"v{view}_{field}": getattr(episode, field) for field in NATIVE_FIELDS})
    design = FrontierDesign()
    preparation = FrontierPreparation(
        root,
        ObjectIdentity.from_record(design.config_id, design),
        config.source_sha256,
        tuple(contexts),
        native_calls,
        retained_parents,
        reasons,
    )
    private = FrontierPrivate(
        root,
        ObjectIdentity.from_record(preparation.record_id, preparation),
        LocalArrayPayload.pack(data),
        tuple(e.failure for e in episodes),
    )
    return preparation, private

def donor_episodes(
    preparation: FrontierPreparation, private: FrontierPrivate
) -> tuple[NativeEpisode, ...]:
    if private.root != preparation.root or private.preparation != ObjectIdentity.from_record(
        preparation.record_id, preparation
    ):
        raise ValueError("private preparation changed its exact causal parent")
    arrays = private.arrays.unpack()
    return tuple(
        NativeEpisode(
            preparation.root,
            "exploration-unshifted",
            0.5 if view else 1.0,
            **{field: arrays[f"v{view}_{field}"] for field in NATIVE_FIELDS},
            failure=failure,
        )
        for view, failure in enumerate(private.failures)
    )

def scenario_for(root: str) -> ReactorAssignedScenario:
    role, seed = assignment(root)
    return draw_scenario(root, "calibration" if role == "development" else "heldout", seed)

def native_window(
    donor: NativeEpisode, branch: NativeEpisode, callback: int, tape: np.ndarray
) -> dict[str, np.ndarray]:
    """Retain the complete local native measurement and full-episode digests."""
    if not branch.complete or donor.root != branch.root or donor.dt != branch.dt:
        return {}
    prefix_valid = (
        np.array_equal(branch.observations[: callback + 1], donor.observations[: callback + 1])
        and np.array_equal(branch.requests, tape)
        and np.array_equal(branch.stages[:callback], donor.stages[:callback])
        and np.array_equal(branch.exposure[:callback], donor.exposure[:callback])
    )
    first = int(callback * 10 / branch.dt)
    result = {
        "grid": branch.grid[first : first + int(GUARD / branch.dt) + 1].copy(),
        "valid": np.asarray([prefix_valid], dtype=np.uint8),
    }
    result.update(
        {
            field: getattr(branch, field)[callback : callback + GUARD // 10].copy()
            for field in ("requests", "stages", "exposure")
        }
    )
    for name, array in (
        ("prefix", branch.observations[: callback + 1]),
        ("full_grid", branch.grid),
    ):
        result[f"{name}_sha256"] = np.frombuffer(
            sha256(array.tobytes()).digest(), dtype=np.uint8
        ).copy()
    return result
