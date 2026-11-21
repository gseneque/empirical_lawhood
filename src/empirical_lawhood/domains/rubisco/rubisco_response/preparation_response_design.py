# SPDX-License-Identifier: MPL-2.0
"""Frozen paired formation-response design and its exact finite effect census."""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ScientificConditionScope
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint, HARTREE_KJ_MOL
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_selection import ActivePreparationPrefixSelection
from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import PreparedFormationCoordinate
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootScopedAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import PeriodicPhysicalDirection
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import ENVIRONMENT_DESIGN_SCHEMA, NOMINATION_SCHEMA, PreparationResponseEnvironment

MODELS = ('m1-i95m', 'm1-wt')
POSITIONS = tuple((model, position) for model in MODELS for position in ('initial', 'later'))


@dataclass(frozen=True, slots=True)
class PreparationResponseDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-design'
    design_id: str
    prefix: ActivePreparationPrefixSelection
    root_assessment: ObjectIdentity
    formation_coordinates: tuple[tuple[str, PreparedFormationCoordinate], ...]
    steps_bohr: tuple[Decimal, Decimal]
    challenge_amplitude_bohr: Decimal
    reference_temperature_kelvin: Decimal
    useful_error_work_fraction_rt: Decimal
    numerical_allowance_fraction: Decimal
    receiver: str = 'MINUS_COMPLETE_NATIVE_GRADIENT_DOT_FIXED_INITIAL_FORMATION_UNIT_DIRECTION'
    additional_direction: str = 'ORTHOGONALIZED_GRADIENT_OF_DISTANCE_C3_H3_PLUS_DISTANCE_H3_KCX_O'
    challenge_direction: str = 'UNIT_SUM_OF_FIXED_INITIAL_PRIMARY_AND_ADDITIONAL_DIRECTIONS'
    error_convention: str = 'OBSERVED_RECEIVER_CHANGE_MINUS_FROZEN_PREDICTED_CHANGE'
    mutation_error_convention: str = 'I95M_ERROR_MINUS_WT_ERROR'
    scope: str = 'ONE_MATCHED_CONSTRUCTION_FOUR_NESTED_STATES_NO_POPULATION_OR_KINETIC_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.design_id)
        exact(self.prefix, ActivePreparationPrefixSelection)
        exact(self.root_assessment, ObjectIdentity)
        if (self.root_assessment.object_schema != InitialRootScopedAssessment.SCHEMA
                or self.root_assessment.object_version != InitialRootScopedAssessment.VERSION
                or self.prefix.conditional.state_census[0][1:] != ('keto-hie', 'AS_CONSTRUCTED')
                or type(self.formation_coordinates) is not tuple
                or tuple(row[0] for row in self.formation_coordinates) != MODELS):
            raise ValueError('response design changes its paired original chemical case or root assessment')
        for _, coordinate in self.formation_coordinates:
            exact(coordinate, PreparedFormationCoordinate)
            if coordinate.site_id != self.prefix.conditional.state_census[0][0]:
                raise ValueError('response design changes its matched physical atom roles')
        if type(self.steps_bohr) is not tuple or len(self.steps_bohr) != 2:
            raise ValueError('response design needs two explicit primary scales')
        for value in (*self.steps_bohr, self.challenge_amplitude_bohr, self.reference_temperature_kelvin,
                      self.useful_error_work_fraction_rt, self.numerical_allowance_fraction):
            validate_decimal(value, field_name='response_design_quantity', minimum=Decimal(0))
            if value == 0:
                raise ValueError('response design requires positive physical and comparison quantities')
        if (self.steps_bohr[0] != 2 * self.steps_bohr[1]
                or self.challenge_amplitude_bohr < 5 * self.steps_bohr[0]
                or self.numerical_allowance_fraction >= 1 or self.useful_error_work_fraction_rt > 1
                or self.receiver != 'MINUS_COMPLETE_NATIVE_GRADIENT_DOT_FIXED_INITIAL_FORMATION_UNIT_DIRECTION'
                or self.additional_direction != ('INITIAL_WT_ACTION_ON_FROZEN_COMMON_PROTEIN_SUPPORT'
                    if self.SCHEMA == ENVIRONMENT_DESIGN_SCHEMA else 'ORTHOGONALIZED_GRADIENT_OF_DISTANCE_C3_H3_PLUS_DISTANCE_H3_KCX_O')
                or self.challenge_direction != ('PURE_FIXED_COMMON_ENVIRONMENTAL_DIRECTION'
                    if self.SCHEMA == ENVIRONMENT_DESIGN_SCHEMA else 'UNIT_SUM_OF_FIXED_INITIAL_PRIMARY_AND_ADDITIONAL_DIRECTIONS')
                or self.error_convention != 'OBSERVED_RECEIVER_CHANGE_MINUS_FROZEN_PREDICTED_CHANGE'
                or self.mutation_error_convention != 'I95M_ERROR_MINUS_WT_ERROR'
                or self.scope != 'ONE_MATCHED_CONSTRUCTION_FOUR_NESTED_STATES_NO_POPULATION_OR_KINETIC_ADMISSION'):
            raise ValueError('response design changes its distinct finite challenge, sign or evidence scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.design_id, self)

    @property
    def useful_error_hartree_per_bohr(self):
        # A selected work-equivalent tolerance, not an activation-energy bound.
        with localcontext() as context:
            context.prec = 50
            return +(self.useful_error_work_fraction_rt * Decimal('0.00831446261815324')
                * self.reference_temperature_kelvin / Decimal.from_float(HARTREE_KJ_MOL)
                / self.challenge_amplitude_bohr)


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentalPreparationResponseDesign(PreparationResponseDesign):
    """A distinct environmental question with a frozen WT-nominated direction."""
    SCHEMA: ClassVar[str] = ENVIRONMENT_DESIGN_SCHEMA
    environment: PreparationResponseEnvironment

    def __post_init__(self):
        PreparationResponseDesign.__post_init__(self)
        exact(self.environment, PreparationResponseEnvironment)
        for model, coordinate in self.formation_coordinates:
            if (coordinate.representation != dict(self.environment.representations)[model]
                    or coordinate.preparation != dict(self.environment.preparations)[model]
                    or coordinate.physical_atom_count != dict(self.environment.physical_atom_counts)[model]
                    or not set(coordinate.native_atom_indices).issubset(dict(self.environment.excluded_atom_indices)[model])):
                raise ValueError('environmental design changes its prospective physical support or receiver exclusion')


def is_environmental(design):
    return type(design) is EnvironmentalPreparationResponseDesign


def require_response_design(design):
    if type(design) not in (PreparationResponseDesign, EnvironmentalPreparationResponseDesign):
        raise ValueError('response requires one exact registered local or environmental design')
    exact(design, type(design))


def response_stages(design):
    require_response_design(design)
    return (*diagnostic_stages(design), 'challenge', 'additional-refinement')


def diagnostic_stages(design):
    require_response_design(design)
    return ('initial-primary', 'environment-diagnostic') if is_environmental(design) else ('diagnostic',)


def prepare_response_design(*, prefix, root_assessment, formation_coordinates,
        steps_bohr=(Decimal('0.02'), Decimal('0.01')), challenge_amplitude_bohr=Decimal('0.2'),
        reference_temperature_kelvin=Decimal('298.15'), useful_error_work_fraction_rt=Decimal('0.1'),
        numerical_allowance_fraction=Decimal('0.1'), environment=None):
    kind = PreparationResponseDesign if environment is None else EnvironmentalPreparationResponseDesign
    options = {} if environment is None else dict(environment=environment,
        additional_direction='INITIAL_WT_ACTION_ON_FROZEN_COMMON_PROTEIN_SUPPORT',
        challenge_direction='PURE_FIXED_COMMON_ENVIRONMENTAL_DIRECTION')
    provisional = kind('design.preparation-response.pending', prefix, root_assessment,
        formation_coordinates, steps_bohr, challenge_amplitude_bohr, reference_temperature_kelvin,
        useful_error_work_fraction_rt, numerical_allowance_fraction, **options)
    return replace(provisional, design_id='design.preparation-response.' + provisional.fingerprint())


@dataclass(frozen=True, slots=True)
class PreparationResponseContext(CanonicalRecord):
    """Bind the local investigation to an actual unresolved root contribution."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-context'
    design: PreparationResponseDesign | EnvironmentalPreparationResponseDesign
    original_root: InitialRootScopedAssessment
    parent: ContributionManifest

    def __post_init__(self):
        require_response_design(self.design)
        exact(self.original_root, InitialRootScopedAssessment)
        exact(self.parent, ContributionManifest)
        if (self.design.root_assessment != self.original_root.identity or self.parent.scope != self.original_root.scope
                or self.original_root.joint_outcome != 'UNRESOLVED'
                or len([row for row in self.parent.products if row.record == self.original_root.identity]) != 1
                or not any(row.requirement_id.endswith('actual-paired-physical-preparation') for row in self.parent.remaining_requirements)):
            raise ValueError('response context loses its actual unresolved root or physical preparation requirement')

    @property
    def identity(self):
        return ObjectIdentity.from_record('context.preparation-response.' + self.fingerprint(), self)


def response_scope(design):
    require_response_design(design)
    return ScientificConditionScope(design.prefix.plan.object_id, 'world.periodic-gp-preparation-response',
        design.identity.object_id, ('receiver-force-change',), ('hartree/bohr',),
        'receiver.rubisco.fixed-initial-formation-force', 'clock.rubisco.preparation-information-order',
        ('Fixed initial formation receivers, one common protein direction selected from initial WT actions, '
         if is_environmental(design) else 'Fixed initial chemical directions, ')
        + 'two accepted positions per genotype, and one same finite Cartesian challenge. '
        'Preparation order is not physical time; no equilibrium mean, population or rate admission.',
        source_config_sha256=design.fingerprint(), instance_id=design.design_id,
        population_id='population.one-matched-construction-no-biological-replicates', uncertainty_contract=design.identity)


@dataclass(frozen=True, slots=True)
class PreparationResponseEffect(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-effect'
    effect_id: str
    design: ObjectIdentity
    stage: str
    ordinal: int
    model_name: str
    position: str
    direction: str
    signed_step_bohr: Decimal

    def __post_init__(self):
        validate_stable_id(self.effect_id)
        exact(self.design, ObjectIdentity)
        validate_decimal(self.signed_step_bohr, field_name='signed_step_bohr')
        if (self.stage not in ('diagnostic', 'initial-primary', 'environment-diagnostic', 'challenge', 'additional-refinement')
                or self.model_name not in MODELS or self.position not in ('initial', 'later')
                or self.direction not in ('primary', 'additional', 'challenge')
                or type(self.ordinal) is not int or self.ordinal < 0 or self.signed_step_bohr == 0):
            raise ValueError('response effect changes its selected physical coordinates')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.effect_id, self)


def response_effects(design, stage):
    """Derive 20 diagnostic, four challenge or four optional refinement effects."""
    require_response_design(design)
    if stage not in response_stages(design):
        raise ValueError('response stage changes its prospectively selected acquisition sequence')
    if stage == 'diagnostic':
        rows = [(model, position, 'primary', sign * step) for model, position in POSITIONS
            for step in design.steps_bohr for sign in (-1, 1)]
        rows += [(model, 'later', 'additional', sign * design.steps_bohr[0]) for model in MODELS for sign in (-1, 1)]
    elif stage == 'initial-primary':
        rows = [(model, 'initial', 'primary', sign * step) for model in MODELS
            for step in design.steps_bohr for sign in (-1, 1)]
    elif stage == 'environment-diagnostic':
        rows = [(model, 'later', 'primary', sign * step) for model in MODELS
            for step in design.steps_bohr for sign in (-1, 1)]
        rows += [(model, 'later', 'additional', sign * design.steps_bohr[0]) for model in MODELS for sign in (-1, 1)]
    elif stage == 'challenge':
        rows = [(model, position, 'challenge', design.challenge_amplitude_bohr) for model, position in POSITIONS]
    elif stage == 'additional-refinement':
        rows = [(model, 'later', 'additional', sign * design.steps_bohr[1]) for model in MODELS for sign in (-1, 1)]
    else:
        raise ValueError('response design has no selected effect stage')
    return tuple(PreparationResponseEffect('effect.preparation-response.' + design.fingerprint() + '.' + stage + '.' + f'{i:02d}',
        design.identity, stage, i, model, position, direction, step)
        for i, (model, position, direction, step) in enumerate(rows))


@dataclass(frozen=True, slots=True)
class PreparationResponseFrame(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-frame'
    frame_id: str
    design: ObjectIdentity
    model_name: str
    initial_checkpoint: ObjectIdentity
    coordinate: PreparedFormationCoordinate
    primary: PeriodicPhysicalDirection
    additional: PeriodicPhysicalDirection | None
    challenge: PeriodicPhysicalDirection | None

    def __post_init__(self):
        validate_stable_id(self.frame_id)
        for pin in (self.design, self.initial_checkpoint):
            exact(pin, ObjectIdentity)
        exact(self.coordinate, PreparedFormationCoordinate)
        if self.model_name not in MODELS or self.initial_checkpoint.object_schema != ActivePreparationCheckpoint.SCHEMA:
            raise ValueError('response frame changes its actual initial state')
        environmental = self.design.object_schema == ENVIRONMENT_DESIGN_SCHEMA
        if environmental and ((self.additional is None) != (self.challenge is None)
                or self.additional != self.challenge):
            raise ValueError('environmental frame requires one shared pure direction or the pending primary frame')
        for role, direction in (('primary', self.primary), ('additional', self.additional), ('challenge', self.challenge)):
            if environmental and role != 'primary' and direction is None:
                continue
            exact(direction, PeriodicPhysicalDirection)
            source_valid = (direction.source.object_schema == NOMINATION_SCHEMA if environmental and role != 'primary'
                else direction.source == self.coordinate.identity)
            if (direction.representation != self.coordinate.representation or not source_valid
                    or direction.physical_atom_count != self.coordinate.physical_atom_count
                    or direction.coordinates != self.primary.coordinates
                    or direction.coordinates.scientific_references != (self.initial_checkpoint,)):
                raise ValueError('response frame changes its fixed initial atom population or source')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.frame_id, self)


def primary_response_frame(frame):
    """Recover the exact immutable frame used before environmental nomination."""
    exact(frame, PreparationResponseFrame)
    if frame.design.object_schema != ENVIRONMENT_DESIGN_SCHEMA or frame.additional is None:
        return frame
    provisional = replace(frame, frame_id='frame.preparation-response.pending', additional=None, challenge=None)
    return replace(provisional, frame_id='frame.preparation-response.' + provisional.fingerprint())


def validate_environmental_primary_frame(*, design, frame, coordinates):
    """Reconstruct the initial formation receiver from authenticated geometry."""
    import numpy as np
    if not is_environmental(design):
        raise ValueError('environmental primary-frame validation requires its selected design')
    frame = primary_response_frame(frame)
    if (frame.design != design.identity or frame.coordinate != dict(design.formation_coordinates)[frame.model_name]
            or coordinates.shape != (frame.coordinate.physical_atom_count, 3)):
        raise ValueError('environmental primary frame changes original physical receiver roles')
    primary, *_ = _formation_vectors(coordinates, frame.coordinate,
        np.array(tuple(map(float, design.environment.cell_lengths_angstrom))))
    components = tuple(sorted((atom, axis, Decimal.from_float(float(primary[row, axis])))
        for row, atom in enumerate(frame.coordinate.native_atom_indices) for axis in range(3) if primary[row, axis] != 0))
    member, = frame.primary.coordinates.members
    if (member.sha256 != sha256(coordinates.tobytes()).hexdigest() or frame.primary.components != components):
        raise ValueError('environmental primary frame substitutes its fixed initial formation gradient')


def _formation_vectors(xyz, coordinate, lengths):
    """One physical-direction implementation for design review and native queries."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import _bond
    carbon, hydrogen, oxygen = coordinate.native_atom_indices
    _, first, a = _bond(xyz[carbon], xyz[hydrogen], lengths)
    _, second, b = _bond(xyz[hydrogen], xyz[oxygen], lengths)
    u = np.array((a, -a - b, b), dtype='<f8')
    v = np.array((a, -a + b, -b), dtype='<f8')
    primary_norm = np.linalg.norm(u)
    u /= primary_norm
    v -= np.vdot(u, v) * u
    additional_norm = np.linalg.norm(v)
    if not np.isfinite((primary_norm, additional_norm)).all() or min(primary_norm, additional_norm) <= 1e-12:
        raise ValueError('formation directions lack distinct finite physical support')
    v /= additional_norm
    return u, v, (u + v) / np.sqrt(2.), first, second, primary_norm, additional_norm


@dataclass(frozen=True, slots=True)
class PreparationResponseGeometryReview(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-geometry-review'
    design: ObjectIdentity
    model_name: str
    prototype: ObjectIdentity
    seed: ObjectIdentity
    coordinate: PreparedFormationCoordinate
    initial_coordinate_sha256: str
    quantities: tuple[tuple[str, Decimal], ...]
    scope: str = 'RETAINED_GEOMETRY_DESIGN_REVIEW_WITHOUT_FORCE_OR_POPULATION_ADMISSION'

    def __post_init__(self):
        from empirical_lawhood.science.records.serialization import validate_sha256
        for pin in (self.design, self.prototype, self.seed):
            exact(pin, ObjectIdentity)
        exact(self.coordinate, PreparedFormationCoordinate)
        validate_sha256(self.initial_coordinate_sha256)
        names = ('challenge-c3-h3-angstrom', 'challenge-h3-oxygen-angstrom', 'challenge-xi-change-angstrom',
            'initial-c3-h3-angstrom', 'initial-h3-oxygen-angstrom', 'linear-xi-change-angstrom',
            'maximum-atom-displacement-angstrom', 'primary-additional-overlap', 'primary-gradient-norm')
        if (self.model_name not in MODELS or tuple(name for name, _ in self.quantities) != names
                or self.seed != self.coordinate.state_seeds[0]
                or self.scope != 'RETAINED_GEOMETRY_DESIGN_REVIEW_WITHOUT_FORCE_OR_POPULATION_ADMISSION'):
            raise ValueError('response geometry review changes its actual source or physical question')
        for _, value in self.quantities:
            validate_decimal(value, field_name='geometry_review_quantity')

    @property
    def identity(self):
        return ObjectIdentity.from_record('geometry.response-design.' + self.fingerprint(), self)


def review_response_initial_geometry(*, design, model_name, representation, prepared, prototype, coordinate_bytes):
    """Assess the proposed amplitude on original geometry without a force call."""
    import numpy as np
    if is_environmental(design):
        raise ValueError('environmental challenge geometry is unavailable before the initial-action nomination')
    from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import verified_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import expand_state_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import BOHR_ANGSTROM
    validate_periodic_probe_model(prototype, representation)
    verified_coordinates(representation, coordinate_bytes)
    coordinate = dict(design.formation_coordinates)[model_name]
    if (coordinate.representation != representation.identity or coordinate.preparation != prepared.identity
            or prepared.prototype != prototype.identity):
        raise ValueError('response design review substitutes its original physical preparation')
    seed, = (s for s in prepared.seeds if s.identity == coordinate.state_seeds[0])
    xyz = expand_state_coordinates(seed, coordinate_bytes)
    lengths = np.array(tuple(map(float, prototype.cell.lengths_angstrom)))
    u, v, w, first, second, norm, _ = _formation_vectors(xyz, coordinate, lengths)
    delta = float(design.challenge_amplitude_bohr * BOHR_ANGSTROM) * w
    displaced = xyz.copy()
    displaced[list(coordinate.native_atom_indices)] += delta
    _, _, _, final_first, final_second, _, _ = _formation_vectors(displaced, coordinate, lengths)
    quantities = dict(
        **{'initial-c3-h3-angstrom': first, 'initial-h3-oxygen-angstrom': second,
           'challenge-c3-h3-angstrom': final_first, 'challenge-h3-oxygen-angstrom': final_second,
           'challenge-xi-change-angstrom': (final_first - final_second) - (first - second),
           'linear-xi-change-angstrom': norm * np.vdot(u, delta),
           'maximum-atom-displacement-angstrom': np.max(np.linalg.norm(delta, axis=1)),
           'primary-additional-overlap': np.vdot(u, v), 'primary-gradient-norm': norm})
    return PreparationResponseGeometryReview(design.identity, model_name, prototype.identity, seed.identity,
        coordinate, sha256(xyz.tobytes()).hexdigest(),
        tuple((name, Decimal.from_float(float(value))) for name, value in sorted(quantities.items())))


def prepare_response_frame(*, design, model_name, checkpoint, arrays, prototype):
    """Construct fixed chemical directions from the independently read initial state."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import read_checkpoint_arrays
    require_response_design(design)
    if model_name not in MODELS or checkpoint.iterations != 0 or checkpoint.prototype != prototype.identity:
        raise ValueError('response frame requires the actual initial accepted state and operator')
    read_checkpoint_arrays(checkpoint, arrays, configuration=checkpoint.configuration,
                           seed=checkpoint.seed, prototype=prototype.identity)
    coordinate = dict(design.formation_coordinates)[model_name]
    if (coordinate.representation != prototype.representation or checkpoint.seed != coordinate.state_seeds[0]
            or prototype.molecular.constraints != 'NONE_NATURAL_MASSES'):
        raise ValueError('response frame changes its selected physical chemical roles or constraints')
    xyz = arrays['coordinates-angstrom']
    member = ArrayDatasetMember('coordinates', '<f8', xyz.shape, sha256(xyz.tobytes()).hexdigest())
    coordinates = ArrayDatasetManifest('arrays.response-frame.' + checkpoint.fingerprint(), (member,), (checkpoint.identity,))
    lengths = np.array(tuple(map(float, prototype.cell.lengths_angstrom)))
    u, v, w, *_ = _formation_vectors(xyz, coordinate, lengths)
    directions = []
    for role, value in (('primary', u), ('additional', v), ('challenge', w)):
        if is_environmental(design) and role != 'primary':
            directions.append(None)
            continue
        components = tuple(sorted((atom, axis, Decimal.from_float(float(value[i, axis])))
            for i, atom in enumerate(coordinate.native_atom_indices) for axis in range(3) if value[i, axis] != 0))
        provisional = PeriodicPhysicalDirection('direction.preparation-response.' + role + '.pending',
            coordinate.representation, coordinates, coordinate.identity, len(xyz), components)
        directions.append(replace(provisional, direction_id='direction.preparation-response.' + role + '.' + provisional.fingerprint()))
    provisional = PreparationResponseFrame('frame.preparation-response.pending', design.identity, model_name,
        checkpoint.identity, coordinate, *directions)
    return replace(provisional, frame_id='frame.preparation-response.' + provisional.fingerprint())
