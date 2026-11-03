# SPDX-License-Identifier: MPL-2.0
"""Actual Matrix root growth with no native contact.

E3 uses issued software controls and its real public prospective plan.
Selected CONF/transfer controls retain whole-root censuses and current public
missing-commitment holds; they do not assert an issued completed child, genuine
qualification, successful scientific read or receipt-based recovery.
"""
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import current_result_custody, execution as execution_owner
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody, current_issued_task_control_scope
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile, resolve_external_root_contract
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.test_current_result_custody import _DisclosedCustodySupplier
from tests.test_matrix_e3_public_programme import ROOT, _execution, _selected_case


def _population_profile(directory):
    # Same actual-mount selection as tests.numerical_provenance_fixtures.
    mounted = next(value for value in (directory, *directory.parents) if value.is_mount())
    profile = OperatorStorageProfile("software.matrix-population.storage", "external-filesystem", "1.0.0",
        str(directory / "originals"), str(mounted), "selected", "scientific-scratch",
        OperatorStorageAccessMode.READ_WRITE, None, None, (), "strict-mount-contained-no-symlink",
        1, (), 4, False)
    contract = resolve_external_root_contract(profile, repo_root=ROOT, home_root=Path.home())
    assert Path(contract.canonical_path) == directory / "originals" / "selected"
    assert Path(contract.required_mount_path).is_mount()
    return profile, contract


def test_population_profile_resolves_actual_mount_and_original_fixture_namespace(tmp_path):
    profile, contract = _population_profile(tmp_path)
    assert Path(contract.canonical_path) == Path(profile.external_root_locator) / profile.artifact_namespace
    assert Path(profile.external_root_locator).is_relative_to(Path(contract.required_mount_path))
    assert contract.required_mount_path == profile.required_mount_path


def _issued_e3(directory, design, monkeypatch):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import (
        RESOURCE_BINDING_DEPENDENCY, bind_protected_e3_experiment_inputs,
    )
    from empirical_lawhood.infrastructure.source_closure import capture_target_closure
    from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff
    from tests.runtime_platform.test_study_issue import _issue_api_fixture

    directory.mkdir()
    # Refuse a mismatched profile before the expensive scientific fixture setup.
    profile, selected_contract = _population_profile(directory)
    case = _selected_case(directory / "originals", design, maximum_parallel_tasks=4)
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    original = case.plane
    assert original.root.contract.canonical_path == selected_contract.canonical_path
    # Keep actual publication storage IDs and paths; select the real EL mount
    # for this disposable operational writer, as the existing public E3 owner does.
    case.plane = ExternalArtifactPlane(GuardedExternalRoot(replace(original.root.contract,
        required_mount_path=selected_contract.required_mount_path)), validators=original.validators,
        semantic_validations=original.semantic_validations, custody_limits=original.custody_limits)
    assert case.plane.root.contract.required_mount_path == profile.required_mount_path
    diagnostic = case.plane.root.diagnostic()
    assert diagnostic.read_ready and diagnostic.write_ready, diagnostic
    service = ExperimentProgrammeService(ROOT, case.plane, profile)
    closure = capture_target_closure(ROOT, case.selection.selection_id + ".prospective.source-closure").closure
    execution = ExecutionSelection(4, "main-locked",
        ObjectIdentity.from_record("recursive-member.implementation", closure), case.plane.root.contract.canonical_path)
    inputs = bind_protected_e3_experiment_inputs(case.specification,
        {"protected-selection": case.selection}, files=case.files)
    prepared = service.prepare(case.specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=execution, protocol_bytes=case.candidate_bytes)
    assert prepared.draft is not None
    assert tuple((row.code, row.kind) for row in prepared.dependencies) == (
        (RESOURCE_BINDING_DEPENDENCY, DependencyKind.SOFTWARE),)
    assert not prepared.executable
    assert prepared.draft.prospective_draft.system.authority_policy.budget_ceiling.contains(
        prepared.draft.prospective_draft.resource_ceiling)
    authored_directory = Path(case.plane.root.contract.canonical_path) / "public-e3-programme"
    service.author(preparation=prepared, output_dir=authored_directory)
    selected = load_prepared_prospective_experiment(directory=authored_directory, project_root=ROOT,
        storage_profile=profile, artifact_writer=case.plane)
    scaffold = directory / "synthetic-authority"
    scaffold.mkdir()
    handoff = selected.handoff
    assert handoff.compilation.draft == prepared.draft
    assert handoff.compilation.candidate_report.candidate is not None, handoff.compilation.candidate_report.diagnostics
    assert selected.candidate.authoring_package == handoff.authoring
    assert handoff.resources.maximum_parallel_tasks == 4
    scaffold_api, paths, _, custody = _issue_api_fixture(scaffold, standard_fixture=lambda: (
        handoff.authoring.base, handoff.context.resolve_standard(handoff.authoring.base).context))
    parts = (handoff, EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
        GENERATED_EXTENSION_BUNDLE_AGGREGATE, case.plane, b"", scaffold_api, paths, custody)
    issued = _issue_public_handoff(directory, monkeypatch, handoff_parts=parts,
        namespace="software-matrix-population-" + design, compiled_candidate=selected.candidate)
    control = _execution(case, handoff, issued, directory, maximum_parallel_tasks=4)
    runs = []
    original = execution_owner.compile_run_plan
    def capture(**kwargs):
        value = original(**kwargs)
        runs.append(value)
        return value
    with monkeypatch.context() as patch:
        patch.setattr(execution_owner, "compile_run_plan", capture)
        plan = control.service._recompile_rebuild_execution_plan(control.package)
    run, = runs
    control.service._persist_plans(control.package, run, plan, package_name="campaign-package",
        source_plan_name="run-plan", minimum_free_bytes=1)
    return case, control, plan


