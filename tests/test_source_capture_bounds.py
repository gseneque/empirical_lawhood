# SPDX-License-Identifier: MPL-2.0
"""Bounded Git capture preserves exact bytes and managed process-group cleanup."""

from hashlib import sha1, sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tarfile
import tracemalloc

import pytest

from empirical_lawhood.execution.local import bounded_process
from empirical_lawhood.storage import source_closure
from tests.test_source_origin import ROOT


def _capture(argv, *, streamed=False, **kwargs):
    if not streamed:
        return bounded_process.run_bounded_command(argv, **kwargs)
    def consume(reader):
        rows = []
        while chunk := reader.read(1024):
            rows.append(chunk)
        return b"".join(rows)
    result = bounded_process.run_bounded_stream_command(argv, consume_stdout=consume, **kwargs)
    return bounded_process.BoundedProcessResult(result.returncode, result.output, result.stderr)


@pytest.mark.parametrize("streamed", (False, True))
@pytest.mark.parametrize("size", (8, 9))
def test_stdout_ceiling_is_enforced_while_capturing(size, streamed):
    command = [sys.executable, "-c", f"import os; os.write(1,b'x'*{size})"]
    if size == 8:
        result = _capture(command, streamed=streamed, maximum_stdout_bytes=8)
        assert result.stdout == b"x" * 8
    else:
        with pytest.raises(bounded_process.BoundedProcessError, match="stdout.*byte ceiling"):
            _capture(command, streamed=streamed, maximum_stdout_bytes=8)


@pytest.mark.parametrize("streamed", (False, True))
def test_stderr_ceiling_and_nonzero_exit_are_separate(streamed):
    command = [sys.executable, "-c", "import os; os.write(2,b'error'); raise SystemExit(7)"]
    result = _capture(command, streamed=streamed, maximum_stderr_bytes=5)
    assert result.returncode == 7 and result.stderr == b"error"
    with pytest.raises(bounded_process.BoundedProcessError, match="stderr.*byte ceiling"):
        _capture(command, streamed=streamed, maximum_stderr_bytes=4)


def _still_running(pid):
    try:
        status = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return False
    # A terminated orphan may remain a zombie until its host init reaps it.
    return status[status.rfind(")") + 2:].split()[0] != "Z"


