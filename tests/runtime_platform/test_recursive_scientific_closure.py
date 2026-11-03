# SPDX-License-Identifier: MPL-2.0
"""Pure scientific closure falsifiers, independent of the operational task DAG."""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import SupplierProposal, explain_recursive_draft
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave, project_recursive_assessments
from empirical_lawhood.runtime.scientific_graph_preservation import prove_development_graph_parity
from tests.runtime_platform.test_recursive_compiler import fixture


def _background_wave(prerequisites, supplier_prerequisites=(), maximum_depth=32):
    draft, registrations, registry = fixture()
    original = draft.requirements[0]
    requirements = tuple(replace(original, requirement_id=key,
        further_requirement_ids=tuple(sorted(parents)), background_assumption_ids=("assumption.fixed",))
        for key, parents in sorted(prerequisites.items()))
    suppliers = tuple(SupplierProposal("supplier." + key, key, ("source",),
        tuple(sorted(parents)), True, "Selected static supplier prerequisites")
        for key, parents in sorted(dict(supplier_prerequisites).items()))
    return replace(draft, requirements=requirements, connections=(), suppliers=suppliers,
        links=tuple(replace(link, requirement_id=None, connection_id=None) for link in draft.links),
        maximum_depth=maximum_depth), registrations, registry


def _compile(parts):
    draft, registrations, registry = parts
    return compile_recursive_wave(draft=draft, registrations=registrations,
                                  registry=registry, implementation_commit="1" * 40)


@pytest.mark.parametrize(("prerequisites", "supplier_prerequisites"), [
    ({"a": ("b",), "b": ("a",)}, ()),
    ({"a": ("b",), "b": ("c",), "c": ("a",)}, ()),
    ({"a": (), "b": ()}, (("a", ("b",)), ("b", ("a",)))),
    ({"a": ("b",), "b": ()}, (("b", ("a",)),)),
    ({"a": ()}, (("a", ("a",)),)),
])
def test_scientific_cycles_refuse_acyclic_task_wave_and_retained_empty_outputs(prerequisites, supplier_prerequisites):
    parts = _background_wave(prerequisites, supplier_prerequisites)
    draft, registrations, _ = parts
    assert [(link.producer_node_id, link.consumer_node_id) for link in draft.links] == [("source", "use")]
    with pytest.raises(ValueError, match="scientific requirement graph.*cycle"):
        _compile(parts)
    with pytest.raises(ValueError, match="scientific requirement graph.*cycle"):
        project_recursive_assessments(draft=draft, registrations=registrations, outputs={})
    assert any("cycle" in reason for _, reason in explain_recursive_draft(draft)["unresolved_selected_premises"])


def test_retained_preservation_proof_revalidates_coherently_substituted_requirement_cycle():
    parts = _background_wave({"a": (), "b": ("a",)})
    compiled = _compile(parts)
    changed = replace(parts[0], requirements=(replace(parts[0].requirements[0], further_requirement_ids=("b",)),
                                             parts[0].requirements[1]))
    selection = replace(compiled.selected_scientific_projection, requirements=changed.requirements)
    run = replace(compiled.run_plan, draft=ObjectIdentity.from_record(changed.draft_id, changed),
                  scientific_projection=ObjectIdentity.from_record(selection.selection_id, selection))
    plan = replace(compiled.execution_plan, source_plan=ObjectIdentity.from_record(run.run_plan_id, run))
    with pytest.raises(ValueError, match="scientific requirement graph.*cycle"):
        prove_development_graph_parity(draft=changed, selection=selection, template=compiled.template,
            run_plan=run, execution_plan=plan, registry=compiled.registry)


def test_acyclic_scientific_dependencies_are_distinct_from_flat_task_dependencies():
    compiled = _compile(_background_wave({"a": (), "b": ("a",), "c": ("a", "b")},
                                        (("c", ("a",)),)))
    assert compiled.proof.requirement_count == 3 and compiled.proof.node_count == 2
    assert project_recursive_assessments(draft=compiled.draft, registrations=fixture()[1], outputs={}) == ()


def test_scientific_depth_limit_refuses_flat_operational_dag():
    with pytest.raises(ValueError, match="scientific requirement graph.*depth"):
        _compile(_background_wave({"a": (), "b": ("a",), "c": ("b",)}, maximum_depth=2))


def test_unrestricted_scientific_graph_exceeds_original_depth_and_object_ceilings():
    prerequisites = {f'requirement-{index:04d}': (() if index == 0 else (f'requirement-{index - 1:04d}',))
                     for index in range(270)}
    compiled = _compile(_background_wave(prerequisites, maximum_depth=None))
    assert compiled.proof.requirement_count == 270
    assert compiled.proof.node_count == 2
    assert compiled.draft.maximum_depth is None


def test_selected_supplier_prerequisite_must_be_in_closed_selected_scientific_wave():
    with pytest.raises(ValueError, match="scientific requirement graph.*unresolved"):
        _compile(_background_wave({"a": ()}, (("a", ("missing",)),)))


