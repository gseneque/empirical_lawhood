# SPDX-License-Identifier: MPL-2.0
"""Disclosed quadratic controls for staged environmental acquisition and custody.

These operators test software and a specified matrix, not molecular validity,
provider deployment, or any I95M mechanism. The public lifecycle owns actual
contribution export, inquiry admission and process-backed interpretation.
"""

from dataclasses import replace
import json
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import preparation_response_read as reader
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_operation as shared
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_native
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import BOHR_ANGSTROM
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import selected_prefix_scope
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_action_read import direction_values
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import assess_response_operands, freeze_response_predictions
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import EnvironmentalPreparationResponseAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, POSITIONS, response_effects, response_scope
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import prepare_environmental_frames
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import prepare_response_point, read_response_center
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import PreparationSupplySelection, assess_supply
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import preparation_response_draft
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from tests import test_rubisco_preparation_response as control

fixture = control.fixture
matched = control.matched
prefix = control.prefix


def _parent(records, scope, label):
    """Declared references for software controls; they confer no custody authority."""
    products = tuple(ContributionProduct('product.exposed.' + label + '.' + str(index), record.identity,
        ArtifactIdentity(record.identity.object_id, 'exposed-environment-control', record.SCHEMA,
            record.fingerprint(), 'application/json', record.canonical_size_bytes()),
        ObjectIdentity('receipt.exposed.' + label, CanonicalTaskReceipt.SCHEMA, CanonicalTaskReceipt.VERSION, '1' * 64),
        ContributionRole.RETAINED_ANALYSIS_INPUT, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
        for index, record in enumerate(records))
    return ContributionManifest('contribution.exposed.' + label, 'Test the original staged environmental consumer.',
        'Declared software-control references without qualification or molecular claims.', scope, products,
        tuple(sorted((record.identity for record in records), key=lambda pin: pin.object_id)), ())


def install_quadratic_environment(paired, monkeypatch):
    """Choose a matrix independently of nomination, then return its exact gradient."""
    calls = []
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: None)
    monkeypatch.setattr(shared, 'authenticate_periodic_engine', lambda *a, **k: None)
    support = paired.design.environment.atom_pairs[0]
    indices = {model: support[4 + MODELS.index(model)] for model in MODELS}

    def execute(**kwargs):
        records = dict(kwargs['coordinate_records'])
        effect = records['response-point.json'].effect
        key = effect.model_name, effect.position
        xyz, base = read_response_center(paired.centers[key], paired.raw[key])
        u = direction_values(paired.frames[effect.model_name].primary, len(xyz))
        d = np.zeros_like(xyz)
        d[indices[effect.model_name], 0] = 1.
        dx = (kwargs['coordinates'] - xyz) / BOHR_ANGSTROM
        receiver, environment = np.vdot(u, dx), np.vdot(d, dx)
        # This control selects the sufficient-initial-response path. Increase
        # the later signal so signal suppression is not a competing finding.
        coupling = .15 if effect.position == 'initial' else .18
        gradient = base + (.2 * receiver + coupling * environment) * u
        gradient += (.4 * environment + coupling * receiver) * d
        energy = float(np.vdot(base, dx) + .1 * receiver**2 + .2 * environment**2
            + coupling * receiver * environment)
        root = kwargs['root']
        for name, record in (*records.items(), ('selection.json', kwargs['selection']),
                ('electronic-settings.json', kwargs['settings']), ('mm-settings.json', kwargs['mm_settings']),
                ('cell.json', kwargs['cell'])):
            (root / name).write_bytes(record.canonical_bytes())
        (root / 'original.prmtop').write_bytes(kwargs['raw_topology'])
        (root / 'original.inpcrd').write_bytes(kwargs['raw_coordinates'])
        np.save(root / 'coordinate-array.npy', kwargs['coordinates'], allow_pickle=False)
        (root / 'native-observations.jsonl').write_text(''.join(json.dumps(dict(event=event, evaluation=1,
            converged=True, orbital_gradient_norm=0., energy_hartree=energy)) + '\n'
            for event in ('entry', 'electronic-return', 'return')))
        calls.append((effect, kwargs['coordinates'].copy()))
        return dict(energy_hartree=energy, gradient_hartree_per_bohr=gradient)

    monkeypatch.setattr(periodic_probe_native, '_execute_periodic_at_coordinates', execute)
    return calls


