# SPDX-License-Identifier: MPL-2.0
"""Exposed whole-root error prediction, with no scientific qualification.

This PURE owner reads no files, calls no native provider, and creates no reserve
or authority. Callers authenticate the original prefix/source/clock/array joins
and the actual earlier role and physical-regime publications before real fits.
Publication identities below express those mandatory operands; checksum equality
alone does not prove their custody, prior publication or scientific assessment.

The current 256 roots remain exposed under every subrole. Mathematical split-rank
queries are conditional on exchangeable whole groups and an already fixed score.
No current wrapper, software control or confidence query promotes that warrant.
An eligible future predictor/calibration needs a separately assessed successor.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, DecimalException, localcontext
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)

from .records import PREDICTORS
from .response_population_statistics import (
    DISPOSITIONS as LABEL_DISPOSITIONS,
    HORIZONS, ROOT_IDS, STANDING, STRATA, MatrixResponsePopulationStatisticsSpec,
    MatrixResponseRootLossBounds,
)

SUBROLES = ('TRAIN', 'CALIBRATION_DESCRIPTIVE', 'EVALUATION_DESCRIPTIVE')
METHODS = ('CONTEXT', 'NORM_RADIUS', 'SPECTRAL', 'ALL_ORIGIN')
ENDPOINTS = tuple((m, h) for m in PREDICTORS for h in HORIZONS)
WARRANT = 'UNASSESSED_EXPOSED_NO_FRESH_EXCHANGEABLE_CALIBRATION'
FEATURE_BLOCKS = {
    'CONTEXT': ('alpha-x', 'alpha-y', 'bath-temperature', 'cross-gamma', 'cutoff',
                'family-de-anneal', 'family-x-first', 'family-y-first', 'friction', 'potential-m'),
    'NORM_RADIUS': ('momentum-x-norm', 'momentum-y-norm', 'position-x-norm', 'position-y-norm'),
    'SPECTRAL': ('largest-y-rate', 'slow-y-mean', 'third-fourth-y-gap'),
    'FACTOR': ('associative-leakage', 'factor-fit-angle', 'lie-leakage', 'trailing-angle'),
}
FEATURES = tuple(sorted(x for block in FEATURE_BLOCKS.values() for x in block))
FEATURE_DISPOSITIONS = ('AVAILABLE', 'NO_CAUSAL_ORIGIN', 'UNAVAILABLE', 'REFUSED', 'UNSUPPORTED')


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def _decimal(value):
    result = Decimal(str(float(value)))
    validate_decimal(result, field_name='numerical prediction value')
    return result


def _log_error(value):
    with localcontext() as ctx:
        ctx.prec = 50
        return (Decimal(1) + value).ln()


def _roles(population):
    """No RNG, numeric outcomes or origin disposition enters assignment."""
    result = []
    for stratum in STRATA:
        rows = tuple(s for s in population.selections if s.family_id == stratum)
        observed = tuple(s for s in rows if s.root_id in ROOT_IDS[:2])
        remaining = sorted((s for s in rows if s.root_id not in ROOT_IDS[:2]), key=lambda s: (
            sha256(('el.e3.exposed-whole-root-subroles.v1\0' + population.policy.fingerprint()
                    + '\0' + s.independent_group_id).encode()).hexdigest(), s.independent_group_id))
        for index, selection in enumerate((*observed, *remaining)):
            role = SUBROLES[0 if index < 32 else 1 if index < 48 else 2]
            result.append((selection.root_id, selection.independent_group_id, stratum, role,
                           selection.root_id in ROOT_IDS[:2]))
    return tuple(sorted(result))


@dataclass(frozen=True, slots=True)
class MatrixResponseDevelopmentRoles(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/development-roles'
    record_id: str
    population: ObjectIdentity
    rows: tuple[tuple[str, str, str, str, bool], ...]
    exposure: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (any(type(r) is not tuple or len(r) != 5 for r in self.rows)
                or self.population.object_schema != MatrixResponsePopulationStatisticsSpec.SCHEMA
                or tuple(r[0] for r in self.rows) != ROOT_IDS or self.exposure != STANDING
                or len({r[1] for r in self.rows}) != 256):
            raise ValueError('error roles change original256 exposed whole-root census')
        for i, row in enumerate(self.rows):
            if (len(row) != 5 or row[1] != f'unit.cc1-grr-c2.h{i:03d}' or row[2] != STRATA[i // 64]
                    or row[3] not in SUBROLES or type(row[4]) is not bool
                    or row[4] != (i < 2) or i < 2 and row[3] != 'TRAIN'):
                raise ValueError('error roles split a group or relabel observed roots as independent evaluation')
        if any(Counter(r[3] for r in self.rows if r[2] == f) !=
               Counter(dict(zip(SUBROLES, (32, 16, 16), strict=True))) for f in STRATA):
            raise ValueError('error roles lose fixed family32/16/16 denominator')


def development_roles(population, *, record_id):
    if type(population) is not MatrixResponsePopulationStatisticsSpec:
        raise TypeError('error roles need exact typed current population')
    return MatrixResponseDevelopmentRoles(record_id, population.identity, _roles(population))


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorPredictionSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/prediction-spec'
    record_id: str
    population: MatrixResponsePopulationStatisticsSpec
    roles: MatrixResponseDevelopmentRoles
    roles_publication: ArtifactIdentity
    future_regime_reservation: ObjectIdentity
    future_reservation_publication: ArtifactIdentity
    feature_window_ticks: int = 32
    feature_cadence_ticks: int = 16
    ridge_lambda: Decimal = Decimal(1)
    target: str = 'LOG1P_COMPLETE_FINITE_DT_CUMULATIVE_NORMALIZED_RESPONSE_ERROR_15'
    information: str = 'FULL_MICROSCOPIC_ORIGIN_ONLY_SMALL_FEATURE_RECORD'
    standing: str = STANDING
    sampling_warrant: str = WARRANT

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.population) is not MatrixResponsePopulationStatisticsSpec
                or type(self.roles) is not MatrixResponseDevelopmentRoles
                or self.roles.population != self.population.identity or self.roles.rows != _roles(self.population)
                or self.population.alpha is not None
                or self.feature_window_ticks != 32 or self.feature_cadence_ticks != 16
                or type(self.feature_window_ticks) is not int or type(self.feature_cadence_ticks) is not int
                or self.ridge_lambda != Decimal(1)
                or self.target != 'LOG1P_COMPLETE_FINITE_DT_CUMULATIVE_NORMALIZED_RESPONSE_ERROR_15'
                or self.information != 'FULL_MICROSCOPIC_ORIGIN_ONLY_SMALL_FEATURE_RECORD'
                or self.standing != STANDING or self.sampling_warrant != WARRANT):
            raise ValueError('error prediction substitutes frozen roles/criterion/features or invents warrant')
        for publication, record in ((self.roles_publication, identity(self.roles)),
                                    (self.future_reservation_publication, self.future_regime_reservation)):
            if (type(publication) is not ArtifactIdentity or publication.size_bytes < 1
                    or publication.payload_schema != record.object_schema
                    or publication.sha256 != record.object_fingerprint):
                raise ValueError('error fit requires exact prior role/regime publication bindings')

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixResponseOriginFeatures(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/origin-features'
    record_id: str
    spec: ObjectIdentity
    root_id: str
    independent_group_id: str
    stratum_id: str
    selection: ObjectIdentity
    source: ObjectIdentity | None
    origin: ObjectIdentity | None
    clock_id: str | None
    cutoff: Decimal | None
    frame_sha256: str | None
    disposition: str
    values: tuple[tuple[str, Decimal], ...]
    evidence: tuple[ObjectIdentity, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        for name in ('record_id', 'root_id', 'independent_group_id', 'stratum_id'):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_strings(self.reason_codes, field_name='feature reasons', allow_empty=False)
        if (self.spec.object_schema != MatrixResponseErrorPredictionSpec.SCHEMA
                or self.disposition not in FEATURE_DISPOSITIONS or not self.evidence
                or tuple(e.object_id for e in self.evidence) != tuple(sorted({e.object_id for e in self.evidence}))):
            raise ValueError('origin features lose source/cutoff/disposition evidence')
        if self.disposition == 'AVAILABLE':
            if (tuple(k for k, _ in self.values) != FEATURES or self.source is None or self.origin is None
                    or self.clock_id is None or self.cutoff is None or self.frame_sha256 is None):
                raise ValueError('available origin features require every frozen channel and clock/frame')
            validate_stable_id(self.clock_id)
            validate_sha256(self.frame_sha256)
        elif self.values:
            raise ValueError('refused/unavailable origin cannot manufacture feature values')
        if self.cutoff is not None:
            validate_decimal(self.cutoff, field_name='feature cutoff', minimum=Decimal(0))
        for _, value in self.values:
            validate_decimal(value, field_name='origin feature', minimum=Decimal(0))
            if not np.isfinite(float(value)):
                raise ValueError('origin feature has no finite binary64 estimator representation')


def _selection(spec, root_id):
    row = next((s for s in spec.population.selections if s.root_id == root_id), None)
    if row is None:
        raise ValueError('error consumer root outside complete scientific population')
    return row


def _validate_feature(spec, feature):
    if type(feature) is not MatrixResponseOriginFeatures or feature.spec != spec.identity:
        raise ValueError('error feature substitutes frozen specification')
    selected = _selection(spec, feature.root_id)
    if (feature.selection != ObjectIdentity.from_record(selected.selection_id, selected)
            or feature.independent_group_id != selected.independent_group_id or feature.stratum_id != selected.family_id
            or feature.cutoff != selected.cutoff
            or (selected.disposition == 'NO_CAUSAL_ORIGIN') != (feature.disposition == 'NO_CAUSAL_ORIGIN')
            or selected.disposition != 'SELECTED' and feature.disposition == 'AVAILABLE'):
        raise ValueError('error feature changes original group/family/causal selection/cutoff')
    if feature.disposition == 'AVAILABLE':
        values = dict(feature.values)
        expected_family = {'family-' + f.rsplit('.', 1)[1]: Decimal(selected.family_id == f)
                           for f in STRATA[1:]}
        if (values['cutoff'] != selected.cutoff
                or any(values[name] != value for name, value in expected_family.items())):
            raise ValueError('error features substitute the actual cutoff or preparation family')


def origin_features(spec, selection, *, record_id, evidence, source=None, origin=None,
                    clock_id=None, frame_sha256=None, context=None, state=None,
                    spectrum=None, observations=(), unavailable_reason=None):
    """Reduce supplied origin measurements only; no source/array acquisition.

    The trusted caller authenticates the actual cutoff state, saved spectrum,
    trace publication and causal prefix; these arrays are not forecast ports.
    Extra postcutoff observations never enter a value or its feature identity.
    A missing trailing window is refused instead of imputed.
    """
    if _selection(spec, selection.root_id) != selection:
        raise ValueError('feature extractor substitutes actual causal selection')
    values = ()
    if selection.disposition == 'NO_CAUSAL_ORIGIN':
        disposition, reason = 'NO_CAUSAL_ORIGIN', 'original-no-causal-origin'
    elif selection.disposition != 'SELECTED' or unavailable_reason is not None:
        disposition, reason = 'UNAVAILABLE', unavailable_reason or 'origin-selection-unresolved'
    else:
        try:
            if (not isinstance(state, np.ndarray) or state.shape != (2, 2, 3, 4, 4)
                    or state.dtype != np.dtype('complex128') or not np.isfinite(state).all()
                    or not np.allclose(state, state.swapaxes(-1, -2).conj(), rtol=0, atol=1e-12)):
                raise ValueError('invalid supplied origin state')
            if (not isinstance(spectrum, tuple) or len(spectrum) != 15
                    or any(type(x) is not Decimal or not x.is_finite() or x < 0 for x in spectrum)
                    or spectrum != tuple(sorted(spectrum))):
                raise ValueError('invalid saved origin spectrum')
            tick = selection.origin_tick
            wanted = tuple(range(max(0, tick - spec.feature_window_ticks), tick + 1, spec.feature_cadence_ticks))
            past = tuple(o for o in observations if o.tick in wanted)
            if (tuple(o.tick for o in past) != wanted or any(o.status != 'AVAILABLE'
                    or o.identifiable is not True or o.alignment_ambiguous for o in past)):
                raise ValueError('missing/ambiguous trailing prefix')
            last = past[-1]
            required = (last.associative_leakage, last.lie_leakage,
                        last.factor_fit_angle_degrees)
            # Each angle ends at its observation. The first observation's
            # angle starts before this window; a restarted track may omit it.
            # The exact cadence check above establishes both endpoints for
            # every interval represented by the remaining observations.
            angles = tuple(o.adjacent_angle_degrees for o in past[1:])
            if (any(type(v) is not Decimal or not v.is_finite() or v < 0
                    for v in (*required, *angles)) or not angles):
                raise ValueError('missing required causal factor diagnostic')
            ctx = {name: context[name] for name in ('alpha-x', 'alpha-y', 'bath-temperature',
                   'cross-gamma', 'friction', 'potential-m')}
            if any(type(v) is not Decimal or not v.is_finite() or v < 0 for v in ctx.values()):
                raise ValueError('invalid actual physical context')
            ctx.update({'cutoff': selection.cutoff,
                **{'family-' + f.rsplit('.', 1)[1]: Decimal(selection.family_id == f) for f in STRATA[1:]},
                'slow-y-mean': sum(spectrum[:3]) / 3, 'largest-y-rate': spectrum[-1],
                'third-fourth-y-gap': spectrum[3] - spectrum[2],
                'associative-leakage': last.associative_leakage, 'lie-leakage': last.lie_leakage,
                'factor-fit-angle': last.factor_fit_angle_degrees,
                'trailing-angle': max(angles)})
            for component, label in enumerate(('position', 'momentum')):
                for sector, name in enumerate(('x', 'y')):
                    ctx[label + '-' + name + '-norm'] = _log_error(_decimal(np.linalg.norm(state[component, sector])))
            values = tuple(sorted(ctx.items()))
            if any(not np.isfinite(float(v)) for _, v in values):
                raise ValueError('supplied origin feature has no finite estimator representation')
            disposition, reason = 'AVAILABLE', 'authenticated-supplied-origin-measurements'
        except (ValueError, TypeError, KeyError, AttributeError):
            disposition, reason = 'REFUSED', 'required-origin-channel-missing-or-invalid'
    result = MatrixResponseOriginFeatures(record_id, spec.identity, selection.root_id,
        selection.independent_group_id, selection.family_id,
        ObjectIdentity.from_record(selection.selection_id, selection), source, origin, clock_id,
        selection.cutoff, frame_sha256, disposition, values, tuple(sorted(evidence, key=lambda e: e.object_id)), (reason,))
    _validate_feature(spec, result)
    return result


def _role_roots(spec, role):
    return tuple(r[0] for r in spec.roles.rows if r[3] == role)


def _features(spec, values, roots):
    indexed = {f.root_id: f for f in values}
    if len(indexed) != len(values) or tuple(sorted(indexed)) != roots:
        raise ValueError('error feature input thins/duplicates or crosses whole-root roles')
    for value in values:
        _validate_feature(spec, value)
    return indexed


def _labels(spec, values, roots):
    expected = tuple((r, m, h) for r in roots for m, h in ENDPOINTS)
    if (any(type(v) is not MatrixResponseRootLossBounds for v in values)
            or tuple(v.key for v in values) != expected):
        raise ValueError('error label input thins/duplicates or crosses whole-root roles/endpoints')
    for value in values:
        selected = _selection(spec, value.root_id)
        if (value.spec != spec.population.identity or value.independent_group_id != selected.independent_group_id
                or value.stratum_id != selected.family_id
                or selected.disposition == 'NO_CAUSAL_ORIGIN' and value.disposition != 'NO_CAUSAL_ORIGIN'):
            raise ValueError('error labels substitute criterion/group/stratum or hide original nonuse')
    indexed = {v.key: v for v in values}
    for root in roots:
        frontiers = {indexed[root, m, h].frontier for m, h in ENDPOINTS
                     if indexed[root, m, h].frontier is not None}
        if len(frontiers) > 1:
            raise ValueError('error label root mixes independently supplied response frontiers')
        for m in PREDICTORS:
            lower, unbounded_nonuse = Decimal(0), False
            for h in HORIZONS:
                value = indexed[root, m, h]
                if unbounded_nonuse and value.bound_kind != 'KNOWN_NONUSE_INFINITY':
                    raise ValueError('cumulative error replaces known nonuse with a finite/unknown label')
                if value.lower_loss is not None and value.lower_loss < lower:
                    raise ValueError('cumulative error label decreases across declared horizons')
                lower = lower if value.lower_loss is None else value.lower_loss
                unbounded_nonuse = value.bound_kind == 'KNOWN_NONUSE_INFINITY'
    return indexed


def _mask(method):
    if method not in METHODS:
        raise ValueError('error method outside four fixed feature masks')
    blocks = ('CONTEXT',) if method == 'CONTEXT' else ('CONTEXT', method) if method != 'ALL_ORIGIN' else tuple(FEATURE_BLOCKS)
    return tuple(sorted(k for b in blocks for k in FEATURE_BLOCKS[b]))


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/model'
    record_id: str
    spec: ObjectIdentity
    roles: ObjectIdentity
    reservation: ObjectIdentity
    method: str
    feature_names: tuple[str, ...]
    means: tuple[Decimal, ...]
    scales: tuple[Decimal, ...]
    zero_variance_mask: tuple[bool, ...]
    coefficients: tuple[tuple[Decimal, ...] | None, ...]
    training_root_ids: tuple[str, ...]
    training_features: tuple[ObjectIdentity, ...]
    training_label_sha256: str
    endpoint_finite_group_counts: tuple[int, ...]
    endpoint_family_group_counts: tuple[tuple[int, ...], ...]
    endpoint_omissions: tuple[tuple[str, str, int, str], ...]
    algorithm: str = 'TRAIN_STANDARDISED_FAMILY_MEAN_OR_RIDGE_FIXED_LAMBDA1_V1'
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.training_label_sha256)
        require_sorted_unique_strings(self.training_root_ids, field_name='training roots', allow_empty=False)
        if (self.spec.object_schema != MatrixResponseErrorPredictionSpec.SCHEMA
                or self.feature_names != _mask(self.method) or len(self.means) != len(self.feature_names)
                or len(self.scales) != len(self.means) or len(self.coefficients) != 15
                or len(self.zero_variance_mask) != len(self.means)
                or any(type(v) is not bool for v in self.zero_variance_mask)
                or len(self.endpoint_finite_group_counts) != 15
                or len(self.endpoint_family_group_counts) != 15
                or len(self.training_features) != len(self.training_root_ids)
                or self.algorithm != 'TRAIN_STANDARDISED_FAMILY_MEAN_OR_RIDGE_FIXED_LAMBDA1_V1'
                or self.standing != STANDING):
            raise ValueError('error model changes fixed algorithm/task/training census')
        for value in (*self.means, *self.scales, *(x for c in self.coefficients if c is not None for x in c)):
            validate_decimal(value, field_name='fitted numerical payload')
        if (any(s <= 0 for s in self.scales) or any(c is not None and len(c) != len(self.means) + 1 for c in self.coefficients)
                or any(z and s != Decimal(1) for z, s in zip(self.zero_variance_mask, self.scales, strict=True))
                or any(type(n) is not int or n < 0 or n > len(self.training_root_ids) for n in self.endpoint_finite_group_counts)
                or any(len(row) != 4 or any(type(n) is not int or n < 0 for n in row)
                       or sum(row) != total for row, total in
                       zip(self.endpoint_family_group_counts, self.endpoint_finite_group_counts, strict=True))
                or any((c is None) != (n == 0) for c, n in zip(self.coefficients, self.endpoint_finite_group_counts, strict=True))):
            raise ValueError('error model loses finite payload or unavailable-target denominator')
        omission_keys = tuple(row[:3] for row in self.endpoint_omissions)
        if (self.endpoint_omissions != tuple(sorted(self.endpoint_omissions))
                or len(set(omission_keys)) != len(omission_keys)
                or any(root not in self.training_root_ids or (m, h) not in ENDPOINTS
                       or reason not in (*FEATURE_DISPOSITIONS, *LABEL_DISPOSITIONS)
                       for root, m, h, reason in self.endpoint_omissions)
                or any(sum((row[1], row[2]) == endpoint for row in self.endpoint_omissions)
                       != len(self.training_root_ids) - count for endpoint, count in
                       zip(ENDPOINTS, self.endpoint_finite_group_counts, strict=True))):
            raise ValueError('error model thins its exact omitted-root endpoint mask')


def _validate_model(spec, model):
    if (type(model) is not MatrixResponseErrorModel or model.spec != spec.identity
            or model.roles != identity(spec.roles) or model.reservation != spec.future_regime_reservation
            or model.training_root_ids != _role_roots(spec, 'TRAIN')):
        raise ValueError('error model changes whole-root role/criterion/reservation join')


def fit_error_model(spec, features, labels, *, method, record_id):
    """Fit supplied TRAIN-only exposed operands after caller custody admission."""
    roots = _role_roots(spec, 'TRAIN')
    fs, ys = _features(spec, features, roots), _labels(spec, labels, roots)
    names = _mask(method)
    available = tuple(r for r in roots if fs[r].disposition == 'AVAILABLE')
    x = np.asarray([[float(dict(fs[r].values)[n]) for n in names] for r in available], dtype=float).reshape(-1, len(names))
    means = x.mean(axis=0) if len(x) else np.zeros(len(names))
    scales = x.std(axis=0) if len(x) else np.ones(len(names))
    constant = np.ones(len(names), dtype=bool)
    if len(x):
        # Literal constant columns stay centred zero even when the floating
        # mean of repeated values has a rounding residual.
        constant = np.ptp(x, axis=0) == 0
        means[constant] = x[0, constant]
        scales[constant] = 1
    scales[scales == 0] = 1
    if not np.isfinite(means).all() or not np.isfinite(scales).all():
        raise ValueError('training feature standardisation is numerically unrepresentable')
    x = np.column_stack((np.ones(len(x)), (x - means) / scales))
    coefficients, counts, family_counts, omitted = [], [], [], []
    for m, h in ENDPOINTS:
        used = tuple(i for i, r in enumerate(available) if ys[r, m, h].bound_kind == 'FINITE_POINT')
        counts.append(len(used))
        family_counts.append(tuple(sum(fs[available[i]].stratum_id == f for i in used) for f in STRATA))
        included = {available[i] for i in used}
        omitted.extend((r, m, h, ys[r, m, h].disposition if fs[r].disposition == 'AVAILABLE' else fs[r].disposition)
                       for r in roots if r not in included)
        if used:
            design = x[list(used)]
            target = np.asarray([float(_log_error(ys[available[i], m, h].lower_loss)) for i in used])
            if method == 'CONTEXT':
                # Literal family means, with no ridge shrinkage or continuous
                # context regression. Empty family cells refuse at forecast.
                family_means = tuple(float(np.mean([target[j] for j, i in enumerate(used)
                    if fs[available[i]].stratum_id == f])) if count else 0.
                    for f, count in zip(STRATA, family_counts[-1], strict=True))
                coefficient = np.zeros(len(names) + 1)
                coefficient[0] = family_means[0]
                for f, value in zip(STRATA[1:], family_means[1:], strict=True):
                    j = names.index('family-' + f.rsplit('.', 1)[1])
                    delta = value - family_means[0]
                    coefficient[j + 1] = delta * scales[j]
                    coefficient[0] += delta * means[j]
            else:
                penalty = np.eye(len(names) + 1) * float(spec.ridge_lambda)
                penalty[0, 0] = 0
                coefficient = np.linalg.solve(design.T @ design + penalty, design.T @ target)
            coefficients.append(tuple(_decimal(v) for v in coefficient))
        else:
            coefficients.append(None)
    return MatrixResponseErrorModel(record_id, spec.identity, identity(spec.roles), spec.future_regime_reservation,
        method, names, tuple(_decimal(v) for v in means), tuple(_decimal(v) for v in scales),
        tuple(bool(v) for v in constant), tuple(coefficients),
        roots, tuple(identity(fs[r]) for r in roots), sha256(canonical_json_bytes(tuple(labels))).hexdigest(),
        tuple(counts), tuple(family_counts), tuple(sorted(omitted)))


def fit_scheduled_error_model(spec, reservation, *, allocation_port, reservation_port,
        roles_port, load_training_inputs, method, record_id):
    """Authenticate the scheduled future reserve before loading or fitting data.

    The numerical fitting algorithm and exposed training census are unchanged.
    Original publication ports come from the caller's authenticated custody;
    this entry grants no source eligibility, scientific issue or authority.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import require_reserved_fit_input
    require_reserved_fit_input(spec, reservation, allocation_port=allocation_port,
        reservation_port=reservation_port, roles_port=roles_port)
    if not callable(load_training_inputs):
        raise ValueError('scheduled fit requires an explicit post-reservation training loader')
    features, labels = load_training_inputs()
    return fit_error_model(spec, features, labels, method=method, record_id=record_id)


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/calibration'
    record_id: str
    spec: ObjectIdentity
    roles: ObjectIdentity
    reservation: ObjectIdentity
    model: ObjectIdentity
    root_ids: tuple[str, ...]
    feature_identities: tuple[ObjectIdentity, ...]
    label_sha256: str
    scores: tuple[tuple[str, str, Decimal | None, tuple[str, ...]], ...]
    alpha: Decimal | None = None
    sampling_warrant: str = WARRANT
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.label_sha256)
        require_sorted_unique_strings(self.root_ids, field_name='calibration roots', allow_empty=False)
        if (self.spec.object_schema != MatrixResponseErrorPredictionSpec.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or len(self.root_ids) != len(self.feature_identities) or len(self.scores) != len(self.root_ids)
                or tuple(s[0] for s in self.scores) != tuple(sorted({s[0] for s in self.scores}))
                or self.sampling_warrant != WARRANT or self.standing != STANDING):
            raise ValueError('error calibration changes whole-group score census or invents warrant')
        for _, family, value, reasons in self.scores:
            if family not in STRATA or not reasons:
                raise ValueError('calibration score lacks family/negative or uncertainty reason')
            if value is not None:
                validate_decimal(value, field_name='one-sided root score', minimum=Decimal(0))
        if self.alpha is not None:
            _alpha(self.alpha)


