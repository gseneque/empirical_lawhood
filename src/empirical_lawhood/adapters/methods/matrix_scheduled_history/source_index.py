# SPDX-License-Identifier: MPL-2.0
"""Operation-local resolution of bounded current scheduled source identities.

The index owns no publication, access or execution authority. Boundary owners
authenticate their shared operands before constructing a fresh index. Nothing
here serializes a resolved population or reconstructs an earlier source record.
"""
from __future__ import annotations
from empirical_lawhood.kernel.decoding import validate_record_fields

from dataclasses import dataclass, field
from math import prod
from types import MappingProxyType
from typing import Mapping

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity, expected_members
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import require_sorted_unique_strings

from .records import (
    CANDIDATE, NAMESPACE, ScheduledConfig, ScheduledPrefixPolicy, ScheduledReservation,
    ScheduledRoot, ScheduledSource, ScheduledSpecification, identity,
)


@dataclass(frozen=True, slots=True, eq=False)
class ScheduledSourceIndex:
    reservation: ScheduledReservation
    specification: ScheduledSpecification
    provenances: tuple[NumericalProducingProvenance, ...]
    allocation_identity: ObjectIdentity = field(init=False)
    reservation_identity: ObjectIdentity = field(init=False)
    specification_identity: ObjectIdentity = field(init=False)
    selection_identity: ObjectIdentity = field(init=False)
    root_ids: tuple[str, ...] = field(init=False)
    _roots: Mapping[str, ScheduledRoot] = field(init=False, repr=False)
    _root_positions: Mapping[str, int] = field(init=False, repr=False)
    _coordinates: Mapping[ObjectIdentity, MatrixParameterCoordinate] = field(init=False, repr=False)
    _policies: Mapping[ObjectIdentity, ScheduledPrefixPolicy] = field(init=False, repr=False)
    _provenances: Mapping[ObjectIdentity, NumericalProducingProvenance] = field(init=False, repr=False)
    _bounded_coordinates: Mapping[ObjectIdentity, bool] = field(init=False, repr=False)

    def __post_init__(self):
        if (type(self.reservation) is not ScheduledReservation
                or type(self.specification) is not ScheduledSpecification
                or type(self.provenances) is not tuple or not self.provenances
                or any(type(value) is not NumericalProducingProvenance for value in self.provenances)):
            raise TypeError('scheduled source index requires exact shared scientific parents')
        allocation, selection = self.reservation.allocation, self.specification.selection
        validate_record_fields(allocation)
        validate_record_fields(self.reservation)
        validate_record_fields(selection)
        validate_record_fields(self.specification)
        for provenance in self.provenances:
            validate_record_fields(provenance)
        provenance_ids = tuple(value.identity for value in self.provenances)
        digests = tuple(value.object_fingerprint for value in provenance_ids)
        if digests != tuple(sorted(set(digests))):
            raise ValueError('scheduled source index duplicates or reorders producing provenance')
        allocation_id, reservation_id = identity(allocation), identity(self.reservation)
        specification_id, selection_id = identity(self.specification), identity(selection)
        if selection.reservation != reservation_id:
            raise ValueError('scheduled source index changes the actual frozen reservation')
        coordinates = {coordinate_identity(value): value for value in allocation.coordinates}
        selected_policies = dict(selection.coordinate_policies)
        policies = {identity(value): value for value in selection.prefix_policies}
        if set(selected_policies) != set(coordinates):
            raise ValueError('scheduled source index omits exact coordinate/policy coverage')
        for coordinate_id, coordinate in coordinates.items():
            policy = policies[selected_policies[coordinate_id]]
            if (not policy.cutoff_tick < coordinate.total_ticks
                    or policy.factor_rule.primary_dt != coordinate.primary_view.timestep
                    or policy.factor_rule.lattice != tuple(t for t in coordinate.observation_ticks
                        if t <= policy.cutoff_tick)):
                raise ValueError('scheduled prefix changes original causal observation/paired clock boundary')
        for scope in allocation.matched_scopes:
            if len({selected_policies[value] for value in scope.coordinates}) != 1:
                raise ValueError('matched scheduled coordinates change frozen cutoff/admission/sector/numerical policy')
        roots = {value.root.root_id: value for value in allocation.roots}
        bounded = {}
        for coordinate_id, coordinate in coordinates.items():
            size = sum(prod(shape) * {'<c16': 16, '<f8': 8, '<i8': 8}[dtype]
                for dtype, shape in expected_members(coordinate).values())
            bounded[coordinate_id] = size + 11 * 10000 <= MAXIMUM_MATRIX_ARRAY_BYTES
        for name, value in (
                ('allocation_identity', allocation_id), ('reservation_identity', reservation_id),
                ('specification_identity', specification_id), ('selection_identity', selection_id),
                ('root_ids', tuple(roots)), ('_roots', MappingProxyType(roots)),
                ('_root_positions', MappingProxyType({root: position for position, root in enumerate(roots)})),
                ('_coordinates', MappingProxyType(coordinates)),
                ('_policies', MappingProxyType({key: policies[value] for key, value in selected_policies.items()})),
                ('_provenances', MappingProxyType(dict(zip(provenance_ids, self.provenances, strict=True)))),
                ('_bounded_coordinates', MappingProxyType(bounded))):
            object.__setattr__(self, name, value)

    @classmethod
    def from_shared(cls, *, reservation, specification, provenances):
        return cls(reservation, specification, provenances)

    def reference(self, *, source_id, root_id, provenance):
        if root_id not in self._roots or provenance not in self._provenances:
            raise ValueError('scheduled source selects an undeclared root or producing provenance')
        reference = ScheduledSource(source_id, self._roots[root_id], self.allocation_identity,
            self.reservation_identity, self.specification_identity, self.selection_identity, provenance)
        self.require_reference(reference)
        return reference

    def require_reference(self, reference):
        if type(reference) is not ScheduledSource:
            raise TypeError('scheduled source resolution requires the current bounded reference')
        validate_record_fields(reference)
        if ((reference.allocation, reference.reservation, reference.specification, reference.selection) !=
                (self.allocation_identity, self.reservation_identity, self.specification_identity, self.selection_identity)
                or reference.root_id not in self._roots or reference.root != self._roots[reference.root_id]
                or reference.provenance not in self._provenances):
            raise ValueError('scheduled source substitutes its exact root/streams or shared scientific parents')
        if not self._bounded_coordinates[reference.coordinate]:
            raise ValueError('selected complete scheduled source needs an explicit bounded chunked successor')

    def resolve(self, reference):
        self.require_reference(reference)
        return ResolvedScheduledSource(reference, self)

    def require_roster(self, references, *, expected_root_ids):
        require_sorted_unique_strings(expected_root_ids, field_name='expected scheduled root census', allow_empty=False)
        if (type(references) is not tuple or not references
                or any(type(value) is not ScheduledSource for value in references)
                or tuple(value.root_id for value in references) != expected_root_ids
                or not set(expected_root_ids) <= set(self.root_ids)):
            raise ValueError('scheduled source roster drops, repeats or changes assigned roots')
        for reference in references:
            self.require_reference(reference)

    def require_shared_source(self, reference, shared):
        """Join one local reference to an already validated complete shared bank."""
        self.require_reference(reference)
        self.require_parents(reservation=shared.reservation, specification=shared.specification,
            provenances=shared.provenances)
        if (len(shared.sources) != len(self.root_ids)
                or shared.sources[self._root_positions[reference.root_id]] != reference):
            raise ValueError('scheduled native context substitutes its exact shared source roster')

    def require_parents(self, *, reservation, specification, provenances):
        if ((identity(reservation), identity(specification)) !=
                (self.reservation_identity, self.specification_identity)
                or tuple(value.identity for value in provenances) != tuple(self._provenances)):
            raise ValueError('scheduled source index substitutes its actual shared scientific parents')


