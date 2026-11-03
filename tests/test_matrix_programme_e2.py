# SPDX-License-Identifier: MPL-2.0
"""Exposed C-to-E2 metadata controls; no acquisition or qualification."""
from dataclasses import fields, replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as utility
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import ALL_PHASES, NativeTrainingResources
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e2_assembly as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
from empirical_lawhood.api import matrix_programme_e2 as owner
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from tests.test_matrix_programme_allocations import census as census  # noqa: F401

ROOT = Path(__file__).parents[1]


def assembly_case(tmp_path, census, *, count):
    """Actual published C with an explicit exposed E2 size of one or three."""
    from empirical_lawhood.api.codecs import load_authoring
    from empirical_lawhood.api.matrix_programme_allocations import publish_matrix_programme_allocations
    from tests.test_matrix_programme_allocations import _publisher_case
    from tests.test_matrix_programme_scientific_design import build_scientific_design

    design = build_scientific_design()
    design = replace(design, e2=replace(design.e2, expected_units=count))
    writer, arguments = _publisher_case(tmp_path, design, census)
    published = publish_matrix_programme_allocations(**arguments)
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 256 * 1024**2, 64 * 1024**2)
    resources = NativeTrainingResources('resources.disclosed.current-e2', tuple((phase, budget) for phase in ALL_PHASES), 4)
    aggregate = ResourceBudget.aggregate(tuple(resources.for_operation(phase) for phase in utility.ALL_PHASES
        for _ in range(1 if phase in ('entry', 'terminal') else count)))
    campaign = replace(load_authoring(ROOT / 'tests/fixtures/reference-campaign.json').campaign,
        budget=aggregate)
    request = domain.MatrixProgrammeE2AssemblyRequest('request.disclosed.current-e2-assembly', resources, campaign)
    specification = domain.MatrixProgrammeE2AssemblySpecification('assembly.disclosed.current-e2', request.identity, published.commitment)
    directory = Path(writer.root.contract.canonical_path) / 'e2-assembled'
    return dict(specification=specification, request=request, project_root=ROOT, artifact_writer=writer,
        metadata_directory=directory, output_selection_path=directory / 'inputs/sources.json',
        execution=arguments['execution']), published


@pytest.fixture
def assembled_case(tmp_path, census):  # noqa: F811
    return assembly_case(tmp_path, census, count=1)


def _inventory(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob('*') if path.is_file()}


def _forbid_acquisition(monkeypatch):
    from tests.test_matrix_programme_allocations import _forbid_acquisition as forbid
    forbid(monkeypatch)


def test_current_e2_request_has_no_train_or_manual_source_roster(assembled_case):
    kwargs, _ = assembled_case
    request, specification = kwargs['request'], kwargs['specification']
    assert {field.name for field in fields(request)} == {'record_id', 'resources', 'campaign'}
    assert specification.input_commitments == assembled_case[1].commitment
    for value in (request, specification):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
        with pytest.raises(ValueError):
            decode_canonical_record({**value.to_document(), 'version': '1.0.0'}, type(value))
    with pytest.raises(TypeError, match='actual programme commitment'):
        replace(specification, input_commitments=None)
    assert domain.bind_inputs(specification, {'request': request}).method_inputs is request
    prepared = domain.prepare(specification, execution=kwargs['execution'], method_inputs=request)
    assert prepared.draft is None
    assert prepared.census.native_effect_count == 0
    assert {value.code for value in prepared.dependencies} == {'programme-e2.derive'}
    with pytest.raises(ValueError, match='only its current operational'):
        domain.bind_inputs(specification, {'request': request, 'train-request': object()})
    with pytest.raises(ValueError, match='frozen request'):
        domain.bind_inputs(specification, {'request': replace(request, record_id='request.foreign-e2')})