def _alpha(value):
    validate_decimal(value, field_name='conditional software rank-query alpha')
    if not Decimal(0) < value < Decimal(1):
        raise ValueError('conditional rank-query alpha must be strictly between0and1')


def rank_radius(calibration, stratum_id, alpha):
    """Conditional software formula only, not a nominated confidence level."""
    _alpha(alpha)
    if stratum_id not in STRATA:
        raise ValueError('rank query outside frozen calibration stratum')
    scores = tuple(s[2] for s in calibration.scores if s[1] == stratum_id)
    n = len(scores)
    # Decimal arithmetic uses the ambient precision. A rounded rank at the
    # boundary can replace the required infinite radius with a finite one.
    numerator, denominator = alpha.as_integer_ratio()
    rank_numerator = (n + 1) * (denominator - numerator)
    k = (rank_numerator + denominator - 1) // denominator
    ordered = tuple(sorted((s for s in scores if s is not None))) + (None,) * sum(s is None for s in scores)
    return n, k, None if k > n else ordered[k - 1]


def _validate_calibration(spec, model, calibration):
    roots = _role_roots(spec, 'CALIBRATION_DESCRIPTIVE')
    selections = {r.root_id: r for r in spec.population.selections}
    if (type(calibration) is not MatrixResponseErrorCalibration or calibration.spec != spec.identity
            or calibration.roles != identity(spec.roles) or calibration.reservation != spec.future_regime_reservation
            or calibration.model != identity(model) or calibration.root_ids != roots
            or tuple((s[0], s[1]) for s in calibration.scores) !=
               tuple((selections[r].independent_group_id, selections[r].family_id) for r in roots)):
        raise ValueError('calibration substitutes model/roles/criterion/reserve/whole-group stratum')


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/forecast'
    record_id: str
    spec: ObjectIdentity
    model: ObjectIdentity
    feature: ObjectIdentity
    calibration: ObjectIdentity | None
    root_id: str
    independent_group_id: str
    stratum_id: str
    disposition: str
    raw_log_error_points: tuple[Decimal | None, ...]
    log_error_points: tuple[Decimal | None, ...]
    log_error_uppers: tuple[Decimal | None, ...]
    sampling_warrant: str = WARRANT
    standing: str = STANDING
    prediction_transform: str = 'CLIP_ZERO_THEN_MODELWISE_CUMULATIVE_MAX_NO_MISSING_IMPUTATION'

    def __post_init__(self):
        for name in ('record_id', 'root_id', 'independent_group_id', 'stratum_id'):
            validate_stable_id(getattr(self, name))
        if (self.spec.object_schema != MatrixResponseErrorPredictionSpec.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or self.feature.object_schema != MatrixResponseOriginFeatures.SCHEMA
                or len(self.raw_log_error_points) != 15 or len(self.log_error_points) != 15 or len(self.log_error_uppers) != 15
                or self.disposition not in (*FEATURE_DISPOSITIONS, 'PARTIAL_MODEL', 'NO_FINITE_MODEL')
                or self.sampling_warrant != WARRANT or self.standing != STANDING
                or self.prediction_transform != 'CLIP_ZERO_THEN_MODELWISE_CUMULATIVE_MAX_NO_MISSING_IMPUTATION'):
            raise ValueError('error forecast changes complete target/information/warrant')
        for value in self.raw_log_error_points:
            if value is not None:
                validate_decimal(value, field_name='raw pre-clipping numerical prediction')
        for point, upper in zip(self.log_error_points, self.log_error_uppers, strict=True):
            for value in (point, upper):
                if value is not None:
                    validate_decimal(value, field_name='forecast transformed loss', minimum=Decimal(0))
            if upper is not None and (point is None or upper < point or self.calibration is None):
                raise ValueError('forecast manufactures a finite uncalibrated bound')
        if self.disposition in FEATURE_DISPOSITIONS[1:] and any(x is not None for x in
                (*self.raw_log_error_points, *self.log_error_points, *self.log_error_uppers)):
            raise ValueError('refused/no-origin forecast cannot manufacture a point/bound')
        for values in (self.log_error_points, self.log_error_uppers):
            for start in range(0, 15, 3):
                prior, missing = Decimal(0), False
                for value in values[start:start + 3]:
                    if value is None:
                        missing = True
                    elif missing or value < prior:
                        raise ValueError('cumulative error forecast reverses or imputes an unresolved horizon')
                    else:
                        prior = value
        expected = []
        for start in range(0, 15, 3):
            prior, missing = Decimal(0), False
            for raw in self.raw_log_error_points[start:start + 3]:
                missing = missing or raw is None
                if missing:
                    expected.append(None)
                else:
                    prior = max(prior, raw)
                    expected.append(prior)
        if self.log_error_points != tuple(expected):
            raise ValueError('forecast changes the frozen raw-to-cumulative prediction transform')
        count = sum(value is not None for value in self.log_error_points)
        if (self.disposition == 'AVAILABLE' and count != 15
                or self.disposition == 'PARTIAL_MODEL' and not 0 < count < 15
                or self.disposition == 'NO_FINITE_MODEL' and count != 0):
            raise ValueError('forecast disposition hides unavailable cumulative targets')


