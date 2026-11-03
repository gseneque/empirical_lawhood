# SPDX-License-Identifier: MPL-2.0
"""Public copied metadata and current-exposure controls; no genuine acquisition."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_prepared_source_assembly as domain
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs,load_experiment_specification,prepare_experiment
from empirical_lawhood.api.domain_composition.matrix_prepared_source_assembly.assembly import current_confirmation_sources
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_prepared_source import prepared_bank
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import transfer,confirmation,unpublished  # noqa: F401

ROOT=Path(__file__).parents[1]
EXAMPLE=ROOT/'programmes/foundations/emergent-structure/workflows/matrix-response-experiment'


def test_copied_public_request_reports_exact_two_missing_original_scientific_roles():
    specification=load_experiment_specification(EXAMPLE/'prepared-source-assembly.example.json')
    inputs=load_experiment_inputs(specification,EXAMPLE/'prepared-source-assembly-sources.example.json')
    request=inputs.method_inputs.request
    assert type(request) is domain.MatrixPreparedSourceAssemblyRequest
    assert not request.allow_metadata_key_creation
    assert decode_canonical_bytes(request.canonical_bytes(),type(request),maximum_bytes=None)==request
    prepared=prepare_experiment(specification,method_inputs=inputs.method_inputs,execution=ExecutionSelection(workers=4))
    assert not prepared.executable and prepared.census.native_effect_count==0
    assert {value.source_key for value in prepared.dependencies if value.source_key}=={
        'prepared-programme','development-product'}
    assert 'prepared-source-assembly.derive' not in {value.code for value in prepared.dependencies}
    changed=replace(request,metadata_validity_seconds=request.metadata_validity_seconds+1)
    assert changed.identity!=request.identity
    with pytest.raises(ValueError,match='request pin'):
        domain.bind_inputs(specification,{'request':changed})


def test_copied_request_checks_actual_metadata_policy_and_original_custody_before_derivation():
    specification=load_experiment_specification(EXAMPLE/'prepared-source-assembly.example.json')
    inputs=load_experiment_inputs(specification,EXAMPLE/'prepared-source-assembly-sources.example.json')
    request=inputs.method_inputs.request
    with pytest.raises(PermissionError,match='self-approve'):replace(request,metadata_approver_id=request.metadata_requester_id)
    with pytest.raises(ValueError):replace(request,metadata_private_key_relative_path='../foreign-key')
    with pytest.raises(ValueError):replace(request,metadata_validity_seconds=0)
    with pytest.raises(ValueError):replace(request,metadata_reason_codes=())
    # Dataset reason strings use their real owner, including descriptive words.
    assert replace(request,metadata_reason_codes=('Explicit metadata-only replay.',)).metadata_reason_codes
    with pytest.raises(ValueError,match='exact.*support'):
        replace(request,exposure_support=())
    first,*rest=request.exposure_support
    with pytest.raises(ValueError,match='byte custody'):
        replace(request,exposure_support=((replace(first[0],sha256='0'*64),first[1]),*rest))
    with pytest.raises(ValueError,match='canonical publication custody'):
        replace(request,input_commitments=replace(request.input_commitments,publication=replace(
            request.input_commitments.publication,logical=replace(request.input_commitments.publication.logical,media_type='text/plain'))))


@pytest.mark.parametrize('family',('confirmation','transfer'))
def test_current_conf_projection_keeps_original_bytes_and_e6_refuses_projection(tmp_path,request,family):
    from empirical_lawhood.api.matrix_prepared_source_runtime import _require_current_exposure_subset
    from tests.test_matrix_factor_confirmation_eligibility import publish
    from tests.test_recursive_public_service import _plane
    programme=request.getfixturevalue(family)
    bank=prepared_bank(programme)
    programme=SimpleNamespace(phase=programme.phase,sources=bank.sources)
    plane=_plane(tmp_path/'actual-publication-control')
    before=programme.sources.canonical_bytes()
    audit=programme.sources.closure.audit
    seed=next(value for value in range(1,10000) if value not in audit.census.effective_seed_exclusions)
    group='group.disclosed.actual-sequence-union'
    coordinate=programme.sources.source_arms()[0][1].coordinate
    facts=SimpleNamespace(request=SimpleNamespace(future_manifest=SimpleNamespace(audit=audit)),
        effective_seeds=(seed,),group_ids=(group,),coordinates=(coordinate,))
    published=[]
    def publication(name,record):
        stored=publish(plane,record,'projection.control.'+name.replace('/','.'))
        published.append(stored)
        return stored
    support=publication('witness',audit.census)
    if family=='transfer':
        before_count=len(published)
        with pytest.raises(ValueError,match='only to new unacquired CONF'):
            current_confirmation_sources(programme=programme,facts=facts,namespace='disclosed.current-exposure',
                publication=publication,audit_publication=support)
        assert len(published)==before_count
        assert programme.sources.canonical_bytes()==before
        assert programme.sources.closure.audit==audit
        return
    sources,supports=current_confirmation_sources(programme=programme,facts=facts,namespace='disclosed.current-exposure',
        publication=publication,audit_publication=support)
    current=sources.closure.audit
    assert programme.sources.canonical_bytes()==before
    assert sources.recipes==programme.sources.recipes
    assert tuple(row.root for row in sources.closure.descriptors)==tuple(row.root for row in programme.sources.closure.descriptors)
    assert sources.closure.provenances==programme.sources.closure.provenances
    assert sources.closure.initial_states==programme.sources.closure.initial_states
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
    assert supports==exposure_support(current) and len(supports)==1
    _require_current_exposure_subset(audit,current,effective_seeds=(seed,),group_ids=(group,),coordinates=(coordinate,))
    assert seed in current.census.effective_seed_exclusions and group in current.census.exposed_independent_groups
    # Every projected prior-corpus row is an actual immutable publication.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    for stored in current.prior_corpus:authenticate_publication(plane,stored)


def test_registry_declares_source_preprocessing_target_and_configuration():
    from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
    from empirical_lawhood.adapters.methods.matrix_prepared_source_experiment import PROTOCOL_ID as target
    from empirical_lawhood.api.experiment_preparation import experiment_protocols
    declaration,=(value for value in experiment_protocols() if value.protocol_id==domain.PROTOCOL_ID)
    assert declaration.example_paths==('programmes/foundations/emergent-structure/workflows/matrix-response-experiment/prepared-source-assembly.example.json',)
    assert declaration.input_record_types==domain.input_record_types()
    assert declaration.configuration_inputs[0].record_type is domain.MatrixPreparedSourceAssemblyRequest
    binding=experiment_runtime_binding(declaration)
    assert binding.derivation_target_protocol_ids==(target,)


def test_current_conf_rebinds_actual_declared_v2_initialization_metadata_without_native(confirmation,tmp_path,monkeypatch):  # noqa: F811
    """Real public initializer output class; all original-custody rows are TEST.

    No source qualification or original execution is claimed. The actual Q2
    initializer and independent consumer check every retained array without RNG.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_initialization_science as initializer
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science as consumer
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import (
        MatrixPreparationInitialStateV2,MatrixCouplingRecipe,original_schedule_recipe)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    from empirical_lawhood.api.matrix_prepared_source_runtime import _require_current_exposure_subset
    from tests.test_matrix_factor_confirmation_eligibility import publish
    from tests.test_matrix_preparation_initialization import forbid_contact
    from tests.test_recursive_public_service import _plane
    forbid_contact(monkeypatch)
    bank=prepared_bank(confirmation)
    prior=bank.sources.closure
    states=[];arrays={}
    source_index = prior.source_index()
    for descriptor in prior.descriptors:
        subject=prior.original(descriptor, index=source_index)
        state,raw=initializer.initialize_source(subject,subject.provenance,
            state_id='initial.disclosed.current.'+descriptor.root_id,artifact_id='array.disclosed.current.'+descriptor.root_id)
        assert type(state) is MatrixPreparationInitialStateV2
        assert decode_canonical_bytes(state.canonical_bytes(),MatrixPreparationInitialStateV2,maximum_bytes=None)==state
        states.append((descriptor.root_id,state));arrays[descriptor.root_id]=raw
    closure=replace(prior,initial_states=tuple(states))
    subject=closure.original(closure.descriptors[0], index=closure.source_index())
    baseline=original_schedule_recipe(subject.coordinate,subject.policy.cutoff_tick,
        recipe_id='recipe.disclosed.current.baseline',effort_unit=confirmation.criterion.effort_unit)
    schedule=list(baseline.half_tick_couplings);schedule[1]=schedule[2]
    arm=next(value for value,_ in bank.sources.recipes if value!=bank.sources.hold_arm_id)
    recipe=MatrixCouplingRecipe('recipe.disclosed.current.fixed','FIXED_COUPLING',baseline.primary_steps,
        tuple(schedule),baseline.effort_rule,baseline.effort_unit)
    sources=replace(bank.sources,closure=closure,
        recipes=tuple(sorted(((bank.sources.hold_arm_id,baseline),(arm,recipe)))))
    before=sources.canonical_bytes();old_initials=dict(sources.closure.initial_states)
    programme=SimpleNamespace(phase='E5_CONFIRMATION',sources=sources)
    audit=closure.audit
    seed=next(value for value in range(1,10000) if value not in audit.census.effective_seed_exclusions)
    group='group.disclosed.current-v2-union'
    coordinate=subject.coordinate
    facts=SimpleNamespace(request=SimpleNamespace(future_manifest=SimpleNamespace(audit=audit)),
        effective_seeds=(seed,),group_ids=(group,),coordinates=(coordinate,))
    plane=_plane(tmp_path/'actual-v2-publication-control')
    published=[]
    def publication(name,record):
        stored=publish(plane,record,'projection.v2.control.'+name.replace('/','.'))
        published.append(stored)
        from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
        return _publication_from_manifest(plane,plane.read_manifest(stored.materialization.relative_path))
    support=publication('witness',audit.census)
    current,supports=current_confirmation_sources(programme=programme,facts=facts,namespace='disclosed.current-v2',
        publication=publication,audit_publication=support)
    # Reopen the same original initialization/custody; a resume never feeds
    # the already projected closure back into the current-audit projection.
    replay,replay_supports=current_confirmation_sources(programme=programme,facts=facts,namespace='disclosed.current-v2',
        publication=publication,audit_publication=support)
    assert replay.canonical_bytes()==current.canonical_bytes() and replay_supports==supports
    assert sources.canonical_bytes()==before
    assert current.identity!=sources.identity and current.closure.identity!=sources.closure.identity
    assert current.closure.provenances==closure.provenances
    assert current.recipes==sources.recipes
    assert {value.root for value in current.closure.descriptors}=={value.root for value in closure.descriptors}
    source_index = current.closure.source_index()
    for descriptor in current.closure.descriptors:
        old=old_initials[descriptor.root_id];actual=dict(current.closure.initial_states)[descriptor.root_id]
        new_subject=current.closure.original(descriptor, index=source_index)
        assert actual.original==ScheduledPublicSource.from_source(new_subject)
        assert actual.identity!=old.identity and actual.state_id!=old.state_id
        assert replace(actual,state_id=old.state_id,original=old.original)==old
        assert actual.array_artifact==old.array_artifact and actual.members==old.members
        assert actual.root==old.root and actual.producing_provenance==old.producing_provenance
        assert actual.cutoff==old.cutoff and actual.alpha_tilde==old.alpha_tilde
        assert actual.consumed_streams==() and actual.native_contact_count==0
        assert consumer.initial_state(actual,arrays[descriptor.root_id]).step_index==0
        for selected_arm,prepared in current.source_arms():
            if prepared.root.root.root_id==descriptor.root_id:
                assert prepared.initial==actual and prepared.original==actual.original
    _require_current_exposure_subset(audit,current.closure.audit,effective_seeds=(seed,),group_ids=(group,),coordinates=(coordinate,))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
    assert supports==exposure_support(current.closure.audit) and len(supports)==1
    # The old public initialization bank is preserved, not relabelled as the
    # new canonical state. Reintroducing its source pin must still refuse.
    stale=replace(current.closure,initial_states=tuple(states))
    with pytest.raises(ValueError,match='declared initialization source or root streams'):
        replace(current,closure=stale)


