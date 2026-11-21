# SPDX-License-Identifier: MPL-2.0
"""Prepare and independently read a closed source-conditioned initial model.

Every external source is an exact original guarded publication. Source custody,
the scientific content of a review, numerical arithmetic and physical validity
remain distinct. This route enters no native worker or acquisition service.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
import time
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import empty_initial_evidence, read_initial_model, required_initial_sources
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialChemicalAlternative, InitialCaseEvidence, InitialContrastDependency, InitialContrastEvidence, InitialContrastReview, InitialJointRealization, InitialJointSupportReview, InitialModelCase, InitialModelEvidence, InitialModelSelection, InitialSourceDocument, validate_initial_model_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_contributions import InitialContribution, InitialContributionRealization, initial_contrast_evidence, read_initial_contributions, validate_initial_contribution_projection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_document_bytes, validate_decimal, validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key


MEMBERS = ('selection.json', 'inputs.json', 'evidence.json', 'readout.json', 'report.txt')
MAXIMUM_BYTES = 64 * 2**20


@dataclass(frozen=True, slots=True)
class InitialModelSource:
    identity: ObjectIdentity
    artifact_writer: object
    relative_path: str

    def __post_init__(self):
        exact(self.identity,ObjectIdentity)
        validate_relative_locator(self.relative_path)


@dataclass(frozen=True, slots=True)
class InitialModelAnalysisEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-model-analysis-evidence'
    selection: ObjectIdentity
    inputs: ObjectIdentity
    provenance: NumericalProducingProvenance
    original_sources: tuple[ObjectIdentity, ...]
    readout: FileEvidence
    cpu_seconds: Decimal
    wall_seconds: Decimal
    new_native_calls: int = 0

    def __post_init__(self):
        for pin,kind in ((self.selection,InitialModelSelection),(self.inputs,InitialModelEvidence)):
            exact(pin,ObjectIdentity)
            if (pin.object_schema,pin.object_version)!=(kind.SCHEMA,kind.VERSION):
                raise ValueError('initial analysis changes its exact model or evidence revision')
        exact(self.provenance,NumericalProducingProvenance)
        identities(self.original_sources)
        exact(self.readout,FileEvidence)
        if self.readout.relative_path!='readout.json':
            raise ValueError('initial analysis changes its readout member')
        for name in ('cpu_seconds','wall_seconds'):
            validate_decimal(getattr(self,name),field_name=name,minimum=Decimal(0))
        if type(self.new_native_calls) is not int or self.new_native_calls!=0:
            raise ValueError('independent initial analysis cannot claim native acquisition')


def prepare_initial_model(*, protocol, cases, closure_source, closure_assumptions, source_evidence, maximum_analysis_bytes):
    candidate=InitialModelSelection('initial-model.pending',protocol,cases,closure_source,
        closure_assumptions,source_evidence,maximum_analysis_bytes)
    return replace(candidate,selection_id='initial-model.'+candidate.fingerprint())


def prepare_initial_contribution_realization(*, case, alternative_id, realization_id,
        dependence_group_id, support_kind, contributions):
    """Bind the minimal contributions to one existing case and chemical alternative."""
    exact(case,InitialModelCase)
    if alternative_id not in case.expected_alternative_ids:
        raise ValueError('initial contribution substitutes the selected chemical alternative')
    candidate=InitialContributionRealization('initial-contributions.pending',case.case.identity,
        case.context.identity,case.state_selection,alternative_id,realization_id,dependence_group_id,
        support_kind,contributions)
    return replace(candidate,contribution_id='initial-contributions.'+candidate.fingerprint())


def prepare_matched_initial_model(*,plan,state_selection,contexts,protocol,closure_source,
        closure_assumptions,dependencies,expected_alternative_ids,source_evidence,maximum_analysis_bytes):
    """Derive both processing-view cases from the complete original matched plan.

    Contexts are explicit operator selections. Sequence, substitution, state
    and focal-site censuses come from the existing preparation owners.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import validate_conditional_relaxation_selection
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import paired_case
    from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
    validate_conditional_relaxation_selection(plan,state_selection)
    if type(contexts) is not tuple or tuple(name for name,_ in contexts)!=('m1','v1'):
        raise ValueError('initial model needs separate M1 and V1 assay selections')
    sites={site for site,_,_ in state_selection.state_census}
    if len(sites)!=1:
        raise ValueError('one initial-model comparison requires one explicit focal-site view')
    if not {plan.identity,state_selection.identity}.issubset(source_evidence):
        raise ValueError('initial model drops its original complete matched preparation plan')
    materials={m.model_name:m.material for m in plan.members}
    cases=[]
    for processing,context in contexts:
        exact(context,RubiscoAssayContext)
        case=paired_case(case_id='case.initial.'+processing+'.'+plan.fingerprint(),
            parent=materials[processing+'-wt'],mutant=materials[processing+'-i95m'],case_role='CANDIDATE',
            exposure_group='exposure.initial.'+processing+'.'+state_selection.fingerprint(),sources=(plan.identity,))
        cases.append(InitialModelCase('initial-case.'+processing+'.'+state_selection.fingerprint(),case,context,
            next(iter(sites)),state_selection.identity,expected_alternative_ids,dependencies,(plan.identity,),
            ('initial-model.actual-paired-physical-preparation','initial-model.chemical-model-and-closure-applicability')))
    return prepare_initial_model(protocol=protocol,cases=tuple(cases),closure_source=closure_source,
        closure_assumptions=closure_assumptions,source_evidence=source_evidence,maximum_analysis_bytes=maximum_analysis_bytes)


