# SPDX-License-Identifier: MPL-2.0
"""Explicit contacted-response missingness and its original score projection.

The availability record retains an UNKNOWN contact, never a completed native
response or permission to repeat it. Its constructors establish immutable joins
only. The owning API authenticates the original issued plan and native store,
pre-entry forecasts and current outcome access before this pure projection.
Neither operation here opens arrays, integrates, draws, fits or recalibrates.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseLossCell, ScheduledResponseScore,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin, NativeSubworkContact, NativeSubworkDefinition,
    NativeSubworkInspection, NativeSubworkPartialOutput, NativeSubworkRoster, NativeSubworkState,
)

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3PairedOutcome, identity
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import ConfiguredProtectedE3PrefixHistory
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_preparation import ConfiguredProtectedE3ResponseOperands
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import (
    ConfiguredProtectedE3PhysicalForecast, _error_forecast, _exact, _object,
    protected_e3_response_native_contract,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_source_records import ConfiguredProtectedE3SourceConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3ViewOutcome
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_score_validation import validate_current_score
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_secondary_readout import _checked_pair


def _pin(value, kind):
    if (type(value) is not ObjectIdentity
            or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION)):
        raise ValueError("unknown response substitutes an exact evidence contract")
    value.__post_init__()


def _manifests(values):
    if type(values) is not tuple or any(type(row) is not ArtifactManifest for row in values):
        raise TypeError("unknown response requires its immutable observed publication census")
    keys = tuple(row.logical.logical_artifact_id for row in values)
    if keys != tuple(sorted(set(keys))):
        raise ValueError("unknown response publication census repeats or reorders members")
    for row in values:
        row.__post_init__()
        row.logical.__post_init__()
        row.materialization.__post_init__()


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3UnknownResponseAvailability(CanonicalRecord):
    """A retained BEGIN/contact whose response completion is unknown.

