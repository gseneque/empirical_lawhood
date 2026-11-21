# SPDX-License-Identifier: MPL-2.0
"""Code-derived SCI02-C tranches on the existing recursive operation lifecycle."""
from dataclasses import dataclass, replace
from functools import partial
import time
from types import MappingProxyType

from empirical_lawhood.domains.matrix.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.domains.matrix.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract, RecursiveScientificRootPreparationContext
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as old
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, RECIPES, Sci02Design, Sci02Root
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import NAMESPACE, NATIVE_PHASES, PHASES, ROOT_PHASES, COMMON, POOLED, Sci02CConfig, Sci02CDesign, Sci02CProduct, Sci02CRetainedCase, Sci02CNativeCheckpoint

BUDGET, ACCESS, VISIBILITY, PERMISSIONS, MAX_RECORD = old.BUDGET, old.ACCESS, old.VISIBILITY, old.PERMISSIONS, old.MAX_RECORD
QUESTION = 'Can a causal empirical description predict a precise paired consumer quantity and direct economical additional work?'
WORLD = 'world.matrix-sci02c.finite-reservation'
DEPENDENCIES = {
    'prefix': (), 'source-state': ('prefix',), 'instrument': ('source-state',),
    'completion': ('prefix', 'instrument'), 'handoff': ('completion',),
    'baseline': ('handoff', 'instrument'), 'observation': ('baseline',), 'history-observation': ('baseline',),
    'basic': ('instrument', *(r + '.' + p for r in RECIPES for p in ('handoff', 'observation'))),
    'request': ('basic',),
    'history': ('basic', 'request', *(r + '.history-observation' for r in RECIPES)),
    'decision': ('request', 'history'),
    'reference': ('handoff', 'instrument', 'baseline', 'decision'),
    'assess': ('prefix', 'completion', 'handoff', 'baseline', 'observation', 'instrument', 'reference'),
    'reduce': ('basic', 'history', 'request', 'decision', *(r + '.' + p for r in RECIPES for p in ('assess', 'handoff', 'observation', 'history-observation'))),
    'diagnose': (),
}


def stage(phase):
    if phase in NATIVE_PHASES: return ScientificStage.ACQUIRE
    if phase in ('source-state', 'handoff', 'observation', 'history-observation'): return ScientificStage.TRANSFORM
    if phase in ('assess', 'diagnose'): return ScientificStage.FALSIFY
    if phase in (*POOLED, 'reduce'): return ScientificStage.SYNTHESIZE
    return ScientificStage.DEVELOP


def make_config(study, roots, phase, recipe, provenance, cases=(), model=None, calibration=None):
    unit = roots[0].group_id if len(roots) == 1 else 'pool.' + phase
    node = f'{NAMESPACE}.{study.fingerprint()[:16]}.{unit}.{recipe.lower()}.{phase}'
    return Sci02CConfig('config.' + node, study, roots, phase, recipe, provenance, cases, model, calibration)


def configs(study, roots, provenance, cases=(), model=None, calibration=None):
    training = model is None
    held = roots[0].bank == 'HOLDOUT'
    expected = tuple(range(8)) if training else tuple(range(32)) if held else tuple(range(8, 16))
    if (tuple(r.ordinal for r in roots) != expected or any(r.bank != ('HOLDOUT' if held else 'DEV') for r in roots)
            or len(cases) != (8 if training else 0)):
        raise ValueError('SCI02-C tranche changes its complete original reserved population')
    result = []
    for index, root in enumerate(roots):
        for phase in (('diagnose',) if training else ROOT_PHASES):
            for recipe in (('COMMON',) if phase in COMMON else RECIPES):
                result.append(make_config(study, (root,), phase, recipe, provenance,
                    (cases[index],) if training else (), model, calibration))
    pooled = 'fit' if training else 'confirm' if held else 'calibrate'
    result.append(make_config(study, roots, pooled, 'COMMON', provenance, cases, model, calibration))
    return tuple(sorted(result, key=lambda c: c.node_id))


def selected_for(pooled):
    if pooled.phase not in POOLED: raise ValueError('SCI02-C complete pooled tranche required')
    return configs(pooled.study, pooled.roots, pooled.provenance, pooled.retained_cases, pooled.model, pooled.calibration)


