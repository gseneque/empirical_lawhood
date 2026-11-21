# SPDX-License-Identifier: MPL-2.0
"""Public source/authoring trace and explicit workspace boundaries."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.api.investigations import authored_operation_trace, create_local_workspace
from empirical_lawhood.methods.mass_balance_starter import MassSpecification, example_evidence
from empirical_lawhood.methods.mass_balance_starter import bindings, design


def test_complete_origin_trace_preserves_selected_and_unselected_authored_objects(monkeypatch):
    evidence = example_evidence('positive')
    specification = MassSpecification('test.mass.specification', evidence.identity, evidence.scope,
        evidence.independent_unit_ids, Decimal('0.01'))
    draft, _ = design.lower(specification, evidence)
    factories = tuple(operation.provider_factory() for operation in bindings.operation_declarations())
    calls = []
    def selected(selection_ids):
        calls.append(tuple(selection_ids))
        return tuple(factory for factory in factories if factory.registration.selection.selection_id in selection_ids)
    monkeypatch.setattr('empirical_lawhood.api.recursive_operations.selected_operation_factories', selected)
    draft = replace(draft, selected_operation_ids=draft.selected_operation_ids[:1])
    trace = authored_operation_trace(draft, specification=specification.identity)
    assert len(calls) == 1
    assert {row['operation_id'] for row in trace} == {operation.node_id for operation in draft.operations}
    assert sum(row['selected'] for row in trace) == 1
    assert all(row['authored_object'] == specification.identity.to_document() for row in trace)
    assert all(row['implementation']['status'] == 'EXACT_INSTALLED_DECLARATION' for row in trace)
    assert {row['authored_configuration']['value']['object_fingerprint'] for row in trace} == {
        operation.config_identity.object_fingerprint for operation in draft.operations}


def test_trace_labels_changed_implementation_without_substituting_original(monkeypatch):
    evidence = example_evidence('positive')
    specification = MassSpecification('test.mass.specification', evidence.identity, evidence.scope,
        evidence.independent_unit_ids, Decimal('0.01'))
    draft, _ = design.lower(specification, evidence)
    factories = tuple(operation.provider_factory() for operation in bindings.operation_declarations())
    monkeypatch.setattr('empirical_lawhood.api.recursive_operations.selected_operation_factories', lambda ids: factories)
    changed = replace(draft.operations[0], selection=replace(draft.operations[0].selection, implementation_sha256='0'*64))
    draft = replace(draft, operations=(changed,*draft.operations[1:]))
    trace = authored_operation_trace(draft, specification=specification.identity)
    assert trace[0]['implementation']['status'] == 'INSTALLED_IMPLEMENTATION_DIFFERS'
    assert trace[0]['implementation']['implementation_sha256'] == '0'*64
    assert trace[0]['implementation']['module'] is None


def test_workspace_refuses_existing_roots_and_source_containment(tmp_path):
    source = Path(__file__).resolve().parents[1]
    with pytest.raises(FileExistsError):
        create_local_workspace(tmp_path, project_root=source)
    target = source / 'must-not-be-created-by-profile-test'
    with pytest.raises(ValueError, match='forbidden local root'):
        create_local_workspace(target, project_root=source)
    assert not target.exists()


def test_workspace_explicit_invalid_concurrency_is_not_silently_clamped(tmp_path, monkeypatch):
    monkeypatch.setattr('empirical_lawhood.api.investigations.select_experiment_workers', lambda workers: workers or 100)
    with pytest.raises(ValueError, match='registered envelope'):
        create_local_workspace(tmp_path / 'new', project_root=Path(__file__).resolve().parents[1], maximum_parallel_tasks=65)
    assert not (tmp_path / 'new').exists()


def test_public_authoring_accepts_complete_native_study_without_external_operands(tmp_path):
    """Real public prepare/author path, with native work left for its execution phase."""
    from contextlib import nullcontext
    from tempfile import TemporaryDirectory
    from empirical_lawhood.api.classical_matrix_series import create_inputs
    from empirical_lawhood.api.investigations import create_investigation_service, prepare_investigation

    source = Path(__file__).resolve().parents[1]
    # Normal pytest uses /tmp, which the real storage contract deliberately
    # rejects. Keep release-selected external fixtures where selected; for an
    # ordinary test invocation choose and clean a genuinely permitted directory.
    temporary_root = Path('/tmp').resolve()
    parent = source.parent if not source.parent.is_relative_to(temporary_root) else Path.home()
    location = (TemporaryDirectory(prefix='el-native-authoring-control-', dir=parent)
        if tmp_path.resolve().is_relative_to(temporary_root) else nullcontext(str(tmp_path)))
    with location as selected:
        workspace = create_local_workspace(Path(selected) / 'native-study', project_root=source,
            maximum_parallel_tasks=1)
        service = create_investigation_service(project_root=source, operator_profile=workspace.profile_path)
        inputs = create_inputs(project_root=source, output_directory=workspace.scratch_root / 'inputs',
            definition_path=source / 'programmes/foundations/emergent-structure/workflows/classical-series/smoke.json')
        prepared = prepare_investigation(service, specification_path=Path(inputs['specification']),
            source_selection_path=Path(inputs['sources']), environment_id='environment.matrix-classical-series.base')
        assert prepared.executable
        assert not prepared.input_records and not prepared.input_files and not prepared.contribution_dirs
        assert not prepared.draft.external_inputs
        result = service.author(preparation=prepared, output_dir=workspace.artifact_root / 'native-study')
        assert result['specification'] == prepared.specification.to_document()
        assert result['experiment_census'] == dict(prepared.census.role_counts)
