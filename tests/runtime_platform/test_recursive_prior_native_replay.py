# SPDX-License-Identifier: MPL-2.0
"""Tiny historical native-custody controls; no entry token or native computation.

All contacts, source pins and completion labels are explicit exposed software
fixtures. Only their actual stored bytes and custody joins are tested. No issue,
source qualification or scientific authority follows from these declarations.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_qualified_parents as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityPermission, CapabilityRequirement
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition,
    NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, NativeSubworkUncertainContact,
)
from empirical_lawhood.runtime.plans import (
    ArtifactOutputSpec, BarrierKind, ExecutionPlan, ExecutionTask, ExternalInputSpec, PlanLane,
    ScientificInputRole, ScientificInputSpec, ScientificStage,
)
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding, RecursivePriorNativeBinding
from tests.runtime_platform.test_native_subwork import ExposedInput, _plane

BUDGET = ResourceBudget(1, 1_000_000, 0, 1, 4096, 8192)
RAW_SCHEMA = 'empirical-lawhood/source/checksummed-uninterpreted-public-bytes'


def _pin(key, schema):
    return ObjectIdentity(key, schema, '1.0.0', sha256(key.encode()).hexdigest())


def _manifest(plane, written):
    return decode_artifact_manifest(plane.root.resolve(written.materialization.relative_path+'.manifest.json',
        for_write=False).read_bytes())


def _record(plane, record, key, *, sealed=False):
    return _manifest(plane, plane.write(ArtifactWriteRequest(key, 'inputs/'+key+'.json', record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.'+key, 'inputs', record.canonical_bytes(),
        Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED if sealed else Access.OUTCOME_BLIND)))


def _blocked_progress(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail('retained native replay requested new contact, entry token or execution')
    monkeypatch.setattr(ExternalNativeEffectContactStore, 'begin', blocked)
    for method in ('begin', 'contact', 'freeze_roster', 'complete', 'publish_output'):
        monkeypatch.setattr(ExternalNativeSubworkStore, method, blocked)
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor, 'execute_deadline_free', blocked)


def _stored(tmp_path, *, missing_receipt=False, unknown_stream=False, foreign_configuration=False, subwork_count=None):
    """Publish historical fixture records directly, creating no live capability."""
    plane = _plane(tmp_path/'tiny-original-custody')
    config = ExposedInput('config.synthetic.native', 'fixed dummy configuration')
    source = ExposedInput('source.synthetic', 'tiny retained input')
    stream = ExposedInput('stream.synthetic', 'already-consumed dummy stream bytes; no RNG')
    config_manifest = _record(plane, config, config.selected_id)
    source_manifest = _record(plane, source, source.selected_id)
    stream_manifest = _record(plane, stream, stream.selected_id)
    dependency_record = ExposedInput('product.dependency', 'tiny blind dependency')
    dep_manifest = _record(plane, dependency_record, 'artifact.synthetic.dependency')
    product = ExposedInput('product.native', 'dummy native phase metadata; software only')
    product_manifest = _record(plane, product, 'artifact.synthetic.native', sealed=True)
    run = 'run.synthetic-prior-native'

    def task(task_id, output_manifest, *, native=False):
        cfg = CapabilityConfigRef(config.selected_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
            config.fingerprint(), config_manifest.logical.logical_artifact_id)
        access = Access.EVALUATION_SEALED if native else Access.OUTCOME_BLIND
        req = CapabilityRequirement('synthetic.'+task_id, '1.0.0', CapabilityKind.SIMULATOR if native else CapabilityKind.SOURCE,
            cfg, (config.SCHEMA,), (product.SCHEMA,),
            (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
            EvidenceCeiling.RESPONSE, access, BUDGET)
        externals = (ExternalInputSpec('input.config.'+task_id, config_manifest.logical.logical_artifact_id,
            config.fingerprint(), config.SCHEMA, 'application/json', len(config.canonical_bytes()),
            Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None),)
        if native:
            externals += tuple(ExternalInputSpec('input.'+kind+'.'+task_id, manifest.logical.logical_artifact_id,
                record.fingerprint(), record.SCHEMA, 'application/json', len(record.canonical_bytes()),
                Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None)
                for kind, record, manifest in (('source', source, source_manifest), ('stream', stream, stream_manifest)))
        edges = (ScientificInputSpec('edge.dependency.native', 'dependency-product', ScientificInputRole.HISTORY,
            'dependency', 'dependency.product', None, dep_manifest.logical.logical_artifact_id,
            dep_manifest.logical.logical_artifact_id, source.SCHEMA, 'application/json', 4096,
            Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, BarrierKind.NONE),) if native else ()
        p = output_manifest
        output = ArtifactOutputSpec(task_id+'.product', p.logical.logical_artifact_id, p.materialization.relative_path,
            p.logical.payload_schema, p.logical.profile, p.logical.media_type, p.logical.visibility_ceiling, (), p.logical.outcome_access)
        return ExecutionTask(task_id, ScientificStage.ACQUIRE if native else ScientificStage.PREPARE, req,
            sha256(task_id.encode()).hexdigest(), ('dependency',) if native else (), externals, (output,), (),
            BarrierKind.NONE, 1, ('obligation.synthetic.'+task_id,), scientific_inputs=edges)

    dependency, native = task('dependency', dep_manifest), task('native', product_manifest, native=True)
    plan = ExecutionPlan('plan.synthetic-prior-native', PlanLane.PROSPECTIVE,
        _pin(run, 'empirical-lawhood/runtime/run-plan'), '2'*64, '3'*40, (dependency, native), True,
        candidate=_pin('candidate.synthetic', 'empirical-lawhood/runtime/executable-study-candidate'),
        issued_extension_set=_pin('extensions.synthetic', 'empirical-lawhood/runtime/issued-extension-set'),
        execution_resource_envelope_spec=_pin('resources.synthetic', 'empirical-lawhood/runtime/execution-resource-envelope-spec'),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    plan_id = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    input_ids = tuple(sorted(p.materialization.materialization_id for p in
        (config_manifest, source_manifest, stream_manifest, dep_manifest)))
    def receipt(task, manifest, inputs):
        attempt = run+'.'+task.task_id+'.attempt-001'
        value = CanonicalTaskReceipt('receipt.'+attempt, run, task.task_id, attempt, plan.implementation_commit,
            inputs, (manifest.materialization,), (manifest.logical,),
            (ReceiptCheck('synthetic-historical-phase-custody', True, ()),), OperationalStatus.SUCCEEDED, ())
        ExternalTaskReceiptStore(plane).commit(value, visibility_ceiling=Visibility.PROSPECTIVE,
            outcome_access=task.capability.requested_outcome_access)
        return value
    dep_receipt = receipt(dependency, dep_manifest, (config_manifest.materialization.materialization_id,))
    native_receipt = receipt(native, product_manifest, input_ids)
    by_task = {'dependency': dep_receipt, 'native': native_receipt}
    parent = NativeEffectContact(run, native.task_id, native_receipt.attempt_id, plan_id,
        ObjectIdentity.from_record(native.task_id, native), plan.implementation_commit, input_ids, (dep_receipt.receipt_id,))
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=plan_id,
        visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
    # Direct historical publication: no contacts.begin or live creator token.
    contact_path = contacts._path(run, native.task_id)
    parent_lineage = ArtifactLineageParent(plan_id, Visibility.PROSPECTIVE, Access.EVALUATION_SEALED)
    plane.write(ArtifactWriteRequest('native-contact.'+run+'.'+sha256(native.task_id.encode()).hexdigest(), contact_path,
        parent.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'native-contacts.'+run,
        'runs/'+run+'/native-contacts', parent.canonical_bytes(), Visibility.PROSPECTIVE, (Visibility.PROSPECTIVE,),
        Access.EVALUATION_SEALED, lineage_parents=(parent_lineage,)))
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent)
    config_id = ObjectIdentity.from_record(config.selected_id, config)
    substitutions = {
        'sha': {'object_fingerprint': 'f'*64},
        'schema': {'object_schema': 'empirical-lawhood/tests/foreign-native-configuration'},
        'id': {'object_id': 'config.foreign-native'},
    }
    selected_config = replace(config_id, **substitutions[foreign_configuration]) if foreign_configuration else config_id
    names = ('one', 'two') if subwork_count is None else tuple(f'{index:03}' for index in range(subwork_count))
    definitions = tuple(NativeSubworkDefinition('subwork.'+name, 'synthetic.dummy-return', parent, selected_config,
        (ObjectIdentity.from_record(source.selected_id, source),), '4'*64, '5'*64, input_ids,
        (ObjectIdentity.from_record(stream.selected_id, stream),),
        (NativeSubworkOutput('dummy', RAW_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, 'text/plain'),)) for name in names)
    roster = NativeSubworkRoster('selected.native-subwork', parent, tuple(d.identity for d in definitions))
    relative, token = store._roster_path(parent, roster.roster_id), store._roster_key(parent, roster.roster_id)
    parents = store._parents(plan_id)
    plane.write(ArtifactWriteRequest('native-subwork-roster.'+token, relative, roster.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'native-subwork-rosters.'+run+'.'+sha256(native.task_id.encode()).hexdigest(),
        store._roster_root(parent), roster.canonical_bytes(), Visibility.PROSPECTIVE,
        tuple(p.visibility_ceiling for p in parents), Access.EVALUATION_SEALED, lineage_parents=parents))
    inspections, requests = [], []
    for definition in definitions:
        dm, _ = store._write_control(definition, 'definition', definition, store._parents(plan_id))
        begin = NativeSubworkBegin(definition.identity)
        bm, _ = store._write_control(definition, 'begin', begin, store._parents(definition.identity))
        begin_id = ObjectIdentity.from_record(store._id(definition, 'begin'), begin)
        contact = NativeSubworkContact(begin_id)
        cm, _ = store._write_control(definition, 'contact', contact, store._parents(begin_id))
        contact_id = ObjectIdentity.from_record(store._id(definition, 'contact'), contact)
        parents = store._parents(definition.identity, contact_id)
        payload = b'dummy retained byte return; no mathematical computation'
        output = _manifest(plane, plane.write(ArtifactWriteRequest(store._id(definition, 'output.dummy'),
            store._root(definition)+'/outputs/dummy', RAW_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, 'text/plain',
            store._id(definition, 'outputs'), store._root(definition)+'/outputs', payload, Visibility.PROSPECTIVE,
            tuple(p.visibility_ceiling for p in parents), Access.EVALUATION_SEALED, lineage_parents=parents)))
        completion = NativeSubworkCompletion(definition.identity, contact_id, OperationalStatus.SUCCEEDED, ('dummy',), (),
            () if unknown_stream else definition.streams, (), definition.streams if unknown_stream else (),
            InquiryCost(None, None, None), 'DECLARED SOFTWARE FIXTURE; NO NATIVE COST WAS MEASURED', None, ())
        completion_manifest, _ = store._write_control(definition, 'completion', completion, parents)
        outputs = tuple(sorted((output, completion_manifest), key=lambda m: m.logical.logical_artifact_id))
        native_run, native_task, attempt = store._receipt_locator(definition)
        subreceipt = CanonicalTaskReceipt('receipt.'+attempt, native_run, native_task, attempt, plan.implementation_commit,
            tuple(sorted((*input_ids, dm.materialization.materialization_id, bm.materialization.materialization_id,
                cm.materialization.materialization_id))), tuple(m.materialization for m in outputs), tuple(m.logical for m in outputs),
            (ReceiptCheck('native-subwork-exact-completion-census', True, ()),), OperationalStatus.SUCCEEDED, ())
        if not missing_receipt:
            store.receipts.commit(subreceipt, visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
            inspections.append(store.recover(definition))
        requests.append(RecursivePriorNativeBinding(native.task_id, definition.identity,
            ObjectIdentity.from_record('completion.'+definition.subwork_id, completion),
            ObjectIdentity.from_record(subreceipt.receipt_id, subreceipt)))
    binding = RecursivePriorExecutionBinding('binding.synthetic-original-native',
        _pin('issue.synthetic', 'empirical-lawhood/runtime/issued-executable-study-manifest'),
        _pin('authority.synthetic', 'empirical-lawhood/planning/study-operation-authority'),
        _pin('package.synthetic', 'empirical-lawhood/api/experiment-package'), plan_id, run, native.task_id,
        ObjectIdentity.from_record(native_receipt.receipt_id, native_receipt), product_manifest.logical.logical_artifact_id,
        ObjectIdentity.from_record(product.selected_id, product), native_subwork=tuple(requests))
    assert contacts._live_creators == set()
    return SimpleNamespace(plane=plane, plan=plan, binding=binding, by_task=by_task, store=store, parent=parent,
        definitions=definitions, inspections=tuple(inspections), native=native)


@pytest.fixture
def retained(tmp_path, monkeypatch):
    _blocked_progress(monkeypatch)
    return _stored(tmp_path)


def _replay(fixture, *, binding=None, plan=None, by_task=None):
    return owner._prior_native_subwork(fixture.plane, binding or fixture.binding, plan or fixture.plan,
        fixture.by_task if by_task is None else by_task)


def test_actual_retained_native_census_reopens_original_known_bytes_without_entry_token(retained, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('retained native read attempted recovery or receipt publication')
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', forbidden)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', forbidden)
    root = Path(retained.plane.root.contract.canonical_path)
    before = {str(p): sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    values = _replay(retained)
    assert tuple(v.binding for v in values) == retained.binding.native_subwork
    assert tuple(v.inspection for v in values) == retained.inspections
    assert all(v.inspection.state is NativeSubworkState.COMPLETED for v in values)
    assert all(v.inspection.completion.unknown_streams == () for v in values)
    assert all(v.inspection.completion.cost.cpu_seconds is None for v in values)
    assert retained.store.parent_contacts._live_creators == set()
    after = {str(p): sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    assert after == before
    assert decode_canonical_bytes(retained.binding.native_subwork[0].canonical_bytes(), RecursivePriorNativeBinding,
        maximum_bytes=4096) == retained.binding.native_subwork[0]


@pytest.mark.parametrize('field', ('definition', 'completion', 'receipt'))
def test_exact_requested_native_identity_substitutions_refuse(retained, field):
    first = retained.binding.native_subwork[0]
    bad = replace(first, **{field: replace(getattr(first, field), object_fingerprint='0'*64)})
    with pytest.raises((PermissionError, ValueError, ArtifactPlaneError)):
        _replay(retained, binding=replace(retained.binding, native_subwork=(bad, *retained.binding.native_subwork[1:])))


@pytest.mark.parametrize('mutation', ('config', 'task-id', 'attempt', 'inputs', 'dependency-receipt', 'missing-task', 'missing-receipt'))
def test_original_contact_binds_actual_task_config_inputs_and_dependency_graph(retained, mutation):
    plan, receipts = retained.plan, dict(retained.by_task)
    if mutation == 'config':
        native = replace(retained.native, capability=replace(retained.native.capability,
            config=replace(retained.native.capability.config, content_sha256='f'*64)))
        plan = replace(plan, tasks=(plan.tasks[0], native))
    elif mutation == 'task-id':
        first = replace(retained.binding.native_subwork[0], task_id='dependency')
        with pytest.raises((PermissionError, ValueError)):
            _replay(retained, binding=replace(retained.binding, native_subwork=(first,)))
        return
    elif mutation == 'attempt':
        receipts['native'] = replace(receipts['native'], attempt_id='attempt.other')
    elif mutation == 'inputs':
        receipts['native'] = replace(receipts['native'], input_materialization_ids=())
    elif mutation == 'dependency-receipt':
        receipts['dependency'] = replace(receipts['dependency'], receipt_id='receipt.other-dependency')
    elif mutation == 'missing-task':
        plan = replace(plan, tasks=(plan.tasks[0],))
    else:
        del receipts['native']
    with pytest.raises((PermissionError, ValueError), match='census|entered task'):
        _replay(retained, plan=plan, by_task=receipts)


def test_native_requested_census_is_closed_unique_and_bounded(retained):
    first = retained.binding.native_subwork[0]
    with pytest.raises(ValueError, match='census'):
        replace(retained.binding, native_subwork=(first, first))
    with pytest.raises(ValueError, match='census'):
        replace(retained.binding, native_subwork=tuple(replace(first,
            definition=replace(first.definition, object_id='subwork.'+str(i)),
            completion=replace(first.completion, object_id='completion.subwork.'+str(i))) for i in range(217)))
    assert _replay(retained, binding=replace(retained.binding, native_subwork=())) == ()


@pytest.mark.parametrize('mode', ('missing-receipt', 'unknown-stream'))
def test_unknown_completion_or_stream_never_grants_retained_success(tmp_path, monkeypatch, mode):
    _blocked_progress(monkeypatch)
    fixture = _stored(tmp_path, missing_receipt=mode == 'missing-receipt', unknown_stream=mode == 'unknown-stream')
    def forbidden(*args, **kwargs):
        pytest.fail('incomplete native read attempted recovery or receipt publication')
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', forbidden)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', forbidden)
    root = Path(fixture.plane.root.contract.canonical_path)
    before = {str(p): sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    with pytest.raises((PermissionError, NativeSubworkUncertainContact), match='known original|no automatic retry'):
        _replay(fixture)
    after = {str(p): sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    assert after == before


@pytest.mark.parametrize('member', ('definition', 'completion', 'receipt', 'output'))
def test_changed_original_stored_bytes_refuse_exact_custody(retained, member):
    definition = retained.definitions[0]
    if member == 'receipt':
        run, task, attempt = retained.store._receipt_locator(definition)
        relative = f'runs/{run}/receipts/{task}/{attempt}.json'
    elif member == 'output':
        relative = retained.store._root(definition)+'/outputs/dummy'
    else:
        relative = retained.store._root(definition)+'/'+member+'.json'
    path = retained.plane.root.resolve(relative, for_write=False)
    raw = path.read_bytes()
    path.write_bytes(raw+b' ')
    with pytest.raises((ValueError, PermissionError, ArtifactPlaneError)):
        _replay(retained)


@pytest.mark.parametrize('configuration', ('sha', 'schema', 'id'))
def test_recovered_mathematical_configuration_matches_actual_task_configuration(tmp_path, monkeypatch, configuration):
    _blocked_progress(monkeypatch)
    fixture = _stored(tmp_path, foreign_configuration=configuration)
    def blocked(*args, **kwargs):
        pytest.fail('foreign native configuration reached recovery or protected native output verification')
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', blocked)
    from empirical_lawhood.runtime import artifacts
    monkeypatch.setattr(artifacts, 'verify_artifact_manifests', blocked)
    with pytest.raises(PermissionError, match='config'):
        _replay(fixture)
