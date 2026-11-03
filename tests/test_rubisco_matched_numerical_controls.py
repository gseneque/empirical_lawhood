# SPDX-License-Identifier: MPL-2.0
"""Exposed typed adversaries only: no models, native calls or qualification."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation import controlled_constructs
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import PreparationIntegrity
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import PhysicalPreparationGeometry
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import contracts as sampling, control_contracts as f, nve_contracts as n
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.matched_controls import (
    MatchedNumericalAssessment, NVE_KEYS, SCIENCE_PREFIXES, assess_matched_numerical,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.science import hardware_from_stdout
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkCompletion


def identity(name, kind):
    schema = kind if isinstance(kind, str) else kind.SCHEMA
    return ObjectIdentity('exposed.'+name, schema, '1.0.0', sha256(name.encode()).hexdigest())


def source(label):
    gp_lsu = 'A'*493
    ssu = 'M'+'A'*93+'I'+'A'*43
    constructs = controlled_constructs(gp_lsu=gp_lsu, gp_ssu_m1=ssu, gp_ssu_v1='V'+ssu[1:],
        te_lsu='A'*414+'P'+'A'*60, te_ssu='A'*97+'V'+'A'*20)
    nomination = identity('nomination', 'empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier')
    nomination = replace(nomination, object_fingerprint='8121b9e941cbc66d0634dbc9f3047c6e22232fb1a783f2a313a17bf5f63f35fa')
    stock = p.SourceMember('source.exposed', 'EXPOSED_TEST_STOCK_NOT_AUTHENTIC_SCIENCE', sha256(b'exposed').hexdigest(), 'exposed')
    return p.PreparationSelection('input.exposed.source.'+label,
        identity('inventory', 'empirical-lawhood/rubisco-insilico-structure/inventory'),
        identity('coordinates', 'empirical-lawhood/rubisco-insilico-structure/assembly-coordinates'), nomination,
        p.NATIVE_WORK_ROOT+'/exposed-'+label+'-never-entered', p.ENGINE_INVENTORY_SHA256, constructs, (stock,))


def files(unit, names):
    return tuple(sorted((p.FileEvidence(unit+'/'+name, 7, sha256(b'exposed').hexdigest()) for name in names), key=lambda row: row.relative_path))


def episode(material, label):
    """Typed illustrative records, not molecular/independent assessment supply."""
    original = source(label)
    names = tuple(f.model_id((material, 'joint-01', parameter)) for parameter in p.PARAMETER_VIEWS)
    code = tuple(sorted((prefix+'native.py', '4'*64) for prefix in SCIENCE_PREFIXES))
    plan = f.ChemicalForcePlan('config.exposed.chemical.'+label, p.identity(original), identity('preparation.'+label, p.PreparationProduct),
        identity('integrity.'+label, PreparationIntegrity), identity('geometry.'+label, PhysicalPreparationGeometry),
        tuple((name, identity('asset.'+name, p.ModelAssets)) for name in names),
        tuple((name, identity('definition.'+name, NativeSubworkDefinition), identity('completion.'+name, NativeSubworkCompletion),
            identity('return.'+name, DurableUnitReturn)) for name in names),
        hardware_from_stdout(b'GPU-exposed, Exposed software fixture, 0, 0000:00:00.0, 1, 0\n'),
        p.NATIVE_WORK_ROOT+'/exposed-chemical-'+label+'-never-entered', '/tmp/exposed-interpreter', '1'*64,
        p.ENGINE_INVENTORY_SHA256, '/tmp/exposed-inspector', '2'*64, code, '3'*64)
    returns, assessments, parents = [], [], []
    for name, asset in plan.selected_assets:
        unit = 'control.chemical-force.'+name
        raw = files(unit, ('force-control.npz', 'minimized.xml', 'cpu-force-reference.xml', 'minimizer-termination.json',
            'minimizer-progress.jsonl', 'declared-system-constraints.json', 'minimizer-apparatus.json',
            'apparatus-cuda.json', 'apparatus-cpu.json', 'controlled-system-01.xml', 'controlled-integrator-01.xml'))
        returned = f.ChemicalForceReturn(unit, plan.identity, asset, True, 2, unit+'/force-control.npz', raw,
            (identity('call.'+name, NativeSubworkDefinition),))
        assessed = f.ChemicalForceAssessment('assessment.exposed.'+name, plan.identity, returned.identity,
            A.SATISFIED, A.SATISFIED, Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), ())
        returns.append(returned)
        assessments.append(assessed)
        parents.append((name, identity('relaxed.'+name, n.RelaxedModelSupply), identity('force-definition.'+name, NativeSubworkDefinition),
            identity('force-completion.'+name, NativeSubworkCompletion), returned.identity,
            ObjectIdentity.from_record(assessed.product_id, assessed)))
    selected = tuple(sorted((material, 'joint-01', *key) for key in NVE_KEYS))
    nve_plan = n.NVEControlPlan('config.exposed.nve.'+label, plan, tuple(parents), selected,
        p.NATIVE_WORK_ROOT+'/exposed-nve-'+label+'-never-entered', code, '3'*64)
    nve_returns = []
    for key in selected:
        unit = n.unit_id(key)
        raw = files(unit, ('numerical-control.json', 'nve-progress.jsonl', 'apparatus-cuda.json', 'initial-full-state.xml',
            *('nve-state-'+str(i).zfill(2)+'.xml' for i in range(1, 11)),
            *('nve-checkpoint-'+str(i).zfill(2)+'.bin' for i in range(11))))
        supply = next(row[1] for row in parents if row[0] == f.model_id(key[:3]))
        nve_returns.append(n.NVEControlReturn(unit, nve_plan.identity, supply, True, 2, raw,
            (identity('nve-call.'+unit, NativeSubworkDefinition),)))
    actual = {row.unit_id for row in nve_returns}
    cases = tuple((name, A.SATISFIED, Decimal('0'), ()) if name in actual
        else (name, A.UNEVALUABLE, None, ('UNENTERED_EXPOSED_FIXTURE',)) for name in n.unit_ids())
    refinements = tuple((n.unit_id(key).rsplit('.', 1)[0], A.SATISFIED, Decimal('0'), Decimal('0')) if n.unit_id(key) in actual
        else (n.unit_id(key).rsplit('.', 1)[0], A.UNEVALUABLE, None, None)
        for key in sampling.trajectory_roster() if key[-1] == 'primary')
    components = tuple((name, 0, 1) if name in actual else (name, None, None) for name in n.unit_ids())
    assessed = n.NVEControlAssessment('assessment.exposed.nve.'+label, nve_plan.identity,
        tuple(row.identity for row in sorted(nve_returns, key=lambda row: row.unit_id)), cases, refinements, A.UNEVALUABLE, components)
    return dict(source=original, chemical_plan=plan, chemical_returns=tuple(returns), chemical_assessments=tuple(assessments),
        nve_plan=nve_plan, nve_returns=tuple(nve_returns), nve_assessment=assessed)


def compare(wt, mutant):
    kwargs = {prefix+key: value for prefix, data in (('wt_', wt), ('i95m_', mutant)) for key, value in data.items() if key != 'source'}
    return assess_matched_numerical('assessment.exposed.matched', wt['source'], mutant['source'], **kwargs)


@pytest.fixture
def pair():
    return episode('gp.wt.m1', 'wt'), episode('gp.i95m.m1', 'i95m')


def test_missing_actual_controls_preserve_both_full_denominators_without_entry():
    result = assess_matched_numerical('assessment.exposed.missing', source('wt'), source('i95m'))
    assert result.selected_numerical_disposition is A.UNEVALUABLE
    assert len(result.paired_chemical) == 2 and len(result.paired_nve) == 8 and len(result.paired_refinements) == 4
    assert all(len(row.chemical_outcomes) == 24 and len(row.nve_cases) == 96 and len(row.nve_refinements) == 48 for row in result.episodes)
    assert all(not row.chemical_returns and not row.nve_returns for row in result.episodes)


def test_selected_pairs_can_pass_while_whole96_and_physical_scope_stay_unevaluable(pair):
    result = compare(*pair)
    assert result.selected_numerical_disposition is A.SATISFIED
    assert all(data['nve_assessment'].disposition is A.UNEVALUABLE for data in pair)
    assert all(sum(row[1] is A.UNEVALUABLE for row in episode.nve_cases) == 88 for episode in result.episodes)
    assert result.ensemble_adequacy is result.structural_effect is result.kinetic_transport is result.biological_target is A.UNEVALUABLE
    raw = result.canonical_bytes()
    assert decode_canonical_bytes(raw, MatchedNumericalAssessment, maximum_bytes=len(raw)) == result


@pytest.mark.parametrize('kind', ['chemical', 'nve'])
def test_positive_assessment_without_original_return_cannot_admit_a_pair(pair, kind):
    wt, mutant = pair
    mutant = dict(mutant, **{kind+'_returns': mutant[kind+'_returns'][1:]})
    result = compare(wt, mutant)
    assert result.selected_numerical_disposition is A.UNEVALUABLE
    original = mutant['nve_assessment']
    assert result.episodes[1].nve_cases == original.cases
    assert result.episodes[1].reported_component_excursions == original.reported_component_excursions


def test_known_negative_survives_missing_other_controls(pair):
    wt, mutant = pair
    first = mutant['chemical_assessments'][0]
    negative = replace(first, objective_precision_disposition=A.REFUSED, objective_gradient_rms_kj_mol_nm=Decimal('11'),
        reason_codes=('EXPOSED_OBJECTIVE_PRECISION_MISS',))
    mutant = dict(mutant, chemical_assessments=(negative, *mutant['chemical_assessments'][1:]), nve_plan=None,
        nve_returns=(), nve_assessment=None)
    result = compare(wt, mutant)
    assert result.selected_numerical_disposition is A.REFUSED
    assert result.paired_chemical[0][2] is A.REFUSED
    assert all(row[2] is A.UNEVALUABLE for row in result.paired_nve)


def test_source_or_apparatus_mismatch_is_a_retained_local_refusal():
    wt, mutant = source('wt'), source('i95m')
    stock = p.SourceMember('source.exposed', 'EXPOSED_CHANGED_STOCK', sha256(b'changed').hexdigest(), 'changed')
    changed = replace(mutant, source_members=(stock,))
    result = assess_matched_numerical('assessment.exposed.source-mismatch', wt, changed)
    assert result.source_compatibility is result.selected_numerical_disposition is A.REFUSED
    first, second = episode('gp.wt.m1', 'wt'), episode('gp.i95m.m1', 'i95m')
    changed_plan = replace(second['chemical_plan'], interpreter_sha256='9'*64)
    result = assess_matched_numerical('assessment.exposed.apparatus-mismatch', first['source'], second['source'],
        wt_chemical_plan=first['chemical_plan'], i95m_chemical_plan=changed_plan)
    assert result.apparatus_compatibility is result.selected_numerical_disposition is A.REFUSED


def test_extra_genotype_change_cannot_be_hidden_by_a_matched_source_label():
    original = source('wt')
    rows = tuple(replace(row, ssu_sequence=row.ssu_sequence[:95]+'R'+row.ssu_sequence[96:])
        if row.construct_id == 'gp.i95m.m1' else row for row in original.constructs)
    wt = replace(original, constructs=rows)
    mutant = replace(wt, selection_id='input.exposed.second', native_workdir=p.NATIVE_WORK_ROOT+'/exposed-other-never-entered')
    result = assess_matched_numerical('assessment.exposed.extra-edit', wt, mutant)
    assert result.source_compatibility is A.REFUSED


@pytest.mark.parametrize('field', ['ensemble_adequacy', 'structural_effect', 'native_optimizer_convergence', 'kinetic_transport', 'biological_target'])
def test_numerical_report_cannot_promote_physical_or_target_scope(pair, field):
    with pytest.raises(ValueError, match='cannot qualify'):
        replace(compare(*pair), **{field: A.SATISFIED})


def test_counterfeit_positive_pair_or_substituted_original_identity_refuses(pair):
    missing = assess_matched_numerical('assessment.exposed.missing', source('wt'), source('i95m'))
    forged = tuple((key, A.SATISFIED, A.SATISFIED, A.SATISFIED) for key in NVE_KEYS)
    with pytest.raises(ValueError, match='substitutes original'):
        replace(missing, paired_nve=forged)
    wt, mutant = pair
    foreign = replace(mutant['chemical_returns'][0], plan=wt['chemical_plan'].identity)
    with pytest.raises(ValueError, match='substitutes original chemical'):
        compare(wt, dict(mutant, chemical_returns=(foreign, *mutant['chemical_returns'][1:])))
    with pytest.raises(ValueError, match='distinct original source'):
        assess_matched_numerical('assessment.exposed.same-source', wt['source'], wt['source'])


def test_operator_source_changes_remain_explicit_in_comparability():
    wt, mutant = episode('gp.wt.m1', 'wt'), episode('gp.i95m.m1', 'i95m')
    code = tuple((path, '9'*64 if path == SCIENCE_PREFIXES[1]+'native.py' else digest)
        for path, digest in mutant['chemical_plan'].code_sources)
    result = assess_matched_numerical('assessment.exposed.operator-mismatch', wt['source'], mutant['source'],
        wt_chemical_plan=wt['chemical_plan'], i95m_chemical_plan=replace(mutant['chemical_plan'], code_sources=code))
    assert result.apparatus_compatibility is A.REFUSED


def test_full_denominator_or_seed_pair_cannot_be_thinned(pair):
    result = compare(*pair)
    with pytest.raises(ValueError, match='denominators'):
        replace(result.episodes[0], nve_cases=result.episodes[0].nve_cases[:-1])
    with pytest.raises(ValueError, match='seed/resolution'):
        replace(result, paired_nve=result.paired_nve[:-1])


def test_own_nve_dependency_lock_difference_refuses_matching_apparatus(pair):
    wt, mutant = pair
    plan = replace(mutant['nve_plan'], dependency_lock_sha256='9'*64)
    returns = tuple(replace(row, plan=plan.identity) for row in mutant['nve_returns'])
    assessment = replace(mutant['nve_assessment'], plan=plan.identity,
        returned=tuple(row.identity for row in returns))
    result = compare(wt, dict(mutant, nve_plan=plan, nve_returns=returns, nve_assessment=assessment))
    assert result.apparatus_compatibility is result.selected_numerical_disposition is A.REFUSED
    assert 'MATCHED_NUMERICAL_APPARATUS_DIFFERS' in result.reason_codes


@pytest.mark.parametrize('field', ['chemical_plan', 'nve_plan', 'nve_assessment'])
def test_positive_episode_cannot_lose_declared_plan_or_independent_nve_parent(pair, field):
    result = compare(*pair)
    with pytest.raises(ValueError, match='loses'):
        replace(result.episodes[1], **{field: None})


def test_positive_episode_cannot_lose_independent_chemical_parents(pair):
    episode = compare(*pair).episodes[1]
    with pytest.raises(ValueError, match='exact independent chemical'):
        replace(episode, chemical_assessments=())
    with pytest.raises(ValueError, match='per-unit independent chemical'):
        replace(episode, chemical_assessments=(), chemical_assessment_parents=())


def test_unrelated_nonempty_chemical_assessment_does_not_cover_missing_unit(pair):
    episode = compare(*pair).episodes[1]
    parents = episode.chemical_assessment_parents[1:]
    assert parents
    with pytest.raises(ValueError, match='per-unit independent chemical'):
        replace(episode, chemical_assessment_parents=parents,
            chemical_assessments=tuple(row for row in episode.chemical_assessments if row == parents[0][1]))


def test_exact_assessed_return_revisions_cannot_be_substituted(pair):
    episode = compare(*pair).episodes[1]
    returned, assessment = episode.chemical_assessment_parents[0]
    with pytest.raises(ValueError, match='original chemical return bytes'):
        replace(episode, chemical_assessment_parents=(
            (replace(returned, object_fingerprint='9'*64), assessment), *episode.chemical_assessment_parents[1:]))
    with pytest.raises(ValueError, match='NVE return bytes'):
        replace(episode, nve_assessed_returns=(
            replace(episode.nve_assessed_returns[0], object_fingerprint='9'*64), *episode.nve_assessed_returns[1:]))


def test_positive_refinement_requires_both_assessed_positive_cases(pair):
    episode = compare(*pair).episodes[1]
    selected = episode.nve_returns[0].object_id
    cases = tuple((name, A.UNEVALUABLE, None, ('EXPOSED_MISSING_CASE',)) if name == selected else row
        for row in episode.nve_cases for name in (row[0],))
    with pytest.raises(ValueError, match='refinement returns'):
        replace(episode, nve_cases=cases)


def test_absent_nve_assessment_retains_real_returns_with_unevaluable_outcomes(pair):
    wt, mutant = pair
    result = compare(wt, dict(mutant, nve_assessment=None))
    episode = result.episodes[1]
    assert episode.nve_returns and not episode.nve_assessed_returns
    assert episode.nve_assessment is None
    assert all(row[1] is A.UNEVALUABLE for row in (*episode.nve_cases, *episode.nve_refinements))
    assert result.selected_numerical_disposition is A.UNEVALUABLE


def test_independently_assessed_negative_with_missing_return_is_retained(pair):
    wt, mutant = pair
    original = mutant['chemical_assessments'][0]
    adverse = replace(original, objective_precision_disposition=A.REFUSED,
        objective_gradient_rms_kj_mol_nm=Decimal('11'), reason_codes=('EXPOSED_INDEPENDENT_NEGATIVE',))
    result = compare(wt, dict(mutant, chemical_returns=(),
        chemical_assessments=(adverse, *mutant['chemical_assessments'][1:]),
        nve_plan=None, nve_returns=(), nve_assessment=None))
    assert result.selected_numerical_disposition is A.REFUSED
    assert result.paired_chemical[0][2] is A.REFUSED
    assert result.episodes[1].chemical_assessment_parents
    assert not result.episodes[1].chemical_returns
