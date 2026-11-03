"""Guarded content-addressed reads for candidate readiness."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
import time
from typing import Final, Protocol

from empirical_lawhood.infrastructure.atomic_files import rename_noreplace
from empirical_lawhood.infrastructure.artifacts import (
    ArtifactIdentityConflict,
    ExternalRootUnavailable,
    GuardedExternalRoot,
)
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError, file_matches_bytes
from empirical_lawhood.infrastructure.dataset_io import ExternalDatasetSourceOpener
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.dataset_authority import DatasetStorageScope
from empirical_lawhood.runtime.progress import report_progress
from empirical_lawhood.runtime.source_resolution import (
    ContentAddressedInputRequirement,
    ContentAddressedResolutionError,
    ContentResolutionReceipt,
    ResolvedContent,
)


_DEFAULT_CHUNK_BYTES: Final[int] = 1024 * 1024


class CandidateSourceClock(Protocol):
    def now_utc(self) -> str: ...

    def monotonic_ns(self) -> int: ...


@dataclass(frozen=True, slots=True)
class SystemCandidateSourceClock:
    def now_utc(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


class ExternalContentAddressedInputResolver:
    """Read exact derived addresses without acquisition, writes, or path input."""

    def __init__(
        self,
        root: GuardedExternalRoot,
        *,
        clock: CandidateSourceClock | None = None,
        chunk_bytes: int = _DEFAULT_CHUNK_BYTES,
    ) -> None:
        if (
            not isinstance(chunk_bytes, int)
            or isinstance(chunk_bytes, bool)
            or chunk_bytes <= 0
            or chunk_bytes > _DEFAULT_CHUNK_BYTES
        ):
            raise ValueError("chunk_bytes must be in (0, 1 MiB]")
        self.root = root
        self.clock = clock or SystemCandidateSourceClock()
        self.chunk_bytes = chunk_bytes
        self._opener = ExternalDatasetSourceOpener(root)

    def resolve(
        self,
        requirement: ContentAddressedInputRequirement,
        *,
        materialize: bool,
    ) -> ResolvedContent:
        if not isinstance(requirement, ContentAddressedInputRequirement):
            raise TypeError("requirement must be a ContentAddressedInputRequirement")
        if type(materialize) is not bool:
            raise TypeError("materialize must be a boolean")
        try:
            path = self.root.resolve(
                requirement.relative_locator,
                for_write=False,
            )
            before = path.lstat()
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                raise ContentAddressedResolutionError(
                    "content address is not a regular non-symlink file"
                )
            observed_size = before.st_size
            if requirement.maximum_bytes is not None and observed_size > requirement.maximum_bytes:
                raise ContentAddressedResolutionError(
                    "content address exceeds its read-work envelope"
                )
            if (
                requirement.expected_size_bytes is not None
                and observed_size != requirement.expected_size_bytes
            ):
                raise ContentAddressedResolutionError(
                    "content address size differs from its exact expectation"
                )
            root_identity = ObjectIdentity.from_record(
                self.root.contract.storage_root_id,
                self.root.contract,
            )
            source_scope = DatasetStorageScope(
                scope_id=f"candidate-input.{requirement.content_sha256[:24]}",
                storage_root=root_identity,
                relative_prefix=requirement.relative_locator,
            )
            trusted_at_utc = self.clock.now_utc()
            started_ns = self.clock.monotonic_ns()
            chunks: list[bytes] | None = [] if materialize else None
            chunk_count = 0
            maximum_chunk = 0
            observed_consumer_bytes = 0
            with self._opener.open_exact(
                source_scope=source_scope,
                expected_size_bytes=observed_size,
                expected_sha256=requirement.content_sha256,
                # Exact observed size supplies the read guard when the caller
                # selects no resource ceiling. The opener's positive envelope
                # represents an empty file with 1, while expected_size_bytes
                # still requires exactly zero bytes.
                maximum_bytes=(max(1, observed_size) if requirement.maximum_bytes is None
                               else requirement.maximum_bytes),
                trusted_at_utc=trusted_at_utc,
            ) as guarded:
                while True:
                    chunk = guarded.stream.read(self.chunk_bytes)
                    if not chunk:
                        break
                    chunk_count += 1
                    maximum_chunk = max(maximum_chunk, len(chunk))
                    observed_consumer_bytes += len(chunk)
                    if chunks is not None:
                        chunks.append(chunk)
            guard_receipt = guarded.guard_receipt
            finished_ns = self.clock.monotonic_ns()
            elapsed_ns = finished_ns - started_ns
            if elapsed_ns <= 0:
                raise ContentAddressedResolutionError(
                    "source clock did not advance during content resolution"
                )
            if observed_consumer_bytes != observed_size:
                raise ContentAddressedResolutionError(
                    "content consumer did not read the exact byte envelope"
                )
            after = path.lstat()
            if (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ) != (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            ):
                raise ContentAddressedResolutionError("content address changed across resolution")
            receipt_subject = canonical_json_bytes(
                {
                    "guard_receipt_id": guard_receipt.guard_receipt_id,
                    "requirement": requirement,
                }
            )
            receipt_id = f"content-resolution.{hashlib.sha256(receipt_subject).hexdigest()[:24]}"
            receipt = ContentResolutionReceipt(
                receipt_id=receipt_id,
                requirement=ObjectIdentity.from_record(
                    requirement.requirement_id,
                    requirement,
                ),
                observed_sha256=guard_receipt.observed_sha256,
                observed_size_bytes=observed_size,
                chunk_count=chunk_count,
                maximum_chunk_bytes=maximum_chunk,
                verification_pass_count=2,
                consumer_pass_count=1,
                observed_total_read_bytes=observed_size * 3,
                payload_materialized=materialize,
                materialized_bytes=observed_size if materialize else 0,
                algorithmic_peak_buffer_bound_bytes=(
                    observed_size * 2 + maximum_chunk if materialize else maximum_chunk
                ),
                observed_throughput_bytes_per_second=(
                    observed_size * 3 * 1_000_000_000 // elapsed_ns
                ),
                elapsed_nanoseconds=elapsed_ns,
                repository_bytes_written=0,
                external_bytes_written=0,
                network_bytes=guard_receipt.network_bytes,
                read_only=True,
                nofollow_enforced=guard_receipt.nofollow_enforced,
                file_identity_stable=guard_receipt.file_identity_stable,
            )
            payload = None if chunks is None else b"".join(chunks)
            return ResolvedContent(receipt=receipt, payload=payload)
        except ContentAddressedResolutionError:
            raise
        except FileNotFoundError as error:
            raise ContentAddressedResolutionError(
                "content address is absent; acquisition was not attempted"
            ) from error
        except (
            ArtifactIdentityConflict,
            ExternalRootUnavailable,
            OSError,
            ValueError,
        ) as error:
            raise ContentAddressedResolutionError(
                "guarded content-addressed read failed"
            ) from error

    @staticmethod
    def install_path(root: Path, content_sha256: str) -> Path:
        """Return the deterministic test/owner publication target; perform no write."""

        return root / "candidate-inputs" / "sha256" / content_sha256[:2] / content_sha256


@dataclass(frozen=True, slots=True)
class CandidateInputPublication:
    """Result of an immutable exact-byte candidate-control publication."""

    content_sha256: str
    size_bytes: int
    relative_locator: str
    replayed: bool
    publication_mode: str


class ExternalCandidateInputPublisher:
    """Publish compact candidate control bytes atomically at their content address."""

    def __init__(self, root: GuardedExternalRoot) -> None:
        self.root = root

    def publish(
        self,
        payload: bytes,
        *,
        maximum_bytes: int | None = None,
    ) -> CandidateInputPublication:
        return self.publish_many((payload,), maximum_bytes=maximum_bytes, batch_size=1)[0]

    def publish_many(
        self,
        payloads: Iterable[bytes],
        *,
        maximum_bytes: int | None = None,
        batch_size: int = 64,
    ) -> tuple[CandidateInputPublication, ...]:
        """Publish each input atomically, sharing only directory durability work.

        One input is written and file-synced at a time. At most ``batch_size``
        input publications share a directory-sync window; payloads are not
        buffered. A failed iterator or member leaves complete content addresses
        already published, which are synced before the error propagates. This
        is not an atomic multi-input transaction.
        """
        if type(batch_size) is not int or batch_size <= 0:
            raise ValueError("candidate publication batch_size must be a positive integer")
        publications = []
        dirty_directories: set[Path] = set()
        report_progress(phase="publish_inputs", done=0)
        try:
            try:
                for payload in payloads:
                    publications.append(self._publish(payload, maximum_bytes, dirty_directories))
                    if len(publications) % batch_size == 0:
                        self._sync_directories(dirty_directories)
                        report_progress(phase="publish_inputs", done=len(publications))
            finally:
                self._sync_directories(dirty_directories)
        except Exception:
            report_progress(phase="publish_inputs", failed=1)
            raise
        result = tuple(publications)
        report_progress(phase="publish_inputs", done=len(publications), total=len(publications))
        return result

    @staticmethod
    def _sync_directories(directories: set[Path]) -> None:
        # Children must reach storage before the entries naming their parents.
        # Attempt every pending directory even if one sync fails. A failed
        # operation returns no publications and does not claim durability.
        pending = sorted(directories, key=lambda path: (-len(path.parts), str(path)))
        directories.clear()
        first_error: BaseException | None = None
        for path in pending:
            descriptor = None
            try:
                descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0))
                os.fsync(descriptor)
            except BaseException as error:
                if first_error is None:
                    first_error = error
            finally:
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except BaseException as error:
                        if first_error is None:
                            first_error = error
        if first_error is not None:
            raise first_error

    @staticmethod
    def _require_exact_replay(target: Path, payload: bytes) -> None:
        try:
            before = target.lstat()
            if not stat.S_ISREG(before.st_mode) or not file_matches_bytes(target, payload):
                raise ArtifactIdentityConflict("candidate input content address contains different bytes")
            after = target.lstat()
            fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
            if tuple(getattr(before, key) for key in fields) != tuple(getattr(after, key) for key in fields):
                raise ArtifactIdentityConflict("candidate input changed during exact replay")
        except (OSError, BoundedFileIOError) as error:
            raise ArtifactIdentityConflict("candidate input destination is not a stable regular file") from error

    def _publish(
        self, payload: bytes, maximum_bytes: int | None, dirty_directories: set[Path],
    ) -> CandidateInputPublication:
        if not isinstance(payload, bytes):
            raise TypeError("candidate input payload must be bytes")
        if not payload or (maximum_bytes is not None and len(payload) > maximum_bytes):
            raise ValueError("candidate input payload violates its byte envelope")
        digest = hashlib.sha256(payload).hexdigest()
        relative = f"candidate-inputs/sha256/{digest[:2]}/{digest}"
        target = self.root.resolve(
            relative,
            for_write=True,
            operation_minimum_free_bytes=len(payload),
        )
        root_path = Path(self.root.contract.canonical_path)
        directory = root_path
        for component in target.parent.relative_to(root_path).parts:
            parent, directory = directory, directory / component
            try:
                directory.mkdir()
            except FileExistsError:
                if directory.is_symlink() or not directory.is_dir():
                    raise ExternalRootUnavailable("candidate input parent is not a regular directory") from None
            else:
                dirty_directories.add(parent)
        target = self.root.resolve(
            relative,
            for_write=True,
            operation_minimum_free_bytes=len(payload),
        )
        # Also sync existing ancestry: a concurrent publisher or an interrupted
        # earlier call may have installed an entry without completing its sync.
        directory = target.parent
        while True:
            dirty_directories.add(directory)
            if directory == root_path:
                break
            directory = directory.parent
        try:
            before = target.lstat()
        except FileNotFoundError:
            before = None
        if before is not None:
            self._require_exact_replay(target, payload)
            return CandidateInputPublication(
                content_sha256=digest,
                size_bytes=len(payload),
                relative_locator=relative,
                replayed=True,
                publication_mode="EXACT_REPLAY",
            )

        token = hashlib.sha256(f"{os.getpid()}\0{time.time_ns()}\0{digest}".encode()).hexdigest()[
            :24
        ]
        staged = target.parent / f".{digest}.{token}.stage"
        descriptor: int | None = None
        staged_created = False
        try:
            descriptor = os.open(
                staged,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o440,
            )
            staged_created = True
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("candidate input publication made no progress")
                view = view[written:]
            os.fsync(descriptor)
            synced_descriptor, descriptor = descriptor, None
            os.close(synced_descriptor)
            try:
                try:
                    os.link(staged, target, follow_symlinks=False)
                except PermissionError:
                    # The same synced staging inode can be installed on VFAT.
                    # Unsupported exclusive rename fails closed; never copy
                    # bytes into a visible target or replace an address.
                    rename_noreplace(staged, target)
                    publication_mode = "ATOMIC_RENAME_NO_REPLACE"
                else:
                    publication_mode = "ATOMIC_HARDLINK_NO_REPLACE"
            except FileExistsError:
                self._require_exact_replay(target, payload)
                replayed = True
                publication_mode = "EXACT_REPLAY"
            else:
                replayed = False
        finally:
            try:
                if descriptor is not None:
                    os.close(descriptor)
            finally:
                if staged_created:
                    try:
                        staged.unlink()
                    except FileNotFoundError:
                        pass
        return CandidateInputPublication(
            content_sha256=digest,
            size_bytes=len(payload),
            relative_locator=relative,
            replayed=replayed,
            publication_mode=publication_mode,
        )


__all__ = [
    "CandidateInputPublication",
    "CandidateSourceClock",
    "ExternalCandidateInputPublisher",
    "ExternalContentAddressedInputResolver",
    "SystemCandidateSourceClock",
]
