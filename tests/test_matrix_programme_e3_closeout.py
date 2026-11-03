# SPDX-License-Identifier: MPL-2.0
"""Closeout programme construction from disclosed, unissued software premises."""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme import e3_closeout as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.retained_e3_continuation import MatrixProgrammeRetainedE3ContinuationSpecification
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    MatrixContinuedProgrammeSpecification, MatrixProgrammePhaseBinding, MatrixProgrammeRunBinding,
    MatrixResearchProgrammePlan, MatrixResearchProgrammeSpecification, PREPARATION_CONTEXT,
)
from empirical_lawhood.api.experiment_preparation import prepare_experiment
from empirical_lawhood.api.matrix_programme_retained_e3_continuation import _training_source
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_e3_cal_closeout import (  # noqa: F401
    closeout_case, unfinished_case, continuation_case, public_case,
)
from tests.test_matrix_programme_retained_training_continuation import retained_case, metadata_case  # noqa: F401


@pytest.fixture(scope='module')
def programme_closeout_case(closeout_case, retained_case):  # noqa: F811
    scope = closeout_case.scope
    previous = MatrixProgrammeRetainedE3ContinuationSpecification('request.disclosed-before-closeout',
        retained_case.request.predecessor, 'disclosed-before-closeout', scope.predecessor_run_id,
        scope.predecessor_reveal_authority.object_id)
    request = domain.MatrixProgrammeE3CloseoutSpecification('request.disclosed-programme-closeout',
        previous.predecessor, 'disclosed-programme-closeout', scope.retention.continued_run_id,
        scope.predecessor_reveal_authority.object_id)
    old_training = _training_source(retained_case.lineage, previous,
        scope.original_boundary.retention.response_provenance)
    training = _training_source(old_training, request, scope.retention.response_provenance)
    # This preparation binds the target request and compiler types only. Its
    # disclosed C is not a live closeout commitment; source/custody admission
    # must remain unresolved and no execution owner is invoked here.
    target = MatrixContinuedProgrammeSpecification('specification.disclosed-programme-closeout',
        request.directory, retained_case.commitment, retained_case.target.operations,
        request.predecessor, request.identity)
    prepared = prepare_experiment(target, execution=retained_case.case.execution)
    binding = ObjectIdentity('binding.disclosed-e3', MatrixProgrammePhaseBinding.SCHEMA,
        MatrixProgrammePhaseBinding.VERSION, 'a' * 64)
    run = ObjectIdentity('run.disclosed-e3', MatrixProgrammeRunBinding.SCHEMA,
        MatrixProgrammeRunBinding.VERSION, 'b' * 64)
    record = domain.MatrixProgrammeClosedE3Continuation('continuation.disclosed-programme-closeout',
        request, prepared.programme, retained_case.record.predecessor_bindings,
        retained_case.record.predecessor_terminals, binding, run, old_training, training,
        scope.retention, scope)
    return request, prepared, record


def test_closeout_request_prepares_and_decodes_its_exact_continued_programme(programme_closeout_case):
    request, prepared, record = programme_closeout_case
    assert type(prepared.programme) is MatrixResearchProgrammePlan
    assert prepared.programme.specification.continuation_request == request.identity
    assert not prepared.executable
    assert PREPARATION_CONTEXT in {row.code for row in prepared.dependencies}
    for value in (request, prepared.programme, record):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
    assert record.predecessor_reveal_authority == record.closeout.predecessor_reveal_authority
    assert type(record.retained_training) is domain.MatrixE3ClosedTrainingSource


@pytest.mark.parametrize('damage', ('request-schema', 'request-version', 'request-identity', 'directory'))
def test_closeout_programme_keeps_exact_request_guards(programme_closeout_case, damage):
    request, prepared, record = programme_closeout_case
    with pytest.raises((TypeError, ValueError)):
        if damage in ('request-schema', 'request-version'):
            changes = ({'object_schema': MatrixResearchProgrammeSpecification.SCHEMA}
                if damage == 'request-schema' else {'object_version': '99.0.0'})
            replace(prepared.programme.specification, continuation_request=replace(request.identity, **changes))
        elif damage == 'request-identity':
            changed = replace(prepared.programme.specification,
                continuation_request=replace(request.identity, object_id='request.disclosed-other'))
            replace(record, target_plan=replace(prepared.programme, specification=changed))
        else:
            replace(record, specification=replace(request, directory='disclosed-other-closeout'))
