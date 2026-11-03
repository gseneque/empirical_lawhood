# SPDX-License-Identifier: MPL-2.0
"""Source operand discovery sequencing only; no scientific admission is mocked."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as owner
from tests.runtime_platform.test_recursive_compiler import fixture
from tests.runtime_platform.test_prospective_preparation_contract import prepared  # noqa: F401


def selection(monkeypatch):
    draft, _, _ = fixture()
    specification = SimpleNamespace(specification_id="specification.selected-wave", component_id="wave.selected", wave_id="wave.selected")
    declaration = SimpleNamespace(programme=object(), root=SimpleNamespace(campaign=draft.campaign))
    preparation = SimpleNamespace(qualifications=(), source_configs=())
    evidence = SimpleNamespace(source=SimpleNamespace(pipeline=SimpleNamespace(
        pipeline_config=SimpleNamespace(profile=SimpleNamespace(
            observation_operator="operator.disclosed-source-sequencing")))))
    plan = SimpleNamespace(declaration=declaration, bank=object(), evidence=evidence, preparation=preparation,
        structure=SimpleNamespace(secondary_target=object()),secondary_readout=object())
    class DisclosedResolvedInputs(SimpleNamespace):
        # This fixture tests sequencing, never programme/publication admission.
        def __post_init__(self):
            pass
    monkeypatch.setattr(owner,"ResolvedSelectedE4ComponentInputs",DisclosedResolvedInputs)
    inputs = DisclosedResolvedInputs(plan=plan,component_id=specification.component_id,
        collection=None,declaration_publication=object())
    observed = []
    records, arrays = (), ()
    def lower(*args, **kwargs):
        observed.append((args, kwargs))
        return SimpleNamespace(draft=draft, input_records=records, input_artifacts=arrays)
    monkeypatch.setattr(owner, "component_specification", lambda selected, component: specification)
    monkeypatch.setattr(owner.native, "lower_selected_e4_protected_wave", lower)
    # This sequencing fixture supplies no prospective scientific programme;
    # obligation ownership is covered by the full component contract controls.
    monkeypatch.setattr(owner, "_bind_component_obligations", lambda selected, *_args: selected)
    return specification, inputs, draft, records, arrays, observed


def test_operand_discovery_does_not_consult_source_qualification_and_preserves_final_refusal(monkeypatch):
    specification, inputs, draft, records, arrays, observed = selection(monkeypatch)
    projected = []
    def refuse(selected, *args):
        projected.append(selected)
        raise PermissionError("actual source qualification remains required")
    monkeypatch.setattr(owner, "select_component_qualifications", refuse)
    assert owner.component_source_operands(specification, inputs) == (draft, records, arrays)
    assert len(observed) == 1 and projected == []
    assert observed[0][1]["secondary_target"] is inputs.plan.structure.secondary_target
    assert observed[0][1]["secondary_readout"] is inputs.plan.secondary_readout
    with pytest.raises(PermissionError, match="source qualification"):
        owner.component_design(specification, inputs)
    assert projected == [draft]


def test_operand_discovery_refuses_future_collection_on_native_wave_before_lowering(monkeypatch):
    specification, inputs, _, _, _, observed = selection(monkeypatch)
    inputs.collection = object()
    with pytest.raises(ValueError, match="later collection outcomes"):
        owner.component_source_operands(specification, inputs)
    assert observed == []


def test_component_config_merge_obeys_actual_public_sha_roster_guard(prepared,tmp_path,monkeypatch):  # noqa: F811
    """Disclosed roster control only: stop before source capture or admission."""
    from empirical_lawhood.api import prospective_experiment as public
    from empirical_lawhood.planning.study_authoring import SourceAccessDisposition
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs

    original,=prepared.source_configs
    candidates=tuple(replace(original,config_id='config.roster.'+str(index),
        source_id='source.roster.'+str(index)) for index in range(8))
    left,right=next((left,right) for left in candidates for right in candidates
        if left.source_id<right.source_id and left.fingerprint()>right.fingerprint())
    unused=next(value for value in candidates if value not in (left,right))
    before={value.source_id:value.canonical_bytes() for value in (left,right,unused)}
    wanted={left.source_id,right.source_id}
    merged=owner._component_source_configs((left,unused,right),(right,left),wanted)
    assert len(merged)==2 and {value.source_id for value in merged}==wanted
    assert {value.source_id:value.canonical_bytes() for value in merged}=={
        value.source_id:before[value.source_id] for value in (left,right)}
    with pytest.raises(ValueError,match='conflicting source configs'):
        owner._component_source_configs((left,right),(replace(left,config_id=left.config_id+'.changed'),),wanted)

    # Use real preparation/design records and the owning public guard. These
    # extra references are explicitly unavailable; this test grants no source
    # qualification and stops before capture, provider construction or execution.
    old_ref,=prepared.draft.prospective_draft.source_materializations
    references=tuple(replace(old_ref,source_id=value.source_id,source_config_sha256=value.fingerprint(),
        qualification_receipt=None,access_disposition=SourceAccessDisposition.UNAVAILABLE) for value in (left,right))
    root=replace(prepared.draft.prospective_draft,source_materializations=references)
    draft=replace(prepared.draft,prospective_draft=root)
    spec=replace(prepared.prospective_spec,draft=draft)
    selected=replace(prepared,draft=draft,prospective_spec=spec,source_configs=merged,
        execution=replace(prepared.execution,output_root=str(tmp_path)))
    design=RecursiveProspectiveDesignInputs.from_spec(spec)
    writer=SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path=str(tmp_path))))
    reached=[]
    class RosterAccepted(BaseException):
        pass
    def stop_before_capture(*args,**kwargs):
        reached.append(True)
        raise RosterAccepted()
    monkeypatch.setattr(public,'capture_target_closure',stop_before_capture)
    with pytest.raises(ValueError,match='SHA-keyed source configuration roster'):
        public.preview_prepared_prospective_experiment_candidate(preparation=selected,design_inputs=design,
            source_configs=(left,right),project_root=tmp_path,artifact_writer=writer)
    assert reached==[]
    with pytest.raises(RosterAccepted):
        public.preview_prepared_prospective_experiment_candidate(preparation=selected,design_inputs=design,
            source_configs=merged,project_root=tmp_path,artifact_writer=writer)
    assert reached==[True]
