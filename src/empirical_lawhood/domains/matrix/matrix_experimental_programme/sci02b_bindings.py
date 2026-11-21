# SPDX-License-Identifier: MPL-2.0
"""SCI02-B retained development on the shared recursive experiment lifecycle."""
from dataclasses import replace
from functools import partial
import time

from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.domains.matrix.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as old
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_development as development
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import NAMESPACE, Sci02BConfig, Sci02BDesign, Sci02BProduct, Sci02BRetainedCase

BUDGET, ACCESS, VISIBILITY, PERMISSIONS, MAX_RECORD = old.BUDGET, old.ACCESS, old.VISIBILITY, old.PERMISSIONS, old.MAX_RECORD
QUESTION = 'Can a causal response description preserve the paired receiver and support economical finite reuse?'
WORLD = 'world.matrix-sci02b.development'


def configs(study, roots, cases, provenance):
    if len(roots) != 8 or tuple(r.ordinal for r in roots) != tuple(range(8)) or len(cases) != 8:
        raise ValueError('SCI02-B development requires the complete original DEV8 census')
    result = []
    for root, case in zip(roots, cases, strict=True):
        for dimension in (24, 32):
            node = f'{NAMESPACE}.{study.fingerprint()[:16]}.{root.group_id}.common.d{dimension}.diagnose'
            result.append(Sci02BConfig('config.' + node, study, (root,), 'diagnose', 'COMMON', provenance,
                retained_cases=(case,), candidate_dimension=dimension))
    node = f'{NAMESPACE}.{study.fingerprint()[:16]}.pool.fit.common.fit'
    result.append(Sci02BConfig('config.' + node, study, roots, 'fit', 'COMMON', provenance, retained_cases=cases))
    return tuple(sorted(result, key=lambda c: c.node_id))


def selected_for(config):
    if config.phase != 'fit': raise ValueError('SCI02-B pooled configuration required')
    return configs(config.study, config.roots, config.retained_cases, config.provenance)


def stage(phase): return ScientificStage.FALSIFY if phase == 'diagnose' else ScientificStage.SYNTHESIZE
def units(config): return tuple(sorted(r.group_id for r in config.roots))
def operands(config):
    return tuple(sorted({config.study.fingerprint(), config.provenance.object_fingerprint,
        *(r.fingerprint() for r in config.roots), *(p.object_fingerprint for p in config.retained_cases)}))


def development_root(selected, study_id):
    pooled, = (c for c in selected if c.phase == 'fit')
    physical = pooled.design
    views = tuple(sorted((physical.coordinate.primary_view.view_id, physical.coordinate.fine_view.view_id)))
    claim = ClaimSpec('claim.' + study_id, WORLD, 'population.matrix-sci02b.original-reservation', QUESTION,
        'Eight original whole roots, two fixed representations, all three preparation arms and complete paired criteria.',
        'unit.original-whole-root', None, EvidenceCeiling.NON_PROMOTABLE, ACCESS, VISIBILITY,
        'Exposed development and bounded continuation only; no molecular qualification or prospective claim.',
        ('assumption.matrix-sci02b.original-nominal-source',), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, pooled.study.original_selection, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        units(pooled), views, (claim,), tuple(sorted({pooled.study.identity, pooled.study.original_selection,
            pooled.provenance, *(r.identity for r in pooled.roots), *pooled.retained_cases}, key=lambda p: p.object_id)))


def external_contracts(cases):
    result = []
    for case in cases:
        result.append(old.source_external(case.identity))
        artifact = case.arrays.array_artifact
        result.append(RecursiveExternalInput('external.' + artifact.artifact_id, artifact.artifact_id, artifact.payload_schema,
            artifact.media_type, artifact.size_bytes, ACCESS, VISIBILITY, artifact.sha256, 'SOURCE'))
    return tuple(sorted(result, key=lambda v: v.input_id))


def input_links(config, cases):
    links = []
    if config.phase == 'diagnose':
        case, = (r for r in cases if r.identity == config.retained_cases[0])
        for key, external in (('retained', 'external.' + case.record_id), ('retained-arrays', 'external.' + case.arrays.array_artifact.artifact_id)):
            links.append(RecursiveInputLink('edge.' + config.node_id + '.' + key, config.node_id, key,
                external_input_id=external, scientific_role='SOURCE'))
    else:
        for parent in selected_for(config):
            if parent.phase != 'diagnose': continue
            label = f'r{parent.root.ordinal:02d}.d{parent.candidate_dimension}'
            for suffix in ('product', 'arrays'):
                key = label + '-' + suffix
                links.append(RecursiveInputLink('edge.' + config.node_id + '.' + key, config.node_id, key,
                    producer_node_id=parent.node_id, producer_output_id=suffix, scientific_role='HISTORY'))
    return tuple(sorted(links, key=lambda v: v.edge_id))


