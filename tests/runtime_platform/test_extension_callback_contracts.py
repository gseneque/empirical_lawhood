# SPDX-License-Identifier: MPL-2.0
"""Small disclosed callback fixtures; no sources, runners or scientific evidence."""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from typing import get_args, get_type_hints

import pytest

from empirical_lawhood.api import experiment_scientific_read as reads
from empirical_lawhood.execution import experiment_callbacks, recursive_callbacks
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.execution.recursive_provider import require_recursive_input_supplier


def forbidden(*_args, **_kwargs):
    pytest.fail("a callback contract check reached an input source or native runner")


def test_callback_api_negotiation_refuses_incompatible_and_invalid_ranges():
    from empirical_lawhood.execution.extension_api import require_extension_callback_api

    assert require_extension_callback_api(minimum="1.0.0", maximum_exclusive="2.0.0") == "1.0.0"
    for lower, upper in (("1.0.1", "2.0.0"), ("0.1.0", "1.0.0"), ("2.0.0", "1.0.0"),
                         ("1.0.0", "1.0.0"), ("1.0.0-guess", "2.0.0"), (None, "2.0.0")):
        with pytest.raises((TypeError, ValueError)):
            require_extension_callback_api(minimum=lower, maximum_exclusive=upper)


def _read(monkeypatch, hook, result):
    binding = SimpleNamespace(**{hook: lambda **_context: result})
    monkeypatch.setattr(reads, "_development_runtime_context", lambda **_context: (binding, None, None))
    context = dict(directory=None, artifact_writer=None, payloads={}, draft=None, plan=None)
    if hook == "read_development_result":
        return reads.read_prepared_development_science(**context, report={}, products={})
    return reads.complete_prepared_development_science(**context, project_root=None,
        maximum_parallel_tasks=1, scheduler_result=None)


@pytest.mark.parametrize("hook", ("read_development_result", "complete_development_result"))
@pytest.mark.parametrize("result", (None, True, {1: "invalid-key"}))
def test_development_hook_rejects_invalid_return_at_its_actual_dispatch(monkeypatch, hook, result):
    with pytest.raises(TypeError, match=hook + " must return a report mapping"):
        _read(monkeypatch, hook, result)


@pytest.mark.parametrize("hook", ("read_development_result", "complete_development_result"))
def test_reports_preserve_exact_values_and_independent_status_axes(monkeypatch, hook):
    report = {"status": "SUCCEEDED", "inquiry_outcome": "useful-supply", "claim": "UNEVALUABLE",
              "qualification": "NOT_ESTABLISHED", "decimal": Decimal("0.123456789012345678901234567890"),
              "denominator": ("unit.positive", "unit.adverse", "unit.missing")}
    assert _read(monkeypatch, hook, report) is report


def test_registered_product_export_returns_a_report_without_a_new_effect(monkeypatch):
    from pathlib import Path
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService

    service = ExperimentProgrammeService(Path('/disclosed-source'), None)
    for value in (None, {"claim": "UNEVALUABLE", "new_native_contacts": 0}):
        composite = SimpleNamespace(export_products=lambda **_kwargs: value)
        monkeypatch.setattr(ExperimentProgrammeService, '_composite_programme', lambda *_args, **_kwargs: composite)
        if value is None:
            with pytest.raises(TypeError, match='programme.export_products must return a report mapping'):
                service.export_products(directory=None, selection_path=None)
        else:
            assert service.export_products(directory=None, selection_path=None) is value


@pytest.mark.parametrize("result", (None, {1: "invalid-key"}, {"claim": "UNEVALUABLE"}))
def test_prospective_reader_checks_return_without_replacing_current_access(monkeypatch, result):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
    from empirical_lawhood.science.identity.provenance import ObjectIdentity

    pin = ObjectIdentity("spec.fixture", "empirical-lawhood/fixture/spec", "1.0.0", "a" * 64)
    calls = []
    def current():
        calls.append("access")
    selected = SimpleNamespace(instance=SimpleNamespace(specification=pin),
        original_input_access=SimpleNamespace(require_current=current))
    binding = ExperimentRuntimeBinding("protocol.callback-fixture", forbidden,
        read_result=lambda **_kwargs: result, specification_schema=pin.object_schema)
    monkeypatch.setattr(generated, "EXPERIMENT_SPECIFICATION_PROTOCOLS",
        ((pin.object_schema, pin.object_version, binding.protocol_id),))
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    if result == {"claim": "UNEVALUABLE"}:
        assert reads.read_prepared_experiment_science(selected=selected, artifact_writer=None, run_id="fixture") is result
    else:
        with pytest.raises(TypeError, match="read_result must return a report mapping"):
            reads.read_prepared_experiment_science(selected=selected, artifact_writer=None, run_id="fixture")
    assert calls == ["access", "access"]


