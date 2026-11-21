# SPDX-License-Identifier: MPL-2.0
"""Prospective common-protein support and one initial-WT environmental direction.

The support is frozen before primary observations. No later alignment,
renomination, or favorable-outcome fallback is permitted.
"""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

MODELS = ('m1-i95m', 'm1-wt')
ENVIRONMENT_DESIGN_SCHEMA = 'empirical-lawhood/rubisco-response/preparation-environment-design'
NOMINATION_SCHEMA = 'empirical-lawhood/rubisco-response/preparation-environment-nomination'
REGIONS = ('COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE', 'SELECTED_COMMON_PROTEIN_RESIDUES')
DISPOSITIONS = ('AVAILABLE', 'UNAVAILABLE_INITIAL_ACTIONS', 'INVALID_COORDINATE_CORRESPONDENCE',
    'NEGLIGIBLE_PROJECTED_RESPONSE', 'NUMERICALLY_UNRESOLVED')
MAX_SUPPORT_ATOMS = 4096


def _product(left, right):
    with localcontext() as context:
        context.prec = len(left.as_tuple().digits) + len(right.as_tuple().digits) + 2
        return left * right


@dataclass(frozen=True, slots=True)
class PreparationResponseEnvironment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-environment-support'
    environment_id: str
    region: str
    residue_keys: tuple[tuple[str, int], ...]
    representations: tuple[tuple[str, ObjectIdentity], ...]
    preparations: tuple[tuple[str, ObjectIdentity], ...]
    physical_atom_counts: tuple[tuple[str, int], ...]
    excluded_atom_indices: tuple[tuple[str, tuple[int, ...]], ...]
    # Logical chain, sequence position, atom name, element, I95M index, WT index.
    atom_pairs: tuple[tuple[str, int, str, int, int, int], ...]
    cell_lengths_angstrom: tuple[Decimal, Decimal, Decimal]
    coordinate_tolerance_angstrom: Decimal
    coordinate_convention: str = 'SAME_CARTESIAN_AXES_NO_FITTED_ALIGNMENT'
    nomination: str = 'NORMALIZED_INITIAL_WT_FINE_PRIMARY_ACTION_ON_DECLARED_COMMON_PROTEIN'
    minimum_projected_norm_hartree_per_bohr2: Decimal = Decimal('1e-12')
    scope: str = 'DECLARED_RECEIVER_ENVIRONMENT_DECOMPOSITION_NOT_A_MUTATION_MECHANISM'

    def __post_init__(self):
        validate_stable_id(self.environment_id)
        if self.region not in REGIONS or self.residue_keys != tuple(sorted(set(self.residue_keys))) or not self.residue_keys:
            raise ValueError('environment requires one prospective nonempty protein-residue region')
        for chain, position in self.residue_keys:
            validate_stable_id(chain)
            if type(position) is not int or position <= 0:
                raise ValueError('environment requires exact complete-sequence positions')
        for rows in (self.representations, self.preparations, self.physical_atom_counts, self.excluded_atom_indices):
            if type(rows) is not tuple or tuple(row[0] for row in rows) != MODELS:
                raise ValueError('environment omits its paired physical construction')
        for _, pin in (*self.representations, *self.preparations):
            exact(pin, ObjectIdentity)
        counts, excluded = dict(self.physical_atom_counts), dict(self.excluded_atom_indices)
        for model in MODELS:
            count = counts[model]
            if (type(count) is not int or count < 3 or not excluded[model]
                    or excluded[model] != tuple(sorted(set(excluded[model])))
                    or any(type(i) is not int or not 0 <= i < count for i in excluded[model])):
                raise ValueError('environment changes excluded physical atoms or population')
        if type(self.atom_pairs) is not tuple or not 0 < len(self.atom_pairs) <= MAX_SUPPORT_ATOMS:
            raise ValueError('environment requires 1..4096 common atoms; select explicit common protein residues without truncation')
        keys, mapped = [], {m: [] for m in MODELS}
        for chain, position, name, element, mutant, wt in self.atom_pairs:
            if ((chain, position) not in self.residue_keys or not isinstance(name, str) or not name
                    or type(element) is not int or not 1 <= element <= 118):
                raise ValueError('environment map escapes its declared chemical region')
            keys.append((chain, position, name))
            for model, index in zip(MODELS, (mutant, wt), strict=True):
                if type(index) is not int or not 0 <= index < counts[model] or index in excluded[model]:
                    raise ValueError('environment map includes a retained-core or receiver atom')
                mapped[model].append(index)
        if (keys != sorted(set(keys)) or {key[:2] for key in keys} != set(self.residue_keys)
                or any(len(indices) != len(set(indices)) for indices in mapped.values())):
            raise ValueError('environment map duplicates or omits an original atom correspondence')
        for value in (*self.cell_lengths_angstrom, self.coordinate_tolerance_angstrom,
                      self.minimum_projected_norm_hartree_per_bohr2):
            validate_decimal(value, field_name='environment_quantity', minimum=Decimal(0))
            if value == 0:
                raise ValueError('environment requires positive finite physical limits')
        if (len(self.cell_lengths_angstrom) != 3 or self.coordinate_tolerance_angstrom > Decimal('0.0001')
                or self.coordinate_convention != 'SAME_CARTESIAN_AXES_NO_FITTED_ALIGNMENT'
                or self.nomination != 'NORMALIZED_INITIAL_WT_FINE_PRIMARY_ACTION_ON_DECLARED_COMMON_PROTEIN'
                or self.scope != 'DECLARED_RECEIVER_ENVIRONMENT_DECOMPOSITION_NOT_A_MUTATION_MECHANISM'):
            raise ValueError('environment changes its fixed coordinate map or scientific interpretation')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.environment_id, self)


