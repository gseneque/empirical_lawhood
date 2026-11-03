# SPDX-License-Identifier: MPL-2.0
"""Exact commitment joins over actual disclosed metadata; no native or fits.

Literal initial arrays below are shape controls, never acquisition
or freshness evidence. Public API tests retain genuine publication validation.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_original_commitments as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_experiment import MatrixPreparationSourceBank
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationInitialState, MatrixCouplingRecipe, MatrixPreparationSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import MatrixProtectedSourceClosure, MatrixReservedTransferSources
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_future_response_selections
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
from tests.test_matrix_native_training_future_commitments import _declare, _selections


def _initial(source):
    n = source.policy.cutoff_tick
    alpha = tuple(Decimal(str(value)) for value in source.coordinate.couplings(n))
    pin = ObjectIdentity('literal.unexecuted.initial-history', 'empirical-lawhood/disclosed/control', '1.0.0', 'a' * 64)
    raw, members = encode_matrix_arrays({name: np.zeros((2, 3, 4, 4), dtype='<c16') for name in ('momenta', 'positions')})
    artifact = ArtifactIdentity('literal.unexecuted.initial-array', 'initial-state', MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    initial = MatrixPreparationInitialState('initial.disclosed.' + source.root_id, pin, pin, artifact, members, alpha)
    recipe = MatrixCouplingRecipe('recipe.disclosed.hold.' + source.coordinate.coordinate_id, 'HOLD', n,
        (alpha,) * (2 * n + 1), 'HALF_TICK_COUPLING_TOTAL_VARIATION_L1', 'unit.disclosed.coupling')
    return initial, recipe


def _future(case):
    request, _ = _declare(case, _selections(case))
    return request, authenticate_future_response_selections(case.plane, request)


def _transfer(request, future):
    manifest = request.future_manifest
    selected = tuple(value for role, selection in future if role.startswith('TRANSFER_') for value in selection.protocols)
    source_index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    sources = tuple(sorted((source_index.resolve(source_index.reference(source_id=value.public_source.source.object_id,
        root_id=value.public_source.root.root_id, provenance=manifest.provenances[0].identity)) for value in selected),
        key=lambda value: value.root_id))
    initials, recipes = {}, {}
    for source in sources:
        initial, recipe = _initial(source)
        initials[source.root_id] = initial
        recipes[coordinate_identity(source.coordinate)] = recipe
    closure = MatrixProtectedSourceClosure('closure.disclosed.original-panels', manifest.reservation,
        manifest.native_specification, manifest.provenances, tuple(value.reference for value in sources),
        manifest.audit, manifest.audit_publication, tuple(sorted(initials.items())), sr.identity(manifest.native_specification.selection.numerical_design))
    bank = MatrixReservedTransferSources('sources.disclosed.original-panels', closure,
        tuple(sorted(recipes.items(), key=lambda value: value[0].object_id)), 'arm.hold')
    assay = MatrixPreparedAssayMethod.from_protocol('assay.disclosed.original-panels', selected[0])
    panels = tuple(sorted((group, tuple(sorted((owner.prepared_original_panel(panel) for panel in values), key=lambda value: value.panel_id)))
        for role, selection in future if role.startswith('TRANSFER_') for group, values in selection.panels))
    return bank, assay, panels


def test_e6_consumes_exact_actual_pretrain_four_role_publications_and_panels(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    historical = case.request.canonical_bytes()
    request, future = _future(case)
    sources, assay, panels = _transfer(request, future)
    phases = tuple((role, case.programme_inputs.phase(role)) for role in
        ('e5.development', 'e5.confirmation', 'e6.nearby', 'e6.shifted'))
    selections = tuple((role, selected.responses) for role, selected in phases)
    owner.validate_committed_prepared_sources(phase='E6_TRANSFER', sources=sources,
        phases=phases, producing_provenance=case.programme_inputs.producing_provenance)
    owner.validate_committed_prepared_panels(phase='E6_TRANSFER', assay=assay, panels=panels, selections=selections)
    foreign = tuple((role, replace(case.programme_inputs.phase('e5.confirmation'), role=role)
        if role == 'e6.nearby' else value) for role, value in phases)
    with pytest.raises(PermissionError, match='complete original phase root census'):
        owner.validate_committed_prepared_sources(phase='E6_TRANSFER', sources=sources,
            phases=foreign, producing_provenance=case.programme_inputs.producing_provenance)
    locator = owner.MatrixFiniteDtTrainingLocator('unexecuted/commitment-shape', 'run.unexecuted.commitment-shape',
        ObjectIdentity('packet.unexecuted.commitment-shape', 'empirical-lawhood/runtime/authored-recursive-wave', '1.0.0', 'a' * 64),
        ObjectIdentity('plan.unexecuted.commitment-shape', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', 'b' * 64))
    commitment = owner.MatrixPreparedOriginalCommitments('commitments.disclosed.current-c', locator,
        request.input_commitments, 128 * 1024**2)
    assert commitment.VERSION == '2.0.0'
    assert decode_canonical_bytes(commitment.canonical_bytes(), type(commitment), maximum_bytes=None) == commitment
    for bound in (None, 0, -1, True):
        with pytest.raises(ValueError, match='positive complete C source byte budget'):
            replace(commitment, maximum_source_bytes=bound)
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    with pytest.raises(ValueError, match='version'):
        decode_canonical_record({**commitment.to_document(), 'version': '1.0.0'}, type(commitment))
    assert 'original_e4_recipe_index' not in commitment.to_document()['value']
    owner.validate_original_prepared_scope(phase='E6_TRANSFER', sources=sources, assay=assay, panels=panels,
        request=request, future_selections=future, e4_phases=())
    # The prepared source predecessor must enforce the same exact panel IDs
    # before qualification, independently of the later protected entry check.
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as prepared
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
    supports=exposure_support(request.future_manifest.audit)
    bank=prepared.MatrixPreparedSourceBank('bank.disclosed.original-transfer',sources,assay,panels,supports,request.input_commitments)
    prepared.require_original_future_commitments(bank,request,future)
    assert case.request.canonical_bytes() == historical
    assert decode_canonical_bytes(historical, type(case.request), maximum_bytes=len(historical)) == case.request
    # Same roots and otherwise valid new streams are not the old commitment.
    group, first = panels[0]
    independent = next(value for value in first if value.role == 'INDEPENDENT_FUTURE')
    streams = tuple(MatrixHistorySeed(purpose, sha256(('uncommitted.' + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)
    for changed in (replace(independent, streams=streams), replace(independent, panel_id=independent.panel_id + '.renamed')):
        changed_panels = ((group, tuple(sorted((changed if value == independent else value for value in first), key=lambda value: value.panel_id))), *panels[1:])
        with pytest.raises(ValueError, match='panel identities|streams'):
            owner.validate_original_prepared_scope(phase='E6_TRANSFER', sources=sources, assay=assay, panels=changed_panels,
                request=request, future_selections=future, e4_phases=())
        with pytest.raises(ValueError,match='panel identities|streams'):
            prepared.require_original_future_commitments(replace(bank,panels=changed_panels),request,future)
    with pytest.raises(ValueError, match='four'):
        owner.validate_original_prepared_scope(phase='E6_TRANSFER', sources=sources, assay=assay, panels=panels,
            request=request, future_selections=future[:-1], e4_phases=())


def _opportunity(case, *, streams=None, coordinate=None):
    """A separate typed disclosed DEV source, published through ordinary owners."""
    original = case.source
    coordinate = original.coordinate if coordinate is None else coordinate
    streams = streams or tuple(MatrixHistorySeed(purpose, sha256(('separate.E5.' + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)
    root = replace(original.root, root=replace(original.root.root, root_id='root.disclosed.separate-e5',
        independent_group_id='group.disclosed.separate-e5', coordinate_id=coordinate.coordinate_id, clock_id=coordinate.clock_id),
        coordinate=coordinate_identity(coordinate), streams=streams)
    allocation = replace(original.reservation.allocation, allocation_id='allocation.disclosed.separate-e5',
        coordinates=(coordinate,), roots=(root,), matched_scopes=tuple(replace(value,
            independent_group_ids=(root.root.independent_group_id,), coordinates=(coordinate_identity(coordinate),))
            for value in original.reservation.allocation.matched_scopes))
    reservation = sr.ScheduledReservation('reservation.disclosed.separate-e5', allocation,
        publish(case.plane, allocation, 'publication.disclosed.separate-e5.allocation.' + allocation.fingerprint()))
    selection = replace(original.specification.selection, selection_id='selection.disclosed.separate-e5', reservation=sr.identity(reservation),
        coordinate_policies=((coordinate_identity(coordinate), sr.identity(original.policy)),))
    specification = sr.ScheduledSpecification('specification.disclosed.separate-e5', selection,
        publish(case.plane, selection, 'publication.disclosed.separate-e5.selection.' + selection.fingerprint()))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=(original.provenance,))
    source = source_index.resolve(source_index.reference(source_id='source.disclosed.separate-e5',
        root_id=root.root.root_id, provenance=original.provenance.identity))
    initial, recipe = _initial(source)
    prepared = MatrixPreparationSource('prepared.disclosed.separate-e5', ScheduledPublicSource.from_source(source), source.root,
        initial, recipe, source.provenance, source.numerical_design)
    return MatrixPreparationSourceBank('bank.disclosed.separate-e5', (allocation,), (prepared,))


def test_e5_refuses_actual_original_train_reserved_panel_and_full_e6_physical_aliases(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    request, future = _future(case)
    source_bank = _opportunity(case)
    _, assay, panels = _transfer(request, future)
    # Existing typed selectors stand for disclosed already-committed E4 scope;
    # production obtains these only from the authenticated actual whole C.
    by_role = dict(future)
    e4 = tuple((name, by_role[role]) for name, role in (('CALIBRATION', 'CALIBRATION'), ('CONFIRMATION', 'EVALUATION'), ('DEVELOPMENT', 'TRANSFER_NEARBY')))
    # A distinct actually typed committed E4 independent panel is absent from
    # the original four selectors; it still cannot be reused downstream.
    name, last = e4[-1]
    e4_streams = {group: tuple(MatrixHistorySeed(purpose, sha256(('committed.E4.only.' + group + purpose).encode()).hexdigest())
        for purpose in HISTORY_PURPOSES) for group, _ in last.panels}
    e4_only = next(iter(e4_streams.values()))
    changed = tuple((group, tuple(replace(panel, streams=e4_streams[group]) if panel.role == 'INDEPENDENT_FUTURE' else panel for panel in values))
        for group, values in last.panels)
    e4 = (*e4[:-1], (name, replace(last, panels=changed)))
    own_streams = source_bank.sources[0].root.streams
    prepared_panel = replace(panels[0][1][0], panel_id='panel.disclosed.separate-e5', independent_group_id='group.disclosed.separate-e5', streams=own_streams)
    own_panels = (('group.disclosed.separate-e5', (prepared_panel,)),)
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import ResolvedMatrixProgrammePhaseInputs
    e4 = tuple((label, ResolvedMatrixProgrammePhaseInputs("e4." + label.lower(),
        request.future_manifest.reservation, request.future_manifest.native_specification, selection))
        for label, selection in e4)
    def check(bank=source_bank, selected_panels=own_panels):
        return owner.validate_original_prepared_scope(phase='E5_OPPORTUNITY', sources=bank, assay=assay, panels=selected_panels,
            request=request, future_selections=future, e4_phases=e4)
    check()
    with pytest.raises(ValueError, match='E5 consumes'):
        check(_opportunity(case, streams=case.source.root.streams))
    reserved_panel = next(value for _, values in by_role['TRANSFER_SHIFTED'].panels for value in values if value.role == 'INDEPENDENT_FUTURE')
    with pytest.raises(ValueError, match='E5 consumes'):
        check(selected_panels=(('group.disclosed.separate-e5', (replace(prepared_panel, streams=reserved_panel.streams),)),))
    with pytest.raises(ValueError, match='E5 consumes'):
        check(selected_panels=(('group.disclosed.separate-e5', (replace(prepared_panel, streams=e4_only),)),))
    coordinate = by_role['TRANSFER_SHIFTED'].protocols[0].public_source.coordinate
    with pytest.raises(ValueError, match='E5 consumes'):
        check(_opportunity(case, coordinate=coordinate))


def test_all_new_entry_declarations_have_exact_committed_evidence_and_real_worker_factories():
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as opportunity
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as protected
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision
    owners = ((opportunity, owner.MatrixSelectedOpportunityRootConfigV2, owner.MatrixSelectedOpportunityEvidenceV2),
        (protected, owner.MatrixSelectedProtectedRootConfigV3, owner.MatrixSelectedEntryEvidenceV3),
        (revision, owner.MatrixRevisionRootConfigV2, owner.MatrixRevisionEntryEvidenceV2))
    for module, config, evidence in owners:
        selected = tuple(value for value in module.operation_declarations() if value.config_record_type is config)
        assert len(selected) == (2 if module is revision else 1)
        for declaration in selected:
            worker = declaration.runner_factory()
            assert worker.manifest == declaration.manifest()
            assert len(declaration.input_ports) == 1 and declaration.input_ports[0].payload_schema == evidence.SCHEMA
            assert declaration.record_codecs[evidence.SCHEMA] is evidence


def test_all_actual_entry_owners_stop_missing_commitments_before_any_writer_or_science_read():
    from empirical_lawhood.api.matrix_selected_opportunity_runtime import _authenticate_original_products
    from empirical_lawhood.api.matrix_selected_runtime import _authenticate_entry
    from empirical_lawhood.api.matrix_selected_revision_runtime import authenticate_revision_entry
    class NoEffects:
        def __getattr__(self, name):
            pytest.fail('missing original commitment touched external/scientific owner: ' + name)
    for entry in (_authenticate_original_products, _authenticate_entry, authenticate_revision_entry):
        with pytest.raises(ValueError, match='Original commitment evidence is missing'):
            entry(NoEffects(), object(), object(), {}, source_scan_bytes=128 * 1024**2)
