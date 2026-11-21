"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from hashlib import sha256
from io import BytesIO
from typing import Any
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.six_matrix_response.artifact_inventory import MATRIX_RESPONSE_PREPARATION_SCHEDULING_MEASUREMENT_HDF5_SCHEMA, SixMatrixResponsePreparationWindowSchedulingTrajectoryArtifactReservation
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import SixMatrixResponseNumericalView, SixMatrixResponseSixMatrixSourceConfig

from empirical_lawhood.domains.matrix.six_matrix_response.preparation_schedule import (
    MATRIX_RESPONSE_PREPARATION_SCHEDULING_MAXIMUM_RESULT_BYTES as _science_MATRIX_RESPONSE_PREPARATION_SCHEDULING_MAXIMUM_RESULT_BYTES,
    SixMatrixResponsePreparationWindowSchedulingDevelopmentRoster as _science_SixMatrixResponsePreparationWindowSchedulingDevelopmentRoster,
    SixMatrixResponsePreparationWindowSchedulingExecutedTrajectory as _science_SixMatrixResponsePreparationWindowSchedulingExecutedTrajectory,
    SixMatrixResponsePreparationWindowSchedulingMeasurementArtifactReceipt as _science_SixMatrixResponsePreparationWindowSchedulingMeasurementArtifactReceipt,
    SixMatrixResponsePreparationWindowSchedulingNoiseTape as _science_SixMatrixResponsePreparationWindowSchedulingNoiseTape,
    SixMatrixResponsePreparationWindowSchedulingNoiseTapeKind as _science_SixMatrixResponsePreparationWindowSchedulingNoiseTapeKind,
    SixMatrixResponsePreparationWindowSchedulingPersistedScheduleTrace as _science_SixMatrixResponsePreparationWindowSchedulingPersistedScheduleTrace,
    SixMatrixResponsePreparationWindowSchedulingPersistedTrajectory as _science_SixMatrixResponsePreparationWindowSchedulingPersistedTrajectory,
    SixMatrixResponsePreparationWindowSchedulingScheduleTrace as _science_SixMatrixResponsePreparationWindowSchedulingScheduleTrace,
    SixMatrixResponsePreparationWindowSchedulingScheduleTraceResult as _science_SixMatrixResponsePreparationWindowSchedulingScheduleTraceResult,
    SixMatrixResponsePreparationWindowSchedulingStudyConfig as _science_SixMatrixResponsePreparationWindowSchedulingStudyConfig,
    SixMatrixResponsePreparationWindowSchedulingTrajectoryRequest as _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryRequest,
    SixMatrixResponsePreparationWindowSchedulingTrajectoryResult as _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryResult,
    SixMatrixResponsePreparationWindowSchedulingTrajectoryTranche as _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryTranche,
    _measurement_dataset_paths,
    _readonly_array,
    _require_preparation_scientific_inputs,
    _root_seed_sha256,
    derive_six_matrix_response_preparation_window_scheduling_noise_tape as _science_derive_six_matrix_response_preparation_window_scheduling_noise_tape,
    execute_six_matrix_response_preparation_window_scheduling_schedule as _science_execute_six_matrix_response_preparation_window_scheduling_schedule,
    six_matrix_response_preparation_window_scheduling_trajectory_decoded_dataset_bytes as _science_six_matrix_response_preparation_window_scheduling_trajectory_decoded_dataset_bytes,
)