@pytest.mark.parametrize('count', (1, 3))
def test_actual_c_derives_complete_current_e2_and_exact_replay_without_native(tmp_path, census, monkeypatch, count):  # noqa: F811
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex

    kwargs, actual = assembly_case(tmp_path, census, count=count)
    _forbid_acquisition(monkeypatch)
    from empirical_lawhood.api import selected_e4_bank_recipe
    from empirical_lawhood.infrastructure import numerical_provenance, source_closure
    observed_captures,observed_archives,observed_runtime=[],[],[]
    actual_capture=source_closure.capture_admitted_target_source
    actual_git=source_closure._git
    actual_runtime=numerical_provenance.numerical_runtime_observation
    def capture(*args,**kwargs):
        source=actual_capture(*args,**kwargs)
        observed_captures.append(source)
        return source
    def git(root,*args):
        if args[0]=="archive":observed_archives.append(args)
        return actual_git(root,*args)
    def runtime():
        value=actual_runtime()
        observed_runtime.append(value)
        return value
    def raw_inventory(*_a,**_kw):
        pytest.fail("E2 assembly rebuilt an already admitted package/lock inventory")
    monkeypatch.setattr(source_closure,"capture_admitted_target_source",capture)
    monkeypatch.setattr(selected_e4_bank_recipe,"capture_admitted_target_source",capture)
    monkeypatch.setattr(source_closure,"_git",git)
    monkeypatch.setattr(numerical_provenance,"numerical_runtime_observation",runtime)
    monkeypatch.setattr(numerical_provenance,"numerical_package_sources",raw_inventory)
    monkeypatch.setattr(numerical_provenance,"selected_dependency_lock_sha256",raw_inventory)
    result = owner.assemble_programme_e2(**kwargs)
    assert len(observed_captures)==len(observed_archives)==1 and len(observed_runtime)==3
    inputs = load_experiment_inputs(result.target_specification, result.source_selection_path)
    request = inputs.method_inputs.request
    original = actual.resolved.phase('e2')
    design = actual.resolved.scientific_design.e2
    assert type(request) is utility.NativeUtilityRequest and request.VERSION == '2.0.0'
    assert request.source_manifest.reservation == original.reservation
    assert request.source_manifest.native_specification == original.native_specification
    assert request.source_manifest.provenances == (actual.resolved.producing_provenance,)
    assert request.source_manifest.scalar_definition == design.scalar_definition
    assert request.source_manifest.audit == actual.resolved.exposure_audit
    assert request.mathematical_protocol == design.mathematical_protocol
    assert result.target_specification.criterion == design.criterion
    assert request.protocols == tuple(sorted(original.responses.protocols, key=lambda value: value.protocol_id))
    assert request.panels == tuple(sorted((panel for _, panels in original.responses.panels for panel in panels),
        key=lambda value: value.panel_id))
    assert request.template_publications == original.responses.template_publications
    assert request.exposure_support == exposure_support(actual.resolved.exposure_audit)
    assert len(request.exposure_support) == 1
    assert actual.commitment.record in request.campaign.evidence_state
    assert request.campaign.budget == kwargs['request'].campaign.budget
    assert request.campaign.authority_policy == kwargs['request'].campaign.authority_policy
    assert request.campaign.decision_rights == kwargs['request'].campaign.decision_rights
    assert tuple(name for name, _ in request.resources.budgets) == utility.ALL_PHASES
    assert 'feature' not in dict(request.resources.budgets)
    index = ScheduledSourceIndex.from_shared(reservation=original.reservation,
        specification=original.native_specification, provenances=request.source_manifest.provenances)
    index.require_roster(request.sources, expected_root_ids=index.root_ids)
    assert tuple(source.source_id for source in request.sources) == tuple(
        protocol.public_source.source.object_id for protocol in original.responses.protocols)
    protocols = {value.public_source.root.root_id: value for value in request.protocols}
    for source in request.sources:
        protocols[source.root_id].public_source.validate_source(index.resolve(source))
    assert len(request.sources) == count == actual.resolved.scientific_design.e2.expected_units
    assert len(result.preparation.draft.operations) == 8 * count + 2
    assert result.preparation.dependencies == ()
    assert result.preparation.census.native_effect_count == 2 * count
    artifact = design.assay.array_artifact
    file, = inputs.method_inputs.files
    assert file[0] == artifact.artifact_id and file[1].identity == artifact
    copied_template = kwargs['metadata_directory'] / 'inputs' / (artifact.sha256 + '.npz')
    original_template, = (value for value in original.responses.template_publications
        if value.logical.logical_artifact_id == artifact.artifact_id)
    assert copied_template.read_bytes() == kwargs['artifact_writer'].root.resolve(
        original_template.materialization.relative_path, for_write=False).read_bytes()
    assert not tuple(Path(kwargs['artifact_writer'].root.contract.canonical_path).rglob('native-subwork'))
    before = _inventory(kwargs['metadata_directory'])
    replay = owner.assemble_programme_e2(**kwargs)
    assert len(observed_captures)==len(observed_archives)==2 and len(observed_runtime)==6
    assert observed_captures[0] is not observed_captures[1]
    assert replay.target_specification == result.target_specification
    assert before == _inventory(kwargs['metadata_directory'])


