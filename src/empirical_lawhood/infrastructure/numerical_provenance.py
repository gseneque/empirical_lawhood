# SPDX-License-Identifier: MPL-2.0
"""Observe selected producing source/environment without scientific admissibility.

Observation authenticates the selected implementation, not a domain's numerical
support. Registered requirements and independent domain assessors own that claim.
"""

from hashlib import sha256
from pathlib import Path
import json
import os
import stat
import sys

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.bounded_process import run_bounded_command
from empirical_lawhood.infrastructure.source_policy import NESTED_WORK_PLAN_PATHS
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment


WORKER_ENVIRONMENT_DEFAULTS = {
    "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1", "PYTHONHASHSEED": "0",
}
WORKER_ENVIRONMENT_OPTIONAL = (
    "OPENBLAS_CORETYPE", "NPY_DISABLE_CPU_FEATURES", "OPENMM_CPU_THREADS",
    "PYBAMM_DISABLE_TELEMETRY", "KMP_DUPLICATE_LIB_OK", "CASADIPATH",
)


def numerical_observer_environment(environment):
    """Select the locked observer's import setting before any child launches.

    The selected threadpoolctl imports set this default in the process. Bind it
    before hashing the complete environment, retaining an explicitly supplied
    value and refusing all later unselected changes through the existing gate.
    """
    if type(environment) is not dict or any(type(name) is not str or type(value) is not str
            for name, value in environment.items()):
        raise ValueError("numerical observation requires an exact string environment")
    selected = dict(environment)
    selected.setdefault("KMP_DUPLICATE_LIB_OK", "True")
    return selected


def selected_worker_environment():
    """Code-owned post-sanitize settings; preserve explicitly selected CPU masks."""
    return tuple(sorted(numerical_observer_environment({**WORKER_ENVIRONMENT_DEFAULTS, **{
        name: os.environ[name] for name in WORKER_ENVIRONMENT_OPTIONAL if name in os.environ}}).items()))


def observe_worker_environment(*, selected_environment=None):
    """Observe this actual interpreter and settings without domain inference."""
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256

    names = tuple(name for name, _ in selected_environment) if selected_environment is not None else (
        *WORKER_ENVIRONMENT_DEFAULTS, *WORKER_ENVIRONMENT_OPTIONAL)
    return PreparedWorkerEnvironment(str(Path(sys.executable).absolute()),
        bounded_file_sha256(Path(sys.executable).resolve(), maximum_bytes=None)[1],
        str(Path(sys.prefix).absolute()), tuple(sorted((name, os.environ[name])
            for name in names if name in os.environ)))


def observe_prepared_worker(contract, provenance_requirements=(), *, prefix_selected=True):
    """Observe the actual selected worker, including a specialist interpreter.

    Input transport and domain operand joins remain with their existing owners.
    This observation does not infer a domain's admissibility from a main profile.
    """
    from empirical_lawhood.runtime.prepared_native_invocation import WorkerPreflightMismatch

    provenance = environment = None
    mismatches = []
    if type(prefix_selected) is not bool:
        raise ValueError("worker prefix selection requires its explicit diagnostic disposition")
    if not prefix_selected:
        mismatches.append(WorkerPreflightMismatch("worker.prefix", "selected specialist prefix is not yet bound"))
    try:
        environment = observe_worker_environment(selected_environment=contract.environment.selected_environment)
        from dataclasses import replace
        expected = contract.environment if prefix_selected else replace(contract.environment, prefix=environment.prefix)
        if environment != expected:
            raise ValueError("actual worker interpreter, prefix or selected environment differs")
    except Exception as error:  # noqa: BLE001 - preserve all independent prerequisites
        mismatches.append(WorkerPreflightMismatch("worker.environment", str(error) or type(error).__name__))
    try:
        import empirical_lawhood

        package_root = Path(empirical_lawhood.__file__).resolve().parent
        project_root = package_root.parent.parent if package_root.parent.name == "src" else None
        provenance = capture_numerical_provenance(project_root=project_root,
            expected_code_sha256=contract.implementation.code_sources_sha256,
            expected_lock_sha256=contract.implementation.dependency_lock_sha256)
        if (provenance.package_sources, provenance.observed_git_head) != (
                contract.implementation.package_sources, contract.implementation.observed_git_head):
            raise ValueError("actual worker changes its frozen package inventory or Git identity")
    except Exception as error:  # noqa: BLE001 - preserve the source and runtime census
        mismatches.append(WorkerPreflightMismatch("worker.implementation", str(error) or type(error).__name__))
    if tuple(sorted(row.requirement_id for row in provenance_requirements)) != contract.provenance_requirement_ids:
        mismatches.append(WorkerPreflightMismatch("worker.provenance", "installed numerical predicate census differs"))
    elif provenance is not None:
        for requirement in provenance_requirements:
            try:
                if requirement.validate_observation(provenance) is not None:
                    raise ValueError("numerical predicate must return None or refuse")
            except Exception as error:  # noqa: BLE001 - report each selected predicate
                mismatches.append(WorkerPreflightMismatch(requirement.requirement_id,
                    str(error) or type(error).__name__))
    return provenance, environment, tuple(mismatches)


