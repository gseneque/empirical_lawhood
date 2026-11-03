# SPDX-License-Identifier: MPL-2.0
"""Publication-boundary conformance with synthetic configs, without authority."""

from dataclasses import dataclass, replace
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.api import load_authoring
from empirical_lawhood.api.recursive_publications import (
    authenticate_draft_publications, authenticate_registered_publications,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import CapabilitySelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.plans import BarrierKind, ExternalInputSpec, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursiveConfigInput, RecursiveOperationRegistration, RegisteredPublicationRequirement,
)


@dataclass(frozen=True, slots=True)
class PublicationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/publication-dispatch-config"
    config_id: str
    member_id: str


@dataclass(frozen=True, slots=True)
class ForeignConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/foreign-publication-config"
    config_id: str
    member_id: str


BUDGET = ResourceBudget(1, 4096, 0, 1, 4096, 4096)


def _registration(name, requirements=()):
    return RecursiveOperationRegistration(
        CapabilitySelection("testing.publication." + name, "1.0.0", "a" * 64),
        ScientificStage.FREEZE, PublicationConfig, (),
        (OutputTemplate("result", PublicationConfig.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                        "application/json", ".json"),),
        (), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BUDGET,
        barrier=BarrierKind.FREEZE, publication_requirements=requirements,
    )


def _frozen_config(operation, record):
    raw = record.canonical_bytes()
    return RecursiveConfigInput(
        operation.node_id, operation.config_id,
        ExternalInputSpec("config", operation.config_id, record.fingerprint(), record.SCHEMA,
                          "application/json", len(raw), VisibilityCeiling.PROSPECTIVE,
                          OutcomeAccess.OUTCOME_BLIND, None),
        raw, record, type(record),
    )


def _scope(requirements, *, second_requirements=None):
    registrations = (
        _registration("alpha", requirements), _registration("plain"),
        _registration("zeta", requirements if second_requirements is None else second_requirements),
    )
    entries = (("node.a", registrations[0]), ("node.m", registrations[1]), ("node.z", registrations[2]))
    operations, configs = [], []
    for node_id, registration in entries:
        record = PublicationConfig("config." + node_id, "member." + node_id)
        operation = RecursiveOperationSpec.from_config(
            node_id=node_id, selection=registration.selection, config_id=record.config_id,
            config=record, obligation_ids=("obligation." + node_id,), resource_budget=BUDGET,
        )
        operations.append(operation)
        configs.append(_frozen_config(operation, record))
    # This campaign is exposed fixture metadata; nothing is issued or executed.
    campaign = load_authoring(Path(__file__).resolve().parents[1] / "fixtures/reference-campaign.json").campaign
    draft = RecursiveStudyDraft(
        "draft.publication-dispatch", "Authenticate complete frozen selected configs", campaign,
        (), (), (), tuple(operations), (), (), tuple(row.node_id for row in operations),
    )
    return draft, tuple(configs), registrations


def _authenticate(scope, writer, *, configs=None, registrations=None):
    draft, original_configs, original_registrations = scope
    return authenticate_registered_publications(
        draft=draft, config_inputs=original_configs if configs is None else configs,
        registrations=original_registrations if registrations is None else registrations,
        artifact_writer=writer,
    )


def test_shared_requirement_receives_complete_sorted_configs_once_across_registrations():
    calls = []
    writer = object()

    def authenticate(actual_writer, rows):
        calls.append((actual_writer, rows))

    shared = RegisteredPublicationRequirement("publication.shared", authenticate)
    scope = _scope((shared,))
    assert _authenticate(scope, writer, configs=tuple(reversed(scope[1]))) is None
    assert calls == [(writer, (scope[1][0], scope[1][2]))]
    assert tuple(row.payload for row in calls[0][1]) == tuple(
        operation.config_payload.encode() for operation in (scope[0].operations[0], scope[0].operations[2])
    )


def test_each_new_custody_boundary_reauthenticates_instead_of_reusing_an_old_success():
    calls = []

    def authenticate(writer, rows):
        calls.append((writer, tuple(row.node_id for row in rows)))

    scope = _scope((RegisteredPublicationRequirement("publication.shared", authenticate),))
    author_writer, reader_writer = object(), object()
    _authenticate(scope, author_writer)
    _authenticate(scope, reader_writer)
    assert calls == [(author_writer, ("node.a", "node.z")), (reader_writer, ("node.a", "node.z"))]


def test_retained_draft_reauthenticates_exact_frozen_configs_at_each_boundary():
    calls = []
    permitted = [True]

    def authenticate(writer, rows):
        calls.append((writer, rows))
        if not permitted[0]:
            raise PermissionError("retained publication no longer authenticates")

    draft, configs, registrations = _scope((
        RegisteredPublicationRequirement("publication.shared", authenticate),))
    first, second = object(), object()
    authenticate_draft_publications(draft=draft, registrations=registrations, artifact_writer=first)
    assert calls == [(first, (configs[0], configs[2]))]
    permitted[0] = False
    with pytest.raises(PermissionError, match="no longer authenticates"):
        authenticate_draft_publications(draft=draft, registrations=registrations, artifact_writer=second)
    assert calls[-1] == (second, (configs[0], configs[2]))


