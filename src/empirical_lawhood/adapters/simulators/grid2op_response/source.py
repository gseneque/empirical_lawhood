"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import bz2
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from empirical_lawhood.science.records.serialization import require_sorted_unique_strings, validate_sha256
from empirical_lawhood.domains.energy.grid2op.contracts import Grid2OpChronicBinding, Grid2OpSourceBinding

_EXOGENOUS_FILENAMES = (
    "hazards.csv.bz2",
    "load_p.csv.bz2",
    "load_q.csv.bz2",
    "maintenance.csv.bz2",
    "prod_p.csv.bz2",
    "prod_v.csv.bz2",
)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 * 1024**2):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_sha256(root: Path, *, selected_names: set[str] | None = None) -> str:
    digest = sha256()
    members = tuple(
        sorted(
            path
            for path in root.iterdir()
            if path.is_file() and (selected_names is None or path.name in selected_names)
        )
    )
    if not members:
        raise ValueError("Grid2Op chronic has no bounded source members")
    for path in members:
        relative = path.name.encode("utf-8")
        content = _sha256_file(path).encode("ascii")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(path.stat().st_size.to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _timestep_seconds(path: Path) -> int:
    value = path.read_text(encoding="ascii").strip()
    parsed = datetime.strptime(value, "%H:%M").replace(tzinfo=UTC)
    seconds = parsed.hour * 3600 + parsed.minute * 60 + parsed.second
    if seconds <= 0:
        raise ValueError("Grid2Op chronic timestep is not positive")
    return seconds


def _maximum_steps(path: Path) -> int:
    with bz2.open(path, "rt", encoding="utf-8", errors="strict", newline="") as source:
        rows = sum(1 for _line in source)
    # One header and one reset observation precede the maximum action-step count.
    maximum = rows - 2
    if maximum <= 0:
        raise ValueError("Grid2Op chronic has no executable steps")
    return maximum


def _chronic_binding(root: Path, native_id: str) -> Grid2OpChronicBinding:
    if root.name != native_id or not root.is_dir():
        raise ValueError("Grid2Op chronic locator differs from its native identity")
    timestep = _timestep_seconds(root / "time_interval.info")
    start = datetime.strptime(
        (root / "start_datetime.info").read_text(encoding="ascii").strip(),
        "%Y-%m-%d %H:%M",
    ).replace(tzinfo=UTC)
    initial = start + timedelta(seconds=timestep)
    exogenous_names = {value for value in _EXOGENOUS_FILENAMES if (root / value).is_file()}
    required = {"load_p.csv.bz2", "load_q.csv.bz2", "prod_p.csv.bz2", "prod_v.csv.bz2"}
    if not required <= exogenous_names:
        raise ValueError("Grid2Op chronic lacks its exact exogenous state files")
    forecast_names = {
        "load_p_forecasted.csv.bz2",
        "load_q_forecasted.csv.bz2",
        "prod_p_forecasted.csv.bz2",
        "prod_v_forecasted.csv.bz2",
    }
    return Grid2OpChronicBinding(
        chronic_id=f"chronic.grid2op.{native_id}",
        native_chronic_id=native_id,
        content_sha256=_tree_sha256(root),
        initial_timestamp_utc=initial.strftime("%Y-%m-%dT%H:%M:%SZ"),
        timestep_seconds=timestep,
        maximum_steps=_maximum_steps(root / "load_p.csv.bz2"),
        exogenous_event_sha256=_tree_sha256(root, selected_names=exogenous_names),
        forecasts_available=all((root / value).is_file() for value in forecast_names),
    )


def build_held_grid2op_source_binding(
    *,
    binding_id: str,
    grid2op_version: str,
    grid2op_wheel: Path,
    backend_version: str,
    backend_wheel: Path,
    dataset_path: Path,
    native_chronic_ids: tuple[str, ...],
    observation_operator_sha256: str,
    fresh_target_identity_disjoint: bool,
) -> Grid2OpSourceBinding:
    """Inventory exact held bytes without importing or executing Grid2Op."""

    validate_sha256(
        observation_operator_sha256,
        field_name="observation_operator_sha256",
    )
    require_sorted_unique_strings(
        native_chronic_ids,
        field_name="native_chronic_ids",
        allow_empty=False,
    )
    for path in (grid2op_wheel, backend_wheel, dataset_path):
        if not path.is_absolute() or not path.exists():
            raise ValueError("Grid2Op held source locator is absent or relative")
    chronics_root = dataset_path / "chronics"
    chronics = tuple(
        _chronic_binding(chronics_root / native_id, native_id) for native_id in native_chronic_ids
    )
    return Grid2OpSourceBinding(
        binding_id=binding_id,
        grid2op_version=grid2op_version,
        package_source_sha256=_sha256_file(grid2op_wheel),
        environment_name=dataset_path.name,
        backend_class_id="lightsim2grid.LightSimBackend",
        backend_version=backend_version,
        backend_source_sha256=_sha256_file(backend_wheel),
        grid_sha256=_sha256_file(dataset_path / "grid.json"),
        rules_class_id="grid2op.Rules.DefaultRules",
        parameters_sha256=_sha256_file(dataset_path / "config.py"),
        action_class_id="grid2op.Action.TopologyAndDispatchAction",
        observation_class_id="grid2op.Observation.CompleteObservation",
        observation_operator_sha256=observation_operator_sha256,
        chronic_handler_class_id="grid2op.Chronics.Multifolder",
        chronic_bindings=chronics,
        reward_ignored=True,
        source_network_required=False,
        fresh_target_identity_disjoint=fresh_target_identity_disjoint,
    )
