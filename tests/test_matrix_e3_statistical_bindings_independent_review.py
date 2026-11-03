# SPDX-License-Identifier: MPL-2.0
"""Independent in-process statistical custody controls over exposed literals.

The declaration factories, guarded ports and committed receipts are real. The
source/publication hooks and causal/response values are disclosed conformance
fixtures; these checks establish no native result, eligibility or issue act.
"""

from dataclasses import fields, replace
from decimal import Decimal as D, ROUND_CEILING, localcontext
from fractions import Fraction
from math import comb
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_statistical_bindings as owner
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.execution import WorkerInputPort
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.plans import ScientificInputRole
from tests.test_matrix_e3_protected_methods import causal, outcome
from tests.test_matrix_e3_protected_prefix_science import forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_e3_statistical_bindings import (
    OUTCOME, case as case, config, execute, fitted as fitted, prepared, sources, stored,
)


def _forecast_operands(case, fitted, *, role="calibration", unit=None, frozen=None, calibration=None):
    unit = unit or case.allocation.unit_ids(role)[0]
    source, feature = causal(case, unit)
    feature_port = stored(case, feature, "independent.feature." + unit,
        task=owner.feature_task_id(source.root_id))
    operands = {**fitted.common, "models": fitted.models, "frozen": frozen or fitted.frozen,
        "feature": feature_port}
    if role == "evaluation":
        operands.update(calibration=calibration, **{"model-freeze": fitted.frozen})
    return source, operands


def _paired(case, current, name, *, index, role):
    """Author targets independently, with distinct paired views and endpoints."""
    if role == "calibration":
        primary = tuple(D("0.2") + D(index) / 100 + D(k) / 1000 for k in range(15))
    else:
        # The original fit, rather than a replacement predictor, supplies points.
        method = "SPECTRAL_RIDGE" if index < 5 else "RAW_TRAIN_MEDIAN"
        with localcontext() as context:
            context.prec = 50
            primary = tuple(value.exp() - 1 for value in dict(current.record.log_points)[method])
    paired = outcome(current.record, values=primary, missing=role == "evaluation" and index == 7)
    if not (role == "evaluation" and index == 7):
        paired = replace(paired, views=(replace(paired.views[0],
            errors=tuple(v + D("0.00005") for v in primary)), paired.views[1]))
    return stored(case, paired, name, access=Access.EVALUATION_SEALED,
        ceiling=Visibility.DEVELOPMENT_ONLY, task=OUTCOME(paired.feature.public_source.root.root_id), output="outcome")


def _fit_receipt(case, models, joined):
    """One complete literal fit receipt carries both adversarial publications."""
    models = stored(case, models.record, "independent.fit.model-for-foreign-join",
        access=Access.DEVELOPMENT_VISIBLE, ceiling=Visibility.DEVELOPMENT_ONLY)
    publications = (models.publication, joined.publication)
    task = owner.statistical_task_id(case.inputs.specification.identity, case.allocation.identity, "fit")
    receipt = CanonicalTaskReceipt("receipt.independent.fit.foreign-join", "run.literal.statistical", task,
        "attempt.independent.fit.foreign-join", case.provenance.observed_git_head, (),
        tuple(sorted((p.materialization for p in publications), key=lambda p: p.materialization_id)),
        tuple(sorted((p.logical for p in publications), key=lambda p: p.logical_artifact_id)), (),
        OperationalStatus.SUCCEEDED, ())
    ExternalTaskReceiptStore(case.plane).commit(receipt,
        visibility_ceiling=Visibility.DEVELOPMENT_ONLY, outcome_access=Access.DEVELOPMENT_VISIBLE)
    return (SimpleNamespace(**{**vars(models), "receipt": receipt}),
        SimpleNamespace(**{**vars(joined), "receipt": receipt}))