@dataclass(frozen=True, slots=True, eq=False)
class ResolvedScheduledSource:
    """Explicit scientific view; the bounded reference is its sole identity."""
    reference: ScheduledSource
    index: ScheduledSourceIndex

    def __post_init__(self):
        if type(self.index) is not ScheduledSourceIndex:
            raise TypeError('resolved scheduled source requires its operation-local shared index')
        self.index.require_reference(self.reference)

    def __eq__(self, other):
        return type(other) is ResolvedScheduledSource and self.reference == other.reference

    def __hash__(self):
        return hash(self.reference)

    @property
    def identity(self): return self.reference.identity
    @property
    def source_id(self): return self.reference.source_id
    @property
    def root_id(self): return self.reference.root_id
    @property
    def root(self): return self.reference.root
    @property
    def allocation(self): return self.index.reservation.allocation
    @property
    def reservation(self): return self.index.reservation
    @property
    def specification(self): return self.index.specification
    @property
    def selection(self): return self.index.specification.selection
    @property
    def coordinate(self): return self.index._coordinates[self.reference.coordinate]
    @property
    def policy(self): return self.index._policies[self.reference.coordinate]
    @property
    def provenance(self): return self.index._provenances[self.reference.provenance]
    @property
    def numerical_design(self): return self.selection.numerical_design
    @property
    def evidence_role(self):
        return ('EXPOSED_DEVELOPMENT_NONPROMOTABLE'
            if self.root.root.role is MatrixProgrammeRole.DEVELOPMENT else CANDIDATE)


