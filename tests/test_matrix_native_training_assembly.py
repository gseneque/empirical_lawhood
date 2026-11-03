# SPDX-License-Identifier: MPL-2.0
"""Real public metadata derivation over disclosed TEST input custody; no native."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import (
    PROTOCOL_ID,NativeTrainingAssemblyRequest,NativeTrainingAssemblySpecification)
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs,load_experiment_inputs,prepare_experiment
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection,ExperimentInputBinding

ROOT=Path(__file__).parents[1]


def test_current_copied_scientific_native_inputs_validate_without_authority():
    from empirical_lawhood.api.configuration import validate_configuration
    examples=ROOT/'programmes/foundations/emergent-structure/workflows/matrix-response-experiment'
    for name,consumer in (('assembly','matrix-native-training-input-assembly'),
            ('request','matrix-native-training-assembly-request'),
            ('scientific-protocol','matrix-native-training-scientific-protocol'),
            ('assay','matrix-native-training-response-assay')):
        result=validate_configuration(examples/('native-training-'+name+'.example.json'),consumer=consumer)
        assert result['status']=='VALIDATED' and result['authority_granted'] is False


def assembly_case(tmp_path, *, training_count=1):
    """Actual C before TRAIN, with explicitly disclosed software populations.

    The default allocated E3 counts remain TRAIN1/CAL20/CONF8/E6 2+2.
    Metadata-only controls can explicitly select the current TRAIN12 count.
    This new whole-C metadata control adds E4 4/4/4 and E5 DEV2/CONF4;
    the old unallocated E4 example labels 32/64/64 are archived externally.
    No selected scientific programme count or full selected-size proof changes.
    """
    from types import SimpleNamespace
    import json
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import ALL_PHASES, NativeTrainingResources
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    from empirical_lawhood.api.matrix_programme_allocations import publish_matrix_programme_allocations
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    from empirical_lawhood.api.codecs import load_authoring
    from tests.test_matrix_programme_allocations import _publisher_case
    from tests.test_matrix_programme_scientific_design import build_scientific_design

    design = build_scientific_design()
    counts = {'TRAIN': training_count, 'CALIBRATION': 20, 'EVALUATION': 8, 'TRANSFER_NEARBY': 2, 'TRANSFER_SHIFTED': 2}
    design = replace(design,
        e3=replace(design.e3, populations=tuple(replace(value, expected_units=counts[value.role])
            for value in design.e3.populations)),
        e3_calibration_criterion=replace(design.e3_calibration_criterion, minimum_group_count=20),
        e6=replace(design.e6, expected_groups=2))
    census = decode_canonical_record(json.loads((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/exposure-census.example.json').read_text()),
        MatrixFactorExposureCensus)
    plane, kwargs = _publisher_case(tmp_path, design, census)
    compiled = publish_matrix_programme_allocations(**kwargs)
    old = SimpleNamespace(plane=plane, programme_inputs=compiled.resolved, programme_commitment=compiled.commitment)
    copied = Path(plane.root.contract.canonical_path) / 'copied-assembly'
    copied.mkdir()
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 128 * 1024**2, 64 * 1024**2)
    resources = NativeTrainingResources('resources.native-training.control', tuple((phase, budget) for phase in ALL_PHASES), 4)
    campaign = load_authoring(ROOT / 'tests/fixtures/reference-campaign.json').campaign
    request = NativeTrainingAssemblyRequest('request.disclosed-native-training', resources, campaign)
    specification = NativeTrainingAssemblySpecification('assembly.disclosed-native-training', 'disclosed-native-assembly',
        compiled.resolved.scientific_design.e3.identity, request.identity, compiled.commitment)
    request_path = copied / 'request.json'
    request_path.write_bytes(request.canonical_bytes())
    spec_path = copied / 'specification.json'
    spec_path.write_bytes(specification.canonical_bytes())
    selector = ExperimentFileInputSelection('sources.disclosed-native-assembly', PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, request_path.name, request_path.stat().st_size),), ())
    source_path = copied / 'sources.json'
    source_path.write_bytes(selector.canonical_bytes())
    return old, specification, request, spec_path, source_path, kwargs['execution']


def test_public_native_input_preprocessing_commits_complete_future_panels_and_exact_replay(tmp_path,monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as workers
    monkeypatch.setattr('tests.test_matrix_e3_protected_public_lowering.prepared_case',
        lambda *a,**kw:pytest.fail('native inputs reconstructed an old protected preparation'))
    monkeypatch.setattr(workers,'execute_parameter_native_work',lambda *a,**kw:pytest.fail('metadata assembly entered native prefix'))
    monkeypatch.setattr(workers,'execute_paired_response_native_work',lambda *a,**kw:pytest.fail('metadata assembly entered native panels'))
    from empirical_lawhood.api import native_training_banks
    monkeypatch.setattr(native_training_banks, 'export_native_training_banks',
        lambda **_: pytest.fail('preTRAIN metadata entered native bank export'))
    old,specification,request,spec_path,source_path,execution=assembly_case(tmp_path)
    loaded=load_experiment_inputs(specification,source_path)
    initial=prepare_experiment(specification,method_inputs=loaded.method_inputs,execution=execution)
    assert not initial.executable and 'native-assembly.derive' in {value.code for value in initial.dependencies}
    target_root=Path(old.plane.root.contract.canonical_path)/'native-derived'
    kwargs=dict(specification_path=spec_path,source_selection_path=source_path,project_root=ROOT,artifact_writer=old.plane,
        metadata_directory=target_root,output_selection_path=target_root/'inputs/sources.json',execution=execution)
    first=derive_experiment_inputs(**kwargs)
    assert first.specification==specification.identity
    assert first.target_specification.candidate==old.programme_inputs.scientific_design.e3.identity
    assert first.preparation.executable
    assert first.preparation.census.native_effect_count==2
    actual=load_experiment_inputs(first.target_specification,first.source_selection_path).method_inputs.request
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_input_custody import read_protected_e3_original_publication
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    handle_path = target_root / 'inputs/train-unit-allocation-publication.json'
    handle_raw = handle_path.read_bytes()
    allocation_publication = decode_canonical_bytes(handle_raw, ArtifactWriteResult, maximum_bytes=len(handle_raw))
    assert allocation_publication.canonical_bytes() == handle_raw
    assert allocation_publication.materialization.relative_path == 'native-derived/publications/train-unit-allocation.json'
    assert allocation_publication.logical.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert allocation_publication.logical.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
    expected_allocation = native.training_allocation(first.target_specification, actual)
    allocation = read_protected_e3_original_publication(old.plane, allocation_publication, UnitAllocation)
    assert allocation == expected_allocation
    assert old.plane.root.resolve(allocation_publication.materialization.relative_path,
        for_write=False).read_bytes() == expected_allocation.canonical_bytes()
    assert any((row.logical, row.materialization, row.manifest_materialization) ==
        (allocation_publication.logical, allocation_publication.materialization,
            allocation_publication.manifest_materialization) for row in first.publications)
    assert not (Path(old.plane.root.contract.canonical_path) / 'runs').exists()
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_future_response_selections
    future=authenticate_future_response_selections(old.plane,actual)
    assert tuple(role for role,_ in future)==('CALIBRATION','EVALUATION','TRANSFER_NEARBY','TRANSFER_SHIFTED')
    assert len(actual.campaign.evidence_state)==7 and len(actual.exposure_support)==8
    from empirical_lawhood.planning.approval import SystemDecisionClock
    monkeypatch.setattr(SystemDecisionClock,'now_utc',lambda self:pytest.fail('exact retry replaced original pre-TRAIN availability'))
    second=derive_experiment_inputs(**kwargs)
    assert first.target_specification==second.target_specification
    assert first.source_selection==second.source_selection
    assert first.preparation==second.preparation
    assert handle_path.read_bytes() == handle_raw
    assert first.target_specification_path.read_bytes()==first.target_specification.canonical_bytes()
    from empirical_lawhood.api.experiment_preparation import _authenticate_derived_target
    manifest=old.plane.read_manifest(first.target_specification_path.relative_to(old.plane.root.contract.canonical_path).as_posix())
    assert manifest.publication is not None
    marker=old.plane.root.resolve(manifest.publication.commit_marker_relative_path,for_write=False)
    original_marker=marker.read_bytes()
    try:
        marker.write_bytes(b'changed disposable TEST publication commit')
        with pytest.raises((ValueError,PermissionError,RuntimeError)):
            _authenticate_derived_target(first,old.plane)
    finally:
        marker.write_bytes(original_marker)
    # A changed source definition refuses exact replay before native/issue.
    changed=replace(request,resources=replace(request.resources,record_id=request.resources.record_id+'.foreign'))
    changed_spec=replace(specification,request=changed.identity)
    source_path.parent.joinpath('request.json').write_bytes(changed.canonical_bytes())
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    selected=decode_canonical_bytes(source_path.read_bytes(),ExperimentFileInputSelection,maximum_bytes=None)
    selected=replace(selected,bindings=(replace(selected.bindings[0],identity=changed.identity,maximum_bytes=len(changed.canonical_bytes())),))
    source_path.write_bytes(selected.canonical_bytes());spec_path.write_bytes(changed_spec.canonical_bytes())
    with pytest.raises((ValueError,PermissionError,RuntimeError)):
        derive_experiment_inputs(**kwargs)


def test_direct_math_and_assay_preserve_existing_per_root_canonical_outputs(tmp_path):
    """Current source operands retain the independent original math/assay bytes."""
    from tests.test_matrix_native_training_protocol import scientific_inputs
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    scientific, assay = scientific_inputs()
    old, *_ = assembly_case(tmp_path)
    actual = old.programme_inputs
    assert scientific.canonical_bytes() == actual.scientific_design.training_protocol.canonical_bytes()
    future = actual.phase('e3.calibration')
    selection = future.native_specification.selection
    assert scientific.numerical_design.canonical_bytes() == selection.numerical_design.canonical_bytes()
    assert tuple(value.canonical_bytes() for value in scientific.prefix_policies) == tuple(
        value.canonical_bytes() for value in selection.prefix_policies)
    assert scientific.coordinate_policies == selection.coordinate_policies
    index = ScheduledSourceIndex.from_shared(reservation=future.reservation,
        specification=future.native_specification, provenances=(actual.producing_provenance,))
    for protocol in future.responses.protocols:
        source = index.resolve(index.reference(source_id=protocol.public_source.source.object_id,
            root_id=protocol.public_source.root.root_id, provenance=actual.producing_provenance.identity))
        bound = assay.bind(source, protocol_id=protocol.protocol_id)
        assert bound.canonical_bytes() == protocol.canonical_bytes()
        assert bound.templates.canonical_bytes() == protocol.templates.canonical_bytes()


def test_native_assembly_refuses_missing_operands_and_mixed_candidate_before_publication(tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import bind_inputs
    _, specification, request, _, source, execution = assembly_case(tmp_path)
    with pytest.raises(TypeError, match='actual programme commitment'):
        replace(specification, input_commitments=None)
    with pytest.raises(ValueError, match='only its exact current'):
        bind_inputs(specification, {'request': request, 'scientific-protocol': object()})
    with pytest.raises(ValueError, match='frozen request pin'):
        bind_inputs(specification, {'request': replace(request, record_id=request.record_id+'.foreign')})
    inputs = load_experiment_inputs(specification, source)
    stopped = prepare_experiment(specification, method_inputs=inputs.method_inputs, execution=replace(execution, workers=2))
    assert 'native-assembly.worker-selection' in {value.code for value in stopped.dependencies}


@pytest.mark.parametrize('damage', ('candidate', 'normalization-bytes', 'template-bytes', 'census-bytes'))
def test_direct_scientific_file_refusals_precede_any_publication(tmp_path, monkeypatch, damage):
    from empirical_lawhood.api.domain_composition.matrix_native_training_assembly.assembly import assemble_native_training_inputs
    old, specification, request, _, source, execution = assembly_case(tmp_path)
    original = old.programme_inputs.commitments
    if damage == 'candidate':
        specification = replace(specification, candidate=replace(specification.candidate, object_fingerprint='f'*64))
    else:
        publication = (original.support_files[0][1] if damage == 'normalization-bytes' else
            old.programme_inputs.phase('train').responses.template_publications[0] if damage == 'template-bytes' else
            original.exposure_census.publication)
        path = old.plane.root.resolve(publication.materialization.relative_path, for_write=False)
        raw = path.read_bytes()
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    monkeypatch.setattr(old.plane, 'write', lambda *a, **kw: pytest.fail('refused scientific input published metadata'))
    target = Path(old.plane.root.contract.canonical_path) / 'refused-native'
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        assemble_native_training_inputs(assembly_specification=specification, request=request, request_path=source.parent/'request.json',
            project_root=ROOT, artifact_writer=old.plane, metadata_directory=target,
            output_selection_path=target/'inputs/sources.json', execution=execution)
    assert not target.exists()


def test_nested_source_selector_stays_immutable_in_requirements_serialization():
    from empirical_lawhood.kernel.serialization import canonical_json_bytes,canonical_json_document_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    selected=ExperimentFileInputSelection('selection.disclosed-nested','protocol.disclosed-nested',(),())
    raw=canonical_json_bytes({'source_selection':selected})
    import json
    nested=canonical_json_document_bytes(json.loads(raw)['source_selection'])
    assert decode_canonical_bytes(nested,ExperimentFileInputSelection,maximum_bytes=None)==selected


def test_current_c_backed_specification_keeps_original_policy_and_refuses_source_substitution(tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import bind_inputs
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    old, specification, request, _, _, _ = assembly_case(tmp_path)
    assert bind_inputs(specification, {'request': request}).method_inputs.request is request
    assert decode_canonical_bytes(request.canonical_bytes(), type(request), maximum_bytes=None) == request
    assert specification.input_commitments == old.programme_commitment
    assert not hasattr(request, 'input_commitments')
    original_policy = old.programme_inputs.e6_policy
    assert original_policy.criterion == old.programme_inputs.scientific_design.e6_policy.criterion
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import validate_e6_transport_criterion
    for changes in ({'null_success_numerator': 1, 'null_success_denominator': 3},
            {'alpha_denominator': 480},
            {'family_slots': tuple(sorted('e1.foreign' if value == 'e1.recurrence-survival' else value
                for value in original_policy.criterion.family_slots))},
            {'minimum_usable_groups': old.programme_inputs.scientific_design.e3.population('TRANSFER_NEARBY').expected_units + 1}):
        with pytest.raises(ValueError, match='E6 criterion changes original'):
            validate_e6_transport_criterion(replace(original_policy.criterion, **changes), old.programme_inputs.scientific_design.e3)
    with pytest.raises(ValueError, match='exact current candidate/request edition'):
        replace(specification, request=replace(request.identity, object_version='1.0.0'))
    with pytest.raises(ValueError, match='exact current scientific record edition'):
        replace(specification, input_commitments=replace(specification.input_commitments,
            record=replace(specification.input_commitments.record, object_version='0.0.0')))


def test_transport_policy_is_published_and_freshly_authenticated_before_train(tmp_path,monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as workers
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import (
        authenticate_e6_transport_policy,authenticate_future_response_selections)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.time import AvailabilitySpec
    monkeypatch.setattr(workers,'execute_parameter_native_work',lambda *a,**kw:pytest.fail('policy assembly acquired prefix'))
    monkeypatch.setattr(workers,'execute_paired_response_native_work',lambda *a,**kw:pytest.fail('policy assembly acquired future'))
    old,specification,request,spec_path,source_path,execution=assembly_case(tmp_path)
    specification=replace(specification,request=request.identity)
    request_path=source_path.parent/'request.json'
    request_path.write_bytes(request.canonical_bytes());spec_path.write_bytes(specification.canonical_bytes())
    source=decode_canonical_bytes(source_path.read_bytes(),ExperimentFileInputSelection,maximum_bytes=None)
    source=replace(source,bindings=(replace(source.bindings[0],identity=request.identity,
        maximum_bytes=len(request.canonical_bytes())),))
    source_path.write_bytes(source.canonical_bytes())
    destination=Path(old.plane.root.contract.canonical_path)/'transport-derived'
    result=derive_experiment_inputs(specification_path=spec_path,source_selection_path=source_path,
        project_root=ROOT,artifact_writer=old.plane,metadata_directory=destination,
        output_selection_path=destination/'inputs/sources.json',execution=execution)
    actual=load_experiment_inputs(result.target_specification,result.source_selection_path).method_inputs.request
    raw=(destination/'inputs/e6-transport-policy.json').read_bytes()
    policy=decode_canonical_bytes(raw,MatrixE6EmpiricalTransportPolicy,maximum_bytes=None)
    future=authenticate_future_response_selections(old.plane,actual)
    assert len(actual.campaign.evidence_state)==7 and len(actual.exposure_support)==8
    assert policy.identity in actual.campaign.evidence_state
    assert policy.criterion==old.programme_inputs.scientific_design.e6_policy.criterion
    assert authenticate_e6_transport_policy(old.plane,actual,policy,future_selections=future)==policy
    changed=replace(policy,criterion=replace(policy.criterion,
        normalized_error_maximum=policy.criterion.normalized_error_maximum+Decimal('.01')))
    with pytest.raises(PermissionError,match='differs'):
        authenticate_e6_transport_policy(old.plane,actual,changed,future_selections=future)
    with pytest.raises(ValueError,match='omits|substitutes'):
        authenticate_e6_transport_policy(old.plane,actual,policy,future_selections=future[:-1])
    for schema in (MatrixE6EmpiricalTransportPolicy.SCHEMA,AvailabilitySpec.SCHEMA):
        _,publication=next((artifact,publication) for artifact,publication in actual.exposure_support
            if artifact.payload_schema==schema)
        path=old.plane.root.resolve(publication.materialization.relative_path,for_write=False)
        original=path.read_bytes()
        try:
            path.write_bytes(b'changed disposable TEST commitment')
            with pytest.raises((ValueError,PermissionError,RuntimeError)):
                authenticate_e6_transport_policy(old.plane,actual,policy,future_selections=future)
        finally:path.write_bytes(original)
    assert authenticate_e6_transport_policy(old.plane,actual,policy,future_selections=future)==policy
