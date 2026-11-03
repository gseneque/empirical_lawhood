# SPDX-License-Identifier: MPL-2.0
"""Actual protected E4 native worker consumers; disclosed tiny software fixture.

The fixture uses existing exposed scheduled CONF keys and really executes an
6-tick protected prefix within an 8-tick history to supply exact original typed history/receipt inputs.
The decision is an explicitly synthetic NOT_TRIGGERED branch. No public issue,
real qualification or candidate authority is asserted. Added controls execute no
continuation/response solver; durable BEGIN is distinct from native CONTACT.
Triggered CAL/CONF model-bearing point parity/source admission remain separate.
"""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old, science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_science as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as programme_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as devrecords
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4RevisionNomination, SelectedE4FrozenRevision
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP, ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_protected_workers import SelectedE4ProtectedWorker
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.infrastructure.numerical_provenance import selected_worker_environment
from empirical_lawhood.kernel.evidence import EvidenceCeiling, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.native_subwork import NativeSubworkInputError, NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from tests.test_matrix_e4_worker_preflight import pin, record_exposure
from tests.test_matrix_factor_confirmation_eligibility import stock, provenance, publish  # noqa: F401
from tests.test_matrix_scheduled_history import scheduled  # noqa: F401
from tests.test_matrix_scheduled_response_forecast import pauli
from tests.test_matrix_prepared_assay_method import literal_protocol
from tests.test_matrix_selected_package import package
from tests.worker_configuration_support import freeze_worker_configuration


def _store(plane, parent, inputs=(), *, prepared_invocation=None):
    phase = parent.task_id.rsplit('.', 1)[-1]
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=owner.access(phase))
    return ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts,
        parent_contact=parent, parent_inputs=inputs, prepared_invocation=prepared_invocation)


