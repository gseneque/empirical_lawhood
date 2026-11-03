# SPDX-License-Identifier: MPL-2.0
"""Exposed small software controls; no official receiver or biological evidence."""

from dataclasses import replace
from decimal import Decimal
import hashlib
import json
import subprocess
import sys

import h5py
import numpy as np
import pytest
from scipy.stats import false_discovery_control, mannwhitneyu

from empirical_lawhood.kernel.decoding import decode_canonical_bytes

from empirical_lawhood.adapters.physical.virtual_cell.config import (
    virtual_cell_2025_metric_contract,
)
from empirical_lawhood.adapters.physical.virtual_cell.contracts import (
    VirtualCellContractError,
)
from empirical_lawhood.adapters.physical.virtual_cell.dataset import (
    ControlReservoirArrays,
)
from empirical_lawhood.adapters.physical.virtual_cell.evaluation import (
    _metric_arrays,
    evaluate_official_2025,
)
from empirical_lawhood.adapters.physical.virtual_cell.metric_correction_v2 import (
    MetricSourceSemantics,
    OfficialMetricGaugeV2,
    OfficialMetricSetV2,
    correct_historical_crosswired_metrics,
    metric_set_from_source_columns,
    score_corrected_metrics,
    score_source_aggregate,
)
from empirical_lawhood.adapters.physical.virtual_cell.prediction import (
    PredictionH5ADBuildReceipt,
    PredictionRoster,
    PredictionTargetAllocation,
    write_historical_mean_preserving_prediction_h5ad,
    write_prediction_h5ad,
    compile_absolute_prediction_means,
)
from empirical_lawhood.adapters.physical.virtual_cell.prediction_v2 import (
    SharedTemplateShiftV2BuildReceipt,
    SharedTemplateShiftV2Selection,
    compile_shared_template_shift_v2_cells,
    shared_template_shift_v2_null_cells,
    write_shared_template_shift_v2_prediction_h5ad,
)


class _Column:
    def __init__(self, values):
        self.values = values

    def to_numpy(self):
        return np.asarray(self.values)

    def to_list(self):
        return list(self.values)


class _SourceTable:
    """Only the table access surface; no evaluator or metric-name implementation."""

    def __init__(self, rows):
        self.rows = rows
        self.columns = (
            "perturbation",
            "overlap_at_N",
            "discrimination_score_l1",
            "mae",
        )

    def sort(self, column):
        return _SourceTable(sorted(self.rows, key=lambda row: row[column]))

    def __getitem__(self, name):
        return _Column([row[name] for row in self.rows])


def test_unequal_source_columns_survive_current_evaluator_mapping():
    rows = [
        dict(
            perturbation="target.b",
            overlap_at_N=0.4,
            discrimination_score_l1=0.9,
            mae=0.03,
        ),
        dict(
            perturbation="target.a",
            overlap_at_N=0.2,
            discrimination_score_l1=0.7,
            mae=0.01,
        ),
    ]
    target_ids, des, pds, mae = _metric_arrays(_SourceTable(rows))
    assert target_ids == ("target.a", "target.b")
    np.testing.assert_array_equal(des, [0.2, 0.4])
    np.testing.assert_array_equal(pds, [0.7, 0.9])
    np.testing.assert_array_equal(mae, [0.01, 0.03])


