# SPDX-License-Identifier: MPL-2.0
"""Pure whole-design controls; exposed mathematics supplies no input or authority."""
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal as D
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest


from empirical_lawhood.adapters.methods.matrix_researcher_programme import scientific_design as owner

from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixCouplingRecipe, original_schedule_recipe
from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import MatrixFunctionalCriterion
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import (
    SelectedPreparedDevelopmentSpecification, SelectedPreparedProtectedSpecification, SelectedPreparedRecipeFamily,
)
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_records import E1CompactCriterion, E1FamilySize
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1HistoryAllocation
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryTarget
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_records import NativeUtilityCriterion
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import E4_COMPARISONS, ScheduledFactorialComparison, mean_t_requirement
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionTarget, ScheduledRevisionTrigger, ScheduledRevisionTuning
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity, identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Design
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_choices import SelectedE4FactorialChoices
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4NominationRule
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selection_specification import RevisionCandidateSelection
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative

EXPERIMENTS = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows'
FAMILY = ('e1.recurrence-survival', 'e2.utility', 'e3.model', 'e4.aggregate-curvature',
    'e4.main.coupling', 'e4.main.friction', 'e4.main.temperature', 'e4.pair.friction-coupling',
    'e4.pair.temperature-coupling', 'e4.pair.temperature-friction', 'e4.revision-baseline',
    'e5.preparation', 'e6.nearby', 'e6.shifted')


def _read(name, kind):
    return decode_canonical_record(json.loads((EXPERIMENTS / name).read_text()), kind)


def _declared_pin(name, kind):
    """Disclosed software metadata only; never an allocation or recorded act."""
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


