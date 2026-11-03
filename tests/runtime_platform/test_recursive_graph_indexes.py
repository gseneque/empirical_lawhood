# SPDX-License-Identifier: MPL-2.0
"""Ordered graph lowering and independent proof over disclosed pure metadata.

No source capture, native entry, publication, actual grant or qualification is
performed. Work counts concern these lowering/index boundaries, not whole-run
capacity or every independent constructor's graph validation.
"""
from dataclasses import replace
import sys

import pytest

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec
from empirical_lawhood.runtime.candidate_compiler import CandidateGraphEdge, StudyTemplate
from empirical_lawhood.runtime.plans import ScientificInputRole
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.scientific_graph_preservation import (
    _scientific_graph_indexes, prove_development_graph_parity,
)
from tests.runtime_platform.test_development_original_input_contracts import Config, _case


def _fanout(count):
    draft, registrations, registry = _case()
    source, consumer = draft.operations
    registrations = tuple(replace(value, config_input_parents=lambda config, records: config.parents)
        for value in registrations)
    registrations = (replace(registrations[0], outputs=tuple(
        replace(registrations[0].outputs[0], output_id="result-" + suffix) for suffix in ("a", "z"))),
        replace(registrations[1], input_ports=(
        replace(registrations[1].input_ports[0], minimum_count=2, maximum_count=2),)))
    operations, links = [source], []
    for index in range(count):
        node = f"use-{index:04d}"
        config = Config("config." + node, index, ())
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=consumer.selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node,),
            resource_budget=consumer.resource_budget))
        for suffix in ("a", "z"):
            # Global order deliberately interleaves each consumer's two edges.
            links.append(RecursiveInputLink(f"edge.{suffix}.{index:04d}", node, "operand." + suffix,
                source.node_id, "result-" + suffix, scientific_role="MODEL"))
    return replace(draft, operations=tuple(operations), links=tuple(sorted(links, key=lambda value: value.edge_id)),
        selected_operation_ids=tuple(value.node_id for value in operations)), registrations, registry


def _compile(count=3):
    draft, registrations, registry = _fanout(count)
    return compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


def _prove(compiled, *, graph=None):
    template, run = compiled.template, compiled.run_plan
    if graph is not None:
        ids = {edge.edge_id for edge in graph.edges}
        coverage = replace(template.coverage, bindings=tuple(replace(binding,
            contributor_edge_ids=tuple(edge for edge in binding.contributor_edge_ids if edge in ids))
            for binding in template.coverage.bindings))
        template = replace(template, graph=graph, coverage=coverage)
        # Keep the changed packet internally pinned so the independent proof
        # reaches the actual edge census/contract rather than a stale hash.
        run = replace(run, template=ObjectIdentity.from_record(template.template_key, template))
    return prove_development_graph_parity(draft=compiled.draft,
        selection=compiled.selected_scientific_projection, template=template,
        run_plan=run, execution_plan=compiled.execution_plan, registry=compiled.registry)


def test_lowering_coverage_and_independent_proof_retain_final_inherited_custody_and_order():
    compiled = _compile()
    graph = compiled.template.graph
    assert tuple(edge.edge_id for edge in graph.edges) == tuple(sorted(edge.edge_id for edge in graph.edges))
    coverage = {value.proof_owner_node_id: value for value in compiled.template.coverage.bindings}
    steps = {step.step_id: step for step in compiled.run_plan.steps}
    for task in compiled.execution_plan.tasks:
        incoming = tuple(edge for edge in graph.edges if edge.consumer_node_id == task.task_id)
        assert coverage[task.task_id].contributor_edge_ids == tuple(edge.edge_id for edge in incoming)
        assert tuple(value.edge_id for value in task.scientific_inputs) == tuple(edge.edge_id for edge in incoming)
        assert steps[task.task_id].scientific_inputs == task.scientific_inputs
        for edge, value in zip(incoming, task.scientific_inputs, strict=True):
            assert (value.outcome_access, value.visibility_ceiling) == (edge.outcome_access, edge.visibility_ceiling)
        if task.task_id != "source":
            operands = tuple(edge for edge in incoming if edge.scientific_role is ScientificInputRole.MODEL)
            assert tuple(edge.consumer_input_id for edge in operands) == ("operand.a", "operand.z")
            assert all(edge.outcome_access is OutcomeAccess.EVALUATION_SEALED for edge in operands)
            configuration, = (edge for edge in incoming if edge.scientific_role is ScientificInputRole.CONFIGURATION)
            assert configuration.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        assert all((output.outcome_access, output.visibility_ceiling) == (
            OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY) for output in task.outputs)
    assert _prove(compiled) == compiled.proof


