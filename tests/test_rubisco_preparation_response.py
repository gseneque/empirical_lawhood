# SPDX-License-Identifier: MPL-2.0
"""Exposed full-custody controls for paired physical response and finite errors."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import replace
from decimal import Decimal
import json
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_read as reader
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_operation as shared
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_native
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import BOHR_ANGSTROM
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import read_preparation_prefix
from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import prepare_formation_coordinate
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootScopedAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_action_read import direction_values
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeConfig, PeriodicProbeResult
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import PreparationResponseAssessment, freeze_response_predictions
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import POSITIONS, prepare_response_design, prepare_response_frame, response_effects
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import prepare_response_center, prepare_response_point, read_response_center
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import preparation_response_draft
from empirical_lawhood.execution.local.execution import prepare_worker_invocation

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.runtime_platform.test_worker_preflight import _original_task
from tests import test_rubisco_active_preparation as preparation

fixture = preparation.fixture
matched = preparation.matched
prefix = preparation.prefix


def response_custody(f, config, center_bytes, directory):
    plane = _plane(directory, binary_codecs=(owner.CENTER_CODEC,))
    records = (('config', config.identity, config), *owner.native_input_records(config, f.model, f.sources),
               ('native-center-bytes', config.center.center_bytes, center_bytes))
    manifests = []
    for name, pin, record in records:
        binary = type(record) is bytes
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import history_parent
        parent = history_parent(config, name)
        artifact_id = pin.object_id if parent is None else next(p.artifact.artifact_id for p in parent.products if p.record == pin)
        result = plane.write(ArtifactWriteRequest(artifact_id, 'inputs/' + name + ('.bin' if binary else '.json'),
            pin.object_schema, ArtifactProfile.RAW_SOURCE_BYTES if binary else ArtifactProfile.CANONICAL_JSON,
            'application/octet-stream' if binary else 'application/json', 'exposed.response.inputs', 'inputs',
            record if binary else record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(result.materialization.relative_path + '.manifest.json', for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda m: m.materialization.materialization_id))
    verified = tuple(sorted((VerifiedArtifactInput(m.logical, m.materialization) for m in manifests), key=lambda r: r.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id = {m.logical.logical_artifact_id: m for m in manifests}
    def ports():
        return tuple(plane.open(by_id[b.artifact_id], binding=b, maximum_bytes=b.size_bytes) for b in bindings)
    manifest = owner.operation_declaration().manifest()
    node = owner.node_id(config)
    context = TaskContext('exposed.response', node, 'exposed.response.' + node + '.attempt-001',
        CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.identity.object_id),
        bindings, ports(),
        (WorkerOutputPort(node + '.assessment', reader.PreparationResponsePointReadout.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.response-assessment'),
         WorkerOutputPort(node + '.product', PeriodicProbeResult.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.response-product')),
        manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, owner.resource_budget(config), WorkerIsolationProfile.TRUSTED_LOCAL)
    runner = owner.PreparationResponseRunner()
    task = _original_task(runner, context, SimpleNamespace(verified_inputs=verified))
    plan = ObjectIdentity('plan.exposed.response', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1' * 64)
    contract = prepare_worker_invocation(runner, context, verified, implementation=config.original.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        native_effect=True, native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None, contract.native_preparation_error
    context = replace(context, prepared_invocation=contract)
    f.contexts.append(context)
    store = _store(plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)
    def fresh():
        value = replace(context, input_ports=ports())
        f.contexts.append(value)
        return value
    return SimpleNamespace(plane=plane, context=context, store=store, fresh=fresh)


def paired_preparation(prefix, monkeypatch, *, environmental=False):
    f = prefix
    coordinates = tuple((name, prepare_formation_coordinate(representation=row[0], prepared=row[2],
        site_id=f.config.prefix.conditional.state_census[0][0]))
        for name, row in zip(('m1-i95m', 'm1-wt'), f.models[:2], strict=True))
    root = ObjectIdentity('assessment.exposed.original-root', InitialRootScopedAssessment.SCHEMA,
        InitialRootScopedAssessment.VERSION, '8' * 64)
    environment = None
    if environmental:
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import prepare_response_environment
        rows = dict(zip(('m1-i95m', 'm1-wt'), f.models[:2], strict=True))
        environment = prepare_response_environment(models={name: row[0] for name, row in rows.items()},
            preparations={name: row[2] for name, row in rows.items()},
            prototypes={name: row[1] for name, row in rows.items()}, formation_coordinates=coordinates,
            region='SELECTED_COMMON_PROTEIN_RESIDUES', residue_keys=(('lsu.01', 1),))
    design = prepare_response_design(prefix=f.config.prefix, root_assessment=root,
        formation_coordinates=coordinates, environment=environment)
    centers, frames, raw, fixtures, readouts = {}, {}, {}, {}, []
    for name, row in zip(('m1-i95m', 'm1-wt'), f.models[:2], strict=True):
        model, prototype, prepared, raw_top, raw_xyz, coordinate_bytes = row
        temporary = f.tmp_path / name
        temporary.mkdir()
        sources = preparation.original.prepare_raw_sources(prototype, raw_top, raw_xyz)
        original = replace(f.config.original, config_id='config.exposed.relaxation.' + name, model_name=name,
            prototype=prototype, preparation=prepared.identity, preparation_size_bytes=prepared.canonical_size_bytes(),
            seeds=prepared.seeds, representation_size_bytes=model.canonical_size_bytes(), raw_sources=sources.identity,
            raw_source_size_bytes=sources.canonical_size_bytes(), work_directory=str(temporary / 'prefix-work'))
        config = preparation.owner.ActivePreparationPrefixConfig('config.exposed.prefix.' + name, original, f.config.prefix)
        member = SimpleNamespace(**(vars(f) | dict(model=model, prototype=prototype, prepared=prepared,
            raw_top=raw_top, raw_xyz=raw_xyz, coordinates=coordinate_bytes, sources=sources, config=config, tmp_path=temporary)))
        custody = preparation.custody(member)
        preparation.install_exposed_operator(member, monkeypatch)
        result = preparation.owner.ActivePreparationPrefixRunner().execute_with_native_subwork(custody.context, custody.store)
        result = decode_canonical_bytes(result.outputs[1].payload, preparation.owner.ActivePreparationPrefixResult, maximum_bytes=16 * 2**20)
        readout, arrays, _ = read_preparation_prefix(config=config, representation=model, prepared=prepared,
            coordinate_bytes=coordinate_bytes, original_result=result, native_subwork=custody.store,
            assessor_source=model.material.sources[0], readout_id='readout.exposed.prefix.' + name, include_operands=True)
        assert readout.assessment_error is None, readout.assessment_error
        readouts.append(readout)
        checkpoints = {r.checkpoint.identity: r.checkpoint for r in readout.assessment.checkpoints}
        for state in readout.assessment.positions:
            checkpoint = checkpoints[state.checkpoint]
            center, data = prepare_response_center(design=design, readout=readout, position=state.position,
                checkpoint=checkpoint, checkpoint_arrays=arrays[checkpoint.identity])
            centers[name, state.position], raw[name, state.position] = center, data
            if state.position == 'initial':
                frames[name] = prepare_response_frame(design=design, model_name=name, checkpoint=checkpoint,
                    arrays=arrays[checkpoint.identity], prototype=prototype)
        member.probe = PeriodicProbeConfig('config.exposed.response-base.' + name, prototype, sources.identity,
            model.canonical_size_bytes(), sources.canonical_size_bytes(), original.implementation,
            str(temporary / 'response-work'), original.provenance)
        fixtures[name] = member
    return SimpleNamespace(design=design, centers=centers, frames=frames, raw=raw, fixtures=fixtures,
        assessor=f.model.material.sources[0], tmp_path=f.tmp_path, readouts=tuple(readouts))


def _compile_admission(paired, response=None):
    """Disclosed contribution references test compilation, not source custody.

    The public lifecycle separately exports and imports the original products.
    This control checks both destination worlds before any new native work.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import selected_prefix_scope
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_scope
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import operation_declaration
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_supply import prepare_preparation_supply
    from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
    from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
    from empirical_lawhood.science.identity.references import ArtifactIdentity
    from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
    from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.execution.capabilities import CapabilityRegistry
    from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
    groups = [('prefix', paired.readouts, selected_prefix_scope(paired.design.prefix))]
    if response is not None:
        groups.append(('response', (response,), response_scope(paired.design)))
    parents = []
    for name, records, scope in groups:
        products = tuple(ContributionProduct('product.exposed.' + name + '.' + str(index), record.identity,
            ArtifactIdentity('artifact.exposed.' + name + '.' + str(index), 'disclosed-compilation-reference',
                record.SCHEMA, record.fingerprint(), 'application/json', record.canonical_size_bytes()),
            ObjectIdentity('receipt.exposed.compilation', CanonicalTaskReceipt.SCHEMA, CanonicalTaskReceipt.VERSION, '1' * 64),
            ContributionRole.RETAINED_ANALYSIS_INPUT, EvidenceCeiling.NON_PROMOTABLE,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
            for index, record in enumerate(records))
        parents.append(ContributionManifest('contribution.exposed.compilation.' + name,
            'Can the exact local destination compile?', 'Exposed references, no scientific custody or qualification.',
            scope, products, tuple(sorted((r.identity for r in records), key=lambda p: p.object_id)), ()))
    prepared = prepare_preparation_supply(design=paired.design, original_prefixes=paired.readouts,
        parents=tuple(parents), original_response=response)
    draft, declaration = prepared['draft'], operation_declaration()
    compiled = compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed.preparation-admission', (declaration.manifest(),)),
        implementation_commit='a' * 40, output_codecs=declaration.record_codecs)
    assert compiled.draft == draft
    assert draft.development_study.system == paired.design.prefix.plan
    if response is not None:
        assert parents[0].scope.world_id != draft.development_study.world_id
    _exercise_admission_worker(prepared['config'])
    return draft


