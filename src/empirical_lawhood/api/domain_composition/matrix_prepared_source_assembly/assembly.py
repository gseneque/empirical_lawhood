# SPDX-License-Identifier: MPL-2.0
"""Authenticated prepared finite-dt source assembly from actual selected evidence.

CONF adds the exact authenticated TRAIN/E3/E4/E5 DEV exposure union. E6 keeps
its original audit/reserve/panels. Actual fresh E5 DEV custody remains required.
"""
from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import MatrixScheduledPhysicalExclusion
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

def source_root_from_e3(*, original, programme, bank, certificate, cutoff, computability,
        budget, namespace, scientific_pins, confidence, discrepancy_tolerance):
    """Declare source-specific obligations from actual E3 numerical definitions.

    This is a new prospective design. It copies no old READY state, qualified
    source, authorization, proposer act, formal entry or scientific outcome.
    The genuine numerical world, represented/unrepresented physics, relation,
    paired views and explicit computability evidence retain their real scope.
    """
    from empirical_lawhood.adapters.composition.experiment_authoring import single_experiment_campaign
    from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as r
    from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
    from empirical_lawhood.kernel.evidence import ClaimSpec, OutcomeAccess
    from empirical_lawhood.kernel.experiments import ControlKind, ControlSpec, PrecisionGoal, RevealBarrierSpec
    from empirical_lawhood.kernel.obligations import (
        ClosureSpec, FalsifierKind, FalsifierSpec, ObligationStatus, ScientificObligations,
        StructuralConvergenceSpec, SupportSpec, UncertaintySpec, ValiditySpec,
    )
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.kernel.status import ReadinessStatus
    from empirical_lawhood.kernel.worlds import WorldKind
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateKind
    from empirical_lawhood.planning.study_authoring import (
        DesignInputRecord, DesignInputRole, DesignOrigin, DesignOriginKind, StudyDraft, StudyDraftLifecycle,
    )
    original.__post_init__()
    computability.__post_init__()
    if original.system is None or original.experiment is None or original.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR:
        raise ValueError("source design requires its actual original E3 numerical system")
    system = original.system
    views = tuple(value.view_id for value in system.numerical_views)
    if (not views or computability.numerical_view_ids != tuple(sorted(views))
            or computability.envelope_id not in {value.envelope_id for value in system.computability_envelopes}
            or cutoff.clock_id not in {value.clock_id for value in system.clocks}):
        raise ValueError("explicit source computability/cutoff changes actual E3 paired views, envelope or physical clock")
    physical_cutoffs = r.prepared_source_cutoffs(tuple(source for _, source in bank.source_arms()), cutoff)
    if any(value.clock_id not in {clock.clock_id for clock in system.clocks} for value in physical_cutoffs):
        raise ValueError("source design omits an actual original regime clock")
    prefix = namespace
    source_system_id = prefix + ".system"
    aggregate = ResourceBudget.aggregate((budget,) * (len(r.GATES) + 3))
    if not system.authority_policy.budget_ceiling.contains(aggregate):
        raise ValueError("actual Matrix policy must contain the complete selected source resource aggregate")
    # A new declaration of already delegated scope is not a grant or human act.
    policy = replace(system.authority_policy, policy_id=prefix + ".policy", budget_ceiling=aggregate,
        scope_ids=tuple(sorted({*system.authority_policy.scope_ids, source_system_id})))
    interfaces = tuple(replace(value,
        source=replace(value.source, owner_id=source_system_id) if value.source.owner_id == system.system_id else value.source,
        target=replace(value.target, owner_id=source_system_id) if value.target.owner_id == system.system_id else value.target)
        for value in system.interfaces)
    system = replace(system, system_id=source_system_id, authority_policy=policy, interfaces=interfaces)
    relation = system.relation
    unit = system.independent_unit.unit_id
    groups = programme.group_ids
    required = ObligationStatus.REQUIRED
    independent_control = bindings.gate_declaration(ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY, bank.phase).manifest()
    uncertainty = UncertaintySpec(prefix + ".uncertainty", prefix + ".global-qualification-not-established", unit,
        confidence, relation.receiver_quantity_ids,
        ("CONTINUUM_NOT_ESTABLISHED", "NO_FUTURE_PREPARED_OUTCOME_READ", "SAMPLING_NOT_ESTABLISHED", "TRANSPORT_NOT_ESTABLISHED"), required)
    obligations = ScientificObligations(prefix + ".single-terminal",
        SupportSpec(prefix + ".support", relation.relation_id, unit, len(groups), len(views), cutoff.cutoff_id,
            (bank.assay.identity.object_id,), (bank.identity.object_id,), (), required),
        ValiditySpec(prefix + ".validity", (bank.identity.object_id,),
            ("ACTUAL_PREPARED_DEV_INDEPENDENT_CONTROLS", "EXACT_FUTURE_SOURCE_ROSTER", "FINITE_DT_INSTRUMENT_ONLY"),
            ("ADVERSE_OR_MISSING_NATIVE_CONTROL", "NO_SAMPLING_OR_TRANSPORT_WARRANT", "NO_USABLE_ORIGIN_RETAINED"), required),
        uncertainty,
        (FalsifierSpec(prefix + ".falsifier", FalsifierKind.STRUCTURAL_CONVERGENCE,
            independent_control.capability_key, "Replay the actual independent native trajectory, OU, frame and response controls.",
            "Every actual E5 DEV independent control and nonuse must remain visible; failed or absent instrument support is UNEVALUABLE.", required),),
        ClosureSpec(prefix + ".closure", (bank.identity.object_id,),
            tuple(sorted({source.recipe.recipe_id for _, source in bank.source_arms()})), relation.history_quantity_ids, required),
        StructuralConvergenceSpec(prefix + ".convergence", (certificate.identity.object_id,), tuple(sorted(views)), (), required),
        computability)
    ceiling = bindings.closeout_declaration().manifest().maximum_evidence_ceiling
    question = "Assess the finite-dt instrument source premises for the complete prospective prepared " + bank.phase + " bank."
    claim = ClaimSpec(prefix + ".claim", system.world.world_id, relation.relation_id, question,
        "Exact source/instrument contract predicates; future prepared outcomes, global scientific qualification, continuum, sampling and transport remain unestablished.",
        unit, None, ceiling, OutcomeAccess.EVALUATION_SEALED, r.PROSPECTIVE,
        "No rung promotion is requested by this source-only closeout; downstream measurements require their own actual acquisition and assessment.",
        ("COMPLETE_INDEPENDENT_GROUP_DENOMINATOR", "FINITE_DT_ONLY", "ORIGINAL_CONTROLS_AND_NONUSE_RETAINED"),
        numerical_view_ids=tuple(sorted(views)))
    controls = (ControlSpec(prefix + ".control", ControlKind.BASELINE_COMPARATOR, independent_control.capability_key,
        relation.receiver_quantity_ids, "Mandatory independent numerical/instrument controls are replayed from actual complete E5 DEV custody, including HOLD, recipe arms, failures and nonuse."),)
    precision = (PrecisionGoal(prefix + ".precision", prefix + ".frozen-instrument-target-discrepancy",
        discrepancy_tolerance, "dimensionless-response-error", len(groups),
        "Read the complete original E5 DEV controls and assigned future source roster once; acquire no future outcome and perform no top-up."),)
    training_groups = tuple(sorted({value.group_id for value in certificate.controls}))
    reveal = RevealBarrierSpec(prefix + ".reveal", training_groups, prefix + ".future-source-cohort",
        sha256(canonical_json_bytes(groups)).hexdigest(), (prefix + ".sealed-source-closeout",),
        OutcomeAccess.EVALUATION_SEALED, True)
    experiment = replace(original.experiment, experiment_id=prefix + ".experiment", system_id=system.system_id,
        claims=(claim,), controls=controls, precision_goals=precision, information_cutoffs=physical_cutoffs,
        reveal_barrier=reveal, obligations=obligations, authority_policy_id=policy.policy_id,
        readiness=ReadinessStatus.AUTHORITY_REQUIRED, authorization_record_id=None,
        predecessor_experiment_ids=(original.experiment.experiment_id,))
    campaign = single_experiment_campaign(system, experiment, prefix=prefix, budget=aggregate, objective=question,
        actions=(("execute", AuthorityAction.SIMULATION_EXECUTION),
            ("freeze", AuthorityAction.NONACTUATING_PROSPECTIVE_FREEZE), ("reveal", AuthorityAction.EVALUATOR_REVEAL)))
    pins = tuple(sorted(set(scientific_pins), key=lambda value: value.object_id))
    designs = tuple(DesignInputRecord(prefix + ".design." + str(index), pin, pin.object_fingerprint, cutoff,
        DesignInputRole.READINESS_METADATA, r.BLIND, r.PROSPECTIVE, policy.delegate_id)
        for index, pin in enumerate(pins))
    designs = tuple(sorted(designs, key=lambda value: value.input_id))
    return StudyDraft(prefix + ".draft", StudyDraftLifecycle.DRAFT, question,
        ("FINITE_DT_INSTRUMENT_SOURCE_PREMISES_ONLY",),
        DesignOrigin(prefix + ".origin", DesignOriginKind.ORDINARY_THEORY_PREDECLARED,
            tuple(value.input_id for value in designs), r.PROSPECTIVE), designs, training_groups, groups, (), (), (),
        system, experiment, campaign, prefix + ".pending-template", (), (), aggregate)


