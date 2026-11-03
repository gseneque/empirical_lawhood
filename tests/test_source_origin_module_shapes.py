# SPDX-License-Identifier: MPL-2.0
"""Read-only origin controls with an in-memory module and Git census."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import source_origin as owner


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/empirical_lawhood"
TRACKED = ("src/empirical_lawhood/__init__.py", "src/empirical_lawhood/infrastructure/source_origin.py",
    "src/empirical_lawhood/_vendor/declared.py")


@pytest.fixture
def modules(monkeypatch):
    values = {"empirical_lawhood": SimpleNamespace(__file__=str(PACKAGE / "__init__.py"))}
    monkeypatch.setattr(owner, "sys", SimpleNamespace(modules=values))

    def git(arguments, **kwargs):
        assert kwargs["cwd"] == ROOT
        if arguments == ("git", "rev-parse", "--show-toplevel"):
            raw = str(ROOT).encode() + b"\n"
        else:
            assert arguments == ("git", "ls-files", "-z", "--", "src/empirical_lawhood")
            raw = b"\0".join(path.encode() for path in TRACKED) + b"\0"
        return SimpleNamespace(returncode=0, stdout=raw)

    monkeypatch.setattr(owner, "run_bounded_command", git)
    return values


def test_tracked_python_module_and_exact_source_namespace_are_admitted(modules):
    modules["empirical_lawhood.infrastructure.source_origin"] = SimpleNamespace(__file__=str(PACKAGE / "infrastructure/source_origin.py"))
    modules["empirical_lawhood._vendor"] = SimpleNamespace(__file__=None,
        __spec__=SimpleNamespace(submodule_search_locations=[str(PACKAGE / "_vendor")]))
    assert owner.require_executing_target_source(ROOT) == PACKAGE


@pytest.mark.parametrize("origin", ("/other/module.so", "/other/module.pyc", str(PACKAGE / "__pycache__/module.pyc"), 4))
def test_non_source_or_foreign_extension_origins_cannot_be_silently_skipped(modules, origin):
    modules["empirical_lawhood.intruder"] = SimpleNamespace(__file__=origin)
    with pytest.raises(owner.ExecutingSourceMismatch, match="supported tracked Python"):
        owner.require_executing_target_source(ROOT)


@pytest.mark.parametrize("module", (None, SimpleNamespace(__file__=None),
    SimpleNamespace(__file__=None, __spec__=SimpleNamespace(submodule_search_locations=[])),
    SimpleNamespace(__file__=None, __spec__=SimpleNamespace(submodule_search_locations=str(PACKAGE / "_vendor"))),
    SimpleNamespace(__file__=None, __spec__=SimpleNamespace(submodule_search_locations=[str(PACKAGE / "_vendor"), "/other"])),
    SimpleNamespace(__file__=None, __spec__=SimpleNamespace(submodule_search_locations=[str(PACKAGE / "infrastructure")]))))
def test_originless_modules_require_one_exact_actual_namespace_directory(modules, module):
    modules["empirical_lawhood._vendor"] = module
    with pytest.raises(owner.ExecutingSourceMismatch, match="namespace|origin cannot be verified"):
        owner.require_executing_target_source(ROOT)


def test_regular_package_cannot_masquerade_as_an_originless_namespace(modules):
    modules["empirical_lawhood.infrastructure"] = SimpleNamespace(__file__=None,
        __spec__=SimpleNamespace(submodule_search_locations=[str(PACKAGE / "infrastructure")]))
    with pytest.raises(owner.ExecutingSourceMismatch, match="namespace"):
        owner.require_executing_target_source(ROOT)


def test_foreign_python_and_untracked_local_python_origins_still_refuse(modules):
    for origin in ("/other/module.py", str(PACKAGE / "untracked.py")):
        modules["empirical_lawhood.intruder"] = SimpleNamespace(__file__=origin)
        with pytest.raises(owner.ExecutingSourceMismatch, match="outside|not tracked"):
            owner.require_executing_target_source(ROOT)
