# SPDX-License-Identifier: MPL-2.0
"""E1 full paired histories, independent witnesses and complete risk reductions.

Pure consumers receive authenticated source and array contracts. Acquisition
is confined to the separate issued native provider. Cold reading calls neither
that provider nor RNG, a producer, nor any eigenvalue decomposition.
"""

from hashlib import sha256


from empirical_lawhood.adapters.methods.matrix_factor_lifetime import science as factor_science
from empirical_lawhood.adapters.methods.matrix_parameter_history import independent as history_independent
from empirical_lawhood.adapters.methods.matrix_parameter_history.science import validate_arrays
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistoryControl, coordinate_identity
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt

from . import pure_math

from .records import (
    VIEWS, E1Arrays, E1FactorAssessment, E1FactorProduct, E1FactorRootRole,
    E1FactorTrace, E1FamilyFinding, E1NumericalAssessment, E1PopulationResult,
    E1FactorPopulation, E1UnavailableRoot, identity,
)


from .pure_math import _survival as _survival

def array_product(source, arrays, *, artifact_id, raw=None):
    validate_arrays(source, arrays)
    encoded, members = encode_matrix_arrays(arrays)
    raw = encoded if raw is None else raw
    artifact = ArtifactIdentity(artifact_id, 'e1-full-native-history', MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    operand = E1Arrays('arrays.'+source.root_id, identity(source), 'NATIVE_HISTORY', artifact, members,
        tuple(sorted((identity(source), coordinate_identity(source.coordinate)), key=lambda x: x.object_id)),
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE)
    # Original compressed bytes stay exact even when their encoding differs.
    decode_matrix_arrays(raw, operand)
    operand.validate_source(source)
    return raw, operand


def consume_arrays(source, operand, raw):
    operand.validate_source(source)
    if operand.role != 'NATIVE_HISTORY':
        raise ValueError('E1 full history consumer receives factor diagnostics')
    arrays = decode_matrix_arrays(raw, operand)
    validate_arrays(source, arrays)
    return arrays


def assess_history(source, history, arrays):
    history.validate_source(source)
    validate_arrays(source, arrays)
    design = source.numerical_design
    rows = history_independent.assess_arrays(source.coordinate, arrays,
        trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance)
    controls = tuple(MatrixParameterHistoryControl(**r) for r in rows)
    result = E1NumericalAssessment('numerical.'+source.root_id, identity(source), identity(history),
        identity(design), controls, all(c.disposition == 'SATISFIED' for c in controls))
    validate_numerical(source, history, result)
    return result


def validate_numerical(source, history, assessment):
    history.validate_source(source)
    n, design = source.coordinate.total_ticks, source.numerical_design
    if (type(assessment) is not E1NumericalAssessment or assessment.source != identity(source)
            or assessment.history != identity(history) or assessment.numerical_design != identity(design)
            or tuple((c.denominator_steps, c.denominator_real_coordinates, c.tolerance) for c in assessment.controls)
            != ((n, 192, design.trajectory_tolerance), (2*n, 192, design.trajectory_tolerance),
                (n, 192, design.bridge_tolerance), (n, 96, design.trajectory_tolerance))):
        raise ValueError('E1 numerical assessment substitutes source or full independent numerical denominators')


def measure(source, history, numerical, native, *, artifact_id):
    """Measure a full selected lattice; create only new E1 trace schemas."""
    validate_numerical(source, history, numerical)
    validate_arrays(source, native)
    rule = source.rule
    role = E1FactorRootRole(source.root_id, source.root.root.independent_group_id, source.coordinate.family_id,
        identity(source), history.arrays.array_artifact, identity(history))
    raw,members,artifact,trace_parts = pure_math.measurement_values(rule,native,artifact_id=artifact_id)
    arrays = E1Arrays('diagnostics.'+source.root_id, identity(source), 'FACTOR_DIAGNOSTICS', artifact, members,
        tuple(sorted((identity(source), identity(history), identity(numerical)), key=lambda x: x.object_id)),
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE)
    traces = tuple(E1FactorTrace(role, identity(rule), v, s, obs, moving, fixed, artifact, members)
        for v, s, obs, moving, fixed in trace_parts)
    product = E1FactorProduct('factor.'+source.root_id, identity(source), identity(history), identity(numerical),
        numerical.numerical_pass, traces, arrays)
    validate_product(source, history, numerical, product)
    return raw, product


def validate_product(source, history, numerical, product):
    validate_numerical(source, history, numerical)
    rule = source.rule
    role = E1FactorRootRole(source.root_id, source.root.root.independent_group_id, source.coordinate.family_id,
        identity(source), history.arrays.array_artifact, identity(history))
    product.arrays.validate_source(source)
    if (type(product) is not E1FactorProduct or product.source != identity(source)
            or product.history != identity(history) or product.numerical_assessment != identity(numerical)
            or product.history_numerical_pass != numerical.numerical_pass
            or product.arrays.producers != tuple(sorted((identity(source), identity(history), identity(numerical)), key=lambda x: x.object_id))
            or tuple((t.view, t.sector) for t in product.traces) != tuple((v, s) for v in VIEWS for s in rule.sectors)):
        raise ValueError('E1 factor product thins full source/history/numerical/view/sector census')
    for trace in product.traces:
        if (trace.root != role or trace.diagnostics != product.arrays.array_artifact
                or trace.diagnostic_members != product.arrays.members):
            raise ValueError('E1 trace substitutes original native root or exact diagnostic custody')
        factor_science.validate_trace(trace, rule)


def assess_factor(source, history, numerical, product, native_raw, diagnostic_raw):
    """Literal raw-state/operator/eigenpair checks, with no eigensolve or RNG."""
    validate_product(source, history, numerical, product)
    native = consume_arrays(source, history.arrays, native_raw)
    arrays = decode_matrix_arrays(diagnostic_raw, product.arrays)
    design = source.specification.selection.factor_numerical_design
    controls = pure_math.factor_control_values(source.rule,design,product.traces,native,arrays)
    return E1FactorAssessment('factor-assessment.'+source.root_id, identity(source), identity(product), identity(design),
        controls, all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in controls))


