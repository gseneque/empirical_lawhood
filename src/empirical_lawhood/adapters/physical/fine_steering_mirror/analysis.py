"""Authenticated source-file acquisition for the optical development analysis."""
from pathlib import Path
from empirical_lawhood.domains.optics.fine_steering_mirror.contracts import FineSteeringMirrorProtocolSpec, FineSteeringMirrorBlockResponse, FineSteeringMirrorDevelopmentModel
from empirical_lawhood.domains.optics.fine_steering_mirror.analysis import FineSteeringMirrorDevelopmentError as _science_FineSteeringMirrorDevelopmentError, analyze_development_arrays as _science_analyze_development_arrays
from empirical_lawhood.adapters.physical.fine_steering_mirror.observation import load_safe_array, sha256_path

def analyze_development(
    *,
    action_paths: tuple[Path, Path, Path],
    receiver_paths: tuple[Path, Path, Path],
    protocol: FineSteeringMirrorProtocolSpec,
    member_sha256: dict[str, str],
) -> tuple[tuple[FineSteeringMirrorBlockResponse, ...], FineSteeringMirrorDevelopmentModel]:
    """Reduce six development blocks and fit the predeclared scalar action map."""

    observed_digests = tuple(sorted(sha256_path(path) for path in (*action_paths, *receiver_paths)))
    if observed_digests != protocol.expected_development_sha256:
        raise _science_FineSteeringMirrorDevelopmentError("development source bytes differ from the frozen protocol")
    for path in (*action_paths, *receiver_paths):
        expected = member_sha256.get(path.name)
        if expected is None or sha256_path(path) != expected:
            raise _science_FineSteeringMirrorDevelopmentError(f"development member identity differs: {path.name}")
    actions = tuple(load_safe_array(path, expected_realizations=6, operator=protocol.observation_operator) for path in action_paths)
    receivers = tuple(load_safe_array(path, expected_realizations=6, operator=protocol.observation_operator) for path in receiver_paths)
    return _science_analyze_development_arrays(action_arrays=actions, receiver_arrays=receivers, protocol=protocol)
