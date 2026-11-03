# SPDX-License-Identifier: MPL-2.0
"""Default recovery loader guard and truthful assessment status propagation."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api import selected_e4_programme_service as owner
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.runtime_platform.test_artifact_verification_scope import _publication

ROOT = Path(__file__).resolve().parents[1]


def wrapper_state(monkeypatch, service, *, collection=None):
    wrapper = owner.SelectedE4ProgrammeService(service=service)
    declaration_pin = ObjectIdentity("declaration.test.scope", "empirical-lawhood/testing/declaration", "1.0.0", "a" * 64)
    programme_pin = ObjectIdentity("programme.test.scope", "empirical-lawhood/testing/programme", "1.0.0", "b" * 64)
    plan = SimpleNamespace(identity=programme_pin, component_ids=("wave.a", "assessment"),
        declaration=SimpleNamespace(identity=declaration_pin, maximum_parallel_tasks=4,
            programme=SimpleNamespace(waves=(SimpleNamespace(wave_id="wave.a"),))))
    wave = owner.SelectedE4ComponentRequest("wave.a", "run.wave.a", "controls/wave.json", "authority.reveal.wave",
        None, ())
    assessment = owner.SelectedE4ComponentRequest("assessment", "run.assessment", "controls/assessment.json", "authority.reveal.assessment",
        None, ())
    request = SimpleNamespace(components=(wave, assessment), collection=collection)
    monkeypatch.setattr(wrapper, "_state", lambda directory: (plan, None))
    monkeypatch.setattr(wrapper, "_request", lambda path, value, **_kwargs: request)
    monkeypatch.setattr(wrapper, "_unentered", lambda value: None)
    return wrapper, plan, request


def test_composite_recovery_reaches_actual_default_retained_loader_with_exact_run(tmp_path, monkeypatch):
    writer, _ = _publication(tmp_path, count=1)
    service = ExperimentProgrammeService(ROOT, writer, SimpleNamespace(maximum_parallel_tasks=4))
    assert service.prospective_experiment_loader is None
    assert service.prospective_api_factory is None
    wrapper, _, _ = wrapper_state(monkeypatch, service)
    before = tuple(sorted(value.relative_to(tmp_path) for value in tmp_path.rglob("*") if value.is_file()))
    # No loader override: actual load_retained_prospective_experiment must try
    # the guarded missing component. The historical bug stopped earlier with
    # "default recovery requires its exact requested run identity".
    with pytest.raises(FileNotFoundError):
        wrapper.recover(directory=Path(writer.root.contract.canonical_path) / "missing-programme",
            maximum_parallel_tasks=4, confirmed=True)
    after = tuple(sorted(value.relative_to(tmp_path) for value in tmp_path.rglob("*") if value.is_file()))
    assert after == before


def test_default_recovery_still_refuses_omitted_run_before_any_custody_contact():
    class Forbidden:
        artifact_verification = "strict"
        def __getattr__(self, name):
            pytest.fail("missing recovery run contacted custody: " + name)
    service = ExperimentProgrammeService(ROOT, Forbidden(), SimpleNamespace(maximum_parallel_tasks=4))
    with pytest.raises(ValueError, match="exact requested run identity"):
        service._prospective_context(Path("/unused/retained"), lifecycle="recover")


@pytest.mark.parametrize("recover", (False, True))
@pytest.mark.parametrize("status", ("SUCCEEDED", "REFUSED", "BLOCKED", "INVALID", "NOT_FOUND", "CONFLICT", "FAILED", "RUNNING", None))
def test_complete_wave_denominator_does_not_turn_refused_or_nonterminal_assessment_into_retained(
        tmp_path, monkeypatch, recover, status):
    operations, publications, contexts, reads, structure_reads = [], [], [], [], []
    root = tmp_path / "guarded"
    (root / "programme" / "components" / "assessment").mkdir(parents=True)
    result = {"reason_codes": ("ACTUAL_ASSESSMENT_DEPENDENCY",)}
    if status is not None:
        result["status"] = status
    def operation(**kwargs):
        request = kwargs["request"]
        run_id = getattr(request, "run_id", "")
        assessment = run_id == "run.assessment" or getattr(request, "path", None) == root / "controls/assessment.json"
        operations.append("assessment" if assessment else "wave")
        return result if assessment else {"status": "SUCCEEDED"}
    full = {**result, 'scientific_result': {'disclosed_assessment': True}}
    def read(**kwargs):
        reads.append(kwargs)
        return full
    service = SimpleNamespace(artifact_writer=SimpleNamespace(root=SimpleNamespace(resolve=lambda relative, **kwargs: root / relative)),
        run=operation, recover=operation, read=read)
    service._prospective_context = lambda *args, **kwargs: contexts.append(kwargs) or (object(), object())
    wrapper, plan, request = wrapper_state(monkeypatch, service)
    request.collection = SimpleNamespace(evidence=SimpleNamespace(declaration=plan.declaration.identity,
        waves=(SimpleNamespace(locator="actual.wave.locator"),)))
    monkeypatch.setattr(owner, "preflight_selected_e4_component", lambda **kwargs: None)
    monkeypatch.setattr(owner, "_locator", lambda *args: "actual.wave.locator")
    monkeypatch.setattr(wrapper, "_structure", lambda **_kwargs: structure_reads.append(True) or ((), {
        "assigned_group_count": 64, "assigned_case_count": 576, "complete_wave_count": 8}))
    monkeypatch.setattr(wrapper, "_publish_observations", lambda *args: publications.append("authenticated-prior-wave-observations"))
    report = wrapper._operation(directory=root / "programme", maximum_parallel_tasks=4,
        programme_request_path=None, confirmed=True, recover=recover)
    assert report["assessment"] is (full if status == 'SUCCEEDED' else result)
    assert report['scientific_completion'] == ('ASSESSMENT_RETAINED' if status == 'SUCCEEDED' else 'NOT_ESTABLISHED')
    assert len(reads) == (1 if status == 'SUCCEEDED' else 0) and structure_reads == [True]
    if reads:
        assert reads[0]['request'].run_id == 'run.assessment'
        assert reads[0]['reveal_authority_id'] == 'authority.reveal.assessment'
    assert report["state"] == ("ASSESSMENT_RETAINED" if status == "SUCCEEDED" else "ASSESSMENT_REFUSED_OR_INCOMPLETE")
    assert (report["assigned_group_count"], report["assigned_case_count"]) == (64, 576)
    assert report["scientific_qualification"] == "NOT_ESTABLISHED"
    assert operations == ["wave", "assessment"]
    assert publications == ["authenticated-prior-wave-observations"]
    assert tuple(value["recovery_run_id"] for value in contexts) == (
        ("run.wave.a", "run.assessment") if recover else (None, None))
    assert not tuple((root / "programme" / "components" / "assessment").iterdir())


@pytest.mark.parametrize("recover", (False, True))
@pytest.mark.parametrize("damage", ("run", "candidate", "reveal"))
def test_actual_assessment_preflight_refuses_before_any_wave_dispatch(tmp_path, monkeypatch, recover, damage):
    """Exercise the same actual run/candidate/reveal validator used by waves."""
    calls, contexts = [], []
    root = tmp_path / "guarded"
    (root / "programme/components/assessment").mkdir(parents=True)

    class Candidate:
        candidate_id = "candidate.disclosed-e4"
        SCHEMA = "empirical-lawhood/testing/candidate"
        VERSION = "1.0.0"
        def fingerprint(self):
            return "1" * 64

    candidate = Candidate()
    package = SimpleNamespace(run_plan_id="run.foreign" if damage == "run" else "run.assessment",
        issued_study=SimpleNamespace(candidate=candidate))
    selected = SimpleNamespace(association=SimpleNamespace(candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate)))
    if damage == "candidate":
        selected.association.candidate = replace(selected.association.candidate, object_fingerprint="2" * 64)
    execution = SimpleNamespace(load_persisted_package=lambda run_id: package,
        _check_identity=lambda *args, **kwargs: None, _validate_campaign_authorization=lambda *args, **kwargs: None,
        _validate_issued_execution_authority=lambda *args, **kwargs: None)
    def reveal(*args, **kwargs):
        assert kwargs["reveal_authority_id"] == "authority.reveal.assessment"
        raise PermissionError("actual selected assessment reveal refused")
    execution._validate_issued_reveal_authority = reveal
    api = SimpleNamespace(_execution_service=execution,
        _compile_path=lambda path: (package, SimpleNamespace(run_plan_id=package.run_plan_id), object()),
        _compile_package=lambda value: (SimpleNamespace(run_plan_id=value.run_plan_id), object()),
        _study_issue_clock=SimpleNamespace(now_utc=lambda: "2026-10-17T00:00:00Z"))
    def context(path, **kwargs):
        contexts.append((Path(path).name, kwargs))
        return selected, api
    def forbidden(**kwargs):
        calls.append(kwargs)
        pytest.fail("refused assessment preflight dispatched a wave")
    service = SimpleNamespace(artifact_writer=SimpleNamespace(root=SimpleNamespace(resolve=lambda relative, **kwargs: root / relative)),
        run=forbidden, recover=forbidden, _prospective_context=context)
    wrapper, _, _ = wrapper_state(monkeypatch, service)
    actual = owner.preflight_selected_e4_component
    def preflight(**kwargs):
        if kwargs["expected_run_id"] == "run.assessment":
            return actual(**kwargs)
    monkeypatch.setattr(owner, "preflight_selected_e4_component", preflight)
    with pytest.raises(PermissionError, match="run/candidate|reveal refused"):
        wrapper._operation(directory=root / "programme", maximum_parallel_tasks=4,
            programme_request_path=None, confirmed=True, recover=recover)
    assert not calls
    assert tuple(name for name, _ in contexts) == ("wave.a", "assessment")
    assert contexts[-1][1]["recovery_run_id"] == ("run.assessment" if recover else None)


def test_missing_issued_assessment_package_refuses_before_context_or_wave_dispatch(tmp_path, monkeypatch):
    calls = []
    service = SimpleNamespace(artifact_writer=object(),
        _prospective_context=lambda *args, **kwargs: calls.append("context"),
        run=lambda **kwargs: calls.append("run"))
    wrapper, _, request = wrapper_state(monkeypatch, service)
    wave, assessment = request.components
    request.components = (wave, replace(assessment, package_path=None))
    with pytest.raises(ValueError, match="issued package path: assessment"):
        wrapper.run(directory=tmp_path / "programme", maximum_parallel_tasks=4, confirmed=True)
    assert not calls


@pytest.mark.parametrize("already_authored", (False, True))
def test_unissued_assessment_is_an_absent_component_until_actual_authority_selection(tmp_path, monkeypatch, already_authored):
    operations, authored = [], []
    root = tmp_path / "guarded"
    directory = root / "programme"
    assessment_directory = directory / "components/assessment"
    if already_authored:
        assessment_directory.mkdir(parents=True)
    service = SimpleNamespace(project_root=ROOT, artifact_writer=SimpleNamespace(root=SimpleNamespace(resolve=lambda relative, **kwargs: root / relative)),
        run=lambda **kwargs: operations.append(kwargs) or {"status": "SUCCEEDED", "new_native_contact_count": 2},
        _prospective_context=lambda *args, **kwargs: (object(), object()))
    wrapper, plan, request = wrapper_state(monkeypatch, service)
    request.components = tuple(value for value in request.components if value.component_id != "assessment")
    request.collection = SimpleNamespace(evidence=SimpleNamespace(declaration=plan.declaration.identity,
        waves=(SimpleNamespace(locator="actual.wave.locator"),)))
    monkeypatch.setattr(wrapper, "_state", lambda directory: (plan, SimpleNamespace(declaration_publication=object(), source_snapshot=object())))
    monkeypatch.setattr(owner, "preflight_selected_e4_component", lambda **kwargs: None)
    # Sequencing only; source-preflight adversaries exercise the real helper.
    monkeypatch.setattr(owner.programme_source, "preflight_programme_source", lambda *args: None)
    monkeypatch.setattr(owner, "_locator", lambda *args: "actual.wave.locator")
    monkeypatch.setattr(wrapper, "_structure", lambda **_kwargs: ((), {"new_native_contact_count": 0}))
    monkeypatch.setattr(wrapper, "_publish_observations", lambda *args: None)
    def author(**kwargs):
        authored.append(kwargs["component"])
        assessment_directory.mkdir(parents=True)
    monkeypatch.setattr(wrapper, "_author_component", author)
    report = wrapper.run(directory=directory, maximum_parallel_tasks=4, confirmed=True)
    assert report["state"] == "ASSESSMENT_AUTHORITY_REQUIRED" and report["new_native_contact_count"] == 2
    assert len(operations) == 1 and authored == ([] if already_authored else ["assessment"])
    assert report["assessment_directory"] == str(assessment_directory)
    with pytest.raises(ValueError, match="stable identifier"):
        owner.SelectedE4ComponentRequest("assessment", "run.assessment", None, None, None, ())


@pytest.mark.parametrize("contacts", (0, 3, None))
def test_execution_contact_delta_does_not_inherit_read_only_zero(tmp_path, monkeypatch, contacts):
    root = tmp_path / "guarded"
    (root / "programme/components/assessment").mkdir(parents=True)
    def run(**kwargs):
        return {"status": "SUCCEEDED", **({} if contacts is None else {"new_native_contact_count": contacts})}
    service = SimpleNamespace(artifact_writer=SimpleNamespace(root=SimpleNamespace(resolve=lambda relative, **kwargs: root / relative)),
        run=run, _prospective_context=lambda *args, **kwargs: (object(), object()))
    wrapper, _, _ = wrapper_state(monkeypatch, service)
    monkeypatch.setattr(owner, "preflight_selected_e4_component", lambda **kwargs: None)
    monkeypatch.setattr(wrapper, "_structure", lambda **_kwargs: ((), {"new_native_contact_count": 0}))
    report = wrapper.run(directory=root / "programme", maximum_parallel_tasks=4, confirmed=True)
    assert report["new_native_contact_count"] == contacts