@dataclass(frozen=True, slots=True)
class ScheduledNativeSourceContext:
    """Actual current native configuration and shared operands, without authority."""
    source: ResolvedScheduledSource
    configuration: object
    shared: object

    def __post_init__(self):
        from .commitment import ScheduledCommitmentConfig
        from .compact_records import ScheduledCompactBank, ScheduledCompactConfig, ScheduledCompactResponseConfig
        from .response_selection import ScheduledResponseConfig
        if type(self.source) is not ResolvedScheduledSource:
            raise TypeError('scheduled native context needs its explicit resolved scientific source')
        if type(self.shared) is ScheduledCommitmentConfig:
            if type(self.configuration) not in (ScheduledConfig, ScheduledResponseConfig):
                raise TypeError('scheduled native context changes its actual generic configuration owner')
        elif type(self.shared) is ScheduledCompactBank:
            if type(self.configuration) not in (ScheduledCompactConfig, ScheduledCompactResponseConfig):
                raise TypeError('scheduled native context changes its actual compact configuration owner')
        else:
            raise TypeError('scheduled native context requires an actual shared current parent')
        self.source.index.require_shared_source(self.source.reference, self.shared)
        expected = self._configuration(self.configuration.operation)
        if self.configuration != expected:
            raise ValueError('scheduled native context substitutes actual configuration/shared operands')

    def _configuration(self, phase):
        from .commitment import ScheduledCommitmentConfig
        from .compact_records import NAMESPACE as COMPACT_NAMESPACE
        from .compact_records import ScheduledCompactConfig, ScheduledCompactResponseConfig, compact_identity
        from .response_selection import ScheduledResponseConfig
        source = self.source.reference
        if type(self.shared) is ScheduledCommitmentConfig:
            pin = identity(self.shared)
            config_id = 'config.' + NAMESPACE + '.' + source.root_id + '.' + phase
            if phase.startswith(('responses', 'response-score')):
                selection = self.shared.response_selection
                if selection is None:
                    raise ValueError('scheduled native context omits actual complete response selection')
                return ScheduledResponseConfig(config_id, phase, source, selection.identity, pin)
            return ScheduledConfig(config_id, phase, source, pin)
        pin = compact_identity(self.shared)
        config_id = 'config.' + COMPACT_NAMESPACE + '.' + source.root_id + '.' + phase
        if phase.startswith(('responses', 'response-score')):
            selection = self.shared.response_selection
            if selection is None:
                raise ValueError('scheduled native context omits actual complete response selection')
            return ScheduledCompactResponseConfig(config_id, phase, source, selection.identity, pin)
        return ScheduledCompactConfig(config_id, phase, source, pin)

    def contract(self, phase):
        from .commitment import ScheduledCommitmentConfig
        from .compact_records import compact_native_contract
        suffix = '-development' if self.source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else ''
        if phase not in ('prefix', 'continue' + suffix, 'responses' + suffix):
            raise ValueError('scheduled native context changes its declared native phase or access lane')
        if type(self.shared) is not ScheduledCommitmentConfig:
            return compact_native_contract(self.source, phase, bank=self.shared)
        config = self._configuration(phase)
        operation = NAMESPACE + {
            'prefix': '.prefix-before-continuation.v1',
            'continue': '.exact-checkpoint-continuation.v1',
            'continue-development': '.exact-checkpoint-continuation.v1',
            'responses': '.scheduled-paired-pulse-responses.v1',
            'responses-development': '.scheduled-paired-pulse-responses.v1',
        }[phase]
        reference = self.source.reference
        operands = (reference.identity, identity(self.shared), reference.allocation,
            reference.selection, reference.coordinate, reference.provenance)
        return identity(config), NAMESPACE + '.' + reference.root_id + '.' + phase, operation, tuple(
            sorted(operands, key=lambda value: value.object_id))
