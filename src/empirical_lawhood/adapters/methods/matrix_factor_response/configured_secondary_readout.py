# SPDX-License-Identifier: MPL-2.0
"""Direct secondary response mathematics and its prospective publication pin."""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult

from .response_frontier import MatrixResponseFrontierProtocol
from .response_scoring import (
    DENSE_RESPONSE_HORIZONS, RESPONSE_HEADLINE_TOLERANCE, RESPONSE_PRIMARY_TIMESTEP,
    RESPONSE_SENSITIVITY_TOLERANCES,
)

LINEAGE_SCOPE = "EXPLICIT_SELECTED_MATHEMATICAL_CONFIGURATION_FROZEN_BEFORE_CAL_CONF_NO_NATIVE_TRAIN_CONSUMPTION_PROOF"


@dataclass(frozen=True, slots=True)
class MatrixE3SecondaryTarget(CanonicalRecord):
    """Selected scientific definition; no preparation, outcome or authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/secondary-response-target"
    record_id: str
    mathematical_protocol: MatrixResponseFrontierProtocol
    normalized_adequacy_tolerance: Decimal

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.mathematical_protocol) is not MatrixResponseFrontierProtocol:
            raise TypeError("secondary target requires its exact response-task mathematical protocol")
        self.mathematical_protocol.__post_init__()
        validate_decimal(self.normalized_adequacy_tolerance, field_name="normalized_adequacy_tolerance",
            minimum=Decimal(0))
        if self.normalized_adequacy_tolerance == 0:
            raise ValueError("secondary adequacy requires an explicit positive finite tolerance")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def values(self):
        self.__post_init__()
        return self.normalized_adequacy_tolerance

    def validate_selection(self, selection):
        self.__post_init__()
        if selection.mathematical_protocol != self.mathematical_protocol:
            raise ValueError("secondary target substitutes the current response-task mathematics")


@dataclass(frozen=True, slots=True)
class MatrixE3SecondaryReadoutSelection(CanonicalRecord):
    """Blind references to the exact selected mathematics and published target."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/secondary-response-target-selection"
    record_id: str
    mathematical_protocol: ObjectIdentity
    target: ObjectIdentity
    publication: ArtifactWriteResult
    lineage_scope: str = LINEAGE_SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.mathematical_protocol, MatrixResponseFrontierProtocol),
                (self.target, MatrixE3SecondaryTarget)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError("secondary readout requires exact current scientific target references")
            value.__post_init__()
        if type(self.publication) is not ArtifactWriteResult or self.lineage_scope != LINEAGE_SCOPE:
            raise TypeError("secondary readout needs actual target publication and its declared scientific scope")
        self.publication.__post_init__()
        logical, material = self.publication.logical, self.publication.materialization
        if ((logical.payload_schema, logical.profile, logical.media_type, logical.content_sha256,
                material.physical_sha256, logical.outcome_access, logical.visibility_ceiling) !=
                (self.target.object_schema, ArtifactProfile.CANONICAL_JSON, "application/json", self.target.object_fingerprint,
                    self.target.object_fingerprint, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
                or material.size_bytes < 1):
            raise ValueError("secondary readout changes its actual complete DEV target publication")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def bind_secondary_selection(selection, target, publication):
    """Freeze a direct target while preserving the actual primary/TRAIN inputs."""
    from .configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
    if type(selection) is not ConfiguredProtectedE3PreparationSelection or type(target) is not MatrixE3SecondaryTarget:
        raise TypeError("secondary binding requires the exact current preparation and direct scientific target")
    target.validate_selection(selection)
    selected = MatrixE3SecondaryReadoutSelection(target.record_id + ".selection",
        target.mathematical_protocol.identity, target.identity, publication)
    if selection.secondary_readout is not None:
        if selection.secondary_readout != selected:
            raise ValueError("an already frozen secondary target cannot be replaced")
        return selection
    root = selection.root
    pin = selected.identity
    row = DesignInputRecord(selection.selection_id + ".secondary-response-target", pin, pin.object_fingerprint,
        selection.fit_config.fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, root.system.authority_policy.delegate_id)
    if any(value.input_id == row.input_id for value in root.design_inputs):
        raise ValueError("secondary target conflicts with an existing frozen design input")
    design = tuple(sorted((*root.design_inputs, row), key=lambda value: value.input_id))
    root = replace(root, design_inputs=design,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(value.input_id for value in design)))
    entry = replace(selection.entry_package, checklist=replace(selection.entry_package.checklist,
        draft=ObjectIdentity.from_record(root.draft_id, root)))
    return replace(selection, root=root, entry_package=entry, secondary_readout=selected)



