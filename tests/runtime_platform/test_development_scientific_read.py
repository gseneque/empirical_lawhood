# SPDX-License-Identifier: MPL-2.0
"""Generic DEV dispatch controls; actual PURE lifecycle, no native or authority."""
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.adapters.composition import generated_extension_bundles as installed
from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import supply_draft
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.api import experiment_preparation
from empirical_lawhood.api import experiment_scientific_read as owner
from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding, validate_experiment_runtime_binding
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding, ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from tests.test_recursive_public_service import _plane
from tests.test_recursive_report_projection import wave as wave

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class _Specification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/development-read-specification"
    record_id: str

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


class _PoisonProducts:
    def __getattribute__(self, name):
        raise AssertionError("dispatch read scientific products: " + name)

    def __getitem__(self, key):
        raise AssertionError("dispatch opened scientific products: " + str(key))


class _Payloads(dict):
    def __getitem__(self, name):
        self.reads.append(name)
        return super().__getitem__(name)


def _source_draft():
    source = decode_canonical_bytes((ROOT / "programmes/materials/superconductivity/workflows/electron-gas-response/config.json").read_bytes(),
        UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
    return source, supply_draft(source, draft_id="draft.development-read-control")


def _forbidden(*args, **kwargs):
    raise AssertionError("retained dispatch entered current preparation, compiler, provider or science")


@pytest.fixture
def context(monkeypatch):
    _, draft = _source_draft()
    specification = _Specification("specification.development-read-control")
    declaration = ExperimentProtocolDeclaration("protocol.development-read-control", _Specification,
        _forbidden, "consumer.development-read-control")
    # Dispatch controls authenticate canonical association pins only. Allocation,
    # source and projection custody remain the common loader's separate proof.
    instance = ExperimentInstanceBinding(specification.identity,
        ObjectIdentity("allocation.dispatch-control", UnitAllocation.SCHEMA, UnitAllocation.VERSION, "a" * 64),
        ObjectIdentity.from_record(draft.draft_id, draft),
        ObjectIdentity("recursive-member.scientific-projection", RecursiveScientificSelection.SCHEMA,
            RecursiveScientificSelection.VERSION, "b" * 64),
        ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign))
    payloads = _Payloads({"experiment-specification.json": specification.canonical_bytes(),
        "experiment-instance.json": instance.canonical_bytes()})
    payloads.reads = []
    calls = []
    def read(**kwargs):
        calls.append(kwargs)
        return {"scientific_completion": "DISPATCH_CONTROL_DEFERRED" if kwargs["allow_partial"] else "DISPATCH_CONTROL_ONLY"}
    binding = ExperimentRuntimeBinding(declaration.protocol_id, None, read_development_result=read,
        specification_schema=_Specification.SCHEMA)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    monkeypatch.setattr(generated, "EXPERIMENT_SPECIFICATION_PROTOCOLS", ((_Specification.SCHEMA,
        _Specification.VERSION, declaration.protocol_id),))
    monkeypatch.setattr(installed, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", _forbidden)
    arguments = dict(directory="authenticated-directory", artifact_writer="authenticated-writer",
        payloads=payloads, report={"status": "SUCCEEDED"}, products=_PoisonProducts(), draft=draft, plan=object())
    return SimpleNamespace(specification=specification, instance=instance, declaration=declaration,
        binding=binding, calls=calls, arguments=arguments, payloads=payloads)


@pytest.mark.parametrize("partial", (False, True))
def test_exact_retained_development_dispatch_uses_original_codec_and_same_context(context, partial):
    result = owner.read_prepared_development_science(**context.arguments, allow_partial=partial)
    assert result["scientific_completion"] == ("DISPATCH_CONTROL_DEFERRED" if partial else "DISPATCH_CONTROL_ONLY")
    assert len(context.calls) == 1
    actual, = context.calls
    assert actual["specification"] == context.specification and actual["instance"] == context.instance
    for name, value in context.arguments.items():
        assert actual[name] is value
    assert actual["allow_partial"] is partial
    assert context.payloads.reads == ["experiment-instance.json", "experiment-specification.json"]
    assert experiment_runtime_binding(context.declaration) is context.binding


@pytest.mark.parametrize("damage", ("unknown-version", "foreign-specification", "foreign-draft", "foreign-campaign", "codec-version"))
def test_development_dispatch_refuses_edition_or_original_association_changes_before_callback(context, monkeypatch, damage):
    instance = context.instance
    if damage == "unknown-version":
        instance = replace(instance, specification=replace(instance.specification, object_version="99.0.0"))
    elif damage == "foreign-specification":
        context.payloads["experiment-specification.json"] = _Specification("specification.foreign").canonical_bytes()
    elif damage in ("foreign-draft", "foreign-campaign"):
        name = damage.removeprefix("foreign-")
        instance = replace(instance, **{name: replace(getattr(instance, name), object_fingerprint="c" * 64)})
    else:
        @dataclass(frozen=True, slots=True)
        class LaterSpecification(_Specification):
            VERSION: ClassVar[str] = "2.0.0"
        monkeypatch.setattr(installed, "EXPERIMENT_PROTOCOL_DECLARATIONS",
            (replace(context.declaration, specification_type=LaterSpecification),))
    context.payloads["experiment-instance.json"] = instance.canonical_bytes()
    with pytest.raises(ValueError, match="exact installed|original specification/draft/campaign"):
        owner.read_prepared_development_science(**context.arguments)
    assert context.calls == []


def test_unselected_development_read_preserves_old_report_without_reading_specification(context, monkeypatch):
    binding = ExperimentRuntimeBinding(context.declaration.protocol_id, None, export_products=_forbidden)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    context.payloads["experiment-specification.json"] = _PoisonProducts()
    assert owner.read_prepared_development_science(**context.arguments) is None
    assert context.payloads.reads == ["experiment-instance.json"] and context.calls == []
    assert owner.read_prepared_development_science(**{**context.arguments, "payloads": {}}) is None


def test_protected_dispatch_never_calls_development_reader(context):
    selected = SimpleNamespace(instance=context.instance)
    assert owner.read_prepared_experiment_science(selected=selected, artifact_writer="writer", run_id="run.control") is None
    assert context.calls == []


def test_completion_uses_original_context_without_reading_science_or_reloading_packet(context, monkeypatch):
    calls = []
    def complete(**kwargs):
        calls.append(kwargs)
        return {"production": "EXPOSED_PURE_DISPATCH_CONTROL"}
    binding = replace(context.binding, complete_development_result=complete)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    arguments = {name: context.arguments[name] for name in ("directory", "artifact_writer", "payloads", "draft", "plan")}
    arguments["scheduler_result"] = object()
    result = owner.complete_prepared_development_science(**arguments,
        project_root="actual-selected-project", maximum_parallel_tasks=4)
    assert result == {"production": "EXPOSED_PURE_DISPATCH_CONTROL"} and len(calls) == 1
    assert context.calls == []
    actual, = calls
    assert actual["specification"] == context.specification and actual["instance"] == context.instance
    assert all(actual[name] is value for name, value in arguments.items())
    assert actual["project_root"] == "actual-selected-project" and actual["maximum_parallel_tasks"] == 4
    assert context.payloads.reads == ["experiment-instance.json", "experiment-specification.json"]


def test_unselected_completion_does_not_open_specification_or_call_scientific_reader(context):
    context.payloads["experiment-specification.json"] = _PoisonProducts()
    arguments = {name: context.arguments[name] for name in ("directory", "artifact_writer", "payloads", "draft", "plan")}
    arguments["scheduler_result"] = object()
    assert owner.complete_prepared_development_science(**arguments,
        project_root="actual-selected-project", maximum_parallel_tasks=4) is None
    assert context.payloads.reads == ["experiment-instance.json"] and context.calls == []


@pytest.mark.parametrize("damage", ("foreign-draft", "foreign-specification"))
def test_completion_refuses_changed_original_association_before_production(context, monkeypatch, damage):
    calls = []
    binding = replace(context.binding, complete_development_result=lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    if damage == "foreign-draft":
        instance = replace(context.instance, draft=replace(context.instance.draft, object_fingerprint="c" * 64))
        context.payloads["experiment-instance.json"] = instance.canonical_bytes()
    else:
        context.payloads["experiment-specification.json"] = _Specification("specification.foreign").canonical_bytes()
    arguments = {name: context.arguments[name] for name in ("directory", "artifact_writer", "payloads", "draft", "plan")}
    arguments["scheduler_result"] = object()
    with pytest.raises(ValueError, match="original specification/draft/campaign"):
        owner.complete_prepared_development_science(**arguments,
            project_root="actual-selected-project", maximum_parallel_tasks=4)
    assert calls == context.calls == []


def test_completion_requires_its_existing_ordinary_read_owner(context):
    with pytest.raises(TypeError, match="ordinary scientific read owner"):
        replace(context.binding, read_development_result=None, specification_schema=None,
            export_products=_forbidden, complete_development_result=_forbidden)


def test_operational_access_preflight_rechecks_owner_without_opening_products(context, monkeypatch):
    checks, completions = [], []
    access = object()
    def validate(**kwargs):
        checks.append(kwargs)
    binding = replace(context.binding, bind_development_runtime=_forbidden,
        validate_development_read_access=validate, complete_development_result=lambda **kwargs: completions.append(kwargs))
    declaration = replace(context.declaration, requires_development_runtime_binding=True)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
    monkeypatch.setattr(installed, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    arguments = {name: context.arguments[name] for name in ("directory", "artifact_writer", "payloads", "draft", "plan")}
    for _ in range(2):
        assert owner.validate_prepared_development_read_access(**arguments, read_access=access) is None
    assert len(checks) == 2 and context.calls == []
    for actual in checks:
        assert actual["specification"] == context.specification and actual["instance"] == context.instance
        assert actual["read_access"] is access and all(actual[key] is value for key, value in arguments.items())
    owner.read_prepared_development_science(**context.arguments, read_access=access)
    assert len(context.calls) == 1 and context.calls[0]["read_access"] is access
    owner.complete_prepared_development_science(**arguments, read_access=access,
        project_root="actual-selected-project", maximum_parallel_tasks=4, scheduler_result=object())
    assert len(completions) == 1 and completions[0]["read_access"] is access
    assert all(completions[0][key] is value for key, value in arguments.items())


@pytest.mark.parametrize("selection", ("no-owner", "unsupported-owner", "validator-verdict"))
def test_operational_access_cannot_bypass_its_owner_or_reuse_a_verdict(context, monkeypatch, selection):
    arguments = {name: context.arguments[name] for name in ("directory", "artifact_writer", "payloads", "draft", "plan")}
    if selection == "no-owner":
        arguments["payloads"] = {}
    elif selection == "validator-verdict":
        binding = replace(context.binding, bind_development_runtime=_forbidden,
            validate_development_read_access=lambda **_kwargs: object())
        declaration = replace(context.declaration, requires_development_runtime_binding=True)
        monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", (binding,))
        monkeypatch.setattr(installed, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    with pytest.raises(ValueError, match="operational access selection|return None"):
        owner.validate_prepared_development_read_access(**arguments, read_access=object())
    assert context.calls == []


def test_actual_read_refuses_current_access_before_any_scientific_inputs(wave, monkeypatch):
    checks = []
    selected = object()
    def refused(**kwargs):
        checks.append(kwargs)
        assert kwargs["read_access"] is selected
        raise PermissionError("current access was refused by its actual owner")
    monkeypatch.setattr(owner, "validate_prepared_development_read_access", refused)
    monkeypatch.setattr(execution, "_external_inputs", _forbidden)
    monkeypatch.setattr(owner, "read_prepared_development_science", _forbidden)
    with pytest.raises(PermissionError, match="current access was refused"):
        execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane, read_access=selected)
    assert len(checks) == 1


@pytest.mark.parametrize("lifecycle", ("prospective", "composite", "wrong-schema"))
def test_development_reader_cannot_change_its_declared_lifecycle_or_schema(context, lifecycle):
    declaration, binding = context.declaration, context.binding
    if lifecycle == "prospective":
        declaration = replace(declaration, requires_prospective_runtime_binding=True)
    elif lifecycle == "composite":
        declaration = replace(declaration, programme_record_type=_Specification)
    else:
        binding = replace(binding, specification_schema="empirical-lawhood/testing/foreign-specification")
    with pytest.raises(ValueError, match="lifecycle|schema"):
        validate_experiment_runtime_binding(declaration, binding)


@pytest.mark.parametrize("damage", ("missing-schema", "schema-without-reader", "noncallable", "both-readers", "prospective-binder"))
def test_runtime_record_requires_one_code_owned_reader_and_exact_schema(context, damage):
    if damage == "missing-schema":
        changes = {"specification_schema": None}
    elif damage == "schema-without-reader":
        changes = {"read_development_result": None, "export_products": _forbidden}
    elif damage == "noncallable":
        changes = {"read_development_result": object()}
    elif damage == "both-readers":
        changes = {"read_result": _forbidden}
    else:
        changes = {"bind_handoff": _forbidden}
    with pytest.raises((TypeError, ValueError), match="scientific read|code-owned|lifecycle"):
        replace(context.binding, **changes)


def test_actual_pure_complete_read_dispatches_once_with_same_authenticated_objects(wave, monkeypatch):
    reads, calls = [], []
    load, retained = execution.load_authored_wave, execution._retained_plans
    def counted_load(**kwargs):
        reads.append("packet")
        return load(**kwargs)
    def counted_retained(*args):
        reads.append("plan")
        return retained(*args)
    def read(**kwargs):
        calls.append(kwargs)
        return {"scientific_completion": "DISPATCH_CONTROL_ONLY"}
    monkeypatch.setattr(execution, "load_authored_wave", counted_load)
    monkeypatch.setattr(execution, "_retained_plans", counted_retained)
    monkeypatch.setattr(owner, "read_prepared_development_science", read)
    report, products, draft, plan = execution.read_recursive_wave(directory=wave.directory,
        artifact_writer=wave.plane, include_products=True)
    assert report["status"] == "SUCCEEDED" and report["scientific_result"] == {"scientific_completion": "DISPATCH_CONTROL_ONLY"}
    assert reads == ["packet", "plan"] and len(calls) == 1
    actual, = calls
    assert actual["products"] is products and actual["draft"] is draft and actual["plan"] is plan
    assert actual["report"] is report and actual["allow_partial"] is False
    assert actual["payloads"]["draft.json"] == draft.canonical_bytes()


def test_actual_authored_only_partial_read_dispatches_once_without_execution_or_scientific_products(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "author-only-read")
    source, draft = _source_draft()
    selected = Path(plane.root.contract.canonical_path)
    path = selected / "source.json"
    path.write_bytes(source.canonical_bytes())
    directory = selected / "authored"
    author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=directory,
        input_bindings=((draft.external_inputs[0].input_id, path),))
    calls = []
    def read(**kwargs):
        calls.append(kwargs)
        assert kwargs["allow_partial"] is True and kwargs["products"]["records"] == {}
        return {"scientific_completion": "DISPATCH_CONTROL_DEFERRED"}
    monkeypatch.setattr(owner, "read_prepared_development_science", read)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    monkeypatch.setattr(execution, "_provenance", _forbidden)
    monkeypatch.setattr(plane, "write", _forbidden)
    monkeypatch.setattr(plane, "write_stream", _forbidden)
    report, products, actual_draft, plan = execution.read_recursive_wave(directory=directory,
        artifact_writer=plane, include_products=True, terminal_product_format="compact", allow_partial=True)
    assert len(calls) == 1 and report["status"] == "PARTIAL"
    assert report["scientific_result"] == {"scientific_completion": "DISPATCH_CONTROL_DEFERRED"}
    assert calls[0]["draft"] is actual_draft and calls[0]["plan"] is plan
    assert calls[0]["products"] is products and products["records"] == products["receipts"] == {}


@pytest.fixture
def authored_specification(tmp_path, monkeypatch):
    """Actual PURE package with a disclosed test specification association.

    The test declaration checks its exact original records. The common author,
    loader, manifest validation and recursive plan owners remain unmodified.
    """
    source, draft = _source_draft()
    specification = _Specification("specification.single-load-control")
    source_pin = ObjectIdentity.from_record(source.config_id, source)
    allocation = UnitAllocation("allocation.single-load-control", (source_pin,),
        tuple(IndependentUnit(unit, source.config_id, "family.exposed-control", (), True)
            for unit in draft.development_study.assigned_unit_ids),
        tuple(UnitRoleAssignment(unit, "exposed-control") for unit in draft.development_study.assigned_unit_ids))
    def validate_instance(**kwargs):
        assert kwargs == dict(specification=specification, allocation=allocation, draft=draft, source_records=())
    declaration = ExperimentProtocolDeclaration("protocol.single-load-control", _Specification,
        _forbidden, "consumer.single-load-control", validate_instance=validate_instance)
    monkeypatch.setattr(installed, "EXPERIMENT_PROTOCOL_DECLARATIONS", (*installed.EXPERIMENT_PROTOCOL_DECLARATIONS, declaration))
    monkeypatch.setattr(generated, "EXPERIMENT_SPECIFICATION_PROTOCOLS", (*generated.EXPERIMENT_SPECIFICATION_PROTOCOLS,
        (_Specification.SCHEMA, _Specification.VERSION, declaration.protocol_id)))
    plane = _plane(tmp_path / "single-load-control")
    root = Path(plane.root.contract.canonical_path)
    from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot
    mount = next(parent for parent in root.parents if parent.is_mount())
    plane.root = GuardedExternalRoot(replace(plane.root.contract, required_mount_path=str(mount)))
    path = root / "source.json"
    path.write_bytes(source.canonical_bytes())
    directory = root / "authored"
    report = author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=directory,
        input_bindings=((draft.external_inputs[0].input_id, path),),
        experiment_specification=specification, experiment_allocation=allocation)
    return SimpleNamespace(plane=plane, directory=directory, specification=specification, report=report)


def test_matrix_phase_read_authenticates_one_real_packet_and_the_expected_specification(authored_specification, monkeypatch):
    from empirical_lawhood.api import matrix_researcher_programme as matrix
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService

    case = authored_specification
    service = ExperimentProgrammeService(ROOT, case.plane)
    runner = matrix.MatrixResearchProgrammeService(service=service)
    # Only the enclosing programme/selector seam is supplied. Its ordinary
    # child, expected-specification join and complete packet custody are real.
    binding = SimpleNamespace(sources=SimpleNamespace(relative_path="source.json"))
    context = SimpleNamespace(binding=lambda phase: binding,
        bound_specification=lambda selected: (None, case.specification), child_directory=lambda phase: case.directory)
    monkeypatch.setattr(runner, "_phase_scope", lambda *args: nullcontext())
    monkeypatch.setattr(matrix, "load_experiment_inputs", lambda *args, **kwargs: SimpleNamespace(method_inputs=None))
    reads = []
    load = execution.load_authored_wave
    def counted_load(**kwargs):
        reads.append(kwargs["directory"])
        return load(**kwargs)
    monkeypatch.setattr(execution, "load_authored_wave", counted_load)
    monkeypatch.setattr(author, "load_authored_wave", counted_load)
    monkeypatch.setattr(LocalProcessExecutor, "execute", _forbidden)
    report = runner._read_phase(context, "e2")
    assert reads == [case.directory] and report["status"] == "PARTIAL"
    assert report["operational_terminal"] == "ABSENT" and report["new_native_contact_count"] == 0
    assert report["programme"]["next_step"] == "INSPECT_RETAINED_CONTACT_AND_RECOVERY"
    monkeypatch.setattr(owner, "read_prepared_development_science", _forbidden)
    context.bound_specification = lambda selected: (None, _Specification("specification.changed"))
    with pytest.raises(PermissionError, match="original development specification"):
        runner._read_phase(context, "e2")
    assert reads == [case.directory, case.directory]


def test_unexecuted_read_refuses_changed_member_in_an_independent_invocation(authored_specification):
    case = authored_specification
    options = dict(directory=case.directory, artifact_writer=case.plane,
        expected_specification_bytes=case.specification.canonical_bytes(), allow_unexecuted=True)
    assert execution.read_recursive_wave(**options)["operational_terminal"] == "ABSENT"
    path = case.directory / "experiment-specification.json"
    raw = path.read_bytes()
    try:
        path.write_bytes(raw.replace(b"single-load-control", b"changed-load-control"))
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            execution.read_recursive_wave(**options)
    finally:
        path.write_bytes(raw)


def test_unexecuted_read_rechecks_absence_after_its_custody_scope_closes(authored_specification, monkeypatch):
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane

    case = authored_specification
    run_path = case.plane.root.resolve("runs/" + case.report["run_id"], for_write=False)
    original = ExternalArtifactPlane.read_context
    @contextmanager
    def appearing_after_scope(self, *args, **kwargs):
        with original(self, *args, **kwargs) as reading:
            yield reading
        run_path.mkdir(parents=True)
    monkeypatch.setattr(ExternalArtifactPlane, "read_context", appearing_after_scope)
    with pytest.raises(ValueError, match="custody appeared during authored-only inspection"):
        execution.read_recursive_wave(directory=case.directory, artifact_writer=case.plane,
            expected_specification_bytes=case.specification.canonical_bytes(), allow_unexecuted=True)
