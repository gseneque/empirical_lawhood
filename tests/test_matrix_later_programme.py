# SPDX-License-Identifier: MPL-2.0
"""Independent complete-denominator falsifiers; all source facts are exposed toys."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.experiment_preparation import (
    bind_later_inputs, prepare_later_experiment, validate_later_instance,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.operation_bindings import operation_declarations
from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import (
    PACKAGE_ROLES, MatrixFrozenConsumerPackage, MatrixFunctionalCriterion, MatrixLaterExperimentSpecification,
    MatrixProgrammeCase, MatrixProgrammeEvidence, MatrixProgrammeObservation, MatrixProgrammeRoster,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import (
    assess_later_programme, nominate_preparation, source_allocation, validate_evidence,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import (
    CALIBRATED_QUERY, ScheduledForecastFeature, ScheduledForecastSeal, ScheduledPublicSource,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell, ScheduledResponseScore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
from empirical_lawhood.runtime.execution import RunnerRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_factor_confirmation_eligibility import artifact, publish, stock
from tests.test_matrix_parameter_history import source as parameter_source
from tests.test_matrix_scheduled_history import CONSTRUCTION, scheduled


def ref(name, schema="empirical-lawhood/testing/exposed-later-method", *, version="1.0.0"):
    return ObjectIdentity(name, schema, version, sha256(name.encode()).hexdigest())


def criterion(n=2):
    return MatrixFunctionalCriterion("FACTOR", 128, D("0.05"), D("0.001"), n, 1, 0,
        1, 2, 1, 240, FAMILY_IDS, (ref("assumption.exposed.independence"),), "effort.declared-coupling-integral",
        1, 20, "BONFERRONI_FIXED_FULL_PRIMARY_FAMILY", "EXACT_BINOMIAL_ALL_ASSIGNED_GROUPS")


@pytest.fixture
def metadata(tmp_path):
    # These helpers construct and publish small explicit metadata only. No native
    # source, solver, factor producer, random generator or source capture runs.
    plane, prior = stock.__wrapped__(tmp_path, parameter_source().provenance)
    _, sources = scheduled.__wrapped__((plane, prior))
    return plane, sources[0]


def allocation(metadata, label, role, *, groups=2, temperatures=(D(3),)):
    _, template = metadata
    coordinates, roots, scopes = [], [], []
    for regime_at, temperature in enumerate(temperatures):
        coordinate = replace(template.coordinate, coordinate_id="coordinate." + label + "." + str(regime_at),
            autonomous_ticks=256, observation_ticks=(0, 4, 260),
            member=replace(template.coordinate.member, member_id="member." + label + "." + str(regime_at)),
            primary_view=replace(template.coordinate.primary_view, view_id="primary." + label + "." + str(regime_at), bath_temperature=temperature),
            fine_view=replace(template.coordinate.fine_view, view_id="fine." + label + "." + str(regime_at), bath_temperature=temperature))
        coordinates.append(coordinate)
        group_ids = []
        for at in range(groups):
            group = ("group." + label + "." if role is MatrixProgrammeRole.WITHHELD_TRANSFER else "group." + role.value.lower() + ".") + str(regime_at) + "." + str(at)
            group_ids.append(group)
            streams = tuple(MatrixHistorySeed(purpose, sha256((group + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)
            root = MatrixProgrammeRoot("root." + label + "." + str(regime_at) + "." + str(at), group,
                "regime." + str(regime_at), coordinate.coordinate_id, role, coordinate.clock_id)
            roots.append(original.ScheduledRoot(root, coordinate_identity(coordinate), streams))
        scopes.append(original.ScheduledMatchedScope("scope." + label + "." + str(regime_at), role,
            tuple(group_ids), (coordinate_identity(coordinate),), CONSTRUCTION))
    return original.ScheduledAllocation("allocation." + label, tuple(coordinates), tuple(roots), tuple(scopes), template.allocation.exposure)


def products(package, case, value):
    public = case.public_source
    prefix = ref("prefix." + case.case_id, original.ScheduledCausalPrefix.SCHEMA)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import FAMILY_MAP
    feature = ScheduledForecastFeature("feature." + case.case_id, public.source, prefix, public.root.root_id,
        case.unit_id, FAMILY_MAP[public.coordinate.family_id], public.root.clock_id, public.coordinate.physical_time(public.policy.cutoff_tick),
        None, "AVAILABLE", tuple((name, D(0)) for name in FEATURES))
    forecast = ScheduledForecastSeal("forecast." + case.case_id, public.source, prefix,
        ref("design.original." + case.case_id, "empirical-lawhood/matrix-scheduled-history/forecast-design"),
        package.component("model"), package.component("criterion"), package.component("calibration"), CALIBRATED_QUERY,
        feature, (D("0.01"),) * 15, (D("0.01"),) * 15, (D("0.01"),) * 15, D(0))
    cells = tuple(ScheduledResponseLossCell(view, panel, action, predictor, horizon,
        (D(0),), (value,), (value,), (None,), value)
        for view in ("FINE", "PRIMARY") for panel in ("panel.common", "panel.independent")
        for action in ("action.0", "action.1", "action.2", "action.3")
        for predictor in ("FACTOR", "FULL_COUPLED", "GENERIC_SLOW", "NORM_RADIUS", "SPECTRA")
        for horizon in (16, 64, 128))
    controls = tuple(ScheduledResponseTransitionControl("control." + case.case_id + "." + str(at),
        "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), D("1e-9"), "SATISFIED", 1, 192, (D(0),), ()) for at in range(48))
    with localcontext() as context:
        context.prec = 50
        cumulative = ((1 + value).ln(),) * 15
    score = ScheduledResponseScore("score." + case.case_id, public.source, prefix, original.identity(forecast),
        ref("physical." + case.case_id), ref("responses." + case.case_id), public.root.root_id, case.unit_id,
        public.root.role.value, package.component("criterion"), controls, True, "FINITE", cells, cumulative, ())
    comparator = replace(forecast, seal_id="comparator." + case.case_id, model=package.component("comparator"),
        calibration=package.component("comparator-calibration"))
    return MatrixProgrammeObservation(case.case_id, forecast, score, "SUPPORTED", (ref("supplier." + case.case_id),), comparator)


def selection(metadata, *, phase="E5_OPPORTUNITY", groups=2, winning=True, nomination=None, inherited=None):
    plane, template = metadata
    reserve_allocation = allocation(metadata, "reserved", MatrixProgrammeRole.WITHHELD_TRANSFER,
        groups=groups, temperatures=(D(30), D(40)))
    reservation = original.ScheduledReservation("reservation.later.toy", reserve_allocation,
        publish(plane, reserve_allocation, "published.later.reserve." + reserve_allocation.fingerprint()))
    package = MatrixFrozenConsumerPackage("package.later.toy", ref("freeze.before-later-outcomes"),
        tuple((role, ref("package." + role)) for role in PACKAGE_ROLES), original.identity(reservation),
        ("unit.training.original",), ("unit.selection.original",), "OBSERVATION_ASSISTED_SEALED_BEFORE_FUTURE")
    if inherited is not None:
        reservation, package = inherited
    arms = ("hold", "recipe.a", "recipe.b") if phase == "E5_OPPORTUNITY" else ("hold", "recipe.a") if phase == "E5_CONFIRMATION" else ("hold",)
    role = MatrixProgrammeRole.DEVELOPMENT if phase == "E5_OPPORTUNITY" else MatrixProgrammeRole.CONFIRMATION
    allocations = (reserve_allocation,) if phase == "E6_TRANSFER" else tuple(allocation(metadata, arm + "." + phase.lower(), role, groups=groups) for arm in arms)
    cases = []
    for arm, allocated in zip(arms if phase != "E6_TRANSFER" else ("hold",), allocations, strict=True):
        for row in allocated.roots:
            coordinate = next(c for c in allocated.coordinates if coordinate_identity(c) == row.coordinate)
            public = ScheduledPublicSource(ref("source." + row.root.root_id, original.ScheduledSource.SCHEMA,
                version=original.ScheduledSource.VERSION),
                row.root, coordinate, template.policy, original.identity(allocated), original.identity(reservation))
            cases.append(MatrixProgrammeCase("case." + row.root.root_id, arm, ref("recipe.original." + arm), public,
                artifact("state.original." + row.root.independent_group_id), D("0.006"), D(1),
                ref("restored.actual.common"), ref("assay.frozen.common"), (ref("assessment.native.original." + row.root.root_id),)))
    roster = MatrixProgrammeRoster("roster." + phase.lower(), phase,
        tuple(sorted(allocations, key=lambda row: row.allocation_id)), reservation, tuple(sorted(cases, key=lambda row: row.case_id)))
    evidence = MatrixProgrammeEvidence("evidence." + phase.lower(), roster.identity, package.identity,
        tuple(products(package, case, D("0.01") if winning and case.arm_id == "recipe.a" or phase == "E6_TRANSFER" else D("0.1")) for case in roster.cases))
    campaign = campaign_fixture()[0].campaign
    spec = MatrixLaterExperimentSpecification("specification." + phase.lower(), phase, roster.identity, package.identity,
        evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign), criterion(groups), groups, arms, "hold",
        None if nomination is None else nomination.identity, 1, "LEXICAL_ARM_ID",
        ("regime.0", "regime.1") if phase == "E6_TRANSFER" else (),
        ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN") if phase == "E6_TRANSFER" else (),
        "RETAINED_CONDITIONAL_ASSESSMENT",
        "COMMON_COUNTERFACTUAL_MENU_AND_PURPOSE_STREAMS")
    return spec, roster, package, evidence, campaign


def test_opportunity_nomination_is_functional_complete_and_keeps_negative_hold(metadata):
    spec, roster, package, evidence, _ = selection(metadata)
    allocation, design, results = validate_evidence(spec, roster, package, evidence)
    assert len(allocation.units) == 2 and len(design.coordinates) == 6 and len(results) == 6
    result = nominate_preparation(spec, roster, package, evidence, result_id="result.opportunity")
    assert result.selected_arm_id == "recipe.a" and result.disposition == "NOMINATED"
    assert result.candidate_results == (("recipe.a", 2, 2, D(2)), ("recipe.b", 0, 0, D(2)))
    assert all(not row.functional_reliable for row in result.cases if row.arm_id == "hold")
    assert len(result.recoverable_unit_ids) == 2
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


def test_saturated_failed_and_missing_opportunity_do_not_create_confirmation(metadata):
    spec, roster, package, evidence, _ = selection(metadata, winning=False)
    none = nominate_preparation(spec, roster, package, evidence, result_id="result.no-headroom")
    assert none.disposition == "NONDISCRIMINATING_OPPORTUNITY" and none.selected_recipe is None
    short = replace(evidence, rows=evidence.rows[:-1])
    spec = replace(spec, evidence=short.identity)
    missing = nominate_preparation(spec, roster, package, short, result_id="result.missing-opportunity")
    assert missing.disposition == "UNEVALUABLE_OPPORTUNITY" and len(missing.cases) == 6


def test_transfer_complete_regimes_exact_probability_and_unbounded_abstention(metadata):
    spec, roster, package, evidence, _ = selection(metadata, phase="E6_TRANSFER")
    result = assess_later_programme(spec, roster, package, evidence, result_id="result.transfer")
    assert tuple(row.comparison_id for row in result.comparisons) == ("e6.nearby", "e6.shifted")
    assert all(row.successes == 2 and row.usable_groups == 2 and not row.criterion_met_conditionally for row in result.comparisons)
    assert all(Fraction(row.p_value_numerator, row.p_value_denominator) == Fraction(1, 4) for row in result.comparisons)
    rows = []
    for row in evidence.rows:
        forecast = replace(row.forecast, radius=None, log_error_uppers=(None,) * 15)
        rows.append(replace(row, forecast=forecast, score=replace(row.score, error_forecast=original.identity(forecast))))
    unbounded = replace(evidence, rows=tuple(rows))
    failed = assess_later_programme(replace(spec, evidence=unbounded.identity), roster, package, unbounded, result_id="result.unbounded")
    assert all(row.successes == 0 and row.bounded_groups == 0 and not row.criterion_met_conditionally for row in failed.comparisons)
    assert len(failed.cases) == 4 and failed.qualification == "NOT_ESTABLISHED"


def test_transfer_missing_case_remains_in_exact_regime_denominator(metadata):
    spec, roster, package, evidence, _ = selection(metadata, phase="E6_TRANSFER")
    sparse = replace(evidence, rows=evidence.rows[:-1])
    result = assess_later_programme(replace(spec, evidence=sparse.identity), roster, package, sparse, result_id="result.sparse")
    assert len(result.cases) == 4
    assert sorted(row.successes for row in result.comparisons) == [1, 2]
    assert sorted(len(row.missing_group_ids) for row in result.comparisons) == [0, 1]
    assert all(len(row.assigned_group_ids) == 2 for row in result.comparisons)


@pytest.mark.parametrize("damage", ("initial", "duration", "restored", "noise", "missing-arm"))
def test_matched_preparation_refuses_actual_invariant_or_complete_cell_changes(metadata, damage):
    spec, roster, package, evidence, _ = selection(metadata)
    first = next(case for case in roster.cases if case.arm_id == "recipe.a")
    if damage == "initial":
        changed = replace(first, initial_state=replace(first.initial_state, sha256="f" * 64))
    elif damage == "duration":
        changed = replace(first, preparation_duration=D("0.007"))
    elif damage == "restored":
        changed = replace(first, restored_context=ref("restored.changed"))
    elif damage == "missing-arm":
        changed = None
    else:
        actual = next(row for row in roster.allocations if original.identity(row) == first.public_source.allocation)
        root = next(row for row in actual.roots if row.root.root_id == first.public_source.root.root_id)
        altered = replace(root, streams=tuple(replace(stream, digest_sha256=sha256((stream.purpose + "different").encode()).hexdigest()) for stream in root.streams))
        actual = replace(actual, roots=tuple(altered if row == root else row for row in actual.roots))
        roster = replace(roster, allocations=tuple(actual if row.allocation_id == actual.allocation_id else row for row in roster.allocations),
            cases=tuple(replace(case, public_source=replace(case.public_source, allocation=original.identity(actual)))
                if case.public_source.allocation.object_id == actual.allocation_id else case for case in roster.cases))
        changed = next(case for case in roster.cases if case.case_id == first.case_id)
    roster = replace(roster, cases=tuple(changed if case.case_id == first.case_id else case for case in roster.cases if changed is not None or case.case_id != first.case_id))
    evidence = replace(evidence, roster=roster.identity)
    spec = replace(spec, roster=roster.identity, evidence=evidence.identity)
    with pytest.raises(ValueError, match="matched|invariant|cell|duration"):
        validate_evidence(spec, roster, package, evidence)


def test_preparation_and_real_compiler_preserve_saved_route_and_refuse_native_acquisition(metadata, tmp_path):
    spec, roster, package, evidence, campaign = selection(metadata)
    records = dict(roster=roster, package=package, evidence=evidence, campaign=campaign)
    resolved = bind_later_inputs(spec, records)
    execution = ExecutionSelection(workers=1, environment_id="matrix-main", source_snapshot=ref("source.actual-snapshot"), output_root=str(tmp_path))
    prepared = prepare_later_experiment(spec, scientific_inputs=resolved.scientific_inputs, method_inputs=resolved.method_inputs, execution=execution)
    assert prepared.executable and prepared.census.native_effect_count == 0
    declarations = operation_declarations()
    registry = CapabilityRegistry("registry.matrix-later", tuple(row.manifest() for row in declarations))
    compiled = compile_recursive_wave(draft=prepared.draft, registrations=tuple(row.registration() for row in declarations),
        registry=registry, implementation_commit="a" * 40,
        output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    assert len(compiled.execution_plan.tasks) == 1
    runners = RunnerRegistry(tuple(row.provider_factory().runner_factory() for row in declarations),
        registry_sha256=registry.fingerprint())
    task, = compiled.execution_plan.tasks
    assert runners.resolve(task).manifest == registry.resolve(task.capability.capability_key, task.capability.capability_version)
    validate_later_instance(specification=spec, allocation=prepared.allocation, draft=prepared.draft, source_records=prepared.design_records)
    native = replace(spec, mode="ACQUIRE_AND_ASSESS")
    resolved = bind_later_inputs(native, records)
    missing = prepare_later_experiment(native, scientific_inputs=resolved.scientific_inputs, method_inputs=resolved.method_inputs, execution=execution)
    assert not missing.executable
    software = tuple(row for row in missing.dependencies if row.kind is DependencyKind.SOFTWARE)
    assert tuple(row.code for row in software) == ('matrix.later.software.saved-route-native-lowering',)
    assert software[0].detail == 'This protocol supports RETAINED_CONDITIONAL_ASSESSMENT only; native acquisition is unsupported.'
    assert any('RETAINED_CONDITIONAL_ASSESSMENT' in row.detail for row in prepared.assessment_limitations)
    assert any(row.kind is DependencyKind.AUTHORITY for row in missing.dependencies)
    assert decode_canonical_bytes(spec.canonical_bytes(), type(spec), maximum_bytes=None) == spec
    assert ObjectIdentity.from_record(campaign.campaign_id, campaign).object_schema == CampaignSpec.SCHEMA
    assert source_allocation(spec, roster).unit_ids() == prepared.allocation.unit_ids()


def test_fresh_confirmation_preserves_nomination_criterion_recipe_and_complete_pairs(metadata):
    dev, roster, package, evidence, _ = selection(metadata)
    nomination = nominate_preparation(dev, roster, package, evidence, result_id="result.development.nomination")
    spec, fresh, frozen, observations, _ = selection(metadata, phase="E5_CONFIRMATION", nomination=nomination,
        inherited=(roster.reservation, package))
    result = assess_later_programme(spec, fresh, frozen, observations, nomination=nomination, result_id="result.confirmation")
    comparison, = result.comparisons
    assert comparison.successes == 2 and comparison.usable_groups == 2
    assert Fraction(comparison.p_value_numerator, comparison.p_value_denominator) == Fraction(1, 4)
    assert not comparison.criterion_met_conditionally  # Two exposed toy pairs cannot meet alpha1/240.
    assert set(comparison.assigned_group_ids).isdisjoint(nomination.development_unit_ids)
    missing_hold = next(case.case_id for case in fresh.cases if case.arm_id == "hold")
    sparse = replace(observations, rows=tuple(row for row in observations.rows if row.case_id != missing_hold))
    missing = assess_later_programme(replace(spec, evidence=sparse.identity), fresh, frozen, sparse,
        nomination=nomination, result_id="result.missing-confirmation-hold")
    assert len(missing.comparisons[0].assigned_group_ids) == 2 and missing.comparisons[0].usable_groups == 1
    assert len(missing.comparisons[0].missing_group_ids) == 1 and len(missing.cases) == 4
    with pytest.raises(ValueError, match="criterion"):
        assess_later_programme(replace(spec, criterion=replace(spec.criterion, normalized_error_maximum=D("0.2"))),
            fresh, frozen, observations, nomination=nomination, result_id="result.forbidden-criterion-edit")


@pytest.mark.parametrize("damage", ("support", "comparator", "model", "score-census", "controls", "score-projection"))
def test_transfer_preserves_unsupported_accuracy_and_refuses_original_product_substitution(metadata, damage):
    spec, roster, package, evidence, _ = selection(metadata, phase="E6_TRANSFER")
    row = evidence.rows[0]
    if damage == "support":
        changed = replace(row, source_support="UNSUPPORTED")
    elif damage == "comparator":
        changed = replace(row, comparator_forecast=replace(row.comparator_forecast,
            model=ref("model.unselected.comparator")))
    elif damage == "model":
        forecast = replace(row.forecast, model=ref("model.refitted-on-transfer"))
        changed = replace(row, forecast=forecast, score=replace(row.score, error_forecast=original.identity(forecast)))
    elif damage == "score-census":
        changed = replace(row, score=replace(row.score, cells=row.score.cells[:-1]))
    elif damage == "controls":
        changed = replace(row, score=replace(row.score, controls=row.score.controls[:-1]))
    else:
        changed = replace(row, score=replace(row.score, cumulative_log_errors=(D(0),) * 15))
    altered = replace(evidence, rows=(changed, *evidence.rows[1:]))
    spec = replace(spec, evidence=altered.identity)
    if damage == "support":
        result = assess_later_programme(spec, roster, package, altered, result_id="result.unsupported-accurate")
        observed = next(case for case in result.cases if case.case_id == changed.case_id)
        assert observed.actual_error == D("0.01") and observed.functional_reliable
        assert observed.absolute_forecast_log_error is not None and observed.absolute_comparator_log_error is not None
        assert not observed.conditional_admission and observed.source_support == "UNSUPPORTED"
        assert sum(comparison.successes for comparison in result.comparisons) == 3
    else:
        with pytest.raises(ValueError, match="comparator|substitutes|census|controls|projection"):
            assess_later_programme(spec, roster, package, altered, result_id="result.forbidden-transfer-edit")


def test_recipe_tie_and_effort_tie_are_frozen_and_decimal_context_independent(metadata):
    spec, roster, package, evidence, _ = selection(metadata)
    rows = tuple(products(package, case, D("0.1") if case.arm_id == "hold" else D("0.01")) for case in roster.cases)
    tied = replace(evidence, rows=rows)
    spec = replace(spec, evidence=tied.identity)
    result = nominate_preparation(spec, roster, package, tied, result_id="result.lexical-tie")
    assert result.selected_arm_id == "recipe.a"
    cases = tuple(replace(case, preparation_effort=D("1234.56789") if case.arm_id == "recipe.a" else D("1234.56788")) for case in roster.cases)
    revised = replace(roster, cases=cases)
    tied = replace(tied, roster=revised.identity)
    spec = replace(spec, roster=revised.identity, evidence=tied.identity, tie_policy="MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")
    with localcontext() as context:
        context.prec = 3
        result = nominate_preparation(spec, revised, package, tied, result_id="result.effort-tie")
    assert result.selected_arm_id == "recipe.b"
    assert result.candidate_results == (("recipe.a", 2, 2, D("2469.13578")), ("recipe.b", 2, 2, D("2469.13576")))


def test_full_twelve_slot_family_cannot_reassign_alpha_after_unused_claims():
    with pytest.raises(ValueError, match="testing family"):
        replace(criterion(), alpha_numerator=1, alpha_denominator=20)
    with pytest.raises(ValueError, match="primary family"):
        replace(criterion(), family_slots=("e5.preparation",))


@pytest.mark.parametrize("key", ("allocation", "evidence", "package", "roster", "specification"))
@pytest.mark.parametrize("damage", ("digest", "size", "artifact"))
def test_compiler_refuses_selected_original_external_contract_edits(metadata, tmp_path, key, damage):
    spec, roster, package, evidence, campaign = selection(metadata)
    inputs = bind_later_inputs(spec, dict(roster=roster, package=package, evidence=evidence, campaign=campaign))
    prepared = prepare_later_experiment(spec, scientific_inputs=inputs.scientific_inputs, method_inputs=inputs.method_inputs,
        execution=ExecutionSelection(workers=1, environment_id="matrix-main", source_snapshot=ref("snapshot.exposed-contract-test"), output_root=str(tmp_path)))
    external = next(row for row in prepared.draft.external_inputs if row.input_id == "external." + key)
    changes = {"expected_content_sha256": "f" * 64} if damage == "digest" else (
        {"maximum_size_bytes": external.maximum_size_bytes + 1} if damage == "size" else {"logical_artifact_id": "artifact.unselected-original"})
    altered = replace(prepared.draft, external_inputs=tuple(replace(row, **changes) if row == external else row
        for row in prepared.draft.external_inputs))
    declarations = operation_declarations()
    with pytest.raises(ValueError, match="external|contract|original"):
        compile_recursive_wave(draft=altered, registrations=tuple(row.registration() for row in declarations),
            registry=CapabilityRegistry("registry.external-edit", tuple(row.manifest() for row in declarations)), implementation_commit="a" * 40,
            output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})


@pytest.mark.parametrize("field", ("rng_version", "stream_derivation_rule_id", "time_unit"))
def test_matched_preparation_requires_complete_original_random_and_clock_contract(metadata, field):
    spec, roster, package, evidence, _ = selection(metadata)
    selected = next(row for row in roster.allocations if any(case.arm_id == "recipe.a" and
        case.public_source.allocation == original.identity(row) for case in roster.cases))
    if field == "time_unit":
        # The original view owner already has one closed physical clock.
        with pytest.raises(ValueError, match="clock"):
            replace(selected.coordinates[0].primary_view, time_unit="changed.original-contract")
        return
    coordinates = tuple(replace(row, primary_view=replace(row.primary_view, **{field: "2.0.0" if field == "rng_version" else "changed.original-contract"}),
        fine_view=replace(row.fine_view, **{field: "2.0.0" if field == "rng_version" else "changed.original-contract"})) for row in selected.coordinates)
    replacements = {old.coordinate_id: new for old, new in zip(selected.coordinates, coordinates, strict=True)}
    allocated = replace(selected, coordinates=coordinates,
        roots=tuple(replace(row, coordinate=coordinate_identity(replacements[row.root.coordinate_id])) for row in selected.roots),
        matched_scopes=tuple(replace(row, coordinates=tuple(coordinate_identity(replacements[value.object_id]) for value in row.coordinates)) for row in selected.matched_scopes))
    revised = replace(roster, allocations=tuple(allocated if row == selected else row for row in roster.allocations),
        cases=tuple(replace(case, public_source=replace(case.public_source, allocation=original.identity(allocated),
            coordinate=replacements[case.public_source.coordinate.coordinate_id])) if case.public_source.allocation == original.identity(selected)
            else case for case in roster.cases))
    observed = replace(evidence, roster=revised.identity)
    with pytest.raises(ValueError, match="matched|invariant"):
        validate_evidence(replace(spec, roster=revised.identity, evidence=observed.identity), revised, package, observed)


def test_confirmation_refuses_every_known_nontraining_upstream_use_before_pair_reduction(metadata):
    dev, roster, package, evidence, _ = selection(metadata)
    frozen = replace(package, selection_unit_ids=tuple(sorted((*package.selection_unit_ids, "group.confirmation.0.0"))))
    observed = replace(evidence, package=frozen.identity)
    dev = replace(dev, package=frozen.identity, evidence=observed.identity)
    nomination = nominate_preparation(dev, roster, frozen, observed, result_id="nomination.before-confirmation-upstream-use")
    spec, fresh, package, observed, _ = selection(metadata, phase="E5_CONFIRMATION", nomination=nomination,
        inherited=(roster.reservation, frozen))
    with pytest.raises(ValueError, match="upstream"):
        assess_later_programme(spec, fresh, package, observed, result_id="result.forbidden-known-upstream-use", nomination=nomination)


@pytest.mark.parametrize("phase", ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER"))
def test_preparation_and_instance_authentication_never_replay_outcome_worker(metadata, tmp_path, monkeypatch, phase):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import functional_outcome_reduction, science

    nomination, inherited = None, None
    if phase == "E5_CONFIRMATION":
        dev, roster, package, evidence, _ = selection(metadata)
        nomination = nominate_preparation(dev, roster, package, evidence, result_id="nomination.pre-authentication")
        inherited = roster.reservation, package
    spec, roster, package, evidence, campaign = selection(metadata, phase=phase, nomination=nomination, inherited=inherited)

    def forbidden(*args, **kwargs):
        raise AssertionError("preparation/retained instance authentication replayed scientific outcome reduction")

    for name in ("_case_result", "_validate_original_score", "validate_evidence", "nominate_preparation", "assess_later_programme"):
        monkeypatch.setattr(science, name, forbidden)
    for name in ("_nominate_functional_cases", "_functional_comparison", "_confirmation_comparisons", "_transfer_comparisons", "binomial_upper_tail"):
        monkeypatch.setattr(functional_outcome_reduction, name, forbidden)
    records = dict(roster=roster, package=package, evidence=evidence, campaign=campaign)
    if nomination is not None:
        records["nomination"] = nomination
    inputs = bind_later_inputs(spec, records)
    execution = ExecutionSelection(workers=1, environment_id="matrix-main", source_snapshot=ref("snapshot.no-reduction-authentication"), output_root=str(tmp_path))
    prepared = prepare_later_experiment(spec, scientific_inputs=inputs.scientific_inputs, method_inputs=inputs.method_inputs, execution=execution)
    assert prepared.executable
    for _ in range(2):
        validate_later_instance(specification=spec, allocation=prepared.allocation, draft=prepared.draft,
            source_records=prepared.design_records)
    changed = replace(spec, package=replace(spec.package, object_fingerprint="f" * 64))
    rejected = prepare_later_experiment(changed, scientific_inputs=inputs.scientific_inputs, method_inputs=inputs.method_inputs, execution=execution)
    assert not rejected.executable and any(row.code.endswith("package.identity") for row in rejected.dependencies)
    with pytest.raises(ValueError, match="incomplete"):
        validate_later_instance(specification=changed, allocation=prepared.allocation, draft=prepared.draft,
            source_records=prepared.design_records)
    if nomination is not None:
        changed = replace(spec, criterion=replace(spec.criterion, normalized_error_maximum=D(".04")))
        inputs = bind_later_inputs(changed, records)
        rejected = prepare_later_experiment(changed, scientific_inputs=inputs.scientific_inputs, method_inputs=inputs.method_inputs, execution=execution)
        assert not rejected.executable and any("criterion" in row.detail for row in rejected.dependencies)
        with pytest.raises(ValueError, match="incomplete"):
            validate_later_instance(specification=changed, allocation=inputs.scientific_inputs["roster"], draft=prepared.draft,
                source_records=prepared.design_records)
