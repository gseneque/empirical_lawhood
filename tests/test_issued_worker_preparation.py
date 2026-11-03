# SPDX-License-Identifier: MPL-2.0
"""Tiny selected-provider controls; no workers, native science or real grants.

The public service case uses exposed reference authority and a refusing executor
spy. Source observation is a declared synthetic seam, never clean-source proof.
"""

from dataclasses import replace
from functools import partial
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceCampaignRuntimeProvider
from empirical_lawhood.api import execution as owner
from empirical_lawhood.api import recursive_authoring
from empirical_lawhood.api.codecs import load_authoring
from empirical_lawhood.api.results import RunCampaignRequest
from empirical_lawhood.infrastructure.execution import ResourceAdmissionError
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.study_authoring import CapabilitySelection
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.executable_bindings import CompositeCampaignRuntimeProvider
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeWork
from empirical_lawhood.runtime.providers import (
    CampaignRuntimeProvider, CapabilityWorkerPreparation, validate_worker_preparations,
)
from empirical_lawhood.runtime.recursive_compiler import RecursiveOperationRegistration, RegisteredProvenanceRequirement
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProvider, recursive_operation_binding
from tests.api.test_campaign_execution import PACKAGE, _api
from tests.execution_support import ENFORCING_TEST_EXECUTOR_CAPABILITY
from tests.runtime_platform.test_worker_preflight import ExposedReadRunner
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import RunnerRegistry
from empirical_lawhood.runtime.plans import PlanLane, ProtocolExecutionPlan
from tests.runtime_platform.test_native_subwork import ExposedInput
from tests.runtime_platform.test_worker_preflight import _case
from tests.issued_study_support import build_issued_study_fixture
from tests.runtime_platform.test_deadline_free_execution_package import _execution_package_fixture, _compile
from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture
from tests.runtime_platform.test_study_issue import _issue_api_fixture


def _selection(manifest):
    return CapabilitySelection(manifest.capability_key, manifest.capability_version, manifest.implementation_sha256)


def _binding(commit):
    sources = (("synthetic-worker-fixture.py", sha256(b"exposed software only").hexdigest()),)
    return RecursiveImplementationBinding(sources, sha256(canonical_json_bytes(sources)).hexdigest(),
        "a" * 64, commit, False)


def _native(*, runner, context, expected_parent):
    return PreparedNativeWork(expected_parent, ("synthetic.unit",), ("synthetic.slot",))


def _environment(selected):
    return dict(selected, CASADIPATH=selected.get("CASADIPATH", "/synthetic/no-native"))


