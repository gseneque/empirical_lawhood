# SPDX-License-Identifier: MPL-2.0
"""Current-tree release custody excludes ancestor objects and work plans."""

from hashlib import sha256
import io
import subprocess
import tarfile

import pytest

from scripts import release_check as owner
from empirical_lawhood.infrastructure.source_closure import _archive_census


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)


def commit(root, message):
    git(root, "add", "-A")
    git(root, "-c", "user.name=Software fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", message)


def source_identity(root):
    tree = git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
    archive = git(root, "archive", "HEAD")
    return {"commit": git(root, "rev-parse", "HEAD").decode().strip(),
        "tree_inventory_sha256": sha256(tree).hexdigest(), "archive_sha256": sha256(archive).hexdigest(),
        "tracked_files": [row.to_mapping() for row in _archive_census(tree, archive)]}


@pytest.fixture
def archive_case(tmp_path):
    root = tmp_path / "synthetic-source"
    root.mkdir()
    git(root, "init", "--template=")
    (root / "WTF.md").write_bytes(b"ANCESTOR_ONLY_OPERATIONAL_PLAN_DATA\n")
    (root / "module.py").write_bytes(b"VALUE = 1\n")
    commit(root, "ancestor with a local plan")
    (root / "WTF.md").unlink()
    (root / "module.py").write_bytes(b"VALUE = 2\n")
    commit(root, "current candidate excludes plans")
    packet = tmp_path / "release-packet"
    packet.mkdir()
    return root, packet


def test_release_retains_exact_current_archive_without_git_history_or_ancestor_plans(archive_case):
    root, packet = archive_case
    selected = source_identity(root)
    result = owner.preserve_source_archive(root, packet, selected)
    payload = (packet / result["path"]).read_bytes()
    assert payload == git(root, "archive", "HEAD")
    assert result["sha256"] == selected["archive_sha256"] == sha256(payload).hexdigest()
    assert result["scientific_authority"] == "NONE" and result["member_count"] == 1
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        assert archive.getnames() == ["module.py"]
        assert archive.extractfile("module.py").read() == b"VALUE = 2\n"
    assert b"ANCESTOR_ONLY_OPERATIONAL_PLAN_DATA" not in payload
    assert not list(packet.rglob("*.bundle")) and not list(packet.rglob("objects"))


@pytest.mark.parametrize("name", ("WTF.md", "WTF-FINALDESIGN.md", "WTF-OPTIMPRIO.md", "docs/plans/old.md", "PROREVIEW/review.md", "docs/applied-el-handoff.md",
    "src/empirical_lawhood/adapters/methods/preparation_applicability/frozen_specification.md"))
def test_even_committed_work_plan_is_refused_before_archive_publication(archive_case, name):
    root, packet = archive_case
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"operational instructions\n")
    commit(root, "forbidden plan leak fixture")
    with pytest.raises(RuntimeError, match="working plan"):
        owner.preserve_source_archive(root, packet, source_identity(root))
    assert not list(packet.iterdir())


@pytest.mark.parametrize("field", ("commit", "tree_inventory_sha256", "archive_sha256", "tracked_files"))
def test_release_archive_must_match_all_admitted_source_identity_fields(archive_case, field):
    root, packet = archive_case
    source = source_identity(root)
    source[field] = [] if field == "tracked_files" else "f" * len(source[field])
    with pytest.raises(RuntimeError, match="admitted"):
        owner.preserve_source_archive(root, packet, source)
    assert not list(packet.iterdir())


def test_current_archive_packet_is_never_overwritten(archive_case):
    root, packet = archive_case
    source = source_identity(root)
    owner.preserve_source_archive(root, packet, source)
    before = (packet / "source.tar").read_bytes()
    with pytest.raises(FileExistsError):
        owner.preserve_source_archive(root, packet, source)
    assert (packet / "source.tar").read_bytes() == before
