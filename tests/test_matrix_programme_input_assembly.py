# SPDX-License-Identifier: MPL-2.0
"""Public copied-FILE C compilation controls; no native scientific execution."""
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_researcher_programme import input_assembly as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.allocation_request import MatrixProgrammeAllocationRequest
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import PHASE_INPUT_ROLES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE
from empirical_lawhood.api import matrix_programme_input_assembly as owner
from empirical_lawhood.api import matrix_programme_allocations as compiler
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_programme_allocations import MATERIALS, NAMESPACE, census as census  # noqa: F401
from tests.test_matrix_programme_scientific_design import matched_scientific_design  # noqa: F401

ROOT = Path(__file__).parents[1]
REQUIREMENTS_SCHEMA = 'empirical-lawhood/operational/experiment-input-requirements'


def _write_copied(case, *, design=None, census=None, budget=None):
    """Select exact current bytes; no support publication is an input."""
    if design is not None:
        case.design = design
    if census is not None:
        case.census = census
    request = replace(case.request, scientific_design=case.design.identity, exposure_census=case.census.identity,
        metadata_budget=case.request.metadata_budget if budget is None else budget)
    case.request = request
    case.specification = domain.MatrixProgrammeInputAssemblySpecification('assembly.disclosed.public-c', request.identity)
    records = {'request': request, 'scientific-design': case.design, 'exposure-census': case.census}
    bindings = []
    for key, record in sorted(records.items()):
        raw = record.canonical_bytes()
        relative = key + '.json'
        (case.copied / relative).write_bytes(raw)
        bindings.append(ExperimentInputBinding(key, record.identity, relative, len(raw)))
    case.specification_path.write_bytes(case.specification.canonical_bytes())
    case.selector = ExperimentFileInputSelection('sources.disclosed.public-c', domain.PROTOCOL_ID,
        tuple(bindings), request.files)
    case.selector_path.write_bytes(case.selector.canonical_bytes())


def build_public_file_case(tmp_path, census, *, design=None):
    """The existing exposed D/E1 math with actual copied arrays and source FILE.

    No _publisher_case, former TRAIN request, or pre-existing publication handle
    is used. The public deriver must create every actual support publication.
    """
    import numpy as np
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    from tests.runtime_platform.test_native_subwork import _plane
    from tests.test_matrix_programme_e1_allocation import public_e1_case, derive as derive_e1
    from tests.test_matrix_programme_scientific_design import build_scientific_design

    design = build_scientific_design() if design is None else design
    writer = _plane(tmp_path / 'custody', binary_codecs=operation_storage_codecs())
    prospective = public_e1_case(tmp_path, census, design=design, writer=writer)
    e1_result = derive_e1(prospective)
    e1_inputs = load_experiment_inputs(prospective.specification, e1_result.source_selection_path).method_inputs
    e1 = e1_inputs.allocation
    design = replace(design, e1_criterion=e1_inputs.criterion)
    copied = Path(writer.root.contract.canonical_path) / 'copied-public-c'
    (copied / 'support').mkdir(parents=True)
    raw, _ = encode_matrix_arrays({'generic_basis': np.zeros((3, 4, 4), dtype='<c16'),
        'force_coefficients': np.zeros((2, 3, 3), dtype='<f8'), 'trace_coefficients': np.zeros((2, 3), dtype='<f8'),
        'receiver_coefficients': np.zeros((48, 2, 2, 3, 4), dtype='<f8')})
    source = ROOT / 'src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py'
    normalization = design.training_protocol.full_factor_rule.scalar_closure.normalization_owner
    payloads = {artifact: raw for artifact in (design.training_assay.array_artifact, design.e2.assay.array_artifact)}
    payloads[normalization] = source.read_bytes()
    bindings, support_sources = [], []
    for artifact, payload in sorted(payloads.items(), key=lambda row: row[0].artifact_id):
        assert (len(payload), sha256(payload).hexdigest()) == (artifact.size_bytes, artifact.sha256)
        relative = 'support/' + artifact.sha256 + ('.py' if artifact == normalization else '.npz')
        (copied / relative).write_bytes(payload)
        bindings.append(ExperimentFileInputBinding(artifact.artifact_id, artifact, '1.0.0', relative, artifact.size_bytes))
        support_sources.append((artifact, source if artifact == normalization else None, relative, payload))
    matched = design.e3.measurement.is_matched
    budget = ResourceBudget(1, compiler._process_rss_bytes() + (4 if matched else 1) * 1024**3,
        0, 60, 256 * 1024**2, (4 * 1024**3 if matched else 512 * 1024**2))
    request = MatrixProgrammeAllocationRequest('request.disclosed.public-c', NAMESPACE, design.identity, census.identity,
        MATERIALS[0], MATERIALS[1], SelectedE4StreamRecipe('streams.disclosed.programme.e4', MATERIALS[2], MATERIALS[3], STREAM_RULE,
            sha256(b'disclosed.amended.family-allocation').hexdigest() if matched else None),
        MATERIALS[4], MATERIALS[5], tuple(bindings), budget)
    implementation = implementation_binding(ROOT)
    execution = ExecutionSelection(4, 'environment.disclosed.public-c',
        ObjectIdentity.from_record('recursive-member.implementation', implementation), writer.root.contract.canonical_path)
    directory = Path(writer.root.contract.canonical_path) / 'public-programme-inputs'
    case = SimpleNamespace(design=design, census=census, e1=e1, writer=writer, copied=copied, request=request,
        e1_metadata_directory=prospective.directory,
        support_sources=tuple(support_sources), specification_path=copied / 'specification.json',
        selector_path=copied / 'sources.json', directory=directory, execution=execution,
        output_selection_path=directory / 'inputs/sources.json')
    _write_copied(case)
    return case


