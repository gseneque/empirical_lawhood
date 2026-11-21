# SPDX-License-Identifier: MPL-2.0
"""Disclosed R16-base fixtures; no source, native task or scientific authority."""

from dataclasses import dataclass, replace
from decimal import Decimal
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api.extension_conformance import run_extension_conformance
from empirical_lawhood.science.experiments.experimental_design import UnitAllocation
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.artifacts import ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityRegistry
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection, ExperimentCensus, ExperimentInstanceBinding, ExperimentPreparation, ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceCase, ConformanceProfile, ExtensionConformanceSelection, inspect_extension_contracts
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration
from empirical_lawhood.execution.native_effects import NativeEffectContact
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from tests.runtime_platform.test_recursive_compiler import Config, SourceConfig, UseConfig, fixture


def forbidden(*_args, **_kwargs):
    raise AssertionError("conformance attempted source or runner contact")


@dataclass(frozen=True, slots=True)
class Specification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/generic/conformance-specification"
    specification_id: str = "generic.disclosed"

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def selected():
    draft, registered, registry = fixture()
    operations = tuple(RecursiveOperationDeclaration(
        capability_key=row.selection.capability_key, capability_version="1.0.0",
        implementation_id="disclosed-conformance", kind=CapabilityKind.TRANSFORM,
        config_record_type=row.config_record_type, stage=row.stage, input_ports=row.input_ports,
        outputs=row.outputs, permissions=row.required_permissions,
        evidence_ceiling=registry.capabilities[0].maximum_evidence_ceiling,
        outcome_access=row.outcome_access, visibility_ceiling=row.visibility_ceiling,
        resources=row.resource_ceiling, conformance_check_ids=("generic.bounded",),
        runner_factory=forbidden, record_codecs={Config.SCHEMA: Config},
        implementation_sha256=row.selection.implementation_sha256,
    ) for row in registered)
    selection = ExtensionConformanceSelection("generic", "empirical-lawhood/generic/", operations,
        imported_record_types=(Config, SourceConfig, UseConfig))
    return selection, draft


def install_protocol(monkeypatch, selection, *, prepare=None, reader=None):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as runtime
    import empirical_lawhood.api.generated_experiment_protocols as static
    from empirical_lawhood.api import experiment_preparation

    def default_prepare(specification, *, scientific_inputs, execution, protocol_bytes):
        return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0), ())
    protocol = ExperimentProtocolDeclaration("generic.protocol", Specification, prepare or default_prepare,
        "generic.consumer", validate_instance=lambda **_kwargs: None)
    binding = ExperimentRuntimeBinding(protocol.protocol_id, None,
        read_development_result=reader or (lambda **_kwargs: {}), specification_schema=Specification.SCHEMA)
    monkeypatch.setattr(static, "EXPERIMENT_PROTOCOL_DECLARATIONS", (protocol,))
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", lambda: (protocol,))
    monkeypatch.setattr(runtime, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    monkeypatch.setattr(runtime, "EXPERIMENT_SPECIFICATION_PROTOCOLS",
        ((Specification.SCHEMA, Specification.VERSION, protocol.protocol_id),))
    return replace(selection, protocols=(protocol,), bindings=(binding,))


def execute(selection):
    return run_extension_conformance(selection, source={"fixture": "disclosed-test-only"})


def test_static_preflight_rejects_wrong_keyword_before_any_callback(monkeypatch):
    selection, _ = selected()
    calls = []
    def prepare(specification, *, scientific_inputs, executon, protocol_bytes):
        calls.append("entered")
    selection = install_protocol(monkeypatch, selection, prepare=prepare)
    report = execute(selection)
    assert report["status"] == "FAILED"
    assert "prepare" in report["failure"]["message"]
    assert not calls and not report["checks"]


@pytest.mark.parametrize("damage", ("namespace", "schema", "absent-reader", "native", "profile"))
def test_invalid_contracts_refuse_before_runner(damage):
    selection, _ = selected()
    if damage == "namespace":
        selection = replace(selection, namespace="other")
    elif damage == "schema":
        class ConflictingConfig(Config):
            pass
        selection = replace(selection, imported_record_types=(*selection.imported_record_types, ConflictingConfig))
    elif damage == "absent-reader":
        protocol = ExperimentProtocolDeclaration("generic.protocol", Specification,
            lambda specification, **_kwargs: None, "generic.consumer")
        selection = replace(selection, protocols=(protocol,), profile=ConformanceProfile.ORDINARY_DEVELOPMENT,
            cases=(ConformanceCase("generic.prepare", ConformanceCall.PREPARE, {"specification": Specification()}, None),))
    elif damage == "native":
        operation = selection.operations[0]
        # A network prerequisite selects a profile which base must not advertise.
        operation = replace(operation, execution_properties=replace(operation.execution_properties, requires_network=True))
        selection = replace(selection, operations=(operation, *selection.operations[1:]))
    else:
        selection = replace(selection, profile="continuing-source")
    report = execute(selection)
    assert report["status"] == "FAILED" and report["checks"] == []
    assert report["contact_attempts"] == []


def test_wrong_preparation_return_refuses_at_public_owner(monkeypatch):
    selection, _ = selected()
    selection = install_protocol(monkeypatch, selection, prepare=lambda specification, **_kwargs: True)
    case = ConformanceCase("generic.wrong-return", ConformanceCall.PREPARE,
        {"specification": Specification(), "execution": ExecutionSelection(workers=1)},
        "ValueError", "preparation contract")
    report = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=(case,)))
    assert report["status"] == "PASSED_SELECTED_CHECKS"
    assert report["checks"][1]["status"] == "PASSED_EXPECTED_REFUSAL"
    assert report["checks"][1]["call_site"].endswith("prepare_experiment")