# E4's explicit accuracy convention is a separate contract from the E3 target.
E4_OBSERVATION_HORIZONS = DENSE_RESPONSE_HORIZONS
E4_PRIMARY_TIMESTEP = RESPONSE_PRIMARY_TIMESTEP
E4_HEADLINE_TOLERANCE = RESPONSE_HEADLINE_TOLERANCE
E4_SENSITIVITY_TOLERANCES = RESPONSE_SENSITIVITY_TOLERANCES
E4_LINEAGE_SCOPE = 'EXPLICIT_E4_OBSERVATION_CONVENTION_FROZEN_BEFORE_FUTURES_NO_NATIVE_TRAIN_CONSUMPTION_PROOF'


@dataclass(frozen=True, slots=True)
class MatrixE4SecondaryTarget(CanonicalRecord):
    """Frozen sampled accuracy convention, not a selected useful horizon."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/e4-secondary-response-target'
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    mathematical_protocol: MatrixResponseFrontierProtocol
    normalized_adequacy_tolerance: Decimal
    sensitivity_tolerances: tuple[Decimal, ...]
    observation_horizons: tuple[int, ...]
    primary_timestep: Decimal

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.mathematical_protocol) is not MatrixResponseFrontierProtocol:
            raise TypeError('E4 target requires its exact original response mathematics')
        self.mathematical_protocol.__post_init__()
        if (type(self.normalized_adequacy_tolerance) is not Decimal
                or self.normalized_adequacy_tolerance != E4_HEADLINE_TOLERANCE
                or type(self.sensitivity_tolerances) is not tuple
                or any(type(value) is not Decimal for value in self.sensitivity_tolerances)
                or self.sensitivity_tolerances != E4_SENSITIVITY_TOLERANCES
                or type(self.observation_horizons) is not tuple
                or any(type(value) is not int for value in self.observation_horizons)
                or self.observation_horizons != E4_OBSERVATION_HORIZONS
                or type(self.primary_timestep) is not Decimal or self.primary_timestep != E4_PRIMARY_TIMESTEP
                or self.mathematical_protocol.horizon_steps not in ((16, 64, 128), E4_OBSERVATION_HORIZONS)
                or self.mathematical_protocol.primary_timestep != self.primary_timestep
                or any(action.pulse_steps != 16 for action in self.mathematical_protocol.action_scales)):
            raise ValueError('E4 target changes its frozen tolerance family, sampled grid, clock or original pulse')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def validate_protocol(self, protocol):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
        if type(protocol) is not ScheduledResponseProtocol:
            raise TypeError('E4 target requires the exact original bound response protocol')
        self.__post_init__()
        protocol.__post_init__()
        coordinate = protocol.public_source.coordinate
        if (protocol.criterion != self.mathematical_protocol.identity
                or protocol.horizon_steps != self.mathematical_protocol.horizon_steps
                or protocol.receiver_count != 48
                or protocol.receiver_gram_tolerance != self.mathematical_protocol.receiver_gram_tolerance
                or coordinate.primary_view.timestep != self.primary_timestep
                or coordinate.fine_view.timestep != self.primary_timestep / 2
                or protocol.public_source.policy.cutoff_tick + self.observation_horizons[-1] > coordinate.total_ticks
                or tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in protocol.actions)) !=
                    tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps)
                        for a in self.mathematical_protocol.action_scales))):
            raise ValueError('E4 target substitutes actual source clocks, complete original menu or follow-up')


@dataclass(frozen=True, slots=True)
class MatrixE4SecondaryReadoutSelection(CanonicalRecord):
    """Actual target publication selected in entry/mechanical config before futures."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/e4-secondary-response-target-selection'
    record_id: str
    mathematical_protocol: ObjectIdentity
    target: ObjectIdentity
    publication: ArtifactWriteResult
    lineage_scope: str = E4_LINEAGE_SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.mathematical_protocol, MatrixResponseFrontierProtocol),
                (self.target, MatrixE4SecondaryTarget)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError('E4 secondary selection changes its exact scientific references')
            value.__post_init__()
        if type(self.publication) is not ArtifactWriteResult or self.lineage_scope != E4_LINEAGE_SCOPE:
            raise TypeError('E4 secondary selection needs its actual frozen target publication')
        self.publication.__post_init__()
        logical, material = self.publication.logical, self.publication.materialization
        if ((logical.payload_schema, logical.profile, logical.media_type, logical.content_sha256,
                material.physical_sha256, logical.outcome_access, logical.visibility_ceiling) !=
                (self.target.object_schema, ArtifactProfile.CANONICAL_JSON, 'application/json', self.target.object_fingerprint,
                    self.target.object_fingerprint, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
                or material.size_bytes < 1 or logical.lineage_parents):
            raise ValueError('E4 selection changes its actual target publication bytes or custody')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def validate_target(self, target):
        if type(target) is not MatrixE4SecondaryTarget:
            raise TypeError('E4 selection requires its exact target body')
        self.__post_init__()
        target.__post_init__()
        if (self.target != target.identity or self.mathematical_protocol != target.mathematical_protocol.identity
                or self.publication.materialization.size_bytes != len(target.canonical_bytes())):
            raise ValueError('E4 selection substitutes its actual complete published target')