def _encode_six_matrix_response_preparation_window_scheduling_measurement_hdf5(
    *,
    request: _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryRequest,
    numerical_view_id: str,
    view_step_multiplier: int,
    traces: tuple[_science_SixMatrixResponsePreparationWindowSchedulingScheduleTrace, ...],
    preparation_tape: _science_SixMatrixResponsePreparationWindowSchedulingNoiseTape,
    observation_tape: _science_SixMatrixResponsePreparationWindowSchedulingNoiseTape,
) -> bytes:
    """Encode one bounded full trajectory without external I/O."""

    if len(traces) != 1:
        raise ValueError("six-matrix preparation scheduling HDF5 payload must contain exactly one trajectory")

    try:
        import h5py  # type: ignore[import-untyped]
    except ImportError as error:  # pragma: no cover - installed product dependency
        raise RuntimeError("six-matrix preparation scheduling HDF5 encoding requires h5py") from error
    buffer = BytesIO()
    with h5py.File(buffer, "w", libver=("earliest", "v114"), track_order=False) as handle:
        attributes = {
            "empirical_lawhood_clocks": '{"noise":"matrix-preparation-scheduling.root-tape-step","trajectory":"matrix-preparation-scheduling.integrator-step"}',
            "empirical_lawhood_frames": '{"noise":"standardized-hermitian-noise","trajectory":"six-matrix-native"}',
            "empirical_lawhood_keys": '["post_arrival_step"]',
            "empirical_lawhood_payload_schema": MATRIX_RESPONSE_PREPARATION_SCHEDULING_MEASUREMENT_HDF5_SCHEMA,
            "empirical_lawhood_units": '{"alpha_tilde":"1","momenta":"native","noise":"standardized","positions":"native","post_arrival_step":"step"}',
        }
        for name in sorted(attributes):
            encoded = attributes[name].encode("utf-8")
            handle.attrs.create(name, encoded, dtype=f"S{len(encoded)}")
        noise_group = handle.create_group("noise", track_order=False)
        noise_group.create_dataset(
            "observation",
            data=np.ascontiguousarray(observation_tape.noises, dtype="<c16"),
            dtype="<c16",
            chunks=None,
            compression=None,
            shuffle=False,
            fletcher32=False,
            track_times=False,
        )
        noise_group.create_dataset(
            "preparation",
            data=np.ascontiguousarray(preparation_tape.noises, dtype="<c16"),
            dtype="<c16",
            chunks=None,
            compression=None,
            shuffle=False,
            fletcher32=False,
            track_times=False,
        )
        group = handle.create_group("trajectory", track_order=False)
        trace = traces[0]
        states = trace.states
        arrival_index = trace.result.completed_preparation_steps
        datasets = (
            (
                "alpha_tilde",
                np.asarray(
                    tuple((state.alpha_tilde_x, state.alpha_tilde_y) for state in states),
                    dtype="<f8",
                ),
                "<f8",
            ),
            (
                "momenta",
                np.ascontiguousarray(
                    np.stack(tuple(state.momenta for state in states)),
                    dtype="<c16",
                ),
                "<c16",
            ),
            (
                "positions",
                np.ascontiguousarray(
                    np.stack(tuple(state.positions for state in states)),
                    dtype="<c16",
                ),
                "<c16",
            ),
            (
                "post_arrival_step",
                np.arange(len(states), dtype="<i8") - arrival_index,
                "<i8",
            ),
        )
        for name, value, dtype in datasets:
            group.create_dataset(
                name,
                data=value,
                dtype=dtype,
                chunks=None,
                compression=None,
                shuffle=False,
                fletcher32=False,
                track_times=False,
            )
    return buffer.getvalue()


def _validate_six_matrix_response_preparation_window_scheduling_hdf5_objects(
    handle: Any,
    *,
    multiplier: int,
    traces: tuple[_science_SixMatrixResponsePreparationWindowSchedulingScheduleTraceResult, ...],
) -> None:
    import h5py

    if len(traces) != 1:
        raise ValueError("six-matrix preparation scheduling HDF5 validator requires one trajectory result")
    expected_groups = {"noise", "trajectory"}
    expected_datasets: dict[str, tuple[tuple[int, ...], np.dtype[np.generic]]] = {
        "noise/preparation": ((384 * multiplier, 2, 3, 4, 4), np.dtype("<c16")),
        "noise/observation": ((768 * multiplier, 2, 3, 4, 4), np.dtype("<c16")),
    }
    count = traces[0].trajectory_state_count
    expected_datasets.update(
        {
            "trajectory/alpha_tilde": ((count, 2), np.dtype("<f8")),
            "trajectory/momenta": ((count, 2, 3, 4, 4), np.dtype("<c16")),
            "trajectory/positions": ((count, 2, 3, 4, 4), np.dtype("<c16")),
            "trajectory/post_arrival_step": ((count,), np.dtype("<i8")),
        }
    )
    observed: set[str] = set()

    def validate_object(name: str, value: object) -> None:
        observed.add(name)
        link = handle.get(name, getlink=True)
        if not isinstance(link, h5py.HardLink):
            raise ValueError("six-matrix preparation scheduling measurement HDF5 forbids non-hard links")
        if name in expected_groups:
            if not isinstance(value, h5py.Group) or tuple(value.attrs):
                raise ValueError("six-matrix preparation scheduling measurement HDF5 group contract differs")
            return
        spec = expected_datasets.get(name)
        if spec is None or not isinstance(value, h5py.Dataset):
            raise ValueError("six-matrix preparation scheduling measurement HDF5 object inventory differs")
        shape, dtype = spec
        if (
            value.shape != shape
            or value.maxshape != shape
            or value.dtype != dtype
            or value.chunks is not None
            or value.compression is not None
            or value.shuffle
            or value.fletcher32
            or value.scaleoffset is not None
            or value.external
            or tuple(value.attrs)
        ):
            raise ValueError("six-matrix preparation scheduling measurement HDF5 dataset contract differs")

    handle.visititems(validate_object)
    if observed != expected_groups | set(expected_datasets):
        raise ValueError("six-matrix preparation scheduling measurement HDF5 object roster differs")


