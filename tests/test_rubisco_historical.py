"""Exposed E1 preservation, information roles and rank-one limits."""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
from io import BytesIO
import json
from xml.etree.ElementTree import Element, SubElement, tostring

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.rubisco_historical.analysis import (
    commit_forecasts, evaluate, fit, predict, rank_one_feasibility, rr2018_science,
)
from empirical_lawhood.adapters.methods.rubisco_historical.records import (
    BaselineV1, HistoricalEvaluationV1, HistoricalFittedModelV1,
    HistoricalFoldForecastsV1, HistoricalFoldV1, HistoricalForecastCommitmentV1,
    HistoricalScienceV1, RankOneFeasibilityV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
    ReportedEndpointsV1, ReportedSubstitutionV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import Rr2018NativeAuditV1
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity


def endpoint(sample: str, turnover: str, specificity: str) -> ReportedEndpointsV1:
    return ReportedEndpointsV1(sample, Decimal(turnover), Decimal(specificity))


@pytest.fixture
def e1():
    # These already exposed means are a software fixture, not newly acquired
    # biological observations or a signed source/publication claim.
    source = ObjectIdentity("synthetic-exposed-audit", Rr2018NativeAuditV1.SCHEMA, "1.0.0", "a" * 64)
    features = (ReportedSubstitutionV1("d206e", "D206E"), ReportedSubstitutionV1("m100t", "M100T"),
                ReportedSubstitutionV1("wt", "WT"))
    endpoints = (endpoint("d206e", "14.1", "12.1"), endpoint("m100t", "10.6", "11.7"),
                 endpoint("wt", "13.1", "12.3"))
    folds = (HistoricalFoldV1("site100", ("d206e", "wt"), ("m100t",), "wt"),
             HistoricalFoldV1("site206", ("m100t", "wt"), ("d206e",), "wt"))
    science = HistoricalScienceV1("synthetic.exposed-e1", source, folds, features)
    training, targets, labels = [], [], []
    for fold in folds:
        training.append(HistoricalTrainingSliceV1(f"training.{fold.fold_id}", fold.fold_id, source,
            tuple(f for f in features if f.sample_id in fold.training_sample_ids),
            tuple(e for e in endpoints if e.sample_id in fold.training_sample_ids)))
        targets.append(HistoricalFeatureSliceV1(f"features.{fold.fold_id}", fold.fold_id, source,
            tuple(f for f in features if f.sample_id in fold.target_sample_ids)))
        labels.append(HistoricalLabelSliceV1(f"labels.{fold.fold_id}", fold.fold_id, source,
            tuple(e for e in endpoints if e.sample_id in fold.target_sample_ids)))
    return science, tuple(training), tuple(targets), tuple(labels)


def committed(e1):
    science, training, targets, _ = e1
    models = tuple(fit(science, item) for item in training)
    forecasts = tuple(HistoricalFoldForecastsV1(fold.fold_id, predict(science, model, features))
                      for fold, model, features in zip(science.folds, models, targets, strict=True))
    return models, commit_forecasts(science, forecasts)


def test_exposed_two_folds_all_six_forecasts_preserve_null_added_value(e1):
    science, _, _, labels = e1
    _, commitment = committed(e1)
    evaluation = evaluate(science, commitment, labels)
    assert len(commitment.fold_forecasts) == 2
    assert len(evaluation.errors) == 6 and evaluation.paired_table_contrasts == 2
    assert evaluation.all_methods_identical
    assert evaluation.independent_biological_units == 0
    assert evaluation.joint_coverage is None and evaluation.interval_width is None
    assert evaluation.biological_gate.startswith("UNEVALUABLE")
    for error in evaluation.errors:
        assert error.forecast.endpoints.turnover_s_inv == Decimal("13.1")
        assert error.forecast.endpoints.specificity_dimensionless == Decimal("12.3")
        if error.observed.sample_id == "m100t":
            assert not error.jointly_within_point_tolerance
            assert float(error.turnover_relative_error) == pytest.approx(.2358490566037736)
            assert float(error.specificity_relative_error) == pytest.approx(.05128205128205128)
            assert float(error.turnover_log_contrast_error) == pytest.approx(.2117582291, abs=1e-10)
            assert float(error.specificity_log_contrast_error) == pytest.approx(.0500104206, abs=1e-10)
        else:
            assert error.observed.sample_id == "d206e" and error.jointly_within_point_tolerance
    assert {e.forecast.method for e in evaluation.errors} == set(BaselineV1)


def test_fit_and_predict_refuse_target_label_information_roles(e1):
    science, training, targets, labels = e1
    with pytest.raises(ValueError, match="training role"):
        fit(science, labels[0])
    with pytest.raises(ValueError, match="training role"):
        fit(science, targets[0])
    model = fit(science, training[0])
    with pytest.raises(ValueError, match="never target labels"):
        predict(science, model, labels[0])
    all_features = tuple(sorted((*training[0].features, *targets[0].features), key=lambda f: f.sample_id))
    all_labels = tuple(sorted((*training[0].endpoints, *labels[0].endpoints), key=lambda e: e.sample_id))
    injected = replace(training[0], features=all_features, endpoints=all_labels)
    with pytest.raises(ValueError, match="training roster"):
        fit(science, injected)
    document = json.loads(science.canonical_bytes())
    document["value"]["target_labels"] = labels[0].to_document()
    with pytest.raises(ValueError):
        decode_canonical_bytes(json.dumps(document).encode(), HistoricalScienceV1, maximum_bytes=65536)


def test_label_change_cannot_change_already_frozen_forecasts(e1):
    science, _, targets, labels = e1
    models, commitment = committed(e1)
    changed = tuple(replace(item, endpoints=tuple(replace(e, turnover_s_inv=e.turnover_s_inv * 2)
                                                for e in item.endpoints)) for item in labels)
    assert evaluate(science, commitment, changed) != evaluate(science, commitment, labels)
    for bundle, model, features in zip(commitment.fold_forecasts, models, targets, strict=True):
        assert predict(science, model, features) == bundle.forecasts
    assert b'"observed"' not in commitment.canonical_bytes()
    assert b'"training"' not in commitment.canonical_bytes()
    assert b'"labels"' not in commitment.canonical_bytes()


def test_global_barrier_refuses_before_any_label_access(e1):
    science = e1[0]
    _, commitment = committed(e1)
    incomplete = replace(commitment, fold_forecasts=commitment.fold_forecasts[:1])
    class ForbiddenLabels:
        def __iter__(self):
            raise AssertionError("labels opened before all folds were committed")
    with pytest.raises(ValueError, match="global forecast barrier"):
        evaluate(science, incomplete, ForbiddenLabels())
    without_method = replace(commitment.fold_forecasts[0], forecasts=commitment.fold_forecasts[0].forecasts[:-1])
    with pytest.raises(ValueError, match="baseline forecast"):
        commit_forecasts(science, (without_method, commitment.fold_forecasts[1]))


def test_model_fold_features_and_source_cannot_be_substituted(e1):
    science, training, targets, _ = e1
    models, _ = committed(e1)
    with pytest.raises(ValueError, match="prediction changes"):
        predict(science, models[1], targets[0])
    foreign = replace(science.source, object_fingerprint="b" * 64)
    with pytest.raises(ValueError, match="source"):
        fit(science, replace(training[0], source=foreign))
    with pytest.raises(ValueError, match="prediction changes"):
        predict(science, models[0], replace(targets[0], source=foreign))
    with pytest.raises(ValueError, match="target features"):
        predict(science, models[0], replace(targets[0], features=(ReportedSubstitutionV1("m100t", "M100A"),)))


def test_nearest_keeps_every_exact_tie_and_uses_geometric_mean():
    source = ObjectIdentity("synthetic.ties", Rr2018NativeAuditV1.SCHEMA, "1.0.0", "a" * 64)
    features = (ReportedSubstitutionV1("a", "M100T"), ReportedSubstitutionV1("b", "M300A"),
                ReportedSubstitutionV1("target", "M200S"), ReportedSubstitutionV1("wt", "WT"))
    endpoints = (endpoint("a", "16", "36"), endpoint("b", "64", "144"), endpoint("wt", "4", "9"))
    fold = HistoricalFoldV1("ties", ("a", "b", "wt"), ("target",), "wt")
    science = HistoricalScienceV1("synthetic.ties.science", source, (fold,), features)
    training = HistoricalTrainingSliceV1("synthetic.ties.training", "ties", source,
                                        (features[0], features[1], features[3]), endpoints)
    targets = HistoricalFeatureSliceV1("synthetic.ties.features", "ties", source, (features[2],))
    forecasts = predict(science, fit(science, training), targets)
    nearest = next(f for f in forecasts if f.method is BaselineV1.NEAREST)
    assert float(nearest.endpoints.turnover_s_inv) == pytest.approx(16)
    assert float(nearest.endpoints.specificity_dimensionless) == pytest.approx(36)
    assert nearest.endpoints.turnover_s_inv not in (Decimal(4), Decimal(64))


def test_ridge_solution_matches_independent_one_row_formula(e1):
    science, training, targets, _ = e1
    for item in training:
        model = fit(science, item)
        mutant = next(e for e in item.endpoints if e.sample_id != "wt")
        vector = np.asarray(next(f.vector() for f in item.features if f.sample_id != "wt"), dtype=float)
        y = np.log((float(mutant.turnover_s_inv / model.parent.turnover_s_inv),
                    float(mutant.specificity_dimensionless / model.parent.specificity_dimensionless)))
        independent = vector[:, None] * y / (1 + vector @ vector)
        actual = np.asarray(model.ridge_coefficients, dtype=float)
        assert actual == pytest.approx(independent, abs=1e-16)


def test_exact_m100t_opposite_sign_proof_and_required_intervals():
    proof = rank_one_feasibility(endpoint("wt", "13.1", "12.3"), endpoint("d206e", "14.1", "12.1"),
                                  endpoint("m100t", "10.6", "11.7"))
    assert proof.disposition == "INCOMPATIBLE"
    assert "EXACT_OPPOSITE_REQUIRED_SCALAR_SIGNS" in proof.reason_codes
    assert tuple(float(v) for v in (proof.turnover_scalar_interval.lower, proof.turnover_scalar_interval.upper)) == pytest.approx((-4.3108711, -1.5829797), abs=1e-7)
    assert tuple(float(v) for v in (proof.specificity_scalar_interval.lower, proof.specificity_scalar_interval.upper)) == pytest.approx((1.2475208, 4.9085374), abs=1e-7)
    # This exact rational argument does not depend on Decimal ln/exp output.
    assert Decimal("10.6") * Decimal("1.10") < Decimal("13.1") < Decimal("14.1")
    assert Decimal("11.7") * Decimal("1.03") < Decimal("12.3") > Decimal("12.1")


def test_rank_one_can_pass_two_endpoints_on_its_response_direction():
    parent = endpoint("wt", "10", "20")
    training = endpoint("training", "20", "10")
    target = endpoint("target", "20", "10")
    proof = rank_one_feasibility(parent, training, target)
    assert proof.disposition == "ATTAINABLE"
    assert proof.turnover_scalar_interval.lower < 1 < proof.turnover_scalar_interval.upper
    assert proof.specificity_scalar_interval.lower < 1 < proof.specificity_scalar_interval.upper
    assert proof.claim_scope == "ONE_NONZERO_TRAINING_RESPONSE_SHARED_LINEAR_MAP_ONLY"


def test_zero_training_direction_is_unbounded_or_unattainable_not_nan():
    parent = endpoint("wt", "10", "20")
    training = endpoint("training", "10", "20")
    passing = rank_one_feasibility(parent, training, endpoint("target", "10", "20"))
    assert passing.disposition == "ATTAINABLE"
    assert passing.turnover_scalar_interval.state == passing.specificity_scalar_interval.state == "ALL_REAL"
    failing = rank_one_feasibility(parent, training, endpoint("target", "100", "20"))
    assert failing.disposition == "INCOMPATIBLE" and failing.turnover_scalar_interval.state == "EMPTY"
    assert b'Infinity' not in failing.canonical_bytes()


def test_unresolved_subprecision_training_direction_does_not_become_exact_zero():
    proof = rank_one_feasibility(endpoint("wt", "1", "2"),
                                  endpoint("training", "1." + "0" * 80 + "1", "2"),
                                  endpoint("target", "1", "2"))
    assert proof.disposition == "UNRESOLVED_NUMERICAL_BOUNDARY"
    assert proof.turnover_scalar_interval.state == "UNRESOLVED"


def test_strict_successor_records_round_trip_and_refuse_coverage_promotion(e1):
    science, _, _, labels = e1
    models, commitment = committed(e1)
    evaluation = evaluate(science, commitment, labels)
    proof = rank_one_feasibility(models[0].parent, models[0].training.endpoints[0], labels[0].endpoints[0])
    for record, record_type in ((science, HistoricalScienceV1), (models[0], HistoricalFittedModelV1),
                                (commitment, HistoricalForecastCommitmentV1), (evaluation, HistoricalEvaluationV1),
                                (proof, RankOneFeasibilityV1)):
        assert decode_canonical_bytes(record.canonical_bytes(), record_type, maximum_bytes=65536) == record
    with pytest.raises(ValueError, match="cannot establish"):
        replace(evaluation, joint_coverage=Decimal("0.95"))
    with pytest.raises(ValueError, match="exposure"):
        replace(commitment, prior_biological_exposure="FRESH")


def test_complete_numerical_context_prevents_caller_precision_drift(e1):
    _, expected_commitment = committed(e1)
    expected_evaluation = evaluate(e1[0], expected_commitment, e1[3])
    expected_proof = rank_one_feasibility(endpoint("wt", "13.1", "12.3"), endpoint("d206e", "14.1", "12.1"),
                                           endpoint("m100t", "10.6", "11.7"))
    with localcontext() as context:
        context.prec = 3
        _, actual_commitment = committed(e1)
        actual_evaluation = evaluate(e1[0], actual_commitment, e1[3])
        actual_proof = rank_one_feasibility(endpoint("wt", "13.1", "12.3"), endpoint("d206e", "14.1", "12.1"),
                                             endpoint("m100t", "10.6", "11.7"))
    assert (actual_commitment, actual_evaluation, actual_proof) == (expected_commitment, expected_evaluation, expected_proof)


def test_exact_rr2018_builder_refuses_another_article_record():
    # Actual byte authentication belongs to the source adapter; this method
    # cannot accept a different record type merely bearing a familiar ID.
    with pytest.raises(ValueError, match="exact retained"):
        rr2018_science(ObjectIdentity("wrong", Rr2018NativeAuditV1.SCHEMA, "1.0.0", "a" * 64))


class CountingReader(BytesIO):
    total_read = 0

    @property
    def bytes_read(self):
        return self.total_read

    def read(self, size=-1):
        value = super().read(size)
        self.total_read += len(value)
        return value


def worker_context(role, config, records):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import (
        MEDIA_TYPE, PHASES, operation_declarations,
    )
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.execution import (
        DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind,
        WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
    )
    runner = next(declaration.runner_factory() for declaration in operation_declarations()
                  if declaration.capability_key.endswith(f".{role}"))
    row = next(row for row in PHASES if row[0] == role)
    inputs = [(config.config_id, config, False), *records]
    ports, readers, receipts = [], {}, []
    for key, record, dependency in sorted(inputs, key=lambda item: item[0]):
        payload = record.canonical_bytes()
        materialization = f"material.{key}"
        binding = WorkerInputBinding(key, materialization, record.SCHEMA, MEDIA_TYPE, len(payload),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE,
            WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL)
        readers[key] = CountingReader(payload)
        ports.append(WorkerInputPort(binding, readers[key]))
        if dependency:
            receipts.append(DependencyReceiptBinding(f"receipt.{key}", f"producer.{key}", (materialization,)))
    context = TaskContext("synthetic.historical.run", f"synthetic.{role}", f"synthetic.{role}.attempt",
        CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
                            config.fingerprint(), config.config_id),
        tuple(port.binding for port in ports), tuple(ports),
        tuple(WorkerOutputPort(f"synthetic.{role}.{name}", record.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA_TYPE)
              for name, record in row[3]),
        runner.manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, runner.manifest.resource_ceiling,
        WorkerIsolationProfile.TRUSTED_LOCAL, tuple(sorted(receipts, key=lambda value: value.receipt_id)))
    return runner, context, readers, row[3][0][1]


