"""Native acquisition, external-format translation and custody integration."""

from typing import Callable
import numpy as np
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.config import WORDS, assignment
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierAssay, FrontierPreparation, FrontierPrivate
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalArrayPayload
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import ExplorationController, NativeEpisode, TapeController
from empirical_lawhood.adapters.simulators.reactor_causal_response.acquisition import acquire_episode
from empirical_lawhood.domains.reactor.reactor_causal_response.design import draw_scenario
from empirical_lawhood.adapters.simulators.reactor_causal_response.acquisition import acquire_with_progress
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorBatchSource
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_config import FrontierNativeConfig
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.words import pulse_tape

from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_measurements import (
    donor_episodes as _science_donor_episodes,
    native_window as _science_native_window,
    pack_preparation as _science_pack_preparation,
    scenario_for as _science_scenario_for,
)

def acquire_preparation(
    config: FrontierNativeConfig,
    source: ReactorBatchSource,
    root: str,
    *,
    released: bool,
    acquire: Callable[..., NativeEpisode] = acquire_episode,
    progress: Callable[[int], None] | None = None,
) -> tuple[FrontierPreparation, FrontierPrivate]:
    role, seed = assignment(root)
    if role == "development" or source.fingerprint() != config.source_sha256:
        raise ValueError("fresh preparation cannot reacquire a retained root or change source")
    if not released:
        return _science_pack_preparation(
            config, root, (), native_calls=0, reasons=("LOCAL_LAW_PREREQUISITE_NONENTRY",)
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
    reasons = tuple(f"VIEW_{view}_INCOMPLETE" for view, e in enumerate(episodes) if not e.complete)
    return _science_pack_preparation(
        config, root, tuple(episodes), native_calls=len(episodes), reasons=reasons
    )

def acquire_assay(
    source: ReactorBatchSource,
    preparation: FrontierPreparation,
    private: FrontierPrivate,
    seal: ObjectIdentity,
    *,
    acquire: Callable[..., NativeEpisode] = acquire_episode,
    progress: Callable[[int], None] | None = None,
) -> FrontierAssay:
    if (
        source.fingerprint() != preparation.source_sha256
        or seal.object_schema != 'empirical-lawhood/methods/reactor-finite-control-frontier/frontier-prediction-seal'
    ):
        raise ValueError("assay lacks its source/prediction barrier")
    donors = _science_donor_episodes(preparation, private)
    data, failures = {}, []
    calls = completed = 0
    scenario = _science_scenario_for(preparation.root)
    for context in preparation.contexts:
        callback = context.callback
        if callback is None or context.reasons:
            failures.append((context.context, "NO_VALID_CAUSAL_CONTACT"))
            continue
        if len(donors) != 2 or not all(e.complete for e in donors):
            raise ValueError("contacted context lacks its complete paired preparation")
        jacket = float(donors[0].stages[callback - 1, 3])
        for view, donor in enumerate(donors):
            data[f"{context.context}_v{view}_anchor"] = np.asarray(
                (*donor.observations[callback], *donor.stages[callback - 1, 2:])
            )
            data[f"{context.context}_v{view}_prefix_peak"] = np.asarray(
                [donor.grid[: int(callback * 10 / donor.dt) + 1, 1].max()]
            )
        for pulse in WORDS:
            tape = pulse_tape(donors[0].requests, callback, pulse, jacket)
            for view, donor in enumerate(donors):
                key = f"{context.context}_{pulse.word_id}_v{view}"
                branch, completed = acquire_with_progress(
                    source,
                    scenario,
                    key,
                    TapeController(tape),
                    donor.dt,
                    acquire,
                    completed,
                    progress,
                )
                calls += 1
                if not branch.complete:
                    failures.append((key, branch.failure or "INCOMPLETE_NATIVE_ASSAY"))
                    continue
                data.update(
                    {
                        f"{key}_{field}": array
                        for field, array in _science_native_window(donor, branch, callback, tape).items()
                    }
                )
    return FrontierAssay(
        preparation.root,
        ObjectIdentity.from_record(preparation.record_id, preparation),
        seal,
        LocalArrayPayload.pack(data),
        calls,
        tuple(failures),
    )
