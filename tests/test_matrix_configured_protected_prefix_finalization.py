# SPDX-License-Identifier: MPL-2.0
"""Current configured prefix assembly over disclosed completed software records."""

from dataclasses import replace

from hashlib import sha256




from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_bindings as original


from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import ConfiguredProtectedE3PrefixHistory

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledCheckpoint

from empirical_lawhood.infrastructure.execution import prepare_worker_invocation

from empirical_lawhood.kernel.decoding import decode_canonical_bytes

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling

from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA

from empirical_lawhood.kernel.provenance import ObjectIdentity

from empirical_lawhood.kernel.status import OperationalStatus

from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt

from empirical_lawhood.runtime.execution import RunnerResult

from empirical_lawhood.runtime.native_subwork import NativeSubworkInspection, NativeSubworkState

from tests import test_matrix_configured_protected_prefix_worker_routing as literal

from tests.native_completion_fixtures import publish_completion

from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane

configured_prefix_case = literal.configured_prefix_case

legacy_case = literal.legacy_case

original_case = literal.original_case

forbid_native = literal.forbid_native

class _RetainedReader:
    """Explicit read-only SOFTWARE fixture; storage authentication stays outside."""

    def __init__(self, definition, inspection, payloads):
        self.definition, self.inspection, self.payloads = definition, inspection, payloads
        self.calls = []

    @property
    def parent_contact(self):
        return self.definition.parent_contact

    def recover(self, definition):
        assert definition == self.definition
        self.calls.append(('recover', definition.identity))
        return self.inspection

    def iter_completed_output(self, definition, output_id, *, maximum_chunk_bytes=1024 * 1024):
        assert definition == self.definition
        self.calls.append(('output', output_id))
        if output_id not in self.payloads:
            raise FileNotFoundError('disclosed missing retained ' + output_id)
        raw = self.payloads[output_id]
        # Deliberately split the retained archive; never decode or reencode it.
        size = min(8191, maximum_chunk_bytes)
        return iter(raw[index:index + size] for index in range(0, len(raw), size))

    def __getattr__(self, name):
        pytest.fail('completed prefix forwarded a forbidden native/mutation method: ' + name)

@pytest.fixture
def retained_prefix(configured_prefix_case, tmp_path):
    case = configured_prefix_case
    plane = _matrix_plane(tmp_path / 'literal-retained-prefix')
    selected = literal._configured_native_direct_inputs(case, plane)
    contract = prepare_worker_invocation(selected.runner, selected.context,
        selected.bundle.verified_inputs, implementation=selected.implementation,
        execution_plan=selected.plan,
        execution_task=ObjectIdentity.from_record(selected.task.task_id, selected.task),
        execution_task_record=selected.task, native_effect=True,
        native_work_preparer=selected.declaration.execution_properties.native_work_preparer)
    assert contract.native_preparation_error is None
    definition, = contract.native_work.definitions
    parent = definition.parent_contact
    task = 'native-subwork.' + sha256((parent.task_id + ':' + definition.subwork_id).encode()).hexdigest()
    checkpoint = case.history.checkpoint
    assert checkpoint.prefix_arrays.artifact_id == task + '.output.arrays'
    payloads = {'arrays': case.native_raw, 'checkpoint': checkpoint.canonical_bytes()}
    publications = []
    for name, schema, profile, media in (
            ('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),
            ('checkpoint', ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json')):
        publications.append(plane.write(ArtifactWriteRequest(task + '.output.' + name,
            'literal-completed-prefix/' + name, schema, profile, media,
            'literal-completed-prefix', 'literal-completed-prefix', payloads[name],
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)))
    completion = replace(case.history.native.completion, definition=definition.identity)
    attempt = parent.run_id + '.' + task + '.attempt-001'
    receipt = CanonicalTaskReceipt('receipt.' + attempt, parent.run_id, task, attempt,
        parent.implementation_commit, parent.input_materialization_ids,
        tuple(row.materialization for row in publications), tuple(row.logical for row in publications),
        (), OperationalStatus.SUCCEEDED, ())
    receipt = publish_completion(plane, receipt, completion,
        visibility=VisibilityCeiling.PROSPECTIVE, access=OutcomeAccess.OUTCOME_BLIND)
    inspection = NativeSubworkInspection(definition, NativeSubworkState.COMPLETED,
        completion=completion, receipt=receipt)

    def context():
        ports = plane.open_many(selected.bundle.verified_inputs,
            bindings=selected.context.input_bindings, maximum_bytes=None)
        return replace(selected.context, input_ports=ports, prepared_invocation=contract)

    def reader():
        return _RetainedReader(definition, inspection, dict(payloads))

    try:
        yield SimpleNamespace(case=case, definition=definition, context=context, reader=reader,
            inspection=inspection, payloads=payloads, contract=contract)
    finally:
        selected.bundle.close()


def test_completed_configured_prefix_assembles_exact_retained_bytes_without_native(retained_prefix):
    case = retained_prefix
    reader = case.reader()
    result = original.ConfiguredProtectedE3PrefixRunner().execute_with_native_subwork(
        case.context(), reader)
    assert type(result) is RunnerResult
    assert [row[0] for row in reader.calls] == ["recover", "output", "output"]
    outputs = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
    assert outputs["arrays"] == case.payloads["arrays"]
    assert outputs["checkpoint"] == case.payloads["checkpoint"]
    product = decode_canonical_bytes(outputs["product"], ConfiguredProtectedE3PrefixHistory, maximum_bytes=None)
    assert type(product) is ConfiguredProtectedE3PrefixHistory
    assert product.native.definition == case.definition
    assert product.native.completion == case.inspection.completion
    assert product.native.receipt == case.inspection.receipt
    assert product.checkpoint.generators == case.case.history.checkpoint.generators
    assert not set(product.native.completion.consumed_streams).intersection(product.native.completion.unconsumed_streams)
    assert set((*product.native.completion.consumed_streams, *product.native.completion.unconsumed_streams)) == set(case.definition.streams)
