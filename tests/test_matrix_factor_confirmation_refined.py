# SPDX-License-Identifier: MPL-2.0
"""Exact publication helper shared by current disclosed Matrix controls."""

from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


def retained(plane, name, schema, raw, access):
    arrays = schema == MATRIX_ARRAY_SCHEMA
    written = plane.write(ArtifactWriteRequest(name, "refined-inputs/" + name, schema,
        ArtifactProfile.MATRIX_ARRAY_NPZ if arrays else ArtifactProfile.CANONICAL_JSON,
        "application/x-npz" if arrays else "application/json", "publication." + name, "refined-inputs", raw,
        Visibility.PROSPECTIVE, (), access))
    return decode_artifact_manifest(plane.root.resolve(written.materialization.relative_path + ".manifest.json",
        for_write=False).read_bytes())
