# SPDX-License-Identifier: MPL-2.0
"""Original scheduled prefix custody through the stock read-only stores.

The composing API supplies its authorized original plane and selected plan.
Reading creates no qualification, issue, execution or reveal authority. It
never infers completion, begins contact, acquires a history or replays RNG.
"""

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest

from .source_index import ResolvedScheduledSource


def authenticate_source_publications(plane, source):
    """Original payload, sidecar and commit custody, distinct from staging."""
    if type(source) is not ResolvedScheduledSource:
        raise ValueError('scheduled custody cannot relabel another source owner')
    for record, publication in ((source.allocation, source.reservation.publication),
            (source.specification.selection, source.specification.publication)):
        relative = publication.materialization.relative_path
        sidecar_relative = relative+'.manifest.json'
        raw = read_bounded_bytes(plane.root.resolve(sidecar_relative, for_write=False), maximum_bytes=plane.custody_limits.manifest_bytes)
        expected = plane._manifest_materialization(logical_artifact_id=publication.logical.logical_artifact_id,
            relative_path=sidecar_relative, payload=raw)
        if publication.manifest_materialization != expected:
            raise ValueError('scheduled publication substitutes original exact sidecar materialization')
        plane.verify(publication.manifest_materialization)
        manifest = decode_artifact_manifest(raw)
        if manifest.logical != publication.logical or manifest.materialization != publication.materialization:
            raise ValueError('scheduled publication differs from original guarded manifest')
        plane.verify_manifest(manifest)
        value = read_bounded_bytes(plane.root.resolve(relative, for_write=False), maximum_bytes=publication.materialization.size_bytes)
        if value != record.canonical_bytes():
            raise ValueError('scheduled publication changes original exact frozen scientific bytes')


def _manifest(plane, relative):
    result = decode_artifact_manifest(read_bounded_bytes(plane.root.resolve(relative+'.manifest.json', for_write=False),
        maximum_bytes=plane.custody_limits.manifest_bytes))
    if result.materialization.relative_path != relative:
        raise ValueError('scheduled retained manifest substitutes selected physical path')
    plane.verify_manifest(result)
    return result


def _read_output(plane, receipt, *, schema=None, artifact=None):
    pairs = tuple((a, p) for a in receipt.output_logical_artifacts for p in receipt.output_materializations
        if a.logical_artifact_id == p.logical_artifact_id
        and (artifact is None or a.logical_artifact_id == artifact.artifact_id)
        and (schema is None or a.payload_schema == schema))
    if len(pairs) != 1:
        raise ValueError('scheduled receipt omits unique original selected output')
    logical, physical = pairs[0]
    manifest = _manifest(plane, physical.relative_path)
    if (manifest.logical != logical or manifest.materialization != physical
            or artifact is not None and (logical.content_sha256, logical.payload_schema, logical.media_type,
                physical.physical_sha256, physical.size_bytes) !=
               (artifact.sha256, artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.size_bytes)):
        raise ValueError('scheduled received bytes differ from original exact output custody')
    return read_bounded_bytes(plane.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)