def _exercise_admission_worker(config):
    """Exercise the real path-free worker interface and original-byte refusals."""
    from io import BytesIO
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_supply_operation as supply
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import PreparationSupplyResult
    from empirical_lawhood.execution.execution import WorkerInputPort
    manifest = supply.operation_declaration().manifest()
    operands = [(config.identity.object_id, config)] + [
        (config.selection.product(r)[1].artifact.artifact_id, r) for r in config.selection.records]

    def context(*, substitute=False, corrupt=False, omit=False):
        ports = []
        for index, (artifact_id, record) in enumerate(operands):
            if index == 1 and omit:
                continue
            raw = record.canonical_bytes()
            if index == 1 and substitute:
                artifact_id = 'artifact.exposed.substituted'
            if index == 1 and corrupt:
                raw = raw[:-1] + b' '
            binding = WorkerInputBinding(artifact_id, 'materialization.exposed.admission.' + str(index),
                record.SCHEMA, 'application/json', len(raw), VisibilityCeiling.DEVELOPMENT_ONLY,
                OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL)
            ports.append(WorkerInputPort(binding, BytesIO(raw)))
        ports = tuple(sorted(ports, key=lambda p: p.artifact_id))
        return TaskContext('exposed.admission', supply.CAPABILITY, 'exposed.admission.attempt-001',
            CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
                config.fingerprint(), config.identity.object_id), tuple(p.binding for p in ports), ports,
            (WorkerOutputPort(supply.CAPABILITY + '.assessment', PreparationSupplyResult.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.admission'),),
            manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, supply.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)

    runner = supply.PreparationSupplyRunner()
    successful = context()
    output, = runner.execute(successful).outputs
    actual = decode_canonical_bytes(output.payload, PreparationSupplyResult, maximum_bytes=supply.MAX_INPUT)
    assert actual.selection == config.selection
    assert all(p._reader.closed for p in successful.input_ports)
    for changed in (context(substitute=True), context(corrupt=True), context(omit=True)):
        with pytest.raises(ValueError, match='original'):
            runner.execute(changed)
        assert all(p._reader.closed for p in changed.input_ports)


def install_response_operator(paired, monkeypatch):
    calls = []
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: None)
    monkeypatch.setattr(shared, 'authenticate_periodic_engine', lambda *a, **k: None)
    def execute(**kwargs):
        records = dict(kwargs['coordinate_records'])
        point = records['response-point.json']
        effect = point.effect
        key = (effect.model_name, effect.position)
        xyz, base = read_response_center(paired.centers[key], paired.raw[key])
        frame = paired.frames[effect.model_name]
        u, v, w = (direction_values(getattr(frame, role), len(xyz)) for role in ('primary', 'additional', 'challenge'))
        dx = (kwargs['coordinates'] - xyz) / BOHR_ANGSTROM
        stiffness = .2 if effect.position == 'initial' else .3
        coupling = .15
        nonlinear = (.1 if effect.position == 'initial' else .005) * (2 if effect.model_name == 'm1-i95m' else 1)
        gradient = base + stiffness * dx + coupling * (np.vdot(v, dx) * u + np.vdot(u, dx) * v)
        gradient += nonlinear * np.vdot(w, dx)**2 * w
        energy = float(np.vdot(base, dx) + .5 * stiffness * np.vdot(dx, dx)
            + coupling * np.vdot(u, dx) * np.vdot(v, dx) + nonlinear * np.vdot(w, dx)**3 / 3)
        root = kwargs['root']
        for name, record in (*records.items(), ('selection.json', kwargs['selection']),
                ('electronic-settings.json', kwargs['settings']), ('mm-settings.json', kwargs['mm_settings']), ('cell.json', kwargs['cell'])):
            (root / name).write_bytes(record.canonical_bytes())
        (root / 'original.prmtop').write_bytes(kwargs['raw_topology'])
        (root / 'original.inpcrd').write_bytes(kwargs['raw_coordinates'])
        np.save(root / 'coordinate-array.npy', kwargs['coordinates'], allow_pickle=False)
        (root / 'native-observations.jsonl').write_text(''.join(json.dumps(dict(event=event, evaluation=1,
            converged=True, orbital_gradient_norm=0., energy_hartree=energy)) + '\n'
            for event in ('entry', 'electronic-return', 'return')))
        calls.append(effect.effect_id)
        return dict(energy_hartree=energy, gradient_hartree_per_bohr=gradient)
    monkeypatch.setattr(periodic_probe_native, '_execute_periodic_at_coordinates', execute)
    return calls


