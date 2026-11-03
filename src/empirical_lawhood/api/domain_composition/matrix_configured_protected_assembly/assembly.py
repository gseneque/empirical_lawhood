# SPDX-License-Identifier: MPL-2.0
"""Genuine configured E3 preprocessing over actual native TRAIN producers.

Direct mathematical definitions carry no prior study or entry. The actual
current scientific root and formal candidate are built through ordinary owners;
proposer, issue, execution and reveal remain genuine separate acts.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
import calendar
from dataclasses import fields, replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path


def scientific_root(*, namespace, candidate, manifest, allocation, protocols, cutoff,
        policy, envelope, computability, operator_id, scientific_pins):
    """Declare this actual response-error experiment, with all results REQUIRED.

    Numerical selections and whole-unit denominators come only from the frozen
    candidate. Hardware ceilings and authority are explicit operator records.
    This declaration is not a qualification, freshness or human-attestation act.
    """
    from empirical_lawhood.adapters.composition.experiment_authoring import single_experiment_campaign
    from empirical_lawhood.kernel.authority import AuthorityAction
    from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, EvidenceRung, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.experiments import AssignmentKind, AssignmentSpec, ControlKind, ControlSpec, ExperimentSpec, PrecisionGoal, RevealBarrierSpec
    from empirical_lawhood.kernel.obligations import ClosureSpec, FalsifierKind, FalsifierSpec, ObligationStatus, ScientificObligations, StructuralConvergenceSpec, SupportSpec, UncertaintySpec, ValiditySpec
    from empirical_lawhood.kernel.quantities import QuantityKind, QuantitySpec, ResponseDirection
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.kernel.status import ReadinessStatus
    from empirical_lawhood.kernel.systems import IndependentUnitSpec, RelationalIdentity, SystemBoundaryKind, SystemSpec
    from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase, ClockLabelSemantics, ClockSpec, HoldSemantics, HorizonSpec, InformationCutoff, SamplingSemantics
    from empirical_lawhood.kernel.worlds import NumericalCoordinateKind, NumericalCoordinateSpec, NumericalViewSpec, RandomnessSemantics, WorldKind, WorldSpec
    from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, DesignOrigin, DesignOriginKind, StudyDraft, StudyDraftLifecycle

    measurement = candidate.measurement
    prefix = namespace + ".e3"
    coordinate = protocols[0].public_source.coordinate
    physical_clock = coordinate.clock_id
    physical_time = coordinate.physical_time(measurement.origin_tick)
    frame = "six-matrix-response.frame.simultaneous-unitary-quotient"
    time_unit = coordinate.primary_view.time_unit
    pre = AvailabilitySpec(physical_clock, CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, physical_time)
    # The frozen action is requested at the original origin. Applied action
    # evidence belongs to the later native acquisition, never this declaration.
    requested_action = AvailabilitySpec(physical_clock, CausalPhase.ACTION_REQUESTED,
        OutcomeAccess.OUTCOME_BLIND, physical_time)
    receiver = AvailabilitySpec(physical_clock, CausalPhase.RECEIVER, OutcomeAccess.EVALUATION_SEALED,
        physical_time + measurement.horizons[-1] * measurement.primary_timestep)
    clocks = {value.clock_id: ClockSpec(value.clock_id, "Native matrix source physical clock",
        value.primary_view.time_unit, frame, SamplingSemantics.REGULAR, HoldSemantics.NONE,
        ClockLabelSemantics.INSTANT, value.primary_view.timestep, Decimal(0))
        for value in manifest.reservation.allocation.coordinates}
    physical_cutoffs = tuple(sorted((InformationCutoff("cutoff." + value.public_source.root.root_id,
        value.public_source.coordinate.clock_id, CausalPhase.PRE_ACTION,
        value.public_source.coordinate.physical_time(value.public_source.policy.cutoff_tick))
        for value in protocols), key=lambda value: value.cutoff_id))
    clocks[cutoff.clock_id] = ClockSpec(cutoff.clock_id, "Actual host UTC source-publication observation", "UTC-second",
        "UTC-epoch", SamplingSemantics.EVENT_DRIVEN, HoldSemantics.NONE, ClockLabelSemantics.EVENT)
    quantities = (
        QuantitySpec(prefix+".quantity.denominator", "Complete original independently seeded six-matrix history",
            QuantityKind.DENOMINATOR, "physical-root", "physical-root", frame, physical_clock, pre),
        QuantitySpec(prefix+".quantity.history", "Causal prefix and fixed origin-only response features", QuantityKind.HISTORY,
            "six-matrix-history", "native-matrix-history", frame, physical_clock, pre),
        QuantitySpec(prefix+".quantity.action", "Frozen signed physical response action", QuantityKind.ACTION,
            "matrix-force", "native-matrix-force", frame, physical_clock, requested_action),
        QuantitySpec(prefix+".quantity.bath-boundary",
            "Original Langevin bath conditions: friction gamma="+str(coordinate.primary_view.friction_gamma)
            +", temperature="+str(coordinate.primary_view.bath_temperature),
            QuantityKind.BOUNDARY, "Langevin-bath-conditions", "native-Langevin-bath-conditions",
            frame, physical_clock, pre),
        QuantitySpec(prefix+".quantity.receiver", "Complete paired-view normalized response-error target family", QuantityKind.RECEIVER,
            "normalized-response-error", "dimensionless-response-error", frame, physical_clock, receiver,
            ResponseDirection.LOWER_IS_BETTER))
    quantities = tuple(sorted(quantities, key=lambda value:value.quantity_id))
    q = {value.quantity_id.rsplit(".",1)[-1]:value.quantity_id for value in quantities}
    relation = RelationalIdentity(prefix+".relation", (q["denominator"],), (q["history"],), False,
        (q["action"],), (q["receiver"],), HorizonSpec(prefix+".horizon", physical_clock,
            measurement.horizons[-1]*measurement.primary_timestep, time_unit))
    world = WorldSpec(prefix+".world", "Six-matrix paired numerical response-error experiment", WorldKind.NUMERICAL_SIMULATOR,
        ("BAOAB-under-damped-Langevin", "six-Hermitian-matrix-constitutive-dynamics"),
        ("physical-material-realization",), (), EvidenceCeiling.RESPONSE,
        frozenset((OutcomeAccess.OUTCOME_BLIND,OutcomeAccess.DEVELOPMENT_VISIBLE,
            OutcomeAccess.EVALUATION_SEALED,OutcomeAccess.EVALUATOR_REVEAL)))
    independent = IndependentUnitSpec(prefix+".unit", "One original stochastic physical history; signs, panels, targets and numerical views remain nested",
        "matrix-original-independent-group-id")
    views = tuple(sorted((NumericalViewSpec(view.view_id, world.world_id, independent.unit_id,
        "equations.six-matrix-response.six-matrix-baoab", ("closure.six-matrix-response.six-matrix-native",),
        ("boundary.six-matrix-response.complete-history",), (NumericalCoordinateSpec(prefix+".coordinate."+label,
            NumericalCoordinateKind.TIMESTEP, view.timestep, time_unit, index),),
        "solver.six-matrix-response.baoab", "1.0.0", view.precision.value, "cpu", prefix+".runtime",
        RandomnessSemantics.GENERATIVE_PREPARATION, prefix+".response-error-observation", envelope.envelope_id)
        for index,(label,view) in enumerate((("primary",coordinate.primary_view),("fine",coordinate.fine_view)))),
        key=lambda value:value.view_id))
    system = SystemSpec(prefix+".system", "Frozen native TRAIN and protected paired CAL/CONF response-error workflow",
        SystemBoundaryKind.OPEN_DRIVEN_DISSIPATIVE, world, relation, tuple(clocks[key] for key in sorted(clocks)), quantities,
        independent, policy, (), computability_envelopes=(envelope,), numerical_views=views)
    required = ObligationStatus.REQUIRED
    first_cutoff = physical_cutoffs[0].cutoff_id
    assessment_key = "matrix-e3-configured-protected.assess"
    uncertainty = UncertaintySpec(prefix+".uncertainty", prefix+".exact-whole-root-family-comparison", independent.unit_id,
        Decimal(1)-candidate.calibration_alpha,
        (q["receiver"],), ("NUMERICAL_SIMULATOR_ONLY","SAMPLING_QUALIFICATION_NOT_ESTABLISHED"), required)
    obligations = ScientificObligations(prefix+".single-terminal",
        SupportSpec(prefix+".support", relation.relation_id, independent.unit_id,
            candidate.population("EVALUATION").expected_units, len(views), first_cutoff,
            (prefix+".native-response-chart",), (prefix+".complete-evaluation-roster",), (), required),
        ValiditySpec(prefix+".validity", (prefix+".frozen-native-design",),
            ("causal-prefix-only-features","fixed-model-and-target-family","independent-original-physical-roots"),
            ("NATIVE_OR_NUMERICAL_NONUSE","NO_ADMITTED_ORIGIN","SAMPLING_QUALIFICATION_NOT_ESTABLISHED"), required),
        uncertainty,
        (FalsifierSpec(prefix+".falsifier", FalsifierKind.BASELINE_COMPARATOR, assessment_key,
            "Complete paired response-error comparisons with every frozen comparator on the whole evaluation denominator.",
            "The frozen exact family rule retains adverse and unevaluable units; no denominator trimming or view compensation.", required),),
        ClosureSpec(prefix+".closure", (prefix+".complete-action-horizon-predictor-panel-family",),
            (prefix+".frozen-causal-feature-comparators",), relation.history_quantity_ids, required),
        StructuralConvergenceSpec(prefix+".convergence", (prefix+".paired-native-view-checks",),
            tuple(view.view_id for view in views), (), required),
        computability)
    claim = ClaimSpec(prefix+".claim", world.world_id, relation.relation_id, candidate.question,
        "Frozen origin-only estimators predict complete paired native response-error targets under the selected whole-root exact comparison rule.",
        independent.unit_id, EvidenceRung.RESPONSE, EvidenceCeiling.RESPONSE,
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE,
        "Only actual retained numerical outcomes answer this fixed hypothesis; source byte access creates no sampling qualification or cross-world claim.",
        ("complete-original-physical-root-denominator","frozen-protocol-before-held-out-native-acquisition"),
        numerical_view_ids=tuple(view.view_id for view in views))
    query = tuple(sorted((*allocation.unit_ids("calibration"),*allocation.unit_ids("evaluation"))))
    experiment = ExperimentSpec(candidate.specification_id, system.system_id, world.world_id, relation, independent.unit_id,
        (claim,), AssignmentSpec(prefix+".assignment",AssignmentKind.SIMULATOR_INTERVENTION,independent.unit_id,
            relation.action_quantity_ids,"Use the preTRAIN reserved original roots and frozen paired signed-action protocol once.",
            (prefix+".complete-evaluation-roster",)), (q["receiver"],),
        (ControlSpec(prefix+".control", ControlKind.BASELINE_COMPARATOR, assessment_key, (q["receiver"],),
            "All frozen estimator, predictor, action, horizon and panel comparisons retain both native views and the complete original root roster."),),
        (PrecisionGoal(prefix+".precision", prefix+".paired-response-error-discrepancy", measurement.target_discrepancy_tolerance,
            "dimensionless-response-error",candidate.population("EVALUATION").expected_units,
            "Acquire the entire frozen roster once; retain failures and unevaluable outcomes without top-up."),),
        physical_cutoffs, RevealBarrierSpec(prefix+".reveal", allocation.unit_ids("train"), prefix+".evaluation-cohort",
            sha256(canonical_json_bytes(query)).hexdigest(),(prefix+".sealed-complete-evaluation",),
            OutcomeAccess.EVALUATION_SEALED,True), obligations,VisibilityCeiling.PROSPECTIVE,VisibilityCeiling.PROSPECTIVE,
        policy.policy_id,ReadinessStatus.AUTHORITY_REQUIRED)
    campaign = single_experiment_campaign(system,experiment,prefix=prefix,budget=policy.budget_ceiling,
        objective=candidate.question,actions=(("execute",AuthorityAction.SIMULATION_EXECUTION),
            ("freeze",AuthorityAction.NONACTUATING_PROSPECTIVE_FREEZE),("reveal",AuthorityAction.EVALUATOR_REVEAL)))
    design = tuple(sorted((DesignInputRecord(prefix+".design."+str(index),pin,pin.object_fingerprint,cutoff,
        DesignInputRole.READINESS_METADATA,OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE,operator_id)
        for index,pin in enumerate(sorted(set(scientific_pins),key=lambda value:value.object_id))),
        key=lambda value: value.input_id))
    return StudyDraft(prefix+".draft",StudyDraftLifecycle.DRAFT,candidate.question,(prefix+".frozen-selected-design",),
        DesignOrigin(prefix+".origin",DesignOriginKind.ORDINARY_THEORY_PREDECLARED,tuple(row.input_id for row in design),
            VisibilityCeiling.PROSPECTIVE),design,allocation.unit_ids("train"),query,(),(),(),system,experiment,campaign,
        prefix+".pending-template",(),(),policy.budget_ceiling)


def _committed_future_sources(manifest, future_phases):
    """Resolve the exact source pins in all authenticated future responses."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex

    if set(future_phases) != {"CALIBRATION", "EVALUATION", "TRANSFER_NEARBY", "TRANSFER_SHIFTED"}:
        raise ValueError("configured future sources lose their complete original phase census")
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    publics = tuple(protocol.public_source for phase in future_phases.values() for protocol in phase.protocols)
    if any(type(public) is not ScheduledPublicSource for public in publics):
        raise TypeError("configured future sources require exact committed public descriptors")
    if (len(publics) != len(index.root_ids)
            or {public.root.root_id for public in publics} != set(index.root_ids)):
        raise ValueError("configured future sources change the complete unique root census")
    sources = {}
    for public in publics:
        candidates = tuple(index.reference(source_id=public.source.object_id,
            root_id=public.root.root_id, provenance=provenance.identity) for provenance in manifest.provenances)
        matches = tuple(source for source in candidates if source.identity == public.source)
        if len(matches) != 1:
            raise ValueError("configured future source differs from its exact committed source pin")
        source, = matches
        public.validate_source(index.resolve(source))
        sources[source.root_id] = source
    return tuple(sources[root_id] for root_id in index.root_ids)