@pytest.fixture
def products():
    first = ExposedReadRunner().manifest
    other = replace(first, capability_key=first.capability_key + ".other")
    registry = CapabilityRegistry("registry.exposed-worker-preparation", tuple(sorted((first, other), key=lambda row: row.registry_id)))
    requirement = RegisteredProvenanceRequirement("provenance.exposed", lambda value: None)
    values = []
    bindings = []
    for manifest in registry.capabilities:
        registration = RecursiveOperationRegistration(_selection(manifest), ScientificStage.DEVELOP, ExposedInput,
            (), (OutputTemplate("echo", ExposedInput.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
            manifest.permissions, manifest.maximum_outcome_access,
            VisibilityCeiling.DEVELOPMENT_ONLY,
            manifest.resource_ceiling, native_effect=True, provenance_requirements=(requirement,),
            native_work_preparer=_native, worker_environment_selector=_environment)
        values.append(RecursiveOperationProvider(registry, registration, manifest,
            lambda manifest=manifest: SimpleNamespace(manifest=manifest), {ExposedInput.SCHEMA: ExposedInput}, object()))
        bindings.append(recursive_operation_binding(registration=registration, manifest=manifest))
    return registry, tuple(values), tuple(bindings), requirement


def _metadata_plan(registry, *manifests):
    return SimpleNamespace(registry_sha256=registry.fingerprint(), implementation_commit="2" * 40,
        tasks=tuple(SimpleNamespace(capability=SimpleNamespace(capability_key=row.capability_key,
            capability_version=row.capability_version), capability_implementation_sha256=row.implementation_sha256,
            maximum_attempts=1)
            for row in manifests))


def test_recursive_provider_projects_registration_callbacks_and_composite_selects_exact_tasks(products):
    registry, providers, bindings, requirement = products
    composite = CompositeCampaignRuntimeProvider(registry=registry, providers=providers, bindings=bindings)
    original = providers[0].worker_preparations(registry)[0]
    assert original.selection == providers[0].registration.selection
    assert original.provenance_requirements == (requirement,)
    assert original.provenance_requirements[0] is requirement
    assert original.native_work_preparer is _native and original.worker_environment_selector is _environment
    selected = composite.worker_preparations(registry, _metadata_plan(registry, registry.capabilities[1]))
    assert len(selected) == 1 and selected[0].selection == providers[1].registration.selection
    assert CampaignRuntimeProvider().worker_preparations(registry) == ()


@pytest.mark.parametrize("damage", ("other-owner", "version", "implementation", "duplicate", "untyped"))
def test_composite_refuses_conflicting_or_aliased_child_preparation_before_workers(products, monkeypatch, damage):
    registry, providers, bindings, _ = products
    original = providers[0].worker_preparations(registry)[0]
    if damage == "other-owner":
        rows = providers[1].worker_preparations(registry)
    elif damage == "version":
        rows = (replace(original, selection=replace(original.selection, capability_version="99.0.0")),)
    elif damage == "implementation":
        rows = (replace(original, selection=replace(original.selection, implementation_sha256="f" * 64)),)
    elif damage == "duplicate":
        rows = (original, original)
    else:
        rows = [original]
    monkeypatch.setattr(providers[0], "worker_preparations", lambda *args: rows)
    composite = CompositeCampaignRuntimeProvider(registry=registry, providers=providers, bindings=bindings)
    with pytest.raises((KeyError, TypeError, ValueError)):
        composite.worker_preparations(registry)


@pytest.mark.parametrize("damage", ("effect", "preparer", "environment", "provenance"))
def test_code_owned_worker_preparation_refuses_untyped_operational_contract(products, damage):
    registry, providers, _, requirement = products
    row = providers[0].worker_preparations(registry)[0]
    change = {"effect": {"native_effect": 1}, "preparer": {"native_effect": False},
        "environment": {"worker_environment_selector": "import.arbitrary"},
        "provenance": {"provenance_requirements": (requirement, requirement)}}[damage]
    with pytest.raises((TypeError, ValueError)):
        replace(row, **change)


def test_selected_plan_cannot_substitute_implementation_before_filtering(products):
    registry, providers, _, _ = products
    plan = _metadata_plan(registry, registry.capabilities[0])
    plan.tasks[0].capability_implementation_sha256 = "f" * 64
    with pytest.raises(ValueError, match="task differs"):
        validate_worker_preparations(providers[0].worker_preparations(registry), registry, plan)


@pytest.fixture
def selection(products, tmp_path, monkeypatch):
    registry, providers, _, _ = products
    plan = _metadata_plan(registry, registry.capabilities[0])
    service = object.__new__(owner.CampaignExecutionService)
    service.repo_root = tmp_path
    service.enforce_git_identity = True
    calls = []
    monkeypatch.setattr(service, "_check_identity", lambda package, **args: calls.append(("identity", args)))

    def capture(path):
        assert path == tmp_path
        calls.append(("capture", {}))
        return _binding(plan.implementation_commit)

    monkeypatch.setattr(recursive_authoring, "implementation_binding", capture)
    return service, SimpleNamespace(registry=registry), plan, providers[0], calls


def _arguments(selection, **kwargs):
    service, package, plan, provider, _ = selection
    return service._worker_preparation_arguments(provider=provider, package=package, execution_plan=plan, **kwargs)


def test_selected_provider_maps_preserve_callbacks_and_actual_source_observation_order(selection):
    _, _, _, provider, calls = selection
    actual = _arguments(selection)
    key = provider.registration.selection.capability_key
    assert [name for name, _ in calls] == ["identity", "capture", "identity"]
    assert actual["implementation_binding"] == _binding(selection[2].implementation_commit)
    assert actual["provenance_requirements"][key] is provider.registration.provenance_requirements
    assert actual["native_work_preparers"] == {key: _native}
    assert actual["worker_environment_selectors"] == {key: _environment}
    assert actual["native_effect_capability_keys"] == (key,)


def test_legacy_provider_never_captures_or_invents_worker_preparation(selection):
    service, package, plan, _, calls = selection
    assert service._worker_preparation_arguments(provider=CampaignRuntimeProvider(),
        package=package, execution_plan=plan) == {}
    assert calls == []


def test_two_selected_versions_cannot_collapse_into_one_scheduler_key(selection, monkeypatch):
    _, package, plan, provider, calls = selection
    row = provider.worker_preparations(provider.registry)[0]
    manifest = provider.registry.resolve(row.selection.capability_key, row.selection.capability_version)
    second = replace(manifest, capability_version="2.0.0")
    package.registry = CapabilityRegistry("registry.two-selected-versions", (manifest, second))
    updated = _metadata_plan(package.registry, manifest, second)
    plan.registry_sha256, plan.tasks = updated.registry_sha256, updated.tasks
    rows = (row, replace(row, selection=_selection(second)))
    monkeypatch.setattr(provider, "worker_preparations", lambda *args: rows)
    with pytest.raises(owner.CampaignCapabilityError, match="selected versions"):
        _arguments(selection)
    assert calls == []


def test_explicit_non_enforcing_pure_fixture_keeps_actual_binding_head(selection, monkeypatch):
    service, _, _, provider, _ = selection
    service.enforce_git_identity = False
    row = replace(provider.worker_preparations(provider.registry)[0], native_effect=False, native_work_preparer=None)
    monkeypatch.setattr(provider, "worker_preparations", lambda *args: (row,))
    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda path: _binding("f" * 40))
    assert _arguments(selection)["implementation_binding"].observed_git_head == "f" * 40


@pytest.mark.parametrize("damage", ("native-missing", "wrong-source", "changed-after", "bad-product"))
def test_issued_selection_refuses_missing_software_or_source_before_scheduler(selection, monkeypatch, damage):
    service, _, plan, provider, calls = selection
    if damage == "native-missing":
        row = replace(provider.worker_preparations(provider.registry)[0], native_work_preparer=None)
        monkeypatch.setattr(provider, "worker_preparations", lambda *args: (row,))
    elif damage == "changed-after":
        def changed(package, **args):
            if calls:
                raise owner.CampaignIdentityError("selected source changed during actual capture")
        monkeypatch.setattr(service, "_check_identity", changed)
    else:
        monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda path:
            _binding("f" * 40) if damage == "wrong-source" else object())
    with pytest.raises((owner.CampaignCapabilityError, owner.CampaignIdentityError)):
        _arguments(selection)
    if damage == "native-missing":
        assert calls == []