def parents_for(config):
    if config.phase in POOLED:
        phase = 'diagnose' if config.phase == 'fit' else 'reduce'
        return {f'r{r.ordinal:02d}': make_config(config.study, (r,), phase, 'COMMON', config.provenance,
            (config.retained_cases[i],) if config.phase == 'fit' else (), config.model, config.calibration)
            for i, r in enumerate(config.roots)}
    result = {}
    for key in DEPENDENCIES[config.phase]:
        recipe, phase = key.split('.', 1) if '.' in key else ('COMMON' if key in COMMON else config.recipe, key)
        result[key] = make_config(config.study, config.roots, phase, recipe, config.provenance,
            config.retained_cases, config.model, config.calibration)
    return result


def units(config): return tuple(sorted(r.group_id for r in config.roots))
def slots(config): return (config.node_id + '.native',)
def stream_pins(config): return old.stream_pins(config)
def operands(config):
    return tuple(sorted({config.study.fingerprint(), config.provenance.object_fingerprint,
        *(r.fingerprint() for r in config.roots), *(c.object_fingerprint for c in config.retained_cases),
        *(() if config.model is None else (config.model.fingerprint(),)),
        *(() if config.calibration is None else (config.calibration.fingerprint(),))}))


def development_root(selected, study_id):
    pooled, = (c for c in selected if c.phase in POOLED)
    views = tuple(sorted((pooled.design.coordinate.primary_view.view_id, pooled.design.coordinate.fine_view.view_id)))
    claim = ClaimSpec('claim.' + study_id, WORLD, 'population.matrix-sci02c.original-reservation', QUESTION,
        'Complete original whole-root tranche; three recipes, two nested views, two panels and four actions; sealed scalar consumer predictions.',
        'unit.original-whole-root', None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        'Finite numerical development and held-root assessment; no molecular qualification or conditional population guarantee.',
        ('assumption.matrix-sci02c.original-nominal-source',), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, pooled.study.original_selection, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        units(pooled), views, (claim,), tuple(sorted({pooled.study.identity, pooled.study.original_selection, pooled.provenance,
            *(r.identity for r in pooled.roots), *pooled.retained_cases,
            *(() if pooled.model is None else (pooled.model.identity,)),
            *(() if pooled.calibration is None else (pooled.calibration.identity,))}, key=lambda p: p.object_id)))


def external_contracts(selected, cases):
    result = {}
    for c in cases:
        for row in (old.source_external(c.identity), RecursiveExternalInput('external.' + c.arrays.array_artifact.artifact_id,
                c.arrays.array_artifact.artifact_id, MATRIX_ARRAY_SCHEMA, 'application/x-npz', c.arrays.array_artifact.size_bytes,
                ACCESS, VISIBILITY, c.arrays.array_artifact.sha256, 'SOURCE')):
            result[row.input_id] = row
    for c in selected:
        if c.phase in NATIVE_PHASES:
            for pin in (c.design.identity, c.root.identity, c.provenance, *(p for _, p in stream_pins(c))):
                row = old.source_external(pin); result[row.input_id] = row
        if c.phase == 'instrument':
            a = c.design.assay.template_artifact
            row = RecursiveExternalInput('external.templates.' + a.sha256, a.artifact_id, a.payload_schema, a.media_type,
                a.size_bytes, ACCESS, VISIBILITY, a.sha256, 'SOURCE')
            result[row.input_id] = row
    return tuple(sorted(result.values(), key=lambda v: v.input_id))


