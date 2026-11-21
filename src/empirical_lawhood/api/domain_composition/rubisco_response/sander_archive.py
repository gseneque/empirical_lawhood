# SPDX-License-Identifier: MPL-2.0
"""Read original Amber SANDER jobs from an independently selected study ledger."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path

from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_sha256, validate_stable_id
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_census import FileHashCensus
from empirical_lawhood.storage.native_installation import real_path, verified_native_installation


@dataclass(frozen=True)
class SanderArchiveSelection:
    """Explicit locations for one original study and its selected tool installation."""

    ledger: Path
    ledger_sha256: str
    native_root: Path
    reference_root: Path
    installation: Path
    installation_manifest: Path
    installation_manifest_sha256: str


@dataclass(frozen=True, slots=True)
class SanderPrecursorPanel:
    """A selected material, seed roster and one issued job per seed and prepared origin."""

    panel_id: str
    material: str
    seeds: tuple[int, ...]
    coupled_jobs: tuple[str, ...]
    outer_jobs: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.panel_id, field_name="panel_id")
        if type(self.material) is not str or not self.material:
            raise ValueError("select the original SANDER material")
        if (type(self.seeds) is not tuple or not self.seeds or any(type(seed) is not int for seed in self.seeds)
                or len(set(self.seeds)) != len(self.seeds)):
            raise ValueError("select the complete distinct SANDER seed roster")
        for jobs in (self.coupled_jobs, self.outer_jobs):
            if type(jobs) is not tuple or len(jobs) != len(self.seeds):
                raise ValueError("select one issued job per seed for each precursor origin")
            for path in jobs:
                validate_relative_locator(path)
        if len(set(self.coupled_jobs + self.outer_jobs)) != 2 * len(self.seeds):
            raise ValueError("a precursor panel cannot reuse an issued job across assignments")

    @classmethod
    def from_file(cls, path):
        from empirical_lawhood.adapters._strict_json import loads_external_json

        document = loads_external_json(read_bounded_bytes(path, maximum_bytes=None))
        if type(document) is not dict or set(document) != {"panel_id", "material", "seeds", "coupled_jobs", "outer_jobs"}:
            raise ValueError("a precursor panel requires its exact material, seeds and two job rosters")
        if any(type(document[key]) is not list for key in ("seeds", "coupled_jobs", "outer_jobs")):
            raise ValueError("a precursor panel requires ordered JSON arrays for its rosters")
        return cls(document["panel_id"], document["material"], tuple(document["seeds"]),
                   tuple(document["coupled_jobs"]), tuple(document["outer_jobs"]))


@dataclass(frozen=True)
class SanderContinuation:
    """Select one original native parent and the length of its successor in integration steps."""

    parent_directory: str
    parent_receipt_sha256: str
    parent_restart_sha256: str
    steps: int

    def __post_init__(self):
        validate_relative_locator(self.parent_directory)
        validate_sha256(self.parent_receipt_sha256)
        validate_sha256(self.parent_restart_sha256)
        if type(self.steps) is not int or not 1 <= self.steps < 2**31:
            raise ValueError("invalid SANDER continuation step count")


def _member(root, name):
    return real_path(root / validate_relative_locator(name))


def _register(files, path, digest):
    path = real_path(path)
    if not isinstance(digest, str) or len(digest) != 64 or files.setdefault(path, digest) != digest:
        raise ValueError(f"conflicting or invalid SANDER source binding at {path}")


def _json(path, expected, limit):
    data = read_bounded_bytes(real_path(path), maximum_bytes=limit)
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"SANDER record differs from its selected digest at {path}")
    return json.loads(data)


def _sources(selection, ledger, root):
    files = {real_path(selection.ledger): selection.ledger_sha256}
    materials = {}
    for case, binding in ledger["selection_bindings"].items():
        directory = _member(root, case)
        if directory.parent != root:
            raise ValueError("SANDER material requires a single original directory name")
        spec_path = directory / "selection.json"
        spec = _json(spec_path, binding["sha256"], 4 * 1024**2)
        if spec != binding["selection"] or spec["case"] != case or spec["parent"]["case"] != case:
            raise ValueError("SANDER study and original material selections disagree")
        materials[case] = spec
        _register(files, spec_path, binding["sha256"])
        parents = spec["parent"]["checked_inputs"]
        if spec["topology"] not in parents or spec["atom_map"] not in parents:
            raise ValueError("SANDER material omits the source topology or atom map")
        for name, digest in parents.items():
            if not Path(name).is_absolute():
                raise ValueError("SANDER material requires its original absolute parent location")
            _register(files, name, digest)
        _register(files, Path(spec["atom_map"]).with_name("export.json"), spec["export_sha256"])
        _register(files, directory / "all_water_oxygens.npy", spec["all_water_oxygens_sha256"])
        for name, digest in spec["inputs"].items():
            _register(files, _member(selection.reference_root, name), digest)
        for origin, bindings in spec["conditioning_files"].items():
            for name, digest in bindings.items():
                _register(files, _member(_member(directory, origin), name), digest)
    jobs = {}
    for entry in ledger["issued_native_receipts"]:
        directory = _member(root, entry["directory"])
        if directory in jobs or directory.parent != _member(_member(root, entry["case"]), entry["origin"]):
            raise ValueError("SANDER ledger duplicates a job or changes its original material or origin")
        receipt = directory / "receipt.json"
        record = _json(receipt, entry["receipt_sha256"], 1024**2)
        if record != {k: v for k, v in entry.items() if k not in ("directory", "receipt_sha256")}:
            raise ValueError("SANDER ledger and issued native receipt disagree")
        _register(files, receipt, entry["receipt_sha256"])
        for name, digest in record["files"].items():
            path = _member(directory, name)
            if path.parent != directory or name == "receipt.json":
                raise ValueError("SANDER receipt contains an invalid native member")
            _register(files, path, digest)
        jobs[directory] = record
    if not jobs:
        raise ValueError("SANDER archive requires its issued native jobs")
    return files, materials, jobs


def _recheck(root, files, jobs, *, issued_directories):
    if {path.parent for path in root.rglob("receipt.json")} != issued_directories:
        raise ValueError("SANDER native receipt census differs from the selected ledger")
    for directory, job in jobs.items():
        if {p.name for p in directory.iterdir()} != {"receipt.json", *job["files"]}:
            raise ValueError(f"SANDER native member census changed at {directory}")
    with FileHashCensus() as census:
        for path, expected in files.items():
            if census.sha256(real_path(path), maximum_bytes=None)[1] != expected:
                raise ValueError(f"SANDER native member or original source changed at {path}")


def _issued_ancestors(root, ledger, directory):
    issued = {_member(root, row["directory"]): row for row in ledger["issued_native_receipts"]}
    if len(issued) != len(ledger["issued_native_receipts"]):
        raise ValueError("SANDER ledger repeats an issued directory")
    chain = {}
    current = directory
    while current not in chain:
        if current not in issued:
            raise ValueError("SANDER continuation lacks an issued parent")
        row = chain[current] = issued[current]
        start = Path(row["start"])
        if start.name == "start.rst7":
            break
        if start.name != "final.ncrst" or not start.is_relative_to(root):
            raise ValueError("SANDER continuation leaves its original restart ancestry")
        current = start.parent
    else:
        raise ValueError("SANDER continuation contains a restart cycle")
    case = chain[directory]["case"]
    if any(row["case"] != case for row in chain.values()):
        raise ValueError("SANDER continuation crosses original materials")
    subset = dict(ledger, selection_bindings={case: ledger["selection_bindings"][case]},
                  issued_native_receipts=list(chain.values()))
    return subset, issued.keys()


@contextmanager
def _verified_sources(selection, *, parent_directory=None):
    root = real_path(selection.native_root)
    ledger = _json(selection.ledger, selection.ledger_sha256, 64 * 1024**2)
    if root != Path(ledger["native_root"]):
        raise ValueError("SANDER ledger requires its original selected storage root")
    with verified_native_installation(selection.installation, manifest_path=selection.installation_manifest,
                                      manifest_sha256=selection.installation_manifest_sha256) as installation:
        engine = json.loads(read_bounded_bytes(selection.installation_manifest, maximum_bytes=4 * 1024**2))
        original_digest = engine["original_installation_manifest_sha256"]
        if (engine["executable"] != "bin/sander"
                or not any(row["path"] == "manifest.json" and row["sha256"] == original_digest for row in engine["files"])):
            raise ValueError("SANDER installation does not bind the original engine manifest")
        selected = ledger
        issued = None
        if parent_directory is not None:
            selected, issued = _issued_ancestors(root, ledger, _member(root, parent_directory))
        files, materials, jobs = _sources(selection, selected, root)
        if issued is None:
            issued = jobs.keys()
        _recheck(root, files, jobs, issued_directories=issued)
        try:
            digests = {case: binding["sha256"] for case, binding in selected["selection_bindings"].items()}
            yield root, selected, original_digest, installation, materials, digests, jobs
        finally:
            _recheck(root, files, jobs, issued_directories=issued)


def _assess_panel(panel, rows):
    from empirical_lawhood.domains.rubisco.rubisco_response.precursor_occupancy import PrecursorReleasePath, assess_precursor_origins

    origins = {}
    protocols = set()
    for origin, directories in (("coupled", panel.coupled_jobs), ("outer", panel.outer_jobs)):
        paths = []
        for seed, directory in zip(panel.seeds, directories, strict=True):
            row = rows.get(directory)
            if (row is None or row["stage"] not in ("release", "release_mmshake")
                    or (row["case"], row["origin"], row["seed"]) != (panel.material, origin, seed)):
                raise ValueError("a selected precursor job differs from its issued material, origin, seed or stage")
            protocols.add((row["stage"], row["release_settings_sha256"]))
            paths.append(PrecursorReleasePath.from_release(row))
        origins[origin] = paths
    if len(protocols) != 1:
        raise ValueError("a precursor panel combines different release methods or numerical settings")
    stage, settings = protocols.pop()
    assessment = assess_precursor_origins(panel.material, seeds=panel.seeds, **origins)
    return dict(material=panel.material, seeds=list(panel.seeds), coupled_jobs=list(panel.coupled_jobs),
                outer_jobs=list(panel.outer_jobs), stage=stage, release_settings_sha256=settings, **assessment)


def read_sander_release_archive(selection: SanderArchiveSelection, *, precursor_panels: tuple[SanderPrecursorPanel, ...] = ()):
    """Authenticate every issued job, then reconstruct its retained release observations."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.sander_returns import read_sander_jobs

    if (type(precursor_panels) is not tuple or any(type(panel) is not SanderPrecursorPanel for panel in precursor_panels)
            or len({panel.panel_id for panel in precursor_panels}) != len(precursor_panels)):
        raise ValueError("select a tuple of uniquely named SANDER precursor panels")
    with _verified_sources(selection) as (root, ledger, original_digest, installation, materials, material_digests, jobs):
        rows = read_sander_jobs(root, original_digest, materials, material_digests, jobs, real_path(selection.reference_root))
        for case, force in ledger.get("native_proton_force_checks", {}).items():
            measured = [row for row in rows.values() if row["case"] == case and row["stage"] == "forcecheck"]
            if len(measured) != 1:
                raise ValueError("SANDER force control differs from the original material census")
            diagnostic = measured[0]["force_diagnostic"]
            if (measured[0]["native_exit"] != force["native_exit"] or diagnostic["atom_one_based"] != force["native_atom"]
                    or diagnostic["relative_rms_error"] != force["native_relative_RMS_force_error"]
                    or diagnostic["components_numeric_analytic_difference"] != force["components_numeric_analytic_difference"]):
                raise ValueError("SANDER force diagnostic differs from its original numerical operands")
        stages = Counter(job["stage"] for job in jobs.values())
        if stages != {stage: item["calls"] for stage, item in ledger["by_stage"].items()}:
            raise ValueError("SANDER stage counts differ from the issued cost ledger")
        cpu_seconds = sum(job["actual_cpu_s"] for job in jobs.values())
        wall_seconds = sum(job["wall_s"] for job in jobs.values())
        if (abs(cpu_seconds - ledger["total_native_cpu_s"]) > 0.011
                or abs(wall_seconds - ledger["total_summed_native_wall_s"]) > 0.011):
            raise ValueError("SANDER native cost differs from the original ledger")
        report = dict(ledger_sha256=selection.ledger_sha256, installation=installation, jobs=rows,
                    cpu_seconds=cpu_seconds, summed_native_wall_seconds=wall_seconds, new_native_calls=0,
                    scope="Original gas-free SANDER preparations and conditional trajectories.")
        if precursor_panels:
            report["precursor_panels"] = {panel.panel_id: _assess_panel(panel, rows) for panel in precursor_panels}
        return report


