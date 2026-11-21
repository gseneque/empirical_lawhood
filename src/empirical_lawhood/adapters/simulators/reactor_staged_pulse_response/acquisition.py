"""Native acquisition, external-format translation and custody integration."""

from typing import Callable
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import ADDED, BASE, EXPANDED, FIRST, SECONDS, ZERO, ClassicalStage, assignment
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalAssay, ClassicalContext, ClassicalNativeWindow, ClassicalPreparation, ClassicalPrivate
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierAssay
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import ExplorationController, NativeEpisode, TapeController
from empirical_lawhood.adapters.simulators.reactor_causal_response.acquisition import acquire_episode, acquire_with_progress
from empirical_lawhood.domains.reactor.reactor_causal_response.design import draw_scenario
from empirical_lawhood.domains.reactor.reactor_regime_response.prepared_tape import WatchedPreparedTape
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorBatchSource
from empirical_lawhood.domains.reactor.reactor_prefix_response.finite_words import overlay_feed_tape
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_config import ClassicalNativeConfig
from empirical_lawhood.adapters.simulators.reactor_staged_pulse_response.causal_capture import CausalTapeOwner

from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_measurements import (
    causal_context as _science_causal_context,
    donors as _science_donors,
    native_window as _science_native_window,
    pack_preparation as _science_pack_preparation,
    retained_zero_windows as _science_retained_zero_windows,
)

def acquire_preparation(
    config: ClassicalNativeConfig,
    source: ReactorBatchSource,
    block: str,
    root: str,
    *,
    released: bool,
    acquire: Callable[..., NativeEpisode] = acquire_episode,
    progress: Callable[[int], None] | None = None,
) -> tuple[ClassicalPreparation, ClassicalPrivate]:
    assigned_block, role, seed = assignment(root)
    if (
        assigned_block != block
        or role not in ("qualification", "prospective")
        or source.fingerprint() != config.source_sha256
    ):
        raise ValueError("fresh acquisition changes its assigned block, root or source")
    if not released:
        return _science_pack_preparation(
            config, block, root, (), native_calls=0, reasons=("PREREQUISITE_NONENTRY",)
        )
    scenario = draw_scenario(root, "heldout", seed)
    nominal, completed = acquire_with_progress(
        source, scenario, "exploration-unshifted", ExplorationController(0, 0), 1.0, acquire, 0, progress
    )
    episodes = [nominal]
    if nominal.complete:
        refined, _ = acquire_with_progress(
            source,
            scenario,
            "exploration-unshifted",
            TapeController(nominal.requests),
            0.5,
            acquire,
            completed,
            progress,
        )
        episodes.append(refined)
    reasons = tuple(f"VIEW_{i}_INCOMPLETE" for i, e in enumerate(episodes) if not e.complete)
    return _science_pack_preparation(
        config, block, root, tuple(episodes), native_calls=len(episodes), reasons=reasons
    )

def acquire_assay(
    source: ReactorBatchSource,
    stage: ClassicalStage,
    preparation: ClassicalPreparation,
    private: ClassicalPrivate,
    seal: ObjectIdentity,
    *,
    old_assay: FrontierAssay | None = None,
    on_induced: Callable[[ClassicalContext], ObjectIdentity] | None = None,
    acquire: Callable[..., NativeEpisode] = acquire_episode,
    progress: Callable[[int], None] | None = None,
) -> ClassicalAssay:
    if source.fingerprint() != preparation.source_sha256:
        raise ValueError("assay changed its exact native source")
    parent = ObjectIdentity.from_record(preparation.record_id, preparation)
    original = _science_donors(preparation, private)
    windows: list[ClassicalNativeWindow] = []
    induced: list[ClassicalContext] = []
    reasons: list[str] = []
    induced_seal = None
    if stage.block == "staged-sequence-comparison" and on_induced is None:
        raise ValueError(
            "conditional assay requires its declared pre-response publisher before contact"
        )
    calls = completed = 0
    if stage.stage == "expanded-menu-comparison-NOMINATION":
        if old_assay is None:
            raise ValueError(
                "new-word development requires its retained exact zero-reference receipt"
            )
        windows.extend(_science_retained_zero_windows(old_assay, preparation))
    for context in preparation.contexts:
        k = context.callback
        if k is None or context.reasons:
            reasons.append(f"{context.context}.NO_CAUSAL_CONTACT")
            continue
        if len(original) != 2 or not all(e.complete for e in original):
            raise ValueError("assay contact lacks complete nominal/refined preparation")
        jacket = float(original[0].stages[k - 1, 3])
        if stage.block == "staged-sequence-comparison":
            branches = [
                ("00", ZERO.rates(240)),
                ("a0", FIRST.rates() + ZERO.rates()),
                *((f"aw.{w.word_id}", FIRST.rates() + w.rates()) for w in SECONDS),
            ]
        else:
            words = (
                ADDED
                if stage.stage == "expanded-menu-comparison-NOMINATION"
                else (ZERO, *(BASE if stage.block == "base-menu-comparison" else EXPANDED))
            )
            branches = [(f"{context.context}.{w.word_id}", w.rates()) for w in words]
        for name, rates in branches:
            tape = overlay_feed_tape(original[0].requests, k, rates, jacket)
            for view, donor in enumerate(original):
                owner = (
                    CausalTapeOwner(preparation.root, k, on_induced)
                    if name == "a0" and view == 0 and on_induced is not None
                    else None
                )

                def acquire_branch(*args: object, **kwargs: object) -> NativeEpisode:
                    return (
                        acquire(*args, **kwargs, owner=owner)
                        if owner is not None
                        else acquire(*args, **kwargs)
                    )

                controller = (
                    WatchedPreparedTape(tape) if owner is not None else TapeController(tape)
                )
                branch, completed = acquire_with_progress(
                    source,
                    private.scenario,
                    name.replace(".", "-"),
                    controller,
                    0.5 if view else 1.0,
                    acquire_branch,
                    completed,
                    progress,
                )
                calls += 1
                windows.append(_science_native_window(donor, branch, k, rates, tape, name))
                if owner is not None and owner.context is not None:
                    induced.append(owner.context)
                    induced_seal = owner.published
                if stage.block == "staged-sequence-comparison" and name.startswith("aw.") and view == 0 and branch.complete:
                    actual = _science_causal_context(
                        preparation.root, "induced", k + 12, branch, first_callback=k
                    )
                    if induced and actual != induced[0]:
                        raise ValueError(
                            "second-word assay substituted its common actual first-induced prefix"
                        )
                    if not induced:
                        reasons.append("MISSING_PRE_SECOND_RESPONSE_SEAL")
    return ClassicalAssay(
        preparation.root,
        parent,
        seal,
        tuple(windows),
        tuple(induced),
        calls,
        tuple(sorted(set(reasons))),
        induced_seal,
    )
