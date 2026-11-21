# SPDX-License-Identifier: MPL-2.0
"""Original custody and unchanged physical operands across engine-only reuse."""

from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import active_model_rebinding as owner
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
from empirical_lawhood.api.domain_composition.rubisco_response import active_model_rebinding as public
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_rubisco_accelerated_compute import gpu_engine
from tests import test_rubisco_active_relaxation_operation as controls

fixture = controls.fixture
matched = controls.matched


def updated(fixture, **changes):
    original = fixture.prototype
    values = dict(representation=fixture.model, path=original.path, cell=original.cell,
        electronic=original.electronic, molecular=original.molecular,
        engine=gpu_engine(original.engine, molecular_platform='Reference'))
    return prepare_periodic_probe_selection(**(values | changes))


def original_publication(fixture):
    writer = _plane(fixture.tmp_path/'original-preparations')
    prepared = fixture.prepared
    writer.write(ArtifactWriteRequest(prepared.identity.object_id, 'original/preparation.json',
        prepared.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'original.preparation',
        'original', prepared.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    return writer


def test_complete_preparation_is_reused_without_a_seed_constructor(fixture, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import active_state_geometry
    monkeypatch.setattr(active_state_geometry, 'materialize_catalytic_states',
        lambda **kwargs: pytest.fail('engine-only rebinding reconstructed physical states'))
    target = updated(fixture)
    rebound, binding = owner.rebind_prepared_engine(prepared=fixture.prepared,
        original_prototype=fixture.prototype, updated_prototype=target, representation=fixture.model)
    assert rebound.sites == fixture.prepared.sites
    assert rebound.seeds == fixture.prepared.seeds
    assert rebound.assessments == fixture.prepared.assessments
    assert rebound.identity != fixture.prepared.identity
    assert rebound.prototype == target.identity
    assessment = owner.assess_engine_rebinding(binding=binding, original=fixture.prepared,
        rebound=rebound, original_prototype=fixture.prototype, updated_prototype=target, representation=fixture.model)
    assert assessment['sites'] == 8 and assessment['starting_hypotheses'] == 96
    assert assessment['preserved_assessments'] == 96 and assessment['new_native_calls'] == 0
    assert assessment['new_geometry_constructions'] == 0
    assert decode_canonical_bytes(binding.canonical_bytes(), type(binding), maximum_bytes=2**20) == binding


@pytest.mark.parametrize('operand', ('electronic', 'molecular', 'cell', 'unchanged-engine'))
def test_rebinding_refuses_any_changed_physical_selection(fixture, operand):
    original = fixture.prototype
    if operand == 'unchanged-engine':
        target = original
    elif operand == 'molecular':
        target = updated(fixture, molecular=replace(original.molecular,
            settings_id=original.molecular.settings_id+'.changed',
            cutoff_angstrom=original.molecular.cutoff_angstrom-Decimal('.1')))
    elif operand == 'cell':
        lengths = original.cell.lengths_angstrom
        target = updated(fixture, cell=replace(original.cell,
            lengths_angstrom=(lengths[0]+Decimal('.1'), *lengths[1:])))
    else:
        target = updated(fixture, electronic=replace(original.electronic,
            settings_id=original.electronic.settings_id+'.changed',
            real_cutoff_angstrom=original.electronic.real_cutoff_angstrom-Decimal('.1')))
    with pytest.raises(ValueError, match='physical|different selected'):
        owner.rebind_prepared_engine(prepared=fixture.prepared, original_prototype=original,
            updated_prototype=target, representation=fixture.model)


def test_public_rebinding_reconstructs_and_rechecks_its_original(fixture):
    original = original_publication(fixture)
    output = _plane(fixture.tmp_path/'engine-successor')
    target = updated(fixture)
    arguments = dict(original_relative_path='original/preparation.json', original_writer=original,
        original_prototype=fixture.prototype, updated_prototype=target, representation=fixture.model,
        artifact_writer=output)
    returned = public.rebind_active_model_engine(**arguments, output_relative_path='new/preparation.json')
    read = public.read_active_model_engine_rebinding(**arguments,
        preparation_relative_path=returned['preparation_relative_path'], binding_relative_path=returned['binding_relative_path'])
    assert read['preparation'] == returned['preparation'] and read['assessment'] == returned['assessment']
    path = original.root.resolve('original/preparation.json', for_write=False)
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_active_model_engine_rebinding(**arguments,
            preparation_relative_path=returned['preparation_relative_path'], binding_relative_path=returned['binding_relative_path'])


def test_original_guard_remains_live_through_successor_publication(fixture, monkeypatch):
    original = original_publication(fixture)
    output = _plane(fixture.tmp_path/'live-engine-successor')
    path = original.root.resolve('original/preparation.json', for_write=False)
    publish = public._publish
    def mutate(writer, record, relative_path):
        publish(writer, record, relative_path)
        if relative_path.endswith('.engine-binding.json'):
            path.write_bytes(path.read_bytes()+b' ')
    monkeypatch.setattr(public, '_publish', mutate)
    with pytest.raises(ArtifactIdentityConflict):
        public.rebind_active_model_engine(original_relative_path='original/preparation.json', original_writer=original,
            original_prototype=fixture.prototype, updated_prototype=updated(fixture), representation=fixture.model,
            output_relative_path='new/preparation.json', artifact_writer=output)
