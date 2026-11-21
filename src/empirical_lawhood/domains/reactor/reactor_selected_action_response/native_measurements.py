"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from empirical_lawhood.domains.reactor.reactor_selected_action_response.records import ClassicalCausal, ClassicalPrivate
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.science.identity.provenance import ObjectIdentity

FIELDS = ("observations", "requests", "stages", "exposure", "grid", "callback_cpu")

def donor_episode(
    causal: ClassicalCausal, private: ClassicalPrivate, view: int
) -> NativeEpisode:
    if private.causal_preparation != ObjectIdentity.from_record(
        f"{causal.root}.causal-preparation", causal
    ):
        raise ValueError("classical private/causal preparation differs")
    arrays = private.arrays.unpack()
    return NativeEpisode(
        causal.root,
        "exploration-unshifted",
        0.5 if view else 1.0,
        **{field: arrays[f"exploration_unshifted_v{view}_{field}"] for field in FIELDS},
        failure=None,
    )
