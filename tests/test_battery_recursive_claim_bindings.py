# SPDX-License-Identifier: MPL-2.0
"""Scientific claim resolution under coherent authored changes, no native runs."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_recursive_construction import science
from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import BatteryOperationConfig
from empirical_lawhood.adapters.methods.battery_recursive_construction.executable_binding import (
    operation_manifests, operation_registrations, output_codecs,
)
from empirical_lawhood.api.recursive_authoring import author_recursive_wave
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave, project_recursive_assessments
from tests.test_battery_recursive_scope_bindings import _compile, _draft, _edit
from tests.test_recursive_public_service import _plane


def _claims(draft, replacements):
    connections = tuple(replace(value, claim_id=replacements.get(value.connection_id, value.claim_id))
                        for value in draft.connections)
    by_id = {value.connection_id: value for value in connections}
    operations = []
    for operation in draft.operations:
        config = decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig,
                                        maximum_bytes=16 * 1024**2)
        if config.connection is not None:
            config = replace(config, connection=by_id[config.connection.connection_id])
            operation = replace(operation, config_payload=config.canonical_bytes().decode())
        operations.append(operation)
    return replace(draft, connections=connections, operations=tuple(operations))


@pytest.fixture(autouse=True)
def no_native_contact(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("pure claim binding contacted native battery science")

    for name in ("_runtime", "_phase", "capture_checkpoint", "continue_checkpoint", "source_preflight"):
        monkeypatch.setattr(science, name, forbidden)


@pytest.mark.parametrize("wave,tasks", [("A", 11), ("B", 21)])
@pytest.mark.parametrize("direct", [False, True])
def test_maintained_scoped_claims_and_actual_root_members_resolve(wave, tasks, direct):
    draft = _draft(wave)
    if direct:
        draft = _claims(draft, {row.connection_id: draft.development_study.claims[0].claim_id
                                for row in draft.connections})
    elif wave == "A":
        assert (draft.maximum_objects, draft.maximum_links, draft.maximum_depth) == (None, None, None)
        assert draft.fingerprint() == "25deb1b97611cd89ce3065229f642c2cee469e3374bedc22df06cf2b4791731b"
        # The historical identity retains its declared graph ceilings.
        historical = replace(draft, maximum_objects=256, maximum_links=1024, maximum_depth=32)
        assert historical.fingerprint() == "c97154850db52e0064c6232e1d148ada70d90ace127990631093e582c25a164f"
    assert len(_compile(draft).execution_plan.tasks) == tasks
    assert project_recursive_assessments(draft=draft, registrations=operation_registrations(), outputs={}) == ()


@pytest.mark.parametrize("wave", ["A", "B"])
@pytest.mark.parametrize("claim_id", [
    "claim.nonexistent", "claim.rc-chain.rc-j", "battery.wave-other.development-claim",
    "requirement.some-other-condition.claim", "requirement.battery.a.early.exact-state.claim.extra",
])
def test_coherently_changed_connection_claim_refuses_compile_and_retained_projection(wave, claim_id):
    draft = _draft(wave)
    changed = _claims(draft, {draft.connections[0].connection_id: claim_id})
    with pytest.raises(ValueError, match="scientific.*claim"):
        _compile(changed)
    # Missing outputs must not hide a dangling or unrelated scientific claim.
    with pytest.raises(ValueError, match="scientific.*claim"):
        project_recursive_assessments(draft=changed, registrations=operation_registrations(), outputs={})


@pytest.mark.parametrize("word", ["early1", "early3", "hold", "late1"])
def test_each_further_word_claim_is_resolved_even_outside_primary_config(word):
    draft = _draft("B")
    connection = next(value for value in draft.connections
                      if value.requirement_id == f"requirement.battery.b.product-{word}")
    changed = _claims(draft, {connection.connection_id: "claim.nonexistent"})
    with pytest.raises(ValueError, match="scientific.*claim"):
        _compile(changed)
    with pytest.raises(ValueError, match="scientific.*claim"):
        project_recursive_assessments(draft=changed, registrations=operation_registrations(), outputs={})


def test_another_valid_requirement_alias_does_not_answer_this_connection():
    draft = _draft("A")
    changed = _claims(draft, {draft.connections[0].connection_id: draft.connections[1].claim_id})
    with pytest.raises(ValueError, match="scientific.*claim"):
        _compile(changed)


@pytest.mark.parametrize("scope,requirement,connection", [
    ({"receiver_id": "physical-terminal"}, {}, {}),
    ({"available_by": Decimal(301)}, {}, {}),
    ({"valid_until": Decimal(601)}, {}, {}),
    ({}, {"falsifier": "Operational completion establishes physical validity."},
     {"falsifier": "Operational completion establishes physical validity."}),
])
def test_valid_claim_alias_does_not_override_scope_clock_or_falsifier(scope, requirement, connection):
    draft = _draft("A")
    changed = _edit(draft, draft.requirements[0].requirement_id,
                    scope=scope, requirement=requirement, connection=connection)
    with pytest.raises(ValueError, match="scientific scope|criterion or falsifier"):
        _compile(changed)


@pytest.mark.parametrize("direct", [False, True])
def test_exact_root_claim_label_can_be_changed_without_changing_science(direct):
    draft = _draft("A")
    root = replace(draft.development_study,
                   claims=(replace(draft.development_study.claims[0], claim_id="authored.actual-root-claim"),))
    campaign = replace(draft.campaign, target_claim_ids=(root.claims[0].claim_id,),
                       nodes=tuple(replace(node, object_identity=ObjectIdentity.from_record(root.study_id, root))
                                   for node in draft.campaign.nodes))
    changed = replace(draft, development_study=root, campaign=campaign)
    if direct:
        changed = _claims(changed, {row.connection_id: root.claims[0].claim_id for row in changed.connections})
    assert len(_compile(changed).execution_plan.tasks) == 11


def test_named_actual_root_member_does_not_override_the_closed_scientific_question():
    draft = _draft("A")
    root = replace(draft.development_study,
                   claims=(replace(draft.development_study.claims[0],
                                   proposition="This evidence establishes a new physical response law."),))
    campaign = replace(draft.campaign, nodes=tuple(
        replace(node, object_identity=ObjectIdentity.from_record(root.study_id, root))
        for node in draft.campaign.nodes))
    changed = _claims(replace(draft, development_study=root, campaign=campaign),
                      {row.connection_id: root.claims[0].claim_id for row in draft.connections})
    with pytest.raises(ValueError, match="root claim"):
        _compile(changed)


def test_named_actual_root_member_cannot_move_claim_and_campaign_to_another_world():
    draft = _draft("A")
    root = replace(draft.development_study, world_id="another-numerical-world",
                   claims=(replace(draft.development_study.claims[0], world_id="another-numerical-world"),))
    campaign = replace(draft.campaign, world_ids=(root.world_id,), nodes=tuple(
        replace(node, object_identity=ObjectIdentity.from_record(root.study_id, root))
        for node in draft.campaign.nodes))
    changed = _claims(replace(draft, development_study=root, campaign=campaign),
                      {row.connection_id: root.claims[0].claim_id for row in draft.connections})
    with pytest.raises(ValueError, match="battery scientific root"):
        _compile(changed)


def test_public_coherent_nonexistent_claim_refuses_before_authoring_publication(tmp_path):
    draft = _draft("A")
    changed = _claims(draft, {draft.connections[0].connection_id: "claim.nonexistent"})
    selected_root = tmp_path / "selected"
    output_dir = selected_root / "bad-claim"
    with pytest.raises(ValueError, match="scientific.*claim"):
        author_recursive_wave(draft=changed, project_root=Path(__file__).resolve().parents[1],
                              artifact_writer=_plane(selected_root), output_dir=output_dir)
    assert not output_dir.exists()


def test_legacy_structural_proof_cannot_execute_a_coherent_nonexistent_claim(monkeypatch, tmp_path):
    from empirical_lawhood.api import recursive_execution as execution
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, LocalScheduler

    draft = _draft("A")
    changed = _claims(draft, {draft.connections[0].connection_id: "claim.nonexistent"})
    registrations = operation_registrations()
    source = implementation_binding(Path(__file__).resolve().parents[1])
    # This exposed fixture models the earlier accepted claim bug. All actual
    # scientific scopes/edges remain validated and the ordinary structural
    # graph proof is genuine; only target resolution is deliberately permissive
    # while creating this in-memory legacy packet. No provider is constructed.
    def legacy_claim(config, context, requirement, connection):
        return context.root.claims[0]

    legacy = tuple(replace(value, scientific_claim_resolver=legacy_claim) for value in registrations)
    compilation = compile_recursive_wave(draft=changed, registrations=legacy,
        registry=CapabilityRegistry("test.legacy-claim-packet", operation_manifests()),
        implementation_commit=source.observed_git_head, output_codecs=output_codecs())
    assert len(compilation.execution_plan.tasks) == 11 and compilation.proof is not None
    records = {"run-plan.json": compilation.run_plan, "execution-plan.json": compilation.execution_plan,
               "template.json": compilation.template, "scientific-projection.json": compilation.selected_scientific_projection,
               "registry.json": compilation.registry, "graph-preservation.json": compilation.proof}
    payloads = {name: record.canonical_bytes() for name, record in records.items()}
    # Exercise the real retained proof reader before the narrow authenticated
    # loader seam: hashes and graph identities alone accept the legacy shape.
    execution._retained_plans(payloads, changed)
    monkeypatch.setattr(execution, "load_authored_wave", lambda **_: (None, changed, source, payloads))
    monkeypatch.setattr(execution, "implementation_binding", lambda _, **_kwargs: source)
    monkeypatch.setattr(execution, "operation_catalog", lambda: (registrations, compilation.registry, output_codecs()))
    effects = []

    def forbidden(*args, **kwargs):
        effects.append(True)
        pytest.fail("legacy claim packet reached custody publication, runtime capture or a worker")

    monkeypatch.setattr(execution, "_external_inputs", forbidden)
    monkeypatch.setattr(execution, "_provenance", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalScheduler, "execute", forbidden)
    monkeypatch.setattr("empirical_lawhood.api.matrix_numerical_provenance.capture_matrix_provenance", forbidden)
    plane = SimpleNamespace(root=SimpleNamespace(verify=forbidden), write=forbidden)
    with pytest.raises(ValueError, match="scientific.*claim"):
        execution.run_recursive_wave(directory=tmp_path / "legacy-authenticated-packet",
                                     project_root=Path(__file__).resolve().parents[1], artifact_writer=plane)
    assert effects == []
