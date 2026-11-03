# SPDX-License-Identifier: MPL-2.0
"""Local exposed source intake refuses substitution and historical path fallback."""

from pathlib import Path
import subprocess
import sys

import pytest

from tests import rubisco_inquiry_source_fixtures as fixtures


def test_missing_local_stock_does_not_fall_back_to_session_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(fixtures, "FIXTURES", tmp_path)
    with pytest.raises(FileNotFoundError):
        fixtures.candidate_source_operands()


def test_finalist_stock_refuses_substituted_complete_primary(tmp_path, monkeypatch):
    selected = tmp_path / "rubisco/finalist"
    selected.mkdir(parents=True)
    original = fixtures.FIXTURES / "rubisco/finalist"
    (selected / "source-census.json").write_bytes((original / "source-census.json").read_bytes())
    raw = (original / "yamori2026-primary.xml").read_bytes()
    (selected / "yamori2026-primary.xml").write_bytes(raw[:-1] + b" ")
    monkeypatch.setattr(fixtures, "FIXTURES", tmp_path)
    with pytest.raises(ValueError, match="substitutes Yamori"):
        fixtures.finalist_source_operands()


def test_cold_local_stock_never_reads_external_locators_or_imports_native(tmp_path):
    root = Path(__file__).resolve().parents[1]
    probe = """
import importlib.abc
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pybamm', 'openmm', 'cantera', 'brian2'}:
            raise AssertionError('PURE fixture imports a native engine')
sys.meta_path.insert(0, RefuseNative())
original_open = Path.open
def local_read(self, *args, **kwargs):
    self.resolve().relative_to(root)
    mode = args[0] if args else kwargs.get('mode', 'r')
    assert not any(flag in mode for flag in 'wax+'), 'fixture writes outside custody'
    return original_open(self, *args, **kwargs)
Path.open = local_read
from tests.rubisco_inquiry_source_fixtures import (
    candidate_source_operands, portfolio_source_operands,
    finalist_source_operands, successor_source_operands,
)
from tests.rubisco_candidate_programme_fixture import programme_report
from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import (
    WilsonArticleInputV1, TeParentGenbankInputV1,
    WILSON_SOURCE_SHA256, GENBANK_SOURCE_SHA256,
)
assert len(candidate_source_operands()) == 22
macro = portfolio_source_operands()
assert len(macro) == 34
same_macro, mechanism, yamori = finalist_source_operands()
assert same_macro == macro and len(mechanism) == 2 and len(yamori) == 139555
article, genbank = successor_source_operands()
assert WilsonArticleInputV1('input.exposed-compile.article', WILSON_SOURCE_SHA256, article.decode()).input_id == 'input.exposed-compile.article'
assert TeParentGenbankInputV1('input.exposed-compile.genbank', GENBANK_SOURCE_SHA256, genbank.decode()).input_id == 'input.exposed-compile.genbank'
report = programme_report()
assert set(report['waves']) == {'programme-supply', 'programme-use'}
assert report['native_contacts'] == 0
assert not {'pybamm', 'openmm', 'cantera', 'brian2'}.intersection(sys.modules)
"""
    subprocess.run(
        [sys.executable, "-c", probe, str(root)],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