All selected response streams remain UNKNOWN here. Their reservation is not
evidence of consumption or nonuse. Published complete members and received
prefixes are retained as distinct metadata and confer no native completion.
"""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-contacted-response-availability"
    record_id: str
    parent_contact: NativeEffectContact
    roster: NativeSubworkRoster
    definition: NativeSubworkDefinition
    begin: NativeSubworkBegin
    contact: NativeSubworkContact
    contact_identity: ObjectIdentity
    unknown_streams: tuple[ObjectIdentity, ...]
    partial_output_records: tuple[NativeSubworkPartialOutput, ...]
    partial_outputs: tuple[ArtifactManifest, ...]
    retained_outputs: tuple[ArtifactManifest, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for record, kind in ((self.parent_contact, NativeEffectContact),
                (self.roster, NativeSubworkRoster), (self.definition, NativeSubworkDefinition),
                (self.begin, NativeSubworkBegin), (self.contact, NativeSubworkContact)):
            if type(record) is not kind:
                raise TypeError("unknown response requires exact retained control records")
            record.__post_init__()
        _pin(self.contact_identity, NativeSubworkContact)
        _pin(self.contact.begin, NativeSubworkBegin)
        definition = self.definition
        if (self.roster.parent_subwork is not None
                or self.roster.subworks != (definition.identity,)
                or self.roster.roster_id != definition.roster_id
                or self.roster.parent_contact != self.parent_contact
                or definition.parent_contact != self.parent_contact
                or self.begin.definition != definition.identity
                or self.contact.begin != ObjectIdentity.from_record(self.contact.begin.object_id, self.begin)
                or self.contact_identity != ObjectIdentity.from_record(self.contact_identity.object_id, self.contact)
                or type(self.unknown_streams) is not tuple or self.unknown_streams != definition.streams):
            raise ValueError("unknown response changes its actual contact/definition/roster or unknown stream census")
        self._validate_received_metadata()

    @classmethod
    def from_inspection(cls, record_id, *, parent_contact, roster, inspection, contact_identity):
        """Retain an actual ordinary unknown inspection without a completion."""
        if (type(inspection) is not NativeSubworkInspection
                or inspection.state is not NativeSubworkState.UNKNOWN_COMPLETION
                or inspection.begin is None or inspection.contact is None
                or not inspection.has_uncertain_contact
                or inspection.completion is not None or inspection.receipt is not None):
            raise ValueError('unknown response requires an actual uncompleted native contact')
        return cls(record_id, parent_contact, roster, inspection.definition,
            inspection.begin, inspection.contact, contact_identity, inspection.definition.streams,
            inspection.partial_output_records, inspection.partial_outputs, inspection.outputs)

    def _validate_received_metadata(self):
        records = self.partial_output_records
        if type(records) is not tuple or any(type(row) is not NativeSubworkPartialOutput for row in records):
            raise TypeError("unknown response requires exact received-prefix records")
        keys = tuple(row.output_id for row in records)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("unknown response repeats or reorders partial output ports")
        _manifests(self.partial_outputs)
        _manifests(self.retained_outputs)
        if len(records) != len(self.partial_outputs):
            raise ValueError("unknown response loses a retained partial publication")
        outputs = self.definition.outputs
        # The declared original response operation has one arrays port. Native
        # contract rederivation below independently checks its exact contract.
        if len(outputs) != 1 or len(records) > 1 or len(self.retained_outputs) > 1:
            raise ValueError("unknown response changes the original one-port response census")
        output = outputs[0]
        parents = tuple(sorted((self.definition.identity, self.contact_identity), key=lambda row: row.object_id))
        for record, manifest in zip(records, self.partial_outputs, strict=True):
            record.__post_init__()
            logical, physical = manifest.logical, manifest.materialization
            if (record.definition != self.definition.identity or record.contact != self.contact_identity
                    or record.output_id != output.output_id
                    or logical.payload_schema != "empirical-lawhood/runtime/native-subwork-received-prefix"
                    or logical.profile is not ArtifactProfile.NATIVE_SUBWORK_PREFIX
                    or logical.media_type != "application/octet-stream"
                    or tuple(row.identity for row in logical.lineage_parents) != parents
                    or physical.size_bytes != record.received_size_bytes
                    or physical.physical_sha256 != record.received_physical_sha256
                    or logical.content_sha256 != record.received_physical_sha256):
                raise ValueError("unknown response changes the actual received prefix metadata")
        for manifest in self.retained_outputs:
            logical = manifest.logical
            if ((logical.payload_schema, logical.profile, logical.media_type)
                    != (output.payload_schema, output.profile, output.media_type)
                    or tuple(row.identity for row in logical.lineage_parents) != parents):
                raise ValueError("unknown response substitutes a retained declared output")
    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def disposition(self):
        """Original score facade; UNKNOWN_CONTACT remains explicit in this type."""
        return "UNEVALUABLE"

def _validated_operands(availability, operands):
    if type(availability) is not ConfiguredProtectedE3UnknownResponseAvailability:
        raise TypeError("unknown response scorer requires its distinct current availability record")
    availability.__post_init__()
    if type(operands) is not ConfiguredProtectedE3ResponseOperands:
        raise TypeError("unknown response scorer requires the existing explicit response operand carrier")
    config, values = operands.config, operands.science_arguments()
    from .configured_continued_response import require_response_retention
    retention = require_response_retention(config, values.get('retention'), source=values['source'],
        run_id=availability.parent_contact.run_id)
    _exact(values["prefix_config"], ConfiguredProtectedE3SourceConfig)
    _exact(values["history"], ConfiguredProtectedE3PrefixHistory)
    _exact(values["physical"], ConfiguredProtectedE3PhysicalForecast)
    source = values["source"]
    bound = values["history"].validate_source(values["prefix_config"], values["manifest"],
        specification=values["specification"])
    if type(source) is not ResolvedScheduledSource or bound != source:
        raise ValueError("unknown response substitutes its actual original prefix source")
    values["physical"].validate_public_inputs(values["physical_config"],
        **{key: values[key] for key in ("specification", "protocol", "numerical_profile", "causal",
            "mathematical_protocol", "projection")})
    _error_forecast(values["specification"], values["allocation"], values["models"], values["frozen"],
        values["calibration"], values["model_freeze"], values["causal"], values["physical"], values["protocol"],
        values["error"], config.source)
    _, configuration, task, operation, sources, streams, outputs = protected_e3_response_native_contract(config,
        **{key: values[key] for key in ("source", "manifest", "specification", "selection", "protocol",
            "numerical_profile", "panels", "history", "causal", "physical", "error")}, retention=retention)
    definition, parent = availability.definition, availability.parent_contact
    provenance = source.provenance if retention is None else retention.response_provenance
    run_id = values['history'].native.definition.parent_contact.run_id if retention is None else retention.continued_run_id
    if (values["causal"].disposition != "AVAILABLE" or values["physical"].disposition != "AVAILABLE"
            or definition.subwork_id != "responses." + source.root_id
            or (definition.configuration, parent.task_id, definition.operation_id, definition.sources,
                definition.streams, definition.outputs) != (configuration, task, operation, sources, streams, outputs)
            or parent.run_id != run_id
            or parent.implementation_commit != provenance.observed_git_head
            or definition.code_sources_sha256 != provenance.code_sources_sha256
            or definition.dependency_lock_sha256 != provenance.dependency_lock_sha256
            or definition.input_materialization_ids != parent.input_materialization_ids):
        raise ValueError("unknown response changes original pre-entry source/forecasts/native operation or selected streams")
    return config, values


def score_unknown_response(availability, operands, *, score_id, outcome_id):
    """Produce original typed missingness products without native/array entry.