@pytest.mark.parametrize("streamed", (False, True))
@pytest.mark.parametrize("failure", ("timeout", "overflow", "interrupt", "success"))
def test_managed_group_descendants_stop_and_direct_child_is_reaped(tmp_path, monkeypatch, failure, streamed):
    pid_file = tmp_path / "descendant.pid"
    program = '''
import os, subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                         stdout=subprocess.DEVNULL if sys.argv[2] == "success" else None,
                         stderr=subprocess.DEVNULL if sys.argv[2] == "success" else None)
Path(sys.argv[1]).write_text(str(child.pid))
os.write(1, b"ready")
if sys.argv[2] == "overflow":
    os.write(1, b"x" * 1024)
if sys.argv[2] == "success":
    sys.exit(0)
time.sleep(30)
'''
    children = []
    real_popen = subprocess.Popen

    def popen(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(bounded_process.subprocess, "Popen", popen)
    if failure == "interrupt":
        real_read = os.read

        def interrupted_read(fd, size):
            if pid_file.exists():
                raise KeyboardInterrupt("synthetic capture interruption")
            return real_read(fd, size)

        monkeypatch.setattr(bounded_process.os, "read", interrupted_read)
    command = [sys.executable, "-c", program, str(pid_file), failure]
    try:
        if failure == "success":
            result = _capture(command, streamed=streamed, timeout_seconds=5, maximum_stdout_bytes=8)
            assert result.returncode == 0 and result.stdout == b"ready"
        else:
            expected = KeyboardInterrupt if failure == "interrupt" else bounded_process.BoundedProcessError
            with pytest.raises(expected):
                _capture(command, streamed=streamed, timeout_seconds=1, maximum_stdout_bytes=8)
        assert len(children) == 1 and children[0].returncode is not None
        assert all(stream.closed for stream in (children[0].stdin, children[0].stdout, children[0].stderr))
        assert pid_file.exists(), "descendant must actually start before the failure"
        pid = int(pid_file.read_text())
        deadline = time.monotonic() + 1
        while _still_running(pid) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not _still_running(pid)
    finally:
        # Cleanup is limited to the disposable group created by this test,
        # including on a future regression in the production helper.
        for child in children:
            bounded_process._kill_process_tree(child)


def test_git_operations_match_original_bytes_for_same_commit(tmp_path):
    repo = tmp_path / "small-source"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    (repo / "member.txt").write_bytes(b"exact original bytes\n")
    subprocess.run(["git", "-C", str(repo), "add", "member.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Synthetic fixture", "-c",
                    "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "Synthetic source"], check=True)
    for arguments in (("rev-parse", "HEAD"), ("status", "--porcelain=v1", "--untracked-files=all"),
                      ("ls-tree", "-r", "-z", "--full-tree", "HEAD"), ("archive", "HEAD")):
        original = subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True, timeout=60).stdout
        assert source_closure._git(repo, *arguments) == original
    tree = subprocess.check_output(["git", "ls-tree", "-r", "-z", "--full-tree", "HEAD"], cwd=repo)
    archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=repo)
    members, digest = source_closure._git_archive_census(repo, tree)
    assert members == source_closure._stream_archive_census(tree, BytesIO(archive))[0]
    assert digest == source_closure._git_archive_digest(repo) == sha256(archive).hexdigest()


def test_git_capture_bound_failures_are_handled_source_refusals(tmp_path, monkeypatch):
    calls = []

    def bounded(argv, **kwargs):
        calls.append((argv, kwargs))
        raise bounded_process.BoundedProcessError("bounded local command stdout exceeds its byte ceiling")

    monkeypatch.setattr(source_closure, "run_bounded_command", bounded)
    with pytest.raises(PermissionError, match="target source capture failed.*byte ceiling"):
        source_closure._git(tmp_path, "archive", "HEAD")
    assert calls[0][0] == ("git", "archive", "HEAD")
    assert calls[0][1]["maximum_stdout_bytes"] is None
    assert calls[0][1]["maximum_stderr_bytes"] == 64 * 1024
    assert calls[0][1]["timeout_seconds"] == 60


def test_nonzero_git_exit_is_handled_source_refusal(tmp_path):
    with pytest.raises(PermissionError, match="target source capture failed"):
        source_closure._git(tmp_path, "archive", "HEAD")


def test_complete_selected_capture_checks_actual_executing_package_without_copy(tmp_path):
    repo = ROOT
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    tree = sha256(subprocess.check_output(["git", "-C", str(repo), "ls-tree", "-r", "-z", "--full-tree", "HEAD"])).hexdigest()
    original_archive = subprocess.check_output(["git", "-C", str(repo), "archive", "HEAD"])
    program = '''
from pathlib import Path
import json, sys
from empirical_lawhood.storage.source_closure import capture_target_closure
from empirical_lawhood.storage.source_origin import require_executing_target_source
root = Path(sys.argv[1]); require_executing_target_source(root)
captured = capture_target_closure(root, "synthetic.capture")
closure = captured.closure
from empirical_lawhood.storage.study_issue import GitStudySourceClosureInspector
assert GitStudySourceClosureInspector(root).observe(closure) == closure
print(json.dumps({"commit":closure.implementation_commit,
                  "archive":closure.implementation_sha256,"tree":closure.source_tree_sha256}))
'''
    result = subprocess.run([sys.executable, "-c", program, str(repo)], cwd=tmp_path,
                            env=dict(os.environ, PYTHONPATH=str(repo / "src"), PYTHONDONTWRITEBYTECODE="1"),
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"commit": commit, "archive": sha256(original_archive).hexdigest(), "tree": tree}


def test_early_stream_consumer_still_accounts_for_trailing_bytes_and_process_failure():
    size = 3 * bounded_process.PROCESS_IO_CHUNK_BYTES
    command = [sys.executable, "-c", f"import os; os.write(1,b'x'*{size}); os.write(2,b'late'); raise SystemExit(7)"]
    result = bounded_process.run_bounded_stream_command(command, consume_stdout=lambda reader: reader.read(1),
        maximum_stdout_bytes=size, maximum_stderr_bytes=4)
    assert result.output == b"x" and result.stdout_bytes == size
    assert result.returncode == 7 and result.stderr == b"late"
    with pytest.raises(bounded_process.BoundedProcessError, match="stdout.*byte ceiling"):
        bounded_process.run_bounded_stream_command(command, consume_stdout=lambda reader: reader.read(1),
            maximum_stdout_bytes=size - 1, maximum_stderr_bytes=4)


def test_streamed_archive_hash_includes_all_trailing_bytes_and_refuses_truncation():
    from tests.test_local_plan_source_policy import _archive
    tree, archive = _archive({"source.py": b"original"})
    for trailer in (b"", b"retained trailing bytes" * 4000):
        members, digest = source_closure._stream_archive_census(tree, BytesIO(archive + trailer))
        assert digest == sha256(archive + trailer).hexdigest()
        assert members == source_closure._stream_archive_census(tree, BytesIO(archive))[0]
    # Header, body and padding occupy 1024 bytes. No/partial end markers refuse.
    for truncated in (archive[:515], archive[:1024], archive[:1536], archive[:1537]):
        with pytest.raises(source_closure.SourcePolicyError, match="truncated|truncates|malformed"):
            source_closure._stream_archive_census(tree, BytesIO(truncated))


@pytest.mark.parametrize("kind", (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME,
                                  tarfile.GNUTYPE_LONGLINK, tarfile.GNUTYPE_SPARSE))
def test_extended_or_sparse_header_refuses_before_large_payload_allocation(kind):
    member = tarfile.TarInfo("source.py")
    member.type, member.size = kind, source_closure._MAX_ARCHIVE_HEADER_BYTES + 1
    raw = member.tobuf(format=tarfile.GNU_FORMAT)
    digest = sha1(b"blob 0\0").hexdigest()
    tree = f"100644 blob {digest}\tsource.py\0".encode()
    with pytest.raises(source_closure.SourcePolicyError, match="metadata|unsupported"):
        source_closure._stream_archive_census(tree, BytesIO(raw))


@pytest.mark.parametrize("size", (1024**2, 12 * 1024**2))
def test_streamed_archive_heap_does_not_retain_a_member_body_or_archive(tmp_path, size, record_property):
    body = tmp_path / "large-source.bin"
    block = bytes(range(256)) * 256
    blob = sha1(b"blob " + str(size).encode() + b"\0")
    content = sha256()
    with body.open("xb") as stream:
        for _ in range(size // len(block)):
            stream.write(block)
            blob.update(block)
            content.update(block)
    archive = tmp_path / "source.tar"
    with tarfile.open(archive, "w:") as packet:
        member = tarfile.TarInfo("large-source.bin")
        member.mode, member.size = 0o644, size
        with body.open("rb") as stream:
            packet.addfile(member, stream)
    tree = f"100644 blob {blob.hexdigest()}\tlarge-source.bin\0".encode()
    expected = sha256()
    with archive.open("rb") as stream:
        while chunk := stream.read(65536):
            expected.update(chunk)
    tracemalloc.start()
    try:
        with archive.open("rb") as stream:
            members, digest = source_closure._stream_archive_census(tree, stream)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    record_property("member_body_bytes", size)
    record_property("parser_heap_peak_bytes", peak)
    assert digest == expected.hexdigest()
    assert members == (source_closure.TrackedSourceMember("large-source.bin", "100644", size, content.hexdigest()),)
    assert peak < 1024**2 < size + 1


def test_complete_streamed_git_census_still_refuses_nonzero_exit(tmp_path, monkeypatch):
    from tests.test_local_plan_source_policy import _archive
    tree, archive = _archive({"source.py": b"original"})

    def failed(argv, *, consume_stdout, **kwargs):
        output = consume_stdout(BytesIO(archive))
        return bounded_process.BoundedProcessStreamResult(7, output, b"late failure", len(archive))

    monkeypatch.setattr(source_closure, "run_bounded_stream_command", failed)
    with pytest.raises(PermissionError, match="target source capture failed: late failure"):
        source_closure._git_archive_census(tmp_path, tree)