def test_distinct_requirements_dispatch_in_stable_order_with_their_own_complete_groups():
    calls = []

    def first(_writer, rows):
        calls.append(("first", tuple(row.node_id for row in rows)))

    def last(_writer, rows):
        calls.append(("last", tuple(row.node_id for row in rows)))

    alpha = RegisteredPublicationRequirement("publication.a", first)
    zeta = RegisteredPublicationRequirement("publication.z", last)
    scope = _scope((alpha, zeta), second_requirements=(zeta,))
    _authenticate(scope, object(), configs=tuple(reversed(scope[1])))
    assert calls == [("first", ("node.a",)), ("last", ("node.a", "node.z"))]


@pytest.mark.parametrize("mutation, message", (
    ("missing-plain", "omits a selected frozen configuration"),
    ("duplicate-config", "configuration custody omits or substitutes its actual selected record"),
    ("foreign-node", "substitutes a selected operation/configuration"),
    ("foreign-record", "substitutes a selected operation/configuration"),
    ("missing-registration", "substitutes a selected operation/configuration"),
    ("duplicate-registration", "duplicate operation registrations"),
    ("different-implementation", "substitutes a selected operation/configuration"),
))
def test_incomplete_or_substituted_selected_census_refuses_before_any_authenticator(mutation, message):
    def forbidden(*_args):
        raise AssertionError("incomplete selected census reached an authenticator")

    scope = _scope((RegisteredPublicationRequirement("publication.shared", forbidden),))
    configs, registrations = scope[1], scope[2]
    if mutation == "missing-plain":
        configs = (configs[0], configs[2])
    elif mutation == "duplicate-config":
        configs = (*configs, configs[0])
    elif mutation == "foreign-node":
        configs = (*configs, replace(configs[0], node_id="node.unselected"))
    elif mutation == "foreign-record":
        configs = (replace(configs[0], record=ForeignConfig("config.node.a", "member.node.a")), *configs[1:])
    elif mutation == "missing-registration":
        registrations = registrations[1:]
    elif mutation == "duplicate-registration":
        registrations = (*registrations, registrations[0])
    else:
        changed = replace(registrations[0].selection, implementation_sha256="b" * 64)
        registrations = (replace(registrations[0], selection=changed), *registrations[1:])
    with pytest.raises(ValueError, match=message):
        _authenticate(scope, object(), configs=configs, registrations=registrations)


def test_same_requirement_id_with_different_authenticators_refuses_before_both():
    def first(*_args):
        raise AssertionError("conflicting authenticator was invoked")

    def second(*_args):
        raise AssertionError("conflicting authenticator was invoked")

    scope = _scope((RegisteredPublicationRequirement("publication.shared", first),),
        second_requirements=(RegisteredPublicationRequirement("publication.shared", second),))
    with pytest.raises(ValueError, match="conflicting validators"):
        _authenticate(scope, object())


def test_unselected_operation_and_its_conflicting_requirement_do_not_join_selected_scope():
    calls = []

    def selected(_writer, rows):
        calls.append(tuple(row.node_id for row in rows))

    def unselected(*_args):
        raise AssertionError("unselected publication obligation reached custody")

    scope = _scope((RegisteredPublicationRequirement("publication.shared", selected),))
    other = _registration("future", (RegisteredPublicationRequirement("publication.shared", unselected),))
    config = PublicationConfig("config.node.future", "member.node.future")
    operation = RecursiveOperationSpec.from_config(node_id="node.future", selection=other.selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation.future",), resource_budget=BUDGET)
    draft = replace(scope[0], operations=tuple(sorted((*scope[0].operations, operation), key=lambda row: row.node_id)))
    _authenticate((draft, scope[1], (*scope[2], other)), object())
    assert calls == [("node.a", "node.z")]


def test_authenticator_refusal_propagates_the_original_exception_and_stops_dispatch():
    refusal = PermissionError("original publication no longer authenticates")

    def refuse(_writer, _rows):
        raise refusal

    def later(*_args):
        raise AssertionError("dispatch continued after publication refusal")

    scope = _scope((RegisteredPublicationRequirement("publication.a", refuse),
                    RegisteredPublicationRequirement("publication.z", later)))
    with pytest.raises(PermissionError) as caught:
        _authenticate(scope, object())
    assert caught.value is refusal


@pytest.mark.parametrize("result", (True, False, 0, (), {}))
def test_authenticator_must_raise_on_refusal_and_return_exact_none_on_success(result):
    def invalid(_writer, _rows):
        return result

    scope = _scope((RegisteredPublicationRequirement("publication.shared", invalid),))
    with pytest.raises(ValueError, match="raise on refusal and return None"):
        _authenticate(scope, object())


@pytest.mark.parametrize("mutation", ("record", "payload", "config-id", "record-type", "input-digest"))
def test_selected_config_cannot_substitute_its_frozen_record_bytes_or_identity(mutation):
    def forbidden(*_args):
        raise AssertionError("substituted frozen configuration reached publication authentication")

    scope = _scope((RegisteredPublicationRequirement("publication.shared", forbidden),))
    first = scope[1][0]
    if mutation == "record":
        first = replace(first, record=replace(first.record, member_id="member.changed"))
    elif mutation == "payload":
        first = replace(first, payload=replace(first.record, member_id="member.changed").canonical_bytes())
    elif mutation == "config-id":
        first = replace(first, config_id="config.changed")
    elif mutation == "record-type":
        first = replace(first, record_type=ForeignConfig)
    else:
        first = replace(first, input_spec=replace(first.input_spec, expected_content_sha256="c" * 64))
    with pytest.raises(ValueError, match="frozen configuration|selected operation/configuration"):
        _authenticate(scope, object(), configs=(first, *scope[1][1:]))
