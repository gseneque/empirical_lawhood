# SPDX-License-Identifier: MPL-2.0
"""Disclosed protected-role metadata and literal endpoints; no fresh science.

The main predictor here is the genuine old frozen ScheduledForecastDesign.
This fixture does not bridge a newly selected protected E3 model into E5/E6.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import protected_functional as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme.functional_outcome_reduction import _nominate_functional_cases
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_functional import MatrixPreparedFunctionalObservation, MatrixPreparedFunctionalSpecification
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPointFeature, MatrixPreparedRecipeInterpretation, forecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedPrefixArrays
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponsePanel
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_point import MatrixPreparedComparatorMethod, forecast_comparator
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import MatrixConfirmationSources, MatrixProtectedSourceClosure, MatrixReservedTransferSources
from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import PACKAGE_ROLES, MatrixFrozenConsumerPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixFunctionalCaseResult
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, identity as model_identity
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import STRATA
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole as Role
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from tests import test_matrix_coupling_preparation as preparation
from tests import test_matrix_prepared_functional as endpoint_fixture
from tests import test_matrix_scheduled_history as scheduled
from tests import test_matrix_scheduled_history_bindings as bindings
from tests.test_matrix_factor_confirmation_eligibility import publish, stock
from tests.test_matrix_later_programme import criterion, ref
from tests.test_matrix_parameter_history import source as parameter_template


def selected(tmp_path, phase):
    plane, prior = stock.__wrapped__(tmp_path, parameter_template().provenance)
    _, old = scheduled.scheduled.__wrapped__((plane, prior))
    # NEW explicit test source records, published before constructing any source.
    # Extend the original clock to the complete128-step future. Split reserve
    # populations into genuinely distinct declared groups/streams in this toy.
    allocation = old[0].allocation
    coordinates = tuple(replace(row, autonomous_ticks=row.autonomous_ticks + 128,
        observation_ticks=tuple(range(row.total_ticks + 129))) for row in allocation.coordinates)
    by_id = {row.coordinate_id: row for row in coordinates}
    roots = []
    for index, row in enumerate(allocation.roots):
        root = row.root
        streams = row.streams
        if root.role is Role.WITHHELD_TRANSFER:
            root = replace(root, independent_group_id="group.disclosed-reserve." + str(index))
            streams = tuple(MatrixHistorySeed(purpose, sha256((root.independent_group_id + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)
        roots.append(replace(row, root=root, coordinate=original.coordinate_identity(by_id[root.coordinate_id]), streams=streams))
    scopes = tuple(replace(row, coordinates=tuple(original.coordinate_identity(by_id[value.object_id]) for value in row.coordinates))
        for row in allocation.matched_scopes if row.role is not Role.WITHHELD_TRANSFER)
    scopes += tuple(original.ScheduledMatchedScope("scope.disclosed-reserve." + str(index), Role.WITHHELD_TRANSFER,
        (row.root.independent_group_id,), (row.coordinate,), scheduled.CONSTRUCTION)
        for index, row in enumerate(roots) if row.root.role is Role.WITHHELD_TRANSFER)
    allocation = replace(allocation, allocation_id="allocation.disclosed-protected", coordinates=coordinates, roots=tuple(roots),
        matched_scopes=tuple(sorted(scopes, key=lambda row: row.scope_id)))
    reservation = replace(old[0].reservation, reservation_id="reservation.disclosed-protected", allocation=allocation,
        publication=publish(plane, allocation, "published.disclosed-protected-allocation"))
    selection = replace(old[0].specification.selection, selection_id="selection.disclosed-protected", reservation=original.identity(reservation),
        coordinate_policies=tuple((original.coordinate_identity(row), original.identity(old[0].policy)) for row in coordinates))
    specification = replace(old[0].specification, specification_id="specification.disclosed-protected", selection=selection,
        publication=publish(plane, selection, "published.disclosed-protected-selection"))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=(old[0].provenance,))
    references = tuple(index.reference(source_id="source." + row.root.root_id, root_id=row.root.root_id,
        provenance=old[0].provenance.identity) for row in roots)
    subjects = tuple(index.resolve(reference) for reference in references)
    plane, subjects, config = bindings.bank.__wrapped__((plane, subjects))
    role = Role.CONFIRMATION if phase == "E5_CONFIRMATION" else Role.WITHHELD_TRANSFER
    originals = tuple(row for row in subjects if row.root.root.role is role)
    if role is Role.CONFIRMATION:
        originals = originals[:1]
    prepared = tuple(preparation.selected.__wrapped__((None, row))[0] for row in originals)
    closure = MatrixProtectedSourceClosure("closure.disclosed-protected", originals[0].reservation, originals[0].specification,
        (originals[0].provenance,), tuple(row.reference for row in originals), config.audit, config.audit_publication,
        tuple((row.root_id, source.initial) for row, source in zip(originals, prepared, strict=True)), ref("numerical-scope.disclosed-protected"))
    hold = replace(prepared[0].recipe, recipe_id="recipe.disclosed.hold", kind="HOLD",
        half_tick_couplings=(prepared[0].initial.alpha_tilde,) * len(prepared[0].recipe.half_tick_couplings))
    if phase == "E5_CONFIRMATION":
        sources = MatrixConfirmationSources("sources.disclosed-confirmation", closure, (("hold", hold), ("recipe-a", prepared[0].recipe)), "hold")
    else:
        recipes = tuple((source.root.coordinate, replace(hold, recipe_id="recipe.disclosed.hold." + str(index),
            half_tick_couplings=(source.initial.alpha_tilde,) * len(hold.half_tick_couplings))) for index, source in enumerate(prepared))
        sources = MatrixReservedTransferSources("sources.disclosed-transfer", closure, recipes, "hold")
    frozen = config.forecast_design
    package = MatrixFrozenConsumerPackage("package.disclosed-protected", ref("freeze.disclosed-original"),
        tuple((name, frozen.model if name in ("model", "comparator") else frozen.criterion if name == "criterion" else ref("component.disclosed." + name)) for name in PACKAGE_ROLES),
        original.identity(closure.reservation), tuple(sorted({row[1] for row in frozen.training_record.roles.rows if row[3] == "TRAIN"})),
        ("group.disclosed-original-selection",), "OBSERVATION_ASSISTED_SEALED_BEFORE_FUTURE")
    comparator = MatrixPreparedComparatorMethod("comparator.disclosed-protected", package.identity, package.upstream_freeze,
        frozen.model_record, frozen.model_record.method, frozen.training_spec, package.training_unit_ids, package.component("preprocessing"), frozen.training_record)
    literal = endpoint_fixture.endpoint.__wrapped__()
    assay = MatrixPreparedAssayMethod.from_protocol("assay.disclosed-protected", replace(literal[4], criterion=frozen.criterion,
        actions=tuple(sorted((MatrixFactorAction("action.disclosed." + row.role.lower(), row.role, row.amplitude,
            row.pulse_steps, row.force_norm) for row in frozen.criterion_record.action_scales), key=lambda row: row.action_id)),
        receiver_gram_tolerance=frozen.criterion_record.receiver_gram_tolerance))
    functional = replace(criterion(1), effort_unit=hold.effort_unit)
    nomination = publication = receipt = None
    if phase == "E5_CONFIRMATION":
        recipes = (("hold", hold.identity), ("recipe-a", prepared[0].recipe.identity), ("recipe-b", ref("recipe.disclosed-b", hold.SCHEMA)))
        rows = tuple(MatrixFunctionalCaseResult("case.disclosed-dev." + arm, "group.disclosed-dev", arm,
            "FINITE", D(".1") if arm == "hold" else D(".01"), None, None, arm != "hold", False, None, False, D(0), ()) for arm, _ in recipes)
        nomination = _nominate_functional_cases(result_id="nomination.disclosed-opportunity", specification_identity=ref("spec.disclosed-opportunity", MatrixPreparedFunctionalSpecification.SCHEMA),
            package_identity=package.identity, roster_identity=ref("roster.disclosed-opportunity"), evidence_identity=ref("manifest.disclosed-opportunity"),
            group_ids=("group.disclosed-dev",), arm_ids=tuple(arm for arm, _ in recipes), hold_arm_id="hold", criterion=functional,
            minimum_recoverable_groups=1, tie_policy="LEXICAL_ARM_ID", recipes=recipes, cases=rows)
        publication = plane.write(ArtifactWriteRequest("nomination.disclosed-opportunity", "outputs/nomination.json", nomination.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "publication.disclosed-nomination", "outputs", nomination.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        receipt = CanonicalTaskReceipt("receipt.disclosed-nomination", "run.disclosed-opportunity", "task.disclosed-opportunity", "attempt.disclosed-opportunity",
            originals[0].provenance.observed_git_head, (), (publication.materialization,), (publication.logical,), (), OperationalStatus.SUCCEEDED, ())
        spec = method.MatrixPreparationConfirmationSpecification("experiment.disclosed-confirmation", "Frozen recipe versus HOLD on distinct CONF groups",
            sources.identity, package.identity, comparator.identity, assay.identity, functional, 1, "hold", "recipe-a", nomination.identity, "LEXICAL_ARM_ID")
    else:
        regimes = tuple(source.root.root.regime_id for source in prepared)
        spec = method.MatrixReservedTransferSpecification("experiment.disclosed-transfer", "Original untouched regimes, separately assessed",
            sources.identity, package.identity, comparator.identity, assay.identity, functional, 1, "hold", regimes,
            ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN"))
    interpretations = tuple(MatrixPreparedRecipeInterpretation(recipe.identity, STRATA[1], ref("premise.disclosed." + recipe.recipe_id))
        for recipe in sorted({source.recipe for _, source in sources.source_arms()}, key=lambda row: row.recipe_id))
    groups = {source.root.root.independent_group_id: source for _, source in sources.source_arms()}
    panels = tuple((group, tuple(MatrixPreparedResponsePanel("panel.disclosed." + group + "." + role.lower(), group, role,
        source.root.streams if role == "COMMON_NOISE_PANEL" else tuple(MatrixHistorySeed(purpose, sha256(("INDEPENDENT." + group + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
        for role in ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"))) for group, source in sorted(groups.items()))
    return method.MatrixProtectedFunctionalSelection("selection.disclosed-protected", spec, sources, package, frozen, interpretations,
        comparator, assay, panels, nomination, publication, receipt)


def observations(selection):
    result = {}
    original_observation = endpoint_fixture.endpoint.__wrapped__()[-1]
    point_design = selection.point_design
    sources = {"case." + source.source_id: source for _, source in selection.sources.source_arms()}
    for case in selection.roster.cases:
        source, protocol = sources[case.case_id], selection.protocol(sources[case.case_id])
        key = source.source_id
        preparation = replace(original_observation.mechanical.arrays.preparation, object_id="preparation." + key)
        causal_arrays = MatrixPreparedPrefixArrays("arrays.causal." + key, source.identity, "CAUSAL_STATE",
            original_observation.mechanical.arrays.array_artifact, original_observation.mechanical.arrays.members, (source.identity,))
        causal = MatrixPreparedCausalPrefix("prefix." + key, source.identity, preparation,
            ref("numerical." + key, "empirical-lawhood/matrix-experimental-programme/preparation-assessment"),
            ref("witness." + key, "empirical-lawhood/matrix-experimental-programme/prepared-factor-witness"),
            ref("frames." + key, "empirical-lawhood/matrix-experimental-programme/prepared-frame-assessment"),
            original.identity(source.original.policy), source.total_ticks, "a" * 64, "AVAILABLE", None, causal_arrays)
        prefix = ObjectIdentity.from_record(causal.record_id, causal)
        feature = MatrixPreparedPointFeature("feature." + key, source.identity, prefix, point_design.identity,
            source.root.root.root_id, case.unit_id, point_design.family(next(row for row in point_design.sources if row.source == source.identity)),
            source.root.root.clock_id, source.duration, causal.frame_sha256, "AVAILABLE", tuple((name, D(0)) for name in FEATURES))
        public = next(row for row in point_design.sources if row.source == source.identity)
        # Actual unchanged frozen point and comparator arithmetic on one feature.
        point = forecast(point_design, public, causal, feature, record_id="point." + key)
        comparator = forecast_comparator(selection.comparator, selection.package, feature, record_id="comparator." + key)
        protocol_id = ObjectIdentity.from_record(protocol.protocol_id, protocol)
        arrays = replace(original_observation.mechanical.arrays, forecast_id="forecast." + key, source=source.identity,
            preparation=preparation, original_protocol=protocol_id)
        mechanical = replace(original_observation.mechanical, record_id="mechanical." + key, source=source.identity,
            causal=prefix, original_protocol=protocol_id, mechanical_model=model_identity(protocol.mechanical_model), arrays=arrays)
        panels = dict(selection.future_panels)[case.unit_id]
        cells = tuple(sorted((replace(original_observation.readout.cells[0], view=view, panel_id=panel.panel_id,
            action_id=action.action_id, predictor=predictor, horizon_tick=horizon)
            for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
            for predictor in protocol.mechanical_model.predictors for horizon in protocol.horizon_steps), key=lambda row: row.key))
        controls = tuple(replace(original_observation.readout.controls[0], control_id="control.prepared." + key + "." + branch,
            denominator_steps=(1 if view == "PRIMARY" else 2) * 128,
            measured_errors=(D(0),) * ((1 if view == "PRIMARY" else 2) * 128)) for branch, view, *_ in branch_census(protocol, panels))
        with localcontext() as context:
            context.prec = 50
            cumulative = ((D(1) + D(".01")).ln(),) * 15
        readout = replace(original_observation.readout, record_id="readout." + key, source=source.identity, preparation=preparation,
            forecast=arrays.identity, original_protocol=protocol_id, panels=tuple(panel.identity for panel in panels), cells=cells,
            controls=controls, cumulative_log_errors=cumulative)
        result[case.case_id] = MatrixPreparedFunctionalObservation(case.case_id, point, mechanical, readout, comparator)
    return result


@pytest.mark.parametrize("phase", ("E5_CONFIRMATION", "E6_TRANSFER"))
def test_separate_protected_specification_preserves_complete_missing_and_finite_census(tmp_path, phase):
    selected_input = selected(tmp_path, phase)
    assert decode_canonical_bytes(selected_input.canonical_bytes(), method.MatrixProtectedFunctionalSelection, maximum_bytes=None) == selected_input
    manifest, result = method.assess_protected_functional(selected_input, {}, result_id="result.disclosed-missing")
    assert len(result.cases) == len(manifest.rows) == 2 and all(row.disposition == "MISSING" for row in result.cases)
    assert len(result.comparisons) == (1 if phase == "E5_CONFIRMATION" else 2)
    assert all(row.missing_group_ids == row.assigned_group_ids and row.successes == 0 for row in result.comparisons)
    received = observations(selected_input)
    manifest, result = method.assess_protected_functional(selected_input, received, result_id="result.disclosed-finite")
    assert all(row.disposition == "FINITE" and row.absolute_comparator_log_error == row.absolute_forecast_log_error for row in result.cases)
    assert all(row.error_upper is None and not row.conditional_admission and row.source_support == "UNESTABLISHED" for row in result.cases)
    assert all(row[4] is not None for row in manifest.rows)
    assert all(not row.criterion_met_conditionally for row in result.comparisons)


@pytest.mark.parametrize("damage", ("nomination-receipt", "nomination-bytes", "assay", "panel", "case", "comparator", "comparator-feature", "mechanical", "receiver", "control"))
def test_protected_consumer_refuses_substituted_original_selection_or_actual_products(tmp_path, damage):
    chosen = selected(tmp_path, "E5_CONFIRMATION")
    with pytest.raises((TypeError, ValueError)):
        if damage == "nomination-receipt":
            replace(chosen, nomination_receipt=replace(chosen.nomination_receipt, operational_status=OperationalStatus.FAILED, reason_codes=("DISCLOSED_FAILURE",)))
        elif damage == "nomination-bytes":
            replace(chosen, nomination_publication=replace(chosen.nomination_publication,
                logical=replace(chosen.nomination_publication.logical, content_sha256="f" * 64)))
        elif damage == "assay":
            altered = replace(chosen.assay_method, actions=tuple(replace(row, amplitude=row.amplitude * 2) for row in chosen.assay_method.actions))
            replace(chosen, assay_method=altered, specification=replace(chosen.specification, assay_method=altered.identity))
        elif damage == "panel":
            replace(chosen, future_panels=chosen.future_panels[:-1])
        else:
            received = observations(chosen)
            case_id = next(iter(received))
            value = received[case_id]
            if damage == "case":
                received["case.unassigned"] = value
            elif damage == "comparator":
                received[case_id] = replace(value, comparator=None)
            elif damage == "comparator-feature":
                received[case_id] = replace(value, comparator=replace(value.comparator,
                    feature=replace(value.comparator.feature, design=replace(value.comparator.feature.design, object_fingerprint="f" * 64))))
            elif damage == "mechanical":
                received[case_id] = replace(value, mechanical=replace(value.mechanical, mechanical_model=replace(value.mechanical.mechanical_model, object_fingerprint="f" * 64)))
            elif damage == "receiver":
                first = value.readout.cells[0]
                received[case_id] = replace(value, readout=replace(value.readout, cells=(replace(first, actual_odd_responses=first.actual_odd_responses[:-1]), *value.readout.cells[1:])))
            else:
                first = value.readout.controls[0]
                received[case_id] = replace(value, readout=replace(value.readout, controls=(replace(first, control_id=first.control_id + ".foreign"), *value.readout.controls[1:])))
            method.assess_protected_functional(chosen, received, result_id="result.disclosed-refusal")


def test_reserved_transfer_rejects_nomination_and_never_pools_regimes(tmp_path):
    chosen = selected(tmp_path, "E6_TRANSFER")
    with pytest.raises(ValueError, match="cannot import a later preparation nomination"):
        replace(chosen, nomination=object())
    received = observations(chosen)
    del received[next(iter(received))]
    _, result = method.assess_protected_functional(chosen, received, result_id="result.disclosed-partial")
    assert [len(row.assigned_group_ids) for row in result.comparisons] == [1, 1]
    assert len({row.transfer_regime_id for row in result.comparisons}) == 2
    assert sum(len(row.missing_group_ids) for row in result.comparisons) == 1


def test_old_comparator_cannot_hide_fitted_groups_in_root_id_census(tmp_path):
    chosen = selected(tmp_path, "E6_TRANSFER")
    assert chosen.comparator.training_unit_ids != chosen.comparator.model_record.training_root_ids
    with pytest.raises(ValueError):
        replace(chosen.comparator, training_unit_ids=chosen.comparator.model_record.training_root_ids)
    with pytest.raises(TypeError):
        replace(chosen.comparator, original_training_record=None)


def test_unusable_case_still_authenticates_actual_comparator_before_arithmetic(tmp_path):
    chosen = selected(tmp_path, "E6_TRANSFER")
    received = observations(chosen)
    case_id = next(iter(received))
    value = received[case_id]
    first = value.readout.cells[0]
    assert first.view == "FINE"
    adverse = replace(value, readout=replace(value.readout,
        cells=(replace(first, normalized_error=D(".02")), *value.readout.cells[1:])))
    received[case_id] = adverse
    _, result = method.assess_protected_functional(chosen, received, result_id="result.disclosed-adverse")
    assert any(row.disposition == "UNEVALUABLE" and "PAIRED_VIEW_DISCREPANCY" in row.reasons for row in result.cases)
    received[case_id] = replace(adverse, comparator=replace(adverse.comparator,
        model=replace(adverse.comparator.model, object_fingerprint="f" * 64)))
    with pytest.raises(ValueError, match="protected comparator"):
        method.assess_protected_functional(chosen, received, result_id="result.disclosed-refused-adverse")


@pytest.mark.parametrize("collision", ("original-outside-selection", "other-future"))
def test_independent_future_streams_cannot_repeat_known_original_or_other_group_streams(tmp_path, collision):
    chosen = selected(tmp_path, "E6_TRANSFER")
    (group0, panels0), (group1, panels1) = chosen.future_panels
    independent0 = next(row for row in panels0 if row.role == "INDEPENDENT_FUTURE")
    streams = (chosen.sources.closure.reservation.allocation.roots[0].streams
        if collision == "original-outside-selection" else independent0.streams)
    changed = tuple(replace(row, streams=streams) if row.role == "INDEPENDENT_FUTURE" else row for row in panels1)
    with pytest.raises(ValueError, match="reuses an exposed, original allocated or other future stream"):
        replace(chosen, future_panels=((group0, panels0), (group1, changed)))
