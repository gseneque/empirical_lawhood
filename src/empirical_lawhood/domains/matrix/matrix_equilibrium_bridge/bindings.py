# SPDX-License-Identifier: MPL-2.0
"""Finite SCI02-D operations on the existing recursive execution lifecycle."""
from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256
import time
from types import MappingProxyType

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as shared
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, Sci02Arrays
from empirical_lawhood.domains.matrix.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract, RecursiveScientificRootPreparationContext
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import assessment, science
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BANK_COUNTS, NAMESPACE, PHASES, BridgeCheckpoint, BridgeConfig, BridgeDesign, BridgeFit, BridgeProduct, BridgeRoot, BridgeSelection, BridgeStream

# Native subwork and ordinary parent publication both consume the invocation
# allowance. Reference bundles retain both copies of their three array shards.
BUDGET = replace(shared.BUDGET, output_bytes=384 * 1024**2)
ACCESS, VISIBILITY, PERMISSIONS, MAX_RECORD = shared.ACCESS, shared.VISIBILITY, shared.PERMISSIONS, shared.MAX_RECORD
QUESTION = 'Can a frozen equilibrium response control reduce the complete cost of a precise finite paired integral?'
WORLD = 'world.matrix-sci02d.finite-canonical-target'
VIEWS = ('matrix-sci02d.fine', 'matrix-sci02d.primary')


def stage(phase):
    return ScientificStage.ACQUIRE if phase == 'sample' else ScientificStage.FALSIFY if phase in ('controls', 'assess') else ScientificStage.SYNTHESIZE


def make_config(design, selection, roots, phase, provenance, fitted=None):
    unit = roots[0].group_id if len(roots) == 1 else 'pool'
    node = f'{NAMESPACE}.{design.fingerprint()[:16]}.{unit}.{phase}'
    return BridgeConfig('config.'+node, design, selection, roots, phase, provenance, fitted)


def configs(design, selection, roots, provenance, fitted=None):
    banks = ('TRAINING',) if fitted is None else ('CONFIRMATION', 'REFERENCE')
    expected = tuple((bank, i) for bank in banks for i in range(BANK_COUNTS[bank]))
    if tuple((r.bank, r.ordinal) for r in roots) != expected:
        raise ValueError('SCI02-D graph changes its complete committed bank census')
    selected = [make_config(design, selection, (root,), phase, provenance, fitted)
        for root in roots for phase in ('sample', 'assess')]
    selected.append(make_config(design, selection, roots, 'fit' if fitted is None else 'confirm', provenance, fitted))
    if fitted is None: selected.append(make_config(design, selection, (), 'controls', provenance))
    return tuple(sorted(selected, key=lambda c: c.node_id))


def selected_for(pooled):
    if pooled.phase not in ('fit', 'confirm'): raise ValueError('SCI02-D needs its complete pooled selection')
    return configs(pooled.design, pooled.selection, pooled.roots, pooled.provenance, pooled.fitted)


def parents_for(config):
    if config.phase in ('fit', 'confirm'):
        result = {f'{r.bank.lower()}{r.ordinal:02d}': make_config(config.design, config.selection, (r,), 'assess', config.provenance, config.fitted) for r in config.roots}
        if config.phase == 'fit': result['controls'] = make_config(config.design, config.selection, (), 'controls', config.provenance)
        return result
    if config.phase == 'assess':
        return {'sample': make_config(config.design, config.selection, config.roots, 'sample', config.provenance, config.fitted)}
    if config.phase == 'sample' and config.root.bank == 'TRAINING':
        return {'controls': make_config(config.design, config.selection, (), 'controls', config.provenance)}
    return {}


def units(config):
    if config.phase == 'controls':
        return tuple(f'sci02d.{config.selection.object_fingerprint}.training.{i:02d}' for i in range(BANK_COUNTS['TRAINING']))
    return tuple(r.group_id for r in config.roots)
def slots(config): return (config.node_id+'.native',)
def operands(config):
    return tuple(sorted({config.design.fingerprint(), config.selection.object_fingerprint, config.provenance.object_fingerprint,
        *(r.fingerprint() for r in config.roots), *(() if config.fitted is None else (config.fitted.fingerprint(),))}))


def development_root(selected, study_id):
    pooled, = (c for c in selected if c.phase in ('fit', 'confirm'))
    claim = ClaimSpec('claim.'+study_id, WORLD, 'population.matrix-sci02d.independent-bundles', QUESTION,
        'Complete original bank; two coupled Hamiltonians, two starting histories and two numerical views.',
        'unit.independent-bundle', None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        'Numerical estimator development; neither equilibrium state coverage nor molecular qualification.',
        ('assumption.matrix-sci02d.canonical-target',), numerical_view_ids=VIEWS)
    return DevelopmentStudySpec(study_id, QUESTION, pooled.selection, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        units(pooled), VIEWS, (claim,), tuple(sorted({pooled.design.identity, pooled.selection, pooled.provenance,
            *(r.identity for r in pooled.roots), *(() if pooled.fitted is None else (pooled.fitted.identity,))}, key=lambda p: p.object_id)))


