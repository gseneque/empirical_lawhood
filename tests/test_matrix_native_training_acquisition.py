# SPDX-License-Identifier: MPL-2.0
"""Disclosed native TRAIN metadata/graph controls; no native entry or fitting."""
from dataclasses import fields, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_bindings import operation_declarations
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit, corpus_artifact, exposure_support
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave


def _whole_training_commitment(*, plane, train, future, candidate, mathematical, protocols, panels, template_publications):
    """Actual whole-C custody around the unchanged exposed TRAIN/future inputs.

    Synthetic producing provenance remains explicitly synthetic in refusal
    controls; the actual lifecycle supplies its observed provenance through its
    original seam. Every publication here is real. No C reader or source policy
    is mocked, and these newly disclosed metadata roles acquire no native data.
    """
    from datetime import datetime
    from decimal import Decimal
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import build_e6_transport_policy
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import (
        ResolvedMatrixProgrammeInputs, ResolvedMatrixProgrammePhaseInputs, validate_programme_input_records,
    )
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
        PHASE_INPUT_ROLES, MatrixProgrammeInputCommitments, MatrixProgrammePhaseInputs, MatrixProgrammePublishedInput,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay, ScheduledResponsePanel
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion, ScheduledResponseSelection
    from empirical_lawhood.api.matrix_programme_allocations import _source_plan
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs
    from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase
    from empirical_lawhood.planning.approval import SystemDecisionClock
    from tests.test_matrix_factor_confirmation_eligibility import publish
    from tests.test_matrix_programme_allocations import MATERIALS
    from tests.test_matrix_programme_scientific_design import build_scientific_design
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE

    namespace = "native-training.disclosed-whole"
    base = build_scientific_design()
    native = future.native_specification.selection
    scientific = NativeTrainingScientificProtocol("protocol.native-training.control.exact", mathematical,
        train.scalar_definition, future.reservation.allocation.coordinates, native.numerical_design,
        native.prefix_policies, native.coordinate_policies)
    prototype = protocols[0]
    values = {field.name: getattr(prototype, field.name) for field in fields(ScheduledResponseAssay)
        if field.name not in ("assay_id", "array_artifact", "members")}
    assay = ScheduledResponseAssay("assay.native-training.control.exact", **values,
        array_artifact=prototype.templates.array_artifact, members=prototype.templates.members)
    nominal_pin = dict(candidate.role_coordinates)["TRAIN"]
    nominal = next(value for value in scientific.coordinates if coordinate_identity(value) == nominal_pin)
    target = replace(base.e4_factorial.target, criterion=mathematical.identity, horizon_ticks=mathematical.horizon_steps)
    assessment = candidate.assessment
    family = assessment.comparison_ids
    familywise = assessment.alpha * len(family)
    probabilities = dict(null_success_numerator=assessment.null_probability.numerator,
        null_success_denominator=assessment.null_probability.denominator,
        alpha_numerator=assessment.alpha.numerator, alpha_denominator=assessment.alpha.denominator,
        family_slots=family, familywise_alpha_numerator=familywise.numerator,
        familywise_alpha_denominator=familywise.denominator)
    e5_criterion = replace(base.e5_development.criterion, **probabilities)
    e6_criterion = replace(base.e6.criterion, **probabilities)
    design = replace(base, record_id="design.native-training.control.exact", training_protocol=scientific,
        training_assay=assay, e3=candidate,
        e2=replace(base.e2, assay=replace(base.e2.assay, array_artifact=assay.array_artifact, members=assay.members)),
        e3_calibration_criterion=ScheduledCalibrationCriterion("criterion.disclosed.future", "unit.disclosed.future",
            candidate.population("CALIBRATION").expected_units, Decimal(0),
            (candidate.population("CALIBRATION").family_id,),
            "COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY"),
        e4_preparation_coordinates=tuple(replace(nominal, coordinate_id="coordinate.native-training.control.e4." + str(index),
            family_id=value.family_id) for index, value in enumerate(base.e4_preparation_coordinates)),
        e4_factorial=replace(base.e4_factorial, target=target, family_ids=family),
        e4_revision=replace(base.e4_revision, target=target),
        e4_structure=replace(base.e4_structure, factor_rule=scientific.full_factor_rule,
            numerical_design=native.prefix_policies[0].factor_numerical_design,
            secondary_target=replace(base.e4_structure.secondary_target, mathematical_protocol=mathematical)),
        e5_development=replace(base.e5_development, criterion=e5_criterion),
        e5_confirmation=replace(base.e5_confirmation, criterion=e5_criterion),
        e6=replace(base.e6, criterion=e6_criterion, expected_groups=candidate.population("TRANSFER_NEARBY").expected_units),
        e6_policy=replace(base.e6_policy, criterion=e6_criterion, calibration_alpha=candidate.calibration_alpha,
            endpoint_order=tuple((description, horizon) for description in candidate.measurement.descriptions
                for horizon in candidate.measurement.horizons)),
        prepared_assay=MatrixPreparedAssayMethod.from_assay(base.prepared_assay.record_id, assay))
    census, audit, provenance = train.audit.census, train.audit, train.provenances[0]
    e4_streams = SelectedE4StreamRecipe("streams.native-training.control.additional-e4", MATERIALS[2], MATERIALS[3], STREAM_RULE)
    planned = _source_plan(design=design, census=census, namespace=namespace,
        root_material=MATERIALS[0], future_material=MATERIALS[1],
        e4_streams=e4_streams,
        e5_root_material=MATERIALS[4], e5_future_material=MATERIALS[5])
    e1, populations, groups, futures, folds = planned
    design = replace(design, e1_criterion=replace(design.e1_criterion, allocation=sr.identity(e1)))

    shared_publications = {}
    def selected(record, key, *, publication=None, identity=None):
        pin = sr.identity(record) if identity is None else identity
        if pin in shared_publications:
            result = shared_publications[pin]
            if publication is not None and result.publication != publication:
                raise ValueError("disclosed whole C cannot replace actual shared publication custody")
            result.require_record(record, pin)
            return result
        publication = publish(plane, record, namespace + "." + key) if publication is None else publication
        result = MatrixProgrammePublishedInput(pin, publication)
        result.require_record(record, pin)
        shared_publications[pin] = result
        return result

    design_pub = selected(design, "design")
    census_publication, = audit.prior_corpus
    census_pub = selected(census, "census", publication=census_publication,
        identity=ObjectIdentity.from_record(census.census_id, census))
    audit_pub = selected(audit, "audit", publication=train.audit_publication)
    provenance_pub = selected(provenance, "provenance", identity=provenance.identity)
    definitions = {ObjectIdentity.from_record(value.definition_id, value): value for value in
        (design.e1_scalar_definition, design.e2.scalar_definition, train.scalar_definition)}
    scalar_owners = {ObjectIdentity.from_record(value.definition_id, value): owner for value, owner in (
        (design.e1_scalar_definition, design.e1_factor_rule.scalar_closure.normalization_owner),
        (design.e2.scalar_definition, design.e2.prefix_policies[0].factor_rule.scalar_closure.normalization_owner),
        (train.scalar_definition, native.prefix_policies[0].factor_rule.scalar_closure.normalization_owner))}
    scalars = tuple(selected(value, "scalar." + str(index), identity=pin,
        publication=train.scalar_definition_publication if value == train.scalar_definition else
            publish(plane, value, scalar_owners[pin].artifact_id))
        for index, (pin, value) in enumerate(sorted(definitions.items(), key=lambda row: row[0].object_id)))
    normalization = scientific.full_factor_rule.scalar_closure.normalization_owner
    source = Path(__file__).parents[1] / "src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py"
    raw = source.read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == (normalization.size_bytes, normalization.sha256)
    normalization_pub = plane.write(ArtifactWriteRequest(normalization.artifact_id,
        "whole-programme/normalization.py", normalization.payload_schema, ArtifactProfile.RAW_SOURCE_BYTES,
        normalization.media_type, namespace, "whole-programme", raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    e1_reservation = E1AllocationReservation("reservation." + namespace + ".e1", e1,
        publish(plane, e1, namespace + ".e1-allocation"))
    phases = {"e1": ResolvedMatrixProgrammePhaseInputs("e1", e1_reservation, None, None)}
    reservations = {"e1": selected(e1_reservation, "e1-reservation")}
    native_pubs, response_pubs = {}, {}

    def bind_phase(role, reservation, specification, response, *, reservation_publication=None):
        phases[role] = ResolvedMatrixProgrammePhaseInputs(role, reservation, specification, response)
        reservations[role] = selected(reservation, role + ".reservation", publication=reservation_publication)
        native_pubs[role] = selected(specification, role + ".specification")
        response_pubs[role] = selected(response, role + ".responses")

    train_panels = tuple((group, tuple(panel for panel in panels if panel.independent_group_id == group))
        for group in sorted({panel.independent_group_id for panel in panels}))
    train_responses = ScheduledResponseSelection("responses.native-training.control.train", ObjectIdentity.from_record(train.reservation.allocation.allocation_id, train.reservation.allocation),
        protocols, train_panels, template_publications, None)
    train_responses.validate_allocation(train.reservation.allocation)
    bind_phase("train", train.reservation, train.native_specification, train_responses,
        reservation_publication=train.reservation_publication)
    # Generate only the newly required disjoint metadata roles. Existing TRAIN
    # and four-role future allocation/stream/protocol bodies remain untouched.
    for population in populations:
        if population.name in ("train", "future"):
            continue
        exposure = train.reservation.allocation.exposure
        allocation = sr.ScheduledAllocation("allocation." + namespace + "." + population.name,
            population.coordinates, population.roots, population.scopes, exposure)
        reservation = sr.ScheduledReservation("reservation." + namespace + "." + population.name, allocation,
            publish(plane, allocation, namespace + "." + population.name + ".allocation"))
        selection = sr.ScheduledSelection("selection." + namespace + "." + population.name,
            sr.identity(reservation), population.numerical_design, population.prefix_policies, population.coordinate_policies)
        specification = sr.ScheduledSpecification("specification." + namespace + "." + population.name, selection,
            publish(plane, selection, namespace + "." + population.name + ".selection"))
        index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification, provenances=(provenance,))
        for role in ("e2", "e4.development", "e4.calibration", "e4.confirmation", "e5.development", "e5.confirmation"):
            roots = tuple(row for row in allocation.roots if row.root.independent_group_id in groups[role])
            if not roots:
                continue
            current_assay = design.e2.assay if role == "e2" else assay
            selected_protocols = tuple(current_assay.bind(index.resolve(index.reference(source_id="source." + row.root.root_id,
                root_id=row.root.root_id, provenance=provenance.identity)), protocol_id="protocol." + row.root.root_id) for row in roots)
            selected_panels = {}
            for row in roots:
                group = row.root.independent_group_id
                selected_panels[group] = (ScheduledResponsePanel("panel.common." + group, group, "COMMON_NOISE_PANEL",
                    "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", row.streams),
                    ScheduledResponsePanel("panel.independent." + group, group, "INDEPENDENT_FUTURE",
                        "FRESH_DECLARED_FUTURE_START_AT_CUTOFF", futures[group]))
            criterion = design.e4_calibration_criterion if role == "e4.calibration" else None
            response = ScheduledResponseSelection("responses." + namespace + "." + role, ObjectIdentity.from_record(allocation.allocation_id, allocation),
                selected_protocols, tuple(sorted(selected_panels.items())), template_publications, criterion)
            response.validate_allocation(allocation)
            bind_phase(role, reservation, specification, response)

    future_index = ScheduledSourceIndex.from_shared(reservation=future.reservation,
        specification=future.native_specification, provenances=(provenance,))
    role_kinds = (("CALIBRATION", "e3.calibration", MatrixProgrammeRole.CALIBRATION),
        ("EVALUATION", "e3.confirmation", MatrixProgrammeRole.CONFIRMATION),
        ("TRANSFER_NEARBY", "e6.nearby", MatrixProgrammeRole.WITHHELD_TRANSFER),
        ("TRANSFER_SHIFTED", "e6.shifted", MatrixProgrammeRole.WITHHELD_TRANSFER))
    for public_role, role, kind in role_kinds:
        coordinate = dict(candidate.role_coordinates)[public_role]
        roots = tuple(row for row in future.reservation.allocation.roots if row.root.role is kind and row.coordinate == coordinate)
        sources = tuple(future_index.resolve(future_index.reference(source_id="source.disclosed.future." + row.root.root_id,
            root_id=row.root.root_id, provenance=provenance.identity)) for row in roots)
        selected_protocols = tuple(replace(prototype, protocol_id="protocol.disclosed.future." + source.root_id,
            public_source=ScheduledPublicSource.from_source(source),
            templates=replace(prototype.templates, operand_id="templates.disclosed.future." + source.root_id,
                source=sr.identity(source), producers=(sr.identity(source),))) for source in sources)
        selected_panels = []
        for source in sources:
            group = source.root.root.independent_group_id
            independent = tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED.RESERVED.FUTURE." + public_role + "." + group + purpose).encode()).hexdigest())
                for purpose in HISTORY_PURPOSES)
            selected_panels.append((group, (ScheduledResponsePanel("panel.disclosed.future." + group + ".0", group,
                "COMMON_NOISE_PANEL", "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", source.root.streams),
                ScheduledResponsePanel("panel.disclosed.future." + group + ".1", group, "INDEPENDENT_FUTURE",
                    "FRESH_DECLARED_FUTURE_START_AT_CUTOFF", independent))))
        criterion = design.e3_calibration_criterion if public_role == "CALIBRATION" else None
        response = ScheduledResponseSelection("responses.disclosed.future." + public_role.lower(), ObjectIdentity.from_record(future.reservation.allocation.allocation_id, future.reservation.allocation),
            selected_protocols, tuple(sorted(selected_panels)), template_publications, criterion)
        response.validate_allocation(future.reservation.allocation)
        bind_phase(role, future.reservation, future.native_specification, response,
            reservation_publication=future.reservation_publication)
    clock = SystemDecisionClock()
    availability = AvailabilitySpec(clock.clock_id, CausalPhase.PREPARATION, OutcomeAccess.OUTCOME_BLIND,
        Decimal(int(datetime.fromisoformat(clock.now_utc().replace("Z", "+00:00")).timestamp())))
    availability_pin = ObjectIdentity.from_record(namespace + ".availability", availability)
    availability_pub = selected(availability, "availability", identity=availability_pin)
    policy = build_e6_transport_policy(record_id="policy." + namespace, candidate_specification=candidate,
        future_reservation=future.reservation,
        future_response_selections=tuple((public_role, phases[role].responses) for public_role, role, _ in role_kinds),
        availability=(availability_pin, availability), criterion=design.e6_policy.criterion)
    commitment = MatrixProgrammeInputCommitments("commitments." + namespace, namespace, design_pub, census_pub, audit_pub,
        provenance_pub, scalars, ((normalization, normalization_pub),),
        tuple(MatrixProgrammePhaseInputs(role, reservations[role], native_pubs.get(role), response_pubs.get(role))
            for role in PHASE_INPUT_ROLES), folds, availability_pub, selected(policy, "e6-policy"), e4_streams)
    resolved = ResolvedMatrixProgrammeInputs(commitment, design, census, audit, provenance,
        tuple(definitions[row.record] for row in scalars), tuple(phases[role] for role in PHASE_INPUT_ROLES), availability, policy)
    validate_programme_input_records(resolved)
    published = selected(commitment, "commitments")
    authenticated = authenticate_programme_inputs(writer=plane, commitment=published, maximum_source_bytes=128 * 1024**2)
    assert authenticated == resolved
    assert authenticated.phase("train").reservation.canonical_bytes() == train.reservation.canonical_bytes()
    assert authenticated.phase("e3.calibration").reservation.canonical_bytes() == future.reservation.canonical_bytes()
    assert authenticated.phase("train").responses.protocols == protocols
    assert authenticated.phase("train").responses.template_publications == template_publications
    return published, authenticated


