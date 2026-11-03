# SPDX-License-Identifier: MPL-2.0
"""Complete shared assay mathematics, separate from each prepared subject.

Different source-specific protocol identities never count as different assay
methods. This record preserves every physical, template and numerical field;
actual source/protocol/publication joins remain the consuming owner's duty.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay, ScheduledResponseProtocol, physical_forecast_implementation
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id


ORIGIN = "PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME"
TOLERANCES = ("hessian_difference_step", "generic_gap_minimum", "spectral_gap_minimum", "radial_norm_minimum",
    "complement_gram_minimum", "native_reference_tolerance", "hessian_reference_tolerance", "weak_response_minimum", "receiver_gram_tolerance")


@dataclass(frozen=True, slots=True)
class MatrixPreparedAssayMethod(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-assay-method"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    criterion: ObjectIdentity
    mechanical_model: MatrixFactorResponseModel | MatrixOriginResponseModel
    actions: tuple[MatrixFactorAction, ...]
    horizon_steps: tuple[int, ...]
    receiver_count: int
    template_artifact: ArtifactIdentity
    template_members: tuple[MatrixArrayMember, ...]
    hessian_difference_step: Decimal
    generic_gap_minimum: Decimal
    spectral_gap_minimum: Decimal
    radial_norm_minimum: Decimal
    complement_gram_minimum: Decimal
    native_reference_tolerance: Decimal
    hessian_reference_tolerance: Decimal
    weak_response_minimum: Decimal
    receiver_gram_tolerance: Decimal
    origin_rule: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        matched = type(self.mechanical_model) is MatrixOriginResponseModel
        if (type(self.criterion) is not ObjectIdentity or type(self.mechanical_model) not in (MatrixFactorResponseModel, MatrixOriginResponseModel)
                or self.mechanical_model.implementation != physical_forecast_implementation()
                or type(self.actions) is not tuple or any(type(row) is not MatrixFactorAction for row in self.actions)
                or tuple(row.action_id for row in self.actions) != tuple(sorted({row.action_id for row in self.actions}))
                or tuple(sorted(row.role for row in self.actions)) != ACTION_ROLES or len({row.force_norm for row in self.actions}) != 1
                or self.horizon_steps != (DENSE_RESPONSE_HORIZONS if matched else (16, 64, 128))
                or type(self.receiver_count) is not int or self.receiver_count != 48
                or self.origin_rule != ORIGIN):
            raise ValueError("prepared assay method changes its complete original physical action/menu/receiver/origin contract")
        self.criterion.__post_init__()
        self.mechanical_model.__post_init__()
        for action in self.actions:
            action.__post_init__()
            if action.pulse_steps > self.horizon_steps[-1] or matched and action.pulse_steps != 16:
                raise ValueError("prepared assay pulse exceeds its original complete horizon")
        expected = {"generic_basis": ("<c16", (3, 4, 4)), "force_coefficients": ("<f8", (2, 3, 3)),
            "trace_coefficients": ("<f8", (2, 3)), "receiver_coefficients": ("<f8", (48, 2, 2, 3, 4))}
        if (type(self.template_artifact) is not ArtifactIdentity or self.template_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.template_artifact.media_type != "application/x-npz" or not 0 < self.template_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or type(self.template_members) is not tuple or any(type(row) is not MatrixArrayMember for row in self.template_members)
                or tuple(row.name for row in self.template_members) != tuple(sorted(expected))
                or {row.name: (row.dtype, row.shape) for row in self.template_members} != expected
                or any(not row.finite_required for row in self.template_members)
                or sum(row.size_bytes for row in self.template_members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError("prepared assay method changes its exact original bounded complete instrument templates")
        self.template_artifact.__post_init__()
        for member in self.template_members:
            member.__post_init__()
        positive = {"hessian_difference_step", "native_reference_tolerance", "hessian_reference_tolerance", "complement_gram_minimum", "receiver_gram_tolerance"}
        for name in TOLERANCES:
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if name in positive and value <= 0:
                raise ValueError("prepared assay method requires the original explicit positive numerical references")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @classmethod
    def from_assay(cls, record_id, assay):
        """Project the exact source-independent instrument without binding a source."""
        if type(assay) is not ScheduledResponseAssay:
            raise TypeError("prepared assay method requires its exact source-independent physical assay")
        assay.__post_init__()
        return cls(record_id, assay.criterion, assay.mechanical_model, assay.actions, assay.horizon_steps,
            assay.receiver_count, assay.array_artifact, assay.members,
            *(getattr(assay, name) for name in TOLERANCES), assay.origin_rule)

    @classmethod
    def from_protocol(cls, record_id, protocol):
        if type(protocol) is not ScheduledResponseProtocol:
            raise TypeError("prepared assay method requires its exact original source-specific physical protocol")
        protocol.__post_init__()
        return cls(record_id, protocol.criterion, protocol.mechanical_model, protocol.actions, protocol.horizon_steps,
            protocol.receiver_count, protocol.templates.array_artifact, protocol.templates.members,
            *(getattr(protocol, name) for name in TOLERANCES), protocol.origin_rule)

    def validate_protocol(self, protocol):
        if type(self) is not MatrixPreparedAssayMethod:
            raise TypeError("prepared assay comparison requires its exact shared method owner")
        self.__post_init__()
        if type(self).from_protocol(self.record_id, protocol) != self:
            raise ValueError("prepared matched source changes the frozen complete physical/template/numerical assay method")