def forecast_error(spec, model, feature, *, record_id, calibration=None):
    """Only small causal features and immutable model/calibration reach here."""
    _validate_model(spec, model)
    _validate_feature(spec, feature)
    if calibration is not None:
        _validate_calibration(spec, model, calibration)
    raw, points, uppers = [None] * 15, [None] * 15, [None] * 15
    disposition = feature.disposition
    if feature.disposition == 'AVAILABLE':
        values = dict(feature.values)
        x = np.asarray([1., *(0. if z else (float(values[n]) - float(a)) / float(s)
            for n, a, s, z in zip(model.feature_names, model.means, model.scales,
                                 model.zero_variance_mask, strict=True))])
        for j, coefficient in enumerate(model.coefficients):
            supported_family = (model.method != 'CONTEXT'
                or model.endpoint_family_group_counts[j][STRATA.index(feature.stratum_id)] > 0)
            if coefficient is not None and supported_family:
                value = float(np.dot(x, np.asarray(tuple(map(float, coefficient)))))
                if np.isfinite(value):
                    raw[j] = _decimal(value)
                    points[j] = max(Decimal(0), raw[j])
        for start in range(0, 15, 3):
            previous = Decimal(0)
            unresolved = False
            for j in range(start, start + 3):
                unresolved = unresolved or points[j] is None
                if unresolved:
                    points[j] = None
                else:
                    previous = points[j] = max(previous, points[j])
        disposition = 'AVAILABLE' if all(p is not None for p in points) else 'PARTIAL_MODEL' if any(p is not None for p in points) else 'NO_FINITE_MODEL'
        if calibration is not None and calibration.alpha is not None:
            radius = rank_radius(calibration, feature.stratum_id, calibration.alpha)[2]
            if radius is not None:
                uppers = [None if p is None else p + radius for p in points]
    return MatrixResponseErrorForecast(record_id, spec.identity, identity(model), identity(feature),
        None if calibration is None else identity(calibration), feature.root_id, feature.independent_group_id,
        feature.stratum_id, disposition, tuple(raw), tuple(points), tuple(uppers))


