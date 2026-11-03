# SPDX-License-Identifier: MPL-2.0
"""Literal installed files and ordinary build metadata; no scientific authority."""

from hashlib import sha256
from dataclasses import replace
from collections import Counter
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

import empirical_lawhood
from empirical_lawhood.infrastructure import selected_candidate as owner
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes


def encode(value):
    return canonical_json_document_bytes(value)


@pytest.fixture
def candidate_case(tmp_path, monkeypatch):
    installed = tmp_path / "installed"
    package = installed / "empirical_lawhood"
    payloads = {"src/empirical_lawhood/__init__.py": b"# literal installed package\n",
        "src/empirical_lawhood/math.py": b"VALUE = 7\n",
        "src/empirical_lawhood/resources/operand.txt": b"literal operand\n",
        "scripts/build.py": b"# literal build input\n", "uv.lock": b"version = 1\n",
        "pyproject.toml": b"[project]\nname = 'empirical-lawhood'\n"}
    source = tmp_path / "source-distribution"
    for name, raw in payloads.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        if name.startswith("src/empirical_lawhood/"):
            destination = installed / name.removeprefix("src/")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
    document = {"schema": "empirical-lawhood/build/source", "version": "1.0.0",
        "implementation_commit": "a" * 40, "implementation_sha256": "b" * 64,
        "source_tree_sha256": "c" * 64, "tracked_files": [
            {"relative_path": name, "mode": "100644", "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            for name, raw in sorted(payloads.items())]}
    metadata_relative = Path("empirical_lawhood-0.test.dist-info/extra_metadata/source.json")
    metadata = installed / metadata_relative
    metadata.parent.mkdir(parents=True)
    metadata.write_bytes(encode(document))
    (source / owner.SOURCE_METADATA_FILENAME).write_bytes(encode(document))
    observations = {"empirical_lawhood": SimpleNamespace(__file__=str(package / "__init__.py")),
        "empirical_lawhood.math": SimpleNamespace(__file__=str(package / "math.py"))}
    distribution = SimpleNamespace(files=(metadata_relative,), locate_file=lambda path: installed / path)
    monkeypatch.setattr(empirical_lawhood, "__file__", str(package / "__init__.py"))
    monkeypatch.setattr(owner, "distribution", lambda name: distribution if name == "empirical-lawhood" else pytest.fail(name))
    monkeypatch.setattr(owner, "sys", SimpleNamespace(modules=observations))
    monkeypatch.setattr(owner, "_installed_candidates", {})
    monkeypatch.setattr(owner, "_source_roots", {})

    check_output, run = subprocess.check_output, subprocess.run

    def observe(function, command, *args, **kwargs):
        executable = command.split()[0] if isinstance(command, str) else str(command[0])
        if Path(executable).name == "git":
            pytest.fail("installed candidate must not execute Git")
        return function(command, *args, **kwargs)

    # Ordinary library imports can probe uname; observe those real calls while
    # refusing every Git invocation rather than replacing platform discovery.
    monkeypatch.setattr(subprocess, "check_output", lambda command, *args, **kwargs: observe(check_output, command, *args, **kwargs))
    monkeypatch.setattr(subprocess, "run", lambda command, *args, **kwargs: observe(run, command, *args, **kwargs))
    return SimpleNamespace(package=package, installed=installed, source=source, metadata=metadata,
        document=document, payloads=payloads, observations=observations, distribution=distribution)


def admit(case):
    return owner.installed_candidate(source_root=case.source)


def _execution_identity_case(case, tmp_path):
    from empirical_lawhood.api import load_authoring
    from empirical_lawhood.api.execution import CampaignExecutionService
    from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry
    from tests.runtime_platform.test_native_subwork import _plane

    package = replace(load_authoring(Path(__file__).resolve().parents[1] / "fixtures/reference-campaign.json"),
        implementation_commit="a" * 40)
    def no_engine():
        pytest.fail("source admission opened a catalog or entered execution")
    service = CampaignExecutionService(repo_root=case.source,
        artifact_plane=_plane(tmp_path / "identity-custody"), engine_factory=no_engine,
        catalog_path=tmp_path / "unused-catalog.sqlite3", providers=CampaignRuntimeProviderRegistry(()))
    return service, package


@pytest.mark.parametrize("installed_commit", ("a" * 40, "d" * 40))
def test_execution_uses_one_actual_installed_observation_and_retains_commit_check(candidate_case, tmp_path, monkeypatch, installed_commit):
    from empirical_lawhood.api.execution import CampaignIdentityError
    from empirical_lawhood.infrastructure.source_origin import require_selected_implementation

    case = candidate_case
    # Each candidate is internally coherent before its first admission. Keep
    # the independently valid campaign and its actual authorization unchanged.
    case.document = dict(case.document, implementation_commit=installed_commit)
    metadata = encode(case.document)
    case.metadata.write_bytes(metadata)
    (case.source / owner.SOURCE_METADATA_FILENAME).write_bytes(metadata)
    service, package = _execution_identity_case(case, tmp_path)
    calls = []
    original = owner.installed_candidate
    def observe(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)
    monkeypatch.setattr(owner, "installed_candidate", observe)
    if installed_commit == package.implementation_commit:
        assert service._check_identity(package) is None
    else:
        with pytest.raises(CampaignIdentityError, match="campaign implementation"):
            service._check_identity(package)
    assert calls == [{"source_root": case.source}]
    assert require_selected_implementation(case.source) == case.package
    assert len(calls) == 2


@pytest.mark.parametrize("mutation", ("unloaded-member", "added-member", "missing-member", "metadata",
    "source-metadata", "pyproject", "lock"))
def test_next_execution_observation_rechecks_current_installed_bytes(candidate_case, tmp_path, monkeypatch, mutation):
    from empirical_lawhood.api.execution import CampaignIdentityError

    case = candidate_case
    service, package = _execution_identity_case(case, tmp_path)
    calls = []
    original = owner.installed_candidate
    def observe(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)
    monkeypatch.setattr(owner, "installed_candidate", observe)
    service._check_identity(package)
    assert len(calls) == 1
    if mutation == "added-member":
        (case.package / "added.py").write_bytes(b"UNSELECTED = True\n")
    elif mutation == "missing-member":
        (case.package / "resources/operand.txt").unlink()
    else:
        path = {"unloaded-member": case.package / "resources/operand.txt", "metadata": case.metadata,
            "source-metadata": case.source / owner.SOURCE_METADATA_FILENAME,
            "pyproject": case.source / "pyproject.toml", "lock": case.source / "uv.lock"}[mutation]
        raw = path.read_bytes()
        path.write_bytes(raw[:-1] + b"x")
    with pytest.raises(CampaignIdentityError, match="executing package"):
        service._check_identity(package)
    assert len(calls) == 2


@pytest.mark.parametrize("mutation", ("unloaded-member", "added-member"))
def test_first_execution_observation_closes_bytes_and_membership_after_source_binding(candidate_case, tmp_path, monkeypatch, mutation):
    from empirical_lawhood.api.execution import CampaignIdentityError

    case = candidate_case
    service, package = _execution_identity_case(case, tmp_path)
    original = owner.read_bounded_bytes
    changed = []
    def during_source_join(path, **kwargs):
        raw = original(path, **kwargs)
        if path == case.source / "pyproject.toml" and not changed:
            changed.append(path)
            if mutation == "unloaded-member":
                member = case.package / "resources/operand.txt"
                member.write_bytes(member.read_bytes()[:-1] + b"x")
            else:
                (case.package / "resources/late.txt").write_bytes(b"late unselected member\n")
        return raw
    monkeypatch.setattr(owner, "read_bounded_bytes", during_source_join)
    with pytest.raises(CampaignIdentityError, match="executing package"):
        service._check_identity(package)
    assert changed == [case.source / "pyproject.toml"]
    assert owner._installed_candidates == {}


def test_source_identity_is_reused_while_current_bytes_are_checked_without_git(candidate_case, monkeypatch):
    case = candidate_case
    reads = []
    original = owner.read_bounded_bytes

    def observe(path, **kwargs):
        reads.append(path)
        return original(path, **kwargs)

    monkeypatch.setattr(owner, "read_bounded_bytes", observe)
    first = admit(case)
    first_reads = tuple(reads)
    assert admit(case) is first
    next_reads = reads[len(first_reads):]
    assert set(next_reads) == set(first_reads)
    initial_closing_reads = Counter((case.metadata, *(case.package / name.removeprefix("src/empirical_lawhood/")
        for name in case.payloads if name.startswith("src/empirical_lawhood/"))))
    assert Counter(first_reads) == Counter(next_reads) + initial_closing_reads
    assert first.package_root == case.package and first.source_bytes == encode(case.document)
    expected = tuple((name.removeprefix("src/empirical_lawhood/"), sha256(raw).hexdigest())
        for name, raw in sorted(case.payloads.items()) if name.startswith("src/empirical_lawhood/"))
    assert first.package_sources == expected
    assert first.code_sources_sha256 == sha256(canonical_json_bytes(expected)).hexdigest()
    assert first.implementation_commit == "a" * 40
    assert first.implementation_sha256 == "b" * 64 and first.source_tree_sha256 == "c" * 64
    assert first.dependency_lock_sha256 == sha256(case.payloads["uv.lock"]).hexdigest()
    assert reads.count(case.metadata) == 3
    assert set(first.file_identities) == {"__init__.py", "math.py", "resources/operand.txt"}


@pytest.mark.parametrize("defect", ("changed", "missing", "extra", "symlink", "symlink-directory", "executable"))
def test_complete_physical_package_census_and_regular_member_bytes_are_required(candidate_case, defect, tmp_path):
    case = candidate_case
    member = case.package / "resources/operand.txt"
    if defect == "changed":
        member.write_bytes(b"foreign operand\n")
    elif defect == "missing":
        member.unlink()
    elif defect == "extra":
        (case.package / "extra.py").write_bytes(b"FOREIGN = 1\n")
    elif defect == "symlink":
        target = tmp_path / "borrowed-operand.txt"
        member.rename(target)
        member.symlink_to(target)
    elif defect == "symlink-directory":
        target = tmp_path / "borrowed-resources"
        member.parent.rename(target)
        member.parent.symlink_to(target, target_is_directory=True)
    else:
        member.chmod(0o755)
    with pytest.raises((PermissionError, ValueError, BoundedFileIOError)):
        admit(case)


@pytest.mark.parametrize("name", ("metadata", "source-metadata", "lock", "pyproject", "loaded-module"))
def test_admitted_installation_and_source_inputs_cannot_change_during_process_lifetime(candidate_case, name):
    case = candidate_case
    admit(case)
    path = {"metadata": case.metadata, "source-metadata": case.source / owner.SOURCE_METADATA_FILENAME,
        "lock": case.source / "uv.lock", "pyproject": case.source / "pyproject.toml",
        "loaded-module": case.package / "math.py"}[name]
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + b"x")
    with pytest.raises((PermissionError, ValueError, BoundedFileIOError)):
        admit(case)


@pytest.mark.parametrize("defect", ("source-metadata", "source-lock", "source-build", "checkout", "foreign-root"))
def test_source_distribution_must_match_the_installed_candidate(candidate_case, defect, tmp_path):
    case = candidate_case
    if defect == "source-metadata":
        value = dict(case.document, implementation_commit="d" * 40)
        (case.source / owner.SOURCE_METADATA_FILENAME).write_bytes(encode(value))
    elif defect == "source-lock":
        (case.source / "uv.lock").write_bytes(b"version = 9\n")
    elif defect == "source-build":
        (case.source / "pyproject.toml").write_bytes(b"foreign build input\n")
    elif defect == "checkout":
        (case.source / ".git").mkdir()
    else:
        case.source = tmp_path / "foreign-source"
        case.source.mkdir()
    with pytest.raises((PermissionError, ValueError, OSError, BoundedFileIOError)):
        admit(case)


@pytest.mark.parametrize("name", ("metadata", "lock", "pyproject"))
def test_copied_source_identity_inputs_must_remain_nonexecutable(candidate_case, name):
    case = candidate_case
    path = {"metadata": case.source / owner.SOURCE_METADATA_FILENAME,
        "lock": case.source / "uv.lock", "pyproject": case.source / "pyproject.toml"}[name]
    path.chmod(0o755)
    with pytest.raises(PermissionError, match="executable"):
        admit(case)


@pytest.mark.parametrize("defect", ("distribution", "foreign-module", "untracked-module", "namespace", "missing-metadata", "duplicate-metadata"))
def test_selected_distribution_and_loaded_module_origins_are_exact(candidate_case, defect, tmp_path):
    case = candidate_case
    if defect == "distribution":
        case.distribution.locate_file = lambda path: case.installed / "foreign" / path
    elif defect == "foreign-module":
        path = tmp_path / "foreign.py"
        path.write_bytes(b"VALUE = 7\n")
        case.observations["empirical_lawhood.math"].__file__ = str(path)
    elif defect == "untracked-module":
        case.observations["empirical_lawhood.math"].__file__ = str(case.package / "not-in-census.py")
    elif defect == "namespace":
        case.observations["empirical_lawhood.resources"] = SimpleNamespace(__file__=None,
            __spec__=SimpleNamespace(submodule_search_locations=[str(tmp_path)]))
    elif defect == "missing-metadata":
        case.distribution.files = ()
    else:
        case.distribution.files *= 2
    with pytest.raises((PermissionError, ValueError, OSError)):
        admit(case)


def test_exact_namespace_directory_has_the_admitted_installed_origin(candidate_case):
    case = candidate_case
    case.observations["empirical_lawhood.resources"] = SimpleNamespace(__file__=None,
        __spec__=SimpleNamespace(submodule_search_locations=[str(case.package / "resources")]))
    assert admit(case).package_root == case.package


@pytest.mark.parametrize("defect", ("commit", "archive-hash", "tree-hash", "empty", "null", "object", "string",
    "repeated", "escaping", "wrong-size", "encoding"))
def test_source_metadata_validates_canonical_complete_identity_before_admission(candidate_case, defect):
    case = candidate_case
    value = json.loads(encode(case.document))
    if defect == "commit":
        value["implementation_commit"] = "HEAD"
    elif defect == "archive-hash":
        value["implementation_sha256"] = "not-a-digest"
    elif defect == "tree-hash":
        value["source_tree_sha256"] = "not-a-digest"
    elif defect == "empty":
        value["tracked_files"] = []
    elif defect in ("null", "object", "string"):
        value["tracked_files"] = {"null": None, "object": {}, "string": "uv.lock"}[defect]
    elif defect == "repeated":
        value["tracked_files"].append(value["tracked_files"][-1])
    elif defect == "escaping":
        value["tracked_files"][0]["relative_path"] = "../outside.py"
    elif defect == "wrong-size":
        value["tracked_files"][0]["size_bytes"] = -1
    raw = encode(value)
    case.metadata.write_bytes(raw.rstrip(b"\n") if defect == "encoding" else raw)
    with pytest.raises((PermissionError, ValueError)):
        admit(case)


def test_installed_source_admission_never_claims_a_clean_checkout(candidate_case):
    from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source
    from empirical_lawhood.infrastructure.source_policy import InstalledSourceAdmission

    source = capture_admitted_target_source(candidate_case.source)
    assert type(source.source_admission) is InstalledSourceAdmission
    assert source.source_admission.to_mapping()["checkout_observed"] is False
    assert source.source_admission.to_mapping()["observed_checkout_clean"] is False
    assert source.implementation_commit == "a" * 40
    assert source.source_admission.source_metadata_sha256 == sha256(encode(candidate_case.document)).hexdigest()


@pytest.mark.parametrize("defect", ("changed-resource", "same-size-resource", "missing-resource", "extra-file", "extra-nested-file"))
def test_cached_candidate_detects_unloaded_resource_and_complete_membership_changes(candidate_case, defect):
    case = candidate_case
    admit(case)
    member = case.package / "resources/operand.txt"
    if defect == "changed-resource":
        member.write_bytes(b"changed bytes!\n")
    elif defect == "same-size-resource":
        raw = b"foreign operand\n"
        assert len(raw) == member.stat().st_size
        member.write_bytes(raw)
    elif defect == "missing-resource":
        member.unlink()
    elif defect == "extra-file":
        (case.package / "undeclared.py").write_bytes(b"VALUE = 9\n")
    else:
        (case.package / "resources/undeclared.txt").write_bytes(b"new undeclared data\n")
    with pytest.raises((PermissionError, OSError)):
        admit(case)


def test_ordinary_interpreter_cache_does_not_change_installed_source_membership(candidate_case):
    case = candidate_case
    first = admit(case)
    cache = case.package / "__pycache__"
    cache.mkdir()
    (cache / "math.cpython-311.pyc").write_bytes(b"ordinary interpreter cache\n")
    assert admit(case) is first
    (case.package / "math.pyc").write_bytes(b"legacy interpreter cache\n")
    assert admit(case) is first
