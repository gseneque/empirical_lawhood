# SPDX-License-Identifier: MPL-2.0
"""Composite client admission with the existing disclosed dispatch fixture."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import application_programme as owner
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, MAX_RESPONSE_BYTES, load_application_json, response_bytes
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.execution.experiment_programme import PROGRAMME_DESCRIPTOR_FILENAME
from tests.runtime_platform.test_composite_experiment_programme import _descriptor, _installed, _lifecycle, _service


@pytest.fixture
def selected(tmp_path, monkeypatch):
    from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
    service, directory = _service(tmp_path)
    service = replace(service, project_root=Path(__file__).resolve().parents[1])
    calls = []
    lifecycle = _lifecycle(calls)
    _installed(monkeypatch, lambda **kwargs: lifecycle)
    write_experiment_programme_descriptor(service=service, directory=directory, descriptor=_descriptor())
    inputs = directory.parent / "inputs"
    inputs.mkdir()
    selection = inputs / "component-request.json"
    selection.write_bytes(b'{"fixture":"original-component-selection"}')
    context = ApplicationContext("composite", "Disclosed composite dispatch fixture", Path("/selected/python"),
        project_root=service.project_root, operator_profile=Path("/selected/profile"), input_root=inputs, maximum_parallel_tasks=4)
    profile = SimpleNamespace(maximum_parallel_tasks=4, to_document=lambda: {"fixture": True})
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: (service.project_root, profile, service.artifact_writer))
    return SimpleNamespace(context=context, directory=directory, selection=selection, calls=calls,
        lifecycle=lifecycle, service=service)


def run(selected, operation, **values):
    return execute_application(selected.context,
        ApplicationRequest("composite.control", selected.context.context_id, operation, tuple(values.items())))


def wire(result):
    assert result.succeeded, result
    return load_application_json(response_bytes(result), maximum_bytes=MAX_RESPONSE_BYTES)["payload"]


def review(selected, action="RUN"):
    return wire(run(selected, "programme.review", directory=str(selected.directory), action=action,
        programme_request=str(selected.selection)))


@pytest.mark.parametrize("action", ("RUN", "RECOVER"))
def test_review_never_calls_even_unconfirmed_run_and_apply_uses_exact_owner(selected, action):
    report = review(selected, action)
    assert selected.calls == [] and report["owning_review"]["scientific_result"] == "NOT_READ_BY_REVIEW"
    returned = wire(run(selected, "programme.apply", **report["selection"], expected_review_sha256=report["review_sha256"]))
    assert returned["report"] == {"lifecycle": action.lower()}
    assert selected.calls == [(action.lower(), {"directory": selected.directory,
        "programme_request_path": selected.selection, "maximum_parallel_tasks": selected.context.maximum_parallel_tasks,
        "confirmed": True})]


@pytest.mark.parametrize("change", ("bytes", "context", "action", "descriptor"))
def test_changed_review_refuses_before_component_entry(selected, change):
    report = review(selected)
    values = dict(report["selection"])
    if change == "bytes":
        selected.selection.write_bytes(b'{"fixture":"changed"}')
    elif change == "context":
        selected.context = replace(selected.context, label="Changed reviewed context")
    elif change == "action":
        values["action"] = "RECOVER"
    else:
        (selected.directory / PROGRAMME_DESCRIPTOR_FILENAME).write_bytes(replace(_descriptor(), record_id="changed.descriptor").canonical_bytes())
    result = run(selected, "programme.apply", **values, expected_review_sha256=report["review_sha256"])
    assert result.reason_codes == ("REVIEW_CHANGED",) and selected.calls == []


def test_component_authority_remains_required_after_client_confirmation(selected):
    def refuse(**kwargs):
        selected.calls.append(kwargs)
        raise PermissionError("original component authority missing")
    selected.lifecycle.run = refuse
    report = review(selected)
    result = run(selected, "programme.apply", **report["selection"], expected_review_sha256=report["review_sha256"])
    assert not result.succeeded and result.payload is None and len(selected.calls) == 1
    assert selected.calls[0]["programme_request_path"] == selected.selection


def test_absent_or_damaged_selector_never_falls_back_to_single_campaign(selected, monkeypatch):
    monkeypatch.setattr(ExperimentProgrammeService, "_is_prospective", lambda *a: pytest.fail("single-campaign fallback"))
    path = selected.directory / PROGRAMME_DESCRIPTOR_FILENAME
    path.unlink()
    assert run(selected, "programme.review", directory=str(selected.directory), action="RUN").reason_codes == ("COMPOSITE_REQUIRED",)
    path.write_bytes(b"{}")
    assert not run(selected, "programme.read", directory=str(selected.directory)).succeeded
    assert selected.calls == []


def test_original_read_preserves_adverse_missing_components_and_scope(selected):
    original = {"state": "INCOMPLETE", "scientific_qualification": "NOT_ESTABLISHED",
        "phases": [{"component": "assessed", "disposition": "FALSIFIED", "independent_units": 3},
            {"component": "missing", "disposition": "NOT_ATTEMPTED", "independent_units": None}],
        "frontier": {"required": ["original-authority"]}}
    selected.lifecycle.read = lambda **kwargs: original
    result = wire(run(selected, "programme.read", directory=str(selected.directory)))
    assert result["programme"] == original and [row["record"] for row in result["page"]["rows"]] == original["phases"]
    assert result["summary"]["state"] == "INCOMPLETE"


def test_protected_single_campaign_access_refuses_before_storage(selected, monkeypatch):
    selected.context = replace(selected.context, read_access_paths=(Path("/original/access"),))
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: pytest.fail("single-campaign authority crossed"))
    assert run(selected, "programme.read", directory=str(selected.directory)).reason_codes == ("UNSUPPORTED_ACCESS_SELECTION",)


def test_changed_descriptor_during_read_suppresses_the_whole_projection(selected):
    def changed(**kwargs):
        (selected.directory / PROGRAMME_DESCRIPTOR_FILENAME).write_bytes(replace(_descriptor(), record_id="changed.descriptor").canonical_bytes())
        return {"state": "COMPLETE"}
    selected.lifecycle.read = changed
    result = run(selected, "programme.read", directory=str(selected.directory))
    assert not result.succeeded and result.payload is None


def test_prepare_and_author_use_original_registered_inputs_and_preparation(selected, monkeypatch):
    from empirical_lawhood.api import experiment_preparation as preparation_owner
    from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.records.serialization import validate_stable_id
    from empirical_lawhood.design.experiment_inputs import ExperimentInputSelection
    from empirical_lawhood.execution.experiment_preparation import ExperimentCensus, ExperimentPreparation, PreparedExperimentInputs
    from tests.runtime_platform.test_composite_experiment_programme import SoftwareProgramme, SoftwareSpecification

    monkeypatch.setattr(SoftwareSpecification, "identity", property(lambda spec:
        ObjectIdentity.from_record(spec.record_id, spec)), raising=False)
    monkeypatch.setattr(SoftwareProgramme, "__post_init__", lambda record:
        validate_stable_id(record.record_id), raising=False)
    declaration = _installed(monkeypatch, lambda **kwargs: selected.lifecycle)
    def prepare(specification, **kwargs):
        selected.calls.append(("prepare", kwargs))
        return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0), (),
            programme=SoftwareProgramme())
    declaration = replace(declaration, prepare=prepare, input_record_types=(SoftwareProgramme,),
        bind_inputs=lambda spec, records: PreparedExperimentInputs(records))
    monkeypatch.setattr(preparation_owner, "experiment_protocols", lambda: (declaration,))
    inputs = selected.context.input_root
    (inputs / "specification.json").write_bytes(SoftwareSpecification().canonical_bytes())
    (inputs / "sources.json").write_bytes(ExperimentInputSelection("fixture.selection", "fixture.composite", ()).canonical_bytes())
    (inputs / "implementation.json").write_bytes(implementation_binding(Path(__file__).resolve().parents[1]).canonical_bytes())
    destination = selected.directory.parent / "new-programme"
    values = {"input": str(inputs / "specification.json"), "sources": str(inputs / "sources.json"),
        "source_snapshot": str(inputs / "implementation.json"), "environment_id": "fixture.environment", "output_dir": str(destination)}
    report = wire(run(selected, "programme.prepare", **values))
    assert not destination.exists() and [name for name, _ in selected.calls] == ["prepare"]
    assert report["owning_review"]["census"]["native_effects"] == 0
    def author(**kwargs):
        selected.calls.append(("author", kwargs))
        kwargs["output_dir"].mkdir()
        write_experiment_programme_descriptor(service=selected.service, directory=kwargs["output_dir"], descriptor=_descriptor())
        return {"authoring_dir": str(kwargs["output_dir"])}
    selected.lifecycle.author = author
    changed = {**values, "environment_id": "fixture.changed"}
    refused = run(selected, "programme.author", **changed, expected_review_sha256=report["review_sha256"])
    assert refused.reason_codes == ("REVIEW_CHANGED",) and not destination.exists()
    result = wire(run(selected, "programme.author", **values, expected_review_sha256=report["review_sha256"]))
    assert result["report"]["authoring_dir"] == str(destination)
    assert (destination / PROGRAMME_DESCRIPTOR_FILENAME).read_bytes() == _descriptor().canonical_bytes()
    assert [name for name, _ in selected.calls] == ["prepare", "prepare", "prepare", "author"]


def test_worker_selection_reuses_the_original_exact_profile_boundary(selected):
    selected.context = replace(selected.context, maximum_parallel_tasks=selected.context.maximum_parallel_tasks + 1)
    result = run(selected, "programme.review", directory=str(selected.directory), action="RUN")
    assert result.reason_codes == ("OWNER_CONTRACT_REFUSED",) and selected.calls == []
