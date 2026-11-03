# SPDX-License-Identifier: MPL-2.0
"""Complete streamed equation assessment over authenticated segment leaves."""

from hashlib import sha256

import numpy as np

from empirical_lawhood.adapters.methods.matrix_array_chunks import (
    ChunkedMatrixArrays, MatrixArrayInterval, MatrixWholeArrayMember,
    encode_chunk, iter_framed_chunk_arrays, iter_chunk_arrays,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history_segments import segment_intervals
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays

from . import independent
from .chunked_records import (
    MatrixParameterSegmentCheckpoint, chunked_members,
    identity, segment_plan,
)
from .records import coordinate_identity


def package_segment(bound,values,definition,previous,*,science_artifact_id,terminal_artifact_id):
    index = segment_plan(bound).index((values.start,values.stop))
    producers = tuple(sorted((identity(bound.source),coordinate_identity(bound.coordinate)),key=lambda i:i.object_id))
    prefix = 'chunk.'+bound.root_id+'.segment.'+f'{index:08d}'
    intervals = tuple(MatrixArrayInterval(name,start,stop) for name,(start,stop) in segment_intervals(bound.coordinate,values.start,values.stop).items())
    science_raw,science_chunk = encode_chunk(values.arrays,intervals,chunk_id=prefix+'.science',artifact_id=science_artifact_id,producers=producers)
    terminal = {'terminal_'+name:value for name,value in values.terminal_arrays.items()}
    terminal_intervals = tuple(MatrixArrayInterval(name,2*index,2*index+2) for name in sorted(terminal))
    terminal_raw,terminal_chunk = encode_chunk(terminal,terminal_intervals,chunk_id=prefix+'.terminal',artifact_id=terminal_artifact_id,producers=producers)
    checkpoint = MatrixParameterSegmentCheckpoint('checkpoint.'+bound.root_id+'.'+f'{index:08d}',identity(bound.source),
        coordinate_identity(bound.coordinate),values.start,values.stop,science_chunk,terminal_chunk,values.generators,definition.identity,
        None if previous is None else identity(previous.checkpoint))
    checkpoint.validate_source(bound)
    return science_raw,science_chunk,terminal_raw,checkpoint


def complete_manifest(bound,segments,fetch):
    """Derive every complete member digest one receipted leaf at a time."""
    if tuple((s.checkpoint.start,s.checkpoint.stop) for s in segments) != segment_plan(bound):
        raise ValueError('cannot seal incomplete parameter segment denominator')
    previous = None
    expected = chunked_members(bound)
    digests = {name:sha256() for name in expected}
    chunks = []
    for segment in segments:
        segment.validate_source(bound,previous);previous = segment
        for chunk in (segment.arrays,segment.checkpoint.terminal_arrays):
            values = decode_matrix_arrays(fetch(chunk.array_artifact),chunk)
            for name,value in values.items():
                digests[name].update(value.tobytes(order='C'))
            chunks.append(chunk)
            del values
    members = tuple(MatrixWholeArrayMember(name,dtype,shape,digests[name].hexdigest()) for name,(dtype,shape) in expected.items())
    return ChunkedMatrixArrays('arrays.'+bound.root_id,identity(bound.source),bound.source.compact.allocation,members,
        tuple(chunks),tuple(sorted((identity(bound.source),coordinate_identity(bound.coordinate)),key=lambda i:i.object_id)))


def _segment_controls(bound,segment,science,terminal,previous_terminal):
    c,checkpoint = bound.coordinate,segment.checkpoint
    start,stop = checkpoint.start,checkpoint.stop
    expected = segment_intervals(c,start,stop)
    if set(science) != set(expected):
        raise ValueError('parameter segment omits full original scientific members')
    for prefix,multiplier in (('primary',1),('fine',2)):
        for component in ('positions','momenta','alpha_tilde','ticks'):
            name = prefix+'_'+component
            begin,end = expected[name]
            values = science[name]
            wanted = (end-begin,2,3,4,4) if component in ('positions','momenta') else (end-begin,2) if component == 'alpha_tilde' else (end-begin,)
            dtype = '<c16' if component in ('positions','momenta') else '<f8' if component == 'alpha_tilde' else '<i8'
            if values.shape != wanted or values.dtype.str != dtype or not np.isfinite(values).all():
                raise ValueError('parameter segment changes complete state shape/dtype/finite population')
            if component == 'ticks' and not np.array_equal(values,np.arange(begin,end,dtype='<i8')):
                raise ValueError('parameter segment changes exact physical tick denominator')
            if component == 'alpha_tilde' and not np.array_equal(values,np.asarray([c.couplings(t,refinement=multiplier) for t in range(begin,end)],dtype='<f8')):
                raise ValueError('parameter segment changes actual native coupling schedule')
        for component in ('positions','momenta'):
            value = science[prefix+'_'+component][0]
            reference = getattr(initial_parameter_state(c),component) if start == 0 else previous_terminal['terminal_'+prefix+'_'+component]
            if not np.array_equal(value,reference):
                raise ValueError('parameter segment substitutes exact previous terminal/initial phase')
    for name,values in science.items():
        if not np.isfinite(values).all():
            raise ValueError('parameter segment loses finite innovation/state population')
        if values.dtype.str == '<c16' and np.linalg.norm(values-values.conj().swapaxes(-1,-2)) > 1e-10*max(1.,np.linalg.norm(values)):
            raise ValueError('parameter segment loses full Hermitian phase/noise population')
    trajectory = []
    for prefix,multiplier,view in (('primary',1,c.primary_view),('fine',2,c.fine_view)):
        positions,momenta = science[prefix+'_positions'],science[prefix+'_momenta']
        alpha,noise = science[prefix+'_alpha_tilde'],science[prefix+'_innovations']
        errors = independent._trajectory_errors(positions,momenta,noise,c.member,view,alpha,
            (c.couplings(multiplier*start+index+1,refinement=multiplier) for index in range(len(noise))),
            terminal=(terminal['terminal_'+prefix+'_positions'],terminal['terminal_'+prefix+'_momenta']))
        trajectory.append(errors)
        if checkpoint.stop == c.total_ticks:
            for component in ('positions','momenta'):
                if not np.array_equal(science[prefix+'_'+component][-1],terminal['terminal_'+prefix+'_'+component]):
                    raise ValueError('parameter final terminal checkpoint changes complete science endpoint')
    bridge_errors,bath_errors = independent._ou_errors(c.primary_view,science['primary_innovations'],
        science['fine_innovations'],science['bridge_innovations'])
    return *trajectory,bridge_errors,bath_errors


def assessment_from_chunks(bound,history,chunks,*,emit_control,control_artifact_id):
    """Constant-size summaries; retain every exact residual in bounded leaves."""
    from decimal import Decimal
    from empirical_lawhood.adapters.methods.matrix_array_chunks import FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from .chunked_control_records import MatrixParameterChunkControlSummary, MatrixParameterChunkedAssessmentReport
    from .records import METHODS
    history.validate_source(bound)
    if not callable(emit_control) or not control_artifact_id:
        raise ValueError('complete controls require their expressly selected streamed output sink')
    counts = [0]*4
    maxima = [Decimal(-1)]*4
    worst = [0]*4
    violations = [0]*4
    design = bound.numerical_design
    tolerances = (design.trajectory_tolerance,design.trajectory_tolerance,design.bridge_tolerance,design.trajectory_tolerance)
    controls_chunks = []
    digests = {name:sha256() for name in METHODS}
    container_digest,container_bytes = sha256(),0
    iterator = iter(chunks)
    previous_terminal = None
    for index,segment in enumerate(history.segments):
        scientific_chunk,science = next(iterator)
        terminal_chunk,terminal = next(iterator)
        if scientific_chunk != segment.arrays or terminal_chunk != segment.checkpoint.terminal_arrays:
            raise ValueError('parameter reader changes exact ordered native segment leaves')
        rows = _segment_controls(bound,segment,science,terminal,previous_terminal)
        values,intervals = {},[]
        for control_index,(name,row,tolerance) in enumerate(zip(METHODS,rows,tolerances,strict=True)):
            value = np.asarray(row,dtype='<f8')
            begin = counts[control_index]
            values[name] = value
            intervals.append(MatrixArrayInterval(name,begin,begin+len(value)))
            digests[name].update(value.tobytes(order='C'))
            for offset,residual in enumerate(value,begin+1):
                observed = Decimal(repr(float(residual)))
                if not observed.is_finite():
                    raise ValueError('nonfinite independent residual prevents complete assessment')
                if observed > maxima[control_index]:
                    maxima[control_index],worst[control_index] = observed,offset
                violations[control_index] += observed > tolerance
            counts[control_index] += len(value)
        raw,chunk = encode_chunk(values,intervals,chunk_id='chunk.controls.'+bound.root_id+'.'+f'{index:08d}',
            artifact_id='control-array.'+bound.root_id+'.'+f'{index:08d}',
            producers=tuple(sorted((identity(history),identity(design)),key=lambda i:i.object_id)))
        controls_chunks.append(chunk)
        header = len(raw).to_bytes(8,'big')
        for piece in (header,raw):
            container_digest.update(piece);container_bytes += len(piece);emit_control(piece)
        previous_terminal = terminal
        del science,rows,values,raw
    # Exhaustion seals all native input hashes before a final report exists.
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise ValueError('parameter reader introduces extra undeclared native leaf')
    n = bound.coordinate.total_ticks
    if tuple(counts) != (n,2*n,n,n):
        raise ValueError('parameter streamed assessment loses complete outcome denominator')
    summaries = tuple(MatrixParameterChunkControlSummary(name,maxima[i],tolerances[i],
        'VIOLATED' if violations[i] else 'SATISFIED',counts[i],96 if i == 3 else 192,violations[i],worst[i])
        for i,name in enumerate(METHODS))
    members = tuple(MatrixWholeArrayMember(name,'<f8',(counts[i],),digests[name].hexdigest()) for i,name in enumerate(METHODS))
    members = tuple(sorted(members,key=lambda m:m.name))
    evidence = ChunkedMatrixArrays('controls.'+bound.root_id,identity(bound.source),bound.source.compact.allocation,members,
        tuple(controls_chunks),tuple(sorted((identity(history),identity(design)),key=lambda i:i.object_id)))
    container = ArtifactIdentity(control_artifact_id,'framed-complete-control-residuals',FRAMED_ARRAY_SCHEMA,
        container_digest.hexdigest(),FRAMED_ARRAY_MEDIA,container_bytes)
    return MatrixParameterChunkedAssessmentReport('assessment.'+bound.root_id,identity(bound.source),identity(history),identity(design),bound.source.compact.allocation,
        summaries,evidence,container,all(c.disposition == 'SATISFIED' for c in summaries))


def assess_framed(bound,history,read,*,emit_control,control_artifact_id):
    return assessment_from_chunks(bound,history,iter_framed_chunk_arrays(history.arrays,history.container,read),
        emit_control=emit_control,control_artifact_id=control_artifact_id)


def assess_retained(bound,history,fetch,*,emit_control,control_artifact_id):
    return assessment_from_chunks(bound,history,iter_chunk_arrays(history.arrays,fetch),
        emit_control=emit_control,control_artifact_id=control_artifact_id)