def build_scientific_design():
    """Full valid D with explicit exposed sizes and no assigned streams/results."""
    protocol = _read('matrix-response-experiment/native-training-scientific-protocol.example.json', NativeTrainingScientificProtocol)
    assay = _read('matrix-response-experiment/native-training-assay.example.json', ScheduledResponseAssay)
    original_e3 = _read('matrix-response-experiment/configured-protected-v2.json', ConfiguredProtectedE3Specification)
    nominal = next(co for co in protocol.coordinates if co.coordinate_id.endswith('nominal.coordinate'))
    roles = tuple((role, coordinate_identity(next(co for co in protocol.coordinates if
        co.coordinate_id.endswith('e6-nearby.coordinate' if role == 'TRANSFER_NEARBY' else
            'e6-shifted.coordinate' if role == 'TRANSFER_SHIFTED' else 'nominal.coordinate'))))
        for role, _ in original_e3.role_coordinates)
    e3 = replace(original_e3, populations=tuple(replace(row, expected_units=4, unit_ids=None)
        for row in original_e3.populations), role_coordinates=roles,
        assessment=replace(original_e3.assessment, comparison_ids=FAMILY, alpha_numerator=1,
            alpha_denominator=280, minimum_usable_units=1))
    policy = next(policy for policy in protocol.prefix_policies if
        identity(policy) == dict(protocol.coordinate_policies)[coordinate_identity(nominal)])
    utility = NativeUtilityCriterion('criterion.software.e2', 128,
        ('FULL_COUPLED', 'GENERIC_SLOW', 'NORM_RADIUS', 'SPECTRA'), D('.001'), D('.0001'), 1, 2, 1, 280, 1,
        'FACTOR', 'FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS',
        'SAME_CAUSAL_CUTOFF_STATE_PHYSICS_PRIMARY_FRAME_AND_ORIGIN_HESSIAN',
        'ZERO_FIT_ORIGIN_LINEARIZED_BAOAB_BOTH_FORCE_KICKS',
        (('FACTOR',48),('FULL_COUPLED',192),('GENERIC_SLOW',48),('NORM_RADIUS',24),('SPECTRA',48)), 0,
        'MAX_ALL_RECEIVERS_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT')
    e2 = owner.MatrixNativeUtilityDesign('design.software.e2', 4, protocol.mathematical_protocol,
        protocol.scalar_definition, (nominal,), protocol.numerical_design, (policy,),
        ((coordinate_identity(nominal), identity(policy)),), assay,
        replace(utility, minimum_usable_units=1, alpha_numerator=1, alpha_denominator=280))
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    e1_rule = replace(policy.factor_rule, spec_id='rule.software.whole-design.e1', sectors=('X', 'Y'),
        lattice=tuple(range(0, 1153, 16)), risk_start_tick=0)
    e1_coordinates = tuple(replace(nominal, coordinate_id='coordinate.software.e1.'+str(index), family_id=family,
        autonomous_ticks=896, observation_ticks=e1_rule.lattice) for index, family in enumerate(families))
    relation = ObjectIdentity('relation.software.e1', 'empirical-lawhood/kernel/relational-identity', '1.0.0', 'a'*64)
    e1 = E1CompactCriterion('criterion.software.e1', _declared_pin('allocation.software.not-issued.e1', E1HistoryAllocation),
        e1_rule.identity, 'system.software.e1', 'world.software.e1', relation, 'unit.software.whole-root',
        tuple(E1FamilySize(family, 1) for family in families),
        ('PRIMARY', 'FINE'), ('MOVING', 'ORIGIN_FIXED', 'BOTH'), 'INITIAL_PRESENCE_OR_FIRST_CAUSAL_ADMISSION', 1024, 128, 1, 160, 1024,
        'TWO_SIDED_EXACT_BINOMIAL_FEASIBLE_COMPLETION_ENVELOPE', 'EIGHT_PRIMARY_Y_CELLS_DIAGNOSTIC_MARGINAL_95_PERCENT')
    factors = tuple(ScheduledProgrammeFactor(name, 'LOG', D('.5'), D(1), D(2))
        for name in ('temperature', 'friction', 'coupling'))
    designs = tuple(SelectedE3E4Design('design.software.e4.'+role, 4, D('.95'), factors, 4)
        for role in ('development', 'calibration', 'confirmation'))
    target = ScheduledRevisionTarget('target.software.e4', protocol.mathematical_protocol.identity,
        protocol.mathematical_protocol.horizon_steps, ('PRIMARY', 'FINE'), 'CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15')
    factorial = SelectedE4FactorialChoices('factorial.software.e4', target,
        'MAX_PAIRED_CUMULATIVE_LOG1P_RESPONSE_ERROR_ALL15', PairInteractionScale.SIGNED_MEAN_DIFFERENCE,
        tuple(ScheduledFactorialComparison(name, PairedMeanTAlternative.TWO_SIDED_POINT_NULL, D(0), None)
            for name in E4_COMPARISONS), D('.05'), 'PAIRED_GROUP_MEAN_T', mean_t_requirement('requirement.software.e4'), (),
        'REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS', FAMILY)
    candidate_sets = []
    for group, features in (('revision', ('aggregate-curvature', 'coupling', 'friction', 'pair.friction-coupling',
            'pair.temperature-coupling', 'pair.temperature-friction', 'temperature')),
            ('baseline', ('coupling', 'friction', 'temperature'))):
        candidate_sets.append(tuple(RevisionCandidateSelection(group+'.software.'+str(index),
            ScheduledRevisionTuning('tuning.'+group+'.'+str(index), 'physical-grid-standardized-ridge', features,
                penalty, False, len(features)+1)) for index, penalty in enumerate((D(1), D(10)))))
    revision = owner.MatrixE4RevisionChoices('revision.software.e4', target,
        ScheduledRevisionTrigger('trigger.software.e4', 'MEAN_COMPLETE_GROUP_MAX_PAIRED_LOG_ERROR', 'GREATER_THAN', D('.1')),
        tuple((family, 0, index % 2) for index, family in enumerate(families)), 2, 5, *candidate_sets,
        *(tuple(candidate.candidate_id for candidate in candidates) for candidates in candidate_sets),
        'COMMITTED_PHYSICAL_VALUES_SIGNED_GRID_PAIRS_ONE_CENTER_INDICATOR', 'MINIMIZE', 'REQUIRE_COMPLETE')
    nomination = SelectedE4NominationRule('nomination-rule.software.e4', ('REVISION', 'ORIGINAL_E3'), D(0), 3, 3, D(1),
        ('e4.revision-baseline',), 'WHOLE_GROUP_MAX_ABSOLUTE_PAIRED_LOG_PREDICTION_LOSS_NINE_COORDINATES_ALL30', 4,
        PairedMeanTAlternative.LESS)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import selected_structural_prediction
    structure = owner.MatrixE4StructuralChoices('structure.software.e4', protocol.full_factor_rule,
        policy.factor_numerical_design, ('PRIMARY', 'FINE'),
        'COMPLETE_ORIGINAL_LATTICE_ASSOCIATIVE_LIE_FACTOR_TRANSPORT_ORIGIN_FIXED_SCALAR_CONTRAST',
        'ORIGINAL_MATCHED_GROUPS_COORDINATES_VIEWS_SECTORS_AND_TICKS_ARE_NESTED',
        MatrixE4SecondaryTarget('secondary.software.e4.explicit', protocol.mathematical_protocol, D('.01'),
            (D('.005'),D('.02'),D('.05')),tuple(range(16,129,4)),D('.001')),
        selected_structural_prediction('prediction.software.e4'))
    baseline = original_schedule_recipe(nominal, 256, recipe_id='recipe.software.baseline', effort_unit='effort.declared-coupling-integral')
    recipes = (('baseline', baseline), *tuple((arm, MatrixCouplingRecipe('recipe.software.'+arm, 'FIXED_COUPLING',
        baseline.primary_steps, tuple(baseline.half_tick_couplings[min(2*j,512) if arm=='early' else max(2*j-512,0)]
            for j in range(513)), baseline.effort_rule, baseline.effort_unit, baseline.applicability)) for arm in ('delayed', 'early')))
    criterion = MatrixFunctionalCriterion('FACTOR', 128, D('.01'), D('.0001'), 1, 1, 0, 1, 2, 1, 280,
        FAMILY, (), baseline.effort_unit, 1, 20, 'BONFERRONI_FIXED_FULL_PRIMARY_FAMILY', 'EXACT_BINOMIAL_ALL_ASSIGNED_GROUPS',
        'RETAIN_ALL_ASSIGNED_GROUPS_AS_NONSUCCESS')
    development = SelectedPreparedDevelopmentSpecification('specification.software.e5.dev', 'ORIGINAL_E3',
        'E5_OPPORTUNITY', 2, recipes, criterion, 1, 'MINIMUM_TOTAL_EFFORT_THEN_LEXICAL', ())
    confirmation = owner.MatrixE5ConfirmationChoices('confirmation.software.e5', 4, criterion, 'baseline', ('delayed', 'early'),
        'BASELINE_AND_AUTHENTICATED_DEV_WINNER_FROM_FROZEN_MENU_UNCHANGED_CRITERION', 'NO_NOMINATION_NO_CONFIRMATION_ENTRY')
    transfer = SelectedPreparedProtectedSpecification('specification.software.e6', 'ORIGINAL_E3', 'E6_TRANSFER', 4,
        (recipes[0],), criterion, None, None, ('EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN',)*2)
    prepared = owner.MatrixPreparedAssayMethod.from_assay('assay.software.prepared', assay)
    panels = owner.MatrixPreparedPanelChoices('panels.software.rules', ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE'),
        owner.HISTORY_PURPOSES, 'ORIGINAL_ROOT_PURPOSE_STREAMS', 'SEPARATE_DECLARED_WHOLE_GROUP_FUTURE_STREAMS',
        'SAME_PANELS_ALL_MATCHED_ARMS', 'EXACT_ORIGINAL_PRETRAIN_TRANSFER_SELECTORS', 'SUPPLIED_FUTURE_INNOVATIONS_NO_CHECKPOINT_AUTHORITY')
    e6_policy = owner.MatrixE6PolicyChoices('policy.software.e6', criterion,
        tuple((description,horizon) for description in e3.measurement.descriptions for horizon in e3.measurement.horizons),
        e3.calibration_alpha, owner.CALIBRATION_METHOD, owner.POINT_TRANSFORM,
        'FINITE_ORIGINAL_Q_USABLE_CAUSAL_FEATURE_AND_PRIMARY_UPPER_AT_MOST_FROZEN_TOLERANCE',
        'ALL_ASSIGNED_NONSUCCESS_AND_ADMITTED_UNRESOLVED_FALSE_ADMISSION_WORST_CASE',
        ('ALL_ORIGIN_RIDGE', 'RAW_TRAIN_MEDIAN'), owner.STANDING)
    e3_calibration = ScheduledCalibrationCriterion('criterion.software.original-cal', 'unit.software.cal-root', 4,
        D(1), (nominal.family_id,), 'COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY')
    e4_calibration = replace(e3_calibration, criterion_id='criterion.software.e4-cal', required_family_ids=families)
    return owner.MatrixProgrammeScientificDesign(record_id='design.software.complete', downstream_account='ORIGINAL_E3',
        e1_factor_rule=e1_rule, e1_criterion=e1, e1_numerical_design=protocol.numerical_design,
        e1_factor_numerical_design=policy.factor_numerical_design, e1_scalar_definition=protocol.scalar_definition,
        e1_coordinates=e1_coordinates, e2=e2, training_protocol=protocol, training_assay=assay,
        e3_calibration_criterion=e3_calibration, e3=e3,
        e4_development=designs[0], e4_calibration=designs[1], e4_confirmation=designs[2],
        e4_preparation_coordinates=tuple(replace(nominal, coordinate_id='coordinate.software.e4.'+str(index), family_id=family)
            for index, family in enumerate(families)), e4_calibration_criterion=e4_calibration, e4_calibration_alpha=D('.05'),
        e4_factorial=factorial, e4_revision=revision, e4_nomination=nomination, e4_structure=structure,
        e5_development=development, e5_confirmation=confirmation, prepared_assay=prepared,
        recipe_interpretations=tuple(SelectedPreparedRecipeFamily(arm, 'cc1.history.de-anneal', recipe.identity) for arm,recipe in recipes),
        panel_choices=panels, e6=transfer, e6_policy=e6_policy)


