# SPDX-License-Identifier: MPL-2.0
"""Disclosed UNKNOWN-contact metadata controls, never scientific acquisition.

The available causal/forecast metadata is explicitly authored software input.
The real store creates BEGIN/contact over those literal records but no native
callback, response arrays, completion or successful receipt is produced. These
controls establish neither genuine authority nor scientific qualification.
"""

from dataclasses import fields, replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as methods
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingFeatureBank, NativeTrainingOutcomeBank
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_response_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_unknown_response as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_inputs as allocation_owner
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_feature_records import ConfiguredProtectedE3CausalFeature
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_protocol import ConfiguredProtectedE3ProtocolProjection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_preparation import ConfiguredProtectedE3ResponseOperands
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_selection import ConfiguredProtectedE3ResponseSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_score_validation import validate_current_score
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_secondary_readout import _checked_pair, _observed_cell
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments, parameter_source
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import (
    ArtifactGenericValidation, ArtifactManifest, ArtifactMaterialization, ArtifactProfile,
    ArtifactWriteRequest, LogicalArtifactIdentity,
)
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkPartialOutput, NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.runtime.plans import ExecutionPlan, ExecutionTask
from tests.test_matrix_configured_protected_prefix_worker_routing import (
    configured_prefix_case as configured_prefix_case, legacy_case as legacy_case,
    original_case as original_case,
)
from tests.test_matrix_e3_protected_source_records import response_fixture
from tests.test_matrix_e3_response_records import publication, qualification
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane


def _manifest(name, schema, raw=b"disclosed software bytes"):
    logical = LogicalArtifactIdentity(name, sha256(raw).hexdigest(), schema,
        ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE,
        ArtifactGenericValidation("validator.disclosed", "1.0.0", "b" * 64,
            schema, ArtifactProfile.CANONICAL_JSON))
    physical = ArtifactMaterialization("material." + name, name, "storage.disclosed",
        "disclosed/" + name, sha256(raw).hexdigest(), len(raw), "none")
    return ArtifactManifest(logical, physical)


def _pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a" * 64)


def _blocked(*args, **kwargs):
    raise AssertionError("UNKNOWN projection entered an array/native/RNG/fit producer")


