# SPDX-License-Identifier: MPL-2.0
"""Configured protected data/custody/math controls; no scientific authority."""
from dataclasses import replace
from decimal import Decimal
import pytest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_inputs as inputs_owner
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import ConfiguredE3CoordinateCensus
from tests.test_matrix_configured_e3_v2 import configured_case
from tests.test_matrix_e3_original_publications import case as original_case  # noqa: F401
from tests.test_matrix_e3_protected_methods import causal as original_causal, reference
from tests.test_matrix_factor_confirmation_eligibility import publish
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as source_records, response_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as exposed_science
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_originals as custody



def causal(case, unit, *, source_index=None):
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_records as current
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_feature_records import ConfiguredProtectedE3CausalFeature
    source, observed = original_causal(case, unit, source_index=source_index)
    kinds = {kind.SCHEMA.replace("/configured-protected-", "/protected-"): kind for kind in (
        current.ConfiguredProtectedE3CausalPrefix, current.ConfiguredProtectedE3NumericalAssessment,
        current.ConfiguredProtectedE3PrefixWitness, current.ConfiguredProtectedE3FrameAssessment)}
    def fresh_literal(pin):
        kind = kinds[pin.object_schema]
        return type(pin)(pin.object_id + ".configured-literal", kind.SCHEMA, kind.VERSION, pin.object_fingerprint)
    feature = ConfiguredProtectedE3CausalFeature(observed.record_id + ".configured-literal", observed.source_manifest,
        observed.public_source, fresh_literal(observed.prefix), observed.frame_sha256, observed.disposition, observed.values,
        tuple(sorted((fresh_literal(value) for value in observed.evidence), key=lambda value: value.object_id)))
    return source, feature

def selected(case):
    exposed, _ = configured_case()
    source = case.inputs
    role_coordinates = tuple((role, coordinate_identity(source.nearby if role == "TRANSFER_NEARBY" else
        source.shifted if role == "TRANSFER_SHIFTED" else source.nominal)) for role in tuple(role for role, _ in exposed.role_coordinates))
    specification = ConfiguredProtectedE3Specification("experiment.configured-protected.disclosed", exposed.question,
        exposed.protocol, source.specification.populations, exposed.methods, exposed.assessment,
        exposed.calibration_alpha, role_coordinates, evidence_scope="PROSPECTIVE_REQUIRED",
        calibration_target_view="MAX_PAIRED_VIEWS")
    # Match original fixture census while selecting new scientific parameters.
    specification = replace(specification, assessment=replace(specification.assessment,
        minimum_usable_units=min(8, specification.population("EVALUATION").expected_units)))
    coordinates = ConfiguredE3CoordinateCensus("coordinates.configured-protected.train", tuple(
        (row.unit_id, row.native_source, dict(role_coordinates)["TRAIN"]) for row in case.train_features.rows))
    inputs = inputs_owner.ConfiguredProtectedE3SourceInputs(specification, source.training_allocation,
        source.reservation, source.native_specification, source.nominal, source.nearby, source.shifted, coordinates)
    allocation = inputs_owner.project_protected_e3_allocation(inputs)
    return inputs, allocation


def test_configured_protected_spec_is_distinct_and_preserves_explicit_original_coordinates(original_case):  # noqa: F811
    inputs, allocation = selected(original_case)
    specification = inputs.specification
    assert specification.SCHEMA != original_case.inputs.specification.SCHEMA
    assert decode_canonical_bytes(specification.canonical_bytes(), type(specification), maximum_bytes=None) == specification
    assert allocation.unit_ids() == original_case.allocation.unit_ids()
    assert allocation.identity != original_case.allocation.identity
    assert specification.methods[0].ridge_lambda == Decimal(2)
    with pytest.raises(ValueError):
        replace(specification, evidence_scope="EXPOSED_CONFORMANCE")
    with pytest.raises(ValueError):
        replace(inputs, nominal=inputs.nearby)


def test_configured_prefit_requires_versioned_join_and_never_relabels_old_publications(original_case):  # noqa: F811
    inputs, allocation = selected(original_case)
    with pytest.raises(TypeError):
        science.fit_protected_e3_models(inputs, object(), original_case.train_features,
            original_case.train_outcomes, record_id="models.refuse-old-join")
    roles = original_case.allocation
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import E3RequiredPublication
    publications = tuple(E3RequiredPublication(key, {"allocation": inputs.reservation.allocation,
        "native-selection": inputs.native_specification.selection, "reservation": inputs.reservation,
        "roles": roles}[key], publication, availability) for key, publication, availability in original_case.publications)
    with pytest.raises(ValueError, match="substitutes original"):
        inputs_owner.require_e3_reserved_fit_inputs(inputs, publications=publications,
            ports={row.key: object() for row in publications}, fit_cutoff=original_case.fit_cutoff,
            record_id="prefit.refuse-old-roles")
    assert allocation.identity != roles.identity


def original_metadata(case, inputs, allocation):
    values = {"allocation": inputs.reservation.allocation, "native-selection": inputs.native_specification.selection,
        "reservation": inputs.reservation, "roles": allocation}
    publications = tuple(inputs_owner.E3RequiredPublication(key, values[key],
        publish(case.plane, allocation, "configured-protected.roles." + allocation.fingerprint()) if key == "roles" else publication,
        availability) for key, publication, availability in case.publications)
    old = case.originals
    originals = custody.ConfiguredProtectedE3OriginalPublications("originals.configured-protected.disclosed",
        inputs.specification.identity, old.source_manifest, old.training_allocation, old.manifest_publication,
        old.training_allocation_publication, old.exposure_census_publication)
    return publications, originals


