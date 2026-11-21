# SPDX-License-Identifier: MPL-2.0
"""Restore a versioned native closure without modifying retained source custody."""

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import tempfile

from empirical_lawhood.storage.atomic_files import rename_noreplace
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_census import FileHashCensus


SCHEMA = "empirical-lawhood/native-installation-manifest"


def load_manifest(path, *, expected_sha256=None):
    raw = read_bounded_bytes(real_path(path), maximum_bytes=None)
    digest = sha256(raw).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("native installation manifest differs from the selected digest")
    document = json.loads(raw)
    if document.get("schema") != SCHEMA or document.get("version") != "1.0.0":
        raise ValueError("unsupported native installation manifest")
    if document.get("platform") != "linux-x86_64" or (platform.system(), platform.machine()) != ("Linux", "x86_64"):
        raise ValueError("native closure requires its selected Linux x86-64 platform")
    rows = document.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("native closure requires a complete nonempty file census")
    names = []
    for row in rows:
        name = row["path"]
        if not isinstance(name, str) or not name or name == ".":
            raise ValueError("native closure contains an unsafe member path")
        parts = PurePosixPath(name)
        if (parts.is_absolute()
                or parts.as_posix() != name or ".." in parts.parts or "\\" in name):
            raise ValueError("native closure contains an unsafe member path")
        if (type(row["size_bytes"]) is not int or row["size_bytes"] < 0
                or type(row["executable"]) is not bool
                or not isinstance(row["sha256"], str) or len(row["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in row["sha256"])):
            raise ValueError("native closure contains an invalid file binding")
        names.append(name)
    if names != sorted(set(names)) or document["executable"] not in names:
        raise ValueError("native closure loses its ordered complete file census")
    return document, digest


def real_path(path):
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("native closure refuses symbolic-link paths")
    return path


def verify_closure(directory, manifest):
    directory = real_path(directory)
    if not directory.is_dir():
        raise ValueError("native closure requires an actual directory")
    actual = []
    def traversal_error(error):
        raise error

    for base, directories, files in os.walk(directory, followlinks=False, onerror=traversal_error):
        for name in (*directories, *files):
            path = Path(base) / name
            if path.is_symlink():
                raise ValueError("native closure refuses symbolic-link members")
        actual.extend((Path(base) / name).relative_to(directory).as_posix() for name in files)
    if sorted(actual) != [row["path"] for row in manifest["files"]]:
        raise ValueError("native closure differs from its complete file census")
    with FileHashCensus() as census:
        for row in manifest["files"]:
            path = directory / row["path"]
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode) or before.st_size != row["size_bytes"]:
                raise ValueError("native closure changes a regular member size: " + row["path"])
            _, digest = census.sha256(path, maximum_bytes=row["size_bytes"])
            after = path.lstat()
            if (not os.path.samestat(before, after) or before.st_ctime_ns != after.st_ctime_ns
                    or before.st_mode != after.st_mode
                    or digest != row["sha256"] or bool(after.st_mode & 0o111) != row["executable"]):
                raise ValueError("native closure changes member bytes or mode: " + row["path"])


@contextmanager
def verified_native_installation(directory, *, manifest_path, manifest_sha256):
    """Keep one selected tool closure authenticated through consumption and failure."""
    if not isinstance(manifest_sha256, str):
        raise ValueError("native installation requires an independent manifest digest")
    directory = real_path(directory)
    manifest, digest = load_manifest(manifest_path, expected_sha256=manifest_sha256)
    verify_closure(directory, manifest)
    try:
        yield {"installation": "verified", "manifest_sha256": digest,
               "executable": manifest["executable"], "file_count": len(manifest["files"]),
               "total_bytes": sum(row["size_bytes"] for row in manifest["files"])}
    finally:
        if load_manifest(manifest_path)[1] != digest:
            raise ValueError("native installation manifest changed during use")
        verify_closure(directory, manifest)


def restore_closure(*, manifest_path, source, destination):
    manifest, digest = load_manifest(manifest_path)
    source, destination = real_path(source), real_path(destination)
    if destination.exists() or destination == source or destination.is_relative_to(source):
        raise ValueError("native installation requires a fresh destination outside original custody")
    verify_closure(source, manifest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="." + destination.name + "-", dir=destination.parent))
    try:
        for row in manifest["files"]:
            target = staging / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with (source / row["path"]).open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer, 2**20)
                writer.flush()
                os.fsync(writer.fileno())
            target.chmod(0o555 if row["executable"] else 0o444)
        verify_closure(source, manifest)
        verify_closure(staging, manifest)
        rename_noreplace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    verify_closure(destination, manifest)
    return {"schema": "empirical-lawhood/native-installation-receipt", "version": "1.0.0",
        "manifest_sha256": digest, "source": str(source), "destination": str(destination),
        "file_count": len(manifest["files"]), "total_bytes": sum(row["size_bytes"] for row in manifest["files"]),
        "installation": "authenticated-restore", "upstream_build_reproduced": False,
        "scientific_qualification": False}
