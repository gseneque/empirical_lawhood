# SPDX-License-Identifier: MPL-2.0
"""Selected-event populations, exact replay records and scientific invariants."""

import base64
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest
from empirical_lawhood.domains.matrix.matrix_response_study.selected_event_inputs import MatrixSelectedEventConfig
from empirical_lawhood.domains.matrix.matrix_response_study.geometry_records import MatrixGeometryScanInput
from empirical_lawhood.domains.matrix.matrix_response_study.geometry_inputs import validate_geometry_source
from empirical_lawhood.domains.matrix.matrix_response_study import anisotropic_feasibility as geometry
from empirical_lawhood.domains.matrix.matrix_response_study import shooting_committor as shooting
from empirical_lawhood.domains.matrix.six_matrix_response import shooting as native
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import SixMatrixResponseSixMatrixSourceConfig
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import SixMatrixResponseRNGStreamReceipt

SELECTED_EVENT_INPUT_MAXIMUM_BYTES = 16 * 1024**2
SELECTED_EVENT_RESULT_MAXIMUM_BYTES = 16 * 1024**2
PUBLIC_SELECTED_EVENT_MASTER_SEED = 706607
NOMINATED_PARENT_DRIVER = "a0d387ebd22b510ccf5816ba09c1724780cff7bec5e7bf99ae4a518d28242cb9"
NOMINATED_PARENT_FINAL_STATE = "d1dd5ed2501e10de345110f59c4e1ed7ebe23065f5947eea848248cf090dcad5"
ORIGINAL_NUMERICAL_QUALIFICATION = "7530d6361529c0b97eb2094c38ab8bfa9f4f039d12a840f30bc149e436db281b"
CHECKPOINT_STEPS = (816, 848, 880, 896, 928, 960, 1024)