def test_actual_development_read_preserves_independent_axes_and_refuses_wrong_return(monkeypatch):
    selection, draft = selected()
    original = {"status": "SUCCEEDED", "inquiry_outcome": "useful-supply", "claim": "UNEVALUABLE",
        "qualification": "NOT_ESTABLISHED", "denominator": ["positive", "adverse", "missing"],
        "decimal": Decimal("0.123456789012345678901234567890"), "connections": ()}
    returned = [original]
    selection = install_protocol(monkeypatch, selection, reader=lambda **_kwargs: returned[0])
    spec = Specification()
    instance = ExperimentInstanceBinding(spec.identity,
        ObjectIdentity("disclosed.allocation", UnitAllocation.SCHEMA, UnitAllocation.VERSION, "a" * 64),
        ObjectIdentity.from_record(draft.draft_id, draft),
        ObjectIdentity("disclosed.projection", "empirical-lawhood/testing/projection", "1.0.0", "b" * 64),
        ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign))
    arguments = dict(directory=None, artifact_writer=None, payloads={
        "experiment-instance.json": instance.canonical_bytes(), "experiment-specification.json": spec.canonical_bytes()},
        report={}, products={}, draft=draft, plan=None)
    case = ConformanceCase("generic.read", ConformanceCall.DEVELOPMENT_READ, arguments, original)
    report = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=(case,)))
    assert report["status"] == "PASSED_SELECTED_CHECKS", report
    assert report["checks"][1]["observed"]["report"] == original
    assert report["qualification"] == "NOT_ESTABLISHED" and not report["full_installed_lifecycle"]
    returned[0] = True
    case = replace(case, expected="TypeError", refusal_contains="must return a report mapping")
    refused = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=(case,)))
    assert refused["status"] == "PASSED_SELECTED_CHECKS", refused


def test_complete_output_census_uses_the_real_publication_boundary():
    selection, draft = selected()
    registrations = tuple(row.registration() for row in selection.operations)
    registry = CapabilityRegistry("generic.registry", tuple(row.manifest() for row in selection.operations))
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="a" * 40, output_codecs={Config.SCHEMA: Config})
    task = compiled.execution_plan.tasks[0]
    result = RunnerResult((), (ReceiptCheck("generic.check", True, ()),))
    case = ConformanceCase("generic.incomplete", ConformanceCall.OUTPUT_CENSUS,
        dict(task=task, result=result), "SchedulerConsistencyError", "output ports differ")
    complete = replace(case, case_id="generic.complete", expected=None, refusal_contains=None,
        arguments=dict(task=task, result=replace(result, outputs=tuple(
            TaskOutputPayload(output.output_id, Config("disclosed.result", 1).canonical_bytes()) for output in task.outputs))))
    report = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=(case, complete)))
    assert report["status"] == "PASSED_SELECTED_CHECKS", report
    assert report["checks"][1]["call_site"].endswith("validate_runner_output_contract")


