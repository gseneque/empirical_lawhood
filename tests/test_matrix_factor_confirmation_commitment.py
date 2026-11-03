# SPDX-License-Identifier: MPL-2.0
"""Pure protected commitment controls; hypothetical custody grants no authority."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.commitment import COMMIT_KEY, E1Commitment, E1CommitmentConfig, E1Committer, authenticate_prior_publications, committed
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import BUDGET, NAMESPACE, E1NativeRunner, E1OperationConfig, _decode, operation_factories
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from tests.test_matrix_factor_confirmation_adjudication import prospective
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_factor_confirmation_history import e1 as e1
from tests.test_matrix_factor_response import Reader


def _blocked(*args, **kwargs):
    raise AssertionError('pure commitment control reached native, science, RNG or eigensolve')


def _block_science(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import science
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', _blocked)
    for name in ('measure', 'assess_history', 'assess_factor'):
        monkeypatch.setattr(science, name, _blocked)
    monkeypatch.setattr(np.random, 'Generator', _blocked)
    monkeypatch.setattr(np.random, 'PCG64DXSM', _blocked)
    monkeypatch.setattr(np.linalg, 'eigh', _blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', _blocked)


def _port(write, raw, *, dependency=False, verified=None):
    if verified is not None:
        verified.append(VerifiedArtifactInput(write.logical, write.materialization))
    return WorkerInputPort(WorkerInputBinding(write.logical.logical_artifact_id, write.materialization.materialization_id,
        write.logical.payload_schema, write.logical.media_type, len(raw), write.logical.visibility_ceiling, write.logical.outcome_access,
        WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL), Reader(raw))


def _context(config, ports, role, outputs=(), dependencies=()):
    manifest = next(f.manifest for f in operation_factories() if f.manifest.capability_key == NAMESPACE+'.'+role)
    config_port = next(p for p in ports if p.payload_schema == config.SCHEMA)
    ports = tuple(sorted(ports, key=lambda p: p.artifact_id))
    return TaskContext('run.software.e1', COMMIT_KEY if role == 'commit' else NAMESPACE+'.'+config.source.root_id+'.'+role,
        'attempt.software.e1.'+role, CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
            config.fingerprint(), config_port.artifact_id), tuple(p.binding for p in ports), ports, outputs,
        manifest.permissions, Access.OUTCOME_BLIND if role == 'commit' else Access.EVALUATION_SEALED,
        BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)


def _prepare_history_context(context, verified, source):
    """Freeze a disclosed direct-worker task, without issue or native preparation."""
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings as owner
    from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.capabilities import CapabilityRequirement
    from empirical_lawhood.runtime.plans import (
        ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec,
    )
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from tests.worker_configuration_support import freeze_worker_configuration

    declaration = next(row for row in owner.operation_declarations() if row.capability_key == NAMESPACE+'.history')
    manifest = declaration.manifest()
    by_id = {row.artifact_id: row for row in verified}
    stream_names = {source.root.stream_identity(row).object_id: 'streams.'+row.purpose for row in source.root.streams}
    phase, = (row for row in owner.PHASES if row[0] == 'history')
    input_names = {kind.SCHEMA: name for name, kind in phase[1] if name != 'streams'}
    external, edges = [], []
    for port in context.input_ports:
        actual = by_id[port.artifact_id]
        name = ('config' if port.artifact_id == context.config.artifact_id else stream_names[port.artifact_id]
            if port.artifact_id in stream_names else input_names[port.payload_schema])
        receipt = next((row for row in context.dependency_receipts
            if port.materialization_id in row.output_materialization_ids), None)
        if port.kind is WorkerInputKind.EXTERNAL:
            external.append(ExternalInputSpec(name, port.artifact_id, actual.logical.content_sha256,
                port.payload_schema, port.media_type, port.size_bytes, port.visibility_ceiling, port.outcome_access, None))
        if name != 'config':
            edges.append(ScientificInputSpec('edge.'+context.task_id+'.'+name, name, ScientificInputRole.SOURCE,
                None if receipt is None else receipt.task_id, None if receipt is None else 'product',
                'fixture.e1.'+name if receipt is None else None, port.artifact_id, port.artifact_id,
                port.payload_schema, port.media_type, port.size_bytes, port.outcome_access,
                port.visibility_ceiling, BarrierKind.NONE))
    outputs = tuple(ArtifactOutputSpec(row.output_id, 'fixture.e1.history.'+row.output_id,
        'fixture-e1-history/'+row.output_id+('.npz' if row.profile is ArtifactProfile.MATRIX_ARRAY_NPZ else '.json'),
        row.payload_schema, row.profile, row.media_type,
        Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED) for row in declaration.outputs)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        context.config, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        manifest.maximum_evidence_ceiling, context.outcome_access, context.resource_budget)
    task = ExecutionTask(context.task_id, declaration.stage, requirement, manifest.implementation_sha256,
        tuple(sorted(row.task_id for row in context.dependency_receipts)),
        tuple(sorted(external, key=lambda row: row.input_id)), outputs, (), BarrierKind.NONE, 1,
        ('obligation.disclosed.e1-history',), scientific_inputs=tuple(sorted(edges, key=lambda row: row.edge_id)))
    task = freeze_worker_configuration(task)
    context = replace(context, output_ports=tuple(WorkerOutputPort(row.output_id, row.payload_schema,
        row.profile, row.media_type, row.logical_artifact_id) for row in outputs))
    provenance = source.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    contract = prepare_worker_invocation(E1NativeRunner('history'), context, tuple(verified),
        implementation=implementation,
        execution_plan=ObjectIdentity('plan.unissued.literal.e1-history',
            'empirical-lawhood/runtime/execution-plan', '1.0.0', 'e'*64),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task)
    assert not contract.native_effect and contract.native_work is None
    return replace(context, prepared_invocation=contract)


@pytest.mark.parametrize('defect', (None, 'missing-source', 'changed-publication', 'exposed-input', 'changed-config'))
def test_pure_commitment_authenticates_full_source_and_prior_publications(e1, monkeypatch, defect):
    plane, sources, _ = e1
    config = E1CommitmentConfig('config.'+COMMIT_KEY, sources)
    records = (config, *sources)
    ports = [_port(publish(plane, record, record.config_id if record is config else record.source_id), record.canonical_bytes()) for record in records]
    ports += [_port(sources[0].reservation.publication, sources[0].allocation.canonical_bytes()),
        _port(sources[0].specification.publication, sources[0].specification.selection.canonical_bytes())]
    if defect == 'missing-source':
        ports = [p for p in ports if p.artifact_id != sources[-1].source_id]
    elif defect == 'changed-publication':
        ports[-1] = replace(ports[-1], binding=replace(ports[-1].binding, artifact_id='foreign.publication'))
    elif defect == 'exposed-input':
        ports[-1] = replace(ports[-1], binding=replace(ports[-1].binding, outcome_access=Access.DEVELOPMENT_VISIBLE))
    output = WorkerOutputPort(COMMIT_KEY+'.product', E1Commitment.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'ordinary.commit')
    context = _context(config, ports, 'commit', (output,))
    if defect == 'changed-config':
        context = replace(context, config=replace(context.config, content_sha256='f'*64))
    _block_science(monkeypatch)
    manifest = next(f.manifest for f in operation_factories() if f.manifest.capability_key == COMMIT_KEY)
    runner = E1Committer(manifest, BUDGET)
    if defect is None:
        result = runner.execute(context)
        assert decode_canonical_bytes(result.outputs[0].payload, E1Commitment, maximum_bytes=None) == committed(config)
    else:
        with pytest.raises(ValueError, match='commitment'):
            runner.execute(context)


@pytest.mark.parametrize('defect', (None, 'missing-commitment', 'changed-source', 'wrong-receipt', 'external-commitment'))
def test_history_requires_receipted_exact_commitment_before_native_port(e1, monkeypatch, defect):
    plane, sources, _ = e1
    source = sources[0]
    config = E1OperationConfig('config.'+NAMESPACE+'.'+source.root_id+'.history', 'history', source)
    values = ((config.config_id, config), (source.source_id, source), (source.coordinate.coordinate_id, source.coordinate),
        (source.provenance.identity.object_id, source.provenance),
        *((source.root.stream_identity(s).object_id, s) for s in source.root.streams))
    verified = []
    ports = []
    for name, record in values:
        write = (plane.write(ArtifactWriteRequest(name, 'inputs/'+name+'.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.'+name,
            'inputs', record.canonical_bytes(), Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED))
            if record is config else publish(plane, record, name))
        ports.append(_port(write, record.canonical_bytes(), verified=verified))
    ports += [_port(source.reservation.publication, source.allocation.canonical_bytes(), verified=verified),
        _port(source.specification.publication, source.specification.selection.canonical_bytes(), verified=verified)]
    commitment = committed(E1CommitmentConfig('config.'+COMMIT_KEY, sources))
    if defect == 'changed-source':
        commitment = replace(commitment, sources=(replace(commitment.sources[0], object_fingerprint='f'*64), *commitment.sources[1:]))
    write = publish(plane, commitment, 'ordinary.commit')
    if defect != 'missing-commitment':
        ports.append(_port(write, commitment.canonical_bytes(), dependency=defect != 'external-commitment', verified=verified))
    dependency = DependencyReceiptBinding('receipt.ordinary.commit', COMMIT_KEY if defect != 'wrong-receipt' else 'foreign.commit', (write.materialization.materialization_id,))
    context = _context(config, ports, 'history', dependencies=() if defect in ('missing-commitment', 'external-commitment') else (dependency,))
    context = _prepare_history_context(context, verified, source)
    _block_science(monkeypatch)
    if defect is None:
        try:
            assert _decode(context, 'history')[:2] == (config, source)
        finally:
            for port in context.input_ports:
                port.close()
    else:
        class NeverNative:
            @property
            def parent_contact(self):
                return _blocked()
        with pytest.raises(ValueError, match='commitment|complete typed'):
            E1NativeRunner('history').execute_with_native_subwork(context, NeverNative())


@pytest.mark.parametrize('defect', ('missing-commitment', 'missing-history-edge', 'changed-committed-source'))
def test_stock_compiler_refuses_incomplete_or_changed_pre_native_commitment(e1, monkeypatch, defect):
    draft, qualifications = prospective(e1)
    _block_science(monkeypatch)
    if defect == 'missing-commitment':
        draft = replace(draft, operations=tuple(o for o in draft.operations if o.node_id != COMMIT_KEY),
            links=tuple(l for l in draft.links if l.consumer_node_id != COMMIT_KEY and l.producer_node_id != COMMIT_KEY),
            selected_operation_ids=tuple(n for n in draft.selected_operation_ids if n != COMMIT_KEY))
    elif defect == 'missing-history-edge':
        selected = next(l.edge_id for l in draft.links if l.producer_node_id == COMMIT_KEY)
        draft = replace(draft, links=tuple(l for l in draft.links if l.edge_id != selected))
    else:
        operation = next(o for o in draft.operations if o.node_id == COMMIT_KEY)
        config = decode_canonical_bytes(operation.config_payload.encode(), E1CommitmentConfig, maximum_bytes=None)
        config = replace(config, sources=(replace(config.sources[0], source_id='foreign.source'), *config.sources[1:]))
        changed = RecursiveOperationSpec.from_config(node_id=operation.node_id, selection=operation.selection,
            config_id=config.config_id, config=config, obligation_ids=operation.obligation_ids, resource_budget=operation.resource_budget)
        draft = replace(draft, operations=tuple(changed if o.node_id == COMMIT_KEY else o for o in draft.operations))
    factories = operation_factories()
    registry = CapabilityRegistry('registry.software.e1', tuple(sorted((f.manifest for f in factories), key=lambda m: m.registry_id)))
    with pytest.raises(ValueError, match='port|commitment|four-phase|thins|scientific operands'):
        compile_recursive_wave(draft=draft, registrations=tuple(f.registration for f in factories), registry=registry,
            implementation_commit='a'*40, qualifications=qualifications, known_design_inputs=draft.prospective_draft.design_inputs,
            output_codecs={k: v for f in factories for k, v in f.output_codecs.items()})


@pytest.mark.parametrize('defect', (None, 'sidecar-locator', 'sidecar-hash', 'sidecar-size', 'sidecar-id', 'sidecar-root', 'missing-commit'))
def test_prior_publication_authentication_retains_exact_original_sidecar_and_commit(e1, monkeypatch, defect):
    plane, sources, _ = e1
    _block_science(monkeypatch)
    first = sources[0]
    publication = first.reservation.publication
    if defect and defect.startswith('sidecar-'):
        changes = {'sidecar-locator': {'relative_path': 'foreign/manifest.json'}, 'sidecar-hash': {'physical_sha256': 'f'*64},
            'sidecar-size': {'size_bytes': publication.manifest_materialization.size_bytes+1},
            'sidecar-id': {'materialization_id': 'foreign.materialization'}, 'sidecar-root': {'storage_root_id': 'foreign.root'}}
        sidecar = replace(publication.manifest_materialization, **changes[defect])
        if defect == 'sidecar-root':
            publication = replace(publication, materialization=replace(publication.materialization, storage_root_id='foreign.root'),
                manifest_materialization=sidecar)
        else:
            publication = replace(publication, manifest_materialization=sidecar)
        reservation = replace(first.reservation, publication=publication)
        # Rebind the frozen selection to the hypothetical changed reservation,
        # with an actual publication, so the specific sidecar join is tested.
        from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import identity
        selection = replace(first.specification.selection, reservation=identity(reservation))
        specification = replace(first.specification, selection=selection, publication=publish(plane, selection, 'selection.sidecar-control'))
        sources = tuple(replace(s, reservation=reservation, specification=specification) for s in sources)
    config = E1CommitmentConfig('config.'+COMMIT_KEY, sources)
    if defect == 'missing-commit':
        original = publication.materialization.relative_path
        from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
        manifest = decode_artifact_manifest(plane.root.resolve(original+'.manifest.json', for_write=False).read_bytes())
        marker = plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
        moved = marker.with_name(marker.name+'.software-control')
        marker.rename(moved)
    try:
        if defect is None:
            assert authenticate_prior_publications(plane, (SimpleNamespace(record=config),)) is None
            assert authenticate_prior_publications(plane, (SimpleNamespace(record=object()),)) is None
        else:
            with pytest.raises((ValueError, ArtifactIdentityConflict)):
                authenticate_prior_publications(plane, (SimpleNamespace(record=config),))
    finally:
        if defect == 'missing-commit':
            moved.rename(marker)


def test_e1_declarations_preserve_canonical_manifest_and_provider_contracts(monkeypatch):
    from empirical_lawhood.adapters.composition.discovery import manifest
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings as owner
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import (
        E1AdjudicationConfig, E1OperationConfig, PHASES, operation_declarations,
        operation_manifests, operation_registrations,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import (
        E1FactorAssessment, E1FactorProduct, E1HistoryAllocation, E1HistorySource,
        E1PopulationResult, E1ScientificSelection,
    )
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission

    def _historical_manifests():
        values = []
        for role, inputs, output, _ in PHASES:
            values.append(manifest(role, E1OperationConfig, CapabilityKind.SIMULATOR if role == 'history'
                else CapabilityKind.TRANSFORM if role == 'measure' else CapabilityKind.FALSIFIER,
                tuple(sorted({E1OperationConfig.SCHEMA, *(t.SCHEMA if t else MATRIX_ARRAY_SCHEMA for _, t in inputs)})),
                tuple(sorted({output.SCHEMA, *((MATRIX_ARRAY_SCHEMA,) if role in ('history', 'measure') else ())})),
                EvidenceCeiling.RESPONSE, OutcomeAccess.EVALUATION_SEALED, None, namespace=NAMESPACE, resources=BUDGET,
                read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
                implementation_id=NAMESPACE+'.full-paired-history-'+role+'.v1',
                conformance_ids=('complete-four-family-clock-census', 'independent-full-numerical-witness', 'prospective-issued-context-required')))
        value = manifest('adjudicate', E1AdjudicationConfig, CapabilityKind.EVALUATOR,
            tuple(sorted((E1AdjudicationConfig.SCHEMA, E1FactorProduct.SCHEMA, E1FactorAssessment.SCHEMA))),
            tuple(sorted((E1PopulationResult.SCHEMA, ScientificAdjudicationRecord.SCHEMA))),
            EvidenceCeiling.RESPONSE, OutcomeAccess.EVALUATOR_REVEAL, None, namespace=NAMESPACE, resources=BUDGET,
            read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
            implementation_id=NAMESPACE+'.frozen-full-family-recurrence-survival.v1',
            conformance_ids=('complete-risk-censoring-denominators', 'explicit-frozen-estimand-endpoints', 'issued-separate-reveal-required'))
        values.append(replace(value, permissions=tuple(sorted((*value.permissions, CapabilityPermission.REVEAL_OUTCOMES)))))
        values.append(manifest('commit', E1CommitmentConfig, CapabilityKind.TRANSFORM,
            tuple(sorted((E1CommitmentConfig.SCHEMA, E1HistoryAllocation.SCHEMA, E1ScientificSelection.SCHEMA, E1HistorySource.SCHEMA))),
            (E1Commitment.SCHEMA,), EvidenceCeiling.RESPONSE, OutcomeAccess.OUTCOME_BLIND, None, namespace=NAMESPACE,
            resources=BUDGET, read_permission=CapabilityPermission.READ_FROZEN_MODELS,
            implementation_id=NAMESPACE+'.prior-protected-source-commitment.v1',
            conformance_ids=('complete-protected-source-census', 'prior-publication-identity-joins', 'pure-pre-native-freeze')))
        return tuple(values)

    # Declaration discovery must never construct a runner or touch science.
    for name in ('E1NativeRunner', 'E1Runner', 'E1Adjudicator', 'E1Committer'):
        monkeypatch.setattr(owner, name, _blocked)
    declarations = operation_declarations()
    assert len(declarations) == 6
    assert tuple(m.canonical_bytes() for m in operation_manifests()) == tuple(
        m.canonical_bytes() for m in _historical_manifests())
    factories = operation_factories()
    registrations = operation_registrations()
    for declaration, factory, registration in zip(declarations, factories, registrations, strict=True):
        assert declaration.manifest() == factory.manifest
        # Hook functions are newly allocated by each cold declaration; compare all
        # non-callable registration contracts and keep native/reveal hooks explicit.
        from dataclasses import fields
        for field in fields(registration):
            if not callable(getattr(registration, field.name)):
                assert getattr(registration, field.name) == getattr(factory.registration, field.name)
        assert factory.binding.capability_implementation_sha256 == factory.manifest.implementation_sha256
    history = registrations[0]
    assert history.native_effect and history.complete_unit_census and callable(history.native_work_preparer)
    assert registrations[-2].barrier.value == 'REVEAL'
    assert registrations[-2].adjudication_output_id == 'adjudication'
    assert registrations[-1].publication_requirements[0].requirement_id == NAMESPACE+'.prior-publications.v1'