The owning read authenticates the ordinary contact and original operands. This
unpublished assessment has no producing task, successful receipt or adjudication.
"""
    config, values = _validated_operands(availability, operands)
    source, protocol, panels = values["source"], values["protocol"], values["panels"]
    causal, physical, error = values["causal"], values["physical"], values["error"]
    matched = values['specification'].measurement.is_matched
    dense = None
    if matched:
        from .response_scoring import unobserved_dense_response_measurements
        from .matched_response_prediction import MatchedResponseViewOutcome
        cells, dense = unobserved_dense_response_measurements(protocol, panels)
        view_type, endpoint_count = MatchedResponseViewOutcome, 29
    else:
        cells = tuple(sorted((ScheduledResponseLossCell(view, panel.panel_id, action.action_id,
            predictor, horizon, None, None, None, None, None)
            for view in ("FINE", "PRIMARY") for panel in panels for action in protocol.actions
            for predictor in values["specification"].measurement.descriptions for horizon in protocol.horizon_steps),
            key=lambda row: row.key))
        view_type, endpoint_count = MatrixE3ViewOutcome, 15
    score = ScheduledResponseScore(score_id, config.source.identity, identity(causal), identity(error), _object(physical),
        availability.identity, source.root_id, protocol.public_source.root.independent_group_id,
        protocol.public_source.root.role.value, protocol.criterion, (), False, "UNEVALUABLE", cells,
        (None,) * (58 if matched else 15), ("UNKNOWN_CONTACT",), dense)
    outcome = ConfiguredProtectedE3PairedOutcome(outcome_id, error.feature, identity(error), _object(score),
        sha256(canonical_json_bytes(cells)).hexdigest(), _object(protocol), tuple(_object(panel) for panel in panels),
        tuple(view_type(view, (None,) * endpoint_count, ("UNKNOWN_CONTACT",) * endpoint_count)
            for view in ("fine", "primary")), "UNEVALUABLE")
    validate_current_score(score, config, availability, source=source, protocol=protocol, panels=panels,
        causal_identity=identity(causal), error_identity=identity(error), physical_identity=_object(physical),
        response_identity=availability.identity)
    _checked_pair(values["specification"], values["allocation"], error.role, outcome, error, score)
    return score, outcome
