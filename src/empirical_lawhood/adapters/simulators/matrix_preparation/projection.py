"""Bounded verified HDF5 projection readers/writers for reusable domain reduction."""
from __future__ import annotations
from collections.abc import Mapping
from hashlib import sha256
import io
import h5py  # type: ignore[import-untyped]
import numpy as np
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import RESPONSE_BUNDLES, NATIVE_SCHEMA, PARENTS, PreparationNativeResult, PreparationRoot, preparation_actions
from empirical_lawhood.domains.matrix.matrix_preparation_analysis.preparation_dynamics import NATIVE_MAXIMUM_BYTES
from empirical_lawhood.domains.matrix.six_matrix_response.response_checkpoint import ResponseGeometryNativeCheckpoint
from empirical_lawhood.adapters.simulators.six_matrix_response.response_source import response_hdf5_read_text, response_hdf5_text, response_hdf5_writer
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import PROJECTION_SCHEMA, PRIVILEGED_SCHEMA, PROSPECTIVE_TASK_SCHEMA, PreparationProjectionConfig, PreparationProjectionReport, PreparationPrivilegedReport, PreparationProspectiveTaskReport, PreparationProjectionRecord

from empirical_lawhood.domains.matrix.matrix_preparation.projection import Array, OBSERVABLE_SHAPES, PRIVILEGED_SHAPES, PROJECTION_MAXIMUM_BYTES, PROJECTION_METADATA, PROSPECTIVE_TASK_SHAPES, PreparationProjectionPayloads, PreparationProjectionReports, _OBSERVABLE_KEYS, _PROSPECTIVE_TASK_KEYS, project_preparation_records

def _write_projection_part(
    arrays: Mapping[str, Array],
    *,
    schema: str,
    config: PreparationProjectionConfig,
    native: PreparationNativeResult,
    refinement: int,
) -> bytes:
    output = io.BytesIO()
    with response_hdf5_writer(output) as artifact:
        for key, value in {
            **PROJECTION_METADATA,
            "empirical_lawhood_payload_schema": schema,
            "schema": schema,
            "projection_config_sha256": config.fingerprint(),
            "native_result_sha256": native.fingerprint(),
            "root_id": native.root.root_id,
            "refinement": str(refinement),
        }.items():
            response_hdf5_text(artifact, key, value)
        for key, values in arrays.items():
            artifact.create_dataset(key, data=values, track_times=False)
    payload = output.getvalue()
    if len(payload) > PROJECTION_MAXIMUM_BYTES:
        raise ValueError("preparation projection part exceeds its finite byte bound")
    return payload


def _verify_hdf5(group: h5py.Group, maximum: int) -> None:
    """Reject links, executable/object dtypes, filters and over-bound expansion."""
    pending = [group]
    objects, size = 0, 0
    while pending:
        current = pending.pop()
        for name in current:
            objects += 1
            if objects > 4096 or not isinstance(current.get(name, getlink=True), h5py.HardLink):
                raise ValueError("native payload has excessive objects or a nonlocal link")
            value = current[name]
            if isinstance(value, h5py.Group):
                pending.append(value)
            elif isinstance(value, h5py.Dataset):
                if (
                    value.dtype.kind not in "fciub"
                    or value.is_virtual
                    or value.external
                    or value.id.get_create_plist().get_nfilters() != 0
                ):
                    raise ValueError("native payload requires local unfiltered numeric arrays")
                size += value.size * value.dtype.itemsize
                if size > maximum:
                    raise ValueError("native payload expands beyond its byte bound")
            else:
                raise ValueError("native payload contains another object kind")


def _path(
    group: h5py.Group, root: PreparationRoot, refinement: int, retain_native: bool
) -> dict[str, Array]:
    shapes = {
        "ticks": (21,),
        "positions": (21, 2, 3, 4, 4),
        "momenta": (21, 2, 3, 4, 4),
        "couplings": (21, 2),
        "geometry": (21, 6),
        "probe": (21, 9),
        "transfer": (21, 15, 15),
    }
    if retain_native:
        shapes.update(
            {
                name: (320 * refinement + 1, 2, 3, 4, 4)
                for name in ("native_positions", "native_momenta")
            }
        )
    if set(group.keys()) != set(shapes):
        raise ValueError("complete native path changes its exact array roster")
    data = {}
    for name, shape in shapes.items():
        value = group[name]
        dtype = np.dtype(
            "int64"
            if name == "ticks"
            else "complex128"
            if "positions" in name or "momenta" in name
            else "float64"
        )
        if not isinstance(value, h5py.Dataset) or value.shape != shape or value.dtype != dtype:
            raise ValueError("complete native path changes array shape/dtype")
        data[name] = np.asarray(value[...])
    if not np.array_equal(data["ticks"], np.arange(root.handoff, root.handoff + 321, 16)):
        raise ValueError("native response path changes the fixed readout clock")
    if not np.allclose(data["couplings"], [2 / 3, 22 / 3], atol=1e-12, rtol=0):
        raise ValueError("preparation continued parent control after handoff")
    for name in ("positions", "momenta", "native_positions", "native_momenta"):
        if name in data and not np.isfinite(data[name]).all():
            raise ValueError("complete native path contains nonfinite states")
    if retain_native:
        for name in ("positions", "momenta"):
            if not np.array_equal(data[name], data[f"native_{name}"][:: 16 * refinement]):
                raise ValueError("native substeps and receiver-cadence observations disagree")
    return data


