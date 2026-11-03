# SPDX-License-Identifier: MPL-2.0
"""Disclosed compact E1 controls; no scientific qualification or native contact."""
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256

import pytest
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import records as old,science as old_science
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_records as r,compact_science as science
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import lifetime
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import ScientificStatus
from tests.test_matrix_factor_confirmation_history import e1 as e1
from tests.test_matrix_factor_confirmation_eligibility import publish,provenance as provenance,stock as stock
from tests.test_matrix_factor_confirmation_adjudication import products as old_products


def compact_case(e1,*,copies=1,origin_end=6,trailing=0):
    plane,original,definition=e1
    source=original[0];allocation=source.allocation
    if copies>1:
        roots=[]
        for row in allocation.roots:
            for i in range(copies):
                root=replace(row.root,root_id=row.root.root_id+'.'+str(i).zfill(3),independent_group_id=row.root.independent_group_id+'.'+str(i).zfill(3))
                streams=tuple(MatrixHistorySeed(s.purpose,sha256(('DISCLOSED.COMPACT.E1.'+root.root_id+s.purpose).encode()).hexdigest()) for s in row.streams)
                roots.append(replace(row,root=root,streams=streams))
        allocation=replace(allocation,allocation_id=allocation.allocation_id+'.'+str(copies),roots=tuple(sorted(roots,key=lambda value:value.root.root_id)))
        reservation=old.E1AllocationReservation(source.reservation.reservation_id+'.'+str(copies),allocation,publish(plane,allocation,'compact.allocation.'+str(copies)))
    else:reservation=source.reservation
    criterion=source.criterion
    rule = replace(source.rule, risk_start_tick=0, trailing_persistence_ticks=trailing)
    criterion = r.E1CompactCriterion('criterion.compact.software.'+str(copies), old.identity(allocation), rule.identity,
        criterion.system_id, criterion.world_id, criterion.relation, criterion.independent_unit_id,
        tuple(r.E1FamilySize(value.family_id, copies) for value in criterion.family_requirements), r.VIEWS, r.ENDPOINTS,
        'INITIAL_PRESENCE_OR_FIRST_CAUSAL_ADMISSION', origin_end, 2, 1, 160, origin_end,
        'TWO_SIDED_EXACT_BINOMIAL_FEASIBLE_COMPLETION_ENVELOPE', 'EIGHT_PRIMARY_Y_CELLS_DIAGNOSTIC_MARGINAL_95_PERCENT')
    selected=r.E1CompactScientificSelection('selection.compact.software.'+str(copies),old.identity(reservation),rule,
        criterion,source.numerical_design,source.specification.selection.factor_numerical_design)
    frozen=r.E1CompactFrozenSpecification('frozen.compact.software.'+str(copies),selected,publish(plane,selected,'compact.selection.'+str(copies)))
    manifest=r.E1CompactManifest('manifest.compact.software.'+str(copies),reservation,frozen,source.provenance,definition,
        publish(plane,definition,definition.definition_id))
    return manifest,r.sources_for_manifest(manifest)


def compact_products(original,sources,*,flags=None,numerical=True):
    products,assessments=old_products(original,flags=flags,numerical=numerical)
    converted=[];checked=[]
    for source,p,a in zip(sources,products,assessments,strict=True):
        pin=r.identity(source)
        history=ObjectIdentity('synthetic.compact.history.'+source.root_id,r.E1CompactNativeHistory.SCHEMA,'1.0.0','1'*64)
        numerical_pin=ObjectIdentity('synthetic.compact.numerical.'+source.root_id,r.E1CompactNumericalAssessment.SCHEMA,'1.0.0','3'*64)
        traces=[]
        for trace in p.traces:
            origin=next((row.tick for row in trace.observations if row.causal_admitted is True), None)
            obs=tuple(replace(row, origin_angle_degrees=Decimal(0) if row.identifiable is True
                and origin is not None and row.tick >= origin else None) for row in trace.observations)
            traces.append(r.E1CompactFactorTrace(r.E1CompactFactorRootRole(source.root_id,source.root.root.independent_group_id,
                source.coordinate.family_id,pin,trace.root.native_arrays,history),source.rule.identity,trace.view,trace.sector,obs,
                lifetime(obs,source.rule),lifetime(obs,source.rule,origin_fixed=True),trace.diagnostics,trace.diagnostic_members))
        arrays=r.E1CompactArrays('synthetic.compact.arrays.'+source.root_id,pin,p.arrays.role,p.arrays.array_artifact,p.arrays.members,
            tuple(sorted((pin,history,numerical_pin),key=lambda value:value.object_id)),p.arrays.outcome_access,p.arrays.visibility_ceiling)
        product=r.E1CompactFactorProduct('synthetic.compact.product.'+source.root_id,pin,history,numerical_pin,
            p.history_numerical_pass,tuple(traces),arrays)
        assessment=r.E1CompactFactorAssessment('synthetic.compact.assessment.'+source.root_id,pin,r.identity(product),a.numerical_design,a.controls,a.numerical_pass)
        converted.append(product);checked.append(assessment)
    return tuple(converted),tuple(checked)


def test_exact_rational_eight_primary_cell_allowance_preserves_old_criterion_bytes(e1):
    original=e1[1][0].criterion.canonical_bytes()
    manifest,sources=compact_case(e1)
    criterion=manifest.specification.selection.criterion
    with localcontext() as context:
        context.prec=6
        assert criterion.primary_alpha==Fraction(1,160)
        assert criterion.cell_alpha(sources[0].rule)==Fraction(1,1280)
    assert e1[1][0].criterion.canonical_bytes()==original
    assert criterion.SCHEMA!=old.E1ConfirmationCriterion.SCHEMA
    for record in (criterion,manifest,*sources):
        assert decode_canonical_bytes(record.canonical_bytes(),type(record),maximum_bytes=None)==record