def run_worker(role, config, records):
    runner, context, readers, output_type = worker_context(role, config, records)
    result = runner.execute(context)
    return decode_canonical_bytes(result.outputs[0].payload, output_type, maximum_bytes=4 * 1024**2), readers


def test_actual_registered_stages_preserve_six_forecasts_and_global_barrier(e1):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import (
        HistoricalCommitConfigV1, HistoricalEvaluateConfigV1, HistoricalFitConfigV1, HistoricalPredictConfigV1,
    )
    science, training, targets, labels = e1
    bundles = []
    for item, features in zip(training, targets, strict=True):
        model, _ = run_worker("fit", HistoricalFitConfigV1(f"config.fit.{item.fold_id}", science, item.fold_id),
                              [(f"input.training.{item.fold_id}", item, False)])
        forecasts, _ = run_worker("predict", HistoricalPredictConfigV1(f"config.predict.{item.fold_id}", science, item.fold_id),
                                  [(f"input.model.{item.fold_id}", model, True),
                                   (f"input.features.{item.fold_id}", features, False)])
        bundles.append(forecasts)
    commitment, _ = run_worker("commit", HistoricalCommitConfigV1("config.commit", science),
                               [(f"input.forecasts.{f.fold_id}", f, True) for f in bundles])
    evaluation, readers = run_worker("evaluate", HistoricalEvaluateConfigV1("config.evaluate", science),
        [("z.commitment", commitment, True), *((f"a.labels.{label.fold_id}", label, False) for label in labels)])
    assert len(evaluation.errors) == 6 and evaluation.all_methods_identical
    assert all(reader.closed for reader in readers.values())
    assert all(reader.bytes_read > 0 for reader in readers.values())