@pytest.fixture
def scientific_design():
    return build_scientific_design()


@pytest.fixture
def matched_scientific_design():
    """Generated public mathematics with disclosed streams, not fresh science."""
    return _read('matrix-programme/scientific-design.example.json', owner.MatrixProgrammeScientificDesign)


def test_amended_public_design_retains_exact_complete_counts_and_temperature_slice(matched_scientific_design):
    from empirical_lawhood.api.configuration import validate_configuration
    from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
    from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel
    design = matched_scientific_design
    assert validate_configuration(EXPERIMENTS / 'matrix-programme/scientific-design.example.json',
        consumer='matrix-programme-scientific-design')['status'] == 'VALIDATED'
    assert decode_canonical_bytes(design.canonical_bytes(), type(design), maximum_bytes=None) == design
    counts = dict(design.phase_group_counts)
    assert counts == {'e1': 384, 'e2': 96, 'train': 64, 'e3.calibration': 64, 'e3.confirmation': 80,
        'e4.development': 16, 'e4.calibration': 20, 'e4.confirmation': 32,
        'e5.development': 16, 'e5.confirmation': 80, 'e6.nearby': 64, 'e6.shifted': 64}
    assert sum(counts.values()) == 980
    assert sum(count * (9 if role.startswith('e4.') else 3 if role == 'e5.development' else
        2 if role == 'e5.confirmation' else 1) for role, count in counts.items()) == 1636
    assert design.downstream_account == 'REVISION' and design.e3.assessment.comparison_ids == AMENDED_PRIMARY_FAMILY
    assert type(design.e2.assay.mechanical_model) is MatrixOriginResponseModel
    assert design.e2.assay == design.training_assay
    assert design.training_assay.horizon_steps == tuple(range(16, 129, 4))
    assert design.e6_policy.endpoint_order == tuple(('FACTOR', tick) for tick in range(16, 129, 4))
    assert design.e3_calibration_criterion.construction_estimand == 'WHOLE_ROOT_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_FACTOR58_NONUSE_INFINITY'
    assert design.e4_calibration_criterion.required_family_ids == ()
    assert design.e4_revision.trigger is None and not design.e4_factorial.comparisons
    assert tuple(row.family_sampling_rule for row in (design.e4_calibration, design.e4_confirmation)) == (
        'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW',) * 2
    coordinates = {coordinate_identity(co): co for co in design.training_protocol.coordinates}
    roles = dict(design.e3.role_coordinates)
    assert tuple(coordinates[roles[role]].primary_view.bath_temperature for role in (
        'TRAIN', 'TRANSFER_NEARBY', 'TRANSFER_SHIFTED')) == (D(1), D('1.125'), D('3.25'))


