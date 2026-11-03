# SPDX-License-Identifier: MPL-2.0
"""Actual installed source lifecycle over retained exposed native TRAIN custody.

The future bank, scientific framing and authority registrations are explicit
TEST controls. No native TRAIN is acquired or fit again. Actual source transform,
independent predicates, issue/worker/read custody and recovery are production
owners; global qualification, sampling and transport remain NOT_ESTABLISHED.
"""
from dataclasses import replace
import json
import os
from pathlib import Path
from threading import get_ident
from types import SimpleNamespace

import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_experiment as domain
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as records
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import selected_public_package_types
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.api.experiment_preparation import (
    load_experiment_inputs, load_experiment_specification, prepare_experiment)
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_finite_dt_source_runtime import certify_native_training_instrument
from empirical_lawhood.api.native_training_banks import _read_instance
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import _retained_plans
from empirical_lawhood.api.recursive_prospective_authoring import prove_recursive_prospective_handoff
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputSelection, ExperimentInputBinding)
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile, resolve_external_root_contract
from tests.test_matrix_finite_dt_source_production import future_case, source_case

ROOT = Path(__file__).resolve().parents[1]


def _retained_native_inputs():
    variables = ("EL_NATIVE_TRAIN_AUTHORED_DIRECTORY", "EL_NATIVE_TRAIN_ROOT_CONTRACT",
        "EL_FINITE_DT_DISCLOSED_PUBLIC_PACKAGE", "EL_TEST_OPERATOR_PROFILE")
    missing = tuple(name for name in variables if name not in os.environ)
    if missing:
        pytest.skip("select retained exposed source controls: " + ", ".join(missing))
    directory, root_path, package_path, profile_path = (Path(os.environ[name]).resolve(strict=True) for name in variables)
    raw = root_path.read_bytes()
    original_contract = decode_canonical_bytes(raw, ExternalRootContract, maximum_bytes=len(raw))
    raw = profile_path.read_bytes()
    original_profile = decode_canonical_bytes(raw, OperatorStorageProfile, maximum_bytes=len(raw))
    root = Path(original_contract.canonical_path)
    assert root.is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    assert directory.is_relative_to(root) and original_profile.maximum_parallel_tasks >= 4
    profile = replace(original_profile, profile_id="operator.disclosed-finite-dt-source",
        external_root_locator=str(root.parent), artifact_namespace=root.name,
        scientific_scratch_namespace=root.name + ".finite-dt-scientific-scratch", maximum_parallel_tasks=4)
    arguments = dict(repo_root=ROOT, home_root=Path.home())
    contract = resolve_external_root_contract(profile, **arguments)
    contract = replace(contract, storage_root_id=original_contract.storage_root_id, logical_name=original_contract.logical_name)
    contract = resolve_external_root_contract(profile, selected_contract=contract, **arguments)
    writer = ExternalArtifactPlane(GuardedExternalRoot(contract),
        validators=ArtifactProfileValidatorRegistry(binary_codecs=MATRIX_STORAGE_CODECS))
    writer.root.verify(for_write=True)
    packet, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer, lazy_payloads=True)
    _, request, _ = _read_instance(payloads)
    run, plan, _ = _retained_plans(payloads, draft)
    locator = records.MatrixFiniteDtTrainingLocator(directory.relative_to(root).as_posix(), run.run_plan_id,
        ObjectIdentity.from_record(packet.packet_id, packet), ObjectIdentity.from_record(plan.execution_plan_id, plan))
    raw = package_path.read_bytes()
    document = json.loads(raw)
    kind, = (value for value in selected_public_package_types()
        if (value.SCHEMA, value.VERSION) == (document["schema"], document["version"]))
    package = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    assert package.canonical_bytes() == raw
    return SimpleNamespace(writer=writer, profile=profile, request=request, locator=locator, public_package=package)


