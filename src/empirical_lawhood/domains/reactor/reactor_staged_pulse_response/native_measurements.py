"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from decimal import Decimal as D
from hashlib import sha256
import numpy as np
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import CONTEXTS, ZERO, assignment
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import CAUSAL_FIELDS, ClassicalContext, ClassicalNativeWindow, ClassicalPreparation, ClassicalPrivate
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierAssay, FrontierPreparation, FrontierPrivate
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalArrayPayload
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.domains.reactor.reactor_causal_response.design import draw_scenario
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_measurements import donor_episodes as retained_episodes
from empirical_lawhood.domains.reactor.reactor_regime_response.panel import select_anchors
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_config import ClassicalNativeConfig

def causal_context(
    root: str,
    context: str,
    callback: int | None,
    episode: NativeEpisode,
    *,
    reasons: tuple[str, ...] = (),
    first_callback: int | None = None,
    predecessor: ObjectIdentity | None = None,
    owner_scope: str | None = None,
) -> ClassicalContext:
    values = (
        {}
        if callback is None
        else {
            name: getattr(episode, name)[: callback + int(name == "observations")].copy()
            for name in CAUSAL_FIELDS
        }
    )
    return ClassicalContext(
        root,
        context,
        callback,
        LocalArrayPayload.pack(values),
        reasons or (("NO_CAUSAL_CONTACT",) if callback is None else ()),
        first_callback,
        predecessor,
        owner_scope,
    )

def pack_preparation(
    config: ClassicalNativeConfig,
    block: str,
    root: str,
    episodes: tuple[NativeEpisode, ...],
    *,
    native_calls: int,
    retained_parents: tuple[ObjectIdentity, ...] = (),
    reasons: tuple[str, ...] = (),
) -> tuple[ClassicalPreparation, ClassicalPrivate]:
    anchors = (
        {a.name: a for a in select_anchors(episodes[0], config.prepared_domain)}
        if len(episodes) == 2 and all(e.complete for e in episodes)
        else {}
    )
    contexts = []
    for name in ("early",) if block == "staged-sequence-comparison" else CONTEXTS:
        anchor = anchors.get(name)
        callback = None if anchor is None else anchor.callback
        if callback is None:
            contexts.append(
                ClassicalContext(
                    root,
                    name,
                    None,
                    LocalArrayPayload.pack({}),
                    tuple(sorted(set((*reasons, "NO_CAUSAL_CONTACT")))),
                )
            )
        else:
            contexts.append(causal_context(root, name, callback, episodes[0], reasons=reasons))
    preparation = ClassicalPreparation(
        root, block, config.source_sha256, tuple(contexts), native_calls, retained_parents, reasons
    )
    _, role, seed = assignment(root)
    scenario = draw_scenario(root, "calibration" if role == "development" else "heldout", seed)
    private = ClassicalPrivate(
        ObjectIdentity.from_record(preparation.record_id, preparation),
        scenario,
        tuple(e.envelope() for e in episodes),
    )
    return preparation, private

def reuse_preparation(
    config: ClassicalNativeConfig,
    block: str,
    old: FrontierPreparation,
    private: FrontierPrivate,
    *,
    private_identity: ObjectIdentity,
) -> tuple[ClassicalPreparation, ClassicalPrivate]:
    if old.source_sha256 != config.source_sha256 or assignment(old.root)[1] != "development":
        raise ValueError("retained preparation changes source or physical independent unit")
    if (
        private_identity.object_schema != private.SCHEMA
        or private_identity.object_fingerprint != private.fingerprint()
    ):
        raise ValueError("retained private identity lacks its exact issued artifact")
    episodes = retained_episodes(old, private)
    return pack_preparation(
        config,
        block,
        old.root,
        episodes,
        native_calls=0,
        retained_parents=(ObjectIdentity.from_record(old.record_id, old), private_identity),
        reasons=old.reasons,
    )

