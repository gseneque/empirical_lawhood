"""Raw-state operator/eigenpair and retained factor checks without eigensolves.

No history/scalar/factor producer, native marcher or RNG is called. The full
15-dimensional spectral witness is checked against literal matrix products;
retained subspace geometry alone does not establish this source join.
"""

from decimal import Decimal

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import validate_diagnostics
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import independent_scalar_closure_ratio
from empirical_lawhood.adapters.methods.matrix_history_analysis.algebra import BASIS
from empirical_lawhood.adapters.methods.matrix_parameter_history.science import consume_arrays

from .records import DIAGNOSTICS, METHODS, VIEWS, MatrixParameterFactorAssessment, MatrixParameterFactorControl, identity, prefix


def raw_operator(triplet):
    """Literal positive commutator Gram in the exact original real HS basis."""
    commutators = [[z@b-b@z for b in BASIS] for z in triplet]
    value = np.zeros((15,15),dtype='<f8')
    if commutators:
        rows = np.asarray(commutators).reshape(len(commutators),15,16)
        # Each gufunc cell retains the original vdot contraction. Add the
        # triplet's real components in order, without a reassociated Gram GEMM.
        dots = np.vecdot(rows[:,:,None,:],rows[:,None,:,:]).real.astype('<f8')
        for row in dots:
            value += row
    return (value+value.T)/2


def _control(name, errors, tolerance, dimension, applicable=None):
    measured = tuple(None if x is None else Decimal(str(float(x))) for x in errors)
    applicability = tuple(True for _ in measured) if applicable is None else tuple(applicable)
    active = tuple(x for x,a in zip(measured,applicability,strict=True) if a)
    disposition = ('VIOLATED' if any(x is not None and x>tolerance for x in active)
        else 'UNASSESSED' if any(x is None for x in active) else 'SATISFIED' if active else 'NOT_APPLICABLE')
    return MatrixParameterFactorControl(name,measured,tolerance,dimension,disposition,applicability)


def pauli_residual(factor):
    """Literal oriented multiplicity-two Pauli products; no spectral calls."""
    errors = [np.linalg.norm(f@f-np.eye(4)/4) for f in factor]
    for i,j,k in ((0,1,2),(1,2,0),(2,0,1)):
        errors.append(np.linalg.norm(factor[i]@factor[j]+factor[j]@factor[i]))
        errors.append(np.linalg.norm(factor[i]@factor[j]-factor[j]@factor[i]-1j*factor[k]))
    return float(max(errors))


