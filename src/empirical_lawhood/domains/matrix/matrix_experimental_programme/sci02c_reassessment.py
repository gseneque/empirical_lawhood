# SPDX-License-Identifier: MPL-2.0
"""Additive PURE calibration readback over the exact settled SCI02-C receipts."""
from dataclasses import dataclass, replace
from functools import partial
import time
from typing import ClassVar

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as owner
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as original_read
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, RECIPES
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CConfig, Sci02CProduct, ROOT_PHASES, COMMON

NAMESPACE = 'matrix-sci02c-retained'
MAX_RECORD = 64 * 1024**2


@dataclass(frozen=True, slots=True)
class RetainedCalibrationRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/retained-calibration-root'
    record_id: str
    original: Sci02CConfig
    original_plan: ObjectIdentity
    original_terminal: ObjectIdentity
    products: tuple[Sci02CProduct, ...]
    receipts: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        c = self.original
        if (c.phase != 'reduce' or c.root.bank != 'DEV' or not 8 <= c.root.ordinal < 16
                or len(self.products) != 25 or len(self.receipts) != 25):
            raise ValueError('SCI02-C retained readback requires all 25 original completed operations per calibration root')
        expected = tuple(sorted((owner.make_config(c.study, c.roots, phase, recipe, c.provenance, model=c.model)
            for phase in ROOT_PHASES if phase not in ('assess', 'reduce')
            for recipe in (('COMMON',) if phase in COMMON else RECIPES)), key=lambda v: v.node_id))
        if tuple(p.config for p in self.products) != expected or any(p.disposition != 'AVAILABLE' for p in self.products):
            raise ValueError('SCI02-C retained readback changes original source, sealed decisions or complete native population')
        if tuple(p.object_id for p in self.receipts) != tuple(sorted({p.object_id for p in self.receipts})):
            raise ValueError('SCI02-C retained readback repeats or reorders original receipts')
        for value in (c, self.original_plan, self.original_terminal, *self.products, *self.receipts): value.__post_init__()

    @property
    def identity(self): return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class ReassessmentConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/reassessment-config'
    config_id: str
    operation: Sci02CConfig
    retained: tuple[RetainedCalibrationRoot, ...]

    def __post_init__(self):
        c = self.operation
        if (c.phase not in ('reduce', 'calibrate') or self.config_id != 'readback.' + c.config_id
                or len(self.retained) != len(c.roots) or tuple(r.original.root for r in self.retained) != c.roots
                or any((r.original.study, r.original.model) != (c.study, c.model) for r in self.retained)
                or len({r.original_plan for r in self.retained}) != 1
                or len({r.original_terminal for r in self.retained}) != 1):
            raise ValueError('SCI02-C reassessment changes original complete calibration or its frozen account')
        c.__post_init__()
        for r in self.retained: r.__post_init__()

    @property
    def node_id(self): return self.operation.node_id

    @property
    def phase(self): return self.operation.phase


def selected_for(pooled):
    c = pooled.operation
    return tuple(sorted((pooled, *(ReassessmentConfig('readback.config.' + owner.make_config(c.study, (r.original.root,),
        'reduce', 'COMMON', c.provenance, model=c.model).node_id,
        owner.make_config(c.study, (r.original.root,), 'reduce', 'COMMON', c.provenance, model=c.model), (r,))
        for r in pooled.retained)), key=lambda v: v.node_id))


def external_contracts(selected):
    return tuple(sorted((RecursiveExternalInput('external.' + p.arrays.array_artifact.artifact_id,
        p.arrays.array_artifact.artifact_id, MATRIX_ARRAY_SCHEMA, 'application/x-npz', p.arrays.array_artifact.size_bytes,
        owner.ACCESS, owner.VISIBILITY, p.arrays.array_artifact.sha256, 'HISTORY')
        for c in selected if c.phase == 'reduce' for p in c.retained[0].products), key=lambda v: v.input_id))


