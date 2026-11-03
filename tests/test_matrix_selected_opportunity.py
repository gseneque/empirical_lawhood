# SPDX-License-Identifier: MPL-2.0
"""In-memory opportunity controls; synthetic locators establish no authority.

These controls read retained fixtures and construct literal numerical records.
They write no publication, acquire no trajectory and enter no native process.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as declarative

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_experiment import MatrixPreparationSourceBank
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationArrays, MatrixPreparationSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import MatrixPreparedMechanicalForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedForecastArrays, MatrixPreparedResponsePanel, MatrixPreparedResponseReadout
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointDesign, forecast_selected_point
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedNominationSelection
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import assess_selected_programme
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS, identity as model_identity
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell, branch_census
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, validate_recursive_scientific_roots
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_sampling_follow_on import prior_product
from tests.test_matrix_selected_package import reference
from tests.test_matrix_selected_point import selected_design, feature
from tests.test_matrix_selected_protected import transfer, confirmation, unpublished  # noqa: F401 - shared in-memory fixture


def opportunity_from_transfer(base_programme, groups=1, group_ids=None):
    template = selected_design("E5_OPPORTUNITY")
    closure = base_programme.sources.closure
    sample = closure.reservation.allocation.roots[0]
    coordinate, policy = template.sources[0][1].original.coordinate, template.sources[0][1].original.policy
    roots = []
    for index in range(groups):
        name = f"group.opportunity.exposed.{index:03}" if group_ids is None else group_ids[index]
        roots.append(replace(sample, root=replace(sample.root, root_id="root." + name, independent_group_id=name,
            regime_id="regime.opportunity.exposed", role=original.MatrixProgrammeRole.DEVELOPMENT,
            coordinate_id=coordinate.coordinate_id, clock_id=coordinate.clock_id), coordinate=original.coordinate_identity(coordinate),
            streams=tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_OPPORTUNITY." + name + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
    scope = original.ScheduledMatchedScope("scope.opportunity.exposed", original.MatrixProgrammeRole.DEVELOPMENT,
        tuple(row.root.independent_group_id for row in roots), (original.coordinate_identity(coordinate),),
        "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU")
    allocation = replace(closure.reservation.allocation, allocation_id="allocation.opportunity.exposed", coordinates=(coordinate,), roots=tuple(roots), matched_scopes=(scope,))
    reservation = original.ScheduledReservation("reservation.opportunity.exposed", allocation, unpublished(allocation, "allocation.opportunity.exposed"))
    selection = original.ScheduledSelection("selection.opportunity.exposed", original.identity(reservation), closure.specification.selection.numerical_design,
        (policy,), ((original.coordinate_identity(coordinate), original.identity(policy)),))
    specification = original.ScheduledSpecification("specification.opportunity.exposed", selection, unpublished(selection, "selection.opportunity.exposed"))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=closure.provenances)
    sources, panels = [], []
    for root in roots:
        subject = source_index.resolve(source_index.reference(source_id="original." + root.root.root_id,
            root_id=root.root.root_id, provenance=closure.provenances[0].identity))
        initial = replace(closure.initial_states[0][1], state_id="initial." + root.root.root_id)
        for arm, recipe in template.arms:
            sources.append(MatrixPreparationSource("prepared." + root.root.root_id + "." + arm, ScheduledPublicSource.from_source(subject), root,
                initial, recipe, subject.provenance, subject.numerical_design))
        group = root.root.independent_group_id
        pair = tuple(MatrixPreparedResponsePanel("panel." + group + "." + str(index), group, role, root.streams if index == 0 else
            tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_OPPORTUNITY_FUTURE." + group + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
            for index, role in enumerate(("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")))
        panels.append((group, pair))
    sources = tuple(sorted(sources, key=lambda row: row.source_id))
    bank = MatrixPreparationSourceBank("sources.opportunity.exposed", (allocation,), sources)
    arm_by_recipe = {recipe.identity: arm for arm, recipe in template.arms}
    design = MatrixSelectedPointDesign("design.opportunity.exposed", base_programme.point_design.package, "E5_OPPORTUNITY", groups, template.arms,
        tuple((arm_by_recipe[source.recipe.identity], MatrixPreparedPublicSource.from_source(source)) for source in sources), template.interpretations)
    return science.MatrixSelectedOpportunityProgramme("programme.opportunity.exposed", bank, reservation, design, base_programme.assay,
        tuple(panels), base_programme.criterion, 1, "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")


@pytest.fixture(scope="module")
def opportunity(transfer):  # noqa: F811
    return opportunity_from_transfer(transfer)


def evidence_for(programme):
    value = programme.point_design.package
    pins = (science.identity(value.models), science.identity(value.model_freeze), science.calibration_identity(value), science.identity(value.calibrated_freeze))
    products = []
    for pin in sorted(pins, key=lambda row: row.object_id):
        prior = prior_product(pin)
        products.append(MatrixSelectedOriginalProduct(prior.prior_execution, prior.reveal_authority))
    return science.MatrixSelectedOpportunityEvidence("evidence.opportunity.exposed", programme.identity, tuple(products))


def literal_observations(programme, *, hold_error=D(".9"), fixed_error=D(".01")):
    protected = type(programme) in (MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme)
    programme = (MatrixSelectedPublicProgramme.from_programme(programme) if type(programme) is MatrixSelectedProtectedProgramme else programme) if protected else science.public_programme(programme)
    sources = tuple(source for _, source in programme.sources.source_arms()) if protected else programme.sources.sources
    hold_arm = programme.sources.hold_arm_id if protected else programme.hold_arm_id
    result = {}
    for case in programme.roster.cases:
        source = next(row for row in sources if "case." + row.source_id == case.case_id)
        public_source = MatrixPreparedPublicSource.from_source(source)
        observed = feature(programme.point_design, public_source)
        point = forecast_selected_point(programme.point_design, observed, record_id="point." + source.source_id)
        protocol, panels = programme.protocol(source), dict(programme.panels)[case.unit_id]
        protocol_pin = ObjectIdentity.from_record(protocol.protocol_id, protocol)
        preparation = reference("preparation." + source.source_id, MatrixPreparationArrays)
        operand = MatrixPreparedForecastArrays("forecast." + source.source_id, source.identity, preparation, protocol_pin,
            ArtifactIdentity("array.forecast." + source.source_id, "literal-in-memory", MATRIX_ARRAY_SCHEMA, "c" * 64, "application/x-npz", 1),
            (MatrixArrayMember("literal", "<f8", (1,), "d" * 64),))
        mechanical = MatrixPreparedMechanicalForecast("mechanical." + source.source_id, source.identity, observed.prefix, protocol_pin,
            model_identity(protocol.mechanical_model), operand, "AVAILABLE",
            tuple((view, predictor, "AVAILABLE", None) for view in ("PRIMARY", "FINE") for predictor in PREDICTORS))
        error = hold_error if case.arm_id == hold_arm else fixed_error
        cells = tuple(sorted((ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
            (D(0),) * 48, (error,) * 48, (error,) * 48, (None,) * 48, error)
            for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions for predictor in PREDICTORS
            for horizon in protocol.horizon_steps), key=lambda row: row.key))
        controls = tuple(ScheduledResponseTransitionControl("control.prepared." + source.source_id + "." + branch,
            "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), protocol.native_reference_tolerance, "SATISFIED",
            (1 if view == "PRIMARY" else 2) * 128, 192, (D(0),) * ((1 if view == "PRIMARY" else 2) * 128), ())
            for branch, view, *_ in branch_census(protocol, panels))
        with localcontext() as context:
            context.prec = 50
            cumulative = ((D(1) + error).ln(),) * 15
        readout = MatrixPreparedResponseReadout("readout." + source.source_id, source.identity, preparation, operand.identity,
            protocol_pin, tuple(panel.identity for panel in panels), controls, cells, True, "FINITE", cumulative)
        result[case.case_id] = point, mechanical, readout
    return result



def committed_evidence_for(programme):
    """Current unpublished entry shape; no producer custody or qualification."""
    from tests.matrix_selected_commitment_fixture import unpublished_committed_evidence
    from tests.test_matrix_selected_declarative_preparation import disclosed_produced_parents
    evidence = unpublished_committed_evidence(evidence_for(programme))
    return evidence, disclosed_produced_parents(evidence.upstream_products)


def test_selected_opportunity_public_projection_replays_original_pins_without_calibration_scores(opportunity):
    projection = science.public_programme(opportunity)
    assert projection.original_programme == opportunity.identity and projection.roster == opportunity.roster
    assert projection.point_design.original_design == opportunity.point_design.identity
    assert declarative.allocation(projection) == declarative.allocation(science.public_programme(opportunity))
    assert b'"scores"' not in projection.canonical_bytes()
    assert projection.identity != opportunity.identity
    assert decode_canonical_bytes(projection.canonical_bytes(), type(projection), maximum_bytes=None) == projection
    evidence = evidence_for(opportunity)
    science.validate_opportunity_evidence(evidence, projection)
    with pytest.raises(ValueError, match="ancestry"):
        science.validate_opportunity_evidence(replace(evidence, programme=replace(evidence.programme, object_fingerprint="f" * 64)), projection)


def test_selected_opportunity_nomination_uses_actual_selected_points_and_complete_original_endpoint(opportunity):
    observations = literal_observations(opportunity)
    manifest, result = science.nominate_selected_opportunity(opportunity, observations, result_id="nomination.literal-selected-opportunity")
    assert result.disposition == "NOMINATED" and result.selected_arm_id == "fixed-a"
    assert result.package == opportunity.point_design.package.identity
    assert result.specification == opportunity.identity and result.roster == opportunity.roster.identity
    assert len(result.cases) == len(manifest.rows) == 3
    assert all(row.disposition == "FINITE" and row.error_upper is None and not row.conditional_admission and row.covered is None for row in result.cases)
    assert all(row.absolute_comparator_log_error is not None and row.source_support == "UNESTABLISHED" for row in result.cases)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    point, mechanical, readout = next(iter(observations.values()))
    key = next(iter(observations))
    changed = {**observations, key: (replace(point, package=replace(point.package, object_fingerprint="f" * 64)), mechanical, readout)}
    with pytest.raises(ValueError, match="forecasts"):
        science.nominate_selected_opportunity(opportunity, changed, result_id="nomination.foreign")


def test_selected_opportunity_no_headroom_and_missing_case_retain_negative_complete_denominators(opportunity):
    observations = literal_observations(opportunity, hold_error=D(".01"))
    _, result = science.nominate_selected_opportunity(opportunity, observations, result_id="nomination.no-headroom")
    assert result.disposition == "NONDISCRIMINATING_OPPORTUNITY" and result.selected_recipe is None and not result.recoverable_unit_ids
    assert len(result.cases) == 3
    with pytest.raises(TypeError, match="successful nomination"):
        MatrixSelectedNominationSelection.from_nomination(result)
    del observations[next(iter(observations))]
    manifest, missing = science.nominate_selected_opportunity(opportunity, observations, result_id="nomination.missing")
    assert missing.disposition == "UNEVALUABLE_OPPORTUNITY" and len(missing.cases) == 3
    assert sum(row.disposition == "MISSING" for row in missing.cases) == 1
    assert sum(row[1:] == (None, None, None) for row in manifest.rows) == 1


def test_selected_opportunity_preserves_original_transfer_reserves_and_explicit_recovery_threshold(transfer, opportunity):  # noqa: F811
    reserved = transfer.point_design.package.allocation.unit_ids("transfer_nearby")[:1]
    with pytest.raises(ValueError, match="transfer-reserved"):
        opportunity_from_transfer(transfer, group_ids=reserved)
    frozen = replace(opportunity, minimum_recoverable_groups=2)
    _, result = science.nominate_selected_opportunity(frozen, literal_observations(opportunity), result_id="nomination.explicit-threshold")
    assert len(result.recoverable_unit_ids) == 1 and result.disposition == "NONDISCRIMINATING_OPPORTUNITY"


def test_selected_opportunity_complete16x3_graph_preserves_native_prediction_and_future_denominators(transfer):  # noqa: F811
    programme = opportunity_from_transfer(transfer, groups=16)
    evidence, parents = committed_evidence_for(programme)
    configs, external, links, records, arrays = owner.contracts(programme, evidence.identity, len(evidence.canonical_bytes()),
        produced_input_parents=parents)
    assert len(configs) == 434 and len(programme.roster.cases) == 48
    assert len(arrays) == 2  # one genuinely shared matched-state identity plus the fixed assay templates
    assert sum(config.phase in owner.NATIVE for _, config in configs) == 96
    assert sum(1 + (config.phase in owner.ARRAY_OUTPUTS) + (config.phase == "nominate") for _, config in configs) == 675
    design = owner.global_node(programme, "design")
    for node, config in configs:
        assert b'"scores"' not in config.canonical_bytes()
        incoming = tuple(row for row in links if row.consumer_node_id == node)
        if config.phase != "design":
            assert any(row.consumer_input_id == "design" and row.producer_node_id == design for row in incoming)
        if config.phase == "point":
            assert not {"source", "initial-state", "history"}.intersection(row.consumer_input_id for row in incoming)
            assert b'"streams"' not in config.canonical_bytes()
        if config.phase == "responses":
            assert {"point", "mechanical"} <= {row.consumer_input_id for row in incoming}
    point, = (row for row in external if row.input_id.startswith("external.selected-opportunity-point."))
    assert (point.outcome_access, point.visibility_ceiling) == (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    entry_evidence, = (row for row in external if row.input_id.startswith("external.selected-opportunity-evidence."))
    assert (entry_evidence.outcome_access, entry_evidence.visibility_ceiling) == (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    assert all(row.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE and row.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
        for row in external if row not in (point, entry_evidence))
    assert set(dict(records)) | set(dict(arrays)) == {row.input_id for row in external} - {"external.selected-opportunity-evidence." + evidence.fingerprint()}
    manifest, missing = science.nominate_selected_opportunity(programme, {}, result_id="nomination.complete16x3-missing")
    assert len(missing.development_unit_ids) == 16 and len(missing.cases) == len(manifest.rows) == 48
    assert missing.disposition == "UNEVALUABLE_OPPORTUNITY"


def compiler_inputs(programme):
    evidence, parents = committed_evidence_for(programme)
    lowered = owner.lower_selected_opportunity(programme, evidence=evidence, campaign=campaign_fixture()[0].campaign,
        draft_id="draft.opportunity.exposed", produced_input_parents=parents)
    declarations = {row.registration().selection: row for row in owner.operation_declarations()}
    registrations, configs = {}, []
    for operation in lowered.draft.operations:
        registration = declarations[operation.selection].registration()
        registrations[operation.node_id] = registration
        configs.append(decode_recursive_config_input(operation, registration))
    return dict(root=lowered.draft.development_study, config_inputs=tuple(configs), registrations_for_node=registrations,
        requirements=(), connections=(), qualifications=(), known_design_inputs=(), links=lowered.draft.links, external_inputs=lowered.draft.external_inputs)


def test_actual_opportunity_root_refuses_thinned_future_or_nomination_graph(opportunity):
    arguments = compiler_inputs(opportunity)
    validate_recursive_scientific_roots(**arguments)
    for name in ("design", "point", "responses", "readouts"):
        edge = next(row for row in arguments["links"] if row.consumer_input_id == name or row.consumer_input_id.startswith(name + "."))
        with pytest.raises(ValueError, match="graph"):
            validate_recursive_scientific_roots(**{**arguments, "links": tuple(row for row in arguments["links"] if row is not edge)})


def test_opportunity_declarations_require_current_parent_custody_with_only_actual_native_phases():
    declarations = owner.operation_declarations()
    roster = {(row.capability_key, row.capability_version) for row in declarations}
    expected = ({(owner.capability_key(phase), "1.0.0") for phase in owner.PHASES if phase not in ("design", *owner.NATIVE)}
        | {(owner.COMMITTED_DESIGN_KEY, "2.0.0")}
        | {(owner.capability_key(phase, "2.0.0"), "2.0.0") for phase in ("history", "responses")})
    assert len(declarations) == len(roster) == 11 and roster == expected
    assert {(row.runner_factory().phase, row.capability_version) for row in declarations
        if row.registration().native_effect} == {("history", "2.0.0"), ("responses", "2.0.0")}
    for phase in owner.NATIVE:
        with pytest.raises(ValueError, match="installed phase/version"):
            owner.capability_key(phase)
        with pytest.raises(ValueError, match="current direct-input"):
            owner.phase_inputs(phase)
    for declaration in declarations:
        runner = declaration.runner_factory()
        phase = runner.phase
        assert callable(runner.execute_with_native_subwork) == (phase in owner.NATIVE)
        assert declaration.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
        assert declaration.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        assert declaration.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
        assert declaration.execution_properties.runner_preparation_factory is owner.prepare_for_invocation
        with pytest.raises(PermissionError, match="custody"):
            owner.prepare_for_invocation(object(), runner)






@pytest.mark.parametrize("phase", ("confirmation", "transfer"))
def test_actual_finite_protected_endpoint_reuses_original_forecast_array_identity(confirmation, transfer, phase):  # noqa: F811
    programme = confirmation if phase == "confirmation" else transfer
    observations = literal_observations(programme)
    _, result = assess_selected_programme(programme, observations, result_id="result.finite-protected." + phase)
    assert len(result.cases) == 2 and all(row.disposition == "FINITE" for row in result.cases)
    assert all(row.error_upper is None and row.absolute_comparator_log_error is not None for row in result.cases)
    assert not any(row.conditional_admission for row in result.cases)
    key = next(iter(observations))
    point, mechanical, readout = observations[key]
    altered = {**observations, key: (point, mechanical, replace(readout, forecast=replace(readout.forecast, object_fingerprint="f" * 64)))}
    with pytest.raises(ValueError, match="physical prediction"):
        assess_selected_programme(programme, altered, result_id="result.changed-protected." + phase)
