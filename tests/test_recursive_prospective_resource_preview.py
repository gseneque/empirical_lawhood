# SPDX-License-Identifier: MPL-2.0
"""Tiny actual compiler previews over disclosed, nonqualifying software inputs."""

from dataclasses import fields, replace
from pathlib import Path

import pytest

from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_inputs import (
    ProtectedFactorialPreparationRequest, bind_protected_factorial_preparation_request,
    validate_protected_factorial_request_binding,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_resources import ProtectedFactorialResourceSelection
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs
from tests import test_prospective_experiment as fixtures


selected = fixtures.selected


def _bindings(selected):
    def content(digest):
        return selected.plane.root.resolve("candidate-inputs/sha256/" + digest[:2] + "/" + digest, for_write=False)

    bindings = [(row.logical_artifact_id, content(row.content_sha256)) for row in selected.prospective_spec.external_operands]
    bindings.extend((digest, content(digest)) for digest in sorted({row.source_config_sha256
        for row in selected.prospective_spec.draft.prospective_draft.source_materializations}))
    return tuple(bindings)


def _arguments(selected):
    return dict(project_root=selected.root / "checkout", artifact_writer=selected.plane,
        input_bindings=_bindings(selected), composition=selected.composition,
        api_factory=selected.api_factory, candidate_catalog=selected.candidate_catalog)


@pytest.fixture(scope="module")
def preview(selected):
    value = owner.preview_recursive_prospective_candidate(
        design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec), **_arguments(selected))
    assert not tuple(Path(selected.plane.root.contract.canonical_path).glob(".prospective-candidate-*"))
    return value


def test_resource_free_design_preserves_every_existing_scientific_field(selected):
    spec = selected.prospective_spec
    design = RecursiveProspectiveDesignInputs.from_spec(spec)
    assert {field.name for field in fields(design)} == {field.name for field in fields(spec)} - {"resources"}
    assert design.bind_resources(spec.resources).canonical_bytes() == spec.canonical_bytes()
    for malformed in (None, object()):
        with pytest.raises(TypeError, match="exact bound resource envelope"):
            design.bind_resources(malformed)


def test_preview_is_actual_outer_candidate_and_original_extension_projection(selected, preview):
    raw = (selected.original.directory / "candidate.json").read_bytes()
    assert preview.candidate == decode_canonical_bytes(raw, ExecutableStudyCandidate, maximum_bytes=len(raw))
    assert selected.prospective_spec.resources.issued_study_extensions.object_fingerprint == preview.issued_extensions.fingerprint()
    assert preview.implementation.source_closure_id == selected.prospective_spec.spec_id + ".source-closure"


def test_fresh_preview_authoring_preserves_all_fourteen_fully_bound_members(selected, preview):
    directory = Path(selected.plane.root.contract.canonical_path) / "from-resource-preview"
    report = owner.author_recursive_prospective(spec=selected.prospective_spec, output_dir=directory,
        expected_preview=preview, **_arguments(selected))
    original = decode_canonical_bytes((selected.original.directory / "authored-wave.json").read_bytes(),
        AuthoredRecursiveWave, maximum_bytes=None)
    new = decode_canonical_bytes((directory / "authored-wave.json").read_bytes(), AuthoredRecursiveWave, maximum_bytes=None)
    assert len(new.members) == 14 and new == original
    for member in new.members:
        assert (directory / member.filename).read_bytes() == (selected.original.directory / member.filename).read_bytes()
    assert report["scientific_authority"] == "NONE" and report["native_contact"] == "none"


@pytest.mark.parametrize("capacity", (64, 128))
def test_preview_and_authoring_share_capacity_for_the_actual_retained_draft(selected, monkeypatch, capacity):
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded64 import executable_binding as large
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_draft128.executable_binding import REGISTRATION as EXTENDED
    from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection, bind_execution_resources
    from empirical_lawhood.runtime.recursive_prospective_envelope import RecursiveProspectiveAuthoringEnvelope

    original = selected.prospective_spec
    # The projection fits the legacy decoder, while the actual draft and
    # authoring exceed scaled legacy carriers. No scientific bytes are invented.
    monkeypatch.setattr(owner, "MAXIMUM_SPEC_BYTES", len(original.draft.canonical_bytes()) - 1)
    expected_decoder = large.REGISTRATION if capacity == 64 else EXTENDED
    if capacity == 128:
        monkeypatch.setattr(owner, "LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES", len(original.draft.canonical_bytes()) - 1)
    design = RecursiveProspectiveDesignInputs.from_spec(original)
    controls = ExecutionResourceSelection(**{field.name: getattr(original.resources, field.name)
        for field in fields(ExecutionResourceSelection)})
    directory = Path(selected.plane.root.contract.canonical_path) / ("draft-capacity-preview-" + str(capacity))
    calls = []
    compile_candidate = owner._compile_outer_candidate
    def compile_once(**kwargs):
        calls.append(True)
        return compile_candidate(**kwargs)
    monkeypatch.setattr(owner, "_compile_outer_candidate", compile_once)
    with owner._prospective_preparation_scope():
        preview = owner.preview_recursive_prospective_candidate(design_inputs=design, **_arguments(selected))
        spec = design.bind_resources(bind_execution_resources(controls, issued_extensions=preview.issued_extensions))
        report = owner.author_recursive_prospective(spec=spec, output_dir=directory,
            expected_preview=preview, **_arguments(selected))
    assert calls == [True]
    assert (directory / "decoder.json").read_bytes() == expected_decoder.canonical_bytes()
    envelope = decode_canonical_bytes((directory / "recursive-prospective.json").read_bytes(),
        RecursiveProspectiveAuthoringEnvelope, maximum_bytes=None)
    assert envelope.reconstruct().canonical_bytes() == spec.canonical_bytes()
    assert (directory / "draft.json").read_bytes() == original.draft.canonical_bytes()
    assert report["native_contact"] == "none" and report["scientific_authority"] == "NONE"
    loaded = owner.load_retained_recursive_prospective_handoff(directory=directory, root=selected.root / "checkout",
        storage_profile=object(), artifact_writer=selected.plane)
    assert loaded.draft.canonical_bytes() == spec.draft.canonical_bytes()


