# SPDX-License-Identifier: MPL-2.0
"""Lean E3 pooled whole-group calibration for one declared population.

The original exposed256/32-16-16 owners are unchanged. A sufficient roster
does not establish exchangeability, numerical adequacy, finite bounds or useful
coverage. Prior publication custody and the pre-future seal belong to the
versioned caller, not to these pure numerical records.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)

from .eligibility import MatrixAllocationReservation
from .response_error_prediction import FEATURES, FEATURE_DISPOSITIONS, MatrixResponseErrorModel
from .response_frontier import MatrixResponseFrontierProtocol
from .response_population_statistics import HORIZONS, STRATA
from .records import PREDICTORS
from .response_error_joint_v2 import points, split_rank

ENDPOINTS = tuple((m,h) for m in PREDICTORS for h in HORIZONS)
STANDING = 'UNASSESSED_PROSPECTIVE_POOLED_DESIGN_NO_QUALIFICATION'
CALIBRATION_ROLE = 'CALIBRATION'
EVALUATION_ROLE = 'EVALUATION'
OUTCOME_DISPOSITIONS = ('FINITE','NO_CAUSAL_ORIGIN','REFUSED','NATIVE_CROSSCHECK_FAILED',
    'UNKNOWN_CONTACT','UNRESOLVED','MEASUREMENT_UNRESOLVED','OBSERVATION_UNRESOLVED','UNAVAILABLE','NOT_ENTERED')


def identity(record):
    return ObjectIdentity.from_record(record.record_id,record)


@dataclass(frozen=True,slots=True)
class MatrixResponseErrorGroupPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/group-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    independent_group_id: str
    family_id: str
    role: str
    root_ids: tuple[str,...]

    def __post_init__(self):
        validate_stable_id(self.independent_group_id)
        require_sorted_unique_strings(self.root_ids,field_name='whole-group roots',allow_empty=False)
        if self.family_id not in STRATA or self.role not in (CALIBRATION_ROLE,EVALUATION_ROLE):
            raise ValueError('pooled error roster changes declared feature family/whole-group roles')


@dataclass(frozen=True,slots=True)
class MatrixResponseErrorRolesPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/roles-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    reservation: ObjectIdentity
    groups: tuple[MatrixResponseErrorGroupPooled,...]
    family_regimes: tuple[tuple[str,tuple[str,...]],...]
    population_id: str
    transfer_regime_ids: tuple[str,...]
    transfer_group_counts: tuple[int,int] = (64,64)
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.population_id)
        require_sorted_unique_strings(self.transfer_regime_ids,field_name='two prior E6 regimes',allow_empty=False)
        roots = tuple(r for g in self.groups for r in g.root_ids)
        if (self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or self.groups != tuple(sorted(self.groups,key=lambda g:g.independent_group_id))
                or len({g.independent_group_id for g in self.groups}) != len(self.groups)
                or not self.groups or len(set(roots)) != len(roots)
                or tuple(f for f,_ in self.family_regimes) != tuple(sorted({g.family_id for g in self.groups}))
                or len(self.transfer_regime_ids) != 2 or len(self.transfer_group_counts) != 2
                or any(type(n) is not int or n < 1 for n in self.transfer_group_counts) or self.standing != STANDING):
            raise ValueError('pooled roles duplicate/drop whole groups or change reservation')
        regimes = tuple(r for _,values in self.family_regimes for r in values)
        if len(set(regimes)) != len(regimes):
            raise ValueError('pooled roles assign a preparation regime to two feature families')
        for _,values in self.family_regimes:
            require_sorted_unique_strings(values,field_name='reserved population regimes',allow_empty=False)
        if set(regimes) & set(self.transfer_regime_ids):
            raise ValueError('pooled population overlaps its two untouched E6 regimes')

    @property
    def identity(self):
        return identity(self)

    def validate_reservation(self,reservation):
        if type(reservation) is not MatrixAllocationReservation or self.reservation != ObjectIdentity.from_record(
                reservation.reservation_id,reservation):
            raise ValueError('pooled roles substitute the exact prior allocation reservation')
        reserved = {r.root_id:r for r in reservation.allocation.roots
                    if r.role in (MatrixProgrammeRole.CALIBRATION,MatrixProgrammeRole.CONFIRMATION)}
        if set(reserved) != {r for g in self.groups for r in g.root_ids}:
            raise ValueError('pooled roles omit/duplicate allocated calibration/evaluation roots')
        transfer = tuple(r for r in reservation.allocation.roots if r.role is MatrixProgrammeRole.WITHHELD_TRANSFER)
        if (tuple(sorted({r.regime_id for r in transfer})) != self.transfer_regime_ids
                or any(len({r.independent_group_id for r in transfer if r.regime_id == regime}) != count
                       for regime,count in zip(self.transfer_regime_ids,self.transfer_group_counts,strict=True))):
            raise ValueError('lean E3 requires the two prior whole E6 regimes and their declared group counts')
        family_regimes = dict(self.family_regimes)
        for group in self.groups:
            expected_role = MatrixProgrammeRole.CALIBRATION if group.role == CALIBRATION_ROLE else MatrixProgrammeRole.CONFIRMATION
            if (group.independent_group_id in reservation.allocation.exposure.exposed_independent_groups
                    or any(reserved[r].independent_group_id != group.independent_group_id
                           or reserved[r].role is not expected_role
                           or reserved[r].regime_id not in family_regimes[group.family_id] for r in group.root_ids)):
                raise ValueError('pooled roles cross groups/families/roles or relabel exposed roots as fresh')


@dataclass(frozen=True,slots=True)
class MatrixResponseJointDesignPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-design-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    roles: ObjectIdentity
    reservation: ObjectIdentity
    model: ObjectIdentity
    training_spec: ObjectIdentity
    criterion: ObjectIdentity
    calibration_group_count: int = 64
    evaluation_group_count: int = 64
    joint_confidence: Decimal = Decimal('.95')
    population_alpha: Decimal = Decimal('.05')
    endpoint_scope: str = 'WHOLE_GROUP_MAX15_FIVE_PREDICTORS_THREE_HORIZONS'
    simultaneity: str = 'ONE_POOLED_POPULATION_ONE_LOCKED_ERROR_MODEL'
    query_scope: str = 'ONE_PROSPECTIVE_WHOLE_GROUP_FROM_DECLARED_POPULATION_NO_PER_FAMILY_OR_TRANSFER_GUARANTEE'
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.roles.object_schema != MatrixResponseErrorRolesPooled.SCHEMA
                or self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or self.training_spec.object_schema != 'empirical-lawhood/matrix-response-error/prediction-spec'
                or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or type(self.calibration_group_count) is not int or type(self.evaluation_group_count) is not int
                or self.calibration_group_count < 1 or self.evaluation_group_count < 1
                or self.joint_confidence != Decimal('.95') or self.population_alpha != Decimal('.05')
                or split_rank(self.calibration_group_count,self.population_alpha) > self.calibration_group_count
                or self.endpoint_scope != 'WHOLE_GROUP_MAX15_FIVE_PREDICTORS_THREE_HORIZONS'
                or self.simultaneity != 'ONE_POOLED_POPULATION_ONE_LOCKED_ERROR_MODEL'
                or self.query_scope != 'ONE_PROSPECTIVE_WHOLE_GROUP_FROM_DECLARED_POPULATION_NO_PER_FAMILY_OR_TRANSFER_GUARANTEE'
                or self.standing != STANDING):
            raise ValueError('pooled design changes selected .95/onepopulation/15endpoint/model/criterion scope')

    @property
    def identity(self):
        return identity(self)

    def validate_roles(self,roles):
        if type(roles) is not MatrixResponseErrorRolesPooled or roles.identity != self.roles or roles.reservation != self.reservation:
            raise ValueError('pooled design changes its complete selected roles/reservation')
        counts = tuple(sum(g.role == role for g in roles.groups) for role in (CALIBRATION_ROLE,EVALUATION_ROLE))
        if counts != (self.calibration_group_count,self.evaluation_group_count):
            raise ValueError('lean pooled design thins declared independent calibration/evaluation group counts')



@dataclass(frozen=True,slots=True)
class MatrixResponseCausalErrorInputPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/causal-input-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    design: ObjectIdentity
    root_id: str
    independent_group_id: str
    family_id: str
    source: ObjectIdentity
    origin: ObjectIdentity
    clock_id: str
    cutoff: Decimal
    frame_sha256: str
    disposition: str
    values: tuple[tuple[str,Decimal],...]
    evidence: tuple[ObjectIdentity,...]
    standing: str = STANDING

    def __post_init__(self):
        for name in ('record_id','root_id','independent_group_id','clock_id'):
            validate_stable_id(getattr(self,name))
        validate_decimal(self.cutoff,field_name='causal feature cutoff',minimum=Decimal(0))
        validate_sha256(self.frame_sha256)
        if (self.design.object_schema != MatrixResponseJointDesignPooled.SCHEMA or self.family_id not in STRATA
                or self.disposition not in FEATURE_DISPOSITIONS or self.standing != STANDING
                or not self.evidence or tuple(e.object_id for e in self.evidence) != tuple(sorted({e.object_id for e in self.evidence}))
                or (tuple(k for k,_ in self.values) != FEATURES if self.disposition == 'AVAILABLE' else bool(self.values))):
            raise ValueError('joint causal input changes complete frozen feature/evidence boundary')
        for _,value in self.values:
            validate_decimal(value,field_name='causal error feature',minimum=Decimal(0))
            if not np.isfinite(float(value)):
                raise ValueError('joint causal input is numerically unrepresentable')

    @property
    def identity(self):
        return identity(self)


def _validate_input(design,roles,feature):
    design.validate_roles(roles)
    group = next((g for g in roles.groups if feature.root_id in g.root_ids),None)
    if (type(feature) is not MatrixResponseCausalErrorInputPooled or feature.design != design.identity
            or group is None or (group.independent_group_id,group.family_id) != (feature.independent_group_id,feature.family_id)):
        raise ValueError('pooled feature changes exact root/group/family/design')
    if feature.disposition == 'AVAILABLE':
        values = dict(feature.values)
        if values['cutoff'] != feature.cutoff or any(values['family-'+f.rsplit('.',1)[1]] != Decimal(feature.family_id == f)
                for f in STRATA[1:]):
            raise ValueError('pooled feature substitutes actual cutoff/preparation family')


def causal_input_from_origin(design,roles,source,origin,arrays,*,record_id):
    """Measure the receipted causal prefix; never access/draw a future stream.

    Caller authenticates the full origin manifest/arrays before this pure
    projection. The three feature-window observations use their complete
    intervals; alignment is reconstructed using the declared causal lattice.
    Chunk readers may supply indexed prefix arrays without materialising them.
    """
    from .records import identity as response_identity
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import causal_observations,measure_sector
    d = origin.design
    group = next((g for g in roles.groups if source.root.root_id in g.root_ids),None)
    if (group is None or group.independent_group_id != source.root.independent_group_id
            or origin.source != response_identity(source) or origin.design != source.design
            or (origin.root_id,origin.independent_group_id,origin.clock_id) != (
                source.root.root_id,source.root.independent_group_id,source.root.clock_id)):
        raise ValueError('pooled feature projection substitutes actual source/origin/root/clock')
    design.validate_roles(roles)
    evidence = tuple(sorted((response_identity(source),response_identity(origin),
        ObjectIdentity.from_record(origin.arrays.operand_id,origin.arrays)),key=lambda e:e.object_id))
    values,disposition = (), 'REFUSED'
    try:
        expected = (d.origin_tick+1,2,3,4,4)
        if any(arrays[n].shape != expected or arrays[n].dtype != np.dtype('<c16') for n in ('positions','momenta')):
            raise ValueError('pooled feature source loses its exact causal-prefix geometry')
        frame = np.asarray(arrays['frame'])
        if (frame.shape != (3,4,4) or frame.dtype != np.dtype('<c16')
                or sha256(np.ascontiguousarray(frame).tobytes()).hexdigest() != origin.frame_sha256):
            raise ValueError('pooled feature source changes the sealed causal frame')
        sector = ('X','Y').index(d.factor_sector)
        measured = {tick:measure_sector(arrays['positions'][tick,sector],d.rule)
                    if tick <= d.origin_tick else None for tick in d.rule.lattice}
        observations,frames = causal_observations(d.rule,measured)
        if d.origin_tick not in frames or not np.allclose(frames[d.origin_tick],frame,rtol=0,atol=1e-12):
            raise ValueError('pooled feature apparatus differs from actual origin frame')
        wanted = tuple(range(max(0,d.origin_tick-32),d.origin_tick+1,16))
        past = tuple(o for o in observations if o.tick in wanted)
        if (tuple(o.tick for o in past) != wanted or any(o.status != 'AVAILABLE' or o.identifiable is not True
                or o.alignment_ambiguous for o in past) or len(past) < 2):
            raise ValueError('pooled feature source lacks complete causal window')
        last = past[-1]
        required = (last.associative_leakage,last.lie_leakage,last.factor_fit_angle_degrees,
                    *(o.adjacent_angle_degrees for o in past[1:]))
        if any(type(v) is not Decimal or not v.is_finite() or v < 0 for v in required):
            raise ValueError('pooled feature source lacks actual within-window diagnostics')
        spectrum = tuple(Decimal(repr(float(v))) for v in measured[d.origin_tick].spectrum)
        context = {'alpha-x':d.alpha_x,'alpha-y':d.alpha_y,'bath-temperature':d.view.bath_temperature,
            'cross-gamma':d.member.cross_coupling_gamma,'friction':d.view.friction_gamma,'potential-m':d.member.mass_y,
            'cutoff':d.cutoff,**{'family-'+f.rsplit('.',1)[1]:Decimal(group.family_id == f) for f in STRATA[1:]},
            'largest-y-rate':spectrum[-1],'third-fourth-y-gap':spectrum[3]-spectrum[2],
            'associative-leakage':last.associative_leakage,'lie-leakage':last.lie_leakage,
            'factor-fit-angle':last.factor_fit_angle_degrees,'trailing-angle':max(required[3:])}
        with localcontext() as ctx:
            ctx.prec = 50
            context['slow-y-mean'] = sum(spectrum[:3])/3
            for name,label in (('positions','position'),('momenta','momentum')):
                state = np.asarray(arrays[name][d.origin_tick])
                if not np.isfinite(state).all() or not np.allclose(state,state.conj().swapaxes(-1,-2),rtol=0,atol=1e-12):
                    raise ValueError('pooled feature state changes full finite Hermitian geometry')
                for j,sector_name in enumerate(('x','y')):
                    norm = Decimal(repr(float(np.linalg.norm(state[j]))))
                    context[label+'-'+sector_name+'-norm'] = (Decimal(1)+norm).ln()
        values,disposition = tuple(sorted(context.items())),'AVAILABLE'
    except (ValueError,TypeError,KeyError,AttributeError,FloatingPointError):
        pass
    result = MatrixResponseCausalErrorInputPooled(record_id,design.identity,source.root.root_id,
        source.root.independent_group_id,group.family_id,response_identity(source),response_identity(origin),
        source.root.clock_id,d.cutoff,origin.frame_sha256,disposition,values,evidence)
    _validate_input(design,roles,result)
    return result


@dataclass(frozen=True,slots=True)
class MatrixResponseJointCalibrationPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-calibration-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    design: ObjectIdentity
    roles: ObjectIdentity
    reservation: ObjectIdentity
    model: ObjectIdentity
    scores: tuple[tuple[str,str,Decimal|None,tuple[str,...]],...]
    input_identities: tuple[ObjectIdentity,...]
    outcome_sha256: str
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id);validate_sha256(self.outcome_sha256)
        if (self.design.object_schema != MatrixResponseJointDesignPooled.SCHEMA or self.roles.object_schema != MatrixResponseErrorRolesPooled.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA or self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or not self.scores or not self.input_identities
                or any(i.object_schema != MatrixResponseCausalErrorInputPooled.SCHEMA for i in self.input_identities)
                or tuple(i.object_id for i in self.input_identities) != tuple(sorted({i.object_id for i in self.input_identities}))
                or tuple(s[0] for s in self.scores) != tuple(sorted({s[0] for s in self.scores})) or self.standing != STANDING):
            raise ValueError('pooled calibration changes complete whole-group ancestry/score census')
        for group,family,value,reasons in self.scores:
            validate_stable_id(group)
            require_sorted_unique_strings(reasons,field_name='calibration reasons',allow_empty=False)
            if family not in STRATA:
                raise ValueError('pooled calibration changes family')
            if value is not None:
                validate_decimal(value,field_name='root max15 score',minimum=Decimal(0))

    @property
    def identity(self):
        return identity(self)


def calibration_radius(calibration,alpha=Decimal('.05')):
    if type(calibration) is not MatrixResponseJointCalibrationPooled:
        raise ValueError('pooled radius substitutes the calibration edition')
    scores = tuple(s[2] for s in calibration.scores)
    n = len(scores);k = split_rank(n,alpha)
    ordered = tuple(sorted(v for v in scores if v is not None))+(None,)*sum(v is None for v in scores)
    return n,k,None if k > n else ordered[k-1]


def validate_calibration(design,roles,calibration):
    design.validate_roles(roles)
    expected = tuple((g.independent_group_id,g.family_id) for g in roles.groups if g.role == CALIBRATION_ROLE)
    if (type(calibration) is not MatrixResponseJointCalibrationPooled or calibration.design != design.identity
            or calibration.roles != roles.identity or calibration.reservation != design.reservation
            or calibration.model != design.model or tuple(s[:2] for s in calibration.scores) != expected
            or len(calibration.input_identities) != sum(len(g.root_ids) for g in roles.groups if g.role == CALIBRATION_ROLE)):
        raise ValueError('pooled calibration thins/substitutes actual reserved groups/model/criterion')


def calibrate(design,roles,model,features,outcomes,*,record_id):
    """Complete supplied calibration corpus; no acquisition or custody claim.

    outcomes are (root_id, fifteen cumulative finite-dt upper losses or None,
    fifteen explicit dispositions). Missing/nonuse/unknown values give infinity;
    nested roots of one independent group are maximised together.
    """
    design.validate_roles(roles)
    groups = tuple(g for g in roles.groups if g.role == CALIBRATION_ROLE)
    roots = tuple(sorted(r for g in groups for r in g.root_ids))
    fs = {f.root_id:f for f in features};ys = {row[0]:row[1:] for row in outcomes}
    if len(fs) != len(features) or len(ys) != len(outcomes) or tuple(sorted(fs)) != roots or tuple(sorted(ys)) != roots:
        raise ValueError('pooled calibration drops/duplicates/crosses reserved whole-root roles')
    for feature in features:
        _validate_input(design,roles,feature)
    scores = []
    for group in groups:
        residuals,reasons = [],[]
        for root in group.root_ids:
            losses,dispositions = ys[root]
            if len(losses) != 15 or len(dispositions) != 15:
                raise ValueError('pooled calibration thins15 endpoints')
            _,predicted = points(design,model,fs[root])
            for j,(loss,point,disposition) in enumerate(zip(losses,predicted,dispositions,strict=True)):
                if disposition not in OUTCOME_DISPOSITIONS:
                    raise ValueError('pooled calibration invents outcome disposition')
                if loss is not None:
                    validate_decimal(loss,field_name='reported finite-dt loss upper',minimum=Decimal(0))
                if (loss is None) != (disposition != 'FINITE'):
                    raise ValueError('pooled calibration manufactures finite negative/unknown outcomes')
                if j % 3 and loss is not None and (losses[j-1] is None or loss < losses[j-1]):
                    raise ValueError('pooled calibration reverses/imputes cumulative horizons')
                if loss is None or point is None:
                    reasons.append(disposition if loss is None else 'NO_FINITE_MODEL' if fs[root].disposition == 'AVAILABLE' else fs[root].disposition)
                else:
                    with localcontext() as ctx:
                        ctx.prec = 50
                        residuals.append(max(Decimal(0),(Decimal(1)+loss).ln()-point))
        scores.append((group.independent_group_id,group.family_id,None if reasons else max(residuals),
            tuple(sorted(set(reasons))) if reasons else ('finite-whole-group-max15',)))
    result = MatrixResponseJointCalibrationPooled(record_id,design.identity,roles.identity,design.reservation,design.model,
        tuple(scores),tuple(f.identity for f in sorted(features,key=lambda f:f.root_id)),
        sha256(canonical_json_bytes(tuple(outcomes))).hexdigest())
    validate_calibration(design,roles,result)
    return result


@dataclass(frozen=True,slots=True)
class MatrixResponseJointForecastPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-forecast-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    design: ObjectIdentity
    roles: ObjectIdentity
    reservation: ObjectIdentity
    model: ObjectIdentity
    criterion: ObjectIdentity
    calibration: ObjectIdentity
    feature: MatrixResponseCausalErrorInputPooled
    raw_log_error_points: tuple[Decimal|None,...]
    log_error_points: tuple[Decimal|None,...]
    log_error_uppers: tuple[Decimal|None,...]
    radius: Decimal|None
    standing: str = STANDING
    qualification: str = 'NOT_ESTABLISHED'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.design != self.feature.design or self.design.object_schema != MatrixResponseJointDesignPooled.SCHEMA
                or self.calibration.object_schema != MatrixResponseJointCalibrationPooled.SCHEMA
                or self.roles.object_schema != MatrixResponseErrorRolesPooled.SCHEMA or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA or self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or any(len(v) != 15 for v in (self.raw_log_error_points,self.log_error_points,self.log_error_uppers))
                or self.standing != STANDING or self.qualification != 'NOT_ESTABLISHED'):
            raise ValueError('pooled forecast changes actual locked operands/15endpoint/standing')
        if self.radius is not None:
            validate_decimal(self.radius,field_name='pooled population radius',minimum=Decimal(0))
        for raw,point,upper in zip(self.raw_log_error_points,self.log_error_points,self.log_error_uppers,strict=True):
            if raw is not None:
                validate_decimal(raw,field_name='raw error point')
            for value in (point,upper):
                if value is not None:
                    validate_decimal(value,field_name='transformed error bound',minimum=Decimal(0))
            if upper != (None if self.radius is None or point is None else point+self.radius):
                raise ValueError('pooled forecast clips infinity or changes radius')
        expected = []
        for start in range(0,15,3):
            prior,missing = Decimal(0),False
            for value in self.raw_log_error_points[start:start+3]:
                missing = missing or value is None
                if missing:expected.append(None)
                else:prior=max(prior,value);expected.append(prior)
        if self.log_error_points != tuple(expected) or (self.feature.disposition != 'AVAILABLE' and any(
                v is not None for v in (*self.raw_log_error_points,*self.log_error_points,*self.log_error_uppers))):
            raise ValueError('pooled forecast changes cumulative transform or manufactures refused predictions')

    @property
    def identity(self):
        return identity(self)


def forecast(design,roles,model,calibration,feature,*,record_id):
    _validate_input(design,roles,feature);validate_calibration(design,roles,calibration)
    raw,point = points(design,model,feature)
    _,_,radius = calibration_radius(calibration,design.population_alpha)
    upper = tuple(None if radius is None or p is None else p+radius for p in point)
    return MatrixResponseJointForecastPooled(record_id,design.identity,roles.identity,design.reservation,design.model,
        design.criterion,calibration.identity,feature,raw,point,upper,radius)


@dataclass(frozen=True,slots=True)
class MatrixResponseJointReadoutPooled(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-readout-pooled-v1'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    design: ObjectIdentity
    roles: ObjectIdentity
    forecasts: tuple[ObjectIdentity,...]
    outcome_sha256: str
    cells: tuple[tuple[str,str,int,str,bool,bool|None],...]
    qualification: str = 'NOT_ESTABLISHED'
    usefulness: str = 'UNASSESSED_NO_INDEPENDENT_COVERAGE_OR_CONSUMER_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.record_id);validate_sha256(self.outcome_sha256)
        if (self.design.object_schema != MatrixResponseJointDesignPooled.SCHEMA or self.roles.object_schema != MatrixResponseErrorRolesPooled.SCHEMA
                or self.qualification != 'NOT_ESTABLISHED'
                or self.usefulness != 'UNASSESSED_NO_INDEPENDENT_COVERAGE_OR_CONSUMER_ADMISSION'
                or self.cells != tuple(sorted(self.cells,key=lambda c:c[:3]))
                or len({c[:3] for c in self.cells}) != len(self.cells)):
            raise ValueError('pooled readout changes exact result/standing census')
        for root,predictor,horizon,disposition,finite,covered in self.cells:
            validate_stable_id(root)
            if ((predictor,horizon) not in ENDPOINTS or type(finite) is not bool or covered is not None and type(covered) is not bool
                    or disposition not in ('FINITE_COVERED','FINITE_MISSED','UNBOUNDED','NONUSE','UNKNOWN')
                    or covered is not None and not finite):
                raise ValueError('pooled readout confuses missing/nonuse/finite coverage')


def evaluate(design,roles,forecasts,outcomes,*,calibration,record_id):
    """Assess the complete denominator against the selected frozen calibration.

    Caller supplies the prior calibrated package; agreeing replacement forecasts
    cannot select a different package from evaluation outcomes. Conditional
    coverage remains distinct from usefulness and scientific qualification.
    """
    validate_calibration(design,roles,calibration)
    _,_,radius = calibration_radius(calibration,design.population_alpha)
    if any(type(p) is not MatrixResponseJointForecastPooled for p in forecasts):
        raise ValueError('pooled readout substitutes the actual typed forecast edition')
    roots = tuple(sorted(r for g in roles.groups if g.role == EVALUATION_ROLE for r in g.root_ids))
    ps = {p.feature.root_id:p for p in forecasts};ys = {r:values for r,*values in outcomes}
    if (len(ps) != len(forecasts) or len(ys) != len(outcomes) or tuple(sorted(ps)) != roots or tuple(sorted(ys)) != roots):
        raise ValueError('pooled readout drops/duplicates/crosses requested evaluation roots')
    cells = []
    for root in roots:
        prediction = ps[root];_validate_input(design,roles,prediction.feature)
        if (prediction.design != design.identity or prediction.model != design.model or prediction.criterion != design.criterion
                or prediction.roles != roles.identity or prediction.reservation != design.reservation
                or prediction.calibration != calibration.identity or prediction.radius != radius):
            raise ValueError('pooled readout substitutes the selected frozen model/criterion/roles/reservation/calibration package')
        losses,dispositions = ys[root]
        if len(losses) != 15 or len(dispositions) != 15:
            raise ValueError('pooled readout thins15 endpoints')
        if any(j % 3 and loss is not None and (losses[j-1] is None or loss < losses[j-1])
               for j,loss in enumerate(losses)):
            raise ValueError('pooled readout reverses/imputes cumulative horizons')
        for (predictor,horizon),loss,disposition,upper in zip(ENDPOINTS,losses,dispositions,prediction.log_error_uppers,strict=True):
            if disposition not in OUTCOME_DISPOSITIONS:
                raise ValueError('pooled readout invents an outcome disposition')
            if loss is not None:
                validate_decimal(loss,field_name='evaluation loss',minimum=Decimal(0))
            if (loss is None) != (disposition != 'FINITE'):
                raise ValueError('pooled readout manufactures finite negative/unknown outcomes')
            finite = upper is not None
            if disposition in ('NO_CAUSAL_ORIGIN','REFUSED','NATIVE_CROSSCHECK_FAILED'):
                status,covered = 'NONUSE',None
            elif loss is None:
                status,covered = 'UNKNOWN',None
            elif upper is None:
                status,covered = 'UNBOUNDED',None
            else:
                with localcontext() as ctx:
                    ctx.prec = 50;covered = (Decimal(1)+loss).ln() <= upper
                status = 'FINITE_COVERED' if covered else 'FINITE_MISSED'
            cells.append((root,predictor,horizon,status,finite,covered))
    return MatrixResponseJointReadoutPooled(record_id,design.identity,roles.identity,
        tuple(ps[r].identity for r in roots),sha256(canonical_json_bytes(tuple(outcomes))).hexdigest(),
        tuple(sorted(cells,key=lambda c:c[:3])))
