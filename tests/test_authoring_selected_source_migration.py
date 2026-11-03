# SPDX-License-Identifier: MPL-2.0
"""Actual selected-source/companion owners; no native entry or scientific authority.

These controls run only against committed installed checkout source. They never
mock source capture or its Git/archive/member verification on positive paths.
"""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import importlib
import json
import os
import subprocess

import pytest

from empirical_lawhood.api import authoring_handoff as shared
from empirical_lawhood.api.recursive_prospective_authoring import _capture_prospective_source, _publish_source_provenance
from empirical_lawhood.infrastructure import source_closure
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactPlaneError
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.operator_profile import (
    OperatorStorageAccessMode, OperatorStorageProfile, resolve_external_root_contract,
)

ROOT = Path(__file__).resolve().parents[1]
NOTES = {"CONSOLIDATION.md", "MATRIXAUDIT.md", "THEMATRIX-AUDIT-EXPDESIGN.md"}
FAMILIES = ("rc_authoring", "synthetic_material_authoring", "uniform_electron_gas_authoring",
    "rc_challenge_authoring", "finite_rerun_authoring", "preparation_applicability", "constructed_preparation_applicability")


def plane(tmp_path):
    mount = next(parent for parent in (tmp_path, *tmp_path.parents) if os.path.ismount(parent))
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "software.selected-source-controls", "explicit exposed source-control storage", str(tmp_path), str(mount),
        OperatorStorageProfile.SCHEMA, 1, None, None, ())))


def current_packet(tmp_path):
    writer = plane(tmp_path)
    directory = tmp_path / "source-packet"
    directory.mkdir()
    captured = _capture_prospective_source(ROOT, "software.actual-selected-source")
    shared.write_exclusive_record(directory, "source-closure.json", captured.closure)
    _publish_source_provenance(captured=captured, destination=directory, artifact_writer=writer)
    return writer, directory, captured


def assert_actual_source_disclosure(captured):
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT)
    assert captured.closure.kind is SourceClosureKind.EXACT_SOURCE_CLOSURE
    assert captured.closure.clean_worktree is (not bool(status))
    assert captured.source.source_admission.raw_status == status
    assert captured.source.final_source_admission.raw_status == status
    disclosure = captured.source.to_mapping()
    assert disclosure["source_admission"]["observed_checkout_clean"] is (not bool(status))
    assert disclosure["final_source_admission"]["observed_checkout_clean"] is (not bool(status))
    # Local notes are genuine operational disclosure when present; source
    # exports intentionally omit them and must exercise the same source owner.
    actual_notes = {row[3:].decode() for row in status.split(b"\0")
        if row.startswith(b"?? ") and row[3:].decode() in NOTES}
    disclosed_notes = {row["relative_path"] for row in disclosure["final_source_admission"]["changes"]
        if row["status"] == "??" and row["relative_path"] in NOTES}
    assert disclosed_notes == actual_notes
    return status


def test_actual_committed_source_publishes_and_replays_exact_actual_disclosure_and_companions(tmp_path):
    writer, directory, captured = current_packet(tmp_path)
    before = assert_actual_source_disclosure(captured)
    actual = shared.authenticate_authoring_source(directory=directory, project_root=ROOT, artifact_writer=writer)
    assert actual == captured.closure
    assert (directory / "source-closure.json").read_bytes() == captured.closure.canonical_bytes()
    assert set(p.name for p in (directory / "provenance").glob("*.json")) == {
        "selected-source-manifest.json", "selected-source-manifest.json.manifest.json",
        "source-observation.json", "source-observation.json.manifest.json"}
    observed = json.loads((directory / "provenance/source-observation.json").read_bytes())["value"]
    assert json.loads(observed["source_observation_json"]) == json.loads(json.dumps(captured.source.to_mapping()))
    assert subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT) == before