def decode_six_matrix_response_preparation_window_scheduling_trajectory_hdf5(
    payload: bytes,
    *,
    reservation: SixMatrixResponsePreparationWindowSchedulingTrajectoryArtifactReservation,
    result: _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryResult,
) -> _science_SixMatrixResponsePreparationWindowSchedulingPersistedTrajectory:
    """Strictly reconstruct one trajectory in a fresh method process."""

    receipt = result.measurement_artifact
    if (
        not isinstance(payload, bytes)
        or receipt.reservation != reservation
        or len(payload) != receipt.size_bytes
        or len(payload) > reservation.maximum_bytes
        or sha256(payload).hexdigest() != receipt.content_sha256
    ):
        raise ValueError("six-matrix preparation scheduling trajectory payload differs from its custody receipt")
    try:
        import h5py
    except ImportError as error:  # pragma: no cover - installed product dependency
        raise RuntimeError("six-matrix preparation scheduling HDF5 decoding requires h5py") from error
    expected_attributes = {
        "empirical_lawhood_clocks": '{"noise":"matrix-preparation-scheduling.root-tape-step","trajectory":"matrix-preparation-scheduling.integrator-step"}',
        "empirical_lawhood_frames": '{"noise":"standardized-hermitian-noise","trajectory":"six-matrix-native"}',
        "empirical_lawhood_keys": '["post_arrival_step"]',
        "empirical_lawhood_payload_schema": MATRIX_RESPONSE_PREPARATION_SCHEDULING_MEASUREMENT_HDF5_SCHEMA,
        "empirical_lawhood_units": '{"alpha_tilde":"1","momenta":"native","noise":"standardized","positions":"native","post_arrival_step":"step"}',
    }
    with h5py.File(BytesIO(payload), "r") as handle:
        if tuple(sorted(handle.attrs)) != tuple(sorted(expected_attributes)):
            raise ValueError("six-matrix preparation scheduling trajectory HDF5 root attributes differ")
        for name, expected in expected_attributes.items():
            observed = handle.attrs[name]
            if not isinstance(observed, (bytes, np.bytes_)) or bytes(observed).decode() != expected:
                raise ValueError("six-matrix preparation scheduling trajectory HDF5 attribute bytes differ")
        _validate_six_matrix_response_preparation_window_scheduling_hdf5_objects(
            handle,
            multiplier=result.view_step_multiplier,
            traces=(result.schedule_trace,),
        )
        preparation = _readonly_array(handle["/noise/preparation"][...], dtype="<c16")
        observation = _readonly_array(handle["/noise/observation"][...], dtype="<c16")
        prefix = "/trajectory"
        trace = _science_SixMatrixResponsePreparationWindowSchedulingPersistedScheduleTrace(
            result=result.schedule_trace,
            positions=_readonly_array(handle[f"{prefix}/positions"][...], dtype="<c16"),
            momenta=_readonly_array(handle[f"{prefix}/momenta"][...], dtype="<c16"),
            alpha_tilde=_readonly_array(handle[f"{prefix}/alpha_tilde"][...], dtype="<f8"),
            post_arrival_steps=_readonly_array(
                handle[f"{prefix}/post_arrival_step"][...], dtype="<i8"
            ),
        )
    return _science_SixMatrixResponsePreparationWindowSchedulingPersistedTrajectory(
        result=result,
        preparation_noise=preparation,
        observation_noise=observation,
        trace=trace,
    )