def test_corrected_per_target_and_aggregate_use_unequal_decimal_oracle():
    gauge = OfficialMetricGaugeV2()
    columns = {
        "overlap_at_N": (0.2, 0.4),
        "discrimination_score_l1": (0.7, 0.9),
        "mae": (0.01, 0.03),
    }
    metrics = metric_set_from_source_columns(
        target_ids=("target.a", "target.b"), columns=columns, gauge=gauge
    )
    assert metrics.des == (Decimal("0.2"), Decimal("0.4"))
    assert metrics.pds == (Decimal("0.7"), Decimal("0.9"))
    contract = virtual_cell_2025_metric_contract()
    # Literal source-column oracle, independent of the production mapping.
    des, pds, mae = Decimal("0.3"), Decimal("0.8"), Decimal("0.02")
    baseline = contract.baseline
    expected = (
        max(Decimal(0), (des - baseline.des) / (1 - baseline.des))
        + max(Decimal(0), (pds - baseline.pds) / (1 - baseline.pds))
        + max(Decimal(0), 1 - mae / baseline.mae)
    ) / 3
    score = score_source_aggregate(
        columns={"overlap_at_N": des, "discrimination_score_l1": pds, "mae": mae},
        gauge=gauge,
        metric_contract=contract,
    )
    assert (score.des, score.pds, score.mae) == (des, pds, mae)
    assert score.average_score == expected
    # Per-target reduction uses the same selected semantics, with float reduction tolerance.
    assert abs(
        score_corrected_metrics(metrics, metric_contract=contract).average_score
        - expected
    ) < Decimal("1e-15")
    crossed = score_source_aggregate(
        columns={"overlap_at_N": pds, "discrimination_score_l1": des, "mae": mae},
        gauge=gauge,
        metric_contract=contract,
    )
    assert abs(crossed.average_score - expected) > Decimal("0.01")


def test_corrected_record_roundtrip_and_no_second_historical_swap():
    metrics = metric_set_from_source_columns(
        target_ids=("target.a",),
        columns={
            "overlap_at_N": (0.2,),
            "discrimination_score_l1": (0.8,),
            "mae": (0.01,),
        },
        gauge=OfficialMetricGaugeV2(),
    )
    payload = metrics.canonical_bytes()
    assert (
        decode_canonical_bytes(payload, OfficialMetricSetV2, maximum_bytes=65536)
        == metrics
    )
    with pytest.raises(ValueError, match="successor"):
        correct_historical_crosswired_metrics(payload, gauge=OfficialMetricGaugeV2())
    with pytest.raises(ValueError, match="original byte"):
        replace(metrics, source_semantics=MetricSourceSemantics.HISTORICAL_CROSSED_V1)
    changed = json.loads(payload)
    changed["version"] = "1.0.0"
    with pytest.raises(ValueError):
        decode_canonical_bytes(
            json.dumps(changed).encode(), OfficialMetricSetV2, maximum_bytes=65536
        )


@pytest.mark.parametrize(
    "changed",
    [
        dict(des_source_column="discrimination_score_l1"),
        dict(pds_source_column="overlap_at_N"),
        dict(pdex_version="0.1.25"),
    ],
)
def test_metric_gauge_refuses_wrong_mapping_or_receiver(changed):
    with pytest.raises(ValueError, match="semantics"):
        OfficialMetricGaugeV2(**changed)


