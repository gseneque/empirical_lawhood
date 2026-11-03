# SPDX-License-Identifier: MPL-2.0
"""Native invocation plumbing shared by the three exact selected lane facades."""
from hashlib import sha256

from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload

from . import preparation_bindings as preparation
from . import preparation_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_array_preparation import NativeResponseArrayPreparation


def _read(port, contract):
    cursor = port.cursor()
    try:
        raw = cursor.read()
    finally:
        cursor.close()
    digest = sha256(raw).hexdigest()
    if (len(raw) != port.size_bytes or digest != contract.physical_sha256
            or digest != contract.logical.content_sha256):
        raise ValueError("selected worker changes exact issued physical/canonical bytes")
    return raw

def _outputs(context, products, raw=None):
    values = {name: value.canonical_bytes() for name, value in products.items()}
    if raw is not None:
        values["arrays"] = raw
    if {row.output_id for row in context.output_ports} != {context.task_id + "." + name for name in values}:
        raise ValueError("selected worker changes its complete compiler-derived output census")
    return RunnerResult(tuple(TaskOutputPayload(context.task_id + "." + name, value) for name, value in sorted(values.items())),
        (ReceiptCheck("selected-original-source-native-and-complete-independent-products", True, ()),))

def _native_inputs(context, config, records, arrays, expected_parent):
    source = config.source
    if (expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id, expected_parent.input_materialization_ids,
            expected_parent.implementation_commit) != (context.run_id, context.task_id, context.attempt_id,
            context.input_materialization_ids, source.provenance.observed_git_head):
        raise ValueError("selected native preparation changes its actual issued parent/source implementation")



class PreparedNativeArrayPreparation(NativeResponseArrayPreparation):
    """Same invocation-local cache, using the prepared subject's exact validators."""
    def prepare(self, context, *, config, records, arrays):
        from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
        from . import prepared_response_science
        key = self._key(context)
        scope = config.source, records.get("history"), records.get("mechanical")
        if self._prepared is not None and self._prepared[0] == key and self._prepared[4] == scope:
            return
        self.clear()
        source = config.source
        raw_arrays = {name: value if type(value) is bytes else value.read() for name, value in arrays.items()}
        initial = preparation_science.initial_state(source.initial, raw_arrays["initial-state"])
        prefix = frozen = None
        if config.phase == "responses":
            history, mechanical = records["history"], records["mechanical"]
            history.arrays.validate_source(source)
            prefix = decode_matrix_arrays(raw_arrays["history-arrays"], history.arrays)
            preparation_science.validate_preparation_arrays(source, prefix, initial=initial)
            if records["causal"].disposition == mechanical.disposition == "AVAILABLE":
                frozen = prepared_response_science._context(source, history.arrays, config.protocol,
                    config.panels, mechanical.arrays, raw_arrays["mechanical-arrays"])
            else:
                frozen = decode_matrix_arrays(raw_arrays["mechanical-arrays"], mechanical.arrays)
        self._prepared = key, initial, prefix, frozen, scope, raw_arrays

    def arrays(self, context):
        return self._current(context)[1:4]

    def raw_arrays(self, context):
        return self._current(context)[5]


def execute_selected_native(runner, context, native_subwork, *, native_phases, decode, native_inputs, execute_future, outputs, progress=None):
    try:
        config, records, arrays = decode(context, runner)
        if runner.phase in native_phases:
            native_inputs(context, config, records, arrays, native_subwork.parent_contact)
        initial, prefix, frozen = runner._native_array_preparation.arrays(context)
        arrays = runner._native_array_preparation.raw_arrays(context)
        if runner.phase == "history":
            source = config.source
            work = preparation.initial_native_work(context, config, source, native_subwork.parent_contact)
            from .prepared_native_body import _execute_preparation_native
            product, raw = _execute_preparation_native(context, source, records["allocation"], arrays["initial-state"], native_subwork, work, progress=progress, prepared_initial=initial)
        elif runner.phase == "responses":
            raw, product = execute_future(context, config, records["history"], records["causal"], records["point"], records["mechanical"],
                arrays["initial-state"], arrays["history-arrays"], arrays["mechanical-arrays"], native_subwork, allocation=records["allocation"], progress=progress, prepared_arrays=(prefix, frozen))
        else:
            raise ValueError("selected nonnative phase cannot enter native subwork")
        return outputs(context, {"product": product}, raw)
    finally:
        runner._native_array_preparation.clear()
        for port in context.input_ports:
            port.close()

