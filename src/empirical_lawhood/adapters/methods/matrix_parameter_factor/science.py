"""Parameter-source scoring using the unchanged factor algebra and tracking."""

from dataclasses import replace
from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorRootRole, FactorTrace
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import measure_trace_values, validate_trace
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_parameter_history import science as history_science
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity

from . import scalar
from .records import (
    DIAGNOSTICS, VIEWS, MatrixParameterFactorArrays, MatrixParameterFactorProduct,
    expected_members, identity, prefix,
    allocation_scopes,
)


def _empty(rule):
    arrays = {}
    for name,(dtype,shape) in expected_members(rule).items():
        if name.endswith('_ticks'):
            value = np.asarray(rule.lattice,dtype=dtype)
        elif dtype=='|b1':
            value = np.zeros(shape,dtype=dtype)
        else:
            value = np.full(shape,np.nan,dtype=dtype)
        arrays[name] = value
    return arrays


def original_arrays(parameter, supply, raw):
    supply.validate_source(parameter)
    if (supply.state=='COMPLETED') != (raw is not None):
        raise ValueError('parameter factor raw availability differs from known original supply')
    return None if raw is None else history_science.consume_arrays(parameter,supply.product.arrays,raw)


def measure_values(*, root, rule, native, samples, trace_factory=FactorTrace):
    """Shared numerical values; the caller owns its exact source/trace contract."""
    arrays, traces = _empty(rule), []
    if native is not None:
        for view in VIEWS:
            multiplier = 1 if view=='PRIMARY' else 2
            for sector in rule.sectors:
                ratios = {s.tick:s.ratio for s in samples if (s.view,s.sector)==(view,sector)}
                values, diagnostics = measure_trace_values(rule,view,sector,native[view.lower()+'_positions'],scalar_closure=ratios)
                trace = trace_factory(root,rule.identity,view,sector,*values,None)
                base = prefix(view,sector)
                for name in DIAGNOSTICS:
                    arrays[base+name] = diagnostics[name]
                for i,tick in enumerate(rule.lattice):
                    if diagnostics['available'][i]:
                        fields = native[view.lower()+'_positions'][multiplier*tick,('X','Y').index(sector)]
                        operator = algebra.operator(fields)
                        values, vectors = np.linalg.eigh(operator)
                        if not np.allclose(values,diagnostics['spectrum'][i],atol=0,rtol=0):
                            raise ValueError('parameter spectral witness differs from measured complete spectrum')
                        arrays[base+'operator'][i] = operator
                        arrays[base+'eigenvectors'][i] = vectors
                traces.append(trace)
    return arrays, tuple(traces)


def measure(source, parameter, supply, rule, contrast, definition, design, provenance, raw, *, artifact_id):
    source.validate_operands(parameter,supply,rule,contrast,definition,design,provenance)
    native = original_arrays(parameter,supply,raw)
    samples = scalar.measure(parameter,supply,rule,native)
    root = (None if native is None else FactorRootRole(source.root_id,source.independent_group_id,parameter.coordinate.family_id,
        source.parameter_source,supply.product.arrays.array_artifact,supply.product_artifact))
    arrays, traces = measure_values(root=root,rule=rule,native=native,samples=samples)
    nonfinite = tuple(n for n in arrays if not n.endswith(('_ticks','_available','_identifiable')))
    encoded, members = encode_matrix_arrays(arrays,nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id,'parameter-factor-diagnostics',MATRIX_ARRAY_SCHEMA,
        sha256(encoded).hexdigest(),'application/x-npz',len(encoded))
    operand = MatrixParameterFactorArrays('arrays.'+source.source_id,identity(source),artifact,members,
        tuple(sorted((identity(source),identity(supply)),key=lambda x:x.object_id)))
    # Each trace binds the complete newly produced archive, whose prefixes and
    # full witness have their own new source/member contract. No old reader or
    # historical FactorPopulationResult is used for this bundle.
    traces = tuple(replace(t,diagnostics=artifact,diagnostic_members=members) for t in traces)
    product = MatrixParameterFactorProduct('product.'+source.source_id,identity(source),source.root_id,
        source.independent_group_id,source.coordinate,source.clock_id,supply.state,
        None if supply.assessment is None else supply.assessment.numerical_pass,2*len(rule.sectors),len(rule.lattice),
        traces,samples,operand)
    validate_product(source,parameter,supply,rule,product)
    return encoded,product