@pytest.fixture
def public_file_case(tmp_path, census):  # noqa: F811
    return build_public_file_case(tmp_path, census)


def _derive(case):
    return derive_experiment_inputs(specification_path=case.specification_path, source_selection_path=case.selector_path,
        project_root=ROOT, artifact_writer=case.writer, metadata_directory=case.directory,
        output_selection_path=case.output_selection_path, execution=case.execution)


def _inventory(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob('*') if path.is_file()}


def _forbid_acquisition(monkeypatch):
    from tests.test_matrix_programme_allocations import _forbid_acquisition as forbid
    forbid(monkeypatch)


def _assert_no_custody_before_or_after_refusal(case, action, *, match):
    root = Path(case.writer.root.contract.canonical_path)
    before = _inventory(root)
    with pytest.raises((ValueError, PermissionError, RuntimeError), match=match):
        action()
    assert _inventory(root) == before
    assert not case.directory.exists()


def _assert_public_compiler_roundtrip(case, monkeypatch):
    from empirical_lawhood.api.configuration import validate_configuration
    _forbid_acquisition(monkeypatch)
    assert validate_configuration(case.specification_path, consumer='matrix-programme-input-assembly')['status'] == 'VALIDATED'
    inputs = load_experiment_inputs(case.specification, case.selector_path).method_inputs
    assert inputs.input_commitments is None
    assert tuple(key for key, _ in inputs.record_paths) == ('exposure-census', 'request', 'scientific-design')
    assert {file.identity for _, file in inputs.files} == domain.required_support_files(case.design)
    assert len(inputs.files) == len({row[0] for row in case.support_sources})
    existing = tuple(Path(case.writer.root.contract.canonical_path).rglob('*.manifest.json'))
    assert existing and all(path.is_relative_to(case.e1_metadata_directory) for path in existing)
    assert not case.directory.exists()
    from empirical_lawhood.api import selected_e4_bank_recipe as source_selection
    from empirical_lawhood.infrastructure import numerical_provenance, source_closure

    # Observe the real public C path, preserving every actual admission and byte guard.
    captured, archives, current_checks, observed_publications, runtimes, events = [], [], [], [], [], []
    actual_capture = source_closure.capture_admitted_target_source
    actual_current = source_closure.require_admitted_target_source_current
    actual_git = source_closure._git
    actual_runtime = numerical_provenance.numerical_runtime_observation
    actual_write, actual_batch = case.writer.write, case.writer.write_batch

    def capture(*args, **kwargs):
        source = actual_capture(*args, **kwargs)
        captured.append(source)
        events.append('capture')
        return source

    def git(selected_root, *arguments):
        if arguments[0] == 'archive':
            archives.append(arguments)
        return actual_git(selected_root, *arguments)

    def current(selected_root, source):
        assert captured and source is captured[-1]
        actual_current(selected_root, source)
        current_checks.append(source)
        events.append('current')

    def runtime():
        value = actual_runtime()
        runtimes.append(value)
        return value

    def publish(actual, *args, **kwargs):
        assert current_checks and current_checks[-1] is captured[-1]
        observed_publications.append(len(captured))
        events.append('publication')
        return actual(*args, **kwargs)

    def raw_inventory_forbidden(*_args, **_kwargs):
        pytest.fail('public C reconstructed the already admitted package/lock inventory')

    monkeypatch.setattr(source_closure, 'capture_admitted_target_source', capture)
    monkeypatch.setattr(source_selection, 'capture_admitted_target_source', capture)
    monkeypatch.setattr(source_closure, '_git', git)
    for consumer in (source_selection, compiler, owner):
        monkeypatch.setattr(consumer, 'require_admitted_target_source_current', current)
    monkeypatch.setattr(numerical_provenance, 'numerical_runtime_observation', runtime)
    monkeypatch.setattr(numerical_provenance, 'numerical_package_sources', raw_inventory_forbidden)
    monkeypatch.setattr(numerical_provenance, 'selected_dependency_lock_sha256', raw_inventory_forbidden)
    monkeypatch.setattr(case.writer, 'write', lambda *args, **kwargs: publish(actual_write, *args, **kwargs))
    monkeypatch.setattr(case.writer, 'write_batch', lambda *args, **kwargs: publish(actual_batch, *args, **kwargs))
    result = _derive(case)
    assert len(captured) == len(archives) == 1
    assert len(current_checks) == 4 and len(runtimes) == 5
    assert observed_publications and set(observed_publications) == {1} and events[-1] == 'current'
    assert result.target_specification is None and result.specification == case.specification.identity
    assert result.preparation.census.native_effect_count == 0 and result.preparation.draft is None
    assert {row.code for row in result.preparation.dependencies} == {'programme-inputs.use-commitment'}
    rebound = load_experiment_inputs(case.specification, result.source_selection_path).method_inputs
    assert rebound.request is None and rebound.design is None and rebound.census is None and rebound.files == ()
    commitment = rebound.input_commitments
    resolved = authenticate_programme_inputs(writer=case.writer, commitment=commitment,
        maximum_source_bytes=case.request.metadata_budget.source_scan_bytes)
    assert resolved.scientific_design == case.design and resolved.exposure_census == case.census
    assert resolved.commitments.e4_streams == case.request.e4_streams
    assert resolved.commitments.VERSION == '2.0.0'
    assert tuple(phase.role for phase in resolved.phases) == PHASE_INPUT_ROLES
    assert resolved.phase('e1').reservation.allocation == case.e1
    counts = dict(case.design.phase_group_counts)
    for role in PHASE_INPUT_ROLES:
        phase = resolved.phase(role)
        if role == 'e1':
            groups = {row.root.independent_group_id for row in phase.reservation.allocation.roots}
        else:
            groups = {protocol.public_source.root.independent_group_id for protocol in phase.responses.protocols}
            assert len(phase.responses.protocols) == counts[role] * (9 if role.startswith('e4.') else 1)
            assert all({panel.role for panel in panels} == {'COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE'}
                for _, panels in phase.responses.panels)
        assert len(groups) == counts[role]
    for role in ('e4.development', 'e4.calibration', 'e4.confirmation'):
        assert set(Counter(protocol.public_source.root.independent_group_id
            for protocol in resolved.phase(role).responses.protocols).values()) == {9}
    assert set(dict(resolved.commitments.revision_folds)) == {
        protocol.public_source.root.independent_group_id for protocol in resolved.phase('e4.development').responses.protocols}
    for artifact, source, relative, payload in case.support_sources:
        assert (case.copied / relative).read_bytes() == payload
        if source is not None:
            assert source.read_bytes() == payload
            actual_artifact, publication = next(row for row in resolved.commitments.support_files if row[0] == artifact)
            assert actual_artifact == artifact
        else:
            publications = {value for phase in resolved.phases if phase.responses is not None
                for value in phase.responses.template_publications if value.logical.logical_artifact_id == artifact.artifact_id}
            assert len(publications) == 1
            publication, = publications
        assert case.writer.root.resolve(publication.materialization.relative_path, for_write=False).read_bytes() == payload
    assert resolved.e6_policy.future_reservation == scheduled.identity(resolved.phase('e3.calibration').reservation)
    assert resolved.e6_policy.criterion == case.design.e6_policy.criterion
    requirements = json.loads(case.writer.root.resolve(
        result.requirements_publication.materialization.relative_path, for_write=False).read_bytes())
    assert requirements['schema'] == REQUIREMENTS_SCHEMA
    assert requirements['value']['scientific_design'] == case.design.identity.to_document()
    assert requirements['value']['phase_group_counts'] == [list(row) for row in case.design.phase_group_counts]
    assert requirements['value']['native_contact'] == requirements['value']['scientific_authority'] == 'NONE'
    assert requirements['value']['qualification'] == 'NOT_ESTABLISHED'
    assert not tuple(Path(case.writer.root.contract.canonical_path).rglob('native-subwork'))
    before = _inventory(Path(case.writer.root.contract.canonical_path))
    monkeypatch.setattr('empirical_lawhood.planning.approval.SystemDecisionClock.now_utc',
        lambda _: pytest.fail('exact retry reconstructed original availability'))
    replay = _derive(case)
    assert len(captured) == len(archives) == 2
    assert captured[1] is not captured[0]
    assert len(current_checks) == 8 and len(runtimes) == 10
    assert set(observed_publications) == {1, 2} and events[-1] == 'current'
    assert replay == result
    assert _inventory(Path(case.writer.root.contract.canonical_path)) == before
    return resolved


