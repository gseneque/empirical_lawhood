# SPDX-License-Identifier: MPL-2.0
"""Exposed stock/path witnesses only; no Amber or molecular software executes."""

from hashlib import sha256
import os
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
    TLEAP_SEARCH_KINDS, authenticate_tleap_search_stock, selected_tleap_command,
)


@pytest.fixture
def search_stock(tmp_path):
    engine = tmp_path / "selected-engine"
    amber = engine / "ambertools24-tleap"
    binary = amber / "bin/teLeap"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"EXPOSED NEVER EXECUTABLE")
    files = [binary]
    for kind in TLEAP_SEARCH_KINDS:
        directory = amber / "dat/leap" / kind
        directory.mkdir(parents=True)
        path = directory / ("leaprc.protein.ff14SB" if kind == "cmd" else "selected-stock.dat")
        path.write_bytes(("EXPOSED " + kind).encode())
        files.append(path)
    for name in ("leaprc.water.tip3p", "leaprc.gaff2"):
        path = amber / "dat/leap/cmd" / name
        path.write_bytes(("EXPOSED " + name).encode())
        files.append(path)
    inventory = {"selected_engine_root": str(engine), "entries": tuple({
        "kind": "file", "actual_path": str(path), "path": str(path.relative_to(engine)),
        "size": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest(),
    } for path in files)}
    plan = SimpleNamespace(tleap_path=str(binary), tleap_sha256=sha256(binary.read_bytes()).hexdigest())
    return plan, inventory, amber


def test_explicit_raw_binary_command_matches_wrapper_search_order(search_stock):
    plan, inventory, amber = search_stock
    expected = (plan.tleap_path, *("-I" + str(amber / "dat/leap" / kind)
                for kind in ("prep", "lib", "parm", "cmd")), "-f", "tleap.in")
    assert selected_tleap_command(plan) == expected
    rows = authenticate_tleap_search_stock(plan, inventory)
    assert len(rows) == 6
    assert tuple(row["actual_path"] for row in rows) == tuple(
        str(path) for kind in TLEAP_SEARCH_KINDS for path in sorted((amber / "dat/leap" / kind).iterdir()))


@pytest.mark.parametrize("fault", ("extra", "missing", "changed", "directory-link", "file-link", "outside-root", "absent-command", "wrong-executable", "fifo"))
def test_unknown_or_substituted_search_stock_refuses_before_native_entry(search_stock, fault):
    plan, inventory, amber = search_stock
    if fault == "extra":
        (amber / "dat/leap/cmd/uncounted-leaprc").write_bytes(b"EXPOSED UNSELECTED")
    elif fault == "missing":
        (amber / "dat/leap/lib/selected-stock.dat").unlink()
    elif fault == "changed":
        (amber / "dat/leap/parm/selected-stock.dat").write_bytes(b"EXPOSED WRONG BYTES")
    elif fault == "directory-link":
        directory = amber / "dat/leap/prep"
        directory.rename(amber / "elsewhere")
        directory.symlink_to(amber / "elsewhere", target_is_directory=True)
    elif fault == "file-link":
        path = amber / "dat/leap/lib/selected-stock.dat"
        path.unlink()
        path.symlink_to(amber / "dat/leap/parm/selected-stock.dat")
    elif fault == "outside-root":
        inventory = inventory | {"selected_engine_root": str(amber)}
    elif fault == "absent-command":
        path = amber / "dat/leap/cmd/leaprc.protein.ff14SB"
        path.unlink()
        inventory = inventory | {"entries": tuple(row for row in inventory["entries"] if row["actual_path"] != str(path))}
    elif fault == "wrong-executable":
        plan = SimpleNamespace(tleap_path=plan.tleap_path, tleap_sha256="0" * 64)
    elif fault == "fifo":
        os.mkfifo(amber / "dat/leap/prep/unselected-fifo")
    with pytest.raises(ValueError, match="teLeap search"):
        authenticate_tleap_search_stock(plan, inventory)


def test_nested_declared_search_file_is_preserved_not_thinned(search_stock):
    plan, inventory, amber = search_stock
    path = amber / "dat/leap/parm/nested/additional.dat"
    path.parent.mkdir()
    path.write_bytes(b"EXPOSED NESTED COMPLETE STOCK")
    row = {"kind": "file", "actual_path": str(path), "path": str(path.relative_to(amber.parent)),
           "size": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}
    inventory = inventory | {"entries": (*inventory["entries"], row)}
    assert row in authenticate_tleap_search_stock(plan, inventory)


@pytest.mark.parametrize("fault", (None, "changed-target", "outside-directory"))
def test_exact_declared_search_links_are_retained_without_escape(search_stock, fault):
    plan, inventory, amber = search_stock
    directory = amber / "dat/leap/lib"
    path = directory / "declared-stock-link.dat"
    target = "selected-stock.dat"
    path.symlink_to(target if fault is None else "../parm/selected-stock.dat")
    row = {"kind": "symlink", "actual_path": str(path), "path": str(path.relative_to(amber.parent)), "target": target}
    if fault == "outside-directory":
        row = row | {"target": "../parm/selected-stock.dat"}
    inventory = inventory | {"entries": (*inventory["entries"], row)}
    if fault is None:
        assert row in authenticate_tleap_search_stock(plan, inventory)
    else:
        with pytest.raises(ValueError, match="teLeap search"):
            authenticate_tleap_search_stock(plan, inventory)