class SixMatrixResponsePreparationWindowSchedulingTrajectoryEngine:
    """Source-free one-request/one-action-homogeneous-trajectory engine."""

    def __init__(
        self,
        *,
        source_config: SixMatrixResponseSixMatrixSourceConfig,
        study_config: _science_SixMatrixResponsePreparationWindowSchedulingStudyConfig,
        development_roster: _science_SixMatrixResponsePreparationWindowSchedulingDevelopmentRoster,
    ) -> None:
        if study_config.source_config != ObjectIdentity.from_record(
            source_config.config_id,
            source_config,
        ):
            raise ValueError("six-matrix preparation scheduling engine source/study identities differ")
        if study_config.family_member not in source_config.anisotropic_model.family_members:
            raise ValueError("six-matrix preparation scheduling engine member is absent from the source family")
        if study_config.primary_view != source_config.primary_view:
            raise ValueError("six-matrix preparation scheduling engine numerical views differ from the source")
        if (
            development_roster.study_config
            != ObjectIdentity.from_record(study_config.config_id, study_config)
            or development_roster.issue_id != study_config.development_issue_id
            or development_roster.seed_namespace_id != study_config.development_seed_namespace_id
            or development_roster.root_namespace_id != study_config.development_root_namespace_id
            or development_roster.numerical_member_id != study_config.primary_numerical_member_id
            or development_roster.numerical_view_id != study_config.primary_view.view_id
        ):
            raise ValueError("six-matrix preparation scheduling engine roster differs from its study config")
        self.source_config = source_config
        self.study_config = study_config
        self.development_roster = development_roster

    def _view(
        self,
        request: _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryRequest,
    ) -> tuple[SixMatrixResponseNumericalView, int]:
        if request.numerical_view_id == self.study_config.primary_view.view_id:
            return self.study_config.primary_view, 1
        raise ValueError("six-matrix preparation scheduling DEVELOPMENT requires the primary numerical view")

    def run_trajectory(
        self,
        request: _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryRequest,
    ) -> _science_SixMatrixResponsePreparationWindowSchedulingExecutedTrajectory:
        """Execute one platform action-homogeneous trajectory task."""

        if (
            request.study_config
            != ObjectIdentity.from_record(self.study_config.config_id, self.study_config)
            or request.source_config != self.study_config.source_config
            or request.development_roster
            != ObjectIdentity.from_record(
                self.development_roster.roster_id,
                self.development_roster,
            )
            or request.issued_nested_view not in self.development_roster.views
        ):
            raise ValueError("six-matrix preparation scheduling trajectory config/roster differs from the engine")
        numerical_view, multiplier = self._view(request)
        if (
            request.tranche is not _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryTranche.DEVELOPMENT
            or request.issue_id != self.study_config.development_issue_id
            or request.seed_namespace_id != self.study_config.development_seed_namespace_id
            or request.numerical_member_id != self.study_config.primary_numerical_member_id
            or request.root_block_id
            != self.development_roster.physical_independent_unit_ids[request.block_index]
            or multiplier != 1
        ):
            raise ValueError("six-matrix preparation scheduling trajectory lies outside issued DEVELOPMENT")
        _require_preparation_scientific_inputs(
            request.scientific_inputs, root_block_id=request.root_block_id,
            seed_root_id=request.seed_root_id, block_index=request.block_index,
            current_context_sha256=self.study_config.fingerprint(),
        )
        preparation = _science_derive_six_matrix_response_preparation_window_scheduling_noise_tape(
            config=self.study_config,
            root_block_id=request.root_block_id,
            seed_root_id=request.seed_root_id,
            block_index=request.block_index,
            tape_kind=_science_SixMatrixResponsePreparationWindowSchedulingNoiseTapeKind.PREPARATION,
            scientific_seed_input=request.scientific_inputs[1],
        )
        observation = _science_derive_six_matrix_response_preparation_window_scheduling_noise_tape(
            config=self.study_config,
            root_block_id=request.root_block_id,
            seed_root_id=request.seed_root_id,
            block_index=request.block_index,
            tape_kind=_science_SixMatrixResponsePreparationWindowSchedulingNoiseTapeKind.OBSERVATION,
            scientific_seed_input=request.scientific_inputs[2],
        )
        word = next(
            value
            for value in self.study_config.schedules
            if value.schedule_id == request.schedule_id
        )
        trace = _science_execute_six_matrix_response_preparation_window_scheduling_schedule(
            config=self.study_config,
            request=request,
            word=word,
            numerical_view=numerical_view,
            view_step_multiplier=multiplier,
            preparation_tape=preparation,
            observation_tape=observation,
        )
        measurement_payload = _encode_six_matrix_response_preparation_window_scheduling_measurement_hdf5(
            request=request,
            numerical_view_id=numerical_view.view_id,
            view_step_multiplier=multiplier,
            traces=(trace,),
            preparation_tape=preparation,
            observation_tape=observation,
        )
        reservation = request.measurement_artifact_reservation
        if len(measurement_payload) > min(
            reservation.maximum_bytes,
            self.study_config.maximum_trajectory_hdf5_bytes,
        ):
            raise ValueError("six-matrix preparation scheduling trajectory exceeds its reserved shard ceiling")
        measurement_artifact = _science_SixMatrixResponsePreparationWindowSchedulingMeasurementArtifactReceipt(
            receipt_id=f"matrix-preparation-scheduling.measurement-receipt.{request.task_id}",
            task_id=request.task_id,
            root_block_id=request.root_block_id,
            output_id=request.measurement_output_id,
            payload_schema=MATRIX_RESPONSE_PREPARATION_SCHEDULING_MEASUREMENT_HDF5_SCHEMA,
            media_type="application/x-hdf5",
            reservation=reservation,
            schedule_ids=(request.schedule_id,),
            dataset_paths=_measurement_dataset_paths(),
            content_sha256=sha256(measurement_payload).hexdigest(),
            size_bytes=len(measurement_payload),
            decoded_dataset_bytes=_science_six_matrix_response_preparation_window_scheduling_trajectory_decoded_dataset_bytes(
                request.schedule_id, view_step_multiplier=multiplier
            ),
            grants_authority=False,
        )
        planned_updates = (
            word.final_arrival_step + self.study_config.post_arrival_steps
        ) * multiplier
        if planned_updates > self.study_config.maximum_trajectory_integration_steps:
            raise ValueError("six-matrix preparation scheduling trajectory exceeds its frozen integration ceiling")
        result = _science_SixMatrixResponsePreparationWindowSchedulingTrajectoryResult(
            result_id=f"result.{request.task_id}",
            task_id=request.task_id,
            output_id=request.output_id,
            request=ObjectIdentity.from_record(request.request_id, request),
            root_block_id=request.root_block_id,
            block_index=request.block_index,
            tranche=request.tranche,
            issue_id=request.issue_id,
            seed_namespace_id=request.seed_namespace_id,
            development_roster=request.development_roster,
            issued_nested_view=request.issued_nested_view,
            schedule_id=request.schedule_id,
            numerical_view_id=numerical_view.view_id,
            numerical_member_id=request.numerical_member_id,
            scientific_view_id=request.scientific_view_id,
            physical_independent_unit_id=request.physical_independent_unit_id,
            acquisition_group_id=request.acquisition_group_id,
            view_step_multiplier=multiplier,
            root_seed_sha256=_root_seed_sha256(
                seed_root_id=request.seed_root_id,
                root_block_id=request.root_block_id,
                block_index=request.block_index,
                current_context_sha256=self.study_config.fingerprint(),
                scientific_seed_input=request.scientific_inputs[0],
            ),
            study_config=request.study_config,
            scientific_inputs=request.scientific_inputs,
            preparation_tape=preparation.receipt,
            observation_tape=observation.receipt,
            measurement_artifact=measurement_artifact,
            schedule_trace=trace.result,
            planned_integration_updates=planned_updates,
            completed_integration_updates=(
                trace.result.completed_preparation_steps + trace.result.completed_observation_steps
            ),
            terminal=trace.result.terminal,
            reason_codes=trace.result.reason_codes,
            evidence_ceiling=request.evidence_ceiling,
            outcome_access=request.outcome_access,
            visibility_ceiling=request.visibility_ceiling,
            scientific_verdict_ids=(),
            grants_authority=False,
        )
        if len(result.canonical_bytes()) > min(
            _science_MATRIX_RESPONSE_PREPARATION_SCHEDULING_MAXIMUM_RESULT_BYTES,
            self.study_config.maximum_trajectory_result_bytes,
        ):
            raise ValueError("six-matrix preparation scheduling trajectory result exceeds its output ceiling")
        return _science_SixMatrixResponsePreparationWindowSchedulingExecutedTrajectory(
            result=result,
            measurement_payload=measurement_payload,
            trace=trace,
            preparation_tape=preparation,
            observation_tape=observation,
        )
