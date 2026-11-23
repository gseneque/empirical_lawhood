# SPDX-License-Identifier: MPL-2.0
"""Native numerical replication of an already measured constructed-preparation root."""

from empirical_lawhood.domains.matrix.constructed_preparation_applicability.phase_records import (
    ConstructedPreparationPanel,
    ConstructedPreparationParents,
)
from empirical_lawhood.domains.matrix.preparation_applicability.dynamics import acquire_phase, acquire_prefix
from empirical_lawhood.domains.matrix.prepared_response.instruments import PreparedPortFrame
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _decode


def verify_measured_native_panel(allocation, source_sha256, selection, seal, measured):
    root_id = allocation.root_id
    if (
        root_id != selection.root_id
        or root_id != measured.root_id
        or root_id != seal.root_id
        or not measured.complete
        or not seal.complete
        or selection.selected_index != 1
    ):
        raise ValueError("Select a complete, exposed root with its original nomination and lower seal")
    prefix = acquire_prefix(allocation, source_sha256, constructed=True)
    if prefix.fingerprint() != measured.prefix_sha256 or selection.prefix_sha256 != measured.prefix_sha256:
        raise ValueError("New native prefix differs from the published prefix")
    frame = PreparedPortFrame(4096, _decode(prefix.frame_base64, (2, 3, 4, 4)))
    common = dict(constructed=True, allocation=allocation, source_sha256=source_sha256, frame=frame)
    parents = tuple(
        acquire_phase(
            **common,
            phase_name="parent",
            refinement=view,
            incoming=prefix.phases[view - 1],
            schedule_index=arm,
        )
        for arm in range(3)
        for view in (1, 2)
    )
    selected_sha = selection.fingerprint()
    if (
        ConstructedPreparationParents(root_id, measured.prefix_sha256, selected_sha, parents).fingerprint()
        != seal.parents_sha256
    ):
        raise ValueError("The native parent entering the sealed decision changed")
    futures = tuple(
        acquire_phase(
            **common,
            phase_name="future",
            refinement=p.refinement,
            incoming=p,
            schedule_index=p.schedule_index,
            future_index=f,
            word_index=w,
        )
        for p in parents
        for f in (0, 1)
        for w in range(9)
    )
    panel = ConstructedPreparationPanel(
        root_id, measured.prefix_sha256, selected_sha, parents + futures, seal.fingerprint()
    )
    if panel.fingerprint() != measured.panel_sha256:
        raise ValueError("The new matched native assay differs from the original")
    phases = (*prefix.phases, *panel.phases)
    return {
        "root": root_id,
        "panel_sha256": panel.fingerprint(),
        "native_phase_views": len(phases),
        "native_intervals": sum(p.completed_intervals for p in phases),
    }