def project_preparation_arrays(native, payload: bytes, refinement: int, *, source_identity):
    """Shared current/frozen measurement arithmetic, without record relabelling."""
    if (
        source_identity != native.source_config
        or len(payload) > NATIVE_MAXIMUM_BYTES
        or sha256(payload).hexdigest() != native.observations_sha256
        or refinement not in (1, 2)
    ):
        raise ValueError("preparation projection changes native content/config/view")
    root = native.root
    deliveries = {d.occurrence_id: d for d in native.deliveries if d.refinement == refinement}
    with h5py.File(io.BytesIO(payload), "r") as source:
        _verify_hdf5(source, NATIVE_MAXIMUM_BYTES)
        if (
            response_hdf5_read_text(source, "schema") != NATIVE_SCHEMA
            or response_hdf5_read_text(source, "source_config_sha256")
            != source_identity.object_fingerprint
            or response_hdf5_read_text(source, "root_sha256") != root.fingerprint()
            or set(source.keys())
            != ({"r1", "r2"} if native.mode_sha256 is None else {"mode", "r1", "r2"})
        ):
            raise ValueError("preparation projection changes native metadata/roster")
        view = source[f"r{refinement}"]
        mode = None if native.mode_sha256 is None else np.asarray(source["mode"][...])
        if mode is not None and (
            mode.shape != (3, 4, 4)
            or mode.dtype != np.dtype("complex128")
            or sha256(mode.tobytes()).hexdigest() != native.mode_sha256
        ):
            raise ValueError("preparation projection changes the common preparent mode")
        imported_checkpoint = None
        if mode is not None and "imported_checkpoint" in view:
            imported_checkpoint = decode_canonical_bytes(view["imported_checkpoint"][...].tobytes(),
                ResponseGeometryNativeCheckpoint, maximum_bytes=128 * 1024)

        def parent_records():
            for parent in PARENTS:
                group = view[parent]
                parent_delivery = deliveries[f"{root.root_id}.{parent}.parent.r{refinement}"]
                if parent_delivery.disposition != "COMPLETE":
                    yield None, {}
                    continue
                if mode is None or "handoff_checkpoint" not in group:
                    raise ValueError("complete preparation has no observed handoff or common mode")
                checkpoint = decode_canonical_bytes(group["handoff_checkpoint"][...].tobytes(),
                    ResponseGeometryNativeCheckpoint, maximum_bytes=128 * 1024)
                paths = {}
                for action in (a for a in preparation_actions(root) if a.parent == parent):
                    key = action.action_id.rsplit(f".{parent}.", 1)[1]
                    delivered = deliveries[f"{action.action_id}.r{refinement}"]
                    if delivered.disposition == "COMPLETE":
                        paths[key] = _path(group[key], root, refinement, action.retain_native_path)
                yield checkpoint, paths

        return project_preparation_records(native, refinement, mode=mode,
            imported_checkpoint=imported_checkpoint, parent_records=parent_records())


