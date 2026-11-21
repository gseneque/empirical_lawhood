# SPDX-License-Identifier: MPL-2.0
"""SCI02 domain graph on the ordinary recursive/native lifecycle.

The registered lowerer owns every operation and predecessor. Pure predictor
ports carry state projections and immutable array witnesses, never RNG values.
"""
from dataclasses import replace
from decimal import Decimal
from functools import partial
from hashlib import sha256
import resource
import time

from empirical_lawhood.domains.matrix.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.domains.matrix.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, NAMESPACE, NATIVE_PHASES, PHASES, RECIPES, Sci02Arrays, Sci02Config, Sci02Design, Sci02Root, Sci02NativeCheckpoint, Sci02NativeHistory, Sci02Product

BUDGET = ResourceBudget(1, 2 * 1024**3, 0, 3600, 2 * 1024**3, 128 * 1024**2)
QUESTION = 'Does preparation improve an H64 response shortcut, can a tick64 shadow predict its error, and does a frozen selection policy add value?'
WORLD = 'world.matrix-sci02.development'
MAX_RECORD = 4 * 1024**2
ACCESS, VISIBILITY = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS = tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT)))
DEPENDENCIES = {
    'prefix': (), 'source-state': ('prefix',), 'shadow': ('source-state',),
    'completion': ('prefix', 'shadow'), 'handoff': ('completion',), 'origin': ('handoff', 'shadow'),
    'response-prefix': ('handoff', 'origin', 'shadow'), 'observation': ('response-prefix',),
    'refresh': ('origin', 'observation'), 'response-suffix': ('response-prefix', 'refresh'),
    'assess': ('prefix', 'source-state', 'shadow', 'completion', 'handoff', 'origin', 'response-prefix', 'observation', 'refresh', 'response-suffix'),
    'reduce': tuple(recipe + '.assess' for recipe in RECIPES),
}
COMMON = ('prefix', 'source-state', 'shadow', 'reduce')


def stage(phase):
    if phase in NATIVE_PHASES: return ScientificStage.ACQUIRE
    if phase == 'assess': return ScientificStage.FALSIFY
    if phase == 'reduce': return ScientificStage.SYNTHESIZE
    if phase in ('source-state', 'handoff', 'observation'): return ScientificStage.TRANSFORM
    return ScientificStage.DEVELOP


def config_for(config, key):
    recipe, phase = key.split('.', 1) if '.' in key else ('COMMON' if key in COMMON else config.recipe, key)
    node = f'{NAMESPACE}.{config.root.group_id}.{recipe.lower()}.{phase}'
    return Sci02Config('config.' + node, config.design, config.root, phase, recipe, config.provenance)


def configs(design, root, provenance):
    base = Sci02Config(f'config.{NAMESPACE}.{root.group_id}.common.prefix', design, root, 'prefix', 'COMMON', provenance)
    return tuple(sorted((*(config_for(base, p) for p in COMMON),
        *(config_for(base, r + '.' + p) for r in RECIPES for p in PHASES if p not in COMMON)), key=lambda c: c.node_id))


def units(config): return (config.root.group_id,)
def slots(config): return (config.node_id + '.native',)
def operands(config): return tuple(sorted({config.design.fingerprint(), config.root.fingerprint(), config.provenance.object_fingerprint}))


def stream_pins(config):
    purpose = 'preparation' if config.phase in ('prefix', 'completion') else 'autonomous'
    return tuple(sorted(((panel, pin) for panel, pins in config.root.streams for pin in pins
        if (purpose == 'autonomous' or panel == 0) and pin.object_id.rsplit('.', 1)[-1].startswith(purpose)),
        key=lambda row: row[1].object_id))