@pytest.mark.parametrize('damage', ('old-calibration', 'old-utility', 'nominal-grid', 'old-temperature', 'changed-friction', 'stale-version'))
def test_amended_design_refuses_valid_but_inconsistent_phase_science(matched_scientific_design, scientific_design, damage):
    design = matched_scientific_design
    with pytest.raises((ValueError, TypeError)):
        if damage == 'old-calibration':
            replace(design, e3_calibration_criterion=replace(design.e3_calibration_criterion,
                construction_estimand='COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY'))
        elif damage == 'old-utility':
            replace(design, e2=scientific_design.e2)
        elif damage == 'nominal-grid':
            factors = tuple(replace(factor, low=factor.low*2, center=factor.center*2, high=factor.high*2)
                for factor in design.e4_development.factors)
            replace(design, **{field: replace(getattr(design, field), factors=factors)
                for field in ('e4_development', 'e4_calibration', 'e4_confirmation')})
        elif damage in ('old-temperature', 'changed-friction'):
            pin = dict(design.e3.role_coordinates)['TRANSFER_NEARBY']
            old = next(co for co in design.training_protocol.coordinates if coordinate_identity(co) == pin)
            field, value = ('bath_temperature', D('1.25')) if damage == 'old-temperature' else ('friction_gamma', D(2))
            new = replace(old, primary_view=replace(old.primary_view, **{field: value}), fine_view=replace(old.fine_view, **{field: value}))
            protocol = replace(design.training_protocol,
                coordinates=tuple(new if co == old else co for co in design.training_protocol.coordinates),
                coordinate_policies=tuple((coordinate_identity(new) if co == pin else co, policy)
                    for co, policy in design.training_protocol.coordinate_policies))
            e3 = replace(design.e3, role_coordinates=tuple((role, coordinate_identity(new) if co == pin else co)
                for role, co in design.e3.role_coordinates))
            replace(design, training_protocol=protocol, e3=e3)
        else:
            document = design.to_document()
            document['version'] = '2.0.0'
            owner.MatrixProgrammeScientificDesign.from_document(document)