@pytest.mark.parametrize("family,damage", (("confirmation", None), ("transfer", None),
    ("confirmation", "candidate"), ("transfer", "candidate"),
    ("confirmation", "locator"), ("transfer", "locator"),
    ("confirmation", "publication"), ("confirmation", "before-certificate"), ("transfer", "before-certificate")))
def test_prepared_assembly_reuses_one_disclosed_fact_read_and_guards_real_file_bytes(tmp_path, request, opportunity, monkeypatch, family, damage):  # noqa: F811
    """Actual assembly composition/publications/FILE guards; original source and certificate are explicit TEST seams."""
    from hashlib import sha256
    from empirical_lawhood.api.domain_composition.matrix_prepared_source_assembly import assembly as api
    from empirical_lawhood.api import matrix_prepared_source_runtime as runtime
    from empirical_lawhood.api import recursive_authoring, recursive_execution, native_training_banks
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    from tests.test_matrix_prepared_source import disclosed_certificate
    from tests.test_matrix_factor_confirmation_eligibility import publish
    from tests.test_recursive_public_service import _plane
    programme = request.getfixturevalue(family)
    plane = _plane(tmp_path / "actual-guarded-publications")
    original = prepared_bank(programme, publisher=lambda record, name: publish(plane, record, name))
    assert original.audit.census == programme.sources.closure.audit.census
    assert original.reservation.allocation.roots == programme.sources.closure.reservation.allocation.roots
    assert original.reservation.allocation.coordinates == programme.sources.closure.reservation.allocation.coordinates
    assert original.reservation.allocation.matched_scopes == programme.sources.closure.reservation.allocation.matched_scopes
    template = disclosed_certificate(original, opportunity)
    file_path = Path(plane.root.contract.canonical_path) / "original-support.bin"
    file_raw = b"original FILE exposure support\n"
    file_path.write_bytes(file_raw)
    artifact = ArtifactIdentity("support.disclosed.initial-file", "disclosed-file-support",
        "empirical-lawhood/testing/checksummed-file", sha256(file_raw).hexdigest(), "application/octet-stream", len(file_raw))
    handle = ExperimentFileInputBinding("file.disclosed.initial", artifact, "1.0.0", file_path.name, len(file_raw))
    expected_candidate = object()
    native_request = SimpleNamespace(identity=template.native_training_request,
        candidate_specification=object() if damage == "candidate" else expected_candidate,
        future_manifest=SimpleNamespace(reservation=original.reservation, audit=original.audit), exposure_support=((artifact, handle),),
        input_commitments=original.input_commitments)
    public = SimpleNamespace(specification=expected_candidate)
    preparation = SimpleNamespace(manifest=SimpleNamespace(reservation=original.reservation))
    programme_inputs = SimpleNamespace(commitments=original.input_commitments.record)
    # This control supplies unexecuted C descriptors and replaces upstream
    # scientific custody. Exercise FILE guards without pretending that the
    # descriptor is a decoded, authenticated programme commitment.
    from empirical_lawhood.infrastructure import matrix_completed_source
    def original_commitment(writer, inputs, commitment):
        assert inputs is programme_inputs and commitment == original.input_commitments
        return commitment
    monkeypatch.setattr(matrix_completed_source, 'original_e3_commitment', original_commitment)
    facts = SimpleNamespace(request=native_request, acquisition=SimpleNamespace(identity=template.native_training_acquisition),
        programme=SimpleNamespace(identity=template.development_programme), controls=template.controls,
        input_commitments=original.input_commitments.record, effective_seeds=template.excluded_effective_seeds,
        group_ids=template.development_group_ids, coordinates=(original.source_arms()[0][1].coordinate,))
    locator = template.native_training_locator
    packet = SimpleNamespace(packet_id=locator.packet.object_id, SCHEMA=locator.packet.object_schema,
        VERSION=locator.packet.object_version, fingerprint=lambda: "f" * 64 if damage == "locator" else locator.packet.object_fingerprint)
    plan = SimpleNamespace(execution_plan_id=locator.execution_plan.object_id, SCHEMA=locator.execution_plan.object_schema,
        VERSION=locator.execution_plan.object_version, fingerprint=lambda: locator.execution_plan.object_fingerprint)
    run = SimpleNamespace(run_plan_id=locator.run_id)
    counts = {"preliminary": 0, "facts": 0, "certificate": 0}
    def preliminary(**_):
        counts["preliminary"] += 1
        return packet, object(), object(), object()
    monkeypatch.setattr(recursive_authoring, "load_authored_wave", preliminary)
    monkeypatch.setattr(recursive_execution, "_retained_plans", lambda *_: (run, plan, object()))
    monkeypatch.setattr(native_training_banks, "_read_instance", lambda _: (object(), native_request, object()))
    def source_facts(**arguments):
        counts["facts"] += 1
        assert arguments["locator"] == template.locator and arguments["request"] is native_request
        assert arguments["inputs"] is programme_inputs
        return facts
    monkeypatch.setattr(runtime, "_prepared_source_exposure_facts", source_facts)
    monkeypatch.setattr(runtime, "_native_training_prerequisite", lambda *_: (object(), native_request, object(), ()))
    publications = []
    def publication(name, record):
        stored = publish(plane, record, "facts-reuse." + name.replace("/", "."))
        publications.append(stored)
        if damage == "publication":
            file_path.write_bytes(b"x" * len(file_raw))
        return stored
    actual_validate = runtime._validate_prepared_source_certificate_bank
    def validate(writer, bank):
        actual_validate(writer, bank)
        if damage == "before-certificate":
            file_path.write_bytes(b"x" * len(file_raw))
    monkeypatch.setattr(runtime, "_validate_prepared_source_certificate_bank", validate)
    def certificate(**arguments):
        counts["certificate"] += 1
        assert arguments["facts"] is facts
        return replace(template, future_bank=arguments["bank"].identity, future_group_ids=arguments["bank"].group_ids)
    monkeypatch.setattr(runtime, "_prepared_source_certificate_from_facts", certificate)
    options = dict(writer=plane, programme_inputs=programme_inputs, public=public, preparation=preparation,
        actual_programme=SimpleNamespace(phase=programme.phase, sources=original.sources, assay=original.assay, panels=original.panels),
        development=template.locator, locator=locator, input_commitments=original.input_commitments,
        exposure_support=original.exposure_support, cutoff=template.cutoff, namespace="disclosed.facts-reuse",
        prefix="derived-facts-reuse", publication=publication)
    def reconstruct():
        # The public assembly owns this lifetime through its dependent writes;
        # this direct control supplies the same explicit ordinary byte scope.
        with plane.verification_scope() as writer:
            return api._prepared_source_bank_and_certificate(**dict(options, writer=writer))
    if damage is not None:
        reason = "native TRAIN candidate/reservation" if damage == "candidate" else "native TRAIN packet/run/plan" if damage == "locator" else "exact selected bytes"
        with pytest.raises((ValueError, PermissionError), match=reason):
            reconstruct()
        assert counts["preliminary"] == 1 and counts["certificate"] == 0
        assert counts["facts"] == int(damage not in ("candidate", "locator"))
        if damage in ("candidate", "locator"):
            assert not publications and not plane.root.resolve("derived-facts-reuse/current-exposure/support.json", for_write=False).exists()
        return
    bank, result, returned_request = reconstruct()
    assert counts == {"preliminary": 1, "facts": 1, "certificate": 1} and returned_request is native_request
    assert result.future_bank == bank.identity and file_path.read_bytes() == file_raw
    if family == "transfer":
        assert bank.sources is original.sources and bank.audit == original.audit and not publications
    else:
        assert bank.audit != original.audit and publications
        assert set(facts.group_ids) <= set(bank.audit.census.exposed_independent_groups)
    # The independent public reconstruction opens fresh whole-C custody on a
    # later call; this unit keeps only that original-custody seam disclosed.
    from contextlib import contextmanager
    @contextmanager
    def current_facts(**arguments):
        assert arguments["input_commitments"] == original.input_commitments
        assert arguments["maximum_source_bytes"] == 128 * 1024**2
        counts["facts"] += 1
        yield facts
    monkeypatch.setattr(runtime, "prepared_source_exposure_facts", current_facts)
    standalone = runtime.certify_prepared_source_instrument(writer=plane, locator=template.locator,
        native_training_locator=locator, bank=bank, cutoff=template.cutoff, record_id="certificate.disclosed.facts-reuse",
        maximum_source_bytes=128 * 1024**2)
    assert counts == {"preliminary": 1, "facts": 2, "certificate": 2}
    assert standalone.canonical_bytes() == result.canonical_bytes()
