# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Selected response nonuse retains potential work without entering a child.

The existing pure source fixtures and literal received-array/native metadata
below are disclosed software premises. No native producer, contact, issue,
qualification or favorable scientific observation is manufactured or executed.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as common
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_native as development
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as dev_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_execution as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import array_product
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import PREDICTORS, branch_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source, selected_stream_operands
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import ParameterGeneratorState
from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity
from empirical_lawhood.runtime.native_subwork import NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.native_completion_fixtures import literal_completion, receipt_with_completion
from tests.test_matrix_e4_entry_source_identity import _case as development_prefix
from tests.test_matrix_e4_protected_entry_source_identity import _prefix_case as protected_prefix
from tests.test_matrix_selected_e3_e4_workers import invocation as development_invocation
from tests.test_matrix_selected_e4_native_workers import _invocation as protected_invocation
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision  # noqa: F401


def pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("response metadata/nonuse control entered a native effect")
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments, parameter_source
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    for owner, names in ((development, ("execute_parameter_native_work", "execute_paired_response_native_work")),
            (protected, ("execute_parameter_native_work", "execute_paired_response_native_work")),
            (parameter_history_segments, ("acquire_parameter_segment",)),
            (parameter_source, ("acquire_parameter_history",)),
            (ExternalNativeEffectContactStore, ("begin",)), (ExternalNativeSubworkStore, ("begin", "contact")),
            (lifecycle.LocalProcessExecutor, ("execute", "execute_deadline_free"))):
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)


def implementation(provenance):
    return RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, False)