def test_complete_pure_design_roundtrip_and_scoped_multiplicity(scientific_design):
    design = scientific_design
    assert owner.MatrixProgrammeScientificDesign.from_document(design.to_document()) == design
    assert decode_canonical_bytes(design.canonical_bytes(), type(design), maximum_bytes=None) == design
    assert design.identity == ObjectIdentity.from_record(design.record_id, design)
    assert design.e1_criterion.cell_alpha(design.e1_factor_rule) == Fraction(1,1280)
    assert design.e4_factorial.alpha == D('.05') > design.e5_development.criterion.alpha
    assert design.e5_confirmation.criterion.alpha == Fraction(1,280)
    assert len(design.e4_factorial.family_ids) == 14
    assert len(design.phase_group_counts) == 12
    assert dict(design.phase_group_counts) == {'e1':4,'e2':4,'train':4,'e3.calibration':4,'e3.confirmation':4,
        'e4.development':4,'e4.calibration':4,'e4.confirmation':4,'e5.development':2,'e5.confirmation':4,'e6.nearby':4,'e6.shifted':4}
    assert design.e1_family_counts == tuple((family,1) for family in sorted(FOUR_FAMILY_PREPARATION_IDS))
    with pytest.raises(FrozenInstanceError):
        design.record_id = 'edited.design'