def root_validator(config, context):
    selected = tuple(row.record for row in context.config_inputs)
    pooled = tuple(c for c in selected if type(c) is Sci02BConfig and c.phase == 'fit')
    if len(pooled) != 1 or tuple(sorted(selected, key=lambda c: c.node_id)) != selected_for(pooled[0]):
        raise ValueError('SCI02-B graph changes its complete fixed DEV8 candidate census')
    if (context.root != development_root(selected, context.root.study_id) or context.node_id != config.node_id
            or context.stage is not stage(config.phase) or context.unit_ids != units(config)
            or context.selected_unit_ids != context.root.assigned_unit_ids
            or context.complete_unit_census
            or context.outcome_access is not ACCESS or context.visibility_ceiling is not VISIBILITY):
        raise ValueError('SCI02-B graph substitutes scientific scope or independent units')
    links = tuple(row for row in context.links if row.consumer_node_id == config.node_id)
    if config.phase == 'fit':
        if links != input_links(config, ()):
            raise ValueError('SCI02-B fit omits an original diagnosis')
    else:
        case = config.retained_cases[0]
        expected = {('retained', 'external.' + case.object_id),
            ('retained-arrays', 'external.arrays.sci02b.retained.' + config.root.fingerprint())}
        if len(links) != 2 or {(l.consumer_input_id, l.external_input_id) for l in links} != expected:
            raise ValueError('SCI02-B diagnosis changes its original source ports')
        sources = {v.input_id: v for v in context.external_inputs}
        source = sources.get('external.' + case.object_id)
        if source != old.source_external(case):
            raise ValueError('SCI02-B diagnosis substitutes retained source identity')
    expected_ids = {'external.' + p.object_id for p in pooled[0].retained_cases} | {
        'external.arrays.sci02b.retained.' + root.fingerprint() for root in pooled[0].roots}
    if {e.input_id for e in context.external_inputs} != expected_ids:
        raise ValueError('SCI02-B graph adds unselected source or outcome inputs')


def lower(study, selection, cases, provenance, campaign, *, draft_id):
    roots = tuple(selection.root('DEV', i) for i in range(8))
    if (study.original_selection != selection.identity or study.physical != selection.design
            or tuple(c.root for c in cases) != roots or any(c.design != study.physical for c in cases)):
        raise ValueError('SCI02-B source selection changes original retained roots or physics')
    selected = configs(study, roots, tuple(c.identity for c in cases), provenance.identity)
    declarations = {d.capability_key.rsplit('.', 1)[-1]: d for d in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=c.node_id, selection=declarations[c.phase].registration().selection,
        config_id=c.config_id, config=c, obligation_ids=('obligation.' + c.node_id,), resource_budget=BUDGET) for c in selected)
    root = development_root(selected, 'study.' + draft_id)
    campaign = replace(campaign, objective=QUESTION, system_ids=(root.system.object_id,), world_ids=(WORLD,), target_claim_ids=(root.claims[0].claim_id,))
    draft = RecursiveStudyDraft(draft_id, QUESTION, campaign, (), (), (), operations, external_contracts(cases),
        tuple(sorted((link for c in selected for link in input_links(c, cases)), key=lambda v: v.edge_id)),
        tuple(c.node_id for c in selected), development_study=root)
    return draft, tuple(sorted(('external.' + c.record_id, c) for c in cases))


def decode(context):
    config, products, retained, raw = None, {}, None, {}
    for port in context.input_ports:
        if port.payload_schema == Sci02BConfig.SCHEMA:
            if config is not None: raise ValueError('SCI02-B repeats its configuration')
            config = decode_canonical_bytes(port.read(), Sci02BConfig, maximum_bytes=MAX_RECORD)
        elif port.payload_schema == Sci02BProduct.SCHEMA:
            value = decode_canonical_bytes(port.read(), Sci02BProduct, maximum_bytes=MAX_RECORD)
            if value.config.node_id in products: raise ValueError('SCI02-B repeats a predecessor')
            products[value.config.node_id] = value
        elif port.payload_schema == Sci02BRetainedCase.SCHEMA:
            if retained is not None: raise ValueError('SCI02-B repeats a retained root')
            retained = decode_canonical_bytes(port.read(), Sci02BRetainedCase, maximum_bytes=MAX_RECORD)
        elif port.payload_schema == MATRIX_ARRAY_SCHEMA:
            if port.artifact_id in raw: raise ValueError('SCI02-B repeats an array source')
            raw[port.artifact_id] = port
        else:
            raise ValueError('SCI02-B development receives an undeclared input')
    if (config is None or config.node_id != context.task_id or config.fingerprint() != context.config.content_sha256
            or context.config.config_id != config.config_id or context.resource_budget != BUDGET
            or context.permissions != PERMISSIONS or context.outcome_access is not ACCESS):
        raise ValueError('SCI02-B worker changes its frozen task contract')
    if config.phase == 'diagnose':
        if products or retained is None or retained.identity != config.retained_cases[0] or retained.root != config.root:
            raise ValueError('SCI02-B diagnosis changes the exact original retained source')
        operands = {'retained': retained.arrays}
    elif config.phase == 'fit':
        expected = {c.node_id: c for c in selected_for(config) if c.phase == 'diagnose'}
        if retained is not None or set(products) != set(expected) or any(p.config != expected[k] for k, p in products.items()):
            raise ValueError('SCI02-B fit changes the complete original diagnosis population')
        operands = {k: p.arrays for k, p in products.items()}
    else: raise ValueError('SCI02-B development runner cannot enter another tranche')
    if set(raw) != {v.array_artifact.artifact_id for v in operands.values()}:
        raise ValueError('SCI02-B worker changes its exact source array census')
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    arrays = {}
    for key, operand in operands.items():
        port = raw[operand.array_artifact.artifact_id]
        if port.size_bytes != operand.array_artifact.size_bytes or port.media_type != 'application/x-npz':
            raise ValueError('SCI02-B array transport substitutes an original operand')
        arrays[key] = dict(decode_matrix_arrays(port.read(), operand))
    return config, retained, products, arrays