def _task_context(control, task):
    manifest = control.package.registry.resolve(task.capability.capability_key, task.capability.capability_version)
    context = TaskContext(control.package.run_plan_id, task.task_id, "attempt.disclosed.matrix-population",
        task.capability.config, (), (), tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile,
            row.media_type, row.logical_artifact_id) for row in task.outputs),
        task.capability.required_permissions, task.capability.requested_outcome_access,
        task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL)
    return context, SimpleNamespace(manifest=manifest)


def test_actual_e3_two_root_populations_bound_static_controls_and_replay_current_authority(tmp_path, monkeypatch):
    metrics = []
    for design in ("small", "alternative"):
        case, control, plan = _issued_e3(tmp_path / design, design, monkeypatch)
        roots = tuple(task for task in plan.tasks
            if task.capability.capability_key.startswith("matrix-e3-protected.")
            and task.capability.capability_key.endswith(".prefix"))
        assert roots
        custody = CurrentIssuedTaskCustody(writer=case.plane, reveal_authority_id=control.reveal.authority_id)
        control.service.executable_platform_ports = (ExecutablePlatformPort("disclosed.actual-matrix-control",
            RecursiveOperationInputPort(_DisclosedCustodySupplier(custody=custody,
                resolve_input=lambda spec: pytest.fail("control test entered a worker input")))),)
        validations, issued_reads, grants, payload_reads, parent_scopes = [], [], [], [], []
        validate_plan = current_result_custody._require_prepared_plan_bindings
        load_issue = ExternalIssuedStudyPublisher._load_executable_study
        load_grant = ExternalStudyOperationAuthorityStore.load
        from empirical_lawhood.infrastructure import canonical_record_read
        decode_control = canonical_record_read._SelectedCanonicalRecordRead.decode
        def counted_validation(**kwargs):
            validations.append(kwargs["run_plan"].run_plan_id)
            return validate_plan(**kwargs)
        def counted_issue(self, issue_id, **options):
            issued_reads.append(issue_id)
            return load_issue(self, issue_id, **options)
        def current_grant(self, authority_id):
            grants.append(authority_id)
            return load_grant(self, authority_id)
        def bounded_control(reader, raw):
            result = decode_control(reader, raw)
            path = reader.manifest.materialization.relative_path
            if "/plans/" in path:
                payload_reads.append((path, len(raw), reader.manifest.materialization.size_bytes))
            return result
        with monkeypatch.context() as patch:
            patch.setattr(current_result_custody, "_require_prepared_plan_bindings", counted_validation)
            patch.setattr(ExternalIssuedStudyPublisher, "_load_executable_study", counted_issue)
            patch.setattr(ExternalStudyOperationAuthorityStore, "load", current_grant)
            patch.setattr(canonical_record_read._SelectedCanonicalRecordRead, "decode", bounded_control)
            with current_issued_task_control_scope(control.api):
                for task in roots:
                    context, runner = _task_context(control, task)
                    with custody.preparation_scope():
                        assert custody.current_task(context, runner)[1] == plan
                        with custody.original_read_scope() as (_, parent):
                            parent_scopes.append(parent)
                            assert parent.plan_reader.authenticate_execution_plan(package=control.package,
                                issued=control.package.issued_study, run_id=context.run_id) == plan
                assert validations == [control.package.run_plan_id]
                assert issued_reads == [control.package.issued_study.issue_id]
                assert len({id(value) for value in parent_scopes}) == 1
                execution_id = control.package.execution_authority.authority_id
                assert grants.count(execution_id) == len(roots)
                assert Counter(path for path, _, _ in payload_reads).most_common(1)[0][1] == 1
                assert all(size <= bound for _, size, bound in payload_reads)
                context, runner = _task_context(control, roots[0])
                with pytest.raises(PermissionError, match="actual current installed task"):
                    custody.current_task(replace(context, task_id=context.task_id + ".foreign"), runner)
                def changed_grant(self, authority_id):
                    value = load_grant(self, authority_id)
                    return replace(value, expires_at_utc="2026-08-23T20:43:00Z") if authority_id == execution_id else value
                patch.setattr(ExternalStudyOperationAuthorityStore, "load", changed_grant)
                with pytest.raises(PermissionError, match="current execution grant"):
                    custody.current_task(context, runner)
                assert validations == [control.package.run_plan_id]
        assert custody._control_reader is custody._parent_read_scope is None
        assert not control.executor.contracts and not control.executor.processes
        metrics.append(dict(design=design, whole_roots=len(roots), plan_tasks=len(plan.tasks),
            role_counts=dict(case.allocation.role_counts), prepared_plan_validations=len(validations),
            common_parent_scope_count=len({id(value) for value in parent_scopes}),
            control_payload_reads=len(payload_reads), control_payload_bytes=sum(size for _, size, _ in payload_reads)))
    assert metrics[1]["whole_roots"] > metrics[0]["whole_roots"]
    assert metrics[1]["plan_tasks"] > metrics[0]["plan_tasks"]
    assert metrics[0]["prepared_plan_validations"] == metrics[1]["prepared_plan_validations"] == 1
    assert metrics[0]["control_payload_reads"] == metrics[1]["control_payload_reads"]
    (tmp_path / "actual-matrix-population-controls.json").write_text(json.dumps(metrics, sort_keys=True) + "\n")