def test_public_files_compile_all_twelve_roles_and_reopen_exact_originals(public_file_case, monkeypatch):
    _assert_public_compiler_roundtrip(public_file_case, monkeypatch)


def test_public_amended_design_compiles_980_groups_and_reopens_exact_current_commitments(
        matched_scientific_design, census, tmp_path, monkeypatch):  # noqa: F811
    case = build_public_file_case(tmp_path, census, design=matched_scientific_design)
    resolved = _assert_public_compiler_roundtrip(case, monkeypatch)
    assert sum(dict(resolved.scientific_design.phase_group_counts).values()) == 980
    for role in PHASE_INPUT_ROLES:
        phase = resolved.phase(role)
        if phase.responses is not None:
            assert all(protocol.horizon_steps == tuple(range(16, 129, 4)) for protocol in phase.responses.protocols)
    assert resolved.e6_policy.endpoint_order == tuple(('FACTOR', tick) for tick in range(16, 129, 4))
    assert resolved.e6_policy.comparator_methods == ('B0', 'BR', 'S0', 'SR')


@pytest.mark.parametrize('damage', ('wrong-e1', 'exposed-e2-group', 'file-bytes', 'output-budget'))
def test_public_compiler_refuses_wrong_originals_before_any_publication(public_file_case, monkeypatch, damage):
    case = public_file_case
    _forbid_acquisition(monkeypatch)
    if damage == 'wrong-e1':
        _write_copied(case, design=replace(case.design, e1_criterion=replace(case.design.e1_criterion,
            allocation=replace(case.design.e1_criterion.allocation, object_fingerprint='a' * 64))))
        match = 'E1 frozen criterion changes requested roots'
    elif damage == 'exposed-e2-group':
        exposed = replace(case.census, exposed_independent_groups=tuple(sorted({*case.census.exposed_independent_groups,
            'group.' + NAMESPACE + '.e2.000'})))
        e1 = replace(case.e1, exposure=exposed)
        _write_copied(case, census=exposed, design=replace(case.design,
            e1_criterion=replace(case.design.e1_criterion, allocation=scheduled.identity(e1))))
        match = 'exposed|group'
    elif damage == 'file-bytes':
        artifact, _, relative, raw = next(row for row in case.support_sources if row[0] == case.design.e2.assay.array_artifact)
        assert artifact.size_bytes == len(raw)
        (case.copied / relative).write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
        match = 'exact bytes|size|selected'
    else:
        _write_copied(case, budget=replace(case.request.metadata_budget, output_bytes=1))
        match = 'output-byte lower bound|output.*budget'
    _assert_no_custody_before_or_after_refusal(case, lambda: _derive(case), match=match)