class Runner:
    def __init__(self, *, manifest): self.manifest = manifest

    def execute(self, context):
        try:
            config, retained, parents, arrays = decode(context)
            cpu, wall = time.process_time(), time.monotonic()
            frozen = None
            if config.phase == 'diagnose': result = development.diagnose(config, retained, arrays['retained'])
            else: result, frozen = development.fit(config, parents, arrays)
            result = science.with_cost(result, cpu, wall)
            output, = (p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, operand = old._pack(config, result, output.logical_artifact_id)
            product = Sci02BProduct('product.' + config.node_id, config,
                tuple(sorted((p.identity for p in parents.values()), key=lambda v: v.object_id)), operand,
                result.disposition, result.reasons, result.measurements, frozen_description=frozen)
            payloads = {'arrays': raw, 'product': product.canonical_bytes()}
            if {p.output_id for p in context.output_ports} != {config.node_id + '.' + k for k in payloads}:
                raise ValueError('SCI02-B worker changes its compiler-derived output census')
            return RunnerResult(tuple(TaskOutputPayload(config.node_id + '.' + k, v) for k, v in sorted(payloads.items())),
                (ReceiptCheck('sci02b-original-retained-population-and-paired-criteria', True, ()),))
        finally:
            for port in context.input_ports: port.close()


def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_inquiry as inquiry
    codecs = {kind.SCHEMA: kind for kind in (Sci02BConfig, Sci02BDesign, Sci02BRetainedCase, Sci02BProduct)}
    result = []
    for phase in ('diagnose', 'fit'):
        if phase == 'diagnose':
            ports = (RecursivePortContract('retained', Sci02BRetainedCase.SCHEMA, 'application/json', MAX_RECORD),
                RecursivePortContract('retained-arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES))
        else:
            ports = tuple(RecursivePortContract(f'r{i:02d}.d{d}-' + suffix, schema, media, bound)
                for i in range(8) for d in (24, 32) for suffix, schema, media, bound in (
                    ('product', Sci02BProduct.SCHEMA, 'application/json', None),
                    ('arrays', MATRIX_ARRAY_SCHEMA, 'application/x-npz', MAXIMUM_MATRIX_ARRAY_BYTES)))
        row = RecursiveOperationDeclaration(capability_key=NAMESPACE + '.' + phase, capability_version='1.0.0',
            implementation_id=NAMESPACE + '.' + phase + '.v1', kind=CapabilityKind.FALSIFIER if phase == 'diagnose' else CapabilityKind.ANALYSIS,
            config_record_type=Sci02BConfig, stage=stage(phase), input_ports=tuple(sorted(ports, key=lambda p: p.port_id)),
            outputs=(OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),
                OutputTemplate('product', Sci02BProduct.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
            permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=ACCESS, visibility_ceiling=VISIBILITY,
            resources=BUDGET, conformance_check_ids=('sci02b-complete-original-root-census', 'sci02b-independent-paired-error-equations'),
            runner_factory=Runner, record_codecs=codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operands, scientific_unit_ids=units,
                scientific_root_validator=root_validator), execution_properties=RecursiveExecutionProperties(),
            inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=lambda p: p.identity if type(p) is Sci02BProduct else None,
                inquiry_work_projector=inquiry.inquiry_work_projector, inquiry_endpoint_validator=inquiry.inquiry_endpoint_validator,
                inquiry_evidence_projector=inquiry.inquiry_evidence_projector, inquiry_outcome_projector=inquiry.inquiry_outcome_projector,
                inquiry_claim_assessment_projector=inquiry.inquiry_claim_assessment_projector),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        result.append(replace(row, runner_factory=partial(Runner, manifest=row.manifest())))
    return tuple(result)