def test_unmet_prerequisite_is_not_a_passing_or_executed_fixture():
    selection, _ = selected()
    report = execute(replace(selection, unmet_prerequisites=("installed starter acceptance pending",)))
    assert report["status"] == "PREREQUISITES_UNMET"
    assert len(report["checks"]) == 1


def test_contact_guard_fails_even_when_callback_swallows_the_refusal(monkeypatch):
    import subprocess
    selection, _ = selected()
    def prepare(specification, **_kwargs):
        try:
            subprocess.Popen(["should-never-start"])
        except PermissionError:
            pass
        return True
    selection = install_protocol(monkeypatch, selection, prepare=prepare)
    case = ConformanceCase("generic.contact", ConformanceCall.PREPARE, {"specification": Specification()},
        "ValueError", "preparation contract")
    report = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=(case,)))
    assert report["status"] == "FAILED"
    assert report["checks"][1]["status"] == "FAILED_CONTACT_ATTEMPT"
    assert report["contact_attempts"] == ["subprocess.Popen"]


def test_static_signature_validation_does_not_construct_provider():
    selection, _ = selected()
    report = inspect_extension_contracts(selection)
    assert len(report["operations"]) == 2 and report["executed_callbacks"] == 0


def test_fixture_argument_typo_prevents_all_execution(monkeypatch):
    selection, _ = selected()
    selection = install_protocol(monkeypatch, selection)
    valid = ConformanceCase("generic.first", ConformanceCall.PREPARE, {"specification": Specification()}, None)
    invalid = replace(valid, case_id="generic.second", arguments={"specfication": Specification()})
    report = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=(valid, invalid)))
    assert report["status"] == "FAILED" and len(report["checks"]) == 1


def test_runtime_binding_to_wrong_protocol_is_not_substituted(monkeypatch):
    selection, _ = selected()
    selection = install_protocol(monkeypatch, selection)
    selection = replace(selection, bindings=(replace(selection.bindings[0], protocol_id="generic.other"),))
    assert execute(selection)["status"] == "FAILED"


def test_compiler_and_strict_codec_keep_an_absent_scientific_connection_absent():
    selection, draft = selected()
    draft = replace(draft, requirements=(), connections=(), suppliers=(), links=(), selected_operation_ids=("source",))
    arguments = dict(draft=draft, registrations=tuple(row.registration() for row in selection.operations),
        registry=CapabilityRegistry("generic.registry", tuple(row.manifest() for row in selection.operations)),
        implementation_commit="a" * 40, output_codecs={Config.SCHEMA: Config})
    expected = compile_recursive_wave(**arguments)
    record = Config("generic.original", 3)
    cases = (ConformanceCase("generic.codec", ConformanceCall.CODEC_ROUNDTRIP,
                dict(record=record, codec=Config), record),
             ConformanceCase("generic.compile", ConformanceCall.COMPILE, arguments, expected))
    report = execute(replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT, cases=cases))
    assert report["status"] == "PASSED_SELECTED_CHECKS", report
    assert expected.draft.connections == () and expected.requirement_bindings == ()


@dataclass(frozen=True)
class DisclosedNativeContext:
    input_ports: tuple = ()
    prepared_invocation: object = None


