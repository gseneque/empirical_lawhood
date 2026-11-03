# SPDX-License-Identifier: MPL-2.0
"""Observe checkout changes separately from selected-source authentication.

This operational observation is separate from historical scientific source
records. It authorizes no execution, source amendment or scientific act.
"""

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import stat


LOCAL_PLAN_NAME = "WTF.md"
# Operational instructions and implementation/audit ledgers are local data,
# never supported researcher inputs. Keep this inventory explicit so a newly
# introduced root Markdown file needs a deliberate release classification.
ROOT_WORK_PLAN_NAMES = frozenset({
    "DOCSTRUCTCONSOL.md",  # Local approved documentation consolidation ledger.
    "APPLIED-EL-REVIEW-WORKING.md", "CONSOLIDATE.md", "CONSOLIDATION.md",
    "E1-ANALYSIS.md", "E3-ANALYSIS.md",  # Local retained-result reports with external evidence links.
    "E-RECCHAIN-FINALANALYSIS.md",  # Local integrated scientific analysis, not a public workflow.
    "E2-CONTROLPRELIM.md", "E2-PRELIM.md",  # Local retained-E2 analysis plans and ledgers.
    "E2-MECHANISM-ANALYSIS.md", "E2-MECHANISM-ANALYSIS-RESULTS.md",
    "E4-PRELIM.md", "E4-POSTANALYSIS.md",  # Local retained-E4 analyses with external evidence links.
    "EL-MECHANISM-DENOMINATORS-RECURSION-AND-APPLICATIONS.md",  # Local research synthesis, not an implementation queue.
    "EL-PREP-H64-LITERATURE-AUDIT-AND-DESIGN.md",  # Local future-study proposal and literature audit.
    "RLS-INTEGAUDIT.md",  # Local scientific-integrity and bookkeeping audit.
    "RUBCAND-1.md", "RUBCAND-1-LINEAGE.md",  # Local candidate and lineage analyses.
    "ELSC.md", "ELTOP5.md", "MATRIX-FINALOPTIM.md", "MATRIXAUDIT.md",
    "PAPERMIGRATION.md", "RECHAIN-OPTIM-CURRENTSTATE.md",
    "PREPRINTNOVELTY.md", "RECCHAIN-CURRENT.md", "RECURARCH.md", "RUBISCO-FINALSE.md", "RUBISCO-FINALSE-UPDATED.md", "RUBISCO-LOOP.md",
    "RUBISCO-PRIZE-REFINED-PLAN.md", "THEMATRIX-AUDIT-EXPDESIGN.md", "THEMATRIX-LEAN.md",
    "THEMATRIX-NOVELTY-E3-E6-REVIEW.md",
    "THEMATRIX-MIDFIXES.md", "THEMATRIX-OPTIM-DEFERRED.md", "THEMATRIX-OPTIM.md",
    "THEMATRIX.md", "WTF-FINALDESIGN.md", "WTF-OPTIMPRIO.md", LOCAL_PLAN_NAME,
})
# These documentary records contain implementation assignments, work queues or
# acceptance plans. Their historical scientific evidence remains preserved;
# their location among public documents does not make the work orders inputs.
DOCUMENT_WORK_PLAN_PATHS = frozenset({
    "docs/applied-el-handoff.md",
    "docs/applied-el/architecture-finalisation.md",
    "docs/applied-el/battery-controller-composition.md",
    "docs/applied-el/battery-interface-selection.md",
    "docs/applied-el/ra0-selection.md",
    "docs/applied-el/consolidation-c4-progress.md",
    "docs/applied-el/matrix-factor-development-progress.md",
    "docs/applied-el/battery-remediation-progress.md",
    "docs/rubisco-inquiry/scientific-redirection-v1.md",
})
NESTED_WORK_PLAN_PATHS = frozenset({
    "src/empirical_lawhood/adapters/methods/preparation_applicability/frozen_specification.md",
    "src/empirical_lawhood/adapters/methods/constructed_preparation_applicability/frozen_specification.md",
})
MAINTAINED_ROOT_MARKDOWN = frozenset({
    "AGENTS.md", "CHANGELOG.md", "CITATION.md", "CONTRIBUTING.md", "README.md",
    "REPRODUCIBILITY.md",
})
WORK_PLAN_DIRECTORIES = ("docs/plans", "PROREVIEW")
_READ_CHUNK_BYTES = 1024 * 1024


def is_work_plan_path(relative_path: str) -> bool:
    """Classify preserved work records, distinct from scientific protocols.

    Current scientific specifications belong to their programme records. The
    two explicitly inventoried nested records contain historical instructions
    and grants, despite their ``frozen_specification.md`` filenames.
    """
    return (relative_path in ROOT_WORK_PLAN_NAMES or relative_path in DOCUMENT_WORK_PLAN_PATHS
            or relative_path in NESTED_WORK_PLAN_PATHS
            or relative_path.startswith(tuple(name + "/" for name in WORK_PLAN_DIRECTORIES))
            and relative_path.endswith(".md")
            or "/" not in relative_path and relative_path.endswith(".md")
            and relative_path.startswith(("FINAL", "DERPCHAIN", "LOWFRICTION", "SCIREVIEW", "DOCFINALISE")))