@pytest.mark.parametrize("mutation", ("source", "outer-candidate", "extensions"))
def test_final_authoring_recompiles_and_refuses_changed_preview_facts(selected, preview, mutation):
    changed = {
        "source": lambda: replace(preview, implementation=replace(preview.implementation, implementation_sha256="b" * 64)),
        "outer-candidate": lambda: replace(preview, candidate=replace(preview.candidate, candidate_id="candidate.substituted")),
        "extensions": lambda: replace(preview, issued_extensions=replace(preview.issued_extensions,
            issued_extension_set_id="extensions.substituted")),
    }[mutation]()
    directory = Path(selected.plane.root.contract.canonical_path) / ("refused-preview-" + mutation)
    refusal = (
        "prospective source capture changes its retained exact selected-source identity"
        if mutation == "source"
        else "fresh source, outer candidate or issued-extension preview"
    )
    with pytest.raises(ValueError, match=refusal):
        owner.author_recursive_prospective(spec=selected.prospective_spec, output_dir=directory,
            expected_preview=changed, **_arguments(selected))
    assert not (directory / "authored-wave.json").exists()


def test_changed_scientific_preview_refuses_before_candidate_publication(selected, preview):
    changed = replace(preview, design_inputs=replace(preview.design_inputs,
        draft=replace(preview.design_inputs.draft, question="Changed scientific question.")))
    directory = Path(selected.plane.root.contract.canonical_path) / "refused-preview-design"
    with pytest.raises(ValueError, match="preview scientific design inputs"):
        owner.author_recursive_prospective(spec=selected.prospective_spec, output_dir=directory,
            expected_preview=changed, **_arguments(selected))
    assert not directory.exists()


def _request(selected):
    spec = selected.prospective_spec
    resources = ProtectedFactorialResourceSelection(**{field.name: getattr(spec.resources, field.name)
        for field in fields(ProtectedFactorialResourceSelection)})
    return ProtectedFactorialPreparationRequest("request.disclosed-software-fixture",
        selected.preparation.input_files[0][1].identity, spec.draft.prospective_draft.resource_ceiling,
        spec.formal_methods, spec.formal_source_inventories, spec.qualifications, (selected.config,), resources)


def test_unbound_request_binds_actual_extensions_without_rewriting_request(selected, preview):
    request = _request(selected)
    raw = request.canonical_bytes()
    assert not hasattr(request, "resources") and not hasattr(request.resource_selection, "issued_study_extensions")
    bound = bind_protected_factorial_preparation_request(request, issued_extensions=preview.issued_extensions)
    validate_protected_factorial_request_binding(request, bound)
    assert bound.selection_id == request.request_id + ".bound"
    assert bound.resources == selected.prospective_spec.resources
    assert request.canonical_bytes() == raw
    assert decode_canonical_bytes(raw, ProtectedFactorialPreparationRequest, maximum_bytes=len(raw)) == request


@pytest.mark.parametrize("mutation", ("bound-id", "bank", "configs", "resource"))
def test_request_binding_refuses_source_identity_or_operational_substitution(selected, preview, mutation):
    request = _request(selected)
    bound = bind_protected_factorial_preparation_request(request, issued_extensions=preview.issued_extensions)
    changed = {
        "bound-id": lambda: replace(bound, selection_id="selection.substituted"),
        "bank": lambda: replace(bound, bank=replace(bound.bank, sha256="d" * 64)),
        "configs": lambda: replace(bound, source_configs=()),
        "resource": lambda: replace(bound, resources=replace(bound.resources,
            aggregate_memory_ceiling_bytes=bound.resources.aggregate_memory_ceiling_bytes + 1)),
    }[mutation]()
    with pytest.raises(ValueError, match="exact original request or resource choices"):
        validate_protected_factorial_request_binding(request, changed)


