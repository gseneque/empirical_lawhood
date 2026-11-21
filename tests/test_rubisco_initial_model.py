# SPDX-License-Identifier: MPL-2.0
"""Independent exact controls, partial endpoints and original-source custody.

All supplied ratios, source texts and scientific reviews are disclosed software
operands. They are not evidence about Gp, scientific qualification or authority.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as E
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import DissolvedGasQuery, FourStateRates, solve_four_state
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import read_initial_model, required_initial_sources
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import RATIO_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
from empirical_lawhood.api.domain_composition.rubisco_response import initial_model as public
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_recursive_public_service import _plane
from tests import test_rubisco_active_relaxation_operation as preparation_controls


matched=preparation_controls.matched


def selection():
    supply=disclosed_supply()
    source=public.InitialSourceDocument('source.exposed.initial-model','urn:exposed:software-control',
        'Disclosed algebra input only. No physical, biological or prospective qualification.','MODEL_SPECIFICATION')
    dependencies=tuple(public.InitialContrastDependency(name,(source.identity,),('Declared exposed closure.',),
        ('quantity.'+name,),'DISCLOSED_CONTROL',('No Gp observations.',)) for name in RATIO_ORDER)
    case=public.InitialModelCase('case.initial.exposed',supply.case,supply.context,
        supply.context.chemistry.sites[0].site_id,source.identity,('chemical.exposed',),dependencies,(),())
    selected=public.prepare_initial_model(protocol=source.identity,cases=(case,),closure_source=source.identity,
        closure_assumptions=('Exposed four-state limiting endpoint closure.',),source_evidence=(source.identity,),maximum_analysis_bytes=2**20)
    return selected,source


def test_source_text_preserves_original_whitespace_and_newline():
    raw='  Original source text.\n\n'
    document=public.InitialSourceDocument('source.whitespace','urn:exposed:source',raw,'PUBLIC_SOURCE')
    returned=decode_canonical_bytes(document.canonical_bytes(),type(document),maximum_bytes=2**20)
    assert returned.raw_utf8.encode()==raw.encode()
    with pytest.raises(ValueError,match='nonempty UTF-8'):
        replace(document,raw_utf8=' \n ')


def test_matched_initial_preparer_derives_full_substitutions_and_both_processing_views(matched):
    from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
    from empirical_lawhood.api.domain_composition.rubisco_response.active_relaxation import prepare_conditional_active_relaxation
    plan,models=matched
    original,source=selection()
    states=prepare_conditional_active_relaxation(plan=plan,state_census=plan.members[0].state_census[:2],
        assumptions=('Disclosed selection only; no population or physical admission.',))
    context=RubiscoAssayContext('context.exposed.matched-initial',D('298.15'),(D(8),D(8)),
        'Explicit disclosed pH context.',models[0][0].chemistry,'INITIAL_RATE_SINKS',(source.identity,),'NEW_SELECTION')
    arguments=dict(plan=plan,state_selection=states,contexts=(('m1',context),('v1',context)),protocol=source.identity,
        closure_source=source.identity,closure_assumptions=('Disclosed limiting closure.',),
        dependencies=original.cases[0].dependencies,expected_alternative_ids=('chemical.exposed',),
        source_evidence=tuple(sorted((source.identity,plan.identity,states.identity),key=lambda p:p.object_id)),
        maximum_analysis_bytes=8*2**20)
    result=public.prepare_matched_initial_model(**arguments)
    assert tuple(c.case.parent.processing_view for c in result.cases)==('m1','v1')
    assert all(len(c.case.substitutions)==8 for c in result.cases)
    assert all(c.preparation_sources==(plan.identity,) for c in result.cases)
    missing=public.empty_initial_evidence(result,evidence_id='evidence.exposed.matched-missing')
    assert len(missing.cases)==2
    with pytest.raises(ValueError,match='complete matched preparation plan'):
        public.prepare_matched_initial_model(**{**arguments,'source_evidence':(source.identity,states.identity)})
    with pytest.raises(ValueError,match='separate M1 and V1'):
        public.prepare_matched_initial_model(**{**arguments,'contexts':(('m1',context),)})


def test_formation_coordinate_and_complete_finite_map_use_source_roles(matched):
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import paired_case
    from empirical_lawhood.api.domain_composition.rubisco_response import restrained_formation as formation
    _,models=matched
    mutant,_,mutant_prepared,*_=models[0]
    wt,_,wt_prepared,*_=models[1]
    case=paired_case(case_id='case.formation.matched-exposed',parent=wt.material,mutant=mutant.material,
        case_role='CANDIDATE',exposure_group='group.exposed.matched',sources=wt.material.sources)
    protocol=wt.material.sources[0]
    transform=formation.prepare_formation_atom_correspondence(case=case,wt_representation=wt,
        mutant_representation=mutant,protocol=protocol,sources=(protocol,))
    coordinates=tuple(formation.prepare_formation_coordinate(representation=model,prepared=prepared,
        site_id=prepared.sites[0].path.reactive_site_id) for model,prepared in ((wt,wt_prepared),(mutant,mutant_prepared)))
    assert coordinates[0].graph_atom_labels==('ligand.C3','ligand.HC3','protein.210.OQ2')
    assert tuple(dict(transform.common_atoms)[i] for i in coordinates[0].native_atom_indices)==coordinates[1].native_atom_indices
    assert all(c.required_constraints=='NONE' and len(c.state_seeds)==2 for c in coordinates)
    assert all(len(c.complete_mass_sha256)==64 for c in coordinates)
    assert all(decode_canonical_bytes(c.canonical_bytes(),type(c),maximum_bytes=2**20)==c for c in coordinates)
    with pytest.raises(ValueError,match='original representation'):
        formation.prepare_formation_coordinate(representation=wt,prepared=mutant_prepared,
            site_id=mutant_prepared.sites[0].path.reactive_site_id)


def support(values=(F(2),F(3),F(1),F(1)),*,intervals=False,kind='FIXED_JOINT_REALIZATION'):
    selected,source=selection()
    case=selected.cases[0]
    reviews=[]
    contrasts=[]
    for name,value in zip(RATIO_ORDER,values,strict=True):
        if value is None:
            contrasts.append(public.InitialContrastEvidence(name,None,'UNIDENTIFIED',(),None,('requirement.exposed.'+name,)))
            continue
        bounds=tuple(E.of(v) for v in value) if intervals else (E.of(value),E.of(value))
        review=public.InitialContrastReview('review.exposed.'+name,case.case.identity,case.context.identity,case.state_selection,
            name,bounds,(source.identity,),'Disclosed test assertion, not a scientific review of Gp.',A.SATISFIED,())
        reviews.append(review)
        pins=tuple(sorted((source.identity,review.identity),key=lambda p:p.object_id))
        contrasts.append(public.InitialContrastEvidence(name,bounds,'SOURCE_CONDITIONED',pins,review.identity,()))
    joint=public.InitialJointSupportReview('review.exposed.joint',case.case.identity,case.context.identity,case.state_selection,
        'point.exposed','dependence.exposed',kind,tuple(c.bounds for c in contrasts),(E.of(0),E.of(1)),
        tuple(sorted((source.identity,*(r.identity for r in reviews)),key=lambda p:p.object_id)),
        'Disclosed simultaneous support for an exact software control, no molecular coverage.',A.SATISFIED,())
    point=public.InitialJointRealization('point.exposed','dependence.exposed',joint.identity,kind,tuple(contrasts),(E.of(0),E.of(1)),None)
    alternative=public.InitialChemicalAlternative('chemical.exposed',(point.realization_id,),(point,),'AVAILABLE',())
    supplied=public.InitialCaseEvidence(case.case_id,case.case.identity,case.context.identity,case.state_selection,(alternative,))
    evidence=public.InitialModelEvidence('evidence.exposed.initial',selected.identity,(supplied,))
    return selected,evidence,(source,*reviews,joint),tuple(reviews)


def read(operands):
    selected,evidence,records,reviews=operands
    report=read_initial_model(selection=selected,evidence=evidence,reviews=reviews,joint_reviews=(records[-1],))
    return report,report['cases'][selected.cases[0].case_id]


@pytest.mark.parametrize('qa,qr,qd,qchi,turnover,specificity',[
    (2,3,1,1,'FAVOURABLE','FAVOURABLE'),
    (1,1,1,1,'ADVERSE','FAVOURABLE'),
    (F(1,2),2,2,1,'INCONCLUSIVE','FAVOURABLE'),
    (2,3,F(9,10),1,'FAVOURABLE','ADVERSE'),
    (F(10**50+1,10**50),F(10**50+2,10**50),1,1,'FAVOURABLE','FAVOURABLE'),
])
def test_exact_owner_boundaries_without_new_gain_or_confidence_threshold(qa,qr,qd,qchi,turnover,specificity):
    with localcontext() as ctx:
        ctx.prec=2
        report,row=read(support((qa,qr,qd,qchi)))
    assert row['endpoints']['turnover']['conditional_criterion']==turnover
    assert row['endpoints']['specificity']['conditional_criterion']==specificity
    assert report['all_requested_endpoints_evaluable']
    assert report['new_native_calls']==report['independent_biological_units']==0
    assert row['physical_rate_admission']=='UNEVALUABLE'


@pytest.mark.parametrize('missing',range(4))
def test_missing_mutation_operand_only_blocks_its_own_endpoint(missing):
    values=[F(2),F(3),F(1),F(1)]; values[missing]=None
    report,row=read(support(tuple(values)))
    blocked='turnover' if missing<2 else 'specificity'
    other='specificity' if missing<2 else 'turnover'
    assert row['endpoints'][blocked]['conditional_criterion']=='UNEVALUABLE'
    assert row['endpoints'][other]['conditional_criterion']=='FAVOURABLE'
    assert row['joint_owner_criterion']=='UNEVALUABLE'
    assert not report['all_requested_endpoints_evaluable']
    assert not row['chemical_alternatives'][0]['realizations'][0]['independent_corner_controls']


def test_positive_joint_regions_enclose_independent_complete_reversible_solver():
    operands=support(((F(3,2),F(5,2)),(F(2,3),F(7,3)),(F(2,3),F(3,2)),(F(1,2),F(2))),intervals=True,kind='JOINT_ENCLOSURE')
    _,row=read(operands)
    endpoints=row['endpoints']
    tlo,thi=map(fraction,endpoints['turnover']['complete_support_envelope'])
    slo,shi=map(fraction,endpoints['specificity']['complete_support_envelope'])
    for a,r,c,o,b in ((3,2,1,2,1),(7,13,2,1,100),(2,7,2,2,3)):
        wt=FourStateRates(*(D(n) for n in (a,b,c,2,2,o,r,3)))
        mutant=replace(wt,a=D(a)*2,r_c=D(r),c=D(c),o=D(o),b=D(971),r_o=D(3))
        p,q=(solve_four_state(rate,DissolvedGasQuery(D(20),D(250)),result_id='result.'+str(i)).intrinsic
            for i,rate in enumerate((wt,mutant)))
        assert tlo<=q.kcat_c.fraction/p.kcat_c.fraction<=thi
        assert slo<=q.specificity.fraction/p.specificity.fraction<=shi
    controls=row['chemical_alternatives'][0]['realizations'][0]['independent_corner_controls']
    assert len(controls)==16 and {c['numerical_disposition'] for c in controls}=={'SATISFIED'}


def test_source_text_or_unavailable_review_cannot_admit_supplied_ratios():
    selected,evidence,_,reviews=support()
    without=read_initial_model(selection=selected,evidence=evidence)
    row=without['cases'][selected.cases[0].case_id]
    assert row['joint_owner_criterion']=='UNEVALUABLE'
    assert row['chemical_alternatives'][0]['realizations'][0]['endpoints']['turnover']['arithmetic_criterion']=='FAVOURABLE'
    changed=replace(reviews[0],covered_bounds=(E.of(4),E.of(4)))
    contrast=evidence.cases[0].alternatives[0].realizations[0].contrasts[0]
    changed_contrast=replace(contrast,applicability_review=changed.identity,
        sources=tuple(sorted((contrast.sources[-1] if contrast.sources[-1]!=contrast.applicability_review else contrast.sources[0],changed.identity),key=lambda p:p.object_id)))
    point=evidence.cases[0].alternatives[0].realizations[0]
    alternative=replace(evidence.cases[0].alternatives[0],realizations=(replace(point,contrasts=(changed_contrast,*point.contrasts[1:])),))
    changed_evidence=replace(evidence,cases=(replace(evidence.cases[0],alternatives=(alternative,)),))
    with pytest.raises(ValueError,match='substitutes'):
        read_initial_model(selection=selected,evidence=changed_evidence,reviews=(changed,*reviews[1:]))


def test_samples_do_not_acquire_coverage_and_unknown_alternatives_remain_in_denominator():
    _,row=read(support(kind='JOINT_SAMPLE'))
    assert row['endpoints']['turnover']['conditional_criterion']=='UNEVALUABLE'
    assert row['endpoints']['turnover']['complete_support_envelope'] is None
    assert row['endpoints']['turnover']['available_support_envelope'] is not None
    selected,source=selection()
    case=replace(selected.cases[0],expected_alternative_ids=('chemical.exposed','chemical.failed'))
    selected=replace(selected,cases=(case,))
    evidence=public.empty_initial_evidence(selected,evidence_id='evidence.missing')
    result=read_initial_model(selection=selected,evidence=evidence)
    alternatives=result['cases'][case.case_id]['chemical_alternatives']
    assert len(alternatives)==2 and all(a['original_state']=='UNKNOWN' for a in alternatives)
    with pytest.raises(ValueError,match='alternative'):
        read_initial_model(selection=selected,evidence=replace(evidence,cases=(replace(evidence.cases[0],alternatives=evidence.cases[0].alternatives[:1]),)))
    assert required_initial_sources(selected,evidence)==(source.identity,)


def test_contracts_roundtrip_and_refuse_marginals_changed_context_or_unsupported_invariance():
    selected,evidence,_,_=support()
    for value in (selected,evidence):
        assert decode_canonical_bytes(value.canonical_bytes(),type(value),maximum_bytes=2**20)==value
    point=evidence.cases[0].alternatives[0].realizations[0]
    with pytest.raises(ValueError,match='marginal'):
        replace(point,support_kind='MARGINAL_BOX')
    with pytest.raises(ValueError,match='missing scientific'):
        replace(point.contrasts[0],evidence_kind='IMPOSED_ASSUMPTION')
    with pytest.raises(ValueError,match='narrowed'):
        replace(point,wild_type_formation_wait_fraction=(E.of(F(1,4)),E.of(F(3,4))))
    changed=replace(selected.cases[0],context=replace(selected.cases[0].context,temperature_k=D('300')))
    with pytest.raises(ValueError,match='selected model|assay'):
        read_initial_model(selection=replace(selected,cases=(changed,)),evidence=evidence)


def publish_sources(writer,records):
    writes=[]
    sources=[]
    for index,record in enumerate(records):
        name='sources/'+str(index)+'.json'
        writes.append(ArtifactWriteRequest('source.exposed.'+str(index),name,record.SCHEMA,ArtifactProfile.CANONICAL_JSON,
            'application/json','package.exposed.sources','sources',record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY,(),outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        sources.append(public.InitialModelSource(record.identity,writer,name))
    writer.write_batch(tuple(writes))
    return tuple(sources)


def test_closed_original_source_export_reconstructs_and_refuses_late_or_retained_mutation(tmp_path,monkeypatch):
    selected,evidence,records,_=support()
    writer=_plane(tmp_path/'custody')
    sources=publish_sources(writer,records)
    package=(('src/exposed_initial_control.py','4'*64),)
    digest=sha256(canonical_json_bytes(package)).hexdigest()
    provenance=NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '5'*64,package,digest,'3'*40,False)
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:SimpleNamespace(code_sources_sha256=digest,dependency_lock_sha256='5'*64))
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:provenance)
    exported=public.export_initial_model(selection=selected,evidence=evidence,sources=sources,project_root=tmp_path,
        artifact_writer=writer,output_relative_path='analysis')
    reread=public.read_initial_model_export(directory_relative_path='analysis',sources=sources,artifact_writer=writer)
    assert reread['report']==exported['report'] and reread['new_native_calls']==0
    assert reread['report']['all_requested_endpoints_evaluable']
    with pytest.raises(ValueError,match='fresh'):
        public.export_initial_model(selection=selected,evidence=evidence,sources=sources,project_root=tmp_path,
            artifact_writer=writer,output_relative_path='analysis')
    path=tmp_path/'custody'/'sources'/'0.json'
    raw=path.read_bytes()
    path.write_bytes(raw.replace(b'Disclosed',b'Alteredxx'))
    with pytest.raises(ArtifactIdentityConflict):
        public.read_initial_model_export(directory_relative_path='analysis',sources=sources,artifact_writer=writer)


def test_source_guard_stays_live_during_analysis_and_missing_source_refuses_before_math(tmp_path,monkeypatch):
    selected,evidence,records,_=support()
    writer=_plane(tmp_path/'custody')
    sources=publish_sources(writer,records)
    original=public.read_initial_model
    path=tmp_path/'custody'/'sources'/'0.json'
    def mutate(**kwargs):
        result=original(**kwargs)
        path.write_bytes(path.read_bytes()+b'\n')
        return result
    monkeypatch.setattr(public,'read_initial_model',mutate)
    with pytest.raises(ValueError,match='complete original census'):
        public.read_initial_model_sources(selection=selected,evidence=evidence,sources=sources[:-1])
    with pytest.raises(ArtifactIdentityConflict):
        public.read_initial_model_sources(selection=selected,evidence=evidence,sources=sources)