def test_selected_supplier_edge_cannot_be_omitted_from_authoritative_requirement_projection():
    parts = _background_wave({"a": (), "b": ()}, (("b", ("a",)),))
    with pytest.raises(ValueError, match="supplier prerequisites must be declared"):
        _compile(parts)
    with pytest.raises(ValueError, match="supplier prerequisites must be declared"):
        project_recursive_assessments(draft=parts[0], registrations=parts[1], outputs={})


def test_issued_recursive_parity_rejects_scientific_cycle_before_issuing_a_proof(tmp_path):
    from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
    from empirical_lawhood.runtime.scientific_graph_preservation import prove_recursive_graph_parity
    from tests.runtime_platform.test_recursive_compiler import prospective_fixture
    from tests.runtime_platform.test_recursive_prospective_workflow import _actual_source, _issued_fixture

    original, _, _ = prospective_fixture(typed_outputs=True)
    compiled, authoring, context, _, _ = _actual_source(original)
    issued = _issued_fixture(tmp_path, compiled, authoring, context)
    candidate = issued.package.issued_study.candidate
    assert isinstance(candidate, ExecutableStudyCandidate)
    cycle = _background_wave({"a": ("b",), "b": ("a",)})[0].requirements
    selection = replace(compiled.selected_scientific_projection, requirements=cycle)
    with pytest.raises(ValueError, match="scientific requirement graph.*cycle"):
        prove_recursive_graph_parity(base_receipt=None, selection=selection, template=compiled.template,
            candidate=candidate, run_plan=None, execution_plan=None, registry=compiled.registry,
            issued_extensions=None)


def test_unselected_partial_requirement_cycle_remains_authorable_without_blessing_it():
    draft, registrations, registry = fixture()
    prototype = draft.requirements[0]
    extras = tuple(replace(prototype, requirement_id="unselected." + key,
        consumer_operation_id="later.unregistered", assessment_operation_id=None,
        further_requirement_ids=("unselected." + other,)) for key, other in (("a", "b"), ("b", "a")))
    changed = replace(draft, requirements=tuple(sorted((*draft.requirements, *extras), key=lambda value: value.requirement_id)))
    compiled = _compile((changed, registrations, registry))
    assert compiled.proof.requirement_count == 1 and len(changed.requirements) == 3
    assert explain_recursive_draft(changed)["selected_requirement_count"] == 1


@pytest.mark.parametrize("label", ["claim.missing", "claim.wrong-domain", "claim.other-root"])
def test_default_scientific_claim_resolution_rejects_undeclared_aliases_and_retained_projection(label):
    draft, registrations, registry = fixture()
    changed = replace(draft, connections=(replace(draft.connections[0], claim_id=label),))
    with pytest.raises(ValueError, match="declared root claim"):
        _compile((changed, registrations, registry))
    with pytest.raises(ValueError, match="declared root claim"):
        project_recursive_assessments(draft=changed, registrations=registrations, outputs={})


def test_installed_claim_resolver_receives_actual_assessor_config_and_exact_frozen_pair():
    draft, registrations, registry = fixture()
    alias = replace(draft.connections[0], claim_id="reviewed.alias")
    changed = replace(draft, connections=(alias,))
    calls = []

    def resolve(config, context, requirement, connection):
        assert config.config_id == "config.use" and context.node_id == "use"
        assert context.root == changed.development_study
        assert requirement == changed.requirements[0] and connection == alias
        calls.append((requirement.requirement_id, connection.connection_id))
        return context.root.claims[0]

    registered = tuple(replace(value, scientific_claim_resolver=resolve)
                       if value.selection.capability_key == "generic.use" else value for value in registrations)
    _compile((changed, registered, registry))
    project_recursive_assessments(draft=changed, registrations=registered, outputs={})
    assert calls == [(draft.requirements[0].requirement_id, alias.connection_id)] * 2


@pytest.mark.parametrize("change", [lambda claim: False, lambda claim: claim.claim_id,
    lambda claim: ObjectIdentity.from_record(claim.claim_id, claim),
    lambda claim: replace(claim, proposition="fabricated target with unchanged label")])
def test_claim_resolver_cannot_return_untyped_or_substituted_root_claim(change):
    draft, registrations, registry = fixture()
    registered = tuple(replace(value, scientific_claim_resolver=lambda *_: change(draft.development_study.claims[0]))
                       if value.selection.capability_key == "generic.use" else value for value in registrations)
    with pytest.raises(ValueError, match="exact typed declared root claim"):
        _compile((draft, registered, registry))


@pytest.mark.parametrize("scope_change", [{"world_id": "world.other"}, {"system_id": "system.other"}])
def test_root_claim_membership_does_not_allow_wrong_requirement_domain(scope_change):
    draft, registrations, registry = fixture()
    requirement = replace(draft.requirements[0], scope=replace(draft.requirements[0].scope, **scope_change))
    changed = replace(draft, requirements=(requirement,))
    with pytest.raises(ValueError, match="requirement world or system"):
        _compile((changed, registrations, registry))