def project_preparation_root(
    config: PreparationProjectionConfig,
    native: PreparationNativeResult,
    payload: bytes,
    refinement: int,
) -> tuple[PreparationProjectionReports, PreparationProjectionPayloads]:
    arrays, failed_mechanisms, failed_benchmarks = project_preparation_arrays(
        native, payload, refinement, source_identity=config.source_config,
    )
    root = native.root
    deliveries = {d.occurrence_id: d for d in native.deliveries if d.refinement == refinement}
    observable = {
        key: arrays[key][:, :4] if key in _PROSPECTIVE_TASK_KEYS else arrays[key] for key in _OBSERVABLE_KEYS
    }
    privileged = {key: arrays[key] for key in PRIVILEGED_SHAPES}
    task = {key: arrays[key][:, 4] for key in _PROSPECTIVE_TASK_KEYS}
    # Distinct artifact ports enforce the information boundary. Observable
    # fitting never receives microscopic diagnostics or the independent task.
    data = PreparationProjectionPayloads(
        _write_projection_part(
            observable,
            schema=PROJECTION_SCHEMA,
            config=config,
            native=native,
            refinement=refinement,
        ),
        _write_projection_part(
            privileged,
            schema=PRIVILEGED_SCHEMA,
            config=config,
            native=native,
            refinement=refinement,
        ),
        _write_projection_part(
            task, schema=PROSPECTIVE_TASK_SCHEMA, config=config, native=native, refinement=refinement
        ),
    )

    def counts(role: str) -> tuple[int, int]:
        actions = preparation_actions(root)
        if role == "observable":
            ids = {f"{root.root_id}.{p}.parent.r{refinement}" for p in PARENTS}
            ids.update(
                f"{a.action_id}.r{refinement}"
                for a in actions
                if a.bundle in RESPONSE_BUNDLES and a.magnitude == 8
            )
        elif role == "prospective-task":
            ids = {f"{a.action_id}.r{refinement}" for a in actions if a.bundle == "prospective-task"}
        else:
            ids = {
                f"{a.action_id}.r{refinement}"
                for a in actions
                if root.numerical_semantics and a.bundle == "common-response"
            }
        complete = sum(deliveries[key].disposition == "COMPLETE" for key in ids)
        return complete, len(ids) - complete

    config_ref = ObjectIdentity.from_record(config.config_id, config)
    native_ref = ObjectIdentity.from_record(native.result_id, native)
    report = PreparationProjectionReports(
        PreparationProjectionReport(
            f"report.{root.root_id}.r{refinement}",
            root,
            refinement,
            config_ref,
            native_ref,
            sha256(data.observable).hexdigest(),
            *counts("observable"),
        ),
        PreparationPrivilegedReport(
            f"report.{root.root_id}.privileged.r{refinement}",
            root,
            refinement,
            config_ref,
            native_ref,
            sha256(data.privileged).hexdigest(),
            *counts("privileged"),
            tuple(sorted(failed_mechanisms)),
            tuple(sorted(failed_benchmarks)),
        ),
        PreparationProspectiveTaskReport(
            f"report.{root.root_id}.prospective-task.r{refinement}",
            root,
            refinement,
            config_ref,
            native_ref,
            sha256(data.prospective_task).hexdigest(),
            *counts("prospective-task"),
        ),
    )
    return report, data


def read_preparation_projection(
    report: PreparationProjectionRecord,
    payload: bytes,
    *,
    role: str = "observable",
) -> dict[str, Array]:
    if role not in ("observable", "privileged", "prospective-task") or report.PART != role:
        raise ValueError("projection reader changes its declared information role")
    schema, shapes, digest = {
        "observable": (PROJECTION_SCHEMA, OBSERVABLE_SHAPES, report.data_sha256),
        "privileged": (PRIVILEGED_SCHEMA, PRIVILEGED_SHAPES, report.data_sha256),
        "prospective-task": (PROSPECTIVE_TASK_SCHEMA, PROSPECTIVE_TASK_SHAPES, report.data_sha256),
    }[role]
    if len(payload) > PROJECTION_MAXIMUM_BYTES or sha256(payload).hexdigest() != digest:
        raise ValueError("projected data differs from its immutable report")
    with h5py.File(io.BytesIO(payload), "r") as artifact:
        _verify_hdf5(artifact, PROJECTION_MAXIMUM_BYTES)
        if (
            response_hdf5_read_text(artifact, "schema") != schema
            or response_hdf5_read_text(artifact, "root_id") != report.root.root_id
            or response_hdf5_read_text(artifact, "refinement") != str(report.refinement)
            or response_hdf5_read_text(artifact, "projection_config_sha256")
            != report.projection_config.object_fingerprint
            or response_hdf5_read_text(artifact, "native_result_sha256")
            != report.native_result.object_fingerprint
            or set(artifact.keys()) != set(shapes)
        ):
            raise ValueError("projection metadata/array roster differs")
        arrays = {}
        for key, shape in shapes.items():
            if artifact[key].shape != shape or artifact[key].dtype != np.dtype("float64"):
                raise ValueError("projected array changes its typed shape/dtype")
            arrays[key] = np.asarray(artifact[key][...])
    return arrays
