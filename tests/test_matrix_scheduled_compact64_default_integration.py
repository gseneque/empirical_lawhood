# SPDX-License-Identifier: MPL-2.0
"""Public conformance for 707 tasks over exposed software declarations.

The installed catalog, compiler, guarded publications, author/load and provider
proof are real. Source qualifications and the clean-source inspector remain
explicit hypothetical fixtures. No issue, scientific execution or qualification
is obtained from the operational envelope or these tests.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_scheduled_history.compact_records import NAMESPACE, ScheduledCompactCommitmentConfig
from empirical_lawhood.api import recursive_prospective_authoring as author
from empirical_lawhood.api.recursive_operations import operation_factories
from empirical_lawhood.storage.artifacts import ArtifactPlaneError
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.execution.recursive_prospective import RecursiveProspectiveAuthoringSpec
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from tests.test_matrix_scheduled_calibration import (
    TEST_BUDGET, bank as bank, provenance as provenance, response_bank as response_bank,
    scheduled as scheduled, stock as stock,
)
from tests.test_matrix_scheduled_compact_graph import calibration64_bank
from tests.test_matrix_scheduled_default_integration import _application, _load


@pytest.fixture
def application64(response_bank, tmp_path, monkeypatch):
    from empirical_lawhood.domains.matrix.matrix_factor_response import response_error_prediction
    from empirical_lawhood.domains.matrix.matrix_scheduled_history import response_forecast, response_science
    from empirical_lawhood.domains.matrix.six_matrix_response import parameter_history_segments, parameter_source

    def blocked(*args, **kwargs):
        pytest.fail('public authoring, loading or provider proof for 707 tasks entered numerical science')

    # The source/template fixtures above are already explicitly exposed. Their
    # prepared immutable records are then passed through the actual public API.
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(response_science, 'native_responses', blocked)
    monkeypatch.setattr(response_forecast, 'forecast', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_error_model', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_scheduled_error_model', blocked)
    bundle = calibration64_bank(response_bank)
    return _application(response_bank, tmp_path, monkeypatch, compact=True, draft_bundle=bundle)


def test_public_calibration64_author_load_proof_preserves_complete_semantics(application64, monkeypatch):

    args, compilation, plane = application64
    spec = args['spec']
    original_bytes = spec.canonical_bytes()
    assert type(spec) is RecursiveProspectiveAuthoringSpec
    assert len(compilation.selected_scientific_projection.canonical_bytes()) <= 16*1024**2
    factories = tuple(factory for factory in operation_factories() if factory.manifest.capability_key.startswith(NAMESPACE+'.'))
    assert len(factories) == 19
    bank, = (value.record.bank for value in compilation.config_inputs if type(value.record) is ScheduledCompactCommitmentConfig)
    assert len(bank.selected_root_ids) == 64 and len(bank.sources) == 70
    assert len(bank.forecast_design.training_record.population.selections) == 256
    assert len(bank.forecast_design.model_record.training_root_ids) == 128
    assert len(spec.draft.prospective_draft.evaluation_unit_ids) == 64
    assert len(spec.resources.task_cells) == 707
    assert sum(cell.native_simulator_launch for cell in spec.resources.task_cells) == 192

    destination = Path(plane.root.contract.canonical_path)/'default-compact64-authoring'
    result = author.author_recursive_prospective(**args, output_dir=destination)
    assert result['task_count'] == 707 and result['native_contact'] == 'none'
    assert result['scientific_authority'] == 'NONE' and result['qualification'] == 'NOT_ESTABLISHED'
    packet = decode_canonical_bytes((destination/'authored-wave.json').read_bytes(), AuthoredRecursiveWave, maximum_bytes=1024**2)
    member, = (value for value in packet.members if value.filename == 'recursive-prospective.json')
    raw = (destination/member.filename).read_bytes()
    assert member.identity.object_schema == RecursiveProspectiveAuthoringSpec.SCHEMA
    assert member.identity.object_version == RecursiveProspectiveAuthoringSpec.VERSION
    assert member.size_bytes == len(raw)
    assert member.identity.object_fingerprint == sha256(raw).hexdigest()
    assert raw == original_bytes
    decoded = author.load_recursive_prospective_spec(destination/member.filename)
    assert type(decoded) is RecursiveProspectiveAuthoringSpec
    assert decoded.canonical_bytes() == original_bytes and decoded.fingerprint() == spec.fingerprint()
    decoder = decode_canonical_bytes((destination/'decoder.json').read_bytes(), StudyExtensionDecoderRegistration, maximum_bytes=16*1024**2)
    assert decoder.maximum_payload_bytes is None

    handoff = _load(application64, destination, monkeypatch)
    assert handoff.compilation.draft.canonical_bytes() == spec.draft.canonical_bytes()
    assert len(handoff.compilation.config_inputs) == len(handoff.projection.tasks) == 707
    assert {task.capability.requested_resources for task in handoff.projection.tasks} == {TEST_BUDGET}
    proof = author.prove_recursive_prospective_handoff(handoff)
    assert proof['task_count'] == 707 and proof['scientific_execution_performed'] is False
    assert len(handoff.compilation.candidate_context.qualifications) == len(spec.qualifications)

    # The complete specification and public decoder have already passed. Corrupting an
    # actual original shared publication must still refuse before another proof.
    publication = bank.reservation.publication
    path = plane.root.resolve(publication.materialization.relative_path, for_write=True)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ArtifactPlaneError):
        _load(application64, destination, monkeypatch)


def test_exact_spec_and_authenticated_member_sizes_have_no_tier(application64, tmp_path):
    from empirical_lawhood.design.recursive_authoring import RecursiveScientificSelection

    spec = application64[0]['spec']
    path = tmp_path / 'complete-spec.json'
    path.write_bytes(spec.canonical_bytes())
    assert author.load_recursive_prospective_spec(path) == spec
    root = spec.draft.prospective_draft
    world = replace(root.system.world, label='software-observed-size-'+('x'*(32*1024**2 - len(spec.canonical_bytes()) + 1024)))
    larger = replace(spec, draft=replace(spec.draft, prospective_draft=replace(root, system=replace(root.system, world=world))))
    assert len(larger.canonical_bytes()) > 32*1024**2
    path.write_bytes(larger.canonical_bytes())
    assert author.load_recursive_prospective_spec(path) == larger
    scientific = application64[1].selected_scientific_projection
    member = RecursiveWaveMember('scientific-projection.json', ObjectIdentity.from_record(scientific.selection_id, scientific),
        len(scientific.canonical_bytes()))
    assert author._prospective_member_codec(member) == (RecursiveScientificSelection, member.size_bytes)
    assert author._prospective_member_codec(replace(member, size_bytes=256*1024**2+1)) == (RecursiveScientificSelection, 256*1024**2+1)
    with pytest.raises(ValueError, match='schema/version'):
        author._prospective_member_codec(replace(member, identity=replace(member.identity, object_version='9.0.0')))
