# SPDX-License-Identifier: MPL-2.0
"""Native projections/nonentry over literal in-memory records; no native work.

All custody below is explicitly synthetic unpublished software metadata. No
RNG, integrator, acquisition, child process, storage or authority service runs.
"""

from dataclasses import fields, replace
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_bindings as preparation
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_future as future
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationHistory, preparation_identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import forecast_public
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import identity
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import package_identity
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory, expected_members
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, LogicalArtifactIdentity
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkContact
from tests.test_matrix_selected_point import feature
from tests.test_matrix_selected_protected import transfer, unpublished  # noqa: F401 - shared pure fixture
from tests.native_completion_fixtures import literal_completion


def literal_history(programme, *, native_version="1.0.0"):
    source = programme.sources.source_arms()[0][1]
    task = preparation.node_id(source, "history")
    parent = NativeEffectContact("run.synthetic-native", task, "attempt.synthetic-native",
        ObjectIdentity("plan.synthetic-native", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64),
        ObjectIdentity(task, "empirical-lawhood/runtime/execution-task", "1.0.0", "b" * 64),
        source.provenance.observed_git_head, ("material.synthetic-native",), ())
    context = SimpleNamespace(input_ports=(SimpleNamespace(materialization_id="material.synthetic-native"),))
    config_type = preparation.MatrixPreparationOperationConfigV2 if native_version == "2.0.0" else preparation.MatrixPreparationOperationConfig
    config = config_type("config." + task, "history", source,
        len(programme.sources.closure.reservation.allocation.canonical_bytes()))
    work = preparation.initial_native_work(context, config, source, parent)
    definition, = work.definitions
    values = {name: np.zeros(shape, dtype=dtype) for name, (dtype, shape) in expected_members(source).items()}
    for view, multiplier in (("primary", 1), ("fine", 2)):
        values[view + "_ticks"] = np.arange(multiplier * source.total_ticks + 1, dtype="<i8")
        values[view + "_alpha_tilde"][:] = np.asarray(source.recipe.half_tick_couplings[::2 // multiplier], dtype="<f8")
    # Initial bytes are the literal all-zero Hermitian arrays from the fixture.
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    initial_raw, _ = encode_matrix_arrays({"positions": np.zeros((2, 3, 4, 4), dtype="<c16"), "momenta": np.zeros((2, 3, 4, 4), dtype="<c16")})
    child = "native-subwork." + sha256((task + ":" + definition.subwork_id).encode()).hexdigest()
    raw, operand = preparation_science.preparation_array_product(source, initial_raw, values, artifact_id=child + ".output.arrays")
    contact = NativeSubworkContact(ObjectIdentity("begin.synthetic-native", "empirical-lawhood/runtime/native-subwork-begin", "1.0.0", "c" * 64))
    consumed = tuple(row for row in definition.streams if row.object_id.rsplit(".", 1)[-1].startswith("preparation"))
    completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record("contact.synthetic-native", contact), OperationalStatus.SUCCEEDED,
        ("arrays",), (), consumed, tuple(row for row in definition.streams if row not in consumed), (), InquiryCost(None, None, None),
        "synthetic unpublished literal metadata only", None, ())
    original_publication = unpublished(completion, child + ".completion")
    completion_publication = literal_completion(completion, child,
        visibility=original_publication.logical.visibility_ceiling, access=original_publication.logical.outcome_access)
    logical = LogicalArtifactIdentity(child + ".output.arrays", sha256(raw).hexdigest(), MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
        "application/x-npz", completion_publication.logical.visibility_ceiling, (), completion_publication.logical.outcome_access,
        ArtifactGenericValidation("validator.synthetic-native", "1.0.0", "a" * 64, MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ))
    physical = ArtifactMaterialization("material." + logical.logical_artifact_id, logical.logical_artifact_id, "storage.synthetic-unpublished", "unpublished/native.npz",
        sha256(raw).hexdigest(), len(raw), "none")
    arrays_publication = ArtifactWriteResult(logical, physical, replace(completion_publication.manifest_materialization,
        materialization_id="manifest." + child), False)
    receipt = CanonicalTaskReceipt("receipt." + parent.run_id + "." + child + ".attempt-001", parent.run_id, child,
        parent.run_id + "." + child + ".attempt-001", parent.implementation_commit, parent.input_materialization_ids,
        tuple(sorted((row.materialization for row in (arrays_publication, completion_publication)), key=lambda row: row.materialization_id)),
        tuple(sorted((row.logical for row in (arrays_publication, completion_publication)), key=lambda row: row.logical_artifact_id)),
        (), OperationalStatus.SUCCEEDED, ())
    root = source.root.root
    history = MatrixPreparationHistory("history." + source.source_id, source.identity, root.root_id, root.independent_group_id, root.clock_id,
        operand, MatrixParameterNativeHistory(definition, completion, receipt), source.total_ticks, source.total_ticks * 2)
    history.validate_source(source, programme.sources.closure.reservation.allocation)
    return source, history, work, initial_raw, raw


def test_actual_preparation_native_work_keeps_original_source_streams_config_and_group(transfer):  # noqa: F811
    source, history, work, _, _ = literal_history(transfer)
    assert work.scientific_unit_ids == (source.root.root.independent_group_id,)
    assert work.native_effect_slot_ids == preparation.slots(preparation.MatrixPreparationOperationConfig(
        "config." + preparation.node_id(source, "history"), "history", source, len(transfer.sources.closure.reservation.allocation.canonical_bytes())))
    assert work.definitions[0] == history.native.definition
    assert len(work.definitions[0].streams) == 4
    assert len(history.native.completion.consumed_streams) == 2
    assert len(history.native.completion.unconsumed_streams) == 2


def test_direct_preparation_native_revision_uses_only_actual_rng_pair_and_preserves_historical_scope(transfer):  # noqa: F811
    before = transfer.canonical_bytes()
    old_source, old_history, old_work, _, old_raw = literal_history(transfer)
    source, history, work, _, raw = literal_history(transfer, native_version="2.0.0")
    assert source == old_source and transfer.canonical_bytes() == before
    assert raw == old_raw and history.arrays.members == old_history.arrays.members
    definition, = work.definitions
    assert definition.operation_id == preparation.NAMESPACE + ".native.direct-inputs.v2"
    expected = {source.root.stream_identity(value) for value in source.root.streams if value.purpose.startswith("preparation")}
    assert set(definition.streams) == expected == set(history.native.completion.consumed_streams)
    assert history.native.completion.unconsumed_streams == ()
    assert set(definition.sources) == {source.identity, source.original.allocation, source.provenance.identity}
    assert len(source.root.streams) == len(old_work.definitions[0].streams) == 4
    assert len(old_history.native.completion.unconsumed_streams) == 2
    history.validate_source(source, transfer.sources.closure.reservation.allocation)
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    assert decode_canonical_bytes(old_history.canonical_bytes(), type(old_history), maximum_bytes=None) == old_history
    assert decode_canonical_bytes(history.canonical_bytes(), type(history), maximum_bytes=None) == history


@pytest.mark.parametrize("recovered", (False, True))
def test_preparation_native_closeout_reuses_authenticated_initial_and_decodes_output_once(transfer, monkeypatch, recovered):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_native_body
    from empirical_lawhood.infrastructure import matrix_array_io
    from tests.test_matrix_native_real_progress import DisclosedStore

    source, history, work, initial_raw, raw = literal_history(transfer, native_version="2.0.0")
    arrays = decode_matrix_arrays(raw, history.arrays)
    initial = preparation_science.initial_state(source.initial, initial_raw)
    store = DisclosedStore(raw if recovered else None)
    store.completed = SimpleNamespace(state=store.completed.state, receipt=history.native.receipt,
        completion=history.native.completion)
    monkeypatch.setattr(preparation_science, "acquire_preparation", lambda *args, **kwargs:
        pytest.fail("completed preparation was repeated") if recovered else arrays)
    monkeypatch.setattr(preparation_science, "initial_state", lambda *_:
        pytest.fail("authenticated child initial state was decoded again"))
    calls = []
    decode = matrix_array_io.decode_native_matrix_arrays
    def observed(*args, **kwargs):
        calls.append("decode")
        return decode(*args, **kwargs)
    monkeypatch.setattr(matrix_array_io, "decode_native_matrix_arrays", observed)
    context = SimpleNamespace(output_ports=(SimpleNamespace(profile=ArtifactProfile.MATRIX_ARRAY_NPZ,
        logical_artifact_id="array.preparation.parent-single-closeout"),))
    product, actual_raw = prepared_native_body._execute_preparation_native(context, source,
        transfer.sources.closure.reservation.allocation, initial_raw, store, work, prepared_initial=initial)
    assert actual_raw == raw and product.arrays.members == history.arrays.members
    assert product == replace(history, arrays=replace(history.arrays,
        array_artifact=replace(history.arrays.array_artifact, artifact_id=context.output_ports[0].logical_artifact_id)))
    assert calls == ["decode"] and store.entered == (0 if recovered else 1)
    product.validate_source(source, transfer.sources.closure.reservation.allocation)


@pytest.mark.parametrize("native_version", ("1.0.0", "2.0.0"))
def test_preparation_history_refuses_zero_consumed_or_wrong_purpose_partition(transfer, native_version):  # noqa: F811
    from tests.native_completion_fixtures import literal_completion, receipt_with_completion
    source, history, _, _, _ = literal_history(transfer, native_version=native_version)
    changed = replace(history.native.completion, consumed_streams=(), unconsumed_streams=history.native.definition.streams)
    original = history.native.receipt.output_logical_artifacts[0]
    publication = literal_completion(changed, history.native.receipt.task_id,
        visibility=original.visibility_ceiling, access=original.outcome_access)
    altered = replace(history, native=replace(history.native, completion=changed,
        receipt=receipt_with_completion(history.native.receipt, publication)))
    with pytest.raises(ValueError, match="stream census"):
        altered.validate_source(source, transfer.sources.closure.reservation.allocation)


@pytest.mark.parametrize("native_version", ("1.0.0", "2.0.0"))
def test_preparation_history_refuses_coherent_completion_in_another_array_lane(transfer, native_version):  # noqa: F811
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from tests.native_completion_fixtures import literal_completion, receipt_with_completion
    source, history, _, _, _ = literal_history(transfer, native_version=native_version)
    publication = literal_completion(history.native.completion, history.native.receipt.task_id,
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY, access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    altered = replace(history, native=replace(history.native,
        receipt=receipt_with_completion(history.native.receipt, publication)))
    with pytest.raises(ValueError, match="completion bytes, access or lineage"):
        altered.validate_source(source, transfer.sources.closure.reservation.allocation)


def test_selected_future_native_work_and_nonentry_keep_selected_points_and_all48_branches(transfer, monkeypatch):  # noqa: F811
    transfer = MatrixSelectedPublicProgramme.from_programme(transfer)
    source, history, _, _, _ = literal_history(transfer, native_version="2.0.0")
    public = next(row for _, row in transfer.point_design.sources if row.source == source.identity)
    observed = feature(transfer.point_design, public)
    # An unavailable prefix is a truthful complete nonentry, never a small run.
    from tests.test_matrix_selected_point import literal_unavailable_measurement
    _, _, prefix, _, _, prefix_raw, _ = literal_unavailable_measurement("E6_TRANSFER")
    prefix = replace(prefix, source=source.identity, preparation=preparation_identity(history.arrays),
        arrays=replace(prefix.arrays, source=source.identity, producers=tuple(sorted((source.identity, preparation_identity(history.arrays),
            prefix.witness, prefix.frame_assessment), key=lambda row: row.object_id))))
    point = forecast_selected_point(transfer.point_design, replace(observed, prefix=identity(prefix), frame_sha256=None,
        disposition="UNAVAILABLE", values=()), record_id="point.synthetic-native")
    protocol = transfer.protocol(source)
    # Produce mechanical nonentry from unchanged source/causal arrays, using the
    # literal templates retained in this fixture's assay metadata.
    from tests.test_matrix_prepared_assay_method import literal_protocol
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    templates, _ = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"), "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"),
        "trace_coefficients": np.zeros((2, 3), dtype="<f8"), "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    assert literal_protocol()[0].templates.array_artifact.sha256 == sha256(templates).hexdigest()
    _, mechanical = forecast_public(public, protocol, prefix, prefix_raw, templates, artifact_id="mechanical.synthetic-native")
    config = future.MatrixSelectedFutureConfigV2("config." + future.node_id(source, "responses"), transfer.identity, source, protocol,
        dict(transfer.panels)[source.root.root.independent_group_id], transfer.point_design.identity, package_identity(transfer.point_design.package), "responses")
    task = future.node_id(source, "responses")
    parent = replace(history.native.definition.parent_contact, task_id=task,
        execution_task=ObjectIdentity(task, "empirical-lawhood/runtime/execution-task", "1.0.0", "d" * 64))
    context = SimpleNamespace(run_id=parent.run_id, task_id=task, attempt_id=parent.attempt_id,
        input_materialization_ids=parent.input_materialization_ids)
    obsolete = future.MatrixSelectedFutureConfig(**{field.name: getattr(config, field.name) for field in fields(config)})
    with pytest.raises(TypeError, match="current direct-input"):
        future.initial_native_work(context, obsolete, history, prefix, point, mechanical, parent)
    work = future.initial_native_work(context, config, history, prefix, point, mechanical, parent)
    assert work.scientific_unit_ids == (source.root.root.independent_group_id,) and len(work.definitions[0].streams) == 4
    assert identity(point) in work.definitions[0].sources and identity(mechanical) in work.definitions[0].sources
    def forbidden(*args, **kwargs):
        raise AssertionError("known complete nonentry entered RNG/native child")
    monkeypatch.setattr(np.random, "Generator", forbidden)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_native_body import _execute_future_native
    values, _, native, disposition = _execute_future_native(config, history, prefix, mechanical, b"", b"", b"", SimpleNamespace(), work)
    assert disposition == "UNEVALUABLE" and native == ()
    assert np.array_equal(values["unentered_branches"], np.arange(48, dtype="<i8"))
    raw, arrays = future.array_product(source, values, artifact_id="future.synthetic-native")
    product = future.MatrixSelectedFutureHistory("responses.synthetic-native", source.identity, preparation_identity(history), identity(prefix), identity(point),
        identity(mechanical), ObjectIdentity.from_record(protocol.protocol_id, protocol), tuple(row.identity for row in config.panels),
        tuple(row[0] for row in branch_census(protocol, config.panels)), arrays, (), disposition)
    future.validate_future_history(config, history, prefix, point, mechanical, product)
    assert len(decode_matrix_arrays(raw, arrays)["unentered_branches"]) == 48
    readout = future.assess_future(config, history, prefix, point, mechanical, product, b"", b"", b"", raw, record_id="readout.synthetic-native")
    assert readout.disposition == "UNEVALUABLE" and len(readout.cells) == 240
    assert all(row.normalized_error is None for row in readout.cells)
    with pytest.raises(ValueError, match="selected point"):
        future.validate_future_history(config, history, prefix, replace(point, record_id="point.foreign"), mechanical, product)