def test_evaluate_worker_checks_incomplete_global_commit_before_label_bytes(e1):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import HistoricalEvaluateConfigV1
    science, _, _, labels = e1
    _, commitment = committed(e1)
    incomplete = replace(commitment, fold_forecasts=commitment.fold_forecasts[:1])
    runner, context, readers, _ = worker_context("evaluate", HistoricalEvaluateConfigV1("config.evaluate", science),
        [("z.commitment", incomplete, True), *((f"a.labels.{label.fold_id}", label, False) for label in labels)])
    with pytest.raises(ValueError, match="global forecast barrier"):
        runner.execute(context)
    assert readers["z.commitment"].bytes_read > 0
    assert all(readers[f"a.labels.{label.fold_id}"].bytes_read == 0 for label in labels)
    assert all(reader.closed for reader in readers.values())


def test_forecast_worker_refuses_label_injection_before_any_data_reads(e1):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import HistoricalPredictConfigV1
    science, _, targets, labels = e1
    models, _ = committed(e1)
    runner, context, readers, _ = worker_context("predict", HistoricalPredictConfigV1("config.predict", science, "site100"),
        [("input.model", models[0], True), ("input.features", targets[0], False), ("input.labels", labels[0], False)])
    with pytest.raises(ValueError, match="undeclared label/oracle"):
        runner.execute(context)
    assert all(reader.bytes_read == 0 for reader in readers.values())