def test_public_campaign_prepares_exact_pure_contract_before_refusing_executor_without_contact(tmp_path, monkeypatch):
    package = load_authoring(PACKAGE)
    manifest = package.registry.resolve("reference.prepare", "1.0.0")
    requirement = RegisteredProvenanceRequirement("provenance.exposed.public", lambda value: None)
    row = CapabilityWorkerPreparation(_selection(manifest), (requirement,), False, None, _environment)

    class SelectedProvider(ReferenceCampaignRuntimeProvider):
        def worker_preparations(self, registry, execution_plan=None):
            return validate_worker_preparations((row,), registry, execution_plan)

    observed = []

    class RefusingExecutor:
        enforcement_capability = ENFORCING_TEST_EXECUTOR_CAPABILITY

        def execute(self, runner, context, *, timeout_seconds, prepared_contract,
                provenance_requirements, native_work_preparer, native_entry=None):
            assert type(prepared_contract) is PreparedInvocationContract
            assert prepared_contract.manifest == manifest and not prepared_contract.native_effect
            assert prepared_contract.native_work is None
            assert dict(prepared_contract.environment.selected_environment)["CASADIPATH"]
            assert provenance_requirements == (requirement,) and native_work_preparer is None
            assert native_entry is None
            observed.append(prepared_contract)
            raise ResourceAdmissionError("exposed executor refusal before worker or native entry")

    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda path: _binding(package.implementation_commit))
    api, external, _ = _api(tmp_path, provider=SelectedProvider(registry=package.registry),
        executor=RefusingExecutor(), executor_enforces_resources=False)
    failures = []
    original_execute = api._execution_service._execute_plan
    def retained_execution(**arguments):
        try:
            return original_execute(**arguments)
        except BaseException as error:
            current = error
            while current is not None:
                failures.append(type(current).__name__ + ": " + str(current))
                current = current.__cause__
            raise
    monkeypatch.setattr(api._execution_service, "_execute_plan", retained_execution)
    result = api.run_campaign(RunCampaignRequest(PACKAGE, confirmed=True))
    assert not result.succeeded and len(observed) == 1, (failures, tuple(error.message for error in result.errors))
    assert not tuple(external.rglob("native-contacts/*.json"))
    assert not tuple(external.rglob("receipts/*/*.json"))
    assert not tuple(external.rglob("outputs/*/*"))


