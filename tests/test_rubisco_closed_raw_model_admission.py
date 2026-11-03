# SPDX-License-Identifier: MPL-2.0
"""Complete exposed CLOSED_RAW/known-parent admission; no real science entry."""

from dataclasses import fields, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p, amber_parameters
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import parameter_audit as producer
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions as prep_definitions, json_output
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableNativeReturnWitness
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_roster
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_invocation import build_invocation
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_preparation_admission import decode_plan, validate_operands
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_runner import ChemicalForceRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.closed_raw_model_admission import (
    GLOBAL_MODEL, HISTORY_SCOPE, MODEL_IDS, UNIT_IDS, ClosedRawModelHistory, ClosedRawModelSupply,
    ClosedRawModelInstance, KnownDerivedModelInstance, ModelInstanceInputs, InstanceChemicalForcePlan,
    ordinary_instance_records,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import GeometryDiagnostic
from empirical_lawhood.runtime.native_subwork import NativeSubworkBegin, NativeSubworkContact, NativeSubworkState
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.test_rubisco_derived_model_chemical_admission import (
    COLD_READER, binding, document, json_file, text_file, native_shape, derived as derived_fixture,
)
from tests.test_rubisco_geometry_reuse import original as original  # noqa: F401
from tests.test_rubisco_preparation_integrity import amber_text


COLD_CHILD = r'''
import importlib.abc,json,sys
from pathlib import Path
from types import SimpleNamespace
class NoBackend(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('numpy','scipy','openmm','parmed','pdbfixer') or fullname.endswith('.parameter_audit'):
            raise AssertionError('backend/producer entered closed-raw consumer: '+fullname)
sys.meta_path.insert(0,NoBackend())
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_native_entry as entry,control_preparation_admission as admission
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import science as preparation_science
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
root=Path(sys.argv[1]);data=json.loads((root/'invocation.json').read_bytes())
first=decode_canonical_bytes(data['definitions'][0].encode(),NativeSubworkDefinition,maximum_bytes=None)
observed={'admission':0,'roster':0}
original=admission.validate_operands
def validate(*args):
    result=original(*args);observed['admission']+=1
    assert args[3] is args[4] is None and args[-1]==()
    return result
admission.validate_operands=validate
def freeze(roster,definitions):
    observed['roster']=len(definitions)
progress=SimpleNamespace(parent_contact=first.parent_contact,freeze_roster=freeze)
def stop(*args):raise RuntimeError('EXPOSED_STOCK_BOUNDARY_NO_BACKEND_ENTRY')
preparation_science.validate_stock=stop
try:entry._authenticated_child(progress,data)
except RuntimeError as error:assert str(error)=='EXPOSED_STOCK_BOUNDARY_NO_BACKEND_ENTRY'
else:raise AssertionError('unexpected backend entry')
assert observed=={'admission':1,'roster':0}
(root/'child-result.json').write_text(json.dumps(observed))
'''


@pytest.fixture(scope='module')
def known_derived(original, tmp_path_factory):
    return derived_fixture.__wrapped__(original, tmp_path_factory)


@pytest.fixture(scope='module')
def closed(known_derived, tmp_path_factory):
    known = known_derived
    root = tmp_path_factory.mktemp('closed-raw-instance-exposed')
    # Full5050-atom independent source/genotype fixture, new global topology and
    # independently generated audit. Scoped assessment bytes cannot substitute.
    raw_topology = (known.root / 'raw/model.prmtop').read_text()
    rows = amber_parameters.read_prmtop(raw_topology)
    rows['MASS'] = (rows['MASS'][0] + 1, *rows['MASS'][1:])
    census = amber_parameters.assigned_census_supported_inactive14(rows)
    shape = native_shape(census, rows)
    shape.atoms[0].mass = 13.
    origin = json.loads((known.root / 'raw/atom-origin-provenance.json').read_bytes())
    raw = {name: text_file(root, GLOBAL_MODEL + '/' + name, (known.root / 'raw' / name).read_text())
        for name in ('model.inpcrd', 'complete-heavy.pdb', 'atom-origin-provenance.json')}
    raw['model.prmtop'] = text_file(root, GLOBAL_MODEL + '/model.prmtop', amber_text(rows))
    for name in ('model.prmtop', 'model.inpcrd', 'complete-heavy.pdb'):
        text_file(root, 'raw/' + name, raw[name].raw_utf8)
    origin['amber_realization'] = producer.realized_atom_origins_from_coordinates(shape, origin,
        raw['complete-heavy.pdb'].raw_utf8, raw['model.inpcrd'].raw_utf8)
    derived_origin = json_file(root, 'derived/atom-origin-provenance.json', origin)
    audit = json_file(root, 'derived/complete-assigned-parameters.json', producer.assigned_parameter_inventory(shape))
    reader = json.loads((known.root / 'reader-input.json').read_bytes())
    json_file(root, 'reader-input.json', reader)
    source_root = Path(p.__file__).resolve().parents[5]
    environment = dict(os.environ, PYTHONPATH=str(source_root / 'src'), PYTHONDONTWRITEBYTECODE='1')
    cold = subprocess.run([sys.executable, '-c', COLD_READER, str(root)], env=environment, capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
    result = json.loads((root / 'independent-result.json').read_bytes())
    diagnostic_text = text_file(root, 'retained/diagnostic.json', (root / 'geometry-diagnostic.json').read_text())
    global_source = replace(known.source, native_workdir=p.NATIVE_WORK_ROOT + '/exposed-closed-global-parent/native-work')
    original_plan = replace(known.plan.preparation_plan, source=p.identity(global_source), workdir=global_source.native_workdir,
        attempted_model_ids=(GLOBAL_MODEL, known.plan.selected_assets[0][0]),
        archive_inputs=tuple((identity, str(Path(global_source.native_workdir).parent / 'inputs' / 'original-geometry.archive'))
            for identity, _ in known.plan.preparation_plan.archive_inputs))
    definitions = list(prep_definitions(original_plan, known.parent, sources=(original_plan.source,
        original_plan.nomination, original_plan.inventory, original_plan.coordinates,
        *original_plan.geometry_supplies, *[row for row in known.custody[0][1].sources
            if row.object_schema.endswith('pre-amber-geometry-integrity')]),
        input_materialization_ids=known.parent.input_materialization_ids))
    metadata = next(row for row in definitions if row.subwork_id == 'preparation.metadata')
    # Conditional native-shaped rows are disclosed software records only; none
    # is completed. All36 original scientific rows remain UNKNOWN/unentered.
    definitions.extend((replace(metadata, subwork_id='preparation.launch',
        outputs=(json_output('process.return', IsolatedNativeEntryReturn),)),
        replace(metadata, subwork_id=GLOBAL_MODEL + '.call.000001', outputs=(
            json_output('call.return', p.NativeCall), json_output('call.witness', DurableNativeReturnWitness))),
        replace(metadata, subwork_id=GLOBAL_MODEL + '.call.000001.operand', outputs=())))
    definitions = tuple(sorted(definitions, key=lambda row: row.subwork_id))
    begun = tuple(sorted((GLOBAL_MODEL, 'preparation.metadata', 'preparation.launch',
        GLOBAL_MODEL + '.call.000001', GLOBAL_MODEL + '.call.000001.operand')))
    begin_records = {name: NativeSubworkBegin(next(row.identity for row in definitions if row.subwork_id == name)) for name in begun}
    definition_rows, begin_rows, contact_rows = [], [], []
    for definition in definitions:
        record = text_file(root, 'custody/' + definition.subwork_id + '.definition.json', definition.canonical_bytes().decode())
        definition_rows.append(dict(binding=binding(root, record), record=document(definition)))
    for name in begun:
        begin = begin_records[name]
        record = text_file(root, 'custody/' + name + '.begin.json', begin.canonical_bytes().decode())
        begin_rows.append(dict(binding=binding(root, record), record=document(begin)))
        prefix = 'native-subwork.' + sha256((known.parent.task_id + ':' + name).encode()).hexdigest()
        contact = NativeSubworkContact(ObjectIdentity.from_record(prefix + '.begin', begin))
        contact_rows.append((name, text_file(root, 'custody/' + name + '.contact.json', contact.canonical_bytes().decode())))
    closure = json_file(root, 'retained/closure.json', dict(schema='el.rubisco.wt03-live-root-metadata-observation.v1',
        definition_count=40, begin_count=5, completion_count=0, full_definitions=definition_rows,
        full_begins=begin_rows, full_completions=[], native_os_return='UNKNOWN', scientific_return='UNKNOWN',
        typed_process_return_exists=False, os_process_closure_observed=True, stable_raw_fragment_diagnosis_eligible=True,
        selected_process_observations=[], unreadable_potentially_selected_processes=[],
        original_identity_observations=[dict(pid=index+1, original_start_time_ticks=100+index,
            same_original_identity_present=False) for index in range(5)]))
    geometry = next(row for row in json.loads(known.supply.historical_readout.raw_utf8)['full36states'] if row.startswith('geometry.gp.wt.m1.joint-01'))
    supply_identity = original_plan.geometry_supplies[0]
    geometry_parent = json_file(root, GLOBAL_MODEL + '/geometry-reuse-parent.json', dict(
        supply=document(supply_identity), original_geometry=document(ObjectIdentity(geometry,
            definitions[0].SCHEMA, '1.0.0', '1'*64)), original_geometry_receipt=document(ObjectIdentity(
            'receipt.exposed.original-geometry', 'empirical-lawhood/runtime/canonical-task-receipt', '1.0.0', '2'*64)),
        independent_integrity=document(ObjectIdentity('assessment.exposed.original-geometry',
            'empirical-lawhood/rubisco-insilico-dynamics/pre-amber-geometry-integrity', '1.0.0', '3'*64)),
        original_archive=document(p.FileEvidence('original/archive', 1, '4'*64))))
    members = list(raw.values()) + [geometry_parent]
    for index in range(18):
        members.append(text_file(root, 'other/member-' + str(index).zfill(2) + '.txt', 'EXPOSED CLOSED RAW CENSUS\n'))
    members.sort(key=lambda row: row.evidence.relative_path)
    carriers = [dict(subwork_id=row.subwork_id, output_id=out.output_id, present=False,
        manifest_present=False, binding=None) for row in definitions for out in row.outputs
        if out.output_id.endswith('.return') or out.output_id == 'call.witness']
    raw_audit = json_file(root, 'retained/raw-custody.json', dict(schema='el.rubisco.wt03.closed-raw-fragment-custody-audit.v1',
        scientific_return='UNKNOWN', native_os_return='UNKNOWN', typed_original_native_process_return='ABSENT',
        complete_model_unit_returns='ABSENT', controller_readout='ABSENT', original_definition_count=40,
        original_begin_count=5, original_completion_count=0, original_completion_bindings=[], regular_file_count=23,
        regular_file_bytes=sum(row.evidence.byte_count for row in members), symlink_or_special_members=[], unknown_replay=False,
        genuine_root_process_closure=binding(root, closure), regular_file_inventory=[dict(relative_path=row.evidence.relative_path,
            binding=binding(root, row)) for row in members], complete_original_definition_bindings=[row['binding'] for row in definition_rows],
        complete_original_begin_bindings=[row['binding'] for row in begin_rows], complete_declared_typed_return_carrier_presence=carriers))
    states = tuple((name, NativeSubworkState.UNKNOWN_COMPLETION if name == GLOBAL_MODEL else NativeSubworkState.NOT_ENTERED) for name in UNIT_IDS)
    assignment_states = tuple((name, 'ABSENT_NOT_ASSESSED') for name in MODEL_IDS)
    history = ClosedRawModelHistory('history.exposed.closed-raw', p.identity(global_source), original_plan,
        raw_audit, closure, geometry_parent, tuple(contact_rows), tuple(row.evidence for row in members), states, assignment_states)
    owner = known.supply.producer_source_manifest
    independent = known.supply.independent_source_manifest
    producer_manifest = json_file(root, 'retained/producer-source.json', dict(
        schema='el.rubisco.wt03.closed-raw-derived-postprocessing-source.v1',
        reused_producer_source_manifest=binding(known.root, owner), independent_method_source_manifest=binding(known.root, independent)))
    common = dict(original_history_scope=HISTORY_SCOPE, original_definition_count=40, original_begin_count=5,
        original_contact_count=5, original_completion_count=0, original_unit_return='ABSENT', original_typed_native_return='ABSENT',
        original_native_os_return='UNKNOWN', original_scientific_return='UNKNOWN', original_native_attempt_count='UNKNOWN',
        original_native_completed_count='UNKNOWN', original_native_cost='UNKNOWN',
        original_unit_states={name: state.value for name, state in states}, original_assignment_states=[list(row) for row in assignment_states],
        model_id=GLOBAL_MODEL, original_raw_custody_audit=binding(root, raw_audit),
        authoritative_original_process_closure=binding(root, closure), geometry_parent=binding(root, geometry_parent),
        original_raw_operands={name: binding(root, row) for name, row in raw.items()},
        derived_origin=binding(root, derived_origin), derived_parameter_audit=binding(root, audit))
    produced = json_file(root, 'retained/produced.json', common | dict(
        schema='el.rubisco.wt03.closed-raw-derived-postprocessing.v1', derived_postprocessing='PRODUCTS_PRODUCED', error=None,
        new_postprocess_load_count=1, original_origin_prefix_preserved=True, molecular_acquisition_count=0,
        native_solver_count=0, tleap_count=0, source_manifest=binding(root, producer_manifest),
        postprocess_load_procedures=[dict(model_id=GLOBAL_MODEL, termination='COMPLETED', error=None,
            original_prmtop=binding(root, raw['model.prmtop']), original_inpcrd=binding(root, raw['model.inpcrd']), cpu_seconds='0', wall_seconds='0')]))
    phase = common | dict(schema='el.rubisco.wt03.closed-raw-derived-independent-phase.v1',
        phase_state='COMPLETED', assessment_error=None, native_calls=0, producer_reexecution=False,
        qualification=False, physical_independent_units=0, matched_I95M_admission=False,
        source_manifest=binding(known.root, independent), historical_producer_source_manifest=binding(root, producer_manifest),
        derived_products=binding(root, produced))
    assignment = json_file(root, 'retained/assignment.json', phase | dict(phase='assignment-origin', result={
        name: result[name] for name in ('complete_parameter_term_census', 'coordinate_origin_validation', 'inactive14_support')}))
    diagnostic = json.loads(diagnostic_text.raw_utf8)['value']
    geometry_readout = json_file(root, 'retained/geometry.json', phase | dict(phase='geometry', result=dict(
        method=result['geometry_method'], diagnostic=binding(root, diagnostic_text),
        independent_assignment_origin_parent=binding(root, assignment), hard_geometry_disposition=diagnostic['hard_geometry_disposition'],
        pair_counts=diagnostic['pair_counts'], bonded_counts=diagnostic['bonded_counts'])))
    files = [raw[name] for name in ('model.prmtop', 'model.inpcrd', 'complete-heavy.pdb')] + [derived_origin, audit]
    asset = p.ModelAssets('product.exposed.global-derived', p.identity(global_source), 'gp.wt.m1', 'joint-01',
        'published-global-kcx-override', tuple(sorted(files, key=lambda row: row.evidence.relative_path)))
    supply = ClosedRawModelSupply('supply.exposed.closed-raw', history, p.identity(asset), produced, assignment,
        geometry_readout, producer_manifest, owner, independent, diagnostic_text)
    instance = ClosedRawModelInstance('instance.exposed.global', global_source, supply)
    return SimpleNamespace(root=root, source_root=source_root, known=known, history=history, supply=supply,
        instance=instance, asset=asset, environment=environment)


def operands(row, mixed=False):
    instances, assets = [row.instance], [row.asset]
    if mixed:
        old = row.known
        # Exact historical source bytes with reused object IDs are retained;
        # transport aliases distinguish parents rather than rewriting records.
        instances.append(KnownDerivedModelInstance('instance.exposed.scoped', old.source, old.plan,
            old.preparation, old.integrity, old.geometry, old.custody))
        assets.extend(old.assets)
    inputs = ModelInstanceInputs('inputs.exposed.model-instances', tuple(instances))
    selected = tuple((instance.model_id, instance.assets) for instance in instances)
    source = row.known.source
    identities = {identity for identity, _ in ordinary_instance_records(inputs)} | {p.identity(source)} | {identity for _, identity in selected}
    kwargs = {field.name: getattr(row.known.plan, field.name) for field in fields(InstanceChemicalForcePlan)
        if hasattr(row.known.plan, field.name)}
    kwargs.update(plan_id='config.exposed.closed-raw-instance', instance_inputs=inputs.identity,
        selected_assets=selected, instance_operands=tuple(sorted(identities, key=lambda item: item.object_id)))
    return InstanceChemicalForcePlan(**kwargs), source, inputs, None, None, tuple(assets), ()


@pytest.mark.parametrize('mixed', (False, True))
def test_full_producer_cold_proof_ordinary_inputs_and_actual_child_preserve_unknown(closed, mixed):
    args = operands(closed, mixed)
    plan, source, inputs, _, _, assets, _ = args
    before = closed.history.canonical_bytes()
    assert validate_operands(*args) == plan
    assert decode_plan(plan.canonical_bytes().decode()) == plan
    selected = control_roster.definitions(plan, closed.known.parent, sources=plan.instance_operands,
        input_materialization_ids=closed.known.parent.input_materialization_ids)
    # The actual runner authenticates all ordinary operand bytes, including
    # originals whose IDs recur across parents. No history is an outcome alias.
    records = dict(ordinary_instance_records(inputs)) | {plan.identity: plan, p.identity(source): source,
        **{p.identity(asset): asset for asset in assets}}
    ports = [SimpleNamespace(artifact_id=identity.object_id, payload_schema=identity.object_schema,
        media_type='application/json', visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, size_bytes=len(record.canonical_bytes()),
        materialization_id='exposed.materialization.' + str(index), read=lambda value=record: value.canonical_bytes())
        for index, (identity, record) in enumerate(sorted(records.items(), key=lambda row: row[0].object_id))]
    attempted = tuple('control.chemical-force.' + name for name, _ in plan.selected_assets)
    outputs = [SimpleNamespace(output_id='census', payload_schema='empirical-lawhood/rubisco-insilico-sampling/chemical-force-census',
        profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json')]
    raw_out = next(row for row in selected[0].outputs if row.output_id == 'files.raw') if selected[0].outputs else next(
        row for definition in selected for row in definition.outputs if row.output_id == 'files.raw')
    outputs.extend(SimpleNamespace(output_id=name, payload_schema=raw_out.payload_schema, profile=raw_out.profile,
        media_type=raw_out.media_type) for name in attempted)
    environment = tuple(sorted(dict(PYTHONDONTWRITEBYTECODE='1', OPENMM_PLUGIN_DIR='/tmp/exposed-plugins',
        OPENMM_CPU_THREADS='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1').items()))
    runner = ChemicalForceRunner(plan, '/tmp/exposed-invocation', selected, environment,
        tuple((name, name) for name in attempted), 'census')
    # Keep actual declared materialization identities; port reads are complete
    # canonical fixtures, and the production SHA/schema/access checks run.
    context = SimpleNamespace(task_id=closed.known.parent.task_id, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        input_ports=tuple(ports), output_ports=tuple(outputs))
    for port, mid in zip(ports, (*closed.known.parent.input_materialization_ids,
            *('exposed.materialization.' + str(i) for i in range(len(ports)))), strict=False):
        port.materialization_id = mid
    parent = replace(closed.known.parent, input_materialization_ids=tuple(sorted(port.materialization_id for port in ports)))
    selected = control_roster.definitions(plan, parent, sources=plan.instance_operands,
        input_materialization_ids=parent.input_materialization_ids)
    runner = replace(runner, selected_definitions=selected)
    assert runner.validate_context(context, SimpleNamespace(parent_contact=parent)) == attempted
    original_read = ports[0].read
    ports[0].read = lambda: original_read() + b'EXPOSED_CHANGED_ORDINARY_INPUT'
    with pytest.raises(ValueError, match='canonical materialized input'):
        runner.validate_context(context, SimpleNamespace(parent_contact=parent))
    ports[0].read = original_read
    raw = build_invocation(*args, selected, source_root=str(closed.source_root))
    text_file(closed.root, 'invocation.json', raw.decode())
    cold = subprocess.run([sys.executable, '-c', COLD_CHILD, str(closed.root)], env=closed.environment,
        capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
    assert json.loads((closed.root / 'child-result.json').read_bytes()) == dict(admission=1, roster=0)
    assert before == closed.history.canonical_bytes()
    assert closed.history.original_native_attempt_count is closed.history.original_native_completed_count is None
    assert len(closed.history.files) == 23 and len(closed.history.original_unit_states) == 36
    assert all(state == 'ABSENT_NOT_ASSESSED' for _, state in closed.history.original_assignment_states)
    assert len(plan.nve_census) == 96
    assert all(record.canonical_bytes() == next(value for identity, value in ordinary_instance_records(inputs)
        if identity == alias).canonical_bytes() for alias, record in ordinary_instance_records(inputs))
    if mixed:
        assert len(assets) == 2 and inputs.instances[1].custody[0][-1].preparation_succeeded is False
        assert inputs.instances[0].source.selection_id == inputs.instances[1].source.selection_id
        assert p.identity(inputs.instances[0].source) != p.identity(inputs.instances[1].source)


@pytest.mark.parametrize('change', ('live', 'missing-file', 'thinned-definition', 'invented-return', 'invented-assessment', 'missing-contact'))
def test_original_unknown_closed_history_guards_refuse(closed, change):
    row = closed.history
    with pytest.raises(ValueError):
        if change == 'live':
            data = json.loads(row.process_closure.raw_utf8); data['os_process_closure_observed'] = False
            replace(row, process_closure=json_file(closed.root, 'mutations/live.json', data))
        elif change == 'missing-file': replace(row, files=row.files[:-1])
        elif change == 'thinned-definition':
            data = json.loads(row.process_closure.raw_utf8); data['full_definitions'].pop()
            replace(row, process_closure=json_file(closed.root, 'mutations/thinned.json', data))
        elif change == 'invented-return': replace(row, original_scientific_return='SUCCEEDED')
        elif change == 'invented-assessment': replace(row, original_assignment_states=tuple((name, 'SATISFIED') for name, _ in row.original_assignment_states))
        else: replace(row, original_contacts=row.original_contacts[:-1])


@pytest.mark.parametrize('change', ('absent-proof', 'negative-proof', 'scoped-topology', 'wrong-method', 'wrong-lineage', 'unrecorded-load'))
def test_separate_same_product_source_proof_and_load_guards_refuse(closed, change):
    supply = closed.supply
    data = json.loads(supply.assignment_readout.raw_utf8)
    with pytest.raises(ValueError):
        if change == 'absent-proof': data.pop('result')
        elif change == 'negative-proof': data['phase_state'] = 'KNOWN_ADVERSE_RETURN'
        elif change == 'scoped-topology': data['original_raw_operands']['model.prmtop'] = json.loads(closed.known.supply.postprocessing_readout.raw_utf8)['original_raw_operands']['model.prmtop']
        elif change == 'wrong-method': data['result']['coordinate_origin_validation']['method']['object_fingerprint'] = '9'*64
        elif change == 'wrong-lineage': data['original_scientific_return'] = 'SUCCEEDED'
        else:
            produced = json.loads(supply.postprocessing_readout.raw_utf8); produced['postprocess_load_procedures'] = []
            replace(supply, postprocessing_readout=json_file(closed.root, 'mutations/load.json', produced))
            return
        replace(supply, assignment_readout=json_file(closed.root, 'mutations/' + change + '.json', data))


def test_actual_consumer_requires_every_ordinary_original_parent(closed):
    args = operands(closed, True)
    plan, source, inputs, integrity, geometry, assets, custody = args
    changed = replace(plan, instance_operands=tuple(row for row in plan.instance_operands if row.object_schema != NativeSubworkBegin.SCHEMA))
    with pytest.raises(ValueError, match='ordinary original'):
        validate_operands(changed, source, inputs, integrity, geometry, assets, custody)


def test_null_slots_and_old_version_are_not_interchangeable(closed):
    args = operands(closed)
    with pytest.raises(ValueError, match='absent legacy'):
        validate_operands(*args[:3], closed.known.integrity, *args[4:])
    plan = args[0]
    data = document(plan); data['version'] = '1.3.0'
    with pytest.raises(ValueError): decode_plan(json.dumps(data))


def test_complete_adverse_geometry_record_never_admits_closed_raw_instance(closed):
    supply = closed.supply
    diagnostic = decode_canonical_bytes(supply.geometry_diagnostic.raw_utf8.encode(), GeometryDiagnostic, maximum_bytes=None)
    adverse = replace(diagnostic, coincident_unwrapped_pair_count=1, hard_geometry_disposition=A.FALSIFIED)
    retained = text_file(closed.root, 'mutations/adverse-diagnostic.json', adverse.canonical_bytes().decode())
    data = json.loads(supply.geometry_readout.raw_utf8)
    data['result'].update(diagnostic=binding(closed.root, retained), hard_geometry_disposition='FALSIFIED')
    changed = replace(supply, geometry_diagnostic=retained,
        geometry_readout=json_file(closed.root, 'mutations/adverse-geometry.json', data))
    instance = replace(closed.instance, supply=changed)
    updated = SimpleNamespace(**(vars(closed) | dict(instance=instance)))
    with pytest.raises(ValueError, match='adverse independent hard geometry'):
        validate_operands(*operands(updated))


@pytest.mark.parametrize('slot', ('integrity', 'geometry', 'custody'))
def test_actual_child_rejects_inconsistent_legacy_slots_before_stock(closed, slot):
    args = operands(closed)
    selected = control_roster.definitions(args[0], closed.known.parent, sources=args[0].instance_operands,
        input_materialization_ids=closed.known.parent.input_materialization_ids)
    data = json.loads(build_invocation(*args, selected, source_root=str(closed.source_root)))
    data[slot] = ['EXPOSED_FALSE_LEGACY_CUSTODY'] if slot == 'custody' else '{}'
    json_file(closed.root, 'invocation.json', data)
    refusal = COLD_CHILD.replace("except RuntimeError as error:assert str(error)=='EXPOSED_STOCK_BOUNDARY_NO_BACKEND_ENTRY'",
        "except ValueError as error:assert 'absent legacy' in str(error)")
    refusal = refusal.replace("assert observed=={'admission':1,'roster':0}", "assert observed=={'admission':0,'roster':0}")
    cold = subprocess.run([sys.executable, '-c', refusal, str(closed.root)], env=closed.environment,
        capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
