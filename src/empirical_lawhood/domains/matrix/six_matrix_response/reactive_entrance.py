"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import ClassVar
import numpy as np
from empirical_lawhood.domains.matrix.six_matrix_response.reactive_entrance_scientific_inputs import MatrixReactiveEntranceScientificInputs
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_schema, validate_semantic_version, validate_sha256, validate_stable_id
from empirical_lawhood.execution.response_experiment_ports import NativeAcquisitionRequest
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView
from empirical_lawhood.domains.matrix.six_matrix_response.model import ComplexArray, SixMatrixState, hermiticity_residual
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import SixMatrixResponseShootingCommittorCheckpoint, brownian_bridge_split, state_from_shooting_checkpoint
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import BAOABGradientCache, baoab_step_with_hermitian_noise, hermitian_noise


REACTIVE_ENTRANCE_HDF5_SCHEMA = 'empirical-lawhood/simulators/six-matrix-response/reactive-entrance-precursor-phase-space-hdf5'


REACTIVE_ENTRANCE_HDF5_MEDIA_TYPE = "application/x-hdf5"


REACTIVE_ENTRANCE_CANONICAL_MEDIA_TYPE = "application/vnd.empirical-lawhood.canonical+json"


REACTIVE_ENTRANCE_SOURCE_SEED_RULE = "matrix-response-reactive-entrance.precursor-pcg64dxsm.plan-source-bound"


REACTIVE_ENTRANCE_BRIDGE_SEED_RULE = "matrix-response-reactive-entrance.bridge-pcg64dxsm.plan-source-bound"


REACTIVE_ENTRANCE_FINE_SUBSET_RULE = "matrix-response-reactive-entrance.fine-subset.explicit-original-128-roster"


REACTIVE_ENTRANCE_COHORT_ID = "matrix-response-reactive-entrance.law-development"


REACTIVE_ENTRANCE_PRIMARY_MEMBER_ID = "matrix-response-reactive-entrance.primary"


REACTIVE_ENTRANCE_FINE_MEMBER_ID = "matrix-response-reactive-entrance.brownian-bridge-dt-half"


REACTIVE_ENTRANCE_ROOT_COUNT = 512


REACTIVE_ENTRANCE_FINE_COUNT = 128


REACTIVE_ENTRANCE_PRIMARY_STEPS = 512


REACTIVE_ENTRANCE_FINE_STEPS = 1024


REACTIVE_ENTRANCE_RECEIVER_CADENCE = 16


MATRIX_RESPONSE_SHOOTING_COMMITTOR_COHORT_RESULT_SCHEMA = 'empirical-lawhood/methods/matrix-response-study/matrix-response-shooting-committor-cohort-result'


REACTIVE_ENTRANCE_HDF5_UNITS = (
    '{"/noise/standardized":"standard-normal-complex-hermitian",'
    '"/state/alpha_tilde":"dimensionless-scaled-coupling",'
    '"/state/momenta":"dimensionless-canonical-momentum",'
    '"/state/positions":"dimensionless-matrix-coordinate",'
    '"/state/step_index":"integration-step"}'
)


REACTIVE_ENTRANCE_HDF5_FRAMES = (
    '{"/noise/standardized":"six-matrix-response.frame.six-matrix-hermitian",'
    '"/state/alpha_tilde":"six-matrix-response.frame.xy-coupling",'
    '"/state/momenta":"six-matrix-response.frame.six-matrix-hermitian",'
    '"/state/positions":"six-matrix-response.frame.six-matrix-hermitian",'
    '"/state/step_index":"six-matrix-response.frame.integration-index"}'
)


REACTIVE_ENTRANCE_HDF5_CLOCKS = (
    '{"/noise/standardized":"six-matrix-response.clock.native-integration-step",'
    '"/state/alpha_tilde":"six-matrix-response.clock.native-integration-step",'
    '"/state/momenta":"six-matrix-response.clock.native-integration-step",'
    '"/state/positions":"six-matrix-response.clock.native-integration-step",'
    '"/state/step_index":"six-matrix-response.clock.native-integration-step"}'
)


