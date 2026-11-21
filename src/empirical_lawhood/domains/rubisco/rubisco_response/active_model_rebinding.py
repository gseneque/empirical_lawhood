# SPDX-License-Identifier: MPL-2.0
"""Reuse immutable geometry when only the selected numerical engine changes."""

from dataclasses import dataclass, fields, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, validate_periodic_probe_model


@dataclass(frozen=True, slots=True)
class ActiveModelEngineRebinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-model-engine-rebinding'
    binding_id: str
    original_preparation: ObjectIdentity
    rebound_preparation: ObjectIdentity
    original_prototype: ObjectIdentity
    rebound_prototype: ObjectIdentity
    representation: ObjectIdentity
    scope: str = 'IDENTICAL_PHYSICAL_PREPARATION_NEW_ENGINE_NO_NATIVE_OR_GEOMETRY_RECONSTRUCTION'

    def __post_init__(self):
        validate_stable_id(self.binding_id)
        for name in ('original_preparation', 'rebound_preparation', 'original_prototype',
                'rebound_prototype', 'representation'):
            exact(getattr(self, name), ObjectIdentity)
        for name, kind in (('original_preparation', ActiveModelPreparation),
                ('rebound_preparation', ActiveModelPreparation),
                ('original_prototype', PeriodicProbeSelection), ('rebound_prototype', PeriodicProbeSelection)):
            pin = getattr(self, name)
            if (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('engine rebinding changes its preparation or prototype revision')
        if (self.original_preparation == self.rebound_preparation
                or self.original_prototype == self.rebound_prototype
                or self.scope != 'IDENTICAL_PHYSICAL_PREPARATION_NEW_ENGINE_NO_NATIVE_OR_GEOMETRY_RECONSTRUCTION'):
            raise ValueError('engine rebinding requires a changed engine and no physical preparation claim')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.binding_id, self)


def _validate_prototypes(original, updated, representation):
    for prototype in (original, updated):
        validate_periodic_probe_model(prototype, representation)
    physical_fields = tuple(f.name for f in fields(PeriodicProbeSelection)
        if f.name not in {'selection_id', 'engine', 'sources'})
    if any(getattr(original, name) != getattr(updated, name) for name in physical_fields):
        raise ValueError('engine rebinding changes a physical, chemical, coordinate or force-setting operand')
    if original.engine == updated.engine:
        raise ValueError('engine rebinding requires a different selected numerical engine')
    if set(original.sources)-{original.engine.identity} != set(updated.sources)-{updated.engine.identity}:
        raise ValueError('engine rebinding changes original physical source closure')


def rebind_prepared_engine(*, prepared, original_prototype, updated_prototype, representation):
    """Derive a successor from original records without regenerating any seed."""
    exact(prepared, ActiveModelPreparation)
    _validate_prototypes(original_prototype, updated_prototype, representation)
    if prepared.prototype != original_prototype.identity or prepared.representation != representation.identity:
        raise ValueError('engine rebinding substitutes the original preparation')
    digest = sha256((representation.fingerprint()+updated_prototype.fingerprint()+prepared.protocol.fingerprint()).encode()).hexdigest()
    rebound = replace(prepared, preparation_id='preparation.gp-active-states.'+digest,
        prototype=updated_prototype.identity)
    binding_digest = sha256((prepared.fingerprint()+rebound.fingerprint()).encode()).hexdigest()
    binding = ActiveModelEngineRebinding('binding.active-model-engine.'+binding_digest,
        prepared.identity, rebound.identity, original_prototype.identity, updated_prototype.identity,
        representation.identity)
    return rebound, binding


def assess_engine_rebinding(*, binding, original, rebound, original_prototype, updated_prototype, representation):
    """Independently compare every preserved operand and both complete censuses."""
    exact(binding, ActiveModelEngineRebinding)
    exact(original, ActiveModelPreparation)
    exact(rebound, ActiveModelPreparation)
    _validate_prototypes(original_prototype, updated_prototype, representation)
    if ((binding.original_preparation, binding.rebound_preparation, binding.original_prototype,
            binding.rebound_prototype, binding.representation) !=
            (original.identity, rebound.identity, original_prototype.identity, updated_prototype.identity, representation.identity)
            or original.prototype != original_prototype.identity or rebound.prototype != updated_prototype.identity
            or original.representation != representation.identity):
        raise ValueError('engine rebinding loses an exact original or successor identity')
    for field in fields(ActiveModelPreparation):
        if field.name not in {'preparation_id', 'prototype'} and getattr(original, field.name) != getattr(rebound, field.name):
            raise ValueError('engine rebinding changes an original physical preparation member')
    return dict(disposition='SATISFIED', scope=binding.scope, sites=len(rebound.sites),
        starting_hypotheses=len(rebound.seeds), preserved_assessments=len(rebound.assessments),
        new_native_calls=0, new_geometry_constructions=0, ensemble_admission='UNEVALUABLE',
        target_engine_numerical_conformance='REQUIRES_ITS_SEPARATE_EVIDENCE')