def _protein_residues(model):
    return {(r.chain_id, r.sequence_position_1based): r for r in model.residues if r.role == 'PROTEIN'}


def _atom_tables(model):
    tables = {}
    for index, atom in enumerate(model.atoms):
        tables.setdefault(atom.residue_id, {})[atom.name] = (index, atom)
    return tables


def _protein_bond_neighbourhoods(model):
    """Keep logical covalent neighbours and unknown native chemical order."""
    residues = {row.residue_id: row for row in model.residues}
    keys = {}
    for index, atom in enumerate(model.atoms):
        residue = residues[atom.residue_id]
        if residue.role == 'PROTEIN':
            keys[index] = (residue.chain_id, residue.sequence_position_1based, atom.name, atom.atomic_number)
    neighbours, nonprotein = {index: set() for index in keys}, set()
    for edge in model.bonds:
        for atom, other in ((edge.first, edge.second), (edge.second, edge.first)):
            if atom not in keys:
                continue
            if other not in keys:
                nonprotein.add(atom)
            else:
                neighbours[atom].add((keys[other], edge.order))
    return neighbours, nonprotein


def prepare_response_environment(*, models, preparations, prototypes, formation_coordinates,
        residue_keys=(), region='COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE',
        coordinate_tolerance_angstrom=Decimal('0.000001')):
    """Freeze complete unchanged protein residues before response acquisition.

    Whole residues touched by the selected retained site core are excluded.
    A covalent nonprotein connection requires a separately declared map.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model
    coordinates = dict(formation_coordinates)
    if any(set(rows) != set(MODELS) for rows in (models, preparations, prototypes, coordinates)) or region not in REGIONS:
        raise ValueError('environment support requires both exact original molecular preparations')
    excluded, residues, atom_tables, neighbourhoods = {}, {}, {}, {}
    for name in MODELS:
        model, prepared, prototype, coordinate = models[name], preparations[name], prototypes[name], coordinates[name]
        exact(model, MolecularRepresentation)
        exact(prepared, ActiveModelPreparation)
        validate_periodic_probe_model(prototype, model)
        if (prepared.representation != model.identity or prepared.prototype != prototype.identity
                or coordinate.representation != model.identity or coordinate.preparation != prepared.identity
                or prototype.molecular.constraints != 'NONE_NATURAL_MASSES'):
            raise ValueError('environment support changes its unconstrained original physical preparation')
        site, = (s for s in prepared.sites if s.identity == coordinate.prepared_site)
        core = {i for i in site.core_atom_indices if i < len(model.atoms)} | set(coordinate.native_atom_indices)
        core_residues = {model.atoms[i].residue_id for i in core}
        excluded[name] = tuple(i for i, atom in enumerate(model.atoms) if atom.residue_id in core_residues)
        residues[name], atom_tables[name] = _protein_residues(model), _atom_tables(model)
        neighbourhoods[name] = _protein_bond_neighbourhoods(model)
    lengths = prototypes[MODELS[0]].cell.lengths_angstrom
    if any(prototypes[m].cell.lengths_angstrom != lengths for m in MODELS):
        raise ValueError('environment transfer requires the same original Cartesian periodic cell')
    candidates = []
    for key in sorted(set(residues[MODELS[0]]) & set(residues[MODELS[1]])):
        pair = [residues[m][key] for m in MODELS]
        if (pair[0].component, pair[0].sequence_letter) != (pair[1].component, pair[1].sequence_letter):
            continue
        tables = [atom_tables[m][residue.residue_id] for m, residue in zip(MODELS, pair, strict=True)]
        if set(tables[0]) != set(tables[1]):
            continue
        if any(index in excluded[m] for m, table in zip(MODELS, tables, strict=True) for index, _ in table.values()):
            continue
        def chemistry(atom):
            return (atom.atomic_number, atom.mass_dalton, atom.charge_native, atom.charge_scale_per_electron, atom.parameter_type)
        if any(chemistry(tables[0][name][1]) != chemistry(tables[1][name][1]) for name in tables[0]):
            continue
        if any(tables[index][name][0] in neighbourhoods[model][1]
                for index, model in enumerate(MODELS) for name in tables[index]):
            continue
        if any(neighbourhoods[MODELS[0]][0][tables[0][name][0]]
                != neighbourhoods[MODELS[1]][0][tables[1][name][0]] for name in tables[0]):
            continue
        candidates.append((key, tables))
    if region == 'SELECTED_COMMON_PROTEIN_RESIDUES':
        if (type(residue_keys) is not tuple or not residue_keys or residue_keys != tuple(sorted(set(residue_keys)))
                or set(residue_keys) - {key for key, _ in candidates}):
            raise ValueError('selected environmental residues include absent, mutated, noncommon or retained-core chemistry')
        candidates = [(key, tables) for key, tables in candidates if key in residue_keys]
    elif residue_keys:
        raise ValueError('automatic common-protein support cannot silently override an explicit residue selection')
    atom_pairs = tuple((*key, name, tables[0][name][1].atomic_number, tables[0][name][0], tables[1][name][0])
        for key, tables in candidates for name in sorted(tables[0]))
    if len(atom_pairs) > MAX_SUPPORT_ATOMS:
        raise ValueError('environment support exceeds 4096 atoms; prospectively choose SELECTED_COMMON_PROTEIN_RESIDUES, without truncation')
    result = PreparationResponseEnvironment('environment.preparation-response.pending', region,
        tuple(key for key, _ in candidates), tuple((m, models[m].identity) for m in MODELS),
        tuple((m, preparations[m].identity) for m in MODELS), tuple((m, len(models[m].atoms)) for m in MODELS),
        tuple((m, excluded[m]) for m in MODELS), atom_pairs, lengths, coordinate_tolerance_angstrom)
    return replace(result, environment_id='environment.preparation-response.' + result.fingerprint())


def validate_response_environment_sources(*, environment, models, preparations, prototypes, formation_coordinates):
    """Reproduce the entire prospective selection from authenticated originals."""
    exact(environment, PreparationResponseEnvironment)
    expected = prepare_response_environment(models=models, preparations=preparations, prototypes=prototypes,
        formation_coordinates=formation_coordinates, region=environment.region,
        residue_keys=environment.residue_keys if environment.region == 'SELECTED_COMMON_PROTEIN_RESIDUES' else (),
        coordinate_tolerance_angstrom=environment.coordinate_tolerance_angstrom)
    if environment != expected:
        raise ValueError('environment support differs from its full authenticated paired construction')


def validate_environment_model(environment, model, model_name):
    """Rejoin selected indices to the complete authenticated physical atom map."""
    exact(environment, PreparationResponseEnvironment)
    if model_name not in MODELS or model.identity != dict(environment.representations)[model_name]:
        raise ValueError('environment substitutes its authenticated complete molecular representation')
    residues = {r.residue_id: r for r in model.residues}
    index_column, selected = 4 + MODELS.index(model_name), set()
    for pair in environment.atom_pairs:
        chain, position, name, element = pair[:4]
        atom = model.atoms[pair[index_column]]
        residue = residues[atom.residue_id]
        if (residue.role, residue.chain_id, residue.sequence_position_1based, atom.name, atom.atomic_number) != (
                'PROTEIN', chain, position, name, element):
            raise ValueError('environment substitutes a logical protein atom with an unrelated native index')
        selected.add(pair[index_column])
    expected = {i for i, atom in enumerate(model.atoms)
        if (residues[atom.residue_id].chain_id, residues[atom.residue_id].sequence_position_1based) in environment.residue_keys}
    if selected != expected:
        raise ValueError('environment changes the complete selected residue atom census')


def environment_coordinate_discrepancy(environment, coordinates):
    """Check the common Cartesian frame before buying primary forces."""
    import numpy as np
    exact(environment, PreparationResponseEnvironment)
    if set(coordinates) != set(MODELS):
        raise ValueError('environment coordinate check requires both original initial arrays')
    selected = []
    for model in MODELS:
        xyz = coordinates[model]
        if (not isinstance(xyz, np.ndarray) or xyz.dtype.str != '<f8'
                or xyz.shape != (dict(environment.physical_atom_counts)[model], 3) or not np.isfinite(xyz).all()):
            raise ValueError('environment coordinate check changes the complete finite original population')
        indices = [row[4 + MODELS.index(model)] for row in environment.atom_pairs]
        selected.append(xyz[indices])
    return Decimal.from_float(float(np.max(np.abs(selected[0] - selected[1]))))


@dataclass(frozen=True, slots=True)
class PreparationResponseEnvironmentNomination(CanonicalRecord):
    SCHEMA: ClassVar[str] = NOMINATION_SCHEMA
    nomination_id: str
    design: ObjectIdentity
    environment: ObjectIdentity
    initial_checkpoints: tuple[tuple[str, ObjectIdentity], ...]
    primary_actions: tuple[tuple[str, Decimal, ArrayDatasetManifest | None], ...]
    original_readouts: tuple[ObjectIdentity, ...]
    disposition: str
    projected_norm_hartree_per_bohr2: Decimal | None
    maximum_coordinate_discrepancy_angstrom: Decimal | None
    projected_discrepancies_hartree_per_bohr: tuple[tuple[str, Decimal | None], ...]
    numerical_allowance_hartree_per_bohr: Decimal
    candidate_components: tuple[tuple[str, tuple[tuple[int, int, Decimal], ...]], ...]
    native_force_uncertainty: str = 'UNAVAILABLE'
    fallback: str = 'NONE_RETAIN_NEGATIVE_OUTCOME'

    def __post_init__(self):
        validate_stable_id(self.nomination_id)
        for pin in (self.design, self.environment):
            exact(pin, ObjectIdentity)
        if (self.design.object_schema != ENVIRONMENT_DESIGN_SCHEMA
                or self.environment.object_schema != PreparationResponseEnvironment.SCHEMA
                or tuple(m for m, _ in self.initial_checkpoints) != MODELS
                or tuple(m for m, _ in self.projected_discrepancies_hartree_per_bohr) != MODELS
                or self.disposition not in DISPOSITIONS or self.native_force_uncertainty != 'UNAVAILABLE'
                or self.fallback != 'NONE_RETAIN_NEGATIVE_OUTCOME'):
            raise ValueError('environment nomination changes its declared original sources or negative outcomes')
        for _, pin in self.initial_checkpoints:
            exact(pin, ObjectIdentity)
        if (len(self.primary_actions) != 4 or tuple(m for m, _, _ in self.primary_actions) != (MODELS[0],) * 2 + (MODELS[1],) * 2
                or self.original_readouts != tuple(sorted(set(self.original_readouts), key=lambda p: p.object_id))):
            raise ValueError('environment nomination drops or changes original initial-primary evidence')
        for _, step, action in self.primary_actions:
            validate_decimal(step, field_name='nomination_step', minimum=Decimal(0))
            if action is not None:
                exact(action, ArrayDatasetManifest)
        for value in (self.projected_norm_hartree_per_bohr2, self.maximum_coordinate_discrepancy_angstrom,
                      self.numerical_allowance_hartree_per_bohr,
                      *(value for _, value in self.projected_discrepancies_hartree_per_bohr)):
            if value is not None:
                validate_decimal(value, field_name='nomination_quantity', minimum=Decimal(0))
        if self.candidate_components and tuple(m for m, _ in self.candidate_components) != MODELS:
            raise ValueError('environment nomination loses its paired shared direction')
        for _, components in self.candidate_components:
            if not components or tuple((a, b) for a, b, _ in components) != tuple(sorted({(a, b) for a, b, _ in components})):
                raise ValueError('environment nomination repeats or omits Cartesian components')
            for atom, axis, value in components:
                if type(atom) is not int or atom < 0 or type(axis) is not int or not 0 <= axis < 3:
                    raise ValueError('environment nomination changes Cartesian component roles')
                validate_decimal(value, field_name='nomination_component')
        if self.disposition == 'AVAILABLE' and (not self.candidate_components or len(self.original_readouts) != 8
                or any(action is None for _, _, action in self.primary_actions)
                or any(value is None for _, value in self.projected_discrepancies_hartree_per_bohr)):
            raise ValueError('available environment nomination lacks complete initial evidence')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.nomination_id, self)


def nominate_response_environment(*, design, centers, frames, center_arrays, actions, action_values, readouts):
    """Reconstruct the sole nomination from original initial evidence only."""
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental, response_effects
    if not is_environmental(design):
        raise ValueError('environment nomination requires the prospectively selected environmental design')
    environment = design.environment
    primary = tuple((model, step, next(row.action for row in actions if
        (row.model_name, row.position, row.direction, row.step_bohr) == (model, 'initial', 'primary', step)))
        for model in MODELS for step in design.steps_bohr)
    evidence = tuple(sorted((readouts[e.effect_id].identity for e in response_effects(design, 'initial-primary')
        if e.effect_id in readouts), key=lambda p: p.object_id))
    allowed = _product(design.useful_error_hartree_per_bohr, design.numerical_allowance_fraction)
    initial_coordinates = {m: center_arrays[m, 'initial'][0] for m in MODELS}
    mismatch = environment_coordinate_discrepancy(environment, initial_coordinates)
    status = ('INVALID_COORDINATE_CORRESPONDENCE' if mismatch > environment.coordinate_tolerance_angstrom
        else 'UNAVAILABLE_INITIAL_ACTIONS')
    norm, discrepancies, components = None, tuple((m, None) for m in MODELS), ()
    if status != 'INVALID_COORDINATE_CORRESPONDENCE' and all(action is not None for _, _, action in primary) and len(evidence) == 8:
        big, small = design.steps_bohr
        status, norm, mismatch, discrepancies, components = _environmental_candidate(environment=environment,
            coordinates=initial_coordinates,
            fine_actions={m: action_values[m, 'initial', 'primary', small] for m in MODELS},
            coarse_actions={m: action_values[m, 'initial', 'primary', big] for m in MODELS},
            amplitude=design.challenge_amplitude_bohr, allowance=allowed)
    result = PreparationResponseEnvironmentNomination('nomination.preparation-environment.pending', design.identity,
        environment.identity, tuple((m, centers[m, 'initial'].checkpoint.identity) for m in MODELS), primary,
        evidence, status, norm, mismatch, discrepancies, allowed, components)
    return replace(result, nomination_id='nomination.preparation-environment.' + result.fingerprint())


def _environmental_candidate(*, environment, coordinates, fine_actions, coarse_actions, amplitude, allowance):
    """Numerical nomination; the caller owns original-source authentication."""
    import numpy as np
    exact(environment, PreparationResponseEnvironment)
    indices = {model: [p[4 + MODELS.index(model)] for p in environment.atom_pairs] for model in MODELS}
    mismatch = environment_coordinate_discrepancy(environment, coordinates)
    empty_checks = tuple((m, None) for m in MODELS)
    if mismatch > environment.coordinate_tolerance_angstrom:
        return 'INVALID_COORDINATE_CORRESPONDENCE', None, mismatch, empty_checks, ()
    retained = np.asarray(fine_actions['m1-wt'][indices['m1-wt']], dtype='<f8')
    norm_float = float(np.linalg.norm(retained))
    if not np.isfinite(norm_float):
        raise ValueError('environmental projection norm is nonfinite')
    norm = Decimal.from_float(norm_float)
    if norm <= environment.minimum_projected_norm_hartree_per_bohr2 or _product(amplitude, norm) <= allowance:
        return 'NEGLIGIBLE_PROJECTED_RESPONSE', norm, mismatch, empty_checks, ()
    direction = retained / norm_float
    candidates, checks = [], []
    for model in MODELS:
        components = tuple(sorted((index, axis, Decimal.from_float(float(direction[row, axis])))
            for row, index in enumerate(indices[model]) for axis in range(3) if direction[row, axis] != 0))
        candidates.append((model, components))
        discrepancy = float(amplitude) * abs(np.vdot(direction, (fine_actions[model] - coarse_actions[model])[indices[model]]))
        if not np.isfinite(discrepancy):
            raise ValueError('environmental projected scale discrepancy is nonfinite')
        checks.append((model, Decimal.from_float(float(discrepancy))))
    status = 'NUMERICALLY_UNRESOLVED' if any(value > allowance for _, value in checks) else 'AVAILABLE'
    return status, norm, mismatch, tuple(checks), tuple(candidates)


def validate_nomination_components(design, nomination):
    """Require exact common Cartesian transfer without mutant renormalization."""
    values = dict(nomination.candidate_components)
    if not values:
        return
    environment = design.environment
    transfer = {row[5]: row[4] for row in environment.atom_pairs}
    expected = tuple(sorted((transfer[atom], axis, value) for atom, axis, value in values['m1-wt'] if atom in transfer))
    if (len(expected) != len(values['m1-wt']) or values['m1-i95m'] != expected
            or any(atom in dict(environment.excluded_atom_indices)['m1-wt'] for atom, _, _ in values['m1-wt'])):
        raise ValueError('environment nomination changes its one shared signed Cartesian direction')


def prepare_environmental_frames(*, design, frames, nomination):
    """Apply one original nominee to both genotypes and both checkpoints."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import PeriodicPhysicalDirection
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental, primary_response_frame
    exact(nomination, PreparationResponseEnvironmentNomination)
    if (not is_environmental(design) or nomination.design != design.identity
            or nomination.environment != design.environment.identity or nomination.disposition != 'AVAILABLE'
            or set(frames) != set(MODELS)):
        raise ValueError('environmental frame requires its original available shared nomination')
    validate_nomination_components(design, nomination)
    components, result = dict(nomination.candidate_components), {}
    for model in MODELS:
        frame = primary_response_frame(frames[model])
        if (frame.design != design.identity or frame.initial_checkpoint != dict(nomination.initial_checkpoints)[model]
                or frame.primary.physical_atom_count != dict(design.environment.physical_atom_counts)[model]):
            raise ValueError('environmental frame changes its original initial population')
        if any(frame.primary.identity not in action.scientific_references
                for name, _, action in nomination.primary_actions if name == model):
            raise ValueError('environmental frame substitutes its original initial primary direction')
        selected = {row[4 + MODELS.index(model)] for row in design.environment.atom_pairs}
        if any(atom not in selected for atom, _, _ in components[model]):
            raise ValueError('environmental direction escapes its prospective support')
        direction = PeriodicPhysicalDirection('direction.preparation-environment.pending',
            frame.coordinate.representation, frame.primary.coordinates, nomination.identity,
            frame.primary.physical_atom_count, components[model])
        direction = replace(direction, direction_id='direction.preparation-environment.' + direction.fingerprint())
        final = replace(frame, frame_id='frame.preparation-response.pending', additional=direction, challenge=direction)
        result[model] = replace(final, frame_id='frame.preparation-response.' + final.fingerprint())
    return result


