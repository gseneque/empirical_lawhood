# SPDX-License-Identifier: MPL-2.0
"""Whole-root selection and calibration of optional parameter-relation comparators.

This is an explicitly fitted supplier, separate from the model-free core.
CAL quantiles use a complete assigned-root maximum over the frozen parameter
frame; unseen parameter points inherit no coverage statement. No root fold is
split into independently treated parameter rows.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import numpy as np


def _features(row, kind, family):
    value=row['features'].get(kind)
    if value is None:
        return None
    x=np.asarray(value,dtype=float)
    if x.ndim!=1 or not np.isfinite(x).all():
        return None
    if family=='interactions':
        p=np.asarray(row['parameters'],dtype=float)
        x=np.concatenate((x,[p[0]*p[1],p[0]*p[2],p[1]*p[2]]))
    return x


def _fit(rows, kind, family, penalty):
    x=np.stack([_features(r,kind,family) for r in rows])
    y=np.log1p([r['target'] for r in rows])
    if x.shape[1]==0 or not np.allclose(x[:,0],1.,rtol=0.,atol=1e-12):
        raise ValueError('Parameter-relation features must start with the declared unit intercept')
    scale=np.maximum(np.sqrt(np.mean(x*x,axis=0)),1e-12)
    scaled=x/scale
    # Physical descriptors can be identically zero, constant, or redundant in a
    # preparation. Resolve that TRAIN-only column span explicitly; ridge alone
    # must not be presented as identifying coefficients of duplicate features.
    active=[]; dropped=[]; q=np.zeros((len(x),0))
    threshold=1e-10*math.sqrt(len(x))
    for index in range(scaled.shape[1]):
        value=scaled[:,index].copy()
        for _ in range(2):
            value-=q@(q.T@value)
        norm=float(np.linalg.norm(value))
        if norm>threshold:
            active.append(index)
            q=np.column_stack((q,value/norm))
        else:
            constant=np.ptp(x[:,index])<=1e-10*max(float(scale[index]),1e-12)
            dropped.append({'index':index,'reason':'CONSTANT_ON_TRAIN' if constant else 'LINEARLY_DEPENDENT_ON_TRAIN'})
    if not active:
        return None
    reduced=scaled[:,active]
    singular=np.linalg.svd(reduced,compute_uv=False)
    rank=int(np.sum(singular>1e-10*singular[0]))
    if rank<len(active):
        return None
    ridge=penalty*np.eye(len(active)); ridge[active.index(0),active.index(0)]=0.
    coefficient=np.linalg.solve(reduced.T@reduced+ridge,reduced.T@y)
    return {'coefficients':coefficient.tolist(),'scale':scale.tolist(),'rank':rank,
            'feature_count':scaled.shape[1],'active_feature_indices':active,
            'dropped_features':dropped,'singular_values':singular.tolist(),
            'feature_screening_scope':'TRAIN_ONLY_ORDERED_INDEPENDENT_COLUMN_SPAN; REPEATED_WITHIN_EACH_ROOT_FOLD',
            'family':family,'penalty':penalty}


def _log_prediction(row, kind, model):
    x=_features(row,kind,model['family'])
    if x is None or x.shape!=(len(model['scale']),):
        return None
    active=np.asarray(model['active_feature_indices'],dtype=int)
    value=float((x/np.asarray(model['scale']))[active]@np.asarray(model['coefficients']))
    return value if math.isfinite(value) else None


def fit_parameter_relations(rows, *, training_roots, calibration_roots, coordinate_ids,
                            ridge_candidates=(1e-6,1e-3,1.), folds=4, alpha=.05,
                            parameter_names=('log_temperature','log_friction','log_cross_coupling')):
    """Fit matched BR/SR relations with grouped CV and complete-root CAL scores.

    Rows contain root_id, coordinate_id, parameters (three log coordinates),
    features {'baseline':..., 'structure':...}, target (nonnegative loss).
    Incomplete TRAIN roots are explicitly listed and excluded identically from
    both fitted accounts. Every assigned CAL root remains in its quantile.
    """
    train,cal=tuple(training_roots),tuple(calibration_roots)
    ids=tuple(coordinate_ids)
    if not train or not cal or len(set(train))!=len(train) or len(set(cal))!=len(cal) or set(train)&set(cal):
        raise ValueError('TRAIN/CAL require disjoint nonempty independent-root identities')
    if not ids or len(set(ids))!=len(ids):
        raise ValueError('parameter frame must be unique and nonempty')
    if type(folds) is not int or folds<2 or not 0<alpha<1:
        raise ValueError('fold count and alpha outside their declared domains')
    penalties=tuple(float(v) for v in ridge_candidates)
    if not penalties or len(set(penalties))!=len(penalties) or any(not math.isfinite(v) or v<=0 for v in penalties):
        raise ValueError('ridge candidates must be distinct finite positive values')
    indexed={}
    parameter_frame={}
    for row in rows:
        key=(row['root_id'],row['coordinate_id'])
        if key in indexed or key[0] not in set(train)|set(cal) or key[1] not in ids:
            raise ValueError('relation row duplicated or outside assigned root/frame')
        p=np.asarray(row['parameters'],dtype=float)
        if p.shape!=(3,) or not np.isfinite(p).all():
            raise ValueError('relation requires three finite log parameters')
        if key[1] in parameter_frame and parameter_frame[key[1]]!=p.tolist():
            raise ValueError('Coordinate identity changes its physical parameters across roots')
        parameter_frame[key[1]]=p.tolist()
        indexed[key]=row
    def usable(row):
        return (row is not None and row.get('target') is not None
            and math.isfinite(float(row['target'])) and row['target']>=0
            and all(_features(row,k,'linear') is not None for k in ('baseline','structure')))
    complete=[root for root in train if all(usable(indexed.get((root,coord))) for coord in ids)]
    base={'schema':'grouped-parameter-relation.v1','training_roots':list(train),'calibration_roots':list(cal),
          'training_coordinates':list(ids),'matched_training_roots':complete,
          'excluded_training_roots':[root for root in train if root not in complete],
          'selection_scope':'WHOLE_ROOT_FOLDS_SHARED_ROWS_AND_CANDIDATE_BUDGET',
          'target_transform':'log1p(nonnegative receiver loss)','models':{},'parameter_names':list(parameter_names),
          'parameter_frame':parameter_frame,
          'coverage_scope':'COMPLETE_ROOT_MAXIMUM_ON_FROZEN_PARAMETER_FRAME_ONLY'}
    if len(complete)<2:
        return {**base,'status':'FIT_UNAVAILABLE','reason':'INSUFFICIENT_COMPLETE_TRAIN_ROOTS'}
    data=[indexed[(root,coord)] for root in complete for coord in ids]
    parameter_design=np.asarray([[1.,*r['parameters']] for r in data])
    parameter_rank=int(np.linalg.matrix_rank(parameter_design,tol=1e-10))
    base['parameter_design_rank']=parameter_rank
    if parameter_rank<4:
        return {**base,'status':'FIT_UNAVAILABLE','reason':'DECLARED_PARAMETER_EFFECTS_NOT_IDENTIFIABLE'}
    if np.ptp([r['target'] for r in data])<=1e-12:
        return {**base,'status':'FIT_UNAVAILABLE','reason':'NO_RESOLVED_TARGET_VARIATION'}
    fold_count=min(folds,len(complete))
    fold_map={root:index%fold_count for index,root in enumerate(sorted(complete))}
    base['fold_assignments']=[{'root_id':root,'fold':fold_map[root]} for root in sorted(complete)]
    menu=[(family,p) for family in ('linear','interactions') for p in penalties]
    base['candidates_per_account']=len(menu)
    for kind in ('baseline','structure'):
        evaluations=[]
        for family,penalty in menu:
            scores=[]; valid=True
            for fold in range(fold_count):
                fit_rows=[r for r in data if fold_map[r['root_id']]!=fold]
                model=_fit(fit_rows,kind,family,penalty)
                if model is None:
                    valid=False; break
                for root in complete:
                    if fold_map[root]!=fold:
                        continue
                    score=max(abs(math.log1p(indexed[(root,coord)]['target'])-_log_prediction(indexed[(root,coord)],kind,model)) for coord in ids)
                    scores.append(score)
            evaluations.append({'family':family,'penalty':penalty,'group_validation_score':float(np.mean(scores)) if valid and scores else None,
                                'status':'EVALUABLE' if valid and scores else 'UNIDENTIFIABLE_FOLD'})
        eligible=[x for x in evaluations if x['group_validation_score'] is not None]
        if not eligible:
            base['models'][kind]={'status':'FIT_UNAVAILABLE','reason':'NO_IDENTIFIABLE_CANDIDATE','candidate_evaluations':evaluations}
            continue
        selected=min(eligible,key=lambda x:(x['group_validation_score'],x['family'],x['penalty']))
        model=_fit(data,kind,selected['family'],selected['penalty'])
        scores=[]
        for root in cal:
            parts=[]
            for coord in ids:
                row=indexed.get((root,coord))
                value=_log_prediction(row,kind,model) if usable(row) else None
                parts.append(None if value is None else abs(math.log1p(row['target'])-value))
            scores.append(None if any(v is None for v in parts) else max(parts))
        order=math.ceil((len(cal)+1)*(1-alpha))
        ordered=sorted(math.inf if score is None else score for score in scores)
        radius=math.inf if order>len(ordered) else ordered[order-1]
        base['models'][kind]={'status':'FROZEN',**model,'calibration_radius':radius if math.isfinite(radius) else None,
            'calibration_scores':[{'root_id':root,'score':score} for root,score in zip(cal,scores,strict=True)],
            'order_statistic':order,'calibration_assigned':len(cal),'candidate_evaluations':evaluations,
            'selected_group_validation_score':selected['group_validation_score']}
    base['status']='FROZEN' if any(m['status']=='FROZEN' for m in base['models'].values()) else 'FIT_UNAVAILABLE'
    base['package_sha256']=sha256(json.dumps(base,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return base


def predict_parameter_relations(package, *, root_id, coordinate_id, parameters, features, tolerance):
    if root_id in set(package['training_roots'])|set(package['calibration_roots']):
        raise ValueError('CONF forecast cannot reuse a fitted or calibrated root')
    tolerance=float(tolerance)
    if not math.isfinite(tolerance) or tolerance<=0:
        raise ValueError('receiver tolerance must be finite and positive')
    p=np.asarray(parameters,dtype=float)
    if p.shape!=(3,) or not np.isfinite(p).all():
        raise ValueError('Prediction requires three finite physical log parameters')
    if coordinate_id in package.get('parameter_frame',{}) and package['parameter_frame'][coordinate_id]!=p.tolist():
        raise ValueError('Forecast substitutes the declared physical parameter coordinate')
    if package.get('package_sha256') is not None:
        body={k:v for k,v in package.items() if k!='package_sha256'}
        if sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()!=package['package_sha256']:
            raise ValueError('Frozen relation package bytes changed')
    row={'parameters':p.tolist(),'features':features}
    output={}
    for kind in ('baseline','structure'):
        model=package.get('models',{}).get(kind,{})
        logvalue=_log_prediction(row,kind,model) if model.get('status')=='FROZEN' else None
        radius=model.get('calibration_radius')
        point=None if logvalue is None or logvalue>700 else math.expm1(max(0.,logvalue))
        upper=None if logvalue is None or radius is None or logvalue+radius>700 else math.expm1(max(0.,logvalue+radius))
        output[kind]={'status':'FINITE' if upper is not None else 'UNRESOLVED','point':point,'upper':upper,
            'admitted':upper is not None and upper<=tolerance,
            'transfer_coordinate':coordinate_id not in package['training_coordinates'],
            'coverage_inherited':coordinate_id in package['training_coordinates'] and upper is not None,
            'target_scope':'FROZEN_PARAMETER_RELATION_SAME_RECEIVER_LOSS'}
    return output