def external_contracts(selected):
    result = {}
    for c in selected:
        if c.phase != 'sample': continue
        for pin in (c.design.identity, c.root.identity, c.provenance, *c.root.streams):
            row = shared.source_external(pin); result[row.input_id] = row
    return tuple(sorted(result.values(), key=lambda p: p.input_id))


def input_links(config):
    links = []
    for key, parent in parents_for(config).items():
        for suffix in ('product', 'arrays', *(('positions', 'gradients') if parent.phase == 'sample' else ())):
            port = key+'-'+suffix
            links.append(RecursiveInputLink('edge.'+config.node_id+'.'+port, config.node_id, port,
                producer_node_id=parent.node_id, producer_output_id=suffix, scientific_role='HISTORY'))
    if config.phase == 'sample':
        for key, pin in (('native-design', config.design.identity), ('native-root', config.root.identity),
                ('native-provenance', config.provenance), *(('native-stream.'+p.object_fingerprint, p) for p in config.root.streams)):
            links.append(RecursiveInputLink('edge.'+config.node_id+'.'+key, config.node_id, key,
                external_input_id='external.'+pin.object_id, scientific_role='SOURCE'))
    return tuple(sorted(links, key=lambda p: p.edge_id))


@dataclass(frozen=True, slots=True, eq=False)
class ScientificPreparation:
    batch: RecursiveScientificRootPreparationContext
    node_configs: object


def prepare_root(batch):
    if type(batch) is not RecursiveScientificRootPreparationContext: raise TypeError('SCI02-D requires shared scientific preparation')
    selected = tuple(v.record for v in batch.config_inputs)
    pooled = tuple(c for c in selected if type(c) is BridgeConfig and c.phase in ('fit', 'confirm'))
    if (len(pooled) != 1 or tuple(sorted(selected, key=lambda c: c.node_id)) != selected_for(pooled[0])
            or batch.root != development_root(selected, batch.root.study_id)
            or batch.links != tuple(sorted((l for c in selected for l in input_links(c)), key=lambda l: l.edge_id))
            or batch.external_inputs != external_contracts(selected) or batch.requirements or batch.connections
            or any(v != batch.root.assigned_unit_ids for v in batch.selected_unit_ids_by_selection.values())):
        raise ValueError('SCI02-D changes complete roots, original source ports or scientific scope')
    return ScientificPreparation(batch, MappingProxyType({v.node_id: v.record for v in batch.config_inputs}))


def root_validator(config, context):
    prepared = context.scientific_preparation
    if type(prepared) is not ScientificPreparation: raise ValueError('SCI02-D requires invocation-local preparation')
    batch = prepared.batch
    if (prepared.node_configs.get(context.node_id) is not config or context.root is not batch.root
            or context.config_inputs is not batch.config_inputs or context.links is not batch.links
            or context.external_inputs is not batch.external_inputs or context.requirements is not batch.requirements
            or context.connections is not batch.connections or context.qualifications is not batch.qualifications
            or context.known_design_inputs is not batch.known_design_inputs
            or context.node_id != config.node_id or context.stage is not stage(config.phase) or context.unit_ids != units(config)
            or context.selected_unit_ids != context.root.assigned_unit_ids or context.complete_unit_census != (config.phase == 'sample')
            or context.outcome_access is not ACCESS or context.visibility_ceiling is not VISIBILITY):
        raise ValueError('SCI02-D changes exact prepared invocation or original scientific boundary')


