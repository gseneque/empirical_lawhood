# SPDX-License-Identifier: MPL-2.0
"""Build ordinary distribution source metadata, without importing native code."""

from hashlib import sha1, sha256
from io import BytesIO
import json
import os
from pathlib import Path
import runpy
import stat
import tarfile

SOURCE_METADATA_FILENAME = "empirical-lawhood-source.json"


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"


def build_source_metadata(root):
    root = Path(root).resolve(strict=True)
    retained = root / SOURCE_METADATA_FILENAME
    excluded = runpy.run_path(str(root / "src/empirical_lawhood/infrastructure/source_policy.py"))["is_work_plan_path"]
    checkout = (root / ".git").exists()
    if retained.exists() and checkout:
        raise ValueError("a checkout cannot replace its current committed identity with retained sdist metadata")
    if retained.exists():
        if retained.is_symlink() or not retained.is_file() or retained.stat().st_size > 8 * 1024**2:
            raise ValueError("distribution source metadata must be a regular file")
        raw = retained.read_bytes()
        document = json.loads(raw)
        if encode(document) != raw:
            raise ValueError("distribution source metadata is not canonical")
    else:
        command_owner = runpy.run_path(str(root / "src/empirical_lawhood/infrastructure/bounded_process.py"))
        def git(*args):
            environment = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
            environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                GIT_CONFIG_SYSTEM=os.devnull, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
            result = command_owner["run_bounded_command"](("git", *args), cwd=root,
                environment=environment, timeout_seconds=60,
                maximum_stdout_bytes=256 * 1024**2, maximum_stderr_bytes=64 * 1024)
            if result.returncode:
                raise ValueError("committed build source observation failed")
            return result.stdout

        if Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
            raise ValueError("build requires its committed source root or retained sdist metadata")
        tree = git("ls-tree", "-r", "-z", "--full-tree", "HEAD")
        entries = {}
        for entry in tree.split(b"\0"):
            if not entry:
                continue
            header, path = entry.split(b"\t", 1)
            mode, kind, blob = header.decode().split(" ")
            name = path.decode()
            if excluded(name):
                continue
            if kind != "blob" or mode not in ("100644", "100755"):
                raise ValueError("distribution source requires regular committed members")
            entries[name] = (mode, blob)
        archive = git("archive", "HEAD")
        rows = []
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as source:
            for member in source:
                if member.isdir() or excluded(member.name):
                    continue
                if not member.isfile() or member.name not in entries:
                    raise ValueError("source archive changes its regular committed membership")
                mode, blob = entries.pop(member.name)
                stream = source.extractfile(member)
                if stream is None:
                    raise ValueError("source archive member has no bytes")
                data = stream.read()
                if sha1(f"blob {len(data)}\0".encode() + data).hexdigest() != blob:
                    raise ValueError("source archive member differs from its committed blob")
                rows.append({"relative_path": member.name, "mode": mode, "size_bytes": len(data), "sha256": sha256(data).hexdigest()})
        if entries:
            raise ValueError("source archive omits committed members")
        document = {
            "schema": "empirical-lawhood/build/source", "version": "1.0.0",
            "implementation_commit": git("rev-parse", "HEAD").decode().strip(),
            "implementation_sha256": sha256(archive).hexdigest(),
            "source_tree_sha256": sha256(tree).hexdigest(),
            "tracked_files": sorted(rows, key=lambda row: row["relative_path"]),
        }
        raw = encode(document)
    if (type(document) is not dict or set(document) != {"schema", "version", "implementation_commit",
            "implementation_sha256", "source_tree_sha256", "tracked_files"}
            or document["schema"] != "empirical-lawhood/build/source" or document["version"] != "1.0.0"
            or type(document["tracked_files"]) is not list or not document["tracked_files"]):
        raise ValueError("distribution source metadata changes its contract")
    previous = ""
    for key, length in (("implementation_commit", 40), ("implementation_sha256", 64), ("source_tree_sha256", 64)):
        value = document[key]
        if type(value) is not str or len(value) != length or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("distribution source metadata omits its exact source identity")
    for row in document["tracked_files"]:
        if type(row) is not dict or set(row) != {"relative_path", "mode", "size_bytes", "sha256"}:
            raise ValueError("distribution source member changes its contract")
        name = row["relative_path"]
        if (type(name) is not str or name.startswith("/") or "\\" in name
                or any(part in ("", ".", "..") for part in name.split("/")) or name <= previous
                or row["mode"] not in ("100644", "100755") or type(row["size_bytes"]) is not int
                or row["size_bytes"] < 0 or type(row["sha256"]) is not str
                or len(row["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["sha256"])):
            raise ValueError("distribution source member is not unique, regular and bounded")
        previous = name
    expected_paths = {row["relative_path"] for row in document["tracked_files"]
        if row["relative_path"].startswith(("src/empirical_lawhood/", "scripts/"))}
    actual_paths = set()
    for directory in (root / "src/empirical_lawhood", root / "scripts"):
        for path in directory.rglob("*"):
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
                continue
            name = relative.as_posix()
            mode = path.lstat().st_mode
            if path.is_symlink():
                raise ValueError("distribution build source refuses symbolic members")
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise ValueError("distribution build source requires regular members")
            if excluded(name):
                if mode & 0o111:
                    raise ValueError("excluded work plans must be nonexecutable")
                continue
            actual_paths.add(name)
    if expected_paths != actual_paths:
        raise ValueError("distribution build source changes its complete executable census")
    # Rebuilding an sdist needs no Git. Every member that affects execution or
    # the build must still match the retained source identity before packaging.
    for row in document["tracked_files"]:
        name = row["relative_path"]
        if not (name.startswith(("src/empirical_lawhood/", "scripts/")) or name in ("pyproject.toml", "uv.lock")):
            continue
        path = root / name
        metadata = path.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or path.resolve(strict=True) != path
                or metadata.st_mode & 0o7000
                or (row["mode"] == "100644" and metadata.st_mode & 0o111)
                or (row["mode"] == "100755" and not metadata.st_mode & stat.S_IXUSR)):
            raise ValueError("distribution build source changed a regular member: " + name)
        data = path.read_bytes()
        if len(data) != row["size_bytes"] or sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("distribution build source differs from its committed identity: " + name)
    if checkout and git("rev-parse", "HEAD").decode().strip() != document["implementation_commit"]:
        raise ValueError("committed build source changed during packaging")
    return raw