def run_stage(paired, stage, results, custody_by_result, predictions=(), *, monkeypatch=None,
              preparation_parent=None, diagnostic=None, diagnostic_parent=None):
    predictions = dict(predictions)
    configs = []
    for effect in response_effects(paired.design, stage):
        key = (effect.model_name, effect.position)
        member = paired.fixtures[effect.model_name]
        point = prepare_response_point(design=paired.design, center=paired.centers[key], frame=paired.frames[effect.model_name],
            effect=effect, prototype=member.prototype, center_bytes=paired.raw[key], prediction=predictions.get(key))
        config = owner.PreparationResponseConfig('config.' + point.point_id, member.probe, paired.design,
            paired.centers[key], paired.frames[effect.model_name], point, preparation_parent, diagnostic, diagnostic_parent)
        configs.append(config)
        custody = response_custody(member, config, paired.raw[key], paired.tmp_path / (stage + '-' + str(effect.ordinal)))
        if effect.ordinal == 0 and monkeypatch is not None:
            preparation.assert_sealed_input_reuse(custody.fresh(), owner._decode, monkeypatch)
        result = owner.PreparationResponseRunner().execute_with_native_subwork(custody.context, custody.store)
        parsed = decode_canonical_bytes(result.outputs[1].payload, PeriodicProbeResult, maximum_bytes=16 * 2**20)
        results[effect.effect_id] = parsed
        custody_by_result[parsed.result_id] = custody.store
        if effect.ordinal == 0:
            second = owner.PreparationResponseRunner().execute_with_native_subwork(custody.fresh(), custody.store)
            assert [r.payload for r in second.outputs] == [r.payload for r in result.outputs]
    return tuple(configs)