def input_links(config):
    links = []
    for key, parent in parents_for(config).items():
        for suffix in ('product', 'arrays'):
            port = key.lower() + '-' + suffix
            links.append(RecursiveInputLink('edge.' + config.node_id + '.' + port, config.node_id, port,
                producer_node_id=parent.node_id, producer_output_id=suffix, scientific_role='HISTORY'))
    if config.phase == 'diagnose':
        for key, external in (('retained', 'external.' + config.retained_cases[0].object_id),
                ('retained-arrays', 'external.arrays.sci02c.retained.' + config.root.fingerprint())):
            links.append(RecursiveInputLink('edge.' + config.node_id + '.' + key, config.node_id, key,
                external_input_id=external, scientific_role='SOURCE'))
    if config.phase in NATIVE_PHASES:
        for key, pin in (('native-design', config.design.identity), ('native-root', config.root.identity),
                ('native-provenance', config.provenance), *(('native-stream.' + p.object_fingerprint, p) for _, p in stream_pins(config))):
            links.append(RecursiveInputLink('edge.' + config.node_id + '.' + key, config.node_id, key,
                external_input_id='external.' + pin.object_id, scientific_role='SOURCE'))
    if config.phase == 'instrument':
        links.append(RecursiveInputLink('edge.' + config.node_id + '.templates', config.node_id, 'templates',
            external_input_id='external.templates.' + config.design.assay.template_artifact.sha256, scientific_role='SOURCE'))
    return tuple(sorted(links, key=lambda v: v.edge_id))


@dataclass(frozen=True, slots=True, eq=False)
class ScientificPreparation:
    batch: RecursiveScientificRootPreparationContext
    node_configs: object


def prepare_root(batch):
    if type(batch) is not RecursiveScientificRootPreparationContext:
        raise TypeError('SCI02-C requires its exact shared scientific preparation')
    selected = tuple(row.record for row in batch.config_inputs)
    pooled = tuple(c for c in selected if type(c) is Sci02CConfig and c.phase in POOLED)
    if (len(pooled) != 1 or tuple(sorted(selected, key=lambda c: c.node_id)) != selected_for(pooled[0])
            or batch.root != development_root(selected, batch.root.study_id)
            or batch.links != tuple(sorted((l for c in selected for l in input_links(c)), key=lambda l: l.edge_id))
            or batch.requirements or batch.connections
            or any(v != batch.root.assigned_unit_ids for v in batch.selected_unit_ids_by_selection.values())):
        raise ValueError('SCI02-C graph changes original population, causal predecessors, criterion or scope')
    if pooled[0].phase != 'fit':
        if batch.external_inputs != external_contracts(selected, ()):
            raise ValueError('SCI02-C graph substitutes original native source or adds a future input')
    else:
        expected = {'external.' + c.object_id for c in pooled[0].retained_cases} | {
            'external.arrays.sci02c.retained.' + r.fingerprint() for r in pooled[0].roots}
        if {e.input_id for e in batch.external_inputs} != expected:
            raise ValueError('SCI02-C training changes its complete original retained census')
        sources = {e.input_id: e for e in batch.external_inputs}
        for p in pooled[0].retained_cases:
            if sources['external.' + p.object_id] != old.source_external(p):
                raise ValueError('SCI02-C training substitutes a retained scientific identity')
    return ScientificPreparation(batch, MappingProxyType({row.node_id: row.record for row in batch.config_inputs}))


def root_validator(config, context):
    prepared = context.scientific_preparation
    if type(prepared) is not ScientificPreparation:
        raise ValueError('SCI02-C requires invocation-local scientific preparation')
    batch = prepared.batch
    if (prepared.node_configs.get(context.node_id) is not config or context.root is not batch.root
            or context.config_inputs is not batch.config_inputs or context.links is not batch.links
            or context.external_inputs is not batch.external_inputs or context.requirements is not batch.requirements
            or context.connections is not batch.connections or context.qualifications is not batch.qualifications
            or context.known_design_inputs is not batch.known_design_inputs
            or context.node_id != config.node_id or context.stage is not stage(config.phase) or context.unit_ids != units(config)
            or context.selected_unit_ids != context.root.assigned_unit_ids or context.complete_unit_census != (config.phase == 'prefix')
            or context.outcome_access is not ACCESS or context.visibility_ceiling is not VISIBILITY):
        raise ValueError('SCI02-C changes its exact prepared invocation, selected operation or scientific boundary')


