# SPDX-License-Identifier: MPL-2.0
"""Direct mathematical inputs to fresh native TRAIN and future reservations.

These definitions carry no issued study, old allocation, publication handle,
training bank, source qualification or execution authority.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixPolicy, coordinate_identity, identity
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id

from .response_frontier import MatrixResponseFrontierProtocol


@dataclass(frozen=True, slots=True)
class NativeTrainingScientificProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/native-training-scientific-protocol'
    protocol_id: str
    mathematical_protocol: MatrixResponseFrontierProtocol
    scalar_definition: MatrixParameterScalarDefinition
    coordinates: tuple[MatrixParameterCoordinate, ...]
    numerical_design: MatrixParameterNumericalDesign
    prefix_policies: tuple[ScheduledPrefixPolicy, ...]
    coordinate_policies: tuple[tuple[ObjectIdentity, ObjectIdentity], ...]

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        for value, kind in ((self.mathematical_protocol, MatrixResponseFrontierProtocol),
                (self.scalar_definition, MatrixParameterScalarDefinition),
                (self.numerical_design, MatrixParameterNumericalDesign)):
            if type(value) is not kind:
                raise TypeError('native scientific protocol requires exact mathematical definitions')
            value.__post_init__()
        for values, kind, attribute in ((self.coordinates, MatrixParameterCoordinate, 'coordinate_id'),
                (self.prefix_policies, ScheduledPrefixPolicy, 'policy_id')):
            if type(values) is not tuple or not values or any(type(value) is not kind for value in values):
                raise TypeError('native scientific protocol requires exact coordinates and prefix policies')
            require_sorted_unique_ids(values, attribute=attribute, field_name=attribute)
            for value in values:
                value.__post_init__()
        if (type(self.coordinate_policies) is not tuple
                or any(type(row) is not tuple or len(row) != 2 or any(type(pin) is not ObjectIdentity for pin in row)
                    for row in self.coordinate_policies)
                or tuple(pin.object_id for pin, _ in self.coordinate_policies)
                    != tuple(sorted(coordinate.coordinate_id for coordinate in self.coordinates))
                or {pin for pin, _ in self.coordinate_policies} != {coordinate_identity(value) for value in self.coordinates}
                or {pin for _, pin in self.coordinate_policies} != {identity(value) for value in self.prefix_policies}):
            raise ValueError('native scientific protocol omits exact coordinate/prefix coverage')
        full_rule = self.full_factor_rule
        if full_rule.scalar_closure is None:
            raise ValueError('native scientific protocol lacks the original full scalar normalization source')
        from .configured_protected_protocol import ORIGINAL_SCALAR_SOURCE_BYTES, ORIGINAL_SCALAR_SOURCE_SHA256
        original = full_rule.scalar_closure.normalization_owner
        if (original.payload_schema, original.media_type, original.sha256, original.size_bytes,
                full_rule.scalar_closure.threshold) != (
                'empirical-lawhood/source/checksummed-uninterpreted-public-bytes', 'text/x-python',
                ORIGINAL_SCALAR_SOURCE_SHA256, ORIGINAL_SCALAR_SOURCE_BYTES, self.scalar_definition.threshold):
            raise ValueError('native scientific protocol substitutes original scalar normalization source or threshold')
        for policy in self.prefix_policies:
            scalar = policy.factor_rule.scalar_closure
            if scalar is None or scalar.threshold != self.scalar_definition.threshold:
                raise ValueError('native scientific protocol changes its typed scalar normalization')
            owner = scalar.normalization_owner
            if (owner.payload_schema, owner.media_type, owner.sha256, owner.size_bytes) != (
                    self.scalar_definition.SCHEMA, 'application/json', self.scalar_definition.fingerprint(),
                    len(self.scalar_definition.canonical_bytes())):
                raise ValueError('native scientific protocol substitutes its exact typed scalar bytes')
            if owner == original:
                raise ValueError('native scientific protocol conflates original source and typed scalar normalization')
        if len({policy.factor_rule.scalar_closure.normalization_owner for policy in self.prefix_policies}) != 1:
            raise ValueError('native scientific protocol changes scalar owner across prefix policies')

    @property
    def full_factor_rule(self):
        mathematical = self.mathematical_protocol
        rules = tuple(row.target for row in mathematical.factor_rule_compatibilities
            if row.target.identity == mathematical.factor_rule)
        if not rules or any(value.canonical_bytes() != rules[0].canonical_bytes() for value in rules):
            raise ValueError('native scientific protocol lacks its exact original full factor rule')
        return rules[0]

    @property
    def scalar_artifact(self):
        return self.prefix_policies[0].factor_rule.scalar_closure.normalization_owner

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)