def assess_values(*, rule, design, source_state, scalars, traces, arrays, native):
    """Independent raw-state checks; no producer/eigensolve/native/RNG call."""
    errors = {method:[] for method in METHODS}
    pauli_applicable = []
    samples = {(s.view,s.sector,s.tick):s for s in scalars}
    traces = {(t.view,t.sector):t for t in traces}
    for view in VIEWS:
        multiplier = 1 if view=='PRIMARY' else 2
        for sector in rule.sectors:
            base = prefix(view,sector)
            diag = {name:arrays[base+name] for name in DIAGNOSTICS}
            if not np.array_equal(diag['ticks'],rule.lattice):
                raise ValueError('parameter witness substitutes actual coordinate observation clock')
            if native is not None:
                validate_diagnostics(diag,traces[view,sector],rule)
            elif (diag['available'].any() or diag['identifiable'].any()
                    or any(not np.isnan(arrays[base+k]).all() for k in ('spectrum','projector','basis','factor','aligned_factor','operator','eigenvectors'))):
                raise ValueError('unavailable parameter source manufactures spectral/frame operands')
            for i,tick in enumerate(rule.lattice):
                observation = None if native is None else traces[view,sector].observations[i]
                sample = samples[view,sector,tick]
                if native is None:
                    if sample.ratio is not None or sample.reason!='SOURCE_'+source_state:
                        raise ValueError('unavailable scalar source manufactures a measurement')
                    ratio = None
                else:
                    index = multiplier*tick
                    fields = native[view.lower()+'_positions'][index,('X','Y').index(sector)]
                    alpha = native[view.lower()+'_alpha_tilde'][index,('X','Y').index(sector)]
                    try:
                        ratio = independent_scalar_closure_ratio(fields,alpha)
                    except ValueError:
                        ratio = None
                    if (ratio is None)!=(sample.ratio is None) or (ratio is None and sample.reason!='SCALAR_NUMERICALLY_UNRESOLVED'):
                        raise ValueError('parameter scalar loses independent numerical missingness')
                    if observation.scalar_closure_ratio!=sample.ratio:
                        raise ValueError('parameter scalar trace substitutes its independently selected observation')
                errors['scalar-contrast'].append(None if ratio is None else abs(float(ratio-sample.ratio)))
                available = bool(diag['available'][i])
                identified = bool(diag['identifiable'][i])
                # A known unidentifiable sector has no supplied factor to
                # assess. Unknown/unavailable sources remain unassessed,
                # rather than becoming a not-applicable pass.
                pauli_applicable.append(not available or identified)
                errors['pauli-factor'].append(pauli_residual(diag['factor'][i]) if identified else None)
                if not available:
                    if (not np.isnan(arrays[base+'operator'][i]).all()
                            or not np.isnan(arrays[base+'eigenvectors'][i]).all()):
                        raise ValueError('unavailable factor witness invents source eigenpairs')
                    for name in ('raw-operator','eigenvector-orthogonality','slow-projector'):
                        errors[name].append(None)
                    errors['all-eigenpairs'].extend([None]*15)
                    continue
                op, vectors, spectrum = arrays[base+'operator'][i],arrays[base+'eigenvectors'][i],diag['spectrum'][i]
                if (not np.isfinite(op).all() or not np.isfinite(vectors).all() or not np.isfinite(spectrum).all()
                        or np.any(np.diff(spectrum)<0)):
                    raise ValueError('parameter witness omits finite ordered complete15 eigenpairs')
                independently_formed = raw_operator(fields)
                errors['raw-operator'].append(np.linalg.norm(op-independently_formed))
                # Checking all columns against the raw operator prevents a
                # mutually forged stored operator/spectrum from passing.
                residuals = independently_formed@vectors-vectors*spectrum[None,:]
                errors['all-eigenpairs'].extend(np.linalg.norm(residuals,axis=0))
                errors['eigenvector-orthogonality'].append(np.linalg.norm(vectors.T@vectors-np.eye(15)))
                errors['slow-projector'].append(np.linalg.norm(diag['projector'][i]-vectors[:,:3]@vectors[:,:3].T))
    tolerances = (design.operator_tolerance,design.eigenpair_tolerance,design.orthogonality_tolerance,design.projector_tolerance,design.factor_tolerance,design.scalar_tolerance)
    controls = tuple(_control(name,errors[name],tol,dimension,pauli_applicable if name=='pauli-factor' else None)
        for name,tol,dimension in zip(METHODS,tolerances,(225,15,225,225,48,1),strict=True))
    n = 2*len(rule.sectors)*len(rule.lattice)
    if tuple(len(c.measured_errors) for c in controls)!=(n,15*n,n,n,n,n):
        raise ValueError('independent factor controls thin full view/sector/tick/eigenpair denominator')
    return controls


def assess(source, parameter, supply, rule, contrast, definition, design, provenance, product, native_raw, diagnostic_raw):
    from .science import consume_diagnostics, validate_product
    source.validate_operands(parameter,supply,rule,contrast,definition,design,provenance)
    validate_product(source,parameter,supply,rule,product)
    arrays = consume_diagnostics(source,rule,product,diagnostic_raw)
    if (native_raw is not None)!=(supply.state=='COMPLETED'):
        raise ValueError('independent factor assessment changes source/raw availability')
    native = None if native_raw is None else consume_arrays(parameter,supply.product.arrays,native_raw)
    controls = assess_values(rule=rule,design=design,source_state=supply.state,
        scalars=product.scalars,traces=product.traces,arrays=arrays,native=native)
    return MatrixParameterFactorAssessment('assessment.'+source.source_id,identity(source),identity(product),identity(design),
        controls,all(c.disposition in ('SATISFIED','NOT_APPLICABLE') for c in controls))


def read_retained(source, parameter, supply, rule, contrast, definition, design, provenance, product, assessment, native_raw, diagnostic_raw):
    observed = assess(source,parameter,supply,rule,contrast,definition,design,provenance,product,native_raw,diagnostic_raw)
    if observed!=assessment:
        raise ValueError('parameter factor retained independent assessment changes original measured controls')
    return observed
