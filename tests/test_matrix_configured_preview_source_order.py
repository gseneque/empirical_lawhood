# SPDX-License-Identifier: MPL-2.0
"""Transient E3 preview ordering over unchanged disclosed public metadata.

The fixture's existing software qualification/source records remain disclosed
TEST inputs. Roster controls stop before prospective source capture. The full
hook control uses real source/candidate/resource owners and stops before handoff
authoring, issue or execution. No worker, native effect or authority is created.
"""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
    RESOURCE_BINDING_DEPENDENCY, derive_protected_e3_design_inputs,
)
from empirical_lawhood.api import prospective_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.runtime.experiment_preparation import DependencyKind
from tests.test_matrix_configured_protected_public_preparation import public_case  # noqa: F401
from tests.test_matrix_researcher_programme_deferred_authoring import _prepare
from tests.test_matrix_researcher_programme import ROOT


class _ReachedAfterExactRoster(RuntimeError):
    pass


@pytest.fixture(scope='module', autouse=True)
def no_native_effects():
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor

    def forbidden(*_args, **_kwargs):
        raise AssertionError('source-order control entered a worker/native effect')

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(LocalProcessExecutor, 'execute', forbidden)
        patch.setattr(LocalProcessExecutor, 'execute_deadline_free', forbidden)
        patch.setattr(parameter_source, 'acquire_parameter_history', forbidden)
        yield


@pytest.fixture(scope='module')
def ordered_preparation(public_case):  # noqa: F811
    # Copy only the operational transport order. Every canonical config body,
    # source identity, threshold, denominator and qualification stays exact.
    selection = replace(public_case.selection, source_configs=tuple(sorted(
        public_case.selection.source_configs, key=lambda row: row.source_id)))
    case = SimpleNamespace(**{**vars(public_case), 'selection': selection})
    service = ExperimentProgrammeService(ROOT, case.plane, SimpleNamespace(maximum_parallel_tasks=4))
    _sources, prepared = _prepare(case, service)
    assert tuple((row.code, row.kind) for row in prepared.dependencies) == (
        (RESOURCE_BINDING_DEPENDENCY, DependencyKind.SOFTWARE),)
    actual = tuple(row.fingerprint() for row in selection.source_configs)
    expected = tuple(sorted({row.source_config_sha256 for row in prepared.draft.prospective_draft.source_materializations}))
    assert len(actual) > 1 and len(actual) == len(set(actual))
    assert actual != expected and tuple(sorted(actual)) == expected
    return case, service, prepared


def test_configured_authoring_projects_only_preview_source_order(ordered_preparation, monkeypatch):
    case, service, prepared = ordered_preparation
    selected = case.selection
    before = selected.canonical_bytes(), prepared.draft.canonical_bytes()
    original_configs = selected.source_configs
    config_bytes = tuple(row.canonical_bytes() for row in original_configs)
    actual_preview = prospective_experiment.preview_prepared_prospective_experiment_candidate
    observed, reached = [], []

    def stop_before_capture(*_args, **_kwargs):
        reached.append(True)
        raise _ReachedAfterExactRoster('real generic SHA roster accepted before source capture')

    def inspect_preview(**kwargs):
        rows = kwargs['source_configs']
        assert kwargs['preparation'] is prepared
        assert tuple(row.fingerprint() for row in rows) == tuple(sorted(row.fingerprint() for row in original_configs))
        assert {row.source_id: row.canonical_bytes() for row in rows} == {
            row.source_id: row.canonical_bytes() for row in original_configs}
        observed.append(rows)
        return actual_preview(**kwargs)

    monkeypatch.setattr(prospective_experiment, 'capture_target_closure', stop_before_capture)
    monkeypatch.setattr(prospective_experiment, 'preview_prepared_prospective_experiment_candidate', inspect_preview)
    destination = Path(case.plane.root.contract.canonical_path) / 'preview-source-order-only'
    with pytest.raises(_ReachedAfterExactRoster, match='real generic SHA roster accepted'):
        service.author(preparation=prepared, output_dir=destination)
    assert len(observed) == 1 and reached == [True] and not destination.exists()
    assert selected.source_configs is original_configs
    assert config_bytes == tuple(row.canonical_bytes() for row in selected.source_configs)
    assert before == (selected.canonical_bytes(), prepared.draft.canonical_bytes())
    # This pure later mapping keys configurations by SHA even in source-ID
    # order. The returned operational preparation separately requires SHA order.
    design = derive_protected_e3_design_inputs(prepared)
    _external, _sources, _files, configs = prospective_experiment._inputs(prepared, design, original_configs)
    assert tuple(configs) == tuple(row.fingerprint() for row in original_configs)
    assert {digest: value.payload for digest, value in configs.items()} == {
        row.fingerprint(): row.canonical_bytes() for row in original_configs}


