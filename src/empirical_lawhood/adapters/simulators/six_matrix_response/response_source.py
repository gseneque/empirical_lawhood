"""Native acquisition and external-format binding for the domain science."""

from dataclasses import replace
from hashlib import sha256
import io
from typing import Callable
import h5py  # type: ignore[import-untyped]
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _decode, _encode
from empirical_lawhood.domains.matrix.six_matrix_response.response_qualification import ResponseGeometryAssayNativeConfig, ResponseGeometryAssayNativeSegmentResult, ResponseGeometryAssayNativeSegment

from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import (
    ASSAY_NATIVE_HDF5_METADATA as _science_ASSAY_NATIVE_HDF5_METADATA,
    _run_view,
    _unitary,
)

def response_hdf5_text(parent: h5py.Group, name: str, value: str) -> None:
    """Fixed, bounded UTF-8 bytes; no HDF5 variable-length heap references."""
    encoded = value.encode("utf-8")
    if not encoded or len(encoded) > 4096 or b"\0" in encoded:
        raise ValueError("assay HDF5 text is outside its scalar byte bound")
    parent.attrs.create(name, encoded, dtype=f"S{len(encoded)}")


def response_hdf5_read_text(parent: h5py.Group, name: str) -> str:
    if name not in parent.attrs:
        raise ValueError("assay HDF5 identity attribute is absent")
    attribute = parent.attrs.get_id(name)
    try:
        data_type = attribute.get_type()
        if (
            data_type.get_class() != h5py.h5t.STRING
            or data_type.is_variable_str()
            or not 0 < data_type.get_size() <= 4096
            or attribute.get_space().get_simple_extent_ndims() != 0
        ):
            raise ValueError("assay HDF5 identity requires bounded fixed UTF-8 bytes")
    finally:
        attribute.close()
    value = parent.attrs.get(name)
    if isinstance(value, bytes) and 0 < len(value) <= 4096:
        return value.decode("utf-8")
    raise ValueError("assay HDF5 identity requires bounded fixed UTF-8 bytes")


def response_hdf5_writer(stream: io.BytesIO) -> h5py.File:
    """In-memory assay artifact with no wall-clock metadata in scientific bytes."""
    creation = h5py.h5p.create(h5py.h5p.FILE_CREATE)
    creation.set_obj_track_times(False)
    access = h5py.h5p.create(h5py.h5p.FILE_ACCESS)
    access.set_fileobj_driver(h5py.h5fd.fileobj_driver, stream)
    return h5py.File(h5py.h5f.create(b"response-geometry-assay-memory", fapl=access, fcpl=creation))


def response_hdf5_group(parent: h5py.Group, name: str) -> h5py.Group:
    creation = h5py.h5p.create(h5py.h5p.GROUP_CREATE)
    creation.set_obj_track_times(False)
    return h5py.Group(h5py.h5g.create(parent.id, name.encode("ascii"), gcpl=creation))


def _execute_response_segment(
    config: ResponseGeometryAssayNativeConfig,
    segment: ResponseGeometryAssayNativeSegment,
    predecessor: ResponseGeometryAssayNativeSegmentResult | None,
    *,
    progress: Callable[[int], None] | None = None,
) -> tuple[ResponseGeometryAssayNativeSegmentResult, bytes]:
    """Execute exactly the planned segment; the production caller owns authority."""
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    if segment.root not in config.roots:
        raise ValueError("assay segment root differs from the issued source roster")
    if segment.predecessor is None:
        if predecessor is not None:
            raise ValueError("assay root prefix cannot consume a predecessor")
    elif (
        predecessor is None
        or predecessor.segment != segment.predecessor
        or predecessor.source_config != config_identity
    ):
        raise ValueError("assay source predecessor/config differs from the exact issued continuation")
    completed_before_view, last_reported = 0, 0

    def report(local_completed: int) -> None:
        nonlocal last_reported
        completed = completed_before_view + local_completed
        if progress is not None and completed > last_reported:
            progress(completed)
            last_reported = completed

    stream = io.BytesIO()
    with response_hdf5_writer(stream) as artifact:
        for name, text in _science_ASSAY_NATIVE_HDF5_METADATA.items():
            if name == "empirical_lawhood_payload_schema":
                text = config.observation_schema
            response_hdf5_text(artifact, name, text)
        response_hdf5_text(artifact, "schema", config.observation_schema)
        response_hdf5_text(artifact, "segment_sha256", segment.fingerprint())
        response_hdf5_text(artifact, "source_config_sha256", config.fingerprint())
        view_results = []
        for index, refinement in enumerate(segment.root.refinements):
            view_group = response_hdf5_group(artifact, f"r{refinement}")
            view_result, view_arrays = _run_view(
                config,
                segment,
                refinement,
                None if predecessor is None else predecessor.views[index],
                progress=report if progress is not None else None,
            )
            for name, values in view_arrays.items():
                view_group.create_dataset(name, data=values, track_times=False)
            del view_arrays
            report(view_result.delivery.completed_intervals)
            completed_before_view += view_result.delivery.completed_intervals
            view_results.append(view_result)
        views = tuple(view_results)
        if segment.phase == "prefix":
            # The primary mode defines the physical action in every view.
            # Shadow eigendirections are retained only as numerical diagnostics.
            primary = views[0].checkpoint
            primary_mode = (
                None
                if primary is None or primary.frozen_mode_base64 is None
                else _decode(primary.frozen_mode_base64, (3, 4, 4))
            )
            bound_views = []
            for item in views:
                if item.checkpoint is not None:
                    unitary = _unitary(config, segment.root, item.refinement)
                    mode = (
                        None
                        if primary_mode is None
                        else _encode(
                            np.asarray(unitary @ primary_mode @ unitary.conj().T, dtype="<c16")
                        )
                    )
                    item = replace(
                        item, checkpoint=replace(item.checkpoint, frozen_mode_base64=mode)
                    )
                bound_views.append(item)
            views = tuple(bound_views)
    payload = stream.getvalue()
    if len(payload) > 16 * 1024**2:
        raise ValueError("assay native observation shard exceeds its 16-MiB bound")
    result = config.result_type(
        f"result.{segment.task_id}",
        config_identity,
        segment,
        None
        if predecessor is None
        else ObjectIdentity.from_record(predecessor.result_id, predecessor),
        views,
        sha256(payload).hexdigest(),
    )
    return result, payload


def execute_assay_segment(
    config: ResponseGeometryAssayNativeConfig,
    segment: ResponseGeometryAssayNativeSegment,
    predecessor: ResponseGeometryAssayNativeSegmentResult | None,
    *,
    progress: Callable[[int], None] | None = None,
) -> tuple[ResponseGeometryAssayNativeSegmentResult, bytes]:
    """Preserve the strict assay entrypoint over the common native mechanics."""
    if type(config) is not ResponseGeometryAssayNativeConfig or type(segment) is not ResponseGeometryAssayNativeSegment:
        raise ValueError("assay execution requires its exact assay config and segment types")
    return _execute_response_segment(config, segment, predecessor, progress=progress)
