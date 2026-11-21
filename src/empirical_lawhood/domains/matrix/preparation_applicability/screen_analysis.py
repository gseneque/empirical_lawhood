# SPDX-License-Identifier: MPL-2.0
"""Scientific D32/E64 roles and whole-root development screens.

These reductions use authenticated operands supplied by the caller. They perform
no artifact authentication, file export, discovery or scientific acquisition.
"""

import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.preparation_applicability.measurement import reduce_panel, validity, service, requests
from empirical_lawhood.domains.matrix.preparation_applicability.root_measurement import measure_root
from empirical_lawhood.domains.matrix.preparation_applicability.readout import report
from empirical_lawhood.domains.matrix.preparation_applicability.headroom import opportunity, prefix_forecast
from empirical_lawhood.domains.matrix.preparation_applicability.config import preparation_run_id


def reduce_ordinary_panels(stage, original_f, panels):
    """Reduce every assigned native panel, retaining its independent-root meaning."""
    if tuple(value.prefix.root_id for value in panels)!=stage.root_ids:
        raise ValueError("ordinary panel export changes its complete assigned independent-root roster")
    if stage.upstream[0].artifact.sha256!=original_f.fingerprint():
        raise ValueError("ordinary panels substitute the original unchanged current F wrapper")
    arrays={"prefix":[],"handoff":[],"maxima":[],"work":[]}
    if stage.phase=="E":
        arrays["success"]=[]
    measured=[]
    for index,value in enumerate(panels):
        allocation=stage.allocation.roots[index]
        if (any(phase.allocation!=allocation or phase.source_sha256!=stage.source.object_fingerprint for phase in (*value.prefix.phases,*value.panel.phases))
            or any(receipt.run_id!=preparation_run_id(stage) for receipt in value.receipts)):
            raise ValueError("ordinary panel substitutes its actual source/allocation/run")
        reduced=reduce_panel(value.prefix,value.panel)
        if reduced is None:
            raise ValueError("UNEVALUABLE: ordinary screen retains an incomplete assigned panel; inspect its receipts")
        z,y,work=reduced
        row=measure_root(value.prefix,value.panel,original_f,stage.phase,allocation.seed_for("requests"),value.seal)
        if row!=value.measurement:
            raise ValueError("ordinary screen substitutes its independent readout")
        measured.append(row)
        maxima,_,_,mean,width,support=validity(original_f,z,y,work)
        arrays["prefix"].append(np.asarray(value.prefix.features,dtype=float).T)
        arrays["handoff"].append(z); arrays["maxima"].append(maxima); arrays["work"].append(work)
        if stage.phase=="E":
            arrays["success"].append(service(mean,width,support,y,work,*requests(allocation.seed_for("requests")))[1])
    summary=report(stage,tuple(measured))
    return {name: np.stack(rows) for name, rows in arrays.items()}, summary


def validate_screen_input(manifest, allocation, arrays, stage, summary, count, phase, original_f):
    """Refuse substituted populations, source roles and complete service censuses."""
    if (manifest.original_f!=original_f.identity or len(allocation.roots)!=count
        or stage.phase!=phase or stage.allocation!=allocation or summary.phase!=phase
        or not summary.complete or summary.root_ids!=stage.root_ids
        or summary.allocation_sha256!=allocation.fingerprint()
        or summary.source_sha256!=stage.source.object_fingerprint
        or summary.lower_sha256!=original_f.fingerprint()
        or ObjectIdentity.from_record(stage.config_id,stage) not in manifest.producers
        or ObjectIdentity.from_record(f"{stage.config_id}.report",summary) not in manifest.producers
        or any(root.cohort!="q2" for root in allocation.roots)
        or arrays["prefix"].shape!=(count,24,2) or arrays["handoff"].shape!=(count,3,24,2)
        or arrays["maxima"].shape!=(count,3,7) or arrays["work"].shape!=(count,3,2)
        or set(arrays)!={"prefix","handoff","maxima","work",*(('success',) if phase=='E' else ())}
        or not np.array_equal(np.asarray(summary.handoff,dtype=float).reshape(count,3,24,2),arrays["handoff"])
        or summary.full_valid_counts!=tuple(map(int,(arrays["maxima"]<=1).all(axis=2).sum(axis=0)))
        or summary.support_counts!=tuple(map(int,(arrays["maxima"][:,:,0]<=1).sum(axis=0)))):
        raise ValueError("ordinary screen changes D32/E64 roles, source or full panel census")
    if phase=="E":
        success=arrays["success"]
        if success.shape!=(64,3,256,2) or success.dtype!=np.bool_:
            raise ValueError("ordinary evaluation changes its complete paired request census")
        joint=success.all(axis=3).sum(axis=2)
        if (summary.joint_counts!=tuple(map(int,joint.sum(axis=0)))
            or summary.covered_counts!=tuple(map(int,(joint*(arrays["maxima"]<=1).all(axis=2)).sum(axis=0)))):
            raise ValueError("ordinary screen changes its actual joint/covered service counts")


def ordinary_screen_analysis(retained, original_f):
    """Finite-menu headroom and leave-one-root-out support-face prediction."""
    development,evaluation=retained
    if set(root.root_id for root in development[1].roots)&set(root.root_id for root in evaluation[1].roots):
        raise ValueError("ordinary D/E screens repeat independent roots")
    from empirical_lawhood.domains.matrix.preparation_applicability.exposure import effective_seed_ids
    if set(effective_seed_ids(development[1]))&set(effective_seed_ids(evaluation[1])):
        raise ValueError("ordinary D/E screens repeat effective source streams")
    d,e=development[2],evaluation[2]
    face=float(original_f.center[17]+6*original_f.scale[17])
    prefix=np.concatenate((d["prefix"][...,0],e["prefix"][...,0]))
    handoff=np.concatenate((d["handoff"][:,0,17,0],e["handoff"][:,0,17,0]))
    result={"ordinary_independent_roots":96,"development_roots":32,"evaluation_roots":64,
        "original_f_sha256":original_f.fingerprint(),"support_screen":{
            "development_support_counts":(d["maxima"][:,:,0]<=1).sum(axis=0).tolist(),
            "evaluation_support_counts":(e["maxima"][:,:,0]<=1).sum(axis=0).tolist()},
        "headroom":opportunity(e["maxima"],e["success"]),
        "causal_prefix_forecast":prefix_forecast(prefix,handoff,face),
        "input_manifest_sha256s":[value[0].fingerprint() for value in retained],
        "ceiling":"EXPOSED_DEVELOPMENT_NONPROMOTABLE","follow_on_status":"UNENTERED"}
    return result
