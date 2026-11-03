# SPDX-License-Identifier: MPL-2.0
"""Registered composite routing is a selector, never component authority."""

from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import composite_experiment_programme as owner
from empirical_lawhood.api import experiment_preparation as preparation_owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.infrastructure.artifact_stream_primitives import ExternalRootUnavailable
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from empirical_lawhood.runtime.experiment_programme import (
    PROGRAMME_DESCRIPTOR_FILENAME, ExperimentProgrammeDescriptor,
)
from tests.test_recursive_public_service import _plane


@dataclass(frozen=True, slots=True)
class SoftwareSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/composite-specification"
    record_id: str = "fixture.specification"


@dataclass(frozen=True, slots=True)
class SoftwareProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/composite-programme"
    record_id: str = "fixture.programme"


def _installed(monkeypatch, factory):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as installed

    declaration = ExperimentProtocolDeclaration(
        protocol_id="fixture.composite", specification_type=SoftwareSpecification,
        prepare=lambda *args, **kwargs: None, consumer_id="fixture-composite",
        programme_record_type=SoftwareProgramme)
    monkeypatch.setattr(preparation_owner, "experiment_protocols", lambda: (declaration,))
    monkeypatch.setattr(installed, "EXPERIMENT_RUNTIME_BINDINGS", (
        ExperimentRuntimeBinding("fixture.composite", bind_handoff=None, programme_service_factory=factory),))
    return declaration


def _descriptor():
    return ExperimentProgrammeDescriptor("fixture.descriptor", "fixture.composite",
        ObjectIdentity.from_record("fixture.specification", SoftwareSpecification()),
        ObjectIdentity.from_record("fixture.programme", SoftwareProgramme()))


def _service(tmp_path):
    plane = _plane(tmp_path / "custody")
    directory = Path(plane.root.contract.canonical_path) / "programme"
    directory.mkdir()
    return ExperimentProgrammeService(Path("/unused"), plane,
        SimpleNamespace(maximum_parallel_tasks=4)), directory


def _lifecycle(calls):
    def method(name):
        def selected(**kwargs):
            calls.append((name, kwargs))
            return {"lifecycle": name}
        return selected
    return SimpleNamespace(**{name: method(name) for name in ("author", "run", "read", "recover")})


def test_descriptor_is_closed_canonical_guarded_and_cannot_be_overwritten(tmp_path, monkeypatch):
    calls = []
    selected = _lifecycle(calls)
    _installed(monkeypatch, lambda **kwargs: selected)
    service, directory = _service(tmp_path)
    descriptor = _descriptor()
    owner.write_experiment_programme_descriptor(service=service, directory=directory, descriptor=descriptor)
    path = directory / PROGRAMME_DESCRIPTOR_FILENAME
    assert path.read_bytes() == descriptor.canonical_bytes()
    assert owner.selected_composite_programme_service(service=service, directory=directory) is selected
    with pytest.raises(ValueError):
        owner.write_experiment_programme_descriptor(service=service, directory=directory, descriptor=descriptor)
    assert path.read_bytes() == descriptor.canonical_bytes() and calls == []


@pytest.mark.parametrize("damage", ("malformed", "noncanonical", "symlink", "oversize",
    "foreign-protocol", "foreign-specification-revision", "foreign-plan-revision"))
def test_present_damaged_descriptor_refuses_before_owner_or_single_run_fallback(tmp_path, monkeypatch, damage):
    entered = []
    _installed(monkeypatch, lambda **kwargs: entered.append(kwargs))
    service, directory = _service(tmp_path)
    descriptor = _descriptor()
    payload = descriptor.canonical_bytes()
    if damage == "malformed":
        payload = b"{}"
    elif damage == "noncanonical":
        payload += b"\n"
    elif damage == "oversize":
        payload = b" " * (64 * 1024 + 1)
    elif damage == "foreign-protocol":
        payload = replace(descriptor, protocol_id="fixture.foreign").canonical_bytes()
    elif damage == "foreign-specification-revision":
        payload = replace(descriptor, specification=replace(descriptor.specification,
            object_version="2.0.0")).canonical_bytes()
    elif damage == "foreign-plan-revision":
        payload = replace(descriptor, programme=replace(descriptor.programme,
            object_version="2.0.0")).canonical_bytes()
    path = directory / PROGRAMME_DESCRIPTOR_FILENAME
    if damage == "symlink":
        target = tmp_path / "outside.json"
        target.write_bytes(payload)
        path.symlink_to(target)
    else:
        path.write_bytes(payload)
    monkeypatch.setattr(ExperimentProgrammeService, "_is_prospective",
        lambda *args: pytest.fail("present malformed descriptor fell through to single-run custody"))
    with pytest.raises((ValueError, TypeError, OSError, ExternalRootUnavailable, BoundedFileIOError)):
        service.read(directory=directory)
    assert entered == []