def links(config):
    result = []
    if config.phase == 'reduce':
        for i, p in enumerate(config.retained[0].products):
            result.append(RecursiveInputLink('edge.' + config.node_id + f'.original{i:02d}', config.node_id, f'original-arrays.{i:02d}',
                external_input_id='external.' + p.arrays.array_artifact.artifact_id, scientific_role='HISTORY'))
    else:
        for r in config.retained:
            node = owner.make_config(config.operation.study, (r.original.root,), 'reduce', 'COMMON',
                config.operation.provenance, model=config.operation.model).node_id
            for suffix in ('product', 'arrays'):
                port = f'r{r.original.root.ordinal:02d}-' + suffix
                result.append(RecursiveInputLink('edge.' + config.node_id + '.' + port, config.node_id, port,
                    producer_node_id=node, producer_output_id=suffix, scientific_role='HISTORY'))
    return tuple(sorted(result, key=lambda v: v.edge_id))


def scientific_root(selected, study_id):
    root = owner.development_root(tuple(c.operation for c in selected), study_id)
    operands = {*root.scientific_operands, *(r.identity for c in selected for r in c.retained)}
    return replace(root, scientific_operands=tuple(sorted(operands, key=lambda v: v.object_id)))


def root_validator(config, context):
    selected = tuple(v.record for v in context.config_inputs)
    pools = tuple(v for v in selected if type(v) is ReassessmentConfig and v.phase == 'calibrate')
    if (len(pools) != 1 or selected != selected_for(pools[0]) or context.node_id != config.node_id
            or context.root != scientific_root(selected, context.root.study_id)
            or context.links != tuple(sorted((l for c in selected for l in links(c)), key=lambda v: v.edge_id))
            or context.external_inputs != external_contracts(selected) or context.requirements or context.connections
            or context.unit_ids != owner.units(config.operation) or context.selected_unit_ids != context.root.assigned_unit_ids
            or context.stage is not ScientificStage.SYNTHESIZE or context.complete_unit_census
            or context.outcome_access is not owner.ACCESS or context.visibility_ceiling is not owner.VISIBILITY):
        raise ValueError('SCI02-C reassessment changes its exact PURE original-receipt graph')


