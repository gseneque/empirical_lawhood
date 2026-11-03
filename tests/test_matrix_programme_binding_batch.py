# SPDX-License-Identifier: MPL-2.0
"""Actual publication binding costs and refusals; no native or scientific grant."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    MatrixProgrammePhaseBinding, MatrixResearchProgrammePlan,
)
from empirical_lawhood.api import matrix_researcher_programme as owner
from empirical_lawhood.api import matrix_researcher_programme_lineage as lineage
from empirical_lawhood.api.experiment_preparation import (
    _protocol, load_experiment_specification, prepare_experiment,
)
from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputSelection, ExperimentInputBinding,
)
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactWriteRequest, ExternalRootContract,
)
from empirical_lawhood.runtime.experiment_preparation import (
    ExecutionSelection, ExperimentInputDerivationResult,
)


ROOT = Path(__file__).parents[1]


def _case(directory, count=4, shape="singletons"):
    directory.mkdir(parents=True)
    mount = next(parent for parent in directory.parents if parent.is_mount())
    plane = artifacts.ExternalArtifactPlane(artifacts.GuardedExternalRoot(ExternalRootContract(
        "exposed.programme-binding", "Literal software custody only", str(directory), str(mount),
        "empirical-lawhood/testing/programme-binding", 1)))
    target = load_experiment_specification(
        ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-assembly.example.json")
    preparation = prepare_experiment(target, execution=ExecutionSelection(4))
    assert not preparation.executable  # Missing originals never create native authority.
    protocol = _protocol(target).protocol_id
    selector = ExperimentFileInputSelection("selection.exposed-binding", protocol, (), ())
    requirements_schema = "empirical-lawhood/operational/experiment-input-requirements"
    rows = [
        ("specification", target.SCHEMA, target.canonical_bytes()),
        ("sources", selector.SCHEMA, selector.canonical_bytes()),
        ("requirements", requirements_schema, canonical_json_bytes({
            "schema": requirements_schema, "version": "1.0.0", "value": {
                "specification": target.identity, "scientific_authority": "NONE"}})),
    ]
    rows.extend(("operand-" + str(index), ObjectIdentity.SCHEMA,
        ObjectIdentity("exposed.operand." + str(index), ObjectIdentity.SCHEMA,
            "1.0.0", "a" * 64).canonical_bytes()) for index in range(count - 3))

    def request(name, schema, raw):
        return ArtifactWriteRequest("exposed.binding." + name, "inputs/" + name + ".json",
            schema, ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.binding", "inputs",
            raw, VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)

    requests = tuple(request(*row) for row in rows)
    if shape == "singletons":
        publications = tuple(plane.write(row) for row in requests)
    elif shape == "mixed":
        publications = (*plane.write_batch(requests[:count // 2], compact_manifests=True),
            *(plane.write(row) for row in requests[count // 2:]))
    else:
        publications = plane.write_batch(requests, compact_manifests=shape == "shared")
    result = ExperimentInputDerivationResult(target.identity, selector, directory / "inputs/sources.json",
        preparation, publications, publications[2], target, directory / "inputs/specification.json")
    plan_pin = ObjectIdentity("plan.exposed-binding", MatrixResearchProgrammePlan.SCHEMA,
        MatrixResearchProgrammePlan.VERSION, "b" * 64)
    context = SimpleNamespace(plan=SimpleNamespace(identity=plan_pin, fingerprint=lambda: plan_pin.object_fingerprint),
        directory=directory / "programme", bindings={}, pending_bindings={"e1": "not retained"})
    expected_publications = tuple(replace(row, created=False) for row in publications)
    expected = MatrixProgrammePhaseBinding("binding." + plan_pin.object_fingerprint + ".e1",
        plan_pin, "e1", protocol,
        ExperimentInputBinding("specification", target.identity, "inputs/specification.json", len(target.canonical_bytes())),
        ExperimentInputBinding("sources", ObjectIdentity.from_record(selector.selection_id, selector),
            "inputs/sources.json", len(selector.canonical_bytes())), expected_publications[2], expected_publications)
    prior = plane.write(ArtifactWriteRequest("exposed.prior", "prior/input.json", ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.prior", "prior",
        ObjectIdentity("exposed.prior", ObjectIdentity.SCHEMA, "1.0.0", "c" * 64).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    return SimpleNamespace(plane=plane, result=result, context=context, expected=expected, prior=prior)


def _bind(case, writer=None):
    service = owner.MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=writer or case.plane))
    return service._retain_binding(case.context, "e1", case.result)


def _measured_binding(case):
    counts = Counter()
    snapshot = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    physical = artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__

    def observe(frame, event, _arg):
        if event != "call":
            return
        if frame.f_code is snapshot:
            paths = frame.f_locals["snapshots"]
            counts["nonempty_union_scans"] += bool(paths)
            counts["paths_scanned"] += len(paths)
            counts["bytes_scanned"] += sum(row[2] for row in paths.values())
        elif frame.f_code is physical:
            counts["physical_member_validations"] += 1

    with case.plane.verification_scope() as writer:
        writer.verify_manifest(writer.read_manifest(case.prior.materialization.relative_path))
        assert writer._read_verification.snapshots
        assert sys.getprofile() is None
        sys.setprofile(observe)
        try:
            result = _bind(case, writer)
        finally:
            sys.setprofile(None)
    assert result.canonical_bytes() == case.expected.canonical_bytes()
    retained = (case.context.directory / "bindings/e1.json").read_bytes()
    assert retained == result.canonical_bytes()
    assert decode_canonical_bytes(retained, MatrixProgrammePhaseBinding, maximum_bytes=len(retained)) == result
    assert case.context.bindings == {"e1": result} and case.context.pending_bindings == {}
    return dict(counts)


@pytest.mark.parametrize("shape", ("singletons", "shared", "shared-legacy", "mixed"))
def test_complete_binding_has_bounded_collection_scans_and_exact_bytes(tmp_path, shape):
    observations = []
    for count in (4, 32):
        case = _case(tmp_path / str(count), count, shape)
        observed = _measured_binding(case)
        observations.append({"publications": count, **observed})
    (tmp_path / "binding-verification-counts.json").write_text(json.dumps(observations, indent=2) + "\n")
    for observed, count in zip(observations, (4, 32), strict=True):
        # Include an already-observed input: an empty initial scan hides the old multiplier.
        assert observed["nonempty_union_scans"] <= 5
        assert observed["physical_member_validations"] == count
    small, large = observations
    assert large["nonempty_union_scans"] == small["nonempty_union_scans"]
    assert large["paths_scanned"] <= 8 * small["paths_scanned"]
    # Legacy sidecars physically repeat the roster; count work against actual bytes.


@pytest.mark.parametrize("damage", ("body", "sidecar", "marker", "ancestor", "prior"))
def test_final_guard_refuses_mutation_before_any_binding_publication(tmp_path, damage):
    case = _case(tmp_path / "actual", shape="shared")
    manifest = case.plane.read_manifest(case.result.publications[0].materialization.relative_path)
    constructed = MatrixProgrammePhaseBinding.__post_init__.__code__
    changed = []

    def mutate(frame, event, _arg):
        if event != "return" or frame.f_code is not constructed or changed:
            return
        changed.append(True)
        if damage == "ancestor":
            folder = Path(case.plane.root.contract.canonical_path) / "inputs"
            moved = folder.with_name("inputs-original")
            folder.rename(moved)
            folder.symlink_to(moved, target_is_directory=True)
        else:
            relative = (manifest.materialization.relative_path if damage == "body"
                else manifest.materialization.relative_path + ".manifest.json" if damage == "sidecar"
                else manifest.publication.commit_marker_relative_path if damage == "marker"
                else case.prior.materialization.relative_path)
            path = case.plane.root.resolve(relative, for_write=False)
            path.write_bytes(path.read_bytes() + b" ")

    # Mutate at the last reconstruction boundary. A guard only at outer-scope
    # exit would reject too late, after the immutable binding had been written.
    with pytest.raises((artifacts.ArtifactIdentityConflict, artifacts.ExternalRootUnavailable)):
        with case.plane.verification_scope() as writer:
            writer.verify_manifest(writer.read_manifest(case.prior.materialization.relative_path))
            assert sys.getprofile() is None
            sys.setprofile(mutate)
            try:
                _bind(case, writer)
            finally:
                sys.setprofile(None)
    assert changed == [True]
    assert not (case.context.directory / "bindings/e1.json").exists()
    assert case.context.bindings == {} and case.context.pending_bindings


def test_current_member_access_denial_precedes_binding_publication(tmp_path):
    case = _case(tmp_path / "actual", shape="shared")
    seen = []

    def deny(manifest):
        seen.append(manifest.materialization.relative_path)
        raise PermissionError("exposed current access withdrawn")

    with pytest.raises(PermissionError, match="current access withdrawn"):
        with case.plane.verification_scope(before_member=deny) as writer:
            _bind(case, writer)
    assert seen
    assert not (case.context.directory / "bindings/e1.json").exists()


@pytest.mark.parametrize("withdraw", (False, True))
def test_current_member_access_is_refreshed_after_reconstruction(tmp_path, withdraw):
    case = _case(tmp_path / "actual", shape="shared")
    constructed = MatrixProgrammePhaseBinding.__post_init__.__code__
    finished, seen = [], []

    def current(manifest):
        seen.append(manifest.materialization.relative_path)
        assert not manifest.materialization.relative_path.endswith(".manifest.json")
        if finished and withdraw:
            raise PermissionError("exposed access expired during reconstruction")

    def observe(frame, event, _arg):
        if event == "return" and frame.f_code is constructed:
            finished.append(True)

    def operation():
        with case.plane.verification_scope(before_member=current) as writer:
            assert sys.getprofile() is None
            sys.setprofile(observe)
            try:
                return _bind(case, writer)
            finally:
                sys.setprofile(None)

    if withdraw:
        with pytest.raises(PermissionError, match="expired during reconstruction"):
            operation()
        assert not (case.context.directory / "bindings/e1.json").exists()
    else:
        assert operation() == case.expected
        assert set(seen) == {row.materialization.relative_path for row in case.result.publications}
    assert seen and finished


def test_protected_phase_keeps_its_current_original_reader_boundary(tmp_path):
    case = _case(tmp_path / "actual")
    seen = []

    @contextmanager
    def originals():
        seen.append("entered")
        raise PermissionError("exposed original reveal withdrawn")
        yield  # pragma: no cover

    case.context.e3_originals = originals
    service = owner.MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=case.plane))
    with pytest.raises(PermissionError, match="original reveal withdrawn"):
        service._retain_binding(case.context, "e4.source-cal", case.result)
    assert seen == ["entered"] and not case.context.directory.exists()


def _read_binding(case, writer):
    return lineage.authenticate_phase_binding(
        SimpleNamespace(plan=case.context.plan, writer=writer), case.expected)


def _measured_binding_read(case, writer):
    counts = Counter()
    snapshot = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    physical = artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__

    def observe(frame, event, _arg):
        if event != "call":
            return
        if frame.f_code is snapshot:
            paths = frame.f_locals["snapshots"]
            counts["nonempty_union_scans"] += bool(paths)
            counts["paths_scanned"] += len(paths)
            counts["bytes_scanned"] += sum(row[2] for row in paths.values())
        elif frame.f_code is physical:
            counts["physical_member_validations"] += 1

    assert sys.getprofile() is None
    sys.setprofile(observe)
    try:
        path, specification = _read_binding(case, writer)
    finally:
        sys.setprofile(None)
    assert path == case.result.target_specification_path
    assert specification.canonical_bytes() == case.result.target_specification.canonical_bytes()
    assert specification.identity == case.expected.specification.identity
    assert not case.context.directory.exists()  # A cold read publishes nothing.
    return dict(counts)


@pytest.mark.parametrize("shape", ("singletons", "shared", "shared-legacy", "mixed"))
@pytest.mark.parametrize("scoped", (False, True))
def test_cold_phase_read_has_bounded_collection_and_member_validation(tmp_path, shape, scoped):
    observations = []
    for count in (4, 32):
        case = _case(tmp_path / str(count), count, shape)
        if scoped:
            with case.plane.verification_scope() as writer:
                writer.verify_manifest(writer.read_manifest(case.prior.materialization.relative_path))
                observed = _measured_binding_read(case, writer)
        else:
            observed = _measured_binding_read(case, case.plane)
        observations.append({"publications": count, **observed})
    (tmp_path / "phase-read-verification-counts.json").write_text(json.dumps(observations, indent=2) + "\n")
    for observed, count in zip(observations, (4, 32), strict=True):
        # A singular check revalidates every sibling of a shared publication.
        # A live eager scope instead multiplies whole-collection rehashes.
        assert observed["physical_member_validations"] == count
        assert observed["nonempty_union_scans"] <= 5
    small, large = observations
    assert large["nonempty_union_scans"] == small["nonempty_union_scans"]
    assert large["paths_scanned"] <= 8 * small["paths_scanned"]


@pytest.mark.parametrize("damage", ("body", "sidecar", "marker", "ancestor", "prior"))
def test_cold_phase_final_guard_refuses_mutation_after_selector_decode(tmp_path, damage):
    case = _case(tmp_path / "actual", shape="shared")
    manifest = case.plane.read_manifest(case.result.publications[0].materialization.relative_path)
    changed, returned = [], []

    def mutate(frame, event, value):
        if (event != "return" or frame.f_code is not decode_canonical_bytes.__code__
                or type(value) is not ExperimentFileInputSelection or changed):
            return
        changed.append(True)
        if damage == "ancestor":
            folder = Path(case.plane.root.contract.canonical_path) / "inputs"
            moved = folder.with_name("inputs-original")
            folder.rename(moved)
            folder.symlink_to(moved, target_is_directory=True)
        else:
            relative = (manifest.materialization.relative_path if damage == "body"
                else manifest.materialization.relative_path + ".manifest.json" if damage == "sidecar"
                else manifest.publication.commit_marker_relative_path if damage == "marker"
                else case.prior.materialization.relative_path)
            path = case.plane.root.resolve(relative, for_write=False)
            path.write_bytes(path.read_bytes() + b" ")

    with pytest.raises((artifacts.ArtifactIdentityConflict, artifacts.ExternalRootUnavailable)):
        with case.plane.verification_scope() as writer:
            writer.verify_manifest(writer.read_manifest(case.prior.materialization.relative_path))
            assert sys.getprofile() is None
            sys.setprofile(mutate)
            try:
                returned.append(_read_binding(case, writer))
            finally:
                sys.setprofile(None)
    assert changed == [True] and returned == []


@pytest.mark.parametrize("when", ("before", "after-decode"))
def test_cold_phase_read_rechecks_current_access_before_return(tmp_path, when):
    case = _case(tmp_path / "actual", shape="shared")
    decoded, seen, returned = [], [], []

    def current(manifest):
        seen.append(manifest.materialization.relative_path)
        if when == "before" or decoded:
            raise PermissionError("exposed current access withdrawn")

    def observe(frame, event, value):
        if (event == "return" and frame.f_code is decode_canonical_bytes.__code__
                and type(value) is ExperimentFileInputSelection):
            decoded.append(True)

    with pytest.raises(PermissionError, match="current access withdrawn"):
        with case.plane.verification_scope(before_member=current) as writer:
            assert sys.getprofile() is None
            sys.setprofile(observe)
            try:
                returned.append(_read_binding(case, writer))
            finally:
                sys.setprofile(None)
    assert seen and returned == []
    assert bool(decoded) == (when == "after-decode")


@pytest.mark.parametrize("field", ("programme", "specification", "sources", "protocol_id"))
def test_cold_phase_read_preserves_exact_original_record_joins(tmp_path, field):
    case = _case(tmp_path / "actual", shape="shared")
    original = getattr(case.expected, field)
    changed = ("another.exposed.protocol" if field == "protocol_id"
        else replace(original, object_fingerprint="f" * 64) if field == "programme"
        else replace(original, identity=replace(original.identity, object_fingerprint="f" * 64)))
    case.expected = replace(case.expected, **{field: changed})
    with pytest.raises(PermissionError, match="Matrix phase"):
        _read_binding(case, case.plane)