def lower(design, selection, roots, provenance, campaign, *, draft_id, fitted=None):
    if selection.design != design or any(r != selection.root(r.bank, r.ordinal) for r in roots):
        raise ValueError('SCI02-D substitutes committed native sources or allocation')
    selected = configs(design, selection.identity, roots, provenance.identity, fitted)
    declarations = {d.capability_key.rsplit('.', 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id, selection=declarations[c.phase].registration().selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.'+c.node_id,), resource_budget=BUDGET) for c in selected)
    root = development_root(selected, 'study.'+draft_id)
    campaign = replace(campaign, objective=QUESTION, system_ids=(root.system.object_id,), world_ids=(WORLD,), target_claim_ids=(root.claims[0].claim_id,))
    draft = RecursiveStudyDraft(draft_id, QUESTION, campaign, (), (), (), operations, external_contracts(selected),
        tuple(sorted((l for c in selected for l in input_links(c)), key=lambda l: l.edge_id)), tuple(c.node_id for c in selected), development_study=root)
    records = {}
    for root in roots:
        for value in (design, root, provenance, *selection.streams(root.bank, root.ordinal)):
            records['external.'+value.identity.object_id] = value
    return draft, tuple(sorted(records.items()))


def decode(context):
    kinds = {c.SCHEMA: c for c in (BridgeConfig, BridgeProduct, BridgeDesign, BridgeRoot, BridgeStream, NumericalProducingProvenance)}
    decoded, raw = {}, {}
    for port in context.input_ports:
        if port.payload_schema == MATRIX_ARRAY_SCHEMA:
            if port.artifact_id in raw: raise ValueError('SCI02-D repeats an array input')
            raw[port.artifact_id] = port
        else:
            kind = kinds.get(port.payload_schema)
            if kind is None: raise ValueError('SCI02-D receives an unselected scientific input')
            decoded.setdefault(kind, []).append(decode_canonical_bytes(port.read(), kind, maximum_bytes=MAX_RECORD))
    config, = decoded.pop(BridgeConfig, ())
    if (config.node_id != context.task_id or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256
            or context.resource_budget != BUDGET or context.permissions != PERMISSIONS or context.outcome_access is not ACCESS):
        raise ValueError('SCI02-D changes its compiler-derived worker contract')
    received = decoded.pop(BridgeProduct, ())
    products = {p.config.node_id: p for p in received}; expected = parents_for(config)
    if (len(products) != len(received) or set(products) != {c.node_id for c in expected.values()}
            or any(products[c.node_id].config != c for c in expected.values())):
        raise ValueError('SCI02-D changes its complete original predecessor population')
    products = {key: products[c.node_id] for key, c in expected.items()}
    provenance, streams = None, ()
    if config.phase == 'sample':
        design, = decoded.pop(BridgeDesign, ()); root, = decoded.pop(BridgeRoot, ())
        provenance, = decoded.pop(NumericalProducingProvenance, ())
        streams = tuple(sorted(decoded.pop(BridgeStream, ()), key=lambda s: s.record_id))
        if (design != config.design or root != config.root or provenance.identity != config.provenance
                or tuple(s.identity for s in streams) != config.root.streams):
            raise ValueError('SCI02-D native entry changes original direct source or committed streams')
        if 'controls' in products and products['controls'].disposition != 'AVAILABLE':
            raise ValueError('SCI02-D solvable controls did not establish its estimator construction')
    if decoded: raise ValueError('SCI02-D pure operation receives unselected source or random material')
    selected_arrays = {key: (p.arrays, *p.shards) for key, p in products.items()}
    if set(raw) != {a.array_artifact.artifact_id for values in selected_arrays.values() for a in values}:
        raise ValueError('SCI02-D changes the complete bounded array census')
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    arrays = {}
    for key, values in selected_arrays.items():
        arrays[key] = {}
        for a in values:
            port = raw[a.array_artifact.artifact_id]
            if port.media_type != 'application/x-npz' or port.size_bytes != a.array_artifact.size_bytes:
                raise ValueError('SCI02-D changes original array transport')
            part = dict(decode_matrix_arrays(port.read(), a))
            if set(part) & set(arrays[key]): raise ValueError('SCI02-D repeats a sharded array member')
            arrays[key].update(part)
    return config, products, arrays, provenance, streams


def pack(config, result, output_ids):
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
    groups = {'arrays': {k: v for k, v in result.arrays.items() if config.phase != 'sample' or k not in ('positions', 'gradients')}}
    if config.phase == 'sample': groups.update({k: {k: result.arrays[k]} for k in ('positions', 'gradients')})
    payloads, operands = {}, {}
    for key, values in sorted(groups.items()):
        raw, members = encode_matrix_arrays(values)
        artifact = ArtifactIdentity(output_ids[key], 'scientific-product', MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
        payloads[key], operands[key] = raw, Sci02Arrays(key+'.'+config.node_id, artifact, members)
    return payloads, operands


def product(config, parents, result, operands, *, native=(), fitted=None):
    return BridgeProduct('product.'+config.node_id, config, tuple(sorted((p.identity for p in parents.values()), key=lambda p: p.object_id)),
        operands['arrays'], result.disposition, result.reasons, result.measurements, native, fitted,
        tuple(operands[k] for k in ('positions', 'gradients')) if config.phase == 'sample' else ())


def outputs(context, product, payloads):
    payloads = {**payloads, 'product': product.canonical_bytes()}
    if {p.output_id for p in context.output_ports} != {context.task_id+'.'+k for k in payloads}:
        raise ValueError('SCI02-D changes compiler-derived output census')
    return RunnerResult(tuple(TaskOutputPayload(context.task_id+'.'+k, v) for k, v in sorted(payloads.items())),
        (ReceiptCheck('sci02d-original-native-or-independent-assessment-custody', True, ()),))


def compute(config, products, arrays):
    fitted = None
    if config.phase == 'controls': result = science.controls()
    elif config.phase == 'assess': result = assessment.assess(config, arrays['sample'])
    else:
        parents = {p.config.node_id: p for p in products.values()}
        values = {p.config.node_id: arrays[k] for k, p in products.items()}
        if config.phase == 'fit': result, fitted = science.fit(config, parents, values)
        elif config.phase == 'confirm': result = science.confirm(config, parents, values)
        else: raise ValueError('SCI02-D pure operation cannot acquire native science')
    return result, fitted


class Runner:
    def __init__(self, *, manifest): self.manifest = manifest
    def execute(self, context):
        try:
            config, parents, arrays, _, _ = decode(context)
            cpu, wall = time.process_time(), time.monotonic()
            result, fitted = compute(config, parents, arrays)
            result = science.with_cost(result, cpu, wall)
            ids = {p.output_id.rsplit('.', 1)[-1]: p.logical_artifact_id for p in context.output_ports}
            raw, operands = pack(config, result, ids)
            return outputs(context, product(config, parents, result, operands, fitted=fitted), raw)
        finally:
            for port in context.input_ports: port.close()


def port_contracts(phase):
    keys = () if phase == 'controls' else ('controls',) if phase == 'sample' else ('sample',) if phase == 'assess' else (
        ('controls', *(f'training{i:02d}' for i in range(16))) if phase == 'fit' else
        (*(f'confirmation{i:02d}' for i in range(64)), *(f'reference{i:02d}' for i in range(8))))
    ports = []
    for key in keys:
        ports.append(RecursivePortContract(key+'-product', BridgeProduct.SCHEMA, 'application/json', None, minimum_count=0 if phase == 'sample' else 1))
        for suffix in ('arrays', *(('positions', 'gradients') if phase == 'assess' else ())):
            ports.append(RecursivePortContract(key+'-'+suffix, MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES,
                minimum_count=0 if phase == 'sample' else 1))
    if phase == 'sample':
        ports.extend((RecursivePortContract('native-design', BridgeDesign.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('native-root', BridgeRoot.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_RECORD),
            RecursivePortContract('native-stream', BridgeStream.SCHEMA, 'application/json', MAX_RECORD, minimum_count=3, maximum_count=3)))
    return tuple(sorted(ports, key=lambda p: p.port_id))


def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import inquiry
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.native import NativeRunner, prepare_native_work
    codecs = {kind.SCHEMA: kind for kind in (BridgeConfig, BridgeDesign, BridgeSelection, BridgeRoot, BridgeStream, BridgeFit, BridgeProduct, BridgeCheckpoint, NumericalProducingProvenance)}
    rows = []
    for phase in sorted(PHASES):
        native = phase == 'sample'
        row = RecursiveOperationDeclaration(capability_key=NAMESPACE+'.'+phase, capability_version='1.0.0', implementation_id=NAMESPACE+'.'+phase+'.v1',
            kind=CapabilityKind.SIMULATOR if native else CapabilityKind.FALSIFIER if phase in ('controls', 'assess') else CapabilityKind.ANALYSIS,
            config_record_type=BridgeConfig, stage=stage(phase), input_ports=port_contracts(phase),
            outputs=tuple(OutputTemplate(key, MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz')
                for key in ('arrays', *(('gradients', 'positions') if native else ())))+(
                OutputTemplate('product', BridgeProduct.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
            permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=ACCESS, visibility_ceiling=VISIBILITY,
            resources=BUDGET, conformance_check_ids=('sci02d-complete-population-and-frozen-coefficients', 'sci02d-native-force-and-stein-equations'),
            runner_factory=NativeRunner if native else Runner, record_codecs=codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operands, scientific_unit_ids=units,
                native_effect_slot_ids=slots if native else None, scientific_root_preparer=prepare_root, scientific_root_validator=root_validator),
            execution_properties=RecursiveExecutionProperties(native_effect=native, complete_unit_census=native,
                native_work_preparer=prepare_native_work if native else None),
            inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=lambda p: p.identity if type(p) is BridgeProduct else None,
                inquiry_work_projector=inquiry.inquiry_work_projector, inquiry_endpoint_validator=inquiry.inquiry_endpoint_validator,
                inquiry_evidence_projector=inquiry.inquiry_evidence_projector, inquiry_outcome_projector=inquiry.inquiry_outcome_projector,
                inquiry_claim_assessment_projector=inquiry.inquiry_claim_assessment_projector),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        rows.append(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest())))
    return tuple(rows)