def test_single_response_point_retains_geometry_and_blocks_rejected_read(prefix, monkeypatch):
    """One complete mocked M50 link, with explicit geometry software substitution."""
    paired = paired_preparation(prefix, monkeypatch)
    calls = install_response_operator(paired, monkeypatch)
    effect = response_effects(paired.design, 'diagnostic')[0]
    key = effect.model_name, effect.position
    member = paired.fixtures[effect.model_name]
    point = prepare_response_point(design=paired.design, center=paired.centers[key], frame=paired.frames[effect.model_name],
        effect=effect, prototype=member.prototype, center_bytes=paired.raw[key])
    config = owner.PreparationResponseConfig('config.'+point.point_id, member.probe, paired.design,
        paired.centers[key], paired.frames[effect.model_name], point)
    custody = response_custody(member, config, paired.raw[key], paired.tmp_path/'single-response-point')
    output = owner.PreparationResponseRunner().execute_with_native_subwork(custody.context, custody.store)
    original = decode_canonical_bytes(output.outputs[1].payload, PeriodicProbeResult, maximum_bytes=16*2**20)
    report = reader.read_response_point(config=config, representation=member.model, center_bytes=paired.raw[key],
        original_result=original, native_subwork=custody.store, assessor_source=paired.assessor,
        readout_id='readout.exposed.single-response')
    assert calls == [effect.effect_id]
    assert report.original.geometry_quality.disposition == 'SCREEN_PASSED'
    assert report.original.geometry_quality.coordinate_sha256 == point.coordinate_sha256
    assert reader.response_values(report, custody.store) is not None
    # Finite arrays remain unavailable when the independent geometric predicate
    # rejects them, even if every electronic/numerical predicate had passed.
    bad_geometry = replace(report.original.geometry_quality, disposition='REJECTED',
        findings=('whole-molecule-bond-deviation',))
    rejected = replace(report, original=replace(report.original, geometry_quality=bad_geometry))
    assert reader.response_values(rejected, custody.store) is None
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis import available_capture
    assert available_capture(rejected) is None
    assert decode_canonical_bytes(report.canonical_bytes(), reader.PreparationResponsePointReadout,
        maximum_bytes=16*2**20) == report


