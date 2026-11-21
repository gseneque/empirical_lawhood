# SPDX-License-Identifier: MPL-2.0
"""Finite exposed sharing fixtures; no native contact or qualification authority."""

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.methods.mass_balance_starter import bindings, design, science
from empirical_lawhood.methods.mass_balance_starter.records import MassAssessment, MassScope
from empirical_lawhood.methods.shared_mass_reference.provider import OperationInputHandle
from empirical_lawhood.methods.shared_mass_reference.service import MassScopeService
from empirical_lawhood.api import shared_mass_composition as composition
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.providers import ExternalInputPayload
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests.test_mass_balance_starter import operands


def fixture(case='positive'):
    evidence, specification, config, _, _ = operands(case)
    draft, sources = design.lower(specification, evidence)
    declarations = bindings.operation_declarations()
    registry = CapabilityRegistry('test.mass.shared-registry', tuple(d.manifest() for d in declarations))
    compiled = compile_recursive_wave(draft=draft, registry=registry,
        registrations=tuple(d.registration() for d in declarations), implementation_commit='a' * 40,
        output_codecs={key: codec for d in declarations for key, codec in d.record_codecs.items()})
    payloads = {row.config_id: row.payload for row in compiled.config_inputs}
    payloads.update({name: value.canonical_bytes() for name, value in sources})
    raws = {sha256(raw).hexdigest(): raw for raw in payloads.values()}
    calls = []

    def supply(spec):
        calls.append(spec)
        parent = ArtifactLineageParent(ObjectIdentity.from_record(draft.draft_id, draft),
            spec.expected_visibility_ceiling, spec.expected_outcome_access)
        return ExternalInputPayload.from_bytes(logical_artifact_id=spec.logical_artifact_id,
            payload_schema=spec.expected_payload_schema, profile=ArtifactProfile.CANONICAL_JSON,
            media_type=spec.expected_media_type, payload=raws[spec.expected_content_sha256],
            visibility_ceiling=spec.expected_visibility_ceiling, outcome_access=spec.expected_outcome_access,
            parent_visibility_ceilings=(spec.expected_visibility_ceiling,), lineage_parents=(parent,))

    supplier = SimpleNamespace(resolve_input=supply)
    kwargs = dict(registry=registry, execution_plan=compiled.execution_plan,
        configurations=(config, science.prediction_config(config)),
        scope_payload=evidence.scope.canonical_bytes(),
        scope_reference=ObjectIdentity.from_record('test.mass.shared-scope', evidence.scope),
        input_suppliers=tuple((d.capability_key, supplier) for d in declarations))
    return SimpleNamespace(kwargs=kwargs, draft=draft, compiled=compiled, payloads=payloads,
        calls=calls, supplier=supplier, registry=registry)


def test_one_decode_and_one_service_preserve_separate_provider_inputs(monkeypatch):
    selected = fixture()
    decode = composition.decode_canonical_bytes
    decoded = []

    def observe(*args, **kwargs):
        decoded.append(args[1])
        return decode(*args, **kwargs)

    monkeypatch.setattr(composition, 'decode_canonical_bytes', observe)
    runtime = composition.compose_mass_reference(**selected.kwargs)
    assert decoded == [MassScope] and selected.calls == []
    assert runtime.providers[0].__class__.__module__ != runtime.providers[1].__class__.__module__
    assert all(provider.service is runtime.service for provider in runtime.providers)
    assert runtime.precomposed.resolve(selected.registry.fingerprint()) is runtime.provider
    handles = tuple(provider.delegate.supplier for provider in runtime.providers)
    assert handles[0] is not handles[1] and handles[0].supplier is handles[1].supplier
    assert not set(handles[0].allowed_specs) & set(handles[1].allowed_specs)
    for handle, other in ((handles[0], handles[1]), (handles[1], handles[0])):
        with pytest.raises(PermissionError, match='another owner'):
            handle.resolve_input(other.allowed_specs[0])
        with pytest.raises(PermissionError, match='changed frozen input'):
            handle.resolve_input(replace(handle.allowed_specs[0], expected_content_sha256='f' * 64))
    assert selected.calls == []
    payloads = runtime.provider.external_inputs(selected.compiled.execution_plan)
    assert len(payloads) == len(selected.calls) == 4
    for payload in payloads:
        assert sha256(b''.join(payload.chunks())).hexdigest() == payload.source_sha256
        payload.close()
    assert len(runtime.provider.runners(selected.registry)) == 2
    assert len(runtime.provider.worker_preparations(selected.registry, selected.compiled.execution_plan)) == 2
    assert len(runtime.provider.output_semantic_contracts(selected.registry, selected.compiled.execution_plan)) == 2
    assert runtime.provider.scientific_adjudication_contract(selected.registry, selected.compiled.execution_plan) is None