@pytest.fixture(scope="module")
def sequence(case, fitted):
    models_before = fitted.models.record.canonical_bytes()
    forecasts, outcomes = {}, {}
    calibration = sealed = None
    for role in ("calibration", "evaluation"):
        fs, ys = [], []
        for i, unit in enumerate(case.allocation.unit_ids(role)):
            source, operands = _forecast_operands(case, fitted, role=role, unit=unit,
                frozen=fitted.frozen if role == "calibration" else sealed, calibration=calibration)
            current = execute(case, prepared(case, config(case, "forecast", mode=role, root=source.root.root), operands))["product"]
            fs.append(current)
            ys.append(_paired(case, current, "independent.outcome." + unit, index=i, role=role))
        forecasts[role], outcomes[role] = tuple(fs), tuple(ys)
        if role == "calibration":
            calibration = execute(case, prepared(case, config(case, "calibrate"),
                {**fitted.common, "models": fitted.models, "frozen": fitted.frozen,
                    "forecasts": tuple(fs), "outcomes": tuple(ys)}))["product"]
            sealed = execute(case, prepared(case, config(case, "freeze", mode="calibration"),
                {**fitted.common, "models": fitted.models, "model-freeze": fitted.frozen,
                    "calibration": calibration}))["product"]
    assessment = execute(case, prepared(case, config(case, "assess"),
        {**fitted.common, "frozen": sealed, "forecasts": forecasts["evaluation"],
            "outcomes": outcomes["evaluation"]}))["product"]
    assert fitted.models.record.canonical_bytes() == models_before
    return SimpleNamespace(forecasts=forecasts, outcomes=outcomes, calibration=calibration,
        sealed=sealed, assessment=assessment)


