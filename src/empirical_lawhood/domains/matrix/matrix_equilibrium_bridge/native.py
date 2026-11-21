# SPDX-License-Identifier: MPL-2.0
"""SCI02-D acquisition using the shared native contact and recovery store."""
from decimal import Decimal
from hashlib import sha256
import resource
import time

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import sampling
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BridgeCheckpoint, BridgeNativeHistory, NAMESPACE


def native_work(context, config, provenance, expected_parent):
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import bindings as binding
    outputs = tuple(NativeSubworkOutput(key, binding.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz')
        for key in ('arrays', 'gradients', 'positions')) + (
        NativeSubworkOutput('checkpoint', BridgeCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'),)
    definition = NativeSubworkDefinition('subwork.'+config.node_id, NAMESPACE+'.native.v1', expected_parent, config.identity,
        tuple(sorted((config.design.identity, config.root.identity, provenance.identity), key=lambda p: p.object_id)),
        provenance.code_sources_sha256, provenance.dependency_lock_sha256, tuple(sorted(p.materialization_id for p in context.input_ports)),
        config.root.streams, tuple(sorted(outputs, key=lambda p: p.output_id)))
    roster = NativeSubworkRoster('selected.native-subwork', expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, binding.units(config), binding.slots(config), (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.bindings import decode
    if type(runner) is not NativeRunner: raise TypeError('SCI02-D needs its registered native runner')
    config, _, _, provenance, _ = decode(context)
    return native_work(context, config, provenance, expected_parent)


class NativeRunner:
    def __init__(self, *, manifest): self.manifest = manifest
    def execute(self, context): raise ValueError('SCI02-D native acquisition requires ordinary lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import bindings as binding
        try:
            config, parents, _, provenance, streams = binding.decode(context)
            ids = {p.output_id.rsplit('.', 1)[-1]: p.logical_artifact_id for p in context.output_ports}
            work = native_work(context, config, provenance, native_subwork.parent_contact)
            definition, = work.definitions
            completed = native_subwork.recover(definition)
            if completed is not None:
                if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None or completed.receipt is None
                        or completed.completion.operational_status is not OperationalStatus.SUCCEEDED):
                    raise ValueError('SCI02-D refuses unknown or failed original native contact replay')
                checkpoint = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'checkpoint')),
                    BridgeCheckpoint, maximum_bytes=binding.MAX_RECORD)
                operands = dict(zip(('arrays', 'positions', 'gradients'), (checkpoint.arrays, *checkpoint.shards), strict=True))
                if checkpoint.config != config.identity or any(a.array_artifact.artifact_id != ids[k] for k, a in operands.items()):
                    raise ValueError('SCI02-D recovery changes original native outputs or checkpoint')
                raw = {key: b''.join(native_subwork.iter_completed_output(definition, key)) for key in operands}
                from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
                values = {}
                for key, operand in operands.items(): values.update(decode_matrix_arrays(raw[key], operand))
                result = Computation(values, measurements=checkpoint.measurements)
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('SCI02-D refuses unreceipted native reacquisition')
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
                entry = native_subwork.begin(definition); native_subwork.contact(entry)
                cpu, wall = time.process_time(), time.monotonic()
                try:
                    result = invoke_native_subwork(native_subwork, entry, sampling.acquire, config, streams,
                        **({'progress': lambda count: progress.advance(Decimal(count))} if progress is not None else {}))
                    raw, operands = binding.pack(config, result, ids)
                    checkpoint = BridgeCheckpoint('checkpoint.'+config.node_id, config.identity, operands['arrays'], result.measurements,
                        tuple(operands[k] for k in ('positions', 'gradients')))
                    for key, payload in sorted({**raw, 'checkpoint': checkpoint.canonical_bytes()}.items()):
                        native_subwork.publish_output(entry, key, (payload,), maximum_bytes=len(payload), maximum_chunk_bytes=len(payload),
                            expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())
                except (ArithmeticError, MemoryError, ValueError):
                    native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), None),
                        cost_scope='SCI02-D original native bundle inside ordinary task', unknown_streams=definition.streams,
                        reason_codes=('matrix-sci02d-native-failure',))
                    raise
                completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), Decimal(sum(map(len, raw.values())))),
                    cost_scope='SCI02-D original native bundle inside ordinary task', consumed_streams=definition.streams,
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
            native = (BridgeNativeHistory(definition, completed.completion, completed.receipt),)
            return binding.outputs(context, binding.product(config, parents, result, operands, native=native), raw)
        finally:
            for port in context.input_ports: port.close()
