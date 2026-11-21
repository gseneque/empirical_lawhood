# SPDX-License-Identifier: MPL-2.0
"""Two distinct classical capstone connections with frozen, reusable coefficients.

This is a new authored adaptation, not a historical-result importer. One connection
forecasts a 24-coordinate prepared description before preparation, then supplies
that forecast to an already frozen response relation. The other applies the same
complete relation, support and calibration to actual descriptions after different
physical preparations. Fits use TRAIN only; complete-root residuals use CAL only;
CONF commitments are made before the observations whose outcomes they predict.

Pure JSON arithmetic here owns no acquisition, scheduler, custody or qualification.
The native domain supplies the initial/actual descriptors and fixed scalar assay
channels; its shared execution product binds these records and the source closure.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
import math

import numpy as np

SUMMARY_SCHEMA = 'classical-series-capstone-case.v1'
PACKAGE_SCHEMA = 'classical-series-capstones.v1'
PREPARATION_COMMITMENT_SCHEMA = 'classical-series-before-preparation.v1'
RESPONSE_COMMITMENT_SCHEMA = 'classical-series-fixed-response-commitment.v1'


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _vector(value, dimension, name):
    result = np.asarray(value, dtype=float)
    if result.shape != (dimension,) or not np.isfinite(result).all():
        raise ValueError(f'{name} requires {dimension} finite coordinates')
    return result


def _descriptors(value):
    result = np.asarray(value, dtype=float)
    if result.shape == (24,):
        result = result[None]
    if result.ndim != 2 or result.shape[1] != 24 or result.shape[0] not in (1, 2) or not np.isfinite(result).all():
        raise ValueError('prepared descriptions require one or two finite 24-coordinate views')
    return result


def _seed(value):
    if type(value) is not int or value < 0:
        raise ValueError('capstone root seed must be a nonnegative integer')
    return value


def _settings(config):
    if not isinstance(config, Mapping):
        raise TypeError('capstone scientific settings require a mapping')
    n = config['horizon_ticks']
    selected = config.get('capstone_horizon_tick')
    horizon = min(64, n) if selected is None else selected
    if type(horizon) is not int or not 1 <= horizon <= n:
        raise ValueError('capstone horizon must be an acquired positive tick')
    radius = float(config.get('capstone_support_radius', '3'))
    threshold = float(config.get('capstone_task_threshold', '0'))
    tolerance = float(config['response_tolerance'])
    alpha, ridge = float(config['calibration_alpha']), float(config['ridge_penalty'])
    if not all(math.isfinite(x) for x in (radius, threshold, tolerance, alpha, ridge)) or min(radius, tolerance, ridge) <= 0 or not 0 < alpha < 1:
        raise ValueError('capstone support, tolerance, alpha or ridge setting is invalid')
    actions = list(config['actions'])
    if not actions or len(set(actions)) != len(actions):
        raise ValueError('capstone needs the original unique physical action census')
    return {'horizon_tick': horizon, 'support_radius': radius, 'task_threshold': threshold,
        'response_tolerance': tolerance, 'alpha': alpha, 'ridge_penalty': ridge,
        'tasks': [
            {'task_id':'position-task', 'action':actions[0], 'action_index':0,
             'block':'POSITION','receiver_component':1,'receiver_index':1},
            {'task_id':'momentum-task', 'action':actions[-1], 'action_index':len(actions)-1,
             'block':'MOMENTUM','receiver_component':0,'receiver_index':24}],
        'coordinate_ids': [row['id'] for row in config['coordinates']],
        'arms': list(config['preparation_arms'])}


def _config_digest(config):
    return _digest({key:value for key, value in config.items() if key != 'phases'})


def _coordinate_features(coordinate):
    vals = [float(coordinate[key]) for key in ('temperature', 'friction', 'cross_coupling')]
    if any(not math.isfinite(x) or x <= 0 for x in vals):
        raise ValueError('native parameter coordinates must be finite and positive')
    return np.log(vals)


def _nominal(coordinate):
    return bool(np.all(_coordinate_features(coordinate) == 0))


def _forces(value, config):
    result = np.asarray(value, dtype=float)
    if result.shape != (96, len(config['actions'])) or not np.isfinite(result).all():
        raise ValueError('capstone requires the actual complete 96-coordinate force chart')
    return result


def _response_features(descriptor, coordinate, force):
    # Each feature is odd in the physical force. Descriptor-only intercepts
    # would predict a response even at zero force and break the signed chord.
    context=np.concatenate(([1.],_vector(descriptor,24,'prepared descriptor'),_coordinate_features(coordinate)))
    return np.outer(_vector(force,96,'physical force'),context).reshape(-1)


def _upstream_features(descriptor, coordinate):
    return np.concatenate((_vector(descriptor, 24, 'initial descriptor'), _coordinate_features(coordinate)))


def _fit(features, targets, penalty, *, odd=False):
    if not features:
        return {'status':'FIT_UNAVAILABLE','training_rows':0}
    x, y = np.asarray(features), np.asarray(targets)
    if y.ndim == 1:
        y = y[:, None]
    mean, target_mean = (np.zeros(x.shape[1]),np.zeros(y.shape[1])) if odd else (x.mean(axis=0),y.mean(axis=0))
    centered = x-mean
    scale = np.sqrt(np.mean(centered**2, axis=0))
    floor = 64*np.finfo(float).eps*np.maximum(1., np.abs(mean))
    scale = np.where(scale > floor, scale, 1.)
    standardized, yy = centered/scale, y-target_mean
    # Dual solve scales with acquired TRAIN rows, avoiding a dense feature-square
    # solve when physical force covariates exceed the independent root count.
    if len(x) <= x.shape[1]:
        coefficients = standardized.T@np.linalg.solve(standardized@standardized.T+penalty*np.eye(len(x)), yy)
    else:
        coefficients = np.linalg.solve(standardized.T@standardized+penalty*np.eye(x.shape[1]), standardized.T@yy)
    return {'status':'FROZEN','training_rows':len(x),'feature_mean':mean.tolist(),
        'feature_scale':scale.tolist(),'target_mean':target_mean.tolist(),
        'coefficients':coefficients.tolist(),'ridge_penalty':penalty,'force_odd':odd}


def _predict(model, features):
    if model.get('status') != 'FROZEN':
        return None
    x = np.asarray(features, dtype=float)
    mean, scale = np.asarray(model['feature_mean']), np.asarray(model['feature_scale'])
    if x.shape != mean.shape or not np.isfinite(x).all() or np.any(scale <= 0):
        raise ValueError('frozen capstone model feature contract changed')
    value = np.asarray(model['target_mean'])+(x-mean)/scale@np.asarray(model['coefficients'])
    if not np.isfinite(value).all():
        raise ArithmeticError('frozen capstone prediction became nonfinite')
    return value


def _radius(scores, alpha):
    order = math.ceil((len(scores)+1)*(1-alpha))
    ordered = sorted(math.inf if value is None else value for value in scores)
    value = math.inf if order > len(scores) else ordered[order-1]
    return None if not math.isfinite(value) else float(value), order


def _support(descriptor, support, *, extra_radius=0.):
    if support is None:
        return False, None
    z = _descriptors(descriptor)
    center, scale = np.asarray(support['center']), np.asarray(support['scale'])
    distance = float(np.max(np.abs(z-center)/scale))
    return bool(distance+extra_radius <= support['radius']), distance


def _package(config, package, seed=None):
    if package is None:
        return None
    if (not isinstance(package, dict) or package.get('schema') != PACKAGE_SCHEMA
            or package.get('config_sha256') != _config_digest(config)
            or package.get('package_sha256') != _digest({k:v for k,v in package.items() if k!='package_sha256'})):
        raise ValueError('capstone package has changed settings, coefficients, support or calibration')
    if seed is not None and seed in set(package['training_seeds'])|set(package['calibration_seeds']):
        raise ValueError('a confirmation commitment cannot reuse a TRAIN or CAL root')
    fixed = package['fixed_response_package']
    if fixed['package_sha256'] != _digest({k:v for k,v in fixed.items() if k!='package_sha256'}):
        raise ValueError('unchanged response package digest is invalid')
    return package


def _prediction_records(config, coordinate, descriptor, forces, fixed, radius, *, descriptor_radius=0.):
    settings = _settings(config)
    force = _forces(forces, config)
    descriptors = _descriptors(descriptor)
    supported, distance = _support(descriptors, fixed['support'], extra_radius=descriptor_radius)
    nominal = _nominal(coordinate)
    rows = []
    for task, model in zip(settings['tasks'], fixed['models'], strict=True):
        value = _predict(model, _response_features(descriptors[0], coordinate, force[:,task['action_index']]))
        point = None if value is None else float(value[0])
        lower = None if point is None or radius is None else point-radius
        upper = None if point is None or radius is None else point+radius
        available = point is not None and lower is not None and supported and nominal
        admitted = bool(available and radius <= settings['response_tolerance'] and lower >= settings['task_threshold'])
        rows.append({**task,'point':point,'lower':lower,'upper':upper,'radius':radius,
            'supported':bool(supported and nominal),'support_distance':distance,
            'admitted':admitted,'status': 'ADMITTED' if admitted else 'DECLINED',
            'decline_reasons': ([] if admitted else [name for flag,name in (
                (point is None,'RESPONSE_FIT_UNAVAILABLE'), (radius is None,'CALIBRATION_VACUOUS'),
                (not nominal,'TRANSFER_COORDINATE_OUTSIDE_FIXED_PACKAGE'),
                (not supported,'PREPARED_DESCRIPTION_OUTSIDE_FIXED_SUPPORT'),
                (radius is not None and radius>settings['response_tolerance'],'INTERVAL_TOO_WIDE'),
                (lower is not None and lower<settings['task_threshold'],'REQUESTED_SIGN_NOT_CERTIFIED')) if flag])})
    return rows


def capstone_preparation_commitment(config, seed, coordinate, arm, initial_descriptor, forces, package):
    """Commit U(z0,p), F(U(z0,p),a) and task choices before any preparation advance."""
    settings, seed = _settings(config), _seed(seed)
    initial = _vector(initial_descriptor, 24, 'initial descriptor')
    force = _forces(forces, config)
    if arm not in settings['arms']:
        raise ValueError('preparation arm is outside its authored assignment')
    package = _package(config, package, seed)
    predicted, tasks = None, []
    descriptor_radius = None
    if package is not None:
        model = package['upstream_models'][arm]
        value = _predict(model, _upstream_features(initial, coordinate))
        predicted = None if value is None else value.tolist()
        descriptor_radius = package['composition_calibration']['descriptor_radius']
        if predicted is not None:
            tasks = _prediction_records(config, coordinate, predicted, force,
                package['fixed_response_package'], package['composition_calibration']['response_radius'],
                descriptor_radius=math.inf if descriptor_radius is None else descriptor_radius)
    result = {'schema':PREPARATION_COMMITMENT_SCHEMA,'seed':seed,'coordinate':deepcopy(coordinate),'arm':arm,
        'config_sha256':_config_digest(config),'package_sha256':None if package is None else package['package_sha256'],
        'fixed_response_package_sha256':None if package is None else package['fixed_response_package']['package_sha256'],
        'initial_descriptor':initial.tolist(),'physical_forces_sha256':_digest(force.tolist()),
        'predicted_prepared_descriptor':predicted,'descriptor_radius':descriptor_radius,'tasks':tasks,
        'cutoff_tick':0,'information_schedule':'BEFORE_PREPARATION_NOISE_TAPE_GENERATION_OR_NATIVE_ADVANCE',
        'status':'COMMITTED' if predicted is not None else 'UNAVAILABLE',
        'scientific_connection':'FORECAST_PREPARED_24_DESCRIPTION_SUPPLIES_INPUT_TO_FIXED_RESPONSE_COEFFICIENTS'}
    result['commitment_sha256'] = _digest(result)
    return result


def capstone_response_commitment(config, seed, coordinate, arm, prepared_descriptor, forces, package):
    """Use observed prepared input with exactly the same F/support/CAL for every arm."""
    seed = _seed(seed)
    prepared = _descriptors(prepared_descriptor)
    force = _forces(forces, config)
    package = _package(config, package, seed)
    if arm not in _settings(config)['arms']:
        raise ValueError('response commitment uses an unassigned preparation arm')
    tasks = [] if package is None else _prediction_records(config, coordinate, prepared, force,
        package['fixed_response_package'], package['fixed_response_package']['calibration_radius'])
    result = {'schema':RESPONSE_COMMITMENT_SCHEMA,'seed':seed,'coordinate':deepcopy(coordinate),'arm':arm,
        'config_sha256':_config_digest(config),'package_sha256':None if package is None else package['package_sha256'],
        'fixed_response_package_sha256':None if package is None else package['fixed_response_package']['package_sha256'],
        'prepared_descriptors':prepared.tolist(),'physical_forces_sha256':_digest(force.tolist()),'tasks':tasks,
        'cutoff_tick':config['handoff_tick'],'information_schedule':'AFTER_PREPARATION_BEFORE_ANY_ASSAY_FUTURE_NOISE_OR_ADVANCE',
        'status':'COMMITTED' if package is not None else 'UNAVAILABLE',
        'scientific_connection':'PHYSICAL_PREPARATION_CHANGES_INPUT_SUPPORT_FOR_COMPLETELY_UNCHANGED_RESPONSE_PACKAGE'}
    result['commitment_sha256'] = _digest(result)
    return result


def capstone_case_summary(config, seed, case, receivers, forces):
    """Compact original descriptors and two fixed scalar assay channels, no model refit."""
    settings = _settings(config)
    seed = _seed(seed)
    force = _forces(forces, config)
    receiver = np.asarray(receivers, dtype=float)
    if receiver.shape != (48, 192) or not np.isfinite(receiver).all():
        raise ValueError('capstone requires the original physical 48-by-192 receiver')
    initial = case.get('preparation_initial_descriptor')
    if initial is not None:
        initial = _vector(initial, 24, 'initial descriptor').tolist()
    result = {'schema':SUMMARY_SCHEMA,'seed':seed,'coordinate':deepcopy(case['coordinate']),
        'arm':case['arm'],'status':'UNAVAILABLE','initial_descriptor':initial,
        'prepared_descriptors':None,'task_values':None,'task_forces':[force[:,t['action_index']].tolist() for t in settings['tasks']],
        'task_definitions':settings['tasks'],'numerical_policy_pass':None,
        'preparation_commitment':deepcopy(case.get('capstone_preparation_commitment')),
        'response_commitment':deepcopy(case.get('capstone_response_commitment'))}
    if case.get('status') != 'COMPLETED' or initial is None:
        result['reason'] = case.get('reason','INITIAL_DESCRIPTOR_OR_NATIVE_OUTCOME_UNAVAILABLE')
        return result
    states = np.asarray(case['origin_states'], dtype=float)
    if states.shape != (2, 192) or not np.isfinite(states).all():
        raise ValueError('capstone original states require both complete physical numerical views')
    prepared = (receiver[:24,:96]@states[:,:96].T).T
    values = [[] for _ in settings['tasks']]
    maximum_discrepancy = 0.
    dt = float(config['timestep'])
    times = dt*np.arange(1,config['horizon_ticks']+1)
    pulse = np.minimum(times,dt*config['pulse_ticks'])
    scales = np.stack((float(config['amplitude'])*pulse*(times-pulse/2),float(config['amplitude'])*pulse),axis=-1)
    if len(case['panels']) != config['panels']:
        raise ValueError('capstone summary cannot omit an assigned response panel')
    for panel in case['panels']:
        native = np.asarray(panel['native_response'],dtype=float)
        expected = (2,len(config['actions']),config['horizon_ticks']+1,48)
        if native.shape != expected or not np.isfinite(native).all():
            raise ValueError('capstone summary requires complete finite original native response arrays')
        discrepancy = (native[0,:,1:]-native[1,:,1:]).reshape(len(config['actions']),config['horizon_ticks'],2,24)
        normalized = np.linalg.norm(discrepancy,axis=-1)/scales[None]
        maximum_discrepancy = max(maximum_discrepancy,float(normalized.max()))
        for index,task in enumerate(settings['tasks']):
            block = 0 if task['block']=='POSITION' else 1
            scale = scales[settings['horizon_tick']-1,block]
            values[index].extend((native[:,task['action_index'],settings['horizon_tick'],task['receiver_index']]/scale).tolist())
    result.update(status='COMPLETED', prepared_descriptors=prepared.tolist(), task_values=values,
        numerical_policy_pass=bool(maximum_discrepancy<=float(config['numerical_tolerance'])),
        paired_view_discrepancy=maximum_discrepancy)
    return result


def _usable(case):
    return (case.get('status')=='COMPLETED' and case.get('numerical_policy_pass') is True
            and case.get('initial_descriptor') is not None and case.get('prepared_descriptors') is not None
            and case.get('task_values') is not None)


def _case_roster(config, summaries, seeds):
    expected = {(arm,row['id']) for arm in config['preparation_arms'] for row in config['coordinates']}
    collected = {}
    for seed in seeds:
        body = summaries.get(seed)
        cases = [] if body is None else body.get('capstone_cases',[])
        by_key = {}
        for case in cases:
            key = (case.get('arm'),case.get('coordinate',{}).get('id'))
            if case.get('schema') != SUMMARY_SCHEMA or case.get('seed') != seed or key not in expected or key in by_key:
                raise ValueError('capstone summary changes or duplicates its assigned root/case')
            by_key[key] = case
        # Missing cases retain missing score status; they are never dropped from CAL.
        collected[seed] = by_key
    return collected


def freeze_capstones(config, summaries_by_seed, training_seeds, calibration_seeds):
    """Fit F/U on TRAIN, calibrate complete roots on CAL, freeze both connections."""
    settings = _settings(config)
    train, cal = tuple(training_seeds), tuple(calibration_seeds)
    if not train or not cal or len(set(train))!=len(train) or len(set(cal))!=len(cal) or set(train)&set(cal):
        raise ValueError('capstone TRAIN/CAL rosters must be nonempty, unique and disjoint')
    for seed in (*train,*cal):
        _seed(seed)
    if not isinstance(summaries_by_seed, Mapping) or set(summaries_by_seed)-set(train)-set(cal):
        raise ValueError('capstone freeze cannot receive unassigned or CONF outcomes')
    cases = _case_roster(config,summaries_by_seed,(*train,*cal))
    nominal_ids = [row['id'] for row in config['coordinates'] if _nominal(row)]
    if len(nominal_ids) != 1:
        raise ValueError('capstone fit requires exactly one declared nominal coordinate')
    nominal = nominal_ids[0]
    baseline = [cases[seed].get(('baseline',nominal)) for seed in train]
    usable = [case for case in baseline if case is not None and _usable(case)]
    models = []
    for index in range(2):
        x = [_response_features(case['prepared_descriptors'][0],case['coordinate'],case['task_forces'][index]) for case in usable]
        # One primary-view panel-mean target per independent TRAIN root.
        y = [float(np.mean(case['task_values'][index][::2])) for case in usable]
        models.append(_fit(x,y,settings['ridge_penalty'],odd=True))
    support = None
    if usable:
        z = np.asarray([case['prepared_descriptors'][0] for case in usable])
        center = np.mean(z,axis=0)
        scale = np.std(z,axis=0)
        arithmetic_floor = 64*np.finfo(float).eps*np.maximum(1.,np.abs(center))
        scale = np.maximum(scale,arithmetic_floor)
        support = {'center':center.tolist(),'scale':scale.tolist(),'radius':settings['support_radius'],
            'source':'BASELINE_NOMINAL_TRAIN_ONLY; NUMERICAL_FLOOR_64EPS',
            'coordinate_id':nominal,'descriptor_dimension':24}
    fixed = {'schema':'classical-series-fixed-response-package.v1','models':models,'support':support,
        'tasks':settings['tasks'],'horizon_tick':settings['horizon_tick'],
        'threshold':settings['task_threshold'],'response_tolerance':settings['response_tolerance'],
        'training_assigned':len(train),'training_usable_roots':len(usable),
        'training_scope':'BASELINE_NOMINAL_ONLY','calibration_scope':'BASELINE_NOMINAL_COMPLETE_ROOT_MAX_OVER_TASK_PANEL_VIEW',
        'calibration_radius':None,'calibration_scores':[],'order_statistic':None,
        'scientific_object':'FIXED_COEFFICIENTS_PLUS_SUPPORT_PLUS_UNCERTAINTY_PLUS_TASKS',
        'response_feature_rule':'PHYSICAL_FORCE_TENSOR_DESCRIPTOR_AND_PARAMETER_CONTEXT; EXACTLY_ODD',
        'uncertainty_applicability':'BASELINE_NOMINAL_MARGINAL_CALIBRATION; OTHER_PREPARATIONS_TEST_THE_UNCHANGED_PACKAGE_HYPOTHESIS; SUPPORT_MEMBERSHIP_ALONE_DOES_NOT_TRANSFER_DISTRIBUTIONAL_COVERAGE'}
    scores = []
    for seed in cal:
        case = cases[seed].get(('baseline',nominal))
        score = None
        if case is not None and _usable(case) and all(model['status']=='FROZEN' for model in models):
            score = max(abs(float(value)-float(_predict(models[index],_response_features(
                case['prepared_descriptors'][0],case['coordinate'],case['task_forces'][index]))[0]))
                for index in range(2) for value in case['task_values'][index])
        scores.append(score)
        fixed['calibration_scores'].append({'seed':seed,'score':score})
    fixed['calibration_radius'],fixed['order_statistic'] = _radius(scores,settings['alpha'])
    fixed['package_sha256'] = _digest(fixed)
    upstream = {}
    for arm in settings['arms']:
        selected = [cases[seed].get((arm,nominal)) for seed in train]
        selected = [case for case in selected if case is not None and _usable(case)]
        upstream[arm] = _fit([_upstream_features(case['initial_descriptor'],case['coordinate']) for case in selected],
            [case['prepared_descriptors'][0] for case in selected],settings['ridge_penalty'])
    descriptor_scores,response_scores = [],[]
    for seed in cal:
        state_errors,output_errors = [],[]
        complete = support is not None
        for arm in settings['arms']:
            case = cases[seed].get((arm,nominal))
            if case is None or not _usable(case):
                complete = False
                continue
            predicted = _predict(upstream[arm],_upstream_features(case['initial_descriptor'],case['coordinate']))
            if predicted is None or any(model['status']!='FROZEN' for model in models):
                complete = False
                continue
            if support is not None:
                state_errors.append(float(np.max(np.abs(np.asarray(case['prepared_descriptors'])-predicted)/np.asarray(support['scale']))))
            for index in range(2):
                predicted_response = float(_predict(models[index],_response_features(predicted,case['coordinate'],case['task_forces'][index]))[0])
                output_errors.extend(abs(float(value)-predicted_response) for value in case['task_values'][index])
        descriptor_scores.append(max(state_errors) if complete and state_errors else None)
        response_scores.append(max(output_errors) if complete and output_errors else None)
    descriptor_radius,order = _radius(descriptor_scores,settings['alpha'])
    response_radius,_ = _radius(response_scores,settings['alpha'])
    # Development nomination uses TRAIN outcomes and support only. F and
    # its CAL uncertainty remain unchanged; CONF never selects a preparation.
    arm_distances = {}
    for arm in settings['arms']:
        values = []
        for seed in train:
            case = cases[seed].get((arm,nominal))
            if case is None or not _usable(case) or support is None:
                values = []
                break
            values.append(_support(case['prepared_descriptors'],support)[1])
        arm_distances[arm] = float(np.mean(values)) if values else None
    # Baseline/no action is a valid selection; lower distance alone cannot
    # justify an obligatory adverse preparation or an empty service region.
    service_rates={}
    for arm in settings['arms']:
        delivered=0
        for seed in train:
            case=cases[seed].get((arm,nominal))
            if case is None or not _usable(case):
                continue
            for index,model in enumerate(models):
                value=_predict(model,_response_features(case['prepared_descriptors'][0],case['coordinate'],case['task_forces'][index]))
                # Nomination uses TRAIN only. The development allowance is the
                # authored task tolerance, not a CAL-selected residual radius.
                radius=settings['response_tolerance']
                if value is not None and radius is not None:
                    point=float(value[0])
                    supported=_support(case['prepared_descriptors'],support)[0]
                    delivered+=bool(supported and radius<=settings['response_tolerance']
                        and point-radius>=settings['task_threshold']
                        and all(v>=settings['task_threshold'] and abs(v-point)<=radius for v in case['task_values'][index]))
        service_rates[arm]=delivered/(len(train)*len(settings['tasks']))
    candidates=[arm for arm in settings['arms'] if arm!='baseline'
        and arm_distances[arm] is not None and arm_distances.get('baseline') is not None
        and arm_distances[arm]<arm_distances['baseline']
        and service_rates[arm]>service_rates['baseline']]
    nominee=min(candidates,key=lambda arm:(-service_rates[arm],arm_distances[arm],arm)) if candidates else None
    feasibility={'fixed_response_region_nonempty':fixed['calibration_radius'] is not None
        and fixed['calibration_radius']<=settings['response_tolerance'] and support is not None,
        'composition_region_nonempty':descriptor_radius is not None and descriptor_radius<=settings['support_radius']
        and response_radius is not None and response_radius<=settings['response_tolerance'] and support is not None,
        'development_service_rates':service_rates,
        'development_service_definition':'TRAIN_NATIVE_TARGET_AND_TOLERANCE_WITHOUT_CAL_QUANTILE',
        'development_positive_control':any(value>0 for value in service_rates.values())}
    # A numerical support/radius check is necessary but not sufficient for a
    # nonempty signed-task region. Retain actual observed development witnesses
    # evaluated with the final frozen uncertainty, separately for U->F and F.
    fixed_witnesses,composition_witnesses=[],[]
    for seed in train:
        for arm in settings['arms']:
            case=cases[seed].get((arm,nominal))
            if case is None or not _usable(case):
                continue
            force=np.zeros((96,len(config['actions'])))
            for task,physical in zip(settings['tasks'],case['task_forces'],strict=True):
                force[:,task['action_index']]=physical
            tasks=_prediction_records(config,case['coordinate'],case['prepared_descriptors'],force,fixed,fixed['calibration_radius'])
            if all(t['admitted'] for t in tasks):
                fixed_witnesses.append({'seed':seed,'arm':arm})
            predicted=_predict(upstream[arm],_upstream_features(case['initial_descriptor'],case['coordinate']))
            if predicted is not None and descriptor_radius is not None:
                tasks=_prediction_records(config,case['coordinate'],predicted,force,fixed,response_radius,descriptor_radius=descriptor_radius)
                if all(t['admitted'] for t in tasks):
                    composition_witnesses.append({'seed':seed,'arm':arm})
    feasibility['fixed_radius_support_necessary_conditions']=feasibility['fixed_response_region_nonempty']
    feasibility['composition_radius_support_necessary_conditions']=feasibility['composition_region_nonempty']
    feasibility['fixed_response_region_nonempty']=bool(fixed_witnesses)
    feasibility['composition_region_nonempty']=bool(composition_witnesses)
    feasibility['fixed_development_witnesses']=fixed_witnesses
    feasibility['composition_development_witnesses']=composition_witnesses
    feasibility['development_positive_control']=bool(fixed_witnesses or composition_witnesses)
    feasibility['missing_witness_meaning']='UNRESOLVED_FEASIBILITY; NOT_A_PROOF_OF_MATHEMATICAL_EMPTINESS'
    package = {'schema':PACKAGE_SCHEMA,'config_sha256':_config_digest(config),
        'training_seeds':list(train),'calibration_seeds':list(cal),
        'fixed_response_package':fixed,'upstream_models':upstream,
        'composition_calibration':{'descriptor_radius':descriptor_radius,'response_radius':response_radius,
            'descriptor_scores':[{'seed':seed,'score':score} for seed,score in zip(cal,descriptor_scores,strict=True)],
            'response_scores':[{'seed':seed,'score':score} for seed,score in zip(cal,response_scores,strict=True)],
            'order_statistic':order,'assigned_roots':len(cal),
            'scope':'SEPARATE_COMPOSITION_CALIBRATION; COMPLETE_ROOT_MAX_OVER_ALL_ASSIGNED_PREPARATIONS_TASKS_PANELS_VIEWS',
            'marginal_alpha_each':settings['alpha'],
            'joint_coverage_lower_if_exchangeable':max(0.,1-2*settings['alpha']),
            'joint_coverage_rule':'UNION_BOUND_FOR_DESCRIPTOR_AND_RESPONSE; NOT_CONDITIONAL_ON_ADMISSION'},
        'preparation_nominee':nominee,'training_support_distances':arm_distances,
        'design_feasibility':feasibility,'training_service_rates':service_rates,
        'nomination_rule':'TRAIN_ONLY_USEFUL_SERVICE_GAIN_AND_STRICT_SUPPORT_IMPROVEMENT; BASELINE_OR_NONENTRY_ALLOWED',
        'qualification':'NOT_ESTABLISHED','historical_result_claim':False,
        'coverage_premises':'Exchangeable independent assigned roots under the same declared joint preparation/assay protocol; fixed-F calibration is baseline-nominal only; two composition calibrations each have marginal alpha; numerical views and panels are nested; missing CAL contributes infinite residual; no conditional-on-admission coverage claim'}
    package['package_sha256'] = _digest(package)
    return package


def _task_assessment(task, values, numerical, actual_supported, threshold):
    admitted = task['admitted']
    available = values is not None and numerical is True
    covered = None if not available or task['lower'] is None else bool(all(task['lower']<=v<=task['upper'] for v in values))
    satisfies = None if not available else bool(all(v>=threshold for v in values))
    delivered = None if admitted and not available else bool(admitted and satisfies and covered and actual_supported)
    return {**deepcopy(task),'native_values':values,'numerical_policy_pass':numerical,
        'actual_description_supported':actual_supported,'covered':covered,'requested_target_satisfied':satisfies,
        'delivered_service':delivered,'false_admission':None if admitted and not available else bool(admitted and not delivered),
        'unresolved_admitted_future':bool(admitted and not available)}


def _empty_tasks(settings):
    return [{**task,'point':None,'lower':None,'upper':None,'radius':None,'supported':False,'support_distance':None,
             'admitted':False,'status':'DECLINED','decline_reasons':['UPSTREAM_FIT_OR_PACKAGE_UNAVAILABLE']}
            for task in settings['tasks']]


def _stage_census(rows, settings):
    tasks = [task for row in rows for task in row['tasks']]
    return {'assigned_cases':len(rows),'assigned_task_requests':len(rows)*len(settings['tasks']),
        'admitted_requests':sum(task['admitted'] for task in tasks),
        'declined_requests':sum(not task['admitted'] for task in tasks),
        'delivered_requests':sum(task['delivered_service'] is True for task in tasks),
        'false_admissions':sum(task['false_admission'] is True for task in tasks),
        'unresolved_admitted_requests':sum(task['unresolved_admitted_future'] for task in tasks),
        'unavailable_future_requests':sum(task['numerical_policy_pass'] is not True for task in tasks),
        'nested_requests_are_independent_units':False,'independent_units':1}


def assess_capstones(config, acquired, package):
    """Assess the original commitments; no CONF fit, repair, admission or nomination."""
    settings = _settings(config)
    seed = _seed(acquired['seed'])
    package = _package(config, package, seed)
    summaries = [capstone_case_summary(config,seed,case,acquired['receivers'],acquired['forces']) for case in acquired['cases']]
    expected = {(arm,row['id']) for arm in settings['arms'] for row in config['coordinates']}
    if {(case['arm'],case['coordinate']['id']) for case in summaries} != expected or len(summaries)!=len(expected):
        raise ValueError('capstone assessment requires the complete assigned case census')
    fixed = None if package is None else package['fixed_response_package']
    forecast_rows,preparation_rows = [],[]
    for summary in summaries:
        pre, direct = summary['preparation_commitment'],summary['response_commitment']
        if package is not None and summary['initial_descriptor'] is not None:
            expected_pre = capstone_preparation_commitment(config,seed,summary['coordinate'],summary['arm'],
                summary['initial_descriptor'],acquired['forces'],package)
            if pre != expected_pre:
                raise ValueError('original before-preparation forecast commitment changed or is absent')
        if package is not None and summary['status']=='COMPLETED':
            expected_direct = capstone_response_commitment(config,seed,summary['coordinate'],summary['arm'],
                summary['prepared_descriptors'],acquired['forces'],package)
            if direct != expected_direct:
                raise ValueError('original before-assay fixed response commitment changed or is absent')
        supported = False if fixed is None or summary['prepared_descriptors'] is None else (
            _nominal(summary['coordinate']) and _support(summary['prepared_descriptors'],fixed['support'])[0])
        for commitment, rows in ((pre,forecast_rows),(direct,preparation_rows)):
            choices = _empty_tasks(settings) if not commitment or not commitment.get('tasks') else commitment['tasks']
            if len(choices)!=len(settings['tasks']):
                raise ValueError('committed task census differs from the fixed package')
            tasks = [_task_assessment(task,None if summary['task_values'] is None else summary['task_values'][i],
                summary['numerical_policy_pass'],supported,settings['task_threshold']) for i,task in enumerate(choices)]
            rows.append({'coordinate':summary['coordinate'],'arm':summary['arm'],'status':summary['status'],
                'tasks':tasks,'commitment_sha256':None if not commitment else commitment['commitment_sha256'],
                'fixed_response_package_sha256':None if fixed is None else fixed['package_sha256']})
    base = {'status':'ASSESSED_FROZEN_CONNECTION' if package is not None else 'PACKAGE_UNAVAILABLE',
        'seed':seed,'horizon_tick':settings['horizon_tick'],'fixed_response_package_sha256':None if fixed is None else fixed['package_sha256'],
        'coefficient_refits_on_confirmation':0,'historical_result_claim':False,'qualification':'NOT_ESTABLISHED',
        'native_work_avoided':0,'task_requirement':'SCALAR_RESPONSE_LOWER_BOUND_AT_LEAST_AUTHORED_THRESHOLD_WITH_INTERVAL_RADIUS_WITHIN_RESPONSE_TOLERANCE'}
    forecast = {**base,'scientific_connection':'FORECAST_PREPARED_DESCRIPTION_SUPPLIES_FIXED_F_INPUT',
        'prepared_state_observed_to_make_forecast':False,'cases':forecast_rows,
        'census':_stage_census(forecast_rows,settings),
        'composition_calibration_sha256':None if package is None else _digest(package['composition_calibration'])}
    nominee = None if package is None else package['preparation_nominee']
    comparisons = []
    for coordinate in config['coordinates']:
        pair = {row['arm']:row for row in preparation_rows if row['coordinate']['id']==coordinate['id']}
        baseline, candidate = pair['baseline'],pair.get(nominee)
        known = candidate is not None and all(task['delivered_service'] is not None and task['numerical_policy_pass'] is True
            for row in (baseline,candidate) for task in row['tasks'])
        before = sum(task['delivered_service'] is True for task in baseline['tasks'])
        after = None if candidate is None else sum(task['delivered_service'] is True for task in candidate['tasks'])
        comparisons.append({'coordinate':coordinate,'nominee':nominee,'baseline_delivered':before,
            'prepared_delivered':after,'gain':None if not known else after>before,
            'harm':None if not known else after<before,'complete_pair':known,
            'same_complete_package':candidate is None or candidate['fixed_response_package_sha256']==baseline['fixed_response_package_sha256']})
    preparation = {**base,'scientific_connection':'PHYSICAL_PREPARATION_EXTENDS_USE_OF_ENTIRE_UNCHANGED_PACKAGE',
        'cases':preparation_rows,'census':_stage_census(preparation_rows,settings),'nominee':nominee,
        'nomination_scope':'TRAIN_ONLY_SERVICE_AND_SUPPORT; BASELINE_OR_NONENTRY_ALLOWED; ALL_ASSIGNED_ARMS_RETAINED',
        'comparisons':comparisons,'same_response_coefficients_support_and_calibration':True}
    return {'forecast':forecast,'preparation':preparation}
