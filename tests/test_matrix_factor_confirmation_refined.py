# SPDX-License-Identifier: MPL-2.0
"""Exact publication helper shared by current disclosed Matrix controls."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes


from empirical_lawhood.science.evidence.evidence import VisibilityCeiling as Visibility
from empirical_lawhood.domains.matrix.input_contracts import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest


def retained(plane, name, schema, raw, access):
    arrays = schema == MATRIX_ARRAY_SCHEMA
    written = plane.write(ArtifactWriteRequest(name, "refined-inputs/" + name, schema,
        ArtifactProfile.MATRIX_ARRAY_NPZ if arrays else ArtifactProfile.CANONICAL_JSON,
        "application/x-npz" if arrays else "application/json", "publication." + name, "refined-inputs", raw,
        Visibility.PROSPECTIVE, (), access))
    return resolve_artifact_sidecar_bytes(plane, plane.root.resolve(written.materialization.relative_path + '.manifest.json', for_write=False).read_bytes())