def immutable_json(value):
    if isinstance(value, (list, tuple)):
        return tuple(immutable_json(item) for item in value)
    if isinstance(value, dict):
        return {key: immutable_json(item) for key, item in value.items()}
    return value


def numerical_package_sources(package_root=None):
    """Exact package census; omit caches and explicit nonexecutable archival plans."""
    root = Path(__file__).parents[1] if package_root is None else Path(package_root)
    entries = []
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.relative_to(root).parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            raise ValueError("Numerical package source inventory refuses symbolic links")
        if "src/empirical_lawhood/" + path.relative_to(root).as_posix() in NESTED_WORK_PLAN_PATHS:
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111:
                raise ValueError("excluded work plans must be regular non-executable files")
            continue
        if path.is_file():
            entries.append((path.relative_to(root).as_posix(),
                            sha256(read_bounded_bytes(path, maximum_bytes=None)).hexdigest()))
    if not entries:
        raise ValueError("Numerical producing package is empty")
    return tuple(entries)


def numerical_package_code_sha256():
    return sha256(canonical_json_bytes(numerical_package_sources())).hexdigest()


def selected_dependency_lock_sha256(project_root):
    return sha256(read_bounded_bytes(Path(project_root) / "uv.lock", maximum_bytes=None)).hexdigest()


def numerical_runtime_observation():
    """Actual loaded runtime, with no inferred scientific validity."""
    import platform
    import numpy as np
    import scipy
    from threadpoolctl import threadpool_info

    # Loaded-library enumeration order is process-local, not runtime identity.
    # Keep every complete observation (including duplicates and unknown fields).
    pools = sorted(threadpool_info(), key=canonical_json_bytes)
    return immutable_json({"python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "system": sys.platform, "machine": platform.machine(),
        "threadpools": pools})



def _admitted_implementation_source(project_root, source):
    """Project an actual operation's admitted census, without granting freshness.

    Entry/final owners retain complete current byte and membership guards. This
    private projection adds no permission or source-admission verdict.
    """
    from empirical_lawhood.infrastructure.source_closure import AdmittedTargetSource, TrackedSourceMember
    from empirical_lawhood.infrastructure.source_policy import CheckoutSourceAdmission, InstalledSourceAdmission, is_work_plan_path
    from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_sha256

    if project_root is None or type(source) is not AdmittedTargetSource:
        raise TypeError("admitted source projection requires its exact operation source and explicit selected root")
    root = Path(project_root).resolve(strict=True)
    if (type(source.tracked_files) is not tuple or not source.tracked_files
            or any(type(member) is not TrackedSourceMember for member in source.tracked_files)):
        raise TypeError("admitted source projection requires its complete immutable tracked census")
    names = tuple(member.relative_path for member in source.tracked_files)
    if names != tuple(sorted(set(names))):
        raise ValueError("admitted source projection changes complete sorted unique source membership")
    by_name = {member.relative_path: member for member in source.tracked_files}
    required = {name for name in names if name.startswith(("src/empirical_lawhood/", "scripts/"))
        and not is_work_plan_path(name)} | {"pyproject.toml", "uv.lock"}
    for admission in (source.source_admission, source.final_source_admission):
        if type(admission) not in (CheckoutSourceAdmission, InstalledSourceAdmission):
            raise TypeError("admitted source projection requires its exact checkout or installed source observation")
        admission.__post_init__()
        selected = {name for name in admission.selected_paths
            if name in ("pyproject.toml", "uv.lock") or name.startswith(("src/empirical_lawhood/", "scripts/"))
            and not is_work_plan_path(name)}
        if selected != required:
            raise ValueError("partial admitted source census or scope cannot project the complete selected candidate")
    if type(source.source_admission) is not type(source.final_source_admission):
        raise TypeError("admitted source projection changes its checkout or installed source kind")
    for name in required:
        member = by_name.get(name)
        if (member is None or member.mode not in ("100644", "100755")
                or type(member.size_bytes) is not int or member.size_bytes < 0):
            raise ValueError("admitted source projection loses a selected package, script, build or lock operand")
        validate_relative_locator(name)
        validate_sha256(member.sha256)
    prefix = "src/empirical_lawhood/"
    rows = tuple(sorted((name[len(prefix):], member.sha256) for name, member in by_name.items()
        if name.startswith(prefix) and name not in NESTED_WORK_PLAN_PATHS
        and "__pycache__" not in Path(name).parts and Path(name).suffix not in (".pyc", ".pyo")))
    if not rows:
        raise ValueError("admitted source projection loses its complete package census")
    clean = False
    if type(source.final_source_admission) is CheckoutSourceAdmission:
        observed = run_bounded_command(("git", "status", "--porcelain"), cwd=root,
            timeout_seconds=5, maximum_stdout_bytes=1024**2, maximum_stderr_bytes=4096)
        if observed.returncode:
            raise ValueError("Numerical producing checkout Git observation failed")
        clean = not bool(observed.stdout.strip())
    return rows, sha256(canonical_json_bytes(rows)).hexdigest(), by_name["uv.lock"].sha256, source.implementation_commit, clean