@pytest.mark.parametrize('field', ('source_scan_bytes', 'memory_bytes'))
def test_public_budget_refuses_before_materializing_support_files(public_file_case, monkeypatch, field):
    case = public_file_case
    _forbid_acquisition(monkeypatch)
    _write_copied(case, budget=replace(case.request.metadata_budget, **{field: 1}))
    reads = []
    original = owner.read_bounded_bytes

    def observed(path, **kwargs):
        reads.append(path)
        return original(path, **kwargs)

    monkeypatch.setattr(owner, 'read_bounded_bytes', observed)
    _assert_no_custody_before_or_after_refusal(case, lambda: _derive(case), match='source or memory budget')
    # The generic copied-input loader has independently hashed actual FILEs.
    # This assertion concerns the compiler API's owned body materialization.
    assert reads == []


@pytest.mark.parametrize('assay_owner', ('TRAIN', 'E2'))
def test_same_array_alias_checks_each_independent_assay_member_digest(public_file_case, monkeypatch, assay_owner):
    case = public_file_case
    _forbid_acquisition(monkeypatch)
    assert case.design.training_assay.array_artifact == case.design.e2.assay.array_artifact
    assay = case.design.training_assay if assay_owner == 'TRAIN' else case.design.e2.assay
    changed = replace(assay, members=tuple(replace(row, sha256='0' * 64)
        if row.name == 'force_coefficients' else row for row in assay.members))
    if assay_owner == 'TRAIN':
        design = replace(case.design, training_assay=changed,
            prepared_assay=MatrixPreparedAssayMethod.from_assay(case.design.prepared_assay.record_id, changed))
    else:
        design = replace(case.design, e2=replace(case.design.e2, assay=changed))
    assert design.training_assay.array_artifact == design.e2.assay.array_artifact
    assert design.training_assay.members != design.e2.assay.members
    _write_copied(case, design=design)
    _assert_no_custody_before_or_after_refusal(case, lambda: _derive(case), match='Matrix array values')