def test_public_copied_request_derives_existing_native_utility_protocol(assembled_case, monkeypatch):
    from empirical_lawhood.api.configuration import validate_configuration
    from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs

    kwargs, _ = assembled_case
    _forbid_acquisition(monkeypatch)
    copied = Path(kwargs['artifact_writer'].root.contract.canonical_path) / 'copied-e2-assembly'
    copied.mkdir()
    specification, request = kwargs['specification'], kwargs['request']
    (copied / 'specification.json').write_bytes(specification.canonical_bytes())
    (copied / 'request.json').write_bytes(request.canonical_bytes())
    selector = ExperimentFileInputSelection('inputs.disclosed.current-e2-assembly', domain.PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, 'request.json', len(request.canonical_bytes())),), ())
    (copied / 'sources.json').write_bytes(selector.canonical_bytes())
    assert validate_configuration(copied / 'specification.json', consumer='matrix-programme-e2-assembly')['status'] == 'VALIDATED'
    result = derive_experiment_inputs(specification_path=copied / 'specification.json', source_selection_path=copied / 'sources.json',
        project_root=ROOT, artifact_writer=kwargs['artifact_writer'], metadata_directory=kwargs['metadata_directory'],
        output_selection_path=kwargs['output_selection_path'], execution=kwargs['execution'])
    assert result.source_selection.protocol_id == acquisition.PROTOCOL_ID
    assert type(result.target_specification) is utility.NativeUtilitySpecification
    assert type(load_experiment_inputs(result.target_specification, result.source_selection_path).method_inputs.request) is utility.NativeUtilityRequest


def test_original_c_mutation_during_e2_publication_refuses_final_return(assembled_case, monkeypatch):
    kwargs, actual = assembled_case
    _forbid_acquisition(monkeypatch)
    writer, observed = kwargs['artifact_writer'], []
    original_write = writer.write
    path = writer.root.resolve(actual.commitment.publication.materialization.relative_path, for_write=False)

    def mutate(request):
        result = original_write(request)
        if request.relative_path.endswith('/inputs/native-utility-specification.json'):
            raw = path.read_bytes()
            path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
            observed.append(request.logical_artifact_id)
        return result

    monkeypatch.setattr(writer, 'write', mutate)
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        owner.assemble_programme_e2(**kwargs)
    assert len(observed) == 1


@pytest.mark.parametrize('damage', ('census-bytes', 'provenance', 'campaign-budget', 'output-budget'))
def test_changed_originals_or_insufficient_budget_refuse_before_e2_publication(assembled_case, monkeypatch, damage):
    from empirical_lawhood.api import matrix_numerical_provenance

    kwargs, actual = assembled_case
    _forbid_acquisition(monkeypatch)
    selected = kwargs['request']
    if damage == 'census-bytes':
        path = kwargs['artifact_writer'].root.resolve(
            actual.resolved.commitments.exposure_census.publication.materialization.relative_path, for_write=False)
        raw = path.read_bytes()
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    elif damage == 'provenance':
        original = actual.resolved.producing_provenance
        changed_sources = tuple((name, 'a' * 64 if index == 0 else digest)
            for index, (name, digest) in enumerate(original.package_sources))
        foreign = replace(original, package_sources=changed_sources,
            code_sources_sha256=sha256(canonical_json_bytes(changed_sources)).hexdigest())
        monkeypatch.setattr(matrix_numerical_provenance, 'capture_matrix_provenance', lambda **_: foreign)
    elif damage == 'campaign-budget':
        selected = replace(selected, campaign=replace(selected.campaign,
            budget=ResourceBudget(1, 1, 0, None, None, None)))
    else:
        selected = replace(selected, resources=replace(selected.resources, budgets=tuple((name,
            replace(budget, output_bytes=1) if name == 'entry' else budget) for name, budget in selected.resources.budgets)))
    kwargs = dict(kwargs, request=selected, specification=replace(kwargs['specification'], request=selected.identity))
    original_write, observed = kwargs['artifact_writer'].write, []

    def observe(request):
        observed.append(request.logical_artifact_id)
        return original_write(request)

    monkeypatch.setattr(kwargs['artifact_writer'], 'write', observe)
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        owner.assemble_programme_e2(**kwargs)
    assert observed == []