def test_paired_original_response_custody_recovery_and_six_question_assessment(prefix, monkeypatch):
    paired = paired_preparation(prefix, monkeypatch)
    _compile_admission(paired)
    calls = install_response_operator(paired, monkeypatch)
    results, custody = {}, {}
    diagnostic = run_stage(paired, 'diagnostic', results, custody, monkeypatch=monkeypatch)
    draft = preparation_response_draft(diagnostic)
    assert len(draft.operations) == 20 and len(draft.development_study.numerical_view_ids) == 20
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_inquiry as inquiry
    from empirical_lawhood.api.recursive_inquiry import _project_wave_scientific_work
    expected_work = {task: inquiry.scientific_work(draft, task) for task in draft.selected_operation_ids}
    complete_validations = []
    original_configs = inquiry.selected_configs
    def counted_configs(candidate):
        complete_validations.append(candidate)
        return original_configs(candidate)
    with monkeypatch.context() as scoped:
        scoped.setattr(inquiry, 'selected_configs', counted_configs)
        assert _project_wave_scientific_work(draft, draft.selected_operation_ids) == expected_work
        assert complete_validations == [draft]
        endpoint = inquiry.endpoint_projector(draft)
        assert inquiry.endpoint_validator(draft, endpoint) is None
        with pytest.raises(ValueError, match='original local receiver'):
            inquiry.endpoint_validator(draft, replace(endpoint, receiver_id='receiver.substituted'))
        with pytest.raises(ValueError, match='complete stage graph'):
            inquiry.scientific_work_batch(replace(draft, question='Substituted full stage question'),
                draft.selected_operation_ids[:1])
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_translation as translation
    import gc
    import weakref
    reconstructions = []
    construct = translation.preparation_response_draft
    def counted_draft(*args, **kwargs):
        reconstructions.append(True)
        return construct(*args, **kwargs)
    with monkeypatch.context() as scoped:
        scoped.setattr(translation, 'preparation_response_draft', counted_draft)
        with translation.selection_scope(draft) as selection:
            selection_ref = weakref.ref(selection[0])
            assert translation.selected_configs(draft) is selection
            assert _project_wave_scientific_work(draft, draft.selected_operation_ids) == expected_work
            endpoint = inquiry.endpoint_projector(draft)
            inquiry.endpoint_validator(draft, endpoint)
            translation.response_input_origins(draft)
            assert reconstructions == [True]
        del selection
        gc.collect()
        assert selection_ref() is None
        with translation.selection_scope(draft):
            assert reconstructions == [True, True]
            with pytest.raises(ValueError, match='complete stage graph'):
                translation.selected_configs(replace(draft, question='Substituted stage during scoped read'))
        assert reconstructions == [True, True, True]
    with pytest.raises(ValueError, match='effect census'):
        preparation_response_draft(diagnostic[:-1])
    common = dict(representations={name: f.model for name, f in paired.fixtures.items()}, centers=paired.centers,
        frames=paired.frames, center_bytes=paired.raw, native_subwork_for_result=lambda r: custody[r.result_id],
        assessor_source=paired.assessor)
    report, arrays, _ = reader.read_preparation_response(stages=(diagnostic,), original_results=results,
        assessment_id='assessment.exposed.response.diagnostic', **common)
    assert len(calls) == 20 and len(arrays) == 10
    assert [q.disposition for q in report.questions[:3]] == ['EMPIRICALLY_CONSISTENT',
        'CONSEQUENTIAL_OMITTED_COUPLING', 'CONSEQUENTIAL_OPERATOR_CHANGE']
    assert all(q.disposition == 'UNAVAILABLE' for q in report.questions[3:])
    assert all(r.state == 'NOT_SELECTED' for r in report.coverage if r.stage == 'additional-refinement')
    assert sum(r.action is None for r in report.actions) == 2  # Additional directions lack a second scale.
    predictions = freeze_response_predictions(assessment=report, centers=paired.centers, frames=paired.frames)
    challenge = run_stage(paired, 'challenge', results, custody, predictions)
    final, arrays, _ = reader.read_preparation_response(stages=(diagnostic, challenge), original_results=results,
        assessment_id='assessment.exposed.response.final', **common)
    assert len(calls) == 24
    assert final.questions[3].disposition == 'WITHIN_SELECTED_ERROR_AFTER_PREPARATION'
    assert final.questions[5].disposition == 'PREPARATION_IMPROVES_ARMS_PAIRED_SIGNAL_BELOW_ALLOWANCE'
    assert final.next_supplier_decision == 'RETAIN_SIGNAL_LIMIT_AND_ASSESS_A_CONSEQUENTIAL_FORMATION_RECEIVER'
    _compile_admission(paired, final)
    expected = {(model, position): -(.1 if position == 'initial' else .005)
        * (2 if model == 'm1-i95m' else 1) * .2**2 / np.sqrt(2.) for model, position in POSITIONS}
    actual = {(q.model_name, q.position): float(q.value) for q in final.quantities if q.name == 'signed-prediction-error'}
    assert actual == pytest.approx(expected, abs=2e-13)
    paired_errors = {q.position: float(q.value) for q in final.quantities if q.name == 'paired-signed-prediction-error'}
    assert paired_errors['initial'] == pytest.approx(expected['m1-i95m', 'initial'] - expected['m1-wt', 'initial'], abs=2e-13)
    assert decode_canonical_bytes(final.canonical_bytes(), PreparationResponseAssessment, maximum_bytes=16 * 2**20) == final
    from threadpoolctl import threadpool_info, threadpool_limits
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import BUDGET
    assert BUDGET.cpu_cores == 1
    with threadpool_limits(limits=8):
        before = threadpool_info()
        reread, replayed_arrays, _ = reader.read_preparation_response(stages=(diagnostic, challenge),
            original_results=results, assessment_id=final.assessment_id, **common)
        assert threadpool_info() == before
    assert reread.canonical_bytes() == final.canonical_bytes()
    assert all(np.array_equal(original, replayed) for (_, original), (_, replayed)
        in zip(arrays, replayed_arrays, strict=True))
    assert len(calls) == 24
    assert all(q.independent_biological_replicates == 0 and q.original_starting_hypotheses == 384 for q in final.questions)
    with pytest.raises(ValueError, match='before any challenge'):
        freeze_response_predictions(assessment=final, centers=paired.centers, frames=paired.frames)
    missing = dict(results)
    del missing[challenge[0].point.effect.effect_id]
    incomplete, _, _ = reader.read_preparation_response(stages=(diagnostic, challenge), original_results=missing,
        assessment_id='assessment.exposed.response.missing', **common)
    assert incomplete.questions[3].assessable_comparisons == 3
    assert incomplete.questions[4].assessable_comparisons == 1
    assert len(incomplete.coverage) == 28 and len(calls) == 24
    changed = dict(paired.raw)
    key = POSITIONS[0]
    changed[key] = changed[key][:-1] + bytes((changed[key][-1] ^ 1,))
    with pytest.raises(ValueError, match='original complete raw bytes'):
        reader.read_preparation_response(stages=(diagnostic,), original_results={},
            assessment_id='assessment.exposed.response.changed', **(common | dict(center_bytes=changed)))
    with pytest.raises(ValueError, match='frozen pre-reveal'):
        replace(challenge[0].point, prediction=None)
    assert paired.design.challenge_amplitude_bohr == Decimal('.2')
