# SPDX-License-Identifier: MPL-2.0
"""Complete exposed response-error frontiers; no sampling or use warrant.

The caller authenticates selections, frontiers and disposition evidence through
their original readers. This pure consumer owns no source access, native effect,
fit, authority or admission. Exact finite-roster envelopes need no IID or
missing-at-random assumption. Optional DKW formula values are conditional
mathematical sensitivity, not established population coverage or numerical
enclosures. See the source-bound report specification before interpreting them.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_stable_id,
)

from .records import PREDICTORS
from .response_contracts import MatrixResponseOriginSelection, MatrixResponsePopulationPolicy
from .response_frontier import MatrixResponseRootFrontier, root_frontier_census

STRATA = ('cc1.history.co-anneal', 'cc1.history.de-anneal',
          'cc1.history.x-first', 'cc1.history.y-first')
HORIZONS = (16, 64, 128)
ROOT_IDS = tuple(f'history.cc1-grr-c2.h{i:03d}' for i in range(256))
STANDING = 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'
WARRANT = 'UNASSESSED_NO_FIXED_MAP_IID_ASSESSMENT'
NUMERICAL_SCOPE = 'FINITE_DT_EMPIRICAL_CROSSCHECK_NOT_CERTIFIED_ERROR_ENCLOSURE'
RADIUS_SCOPE = 'APPROXIMATE_DECIMAL_DKW_FORMULA_CONDITIONAL_ON_FIXED_MAP_IID_WHOLE_ROOTS'
DISPOSITIONS = ('CROSSCHECKED_FINITE', 'MEASUREMENT_UNRESOLVED', 'NATIVE_CROSSCHECK_FAILED',
                'NOT_ENTERED', 'NO_CAUSAL_ORIGIN', 'OBSERVATION_UNRESOLVED', 'REFUSED',
                'UNAVAILABLE', 'UNKNOWN_CONTACT')


def _identity(record):
    name = record.spec_id if type(record) is MatrixResponsePopulationStatisticsSpec else record.report_id
    return ObjectIdentity.from_record(name, record)


@dataclass(frozen=True, slots=True)
class MatrixResponsePopulationStatisticsSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-population/statistics-spec'
    spec_id: str
    policy: MatrixResponsePopulationPolicy
    selections: tuple[MatrixResponseOriginSelection, ...]
    selection_artifact: ArtifactIdentity
    allocation_artifact: ArtifactIdentity
    alpha: Decimal | None = None
    endpoint: str = 'COMPLETE_SELECTED_ORIGIN_CROSSCHECKED_FINITE_DT_REPORTED_LOSS'
    missingness: str = 'TAGGED_NONUSE_AND_EXPLICIT_UNRESOLVED_INTERVALS_NO_IMPUTATION'
    sampling_warrant: str = WARRANT
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.spec_id)
        if type(self.policy) is not MatrixResponsePopulationPolicy:
            raise TypeError('response statistics require the exact typed population policy')
        require_sorted_unique_ids(self.selections, attribute='root_id', field_name='selections')
        if (self.policy.requested_root_ids != ROOT_IDS
                or tuple(s.root_id for s in self.selections) != ROOT_IDS
                or any(type(s) is not MatrixResponseOriginSelection for s in self.selections)
                or len({s.independent_group_id for s in self.selections}) != 256
                or self.policy.protocol.horizon_steps != HORIZONS
                or self.policy.protocol.primary_timestep != Decimal('0.001')
                or self.policy.protocol.panel_roles != ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                or self.endpoint != 'COMPLETE_SELECTED_ORIGIN_CROSSCHECKED_FINITE_DT_REPORTED_LOSS'
                or self.missingness != 'TAGGED_NONUSE_AND_EXPLICIT_UNRESOLVED_INTERVALS_NO_IMPUTATION'
                or self.sampling_warrant != WARRANT or self.standing != STANDING):
            raise ValueError('response statistics change complete current roster/task or invent warrant')
        for i, selection in enumerate(self.selections):
            if (selection.policy != self.policy.identity
                    or selection.family_id != STRATA[i // 64]
                    or selection.independent_group_id != f'unit.cc1-grr-c2.h{i:03d}'):
                raise ValueError('response statistics substitute original root/group/stratum/policy')
        if (type(self.selection_artifact) is not ArtifactIdentity
                or type(self.allocation_artifact) is not ArtifactIdentity
                or self.selection_artifact.size_bytes < 1 or self.allocation_artifact.size_bytes < 1):
            raise ValueError('response statistics require retained selection/allocation artifact bindings')
        if self.alpha is not None:
            validate_decimal(self.alpha, field_name='conditional reporting alpha')
            if not Decimal(0) < self.alpha < Decimal(1):
                raise ValueError('conditional reporting alpha must be strictly between zero and one')

    @property
    def identity(self):
        return _identity(self)


@dataclass(frozen=True, slots=True)
class MatrixResponseRootLossBounds(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-population/root-loss-bounds'
    bounds_id: str
    spec: ObjectIdentity
    root_id: str
    independent_group_id: str
    stratum_id: str
    predictor: str
    horizon_step: int
    disposition: str
    bound_kind: str
    lower_loss: Decimal | None
    upper_loss: Decimal | None
    frontier: ObjectIdentity | None
    evidence: tuple[ObjectIdentity, ...]
    reason_codes: tuple[str, ...]

    @property
    def key(self):
        return self.root_id, self.predictor, self.horizon_step

    def __post_init__(self):
        for name in ('bounds_id', 'root_id', 'independent_group_id', 'stratum_id'):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_ids(self.evidence, attribute='object_id', field_name='evidence')
        require_sorted_unique_strings(self.reason_codes, field_name='reason_codes', allow_empty=False)
        if (self.spec.object_schema != MatrixResponsePopulationStatisticsSpec.SCHEMA
                or self.predictor not in PREDICTORS or self.horizon_step not in HORIZONS
                or type(self.horizon_step) is not int or self.disposition not in DISPOSITIONS
                or not self.evidence):
            raise ValueError('response loss bounds lose exact endpoint/disposition/evidence')
        for value in (self.lower_loss, self.upper_loss):
            if value is not None:
                validate_decimal(value, field_name='finite loss bound', minimum=Decimal(0))
        if self.bound_kind == 'FINITE_POINT':
            valid = (self.disposition == 'CROSSCHECKED_FINITE' and self.frontier is not None
                     and self.lower_loss is not None and self.lower_loss == self.upper_loss)
        elif self.bound_kind == 'KNOWN_NONUSE_INFINITY':
            valid = (self.disposition in ('NO_CAUSAL_ORIGIN', 'REFUSED', 'NATIVE_CROSSCHECK_FAILED')
                     and self.lower_loss is None and self.upper_loss is None)
        elif self.bound_kind == 'UNRESOLVED_INTERVAL':
            valid = (self.disposition in ('MEASUREMENT_UNRESOLVED', 'NOT_ENTERED',
                     'OBSERVATION_UNRESOLVED', 'UNAVAILABLE', 'UNKNOWN_CONTACT')
                     and self.lower_loss is not None and (self.upper_loss is None
                     or self.upper_loss >= self.lower_loss))
        else:
            valid = False
        if (not valid or self.frontier is not None
                and self.frontier.object_schema != MatrixResponseRootFrontier.SCHEMA
                or self.disposition == 'NATIVE_CROSSCHECK_FAILED' and self.frontier is None):
            raise ValueError('response loss bounds confuse finite error, nonuse or unknown performance')


def _cdf_rows(bounds):
    """Integer count envelopes, with zero and every finite interval endpoint."""
    rows = []
    for stratum in STRATA:
        for predictor in PREDICTORS:
            for horizon in HORIZONS:
                selected = tuple(b for b in bounds if (b.stratum_id, b.predictor, b.horizon_step)
                                 == (stratum, predictor, horizon))
                points = sorted({Decimal(0), *(v for b in selected
                    for v in (b.lower_loss, b.upper_loss) if v is not None)})
                crossings = tuple((t,
                    sum(b.upper_loss is not None and b.upper_loss <= t for b in selected),
                    sum(b.lower_loss is not None and b.lower_loss <= t for b in selected)) for t in points)
                reasons = tuple((d, sum(b.disposition == d for b in selected)) for d in DISPOSITIONS)
                rows.append((stratum, predictor, horizon, len(selected), crossings, reasons))
    return tuple(rows)


def _conditional_radii(spec):
    if spec.alpha is None:
        return ()
    # Merely the theorem's formula evaluated in Decimal arithmetic. We do not
    # certify log/sqrt rounding as a mathematical enclosure or the assumptions.
    with localcontext() as context:
        context.prec = 50
        radius = ((Decimal(120) / spec.alpha).ln() / Decimal(128)).sqrt()
    return tuple((stratum, radius) for stratum in STRATA)


@dataclass(frozen=True, slots=True)
class MatrixResponsePopulationStatistics(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-population/statistics'
    report_id: str
    spec: MatrixResponsePopulationStatisticsSpec
    bounds: tuple[MatrixResponseRootLossBounds, ...]
    stratum_cdfs: tuple[tuple[str, str, int, int,
        tuple[tuple[Decimal, int, int], ...], tuple[tuple[str, int], ...]], ...]
    conditional_radii: tuple[tuple[str, Decimal], ...]
    sampling_warrant: str = WARRANT
    radius_scope: str = RADIUS_SCOPE
    numerical_scope: str = NUMERICAL_SCOPE
    admission: str = 'UNASSESSED'
    qualification: str = 'NOT_ESTABLISHED'
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.report_id)
        if type(self.spec) is not MatrixResponsePopulationStatisticsSpec:
            raise TypeError('response statistics require their typed immutable specification')
        expected = tuple((r, m, h) for r in ROOT_IDS for m in PREDICTORS for h in HORIZONS)
        if (tuple(b.key for b in self.bounds) != expected
                or any(type(b) is not MatrixResponseRootLossBounds for b in self.bounds)
                or self.stratum_cdfs != _cdf_rows(self.bounds)
                or self.conditional_radii != _conditional_radii(self.spec)
                or self.sampling_warrant != WARRANT or self.radius_scope != RADIUS_SCOPE
                or self.numerical_scope != NUMERICAL_SCOPE or self.admission != 'UNASSESSED'
                or self.qualification != 'NOT_ESTABLISHED' or self.standing != STANDING):
            raise ValueError('response statistics thin census, alter counts or invent coverage/qualification')
        selections = {s.root_id: s for s in self.spec.selections}
        for bound in self.bounds:
            selection = selections[bound.root_id]
            if (bound.spec != self.spec.identity
                    or bound.independent_group_id != selection.independent_group_id
                    or bound.stratum_id != selection.family_id
                    or (selection.disposition == 'NO_CAUSAL_ORIGIN') !=
                       (bound.disposition == 'NO_CAUSAL_ORIGIN')
                    or selection.disposition == 'OBSERVATION_UNRESOLVED'
                       and bound.disposition != 'OBSERVATION_UNRESOLVED'):
                raise ValueError('response statistics substitute root/origin/group/stratum lineage')
        for offset in range(0, len(self.bounds), len(HORIZONS)):
            local = self.bounds[offset:offset + len(HORIZONS)]
            for previous, later in zip(local, local[1:]):
                if ((previous.lower_loss is None and later.lower_loss is not None)
                        or previous.lower_loss is not None and later.lower_loss is not None
                        and previous.lower_loss > later.lower_loss):
                    raise ValueError('response cumulative bounds lose a prior horizon failure/lower bound')

    @property
    def identity(self):
        return _identity(self)


def root_loss_bounds(spec, selection, frontier=None, *, disposition=None,
                     evidence=(), reason_codes=()):
    """Extract one root's full menu, or retain an explicit unavailable outcome.

    Inputs must already be authenticated by their original custody readers.
    Missing evidence means UNAVAILABLE, not proof of absent native contact.
    No file, RNG, provider or scientific-effect service is invoked here.
    """
    if selection not in spec.selections:
        raise ValueError('response loss selection is outside the exact source-bound roster')
    selection_identity = ObjectIdentity.from_record(selection.selection_id, selection)
    evidence = tuple(sorted((selection_identity, *evidence), key=lambda x: x.object_id))
    frontier_id = None
    losses = {}
    if selection.disposition != 'SELECTED':
        if frontier is not None or disposition is not None:
            raise ValueError('unselected response origin cannot furnish a native frontier')
        disposition = selection.disposition
    elif frontier is not None:
        if type(frontier) is not MatrixResponseRootFrontier or disposition is not None:
            raise ValueError('response frontier cannot be replaced by a disposition label')
        frontier.__post_init__()
        root_frontier_census(spec.policy.protocol, (frontier,), requested_root_ids=(selection.root_id,))
        if (frontier.root_id != selection.root_id
                or frontier.independent_group_id != selection.independent_group_id
                or frontier.stratum_id != selection.family_id
                or frontier.disposition != 'MEASURED_DEVELOPMENT'):
            raise ValueError('response frontier substitutes selected original root/group/stratum')
        frontier_id = ObjectIdentity.from_record(frontier.frontier_id, frontier)
        evidence = tuple(sorted((*evidence, frontier_id), key=lambda x: x.object_id))
        disposition = 'CROSSCHECKED_FINITE' if frontier.native_reference_pass else 'NATIVE_CROSSCHECK_FAILED'
        losses = {(x.predictor, x.horizon_step): x.cumulative_loss for x in frontier.horizon_losses}
    else:
        disposition = 'UNAVAILABLE' if disposition is None else disposition
        if disposition not in ('NOT_ENTERED', 'REFUSED', 'UNAVAILABLE', 'UNKNOWN_CONTACT'):
            raise ValueError('missing response frontier cannot establish a native or measured outcome')
        if disposition != 'UNAVAILABLE' and len(evidence) == 1:
            raise ValueError('explicit contact/refusal/nonentry requires retained disposition evidence')
    reasons = tuple(sorted(set(reason_codes or (disposition.lower().replace('_', '-'),))))
    output = []
    for predictor in PREDICTORS:
        known_lower = Decimal(0)
        for horizon in HORIZONS:
            value = losses.get((predictor, horizon))
            selected_disposition = disposition
            if disposition in ('NO_CAUSAL_ORIGIN', 'REFUSED', 'NATIVE_CROSSCHECK_FAILED'):
                kind, lower, upper = 'KNOWN_NONUSE_INFINITY', None, None
            elif disposition == 'CROSSCHECKED_FINITE' and value is not None:
                kind, lower, upper = 'FINITE_POINT', value, value
                known_lower = value
            else:
                kind, lower, upper = 'UNRESOLVED_INTERVAL', known_lower, None
                if disposition == 'CROSSCHECKED_FINITE':
                    selected_disposition = 'MEASUREMENT_UNRESOLVED'
            output.append(MatrixResponseRootLossBounds(
                f'bounds.{selection.root_id}.{predictor.lower()}.{horizon}', spec.identity,
                selection.root_id, selection.independent_group_id, selection.family_id,
                predictor, horizon, selected_disposition, kind, lower, upper, frontier_id,
                evidence, reasons if selected_disposition == disposition else ('measurement-unresolved',)))
    return tuple(output)


def population_statistics(spec, root_bounds, *, report_id):
    """Incremental caller supplies endpoint batches, never a full raw array bank."""
    bounds = tuple(sorted((bound for batch in root_bounds for bound in batch), key=lambda b: b.key))
    return MatrixResponsePopulationStatistics(report_id, spec, bounds, _cdf_rows(bounds), _conditional_radii(spec))


def query_statistics(report, tolerance):
    """Exact count envelopes at any finite tolerance; no success gate is set."""
    validate_decimal(tolerance, field_name='requested reporting tolerance', minimum=Decimal(0))
    findings = []
    radii = dict(report.conditional_radii)
    for stratum, predictor, horizon, denominator, crossings, dispositions in report.stratum_cdfs:
        _, lower, upper = next(row for row in reversed(crossings) if row[0] <= tolerance)
        radius = radii.get(stratum)
        with localcontext() as context:
            context.prec = 50
            conditional = None if radius is None else (
                max(Decimal(0), Decimal(lower) / denominator - radius),
                min(Decimal(1), Decimal(upper) / denominator + radius))
        findings.append({'stratum_id': stratum, 'predictor': predictor, 'horizon_step': horizon,
            'requested_roots': denominator, 'empirical_lower_count': lower, 'empirical_upper_count': upper,
            'dispositions': dispositions, 'conditional_formula_band': conditional,
            'sampling_warrant': report.sampling_warrant, 'radius_scope': report.radius_scope,
            'numerical_scope': report.numerical_scope, 'admission': report.admission})
    mixtures = []
    for predictor in PREDICTORS:
        for horizon in HORIZONS:
            selected = [r for r in findings if (r['predictor'], r['horizon_step']) == (predictor, horizon)]
            with localcontext() as context:
                context.prec = 50
                band = None if not radii else tuple(sum(
                    r['conditional_formula_band'][side] for r in selected) / 4 for side in (0, 1))
            mixtures.append({'predictor': predictor, 'horizon_step': horizon, 'requested_roots': 256,
                'empirical_lower_count': sum(r['empirical_lower_count'] for r in selected),
                'empirical_upper_count': sum(r['empirical_upper_count'] for r in selected),
                'weights': tuple((s, 64, 256) for s in STRATA), 'conditional_formula_band': band,
                'sampling_warrant': report.sampling_warrant, 'radius_scope': report.radius_scope})
    comparisons = []
    for stratum, rows in (*((s, [r for r in findings if r['stratum_id'] == s]) for s in STRATA),
                          ('FIXED_EQUAL_STRATUM_MIXTURE', mixtures)):
        lookup = {(r['predictor'], r['horizon_step']): r for r in rows}
        for comparator in PREDICTORS[1:]:
            for horizon in HORIZONS:
                factor, other = lookup['FACTOR', horizon], lookup[comparator, horizon]
                with localcontext() as context:
                    context.prec = 50
                    band = None if not radii else (
                        factor['conditional_formula_band'][0] - other['conditional_formula_band'][1],
                        factor['conditional_formula_band'][1] - other['conditional_formula_band'][0])
                comparisons.append({'stratum_id': stratum, 'comparator': comparator, 'horizon_step': horizon,
                    'requested_roots': factor['requested_roots'],
                    'empirical_difference_lower_count': factor['empirical_lower_count'] - other['empirical_upper_count'],
                    'empirical_difference_upper_count': factor['empirical_upper_count'] - other['empirical_lower_count'],
                    'conditional_formula_difference_band': band, 'sampling_warrant': report.sampling_warrant,
                    'interpretation': 'DESCRIPTIVE_CDF_DIFFERENCE_NO_SUPERIORITY_OR_EQUIVALENCE_GATE'})
    return {'tolerance': tolerance, 'strata': tuple(findings), 'finite_roster_mixture': tuple(mixtures),
            'factor_comparator_cdf_differences': tuple(comparisons),
            'qualification': report.qualification, 'standing': report.standing}