class SourcePolicyError(PermissionError):
    """The checkout's operational source disclosure cannot be authenticated."""


@dataclass(frozen=True, slots=True)
class CheckoutPathChange:
    status: str
    relative_path: str
    original_path: str | None = None

    def to_mapping(self):
        return {"status": self.status, "relative_path": self.relative_path,
                "original_path": self.original_path}


def _status_changes(raw):
    if type(raw) is not bytes:
        raise TypeError("source observation requires complete raw Git status bytes")
    if not raw:
        return ()
    nul = b"\0" in raw
    separator = b"\0" if nul else b"\n"
    if not raw.endswith(separator):
        raise SourcePolicyError("Git status must retain its complete record terminators")
    rows, changes = iter(raw[:-1].split(separator)), []
    for row in rows:
        if (len(row) < 4 or row[2:3] != b" "
                or any(value not in b" MADRCUT?!" for value in row[:2])):
            raise SourcePolicyError("malformed porcelain-v1 Git status record")
        status, path = row[:2].decode("ascii"), row[3:].decode("utf-8", "surrogateescape")
        original = None
        if not nul and (path.startswith('"') or "R" in status or "C" in status):
            raise SourcePolicyError("quoted or renamed Git paths require NUL-terminated status")
        if nul and ("R" in status or "C" in status):
            try:
                original = next(rows).decode("utf-8", "surrogateescape")
            except StopIteration as error:
                raise SourcePolicyError("renamed Git status omits its original path") from error
            if not original:
                raise SourcePolicyError("renamed Git status has an empty original path")
        changes.append(CheckoutPathChange(status, path, original))
    return tuple(changes)


@dataclass(frozen=True, slots=True)
class LocalPlanDisclosure:
    relative_path: str
    size_bytes: int
    sha256: str
    mode: int

    def __post_init__(self):
        if (self.relative_path != LOCAL_PLAN_NAME or type(self.size_bytes) is not int or self.size_bytes < 0
                or type(self.mode) is not int or not 0 <= self.mode <= 0o7777 or self.mode & 0o111
                or type(self.sha256) is not str or len(self.sha256) != 64
                or any(value not in "0123456789abcdef" for value in self.sha256)):
            raise ValueError("local-plan disclosure changes its exact path, size, mode or digest")

    def to_mapping(self):
        return {"relative_path": self.relative_path, "size_bytes": self.size_bytes,
                "sha256": self.sha256, "mode": self.mode}


@dataclass(frozen=True, slots=True)
class CheckoutSourceAdmission:
    raw_status: bytes
    local_plan: LocalPlanDisclosure | None
    selected_paths: tuple[str, ...] = ()

    def __post_init__(self):
        changes = _status_changes(self.raw_status)
        plan_status = tuple(row for row in changes if row.relative_path == LOCAL_PLAN_NAME)
        if (self.local_plan is not None and (type(self.local_plan) is not LocalPlanDisclosure
                or len(plan_status) != 1 or plan_status[0].status != "??")
                or type(self.selected_paths) is not tuple
                or any(type(path) is not str or not path or path.startswith("/")
                    or ".." in path.split("/") or "\0" in path or "\\" in path
                    or PurePosixPath(path).as_posix() != path or path == "." for path in self.selected_paths)
                or self.selected_paths != tuple(sorted(set(self.selected_paths)))):
            raise ValueError("source observation changes its separate plan or exact selected-path scope")

    @property
    def changes(self) -> tuple[CheckoutPathChange, ...]:
        return _status_changes(self.raw_status)

    @property
    def selected_path_changes(self) -> tuple[CheckoutPathChange, ...]:
        return tuple(row for row in self.changes if row.relative_path in self.selected_paths
                     or row.original_path in self.selected_paths)

    @property
    def observed_checkout_clean(self) -> bool:
        """Raw Git cleanliness, including the disclosed untracked plan."""
        return not self.raw_status

    def to_mapping(self):
        return {"policy": "selected-source-identities-v1",
                "raw_status_sha256": sha256(self.raw_status).hexdigest(),
                "observed_checkout_clean": self.observed_checkout_clean,
                "changes": tuple(row.to_mapping() for row in self.changes),
                "selected_paths": self.selected_paths,
                "selected_path_changes": tuple(row.to_mapping() for row in self.selected_path_changes),
                "local_plan": None if self.local_plan is None else self.local_plan.to_mapping()}