@pytest.mark.parametrize("member", ("selected-source-manifest.json", "source-observation.json"))
@pytest.mark.parametrize("damage", ("missing", "changed-byte", "changed-sidecar"))
def test_selected_source_missing_or_corrupt_real_companion_refuses_before_reobservation(tmp_path, monkeypatch, member, damage):
    writer, directory, captured = current_packet(tmp_path)
    target = directory / "provenance" / member
    if damage == "missing":
        target.unlink()
    elif damage == "changed-byte":
        raw = target.read_bytes()
        target.write_bytes(raw[:-1] + bytes((raw[-1] ^ 1,)))
    else:
        sidecar = target.with_name(target.name + ".manifest.json")
        raw = sidecar.read_bytes()
        sidecar.write_bytes(raw[:-1] + bytes((raw[-1] ^ 1,)))
    from empirical_lawhood.infrastructure import study_issue
    monkeypatch.setattr(study_issue.GitStudySourceClosureInspector, "observe",
        lambda *_: pytest.fail("corrupt companion reached current source reobservation"))
    with pytest.raises((OSError, ValueError, PermissionError, ArtifactPlaneError)):
        shared.authenticate_authoring_source(directory=directory, project_root=ROOT, artifact_writer=writer)
    assert (directory / "source-closure.json").read_bytes() == captured.closure.canonical_bytes()


class ScienceReached(Exception):
    pass


def entry(module, writer, output):
    """Only unacquired argument skeletons; scientific builder is trapped below."""
    config = SimpleNamespace(config_id="software.current-source", experiment_id="software.current-source")
    stage = SimpleNamespace(config_id="software.current-source")
    if module.__name__.endswith(".rc_authoring"):
        return module.author_fresh_rc(root=ROOT, study=None, experiment_id=config.config_id, output_dir=output, artifact_writer=writer)
    if module.__name__.endswith(".synthetic_material_authoring"):
        return module.author_synthetic_material_response(root=ROOT, config=None, experiment_id=config.config_id, output_dir=output, artifact_writer=writer)
    if module.__name__.endswith(".uniform_electron_gas_authoring"):
        return module.author_uniform_electron_gas_analytic_reference(root=ROOT, config=None, experiment_id=config.config_id, output_dir=output, artifact_writer=writer)
    if module.__name__.endswith(".rc_challenge_authoring"):
        return module.author_rc_challenge_phase(root=ROOT, config=config, external_records=(), output_dir=output, artifact_writer=writer)
    if module.__name__.endswith(".finite_rerun_authoring"):
        return module.author_finite_response_rerun(root=ROOT, packet=config, exposure=None,
            nomination_directory=output, output_dir=output, artifact_writer=writer)
    selection = SimpleNamespace(stage=stage, upstream_records=())
    if module.__name__.endswith(".constructed_preparation_applicability"):
        return module.author_constructed_preparation_applicability(root=ROOT, selection=selection, output_dir=output, artifact_writer=writer)
    return module.author_preparation_applicability(root=ROOT, selection=selection, output_dir=output, artifact_writer=writer)


def trap_science(monkeypatch, module):
    leaf = module.__name__.rsplit(".", 1)[-1]
    names = {"rc_authoring": "build_rc_authoring", "synthetic_material_authoring": "build_synthetic_material_response_method_authoring",
        "uniform_electron_gas_authoring": "build_uniform_electron_gas_analytic_authoring", "rc_challenge_authoring": "compose_simulator_morphism_challenges_phase",
        "finite_rerun_authoring": "current_nomination_operand_import", "preparation_applicability": "_bundle",
        "constructed_preparation_applicability": "_bundle"}
    def stopped(*_args, **_kwargs):
        raise ScienceReached
    monkeypatch.setattr(module, names[leaf], stopped)
    # RC's declared implementation files precede its composition; their exact
    # actual source reads remain enabled and enter no simulator.


