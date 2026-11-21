"""External array-format effects over domain-owned scientific calculations."""
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import numpy as np
from empirical_lawhood.domains.matrix.matrix_preparation.projection import PROJECTION_SHAPES
from empirical_lawhood.adapters.simulators.matrix_preparation.projection import project_preparation_arrays
from empirical_lawhood.adapters.simulators.matrix_preparation.source import execute_preparation_panel
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _decode, _encode
from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import _run_view
from empirical_lawhood.adapters.simulators.six_matrix_response.response_source import response_hdf5_group, response_hdf5_text, response_hdf5_writer
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.matrix.matrix_preparation_analysis.tangent_records import TangentNativeResult, TangentPreparationConfig, TangentPrefixResult, TangentPrefixSegment


def acquire_tangent_root(config: TangentPreparationConfig, root, *, progress=None):
    """Full current native root; imported historical prefixes are not accepted."""
    if type(config) is not TangentPreparationConfig or root not in config.roots:
        raise ValueError("Current tangent source requires its strict complete allocation")
    segment = TangentPrefixSegment(root)
    prefix_stream = BytesIO()
    with response_hdf5_writer(prefix_stream) as artifact:
        response_hdf5_text(artifact, "schema", "empirical-lawhood/methods/matrix-preparation-analysis/current-prefix-hdf5")
        response_hdf5_text(artifact, "source_config_sha256", config.fingerprint())
        response_hdf5_text(artifact, "root_sha256", root.fingerprint())
        views = []
        for refinement in (1, 2):
            group = response_hdf5_group(artifact, f"r{refinement}")
            view, arrays = _run_view(config, segment, refinement, None, progress=progress)
            for name, values in arrays.items():
                group.create_dataset(name, data=values, track_times=False)
            views.append(view)
            del arrays
        views = tuple(views)
    primary = views[0].checkpoint
    mode = None if primary is None or primary.frozen_mode_base64 is None else _decode(primary.frozen_mode_base64, (3, 4, 4))
    views = tuple(replace(view, checkpoint=replace(view.checkpoint, frozen_mode_base64=None if mode is None else _encode(mode)))
                  if view.checkpoint is not None else view for view in views)
    prefix = TangentPrefixResult(root.root_id + ".prefix-result", config.identity, root, views)
    prefix_raw = prefix.canonical_bytes()
    prefix_artifact = ArtifactIdentity(root.root_id + ".prefix-result", "current-prefix", prefix.SCHEMA, sha256(prefix_raw).hexdigest(), "application/json", len(prefix_raw))
    checkpoints = {view.refinement: view.checkpoint for view in views if view.disposition == "COMPLETE"}
    payload, deliveries, mode_sha, completed = execute_preparation_panel(config, root, checkpoints, prefix_sha256=prefix.fingerprint(), progress=progress)
    result = TangentNativeResult(root.root_id + ".native-result", config.identity, root, prefix_artifact,
                                 mode_sha, deliveries, sha256(payload).hexdigest(), completed)
    projections = tuple(project_preparation_arrays(result, payload, refinement, source_identity=config.identity) for refinement in (1, 2))
    arrays = {name: np.stack([projection[0][name] for projection in projections]) for name in PROJECTION_SHAPES}
    arrays["prefix_complete"] = np.asarray([view.disposition == "COMPLETE" for view in views], dtype=np.bool_)
    arrays["mechanism_complete"] = np.asarray([not projection[1] for projection in projections], dtype=np.bool_)
    arrays["native_complete"] = np.asarray(all(delivery.disposition == "COMPLETE" for delivery in deliveries), dtype=np.bool_)
    arrays["prefix_completed_updates"] = np.asarray([view.delivery.completed_intervals for view in views], dtype=np.int64)
    return prefix, prefix_stream.getvalue(), result, payload, arrays
