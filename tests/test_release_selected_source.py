# SPDX-License-Identifier: MPL-2.0
"""Release admission authenticates selected blobs instead of empty Git status."""

import hashlib
import io
import tarfile
import tomllib
import zipfile

import pytest

from scripts import release_check as release
from scripts import release_portable_evidence as evidence
from empirical_lawhood.infrastructure import source_policy


SOURCE_METADATA = b'{"software_fixture":"complete-source-owner-stub"}\n'


@pytest.fixture(autouse=True)
def synthetic_metadata_owner(monkeypatch):
    # This module isolates member/plan census; metadata-owner contract and
    # adverse exact identities have their own release artifact controls.
    monkeypatch.setattr(release, "source_metadata_bytes", lambda root: SOURCE_METADATA)


def add_source_metadata(archive):
    member = tarfile.TarInfo("distribution/empirical-lawhood-source.json")
    member.size = len(SOURCE_METADATA)
    archive.addfile(member, io.BytesIO(SOURCE_METADATA))


def blob(payload):
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def index(monkeypatch, entries):
    raw = b"".join(f"{mode} {blob(payload)} 0\t{name}\0".encode()
                   for name, (mode, payload) in entries.items())
    monkeypatch.setattr(evidence.subprocess, "check_output", lambda *args, **kwargs: raw)