@pytest.mark.parametrize("family", FAMILIES)
def test_each_current_author_entry_uses_actual_admitted_source_before_any_science(tmp_path, monkeypatch, family):
    module = importlib.import_module("empirical_lawhood.api." + family)
    writer = plane(tmp_path)
    output = tmp_path / "unentered"
    trap_science(monkeypatch, module)
    actual_capture = module._capture_prospective_source
    observed = []
    def observe_capture(*args, **kwargs):
        captured = actual_capture(*args, **kwargs)
        assert_actual_source_disclosure(captured)
        observed.append(captured)
        return captured
    # A delegating observation counts the real capture; no fabricated closure.
    monkeypatch.setattr(module, "_capture_prospective_source", observe_capture)
    with pytest.raises(ScienceReached):
        entry(module, writer, output)
    assert len(observed) == 1 and not output.exists()


@pytest.mark.parametrize("family", FAMILIES)
def test_undeclared_executable_census_refuses_each_author_before_science_or_output(tmp_path, monkeypatch, family):
    module = importlib.import_module("empirical_lawhood.api." + family)
    writer = plane(tmp_path)
    output = tmp_path / "refused"
    actual_census = source_closure._source_path_census
    # Inject one observation at the real census guard; never mutate the checkout.
    monkeypatch.setattr(source_closure, "_source_path_census", lambda root: actual_census(root) | {"src/empirical_lawhood/undeclared_software_control.py"})
    trap_science(monkeypatch, module)
    with pytest.raises(source_closure.SourcePolicyError, match="census"):
        entry(module, writer, output)
    assert not output.exists()


@pytest.mark.parametrize("family", ("rc_authoring", "synthetic_material_authoring", "uniform_electron_gas_authoring"))
def test_writerless_api_migration_requires_explicit_actual_guarded_plane(tmp_path, monkeypatch, family):
    module = importlib.import_module("empirical_lawhood.api." + family)
    monkeypatch.setattr(module, "_capture_prospective_source", lambda *_: pytest.fail("unsupported writer reached source"))
    with pytest.raises(TypeError, match="actual guarded external artifact plane"):
        entry(module, object(), tmp_path / "refused")


@pytest.mark.parametrize("kind", ("rc", "electron", "material"))
@pytest.mark.parametrize("damage", ("missing-companion", "clean-substitution"))
def test_actual_cli_composition_rejects_missing_or_downgraded_source_before_bundle(tmp_path, monkeypatch, kind, damage):
    from empirical_lawhood.api import composition
    writer, directory, captured = current_packet(tmp_path)
    if damage == "missing-companion":
        (directory / "provenance/source-observation.json").unlink()
    else:
        downgraded = replace(captured.closure, kind=SourceClosureKind.CLEAN_GIT_COMMIT, clean_worktree=True, exact_source_manifest=None)
        (directory / "source-closure.json").write_bytes(downgraded.canonical_bytes())
    monkeypatch.setattr(composition, "resolve_authoring_directory", lambda *_args, **_kwargs: (directory, writer.root.contract))
    loader = {"rc": "load_fresh_rc_bundle", "electron": "load_uniform_electron_gas_analytic_authoring_bundle", "material": "load_synthetic_material_response_bundle"}[kind]
    monkeypatch.setattr(composition, loader, lambda *_: pytest.fail("missing source companion reached adapter bundle"))
    keyword = {"rc": "circuit_authoring_dir", "electron": "electron_gas_authoring_dir", "material": "synthetic_material_authoring_dir"}[kind]
    with pytest.raises((OSError, ValueError, PermissionError, ArtifactPlaneError)):
        composition.create_cli_api(repo_root=ROOT, operator_storage_profile=object(), **{keyword: directory})