def donors(
    preparation: ClassicalPreparation, private: ClassicalPrivate
) -> tuple[NativeEpisode, ...]:
    if (
        private.preparation != ObjectIdentity.from_record(preparation.record_id, preparation)
        or private.scenario.unit_id != preparation.root
    ):
        raise ValueError("native consumer changed its causal/private preparation pair")
    return tuple(NativeEpisode.from_envelope(e) for e in private.episodes)

def native_window(
    donor: NativeEpisode,
    branch: NativeEpisode,
    callback: int,
    rates: tuple[D, ...],
    tape: np.ndarray,
    branch_id: str,
) -> ClassicalNativeWindow:
    guard = 10 * len(rates)
    first = int(callback * 10 / branch.dt)
    stop = first + int(guard / branch.dt) + 1
    stop_callback = callback + len(rates)
    values: dict[str, np.ndarray] = {}
    if donor.root != branch.root or donor.dt != branch.dt:
        raise ValueError("local measurement changes its root or numerical view")
    known = (
        len(branch.grid) >= stop
        and len(branch.requests) >= stop_callback
        and len(branch.stages) >= stop_callback
        and len(branch.exposure) >= stop_callback
    )
    if known:
        prefix_valid = (
            np.array_equal(branch.observations[: callback + 1], donor.observations[: callback + 1])
            and np.array_equal(branch.requests[:stop_callback], tape[:stop_callback])
            and np.array_equal(branch.stages[:callback], donor.stages[:callback])
            and np.array_equal(branch.exposure[:callback], donor.exposure[:callback])
        )
        values = {
            "grid": branch.grid[first:stop].copy(),
            "anchor": np.asarray(
                (*branch.observations[callback], *branch.stages[callback - 1, 2:])
            ),
            "prefix_peak": np.asarray([branch.grid[: first + 1, 1].max()]),
            "valid": np.asarray([prefix_valid], dtype=np.uint8),
            "observations": branch.observations[
                callback : min(stop_callback + 1, len(branch.observations))
            ].copy(),
            **{
                name: getattr(branch, name)[callback:stop_callback].copy()
                for name in ("requests", "stages", "exposure")
            },
        }
        for name, array in (
            ("prefix", branch.observations[: callback + 1]),
            ("full_grid", branch.grid),
        ):
            values[f"{name}_sha256"] = np.frombuffer(
                sha256(array.tobytes()).digest(), dtype=np.uint8
            ).copy()
    return ClassicalNativeWindow(
        donor.root,
        branch_id,
        branch.dt == 0.5,
        D(callback * 10),
        guard,
        rates,
        LocalArrayPayload.pack(values),
        branch.failure if known else branch.failure or "INCOMPLETE_NATIVE_WINDOW",
    )

def retained_zero_windows(
    old: FrontierAssay, preparation: ClassicalPreparation
) -> tuple[ClassicalNativeWindow, ...]:
    if old.root != preparation.root:
        raise ValueError("retained zero reference changes its independent root")
    data = old.arrays.unpack()
    windows = []
    for context in preparation.contexts:
        if context.callback is None:
            continue
        for view in (0, 1):
            key = f"{context.context}_{ZERO.word_id}_v{view}"
            names = (
                "grid",
                "requests",
                "stages",
                "exposure",
                "valid",
                "prefix_sha256",
                "full_grid_sha256",
            )
            values = {name: data[f"{key}_{name}"] for name in names if f"{key}_{name}" in data}
            for name in ("anchor", "prefix_peak"):
                if f"{context.context}_v{view}_{name}" in data:
                    values[name] = data[f"{context.context}_v{view}_{name}"]
            windows.append(
                ClassicalNativeWindow(
                    old.root,
                    f"{context.context}.{ZERO.word_id}",
                    bool(view),
                    D(context.callback * 10),
                    120,
                    ZERO.rates(),
                    LocalArrayPayload.pack(values),
                    None if len(values) == 9 else "RETAINED_ZERO_INCOMPLETE",
                )
            )
    return tuple(windows)