def assemble_configured_e3_inputs(*,assembly_specification,assembly_request,scientific_protocol,primary_amendment=None,request_path,project_root,artifact_writer,
        metadata_directory,output_selection_path,execution,export_adoption=None,continued_context=None):
    from empirical_lawhood.adapters.composition.experiment_authoring import formal_entry
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_inputs as inputs_owner
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as preparation_owner
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import lower_protected_matrix_response_error
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import ConfiguredProtectedE3OriginalPublications
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_protocol import project_protected_e3_protocol, validate_protected_e3_response_selection
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import project_protected_e3_response_numerics
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_selection import ConfiguredProtectedE3ResponseSelection
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import ConfiguredProtectedE3FitConfig, statistical_task_id
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import ConfiguredE3CoordinateCensus
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest, identity
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_input_custody import read_protected_e3_original_publication
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity, identity as scheduled_identity
    from empirical_lawhood.api.derived_array_access import derive_matrix_array_access
    from empirical_lawhood.api.derived_metadata_access import derive_canonical_metadata_access
    from empirical_lawhood.api.native_training_banks import export_native_training_banks
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_future_response_selections
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import EvidenceCeiling,OutcomeAccess,VisibilityCeiling
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.time import AvailabilitySpec,CausalPhase,InformationCutoff
    from empirical_lawhood.planning.approval import SystemDecisionClock
    from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding,ExperimentFileInputSelection,ExperimentInputBinding
    from empirical_lawhood.planning.formal_gaps import FormalGapEvidenceWorld
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
    from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest,ArtifactWriteResult
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import (
        ConfiguredProtectedE3AssemblyRequest, validate_scientific_protocol)
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.experiment_preparation import _input_member
    if type(assembly_request) is not ConfiguredProtectedE3AssemblyRequest:
        raise TypeError('configured E3 preprocessing requires its exact current scientific request')
    validate_scientific_protocol(assembly_request, scientific_protocol)
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_primary_amendment import MatrixE3PrimaryFamilyAmendment
    if assembly_request.primary_amendment is not None:
        if type(primary_amendment) is not MatrixE3PrimaryFamilyAmendment or primary_amendment.identity != assembly_request.primary_amendment:
            raise ValueError("configured scientific assembly requires its exact declared primary amendment")
        primary_amendment.__post_init__()
    elif primary_amendment is not None:
        raise ValueError("a primary amendment requires its explicit current assembler request pin")
    if assembly_specification.request!=assembly_request.identity:
        raise ValueError('configured E3 preprocessing changes its original input request')
    project=Path(project_root).resolve(strict=True);writer=artifact_writer
    destination=Path(metadata_directory);plane=Path(writer.root.contract.canonical_path)
    if (not destination.is_absolute() or destination!=destination.resolve(strict=False)
            or Path(output_selection_path)!=destination/'inputs/sources.json'):
        raise ValueError('configured E3 preprocessing needs exact guarded metadata and <metadata>/inputs/sources.json target')
    prefix=destination.relative_to(plane).as_posix();writer.root.resolve(prefix+'/inputs/sources.json',for_write=True)
    if execution.output_root!=str(plane) or any(value is None for value in (execution.workers,execution.environment_id,execution.source_snapshot)):
        raise ValueError('configured E3 preprocessing needs explicit current source/environment/workers/root')
    implementation=implementation_binding(project)
    if ObjectIdentity.from_record('recursive-member.implementation',implementation)!=execution.source_snapshot:
        raise ValueError('configured E3 preprocessing changes its actual selected executing source')
    namespace=assembly_request.namespace
    inputs=writer.root.resolve(assembly_request.pretrain_inputs_relative_directory,for_write=False)
    selected={'namespace':namespace,'operator_id':assembly_request.operator_id,'bank_export_record_id':assembly_request.bank_export_record_id,
        'bank_export_relative_path':assembly_request.bank_export_relative_path,
        'native_training_directory':str(writer.root.resolve(assembly_request.native_training_locator.authored_directory,for_write=False)),
        'normalization_source_file':str(_input_member(Path(request_path).parent,assembly_request.normalization_file.relative_path))}
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    publications=[]
    def commit(request):
        from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
        writer.write(request)
        result=_publication_from_manifest(writer,writer.read_manifest(request.relative_path))
        publications.append(result)
        return result
    def load(path,kind):
        target=Path(path)
        if any(value.is_symlink() for value in (target,*target.parents)):
            raise ValueError('configured E3 preprocessing refuses linked source operands')
        target=writer.root.resolve(target.relative_to(plane).as_posix(),for_write=False)
        raw=read_bounded_bytes(target,maximum_bytes=target.stat().st_size)
        record=decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))
        if record.canonical_bytes()!=raw:raise ValueError('configured E3 preprocessing changes exact selected canonical bytes')
        return record
    def write_exact(path,raw):
        relative=path.relative_to(plane).as_posix()
        if path.suffix=='.npz':
            schema,profile,media=MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'
        else:
            document=json.loads(raw);schema,profile,media=document['schema'],ArtifactProfile.CANONICAL_JSON,'application/json'
        training=schema in (native.NativeTrainingFeatureBank.SCHEMA,native.NativeTrainingOutcomeBank.SCHEMA)
        access=OutcomeAccess.DEVELOPMENT_VISIBLE if training else OutcomeAccess.OUTCOME_BLIND
        ceiling=VisibilityCeiling.DEVELOPMENT_ONLY if training else VisibilityCeiling.PROSPECTIVE
        commit(ArtifactWriteRequest(namespace+'.copied.'+sha256(relative.encode()).hexdigest(),relative,schema,profile,media,
            namespace,prefix,raw,ceiling,(),access))
    candidate=load(inputs/"candidate.json",ConfiguredProtectedE3Specification)
    access_scope={'observation_operator':ObjectIdentity.from_record(candidate.specification_id+'.measurement',candidate.measurement)}
    manifest=load(inputs/"future-manifest.json",ProtectedE3NativeSourceManifest)
    manifest_publication=load(inputs/"future-manifest-publication.json",ArtifactWriteResult)
    authenticate_publication(writer,manifest_publication,manifest)
    future_availability=load(inputs/"future-availability.json",AvailabilitySpec)
    future_availability_publication=load(inputs/"future-availability-publication.json",ArtifactWriteResult)
    authenticate_publication(writer,future_availability_publication,future_availability)
    if (future_availability.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or future_availability.phase is not CausalPhase.PREPARATION
            or future_availability.available_at is None
            or future_availability.clock_id!=SystemDecisionClock().clock_id
            or future_availability_publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or future_availability_publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise ValueError("PreTRAIN availability changes its actual blind preparation scope")
    training_specification=load(inputs/"native-training-specification.json",native.NativeTrainingAcquisitionSpecification)
    training_request=load(inputs/"request.json",native.NativeTrainingAcquisitionRequest)
    # The exporter replays complete request science/custody before publishing;
    # bind its exact admitted request here without repeating that whole census.
    if (training_request.candidate_specification!=candidate or training_request.future_manifest!=manifest
            or training_specification.candidate!=candidate.identity
            or training_specification.future_reservation!=scheduled_identity(manifest.reservation)):
        raise ValueError("Native TRAIN changes the exact candidate or future reservation frozen before acquisition")
    if primary_amendment is not None:
        primary_amendment.validate_native(training_specification,training_request)
        candidate=primary_amendment.candidate
    # The owning API authenticates all five committed publications and their
    # complete role, source and stream joins. The genuine path cannot use the
    # historical no-panel-commitment interpretation.
    future_phases=dict(authenticate_future_response_selections(writer,training_request))
    required_roles={"CALIBRATION","EVALUATION","TRANSFER_NEARBY","TRANSFER_SHIFTED"}
    if set(future_phases)!=required_roles:
        raise ValueError("Genuine E3 requires all four original preTRAIN response commitments")
    training_publication=load(inputs/'train-unit-allocation-publication.json',ArtifactWriteResult)
    expected_training=native.training_allocation(training_specification,training_request)
    if training_publication.materialization.relative_path!=(inputs.parent/'publications/train-unit-allocation.json').relative_to(plane).as_posix():
        raise ValueError('PreTRAIN unit allocation substitutes its actual original metadata publication')
    if training_publication.materialization.size_bytes!=len(expected_training.canonical_bytes()):
        raise ValueError('PreTRAIN unit allocation changes its exact declared byte census')
    declared_training=read_protected_e3_original_publication(writer,training_publication,UnitAllocation)
    if declared_training!=expected_training:
        raise ValueError('PreTRAIN unit allocation differs from the original acquisition declaration')
    availability_pin=ObjectIdentity.from_record(future_availability_publication.logical.logical_artifact_id,future_availability)
    if availability_pin not in training_request.campaign.evidence_state:
        raise ValueError("PreTRAIN availability differs from the actual acquisition commitment")
    supports=training_request.exposure_support
    availability_supports=tuple(publication for artifact,publication in supports
        if (artifact.artifact_id,artifact.payload_schema,artifact.sha256)==
           (availability_pin.object_id,availability_pin.object_schema,availability_pin.object_fingerprint))
    if availability_supports!=(future_availability_publication,):
        raise ValueError("Copied preTRAIN availability changes its actual committed publication")
    for role,phase in future_phases.items():
        raw=phase.canonical_bytes()
        if read_bounded_bytes(inputs/("future-responses-"+role.lower()+".json"),maximum_bytes=len(raw))!=raw:
            raise ValueError("Copied CAL/CONF/E6 selection differs from its original authenticated commitment")
        publication=load(inputs/("future-responses-"+role.lower()+"-publication.json"),ArtifactWriteResult)
        committed=tuple(value for artifact,value in supports
            if (artifact.payload_schema,artifact.sha256,artifact.size_bytes)==(phase.SCHEMA,phase.fingerprint(),len(raw)))
        if committed!=(publication,):
            raise ValueError("Copied CAL/CONF/E6 publication differs from the actual acquisition commitment")
    retained_source = None
    if continued_context is not None:
        from empirical_lawhood.api.matrix_programme_retained_training_continuation import continued_e3_future
        if continued_context.execution != execution:
            raise PermissionError('continued E3 changes its actual admitted source/environment selection')
        manifest, future_phases, retained_source = continued_e3_future(continued_context,
            assembly_request=assembly_request, training_request=training_request,
            scientific_protocol=scientific_protocol, candidate=candidate, export_adoption=export_adoption)
    phase_responses=tuple(future_phases[role] for role in ("CALIBRATION","EVALUATION"))
    resources=assembly_request.resources
    if resources.resources.maximum_parallel_tasks!=execution.workers:
        raise ValueError("Actual E3 resource/profile worker ceilings differ")
    policy=assembly_request.authority_policy
    envelope=assembly_request.computability_envelope
    computability=assembly_request.computability_evidence
    coordinate_map={coordinate_identity(value):value for value in manifest.reservation.allocation.coordinates}
    roles=dict(candidate.role_coordinates)
    nominal=coordinate_map[roles["CALIBRATION"]]
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import require_computability_scope
    require_computability_scope(envelope, computability, nominal)
    observation=capture_matrix_provenance(project_root=project)
    expected_source=(implementation.package_sources,implementation.code_sources_sha256,
        implementation.dependency_lock_sha256,implementation.observed_git_head)
    current = (observation, *manifest.provenances)
    if retained_source is None:
        current += training_request.train_manifest.provenances
    else:
        original = retained_source.export_adoption.producer_implementation
        historical_source = (original.package_sources, original.code_sources_sha256,
            original.dependency_lock_sha256, original.observed_git_head)
        for observed in (*training_request.train_manifest.provenances, *training_request.future_manifest.provenances):
            if (observed.package_sources, observed.code_sources_sha256,
                    observed.dependency_lock_sha256, observed.observed_git_head) != historical_source:
                raise PermissionError('continued E3 changes its exact original TRAIN producer provenance')
    for observed in current:
        if (observed.package_sources,observed.code_sources_sha256,
                observed.dependency_lock_sha256,observed.observed_git_head)!=expected_source:
            raise ValueError("Current worker source differs from the selected snapshot or preTRAIN frozen future provenance")
    mathematical=scientific_protocol.mathematical_protocol
    if mathematical != training_request.mathematical_protocol:
        raise ValueError("Configured mathematical protocol differs from the actual preTRAIN commitment")
    declared_coordinates = {coordinate_identity(value): value for value in scientific_protocol.coordinates}
    declared_policies = {scheduled_identity(value): value for value in scientific_protocol.prefix_policies}
    declared_mapping = dict(scientific_protocol.coordinate_policies)
    observed_coordinates = {}
    for committed_manifest in (manifest, training_request.train_manifest):
        selected_native = committed_manifest.native_specification.selection
        if (committed_manifest.scalar_definition != scientific_protocol.scalar_definition
                or selected_native.numerical_design != scientific_protocol.numerical_design):
            raise ValueError("Configured scalar or numerical design differs from actual committed TRAIN/source science")
        for coordinate in committed_manifest.reservation.allocation.coordinates:
            pin = coordinate_identity(coordinate)
            if declared_coordinates.get(pin) != coordinate:
                raise ValueError("Configured coordinate differs from its actual preTRAIN source commitment")
            observed_coordinates[pin] = coordinate
        if (any(declared_mapping.get(pin) != policy for pin, policy in selected_native.coordinate_policies)
                or any(declared_policies.get(scheduled_identity(policy)) != policy for policy in selected_native.prefix_policies)):
            raise ValueError("Configured prefix policy differs from the actual preTRAIN source commitment")
    if observed_coordinates != declared_coordinates:
        raise ValueError("Configured scientific protocol adds coordinates outside actual TRAIN and future source commitments")
    rules=tuple(value.target for value in mathematical.factor_rule_compatibilities if value.target.identity==mathematical.factor_rule)
    if not rules or any(value.canonical_bytes()!=rules[0].canonical_bytes() for value in rules):
        raise ValueError("Selected mathematical protocol lacks its exact original full factor rule")
    full_rule=rules[0]
    if full_rule.scalar_closure is None:
        raise ValueError("Selected full factor rule lacks its actual scalar normalization owner")
    normalization=full_rule.scalar_closure.normalization_owner
    normalization_raw=read_bounded_bytes(Path(selected["normalization_source_file"]),maximum_bytes=normalization.size_bytes)
    projections=tuple(sorted((project_protected_e3_protocol(specification=candidate,
        nominal=coordinate_map[roles["CALIBRATION"]],nearby=coordinate_map[roles["TRANSFER_NEARBY"]],shifted=coordinate_map[roles["TRANSFER_SHIFTED"]],
        mathematical_protocol=mathematical,original_factor_rule=full_rule,prefix_policy=value,
        scalar_definition=manifest.scalar_definition,normalization_source=normalization,normalization_source_bytes=normalization_raw,
        record_id="projection."+namespace+"."+str(index))
        for index,value in enumerate(manifest.native_specification.selection.prefix_policies)),key=lambda value:value.record_id))
    protocols=tuple(sorted((value for phase in phase_responses for value in phase.protocols),
        key=lambda value:value.public_source.root.root_id))
    panels=tuple(sorted((value for phase in phase_responses for _,rows in phase.panels for value in rows),key=lambda value:value.panel_id))
    sources = _committed_future_sources(manifest, future_phases)
    templates=tuple(sorted({value.logical.logical_artifact_id:value for phase in phase_responses
        for value in phase.template_publications}.values(),key=lambda value:value.logical.logical_artifact_id))
    responses=ConfiguredProtectedE3ResponseSelection("responses."+namespace,candidate.identity,identity(manifest),
        tuple((value.public_source.root.root_id,ObjectIdentity.from_record(value.protocol_id,value)) for value in protocols),
        tuple(sorted((group,tuple(ObjectIdentity.from_record(value.panel_id,value) for value in rows)) for phase in phase_responses for group,rows in phase.panels)),
        templates,tuple(identity(value) for value in projections))
    validate_protected_e3_response_selection(responses,specification=candidate,manifest=manifest,
        projections=projections,mathematical_protocol=mathematical,sources=sources,protocols=protocols,panels=panels)
    _,_,_,native_payloads=load_authored_wave(directory=Path(selected["native_training_directory"]),
        artifact_writer=writer,lazy_payloads=True)
    instance_raw=native_payloads["experiment-instance.json"]
    native_instance=decode_canonical_bytes(instance_raw,ExperimentInstanceBinding,maximum_bytes=len(instance_raw))
    native_requests=tuple(value for value in native_instance.sources if (value.object_schema,value.object_version)==
        (native.NativeTrainingAcquisitionRequest.SCHEMA,native.NativeTrainingAcquisitionRequest.VERSION))
    if (native_requests!=(training_request.identity,) or native_instance.specification!=training_specification.identity
            or native_instance.allocation!=declared_training.identity):
        raise ValueError("Selected completed TRAIN run differs from the exact preTRAIN acquisition request")
    export_options=dict(directory=Path(selected["native_training_directory"]),artifact_writer=writer,
        output_directory=writer.root.resolve(selected["bank_export_relative_path"],for_write=True),
        record_id=selected["bank_export_record_id"],expected_locator=assembly_request.native_training_locator)
    if export_adoption is not None:
        from empirical_lawhood.api.native_training_export_resume import adopt_native_training_bank_export
        export=adopt_native_training_bank_export(selection=export_adoption,project_root=project,**export_options)
    else:
        export=export_native_training_banks(**export_options)
    if export.allocation!=declared_training:
        raise ValueError('Actual TRAIN export differs from the original preTRAIN unit allocation')
    retained_publications=[]
    for name,publication in zip(("allocation","features","outcomes"),export.publications,strict=True):
        path=destination/"inputs"/("bank-export-"+name+"-publication.json")
        if path.exists():
            retained=load(path,ArtifactWriteResult)
            if (retained.logical,retained.materialization,retained.manifest_materialization)!=(
                    publication.logical,publication.materialization,publication.manifest_materialization):
                raise ValueError("Actual exported native bank publication differs on retry")
            authenticate_publication(writer,retained)
        else:
            retained=publication;write_exact(path,retained.canonical_bytes())
        retained_publications.append(retained)
    export=replace(export,publications=tuple(retained_publications))
    if any(row.source_manifest!=training_request.identity for bank in (export.features,export.outcomes) for row in bank.rows):
        raise ValueError("Actual native TRAIN bank rows substitute their authenticated preTRAIN request")
    training=export.allocation
    train_coordinates=ConfiguredE3CoordinateCensus("coordinates."+namespace+".native-train",
        tuple((row.unit_id,row.native_source,roles["TRAIN"]) for row in export.features.rows))
    source_inputs=inputs_owner.ConfiguredProtectedE3SourceInputs(candidate,training,manifest.reservation,
        manifest.native_specification,coordinate_map[roles["CALIBRATION"]],coordinate_map[roles["TRANSFER_NEARBY"]],
        coordinate_map[roles["TRANSFER_SHIFTED"]],train_coordinates)
    allocation=inputs_owner.project_protected_e3_allocation(source_inputs)
    # Metadata publications are actual owner outputs, including exact retry.
    def publish(name,record,*,access=OutcomeAccess.OUTCOME_BLIND,ceiling=VisibilityCeiling.PROSPECTIVE,logical=None):
        request=ArtifactWriteRequest(logical or namespace+"."+name,prefix+"/publications/"+name+".json",record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,"application/json",namespace,prefix,record.canonical_bytes(),ceiling,(),access)
        return commit(request)
    if retained_source is not None:
        manifest_publication = publish('continued-future-manifest', manifest)
    role_publication=publish("roles",allocation)
    # This observes now, after roles publication, and never backdates to TRAIN.
    availability_path=writer.root.resolve(prefix+"/publications/actual-fit-availability.json",for_write=False)
    if availability_path.exists():current_availability=load(availability_path,AvailabilitySpec)
    else:
        clock=SystemDecisionClock();utc=clock.now_utc()
        epoch=calendar.timegm(datetime.fromisoformat(utc.replace("Z","+00:00")).utctimetuple())
        current_availability=AvailabilitySpec(clock.clock_id,CausalPhase.PREPARATION,OutcomeAccess.OUTCOME_BLIND,Decimal(epoch))
    publish("actual-fit-availability",current_availability)
    cutoff=InformationCutoff("cutoff."+namespace+".actual-before-fit",current_availability.clock_id,
        CausalPhase.PREPARATION,current_availability.available_at)
    cutoff.require_allows(future_availability)
    response_publication=publish("responses",responses)
    expected_support=current_exposure_support(manifest.audit)
    support=tuple(load(inputs/("support-publication-"+artifact.sha256+".json"),ArtifactWriteResult)
        for artifact,_ in expected_support)
    for (artifact,expected),publication in zip(expected_support,support,strict=True):
        committed=tuple(value for selected_artifact,value in training_request.exposure_support if selected_artifact==artifact)
        if committed!=(publication,) or publication!=expected:
            raise ValueError('Copied exposure support changes its exact original TRAIN census commitment')
        authenticate_publication(writer,publication,manifest.audit.census)
    originals=ConfiguredProtectedE3OriginalPublications("originals."+namespace,candidate.identity,identity(manifest),training.identity,
        manifest_publication,training_publication,support[0])
    fit_publications=(("allocation",manifest.reservation.publication,future_availability),
        ("native-selection",manifest.native_specification.publication,future_availability),
        ("reservation",manifest.reservation_publication,future_availability),("roles",role_publication,current_availability))
    fit=ConfiguredProtectedE3FitConfig("config."+statistical_task_id(candidate.identity,allocation.identity,"fit"),candidate.identity,
        allocation.identity,tuple((role,len(allocation.unit_ids(role))) for role in ("calibration","evaluation")),identity(manifest),
        training.identity,cutoff,fit_publications,train_coordinates,originals)
    root=scientific_root(namespace=namespace,candidate=candidate,manifest=manifest,allocation=allocation,protocols=protocols,
        cutoff=cutoff,policy=policy,envelope=envelope,computability=computability,operator_id=selected["operator_id"],
        scientific_pins=(candidate.identity,allocation.identity,identity(manifest),identity(responses),
            ObjectIdentity.from_record(computability.computability_id,computability),*(identity(value) for value in projections),
            *((retained_source.identity,) if retained_source is not None else ())))
    response_external=RecursiveExternalInput("source."+namespace+".responses",response_publication.logical.logical_artifact_id,
        responses.SCHEMA,"application/json",len(responses.canonical_bytes()),OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE,responses.fingerprint(),"MODEL")
    _,response_qualification=derive_canonical_metadata_access(writer=writer,publication=response_publication,record=responses,
        external=response_external,root=root,**access_scope)
    numerical_profiles=tuple(project_protected_e3_response_numerics(value,provenance=responses,publication=response_publication,
        qualification=response_qualification) for value in protocols)
    artifacts=tuple(ArtifactIdentity(value.logical.logical_artifact_id,"actual-native-train-bank",record.SCHEMA,
        record.fingerprint(),"application/json",len(record.canonical_bytes()))
        for record,value in zip((export.features,export.outcomes),export.publications[1:],strict=True))
    selection=preparation_owner.ConfiguredProtectedE3LoweringInputs("selection."+namespace,root,fit,
        manifest,training,sources,projections,mathematical,responses,protocols,panels,numerical_profiles,*artifacts,
        resources,numerical_qualifications=(response_qualification,))
    if primary_amendment is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_primary_amendment import MatrixE3PrimaryFamilyAmendmentBinding,primary_amendment_root
        from empirical_lawhood.api.configured_e3_primary_amendment import authenticate_primary_amendment
        from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
        if export.acquisition is None or export.acquisition_publication is None or export.acquisition_receipt is None:
            raise ValueError("primary amendment requires the actual authenticated original native acquisition seal")
        specification_relative=(inputs/"native-training-specification.json").relative_to(plane).as_posix()
        specification_publication=_publication_from_manifest(writer,writer.read_manifest(specification_relative))
        binding=MatrixE3PrimaryFamilyAmendmentBinding("primary-amendment."+namespace,primary_amendment,
            specification_publication,assembly_request.native_training_locator,export.acquisition_receipt,
            export.acquisition.identity,export.acquisition_publication,export.publications[1:])
        selection=replace(selection,root=primary_amendment_root(selection,binding),primary_amendment=binding)
        root=selection.root
        authenticate_primary_amendment(writer=writer,selection=selection)
    lowered=lower_protected_matrix_response_error(candidate,allocation,selection)
    if not all(policy.budget_ceiling.contains(value) for value in
            (lowered.draft.campaign.budget, lowered.draft.prospective_draft.resource_ceiling)):
        raise ValueError("Supplied Matrix policy must explicitly contain both the complete selected E3 resource aggregate and the candidate execution ceiling")
    record_inputs=dict(lowered.input_records)
    bank_records={value.logical.logical_artifact_id:(record,value) for record,value in zip(
        (export.features,export.outcomes),export.publications[1:],strict=True)}
    templates_by_id={value.logical.logical_artifact_id:value for value in templates}
    from empirical_lawhood.api.derived_array_access import DerivedInputAccess, derive_matrix_input_access_batch, supports_derived_input_access_batch
    from empirical_lawhood.infrastructure.publication_metadata import (
        checkpoint_publication_access,
    )
    versions={};configs=[];qualifications=[];copied=[]
    batch_access=supports_derived_input_access_batch(writer,len(lowered.draft.external_inputs))
    pending=[]
    if batch_access:
        checkpoint_publication_access(writer)
    for external in lowered.draft.external_inputs:
        if external.input_id in record_inputs:
            record=record_inputs[external.input_id]
            publication=publish("input."+sha256(external.input_id.encode()).hexdigest(),record,
                access=external.outcome_access,ceiling=external.visibility_ceiling,logical=external.logical_artifact_id)
            if batch_access:
                pending.append(DerivedInputAccess(publication,record,external))
            else:
                config,q=derive_canonical_metadata_access(writer=writer,publication=publication,record=record,
                    external=external,root=lowered.draft.prospective_draft,**access_scope)
            versions[external.logical_artifact_id]=record.VERSION
        elif external.logical_artifact_id in bank_records:
            record,publication=bank_records[external.logical_artifact_id]
            if batch_access:
                pending.append(DerivedInputAccess(publication,record,external))
            else:
                config,q=derive_canonical_metadata_access(writer=writer,publication=publication,record=record,
                    external=external,root=lowered.draft.prospective_draft,**access_scope)
            versions[external.logical_artifact_id]=record.VERSION;copied.append((record.VERSION,publication))
        else:
            publication=templates_by_id[external.logical_artifact_id]
            operand=next(value.templates for value in protocols if value.templates.array_artifact.artifact_id==external.logical_artifact_id)
            if batch_access:
                pending.append(DerivedInputAccess(publication,operand,external))
            else:
                config,q=derive_matrix_array_access(writer=writer,publication=publication,arrays=operand,external=external,
                    root=lowered.draft.prospective_draft,**access_scope)
            versions[external.logical_artifact_id]="1.0.0";copied.append(("1.0.0",publication))
        if not batch_access:
            configs.append(config);qualifications.append(q)
    if pending:
        for config,q in derive_matrix_input_access_batch(writer=writer,inputs=tuple(pending),
                root=lowered.draft.prospective_draft,**access_scope):
            configs.append(config);qualifications.append(q)
    selection=replace(selection,qualifications=tuple(sorted(qualifications,key=lambda value:value.receipt_id)),
        source_configs=tuple(configs))
    draft=preparation_owner._source_projection(lowered.draft,selection,versions)
    registrations,registry,codecs=operation_catalog()
    compiled=compile_recursive_wave(draft=draft,registrations=registrations,registry=registry,
        implementation_commit=implementation.observed_git_head,qualifications=selection.qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,output_codecs=codecs,
        implementation_sha256=implementation.fingerprint())
    if compiled.candidate_context is None or compiled.candidate_draft is None or compiled.candidate_report.candidate is None:
        raise ValueError("Actual configured E3 candidate graph is not valid: "+str(compiled.candidate_report))
    evaluator=registry.resolve("matrix-e3-configured-protected.assess","1.0.0")
    authoring,standard=formal_entry(compiled.candidate_draft,compiled.candidate_context,candidate.identity,prefix=namespace+".e3",
        minimum_units=candidate.population("EVALUATION").expected_units,
        operand_description="Selected paired native response-error {domain} on the complete independently seeded physical-root roster",
        estimator="whole-root-exact-comparison",uncertainty="family-exact-uncertainty",ceiling=EvidenceCeiling.RESPONSE,
        evaluator=evaluator,input_schema=candidate.SCHEMA,
        output_schema="empirical-lawhood/matrix-response-experiment/configured-protected-assessment",
        world=FormalGapEvidenceWorld.NUMERICAL_SIMULATOR,minimum_views=len(root.system.numerical_views),
        evidence_unit_ids=allocation.unit_ids("evaluation"))
    values={field.name:getattr(selection,field.name)
        for field in fields(preparation_owner.ConfiguredProtectedE3PreparationSelection)
        if field.name not in {"entry_package","formal_methods","formal_source_inventories","secondary_readout","primary_amendment"}}
    values.update(root=authoring.draft,entry_package=authoring.entry_package,
        formal_methods=standard.formal_methods,formal_source_inventories=standard.source_inventories)
    selection=preparation_owner.ConfiguredProtectedE3PreparationSelection(**values,primary_amendment=selection.primary_amendment)
    final=lower_protected_matrix_response_error(candidate,allocation,selection)
    final_draft=preparation_owner._source_projection(final.draft,selection,versions)
    entry=replace(selection.entry_package,checklist=replace(selection.entry_package.checklist,
        draft=ObjectIdentity.from_record(final_draft.prospective_draft.draft_id,final_draft.prospective_draft)))
    validate_experiment_entry(final_draft.prospective_draft,entry,for_issue=False)
    selection=replace(selection,entry_package=entry)
    members=destination/"inputs"
    write_exact(members/"candidate.json",candidate.canonical_bytes())
    write_exact(members/"protected-selection.json",selection.canonical_bytes())
    bindings=[]
    for version,publication in {pub.logical.logical_artifact_id:(version,pub) for version,pub in copied}.values():
        logical,material=publication.logical,publication.materialization
        raw=read_bounded_bytes(writer.root.resolve(material.relative_path,for_write=False),maximum_bytes=material.size_bytes)
        filename=logical.content_sha256+(".npz" if logical.media_type=="application/x-npz" else ".json")
        write_exact(members/filename,raw)
        identity_value=next(value for _,value in final.file_identities if value.artifact_id==logical.logical_artifact_id)
        bindings.append(ExperimentFileInputBinding(identity_value.artifact_id,identity_value,version,filename,material.size_bytes))
    files=ExperimentFileInputSelection("files."+namespace,"matrix.response-error.configured-protected-v2",
        (ExperimentInputBinding("protected-selection",ObjectIdentity.from_record(selection.selection_id,selection),
            "protected-selection.json",len(selection.canonical_bytes())),),tuple(sorted(bindings,key=lambda value:value.key)))
    write_exact(members/"sources.json",files.canonical_bytes())
    # These are reviewable scientific inputs, not a fabricated human act.
    write_exact(members/"authoring-base.json",replace(authoring,draft=final_draft.prospective_draft,entry_package=entry).canonical_bytes())
    return candidate,files,members/"candidate.json",tuple(publications)
