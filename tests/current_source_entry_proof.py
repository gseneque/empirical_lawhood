# SPDX-License-Identifier: MPL-2.0
"""Independent source-entry observations for exposed worker controls."""

from hashlib import sha256
import json

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.selected_candidate import read_source_metadata
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes


def current_source_entry_proof(custody_root, context, prepared_contract):
    implementation = prepared_contract.implementation
    commit = implementation.observed_git_head
    entries = custody_root / "operational/run-source-entries" / context.run_id
    matching = []
    candidate_reference = None
    for path in sorted(entries.glob("*.json")):
        raw = read_bounded_bytes(path, maximum_bytes=1024**2)
        entry = json.loads(raw)
        assert canonical_json_document_bytes(entry) == raw
        assert path.stem == sha256(raw).hexdigest()
        if (entry["run_id"] != context.run_id
                or entry["candidate"]["implementation_commit"] != commit
                or prepared_contract.execution_plan.to_document() not in entry["source_bindings"]):
            continue
        assert entry["schema"] == "empirical-lawhood/operational/run-source-entry"
        assert entry["version"] == "1.0.0"
        assert entry["scientific_authority"] == "NONE"
        assert entry["worker_source_checks"] == "REQUIRED_SEPARATELY"
        assert entry["dependency_lock_sha256"] == implementation.dependency_lock_sha256
        if candidate_reference is None:
            candidate_reference = entry["candidate"]
        else:
            assert entry["candidate"] == candidate_reference
        matching.append({"path": str(path), "sha256": path.stem})
    assert matching and candidate_reference is not None
    reference = candidate_reference
    expected_relative = "operational/source-candidates/" + reference["sha256"] + ".json"
    assert reference["relative_path"] == expected_relative
    metadata, raw = read_source_metadata(custody_root / expected_relative)
    assert len(raw) == reference["size_bytes"] and sha256(raw).hexdigest() == reference["sha256"]
    assert metadata["implementation_commit"] == reference["implementation_commit"] == commit
    assert metadata["implementation_sha256"] == reference["implementation_sha256"]
    assert metadata["source_tree_sha256"] == reference["source_tree_sha256"]
    prefix = "src/empirical_lawhood/"
    package_sources = tuple((row["relative_path"][len(prefix):], row["sha256"])
        for row in metadata["tracked_files"] if row["relative_path"].startswith(prefix))
    assert package_sources == implementation.package_sources
    assert sha256(canonical_json_bytes(package_sources)).hexdigest() == implementation.code_sources_sha256
    assert tuple(row["sha256"] for row in metadata["tracked_files"]
                 if row["relative_path"] == "uv.lock") == (implementation.dependency_lock_sha256,)
    return {"candidate": reference, "entry_receipts": matching}
