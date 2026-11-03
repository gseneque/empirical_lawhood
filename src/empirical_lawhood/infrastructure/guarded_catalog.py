# SPDX-License-Identifier: MPL-2.0
"""One explicitly selected SQLite projection in guarded external scratch.

Selection is operational and grants no scientific authority. Construction opens
no database and creates no directory; actual connections recheck the mount.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import pwd
import sqlite3
import stat
from urllib.parse import quote

from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool

from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot
from empirical_lawhood.infrastructure.sql.database import (
    _configure_sqlite_read_only, _configure_sqlite_read_write, schema_audit, upgrade_catalog,
)
from empirical_lawhood.runtime.artifacts import validate_relative_locator
from empirical_lawhood.runtime.operator_profile import (
    OperatorStorageAccessMode, resolve_scientific_scratch_contract,
)


@dataclass(frozen=True, slots=True)
class GuardedCatalogAccess:
    root: GuardedExternalRoot
    relative_path: str
    writable: bool

    def __post_init__(self):
        if type(self.root) is not GuardedExternalRoot or type(self.writable) is not bool:
            raise TypeError("catalog requires the selected guarded root and exact access mode")
        if type(self.relative_path) is not str:
            raise TypeError("catalog_relative_path must be an exact relative string")
        validate_relative_locator(self.relative_path)
        if Path(self.relative_path).as_posix() != self.relative_path:
            raise ValueError("catalog_relative_path must be canonical")
        if self.relative_path.endswith(("-wal", "-shm", "-journal")):
            raise ValueError("catalog target cannot select a SQLite sidecar")

    @property
    def database_path(self):
        return Path(self.root.contract.canonical_path) / self.relative_path

    @property
    def display_locator(self):
        return "external-scratch:" + self.relative_path

    def verify(self, *, for_write, require_exists=False):
        if for_write and not self.writable:
            raise PermissionError("selected catalog profile is read-only")
        self.root.verify(for_write=for_write)
        path = self.root.resolve(self.relative_path, for_write=for_write)
        # SQLite also opens these neighbors. A linked database or sidecar is
        # never admitted, including a dangling link.
        for candidate in (path, *(path.with_name(path.name + suffix)
                for suffix in ("-wal", "-shm", "-journal"))):
            if candidate.is_symlink():
                raise PermissionError("selected SQLite catalog or sidecar is symlinked")
            if candidate.exists() and not stat.S_ISREG(candidate.stat().st_mode):
                raise PermissionError("selected SQLite catalog or sidecar is not regular")
        if not for_write:
            if any(path.with_name(path.name + suffix).exists() for suffix in ("-wal", "-shm")):
                raise PermissionError("selected read-only catalog requires its settled DELETE journal policy")
            if path.exists():
                self._require_rollback_header(path)
        if for_write:
            ancestor = path.parent
            while not ancestor.exists():
                ancestor = ancestor.parent
            if not ancestor.is_dir() or not os.access(ancestor, os.W_OK):
                raise PermissionError("selected catalog parent is not writable")
        if require_exists and not path.is_file():
            raise FileNotFoundError(path)
        return path

    @staticmethod
    def _require_rollback_header(path):
        # mode=ro can create WAL/SHM neighbors for a database whose retained
        # header still selects WAL, even after checkpoint removed the neighbors.
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise PermissionError("selected read-only catalog is not a regular file")
            header = os.read(descriptor, 100)
            after = os.fstat(descriptor)
            current = path.stat(follow_symlinks=False)
            fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
            identity = lambda value: tuple(getattr(value, field) for field in fields)
            if identity(before) != identity(after) or identity(before) != identity(current):
                raise PermissionError("selected read-only catalog changed during header admission")
            if len(header) != 100 or header[:16] != b"SQLite format 3\x00" or header[18:20] != bytes((1, 1)):
                raise PermissionError("selected read-only catalog requires a settled rollback-journal header")
        finally:
            os.close(descriptor)

    def _prepare_parent(self):
        self.verify(for_write=True)
        current = self.root.verify(for_write=True)
        for part in Path(self.relative_path).parts[:-1]:
            current /= part
            if not current.exists():
                current.mkdir(mode=0o700)
            if current.is_symlink() or not current.is_dir():
                raise PermissionError("selected catalog parent is not a real directory")
        self.verify(for_write=True)

    def _engine(self, *, read_only, initialize=False):
        # Read and preview never create a parent, database, journal or lock.
        self.verify(for_write=not read_only, require_exists=not initialize)
        if initialize:
            self._prepare_parent()

        def connect():
            path = self.verify(for_write=not read_only, require_exists=not initialize)
            mode = "ro" if read_only else ("rwc" if initialize else "rw")
            uri = "file:" + quote(path.as_posix(), safe="/") + "?mode=" + mode
            connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
            try:
                self.verify(for_write=not read_only, require_exists=True)
                # Keep SQLite's disposable sorting storage off implicit /tmp.
                connection.execute("PRAGMA temp_store=MEMORY")
            except BaseException:
                connection.close()
                raise
            return connection

        engine = create_engine("sqlite+pysqlite://", creator=connect, future=True, poolclass=NullPool)
        event.listen(engine, "connect", _configure_sqlite_read_only if read_only else _configure_sqlite_read_write)
        return engine

    def read_only_engine(self):
        return self._engine(read_only=True)

    def read_write_engine(self):
        return self._engine(read_only=False)

    def initialize_engine(self):
        engine = self._engine(read_only=False, initialize=True)
        try:
            upgrade_catalog(engine)
            if not schema_audit(engine).passed:
                raise RuntimeError("selected external catalog schema audit failed")
        except BaseException:
            engine.dispose()
            raise
        return engine


def select_operator_catalog(*, profile, project_root, catalog_relative_path):
    """Select the disjoint scratch contract without connecting or creating it."""
    if catalog_relative_path is None:
        return None
    if profile is None:
        raise ValueError("catalog_relative_path requires its explicit operator storage profile")
    contract = resolve_scientific_scratch_contract(profile, repo_root=project_root,
        home_root=Path(pwd.getpwuid(os.geteuid()).pw_dir), for_write=False)
    return GuardedCatalogAccess(GuardedExternalRoot(contract), catalog_relative_path,
        profile.access_mode is OperatorStorageAccessMode.READ_WRITE)


__all__ = ["GuardedCatalogAccess", "select_operator_catalog"]