@pytest.mark.parametrize("count", (64, 128))
def test_lowering_consumer_lookup_work_is_bounded_by_selected_links_and_final_edges(monkeypatch, count):
    counts = {"links": 0, "edges": 0}
    lowering_codes = {compile_recursive_wave.__code__, StudyTemplate._validate_protocol_graph_parity.__code__}

    def counted(kind, key):
        original = kind.__getattribute__

        def read(instance, name):
            if name == "consumer_node_id":
                frame = sys._getframe(1)
                while frame is not None and frame.f_code.co_name in ("<genexpr>", "<listcomp>", "<dictcomp>"):
                    frame = frame.f_back
                if frame is not None and frame.f_code in lowering_codes:
                    counts[key] += 1
            return original(instance, name)

        monkeypatch.setattr(kind, "__getattribute__", read)

    counted(RecursiveInputLink, "links")
    counted(CandidateGraphEdge, "edges")
    compiled = _compile(count)
    # These generous linear limits include the actual template constructor and
    # local-port checks, but reject full link/edge scans for every node.
    assert counts["links"] <= 16 * len(compiled.selected_scientific_projection.links)
    assert counts["edges"] <= 16 * len(compiled.template.graph.edges)
    assert compiled.proof.node_count == count + 1


class CountedEdges(tuple):
    def __new__(cls, values):
        instance = super().__new__(cls, values)
        instance.visits = 0
        return instance

    def __iter__(self):
        for edge in super().__iter__():
            self.visits += 1
            yield edge


@pytest.mark.parametrize("count", (16, 32))
def test_proof_indexes_traverse_supplied_final_graph_once_and_keep_exact_objects(count):
    compiled = _compile(count)
    edges = CountedEdges(compiled.template.graph.edges)
    graph = replace(compiled.template.graph, edges=edges)
    edges.visits = 0
    by_id, incoming, external = _scientific_graph_indexes(graph)
    assert edges.visits == len(edges)
    assert tuple(by_id) == tuple(edge.edge_id for edge in compiled.template.graph.edges)
    assert tuple(external) == tuple(value.input_id for value in graph.external_inputs)
    for node in graph.nodes:
        expected = tuple(edge for edge in compiled.template.graph.edges if edge.consumer_node_id == node.node_id)
        assert incoming[node.node_id] == expected
        assert all(actual is original for actual, original in zip(incoming[node.node_id], expected, strict=True))
    second, _, _ = _scientific_graph_indexes(graph)
    assert second is not by_id


@pytest.mark.parametrize("damage", ("missing-edge", "role", "logical-identity", "custody"))
def test_independent_proof_refuses_supplied_final_graph_thinning_or_substitution(damage):
    compiled = _compile()
    original = next(edge for edge in compiled.template.graph.edges if edge.edge_id == "edge.a.0000")
    if damage == "missing-edge":
        edges = tuple(edge for edge in compiled.template.graph.edges if edge is not original)
    else:
        changed = replace(original,
            **({"scientific_role": ScientificInputRole.HISTORY} if damage == "role" else
               {"logical_artifact_id": "scientific.foreign.result"} if damage == "logical-identity" else
               {"outcome_access": OutcomeAccess.DEVELOPMENT_VISIBLE}))
        edges = tuple(changed if edge is original else edge for edge in compiled.template.graph.edges)
    graph = replace(compiled.template.graph, edges=edges)
    with pytest.raises(ValueError, match="scientific edge census|edge role or endpoints|scientific step"):
        _prove(compiled, graph=graph)


@pytest.mark.parametrize("member", ("edges", "external_inputs"))
def test_proof_index_refuses_duplicate_supplied_identity_instead_of_overwriting(member):
    graph = _compile().template.graph
    original = getattr(graph, member)
    # Supply corrupt retained metadata directly to the index boundary; using a
    # normal constructor would refuse before testing dictionary deduplication.
    graph = replace(graph)
    object.__setattr__(graph, member, (*original, original[0]))
    with pytest.raises(ValueError, match="repeats an exact"):
        _scientific_graph_indexes(graph)