@pytest.mark.parametrize("family", ("rc_authoring", "synthetic_material_authoring", "uniform_electron_gas_authoring"))
def test_real_public_authoring_preserves_exposed_inputs_and_authenticates_selected_source(tmp_path, family):
    """Real source, compiler, writer and companion reader; no science/native seam."""
    module = importlib.import_module("empirical_lawhood.api." + family)
    writer = plane(tmp_path)
    output = tmp_path / "real-public-authoring"
    choices = {
        "rc_authoring": ("programmes/foundations/measurement-and-response/workflows/rc-ladder-response/study.json", module.ResistorCapacitorLadderStudyConfig if family == "rc_authoring" else None),
        "synthetic_material_authoring": ("programmes/materials/superconductivity/workflows/lattice-pairing-method/authoring.json", module.SyntheticMaterialResponseMethodConfig if family == "synthetic_material_authoring" else None),
        "uniform_electron_gas_authoring": ("programmes/materials/superconductivity/workflows/electron-gas-response/config.json", module.UniformElectronGasAnalyticReferenceConfig if family == "uniform_electron_gas_authoring" else None),
    }
    relative, kind = choices[family]
    raw = (ROOT / relative).read_bytes()
    config = decode_canonical_bytes(raw, kind, maximum_bytes=128 * 1024)
    common = dict(root=ROOT, experiment_id="software.actual-selected." + family.replace("_", "-"), output_dir=output, artifact_writer=writer)
    if family == "rc_authoring":
        report = module.author_fresh_rc(study=config, **common)
    elif family == "synthetic_material_authoring":
        report = module.author_synthetic_material_response(config=config, **common)
    else:
        report = module.author_uniform_electron_gas_analytic_reference(config=config, **common)
    assert report["native_tasks_executed"] == 0 and report["source_contacted"] is False
    assert report["task_count"] > 0 and report["authoring_dir"] == str(output)
    closure = shared.authenticate_authoring_source(directory=output, project_root=ROOT, artifact_writer=writer)
    assert type(closure) is ImplementationSourceClosure and closure.kind is SourceClosureKind.EXACT_SOURCE_CLOSURE
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT)
    assert closure.clean_worktree is (not bool(status))
    stored = decode_canonical_bytes((output / ("study.json" if family == "rc_authoring" else "config.json")).read_bytes(), kind, maximum_bytes=128 * 1024)
    assert stored == config and (ROOT / relative).read_bytes() == raw


def _actual_handoff_storage(tmp_path):
    mount = next(parent for parent in (tmp_path, *tmp_path.parents) if os.path.ismount(parent))
    profile = OperatorStorageProfile("software.selected-source-handoff", "external-filesystem", "1.0.0",
        str(tmp_path), str(mount), "artifacts", "scratch", OperatorStorageAccessMode.READ_WRITE,
        None, None, (), "strict-mount-contained-no-symlink", 1, (), 1, False)
    contract = resolve_external_root_contract(profile, repo_root=ROOT, home_root=Path.home())
    Path(contract.canonical_path).mkdir()
    return ExternalArtifactPlane(GuardedExternalRoot(contract)), profile


def _assert_actual_handoff_source(directory, writer):
    closure = shared.authenticate_authoring_source(directory=directory, project_root=ROOT, artifact_writer=writer)
    assert closure.kind is SourceClosureKind.EXACT_SOURCE_CLOSURE
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT)
    assert closure.implementation_commit == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert closure.clean_worktree is (not bool(status))
    observed = json.loads((directory / "provenance/source-observation.json").read_bytes())["value"]
    disclosure = json.loads(observed["source_observation_json"])
    for name in ("source_admission", "final_source_admission"):
        assert disclosure[name]["observed_checkout_clean"] is (not bool(status))
    assert {row["relative_path"] for row in disclosure["final_source_admission"]["changes"]
        if row["status"] == "??" and row["relative_path"] in NOTES} == {
            row[3:].decode() for row in status.split(b"\0")
            if row.startswith(b"?? ") and row[3:].decode() in NOTES}
    return closure


def _forbid_handoff_execution(monkeypatch):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore

    def forbidden(*args, **kwargs):
        pytest.fail("software author/load/prove attempted scientific execution or native contact")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(ExternalNativeEffectContactStore, "begin", forbidden)