def native_selection(callback=None):
    """No input grant or task execution; the anticipated parent is unpublished."""
    selection, _ = selected()
    parent = NativeEffectContact("exposed.run", "exposed.task", "exposed.attempt",
        ObjectIdentity("exposed.plan", "empirical-lawhood/testing/plan", "1.0.0", "a" * 64),
        ObjectIdentity("exposed.task", "empirical-lawhood/testing/task", "1.0.0", "b" * 64),
        "c" * 40, (), ())
    expected = PreparedNativeWork(parent, ("exposed.unit",), ("exposed.slot",))
    def prepare(*, runner, context, expected_parent):
        return expected
    callback = callback or prepare
    original = selection.operations[0]
    operation = replace(original, execution_properties=replace(original.execution_properties,
        native_effect=True, complete_unit_census=True, native_work_preparer=callback))
    case = ConformanceCase("generic.native-preparation", ConformanceCall.NATIVE_PREPARE,
        dict(callback=callback, runner=SimpleNamespace(manifest=operation.manifest()),
            context=DisclosedNativeContext(), expected_parent=parent), expected)
    return replace(selection, operations=(operation,),
        profile=ConformanceProfile.ISOLATED_NATIVE_CONTRACTS, cases=(case,))


def test_native_profile_uses_existing_pure_preparation_and_checks_return():
    report = execute(native_selection())
    assert report["status"] == "PASSED_SELECTED_CHECKS", report
    assert report["checks"][1]["call_site"].endswith("execution._prepare_native_work")
    assert not report["contact_attempts"] and not report["full_installed_lifecycle"]
    selection = native_selection(lambda *, runner, context, expected_parent: True)
    case = replace(selection.cases[0], expected="ValueError", refusal_contains="exact typed anticipated effect scope")
    assert execute(replace(selection, cases=(case,)))["status"] == "PASSED_SELECTED_CHECKS"


@pytest.mark.parametrize("damage", ("wrong-keyword", "ordinary-profile", "missing-preparer", "incomplete-census",
    "network", "substitute-callback", "substitute-manifest", "bound-context"))
def test_native_profile_refuses_incompatible_selection_before_callback(damage):
    calls = []
    def prepare(*, runner, context, expected_parent):
        calls.append("entered")
    selection = native_selection(prepare)
    operation = selection.operations[0]
    properties = operation.execution_properties
    case = selection.cases[0]
    if damage == "wrong-keyword":
        properties = replace(properties, native_work_preparer=lambda *, runner, context, expected_parnt: None)
    elif damage == "ordinary-profile":
        selection = replace(selection, profile=ConformanceProfile.ORDINARY_DEVELOPMENT)
    elif damage == "missing-preparer":
        properties = replace(properties, native_work_preparer=None)
    elif damage == "incomplete-census":
        properties = replace(properties, complete_unit_census=False)
    elif damage == "network":
        properties = replace(properties, requires_network=True)
    elif damage == "substitute-callback":
        case = replace(case, arguments={**case.arguments, "callback": forbidden})
    elif damage == "substitute-manifest":
        case = replace(case, arguments={**case.arguments, "runner": SimpleNamespace(manifest=None)})
    else:
        case = replace(case, arguments={**case.arguments, "context": DisclosedNativeContext(prepared_invocation=True)})
    selection = replace(selection, operations=(replace(operation, execution_properties=properties),), cases=(case,))
    report = execute(selection)
    assert report["status"] == "FAILED", report
    assert not calls and not report["contact_attempts"]


def test_native_profile_requires_native_operation_and_keeps_contact_guards():
    selection, _ = selected()
    codec = Config
    original = codec("generic.disclosed", 3)
    case = ConformanceCase("generic.codec", ConformanceCall.CODEC_ROUNDTRIP,
        dict(record=original, codec=codec), original)
    refused = execute(replace(selection, profile=ConformanceProfile.ISOLATED_NATIVE_CONTRACTS, cases=(case,)))
    assert refused["status"] == "FAILED" and "selected native operation" in refused["failure"]["message"]
    def prepare(*, runner, context, expected_parent):
        import subprocess
        try:
            subprocess.Popen(["must-not-enter"])
        except PermissionError:
            pass
        return PreparedNativeWork(expected_parent, ("exposed.unit",), ("exposed.slot",))
    report = execute(native_selection(prepare))
    assert report["status"] == "FAILED"
    assert report["checks"][1]["status"] == "FAILED_CONTACT_ATTEMPT"
    assert report["contact_attempts"] == ["subprocess.Popen"]