@pytest.mark.parametrize('change,diagnostic', (
    ({'service_key': 'foreign.shared-scope'}, 'namespace'),
    ({'service_version': '2.0.0'}, 'revision'),
    ({'configuration': ObjectIdentity('foreign.scope', MassScope.SCHEMA, '1.0.0', 'f' * 64)}, 'identity'),
))
def test_service_selection_refuses_conflicting_ownership_and_revision(change, diagnostic):
    runtime = composition.compose_mass_reference(**fixture().kwargs)
    with pytest.raises(ValueError, match=diagnostic):
        runtime.service.resolve(replace(runtime.service.selection, **change))
    with pytest.raises(FrozenInstanceError):
        runtime.service.configuration = None
    with pytest.raises(TypeError, match='immutable MassScope'):
        MassScopeService({}, runtime.service.reference)


@pytest.mark.parametrize('field,value', (
    ('source_id', 'source.foreign'), ('receiver_id', 'receiver.foreign'), ('clock_id', 'clock.foreign'),
))
def test_correctly_encoded_wrong_physical_scope_refuses_before_provider_or_input(field, value, monkeypatch):
    selected = fixture()
    scope = replace(selected.kwargs['configurations'][0].scope, **{field: value})
    selected.kwargs.update(scope_payload=scope.canonical_bytes(),
        scope_reference=ObjectIdentity.from_record('test.mass.shared-scope', scope))
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory
    monkeypatch.setattr(RecursiveOperationProviderFactory, 'build_provider', lambda *a, **kw: pytest.fail('provider entered'))
    with pytest.raises(ValueError, match='source, receiver or clock'):
        composition.compose_mass_reference(**selected.kwargs)
    assert selected.calls == []


@pytest.mark.parametrize('change,diagnostic', (
    ('large', '4096-byte'), ('digest', 'bytes differ'), ('revision', 'MassScope@1.0.0'),
    ('missing-owner', 'per operation owner'), ('config', 'planned configuration'),
))
def test_changed_composition_refuses_before_any_supplier_or_factory(change, diagnostic, monkeypatch):
    selected = fixture()
    if change == 'large':
        selected.kwargs['scope_payload'] = b' ' * 4097
    elif change == 'digest':
        selected.kwargs['scope_payload'] += b'\n'
    elif change == 'revision':
        selected.kwargs['scope_reference'] = replace(selected.kwargs['scope_reference'], object_version='2.0.0')
    elif change == 'missing-owner':
        selected.kwargs['input_suppliers'] = selected.kwargs['input_suppliers'][:1]
    else:
        plan = selected.kwargs['execution_plan']
        first, *rest = plan.tasks
        selected.kwargs['execution_plan'] = replace(plan, tasks=(replace(first,
            capability=replace(first.capability,
                config=replace(first.capability.config, content_sha256='f' * 64))), *rest))
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory
    monkeypatch.setattr(RecursiveOperationProviderFactory, 'build_provider', lambda *a, **kw: pytest.fail('provider entered'))
    with pytest.raises(ValueError, match=diagnostic):
        composition.compose_mass_reference(**selected.kwargs)
    assert selected.calls == []


def test_finite_input_handle_and_provider_refuse_substitution():
    selected = fixture()
    runtime = composition.compose_mass_reference(**selected.kwargs)
    handle = runtime.providers[0].delegate.supplier
    with pytest.raises(TypeError, match='immutable external input'):
        replace(handle, allowed_specs=({},))
    with pytest.raises(ValueError, match='distinct finite input census'):
        replace(handle, allowed_specs=(handle.allowed_specs[0],) * 2)
    with pytest.raises(TypeError, match='exact code-owned'):
        type(runtime.providers[0])(delegate=runtime.providers[0], service=runtime.service,
            selection=runtime.service.selection, execution_plan=handle.execution_plan)
    with pytest.raises(ValueError, match='separate pure operation'):
        type(runtime.providers[0])(delegate=runtime.providers[1].delegate, service=runtime.service,
            selection=runtime.service.selection, execution_plan=handle.execution_plan)
    plan = replace(selected.compiled.execution_plan, execution_plan_id='test.changed-plan')
    with pytest.raises(ValueError, match='another frozen execution plan'):
        runtime.provider.external_inputs(plan)
    assert selected.calls == [] and type(handle) is OperationInputHandle