def forecast_error_points(forecast):
    """Original-unit approximate point errors, without a numerical enclosure.

    The transformed points remain the primary stored operands. Decimal50
    exp-minus-one conversion explicitly refuses arithmetic overflow; missing
    points remain absent instead of becoming zero error.
    """
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            return tuple(None if value is None else value.exp() - 1
                         for value in forecast.log_error_points)
    except DecimalException as exc:
        raise ValueError('original-unit error conversion is numerically unrepresentable') from exc


def calibrate_error_model(spec, model, features, labels, *, record_id, alpha=None):
    """Every assigned calibration root/endpoint remains, including unknown∞."""
    _validate_model(spec, model)
    roots = _role_roots(spec, 'CALIBRATION_DESCRIPTIVE')
    fs, ys = _features(spec, features, roots), _labels(spec, labels, roots)
    scores = []
    for root in roots:
        prediction = forecast_error(spec, model, fs[root], record_id='score.' + root)
        reasons, residuals = [], []
        for j, (m, h) in enumerate(ENDPOINTS):
            label = ys[root, m, h]
            point = prediction.log_error_points[j]
            if label.upper_loss is None or point is None:
                reasons.append(label.disposition if label.upper_loss is None else prediction.disposition)
            else:
                residuals.append(max(Decimal(0), _log_error(label.upper_loss) - point))
        value = None if reasons else max(residuals)
        scores.append((fs[root].independent_group_id, fs[root].stratum_id, value,
                       tuple(sorted(set(reasons))) if reasons else ('finite-complete-one-sided-group-max15',)))
    result = MatrixResponseErrorCalibration(record_id, spec.identity, identity(spec.roles), spec.future_regime_reservation,
        identity(model), roots, tuple(identity(fs[r]) for r in roots), sha256(canonical_json_bytes(tuple(labels))).hexdigest(),
        tuple(scores), alpha)
    _validate_calibration(spec, model, result)
    return result


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/readout'
    record_id: str
    spec: ObjectIdentity
    model: ObjectIdentity
    forecasts: tuple[ObjectIdentity, ...]
    label_sha256: str
    cells: tuple[tuple[str, str, int, str, str, str, Decimal | None, str, bool], ...]
    sampling_warrant: str = WARRANT
    standing: str = STANDING
    qualification: str = 'NOT_ESTABLISHED'
    usefulness: str = 'UNASSESSED_NO_CONSUMER_TOLERANCE_OR_INDEPENDENT_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.label_sha256)
        if (self.spec.object_schema != MatrixResponseErrorPredictionSpec.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or tuple(c[:3] for c in self.cells) != tuple((r, m, h) for r in ROOT_IDS for m, h in ENDPOINTS)
                or len(self.forecasts) > 256 or self.sampling_warrant != WARRANT or self.standing != STANDING
                or self.qualification != 'NOT_ESTABLISHED'
                or self.usefulness != 'UNASSESSED_NO_CONSUMER_TOLERANCE_OR_INDEPENDENT_ADMISSION'):
            raise ValueError('error readout loses complete3840 denominator or invents useful qualification')
        for cell in self.cells:
            if cell[3] not in SUBROLES or cell[7] not in ('FINITE_COVERED', 'FINITE_MISSED', 'UNKNOWN', 'UNBOUNDED', 'NONUSE') or type(cell[8]) is not bool:
                raise ValueError('error readout changes role/coverage or finite-bound semantics')
            if cell[6] is not None:
                validate_decimal(cell[6], field_name='finite-label absolute transformed prediction error', minimum=Decimal(0))


