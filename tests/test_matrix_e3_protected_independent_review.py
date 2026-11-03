# SPDX-License-Identifier: MPL-2.0
"""Independent bounded metadata/math review; no acquisition or qualification.

Producer fixtures supply disclosed inputs. Independent assertions cover source
joins, canonical preservation and adverse complete-denominator boundaries.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import e3_numerical_methods as numerical
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as protected
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import project_protected_e3_allocation
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests import test_matrix_e3_protected_methods as producer
from tests.test_matrix_e3_protected_inputs import (
    build_source_inputs, source_inputs as source_inputs, scheduled as scheduled, stock as stock, provenance as provenance,
)


def reference(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


def test_selected320_original_roles_and_all_four_stream_purposes(scheduled):
    case = build_source_inputs(scheduled, selected64=True)
    allocation = project_protected_e3_allocation(case.inputs)
    assert allocation.role_counts == (("calibration", 64), ("evaluation", 64), ("train", 64), ("transfer_nearby", 64), ("transfer_shifted", 64))
    assert len(allocation.units) == 320 and len({row.unit_id for row in allocation.units}) == 320
    assert len(case.inputs.reservation.allocation.roots) == 256
    assert original.identity(case.inputs.reservation) in allocation.sources
    assert original.identity(case.inputs.native_specification) in allocation.sources
    assert case.inputs.training_allocation.identity in allocation.sources
    by_group = {row.root.independent_group_id: row for row in case.inputs.reservation.allocation.roots}
    seeds = set()
    for role in ("calibration", "evaluation", "transfer_nearby", "transfer_shifted"):
        for unit in allocation.unit_ids(role):
            root = by_group[unit]
            assert len(root.streams) == 4
            assert all(stream.effective_seed not in seeds for stream in root.streams)
            seeds.update(stream.effective_seed for stream in root.streams)
    assert len(seeds) == 1024
    assert producer.join(case).allocation == allocation.identity


def test_primary_train_and_even_raw_median_remain_independently_distinguishable(source_inputs):
    case = source_inputs
    features = replace(case.train_features, rows=tuple(replace(row, values=case.train_features.rows[0].values) for row in case.train_features.rows))
    outcomes = replace(case.train_outcomes, rows=tuple(replace(row, views=tuple(replace(view,
        errors=(D(0 if index % 2 == 0 else 3) + (D(".00005") if view.view_id == "fine" else 0),) * 15)
        for view in row.views)) for index, row in enumerate(case.train_outcomes.rows)))
    models = protected.fit_protected_e3_models(case.inputs, producer.join(case), features, outcomes, record_id="review.primary-train")
    with localcontext() as context:
        context.prec = 50
        expected = D(4).ln() / 2
        wrong_median = ((D(1).ln() + D(4).ln()) / 2).exp() - 1
    for model in models.models:
        assert model.finite_counts == (12,) * 15
        if model.method_key == "RAW_TRAIN_MEDIAN":
            assert model.raw_constants == (D("1.5"),) * 15
            assert model.raw_constants[0] != wrong_median
        else:
            assert all(abs(row.coefficients[0] - expected) < D("1e-14") for row in model.ridge_parameters)


def test_missing_three_calibration_units_keep_rank62_infinite(scheduled):
    case = build_source_inputs(scheduled, selected64=True)
    models, frozen = producer.fitted(case)
    before = models.canonical_bytes()
    _, _, calibration, sealed = producer.calibrated(case, models, frozen, missing_count=3)
    assert calibration.rank == 62 and calibration.radius is None and len(calibration.scores) == 64
    assert sum(value is None for _, value, _ in calibration.scores) == 3
    assert sealed.models == frozen.models and models.canonical_bytes() == before
    assert Fraction(case.inputs.specification.assessment.null_probability) == Fraction(1, 2)
    assert Fraction(case.inputs.specification.assessment.alpha) == Fraction(1, 240)


@pytest.mark.parametrize("field", ("specification", "allocation"))
def test_calibrated_freeze_rejects_foreign_original_model_freeze_scope(source_inputs, field):
    case = source_inputs
    models, frozen = producer.fitted(case)
    _, _, calibration, _ = producer.calibrated(case, models, frozen)
    kind = MatrixResponseErrorSpecification if field == "specification" else UnitAllocation
    foreign = replace(frozen, **{field: reference("review.foreign." + field, kind)})
    calibration = replace(calibration, model_freeze=protected.identity(foreign))
    with pytest.raises(ValueError):
        protected.freeze_protected_e3(case.inputs.specification, case.allocation, models,
            record_id="review.refused-foreign-freeze", model_freeze=foreign, calibration=calibration)


@pytest.mark.parametrize("thin", ("actual", "errors"))
def test_projection_rejects_short_original_receiver_denominators(source_inputs, thin):
    case = source_inputs
    source, selection, forecast, score = producer.projection_fixture(case)
    first = score.cells[0]
    change = {"actual_odd_responses": first.actual_odd_responses[:-1]} if thin == "actual" else {
        name: getattr(first, name)[:-1] for name in ("signed_errors", "absolute_errors", "relative_errors")}
    damaged = replace(score, cells=(replace(first, **change), *score.cells[1:]))
    # Original records accept arbitrary nonempty vector lengths. The complete
    # source/protocol wrapper therefore must establish its actual48 denominator.
    damaged.__post_init__()
    with pytest.raises(ValueError):
        protected.project_protected_e3_outcome(case.inputs.specification, source, selection, forecast, damaged,
            record_id="review.refused-short-receivers")


def test_projection_requires_exact_prospective_specification_owner(source_inputs):
    case = source_inputs
    source, selection, forecast, score = producer.projection_fixture(case)
    duck = SimpleNamespace(identity=case.inputs.specification.identity, measurement=case.inputs.specification.measurement)
    with pytest.raises(TypeError):
        protected.project_protected_e3_outcome(duck, source, selection, forecast, score, record_id="review.refused-duck-spec")


def test_projection_rejects_changed_force_normalization_under_same_specification(source_inputs):
    case = source_inputs
    source, selection, forecast, score = producer.projection_fixture(case)
    changed = replace(selection.protocols[0], actions=tuple(replace(action, force_norm=D(2)) for action in selection.protocols[0].actions))
    selection = replace(selection, protocols=(changed,))
    with pytest.raises(ValueError):
        protected.project_protected_e3_outcome(case.inputs.specification, source, selection, forecast, score,
            record_id="review.refused-changed-force-scale")


@pytest.mark.parametrize("changed_scope", ("source-allocation", "native-role"))
def test_calibration_rechecks_original_source_and_native_role_of_received_forecast(source_inputs, changed_scope):
    case = source_inputs
    models, frozen = producer.fitted(case)
    fs, ys, _, _ = producer.calibrated(case, models, frozen)
    feature = fs[0].feature
    if changed_scope == "source-allocation":
        foreign = reference("review.foreign.original-allocation", original.ScheduledAllocation)
        public = replace(feature.public_source, allocation=foreign)
        feature = replace(feature, public_source=public, source_manifest=foreign)
    else:
        public = replace(feature.public_source, root=replace(feature.public_source.root, role=MatrixProgrammeRole.CONFIRMATION))
        feature = replace(feature, public_source=public)
    changed = replace(fs[0], feature=feature)
    observed = replace(ys[0], feature=feature, forecast=protected.identity(changed))
    with pytest.raises(ValueError):
        protected.calibrate_protected_e3(case.inputs.specification, case.allocation, models, frozen,
            (changed, *fs[1:]), (observed, *ys[1:]), record_id="review.refused-foreign-cal-source")


def test_strict_paired_margin_requires_each_baseline_and_both_original_views(source_inputs):
    spec = source_inputs.inputs.specification
    primary_index = 2
    with localcontext() as context:
        context.prec = 50
        good, bad = (1 + D(".05")).ln(), (1 + D(".051")).ln()
    menu = {name: (good if name == "SPECTRAL_RIDGE" else bad,) * 15 for name in producer.old.METHODS}
    # The SAME PRIMARY point menu is reused at FINE; no view-specific retraining.
    y = SimpleNamespace(view=lambda name: SimpleNamespace(errors=(D(".05"),) * 15))
    usable, success, comparisons, _ = numerical.paired_root_decision(spec, menu, y, primary_index, ())
    assert usable and success and len(comparisons) == 4
    for baseline in ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN"):
        altered = dict(menu)
        altered[baseline] = menu["SPECTRAL_RIDGE"]
        assert not numerical.paired_root_decision(spec, altered, y, primary_index, ())[1]
    mixed = SimpleNamespace(view=lambda name: SimpleNamespace(errors=(D(".051") if name == "fine" else D(".05"),) * 15))
    assert not numerical.paired_root_decision(spec, menu, mixed, primary_index, ())[1]
