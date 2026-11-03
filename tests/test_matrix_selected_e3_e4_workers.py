# SPDX-License-Identifier: MPL-2.0
"""Actual pure DEV worker transport controls; all receipt pins are synthetic.

These controls exercise owning source/byte checks, never original qualification,
protected access, a native controller, durable publication or child processes.
"""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner, selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_workers import SelectedE3E4Worker
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility, inherited_visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity, derived_outcome_access
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401 - pure shared fixture

def invocation(config, values, producers, *, sealed_inputs=(), array_artifact_ids=None):
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE + "." + config.phase)
    manifest, task_id = declaration.manifest(), config.config_id.removeprefix("config.")
    ports, contracts, external, edges, receipts = [], [], [], [], {}
    for name, value in sorted({"automatic": config, **values}.items()):
        raw = value if type(value) is bytes else value.canonical_bytes()
        arrays = type(value) is bytes
        schema, media, profile = (MATRIX_ARRAY_SCHEMA, "application/x-npz", ArtifactProfile.MATRIX_ARRAY_NPZ) if arrays else (value.SCHEMA, "application/json", ArtifactProfile.CANONICAL_JSON)
        digest = sha256(raw).hexdigest()
        producer = producers.get(name)
        producer_output = None
        if type(producer) is tuple:
            producer, producer_output = producer
        access = Access.EVALUATION_SEALED if name in sealed_inputs else Access.DEVELOPMENT_VISIBLE
        logical_id = (config.config_id if name == "automatic" else
            array_artifact_ids[name] if arrays and array_artifact_ids is not None else "artifact." + name)
        logical = LogicalArtifactIdentity(logical_id, digest, schema, profile, media, Visibility.DEVELOPMENT_ONLY, (), access,
            ArtifactGenericValidation("validator.disclosed-e4-control", "1.0.0", "1" * 64, schema, profile))
        binding = WorkerInputBinding(logical.logical_artifact_id, "material." + name, schema, media, len(raw), Visibility.DEVELOPMENT_ONLY,
            access, WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical, binding, digest))
        output = None if producer is None else producer + "." + (producer_output or ("arrays" if arrays else "product"))
        if producer:
            receipts.setdefault(producer, []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external." + name, logical.logical_artifact_id, digest, schema, media,
                len(raw), Visibility.DEVELOPMENT_ONLY, access, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                producer, output, None if producer else "external." + name, "scientific." + name, logical.logical_artifact_id,
                schema, media, len(raw), access, Visibility.DEVELOPMENT_ONLY, BarrierKind.NONE))
    ports.sort(key=lambda row: row.artifact_id)
    contracts.sort(key=lambda row: row.artifact_id)
    dependencies = tuple(DependencyReceiptBinding("receipt." + task, task, tuple(sorted(materials))) for task, materials in sorted(receipts.items()))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id)
    outputs = tuple(WorkerOutputPort(task_id + "." + row.output_id, row.payload_schema, row.profile, row.media_type,
        "output.disclosed-e4-control." + row.output_id) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE, Access.DEVELOPMENT_VISIBLE, owner.BUDGET)
    output_access = derived_outcome_access(Access.DEVELOPMENT_VISIBLE, *(port.outcome_access for port in ports))
    output_visibility = inherited_visibility(tuple(port.visibility_ceiling for port in ports), output_access)
    task = ExecutionTask(task_id, owner.stage(config.phase), requirement, manifest.implementation_sha256, tuple(sorted(receipts)), tuple(external),
        tuple(ArtifactOutputSpec(output.output_id, output.logical_artifact_id, "unpublished/" + output.output_id + ".json", output.payload_schema, output.profile,
            output.media_type, output_visibility, tuple(port.visibility_ceiling for port in ports), output_access) for output in outputs),
        (), BarrierKind.NONE, 1, ("obligation.disclosed-e4-control",), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    plan = ObjectIdentity("plan.disclosed-e4-control", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64)
    packages = (("synthetic/control.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(packages, sha256(canonical_json_bytes(packages)).hexdigest(), "2" * 64, "3" * 40, False)
    context = TaskContext("run.disclosed-e4-control", task_id, "attempt.disclosed-e4-control", config_ref, tuple(row.binding for row in ports), tuple(ports),
        outputs, manifest.permissions, Access.DEVELOPMENT_VISIBLE, owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    prepared = PreparedInvocationContract("prepared.disclosed-e4-control", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4" * 64, "/synthetic", ()), context.run_id, task_id, context.attempt_id,
        config_ref, tuple(contracts), outputs, manifest.permissions, Access.DEVELOPMENT_VISIBLE, owner.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, dependencies, execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task),
        execution_task_record=task, required_input_artifact_ids=tuple(row.artifact_id for row in ports))
    context = replace(context, prepared_invocation=prepared)
    runner = SelectedE3E4Worker(config.phase, manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    return runner, context



def entry_invocation(f):
    config = owner.SelectedE3E4EntryConfig("config." + owner.global_node(f.programme, "entry"), f.programme, f.bank,
        f.evidence.identity, len(f.evidence.canonical_bytes()), f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)
    return invocation(config, {"evidence": f.evidence, "secondary-target": f.secondary_target}, {})


def test_actual_pure_entry_worker_preserves_complete_original_census_and_no_cal_bank(selected_bridge):  # noqa: F811
    runner, context = entry_invocation(selected_bridge)
    result = runner.execute(context)
    product = decode_canonical_bytes(result.outputs[0].payload, r.SelectedE3E4EntrySeal, maximum_bytes=None)
    assert product == r.entry_seal(selected_bridge.programme, selected_bridge.evidence, secondary_readout=selected_bridge.secondary_readout)
    assert len(product.groups) == 32 and len(product.sources) == 288
    assert b'"scores"' not in product.canonical_bytes()
    assert all(port._reader.stream.closed for port in context.input_ports)


def test_actual_dev_decoder_preserves_frozen_sealed_original_input_custody(selected_bridge):  # noqa: F811
    config = owner.SelectedE3E4EntryConfig("config." + owner.global_node(selected_bridge.programme, "entry"),
        selected_bridge.programme, selected_bridge.bank, selected_bridge.evidence.identity,
        len(selected_bridge.evidence.canonical_bytes()), selected_bridge.evidence.produced_input_parents, secondary_readout=selected_bridge.secondary_readout)
    # These are disclosed in-memory transport labels. Actual current grants and
    # byte-opening authority remain covered by the installed public lifecycle.
    runner, context = invocation(config, {"evidence": selected_bridge.evidence, "secondary-target": selected_bridge.secondary_target}, {},
        sealed_inputs=("automatic", "evidence", "secondary-target"))
    assert context.outcome_access is Access.DEVELOPMENT_VISIBLE
    assert all(port.outcome_access is Access.EVALUATION_SEALED for port in context.input_ports)
    assert context.prepared_invocation.execution_task_record.outputs[0].outcome_access is Access.EVALUATION_SEALED
    result = runner.execute(context)
    actual = decode_canonical_bytes(result.outputs[0].payload, r.SelectedE3E4EntrySeal, maximum_bytes=None)
    assert actual == r.entry_seal(selected_bridge.programme, selected_bridge.evidence, secondary_readout=selected_bridge.secondary_readout)
    assert len(actual.groups) == 32 and len(actual.sources) == 288
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("damage", ("unprepared", "run", "plan", "bytes"))
def test_actual_entry_worker_refuses_preparation_or_canonical_input_substitution(selected_bridge, damage):  # noqa: F811
    runner, context = entry_invocation(selected_bridge)
    if damage == "unprepared":
        runner = SelectedE3E4Worker("entry", runner.manifest)
    elif damage == "run":
        runner = runner.with_prepared_scope(("run.foreign", *runner.prepared_scope[1:]))
    elif damage == "plan":
        runner = runner.with_prepared_scope((*runner.prepared_scope[:3], replace(runner.prepared_scope[3], object_id="plan.foreign")))
    else:
        port = next(value for value in context.input_ports if value.artifact_id == "artifact.evidence")
        port._reader.raw = port._reader.raw[:-1] + b"X"
    with pytest.raises((ValueError, PermissionError), match="preparation|bytes"):
        runner.execute(context)
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.fixture(scope="module")
def e4_dense_case(selected_bridge):  # noqa: F811
    """Real equation/worker operands with disclosed synthetic native custody.

    Prefix observations and native receipt headers are literal software premises.
    The original/dense mechanical arrays, all48 supplied-innovation128-step
    response branches and their independent numerical controls are computed by
    current owners. This fixture performs no native contact or qualification.
    """
    from decimal import Decimal
    from types import SimpleNamespace

    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as common
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast, response_science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_native as native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science as method
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
        branch_census, response_consumed_streams,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source, selected_stream_operands
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import ArtifactMaterialization, CanonicalTaskReceipt
    from empirical_lawhood.runtime.native_subwork import NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact
    from tests.matrix_e4_structure_support import dense_array_operands, dense_response_arrays
    from tests.native_completion_fixtures import literal_completion, receipt_with_completion
    from tests.test_matrix_e4_response_nonentry import implementation, literal_prefix

    values = dense_array_operands(selected_bridge)
    f, source, protocol, panels = values.f, values.source, values.protocol, values.panels
    local = r.SelectedE3E4NativeSourceReference.from_bank(f.programme, f.bank,
        next(row for row in f.bank.sources if row.root_id == source.root_id), index=f.bank.source_index())
    source = bind_selected_native_source(local, values.source.provenance)
    entry = r.entry_seal(f.programme, f.evidence, secondary_readout=f.secondary_readout)
    prefix_config = owner.SelectedE3E4CompactConfig("config." + owner.local_node(source.root_id, "prefix"),
        f.programme.identity, local, protocol, panels, f.bank.response_selection.identity, "prefix")
    prefix_values = {"entry": entry, "source": local, "provenance": source.provenance,
        **{"streams." + str(index): row for index, (_, row) in enumerate(
            selected_stream_operands(local, panels, include_future=False))}}
    _, context = invocation(prefix_config, prefix_values, {"entry": owner.global_node(f.programme, "entry")})
    try:
        context = replace(context, prepared_invocation=replace(context.prepared_invocation, native_effect=True))
        kinds = (r.SelectedE3E4PrefixHistory, r.SelectedE3E4CausalPrefix, r.SelectedE3E4NumericalAssessment,
            r.SelectedE3E4Witness, r.SelectedE3E4Frames, r.SelectedE3E4Feature, r.SelectedE3E4MechanicalForecast)
        prefix, prefix_raw = literal_prefix(native, kinds, prefix_config, source, context,
            prefix_arrays=values.prefix_arrays)
    finally:
        for port in context.input_ports:
            port.close()

    def pin(name, kind):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())

    causal_raw, operand = method.array_product(source, values.causal_arrays, role="CAUSAL_STATE",
        artifact_id="array.e4-dense-worker.causal", producers=(common.identity(source),))
    causal = r.SelectedE3E4CausalPrefix("causal.e4-dense-worker", common.identity(source), common.identity(prefix),
        pin("numerical.e4-dense-worker", r.SelectedE3E4NumericalAssessment),
        pin("witness.e4-dense-worker", r.SelectedE3E4Witness),
        pin("frames.e4-dense-worker", r.SelectedE3E4Frames), common.identity(source.policy), source.root.root,
        source.policy.cutoff_tick, sha256(values.causal_arrays["frame"].tobytes()).hexdigest(), "AVAILABLE", None, operand)
    feature = r.SelectedE3E4Feature("feature.e4-dense-worker", common.identity(source), common.identity(causal),
        source.root_id, source.root.root.independent_group_id, FAMILY_MAP[source.coordinate.family_id],
        source.coordinate.clock_id, source.coordinate.physical_time(source.policy.cutoff_tick), causal.frame_sha256,
        "AVAILABLE", tuple((name, Decimal(0)) for name in FEATURES))
    points = f.bank.forecast_design.package.predict(values=feature.values, disposition=feature.disposition)
    account = r.SelectedE3E4AccountSeal("account.e4-dense-worker", f.bank.forecast_design.identity,
        common.identity(source), common.identity(causal), feature, f.bank.forecast_design.package.original_package,
        f.bank.forecast_design.package.calibration, points)
    original_raw, physical = method.mechanical(protocol, causal, values.causal_arrays, values.templates,
        artifact_id="output.disclosed-e4-control.arrays")
    assert physical.disposition == "AVAILABLE"
    frozen = decode_matrix_arrays(original_raw, physical.arrays)
    dense_raw, dense = response_forecast.forecast_e4_dense(protocol, causal, values.causal_arrays, values.templates,
        target=f.secondary_target, secondary=f.secondary_readout, original_physical=physical,
        original_forecast_raw=original_raw, artifact_id="output.disclosed-e4-control.dense-arrays",
        forecast_id="dense-mechanical." + source.root_id)
    received = dense_response_arrays(source, protocol, panels, values.prefix_arrays, frozen)

    response_config = native.phase_config(prefix_config, "responses")
    response_values = {"entry": entry, "source": local, "provenance": source.provenance,
        "prefix": prefix, "prefix-arrays": prefix_raw, "checkpoint": prefix.checkpoint,
        "causal": causal, "account": account, "mechanical": physical, "mechanical-arrays": original_raw,
        **{"streams." + str(index): row for index, (_, row) in enumerate(
            selected_stream_operands(local, panels, include_future=True))}}
    producers = {"entry": owner.global_node(f.programme, "entry"),
        **{name: (owner.local_node(source.root_id, phase), output) for name, phase, output in (
            ("prefix", "prefix", "product"), ("prefix-arrays", "prefix", "arrays"),
            ("checkpoint", "prefix", "checkpoint"), ("causal", "project", "product"),
            ("account", "account", "product"), ("mechanical", "mechanical", "product"),
            ("mechanical-arrays", "mechanical", "arrays"))}}
    _, context = invocation(response_config, response_values, producers, array_artifact_ids={
        "prefix-arrays": prefix.arrays.array_artifact.artifact_id,
        "mechanical-arrays": physical.arrays.array_artifact.artifact_id})
    try:
        prepared = replace(context.prepared_invocation, native_effect=True, implementation=implementation(source.provenance))
        context = replace(context, prepared_invocation=prepared)
        definition, = native.initial_native_work(context, response_config, response_values, {},
            prepared.expected_parent_contact).definitions
        child = "native-subwork." + sha256((context.task_id + ":" + definition.subwork_id).encode()).hexdigest()
        response_raw, response_operand = response_forecast.array_product(protocol, received, role="RESPONSES",
            artifact_id=child + ".output.arrays", producers=(common.identity(source),
                f.bank.response_selection.identity, common.identity(physical), account.identity), access=r.DEV, visibility=r.EXPOSED)
        logical_id = child + ".output.arrays"
        logical = LogicalArtifactIdentity(logical_id, sha256(response_raw).hexdigest(), MATRIX_ARRAY_SCHEMA,
            ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", r.EXPOSED, (), r.DEV,
            ArtifactGenericValidation("validator.disclosed-e4-dense-arrays", "1.0.0", "a" * 64,
                MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ))
        material = ArtifactMaterialization("material." + logical_id, logical_id, "storage.synthetic-unpublished",
            "unpublished/" + logical_id, logical.content_sha256, len(response_raw), "none")
        attempt = context.run_id + "." + child + ".attempt-001"
        receipt = CanonicalTaskReceipt("receipt." + attempt, context.run_id, child, attempt,
            source.provenance.observed_git_head, context.input_materialization_ids, (material,), (logical,), (),
            OperationalStatus.SUCCEEDED, ())
        contact = NativeSubworkContact(pin("begin.disclosed-e4-dense-response", NativeSubworkBegin))
        consumed = response_consumed_streams(source, protocol, definition.streams)
        completion = NativeSubworkCompletion(definition.identity,
            ObjectIdentity.from_record("contact.disclosed-e4-dense-response", contact), OperationalStatus.SUCCEEDED,
            ("arrays",), (), consumed, tuple(row for row in definition.streams if row not in consumed), (),
            InquiryCost(None, None, None), "Synthetic custody premise for actual supplied-innovation equation arrays; no native contact", None, ())
        receipt = receipt_with_completion(receipt, literal_completion(completion, child, visibility=r.EXPOSED, access=r.DEV))
        responses = r.SelectedE3E4Responses("responses.e4-dense-worker", common.identity(source), common.identity(causal),
            common.identity(physical), account.identity, ObjectIdentity.from_record(protocol.protocol_id, protocol),
            response_operand, tuple(row[0] for row in branch_census(protocol, panels)),
            (common.ScheduledNativeEvidence(definition, completion, receipt),), "COMPLETED", ())
        responses.validate_source(source, prefix, causal, physical, account, config=response_config, prefix_config=prefix_config)
    finally:
        for port in context.input_ports:
            port.close()
    score = response_science.assess_paired_response_arrays(source, causal, prefix, values.prefix_arrays,
        physical, frozen, protocol, panels, responses, received, error_forecast=account.identity,
        score_id="score." + source.root_id)
    assert score.disposition == "FINITE" and score.numerical_pass and len(score.controls) == 48
    dense_score = response_science.score_e4_dense(source, protocol, panels, target=f.secondary_target,
        secondary=f.secondary_readout, original_score=score, original_physical=physical, dense_physical=dense,
        responses=responses, original_forecast_raw=original_raw, dense_forecast_raw=dense_raw,
        response_raw=response_raw, score_id="dense-score." + source.root_id)
    return SimpleNamespace(f=f, source=source, local=local, protocol=protocol, panels=panels, entry=entry,
        prefix=prefix, prefix_raw=prefix_raw, prefix_arrays=values.prefix_arrays, causal=causal,
        causal_raw=causal_raw, causal_arrays=values.causal_arrays, templates=values.templates,
        template_raw=values.template_raw, account=account, original_physical=physical,
        original_forecast_raw=original_raw, dense_physical=dense, dense_forecast_raw=dense_raw,
        responses=responses, response_raw=response_raw, original_score=score, dense_score=dense_score,
        frozen=frozen, received=received, prefix_config=prefix_config)


def _dense_worker_invocation(case, phase, *, damage=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays

    root = case.source.root_id
    if phase == "mechanical":
        config = owner.SelectedE3E4PublicConfig("config." + owner.local_node(root, phase),
            case.f.programme.identity, case.protocol.public_source, case.protocol, phase, case.f.secondary_readout)
        values = {"entry": case.entry, "causal": case.causal, "causal-arrays": case.causal_raw,
            "templates": case.template_raw, "secondary-target": case.f.secondary_target}
    else:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_native import phase_config
        config = phase_config(case.prefix_config, phase)
        values = {"entry": case.entry, "source": case.local, "provenance": case.source.provenance,
            "prefix": case.prefix, "prefix-arrays": case.prefix_raw, "causal": case.causal,
            "causal-arrays": case.causal_raw, "account": case.account, "mechanical": case.original_physical,
            "mechanical-arrays": case.original_forecast_raw, "responses": case.responses,
            "response-arrays": case.response_raw, "templates": case.template_raw,
            "secondary-target": case.f.secondary_target, "secondary-readout": case.f.secondary_readout,
            "dense-mechanical": case.dense_physical, "dense-mechanical-arrays": case.dense_forecast_raw}
    producers = {"entry": owner.global_node(case.f.programme, "entry"),
        **{name: (owner.local_node(root, producer), output) for name, producer, output in (
            ("prefix", "prefix", "product"), ("prefix-arrays", "prefix", "arrays"),
            ("causal", "project", "product"), ("causal-arrays", "project", "arrays"),
            ("account", "account", "product"), ("mechanical", "mechanical", "product"),
            ("mechanical-arrays", "mechanical", "arrays"), ("dense-mechanical", "mechanical", "dense-product"),
            ("dense-mechanical-arrays", "mechanical", "dense-arrays"),
            ("responses", "responses", "product"), ("response-arrays", "responses", "arrays")) if name in values}}
    if damage in ("missing-dense-record", "missing-dense-arrays"):
        del values["dense-mechanical" if damage == "missing-dense-record" else "dense-mechanical-arrays"]
    elif damage == "dense-archive-bytes":
        values["dense-mechanical-arrays"] += b"\n"
    elif damage == "dense-unsampled-value":
        changed = {name: value.copy() for name, value in decode_matrix_arrays(
            case.dense_forecast_raw, case.dense_physical.arrays).items()}
        changed["primary_factor"][0, 1, 0] += 1e-6
        raw, operand = response_forecast.array_product(case.protocol, changed, role="FORECAST",
            artifact_id=case.dense_physical.arrays.array_artifact.artifact_id,
            producers=case.dense_physical.arrays.producers, access=r.DEV, visibility=r.EXPOSED)
        values["dense-mechanical-arrays"] = raw
        values["dense-mechanical"] = replace(case.dense_physical, arrays=operand)
    elif damage == "dense-producer-output":
        producers["dense-mechanical"] = (owner.local_node(root, "mechanical"), "product")
    elif damage == "entry-selection":
        values["entry"] = replace(case.entry,
            secondary_readout=replace(case.entry.secondary_readout, object_fingerprint="f" * 64))
    declared_arrays = {"causal-arrays": case.causal.arrays.array_artifact,
        "templates": case.protocol.templates.array_artifact, "prefix-arrays": case.prefix.arrays.array_artifact,
        "mechanical-arrays": case.original_physical.arrays.array_artifact,
        "dense-mechanical-arrays": case.dense_physical.arrays.array_artifact,
        "response-arrays": case.responses.arrays.array_artifact}
    return invocation(config, values, producers, array_artifact_ids={
        name: artifact.artifact_id for name, artifact in declared_arrays.items() if name in values})


def _forbid_dense_effects(monkeypatch, *, cold):
    import numpy as np
    import scipy.linalg

    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments, parameter_source
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore

    def forbidden(*_args, **_kwargs):
        pytest.fail("dense pure worker entered an acquisition, RNG or new cold eigensolve")

    owners = [(parameter_history_segments, ("acquire_parameter_segment",)),
        (parameter_source, ("acquire_parameter_history",)),
        (ExternalNativeEffectContactStore, ("begin",)), (ExternalNativeSubworkStore, ("begin", "contact")),
        (LocalProcessExecutor, ("execute", "execute_deadline_free")),
        (np.random, ("Generator", "PCG64", "PCG64DXSM", "default_rng"))]
    if cold:
        owners.extend(((response_forecast, ("_hessian",)), (np.linalg, ("eigh", "eigvalsh")),
            (scipy.linalg, ("eigh", "eigvalsh"))))
    for module, names in owners:
        for name in names:
            monkeypatch.setattr(module, name, forbidden)


def test_actual_e4_mechanical_worker_emits_both_exact_archives_before_any_future(e4_dense_case, monkeypatch):
    case = e4_dense_case
    _forbid_dense_effects(monkeypatch, cold=False)
    runner, context = _dense_worker_invocation(case, "mechanical")
    result = runner.execute(context)
    outputs = {row.output_id.rsplit(".", 1)[1]: row.payload for row in result.outputs}
    assert set(outputs) == {"product", "arrays", "dense-product", "dense-arrays"}
    assert outputs["product"] == case.original_physical.canonical_bytes()
    assert outputs["arrays"] == case.original_forecast_raw
    assert outputs["dense-product"] == case.dense_physical.canonical_bytes()
    assert outputs["dense-arrays"] == case.dense_forecast_raw
    assert case.dense_physical.secondary_target == case.f.secondary_target.identity
    assert case.dense_physical.secondary_selection == case.entry.secondary_readout
    assert all(port._reader.stream.closed for port in context.input_ports)


def test_actual_e4_score_worker_cold_reproves_both_archives_and_preserves_original_score(e4_dense_case, monkeypatch):
    case = e4_dense_case
    _forbid_dense_effects(monkeypatch, cold=True)
    runner, context = _dense_worker_invocation(case, "response-score")
    result = runner.execute(context)
    outputs = {row.output_id.rsplit(".", 1)[1]: row.payload for row in result.outputs}
    assert set(outputs) == {"product", "dense-score"}
    assert outputs["product"] == case.original_score.canonical_bytes()
    assert outputs["dense-score"] == case.dense_score.canonical_bytes()
    assert len(case.dense_score.cells) == 2 * 2 * 4 * 5 * 29
    assert len(case.original_score.controls) == 48 and case.original_score.numerical_pass
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("damage", ("missing-dense-record", "missing-dense-arrays", "dense-archive-bytes",
    "dense-unsampled-value", "dense-producer-output", "entry-selection"))
def test_actual_e4_score_worker_refuses_missing_or_substituted_dense_custody_before_output(e4_dense_case, monkeypatch, damage):
    _forbid_dense_effects(monkeypatch, cold=True)
    runner, context = _dense_worker_invocation(e4_dense_case, "response-score", damage=damage)
    expected = {
        "missing-dense-record": "omits a required exact scientific operand",
        "missing-dense-arrays": "omits a required exact scientific operand",
        "dense-archive-bytes": "Matrix dataset port substitutes its original artifact binding",
        "dense-unsampled-value": "scheduled cold forecast substitutes actual frozen forces/receivers/predictions/witnesses",
        "dense-producer-output": "replaces the exact ordinary scientific producer/output",
        "entry-selection": "E4 score changes its actual pre-future entry-selected target",
    }
    with pytest.raises(ValueError, match=expected[damage]):
        runner.execute(context)
    assert all(port._reader.stream.closed for port in context.input_ports)
