# SPDX-License-Identifier: MPL-2.0
"""Literal disclosed prefix metadata; no native operation or qualification."""

from dataclasses import fields, replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_records as p
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_source_records as source_owner
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import (
    ScheduledCompactBank, ScheduledCompactConfig, compact_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledNativeSourceContext, ScheduledSourceIndex
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkOutput
from tests.test_matrix_e3_prefix_science_extraction import (
    blocked, literal_segment,
    provenance as provenance, scheduled as scheduled, stock as stock,
)
from tests.test_matrix_e3_protected_source_records import fixture as source_fixture
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_scheduled_history_bindings import bank as compact_bank  # noqa: F401
from tests.native_completion_fixtures import publish_completion
from tests.test_matrix_scheduled_history import pure_assess_prefix, pure_measure_prefix, pure_check_frames, pure_causal_delivery


def native_change(history, *, definition=None, receipt=None, completion=None):
    definition = definition or history.native.definition
    completion = completion or replace(history.native.completion, definition=definition.identity)
    return replace(history, native=r.ScheduledNativeEvidence(definition, completion, receipt or history.native.receipt))


def native_adversaries(history):
    definition, receipt = history.native.definition, history.native.receipt
    foreign = ObjectIdentity("literal.foreign.source", r.ScheduledSource.SCHEMA, r.ScheduledSource.VERSION, "e" * 64)
    changes = (
        ("configuration", dict(configuration=replace(definition.configuration, object_fingerprint="e" * 64))),
        ("operation", dict(operation_id="literal.foreign.operation")),
        ("subwork", dict(subwork_id="prefix.literal.foreign")),
        ("parent-task", dict(parent_contact=replace(definition.parent_contact, task_id="literal.foreign.task", execution_task=replace(definition.parent_contact.execution_task, object_id="literal.foreign.task")))),
        ("source-closure", dict(sources=tuple(sorted((*definition.sources, foreign), key=lambda row: row.object_id)))),
        ("code", dict(code_sources_sha256="e" * 64)),
        ("lock", dict(dependency_lock_sha256="e" * 64)),
        ("output-media", dict(outputs=(replace(definition.outputs[0], media_type="application/octet-stream"), definition.outputs[1]))),
    )
    result = [(name, lambda change=change: native_change(history, definition=replace(definition, **change))) for name, change in changes]
    result += [
        ("receipt-attempt", lambda: native_change(history, receipt=replace(receipt, attempt_id="literal.foreign.attempt"))),
        ("receipt-run", lambda: native_change(history, receipt=replace(receipt, run_id="literal.foreign.run"))),
        ("receipt-task", lambda: native_change(history, receipt=replace(receipt, task_id="literal.foreign.task"))),
        ("physical-bytes", lambda: native_change(history, receipt=replace(receipt, output_materializations=(
            replace(receipt.output_materializations[0], physical_sha256="e" * 64), *receipt.output_materializations[1:])))),
        ("logical-bytes", lambda: native_change(history, receipt=replace(receipt, output_logical_artifacts=(
            replace(receipt.output_logical_artifacts[0], content_sha256="e" * 64), *receipt.output_logical_artifacts[1:])))),
        ("checkpoint-cursor", lambda: replace(history, checkpoint=replace(history.checkpoint, generators=(
            replace(history.checkpoint.generators[0], completed_noise_matrices=999), *history.checkpoint.generators[1:])))),
        ("checkpoint-seed", lambda: replace(history, checkpoint=replace(history.checkpoint, generators=(
            replace(history.checkpoint.generators[0], effective_seed=history.checkpoint.generators[0].effective_seed+1), *history.checkpoint.generators[1:])))),
    ]
    return tuple(result)


def old_refusals(case):
    results = []
    for name, altered in native_adversaries(case.history):
        try:
            altered().validate_source(case.source, native_context=case.native_context)
        except (TypeError, ValueError) as error:
            results.append((name, type(error).__name__, str(error)))
        else:
            raise AssertionError(name + " accepted")
    return tuple(results)


def test_current_generic_native_canonical_and_exact_guards(compact_bank):  # noqa: F811
    case = current_native_case(compact_bank, compact=False)
    case.history.validate_source(case.source, native_context=case.native_context)
    assert decode_canonical_bytes(case.history.canonical_bytes(), r.ScheduledPrefixHistory, maximum_bytes=None) == case.history
    assert len(old_refusals(case)) == 15


def literal_history(plane, source, *, configuration, task, operation, sources):
    """Disclosed complete metadata only; never a native contact or worker."""
    parent = NativeEffectContact("run.literal.current-prefix", task, "attempt." + task,
        ObjectIdentity("plan.literal.current-prefix", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a"*64),
        ObjectIdentity(task, "empirical-lawhood/runtime/execution-task", "1.0.0", "b"*64), source.provenance.observed_git_head,
        ("input.literal.current-prefix",), ())
    streams = tuple(sorted((source.root.stream_identity(row) for row in source.root.streams), key=lambda row: row.object_id))
    definition = NativeSubworkDefinition("prefix." + source.root_id, operation, parent, configuration, tuple(sorted(sources, key=lambda row: row.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, parent.input_materialization_ids, streams,
        (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
         NativeSubworkOutput("checkpoint", r.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")))
    native_task = "native-subwork." + sha256((task + ":" + definition.subwork_id).encode()).hexdigest()
    raw, arrays, checkpoint = science.prefix_from_segment(source, literal_segment(source), artifact_id=native_task + ".output.arrays")
    array_publication = plane.write(ArtifactWriteRequest(arrays.array_artifact.artifact_id, "software/" + native_task + ".npz",
        MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "exposed-literal-metadata", "software", raw,
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    checkpoint_publication = publish(plane, checkpoint, native_task + ".output.checkpoint")
    receipt = CanonicalTaskReceipt("receipt." + native_task, parent.run_id, native_task, parent.run_id + "." + native_task + ".attempt-001",
        parent.implementation_commit, parent.input_materialization_ids,
        (array_publication.materialization, checkpoint_publication.materialization),
        (array_publication.logical, checkpoint_publication.logical), (), OperationalStatus.SUCCEEDED, ())
    contact = NativeSubworkContact(ObjectIdentity("begin.literal.current-prefix", "empirical-lawhood/runtime/native-subwork-begin", "1.0.0", "c"*64))
    consumed = tuple(sorted((source.root.stream_identity(row) for row in source.root.streams
        if row.purpose.startswith("preparation") or source.policy.cutoff_tick > source.coordinate.ramp_ticks), key=lambda row: row.object_id))
    completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record("contact.literal.current-prefix", contact),
        OperationalStatus.SUCCEEDED, ("arrays", "checkpoint"), (), consumed,
        tuple(row for row in streams if row not in consumed), (), InquiryCost(None, None, None),
        "exposed literal metadata; no native operation or qualification", None, ())
    receipt = publish_completion(plane, receipt, completion, visibility=VisibilityCeiling.PROSPECTIVE,
        access=OutcomeAccess.OUTCOME_BLIND)
    return raw, arrays, checkpoint, r.ScheduledNativeEvidence(definition, completion, receipt)


def current_native_case(bank_fixture, *, compact):
    plane, original_sources, commitment = bank_fixture[:3]
    source = next(row for row in original_sources if row.root.root.role.value == "CALIBRATION")
    if compact:
        shared = ScheduledCompactBank.from_commitment(commitment)
        configuration = ScheduledCompactConfig("config.matrix-scheduled-history-compact."+source.root_id+".prefix",
            "prefix", source.reference, compact_identity(shared))
    else:
        shared = commitment
        configuration = r.ScheduledConfig("config."+r.NAMESPACE+"."+source.root_id+".prefix",
            "prefix", source.reference, r.identity(shared))
    native_context = ScheduledNativeSourceContext(source, configuration, shared)
    configuration_pin, task, operation, sources = native_context.contract("prefix")
    raw, arrays, checkpoint, native = literal_history(plane, source, configuration=configuration_pin,
        task=task, operation=operation, sources=sources)
    history = r.ScheduledPrefixHistory("history.literal.current-native", r.identity(source), arrays, checkpoint, native)
    assert source in original_sources
    return SimpleNamespace(source=source, history=history, native_raw=raw, native_context=native_context)


def test_current_compact_native_contract_and_refusals_remain_exact(compact_bank):  # noqa: F811
    case = current_native_case(compact_bank, compact=True)
    case.history.validate_source(case.source, native_context=case.native_context)
    assert case.history.native.definition.configuration.object_version == ScheduledCompactConfig.VERSION
    assert len(case.history.native.definition.sources) == 6
    assert len(old_refusals(case)) == 15


def current_case(scheduled, monkeypatch):
    """Small disclosed source and real typed metadata, with literal arrays."""
    originals = source_fixture(scheduled)
    plane, manifest, specification = originals.plane, originals.manifest, originals.inputs.specification
    source = next(row for row in originals.sources if row.root.root.role.value == "CALIBRATION")
    descriptor = next(row for row in originals.descriptors if row.identity == r.identity(source))
    config = source_owner.ProtectedE3SourceConfig("config." + source_owner.source_task_id(source.root_id, source_owner.ProtectedE3SourcePhase.PREFIX),
        source_owner.ProtectedE3SourcePhase.PREFIX, specification.identity, source_owner.identity(manifest), descriptor)
    monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
    bound, configuration, task, operation, closure, _ = p.protected_prefix_native_contract(
        config, manifest, specification=specification)
    assert bound == source
    native_raw, arrays, checkpoint, native = literal_history(plane, source,
        configuration=configuration, task=task, operation=operation, sources=closure)
    # Literal generic metadata supplies independent value reducers only. Its
    # native envelope is the disclosed current protected call, never a claim
    # that a generic forecast bank or native configuration was authored.
    history = r.ScheduledPrefixHistory("history.literal.numerical-comparison", r.identity(source), arrays, checkpoint, native)
    native_values = science.consume_prefix(source, arrays, native_raw)
    numerical = pure_assess_prefix(source, history, native_values)
    diagnostic_raw, witness = pure_measure_prefix(source, history, numerical, native_values, artifact_id="diagnostics.literal.original")
    frames = pure_check_frames(source, history, numerical, witness, native_raw, diagnostic_raw)
    causal_raw, causal = pure_causal_delivery(source, history, numerical, witness, frames, native_raw, diagnostic_raw, artifact_id="causal.literal.original")
    current_history = p.ProtectedE3PrefixHistory("prefix.literal.current", r.identity(source), configuration, arrays, checkpoint, native)
    current_numerical = p.ProtectedE3NumericalAssessment("numerical.literal.current", r.identity(source), p.identity(current_history),
        numerical.numerical_design, numerical.controls, numerical.numerical_pass)
    current_witness = p.ProtectedE3PrefixWitness("witness.literal.current", r.identity(source), p.identity(current_history), p.identity(current_numerical),
        witness.policy, witness.traces, replace(witness.arrays, producers=tuple(sorted((r.identity(source), p.identity(current_history), p.identity(current_numerical)), key=lambda row: row.object_id))))
    current_frames = p.ProtectedE3FrameAssessment("frames.literal.current", r.identity(source), p.identity(current_witness), frames.numerical_design,
        frames.controls, frames.numerical_pass)
    current_causal = p.ProtectedE3CausalPrefix("causal.literal.current", r.identity(source), p.identity(current_history), p.identity(current_numerical),
        p.identity(current_witness), p.identity(current_frames), causal.policy, source.root.root, causal.cutoff_tick, causal.frame_sha256,
        causal.disposition, causal.reason, replace(causal.arrays, producers=tuple(sorted((r.identity(source), p.identity(current_history),
            p.identity(current_witness), p.identity(current_frames)), key=lambda row: row.object_id))))
    return SimpleNamespace(plane=plane, originals=originals, source=source, manifest=manifest, config=config, specification=specification, history=current_history,
        numerical=current_numerical, witness=current_witness, frames=current_frames, causal=current_causal, old_history=history,
        native_raw=native_raw, diagnostic_raw=diagnostic_raw, causal_raw=causal_raw,
        old_numerical=numerical, old_witness=witness, old_frames=frames, old_causal=causal)


@pytest.fixture
def current(scheduled, monkeypatch):
    return current_case(scheduled, monkeypatch)


def test_current_prefix_has_actual_config_and_exact_five_source_closure(current):
    case = current
    assert case.history.validate_source(case.config, case.manifest, specification=case.specification) == case.source
    source, configuration, task, operation, references, outputs = p.protected_prefix_native_contract(case.config, case.manifest, specification=case.specification)
    assert set(references) == {compact_identity(case.config.source), p.identity(case.manifest), case.specification.identity, coordinate_identity(source.coordinate), source.provenance.identity}
    assert len(references) == 5 and configuration == p.identity(case.config)
    assert references.count(r.identity(source)) == 1 and r.identity(source.allocation) not in references
    assert source.policy.cutoff_tick == case.specification.measurement.origin_tick == 256
    assert task == "matrix-e3-protected." + source.root_id + ".prefix"
    assert operation == "matrix-e3-protected.prefix-before-continuation.v1"
    assert tuple(output.output_id for output in outputs) == ("arrays", "checkpoint")
    assert case.history.native.definition.configuration.object_schema == source_owner.ProtectedE3SourceConfig.SCHEMA
    assert case.old_history.canonical_bytes() != case.history.canonical_bytes()


def test_all_current_products_roundtrip_and_validate_complete_metadata(current):
    c = current
    c.numerical.validate_source(c.source, c.history)
    c.witness.validate_source(c.source, c.history, c.numerical)
    c.frames.validate_source(c.source, c.witness)
    c.causal.validate_source(c.source, c.history, c.numerical, c.witness, c.frames)
    for record in (c.history, c.numerical, c.witness, c.frames, c.causal):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    assert c.causal.disposition == "UNEVALUABLE" and c.causal.reason == "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED"
    assert tuple(control.denominator_real_coordinates for control in c.numerical.controls) == (192, 192, 192, 96)
    assert tuple(len(control.measured_errors) for control in c.frames.controls) == (68, 1020, 68, 68, 68, 68)
    assert not any(member.name.endswith("innovations") for member in c.causal.arrays.members)
    assert "generators" not in c.causal.to_document()["value"] and "checkpoint" not in c.causal.to_document()["value"]


def test_current_native_adversaries_keep_exact_receipt_and_original_stream_contract(current):
    for _, altered in native_adversaries(current.history):
        with pytest.raises((ValueError, TypeError)):
            altered().validate_source(current.config, current.manifest, specification=current.specification)
    completion = current.history.native.completion
    with pytest.raises(ValueError, match="native phase|exact completion"):
        native_change(current.history, completion=replace(completion, consumed_streams=completion.consumed_streams[:-1],
            unconsumed_streams=tuple(sorted((*completion.unconsumed_streams, completion.consumed_streams[-1]), key=lambda row: row.object_id)))).validate_source(current.config, current.manifest, specification=current.specification)


def test_current_native_records_require_exact_inner_types(current):
    for name in ("definition", "completion", "receipt"):
        original = getattr(current.history.native, name)
        foreign = type("Foreign" + type(original).__name__, (type(original),), {})
        changed = foreign(**{field.name: getattr(original, field.name) for field in fields(original)})
        with pytest.raises(TypeError, match="exact original or current record types|exact completion and receipt types"):
            native_change(current.history, **{name: changed})


def test_actual_ordinary_array_alias_preserves_strict_native_byte_custody(current):
    c = current
    logical_id = "ordinary." + c.history.native.definition.parent_contact.task_id + ".arrays"
    publication = c.plane.write(ArtifactWriteRequest(logical_id, "software/ordinary-prefix-arrays.npz", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "exposed-literal-ordinary-relay", "software", c.native_raw,
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    actual_port = ArtifactIdentity(publication.logical.logical_artifact_id, "disclosed-ordinary-publication", MATRIX_ARRAY_SCHEMA,
        publication.materialization.physical_sha256, publication.logical.media_type, publication.materialization.size_bytes)
    aliased = replace(c.history, arrays=replace(c.history.arrays, array_artifact=actual_port))
    assert aliased.arrays.array_artifact == actual_port
    assert aliased.checkpoint == c.history.checkpoint and aliased.native == c.history.native
    assert aliased.arrays.array_artifact.artifact_id != aliased.checkpoint.prefix_arrays.artifact_id
    assert aliased.validate_source(c.config, c.manifest, specification=c.specification) == c.source
    with pytest.raises(ValueError, match="scheduled checkpoint substitutes"):
        replace(aliased, arrays=replace(aliased.arrays, array_artifact=replace(actual_port, sha256="e"*64))).validate_source(
            c.config, c.manifest, specification=c.specification)
    with pytest.raises(ValueError, match="physical native arrays/checkpoint custody"):
        replace(aliased, checkpoint=replace(aliased.checkpoint, prefix_arrays=replace(aliased.checkpoint.prefix_arrays,
            artifact_id=logical_id))).validate_source(c.config, c.manifest, specification=c.specification)


def test_selected_contract_refuses_changed_cutoff_and_reserved_transfer(current):
    c = current
    policy = replace(c.source.policy, cutoff_tick=512, factor_rule=replace(c.source.policy.factor_rule, lattice=tuple(range(0, 513, 16))))
    selection = replace(c.source.specification.selection, prefix_policies=(policy,),
        coordinate_policies=tuple((coordinate, r.identity(policy)) for coordinate, _ in c.source.specification.selection.coordinate_policies))
    native_spec = replace(c.source.specification, selection=selection, publication=publish(c.plane, selection, "literal.rejected.changed-cutoff-selection"))
    manifest = replace(c.manifest, native_specification=native_spec)
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation, specification=native_spec,
        provenances=manifest.provenances)
    source = index.resolve(index.reference(source_id=c.source.source_id, root_id=c.source.root_id,
        provenance=c.source.provenance.identity))
    config = replace(c.config, source=source.reference, source_manifest=p.identity(manifest))
    with pytest.raises(ValueError, match="selected original causal cutoff"):
        p.protected_prefix_native_contract(config, manifest, specification=c.specification)
    transfer = next(row for row in c.originals.descriptors if row.root.root.role.value == "WITHHELD_TRANSFER")
    with pytest.raises(ValueError, match="root/phase"):
        replace(c.config, source=transfer, record_id="config." + source_owner.source_task_id(transfer.root_id, source_owner.ProtectedE3SourcePhase.PREFIX))
    other = next(row for row in c.originals.descriptors if row.root.root.role.value == "CONFIRMATION")
    config = replace(c.config, source=other, record_id="config." + source_owner.source_task_id(other.root_id, source_owner.ProtectedE3SourcePhase.PREFIX))
    with pytest.raises(ValueError):
        c.history.validate_source(config, c.manifest, specification=c.specification)


@pytest.mark.parametrize("damage", ("phase", "config", "specification", "manifest", "historical-type", "ducktype"))
def test_current_prefix_cannot_substitute_typed_current_binding(current, damage):
    c = current
    args = dict(config=c.config, manifest=c.manifest, specification=c.specification)
    if damage == "phase":
        args["config"] = replace(c.config, phase=source_owner.ProtectedE3SourcePhase.PROJECT,
            record_id="config." + source_owner.source_task_id(c.source.root_id, source_owner.ProtectedE3SourcePhase.PROJECT))
    elif damage == "config":
        args["config"] = replace(c.config, source=replace(c.config.source, selection=replace(c.config.source.selection, object_fingerprint="a"*64)))
    elif damage == "specification":
        args["specification"] = replace(c.specification, specification_id="specification.literal.foreign")
    elif damage == "manifest":
        args["manifest"] = replace(c.manifest, record_id="manifest.literal.foreign")
    elif damage == "historical-type":
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledCommitmentConfig
        args["config"] = r.ScheduledConfig("config." + r.NAMESPACE + "." + c.source.root_id + ".prefix", "prefix", c.source.reference,
            ObjectIdentity("commitment.literal.historical", ScheduledCommitmentConfig.SCHEMA, ScheduledCommitmentConfig.VERSION, "a"*64))
    else:
        args["config"] = SimpleNamespace(**c.config.to_document()["value"])
    with pytest.raises((ValueError, TypeError)):
        c.history.validate_source(**args)


@pytest.mark.parametrize("damage", ("old-history", "history-replay", "numerical-tolerance", "witness-lattice", "missing-fine", "frame-denominator", "frame-design", "causal-cutoff", "causal-role", "seed-leak", "available"))
def test_current_prefix_context_refuses_thinned_or_foreign_products(current, damage):
    c = current
    with pytest.raises((ValueError, TypeError)):
        if damage == "old-history":
            c.numerical.validate_source(c.source, c.old_history)
        elif damage == "history-replay":
            c.numerical.validate_source(c.source, replace(c.history, record_id="prefix.literal.replayed"))
        elif damage == "numerical-tolerance":
            control = replace(c.numerical.controls[0], tolerance=c.numerical.controls[0].tolerance + Decimal(".01"))
            replace(c.numerical, controls=(control, *c.numerical.controls[1:])).validate_source(c.source, c.history)
        elif damage == "witness-lattice":
            trace = replace(c.witness.traces[0], observations=c.witness.traces[0].observations[:-1])
            replace(c.witness, traces=(trace, *c.witness.traces[1:])).validate_source(c.source, c.history, c.numerical)
        elif damage == "missing-fine":
            replace(c.witness, traces=c.witness.traces[:2])
        elif damage == "frame-denominator":
            control = replace(c.frames.controls[1], measured_errors=c.frames.controls[1].measured_errors[:-1], applicable=c.frames.controls[1].applicable[:-1])
            replace(c.frames, controls=(c.frames.controls[0], control, *c.frames.controls[2:]))
        elif damage == "frame-design":
            replace(c.frames, numerical_design=replace(c.frames.numerical_design, object_fingerprint="e"*64)).validate_source(c.source, c.witness)
        elif damage == "causal-cutoff":
            replace(c.causal, cutoff_tick=c.causal.cutoff_tick+1)
        elif damage == "causal-role":
            replace(c.causal, root=replace(c.causal.root, independent_group_id="group.literal.foreign")).validate_source(c.source, c.history, c.numerical, c.witness, c.frames)
        elif damage == "seed-leak":
            replace(c.causal, arrays=replace(c.causal.arrays, members=tuple(sorted((*c.causal.arrays.members,
                c.history.arrays.members[0]), key=lambda member: member.name))))
        else:
            members = tuple(replace(member, finite_required=True) if member.name == "frame" else member for member in c.causal.arrays.members)
            frame = next(member for member in members if member.name == "frame")
            replace(c.causal, disposition="AVAILABLE", reason=None, frame_sha256=frame.sha256,
                arrays=replace(c.causal.arrays, members=members)).validate_source(c.source, c.history, c.numerical, c.witness, c.frames)


def old_products(case):
    return canonical_json_bytes((case.source, case.history, case.history.native.definition, case.history.checkpoint))