def test_evaluation_worker_refuses_external_commitment_without_receipt_before_reads(e1):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import HistoricalEvaluateConfigV1
    science, _, _, labels = e1
    _, commitment = committed(e1)
    runner, context, readers, _ = worker_context("evaluate", HistoricalEvaluateConfigV1("config.evaluate", science),
        [("z.commitment", commitment, False), *((f"a.labels.{label.fold_id}", label, False) for label in labels)])
    with pytest.raises(ValueError, match="receipt-bound predecessor"):
        runner.execute(context)
    assert all(reader.bytes_read == 0 for reader in readers.values())


def test_historical_binding_construction_is_cold_and_complete(monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_historical import analysis, operation_bindings
    from empirical_lawhood.adapters.methods.rubisco_historical.executable_binding import EXECUTABLE_BINDING_FACTORIES
    from empirical_lawhood.adapters.methods.rubisco_historical.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import (
        operation_declarations, output_codecs,
    )
    from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
    def forbidden(*args):
        raise AssertionError("cold construction entered science")
    for function in ("fit", "predict", "commit_forecasts", "evaluate", "rr2018_science"):
        monkeypatch.setattr(analysis, function, forbidden)
    monkeypatch.setattr(operation_bindings, "prepare_source", forbidden)
    assert len(tuple(declaration.manifest() for declaration in operation_declarations())) == len(tuple(declaration.registration() for declaration in operation_declarations())) == len(tuple(declaration.runner_factory() for declaration in operation_declarations())) == 5
    assert len(EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests) == len(EXECUTABLE_BINDING_FACTORIES) == 5
    assert len(output_codecs()) == 9
    assert all(output_codecs()[record.SCHEMA] is record for record in (
        HistoricalTrainingSliceV1, HistoricalFeatureSliceV1, HistoricalLabelSliceV1))
    assert all(not registration.native_effect for registration in tuple(declaration.registration() for declaration in operation_declarations()))
    assessment = next(value for value in tuple(declaration.registration() for declaration in operation_declarations()) if value.config_record_type.SCHEMA.endswith("evaluate-config"))
    assert assessment.stage is ScientificStage.FALSIFY and assessment.barrier is BarrierKind.NONE
    assert all(factory.runner_factory().manifest == factory.manifest for factory in EXECUTABLE_BINDING_FACTORIES)


def root_contexts(science, *, source_linked=False):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import (
        MEDIA_TYPE, historical_development_root, operation_declarations, scientific_unit_ids,
    )
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import (
        HistoricalCommitConfigV1, HistoricalEvaluateConfigV1, HistoricalFitConfigV1, HistoricalPredictConfigV1,
    )
    from empirical_lawhood.adapters.methods.rubisco_historical.source_binding import HistoricalSourceConfigV1
    from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink
    from empirical_lawhood.runtime.plans import ExternalInputSpec
    from empirical_lawhood.runtime.recursive_compiler import RecursiveConfigInput, RecursiveScientificRootContext
    configs, links = [], []
    for fold in science.folds:
        configs.extend(((f"fit.{fold.fold_id}", HistoricalFitConfigV1(f"config.fit.{fold.fold_id}", science, fold.fold_id)),
                        (f"predict.{fold.fold_id}", HistoricalPredictConfigV1(f"config.predict.{fold.fold_id}", science, fold.fold_id))))
        links.extend((RecursiveInputLink(f"edge.training.{fold.fold_id}", f"fit.{fold.fold_id}", "training",
                                         external_input_id=f"training.{fold.fold_id}"),
                      RecursiveInputLink(f"edge.features.{fold.fold_id}", f"predict.{fold.fold_id}", "features",
                                         external_input_id=f"features.{fold.fold_id}"),
                      RecursiveInputLink(f"edge.model.{fold.fold_id}", f"predict.{fold.fold_id}", "model",
                                         f"fit.{fold.fold_id}", "model"),
                      RecursiveInputLink(f"edge.forecasts.{fold.fold_id}", "commit", f"forecasts.{fold.fold_id}",
                                         f"predict.{fold.fold_id}", "forecasts"),
                      RecursiveInputLink(f"edge.labels.{fold.fold_id}", "evaluate", f"labels.{fold.fold_id}",
                                         external_input_id=f"labels.{fold.fold_id}")))
    configs.extend((("commit", HistoricalCommitConfigV1("config.commit", science)),
                    ("evaluate", HistoricalEvaluateConfigV1("config.evaluate", science))))
    links.append(RecursiveInputLink("edge.commitment", "evaluate", "commitment", "commit", "commitment"))
    if source_linked:
        configs.insert(0, ("source", HistoricalSourceConfigV1("config.source", science)))
        links = [replace(link, external_input_id=None, producer_node_id="source",
                         producer_output_id=link.external_input_id)
                 if link.external_input_id is not None else link for link in links]
        links.append(RecursiveInputLink("edge.article", "source", "article", external_input_id="article"))
    registrations = {registration.config_record_type: registration for registration in tuple(declaration.registration() for declaration in operation_declarations())}
    root = historical_development_root(science)
    rows = tuple(RecursiveConfigInput(node, config.config_id,
        ExternalInputSpec("config", config.config_id, config.fingerprint(), config.SCHEMA, MEDIA_TYPE,
                          len(config.canonical_bytes()), registrations[type(config)].visibility_ceiling,
                          registrations[type(config)].outcome_access, None),
                          config.canonical_bytes(), config, type(config))
        for node, config in configs)
    contexts = []
    for node, config in configs:
        registration = registrations[type(config)]
        contexts.append((config, RecursiveScientificRootContext(root, node, registration.stage,
            registration.outcome_access, registration.visibility_ceiling, scientific_unit_ids(config),
            scientific_unit_ids(config), False, (), (), (), (), rows, tuple(links))))
    return contexts


def test_exact_analysis_root_and_role_joins_refuse_world_science_or_barrier_substitution(e1):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import scientific_root_validator
    from empirical_lawhood.kernel.worlds import WorldKind
    contexts = root_contexts(e1[0])
    for config, context in contexts:
        assert scientific_root_validator(config, context) is None
    config, context = contexts[-1]
    with pytest.raises(ValueError, match="exact analysis root"):
        scientific_root_validator(config, replace(context, root=replace(context.root, world_kind=WorldKind.NUMERICAL_SIMULATOR)))
    with pytest.raises(ValueError, match="exact analysis root"):
        scientific_root_validator(config, replace(context, root=replace(context.root, scientific_operands=context.root.scientific_operands[:1])))
    changed_links = tuple(link for link in context.links if link.edge_id != "edge.commitment")
    with pytest.raises(ValueError, match="global-commit/label census"):
        scientific_root_validator(config, replace(context, links=changed_links))
    commit_config, commit_context = contexts[-2]
    missing = tuple(link for link in commit_context.links if link.edge_id != "edge.forecasts.site206")
    with pytest.raises(ValueError, match="omits a required forecast fold"):
        scientific_root_validator(commit_config, replace(commit_context, links=missing))


@pytest.fixture
def source_fixture(monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_historical import analysis, source_binding
    from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import DOI, HEADERS, LABELS, decode_rr2018
    # The hash is overridden only within this synthetic software fixture. Real
    # execution accepts exclusively the actual retained article digest.
    root = Element("article")
    meta = SubElement(SubElement(root, "front"), "article-meta")
    SubElement(meta, "article-id", {"pub-id-type": "doi"}).text = DOI
    table = SubElement(SubElement(root, "table-wrap", {"id": "Tab1"}), "table")
    points = {"RubRr": ("13.1", "12.3"), "Clone 11": ("10.6", "11.7"), "Clone 27": ("14.1", "12.1")}
    native = []
    for label in LABELS:
        turnover, specificity = points.get(label, ("1", "2"))
        native.append((label, "synthetic", "1", "1 ± 0", f"{specificity} ± 0.1", "1 ± 0",
                       f"{turnover} ± 0.2", "1 ± 0", "1 ± 0"))
    for cells in (HEADERS, *native):
        row = SubElement(table, "tr")
        for value in cells:
            SubElement(row, "td").text = value
    payload = tostring(root, encoding="utf-8")
    digest = sha256(payload).hexdigest()
    monkeypatch.setattr(source_binding, "SOURCE_SHA256", digest)
    monkeypatch.setattr(analysis, "SOURCE_SHA256", digest)
    audit = decode_rr2018(payload, expected_sha256=digest)
    science = analysis.rr2018_science(audit)
    article = source_binding.Rr2018ArticleInputV1("synthetic.article", digest, payload.decode("utf-8"))
    config = source_binding.HistoricalSourceConfigV1("synthetic.config.source", science)
    return config, article, audit


def test_source_input_preserves_exact_utf8_bytes_and_refuses_changed_or_unbounded_input():
    from empirical_lawhood.adapters.methods.rubisco_historical.source_binding import Rr2018ArticleInputV1
    from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import MAX_INPUT_BYTES
    raw = "<article>°±μ\r\n</article>"
    record = Rr2018ArticleInputV1("synthetic.utf8", sha256(raw.encode()).hexdigest(), raw)
    assert decode_canonical_bytes(record.canonical_bytes(), Rr2018ArticleInputV1, maximum_bytes=4096) == record
    with pytest.raises(ValueError, match="exact-byte identity"):
        replace(record, raw_xml_utf8=raw.replace("\r\n", "\n"))
    with pytest.raises(ValueError, match="UTF-8"):
        Rr2018ArticleInputV1("synthetic.badutf8", "a" * 64, "\ud800")
    # Character count alone cannot enforce the native byte limit.
    many_bytes = "μ" * (MAX_INPUT_BYTES // 2 + 1)
    with pytest.raises(ValueError, match="bounded exact-byte identity"):
        Rr2018ArticleInputV1("synthetic.toobig", sha256(many_bytes.encode()).hexdigest(), many_bytes)


def test_source_stage_refuses_another_hash_before_native_decode(e1, monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_historical import source_binding
    raw = "<article/>"
    article = source_binding.Rr2018ArticleInputV1("synthetic.wrong", sha256(raw.encode()).hexdigest(), raw)
    config = source_binding.HistoricalSourceConfigV1("synthetic.config", e1[0])
    def forbidden(*args, **kwargs):
        raise AssertionError("source decoding entered before exact retained digest check")
    monkeypatch.setattr(source_binding, "decode_rr2018", forbidden)
    with pytest.raises(ValueError, match="actual retained raw-source digest"):
        source_binding.prepare_source(config, article)


def test_registered_source_stage_emits_exact_separate_roles_then_runs_historical_barrier(source_fixture):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import (
        HistoricalCommitConfigV1, HistoricalEvaluateConfigV1, HistoricalFitConfigV1, HistoricalPredictConfigV1,
    )
    from empirical_lawhood.adapters.methods.rubisco_historical.source_binding import SOURCE_OUTPUTS
    config, article, expected_audit = source_fixture
    runner, context, readers, _ = worker_context("source", config, [("article", article, False)])
    result = runner.execute(context)
    assert tuple(output.output_id for output in result.outputs) == tuple(f"{context.task_id}.{name}" for name, _ in SOURCE_OUTPUTS)
    products = {name: decode_canonical_bytes(output.payload, record, maximum_bytes=4 * 1024**2)
                for output, (name, record) in zip(result.outputs, SOURCE_OUTPUTS, strict=True)}
    assert products["audit"] == expected_audit
    assert not products["audit"].supplement_bytes_verified
    assert not products["audit"].physical_independent_units_known
    assert all(reader.closed and reader.bytes_read > 0 for reader in readers.values())
    science = config.science
    bundles = []
    for fold in science.folds:
        training, features = products[f"training.{fold.fold_id}"], products[f"features.{fold.fold_id}"]
        assert {e.sample_id for e in training.endpoints}.isdisjoint(f.sample_id for f in features.features)
        assert b'"endpoints"' not in features.canonical_bytes()
        model, _ = run_worker("fit", HistoricalFitConfigV1(f"config.fit.{fold.fold_id}", science, fold.fold_id),
                              [(f"training.{fold.fold_id}", training, True)])
        forecasts, _ = run_worker("predict", HistoricalPredictConfigV1(f"config.predict.{fold.fold_id}", science, fold.fold_id),
                                  [(f"model.{fold.fold_id}", model, True),
                                   (f"features.{fold.fold_id}", features, True)])
        bundles.append(forecasts)
    commitment, _ = run_worker("commit", HistoricalCommitConfigV1("config.commit", science),
                               [(f"forecasts.{f.fold_id}", f, True) for f in bundles])
    evaluation, _ = run_worker("evaluate", HistoricalEvaluateConfigV1("config.evaluate", science),
        [("commitment", commitment, True), *((f"labels.{fold.fold_id}", products[f"labels.{fold.fold_id}"], True)
                                             for fold in science.folds)])
    assert len(evaluation.errors) == 6 and evaluation.all_methods_identical
    assert {error.forecast.endpoints.turnover_s_inv for error in evaluation.errors} == {Decimal("13.1")}
    assert {error.forecast.endpoints.specificity_dimensionless for error in evaluation.errors} == {Decimal("12.3")}
    assert all(error.jointly_within_point_tolerance == (error.observed.sample_id == "d206e")
               for error in evaluation.errors)


def test_source_stage_refuses_science_audit_identity_substitution(source_fixture):
    from empirical_lawhood.adapters.methods.rubisco_historical.source_binding import prepare_source
    config, article, _ = source_fixture
    changed_source = replace(config.science.source, object_fingerprint="b" * 64)
    changed = replace(config, science=replace(config.science, source=changed_source))
    with pytest.raises(ValueError, match="exact audit/science/root source identity"):
        prepare_source(changed, article)


def test_source_linked_roots_require_exact_fold_role_and_declared_article_port(source_fixture):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import scientific_root_validator
    contexts = root_contexts(source_fixture[0].science, source_linked=True)
    for config, context in contexts:
        assert scientific_root_validator(config, context) is None
    source_config, source_context = contexts[0]
    changed = tuple(replace(link, consumer_input_id="filepath") if link.consumer_node_id == "source" else link
                    for link in source_context.links)
    with pytest.raises(ValueError, match="sole external raw-article role"):
        scientific_root_validator(source_config, replace(source_context, links=changed))
    for node, output in (("fit.site100", "training.site206"), ("predict.site100", "labels.site100"),
                         ("evaluate", "labels.site206")):
        config, context = next((config, context) for config, context in contexts if context.node_id == node)
        changed = tuple(replace(link, producer_output_id=output)
                        if link.consumer_node_id == node and link.producer_output_id.endswith("site100") else link
                        for link in context.links)
        with pytest.raises(ValueError, match="exact source-preparation output"):
            scientific_root_validator(config, replace(context, links=changed))


def test_historical_runners_use_exact_compiler_output_contracts_for_source_and_fit(source_fixture):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_bindings import (
        operation_declarations, output_codecs,
    )
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import HistoricalFitConfigV1
    from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
    from empirical_lawhood.adapters.methods.rubisco_historical.source_binding import SOURCE_OUTPUTS
    from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import role_slices
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.execution import WorkerOutputPort
    from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    config, article, audit = source_fixture
    draft = historical_recursive_draft(config.science, role_slices(audit), article_input=article)
    compiled = compile_recursive_wave(draft=draft, registrations=tuple(declaration.registration() for declaration in operation_declarations()),
        registry=CapabilityRegistry("registry.synthetic-compiler-output-test",
            tuple(sorted(tuple(declaration.manifest() for declaration in operation_declarations()), key=lambda value: value.registry_id))),
        implementation_commit="a" * 40, output_codecs=output_codecs())
    assert len(compiled.execution_plan.tasks) == 7
    assessment = next(task for task in compiled.execution_plan.tasks if task.task_id.endswith(".evaluate"))
    commitment = next(task for task in compiled.execution_plan.tasks if task.task_id.endswith(".commit"))
    assert assessment.stage is ScientificStage.FALSIFY and assessment.barrier is BarrierKind.NONE
    assert commitment.barrier is BarrierKind.FREEZE and commitment.task_id in assessment.dependency_task_ids
    assert assessment.capability.requested_outcome_access is commitment.capability.requested_outcome_access
    assert all(task.barrier is not BarrierKind.REVEAL for task in compiled.execution_plan.tasks)
    inputs = {row.node_id: row.record for row in compiled.config_inputs}
    source_task = next(task for task in compiled.execution_plan.tasks if task.task_id.endswith(".source"))
    runner, context, _, _ = worker_context("source", inputs[source_task.task_id], [(article.input_id, article, False)])

    def actual_context(context, task):
        # Use the materialized compiler output objects just as the shared
        # executor does, rather than reconstructing the runner's expectation.
        return replace(context, task_id=task.task_id, config=task.capability.config,
            output_ports=tuple(WorkerOutputPort(output.output_id, output.payload_schema, output.profile,
                                                output.media_type, output.logical_artifact_id)
                               for output in task.outputs))

    result = runner.execute(actual_context(context, source_task))
    assert tuple(output.output_id for output in result.outputs) == tuple(output.output_id for output in source_task.outputs)
    products = {name: decode_canonical_bytes(output.payload, record, maximum_bytes=4 * 1024**2)
                for output, (name, record) in zip(result.outputs, SOURCE_OUTPUTS, strict=True)}
    for fit_task in (task for task in compiled.execution_plan.tasks if task.task_id.endswith(".fit")):
        fit_config = inputs[fit_task.task_id]
        assert type(fit_config) is HistoricalFitConfigV1
        training = products[f"training.{fit_config.fold_id}"]
        runner, context, _, _ = worker_context("fit", fit_config, [(training.slice_id, training, True)])
        result = runner.execute(actual_context(context, fit_task))
        assert tuple(output.output_id for output in result.outputs) == tuple(output.output_id for output in fit_task.outputs)
        model = decode_canonical_bytes(result.outputs[0].payload, HistoricalFittedModelV1, maximum_bytes=65536)
        assert model.training == training


@pytest.mark.parametrize("role", ("source", "fit"))
@pytest.mark.parametrize("prefix", ("", "unrelated.task."))
def test_output_namespace_substitution_refuses_before_reading_inputs(source_fixture, role, prefix):
    from empirical_lawhood.adapters.methods.rubisco_historical.operation_contracts import HistoricalFitConfigV1
    from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import role_slices
    config, article, audit = source_fixture
    if role == "source":
        records = [(article.input_id, article, False)]
    else:
        config = HistoricalFitConfigV1("synthetic.fit.config", config.science, "site100")
        training = next(record for record in role_slices(audit)
                        if isinstance(record, HistoricalTrainingSliceV1) and record.fold_id == "site100")
        records = [(training.slice_id, training, True)]
    runner, context, readers, _ = worker_context(role, config, records)
    changed = replace(context, output_ports=tuple(
        replace(port, output_id=prefix + port.output_id.removeprefix(context.task_id + "."))
        for port in context.output_ports))
    with pytest.raises(ValueError, match="exact typed output contract"):
        runner.execute(changed)
    assert all(reader.bytes_read == 0 and reader.closed for reader in readers.values())
