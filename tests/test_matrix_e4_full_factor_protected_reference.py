# SPDX-License-Identifier: MPL-2.0
"""Disclosed protected reference controls; no genuine issue/reveal is created."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import (
    ScheduledFullFactorScope, ScheduledFullFactorScopeReference, ScheduledFullFactorSourceReference)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.runtime.plans import ExecutionPlan
from tests.test_matrix_e4_full_factor_values import scopes, pin  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_e4_full_factor_public import _real_plane


def _waves(programme):
    return tuple(protected.SelectedE4WaveLocator(wave.wave_id,'run.disclosed.'+wave.wave_id,
        ObjectIdentity('package.disclosed','empirical-lawhood/api/experiment-package','1.0.0','a'*64),
        ObjectIdentity('issue.disclosed','empirical-lawhood/tests/issue','1.0.0','b'*64),
        ObjectIdentity('execution.disclosed','empirical-lawhood/tests/execution','1.0.0','c'*64),
        ObjectIdentity('reveal.disclosed','empirical-lawhood/tests/reveal','1.0.0','d'*64),pin('plan.disclosed',ExecutionPlan))
        for wave in programme.waves)


def test_protected_request_and_reference_retain_only_declaration_pin(scopes,literal_recipe_source_inputs,tmp_path):  # noqa: F811
    programme,_,sources=scopes['CONFIRMATION']
    declaration=pin('declaration.disclosed',protected.SelectedE4NativeProgrammeDeclaration)
    waves=_waves(programme)
    from tests.test_matrix_e4_full_factor_public import selected_values
    selected=selected_values(scopes,literal_recipe_source_inputs,plane=_real_plane(tmp_path/"target-custody"))
    request=domain.ScheduledFullFactorProtectedRequestV4('request.disclosed',programme.identity,programme.bank,
        pin('resources.disclosed',domain.ScheduledFullFactorResources),declaration,waves,
        pin('campaign.disclosed',domain.CampaignSpec),selected.secondary_readout)
    scope=pin('scope.disclosed',ScheduledFullFactorScope)
    reference=ScheduledFullFactorScopeReference('reference.disclosed',scope,
        ArtifactIdentity(scope.object_id,'original-full-factor-scope',scope.object_schema,scope.object_fingerprint,'application/json',1),
        programme,tuple(ScheduledFullFactorSourceReference(row.root_id,row.group_id,row.identity,
            ArtifactIdentity(row.record_id,'original-full-factor-source',row.SCHEMA,row.fingerprint(),'application/json',len(row.canonical_bytes())),None)
            for row in sources),tuple(sorted({view.view_id for source in sources for view in (source.coordinate.primary_view,source.coordinate.fine_view)})),
        None,declaration,waves,sources[0].produced_input_parents)
    for record in (request,reference):
        assert record.declaration is declaration
        assert record.to_document()['value']['declaration']==declaration.to_document()
        assert b'"planned_task_budgets"' not in record.canonical_bytes()
        assert b'"development_decision"' not in record.canonical_bytes()
        assert b'"calibration"' not in record.canonical_bytes()
    with pytest.raises((TypeError,ValueError)):
        replace(request,declaration=SimpleNamespace(identity=declaration))
    with pytest.raises(ValueError,match='wave'):
        replace(request,waves=(waves[0],waves[0]))
    with pytest.raises(ValueError,match='protected selectors'):
        replace(reference,waves=waves[:-1])
    raw=request.canonical_bytes()
    assert decode_canonical_bytes(raw,type(request),maximum_bytes=len(raw)).canonical_bytes()==raw
    for version in ('1.0.0','2.0.0','3.0.0'):
        document=request.to_document();document['version']=version
        with pytest.raises(ValueError,match='unsupported canonical document version'):
            decode_canonical_bytes(canonical_json_document_bytes(document),type(request),maximum_bytes=None)


def test_original_reveal_refusal_precedes_declaration_body_io(scopes,monkeypatch):  # noqa: F811
    from empirical_lawhood.api import matrix_full_factor_custody as custody,recursive_qualified_parents as parents,matrix_selected_runtime as source
    programme,_,_=scopes['CONFIRMATION'];waves=_waves(programme)
    package=object();actual_pin=custody._pin;events=[]
    monkeypatch.setattr(parents,'_actual_package',lambda writer,run_id:package)
    monkeypatch.setattr(custody,'_pin',lambda value,field:waves[0].package if value is package else actual_pin(value,field))
    def refused(*args,**kwargs):
        events.append('current-original-reveal')
        raise PermissionError('disclosed original reveal is absent')
    monkeypatch.setattr(parents,'_replay_parent_authority',refused)
    monkeypatch.setattr(source,'_published_input',lambda *args,**kwargs:pytest.fail('declaration body read before actual original reveal'))
    with pytest.raises(PermissionError,match='reveal is absent'):
        custody._protected_declaration(writer=None,programme=programme,
            declaration=pin('declaration.disclosed',protected.SelectedE4NativeProgrammeDeclaration),waves=waves)
    assert events==['current-original-reveal']
