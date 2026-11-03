# SPDX-License-Identifier: MPL-2.0
"""Exposed custody memory probe; opaque strings are not scientific validation."""

from hashlib import sha256
import json
from pathlib import Path
import resource
import sys

from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
from tests.test_recursive_public_service import _plane


def main():
    plane = _plane(Path(sys.argv[1]))
    root = Path(plane.root.contract.canonical_path)
    schema = "empirical-lawhood/testing/opaque-custody-shape"
    kinds = ("battery", "rubisco", "material", "sparse-biological")
    block = b"A" * 65536
    count = 512
    members = []
    baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    for number, kind in enumerate(kinds):
        prefix = ('{"schema":"' + schema + '","value":{"kind":"' + kind + '","raw_utf8":"').encode()
        suffix = b'"},"version":"1.0.0"}\n'
        size = len(prefix) + count * len(block) + len(suffix)
        digest = sha256(prefix)
        for _ in range(count):
            digest.update(block)
        digest.update(suffix)

        def chunks():
            yield prefix
            for _ in range(count):
                yield block
            yield suffix

        name = f"operand-{number}.json"
        plane.write_stream(ArtifactStreamWriteRequest(
            logical_artifact_id=f"opaque.{kind}", relative_path="operands/" + name,
            payload_schema=schema, profile=ArtifactProfile.CANONICAL_JSON,
            media_type="application/json", publication_scope_id=f"opaque.{kind}",
            publication_scope_relative_root="operands", chunks=chunks(), maximum_bytes=size,
            maximum_chunk_bytes=len(block), visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            parent_visibility_ceilings=(), outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            expected_size_bytes=size, expected_physical_sha256=digest.hexdigest()))
        members.append(RecursiveWaveMember(name,
            ObjectIdentity(f"opaque.{kind}", schema, "1.0.0", digest.hexdigest()), size))
    payloads = AuthenticatedRecursivePayloads(plane=plane, directory=root / "operands", members=tuple(members))
    copied = []
    for member in members:
        manifest = plane.write_stream(ArtifactStreamWriteRequest(
            logical_artifact_id="copy." + member.identity.object_id,
            relative_path="copies/" + member.filename, payload_schema=schema,
            profile=ArtifactProfile.CANONICAL_JSON, media_type="application/json",
            publication_scope_id="copy." + member.identity.object_id,
            publication_scope_relative_root="copies", chunks=payloads.chunks(member.filename),
            maximum_bytes=member.size_bytes, maximum_chunk_bytes=len(block),
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=(),
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, expected_size_bytes=member.size_bytes,
            expected_physical_sha256=member.identity.object_fingerprint))
        assert manifest.logical.content_sha256 == member.identity.object_fingerprint
        assert manifest.materialization.size_bytes == member.size_bytes
        copied.append(manifest.materialization.relative_path)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    report = {"evidence_role": "EXPOSED_CUSTODY_ONLY_NO_TYPED_SCIENCE",
        "baseline_peak_rss_bytes": baseline, "peak_rss_bytes": peak,
        "additional_peak_rss_bytes": peak - baseline, "complete_member_count": len(payloads),
        "complete_payload_bytes": sum(member.size_bytes for member in members),
        "payload_kinds": kinds, "retained_decoded_scientific_records": 0,
        "complete_streamed_copy_count": len(copied), "streamed_copy_paths": copied,
        "member_census": [member.to_document() for member in members],
        "probe_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / "memory-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
