# SPDX-License-Identifier: MPL-2.0
"""Reference-delivery controls over real publications; no native qualification.

The small owner reports below are disclosed orchestration fixtures. They test
delivery custody and refusal ordering, not the scientific E1–E6 lifecycle.
"""
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import (
    PHASES, MatrixProgrammeObservation, programme_frontier,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.product_export import MatrixProgrammeProductExportSelection
from empirical_lawhood.adapters.methods.matrix_researcher_programme.product_export import MatrixProgrammePortableProductExportSelection
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixResearchProgrammePlan
from empirical_lawhood.api import matrix_programme_products as delivery
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeE3Originals
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_recursive_public_service import ROOT, _plane
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_current_result_historical_access import LaterClock


def _pin(name, schema):
    return ObjectIdentity(name, schema, '1.0.0', 'a' * 64)


class _DeliveryControlOwner(MatrixResearchProgrammeService):
    def _plan(self, directory):
        return self._control.plan

    def _request(self, plan, path):
        return None

    @contextmanager
    def _context(self, plan, *, operation=None):
        context = SimpleNamespace(plan=plan, writer=self.writer, bindings=self._control.bindings,
            observations={}, pending_bindings={}, design=self._control.design,
            phase_origins={}, continuation_records=[], amendment_records=[])
        if hasattr(self._control, 'authority'):
            context.authority = self._control.authority
        if hasattr(self._control, 'e3_originals'):
            context.e3_originals = self._control.e3_originals
        if hasattr(self._control, 'require_original_access'):
            context.require_original_access = self._control.require_original_access
        yield context

    def _observe(self, context, *, allow_partial=False, phases=PHASES, reports=None):
        for path in self._control.sources:
            self.writer.verify_manifest(self.writer.read_manifest(path))
        for phase in phases:
            if phase in self._control.observations:
                original = self._control.observations[phase]
                context.observations[phase] = (original if reports is None or phase not in reports
                    else replace(original, report=reports[phase]))

    def _read_phase(self, context, phase, *, execution_only=False, **kwargs):
        if execution_only:
            for path in self._control.sources:
                self.writer.verify_manifest(self.writer.read_manifest(path))
            return {'read_scope': 'EXECUTION_RECORDS', 'execution_complete': True,
                'status': 'SUCCEEDED', 'phase': phase}
        return super()._read_phase(context, phase, execution_only=execution_only, **kwargs)


@pytest.fixture
def case(tmp_path):
    return _delivery_case(_plane(tmp_path / 'guarded'))


def _delivery_case(plane):
    root = Path(plane.root.contract.canonical_path)
    product = Config('science.disclosed-adverse', 17)
    path = 'runs/run.disclosed/outputs/task.disclosed/product.json'
    published = plane.write(ArtifactWriteRequest('artifact.disclosed.product', path, product.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed-product',
        str(Path(path).parent), product.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE))
    receipt = CanonicalTaskReceipt('receipt.run.disclosed.task.disclosed.attempt-001',
        'run.disclosed', 'task.disclosed', 'run.disclosed.task.disclosed.attempt-001', 'a' * 40,
        (), (published.materialization,), (published.logical,), (), OperationalStatus.SUCCEEDED, ())
    receipt_publication = ExternalTaskReceiptStore(plane).commit(receipt,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    plan_pin = ObjectIdentity('plan.disclosed-delivery-control', MatrixResearchProgrammePlan.SCHEMA,
        MatrixResearchProgrammePlan.VERSION, 'b' * 64)
    plan = SimpleNamespace(identity=plan_pin, specification=SimpleNamespace(input_commitments=SimpleNamespace(
        record=_pin('c.disclosed-unwritten', 'empirical-lawhood/testing/disclosed-c'))))
    design = SimpleNamespace(identity=_pin('d.disclosed-unwritten', 'empirical-lawhood/testing/disclosed-d'),
        downstream_account='ORIGINAL_E3', e4_structure=SimpleNamespace(prediction=None))
    report = {'run_id': 'run.disclosed', 'status': OperationalStatus.SUCCEEDED,
        'scientific_result': {'scientific_status': 'PRIMARY_NONSUCCESS', 'qualification': 'NOT_ESTABLISHED',
            'denominators': {'groups': {'assigned_units': 4, 'successes': 0}}}}
    service = ExperimentProgrammeService(ROOT, plane)
    # Dataclass replacement keeps only declared fields. Put fixture data on the
    # control owner class rather than changing the production service contract.
    _DeliveryControlOwner._control = SimpleNamespace(plan=plan, design=design,
        bindings={'e2': SimpleNamespace(identity=_pin('binding.disclosed', 'empirical-lawhood/testing/disclosed-binding'))},
        sources=(path, receipt_publication.materialization.relative_path),
        observations={'e2': MatrixProgrammeObservation('e2', report, True)})
    directory = root / 'programme'
    directory.mkdir()
    selection = MatrixProgrammeProductExportSelection('export.disclosed-control', plan_pin, 'exports/current')
    selection_path = root / 'selection.json'
    selection_path.write_bytes(selection.canonical_bytes())
    return SimpleNamespace(plane=plane, root=root, product=published, receipt=receipt,
        receipt_publication=receipt_publication, plan=plan, report=report, service=service,
        owner=_DeliveryControlOwner(service=service), directory=directory,
        selection=selection, selection_path=selection_path)


def test_export_keeps_exact_reports_products_receipts_and_complete_missing_phase_census(case):
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    before = {path: path.read_bytes() for path in (case.root / 'runs').rglob('*') if path.is_file()}
    with scientific_reconstruction_operation('full'):
        actual = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert actual['phase_count'] == len(PHASES) and actual['observed_phase_count'] == 1
    assert actual['scientific_product_count'] == 1 and actual['new_native_contact_count'] == 0
    document = json.loads(Path(actual['path']).read_bytes())['value']
    assert tuple(row['phase'] for row in document['phase_census']) == PHASES
    assert len([row for row in document['phase_census'] if row['observation'] == 'NOT_OBSERVED']) == len(PHASES) - 1
    product, = document['scientific_products']
    reference, = (row for row in document['evidence_references'] if row['relative_path'] == product['reference'])
    original_manifest = case.plane.read_manifest(product['reference'])
    assert reference['manifest'] == json.loads(original_manifest.canonical_bytes())
    assert product['manifest'] == json.loads(ObjectIdentity.from_record(
        'manifest.' + original_manifest.fingerprint(), original_manifest).canonical_bytes())
    assert original_manifest.materialization == case.product.materialization
    assert 'materialization' not in product and 'logical_artifact' not in product
    receipt, = document['producing_receipts']
    assert receipt['record'] == json.loads(case.receipt.canonical_bytes())
    readout = document['programme_readout']
    assert 'input_commitments' not in document and 'scientific_design' not in document
    assert readout['report']['input_commitments'] == json.loads(case.plan.specification.input_commitments.record.canonical_bytes())
    assert readout['report']['prospective_amendments'] == []
    assert readout['report']['phases'][0]['report'] == case.report
    encoded = canonical_json_document_bytes(readout['report'])
    assert (readout['encoded_report_size_bytes'], readout['encoded_report_sha256']) == (len(encoded), sha256(encoded).hexdigest())
    phase, = document['phase_readouts']
    encoded_phase = canonical_json_document_bytes(case.report)
    assert phase == {'phase': 'e2', 'encoded_report_size_bytes': len(encoded_phase),
        'encoded_report_sha256': sha256(encoded_phase).hexdigest()}
    assert not (case.root / 'exports/current/e2.report.json').exists()
    assert not (case.root / 'exports/current/programme-report.json').exists()
    assert document['delivery_mode'] == 'ORIGINAL_CUSTODY_REFERENCES_NO_ARRAY_DUPLICATION'
    assert document['original_artifact_root'] == json.loads(case.plane.root.contract.canonical_bytes())
    manifest = case.plane.read_manifest('exports/current/products.json')
    assert manifest.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert manifest.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert {path: path.read_bytes() for path in before} == before
    with scientific_reconstruction_operation('full'):
        repeated = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert repeated['path'] == actual['path']
    assert all(not row['value']['created'] for row in repeated['publications'])


@pytest.mark.parametrize('extra_members', (0, 6))
@pytest.mark.parametrize('portable', (False, True))
def test_e3_export_full_snapshot_count_does_not_grow_with_member_count(case, monkeypatch, extra_members, portable):
    calls = {'snapshot': 0, 'access': 0}
    def snapshot():
        calls['snapshot'] += 1
    def access():
        calls['access'] += 1
    @contextmanager
    def originals():
        yield MatrixProgrammeE3Originals(None, None, None, None, None, None, (), snapshot, access)
    control = case.owner._control
    control.e3_originals = originals
    control.bindings['e3'] = SimpleNamespace(identity=_pin('binding.e3-disclosed', 'empirical-lawhood/testing/disclosed-binding'))
    control.observations['e3'] = MatrixProgrammeObservation('e3', case.report, True)
    monkeypatch.setattr(delivery, '_current_grants', lambda *args: access)
    for index in range(extra_members):
        record = Config(f'metadata.{index}', index)
        path = f'extra/{index}/record.json'
        case.plane.write(ArtifactWriteRequest(f'metadata.{index}', path, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', f'publication.metadata.{index}',
            f'extra/{index}', record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (),
            OutcomeAccess.DEVELOPMENT_VISIBLE))
        control.sources += (path,)
    if portable:
        _select_portable(case)
    case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert calls['snapshot'] == (5 if portable else 3)
    assert calls['access'] > calls['snapshot']


@pytest.mark.parametrize('damage', ('foreign-plan', 'inside-programme', 'ancestor', 'noncanonical'))
def test_invalid_delivery_selection_refuses_before_publication(case, damage):
    selection = case.selection
    if damage == 'foreign-plan':
        selection = replace(selection, programme=replace(selection.programme, object_fingerprint='c' * 64))
    elif damage == 'inside-programme':
        selection = replace(selection, output_relative_path='programme/export')
    elif damage == 'ancestor':
        selection = replace(selection, output_relative_path='programme')
    raw = selection.canonical_bytes()
    case.selection_path.write_bytes(raw + b' ' if damage == 'noncanonical' else raw)
    with pytest.raises((ValueError, PermissionError), match='original programme|closed original|canonical'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert not (case.root / 'exports').exists()


@pytest.mark.parametrize('moment', ('before-publication', 'after-publication'))
def test_late_same_size_original_product_change_refuses_final_success(case, monkeypatch, moment):
    original = delivery._require_snapshot
    target = case.root / case.product.materialization.relative_path
    calls = []
    def changed(*args):
        calls.append(1)
        if len(calls) == (1 if moment == 'before-publication' else 2):
            raw = target.read_bytes()
            target.write_bytes(raw.replace(b'17', b'18'))
        return original(*args)
    monkeypatch.setattr(delivery, '_require_snapshot', changed)
    with pytest.raises((PermissionError, ArtifactIdentityConflict), match='bytes differ|evidence bytes|changed'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert (case.root / 'exports/current/products.json').exists() is (moment == 'after-publication')


@pytest.mark.parametrize('moment', ('before-publication', 'after-publication'))
@pytest.mark.parametrize('change', ('expiry', 'revocation'))
def test_actual_stored_grant_change_at_final_publication_refuses_success(
        actual_issued_current_task_controls, monkeypatch, moment, change):  # noqa: F811
    """Actual stored test grants exercise access, not E5 scientific ancestry.

    The report/phase adapter remains a disclosed orchestration fixture. The
    production export guard reloads the actual issue/execution/reveal binding
    through its ordinary store and UTC validator at the publication boundary.
    """
    from empirical_lawhood.api import recursive_qualified_parents as authority_owner

    f = actual_issued_current_task_controls
    case = _delivery_case(f.control.service.artifact_plane)
    control = case.owner._control
    phase = 'e5.confirmation'
    control.observations[phase] = MatrixProgrammeObservation(phase, {'status': OperationalStatus.SUCCEEDED}, False)
    control.bindings[phase] = SimpleNamespace(identity=_pin('binding.disclosed-access',
        'empirical-lawhood/testing/disclosed-binding'))
    control.authority = lambda selected, component=None: (None, None,
        SimpleNamespace(reveal_authority_id=f.control.reveal.authority_id), f.control.package, None, None)
    original_load, original_snapshot = ExternalStudyOperationAuthorityStore.load, delivery._require_snapshot
    boundary = {'changed': False, 'calls': 0}
    loads = []
    def load(store, authority_id):
        if authority_id == f.control.reveal.authority_id:
            loads.append(boundary['changed'])
            if boundary['changed'] and change == 'revocation':
                raise PermissionError('stored publication grant revoked')
        return original_load(store, authority_id)
    def snapshot(*args):
        boundary['calls'] += 1
        if boundary['calls'] == (1 if moment == 'before-publication' else 2):
            boundary['changed'] = True
            if change == 'expiry':
                monkeypatch.setattr(authority_owner, 'datetime', LaterClock)
        return original_snapshot(*args)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', load)
    monkeypatch.setattr(delivery, '_require_snapshot', snapshot)
    with pytest.raises(PermissionError, match='expired|revoked'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert False in loads and True in loads
    assert (case.root / 'exports/current/products.json').exists() is (moment == 'after-publication')


def test_complete_phase_census_preserves_conditional_nonentry_and_adverse_nomination():
    skipped = {'e4.source-cal', 'e4.calibration', 'e5.initialize-confirmation', 'e5.source', 'e5.confirmation'}
    observations = {phase: MatrixProgrammeObservation(phase, {'status': 'SUCCEEDED'}, True,
        'UNEVALUABLE' if phase == 'e4.revision' else None,
        'NONDISCRIMINATING_OPPORTUNITY' if phase == 'e5.development' else None)
        for phase in PHASES if phase not in skipped}
    context = SimpleNamespace(observations=observations, bindings={}, pending_bindings={},
        design=SimpleNamespace(downstream_account='ORIGINAL_E3'))
    frontier = programme_frontier(observations, downstream_account=context.design.downstream_account)
    rows = {row['phase']: row for row in delivery._phase_census(context,
        {'eligible': frontier.eligible, 'unentered': frontier.unentered, 'waiting': frontier.waiting})}
    assert rows['e4.calibration']['observation'] == 'UNENTERED_REVISION_UNEVALUABLE'
    assert rows['e5.confirmation']['observation'] == 'UNENTERED_E5_NONDISCRIMINATING_OPPORTUNITY'
    assert rows['e6']['operational_completion']
    assert not any(rows[phase]['operational_completion'] for phase in skipped)


def test_export_selection_is_closed_canonical_operational_configuration():
    path = ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/product-export.example.json'
    selected = decode_canonical_bytes(path.read_bytes(), MatrixProgrammeProductExportSelection, maximum_bytes=1024**2)
    assert selected.canonical_bytes() == path.read_bytes()
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.extension_bundle import EXPERIMENT_PROTOCOL_DECLARATIONS
    declaration, = (value for value in EXPERIMENT_PROTOCOL_DECLARATIONS
        if value.protocol_id == 'matrix.researcher-programme.v2')
    config, = (row for row in declaration.configuration_inputs if row.consumer_id == 'matrix-programme-product-export')
    assert config.record_type is MatrixProgrammeProductExportSelection
    for path in ('..', '/absolute', '.', 'exports/../escape'):
        with pytest.raises(ValueError):
            replace(selected, output_relative_path=path)


def _select_portable(case):
    target = case.root.parent / 'portable'
    target.mkdir()
    mount = next(path for path in target.parents if path.is_mount())
    contract = replace(case.plane.root.contract, canonical_path=str(target), required_mount_path=str(mount))
    selection = MatrixProgrammePortableProductExportSelection('export.disclosed-portable',
        case.plan.identity, 'exports/portable-reference', contract,
        str(case.root.parent / 'portable-receipt.json'), 10 * 1024**2, 100)
    case.selection_path.write_bytes(selection.canonical_bytes())
    return selection, target


@pytest.mark.parametrize('portable', (False, True))
def test_full_report_and_delivery_share_one_authenticated_observation(case, monkeypatch, portable):
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    observed = []
    original = _DeliveryControlOwner._observe
    def observe(owner, context, **kwargs):
        observed.append(context)
        return original(owner, context, **kwargs)
    monkeypatch.setattr(_DeliveryControlOwner, '_observe', observe)
    if portable:
        _select_portable(case)
    with scientific_reconstruction_operation('full'):
        result = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert len(observed) == 1
    body = json.loads(Path(result['path']).read_bytes())
    locator = result['programme_readout']
    report = body
    for component in locator['json_pointer'].split('/')[1:]:
        report = report[component]
    assert report['scientific_reconstruction'] == locator['scientific_reconstruction'] == 'full'
    assert report['read_scope'] == locator['read_scope'] == 'FULL'
    assert report['state'] == locator['state'] == 'IN_PROGRESS'
    assert report['phases'][0]['report'] == case.report
    encoded = canonical_json_document_bytes(report)
    assert (len(encoded), sha256(encoded).hexdigest()) == (
        locator['encoded_report_size_bytes'], locator['encoded_report_sha256'])
    assert (result['portable_replica'] is not None) is portable


def test_completed_phase_survives_delivery_failure_and_resumes_without_scientific_read(case, monkeypatch):
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    original = delivery._receipt_products
    def interrupted(*args, **kwargs):
        raise InterruptedError('disclosed failure after scientific reconstruction')
    monkeypatch.setattr(delivery, '_receipt_products', interrupted)
    with scientific_reconstruction_operation('full'), pytest.raises(InterruptedError):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    checkpoint = case.root / 'exports/current/checkpoints/e2.json'
    assert json.loads(checkpoint.read_bytes())['value']['export_status'] == 'IN_PROGRESS'
    assert not (case.root / 'exports/current/products.json').exists()
    monkeypatch.setattr(delivery, '_receipt_products', original)
    observe = _DeliveryControlOwner._observe
    def resumed(owner, context, **kwargs):
        assert kwargs['reports']['e2'] == case.report
        return observe(owner, context, **kwargs)
    monkeypatch.setattr(_DeliveryControlOwner, '_observe', resumed)
    with scientific_reconstruction_operation('full'):
        result = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert result['reused_export_stages'] == ('e2',)
    actual = json.loads(Path(result['path']).read_bytes())['value']['programme_readout']['report']
    assert actual['phases'][0]['report'] == case.report


@pytest.mark.parametrize('damage', ('none', 'execution', 'body'))
def test_saved_report_finalization_opens_recorded_context_and_never_calls_phase_reader(case, monkeypatch, damage):
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
    from empirical_lawhood.runtime.operational_configuration import (
        scientific_reconstruction_enabled, scientific_reconstruction_operation,
    )

    report = {**case.report, 'scientific_result': {**case.report['scientific_result'],
        'scientific_completion': 'COMPLETE_NATIVE_UTILITY_ASSESSMENT'}}
    case.owner._control.observations['e2'] = MatrixProgrammeObservation('e2', report, True)
    opened = []
    # The report/census are disclosed seams. Use the real projection type so
    # this tests the new transport branch, including context mode at exit.
    @contextmanager
    def context(owner, plan, *, operation=None):
        selected_mode = scientific_reconstruction_enabled()
        opened.append(selected_mode)
        yield MatrixProgrammeProjectionContext(owner.service, plan,
            SimpleNamespace(scientific_design=owner._control.design), case.directory,
            owner._control.bindings, {}, operation)
        assert scientific_reconstruction_enabled() is selected_mode
    monkeypatch.setattr(_DeliveryControlOwner, '_context', context)
    ordinary = delivery._receipt_products
    def interrupt(*args, **kwargs):
        raise InterruptedError('completed report retained before delivery')
    monkeypatch.setattr(delivery, '_receipt_products', interrupt)
    with scientific_reconstruction_operation('full'), pytest.raises(InterruptedError):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    checkpoint = case.root / 'exports/current/checkpoints/e2.json'
    original_bytes = checkpoint.read_bytes()
    monkeypatch.setattr(delivery, '_receipt_products', ordinary)
    monkeypatch.setattr(_DeliveryControlOwner, '_observe',
        lambda *args, **kwargs: pytest.fail('saved report reopened its scientific reader'))
    execution = _DeliveryControlOwner._read_phase
    def read(owner, context, phase, *, execution_only=False, **kwargs):
        assert execution_only and not scientific_reconstruction_enabled()
        result = execution(owner, context, phase, execution_only=True, **kwargs)
        return {**result, 'changed': True} if damage == 'execution' else result
    monkeypatch.setattr(_DeliveryControlOwner, '_read_phase', read)
    if damage == 'body':
        checkpoint.write_bytes(original_bytes + b' ')
    with scientific_reconstruction_operation('full'):
        if damage == 'none':
            result = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
            saved = json.loads(Path(result['path']).read_bytes())['value']['programme_readout']['report']
            assert saved['phases'][0]['report'] == report
            assert result['reused_export_stages'] == ('e2',)
            assert checkpoint.read_bytes() == original_bytes
        else:
            with pytest.raises((PermissionError, ArtifactIdentityConflict)):
                case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
            assert not (case.root / 'exports/current/products.json').exists()
    assert opened == [True, False]


@pytest.mark.parametrize('damage', ('binding', 'execution', 'execution-census', 'checkpoint', 'source'))
def test_phase_checkpoint_refuses_substitution(case, monkeypatch, damage):
    from empirical_lawhood.api import matrix_programme_export_checkpoints as checkpoints
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    with scientific_reconstruction_operation('full'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    if damage == 'binding':
        case.owner._control.bindings['e2'] = SimpleNamespace(identity=_pin('binding.changed', 'empirical-lawhood/testing/changed'))
    elif damage == 'execution':
        monkeypatch.setattr(_DeliveryControlOwner, '_read_phase', lambda *args, **kwargs:
            {'read_scope': 'EXECUTION_RECORDS', 'execution_complete': False})
    elif damage == 'execution-census':
        read = _DeliveryControlOwner._read_phase
        monkeypatch.setattr(_DeliveryControlOwner, '_read_phase', lambda *args, **kwargs:
            {**read(*args, **kwargs), 'changed_complete_census': True})
    elif damage == 'checkpoint':
        target = case.root / 'exports/current/checkpoints/e2.json'
        target.write_bytes(target.read_bytes().replace(b'PRIMARY_NONSUCCESS', b'PRIMARY_SUCCESSESX'))
    else:
        original = checkpoints._source
        monkeypatch.setattr(checkpoints, '_source', lambda root: {**original(root), 'commit': '0' * 40})
    with scientific_reconstruction_operation('full'), pytest.raises((PermissionError, ArtifactIdentityConflict)):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)


@pytest.mark.parametrize('changed_report', (False, True))
def test_aggregate_checkpoint_keeps_bounded_phase_references_and_exact_reassembly(case, monkeypatch, changed_report):
    from empirical_lawhood.api import matrix_programme_export_checkpoints as checkpoints
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    # Disclosed complete reports exceed the aggregate's test bound together,
    # while each individual saved phase remains within that same bound.
    monkeypatch.setattr(checkpoints, 'MAX_CHECKPOINT_BYTES', 32 * 1024)
    report = {**case.report, 'disclosed_payload': 'complete-adverse-report:' + 'x' * 20000}
    case.owner._control.observations = {phase: MatrixProgrammeObservation(phase, report, True)
        for phase in ('e2', 'train')}
    case.owner._control.bindings['train'] = SimpleNamespace(identity=_pin('binding.train', 'empirical-lawhood/testing/disclosed-binding'))
    project = _DeliveryControlOwner._report
    expected = []
    def complete(owner, context, **kwargs):
        result = {**project(owner, context, **kwargs), 'state': 'COMPLETE'}
        expected.append(canonical_json_document_bytes(result))
        return result
    monkeypatch.setattr(_DeliveryControlOwner, '_report', complete)
    receipt_products = delivery._receipt_products
    def interrupted(*args, **kwargs):
        raise InterruptedError('disclosed failure after complete report checkpoint')
    monkeypatch.setattr(delivery, '_receipt_products', interrupted)
    with scientific_reconstruction_operation('full'), pytest.raises(InterruptedError):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    saved = case.root / 'exports/current/checkpoints/programme-report.json'
    raw = saved.read_bytes()
    value = json.loads(raw)['value']
    assert len(raw) < checkpoints.MAX_CHECKPOINT_BYTES < len(expected[0])
    assert value['report_encoding'] == 'COMPLETED_PHASE_REFERENCES'
    assert all('report' not in row and row['report_checkpoint']['report']['size_bytes'] > 20000
        for row in value['report']['phases'])
    assert set(value['stage_binding']['execution']) == {'size_bytes', 'sha256'}
    monkeypatch.setattr(delivery, '_receipt_products', receipt_products)
    def forbidden_report(*args, **kwargs):
        raise AssertionError('complete aggregate was reconstructed instead of authenticated')
    monkeypatch.setattr(_DeliveryControlOwner, '_report', forbidden_report)
    observe = _DeliveryControlOwner._observe
    def resumed(owner, context, **kwargs):
        assert kwargs['reports'], 'phase reconstruction was repeated'
        observe(owner, context, **kwargs)
        if changed_report and kwargs['phases'] == ('train',):
            observation = context.observations['train']
            context.observations['train'] = replace(observation, report={**observation.report, 'changed': True})
    monkeypatch.setattr(_DeliveryControlOwner, '_observe', resumed)
    if changed_report:
        with scientific_reconstruction_operation('full'), pytest.raises(PermissionError, match='authenticated phase report'):
            case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    else:
        with scientific_reconstruction_operation('full'):
            result = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
        assert result['reused_export_stages'] == ('e2', 'train', 'programme-report')
        actual = json.loads(Path(result['path']).read_bytes())['value']['programme_readout']['report']
        assert canonical_json_document_bytes(actual) == expected[0]


@pytest.mark.parametrize('damage', ('none', 'scientific-owner', 'lock', 'runtime', 'commit',
    'library-relocation', 'library-bytes', 'late-library-bytes'))
def test_v1_checkpoint_migration_allows_only_exact_transport_owner_change(case, monkeypatch, damage):
    from empirical_lawhood.api import matrix_programme_export_checkpoints as checkpoints
    from empirical_lawhood.infrastructure.numerical_provenance import observe_implementation_source
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    rows, _, lock, _, _ = observe_implementation_source(ROOT)
    previous = dict(rows)
    previous['api/matrix_programme_export_checkpoints.py'] = 'a7d67ee368fe1d05043699828cd411e0ccff6303bbe2efa2353ccfdfb2341142'
    previous['infrastructure/source_policy.py'] = 'bdcceede975971cd9711d507ebac5a9eb71cdd4a881ae81f30c7c3373be6cf64'
    previous.update({name: before for name, before, _ in checkpoints._V1_TRANSPORT_REPAIRS})
    if damage == 'scientific-owner':
        previous['api/matrix_researcher_programme.py'] = '0' * 64
    source = {'code_sha256': sha256(canonical_json_bytes(tuple(sorted(previous.items())))).hexdigest(),
        'lock_sha256': '0' * 64 if damage == 'lock' else lock,
        'commit': 'invalid' if damage == 'commit' else '1' * 40}
    if damage.startswith('library-') or damage == 'late-library-bytes':
        # Disclosed runtime locations; no real numerical library is modified.
        old_library = case.root / 'old-runtime' / 'libdisclosed.so'
        new_library = case.root / 'new-runtime' / 'libdisclosed.so'
        old_library.parent.mkdir()
        new_library.parent.mkdir()
        old_library.write_bytes(b'exact disclosed runtime bytes')
        new_library.write_bytes(b'changed' if damage == 'library-bytes' else old_library.read_bytes())
        monkeypatch.setattr(checkpoints, 'numerical_runtime_observation', lambda: {
            'disclosed': True, 'threadpools': [{'filepath': str(new_library), 'num_threads': 1}]})
    execution = {'read_scope': 'EXECUTION_RECORDS', 'execution_complete': True, 'status': 'SUCCEEDED', 'phase': 'e2'}
    write = case.plane.write
    def legacy(request):
        if request.relative_path.endswith('/checkpoints/e2.json'):
            document = json.loads(request.payload)
            document['version'] = '1.0.0'
            value = document['value']
            value['binding']['source'] = source
            if damage == 'runtime':
                value['binding']['runtime'] = {'changed': True}
            elif damage.startswith('library-') or damage == 'late-library-bytes':
                value['binding']['runtime']['threadpools'][0]['filepath'] = str(old_library)
            value['stage_binding']['execution'] = execution
            value.pop('report_encoding')
            value.pop('reused_stage_sources')
            value.pop('runtime_relocation_files')
            request = replace(request, payload=canonical_json_document_bytes(document))
        return write(request)
    monkeypatch.setattr(case.plane, 'write', legacy)
    receipt_products = delivery._receipt_products
    def interrupted(*args, **kwargs):
        raise InterruptedError('disclosed legacy delivery failure')
    monkeypatch.setattr(delivery, '_receipt_products', interrupted)
    with scientific_reconstruction_operation('full'), pytest.raises(InterruptedError):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    checkpoint = case.root / 'exports/current/checkpoints/e2.json'
    original = checkpoint.read_bytes()
    monkeypatch.setattr(case.plane, 'write', write)
    monkeypatch.setattr(delivery, '_receipt_products', receipt_products)
    if damage == 'late-library-bytes':
        def mutate_library(*args, **kwargs):
            new_library.write_bytes(b'late changed runtime bytes')
            return receipt_products(*args, **kwargs)
        monkeypatch.setattr(delivery, '_receipt_products', mutate_library)
    observe = _DeliveryControlOwner._observe
    def resumed(owner, context, **kwargs):
        assert kwargs['reports']['e2'] == case.report
        return observe(owner, context, **kwargs)
    monkeypatch.setattr(_DeliveryControlOwner, '_observe', resumed)
    if damage in ('none', 'library-relocation'):
        with scientific_reconstruction_operation('full'):
            result = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
        assert result['reused_export_stages'] == ('e2',)
    elif damage == 'late-library-bytes':
        with scientific_reconstruction_operation('full'), pytest.raises(PermissionError, match='relocated numerical library'):
            case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    else:
        with scientific_reconstruction_operation('full'), pytest.raises(PermissionError, match='source, selection'):
            case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert checkpoint.read_bytes() == original


@pytest.mark.parametrize('damage', ('none', 'after-child-read', 'after-checkpoint'))
def test_checkpoint_uses_real_observer_and_keeps_independent_child_read_bytes(case, monkeypatch, damage):
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    record = Config('independent.scientific-operand', 23)
    extra = case.plane.write(ArtifactWriteRequest('independent.scientific-operand', 'child/operand.json',
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'independent.operand', 'child',
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    source = case.root / extra.materialization.relative_path
    independent = ExternalArtifactPlane(GuardedExternalRoot(case.plane.root.contract, case.plane.root.inspector), case.plane.validators,
        case.plane.semantic_validations)
    full_reads = []
    execution = _DeliveryControlOwner._read_phase
    def read(owner, context, phase, *, execution_only=False, **kwargs):
        if execution_only:
            return execution(owner, context, phase, execution_only=True, **kwargs)
        assert phase == 'e2'
        full_reads.append(phase)
        with independent.read_context() as child:
            child.verify_manifest(child.read_manifest(extra.materialization.relative_path))
        if damage == 'after-child-read':
            source.write_bytes(source.read_bytes().replace(b'23', b'24'))
        execution(owner, context, phase, execution_only=True)
        return {**case.report, 'scientific_result': {**case.report['scientific_result'],
            'scientific_completion': 'COMPLETE_NATIVE_UTILITY_ASSESSMENT'}}
    monkeypatch.setattr(_DeliveryControlOwner, '_observe', MatrixResearchProgrammeService._observe)
    monkeypatch.setattr(_DeliveryControlOwner, '_read_phase', read)
    original = delivery._receipt_products
    def interrupted(*args, **kwargs):
        raise InterruptedError('disclosed delivery failure')
    monkeypatch.setattr(delivery, '_receipt_products', interrupted)
    if damage == 'after-child-read':
        with scientific_reconstruction_operation('full'), pytest.raises((PermissionError, ArtifactIdentityConflict)):
            case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
        assert not (case.root / 'exports/current/checkpoints/e2.json').exists()
        assert full_reads == ['e2']
        return
    with scientific_reconstruction_operation('full'), pytest.raises(InterruptedError):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    value = json.loads((case.root / 'exports/current/checkpoints/e2.json').read_bytes())['value']
    assert [extra.materialization.relative_path, source.stat().st_size, sha256(source.read_bytes()).hexdigest()] in value['files']
    assert extra.materialization.relative_path in value['manifests']
    monkeypatch.setattr(delivery, '_receipt_products', original)
    if damage == 'after-checkpoint':
        source.write_bytes(source.read_bytes().replace(b'23', b'24'))
        with scientific_reconstruction_operation('full'), pytest.raises((PermissionError, ArtifactIdentityConflict)):
            case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    else:
        with scientific_reconstruction_operation('full'):
            result = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
        assert result['reused_export_stages'] == ('e2',)
    assert full_reads == ['e2']


def test_resumed_protected_checkpoint_refreshes_actual_grant_before_body_access(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import matrix_programme_export_checkpoints as checkpoints
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

    f = actual_issued_current_task_controls
    case = _delivery_case(f.control.service.artifact_plane)
    phase = 'e5.confirmation'
    control = case.owner._control
    control.bindings[phase] = SimpleNamespace(identity=_pin('binding.disclosed-protected',
        'empirical-lawhood/testing/disclosed-binding'))
    control.observations[phase] = MatrixProgrammeObservation(phase, {'status': 'SUCCEEDED'}, True)
    control.authority = lambda selected, component=None: (None, None,
        SimpleNamespace(reveal_authority_id=f.control.reveal.authority_id), f.control.package, None, None)
    original = delivery._receipt_products
    def interrupted(*args, **kwargs):
        raise InterruptedError('disclosed delivery failure')
    monkeypatch.setattr(delivery, '_receipt_products', interrupted)
    with scientific_reconstruction_operation('full'), pytest.raises(InterruptedError):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    monkeypatch.setattr(delivery, '_receipt_products', original)
    load = ExternalStudyOperationAuthorityStore.load
    def revoked(store, authority_id):
        if authority_id == f.control.reveal.authority_id:
            raise PermissionError('actual stored checkpoint grant revoked')
        return load(store, authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', revoked)
    read = checkpoints.read_bounded_bytes
    def body(path, **kwargs):
        assert not str(path).endswith('checkpoints/e5.confirmation.json'), 'revoked checkpoint body was opened'
        return read(path, **kwargs)
    monkeypatch.setattr(checkpoints, 'read_bounded_bytes', body)
    with scientific_reconstruction_operation('full'), pytest.raises(PermissionError, match='checkpoint grant revoked'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)


@pytest.mark.parametrize('boundaries', (4, 16))
def test_export_shares_real_original_grant_custody_but_refreshes_every_access(
        actual_issued_current_task_controls, monkeypatch, boundaries):  # noqa: F811
    from tests.test_selected_e3_current_access import _actual_original_access, _authority_read_work
    from empirical_lawhood.api.current_result_custody import require_current_result_reveal_authority
    f = actual_issued_current_task_controls
    case = _delivery_case(f.control.service.artifact_plane)
    access = _actual_original_access(f)
    def current_original():
        access.require_current()
        require_current_result_reveal_authority(writer=case.plane, package=f.control.package,
            reveal_authority_id=f.control.reveal.authority_id)
    case.owner._control.require_original_access = current_original
    original = delivery._receipt_products
    measured = []
    def repeated(writer, manifests, require_current):
        with _authority_read_work() as work:
            for _ in range(boundaries):
                require_current()
        measured.append(dict(work))
        return original(writer, manifests, require_current)
    monkeypatch.setattr(delivery, '_receipt_products', repeated)
    case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert measured[0]['fresh_grant_loads'] == boundaries
    assert measured[0].get('payload_validations', 0) == 0
    assert measured[0]['fresh_utc_checks'] == 2 * boundaries
    assert not f.control.executor.invocations


@pytest.mark.parametrize('damage', ('none', 'masked-body', 'pin', 'access'))
def test_saved_file_pins_share_exact_live_census_and_keep_final_guard(case, monkeypatch, damage):
    from empirical_lawhood.infrastructure import read_checkpoint
    from tests.test_reduced_artifact_verification import _mask_changed_stat
    names = sorted(case.owner._control.sources)
    pins = tuple((name, (case.root / name).stat().st_size,
        sha256((case.root / name).read_bytes()).hexdigest()) for name in names)
    opened = []
    original = read_checkpoint.bounded_file_sha256
    def counted(path, **kwargs):
        opened.append(path)
        return original(path, **kwargs)
    monkeypatch.setattr(read_checkpoint, 'bounded_file_sha256', counted)
    live = [True]
    def current():
        if not live[0]:
            raise PermissionError('current stored grant revoked')
    from contextlib import nullcontext
    expectation = nullcontext() if damage == 'none' else pytest.raises((PermissionError, ArtifactIdentityConflict))
    with expectation:
        with case.plane.read_context() as reading:
            read_checkpoint.authenticate_read_file_pins(reading, pins, require_current=current)
            assert len(opened) == len(pins)
            if damage == 'masked-body':
                path = case.root / case.product.materialization.relative_path
                _mask_changed_stat(monkeypatch, path)
                path.write_bytes(path.read_bytes().replace(b'17', b'18'))
            elif damage == 'pin':
                pins = ((pins[0][0], pins[0][1], '0' * 64), *pins[1:])
            elif damage == 'access':
                live[0] = False
            read_checkpoint.authenticate_read_file_pins(reading, pins, require_current=current)
            assert len(opened) == len(pins)


def test_public_portable_export_copies_actual_npz_receipts_and_original_publication_bytes(case):
    from io import BytesIO
    import numpy as np
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA

    buffer = BytesIO()
    values = np.array([[1.25, -2.5], [3.0, 4.5]], dtype='<f8')
    np.savez(buffer, values=values)
    raw = buffer.getvalue()
    array = case.plane.write(ArtifactWriteRequest('array.disclosed',
        'runs/run.disclosed/outputs/task.disclosed-arrays/arrays.npz', MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', 'publication.disclosed-array',
        'runs/run.disclosed/outputs/task.disclosed-arrays', raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    receipt = replace(case.receipt, receipt_id='receipt.disclosed-arrays', task_id='task.disclosed-arrays',
        attempt_id='attempt.disclosed-arrays', output_materializations=(array.materialization,),
        output_logical_artifacts=(array.logical,))
    published_receipt = ExternalTaskReceiptStore(case.plane).commit(receipt,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    metadata = case.plane.write(ArtifactWriteRequest('metadata.disclosed', 'unreceipted/metadata.json',
        case.product.logical.payload_schema, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'publication.disclosed-metadata', 'unreceipted', Config('metadata.disclosed', 23).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    case.owner._control.sources += (array.materialization.relative_path,
        published_receipt.materialization.relative_path, metadata.materialization.relative_path)
    selection, target = _select_portable(case)
    before = {path: path.read_bytes() for path in (case.root / 'runs').rglob('*') if path.is_file()}
    report = case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    replica = report['portable_replica']
    assert replica['status'] == 'COMPLETE' and report['new_native_contact_count'] == 0
    assert replica['metadata_only_references_require_original_custody']
    copied = target / array.materialization.relative_path
    assert copied.read_bytes() == raw
    with np.load(copied, allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays['values'], values)
    assert not (target / metadata.materialization.relative_path).exists()
    record = json.loads(Path(selection.replica_receipt_path).read_bytes())
    assert record['scientific_qualification'] == 'NOT_ESTABLISHED'
    assert record['execution_authority'] == 'NONE'
    assert record['source_contract']['value']['storage_root_id'] == record['target_contract']['value']['storage_root_id']
    for member in record['files']:
        source = case.root / member['relative_path']
        copied = target / member['relative_path']
        assert copied.read_bytes() == source.read_bytes()
        assert sha256(copied.read_bytes()).hexdigest() == member['sha256']
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize('limit', ['maximum_bytes', 'maximum_files'])
def test_portable_export_refuses_bounds_without_a_complete_replica(case, limit):
    selection, target = _select_portable(case)
    case.selection_path.write_bytes(replace(selection, **{limit: 1}).canonical_bytes())
    with pytest.raises(ValueError, match='file or byte bound'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert not tuple(target.iterdir())
    assert not Path(selection.replica_receipt_path).exists()


def test_portable_export_rechecks_actual_stored_reveal_during_copy(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure import artifact_replication

    f = actual_issued_current_task_controls
    case = _delivery_case(f.control.service.artifact_plane)
    control = case.owner._control
    phase = 'e5.confirmation'
    control.observations[phase] = MatrixProgrammeObservation(phase, {'status': OperationalStatus.SUCCEEDED}, False)
    control.bindings[phase] = SimpleNamespace(identity=_pin('binding.disclosed-access',
        'empirical-lawhood/testing/disclosed-binding'))
    control.authority = lambda selected, component=None: (None, None,
        SimpleNamespace(reveal_authority_id=f.control.reveal.authority_id), f.control.package, None, None)
    selection, target = _select_portable(case)
    original_copy = artifact_replication.copy_bounded_file
    original_load = ExternalStudyOperationAuthorityStore.load
    revoked = False

    def load(store, authority_id):
        if revoked and authority_id == f.control.reveal.authority_id:
            raise PermissionError('stored original reveal revoked during copy')
        return original_load(store, authority_id)

    def copy(*args, **kwargs):
        nonlocal revoked
        result = original_copy(*args, **kwargs)
        revoked = True
        return result

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', load)
    monkeypatch.setattr(artifact_replication, 'copy_bounded_file', copy)
    with pytest.raises(PermissionError, match='reveal revoked'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert tuple(target.iterdir())
    assert not Path(selection.replica_receipt_path).exists()


def test_portable_completion_rechecks_the_larger_original_read_closure(case, monkeypatch):
    from empirical_lawhood.infrastructure import artifact_replication

    metadata = case.plane.write(ArtifactWriteRequest('metadata.read-control', 'controls/original.json',
        case.product.logical.payload_schema, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'publication.read-control', 'controls', Config('metadata.read-control', 23).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    case.owner._control.sources += (metadata.materialization.relative_path,)
    selection, target = _select_portable(case)
    original_copy = artifact_replication.copy_bounded_file
    mutated = False

    def copy(*args, **kwargs):
        nonlocal mutated
        result = original_copy(*args, **kwargs)
        if not mutated:
            mutated = True
            path = case.root / metadata.materialization.relative_path
            path.write_bytes(path.read_bytes().replace(b'23', b'24'))
        return result

    monkeypatch.setattr(artifact_replication, 'copy_bounded_file', copy)
    with pytest.raises((PermissionError, ArtifactIdentityConflict), match='changed|bytes differ'):
        case.owner.export_products(directory=case.directory, selection_path=case.selection_path)
    assert tuple(target.iterdir())
    assert not Path(selection.replica_receipt_path).exists()