def current_confirmation_sources(*, programme, facts, namespace, publication, audit_publication):
    """Declare current CONF metadata from actual owner projections.

    This changes no root/group, stream, physical coordinate, recipe, initial
    state, assay or outcome. It creates no altered public consumer projection;
    the ordinary declarative owner builds the new consumer from these sources. E4 committed streams are conservatively excluded;
    their execution is not asserted. Original records remain retained inputs.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit, corpus_artifact
    if programme.phase != 'E5_CONFIRMATION':
        raise ValueError('current exposure projection applies only to new unacquired CONF sources')
    old = programme.sources.closure
    baseline = facts.request.future_manifest.audit
    current = old.audit.census
    def merge(values, *, name):
        rows = {}
        for value in values:
            key = getattr(value, name)
            if rows.setdefault(key, value) != value:
                raise ValueError('current exposure aliases unchanged historical metadata: ' + key)
        return tuple(rows[key] for key in sorted(rows))
    # Preserve the immutable baseline and conservatively add actual selected
    # sequence facts. This union does not assert that reserved RNG was used.
    provenance=merge((*baseline.census.factual_provenance,*current.factual_provenance,
        corpus_artifact(audit_publication)),name='artifact_id')
    census = replace(current, census_id='census.' + namespace + '.current-conf',
        effective_seed_exclusions=tuple(sorted({*baseline.census.effective_seed_exclusions,
            *current.effective_seed_exclusions,*facts.effective_seeds})),
        constant_physical_exclusions=tuple(sorted({*baseline.census.constant_physical_exclusions,
            *current.constant_physical_exclusions},key=lambda value:value.fingerprint())),
        scheduled_physical_exclusions=tuple(sorted({*baseline.census.scheduled_physical_exclusions,
            *current.scheduled_physical_exclusions,
            *(MatrixScheduledPhysicalExclusion.from_coordinate(value) for value in facts.coordinates)},
            key=lambda value:value.fingerprint())),
        exposed_independent_groups=tuple(sorted({*baseline.census.exposed_independent_groups,*current.exposed_independent_groups,*facts.group_ids})),
        exposed_regimes=tuple(sorted({*baseline.census.exposed_regimes,*current.exposed_regimes})),
        exposed_artifact_sha256s=tuple(sorted({*baseline.census.exposed_artifact_sha256s,*current.exposed_artifact_sha256s,
            audit_publication.logical.content_sha256})),factual_provenance=provenance)
    coordinates=merge((*baseline.prior_scheduled_coordinates,*old.audit.prior_scheduled_coordinates,*facts.coordinates),name='coordinate_id')
    originals={(value.SCHEMA,value.fingerprint()):pub for audit in (baseline,old.audit)
        for value in (audit.census,*audit.prior_scheduled_coordinates) for pub in audit.prior_corpus
        if (pub.logical.payload_schema,pub.logical.content_sha256)==(value.SCHEMA,value.fingerprint())}
    corpus=[]
    for value in (census,*coordinates):
        stored=originals.get((value.SCHEMA,value.fingerprint()))
        if stored is None:
            stored=publication('current-exposure/corpus.' + value.fingerprint(),value)
        corpus.append(stored)
    audit=ScheduledExposureAudit('audit.' + namespace + '.current-conf',census,coordinates,
        tuple(sorted(corpus,key=lambda value:value.logical.logical_artifact_id)))
    stored_audit=publication('current-exposure/audit',audit)
    old_allocation=old.reservation.allocation
    allocation=replace(old_allocation,allocation_id='allocation.' + namespace + '.current-conf',
        exposure=replace(old_allocation.exposure,census=census,prior_scheduled_coordinates=coordinates,
            scheduled_audit=corpus_artifact(stored_audit)))
    stored_allocation=publication('current-exposure/allocation',allocation)
    reservation=scheduled.ScheduledReservation('reservation.' + namespace + '.current-conf',allocation,stored_allocation)
    selection=replace(old.specification.selection,selection_id='selection.' + namespace + '.current-conf',
        reservation=scheduled.identity(reservation))
    stored_selection=publication('current-exposure/native-selection',selection)
    specification=scheduled.ScheduledSpecification('specification.' + namespace + '.current-conf',selection,stored_selection)
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=old.provenances)
    references=tuple(index.reference(source_id=descriptor.source_id, root_id=descriptor.root_id,
        provenance=descriptor.provenance) for descriptor in old.descriptors)
    subjects=tuple(index.resolve(reference) for reference in references)
    # The current audit creates new original source identities. Declared V2
    # initialization metadata must name those exact sources, while retaining
    # its deterministic state/array, clock, root and producing provenance.
    # Historical observed V1 initialization records remain byte-for-byte.
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationInitialStateV2
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    prior_initials=dict(old.initial_states)
    initial_states=tuple((subject.root_id,replace(prior_initials[subject.root_id],
        state_id='initial.' + namespace + '.current-conf.' + prior_initials[subject.root_id].fingerprint(),
        original=ScheduledPublicSource.from_source(subject))
        if type(prior_initials[subject.root_id]) is MatrixPreparationInitialStateV2 else prior_initials[subject.root_id])
        for subject in subjects)
    closure=replace(old,record_id='closure.' + namespace + '.current-conf',reservation=reservation,specification=specification,
        descriptors=references,audit=audit,audit_publication=stored_audit,
        initial_states=initial_states)
    sources=replace(programme.sources,record_id='sources.' + namespace + '.current-conf',closure=closure)
    support=current_exposure_support(audit)
    publication('current-exposure/protected-sources',sources)
    return sources,support


@contextmanager
def assembled_prepared_source_inputs(*,assembly_specification,assembly_inputs,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution,read_access=None):
    from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as r
    from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
    from empirical_lawhood.adapters.methods import matrix_prepared_source_pipeline as rows_owner
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import (
        publish_finite_dt_source_metadata)
    from ...selected_e4_bank_recipe import _current_selection, _read_exact_record, _publication_from_manifest
    from ...matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
    from ...matrix_programme_e4_inputs import authenticated_programme_e4_banks, prepared_source_lineage, _require_original_e3_access
    from ...matrix_programme_e4_inputs import _preparation_kind
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.worlds import WorldKind
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import MatrixPreparedSourceAssemblyInputs,validate_inputs
    from empirical_lawhood.api.recursive_authoring import implementation_binding


    if type(assembly_inputs) is not MatrixPreparedSourceAssemblyInputs:
        raise TypeError('prepared source preprocessing requires exact typed input bindings')
    validate_inputs(assembly_specification,assembly_inputs,complete=True)
    assembly_request=assembly_inputs.request
    actual_programme=assembly_inputs.prepared_programme
    development=assembly_inputs.development_product
    from empirical_lawhood.api.selected_prepared_access import _selected
    current_originals=_selected(assembly_request.original_products,read_access)
    project=Path(project_root).resolve(strict=True);writer=artifact_writer
    directory=Path(metadata_directory);external_root=Path(writer.root.contract.canonical_path)
    if (not directory.is_absolute() or directory!=directory.resolve(strict=False)
            or Path(output_selection_path)!=directory/'sources.json'):
        raise ValueError('prepared source preprocessing requires exact guarded metadata directory and <metadata>/sources.json target')
    prefix=directory.relative_to(external_root).as_posix()
    writer.root.resolve(prefix+'/sources.json',for_write=True)
    if execution.output_root!=str(external_root) or any(value is None for value in (execution.workers,execution.environment_id,execution.source_snapshot)):
        raise ValueError('prepared source preprocessing requires explicit guarded root/current source/environment/workers')
    project, admitted = _current_selection(project_root=project, artifact_writer=writer, execution=execution)
    implementation=implementation_binding(project,_admitted_source=admitted)
    if ObjectIdentity.from_record('recursive-member.implementation',implementation)!=execution.source_snapshot:
        raise ValueError('prepared source preprocessing source differs from actual selected executing implementation')
    if execution.workers!=assembly_request.operational_resources.controls.maximum_parallel_tasks:
        raise ValueError('prepared source controls and selected workers differ')
    namespace=assembly_request.namespace
    selected={name:getattr(assembly_request,name) for name in ('metadata_issuer_id','metadata_approver_id','metadata_requester_id',
        'metadata_validity_seconds','metadata_reason_codes','metadata_valid_from_utc','licence_id','scratch_namespace')}
    selected_start=assembly_request.metadata_valid_from_utc
    seconds=assembly_request.metadata_validity_seconds;reasons=assembly_request.metadata_reason_codes
    key_path=writer.root.resolve(assembly_request.metadata_private_key_relative_path,for_write=True)
    if key_path.is_relative_to(directory):
        raise ValueError('select an operational metadata key outside the source publication directory')
    if not key_path.exists() and not assembly_request.allow_metadata_key_creation:
        raise PermissionError('actual metadata key is absent; supply its provider file or explicitly select ordinary key creation')
    publications=[]
    def publication(name, record, *, relative=None, logical=None, lineage_parents=()):
        from empirical_lawhood.api.matrix_source_input_assembly import publish_source_input_record
        if name == "current-exposure/protected-sources":
            # This actual CONF projection embeds its selected source/model.
            # Audit/allocation/reservation/control publications remain blind.
            if type(record) is not type(actual_programme.sources) or lineage_parents:
                raise PermissionError("current CONF source changes its exact model input publication role")
            lineage_parents = prepared_source_lineage(original_e3=assembly_request.original_e3,
                development_product=development)
        if lineage_parents:
            _require_original_e3_access(writer=writer, original_e3=assembly_request.original_e3,
                original_products=current_originals)

        result, observed = publish_source_input_record(writer=writer, prefix=prefix, namespace=namespace,
            name=name, record=record, relative=relative, logical=logical, lineage_parents=lineage_parents,
            model_input=bool(lineage_parents))

        publications.append(result)
        return observed
    def retained(name, kind):
        relative = prefix + "/" + name + ".json"
        path = writer.root.resolve(relative, for_write=False)
        if not path.exists():
            return None
        # Recreate the exact expected request from a complete canonical primary.
        # The ordinary writer owns commit/intent checks and partial-sidecar
        # recovery; this never treats an uncommitted primary as custody evidence.
        # A truncated dynamic policy/authorization still refuses: its missing
        # original bytes cannot be inferred from a fresh clock or signature.
        raw = read_bounded_bytes(path, maximum_bytes=assembly_request.source_budget.source_scan_bytes)
        value = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        if raw != value.canonical_bytes():
            raise PermissionError("retained control primary changes its exact canonical bytes")
        return _read_exact_record(writer, publication(name, value), kind, maximum_bytes=assembly_request.source_budget.source_scan_bytes)
    with writer.verification_scope() as writer, authenticated_programme_e4_banks(artifact_writer=writer,
            input_commitments=assembly_request.input_commitments, original_e3=assembly_request.original_e3,
            original_preparation=assembly_request.original_preparation, original_assay=assembly_request.original_assay,
            original_products=current_originals, native_training_locator=assembly_request.native_training_locator,
            maximum_source_bytes=assembly_request.source_budget.source_scan_bytes) as composed:
        require_admitted_target_source_current(project,admitted)
        if capture_matrix_provenance(project_root=project,_admitted_source=admitted) != composed.inputs.producing_provenance:
            raise ValueError("prepared source C changes the actual selected numerical/source provenance")
        preparation = _read_exact_record(writer, assembly_request.original_preparation.publication,
            _preparation_kind(assembly_request.original_preparation), maximum_bytes=assembly_request.source_budget.source_scan_bytes)
        assay = _read_exact_record(writer, assembly_request.original_assay.publication,
            ScheduledResponseProtocol, maximum_bytes=assembly_request.source_budget.source_scan_bytes)
        public = composed.original_e3
        original = preparation.root
        if (original.system is None or original.experiment is None
                or original.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
                or original.system.world.maximum_evidence is EvidenceCeiling.NON_PROMOTABLE
                or public.models.training_features.object_schema != native.NativeTrainingFeatureBank.SCHEMA
                or public.models.training_outcomes.object_schema != native.NativeTrainingOutcomeBank.SCHEMA):
            raise ValueError("select the genuine native-trained E3 numerical world and original producer operands")
        computability = assembly_request.source_computability_evidence
        operational = assembly_request.operational_resources
        if operational.controls.maximum_parallel_tasks != execution.workers:
            raise ValueError("source controls and selected worker count differ")
        budget = assembly_request.source_budget
        envelope = assembly_request.dataset_work_envelope
        cutoff = assembly_request.physical_cutoff
        if actual_programme.phase not in ('E5_CONFIRMATION', 'E6_TRANSFER'):
            raise ValueError('prepared source selects exact protected CONF or reserved transfer sources')
        r.prepared_source_cutoffs(tuple(source for _, source in actual_programme.sources.source_arms()), cutoff)
        exposure_support=assembly_request.exposure_support
        if actual_programme.assay != MatrixPreparedAssayMethod.from_protocol(actual_programme.assay.record_id, assay):
            raise ValueError('prepared source changes the original immutable native response assay')
        locator=assembly_request.native_training_locator
        bank, certificate, training_request = _prepared_source_bank_and_certificate(writer=writer,
            programme_inputs=composed.inputs, public=public, preparation=preparation, actual_programme=actual_programme, development=development,
            locator=locator, input_commitments=assembly_request.input_commitments,
            exposure_support=exposure_support,
            cutoff=cutoff, namespace=namespace, prefix=prefix, publication=publication,current_access=read_access)
        # Publish the exact blind reservation after actual bank/certificate auth.
        # Custody is added; the original canonical reservation stays unchanged.
        publication("prepared-reservation", bank.sources.closure.reservation)
        programme=bank
        produced_parents = prepared_source_lineage(original_e3=assembly_request.original_e3, development_product=development)
        root = source_root_from_e3(original=original, programme=programme, bank=bank, certificate=certificate,
            cutoff=cutoff, computability=computability, budget=budget, namespace=namespace,
            confidence=1 - public.specification.calibration_alpha,
            discrepancy_tolerance=public.specification.measurement.target_discrepancy_tolerance,
            scientific_pins=(bank.identity, certificate.identity, bank.sources.identity,
                public.identity, training_request.identity, development.identity,
                ObjectIdentity.from_record(computability.computability_id, computability), r.pin(cutoff, 'cutoff_id')))
        publication("scientific-root." + root.fingerprint(), root, lineage_parents=produced_parents)
        rows = rows_owner.MatrixPreparedPendingSourceRows.from_bank(programme, bank, record_id="rows." + namespace)
        rule = rows_owner.MatrixPreparedSourceValidationRule("rule." + namespace, programme.identity, bank.identity, rows.identity)
        from empirical_lawhood.api.matrix_source_input_assembly import materialize_source_input_rows,prepare_source_candidate
        materialized,evidence_profile=materialize_source_input_rows(writer=writer,project=project,prefix=prefix,
            namespace=namespace,selected=selected,key_path=key_path,selected_start=selected_start,seconds=seconds,reasons=reasons,
            implementation=implementation,publication=publication,retained=retained,rows=rows,rule=rule,bank=bank,
            programme=programme,cutoff=cutoff,envelope=envelope,root=root,rows_owner=rows_owner,r=r,certificate=certificate,
            assay_identity=bank.assay.identity,verification_kind=rows_owner.MatrixPreparedSourceVerification)
        scope = r.MatrixPreparedSourceScope('scope.' + namespace, bank.identity, bank.sources.closure.identity,
            bank.sources.identity, bank.assay.identity, bank.sources.closure.numerical_scope,
            identity(training_request.future_manifest.reservation), certificate.identity, cutoff, programme.group_ids,
            materialized.config.profile, materialized.config.assess(), evidence_profile,
            materialized.verification.identity, materialized.verification.identity, budget)
        metadata_publications=publish_finite_dt_source_metadata(writer=writer,scope=scope,
            materialization=materialized,output_directory=directory/'metadata')
        metadata_publications=tuple((reference,_publication_from_manifest(writer,
            writer.read_manifest(stored.materialization.relative_path))) for reference,stored in metadata_publications)
        operands = {'scope': scope, 'bank': bank, 'source': bank.sources.closure, 'preparation': bank.sources,
            'original-reservation': training_request.future_manifest.reservation, 'assay': bank.assay,
            'numerical': bank.specification.selection.numerical_design, 'cutoff': cutoff, 'certificate': certificate}
        operand_lineage = {name: produced_parents if name in ('bank', 'source', 'preparation') else () for name in operands}
        prospective,configs,authoring,lowered,entry,terminals=prepare_source_candidate(writer=writer,project=project,
            namespace=namespace,publication=publication,domain=domain,bindings=bindings,scope=scope,operands=operands,
            materialized=materialized,root=root,budget=budget,operational=operational,implementation=implementation,programme=programme,
            operand_lineage=operand_lineage, model_input_names=frozenset(("bank", "source", "preparation")))
        supports = bank.exposure_support
        selected_source = domain.MatrixPreparedSourceQualificationSelection("selection." + namespace, scope, bank, training_request.future_manifest.reservation, certificate, rows, rule, materialized.source_publication,
            materialized.output_publication, materialized.verification, materialized.verification_publication,
            materialized.config, prospective, tuple(sorted(configs, key=lambda value: value.fingerprint())),
            supports, metadata_publications, terminals)
        specification = domain.MatrixPreparedSourceQualificationSpecification("specification." + namespace,
            selected_source.identity, execution.workers)
        bound_inputs = domain.MatrixPreparedSourceInputs(selected_source, assembly_request, development)
        preparation = domain.prepare(specification, scientific_inputs={"source": domain.source_allocation(selected_source)},
            method_inputs=bound_inputs, execution=execution)
        if preparation.dependencies:
            raise ValueError("source preparation retains actual dependencies: " + str(preparation.dependencies))
        publication("specification", specification)
        publication("selection", selected_source, lineage_parents=produced_parents)
        publication("source-request", assembly_request)
        publication("development.0", development)
        publication("authoring-base", replace(authoring, draft=lowered.prospective_draft, entry_package=entry), lineage_parents=produced_parents)
        source_selection = ExperimentFileInputSelection("sources." + namespace, domain.PROTOCOL_ID,
            tuple(sorted((ExperimentInputBinding("selection", selected_source.identity, "selection.json", len(selected_source.canonical_bytes())),
                ExperimentInputBinding("source-request", assembly_request.identity, "source-request.json", len(assembly_request.canonical_bytes())),
                ExperimentInputBinding("development.0", development.identity, "development.0.json", len(development.canonical_bytes()))),
                key=lambda value: value.key)), ())
        publication("sources", source_selection)

        yield specification,source_selection,directory/"specification.json",tuple(publications)
        require_admitted_target_source_current(project,admitted)


def _prepared_source_bank_and_certificate(*, writer, programme_inputs, public, preparation, actual_programme, development, locator,
        input_commitments, exposure_support, cutoff, namespace, prefix, publication,current_access=None):
    """Consume the complete TRAIN/DEV source facts once in this guarded derivation.

    Source grants and later author/run/read calls retain their fresh admissions.
    Only immutable bank, certificate and request values leave this invocation.
    """
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as r
    from ...matrix_prepared_source_runtime import (
        _native_training_prerequisite, _prepared_source_exposure_facts, _prepared_source_certificate_from_facts,
        _validate_prepared_source_certificate_bank,
    )
    from ...selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
    from empirical_lawhood.api.native_training_banks import _read_instance
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.api.matrix_finite_dt_source_runtime import _verify_file_supports
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding

    writer.require_verification_context()
    # Keep the existing fast metadata/locator/candidate refusal before
    # either complete TRAIN or E5 development product traversal.
    packet,draft,_,payloads=load_authored_wave(directory=writer.root.resolve(locator.authored_directory,for_write=False),
        artifact_writer=writer,lazy_payloads=True)
    _,training_request,_=_read_instance(payloads)
    run,plan,_=_retained_plans(payloads,draft)
    actual_locator=MatrixFiniteDtTrainingLocator(locator.authored_directory,run.run_plan_id,
        ObjectIdentity.from_record(packet.packet_id,packet),ObjectIdentity.from_record(plan.execution_plan_id,plan))
    if actual_locator!=locator:
        raise PermissionError('prepared source preprocessing substitutes completed native TRAIN packet/run/plan')
    if (training_request.candidate_specification != public.specification
            or training_request.future_manifest.reservation != preparation.manifest.reservation):
        raise ValueError("source sequence substitutes its actual original native TRAIN candidate/reservation")
    training_specification, actual_request, acquisition, future = _native_training_prerequisite(writer, locator)
    if actual_request != training_request:
        raise PermissionError('prepared source changes its exact original TRAIN request or whole C during source reconstruction')
    from empirical_lawhood.infrastructure.matrix_completed_source import original_e3_commitment
    e3_commitment = original_e3_commitment(writer, programme_inputs, input_commitments)
    if training_request.input_commitments != e3_commitment:
        from empirical_lawhood.infrastructure.matrix_retained_training import read_retained_training_source
        # The enclosing E4 input owner holds the complete original/continued C
        # proof alive. Match this second native read to that exact source link.
        retained = read_retained_training_source(writer, programme_inputs.commitments)
        if (retained.input_commitments != training_request.input_commitments
                or retained.training_locator != locator
                or retained.export_adoption.request != training_request.identity
                or retained.export_adoption.specification != training_specification.identity):
            raise PermissionError('prepared source changes its exact retained TRAIN source lineage')
    facts = _prepared_source_exposure_facts(writer=writer, locator=development, request=training_request,
        acquisition=acquisition, future=future, inputs=programme_inputs, training_specification=training_specification,current_access=current_access)
    # Preserve the original initial publication/FILE admission once.
    for artifact, custody in exposure_support:
        _authenticate_artifact(writer, artifact, custody)
    initial_files = tuple((artifact, custody) for artifact, custody in
        (*training_request.exposure_support, *exposure_support)
        if type(custody) is ExperimentFileInputBinding)
    def require_source_inputs():
        writer.require_verification_snapshot()
        # FILE bytes have no publication snapshot. Keep initial handles
        # even when CONF replaces the current audit support publication.
        current_files = tuple((artifact, custody) for artifact, custody in exposure_support
            if type(custody) is ExperimentFileInputBinding)
        _verify_file_supports(writer, tuple(dict.fromkeys((*initial_files, *current_files))))
        writer.require_verification_snapshot()
    def publish_current(*args, **kwargs):
        require_source_inputs()
        result = publication(*args, **kwargs)
        require_source_inputs()
        return result
    require_source_inputs()
    projected_sources=actual_programme.sources
    if actual_programme.phase == 'E5_CONFIRMATION':
        report={'scope':'SELECTED_FRESH_SEQUENCE_EXPOSURE_EXCLUSIONS_NO_GLOBAL_QUALIFICATION',
            'original_native_request':facts.request.identity.to_document(),
            'original_native_acquisition':facts.acquisition.identity.to_document(),
            'actual_development_programme':facts.programme.identity.to_document(),
            'actual_development_locator':development.to_document(),
            'original_input_commitments':facts.input_commitments.to_document(),
            'e4_stream_policy':'CONSERVATIVELY_EXCLUDE_ALL_COMMITTED_BANKS_EXECUTION_NOT_ASSERTED',
            'input_audit':ObjectIdentity.from_record(actual_programme.sources.closure.audit.audit_id,actual_programme.sources.closure.audit).to_document()}
        raw=json.dumps(report,sort_keys=True,separators=(',',':')).encode()
        require_source_inputs()
        support_publication=writer.write(ArtifactWriteRequest('current-exposure-support.'+namespace,
            prefix+'/current-exposure/support.json','empirical-lawhood/source/checksummed-uninterpreted-public-bytes',
            ArtifactProfile.RAW_SOURCE_BYTES,'text/plain','current-exposure.'+namespace,prefix+'/current-exposure',
            raw,r.PROSPECTIVE,(),r.BLIND))
        require_source_inputs()
        support_publication=_publication_from_manifest(writer,
            writer.read_manifest(support_publication.materialization.relative_path))
        projected_sources,exposure_support=current_confirmation_sources(programme=actual_programme,facts=facts,
            namespace=namespace,publication=publish_current,audit_publication=support_publication)
    bank = r.MatrixPreparedSourceBank('bank.'+namespace,projected_sources,actual_programme.assay,
        actual_programme.panels,exposure_support,input_commitments)
    _validate_prepared_source_certificate_bank(writer, bank)
    require_source_inputs()
    certificate = _prepared_source_certificate_from_facts(writer=writer, locator=development,
        native_training_locator=locator, bank=bank, cutoff=cutoff, record_id='certificate.' + namespace, facts=facts)
    require_source_inputs()
    return bank, certificate, training_request


def assemble_prepared_source_inputs(*, assembly_specification, assembly_inputs, project_root,
        artifact_writer, metadata_directory, output_selection_path, execution,read_access=None):
    """Standalone assembly keeps the original whole C guard through return."""
    with assembled_prepared_source_inputs(assembly_specification=assembly_specification,
            assembly_inputs=assembly_inputs, project_root=project_root, artifact_writer=artifact_writer,
            metadata_directory=metadata_directory, output_selection_path=output_selection_path,
            execution=execution,read_access=read_access) as result:
        return result