def test_public_native_automatic_retry_refuses_before_source_capture_or_custody(tmp_path, monkeypatch):
    package = load_authoring(PACKAGE)
    manifest = package.registry.resolve("reference.prepare", "1.0.0")
    row = CapabilityWorkerPreparation(_selection(manifest), native_effect=True, native_work_preparer=_native)

    class SelectedProvider(ReferenceCampaignRuntimeProvider):
        def worker_preparations(self, registry, execution_plan=None):
            return validate_worker_preparations((row,), registry, execution_plan)

    def forbidden_capture(path):
        pytest.fail("unprepared automatic native retry reached source capture")

    monkeypatch.setattr(recursive_authoring, "implementation_binding", forbidden_capture)
    api, external, _ = _api(tmp_path, provider=SelectedProvider(registry=package.registry))
    result = api.run_campaign(RunCampaignRequest(PACKAGE, confirmed=True))
    assert not result.succeeded
    assert any("forbids automatic effect retries" in error.message for error in result.errors)
    assert not (external / "runs").exists()


def test_selected_native_maps_reach_real_preparation_before_executor_refusal_and_no_contact(tmp_path, monkeypatch):
    # Original tiny typed input custody, not an issued study or real authority.
    plane, bundle, runner, context, original, _ = _case(tmp_path, native=True, nested=False)
    try:
        registry = CapabilityRegistry("registry.native-preparation-dispatch", (runner.manifest,))
        task = original.execution_task_record
        plan = ProtocolExecutionPlan("plan.native-preparation-dispatch", PlanLane.DEVELOPMENT,
            ObjectIdentity("source.exposed", "empirical-lawhood/runtime/protocol-run-plan", "1.0.0", "1" * 64),
            registry.fingerprint(), original.implementation.observed_git_head, (task,), True)
        row = CapabilityWorkerPreparation(_selection(runner.manifest), native_effect=True,
            native_work_preparer=_native, worker_environment_selector=_environment)
        provider = SimpleNamespace(worker_preparations=lambda *args: (row,))
        service = object.__new__(owner.CampaignExecutionService)
        service.repo_root, service.enforce_git_identity = tmp_path, True
        monkeypatch.setattr(service, "_check_identity", lambda *args, **kwargs: None)
        monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda path: original.implementation)
        arguments = service._worker_preparation_arguments(provider=provider,
            package=SimpleNamespace(registry=registry), execution_plan=plan)
        store = ExternalNativeEffectContactStore(plane=plane,
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            visibility_ceiling=task.outputs[0].visibility_ceiling, outcome_access=context.outcome_access)
        observed = []

        class RefusingExecutor:
            def execute(self, runner, received, *, timeout_seconds, prepared_contract,
                    provenance_requirements, native_work_preparer, native_entry):
                assert type(prepared_contract) is PreparedInvocationContract
                assert prepared_contract.native_effect and prepared_contract.native_preparation_error is None
                assert prepared_contract.execution_plan == ObjectIdentity.from_record(plan.execution_plan_id, plan)
                assert prepared_contract.execution_task_record is task
                assert prepared_contract.native_work.expected_parent == prepared_contract.expected_parent_contact
                assert native_work_preparer is _native and callable(native_entry)
                assert store.read(received.run_id, received.task_id) is None
                observed.append(prepared_contract)
                raise ResourceAdmissionError("exposed Stop before worker and native contact")

        scheduler = owner.LocalScheduler(operational_repository=object(), artifact_writer=plane,
            receipt_store=object(), recovery_index=object(), recovery_store=object(),
            runner_registry=RunnerRegistry((runner,), registry_sha256=registry.fingerprint()),
            implementation_commit=plan.implementation_commit, executor=RefusingExecutor(),
            input_port_factory=plane, lane=plan.lane, authorized_barriers=(),
            native_effect_contact_store=store, **arguments)
        scheduler._active_execution_plan = ObjectIdentity.from_record(plan.execution_plan_id, plan)
        with pytest.raises(ResourceAdmissionError, match="exposed Stop"):
            scheduler._execute_runner(context.run_id, task, context.attempt_id, (), bundle.verified_inputs, ())
        assert len(observed) == 1
        assert store.read(context.run_id, context.task_id) is None
    finally:
        bundle.close()


