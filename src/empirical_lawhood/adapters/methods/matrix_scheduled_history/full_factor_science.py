# SPDX-License-Identifier: MPL-2.0
"""Casewise full-history measurement, independent checks and complete E4 census.

The parent authenticates actual original receipt locators and protected reveal
before supplying arrays. These PURE methods never load providers, RNG or native
work. They expose no causal predictor input and establish no sampling warrant.
"""
from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_parameter_factor import scalar
from empirical_lawhood.adapters.methods.matrix_parameter_factor.independent import assess_values
from empirical_lawhood.adapters.methods.matrix_parameter_factor.science import measure_values
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from . import science as scheduled_science
from .full_factor_records import (
    ScheduledFullFactorArrays, ScheduledFullFactorAssessment, ScheduledFullFactorProduct,
    ScheduledFullFactorRoot, ScheduledFullFactorSource, ScheduledFullFactorTrace,
    validate_product,
)
from .selected_e3_e4_records import (
    SelectedE3E4CaseResult, SelectedE3E4CausalPrefix, SelectedE3E4FullHistory,
    SelectedE3E4NativeSource, SelectedE3E4NumericalAssessment, pin,
    selected_original_factor_rule, validate_selected_prefix_projection,
)
from .selected_e4_native_records import (
    SelectedE4NativeCaseResult, SelectedE4ProtectedCausalPrefix, SelectedE4ProtectedFullHistory,
    SelectedE4ProtectedNativeSource, SelectedE4ProtectedNumericalAssessment,
)


def source_from_original(*,record_id,source,criterion,case,original_products,produced_input_parents,causal=None,history=None,numerical=None):
    """Convert authenticated original values explicitly; preserve their types/standing.

    This creates an input value, not authority or a proof that the receipt
    locators have been read. The existing original-product API must perform
    that authentication, including genuine reveal for protected full histories.
    """
    protected=type(source) is SelectedE4ProtectedNativeSource
    if type(source) not in (SelectedE3E4NativeSource,SelectedE4ProtectedNativeSource):
        raise TypeError('full factor follow-up requires an actual installed selected E4 source')
    source.__post_init__()
    case_kind=SelectedE4NativeCaseResult if protected else SelectedE3E4CaseResult
    if type(case) is not case_kind:
        raise TypeError('full factor follow-up changes original case edition')
    case.__post_init__()
    if (case.source!=source.reference.identity or case.root_id!=source.root_id
            or case.group_id!=source.root.root.independent_group_id
            or protected and case.coordinate!=source.coordinate):
        raise ValueError('full factor follow-up substitutes original coordinate/group/source')
    rule=selected_original_factor_rule(criterion)
    validate_selected_prefix_projection(criterion,source.policy,source.policy.cutoff_tick)
    continuation=next(value for value in case.native if value.phase=='continue')
    state={'COMPLETED':'COMPLETED','FAILED':'FAILED','UNKNOWN':'UNKNOWN_COMPLETION','UNENTERED':'NOT_ENTERED'}[continuation.disposition]
    origin='UNOBSERVED'
    causal_pin=None
    if causal is not None:
        causal_kind=SelectedE4ProtectedCausalPrefix if protected else SelectedE3E4CausalPrefix
        if type(causal) is not causal_kind:
            raise TypeError('full factor follow-up changes the actual causal record edition')
        causal.__post_init__()
        if causal.source!=source.reference.identity:
            raise ValueError('full factor follow-up substitutes actual original causal source')
        causal_pin=pin(causal,'prefix_id')
        origin=causal.disposition
        if protected and case.causal_prefix is not None:
            projection=case.causal_prefix
            if (projection.original,projection.source,projection.root,projection.cutoff_tick,projection.frame_sha256,projection.disposition)!=(
                    causal_pin,causal.source,causal.root,causal.cutoff_tick,causal.frame_sha256,causal.disposition):
                raise ValueError('full factor follow-up substitutes original protected causal projection')
    if state=='COMPLETED' and causal is None or protected and case.causal_prefix is not None and causal is None:
        raise ValueError('full factor follow-up omits actual original causal disposition')
    history_pin=numerical_pin=arrays=numerical_pass=None
    if (history is not None)!=(state=='COMPLETED'):
        raise ValueError('full factor follow-up changes actual original continuation availability')
    if history is not None:
        history_kind=SelectedE4ProtectedFullHistory if protected else SelectedE3E4FullHistory
        numerical_kind=SelectedE4ProtectedNumericalAssessment if protected else SelectedE3E4NumericalAssessment
        if type(history) is not history_kind or numerical is not None and type(numerical) is not numerical_kind:
            raise TypeError('full factor follow-up changes actual full-history/assessment records')
        history.__post_init__()
        history_pin=pin(history,'history_id')
        if (history.source!=source.reference.identity
                or history.completed_primary_steps!=source.coordinate.total_ticks
                or history.completed_fine_steps!=2*source.coordinate.total_ticks):
            raise ValueError('full factor follow-up changes actual full continuation/numerical producer')
        arrays=history.arrays
    if numerical is not None:
        numerical.__post_init__()
        numerical_pin=pin(numerical,'assessment_id')
        if (history is None or numerical.source!=source.reference.identity or numerical.history!=history_pin
                or numerical.phase!='full' or numerical.numerical_design!=ObjectIdentity.from_record(source.numerical_design.design_id,source.numerical_design)):
            raise ValueError('full factor follow-up changes actual original numerical source/history/design')
        numerical_pass=numerical.numerical_pass
    if case.full_assessment!=numerical_pin:
        raise ValueError('full factor follow-up discards or substitutes actual full numerical assessment')
    return ScheduledFullFactorSource(record_id,source.programme,pin(case,'root_id'),source.reference.identity,
        source.root_id,source.root.root.independent_group_id,source.coordinate,rule,
        source.policy.factor_numerical_design,state,origin,causal_pin,history_pin,arrays,numerical_pin,
        numerical_pass,original_products,produced_input_parents)


