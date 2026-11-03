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
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import ScientificStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.recovery import RunRecoveryIndex, RunRecoveryTerminalEvent

from . import pure_math

from .compact_records import (
    VIEWS, E1CompactArrays, E1CompactFactorAssessment, E1CompactFactorProduct, E1CompactFactorRootRole,
    E1CompactFactorTrace, E1CompactNumericalAssessment, E1CompactPopulationResult,
    E1CompactManifest, sources_for_manifest, E1CompactUnavailableRoot, identity,
    E1CompactClosedRoot, E1CompactClosedPopulationResult, NAMESPACE, PHASES,
)
from .occurrence import occurrence_cells, root_occurrence
from .records import E1RiskRow


from .science import consume_arrays as consume_arrays

from .science import authenticate_published as authenticate_published

from .pure_math import _survival as _survival

def array_product(source, arrays, *, artifact_id, raw=None):
    validate_arrays(source, arrays)
    if raw is None:
        raw, members = encode_matrix_arrays(arrays)
    else:
        members = matrix_array_members(arrays)
    artifact = ArtifactIdentity(artifact_id, 'e1-full-native-history', MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    operand = E1CompactArrays('arrays.'+source.root_id, identity(source), 'NATIVE_HISTORY', artifact, members,
        tuple(sorted((identity(source), coordinate_identity(source.coordinate)), key=lambda x: x.object_id)),
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE)
    # Original compressed bytes stay exact even when their encoding differs.
    decode_matrix_arrays(raw, operand)
    operand.validate_source(source)
    return raw, operand




def assess_history(source, history, arrays):
    history.validate_source(source)
    validate_arrays(source, arrays)
    design = source.numerical_design
    rows = history_independent.assess_arrays(source.coordinate, arrays,
        trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance)
    controls = tuple(MatrixParameterHistoryControl(**r) for r in rows)
    result = E1CompactNumericalAssessment('numerical.'+source.root_id, identity(source), identity(history),
        identity(design), controls, all(c.disposition == 'SATISFIED' for c in controls))
    validate_numerical(source, history, result)
    return result


def validate_numerical(source, history, assessment):
    history.validate_source(source)
    n, design = source.coordinate.total_ticks, source.numerical_design
    if (type(assessment) is not E1CompactNumericalAssessment or assessment.source != identity(source)
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
    role = E1CompactFactorRootRole(source.root_id, source.root.root.independent_group_id, source.coordinate.family_id,
        identity(source), history.arrays.array_artifact, identity(history))
    raw,members,artifact,trace_parts = pure_math.measurement_values(rule,native,artifact_id=artifact_id,initial_presence=True)
    arrays = E1CompactArrays('diagnostics.'+source.root_id, identity(source), 'FACTOR_DIAGNOSTICS', artifact, members,
        tuple(sorted((identity(source), identity(history), identity(numerical)), key=lambda x: x.object_id)),
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE)
    traces = tuple(E1CompactFactorTrace(role, identity(rule), v, s, obs, moving, fixed, artifact, members)
        for v, s, obs, moving, fixed in trace_parts)
    product = E1CompactFactorProduct('factor.'+source.root_id, identity(source), identity(history), identity(numerical),
        numerical.numerical_pass, traces, arrays)
    validate_product(source, history, numerical, product)
    return raw, product


def validate_product(source, history, numerical, product):
    validate_numerical(source, history, numerical)
    rule = source.rule
    role = E1CompactFactorRootRole(source.root_id, source.root.root.independent_group_id, source.coordinate.family_id,
        identity(source), history.arrays.array_artifact, identity(history))
    product.arrays.validate_source(source)
    if (type(product) is not E1CompactFactorProduct or product.source != identity(source)
            or product.history != identity(history) or product.numerical_assessment != identity(numerical)
            or product.history_numerical_pass != numerical.numerical_pass
            or product.arrays.producers != tuple(sorted((identity(source), identity(history), identity(numerical)), key=lambda x: x.object_id))
            or tuple((t.view, t.sector) for t in product.traces) != tuple((v, s) for v in VIEWS for s in rule.sectors)):
        raise ValueError('E1 factor product thins full source/history/numerical/view/sector census')
    for trace in product.traces:
        if (trace.root != role or trace.diagnostics != product.arrays.array_artifact
                or trace.diagnostic_members != product.arrays.members):
            raise ValueError('E1 trace substitutes original native root or exact diagnostic custody')
        factor_science.validate_trace(trace, rule, initial_presence=True)


def assess_factor(source, history, numerical, product, native_raw, diagnostic_raw):
    """Literal raw-state/operator/eigenpair checks, with no eigensolve or RNG."""
    validate_product(source, history, numerical, product)
    native = consume_arrays(source, history.arrays, native_raw)
    arrays = decode_matrix_arrays(diagnostic_raw, product.arrays)
    design = source.factor_numerical_design
    controls = pure_math.factor_control_values(source.rule,design,product.traces,native,arrays)
    return E1CompactFactorAssessment('factor-assessment.'+source.root_id, identity(source), identity(product), identity(design),
        controls, all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in controls))




def read_retained(source, history, numerical, product, assessment, native_raw, diagnostic_raw, *, receipts):
    """Cold independent reproof over exact original bytes; no fresh science."""
    roles = ((history, 'history'), (numerical, 'numerical'), (product, 'measure'), (assessment, 'check'))
    parent = history.native.definition.parent_contact
    for record, role in roles:
        receipt = authenticate_published(record, receipts)
        if (receipt.task_id != 'matrix-factor-confirmation-compact.'+source.root_id+'.'+role
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




def reduce_population(manifest,sources,products,assessments,*,unavailable=()):
    """Frozen complete independent-root inference; no view or tick pooling."""
    return E1CompactPopulationResult(*_population_values(manifest, sources, products, assessments,
        unavailable=unavailable, unavailable_type=E1CompactUnavailableRoot))


def reduce_closed_population(manifest, sources, products, assessments, *, unavailable, plan, index, terminal):
    """The same inference over an authenticated closed operational census.

    A missing task remains missing. This distinct read product is never an
    issued adjudication or permission to acquire another observation.
    """
    if (type(plan) is not ExecutionPlan or type(index) is not RunRecoveryIndex
            or type(terminal) is not RunRecoveryTerminalEvent):
        raise TypeError('closed E1 reduction requires its exact current plan/index/terminal')
    if not sources:
        raise ValueError('closed E1 reduction cannot omit its selected population')
    index.validate_plan(plan)
    terminal.__post_init__()
    index_pin = ObjectIdentity.from_record(index.recovery_index_id, index)
    if (terminal.recovery_index != index_pin or terminal.run_id != index.run_id
            or terminal.operational_status not in ('FAILED', 'BLOCKED')
            or index.implementation_commit != sources[0].implementation_commit):
        raise ValueError('closed E1 reduction changes its original run, source or operational closure')
    latest = {}
    for row in terminal.attempts:
        if row.task_id not in latest or row.ordinal > latest[row.task_id].ordinal:
            latest[row.task_id] = row
    if set(latest) != {task.task_id for task in plan.tasks}:
        raise ValueError('closed E1 reduction omits part of the actual task census')
    missing = {row.source: row for row in unavailable}
    for source in sources:
        nodes = {NAMESPACE+'.'+source.root_id+'.'+phase for phase in PHASES}
        if not nodes.issubset(latest):
            raise ValueError('closed E1 reduction omits an assigned root operation')
        gaps = tuple(sorted((latest[node] for node in nodes if latest[node].disposition.value != 'SUCCEEDED'),
            key=lambda row: row.task_id))
        row = missing.get(identity(source))
        if (row is None) != (not gaps) or row is not None and row.terminal_attempts != gaps:
            raise ValueError('closed E1 reduction changes the exact unavailable root/phase census')
    values = _population_values(manifest, sources, products, assessments,
        unavailable=unavailable, unavailable_type=E1CompactClosedRoot)
    return E1CompactClosedPopulationResult(values[0]+'.closed', *values[1:], index.run_id,
        index.execution_plan, index_pin, ObjectIdentity.from_record(terminal.terminal_event_id, terminal),
        terminal.operational_status, index.implementation_commit)


def _population_values(manifest, sources, products, assessments, *, unavailable, unavailable_type):
    """One scientific reducer for completed and closed-custody populations."""
    sources = tuple(sorted(sources, key=lambda s: s.root_id))
    if not sources:
        raise ValueError('E1 population cannot omit its selected allocation')
    if type(manifest) is not E1CompactManifest or sources != sources_for_manifest(manifest):
        raise ValueError('compact E1 population substitutes exact complete manifest/root correspondence')
    first=sources[0]
    root_ids=tuple(row.root.root_id for row in manifest.reservation.allocation.roots)
    expected = {identity(s): s for s in sources}
    received = {p.source: p for p in products}
    checked = {a.source: a for a in assessments}
    missing = {u.source: u for u in unavailable}
    if (tuple(s.root_id for s in sources) != root_ids or len(received) != len(products) or len(checked) != len(assessments)
            or len(missing) != len(unavailable) or set(received) & set(missing)
            or set(received) | set(missing) != set(expected) or set(checked) != set(received)
            or any(s.manifest != first.manifest for s in sources)):
        raise ValueError('E1 population drops, duplicates or substitutes a complete selected root')
    for source_id, source in expected.items():
        if source_id in missing:
            u = missing[source_id]
            if type(u) is not unavailable_type:
                raise TypeError('E1 unavailable census requires its exact selected custody type')
            u.__post_init__()
            evidence = ((u.receipt if u.receipt is not None else u.contact)
                if unavailable_type is E1CompactUnavailableRoot else u)
            nodes = ((evidence.task_id,) if unavailable_type is E1CompactUnavailableRoot
                else tuple(row.task_id for row in u.terminal_attempts))
            if (evidence.implementation_commit != source.implementation_commit
                    or not set(nodes).issubset({f'{NAMESPACE}.{source.root_id}.{role}' for role in PHASES})):
                raise ValueError('E1 unavailable census substitutes original root operation/source receipt')
            continue
        p, a = received[source_id], checked[source_id]
        design = source.factor_numerical_design
        n = len(VIEWS)*len(source.rule.sectors)*len(source.rule.lattice)
        expected_controls = tuple(zip((n, 15*n, n, n, n, n), (225, 15, 225, 225, 48, 1),
            (design.operator_tolerance, design.eigenpair_tolerance, design.orthogonality_tolerance,
             design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance), strict=True))
        p.arrays.validate_source(source)
        if (type(p) is not E1CompactFactorProduct or type(a) is not E1CompactFactorAssessment or a.product != identity(p)
                or a.numerical_design != identity(source.factor_numerical_design)
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
            factor_science.validate_trace(trace, source.rule, initial_presence=True)
    criterion=manifest.specification.selection.criterion;rule=first.rule
    alpha=criterion.cell_alpha(rule)
    events, usable_traces = [], []
    for source in sources:
        pin = identity(source)
        product = received.get(pin)
        usable = product is not None and product.history_numerical_pass and checked[pin].numerical_pass
        disposition = missing[pin].availability if product is None else 'ASSESSED' if usable else 'NUMERICAL_UNUSABLE'
        for view in VIEWS:
            for sector in rule.sectors:
                trace = None if product is None else next(trace for trace in product.traces
                    if (trace.view, trace.sector) == (view, sector))
                events.append(root_occurrence(root_id=source.root_id, unit_id=source.root.root.independent_group_id,
                    source=pin, family_id=source.coordinate.family_id, view=view, sector=sector, rule=rule,
                    occurrence_end_tick=criterion.occurrence_end_tick, survival_duration_ticks=criterion.survival_duration_ticks,
                    observations=None if trace is None else trace.observations, numerical_usable=usable,
                    source_disposition=disposition))
                if usable:
                    usable_traces.append(trace)
    events = tuple(events)
    counts = {row.family_id: row.requested_roots for row in criterion.family_requirements}
    findings = occurrence_cells(events, family_counts=counts)
    risk_rows = _risk_rows(rule, usable_traces, counts)
    status = ScientificStatus.PARTIAL if any(event.numerical_usable for event in events) else ScientificStatus.UNEVALUABLE
    reasons = ['e1-estimation-map-no-binary-claim']
    if any(row.interval.unknown_eligibility or row.interval.known_risk_unknown_outcomes for row in findings):
        reasons.append('e1-unknowns-retained-in-completion-envelope')
    if any(row.interval.lower is None for row in findings if row.primary):
        reasons.append('e1-conditional-risk-not-established')
    if status is ScientificStatus.UNEVALUABLE:
        reasons.append('e1-no-numerically-usable-observations')
    return ('result.'+criterion.criterion_id,first.manifest,
        identity(manifest.reservation.allocation),identity(criterion),root_ids,tuple(identity(source) for source in sources),
        tuple(identity(received[identity(source)]) for source in sources if identity(source) in received),
        tuple(identity(checked[identity(source)]) for source in sources if identity(source) in checked),
        tuple(missing[identity(source)] for source in sources if identity(source) in missing),events,findings,risk_rows,
        criterion.primary_alpha.numerator,criterion.primary_alpha.denominator,alpha.numerator,alpha.denominator,status,tuple(sorted(reasons)))


def _risk_rows(rule, traces, counts):
    """Descriptive whole-root occupancy; unusable roots stay in every denominator.

    First-causal columns count observed admissions, not an inferred origin across
    unknown time. Exact first-origin knowledge is retained in the root events.
    Left-present persistence is moving survival from time zero.
    """
    rows = []
    for family, count in sorted(counts.items()):
        for view in VIEWS:
            for sector in rule.sectors:
                selected = tuple(trace for trace in traces
                    if (trace.root.family_id, trace.view, trace.sector) == (family, view, sector))
                left = tuple(trace for trace in selected if trace.observations[0].raw_admitted is True)
                for index, tick in enumerate(rule.lattice):
                    observations = tuple(trace.observations[index] for trace in selected)
                    states = tuple(tuple(factor_science._moving_state(row, rule)
                        for row in trace.observations[:index+1]) for trace in left)
                    survived = sum(all(value is True for value in state) for state in states)
                    exited = sum(any(value is False for value in state) for state in states)
                    rows.append(E1RiskRow(family, view, sector, tick, count,
                        sum(row.status == 'AVAILABLE' for row in observations),
                        sum(row.status == 'UNIDENTIFIABLE' for row in observations),
                        count - len(selected) + sum(row.status in ('UNAVAILABLE', 'NUMERICAL_INVALID') for row in observations),
                        sum(row.raw_admitted is True for row in observations),
                        sum(row.causal_admitted is True for row in observations),
                        sum(trace.moving_lifetime.origin_tick == tick for trace in selected),
                        sum(trace.moving_lifetime.origin_tick is not None and trace.moving_lifetime.origin_tick <= tick
                            for trace in selected), len(left), survived, exited, len(left) - survived - exited))
    return tuple(rows)