def _single_attempt_standard():
    """Freeze a valid toy graph once, with no automatic native retry selected."""
    authoring, context = _standard_fixture()
    templates = []
    for template in context.base.templates:
        steps = tuple(replace(step, maximum_attempts=1) for step in template.protocol.steps)
        by_id = {step.step_id: step for step in steps}
        graph = replace(template.graph, nodes=tuple(replace(node,
            protocol_step_sha256=by_id[node.node_id].fingerprint()) for node in template.graph.nodes))
        templates.append(replace(template, protocol=replace(template.protocol, steps=steps), graph=graph))
    return authoring, replace(context, base=replace(context.base, templates=tuple(templates)))


@pytest.fixture(scope="module")
def issued_resources(tmp_path_factory):
    root = tmp_path_factory.mktemp("toy-issued-resource-effect")
    fixture = build_issued_study_fixture(root, issue_fixture_factory=partial(_issue_api_fixture,
        standard_fixture=_single_attempt_standard))
    packages = {native: _execution_package_fixture(fixture, native_simulator=native, jit=False)
        for native in (False, True)}
    return root, packages, {native: _compile(fixture, package)[1] for native, package in packages.items()}


@pytest.mark.parametrize("resource_native,code_native", ((False, False), (True, True), (False, True), (True, False)))
def test_real_issued_resource_cell_and_code_owned_effect_must_agree_before_source_capture(
        issued_resources, monkeypatch, resource_native, code_native):
    # Full original toy package constructors and compiler run above. These are
    # exposed synthetic credentials, not real issue or scientific authority.
    root, packages, plans = issued_resources
    package, plan = packages[resource_native], plans[resource_native]
    cell = next((value for value in package.execution_resource_envelope_spec.task_cells
        if value.native_simulator_launch), package.execution_resource_envelope_spec.task_cells[0])
    task = next(value for value in plan.tasks if value.task_id == cell.task_id)
    manifest = package.registry.resolve(task.capability.capability_key, task.capability.capability_version)
    row = CapabilityWorkerPreparation(_selection(manifest), native_effect=code_native,
        native_work_preparer=_native if code_native else None)
    provider = SimpleNamespace(worker_preparations=lambda registry, execution_plan=None:
        validate_worker_preparations((row,), registry, execution_plan))
    service = object.__new__(owner.CampaignExecutionService)
    service.repo_root, service.enforce_git_identity = root, True
    calls = []
    monkeypatch.setattr(service, "_check_identity", lambda *args, **kwargs: calls.append("identity"))

    def capture(path):
        calls.append("capture")
        return _binding(plan.implementation_commit)

    monkeypatch.setattr(recursive_authoring, "implementation_binding", capture)
    if resource_native != code_native:
        with pytest.raises(owner.CampaignCapabilityError, match="native effect.*resource cell"):
            service._worker_preparation_arguments(provider=provider, package=package, execution_plan=plan)
        assert calls == []
    else:
        selected = service._worker_preparation_arguments(provider=provider, package=package, execution_plan=plan)
        assert bool(selected["native_effect_capability_keys"]) is code_native
        assert calls == ["identity", "capture", "identity"]
