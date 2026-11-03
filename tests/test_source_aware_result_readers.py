# SPDX-License-Identifier: MPL-2.0
"""Retained source-aware read controls; no scientific or execution authority.

The public E3 controls below disclose their package, reveal, plan and terminal
stubs. Dispatch, all five guarded typed product reads, original arithmetic and
the complete scientific projection are the production owners. The records come
from the existing exposed CAL20/CONF8 declaration fixture, not a new issue.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.domain_composition.matrix_protected_response import scientific_read as owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.results import ApiResult, CampaignStatusRequest, OperationStatus
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
from tests.test_matrix_e3_protected_scientific_read import (
    case as case, fitted as fitted, readout as readout, sequence as sequence,
)


def _literal_record(identity, **fields):
    """Disclosed control locator, never used for a scientific product."""
    return SimpleNamespace(SCHEMA=identity.object_schema, VERSION=identity.object_version,
        fingerprint=lambda: identity.object_fingerprint, **fields)


@pytest.fixture
def public_science(case, fitted, readout, sequence, monkeypatch, tmp_path):
    candidate = case.inputs.specification
    # The real full reader authenticates the original fitted model as well as
    # the four terminal products. The original-products view also consumes the
    # model freeze; both views share this complete six-task receipt census.
    retained_receipts = (fitted.models.receipt, fitted.frozen.receipt,
        sequence.calibration.receipt, sequence.sealed.receipt,
        sequence.assessment.receipt, readout.receipts[readout.adjudication.adjudication_task_id])
    tasks = tuple(SimpleNamespace(task_id=receipt.task_id) for receipt in retained_receipts)
    pin = readout.adjudication.execution_plan
    plan = _literal_record(pin, execution_plan_id=pin.object_id, tasks=tasks)
    terminal_pin = ObjectIdentity('terminal.literal.public-e3',
        'empirical-lawhood/testing/public-e3-terminal', '1.0.0', 'a' * 64)
    terminal = _literal_record(terminal_pin, terminal_event_id=terminal_pin.object_id)
    source = candidate.identity
    package = SimpleNamespace(run_plan_id=readout.adjudication.run_id,
        issued_study=SimpleNamespace(candidate=SimpleNamespace(candidate_id=candidate.identity.object_id,
            SCHEMA=candidate.SCHEMA, VERSION=candidate.VERSION, fingerprint=candidate.fingerprint),
            source_closure=source))
    selected = SimpleNamespace(instance=SimpleNamespace(specification=candidate.identity),
        association=SimpleNamespace(identity=candidate.identity, candidate=candidate.identity),
        implementation=source, projection=SimpleNamespace(tasks=tasks),
        handoff=SimpleNamespace(projection=SimpleNamespace(tasks=tasks)))
    receipts = {row.task_id: row for row in retained_receipts}
    gates = []

    def authorize(writer, supplied_package, reveal):
        gates.append('reveal')
        if reveal != 'authority.literal.explicit-public-e3-reveal':
            raise PermissionError('DISCLOSED_PUBLIC_E3_REVEAL_REQUIRED')
        assert writer is case.plane and supplied_package is package

    monkeypatch.setattr(owner, '_original_design', lambda _selected: (candidate, case.allocation))
    monkeypatch.setattr(owner, '_current_control', lambda **_arguments: package)
    monkeypatch.setattr(owner, '_authorize', authorize)
    monkeypatch.setattr(owner, 'authenticate_current_execution_plan', lambda **_arguments: plan)
    monkeypatch.setattr(owner, '_retained_scientific_writer', lambda *_arguments: readout.writer)
    monkeypatch.setattr(owner, '_completed_receipts', lambda *_arguments: (receipts, terminal))
    result = ApiResult('campaign.status', OperationStatus.SUCCEEDED)
    monkeypatch.setattr(ExperimentProgrammeService, '_prospective_context',
        lambda *args, **kwargs: (selected, SimpleNamespace(campaign_status=lambda *args, **kwargs: result)))
    programme = ExperimentProgrammeService(tmp_path, case.plane)

    def read(reveal='authority.literal.explicit-public-e3-reveal'):
        return programme.read(directory=tmp_path, request=CampaignStatusRequest(package.run_plan_id),
            reveal_authority_id=reveal)['scientific_result']

    return SimpleNamespace(read=read, gates=gates, receipts=receipts, plan=plan, selected=selected, package=package)


def test_public_e3_dispatch_reads_all_five_typed_products_and_complete_adverse_rows(public_science, case, readout, sequence, monkeypatch):
    calls = []
    original = owner._product

    def observed(*arguments):
        calls.append(arguments[4])
        return original(*arguments)

    monkeypatch.setattr(owner, '_product', observed)
    report = public_science.read()
    assert calls == [owner.ProtectedE3ModelSet, owner.ProtectedE3Calibration,
        owner.ProtectedE3FrozenProducts, owner.ProtectedE3Assessment, owner.ScientificAdjudicationRecord]
    assert public_science.gates == ['reveal', 'reveal']
    assert set(report['custody']) == {'models', 'calibration', 'calibrated_freeze', 'assessment', 'adjudication'}
    assert report['calibration'] == readout.calibration.to_document()
    assert report['assessment'] == readout.assessment.to_document()
    assert report['adjudication'] == readout.adjudication.to_document()
    assert report['denominators']['calibration']['assigned_units'] == 20
    assert report['denominators']['confirmation'] == {'assigned_units': 8, 'usable_units': 7,
        'successes': sequence.assessment.record.successes, 'units': list(case.allocation.unit_ids('evaluation'))}
    assert 'UNKNOWN_CONTACT' in report['assessment']['value']['decisions'][-1]['value']['reasons']
    assert report['scientific_status'] == report['admission_status'] == 'UNEVALUABLE'
    assert report['qualification'] == 'NOT_ESTABLISHED'
    assert report['completed_tasks'] == 6 and report['typed_product_validation'] == 'COMPLETE'
    assert report['scientific_completion'] == 'RETAINED_ADJUDICATION' and report['native_contact'] == 'none'


def test_public_e3_reveal_denial_precedes_any_typed_product_read(public_science, monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError('reveal denial reached scientific payload')

    monkeypatch.setattr(owner, '_product', forbidden)
    with pytest.raises(PermissionError, match='DISCLOSED_PUBLIC_E3_REVEAL_REQUIRED'):
        public_science.read(None)


@pytest.mark.parametrize('product', ('models', 'calibration', 'sealed', 'assessment'))
@pytest.mark.parametrize('damage', ('missing', 'tampered'))
def test_public_e3_full_reader_refuses_missing_or_changed_original_product(public_science, fitted, sequence, case, product, damage):
    publication = (fitted.models if product == 'models' else getattr(sequence, product)).publication
    path = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        if damage == 'missing':
            path.unlink()
        else:
            path.write_bytes(raw + b' ')
        with pytest.raises((OSError, ValueError, ArtifactIdentityConflict)):
            public_science.read()
    finally:
        path.write_bytes(raw)


def test_public_e3_guarded_typed_freeze_cannot_substitute_original_model(public_science, sequence, case):
    original = sequence.sealed
    changed = replace(original.record, models=replace(original.record.models, object_fingerprint='c' * 64))
    logical = original.publication.logical
    publication = case.plane.write(ArtifactWriteRequest('product.literal.reader-foreign-model',
        'reader-control/foreign-model.json', changed.SCHEMA, logical.profile, logical.media_type,
        'reader-control.foreign-model', 'reader-control', changed.canonical_bytes(),
        logical.visibility_ceiling, logical.parent_visibility_ceilings, logical.outcome_access,
        semantic_validation=logical.semantic_validation))
    public_science.receipts[original.receipt.task_id] = replace(original.receipt,
        output_logical_artifacts=(publication.logical,), output_materializations=(publication.materialization,))
    with pytest.raises(PermissionError, match='COMPLETE_CALIBRATION_AND_FREEZE'):
        public_science.read()


def _original_product_read(public_science, case):
    return owner._read_protected_e3_result(
        selected=public_science.selected, artifact_writer=case.plane,
        run_id=public_science.package.run_plan_id,
        reveal_authority_id="authority.literal.explicit-public-e3-reveal",
        expected_package=public_science.package, include_original_products=True)


def _include_original_receipts(public_science, fitted):
    public_science.receipts.update({
        fitted.models.receipt.task_id: fitted.models.receipt,
        fitted.frozen.receipt.task_id: fitted.frozen.receipt,
    })


def test_one_call_shares_exact_original_products_and_report_without_second_closure(
        public_science, case, fitted, readout, monkeypatch):
    """Disclosed orchestration stubs; actual guarded typed products/math.

    This is not a genuine issue/source/grant acceptance. The separately held
    actual-E3 test supplies those owners without these explicit control stubs.
    """
    _include_original_receipts(public_science, fitted)
    expected = public_science.read()
    calls = []
    plan = owner.authenticate_current_execution_plan
    closure = owner._completed_receipts
    product = owner._product

    def observed_plan(**kwargs):
        calls.append("plan")
        return plan(**kwargs)

    def observed_closure(*args):
        calls.append("closure")
        return closure(*args)

    def observed_product(*args):
        calls.append(("product", args[-1]))
        return product(*args)

    monkeypatch.setattr(owner, "authenticate_current_execution_plan", observed_plan)
    monkeypatch.setattr(owner, "_completed_receipts", observed_closure)
    monkeypatch.setattr(owner, "_product", observed_product)
    result = _original_product_read(public_science, case)
    assert result.report == expected
    assert calls.count("plan") == calls.count("closure") == 1
    assert len([row for row in calls if type(row) is tuple]) == 7
    assert result.models.canonical_bytes() == fitted.models.record.canonical_bytes()
    assert result.model_freeze.canonical_bytes() == fitted.frozen.record.canonical_bytes()
    assert result.prefit.canonical_bytes() == fitted.joined.record.canonical_bytes()
    assert result.calibration.canonical_bytes() == readout.calibration.canonical_bytes()
    assert result.calibrated_freeze.canonical_bytes() == readout.frozen.canonical_bytes()
    assert result.execution_plan is public_science.plan and result.package is public_science.package
    with pytest.raises(TypeError):
        result.receipts["foreign"] = fitted.models.receipt
    assert not hasattr(result, "writer")
    before = len(public_science.gates)
    _original_product_read(public_science, case)
    assert len(public_science.gates) == before + 2 and calls.count("closure") == 2


@pytest.mark.parametrize("damage", ("package", "source", "execution", "reveal", "receipt"))
def test_shared_read_retains_every_fresh_control_refusal_before_typed_products(
        public_science, case, monkeypatch, damage):
    package = public_science.package
    expected = package

    def refused(*_args, **_kwargs):
        raise PermissionError("DISCLOSED_FRESH_" + damage.upper() + "_REFUSAL")

    if damage == "package":
        expected = object()
    elif damage == "source":
        changed = SimpleNamespace(**vars(package))
        changed.issued_study = SimpleNamespace(**vars(package.issued_study))
        changed.issued_study.source_closure = case.allocation.identity
        monkeypatch.setattr(owner, "_current_control", lambda **_kwargs: changed)
        expected = changed
    elif damage == "execution":
        monkeypatch.setattr(owner, "authenticate_current_execution_plan", refused)
    elif damage == "reveal":
        monkeypatch.setattr(owner, "_authorize", refused)
    else:
        monkeypatch.setattr(owner, "_completed_receipts", refused)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("fresh control refusal reached a protected typed product")

    monkeypatch.setattr(owner, "_product", forbidden)
    with pytest.raises(PermissionError):
        owner._read_protected_e3_result(selected=public_science.selected, artifact_writer=case.plane,
            run_id=package.run_plan_id, reveal_authority_id="authority.literal.explicit-public-e3-reveal",
            expected_package=expected, include_original_products=True)


@pytest.mark.parametrize("damage", ("missing", "changed"))
def test_shared_original_products_keep_actual_guarded_payload_refusals(
        public_science, case, fitted, damage):
    _include_original_receipts(public_science, fitted)
    path = case.plane.root.resolve(fitted.models.publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        if damage == "missing":
            path.unlink()
        else:
            path.write_bytes(raw + b" ")
        with pytest.raises((OSError, ValueError, ArtifactIdentityConflict)):
            _original_product_read(public_science, case)
    finally:
        path.write_bytes(raw)


def test_public_original_products_reject_untyped_package_before_any_io():
    class NoIO:
        def verification_scope(self):
            raise AssertionError("untyped expected package reached custody")

    with pytest.raises(PermissionError, match="EXACT_EXPECTED_PACKAGE_REQUIRED"):
        owner.read_protected_e3_original_products(selected=object(), artifact_writer=NoIO(),
            run_id="run.literal", expected_package=object(), reveal_authority_id="authority.literal")


def test_shared_original_product_wrapper_preserves_core_bounded_scope_ownership(monkeypatch):
    """Disclosed wrapper control; all real grant/payload controls remain above."""
    class SelectedPackage:
        run_plan_id = "run.literal.bounded-original-read"

    class NoOuterSnapshot:
        def verification_scope(self):
            raise AssertionError("whole-run wrapper retained every receipt snapshot")

    package, writer, result = SelectedPackage(), NoOuterSnapshot(), object()
    calls = []

    def core(**arguments):
        calls.append(arguments)
        return result

    monkeypatch.setattr(owner, "ExperimentPackage", SelectedPackage)
    monkeypatch.setattr(owner, "_read_protected_e3_result", core)
    actual = owner.read_protected_e3_original_products(selected="selected", artifact_writer=writer,
        run_id=package.run_plan_id, expected_package=package, reveal_authority_id="authority.literal.reveal")
    assert actual is result
    assert calls == [dict(selected="selected", artifact_writer=writer, run_id=package.run_plan_id,
        expected_package=package, reveal_authority_id="authority.literal.reveal", include_original_products=True)]
