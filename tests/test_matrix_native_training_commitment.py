# SPDX-License-Identifier: MPL-2.0
"""Current TRAIN commitment shapes; unpublished metadata grants no authority.

The pure request controls deliberately use an UNWRITTEN publication descriptor.
They never authenticate that descriptor or assert original custody, source
eligibility, execution, scientific qualification or an actual programme C.
"""
from dataclasses import MISSING, fields, replace
import importlib.abc
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


class _NoApiImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('empirical_lawhood.api'):
            raise AssertionError('pure TRAIN commitment contract imported API: '+fullname)


_before_imports = set(sys.modules)
_guard = _NoApiImports()
sys.meta_path.insert(0, _guard)
try:
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_assembly as assembly
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
finally:
    sys.meta_path.remove(_guard)

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, LogicalArtifactIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

_contract_imports = set(sys.modules)


def _unwritten_commitment(*, kind=MatrixProgrammeInputCommitments):
    """Typed proposed handle only: no C body, seal, publication or signer exists."""
    reference = ObjectIdentity('commitments.unwritten', kind.SCHEMA, kind.VERSION, 'a'*64)
    generic = ArtifactGenericValidation('validator.unwritten', '1.0.0', 'b'*64,
        kind.SCHEMA, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity('artifact.unwritten', reference.object_fingerprint, kind.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', VisibilityCeiling.PROSPECTIVE, (),
        OutcomeAccess.OUTCOME_BLIND, generic)
    physical = ArtifactMaterialization('materialization.unwritten', logical.logical_artifact_id,
        'storage.unwritten', 'UNWRITTEN/commitments.json', reference.object_fingerprint, 100, 'none')
    proposed = ArtifactWriteResult(logical, physical, replace(physical,
        materialization_id='materialization.unwritten.sidecar', relative_path=physical.relative_path+'.manifest.json'), False)
    return MatrixProgrammePublishedInput(reference, proposed)


@pytest.fixture
def unissued_assembly():
    # Only these unchanged pure nested records are selected from the exposed
    # example; its enclosing authoring request is not decoded or admitted.
    path = Path(__file__).parents[1]/'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-request.example.json'
    body = json.loads(path.read_text())['value']
    resources = decode_canonical_record(body['resources'], native.NativeTrainingResources)
    campaign = decode_canonical_record(body['campaign'], CampaignSpec)
    request = assembly.NativeTrainingAssemblyRequest('request.unwritten', resources, campaign)
    candidate = ObjectIdentity('candidate.unwritten', ConfiguredProtectedE3Specification.SCHEMA,
        ConfiguredProtectedE3Specification.VERSION, 'c'*64)
    specification = assembly.NativeTrainingAssemblySpecification('assembly.unwritten', 'namespace.unwritten',
        candidate, request.identity, _unwritten_commitment())
    execution = ExecutionSelection(resources.maximum_parallel_tasks, 'environment.unwritten',
        ObjectIdentity('source.unwritten','empirical-lawhood/testing/unwritten-source','1.0.0','d'*64),
        '/media/chevre/EL/empirical-lawhood/checks/UNWRITTEN')
    return specification, request, execution


def test_current_assembly_has_exact_three_operational_fields_and_required_c_in_specification(unissued_assembly):
    specification, request, _ = unissued_assembly
    assert tuple(field.name for field in fields(type(request)))==('record_id','resources','campaign')
    assert all(field.default is MISSING and field.default_factory is MISSING for field in fields(type(request)))
    assert tuple(kind.__name__ for kind in assembly.input_record_types())==(
        'NativeTrainingAssemblyRequest','NativeTrainingScientificProtocol','MatrixFactorExposureCensus','ScheduledResponseAssay')
    for value in (specification,request):
        assert decode_canonical_bytes(value.canonical_bytes(),type(value),maximum_bytes=None)==value
    assert tuple(field.name for field in fields(type(specification))) == (
        'specification_id', 'namespace', 'candidate', 'request', 'input_commitments')
    assert all(field.default is MISSING and field.default_factory is MISSING for field in fields(type(specification)))
    assert specification.input_commitments.publication.created is False


@pytest.mark.parametrize('kind',('request','specification'))
@pytest.mark.parametrize('version',('1.0.0','2.0.0','0.0.0','9.0.0'))
def test_assembly_rejects_obsolete_and_unknown_record_editions(unissued_assembly,kind,version):
    specification, request, _ = unissued_assembly
    value = request if kind=='request' else specification
    document = value.to_document()
    document['version'] = version
    with pytest.raises(ValueError):
        decode_canonical_record(document,type(value))


@pytest.mark.parametrize('field',('input_commitments','scientific_protocol','assay','census','root_seed_material_sha256','future_seed_material_sha256'))
def test_current_assembly_rejects_independent_old_allocation_and_science_fields(unissued_assembly,field):
    _, request, _ = unissued_assembly
    document = request.to_document()
    document['value'][field] = None
    with pytest.raises(ValueError):
        decode_canonical_record(document,type(request))


@pytest.mark.parametrize('replacement',(None,'identity-only','wrong-current-kind'))
def test_assembly_requires_exact_current_whole_commitment_handle(unissued_assembly,replacement):
    specification, _, _ = unissued_assembly
    value = None if replacement is None else specification.input_commitments.record if replacement=='identity-only' else \
        _unwritten_commitment(kind=ConfiguredProtectedE3Specification)
    with pytest.raises((TypeError,ValueError),match='commitment|record edition'):
        replace(specification,input_commitments=value)


def test_assembly_refuses_a_different_frozen_request(unissued_assembly):
    specification, request, _ = unissued_assembly
    with pytest.raises(ValueError,match='frozen request pin'):
        assembly.validate_request(specification,replace(request,record_id='request.other.unwritten'))


@pytest.mark.parametrize('extra',('scientific-protocol','census','selection','blueprint'))
def test_assembly_bind_accepts_only_current_request_and_no_old_source_bundle(unissued_assembly,extra):
    specification, request, _ = unissued_assembly
    with pytest.raises(ValueError,match='operational request'):
        assembly.bind_inputs(specification,{'request':request,extra:request})
    with pytest.raises(ValueError,match='operational request'):
        assembly.bind_inputs(specification,{'request':request},files={'unused-file':object()})


def test_assembly_prepare_never_reads_unwritten_c_or_claims_executable_native_work(unissued_assembly,monkeypatch):
    specification, request, execution = unissued_assembly
    def forbidden(*_args,**_kwargs):
        raise AssertionError('static preparation tried to open unpublished custody')
    monkeypatch.setattr(Path,'open',forbidden)
    monkeypatch.setattr('builtins.open',forbidden)
    bound = assembly.bind_inputs(specification,{'request':request},record_paths={'request':Path('/UNWRITTEN/request.json')})
    result = assembly.prepare(specification,execution=execution,method_inputs=bound.method_inputs)
    assert result.census.native_effect_count==0 and result.census.role_counts==()
    assert not result.executable
    assert tuple(value.code for value in result.dependencies)==('native-assembly.derive',)
    assert bound.method_inputs.request is request


def test_assembly_missing_request_and_resources_remain_explicit_dependencies(unissued_assembly):
    specification, request, execution = unissued_assembly
    result = assembly.prepare(specification,execution=ExecutionSelection())
    assert {value.code for value in result.dependencies}=={'native-assembly.request',
        'native-assembly.execution.workers','native-assembly.execution.environment-id',
        'native-assembly.execution.source-snapshot','native-assembly.execution.output-root'}
    bound = assembly.bind_inputs(specification,{'request':request})
    result = assembly.prepare(specification,execution=replace(execution,workers=execution.workers+1),
        method_inputs=bound.method_inputs)
    assert {value.code for value in result.dependencies}=={'native-assembly.derive','native-assembly.worker-selection'}
    assert result.census.native_effect_count==0


def test_train_request_v3_has_no_optional_or_implicit_c():
    names = tuple(field.name for field in fields(native.NativeTrainingAcquisitionRequest))
    assert names[-1]=='input_commitments'
    assert fields(native.NativeTrainingAcquisitionRequest)[-1].default is MISSING
    assert native.NativeTrainingAcquisitionRequest.VERSION=='3.0.0'
    operands = dict.fromkeys(names)
    operands['record_id'] = 'request.unwritten'
    del operands['input_commitments']
    with pytest.raises(TypeError,match='input_commitments'):
        native.NativeTrainingAcquisitionRequest(**operands)
    with pytest.raises(TypeError,match='complete pre-acquisition programme commitment'):
        native.NativeTrainingAcquisitionRequest(**operands,input_commitments=None)


@pytest.mark.parametrize('version',('1.0.0','2.0.0','9.0.0'))
def test_train_request_rejects_obsolete_and_unknown_editions_before_operand_decoding(version):
    document = {'schema':native.NativeTrainingAcquisitionRequest.SCHEMA,'version':version,'value':{}}
    with pytest.raises(ValueError):
        decode_canonical_record(document,native.NativeTrainingAcquisitionRequest)


def test_pure_training_request_contract_imports_no_new_api_owner():
    assert not any(name.startswith('empirical_lawhood.api') for name in _contract_imports-_before_imports)


@pytest.fixture(scope='module')
def current_committed_train(tmp_path_factory):
    """Actual frozen-source metadata publication; no issued or native execution.

    This fixture is deliberately separate from the UNWRITTEN pure descriptors
    above and must run only in the coordinator's committed-source check lane.
    """
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as workers
    from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs
    from tests.test_matrix_native_training_assembly import ROOT, assembly_case

    def forbidden(*_args,**_kwargs):
        raise AssertionError('TRAIN commitment metadata control attempted native acquisition')
    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(workers,'execute_parameter_native_work',forbidden)
        guard.setattr(workers,'execute_paired_response_native_work',forbidden)
        original,assembly_specification,assembly_request,specification_path,selection_path,execution = assembly_case(
            tmp_path_factory.mktemp('actual-current-train-commitment'))
        root = Path(original.plane.root.contract.canonical_path)
        directory = root/'commitment-derived'
        derived = derive_experiment_inputs(specification_path=specification_path,source_selection_path=selection_path,
            project_root=ROOT,artifact_writer=original.plane,metadata_directory=directory,
            output_selection_path=directory/'inputs/sources.json',execution=execution)
        request = load_experiment_inputs(derived.target_specification,derived.source_selection_path).method_inputs.request
    assert not (root/'runs').exists()
    return SimpleNamespace(original=original,assembly_specification=assembly_specification,assembly_request=assembly_request,request=request,
        specification=derived.target_specification,root=root)


def _actual_committed_references(case):
    original = case.original.programme_inputs.commitments
    values = {'C':case.request.input_commitments,'availability':original.availability,'e6-policy':original.e6_policy}
    values.update((role,original.phase(role).responses) for role in (
        'e3.calibration','e3.confirmation','e6.nearby','e6.shifted'))
    return values


def test_actual_train_request_v3_keeps_all_seven_original_commitments_and_exact_custody(current_committed_train):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_programme_commitment
    case = current_committed_train
    request = case.request
    native.validate_request(case.specification,request)
    resolved = authenticate_programme_commitment(case.original.plane,request)
    assert resolved==case.original.programme_inputs
    assert request.input_commitments==case.original.programme_commitment==case.assembly_specification.input_commitments
    rows = native.future_response_support(request)
    expected = _actual_committed_references(case)
    assert len(rows)==len(request.campaign.evidence_state)==7
    assert {reference:publication for reference,_,publication in rows}=={
        value.record:value.publication for value in expected.values()}
    assert tuple(reference for reference,_,_ in rows)==request.campaign.evidence_state
    assert decode_canonical_bytes(request.canonical_bytes(),type(request),maximum_bytes=None)==request
    assert not (case.root/'runs').exists()


@pytest.mark.parametrize('role',('C','availability','e6-policy','e3.calibration','e3.confirmation','e6.nearby','e6.shifted'))
def test_actual_train_request_cannot_omit_any_original_pretrain_commitment(current_committed_train,role):
    case = current_committed_train
    selected = _actual_committed_references(case)[role].record
    changed = replace(case.request,campaign=replace(case.request.campaign,
        evidence_state=tuple(value for value in case.request.campaign.evidence_state if value!=selected)))
    with pytest.raises(ValueError,match='whole programme|exactly once'):
        native.future_response_support(changed)


@pytest.mark.parametrize('damage',('missing-c-support','file-copy','different-publication','source-byte-limit'))
def test_actual_train_request_refuses_missing_or_substituted_original_support(current_committed_train,damage):
    case = current_committed_train
    request = case.request
    reference,artifact,publication = next(row for row in native.future_response_support(request)
        if row[0]==request.input_commitments.record)
    if damage=='missing-c-support':
        changed = replace(request,exposure_support=tuple(row for row in request.exposure_support if row[0]!=artifact))
    elif damage=='file-copy':
        copied = ExperimentFileInputBinding(artifact.artifact_id,artifact,reference.object_version,
            publication.materialization.relative_path,artifact.size_bytes)
        changed = replace(request,exposure_support=tuple((value,copied if value==artifact else custody)
            for value,custody in request.exposure_support))
    elif damage=='different-publication':
        substituted = replace(publication,materialization=replace(publication.materialization,
            relative_path='UNWRITTEN/substituted-commitment.json'))
        changed = replace(request,exposure_support=tuple((value,substituted if value==artifact else custody)
            for value,custody in request.exposure_support))
    else:
        resources = replace(request.resources,budgets=tuple((name,replace(budget,source_scan_bytes=1)
            if name=='entry' else budget) for name,budget in request.resources.budgets))
        changed = replace(request,resources=resources)
    with pytest.raises(ValueError,match='programme|exactly once|FILE|byte budget'):
        native.future_response_support(changed)


@pytest.mark.parametrize('damage',('different-c','different-math','different-source'))
def test_actual_train_request_independently_joins_the_original_c_body(current_committed_train,damage):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import validate_request_programme_inputs
    case = current_committed_train
    request = case.request
    if damage=='different-c':
        changed = replace(request,input_commitments=_unwritten_commitment())
    elif damage=='different-math':
        changed = replace(request,mathematical_protocol=replace(request.mathematical_protocol,
            protocol_id='protocol.foreign.unwritten'))
    else:
        changed = replace(request,sources=(replace(request.sources[0],source_id='source.foreign.unwritten'),
            *request.sources[1:]))
    with pytest.raises(PermissionError,match='whole programme'):
        validate_request_programme_inputs(changed,case.original.programme_inputs)
