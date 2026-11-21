# SPDX-License-Identifier: MPL-2.0
"""Explicit scientific choices required before a fresh model-free inquiry.

The selection records operator decisions. It does not turn a pilot, a budget,
or an asymptotic interval into a power or physical-qualification certificate.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import math

from empirical_lawhood.science.records.serialization import validate_sha256


ENDPOINTS = {
    'M0.control_law_consistency': 'dimensionless',
    'M1.assigned_service_gain': 'probability-difference',
    'M2.finite_history_receiver_error': 'declared-receiver-units',
    'M3.assigned_adequacy_gain': 'probability-difference',
    'M3.signed_response_contrast': 'actuator-normalized-response',
    'M4.destination_receiver_bound': 'declared-resolvent-receiver-units',
    'M5.finite_frame_signed_mean': 'physical-momentum',
    'M6.restrained_free_energy_difference': 'native-energy',
    'M7.finite_horizon_event_contrast': 'probability-difference',
}
ENDPOINT_THRESHOLDS = {
    'M1.assigned_service_gain': ('formation', 'probability_gain_margin'),
    'M2.finite_history_receiver_error': ('memory', 'tolerance'),
    'M3.assigned_adequacy_gain': ('formation', 'probability_gain_margin'),
    'M4.destination_receiver_bound': ('response', 'certificate_tolerance'),
}
# Each name describes the receiver, its units and the exact cutoff that its
# scientific owner uses. Older endpoint names retain their historical meaning.
RECEIVER_ENDPOINTS = {
    'M0.false_delivery_probability': ('probability', 'false_delivery_limit'),
    'M1.assigned_coverage_loss': ('probability-difference', 'maximum_coverage_loss'),
    'M2.common_future_wrong_decision': ('probability', 'risk_budget'),
    'M3.signed_response_contrast': ('actuator-normalized-response', 'signed_halfwidth'),
    'M4.signed_resolvent_difference': ('declared-resolvent-receiver-units', 'signed_pair_allowance'),
    'M5.signed_frame_mean_rms_error': ('actuator-normalized-momentum', 'mean_rms_budget_actuator'),
    'M5.signed_frame_mean_halfwidth': ('actuator-normalized-momentum', 'mean_halfwidth_actuator'),
    'M6.same_temperature_free_energy_difference': ('kBT', 'energy_budget_kbt'),
    'M7.subsequent_target_incidence': ('probability-difference', 'incidence_budget'),
    'M7.restricted_mean_time_difference': ('native-time', 'rmst_budget'),
}
VERIFICATION = frozenset({
    'COMPLETE_ASSIGNED_AND_FAILED_ROOT_CENSUS', 'INDEPENDENT_ANALYSIS_OPERATION',
    'COUPLED_H_H2_H4', 'WITHHELD_FUTURE_SUFFIX', 'EXACT_FINITE_FRAME_REVEAL_ALL',
    'SEGMENT_AND_PROTOCOL_AGE_DIAGNOSTICS', 'NESTED_CENTER_AND_LONG_REFERENCE',
})

def common_future_tail_alpha(module_alpha, coordinate_count):
    """Clopper–Pearson tail for both directions of five rules in every coordinate."""
    return module_alpha / (4 * coordinate_count * 5)


@dataclass(frozen=True, slots=True)
class ConfirmationEndpoint:
    name: str
    practical_effect: Decimal
    units: str

    def __post_init__(self):
        expected_units = ENDPOINTS.get(self.name)
        if self.name in RECEIVER_ENDPOINTS:
            expected_units = RECEIVER_ENDPOINTS[self.name][0]
        if expected_units is None or self.units != expected_units:
            raise ValueError('Confirmation endpoint must identify its implemented receiver and physical units')
        if not self.practical_effect.is_finite() or self.practical_effect <= 0:
            raise ValueError('Each primary endpoint requires a finite positive practical effect')
        if self.units in ('probability', 'probability-difference') and self.practical_effect > 1:
            raise ValueError('A probability-difference effect cannot exceed one')


@dataclass(frozen=True, slots=True)
class ConfirmationSelection:
    endpoints: tuple[ConfirmationEndpoint, ...]
    population_target: str
    target_law: str
    precision_goal: str
    stopping_rule: str
    independent_verification: tuple[str, ...]
    parent_readout_sha256: str
    capacity_basis: str

    @classmethod
    def from_document(cls, value):
        fields = {'endpoints', 'population_target', 'target_law', 'precision_goal',
            'stopping_rule', 'independent_verification', 'parent_readout_sha256', 'capacity_basis'}
        if type(value) is not dict or set(value) != fields:
            raise ValueError('Confirmation requires every explicit endpoint, population, precision, stopping, verification and capacity choice')
        if type(value['endpoints']) is not list or not value['endpoints']:
            raise ValueError('Confirmation needs a nonempty primary endpoint family')
        endpoints = []
        for row in value['endpoints']:
            if type(row) is not dict or set(row) != {'name', 'practical_effect', 'units'} or type(row['practical_effect']) is not str:
                raise ValueError('An endpoint declares name, decimal practical effect and units')
            endpoints.append(ConfirmationEndpoint(row['name'], Decimal(row['practical_effect']), row['units']))
        if len({r.name for r in endpoints}) != len(endpoints):
            raise ValueError('Primary endpoints must be unique')
        if value['population_target'] != 'COMPLETE_ASSIGNED_ROOT_POPULATION':
            raise ValueError('Confirmation retains all assigned roots, including nonentry and failures')
        if value['target_law'] != 'DECLARED_FINITE_AGE_ROOT_LAW':
            raise ValueError('A stationary law cannot be asserted by a finite-age declaration')
        if value['precision_goal'] not in ('DETECTION_ONLY', 'TASK_EQUIVALENCE_IF_CERTIFIED'):
            raise ValueError('Choose detection or explicitly conditional task equivalence')
        if value['stopping_rule'] != 'FIXED_ROOT_CENSUS_AND_PREDECLARED_RECORD_LADDER':
            raise ValueError('Outcome-dependent root stopping is not implemented')
        verification = value['independent_verification']
        required = {'COMPLETE_ASSIGNED_AND_FAILED_ROOT_CENSUS', 'INDEPENDENT_ANALYSIS_OPERATION'}
        if (type(verification) is not list or any(type(v) is not str for v in verification)
                or len(set(verification)) != len(verification) or set(verification) - VERIFICATION
                or not required <= set(verification)):
            raise ValueError('Declare the independent verification and complete negative denominator')
        validate_sha256(value['parent_readout_sha256'])
        if value['capacity_basis'] != 'AUTHENTICATED_PARENT_AND_OPERATOR_MEASURED_HOST':
            raise ValueError('Operational ceilings require a measured host selection and authenticated pilot')
        return cls(tuple(endpoints), value['population_target'], value['target_law'], value['precision_goal'],
            value['stopping_rule'], tuple(verification), value['parent_readout_sha256'], value['capacity_basis'])


def validate_confirmation(settings, assignments, *, parent_readout=None, parent_modules=None):
    """Validate decisions, with measured-parent binding at the public boundary."""
    selected = ConfirmationSelection.from_document(settings.get('confirmation'))
    modules = {m for row in assignments for m in row.modules}
    if any(endpoint.name.split('.')[0] not in modules for endpoint in selected.endpoints):
        raise ValueError('Primary endpoint has no assigned scientific module')
    endpoint_effects = []
    for endpoint in selected.endpoints:
        module = endpoint.name.split('.')[0]
        if 'receiver_study' in settings:
            if endpoint.name not in RECEIVER_ENDPOINTS:
                raise ValueError('Select an endpoint implemented for this receiver study: ' + endpoint.name)
            if module == 'M1' and not settings['receiver_study']['M1']['structural_service']:
                raise ValueError('M1 structural coverage requires the assigned structural assay')
            threshold = ('receiver_study', module, RECEIVER_ENDPOINTS[endpoint.name][1])
        else:
            if endpoint.name not in ENDPOINTS:
                raise ValueError('This endpoint requires its receiver-study revision: ' + endpoint.name)
            threshold = ENDPOINT_THRESHOLDS.get(endpoint.name)
        if threshold is not None:
            cutoff = settings
            for key in threshold:
                cutoff = cutoff[key]
            if endpoint.practical_effect != Decimal(str(cutoff)):
                raise ValueError('Primary endpoint practical effect must equal its implemented threshold: '
                    + endpoint.name + ' -> ' + '.'.join(threshold))
        endpoint_effects.append({'name': endpoint.name, 'practical_effect': str(endpoint.practical_effect),
            'units': endpoint.units,
            'effect_role': 'IMPLEMENTED_RECEIVER_TOLERANCE_OR_GAIN_MARGIN' if threshold else
                'DECLARED_PRECISION_TARGET_ONLY; NO_IMPLEMENTED_PRACTICAL_EFFECT_DECISION',
            'operative_setting': None if threshold is None else '.'.join(threshold),
            'automatic_success_granted': False})
    if parent_modules is not None and not modules <= set(parent_modules):
        raise ValueError('Confirmation requires a pilot of every selected module')
    if any(type(settings['resources'][key]) is not int or settings['resources'][key] <= 0
            for key in ('memory_bytes', 'wall_time_seconds', 'output_bytes')):
        raise ValueError('Confirmation requires explicit measured memory, wall-time and output ceilings')
    checks = set(selected.independent_verification)
    if 'M2' in modules and ('SEGMENT_AND_PROTOCOL_AGE_DIAGNOSTICS' not in checks
            or ('receiver_study' not in settings and not settings['memory']['protocol_age_ticks'])):
        raise ValueError('Memory confirmation requires frozen protocol-age and segment diagnostics')
    if 'M3' in modules and (not {'COUPLED_H_H2_H4', 'WITHHELD_FUTURE_SUFFIX'} <= checks
            or set(settings['response']['refinements']) != {1, 2, 4}):
        raise ValueError('Response confirmation requires coupled h/h2/h4 and an independent future suffix')
    if 'M5' in modules and 'EXACT_FINITE_FRAME_REVEAL_ALL' not in checks:
        raise ValueError('Finite-frame confirmation requires the reveal-all benchmark comparison')
    if 'M6' in modules and ('NESTED_CENTER_AND_LONG_REFERENCE' not in checks
            or settings['equilibrium']['reference_ticks'] <= settings['equilibrium']['sample_ticks']):
        raise ValueError('Equilibrium confirmation requires nested centers and the longer native reference')
    if parent_readout is not None:
        from .records import json_text
        if sha256(json_text(parent_readout).encode()).hexdigest() != selected.parent_readout_sha256:
            raise ValueError('Confirmation capacity/choice record does not bind the authenticated parent readout')
    root_counts = {module: sum(module in row.modules for row in assignments) for module in sorted(modules)}
    memory_feasibility = None
    if 'M2' in root_counts and 'receiver_study' in settings:
        receiver = settings['receiver_study']['M2']
        count = root_counts['M2']
        module_alpha = float(settings['alpha']) * float(settings['inference']['module_alpha_weights']['M2'])
        tail_alpha = common_future_tail_alpha(module_alpha, len(receiver['coordinates']))
        bound = -math.expm1(math.log(tail_alpha) / count)
        budget = float(receiver['risk_budget'])
        minimum = 1 if budget == 1 else math.ceil(math.log(tail_alpha) / math.log1p(-budget))
        memory_feasibility = {'receiver': 'COMMON_FINITE_AGE_BINARY_FUTURE',
            'coordinates': len(receiver['coordinates']), 'descriptions': 5, 'per_tail_alpha': tail_alpha,
            'assigned_independent_roots': count, 'upper_risk_with_zero_errors_and_complete_paths': bound,
            'minimum_independent_roots_if_all_correct': minimum, 'risk_budget': budget,
            'assumes_independent_identically_distributed_future_decision_errors': True,
            'power_established': False}
        if (selected.precision_goal == 'TASK_EQUIVALENCE_IF_CERTIFIED'
                and any(e.name == 'M2.common_future_wrong_decision' for e in selected.endpoints)
                and bound > budget):
            raise ValueError('The common-future root census cannot meet the risk budget even with zero errors')
    elif 'M2' in root_counts:
        from empirical_lawhood.methods.model_free.memory import memory_bound_feasibility
        memory = settings['memory']
        groups = (len(settings['native']['coordinates']) * len(memory['observation_dimensions'])
            * len(memory['history_orders']) * (1 + len(memory['protocol_age_ticks'])))
        history_alpha = .5 * float(settings['alpha']) * float(settings['inference']['module_alpha_weights']['M2'])
        rows = [{'observation_dimensions': dimension,
            **memory_bound_feasibility(root_counts['M2'],
                alphabet_size=math.prod(len(edges)-1 for edges in memory['bin_edges'][:dimension]),
                history_order=order, alpha=history_alpha, comparison_groups=groups,
                lag_count=len(memory['lags']), looks=len(memory['record_length_ladder']), max_cells=memory['maximum_cells'])}
            for dimension in memory['observation_dimensions'] for order in memory['history_orders']]
        probability_possible = all(row['all_conditioning_lower_bounds_can_be_positive'] for row in rows)
        samples = memory['record_ticks'] // memory['stride'] + 1
        temporal = [{'history_order': order, 'lag_samples': lag,
            'required_history_span_samples': (order + 1) * lag,
            'pooled_complete_anchor_count': max(0, samples - (order + 1) * lag),
            'protocol_ages': [{'age_tick': age, 'future_anchor_sample': age // memory['stride'],
                'complete_anchor_count': int((order + 1) * lag <= age // memory['stride'] < samples)}
                for age in memory['protocol_age_ticks']]}
            for order in memory['history_orders'] for lag in memory['lags']]
        temporal_possible = all(row['pooled_complete_anchor_count'] > 0
            and all(age['complete_anchor_count'] == 1 for age in row['protocol_ages']) for row in temporal)
        possible = probability_possible and temporal_possible
        memory_feasibility = {'history_fraction_of_module_alpha': .5, 'rows': rows,
            'probability_bounds_pass_necessary_condition': probability_possible,
            'record_samples': samples, 'temporal_support': temporal,
            'all_selected_histories_have_temporal_support': temporal_possible,
            'all_selected_menus_pass_necessary_condition': possible,
            'within_root_time_origins_are_not_independent_roots': True, 'power_established': False}
        if (selected.precision_goal == 'TASK_EQUIVALENCE_IF_CERTIFIED'
                and any(endpoint.name == 'M2.finite_history_receiver_error' for endpoint in selected.endpoints)
                and not probability_possible):
            raise ValueError('Memory task-equivalence confirmation is impossible under the declared all-cell root bound; '
                'select DETECTION_ONLY or revise the frozen root count, alphabet/history and comparison family')
        if (selected.precision_goal == 'TASK_EQUIVALENCE_IF_CERTIFIED'
                and any(endpoint.name == 'M2.finite_history_receiver_error' for endpoint in selected.endpoints)
                and not temporal_possible):
            raise ValueError('Memory task-equivalence confirmation is impossible because a declared record or protocol-age '
                'anchor lacks its complete history; more independent roots cannot supply missing time support')
    # This is an optimistic one-event feasibility diagnostic, not a power
    # calculation. Actual joint-cell, conditional and paired bands are wider.
    optimistic = {module: min(1., math.sqrt(math.log(2 / (float(settings['alpha']) *
        float(settings['inference']['module_alpha_weights'][module]))) / (2 * count)))
        for module, count in root_counts.items()}
    conditional = None
    if 'receiver_study' in settings and 'M3' in root_counts:
        coordinates = settings['receiver_study']['M3']['signed_coordinates']
        per_coordinate = (float(settings['alpha']) * float(settings['inference']['module_alpha_weights']['M3'])
                          / len(coordinates))
        conditional = {'per_coordinate_alpha': per_coordinate, 'assigned_roots': root_counts['M3'],
                       'upper_risk_if_all_deliver_and_all_are_correct':
                           -math.expm1(math.log(per_coordinate) / root_counts['M3']),
                       'assumes_independent_identically_distributed_conditional_errors': True}
    return {'selection_complete': True, 'parent_evidence_bound': parent_readout is not None,
        'endpoint_effect_roles': endpoint_effects,
        'independent_roots_by_module': root_counts, 'optimistic_single_event_halfwidth': optimistic,
        'memory_family_feasibility': memory_feasibility,
        **({'signed_delivery_feasibility': conditional} if conditional is not None else {}),
        'precision_goal': selected.precision_goal, 'power_established': False,
        'equivalence_policy': 'REMAIN_UNRESOLVED_UNLESS_ACTUAL_TASK_BOUND_MEETS_TOLERANCE',
        'capacity_scope': 'OPERATOR_SELECTED_CEILINGS; NOT_A_UNIVERSAL_CAPACITY_CERTIFICATE'}