@contextmanager
def _continuation(selection, request):
    from empirical_lawhood.adapters.rubisco.rubisco_response.sander_returns import continuation_controls

    with _verified_sources(selection, parent_directory=request.parent_directory) as source:
        root, ledger, engine, installation, materials, digests, jobs = source
        directory = _member(root, request.parent_directory)
        parent = jobs[directory]
        entry = next(row for row in ledger["issued_native_receipts"] if row["directory"] == request.parent_directory)
        if (entry["receipt_sha256"] != request.parent_receipt_sha256
                or parent["files"].get("final.ncrst") != request.parent_restart_sha256):
            raise ValueError("SANDER continuation changes the selected parent receipt or restart")
        case = parent["case"]
        material = materials[case]
        control, start, thermostat = continuation_controls(root, directory, jobs, material, engine,
                                                           digests[case], request.steps)
        info = dict(parent_directory=request.parent_directory, parent_receipt_sha256=request.parent_receipt_sha256,
                    start_sha256=request.parent_restart_sha256, ledger_sha256=selection.ledger_sha256,
                    installation_manifest_sha256=installation["manifest_sha256"], engine_manifest_sha256=engine,
                    topology_sha256=parent["topology_sha256"], material_sha256=digests[case], case=case,
                    origin=parent["origin"], stage=parent["stage"], seed=parent["seed"], thermostat_seed=thermostat,
                    electronic_temperature_K=parent.get("electronic_temperature_K"), stride=parent["stride"],
                    initial_step=start, steps=request.steps, cumulative_steps=start + request.steps,
                    control_sha256=sha256(control).hexdigest())
        info["expected_coordinate_frames"] = request.steps // parent["stride"]
        info["expected_force_frames"] = request.steps // min(request.steps, 5 * parent["stride"])
        yield info, control, material, directory / "final.ncrst"