def lower(cases, provenance, campaign, *, draft_id):
    roots = tuple(r.original.root for r in cases)
    first = cases[0].original
    operation = owner.make_config(first.study, roots, 'calibrate', 'COMMON', provenance.identity, model=first.model)
    pooled = ReassessmentConfig('readback.' + operation.config_id, operation, cases)
    selected = selected_for(pooled)
    declarations = {d.capability_key.rsplit('.', 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id, selection=declarations[c.phase].registration().selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.' + c.node_id,), resource_budget=owner.BUDGET) for c in selected)
    root = scientific_root(selected, 'study.' + draft_id)
    campaign = replace(campaign, objective=owner.QUESTION, system_ids=(root.system.object_id,), world_ids=(owner.WORLD,),
        target_claim_ids=(root.claims[0].claim_id,))
    return RecursiveStudyDraft(draft_id, owner.QUESTION, campaign, (), (), (), operations, external_contracts(selected),
        tuple(sorted((l for c in selected for l in links(c)), key=lambda v: v.edge_id)), tuple(c.node_id for c in selected), development_study=root)


def reassess(config, arrays):
    case, = config.retained
    records = {p.config.node_id: p for p in case.products}
    values = dict(arrays)
    # Re-read the deterministic causal projections and the original sealed policy.
    for p in case.products:
        c = p.config
        if c.phase in ('source-state', 'handoff', 'observation', 'history-observation', 'request', 'decision'):
            parents = {k: records[v.node_id] for k, v in owner.parents_for(c).items()}
            operands = {k: values[v.config.node_id] for k, v in parents.items()}
            expected, _, _ = owner.compute(c, parents, operands, None)
            actual = values[c.node_id]
            if set(actual) != set(expected.arrays): raise ValueError('SCI02-C readback loses a causal projection member')
            for key, value in expected.arrays.items(): original_read.same(actual[key], value, 'SCI02-C retained causal projection')
    for recipe in RECIPES:
        c = owner.make_config(case.original.study, case.original.roots, 'assess', recipe,
            case.original.provenance, model=case.original.model)
        values[c.node_id] = reader.assess_arm(c, {k: values[v.node_id] for k, v in owner.parents_for(c).items()}).arrays
    operands = {k: values[v.node_id] for k, v in owner.parents_for(case.original).items()}
    result, _, _ = owner.compute(config.operation, {}, operands, None)
    return result


def decode(context):
    configs, products, raw = [], [], {}
    for port in context.input_ports:
        if port.payload_schema == ReassessmentConfig.SCHEMA:
            configs.append(decode_canonical_bytes(port.read(), ReassessmentConfig, maximum_bytes=MAX_RECORD))
        elif port.payload_schema == Sci02CProduct.SCHEMA:
            products.append(decode_canonical_bytes(port.read(), Sci02CProduct, maximum_bytes=owner.MAX_RECORD))
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA:
            if port.artifact_id in raw: raise ValueError('SCI02-C reassessment repeats an array input')
            raw[port.artifact_id] = port
        else: raise ValueError('SCI02-C reassessment receives an unselected input')
    c, = configs
    if (c.node_id != context.task_id or c.config_id != context.config.config_id or c.fingerprint() != context.config.content_sha256
            or context.resource_budget != owner.BUDGET or context.permissions != owner.PERMISSIONS or context.outcome_access is not owner.ACCESS):
        raise ValueError('SCI02-C reassessment changes its selected immutable execution')
    if c.phase == 'reduce':
        if products: raise ValueError('SCI02-C retained root cannot consume another new outcome')
        sources = c.retained[0].products
    else:
        expected = {v.node_id: v.operation for v in selected_for(c) if v.phase == 'reduce'}
        if len(products) != 8 or {p.config.node_id: p.config for p in products} != expected:
            raise ValueError('SCI02-C calibration changes its complete reassessed population')
        sources = products
    if set(raw) != {p.arrays.array_artifact.artifact_id for p in sources}:
        raise ValueError('SCI02-C reassessment changes its exact original array census')
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    arrays = {}
    for p in sources:
        a = p.arrays.array_artifact
        port = raw[a.artifact_id]
        if port.size_bytes != a.size_bytes or port.media_type != a.media_type:
            raise ValueError('SCI02-C reassessment changes original array transport')
        arrays[p.config.node_id] = dict(decode_matrix_arrays(port.read(), p.arrays))
    return c, tuple(sources), arrays


class Runner:
    def __init__(self, *, manifest): self.manifest = manifest

    def execute(self, context):
        try:
            c, sources, arrays = decode(context)
            started, wall = time.process_time(), time.monotonic()
            parents = {p.config.node_id: p for p in sources}
            if c.phase == 'reduce': result, calibrated = reassess(c, arrays), None
            else: result, calibrated = science.calibrate(c.operation, parents, arrays)
            result = science.with_cost(result, started, wall)
            output, = (o for o in context.output_ports if o.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, operand = owner.old._pack(c.operation, result, output.logical_artifact_id)
            return owner.old._outputs(context, owner.product(c.operation, parents, result, operand, calibration=calibrated), raw)
        finally:
            for port in context.input_ports: port.close()


def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    rows = []
    for phase in ('calibrate', 'reduce'):
        ports = (RecursivePortContract('original-arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES,
            minimum_count=25, maximum_count=25),) if phase == 'reduce' else tuple(
                RecursivePortContract(f'r{i:02d}-' + suffix, schema, media, maximum)
                for i in range(8, 16) for suffix, schema, media, maximum in (
                    ('arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES),
                    ('product', Sci02CProduct.SCHEMA, 'application/json', None)))
        row = RecursiveOperationDeclaration(capability_key=NAMESPACE + '.' + phase, capability_version='1.0.0',
            implementation_id=NAMESPACE + '.' + phase + '.v1', kind=CapabilityKind.ANALYSIS,
            config_record_type=ReassessmentConfig, stage=ScientificStage.SYNTHESIZE, input_ports=ports,
            outputs=(OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),
                OutputTemplate('product', Sci02CProduct.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
            permissions=owner.PERMISSIONS, evidence_ceiling=owner.EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=owner.ACCESS, visibility_ceiling=owner.VISIBILITY, resources=owner.BUDGET,
            conformance_check_ids=('sci02c-independent-consumer-readback', 'sci02c-retained-native-custody-no-reacquisition'),
            runner_factory=Runner, record_codecs={k.SCHEMA: k for k in (ReassessmentConfig, RetainedCalibrationRoot, Sci02CProduct)},
            scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({*owner.operands(c.operation),
                *(r.fingerprint() for r in c.retained)})), scientific_unit_ids=lambda c: owner.units(c.operation),
                scientific_root_validator=root_validator), execution_properties=RecursiveExecutionProperties(),
            provenance_requirements=(owner.MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        rows.append(replace(row, runner_factory=partial(Runner, manifest=row.manifest())))
    return tuple(rows)