def _exposed(member):
    if (member.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or member.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('initial model reader cannot open a different original evidence lane')


def _sources(selection, evidence, sources, consumer):
    """Keep every original publication guard live through analysis/publication."""
    expected=required_initial_sources(selection,evidence)
    if (type(sources) is not tuple or any(type(s) is not InitialModelSource for s in sources)
            or tuple(sorted((s.identity for s in sources),key=lambda p:p.object_id))!=expected):
        raise ValueError('initial model source selection differs from its complete original census')
    groups={}
    for source in sources:
        groups.setdefault(id(source.artifact_writer),[]).append(source)
    groups=tuple(groups.values())
    payloads={}
    total=0
    def enter(number):
        nonlocal total
        if number==len(groups):
            contributions={pin:decode_canonical_bytes(payloads[pin],InitialContributionRealization,
                maximum_bytes=selection.maximum_analysis_bytes)
                for pin in expected if pin.object_schema==InitialContributionRealization.SCHEMA}
            for selected_case,supplied in zip(selection.cases,evidence.cases,strict=True):
                for alternative in supplied.alternatives:
                    for realization in alternative.realizations:
                        for contrast in realization.contrasts:
                            for pin in set(contrast.sources)&set(contributions):
                                validate_initial_contribution_projection(contributions[pin],selected_case,
                                    alternative,realization,contrast)
            reviews=tuple(decode_canonical_bytes(payloads[pin],InitialContrastReview,maximum_bytes=selection.maximum_analysis_bytes)
                for pin in expected if pin.object_schema==InitialContrastReview.SCHEMA)
            joint_reviews=tuple(decode_canonical_bytes(payloads[pin],InitialJointSupportReview,maximum_bytes=selection.maximum_analysis_bytes)
                for pin in expected if pin.object_schema==InitialJointSupportReview.SCHEMA)
            for review in (*reviews,*joint_reviews):
                if not set(review.supporting_sources).issubset(expected):
                    raise ValueError('initial contrast review omits original supporting sources')
            return consumer(reviews,joint_reviews)
        group=groups[number]
        writer=group[0].artifact_writer
        manifests=tuple(writer.read_manifest(s.relative_path) for s in group)
        def consume(members):
            nonlocal total
            for source in group:
                if source.relative_path not in members:
                    raise ValueError('initial source is absent from its authenticated original publication')
                raw=read_bounded_bytes(writer.root.resolve(source.relative_path,for_write=False),
                    maximum_bytes=selection.maximum_analysis_bytes)
                total+=len(raw)
                if total>selection.maximum_analysis_bytes:
                    raise ValueError('initial source census exceeds the complete selected read allocation')
                document=json.loads(raw)
                pin=source.identity
                if (sha256(raw).hexdigest()!=pin.object_fingerprint
                        or (document.get('schema'),document.get('version'))!=(pin.object_schema,pin.object_version)
                        or canonical_json_document_bytes(document)!=raw):
                    raise ValueError('initial source substitutes its exact canonical bytes, schema or revision')
                payloads[pin]=raw
            return enter(number+1)
        return writer.verify_manifests_members(manifests,validate_members=consume,before_member=_exposed)
    return enter(0)


def read_initial_model_sources(*, selection, evidence, sources):
    return with_initial_model_sources(selection=selection,evidence=evidence,sources=sources,
        consumer=lambda reviews,joint_reviews:read_initial_model(selection=selection,evidence=evidence,reviews=reviews,joint_reviews=joint_reviews))


def with_initial_model_sources(*, selection, evidence, sources, consumer):
    """Consume exact reviews while all original source guards remain active.

    A derived analysis must finish its calculation and publication inside the
    callback. This shares the original reader's exposure and contribution checks;
    it is not an independent permission or cached admission result.
    """
    return _sources(selection,evidence,sources,consumer)


def _json(report):
    return (json.dumps(report,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')


def _text(report):
    lines=['Source-conditioned initial paired Rubisco model','',
        'Criteria: turnover ratio > 1; specificity ratio >= 1.',
        'Complete WT waiting interval is retained unless its narrower bounds have evidence.',
        'Original contrast reviews, arithmetic and biological validity remain distinct.','']
    for name,row in report['cases'].items():
        lines.append(name+' ('+row['processing_view']+'): '+row['joint_owner_criterion'])
        for endpoint,value in row['endpoints'].items():
            lines.append('  '+endpoint+': '+value['conditional_criterion'])
        lines.extend('  Remaining: '+name for name in row['remaining_requirement_ids'])
    lines.extend(('', 'No absolute rate, missing mutation contrast, population weight or confidence coverage is inferred.',
        'Biological predictive validity: UNEVALUABLE. New native calls: 0.',''))
    return '\n'.join(lines).encode('utf-8')


def _parents(sources):
    return tuple(sorted((ArtifactLineageParent(s.identity,VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE) for s in sources),key=lineage_parent_sort_key))


def export_initial_model(*, selection, evidence, sources, project_root, artifact_writer, output_relative_path):
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    validate_initial_model_inputs(selection,evidence)
    validate_relative_locator(output_relative_path)
    for name in MEMBERS:
        if artifact_writer.root.resolve(output_relative_path+'/'+name,for_write=True).exists():
            raise ValueError('initial model export requires a fresh complete destination')
    implementation=implementation_binding(project_root)
    provenance=capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,expected_lock_sha256=implementation.dependency_lock_sha256)
    cpu,wall=time.process_time(),time.perf_counter()
    def publish(reviews,joint_reviews):
        report=read_initial_model(selection=selection,evidence=evidence,reviews=reviews,joint_reviews=joint_reviews)
        raw=_json(report)
        accepted=InitialModelAnalysisEvidence(selection.identity,evidence.identity,provenance,
            required_initial_sources(selection,evidence),FileEvidence('readout.json',len(raw),sha256(raw).hexdigest()),
            Decimal.from_float(time.process_time()-cpu),Decimal.from_float(time.perf_counter()-wall))
        records={'selection.json':selection,'inputs.json':evidence,'evidence.json':accepted}
        payloads={name:record.canonical_bytes() for name,record in records.items()}
        payloads.update({'readout.json':raw,'report.txt':_text(report)})
        if sum(len(raw) for raw in payloads.values())>selection.maximum_analysis_bytes:
            raise ValueError('initial model export exceeds its selected complete package allocation')
        package='initial-model-package.'+sha256(b''.join(sha256(payloads[n]).digest() for n in MEMBERS)).hexdigest()
        parents=_parents(sources)
        writes=tuple(ArtifactWriteRequest('initial-model-member.'+sha256(raw).hexdigest()+'.'+name.replace('.','-'),
            output_relative_path+'/'+name,records[name].SCHEMA if name in records else 'empirical-lawhood/rubisco-response/initial-model-text',
            ArtifactProfile.CANONICAL_JSON if name in records else ArtifactProfile.TEXT_PARAMETERS,
            'application/json' if name.endswith('.json') else 'text/plain',package,output_relative_path,raw,
            VisibilityCeiling.DEVELOPMENT_ONLY,tuple(p.visibility_ceiling for p in parents),OutcomeAccess.DEVELOPMENT_VISIBLE,
            lineage_parents=parents) for name,raw in payloads.items())
        publications=artifact_writer.write_batch(writes)
        return dict(evidence=accepted,report=report,new_native_calls=0,package_id=package,publications=publications,
            paths={name:str(artifact_writer.root.resolve(output_relative_path+'/'+name,for_write=False)) for name in MEMBERS})
    return _sources(selection,evidence,sources,publish)


def read_initial_model_export(*, directory_relative_path, sources, artifact_writer):
    validate_relative_locator(directory_relative_path)
    manifest=artifact_writer.read_manifest(directory_relative_path+'/evidence.json')
    def consume(members):
        expected={directory_relative_path+'/'+name:name for name in MEMBERS}
        if set(members)!=set(expected):
            raise ValueError('initial model export changes its complete closed member census')
        raw={name:read_bounded_bytes(artifact_writer.root.resolve(path,for_write=False),maximum_bytes=MAXIMUM_BYTES)
            for path,name in expected.items()}
        selection=decode_canonical_bytes(raw['selection.json'],InitialModelSelection,maximum_bytes=MAXIMUM_BYTES)
        inputs=decode_canonical_bytes(raw['inputs.json'],InitialModelEvidence,maximum_bytes=MAXIMUM_BYTES)
        evidence=decode_canonical_bytes(raw['evidence.json'],InitialModelAnalysisEvidence,maximum_bytes=MAXIMUM_BYTES)
        if (sum(map(len,raw.values()))>selection.maximum_analysis_bytes
                or (evidence.selection,evidence.inputs)!=(selection.identity,inputs.identity)
                or evidence.original_sources!=required_initial_sources(selection,inputs)
                or evidence.readout!=FileEvidence('readout.json',len(raw['readout.json']),sha256(raw['readout.json']).hexdigest())
                or any(m.logical.lineage_parents!=_parents(sources) for m in members.values())):
            raise ValueError('initial model export substitutes its original inputs, readout or source ancestry')
        def reconstruct(reviews,joint_reviews):
            report=read_initial_model(selection=selection,evidence=inputs,reviews=reviews,joint_reviews=joint_reviews)
            if raw['readout.json']!=_json(report) or raw['report.txt']!=_text(report):
                raise ValueError('initial model export differs from its independent source reconstruction')
            return dict(selection=selection,inputs=inputs,evidence=evidence,report=report,new_native_calls=0,
                verification='ORIGINAL_SOURCE_PUBLICATIONS_AND_INDEPENDENT_ENDPOINT_RECONSTRUCTION')
        return _sources(selection,inputs,sources,reconstruct)
    return artifact_writer.verify_manifest_members(manifest,validate_members=consume,before_member=_exposed)


__all__=('InitialModelSource','InitialSourceDocument','InitialContrastDependency','InitialContrastReview',
    'InitialContribution','InitialContributionRealization','initial_contrast_evidence','read_initial_contributions',
    'prepare_initial_contribution_realization',
    'InitialModelCase','InitialModelSelection','InitialContrastEvidence','InitialJointRealization','InitialJointSupportReview',
    'InitialChemicalAlternative','InitialCaseEvidence','InitialModelEvidence','InitialModelAnalysisEvidence',
    'prepare_initial_model','prepare_matched_initial_model','empty_initial_evidence','read_initial_model_sources',
    'export_initial_model','read_initial_model_export','with_initial_model_sources')
