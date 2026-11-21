"""Typed plan envelopes preserve compact-control limits and custody refusal."""

from pathlib import Path
import os
from types import MethodType, SimpleNamespace

import pytest

from empirical_lawhood.api import authoring_handoff, codecs
from empirical_lawhood.api.execution import _CatalogSemanticReplayBudget, CampaignCapabilityError, CampaignExecutionService, CampaignIdentityError
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.bounded_io import BoundedFileIOError

from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.storage.contracts.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
from empirical_lawhood.execution.operator_profile import OperatorStorageProfile
from empirical_lawhood.execution.plans import CandidateExecutionPlan


FIXTURE = Path(__file__).parent / 'fixtures/authoring-execution-plan.json'


def test_topological_generations_visit_each_dependency_list_once():
    from empirical_lawhood.execution.plans import _topological_order

    visits = []
    class Dependencies(dict):
        def __getitem__(self, key):
            visits.append(key)
            return super().__getitem__(key)
    identifiers = tuple(f'task.{index:04d}' for index in range(512))
    dependencies = Dependencies({task: (() if index == 0 else (identifiers[index - 1],))
        for index, task in enumerate(identifiers)})
    assert _topological_order(identifiers, dependencies) == identifiers
    assert sorted(visits) == list(identifiers)
    # Whole sorted generations differ from a single global ready heap.
    assert _topological_order(('a', 'b', 'z'), {'a': (), 'b': ('a',), 'z': ()}) == ('a', 'z', 'b')
    with pytest.raises(ValueError, match='cycle'):
        _topological_order(('a', 'b'), {'a': ('b',), 'b': ('a',)})


def _sparse(path, size):
    with path.open('xb') as handle:
        handle.truncate(size)










def _stored_plan(tmp_path):
    mount = next(parent for parent in (tmp_path, *tmp_path.parents) if os.path.ismount(parent))
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'synthetic.plan-bound-store', 'software-only bounded plan custody', str(tmp_path),
        str(mount), OperatorStorageProfile.SCHEMA, 1, None, None, (),
    )))
    (tmp_path / 'preissue-execution-plan.json').write_bytes(FIXTURE.read_bytes())
    plan = authoring_handoff.load_authoring_execution_projection(tmp_path)
    run_id = plan.source_plan.object_id
    retained = plane.write(ArtifactWriteRequest(
        logical_artifact_id=f'execution-plan.{run_id}',
        relative_path=f'runs/{run_id}/plans/execution-plan.json',
        payload_schema=plan.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON,
        media_type='application/json', publication_scope_id='synthetic.plan-controls',
        publication_scope_relative_root=f'runs/{run_id}/plans',
        payload=plan.canonical_bytes(), visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        parent_visibility_ceilings=(), outcome_access=OutcomeAccess.OUTCOME_BLIND,
        minimum_free_bytes=1,
    ))
    service = SimpleNamespace(artifact_plane=plane)
    for name in ('_verified_rebuild_control_payload', '_rebuild_control_pair_present'):
        setattr(service, name, MethodType(getattr(CampaignExecutionService, name), service))
    return plane, service, plan, retained


def test_status_reads_canonical_stored_plan_and_refuses_tampered_bytes(tmp_path):
    plane, service, plan, retained = _stored_plan(tmp_path)
    assert CampaignExecutionService._load_status_execution_plan(service, plan.source_plan.object_id) == plan
    path = plane.root.resolve(retained.materialization.relative_path, for_write=False)
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(CampaignIdentityError, match='custody is invalid'):
        CampaignExecutionService._load_status_execution_plan(service, plan.source_plan.object_id)


@pytest.mark.parametrize('missing_bytes', (0, 1))
def test_replay_aggregate_charges_both_manifest_and_plan_before_open(tmp_path, monkeypatch, missing_bytes):
    plane, service, plan, retained = _stored_plan(tmp_path)
    manifest_path = plane.root.resolve(retained.materialization.relative_path + '.manifest.json', for_write=False)
    aggregate = len(manifest_path.read_bytes()) + retained.materialization.size_bytes
    budget = _CatalogSemanticReplayBudget(remaining_bytes=aggregate - missing_bytes)
    original_open = plane.open
    opens = []

    def observed(*args, **kwargs):
        opens.append(kwargs['maximum_bytes'])
        return original_open(*args, **kwargs)

    monkeypatch.setattr(plane, 'open', observed)
    arguments = dict(logical_artifact_id=retained.logical.logical_artifact_id,
        relative_path=retained.materialization.relative_path,
        payload_schemas=(plan.SCHEMA,), maximum_bytes=None,
        budget=budget)
    if missing_bytes:
        with pytest.raises(CampaignCapabilityError, match='aggregate byte limit'):
            service._verified_rebuild_control_payload(**arguments)
        assert opens == []
    else:
        payload, fingerprint, schema = service._verified_rebuild_control_payload(**arguments)
        assert payload == plan.canonical_bytes() and fingerprint == plan.fingerprint() and schema == plan.SCHEMA
        assert opens == [retained.materialization.size_bytes] and budget.remaining_bytes == 0




def test_closed_plan_loads_observed_extent_and_respects_explicit_allowance(tmp_path):
    raw = FIXTURE.read_bytes()
    path = tmp_path / 'plan.json'
    path.write_bytes(raw + b' ' * 17)
    registry = {CandidateExecutionPlan.SCHEMA: CandidateExecutionPlan}
    assert codecs.load_registered_authoring(path, root_schemas=registry) == codecs.load_registered_authoring(FIXTURE, root_schemas=registry)
    with pytest.raises(codecs.AuthoringCodecError, match='byte limit'):
        codecs.load_registered_authoring(path, root_schemas=registry, maximum_bytes=len(raw))


def test_selected_custody_allowance_refuses_plan_before_decode(tmp_path, monkeypatch):
    _sparse(tmp_path / 'preissue-execution-plan.json', 257)
    monkeypatch.setattr(authoring_handoff, 'decode_canonical_bytes', lambda *a, **kw: pytest.fail('selected byte allowance must refuse before decode'))
    writer = SimpleNamespace(custody_limits=ArtifactCustodyLimits(control_record_bytes=256))
    with pytest.raises(BoundedFileIOError, match='byte limit'):
        authoring_handoff.load_authoring_execution_projection(tmp_path, artifact_writer=writer)
