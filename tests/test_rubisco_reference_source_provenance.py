# SPDX-License-Identifier: MPL-2.0
"""Installed derivative provenance preserves predecessors and exact source bytes."""

from hashlib import sha256
from importlib.resources import files
import json


def test_periodic_derivatives_and_diis_successor_bind_complete_packaged_sources():
    root = files("empirical_lawhood.domains.rubisco.rubisco_response")
    previous_bytes = root.joinpath("pyscf-periodic-provenance.json").read_bytes()
    previous = json.loads(previous_bytes)
    successor = json.loads(root.joinpath("pyscf-periodic-diis-storage-provenance.json").read_bytes())
    assert successor["previous_provenance_sha256"] == sha256(previous_bytes).hexdigest()
    assert successor["previous_provenance_path"] == "pyscf-periodic-provenance.json"
    current = json.loads(root.joinpath("pyscf-periodic-source-provenance-v1.json").read_bytes())
    assert {row["path"]: row["sha256"] for row in current["predecessors"]} == {
        name: sha256(root.joinpath(name).read_bytes()).hexdigest()
        for name in ("pyscf-periodic-provenance.json", "pyscf-periodic-diis-storage-provenance.json")
    }
    frozen = {row["local_path"]: row["local_sha256"] for row in previous["files"]}
    assert frozen[successor["local_path"]] == successor["previous_derivative_sha256"]
    frozen[successor["local_path"]] = successor["local_sha256"]
    for row in (*previous["upstream_notices"], previous["project_memory_helper"], previous["project_jk_helper"]):
        frozen[row["path"]] = row["sha256"]
    package = files("empirical_lawhood")
    for row in current["derivatives"]:
        assert frozen.pop(row["predecessor_path"]) == row["predecessor_sha256"]
        assert sha256(package.joinpath(row["path"]).read_bytes()).hexdigest() == row["sha256"]
    for path, digest in frozen.items():
        assert sha256(root.joinpath(path).read_bytes()).hexdigest() == digest
    assert {row["path"] for row in current["shared_sources"]} == {
        "methods/electronic_structure/diis.py", "methods/electrostatics.py"}
    for row in current["shared_sources"]:
        assert sha256(package.joinpath(row["path"]).read_bytes()).hexdigest() == row["sha256"]