def _copied_source_preparation(case, output):
    directory = output / "copied"
    directory.mkdir()
    specification_path = directory / "specification.json"
    source_path = directory / "selection.json"
    specification_path.write_bytes(case.specification.canonical_bytes())
    source_path.write_bytes(case.selection.canonical_bytes())
    sources = ExperimentFileInputSelection("sources." + case.future.namespace, domain.PROTOCOL_ID,
        (ExperimentInputBinding("selection", case.selection.identity, source_path.name, source_path.stat().st_size),), ())
    sources_path = directory / "sources.json"
    sources_path.write_bytes(sources.canonical_bytes())
    specification = load_experiment_specification(specification_path)
    inputs = load_experiment_inputs(specification, sources_path)
    preparation = prepare_experiment(specification, scientific_inputs=inputs.scientific_inputs,
        execution=case.preparation.execution, method_inputs=inputs.method_inputs)
    assert preparation == case.preparation and preparation.executable
    assert preparation.census.native_effect_count == 0 and len(preparation.draft.operations) == 9
    return preparation


@pytest.mark.held
def test_retained_native_train_source_public_nine_pure_workers_and_zero_executor_recovery(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings
    from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest, RunCampaignRequest
    from tests.matrix_selected_source_predecessor import _sdk_execution
    from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff
    from tests.runtime_platform.test_study_issue import _issue_api_fixture
    from tests.test_matrix_selected_e4_public_programme import NeverExecute, observer_proof

    assert tmp_path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    def forbidden(*_args, **_kwargs):
        raise AssertionError("source-only acceptance attempted a new native acquisition")
    monkeypatch.setattr(native_training_bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(native_training_bindings, "execute_paired_response_native_work", forbidden)
    with threadpool_limits(limits=1):
        retained = _retained_native_inputs()
        future = future_case(tmp_path / "future", plane=retained.writer, request=retained.request,
            public_package=retained.public_package)
        certificate = certify_native_training_instrument(writer=retained.writer, locator=retained.locator,
            programme=future.programme, bank=future.bank, original_future_reservation=future.original_future_reservation,
            cutoff=future.cutoff, record_id="certificate." + future.namespace)
        output = retained.writer.root.resolve("finite-dt-controls/" + future.namespace + "/public-lifecycle", for_write=True)
        case = source_case(output, future=future, certificate=certificate)
        preparation = _copied_source_preparation(case, output)
        directory = output / "authored"
        service = ExperimentProgrammeService(ROOT, retained.writer, retained.profile)
        authored = service.author(preparation=preparation, output_dir=directory)
        assert authored["native_contact"] == "none"
        selected = load_prepared_prospective_experiment(directory=directory, project_root=ROOT,
            storage_profile=retained.profile, artifact_writer=retained.writer)
        prove_recursive_prospective_handoff(selected.handoff)
        handoff = selected.handoff
        assert len(handoff.projection.tasks) == 9
        factories = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
        discovery = GENERATED_EXTENSION_BUNDLE_AGGREGATE
        issue_dir = output / "issue"
        issue_dir.mkdir()
        scaffold, paths, _, custody = _issue_api_fixture(issue_dir,
            standard_fixture=lambda: (handoff.authoring.base, handoff.context.resolve_standard(handoff.authoring.base).context))
        parts = handoff, factories, discovery, retained.writer, b"", scaffold, paths, custody
        issued = _issue_public_handoff(issue_dir, monkeypatch, handoff_parts=parts,
            namespace=future.namespace, compiled_candidate=selected.candidate)
        control = _sdk_execution(retained, handoff, issued, output / "execution", case.operational)
        scoped = ExperimentProgrammeService(ROOT, retained.writer, retained.profile,
            prospective_api_factory=lambda **_kwargs: control.api)
        from empirical_lawhood.api import matrix_finite_dt_source_runtime as source_runtime
        original_certify = source_runtime.certify_native_training_instrument
        caller_thread = get_ident()
        certifications = []
        def counted_certificate(**kwargs):
            if get_ident() != caller_thread:
                certifications.append(kwargs["locator"])
            return original_certify(**kwargs)
        with monkeypatch.context() as running:
            running.setattr(source_runtime, "certify_native_training_instrument", counted_certificate)
            report = scoped.run(directory=directory, maximum_parallel_tasks=4,
                request=RunCampaignRequest(control.package_path, confirmed=True))
        assert report["status"] == "SUCCEEDED", report
        # All six gates share one TRAIN reconstruction in worker preparation.
        # Static companion authentication has its own preceding caller scope;
        # no prerequisite authority is cached.
        assert certifications == [retained.locator]
        expected_tasks = {value.task_id for value in handoff.projection.tasks}
        observer_proof(control.executor, expected_tasks)
        assert len(control.executor.completed) == 9
        assert not any(value.native_effect for value in control.executor.contracts.values())
        assert control.service.maximum_parallel_tasks == control.package.execution_resource_envelope_spec.maximum_parallel_tasks == 4
        result = scoped.read(directory=directory, request=CampaignStatusRequest(control.package.run_plan_id))
        assert result["status"] == "SUCCEEDED", result
        science = result["scientific_result"]
        assert science["scientific_qualification"] == science["sampling"] == science["transport"] == "NOT_ESTABLISHED"
        assert science["source_evidence_ceiling"] == "MEASUREMENT" and science["new_native_contact_count"] == 0
        assert len(science["prior_executions"]) == 8
        _, _, _, expected = domain.lower(case.selection)
        assert science["qualification_result"] == expected.to_document()
        # The generic selected E5/E6 entry passes no parent read scope. Replay
        # this actual installed source there too, using ordinary current bytes
        # and a fresh TRAIN reconstruction rather than an asserted certificate.
        from empirical_lawhood.api.matrix_finite_dt_source_experiment import pipeline_evidence
        from empirical_lawhood.kernel.decoding import decode_canonical_record
        from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
        pipeline, qualification = pipeline_evidence(case.selection)
        publications = tuple((decode_canonical_record(pin, ObjectIdentity),
            decode_canonical_record(publication, ArtifactWriteResult)) for pin, publication in science["publications"])
        original_authenticate = source_runtime.authenticate_instrument_certificate
        ordinary_reconstructions = []
        def without_reader(**kwargs):
            assert kwargs["control_reader"] is None
            ordinary_reconstructions.append(kwargs["certificate"].locator)
            return original_authenticate(**kwargs)
        with monkeypatch.context() as ordinary:
            ordinary.setattr(source_runtime, "authenticate_instrument_certificate", without_reader)
            source_runtime.authenticate_installed_source_prerequisite(writer=retained.writer,
                result=qualification, pipeline=pipeline, publications=publications, read_scope=None)
        assert ordinary_reconstructions == [retained.locator]
        scope_pin, scope_publication = next((pin, publication) for pin, publication in publications
            if pin.object_schema == records.MatrixFiniteDtSourceScope.SCHEMA)
        substituted = tuple((pin, replace(publication, logical=replace(publication.logical,
            content_sha256="0" * 64))) if pin == scope_pin else (pin, publication) for pin, publication in publications)
        assert scope_publication.logical.content_sha256 != "0" * 64
        with pytest.raises(ValueError, match="publication differs from actual guarded manifest custody"):
            source_runtime.authenticate_installed_source_prerequisite(writer=retained.writer,
                result=qualification, pipeline=pipeline, publications=substituted, read_scope=None)
        recovery = _sdk_execution(retained, handoff, issued, output / "completed-recovery", case.operational,
            executor_factory=NeverExecute)
        recovered_service = ExperimentProgrammeService(ROOT, retained.writer, retained.profile,
            prospective_api_factory=lambda **_kwargs: recovery.api)
        recovered = recovered_service.recover(directory=directory, maximum_parallel_tasks=4,
            request=ResumeCampaignRequest(control.package.run_plan_id, confirmed=True))
        assert recovered["status"] == "SUCCEEDED" and not recovery.executor.calls, recovered
        reread = recovered_service.read(directory=directory, request=CampaignStatusRequest(control.package.run_plan_id))
        assert reread["scientific_result"] == science and not recovery.executor.calls
