# SPDX-License-Identifier: MPL-2.0
"""New joint E3 design and conditional whole-group calibration.

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

ENDPOINTS = tuple((m,h) for m in PREDICTORS for h in HORIZONS)
STANDING = 'UNASSESSED_PROSPECTIVE_JOINT_DESIGN_NO_QUALIFICATION'
CALIBRATION_ROLE = 'CALIBRATION'
EVALUATION_ROLE = 'EVALUATION'
OUTCOME_DISPOSITIONS = ('FINITE','NO_CAUSAL_ORIGIN','REFUSED','NATIVE_CROSSCHECK_FAILED',
    'UNKNOWN_CONTACT','UNRESOLVED','MEASUREMENT_UNRESOLVED','OBSERVATION_UNRESOLVED','UNAVAILABLE','NOT_ENTERED')


def identity(record):
    return ObjectIdentity.from_record(record.record_id,record)


def split_rank(n, alpha):
    if type(n) is not int or n < 0 or type(alpha) is not Decimal or not Decimal(0) < alpha < Decimal(1):
        raise ValueError('joint split rank needs a complete group count and exact probability')
    numerator,denominator = alpha.as_integer_ratio()
    top = (n+1)*(denominator-numerator)
    return (top+denominator-1)//denominator


@dataclass(frozen=True,slots=True)
class MatrixResponseErrorGroupV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/group-v2'
    VERSION: ClassVar[str] = '2.0.0'
    independent_group_id: str
    family_id: str
    role: str
    root_ids: tuple[str,...]

    def __post_init__(self):
        validate_stable_id(self.independent_group_id)
        require_sorted_unique_strings(self.root_ids,field_name='whole-group roots',allow_empty=False)
        if self.family_id not in STRATA or self.role not in (CALIBRATION_ROLE,EVALUATION_ROLE):
            raise ValueError('joint error roster changes its four families/whole-group roles')


@dataclass(frozen=True,slots=True)
class MatrixResponseErrorRolesV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/roles-v2'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    reservation: ObjectIdentity
    groups: tuple[MatrixResponseErrorGroupV2,...]
    family_regimes: tuple[tuple[str,tuple[str,...]],...]
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        roots = tuple(r for g in self.groups for r in g.root_ids)
        if (self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or self.groups != tuple(sorted(self.groups,key=lambda g:g.independent_group_id))
                or len({g.independent_group_id for g in self.groups}) != len(self.groups)
                or not self.groups or len(set(roots)) != len(roots)
                or tuple(f for f,_ in self.family_regimes) != STRATA or self.standing != STANDING):
            raise ValueError('joint roles duplicate/drop whole groups or change reservation')
        regimes = tuple(r for _,values in self.family_regimes for r in values)
        if len(set(regimes)) != len(regimes):
            raise ValueError('joint roles pool a preparation regime across families')
        for _,values in self.family_regimes:
            require_sorted_unique_strings(values,field_name='reserved family regimes',allow_empty=False)

    @property
    def identity(self):
        return identity(self)

    def validate_reservation(self,reservation):
        if type(reservation) is not MatrixAllocationReservation or self.reservation != ObjectIdentity.from_record(
                reservation.reservation_id,reservation):
            raise ValueError('joint roles substitute the exact prior allocation reservation')
        reserved = {r.root_id:r for r in reservation.allocation.roots
                    if r.role in (MatrixProgrammeRole.CALIBRATION,MatrixProgrammeRole.CONFIRMATION)}
        if set(reserved) != {r for g in self.groups for r in g.root_ids}:
            raise ValueError('joint roles omit/duplicate allocated calibration/evaluation roots')
        family_regimes = dict(self.family_regimes)
        for group in self.groups:
            expected_role = MatrixProgrammeRole.CALIBRATION if group.role == CALIBRATION_ROLE else MatrixProgrammeRole.CONFIRMATION
            if (group.independent_group_id in reservation.allocation.exposure.exposed_independent_groups
                    or any(reserved[r].independent_group_id != group.independent_group_id
                           or reserved[r].role is not expected_role
                           or reserved[r].regime_id not in family_regimes[group.family_id] for r in group.root_ids)):
                raise ValueError('joint roles cross groups/families/roles or relabel exposed roots as fresh')


@dataclass(frozen=True,slots=True)
class MatrixResponseJointDesignV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-design-v2'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    roles: ObjectIdentity
    reservation: ObjectIdentity
    model: ObjectIdentity
    training_spec: ObjectIdentity
    criterion: ObjectIdentity
    joint_confidence: Decimal = Decimal('.95')
    family_alpha: Decimal = Decimal('.0125')
    endpoint_scope: str = 'WHOLE_GROUP_MAX15_FIVE_PREDICTORS_THREE_HORIZONS'
    simultaneity: str = 'FOUR_FAMILY_BONFERRONI_ONE_LOCKED_ERROR_MODEL'
    query_scope: str = 'ONE_PROSPECTIVE_WHOLE_GROUP_PER_FAMILY_NO_BANK_WIDE_OR_MULTI_MODEL_GUARANTEE'
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.roles.object_schema != MatrixResponseErrorRolesV2.SCHEMA
                or self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or self.training_spec.object_schema != 'empirical-lawhood/matrix-response-error/prediction-spec'
                or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or self.joint_confidence != Decimal('.95') or self.family_alpha != Decimal('.0125')
                or self.endpoint_scope != 'WHOLE_GROUP_MAX15_FIVE_PREDICTORS_THREE_HORIZONS'
                or self.simultaneity != 'FOUR_FAMILY_BONFERRONI_ONE_LOCKED_ERROR_MODEL'
                or self.query_scope != 'ONE_PROSPECTIVE_WHOLE_GROUP_PER_FAMILY_NO_BANK_WIDE_OR_MULTI_MODEL_GUARANTEE'
                or self.standing != STANDING):
            raise ValueError('joint design changes selected .95/4family/15endpoint/model/criterion scope')

    @property
    def identity(self):
        return identity(self)

    def validate_roles(self,roles):
        if type(roles) is not MatrixResponseErrorRolesV2 or roles.identity != self.roles or roles.reservation != self.reservation:
            raise ValueError('joint design changes its complete selected roles/reservation')
        for family in STRATA:
            n = sum(g.family_id == family and g.role == CALIBRATION_ROLE for g in roles.groups)
            if n < 79 or split_rank(n,self.family_alpha) > n or not any(
                    g.family_id == family and g.role == EVALUATION_ROLE for g in roles.groups):
                raise ValueError('joint .95 design needs at least79 independent calibration groups and evaluation in every family')


@dataclass(frozen=True,slots=True)
class MatrixResponseCausalErrorInputV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/causal-input-v2'
    VERSION: ClassVar[str] = '2.0.0'
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
        if (self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA or self.family_id not in STRATA
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
    if (type(feature) is not MatrixResponseCausalErrorInputV2 or feature.design != design.identity
            or group is None or (group.independent_group_id,group.family_id) != (feature.independent_group_id,feature.family_id)):
        raise ValueError('joint feature changes exact root/group/family/design')
    if feature.disposition == 'AVAILABLE':
        values = dict(feature.values)
        if values['cutoff'] != feature.cutoff or any(values['family-'+f.rsplit('.',1)[1]] != Decimal(feature.family_id == f)
                for f in STRATA[1:]):
            raise ValueError('joint feature substitutes actual cutoff/preparation family')


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
        raise ValueError('joint feature projection substitutes actual source/origin/root/clock')
    design.validate_roles(roles)
    evidence = tuple(sorted((response_identity(source),response_identity(origin),
        ObjectIdentity.from_record(origin.arrays.operand_id,origin.arrays)),key=lambda e:e.object_id))
    values,disposition = (), 'REFUSED'
    try:
        expected = (d.origin_tick+1,2,3,4,4)
        if any(arrays[n].shape != expected or arrays[n].dtype != np.dtype('<c16') for n in ('positions','momenta')):
            raise ValueError('joint feature source loses its exact causal-prefix geometry')
        frame = np.asarray(arrays['frame'])
        if (frame.shape != (3,4,4) or frame.dtype != np.dtype('<c16')
                or sha256(np.ascontiguousarray(frame).tobytes()).hexdigest() != origin.frame_sha256):
            raise ValueError('joint feature source changes the sealed causal frame')
        sector = ('X','Y').index(d.factor_sector)
        measured = {tick:measure_sector(arrays['positions'][tick,sector],d.rule)
                    if tick <= d.origin_tick else None for tick in d.rule.lattice}
        observations,frames = causal_observations(d.rule,measured)
        if d.origin_tick not in frames or not np.allclose(frames[d.origin_tick],frame,rtol=0,atol=1e-12):
            raise ValueError('joint feature apparatus differs from actual origin frame')
        wanted = tuple(range(max(0,d.origin_tick-32),d.origin_tick+1,16))
        past = tuple(o for o in observations if o.tick in wanted)
        if (tuple(o.tick for o in past) != wanted or any(o.status != 'AVAILABLE' or o.identifiable is not True
                or o.alignment_ambiguous for o in past) or len(past) < 2):
            raise ValueError('joint feature source lacks complete causal window')
        last = past[-1]
        required = (last.associative_leakage,last.lie_leakage,last.factor_fit_angle_degrees,
                    *(o.adjacent_angle_degrees for o in past[1:]))
        if any(type(v) is not Decimal or not v.is_finite() or v < 0 for v in required):
            raise ValueError('joint feature source lacks actual within-window diagnostics')
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
                    raise ValueError('joint feature state changes full finite Hermitian geometry')
                for j,sector_name in enumerate(('x','y')):
                    norm = Decimal(repr(float(np.linalg.norm(state[j]))))
                    context[label+'-'+sector_name+'-norm'] = (Decimal(1)+norm).ln()
        values,disposition = tuple(sorted(context.items())),'AVAILABLE'
    except (ValueError,TypeError,KeyError,AttributeError,FloatingPointError):
        pass
    result = MatrixResponseCausalErrorInputV2(record_id,design.identity,source.root.root_id,
        source.root.independent_group_id,group.family_id,response_identity(source),response_identity(origin),
        source.root.clock_id,d.cutoff,origin.frame_sha256,disposition,values,evidence)
    _validate_input(design,roles,result)
    return result


def points(design,model,feature):
    if type(model) is not MatrixResponseErrorModel or identity(model) != design.model or model.spec != design.training_spec:
        raise ValueError('joint predictor substitutes locked training model/specification')
    raw = [None]*15
    if feature.disposition == 'AVAILABLE':
        values = dict(feature.values)
        x = np.asarray([1.,*(0. if z else (float(values[n])-float(a))/float(s)
            for n,a,s,z in zip(model.feature_names,model.means,model.scales,model.zero_variance_mask,strict=True))])
        for j,c in enumerate(model.coefficients):
            supported = model.method != 'CONTEXT' or model.endpoint_family_group_counts[j][STRATA.index(feature.family_id)] > 0
            if c is not None and supported:
                value = float(np.dot(x,np.asarray(tuple(map(float,c)))))
                if np.isfinite(value):
                    raw[j] = Decimal(repr(value))
    result = []
    for start in range(0,15,3):
        previous,missing = Decimal(0),False
        for value in raw[start:start+3]:
            missing = missing or value is None
            if missing:
                result.append(None)
            else:
                previous = max(previous,value);result.append(previous)
    return tuple(raw),tuple(result)


@dataclass(frozen=True,slots=True)
class MatrixResponseJointCalibrationV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-calibration-v2'
    VERSION: ClassVar[str] = '2.0.0'
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
        if (self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA or self.roles.object_schema != MatrixResponseErrorRolesV2.SCHEMA
                or self.model.object_schema != MatrixResponseErrorModel.SCHEMA or self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or not self.scores or not self.input_identities
                or any(i.object_schema != MatrixResponseCausalErrorInputV2.SCHEMA for i in self.input_identities)
                or tuple(i.object_id for i in self.input_identities) != tuple(sorted({i.object_id for i in self.input_identities}))
                or tuple(s[0] for s in self.scores) != tuple(sorted({s[0] for s in self.scores})) or self.standing != STANDING):
            raise ValueError('joint calibration changes complete whole-group ancestry/score census')
        for group,family,value,reasons in self.scores:
            validate_stable_id(group)
            require_sorted_unique_strings(reasons,field_name='calibration reasons',allow_empty=False)
            if family not in STRATA:
                raise ValueError('joint calibration changes family')
            if value is not None:
                validate_decimal(value,field_name='root max15 score',minimum=Decimal(0))

    @property
    def identity(self):
        return identity(self)


def calibration_radius(calibration,family,alpha=Decimal('.0125')):
    if family not in STRATA:
        raise ValueError('joint radius changes declared family')
    scores = tuple(s[2] for s in calibration.scores if s[1] == family)
    n = len(scores);k = split_rank(n,alpha)
    ordered = tuple(sorted(v for v in scores if v is not None))+(None,)*sum(v is None for v in scores)
    return n,k,None if k > n else ordered[k-1]


def validate_calibration(design,roles,calibration):
    design.validate_roles(roles)
    expected = tuple((g.independent_group_id,g.family_id) for g in roles.groups if g.role == CALIBRATION_ROLE)
    if (type(calibration) is not MatrixResponseJointCalibrationV2 or calibration.design != design.identity
            or calibration.roles != roles.identity or calibration.reservation != design.reservation
            or calibration.model != design.model or tuple(s[:2] for s in calibration.scores) != expected
            or len(calibration.input_identities) != sum(len(g.root_ids) for g in roles.groups if g.role == CALIBRATION_ROLE)):
        raise ValueError('joint calibration thins/substitutes actual reserved groups/model/criterion')


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
        raise ValueError('joint calibration drops/duplicates/crosses reserved whole-root roles')
    for feature in features:
        _validate_input(design,roles,feature)
    scores = []
    for group in groups:
        residuals,reasons = [],[]
        for root in group.root_ids:
            losses,dispositions = ys[root]
            if len(losses) != 15 or len(dispositions) != 15:
                raise ValueError('joint calibration thins15 endpoints')
            _,predicted = points(design,model,fs[root])
            for j,(loss,point,disposition) in enumerate(zip(losses,predicted,dispositions,strict=True)):
                if disposition not in OUTCOME_DISPOSITIONS:
                    raise ValueError('joint calibration invents outcome disposition')
                if loss is not None:
                    validate_decimal(loss,field_name='reported finite-dt loss upper',minimum=Decimal(0))
                if (loss is None) != (disposition != 'FINITE'):
                    raise ValueError('joint calibration manufactures finite negative/unknown outcomes')
                if j % 3 and loss is not None and (losses[j-1] is None or loss < losses[j-1]):
                    raise ValueError('joint calibration reverses/imputes cumulative horizons')
                if loss is None or point is None:
                    reasons.append(disposition if loss is None else 'NO_FINITE_MODEL' if fs[root].disposition == 'AVAILABLE' else fs[root].disposition)
                else:
                    with localcontext() as ctx:
                        ctx.prec = 50
                        residuals.append(max(Decimal(0),(Decimal(1)+loss).ln()-point))
        scores.append((group.independent_group_id,group.family_id,None if reasons else max(residuals),
            tuple(sorted(set(reasons))) if reasons else ('finite-whole-group-max15',)))
    result = MatrixResponseJointCalibrationV2(record_id,design.identity,roles.identity,design.reservation,design.model,
        tuple(scores),tuple(f.identity for f in sorted(features,key=lambda f:f.root_id)),
        sha256(canonical_json_bytes(tuple(outcomes))).hexdigest())
    validate_calibration(design,roles,result)
    return result


@dataclass(frozen=True,slots=True)
class MatrixResponseJointForecastV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-forecast-v2'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    design: ObjectIdentity
    roles: ObjectIdentity
    reservation: ObjectIdentity
    model: ObjectIdentity
    criterion: ObjectIdentity
    calibration: ObjectIdentity
    feature: MatrixResponseCausalErrorInputV2
    raw_log_error_points: tuple[Decimal|None,...]
    log_error_points: tuple[Decimal|None,...]
    log_error_uppers: tuple[Decimal|None,...]
    radius: Decimal|None
    standing: str = STANDING
    qualification: str = 'NOT_ESTABLISHED'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.design != self.feature.design or self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA
                or self.calibration.object_schema != MatrixResponseJointCalibrationV2.SCHEMA
                or self.roles.object_schema != MatrixResponseErrorRolesV2.SCHEMA or self.model.object_schema != MatrixResponseErrorModel.SCHEMA
                or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA or self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or any(len(v) != 15 for v in (self.raw_log_error_points,self.log_error_points,self.log_error_uppers))
                or self.standing != STANDING or self.qualification != 'NOT_ESTABLISHED'):
            raise ValueError('joint forecast changes actual locked operands/15endpoint/standing')
        if self.radius is not None:
            validate_decimal(self.radius,field_name='joint family radius',minimum=Decimal(0))
        for raw,point,upper in zip(self.raw_log_error_points,self.log_error_points,self.log_error_uppers,strict=True):
            if raw is not None:
                validate_decimal(raw,field_name='raw error point')
            for value in (point,upper):
                if value is not None:
                    validate_decimal(value,field_name='transformed error bound',minimum=Decimal(0))
            if upper != (None if self.radius is None or point is None else point+self.radius):
                raise ValueError('joint forecast clips infinity or changes radius')
        expected = []
        for start in range(0,15,3):
            prior,missing = Decimal(0),False
            for value in self.raw_log_error_points[start:start+3]:
                missing = missing or value is None
                if missing:expected.append(None)
                else:prior=max(prior,value);expected.append(prior)
        if self.log_error_points != tuple(expected) or (self.feature.disposition != 'AVAILABLE' and any(
                v is not None for v in (*self.raw_log_error_points,*self.log_error_points,*self.log_error_uppers))):
            raise ValueError('joint forecast changes cumulative transform or manufactures refused predictions')

    @property
    def identity(self):
        return identity(self)


def forecast(design,roles,model,calibration,feature,*,record_id):
    _validate_input(design,roles,feature);validate_calibration(design,roles,calibration)
    raw,point = points(design,model,feature)
    _,_,radius = calibration_radius(calibration,feature.family_id,design.family_alpha)
    upper = tuple(None if radius is None or p is None else p+radius for p in point)
    return MatrixResponseJointForecastV2(record_id,design.identity,roles.identity,design.reservation,design.model,
        design.criterion,calibration.identity,feature,raw,point,upper,radius)


@dataclass(frozen=True,slots=True)
class MatrixResponseJointReadoutV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/joint-readout-v2'
    VERSION: ClassVar[str] = '2.0.0'
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
        if (self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA or self.roles.object_schema != MatrixResponseErrorRolesV2.SCHEMA
                or self.qualification != 'NOT_ESTABLISHED'
                or self.usefulness != 'UNASSESSED_NO_INDEPENDENT_COVERAGE_OR_CONSUMER_ADMISSION'
                or self.cells != tuple(sorted(self.cells,key=lambda c:c[:3]))
                or len({c[:3] for c in self.cells}) != len(self.cells)):
            raise ValueError('joint readout changes exact result/standing census')
        for root,predictor,horizon,disposition,finite,covered in self.cells:
            validate_stable_id(root)
            if ((predictor,horizon) not in ENDPOINTS or type(finite) is not bool or covered is not None and type(covered) is not bool
                    or disposition not in ('FINITE_COVERED','FINITE_MISSED','UNBOUNDED','NONUSE','UNKNOWN')
                    or covered is not None and not finite):
                raise ValueError('joint readout confuses missing/nonuse/finite coverage')


def evaluate(design,roles,forecasts,outcomes,*,record_id):
    """Complete evaluation denominator; conditional coverage is not usefulness."""
    design.validate_roles(roles)
    roots = tuple(sorted(r for g in roles.groups if g.role == EVALUATION_ROLE for r in g.root_ids))
    ps = {p.feature.root_id:p for p in forecasts};ys = {r:values for r,*values in outcomes}
    if (len(ps) != len(forecasts) or len(ys) != len(outcomes) or tuple(sorted(ps)) != roots or tuple(sorted(ys)) != roots):
        raise ValueError('joint readout drops/duplicates/crosses requested evaluation roots')
    cells = []
    for root in roots:
        prediction = ps[root];_validate_input(design,roles,prediction.feature)
        if prediction.design != design.identity or prediction.model != design.model or prediction.criterion != design.criterion:
            raise ValueError('joint readout substitutes sealed model/criterion/forecast')
        losses,dispositions = ys[root]
        if len(losses) != 15 or len(dispositions) != 15:
            raise ValueError('joint readout thins15 endpoints')
        if any(j % 3 and loss is not None and (losses[j-1] is None or loss < losses[j-1])
               for j,loss in enumerate(losses)):
            raise ValueError('joint readout reverses/imputes cumulative horizons')
        for (predictor,horizon),loss,disposition,upper in zip(ENDPOINTS,losses,dispositions,prediction.log_error_uppers,strict=True):
            if disposition not in OUTCOME_DISPOSITIONS:
                raise ValueError('joint readout invents an outcome disposition')
            if loss is not None:
                validate_decimal(loss,field_name='evaluation loss',minimum=Decimal(0))
            if (loss is None) != (disposition != 'FINITE'):
                raise ValueError('joint readout manufactures finite negative/unknown outcomes')
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
    return MatrixResponseJointReadoutV2(record_id,design.identity,roles.identity,
        tuple(ps[r].identity for r in roots),sha256(canonical_json_bytes(tuple(outcomes))).hexdigest(),
        tuple(sorted(cells,key=lambda c:c[:3])))