def test_existing_precomposition_route_refuses_repeated_construction_inputs():
    from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.methods.mass_balance_starter.extension import EXTENSION as _extension_owner_1
    EXECUTABLE_BINDING_CONTRIBUTION = _extension_owner_1.executable
    from empirical_lawhood.methods.mass_balance_starter.extension import EXTENSION as _extension_owner_2
    EXECUTABLE_BINDING_FACTORIES = _extension_owner_2.factories
    from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityProviderFactoryRegistry, LayeredCampaignRuntimeProviderResolver, compose_executable_binding_aggregate
    selected = fixture()
    runtime = composition.compose_mass_reference(**selected.kwargs)
    aggregate = compose_executable_binding_aggregate((EXECUTABLE_BINDING_CONTRIBUTION,),
        discovery_aggregate=GENERATED_EXTENSION_BUNDLE_AGGREGATE)
    factories = ExecutableCapabilityProviderFactoryRegistry(aggregate=aggregate, factories=EXECUTABLE_BINDING_FACTORIES)
    resolver = LayeredCampaignRuntimeProviderResolver(precomposed=runtime.precomposed, factories=factories)
    assert resolver.resolve(selected.registry) is runtime.provider
    with pytest.raises(ValueError, match='construction inputs unconsumed'):
        resolver.resolve(selected.registry, decoded_records=(runtime.service.configuration,))
    assert selected.calls == []


@pytest.mark.parametrize('case,expected', (('positive', 'SATISFIED'), ('adverse', 'FALSIFIED'), ('unevaluable', 'UNEVALUABLE')))
def test_shared_service_execution_keeps_two_receipts_and_completed_recovery(case, expected, tmp_path, monkeypatch):
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.execution.local.execution import DirectTaskExecutor, LocalScheduler
    from empirical_lawhood.storage.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.storage.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
    from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.science.records.status import OperationalStatus
    from empirical_lawhood.execution.execution import ExecutionAssuranceProfile, RunnerRegistry
    from empirical_lawhood.execution.plans import PlanLane
    from empirical_lawhood.execution.recovery import DevelopmentRunRecoveryIndex
    from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
    from tests.test_recursive_public_service import _plane

    selected = fixture(case)
    runtime = composition.compose_mass_reference(**selected.kwargs)
    plan, run = selected.compiled.execution_plan, selected.compiled.run_plan
    destination = tmp_path / 'shared-service-custody'
    plane = _plane(destination)
    # The provider's separate source handles return the actual original bytes.
    supplied = runtime.provider.external_inputs(plan)
    supplied_bytes = {value.logical_artifact_id: b''.join(value.chunks()) for value in supplied}
    for value in supplied:
        value.close()
    inputs = _external_inputs(plane=plane, plan=plan, draft=selected.draft, payloads=supplied_bytes, read_only=False)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id='wave.exposed-shared-service', authority_identities=())
    engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
    upgrade_catalog(engine)
    scheduler = LocalScheduler(operational_repository=SQLiteOperationalRepository(engine), artifact_writer=plane,
        receipt_store=ExternalTaskReceiptStore(plane), recovery_index=index, recovery_store=ExternalRunRecoveryStore(plane),
        runner_registry=RunnerRegistry(runtime.provider.runners(selected.registry), registry_sha256=selected.registry.fingerprint()),
        implementation_commit='a' * 40, external_input_resolver=StaticExternalInputResolver(inputs),
        executor=DirectTaskExecutor(), input_port_factory=plane, lane=PlanLane.DEVELOPMENT,
        authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    try:
        result = scheduler.execute(run.run_plan_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED and len(result.receipts) == 2
        assert len({receipt.task_id for receipt in result.receipts}) == 2
        receipt = next(row for row in result.receipts if row.task_id.endswith('.assess'))
        raw = (destination / receipt.output_materializations[0].relative_path).read_bytes()
        assessment = decode_canonical_bytes(raw, MassAssessment, maximum_bytes=128 * 1024)
        assert tuple(row.disposition for row in assessment.rows) == (expected, 'SATISFIED', 'SATISFIED')
        before = {path: path.read_bytes() for path in destination.rglob('*') if path.is_file()}
        monkeypatch.setattr(bindings.Runner, 'execute', lambda *a: pytest.fail('completed work entered a runner'))
        monkeypatch.setattr(selected.supplier, 'resolve_input', lambda *a: pytest.fail('completed work opened source'))
        replay = scheduler.execute(run.run_plan_id, plan)
        assert replay.receipts == result.receipts
        assert all(path.read_bytes() == raw for path, raw in before.items())
    finally:
        engine.dispose()
