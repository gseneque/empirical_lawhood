# SPDX-License-Identifier: MPL-2.0
"""Independent ordered-series diagnostics; frames and eight sites are nested.

The source exclusion and a declared effective-sample heuristic identify an
analysis window. Finite block precision and half-window agreement are assessed;
this is not a proof of equilibrium or transport to biochemical rates.
"""

from decimal import Decimal
import math

from . import contracts as c


def statistical_inefficiency(values):
    import numpy as np
    data=np.asarray(values,dtype=float)
    if data.ndim!=1 or len(data)<2 or not np.isfinite(data).all():
        raise ValueError("ordered scalar series is absent, nonfinite or non-scalar")
    centered=data-data.mean()
    variance=float(centered@centered/len(data))
    if variance==0:
        return None
    length=1 << (2*len(data)-1).bit_length()
    transform=np.fft.rfft(centered,n=length)
    cov=np.fft.irfft(transform*transform.conjugate(),n=length)[:len(data)]
    cov=cov/(len(data)-np.arange(len(data)))
    rho=cov/variance
    # Positive paired sequence avoids adding a noisy negative tail. The
    # complete source series remains retained and accessible for reanalysis.
    total=0.0
    for index in range(1,len(data)-1,2):
        pair=float(rho[index]+rho[index+1])
        if pair<=0:
            break
        total+=pair
    return max(1.0,1.0+2.0*total)


def _metric(values, correlation):
    import numpy as np
    data=np.asarray(values,dtype=float)
    if correlation:
        if data.ndim!=2 or data.shape[1]!=2:
            raise ValueError("correlation omits joint interface/active receivers")
        if np.std(data[:,0])==0 or np.std(data[:,1])==0:
            return None
        return float(np.corrcoef(data[:,0],data[:,1])[0,1])
    if data.ndim!=1:
        raise ValueError("scalar metric changes nested-site reduction")
    return float(data.mean())


def diagnose_series(trajectory_id,metric_id,values,times_picosecond,*,
                    source_exclusion_picosecond=Decimal(50000),alpha=0.05/24):
    import numpy as np
    from scipy.stats import t
    data=np.asarray(values,dtype=float)
    clocks=np.asarray(times_picosecond,dtype=float)
    target=dict(c.PRECISION)[metric_id]
    correlation=metric_id=="interface-active-correlation"
    expected_dimensions=2 if correlation else 1
    if data.ndim!=expected_dimensions or len(data)!=len(clocks) or len(clocks)<2 or not np.isfinite(data).all() or not np.isfinite(clocks).all() or not np.all(np.diff(clocks)>0):
        raise ValueError("scalar diagnostic loses ordered complete native receivers")
    start=int(np.searchsorted(clocks,float(source_exclusion_picosecond),side="left"))
    best=None
    # Evaluate physical1ns analysis starts, rather than a hardware/time cutoff.
    candidates=np.unique(np.searchsorted(clocks,np.arange(float(source_exclusion_picosecond),clocks[-1],1000.0)))
    for offset in candidates:
        tail=data[offset:]
        if len(tail)<2:
            continue
        series=(tail[:,0],tail[:,1]) if correlation else (tail,)
        estimates=tuple(statistical_inefficiency(row) for row in series)
        if any(row is None for row in estimates):
            continue
        g=max(estimates)
        score=len(tail)/g
        if best is None or score>best[0]:
            best=(score,int(offset),g)
    reason=[]
    if best is None:
        return c.ScalarDiagnostic(trajectory_id,metric_id,max(0,len(data)-start),start,None,None,None,None,None,target,False,("NO_IDENTIFIED_VARIABILITY_OR_ANALYSIS_WINDOW",))
    effective,offset,g=best
    tail=data[offset:]
    width=max(1,int(math.ceil(5*g)))
    count=len(tail)//width
    mean=_metric(tail,correlation)
    if mean is None or count<4:
        return c.ScalarDiagnostic(trajectory_id,metric_id,len(tail),offset,Decimal(str(g)),Decimal(str(effective)),None if mean is None else Decimal(str(mean)),None,None,target,False,("FEWER_THAN_TWO_VARIANCE_BLOCKS_PER_HALF",))
    # No tail frames are discarded from the estimate. np.array_split includes
    # the remainder in the final block, avoiding a selected favorable tail.
    blocks=np.array_split(tail,count)
    estimates=[_metric(block,correlation) for block in blocks]
    if any(value is None for value in estimates):
        return c.ScalarDiagnostic(trajectory_id,metric_id,len(tail),offset,Decimal(str(g)),Decimal(str(effective)),Decimal(str(mean)),None,None,target,False,("BLOCK_CORRELATION_NOT_IDENTIFIABLE",))
    half=len(tail)//2
    half_metrics=(_metric(tail[:half],correlation),_metric(tail[half:],correlation))
    if any(value is None for value in half_metrics):
        return c.ScalarDiagnostic(trajectory_id,metric_id,len(tail),offset,Decimal(str(g)),Decimal(str(effective)),Decimal(str(mean)),None,None,target,False,("HALF_WINDOW_CORRELATION_NOT_IDENTIFIABLE",))
    drift=abs(half_metrics[0]-half_metrics[1])
    if correlation:
        if any(abs(value)>=1 for value in estimates) or abs(mean)>=1:
            reason.append("SINGULAR_FISHER_CORRELATION")
            halfwidth=None
        else:
            transformed=np.arctanh(estimates)
            margin=float(t.ppf(1-alpha/2,count-1))*float(np.std(transformed,ddof=1))/math.sqrt(count)
            center=float(np.arctanh(mean))
            halfwidth=max(mean-math.tanh(center-margin),math.tanh(center+margin)-mean)
    else:
        halfwidth=float(t.ppf(1-alpha/2,count-1))*float(np.std(estimates,ddof=1))/math.sqrt(count)
    if halfwidth is not None and halfwidth>float(target):
        reason.append("FINITE_BLOCK_PRECISION_TARGET_UNRESOLVED")
    if drift>float(target):
        reason.append("HALF_WINDOW_DRIFT_EXCEEDS_PRECISION_TARGET")
    return c.ScalarDiagnostic(trajectory_id,metric_id,len(tail),offset,Decimal(str(g)),Decimal(str(effective)),Decimal(str(mean)),None if halfwidth is None else Decimal(str(halfwidth)),Decimal(str(drift)),target,not reason,tuple(reason))


def cadence_agreement(fine_values,fine_times,metric_id):
    """Compare retained5ps receivers with their matched10ps coarsening."""
    import numpy as np
    fine=np.asarray(fine_values,dtype=float)
    clocks=np.asarray(fine_times,dtype=float)
    if len(clocks)!=len(fine) or len(clocks)<2 or not np.allclose(np.diff(clocks),5,rtol=0,atol=1e-7):
        raise ValueError("cadence refinement omits actual matched5ps native observations")
    correlation=metric_id=="interface-active-correlation"
    left,right=_metric(fine,correlation),_metric(fine[1::2],correlation)
    if left is None or right is None:
        return None
    difference=Decimal(str(abs(left-right)))
    return difference,difference<=dict(c.PRECISION)[metric_id]
