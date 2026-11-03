# SPDX-License-Identifier: MPL-2.0
"""Pure complete E4 coordinates and matched independent-group allocations."""

from dataclasses import replace
from itertools import product

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.serialization import validate_stable_id

from . import records
from .selected_e3_e4_records import SelectedE3E4Design


PHASES = ("CALIBRATION", "CONFIRMATION", "DEVELOPMENT")
CONSTRUCTION = "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"


def selected_e4_population_groups(*, namespace, population_designs, preparations, streams):
    """Frozen balanced DEV and one independent uniform family draw per CAL/CONF group."""
    from .selected_streams import SelectedE4StreamRecipe
    validate_stable_id(namespace)
    if type(streams) is not SelectedE4StreamRecipe:
        raise TypeError('E4 group allocation requires its explicitly committed random construction')
    streams.__post_init__()
    families = tuple(sorted(co.family_id for co in preparations))
    if families != tuple(sorted(FOUR_FAMILY_PREPARATION_IDS)):
        raise ValueError('E4 group allocation changes the fixed uniform four-family menu')
    result = []
    for phase, design in population_designs:
        design.__post_init__()
        if phase not in PHASES:
            raise ValueError('E4 group allocation changes its declared phase')
        if design.family_sampling_rule == 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW':
            if phase == 'DEVELOPMENT':
                raise ValueError('E4 fitting retains preassigned balanced DEV family support')
            assigned = tuple('group.' + namespace + '.' + phase.lower() + '.iid.' + str(index).zfill(3)
                for index in range(design.group_count))
            draws = tuple((group, streams.family(group)) for group in assigned)
            result.extend((phase, family, tuple(group for group, selected in draws if selected == family)) for family in families)
        else:
            result.extend((phase, family, tuple('group.' + namespace + '.' + phase.lower() + '.' + str(family_index)
                + '.' + str(index).zfill(3) for index in range(design.group_count // len(families))))
                for family_index, family in enumerate(families))
    return tuple(result)


def selected_e4_population_coordinates(preparations, design, *, namespace):
    """Retain all eight frozen corners and the centre for each declared family."""
    validate_stable_id(namespace)
    if (type(preparations) is not tuple or type(design) is not SelectedE3E4Design
            or any(type(value) is not MatrixParameterCoordinate for value in preparations)
            or len(preparations) != len(FOUR_FAMILY_PREPARATION_IDS)
            or {value.family_id for value in preparations} != set(FOUR_FAMILY_PREPARATION_IDS)):
        raise TypeError("E4 coordinates require all four exact preparations and an explicit population design")
    design.__post_init__()
    for value in preparations:
        value.__post_init__()
    preparations = tuple(sorted(preparations, key=lambda value: value.family_id))
    axes = tuple((factor.low, factor.center, factor.high) for factor in design.factors)
    corners = (*product(*((low, high) for low, _, high in axes)), tuple(center for _, center, _ in axes))
    coordinates = []
    for family_index, base in enumerate(preparations):
        for case_index, (temperature, friction, coupling) in enumerate(corners):
            name = namespace + "." + str(family_index) + "." + str(case_index)
            coordinates.append(replace(base, coordinate_id="coordinate." + name,
                member=replace(base.member, member_id="member." + name, cross_coupling_gamma=coupling),
                primary_view=replace(base.primary_view, view_id="view.primary." + name,
                    bath_temperature=temperature, friction_gamma=friction),
                fine_view=replace(base.fine_view, view_id="view.fine." + name,
                    bath_temperature=temperature, friction_gamma=friction)))
    return tuple(sorted(coordinates, key=lambda value: value.coordinate_id))


def _selected_e4_population_members(*, namespace, preparations,
        population_designs, group_ids, history_streams):
    """Validate all source members before their actual exposure is published."""
    if (type(population_designs) is not tuple or tuple(phase for phase, _ in population_designs) != PHASES
            or any(type(design) is not SelectedE3E4Design for _, design in population_designs)):
        raise ValueError("E4 allocation requires all three exact frozen population designs")
    for _, design in population_designs:
        design.__post_init__()
    first = population_designs[0][1]
    if any((design.factors, design.confidence) != (first.factors, first.confidence)
            for _, design in population_designs):
        raise ValueError("E4 phases change their shared factors or confidence")
    coordinates = selected_e4_population_coordinates(preparations, first, namespace=namespace)
    families = tuple(sorted(value.family_id for value in preparations))
    if (type(group_ids) is not tuple or any(type(row) is not tuple or len(row) != 3 for row in group_ids)
            or tuple((phase, family) for phase, family, _ in group_ids) !=
                tuple((phase, family) for phase in PHASES for family in families)):
        raise ValueError("E4 allocation omits a complete phase/family group assignment")
    groups = []
    design_by_phase = dict(population_designs)
    for phase, _, assigned in group_ids:
        if (type(assigned) is not tuple or assigned != tuple(sorted(set(assigned)))
                or design_by_phase[phase].family_sampling_rule == 'BALANCED_FIXED_FOUR_FAMILY_GROUPS'
                    and len(assigned) != design_by_phase[phase].group_count // len(families)):
            raise ValueError("E4 allocation changes its complete independent-group denominator")
        for group in assigned:
            validate_stable_id(group)
        groups.extend(assigned)
    if any(sum(len(assigned) for role, _, assigned in group_ids if role == phase) != design.group_count
            for phase, design in population_designs):
        raise ValueError('E4 allocation drops assigned independent groups from its realised family counts')
    if len(set(groups)) != len(groups):
        raise ValueError("E4 independent groups overlap phases or preparation families")
    if (type(history_streams) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in history_streams)
            or tuple(group for group, _ in history_streams) != tuple(sorted(groups))):
        raise ValueError("E4 allocation changes its complete original history-stream census")
    streams = dict(history_streams)
    roots, scopes = [], []
    for phase, family, assigned in group_ids:
        if not assigned:
            continue
        role = MatrixProgrammeRole(phase)
        local = tuple(value for value in coordinates if value.family_id == family)
        family_index = families.index(family)
        for group in assigned:
            for case_index, coordinate in enumerate(local):
                root = MatrixProgrammeRoot("root." + group + "." + str(case_index), group,
                    "regime." + coordinate.coordinate_id, coordinate.coordinate_id, role, coordinate.clock_id)
                roots.append(records.ScheduledRoot(root, records.coordinate_identity(coordinate), streams[group]))
        scopes.append(records.ScheduledMatchedScope("scope." + namespace + "." + phase.lower()
            + "." + str(family_index), role, assigned,
            tuple(records.coordinate_identity(value) for value in local), CONSTRUCTION))
    return coordinates, tuple(sorted(roots, key=lambda value: value.root.root_id)), tuple(
        sorted(scopes, key=lambda value: value.scope_id))


def selected_e4_population_allocation(*, allocation_id, namespace, preparations,
        population_designs, group_ids, history_streams, exposure):
    """Build every coordinate of each explicitly assigned independent group."""
    validate_stable_id(allocation_id)
    coordinates, roots, scopes = _selected_e4_population_members(namespace=namespace,
        preparations=preparations, population_designs=population_designs,
        group_ids=group_ids, history_streams=history_streams)
    return records.ScheduledAllocation(allocation_id, coordinates,
        tuple(sorted(roots, key=lambda value: value.root.root_id)),
        tuple(sorted(scopes, key=lambda value: value.scope_id)), exposure)
