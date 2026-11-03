# SPDX-License-Identifier: MPL-2.0
"""Observe one ordinary installed distribution and its retained build source.

Distribution metadata identifies the producing source; it grants no execution,
outcome access or numerical qualification. Installed files are authenticated at
process admission and the selected installation must remain unchanged.
"""

from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import distribution
import json
from pathlib import Path
import stat
import sys
from types import MappingProxyType

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.serialization import (
    canonical_json_bytes, canonical_json_document_bytes, validate_relative_locator, validate_sha256,
)

SOURCE_METADATA_FILENAME = "empirical-lawhood-source.json"
_MAX_METADATA_BYTES = 8 * 1024 * 1024


def _identity(path):
    row = path.lstat()
    return (row.st_dev, row.st_ino, row.st_mode, row.st_size, row.st_mtime_ns, row.st_ctime_ns)


def _source_children(path):
    return frozenset(item.name for item in path.iterdir()
        if item.name != "__pycache__" and item.suffix not in (".pyc", ".pyo"))


def canonical_source_metadata_bytes(*, implementation_commit, implementation_sha256,
                                    source_tree_sha256, tracked_files):
    """Render the ordinary build metadata from its already validated source census.

    Stored source observations can authenticate their own metadata identity
    without inspecting the installation used to read them.
    """
    return canonical_json_document_bytes({
        "schema": "empirical-lawhood/build/source", "version": "1.0.0",
        "implementation_commit": implementation_commit,
        "implementation_sha256": implementation_sha256,
        "source_tree_sha256": source_tree_sha256,
        "tracked_files": list(tracked_files),
    })


def read_source_metadata(path):
    raw = read_bounded_bytes(path, maximum_bytes=_MAX_METADATA_BYTES)
    value = json.loads(raw)
    if (type(value) is not dict or set(value) != {"schema", "version", "implementation_commit",
            "implementation_sha256", "source_tree_sha256", "tracked_files"}
            or value["schema"] != "empirical-lawhood/build/source" or value["version"] != "1.0.0"
            or type(value["tracked_files"]) is not list or not value["tracked_files"]
            or canonical_source_metadata_bytes(implementation_commit=value["implementation_commit"],
                implementation_sha256=value["implementation_sha256"],
                source_tree_sha256=value["source_tree_sha256"],
                tracked_files=value["tracked_files"]) != raw):
        raise ValueError("installed candidate source metadata changes its exact contract")
    head = value["implementation_commit"]
    if type(head) is not str or len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
        raise ValueError("installed candidate omits its producing source commit")
    validate_sha256(value["implementation_sha256"])
    validate_sha256(value["source_tree_sha256"])
    previous = ""
    for row in value["tracked_files"]:
        if type(row) is not dict or set(row) != {"relative_path", "mode", "size_bytes", "sha256"}:
            raise ValueError("installed candidate source member changes its contract")
        name = row["relative_path"]
        validate_relative_locator(name)
        validate_sha256(row["sha256"])
        if (name <= previous or row["mode"] not in ("100644", "100755")
                or type(row["size_bytes"]) is not int or row["size_bytes"] < 0):
            raise ValueError("installed candidate source census is not unique, ordered and regular")
        previous = name
    if not {"uv.lock", "pyproject.toml"} <= {row["relative_path"] for row in value["tracked_files"]}:
        raise ValueError("installed candidate omits its build and dependency lock inputs")
    return value, raw


