# SPDX-License-Identifier: MPL-2.0
"""Short supplied-innovation equation controls; no scientific/native entry."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science as method
from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS, MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import instrument
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseProtocol, physical_forecast_implementation
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests import test_matrix_coupling_preparation as preparation_fixture
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_later_programme import ref


@pytest.fixture
def case(tmp_path):
    metadata = preparation_fixture.metadata.__wrapped__(tmp_path)
    source, initial, coarse, bridge, _ = preparation_fixture.selected.__wrapped__(metadata)
    plane, old = metadata
    coordinates = tuple(replace(row, autonomous_ticks=row.autonomous_ticks + 2,
        observation_ticks=tuple(range(row.total_ticks + 3))) for row in old.allocation.coordinates)
    by_id = {row.coordinate_id: row for row in coordinates}
    allocation = replace(old.allocation, coordinates=coordinates,
        roots=tuple(replace(row, coordinate=coordinate_identity(by_id[row.root.coordinate_id])) for row in old.allocation.roots),
        matched_scopes=tuple(replace(row, coordinates=tuple(coordinate_identity(by_id[value.object_id]) for value in row.coordinates))
            for row in old.allocation.matched_scopes))
    reservation = replace(old.reservation, allocation=allocation,
        publication=publish(plane, allocation, "published.prepared-response.literal-allocation"))
    policy = replace(old.policy, origin_sector="Y")
    selection = replace(old.specification.selection, reservation=original.identity(reservation), prefix_policies=(policy,),
        coordinate_policies=tuple((coordinate_identity(row), original.identity(policy)) for row in coordinates))
    specification = replace(old.specification, selection=selection,
        publication=publish(plane, selection, "published.prepared-response.literal-selection"))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=old.index.provenances)
    reference = source_index.reference(source_id=old.source_id, root_id=old.root_id, provenance=old.reference.provenance)
    original_source = source_index.resolve(reference)
    source = replace(source, original=ScheduledPublicSource.from_source(original_source), root=original_source.root)
    source.validate_allocation(allocation)
    arrays = preparation_science.propagate_preparation(source, initial, coarse_innovations=coarse, bridge_innovations=bridge)
    preparation_raw, preparation = preparation_science.preparation_array_product(source, initial, arrays, artifact_id="array.prepared-response.literal-prefix")
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype="<c16")
    frame = np.asarray([np.kron(row, np.eye(2)) / 2 for row in pauli], dtype="<c16")
    templates = {"generic_basis": np.asarray([np.kron(np.eye(2), row) / 2 for row in pauli], dtype="<c16"),
        "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        "trace_coefficients": np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)}
    raw, members = encode_matrix_arrays(templates)
    template_operand = ScheduledResponseArrays("templates.prepared-response.literal", "TEMPLATES", source.original.source,
        ArtifactIdentity("array.prepared-response.literal-templates", "literal-templates", MATRIX_ARRAY_SCHEMA,
            sha256(raw).hexdigest(), "application/x-npz", len(raw)), members, (source.original.source,),
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    protocol = ScheduledResponseProtocol("protocol.prepared-response.literal", source.original, ref("criterion.literal-response"),
        MatrixFactorResponseModel("model.literal-response", physical_forecast_implementation()),
        tuple(MatrixFactorAction("action.literal-response." + role.lower(), role, D(".01"), 1, D(1)) for role in ACTION_ROLES),
        (1, 2, 3), 48, template_operand, D("1e-5"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-8"), D("1e-8"),
        D("1e-5"), D("1e-12"), D("1e-10"), "PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME")
    forces, receivers, _ = instrument(protocol, frame, templates)
    frozen = {"forces": forces, "receivers": receivers,
        **{view + "_" + predictor.lower(): np.zeros((4, 3, 48), dtype="<f8") for view in ("primary", "fine") for predictor in PREDICTORS}}
    frozen_raw, members = encode_matrix_arrays(frozen)
    forecast = method.MatrixPreparedForecastArrays("forecast.literal-prepared-response", source.identity,
        method.preparation_identity(preparation), ObjectIdentity.from_record(protocol.protocol_id, protocol),
        ArtifactIdentity("array.literal-prepared-response-predictions", "literal-supplied-predictions", MATRIX_ARRAY_SCHEMA,
            sha256(frozen_raw).hexdigest(), "application/x-npz", len(frozen_raw)), members)
    group = source.root.root.independent_group_id
    panels = (method.MatrixPreparedResponsePanel("panel.common", group, "COMMON_NOISE_PANEL", source.root.streams),
        method.MatrixPreparedResponsePanel("panel.independent", group, "INDEPENDENT_FUTURE",
            tuple(MatrixHistorySeed(purpose, sha256(("literal-prepared-response-" + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
    innovations = {panel.panel_id: {"primary": np.zeros((3, 2, 3, 4, 4), dtype="<c16"),
        "fine": np.zeros((6, 2, 3, 4, 4), dtype="<c16"), "bridge": np.zeros((3, 2, 3, 4, 4), dtype="<c16")} for panel in panels}
    return source, initial, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, innovations


def test_complete_prepared_response_readout_preserves_original48_controls240_cells_and15_outputs(case, monkeypatch):
    arrays = method.propagate_prepared_responses(*case)

    def forbidden(*args, **kwargs):
        raise AssertionError("prepared cold assessment entered a native producer, RNG or eigensolve")

    monkeypatch.setattr(method, "native_scheduled_branch", forbidden)
    monkeypatch.setattr(preparation_science, "acquire_preparation", forbidden)
    monkeypatch.setattr(preparation_science, "baoab_step_with_hermitian_noise", forbidden)
    monkeypatch.setattr(np.random, "Generator", forbidden)
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    result = method.assess_prepared_responses(*case[:-1], arrays, record_id="readout.literal-complete-prepared-response")
    assert result.numerical_pass and result.disposition == "FINITE"
    assert len(result.controls) == 48 and len(result.cells) == 240 and len(result.cumulative_log_errors) == 15
    assert sum(row.denominator_steps for row in result.controls) == 24 * 3 + 24 * 6
    assert {row.denominator_real_coordinates for row in result.controls} == {192}
    assert all(len(row.actual_odd_responses) == 48 for row in result.cells)
    assert result.source == case[0].identity and result.source.object_schema != original.ScheduledSource.SCHEMA
    assert "NO_FORECAST_CUSTODY" in result.standing and "CROSS_PREPARATION_APPLICABILITY" in result.standing
    damaged = {key: value.copy() for key, value in arrays.items()}
    key = next(key for key in damaged if key.startswith("branch.fine.") and key.endswith(".momenta"))
    damaged[key][1, 0, 0, 0, 0] += .01
    negative = method.assess_prepared_responses(*case[:-1], damaged, record_id="readout.literal-negative-prepared-response")
    assert not negative.numerical_pass and negative.disposition == "NATIVE_CROSSCHECK_FAILED"
    assert len(negative.cells) == 240 and len(negative.controls) == 48 and negative.cumulative_log_errors == (None,) * 15


def test_prepared_native_decoded_array_seam_preserves_every_supplied_branch_byte(case, monkeypatch):
    source, initial, preparation, raw, protocol, panels, forecast, frozen_raw, innovations = case
    expected = method.propagate_prepared_responses(*case)
    prefix = preparation_science.consume_preparation_arrays(source, initial, preparation, raw)
    frozen = method._context(source, preparation, protocol, panels, forecast, frozen_raw)
    def forbidden(*args, **kwargs):
        raise AssertionError("prepared native branch re-expanded its authenticated preflight arrays")
    monkeypatch.setattr(method, "_context", forbidden)
    monkeypatch.setattr(method, "consume_preparation_arrays", forbidden)
    actual = method._propagate_prepared_response_arrays(source, protocol, panels, innovations, prefix=prefix, frozen=frozen)
    assert set(actual) == set(expected)
    assert all((actual[key].dtype, actual[key].shape, actual[key].tobytes()) ==
        (value.dtype, value.shape, value.tobytes()) for key, value in expected.items())


def test_prepared_future_refuses_wrong_noise_before_native_branch_math(case, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("native branch entered before supplied innovation refusal")

    monkeypatch.setattr(method, "native_scheduled_branch", forbidden)
    bad = {key: {name: value.copy() for name, value in values.items()} for key, values in case[-1].items()}
    bad["panel.common"]["fine"][0, 0, 0, 0, 0] = .01
    with pytest.raises(ValueError):
        method.propagate_prepared_responses(*case[:-1], bad)


def test_prepared_response_refuses_source_or_full_branch_census_substitution(case):
    with pytest.raises(ValueError, match="subject"):
        method.propagate_prepared_responses(*case[:6], replace(case[6], source=replace(case[6].source, object_fingerprint="f" * 64)), *case[7:])
    arrays = method.propagate_prepared_responses(*case)
    del arrays[next(iter(arrays))]
    with pytest.raises(ValueError, match="members"):
        method.assess_prepared_responses(*case[:-1], arrays, record_id="readout.literal-forbidden-missing-branch")


@pytest.mark.parametrize("disposition", ("NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED"))
def test_unentered_prepared_assay_retains_every_case_without_native_or_finite_loss(case, disposition, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("unentered response entered native math")

    monkeypatch.setattr(method, "native_scheduled_branch", forbidden)
    source, _, preparation, _, protocol, panels, *_ = case
    result = method.unentered_prepared_responses(source, preparation, protocol, panels,
        record_id="readout.literal-unentered." + disposition.lower(), disposition=disposition)
    assert len(result.unentered_branch_ids) == 48 and not result.controls and len(result.cells) == 240
    assert result.cumulative_log_errors == (None,) * 15 and all(row.actual_odd_responses is None for row in result.cells)
    assert not result.numerical_pass and result.forecast is None



@pytest.mark.parametrize("precision", (28, 80))
def test_prepared_response_reuse_preserves_exact_decimal_and_negative_assessment(case, precision, monkeypatch):
    from decimal import localcontext
    from empirical_lawhood.infrastructure.matrix_array_io import DecodedMatrixArrayInput
    arrays = method.propagate_prepared_responses(*case)
    selected = DecodedMatrixArrayInput(case[7], case[6])
    damaged = {name: value.copy() for name, value in arrays.items()}
    key = next(name for name in damaged if name.startswith("branch.fine.") and name.endswith(".momenta"))
    damaged[key][1, 0, 0, 0, 0] += .01
    with localcontext() as context:
        context.prec = precision
        expected = tuple(method.assess_prepared_responses(*case[:-1], values, record_id="readout.literal-reuse")
            for values in (arrays, damaged))
        actual_decode = method.decode_matrix_arrays

        def decode(received, operand):
            if received is case[7]:
                pytest.fail("prepared assessment re-expanded its already authenticated forecast")
            return actual_decode(received, operand)

        monkeypatch.setattr(method, "decode_matrix_arrays", decode)
        monkeypatch.setattr(method, "native_scheduled_branch", lambda *_args, **_kwargs:
            pytest.fail("cold assessment reuse entered native producer"))
        monkeypatch.setattr(np.random, "Generator", lambda *_args, **_kwargs:
            pytest.fail("cold assessment reuse created RNG"))
        actual = tuple(method.assess_prepared_responses(*case[:-1], values, record_id="readout.literal-reuse", frozen_input=selected)
            for values in (arrays, damaged))
    assert actual == expected
    assert tuple(row.canonical_bytes() for row in actual) == tuple(row.canonical_bytes() for row in expected)
    assert actual[0].numerical_pass and not actual[1].numerical_pass
    assert all(len(row.controls) == 48 and len(row.cells) == 240 and len(row.cumulative_log_errors) == 15 for row in actual)
    assert actual[1].cumulative_log_errors == (None,) * 15



def test_prepared_response_refuses_duck_typed_decoded_holder_before_arrays(case, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(method, "decode_matrix_arrays", lambda *_args:
        pytest.fail("forged decoded holder reached array expansion"))
    forged = SimpleNamespace(for_operand=lambda *_args: pytest.fail("forged holder supplied fabricated arrays"))
    source, _, preparation, _, protocol, panels, forecast, frozen_raw, _ = case
    with pytest.raises(TypeError, match="actual decoded Matrix input"):
        method._context(source, preparation, protocol, panels, forecast, frozen_raw, frozen_input=forged)