def test_descriptor_outside_selected_guarded_root_refuses_before_owner(tmp_path, monkeypatch):
    entered = []
    _installed(monkeypatch, lambda **kwargs: entered.append(kwargs))
    service, _ = _service(tmp_path)
    directory = tmp_path / "outside"
    directory.mkdir()
    (directory / PROGRAMME_DESCRIPTOR_FILENAME).write_bytes(_descriptor().canonical_bytes())
    with pytest.raises(ValueError):
        service.read(directory=directory)
    assert entered == []


@pytest.mark.parametrize("method", ("run", "recover", "read"))
def test_public_lifecycle_forwards_explicit_component_selection_and_profile_workers(tmp_path, monkeypatch, method):
    calls, factories = [], []
    selected = _lifecycle(calls)
    def factory(**kwargs):
        factories.append(kwargs)
        return selected
    _installed(monkeypatch, factory)
    service, directory = _service(tmp_path)
    descriptor = _descriptor()
    owner.write_experiment_programme_descriptor(service=service, directory=directory, descriptor=descriptor)
    request_path = tmp_path / "selected-component-authorities.json"
    options = {"programme_request_path": request_path}
    if method != "read":
        options["confirmed"] = True
    assert getattr(service, method)(directory=directory, **options) == {"lifecycle": method}
    assert factories == [{"service": service, "descriptor": descriptor}]
    expected = {"directory": directory, "programme_request_path": request_path}
    if method == "read":
        expected["allow_partial"] = False
    else:
        expected.update(maximum_parallel_tasks=4, confirmed=True)
    assert calls == [(method, expected)]


def test_descriptor_does_not_replace_component_execution_or_reveal_authority(tmp_path, monkeypatch):
    calls = []
    def refuse(**kwargs):
        calls.append(kwargs)
        raise PermissionError("component original issue and reveal selections are missing")
    selected = _lifecycle([])
    selected.run = refuse
    _installed(monkeypatch, lambda **kwargs: selected)
    service, directory = _service(tmp_path)
    owner.write_experiment_programme_descriptor(service=service, directory=directory, descriptor=_descriptor())
    with pytest.raises(PermissionError, match="original issue"):
        service.run(directory=directory, confirmed=True)
    assert len(calls) == 1 and calls[0]["programme_request_path"] is None


@pytest.mark.parametrize("method", ("run", "recover", "read"))
def test_composite_options_are_disjoint_from_single_campaign_authority(tmp_path, monkeypatch, method):
    calls = []
    _installed(monkeypatch, lambda **kwargs: _lifecycle(calls))
    service, directory = _service(tmp_path)
    owner.write_experiment_programme_descriptor(service=service, directory=directory, descriptor=_descriptor())
    with pytest.raises(ValueError, match="single-campaign"):
        getattr(service, method)(directory=directory, request=object())
    assert calls == []


@pytest.mark.parametrize("missing", ("plan", "factory"))
def test_composition_requires_matching_domain_plan_and_api_service(tmp_path, monkeypatch, missing):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as installed

    declaration = _installed(monkeypatch, lambda **kwargs: _lifecycle([]))
    service, directory = _service(tmp_path)
    if missing == "plan":
        monkeypatch.setattr(preparation_owner, "experiment_protocols",
            lambda: (replace(declaration, programme_record_type=None),))
    else:
        monkeypatch.setattr(installed, "EXPERIMENT_RUNTIME_BINDINGS", ())
    with pytest.raises(ValueError):
        owner.write_experiment_programme_descriptor(service=service, directory=directory,
            descriptor=_descriptor())
    assert not (directory / PROGRAMME_DESCRIPTOR_FILENAME).exists()


def test_composite_api_service_cannot_also_select_an_independent_component_lifecycle():
    with pytest.raises(TypeError, match="separate code-owned"):
        ExperimentRuntimeBinding("fixture.composite", bind_handoff=lambda: None,
            programme_service_factory=lambda **kwargs: _lifecycle([]))



def test_absent_descriptor_preserves_existing_single_run_selection(tmp_path):
    service, directory = _service(tmp_path)
    assert owner.selected_composite_programme_service(service=service, directory=directory) is None
