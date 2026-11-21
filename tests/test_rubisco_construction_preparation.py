# SPDX-License-Identifier: MPL-2.0
"""Selection and active-reader controls; exposed fixtures grant no qualification."""

from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import zlib

import pytest

from empirical_lawhood.api.domain_composition.rubisco_response import construction_preparation as owner
from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import CONSTRUCTION_PACKAGES
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import STOCK_NAMES
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_rubisco_geometry_reuse import original  # noqa: F401


def test_parameter_selection_binds_all_original_bytes_before_return(tmp_path):
    members = {}
    for name in STOCK_NAMES:
        path = tmp_path / name
        path.write_bytes(("EXPOSED " + name).encode())
        members[name] = dict(path=str(path), sha256=sha256(path.read_bytes()).hexdigest(), original_url="exposed:" + name)
    selected = owner.select_gp_amber_parameters(members=members)
    assert tuple(row.member_id for row in selected) == tuple("source.gp-initial-amber." + name for name in STOCK_NAMES)
    (tmp_path / STOCK_NAMES[-1]).write_bytes(b"changed final member")
    with pytest.raises(ValueError, match="original-byte substitution"):
        owner.select_gp_amber_parameters(members=members)
    members.pop(STOCK_NAMES[-1])
    with pytest.raises(ValueError, match="six stock"):
        owner.select_gp_amber_parameters(members=members)


def test_selected_numeric_census_includes_pdbfixer_and_refuses_later_mutation(tmp_path):
    for package in CONSTRUCTION_PACKAGES:
        (tmp_path / package).mkdir()
        (tmp_path / package / "exposed.txt").write_bytes(b"EXPOSED non-executable stock")
    engine = owner.select_gp_construction_engine(site_packages=tmp_path, interpreter=Path(sys.executable).resolve())
    authenticate_numeric_engine(engine)
    assert {row.relative_path.split("/")[0] for row in engine.files} == set(CONSTRUCTION_PACKAGES)
    (tmp_path / "pdbfixer" / "exposed.txt").write_bytes(b"changed construction library")
    with pytest.raises(ValueError):
        authenticate_numeric_engine(engine)


@pytest.mark.parametrize("failure", (None, "receipt", "archive", "consumer"))
def test_parent_preparation_keeps_reader_active_and_closes_every_outcome(original, tmp_path, monkeypatch, failure):  # noqa: F811
    parent = tmp_path / "parent.json"; parent.write_bytes(original.supply.canonical_bytes())
    assessment = tmp_path / "assessment.json"; assessment.write_bytes(original.assessment.canonical_bytes())
    source_plane = _plane(tmp_path / "source-custody")
    destination_plane = _plane(tmp_path / "new-custody")
    archive = source_plane.root.resolve(original.supply.archive_evidence.relative_path, for_write=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original.archive, archive)
    if failure == "archive":
        with archive.open("r+b") as stream:
            stream.seek(32); stream.write(b"corruption")
    state = dict(active=False, entries=0, exits=0, recoveries=0, preparations=0)
    class Native:
        def recover(self, definition):
            assert state["active"] and definition == original.supply.definition
            state["recoveries"] += 1
            return None if failure == "receipt" else SimpleNamespace(
                completion=original.supply.completion, receipt=original.supply.receipt)
    @contextmanager
    def reading(plane, supply):
        assert plane is source_plane and supply == original.supply
        state["active"] = True; state["entries"] += 1
        try:
            yield Native()
        finally:
            state["active"] = False; state["exits"] += 1
    def prepare(**kwargs):
        assert state["active"]
        assert kwargs["heavy_pdb"].encode() == original.files["complete-heavy.pdb"]
        assert kwargs["origin_json"].encode() == original.files["atom-origin-provenance.json"]
        state["preparations"] += 1
        if failure == "consumer":
            raise ValueError("exposed consumer failure")
        return "exposed prepared operand"
    gp = StructuralSourceMember("1bwv.cif", "exposed:source", sha256(b"EXPOSED").hexdigest(), "EXPOSED")
    monkeypatch.setattr(owner, "ORIGINALS", (("1bwv.cif", gp.sha256),))
    monkeypatch.setattr(owner, "native_result_reader", reading)
    monkeypatch.setattr(owner, "original_assembly", lambda *args: ((), (), None, None, None))
    monkeypatch.setattr(owner, "source_disulfide_partners", lambda *args: ())
    monkeypatch.setattr(owner, "assess", lambda **kwargs: original.assessment)
    monkeypatch.setattr(owner, "prepare_gp_geometry_repair", prepare)
    arguments = dict(parent_file=parent, assessment_file=assessment, gp_source=gp,
        original_artifact_writer=source_plane, destination_relative_path="parent-operands",
        artifact_writer=destination_plane, amber_engine=None, numeric_engine=None)
    if failure:
        with pytest.raises((ValueError, OSError, EOFError, zlib.error)):
            owner.prepare_gp_repair_from_original(**arguments)
    else:
        assert owner.prepare_gp_repair_from_original(**arguments) == "exposed prepared operand"
    assert state["entries"] == state["exits"] == state["recoveries"] == 1
    assert not state["active"]
    assert state["preparations"] == (0 if failure in ("receipt", "archive") else 1)
    if failure == "receipt":
        assert not destination_plane.root.resolve("parent-operands", for_write=False).exists()