def test_staged_selected_bytes_are_exact_while_unrelated_prose_is_outside_scope(tmp_path, monkeypatch):
    payload = b"selected = 1\n"
    (tmp_path / "module.py").write_bytes(payload)
    (tmp_path / "unrelated.txt").write_bytes(b"unstaged unrelated prose\n")
    index(monkeypatch, {"module.py": ("100644", payload), "unrelated.txt": ("100644", b"old prose\n")})
    selected = evidence.candidate_inventory(tmp_path, selected_paths=("module.py",), verify_selected=True)
    assert selected == [{"path": "module.py", "mode": "100644", "size_bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()}]
    (tmp_path / "module.py").write_bytes(b"selected = 2\n")
    with pytest.raises(ValueError, match="selected Git blob"):
        evidence.candidate_inventory(tmp_path, selected_paths=("module.py",), verify_selected=True)


@pytest.mark.parametrize("permissions,git_mode,accepted", [(0o664, "100644", True), (0o775, "100755", True),
    (0o674, "100755", False), (0o665, "100644", False), (0o4664, "100644", False)])
def test_selected_git_executable_class_is_exact(tmp_path, monkeypatch, permissions, git_mode, accepted):
    target = tmp_path / "selected.py"
    target.write_bytes(b"source\n")
    target.chmod(permissions)
    index(monkeypatch, {target.name: (git_mode, target.read_bytes())})
    if accepted:
        assert evidence.candidate_inventory(tmp_path, verify_selected=True)[0]["mode"] == git_mode
    else:
        with pytest.raises(ValueError, match="executable mode"):
            evidence.candidate_inventory(tmp_path, verify_selected=True)


def test_release_scope_covers_actual_code_test_documentation_and_environment_inputs(tmp_path, monkeypatch):
    names = ("src/empirical_lawhood/native.bin", "scripts/check.py", "tests/test_case.py", "configs/inputs.json",
             "docs/guide.md", "programmes/foundations/example/workflows/case/input.json", "experiments/case/input.json", "paper/source/storage.py", "assets/figure.svg",
             "LICENSES/MIT.txt", "README.md", "AGENTS.md", ".coveragerc", "uv.lock", "pyproject.toml",
             "unrelated.txt")
    index(monkeypatch, {name: ("100644", b"tracked") for name in names})
    assert evidence.release_input_paths(tmp_path) == tuple(sorted(set(names) - {"unrelated.txt"}))


def test_release_scope_excludes_complete_work_plan_categories_but_keeps_current_scientific_protocols(tmp_path, monkeypatch):
    protocols = ("programmes/foundations/emergent-structure/records/matrix-history-analysis-v1.md",
                 "programmes/foundations/emergent-structure/records/empirical-lawhood.preparation-applicability.md",
                 "src/empirical_lawhood/adapters/methods/finite_response_law/specification.md")
    plans = (*sorted(source_policy.ROOT_WORK_PLAN_NAMES), "docs/plans/matrix-history-analysis-v1.md",
             "docs/plans/future-operational-plan.md", "PROREVIEW/THEMATRIX-FINALDESIGN-UPDATED.md", "FINALISEARCH.md",
             *sorted(source_policy.NESTED_WORK_PLAN_PATHS | source_policy.DOCUMENT_WORK_PLAN_PATHS))
    index(monkeypatch, {name: ("100644", b"tracked") for name in (*protocols, *plans)})
    assert evidence.release_input_paths(tmp_path) == tuple(sorted(protocols))


def test_new_root_markdown_requires_explicit_release_classification(tmp_path, monkeypatch):
    index(monkeypatch, {"unclassified.md": ("100644", b"tracked")})
    with pytest.raises(ValueError, match="classification"):
        evidence.release_input_paths(tmp_path)


def test_work_plan_inventory_accounts_for_the_complete_checkout_root_markdown():
    actual = {path.name for path in release.ROOT.glob("*.md")}
    assert actual <= source_policy.ROOT_WORK_PLAN_NAMES | source_policy.MAINTAINED_ROOT_MARKDOWN
    assert not source_policy.ROOT_WORK_PLAN_NAMES & source_policy.MAINTAINED_ROOT_MARKDOWN
    assert source_policy.LOCAL_PLAN_NAME == "WTF.md"


def test_candidate_source_read_refuses_oversized_census_before_reading(tmp_path, monkeypatch):
    (tmp_path / "selected.py").write_bytes(b"bounded source\n")
    index(monkeypatch, {"selected.py": ("100644", b"bounded source\n")})
    monkeypatch.setattr(evidence, "_MAX_SELECTED_SOURCE_BYTES", 1)
    monkeypatch.setattr(evidence.os, "read", lambda *args: pytest.fail("oversized source was read"))
    with pytest.raises(ValueError, match="bounded complete census"):
        evidence.candidate_inventory(tmp_path, verify_selected=True)


def test_candidate_source_read_refuses_symbolic_member(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.repository_identity import RepositoryIdentityError

    (tmp_path / "original.py").write_bytes(b"source\n")
    (tmp_path / "selected.py").symlink_to(tmp_path / "original.py")
    index(monkeypatch, {"selected.py": ("100644", b"source\n")})
    with pytest.raises(RepositoryIdentityError, match="opened safely"):
        evidence.candidate_inventory(tmp_path, verify_selected=True)


@pytest.mark.parametrize("extra", ["", "?? tests/test_extra.py\0", "?? configs/new.json\0",
    "?? other.md\0", "?? MATRIXAUDIT-extra.md\0", "?? THEMATRIX-AUDIT-EXPDESIGN-copy.md\0",
    "?? nested/MATRIXAUDIT.md\0", "?? docs/THEMATRIX-AUDIT-EXPDESIGN.md\0",
    "?? MATRIX-FINALOPTIM-copy.md\0", "?? docs/MATRIX-FINALOPTIM.md\0"])
def test_local_plan_disclosure_admits_exact_root_notes_and_refuses_undeclared_inputs(tmp_path, monkeypatch, extra):
    from empirical_lawhood.infrastructure import source_closure, source_origin

    notes = tuple(sorted(source_policy.ROOT_WORK_PLAN_NAMES))
    for name in notes:
        (tmp_path / name).write_bytes((name + " local operational note\n").encode())
    monkeypatch.setattr(source_origin, "require_executing_target_source", lambda root: None)
    monkeypatch.setattr(source_closure, "_source_path_census", lambda root: {"scripts/check.py"})
    raw = b"".join(b"?? " + name.encode() + b"\0" for name in notes) + b" M unrelated.txt\0" + extra.encode()
    monkeypatch.setattr(release.subprocess, "check_output", lambda *args, **kwargs: raw)
    if extra:
        with pytest.raises(ValueError, match="undeclared"):
            release.release_source_disclosure(tmp_path, ("scripts/check.py",))
    else:
        result = release.release_source_disclosure(tmp_path, ("scripts/check.py",))
        assert not result["observed_checkout_clean"]
        assert result["raw_status_sha256"] == hashlib.sha256(raw).hexdigest()
        assert tuple(row["relative_path"] for row in result["changes"]) == (*notes, "unrelated.txt")
        assert result["selected_path_changes"] == ()
        assert result["local_plan"]["relative_path"] == "WTF.md"
        assert result["local_plan"]["sha256"] == hashlib.sha256((tmp_path / "WTF.md").read_bytes()).hexdigest()
        assert result["excluded_work_plans"]["active_plan"] == "WTF.md"
        assert tuple(row["path"] for row in result["excluded_work_plans"]["inventory"]) == notes
        for row in result["excluded_work_plans"]["inventory"]:
            assert row["sha256"] == hashlib.sha256((tmp_path / row["path"]).read_bytes()).hexdigest()


@pytest.mark.parametrize("name", ("CONSOLIDATION.md", "RECURARCH.md", "docs/plans/preserved.md",
    *sorted(source_policy.NESTED_WORK_PLAN_PATHS | source_policy.DOCUMENT_WORK_PLAN_PATHS)))
@pytest.mark.parametrize("kind", ("executable", "symlink", "directory"))
def test_audit_note_exception_requires_regular_nonexecutable_root_data(tmp_path, monkeypatch, name, kind):
    from empirical_lawhood.infrastructure import source_closure, source_origin

    note = tmp_path / name
    note.parent.mkdir(parents=True, exist_ok=True)
    if kind == "directory":
        note.mkdir()
    elif kind == "symlink":
        target = tmp_path / "unrelated.txt"
        target.write_bytes(b"ordinary unrelated bytes\n")
        note.symlink_to(target)
    else:
        note.write_bytes(b"operational note\n")
        note.chmod(0o755)
    monkeypatch.setattr(source_origin, "require_executing_target_source", lambda root: None)
    monkeypatch.setattr(source_closure, "_source_path_census", lambda root: {"scripts/check.py"})
    monkeypatch.setattr(release.subprocess, "check_output", lambda *args, **kwargs: b"?? " + name.encode() + b"\0")
    with pytest.raises(ValueError, match="regular non-executable"):
        release.release_source_disclosure(tmp_path, ("scripts/check.py",))


@pytest.mark.parametrize("name", sorted(source_policy.DOCUMENT_WORK_PLAN_PATHS))
def test_documentary_plan_inventory_refuses_symlink_parent(tmp_path, monkeypatch, name):
    from empirical_lawhood.infrastructure import source_closure, source_origin

    plan = tmp_path / name
    plan.parent.mkdir(parents=True)
    plan.write_bytes(b"archival work queue\n")
    directory = tmp_path / "docs"
    directory.rename(tmp_path / "elsewhere")
    directory.symlink_to(tmp_path / "elsewhere", target_is_directory=True)
    monkeypatch.setattr(source_origin, "require_executing_target_source", lambda root: None)
    monkeypatch.setattr(source_closure, "_source_path_census", lambda root: {"scripts/check.py"})
    monkeypatch.setattr(release.subprocess, "check_output", lambda *args, **kwargs: b"?? " + name.encode() + b"\0")
    with pytest.raises(ValueError, match="without symlink parents"):
        release.release_source_disclosure(tmp_path, ("scripts/check.py",))


def test_untracked_executable_has_no_operational_prose_exception(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure import source_closure, source_origin

    path = tmp_path / "unrelated.txt"
    path.write_bytes(b"executable input\n")
    path.chmod(0o755)
    monkeypatch.setattr(source_origin, "require_executing_target_source", lambda root: None)
    monkeypatch.setattr(source_closure, "_source_path_census", lambda root: {"scripts/check.py"})
    monkeypatch.setattr(release.subprocess, "check_output", lambda *args, **kwargs: b"?? unrelated.txt\0")
    with pytest.raises(ValueError, match="undeclared executable"):
        release.release_source_disclosure(tmp_path, ("scripts/check.py",))


def test_wheel_and_sdist_share_the_complete_work_plan_exclusion_policy():
    config = tomllib.loads((release.ROOT / "pyproject.toml").read_text())
    build = config["tool"]["hatch"]["build"]
    assert set(build["exclude"]) == {"/" + name for name in source_policy.ROOT_WORK_PLAN_NAMES
        | source_policy.NESTED_WORK_PLAN_PATHS | source_policy.DOCUMENT_WORK_PLAN_PATHS} | {
        *("/" + name for name in source_policy.WORK_PLAN_DIRECTORIES),
        "/docs/blog", "/FINAL*.md", "/DERPCHAIN*.md", "/LOWFRICTION*.md",
        "/SCIREVIEW*.md", "/DOCFINALISE*.md"}
    assert all("exclude" not in target for target in build["targets"].values())


@pytest.mark.parametrize("target", ("sdist", "wheel"))
def test_actual_build_backend_excludes_work_records_and_preserves_supported_science(target):
    from hatchling.builders.sdist import SdistBuilder
    from hatchling.builders.wheel import WheelBuilder

    builder = (SdistBuilder if target == "sdist" else WheelBuilder)(str(release.ROOT))
    excluded = builder.config.exclude_spec
    assert all(excluded.match_file(name) for name in source_policy.ROOT_WORK_PLAN_NAMES)
    assert all(excluded.match_file(name) for name in source_policy.NESTED_WORK_PLAN_PATHS)
    assert all(excluded.match_file(name) for name in source_policy.DOCUMENT_WORK_PLAN_PATHS)
    assert excluded.match_file("docs/plans/preserved-specification.md")
    assert excluded.match_file("PROREVIEW/THEMATRIX-FINALDESIGN-UPDATED.md")
    assert not excluded.match_file("docs/protocols/current-specification.md")
    assert not excluded.match_file("programmes/shared-records/applied-el/reopened-results.md")
    assert not excluded.match_file("programmes/biology/photosynthesis/records/branch-sensitivity-protocol-v3.md")
    assert not excluded.match_file("docs/applied-el/unclassified-record.md")
    assert not excluded.match_file(
        "src/empirical_lawhood/adapters/methods/finite_response_law/specification.md")
    assert not excluded.match_file(
        "src/empirical_lawhood/adapters/methods/unclassified/frozen_specification.md")


@pytest.mark.parametrize("name", (*sorted(source_policy.ROOT_WORK_PLAN_NAMES), "docs/plans/preserved.md", "PROREVIEW/review.md",
    *sorted(source_policy.NESTED_WORK_PLAN_PATHS | source_policy.DOCUMENT_WORK_PLAN_PATHS)))
def test_even_committed_work_plans_are_refused_in_the_source_distribution(tmp_path, monkeypatch, name):
    monkeypatch.setattr(evidence, "_selected_entries", lambda *args: {name: ("100644", blob(b"plan"))})
    path = tmp_path / "leaked.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("distribution/" + name)
        member.size = 4
        archive.addfile(member, io.BytesIO(b"plan"))
    with pytest.raises(RuntimeError, match="working plan"):
        release.compare_sdist_committed_source(tmp_path, path)


def test_release_disclosure_inventories_nested_and_documentary_archival_plans(tmp_path,monkeypatch):
    from empirical_lawhood.infrastructure import source_closure, source_origin

    plans=source_policy.NESTED_WORK_PLAN_PATHS | source_policy.DOCUMENT_WORK_PLAN_PATHS | {"PROREVIEW/review.md"}
    for name in plans:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b"archival operational instructions\n")
    monkeypatch.setattr(source_origin,"require_executing_target_source",lambda root:None)
    monkeypatch.setattr(source_closure,"_source_path_census",lambda root:{"scripts/check.py"})
    raw=b"".join(b"?? "+name.encode()+b"\0" for name in sorted(plans))
    monkeypatch.setattr(release.subprocess,"check_output",lambda *a,**kw:raw)
    rows=release.release_source_disclosure(tmp_path,("scripts/check.py",))["excluded_work_plans"]["inventory"]
    assert {row["path"] for row in rows}==plans
    assert all(row["sha256"]==hashlib.sha256((tmp_path/row["path"]).read_bytes()).hexdigest() for row in rows)


@pytest.mark.parametrize("name",sorted(source_policy.NESTED_WORK_PLAN_PATHS))
def test_wheel_comparison_excludes_archival_source_and_refuses_any_leak(tmp_path,monkeypatch,name):
    module="src/empirical_lawhood/module.py"
    for selected,raw in ((module,b"current code\n"),(name,b"historical instructions\n")):
        path=tmp_path/selected;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    monkeypatch.setattr(release,"output",lambda *a,**kw:module+"\n"+name)
    clean=tmp_path/"current.whl"
    with zipfile.ZipFile(clean,"w") as archive:
        archive.writestr(module.removeprefix("src/"),b"current code\n")
        archive.writestr("empirical_lawhood-0.test.dist-info/METADATA", b"software fixture\n")
        archive.writestr("empirical_lawhood-0.test.dist-info/extra_metadata/source.json", SOURCE_METADATA)
    assert len(release.compare_wheel_source(tmp_path,clean))==1
    with zipfile.ZipFile(clean,"a") as archive:
        archive.writestr(name.removeprefix("src/"),b"historical instructions\n")
    with pytest.raises(RuntimeError,match="wheel/source mismatch"):
        release.compare_wheel_source(tmp_path,clean)


@pytest.mark.parametrize("name", sorted(source_policy.DOCUMENT_WORK_PLAN_PATHS))
def test_wheel_refuses_documentary_work_plan_outside_the_package(tmp_path, monkeypatch, name):
    module = "src/empirical_lawhood/module.py"
    path = tmp_path / module
    path.parent.mkdir(parents=True)
    path.write_bytes(b"current code\n")
    monkeypatch.setattr(release, "output", lambda *args, **kwargs: module)
    wheel = tmp_path / "leaked.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(module.removeprefix("src/"), path.read_bytes())
        archive.writestr(name, b"historical work queue\n")
    with pytest.raises(RuntimeError, match="working plan"):
        release.compare_wheel_source(tmp_path, wheel)


@pytest.mark.parametrize("name",sorted(source_policy.NESTED_WORK_PLAN_PATHS))
@pytest.mark.parametrize("kind",("regular","executable","symlink","directory","symlink-parent"))
def test_source_inventories_ignore_only_explicit_nonexecutable_regular_plans(tmp_path,name,kind):
    from empirical_lawhood.infrastructure.source_closure import _source_path_census
    from empirical_lawhood.infrastructure.numerical_provenance import numerical_package_sources

    package=tmp_path/"src/empirical_lawhood";package.mkdir(parents=True)
    (tmp_path/"scripts").mkdir()
    (package/"module.py").write_bytes(b"current source\n")
    other=package/"unclassified/frozen_specification.md";other.parent.mkdir();other.write_bytes(b"unclassified resource\n")
    plan=tmp_path/name;plan.parent.mkdir(parents=True)
    if kind=="directory":
        plan.mkdir()
    elif kind=="symlink":
        plan.symlink_to(package/"module.py")
    else:
        plan.write_bytes(b"archival instructions\n")
        if kind=="executable":plan.chmod(0o755)
        if kind=="symlink-parent":
            external=tmp_path/"external-owner";plan.parent.rename(external);plan.parent.symlink_to(external,target_is_directory=True)
    if kind=="regular":
        assert _source_path_census(tmp_path)=={"src/empirical_lawhood/module.py","src/empirical_lawhood/unclassified/frozen_specification.md"}
        assert dict(numerical_package_sources(package))=={"module.py":hashlib.sha256(b"current source\n").hexdigest(),
            "unclassified/frozen_specification.md":hashlib.sha256(b"unclassified resource\n").hexdigest()}
    else:
        with pytest.raises((source_policy.SourcePolicyError,ValueError),match="symbolic|regular non-executable"):
            _source_path_census(tmp_path)
        with pytest.raises(ValueError,match="symbolic|regular non-executable"):
            numerical_package_sources(package)


@pytest.mark.parametrize("defect", [None, "changed", "untracked", "symlink", "duplicate", "executable"])
def test_every_sdist_source_member_joins_its_committed_blob(tmp_path, monkeypatch, defect):
    name, payload = "unrelated.txt", b"incidental shipped prose\n"
    monkeypatch.setattr(evidence, "_selected_entries", lambda *args: {name: ("100644", blob(payload))})
    path = tmp_path / "selected.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("distribution/" + ("undeclared.py" if defect == "untracked" else name))
        raw = b"changed\n" if defect == "changed" else payload
        member.size = len(raw)
        member.mode = 0o755 if defect == "executable" else 0o664
        if defect == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "elsewhere"
            archive.addfile(member)
        else:
            archive.addfile(member, io.BytesIO(raw))
        if defect == "duplicate":
            archive.addfile(member, io.BytesIO(raw))
        add_source_metadata(archive)
    if defect:
        with pytest.raises(RuntimeError, match="source distribution"):
            release.compare_sdist_committed_source(tmp_path, path)
    else:
        assert release.compare_sdist_committed_source(tmp_path, path) == [
            {"path": name, "mode": "100644", "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}]


@pytest.mark.parametrize("defect", ("missing", "changed", "executable", "duplicate", "symlink"))
def test_generated_sdist_source_metadata_requires_exact_authenticated_bytes(tmp_path, monkeypatch, defect):
    monkeypatch.setattr(evidence, "_selected_entries", lambda *args: {})
    path = tmp_path / "metadata.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        root = tarfile.TarInfo("distribution")
        root.type = tarfile.DIRTYPE
        archive.addfile(root)
        if defect != "missing":
            raw = b"changed identity\n" if defect == "changed" else SOURCE_METADATA
            member = tarfile.TarInfo("distribution/empirical-lawhood-source.json")
            member.size = len(raw)
            member.mode = 0o755 if defect == "executable" else 0o644
            if defect == "symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = "foreign.json"
            archive.addfile(member, io.BytesIO(raw) if member.isfile() else None)
            if defect == "duplicate":
                archive.addfile(member, io.BytesIO(raw))
    with pytest.raises(RuntimeError, match="source distribution"):
        release.compare_sdist_committed_source(tmp_path, path)