@dataclass(frozen=True, slots=True)
class InstalledSourceAdmission:
    """An installed candidate observation makes no checkout-cleanliness claim."""

    source_metadata_sha256: str
    selected_paths: tuple[str, ...]

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_sha256

        validate_sha256(self.source_metadata_sha256)
        if type(self.selected_paths) is not tuple or self.selected_paths != tuple(sorted(set(self.selected_paths))):
            raise ValueError("installed candidate requires its exact selected source paths")
        for name in self.selected_paths:
            validate_relative_locator(name)

    @property
    def observed_checkout_clean(self):
        return False

    def to_mapping(self):
        return {"policy": "installed-candidate-v1", "source_metadata_sha256": self.source_metadata_sha256,
                "selected_paths": self.selected_paths, "checkout_observed": False,
                "observed_checkout_clean": False}


def _identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _read_plan(root_descriptor):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(LOCAL_PLAN_NAME, flags, dir_fd=root_descriptor)
    try:
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_mode & 0o111
                or before.st_nlink < 1):
            raise SourcePolicyError("local plan must be a regular non-executable file")
        digest, size = sha256(), 0
        while size < before.st_size:
            raw = os.read(descriptor, min(_READ_CHUNK_BYTES, before.st_size - size))
            if not raw:
                raise SourcePolicyError("local plan was truncated during disclosure")
            digest.update(raw)
            size += len(raw)
        if os.read(descriptor, 1):
            raise SourcePolicyError("local plan grew during disclosure")
        after = os.fstat(descriptor)
        selected = os.stat(LOCAL_PLAN_NAME, dir_fd=root_descriptor, follow_symlinks=False)
        if _identity(before) != _identity(after) or _identity(before) != _identity(selected):
            raise SourcePolicyError("local plan changed during disclosure")
        return LocalPlanDisclosure(LOCAL_PLAN_NAME, size, digest.hexdigest(), stat.S_IMODE(before.st_mode))
    finally:
        os.close(descriptor)


def inspect_checkout_source(repo_root: Path, status: bytes, *, selected_paths: tuple[str, ...] = ()) -> CheckoutSourceAdmission:
    """Disclose raw changes and the plan without imposing empty Git status.

    ``status`` is complete, unstripped porcelain-v1 output with all untracked
    files included. NUL-terminated output is also accepted. The caller owns Git
    HEAD/tree, actual selected-file identities and module-origin authentication.
    ``selected_paths`` names exact tracked inputs owned by that caller; changes
    there are diagnostics, never a substitute for byte verification. Unrelated
    prose changes do not invalidate an independently authenticated selection.
    The root plan must remain explicitly untracked, regular and non-executable.
    """
    if not isinstance(repo_root, Path) or not repo_root.is_absolute() or ".." in repo_root.parts:
        raise ValueError("source admission requires an exact absolute checkout Path")
    changes = _status_changes(status)
    # Validate the scope before opening any descriptor.
    CheckoutSourceAdmission(status, None, selected_paths)
    plan_status = tuple(row for row in changes if row.relative_path == LOCAL_PLAN_NAME)
    if not getattr(os, "O_NOFOLLOW", 0) or not getattr(os, "O_DIRECTORY", 0):
        raise SourcePolicyError("platform cannot enforce no-follow local-plan admission")
    descriptor = None
    try:
        descriptor = os.open(repo_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                             | getattr(os, "O_CLOEXEC", 0))
        if len(plan_status) != 1 or plan_status[0].status != "??":
            try:
                os.stat(LOCAL_PLAN_NAME, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                if plan_status:
                    raise SourcePolicyError("local-plan status cannot be disclosed without its file") from None
                return CheckoutSourceAdmission(status, None, selected_paths)
            raise SourcePolicyError("root local plan lacks its explicit untracked Git status")
        return CheckoutSourceAdmission(status, _read_plan(descriptor), selected_paths)
    except SourcePolicyError:
        raise
    except OSError as error:
        raise SourcePolicyError("local-plan file identity cannot be authenticated") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def require_unchanged_source_admission(before, after) -> None:
    """Bind plan and selected scope; owners reauthenticate selected file identities.

    Raw status can change for unrelated prose during the read. It is disclosed,
    not used as an executable-identity or scientific-input predicate.
    """
    if type(before) is InstalledSourceAdmission and type(after) is InstalledSourceAdmission:
        if before != after:
            raise SourcePolicyError("selected installed candidate changed during source verification")
        return
    if type(before) is not CheckoutSourceAdmission or type(after) is not CheckoutSourceAdmission:
        raise TypeError("source stability requires exact source-admission observations")
    if (before.local_plan, before.selected_paths) != (after.local_plan, after.selected_paths):
        raise SourcePolicyError("selected source scope or disclosed local plan changed during source verification")


__all__ = ["CheckoutPathChange", "CheckoutSourceAdmission", "LOCAL_PLAN_NAME", "LocalPlanDisclosure", "SourcePolicyError",
           "MAINTAINED_ROOT_MARKDOWN", "ROOT_WORK_PLAN_NAMES", "NESTED_WORK_PLAN_PATHS", "WORK_PLAN_DIRECTORIES", "is_work_plan_path",
           "inspect_checkout_source", "require_unchanged_source_admission"]
