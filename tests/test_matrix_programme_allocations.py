# SPDX-License-Identifier: MPL-2.0
"""Exposed pre-TRAIN metadata controls; no scientific acquisition or authority."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import PHASE_INPUT_ROLES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_population import selected_e4_population_coordinates
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE
from empirical_lawhood.api import matrix_programme_allocations as compiler
from empirical_lawhood.kernel.decoding import decode_canonical_record
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_programme_scientific_design import scientific_design  # noqa: F401
from tests.test_matrix_programme_scientific_design import matched_scientific_design  # noqa: F401


ROOT = Path(__file__).parents[1]
NAMESPACE = "programme.software.complete"
MATERIALS = tuple(sha256(("disclosed.programme.material." + str(index)).encode()).hexdigest() for index in range(6))


@pytest.fixture
def census():
    path = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment/exposure-census.example.json"
    return decode_canonical_record(json.loads(path.read_text()), MatrixFactorExposureCensus)


def plan(design, census, **changes):
    values = dict(design=design, census=census, namespace=NAMESPACE, root_material=MATERIALS[0],
        future_material=MATERIALS[1], e4_streams=SelectedE4StreamRecipe("streams.disclosed.programme.e4",
            MATERIALS[2], MATERIALS[3], STREAM_RULE), e5_root_material=MATERIALS[4], e5_future_material=MATERIALS[5])
    return compiler._source_plan(**dict(values, **changes))


def test_pure_source_plan_retains_all_twelve_roles_and_complete_matched_units(scientific_design, census):  # noqa: F811
    e1, populations, groups, futures, folds = plan(scientific_design, census)
    assert tuple(role for role in PHASE_INPUT_ROLES if role in groups) == PHASE_INPUT_ROLES
    assert tuple((role, len(groups[role])) for role in PHASE_INPUT_ROLES) == scientific_design.phase_group_counts
    assert len(e1.roots) == sum(count for _, count in scientific_design.e1_family_counts)
    assert e1.coordinates == scientific_design.e1_coordinates
    assert sum(len(value) for value in groups.values()) == len({group for value in groups.values() for group in value})
    e4, = (population for population in populations if population.name == "e4")
    counts = Counter(row.root.independent_group_id for row in e4.roots)
    assert set(counts.values()) == {9}
    assert len(counts) == sum(getattr(scientific_design, "e4_" + phase).group_count
        for phase in ("development", "calibration", "confirmation"))
    for group in counts:
        rows = tuple(row for row in e4.roots if row.root.independent_group_id == group)
        assert len({row.coordinate for row in rows}) == 9
        assert len({row.streams for row in rows}) == 1
        assert rows[0].streams != futures[group]
    assert e4.coordinates == selected_e4_population_coordinates(scientific_design.e4_preparation_coordinates,
        scientific_design.e4_development, namespace=NAMESPACE + ".e4")
    assert set(dict(folds)) == set(groups["e4.development"])
    assert {fold for _, fold in folds} == set(range(scientific_design.e4_revision.fold_count))


def test_amended_source_plan_keeps_980_disjoint_groups_and_original_iid_family_draws(matched_scientific_design, census, monkeypatch):  # noqa: F811
    _forbid_acquisition(monkeypatch)
    streams = SelectedE4StreamRecipe('streams.disclosed.amended.e4', MATERIALS[2], MATERIALS[3], STREAM_RULE,
        sha256(b'disclosed.amended.family-allocation').hexdigest())
    e1, populations, groups, futures, folds = plan(matched_scientific_design, census, e4_streams=streams)
    assert len(e1.roots) == 384
    assert sum(map(len, groups.values())) == len({group for values in groups.values() for group in values}) == 980
    assert tuple((role, len(groups[role])) for role in PHASE_INPUT_ROLES) == matched_scientific_design.phase_group_counts
    assert matched_scientific_design.e1_criterion.allocation == scheduled.identity(e1)
    e4, = (population for population in populations if population.name == 'e4')
    assert len(e4.roots) == (16 + 20 + 32) * 9
    coordinates = {scheduled.coordinate_identity(co): co for co in e4.coordinates}
    actual = {}
    for row in e4.roots:
        group = row.root.independent_group_id
        family = coordinates[row.coordinate].family_id
        assert actual.setdefault(group, family) == family
        assert row.streams != futures[group]
    for role in ('e4.calibration', 'e4.confirmation'):
        assert tuple(actual[group] for group in groups[role]) == tuple(streams.family(group) for group in groups[role])
    assert Counter(actual[group] for group in groups['e4.development']) == {
        family: 4 for family, _ in matched_scientific_design.e1_family_counts}
    assert set(dict(folds)) == set(groups['e4.development'])


def test_phase_reader_retains_an_absent_iid_family_and_refuses_changed_draws_or_streams(
        matched_scientific_design, census, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import _require_phase_science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
    _forbid_acquisition(monkeypatch)
    # Fixed exposed arithmetic vector: CAL20 has counts 7/4/0/9. It exercises
    # the legitimate absent-family branch without redrawing any scientific bank.
    streams = SelectedE4StreamRecipe('streams.disclosed.absent-family', 'a' * 64, 'b' * 64, STREAM_RULE,
        '09c4c0faca5446bb54078bd94d00d4a8c2ad96316b29400262eea9a3df3162e7')
    _, populations, groups, _, _ = plan(matched_scientific_design, census, e4_streams=streams)
    e4, = (population for population in populations if population.name == 'e4')
    roots = tuple(root for root in e4.roots if root.root.independent_group_id in groups['e4.calibration'])
    assert sorted(Counter(streams.family(group) for group in groups['e4.calibration']).values()) == [4, 7, 9]
    panels = tuple((group, (
        ScheduledResponsePanel('common.' + group, group, 'COMMON_NOISE_PANEL',
            'ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES', streams.streams(group, future=False)),
        ScheduledResponsePanel('future.' + group, group, 'INDEPENDENT_FUTURE',
            'FRESH_DECLARED_FUTURE_START_AT_CUTOFF', streams.streams(group, future=True))))
        for group in groups['e4.calibration'])
    # This component seam supplies only the already-typed source-plan members.
    # The full public compiler test separately authenticates their publications.
    phase = SimpleNamespace(role='e4.calibration', reservation=SimpleNamespace(allocation=e4),
        native_specification=SimpleNamespace(selection=e4),
        responses=SimpleNamespace(panels=panels, calibration_criterion=matched_scientific_design.e4_calibration_criterion))
    def check(selected, selected_roots=roots):
        _require_phase_science(phase, matched_scientific_design,
            SimpleNamespace(namespace=NAMESPACE, e4_streams=selected), selected_roots)
    check(streams)
    for material in (None, 'd' * 64):
        with pytest.raises(ValueError, match='family draw'):
            check(replace(streams, family_seed_material_sha256=material))
    for field in ('prefix_seed_material_sha256', 'future_seed_material_sha256'):
        with pytest.raises(ValueError, match='history/future stream recipe'):
            check(replace(streams, **{field: 'e' * 64}))
    with pytest.raises(ValueError, match='corner or centre'):
        check(streams, roots[:-1])


@pytest.mark.parametrize("category", ("history", "future"))
def test_exposed_effective_stream_refuses_the_complete_plan_before_publication(scientific_design, census, category):  # noqa: F811
    group = "group." + NAMESPACE + ".train.000"
    material = MATERIALS[0 if category == "history" else 1]
    seed = compiler._ordinary_streams(material, group)[0].effective_seed
    exposed = replace(census, effective_seed_exclusions=tuple(sorted({*census.effective_seed_exclusions, seed})))
    with pytest.raises(ValueError, match="exposed|stream"):
        plan(scientific_design, exposed)


def test_exposed_phase_group_refuses_without_relabelling_assigned_units(scientific_design, census):  # noqa: F811
    group = "group." + NAMESPACE + ".e5.confirmation.000"
    exposed = replace(census, exposed_independent_groups=tuple(sorted({*census.exposed_independent_groups, group})))
    with pytest.raises(ValueError, match="exposed|group"):
        plan(scientific_design, exposed)


def test_cross_phase_reused_history_future_material_refuses(scientific_design, census):  # noqa: F811
    with pytest.raises(ValueError, match="effective streams"):
        plan(scientific_design, census, future_material=MATERIALS[0])


def test_e6_physical_key_cannot_enter_the_independent_e2_population(scientific_design, census):  # noqa: F811
    design = scientific_design
    nearby_pin = dict(design.e3.role_coordinates)["TRANSFER_NEARBY"]
    nearby, = (co for co in design.training_protocol.coordinates if scheduled.coordinate_identity(co) == nearby_pin)
    policy = design.e2.prefix_policies[0]
    changed = replace(design, e2=replace(design.e2, coordinates=(nearby,),
        coordinate_policies=((nearby_pin, scheduled.identity(policy)),)))
    with pytest.raises(ValueError, match="physical key reserved for E6"):
        plan(changed, census)


def test_multiple_e2_coordinates_need_explicit_scientific_assignment_rule(scientific_design, census):  # noqa: F811
    design = scientific_design
    coordinates = tuple(sorted((design.e2.coordinates[0], replace(design.e2.coordinates[0],
        coordinate_id="coordinate.disclosed.unassigned-e2")), key=lambda co: co.coordinate_id))
    policy = scheduled.identity(design.e2.prefix_policies[0])
    changed = replace(design, e2=replace(design.e2, coordinates=coordinates,
        coordinate_policies=tuple((scheduled.coordinate_identity(co), policy) for co in coordinates)))
    with pytest.raises(ValueError, match="explicit allocation rule"):
        plan(changed, census)


def test_source_plan_is_pure_deterministic_and_keeps_original_e6_roles(scientific_design, census):  # noqa: F811
    first = plan(scientific_design, census)
    second = plan(scientific_design, census)
    assert first == second
    e1, populations, groups, _, _ = first
    assert all(root.root.role is MatrixProgrammeRole.CONFIRMATION for root in e1.roots)
    future, = (value for value in populations if value.name == "future")
    transfer_groups = {*groups["e6.nearby"], *groups["e6.shifted"]}
    assert {row.root.independent_group_id for row in future.roots
        if row.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER} == transfer_groups


def test_current_stream_recipe_binds_explicit_family_material_and_four_purposes():
    record = SelectedE4StreamRecipe("streams.disclosed-e4", "a" * 64, "b" * 64, STREAM_RULE)
    document = {"schema": "empirical-lawhood/matrix-selected-e4/stream-recipe", "version": "2.0.0",
        "value": {"record_id": "streams.disclosed-e4", "prefix_seed_material_sha256": "a" * 64,
            "future_seed_material_sha256": "b" * 64, "derivation_rule_id": STREAM_RULE,
            "family_seed_material_sha256": None}}
    assert record.canonical_bytes() == canonical_json_bytes(document)
    assert decode_canonical_record(document, SelectedE4StreamRecipe) == record
    with pytest.raises(ValueError):
        decode_canonical_record(dict(document, version='1.0.0'), SelectedE4StreamRecipe)
    first, future = record.streams("group.disclosed", future=False), record.streams("group.disclosed", future=True)
    assert tuple(stream.purpose for stream in first) == tuple(stream.purpose for stream in future) == HISTORY_PURPOSES
    assert len({stream.effective_seed for stream in (*first, *future)}) == 8


def test_large_declared_population_refuses_before_proportional_construction(scientific_design, census, monkeypatch):  # noqa: F811
    from empirical_lawhood.kernel.authority import ResourceBudget

    design = replace(scientific_design, e2=replace(scientific_design.e2, expected_units=10**9))
    calls = []
    ordinary_streams = compiler._ordinary_streams

    def sample(material, group):
        calls.append(group)
        return ordinary_streams(material, group)

    monkeypatch.setattr(compiler, "_ordinary_streams", sample)
    monkeypatch.setattr(compiler, "_process_rss_bytes", lambda: 1024**2)
    with pytest.raises(ValueError, match="cardinalities.*memory ceiling"):
        compiler._admit_source_plan(design=design, census=census, namespace=NAMESPACE, material=MATERIALS[0],
            budget=ResourceBudget(1, 64 * 1024**2, 0, 60, 1024**2, 1024**3), source_bytes=1024)
    assert len(calls) == 1


def test_serialized_root_lower_bound_refuses_before_publication(scientific_design, census, monkeypatch):  # noqa: F811
    from empirical_lawhood.kernel.authority import ResourceBudget

    monkeypatch.setattr(compiler, "_process_rss_bytes", lambda: 0)
    with pytest.raises(ValueError, match="output-byte lower bound"):
        compiler._admit_source_plan(design=scientific_design, census=census, namespace=NAMESPACE, material=MATERIALS[0],
            budget=ResourceBudget(1, 2 * 1024**3, 0, 60, 1024**2, 1), source_bytes=1024)


def test_unavailable_current_rss_refuses_without_a_capacity_claim(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise OSError("disclosed unavailable Linux observation")

    monkeypatch.setattr(Path, "open", unavailable)
    with pytest.raises(ValueError, match="Linux current-RSS observation"):
        compiler._process_rss_bytes()


def _publisher_case(tmp_path, design, census):
    """Actual current metadata and disclosed zero coefficient FILEs, no native."""
    import numpy as np
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    from tests.runtime_platform.test_native_subwork import _plane

    # This allocation precedes D because its existing criterion pins the exact
    # population. It depends on the declared coordinates/counts/census/material,
    # not on D's identity; the compiler must reproduce the same original.
    e1, *_ = plan(design, census)
    design = replace(design, e1_criterion=replace(design.e1_criterion, allocation=scheduled.identity(e1)))
    writer = _plane(tmp_path / "custody", binary_codecs=operation_storage_codecs())
    raw, _ = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"),
        "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"), "trace_coefficients": np.zeros((2, 3), dtype="<f8"),
        "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    templates = {design.training_assay.array_artifact: raw, design.e2.assay.array_artifact: raw}
    scalars = {design.e1_factor_rule.scalar_closure.normalization_owner: design.e1_scalar_definition.canonical_bytes(),
        design.training_protocol.scalar_artifact: design.training_protocol.scalar_definition.canonical_bytes()}
    for policy in design.e2.prefix_policies:
        scalars[policy.factor_rule.scalar_closure.normalization_owner] = design.e2.scalar_definition.canonical_bytes()
    support = []
    for index, (artifact, payload) in enumerate(sorted({**templates, **scalars}.items(), key=lambda row: row[0].artifact_id)):
        assert (len(payload), sha256(payload).hexdigest()) == (artifact.size_bytes, artifact.sha256)
        profile = ArtifactProfile.MATRIX_ARRAY_NPZ if artifact in templates else ArtifactProfile.CANONICAL_JSON
        publication = writer.write(ArtifactWriteRequest(artifact.artifact_id,
            "support/" + str(index) + (".npz" if artifact in templates else ".json"), artifact.payload_schema,
            profile, artifact.media_type, "programme.disclosed.support", "support", payload,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        support.append((artifact, publication))
    copied = Path(writer.root.contract.canonical_path) / "copied"
    copied.mkdir()
    normalization = design.training_protocol.full_factor_rule.scalar_closure.normalization_owner
    original = ROOT / "src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py"
    payload = original.read_bytes()
    assert (len(payload), sha256(payload).hexdigest()) == (normalization.size_bytes, normalization.sha256)
    (copied / "normalization.py").write_bytes(payload)
    request_path = copied / "request.json"
    request_path.write_text('{"disclosed_software_metadata":true}')
    implementation = implementation_binding(ROOT)
    execution = ExecutionSelection(4, "environment.disclosed.programme-inputs",
        ObjectIdentity.from_record("recursive-member.implementation", implementation), writer.root.contract.canonical_path)
    kwargs = dict(design=design, census=census, namespace=NAMESPACE, root_seed_material_sha256=MATERIALS[0],
        future_seed_material_sha256=MATERIALS[1],
        e4_streams=SelectedE4StreamRecipe("streams.disclosed.programme.e4", MATERIALS[2], MATERIALS[3], STREAM_RULE),
        e5_root_seed_material_sha256=MATERIALS[4], e5_future_seed_material_sha256=MATERIALS[5],
        provenance=capture_matrix_provenance(project_root=ROOT), support_publications=tuple(support),
        file_bindings=(ExperimentFileInputBinding(normalization.artifact_id, normalization, "1.0.0",
            "normalization.py", normalization.size_bytes),), request_path=request_path, project_root=ROOT,
        artifact_writer=writer, metadata_directory=Path(writer.root.contract.canonical_path) / "programme-inputs",
        execution=execution, metadata_budget=ResourceBudget(1, compiler._process_rss_bytes() + 512 * 1024**2,
            0, 60, 256 * 1024**2, 512 * 1024**2))
    return writer, kwargs


def _inventory(root):
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()}


def _forbid_acquisition(monkeypatch):
    import numpy as np

    def forbidden(*_args, **_kwargs):
        pytest.fail("pre-TRAIN metadata compiler entered native acquisition, fitting or random generation")

    monkeypatch.setattr(np.random, "default_rng", forbidden)
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    monkeypatch.setattr("empirical_lawhood.adapters.simulators.six_matrix_response.simulation.baoab_step_with_hermitian_noise", forbidden)


def test_current_publications_commit_all_known_inputs_before_train_and_reopen_exactly(
        scientific_design, census, tmp_path, monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs
    from empirical_lawhood.planning.approval import SystemDecisionClock

    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    _forbid_acquisition(monkeypatch)
    published = compiler.publish_matrix_programme_allocations(**kwargs)
    assert tuple(value.role for value in published.resolved.phases) == PHASE_INPUT_ROLES
    assert published.resolved.commitments.namespace == NAMESPACE
    assert len(published.resolved.commitments.canonical_bytes()) < 128 * 1024
    normalization = scientific_design.training_protocol.full_factor_rule.scalar_closure.normalization_owner
    source, publication = next(row for row in published.resolved.commitments.support_files if row[0] == normalization)
    assert source.media_type == publication.logical.media_type == "text/x-python"
    assert source.sha256 == publication.logical.content_sha256 == sha256(
        (ROOT / "src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py").read_bytes()).hexdigest()
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    assert publication.logical.generic_validation == integration_artifact_profile_validators().generic_validation(
        profile=publication.logical.profile, payload_schema=source.payload_schema)
    resolved = authenticate_programme_inputs(writer=writer, commitment=published.commitment,
        maximum_source_bytes=kwargs["metadata_budget"].source_scan_bytes)
    assert resolved == published.resolved
    before = _inventory(Path(writer.root.contract.canonical_path))
    monkeypatch.setattr(SystemDecisionClock, "now_utc", lambda _self: pytest.fail("retry invented another original availability"))
    assert compiler.publish_matrix_programme_allocations(**kwargs) == published
    assert _inventory(Path(writer.root.contract.canonical_path)) == before
    assert not tuple(Path(writer.root.contract.canonical_path).rglob("receipts"))


def test_missing_original_source_codec_refuses_before_any_programme_publication(
        scientific_design, census, tmp_path, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import (
        MATRIX_PYTHON_SOURCE_CODEC, MATRIX_STORAGE_CODECS,
    )
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry

    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    codecs = tuple(codec for codec in MATRIX_STORAGE_CODECS
        if codec.codec_id != MATRIX_PYTHON_SOURCE_CODEC.codec_id)
    assert len(codecs) == len(MATRIX_STORAGE_CODECS) - 1
    kwargs["artifact_writer"] = ExternalArtifactPlane(writer.root,
        validators=ArtifactProfileValidatorRegistry(binary_codecs=codecs))
    before = _inventory(Path(writer.root.contract.canonical_path))
    _forbid_acquisition(monkeypatch)
    with pytest.raises(ArtifactIdentityConflict, match="raw source custody exceeds its uninterpreted contract"):
        compiler.publish_matrix_programme_allocations(**kwargs)
    assert _inventory(Path(writer.root.contract.canonical_path)) == before


def test_interrupted_final_commitment_retains_all_children_and_original_availability(
        scientific_design, census, tmp_path, monkeypatch):  # noqa: F811
    from empirical_lawhood.planning.approval import SystemDecisionClock

    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    _forbid_acquisition(monkeypatch)
    original = type(writer).write

    def interrupted(plane, request):
        if request.relative_path.endswith("/commitments.json"):
            raise OSError("disclosed final metadata publication interruption")
        return original(plane, request)

    with monkeypatch.context() as interrupted_scope:
        interrupted_scope.setattr(type(writer), "write", interrupted)
        with pytest.raises(OSError, match="metadata publication interruption"):
            compiler.publish_matrix_programme_allocations(**kwargs)
    directory = kwargs["metadata_directory"]
    assert not (directory / "publications/commitments.json").exists()
    before = _inventory(Path(writer.root.contract.canonical_path))
    monkeypatch.setattr(SystemDecisionClock, "now_utc", lambda _self: pytest.fail("retry replaced already published availability"))
    published = compiler.publish_matrix_programme_allocations(**kwargs)
    after = _inventory(Path(writer.root.contract.canonical_path))
    assert all(after[path] == digest for path, digest in before.items())
    assert (directory / "publications/commitments.json").read_bytes() == published.resolved.commitments.canonical_bytes()


def _crash_availability_publication(writer, kwargs, monkeypatch, *, after):
    """Hard-exit the real writer after a component rename, without rollback."""
    import multiprocessing
    import os
    import traceback
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.artifacts import ArtifactPublicationIntent, artifact_publication_intent_relative_path

    captured = []
    original = type(writer).write

    def retain_request(plane, request):
        if request.relative_path.endswith("/pretrain-availability.json"):
            captured.append(request)
            raise OSError("disclosed handoff to interrupted Availability publisher")
        return original(plane, request)

    with monkeypatch.context() as capture:
        capture.setattr(type(writer), "write", retain_request)
        with pytest.raises(OSError, match="handoff to interrupted Availability publisher"):
            compiler.publish_matrix_programme_allocations(**kwargs)
    request, = captured
    payload = writer.root.resolve(request.relative_path, for_write=False)
    sidecar = writer.root.resolve(request.relative_path + ".manifest.json", for_write=False)
    assert not payload.exists() and not sidecar.exists()
    boundary = payload if after == "payload" else sidecar
    log = kwargs["metadata_directory"] / ("availability-crash-" + after + ".log")

    def interrupted():
        move = ExternalArtifactPlane._move_file_once

        def publish_then_exit(source, destination):
            move(source, destination)
            if destination == boundary:
                os._exit(77)

        ExternalArtifactPlane._move_file_once = staticmethod(publish_then_exit)
        try:
            writer.write(request)
        except BaseException:
            log.write_text(traceback.format_exc())
        os._exit(78)

    process = multiprocessing.get_context("fork").Process(target=interrupted)
    process.start()
    process.join(60)
    if process.is_alive():
        process.kill()
        process.join(10)
    exitcode = process.exitcode
    process.close()
    assert exitcode == 77, log.read_text() if log.exists() else f"interrupted publisher exited {exitcode}"
    assert payload.read_bytes() == request.payload
    assert sidecar.exists() is (after == "sidecar")
    publication = writer._preflight_publication((request,)).publication
    intent = writer.root.resolve(artifact_publication_intent_relative_path(
        publication.publication_scope, publication.publication_batch_id), for_write=False)
    marker = writer.root.resolve(publication.commit_marker_relative_path, for_write=False)
    assert intent.is_file()
    raw = intent.read_bytes()
    retained_intent = decode_canonical_bytes(raw, ArtifactPublicationIntent, maximum_bytes=len(raw))
    assert (retained_intent.publication_batch_id, retained_intent.publication_scope, retained_intent.members) == (
        publication.publication_batch_id, publication.publication_scope, publication.members)
    assert not marker.exists()
    assert not (kwargs["metadata_directory"] / "publications/commitments.json").exists()
    return request, payload, sidecar, intent, marker


@pytest.mark.parametrize("after", ("payload", "sidecar"))
def test_availability_retry_completes_only_its_exact_durable_publication_intent(
        scientific_design, census, tmp_path, monkeypatch, after):  # noqa: F811
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.time import AvailabilitySpec
    from empirical_lawhood.planning.approval import SystemDecisionClock

    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    _forbid_acquisition(monkeypatch)
    request, payload, sidecar, intent, marker = _crash_availability_publication(
        writer, kwargs, monkeypatch, after=after)
    original = decode_canonical_bytes(request.payload, AvailabilitySpec, maximum_bytes=len(request.payload))
    retained = {path: path.read_bytes() for path in kwargs["metadata_directory"].joinpath("publications").iterdir()
        if path.is_file()}
    monkeypatch.setattr(SystemDecisionClock, "now_utc", lambda _self: pytest.fail("retry resampled retained Availability UTC"))
    published = compiler.publish_matrix_programme_allocations(**kwargs)
    assert published.resolved.availability == original
    assert published.resolved.commitments.availability.record.object_fingerprint == sha256(request.payload).hexdigest()
    assert payload.read_bytes() == request.payload
    assert all(path.read_bytes() == raw for path, raw in retained.items())
    assert sidecar.is_file() and marker.is_file() and not intent.exists()
    manifest = writer.read_manifest(request.relative_path)
    writer.verify_manifest(manifest)
    assert manifest.logical.content_sha256 == sha256(request.payload).hexdigest()
    before = _inventory(Path(writer.root.contract.canonical_path))
    assert compiler.publish_matrix_programme_allocations(**kwargs) == published
    assert _inventory(Path(writer.root.contract.canonical_path)) == before


@pytest.mark.parametrize("damage", ("unowned", "changed-payload", "changed-sidecar",
    "missing-committed-sidecar", "missing-committed-payload"))
def test_availability_retry_refuses_unowned_substituted_or_broken_committed_custody(
        scientific_design, census, tmp_path, monkeypatch, damage):  # noqa: F811
    from decimal import Decimal
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.time import AvailabilitySpec
    from empirical_lawhood.planning.approval import SystemDecisionClock

    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    _forbid_acquisition(monkeypatch)
    request, payload, sidecar, intent, _ = _crash_availability_publication(
        writer, kwargs, monkeypatch, after="sidecar")
    if damage == "unowned":
        intent.unlink()
    elif damage == "changed-payload":
        original = decode_canonical_bytes(request.payload, AvailabilitySpec, maximum_bytes=len(request.payload))
        payload.write_bytes(replace(original, available_at=original.available_at + Decimal(1)).canonical_bytes())
    elif damage == "changed-sidecar":
        sidecar.write_bytes(b"x" * sidecar.stat().st_size)
    else:
        writer.write(request)
        assert not intent.exists()
        (sidecar if damage == "missing-committed-sidecar" else payload).unlink()
    before = _inventory(Path(writer.root.contract.canonical_path))
    monkeypatch.setattr(SystemDecisionClock, "now_utc", lambda _self: pytest.fail("refusal resampled retained Availability UTC"))
    with pytest.raises((ArtifactIdentityConflict, ValueError), match="intent|component|member|payload"):
        compiler.publish_matrix_programme_allocations(**kwargs)
    assert _inventory(Path(writer.root.contract.canonical_path)) == before
    assert not (kwargs["metadata_directory"] / "publications/commitments.json").exists()


@pytest.mark.parametrize("damage", ("seed-material", "source", "template", "scan-budget", "e1-criterion"))
def test_invalid_known_input_prerequisite_refuses_before_any_compiler_publication(
        scientific_design, census, tmp_path, monkeypatch, damage):  # noqa: F811
    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    if damage == "seed-material":
        kwargs["e5_root_seed_material_sha256"] = kwargs["root_seed_material_sha256"]
    elif damage == "source":
        kwargs["provenance"] = replace(kwargs["provenance"], observed_git_head="a" * 40)
    elif damage == "template":
        artifact, publication = next((artifact, publication) for artifact, publication in kwargs["support_publications"]
            if artifact == scientific_design.training_assay.array_artifact)
        changed = replace(artifact, artifact_id=artifact.artifact_id + ".foreign")
        kwargs["support_publications"] = tuple((changed if value == artifact else value, result)
            for value, result in kwargs["support_publications"])
    elif damage == "scan-budget":
        kwargs["metadata_budget"] = replace(kwargs["metadata_budget"], source_scan_bytes=1)
    else:
        kwargs["design"] = replace(kwargs["design"], e1_criterion=scientific_design.e1_criterion)
    before = _inventory(Path(writer.root.contract.canonical_path))
    _forbid_acquisition(monkeypatch)
    with pytest.raises((ValueError, PermissionError)):
        compiler.publish_matrix_programme_allocations(**kwargs)
    assert _inventory(Path(writer.root.contract.canonical_path)) == before


def test_incomplete_matched_scope_refuses_before_any_compiler_publication(
        scientific_design, census, tmp_path, monkeypatch):  # noqa: F811
    writer, kwargs = _publisher_case(tmp_path, scientific_design, census)
    original = compiler._source_plan

    def incomplete(**selected):
        e1, populations, groups, futures, folds = original(**selected)
        changed = tuple(replace(value, scopes=value.scopes[:-1]) if value.name == "e4" else value
            for value in populations)
        return e1, changed, groups, futures, folds

    before = _inventory(Path(writer.root.contract.canonical_path))
    monkeypatch.setattr(compiler, "_source_plan", incomplete)
    _forbid_acquisition(monkeypatch)
    with pytest.raises(ValueError, match="whole-group matched scopes"):
        compiler.publish_matrix_programme_allocations(**kwargs)
    assert _inventory(Path(writer.root.contract.canonical_path)) == before
