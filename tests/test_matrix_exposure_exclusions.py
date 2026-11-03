# SPDX-License-Identifier: MPL-2.0
"""Independent current exclusion metadata controls; no API, RNG or acquisition."""
import ast
from dataclasses import fields, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import exposure as owner
from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import BetaCouplingRule
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity

ROOT = Path(__file__).resolve().parents[1]


def literal_assignment(path, name):
    tree = ast.parse(path.read_text())
    return ast.literal_eval(next(row.value for row in tree.body if isinstance(row, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in row.targets)))


def census():
    # Literal exposed software input, not a factual union or real qualification.
    provenance = ArtifactIdentity('facts.disclosed-software', 'external-factual-provenance',
        'empirical-lawhood/testing/disclosed-exposure-facts', 'a' * 64, 'application/json', 12)
    return owner.MatrixFactorExposureCensus('census.disclosed-software', owner.MANDATORY_FLOOR_IDENTITY,
        tuple(sorted((*owner.MANDATORY_EFFECTIVE_SEEDS, 991234))), ('group.disclosed-exposed',), (), (), (),
        tuple(sorted((owner.MANDATORY_FLOOR_SHA256, provenance.sha256))), (provenance,))


def test_mandatory_floor_exactly_equals_independent_existing_effective_seed_union():
    modules_before = set(sys.modules)
    source = ROOT / 'src/empirical_lawhood'
    original = literal_assignment(source / 'adapters/simulators/six_matrix_response/observation_order_scientific_inputs.py', '_STREAM_ROWS')
    observation = {int(digest[:32], 16) for block in original for _, _, digest in block}
    public_history = {int(sha256(b'empirical-lawhood/history/numeric/v1\0' + (706256).to_bytes(32, 'big')
        + index.to_bytes(2, 'big') + bytes([purpose])).hexdigest()[:32], 16)
        for index in range(256) for purpose in range(4)}
    purposes = literal_assignment(source / 'kernel/matrix_inputs.py', 'MATRIX_NATIVE_PURPOSES')
    example = {*range(101, 101 + len(purposes)), 10001 >> 128}
    expected = observation | public_history | example
    assert (len(observation), len(public_history), len(example), len(expected)) == (1040, 1024, 10, 2074)
    actual = owner.load_mandatory_exposure_floor()
    assert actual.effective_seed_exclusions == tuple(sorted(expected))
    assert len(actual.canonical_bytes()) == owner.MANDATORY_FLOOR_SIZE
    assert actual.fingerprint() == owner.MANDATORY_FLOOR_SHA256
    assert actual.identity == owner.MANDATORY_FLOOR_IDENTITY
    assert not any(name.startswith('empirical_lawhood.api') for name in set(sys.modules) - modules_before)


@pytest.mark.parametrize('damage', ('same-size', 'truncated', 'extra-byte'))
def test_fresh_floor_loader_refuses_changed_literal_bytes(tmp_path, damage):
    original = owner.MANDATORY_EXPOSURE_FLOOR.canonical_bytes()
    changed = original.replace(b'"effective_seed_exclusions":[0,', b'"effective_seed_exclusions":[1,', 1)
    assert len(changed) == len(original) and changed != original
    if damage == 'truncated':
        changed = original[:-1]
    elif damage == 'extra-byte':
        changed = original + b' '
    path = tmp_path / 'copied-floor.json'
    path.write_bytes(changed)
    with pytest.raises(ValueError, match='resource bytes differ'):
        owner.load_mandatory_exposure_floor(path)


def test_current_census_roundtrip_uses_only_immutable_floor_and_explicit_facts(monkeypatch):
    modules_before = set(sys.modules)
    def forbidden(*args, **kwargs):
        pytest.fail('current census tried to load a historical package, example or file')
    monkeypatch.setattr(owner, 'files', forbidden)
    for name, attribute in (
            ('empirical_lawhood.adapters.methods.matrix_prospective.example', 'example_source'),
            ('empirical_lawhood.adapters.methods.matrix_history_analysis.records', 'matrix_known_exposed_effective_seeds')):
        if name in sys.modules:
            monkeypatch.setattr(sys.modules[name], attribute, forbidden)
    value = census()
    raw = value.canonical_bytes()
    assert decode_canonical_bytes(raw, owner.MatrixFactorExposureCensus, maximum_bytes=len(raw)) == value
    assert set(field.name for field in fields(value)).isdisjoint({
        'historical_bank', 'public_history_allocation', 'prior_allocations', 'prior_regimes', 'audit'})
    assert not {'empirical_lawhood.adapters.methods.matrix_prospective.example',
        'empirical_lawhood.adapters.methods.matrix_history_analysis.records'} & (set(sys.modules) - modules_before)


@pytest.mark.parametrize('damage', ('omitted', 'substituted-floor', 'duplicate', 'boolean', 'negative', 'too-wide', 'reordered'))
def test_current_union_refuses_floor_omission_and_inexact_effective_streams(damage):
    value = census()
    seeds = value.effective_seed_exclusions
    kwargs = {'effective_seed_exclusions': seeds}
    if damage == 'substituted-floor':
        kwargs['mandatory_floor'] = replace(value.mandatory_floor, object_fingerprint='b' * 64)
    else:
        kwargs['effective_seed_exclusions'] = {
            'omitted': seeds[1:], 'duplicate': (seeds[0], *seeds), 'boolean': (False, *seeds[1:]),
            'negative': (-1, *seeds), 'too-wide': (*seeds, 2**128), 'reordered': tuple(reversed(seeds)),
        }[damage]
    with pytest.raises((ValueError, TypeError)):
        replace(value, **kwargs)