def fresh_training_metadata_case(tmp_path, *, training_count=1, exposed_stream_group=None, future_namespace=None):
    """Actual small metadata publications, explicit synthetic exposure and seeds.

    Existing constructors produce no trajectories, eigensystems or ridge fits.
    This control does not establish real source qualification or freshness.
    """
    from empirical_lawhood.api import load_authoring
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from tests.test_matrix_factor_confirmation_eligibility import stock, provenance, publish
    from tests.test_matrix_scheduled_history import scheduled, CONSTRUCTION
    from tests.test_matrix_e3_protected_source_records import fixture, response_fixture
    from tests.test_matrix_configured_e3_v2 import configured_case
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    original = fixture(scheduled.__wrapped__(stock.__wrapped__(tmp_path, provenance.__wrapped__(),
        storage_codecs=operation_storage_codecs())))
    plane = original.plane
    support = []
    for name in ("audit", "inventory"):
        raw = ("explicit disclosed native TRAIN software " + name).encode()
        pub = plane.write(ArtifactWriteRequest("native-training.control." + name, "support/" + name + ".bin",
            "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", ArtifactProfile.RAW_SOURCE_BYTES,
            "text/plain", "control.native-training", "support", raw,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        support.append((corpus_artifact(pub), pub))
    previous = original.manifest.audit.census
    facts = tuple(sorted((*previous.factual_provenance, *(artifact for artifact, _ in support)),
        key=lambda value: value.artifact_id))
    census = replace(previous, factual_provenance=facts,
        exposed_artifact_sha256s=tuple(sorted({*previous.exposed_artifact_sha256s, *(value.sha256 for value in facts)})))
    census_pub = publish(plane, census, "native-training.control.census")
    audit = ScheduledExposureAudit("audit.native-training.control", census, (), (census_pub,))
    support = exposure_support(audit)
    audit_pub = publish(plane, audit, "native-training.control.audit-record")
    old = original.manifest
    allocation = replace(old.reservation.allocation, exposure=replace(old.reservation.allocation.exposure,
        census=census, scheduled_audit=corpus_artifact(audit_pub)))
    if future_namespace is not None:
        # A separate disclosed future fixture must not reserve the known exposed
        # TRAIN control's historical streams. Build all mappings before publishing.
        groups = {value.root.independent_group_id: future_namespace + "." + value.root.independent_group_id
            for value in allocation.roots}
        roots = tuple(replace(value, root=replace(value.root,
            root_id=future_namespace + "." + value.root.root_id,
            independent_group_id=groups[value.root.independent_group_id]), streams=tuple(MatrixHistorySeed(purpose,
                sha256(("EXPOSED.FUTURE.NATIVE.TRAIN.CONTROL." + groups[value.root.independent_group_id] + purpose).encode()).hexdigest())
                for purpose in HISTORY_PURPOSES)) for value in allocation.roots)
        scopes = tuple(replace(value, scope_id=future_namespace + "." + value.scope_id,
            independent_group_ids=tuple(groups[group] for group in value.independent_group_ids)) for value in allocation.matched_scopes)
        allocation = replace(allocation, allocation_id=future_namespace + ".allocation", roots=roots, matched_scopes=scopes)
    future = replace(old.reservation, allocation=allocation,
        publication=publish(plane, allocation, "native-training.control.future-allocation"))
    future_selection = replace(old.native_specification.selection, reservation=sr.identity(future))
    future_specification = replace(old.native_specification, selection=future_selection,
        publication=publish(plane, future_selection, "native-training.control.future-selection"))
    future_manifest = replace(old, record_id="manifest.native-training.control.future", reservation=future,
        native_specification=future_specification, audit=audit, audit_publication=audit_pub,
        reservation_publication=publish(plane, future, "native-training.control.future-reservation"))
    coordinate = original.inputs.nominal
    roots, scopes = [], []
    for index in range(training_count):
        root_id, group = "root.native-training.control." + str(index).zfill(3), "group.native-training.control." + str(index).zfill(3)
        known_group = exposed_stream_group[index] if type(exposed_stream_group) is tuple else exposed_stream_group
        prefix = ("EXPOSED.LITERAL.E3." + known_group if known_group is not None else
            "EXPOSED.NATIVE.TRAIN.CONTROL." + group)
        streams = tuple(MatrixHistorySeed(purpose, sha256((prefix + purpose).encode()).hexdigest())
            for purpose in HISTORY_PURPOSES)
        roots.append(sr.ScheduledRoot(MatrixProgrammeRoot(root_id, group, "regime.native-training.control",
            coordinate.coordinate_id, MatrixProgrammeRole.DEVELOPMENT, coordinate.clock_id), coordinate_identity(coordinate), streams))
        scopes.append(sr.ScheduledMatchedScope("scope.native-training.control." + str(index).zfill(3), MatrixProgrammeRole.DEVELOPMENT,
            (group,), (coordinate_identity(coordinate),), CONSTRUCTION))
    train_allocation = sr.ScheduledAllocation("allocation.native-training.control", (coordinate,), tuple(roots), tuple(scopes), allocation.exposure)
    train = sr.ScheduledReservation("reservation.native-training.control", train_allocation,
        publish(plane, train_allocation, "native-training.control.train-allocation"))
    policy = future_specification.selection.prefix_policies[0]
    train_selection = replace(future_selection, selection_id="selection.native-training.control",
        reservation=sr.identity(train), coordinate_policies=((coordinate_identity(coordinate), sr.identity(policy)),))
    train_native_specification = sr.ScheduledSpecification("native-specification.native-training.control", train_selection,
        publish(plane, train_selection, "native-training.control.train-selection"))
    train_manifest = replace(future_manifest, record_id="manifest.native-training.control.train", reservation=train,
        native_specification=train_native_specification,
        reservation_publication=publish(plane, train, "native-training.control.train-reservation"))
    source_index = ScheduledSourceIndex.from_shared(reservation=train, specification=train_native_specification,
        provenances=train_manifest.provenances)
    references = tuple(source_index.reference(source_id="source.native-training.control." + str(index).zfill(3),
        root_id=root.root.root_id, provenance=old.provenances[0].identity) for index, root in enumerate(roots))
    sources = tuple(source_index.resolve(reference) for reference in references)
    source = sources[0]
    response_case = SimpleNamespace(plane=plane, sources=sources, mathematical=original.mathematical,
        inputs=original.inputs, manifest=train_manifest, projection=original.projection)
    response_selection, protocols, panels = response_fixture(response_case)
    configured, _ = configured_case()
    populations = tuple(replace(value, expected_units=training_count, unit_ids=None) if value.role == "TRAIN" else value
        for value in original.inputs.specification.populations)
    coordinates = tuple((role, coordinate_identity(original.inputs.nearby if role == "TRANSFER_NEARBY" else
        original.inputs.shifted if role == "TRANSFER_SHIFTED" else coordinate)) for role, _ in configured.role_coordinates)
    candidate = ConfiguredProtectedE3Specification("candidate.native-training.control", configured.question,
        configured.protocol, populations, configured.methods, configured.assessment, configured.calibration_alpha,
        coordinates, evidence_scope="PROSPECTIVE_REQUIRED", calibration_target_view="MAX_PAIRED_VIEWS")
    specification = r.NativeTrainingAcquisitionSpecification("experiment.native-training.control", candidate.measurement,
        tuple(value.root_id for value in sources), sr.identity(future), candidate.identity)
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 128 * 1024**2, 64 * 1024**2)
    resources = r.NativeTrainingResources("resources.native-training.control",
        tuple((phase, budget) for phase in r.ALL_PHASES), 4)
    campaign = load_authoring(Path(__file__).parent / "fixtures/reference-campaign.json").campaign
    request_id = "request.native-training.control"
    campaign = replace(campaign, objective=acquisition.QUESTION, system_ids=(request_id,), world_ids=(acquisition.WORLD,),
        target_claim_ids=("claim.study." + specification.specification_id,), budget=ResourceBudget.aggregate((budget,) * (len(r.PHASES) * training_count + 2)))
    original_train = train_manifest.reservation.canonical_bytes(), train_manifest.native_specification.canonical_bytes()
    original_future = future_manifest.reservation.canonical_bytes(), future_manifest.native_specification.canonical_bytes()
    original_protocols = tuple(value.canonical_bytes() for value in protocols)
    original_panels = tuple(value.canonical_bytes() for value in panels)
    commitment, committed = _whole_training_commitment(plane=plane, train=train_manifest, future=future_manifest,
        candidate=candidate, mathematical=original.mathematical, protocols=protocols, panels=panels,
        template_publications=response_selection.template_publications)
    assert original_train == (train_manifest.reservation.canonical_bytes(), train_manifest.native_specification.canonical_bytes())
    assert original_future == (future_manifest.reservation.canonical_bytes(), future_manifest.native_specification.canonical_bytes())
    assert original_protocols == tuple(value.canonical_bytes() for value in protocols)
    assert original_panels == tuple(value.canonical_bytes() for value in panels)
    future_rows = (commitment, committed.commitments.availability, committed.commitments.e6_policy,
        *(committed.commitments.phase(role).responses for role in
            ("e3.calibration", "e3.confirmation", "e6.nearby", "e6.shifted")))
    campaign = replace(campaign, evidence_state=tuple(sorted((row.record for row in future_rows), key=lambda value: value.object_id)))
    support = (*support, *((corpus_artifact(row.publication), row.publication) for row in future_rows))
    request = r.NativeTrainingAcquisitionRequest(request_id, train_manifest, future_manifest, candidate,
        references, protocols, tuple(sorted(panels, key=lambda value: value.panel_id)),
        original.mathematical, response_selection.template_publications,
        tuple(sorted(support, key=lambda value: value[0].artifact_id)), campaign, resources, commitment)
    template_files = {protocol.templates.array_artifact.artifact_id: PreparedExperimentFile(protocol.templates.array_artifact,
        "1.0.0", plane.root.resolve(response_selection.template_publications[0].materialization.relative_path, for_write=False),
        protocol.templates.array_artifact.size_bytes) for protocol in protocols}
    return SimpleNamespace(plane=plane, request=request, specification=specification, template_files=template_files,
        source=source, sources=sources, acquisition=r.acquisition_seal(specification, request),
        programme_inputs=committed, future_availability=committed.availability,
        future_response_selections=tuple(sorted((committed.phase(role).responses for role in
            ("e3.calibration", "e3.confirmation", "e6.nearby", "e6.shifted")), key=lambda value: value.selection_id)))


@pytest.mark.parametrize("count", (1, 3))
def test_native_training_contracts_bound_full_request_hashing_and_preserve_all_root_operands(tmp_path, monkeypatch, count):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_bindings import NativeTrainingOperationConfig

    case = fresh_training_metadata_case(tmp_path, training_count=count)
    expected = case.specification.identity, case.request.identity
    calls = {"specification": 0, "request": 0}
    original = r._Identity.identity
    def counted(label):
        def identity(value):
            calls[label] += 1
            return original.__get__(value, type(value))
        return property(identity)
    acquisition._contracts.cache_clear()
    with monkeypatch.context() as control:
        control.setattr(r.NativeTrainingAcquisitionSpecification, "identity", counted("specification"))
        control.setattr(r.NativeTrainingAcquisitionRequest, "identity", counted("request"))
        configurations, *_ = acquisition.contracts(case.specification, case.request)
    acquisition._contracts.cache_clear()
    # Both existing request validations bind their actual training allocation.
    # The phase configurations share one further pin, independent of root count.
    assert calls == {"specification": 1, "request": 3}
    selected = {key: value for key, value in configurations if type(value) is NativeTrainingOperationConfig}
    assert len(selected) == count * len(r.PHASES) + 1
    assert all((value.specification, value.request) == expected for value in selected.values())
    assert {key for key in selected if key != acquisition.terminal_task_id(case.specification)} == {
        acquisition.task_id(root, phase) for root in case.specification.root_ids for phase in r.PHASES}


def test_public_native_training_preparation_compiles_exact_census_without_native_or_fits(tmp_path, monkeypatch):
    case = fresh_training_metadata_case(tmp_path)
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as bindings
    monkeypatch.setattr(bindings, "execute_parameter_native_work", lambda *a, **k: pytest.fail("metadata entered native prefix"))
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", lambda *a, **k: pytest.fail("metadata entered native futures"))
    bound = acquisition.bind_inputs(case.specification, {"request": case.request}, files=case.template_files)
    execution = ExecutionSelection(4, "environment.disclosed", case.source.provenance.identity, str(tmp_path))
    prepared = acquisition.prepare(case.specification, execution=execution, method_inputs=bound.method_inputs)
    assert prepared.executable and prepared.census.native_effect_count == 2
    assert all(value.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE and
        value.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY for value in prepared.draft.external_inputs)
    assert all(value.templates.outcome_access is OutcomeAccess.OUTCOME_BLIND and
        value.templates.visibility_ceiling is VisibilityCeiling.PROSPECTIVE for value in case.request.protocols)
    assert all(value.logical.outcome_access is OutcomeAccess.OUTCOME_BLIND and
        value.logical.visibility_ceiling is VisibilityCeiling.PROSPECTIVE for value in case.request.template_publications)
    assert dict(prepared.census.output_counts)["selected-tasks"] == 11
    declarations = operation_declarations()
    registry = CapabilityRegistry("registry.native-training.control", tuple(sorted((value.manifest() for value in declarations),
        key=lambda value: value.registry_id)))
    compiled = compile_recursive_wave(draft=prepared.draft, registrations=tuple(value.registration() for value in declarations),
        registry=registry, implementation_commit=case.source.provenance.observed_git_head,
        output_codecs={key: value for declaration in declarations for key, value in declaration.record_codecs.items()})
    assert len(compiled.execution_plan.tasks) == 11
    assert sum(value.registration().native_effect for value in declarations) == 2
    assert all(value.capability.requested_resources.cpu_cores == 1 for value in compiled.execution_plan.tasks)
    for value in (case.specification, case.request, case.acquisition):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value


def test_native_training_export_preserves_frame_free_nonuse_and_complete_denominator(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    public = case.request.protocols[0].public_source
    causal = ObjectIdentity("causal.disclosed.native-training", r.NativeTrainingCausalPrefix.SCHEMA, "1.0.0", "a" * 64)
    evidence = (case.acquisition.identity,)
    feature = r.NativeTrainingFeature("feature.disclosed.native-training", public.root.independent_group_id,
        case.request.identity, public.source, causal, public.root.clock_id, public.coordinate.physical_time(public.policy.cutoff_tick),
        None, "NO_CAUSAL_ORIGIN", (), evidence)
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3ViewOutcome
    views = tuple(MatrixE3ViewOutcome(view, (None,) * 15, ("UNAVAILABLE",) * 15) for view in ("fine", "primary"))
    outcome = r.NativeTrainingOutcome("outcome.disclosed.native-training", feature.unit_id, feature.source_manifest,
        feature.native_source, feature.origin, feature.clock_id, feature.cutoff, None, views, "UNEVALUABLE", evidence)
    allocation, features, outcomes = acquisition.export_training_banks(case.specification, case.request,
        acquisition=case.acquisition, features=(feature,), outcomes=(outcome,), record_id="banks.disclosed.native-training")
    assert allocation.unit_ids("train") == (feature.unit_id,)
    assert features.rows[0].frame_sha256 is None and outcomes.rows[0].views == views
    assert decode_canonical_bytes(features.canonical_bytes(), type(features), maximum_bytes=None) == features
    with pytest.raises(ValueError, match="assigned|bank"):
        acquisition.export_training_banks(case.specification, case.request, acquisition=case.acquisition,
            features=(), outcomes=(), record_id="banks.refuse-dropped-unit")
    with pytest.raises(ValueError, match="substitute"):
        acquisition.export_training_banks(case.specification, case.request, acquisition=case.acquisition,
            features=(replace(feature, origin=replace(causal, object_id="causal.foreign")),), outcomes=(outcome,), record_id="banks.refuse-crossed-prefix")


def _republish_manifest(case, manifest, allocation, namespace, *, audit=None, audit_publication=None):
    from tests.test_matrix_factor_confirmation_eligibility import publish
    reservation = replace(manifest.reservation, allocation=allocation,
        publication=publish(case.plane, allocation, namespace + ".allocation"))
    selection = replace(manifest.native_specification.selection, reservation=sr.identity(reservation))
    native_specification = replace(manifest.native_specification, selection=selection,
        publication=publish(case.plane, selection, namespace + ".selection"))
    return replace(manifest, reservation=reservation, native_specification=native_specification,
        audit=manifest.audit if audit is None else audit,
        audit_publication=manifest.audit_publication if audit_publication is None else audit_publication,
        reservation_publication=publish(case.plane, reservation, namespace + ".reservation"))


def test_incomplete_future_reserve_refuses_before_training_acquisition(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    with pytest.raises(ValueError, match="future reservation"):
        r.validate_request(replace(case.specification, future_reservation=replace(case.specification.future_reservation,
            object_fingerprint="b" * 64)), case.request)
    original = case.request.future_manifest.reservation.allocation
    omitted = next(value for value in original.roots if value.root.role is MatrixProgrammeRole.CALIBRATION)
    scopes = tuple(replace(value, independent_group_ids=tuple(group for group in value.independent_group_ids
        if group != omitted.root.independent_group_id)) if omitted.root.independent_group_id in value.independent_group_ids else value
        for value in original.matched_scopes)
    allocation = replace(original, roots=tuple(value for value in original.roots if value != omitted), matched_scopes=scopes)
    manifest = _republish_manifest(case, case.request.future_manifest, allocation, "missing-future-root")
    specification = replace(case.specification, future_reservation=sr.identity(manifest.reservation))
    with pytest.raises(ValueError, match="census|count|denominator|population|units"):
        r.validate_request(specification, replace(case.request, future_manifest=manifest))


def test_other_future_census_exposure_refuses_before_training_acquisition(tmp_path):
    from tests.test_matrix_factor_confirmation_eligibility import publish
    case = fresh_training_metadata_case(tmp_path)
    original = case.request.future_manifest
    exposed = case.source.root.streams[0].effective_seed
    census = replace(original.audit.census,
        effective_seed_exclusions=tuple(sorted((*original.audit.census.effective_seed_exclusions, exposed))))
    corpus = (publish(case.plane, census, "other-census.exposure"),)
    audit = replace(original.audit, audit_id="audit.other-census.exposure", census=census, prior_corpus=corpus)
    audit_publication = publish(case.plane, audit, "other-census.audit")
    allocation = replace(original.reservation.allocation, exposure=replace(original.reservation.allocation.exposure,
        census=census, scheduled_audit=corpus_artifact(audit_publication)))
    manifest = _republish_manifest(case, original, allocation, "other-census.future", audit=audit, audit_publication=audit_publication)
    specification = replace(case.specification, future_reservation=sr.identity(manifest.reservation))
    with pytest.raises(ValueError, match="overlap"):
        r.validate_request(specification, replace(case.request, future_manifest=manifest))


def test_withheld_physics_cannot_be_renamed_into_separate_training_allocation(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    original = case.request.train_manifest
    withheld = next(value for value in case.request.future_manifest.reservation.allocation.coordinates
        if coordinate_identity(value) == dict(case.request.candidate_specification.role_coordinates)["TRANSFER_SHIFTED"])
    old_coordinate = case.source.coordinate
    coordinate = replace(withheld, coordinate_id="coordinate.renamed-withheld-training", clock_id=old_coordinate.clock_id)
    old_root = original.reservation.allocation.roots[0]
    root = replace(old_root, root=replace(old_root.root, coordinate_id=coordinate.coordinate_id,
        regime_id="regime.renamed-withheld-training"), coordinate=coordinate_identity(coordinate))
    scope = replace(original.reservation.allocation.matched_scopes[0], coordinates=(coordinate_identity(coordinate),))
    allocation = replace(original.reservation.allocation, coordinates=(coordinate,), roots=(root,), matched_scopes=(scope,))
    manifest = _republish_manifest(case, original, allocation, "renamed-withheld.train")
    from tests.test_matrix_factor_confirmation_eligibility import publish
    policy = manifest.native_specification.selection.prefix_policies[0]
    selection = replace(manifest.native_specification.selection, coordinate_policies=((coordinate_identity(coordinate), sr.identity(policy)),))
    native_specification = replace(manifest.native_specification, selection=selection,
        publication=publish(case.plane, selection, "renamed-withheld.train-selection"))
    manifest = replace(manifest, native_specification=native_specification)
    source_index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation, specification=native_specification,
        provenances=manifest.provenances)
    source = source_index.resolve(source_index.reference(source_id=case.source.source_id,
        root_id=case.source.root_id, provenance=case.source.provenance.identity))
    old_protocol = case.request.protocols[0]
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    protocol = replace(old_protocol, public_source=ScheduledPublicSource.from_source(source),
        templates=replace(old_protocol.templates, source=sr.identity(source), producers=(sr.identity(source),)))
    candidate = replace(case.request.candidate_specification, role_coordinates=tuple((role,
        coordinate_identity(coordinate) if role == "TRAIN" else value) for role, value in case.request.candidate_specification.role_coordinates))
    specification = replace(case.specification, candidate=candidate.identity)
    request = replace(case.request, train_manifest=manifest, candidate_specification=candidate,
        sources=(source.reference,), protocols=(protocol,))
    with pytest.raises(ValueError, match="withheld future physical"):
        r.validate_request(specification, request)


def test_configured_e3_public_sources_loader_accepts_exact_native_training_banks(tmp_path):
    """Real public file admission; disclosed nonuse records, no fit or native run."""
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, load_experiment_specification
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3ViewOutcome
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection

    case = fresh_training_metadata_case(tmp_path)
    public = case.request.protocols[0].public_source
    causal = ObjectIdentity("causal.disclosed.native-file-control", r.NativeTrainingCausalPrefix.SCHEMA, "1.0.0", "a" * 64)
    feature = r.NativeTrainingFeature("feature.disclosed.native-file-control", public.root.independent_group_id,
        case.request.identity, public.source, causal, public.root.clock_id,
        public.coordinate.physical_time(public.policy.cutoff_tick), None, "NO_CAUSAL_ORIGIN", (), (case.acquisition.identity,))
    views = tuple(MatrixE3ViewOutcome(view, (None,) * 15, ("UNAVAILABLE",) * 15) for view in ("fine", "primary"))
    outcome = r.NativeTrainingOutcome("outcome.disclosed.native-file-control", feature.unit_id, feature.source_manifest,
        feature.native_source, feature.origin, feature.clock_id, feature.cutoff, None, views, "UNEVALUABLE", (case.acquisition.identity,))
    _, features, outcomes = acquisition.export_training_banks(case.specification, case.request,
        acquisition=case.acquisition, features=(feature,), outcomes=(outcome,), record_id="banks.disclosed.native-file-control")
    directory = tmp_path / "copied-native-bank-inputs"
    directory.mkdir()
    specification_path = directory / "specification.json"
    specification_path.write_bytes(case.request.candidate_specification.canonical_bytes())
    files = []
    for name, value in (("features", features), ("outcomes", outcomes)):
        raw = value.canonical_bytes()
        path = directory / (name + ".json")
        path.write_bytes(raw)
        artifact = ArtifactIdentity(value.record_id, "disclosed-native-file-control", value.SCHEMA,
            value.fingerprint(), "application/json", len(raw))
        files.append(ExperimentFileInputBinding(artifact.artifact_id, artifact, value.VERSION, path.name, len(raw)))
    selection = ExperimentFileInputSelection("sources.disclosed-native-file-control", "matrix.response-error.configured-protected-v2",
        (), tuple(sorted(files, key=lambda value: value.key)))
    sources_path = directory / "sources.json"
    sources_path.write_bytes(selection.canonical_bytes())
    specification = load_experiment_specification(specification_path)
    loaded = load_experiment_inputs(specification, sources_path)
    assert loaded.scientific_inputs == {}
    assert tuple(key for key, _ in loaded.method_inputs.files) == tuple(value.key for value in selection.files)
    assert tuple(value.identity.payload_schema for _, value in loaded.method_inputs.files) == (
        r.NativeTrainingFeatureBank.SCHEMA, r.NativeTrainingOutcomeBank.SCHEMA)
    assert all(value.path.read_bytes() == expected.canonical_bytes() for (_, value), expected in
        zip(loaded.method_inputs.files, (features, outcomes), strict=True))
    # Missing protected selection remains an explicit dependency; file admission
    # cannot create prospective authority or skip exact original byte checks.
    assert loaded.method_inputs.selection is None
    (directory / "features.json").write_bytes(b" " + features.canonical_bytes()[1:])
    with pytest.raises(ValueError, match="selected exact bytes|selected bytes|bounded"):
        load_experiment_inputs(specification, sources_path)


def test_e4_full_physical_exclusion_accepts_half_double_grid_and_refuses_renamed_t3(tmp_path):
    from itertools import product
    from decimal import Decimal
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import require_e4_reserved_physical_exclusion
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
    case = fresh_training_metadata_case(tmp_path)
    reservation = case.request.future_manifest.reservation
    nominal = case.source.coordinate
    corners = (*product((Decimal(".5"), Decimal(2)), repeat=3), (Decimal(1),) * 3)
    coordinates = tuple(replace(nominal, coordinate_id="coordinate.disclosed-e4." + str(fi) + "." + str(ci),
        family_id=family, member=replace(nominal.member, cross_coupling_gamma=coupling),
        primary_view=replace(nominal.primary_view, bath_temperature=temperature, friction_gamma=friction),
        fine_view=replace(nominal.fine_view, bath_temperature=temperature, friction_gamma=friction))
        for fi, family in enumerate(sorted(FOUR_FAMILY_PREPARATION_IDS))
        for ci, (temperature, friction, coupling) in enumerate(corners))
    assert len(coordinates) == 36
    require_e4_reserved_physical_exclusion(coordinates, reservation)
    shifted = next(value for value in reservation.allocation.coordinates
        if coordinate_identity(value) == dict(case.request.candidate_specification.role_coordinates)["TRANSFER_SHIFTED"])
    assert shifted.primary_view.bath_temperature == Decimal(3)
    renamed = replace(shifted, coordinate_id="coordinate.disclosed-e4.renamed-t3", clock_id="clock.disclosed-e4.renamed-t3",
        member=replace(shifted.member, member_id="member.disclosed-e4.renamed-t3"),
        primary_view=replace(shifted.primary_view, view_id="view.disclosed-e4.renamed-t3.primary"),
        fine_view=replace(shifted.fine_view, view_id="view.disclosed-e4.renamed-t3.fine"))
    with pytest.raises(ValueError, match="reserved E6 full physical key"):
        require_e4_reserved_physical_exclusion((renamed,), reservation)
    # Temperature alone is not a full regime: retain the other physical fields.
    require_e4_reserved_physical_exclusion((replace(renamed, member=replace(renamed.member,
        cross_coupling_gamma=Decimal(2))),), reservation)
