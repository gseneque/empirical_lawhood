# SPDX-License-Identifier: MPL-2.0
"""Additive selected E6 configurations with seedless frozen transport scope."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
from .selected_produced_inputs import validate_produced_input_parents
from empirical_lawhood.kernel.serialization import CanonicalRecord

from .e6_transport_records import MatrixE6EmpiricalTransportPolicy, MatrixE6FrozenCalibrationProjection
from .e6_transport_science import validate_e6_public_calibration_projection, validate_e6_transport_scope
from .prepared_point import MatrixPreparedPublicSource
from .selected_future import MatrixSelectedFutureConfig, MatrixSelectedFutureConfigV2, NAMESPACE
from .selected_original_commitments import MatrixSelectedEntryEvidenceV3
from .selected_protected_programme import MatrixSelectedPreparedConfig, MatrixSelectedPublicProgramme, global_node

ENTRY_TRANSPORT_KEY = NAMESPACE + ".entry-empirical-transport"


def validate_transport_source(policy, projection, source):
    if type(policy) is not MatrixE6EmpiricalTransportPolicy or type(projection) is not MatrixE6FrozenCalibrationProjection:
        raise TypeError("selected E6 requires its exact frozen policy and calibration projection")
    policy.__post_init__()
    projection.__post_init__()
    public = source if type(source) is MatrixPreparedPublicSource else MatrixPreparedPublicSource.from_source(source)
    root = public.original.root
    if (projection.policy != policy.identity or projection.specification != policy.candidate_specification
            or projection.endpoint_order != policy.endpoint_order or projection.calibration_alpha != policy.calibration_alpha
            or (root.regime_id, root.root_id, root.independent_group_id, public.original.source) not in
                tuple(row[1:] for row in policy.regime_roster)):
        raise ValueError("selected E6 configuration substitutes original source or empirical transport scope")


@dataclass(frozen=True, slots=True)
class MatrixSelectedTransportRootConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-transport-root-config"
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    programme: MatrixSelectedPublicProgramme
    phase: str
    transport_policy: MatrixE6EmpiricalTransportPolicy
    transport_calibration: MatrixE6FrozenCalibrationProjection
    produced_input_parents: tuple[ArtifactLineageParent, ...]
    entry_evidence: ObjectIdentity | None = None
    entry_evidence_size_bytes: int | None = None

    def __post_init__(self):
        validate_produced_input_parents(self.produced_input_parents)
        if (type(self.programme) is not MatrixSelectedPublicProgramme or self.phase not in ("entry", "assess-programme")
                or self.config_id != "config." + global_node(self.programme, self.phase)):
            raise ValueError("selected E6 transport root changes its exact complete phase configuration")
        validate_e6_transport_scope(self.transport_policy, self.programme)
        validate_e6_public_calibration_projection(self.transport_calibration, self.transport_policy, self.programme.point_design.package)
        if self.phase == "entry":
            if (type(self.entry_evidence) is not ObjectIdentity or self.entry_evidence.object_schema != MatrixSelectedEntryEvidenceV3.SCHEMA
                    or type(self.entry_evidence_size_bytes) is not int or self.entry_evidence_size_bytes < 1):
                raise ValueError("selected E6 entry requires exact actual committed original evidence")
        elif self.entry_evidence is not None or self.entry_evidence_size_bytes is not None:
            raise ValueError("selected E6 terminal cannot replace original entry evidence")


@dataclass(frozen=True, slots=True)
class MatrixSelectedTransportPointConfig(MatrixSelectedPreparedConfig):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-transport-point-config"
    transport_policy: MatrixE6EmpiricalTransportPolicy
    transport_calibration: MatrixE6FrozenCalibrationProjection

    def __post_init__(self):
        MatrixSelectedPreparedConfig.__post_init__(self)
        if self.phase != "point":
            raise ValueError("selected E6 causal decision selects only the original point phase")
        validate_transport_source(self.transport_policy, self.transport_calibration, self.public_source)


@dataclass(frozen=True, slots=True)
class MatrixSelectedTransportFutureConfig(MatrixSelectedFutureConfigV2):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-transport-future-config"
    transport_policy: MatrixE6EmpiricalTransportPolicy
    transport_calibration: MatrixE6FrozenCalibrationProjection

    def __post_init__(self):
        MatrixSelectedFutureConfigV2.__post_init__(self)
        validate_transport_source(self.transport_policy, self.transport_calibration, self.source)
        if self.frozen_package != self.transport_calibration.package:
            raise ValueError("selected E6 future substitutes its frozen original E3 package")


@dataclass(frozen=True, slots=True)
class MatrixSelectedTransportScoreConfig(MatrixSelectedFutureConfig):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-transport-score-config"
    transport_policy: MatrixE6EmpiricalTransportPolicy
    transport_calibration: MatrixE6FrozenCalibrationProjection

    def __post_init__(self):
        MatrixSelectedFutureConfig.__post_init__(self)
        if self.phase != "response-score":
            raise ValueError("selected E6 transport score selects only exact independent response assessment")
        validate_transport_source(self.transport_policy, self.transport_calibration, self.source)
        if self.frozen_package != self.transport_calibration.package:
            raise ValueError("selected E6 score substitutes its frozen original E3 package")