@dataclass(frozen=True, slots=True)
class InstalledCandidate:
    package_root: Path
    metadata_path: Path
    metadata_identity: tuple
    implementation_commit: str
    implementation_sha256: str
    source_tree_sha256: str
    tracked_files: tuple
    source_bytes: bytes
    package_sources: tuple[tuple[str, str], ...]
    code_sources_sha256: str
    dependency_lock_sha256: str
    file_identities: dict
    directory_observations: dict

    def require_current(self):
        if _identity(self.metadata_path) != self.metadata_identity:
            raise PermissionError("selected installed candidate metadata changed during its lifetime")
        try:
            if read_bounded_bytes(self.metadata_path, maximum_bytes=len(self.source_bytes)) != self.source_bytes:
                raise PermissionError("selected installed candidate metadata bytes changed during its lifetime")
            for relative, digest in self.package_sources:
                path = self.package_root / relative
                expected = self.file_identities[relative]
                if _identity(path) != expected:
                    raise PermissionError("installed candidate package member changed after admission")
                raw = read_bounded_bytes(path, maximum_bytes=expected[3])
                if (len(raw) != expected[3] or sha256(raw).hexdigest() != digest
                        or _identity(path) != expected):
                    raise PermissionError("installed candidate package bytes changed after admission")
            for relative, (expected, children) in tuple(self.directory_observations.items()):
                path = self.package_root / relative
                observed = _identity(path)
                # EL can assign the same stat timestamps to distinct readable
                # writes. Neither file bytes nor membership may be inferred
                # from an unchanged stat identity.
                if observed[:3] != expected[:3] or _source_children(path) != children:
                    raise PermissionError("installed candidate package census changed after admission")
                # Python may create ignored bytecode/cache children.
                self.directory_observations[relative] = (observed, children)
        except OSError as error:
            raise PermissionError("installed candidate package member disappeared after admission") from error
        self.require_loaded_origins()

    def require_loaded_origins(self):
        for name, module in tuple(sys.modules.items()):
            if name != "empirical_lawhood" and not name.startswith("empirical_lawhood."):
                continue
            origin = getattr(module, "__file__", None)
            if origin is None:
                locations = getattr(getattr(module, "__spec__", None), "submodule_search_locations", None)
                expected = self.package_root.joinpath(*name.split(".")[1:])
                if locations is None or tuple(Path(item).resolve(strict=True) for item in locations) != (expected,):
                    raise PermissionError("loaded installed namespace has another source origin")
                continue
            path = Path(origin).absolute()
            if path.resolve(strict=True) != path or not path.is_relative_to(self.package_root):
                raise PermissionError("loaded module is outside the selected installed candidate")
            relative = path.relative_to(self.package_root).as_posix()
            if relative not in self.file_identities or _identity(path) != self.file_identities[relative]:
                raise PermissionError("loaded installed candidate source changed after admission")


_installed_candidates = {}
_source_roots = {}


