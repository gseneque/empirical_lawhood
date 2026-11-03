# SPDX-License-Identifier: MPL-2.0
"""Synthetic release failures retain terminal, independently hashed evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import threading
import tomllib

import pytest


@pytest.fixture
def release_runner(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/release_check.py"
    spec = importlib.util.spec_from_file_location("release_runner_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identity = {"commit": "synthetic", "tree_object": "synthetic-tree",
                "tree_inventory_sha256": "synthetic-inventory", "clean": True}
    monkeypatch.setattr(module, "source_identity", lambda root: identity)
    monkeypatch.setattr(module, "preserve_source_archive", lambda *args: {"synthetic_archive": True})
    monkeypatch.setattr(module, "output", lambda command, **kwargs: "synthetic uv")
    return module


def invoke(runner, monkeypatch, packet, child):
    monkeypatch.setattr(runner.subprocess, "run", child)
    monkeypatch.setattr(runner.sys, "argv", ["release_check.py", "--profile", "native-open",
                                            "--output-dir", str(packet), "--offline"])
    runner.main()


def read_packet(packet):
    manifest_bytes = (packet / "release-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    status = json.loads((packet / "release-status.json").read_bytes())
    assert status["manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
    assert status["software_status"] == manifest["status"]
    assert status["checks"] == manifest["checks"]
    assert status["scientific_qualification"]["status"] == "NOT_PERFORMED"
    for check in manifest["checks"]:
        if check.get("log") is not None:
            payload = (packet / check["log"]).read_bytes()
            assert check["sha256"] == hashlib.sha256(payload).hexdigest()
    return manifest


@pytest.mark.parametrize("error", [RuntimeError("child defect"), SystemExit(7), KeyboardInterrupt()])
def test_catchable_failure_is_terminal_and_propagates(release_runner, monkeypatch, tmp_path, error):
    count = 0

    def child(command, **kwargs):
        nonlocal count
        count += 1
        kwargs["stdout"].write(f"attempt {count}\n")
        kwargs["stdout"].flush()
        if count == 2:
            raise error
        return SimpleNamespace(returncode=0)

    packet = tmp_path / "packet"
    with pytest.raises(type(error)) as raised:
        invoke(release_runner, monkeypatch, packet, child)
    assert raised.value is error
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED"
    assert manifest["failure_type"] == type(error).__name__
    assert len(manifest["checks"]) == 2
    completed, attempted = manifest["checks"]
    assert completed["exit_code"] == 0
    assert attempted["disposition"] == "INTERRUPTED"
    assert attempted["exit_code"] is None
    assert (packet / attempted["log"]).read_bytes() == b"attempt 2\n"


def test_nonzero_child_exit_retains_observed_exit(release_runner, monkeypatch, tmp_path):
    def child(command, **kwargs):
        kwargs["stdout"].write("reported child failure\n")
        return SimpleNamespace(returncode=9)

    packet = tmp_path / "packet"
    with pytest.raises(RuntimeError, match="exit 9"):
        invoke(release_runner, monkeypatch, packet, child)
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED"
    assert manifest["checks"][0]["exit_code"] == 9
    assert manifest["checks"][0]["disposition"] == "FAILED"


@pytest.mark.parametrize("profile", ["native-open", "native-brian2"])
def test_gate_reuses_sole_checkout_and_seals_archive_before_fresh_environment(release_runner, monkeypatch, tmp_path, profile):
    packet = tmp_path / "packet"
    events = []

    def archive(root, destination, source):
        assert root == release_runner.ROOT and destination == packet
        events.append("verified-archive")
        return {"synthetic_archive": True}

    def child(command, **kwargs):
        assert events[0] == "verified-archive"
        assert "clone" not in command and "worktree" not in command
        assert kwargs["cwd"] in {release_runner.ROOT,
            release_runner.ROOT / "programmes/biology/cell-responses/workflows/neuron-current-response/native-env"}
        selected = Path(kwargs["env"]["UV_PROJECT_ENVIRONMENT"])
        assert selected.is_relative_to(packet / "environments")
        assert not selected.is_relative_to(release_runner.ROOT)
        assert Path(kwargs["env"]["TMPDIR"]).is_relative_to(packet / "environments")
        events.append(command)
        kwargs["stdout"].write("selected-source synthetic boundary\n")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(release_runner, "preserve_source_archive", archive)
    monkeypatch.setattr(release_runner.subprocess, "run", child)
    monkeypatch.setattr(release_runner.sys, "argv", ["release_check.py", "--profile", profile,
                                                    "--output-dir", str(packet)])
    release_runner.main()
    manifest = read_packet(packet)
    assert manifest["status"] == "PASSED" and manifest["source_archive"] == {"synthetic_archive": True}
    assert manifest["checkout"] == str(release_runner.ROOT)
    assert any(command[:2] == ["uv", "sync"] and "--locked" in command for command in events[1:])


def test_archive_failure_retains_terminal_packet_before_any_environment_contact(release_runner, monkeypatch, tmp_path):
    def refuse(*args):
        raise ValueError("source archive refused")

    monkeypatch.setattr(release_runner, "preserve_source_archive", refuse)
    packet = tmp_path / "packet"
    with pytest.raises(ValueError, match="source archive refused"):
        invoke(release_runner, monkeypatch, packet, lambda *a, **k: pytest.fail("unsealed source contacted child"))
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED" and manifest["checks"] == []


def test_source_stability_compares_selection_and_discloses_status_separately(release_runner):
    before = {"commit": "selected", "selected_inventory": [{"sha256": "1" * 64}],
              "checkout_disclosure": {"raw_status": "untracked plan"}}
    after = before | {"checkout_disclosure": {"raw_status": "untracked plan and unrelated prose"}}
    release_runner.require_stable_source(before, after)
    with pytest.raises(RuntimeError, match="source identity changed"):
        release_runner.require_stable_source(before, after | {"selected_inventory": [{"sha256": "2" * 64}]})


def test_final_identity_refusal_cannot_pass(release_runner, monkeypatch, tmp_path):
    count = 0
    original = release_runner.source_identity

    def identity(root):
        nonlocal count
        count += 1
        if count == 3:
            raise SystemExit("final source changed")
        return original(root)

    monkeypatch.setattr(release_runner, "source_identity", identity)

    def child(command, **kwargs):
        kwargs["stdout"].write("completed synthetic child\n")
        return SimpleNamespace(returncode=0)

    packet = tmp_path / "packet"
    with pytest.raises(SystemExit, match="final source changed"):
        invoke(release_runner, monkeypatch, packet, child)
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED"
    assert all(check["exit_code"] == 0 for check in manifest["checks"])


def test_interrupted_snapshot_survives_inherited_writer(release_runner, monkeypatch, tmp_path):
    allow_write = threading.Event()
    writer_done = threading.Event()
    thread = None

    def child(command, **kwargs):
        nonlocal thread
        stream = kwargs["stdout"]
        stream.write("observed prefix\n")
        stream.flush()
        descriptor = os.dup(stream.fileno())

        def writer():
            try:
                assert allow_write.wait(10)
                os.write(descriptor, b"later inherited output\n")
            finally:
                os.close(descriptor)
                writer_done.set()

        thread = threading.Thread(target=writer)
        thread.start()
        raise KeyboardInterrupt()

    packet = tmp_path / "packet"
    try:
        with pytest.raises(KeyboardInterrupt):
            invoke(release_runner, monkeypatch, packet, child)
        manifest = read_packet(packet)
        attempted = manifest["checks"][0]
        frozen = (packet / attempted["log"]).read_bytes()
        assert frozen == b"observed prefix\n"
        allow_write.set()
        assert writer_done.wait(10)
        assert (packet / attempted["log"]).read_bytes() == frozen
        assert (packet / attempted["unbound_live_log"]).read_bytes() == frozen + b"later inherited output\n"
        read_packet(packet)
    finally:
        allow_write.set()
        if thread is not None:
            thread.join(timeout=10)
            assert not thread.is_alive()


def test_initial_selected_source_refusal_creates_no_packet(release_runner, monkeypatch, tmp_path):
    def dirty(root):
        raise SystemExit("selected source differs")

    monkeypatch.setattr(release_runner, "source_identity", dirty)
    packet = tmp_path / "packet"
    with pytest.raises(SystemExit, match="selected source differs"):
        invoke(release_runner, monkeypatch, packet, lambda *args, **kwargs: pytest.fail("unexpected child"))
    assert not packet.exists()


def test_uv_prerequisite_interrupt_creates_no_unfinalized_packet(release_runner, monkeypatch, tmp_path):
    def unavailable(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(release_runner, "output", unavailable)
    packet = tmp_path / "packet"
    with pytest.raises(KeyboardInterrupt):
        invoke(release_runner, monkeypatch, packet, lambda *args, **kwargs: pytest.fail("unexpected child"))
    assert not packet.exists()


@pytest.mark.parametrize(("script", "check_name"), (
    ("scripts/generate_integration_examples.py", "generated-integration_examples"),
    ("scripts/generate_matrix_experiment_examples.py", "generated-matrix_experiment_examples"),
    ("scripts/check_frozen_rc_inputs.py", "frozen-rc-numerical-inputs"),
))
def test_source_drift_refuses_before_portable_suite(release_runner, monkeypatch, tmp_path, script, check_name):
    packet = tmp_path / "packet"
    monkeypatch.setattr(release_runner.sys, "argv", ["release_check.py", "--profile", "portable",
                                                    "--output-dir", str(packet)])

    def child(command, **kwargs):
        assert "pytest" not in command, "source drift must refuse before the expensive suite"
        drifted = script in command
        kwargs["stdout"].write("source input drift\n" if drifted else "synthetic preflight passed\n")
        return SimpleNamespace(returncode=1 if drifted else 0)

    monkeypatch.setattr(release_runner.subprocess, "run", child)
    with pytest.raises(RuntimeError, match=f"{check_name} failed"):
        release_runner.main()
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED"
    failed = manifest["checks"][-1]
    assert failed["name"] == check_name
    assert failed["exit_code"] == 1
    assert (packet / failed["log"]).read_text() == "source input drift\n"
    assert not any(check["name"] == "tests" for check in manifest["checks"])


@pytest.mark.parametrize("stage", ["packet", "logs", "temporary-files"])
@pytest.mark.parametrize("error", [RuntimeError("setup defect"), SystemExit(7), KeyboardInterrupt()])
def test_setup_failure_finalizes_created_packet(release_runner, monkeypatch, tmp_path, stage, error):
    packet = tmp_path / "packet"
    environment_root = tmp_path / "environments"
    original_mkdir = Path.mkdir

    def mkdir(path, *args, **kwargs):
        result = original_mkdir(path, *args, **kwargs)
        if path.name == stage:
            raise error
        return result

    monkeypatch.setattr(Path, "mkdir", mkdir)
    monkeypatch.setattr(release_runner.sys, "argv", ["release_check.py", "--profile", "native-open",
                                                    "--output-dir", str(packet),
                                                    "--environment-root", str(environment_root)])
    monkeypatch.setattr(release_runner.subprocess, "run", lambda *args, **kwargs: pytest.fail("unexpected child"))
    with pytest.raises(type(error)) as raised:
        release_runner.main()
    assert raised.value is error
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED"
    assert manifest["failure_type"] == type(error).__name__
    assert manifest["checks"] == []


@pytest.mark.parametrize("exit_code", [0, 9])
def test_completed_snapshot_survives_inherited_writer(release_runner, monkeypatch, tmp_path, exit_code):
    allow_write = threading.Event()
    thread = None
    count = 0

    def child(command, **kwargs):
        nonlocal thread, count
        count += 1
        stream = kwargs["stdout"]
        stream.write("observed completion\n")
        stream.flush()
        if count == 1:
            descriptor = os.dup(stream.fileno())

            def writer():
                try:
                    assert allow_write.wait(10)
                    os.write(descriptor, b"late descendant output\n")
                finally:
                    os.close(descriptor)

            thread = threading.Thread(target=writer)
            thread.start()
            return SimpleNamespace(returncode=exit_code)
        return SimpleNamespace(returncode=0)

    packet = tmp_path / "packet"
    try:
        if exit_code:
            with pytest.raises(RuntimeError, match="exit 9"):
                invoke(release_runner, monkeypatch, packet, child)
        else:
            invoke(release_runner, monkeypatch, packet, child)
        manifest = read_packet(packet)
        assert manifest["status"] == ("FAILED" if exit_code else "PASSED")
        completed = manifest["checks"][0]
        assert completed["exit_code"] == exit_code
        frozen = (packet / completed["log"]).read_bytes()
        assert frozen == b"observed completion\n"
        allow_write.set()
        thread.join(timeout=10)
        assert not thread.is_alive()
        assert (packet / completed["unbound_live_log"]).read_bytes() == frozen + b"late descendant output\n"
        read_packet(packet)
    finally:
        allow_write.set()
        if thread is not None:
            thread.join(timeout=10)
            assert not thread.is_alive()


def test_project_environment_checks_real_origin_and_version(release_runner, monkeypatch, tmp_path):
    real_run = subprocess.run
    environment_command = None

    def child(command, **kwargs):
        nonlocal environment_command
        if command[:4] == ["uv", "run", "--no-sync", "python"] and command[4] == "-c":
            environment_command = command[5]
        kwargs["stdout"].write("synthetic release orchestration\n")
        return SimpleNamespace(returncode=0)

    packet = tmp_path / "packet"
    invoke(release_runner, monkeypatch, packet, child)
    assert read_packet(packet)["status"] == "PASSED"
    assert environment_command is not None
    root = Path(__file__).resolve().parents[1]
    good = real_run([sys.executable, "-c", environment_command], cwd=root,
                    capture_output=True, text=True, timeout=30)
    assert good.returncode == 0, good.stderr
    evidence = json.loads(good.stdout)
    assert Path(evidence["package_origin"]).resolve() == root / "src/empirical_lawhood/__init__.py"
    selected_version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    assert evidence["selected_version"] == selected_version
    wrong_version = environment_command.replace(f"selected={selected_version!r}", "selected='0.0.0'")
    assert wrong_version != environment_command
    bad = real_run([sys.executable, "-c", wrong_version], cwd=root,
                   capture_output=True, text=True, timeout=30)
    assert bad.returncode != 0
    assert "source/module/distribution version mismatch" in bad.stderr


@pytest.mark.parametrize("target", ["packet", "environment"])
@pytest.mark.parametrize("alias", ["symlink", "traversal"])
def test_release_destinations_refuse_aliases_before_child_effects(release_runner, monkeypatch, tmp_path, target, alias):
    if alias == "symlink":
        parent = tmp_path / "alias"
        parent.symlink_to(release_runner.ROOT, target_is_directory=True)
        selected = parent / "must-not-exist"
    else:
        selected = tmp_path / "never-created" / ".." / "must-not-exist"
    packet = selected if target == "packet" else tmp_path / "ordinary-packet"
    args = ["release_check.py", "--profile", "native-open", "--output-dir", str(packet)]
    if target == "environment":
        args += ["--environment-root", str(selected)]
    monkeypatch.setattr(release_runner.sys, "argv", args)
    monkeypatch.setattr(release_runner.subprocess, "run", lambda *a, **k: pytest.fail("invalid destination contacted a child"))
    with pytest.raises(SystemExit, match="outside"):
        release_runner.main()
    assert not packet.exists() and not (tmp_path / "never-created").exists()


def test_sdist_researcher_closure_checks_exact_guides_inputs_and_excludes_plans(release_runner, monkeypatch, tmp_path):
    import io
    import tarfile

    checkout = tmp_path / "checkout"
    from empirical_lawhood.infrastructure.source_policy import ROOT_WORK_PLAN_NAMES, DOCUMENT_WORK_PLAN_PATHS

    names = ("README.md", "docs/development/architecture.md", "programmes/foundations/example/records/current-science.md",
             "programmes/materials/superconductivity/workflows/recursive-materials/materials-partial.json")
    for name in names:
        path = checkout / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((name + "\n").encode())
    monkeypatch.setattr(release_runner, "output", lambda *args, **kwargs: "\n".join(names))

    def export(target, *, changed=None, extra=None):
        with tarfile.open(target, "w:gz") as archive:
            for name in (*names, *((extra,) if extra else ())):
                raw = b"altered" if name == changed else ((name + "\n").encode())
                member = tarfile.TarInfo("source-0.6.0/" + name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))

    good = tmp_path / "good.tar.gz"
    export(good)
    assert [row["path"] for row in release_runner.compare_sdist_researcher_inputs(checkout, good)] == sorted(names)
    changed = tmp_path / "changed.tar.gz"
    export(changed, changed=names[-1])
    with pytest.raises(RuntimeError, match="researcher inputs differ"):
        release_runner.compare_sdist_researcher_inputs(checkout, changed)
    for ordinal, name in enumerate(("FINALISEARCH.md", "docs/plans/preserved.md",
                                    *sorted(ROOT_WORK_PLAN_NAMES | DOCUMENT_WORK_PLAN_PATHS))):
        leaked = tmp_path / f"leaked-{ordinal}.tar.gz"
        export(leaked, extra=name)
        with pytest.raises(RuntimeError, match="working plan"):
            release_runner.compare_sdist_researcher_inputs(checkout, leaked)


def test_historical_matrix_recovery_is_not_a_release_profile(release_runner):
    assert "held-matrix-retained" not in release_runner.PROFILES
    assert all("test_matrix_e3_public_retained_recovery.py" not in selector
               for _, selection in release_runner.PROFILES.values() for selector in selection)
    assert release_runner.PROFILES["portable"][1] == ["tests", "-m", "not native and not held"]


@pytest.mark.parametrize("profile", ("portable", "native-open"))
def test_release_keeps_passed_and_failed_fixture_evidence_in_its_packet(
        release_runner, monkeypatch, tmp_path, profile):
    """Actual isolated pytest bodies survive both outcomes; no native source is contacted."""
    packet = tmp_path / "packet"
    fixture_file = tmp_path / "retention_control.py"
    fixture_file.write_text(
        "def test_passing_contact(tmp_path):\n"
        "    (tmp_path / 'contact.json').write_text('passed-evidence')\n\n"
        "def test_failed_contact(tmp_path):\n"
        "    (tmp_path / 'contact.json').write_text('failed-evidence')\n"
        "    assert False, 'deliberately retained control failure'\n",
        encoding="utf-8")
    actual_run = subprocess.run
    selections = []

    def child(command, **kwargs):
        if "pytest" not in command:
            kwargs["stdout"].write("synthetic non-test release boundary\n")
            return SimpleNamespace(returncode=0)
        selections.append(tuple(command))
        # Preserve the actual runner's selected pytest storage/retention options.
        # Replace only its scientific suite with two disclosed byte-only controls.
        options = []
        for index, item in enumerate(command):
            if item in ("--basetemp", "-o"):
                options.extend((item, command[index + 1]))
        environment = dict(kwargs["env"], PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        environment.pop("PYTEST_ADDOPTS", None)
        environment.pop("PYTEST_PLUGINS", None)
        return actual_run(
            [sys.executable, "-B", "-m", "pytest", "-q", "--noconftest",
             "-p", "no:cacheprovider", *options, str(fixture_file)],
            cwd=packet, env=environment, stdout=kwargs["stdout"],
            stderr=subprocess.STDOUT, text=True)

    monkeypatch.setattr(release_runner.subprocess, "run", child)
    monkeypatch.setattr(release_runner.sys, "argv",
        ["release_check.py", "--profile", profile, "--output-dir", str(packet)])
    with pytest.raises(RuntimeError, match="tests failed"):
        release_runner.main()
    assert len(selections) == 1
    retained = {path.read_text() for path in (packet / "test-artifacts").rglob("contact.json")}
    assert retained == {"passed-evidence", "failed-evidence"}
    manifest = read_packet(packet)
    assert manifest["status"] == "FAILED"
    assert manifest["test_environment_policy"] == {
        "basetemp": str(packet / "test-artifacts"),
        "tmp_path_retention_policy": "all", "tmp_path_retention_count": 1}
    assert next(row for row in manifest["checks"] if row["name"] == "tests")["exit_code"] == 1


def test_portable_partitions_and_module_shards_preserve_the_complete_census():
    from scripts import test_profiles as profiles

    ci = sorted(profiles.CI_FILES)[0]
    scale = sorted(profiles.SCALE_FILES)[0]
    nodeids = [f"{ci}::test_contract", f"{scale}::test_scale[a]", f"{scale}::test_scale[b]",
               "tests/test_new_workflow.py::test_case[a]", "tests/test_new_workflow.py::test_case[b]",
               "tests/test_other_workflow.py::test_case"]
    partitions = [profiles.selection_record(nodeids, name) for name in profiles.PARTITION_PROFILES]
    selections = [set(record["selected_nodeids"]) for record in partitions]
    assert set.union(*selections) == set(nodeids)
    assert sum(map(len, selections)) == len(nodeids)
    assert profiles.profile_for("tests/test_new_module.py::test_future") == "integration"
    for name in ("integration", "scale"):
        records = [profiles.selection_record(nodeids, name, index, 4) for index in range(4)]
        sharded = [node for record in records for node in record["selected_nodeids"]]
        assert set(sharded) == {node for node in nodeids if profiles.profile_for(node) == name}
        assert len(sharded) == len(set(sharded))
        for module in {node.split("::")[0] for node in sharded}:
            assert sum(any(node.startswith(module + "::") for node in record["selected_nodeids"])
                       for record in records) == 1
        assert profiles.selection_record(list(reversed(nodeids)), name, 1, 4) == records[1]


def test_test_profile_refuses_invalid_shards_and_missing_or_overlapping_declarations(monkeypatch, tmp_path):
    from scripts import test_profiles as profiles

    for name, index, count in (("ci", 1, 2), ("portable", 0, 2), ("integration", -1, 2),
                               ("scale", 2, 2), ("scale", 0, 0), ("integration", False, 1)):
        with pytest.raises(ValueError, match="shard"):
            profiles.validate_shard(name, index, count)
    with pytest.raises(ValueError, match="unknown"):
        profiles.selection_record([], "typo")
    with pytest.raises(ValueError, match="duplicate"):
        profiles.selection_record(["test.py::test_a"] * 2, "ci")
    monkeypatch.setattr(profiles, "CI_FILES", frozenset({"tests/test_missing.py"}))
    monkeypatch.setattr(profiles, "SCALE_FILES", frozenset())
    with pytest.raises(ValueError, match="missing modules"):
        profiles.validate_declarations(tmp_path)
    monkeypatch.setattr(profiles, "SCALE_FILES", profiles.CI_FILES)
    with pytest.raises(ValueError, match="overlap"):
        profiles.validate_declarations(tmp_path)


def test_portable_partition_hook_excludes_native_and_held_after_marker_selection(tmp_path):
    """Actual collection verifies plugin ordering without executing any fixture."""
    from scripts import test_profiles as profiles

    root = tmp_path / "partition-fixture"
    root.mkdir()
    (root / "tests").mkdir()
    module = root / "tests/test_bounded.py"
    module.write_text("import pytest\n"
                      "def test_bounded(): raise AssertionError('collection only')\n"
                      "@pytest.mark.native\ndef test_native(): pass\n"
                      "@pytest.mark.held\ndef test_held(): pass\n")
    (root / "conftest.py").write_text(
        "import profile_fixture\n"
        "profile_fixture.CI_FILES = frozenset({'tests/test_bounded.py'})\n"
        "profile_fixture.SCALE_FILES = frozenset()\n")
    (root / "profile_fixture.py").write_bytes(Path(profiles.__file__).read_bytes())
    census = root / "selection.json"
    command = [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q", "-p", "profile_fixture",
               "tests", "-m", "not native and not held", "--test-profile", "ci",
               "--test-selection-output", str(census), "-p", "no:cacheprovider"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                            env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS=""))
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(census.read_text())
    assert record["selected_nodeids"] == ["tests/test_bounded.py::test_bounded"]
    assert record["eligible_collected_cases"] == 1
    # A filtered invocation cannot masquerade as the complete partition census.
    result = subprocess.run([*command, "-k", "bounded"], cwd=root, capture_output=True, text=True,
                            env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS=""))
    assert result.returncode != 0 and "without -k" in result.stderr


@pytest.mark.parametrize("profile", ("ci", "integration", "scale"))
def test_partitioned_release_retains_failed_selection_and_does_not_run_coverage(
        release_runner, monkeypatch, tmp_path, profile):
    packet = tmp_path / "packet"
    commands = []

    def child(command, **kwargs):
        commands.append(command)
        kwargs["stdout"].write("synthetic profile control\n")
        if "--test-selection-output" in command:
            census = Path(command[command.index("--test-selection-output") + 1])
            census.write_text('{"selected_cases": 1}\n')
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(release_runner.subprocess, "run", child)
    index, count = (0, 1) if profile == "ci" else (2, 4)
    monkeypatch.setattr(release_runner.sys, "argv", ["release_check.py", "--profile", profile,
        "--shard-index", str(index), "--shard-count", str(count), "--output-dir", str(packet)])
    with pytest.raises(RuntimeError, match="tests failed"):
        release_runner.main()
    manifest = read_packet(packet)
    assert manifest["test_shard"] == {"index": index, "count": count}
    assert manifest["test_selection"]["sha256"] == hashlib.sha256((packet / "test-selection.json").read_bytes()).hexdigest()
    assert not any("coverage" in command or command[:2] == ["uv", "build"] for command in commands)
    if profile == "ci":
        assert "no complete portable coverage claim" in manifest["software_scope"]
        assert any("scripts/check_documentation.py" in command for command in commands)
    else:
        assert "no distribution build or complete coverage claim" in manifest["software_scope"]
