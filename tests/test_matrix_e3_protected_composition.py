# SPDX-License-Identifier: MPL-2.0
"""Closed graph controls over disclosed originals, without scientific entry."""

from dataclasses import replace
from pathlib import Path
import pickle

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_composition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_adjudication import ProtectedE3AdjudicationConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_feature_bindings import ProtectedE3FeatureConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_original_publications import ORIGINAL_PUBLICATION_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import ProtectedE3ResponseConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3SourceConfig, ProtectedE3SourcePhase
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import ProtectedE3StatisticalConfig
from empirical_lawhood.api.experiment_preparation import prepare_experiment
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import bind_protected_e3_experiment_inputs
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursiveScientificRootContext, decode_recursive_config_input, project_recursive_config_inputs, validate_recursive_scientific_roots,
)
from tests.test_matrix_e3_protected_public_lowering import prepared_case


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    selected = prepared_case(tmp_path_factory.mktemp("literal-composition"))
    inputs = bind_protected_e3_experiment_inputs(selected.specification,
        {"protected-selection": selected.selection}, files=selected.files)
    prepared = prepare_experiment(selected.specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=ExecutionSelection(), protocol_bytes=selected.candidate_bytes)
    selected.preparation = prepared
    declarations = {row.capability_key: row for row in owner.operation_declarations()}
    selected.registrations = {operation.node_id: declarations[operation.selection.capability_key].registration()
        for operation in prepared.draft.operations}
    selected.configs = project_recursive_config_inputs(tuple(
        decode_recursive_config_input(operation, selected.registrations[operation.node_id])
        for operation in prepared.draft.operations), selected.registrations)
    return selected


def validate(case, **changes):
    arguments = dict(root=case.preparation.draft.prospective_draft, config_inputs=case.configs,
        registrations_for_node=case.registrations, requirements=(), connections=(),
        links=case.preparation.draft.links, qualifications=case.selection.qualifications,
        known_design_inputs=case.preparation.draft.prospective_draft.design_inputs,
        external_inputs=case.preparation.draft.external_inputs)
    arguments.update(changes)
    return validate_recursive_scientific_roots(**arguments)


def test_all16_declarations_install_the_same_global_root_and_original_publication_gate():
    declarations = owner.operation_declarations()
    assert len(declarations) == 16 and len({row.capability_key for row in declarations}) == 16
    assert pickle.loads(pickle.dumps(owner.scientific_root_validator)) is owner.scientific_root_validator
    for declaration in declarations:
        assert declaration.scientific_hooks.scientific_root_validator is owner.scientific_root_validator
        assert declaration.publication_requirements == (ORIGINAL_PUBLICATION_REQUIREMENT,)
        assert declaration.runner_factory().manifest == declaration.manifest()


def test_complete_current_graph_and_exact_qualified_sources_validate_without_io(case, monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *_a, **_k: pytest.fail("root validation read scientific bytes"))
    current = owner.validate_current_configs(case.configs)
    assert len(current.by_task) == 286 and len(current.roots) == 28
    assert owner.validate_current_configs(case.configs) is current
    validate(case)
    # Repeat the shared root pass over exactly the immutable inputs. The root
    # cache avoids rewalking every qualifier and full graph per operation.
    validate(case)


def test_terminal_adjudication_keeps_the_complete_assessment_and_actual_reveal_boundary(case):
    current = owner.validate_current_configs(case.configs)
    config = next(row.record for row in case.configs if type(row.record) is ProtectedE3AdjudicationConfig)
    expected = owner.expected_producers(config, case.configs)
    assert expected == {"specification": None, "allocation": None,
        "assessment": (owner.statistical_task_id(config.specification, config.allocation, "assess"), "product")}
    declaration = current.declarations["matrix-e3-protected.adjudicate"]
    assert declaration.stage is ScientificStage.EVALUATE and declaration.kind is CapabilityKind.EVALUATOR
    assert declaration.execution_properties.barrier is BarrierKind.REVEAL
    assert declaration.scientific_hooks.adjudication_output_id == "adjudication"
    assert len(declaration.outputs) == 1 and declaration.outputs[0].payload_schema == ScientificAdjudicationRecord.SCHEMA
    assert current.declarations["matrix-e3-protected.assess"].stage is ScientificStage.FALSIFY


