# SPDX-License-Identifier: MPL-2.0
"""Public native TRAIN conformance on already exposed test streams.

The numerical source/response adapters, workers, receipts and recovery are real.
The exposure support and reservation chronology are disclosed software fixtures;
this test grants no freshness, sampling qualification or scientific authority.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import shutil

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.api.experiment_preparation import (
    author_prepared_experiment, load_experiment_inputs, load_experiment_specification, prepare_experiment)
from empirical_lawhood.api.recursive_authoring import implementation_binding, load_authored_wave
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.api.native_training_banks import export_native_training_banks
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as records
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding)
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case

ROOT = Path(__file__).resolve().parents[1]


def _copied_preparation(case, directory):
    """Exercise the unchanged copied specification/source front door."""
    directory.mkdir()
    specification_path, request_path = directory / "specification.json", directory / "request.json"
    specification_path.write_bytes(case.specification.canonical_bytes())
    request_path.write_bytes(case.request.canonical_bytes())
    members = []
    for index, (key, value) in enumerate(sorted(case.template_files.items())):
        member = directory / ("template-" + str(index).zfill(3) + ".npz")
        shutil.copyfile(value.path, member)
        members.append(ExperimentFileInputBinding(key, value.identity, value.record_version,
            member.name, value.maximum_bytes))
    selection = ExperimentFileInputSelection("selection.disclosed-native-train", acquisition.PROTOCOL_ID,
        (ExperimentInputBinding("request", case.request.identity, request_path.name, request_path.stat().st_size),), tuple(members))
    selection_path = directory / "sources.json"
    selection_path.write_bytes(selection.canonical_bytes())
    specification = load_experiment_specification(specification_path)
    inputs = load_experiment_inputs(specification, selection_path)
    source = implementation_binding(ROOT)
    execution = ExecutionSelection(4, "environment.disclosed-native-train",
        ObjectIdentity.from_record("recursive-member.implementation", source), case.plane.root.contract.canonical_path)
    prepared = prepare_experiment(specification, scientific_inputs=inputs.scientific_inputs,
        execution=execution, method_inputs=inputs.method_inputs)
    assert prepared.executable, prepared.dependencies
    return prepared


def _actual_case(tmp_path, monkeypatch, *, training_count=1):
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from tests import test_matrix_scheduled_history as source_literals
    from tests import test_matrix_e3_protected_source_records as response_literals
    from tests.test_matrix_scheduled_response_forecast import pauli
    observed = capture_matrix_provenance(project_root=ROOT)
    original_source, encode = source_literals.parameter_template, response_literals.encode_matrix_arrays
    # Reuse the existing declared finite Pauli-complement test instrument. The
    # original zero-template metadata controls remain their original bytes.
    instrument = dict(generic_basis=np.asarray([np.kron(np.eye(2), value) / 2 for value in pauli()], dtype="<c16"),
        force_coefficients=np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        trace_coefficients=np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        receiver_coefficients=np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4))

    def templates(values, **kwargs):
        assert {name: (value.dtype.str, value.shape) for name, value in values.items()} == {
            name: (value.dtype.str, value.shape) for name, value in instrument.items()}
        return encode(instrument, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(source_literals, "parameter_template", lambda: replace(original_source(), provenance=observed))
        patch.setattr(response_literals, "encode_matrix_arrays", templates)
        # This exact already-exposed E3 seed recipe has an AVAILABLE retained
        # paired prefix. These streams must remain excluded from fresh science.
        groups = tuple('group.literal.e3.evaluation.' + str(index).zfill(3) for index in range(training_count))
        case = fresh_training_metadata_case(tmp_path, training_count=training_count,
            exposed_stream_group=groups[0] if training_count == 1 else groups,
            future_namespace="future.disclosed-native-train")
        # FILE-only recheck controls need a separate unpublished copy. The
        # actual census publication and its complete scientific values stay
        # unchanged in the prospective manifest and its prior corpus.
        census = case.request.future_manifest.audit.census
        future_bytes = case.request.future_manifest.canonical_bytes()
        prior_corpus = case.request.future_manifest.audit.prior_corpus
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
        census_artifacts = {artifact for artifact, _ in exposure_support(case.request.future_manifest.audit)}
        assert len(census_artifacts) == 1
        mandatory_publications = records.future_response_support(case.request)
        assert len(mandatory_publications) == 7
        original_handles = tuple(row for row in case.request.exposure_support if row[0] not in census_artifacts)
        support_directory = case.plane.root.resolve('native-file-support', for_write=True)
        support_directory.mkdir()
        supports = []
        copied_names = set()
        for index, (artifact, publication) in enumerate(case.request.exposure_support):
            if artifact not in census_artifacts:
                supports.append((artifact, publication))
                continue
            original = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
            raw = original.read_bytes()
            assert raw == census.canonical_bytes()
            assert (artifact.sha256, artifact.size_bytes) == (sha256(raw).hexdigest(), len(raw))
            assert artifact.payload_schema == census.SCHEMA
            actual = decode_canonical_bytes(raw, type(census), maximum_bytes=len(raw))
            assert actual == census
            manifest = case.plane.read_manifest(publication.materialization.relative_path)
            case.plane.verify_manifest(manifest)
            assert (manifest.logical, manifest.materialization) == (publication.logical, publication.materialization)
            sidecar = case.plane.root.resolve(publication.manifest_materialization.relative_path, for_write=False)
            sidecar_raw = sidecar.read_bytes()
            assert sha256(sidecar_raw).hexdigest() == publication.manifest_materialization.physical_sha256
            marker = case.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
            marker_raw = marker.read_bytes()
            assert sha256(marker_raw).hexdigest() == manifest.publication.commit_marker_sha256
            relative = 'native-file-support/exposure-' + str(index).zfill(3) + '.json'
            copied_names.add(Path(relative).name)
            copied = case.plane.root.resolve(relative, for_write=True)
            shutil.copyfile(original, copied)
            assert copied.read_bytes() == raw and copied.stat().st_size == artifact.size_bytes
            assert sha256(copied.read_bytes()).hexdigest() == artifact.sha256
            assert not Path(str(copied) + '.manifest.json').exists()
            assert original.read_bytes() == raw
            assert sidecar.read_bytes() == sidecar_raw and marker.read_bytes() == marker_raw
            supports.append((artifact, ExperimentFileInputBinding('file.' + artifact.artifact_id,
                artifact, actual.VERSION, relative, artifact.size_bytes)))
        assert len(copied_names) == 1
        assert {path.name for path in support_directory.iterdir()} == copied_names
        assert not (support_directory / '.publication-batches').exists()
        case.request = replace(case.request, exposure_support=tuple(supports))
        assert tuple(row for row in case.request.exposure_support if row[0] not in census_artifacts) == original_handles
        assert records.future_response_support(case.request) == mandatory_publications
        assert case.request.future_manifest.canonical_bytes() == future_bytes
        assert case.request.future_manifest.audit.prior_corpus == prior_corpus
        case.acquisition = records.acquisition_seal(case.specification, case.request)
        return case


@pytest.mark.native
def test_public_native_train_author_run_read_export_and_zero_executor_recovery(tmp_path, monkeypatch):
    from tests.test_matrix_native_training_parent_preflight import observe_native_preflight_controls
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings
    ready_phases = observe_native_preflight_controls(monkeypatch, native_training_bindings)
    with threadpool_limits(limits=1):
        case = _actual_case(tmp_path, monkeypatch)
        preparation = _copied_preparation(case, tmp_path / "copied")
        directory = Path(case.plane.root.contract.canonical_path) / "native-training-authored"
        authored = author_prepared_experiment(preparation=preparation, project_root=ROOT,
            artifact_writer=case.plane, output_dir=directory)
        assert authored["task_count"] == 11 and authored["native_contact"] == "none"
        service = ExperimentProgrammeService(ROOT, case.plane)
        report = service.run(directory=directory, maximum_parallel_tasks=4)
        assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 2
        assert ready_phases == ['prefix', 'responses']
        retained, products, actual_draft, actual_plan = read_recursive_wave(directory=directory, artifact_writer=case.plane, include_products=True)
        def product(phase, kind):
            task = acquisition.task_id(case.source.root_id, phase)
            row, = (value for value in products["records"][task].values() if type(value) is kind)
            return row
        from tests.matrix_native_acquisition_replay_controls import assert_actual_replay_rejects_changed_records
        assert_actual_replay_rejects_changed_records(case=case, products=products, draft=actual_draft,
            plan=actual_plan, training=True, monkeypatch=monkeypatch)
        causal = product("project", records.NativeTrainingCausalPrefix)
        responses = product("responses", records.NativeTrainingResponse)
        assert retained["scientific_result"]["scientific_completion"] == "COMPLETE_NATIVE_TRAIN_ARRAY_REPLAY"
        assert causal.disposition == "AVAILABLE" and responses.disposition == "COMPLETED"
        assert len(responses.native) == 1 and len(responses.branch_ids) == 48
        exported = export_native_training_banks(directory=directory, artifact_writer=case.plane,
            output_directory=Path(case.plane.root.contract.canonical_path) / "native-training-banks",
            record_id="banks.disclosed-native-train")
        assert exported.allocation == preparation.allocation
        assert exported.acquisition == case.acquisition
        from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
        authenticate_published_materialization(case.plane, exported.acquisition_publication)
        assert exported.acquisition_publication.logical.content_sha256 == exported.acquisition.fingerprint()
        assert exported.acquisition.candidate == case.request.candidate_specification.identity
        assert len(exported.publications) == 3
        assert len(exported.features.rows) == len(exported.outcomes.rows) == 1
        assert exported.features.rows[0].disposition == "AVAILABLE"
        assert exported.features.rows[0].origin == causal.identity
        assert retained["scientific_authority"] == "NONE" and retained["qualification"] == "NOT_ESTABLISHED"
        for value in (exported.features, exported.outcomes):
            assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value

        # The installed generic public export transition reuses those exact
        # publications; it must not schedule any additional native task.
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_exports import NativeTrainingBankExportSelection
        from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
        from empirical_lawhood.api.recursive_execution import _retained_plans
        packet, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=case.plane, lazy_payloads=True)
        run, plan, _ = _retained_plans(payloads, draft)
        locator = MatrixFiniteDtTrainingLocator(directory.relative_to(case.plane.root.contract.canonical_path).as_posix(),
            run.run_plan_id, ObjectIdentity.from_record(packet.packet_id, packet),
            ObjectIdentity.from_record(plan.execution_plan_id, plan))
        from types import SimpleNamespace
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_primary_amendment import MatrixE3PrimaryFamilyAmendment
        from empirical_lawhood.api.configured_e3_primary_amendment import _entry_product
        family=tuple(sorted((*case.request.candidate_specification.assessment.comparison_ids,'e1.recurrence-survival','e2.utility')))
        amended=replace(case.request.candidate_specification.assessment,alpha_denominator=280,comparison_ids=family)
        amendment=MatrixE3PrimaryFamilyAmendment('amendment.actual-exposed-native-control',case.request.candidate_specification,
            amended,case.request.identity,case.specification.identity)
        assert _entry_product(case.plane,SimpleNamespace(native_training_locator=locator,entry_receipt=exported.acquisition_receipt,
            amendment=amendment,acquisition_publication=exported.acquisition_publication))==exported.acquisition
        selection = NativeTrainingBankExportSelection('export.disclosed-native-train',
            'banks.disclosed-native-train', 'native-training-banks')
        selection_path = tmp_path / 'export-selection.json'
        selection_path.write_bytes(selection.canonical_bytes())
        exported_report = service.export_products(directory=directory, selection_path=selection_path)
        assert exported_report['native_training_locator'] == locator.to_document()
        assert exported_report['features'] == exported.features.identity.to_document()
        assert exported_report['outcomes'] == exported.outcomes.identity.to_document()
        assert exported_report['native_contact'] == 'NONE'
        assert exported_report['scientific_qualification'] == 'NOT_ESTABLISHED'
        assert all(not value['value']['created'] for value in exported_report['publications'])
        with pytest.raises(PermissionError, match='original authored packet'):
            export_native_training_banks(directory=directory, artifact_writer=case.plane,
                output_directory=Path(case.plane.root.contract.canonical_path) / 'native-training-banks',
                record_id='banks.disclosed-native-train',
                expected_locator=replace(locator, run_id='run.unexecuted-substitution'))

        _assert_actual_native_training_instrument_certificate(case, directory, products, monkeypatch)

        def forbidden(*args, **kwargs):
            raise AssertionError("completed native TRAIN recovery entered an executor")
        monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
        recovered = service.recover(directory=directory, maximum_parallel_tasks=4)
        assert recovered == {**report, "native_contact": "none", "new_native_contact_count": 0}
        assert read_recursive_wave(directory=directory, artifact_writer=case.plane) == retained


@pytest.mark.held
def test_full64_native_training_public_author_load_remains_bounded_and_effect_free(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as bindings
    def forbidden(*args, **kwargs):
        raise AssertionError("full64 metadata preparation entered native work")
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    case = fresh_training_metadata_case(tmp_path, training_count=64)
    preparation = _copied_preparation(case, tmp_path / "copied")
    directory = Path(case.plane.root.contract.canonical_path) / "full64-native-training-authored"
    report = author_prepared_experiment(preparation=preparation, project_root=ROOT,
        artifact_writer=case.plane, output_dir=directory)
    assert report["task_count"] == 578 and report["native_contact"] == "none"
    _, draft, _, _ = load_authored_wave(directory=directory, artifact_writer=case.plane)
    assert draft == preparation.draft and len(draft.selected_operation_ids) == 578
    assert preparation.census.native_effect_count == 128


def _assert_actual_native_training_instrument_certificate(case, directory, products, monkeypatch):
    """Reuse the real completed run; only the future-bank admission is disclosed.

    This control does not build/admit an E4 source bank or confer freshness.
    Every TRAIN source, plan, receipt, control and native evidence remains real.
    """
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as finite
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank
    from empirical_lawhood.api import matrix_finite_dt_source_runtime as runtime
    from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff

    packet, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=case.plane, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    locator = finite.MatrixFiniteDtTrainingLocator(directory.relative_to(case.plane.root.contract.canonical_path).as_posix(),
        run.run_plan_id, ObjectIdentity.from_record(packet.packet_id, packet),
        ObjectIdentity.from_record(plan.execution_plan_id, plan))
    cutoff = InformationCutoff("cutoff.disclosed-future-instrument", case.source.root.root.clock_id,
        CausalPhase.PRE_ACTION, case.source.coordinate.physical_time(case.source.policy.cutoff_tick))
    # A typed disclosed pin scopes this internal projection only. Public
    # certify_native_training_instrument independently authenticates a real bank.
    future_bank = ObjectIdentity("bank.disclosed-future-instrument", SelectedE4PhaseBank.SCHEMA,
        SelectedE4PhaseBank.VERSION, "1" * 64)
    arguments = dict(locator=locator, future_bank=future_bank,
        future_group_ids=("group.disclosed-future-instrument",),
        original_future_reservation=case.request.future_manifest.reservation, cutoff=cutoff,
        record_id="certificate.disclosed-native-instrument", expected_census=case.request.future_manifest.audit.census)
    certificate = runtime._certify_native_training_instrument(writer=case.plane, **arguments)
    assert len(certificate.controls) == 1
    control, = certificate.controls
    score_task = acquisition.task_id(case.source.root_id, "response-score")
    score, = (value for value in products["records"][score_task].values() if type(value) is records.NativeTrainingScore)
    assert (control.source, control.group_id, control.response_controls_pass, control.response_control_count) == (
        records.identity(case.source), case.source.root.root.independent_group_id, score.numerical_pass, len(score.controls))
    assert control.response_disposition == "COMPLETED" and control.response_control_count == 48
    assert len(control.receipts) == len(records.PHASES) + 1
    assert {value.object_fingerprint for value in control.receipts}.issubset(
        {value.fingerprint() for value in products["receipts"].values()})
    assert certificate.instrument_sha256 == finite.instrument_signature(case.request.protocols[0])
    assert certificate.standing == finite.STANDING
    for altered in (replace(locator, packet=replace(locator.packet, object_fingerprint="2" * 64)),
            replace(locator, run_id=locator.run_id + ".substituted")):
        with pytest.raises(PermissionError, match="substitutes original TRAIN"):
            runtime._certify_native_training_instrument(writer=case.plane, **{**arguments, "locator": altered})

    original_read = runtime._read_recursive_wave_with_roots
    reads = []
    def actual_read(**kwargs):
        reads.append(kwargs["directory"])
        return original_read(**kwargs)
    def disclosed_bank_boundary(**kwargs):
        assert kwargs["programme"] is case.specification and kwargs["bank"] is case.request
        assert kwargs["original_future_reservation"] == arguments["original_future_reservation"]
        return runtime._certify_native_training_instrument(writer=kwargs["writer"],
            **{**arguments, "cutoff": kwargs["cutoff"], "record_id": kwargs["record_id"]})
    with monkeypatch.context() as patch:
        patch.setattr(runtime, "_read_recursive_wave_with_roots", actual_read)
        # The public real-E4-bank admission is the sole disclosed seam; its
        # completed TRAIN verification executes unchanged on the actual run.
        patch.setattr(runtime, "certify_native_training_instrument", disclosed_bank_boundary)
        operands = dict(certificate=certificate, programme=case.specification, bank=case.request,
            original_future_reservation=arguments["original_future_reservation"])
        with case.plane.verification_scope() as writer:
            reader = CurrentResultPlanReader(writer)
            runtime.authenticate_instrument_certificate(writer=writer, control_reader=reader, **operands)
            runtime.authenticate_instrument_certificate(writer=writer, control_reader=reader, **operands)
            assert len(reads) == 1
            altered = replace(certificate, controls=(replace(control,
                prefix_controls_pass=not control.prefix_controls_pass),))
            with pytest.raises(PermissionError, match="caller-asserted, altered or incomplete"):
                runtime.authenticate_instrument_certificate(writer=writer, control_reader=reader,
                    **{**operands, "certificate": altered})
            assert len(reads) == 1
            artifact, file_input = case.request.exposure_support[0]
            support_path = case.plane.root.resolve(file_input.relative_path, for_write=False)
            support_raw = support_path.read_bytes()
            try:
                support_path.write_bytes(b"x" * artifact.size_bytes)
                # This raw FILE has no artifact publication snapshot. Both an
                # actual warm certificate and ordinary reconstruction must
                # authenticate its bytes, not reuse the prior positive result.
                with pytest.raises(ValueError, match="FILE differs"):
                    runtime.authenticate_instrument_certificate(writer=writer, control_reader=reader, **operands)
                with pytest.raises(ValueError, match="FILE differs"):
                    runtime.authenticate_instrument_certificate(writer=writer, **operands)
                assert len(reads) == 1
            finally:
                support_path.write_bytes(support_raw)
            before_late_change = len(reads)
            def change_after_reconstruction(**kwargs):
                result = disclosed_bank_boundary(**kwargs)
                support_path.write_bytes(b"x" * artifact.size_bytes)
                return result
            try:
                with monkeypatch.context() as late:
                    late.setattr(runtime, "certify_native_training_instrument", change_after_reconstruction)
                    with pytest.raises(ValueError, match="FILE differs"):
                        runtime.authenticate_instrument_certificate(writer=writer, **operands)
                assert len(reads) == before_late_change + 1
            finally:
                support_path.write_bytes(support_raw)
        with pytest.raises(ArtifactIdentityConflict, match="scope has ended"):
            runtime.authenticate_instrument_certificate(writer=reader.writer, control_reader=reader, **operands)
        # Reuse must notice actual retained-byte replacement, even when the
        # caller supplies the same certificate and immutable selection pins.
        prefix_task = acquisition.task_id(case.source.root_id, "prefix")
        prefix_receipt = products["receipts"][prefix_task]
        logical, = (value for value in prefix_receipt.output_logical_artifacts
            if value.payload_schema == records.NativeTrainingPrefixHistory.SCHEMA)
        material, = (value for value in prefix_receipt.output_materializations
            if value.logical_artifact_id == logical.logical_artifact_id)
        path = case.plane.root.resolve(material.relative_path, for_write=False)
        raw = path.read_bytes()
        try:
            with pytest.raises(ArtifactIdentityConflict, match="changed|replaced"):
                with case.plane.verification_scope() as writer:
                    reader = CurrentResultPlanReader(writer)
                    runtime.authenticate_instrument_certificate(writer=writer, control_reader=reader, **operands)
                    path.write_bytes(raw + b"\n")
                    runtime.authenticate_instrument_certificate(writer=writer, control_reader=reader, **operands)
        finally:
            path.write_bytes(raw)
        assert len(reads) == 3
