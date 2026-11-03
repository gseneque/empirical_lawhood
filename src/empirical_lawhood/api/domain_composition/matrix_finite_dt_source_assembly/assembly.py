# SPDX-License-Identifier: MPL-2.0
"""Actual typed finite-dt source preprocessing through existing production owners.

Metadata-only authorization is an explicit operational effect selected by the
request. No scientific study issue, human attestation, reveal or acquisition is
performed. Source comparators/nonuse retain their original actual custody.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from hashlib import sha256
from pathlib import Path


def source_root_from_e3(*, original, programme, bank, certificate, cutoff, computability,
        budget, namespace, scientific_pins):
    """Declare source-specific obligations from actual E3 numerical definitions.

    This is a new prospective design. It copies no old READY state, qualified
    source, authorization, proposer act, formal entry or scientific outcome.
    The genuine numerical world, represented/unrepresented physics, relation,
    paired views and explicit computability evidence retain their real scope.
    """
    from empirical_lawhood.adapters.composition.experiment_authoring import single_experiment_campaign
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_bindings as bindings
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
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
    independent_control = bindings.gate_declaration(ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY).manifest()
    uncertainty = UncertaintySpec(prefix + ".uncertainty", prefix + ".global-qualification-not-established", unit,
        bank.design.confidence, relation.receiver_quantity_ids,
        ("CONTINUUM_NOT_ESTABLISHED", "NO_FUTURE_E4_OUTCOME_READ", "SAMPLING_NOT_ESTABLISHED", "TRANSPORT_NOT_ESTABLISHED"), required)
    obligations = ScientificObligations(prefix + ".single-terminal",
        SupportSpec(prefix + ".support", relation.relation_id, unit, len(groups), len(views), cutoff.cutoff_id,
            (bank.response_selection.identity.object_id,), (bank.identity.object_id,), (), required),
        ValiditySpec(prefix + ".validity", (bank.identity.object_id,),
            ("ACTUAL_NATIVE_TRAIN_CONTROLS", "EXACT_FUTURE_SOURCE_ROSTER", "FINITE_DT_INSTRUMENT_ONLY"),
            ("ADVERSE_OR_MISSING_NATIVE_CONTROL", "NO_SAMPLING_OR_TRANSPORT_WARRANT", "NO_USABLE_ORIGIN_RETAINED"), required),
        uncertainty,
        (FalsifierSpec(prefix + ".falsifier", FalsifierKind.STRUCTURAL_CONVERGENCE,
            independent_control.capability_key, "Replay the actual independent native trajectory, OU, frame and response controls.",
            "Every retained original TRAIN control and nonuse must remain visible; failed or absent instrument support is UNEVALUABLE.", required),),
        ClosureSpec(prefix + ".closure", (bank.identity.object_id,),
            tuple(sorted(value.factor_id for value in bank.design.factors)), relation.history_quantity_ids, required),
        StructuralConvergenceSpec(prefix + ".convergence", (certificate.identity.object_id,), tuple(sorted(views)), (), required),
        computability)
    ceiling = bindings.closeout_declaration().manifest().maximum_evidence_ceiling
    question = "Assess the finite-dt instrument source premises for the complete prospective E4 " + bank.phase + " bank."
    claim = ClaimSpec(prefix + ".claim", system.world.world_id, relation.relation_id, question,
        "Exact source/instrument contract predicates; future E4 outcomes, global scientific qualification, continuum, sampling and transport remain unestablished.",
        unit, None, ceiling, OutcomeAccess.EVALUATION_SEALED, r.PROSPECTIVE,
        "No rung promotion is requested by this source-only closeout; downstream measurements require their own actual acquisition and assessment.",
        ("COMPLETE_INDEPENDENT_GROUP_DENOMINATOR", "FINITE_DT_ONLY", "ORIGINAL_CONTROLS_AND_NONUSE_RETAINED"),
        numerical_view_ids=tuple(sorted(views)))
    controls = (ControlSpec(prefix + ".control", ControlKind.BASELINE_COMPARATOR, independent_control.capability_key,
        relation.receiver_quantity_ids, "Mandatory independent numerical/instrument controls are replayed from actual retained native TRAIN custody."),)
    precision = (PrecisionGoal(prefix + ".precision", prefix + ".frozen-instrument-target-discrepancy",
        certificate.measurement.target_discrepancy_tolerance, "dimensionless-response-error", len(groups),
        "Read the complete original TRAIN controls and assigned future source roster once; acquire no future outcome and perform no top-up."),)
    training_groups = tuple(sorted({value.group_id for value in certificate.controls}))
    reveal = RevealBarrierSpec(prefix + ".reveal", training_groups, prefix + ".future-source-cohort",
        sha256(canonical_json_bytes(groups)).hexdigest(), (prefix + ".sealed-source-closeout",),
        OutcomeAccess.EVALUATION_SEALED, True)
    experiment = replace(original.experiment, experiment_id=prefix + ".experiment", system_id=system.system_id,
        claims=(claim,), controls=controls, precision_goals=precision, information_cutoffs=(cutoff,),
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



@contextmanager
def assembled_finite_dt_source_inputs(*,assembly_specification,assembly_request,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution):
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_experiment as domain
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_bindings as bindings
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_pipeline as rows_owner
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import (
        publish_finite_dt_source_metadata)
    from empirical_lawhood.api.matrix_finite_dt_source_runtime import certify_native_training_instrument
    from empirical_lawhood.api.selected_e4_bank_recipe import _read_exact_record, _publication_from_manifest
    from empirical_lawhood.api.matrix_programme_e4_inputs import published_programme_e4_inputs, original_e3_lineage, _require_original_e3_access
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.serialization import validate_stable_id
    from empirical_lawhood.kernel.worlds import WorldKind
    from empirical_lawhood.planning import dataset_authority as grants
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    from empirical_lawhood.planning.source_pipelines import (
        _validate_static_locator)

    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import (
        source_assembly_request_types)
    if type(assembly_request) not in source_assembly_request_types():
        raise TypeError('source preprocessing requires its exact typed request')
    assembly_request.__post_init__()
    if (assembly_specification.request!=assembly_request.identity
            or assembly_specification.REQUEST_TYPE is not type(assembly_request)):
        raise ValueError('source preprocessing changes its exact input request pin')
    project=Path(project_root).resolve(strict=True);writer=artifact_writer
    directory=Path(metadata_directory);external_root=Path(writer.root.contract.canonical_path)
    if (not directory.is_absolute() or directory!=directory.resolve(strict=False)
            or Path(output_selection_path)!=directory/'sources.json'):
        raise ValueError('source preprocessing requires exact guarded metadata directory and <metadata>/sources.json target')
    prefix=directory.relative_to(external_root).as_posix()
    writer.root.resolve(prefix+'/sources.json',for_write=True)
    if execution.output_root!=str(external_root) or any(value is None for value in (execution.workers,execution.environment_id,execution.source_snapshot)):
        raise ValueError('source preprocessing requires its explicit guarded root/current source/environment/workers')
    namespace=assembly_request.namespace
    selected={name:getattr(assembly_request,name) for name in ('metadata_issuer_id','metadata_approver_id','metadata_requester_id',
        'metadata_validity_seconds','metadata_reason_codes','metadata_valid_from_utc','licence_id','scratch_namespace','phase')}
    selected['metadata_private_key_file']=str(writer.root.resolve(assembly_request.metadata_private_key_relative_path,for_write=True))
    selected['native_training_directory']=str(writer.root.resolve(assembly_request.native_training_locator.authored_directory,for_write=False))
    implementation=implementation_binding(project)
    if ObjectIdentity.from_record('recursive-member.implementation',implementation)!=execution.source_snapshot:
        raise ValueError('source preprocessing source differs from actual selected executing implementation')
    publications=[]
    for field in ("metadata_issuer_id", "metadata_approver_id", "metadata_requester_id"):
        validate_stable_id(selected[field])
    if selected["metadata_requester_id"] == selected["metadata_approver_id"]:
        raise PermissionError("the actual dataset owner forbids requester self-approval")
    _validate_static_locator(selected["scratch_namespace"], field_name="scratch_namespace")
    if not isinstance(selected["licence_id"], str) or not selected["licence_id"].strip():
        raise ValueError("select the actual source licence identifier")
    seconds = selected["metadata_validity_seconds"]
    reasons = tuple(selected["metadata_reason_codes"])
    if type(seconds) is not int or seconds <= 0 or not reasons or reasons != tuple(sorted(set(reasons))):
        raise ValueError("select positive metadata grant validity and sorted unique reason codes")
    selected_start = selected.get("metadata_valid_from_utc")
    if selected_start is not None:
        if not isinstance(selected_start, str) or not selected_start.endswith("Z"):
            raise ValueError("explicit metadata policy validity must be a UTC timestamp")
        datetime.fromisoformat(selected_start.replace("Z", "+00:00"))
    key_path = Path(selected["metadata_private_key_file"])
    if (not key_path.is_absolute() or key_path != key_path.resolve(strict=False)
            or not key_path.is_relative_to(external_root) or key_path.is_relative_to(directory)
            or any(value.is_symlink() for value in (key_path, *key_path.parents))):
        raise ValueError("select an actual owner-only operational key on EL outside the publication directory")
    if not key_path.exists() and not assembly_request.allow_metadata_key_creation:
        raise PermissionError('actual metadata key is absent; supply its provider file or explicitly select ordinary key creation')
    def publication(name, record, *, relative=None, logical=None, lineage_parents=()):
        from empirical_lawhood.api.matrix_source_input_assembly import publish_source_input_record
        if lineage_parents:
            _require_original_e3_access(writer=writer, original_e3=assembly_request.original_e3,
                original_products=assembly_request.original_products)
        result, observed = publish_source_input_record(writer=writer, prefix=prefix, namespace=namespace,
            name=name, record=record, relative=relative, logical=logical, lineage_parents=lineage_parents)
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
        limit=assembly_request.source_budget.source_scan_bytes
        if kind in (grants.DatasetOperationPolicy,grants.DatasetOperationAuthorization):
            limit=min(limit,assembly_request.dataset_work_envelope.control.max_receipt_bytes)
        raw = read_bounded_bytes(path, maximum_bytes=limit)
        value = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        if raw != value.canonical_bytes():
            raise PermissionError("retained control primary changes its exact canonical bytes")
        return _read_exact_record(writer, publication(name, value), kind)
    with writer.verification_scope() as writer, published_programme_e4_inputs(request=assembly_request, project_root=project, artifact_writer=writer,
        metadata_directory=directory / "e4-inputs", execution=execution) as committed:
        original = committed.original_preparation.root
        public = committed.original_e3
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
        phase = selected["phase"]
        if phase not in ("CALIBRATION", "CONFIRMATION"):
            raise ValueError("finite-dt source selects the actual protected E4 phase")
        # C already owns all three matched populations and their original streams.
        # The composition authenticates actual E3/TRAIN custody, allocating nothing.
        bank, programme = dict(committed.banks)[phase], dict(committed.programmes)[phase]
        training_request = committed.training_request
        locator = assembly_request.native_training_locator
        certificate = certify_native_training_instrument(writer=writer, locator=locator, programme=programme, bank=bank,
            original_future_reservation=training_request.future_manifest.reservation, cutoff=cutoff, record_id="certificate." + namespace)
        root = source_root_from_e3(original=original, programme=programme, bank=bank, certificate=certificate,
            cutoff=cutoff, computability=computability, budget=budget, namespace=namespace,
            scientific_pins=(bank.identity, programme.identity, certificate.identity,
                public.identity, assembly_request.input_commitments.record, training_request.identity,
                ObjectIdentity.from_record(computability.computability_id, computability), r.pin(cutoff, "cutoff_id")))
        publication("scientific-root." + root.fingerprint(), root)
        rows = rows_owner.MatrixFiniteDtPendingSourceRows.from_bank(programme, bank, record_id="rows." + namespace)
        rule = rows_owner.MatrixFiniteDtSourceValidationRule("rule." + namespace, programme.identity, bank.identity, rows.identity)
        from empirical_lawhood.api.matrix_source_input_assembly import materialize_source_input_rows,prepare_source_candidate
        materialized,evidence_profile=materialize_source_input_rows(writer=writer,project=project,prefix=prefix,
            namespace=namespace,selected=selected,key_path=key_path,selected_start=selected_start,seconds=seconds,reasons=reasons,
            implementation=implementation,publication=publication,retained=retained,rows=rows,rule=rule,bank=bank,
            programme=programme,cutoff=cutoff,envelope=envelope,root=root,rows_owner=rows_owner,r=r,certificate=certificate,
            assay_identity=bank.response_selection.identity,verification_kind=rows_owner.MatrixFiniteDtSourceVerification)
        scope = r.MatrixFiniteDtSourceScope("scope." + namespace, programme.identity, bank.identity, identity(bank.reservation),
            identity(training_request.future_manifest.reservation), bank.response_selection.identity,
            identity(bank.specification.selection.numerical_design), certificate.identity, cutoff, programme.group_ids,
            materialized.config.profile, materialized.config.assess(), evidence_profile,
            materialized.verification.identity, materialized.verification.identity, budget)
        metadata_publications = publish_finite_dt_source_metadata(writer=writer, scope=scope,
            materialization=materialized, output_directory=directory / "metadata")
        # One atomic write, followed by truthful current read observations. Stored
        # historical handles are never rewritten; this new selection is stable on retry.
        metadata_publications=tuple((reference,_publication_from_manifest(writer,
            writer.read_manifest(stored.materialization.relative_path))) for reference,stored in metadata_publications)
        operands = {"scope": scope, "programme": programme, "bank": bank, "reservation": bank.reservation,
            "original-reservation": training_request.future_manifest.reservation, "assay": bank.response_selection,
            "numerical": bank.specification.selection.numerical_design, "cutoff": cutoff, "certificate": certificate}
        produced_parents = original_e3_lineage(original_e3=assembly_request.original_e3)
        operand_lineage = {name: produced_parents if name in ("programme", "bank") else () for name in operands}
        prospective,configs,authoring,lowered,entry,terminals=prepare_source_candidate(writer=writer,project=project,
            namespace=namespace,publication=publication,domain=domain,bindings=bindings,scope=scope,operands=operands,
            materialized=materialized,root=root,budget=budget,operational=operational,implementation=implementation,programme=programme,
            operand_lineage=operand_lineage)
        required_support = {artifact for artifact, _ in current_exposure_support(bank.audit)}
        supports = tuple((artifact, custody) for artifact, custody in training_request.exposure_support if artifact in required_support)
        selected_source = domain.MatrixFiniteDtSourceQualificationSelection("selection." + namespace, scope, programme,
            bank, training_request.future_manifest.reservation, certificate, rows, rule, materialized.source_publication,
            materialized.output_publication, materialized.verification, materialized.verification_publication,
            materialized.config, prospective, tuple(sorted(configs, key=lambda value: value.fingerprint())),
            supports, metadata_publications, terminals)
        specification = domain.MatrixFiniteDtSourceQualificationSpecification("specification." + namespace,
            selected_source.identity, execution.workers)
        preparation = domain.prepare(specification, scientific_inputs={"source": domain.source_allocation(selected_source)},
            method_inputs=selected_source, execution=execution)
        if preparation.dependencies:
            raise ValueError("source preparation retains actual dependencies: " + str(preparation.dependencies))
        publication("specification", specification, lineage_parents=produced_parents)
        publication("selection", selected_source, lineage_parents=produced_parents)
        publication("authoring-base", replace(authoring, draft=lowered.prospective_draft, entry_package=entry), lineage_parents=produced_parents)
        source_selection = ExperimentFileInputSelection("sources." + namespace, domain.PROTOCOL_ID,
            (ExperimentInputBinding("selection", selected_source.identity, "selection.json", len(selected_source.canonical_bytes())),), ())
        publication("sources", source_selection, lineage_parents=produced_parents)
        yield specification,source_selection,directory/"specification.json",tuple(publications)


def assemble_finite_dt_source_inputs(*, assembly_specification, assembly_request, project_root,
        artifact_writer, metadata_directory, output_selection_path, execution):
    """Standalone assembly retains original input guards through its final return."""
    with assembled_finite_dt_source_inputs(assembly_specification=assembly_specification,
            assembly_request=assembly_request, project_root=project_root, artifact_writer=artifact_writer,
            metadata_directory=metadata_directory, output_selection_path=output_selection_path,
            execution=execution) as result:
        return result