def installed_candidate(*, source_root=None):
    """Reuse one decoded source identity, checking current bytes without Git.

    A selected source distribution supplies public documentation/configuration;
    it must carry the exact same build metadata as the executing distribution.
    It is not an executable checkout or a reconstructed historical compiler.
    """
    import empirical_lawhood

    package = Path(empirical_lawhood.__file__).absolute().parent
    selected = distribution("empirical-lawhood")
    if Path(selected.locate_file("empirical_lawhood")).absolute() != package:
        raise PermissionError("executing package differs from its selected installed distribution")
    members = tuple(row for row in selected.files or () if str(row).endswith(".dist-info/extra_metadata/source.json"))
    if len(members) != 1:
        raise PermissionError("installed candidate omits its ordinary build source metadata")
    metadata = Path(selected.locate_file(members[0])).absolute()
    if package.resolve(strict=True) != package or metadata.resolve(strict=True) != metadata:
        raise PermissionError("installed candidate refuses symbolic source paths")
    key = (package, metadata)
    result = _installed_candidates.get(key)
    admitted_now = result is None
    if result is None:
        metadata_identity = _identity(metadata)
        if metadata_identity[2] & 0o7111:
            raise PermissionError("installed candidate source metadata must be nonexecutable data")
        source, raw = read_source_metadata(metadata)
        if _identity(metadata) != metadata_identity:
            raise PermissionError("installed candidate metadata changed during admission")
        prefix = "src/empirical_lawhood/"
        expected = {row["relative_path"][len(prefix):]: row for row in source["tracked_files"]
                    if row["relative_path"].startswith(prefix)}
        actual = set()
        identities = {}
        directories = {".": (_identity(package), _source_children(package))}
        rows = []
        for path in package.rglob("*"):
            relative = path.relative_to(package)
            if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
                continue
            observed = path.lstat()
            if path.is_symlink():
                raise PermissionError("installed candidate contains a symbolic package member")
            if stat.S_ISDIR(observed.st_mode):
                directories[relative.as_posix()] = (_identity(path), _source_children(path))
                continue
            name = relative.as_posix()
            row = expected.get(name)
            if row is None or not stat.S_ISREG(observed.st_mode):
                raise PermissionError("installed candidate changes its complete package census")
            if (observed.st_mode & 0o7000 or
                    (row["mode"] == "100644" and observed.st_mode & 0o111) or
                    (row["mode"] == "100755" and not observed.st_mode & stat.S_IXUSR)):
                raise PermissionError("installed candidate changes its source executable mode")
            identity = _identity(path)
            data = read_bounded_bytes(path, maximum_bytes=row["size_bytes"])
            if len(data) != row["size_bytes"] or sha256(data).hexdigest() != row["sha256"] or _identity(path) != identity:
                raise PermissionError("installed candidate package bytes differ from its build source")
            actual.add(name)
            identities[name] = identity
            rows.append((name, row["sha256"]))
        if actual != set(expected):
            raise PermissionError("installed candidate omits a producing package member")
        lock, = (row["sha256"] for row in source["tracked_files"] if row["relative_path"] == "uv.lock")
        package_sources = tuple(sorted(rows))
        from empirical_lawhood.infrastructure.source_closure import TrackedSourceMember

        members = tuple(TrackedSourceMember(**row) for row in source["tracked_files"])
        result = InstalledCandidate(package, metadata, metadata_identity,
            source["implementation_commit"], source["implementation_sha256"], source["source_tree_sha256"],
            members, raw, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(),
            lock, MappingProxyType(identities), directories)
    if not admitted_now:
        result.require_current()
    if source_root is not None:
        root = Path(source_root).resolve(strict=True)
        if (root / ".git").exists():
            raise PermissionError("installed execution selects its source distribution, not an executing checkout")
        paths = (root / SOURCE_METADATA_FILENAME, root / "uv.lock", root / "pyproject.toml")
        key = (root, result.metadata_path)
        observed = tuple(_identity(path) for path in paths)
        if observed[0][2] & 0o7111:
            raise PermissionError("selected source metadata must be ordinary nonexecutable data")
        previous = _source_roots.get(key)
        if previous is not None and previous != observed:
            raise PermissionError("selected source distribution changed after admission")
        raw = read_bounded_bytes(paths[0], maximum_bytes=len(result.source_bytes))
        if raw != result.source_bytes:
            raise PermissionError("selected source distribution differs from the installed candidate")
        expected = {row.relative_path: row for row in result.tracked_files}
        for path, observation in zip(paths[1:], observed[1:], strict=True):
            row = expected[path.name]
            if (observation[2] & 0o7000
                    or (row.mode == "100644" and observation[2] & 0o111)
                    or (row.mode == "100755" and not observation[2] & stat.S_IXUSR)):
                raise PermissionError("selected source distribution changes its build or lock executable mode")
            data = read_bounded_bytes(path, maximum_bytes=row.size_bytes)
            if len(data) != row.size_bytes or sha256(data).hexdigest() != row.sha256:
                raise PermissionError("selected source distribution changes its build or lock input")
        if tuple(_identity(path) for path in paths) != observed:
            raise PermissionError("selected source distribution changed during admission")
        _source_roots[key] = observed
    if admitted_now:
        # Close the complete first observation after its selected source joins.
        # Loaded origins alone cannot detect a changed unloaded member or a
        # child added to a directory already visited during the initial census.
        result.require_current()
        _installed_candidates[(package, metadata)] = result
    return result