def _native(source,native_raw):
    source.__post_init__()
    if (native_raw is not None)!=(source.source_state=='COMPLETED'):
        raise ValueError('full factor follow-up changes actual full-history availability')
    native=None if native_raw is None else decode_matrix_arrays(native_raw,source.full_arrays)
    if native is not None:scheduled_science.validate_full_arrays(source,native)
    return native


def measure(source,native,*,artifact_id):
    """Measure every original full-lattice cell; no-origin does not erase history."""
    native=_native(source,native)
    samples=scalar.measure_values(source.coordinate,source.source_state,source.rule,native)
    root=(None if native is None else ScheduledFullFactorRoot(source.identity,source.root_id,source.group_id,
        ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate),source.history,source.full_arrays.array_artifact))
    arrays,traces=measure_values(root=root,rule=source.rule,native=native,samples=samples,
        trace_factory=ScheduledFullFactorTrace)
    nonfinite=tuple(name for name in arrays if not name.endswith(('_ticks','_available','_identifiable')))
    raw,members=encode_matrix_arrays(arrays,nonfinite_members=nonfinite)
    artifact=ArtifactIdentity(artifact_id,'selected-full-factor-diagnostics',MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(),'application/x-npz',len(raw))
    producers=source.producers
    operand=ScheduledFullFactorArrays('arrays.'+source.record_id,source.identity,artifact,members,producers,
        source.outcome_access,source.visibility_ceiling)
    traces=tuple(replace(row,diagnostics=artifact,diagnostic_members=members) for row in traces)
    product=ScheduledFullFactorProduct('product.'+source.record_id,source.identity,2*len(source.rule.sectors),
        len(source.rule.lattice),traces,samples,operand)
    validate_product(source,product)
    return raw,product


def assess(source,product,native,diagnostic_raw):
    """Independent all-eigenpair/raw-state oracle; never calls the producer."""
    validate_product(source,product)
    native=_native(source,native)
    arrays=decode_matrix_arrays(diagnostic_raw,product.arrays)
    from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import expected_members
    if {name:(row.dtype.str,row.shape) for name,row in arrays.items()}!=expected_members(source.rule):
        raise ValueError('full factor independent check changes exact diagnostic geometry')
    controls=assess_values(rule=source.rule,design=source.numerical_design,source_state=source.source_state,
        scalars=product.scalars,traces=product.traces,arrays=arrays,native=native)
    witness=all(row.disposition in ('SATISFIED','NOT_APPLICABLE') for row in controls)
    disposition=('HISTORY_UNAVAILABLE' if source.history is None else 'HISTORY_NUMERICAL_UNASSESSED'
        if source.history_numerical_pass is None else 'HISTORY_NUMERICALLY_FAILED'
        if not source.history_numerical_pass else 'MEASUREMENT_CHECKS_SATISFIED' if witness else 'WITNESS_NOT_ESTABLISHED')
    return ScheduledFullFactorAssessment('assessment.'+source.record_id,source.identity,product.identity,
        ObjectIdentity.from_record(source.numerical_design.design_id,source.numerical_design),controls,witness,
        source.history_numerical_pass,source.history is not None,disposition)