def _read(paired, stages, results, custody, label, *, frames=None, assessor=None):
    return reader.read_preparation_response(stages=stages, original_results=results,
        representations={name: f.model for name, f in paired.fixtures.items()}, centers=paired.centers,
        frames=paired.frames if frames is None else frames, center_bytes=paired.raw,
        native_subwork_for_result=lambda result: custody[result.result_id],
        assessor_source=paired.assessor if assessor is None else assessor, assessment_id='assessment.exposed.environment.' + label)


def _configs(paired, stage, parent, diagnostic=None, diagnostic_parent=None, predictions=()):
    predicted = dict(predictions)
    configs = []
    for effect in response_effects(paired.design, stage):
        key = effect.model_name, effect.position
        member = paired.fixtures[effect.model_name]
        point = prepare_response_point(design=paired.design, center=paired.centers[key], frame=paired.frames[effect.model_name],
            effect=effect, prototype=member.prototype, center_bytes=paired.raw[key], prediction=predicted.get(key))
        configs.append(owner.PreparationResponseConfig('config.' + point.point_id, member.probe, paired.design,
            paired.centers[key], paired.frames[effect.model_name], point, parent, diagnostic, diagnostic_parent))
    return tuple(configs)


def _eligibility(paired, configs, report, prefix_parent, monkeypatch):
    """Only scientific policy inputs are declared here, without new native work."""
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_supply_decision as decision
    from empirical_lawhood.domains.rubisco.rubisco_response import preparation_supply_policy as policy
    response_parent = _parent((report,), response_scope(paired.design), 'response-policy')
    selection = PreparationSupplySelection(paired.design, paired.readouts, report,
        tuple(sorted((prefix_parent, response_parent), key=lambda p: p.contribution_id)))
    supply = assess_supply(selection)
    with monkeypatch.context() as patch:
        patch.setattr(decision, 'original_supply_results', lambda completed: (supply,))
        patch.setattr(policy, 'supply_owners', lambda draft: (configs, selection.scope, None, None))
        result = decision.assess_supplier_eligibility(draft=SimpleNamespace(), design=paired.design, completed=())
    return result, supply


