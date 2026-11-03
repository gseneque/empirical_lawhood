# SPDX-License-Identifier: MPL-2.0
"""Small software resource projections, without issue, workers or observations."""

from dataclasses import fields, replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_resources import (
    ProtectedFactorialResourceSelection, bind_protected_factorial_resources,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_entry import (
    ExecutableStudyDefinition, ProposedStudyExtension, ProposedStudyExtensionSet,
)
from empirical_lawhood.runtime.candidate_compiler import bind_standard_candidate_extensions, compile_study_candidate
from empirical_lawhood.runtime.compiler import ProtocolCompilationError, compile_preissue_run_plan
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec,
    NonTimeResourceBudget, RosterCapacityBranchSpec,
)
from empirical_lawhood.runtime.study_extensions import StudyExtensionMaterializationReceipt
from empirical_lawhood.runtime.study_issue import StudyExtensionDecoderRegistration, project_standard_study_extensions
from tests.runtime_platform.test_candidate_compiler import _materialization
from tests.runtime_platform.test_recursive_compiler import Config
from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture


@pytest.fixture(scope="module")
def projected():
    authoring, context = _standard_fixture()
    report = compile_study_candidate(authoring_package=authoring, authoring_materialization=_materialization(), context=context)
    assert report.candidate is not None
    payload = Config("config.software-resource-selection", 3)
    raw = payload.canonical_bytes()
    digest = sha256(raw).hexdigest()
    decoder = StudyExtensionDecoderRegistration("decoder.software-resource-selection", "software.resource-selection",
        "1.0.0", payload.SCHEMA, payload.VERSION, sha256(b"config").hexdigest(), sha256(b"implementation").hexdigest(), 1024)
    proposal = ProposedStudyExtension("extension.software-resource-selection", "software-resource-selection",
        ObjectIdentity.from_record(payload.config_id, payload), len(raw), decoder.decoder_key, decoder.decoder_version,
        decoder.config_sha256, True, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    proposals = ProposedStudyExtensionSet("extensions.software-resource-selection",
        ObjectIdentity.from_record(authoring.package_id, authoring), (proposal.namespace_id,), (proposal,))
    executable = ExecutableStudyDefinition("authoring.software-resource-selection", authoring, proposals)
    candidate = bind_standard_candidate_extensions(base_candidate=report.candidate, authoring_package=executable)
    material = StudyExtensionMaterializationReceipt("materialization.software-resource-selection", proposal.extension_id,
        ObjectIdentity.from_record(proposal.extension_id, proposal), proposal.payload, len(raw), digest,
        ObjectIdentity.from_record(decoder.registration_id, decoder), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    extensions, _, _ = project_standard_study_extensions(candidate=candidate, extension_payload_bytes=(raw,),
        decoder_registrations=(decoder,), extension_materializations=(material,))
    cells = []
    for step in candidate.base_candidate.base_candidate.protocol.steps:
        budget = step.resource_budget
        finite = NonTimeResourceBudget("budget." + step.step_id, budget.cpu_cores, budget.memory_bytes,
            budget.output_bytes, 1, budget.source_scan_bytes)
        cells.append(ExecutionResourceTaskCellSpec("cell." + step.step_id, step.step_id, "child.software-resources",
            None, None, step.maximum_attempts, 0, 0, False, finite, None, None, None))
    cells = tuple(sorted(cells, key=lambda row: row.cell_id))
    branches = tuple(RosterCapacityBranchSpec("branch." + str(index), "group.software-resources",
        "child.software-resources", (cell.cell_id,)) for index, cell in enumerate(cells[:2]))
    selection = ProtectedFactorialResourceSelection("resources.software-selection", cells,
        (ChildResourceTokenLimit("child.software-resources", 0, 0),), branches,
        ("SOFTWARE_RETRY",), ("SOFTWARE_STOP",), None, None, 1,
        max(cell.resource_budget.memory_bytes for cell in cells) * 2, ("lock.software-resources",),
        (ObjectIdentity.from_record(payload.config_id, payload),), sha256(b"resource-policy").hexdigest(), True, True, True, True)
    return SimpleNamespace(selection=selection, extensions=extensions, candidate=candidate, registry=context.base.registry)


def _preissue(projected, envelope, *, extensions=None):
    return compile_preissue_run_plan(run_plan_id="preissue.software-resources",
        candidate_record=projected.candidate.base_candidate.base_candidate,
        candidate=ObjectIdentity.from_record(projected.candidate.candidate_id, projected.candidate), registry=projected.registry,
        implementation_commit="1" * 40, issued_extension_set=projected.extensions if extensions is None else extensions,
        resource_envelope=envelope, jit_census=None, jit_manifest=None)


def test_unbound_canonical_selection_binds_every_original_operational_field_and_actual_extension_record(projected):
    selection = projected.selection
    before = selection.canonical_bytes()
    assert "issued_study_extensions" not in {field.name for field in fields(selection)}
    assert decode_canonical_bytes(before, ProtectedFactorialResourceSelection, maximum_bytes=16384) == selection
    envelope = bind_protected_factorial_resources(selection, issued_extensions=projected.extensions)
    assert {field.name for field in fields(selection)} == {
        field.name for field in fields(ExecutionResourceEnvelopeSpec)} - {"issued_study_extensions"}
    assert all(getattr(envelope, field.name) == getattr(selection, field.name) for field in fields(selection))
    assert envelope.issued_study_extensions == ObjectIdentity.from_record(
        projected.extensions.issued_extension_set_id, projected.extensions)
    assert selection.identity != ObjectIdentity.from_record(envelope.envelope_spec_id, envelope)
    assert selection.canonical_bytes() == before
    plan = _preissue(projected, envelope)
    assert {step.step_id for step in plan.steps} == {cell.task_id for cell in selection.task_cells}


@pytest.mark.parametrize("supplied", ("identity", "mapping", "none"))
def test_only_exact_typed_extension_projection_can_bind_no_identity_or_placeholder(projected, supplied):
    value = {"identity": ObjectIdentity.from_record(projected.extensions.issued_extension_set_id, projected.extensions),
        "mapping": projected.extensions.to_document(), "none": None}[supplied]
    with pytest.raises(TypeError, match="actual typed extension set"):
        bind_protected_factorial_resources(projected.selection, issued_extensions=value)


@pytest.mark.parametrize("damage,reason", (("budget", "budget"), ("task", "topology"), ("attempts", "attempt ceiling")))
def test_actual_preissue_owner_refuses_operational_selection_drift_from_compiled_tasks(projected, damage, reason):
    cell, *rest = projected.selection.task_cells
    if damage == "budget":
        cell = replace(cell, resource_budget=replace(cell.resource_budget, cpu_cores=cell.resource_budget.cpu_cores + 1))
    elif damage == "task":
        cell = replace(cell, task_id="task.unselected-software")
    else:
        cell = replace(cell, maximum_attempts=2 if cell.maximum_attempts == 1 else 1)
    selection = replace(projected.selection, task_cells=(cell, *rest))
    envelope = bind_protected_factorial_resources(selection, issued_extensions=projected.extensions)
    with pytest.raises(ProtocolCompilationError, match=reason):
        _preissue(projected, envelope)


@pytest.mark.parametrize("damage,reason", (("tokens", "maximum demand"), ("branch", "unknown/cross-child"),
    ("aggregate", "memory exceeds"), ("jit", "partial or incompatible")))
def test_complete_envelope_owner_rules_remain_mandatory_at_binding(projected, damage, reason):
    selection = projected.selection
    if damage == "tokens":
        selection = replace(selection, child_token_limits=(replace(selection.child_token_limits[0], physical_execution_token_limit=1),))
    elif damage == "branch":
        first, *rest = selection.roster_capacity_branches
        selection = replace(selection, roster_capacity_branches=(replace(first, cell_ids=("cell.absent-software",)), *rest))
    elif damage == "aggregate":
        selection = replace(selection, aggregate_memory_ceiling_bytes=1)
    else:
        selection = replace(selection, predevelopment_jit_signature_census=selection.non_gating_forecast_records[0])
    with pytest.raises(ValueError, match="failed final envelope validation: .*" + reason):
        bind_protected_factorial_resources(selection, issued_extensions=projected.extensions)


def test_bound_envelope_cannot_be_reused_for_a_different_exact_extension_record(projected):
    envelope = bind_protected_factorial_resources(projected.selection, issued_extensions=projected.extensions)
    changed = replace(projected.extensions, issued_extension_set_id="issued-extensions.other-software-projection")
    with pytest.raises(ProtocolCompilationError, match="another issued extension set"):
        _preissue(projected, envelope, extensions=changed)


@pytest.mark.parametrize("damage", ("cell-type", "budget-type", "parallel-type", "durability"))
def test_unbound_selection_retains_exact_component_and_policy_types(projected, damage):
    selection = projected.selection
    with pytest.raises((TypeError, ValueError)):
        if damage == "cell-type":
            replace(selection, task_cells=list(selection.task_cells))
        elif damage == "budget-type":
            cell, *rest = selection.task_cells
            replace(selection, task_cells=(replace(cell, resource_budget=SimpleNamespace()), *rest))
        elif damage == "parallel-type":
            replace(selection, maximum_parallel_tasks=True)
        else:
            replace(selection, nonrefundable_reservations=1)
