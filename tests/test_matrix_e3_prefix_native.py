# SPDX-License-Identifier: MPL-2.0
"""Actual custody with explicitly literal acquisition, never qualified science.

Only the acquisition return is replaced by disclosed constant arrays. No native
integrator, RNG, execution worker, protected issue or genuine source is used.
The actual existing parent/progress/receipt stores exercise the new caller.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_records import ProtectedE3PrefixHistory
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments as segments
from empirical_lawhood.infrastructure.execution import LocalScheduler, prepare_worker_invocation
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from tests.test_matrix_e3_prefix_preparation import _context, _work
from tests.test_matrix_e3_prefix_preparation import case as case, scheduled as scheduled, stock as stock, provenance as provenance  # noqa: F401
from tests.test_matrix_e3_prefix_science_extraction import literal_segment
from tests.test_matrix_scheduled_history_bindings import finish


def blocked(*args, **kwargs):
    raise AssertionError("cold current prefix entered acquisition, stepping or RNG")


def current(case, *, mixed_native_scopes=False):
    selected = _context(case)
    selected.runner = owner.ProtectedE3PrefixRunner()
    selected.capability = selected.runner.manifest
    selected.task = replace(selected.task, capability_implementation_sha256=selected.capability.implementation_sha256)
    selected.parent = replace(selected.parent, execution_task=ObjectIdentity.from_record(selected.task.task_id, selected.task))
    contacts = ExternalNativeEffectContactStore(plane=case.plane, execution_plan=selected.parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if mixed_native_scopes else VisibilityCeiling.PROSPECTIVE,
        outcome_access=OutcomeAccess.EVALUATION_SEALED if mixed_native_scopes else OutcomeAccess.OUTCOME_BLIND,
        task_scopes={selected.task.task_id: (VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND),
            "sealed.future": (VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.EVALUATION_SEALED)}
            if mixed_native_scopes else None)
    contacts.begin(selected.parent)
    selected.contacts = contacts
    selected.native = LocalScheduler._native_subwork_progress(
        SimpleNamespace(artifact_writer=case.plane, native_effect_contact_store=contacts),
        selected.runner, selected.parent, selected.bundle.verified_inputs)
    return selected


def run(selected, *, context=None):
    original = context or getattr(selected, "prepared_context", None)
    if original is None:
        original, _ = bound_current(selected)
    ports = tuple(port.cursor() for port in original.input_ports)
    return selected.runner.execute_with_native_subwork(replace(original, input_ports=ports), selected.native)


def bound_current(selected):
    contract = prepare_worker_invocation(selected.runner, selected.context, selected.bundle.verified_inputs,
        implementation=selected.implementation, execution_plan=selected.parent.execution_plan,
        execution_task=selected.parent.execution_task, execution_task_record=selected.task,
        native_effect=True, native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    selected.native = LocalScheduler._native_subwork_progress(
        SimpleNamespace(artifact_writer=selected.native.plane, native_effect_contact_store=selected.contacts),
        selected.runner, selected.parent, selected.bundle.verified_inputs, prepared_contract=contract)
    selected.prepared_context = replace(selected.context, prepared_invocation=contract)
    return selected.prepared_context, contract


def snapshot(case):
    root = Path(case.plane.root.contract.canonical_path)
    return {str(path.relative_to(root)): (sha256(path.read_bytes()).hexdigest(), path.stat().st_size, path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()}


def literal_acquisition(selected, monkeypatch):
    values = literal_segment(selected.source)
    calls = []

    def deliver(coordinate, streams, start, stop, **kwargs):
        assert (coordinate, streams, start, stop, kwargs) == (selected.source.coordinate,
            selected.source.root.streams, 0, 256, {})
        calls.append("explicit-literal-segment")
        return values

    monkeypatch.setattr(segments, "acquire_parameter_segment", deliver)
    monkeypatch.setattr(parameter_history, "advance_parameter_pair", blocked)
    monkeypatch.setattr(np.random, "Generator", blocked)
    monkeypatch.setattr(np.random, "PCG64DXSM", blocked)
    return calls


def product(result):
    return decode_canonical_bytes(next(output.payload for output in result.outputs
        if output.output_id.endswith(".product")), ProtectedE3PrefixHistory, maximum_bytes=None)


def test_cold_declaration_has_one_native_preparer_and_exact_direct_inputs(monkeypatch):
    monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
    declaration = owner.prefix_declaration()
    registration = declaration.registration()
    assert registration.native_effect and registration.complete_unit_census
    assert registration.native_work_preparer is owner.prepare_native_work
    assert tuple(port.port_id for port in registration.input_ports) == (
        "coordinate", "manifest", "provenance", "source", "specification", "streams")
    assert registration.input_ports[-1].minimum_count == registration.input_ports[-1].maximum_count == 4
    assert tuple(output.output_id for output in registration.outputs) == ("arrays", "checkpoint", "product")
    assert next(port for port in registration.input_ports if port.port_id == "source").payload_schema == sr.ScheduledSource.SCHEMA
    assert sr.ScheduledAllocation.SCHEMA not in {port.payload_schema for port in registration.input_ports}


def test_mixed_native_campaign_keeps_prefix_blind_and_completes_ordinary_parent(case, monkeypatch):
    """Real prefix controller/store plus literal arrays; no native acquisition."""
    selected = current(case, mixed_native_scopes=True)
    try:
        calls = literal_acquisition(selected, monkeypatch)
        context, _ = bound_current(selected)
        result = run(selected, context=context)
        history = product(result)
        history.validate_source(selected.config, case.manifest, specification=case.inputs.specification)
        assert calls == ["explicit-literal-segment"]
        assert selected.native.parent_contacts is selected.contacts.for_task(selected.task.task_id)
        assert selected.native.access is OutcomeAccess.OUTCOME_BLIND
        assert selected.native.visibility is VisibilityCeiling.PROSPECTIVE
        assert selected.contacts.for_task("sealed.future").outcome_access is OutcomeAccess.EVALUATION_SEALED
        assert selected.contacts.is_live_creator(selected.parent)
        parent, _ = finish(case.plane, selected.context, result, selected.source)
        assert parent.task_id == selected.task.task_id != history.native.receipt.task_id
        assert parent.operational_status is history.native.receipt.operational_status is OperationalStatus.SUCCEEDED
        selected.contacts.retire_live_creator(selected.parent)
        assert not selected.native.parent_contacts.is_live_creator(selected.parent)
        before = snapshot(case)
        monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
        assert run(selected, context=context) == result
        assert snapshot(case) == before
    finally:
        for port in selected.context.input_ports:
            port.close()


def test_current_prefix_actual_store_relay_cold_science_and_unchanged_completed_recovery(case, monkeypatch):
    selected = current(case)
    try:
        calls = literal_acquisition(selected, monkeypatch)
        context, contract = bound_current(selected)
        assert contract.native_work == _work(selected, context=context)
        first = run(selected, context=context)
        history = product(first)
        assert calls == ["explicit-literal-segment"]
        assert history.validate_source(selected.config, case.manifest, specification=case.inputs.specification) == selected.source
        receipt, publications = finish(case.plane, selected.context, first, selected.source)
        arrays = next(row for row in publications if row.logical.payload_schema == MATRIX_ARRAY_SCHEMA)
        case.plane.verify_manifest(arrays)
        actual = history.arrays.array_artifact
        assert (actual.artifact_id, actual.sha256, actual.size_bytes, actual.media_type) == (
            arrays.logical.logical_artifact_id, arrays.logical.content_sha256,
            arrays.materialization.size_bytes, arrays.logical.media_type)
        assert arrays.logical.profile is ArtifactProfile.MATRIX_ARRAY_NPZ
        assert actual.artifact_id != history.checkpoint.prefix_arrays.artifact_id
        assert history.checkpoint.prefix_arrays.artifact_id == history.native.receipt.task_id + ".output.arrays"
        assert history.native.receipt.operational_status is receipt.operational_status is OperationalStatus.SUCCEEDED
        assert selected.native.recover(history.native.definition).receipt == history.native.receipt
        raw = next(output.payload for output in first.outputs if output.output_id.endswith(".arrays"))
        assert raw == b"".join(selected.native.iter_completed_output(history.native.definition, "arrays"))
        assert history.checkpoint.canonical_bytes() == b"".join(
            selected.native.iter_completed_output(history.native.definition, "checkpoint"))
        before = snapshot(case)
        monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
        second = run(selected, context=context)
        assert second == first
        assert snapshot(case) == before
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
        # A completed software-native delivery does not make deliberately
        # nonintegrated constant paths satisfy the independent equations.
        keywords = dict(prefix_config=selected.config, manifest=case.manifest, specification=case.inputs.specification)
        numerical = science.assess_prefix(history, raw, **keywords)
        assert not numerical.numerical_pass
        diagnostic_raw, witness = science.measure_prefix(history, numerical, raw, artifact_id="exposed.current.diagnostics", **keywords)
        assessment = science.check_frames(history, numerical, witness, raw, diagnostic_raw, **keywords)
        _, causal = science.causal_delivery(history, numerical, witness, assessment, raw, diagnostic_raw,
            artifact_id="exposed.current.causal", **keywords)
        assert causal.disposition == "UNEVALUABLE"
    finally:
        selected.bundle.close()


@pytest.mark.parametrize("contacted", (False, True))
def test_current_prefix_actual_unfinished_contact_never_reenters_or_changes_custody(case, monkeypatch, contacted):
    selected = current(case)
    try:
        work = _work(selected)
        definition, = work.definitions
        selected.native.freeze_roster(work.rosters[0], definitions=work.definitions)
        entry = selected.native.begin(definition)
        if contacted:
            selected.native.contact(entry)
        before = snapshot(case)
        monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
        monkeypatch.setattr(np.random, "Generator", blocked)
        kind = NativeSubworkUncertainContact if contacted else ValueError
        message = "contacted without exact receipt; no automatic retry" if contacted else "unreceipted/unknown native contact"
        with pytest.raises(kind, match=message):
            run(selected)
        assert snapshot(case) == before
        expected = NativeSubworkState.UNKNOWN_COMPLETION if contacted else NativeSubworkState.BEGUN
        assert selected.native.inspect(definition).state is expected
    finally:
        selected.bundle.close()


def test_current_prefix_actual_failed_return_retains_failed_receipt_and_refuses_retry(case, monkeypatch):
    selected = current(case)
    try:
        def failed(*args, **kwargs):
            raise ValueError("exposed literal acquisition failure")

        monkeypatch.setattr(segments, "acquire_parameter_segment", failed)
        with pytest.raises(ValueError, match="exposed literal acquisition failure"):
            run(selected)
        definition, = _work(selected).definitions
        inspection = selected.native.inspect(definition)
        assert inspection.state is NativeSubworkState.COMPLETED
        assert inspection.receipt.operational_status is OperationalStatus.FAILED
        assert inspection.completion.unknown_streams == definition.streams
        assert inspection.completion.omitted_output_ids == ("arrays", "checkpoint")
        before = snapshot(case)
        monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
        with pytest.raises(ValueError, match="failed/unknown contact replay"):
            run(selected)
        assert snapshot(case) == before
    finally:
        selected.bundle.close()


@pytest.mark.parametrize("member", ("arrays", "checkpoint"))
def test_current_prefix_actual_corrupt_retained_member_refuses_without_new_acquisition(case, monkeypatch, tmp_path, member):
    selected = current(case)
    try:
        literal_acquisition(selected, monkeypatch)
        history = product(run(selected))
        target = next(row for row in history.native.receipt.output_materializations
            if row.logical_artifact_id == history.native.receipt.task_id + ".output." + member)
        path = case.plane.root.resolve(target.relative_path, for_write=False)
        original = path.read_bytes()
        (tmp_path / (member + ".before-corruption")).write_bytes(original)
        path.write_bytes(original[:-1] + bytes((original[-1] ^ 1,)))
        before = snapshot(case)
        monkeypatch.setattr(segments, "acquire_parameter_segment", blocked)
        monkeypatch.setattr(np.random, "Generator", blocked)
        with pytest.raises(ArtifactIdentityConflict, match="artifact bytes differ|artifact changed during its verification scope"):
            run(selected)
        assert snapshot(case) == before
    finally:
        selected.bundle.close()