def development_root(selected, study_id):
    roots = tuple(sorted({c.root for c in selected}, key=lambda row: row.record_id))
    design, = {c.design for c in selected}
    selection, = {r.selection for r in roots}
    views = tuple(sorted((design.coordinate.primary_view.view_id, design.coordinate.fine_view.view_id)))
    claim = ClaimSpec('claim.' + study_id, WORLD, 'population.matrix-sci02.selected', QUESTION,
        'Every assigned whole root, all three arms, two nested numerical views, two panels, four actions and all 49 aligned H16--H64 checks.',
        'unit.original-whole-root', None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        'Matrix development and sealed finite holdout comparison only; no molecular admission, prospective qualification or 95/95 reliability claim.',
        ('assumption.matrix-sci02.original-nominal-source',), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, selection, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        tuple(r.group_id for r in roots), views, (claim,), tuple(sorted({design.identity, selection,
            *(r.identity for r in roots), *(c.provenance for c in selected)}, key=lambda v: v.object_id)))


def source_external(pin, *, size=MAX_RECORD):
    return RecursiveExternalInput('external.' + pin.object_id, pin.object_id, pin.object_schema, 'application/json', size,
        ACCESS, VISIBILITY, pin.object_fingerprint, 'SOURCE')


def external_contracts(selected):
    result = {}
    for config in selected:
        if config.phase in NATIVE_PHASES:
            for pin in (config.design.identity, config.root.identity, config.provenance, *(pin for _, pin in stream_pins(config))):
                row = source_external(pin)
                result[row.input_id] = row
        if config.phase == 'shadow':
            artifact = config.design.assay.template_artifact
            row = RecursiveExternalInput('external.templates.' + artifact.sha256, artifact.artifact_id, artifact.payload_schema,
                artifact.media_type, artifact.size_bytes, ACCESS, VISIBILITY, artifact.sha256, 'SOURCE')
            result[row.input_id] = row
    return tuple(sorted(result.values(), key=lambda v: v.input_id))


def input_links(config):
    links = []
    for key in DEPENDENCIES[config.phase]:
        parent = config_for(config, key)
        for suffix in ('product', 'arrays'):
            port = key.lower() + '-' + suffix
            links.append(RecursiveInputLink('edge.' + config.node_id + '.' + port, config.node_id, port,
                producer_node_id=parent.node_id, producer_output_id=suffix, scientific_role='HISTORY'))
    if config.phase in NATIVE_PHASES:
        for key, pin in (('native-design', config.design.identity), ('native-root', config.root.identity), ('native-provenance', config.provenance),
                *(('native-stream.' + pin.object_fingerprint, pin) for _, pin in stream_pins(config))):
            links.append(RecursiveInputLink('edge.' + config.node_id + '.' + key, config.node_id, key,
                external_input_id='external.' + pin.object_id, scientific_role='SOURCE'))
    if config.phase == 'shadow':
        links.append(RecursiveInputLink('edge.' + config.node_id + '.templates', config.node_id, 'templates',
            external_input_id='external.templates.' + config.design.assay.template_artifact.sha256, scientific_role='SOURCE'))
    return tuple(sorted(links, key=lambda v: v.edge_id))


def root_validator(config, context):
    selected = tuple(row.record for row in context.config_inputs)
    if not selected or any(type(c) is not Sci02Config for c in selected):
        raise ValueError('SCI02 graph mixes foreign scientific operations')
    roots = tuple(sorted({c.root for c in selected}, key=lambda r: r.record_id))
    expected = tuple(sorted((c for root in roots for c in configs(config.design, root, config.provenance)), key=lambda c: c.node_id))
    if (tuple(sorted(selected, key=lambda c: c.node_id)) != expected
            or context.root != development_root(selected, context.root.study_id)
            or context.node_id != config.node_id or context.stage is not stage(config.phase)
            or context.unit_ids != units(config) or context.selected_unit_ids != context.root.assigned_unit_ids
            or context.complete_unit_census != (config.phase == 'prefix')
            or context.outcome_access is not ACCESS or context.visibility_ceiling is not VISIBILITY
            or context.external_inputs != external_contracts(selected)
            or tuple(row for row in context.links if row.consumer_node_id == config.node_id) != input_links(config)):
        raise ValueError('SCI02 graph changes its complete source, causal cutoffs, original groups, phases or stream operands')