def literal_prefix(module, kinds, config, source, context, *, prefix_arrays=None):
    """Exact typed custody premises for literal arrays, never producer evidence."""
    initial = replace(context.prepared_invocation, implementation=implementation(source.provenance))
    context = replace(context, prepared_invocation=initial)
    work = module.initial_native_work(context, config, {"provenance": source.provenance}, {}, initial.expected_parent_contact)
    definition, = work.definitions
    child = "native-subwork." + sha256((context.task_id + ":" + definition.subwork_id).encode()).hexdigest()
    access, visibility = ((OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
        if module is development else (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science, selected_e4_native_science
    science = selected_e3_e4_science if module is development else selected_e4_native_science
    values = {"literal": np.zeros(1, dtype="<f8")} if prefix_arrays is None else prefix_arrays
    raw, operand = science.array_product(source, values, role="PREFIX",
        artifact_id=child + ".output.arrays", producers=(common.identity(source),))
    tick = source.policy.cutoff_tick
    checkpoint = common.ScheduledCheckpoint("checkpoint.response-nonentry", common.identity(source),
        common.coordinate_identity(source.coordinate), tick, operand.array_artifact,
        tuple(ParameterGeneratorState(stream.purpose, stream.effective_seed, 0, 1, 0, 0,
            min(tick, source.coordinate.ramp_ticks) if stream.purpose.startswith("preparation")
            else max(0, tick - source.coordinate.ramp_ticks)) for stream in source.root.streams))
    logicals, physicals = [], []
    for output, value, profile, media in (("arrays", raw, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
            ("checkpoint", checkpoint, ArtifactProfile.CANONICAL_JSON, "application/json")):
        payload = value if type(value) is bytes else value.canonical_bytes()
        schema = operand.array_artifact.payload_schema if type(value) is bytes else value.SCHEMA
        name = child + ".output." + output
        digest = sha256(payload).hexdigest()
        logicals.append(LogicalArtifactIdentity(name, digest, schema, profile, media, visibility, (), access,
            ArtifactGenericValidation("validator.literal-response-nonentry", "1.0.0", "a" * 64, schema, profile)))
        physicals.append(ArtifactMaterialization("material." + name, name, "storage.literal-unpublished",
            "unpublished/" + name, digest, len(payload), "none"))
    receipt = CanonicalTaskReceipt("receipt." + child, context.run_id, child,
        context.run_id + "." + child + ".attempt-001", source.provenance.observed_git_head,
        context.input_materialization_ids, tuple(sorted(physicals, key=lambda row: row.materialization_id)),
        tuple(sorted(logicals, key=lambda row: row.logical_artifact_id)), (), OperationalStatus.SUCCEEDED, ())
    contact = NativeSubworkContact(pin("begin.literal-response-nonentry", NativeSubworkBegin))
    consumed = tuple(sorted((source.root.stream_identity(stream) for stream in source.root.streams
        if stream.purpose.startswith("preparation") or tick > source.coordinate.ramp_ticks), key=lambda row: row.object_id))
    completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record("contact.literal-response-nonentry", contact),
        OperationalStatus.SUCCEEDED, ("arrays", "checkpoint"), (), consumed,
        tuple(row for row in definition.streams if row not in consumed), (), InquiryCost(None, None, None),
        "Literal unpublished software metadata; no native producer/contact or qualification", None, ())
    receipt = receipt_with_completion(receipt, literal_completion(completion, child, visibility=visibility, access=access))
    history = kinds[0]("prefix.response-nonentry", common.identity(source), operand, checkpoint,
        common.ScheduledNativeEvidence(definition, completion, receipt))
    history.validate_source(source, config=config)
    return history, raw


def response_case(fixture, population, causal_disposition, mechanical_disposition):
    if population == "development":
        config, local, entry, _, context = development_prefix(fixture)
        module, records, invoke = development, dev_records, development_invocation
        kinds = (records.SelectedE3E4PrefixHistory, records.SelectedE3E4CausalPrefix,
            records.SelectedE3E4NumericalAssessment, records.SelectedE3E4Witness, records.SelectedE3E4Frames,
            records.SelectedE3E4Feature, records.SelectedE3E4MechanicalForecast)
        from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as bindings
    else:
        _, config, local, entry, _, context = protected_prefix(fixture)
        module, records, invoke = protected, protected_records, protected_invocation
        kinds = (records.SelectedE4ProtectedPrefixHistory, records.SelectedE4ProtectedCausalPrefix,
            records.SelectedE4ProtectedNumericalAssessment, records.SelectedE4ProtectedWitness, records.SelectedE4ProtectedFrames,
            records.SelectedE4ProtectedFeature, records.SelectedE4ProtectedMechanicalForecast)
        from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as bindings
    try:
        entry_producer, = (row.task_id for row in context.dependency_receipts)
        provenance = next(value for value in (fixture.bank.provenances if population == "development"
            else fixture.populations.calibration_bank.provenances) if value.identity == local.provenance)
        source = bind_selected_native_source(local, provenance)
        history, prefix_raw = literal_prefix(module, kinds, config, source, context)
    finally:
        for port in context.input_ports:
            port.close()
    causal_arrays = replace(history.arrays, operand_id="arrays.literal-causal", role="CAUSAL_STATE")
    available = causal_disposition == "AVAILABLE"
    causal = kinds[1]("causal.response-nonentry", common.identity(source), common.identity(history),
        pin("numerical.response-nonentry", kinds[2]), pin("witness.response-nonentry", kinds[3]),
        pin("frames.response-nonentry", kinds[4]), common.identity(source.policy), source.root.root, source.policy.cutoff_tick,
        "f" * 64 if available else None, causal_disposition, None if available else "DISCLOSED_SOFTWARE_NONUSE", causal_arrays)
    feature = kinds[5]("feature.response-nonentry", common.identity(source), common.identity(causal), source.root_id,
        source.root.root.independent_group_id, FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id,
        source.coordinate.physical_time(source.policy.cutoff_tick), causal.frame_sha256,
        "AVAILABLE" if available else "NO_CAUSAL_ORIGIN", tuple((name, Decimal(0)) for name in FEATURES) if available else ())
    points = tuple((name, (Decimal(0) if available else None,) * 15) for name in METHODS)
    if population == "development":
        package = fixture.bank.forecast_design.package
        account = records.SelectedE3E4AccountSeal("account.response-nonentry", fixture.bank.forecast_design.identity,
            common.identity(source), common.identity(causal), feature, package.original_package, package.calibration, points)
    else:
        revision = selected_e4_native_science._forecast_public_source(config.models, config.programme, config.source.public,
            record_id="revision." + source.root_id)
        account = records.SelectedE4ProtectedAccountSeal("account.response-nonentry", entry.forecast_design,
            common.identity(source), common.identity(causal), feature, config.original_summary.original_package,
            config.original_summary.calibration, config.original_summary, points, revision, config.decision.identity, None)
    config = module.phase_config(config, "responses")
    access, visibility = ((OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
        if population == "development" else (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE))
    mechanical_raw, mechanical_arrays = array_product(config.protocol, {"literal": np.zeros(1, dtype="<f8")}, role="FORECAST",
        artifact_id="array.literal-mechanical", producers=(common.identity(source),), access=access, visibility=visibility)
    mechanical = kinds[6]("mechanical.response-nonentry", common.identity(source), common.identity(causal),
        ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol),
        ObjectIdentity.from_record(config.protocol.mechanical_model.model_id, config.protocol.mechanical_model),
        causal.frame_sha256, mechanical_arrays, mechanical_disposition,
        tuple((view, predictor, "AVAILABLE" if mechanical_disposition == "AVAILABLE" else "UNRESOLVED",
            None if mechanical_disposition == "AVAILABLE" else "DISCLOSED_SOFTWARE_NONUSE")
            for view in ("PRIMARY", "FINE") for predictor in PREDICTORS))
    values = {"entry": entry, "source": local, "provenance": provenance, "prefix": history,
        "checkpoint": history.checkpoint, "causal": causal,
        "account": account, "mechanical": mechanical, "prefix-arrays": prefix_raw, "mechanical-arrays": mechanical_raw,
        **{"streams." + str(index): value for index, (_, value) in enumerate(
            selected_stream_operands(local, config.panels, include_future=True))}}
    producers = {name: bindings.local_node(source.root_id, phase) for name, phase in (
        ("prefix", "prefix"), ("prefix-arrays", "prefix"), ("checkpoint", "prefix"), ("causal", "project"),
        ("account", "account"), ("mechanical", "mechanical"), ("mechanical-arrays", "mechanical"))}
    producers["entry"] = entry_producer
    runner, context = invoke(config, values, producers)
    # The shared literal helper defaults canonical outputs to `.product`.
    # Freeze this actual prefix companion under its distinct checkpoint port.
    task = context.prepared_invocation.execution_task_record
    task = replace(task, scientific_inputs=tuple(replace(edge,
        producer_output_id=bindings.local_node(source.root_id, "prefix") + ".checkpoint")
        if edge.consumer_input_id == "checkpoint" else edge for edge in task.scientific_inputs))
    initial = replace(context.prepared_invocation, native_effect=True, implementation=implementation(provenance),
        execution_task_record=task, execution_task=ObjectIdentity.from_record(task.task_id, task))
    context = replace(context, prepared_invocation=initial)
    return SimpleNamespace(module=module, config=config, records=values, runner=runner, context=context, bindings=bindings)


@pytest.mark.parametrize("population", ("development", "protected"))
@pytest.mark.parametrize("causal,mechanical,expected", (("NO_ORIGIN", "NO_ORIGIN", "NO_ORIGIN"),
    ("UNEVALUABLE", "UNEVALUABLE", "UNEVALUABLE"), ("AVAILABLE", "INSTRUMENT_UNRESOLVED", "INSTRUMENT_UNRESOLVED")))
def test_adverse_responses_keep_exact_potential_work_and_all48_unentered_branches(
        selected_bridge, selected_revision, population, causal, mechanical, expected):
    case = response_case(selected_bridge if population == "development" else selected_revision, population, causal, mechanical)
    try:
        work = lifecycle._prepare_native_work(case.bindings.prepare_native_work, case.runner, case.context,
            case.context.prepared_invocation.expected_parent_contact)
        definition, = work.definitions
        assert len(work.rosters) == 1 and work.rosters[0].subworks == (definition.identity,)
        assert len(definition.streams) == 8 and work.native_effect_slot_ids == ("responses." + case.config.source.root_id,)
        assert callable(case.runner.execute_with_native_subwork)
        store = SimpleNamespace(parent_contact=work.expected_parent)
        raw, product = case.module.execute_native(case.context, case.config, case.records, {}, store,
            artifact_id="arrays.nonentry-result", prepared_arrays=({}, {}))
        assert product.disposition == expected and product.native == ()
        assert len(product.branch_ids) == len(branch_census(case.config.protocol, case.config.panels)) == 48
        values = decode_canonical_bytes(product.canonical_bytes(), type(product), maximum_bytes=None)
        assert values == product and product.reason_codes == ("complete48-pulse-slots-not-entered-" + expected.lower(),)
        from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
        assert np.array_equal(decode_matrix_arrays(raw, product.arrays)["unentered_branches"], np.arange(48, dtype="<i8"))
    finally:
        for port in case.context.input_ports:
            port.close()


@pytest.mark.parametrize("population", ("development", "protected"))
def test_available_responses_keep_full_native_eligibility_without_entering_it(selected_bridge, selected_revision, population, monkeypatch):
    case = response_case(selected_bridge if population == "development" else selected_revision, population, "AVAILABLE", "AVAILABLE")
    try:
        work = lifecycle._prepare_native_work(case.bindings.prepare_native_work, case.runner, case.context,
            case.context.prepared_invocation.expected_parent_contact)
        definition, = work.definitions
        assert definition.parent_contact == work.expected_parent
        assert definition.configuration == ObjectIdentity.from_record(case.config.config_id, case.config)
        assert len(definition.streams) == 8 and len(work.scientific_unit_ids) == 1
        assert work.rosters[0].subworks == (definition.identity,)
        class EligibleNativeBoundary(Exception):
            pass
        def selected_native(source, actual, store, **_kwargs):
            assert actual == work and store.parent_contact == work.expected_parent
            assert source.reference.identity == case.config.source.descriptor.identity
            raise EligibleNativeBoundary
        monkeypatch.setattr(case.module, "execute_paired_response_native_work", selected_native)
        with pytest.raises(EligibleNativeBoundary):
            case.module.execute_native(case.context, case.config, case.records, {},
                SimpleNamespace(parent_contact=work.expected_parent), artifact_id="arrays.eligible-result", prepared_arrays=({}, {}))
    finally:
        for port in case.context.input_ports:
            port.close()


@pytest.mark.parametrize("population", ("development", "protected"))
def test_response_potential_work_refuses_foreign_source_before_any_contact(selected_bridge, selected_revision, population):
    case = response_case(selected_bridge if population == "development" else selected_revision, population, "NO_ORIGIN", "NO_ORIGIN")
    try:
        foreign_source = replace(case.records["mechanical"].source, object_fingerprint="f" * 64)
        foreign = replace(case.records["mechanical"], source=foreign_source,
            arrays=replace(case.records["mechanical"].arrays, source=foreign_source))
        with pytest.raises(ValueError, match="forecast-before-future chain"):
            case.module.initial_native_work(case.context, case.config,
                {**case.records, "mechanical": foreign}, {}, case.context.prepared_invocation.expected_parent_contact)
    finally:
        for port in case.context.input_ports:
            port.close()


@pytest.mark.parametrize("population", ("development", "protected"))
def test_shared_native_guard_still_refuses_empty_initial_nested_work(selected_bridge, selected_revision, population):
    case = response_case(selected_bridge if population == "development" else selected_revision, population, "NO_ORIGIN", "NO_ORIGIN")
    try:
        def empty_work(*, runner, context, expected_parent):
            actual = case.bindings.prepare_native_work(runner=runner, context=context, expected_parent=expected_parent)
            return replace(actual, definitions=(), rosters=())
        with pytest.raises(ValueError, match="ordinary versus initial nested work applicability"):
            lifecycle._prepare_native_work(empty_work, case.runner, case.context,
                case.context.prepared_invocation.expected_parent_contact)
    finally:
        for port in case.context.input_ports:
            port.close()