def invoke(case, phase, extra=None, *, suffix="original"):
    config = replace(case.config, phase=phase, config_id="config."+owner.local_node(case.source.root_id, phase))
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE+"."+phase)
    manifest = declaration.manifest()
    values = {"entry": case.entry, "source": case.local, "provenance": case.source.provenance,
        **{"streams."+str(index): value for index, value in enumerate(case.source.root.streams)}}
    producers = {"entry": (owner.NAMESPACE+".entry."+case.programme.object_fingerprint+".wave."+case.entry.wave_id, "product")}
    if phase != "prefix":
        values.update(case.future)
        producers.update({name: (owner.local_node(case.source.root_id, producer), output) for name, producer, output in (
            ("prefix", "prefix", "product"), ("prefix-arrays", "prefix", "arrays"),
            ("checkpoint", "prefix", "checkpoint"), ("causal", "project", "product"),
            ("account", "account", "product"), ("mechanical", "mechanical", "product"))})
    if phase == "responses":
        values["mechanical-arrays"] = case.physical_raw
        producers["mechanical-arrays"] = (owner.local_node(case.source.root_id, "mechanical"), "arrays")
        independent = next(row for row in case.panels if row.role == "INDEPENDENT_FUTURE")
        values.update({"streams."+str(index+4): value for index, value in enumerate(independent.streams)})
    values.update(extra or {})
    values["automatic"] = config
    verified, bindings, external, edges, dependencies = [], [], [], [], {}
    for index, (name, value) in enumerate(sorted(values.items())):
        array = type(value) is bytes
        raw = value if array else value.canonical_bytes()
        lane = owner.access(phase) if name == "automatic" else owner.input_access(name)
        logical_id = config.config_id if name == "automatic" else "e4-control."+phase+"."+suffix+"."+name
        result = case.plane.write(ArtifactWriteRequest(logical_id,
            "worker-inputs/"+phase+"/"+suffix+"/"+str(index).zfill(2)+( ".npz" if array else ".json"),
            MATRIX_ARRAY_SCHEMA if array else value.SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ if array else ArtifactProfile.CANONICAL_JSON,
            "application/x-npz" if array else "application/json", "e4-software-controls", "worker-inputs", raw,
            Visibility.PROSPECTIVE, (), lane))
        selected = VerifiedArtifactInput(result.logical, result.materialization)
        verified.append(selected)
        producer = producers.get(name)
        binding = WorkerInputBinding.from_verified(selected, kind=WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        bindings.append(binding)
        if producer:
            dependencies.setdefault(producer[0], []).append(binding.materialization_id)
        else:
            external.append(ExternalInputSpec("external."+name, logical_id, result.logical.content_sha256,
                result.logical.payload_schema, result.logical.media_type, len(raw), Visibility.PROSPECTIVE, lane, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge."+name, name, ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                None if producer is None else producer[0], None if producer is None else producer[0]+"."+producer[1],
                "external."+name if producer is None else None, "scientific."+name, logical_id,
                result.logical.payload_schema, result.logical.media_type, len(raw), lane,
                Visibility.PROSPECTIVE, BarrierKind.NONE))
    task_id = owner.local_node(case.source.root_id, phase)
    receipts = tuple(DependencyReceiptBinding("receipt.control."+name, name, tuple(sorted(materials)))
        for name, materials in sorted(dependencies.items()))
    config_input = next(row for row in verified if row.artifact_id == config.config_id)
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config_input.artifact_id)
    outputs = tuple(WorkerOutputPort(task_id+"."+row.output_id, row.payload_schema, row.profile, row.media_type,
        "e4-control.output."+phase+"."+row.output_id) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE,
        owner.access(phase), owner.BUDGET)
    task = ExecutionTask(task_id, owner.stage(phase), requirement, manifest.implementation_sha256,
        tuple(sorted(dependencies)), tuple(external), tuple(ArtifactOutputSpec(row.output_id, row.logical_artifact_id,
            "outputs/"+phase+"/"+row.output_id, row.payload_schema, row.profile, row.media_type,
            Visibility.PROSPECTIVE, (Visibility.PROSPECTIVE,), owner.access(phase)) for row in outputs),
        (), BarrierKind.NONE, 1, ("obligation.e4-control."+phase,), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    verified.sort(key=lambda row: row.artifact_id)
    bindings.sort(key=lambda row: row.artifact_id)
    ports = case.plane.open_many(tuple(verified), bindings=tuple(bindings), maximum_bytes=None)
    context = TaskContext("run.e4-worker-control", task_id, "attempt.e4-worker-control."+phase,
        config_ref, tuple(bindings), ports, outputs, manifest.permissions, owner.access(phase),
        owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    plan = ObjectIdentity("plan.e4-worker-control", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a"*64)
    runner = SelectedE4ProtectedWorker(phase, manifest).with_prepared_scope((context.run_id, task_id, context.input_materialization_ids, plan))
    initial = lifecycle.prepare_worker_invocation(runner, context, tuple(verified), implementation=case.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task,
        native_effect=True, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
    bound = replace(context, prepared_invocation=initial)
    work = runner.prepare_native_work(bound, expected_parent=initial.expected_parent_contact)
    final = replace(initial, native_work=work)
    return runner, replace(context, prepared_invocation=final), final, tuple(verified)


def ready(runner, context, contract):
    result = lifecycle._worker_preflight(runner, context, contract, (MATRIX_PROVENANCE_REQUIREMENT,),
        native_work_preparer=owner.prepare_native_work)
    assert result.ready, tuple((row.operand_id, row.reason) for row in result.mismatches)
    return result


@pytest.fixture
def protected_native_case(scheduled, provenance, monkeypatch):  # noqa: F811
    for name, value in selected_worker_environment():
        monkeypatch.setenv(name, value)
    with threadpool_limits(limits=1):
        plane, sources = scheduled
        source = next(row for row in sources if row.root.root.role.value == "CONFIRMATION")
        policy = replace(source.policy, origin_sector="Y")
        selection = replace(source.specification.selection, prefix_policies=(policy,),
            coordinate_policies=tuple((co, old.identity(policy)) for co, _ in source.specification.selection.coordinate_policies))
        specification = replace(source.specification, selection=selection,
            publication=publish(plane, selection, "worker-control.selection"))
        index=ScheduledSourceIndex.from_shared(reservation=source.reservation,specification=specification,provenances=(provenance,))
        source=index.resolve(index.reference(source_id=source.source_id,root_id=source.root_id,provenance=provenance.identity))
        programme, bank = pin("programme.e4-worker-control", programme_owner.SelectedE4PhaseProgramme), pin("bank.e4-worker-control", programme_owner.SelectedE4PhaseBank)
        local = r.SelectedE4ProtectedNativeSourceReference("native."+source.source_id, programme, bank,
            source.reference, ScheduledPublicSource.from_source(source), policy,
            source.numerical_design, provenance.identity, len(provenance.canonical_bytes()))
        protocol, _ = literal_protocol()
        protocol = replace(protocol, public_source=local.public, horizon_steps=(1, 2),
            templates=replace(protocol.templates, source=local.reference.identity, producers=(local.reference.identity,)))
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
        from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
        group = source.root.root.independent_group_id
        panels = (ScheduledResponsePanel("panel.e4-worker.common", group, "COMMON_NOISE_PANEL", "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", source.root.streams),
            ScheduledResponsePanel("panel.e4-worker.independent", group, "INDEPENDENT_FUTURE", "FRESH_DECLARED_FUTURE_START_AT_CUTOFF",
                tuple(MatrixHistorySeed(purpose, sha256(("EXPOSED_E4_PROTECTED_WORKER_CONTROL"+purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
        original = package()
        summary = programme_owner.SelectedE4OriginalCalibrationSummary.from_package(original,
            record_id="summary.e4-protected-worker-control")
        decision = programme_owner.SelectedE4PublicRevisionDecision("decision.e4-protected-worker-control",
            pin("development.e4-protected-worker-control", devrecords.SelectedE3E4DevelopmentProgramme),
            pin("nomination.e4-protected-worker-control", SelectedE4RevisionNomination),
            pin("frozen.e4-protected-worker-control", SelectedE4FrozenRevision),
            "NOT_TRIGGERED", "UNENTERED", None, None)
        config = owner.SelectedE4ProtectedCompactConfig("config." + owner.local_node(source.root_id, "prefix"),
            programme, local, protocol, panels,
            ObjectIdentity("selection.e4-protected-worker-control", "empirical-lawhood/matrix-scheduled-history/response-selection", "1.0.0", "b" * 64),
            "prefix", "CONFIRMATION", decision, None, None, summary)
        entry = r.SelectedE4ProtectedEntrySeal("entry.e4-protected-worker-control", programme, bank,
            pin("forecast-design.e4-worker-control", devrecords.SelectedE3E4ForecastDesign),
            pin("evidence.e4-worker-control", r.SelectedE4ProtectedEvidence), (group,),
            tuple(sorted((local.reference.identity, *(pin("source.control." + str(index).zfill(2), old.ScheduledSource)
                for index in range(8))), key=lambda row: row.object_id)),
            "CONFIRMATION", "wave.e4-protected-worker-control", None, decision.identity, None, None, secondary_readout=pin("secondary.disclosed-control", MatrixE4SecondaryReadoutSelection))
        case = SimpleNamespace(plane=plane, source=source, local=local, config=config, programme=programme,
            panels=panels, entry=entry, implementation=implementation_binding(Path(__file__).resolve().parents[1]))
        runner, context, contract, inputs = invoke(case, "prefix")
        ready(runner, context, contract)
        store = _store(plane, contract.expected_parent_contact, tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs), prepared_invocation=contract)
        store.parent_contacts.begin(contract.expected_parent_contact)
        result = runner.execute_with_native_subwork(context, store)
        raw_outputs = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        history = decode_canonical_bytes(raw_outputs["product"], r.SelectedE4ProtectedPrefixHistory, maximum_bytes=None)
        record_exposure(case, "prefix", completion=history.native.completion, raw=raw_outputs["arrays"])
        prefix = science.consume_prefix(bind_selected_native_source(local, provenance), history.arrays, raw_outputs["arrays"])
        frame = np.asarray([np.kron(value, np.eye(2))/2 for value in pauli()], dtype="<c16")
        causal_values = {**prefix, "frame": frame}
        _, causal_arrays = method.array_product(source, causal_values, role="CAUSAL_STATE", artifact_id="control.causal.arrays",
            producers=(old.identity(source),))
        causal = r.SelectedE4ProtectedCausalPrefix("causal.e4-worker-control", old.identity(source), old.identity(history),
            pin("numerical.control", r.SelectedE4ProtectedNumericalAssessment), pin("witness.control", r.SelectedE4ProtectedWitness),
            pin("frames.control", r.SelectedE4ProtectedFrames), old.identity(policy), source.root.root, policy.cutoff_tick,
            sha256(frame.tobytes()).hexdigest(), "AVAILABLE", None, causal_arrays)
        feature = r.SelectedE4ProtectedFeature("feature.e4-worker-control", old.identity(source), old.identity(causal), source.root_id,
            group, FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id, source.coordinate.physical_time(policy.cutoff_tick),
            causal.frame_sha256, "AVAILABLE", tuple((name, D(1)) for name in FEATURES))
        account = r.SelectedE4ProtectedAccountSeal("account.e4-worker-control", entry.forecast_design,
            old.identity(source), old.identity(causal), feature, original.identity, old.identity(original.calibration),
            summary, tuple((name, (D(0),) * 15) for name in METHODS), None, decision.identity, None)
        templates = {"generic_basis": np.asarray([np.kron(np.eye(2), value)/2 for value in pauli()], dtype="<c16"),
            "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8")/np.sqrt(6),
            "trace_coefficients": np.ones((2, 3), dtype="<f8")/np.sqrt(6),
            "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)}
        physical_values, disposition, dispositions = response_forecast.forecast_response_arrays(protocol, causal_values, templates, disposition="AVAILABLE")
        assert disposition == "AVAILABLE"
        physical_raw, physical_arrays = response_forecast.array_product(protocol, physical_values, role="FORECAST",
            artifact_id="control.physical.arrays", producers=(old.identity(source), old.identity(causal)),
            access=r.BLIND, visibility=Visibility.PROSPECTIVE,
            nonfinite=tuple(name for name, value in physical_values.items() if not np.isfinite(value).all()))
        mechanical = r.SelectedE4ProtectedMechanicalForecast("mechanical.e4-worker-control", old.identity(source), old.identity(causal),
            ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
            causal.frame_sha256, physical_arrays, disposition, dispositions)
        case.future = {"prefix": history, "prefix-arrays": raw_outputs["arrays"], "checkpoint": history.checkpoint,
            "causal": causal, "account": account, "mechanical": mechanical}
        case.physical_raw = physical_raw
        case.physical_values = physical_values
        case.prefix_store = store
        case.prefix_raw = raw_outputs
        yield case



PHASES = ('prefix', 'continue', 'responses')


def _invocation(case, phase, *, suffix):
    runner, context, contract, inputs = invoke(case, phase, suffix=suffix)
    if phase == 'prefix':
        # The shared fixture already completed a prefix at its original contact.
        # This distinct software run reuses the same disclosed keys without
        # acquiring them, inventing freshness or touching the completed custody.
        context = replace(context, run_id=context.run_id + '.boundary-control',
            attempt_id=context.attempt_id + '.boundary-control', prepared_invocation=None)
        runner = type(runner)(phase, runner.manifest).with_prepared_scope((
            context.run_id, context.task_id, context.input_materialization_ids, contract.execution_plan))
        initial = lifecycle.prepare_worker_invocation(runner, context, inputs,
            implementation=case.implementation, execution_plan=contract.execution_plan,
            execution_task=contract.execution_task, execution_task_record=contract.execution_task_record,
            native_effect=True, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
        work = runner.prepare_native_work(replace(context, prepared_invocation=initial),
            expected_parent=initial.expected_parent_contact)
        contract = replace(initial, native_work=work)
        context = replace(context, prepared_invocation=contract)
    return runner, context, contract, inputs


def _ready_store(case, phase, *, suffix):
    runner, context, contract, inputs = _invocation(case, phase, suffix=suffix)
    ready(runner, context, contract)
    manifests = tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs)
    store = _store(case.plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    definition, = contract.native_definitions
    roster, = contract.native_work.rosters
    # This is a disclosed custody-only parent contact, not a solver invocation.
    store.parent_contacts.begin(contract.expected_parent_contact)
    store.freeze_roster(roster, definitions=(definition,))
    return runner, context, contract, inputs, store, definition


def _close(context, store=None, parent=None):
    for port in context.input_ports:
        port.close()
    if store is not None:
        store.parent_contacts.retire_live_creator(parent)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_protected_e4_native_ready_reaches_exact_durable_begin_without_native_contact(protected_native_case, phase):  # noqa: F811
    runner, context, contract, inputs, store, definition = _ready_store(
        protected_native_case, phase, suffix='ready-begin')
    try:
        assert definition.parent_contact == contract.expected_parent_contact
        assert len(definition.streams) == (8 if phase == 'responses' else 4)
        assert set(definition.input_materialization_ids) == {row.materialization.materialization_id for row in inputs}
        assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED
        store.begin(definition)
        observed = store.inspect(definition)
        assert observed.state is NativeSubworkState.BEGUN
        assert observed.begin is not None and observed.contact is None
        assert observed.completion is None and observed.receipt is None
        assert store.read_roster(definition.parent_contact, definition.roster_id).subworks == (definition.identity,)
    finally:
        _close(context, store, contract.expected_parent_contact)


@pytest.mark.parametrize('phase', PHASES)
@pytest.mark.parametrize('damage', ('source-body', 'source-sidecar', 'source-marker'))
def test_actual_protected_e4_begin_replays_late_input_publication_damage(protected_native_case, phase, damage):  # noqa: F811
    runner, context, contract, inputs, store, definition = _ready_store(
        protected_native_case, phase, suffix='late-' + damage)
    original = next(row for row in inputs if row.artifact_id.endswith('.source'))
    source_path = protected_native_case.plane.root.resolve(original.materialization.relative_path, for_write=False)
    sidecar = source_path.with_name(source_path.name + '.manifest.json')
    manifest = decode_artifact_manifest(sidecar.read_bytes())
    assert manifest.publication is not None
    target = (source_path if damage == 'source-body' else sidecar if damage == 'source-sidecar' else
        protected_native_case.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False))
    saved = target.read_bytes()
    try:
        # Original custody changes while worker ports retain sealed bytes.
        # BEGIN must independently refuse its fresh read before any contact.
        target.write_bytes(saved[:-1] + bytes((saved[-1] ^ 1,)))
        with pytest.raises(NativeSubworkInputError) as refused:
            store.begin(definition)
        assert refused.value.mismatches
        observed = store.inspect(definition)
        assert observed.state is NativeSubworkState.NOT_ENTERED
        assert observed.begin is None and observed.contact is None
        assert store.parent_contacts.read(context.run_id, context.task_id) == contract.expected_parent_contact
        if damage == 'source-body':
            cursor = next(port for port in context.input_ports if port.artifact_id == original.artifact_id).cursor()
            try:
                assert cursor.read() == saved
            finally:
                cursor.close()
            sealed = lifecycle._worker_preflight(runner, context, contract,
                (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
            assert sealed.ready
    finally:
        target.write_bytes(saved)
        assert target.read_bytes() == saved
        _close(context, store, contract.expected_parent_contact)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_protected_e4_ready_stops_replaced_dependency_receipt_after_preparation(protected_native_case, phase):  # noqa: F811
    runner, context, contract, inputs = _invocation(protected_native_case, phase, suffix='late-dependency')
    try:
        ready(runner, context, contract)
        original = context.dependency_receipts[0]
        substituted = replace(original, receipt_id=original.receipt_id + '.substituted')
        with pytest.raises(ValueError, match='complete worker context'):
            replace(context, dependency_receipts=(substituted, *context.dependency_receipts[1:]))
        changed = replace(context, dependency_receipts=(substituted, *context.dependency_receipts[1:]),
            prepared_invocation=None)
        stopped = lifecycle._worker_preflight(runner, changed, contract,
            (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
        assert not stopped.ready
        assert any(row.operand_id == contract.task_id and 'complete worker context' in row.reason
            for row in stopped.mismatches)
        store = _store(protected_native_case.plane, contract.expected_parent_contact,
            tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs), prepared_invocation=contract)
        assert store.parent_contacts.read(context.run_id, context.task_id) is None
    finally:
        _close(context)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_protected_e4_begin_stops_when_creating_parent_lifetime_ends(protected_native_case, phase):  # noqa: F811
    runner, context, contract, inputs, store, definition = _ready_store(
        protected_native_case, phase, suffix='retired-creator')
    try:
        original = store.parent_contacts.read(context.run_id, context.task_id)
        store.parent_contacts.retire_live_creator(original)
        assert not store.parent_contacts.is_live_creator(original)
        with pytest.raises(NativeSubworkUncertainContact, match='live creating launch'):
            store.begin(definition)
        assert store.parent_contacts.read(context.run_id, context.task_id) == original
        observed = store.inspect(definition)
        assert observed.state is NativeSubworkState.NOT_ENTERED
        assert observed.begin is None and observed.contact is None
    finally:
        _close(context, store, contract.expected_parent_contact)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_protected_e4_ready_stops_missing_provenance_after_preparation(protected_native_case, phase):
    runner, context, contract, inputs = _invocation(protected_native_case, phase, suffix='missing-provenance')
    try:
        ready(runner, context, contract)
        removed = next(port for port in context.input_ports if port.payload_schema == protected_native_case.source.provenance.SCHEMA)
        missing = replace(context, prepared_invocation=None,
            input_ports=tuple(port for port in context.input_ports if port is not removed),
            input_bindings=tuple(binding for binding in context.input_bindings if binding.artifact_id != removed.artifact_id))
        stopped = lifecycle._worker_preflight(runner, missing, contract,
            (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
        assert not stopped.ready
        assert any(row.operand_id == removed.artifact_id for row in stopped.mismatches)
    finally:
        _close(context)