def lower(selection, roots, provenance, campaign, *, draft_id):
    selected = tuple(sorted((c for root in roots for c in configs(selection.design, root, provenance.identity)), key=lambda c: c.node_id))
    if any(root != selection.root(root.bank, root.ordinal) for root in roots):
        raise ValueError('SCI02 lowerer substitutes a root outside its exact original reservation')
    declarations = {row.capability_key.rsplit('.', 1)[-1]: row for row in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id, selection=declarations[c.phase].registration().selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.' + c.node_id,), resource_budget=BUDGET) for c in selected)
    study = development_root(selected, 'study.' + draft_id)
    campaign = replace(campaign, objective=QUESTION, system_ids=(study.system.object_id,), world_ids=(WORLD,), target_claim_ids=(study.claims[0].claim_id,))
    draft = RecursiveStudyDraft(draft_id, QUESTION, campaign, (), (), (), operations, external_contracts(selected),
        tuple(sorted((link for c in selected for link in input_links(c)), key=lambda row: row.edge_id)),
        tuple(c.node_id for c in selected), development_study=study)
    records = {'external.' + provenance.identity.object_id: provenance}
    for config in selected:
        if config.phase not in NATIVE_PHASES: continue
        for value in (config.design, config.root):
            records['external.' + value.identity.object_id] = value
        for panel, pin in stream_pins(config):
            stream, = (s for s in selection.streams.streams(config.root.group_id, future=bool(panel))
                if pin.object_id.endswith('.' + s.purpose))
            if ObjectIdentity.from_record(pin.object_id, stream) != pin:
                raise ValueError('SCI02 stream bytes differ from their committed original root')
            records['external.' + pin.object_id] = stream
    return draft, tuple(sorted(records.items()))


def _decode(context):
    config, provenance, products, streams, raw, sources = None, None, {}, [], {}, {}
    for port in context.input_ports:
        if port.payload_schema == MATRIX_ARRAY_SCHEMA:
            if port.artifact_id in raw: raise ValueError('SCI02 repeats an array operand')
            raw[port.artifact_id] = port
        elif port.payload_schema == Sci02Config.SCHEMA:
            if config is not None: raise ValueError('SCI02 repeats its original configuration')
            config = decode_canonical_bytes(port.read(), Sci02Config, maximum_bytes=port.size_bytes)
        elif port.payload_schema == Sci02Product.SCHEMA:
            product = decode_canonical_bytes(port.read(), Sci02Product, maximum_bytes=port.size_bytes)
            if product.config.node_id in products: raise ValueError('SCI02 repeats a predecessor')
            products[product.config.node_id] = product
        elif port.payload_schema == NumericalProducingProvenance.SCHEMA:
            if provenance is not None: raise ValueError('SCI02 repeats producing provenance')
            provenance = decode_canonical_bytes(port.read(), NumericalProducingProvenance, maximum_bytes=port.size_bytes)
        elif port.payload_schema == MatrixHistorySeed.SCHEMA:
            streams.append(decode_canonical_bytes(port.read(), MatrixHistorySeed, maximum_bytes=port.size_bytes))
        elif port.payload_schema in (Sci02Design.SCHEMA, Sci02Root.SCHEMA):
            kind = Sci02Design if port.payload_schema == Sci02Design.SCHEMA else Sci02Root
            if kind in sources: raise ValueError('SCI02 repeats its actual native source')
            sources[kind] = decode_canonical_bytes(port.read(), kind, maximum_bytes=port.size_bytes)
        else: raise ValueError('SCI02 worker receives a foreign scientific input')
    if (config is None or context.task_id != config.node_id or context.config.config_id != config.config_id
            or context.config.content_sha256 != config.fingerprint() or context.permissions != PERMISSIONS
            or context.resource_budget != BUDGET or context.outcome_access is not ACCESS):
        raise ValueError('SCI02 worker changes its exact configuration or execution contract')
    expected = {key: config_for(config, key) for key in DEPENDENCIES[config.phase]}
    if set(products) != {c.node_id for c in expected.values()}:
        raise ValueError('SCI02 worker changes its original predecessor census')
    products = {key: products[c.node_id] for key, c in expected.items()}
    if any(products[key].config != c for key, c in expected.items()):
        raise ValueError('SCI02 predecessor changes the actual source, recipe or cutoff')
    if config.phase in NATIVE_PHASES:
        if sources != {Sci02Design: config.design, Sci02Root: config.root}:
            raise ValueError('SCI02 native entry omits its actual direct design or root operand')
        if provenance is None or provenance.identity != config.provenance:
            raise ValueError('SCI02 native entry omits its actual direct provenance operand')
        received = []
        for panel, pin in stream_pins(config):
            found = [s for s in streams if ObjectIdentity.from_record(pin.object_id, s) == pin]
            if len(found) != 1: raise ValueError('SCI02 native entry substitutes an actual original stream')
            received.append((panel, found[0]))
        if len(received) != len(streams): raise ValueError('SCI02 native entry adds unselected random material')
        streams = tuple(received)
    elif provenance is not None or streams or sources:
        raise ValueError('SCI02 predictor receives native provenance or random continuation material')
    artifacts = {key: p.arrays for key, p in products.items()}
    if config.phase == 'shadow':
        artifacts['templates'] = config.design.assay
    expected_artifacts = {v.template_artifact.artifact_id if k == 'templates' else v.array_artifact.artifact_id for k, v in artifacts.items()}
    if set(raw) != expected_artifacts:
        raise ValueError('SCI02 worker adds or omits original predecessor array bytes')
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import NPZMemberSelection, decode_matrix_arrays
    arrays = {}
    for key, value in artifacts.items():
        operand = NPZMemberSelection(value.template_artifact, value.template_members) if key == 'templates' else value
        port = raw[operand.array_artifact.artifact_id]
        if (port.payload_schema, port.media_type, port.size_bytes) != (MATRIX_ARRAY_SCHEMA, 'application/x-npz', operand.array_artifact.size_bytes):
            raise ValueError('SCI02 worker substitutes exact original array transport')
        arrays[key] = dict(decode_matrix_arrays(port.read(), operand))
    if config.phase in NATIVE_PHASES:
        validate_native_operands(config, products, arrays, streams)
    return config, products, arrays, provenance, streams


def validate_native_operands(config, parents, arrays, streams):
    phase = config.phase
    count = 64 if phase == 'completion' else 32 if phase == 'response-suffix' else 0
    previous = 'prefix' if phase == 'completion' else 'response-prefix'
    if count and parents[previous].disposition == 'UNAVAILABLE':
        if phase == 'response-suffix': return
        raise ValueError('SCI02 completion cannot enter without its original prefix')
    saved = parents[previous].generators if count else ()
    for panel in ((0,) if phase in ('prefix', 'completion') else (0, 1)):
        science.validate_generators(tuple(s for p, s in streams if p == panel), saved, count, panel)
    if phase == 'completion':
        for view, mult in (('primary', 1), ('fine', 2)):
            state = science.state_at(arrays['prefix'], view)
            if state.step_index != 64 * mult:
                raise ValueError('SCI02 native completion changes its original absolute clock')
    if phase == 'response-prefix':
        for view, mult in (('primary', 1), ('fine', 2)):
            if int(arrays['handoff'][view + '_ticks'][0]) != 256 * mult:
                raise ValueError('SCI02 native response changes its actual handoff clock')
    if phase == 'response-suffix':
        for view, mult in (('primary', 1), ('fine', 2)):
            for panel in (0, 1):
                for action in range(4):
                    for sign in ('hold', 'minus', 'plus'):
                        key = f'branch.{view}.p{panel}.a{action}.{sign}.ticks'
                        if int(arrays['response-prefix'][key][-1]) != 288 * mult:
                            raise ValueError('SCI02 native suffix changes its original response cursor')


def _pack(config, computation, artifact_id):
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
    raw, members = encode_matrix_arrays(computation.arrays)
    artifact = ArtifactIdentity(artifact_id, 'scientific-product', MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    return raw, Sci02Arrays('arrays.' + config.node_id, artifact, members)


def _outputs(context, product, raw):
    payloads = {'product': product.canonical_bytes(), 'arrays': raw}
    if {p.output_id for p in context.output_ports} != {context.task_id + '.' + k for k in payloads}:
        raise ValueError('SCI02 worker changes its compiler-derived output census')
    return RunnerResult(tuple(TaskOutputPayload(context.task_id + '.' + k, v) for k, v in sorted(payloads.items())),
        (ReceiptCheck('sci02-original-source-and-causal-member-census', True, ()),))


def _product(config, parents, computation, operand, native=()):
    return Sci02Product('product.' + config.node_id, config, tuple(sorted((p.identity for p in parents.values()), key=lambda v: v.object_id)),
        operand, computation.disposition, computation.reasons, tuple(sorted(computation.generators, key=lambda r: (r[0], r[1].purpose))), native,
        computation.measurements)


def compute(config, parents, arrays):
    d, phase = config.design, config.phase
    if phase == 'source-state': return science.project_state(arrays['prefix'], tick=64)
    if phase == 'handoff': return science.project_state(arrays['completion'], tick=256)
    if phase == 'shadow': return science.shadow_forecasts(d, arrays['source-state'], arrays['templates'])
    if phase == 'origin':
        if 'forces' not in arrays['shadow']: return science.unavailable('SOURCE_INSTRUMENT_UNAVAILABLE')
        return science.origin_models(d, arrays['handoff'], arrays['shadow'])
    if phase == 'observation':
        if 'unavailable' in arrays['response-prefix']: return science.unavailable('NO_RESPONSE_OBSERVATION')
        return science.project_checkpoint(d, arrays['response-prefix'])
    if phase == 'refresh':
        if 'forces' not in arrays['origin'] or 'unavailable' in arrays['observation']:
            return science.unavailable('NO_CONSTRUCTIBLE_ORIGIN_OR_OBSERVATION')
        return science.refresh_models(d, arrays['origin'], arrays['observation'])
    if phase == 'assess':
        shadow_control = reader.shadow_checks(d, arrays['source-state'], arrays['shadow'])
        result = reader.assess_arm(d, config.recipe, arrays['prefix'], arrays['completion'], arrays['handoff'], arrays['shadow'],
            arrays['origin'], arrays['observation'], arrays['refresh'], arrays['response-prefix'], arrays['response-suffix'])
        # Every sealed shadow is checked independently; retain its full residual population once per source arm.
        return replace(result, arrays={**result.arrays, **{'shadow-control.' + k: v for k, v in shadow_control.items()}})
    if phase == 'reduce': return reader.reduce_root(tuple(parents[r + '.assess'] for r in RECIPES),
        {r: arrays[r + '.assess'] for r in RECIPES})
    raise ValueError('SCI02 pure worker cannot enter native acquisition')


def native_work(context, config, provenance, expected_parent):
    definition = NativeSubworkDefinition('subwork.' + config.node_id, NAMESPACE + '.native.v1', expected_parent,
        config.identity, tuple(sorted((config.design.identity, config.root.identity, provenance.identity), key=lambda v: v.object_id)),
        provenance.code_sources_sha256, provenance.dependency_lock_sha256, tuple(sorted(p.materialization_id for p in context.input_ports)),
        tuple(pin for _, pin in stream_pins(config)),
        (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),
         NativeSubworkOutput('checkpoint', Sci02NativeCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json')))
    roster = NativeSubworkRoster('selected.native-subwork', expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, units(config), slots(config), (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not Sci02NativeRunner: raise TypeError('SCI02 native preparation needs its registered runner')
    config, _, _, provenance, _ = _decode(context)
    return native_work(context, config, provenance, expected_parent)


def acquire(config, parents, arrays, streams, on_step=None):
    if config.phase in ('prefix', 'completion'):
        return science.acquire_preparation_interval(config.design, 'ORIGINAL' if config.phase == 'prefix' else config.recipe,
            tuple(s for p, s in streams), prefix=None if config.phase == 'prefix' else arrays['prefix'],
            saved=() if config.phase == 'prefix' else parents['prefix'].generators, on_step=on_step)
    start = 0 if config.phase == 'response-prefix' else 32
    return science.acquire_response_interval(config.design, arrays['handoff'] if start == 0 else arrays['response-prefix'],
        arrays['shadow'] if start == 0 else arrays['refresh'], streams, start=start,
        saved=() if start == 0 else parents['response-prefix'].generators, on_step=on_step)


class Sci02Runner:
    def __init__(self, *, manifest): self.manifest = manifest

    def execute(self, context):
        try:
            config, parents, arrays, _, _ = _decode(context)
            cpu, wall = time.process_time(), time.monotonic()
            result = compute(config, parents, arrays)
            result = replace(result, measurements=tuple(sorted((*result.measurements,
                ('runtime.science_cpu_seconds', Decimal(str(time.process_time() - cpu))),
                ('runtime.science_wall_seconds', Decimal(str(time.monotonic() - wall)))))))
            output, = (p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, operand = _pack(config, result, output.logical_artifact_id)
            return _outputs(context, _product(config, parents, result, operand), raw)
        finally:
            for port in context.input_ports: port.close()


class Sci02NativeRunner(Sci02Runner):
    def execute(self, context):
        raise ValueError('SCI02 acquisition requires its actual ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, parents, arrays, provenance, streams = _decode(context)
            output, = (p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            # Lack of a physical task is retained explicitly without random draws or contact.
            missing = config.phase == 'response-prefix' and 'forces' not in arrays['shadow'] or config.phase == 'response-suffix' and (
                'unavailable' in arrays['response-prefix'] or 'forces' not in arrays['refresh'])
            if missing:
                result = science.unavailable('SOURCE_OR_CONTINUATION_UNAVAILABLE')
                raw, operand = _pack(config, result, output.logical_artifact_id)
                return _outputs(context, _product(config, parents, result, operand), raw)
            work = native_work(context, config, provenance, native_subwork.parent_contact)
            definition, = work.definitions
            completed = native_subwork.recover(definition)
            if completed is not None:
                if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None or completed.receipt is None
                        or completed.completion.operational_status is not OperationalStatus.SUCCEEDED):
                    raise ValueError('SCI02 refuses unknown or failed native contact replay')
                raw = b''.join(native_subwork.iter_completed_output(definition, 'arrays'))
                checkpoint = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'checkpoint')),
                    Sci02NativeCheckpoint, maximum_bytes=MAX_RECORD)
                if checkpoint.config != config.identity or checkpoint.arrays.array_artifact.artifact_id != output.logical_artifact_id:
                    raise ValueError('SCI02 recovery substitutes its original checkpoint or compiler output')
                from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
                retained = decode_matrix_arrays(raw, checkpoint.arrays)
                result = science.Computation(dict(retained), generators=checkpoint.generators, measurements=checkpoint.measurements)
                operand = checkpoint.arrays
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('SCI02 refuses to replay unreceipted native contact')
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                cpu, wall = time.process_time(), time.monotonic()
                try:
                    result = invoke_native_subwork(native_subwork, entry, acquire, config, parents, arrays, streams,
                        **({'on_step': lambda count: progress.advance(Decimal(count))} if progress is not None else {}))
                    raw, operand = _pack(config, result, output.logical_artifact_id)
                    checkpoint = Sci02NativeCheckpoint('checkpoint.' + config.node_id, config.identity, operand,
                        tuple(sorted(result.generators, key=lambda r: (r[0], r[1].purpose))), result.measurements)
                    for key, payload in (('arrays', raw), ('checkpoint', checkpoint.canonical_bytes())):
                        native_subwork.publish_output(entry, key, (payload,), maximum_bytes=len(payload), maximum_chunk_bytes=len(payload),
                            expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())
                except (ArithmeticError, MemoryError, ValueError):
                    native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), None),
                        cost_scope='SCI02 complete paired interval inside ordinary task', unknown_streams=definition.streams,
                        reason_codes=('matrix-sci02-native-failure',))
                    raise
                completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), Decimal(len(raw))),
                    cost_scope='SCI02 complete paired interval inside ordinary task', consumed_streams=definition.streams,
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
            native = (Sci02NativeHistory(definition, completed.completion, completed.receipt),)
            return _outputs(context, _product(config, parents, result, operand, native), raw)
        finally:
            for port in context.input_ports: port.close()