@pytest.mark.parametrize("phase", ("E5_CONFIRMATION", "E6_TRANSFER"))
def test_selected_two_actual_root_populations_keep_complete_graph_and_current_declarative_entry_hold(monkeypatch, phase):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as graph
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as public
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedProtectedSpecification
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedEntryEvidenceV3
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import assess_selected_programme
    from tests.test_matrix_selected_package import reference
    from tests.test_matrix_selected_protected import transfer_case, confirmation_case, root_inputs, validate_recursive_scientific_roots

    observations = []
    phase_id = phase.lower()
    def forbidden(*args, **kwargs):
        pytest.fail("unqualified exposed population control entered protected lowering")
    monkeypatch.setattr(public, "lower", forbidden)
    for count in (1, 2):
        transfer = transfer_case(groups_per_regime=count)
        programme = confirmation_case(transfer, groups=count) if phase == "E5_CONFIRMATION" else transfer
        projection = MatrixSelectedPublicProgramme.from_programme(programme)
        allocation = public.allocation(projection)
        groups = count if phase == "E5_CONFIRMATION" else 2 * count
        sources = 2 * count
        assert len(allocation.units) == groups
        assert len(programme.point_design.sources) == sources
        assert len(programme.sources.closure.reservation.allocation.roots) == groups
        assert len(public.allocation(projection).units) == groups
        evidence = reference("evidence.disclosed." + phase_id, MatrixSelectedEntryEvidenceV3)
        from tests.test_matrix_e6_transport_assessment import exposed_parent_census
        configs, external, links, _, _ = graph.contracts(programme, evidence, 1,
            produced_input_parents=exposed_parent_census(programme))
        assert len(configs) == 2 + 9 * sources
        assert len({node for node, _ in configs}) == len(configs)
        assert sum(row.consumer_input_id.startswith("readouts.") for row in links) == sources
        validate_recursive_scientific_roots(**root_inputs(programme))
        manifest, result = assess_selected_programme(programme, {}, result_id="result.disclosed." + phase_id)
        assert len(manifest.rows) == len(result.cases) == sources
        assert all(row.disposition == "MISSING" for row in result.cases)
        specification = SelectedPreparedProtectedSpecification("experiment.disclosed." + phase_id,
            "ORIGINAL_E3", phase, count, programme.point_design.arms, programme.criterion, None, None,
            programme.transfer_domain_claims)
        prepared = public.prepare(specification, scientific_inputs={}, execution=ExecutionSelection())
        assert not prepared.executable and prepared.draft is None
        assert dict(prepared.census.role_counts) == {"groups": groups, "sources": sources}
        assert dict(prepared.census.resolved_role_counts) == {"groups": 0, "sources": 0}
        assert {row.source_key for row in prepared.dependencies if row.source_key} == {"request"}
        assert len(external) > 0
        observations.append((groups, sources, len(configs), len(links)))
    assert all(right > left for left, right in zip(observations[0], observations[1], strict=True))
