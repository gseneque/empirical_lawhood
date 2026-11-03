# SPDX-License-Identifier: MPL-2.0
"""Immutable Matrix mathematics, separate from inputs, products and permission.

No assigned streams, publications, fitted coefficients, outcome records or
operational phase selection belong here. Existing scientific owners retain
their exact bodies and scoped statistical procedures. A design is neither an
input commitment nor a qualification or execution act.
"""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import (
    CALIBRATION_METHOD, POINT_TRANSFORM, STANDING, MATCHED_CALIBRATION_METHOD, MATCHED_ADMISSION_RULE, MATCHED_METHODS, MATCHED_STANDING,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import (
    MatrixOriginalScheduleRecipe, validate_original_schedule_recipe,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import MatrixFunctionalCriterion
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import (
    SelectedPreparedDevelopmentSpecification, SelectedPreparedProtectedSpecification, SelectedPreparedRecipeFamily,
)
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_records import E1CompactCriterion
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryTarget
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_records import NativeAmendedUtilityCriterion, NativeUtilityCriterion
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorNumericalDesign, MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionTarget, ScheduledRevisionTrigger
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixPolicy, coordinate_identity, identity, matched_key, physical_key
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import (
    SelectedE3E4Design, selected_original_factor_rule, validate_selected_prefix_projection,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_choices import SelectedE4FactorialChoices
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4NominationRule, SelectedE4MatchedRelationRule
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selection_specification import RevisionCandidateSelection
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.decoding import decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import (
    E4StructuralPredictionSelection, E4MatchedRelationSelection, E4MatchedRelationTarget,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id


def _exact(value, kind):
    kinds = kind if type(kind) is tuple else (kind,)
    if type(value) not in kinds:
        raise TypeError('programme mathematics requires exact ' + '/'.join(row.__name__ for row in kinds))
    value.__post_init__()


def _records(values, kind, attribute):
    if type(values) is not tuple or not values:
        raise TypeError('programme mathematics requires a nonempty immutable ' + attribute + ' roster')
    for value in values:
        _exact(value, kind)
    require_sorted_unique_ids(values, attribute=attribute, field_name=attribute)


def _positive_count(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(name + ' requires an explicit positive integer')


def _scalar(rule, definition):
    closure = rule.scalar_closure
    if closure is None or closure.threshold != definition.threshold:
        raise ValueError('programme mathematics changes its explicit scalar threshold')
    owner = closure.normalization_owner
    if (owner.payload_schema, owner.sha256, owner.size_bytes, owner.media_type) != (
            definition.SCHEMA, definition.fingerprint(), len(definition.canonical_bytes()), 'application/json'):
        raise ValueError('programme mathematics changes its exact typed scalar normalization')


def _assay_math(assay, protocol):
    if (assay.criterion != protocol.identity or assay.horizon_steps != protocol.horizon_steps
            or tuple(sorted((action.role, action.amplitude, action.pulse_steps, action.force_norm) for action in assay.actions))
                != tuple(sorted((action.role, action.amplitude, action.pulse_steps, action.force_norm) for action in protocol.action_scales))
            or assay.receiver_gram_tolerance != protocol.receiver_gram_tolerance):
        raise ValueError('response assay changes its exact criterion, actuator scales, horizons or receiver metric')


def _coordinate_physics(coordinate):
    return (coordinate.member, coordinate.primary_view, coordinate.fine_view, coordinate.target_x, coordinate.target_y,
        coordinate.decreasing_start, coordinate.ramp_ticks, coordinate.autonomous_ticks, coordinate.observation_ticks,
        coordinate.initial_state_rule_id, coordinate.preparation_rule_id)


class _DesignIdentity:
    __slots__ = ()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixNativeUtilityDesign(_DesignIdentity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/native-utility-design'
    record_id: str
    expected_units: int
    mathematical_protocol: MatrixResponseFrontierProtocol
    scalar_definition: MatrixParameterScalarDefinition
    coordinates: tuple[MatrixParameterCoordinate, ...]
    numerical_design: MatrixParameterNumericalDesign
    prefix_policies: tuple[ScheduledPrefixPolicy, ...]
    coordinate_policies: tuple[tuple[ObjectIdentity, ObjectIdentity], ...]
    assay: ScheduledResponseAssay
    criterion: NativeUtilityCriterion | NativeAmendedUtilityCriterion

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _positive_count(self.expected_units, 'native utility denominator')
        for value, kind in ((self.mathematical_protocol, MatrixResponseFrontierProtocol),
                (self.scalar_definition, MatrixParameterScalarDefinition),
                (self.numerical_design, MatrixParameterNumericalDesign), (self.assay, ScheduledResponseAssay)):
            _exact(value, kind)
        if type(self.criterion) not in (NativeUtilityCriterion, NativeAmendedUtilityCriterion):
            raise TypeError('native utility design requires its exact selected scientific questions')
        self.criterion.__post_init__()
        if (type(self.criterion) is NativeAmendedUtilityCriterion) != (type(self.assay.mechanical_model) is MatrixOriginResponseModel):
            raise ValueError('native utility design substitutes the model menu bound to its old or amended questions')
        _records(self.coordinates, MatrixParameterCoordinate, 'coordinate_id')
        _records(self.prefix_policies, ScheduledPrefixPolicy, 'policy_id')
        _assay_math(self.assay, self.mathematical_protocol)
        if (type(self.coordinate_policies) is not tuple
                or any(type(row) is not tuple or len(row) != 2 or any(type(pin) is not ObjectIdentity for pin in row)
                    for row in self.coordinate_policies)
                or tuple(co.object_id for co, _ in self.coordinate_policies) != tuple(co.coordinate_id for co in self.coordinates)
                or {co for co, _ in self.coordinate_policies} != {coordinate_identity(co) for co in self.coordinates}
                or {policy for _, policy in self.coordinate_policies} != {identity(policy) for policy in self.prefix_policies}):
            raise ValueError('native utility design omits exact coordinate/prefix coverage')
        if (self.assay.criterion != self.mathematical_protocol.identity
                or self.assay.horizon_steps != self.mathematical_protocol.horizon_steps
                or self.criterion.primary_horizon not in self.assay.horizon_steps
                or self.criterion.minimum_usable_units > self.expected_units):
            raise ValueError('native utility design changes its complete assay, endpoint or denominator')
        by_policy = {identity(policy): policy for policy in self.prefix_policies}
        for coordinate, (_, policy_pin) in zip(self.coordinates, self.coordinate_policies, strict=True):
            policy = by_policy[policy_pin]
            _scalar(policy.factor_rule, self.scalar_definition)
            validate_selected_prefix_projection(self.mathematical_protocol, policy, policy.cutoff_tick)
            if (coordinate.primary_view.timestep != self.mathematical_protocol.primary_timestep
                    or policy.cutoff_tick not in coordinate.observation_ticks
                    or coordinate.observation_ticks[-1] < policy.cutoff_tick + max(self.assay.horizon_steps)):
                raise ValueError('native utility design changes its paired cutoff or complete horizon geometry')


@dataclass(frozen=True, slots=True)
class MatrixE4RevisionChoices(_DesignIdentity, CanonicalRecord):
    """Whole-family fold slots precede their concrete independent-group binding."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e4-revision-choices'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    target: ScheduledRevisionTarget | E4MatchedRelationTarget
    trigger: ScheduledRevisionTrigger | None
    fold_slots: tuple[tuple[str, int, int], ...]
    fold_count: int
    maximum_fit_calls: int
    revision_candidates: tuple[RevisionCandidateSelection, ...]
    baseline_candidates: tuple[RevisionCandidateSelection, ...]
    revision_tie_order: tuple[str, ...]
    baseline_tie_order: tuple[str, ...]
    feature_rule: str
    score_direction: str
    missing_policy: str
    matched_selection: E4MatchedRelationSelection | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        matched = self.matched_selection is not None
        _exact(self.target, E4MatchedRelationTarget if matched else ScheduledRevisionTarget)
        if matched:
            _exact(self.matched_selection, E4MatchedRelationSelection)
            if (self.trigger is not None or (self.fold_count, self.maximum_fit_calls) != (2, 5)
                    or any((self.revision_candidates, self.baseline_candidates, self.revision_tie_order, self.baseline_tie_order))):
                raise ValueError('matched relation choices cannot add an inadequacy trigger or alternate model search')
        else:
            _exact(self.trigger, ScheduledRevisionTrigger)
        _positive_count(self.maximum_fit_calls, 'revision fitting budget')
        if (type(self.fold_count) is not int or self.fold_count < 2
                or type(self.fold_slots) is not tuple or not self.fold_slots
                or any(type(row) is not tuple or len(row) != 3 or type(row[0]) is not str
                    or type(row[1]) is not int or row[1] < 0 or type(row[2]) is not int
                    or not 0 <= row[2] < self.fold_count for row in self.fold_slots)
                or tuple((family, ordinal) for family, ordinal, _ in self.fold_slots)
                    != tuple(sorted({(family, ordinal) for family, ordinal, _ in self.fold_slots}))
                or {fold for _, _, fold in self.fold_slots} != set(range(self.fold_count))
                or self.feature_rule != (self.matched_selection.feature_rule if matched else 'COMMITTED_PHYSICAL_VALUES_SIGNED_GRID_PAIRS_ONE_CENTER_INDICATOR')
                or self.score_direction != 'MINIMIZE'
                or self.missing_policy != (self.matched_selection.missing_policy if matched else 'REQUIRE_COMPLETE')):
            raise ValueError('revision choices change explicit whole-group folds, features or complete scoring')
        if matched:
            return
        all_ids, tunings = set(), {}
        for candidates, ties in ((self.revision_candidates, self.revision_tie_order),
                (self.baseline_candidates, self.baseline_tie_order)):
            _records(candidates, RevisionCandidateSelection, 'candidate_id')
            if (type(ties) is not tuple or len(ties) != len(candidates)
                    or set(ties) != {candidate.candidate_id for candidate in candidates}):
                raise ValueError('revision choices omit an exact candidate tie order')
            for candidate in candidates:
                if candidate.candidate_id in all_ids:
                    raise ValueError('revision and baseline candidates must remain distinct')
                all_ids.add(candidate.candidate_id)
                tuning = candidate.tuning
                if tunings.setdefault(tuning.tuning_id, tuning) != tuning:
                    raise ValueError('revision choices alias different tuning bodies')
        if len(self.revision_candidates) != len(self.baseline_candidates):
            raise ValueError('revision and baseline retain comparable candidate budgets')


@dataclass(frozen=True, slots=True)
class MatrixE4StructuralChoices(_DesignIdentity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e4-structural-choices'
    VERSION: ClassVar[str] = '4.0.0'
    record_id: str
    factor_rule: FactorEventSpec
    numerical_design: MatrixParameterFactorNumericalDesign
    views: tuple[str, ...]
    measurement: str
    independence: str
    secondary_target: MatrixE4SecondaryTarget
    prediction: E4StructuralPredictionSelection | E4MatchedRelationSelection

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _exact(self.factor_rule, FactorEventSpec)
        _exact(self.numerical_design, MatrixParameterFactorNumericalDesign)
        _exact(self.secondary_target, MatrixE4SecondaryTarget)
        _exact(self.prediction, (E4StructuralPredictionSelection, E4MatchedRelationSelection))
        if (self.views != ('PRIMARY', 'FINE')
                or self.measurement != 'COMPLETE_ORIGINAL_LATTICE_ASSOCIATIVE_LIE_FACTOR_TRANSPORT_ORIGIN_FIXED_SCALAR_CONTRAST'
                or self.independence != 'ORIGINAL_MATCHED_GROUPS_COORDINATES_VIEWS_SECTORS_AND_TICKS_ARE_NESTED'):
            raise ValueError('structural choices change the complete original measurement or nested denominator')


@dataclass(frozen=True, slots=True)
class MatrixE5ConfirmationChoices(_DesignIdentity, CanonicalRecord):
    """Freeze the construction rule; the actual winning recipe does not exist yet."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e5-confirmation-choices'
    record_id: str
    expected_groups: int
    criterion: MatrixFunctionalCriterion
    baseline_arm_id: str
    eligible_nominee_arm_ids: tuple[str, ...]
    construction_rule: str
    no_nomination_rule: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.baseline_arm_id)
        _positive_count(self.expected_groups, 'preparation confirmation denominator')
        _exact(self.criterion, MatrixFunctionalCriterion)
        if (type(self.eligible_nominee_arm_ids) is not tuple or not self.eligible_nominee_arm_ids
                or self.eligible_nominee_arm_ids != tuple(sorted(set(self.eligible_nominee_arm_ids)))
                or self.baseline_arm_id in self.eligible_nominee_arm_ids
                or self.construction_rule != 'BASELINE_AND_AUTHENTICATED_DEV_WINNER_FROM_FROZEN_MENU_UNCHANGED_CRITERION'
                or self.no_nomination_rule != 'NO_NOMINATION_NO_CONFIRMATION_ENTRY'
                or max(self.criterion.minimum_usable_groups, self.criterion.minimum_admitted_groups) > self.expected_groups):
            raise ValueError('confirmation choices invent a nominee, thin its menu or change complete criterion scope')
        for arm in self.eligible_nominee_arm_ids:
            validate_stable_id(arm)


@dataclass(frozen=True, slots=True)
class MatrixPreparedPanelChoices(_DesignIdentity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/prepared-panel-choices'
    record_id: str
    panel_roles: tuple[str, ...]
    stream_purposes: tuple[str, ...]
    common_noise_rule: str
    independent_future_rule: str
    matched_arm_sharing_rule: str
    e6_panel_rule: str
    innovation_scope: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.panel_roles != ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                or self.stream_purposes != HISTORY_PURPOSES
                or self.common_noise_rule != 'ORIGINAL_ROOT_PURPOSE_STREAMS'
                or self.independent_future_rule != 'SEPARATE_DECLARED_WHOLE_GROUP_FUTURE_STREAMS'
                or self.matched_arm_sharing_rule != 'SAME_PANELS_ALL_MATCHED_ARMS'
                or self.e6_panel_rule != 'EXACT_ORIGINAL_PRETRAIN_TRANSFER_SELECTORS'
                or self.innovation_scope != 'SUPPLIED_FUTURE_INNOVATIONS_NO_CHECKPOINT_AUTHORITY'):
            raise ValueError('prepared panel choices change original purpose streams or matched counterfactual sharing')


@dataclass(frozen=True, slots=True)
class MatrixE6PolicyChoices(_DesignIdentity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e6-policy-choices'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    criterion: MatrixFunctionalCriterion
    endpoint_order: tuple[tuple[str, int], ...]
    calibration_alpha: Decimal
    calibration_method: str
    point_transform: str
    admission_rule: str
    missing_policy: str
    comparator_methods: tuple[str, ...]
    standing: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _exact(self.criterion, MatrixFunctionalCriterion)
        matched = self.criterion.is_matched
        validate_decimal(self.calibration_alpha, field_name='transport calibration alpha', minimum=Decimal(0))
        if (not 0 < self.calibration_alpha < 1 or type(self.endpoint_order) is not tuple or not self.endpoint_order
                or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str
                    or type(row[1]) is not int or row[1] < 1 for row in self.endpoint_order)
                or len(set(self.endpoint_order)) != len(self.endpoint_order)
                or (self.criterion.predictor, self.criterion.horizon_tick) not in self.endpoint_order
                or self.calibration_method != (MATCHED_CALIBRATION_METHOD if matched else CALIBRATION_METHOD) or self.point_transform != POINT_TRANSFORM
                or self.admission_rule != (MATCHED_ADMISSION_RULE if matched else 'FINITE_ORIGINAL_Q_USABLE_CAUSAL_FEATURE_AND_PRIMARY_UPPER_AT_MOST_FROZEN_TOLERANCE')
                or self.missing_policy != 'ALL_ASSIGNED_NONSUCCESS_AND_ADMITTED_UNRESOLVED_FALSE_ADMISSION_WORST_CASE'
                or self.comparator_methods != (MATCHED_METHODS if matched else ('ALL_ORIGIN_RIDGE', 'RAW_TRAIN_MEDIAN'))
                or self.standing != (MATCHED_STANDING if matched else STANDING)):
            raise ValueError('transport choices change the frozen empirical rule or complete endpoint accounting')
        if matched:
            from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
            if self.endpoint_order != tuple(('FACTOR', tick) for tick in DENSE_RESPONSE_HORIZONS) or self.calibration_alpha != Decimal('.05'):
                raise ValueError('matched transport choices change their frozen both-view dense FACTOR query menu')


@dataclass(frozen=True, slots=True)
class MatrixProgrammeScientificDesign(_DesignIdentity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/scientific-design'
    VERSION: ClassVar[str] = '3.0.0'
    record_id: str
    downstream_account: str
    e1_factor_rule: E1FactorRule
    e1_criterion: E1CompactCriterion
    e1_numerical_design: MatrixParameterNumericalDesign
    e1_factor_numerical_design: MatrixParameterFactorNumericalDesign
    e1_scalar_definition: MatrixParameterScalarDefinition
    e1_coordinates: tuple[MatrixParameterCoordinate, ...]
    e2: MatrixNativeUtilityDesign
    training_protocol: NativeTrainingScientificProtocol
    training_assay: ScheduledResponseAssay
    e3_calibration_criterion: ScheduledCalibrationCriterion
    e3: ConfiguredProtectedE3Specification
    e4_development: SelectedE3E4Design
    e4_calibration: SelectedE3E4Design
    e4_confirmation: SelectedE3E4Design
    e4_preparation_coordinates: tuple[MatrixParameterCoordinate, ...]
    e4_calibration_criterion: ScheduledCalibrationCriterion
    e4_calibration_alpha: Decimal
    e4_factorial: SelectedE4FactorialChoices
    e4_revision: MatrixE4RevisionChoices
    e4_nomination: SelectedE4NominationRule | SelectedE4MatchedRelationRule
    e4_structure: MatrixE4StructuralChoices
    e5_development: SelectedPreparedDevelopmentSpecification
    e5_confirmation: MatrixE5ConfirmationChoices
    prepared_assay: MatrixPreparedAssayMethod
    recipe_interpretations: tuple[SelectedPreparedRecipeFamily, ...]
    panel_choices: MatrixPreparedPanelChoices
    e6: SelectedPreparedProtectedSpecification
    e6_policy: MatrixE6PolicyChoices

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for name, kind in (
                ('e1_factor_rule', E1FactorRule), ('e1_criterion', E1CompactCriterion),
                ('e1_numerical_design', MatrixParameterNumericalDesign),
                ('e1_factor_numerical_design', MatrixParameterFactorNumericalDesign),
                ('e1_scalar_definition', MatrixParameterScalarDefinition), ('e2', MatrixNativeUtilityDesign),
                ('training_protocol', NativeTrainingScientificProtocol), ('training_assay', ScheduledResponseAssay),
                ('e3_calibration_criterion', ScheduledCalibrationCriterion),
                ('e3', ConfiguredProtectedE3Specification), ('e4_development', SelectedE3E4Design),
                ('e4_calibration', SelectedE3E4Design), ('e4_confirmation', SelectedE3E4Design),
                ('e4_calibration_criterion', ScheduledCalibrationCriterion), ('e4_factorial', SelectedE4FactorialChoices),
                ('e4_revision', MatrixE4RevisionChoices), ('e4_nomination', (SelectedE4NominationRule, SelectedE4MatchedRelationRule)),
                ('e4_structure', MatrixE4StructuralChoices), ('e5_development', SelectedPreparedDevelopmentSpecification),
                ('e5_confirmation', MatrixE5ConfirmationChoices), ('prepared_assay', MatrixPreparedAssayMethod),
                ('panel_choices', MatrixPreparedPanelChoices), ('e6', SelectedPreparedProtectedSpecification),
                ('e6_policy', MatrixE6PolicyChoices)):
            _exact(getattr(self, name), kind)
        if (self.downstream_account not in ('ORIGINAL_E3', 'REVISION')
                or self.e5_development.account != self.downstream_account or self.e6.account != self.downstream_account
                or self.e5_development.phase != 'E5_OPPORTUNITY' or self.e6.phase != 'E6_TRANSFER'):
            raise ValueError('programme changes its explicit downstream account or scientific phase')
        self._validate_e1()
        self._validate_e3()
        self._validate_e4()
        self._validate_preparation()
        if self.e3.measurement.is_matched:
            self._validate_matched()

    def _validate_matched(self):
        """Reject mismatched science before allocations, fitting or acquisition."""
        from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
        by_coordinate = {coordinate_identity(co): co for co in self.training_protocol.coordinates}
        roles = dict(self.e3.role_coordinates)
        nominal = by_coordinate[roles['TRAIN']]
        physical = nominal.primary_view.bath_temperature, nominal.primary_view.friction_gamma, nominal.member.cross_coupling_gamma
        selection = self.e4_revision.matched_selection
        if (selection.is_curve_primary != self.e3.is_curve_primary
                or self.e4_nomination.is_curve_primary != self.e3.is_curve_primary):
            raise ValueError('matched programme mixes old-K and prospective-curve claims or fitting rules')
        if (type(self.e2.criterion) is not NativeAmendedUtilityCriterion
                or type(self.training_assay.mechanical_model) is not MatrixOriginResponseModel
                or self.e2.mathematical_protocol != self.training_protocol.mathematical_protocol
                or self.e2.assay != self.training_assay
                or self.training_assay.horizon_steps != DENSE_RESPONSE_HORIZONS
                or self.e3.assessment.comparison_ids != AMENDED_PRIMARY_FAMILY
                or (self.e1_criterion.alpha_numerator, self.e1_criterion.alpha_denominator) != (1, 160)
                or (selection.nominal_temperature, selection.nominal_friction, selection.nominal_coupling) != physical
                or tuple(factor.center for factor in self.e4_development.factors) != physical
                or any(factor.scale != 'LOG' or factor.low * 2 != factor.center or factor.high != factor.center * 2
                    for factor in self.e4_development.factors)):
            raise ValueError('matched programme changes its shared dense assay, primary family or nominal relation geometry')
        if (any(physical_key(by_coordinate[roles[role]]) != physical_key(nominal) for role in ('CALIBRATION', 'EVALUATION'))
                or len(self.e2.coordinates) != 1 or physical_key(self.e2.coordinates[0]) != physical_key(nominal)):
            raise ValueError('matched E2/TRAIN/CAL/CONF change the nominal de-anneal physical slice')
        for role, temperature in (('TRANSFER_NEARBY', Decimal('1.125')), ('TRANSFER_SHIFTED', Decimal('3.25'))):
            co = by_coordinate[roles[role]]
            restored = replace(co,
                primary_view=replace(co.primary_view, bath_temperature=nominal.primary_view.bath_temperature),
                fine_view=replace(co.fine_view, bath_temperature=nominal.fine_view.bath_temperature))
            if (co.primary_view.bath_temperature != temperature or co.fine_view.bath_temperature != temperature
                    or matched_key(co) != matched_key(nominal) or physical_key(restored) != physical_key(nominal)
                    or co.fine_view.friction_gamma != nominal.fine_view.friction_gamma):
                raise ValueError('matched E6 changes the frozen temperature-only nominal de-anneal slice')
        temperature_factor = self.e4_development.factors[0]
        if not temperature_factor.low < Decimal('1.125') < temperature_factor.high < Decimal('3.25'):
            raise ValueError('matched E6 temperatures do not have their declared interior/exterior E4 meanings')

    def _validate_e1(self):
        _records(self.e1_coordinates, MatrixParameterCoordinate, 'coordinate_id')
        rule, criterion = self.e1_factor_rule, self.e1_criterion
        stride = rule.lattice[1] - rule.lattice[0]
        if ({co.family_id for co in self.e1_coordinates} != set(FOUR_FAMILY_PREPARATION_IDS)
                or len(self.e1_coordinates) != len(FOUR_FAMILY_PREPARATION_IDS)
                or criterion.factor_rule != identity(rule)
                or rule.risk_start_tick != 0 or rule.sectors != ('X', 'Y')
                or any(co.observation_ticks != rule.lattice or co.primary_view.timestep != rule.primary_dt
                    for co in self.e1_coordinates)
                or any(_coordinate_physics(co) != _coordinate_physics(self.e1_coordinates[0]) for co in self.e1_coordinates)
                or criterion.occurrence_end_tick not in rule.lattice
                or criterion.survival_duration_ticks % stride
                or criterion.occurrence_end_tick + criterion.survival_duration_ticks > rule.lattice[-1]):
            raise ValueError('E1 design changes its four-family full history, paired clock or survival window')
        _scalar(rule, self.e1_scalar_definition)

    def _validate_e3(self):
        protocol = self.training_protocol
        math = protocol.mathematical_protocol
        measurement = self.e3.measurement
        calibration_population = self.e3.population('CALIBRATION')
        _assay_math(self.training_assay, math)
        if (self.training_assay.criterion != math.identity
                or self.training_assay.horizon_steps != math.horizon_steps
                or math.primary_timestep != measurement.primary_timestep or math.horizon_steps != measurement.horizons
                or any(getattr(math, name) != getattr(measurement, name)
                    for name in ('panel_roles', 'estimand', 'metric', 'aggregation'))
                or tuple((action.role, action.amplitude, action.pulse_steps) for action in math.action_scales)
                    != tuple((role, measurement.action_amplitude, measurement.pulse_ticks) for role in measurement.actions)
                or self.e3.calibration_target_view != 'MAX_PAIRED_VIEWS'
                or self.e3_calibration_criterion.minimum_group_count != calibration_population.expected_units
                or self.e3_calibration_criterion.required_family_ids != (calibration_population.family_id,)
                or self.e3_calibration_criterion.construction_estimand != (
                    'WHOLE_ROOT_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_FACTOR58_NONUSE_INFINITY' if measurement.is_matched else
                    'COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY')
                or any(population.unit_ids is not None for population in self.e3.populations)):
            raise ValueError('TRAIN/E3 design changes exact paired response mathematics or embeds assigned units')
        coordinates = {coordinate_identity(co): co for co in protocol.coordinates}
        policies = dict(protocol.coordinate_policies)
        by_policy = {identity(policy): policy for policy in protocol.prefix_policies}
        if set(co for _, co in self.e3.role_coordinates) != set(coordinates):
            raise ValueError('TRAIN/E3 design omits or substitutes a role coordinate')
        for role, pin in self.e3.role_coordinates:
            co, policy = coordinates[pin], by_policy[policies[pin]]
            if (co.primary_view.timestep != measurement.primary_timestep or co.fine_view.timestep != measurement.fine_timestep
                    or co.family_id != self.e3.population(role).family_id
                    or co.q != measurement.q or policy.cutoff_tick != measurement.origin_tick
                    or co.observation_ticks[-1] < policy.cutoff_tick + max(measurement.horizons)):
                raise ValueError('TRAIN/E3 design changes its actual input geometry, cutoff or complete futures')
            validate_selected_prefix_projection(math, policy, measurement.origin_tick)

    def _validate_e4(self):
        _records(self.e4_preparation_coordinates, MatrixParameterCoordinate, 'coordinate_id')
        phases = self.e4_development, self.e4_calibration, self.e4_confirmation
        families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
        matched = self.e4_revision.matched_selection is not None
        if (len(self.e4_preparation_coordinates) != len(families)
                or {co.family_id for co in self.e4_preparation_coordinates} != set(families)
                or any((phase.factors, phase.confidence) != (phases[0].factors, phases[0].confidence) for phase in phases)
                or any(co.observation_ticks != self.e4_structure.factor_rule.lattice
                    or co.primary_view.timestep != self.e4_structure.factor_rule.primary_dt for co in self.e4_preparation_coordinates)
                or self.e4_nomination.confirmation_group_count != self.e4_confirmation.group_count
                or self.e4_calibration_criterion.minimum_group_count > self.e4_calibration.group_count
                or self.e4_calibration_criterion.required_family_ids != (() if matched else families)):
            raise ValueError('E4 design changes its four families, full grid histories or declared phase denominators')
        validate_decimal(self.e4_calibration_alpha, field_name='E4 calibration alpha', minimum=Decimal(0))
        if not 0 < self.e4_calibration_alpha < 1:
            raise ValueError('E4 calibration alpha must be explicitly between zero and one')
        expected_slots = {(family, ordinal) for family in families
            for ordinal in range(self.e4_development.group_count // len(families))}
        math = self.training_protocol.mathematical_protocol
        if (matched != self.e3.measurement.is_matched
                or matched != (type(self.e4_structure.prediction) is E4MatchedRelationSelection)
                or matched != (type(self.e4_nomination) is SelectedE4MatchedRelationRule)
                or matched and (self.downstream_account != 'REVISION'
                    or self.e4_revision.matched_selection != self.e4_structure.prediction
                    or self.e4_calibration_alpha != Decimal('.05')
                    or self.e4_development.family_sampling_rule != 'BALANCED_FIXED_FOUR_FAMILY_GROUPS'
                    or any(phase.family_sampling_rule != 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW'
                        for phase in (self.e4_calibration, self.e4_confirmation)))):
            raise ValueError('programme changes the declared matched relation, downstream pair or calibration coverage')
        if ({(family, ordinal) for family, ordinal, _ in self.e4_revision.fold_slots} != expected_slots
                or self.e4_revision.fold_count != self.e4_structure.prediction.fold_count
                or self.e4_revision.target != self.e4_factorial.target
                or self.e4_factorial.target.criterion != math.identity
                or self.e4_factorial.target.horizon_ticks != math.horizon_steps
                or self.e4_factorial.family_ids != self.e3.assessment.comparison_ids
                or self.e4_structure.factor_rule != selected_original_factor_rule(math)
                or self.e4_structure.secondary_target.mathematical_protocol != math
                or any(policy.factor_numerical_design != self.e4_structure.numerical_design
                    for policy in self.training_protocol.prefix_policies)):
            raise ValueError('E4 design changes its original target, fold slots, full family or structural mathematics')

    def _validate_preparation(self):
        development, confirmation, transfer = self.e5_development, self.e5_confirmation, self.e6
        arms = dict(development.arms)
        baseline = arms.get(confirmation.baseline_arm_id)
        nominal_pin = dict(self.e3.role_coordinates)['TRAIN']
        nominal = next(co for co in self.training_protocol.coordinates if coordinate_identity(co) == nominal_pin)
        _assay_math(self.prepared_assay, self.training_protocol.mathematical_protocol)
        matched = self.e3.measurement.is_matched
        if (type(baseline) is not MatrixOriginalScheduleRecipe
                or any(criterion.is_matched != matched for criterion in (development.criterion, confirmation.criterion, transfer.criterion))
                or any(criterion.is_curve_primary != self.e3.is_curve_primary
                    for criterion in (development.criterion, confirmation.criterion, transfer.criterion))
                or set(confirmation.eligible_nominee_arm_ids) != set(arms) - {confirmation.baseline_arm_id}
                or confirmation.criterion != development.criterion
                or transfer.arms != ((confirmation.baseline_arm_id, baseline),)
                or transfer.criterion != self.e6_policy.criterion
                or transfer.expected_groups != self.e3.population('TRANSFER_NEARBY').expected_units
                or transfer.expected_groups != self.e3.population('TRANSFER_SHIFTED').expected_units
                or self.e6_policy.calibration_alpha != self.e3.calibration_alpha
                or self.e6_policy.endpoint_order != tuple((description, horizon)
                    for description in (('FACTOR',) if matched else self.e3.measurement.descriptions)
                    for horizon in self.e3.measurement.horizons)
                or self.prepared_assay != MatrixPreparedAssayMethod.from_assay(
                    self.prepared_assay.record_id, self.training_assay)
                or development.criterion.family_slots != self.e4_factorial.family_ids
                or transfer.criterion.family_slots != self.e4_factorial.family_ids):
            raise ValueError('preparation design changes the frozen menu, unchanged criterion, transfer or assay joins')
        if matched and (self.downstream_account != 'REVISION' or development.criterion != transfer.criterion
                or development.expected_groups != 16 or confirmation.expected_groups != 80 or transfer.expected_groups != 64
                or development.minimum_recoverable_groups != 2 or development.tie_policy != 'MINIMUM_TOTAL_EFFORT_THEN_LEXICAL'):
            raise ValueError('matched preparation changes its fixed SR/BR account, DEV16/CONF80/transfer64 census or nomination rule')
        validate_original_schedule_recipe(baseline, nominal, baseline.primary_steps)
        _records(self.recipe_interpretations, SelectedPreparedRecipeFamily, 'arm_id')
        if tuple(row.arm_id for row in self.recipe_interpretations) != tuple(arm for arm, _ in development.arms):
            raise ValueError('preparation design omits an explicit recipe feature-family interpretation')
        if any(row.scientific_premise != arms[row.arm_id].identity for row in self.recipe_interpretations):
            raise ValueError('preparation feature-family premise must name its exact frozen recipe body')
        if self.panel_choices.panel_roles != self.training_protocol.mathematical_protocol.panel_roles:
            raise ValueError('preparation design changes its original complete response panel roles')

    @property
    def e1_family_counts(self):
        return tuple((family.family_id, family.requested_roots) for family in self.e1_criterion.family_requirements)

    @property
    def phase_group_counts(self):
        """Complete independent-unit denominators; E1/E2 units are whole roots."""
        return (('e1', sum(count for _, count in self.e1_family_counts)), ('e2', self.e2.expected_units),
            ('train', self.e3.population('TRAIN').expected_units),
            ('e3.calibration', self.e3.population('CALIBRATION').expected_units),
            ('e3.confirmation', self.e3.population('EVALUATION').expected_units),
            ('e4.development', self.e4_development.group_count), ('e4.calibration', self.e4_calibration.group_count),
            ('e4.confirmation', self.e4_confirmation.group_count), ('e5.development', self.e5_development.expected_groups),
            ('e5.confirmation', self.e5_confirmation.expected_groups),
            ('e6.nearby', self.e3.population('TRANSFER_NEARBY').expected_units),
            ('e6.shifted', self.e3.population('TRANSFER_SHIFTED').expected_units))

    @classmethod
    def from_document(cls, document):
        return decode_canonical_record(document, cls)