@pytest.mark.parametrize('damage', ('missing', 'duplicate', 'substituted'))
def test_generic_preview_keeps_exact_source_census_guard(ordered_preparation, monkeypatch, damage):
    case, _service, prepared = ordered_preparation
    rows = tuple(sorted(case.selection.source_configs, key=lambda row: row.fingerprint()))
    if damage == 'missing':
        changed = rows[:-1]
    elif damage == 'duplicate':
        changed = tuple(sorted((*rows, rows[0]), key=lambda row: row.fingerprint()))
    else:
        foreign = replace(rows[0], config_id=rows[0].config_id + '.foreign')
        changed = tuple(sorted((foreign, *rows[1:]), key=lambda row: row.fingerprint()))

    def forbidden(*_args, **_kwargs):
        raise AssertionError('incorrect source roster reached source capture')

    monkeypatch.setattr(prospective_experiment, 'capture_target_closure', forbidden)
    design = derive_protected_e3_design_inputs(prepared)
    before = case.selection.canonical_bytes()
    with pytest.raises(ValueError, match='exact selected SHA-keyed source configuration roster'):
        prospective_experiment.preview_prepared_prospective_experiment_candidate(preparation=prepared,
            design_inputs=design, source_configs=changed, project_root=ROOT, artifact_writer=case.plane)
    assert case.selection.canonical_bytes() == before


@pytest.fixture(scope='module')
def full_authoring_return(ordered_preparation, no_native_effects):
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import runtime
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    case, _service, original = ordered_preparation
    design = derive_protected_e3_design_inputs(original)
    # A real candidate preview requires the exact ordinary prospective source
    # closure. This changes only the explicit operational execution selection.
    captured = prospective_experiment.capture_target_closure(ROOT, design.spec_id + '.source-closure')
    prepared = replace(original, execution=replace(original.execution,
        source_snapshot=ObjectIdentity.from_record('recursive-member.implementation', captured.closure)))
    selected = case.selection
    before = (selected.canonical_bytes(), prepared.draft.canonical_bytes(),
        tuple((key, record.canonical_bytes()) for key, record in prepared.design_records))
    destination = Path(case.plane.root.contract.canonical_path) / 'full-preview-return-only'
    assert destination.is_relative_to(Path('/media/chevre/EL'))
    assert not destination.exists()
    result = runtime.prepare_protected_e3_experiment_authoring(prepared, project_root=ROOT,
        artifact_writer=case.plane, output_dir=destination)
    return case, prepared, result, before, destination


def test_actual_authoring_hook_returns_typed_sha_order_without_changing_selected_science(full_authoring_return):
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
    from empirical_lawhood.runtime.recursive_prospective import (
        RecursiveProspectiveAuthoringSpec, RecursiveProspectiveCandidatePreview,
    )

    case, prepared, result, before, destination = full_authoring_return
    assert type(result) is ExperimentPreparation and result.executable
    assert type(result.prospective_spec) is RecursiveProspectiveAuthoringSpec
    assert type(result.prospective_candidate_preview) is RecursiveProspectiveCandidatePreview
    result.__post_init__()
    expected = tuple(sorted(case.selection.source_configs, key=lambda row: row.fingerprint()))
    assert result.source_configs == expected
    assert tuple(row.source_id for row in case.selection.source_configs) == tuple(sorted(
        row.source_id for row in case.selection.source_configs))
    assert case.selection.source_configs != expected
    assert {row.source_id: row.canonical_bytes() for row in result.source_configs} == {
        row.source_id: row.canonical_bytes() for row in case.selection.source_configs}
    for field in ('specification', 'census', 'allocation', 'draft', 'input_records', 'input_files',
            'execution', 'specification_record', 'design_records', 'contribution_dirs', 'origins',
            'assessment_limitations', 'authoring_source_records'):
        assert getattr(result, field) == getattr(prepared, field), field
    assert before == (case.selection.canonical_bytes(), prepared.draft.canonical_bytes(),
        tuple((key, record.canonical_bytes()) for key, record in prepared.design_records))
    preview = result.prospective_candidate_preview
    assert result.prospective_spec.resources.issued_study_extensions == ObjectIdentity.from_record(
        preview.issued_extensions.issued_extension_set_id, preview.issued_extensions)
    assert prepared.prospective_spec is None and prepared.source_configs == ()
    assert not destination.exists()
    run_root = Path(case.plane.root.contract.canonical_path) / 'runs'
    assert not run_root.exists()


def test_returned_operational_preparation_refuses_selected_id_order(full_authoring_return):
    case, _prepared, result, _before, _destination = full_authoring_return
    assert result.source_configs != case.selection.source_configs
    with pytest.raises(ValueError, match='prospective source configurations change the exact selected digest roster'):
        replace(result, source_configs=case.selection.source_configs)



def test_programme_child_source_uses_actual_configured_design_id(ordered_preparation):
    from empirical_lawhood.api.composite_experiment_programme import prepared_component_source_snapshot
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.infrastructure.source_closure import capture_target_closure
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    _case, _service, original = ordered_preparation
    parent = ObjectIdentity.from_record('recursive-member.implementation', implementation_binding(ROOT))
    prepared = replace(original, execution=replace(original.execution, source_snapshot=parent))
    design = derive_protected_e3_design_inputs(prepared)
    assert design.spec_id != 'prospective.' + prepared.specification_record.specification_id
    actual = prepared_component_source_snapshot(ROOT, prepared)
    expected = capture_target_closure(ROOT, design.spec_id + '.source-closure').closure
    assert actual == ObjectIdentity.from_record('recursive-member.implementation', expected)
    assert original.draft == prepared.draft
