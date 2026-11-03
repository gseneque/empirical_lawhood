# SPDX-License-Identifier: MPL-2.0
"""Tiny exposed software controls, without optional receivers or response data."""

from dataclasses import replace
from decimal import Decimal
from importlib.metadata import PackageNotFoundError
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity

from empirical_lawhood.adapters.physical.virtual_cell.config import (
    EVALUATOR_CAPABILITY_KEY,
    MODEL_CAPABILITY_KEY,
    PREDICTION_CAPABILITY_KEY,
    SUMMARY_CAPABILITY_KEY,
    build_virtual_cell_2025_pipeline_config,
)
from empirical_lawhood.adapters.physical.virtual_cell.config_v2 import (
    VirtualCellPipelineSelectionV2,
    derive_pipeline_selection_v2,
)
from empirical_lawhood.adapters.physical.virtual_cell.contracts import (
    PredictionCommitment,
    VirtualCellContractError,
)
from empirical_lawhood.adapters.physical.virtual_cell.correction_records_v2 import (
    MetricSourceSemantics,
    OfficialMetricGaugeV2,
    OfficialMetricSetV2,
    SharedTemplateShiftV2BuildReceipt,
    SharedTemplateShiftV2Selection,
)
from empirical_lawhood.adapters.physical.virtual_cell import (
    receiver_readiness_v2 as readiness,
)
from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import (
    CandidateValidationRecordV2,
    ModelDevelopmentRecordV2,
    OfficialEvaluationRecordV2,
    PredictionFreezeRecordV2,
)


def _original_config():
    # Metadata-only constructor inputs: no original physical dataset or source claim.
    source = SimpleNamespace(fingerprint=lambda: "1" * 64)
    features = SimpleNamespace(
        arrow_sha256="2" * 64,
        feature_provenance_sha256="3" * 64,
        build_receipt_sha256="4" * 64,
    )
    leaderboard = SimpleNamespace(fingerprint=lambda: "5" * 64)
    return build_virtual_cell_2025_pipeline_config(
        source_manifest=source, feature_receipt=features, leaderboard=leaderboard
    )


def _selection(original=None):
    return derive_pipeline_selection_v2(
        selection_id="selection.exposed-v2",
        original_config=original or _original_config(),
        compiler=SharedTemplateShiftV2Selection(),
        metric_gauge=OfficialMetricGaugeV2(),
    )


def _build_receipt():
    selected = SharedTemplateShiftV2Selection()
    return SharedTemplateShiftV2BuildReceipt(
        selected.fingerprint(),
        "receipt.exposed",
        selected.compiler_id,
        selected.receiver_id,
        *("1" * 64 for _ in range(6)),
        3,
        2,
        1,
        1,
        2,
        Decimal(0),
        Decimal(0),
        0,
        Decimal(0),
        Decimal("14.999"),
        "float32",
        False,
    )


def _reference(schema, object_id, version="1.0.0", digest="1" * 64):
    return ObjectIdentity(object_id, schema, version, digest)


def test_extraction_preserves_exact_original_class_objects_and_canonical_goldens():
    from empirical_lawhood.adapters.physical.virtual_cell import (
        metric_correction_v2,
        prediction_v2,
    )

    values = (
        (
            SharedTemplateShiftV2Selection(),
            "e78370f22f2b980e5a7d509d9086ba8234ec66cc83717e1dcac2af882a59acde",
        ),
        (
            OfficialMetricGaugeV2(),
            "ab798ade2346a9ddd2145f89b3c58e77c835e2360b9f060185f365c19a892b37",
        ),
        (
            OfficialMetricSetV2(
                OfficialMetricGaugeV2(),
                MetricSourceSemantics.OFFICIAL_SOURCE_COLUMNS,
                None,
                ("target.exposed",),
                (Decimal("0.2"),),
                (Decimal("0.8"),),
                (Decimal("0.01"),),
            ),
            "52c095f613321c9ea6ce943a6e42c040798fc00279ea1c63eb10102dc906b29a",
        ),
        (
            _build_receipt(),
            "41877a1f687a00b7c248925e0c04490496c4fc26aa45948b8b6d85eb0b666843",
        ),
    )
    for record, original_sha in values:
        assert record.fingerprint() == original_sha
        assert (
            decode_canonical_bytes(
                record.canonical_bytes(), type(record), maximum_bytes=8192
            )
            == record
        )
    for name in (
        "OfficialMetricGaugeV2",
        "OfficialMetricSetV2",
        "MetricSourceSemantics",
    ):
        assert getattr(metric_correction_v2, name) is globals()[name]
    for name in ("SharedTemplateShiftV2Selection", "SharedTemplateShiftV2BuildReceipt"):
        assert getattr(prediction_v2, name) is globals()[name]