def test_unusable_paired_preparation_reaches_destination_with_original_evidence(prefix, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_supply import prepare_preparation_supply
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import assess_unavailable_preparation, response_supplier_decision

    paired = control.paired_preparation(prefix, monkeypatch, environmental=True)
    for index, original in enumerate(paired.readouts):
        assessment = original.assessment
        initial, later = assessment.positions
        rejected_checkpoint = replace(assessment.checkpoints[-1], findings=('test.geometry',), disposition='REJECTED')
        rejected = replace(assessment, checkpoints=(*assessment.checkpoints[:-1], rejected_checkpoint),
            positions=(initial, replace(later, disposition='REJECTED')))
        incomplete = replace(assessment, checkpoints=assessment.checkpoints[:1],
            positions=(initial, replace(later, checkpoint=None, disposition='UNAVAILABLE')))
        for failure in (None, rejected, incomplete):
            changed = replace(original, assessment=failure, assessment_error='Disclosed read failure' if failure is None else None)
            readouts = list(paired.readouts)
            readouts[index] = changed
            readouts = tuple(readouts)
            report = assess_unavailable_preparation(design=paired.design, readouts=readouts,
                assessor_source=paired.assessor, assessment_id='report.exposed.missing-prefix')
            assert report.next_supplier_decision == response_supplier_decision(report)
            assert [(q.assessable_comparisons, q.assigned_comparisons) for q in report.questions] == [
                (0, 6), (0, 4), (0, 2), (0, 4), (0, 2), (0, 2)]
            parents = (_parent(readouts, selected_prefix_scope(paired.design.prefix), 'prefix'),
                _parent((report,), response_scope(paired.design), 'response'))
            prepared = prepare_preparation_supply(design=paired.design, original_prefixes=readouts,
                original_response=report, parents=parents)
            result = assess_supply(prepared['config'].selection)
            assert result.next_supplier_decision == 'DECLINE_DIAGNOSTIC_WITHOUT_THE_COMPLETE_USABLE_PAIRED_HANDOFF'
            assert result.response_disposition.value == 'UNEVALUABLE'
            assert all(row.point is None and row.original_readout is None for row in report.coverage)
            with pytest.raises(ValueError, match='available paired preparation'):
                prepare_preparation_supply(design=paired.design, original_prefixes=paired.readouts,
                    original_response=report, parents=parents)
            other = replace(changed, readout_id='readout.exposed.substituted')
            swapped = tuple(other if r is changed else r for r in readouts)
            with pytest.raises(ValueError, match='original paired prefix evidence'):
                prepare_preparation_supply(design=paired.design, original_prefixes=swapped,
                    original_response=report, parents=parents)


def test_staged_environment_custody_nomination_predictions_and_finite_receiver(prefix, monkeypatch):
    paired = control.paired_preparation(prefix, monkeypatch, environmental=True)
    control._compile_admission(paired)
    prefix_parent = _parent(paired.readouts, selected_prefix_scope(paired.design.prefix), 'prefix')
    original_frames = dict(paired.frames)
    assert all(frame.additional is None and frame.challenge is None for frame in original_frames.values())
    calls = install_quadratic_environment(paired, monkeypatch)
    results, custody = {}, {}
    initial = control.run_stage(paired, 'initial-primary', results, custody, monkeypatch=monkeypatch,
        preparation_parent=prefix_parent)
    draft = preparation_response_draft(initial)
    assert len(draft.operations) == len(draft.development_study.numerical_view_ids) == len(calls) == 8
    first, _, readouts = _read(paired, (initial,), results, custody, 'initial')
    assert first.nomination.disposition == 'AVAILABLE'
    assert len(first.nomination.original_readouts) == 8
    assert all(r.readout_id == owner.node_id(c) + '.assessment' for r, c in zip(
        sorted(readouts, key=lambda r: r.point.effect.ordinal), initial, strict=True))
    assert first.next_supplier_decision == 'ASSESS_SELECTED_ENVIRONMENT_DIAGNOSTIC_WITH_FIXED_INITIAL_WT_DIRECTION'
    with pytest.raises(ValueError, match='complete consistent diagnostic'):
        freeze_response_predictions(assessment=first, centers=paired.centers, frames=paired.frames)
    missing = dict(results)
    del missing[initial[0].point.effect.effect_id]
    incomplete, _, _ = _read(paired, (initial,), missing, custody, 'missing-initial')
    assert incomplete.nomination.disposition == 'UNAVAILABLE_INITIAL_ACTIONS'
    assert incomplete.next_supplier_decision == 'RETAIN_UNAVAILABLE_INITIAL_ACTIONS_WITHOUT_ENVIRONMENTAL_ACQUISITION'
    with pytest.raises(ValueError, match='available shared nomination'):
        prepare_environmental_frames(design=paired.design, frames=paired.frames, nomination=incomplete.nomination)
    initial_parent = _parent((first,), response_scope(paired.design), 'initial')
    paired.frames = prepare_environmental_frames(design=paired.design, frames=paired.frames, nomination=first.nomination)
    for model, frame in paired.frames.items():
        assert frame.primary == original_frames[model].primary
        assert frame.additional == frame.challenge and frame.additional.source == first.nomination.identity
        assert not set(atom for atom, _, _ in frame.additional.components) & set(frame.coordinate.native_atom_indices)
    later = control.run_stage(paired, 'environment-diagnostic', results, custody,
        preparation_parent=prefix_parent, diagnostic=first, diagnostic_parent=initial_parent)
    assert len(later) == 12 and len(calls) == 20
    diagnostic, _, _ = _read(paired, (initial, later), results, custody, 'diagnostic')
    assert diagnostic.nomination == first.nomination
    assert diagnostic.questions[0].disposition == 'EMPIRICALLY_CONSISTENT'
    assert diagnostic.questions[1].disposition == 'CONSEQUENTIAL_OMITTED_COUPLING'
    assert all(q.disposition == 'UNAVAILABLE' for q in diagnostic.questions[3:])
    projected = [q.value for q in diagnostic.quantities if q.name == 'prediction-scale-discrepancy']
    assert len(projected) == 4 and all(v is not None and v <= first.nomination.numerical_allowance_hartree_per_bohr for v in projected)
    for config in later:
        with pytest.raises(ValueError, match='original preparation and initial diagnostic suppliers'):
            replace(config, preparation_parent=None)
        with pytest.raises(ValueError, match='original preparation and initial diagnostic suppliers'):
            replace(config, diagnostic=None, diagnostic_parent=None)
    diagnostic_parent = _parent((diagnostic,), response_scope(paired.design), 'diagnostic')
    with pytest.raises(ValueError, match='before later or finite outcomes'):
        replace(later[0], diagnostic=diagnostic, diagnostic_parent=diagnostic_parent)
    predictions = freeze_response_predictions(assessment=diagnostic, centers=paired.centers, frames=paired.frames)
    assert len(predictions) == 4
    for (model, position), prediction in predictions:
        assert prediction.scalar_change_hartree_per_bohr == 0
        assert float(prediction.predicted_change_hartree_per_bohr) == pytest.approx(-.2 * (.15 if position == 'initial' else .18), abs=2e-13)
        assert prediction.native_force_uncertainty == 'UNAVAILABLE'
    challenge = control.run_stage(paired, 'challenge', results, custody, predictions,
        preparation_parent=prefix_parent, diagnostic=diagnostic, diagnostic_parent=diagnostic_parent)
    final, arrays, _ = _read(paired, (initial, later, challenge), results, custody, 'final')
    assert len(calls) == 24 and final.nomination == first.nomination
    assert final.questions[3].disposition == 'WITHIN_SELECTED_ERROR_ALL_POSITIONS'
    assert final.questions[5].disposition == 'PREPARATION_NOT_NEEDED_FOR_SELECTED_TOLERANCE'
    assert final.next_supplier_decision == 'RETAIN_SUFFICIENT_INITIAL_RESPONSE_AND_ASSESS_OMITTING_ADDITIONAL_PREPARATION'
    expected = {(model, position): -.2 * (.15 if position == 'initial' else .18) for model, position in POSITIONS}
    actual = {(q.model_name, q.position): float(q.value) for q in final.quantities if q.name == 'observed-change'}
    assert actual == pytest.approx(expected, abs=2e-13)
    assert all(abs(float(q.value)) < 2e-13 for q in final.quantities if q.name == 'signed-prediction-error')
    for effect, xyz in calls:
        if effect.stage == 'challenge':
            base, _ = read_response_center(paired.centers[effect.model_name, effect.position], paired.raw[effect.model_name, effect.position])
            receiver = list(dict(paired.design.formation_coordinates)[effect.model_name].native_atom_indices)
            assert np.array_equal(xyz[receiver], base[receiver])
    control._compile_admission(paired, final)
    assert decode_canonical_bytes(final.canonical_bytes(), EnvironmentalPreparationResponseAssessment, maximum_bytes=16 * 2**20) == final
    different_assessor = replace(paired.assessor, object_id='source.exposed.second-independent-reader')
    reread, replayed, _ = _read(paired, (initial, later, challenge), results, custody, 'independent', assessor=different_assessor)
    assert reread.nomination == final.nomination
    assert all(np.array_equal(a, b) for (_, a), (_, b) in zip(arrays, replayed, strict=True))
    with pytest.raises(ValueError, match='before any challenge'):
        freeze_response_predictions(assessment=final, centers=paired.centers, frames=paired.frames)
    final_parent = _parent((final,), response_scope(paired.design), 'final')
    selected_refinement = _configs(paired, 'additional-refinement', prefix_parent, final, final_parent)
    decision, _ = _eligibility(paired, selected_refinement, final, prefix_parent, monkeypatch)
    assert not decision.allowed and 'Decline the optional refinement' in decision.consequence
    # Exercise the bounded worker path as a disclosed software control; the
    # scientific policy above correctly declines this unnecessary acquisition.
    refinement = control.run_stage(paired, 'additional-refinement', results, custody,
        preparation_parent=prefix_parent, diagnostic=final, diagnostic_parent=final_parent)
    refined, _, _ = _read(paired, (initial, later, challenge, refinement), results, custody, 'refined')
    assert len(calls) == 28 and refined.nomination == final.nomination
    assert refined.questions[0].disposition == 'EMPIRICALLY_CONSISTENT'
    assert all(q.independent_biological_replicates == 0 and q.original_starting_hypotheses == 384 for q in refined.questions)


def test_environment_negative_nomination_and_mapping_gate_retain_original_denominator(prefix, monkeypatch):
    paired = control.paired_preparation(prefix, monkeypatch, environmental=True)
    report, _ = assess_response_operands(design=paired.design, centers=paired.centers, frames=paired.frames,
        center_bytes=paired.raw, selected_points={}, readouts={}, values={}, assessor_source=paired.assessor,
        assessment_id='assessment.exposed.environment.no-response-purchase')
    assert report.nomination.disposition == 'UNAVAILABLE_INITIAL_ACTIONS'
    assert len(report.coverage) == 28 and all(row.original_readout is None for row in report.coverage)
    assert report.next_supplier_decision == 'RETAIN_UNAVAILABLE_INITIAL_ACTIONS_WITHOUT_ENVIRONMENTAL_ACQUISITION'
    prefix_parent = _parent(paired.readouts, selected_prefix_scope(paired.design.prefix), 'prefix-negative')
    initial = _configs(paired, 'initial-primary', prefix_parent)
    allowed, _ = _eligibility(paired, initial, report, prefix_parent, monkeypatch)
    assert allowed.allowed  # Missing initial evidence still permits its first purchase.
    # A declared adverse report tests policy only. Numerical mapping itself is
    # independently tested against coordinate arrays in the pure controls.
    invalid = replace(report.nomination, nomination_id='nomination.exposed.invalid-coordinate-map',
        disposition='INVALID_COORDINATE_CORRESPONDENCE',
        maximum_coordinate_discrepancy_angstrom=paired.design.environment.coordinate_tolerance_angstrom * 2)
    stopped = replace(report, assessment_id='assessment.exposed.environment.invalid-coordinate-map',
        nomination=invalid, next_supplier_decision='RETAIN_INVALID_COORDINATE_CORRESPONDENCE_WITHOUT_ENVIRONMENTAL_ACQUISITION')
    refused, retained = _eligibility(paired, initial, stopped, prefix_parent, monkeypatch)
    assert not refused.allowed and refused.consequence == stopped.next_supplier_decision
    assert refused.evidence == (retained.identity,) and len(refused.prerequisite_requirement_ids) == 2
    with pytest.raises(ValueError, match='available shared nomination'):
        prepare_environmental_frames(design=paired.design, frames=paired.frames, nomination=invalid)
    assert decode_canonical_bytes(stopped.canonical_bytes(), EnvironmentalPreparationResponseAssessment, maximum_bytes=16 * 2**20) == stopped