@pytest.mark.parametrize('field', ('active_slot','future_reservation','publications','fitted_model','nomination','panels','group_seeds'))
def test_design_rejects_operational_and_produced_fields(scientific_design, field):
    document = scientific_design.to_document()
    document['value'][field] = None
    with pytest.raises(ValueError):
        owner.MatrixProgrammeScientificDesign.from_document(document)


@pytest.mark.parametrize('field', ('training_assay','e3_calibration_criterion','e4_structure','e5_confirmation','panel_choices','e6_policy'))
def test_design_has_no_missing_scientific_defaults(scientific_design, field):
    document = scientific_design.to_document()
    del document['value'][field]
    with pytest.raises(ValueError):
        owner.MatrixProgrammeScientificDesign.from_document(document)


@pytest.mark.parametrize('damage', ('e1-clock','e1-physics','e2-scalar','e2-action-scale','training-action-scale',
    'role-coordinate','calibration-family','calibration-count','e4-denominator',
    'fold-roster','factorial-family','target','structure-rule','secondary-math','confirmation-criterion',
    'nominee-menu','assay','prepared-actuator','interpretations','interpretation-premise',
    'transfer-count','transfer-criterion','transport-endpoints','account'))
def test_independent_phase_joins_refuse_valid_but_foreign_mathematics(scientific_design, damage):
    d = scientific_design
    with pytest.raises((ValueError,TypeError)):
        if damage=='e1-clock':
            replace(d,e1_coordinates=(replace(d.e1_coordinates[0],observation_ticks=d.e1_coordinates[0].observation_ticks[:-1]),*d.e1_coordinates[1:]))
        elif damage=='e1-physics':
            co=d.e1_coordinates[0]
            replace(d,e1_coordinates=(replace(co,target_x=co.target_x+D('.1')),*d.e1_coordinates[1:]))
        elif damage=='e2-scalar':
            replace(d,e2=replace(d.e2,scalar_definition=replace(d.e2.scalar_definition,definition_id='foreign.scalar')))
        elif damage=='e2-action-scale':
            assay=d.e2.assay
            replace(d,e2=replace(d.e2,assay=replace(assay,actions=(replace(assay.actions[0],amplitude=D('.02')),*assay.actions[1:]))))
        elif damage=='training-action-scale':
            assay=d.training_assay
            replace(d,training_assay=replace(assay,actions=(replace(assay.actions[0],amplitude=D('.02')),*assay.actions[1:])))
        elif damage=='role-coordinate':
            replace(d,e3=replace(d.e3,role_coordinates=tuple((role,coordinate_identity(d.training_protocol.coordinates[0])) for role,_ in d.e3.role_coordinates)))
        elif damage=='calibration-family':
            replace(d,e3_calibration_criterion=replace(d.e3_calibration_criterion,required_family_ids=('matrix-history.joint-increasing-coupling',)))
        elif damage=='calibration-count':
            replace(d,e3_calibration_criterion=replace(d.e3_calibration_criterion,minimum_group_count=3))
        elif damage=='e4-denominator':
            replace(d,e4_confirmation=replace(d.e4_confirmation,group_count=8))
        elif damage=='fold-roster':
            replace(d,e4_revision=replace(d.e4_revision,fold_slots=d.e4_revision.fold_slots[:-1]))
        elif damage=='factorial-family':
            replace(d,e4_factorial=replace(d.e4_factorial,family_ids=tuple(sorted((*d.e4_factorial.family_ids,'extra.claim')))))
        elif damage=='target':
            target=replace(d.e4_factorial.target,target_id='foreign.target')
            replace(d,e4_factorial=replace(d.e4_factorial,target=target))
        elif damage=='structure-rule':
            replace(d,e4_structure=replace(d.e4_structure,factor_rule=replace(d.e4_structure.factor_rule,spec_id='foreign.rule')))
        elif damage=='secondary-math':
            target=replace(d.e4_structure.secondary_target,mathematical_protocol=replace(d.training_protocol.mathematical_protocol,protocol_id='foreign.math'))
            replace(d,e4_structure=replace(d.e4_structure,secondary_target=target))
        elif damage=='confirmation-criterion':
            replace(d,e5_confirmation=replace(d.e5_confirmation,criterion=replace(d.e5_confirmation.criterion,normalized_error_maximum=D('.02'))))
        elif damage=='nominee-menu':
            replace(d,e5_confirmation=replace(d.e5_confirmation,eligible_nominee_arm_ids=('early',)))
        elif damage=='assay':
            replace(d,prepared_assay=replace(d.prepared_assay,criterion=replace(d.prepared_assay.criterion,object_fingerprint='f'*64)))
        elif damage=='prepared-actuator':
            assay=d.prepared_assay
            replace(d,prepared_assay=replace(assay,actions=(replace(assay.actions[0],amplitude=D('.02')),*assay.actions[1:])))
        elif damage=='interpretations':
            replace(d,recipe_interpretations=d.recipe_interpretations[:-1])
        elif damage=='interpretation-premise':
            first=d.recipe_interpretations[0]
            replace(d,recipe_interpretations=(replace(first,scientific_premise=d.recipe_interpretations[1].scientific_premise),*d.recipe_interpretations[1:]))
        elif damage=='transfer-count':
            replace(d,e6=replace(d.e6,expected_groups=8))
        elif damage=='transfer-criterion':
            replace(d,e6_policy=replace(d.e6_policy,criterion=replace(d.e6_policy.criterion,normalized_error_maximum=D('.02'))))
        elif damage=='transport-endpoints':
            replace(d,e6_policy=replace(d.e6_policy,endpoint_order=d.e6_policy.endpoint_order[:-1]))
        else:
            replace(d,downstream_account='REVISION')


