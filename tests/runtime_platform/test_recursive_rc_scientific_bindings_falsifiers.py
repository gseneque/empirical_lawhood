# SPDX-License-Identifier: MPL-2.0
"""Independent pure RC scientific-binding falsifiers, with effects blocked."""

from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operation_contracts as records
from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operations, science
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.operation_bindings import (
    operation_manifests, operation_registrations, output_codecs,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
from empirical_lawhood.adapters.composition.recursive_examples import rc_scientific_examples
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole
from empirical_lawhood.kernel.time import CausalPhase
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave, project_recursive_assessments

D = Decimal


@pytest.fixture
def frozen(monkeypatch):
    config = science.default_chain_config()
    draft = rc_recursive_draft(config, unit_ids=(config.units[6].unit_id,), include_summary=False)

    def denied(*args, **kwargs):
        pytest.fail("Pure scientific closure contacted acquisition, an oracle or a preparation decision")

    monkeypatch.setattr(operations, "_execute_native_views", denied)
    monkeypatch.setattr(science, "_measurement_state", denied)
    monkeypatch.setattr(science, "decide_preparation", denied)
    return config, draft


def _compile(draft):
    return compile_recursive_wave(draft=draft, registrations=operation_registrations(),
        registry=CapabilityRegistry("independent.rc.scientific-binding",
            tuple(sorted(operation_manifests(), key=lambda value: value.registry_id))),
        implementation_commit="a" * 40, output_codecs=output_codecs())


def _configs(draft, change):
    codecs = {registration.selection.selection_id: registration.config_record_type
              for registration in operation_registrations()}
    values = []
    for operation in draft.operations:
        config = decode_canonical_bytes(operation.config_payload.encode(),
            codecs[operation.selection.selection_id], maximum_bytes=16 * 1024**2)
        changed = change(operation.node_id, config)
        values.append(replace(operation, config_id=changed.config_id,
                              config_payload=changed.canonical_bytes().decode()))
    return replace(draft, operations=tuple(values))


def _refuses(draft):
    with pytest.raises(ValueError):
        _compile(draft)


def test_unchanged_rc_early_wave_is_pure_and_policy_ports_contain_no_native_truth(frozen):
    _, draft = frozen
    result = _compile(draft)
    assert len(result.execution_plan.tasks) == 9
    for row in result.config_inputs:
        if isinstance(row.record, records.RCPolicyOperationConfig):
            assert not hasattr(row.record, "scientific_config")
            assert not hasattr(row.record, "initial_voltage_volts")
            assert not hasattr(row.record, "units")


@pytest.mark.parametrize("phase", ["observations", "admit", "commit"])
@pytest.mark.parametrize("operand", ["menu", "task-tolerance", "decision-clock", "response-action"])
def test_policy_protocol_cannot_substitute_while_opaque_scientific_hash_matches(frozen, phase, operand):
    config, draft = frozen
    if operand == "menu":
        protocol = replace(config.protocol, preparation_durations_seconds=(D(0), D(2)))
    elif operand == "task-tolerance":
        protocol = replace(config.protocol, maximum_task_error_volts=D("0.5"))
    elif operand == "decision-clock":
        protocol = replace(config.protocol, decision_seconds=D("0.045"))
    else:
        with localcontext() as context:
            context.prec = 50
            protocol = replace(config.protocol, response_left_voltage_volts=D(2),
                response_coefficient_b_volts=(1 - config.protocol.response_coefficient_a))
    altered = _configs(draft, lambda node, record:
        replace(record, protocol=protocol) if node == "rc.u01." + phase else record)
    _refuses(altered)


def test_actual_full_configuration_cannot_change_without_matching_root_system_identity(frozen):
    config, draft = frozen
    changed_config = replace(config, config_id="actual.scientific-config.changed")

    def change(node, record):
        if isinstance(record, records.RCPolicyOperationConfig):
            return replace(record, scientific_config_sha256=changed_config.fingerprint())
        return replace(record, scientific_config=changed_config)

    altered = _configs(draft, change)
    altered = replace(altered, development_study=replace(altered.development_study,
        scientific_operands=(ObjectIdentity.from_record(changed_config.config_id, changed_config),)),
        requirements=tuple(replace(requirement, scope=replace(requirement.scope,
            source_config_sha256=changed_config.fingerprint())) for requirement in altered.requirements))
    assert altered.development_study.system.object_fingerprint == config.fingerprint()
    _refuses(altered)


@pytest.mark.parametrize("field,value", [
    ("quantity_ids", ("temperature",)), ("native_units", ("K",)),
    ("receiver_id", "other.receiver"), ("clock_id", "other.clock"),
    ("source_config_sha256", "f" * 64), ("instance_id", "other.assigned-preparation"),
    ("available_by", D("0.06")), ("valid_from", D("0.01")), ("valid_until", D(16)),
    ("population_id", "unassessed.population"),
    ("system_id", "other.system"), ("world_id", "other.world"),
    ("coordinate_meaning", "Temperature on a physical sensor's wall clock"),
])
@pytest.mark.parametrize("tag", ["m", "p", "j"])
def test_authored_requirement_scope_cannot_relabel_actual_rc_supply(frozen, field, value, tag):
    _, draft = frozen
    target = next(requirement for requirement in draft.requirements if requirement.requirement_id.endswith("." + tag))
    changed = replace(target, scope=replace(target.scope, **{field: value}))
    _refuses(replace(draft, requirements=tuple(changed if requirement == target else requirement
                                             for requirement in draft.requirements)))


def test_requirement_uncertainty_contract_must_be_actual_frozen_protocol(frozen):
    _, draft = frozen
    target = draft.requirements[0]
    changed = replace(target, scope=replace(target.scope, uncertainty_contract=replace(
        target.scope.uncertainty_contract, object_fingerprint="f" * 64)))
    _refuses(replace(draft, requirements=tuple(changed if requirement == target else requirement
                                             for requirement in draft.requirements)))


@pytest.mark.parametrize("meaning", ["criterion", "falsifier", "role", "claim"])
@pytest.mark.parametrize("tag", ["m", "p", "j"])
def test_rc_assessment_cannot_certify_another_criterion_role_or_claim(frozen, meaning, tag):
    _, draft = frozen
    target = next(requirement for requirement in draft.requirements if requirement.requirement_id.endswith("." + tag))
    connection = next(connection for connection in draft.connections if connection.requirement_id == target.requirement_id)
    if meaning == "criterion":
        target = replace(target, condition="The state interval proves a physical temperature measurement.")
    elif meaning == "falsifier":
        target = replace(target, falsifier="Always accept the observed endpoint.")
        connection = replace(connection, falsifier=target.falsifier)
    elif meaning == "role":
        target = replace(target, condition_role=ConditionRole.EVIDENTIAL,
                         permitted_roles=(ContributionRole.DESIGN_OPERAND,))
        connection = replace(connection, evidence_role=ContributionRole.DESIGN_OPERAND)
    else:
        connection = replace(connection, claim_id="claim.rc-chain.rc-" + ("m" if tag == "j" else "j"))
    _refuses(replace(draft,
        requirements=tuple(target if requirement.requirement_id == target.requirement_id else requirement
                           for requirement in draft.requirements),
        connections=tuple(connection if existing.connection_id == connection.connection_id else existing
                          for existing in draft.connections)))


@pytest.mark.parametrize("field,value", [
    ("relation_id", "relation.other.native-quantity"),
    ("proposition", "The two numerical views qualify independent physical sensors."),
    ("estimand", "Temperature in kelvin over independently counted solver rows."),
    ("physical_independent_unit_id", "units.native-solver-rows"),
    ("numerical_view_ids", ("unperformed.native-view",)),
])
def test_root_claim_cannot_substitute_native_estimand_denominator_or_views(frozen, field, value):
    _, draft = frozen
    root = draft.development_study
    claims = (replace(root.claims[0], **{field: value}), *root.claims[1:])
    _refuses(replace(draft, development_study=replace(root, claims=claims)))


def test_actual_rc_numerical_source_cannot_be_relabelled_as_another_world_kind(frozen):
    _, draft = frozen
    _refuses(replace(draft, development_study=replace(draft.development_study,
        world_kind=WorldKind.ANALYTIC_REFERENCE)))


@pytest.mark.parametrize("tag", ["m", "p", "j"])
@pytest.mark.parametrize("field,value", [
    ("clock_id", "clock.other"), ("coordinate", D("0.06")),
    ("phase", CausalPhase.POST_OUTCOME), ("includes_coordinate", False),
])
def test_information_cutoff_cannot_be_coherently_reinterpreted(frozen, tag, field, value):
    _, draft = frozen
    target = next(item for item in draft.requirements if item.requirement_id.endswith("." + tag))
    altered = replace(target, scope=replace(target.scope, information_cutoff=replace(
        target.scope.information_cutoff, **{field: value})))
    _refuses(replace(draft, requirements=tuple(altered if item == target else item for item in draft.requirements)))


def test_numerically_equal_decimal_spelling_has_same_canonical_protocol_identity(frozen):
    config, draft = frozen
    protocol = replace(config.protocol, decision_seconds=D("0.050"))
    assert protocol == config.protocol
    assert protocol.canonical_bytes() == config.protocol.canonical_bytes()
    assert len(_compile(_configs(draft, lambda node, record: replace(record, protocol=protocol)
        if isinstance(record, records.RCPolicyOperationConfig) else record)).execution_plan.tasks) == 9


def test_same_numerical_protocol_cannot_substitute_canonical_record_identity(frozen):
    config, draft = frozen
    protocol = replace(config.protocol, protocol_id="other.protocol.identity")
    assert protocol.decision_seconds == config.protocol.decision_seconds
    assert protocol.canonical_bytes() != config.protocol.canonical_bytes()
    _refuses(_configs(draft, lambda node, record: replace(record, protocol=protocol)
        if isinstance(record, records.RCPolicyOperationConfig) else record))


@pytest.mark.parametrize("tag", ["p", "j"])
def test_supply_cannot_drop_same_unit_measurement_preparation_prerequisites(frozen, tag):
    _, draft = frozen
    target = next(item for item in draft.requirements if item.requirement_id.endswith("." + tag))
    _refuses(replace(draft, requirements=tuple(replace(item, further_requirement_ids=())
        if item == target else item for item in draft.requirements)))


@pytest.mark.parametrize("role", ["ACTION", "SOURCE", "PARENT_RECEIPT"])
def test_same_schema_history_does_not_authorize_another_causal_input_role(frozen, role):
    _, draft = frozen
    edge = next(item for item in draft.links if item.consumer_node_id.endswith(".admit"))
    _refuses(replace(draft, links=tuple(replace(item, scientific_role=role)
        if item == edge else item for item in draft.links)))


@pytest.mark.parametrize("consumer", ["commit", "joined", "reduce"])
def test_requirement_cannot_move_its_consumer_to_same_schema_other_unit(frozen, consumer):
    config, _ = frozen
    draft = rc_recursive_draft(config, unit_ids=(config.units[5].unit_id, config.units[6].unit_id), include_summary=False)
    target = next(item for item in draft.requirements if item.consumer_operation_id == "rc.u01." + consumer)
    changed = replace(target, consumer_operation_id="rc.u02." + consumer)
    _refuses(replace(draft, requirements=tuple(changed if item == target else item for item in draft.requirements)))


@pytest.mark.parametrize("consumer,port", [("admit", "reports"), ("deliver", "commitments"),
    ("measure", "source"), ("joined", "native"), ("reduce", "reports")])
def test_correct_output_schema_does_not_permit_cross_unit_dependency(frozen, consumer, port):
    config, _ = frozen
    draft = rc_recursive_draft(config, unit_ids=(config.units[5].unit_id, config.units[6].unit_id), include_summary=False)
    edge = next(item for item in draft.links if item.consumer_node_id == "rc.u01." + consumer
                and item.consumer_input_id == port)
    _refuses(replace(draft, links=tuple(replace(item, producer_node_id=edge.producer_node_id.replace("u01", "u02"))
        if item == edge else item for item in draft.links)))


def test_independent_units_cannot_alias_scoped_source_declaration(frozen):
    config, _ = frozen
    draft = rc_recursive_draft(config, unit_ids=(config.units[5].unit_id, config.units[6].unit_id), include_summary=False)
    _refuses(replace(draft, requirements=tuple(replace(item, scope=replace(item.scope,
        source_id="source.shared-alias")) for item in draft.requirements)))


def test_same_unit_supply_source_labels_cannot_change_independently(frozen):
    _, draft = frozen
    target = draft.requirements[0]
    _refuses(replace(draft, requirements=tuple(replace(item, scope=replace(item.scope,
        source_id="source.unjoined-alias")) if item == target else item for item in draft.requirements)))


def test_coherent_node_claim_requirement_and_source_label_renaming_preserves_science(frozen):
    _, draft = frozen
    nodes = {item.node_id: f"renamed.operation.{index:02d}" for index, item in enumerate(draft.operations)}
    requirements = {item.requirement_id: f"renamed.requirement.{index:02d}" for index, item in enumerate(draft.requirements)}
    connections = {item.connection_id: f"renamed.connection.{index:02d}" for index, item in enumerate(draft.connections)}
    claims = {item.claim_id: f"renamed.claim.{index:02d}" for index, item in enumerate(draft.development_study.claims)}
    changed_requirements = tuple(replace(item, requirement_id=requirements[item.requirement_id],
        consumer_operation_id=nodes[item.consumer_operation_id], assessment_operation_id=nodes[item.assessment_operation_id],
        further_requirement_ids=tuple(sorted(requirements[parent] for parent in item.further_requirement_ids)),
        scope=replace(item.scope, source_id="renamed.source", information_cutoff=replace(
            item.scope.information_cutoff, cutoff_id="renamed.cutoff"))) for item in draft.requirements)
    changed = replace(draft,
        development_study=replace(draft.development_study, claims=tuple(sorted((replace(item,
            claim_id=claims[item.claim_id]) for item in draft.development_study.claims), key=lambda item: item.claim_id))),
        campaign=replace(draft.campaign, target_claim_ids=tuple(sorted(claims.values()))),
        requirements=changed_requirements,
        connections=tuple(replace(item, connection_id=connections[item.connection_id], requirement_id=requirements[item.requirement_id],
            supplier_operation_id=nodes[item.supplier_operation_id], assessment_operation_id=nodes[item.assessment_operation_id],
            claim_id=claims[item.claim_id]) for item in draft.connections),
        suppliers=tuple(replace(item, requirement_id=requirements[item.requirement_id],
            operation_ids=tuple(sorted(nodes[node] for node in item.operation_ids)),
            prerequisite_requirement_ids=tuple(sorted(requirements[parent] for parent in item.prerequisite_requirement_ids)))
            for item in draft.suppliers),
        operations=tuple(sorted((replace(item, node_id=nodes[item.node_id], obligation_ids=tuple(sorted(
            requirements.get(obligation, obligation) for obligation in item.obligation_ids))) for item in draft.operations),
            key=lambda item: item.node_id)),
        selected_operation_ids=tuple(sorted(nodes.values())),
        links=tuple(replace(item, consumer_node_id=nodes[item.consumer_node_id], producer_node_id=nodes[item.producer_node_id],
            requirement_id=requirements.get(item.requirement_id), connection_id=connections.get(item.connection_id)) for item in draft.links))
    assert len(_compile(changed).execution_plan.tasks) == 9


@pytest.mark.parametrize("name", ["original", "menu-v2", "budget-v3"])
def test_all_three_frozen_scientific_roots_compile_complete_census_without_effects(frozen, name):
    config = rc_scientific_examples()[name]
    result = _compile(rc_recursive_draft(config))
    assert len(result.execution_plan.tasks) == 100
    assert len(result.config_inputs) == 100


@pytest.mark.parametrize("field,value", [
    ("question", "Do physical temperature sensors qualify independent evidence?"),
    ("numerical_view_ids", ("unperformed.view",)),
])
def test_root_cannot_restate_an_unperformed_scientific_question_or_view(frozen, field, value):
    _, draft = frozen
    _refuses(replace(draft, development_study=replace(draft.development_study, **{field: value})))


@pytest.mark.parametrize("field,value", [
    ("object_id", "system.other"), ("object_schema", "empirical-lawhood/other/model"),
    ("object_version", "2.0.0"), ("object_fingerprint", "f" * 64),
])
def test_root_actual_system_identity_cannot_substitute_source_or_revision(frozen, field, value):
    _, draft = frozen
    _refuses(replace(draft, development_study=replace(draft.development_study,
        system=replace(draft.development_study.system, **{field: value}))))


def test_coherently_bound_unrepresentable_work_budget_refuses_before_native_contact(frozen):
    config, draft = frozen
    protocol = replace(config.protocol, maximum_native_steps=1)
    actual = replace(config, protocol=protocol)
    changed = _configs(draft, lambda node, row: replace(row, protocol=protocol,
        scientific_config_sha256=actual.fingerprint()) if isinstance(row, records.RCPolicyOperationConfig)
        else replace(row, scientific_config=actual))
    changed = replace(changed, development_study=replace(changed.development_study,
        system=ObjectIdentity.from_record(changed.development_study.system.object_id, actual),
        scientific_operands=(ObjectIdentity.from_record(actual.config_id, actual),)),
        requirements=tuple(replace(item, scope=replace(item.scope, source_config_sha256=actual.fingerprint(),
            uncertainty_contract=ObjectIdentity.from_record("protocol.rc-chain", protocol))) for item in changed.requirements))
    _refuses(changed)


@pytest.mark.parametrize("change", ["policy", "claim", "scope"])
def test_retained_rc_reader_replays_scientific_bindings_before_any_assessment_output(frozen, change):
    config, draft = frozen
    assert project_recursive_assessments(draft=draft, registrations=operation_registrations(), outputs={}) == ()
    if change == "policy":
        altered = _configs(draft, lambda node, row: replace(row,
            protocol=replace(config.protocol, preparation_durations_seconds=(D(0), D(2))))
            if isinstance(row, records.RCPolicyOperationConfig) else row)
    elif change == "claim":
        claims = (replace(draft.development_study.claims[0], estimand="An unperformed native quantity"),
                  *draft.development_study.claims[1:])
        altered = replace(draft, development_study=replace(draft.development_study, claims=claims))
    else:
        altered = replace(draft, requirements=tuple(replace(item,
            scope=replace(item.scope, native_units=("K",))) for item in draft.requirements))
    with pytest.raises(ValueError):
        project_recursive_assessments(draft=altered, registrations=operation_registrations(), outputs={})