def test_actual_selected_source_rc_canary_author_load_and_prove_without_execution(tmp_path, monkeypatch):
    """Actual source, compiler, exact profile, family loader and provider proof."""
    from empirical_lawhood.api import rc_challenge_authoring as module
    from empirical_lawhood.adapters.simulator_morphism_challenges.contracts import SimulatorMorphismChallengePhase
    from empirical_lawhood.adapters.simulator_morphism_challenges.descriptors import default_config

    writer, profile = _actual_handoff_storage(tmp_path)
    _forbid_handoff_execution(monkeypatch)
    config = default_config(SimulatorMorphismChallengePhase.CANARY)
    directory = Path(writer.root.contract.canonical_path) / "exposed-rc-canary-authoring"
    report = module.author_rc_challenge_phase(root=ROOT, config=config, external_records=(),
        output_dir=directory, artifact_writer=writer)
    handoff = module.load_rc_challenge_handoff(directory=directory, root=ROOT,
        storage_profile=profile, artifact_writer=writer)
    proof = module.prove_rc_challenge_handoff(handoff)
    closure = _assert_actual_handoff_source(directory, writer)
    assert not report["scientific_execution_performed"] and not proof["scientific_execution_performed"]
    assert report["task_count"] == proof["task_count"] == len(handoff.projection.tasks) > 0
    assert report["requested_independent_units"] == len(config.unit_ids)
    assert handoff.composition.issued_inputs.config == config
    assert handoff.composition.implementation_sha256 == closure.implementation_sha256
    assert handoff.projection.implementation_commit == closure.implementation_commit
    assert not Path(writer.root.contract.canonical_path, "runs").exists()


def test_actual_selected_source_finite_calibration32_author_load_and_prove_without_execution(tmp_path, monkeypatch):
    """Declared 32 roots remain unentered; no result, issue or qualification act."""
    from empirical_lawhood.api import finite_rerun_authoring as module
    from empirical_lawhood.api.finite_operands import current_nomination_operand_export
    from empirical_lawhood.adapters.composition.finite_response_law.rerun_input import (
        FiniteResponseLawCurrentExposure, original_development_exposure,
    )

    writer, profile = _actual_handoff_storage(tmp_path)
    _forbid_handoff_execution(monkeypatch)
    nomination_directory = Path(writer.root.contract.canonical_path) / "exposed-nomination"
    nomination_directory.mkdir()
    nomination = current_nomination_operand_export(nomination_directory,
        nomination_id="software.actual-selected.fixed-nomination")
    units, seeds = original_development_exposure()
    exposure = FiniteResponseLawCurrentExposure("software.actual-selected.exposure", units, seeds)
    allocation = module.prepare_finite_response_allocation(stage="calibration",
        cohort_namespace="empirical-lawhood.finite-response-law.calibration.software-selected-source",
        master_seed=202610190032, evidence_role="EXPOSED_DEVELOPMENT_NONPROMOTABLE")
    packet = module.prepare_finite_response_rerun(config_id="software.actual-selected.calibration32",
        stage="calibration", allocation=allocation, exposure=exposure, nomination=nomination,
        nomination_directory=nomination_directory, artifact_writer=writer)
    directory = Path(writer.root.contract.canonical_path) / "exposed-finite-calibration32-authoring"
    report = module.author_finite_response_rerun(root=ROOT, packet=packet, exposure=exposure,
        nomination_directory=nomination_directory, output_dir=directory, artifact_writer=writer)
    handoff = module.load_finite_response_rerun_handoff(directory=directory, root=ROOT,
        storage_profile=profile, artifact_writer=writer)
    proof = module.prove_finite_response_rerun_handoff(handoff)
    closure = _assert_actual_handoff_source(directory, writer)
    assert not report["scientific_execution_performed"] and not report["authority_created"]
    assert not proof["scientific_execution_performed"] and not proof["runtime_authority_bound"]
    assert report["independent_units"] == proof["independent_units"] == 32
    assert report["task_count"] == proof["task_count"] == len(handoff.projection.tasks) > 0
    assert handoff.packet == packet and handoff.packet.nomination == nomination
    assert handoff.projection.implementation_commit == closure.implementation_commit
    assert not Path(writer.root.contract.canonical_path, "runs").exists()