def observe_implementation_source(project_root=None, *, _admitted_source=None):
    """Observe current source, or project an explicitly admitted operation census."""
    if _admitted_source is not None:
        return _admitted_implementation_source(project_root, _admitted_source)
    import empirical_lawhood
    package_root = Path(empirical_lawhood.__file__).resolve().parent
    root = None if project_root is None else Path(project_root).resolve(strict=True)
    if root is None or package_root != root / "src/empirical_lawhood":
        from empirical_lawhood.infrastructure.selected_candidate import installed_candidate

        candidate = installed_candidate(source_root=root)
        rows, code, lock = candidate.package_sources, candidate.code_sources_sha256, candidate.dependency_lock_sha256
        # The retained field names preserve the canonical scientific contract:
        # source commit comes from the build, and no checkout is observed here.
        return rows, code, lock, candidate.implementation_commit, False
    for name, module in tuple(sys.modules.items()):
        if name == "empirical_lawhood" or name.startswith("empirical_lawhood."):
            origin = getattr(module, "__file__", None)
            if origin and origin.endswith(".py") and not Path(origin).resolve().is_relative_to(package_root):
                raise ValueError("Numerical provenance loaded module differs from selected checkout")

    def git(*args):
        result = run_bounded_command(("git", *args), cwd=root, timeout_seconds=5,
                                     maximum_stdout_bytes=1024**2, maximum_stderr_bytes=4096)
        if result.returncode:
            raise ValueError("Numerical producing checkout Git observation failed")
        return result.stdout.decode().strip()

    if Path(git("rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("Numerical provenance requires the selected checkout root")
    rows = numerical_package_sources(package_root)
    code = sha256(canonical_json_bytes(rows)).hexdigest()
    lock = selected_dependency_lock_sha256(root)
    return rows, code, lock, git("rev-parse", "HEAD"), not bool(git("status", "--porcelain"))


def capture_numerical_provenance(*, project_root=None, expected_code_sha256=None, expected_lock_sha256=None,
        _admitted_source=None):
    rows, code, lock, head, clean = (observe_implementation_source(project_root) if _admitted_source is None else
        observe_implementation_source(project_root, _admitted_source=_admitted_source))
    if expected_code_sha256 is not None and code != expected_code_sha256:
        raise ValueError("Numerical producing code/source bytes changed after input preparation")
    if expected_lock_sha256 is not None and lock != expected_lock_sha256:
        raise ValueError("Numerical selected dependency lock changed after input preparation")
    return NumericalProducingProvenance(canonical_json_bytes(numerical_runtime_observation()).decode(),
        lock, rows, code, head, clean)


def authenticate_recorded_numerical_provenance(provenance):
    """Read producing evidence without observing the reader's environment."""
    if type(provenance) is not NumericalProducingProvenance:
        raise ValueError("Exact numerical producing provenance is required")
    provenance.__post_init__()
    value = json.loads(provenance.runtime_observation_json)
    if canonical_json_bytes(immutable_json(value)).decode() != provenance.runtime_observation_json:
        raise ValueError("Numerical runtime observation requires exact canonical JSON")
    if not isinstance(value["threadpools"], list):
        raise ValueError("Numerical runtime observation omits its complete loaded pool census")
    return provenance
