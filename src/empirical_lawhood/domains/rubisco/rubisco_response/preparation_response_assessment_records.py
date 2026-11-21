# SPDX-License-Identifier: MPL-2.0
"""Immutable six-question records shared by acquisition and assessment owners."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, POSITIONS, PreparationResponseDesign, EnvironmentalPreparationResponseDesign, require_response_design, response_effects, response_stages
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import PreparationResponseEnvironmentNomination

UNCERTAINTY = ('Two-scale sensitivity is an empirical discrepancy, not a rigorous derivative enclosure. '
    'Native force uncertainty is unavailable. Four positions are nested within one matched construction; '
    'no biological confidence interval, population or kinetic admission follows.')
LABELS = ('Numerical consistency', 'Omitted receiver coupling', 'Operator change during preparation',
          'Withheld finite response', 'Paired WT/I95M error', 'Preparation benefit')


@dataclass(frozen=True, slots=True)
class PreparationResponseQuantity(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-quantity'
    name: str
    model_name: str
    position: str
    value: Decimal | None
    unit: str

    def __post_init__(self):
        validate_stable_id(self.name)
        if self.model_name not in (*MODELS, 'I95M-minus-WT') or self.position not in ('initial', 'later', 'later-minus-initial'):
            raise ValueError('response quantity changes its paired nested comparison')
        if self.value is not None:
            validate_decimal(self.value, field_name='response_quantity')
        if self.unit not in ('hartree/bohr', 'hartree/bohr2', 'dimensionless', 'bohr', 'cpu-seconds', 'wall-seconds', 'bytes'):
            raise ValueError('response quantity loses its physical or operational unit')


@dataclass(frozen=True, slots=True)
class PreparationResponseAction(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-action'
    model_name: str
    position: str
    direction: str
    step_bohr: Decimal
    minus_effect: ObjectIdentity
    plus_effect: ObjectIdentity
    action: ArrayDatasetManifest | None
    maximum_secant_direction_error: Decimal | None
    maximum_midpoint_shift_bohr: Decimal | None

    def __post_init__(self):
        if ((self.model_name, self.position) not in POSITIONS or self.direction not in ('primary', 'additional')
                or self.direction == 'additional' and self.position != 'later'):
            raise ValueError('response action changes its assigned physical comparison')
        validate_decimal(self.step_bohr, field_name='response_step', minimum=Decimal(0))
        if self.step_bohr == 0:
            raise ValueError('response action needs a positive original displacement')
        for pin in (self.minus_effect, self.plus_effect):
            exact(pin, ObjectIdentity)
        if self.action is not None:
            exact(self.action, ArrayDatasetManifest)
        for value in (self.maximum_secant_direction_error, self.maximum_midpoint_shift_bohr):
            if (value is None) != (self.action is None):
                raise ValueError('response action invents a coordinate comparison without both complete forces')
            if value is not None:
                validate_decimal(value, field_name='response_coordinate_discrepancy', minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class PreparationResponseCoverage(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-coverage'
    effect: ObjectIdentity
    stage: str
    state: str
    point: ObjectIdentity | None
    original_readout: ObjectIdentity | None

    def __post_init__(self):
        exact(self.effect, ObjectIdentity)
        if (self.stage not in ('diagnostic', 'initial-primary', 'environment-diagnostic', 'challenge', 'additional-refinement')
                or self.state not in ('NOT_SELECTED', 'NOT_ENTERED', 'UNAVAILABLE', 'AVAILABLE')
                or (self.original_readout is None) != (self.state in ('NOT_SELECTED', 'NOT_ENTERED'))
                or self.state == 'NOT_SELECTED' and self.point is not None):
            raise ValueError('response coverage loses selected, unavailable or unentered work')
        for pin in (self.point, self.original_readout):
            if pin is not None:
                exact(pin, ObjectIdentity)


@dataclass(frozen=True, slots=True)
class PreparationResponseFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-finding'
    question_id: str
    label: str
    disposition: str
    quantities: tuple[PreparationResponseQuantity, ...]
    assigned_comparisons: int
    assessable_comparisons: int
    evidence: tuple[ObjectIdentity, ...]
    consequence: str
    uncertainty: str = UNCERTAINTY
    independent_biological_replicates: int = 0
    nested_state_positions: int = 4
    original_material_count: int = 4
    original_site_count: int = 32
    original_starting_hypotheses: int = 384

    def __post_init__(self):
        if (self.question_id not in tuple('Q' + str(n) for n in range(1, 7))
                or self.label != LABELS[int(self.question_id[1:]) - 1]
                or type(self.assigned_comparisons) is not int or type(self.assessable_comparisons) is not int
                or not 0 <= self.assessable_comparisons <= self.assigned_comparisons
                or not self.disposition or not self.consequence or self.uncertainty != UNCERTAINTY
                or (self.independent_biological_replicates, self.nested_state_positions, self.original_material_count,
                    self.original_site_count, self.original_starting_hypotheses) != (0, 4, 4, 32, 384)):
            raise ValueError('response finding changes its comparison denominator, uncertainty or consequence')
        for quantity in self.quantities:
            exact(quantity, PreparationResponseQuantity)
        if self.evidence != tuple(sorted(set(self.evidence), key=lambda p: p.object_id)):
            raise ValueError('response finding changes original evidence identity or order')


@dataclass(frozen=True, slots=True)
class PreparationResponseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-assessment'
    assessment_id: str
    design: PreparationResponseDesign | EnvironmentalPreparationResponseDesign
    assessor_source: ObjectIdentity
    coverage: tuple[PreparationResponseCoverage, ...]
    actions: tuple[PreparationResponseAction, ...]
    quantities: tuple[PreparationResponseQuantity, ...]
    questions: tuple[PreparationResponseFinding, ...]
    next_supplier_decision: str

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_response_design(self.design)
        if type(self) is PreparationResponseAssessment and type(self.design) is EnvironmentalPreparationResponseDesign:
            raise ValueError('environmental assessment requires its distinct nomination-bearing schema')
        exact(self.assessor_source, ObjectIdentity)
        expected = tuple(effect for stage in response_stages(self.design)
            for effect in response_effects(self.design, stage))
        if tuple((r.effect, r.stage) for r in self.coverage) != tuple((e.identity, e.stage) for e in expected):
            raise ValueError('response assessment drops a selected or optional effect')
        if tuple(q.question_id for q in self.questions) != tuple('Q' + str(n) for n in range(1, 7)):
            raise ValueError('response assessment must retain all six scientific questions')
        for row in self.coverage:
            exact(row, PreparationResponseCoverage)
        for row in self.actions:
            exact(row, PreparationResponseAction)
        for row in self.quantities:
            exact(row, PreparationResponseQuantity)
        for row in self.questions:
            exact(row, PreparationResponseFinding)
        if not self.next_supplier_decision:
            raise ValueError('response assessment omits the next consequential supplier decision')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentalPreparationResponseAssessment(PreparationResponseAssessment):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-environment-assessment'
    nomination: PreparationResponseEnvironmentNomination | None = None

    def __post_init__(self):
        PreparationResponseAssessment.__post_init__(self)
        exact(self.design, EnvironmentalPreparationResponseDesign)
        if self.nomination is not None:
            exact(self.nomination, PreparationResponseEnvironmentNomination)
            if (self.nomination.design != self.design.identity
                    or self.nomination.environment != self.design.environment.identity):
                raise ValueError('environment assessment substitutes its prospective original nomination')
            readouts = tuple(sorted((row.original_readout for row in self.coverage
                if row.stage == 'initial-primary' and row.original_readout is not None), key=lambda pin: pin.object_id))
            actions = tuple((model, step, next((row.action for row in self.actions if
                (row.model_name, row.position, row.direction, row.step_bohr) == (model, 'initial', 'primary', step)), None))
                for model in MODELS for step in self.design.steps_bohr)
            if self.nomination.original_readouts != readouts or self.nomination.primary_actions != actions:
                raise ValueError('environment nomination substitutes its original initial readout or action census')
            from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import _product, validate_nomination_components
            allowance = _product(self.design.useful_error_hartree_per_bohr, self.design.numerical_allowance_fraction)
            if self.nomination.numerical_allowance_hartree_per_bohr != allowance:
                raise ValueError('environment nomination changes its prospective numerical allowance')
            validate_nomination_components(self.design, self.nomination)
            if self.nomination.disposition == 'AVAILABLE':
                nominee = self.nomination
                if (nominee.maximum_coordinate_discrepancy_angstrom is None
                        or nominee.maximum_coordinate_discrepancy_angstrom > self.design.environment.coordinate_tolerance_angstrom
                        or nominee.projected_norm_hartree_per_bohr2 is None
                        or nominee.projected_norm_hartree_per_bohr2 <= self.design.environment.minimum_projected_norm_hartree_per_bohr2
                        or _product(self.design.challenge_amplitude_bohr, nominee.projected_norm_hartree_per_bohr2) <= allowance
                        or any(value is None or value > allowance for _, value in nominee.projected_discrepancies_hartree_per_bohr)):
                    raise ValueError('available environment nomination contradicts its own original numerical or mapping findings')


def require_response_assessment(assessment):
    if type(assessment) not in (PreparationResponseAssessment, EnvironmentalPreparationResponseAssessment):
        raise ValueError('response requires one exact registered local or environmental assessment')
    exact(assessment, type(assessment))