def test_runtime_binder_rejects_wrong_supplier_before_contact(monkeypatch):
    from empirical_lawhood.api import experiment_preparation as preparation
    from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
    from empirical_lawhood.api.recursive_execution import _development_runtime_supplier
    from tests.runtime_platform.test_experiment_runtime_bindings import protocol
    from tests.runtime_platform.test_recursive_compiler import Config

    declared = replace(protocol(), requires_development_runtime_binding=True)
    config = Config("configuration.callback-fixture", 1)
    monkeypatch.setattr(preparation, "experiment_protocols", lambda: (declared,))
    payloads = {"experiment-instance.json": b"disclosed dispatch fixture",
                "experiment-specification.json": config.canonical_bytes()}
    for value in (None, object(), SimpleNamespace(resolve_input=lambda *, typo: None)):
        binding = ExperimentRuntimeBinding(declared.protocol_id, None,
            bind_development_runtime=lambda **_kwargs: value)
        monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
        with pytest.raises(TypeError, match="recursive input supplier"):
            _development_runtime_supplier(directory=None, writer=None, plan=None, payloads=payloads,
                supplier=SimpleNamespace(resolve_input=forbidden), output_codecs={})
    supplier = SimpleNamespace(resolve_input=forbidden)
    assert require_recursive_input_supplier(supplier) is supplier


def test_invalid_inquiry_validator_verdict_is_not_treated_as_another_scope(monkeypatch):
    from empirical_lawhood.api import recursive_operations
    from empirical_lawhood.api.recursive_inquiry import _validate_wave_endpoint
    from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification

    draft = SimpleNamespace(operations=(SimpleNamespace(node_id="node", selection=SimpleNamespace(selection_id="selected")),),
        selected_operation_ids=("node",))
    calls = []
    def invalid(*_args):
        calls.append("validator")
        return True
    factory = SimpleNamespace(registration=SimpleNamespace(selection=SimpleNamespace(selection_id="selected")),
        inquiry_endpoint_validator=invalid)
    monkeypatch.setattr(recursive_operations, "selected_operation_factories", lambda _ids: (factory,))
    for robust in (False, True):
        # A disclosed dispatch-only value: no canonical claim or scientific
        # assessment is constructed or authenticated by this fixture.
        specification = object.__new__(RobustInquirySpecification) if robust else SimpleNamespace(endpoint=None)
        if robust:
            object.__setattr__(specification, "requirements", (SimpleNamespace(scope=None), SimpleNamespace(scope=None)))
        with pytest.raises(TypeError, match="endpoint validator must return None"):
            _validate_wave_endpoint(draft, specification, {})
    assert calls == ["validator", "validator"]


def test_all_experiment_hooks_have_named_callback_contracts_and_exact_signatures():
    import inspect

    contracts = get_type_hints(ExperimentRuntimeBinding)
    fields = {name: annotation for name, annotation in contracts.items()
              if any(getattr(kind, "__module__", None) == experiment_callbacks.__name__
                     for kind in get_args(annotation))}
    assert len(fields) == 19
    for annotation in fields.values():
        for kind in get_args(annotation):
            if kind is type(None):
                continue
            signature = inspect.signature(kind.__call__)
            assert signature.return_annotation is not inspect.Signature.empty
            assert not any(parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
                           for parameter in signature.parameters.values())
    from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks, RecursiveScientificHooks
    for declaration in (RecursiveInquiryHooks, RecursiveScientificHooks):
        for annotation in get_type_hints(declaration).values():
            assert "typing.Callable" not in str(annotation)
    assert recursive_callbacks.InquiryEndpointValidator.__call__.__annotations__["return"] == "None"