def read_retained(source,product,assessment,native,diagnostic_raw):
    observed=assess(source,product,native,diagnostic_raw)
    if observed!=assessment:
        raise ValueError('full factor retained assessment changes actual independent controls')
    return observed


def census(programme,original_cases,sources,products,assessments,*,record_id):
    """Join every original coordinate and retain the whole matched-group census.

    The actual original reader supplies original_cases, including negative and
    incomplete observations. This performs no outcome selection, regression,
    confidence calculation, source qualification or scientific adjudication.
    """
    from .full_factor_records import ScheduledFullFactorCell, ScheduledFullFactorCensus, validate_assessment
    from .selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
    from .selected_e4_programme import SelectedE4PhaseProgramme
    if type(programme) not in (SelectedE3E4DevelopmentProgramme,SelectedE4PhaseProgramme):
        raise TypeError('full factor census requires the actual original selected programme')
    programme.__post_init__()
    expected=tuple(row.root_id for row in programme.cases)
    if (tuple(row.root_id for row in original_cases)!=expected
            or tuple(row.root_id for row in sources)!=expected
            or len(products)!=len(expected) or len(assessments)!=len(expected)):
        raise ValueError('full factor census omits or reorders original whole-group coordinates')
    cells=[]
    for declared,case,source,product,assessment in zip(programme.cases,original_cases,sources,products,assessments,strict=True):
        expected_case=SelectedE3E4CaseResult if type(programme) is SelectedE3E4DevelopmentProgramme else SelectedE4NativeCaseResult
        if type(case) is not expected_case:raise TypeError('full factor census changes actual original case edition')
        case.__post_init__()
        state={'COMPLETED':'COMPLETED','FAILED':'FAILED','UNKNOWN':'UNKNOWN_COMPLETION','UNENTERED':'NOT_ENTERED'}[
            next(value for value in case.native if value.phase=='continue').disposition]
        if (source.programme!=programme.identity or source.original_case!=pin(case,'root_id')
                or (source.root_id,source.group_id,source.source)!=(declared.root_id,declared.independent_group_id,declared.source)
                or (case.root_id,case.group_id,case.source)!=(declared.root_id,declared.independent_group_id,declared.source)
                or ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate)!=declared.coordinate
                or source.source_state!=state or source.full_numerical!=case.full_assessment):
            raise ValueError('full factor census substitutes actual observed case or original physical/group/continuation scope')
        validate_assessment(source,product,assessment)
        traces={(row.view,row.sector):row for row in product.traces}
        for view in ('PRIMARY','FINE'):
            for sector in source.rule.sectors:
                trace=traces.get((view,sector))
                observations=() if trace is None else trace.observations
                available=sum(row.status=='AVAILABLE' for row in observations)
                unidentifiable=sum(row.status=='UNIDENTIFIABLE' for row in observations)
                unavailable=(len(source.rule.lattice) if trace is None else
                    sum(row.status in ('UNAVAILABLE','NUMERICAL_INVALID') for row in observations))
                comparable=tuple(row for row in observations if row.raw_admitted is not None and row.scalar_closure_pass is not None)
                cells.append(ScheduledFullFactorCell(source.root_id,source.group_id,declared.coordinate,
                    source.identity,product.identity,assessment.identity,view,sector,source.source_state,
                    source.causal_disposition,source.history_numerical_pass,assessment.witness_pass,
                    len(source.rule.lattice),available,unidentifiable,unavailable,len(comparable),
                    sum(row.raw_admitted!=row.scalar_closure_pass for row in comparable),
                    None if trace is None else trace.moving_lifetime,None if trace is None else trace.origin_fixed_lifetime))
    return ScheduledFullFactorCensus(record_id,programme.identity,programme.group_ids,expected,
        tuple(sorted(cells,key=lambda row:(row.root_id,row.view,row.sector))))
