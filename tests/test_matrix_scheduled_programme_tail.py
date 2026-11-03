# SPDX-License-Identifier: MPL-2.0
"""Complete global tail over explicitly exposed software completion fixtures.

Stored wave bytes and custody are real; completion labels and source credentials
are hypothetical. No issue, numerical execution, reveal or qualified parent is
created by this public author/load/provider check.
"""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    programme_calibration as calibration, programme_calibration_bindings as bindings,
    programme_tail_composition as composition,
)
from empirical_lawhood.api import matrix_scheduled_programme as public, recursive_prospective_authoring as author
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from empirical_lawhood.runtime.plans import CandidateExecutionPlan, ExecutionPlan
from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_tail_freeze import TASK_ID as TAIL_FREEZE_TASK_ID
from tests.programme_entry_support import programme_scientific_root, qualify_programme_draft
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_scheduled_calibration import TEST_BUDGET
from tests.test_matrix_scheduled_default_integration import _application
from tests.test_matrix_scheduled_programme import _synthetic_cases
from tests.test_matrix_scheduled_programme_calibration import stored_wave_custody
from tests.test_matrix_scheduled_programme_graph import (
    bank as bank, programme576_bank, provenance as provenance, response_bank as response_bank,
    scheduled as scheduled, stock as stock,
)


def tail_bundle(response_bank):
    programme, bank, _ = programme576_bank(response_bank)
    results, custody, plans = stored_wave_custody(response_bank[0], programme, _synthetic_cases(programme))
    root, reference = programme_scientific_root(response_bank, programme, bank)
    prototype, compatibility = _fixture()
    old_cutoffs = {cutoff.cutoff_id for cutoff in prototype.experiment.information_cutoffs}
    tasks = composition.programme_tail_task_ids()
    owners = [(f'obligation.software.programme-tail.{index}', task) for index, task in enumerate(tasks)]
    owners.extend((row.obligation_id, TAIL_FREEZE_TASK_ID if row.obligation_id in
        ('freeze-complete-protocol', 'prepare-independent-units') else calibration.QUALIFY_TASK_ID)
        for row in compatibility.templates[0].coverage.bindings if row.obligation_id not in old_cutoffs)
    owners.extend((case.information_cutoff.cutoff_id, calibration.CALIBRATE_TASK_ID) for case in programme.cases)
    draft, records = composition.programme_tail_draft(root=root, programme=programme, bank=bank,
        wave_results=results, wave_custody=custody, execution_plans=plans,
        proof_owners=tuple(sorted(set(owners))), operational_budgets=dict.fromkeys(tasks,
            replace(TEST_BUDGET, output_bytes=16*1024**2)), calibration_id='calibration.software.programme-full64',
        draft_id='draft.software.programme-complete-tail')
    draft, qualifications = qualify_programme_draft(draft, records, reference)
    roles = {value.input_id: value.scientific_role for value in draft.external_inputs}
    draft = replace(draft, prospective_draft=replace(draft.prospective_draft,
        source_materializations=tuple(replace(value, role=SourceMaterializationRole.RETAINED_HISTORY)
            if roles[value.source_id] == 'HISTORY' else value for value in draft.prospective_draft.source_materializations)))
    return (draft, qualifications, records, None), programme, bank, results, custody, plans