@pytest.mark.parametrize("damage", ("model-freeze", "calibration-freeze", "prefix-phase", "feature", "response-score", "forecast", "adjudication"))
def test_config_census_refuses_missing_freezes_and_whole_root_members_before_io(case, monkeypatch, damage):
    monkeypatch.setattr(Path, "read_bytes", lambda *_a, **_k: pytest.fail("refused root read scientific bytes"))
    predicates = {
        "model-freeze": lambda config: type(config) is ProtectedE3StatisticalConfig and config.operation == "freeze" and config.mode == "model",
        "calibration-freeze": lambda config: type(config) is ProtectedE3StatisticalConfig and config.operation == "freeze" and config.mode == "calibration",
        "prefix-phase": lambda config: type(config) is ProtectedE3SourceConfig and config.phase is ProtectedE3SourcePhase.CHECK,
        "feature": lambda config: type(config) is ProtectedE3FeatureConfig,
        "response-score": lambda config: type(config) is ProtectedE3ResponseConfig and config.operation == "response-score",
        "forecast": lambda config: type(config) is ProtectedE3StatisticalConfig and config.operation == "forecast",
        "adjudication": lambda config: type(config) is ProtectedE3AdjudicationConfig,
    }
    missing = next(row for row in case.configs if predicates[damage](row.record))
    with pytest.raises(ValueError, match="wave"):
        owner.validate_current_configs(tuple(row for row in case.configs if row is not missing))


@pytest.mark.parametrize("port", ("error", "physical", "models", "frozen", "responses", "assessment"))
def test_cold_graph_refuses_bypassed_actual_forecasts_freezes_and_native_receipts(case, port):
    draft = case.preparation.draft
    edge = next(edge for edge in draft.links if edge.consumer_input_id == port and edge.producer_node_id is not None)
    foreign = replace(edge, producer_node_id="matrix-e3-protected.foreign.producer")
    links = tuple(foreign if row is edge else row for row in draft.links)
    with pytest.raises(ValueError, match="producer|another configuration or lifecycle"):
        validate(case, links=links)


@pytest.mark.parametrize("damage", ("qualification", "source-ref", "external-hash", "external-access", "root-units", "root-world", "design-pin"))
def test_root_refuses_changed_ordinary_custody_population_and_numerical_scope(case, damage):
    root = case.preparation.draft.prospective_draft
    changes = {}
    if damage == "qualification":
        changes["qualifications"] = case.selection.qualifications[1:]
    elif damage == "source-ref":
        root = replace(root, source_materializations=root.source_materializations[1:])
    elif damage in ("external-hash", "external-access"):
        external = case.preparation.draft.external_inputs[0]
        changed = replace(external, expected_content_sha256="f" * 64) if damage == "external-hash" else replace(
            external, outcome_access=next(value for value in type(external.outcome_access) if value != external.outcome_access))
        changes["external_inputs"] = (changed, *case.preparation.draft.external_inputs[1:])
    elif damage == "root-units":
        root = replace(root, evaluation_unit_ids=root.evaluation_unit_ids[1:])
    elif damage == "root-world":
        from empirical_lawhood.kernel.worlds import WorldKind
        root = replace(root, system=replace(root.system, world=replace(root.system.world, kind=WorldKind.ANALYTIC_REFERENCE)))
    else:
        fit = owner.validate_current_configs(case.configs).fit
        root = replace(root, design_inputs=tuple(row for row in root.design_inputs if row.object_identity != fit.specification))
    with pytest.raises(ValueError, match="protected E3"):
        validate(case, root=root, **changes)


def test_current_context_refuses_changed_declared_stage_or_complete_native_census(case):
    current = owner.validate_current_configs(case.configs)
    config = next(row.record for row in case.configs if type(row.record) is ProtectedE3SourceConfig
        and row.record.phase is ProtectedE3SourcePhase.PREFIX)
    declaration = current.declarations["matrix-e3-protected.prefix"]
    context = RecursiveScientificRootContext(case.preparation.draft.prospective_draft, owner._task(config),
        declaration.stage, declaration.outcome_access, declaration.visibility_ceiling,
        declaration.scientific_hooks.scientific_unit_ids(config), current.unit_censuses["prefix"], False,
        (), (), case.selection.qualifications, case.preparation.draft.prospective_draft.design_inputs,
        case.configs, case.preparation.draft.links, case.preparation.draft.external_inputs)
    with pytest.raises(ValueError, match="declared phase"):
        owner.scientific_root_validator(config, context)