def test_entire_cal20_conf8_chain_has_independent_rank_margin_and_binomial_oracles(case, fitted, sequence):
    specification = case.inputs.specification
    cal = sequence.calibration.record
    assert len(sequence.forecasts["calibration"]) == len(cal.scores) == 20
    with localcontext() as context:
        context.prec = 50
        scores = tuple(max(max(D(0), (1 + max(y.record.views[0].errors[k], y.record.views[1].errors[k])).ln()
            - dict(f.record.log_points)["SPECTRAL_RIDGE"][k]) for k in range(15))
            for f, y in zip(sequence.forecasts["calibration"], sequence.outcomes["calibration"], strict=True))
        rank = int((D(21) * (1 - specification.calibration_alpha)).to_integral_value(rounding=ROUND_CEILING))
        assert tuple(row[1] for row in cal.scores) == scores
        assert cal.rank == rank and cal.radius == sorted(scores)[rank - 1] > 0
        primary_index = science.exposed.ENDPOINTS.index((specification.measurement.primary_description,
            specification.measurement.primary_horizon))
        expected = []
        for f, y in zip(sequence.forecasts["evaluation"], sequence.outcomes["evaluation"], strict=True):
            predictions = {method: values[primary_index].exp() - 1 for method, values in f.record.log_points}
            comparisons = tuple((baseline, view.view_id, None if view.errors[primary_index] is None else
                abs(view.errors[primary_index] - predictions[baseline])
                - abs(view.errors[primary_index] - predictions["SPECTRAL_RIDGE"]))
                for baseline in ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN") for view in y.record.views)
            usable = all(value is not None for _, _, value in comparisons)
            success = usable and all(value > specification.assessment.improvement_margin for _, _, value in comparisons)
            expected.append((usable, success, comparisons))
    result = sequence.assessment.record
    assert len(result.decisions) == 8 and result.usable_units == 7
    assert tuple((row.usable, row.success, row.comparisons) for row in result.decisions) == tuple(expected)
    assert result.successes == sum(row[1] for row in expected)
    p = Fraction(specification.assessment.null_probability)
    exact = sum((Fraction(comb(8, k)) * p ** k * (1 - p) ** (8 - k)
        for k in range(result.successes, 9)), Fraction(0))
    assert Fraction(result.binomial_tail_numerator, result.binomial_tail_denominator) == exact
    assert result.criterion_met == (exact <= specification.assessment.alpha
        and result.usable_units >= specification.assessment.minimum_usable_units)
    assert len(result.coverage) == len(result.coverage_bound_kinds) == 8
    assert sequence.sealed.record.model_freeze == science.identity(fitted.frozen.record)
    assert all(f.record.models == science.identity(fitted.models.record)
        for rows in sequence.forecasts.values() for f in rows)
    median = next(row for row in fitted.models.record.models if row.method_key == "RAW_TRAIN_MEDIAN")
    raw = tuple(sorted(row.view("primary").errors[k] for row in case.train_outcomes.rows) for k in range(15))
    assert median.raw_constants == tuple((values[5] + values[6]) / 2 for values in raw)


def test_missing_calibration_retains_all20_units_and_an_infinite_rank20_radius(case, fitted, sequence):
    rows = list(sequence.outcomes["calibration"])
    first = sequence.forecasts["calibration"][0]
    rows[0] = stored(case, outcome(first.record, missing=True), "independent.calibration.missing",
        task=OUTCOME(first.record.feature.public_source.root.root_id), output="outcome",
        access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY)
    result = execute(case, prepared(case, config(case, "calibrate"),
        {**fitted.common, "models": fitted.models, "frozen": fitted.frozen,
            "forecasts": sequence.forecasts["calibration"], "outcomes": tuple(rows)}))["product"].record
    assert result.rank == 20 and result.radius is None and len(result.scores) == 20
    assert result.scores[0][1] is None and "UNKNOWN_CONTACT" in result.scores[0][2]


def test_literal_paired_margin_and_missing_failure_use_eight_assigned_not_seven_usable(case, fitted, sequence):
    """Authored points isolate assessment arithmetic, not fitted prediction."""
    with localcontext() as context:
        context.prec = 50
        candidate, baseline = D("1.05").ln(), D("1.051").ln()
    forecasts, outcomes = [], []
    for i, original in enumerate(sequence.forecasts["evaluation"]):
        literal = replace(original.record, log_points=tuple((name,
            ((candidate if name == "SPECTRAL_RIDGE" else baseline),) * 15) for name, _ in original.record.log_points))
        forecasts.append(stored(case, literal, "independent.literal-points." + str(i),
            task=original.receipt.task_id, access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY))
        paired = outcome(literal, values=((D("0.05") if i < 5 else D("0.051")),) * 15, missing=i == 7)
        if i == 6:
            # A strict failure in FINE coexists with a passing PRIMARY margin.
            paired = replace(paired, views=(replace(paired.views[0], errors=(D("0.050425"),) * 15),
                replace(paired.views[1], errors=(D("0.050375"),) * 15)))
        outcomes.append(stored(case, paired, "independent.literal-margin." + str(i),
            task=OUTCOME(paired.feature.public_source.root.root_id), output="outcome",
            access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY))
    result = execute(case, prepared(case, config(case, "assess"), {**fitted.common,
        "frozen": sequence.sealed, "forecasts": tuple(forecasts), "outcomes": tuple(outcomes)}))["product"].record
    assert len(result.decisions) == 8 and result.successes == 5 and result.usable_units == 7
    exact = Fraction(sum(comb(8, k) for k in range(5, 9)), 2 ** 8)
    assert exact == Fraction(93, 256)
    assert Fraction(result.binomial_tail_numerator, result.binomial_tail_denominator) == exact
    assert exact != Fraction(sum(comb(7, k) for k in range(5, 8)), 2 ** 7)
    assert not result.criterion_met
    assert result.decisions[6].comparisons == (
        ("ALL_ORIGIN_RIDGE", "fine", D("0.00015")),
        ("ALL_ORIGIN_RIDGE", "primary", D("0.00025")),
        ("RAW_TRAIN_MEDIAN", "fine", D("0.00015")),
        ("RAW_TRAIN_MEDIAN", "primary", D("0.00025")))
    assert not result.decisions[6].success and not result.decisions[7].usable
    assert "UNKNOWN_CONTACT" in result.decisions[7].reasons


@pytest.mark.parametrize("name", ("manifest-reference", "original-publication", "train-access"))
def test_invalid_source_metadata_refuses_before_either_train_body_is_read(case, monkeypatch, name):
    operands, selected_config = sources(case), config(case, "fit")
    if name == "manifest-reference":
        selected_config = replace(selected_config, source_manifest=replace(selected_config.source_manifest,
            object_fingerprint="f" * 64))
    elif name == "original-publication":
        foreign = stored(case, operands["original-allocation"].record,
            "independent.foreign.original-publication").publication
        pubs = tuple((key, foreign, available)
            if key == "allocation" else (key, publication, available)
            for key, publication, available in selected_config.publications)
        selected_config = replace(selected_config, publications=pubs)
    else:
        operands["features"] = stored(case, case.train_features, "independent.train.blind")
    selected = prepared(case, selected_config, operands)
    train = {operands[key].publication.logical.logical_artifact_id for key in ("features", "outcomes")}
    reads, original = [], WorkerInputPort.read
    def observe(port, *args, **kwargs):
        if port.artifact_id in train:
            reads.append(port.artifact_id)
        return original(port, *args, **kwargs)
    monkeypatch.setattr(WorkerInputPort, "read", observe)
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)
    assert reads == []