def test_correction_helpers_defer_optional_official_evaluator_imports():
    script = """
import sys
from empirical_lawhood.adapters.physical.virtual_cell import evaluation, metric_correction_v2
assert not {'anndata', 'cell_eval', 'polars', 'pdex'} & set(sys.modules)
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def test_unversioned_calls_refuse_before_output(tmp_path):
    destination = tmp_path / "unversioned.h5ad"
    with pytest.raises(VirtualCellContractError, match="SOFTWARE"):
        write_prediction_h5ad(path=destination)
    with pytest.raises(VirtualCellContractError, match="SOFTWARE"):
        evaluate_official_2025(scratch_directory=tmp_path / "unversioned-evaluator")
    assert not destination.exists()
    assert not (tmp_path / "unversioned-evaluator").exists()


def test_literal_rank_and_order_statistic_oracle():
    template = np.array([[4, 1], [1, 4], [3, 2], [2, 3]], dtype=np.float32)
    # For n=3, midpoint order statistics are [1,3,4]; anchor ranks determine these rows.
    expected = np.array([[4, 1], [1, 4], [3, 3]], dtype=np.float32)
    actual = shared_template_shift_v2_null_cells(template, cell_count=3)
    np.testing.assert_array_equal(actual, expected)
    assert not np.array_equal(np.mean(actual, axis=0), np.mean(template, axis=0))
    np.testing.assert_array_equal(
        shared_template_shift_v2_null_cells(template, cell_count=4), template
    )


@pytest.mark.parametrize("cell_count", [1, 7, 11, 17, 31])
def test_v2_null_and_action_invariants(cell_count):
    template = np.random.default_rng(71).uniform(0.1, 4, (17, 3)).astype(np.float32)
    null = shared_template_shift_v2_null_cells(template, cell_count=cell_count)
    zero = compile_shared_template_shift_v2_cells(
        template=template, requested_delta=np.zeros(3), cell_count=cell_count
    )
    np.testing.assert_array_equal(zero.values, null)
    np.testing.assert_array_equal(zero.realized_delta, np.zeros(3))
    delta = np.array([0.4, 0, -0.2])
    action = compile_shared_template_shift_v2_cells(
        template=template, requested_delta=delta, cell_count=cell_count
    )
    np.testing.assert_array_equal(action.values[:, 1], null[:, 1])
    np.testing.assert_array_equal(
        action.values,
        compile_shared_template_shift_v2_cells(
            template=template, requested_delta=delta, cell_count=cell_count
        ).values,
    )
    # Independent summation of the action's achieved mean changes.
    realized = np.array(
        [
            sum(map(float, action.values[:, j])) / cell_count
            - sum(map(float, null[:, j])) / cell_count
            for j in range(3)
        ]
    )
    np.testing.assert_allclose(realized, delta, atol=1e-6, rtol=0)
    assert np.all(action.values[:, 0] >= null[:, 0])
    assert np.all(action.values[:, 2] <= null[:, 2])
    assert action.values.dtype == np.float32


@pytest.mark.parametrize("seed", [7, 19, 31, 43])
def test_synthetic_unequal_count_rank_null_math_only(seed):
    template = np.random.default_rng(seed).uniform(0.05, 4, (400, 8)).astype(np.float32)
    pvalues = []
    for count in (131, 233, 337, 400):
        null = shared_template_shift_v2_null_cells(template, cell_count=count)
        for gene in range(8):
            # An independent rank statistic; this is NOT pinned pdex/cell-eval conformance.
            pvalues.append(
                mannwhitneyu(
                    template[:, gene],
                    null[:, gene],
                    method="asymptotic",
                    alternative="two-sided",
                ).pvalue
            )
    assert np.min(false_discovery_control(np.array(pvalues))) >= 0.5


@pytest.mark.parametrize(
    "delta", [np.array([-100.0, 0.0]), np.array([0.0, 100.0]), np.array([np.nan, 0.0])]
)
def test_unrepresentable_actions_refuse(delta):
    with pytest.raises(ValueError):
        compile_shared_template_shift_v2_cells(
            template=np.array([[1, 2], [3, 4]], dtype=np.float32),
            requested_delta=delta,
            cell_count=3,
        )


def _tiny_fixture():
    reservoir = ControlReservoirArrays(
        tuple(f"cell.{i}" for i in range(8)),
        ("batch.exposed",) * 8,
        ("gene.a", "gene.b"),
        "log1p-fixed-total",
        10000.0,
        np.tile(np.array([0.5, 1.0], dtype=np.float32), (8, 1)),
    )
    roster = PredictionRoster(
        "roster.synthetic-exposed",
        "a" * 64,
        (
            PredictionTargetAllocation("target.a", 3, Decimal(1), 3),
            PredictionTargetAllocation("target.b", 5, Decimal(1), 5),
        ),
        "non-targeting",
        4,
        12,
        "synthetic unequal-count fixture",
    )
    return reservoir, roster


def test_tiny_v2_h5ad_has_new_receipt_exact_roster_and_action(tmp_path):
    reservoir, roster = _tiny_fixture()
    destination = tmp_path / "selected-v2.h5ad"
    delta = np.array([[0.0, 0.0], [0.2, -0.1]])
    selection = SharedTemplateShiftV2Selection()
    receipt = write_shared_template_shift_v2_prediction_h5ad(
        path=destination,
        roster=roster,
        gene_ids=reservoir.gene_ids,
        predicted_deltas=delta,
        control_reservoir=reservoir,
        control_reservoir_sha256="b" * 64,
        seed=19,
        selection=selection,
    )
    assert receipt.VERSION == "2.0.0"
    assert receipt.SCHEMA != PredictionH5ADBuildReceipt.SCHEMA
    assert receipt.selection_sha256 == selection.fingerprint()
    assert receipt.h5ad_sha256 == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert (
        receipt.maximum_null_mean_error == 0
        and receipt.maximum_action_error < Decimal("1e-6")
    )
    assert not receipt.outcome_read
    assert (
        decode_canonical_bytes(
            receipt.canonical_bytes(),
            SharedTemplateShiftV2BuildReceipt,
            maximum_bytes=65536,
        )
        == receipt
    )
    with h5py.File(destination) as handle:
        values = handle["X"][:]
        assert values.shape == (12, 2) and values.dtype == np.float32
        np.testing.assert_array_equal(values[:7], np.tile([0.5, 1.0], (7, 1)))
        np.testing.assert_allclose(
            np.mean(values[7:], axis=0), [0.7, 0.9], atol=1e-6, rtol=0
        )
        assert (
            handle["obs"]["target_gene"].asstr()[:].tolist()
            == ["non-targeting"] * 4 + ["target.a"] * 3 + ["target.b"] * 5
        )


@pytest.mark.parametrize("bad", ["action", "gene-order", "selection", "template-range"])
def test_whole_selected_action_refuses_before_file_creation(tmp_path, bad):
    reservoir, roster = _tiny_fixture()
    delta = np.zeros((2, 2))
    selection = SharedTemplateShiftV2Selection()
    genes = reservoir.gene_ids
    if bad == "action":
        delta[1, 0] = -100
    elif bad == "gene-order":
        genes = tuple(reversed(genes))
    elif bad == "selection":
        selection = None
    else:
        reservoir = replace(
            reservoir, values=np.full((8, 2), 14.9995, dtype=np.float32)
        )
    destination = tmp_path / f"rejected-{bad}.h5ad"
    with pytest.raises((ValueError, TypeError)):
        write_shared_template_shift_v2_prediction_h5ad(
            path=destination,
            roster=roster,
            gene_ids=genes,
            predicted_deltas=delta,
            control_reservoir=reservoir,
            control_reservoir_sha256="b" * 64,
            seed=19,
            selection=selection,
        )
    assert not destination.exists()


def test_historical_writer_retains_original_receipt_meaning(tmp_path):
    reservoir, roster = _tiny_fixture()
    means = compile_absolute_prediction_means(
        target_ids=("target.a", "target.b"),
        predicted_deltas=np.zeros((2, 2)),
        control_reservoir=reservoir,
    )
    receipt = write_historical_mean_preserving_prediction_h5ad(
        path=tmp_path / "historical.h5ad",
        roster=roster,
        gene_ids=reservoir.gene_ids,
        predicted_means=means,
        control_reservoir=reservoir,
        control_reservoir_sha256="b" * 64,
        seed=19,
        mean_tolerance=1e-6,
    )
    assert type(receipt) is PredictionH5ADBuildReceipt
    assert receipt.VERSION == "1.0.0"
    assert "mean_error" in receipt.canonical_bytes().decode()


@pytest.mark.parametrize("count", [True, 0, -1, 2.5])
def test_null_refuses_noninteger_or_empty_cell_populations(count):
    with pytest.raises(ValueError):
        shared_template_shift_v2_null_cells(
            np.ones((4, 2), dtype=np.float32), cell_count=count
        )


def test_equal_count_preserves_signed_zero_bits():
    template = np.array([[0.0, -0.0], [-0.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    actual = shared_template_shift_v2_null_cells(template, cell_count=3)
    assert actual.tobytes() == template.tobytes()


def test_null_mean_bound_refuses_before_output(tmp_path):
    reservoir, roster = _tiny_fixture()
    reservoir = replace(
        reservoir,
        values=np.tile(np.arange(1, 9, dtype=np.float32)[:, None] / 10, (1, 2)),
    )
    destination = tmp_path / "null-bound-refused.h5ad"
    with pytest.raises(ValueError, match="null population"):
        write_shared_template_shift_v2_prediction_h5ad(
            path=destination,
            roster=roster,
            gene_ids=reservoir.gene_ids,
            predicted_deltas=np.zeros((2, 2)),
            control_reservoir=reservoir,
            control_reservoir_sha256="b" * 64,
            seed=19,
            selection=SharedTemplateShiftV2Selection(),
        )
    assert not destination.exists()


def test_compiler_selection_cannot_relax_donor_scientific_bounds():
    with pytest.raises(ValueError, match="bounds"):
        SharedTemplateShiftV2Selection(maximum_null_mean_error=Decimal("1"))
    with pytest.raises(ValueError, match="range"):
        compile_shared_template_shift_v2_cells(
            template=np.array([[1.0, 2.0]], dtype=np.float32),
            requested_delta=np.zeros(2),
            cell_count=1,
            maximum_value=1.5,
        )


@pytest.mark.parametrize(
    "damage",
    [
        dict(scorer_version="0.6.7"),
        dict(pdex_version="0.1.27"),
        dict(scorer_distribution="unrelated-evaluator"),
    ],
)
def test_evaluator_contract_must_match_gauge_before_import_or_observation(
    tmp_path, monkeypatch, damage
):
    import builtins
    from empirical_lawhood.adapters.physical.virtual_cell.evaluation import (
        evaluate_official_2025_v2,
    )
    from empirical_lawhood.adapters.physical.virtual_cell.metric_correction_v2 import (
        require_metric_contract_gauge,
    )

    contract = replace(virtual_cell_2025_metric_contract(), **damage)
    gauge = OfficialMetricGaugeV2()
    with pytest.raises(ValueError, match="gauge"):
        require_metric_contract_gauge(gauge=gauge, metric_contract=contract)
    old_import = builtins.__import__

    def checked_import(name, *args, **kwargs):
        if name == "cell_eval":
            pytest.fail("mismatched evaluator was imported before gauge refusal")
        return old_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", checked_import)
    with pytest.raises(ValueError, match="gauge"):
        evaluate_official_2025_v2(
            predicted=None,
            real=None,
            metric_contract=contract,
            metric_gauge=gauge,
            scratch_directory=tmp_path / "must-not-exist",
            num_threads=1,
        )
    assert not (tmp_path / "must-not-exist").exists()


def test_selected_final_and_validation_baselines_remain_distinct_and_supported():
    from empirical_lawhood.adapters.physical.virtual_cell.config import (
        virtual_cell_2025_validation_metric_contract,
    )

    gauge = OfficialMetricGaugeV2()
    columns = {
        "overlap_at_N": Decimal("0.3"),
        "discrimination_score_l1": Decimal("0.8"),
        "mae": Decimal("0.02"),
    }
    final = score_source_aggregate(
        columns=columns,
        gauge=gauge,
        metric_contract=virtual_cell_2025_metric_contract(),
    )
    validation = score_source_aggregate(
        columns=columns,
        gauge=gauge,
        metric_contract=virtual_cell_2025_validation_metric_contract(),
    )
    assert final.average_score != validation.average_score