def test_required_secondary_target_is_explicit_and_not_defaulted(scientific_design):
    design = scientific_design
    assert design.e4_structure.secondary_target.normalized_adequacy_tolerance == D('.01')
    with pytest.raises(TypeError):
        replace(design.e4_structure, secondary_target=None)
    with pytest.raises(ValueError):
        replace(design.e4_structure.secondary_target, normalized_adequacy_tolerance=D(0))


@pytest.mark.parametrize('field', (
    'template-artifact', 'template-member', 'mechanical-model',
    'hessian_difference_step', 'generic_gap_minimum', 'spectral_gap_minimum',
    'radial_norm_minimum', 'complement_gram_minimum', 'native_reference_tolerance',
    'hessian_reference_tolerance', 'weak_response_minimum', 'receiver_gram_tolerance',
))
def test_prepared_assay_refuses_an_independently_valid_foreign_instrument(scientific_design, field):
    design = scientific_design
    assay = design.prepared_assay
    if field == 'template-artifact':
        foreign = replace(assay, template_artifact=replace(assay.template_artifact, sha256='f'*64))
    elif field == 'template-member':
        foreign = replace(assay, template_members=(replace(assay.template_members[0], sha256='f'*64),
            *assay.template_members[1:]))
    elif field == 'mechanical-model':
        foreign = replace(assay, mechanical_model=replace(assay.mechanical_model, model_id='model.foreign'))
    else:
        foreign = replace(assay, **{field: getattr(assay, field)+D('.00001')})
    foreign.__post_init__()
    assert foreign != assay
    with pytest.raises(ValueError, match='assay|receiver metric'):
        replace(design, prepared_assay=foreign)


