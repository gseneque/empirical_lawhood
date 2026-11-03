# SPDX-License-Identifier: MPL-2.0
"""In-memory selected graph controls; synthetic descriptors grant no authority.

Only declared metadata and literal bytes are constructed. No publication,
trajectory, native child, signer, source qualification or filesystem write runs.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as declarative

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationInitialState
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource, MatrixPreparedRecipeInterpretation
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponsePanel
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import MatrixConfirmationSources, MatrixProtectedSourceClosure, MatrixReservedTransferSources
from empirical_lawhood.adapters.methods.matrix_experimental_programme.functional_outcome_reduction import _nominate_functional_cases
from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixFunctionalCaseResult
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import adapt_e3_frozen_package
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointDesign
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme, MatrixSelectedProtectedRootConfig, global_node
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import assess_selected_programme, entry_seal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import (
    MANDATORY_EFFECTIVE_SEEDS, MANDATORY_FLOOR_IDENTITY, MANDATORY_FLOOR_SHA256,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from empirical_lawhood.planning.study_authoring import SourceAccessDisposition
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, LogicalArtifactIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, validate_recursive_scientific_roots
from tests.runtime_platform.test_candidate_compiler import _fixture as candidate_fixture
from tests.test_matrix_later_programme import criterion
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_prepared_assay_method import literal_protocol
from tests.test_matrix_selected_package import package, reference
from tests.test_matrix_selected_point import selected_design


def unpublished(record, name):
    """Type-correct disclosed descriptor without durable publication custody."""
    raw = record.canonical_bytes()
    logical = LogicalArtifactIdentity(name, record.fingerprint(), record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND,
        ArtifactGenericValidation("validator.synthetic-selected", "1.0.0", "a" * 64, record.SCHEMA, ArtifactProfile.CANONICAL_JSON))
    physical = ArtifactMaterialization("material." + name, name, "storage.synthetic-unpublished", "unpublished/" + name,
        record.fingerprint(), len(raw), "none")
    sidecar = replace(physical, materialization_id="sidecar." + name, logical_artifact_id=name + ".manifest",
        relative_path="unpublished/" + name + ".manifest.json", physical_sha256="b" * 64, size_bytes=1)
    return ArtifactWriteResult(logical, physical, sidecar, False)


@pytest.fixture(scope="module")
def transfer():
    return transfer_case()


def transfer_case(*, groups_per_regime=1):
    """Explicit exposed whole-root counts; creates no receipt/publication/native work."""
    design = selected_design("E6_TRANSFER", transfer_count=groups_per_regime)
    template = parameter_template()
    placeholder = ArtifactIdentity("audit.synthetic-selected", "synthetic-unpublished", "empirical-lawhood/testing/selected-audit",
        "a" * 64, "application/json", 1)
    census = MatrixFactorExposureCensus("census.synthetic-selected", MANDATORY_FLOOR_IDENTITY,
        tuple(sorted(MANDATORY_EFFECTIVE_SEEDS)), (), (), (), (),
        tuple(sorted({MANDATORY_FLOOR_SHA256, placeholder.sha256})), (placeholder,))
    audit = ScheduledExposureAudit("audit.synthetic-selected", census, (), (unpublished(census, "corpus.synthetic-selected"),))
    audit_publication = unpublished(audit, "audit.synthetic-selected")
    audit_artifact = ArtifactIdentity(audit_publication.logical.logical_artifact_id, "synthetic-unpublished", audit.SCHEMA,
        audit.fingerprint(), "application/json", len(audit.canonical_bytes()))
    roots, scopes = [], []
    coordinates = tuple(sorted({row.original.coordinate for _, row in design.sources}, key=lambda row: row.coordinate_id))
    for _, row in design.sources:
        root = row.original.root
        streams = tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_SELECTED." + root.independent_group_id + purpose).encode()).hexdigest())
            for purpose in HISTORY_PURPOSES)
        roots.append(old.ScheduledRoot(root, old.coordinate_identity(row.original.coordinate), streams))
        scopes.append(old.ScheduledMatchedScope("scope." + root.independent_group_id, root.role, (root.independent_group_id,),
            (old.coordinate_identity(row.original.coordinate),), "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"))
    allocation = old.ScheduledAllocation("original.scheduled", coordinates, tuple(sorted(roots, key=lambda row: row.root.root_id)),
        tuple(sorted(scopes, key=lambda row: row.scope_id)), old.ScheduledExposure("exposure.synthetic-selected", census, (), audit_artifact))
    reservation = old.ScheduledReservation("original.reservation", allocation, unpublished(allocation, "allocation.synthetic-selected"))
    policy = design.sources[0][1].original.policy
    selection = old.ScheduledSelection("selection.synthetic-selected", old.identity(reservation), template.numerical_design,
        (policy,), tuple((old.coordinate_identity(row), old.identity(policy)) for row in coordinates))
    specification = old.ScheduledSpecification("original.native", selection, unpublished(selection, "selection.synthetic-selected"))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=(template.provenance,))
    descriptors = tuple(source_index.reference(source_id="source." + row.root.root_id,
        root_id=row.root.root_id, provenance=template.provenance.identity) for row in allocation.roots)
    subjects = tuple(source_index.resolve(row) for row in descriptors)
    raw, members = encode_matrix_arrays({"positions": np.zeros((2, 3, 4, 4), dtype="<c16"), "momenta": np.zeros((2, 3, 4, 4), dtype="<c16")})
    states = tuple((subject.root_id, MatrixPreparationInitialState("initial." + subject.root_id,
        reference("prior." + subject.root_id, old.ScheduledPrefixHistory), reference("assessment." + subject.root_id, old.ScheduledNumericalAssessment),
        ArtifactIdentity("array.initial." + subject.root_id, "literal-in-memory", MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), "application/x-npz", len(raw)),
        members, dict(design.arms)["hold"].half_tick_couplings[0])) for subject in subjects)
    closure = MatrixProtectedSourceClosure("closure.synthetic-selected", reservation, specification, (template.provenance,),
        descriptors, audit, audit_publication, states,
        reference("numerical-scope.synthetic-selected", old.ScheduledNumericalAssessment))
    sources = MatrixReservedTransferSources("sources.synthetic-selected", closure,
        tuple((old.coordinate_identity(coordinate), dict(design.arms)["hold"]) for coordinate in coordinates), "hold")
    # Rebind the synthetic original upstream package to these actual declared
    # allocation/reservation/specification objects. No custody is asserted.
    value = package(transfer_count=groups_per_regime)
    replacements = {"original.scheduled": old.identity(allocation), "original.reservation": old.identity(reservation), "original.native": old.identity(specification)}
    roles = replace(value.allocation, sources=tuple(replacements.get(row.object_id, row) for row in value.allocation.sources))
    pins = {"allocation": old.identity(allocation), "native-selection": old.identity(specification), "reservation": old.identity(reservation), "roles": roles.identity}
    prefit = replace(value.prefit, allocation=roles.identity, original_allocation=old.identity(allocation), reservation=old.identity(reservation),
        native_specification=old.identity(specification), publications=tuple((key, replace(artifact, payload_schema=pins[key].object_schema,
            sha256=pins[key].object_fingerprint), material, availability) for key, artifact, material, availability in value.prefit.publications))
    models = replace(value.models, allocation=roles.identity, reservation_join=prefit.identity)
    frozen = e3.freeze_protected_e3(value.specification, roles, models, record_id=value.model_freeze.record_id)
    calibration = replace(value.calibration, allocation=roles.identity, models=e3.identity(models), model_freeze=e3.identity(frozen))
    calibrated = e3.freeze_protected_e3(value.specification, roles, models, record_id=value.calibrated_freeze.record_id,
        model_freeze=frozen, calibration=calibration)
    value = adapt_e3_frozen_package(record_id=value.record_id, specification=value.specification, allocation=roles, prefit=prefit,
        models=models, model_freeze=frozen, calibration=calibration, calibrated_freeze=calibrated, selection_unit_ids=value.selection_unit_ids)
    projected = tuple((arm, MatrixPreparedPublicSource.from_source(source)) for arm, source in sources.source_arms())
    design = MatrixSelectedPointDesign(design.record_id, value, "E6_TRANSFER", groups_per_regime, design.arms, projected,
        tuple(MatrixPreparedRecipeInterpretation(recipe.identity, "cc1.history.de-anneal", reference("premise.selected." + arm, type(recipe)))
            for arm, recipe in design.arms))
    protocol, _ = literal_protocol()
    measurement = value.specification.measurement
    protocol = replace(protocol, actions=tuple(replace(action, amplitude=measurement.action_amplitude, pulse_steps=measurement.pulse_ticks)
        for action in protocol.actions))
    assay = MatrixPreparedAssayMethod.from_protocol("assay.synthetic-selected", protocol)
    panels = tuple((source.root.root.independent_group_id, tuple(MatrixPreparedResponsePanel("panel." + source.root.root.independent_group_id + "." + str(index),
        source.root.root.independent_group_id, role, source.root.streams if role == "COMMON_NOISE_PANEL" else
        tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_FUTURE." + source.source_id + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
        for index, role in enumerate(("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")))) for _, source in sources.source_arms())
    return MatrixSelectedProtectedProgramme("programme.synthetic-selected", sources, design, assay, tuple(sorted(panels)),
        replace(criterion(1), effort_unit=dict(design.arms)["hold"].effort_unit),
        ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN"), None, None, None)


@pytest.fixture(scope="module")
def confirmation(transfer):
    return confirmation_case(transfer)


def confirmation_case(transfer, *, groups=1):
    """Exposed whole CONF groups/two arms; unpublished original DEV decision only."""
    template = selected_design("E5_CONFIRMATION")
    coordinate, policy = template.sources[0][1].original.coordinate, template.sources[0][1].original.policy
    original = transfer.sources.closure
    sample = original.reservation.allocation.roots[0]
    roots=[]
    for index in range(groups):
        suffix="" if index==0 else "."+str(index).zfill(3)
        group="group.confirmation.synthetic-selected"+suffix
        roots.append(replace(sample, root=replace(sample.root, root_id="root.confirmation.synthetic-selected"+suffix,
            independent_group_id=group,regime_id="regime.confirmation.synthetic-selected",coordinate_id=coordinate.coordinate_id,
            clock_id=coordinate.clock_id,role=old.MatrixProgrammeRole.CONFIRMATION),coordinate=old.coordinate_identity(coordinate),
            streams=tuple(MatrixHistorySeed(purpose,sha256(("DISCLOSED_CONFIRMATION."+suffix+purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
    scope=old.ScheduledMatchedScope("scope.confirmation.synthetic-selected",roots[0].root.role,
        tuple(root.root.independent_group_id for root in roots),(roots[0].coordinate,),
        "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU")
    allocation=replace(original.reservation.allocation,allocation_id="allocation.confirmation.synthetic-selected",coordinates=(coordinate,),
        roots=tuple(roots),matched_scopes=(scope,))
    reservation=old.ScheduledReservation("reservation.confirmation.synthetic-selected",allocation,unpublished(allocation,"allocation.confirmation.synthetic-selected"))
    selection=old.ScheduledSelection("selection.confirmation.synthetic-selected",old.identity(reservation),original.specification.selection.numerical_design,
        (policy,),((roots[0].coordinate,old.identity(policy)),))
    specification=old.ScheduledSpecification("specification.confirmation.synthetic-selected",selection,unpublished(selection,"selection.confirmation.synthetic-selected"))
    source_index=ScheduledSourceIndex.from_shared(reservation=reservation,specification=specification,
        provenances=original.provenances)
    descriptors=tuple(source_index.reference(source_id="source.confirmation.synthetic-selected"+
        ("" if index==0 else "."+str(index).zfill(3)),root_id=root.root.root_id,
        provenance=original.provenances[0].identity) for index,root in enumerate(roots))
    states=tuple((root.root.root_id,replace(original.initial_states[0][1],state_id="initial.confirmation.synthetic-selected"+
        ("" if index==0 else "."+str(index).zfill(3)))) for index,root in enumerate(roots))
    closure=MatrixProtectedSourceClosure("closure.confirmation.synthetic-selected",reservation,specification,original.provenances,
        descriptors,original.audit,original.audit_publication,states,original.numerical_scope)
    sources=MatrixConfirmationSources("sources.confirmation.synthetic-selected",closure,template.arms,"hold")
    design=MatrixSelectedPointDesign("design.confirmation.synthetic-selected",transfer.point_design.package,"E5_CONFIRMATION",groups,template.arms,
        tuple((arm,MatrixPreparedPublicSource.from_source(source)) for arm,source in sources.source_arms()),template.interpretations)
    all_panels=[]
    for root_index,root in enumerate(roots):
        group=root.root.independent_group_id;suffix="" if root_index==0 else "."+str(root_index).zfill(3)
        panels=tuple(MatrixPreparedResponsePanel("panel."+group+"."+str(index),group,role,root.streams if index==0 else
            tuple(MatrixHistorySeed(purpose,sha256(("DISCLOSED_CONFIRMATION_FUTURE."+suffix+purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
            for index,role in enumerate(("COMMON_NOISE_PANEL","INDEPENDENT_FUTURE")))
        all_panels.append((group,panels))
    declared = transfer.criterion
    recipes = tuple(sorted((*template.arms, ("fixed-b", replace(dict(template.arms)["fixed-a"], recipe_id="recipe.synthetic-selected.fixed-b")))))
    cases = tuple(MatrixFunctionalCaseResult("case.opportunity.synthetic-selected." + arm, "group.opportunity.synthetic-selected", arm,
        "FINITE", D(".9") if arm == "hold" else D(".01"), D(".1"), None, arm != "hold", False, None, False, recipe.effort, ())
        for arm, recipe in recipes)
    nomination = _nominate_functional_cases(result_id="nomination.synthetic-selected", specification_identity=design.identity,
        package_identity=design.package.identity, roster_identity=reference("roster.opportunity.synthetic-selected", old.ScheduledAllocation),
        evidence_identity=reference("evidence.opportunity.synthetic-selected", old.ScheduledAllocation), group_ids=("group.opportunity.synthetic-selected",),
        arm_ids=tuple(arm for arm, _ in recipes), hold_arm_id="hold", criterion=declared, minimum_recoverable_groups=1,
        tie_policy="LEXICAL_ARM_ID", recipes=tuple((arm, recipe.identity) for arm, recipe in recipes), cases=cases)
    publication = unpublished(nomination, "nomination.synthetic-selected")
    publication = replace(publication, logical=replace(publication.logical, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY))
    receipt = CanonicalTaskReceipt("receipt.nomination.synthetic-selected", "run.opportunity.synthetic-selected", "task.nomination.synthetic-selected",
        "attempt.nomination.synthetic-selected", original.provenances[0].observed_git_head, (), (publication.materialization,), (publication.logical,),
        (), OperationalStatus.SUCCEEDED, ())
    return MatrixSelectedProtectedProgramme("programme.confirmation.synthetic-selected", sources, design, transfer.assay, tuple(all_panels), declared,
        (), nomination, publication, receipt)


def test_selected_declarations_install_exact_parent_preparation_and_phase_gated_native_interface():
    declarations = owner.operation_declarations()
    configurations = {
        "assess": owner.preparation.MatrixPreparationOperationConfig,
        "measure": owner.MatrixSelectedPreparedConfig,
        "frames": owner.MatrixSelectedPreparedConfig,
        "project": owner.MatrixSelectedPreparedConfig,
        "point": owner.MatrixSelectedPreparedConfig,
        "mechanical": owner.MatrixSelectedPreparedConfig,
        "response-score": owner.MatrixSelectedFutureConfig,
        "assess-programme": owner.MatrixSelectedProtectedRootConfig,
    }
    expected = {(owner.NAMESPACE + "." + phase, "1.0.0"): kind
        for phase, kind in configurations.items()}
    expected.update({
        (owner.ENTRY_ORIGINAL_COMMITMENTS_KEY, "3.0.0"): owner.MatrixSelectedProtectedRootConfigV3,
        (owner.capability_key("history", "2.0.0"), "2.0.0"): owner.preparation.MatrixPreparationOperationConfigV2,
        (owner.capability_key("responses", "2.0.0"), "2.0.0"): owner.MatrixSelectedFutureConfigV2,
        (owner.ENTRY_TRANSPORT_KEY, "4.0.0"): owner.MatrixSelectedTransportRootConfig,
        (owner.capability_key("point", "2.0.0"), "2.0.0"): owner.MatrixSelectedTransportPointConfig,
        (owner.capability_key("responses", "3.0.0"), "3.0.0"): owner.MatrixSelectedTransportFutureConfig,
        (owner.capability_key("response-score", "2.0.0"), "2.0.0"): owner.MatrixSelectedTransportScoreConfig,
        (owner.capability_key("assess-programme", "2.0.0"), "2.0.0"): owner.MatrixSelectedTransportRootConfig,
    })
    assert len(declarations) == len(expected)
    assert {(row.capability_key, row.capability_version): row.config_record_type
        for row in declarations} == expected
    assert {(row.capability_key, row.capability_version) for row in declarations
        if row.registration().native_effect} == {
            (owner.capability_key("history", "2.0.0"), "2.0.0"),
            (owner.capability_key("responses", "2.0.0"), "2.0.0"),
            (owner.capability_key("responses", "3.0.0"), "3.0.0")}
    entry_evidence = {
        (owner.ENTRY_ORIGINAL_COMMITMENTS_KEY, "3.0.0"): owner.MatrixSelectedEntryEvidenceV3,
        (owner.ENTRY_TRANSPORT_KEY, "4.0.0"): owner.MatrixSelectedEntryEvidenceV3,
    }
    for declaration in declarations:
        kind = entry_evidence.get((declaration.capability_key, declaration.capability_version))
        if kind is not None:
            port, = declaration.input_ports
            assert (port.port_id, port.payload_schema) == ("entry-evidence", kind.SCHEMA)
    for phase in owner.NATIVE:
        with pytest.raises(ValueError, match="installed phase/version"):
            owner.capability_key(phase, "1.0.0")
        with pytest.raises(ValueError, match="current direct-input"):
            owner.phase_inputs(phase)
    for declaration in declarations:
        assert declaration.execution_properties.runner_preparation_factory is owner.prepare_for_invocation
        runner = declaration.runner_factory()
        phase = runner.phase
        assert type(runner) is SelectedProtectedWorker and runner.prepared_scope is None
        assert callable(runner.execute_with_native_subwork) == (phase in owner.NATIVE)
        assert callable(declaration.registration().native_work_preparer) == (phase in owner.NATIVE)


def test_transfer_graph_derives_all_native_forecast_and_assessor_edges_from_actual_original_roots(transfer):
    evidence = ObjectIdentity("evidence.unpublished", owner.MatrixSelectedEntryEvidenceV3.SCHEMA, owner.MatrixSelectedEntryEvidenceV3.VERSION, "a" * 64)
    from tests.test_matrix_e6_transport_assessment import exposed_parent_census
    configs, external, links, records, arrays = owner.contracts(transfer, evidence, 1,
        produced_input_parents=exposed_parent_census(transfer))
    assert len(configs) == 20 and len(arrays) == 3  # distinct original initial identities survive even with equal bytes
    assert len({row[0] for row in configs}) == 20
    entry = global_node(transfer, "entry")
    for node, config in configs:
        assert b'"scores"' not in config.canonical_bytes()
        incoming = tuple(row for row in links if row.consumer_node_id == node)
        if config.phase != "entry":
            assert any(row.consumer_input_id == "entry" and row.producer_node_id == entry for row in incoming)
        if config.phase == "point":
            assert {row.consumer_input_id for row in incoming} == set(owner.INPUTS["point"])
            assert not {"source", "history", "initial-state"}.intersection(row.consumer_input_id for row in incoming)
            assert b'"streams"' not in config.canonical_bytes()
        if config.phase == "responses":
            assert any(row.consumer_input_id == "point" and row.producer_node_id.endswith(".point") for row in incoming)
            assert any(row.consumer_input_id == "mechanical" and row.producer_node_id.endswith(".mechanical") for row in incoming)
        if config.phase == "response-score":
            assert {"responses", "response-arrays", "mechanical", "mechanical-arrays", "causal-arrays", "templates"} <= {row.consumer_input_id for row in incoming}
    assert sum(row.consumer_input_id.startswith("readouts.") for row in links) == 2
    assert sum(row.payload_schema == evidence.object_schema for row in external) == 1
    point, = (row for row in external if row.input_id.startswith("external.selected-point-design."))
    assert (point.outcome_access, point.visibility_ceiling) == (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    entry_evidence, = (row for row in external if row.input_id.startswith("external.selected-entry-evidence."))
    assert (entry_evidence.outcome_access, entry_evidence.visibility_ceiling) == (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    assert all(row.outcome_access is OutcomeAccess.OUTCOME_BLIND for row in external if row not in (point, entry_evidence))
    assert set(dict(records)) | set(dict(arrays)) == {row.input_id for row in external} - {"external.selected-entry-evidence." + evidence.object_fingerprint}


def test_confirmation_whole_programme_preserves_two_arms_nomination_join_and_parent_only_opportunity_outcomes(confirmation):
    projection = MatrixSelectedPublicProgramme.from_programme(confirmation)
    assert projection.nomination.original_nomination == confirmation.nomination.identity
    assert projection.roster == confirmation.roster
    assert declarative.allocation(projection) == declarative.allocation(MatrixSelectedPublicProgramme.from_programme(confirmation))
    raw = projection.canonical_bytes()
    assert all(token not in raw for token in (b'"scores"', b'"candidate_results"', b'"actual_error"', b'"absolute_forecast_log_error"'))
    assert decode_canonical_bytes(raw, MatrixSelectedPublicProgramme, maximum_bytes=None) == projection
    evidence = ObjectIdentity("evidence.confirmation.unpublished", owner.MatrixSelectedEntryEvidenceV3.SCHEMA, owner.MatrixSelectedEntryEvidenceV3.VERSION, "a" * 64)
    from tests.test_matrix_e6_transport_assessment import exposed_parent_census
    configs, _, links, _, arrays = owner.contracts(confirmation, evidence, 1,
        produced_input_parents=exposed_parent_census(confirmation))
    assert len(configs) == 20 and len(arrays) == 2
    assert len(confirmation.sources.source_arms()) == 2
    assert len({source.initial for _, source in confirmation.sources.source_arms()}) == 1
    assert sum(row.consumer_input_id.startswith("readouts.") for row in links) == 2
    validate_recursive_scientific_roots(**root_inputs(confirmation))


def test_transfer_reducer_retains_missing_roots_and_original_nearby_shifted_census(transfer):
    manifest, result = assess_selected_programme(transfer, {}, result_id="result.synthetic-selected")
    assert len(manifest.rows) == len(result.cases) == 2
    assert all(row.disposition == "MISSING" for row in result.cases)
    by_id = {row.comparison_id: row for row in result.comparisons}
    assert by_id["e6.nearby"].assigned_group_ids == transfer.point_design.package.allocation.unit_ids("transfer_nearby")
    assert by_id["e6.shifted"].assigned_group_ids == transfer.point_design.package.allocation.unit_ids("transfer_shifted")
    assert all(not row.criterion_met_conditionally for row in result.comparisons)
    assert entry_seal(transfer).source_ids == tuple(sorted(source.source_id for _, source in transfer.sources.source_arms()))
    assert decode_canonical_bytes(transfer.canonical_bytes(), type(transfer), maximum_bytes=None) == transfer


def test_entry_requires_explicit_original_evidence_and_final_cannot_reselect_it(transfer):
    transfer = MatrixSelectedPublicProgramme.from_programme(transfer)
    evidence = ObjectIdentity("evidence.unpublished", owner.MatrixSelectedEntryEvidenceV3.SCHEMA, owner.MatrixSelectedEntryEvidenceV3.VERSION, "a" * 64)
    with pytest.raises(ValueError, match="complete phase"):
        MatrixSelectedProtectedRootConfig("config." + global_node(transfer, "entry"), transfer, "entry")
    for version in ("1.0.0", "2.0.0"):
        with pytest.raises(ValueError, match="installed phase/version"):
            owner.capability_key("entry", version)
    with pytest.raises(ValueError, match="reselect"):
        MatrixSelectedProtectedRootConfig("config." + global_node(transfer, "assess-programme"), transfer, "assess-programme", evidence, 1)
    with pytest.raises(TypeError, match="actual explicit"):
        owner.lower_selected_protected_programme(transfer, root=None, campaign=None, draft_id="draft.synthetic", entry_evidence=object())




def root_inputs(programme):
    """Unpublished qualification descriptors test compiler joins only."""
    base, candidate = candidate_fixture()
    evidence = ObjectIdentity("evidence.unpublished", owner.MatrixSelectedEntryEvidenceV3.SCHEMA, owner.MatrixSelectedEntryEvidenceV3.VERSION, "a" * 64)
    from tests.test_matrix_e6_transport_assessment import exposed_parent_census
    configs, external, links, _, _ = owner.contracts(programme, evidence, 1,
        produced_input_parents=exposed_parent_census(programme))
    declarations = {(row.capability_key, row.capability_version): row for row in owner.operation_declarations()}
    registrations, inputs = {}, []
    for node, config in configs:
        version = owner.config_capability_version(config)
        registration = declarations[owner.capability_key(config.phase, version), version].registration()
        registrations[node] = registration
        operation = RecursiveOperationSpec.from_config(node_id=node, selection=registration.selection, config_id=config.config_id,
            config=config, obligation_ids=("obligation." + node,), resource_budget=owner.preparation.BUDGET)
        inputs.append(decode_recursive_config_input(operation, registration))
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.sources.source_arms()}))
    world = replace(base.system.world, kind=WorldKind.NUMERICAL_SIMULATOR, unrepresented_physics=("unrepresented.synthetic-matrix",))
    design = tuple(replace(base.design_inputs[0], input_id="design." + pin.object_id, object_identity=pin,
        materialization_sha256=pin.object_fingerprint) for pin in (programme.identity, programme.point_design.package.identity, programme.sources.closure.identity))
    materializations, qualifications = [], []
    for item in external:
        if item.scientific_role == "HISTORY":
            continue
        pin = ObjectIdentity(item.logical_artifact_id, item.payload_schema, "1.0.0", item.expected_content_sha256)
        qualification = replace(candidate.qualifications[0], receipt_id="qualification." + item.input_id, source_id=item.input_id,
            materialization=pin, content_sha256=item.expected_content_sha256, evidence_world_id=world.world_id,
            observation_operator=programme.assay.identity, outcome_access=item.outcome_access, visibility_ceiling=item.visibility_ceiling)
        qualifications.append(qualification)
        materializations.append(replace(base.source_materializations[0], source_id=item.input_id, evidence_world_id=world.world_id,
            materialization=pin, content_sha256=item.expected_content_sha256, observation_operator=qualification.observation_operator,
            numerical_view_ids=qualification.numerical_view_ids, qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification),
            access_disposition=SourceAccessDisposition.VERIFIED_ACCESS))
    root = replace(base, system=replace(base.system, world=world), evaluation_unit_ids=groups, design_inputs=tuple(sorted(design, key=lambda row: row.input_id)),
        design_origin=replace(base.design_origin, declared_input_ids=tuple(sorted(row.input_id for row in design))),
        source_materializations=tuple(materializations))
    return dict(root=root, config_inputs=tuple(inputs), registrations_for_node=registrations, requirements=(), connections=(),
        qualifications=tuple(qualifications), known_design_inputs=root.design_inputs, links=links, external_inputs=external)


def test_actual_root_validator_accepts_complete_typed_graph_and_rejects_thinned_entry_or_future_dependencies(transfer):
    arguments = root_inputs(transfer)
    validate_recursive_scientific_roots(**arguments)
    histories = tuple(value for value in arguments["external_inputs"] if value.scientific_role == "HISTORY")
    sources = {value.input_id for value in arguments["external_inputs"] if value.scientific_role == "SOURCE"}
    assert histories and all(value.outcome_access is OutcomeAccess.EVALUATION_REVEALED for value in histories)
    assert {value.source_id for value in arguments["root"].source_materializations} == sources
    assert {value.source_id for value in arguments["qualifications"]} == sources
    materialization = arguments["root"].source_materializations[0]
    changed_root = replace(arguments["root"], source_materializations=tuple(sorted(
        (*arguments["root"].source_materializations, replace(materialization, source_id=histories[0].input_id)),
        key=lambda value: value.source_id)))
    with pytest.raises(ValueError, match="qualification roster"):
        validate_recursive_scientific_roots(**{**arguments, "root": changed_root})
    for name in ("entry", "point", "responses", "readouts"):
        selected = next(row for row in arguments["links"] if row.consumer_input_id == name or row.consumer_input_id.startswith(name + "."))
        changed = tuple(row for row in arguments["links"] if row is not selected)
        with pytest.raises(ValueError, match="census"):
            validate_recursive_scientific_roots(**{**arguments, "links": changed})
    qualification = arguments["qualifications"][0]
    with pytest.raises(ValueError, match="qualification"):
        validate_recursive_scientific_roots(**{**arguments, "qualifications": tuple(row for row in arguments["qualifications"] if row is not qualification)})