@pytest.fixture(scope="module")
def case(configured_prefix_case, legacy_case, tmp_path_factory):  # noqa: F811
    prefix, original = configured_prefix_case, legacy_case.originals
    plane = _matrix_plane(tmp_path_factory.mktemp("configured-unknown-response") / "plane")
    previous = original.projection
    projection = ConfiguredProtectedE3ProtocolProjection("projection.disclosed.unknown", prefix.specification.identity,
        prefix.specification.protocol_sha256, len(prefix.specification.protocol.canonical_bytes()),
        **{field.name: getattr(previous, field.name) for field in fields(ConfiguredProtectedE3ProtocolProjection)
           if field.name not in ("record_id", "specification", "protocol_sha256", "protocol_size_bytes")})
    old_selection, protocols, all_panels = response_fixture(original)
    protocol = next(row for row in protocols if row.public_source.root.root_id == prefix.source.root_id)
    panels = tuple(row for row in all_panels if row.independent_group_id == protocol.public_source.root.independent_group_id)
    selection = ConfiguredProtectedE3ResponseSelection("selection.disclosed.unknown", prefix.specification.identity,
        identity(prefix.manifest), old_selection.root_protocols, old_selection.group_panels,
        old_selection.template_publications, (identity(projection),))
    stub = SimpleNamespace(plane=plane)
    published = publication(stub, selection, "unknown.selection")
    numerical = records.project_protected_e3_response_numerics(protocol, provenance=selection,
        publication=published, qualification=qualification(selection, published, "unknown.selection"))
    # Separate positive SOFTWARE metadata: never relabel the actual retained
    # negative numerical/witness/frame records as scientifically satisfied.
    supports = tuple(ObjectIdentity("disclosed.positive." + name, pin.object_schema, pin.object_version, "b" * 64)
        for name, pin in (("numerical", prefix.causal.numerical), ("witness", prefix.causal.witness),
            ("frames", prefix.causal.frame_assessment)))
    arrays = replace(prefix.causal.arrays,
        members=tuple(replace(member, finite_required=True, sha256="b" * 64)
            if member.name == "frame" else member for member in prefix.causal.arrays.members),
        producers=tuple(sorted((prefix.causal.source, prefix.causal.history, supports[1], supports[2]), key=lambda pin: pin.object_id)))
    causal = replace(prefix.causal, record_id="causal.disclosed.unknown.available", numerical=supports[0],
        witness=supports[1], frame_assessment=supports[2], arrays=arrays,
        frame_sha256="b" * 64, disposition="AVAILABLE", reason=None)
    physical_config = records.ConfiguredProtectedE3PhysicalForecastConfig(
        "config." + records.NAMESPACE + "." + prefix.source.root_id + ".physical-forecast",
        prefix.source.root_id, prefix.specification.identity, records._object(protocol), identity(numerical))
    # Array members are metadata only; no literal archive is interpreted as a
    # real physical prediction or exposed as future response observations.
    members = tuple(MatrixArrayMember(name, dtype, shape, "c" * 64)
        for name, (dtype, shape) in sorted(records._physical_members(protocol, "AVAILABLE").items()))
    forecast_arrays = replace(protocol.templates, operand_id="arrays.disclosed.unknown.physical", role="FORECAST",
        members=members, producers=tuple(sorted((protocol.public_source.source, identity(causal),
            records._object(protocol), identity(numerical)), key=lambda pin: pin.object_id)))
    physical = records.ConfiguredProtectedE3PhysicalForecast("physical.disclosed.unknown", records._object(physical_config),
        protocol.public_source.source, identity(causal), records._object(protocol), identity(numerical),
        records._object(protocol.mechanical_model), causal.frame_sha256, forecast_arrays, "AVAILABLE",
        tuple((view, predictor, "AVAILABLE", None) for view in ("PRIMARY", "FINE")
            for predictor in prefix.specification.measurement.descriptions))
    allocation = allocation_owner.project_protected_e3_allocation(replace(original.inputs,
        reservation=prefix.manifest.reservation, native_specification=prefix.manifest.native_specification))
    neutral = tuple(methods.exposed.MatrixE3EstimatorModel(method.method_key,
        () if method.method_key == "RAW_TRAIN_MEDIAN" else ("literal",),
        (None,) * 15, (None,) * 15, allocation.unit_ids("train"), (0,) * 15)
        for method in prefix.specification.methods)
    models = methods.ConfiguredProtectedE3ModelSet("models.disclosed.unknown", prefix.specification.identity, allocation.identity,
        _pin("join.disclosed.unknown", ConfiguredProtectedE3PreFitJoin),
        _pin("features.disclosed.unknown", NativeTrainingFeatureBank),
        _pin("outcomes.disclosed.unknown", NativeTrainingOutcomeBank), neutral)
    frozen = methods.ConfiguredProtectedE3FrozenProducts("freeze.disclosed.unknown", prefix.specification.identity,
        allocation.identity, identity(models), models.reservation_join, None, None)
    feature = ConfiguredProtectedE3CausalFeature("feature.disclosed.unknown", prefix.config.source.allocation,
        protocol.public_source, identity(causal), causal.frame_sha256, "AVAILABLE",
        tuple((name, causal.cutoff_tick * prefix.specification.measurement.primary_timestep
            if name == "cutoff" else Decimal(0)) for name in FEATURES),
        tuple(sorted((identity(causal), *supports), key=lambda pin: pin.object_id)))
    error = methods.ConfiguredProtectedE3Forecast("forecast.disclosed.unknown", prefix.specification.identity,
        allocation.identity, identity(models), identity(frozen), feature, "calibration",
        tuple((method, (Decimal("0.25"),) * 15) for method in methods.exposed.METHODS), None, "UNCALIBRATED")
    config = records.ConfiguredProtectedE3ResponseConfig("config." + records.NAMESPACE + "." + prefix.source.root_id + ".responses",
        "responses", prefix.specification.identity, identity(prefix.manifest), prefix.config.source,
        identity(selection), records._object(protocol), identity(numerical))
    operands = ConfiguredProtectedE3ResponseOperands(config, {
        "prefix-config": prefix.config, "specification": prefix.specification, "manifest": prefix.manifest,
        "selection": selection, "protocol": protocol, "numerical-profile": numerical, "panels": panels,
        "history": prefix.history, "causal": causal, "physical-config": physical_config, "physical": physical,
        "error": error, "allocation": allocation, "models": models, "frozen": frozen,
        "calibration": None, "model-freeze": None, "mathematical-protocol": original.mathematical, "projection": projection,
    }, {}, prefix.source, (), VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
    args = operands.science_arguments()
    _, configuration, task, operation, sources, streams, outputs = records.protected_e3_response_native_contract(config,
        **{key: args[key] for key in ("source", "manifest", "specification", "selection", "protocol",
            "numerical_profile", "panels", "history", "causal", "physical", "error")})
    # The real store authenticates every native source/config/stream byte. It
    # performs only exposed metadata BEGIN/contact, never acquisition.
    source_records = (config, config.source, prefix.manifest, prefix.specification, prefix.source.coordinate,
        prefix.source.provenance, selection, protocol, numerical, *panels, prefix.history, prefix.history.checkpoint,
        causal, physical, error, *prefix.source.root.streams,
        *(stream for panel in panels if panel.role == "INDEPENDENT_FUTURE" for stream in panel.streams))
    inputs = []
    for index, record in enumerate(source_records):
        pub = plane.write(ArtifactWriteRequest("input.disclosed.unknown." + str(index), "unknown/inputs/" + str(index),
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "disclosed.unknown", "unknown/inputs",
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        inputs.append(decode_artifact_manifest(plane.root.resolve(pub.materialization.relative_path + ".manifest.json",
            for_write=False).read_bytes()))
    inputs = tuple(inputs)
    parent = replace(prefix.history.native.definition.parent_contact, task_id=task, attempt_id="attempt.disclosed.unknown.response",
        execution_plan=_pin("plan.disclosed.unknown", ExecutionPlan), execution_task=_pin(task, ExecutionTask),
        input_materialization_ids=tuple(sorted(row.materialization.materialization_id for row in inputs)))
    definition = NativeSubworkDefinition("responses." + prefix.source.root_id, operation, parent, configuration, sources,
        prefix.source.provenance.code_sources_sha256, prefix.source.provenance.dependency_lock_sha256,
        parent.input_materialization_ids, streams, outputs)
    roster = NativeSubworkRoster("selected.native-subwork", parent, (definition.identity,))
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    native = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent, parent_inputs=inputs)
    contacts.begin(parent)
    native.freeze_roster(roster, definitions=(definition,))
    entry = native.begin(definition, inputs)
    native.contact(entry)
    inspection = native.inspect(definition)
    assert inspection.state is NativeSubworkState.UNKNOWN_COMPLETION and inspection.completion is None and inspection.receipt is None
    contact_identity = ObjectIdentity.from_record(entry.contact_manifest.logical.logical_artifact_id, inspection.contact)
    availability = owner.ConfiguredProtectedE3UnknownResponseAvailability.from_inspection("availability.disclosed.unknown",
        parent_contact=parent, roster=roster, inspection=inspection, contact_identity=contact_identity)
    return SimpleNamespace(availability=availability, operands=operands, native=native, entry=entry,
        specification=prefix.specification, allocation=allocation, error=error, models=models, frozen=frozen)


@pytest.fixture(autouse=True)
def no_science(monkeypatch):
    for module, names in ((parameter_history, ("advance_parameter_pair",)),
            (parameter_history_segments, ("acquire_parameter_segment",)),
            (parameter_source, ("acquire_parameter_history",)),
            (methods, ("fit_protected_e3_models",))):
        for name in names:
            monkeypatch.setattr(module, name, _blocked)
    for name in ("Generator", "PCG64DXSM", "default_rng"):
        monkeypatch.setattr(np.random, name, _blocked)


def _score(case, **changes):
    return owner.score_unknown_response(changes.get("availability", case.availability),
        changes.get("operands", case.operands),
        score_id="score.disclosed.unknown", outcome_id="outcome.disclosed.unknown")


def test_real_begin_contact_roundtrip_remains_unknown_without_completion(case):
    record = case.availability
    assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    assert record.disposition == "UNEVALUABLE" and record.parent_contact == record.definition.parent_contact
    assert record.unknown_streams == record.definition.streams
    assert not hasattr(record, "arrays") and not hasattr(record, "native") and not hasattr(record, "qualified")
    assert not hasattr(record, "consumed_streams") and not hasattr(record, "unconsumed_streams")
    inspection = case.native.inspect(record.definition)
    assert inspection.state is NativeSubworkState.UNKNOWN_COMPLETION
    assert inspection.completion is None and inspection.receipt is None and inspection.outputs == ()


def test_pure_projection_preserves_full_grid_forecasts_and_unknown_tags(case, monkeypatch):
    from empirical_lawhood.adapters.methods import matrix_dataset_readers
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science

    monkeypatch.setattr(matrix_dataset_readers, "retained_array_mappings", _blocked)
    monkeypatch.setattr(response_science, "native_responses", _blocked)
    before = tuple(record.canonical_bytes() for record in (case.error, case.models, case.frozen))
    score, outcome = _score(case)
    assert before == tuple(record.canonical_bytes() for record in (case.error, case.models, case.frozen))
    assert len(score.cells) == 240 and len({cell.key for cell in score.cells}) == 240
    assert all(all(value is None for value in (cell.actual_odd_responses, cell.signed_errors,
        cell.absolute_errors, cell.relative_errors, cell.normalized_error)) for cell in score.cells)
    assert score.responses == case.availability.identity and score.controls == () and not score.numerical_pass
    assert score.cumulative_log_errors == (None,) * 15 and score.reason_codes == ("UNKNOWN_CONTACT",)
    assert all(view.errors == (None,) * 15 and view.dispositions == ("UNKNOWN_CONTACT",) * 15 for view in outcome.views)
    assert outcome.numerical_disposition == "UNEVALUABLE"
    args = case.operands.science_arguments()
    validate_current_score(score, case.operands.config, case.availability, source=args["source"],
        protocol=args["protocol"], panels=args["panels"], causal_identity=identity(args["causal"]),
        error_identity=identity(args["error"]), physical_identity=records._object(args["physical"]),
        response_identity=case.availability.identity)
    _checked_pair(case.specification, case.allocation, "calibration", outcome, case.error, score)
    observed = _observed_cell(16, None, score=score, feature=case.error.feature,
        tag=outcome.views[0].dispositions[0], normalized_tolerance=Decimal(1))
    assert observed.source_disposition == "UNKNOWN_CONTACT"


@pytest.mark.parametrize("damage", ("parent", "streams", "definition", "roster", "begin", "contact", "contact-pin", "partial-census"))
def test_availability_refuses_control_or_unknown_stream_substitution(case, damage):
    record = case.availability
    with pytest.raises((TypeError, ValueError)):
        if damage == "parent":
            replace(record, parent_contact=replace(record.parent_contact, attempt_id="foreign.attempt"))
        elif damage == "streams":
            replace(record, unknown_streams=record.unknown_streams[:-1])
        elif damage == "definition":
            replace(record, definition=replace(record.definition, operation_id="foreign.operation"))
        elif damage == "roster":
            replace(record, roster=replace(record.roster, subworks=(replace(record.definition.identity, object_fingerprint="f" * 64),)))
        elif damage == "begin":
            replace(record, begin=replace(record.begin, definition=replace(record.definition.identity, object_fingerprint="f" * 64)))
        elif damage == "contact":
            replace(record, contact=replace(record.contact, begin=replace(record.contact.begin, object_fingerprint="f" * 64)))
        elif damage == "contact-pin":
            replace(record, contact_identity=replace(record.contact_identity, object_fingerprint="f" * 64))
        else:
            replace(record, partial_output_records=(NativeSubworkPartialOutput(record.definition.identity,
                record.contact_identity, "arrays", 8, None, None, 1, sha256(b"x").hexdigest(), ("disclosed",)),))


@pytest.mark.parametrize("damage", ("source", "configuration", "forecast", "physical", "protocol", "model-freeze"))
def test_pure_projection_refuses_foreign_original_premises(case, damage):
    availability, operands = case.availability, case.operands
    if damage == "source":
        operands = replace(operands, source=replace(operands.source,
            reference=replace(operands.source.reference, source_id="source.foreign")))
    elif damage == "configuration":
        operands = replace(operands, config=replace(operands.config, source_manifest=replace(
            operands.config.source_manifest, object_fingerprint="f" * 64)))
    else:
        key = {"forecast": "error", "physical": "physical", "protocol": "protocol", "model-freeze": "frozen"}[damage]
        old = operands.records[key]
        if key == "error":
            changed = replace(old, frozen_products=replace(old.frozen_products, object_fingerprint="f" * 64))
        elif key == "physical":
            changed = replace(old, configuration=replace(old.configuration, object_fingerprint="f" * 64))
        elif key == "protocol":
            changed = replace(old, protocol_id="protocol.foreign")
        else:
            changed = replace(old, models=replace(old.models, object_fingerprint="f" * 64))
        operands = replace(operands, records={**operands.records, key: changed})
    with pytest.raises((TypeError, ValueError, PermissionError)):
        _score(case, availability=availability, operands=operands)


def test_real_partial_output_retained_without_becoming_response_arrays(case):
    record = case.availability
    raw = b"literal received prefix"
    partial = NativeSubworkPartialOutput(record.definition.identity, record.contact_identity, "arrays",
        len(raw) + 1, None, None, len(raw), sha256(raw).hexdigest(), ("disclosed.transport-interruption",))
    case.native.retain_partial_output(case.entry, partial, (raw,))
    observed = case.native.inspect(record.definition)
    retained = replace(record, partial_output_records=observed.partial_output_records, partial_outputs=observed.partial_outputs)
    assert retained.partial_output_records == (partial,)
    assert len(retained.partial_outputs) == 1 and retained.retained_outputs == ()
    score, outcome = _score(case, availability=retained)
    assert score.responses == retained.identity and outcome.views[0].dispositions == ("UNKNOWN_CONTACT",) * 15
    assert observed.completion is None and observed.receipt is None
    with pytest.raises(ValueError):
        replace(retained, partial_outputs=(replace(retained.partial_outputs[0],
            materialization=replace(retained.partial_outputs[0].materialization, physical_sha256="f" * 64)),))
    # A later published literal member still does not create completion. Keep
    # both observations, with neither read or promoted to a genuine response.
    raw_output, _ = encode_matrix_arrays({"literal_disclosed_member": np.zeros(1, dtype="<f8")})
    case.native.publish_output(case.entry, "arrays", (raw_output,), maximum_bytes=len(raw_output),
        maximum_chunk_bytes=len(raw_output), expected_size_bytes=len(raw_output),
        expected_physical_sha256=sha256(raw_output).hexdigest())
    observed = case.native.inspect(record.definition)
    both = replace(retained, retained_outputs=observed.outputs)
    assert len(both.retained_outputs) == len(both.partial_outputs) == 1
    score, _ = _score(case, availability=both)
    assert score.responses == both.identity and score.cumulative_log_errors == (None,) * 15
    assert observed.completion is None and observed.receipt is None