def lower(study, selection, roots, provenance, campaign, *, draft_id, cases=(), model=None, calibration=None):
    if (study.original_selection != selection.identity or study.physical != selection.design
            or any(r != selection.root(r.bank, r.ordinal) for r in roots)
            or cases and (tuple(c.root for c in cases) != roots or any(c.design != study.physical for c in cases))):
        raise ValueError('SCI02-C lowerer substitutes original physical roots or reservation')
    selected = configs(study, roots, provenance.identity, tuple(c.identity for c in cases), model, calibration)
    declarations = {d.capability_key.rsplit('.', 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id, selection=declarations[c.phase].registration().selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.' + c.node_id,), resource_budget=BUDGET) for c in selected)
    root = development_root(selected, 'study.' + draft_id)
    campaign = replace(campaign, objective=QUESTION, system_ids=(root.system.object_id,), world_ids=(WORLD,), target_claim_ids=(root.claims[0].claim_id,))
    draft = RecursiveStudyDraft(draft_id, QUESTION, campaign, (), (), (), operations, external_contracts(selected, cases),
        tuple(sorted((l for c in selected for l in input_links(c)), key=lambda v: v.edge_id)), tuple(c.node_id for c in selected), development_study=root)
    records = {'external.' + c.record_id: c for c in cases}
    for c in selected:
        if c.phase not in NATIVE_PHASES: continue
        for value in (c.design, c.root, provenance): records['external.' + value.identity.object_id] = value
        for panel, pin in stream_pins(c):
            stream, = (s for s in selection.streams.streams(c.root.group_id, future=bool(panel)) if pin.object_id.endswith('.' + s.purpose))
            if ObjectIdentity.from_record(pin.object_id, stream) != pin:
                raise ValueError('SCI02-C substitutes the original reserved stream bytes')
            records['external.' + pin.object_id] = stream
    return draft, tuple(sorted(records.items()))


def decode(context):
    types = {c.SCHEMA: c for c in (Sci02CConfig, Sci02CProduct, Sci02CRetainedCase, Sci02Design, Sci02Root, NumericalProducingProvenance, MatrixHistorySeed)}
    decoded, raw = {}, {}
    for port in context.input_ports:
        if port.payload_schema == MATRIX_ARRAY_SCHEMA:
            if port.artifact_id in raw: raise ValueError('SCI02-C repeats an array operand')
            raw[port.artifact_id] = port
        else:
            kind = types.get(port.payload_schema)
            if kind is None: raise ValueError('SCI02-C worker receives a foreign scientific input')
            decoded.setdefault(kind, []).append(decode_canonical_bytes(port.read(), kind, maximum_bytes=MAX_RECORD))
    config, = decoded.pop(Sci02CConfig, ())
    if (config.node_id != context.task_id or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256
            or context.resource_budget != BUDGET or context.permissions != PERMISSIONS or context.outcome_access is not ACCESS):
        raise ValueError('SCI02-C worker changes its frozen execution contract')
    source_products = decoded.pop(Sci02CProduct, [])
    products = {p.config.node_id: p for p in source_products}
    expected = parents_for(config)
    if (len(products) != len(source_products) or set(products) != {c.node_id for c in expected.values()}
            or any(products[c.node_id].config != c for c in expected.values())):
        raise ValueError('SCI02-C worker changes its exact causal predecessor census')
    products = {k: products[c.node_id] for k, c in expected.items()}
    selected_arrays = {k: p.arrays for k, p in products.items()}
    retained = None
    if config.phase == 'diagnose':
        retained, = decoded.pop(Sci02CRetainedCase, ())
        if retained.identity != config.retained_cases[0] or retained.root != config.root:
            raise ValueError('SCI02-C diagnosis substitutes original exposed source')
        selected_arrays['retained'] = retained.arrays
    if config.phase == 'instrument':
        from empirical_lawhood.adapters.matrix_storage.matrix_array_io import NPZMemberSelection
        selected_arrays['templates'] = NPZMemberSelection(config.design.assay.template_artifact, config.design.assay.template_members)
    provenance, streams = None, ()
    if config.phase in NATIVE_PHASES:
        design, = decoded.pop(Sci02Design, ()); root, = decoded.pop(Sci02Root, ())
        provenance, = decoded.pop(NumericalProducingProvenance, ())
        received = decoded.pop(MatrixHistorySeed, ())
        if design != config.design or root != config.root or provenance.identity != config.provenance:
            raise ValueError('SCI02-C native input changes direct source, root or provenance')
        selected = []
        for panel, pin in stream_pins(config):
            matches = [s for s in received if ObjectIdentity.from_record(pin.object_id, s) == pin]
            if len(matches) != 1: raise ValueError('SCI02-C native entry substitutes a committed original stream')
            selected.append((panel, matches[0]))
        if len(selected) != len(received): raise ValueError('SCI02-C native entry adds random material')
        streams = tuple(selected)
    if decoded: raise ValueError('SCI02-C predictor receives unselected source or random continuation material')
    if set(raw) != {a.array_artifact.artifact_id for a in selected_arrays.values()}:
        raise ValueError('SCI02-C worker changes the bounded array operand census')
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    arrays = {}
    for key, a in selected_arrays.items():
        port = raw[a.array_artifact.artifact_id]
        if port.media_type != 'application/x-npz' or port.size_bytes != a.array_artifact.size_bytes:
            raise ValueError('SCI02-C worker changes original array transport')
        arrays[key] = dict(decode_matrix_arrays(port.read(), a))
    if config.phase in NATIVE_PHASES:
        count = 64 if config.phase == 'completion' else 32 if config.phase == 'reference' else 0
        saved = products['prefix' if config.phase == 'completion' else 'baseline'].generators if count else ()
        if not count or saved:
            for panel in ((0,) if config.phase in ('prefix', 'completion') else (0, 1)):
                original.validate_generators(tuple(s for p, s in streams if p == panel), saved, count, panel)
    return config, products, arrays, provenance, streams, retained


def project_observation(values, tick):
    result = science.project_observations(values)
    return replace(result, arrays={k: v for k, v in result.arrays.items() if k.startswith(f'h{tick}.')})


def compute(config, products, arrays, retained):
    d, phase = config.design, config.phase
    model, calibration = None, None
    if phase == 'diagnose': result = science.diagnose(config, retained, arrays['retained'])
    elif phase == 'fit': result, model = science.fit(config, {p.config.node_id: p for p in products.values()},
        {p.config.node_id: arrays[k] for k, p in products.items()})
    elif phase == 'source-state': result = original.project_state(arrays['prefix'], tick=64)
    elif phase == 'instrument': result = original.fixed_instrument(d, arrays['source-state'], arrays['templates'])
    elif phase == 'handoff': result = original.project_state(arrays['completion'], tick=256)
    elif phase in ('observation', 'history-observation'):
        result = original.unavailable('NO_HOLD_OBSERVATION') if 'unavailable' in arrays['baseline'] else project_observation(arrays['baseline'], 16 if phase == 'history-observation' else 32)
    elif phase == 'basic': result = science.basic_models(d, arrays['instrument'],
        {r: arrays[r + '.handoff'] for r in RECIPES}, {r: arrays[r + '.observation'] for r in RECIPES})
    elif phase == 'request': result = science.request(config, arrays['basic'])
    elif phase == 'history':
        result = science.history_models(d, arrays['basic'], {r: arrays[r + '.history-observation'] for r in RECIPES})
        requested = int(arrays['request'].get('request_history', [0])[0])
        result = replace(result, measurements=tuple(sorted((*result.measurements, ('policy.purchased_supplier', science.exact(requested))))))
    elif phase == 'decision': result = science.decide(config, arrays['request'], arrays['history'])
    elif phase == 'assess': result = reader.assess_arm(config, arrays)
    elif phase == 'reduce':
        if 'unavailable' not in arrays['basic'] and 'unavailable' not in arrays['history']:
            reader.check_models(d, {r: arrays[r + '.handoff'] for r in RECIPES},
                {r: {**arrays[r + '.observation'], **arrays[r + '.history-observation']} for r in RECIPES}, arrays['basic'], arrays['history'])
            reader.check_descriptions(d, arrays['basic'], arrays['history'])
        result = reader.reduce_root(config, arrays)
    elif phase in ('calibrate', 'confirm'):
        parents = {p.config.node_id: p for p in products.values()}
        values = {p.config.node_id: arrays[k] for k, p in products.items()}
        if phase == 'calibrate': result, calibration = science.calibrate(config, parents, values)
        else: result = reader.confirm(config, parents, values)
    else: raise ValueError('SCI02-C pure operation cannot acquire a native trajectory')
    return result, model, calibration


def product(config, parents, result, operand, *, native=(), model=None, calibration=None):
    return Sci02CProduct('product.' + config.node_id, config,
        tuple(sorted((p.identity for p in parents.values()), key=lambda p: p.object_id)), operand,
        result.disposition, result.reasons, result.measurements, result.generators, native, model, calibration)


class Runner:
    def __init__(self, *, manifest): self.manifest = manifest

    def execute(self, context):
        try:
            config, parents, arrays, _, _, retained = decode(context)
            cpu, wall = time.process_time(), time.monotonic()
            result, model, calibration = compute(config, parents, arrays, retained)
            result = science.with_cost(result, cpu, wall)
            output, = (p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, operand = old._pack(config, result, output.logical_artifact_id)
            return old._outputs(context, product(config, parents, result, operand, model=model, calibration=calibration), raw)
        finally:
            for port in context.input_ports: port.close()


def port_contracts(phase):
    ports = []
    keys = tuple(f'r{i:02d}' for i in (range(8) if phase == 'fit' else range(8, 16) if phase == 'calibrate' else range(32))) if phase in POOLED else DEPENDENCIES[phase]
    for key in keys:
        ports.extend((RecursivePortContract(key.lower() + '-product', Sci02CProduct.SCHEMA, 'application/json', None),
            RecursivePortContract(key.lower() + '-arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES)))
    if phase == 'diagnose':
        ports.extend((RecursivePortContract('retained', Sci02CRetainedCase.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('retained-arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES)))
    if phase == 'instrument': ports.append(RecursivePortContract('templates', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES))
    if phase in NATIVE_PHASES:
        count = 2 if phase in ('prefix', 'completion') else 4
        ports.extend((RecursivePortContract('native-design', Sci02Design.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('native-root', Sci02Root.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('native-stream', MatrixHistorySeed.SCHEMA, 'application/json', MAX_RECORD, minimum_count=count, maximum_count=count)))
    return tuple(sorted(ports, key=lambda p: p.port_id))


def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_inquiry as inquiry
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_native import NativeRunner, prepare_native_work
    codecs = {kind.SCHEMA: kind for kind in (Sci02CConfig, Sci02CDesign, Sci02CRetainedCase, Sci02CProduct,
        Sci02CNativeCheckpoint, Sci02Design, Sci02Root, NumericalProducingProvenance, MatrixHistorySeed)}
    result = []
    for phase in sorted(PHASES):
        native = phase in NATIVE_PHASES
        row = RecursiveOperationDeclaration(capability_key=NAMESPACE + '.' + phase, capability_version='1.0.0',
            implementation_id=NAMESPACE + '.' + phase + '.v1', kind=CapabilityKind.SIMULATOR if native else CapabilityKind.FALSIFIER if phase in ('assess', 'diagnose') else CapabilityKind.ANALYSIS,
            config_record_type=Sci02CConfig, stage=stage(phase), input_ports=port_contracts(phase),
            outputs=(OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),
                OutputTemplate('product', Sci02CProduct.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
            permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=ACCESS, visibility_ceiling=VISIBILITY,
            resources=BUDGET, conformance_check_ids=('sci02c-independent-physical-and-fit-equations', 'sci02c-original-population-and-causal-ports'),
            runner_factory=NativeRunner if native else Runner, record_codecs=codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operands, scientific_unit_ids=units,
                native_effect_slot_ids=slots if native else None, scientific_root_preparer=prepare_root, scientific_root_validator=root_validator),
            execution_properties=RecursiveExecutionProperties(native_effect=native, complete_unit_census=phase == 'prefix',
                native_work_preparer=prepare_native_work if native else None),
            inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=lambda p: p.identity if type(p) is Sci02CProduct else None,
                inquiry_work_projector=inquiry.inquiry_work_projector, inquiry_endpoint_validator=inquiry.inquiry_endpoint_validator,
                inquiry_evidence_projector=inquiry.inquiry_evidence_projector, inquiry_outcome_projector=inquiry.inquiry_outcome_projector,
                inquiry_claim_assessment_projector=inquiry.inquiry_claim_assessment_projector),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        result.append(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest())))
    return tuple(result)
