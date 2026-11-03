# SPDX-License-Identifier: MPL-2.0
"""Declared initial-condition controls; no acquired trajectory or qualification.

The public publication control discloses its original-custody stub. Independent
source/seed exclusion and original reserve authentication remain with the actual
production entry owner; the stub is never a scientific evidence fixture.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_initialization as domain
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_initialization_science as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_records as records
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science as consumer
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixPreparedOriginalCommitments
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.api import matrix_preparation_initialization as api
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane
from tests.test_matrix_prepared_source import prepared_bank
from tests.test_matrix_selected_protected import transfer, unpublished  # noqa: F401

ROOT = Path(__file__).parents[1]


def source_for_family(transfer, family):  # noqa: F811
    original = transfer.sources.closure.original(transfer.sources.closure.descriptors[0],
        index=transfer.sources.closure.source_index())
    coordinate = replace(original.coordinate, coordinate_id="coordinate.initialization." + family, family_id=family)
    root = replace(original.root, root=replace(original.root.root, coordinate_id=coordinate.coordinate_id,
        regime_id="regime.initialization." + family), coordinate=scheduled.coordinate_identity(coordinate))
    scope = scheduled.ScheduledMatchedScope("scope.initialization." + family, root.root.role,
        (root.root.independent_group_id,), (root.coordinate,),
        "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU")
    allocation = replace(original.allocation, allocation_id="allocation.initialization." + family,
        coordinates=(coordinate,), roots=(root,), matched_scopes=(scope,))
    reservation = scheduled.ScheduledReservation("reservation.initialization." + family, allocation,
        unpublished(allocation, "publication.initialization.allocation." + family))
    selection = replace(original.specification.selection, selection_id="selection.initialization." + family,
        reservation=scheduled.identity(reservation), prefix_policies=(original.policy,),
        coordinate_policies=((scheduled.coordinate_identity(coordinate), scheduled.identity(original.policy)),))
    specification = scheduled.ScheduledSpecification("specification.initialization." + family, selection,
        unpublished(selection, "publication.initialization.selection." + family))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=(original.provenance,))
    return index.resolve(index.reference(source_id="source.initialization." + family,
        root_id=root.root.root_id, provenance=original.provenance.identity))


def forbid_contact(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("declared initialization entered RNG, trajectory or native contact")
    for name in ("Generator", "PCG64DXSM", "default_rng"):
        monkeypatch.setattr(np.random, name, forbidden)
    monkeypatch.setattr(consumer, "acquire_preparation", forbidden)


@pytest.mark.parametrize("family", science.FOUR_FAMILY_PREPARATION_IDS)
def test_all_four_declared_initial_rules_produce_exact_common_state_without_rng(transfer, monkeypatch, family):  # noqa: F811
    source = source_for_family(transfer, family)
    forbid_contact(monkeypatch)
    before = source.reference.canonical_bytes()
    state, raw = science.initialize_source(source, source.provenance, state_id="state.disclosed.initialization", artifact_id="array.disclosed.initialization")
    actual = consumer.initial_state(state, raw)
    expected, alpha = science._literal_initial(source.coordinate)
    assert np.array_equal(actual.positions, expected["positions"]) and np.array_equal(actual.momenta, expected["momenta"])
    assert state.alpha_tilde == alpha and state.cutoff.clock_id == source.coordinate.clock_id
    assert state.cutoff.coordinate == 0 and state.consumed_streams == () and state.native_contact_count == 0
    assert not hasattr(state, "original_history") and not hasattr(state, "original_assessment")
    assert source.reference.canonical_bytes() == before
    assert decode_canonical_bytes(state.canonical_bytes(), records.MatrixPreparationInitialStateV2, maximum_bytes=None) == state
    if family == science.FOUR_FAMILY_PREPARATION_IDS[1]:
        assert np.linalg.norm(actual.positions) > 0
    else:
        assert np.linalg.norm(actual.positions) == 0  # Actual original 00 rule, not a TEST initial array.


def test_primary_and_fine_must_match_before_common_state_projection(transfer, monkeypatch):  # noqa: F811
    source = transfer.sources.closure.original(transfer.sources.closure.descriptors[0],
        index=transfer.sources.closure.source_index())
    original = science.initial_parameter_state
    calls = []
    def changed(coordinate):
        state = original(coordinate)
        calls.append(state)
        if len(calls) == 2:
            positions = state.positions.copy(); positions[0, 0, 0, 0] += 1
            return replace(state, positions=positions)
        return state
    monkeypatch.setattr(science, "initial_parameter_state", changed)
    with pytest.raises(ValueError, match="share the exact original tick-zero"):
        science.initialize_source(source, source.provenance, state_id="state.disclosed.views", artifact_id="array.disclosed.views")


def test_independent_proof_refuses_consistently_rehashed_wrong_state_before_native(transfer, monkeypatch):  # noqa: F811
    source = transfer.sources.closure.original(transfer.sources.closure.descriptors[0],
        index=transfer.sources.closure.source_index())
    state, raw = science.initialize_source(source, source.provenance, state_id="state.disclosed.mutation", artifact_id="array.disclosed.mutation")
    arrays, _ = science._literal_initial(source.coordinate)
    arrays["positions"][0, 0, 0, 0] += 1
    changed_raw, members = encode_matrix_arrays(arrays)
    changed = replace(state, members=members, array_artifact=replace(state.array_artifact,
        sha256=sha256(changed_raw).hexdigest(), size_bytes=len(changed_raw)))
    forbid_contact(monkeypatch)
    with pytest.raises(ValueError, match="independent complete original Q2"):
        consumer.initial_state(changed, changed_raw)
    assert consumer.initial_state(state, raw).step_index == 0
    for values in ({"cutoff": replace(state.cutoff, clock_id="clock.foreign")}, {"alpha_tilde": (Decimal(1), Decimal(1))},
            {"native_contact_count": 1}, {"consumed_streams": (source.root.stream_identity(source.root.streams[0]),)}):
        with pytest.raises(ValueError): replace(state, **values)


def initialization_request(transfer):  # noqa: F811
    bank = prepared_bank(transfer)
    closure = bank.sources.closure
    sources = domain.MatrixPreparationInitializationSources("sources.disclosed.initialization", closure.reservation,
        closure.specification, closure.provenances, closure.descriptors, closure.audit, closure.audit_publication)
    locator = MatrixFiniteDtTrainingLocator("unexecuted/original-train", "run.unexecuted.original-train",
        ObjectIdentity("packet.unexecuted.original-train", AuthoredRecursiveWave.SCHEMA, "1.0.0", "a" * 64),
        ObjectIdentity("plan.unexecuted.original-train", DevelopmentExecutionPlan.SCHEMA, "1.0.0", "b" * 64))
    commitments = MatrixPreparedOriginalCommitments("commitments.disclosed.initialization", locator, bank.input_commitments, 128 * 1024**2)
    return domain.MatrixPreparationInitializationRequest("request.disclosed.initialization", "disclosed.initialization", "E6_TRANSFER",
        sources, commitments, bank.exposure_support)


def test_public_input_derivation_and_cold_file_loader_reopen_explicit_v2_bank(transfer, tmp_path, monkeypatch):  # noqa: F811
    request = initialization_request(transfer)
    specification = domain.MatrixPreparationInitializationSpecification("specification.disclosed.initialization", request.identity)
    plane = _matrix_plane(tmp_path / "custody")
    copied = tmp_path / "copied"; copied.mkdir()
    (copied / "request.json").write_bytes(request.canonical_bytes())
    (copied / "specification.json").write_bytes(specification.canonical_bytes())
    selected = ExperimentFileInputSelection("selection.disclosed.initialization", domain.PROTOCOL_ID,
        (ExperimentInputBinding("request", request.identity, "request.json", len(request.canonical_bytes())),), ())
    (copied / "sources.json").write_bytes(selected.canonical_bytes())
    # This isolated metadata-publication control has no genuine completed TRAIN
    # or E4 history. The production custody owner is tested for refusal below.
    calls = []
    from contextlib import contextmanager
    @contextmanager
    def disclosed(**kwargs):
        calls.append("disclosed-original-custody-control")
        kwargs["request"].__post_init__()
        assert kwargs["maximum_source_bytes"] == request.original_commitments.maximum_source_bytes
        yield
    monkeypatch.setattr(api, "authenticated_initialization_request", disclosed)
    execution = ExecutionSelection(4, "environment.disclosed.initialization",
        ObjectIdentity.from_record("recursive-member.implementation", implementation_binding(ROOT)), str(tmp_path / "custody"))
    result = derive_experiment_inputs(specification_path=copied / "specification.json", source_selection_path=copied / "sources.json",
        project_root=ROOT, artifact_writer=plane, metadata_directory=tmp_path / "custody/current", output_selection_path=tmp_path / "custody/current/sources.json",
        execution=execution)
    assert calls == ["disclosed-original-custody-control"]
    assert result.preparation.census.native_effect_count == 0 and not result.preparation.dependencies
    reopened = load_experiment_inputs(specification, result.source_selection_path)
    assert len(reopened.method_inputs[1].states) == len(request.sources.descriptors) == 2
    assert all(type(state) is records.MatrixPreparationInitialStateV2 for _, state in reopened.method_inputs[1].states)
    assert all(binding.relative_path.startswith("initial-state.") and ".." not in binding.relative_path for binding in result.source_selection.files)
    before = transfer.canonical_bytes()
    assert decode_canonical_bytes(before, type(transfer), maximum_bytes=None).canonical_bytes() == before
    assert all(type(source.initial) is records.MatrixPreparationInitialState for _, source in transfer.sources.source_arms())
    # Preserve the scientific guard: genuine original deanneal tick0 starts at
    # (8,8); existing HOLD targets (2/3,22/3). Initialization does not retune it.
    closure = reopened.method_inputs[1].prepared_closure(record_id="closure.disclosed.initialization",
        numerical_scope=scheduled.identity(request.sources.specification.selection.numerical_design))
    descriptor = closure.descriptors[0]
    recipe = dict(transfer.sources.recipes)[descriptor.coordinate]
    with pytest.raises(ValueError, match="initial coupling or restored handoff"):
        closure.prepare_source(descriptor, recipe, index=closure.source_index())


def test_missing_actual_original_prerequisite_refuses_before_any_publication(transfer, tmp_path):  # noqa: F811
    request = initialization_request(transfer)
    plane = _matrix_plane(tmp_path / "custody")
    before = tuple(sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")))
    with pytest.raises((PermissionError, OSError, ValueError)):
        api.authenticate_initialization_request(writer=plane, request=request, maximum_source_bytes=128 * 1024**2)
    assert tuple(sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))) == before


def test_public_pin_accepts_exact_v2_edition_and_refuses_foreign_version(transfer):  # noqa: F811
    source = transfer.sources.closure.original(transfer.sources.closure.descriptors[0],
        index=transfer.sources.closure.source_index())
    state, _ = science.initialize_source(source, source.provenance, state_id="state.disclosed.public", artifact_id="array.disclosed.public")
    prepared = transfer.sources.source_arms()[0][1]
    value = MatrixPreparedPublicSource(prepared.identity, ScheduledPublicSource.from_source(source), prepared.recipe.identity, state.identity)
    with pytest.raises(ValueError): replace(value, initial=replace(value.initial, object_version="99.0.0"))