def authenticate_published(record, receipts):
    """A retained record must be an exact successful prospective sealed output."""
    matches = tuple((r, a) for r in receipts for a in r.output_logical_artifacts
        if a.payload_schema == record.SCHEMA and a.content_sha256 == record.fingerprint())
    if len(matches) != 1:
        raise ValueError('E1 retained record lacks its unique original ordinary completion receipt')
    receipt, logical = matches[0]
    if (type(receipt) is not CanonicalTaskReceipt or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or logical.profile is not ArtifactProfile.CANONICAL_JSON
            or logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise ValueError('E1 retained output cannot promote development, revealed or failed custody')
    physical = tuple(p for p in receipt.output_materializations if p.logical_artifact_id == logical.logical_artifact_id)
    if (len(physical) != 1 or physical[0].physical_sha256 != record.fingerprint()
            or physical[0].size_bytes != len(record.canonical_bytes())):
        raise ValueError('E1 retained canonical bytes differ from original receipted physical output')
    return receipt


def read_retained(source, history, numerical, product, assessment, native_raw, diagnostic_raw, *, receipts):
    """Cold independent reproof over exact original bytes; no fresh science."""
    roles = ((history, 'history'), (numerical, 'numerical'), (product, 'measure'), (assessment, 'check'))
    parent = history.native.definition.parent_contact
    for record, role in roles:
        receipt = authenticate_published(record, receipts)
        if (receipt.task_id != 'matrix-factor-confirmation.'+source.root_id+'.'+role
                or receipt.run_id != parent.run_id or receipt.implementation_commit != parent.implementation_commit
                or role == 'history' and (receipt.attempt_id != parent.attempt_id
                    or receipt.input_materialization_ids != parent.input_materialization_ids)):
            raise ValueError('E1 retained custody changes original operation or producing implementation')
    for record in (history, product):
        receipt = authenticate_published(record, receipts)
        artifact = record.arrays.array_artifact
        arrays = tuple(a for a in receipt.output_logical_artifacts if a.logical_artifact_id == artifact.artifact_id)
        physical = tuple(p for p in receipt.output_materializations if p.logical_artifact_id == artifact.artifact_id)
        if (len(arrays) != 1 or len(physical) != 1
                or (arrays[0].payload_schema, arrays[0].profile, arrays[0].media_type, arrays[0].content_sha256)
                   != (artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, artifact.media_type, artifact.sha256)
                or physical[0].physical_sha256 != artifact.sha256 or physical[0].size_bytes != artifact.size_bytes
                or arrays[0].outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or arrays[0].visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('E1 native/diagnostic arrays lack their original exact protected ordinary receipt')
    native = consume_arrays(source, history.arrays, native_raw)
    if assess_history(source, history, native) != numerical:
        raise ValueError('E1 retained complete independent numerical controls changed')
    observed = assess_factor(source, history, numerical, product, native_raw, diagnostic_raw)
    if observed != assessment:
        raise ValueError('E1 retained literal raw-state factor controls changed')
    return product, assessment




def reduce_population(sources, products, assessments, *, unavailable=()):
    """Frozen complete independent-root inference; no view or tick pooling."""
    sources = tuple(sorted(sources, key=lambda s: s.root_id))
    if not sources:
        raise ValueError('E1 population cannot omit its selected allocation')
    first = sources[0]
    root_ids = tuple(r.root.root_id for r in first.allocation.roots)
    population = E1FactorPopulation('population.'+first.allocation.allocation_id, identity(first.allocation),
        identity(first.rule), root_ids, tuple(identity(s) for s in sources))
    population.validate_sources(sources)
    expected = {identity(s): s for s in sources}
    received = {p.source: p for p in products}
    checked = {a.source: a for a in assessments}
    missing = {u.source: u for u in unavailable}
    if (tuple(s.root_id for s in sources) != root_ids or len(received) != len(products) or len(checked) != len(assessments)
            or len(missing) != len(unavailable) or set(received) & set(missing)
            or set(received) | set(missing) != set(expected) or set(checked) != set(received)
            or any(s.reservation != first.reservation or s.specification != first.specification for s in sources)):
        raise ValueError('E1 population drops, duplicates or substitutes a complete selected root')
    for source_id, source in expected.items():
        if source_id in missing:
            u = missing[source_id]
            evidence = u.receipt if u.receipt is not None else u.contact
            if (type(u) is not E1UnavailableRoot or evidence.implementation_commit != source.provenance.observed_git_head
                    or evidence.task_id not in {f'matrix-factor-confirmation.{source.root_id}.{role}'
                        for role in ('history', 'numerical', 'measure', 'check')}):
                raise ValueError('E1 unavailable census substitutes original root operation/source receipt')
            continue
        p, a = received[source_id], checked[source_id]
        design = source.specification.selection.factor_numerical_design
        n = len(VIEWS)*len(source.rule.sectors)*len(source.rule.lattice)
        expected_controls = tuple(zip((n, 15*n, n, n, n, n), (225, 15, 225, 225, 48, 1),
            (design.operator_tolerance, design.eigenpair_tolerance, design.orthogonality_tolerance,
             design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance), strict=True))
        p.arrays.validate_source(source)
        if (type(p) is not E1FactorProduct or type(a) is not E1FactorAssessment or a.product != identity(p)
                or a.numerical_design != identity(source.specification.selection.factor_numerical_design)
                or tuple((len(c.measured_errors), c.denominator_real_coordinates, c.tolerance) for c in a.controls) != expected_controls
                or p.arrays.producers != tuple(sorted((source_id, p.history, p.numerical_assessment), key=lambda x: x.object_id))
                or tuple((t.view, t.sector) for t in p.traces) != tuple((v, s) for v in VIEWS for s in source.rule.sectors)):
            raise ValueError('E1 population substitutes protected independently assessed complete factor products')
        for trace in p.traces:
            if (trace.root.source != source_id or trace.root.root_id != source.root_id
                    or trace.root.independent_unit_id != source.root.root.independent_group_id
                    or trace.root.family_id != source.coordinate.family_id or trace.root.native_result != p.history
                    or trace.diagnostics != p.arrays.array_artifact or trace.diagnostic_members != p.arrays.members):
                raise ValueError('E1 population substitutes factor root/source/family/dependence')
            factor_science.validate_trace(trace, source.rule)
    criterion, rule = first.criterion, first.rule
    criterion.validate_allocation(first.allocation, rule)
    cells = len(criterion.family_requirements)*len(criterion.views)*len(rule.sectors)*(1+len(criterion.survival_endpoints))
    alpha = (1-criterion.confidence_level)/(cells if criterion.multiplicity == 'BONFERRONI_FROZEN_FAMILY_VIEW_SECTOR_ENDPOINT_MENU' else 1)
    values,risk_rows,status,reasons = pure_math.population_values(sources,received,checked,missing,
        criterion=criterion,rule=rule,alpha=alpha,identity=identity)
    findings = tuple(E1FamilyFinding(**{key:value for key,value in row.items()
        if key not in ('excluded_late_survival_roots','unresolved_onset_roots')}) for row in values)
    return E1PopulationResult('result.'+criterion.criterion_id, population, identity(criterion), root_ids,
        tuple(identity(received[identity(s)]) for s in sources if identity(s) in received),
        tuple(identity(checked[identity(s)]) for s in sources if identity(s) in checked),
        tuple(missing[identity(s)] for s in sources if identity(s) in missing), tuple(findings), tuple(risk_rows), status, reasons)
