# SPDX-License-Identifier: MPL-2.0
"""Bind ordinary E4 structural choices to the exact current phase mathematics.

This pure binding supplies no acquisition, source qualification, publication or
outcome-access authority. Actual original readers own those later boundaries.
"""


def structural_stage_census(programme):
    """Declare the causally later PURE graph without claiming it has executed."""
    from .full_factor_bindings import key
    from .selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
    from .selected_e4_programme import SelectedE4PhaseProgramme
    if type(programme) not in (SelectedE3E4DevelopmentProgramme, SelectedE4PhaseProgramme):
        raise TypeError('ordinary E4 structural census requires its exact declared phase')
    protected = type(programme) is SelectedE4PhaseProgramme
    count = len(programme.cases)
    operations = tuple(sorted((key(protected, phase), number)
        for phase, number in (('measure', count), ('assess', count), ('reduce', 1))))
    outputs = tuple(sorted((*((key(protected, phase) + '.product', number)
        for phase, number in (('measure', count), ('assess', count), ('reduce', 1))),
        (key(protected, 'measure') + '.arrays', count))))
    return operations, outputs


def structural_measurement(*, programme, bank, choices):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixE4StructuralChoices
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from . import selected_e3_e4_records as development
    from . import selected_e4_programme as protected
    from .full_factor_preparation import ScheduledFullFactorMeasurement

    if type(choices) is not MatrixE4StructuralChoices:
        raise TypeError('ordinary E4 structure requires its exact declared scientific choices')
    choices.__post_init__()
    if (type(programme), type(bank)) not in (
            (development.SelectedE3E4DevelopmentProgramme, development.SelectedE3E4DevelopmentBank),
            (protected.SelectedE4PhaseProgramme, protected.SelectedE4PhaseBank)):
        raise TypeError('ordinary E4 structure requires its actual current phase programme and bank')
    programme.__post_init__()
    if programme.bank != bank.identity:
        raise ValueError('ordinary E4 structure changes its exact phase bank')
    criterion = bank.forecast_design.criterion_record
    if (choices.factor_rule != development.selected_original_factor_rule(criterion)
            or choices.secondary_target.mathematical_protocol != criterion):
        raise ValueError('ordinary E4 structure changes original factor or response-task mathematics')
    index = bank.source_index()
    descriptors = {value.root_id: value for value in bank.sources}
    rules = {}
    for case in programme.cases:
        descriptor = descriptors.get(case.root_id)
        if descriptor is None or descriptor.identity != case.source:
            raise ValueError('ordinary E4 structure substitutes an assigned source or root')
        source = index.resolve(descriptor)
        development.validate_selected_prefix_projection(criterion, source.policy, source.policy.cutoff_tick)
        if (choices.factor_rule.primary_dt != source.coordinate.primary_view.timestep
                or choices.factor_rule.lattice != source.coordinate.observation_ticks
                or choices.numerical_design != source.policy.factor_numerical_design):
            raise ValueError('ordinary E4 structure changes the complete original lattice, clock or numerical checks')
        coordinate = ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate)
        rules[coordinate] = (choices.factor_rule, choices.numerical_design)
    return ScheduledFullFactorMeasurement(programme.identity,
        tuple((coordinate, *value) for coordinate, value in sorted(rules.items(), key=lambda row: row[0].object_id)),
        choices.views, choices.measurement, choices.independence)