def error_readout(spec, model, forecasts, labels, *, record_id):
    _validate_model(spec, model)
    ys = _labels(spec, labels, ROOT_IDS)
    predicted = {p.root_id: p for p in forecasts}
    if len(predicted) != len(forecasts):
        raise ValueError('error readout duplicates forecast roots')
    for root, forecast in predicted.items():
        selected = _selection(spec, root)
        if (type(forecast) is not MatrixResponseErrorForecast or forecast.spec != spec.identity
                or forecast.model != identity(model) or forecast.independent_group_id != selected.independent_group_id
                or forecast.stratum_id != selected.family_id
                or selected.disposition == 'NO_CAUSAL_ORIGIN' and forecast.disposition != 'NO_CAUSAL_ORIGIN'):
            raise ValueError('error readout substitutes model/criterion/group/stratum/forecast')
    roles = {r[0]: r[3] for r in spec.roles.rows}
    cells = []
    for root in ROOT_IDS:
        forecast = predicted.get(root)
        for j, (m, h) in enumerate(ENDPOINTS):
            label = ys[root, m, h]
            point = None if forecast is None else forecast.log_error_points[j]
            upper = None if forecast is None else forecast.log_error_uppers[j]
            error = None if point is None or label.bound_kind != 'FINITE_POINT' else abs(point - _log_error(label.lower_loss))
            coverage = ('NONUSE' if label.bound_kind == 'KNOWN_NONUSE_INFINITY' else 'UNBOUNDED' if upper is None
                else 'UNKNOWN' if label.upper_loss is None else 'FINITE_COVERED' if _log_error(label.upper_loss) <= upper
                else 'FINITE_MISSED' if _log_error(label.lower_loss) > upper else 'UNKNOWN')
            cells.append((root, m, h, roles[root], label.disposition,
                          'FORECAST_MISSING' if forecast is None else forecast.disposition, error, coverage, upper is not None))
    return MatrixResponseErrorReadout(record_id, spec.identity, identity(model),
        tuple(identity(predicted[r]) for r in sorted(predicted)), sha256(canonical_json_bytes(tuple(labels))).hexdigest(), tuple(cells))


