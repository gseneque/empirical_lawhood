# SPDX-License-Identifier: MPL-2.0
"""Literal in-memory selected-product controls; no publications or authority."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_package as selected
from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as original
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import selected_deanneal_specification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES, FEATURE_BLOCKS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, ScheduledReservation, ScheduledSpecification
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase, InformationCutoff
from empirical_lawhood.runtime.experimental_statistics import StandardizedRidgeParameters


def reference(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(("EXPOSED." + name).encode()).hexdigest())


def package(*, missing=0, transfer_count=1):
    """Synthetic original records only, deliberately without custody or signers."""
    spec = selected_deanneal_specification(protocol_sha256="a" * 64)
    counts = {"TRAIN": 2, "CALIBRATION": 20, "EVALUATION": 1, "TRANSFER_NEARBY": transfer_count, "TRANSFER_SHIFTED": transfer_count}
    spec = replace(spec, populations=tuple(replace(row, expected_units=counts[row.role]) for row in spec.populations),
        assessment=replace(spec.assessment, minimum_usable_units=1))
    refs = tuple(sorted((reference("original.train", UnitAllocation), reference("original.scheduled", ScheduledAllocation),
        reference("original.reservation", ScheduledReservation), reference("original.native", ScheduledSpecification)), key=lambda row: row.object_id))
    roles = tuple(sorted((UnitRoleAssignment(f"group.{row.role.lower()}.{index:02}", row.role.lower())
        for row in spec.populations for index in range(row.expected_units)), key=lambda row: row.unit_id))
    allocation = UnitAllocation("allocation.literal-selected", refs,
        tuple(IndependentUnit(row.unit_id, "original.train" if row.role == "train" else "original.scheduled",
            "matrix-history.joint-decreasing-coupling", ("fine", "primary"), row.role == "train") for row in roles), roles)
    refs = {row.object_id: row for row in refs}
    availability = AvailabilitySpec("clock.literal-publications", CausalPhase.PREPARATION, OutcomeAccess.OUTCOME_BLIND, D(0))
    publications = tuple((key, ArtifactIdentity("publication." + key, "synthetic-in-memory", ref.object_schema,
        ref.object_fingerprint, "application/json", 1), "materialization." + key, availability)
        for key, ref in (("allocation", refs["original.scheduled"]), ("native-selection", refs["original.native"]),
            ("reservation", refs["original.reservation"]), ("roles", allocation.identity)))
    prefit = ProtectedE3PreFitJoin("prefit.literal-selected", spec.identity, allocation.identity, refs["original.train"],
        refs["original.scheduled"], refs["original.reservation"], refs["original.native"], publications,
        InformationCutoff("cutoff.literal-publications", availability.clock_id, CausalPhase.PREPARATION, D(1)))
    estimators = []
    for method in spec.methods:
        names = tuple(sorted(name for block in method.feature_blocks for name in FEATURE_BLOCKS[block]))
        parameters = tuple(StandardizedRidgeParameters((D("0.000"),) * len(names), (D("1.000"),) * len(names),
            (False,) * len(names), (D(str((-1, 2, 1)[index % 3])), *((D("0.0000"),) * len(names))), 2, 2)
            for index in range(15)) if names else (None,) * 15
        constants = (None,) * 15 if names else (D("0.000"), D("3.000"), D("1.000")) * 5
        estimators.append(original.MatrixE3EstimatorModel(method.method_key, names, parameters, constants,
            allocation.unit_ids("train"), (2,) * 15))
    models = e3.ProtectedE3ModelSet("models.literal-selected", spec.identity, allocation.identity, prefit.identity,
        reference("train.features", original.MatrixE3FeatureBank), reference("train.outcomes", original.MatrixE3OutcomeBank), tuple(estimators))
    frozen = e3.freeze_protected_e3(spec, allocation, models, record_id="freeze.literal-models")
    units = allocation.unit_ids("calibration")
    scores = tuple((unit, None if index < missing else D(f"0.{index:03}00"),
        ("MISSING_POINT_OR_TARGET",) if index < missing else ("FINITE_WHOLE_UNIT_MAX15",)) for index, unit in enumerate(units))
    calibration = e3.ProtectedE3Calibration("calibration.literal-selected", spec.identity, allocation.identity, e3.identity(models),
        e3.identity(frozen), scores, 20, None if missing else scores[-1][1],
        tuple(reference("forecast." + unit, e3.ProtectedE3Forecast) for unit in units),
        tuple(reference("outcome." + unit, e3.ProtectedE3PairedOutcome) for unit in units))
    calibrated = e3.freeze_protected_e3(spec, allocation, models, record_id="freeze.literal-calibrated", model_freeze=frozen, calibration=calibration)
    use = tuple(sorted((*units, *allocation.unit_ids("evaluation"))))
    return selected.adapt_e3_frozen_package(record_id="selected.literal-products", specification=spec, allocation=allocation,
        prefit=prefit, models=models, model_freeze=frozen, calibration=calibration, calibrated_freeze=calibrated, selection_unit_ids=use)


def test_exact_original_parameters_calibration_and_decimal_bytes_survive_handoff():
    value = package()
    before = tuple(row.canonical_bytes() for row in (value.models, value.calibration, value.model_freeze, value.calibrated_freeze))
    restored = decode_canonical_bytes(value.canonical_bytes(), selected.MatrixSelectedFrozenPackage, maximum_bytes=None)
    assert restored == value
    assert tuple(row.canonical_bytes() for row in (restored.models, restored.calibration, restored.model_freeze, restored.calibrated_freeze)) == before
    assert value.calibration.rank == 20 and value.calibration.radius.as_tuple() == D("0.01900").as_tuple()
    assert value.models.models[-1].ridge_parameters[0].scales[0].as_tuple() == D("1.000").as_tuple()
    assert len(value.endpoint_order) == 15
    assert value.endpoint_order[2] == (value.specification.measurement.descriptions[0], 128)


def test_literal_original_transform_and_median_are_used_without_refitting(monkeypatch):
    value = package()
    def forbidden(*args, **kwargs):
        raise AssertionError("downstream point prediction refits")
    monkeypatch.setattr(selected.numerical, "fit_estimator_values", forbidden)
    points = dict(selected.predict_selected_points(value, values=tuple((name, D("0.500")) for name in FEATURES)))
    assert points["SPECTRAL_RIDGE"] == points["ALL_ORIGIN_RIDGE"] == (D(0), D(2), D(2)) * 5
    with localcontext() as context:
        context.prec = 50
        assert points["RAW_TRAIN_MEDIAN"] == (D(0), D(4).ln(), D(4).ln()) * 5
    assert all(points == (None,) * 15 for _, points in selected.predict_selected_points(value, values=(), disposition="NO_CAUSAL_ORIGIN"))
    with pytest.raises(ValueError, match="complete original"):
        selected.predict_selected_points(value, values=tuple((name, D(0)) for name in FEATURES[:-1]))


def test_missing_calibration_retains_infinite_radius_and_all_original_roots():
    value = package(missing=1)
    assert value.calibration.radius is None and len(value.calibration.scores) == 20
    assert value.calibration.scores[0][1:] == (None, ("MISSING_POINT_OR_TARGET",))
    assert value.calibration_scope == (value.specification.identity, value.allocation.identity, e3.identity(value.model_freeze))


@pytest.mark.parametrize("damage", ("rank", "radius", "population", "mask", "prefit", "selection", "reserve"))
def test_join_and_scope_substitutions_refuse_even_when_outer_records_are_resealed(damage):
    value = package()
    with pytest.raises(ValueError):
        if damage in ("rank", "radius"):
            cal = replace(value.calibration, rank=19) if damage == "rank" else replace(value.calibration, radius=D(".018"))
            frozen = e3.freeze_protected_e3(value.specification, value.allocation, value.models,
                record_id=value.calibrated_freeze.record_id, model_freeze=value.model_freeze, calibration=cal)
            replace(value, calibration=cal, calibrated_freeze=frozen)
        elif damage == "population":
            replace(value, allocation=replace(value.allocation, roles=tuple(replace(row, role="evaluation") if row.role == "calibration" else row for row in value.allocation.roles)))
        elif damage == "mask":
            models = list(value.models.models)
            models[-1] = replace(models[-1], feature_names=tuple("foreign." + name for name in models[-1].feature_names))
            replace(value, models=replace(value.models, models=tuple(models)))
        elif damage == "prefit":
            changed = tuple((key, replace(artifact, sha256="f" * 64) if key == "reservation" else artifact, materialization, availability)
                for key, artifact, materialization, availability in value.prefit.publications)
            prefit = replace(value.prefit, publications=changed)
            replace(value, prefit=prefit)
        elif damage == "selection":
            replace(value, selection_unit_ids=value.selection_unit_ids[:-1])
        else:
            replace(value, selection_unit_ids=tuple(sorted((*value.selection_unit_ids, *value.allocation.unit_ids("transfer_nearby")))))


def test_complete_reserved_transfer_is_kept_distinct_from_upstream_and_new_labels():
    value = package()
    reserve = tuple(sorted((*value.allocation.unit_ids("transfer_nearby"), *value.allocation.unit_ids("transfer_shifted"))))
    value.require_reserved_transfer_groups(reserve, reservation=value.prefit.reservation)
    with pytest.raises(ValueError, match="complete original pre-fit reserve"):
        value.require_reserved_transfer_groups(reserve[:1], reservation=value.prefit.reservation)
    with pytest.raises(ValueError, match="complete original pre-fit reserve"):
        value.require_reserved_transfer_groups(reserve, reservation=replace(value.prefit.reservation, object_id="renamed.reserve"))
    with pytest.raises(ValueError, match="upstream"):
        value.require_unused_groups(value.training_unit_ids)


@pytest.mark.parametrize("phase", selected.DOWNSTREAM_PHASES)
def test_carried_primary_calibration_never_becomes_a_downstream_or_comparator_bound(phase):
    value = package()
    with pytest.raises(ValueError, match=selected.POINT_ONLY):
        selected.require_downstream_calibration(value, phase=phase)
    assert value.calibration.radius is not None
