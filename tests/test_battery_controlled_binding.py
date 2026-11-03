# SPDX-License-Identifier: MPL-2.0
"""Exposed cold compiler/role controls; unresolved witnesses grant no readiness."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import os
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import controlled_forecast_config as config_owner
from empirical_lawhood.adapters.methods.battery_refined_inquiry import controlled_operation_bindings as binding
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as original
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import recursive_translation as translation
from empirical_lawhood.infrastructure.artifact_stream_primitives import _anonymous_input_descriptor, _PreopenedBoundedReader, _seal_anonymous_input
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_battery_forecast_step_control import selected as control_fixture, config as native_fixture
from tests.test_battery_segmented_graph import stock as stock_fixture

selected = control_fixture
config = native_fixture
stock = stock_fixture


@pytest.fixture
def cold_scope(stock, selected):
    """Unpublished compiler inputs with explicit unresolved scientific witnesses.

    This fixture deliberately does not call build_config or a scientific worker.
    Its fake evidence identities permit testing graph closure only, like the
    existing exposed compiler fixtures. Full actual-input preparation must refuse.
    """
    base = stock.configs[original.node_id("forecast", 0)]
    old, new, control = selected
    new = replace(new, roster_id=old.roster_id)
    control = replace(control, selected_roster=step.identity(new, "roster_id"),
        comparison_budget=replace(control.comparison_budget, selected_roster=step.identity(new, "roster_id")))
    refs = {}
    for role, kind in config_owner.ROLE_TYPES.items():
        refs[role] = ObjectIdentity("unresolved." + role, kind.SCHEMA, kind.VERSION, sha256(role.encode()).hexdigest())
    refs.update({"original-roster": step.identity(old, "roster_id"), "selected-roster": step.identity(new, "roster_id"),
        "control": control.identity, "history-contribution": ObjectIdentity.from_record(stock.parent.contribution_id, stock.parent),
        "history": base.source.diagnostic})
    root = original.development_root(base, study_id="study.exposed-controlled-cold")
    root_refs = {ref.object_id: ref for ref in root.scientific_operands}
    root_refs.update((ref.object_id, ref) for role, ref in refs.items() if role != "original-roster")
    root = replace(root, scientific_operands=tuple(root_refs[key] for key in sorted(root_refs)))
    requirement, connection = translation.requirement_pair(base, stock.parent, stock.parent.products[0])
    node = config_owner.node_id(0)
    requirement = replace(requirement, requirement_id="requirement." + node + ".actual-unknown-history",
        consumer_operation_id=node, assessment_operation_id=node)
    connection = replace(connection, connection_id="connection." + node + ".actual-unknown-history",
        requirement_id=requirement.requirement_id, assessment_operation_id=node, external_input_id="external." + node + ".history")
    config = config_owner.ControlledForecastConfig("config." + node, 0, tuple(sorted(refs.items())), "f" * 64,
        root, requirement, connection)
    declaration = binding.operation_declaration()
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation.exposed-controlled",),
        resource_budget=original.BUDGET, maximum_attempts=1)
    external = tuple(RecursiveExternalInput("external." + node + "." + role, binding.artifact_id(config, role),
        ref.object_schema, original.MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        ref.object_fingerprint, "HISTORY" if role in {"history", "uncertain-work"} else "SOURCE") for role, ref in config.role_bindings)
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.recursive_translation import _campaign
    draft = RecursiveStudyDraft("draft.exposed-controlled-cold", original.QUESTION, _campaign(root, "draft.exposed-controlled-cold"),
        (requirement,), (connection,), (), (operation,), external, binding.input_links(config), (node,),
        development_study=root, contribution_parents=(stock.parent,))
    return SimpleNamespace(config=config, draft=draft, original=old, selected=new, control=control)


def compile_cold(scope, draft=None):
    declaration = binding.operation_declaration()
    return compile_recursive_wave(draft=draft or scope.draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry("registry.exposed-controlled-cold", (declaration.manifest(),)),
        implementation_commit="1" * 40, output_codecs=declaration.record_codecs)


def test_cold_closed_graph_is_one_policy_request_with_complete_original_roles(cold_scope):
    compiled = compile_cold(cold_scope)
    task, = compiled.execution_plan.tasks
    assert len(tuple(row for row in task.scientific_inputs if row.consumer_input_id != "config")) == 27
    configuration, = (row for row in task.scientific_inputs if row.consumer_input_id == "config")
    assert configuration.payload_schema == type(cold_scope.config).SCHEMA
    assert len(task.outputs) == 3 and task.maximum_attempts == 1
    assert len({row.logical_artifact_id for row in task.external_inputs}) == 28
    assert cold_scope.config.role_bindings[0][0] == "admission"
    # Compiler closure does not resolve nonexistent evidence or grant readiness.
    with pytest.raises(ValueError, match="omits or adds"):
        config_owner.require_config_records(cold_scope.config, {})


@pytest.mark.parametrize("damage", ("missing-role", "role-swap", "history-role", "history-connection", "unit", "root", "extra-operation"))
def test_cold_compiler_refuses_changed_role_root_and_history_edges(cold_scope, damage):
    draft = cold_scope.draft
    if damage == "missing-role":
        draft = replace(draft, links=draft.links[:-1])
    elif damage == "role-swap":
        link = next(row for row in draft.links if row.consumer_input_id == "original-roster")
        draft = replace(draft, links=tuple(replace(row, external_input_id="external." + row.consumer_node_id + ".selected-roster")
            if row == link else row for row in draft.links))
    elif damage in {"history-role", "history-connection"}:
        link = next(row for row in draft.links if row.consumer_input_id == "history")
        changed = replace(link, scientific_role="SOURCE") if damage == "history-role" else replace(link, connection_id=None, requirement_id=None)
        draft = replace(draft, links=tuple(changed if row == link else row for row in draft.links))
    elif damage == "unit":
        draft = replace(draft, development_study=replace(draft.development_study, assigned_unit_ids=("unit.unrelated",)))
    elif damage == "root":
        draft = replace(draft, development_study=replace(draft.development_study, scientific_operands=draft.development_study.scientific_operands[:-1]))
    else:
        operation = draft.operations[0]
        draft = replace(draft, operations=(operation, replace(operation, node_id=operation.node_id + ".extra")),
            selected_operation_ids=(operation.node_id, operation.node_id + ".extra"))
    with pytest.raises(ValueError):
        compile_cold(cold_scope, draft)


def sealed_port(config, role, record):
    raw = record.canonical_bytes()
    descriptor = _anonymous_input_descriptor()
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(descriptor, raw[offset:])
        _seal_anonymous_input(descriptor)
        return WorkerInputPort(WorkerInputBinding(binding.artifact_id(config, role), "materialization.exposed-" + role,
            record.SCHEMA, original.MEDIA, len(raw), VisibilityCeiling.DEVELOPMENT_ONLY,
            OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL), _PreopenedBoundedReader(descriptor, maximum_bytes=len(raw)))
    except BaseException:
        os.close(descriptor)
        raise


def test_same_scientific_roster_label_retains_two_exact_roles_and_independent_cursors(cold_scope):
    assert cold_scope.original.roster_id == cold_scope.selected.roster_id
    assert cold_scope.original.fingerprint() != cold_scope.selected.fingerprint()
    ports = (sealed_port(cold_scope.config, "original-roster", cold_scope.original),
        sealed_port(cold_scope.config, "selected-roster", cold_scope.selected))
    try:
        for _ in range(2):
            for role, expected in (("original-roster", cold_scope.original), ("selected-roster", cold_scope.selected)):
                actual, port = binding.decode_role_input(cold_scope.config, role, ports)
                assert actual.canonical_bytes() == expected.canonical_bytes() and port.bytes_read == 0
        assert len({port.artifact_id for port in ports}) == 2
    finally:
        for port in ports:
            port.close()


@pytest.mark.parametrize("damage", ("swapped", "missing", "aliased", "schema", "access", "kind"))
def test_original_roster_role_substitution_refuses(cold_scope, damage):
    port = sealed_port(cold_scope.config, "original-roster", cold_scope.selected if damage == "swapped" else cold_scope.original)
    try:
        ports = (port,)
        if damage == "missing":
            ports = ()
        elif damage == "aliased":
            ports = (port, port)
        elif damage in {"schema", "access", "kind"}:
            fields = {"payload_schema": step.ForecastStepPolicy.SCHEMA} if damage == "schema" else {
                "outcome_access": OutcomeAccess.EVALUATION_REVEALED} if damage == "access" else {"kind": WorkerInputKind.DEPENDENCY}
            ports = (replace(port, binding=replace(port.binding, **fields)),)
        with pytest.raises(ValueError):
            binding.decode_role_input(cold_scope.config, "original-roster", ports)
    finally:
        port.close()


def test_request_identity_excludes_cosmetic_labels_and_lossless_encoding(selected, config):
    control = selected[2]
    request = config_owner.request_sha256(config, control)
    changed = replace(config, config_id="config.exposed-other-label", method=replace(config.method, method_id="method.exposed-other-label"))
    assert config_owner.request_sha256(changed, replace(control, policy_id="policy.exposed-other-label")) == request
    changed = replace(config, method=replace(config.method, maximum_segment_horizon_s=Decimal(30)))
    assert config_owner.request_sha256(changed, control) != request
    assert original.forecast_primitive(config) == original.forecast_primitive(replace(config, config_id="config.exposed-lossless-label"))


def test_closed_config_revision_and_reference_tamper_refuse(cold_scope):
    config = cold_scope.config
    assert decode_canonical_bytes(config.canonical_bytes(), type(config), maximum_bytes=None) == config
    with pytest.raises(ValueError):
        replace(config, role_bindings=config.role_bindings[:-1])
    role, ref = config.role_bindings[0]
    with pytest.raises(ValueError):
        replace(config, role_bindings=((role, replace(ref, object_version="9.0.0")), *config.role_bindings[1:]))
    with pytest.raises(ValueError):
        replace(config, role_bindings=((role, replace(ref, object_fingerprint="0" * 64)), *config.role_bindings[1:]))
    with pytest.raises(ValueError):
        config_owner.record_identity("precision", cold_scope.control)


def test_installed_factory_uses_one_declaration_and_original_six_descriptors():
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry.executable_binding import EXECUTABLE_BINDING_FACTORIES
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
    expected = {
        "assess": ("340ce56caa229be35dbb29d7e00da2e54d083941d7e72f0746810ad83e45a77a", "bc17a83f0d6e665ebaf087bc645b732068e95792a7e4d740bb82c0f5ba575b84"),
        "compare": ("cd3f9af9eee9a1c88d5486f81323fdaf497ee92d0b20c6882605b310b8163310", "d3ef974fc79548d5ded0d5088e1da4a44af8c362d2c97a31e74f8676d98917f7"),
        "forecast": ("b11ebcc41d3bc234df38f763475e3308a8b5885fd3390be8b5da854e360ce5ab", "276d694b21453e40c3c8ecd230b9083fbfc9f89f36dae376581571af3e1d8d5c"),
        "qualify": ("25f4d3c121311e042517eca8db6d339a3e123467d7734168e65457dc49389a66", "cf4a61c93b8f11e9827f67e1ce8a02ee9403bfdafbd4f7753eeb7b11e21cde7d"),
        "reuse": ("a6ba85492bf316f36f640a5e3f0134fb2fd96561bd85711948c18a7940bed760", "440eb439b618664e4fde5ace87fa743720f173b1d45e20941e79ffdba31fc165"),
        "validate": ("73fe4233fc1862e024f12cbb07a8890b46e7bb645aeee3b2c3222fbf4f1473df", "67946c3139a80c26ce14ab91d0e296e5aa7b9852a335a71909996e5c0ee9ba6e"),
    }
    for key, hashes in expected.items():
        factory = next(row for row in EXECUTABLE_BINDING_FACTORIES if row.manifest.capability_key == original.NAMESPACE + "." + key)
        assert (factory.manifest.fingerprint(), factory.binding.fingerprint()) == hashes
    factory, = (row for row in EXECUTABLE_BINDING_FACTORIES if row.manifest.capability_key == config_owner.CAPABILITY_KEY)
    assert factory.registration == binding.operation_declaration().registration()
    assert factory.registration.native_work_preparer is binding.prepare_native_work
    assert factory.runner_factory is binding.ControlledForecastWorker
    assert factory.manifest in EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests
    assert len(factory.registration.storage_codecs) == 2


@pytest.mark.parametrize('entry', ('prepare', 'preflight', 'project', 'live'))
def test_historical_controlled_config_cannot_enter_native_without_current_retained_work(entry):
    """Current1.0 software refusal precedes inputs/contact; no readiness claim."""
    worker = binding.ControlledForecastWorker()
    with pytest.raises(ValueError, match='SOFTWARE:.*unfinished-parent'):
        if entry == 'prepare':
            binding.prepare_native_work(runner=worker, context=None, expected_parent=None)
        elif entry == 'preflight':
            worker.preflight(None)
        elif entry == 'project':
            worker.project_forecast_scope(None, None)
        else:
            worker.execute_streaming_with_native_subwork(None, None, None, None)
