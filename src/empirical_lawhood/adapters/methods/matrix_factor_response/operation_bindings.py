"""Shared scoped array, output and native-subwork helpers for current response owners."""

from decimal import Decimal
from hashlib import sha256
import resource
import time
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, invoke_native_subwork
from .eligibility import EligibleMatrixArrays, consume_eligible_arrays, refuse_completed_or_uncertain_branch
from .records import identity


def consume_array(ports,saved,*,expected_producers,source=None,origin=None):
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    port = ports.get(saved.array_artifact.artifact_id)
    expected_producers = tuple(sorted(expected_producers,key=lambda x:x.object_id))
    if type(saved) is EligibleMatrixArrays:
        public = source.eligible if source is not None else origin.eligible_source
        return consume_eligible_arrays(port,saved,public,
            expected_members=tuple((m.name,m.dtype,m.shape) for m in saved.members),expected_producers=expected_producers,
            allocation=None if origin is None else origin.allocation,root_id=None if origin is None else origin.root_id)
    if (not isinstance(port,WorkerInputPort) or saved.producers != expected_producers
            or port.artifact_id != saved.array_artifact.artifact_id or port.payload_schema != MATRIX_ARRAY_SCHEMA
            or port.media_type != 'application/x-npz' or port.size_bytes != saved.array_artifact.size_bytes
            or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('matrix exposed array port/source/full member contract differs')
    return decode_matrix_arrays(port.read(),saved)



def _outputs(context,product,raw=None):
    ports = {p.output_id.rsplit('.',1)[-1]:p for p in context.output_ports}
    if set(ports) != ({'product'} if raw is None else {'product','arrays'}) or ports['product'].payload_schema != product.SCHEMA:
        raise ValueError('matrix B provider changes complete scientific output census')
    outputs = [TaskOutputPayload(ports['product'].output_id,product.canonical_bytes())]
    if raw is not None:
        if product.arrays.array_artifact.artifact_id != ports['arrays'].logical_artifact_id or sha256(raw).hexdigest() != product.arrays.array_artifact.sha256:
            raise ValueError('matrix B product differs from actual published arrays')
        outputs.append(TaskOutputPayload(ports['arrays'].output_id,raw))
    return RunnerResult(tuple(sorted(outputs,key=lambda x:x.output_id)),(ReceiptCheck('complete-coupled-b-census',True,()),))



def _definition(context,config,source,subwork_id,operands,stream,parent_contact):
    return NativeSubworkDefinition(subwork_id,'matrix-factor-native.'+subwork_id,parent_contact,
        identity(config),
        tuple(sorted(set((*operands,source.provenance.identity)),key=lambda x:x.object_id)),source.provenance.code_sources_sha256,source.provenance.dependency_lock_sha256,
        tuple(sorted(p.materialization_id for p in context.input_ports)),
        () if stream is None else (ObjectIdentity.from_record('stream.'+source.root.root_id+'.'+stream.purpose_id,stream),),
        (NativeSubworkOutput('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'),))



def _completed_native_values(native_subwork,definition,inspection,expected_members):
    """Receipt-only bounded readback; no creator handle or effect is reconstructed."""
    import numpy as np
    if (inspection.completion is None or inspection.completion.operational_status is not OperationalStatus.SUCCEEDED
            or inspection.receipt is None or len(inspection.outputs) != 1
            or inspection.outputs[0].logical.payload_schema != MATRIX_ARRAY_SCHEMA
            or inspection.outputs[0].logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
            or inspection.outputs[0].materialization.size_bytes > MAXIMUM_MATRIX_ARRAY_BYTES):
        raise ValueError('B completed child lacks its exact successful scientific output receipt')
    raw = b''.join(native_subwork.iter_completed_output(definition,'arrays'))
    from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays
    values = decode_native_matrix_arrays(raw, expected_members)
    if any(not np.isfinite(v).all() for v in values.values()):
        raise ValueError('B completed child has nonfinite native operands')
    return values



def _run_native(native_subwork,definition,producer,expected_members):
    recovered = native_subwork.recover(definition)
    if recovered is not None:
        return _completed_native_values(native_subwork,definition,recovered,expected_members)
    refuse_completed_or_uncertain_branch(native_subwork,definition)
    entry = native_subwork.begin(definition)
    native_subwork.contact(entry)
    cpu,wall = time.process_time(),time.monotonic()
    try:
        values = invoke_native_subwork(native_subwork, entry, producer)
    except (MemoryError,ArithmeticError,ValueError):
        native_subwork.complete(entry,operational_status=OperationalStatus.FAILED,
            cost=InquiryCost(Decimal(str(time.process_time()-cpu)),Decimal(str(time.monotonic()-wall)),None),
            cost_scope='B native subwork nested inside complete task',unknown_streams=definition.streams,reason_codes=('matrix-factor-native-failure',))
        raise
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    raw,_ = encode_matrix_arrays(values)
    native_subwork.publish_output(entry,'arrays',(raw,),maximum_bytes=len(raw),maximum_chunk_bytes=len(raw),
        expected_size_bytes=len(raw),expected_physical_sha256=sha256(raw).hexdigest())
    native_subwork.complete(entry,operational_status=OperationalStatus.SUCCEEDED,
        cost=InquiryCost(Decimal(str(time.process_time()-cpu)),Decimal(str(time.monotonic()-wall)),Decimal(len(raw))),
        cost_scope='B native subwork nested inside complete task',consumed_streams=definition.streams,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    return values