REACTIVE_ENTRANCE_HDF5_KEYS = (
    '["/noise/standardized","/state/alpha_tilde","/state/momenta",'
    '"/state/positions","/state/step_index"]'
)


class SixMatrixResponseReactiveEntranceHalf(StrEnum):
    FIRST = "FIRST"
    SECOND = "SECOND"


class SixMatrixResponseReactiveEntranceNumericalViewKind(StrEnum):
    PRIMARY = "PRIMARY"
    SAME_DRIVER_HALF = "SAME_DRIVER_HALF"


class SixMatrixResponseReactiveEntrancePrecursorTerminal(StrEnum):
    COMPLETED = "COMPLETED"
    NUMERICAL_INVALID = "NUMERICAL_INVALID"


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntranceSlot(CanonicalRecord):
    """One physical conditional Wiener future and its nested view identities."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/six-matrix-response-reactive-entrance-slot'

    slot_id: str
    slot_index: int
    cohort_id: str
    half: SixMatrixResponseReactiveEntranceHalf
    physical_independent_unit_id: str
    preparation_instance_id: str
    primary_acquisition_group_id: str
    primary_view_id: str
    fine_acquisition_group_id: str | None
    fine_view_id: str | None

    def __post_init__(self) -> None:
        for name in (
            "slot_id",
            "cohort_id",
            "physical_independent_unit_id",
            "preparation_instance_id",
            "primary_acquisition_group_id",
            "primary_view_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.fine_acquisition_group_id is not None:
            validate_stable_id(
                self.fine_acquisition_group_id,
                field_name="fine_acquisition_group_id",
            )
        if self.fine_view_id is not None:
            validate_stable_id(self.fine_view_id, field_name="fine_view_id")
        if not 0 <= self.slot_index < REACTIVE_ENTRANCE_ROOT_COUNT:
            raise ValueError("matrix response reactive entrance slot index differs")
        expected_half = SixMatrixResponseReactiveEntranceHalf.FIRST if self.slot_index < 256 else SixMatrixResponseReactiveEntranceHalf.SECOND
        if self.half is not expected_half or self.cohort_id != REACTIVE_ENTRANCE_COHORT_ID:
            raise ValueError("matrix response reactive entrance slot half/cohort differs")
        if (self.fine_acquisition_group_id is None) != (self.fine_view_id is None):
            raise ValueError("matrix response reactive entrance fine acquisition/view identity is incomplete")

    @property
    def has_fine_view(self) -> bool:
        return self.fine_view_id is not None


def build_six_matrix_response_reactive_entrance_slots(*, checkpoint_sha256: str, scientific_inputs: MatrixReactiveEntranceScientificInputs) -> tuple[SixMatrixResponseReactiveEntranceSlot, ...]:
    """Bind all 512 roots and the complete original 128-root numerical subset."""

    validate_sha256(checkpoint_sha256, field_name="checkpoint_sha256")
    if not isinstance(scientific_inputs, MatrixReactiveEntranceScientificInputs):
        raise ValueError("reactive-entrance slots require explicit scientific inputs")
    scientific_inputs.require_target_checkpoint(checkpoint_sha256)
    fine = frozenset(value.slot_index for value in scientific_inputs.roots if value.has_fine_view)
    values: list[SixMatrixResponseReactiveEntranceSlot] = []
    for index in range(REACTIVE_ENTRANCE_ROOT_COUNT):
        stem = f"matrix-response-reactive-entrance.ld.r{index:04d}"
        values.append(
            SixMatrixResponseReactiveEntranceSlot(
                slot_id=f"slot.{stem}",
                slot_index=index,
                cohort_id=REACTIVE_ENTRANCE_COHORT_ID,
                half=(SixMatrixResponseReactiveEntranceHalf.FIRST if index < 256 else SixMatrixResponseReactiveEntranceHalf.SECOND),
                physical_independent_unit_id=f"unit.{stem}",
                preparation_instance_id=f"preparation.{stem}",
                primary_acquisition_group_id=f"acquisition.{stem}.primary",
                primary_view_id=f"view.{stem}.primary",
                fine_acquisition_group_id=(f"acquisition.{stem}.fine" if index in fine else None),
                fine_view_id=f"view.{stem}.fine" if index in fine else None,
            )
        )
    return tuple(values)


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntranceSourceConfig(CanonicalRecord):
    """All native choices required to reproduce the fixed reactive entrance source corpus."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/six-matrix-response-reactive-entrance-source-config'

    config_id: str
    config_version: str
    plan_sha256: str
    source_cohort: ObjectIdentity
    checkpoint: SixMatrixResponseShootingCommittorCheckpoint
    member: SixMatrixResponseModelFamilyMember
    primary_view: SixMatrixResponseNumericalView
    half_view: SixMatrixResponseNumericalView
    slots: tuple[SixMatrixResponseReactiveEntranceSlot, ...]
    scientific_inputs: MatrixReactiveEntranceScientificInputs
    source_seed_rule_id: str
    bridge_seed_rule_id: str
    fine_subset_rule_id: str
    primary_steps: int
    fine_steps: int
    receiver_cadence_parent_steps: int
    target_alpha_tilde_x: Decimal
    target_alpha_tilde_y: Decimal
    hdf5_payload_schema: str
    source_instance_count: int
    grants_authority: bool
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self) -> None:
        for name in (
            "config_id",
            "source_seed_rule_id",
            "bridge_seed_rule_id",
            "fine_subset_rule_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        validate_schema(self.hdf5_payload_schema)
        validate_semantic_version(self.config_version)
        validate_sha256(self.plan_sha256, field_name="plan_sha256")
        if not isinstance(self.scientific_inputs, MatrixReactiveEntranceScientificInputs):
            raise ValueError("reactive-entrance source requires explicit original scientific inputs")
        self.scientific_inputs.require_target_roots(
            plan_sha256=self.plan_sha256, source_cohort_sha256=self.source_cohort.object_fingerprint
        )
        self.scientific_inputs.require_target_checkpoint(self.checkpoint.combined_state_sha256)
        if self.source_cohort.object_schema != MATRIX_RESPONSE_SHOOTING_COMMITTOR_COHORT_RESULT_SCHEMA:
            raise ValueError("matrix response reactive entrance source cohort schema differs")
        if (
            self.checkpoint.parent_step != 816
            or self.checkpoint.q != 2
            or self.member.member_id != "six-matrix-response.member.mass-0p5.cross-coupling-1"
            or self.primary_view.timestep != Decimal("0.001")
            or self.half_view.timestep != Decimal("0.0005")
            or self.primary_view.friction_gamma != self.half_view.friction_gamma
            or self.primary_view.bath_temperature != self.half_view.bath_temperature
        ):
            raise ValueError("matrix response reactive entrance fixed source denominator differs")
        require_sorted_unique_ids(self.slots, attribute="slot_id", field_name="slots")
        if (
            len(self.slots) != REACTIVE_ENTRANCE_ROOT_COUNT
            or tuple(value.slot_index for value in self.slots) != tuple(range(REACTIVE_ENTRANCE_ROOT_COUNT))
            or sum(value.has_fine_view for value in self.slots) != REACTIVE_ENTRANCE_FINE_COUNT
            or self.slots
            != build_six_matrix_response_reactive_entrance_slots(checkpoint_sha256=self.checkpoint.combined_state_sha256, scientific_inputs=self.scientific_inputs)
        ):
            raise ValueError("matrix response reactive entrance source roster differs")
        if (
            self.source_seed_rule_id != REACTIVE_ENTRANCE_SOURCE_SEED_RULE
            or self.bridge_seed_rule_id != REACTIVE_ENTRANCE_BRIDGE_SEED_RULE
            or self.fine_subset_rule_id != REACTIVE_ENTRANCE_FINE_SUBSET_RULE
            or (self.primary_steps, self.fine_steps, self.receiver_cadence_parent_steps)
            != (
                REACTIVE_ENTRANCE_PRIMARY_STEPS,
                REACTIVE_ENTRANCE_FINE_STEPS,
                REACTIVE_ENTRANCE_RECEIVER_CADENCE,
            )
            or self.hdf5_payload_schema != REACTIVE_ENTRANCE_HDF5_SCHEMA
            or self.source_instance_count != 1
        ):
            raise ValueError("matrix response reactive entrance fixed source contract differs")
        for name in ("target_alpha_tilde_x", "target_alpha_tilde_y"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if (
            self.target_alpha_tilde_x != Decimal("0.6666666666666666666666666667")
            or self.target_alpha_tilde_y != Decimal("7.333333333333333333333333334")
            or self.grants_authority
            or self.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
        ):
            raise ValueError("matrix response reactive entrance source config exceeds its fixed claim/authority")

    def slot(self, slot_index: int) -> SixMatrixResponseReactiveEntranceSlot:
        if not 0 <= slot_index < len(self.slots):
            raise KeyError(slot_index)
        return self.slots[slot_index]


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntrancePrecursorRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/six-matrix-response-reactive-entrance-precursor-request'

    request_id: str
    task_id: str
    result_output_id: str
    trajectory_output_id: str
    source_config: ObjectIdentity
    neutral_request: NativeAcquisitionRequest
    slot: SixMatrixResponseReactiveEntranceSlot
    numerical_view_kind: SixMatrixResponseReactiveEntranceNumericalViewKind
    numerical_member_id: str
    acquisition_group_id: str
    scientific_view_id: str
    integration_steps: int
    receiver_cadence_parent_steps: int
    evidence_ceiling: EvidenceCeiling
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    grants_authority: bool

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "task_id",
            "result_output_id",
            "trajectory_output_id",
            "numerical_member_id",
            "acquisition_group_id",
            "scientific_view_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        primary = self.numerical_view_kind is SixMatrixResponseReactiveEntranceNumericalViewKind.PRIMARY
        if primary:
            expected: tuple[str, str | None, str | None, int] = (
                REACTIVE_ENTRANCE_PRIMARY_MEMBER_ID,
                self.slot.primary_acquisition_group_id,
                self.slot.primary_view_id,
                REACTIVE_ENTRANCE_PRIMARY_STEPS,
            )
        else:
            if not self.slot.has_fine_view:
                raise ValueError("matrix response reactive entrance fine request names a non-fine slot")
            expected = (
                REACTIVE_ENTRANCE_FINE_MEMBER_ID,
                self.slot.fine_acquisition_group_id,
                self.slot.fine_view_id,
                REACTIVE_ENTRANCE_FINE_STEPS,
            )
        if (
            (
                self.numerical_member_id,
                self.acquisition_group_id,
                self.scientific_view_id,
                self.integration_steps,
            )
            != expected
            or self.receiver_cadence_parent_steps != REACTIVE_ENTRANCE_RECEIVER_CADENCE
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
            or self.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or self.grants_authority
        ):
            raise ValueError("matrix response reactive entrance precursor request contract differs")
        if (
            self.neutral_request.physical_independent_unit_id
            != self.slot.physical_independent_unit_id
            or self.neutral_request.acquisition_group_id != self.acquisition_group_id
            or self.neutral_request.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or self.neutral_request.grants_execution_authority
        ):
            raise ValueError("matrix response reactive entrance neutral acquisition request differs")


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntranceNoiseReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/six-matrix-response-reactive-entrance-noise-receipt'

    receipt_id: str
    physical_independent_unit_id: str
    numerical_view_kind: SixMatrixResponseReactiveEntranceNumericalViewKind
    source_seed_rule_id: str
    source_seed_sha256: str
    bridge_seed_rule_id: str | None
    bridge_seed_sha256: str | None
    coarse_driver_sha256: str
    realized_innovation_sha256: str
    terminal_rng_state_sha256: str
    coarse_step_count: int
    realized_step_count: int
    same_driver: bool

    def __post_init__(self) -> None:
        for name in ("receipt_id", "physical_independent_unit_id", "source_seed_rule_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        for name in (
            "source_seed_sha256",
            "coarse_driver_sha256",
            "realized_innovation_sha256",
            "terminal_rng_state_sha256",
        ):
            validate_sha256(getattr(self, name), field_name=name)
        if self.bridge_seed_rule_id is not None:
            validate_stable_id(self.bridge_seed_rule_id, field_name="bridge_seed_rule_id")
        if self.bridge_seed_sha256 is not None:
            validate_sha256(self.bridge_seed_sha256, field_name="bridge_seed_sha256")
        fine = self.numerical_view_kind is SixMatrixResponseReactiveEntranceNumericalViewKind.SAME_DRIVER_HALF
        if (
            self.source_seed_rule_id != REACTIVE_ENTRANCE_SOURCE_SEED_RULE
            or (self.bridge_seed_rule_id is None) == fine
            or (self.bridge_seed_sha256 is None) == fine
            or self.coarse_step_count != REACTIVE_ENTRANCE_PRIMARY_STEPS
            or self.realized_step_count != (REACTIVE_ENTRANCE_FINE_STEPS if fine else REACTIVE_ENTRANCE_PRIMARY_STEPS)
            or self.same_driver != fine
        ):
            raise ValueError("matrix response reactive entrance noise receipt differs")


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntrancePrecursorResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/six-matrix-response/six-matrix-response-reactive-entrance-precursor-result'

    result_id: str
    task_id: str
    result_output_id: str
    trajectory_output_id: str
    request: ObjectIdentity
    neutral_request: ObjectIdentity
    source_config: ObjectIdentity
    slot_id: str
    slot_index: int
    physical_independent_unit_id: str
    acquisition_group_id: str
    scientific_view_id: str
    numerical_member_id: str
    numerical_view_kind: SixMatrixResponseReactiveEntranceNumericalViewKind
    terminal: SixMatrixResponseReactiveEntrancePrecursorTerminal
    completed_steps: int
    total_steps: int
    state_count: int
    initial_positions_sha256: str
    initial_momenta_sha256: str
    terminal_positions_sha256: str
    terminal_momenta_sha256: str
    phase_space_sha256: str
    noise: SixMatrixResponseReactiveEntranceNoiseReceipt
    hdf5_payload_schema: str
    hdf5_physical_sha256: str
    hdf5_size_bytes: int
    scientific_verdict_constructed: bool
    reason_codes: tuple[str, ...]
    evidence_ceiling: EvidenceCeiling
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    grants_authority: bool

    def __post_init__(self) -> None:
        for name in (
            "result_id",
            "task_id",
            "result_output_id",
            "trajectory_output_id",
            "slot_id",
            "physical_independent_unit_id",
            "acquisition_group_id",
            "scientific_view_id",
            "numerical_member_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        validate_schema(self.hdf5_payload_schema)
        for name in (
            "initial_positions_sha256",
            "initial_momenta_sha256",
            "terminal_positions_sha256",
            "terminal_momenta_sha256",
            "phase_space_sha256",
            "hdf5_physical_sha256",
        ):
            validate_sha256(getattr(self, name), field_name=name)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (
            not 0 <= self.completed_steps <= self.total_steps
            or self.state_count != self.completed_steps + 1
            or self.hdf5_size_bytes <= 0
            or self.hdf5_payload_schema != REACTIVE_ENTRANCE_HDF5_SCHEMA
            or self.scientific_verdict_constructed
            or self.evidence_ceiling is not EvidenceCeiling.MEASUREMENT
            or self.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or self.grants_authority
        ):
            raise ValueError("matrix response reactive entrance precursor result contract differs")
        complete = self.completed_steps == self.total_steps and not self.reason_codes
        if (self.terminal is SixMatrixResponseReactiveEntrancePrecursorTerminal.COMPLETED) != complete:
            raise ValueError("matrix response reactive entrance precursor terminal differs")


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntranceExecutedPrecursor:
    result: SixMatrixResponseReactiveEntrancePrecursorResult
    hdf5_payload: bytes
    states: tuple[SixMatrixState, ...]
    innovations: ComplexArray

    def __post_init__(self) -> None:
        values = np.asarray(self.innovations)
        if (
            sha256(self.hdf5_payload).hexdigest() != self.result.hdf5_physical_sha256
            or len(self.hdf5_payload) != self.result.hdf5_size_bytes
            or len(self.states) != self.result.state_count
            or values.shape != (self.result.completed_steps, 2, 3, 4, 4)
            or values.dtype != np.dtype("complex128")
        ):
            raise ValueError("matrix response reactive entrance executed precursor custody differs")
        copied = np.ascontiguousarray(values, dtype="<c16")
        copied.setflags(write=False)
        object.__setattr__(self, "innovations", copied)


@dataclass(frozen=True, slots=True)
class SixMatrixResponseReactiveEntrancePersistedPrecursor:
    result: SixMatrixResponseReactiveEntrancePrecursorResult
    states: tuple[SixMatrixState, ...]
    innovations: ComplexArray

    def __post_init__(self) -> None:
        values = np.asarray(self.innovations)
        if (
            len(self.states) != self.result.state_count
            or values.shape != (self.result.completed_steps, 2, 3, 4, 4)
            or values.dtype != np.dtype("complex128")
        ):
            raise ValueError("matrix response reactive entrance persisted precursor geometry differs")
        copied = np.ascontiguousarray(values, dtype="<c16")
        copied.setflags(write=False)
        object.__setattr__(self, "innovations", copied)


def _rng(*, scientific_seed_sha256: str) -> tuple[np.random.Generator, str]:
    validate_sha256(scientific_seed_sha256, field_name="scientific_seed_sha256")
    digest = bytes.fromhex(scientific_seed_sha256)
    return (
        np.random.Generator(np.random.PCG64DXSM(int.from_bytes(digest[:16], "big"))),
        scientific_seed_sha256,
    )


def _phase_space_sha256(states: tuple[SixMatrixState, ...]) -> str:
    digest = sha256()
    for state in states:
        digest.update(np.ascontiguousarray(state.positions, dtype="<c16").tobytes())
        digest.update(np.ascontiguousarray(state.momenta, dtype="<c16").tobytes())
    return digest.hexdigest()


def _driver_receipt(
    *,
    request: SixMatrixResponseReactiveEntrancePrecursorRequest,
    coarse_seed: str,
    bridge_seed: str | None,
    coarse: ComplexArray,
    realized: ComplexArray,
    coarse_rng: np.random.Generator,
    bridge_rng: np.random.Generator | None,
) -> SixMatrixResponseReactiveEntranceNoiseReceipt:
    document = {
        "coarse": coarse_rng.bit_generator.state,
        "bridge": None if bridge_rng is None else bridge_rng.bit_generator.state,
    }
    rng_state = json.dumps(document, sort_keys=True, separators=(",", ":"))
    fine = request.numerical_view_kind is SixMatrixResponseReactiveEntranceNumericalViewKind.SAME_DRIVER_HALF
    return SixMatrixResponseReactiveEntranceNoiseReceipt(
        receipt_id=f"noise-receipt.{request.request_id}",
        physical_independent_unit_id=request.slot.physical_independent_unit_id,
        numerical_view_kind=request.numerical_view_kind,
        source_seed_rule_id=REACTIVE_ENTRANCE_SOURCE_SEED_RULE,
        source_seed_sha256=coarse_seed,
        bridge_seed_rule_id=REACTIVE_ENTRANCE_BRIDGE_SEED_RULE if fine else None,
        bridge_seed_sha256=bridge_seed,
        coarse_driver_sha256=sha256(
            np.ascontiguousarray(coarse, dtype="<c16").tobytes()
        ).hexdigest(),
        realized_innovation_sha256=sha256(
            np.ascontiguousarray(realized, dtype="<c16").tobytes()
        ).hexdigest(),
        terminal_rng_state_sha256=sha256(rng_state.encode("utf-8")).hexdigest(),
        coarse_step_count=REACTIVE_ENTRANCE_PRIMARY_STEPS,
        realized_step_count=request.integration_steps,
        same_driver=fine,
    )


def integrate_reactive_entrance(*, config: SixMatrixResponseReactiveEntranceSourceConfig, request: SixMatrixResponseReactiveEntrancePrecursorRequest):
    """Execute one action-free primary or exact same-driver half-step future."""
    gradient_cache_state = BAOABGradientCache()
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    if request.source_config != config_identity or request.slot != config.slot(request.slot.slot_index):
        raise ValueError('matrix response reactive entrance precursor request changes its frozen source')
    checkpoint_state, _ = state_from_shooting_checkpoint(config.checkpoint)
    state = SixMatrixState(q=checkpoint_state.q, positions=checkpoint_state.positions, momenta=checkpoint_state.momenta, step_index=0, alpha_tilde_x=checkpoint_state.alpha_tilde_x, alpha_tilde_y=checkpoint_state.alpha_tilde_y)
    coarse_rng, coarse_seed = _rng(scientific_seed_sha256=config.scientific_inputs.roots[request.slot.slot_index].source_seed_sha256)
    coarse = np.ascontiguousarray(np.stack([hermitian_noise(rng=coarse_rng, q=2) for _ in range(REACTIVE_ENTRANCE_PRIMARY_STEPS)]), dtype='<c16')
    bridge_rng: np.random.Generator | None = None
    bridge_seed: str | None = None
    if request.numerical_view_kind is SixMatrixResponseReactiveEntranceNumericalViewKind.PRIMARY:
        realized = coarse
        view = config.primary_view
    else:
        bridge_rng, bridge_seed = _rng(scientific_seed_sha256=config.scientific_inputs.roots[request.slot.slot_index].bridge_seed_sha256)
        bridge = np.ascontiguousarray(np.stack([hermitian_noise(rng=bridge_rng, q=2) for _ in range(REACTIVE_ENTRANCE_PRIMARY_STEPS)]), dtype='<c16')
        half_decay = float(np.exp(-float(config.primary_view.friction_gamma) * float(config.primary_view.timestep) / 2.0))
        halves = [brownian_bridge_split(coarse_noise=coarse_noise, bridge_noise=bridge_noise, half_decay=half_decay) for coarse_noise, bridge_noise in zip(coarse, bridge, strict=True)]
        realized = np.ascontiguousarray(np.stack([value for pair in halves for value in pair]), dtype='<c16')
        view = config.half_view
    states = [state]
    reasons: set[str] = set()
    for noise in realized:
        try:
            state = baoab_step_with_hermitian_noise(state, member=config.member, numerical_view=view, next_alpha_tilde_x=float(config.target_alpha_tilde_x), next_alpha_tilde_y=float(config.target_alpha_tilde_y), standardized_noise=noise, gradient_cache=gradient_cache_state)
        except (FloatingPointError, OverflowError, ValueError, np.linalg.LinAlgError):
            reasons.add('numerical-step-failed')
            break
        if not state.finite or hermiticity_residual(state.positions) > 1e-10:
            reasons.add('nonfinite-or-nonhermitian-state')
            break
        states.append(state)
    state_tuple = tuple(states)
    completed = len(state_tuple) - 1
    realized_prefix = np.ascontiguousarray(realized[:completed], dtype='<c16')
    noise_receipt = _driver_receipt(request=request, coarse_seed=coarse_seed, bridge_seed=bridge_seed, coarse=coarse, realized=realized, coarse_rng=coarse_rng, bridge_rng=bridge_rng)
    return (config_identity, state_tuple, completed, realized_prefix, noise_receipt, reasons)