def prepare_sander_continuation(selection: SanderArchiveSelection, request: SanderContinuation):
    """Verify the complete parent chain and return the successor's input identities without native entry."""
    with _continuation(selection, request) as (info, _, _, _):
        return dict(info, new_native_calls=0)


def run_sander_continuation(selection: SanderArchiveSelection, request: SanderContinuation, *,
                            output: Path, timeout_seconds: float):
    """Execute once in fresh operator-selected storage through final source and native-output verification."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.sander_execution import execute_continuation

    directory = real_path(output)
    if type(timeout_seconds) not in (float, int) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("select a finite positive SANDER deadline")
    if not directory.parent.is_dir() or any(directory.is_relative_to(real_path(p)) for p in
                                           (selection.native_root, selection.installation)):
        raise ValueError("select an existing output parent outside the original SANDER sources")
    entered = False
    try:
        with _continuation(selection, request) as (info, control, material, restart):
            directory.mkdir()
            entered = True
            result = execute_continuation(info, control, material, restart, real_path(selection.installation),
                                          directory, timeout_seconds)
    except BaseException as exc:
        if entered:
            with (directory / "return.json").open("x") as stream:
                json.dump(dict(info, status="interrupted" if isinstance(exc, (SystemExit, KeyboardInterrupt)) else "failed",
                               returned_coordinate_frames=None, returned_force_frames=None,
                               error_type=type(exc).__name__, reason=str(exc)), stream, sort_keys=True)
        raise
    with (directory / "return.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, allow_nan=False)
    return result