def validate_environmental_frame(*, design, frame, nomination):
    """Reproduce this frame without fitting or renormalizing another direction."""
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import primary_response_frame
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import PeriodicPhysicalDirection
    exact(nomination, PreparationResponseEnvironmentNomination)
    if (nomination.design != design.identity or nomination.environment != design.environment.identity
            or nomination.disposition != 'AVAILABLE'):
        raise ValueError('environmental frame substitutes its original available nomination')
    validate_nomination_components(design, nomination)
    base = primary_response_frame(frame)
    if base.initial_checkpoint != dict(nomination.initial_checkpoints)[frame.model_name]:
        raise ValueError('environmental frame changes its initial checkpoint')
    if any(base.primary.identity not in action.scientific_references
            for name, _, action in nomination.primary_actions if name == frame.model_name):
        raise ValueError('environmental frame substitutes its original initial primary direction')
    components = dict(nomination.candidate_components)[frame.model_name]
    support = {row[4 + MODELS.index(frame.model_name)] for row in design.environment.atom_pairs}
    if any(atom not in support for atom, _, _ in components):
        raise ValueError('environmental frame escapes its prospectively selected protein support')
    direction = PeriodicPhysicalDirection('direction.preparation-environment.pending', base.coordinate.representation,
        base.primary.coordinates, nomination.identity, base.primary.physical_atom_count, components)
    direction = replace(direction, direction_id='direction.preparation-environment.' + direction.fingerprint())
    expected = replace(base, frame_id='frame.preparation-response.pending', additional=direction, challenge=direction)
    expected = replace(expected, frame_id='frame.preparation-response.' + expected.fingerprint())
    if frame != expected:
        raise ValueError('environmental frame substitutes or renormalizes the original common direction')