def _install_fixture_hook(selected, monkeypatch, hook):
    from empirical_lawhood.api import experiment_preparation as preparation_owner
    from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding

    declaration = replace(preparation_owner._protocol(selected.preparation.specification_record), requires_prospective_runtime_binding=True)
    monkeypatch.setattr(preparation_owner, "_protocol", lambda _: declaration)
    monkeypatch.setattr(preparation_owner, "experiment_runtime_binding", lambda _: ExperimentRuntimeBinding(
        declaration.protocol_id, lambda *_args, **_kwargs: None, hook))
    return preparation_owner


def test_common_api_invokes_hook_before_entry_guard_and_forwards_exact_preview(selected, preview, monkeypatch):
    from empirical_lawhood.api import prospective_experiment
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentDependency

    dependency = ExperimentDependency("fixture.mechanical-resource-projection", DependencyKind.SOFTWARE, "Fixture projection pending.")
    partial = replace(selected.preparation, dependencies=(dependency,))
    calls = []

    def hook(preparation, **arguments):
        calls.append(preparation)
        return replace(preparation, dependencies=(), prospective_spec=selected.prospective_spec,
            source_configs=(selected.config,), prospective_candidate_preview=preview)

    preparation_owner = _install_fixture_hook(selected, monkeypatch, hook)

    def author(**arguments):
        assert arguments["preparation"].prospective_candidate_preview == preview
        return {"status": "FIXTURE_ROUTING_ONLY"}

    monkeypatch.setattr(prospective_experiment, "author_prepared_prospective_experiment", author)
    assert preparation_owner.author_prepared_experiment(preparation=partial, project_root=selected.root / "checkout",
        artifact_writer=selected.plane, output_dir=selected.directory.parent / "fixture-hook") == {"status": "FIXTURE_ROUTING_ONLY"}
    assert calls == [partial]


@pytest.mark.parametrize("mutation", ("question", "original-record", "authority"))
def test_common_api_hook_cannot_change_science_drop_original_or_waive_authority(selected, monkeypatch, mutation):
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentDependency

    partial = selected.preparation
    if mutation == "authority":
        partial = replace(partial, dependencies=(ExperimentDependency("authority.missing", DependencyKind.AUTHORITY, "No grant."),))

    def hook(preparation, **arguments):
        if mutation == "question":
            return replace(preparation, draft=replace(preparation.draft, question="Substituted question."))
        return replace(preparation, design_records=() if mutation == "original-record" else preparation.design_records, dependencies=())

    preparation_owner = _install_fixture_hook(selected, monkeypatch, hook)
    with pytest.raises(ValueError, match="changed its original scientific|dropped or replaced an original|dropped an unresolved"):
        preparation_owner.author_prepared_experiment(preparation=partial, project_root=selected.root / "checkout",
            artifact_writer=selected.plane, output_dir=selected.directory.parent / ("refused-hook-" + mutation))


@pytest.mark.parametrize("kind_name", ("SOFTWARE", "SCIENTIFIC_EVIDENCE", "AUTHORITY", "EXTERNAL_INPUT", "ENVIRONMENT", "STORAGE"))
def test_domain_hook_rejects_every_injected_entry_dependency_before_discovery(selected, monkeypatch, kind_name):
    from empirical_lawhood.api import matrix_protected_experiment, experiment_runtime_bindings
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import ScheduledFactorialCriteriaBinding
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import (
        ProtectedFactorialAcquisitionRoster, ProtectedFactorialExperimentSpecification,
    )
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_entry import StudyDefinition
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentDependency

    def reference(name, kind, digest):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, digest * 64)

    specification = ProtectedFactorialExperimentSpecification("specification.unresolved",
        reference("study.unresolved", StudyDefinition, "a"), reference("criteria.unresolved", ScheduledFactorialCriteriaBinding, "b"),
        reference("roster.unresolved", ProtectedFactorialAcquisitionRoster, "c"), "Unresolved software-only metadata.")
    partial = replace(selected.preparation, specification=specification.identity, specification_record=specification,
        dependencies=(ExperimentDependency("injected.entry-dependency", DependencyKind(kind_name), "Remains unavailable."),))
    monkeypatch.setattr(experiment_runtime_bindings, "experiment_runtime_binding", lambda _: pytest.fail("entry refusal must precede discovery"))
    with pytest.raises(ValueError, match="unresolved entry dependencies"):
        matrix_protected_experiment.prepare_protected_factorial_experiment_authoring(partial,
            project_root=selected.root / "checkout", artifact_writer=selected.plane, output_dir=selected.directory.parent / "never-authored")


def test_entire_tiny_fixture_stays_within_five_mib_output_budget(selected):
    assert sum(path.stat().st_size for path in selected.root.rglob("*") if path.is_file()) < 5 * 1024**2