def test_prepared_assay_projection_preserves_the_complete_source_independent_instrument(scientific_design):
    assay, prepared = scientific_design.training_assay, scientific_design.prepared_assay
    assert prepared.criterion == assay.criterion
    assert prepared.mechanical_model == assay.mechanical_model
    assert prepared.actions == assay.actions
    assert prepared.horizon_steps == assay.horizon_steps
    assert prepared.receiver_count == assay.receiver_count
    assert prepared.template_artifact == assay.array_artifact
    assert prepared.template_members == assay.members
    assert (prepared.hessian_difference_step, prepared.generic_gap_minimum, prepared.spectral_gap_minimum,
        prepared.radial_norm_minimum, prepared.complement_gram_minimum, prepared.native_reference_tolerance,
        prepared.hessian_reference_tolerance, prepared.weak_response_minimum, prepared.receiver_gram_tolerance,
        prepared.origin_rule) == (assay.hessian_difference_step, assay.generic_gap_minimum, assay.spectral_gap_minimum,
        assay.radial_norm_minimum, assay.complement_gram_minimum, assay.native_reference_tolerance,
        assay.hessian_reference_tolerance, assay.weak_response_minimum, assay.receiver_gram_tolerance, assay.origin_rule)
    with pytest.raises(TypeError, match='source-independent'):
        owner.MatrixPreparedAssayMethod.from_assay('assay.refused', prepared)


def test_recipe_menu_preserves_every_original_early_and_delayed_pair(scientific_design):
    arms = dict(scientific_design.e5_development.arms)
    baseline = arms['baseline'].half_tick_couplings
    assert len(baseline) == len(arms['early'].half_tick_couplings) == len(arms['delayed'].half_tick_couplings) == 513
    assert arms['early'].half_tick_couplings == tuple(baseline[min(2*j,512)] for j in range(513))
    assert arms['delayed'].half_tick_couplings == tuple(baseline[max(2*j-512,0)] for j in range(513))
    assert {recipe.effort for recipe in arms.values()} == {D(8)}


def test_design_imports_no_api_old_preparation_or_commitment_owner():
    # A new interpreter observes the actual import closure independently of
    # other tests that legitimately import API owners in the parent process.
    script = '''
import importlib
import importlib.abc
import sys

def forbidden(name):
    return name.startswith('empirical_lawhood.api') or name.endswith((
        '.selected_declarative_preparation', '.selected_e4_declarative',
        '.selected_original_commitments', '.native_training_initialization',
        '.preparation_initialization'))

attempts = []
class PureImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if forbidden(fullname):
            attempts.append(fullname)
            raise AssertionError('pure design imported operational owner ' + fullname)

assert not any(forbidden(name) for name in sys.modules)
guard = PureImports()
sys.meta_path.insert(0, guard)
try:
    from empirical_lawhood.adapters.methods.matrix_researcher_programme import scientific_design
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedDevelopmentSpecification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_choices import SelectedE4FactorialChoices
    assert scientific_design.MatrixProgrammeScientificDesign.VERSION == '3.0.0'
    assert SelectedPreparedDevelopmentSpecification.__module__.endswith('.selected_prepared_choices')
    assert SelectedE4FactorialChoices.__module__.endswith('.selected_e4_choices')
    assert not attempts
    assert not any(forbidden(name) for name in sys.modules)
    # Prove the installed guard refuses an actual operational import.
    try:
        importlib.import_module('empirical_lawhood.api')
    except AssertionError as error:
        assert str(error) == 'pure design imported operational owner empirical_lawhood.api'
    else:
        raise AssertionError('operational import guard did not execute')
    assert attempts == ['empirical_lawhood.api']
finally:
    sys.meta_path.remove(guard)
print('pure scientific-design import closure verified')
'''
    result = subprocess.run((sys.executable, '-B', '-c', script),
        cwd=Path(__file__).parents[1], capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'pure scientific-design import closure verified'
