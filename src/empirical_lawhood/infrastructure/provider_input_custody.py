# SPDX-License-Identifier: MPL-2.0
"""Shared deterministic custody locators for current and historical provider inputs."""

import errno
import hashlib
from pathlib import Path, PurePosixPath
import stat

from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.kernel.serialization import MAX_RELATIVE_LOCATOR_SEGMENT_BYTES, validate_stable_id


def provider_input_location(
    artifact_plane: ExternalArtifactPlane,
    run_id: str,
    logical_artifact_id: str,
) -> tuple[str, str, str]:
    """Select fresh bounded storage or retain an existing historical input pair."""

    validate_stable_id(run_id, field_name="run_id")
    validate_stable_id(logical_artifact_id, field_name="logical_artifact_id")
    input_root = f"runs/{run_id}/inputs"
    token = hashlib.sha256(logical_artifact_id.encode("utf-8")).hexdigest()
    bucket = token[:2]
    legacy = f"{input_root}/{logical_artifact_id}.bin"
    sharded = f"{input_root}/{bucket}/{token}.bin"

    def pair_present(relative_path: str) -> bool:
        present = False
        for member in (relative_path, f"{relative_path}.manifest.json"):
            if len(PurePosixPath(member).name.encode("utf-8")) > MAX_RELATIVE_LOCATOR_SEGMENT_BYTES:
                continue
            try:
                candidate = artifact_plane.root.resolve(member, for_write=False)
                root = Path(artifact_plane.root.contract.canonical_path)
                current = root
                parts = candidate.relative_to(root).parts
                for index, part in enumerate(parts):
                    current /= part
                    observed = current.lstat()
                    if stat.S_ISLNK(observed.st_mode):
                        raise ArtifactIdentityConflict("provider input path contains a symlink")
                    if index == len(parts) - 1:
                        if not stat.S_ISREG(observed.st_mode):
                            raise ArtifactIdentityConflict("provider input member is not a regular file")
                        present = True
                    elif not stat.S_ISDIR(observed.st_mode):
                        raise ArtifactIdentityConflict("provider input parent is not a directory")
            except FileNotFoundError:
                continue
            except OSError as error:
                # An overlong historical leaf cannot exist on this filesystem.
                # The hashed locator still supports the unchanged logical ID.
                if error.errno != errno.ENAMETOOLONG:
                    raise
        return present

    legacy_present = pair_present(legacy)
    sharded_present = pair_present(sharded)
    if legacy_present and sharded_present:
        raise ArtifactIdentityConflict("provider input has ambiguous legacy and sharded custody")
    if legacy_present:
        return legacy, f"campaign-inputs.{run_id}", input_root
    return sharded, f"campaign-inputs.{run_id}.{bucket}", f"{input_root}/{bucket}"