def test_complete_global_tail_public_author_load_provider_and_original_custody_refusals(response_bank, tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments

    def blocked(*args, **kwargs):
        pytest.fail('global tail author/load/provider proof entered numerical science or fitting')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(response_science, 'native_responses', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_error_model', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_scheduled_error_model', blocked)
    bundle, programme, bank, results, custody, plans = tail_bundle(response_bank)
    plane = response_bank[0]
    draft, _, records, _ = bundle
    assert len(draft.operations) == 3 and len(draft.external_inputs) == 65
    assert set(draft.selected_operation_ids) == set(composition.programme_tail_task_ids())
    assert not any(value.payload_schema in (CandidateExecutionPlan.SCHEMA, ExecutionPlan.SCHEMA)
        for value in draft.external_inputs)
    assert not any(type(value) in (CandidateExecutionPlan, ExecutionPlan) for value in records.values())
    for result, binding, plan in zip(results, custody, plans, strict=True):
        loaded_result, loaded_plan = calibration.authenticate_wave_custody(plane, binding)
        assert (loaded_result, loaded_plan) == (result, plan)
        calibration.validate_wave_custody(programme, loaded_result, binding, loaded_plan)
    application = _application(response_bank, tmp_path, monkeypatch, draft_bundle=bundle,
        formal_method_capability_key=bindings.NAMESPACE+'.calibration-qualify')
    arguments, compilation, _ = application
    assert len(compilation.template.protocol.steps) == 3
    assert len(compilation.selected_scientific_projection.canonical_bytes()) <= 16*1024**2
    assert len(arguments['spec'].canonical_bytes()) <= 32*1024**2
    protected = {plane.root.resolve(value.publication.materialization.relative_path, for_write=False) for value in custody}
    original_open = Path.open

    def no_protected_result_open(path, *args, **kwargs):
        if path in protected:
            pytest.fail('programme preparation read an original protected wave outcome before issued authority')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', no_protected_result_open)
    destination = Path(plane.root.contract.canonical_path)/'complete-programme-tail-authoring'
    authored = public.author_scheduled_programme_prospective(programme=programme, bank=bank,
        wave_custody=custody, **arguments, output_dir=destination)
    assert authored['task_count'] == 3 and authored['scientific_authority'] == 'NONE'
    assert authored['native_contact'] == 'none'
    monkeypatch.setattr(author, 'resolve_authoring_directory',
        lambda directory, **kwargs: (Path(directory).resolve(), plane.root.contract))
    loaded = public.load_scheduled_programme_prospective(programme=programme, bank=bank,
        wave_custody=custody, directory=destination, root=arguments['project_root'], storage_profile=object(), artifact_writer=plane)
    proof = author.prove_recursive_prospective_handoff(loaded)
    assert proof['task_count'] == 3 and proof['scientific_execution_performed'] is False
    assert all(binding.prior_execution is None for binding in custody)
    print({'programme_global_tail_software': {'task_count': 3, 'wave_count': len(custody),
        'scientific_projection_bytes': len(compilation.selected_scientific_projection.canonical_bytes()),
        'draft_bytes': len(compilation.draft.canonical_bytes()),
        'operational_spec_bytes': len(arguments['spec'].canonical_bytes()), 'scientific_authority': 'NONE'}})

    # Exact original plan bytes remain an independently authenticated prerequisite
    # despite their omission from the bounded runtime summary ports.
    original_plan = plane.root.resolve(custody[0].execution_plan_publication.materialization.relative_path, for_write=False)
    original_bytes = original_plan.read_bytes()
    original_plan.write_bytes(original_bytes[:-1]+b' ')
    try:
        with pytest.raises((ValueError, ArtifactPlaneError)):
            public.author_scheduled_programme_prospective(programme=programme, bank=bank,
                wave_custody=custody, **arguments, output_dir=Path(plane.root.contract.canonical_path)/'refused-programme-tail')
        assert not (Path(plane.root.contract.canonical_path)/'refused-programme-tail').exists()
        with pytest.raises((ValueError, ArtifactPlaneError)):
            public.load_scheduled_programme_prospective(programme=programme, bank=bank,
                wave_custody=custody, directory=destination, root=arguments['project_root'], storage_profile=object(), artifact_writer=plane)
    finally:
        original_plan.write_bytes(original_bytes)

    budgets = {operation.node_id: operation.resource_budget for operation in draft.operations}
    owners = tuple((owner, operation.node_id) for operation in draft.operations for owner in operation.obligation_ids)
    common = dict(root=draft.prospective_draft, programme=programme, bank=bank, proof_owners=owners,
        operational_budgets=budgets, calibration_id='calibration.software.programme-full64', draft_id='draft.refused.tail')
    with pytest.raises(ValueError, match='omits, duplicates or reorders'):
        composition.programme_tail_draft(**common, wave_results=results[:-1], wave_custody=custody[:-1], execution_plans=plans[:-1])
    with pytest.raises(ValueError, match='census|custody|plan'):
        composition.programme_tail_draft(**common, wave_results=results, wave_custody=custody,
            execution_plans=(plans[1], plans[0], *plans[2:]))