def readout_census(readout):
    """Full denominators and finite accuracy are different measurements."""
    roots = root_error_summaries(readout)
    return {'requested_roots': 256, 'requested_endpoints': len(readout.cells),
        'subroles': tuple((role, sum(c[3] == role for c in readout.cells) // 15) for role in SUBROLES),
        'forecast_dispositions': tuple(sorted(Counter(c[5] for c in readout.cells).items())),
        'label_dispositions': tuple(sorted(Counter(c[4] for c in readout.cells).items())),
        'coverage_dispositions': tuple(sorted(Counter(c[7] for c in readout.cells).items())),
        'finite_accuracy_endpoints': sum(c[6] is not None for c in readout.cells),
        'finite_bound_endpoints': sum(c[8] for c in readout.cells),
        'complete_accuracy_roots': sum(r[2] == 15 for r in roots),
        'partial_accuracy_roots': sum(0 < r[2] < 15 for r in roots),
        'complete_bound_roots': sum(r[5] == 15 for r in roots),
        'accuracy_roots_by_subrole': tuple((role, sum(r[1] == role and r[2] == 15 for r in roots),
                sum(r[1] == role for r in roots)) for role in SUBROLES),
        'admitted_use_endpoints': 0, 'consumer_tolerance': None,
        'sampling_warrant': readout.sampling_warrant, 'qualification': readout.qualification}


def root_error_summaries(readout):
    """Whole-root accuracy/coverage, with complete and partial maxima separate.

    Rows contain root, role, finite accuracy count, finite-subset maximum,
    complete-max15 (absent unless every endpoint is finite), finite-bound
    count, and all coverage dispositions. These descriptive summaries do not
    declare independent rows, impute unknowns or admit scientific use.
    """
    rows = []
    for index, root in enumerate(ROOT_IDS):
        cells = readout.cells[index * 15:(index + 1) * 15]
        errors = tuple(c[6] for c in cells if c[6] is not None)
        partial = max(errors) if errors else None
        rows.append((root, cells[0][3], len(errors), partial,
                     partial if len(errors) == 15 else None,
                     sum(c[8] for c in cells),
                     tuple(sorted(Counter(c[7] for c in cells).items()))))
    return tuple(rows)


def query_forecast_tolerance(forecast, tolerance):
    """Requested continuous frontier only, no success/admission or lifetime."""
    validate_decimal(tolerance, field_name='requested consumer error tolerance', minimum=Decimal(0))
    threshold = _log_error(tolerance)
    return tuple((m, h, p is not None and p <= threshold, u is not None and u <= threshold)
                 for (m, h), p, u in zip(ENDPOINTS, forecast.log_error_points, forecast.log_error_uppers, strict=True))