@dataclass(frozen=True, slots=True)
class MatrixSelectedParentRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/selected-events/parent-request"
    config_id: str
    source: SixMatrixResponseSixMatrixSourceConfig
    scientific_code_sha256: str
    environment_lock_sha256: str
    minimum_free_bytes: int = 1024**3
    maximum_output_bytes: int = SELECTED_EVENT_RESULT_MAXIMUM_BYTES

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        validate_geometry_source(self.source)
        for name in ("scientific_code_sha256", "environment_lock_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        if self.minimum_free_bytes < 1 or self.maximum_output_bytes != SELECTED_EVENT_RESULT_MAXIMUM_BYTES:
            raise ValueError("Selected parent requires bounded explicit storage")

    @property
    def run_id(self):
        return f"selected-parent.run-{self.fingerprint()[:32]}"



@dataclass(frozen=True, slots=True)
class MatrixSelectedParentOperand(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/selected-events/parent-operand"
    operand_id: str
    request_sha256: str
    conditional_source_instance: str
    source_config: ObjectIdentity
    rollout: geometry.MatrixResponseAnisotropicFeasibilityRolloutSummary
    implementation_commit: str
    numerical_qualification_sha256: str
    source_report: ObjectIdentity | None
    source_geometry_config: MatrixGeometryScanInput | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.operand_id, field_name="operand_id")
        validate_sha256(self.request_sha256, field_name="request_sha256")
        validate_sha256(self.numerical_qualification_sha256, field_name="numerical_qualification_sha256")
        if self.conditional_source_instance not in ("paper-nominated", "current-alternate"):
            raise ValueError("Selected parent requires an explicit conditional source instance")
        row = self.rollout
        if (not row.valid or row.q != 2 or row.stage is not geometry.MatrixResponseAnisotropicFeasibilityStage.FEASIBILITY
            or row.history_id != "matrix-history.joint-increasing-coupling"
            or row.constitution.value != "01" or row.factor_y.final_phi is None
            or row.requested_steps != 1024):
            raise ValueError("Selected parent is absent, invalid or has no admitted geometric event")
        if self.conditional_source_instance == "paper-nominated" and (
            row.alpha_x_index, row.alpha_y_index, row.seed_index, row.rng_seed_sha256, row.final_state_sha256) != (
                1, 11, 1, NOMINATED_PARENT_DRIVER, NOMINATED_PARENT_FINAL_STATE):
            raise ValueError("Paper nominated mathematical parent cannot be replaced")
        if self.conditional_source_instance == "current-alternate" and (self.source_report is None or self.source_geometry_config is None):
            raise ValueError("Alternate selected parent lacks its exact current geometry report")

    @property
    def rollouts(self):
        return (self.rollout,)



@dataclass(frozen=True, slots=True)
class MatrixSelectedFutureSeed(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/selected-events/future-seed"
    checkpoint_step: int
    stream_index: int
    full_seed_sha256: str

    def __post_init__(self) -> None:
        if type(self.checkpoint_step) is not int or type(self.stream_index) is not int:
            raise ValueError("Selected-event allocation requires integer scientific coordinates")
        validate_sha256(self.full_seed_sha256, field_name="full_seed_sha256")



@dataclass(frozen=True, slots=True)
class MatrixSelectedEventInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/selected-events/input"
    config_id: str
    parent_request: MatrixSelectedParentRequest
    parent: ArtifactManifest
    null_reference: MatrixGeometryScanInput
    protocol: MatrixSelectedEventConfig
    branch_seeds: tuple[MatrixSelectedFutureSeed, ...]
    bridge_seeds: tuple[MatrixSelectedFutureSeed, ...]
    prior_exposed_seed_sha256s: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if tuple((s.checkpoint_step, s.stream_index) for s in self.branch_seeds) != tuple((step, i) for step in CHECKPOINT_STEPS for i in range(64)):
            raise ValueError("Selected event requires all seven complete 64-future cohorts")
        if tuple((s.checkpoint_step, s.stream_index) for s in self.bridge_seeds) != tuple((0, i) for i in range(1, 1025)):
            raise ValueError("Selected event requires the complete same-driver bridge allocation")
        if self.parent_request.source != self.null_reference.source:
            raise ValueError("Selected-event null reference uses another numerical source preset")
        if self.parent.logical.payload_schema != MatrixSelectedParentOperand.SCHEMA:
            raise ValueError("Selected-event parent has another scientific role/schema")
        seeds = tuple(s.full_seed_sha256 for s in (*self.branch_seeds, *self.bridge_seeds))
        effective = tuple(s[:32] for s in seeds)
        if len(set(effective)) != len(effective):
            raise ValueError("Selected event repeats an effective future/bridge stream")
        if tuple(sorted(set(self.prior_exposed_seed_sha256s))) != self.prior_exposed_seed_sha256s:
            raise ValueError("Selected event prior exposure census must be sorted and unique")
        for seed in self.prior_exposed_seed_sha256s:
            validate_sha256(seed, field_name="prior_exposed_seed_sha256s")
        excluded = {NOMINATED_PARENT_DRIVER[:32], self.protocol.parent_rng_seed_sha256[:32], *(s[:32] for s in self.prior_exposed_seed_sha256s)}
        if set(effective) & excluded:
            raise ValueError("Selected event reuses its exposed parent or previously exposed effective driver")

    @property
    def source(self):
        return self.parent_request.source

    @property
    def scientific_code_sha256(self):
        return self.parent_request.scientific_code_sha256

    @property
    def environment_lock_sha256(self):
        return self.parent_request.environment_lock_sha256

    @property
    def minimum_free_bytes(self):
        return self.parent_request.minimum_free_bytes

    @property
    def maximum_output_bytes(self):
        return self.parent_request.maximum_output_bytes

    @property
    def run_id(self):
        return f"selected-event.run-{self.fingerprint()[:32]}"



@dataclass(frozen=True, slots=True)
class MatrixSelectedReplayTransport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/selected-events/exact-replay-transport"
    replay_result: shooting.MatrixResponseShootingCommittorReplayResult
    coarse_noises_base64: tuple[str, ...]
    rng_stream: SixMatrixResponseRNGStreamReceipt

    def __post_init__(self):
        if len(self.coarse_noises_base64) != 1024:
            raise ValueError("Selected replay transport omits original coarse innovations")
        for value in self.coarse_noises_base64:
            raw = base64.b64decode(value, validate=True)
            if len(raw) != 1536 or base64.b64encode(raw).decode("ascii") != value:
                raise ValueError("Selected replay innovation has another exact complex128 geometry")

    def replay(self):
        import numpy as np
        checkpoints = self.replay_result.checkpoints
        states = tuple(native.state_from_shooting_checkpoint(c)[0] for c in checkpoints)
        noises = tuple(np.frombuffer(base64.b64decode(raw), dtype="<c16").reshape((2, 3, 4, 4)) for raw in self.coarse_noises_base64)
        if any(not np.isfinite(noise).all() for noise in noises):
            raise ValueError("Selected replay contains nonfinite original innovations")
        return native.SixMatrixResponseShootingCommittorReplayData(checkpoints, states, noises,
            states[-1], checkpoints[-1].rng_state_json, self.rng_stream,
            self.replay_result.observed_final_state_sha256)

