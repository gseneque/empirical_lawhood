# SPDX-License-Identifier: MPL-2.0
"""SCI02-C native science plugged into the existing shared subwork custody."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import resource
import time

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as old
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as previous
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import MATRIX_ARRAY_SCHEMA, Sci02NativeHistory
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import NAMESPACE, Sci02CNativeCheckpoint


def native_work(context, config, provenance, expected_parent):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
    definition = NativeSubworkDefinition('subwork.' + config.node_id, NAMESPACE + '.native.v1', expected_parent,
        config.identity, tuple(sorted((config.design.identity, config.root.identity, provenance.identity), key=lambda v: v.object_id)),
        provenance.code_sources_sha256, provenance.dependency_lock_sha256, tuple(sorted(p.materialization_id for p in context.input_ports)),
        tuple(pin for _, pin in binding.stream_pins(config)),
        (NativeSubworkOutput('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),
         NativeSubworkOutput('checkpoint', Sci02CNativeCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json')))
    roster = NativeSubworkRoster('selected.native-subwork', expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, binding.units(config), binding.slots(config), (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
    if type(runner) is not NativeRunner: raise TypeError('SCI02-C native preparation needs its registered runner')
    config, _, _, provenance, _, _ = binding.decode(context)
    return native_work(context, config, provenance, expected_parent)


def acquire(config, parents, arrays, streams, on_step=None):
    if config.phase in ('prefix', 'completion'):
        return original.acquire_preparation_interval(config.design, 'ORIGINAL' if config.phase == 'prefix' else config.recipe,
            tuple(s for _, s in streams), prefix=None if config.phase == 'prefix' else arrays['prefix'],
            saved=() if config.phase == 'prefix' else parents['prefix'].generators, on_step=on_step)
    if config.phase == 'baseline':
        return previous.acquire_baseline(config.design, arrays['handoff'], arrays['instrument'], streams, on_step=on_step)
    if config.phase == 'reference':
        costs = {}
        result = previous.acquire_reference(config.design, arrays['handoff'], arrays['instrument'], arrays['baseline'],
            streams, parents['baseline'].generators, on_step=on_step, observe_cost=lambda key, value: costs.__setitem__(key, value))
        factor, = (i for i, action in enumerate(config.design.assay.actions) if action.role == 'FACTOR')
        costs['consumer.factor_reference'] = sum(v for k, v in costs.items() if f'.a{factor}.' in k)
        measured = original.measurements({k + '_cpu_seconds': v for k, v in costs.items()})
        return replace(result, measurements=tuple(sorted((*result.measurements, *measured))))
    raise ValueError('SCI02-C native runner cannot execute a pure operation')


class NativeRunner:
    def __init__(self, *, manifest): self.manifest = manifest

    def execute(self, context):
        raise ValueError('SCI02-C native acquisition requires ordinary lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
        try:
            config, parents, arrays, provenance, streams, _ = binding.decode(context)
            output, = (p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            missing = config.phase in ('baseline', 'reference') and 'forces' not in arrays['instrument']
            missing |= config.phase == 'reference' and 'unavailable' in arrays['baseline']
            if missing:
                result = original.unavailable('SOURCE_OR_CONTINUATION_UNAVAILABLE')
                raw, operand = old._pack(config, result, output.logical_artifact_id)
                return old._outputs(context, binding.product(config, parents, result, operand), raw)
            work = native_work(context, config, provenance, native_subwork.parent_contact)
            definition, = work.definitions
            completed = native_subwork.recover(definition)
            if completed is not None:
                if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None or completed.receipt is None
                        or completed.completion.operational_status is not OperationalStatus.SUCCEEDED):
                    raise ValueError('SCI02-C refuses unknown or failed native contact replay')
                raw = b''.join(native_subwork.iter_completed_output(definition, 'arrays'))
                checkpoint = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'checkpoint')),
                    Sci02CNativeCheckpoint, maximum_bytes=binding.MAX_RECORD)
                if checkpoint.config != config.identity or checkpoint.arrays.array_artifact.artifact_id != output.logical_artifact_id:
                    raise ValueError('SCI02-C recovery changes original native checkpoint or compiler output')
                from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
                result = original.Computation(dict(decode_matrix_arrays(raw, checkpoint.arrays)), generators=checkpoint.generators, measurements=checkpoint.measurements)
                operand = checkpoint.arrays
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError('SCI02-C refuses unreceipted native reacquisition')
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
                entry = native_subwork.begin(definition)
                native_subwork.contact(entry)
                cpu, wall = time.process_time(), time.monotonic()
                try:
                    result = invoke_native_subwork(native_subwork, entry, acquire, config, parents, arrays, streams,
                        **({'on_step': lambda count: progress.advance(Decimal(count))} if progress is not None else {}))
                    raw, operand = old._pack(config, result, output.logical_artifact_id)
                    checkpoint = Sci02CNativeCheckpoint('checkpoint.' + config.node_id, config.identity, operand,
                        tuple(sorted(result.generators, key=lambda r: (r[0], r[1].purpose))), result.measurements)
                    for key, payload in (('arrays', raw), ('checkpoint', checkpoint.canonical_bytes())):
                        native_subwork.publish_output(entry, key, (payload,), maximum_bytes=len(payload), maximum_chunk_bytes=len(payload),
                            expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())
                except (ArithmeticError, MemoryError, ValueError):
                    native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), None),
                        cost_scope='SCI02-C original coupled interval inside ordinary task', unknown_streams=definition.streams,
                        reason_codes=('matrix-sci02c-native-failure',))
                    raise
                completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), Decimal(len(raw))),
                    cost_scope='SCI02-C original coupled interval inside ordinary task', consumed_streams=definition.streams,
                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
            native = (Sci02NativeHistory(definition, completed.completion, completed.receipt),)
            return old._outputs(context, binding.product(config, parents, result, operand, native=native), raw)
        finally:
            for port in context.input_ports: port.close()