def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_inquiry as inquiry
    codecs = {kind.SCHEMA: kind for kind in (Sci02Config, Sci02Design, Sci02Root, Sci02Product, Sci02NativeCheckpoint, MatrixHistorySeed, NumericalProducingProvenance)}
    declarations = []
    for phase in sorted(PHASES):
        ports = []
        for key in DEPENDENCIES[phase]:
            ports.append(RecursivePortContract(key.lower() + '-product', Sci02Product.SCHEMA, 'application/json', None))
            ports.append(RecursivePortContract(key.lower() + '-arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES))
        native = phase in NATIVE_PHASES
        if native:
            count = 2 if phase in ('prefix', 'completion') else 4
            ports.extend((RecursivePortContract('native-design', Sci02Design.SCHEMA, 'application/json', MAX_RECORD),
                RecursivePortContract('native-root', Sci02Root.SCHEMA, 'application/json', MAX_RECORD),
                RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_RECORD),
                RecursivePortContract('native-stream', MatrixHistorySeed.SCHEMA, 'application/json', MAX_RECORD, minimum_count=count, maximum_count=count)))
        if phase == 'shadow': ports.append(RecursivePortContract('templates', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES))
        declaration = RecursiveOperationDeclaration(capability_key=NAMESPACE + '.' + phase, capability_version='1.0.0',
            implementation_id=NAMESPACE + '.' + phase + '.v1', kind=CapabilityKind.SIMULATOR if native else CapabilityKind.FALSIFIER if phase == 'assess' else CapabilityKind.ANALYSIS,
            config_record_type=Sci02Config, stage=stage(phase), input_ports=tuple(sorted(ports, key=lambda p: p.port_id)),
            outputs=(OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),
                OutputTemplate('product', Sci02Product.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
            permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=ACCESS, visibility_ceiling=VISIBILITY,
            resources=BUDGET, conformance_check_ids=('sci02-complete-root-census', 'sci02-original-causal-cutoffs', 'sci02-original-stream-continuation'),
            runner_factory=Sci02NativeRunner if native else Sci02Runner, record_codecs=codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operands, scientific_unit_ids=units,
                native_effect_slot_ids=slots if native else None, scientific_root_validator=root_validator),
            execution_properties=RecursiveExecutionProperties(native_effect=native, complete_unit_census=phase == 'prefix',
                native_work_preparer=prepare_native_work if native else None),
            inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=lambda r: r.identity if type(r) is Sci02Product else None,
                inquiry_work_projector=inquiry.inquiry_work_projector, inquiry_endpoint_validator=inquiry.inquiry_endpoint_validator,
                inquiry_evidence_projector=inquiry.inquiry_evidence_projector, inquiry_outcome_projector=inquiry.inquiry_outcome_projector,
                inquiry_claim_assessment_projector=inquiry.inquiry_claim_assessment_projector),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        declarations.append(replace(declaration, runner_factory=partial(declaration.runner_factory, manifest=declaration.manifest())))
    return tuple(declarations)