def validate_product(source, parameter, supply, rule, product):
    if (product.source!=identity(source) or product.source_state!=supply.state
            or (product.root_id,product.independent_group_id,product.coordinate,product.clock_id)!=
               (source.root_id,source.independent_group_id,source.coordinate,source.clock_id)
            or product.history_numerical_pass!=(None if supply.assessment is None else supply.assessment.numerical_pass)
            or (product.requested_traces,product.requested_observations)!=(2*len(rule.sectors),len(rule.lattice))
            or {(m.name,m.dtype,m.shape) for m in product.arrays.members}!=
               {(n,d,s) for n,(d,s) in expected_members(rule).items()}
            or product.arrays.producers!=tuple(sorted((identity(source),identity(supply)),key=lambda x:x.object_id))
            or tuple((s.view,s.sector,s.tick) for s in product.scalars)!=
               tuple((v,s,t) for v in VIEWS for s in rule.sectors for t in rule.lattice)):
        raise ValueError('parameter factor product substitutes complete source/coordinate/view/sector census')
    if supply.state=='COMPLETED':
        if tuple((t.view,t.sector) for t in product.traces)!=tuple((v,s) for v in VIEWS for s in rule.sectors):
            raise ValueError('parameter factor product omits a nested view/sector')
        expected_root = FactorRootRole(source.root_id,source.independent_group_id,parameter.coordinate.family_id,
            source.parameter_source,supply.product.arrays.array_artifact,supply.product_artifact)
        for trace in product.traces:
            if (trace.root!=expected_root or trace.diagnostics!=product.arrays.array_artifact
                    or trace.diagnostic_members!=product.arrays.members):
                raise ValueError('parameter factor trace changes actual original source/product/arrays')
            validate_trace(trace,rule)


def consume_diagnostics(source, rule, product, raw):
    if product.arrays.source!=identity(source):
        raise ValueError('parameter factor diagnostics substitute source identity')
    arrays = decode_matrix_arrays(raw,product.arrays)
    if {n:(a.dtype.str,a.shape) for n,a in arrays.items()}!=expected_members(rule):
        raise ValueError('parameter factor diagnostics omit complete numerical witness members')
    return arrays


def root_census(allocation, products, *, rules, sources):
    """Whole matched groups, never iid coordinate/view/observation rows."""
    roots = {r.root.root_id:r for r in allocation.roots}
    families = {ObjectIdentity.from_record(c.coordinate_id,c):c.family_id for c in allocation.coordinates}
    if (len(products)!=len(roots) or {p.root_id for p in products}!=set(roots)
            or set(rules)!=set(roots) or set(sources)!=set(roots)):
        raise ValueError('parameter factor census omits an assigned root')
    cells = []
    for p in products:
        root = roots[p.root_id].root
        rule = rules[p.root_id]
        source = sources[p.root_id]
        if (p.source!=identity(source) or source.rule!=rule.identity or source.source_state!=p.source_state
                or p.history_numerical_pass!=source.history_numerical_pass
                or source.allocation!=ObjectIdentity.from_record(allocation.allocation_id,allocation)
                or source.roster!=allocation_scopes(allocation)
                or (source.root_id,source.independent_group_id,source.coordinate,source.clock_id)!=
                   (p.root_id,p.independent_group_id,p.coordinate,p.clock_id)
                or p.arrays.producers!=tuple(sorted((identity(source),source.supply),key=lambda x:x.object_id))
                or (p.independent_group_id,p.coordinate,p.clock_id)!=(root.independent_group_id,roots[p.root_id].coordinate,root.clock_id)
                or (p.requested_traces,p.requested_observations)!=(2*len(rule.sectors),len(rule.lattice))):
            raise ValueError('parameter factor census changes coordinate/group/clock/full denominator')
        if tuple((s.view,s.sector,s.tick) for s in p.scalars)!=tuple((v,s,t) for v in VIEWS for s in rule.sectors for t in rule.lattice):
            raise ValueError('parameter factor census changes complete scalar cells')
        if p.source_state=='COMPLETED':
            if tuple((t.view,t.sector) for t in p.traces)!=tuple((v,s) for v in VIEWS for s in rule.sectors):
                raise ValueError('parameter factor census duplicates or omits a view/sector trace')
            actual_roots = {t.root for t in p.traces}
            if (len(actual_roots)!=1 or any(t.root.root_id!=p.root_id or t.root.independent_unit_id!=p.independent_group_id
                    or t.root.source!=source.parameter_source or t.root.native_arrays!=source.history_arrays
                    or t.root.native_result!=source.history_product
                    or t.root.family_id!=families[p.coordinate]
                    or t.diagnostics!=p.arrays.array_artifact or t.diagnostic_members!=p.arrays.members for t in p.traces)):
                raise ValueError('parameter factor census substitutes trace root/source/diagnostic joins')
            for trace in p.traces:
                validate_trace(trace,rule)
        for view in VIEWS:
            for sector in rule.sectors:
                trace = next((t for t in p.traces if (t.view,t.sector)==(view,sector)),None)
                cells.append({'root_id':p.root_id,'coordinate_id':p.coordinate.object_id,'family_id':families[p.coordinate],'independent_group_id':p.independent_group_id,
                    'view':view,'sector':sector,'source_state':p.source_state,'requested_observations':p.requested_observations,
                    'available_observations':0 if trace is None else sum(o.status=='AVAILABLE' for o in trace.observations),
                    'structural_lifetime':None if trace is None else trace.moving_lifetime.disposition,
                    'history_numerical_pass':p.history_numerical_pass})
    return {'requested_roots':len(roots),'independent_groups':len({r.root.independent_group_id for r in roots.values()}),
        'cells':tuple(sorted(cells,key=lambda c:(c['root_id'],c['view'],c['sector']))),'inference':'EXPOSED_DESCRIPTIVE_NO_IID_OR_QUALIFICATION'}