@pytest.mark.parametrize("substitution", ("producer-task", "producer-output", "prefit-value", "external-model"))
def test_model_freeze_refuses_a_substituted_fit_or_join_before_math(case, fitted, monkeypatch, substitution):
    models, joined = fitted.models, fitted.joined
    if substitution == "producer-task":
        models = stored(case, models.record, "independent.model.foreign-task", task="literal.foreign.fit")
    elif substitution == "producer-output":
        models = SimpleNamespace(**{**vars(models), "output": "prefit-join"})
    elif substitution == "prefit-value":
        joined = stored(case, replace(joined.record, record_id="independent.foreign.prefit-join"),
            "independent.join.foreign-value", output="prefit-join",
            access=Access.DEVELOPMENT_VISIBLE, ceiling=Visibility.DEVELOPMENT_ONLY)
        models, joined = _fit_receipt(case, models, joined)
    selected = prepared(case, config(case, "freeze", mode="model"),
        {**fitted.common, "models": models, "prefit-join": joined}, foreign_models=substitution == "external-model")
    monkeypatch.setattr(science, "freeze_protected_e3", lambda *args, **kwargs: pytest.fail("substituted fit reached freeze arithmetic"))
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)


@pytest.mark.parametrize("field", ("logical", "physical", "read-bytes"))
def test_prepared_model_hashes_and_actual_port_bytes_cannot_be_substituted(case, fitted, monkeypatch, field):
    selected = prepared(case, config(case, "freeze", mode="model"),
        {**fitted.common, "models": fitted.models, "prefit-join": fitted.joined})
    alias = fitted.models.publication.logical.logical_artifact_id
    contract = selected.context.prepared_invocation
    if field != "read-bytes":
        def edited(row):
            if row.artifact_id != alias:
                return row
            if field == "physical":
                return replace(row, physical_sha256="f" * 64)
            return replace(row, logical=replace(row.logical, content_sha256="f" * 64), scientific_identity=None)
        contract = replace(contract, inputs=tuple(edited(row) for row in contract.inputs))
        context = replace(selected.context, prepared_invocation=contract)
    else:
        context = selected.context
        original = WorkerInputPort.read
        def corrupted(port, *args, **kwargs):
            raw = original(port, *args, **kwargs)
            return raw[:-1] + b" " if port.artifact_id == alias else raw
        monkeypatch.setattr(WorkerInputPort, "read", corrupted)
    monkeypatch.setattr(science, "freeze_protected_e3", lambda *args, **kwargs: pytest.fail("forged bytes reached arithmetic"))
    with pytest.raises(ValueError, match="publication bytes"):
        selected.runner.execute(context)


@pytest.mark.parametrize("name", ("cal-uses-calibrated-freeze", "conf-uses-model-freeze", "foreign-feature-task",
    "foreign-native-role", "wrong-cutoff"))
