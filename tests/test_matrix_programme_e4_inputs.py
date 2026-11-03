# SPDX-License-Identifier: MPL-2.0
"""Actual original C metadata and explicit original-producer seams; no science."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.e4_inputs import compose_programme_e4_banks
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.api import matrix_programme_e4_inputs as api
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case, selected_request  # noqa: F401

ROOT=Path(__file__).parents[1]


def test_current_e4_banks_reuse_all_original_c_sources_panels_and_phase_denominators(c_backed_source_case,monkeypatch):  # noqa: F811
    case=c_backed_source_case
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as recipes
    monkeypatch.setattr(recipes,'recipe_allocation',lambda *_a,**_kw:pytest.fail('C-backed E4 replayed seed material'))
    original=case.committed.commitments.canonical_bytes()
    result=compose_programme_e4_banks(case.committed,original_e3=case.public,criterion_publication=case.criterion_publication)
    assert tuple(phase for phase,_ in result.banks)==('DEVELOPMENT','CALIBRATION','CONFIRMATION')
    assert len(case.committed.phases)==12
    for phase,bank in result.banks:
        role='e4.'+phase.lower()
        selected=case.committed.phase(role)
        assert bank.reservation is selected.reservation
        assert bank.specification is selected.native_specification
        assert bank.response_selection is selected.responses
        assert bank.response_selection_publication==case.committed.commitments.phase(role).responses.publication
        assert bank.provenances==(case.committed.producing_provenance,)
        assert bank.forecast_design.criterion_publication==case.criterion_publication
        assert len(bank.sources)==9*bank.design.group_count==36
        programme=dict(result.programmes)[phase]
        assert len(programme.cases)==len(bank.sources) and len(programme.group_ids)==4
        assert programme.bank==bank.identity
        index=bank.source_index()
        for protocol in bank.response_selection.protocols:
            reference=next(value for value in bank.sources if value.root_id==protocol.public_source.root.root_id)
            protocol.public_source.validate_source(index.resolve(reference))
        raw=bank.canonical_bytes()
        assert decode_canonical_bytes(raw,type(bank),maximum_bytes=len(raw)).canonical_bytes()==raw
    assert {bank.forecast_design.identity for _,bank in result.banks}=={result.banks[0][1].forecast_design.identity}
    assert case.committed.commitments.canonical_bytes()==original
    assert dict(case.committed.commitments.revision_folds)


@pytest.mark.parametrize('changed',('assay','provenance','shared-specification'))
def test_original_e3_c_join_refuses_substitution_before_any_producer_or_publication(c_backed_source_case,changed):  # noqa: F811
    case=c_backed_source_case
    inputs,assay=case.committed,case.assay
    if changed=='assay':
        assay=replace(assay,protocol_id=assay.protocol_id+'.foreign')
    elif changed=='provenance':
        inputs=replace(inputs,producing_provenance=replace(inputs.producing_provenance,observed_git_head='b'*40))
    else:
        future=inputs.phase('e3.calibration')
        native=replace(future.native_specification,specification_id=future.native_specification.specification_id+'.foreign')
        inputs=replace(inputs,phases=tuple(replace(value,native_specification=native)
            if value.role==future.role else value for value in inputs.phases))
    with pytest.raises(PermissionError,match='original E3/TRAIN/C'):
        api._require_original_preparation(inputs,case.public,case.preparation,assay)


@pytest.mark.parametrize('changed',('commitment-identity','original-identity','commitment-bytes'))
def test_current_c_and_original_custody_refusals_publish_nothing(c_backed_source_case,tmp_path,monkeypatch,changed):  # noqa: F811
    case=c_backed_source_case;request=selected_request(case)
    original_path=None;raw=None
    if changed=='commitment-identity':
        request=replace(request,input_commitments=replace(request.input_commitments,
            record=replace(request.input_commitments.record,object_id=request.input_commitments.record.object_id+'.foreign')))
    elif changed=='original-identity':
        request=replace(request,original_e3=replace(request.original_e3,
            record=replace(request.original_e3.record,object_id=request.original_e3.record.object_id+'.foreign')))
    else:
        original_path=case.plane.root.resolve(request.input_commitments.publication.materialization.relative_path,for_write=False)
        raw=original_path.read_bytes()
        original_path.write_bytes(bytes((raw[0]^1,))+raw[1:])
    monkeypatch.setattr(case.plane,'write_batch',lambda *_a,**_kw:pytest.fail('refused current C published E4 metadata'))
    # This arithmetic fixture has no issued original producer. Isolate the
    # exact C/body guard rather than claiming original-access authority.
    monkeypatch.setattr(api,'_require_original_e3_access',lambda **_:None)
    monkeypatch.setattr(api,'load_authored_wave',lambda **_kw:pytest.fail('refused current C opened a TRAIN producer'))
    target=Path(case.plane.root.contract.canonical_path)/('refused-c-e4-'+changed)
    execution=ExecutionSelection(4,'environment.disclosed-c-e4',
        ObjectIdentity.from_record('recursive-member.implementation',implementation_binding(ROOT)),case.plane.root.contract.canonical_path)
    try:
        with pytest.raises((ValueError,PermissionError,RuntimeError)):
            api.publish_programme_e4_inputs(request=request,project_root=ROOT,artifact_writer=case.plane,
                metadata_directory=target,execution=execution)
    finally:
        if original_path is not None:original_path.write_bytes(raw)
    assert not target.exists()


def test_original_fit_refuses_another_valid_train_allocation_before_opening_bank_inputs(c_backed_source_case,monkeypatch):  # noqa: F811
    """Literal original-plan transport isolates the actual independent join."""
    case=c_backed_source_case
    import empirical_lawhood.api.current_result_custody as current
    import empirical_lawhood.api.matrix_selected_runtime as selected
    import empirical_lawhood.api.recursive_qualified_parents as parents
    from empirical_lawhood.api.matrix_selected_e3_e4_runtime import authenticate_selected_e3_training_banks
    model=next(value for value in case.original_products if value.record==scheduled.identity(case.public.models))
    binding=model.prior_execution
    package=SimpleNamespace(package_id=binding.package.object_id)
    plan=SimpleNamespace(execution_plan_id=binding.execution_plan.object_id,
        tasks=(SimpleNamespace(task_id=binding.task_id),))
    # This supplies no issued authority. The two genuine canonical source
    # declarations have deliberately different TRAIN allocations; the join must
    # refuse that substitution before any fitted bank bytes are opened.
    identity=ObjectIdentity.from_record
    monkeypatch.setattr(ObjectIdentity,'from_record',staticmethod(lambda name,record: binding.package if record is package else
        binding.execution_plan if record is plan else identity(name,record)))
    monkeypatch.setattr(parents,'_actual_package',lambda *_:package)
    monkeypatch.setattr(parents,'_replay_parent_authority',lambda *_:(object(),None))
    monkeypatch.setattr(current,'authenticate_current_execution_plan',lambda **_:plan)
    monkeypatch.setattr(selected,'_published_input',lambda *_a,**_kw:pytest.fail('foreign TRAIN allocation opened fit inputs'))
    with pytest.raises(PermissionError,match='another TRAIN allocation'):
        authenticate_selected_e3_training_banks(public=case.public,upstream_products=case.original_products,
            training_specification=case.training.specification,training_request=case.training.request,writer=case.plane)


@pytest.mark.parametrize('mutation', ('none', 'current-c', 'original-preparation', 'access-revoked'))
def test_shared_e4_context_guards_actual_originals_through_dependent_publication(c_backed_source_case, monkeypatch, mutation):  # noqa: F811
    """Actual C/custody/bytes, disclosed original producer I/O; no native work."""
    import sys

    case = c_backed_source_case
    request = selected_request(case)
    preparation_reads = []
    read_record = api._read_exact_record
    def observe_preparation(writer, publication, kind, **kwargs):
        record = read_record(writer, publication, kind, **kwargs)
        if publication == request.original_preparation.publication:
            preparation_reads.append(record)
        return record
    monkeypatch.setattr(api, '_read_exact_record', observe_preparation)
    locator = request.native_training_locator
    packet = SimpleNamespace(packet_id=locator.packet.object_id, SCHEMA=locator.packet.object_schema,
        VERSION=locator.packet.object_version, fingerprint=lambda: locator.packet.object_fingerprint)
    plan = SimpleNamespace(execution_plan_id=locator.execution_plan.object_id, SCHEMA=locator.execution_plan.object_schema,
        VERSION=locator.execution_plan.object_version, fingerprint=lambda: locator.execution_plan.object_fingerprint)
    monkeypatch.setattr(api, 'load_authored_wave', lambda **_: (packet, object(), object(), object()))
    monkeypatch.setattr(api, '_retained_plans', lambda *_: (SimpleNamespace(run_plan_id=locator.run_id), plan, object()))
    monkeypatch.setattr(api, '_read_instance', lambda *_: (case.training.specification, case.training.request, object()))
    monkeypatch.setattr(api, '_recorded_training_operands', lambda *_: (case.training.specification, case.training.request))
    monkeypatch.setattr(api, 'authenticate_selected_e3_public_package', lambda **_: None)
    monkeypatch.setattr(api, 'authenticate_selected_e3_training_banks', lambda **_: None)
    monkeypatch.setattr(api, 'authenticate_selected_e3_assay', lambda **_: case.criterion_publication)
    # Disclosed upstream producer I/O only; actual provider joins have separate owning controls.
    monkeypatch.setattr(api, '_original_assay_provider_publications', lambda **_: (
        case.original_assay.publication, case.preparation.response_selection.template_publications[0]))
    access_calls = []
    def disclosed_access(**_):
        access_calls.append('current-original-metadata')
        if mutation == 'access-revoked' and len(access_calls) > 1:
            raise PermissionError('disclosed original access revoked during dependent publication')
    monkeypatch.setattr(api, '_require_original_e3_access', disclosed_access)
    from tests.test_matrix_factor_confirmation_eligibility import publish
    selected = request.input_commitments if mutation == 'current-c' else request.original_preparation
    path = case.plane.root.resolve(selected.publication.materialization.relative_path, for_write=False)
    original = path.read_bytes()
    completed = []
    def consume():
        with api.authenticated_programme_e4_banks(artifact_writer=case.plane, input_commitments=request.input_commitments,
                original_e3=request.original_e3, original_preparation=request.original_preparation,
                original_assay=request.original_assay, original_products=request.original_products,
                native_training_locator=locator, maximum_source_bytes=request.source_budget.source_scan_bytes) as resolved:
            assert tuple(name for name, _ in resolved.banks) == ('DEVELOPMENT', 'CALIBRATION', 'CONFIRMATION')
            if mutation == 'none':
                # The duplicate preparation has served its scientific joins.
                # Only this probe may retain it across dependent publication;
                # original bytes and current grants still have live guards.
                assert len(preparation_reads) == 1
                references = sys.getrefcount(preparation_reads[0])
                assert references == 2
            # A normal dependent publication is allowed while exact original
            # snapshots remain active; it creates no issue or source authority.
            completed.append(publish(case.plane, case.assay, 'context.control.' + mutation))
            if mutation in ('current-c', 'original-preparation'):
                path.write_bytes(bytes((original[0] ^ 1,)) + original[1:])
    try:
        if mutation == 'none':
            consume()
        else:
            with pytest.raises((ValueError, PermissionError, RuntimeError)):
                consume()
        assert len(completed) == 1
        if mutation in ('none', 'access-revoked'):
            assert access_calls == ['current-original-metadata', 'current-original-metadata']
    finally:
        path.write_bytes(original)
    assert path.read_bytes() == original


@pytest.mark.parametrize('mutation', ('none', 'original-preparation', 'access-revoked'))
def test_bank_publication_keeps_original_operands_in_their_live_read(c_backed_source_case, monkeypatch, mutation):  # noqa: F811
    """Actual C, bank publication and byte guards; disclosed E3/TRAIN producers."""
    from collections import Counter
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    case = c_backed_source_case
    request = selected_request(case)
    reads, observed, live = Counter(), {}, {'allowed': True}
    read_record = api._read_exact_record

    def read(writer, publication, kind, **kwargs):
        value = read_record(writer, publication, kind, **kwargs)
        reads[publication.materialization.relative_path] += 1
        observed[publication.materialization.relative_path] = value
        return value

    def access(**kwargs):
        kwargs['writer'].require_active_verification_scope()
        if not live['allowed']:
            raise PermissionError('disclosed original access revoked')

    def training(writer, locator):
        writer.require_active_verification_scope()
        assert locator == request.native_training_locator
        reads['TRAIN'] += 1
        return case.training.specification, case.training.request

    monkeypatch.setattr(api, '_read_exact_record', read)
    monkeypatch.setattr(api, '_require_original_e3_access', access)
    monkeypatch.setattr(api, '_recorded_training_operands', training)
    monkeypatch.setattr(api, 'authenticate_selected_e3_public_package', lambda **_: None)
    monkeypatch.setattr(api, 'authenticate_selected_e3_training_banks', lambda **_: None)
    monkeypatch.setattr(api, 'authenticate_selected_e3_assay', lambda **_: case.criterion_publication)
    monkeypatch.setattr(api, '_original_assay_provider_publications', lambda **_: (
        case.original_assay.publication, case.preparation.response_selection.template_publications[0]))
    root = Path(case.plane.root.contract.canonical_path)
    path = root / request.original_preparation.publication.materialization.relative_path
    before = path.read_bytes()
    directory = root / ('scoped-bank-publication-' + mutation)
    execution = ExecutionSelection(4, 'environment.disclosed-bank-publication',
        ObjectIdentity.from_record('recursive-member.implementation', implementation_binding(ROOT)), str(root))
    published = []

    def consume():
        with api.published_programme_e4_inputs(request=request, project_root=ROOT, artifact_writer=case.plane,
                metadata_directory=directory, execution=execution) as result:
            preparation = request.original_preparation.publication.materialization.relative_path
            assay = request.original_assay.publication.materialization.relative_path
            assert reads[preparation] == reads[assay] == reads['TRAIN'] == 1
            assert result.original_preparation is observed[preparation]
            assert result.original_assay is observed[assay]
            assert result.training_request is case.training.request
            assert len(result.publications) == 6
            published.extend(result.publications)
            if mutation == 'original-preparation':
                path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
            elif mutation == 'access-revoked':
                live['allowed'] = False

    try:
        if mutation == 'none':
            consume()
        else:
            with pytest.raises((ArtifactIdentityConflict, PermissionError)):
                consume()
        assert len(published) == 6
    finally:
        live['allowed'] = True
        if mutation == 'original-preparation':
            path.write_bytes(before)


def test_original_current_access_refuses_before_any_export_body_read(c_backed_source_case, monkeypatch):  # noqa: F811
    case = c_backed_source_case
    request = selected_request(case)
    observed = []
    def denied(*_args, **_kwargs):
        observed.append('current-original-metadata')
        raise PermissionError('disclosed original grant expired')
    monkeypatch.setattr(api, '_original_product_metadata', denied)
    monkeypatch.setattr(api, '_read_exact_record', lambda *_a, **_kw: pytest.fail('protected export body opened before current access'))
    with pytest.raises(PermissionError, match='original grant expired'):
        with api.authenticated_programme_e4_banks(artifact_writer=case.plane,
                input_commitments=request.input_commitments, original_e3=request.original_e3,
                original_preparation=request.original_preparation, original_assay=request.original_assay,
                original_products=request.original_products, native_training_locator=request.native_training_locator,
                maximum_source_bytes=request.source_budget.source_scan_bytes):
            pytest.fail('expired access entered the composed source scope')
    assert observed == ['current-original-metadata']


@pytest.mark.parametrize('foreign', (False, True))
def test_original_export_metadata_requires_the_complete_exact_producer_lineage(c_backed_source_case, monkeypatch, foreign):  # noqa: F811
    """Actual literal publication; disclosed metadata seam creates no authority."""
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
    from empirical_lawhood.api.matrix_source_input_assembly import publish_source_input_record
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeProducedInput
    case = c_backed_source_case
    package, issued, reveal = object(), object(), object()
    metadata = SimpleNamespace(visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    calls = []
    def observed(_writer, product, expected):
        assert expected == product.record
        calls.append(expected)
        return package, issued, reveal, object(), metadata, ('disclosed.current-producer',)
    monkeypatch.setattr(api, '_original_product_metadata', observed)
    parents = tuple(sorted({ArtifactLineageParent(pin, metadata.visibility_ceiling, metadata.outcome_access)
        for product in case.original_products for pin in (product.record, product.prior_execution.receipt)},
        key=lineage_parent_sort_key))
    selected = parents
    if foreign:
        selected = tuple(sorted((replace(parents[0], identity=replace(parents[0].identity,
            object_id=parents[0].identity.object_id + '.foreign')), *parents[1:]), key=lineage_parent_sort_key))
    _, publication = publish_source_input_record(writer=case.plane, prefix='lineage-controls', namespace='disclosed-lineage',
        name='foreign' if foreign else 'exact', record=case.public, lineage_parents=selected)
    handle = MatrixProgrammeProducedInput(case.public.identity, publication)
    if foreign:
        with pytest.raises(PermissionError, match='actual producer lineage'):
            api._require_original_e3_access(writer=case.plane, original_e3=handle, original_products=case.original_products)
    else:
        assert api._require_original_e3_access(writer=case.plane,
            original_e3=handle, original_products=case.original_products) is None
    assert tuple(calls) == tuple(value.record for value in case.original_products)
