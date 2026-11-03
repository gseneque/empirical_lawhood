# SPDX-License-Identifier: MPL-2.0
"""Pure invocation-local scientific joins; no effects or access authority."""

from dataclasses import FrozenInstanceError, dataclass, replace
from types import MappingProxyType
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec
from empirical_lawhood.planning.study_authoring import CapabilitySelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursiveOperationRegistration, RecursiveScientificRootPreparationContext,
    decode_recursive_config_input, project_recursive_config_inputs, validate_recursive_scientific_roots,
)
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks


@dataclass(frozen=True, slots=True)
class Config(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/scientific-preparation-config"
    config_id: str
    unit_id: str
    value: int


@dataclass(frozen=True, slots=True)
class Root(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/scientific-preparation-root"
    record_id: str
    expected_nodes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Prepared:
    batch: RecursiveScientificRootPreparationContext
    configs_by_node: object


BUDGET = ResourceBudget(1, 4096, 0, 1, 4096, 4096)
OUTPUTS = (OutputTemplate("product", Config.SCHEMA, ArtifactProfile.CANONICAL_JSON,
    "application/json", ".json"),)
LINKS = (RecursiveInputLink("edge.alpha.beta", "beta", "operand", "alpha", "product"),)


def _registration(name, validator, preparer=None):
    return RecursiveOperationRegistration(
        CapabilitySelection("testing.scientific-preparation." + name, "1.0.0", "a" * 64),
        ScientificStage.TRANSFORM, Config, (), OUTPUTS, (), OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET,
        scientific_unit_ids=lambda config: (config.unit_id,),
        scientific_root_validator=validator, scientific_root_preparer=preparer)


def _case(validator, preparer=None):
    first, second = _registration("first", validator, preparer), _registration("second", validator, preparer)
    registrations = {"alpha": first, "beta": second, "gamma": second}
    decoded = []
    for index, (node, registration) in enumerate(registrations.items()):
        config = Config("config." + node, "unit." + node, index)
        operation = RecursiveOperationSpec.from_config(node_id=node, selection=registration.selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=BUDGET)
        decoded.append(decode_recursive_config_input(operation, registration))
    return Root("root.disclosed", tuple(registrations)), project_recursive_config_inputs(tuple(decoded), registrations), registrations


def _invoke(case, **changes):
    root, rows, registrations = case
    values = dict(root=root, config_inputs=list(rows), registrations_for_node=registrations,
        requirements=[], connections=[], links=list(LINKS), external_inputs=[], qualifications=[], known_design_inputs=[])
    values.update(changes)
    return validate_recursive_scientific_roots(**values)


def _prepare(batch):
    if tuple(row.node_id for row in batch.config_inputs) != batch.root.expected_nodes or batch.links != LINKS:
        raise ValueError("disclosed complete scientific census changed")
    return Prepared(batch, MappingProxyType({row.node_id: row.record for row in batch.config_inputs}))


def test_two_registrations_share_one_complete_preparation_and_actual_unit_tuples():
    events, contexts, batches = [], [], []

    def prepare(batch):
        assert type(batch) is RecursiveScientificRootPreparationContext
        assert not isinstance(batch, CanonicalRecord)
        assert all(type(getattr(batch, name)) is tuple for name in (
            "config_inputs", "requirements", "connections", "links", "external_inputs", "qualifications", "known_design_inputs"))
        events.append("prepare")
        batches.append(batch)
        return _prepare(batch)

    def validate(config, context):
        prepared = context.scientific_preparation
        assert type(prepared) is Prepared
        assert context.root is prepared.batch.root
        assert context.config_inputs is prepared.batch.config_inputs
        assert context.links is prepared.batch.links
        assert context.external_inputs is prepared.batch.external_inputs
        assert context.requirements is prepared.batch.requirements
        assert context.connections is prepared.batch.connections
        assert context.qualifications is prepared.batch.qualifications
        assert context.known_design_inputs is prepared.batch.known_design_inputs
        assert prepared.configs_by_node[context.node_id] is config
        events.append(context.node_id)
        contexts.append(context)

    case = _case(validate, prepare)
    assert _invoke(case) is None
    assert events == ["prepare", "alpha", "beta", "gamma"]
    batch, = batches
    assert all(context.scientific_preparation is contexts[0].scientific_preparation for context in contexts)
    assert contexts[1].selected_unit_ids is contexts[2].selected_unit_ids
    assert contexts[1].selected_unit_ids == ("unit.beta", "unit.gamma")
    for context in contexts:
        selected = case[2][context.node_id].selection.selection_id
        assert context.selected_unit_ids is batch.selected_unit_ids_by_selection[selected]
    with pytest.raises(FrozenInstanceError):
        batch.root = case[0]
    with pytest.raises(TypeError):
        batch.selected_unit_ids_by_selection["foreign"] = ()


def test_new_invocations_prepare_again_and_changed_census_refuses_before_node_acceptance():
    batches, accepted = [], []

    def prepare(batch):
        batches.append(batch)
        return _prepare(batch)

    def validate(config, context):
        accepted.append(context.node_id)

    case = _case(validate, prepare)
    assert _invoke(case) is None and _invoke(case) is None
    assert len(batches) == 2 and batches[0] is not batches[1]
    assert accepted == ["alpha", "beta", "gamma"] * 2
    with pytest.raises(ValueError, match="complete scientific census changed"):
        _invoke(case, config_inputs=case[1][:-1])
    assert len(batches) == 3 and accepted == ["alpha", "beta", "gamma"] * 2
    with pytest.raises(ValueError, match="complete scientific census changed"):
        _invoke(case, links=())
    assert len(batches) == 4 and accepted == ["alpha", "beta", "gamma"] * 2


def test_all_distinct_preparers_run_before_any_node_validator():
    events = []

    def first(batch):
        events.append("first preparation")
        return _prepare(batch)

    def refused(batch):
        events.append("second preparation")
        raise ValueError("second scientific family refused")

    case = _case(lambda config, context: events.append("accepted"), first)
    registrations = {**case[2], "beta": replace(case[2]["beta"], scientific_root_preparer=refused),
        "gamma": replace(case[2]["gamma"], scientific_root_preparer=refused)}
    with pytest.raises(ValueError, match="second scientific family refused"):
        _invoke(case, registrations_for_node=registrations)
    assert events == ["first preparation", "second preparation"]


def test_callback_identity_does_not_call_user_hash_or_merge_equal_callables():
    calls, contexts = [], []

    class Preparer:
        __hash__ = None

        def __init__(self, name):
            self.name = name

        def __eq__(self, other):
            return True

        def __call__(self, batch):
            calls.append(self.name)
            return _prepare(batch)

    first, second = Preparer("first"), Preparer("second")
    case = _case(lambda config, context: contexts.append(context), first)
    registrations = {**case[2], "beta": replace(case[2]["beta"], scientific_root_preparer=second),
        "gamma": replace(case[2]["gamma"], scientific_root_preparer=second)}
    assert _invoke(case, registrations_for_node=registrations) is None
    assert calls == ["first", "second"]
    assert contexts[0].scientific_preparation is not contexts[1].scientific_preparation
    assert contexts[1].scientific_preparation is contexts[2].scientific_preparation
    assert contexts[0].scientific_preparation.batch is contexts[1].scientific_preparation.batch


def test_default_registration_keeps_each_existing_validator_and_no_prepared_result():
    contexts = []
    case = _case(lambda config, context: contexts.append(context))
    assert _invoke(case) is None
    assert tuple(context.node_id for context in contexts) == ("alpha", "beta", "gamma")
    assert all(context.scientific_preparation is None for context in contexts)


def test_none_preparation_refuses_before_any_node_validator():
    accepted = []
    case = _case(lambda config, context: accepted.append(context.node_id), lambda batch: None)
    with pytest.raises(ValueError, match="must return its invocation-local preparation"):
        _invoke(case)
    assert accepted == []


@pytest.mark.parametrize("kind", ("registration", "hooks"))
@pytest.mark.parametrize("preparer,validator", ((False, lambda config, context: None), (lambda batch: object(), None)))
def test_invalid_or_orphan_preparer_requires_its_callable_node_validator(kind, preparer, validator):
    with pytest.raises(TypeError, match="code-owned preparer and validator"):
        if kind == "hooks":
            RecursiveScientificHooks(scientific_root_preparer=preparer, scientific_root_validator=validator)
        else:
            replace(_registration("invalid", lambda config, context: None),
                scientific_root_preparer=preparer, scientific_root_validator=validator)


def test_batch_mapping_copy_preserves_unit_tuple_identity_without_external_mutability():
    case = _case(lambda config, context: None)
    selected = ("unit.alpha",)
    supplied = {"selection.disclosed": selected}
    batch = RecursiveScientificRootPreparationContext(case[0], case[1], (), (), LINKS, (), (), (), supplied)
    supplied["selection.disclosed"] = ("unit.changed",)
    assert batch.selected_unit_ids_by_selection["selection.disclosed"] is selected


def test_declaration_propagates_the_shared_preparer_without_constructing_a_runner():
    def forbidden_runner():
        raise AssertionError("pure scientific projection constructed a runner")

    def validate(config, context):
        return None

    declaration = RecursiveOperationDeclaration("testing.scientific-preparation.declared", "1.0.0", "disclosed-pure-v1",
        CapabilityKind.TRANSFORM, Config, ScientificStage.TRANSFORM, (), OUTPUTS, (), EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET,
        ("disclosed-pure-scientific-joins",), forbidden_runner, {Config.SCHEMA: Config},
        scientific_hooks=RecursiveScientificHooks(scientific_root_validator=validate, scientific_root_preparer=_prepare))
    assert declaration.registration().scientific_root_preparer is _prepare
    assert declaration.registration().scientific_root_validator is validate