def test_source_growth_keeps_per_root_configs_bounded_and_hashes_manifest_once(e1,monkeypatch):
    small,small_sources=compact_case(e1)
    large,large_sources=compact_case(e1,copies=8)
    calls={'manifest':0};fingerprint=r.E1CompactManifest.fingerprint
    def counted(self):
        calls['manifest']+=1
        return fingerprint(self)
    monkeypatch.setattr(r.E1CompactManifest,'fingerprint',counted)
    r.sources_for_manifest(small);small_calls=calls['manifest'];calls['manifest']=0
    r.sources_for_manifest(large)
    assert small_calls==calls['manifest']==1
    assert len(small_sources)==4 and len(large_sources)==32
    assert len(large.canonical_bytes())-len(small.canonical_bytes())<28*4096
    def configs(sources):
        return tuple(r.E1CompactOperationConfig('config.'+r.NAMESPACE+'.'+s.root_id+'.history','history',s).canonical_bytes() for s in sources)
    small_bytes=configs(small_sources);large_bytes=configs(large_sources)
    assert max(map(len,large_bytes))<64*1024
    assert abs(max(map(len,large_bytes))-max(map(len,small_bytes)))<256
    assert all(b'"package_sources"' not in raw and b'"exposure"' not in raw for raw in large_bytes)
    assert b'"package_sources"' in large.canonical_bytes() and b'"exposure"' in large.canonical_bytes()


@pytest.mark.parametrize('origin,expected_risk',((0,1),(6,1),(7,0),(8,0)))
def test_occurrence_boundary_retains_all_assigned_roots_and_complete_followup(e1,origin,expected_risk):
    manifest,sources=compact_case(e1)
    flags={(sources[0].root_id,'PRIMARY','X'):(False,)*origin+(True,)*(9-origin)}
    p,a=compact_products(e1[1],sources,flags=flags)
    result=science.reduce_population(manifest,sources,p,a)
    key=(sources[0].coordinate.family_id,'PRIMARY','X')
    row=next(value for value in result.findings if (value.family_id,value.view,value.sector,value.endpoint)==(*key,'BOTH'))
    assert row.interval.risk_count_lower==row.interval.risk_count_upper==expected_risk
    assert row.interval.known_successes==expected_risk
    occurrence=next(value for value in result.findings if (value.family_id,value.view,value.sector,value.endpoint)==(*key,'OCCURRENCE'))
    assert len(occurrence.interval.unit_ids)==occurrence.interval.risk_count_lower==1
    assert occurrence.interval.known_successes==expected_risk
    assert occurrence.interval.known_failures==1-expected_risk
    assert result.primary_alpha_numerator==result.cell_alpha_numerator==1
    assert result.primary_alpha_denominator==160 and result.cell_alpha_denominator==1280
    assert result.scientific_status is ScientificStatus.PARTIAL
    assert sum(value.primary for value in result.findings)==8
    assert len(result.findings)==64 and len(result.events)==16
    assert decode_canonical_bytes(result.canonical_bytes(),type(result),maximum_bytes=None)==result
    if origin==8:
        oldp,olda=old_products(e1[1],flags=flags)
        original=old_science.reduce_population(e1[1],oldp,olda)
        assert any(value.censored_before_horizon==1 for value in original.findings)


@pytest.mark.parametrize('state',('no-origin','missing','exit','numerical','unknown-before-late'))
def test_complete_denominators_keep_adverse_unknown_and_zero_risk_without_probability_gate(e1,state):
    manifest,sources=compact_case(e1)
    flags=(False,)*9 if state=='no-origin' else (True,None)+(True,)*7 if state=='missing' else (True,False)+(True,)*7 if state=='exit' else (False,)*4+(None,False,False,True,True) if state=='unknown-before-late' else (True,)*9
    p,a=compact_products(e1[1],sources,flags={(sources[0].root_id,'PRIMARY','X'):flags},numerical=state!='numerical')
    result=science.reduce_population(manifest,sources,p,a)
    assert result.root_ids==tuple(source.root_id for source in sources)
    assert result.scientific_status is (ScientificStatus.UNEVALUABLE if state=='numerical' else ScientificStatus.PARTIAL)
    row=next(value for value in result.findings if (value.family_id,value.view,value.sector,value.endpoint)==(sources[0].coordinate.family_id,'PRIMARY','X','BOTH')).interval
    if state=='missing':assert row.known_risk_unknown_outcomes==1 and row.lower==0 and row.upper==1
    if state=='exit':assert row.known_failures==1 and row.known_successes==0
    if state=='no-origin':assert row.risk_count_upper==0 and row.lower is None
    if state=='unknown-before-late':
        assert row.unknown_eligibility==1 and row.lower is None


def test_reducer_rejects_missing_root_foreign_manifest_and_old_source_edition(e1):
    manifest,sources=compact_case(e1);p,a=compact_products(e1[1],sources)
    with pytest.raises(ValueError,match='complete selected root'):science.reduce_population(manifest,sources,p[:-1],a[:-1])
    with pytest.raises(ValueError,match='manifest/root correspondence'):
        science.reduce_population(manifest,(replace(sources[0],manifest=replace(sources[0].manifest,object_fingerprint='b'*64)),*sources[1:]),p,a)
    with pytest.raises(ValueError,match='typed record edition'):
        replace(p[0].arrays,source=replace(p[0].source,object_schema=old.E1HistorySource.SCHEMA))