@pytest.mark.parametrize("family", ("rc_challenge_authoring", "finite_rerun_authoring", "preparation_applicability", "constructed_preparation_applicability"))
@pytest.mark.parametrize("damage", ("missing-companion", "clean-substitution"))
def test_actual_handoff_loader_requires_real_selected_source_before_reconstruction(tmp_path, monkeypatch, family, damage):
    """Real closure/publication guard; disclosed unrelated input/locator seams.

    The fixture supplies no scientific candidate or authority. Each actual loader
    must reject missing source custody before its real reconstruction consumer.
    """
    module = importlib.import_module("empirical_lawhood.api." + family)
    writer, directory, captured = current_packet(tmp_path)
    if damage == "missing-companion":
        (directory / "provenance/source-observation.json").unlink()
    else:
        downgraded = replace(captured.closure, kind=SourceClosureKind.CLEAN_GIT_COMMIT, clean_worktree=True, exact_source_manifest=None)
        (directory / "source-closure.json").write_bytes(downgraded.canonical_bytes())
        monkeypatch.setattr(module, "capture_clean_target_closure",
            lambda *_args: pytest.fail("selected provenance reached legacy source capture"))
    monkeypatch.setattr(module, "resolve_authoring_directory", lambda *_args, **_kwargs: (directory, writer.root.contract))
    def forbidden(*_args, **_kwargs):
        pytest.fail("missing selected-source companion reached scientific reconstruction")
    if family == "finite_rerun_authoring":
        original = module._read_record
        monkeypatch.setattr(module, "_read_record", lambda root, name, kind:
            original(root, name, kind) if name == "source-closure.json" else SimpleNamespace())
        monkeypatch.setattr(module, "_validate_parent", forbidden)
        loader = module.load_finite_response_rerun_handoff
    elif family == "rc_challenge_authoring":
        (directory / "issued-inputs.json").write_bytes(b"{}")
        original = module.decode_canonical_bytes
        monkeypatch.setattr(module, "decode_canonical_bytes", lambda raw, kind, **kwargs:
            SimpleNamespace() if kind is module.RCChallengeIssuedInputs else original(raw, kind, **kwargs))
        monkeypatch.setattr(module, "compose_simulator_morphism_challenges_phase", forbidden)
        loader = module.load_rc_challenge_handoff
    else:
        (directory / "selection.json").write_bytes(b"{}")
        original = module.decode_canonical_bytes
        monkeypatch.setattr(module, "decode_canonical_bytes", lambda raw, kind, **kwargs:
            original(raw, kind, **kwargs) if kind is ImplementationSourceClosure else SimpleNamespace(upstream_records=()))
        monkeypatch.setattr(module, "_bundle", forbidden)
        loader = module.load_constructed_preparation_applicability_handoff if family.startswith("constructed") else module.load_preparation_applicability_handoff
    message = "source provenance changes its exact separate companion census" if damage == "missing-companion" else "selected-source provenance cannot be replaced"
    error = ValueError if damage == "missing-companion" else PermissionError
    with pytest.raises(error, match=message):
        loader(directory=directory, root=ROOT, storage_profile=object(), artifact_writer=writer)


def test_real_selected_packet_cannot_be_relabelled_as_clean_while_retaining_publication(tmp_path):
    writer, directory, captured = current_packet(tmp_path)
    original_companions = {p.name: p.read_bytes() for p in (directory / "provenance").glob("*.json")}
    downgraded = replace(captured.closure, kind=SourceClosureKind.CLEAN_GIT_COMMIT,
        clean_worktree=True, exact_source_manifest=None)
    (directory / "source-closure.json").write_bytes(downgraded.canonical_bytes())
    with pytest.raises(PermissionError, match="selected-source provenance cannot be replaced"):
        shared.authenticate_authoring_source(directory=directory, project_root=ROOT, artifact_writer=writer)
    assert {p.name: p.read_bytes() for p in (directory / "provenance").glob("*.json")} == original_companions
