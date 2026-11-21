"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import SOLVER_TOLERANCE as _science_SOLVER_TOLERANCE, map_coil_currents, assess_static_equilibrium
from collections.abc import Mapping
import contextlib
import hashlib
import io
from pathlib import Path
import pickle
import sys
import time
from typing import Any, Final, cast
import zipfile
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.contracts import StaticTransportDisposition, StaticTransportGateReceipt

from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import (
    StaticTransportError as _science_StaticTransportError,
    preparation_arrays as _science_preparation_arrays,
    receiver_arrays as _science_receiver_arrays,
)

from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import COORDINATES as _science_COORDINATES, MACHINE_ARCHIVE_SHA256 as _science_MACHINE_ARCHIVE_SHA256, SHOT_MEMBERS as _science_SHOT_MEMBERS, SLICE_TIMES_S as _science_SLICE_TIMES_S, VIEWS as _science_VIEWS


TRACE_ARCHIVE_SHA256: Final = "31c1ffacde84db094c91d143d027927746f2778bd5a2bb921140de5a07349bee"



MACHINE_MEMBERS: Final = {
    "active": (
        "MAST-U_active_coils_nonsym.pickle",
        "bc38cf8641e36e8bbba9a7349c0017a6042357aa586b8a7fcbede90846c88d40",
    ),
    "active-symmetric": (
        "MAST-U_active_coils.pickle",
        "5c5cc1da422fdf43f04639c85e97936dc4a68b00cfdda5a1078d426970e84c94",
    ),
    "limiter": (
        "MAST-U_limiter.pickle",
        "e1903bf8b6931e31909b31c9a6ac8a69921b2b28c526cd28c45303a914e2af7f",
    ),
    "probes": (
        "MAST-U_magnetic_probes.pickle",
        "d7c1814d67ef94e7b194aa4bb50b43e1a572ee41208396b170b4aac7c72e9f76",
    ),
    "passive": (
        "MAST-U_passive_coils.pickle",
        "76ae3e588318e60fab2a8b42ef4337e92786507541667992495156bf0c28b85b",
    ),
    "wall": (
        "MAST-U_wall.pickle",
        "e1903bf8b6931e31909b31c9a6ac8a69921b2b28c526cd28c45303a914e2af7f",
    ),
}









