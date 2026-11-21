"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from collections.abc import Callable
from hashlib import sha256
import io
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.six_matrix_response.response_development import ResponseGeometryDevelopmentNativeSegmentResult
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _decode
from empirical_lawhood.adapters.simulators.six_matrix_response.response_source import response_hdf5_group, response_hdf5_text, response_hdf5_writer
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import RESPONSE_BUNDLES, NATIVE_SCHEMA, PARENTS, PreparationDelivery, PreparationNativeResult, PreparationRoot, PreparationSourceConfig, preparation_actions

from empirical_lawhood.domains.matrix.matrix_preparation_analysis.preparation_dynamics import (
    NATIVE_MAXIMUM_BYTES as _science_NATIVE_MAXIMUM_BYTES,
    NATIVE_METADATA as _science_NATIVE_METADATA,
    _Branch,
    _advance,
    _handoff_checkpoint,
    _unentered,
    innovation_bundle as _science_innovation_bundle,
)

def execute_preparation_root(
    config: PreparationSourceConfig,
    root: PreparationRoot,
    prefix: ResponseGeometryDevelopmentNativeSegmentResult,
    *,
    progress: Callable[[int], None] | None = None,
) -> tuple[PreparationNativeResult, bytes]:
    """Native realization only; the public runtime must supply authenticated inputs."""
    declaration = next((p for p in config.prefixes if p.root == root), None)
    if declaration is None or (
        prefix.fingerprint() != declaration.artifact.sha256
        or prefix.source_config != declaration.source_config
        or prefix.segment.phase != "prefix"
        or prefix.segment.root.root_id != declaration.source_root_id
        or prefix.segment.end_tick != root.landmark
    ):
        raise ValueError("preparation root is detached from its authenticated exposed stochastic prefix")
    checkpoints = {v.refinement: v.checkpoint for v in prefix.views if v.disposition == "COMPLETE"}
    payload, deliveries, mode_sha256, total = execute_preparation_panel(
        config, root, checkpoints, prefix_sha256=prefix.fingerprint(), progress=progress,
    )
    result = PreparationNativeResult(
        f"result.{root.root_id}.native",
        ObjectIdentity.from_record(config.config_id, config), root,
        ObjectIdentity.from_record(declaration.imported_artifact_id, declaration),
        mode_sha256, deliveries, sha256(payload).hexdigest(), total,
    )
    return result, payload


def execute_preparation_panel(config, root, checkpoints, *, prefix_sha256: str, progress=None):
    """Shared native orchestration after the caller authenticates its prefix.

    Frozen retained and current fresh callers retain distinct canonical records.
    The native step, noise pairing, clocks, force kicks and action census are
    identical. This function grants no authority and touches no filesystem.
    """
    primary = checkpoints.get(1)
    mode = (
        None
        if primary is None or primary.frozen_mode_base64 is None
        else _decode(primary.frozen_mode_base64, (3, 4, 4))
    )
    stream = io.BytesIO()
    deliveries: list[PreparationDelivery] = []
    total = 0
    with response_hdf5_writer(stream) as artifact:
        for key, value in {
            **_science_NATIVE_METADATA,
            "schema": NATIVE_SCHEMA,
            "source_config_sha256": config.fingerprint(),
            "root_sha256": root.fingerprint(),
            "original_prefix_sha256": prefix_sha256,
        }.items():
            response_hdf5_text(artifact, key, value)
        if mode is not None:
            artifact.create_dataset("mode", data=mode, track_times=False)
        # Materialize shared innovations once; every sign/parent reuses these
        # arrays, while the five audit/task purposes have independent streams.
        bundles = (
            {
                purpose: _science_innovation_bundle(
                    config, root, purpose, 144 if purpose == "parent" else 320
                )
                for purpose in ("parent", *RESPONSE_BUNDLES, "prospective-task")
            }
            if mode is not None
            else {}
        )
        for refinement in (1, 2):
            view_group = response_hdf5_group(artifact, f"r{refinement}")
            checkpoint = checkpoints.get(refinement)
            if checkpoint is not None:
                view_group.create_dataset(
                    "imported_checkpoint",
                    data=np.frombuffer(checkpoint.canonical_bytes(), dtype="u1"),
                    track_times=False,
                )
            for parent in PARENTS:
                group = response_hdf5_group(view_group, parent)
                parent_group = response_hdf5_group(group, "parent")
                occurrence = f"{root.root_id}.{parent}.parent.r{refinement}"
                handoff = None
                if checkpoint is None or mode is None:
                    delivered = _unentered(
                        occurrence,
                        refinement,
                        root.landmark,
                        root.handoff,
                        "PREFIX_OR_PRIMARY_MODE_UNRESOLVED",
                    )
                else:
                    branch = _Branch.restore(checkpoint)
                    base = total
                    delivered, arrays, attributes = _advance(
                        branch,
                        root=root,
                        parent=parent,
                        refinement=refinement,
                        mode=mode,
                        innovations=bundles["parent"],
                        action=None,
                        progress=None if progress is None else lambda n: progress(base + n),
                    )

                    for name, value in attributes.items():
                        response_hdf5_text(parent_group, name, value)
                    for name, value in arrays.items():
                        parent_group.create_dataset(name, data=value, track_times=False)
                    del arrays, attributes
                    if delivered.disposition == "COMPLETE":
                        handoff = _handoff_checkpoint(
                            branch, root, parent, refinement, mode, bundles["parent"]
                        )
                        group.create_dataset(
                            "handoff_checkpoint",
                            data=np.frombuffer(handoff.canonical_bytes(), dtype="u1"),
                            track_times=False,
                        )
                deliveries.append(delivered)
                total += delivered.completed_intervals
                for action in (a for a in preparation_actions(root) if a.parent == parent):
                    action_group = response_hdf5_group(
                        group, action.action_id.rsplit(f".{parent}.", 1)[1]
                    )
                    if handoff is None:
                        delivered = _unentered(
                            f"{action.action_id}.r{refinement}",
                            refinement,
                            root.handoff,
                            root.handoff + 320,
                            "PARENT_INCOMPLETE",
                        )
                    else:
                        assert mode is not None
                        base = total
                        delivered, arrays, attributes = _advance(
                            _Branch.restore(handoff),
                            root=root,
                            parent=parent,
                            refinement=refinement,
                            mode=mode,
                            innovations=bundles[action.bundle],
                                action=action,
                            progress=None if progress is None else lambda n: progress(base + n),
                        )

                        for name, value in attributes.items():
                            response_hdf5_text(action_group, name, value)
                        for name, value in arrays.items():
                            action_group.create_dataset(name, data=value, track_times=False)
                        del arrays, attributes
                    deliveries.append(delivered)
                    total += delivered.completed_intervals
    payload = stream.getvalue()
    if len(payload) > _science_NATIVE_MAXIMUM_BYTES:
        raise ValueError("preparation native panel exceeds its frozen 96-MiB artifact bound")
    return payload, tuple(sorted(deliveries, key=lambda d: d.occurrence_id)), None if mode is None else sha256(mode.tobytes()).hexdigest(), total