def actual_join(case, inputs, allocation):
    publications, originals = original_metadata(case, inputs, allocation)
    ports = {row.key: case.plane.open(VerifiedArtifactInput(row.publication.logical, row.publication.materialization),
        maximum_bytes=None) for row in publications}
    try:
        custody.authenticate_protected_e3_fit_originals(case.plane, originals,
            specification=inputs.specification.identity, allocation=allocation.identity,
            source_manifest=source_records.identity(case.manifest), training_allocation=inputs.training_allocation.identity,
            publications=tuple((row.key, row.publication, row.availability) for row in publications), fit_cutoff=case.fit_cutoff)
        joined = inputs_owner.require_e3_reserved_fit_inputs(inputs, publications=publications, ports=ports,
            fit_cutoff=case.fit_cutoff, record_id="prefit.configured-protected.disclosed")
        return joined, (case.train_features, case.train_outcomes)
    finally:
        for port in ports.values():
            port.close()


def paired_outcome(forecast, *, missing=False):
    views = tuple(exposed_science.MatrixE3ViewOutcome(view, (None if missing else Decimal("0.05"),) * 15,
        ("UNKNOWN_CONTACT" if missing else "FINITE",) * 15) for view in ("fine", "primary"))
    return science.ConfiguredProtectedE3PairedOutcome("outcome.configured." + forecast.feature.unit_id, forecast.feature,
        science.identity(forecast), reference("score." + forecast.feature.unit_id, response_records.ScheduledResponseScore),
        "b" * 64, reference("protocol." + forecast.feature.unit_id, response_records.ScheduledResponseProtocol),
        (reference("panel.common." + forecast.feature.unit_id, response_records.ScheduledResponsePanel),
         reference("panel.independent." + forecast.feature.unit_id, response_records.ScheduledResponsePanel)),
        views, "UNEVALUABLE" if missing else "SATISFIED")


def test_actual_configured_publication_custody_and_complete_protected_math(original_case):  # noqa: F811
    from tests.test_matrix_configured_protected_statistical import case as native_case
    case = native_case.__wrapped__(original_case)
    inputs, allocation = case.inputs, case.allocation
    original_bytes = tuple(record.canonical_bytes() for record in (original_case.inputs.specification,
        original_case.manifest, original_case.inputs.training_allocation))
    joined, (features, outcomes) = actual_join(case, inputs, allocation)
    models = science.fit_protected_e3_models(inputs, joined, features, outcomes, record_id="models.configured-protected.disclosed")
    assert models.specification == inputs.specification.identity and models.reservation_join == joined.identity
    frozen = science.freeze_protected_e3(inputs.specification, allocation, models, record_id="freeze.configured-protected.models")
    source_index = ScheduledSourceIndex.from_shared(reservation=original_case.inputs.reservation,
        specification=original_case.inputs.native_specification, provenances=(original_case.provenance,))
    cal_forecasts = tuple(science.forecast_protected_e3(inputs.specification, allocation, models, frozen,
        causal(original_case, unit, source_index=source_index)[1], role="calibration", record_id="forecast.configured." + unit)
        for unit in allocation.unit_ids("calibration"))
    cal_outcomes = tuple(paired_outcome(row, missing=index == 0) for index, row in enumerate(cal_forecasts))
    calibration = science.calibrate_protected_e3(inputs.specification, allocation, models, frozen, cal_forecasts,
        cal_outcomes, record_id="calibration.configured-protected.disclosed")
    assert len(calibration.scores) == inputs.specification.population("CALIBRATION").expected_units
    assert calibration.scores[0][1] is None and calibration.rank == inputs.specification.calibration_rank
    sealed = science.freeze_protected_e3(inputs.specification, allocation, models, record_id="freeze.configured-protected.calibrated",
        model_freeze=frozen, calibration=calibration)
    forecasts = tuple(science.forecast_protected_e3(inputs.specification, allocation, models, sealed,
        causal(original_case, unit, source_index=source_index)[1], role="evaluation", record_id="forecast.configured." + unit, calibration=calibration)
        for unit in allocation.unit_ids("evaluation"))
    outcomes = tuple(paired_outcome(row, missing=index == 0) for index, row in enumerate(forecasts))
    assessment = science.assess_protected_e3(inputs.specification, allocation, sealed, forecasts, outcomes,
        record_id="assessment.configured-protected.disclosed")
    assert len(assessment.decisions) == inputs.specification.population("EVALUATION").expected_units
    assert not assessment.decisions[0].success and not assessment.decisions[0].usable
    assert assessment.specification == inputs.specification.identity
    for record in (joined, models, frozen, calibration, sealed, forecasts[0], outcomes[0], assessment):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    assert original_bytes == tuple(record.canonical_bytes() for record in (original_case.inputs.specification,
        original_case.manifest, original_case.inputs.training_allocation))
    with pytest.raises(ValueError):
        science.calibrate_protected_e3(inputs.specification, allocation, models, frozen,
            cal_forecasts[:-1], cal_outcomes[:-1], record_id="calibration.refuse-dropped")


def test_configured_fit_rejects_source_substitution_before_fitting(original_case):  # noqa: F811
    from tests.test_matrix_configured_protected_statistical import case as native_case
    case = native_case.__wrapped__(original_case)
    inputs, allocation = case.inputs, case.allocation
    joined, (features, outcomes) = actual_join(case, inputs, allocation)
    changed = replace(inputs.training_coordinates, assignments=tuple((unit, replace(source, object_fingerprint="f" * 64), coordinate)
        if index == 0 else (unit, source, coordinate) for index, (unit, source, coordinate) in enumerate(inputs.training_coordinates.assignments)))
    with pytest.raises(ValueError, match="source identities"):
        science.fit_protected_e3_models(replace(inputs, training_coordinates=changed), joined, features, outcomes,
            record_id="models.refuse-substitution")