def test_forecast_rejects_role_cutoff_and_freeze_leaks(case, fitted, sequence, name):
    role = "evaluation" if name == "conf-uses-model-freeze" else "calibration"
    source, operands = _forecast_operands(case, fitted, role=role,
        frozen=fitted.frozen if role == "evaluation" else sequence.sealed if name == "cal-uses-calibrated-freeze" else None,
        calibration=sequence.calibration)
    if name == "conf-uses-model-freeze":
        # A distinct ordinary publication/receipt reaches the scientific guard;
        # reusing the same physical materialization twice is refused upstream.
        operands["frozen"] = stored(case, fitted.frozen.record, "independent.conf.bare-model-freeze",
            task=owner.statistical_task_id(case.inputs.specification.identity, case.allocation.identity,
                "freeze", mode="calibration"), access=Access.EVALUATION_SEALED,
            ceiling=Visibility.DEVELOPMENT_ONLY)
    elif name == "foreign-feature-task":
        operands["feature"] = stored(case, operands["feature"].record, "independent.feature.foreign-task",
            task="literal.foreign.feature")
    elif name == "foreign-native-role":
        feature = operands["feature"].record
        feature = replace(feature, public_source=replace(feature.public_source,
            root=replace(feature.public_source.root, role=MatrixProgrammeRole.CONFIRMATION)))
        operands["feature"] = stored(case, feature, "independent.feature.confirmation-in-cal",
            task=owner.feature_task_id(source.root_id))
    elif name == "wrong-cutoff":
        feature = operands["feature"].record
        policy = feature.public_source.policy
        policy = replace(policy, cutoff_tick=240,
            factor_rule=replace(policy.factor_rule, risk_start_tick=240,
                lattice=tuple(t for t in policy.factor_rule.lattice if t <= 240)))
        feature = replace(feature, public_source=replace(feature.public_source, policy=policy),
            values=tuple((key, feature.public_source.coordinate.physical_time(240) if key == "cutoff" else value)
                for key, value in feature.values))
        operands["feature"] = stored(case, feature, "independent.feature.cutoff240",
            task=owner.feature_task_id(source.root_id))
    selected = prepared(case, config(case, "forecast", mode=role, root=source.root.root), operands)
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)


@pytest.mark.parametrize("name", ("missing-root", "duplicate-root", "wrong-outcome-task", "foreign-pair"))
def test_calibration_requires_every_actual_root_and_its_current_paired_receipt(case, fitted, sequence, name):
    fs, ys = list(sequence.forecasts["calibration"]), list(sequence.outcomes["calibration"])
    if name == "missing-root":
        fs.pop()
    elif name == "duplicate-root":
        last, first = fs[-1], fs[0]
        fs[-1] = stored(case, first.record, "independent.forecast.duplicate-root",
            access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY,
            task=last.receipt.task_id)
        assert last.record.feature.unit_id != first.record.feature.unit_id
    elif name == "wrong-outcome-task":
        ys[0] = stored(case, ys[0].record, "independent.outcome.foreign-task",
            access=Access.EVALUATION_SEALED, ceiling=Visibility.DEVELOPMENT_ONLY,
            task="literal.foreign.response", output="outcome")
    else:
        ys[0] = stored(case, replace(ys[0].record, forecast=science.identity(fs[1].record)),
            "independent.outcome.foreign-pair", access=Access.EVALUATION_SEALED,
            ceiling=Visibility.DEVELOPMENT_ONLY, task=ys[0].receipt.task_id, output="outcome")
    operands = {**fitted.common, "models": fitted.models, "frozen": fitted.frozen,
        "forecasts": tuple(fs), "outcomes": tuple(ys)}
    if name == "duplicate-root":
        # Exact per-root input names let the existing ExecutionTask owner refuse
        # this duplication before a worker invocation can even be prepared.
        with pytest.raises(ValueError, match="scientific consumer inputs must be unique"):
            prepared(case, config(case, "calibrate"), operands)
        return
    selected = prepared(case, config(case, "calibrate"), operands)
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)


def test_forecast_worker_interface_contains_no_native_or_training_payload(case, fitted):
    source, operands = _forecast_operands(case, fitted)
    selected = prepared(case, config(case, "forecast", mode="calibration", root=source.root.root), operands)
    assert tuple(field.name for field in fields(selected.config)) == (
        "record_id", "operation", "specification", "allocation", "query_census", "mode", "root")
    config_port, = (port for port in selected.context.input_ports
        if port.artifact_id == selected.context.config.artifact_id)
    scientific = validated_scientific_input_edges(selected.context, config_port=config_port)
    assert sum(edge.scientific_role is ScientificInputRole.CONFIGURATION
        for edge in selected.task.scientific_inputs) == 1
    assert len(scientific) == 5
    assert {edge.consumer_input_id for edge in scientific} == {
        "specification", "allocation", "models", "frozen", "feature"}
    assert all(not hasattr(operands["feature"].record, name) for name in (
        "streams", "checkpoint", "native_manifest", "native_specification", "compact_source"))
    for port in selected.context.input_ports:
        port.close()