@pytest.mark.parametrize('damage', ('no-facts', 'missing-floor-digest', 'missing-fact-digest', 'duplicate-facts'))
def test_current_union_keeps_content_pinned_external_facts(damage):
    value = census()
    changes = {
        'no-facts': {'factual_provenance': ()},
        'missing-floor-digest': {'exposed_artifact_sha256s': (value.factual_provenance[0].sha256,)},
        'missing-fact-digest': {'exposed_artifact_sha256s': (owner.MANDATORY_FLOOR_SHA256,)},
        'duplicate-facts': {'factual_provenance': value.factual_provenance * 2},
    }[damage]
    with pytest.raises(ValueError):
        replace(value, **changes)


def test_physical_exclusions_preserve_exact_constant_and_scheduled_keys():
    d = Decimal
    beta = BetaCouplingRule.PUBLISHED_DETERMINISTIC
    constant_key = (d('.5'), d('.5'), d('1'), beta, d('1.125'), d('1'), d('1'), d('1'))
    constant = owner.MatrixConstantPhysicalExclusion(*constant_key)
    scheduled_key = (d('.5'), d('.5'), d('1'), beta, d('1'), d('1.125'),
        'matrix-history.joint-decreasing-coupling', d('1'), d('1'), d('8'), d('.256'), d('.768'),
        'matrix-parameter-q2.four-family-initial.v1', 'matrix-parameter.preparation.v1')
    scheduled = owner.MatrixScheduledPhysicalExclusion(*scheduled_key)
    assert constant.key == constant_key and scheduled.key == scheduled_key
    value = replace(census(), constant_physical_exclusions=(constant,), scheduled_physical_exclusions=(scheduled,))
    assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
    with pytest.raises((ValueError, TypeError)):
        replace(scheduled, ramp_duration=.256)
    for physical in (constant, scheduled):
        with pytest.raises(ValueError, match='positive symmetric'):
            replace(physical, bath_temperature=d(0))
        with pytest.raises(ValueError, match='positive symmetric'):
            replace(physical, mass_y=d('1'))
    with pytest.raises(ValueError, match='repeat or reorder'):
        replace(value, constant_physical_exclusions=(constant, constant))


def test_physical_exclusion_is_unchanged_by_labels_and_refined_physical_clock():
    d = Decimal
    member = SimpleNamespace(member_id='member.original', mass_x=d('.5'), mass_y=d('.5'),
        cross_coupling_gamma=d('1'), beta_rule=BetaCouplingRule.PUBLISHED_DETERMINISTIC)
    values = dict(member=member, primary_view=SimpleNamespace(view_id='view.original', timestep=d('.001'),
        friction_gamma=d('1'), bath_temperature=d('1.125')), family_id='matrix-history.joint-decreasing-coupling',
        target_x=d('1'), target_y=d('1'), decreasing_start=d('8'), ramp_ticks=256, autonomous_ticks=768,
        initial_state_rule_id='matrix-parameter-q2.four-family-initial.v1', preparation_rule_id='matrix-parameter.preparation.v1')
    original = owner.MatrixScheduledPhysicalExclusion.from_coordinate(SimpleNamespace(**values))
    values.update(member=SimpleNamespace(**(vars(member) | {'member_id': 'member.renamed'})),
        primary_view=SimpleNamespace(view_id='view.renamed', timestep=d('.0005'), friction_gamma=d('1'), bath_temperature=d('1.125')),
        ramp_ticks=512, autonomous_ticks=1536)
    refined = owner.MatrixScheduledPhysicalExclusion.from_coordinate(SimpleNamespace(**values))
    assert refined == original
    assert refined.key in {original.key}


def test_current_support_is_one_exact_current_census_publication_without_historical_bodies():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import (
        ScheduledExposureAudit, exposure_census_publication, exposure_support,
    )
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import (
        ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, LogicalArtifactIdentity,
    )
    value = census()
    logical = LogicalArtifactIdentity('census.literal.current-publication', value.fingerprint(), value.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND,
        ArtifactGenericValidation('validator.literal-software', '1.0.0', 'a' * 64, value.SCHEMA, ArtifactProfile.CANONICAL_JSON))
    physical = ArtifactMaterialization('material.literal-current', logical.logical_artifact_id, 'storage.literal-software',
        'unpublished/current-census.json', value.fingerprint(), len(value.canonical_bytes()), 'none')
    sidecar = replace(physical, materialization_id='sidecar.literal-current', logical_artifact_id=logical.logical_artifact_id + '.manifest',
        relative_path='unpublished/current-census.json.manifest.json', physical_sha256='b' * 64, size_bytes=1)
    publication = ArtifactWriteResult(logical, physical, sidecar, False)
    audit = ScheduledExposureAudit('audit.literal-current', value, (), (publication,))
    assert exposure_census_publication(audit) is publication
    support = exposure_support(audit)
    assert len(support) == 1 and support[0][1] is publication
    artifact = support[0][0]
    assert artifact.role == 'matrix-current-exposure-census'
    assert (artifact.sha256, artifact.size_bytes) == (value.fingerprint(), len(value.canonical_bytes()))
    with pytest.raises(ValueError):
        replace(audit, prior_corpus=())
    with pytest.raises(ValueError):
        replace(audit, prior_corpus=(replace(publication, logical=replace(logical, content_sha256='c' * 64)),))


def test_current_census_does_not_decode_prior_record_edition():
    document = json.loads(census().canonical_bytes())
    document['version'] = '1.0.0'
    with pytest.raises(ValueError):
        decode_canonical_bytes(json.dumps(document, separators=(',', ':'), sort_keys=True).encode() + b'\n',
            owner.MatrixFactorExposureCensus, maximum_bytes=None)
    assert type(owner.MANDATORY_FLOOR_IDENTITY) is ObjectIdentity