@pytest.mark.parametrize('target', ('copied-design', 'published-census'))
def test_mutation_during_final_requirements_publication_refuses_return(public_file_case, monkeypatch, target):
    case = public_file_case
    _forbid_acquisition(monkeypatch)
    original = type(case.writer).write_batch
    observed = []

    def mutate(writer, requests, **kwargs):
        results = original(writer, requests, **kwargs)
        if any(request.payload_schema == REQUIREMENTS_SCHEMA for request in requests):
            path = (case.copied / 'scientific-design.json' if target == 'copied-design' else
                case.directory / 'commitments/publications/census.json')
            raw = path.read_bytes()
            path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
            observed.append(path)
        return results

    monkeypatch.setattr(type(case.writer), 'write_batch', mutate)
    with pytest.raises((ValueError, PermissionError, RuntimeError)):
        _derive(case)
    assert len(observed) == 1


def test_source_change_after_final_publication_refuses_successful_derivation(public_file_case, monkeypatch):
    case = public_file_case
    _forbid_acquisition(monkeypatch)
    original_write, original_capture = type(case.writer).write_batch, owner.capture_matrix_provenance
    observed = {'published': False, 'late_source_checks': 0}

    def publish(writer, requests, **kwargs):
        results = original_write(writer, requests, **kwargs)
        if any(request.payload_schema == REQUIREMENTS_SCHEMA for request in requests):
            observed['published'] = True
        return results

    def capture(**kwargs):
        actual = original_capture(**kwargs)
        if observed['published']:
            observed['late_source_checks'] += 1
            changed_sources = tuple((name, 'a' * 64 if index == 0 else digest)
                for index, (name, digest) in enumerate(actual.package_sources))
            return replace(actual, package_sources=changed_sources,
                code_sources_sha256=sha256(canonical_json_bytes(changed_sources)).hexdigest())
        return actual

    monkeypatch.setattr(type(case.writer), 'write_batch', publish)
    monkeypatch.setattr(owner, 'capture_matrix_provenance', capture)
    with pytest.raises(ValueError, match='source changed during dependent metadata publication'):
        _derive(case)
    assert observed['published'] and observed['late_source_checks'] == 1