def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _verify_archive(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise _science_StaticTransportError(f"archive is absent or unsafe: {path}")
    if sha256_file(path) != expected_sha256:
        raise _science_StaticTransportError(f"archive digest differs: {path}")

def _member_bytes(
    archive: Path,
    archive_sha256: str,
    member: str,
    member_sha256: str,
) -> bytes:
    _verify_archive(archive, archive_sha256)
    with zipfile.ZipFile(archive) as source:
        info = source.getinfo(member)
        if info.file_size > 100_000_000 or info.flag_bits & 0x1:
            raise _science_StaticTransportError("selected archive member violates its bound")
        payload = source.read(info)
    if hashlib.sha256(payload).hexdigest() != member_sha256:
        raise _science_StaticTransportError(f"member digest differs: {member}")
    return payload

def publish_bytes(path: Path, payload: bytes) -> None:
    """No-replace publication with byte-exact idempotent recovery."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != payload:
            raise _science_StaticTransportError(f"no-replace publication conflict: {path}")
        return
    temporary = path.with_name(f".{path.name}.partial")
    if temporary.exists():
        raise _science_StaticTransportError(f"ambiguous partial publication: {temporary}")
    temporary.write_bytes(payload)
    temporary.replace(path)

def publish_record(path: Path, record: object) -> None:
    canonical_bytes = getattr(record, "canonical_bytes", None)
    if canonical_bytes is None:
        raise TypeError("published record must be canonical")
    publish_bytes(path, cast(bytes, canonical_bytes()))

def artifact_identity(
    path: Path,
    *,
    artifact_id: str,
    role: str,
    payload_schema: str,
    media_type: str,
) -> ArtifactIdentity:
    return ArtifactIdentity(
        artifact_id=artifact_id,
        role=role,
        payload_schema=payload_schema,
        sha256=sha256_file(path),
        media_type=media_type,
        size_bytes=path.stat().st_size,
    )

def _deterministic_npz_bytes(arrays: Mapping[str, NDArray[np.generic]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(arrays):
            member = io.BytesIO()
            np.lib.format.write_array(member, np.asarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, member.getvalue())
    return output.getvalue()

def _read_npz(path: Path) -> dict[str, NDArray[np.generic]]:
    with np.load(path, allow_pickle=False) as payload:
        return {name: np.asarray(payload[name]) for name in payload.files}

def fair_metadata_canary(metadata_root: Path) -> StaticTransportGateReceipt:
    """Inspect FAIR-MAST metadata only; never open a signal value object."""

    import pyarrow.parquet as parquet  # type: ignore[import-untyped]

    shots_path = metadata_root / "shots.parquet"
    sources_path = metadata_root / "sources.parquet"
    if not shots_path.is_file() or not sources_path.is_file():
        raise _science_StaticTransportError("pinned FAIR-MAST metadata snapshot is absent")
    shots = parquet.read_table(shots_path, columns=["shot_id", "facility"])
    sources = parquet.read_table(sources_path, columns=["shot_id", "name", "quality"])
    shot_ids = {str(value) for value in shots.column("shot_id").to_pylist()}
    source_rows = sources.to_pylist()
    source_names = {str(row["name"]) for row in source_rows}
    quality_values = {str(row["quality"]) for row in source_rows}
    # These required declarations are absent globally from the pinned schema.
    required = {
        "active_pf_order_unit_sign": False,
        "equilibrium_clock_and_validity": False,
        "geometry_identity": False,
        "magnetic_receiver_unit_and_clock": False,
        "passive_current_representation": False,
        "profile_preparation_semantics": False,
        "source_quality_qualified": quality_values == {"Checked"},
    }
    eligible = len(shot_ids) if all(required.values()) else 0
    reasons = (
        "FAIR_SOURCE_UNQUALIFIED",
        "GEOMETRY_IDENTITY_ABSENT",
        "PASSIVE_CURRENT_REPRESENTATION_ABSENT",
        "PROFILE_PREPARATION_SEMANTICS_ABSENT",
        "RECEIVER_UNIT_CLOCK_UNQUALIFIED",
        "SOURCE_QUALITY_NOT_CHECKED",
    )
    return StaticTransportGateReceipt(
        receipt_id="receipt.mast-static.fair-metadata-canary",
        gate_id="gate.f0",
        disposition=StaticTransportDisposition.STOPPED,
        reason_codes=tuple(sorted(reasons)),
        facts={
            "eligible_shot_count": eligible,
            "minimum_required_shot_count": 24,
            "receiver_value_read_count": 0,
            "route_selected": "ROUTE_U_26M5_JMPP",
            "shot_metadata_row_count": shots.num_rows,
            "source_metadata_row_count": sources.num_rows,
            "source_names": tuple(sorted(source_names)),
            "required_declarations": required,
        },
        artifacts=tuple(
            sorted(
                (
                    artifact_identity(
                        shots_path,
                        artifact_id="artifact.fair-mast.shots-metadata",
                        role="source-metadata",
                        payload_schema='empirical-lawhood/physical/mast-freegsnke-static-transport/archive-shot-metadata',
                        media_type="application/vnd.apache.parquet",
                    ),
                    artifact_identity(
                        sources_path,
                        artifact_id="artifact.fair-mast.sources-metadata",
                        role="source-metadata",
                        payload_schema='empirical-lawhood/physical/mast-freegsnke-static-transport/archive-source-metadata',
                        media_type="application/vnd.apache.parquet",
                    ),
                ),
                key=lambda value: value.artifact_id,
            )
        ),
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
    )

def _shot_payload(shot_id: str, *, trace_archive: Path) -> dict[str, object]:
    member, digest = _science_SHOT_MEMBERS[shot_id]
    payload = _member_bytes(trace_archive, TRACE_ARCHIVE_SHA256, member, digest)
    loaded = pickle.loads(payload)  # noqa: S301 - exact trusted public release, owner accepted
    if not isinstance(loaded, dict) or int(loaded.get("shot_number", -1)) != int(shot_id):
        raise _science_StaticTransportError("selected shot payload differs from its identity")
    return cast(dict[str, object], loaded)

def materialize_shot(
    shot_id: str,
    *,
    role: str,
    destination: Path,
    trace_archive: Path,
) -> ArtifactIdentity:
    if role not in {"preparation", "receiver"}:
        raise ValueError("shot role must be preparation or receiver")
    value = _shot_payload(shot_id, trace_archive=trace_archive)
    arrays = _science_preparation_arrays(value) if role == "preparation" else _science_receiver_arrays(value)
    publish_bytes(destination, _deterministic_npz_bytes(arrays))
    return artifact_identity(
        destination,
        artifact_id=f"artifact.mastu-shot-{shot_id}.{role}",
        role=f"mastu-{role}",
        payload_schema=f'empirical-lawhood/physical/mast-freegsnke-static-transport/{role}-arrays',
        media_type="application/x-npz",
    )

def _machine_configuration(machine_archive: Path) -> dict[str, object]:
    values: dict[str, object] = {}
    for role, (member, expected) in MACHINE_MEMBERS.items():
        payload = _member_bytes(machine_archive, _science_MACHINE_ARCHIVE_SHA256, member, expected)
        values[role] = pickle.loads(payload)  # noqa: S301 - exact trusted public release
    return values

def _build_tokamak(machine: Mapping[str, object], coordinate_id: str) -> Any:
    from freegsnke import build_machine  # type: ignore[import-untyped]

    active_role = "active-symmetric" if coordinate_id == "SYMMETRY_COLLAPSED" else "active"
    return build_machine.tokamak(
        active_coils_data=machine[active_role],
        passive_coils_data=machine["passive"],
        limiter_data=machine["limiter"],
        wall_data=machine["wall"],
        magnetic_probe_data=machine["probes"],
    )

def _set_currents(
    tokamak: Any,
    machine: Mapping[str, object],
    coordinate_id: str,
    labels: list[str],
    values: NDArray[np.float64],
) -> None:
    currents = map_coil_currents(tokamak.coils_list, machine, coordinate_id, labels, values)
    for name, current in currents.items():
        tokamak[name].current = current


def _one_static_cell(
    preparation: Mapping[str, NDArray[np.generic]],
    machine: Mapping[str, object],
    coordinate_id: str,
    view_id: str,
    index: int,
) -> dict[str, NDArray[np.generic] | float | str | bool]:
    from freegsnke import GSstaticsolver, equilibrium_update, jtor_update

    size = _science_VIEWS[view_id]
    grid = np.asarray(preparation["grid"], dtype=np.float64)
    tokamak = _build_tokamak(machine, coordinate_id)
    labels = np.asarray(preparation["coil_labels"]).astype(str).tolist()
    currents = np.asarray(preparation["currents_output_a"], dtype=np.float64)[index]
    _set_currents(tokamak, machine, coordinate_id, labels, currents)
    eq = equilibrium_update.Equilibrium(
        tokamak=tokamak,
        Rmin=float(grid[0]),
        Rmax=float(grid[1]),
        Zmin=float(grid[2]),
        Zmax=float(grid[3]),
        nx=size,
        ny=size,
        psi=None,
    )
    profiles = jtor_update.Lao85(
        eq=eq,
        Ip=float(np.asarray(preparation["plasma_current_a"])[index]),
        fvac=float(np.asarray(preparation["fvac_t_m"])[index]),
        alpha=np.asarray(preparation["alpha"], dtype=np.float64)[index],
        beta=np.asarray(preparation["beta"], dtype=np.float64)[index],
        alpha_logic=bool(np.asarray(preparation["alpha_logic"])[index]),
        beta_logic=bool(np.asarray(preparation["beta_logic"])[index]),
    )
    solver = GSstaticsolver.NKGSsolver(eq)
    started = time.monotonic()
    with contextlib.redirect_stdout(sys.stderr):
        solver.solve(
            eq=eq,
            profiles=profiles,
            constrain=None,
            target_relative_tolerance=_science_SOLVER_TOLERANCE,
            max_solving_iterations=100,
            verbose=False,
        )
    runtime_s = time.monotonic() - started
    return assess_static_equilibrium(
        psi_native=np.asarray(eq.psi(), dtype=np.float64),
        psi_axis_native=float(eq.psi_axis), psi_boundary_native=float(eq.psi_bndry),
        r_coordinates=np.asarray(eq.R_1D), z_coordinates=np.asarray(eq.Z_1D),
        grid=grid, xpoints=np.asarray(eq.xpt, dtype=np.float64),
        midplane=np.asarray(eq.innerOuterSeparatrix(0), dtype=np.float64),
        axis_rz=np.asarray(eq.magneticAxis()[:2], dtype=np.float64),
        relative_change=float(solver.relative_change),
        intersects_wall=bool(eq.intersectsWall()), is_limited=bool(eq.flag_limiter),
        runtime_s=runtime_s,
    )

def run_static_target(
    preparation_path: Path, destination: Path, *, machine_archive: Path
) -> ArtifactIdentity:
    preparation = _read_npz(preparation_path)
    machine = _machine_configuration(machine_archive)
    arrays: dict[str, NDArray[np.generic]] = {
        "slice_times_s": np.asarray(_science_SLICE_TIMES_S, dtype=np.float64)
    }
    for coordinate in _science_COORDINATES:
        for view in sorted(_science_VIEWS):
            cells = [
                _one_static_cell(preparation, machine, coordinate, view, index)
                for index in range(len(_science_SLICE_TIMES_S))
            ]
            prefix = f"{coordinate.lower()}__{view.replace('-', '_')}"
            for key in cells[0]:
                arrays[f"{prefix}__{key}"] = np.asarray([cell[key] for cell in cells])
    publish_bytes(destination, _deterministic_npz_bytes(arrays))
    return artifact_identity(
        destination,
        artifact_id=f"artifact.{destination.stem}",
        role="fresh-freegsnke-static-output",
        payload_schema='empirical-lawhood/physical/mast-freegsnke-static-transport/static-output-arrays',
        media_type="application/x-npz",
    )
