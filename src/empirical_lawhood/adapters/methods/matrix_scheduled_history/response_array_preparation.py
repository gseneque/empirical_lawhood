# SPDX-License-Identifier: MPL-2.0
"""Worker-local native array validation over exact authenticated inputs.

Domain callers retain their own configuration, lineage and scientific checks.
Parent PURE projections carry identities; only worker preflight fills this
single-invocation cache, and serialization always drops its arrays.
"""


from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult
from empirical_lawhood.runtime.execution import TaskOutputPayload

from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES

from empirical_lawhood.adapters.methods.matrix_dataset_readers import retained_array_mappings

from contextlib import contextmanager

from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decimal_context_key
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from .science import consume_prefix


class NativeResponseArrayPreparation:
    def __init__(self):
        self._prepared = None

    def __getstate__(self):
        return {'_prepared': None}

    def clear(self):
        self._prepared = None

    @staticmethod
    def _key(context):
        contract = context.prepared_invocation
        if type(contract) is not PreparedInvocationContract:
            raise ValueError('native response arrays need the exact prepared invocation')
        contract.validate_context(context)
        return (contract.identity, tuple((row.binding, row.physical_sha256) for row in contract.inputs),
            decimal_context_key())

    def prepare(self, context, *, source, history, physical, ports, protocol=None, physical_disposition=None):
        key = self._key(context)
        scope = history, physical, protocol, physical_disposition
        if self._prepared is None or self._prepared[0] != key or self._prepared[4] != scope:
            self.clear()
            raw = ports['history-arrays'].read()
            prefix = consume_prefix(source, history, raw)
            frozen = None if physical is None else decode_matrix_arrays(ports['physical-arrays'].read(), physical)
            if physical is not None and (protocol is not None or physical_disposition is not None):
                from .response_science import validate_frozen_response_arrays
                validate_frozen_response_arrays(protocol, frozen, disposition=physical_disposition)
            self._prepared = key, prefix, frozen, raw if physical is None else None, scope

    def _current(self, context):
        cached = self._prepared
        if cached is None or cached[0] != self._key(context):
            raise ValueError('native response execution changes its actual preflight array inputs')
        return cached

    def arrays(self, context):
        cached = self._current(context)
        return cached[1], cached[2]

    def prefix_raw(self, context):
        raw = self._current(context)[3]
        if raw is None:
            raise ValueError('native continuation requires its selected exact prefix archive')
        return raw


@contextmanager
def selected_record_array_mappings(records, ports, *, protocol):
    owners = {"prefix-arrays": lambda: records["prefix"].arrays, "diagnostic-arrays": lambda: records["witness"].arrays,
        "causal-arrays": lambda: records["causal"].arrays, "mechanical-arrays": lambda: records["mechanical"].arrays,
        "dense-mechanical-arrays": lambda: records["dense-mechanical"].arrays,
        "full-arrays": lambda: records["full"].arrays, "response-arrays": lambda: records["responses"].arrays,
        "templates": lambda: protocol.templates}
    names = tuple(sorted(ports))
    selected = iter(ports[name] for name in names)
    with retained_array_mappings(tuple(owners[name]() for name in names), lambda artifact: next(selected),
            maximum_chunk_bytes=1024 * 1024, maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES) as values:
        yield dict(zip(names, values, strict=True))


def selected_worker_outputs(context, products, raw=None, *, additional_arrays=()):
    values = {name: value.canonical_bytes() for name, value in products.items()}
    if raw is not None:
        values["arrays"] = raw
    if (type(additional_arrays) is not tuple
            or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str or type(row[1]) is not bytes
                for row in additional_arrays)
            or len({name for name, _ in additional_arrays}) != len(additional_arrays)
            or any(name in values for name, _ in additional_arrays)):
        raise ValueError("selected E4 additional array outputs change exact names, bytes or census")
    values.update(additional_arrays)
    if {value.output_id for value in context.output_ports} != {context.task_id + "." + name for name in values}:
        raise ValueError("selected E4 worker changes complete compiler-derived output census")
    return RunnerResult(tuple(TaskOutputPayload(context.task_id + "." + name, value) for name, value in sorted(values.items())),
        (ReceiptCheck("selected-e4-original-source-causal-and-complete-development-products", True, ()),))


def read_selected_native_archive(port):
    # Existing segment native owner consumes a bounded single-root NPZ archive.
    # This remains an explicit materialization boundary, not a global-bank copy.
    cursor = port.cursor()
    try:
        raw = cursor.read(MAXIMUM_MATRIX_ARRAY_BYTES + 1)
    finally:
        cursor.close()
    if len(raw) != port.size_bytes or len(raw) > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError("selected E4 original archive differs from its bounded exact input")
    return raw