def test_pure_selection_and_custody_imports_cannot_load_numerical_owners():
    script = """
import importlib.abc
import sys
class ForbidScientific(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        forbidden = ('numpy', 'h5py', 'anndata', 'cell_eval', 'polars', 'pdex')
        if fullname.split('.')[0] in forbidden or fullname.endswith(
                ('.analysis', '.runtime', '.dataset', '.prediction_v2', '.metric_correction_v2')):
            raise AssertionError('forbidden scientific import: ' + fullname)
sys.meta_path.insert(0, ForbidScientific())
from empirical_lawhood.adapters.physical.virtual_cell.correction_records_v2 import (
    OfficialMetricGaugeV2, SharedTemplateShiftV2Selection)
from empirical_lawhood.adapters.physical.virtual_cell.config_v2 import VirtualCellPipelineSelectionV2
from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import PredictionFreezeRecordV2
from empirical_lawhood.adapters.physical.virtual_cell.receiver_readiness_v2 import ReceiverReadinessV2
from empirical_lawhood.adapters.physical.virtual_cell.runtime_v2 import VirtualCellSelectedMethodsV2
assert OfficialMetricGaugeV2().des_source_column == 'overlap_at_N'
assert SharedTemplateShiftV2Selection().VERSION == '2.0.0'
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def test_original_package_exports_retain_exact_names_and_owner_objects():
    import empirical_lawhood.adapters.physical.virtual_cell as adapter
    from empirical_lawhood.adapters.physical.virtual_cell.analysis import (
        CompiledPrediction,
    )
    from empirical_lawhood.adapters.physical.virtual_cell.contracts import (
        MetricContract,
    )

    # Original public __all__, captured before the lazy export change.
    assert adapter.__all__ == [
        "CompiledPrediction",
        "EmpiricalReplaySpec",
        "H5ADStructuralInspection",
        "LinearResponseModel",
        "MetricContract",
        "ModelFamily",
        "PredictionCommitment",
        "ResponseSummaryArrays",
        "SegmentedBinaryReader",
        "TargetFeatureMatrix",
        "TargetResponseMatrix",
        "TaskTranslation2026",
        "VirtualCellDenominator",
        "ProvenanceBoundVirtualCellPipelineConfig",
        "VirtualCellSourceManifest",
        "adjudicate_placement",
        "adjudicate_official_final_top100",
        "compile_prediction_cells",
        "decode_official_final_top100",
        "fit_tier_l0_model",
        "inspect_h5ad",
        "official_aggregate_score",
        "predict_response",
        "summarize_h5ad",
    ]
    assert adapter.CompiledPrediction is CompiledPrediction
    assert adapter.MetricContract is MetricContract
    with pytest.raises(AttributeError):
        _ = adapter.user_selected_module


def test_v2_selection_keeps_original_bytes_and_only_explicit_compiler_successor():
    original = _original_config()
    original_bytes = original.canonical_bytes()
    selected = _selection(original)
    assert original.canonical_bytes() == original_bytes
    assert original.prediction_compiler.mean_tolerance == Decimal("0.000005")
    assert selected.compiler_contract.mean_tolerance == Decimal("0.000001")
    assert selected.original_config == ObjectIdentity.from_record(
        original.config_id, original
    )
    assert selected.compiler_contract == replace(
        original.prediction_compiler,
        contract_id=selected.compiler.compiler_id,
        mean_tolerance=Decimal("0.000001"),
    )
    assert (
        decode_canonical_bytes(
            selected.canonical_bytes(),
            VirtualCellPipelineSelectionV2,
            maximum_bytes=65536,
        )
        == selected
    )


@pytest.mark.parametrize(
    "changed",
    [
        dict(compiler_seed=77),
        dict(total_cell_limit=99999),
        dict(freeze_timestamp_utc="2026-08-09T00:00:00Z"),
        dict(maximum_envelope_bytes=1000000),
    ],
)
def test_v2_selection_refuses_original_budget_replacement(changed):
    original = _original_config()
    selected = _selection(original)
    rebound = replace(
        selected, compiler_contract=replace(selected.compiler_contract, **changed)
    )
    with pytest.raises(
        ValueError, match="row allocation, seed, cutoff or artifact bound"
    ):
        rebound.validate_original(original)


@pytest.mark.parametrize(
    "changed",
    [dict(config_id="config.unrelated"), dict(source_manifest_sha256="9" * 64)],
)
def test_v2_selection_refuses_original_identity_or_byte_republication(changed):
    original = _original_config()
    with pytest.raises(ValueError, match="original pipeline identity or bytes"):
        _selection(original).validate_original(replace(original, **changed))


@pytest.mark.parametrize(
    "changed",
    [
        dict(object_schema="empirical-lawhood/unrelated/original"),
        dict(object_version="2.0.0"),
    ],
)
def test_v2_selection_refuses_relabelled_original_revision(changed):
    selected = _selection()
    with pytest.raises(ValueError, match="original pipeline schema and revision"):
        replace(selected, original_config=replace(selected.original_config, **changed))


def test_readiness_reports_all_four_missing_dependencies_before_optional_imports(
    monkeypatch,
):
    observed = []

    def missing(name):
        observed.append(name)
        raise PackageNotFoundError(name)

    def forbidden_import(*args, **kwargs):
        pytest.fail("availability refusal must precede receiver imports")

    monkeypatch.setattr(readiness, "version", missing)
    monkeypatch.setattr(readiness, "import_module", forbidden_import)
    original = _original_config()
    selected = _selection(original)
    result = readiness.observe_receiver_readiness_v2(
        selection=selected, original_config=original
    )
    assert observed == ["anndata", "cell-eval", "pdex", "polars"]
    assert len(result.reasons) == 4 and not result.ready
    with pytest.raises(
        readiness.ReceiverEnvironmentUnavailable, match="ENVIRONMENT"
    ) as error:
        readiness.require_receiver_ready_v2(
            selection=selected, original_config=original
        )
    for name in observed:
        assert name in str(error.value)


@pytest.mark.parametrize("dependency", ["anndata", "cell-eval", "pdex", "polars"])
def test_readiness_refuses_each_wrong_selected_version_before_receiver_import(
    monkeypatch, dependency
):
    expected = dict(readiness.LOCKED_RECEIVER_DISTRIBUTIONS_V2)
    monkeypatch.setattr(
        readiness,
        "version",
        lambda name: "0.0.0" if name == dependency else expected[name],
    )
    monkeypatch.setattr(
        readiness,
        "import_module",
        lambda *args: pytest.fail("receiver imported despite wrong version"),
    )
    result = readiness.observe_receiver_readiness_v2(
        selection=_selection(), original_config=_original_config()
    )
    assert not result.ready
    assert len(result.reasons) == 1 and dependency in result.reasons[0]


def test_fake_complete_receiver_requires_all_actual_entry_points(monkeypatch):
    # Software-only doubles; this cannot demonstrate official evaluator conformance.
    from empirical_lawhood.adapters.physical.virtual_cell import analysis

    expected = dict(readiness.LOCKED_RECEIVER_DISTRIBUTIONS_V2)
    monkeypatch.setattr(readiness, "version", expected.__getitem__)
    monkeypatch.setattr(
        readiness, "authenticate_installed_scorer_source_v2", lambda contract: None
    )
    monkeypatch.setattr(
        analysis,
        "verify_official_evaluator_versions",
        lambda contract: ("0.6.6", "0.1.26"),
    )
    calls = []

    def fake_module(name):
        calls.append(name)
        return SimpleNamespace(
            AnnData=object,
            read_elem=lambda: None,
            DataFrame=object,
            MetricsEvaluator=object,
        )

    monkeypatch.setattr(readiness, "import_module", fake_module)
    assert readiness.require_receiver_ready_v2(
        selection=_selection(), original_config=_original_config()
    ).ready
    assert calls == ["anndata", "anndata._io.specs", "polars", "cell_eval"]
    monkeypatch.setattr(readiness, "import_module", lambda name: SimpleNamespace())
    result = readiness.observe_receiver_readiness_v2(
        selection=_selection(), original_config=_original_config()
    )
    assert not result.ready and len(result.entry_point_errors) == 4


@pytest.mark.parametrize(
    "capability",
    [
        SUMMARY_CAPABILITY_KEY,
        MODEL_CAPABILITY_KEY,
        PREDICTION_CAPABILITY_KEY,
        EVALUATOR_CAPABILITY_KEY,
    ],
)
def test_historical_runtime_refuses_before_any_stage_source_or_scratch(
    monkeypatch, capability
):
    from empirical_lawhood.adapters.physical.virtual_cell.runtime import (
        VirtualCellTaskRunner,
    )

    runner = object.__new__(VirtualCellTaskRunner)
    runner.manifest = SimpleNamespace(capability_key=capability)
    checked = []
    monkeypatch.setattr(
        runner, "_validate_context", lambda context: checked.append(context)
    )
    for name in ("_summarize", "_develop", "_freeze_prediction", "_evaluate"):
        monkeypatch.setattr(
            runner,
            name,
            lambda context: pytest.fail("historical stage reached source or scratch"),
        )
    context = object()
    with pytest.raises(VirtualCellContractError, match="SOFTWARE"):
        runner.execute(context)
    assert checked == [context]


def test_corrected_custody_uses_successor_metrics_and_original_fit_references():
    # Complete typed metadata only; actual evidence bytes are required by views.
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.adapters.physical.virtual_cell.contracts import (
        MetricContract,
        VirtualCellSourceManifest,
        VirtualCellSourceObject,
    )
    from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import (
        ModelSelectionRecordV2,
        RAW_PREDICTION_DELTAS_SCHEMA,
        registry_sha256,
    )

    selected = _selection()
    genes, targets = ("gene.a", "gene.b"), ("target.exposed",)
    fit = _reference(
        "empirical-lawhood/physical/virtual-cell/model-fit-record", "fit.exposed"
    )
    build = replace(_build_receipt(), gene_order_sha256=registry_sha256(genes))
    metrics = _reference(OfficialMetricSetV2.SCHEMA, "metrics.exposed", "2.0.0")
    score = _reference(
        "empirical-lawhood/physical/virtual-cell/official-aggregate-score",
        "score.exposed",
    )
    artifact = lambda name, schema, media, digest="1" * 64, size=1: ArtifactIdentity(
        name, "exposed-software", schema, digest, media, size
    )
    metric_artifact = artifact(
        "metrics.exposed", OfficialMetricSetV2.SCHEMA, "application/json"
    )
    contract = _reference(MetricContract.SCHEMA, "metric.exposed")
    candidate = CandidateValidationRecordV2(
        "candidate.exposed",
        selected.identity,
        fit,
        ObjectIdentity.from_record(build.receipt_id, build),
        metrics,
        score,
        metric_artifact,
        targets,
        contract,
        Decimal(0),
        OutcomeAccess.DEVELOPMENT_VISIBLE,
    )
    source = _reference(VirtualCellSourceManifest.SCHEMA, "manifest.exposed")
    summary = lambda name: _reference(
        "empirical-lawhood/physical/virtual-cell/response-summary-record", name
    )
    binding = _reference(
        "empirical-lawhood/physical/virtual-cell/model-artifact-binding",
        "binding.exposed",
    )
    development = ModelDevelopmentRecordV2(
        "development.exposed",
        selected.identity,
        source,
        summary("summary.train"),
        summary("summary.validation"),
        "1" * 64,
        (binding,),
        (candidate,),
        _reference(
            "empirical-lawhood/physical/virtual-cell/tournament-record",
            "tournament.exposed",
        ),
        ("target.train",),
        targets,
        (),
        (),
    )
    commitment = PredictionCommitment(
        "commitment.exposed",
        "lane.exposed",
        "model.exposed",
        "1" * 64,
        selected.fingerprint(),
        "1" * 64,
        "1" * 64,
        "1" * 64,
        build.h5ad_sha256,
        "1" * 64,
        "1" * 64,
        build.gene_order_sha256,
        "2026-08-08T00:00:00Z",
        (),
        (),
    )
    freeze = PredictionFreezeRecordV2(
        "freeze.exposed",
        selected.identity,
        _reference(
            ModelSelectionRecordV2.SCHEMA,
            "selection.exposed",
            ModelSelectionRecordV2.VERSION,
        ),
        source,
        contract,
        fit,
        "model.exposed",
        artifact(
            "model.exposed",
            "empirical-lawhood/physical/virtual-cell/linear-model-safetensors",
            "application/x-safetensors",
        ),
        commitment,
        build,
        targets,
        genes,
        _reference(
            "empirical-lawhood/physical/virtual-cell/prediction-roster",
            "roster.exposed",
        ),
        artifact(
            "roster.exposed",
            "empirical-lawhood/physical/virtual-cell/test-roster-csv",
            "text/csv",
        ),
        artifact(
            "deltas.exposed",
            RAW_PREDICTION_DELTAS_SCHEMA,
            "application/octet-stream",
            size=len(str((1, 2))) + 16,
        ),
        artifact(
            "envelope.exposed",
            "empirical-lawhood/physical/virtual-cell/prediction-h5ad-envelope",
            "application/x-hdf5",
        ),
    )
    evaluation = OfficialEvaluationRecordV2(
        "evaluation.exposed",
        selected.identity,
        ObjectIdentity.from_record(freeze.record_id, freeze),
        commitment.fingerprint(),
        _reference(VirtualCellSourceObject.SCHEMA, "source.test"),
        contract,
        metrics,
        metric_artifact,
        score,
        targets,
        "0.6.6",
        "0.1.26",
        OutcomeAccess.EVALUATOR_REVEAL,
    )
    for record in (candidate, development, freeze, evaluation):
        assert record.VERSION == "2.1.0"
        assert (
            decode_canonical_bytes(
                record.canonical_bytes(), type(record), maximum_bytes=65536
            )
            == record
        )
    with pytest.raises(ValueError, match="exact schema or revision"):
        replace(candidate, metrics=replace(metrics, object_version="1.0.0"))
    with pytest.raises(ValueError, match="actual model, selection"):
        replace(freeze, commitment=replace(commitment, config_sha256="9" * 64))
    with pytest.raises(TypeError, match="typed complete validation census"):
        replace(development, validations=[candidate])
    with pytest.raises(ValueError, match="exact reveal scope"):
        replace(evaluation, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)


def test_selected_methods_refuse_missing_stack_before_writer_evaluator_or_destination(
    monkeypatch, tmp_path
):
    from empirical_lawhood.adapters.physical.virtual_cell.runtime_v2 import (
        VirtualCellSelectedMethodsV2,
    )

    monkeypatch.setattr(
        readiness,
        "version",
        lambda name: (_ for _ in ()).throw(PackageNotFoundError(name)),
    )
    methods = VirtualCellSelectedMethodsV2(_original_config(), _selection())
    destination = tmp_path / "forbidden.h5ad"
    with pytest.raises(readiness.ReceiverEnvironmentUnavailable, match="ENVIRONMENT"):
        methods.write_prediction(
            path=destination,
            roster=object(),
            gene_ids=(),
            predicted_deltas=object(),
            control_reservoir=object(),
            control_reservoir_sha256="1" * 64,
        )
    with pytest.raises(readiness.ReceiverEnvironmentUnavailable, match="ENVIRONMENT"):
        methods.evaluate_validation(
            predicted=object(),
            real=object(),
            scratch_directory=destination,
            num_threads=1,
        )
    assert not destination.exists() and list(tmp_path.iterdir()) == []


def _tiny_selected_prediction_inputs():
    import numpy as np
    from empirical_lawhood.adapters.physical.virtual_cell.dataset import (
        ControlReservoirArrays,
    )
    from empirical_lawhood.adapters.physical.virtual_cell.prediction import (
        PredictionRoster,
        PredictionTargetAllocation,
    )

    original = _original_config()
    original = replace(
        original,
        prediction_compiler=replace(
            original.prediction_compiler,
            total_cell_limit=6,
            control_cells=2,
            minimum_cells_per_target=1,
            control_reservoir_cells=4,
        ),
    )
    roster = PredictionRoster(
        "roster.exposed",
        "1" * 64,
        (PredictionTargetAllocation("target.exposed", 4, Decimal(100), 4),),
        "non-targeting",
        2,
        6,
        "exposed-small-software-allocation",
    )
    reservoir = ControlReservoirArrays(
        tuple(f"row.{i}" for i in range(4)),
        ("batch.exposed",) * 4,
        ("gene.a", "gene.b"),
        original.response_summary.normalization,
        float(original.response_summary.normalization_target_sum),
        np.ones((4, 2), dtype=np.float32),
    )
    return original, roster, reservoir


def test_selected_prediction_delegates_raw_unequal_actions_and_exact_original_seed(
    monkeypatch, tmp_path
):
    import numpy as np
    from empirical_lawhood.adapters.physical.virtual_cell import (
        prediction_v2,
        runtime_v2,
    )

    original, roster, reservoir = _tiny_selected_prediction_inputs()
    methods = runtime_v2.VirtualCellSelectedMethodsV2(original, _selection(original))
    events = []
    monkeypatch.setattr(
        runtime_v2,
        "require_receiver_ready_v2",
        lambda **kwargs: events.append(("availability", kwargs)),
    )
    output = object()

    def exposed_writer(**kwargs):
        events.append(("writer", kwargs))
        return output

    monkeypatch.setattr(
        prediction_v2, "write_shared_template_shift_v2_prediction_h5ad", exposed_writer
    )
    actions = np.asarray([[-0.4, 1.2]])
    assert (
        methods.write_prediction(
            path=tmp_path / "explicit.h5ad",
            roster=roster,
            gene_ids=reservoir.gene_ids,
            predicted_deltas=actions,
            control_reservoir=reservoir,
            control_reservoir_sha256="8" * 64,
        )
        is output
    )
    assert [event for event, _ in events] == ["availability", "writer"]
    forwarded = events[1][1]
    assert forwarded["predicted_deltas"] is actions
    np.testing.assert_array_equal(forwarded["predicted_deltas"], [[-0.4, 1.2]])
    assert forwarded["seed"] == original.prediction_compiler.compiler_seed
    assert forwarded["selection"] is methods.selection.compiler
    assert forwarded["control_reservoir_sha256"] == "8" * 64
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("changed", ["rows", "controls", "normalization"])
def test_selected_prediction_refuses_substituted_budget_before_writer(
    monkeypatch, tmp_path, changed
):
    from empirical_lawhood.adapters.physical.virtual_cell import (
        prediction_v2,
        runtime_v2,
    )

    original, roster, reservoir = _tiny_selected_prediction_inputs()
    methods = runtime_v2.VirtualCellSelectedMethodsV2(original, _selection(original))
    monkeypatch.setattr(runtime_v2, "require_receiver_ready_v2", lambda **kwargs: None)
    monkeypatch.setattr(
        prediction_v2,
        "write_shared_template_shift_v2_prediction_h5ad",
        lambda **kwargs: pytest.fail("substituted allocation reached writer"),
    )
    if changed == "rows":
        roster = replace(
            roster,
            total_cell_limit=7,
            targets=(replace(roster.targets[0], allocated_cells=5),),
        )
    elif changed == "controls":
        roster = replace(
            roster,
            control_cells=1,
            targets=(replace(roster.targets[0], allocated_cells=5),),
        )
    else:
        reservoir = replace(reservoir, normalization_target_sum=100.0)
    with pytest.raises(
        ValueError,
        match="selected row allocation or control budget|original control normalization",
    ):
        methods.write_prediction(
            path=tmp_path / "forbidden.h5ad",
            roster=roster,
            gene_ids=reservoir.gene_ids,
            predicted_deltas=object(),
            control_reservoir=reservoir,
            control_reservoir_sha256="8" * 64,
        )
    assert list(tmp_path.iterdir()) == []


def test_validation_composition_uses_original_validation_baseline_and_new_gauge(
    monkeypatch, tmp_path
):
    from empirical_lawhood.adapters.physical.virtual_cell import evaluation, runtime_v2

    original = _original_config()
    methods = runtime_v2.VirtualCellSelectedMethodsV2(original, _selection(original))
    calls = []
    monkeypatch.setattr(
        runtime_v2,
        "require_receiver_ready_v2",
        lambda **kwargs: calls.append("availability"),
    )
    output = object()

    def fake_receiver(**kwargs):
        calls.append(kwargs)
        return output

    monkeypatch.setattr(evaluation, "evaluate_official_2025_v2", fake_receiver)
    predicted, real = object(), object()
    assert (
        methods.evaluate_validation(
            predicted=predicted,
            real=real,
            scratch_directory=tmp_path / "explicit",
            num_threads=1,
        )
        is output
    )
    assert calls[0] == "availability"
    forwarded = calls[1]
    assert forwarded["predicted"] is predicted and forwarded["real"] is real
    assert (
        forwarded["metric_contract"]
        is original.model_selection.validation_metric_contract
    )
    assert forwarded["metric_contract"] != original.metric_contract
    assert forwarded["metric_gauge"] is methods.selection.metric_gauge
    assert forwarded["metric_gauge"].des_source_column == "overlap_at_N"
    assert forwarded["metric_gauge"].pds_source_column == "discrimination_score_l1"
    assert forwarded["control_label"] == original.response_summary.comparator_label
    assert forwarded["perturbation_column"] == original.response_summary.target_field
    assert list(tmp_path.iterdir()) == []


def test_final_evaluation_is_explicitly_unavailable_without_owning_authority_join(
    monkeypatch,
):
    from empirical_lawhood.adapters.physical.virtual_cell import runtime_v2

    methods = runtime_v2.VirtualCellSelectedMethodsV2(_original_config(), _selection())
    monkeypatch.setattr(
        runtime_v2,
        "require_receiver_ready_v2",
        lambda **kwargs: pytest.fail("final route probed receiver"),
    )
    with pytest.raises(VirtualCellContractError, match="SOFTWARE.*owning TaskRunner"):
        methods.evaluate_final(predicted=object(), real=object(), claimed_reveal=True)
