# SPDX-License-Identifier: MPL-2.0
"""Explicit coupling-only E5 recipes and their separate native subjects.

Original scheduled subjects are never relabelled as prepared histories. These
records carry selected physical operands and custody requirements; references
alone establish neither source eligibility nor cross-preparation applicability.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from math import prod
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    METHODS, MatrixParameterHistoryControl, MatrixParameterNativeHistory, MatrixParameterNumericalDesign,
    coordinate_identity, expected_members,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, ScheduledRoot, identity as scheduled_identity
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import require_native_completion_receipt


APPLICABILITY = "COUPLING_ONLY_FIXED_HALF_TICK_RECIPE_ORIGINAL_MEMBER_BATH_RECEIVER_FORCE_V1"
STANDING = "FINITE_DT_EMPIRICAL_EQUATION_CROSSCHECK_NO_CONTINUUM_OR_PREPARATION_APPLICABILITY_BOUND"
INITIAL_MEMBERS = {"momenta": ("<c16", (2, 3, 4, 4)), "positions": ("<c16", (2, 3, 4, 4))}


def preparation_identity(record):
    for name in ("recipe_id", "state_id", "source_id", "operand_id", "history_id", "assessment_id", "config_id", "design_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("prepared Matrix record lacks its declared identity")


def exact_decimal(value):
    """Convert a finite base-ten rational without the caller's Decimal context."""
    value = Fraction(value)
    with localcontext() as context:
        context.prec = len(str(abs(value.numerator))) + 4 * len(str(value.denominator)) + 10
        return Decimal(value.numerator) / Decimal(value.denominator)


def _members(rows, expected):
    if (type(rows) is not tuple or any(type(row) is not MatrixArrayMember for row in rows)
            or tuple(row.name for row in rows) != tuple(sorted(expected))
            or {row.name: (row.dtype, row.shape) for row in rows} != expected
            or any(not row.finite_required for row in rows)):
        raise ValueError("preparation arrays lose their exact finite complete member geometry")
    for row in rows:
        row.__post_init__()


def _artifact(value):
    if (type(value) is not ArtifactIdentity or value.payload_schema != MATRIX_ARRAY_SCHEMA
            or value.media_type != "application/x-npz" or not 0 < value.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES):
        raise ValueError("preparation requires its original bounded NPZ artifact")
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixCouplingRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/coupling-recipe"
    recipe_id: str
    kind: str
    primary_steps: int
    half_tick_couplings: tuple[tuple[Decimal, Decimal], ...]
    effort_rule: str
    effort_unit: str
    applicability: str = APPLICABILITY

    def __post_init__(self):
        self._validate(("HOLD", "FIXED_COUPLING"))

    def _validate(self, kinds):
        validate_stable_id(self.recipe_id)
        validate_stable_id(self.effort_unit)
        if (self.kind not in kinds or type(self.primary_steps) is not int or self.primary_steps < 1
                or type(self.half_tick_couplings) is not tuple or len(self.half_tick_couplings) != 2 * self.primary_steps + 1
                or any(type(row) is not tuple or len(row) != 2 for row in self.half_tick_couplings)
                or self.applicability != APPLICABILITY
                or self.effort_rule != "HALF_TICK_COUPLING_TOTAL_VARIATION_L1"):
            raise ValueError("coupling recipe needs every supplied half tick, duration and explicit effort convention")
        for row in self.half_tick_couplings:
            for value in row:
                validate_decimal(value, field_name="fixed coupling", minimum=Decimal(0))
                if not float(value) < float("inf"):
                    raise ValueError("coupling recipe exceeds the original float64 native domain")
        if self.kind == "HOLD" and len(set(self.half_tick_couplings)) != 1:
            raise ValueError("HOLD cannot contain a hidden preparation intervention")

    @property
    def identity(self):
        return preparation_identity(self)

    @property
    def effort(self):
        # This selected path variation is not thermodynamic work or elapsed CPU.
        return exact_decimal(sum((abs(Fraction(right) - Fraction(left))
            for before, after in zip(self.half_tick_couplings, self.half_tick_couplings[1:])
            for left, right in zip(before, after, strict=True)), Fraction(0)))


@dataclass(frozen=True, slots=True)
class MatrixOriginalScheduleRecipe(MatrixCouplingRecipe):
    """No added intervention: retain the actual original half-tick schedule.

    This distinct successor is not constant HOLD. Its selected path variation
    remains actual coupling effort, and its source validates every original
    half tick. Supported acquisition ends within the preparation stream phase.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/original-schedule-recipe"

    def __post_init__(self):
        self._validate(("ORIGINAL_SCHEDULE_BASELINE",))


def coupling_recipe_types():
    return MatrixCouplingRecipe, MatrixOriginalScheduleRecipe


def coupling_recipe_identity(value):
    return type(value) is ObjectIdentity and (value.object_schema, value.object_version) in {
        (kind.SCHEMA, kind.VERSION) for kind in coupling_recipe_types()}


def is_baseline_recipe(recipe):
    return ((type(recipe) is MatrixCouplingRecipe and recipe.kind == "HOLD")
        or (type(recipe) is MatrixOriginalScheduleRecipe and recipe.kind == "ORIGINAL_SCHEDULE_BASELINE"))


def _original_half_tick_schedule(coordinate, primary_steps):
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
    if type(coordinate) is not MatrixParameterCoordinate:
        raise TypeError("original-schedule baseline requires its exact declared coordinate")
    coordinate.__post_init__()
    if type(primary_steps) is not int or not 1 <= primary_steps <= coordinate.ramp_ticks:
        raise ValueError("original-schedule baseline must end within the original preparation-stream ramp")
    return tuple(tuple(Decimal(repr(float(value))) for value in coordinate.couplings(tick, refinement=2))
        for tick in range(2 * primary_steps + 1))


def validate_original_schedule_recipe(recipe, coordinate, primary_steps):
    """Check the complete source schedule; matching endpoints alone is insufficient."""
    if type(recipe) not in coupling_recipe_types():
        raise TypeError("preparation requires its exact declared recipe edition")
    recipe.__post_init__()
    if type(recipe) is MatrixOriginalScheduleRecipe and (
            recipe.primary_steps != primary_steps
            or recipe.half_tick_couplings != _original_half_tick_schedule(coordinate, primary_steps)):
        raise ValueError("original-schedule baseline changes an actual original half tick or endpoint clock")


def original_schedule_recipe(coordinate, primary_steps, *, recipe_id, effort_unit):
    return MatrixOriginalScheduleRecipe(recipe_id, "ORIGINAL_SCHEDULE_BASELINE", primary_steps,
        _original_half_tick_schedule(coordinate, primary_steps),
        "HALF_TICK_COUPLING_TOTAL_VARIATION_L1", effort_unit)


def validate_matched_preparation_menu(arms):
    """Fixed original/early/delayed half-tick paths; no new recipe search."""
    baselines = tuple(recipe for _, recipe in arms if type(recipe) is MatrixOriginalScheduleRecipe)
    if len(baselines) != 1:
        raise ValueError('matched preparation requires its original-ramp baseline, never constant HOLD')
    baseline, = baselines
    baseline.__post_init__()
    if baseline.primary_steps != 256 or baseline.effort != 8:
        raise ValueError('matched preparation requires the original256-tick ramp and nominal effort8')
    expected = tuple(tuple(baseline.half_tick_couplings[index(j)] for j in range(513))
        for index in (lambda j: min(2 * j, 512), lambda j: max(2 * j - 512, 0)))
    seen = set()
    for _, recipe in arms:
        recipe.__post_init__()
        if recipe == baseline:
            continue
        if (type(recipe) is not MatrixCouplingRecipe or recipe.kind != 'FIXED_COUPLING'
                or recipe.primary_steps != baseline.primary_steps or recipe.effort != baseline.effort
                or recipe.effort_unit != baseline.effort_unit or recipe.half_tick_couplings not in expected
                or recipe.half_tick_couplings in seen):
            raise ValueError('matched preparation changes the exact fixed early/delayed ramp menu or effort')
        seen.add(recipe.half_tick_couplings)


@dataclass(frozen=True, slots=True)
class MatrixPreparationInitialState(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/initial-state"
    state_id: str
    original_history: ObjectIdentity
    original_assessment: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    alpha_tilde: tuple[Decimal, Decimal]

    def __post_init__(self):
        validate_stable_id(self.state_id)
        if (type(self.original_history) is not ObjectIdentity or type(self.original_assessment) is not ObjectIdentity
                or type(self.alpha_tilde) is not tuple or len(self.alpha_tilde) != 2):
            raise ValueError("preparation initial state requires exact original history/assessment and both couplings")
        self.original_history.__post_init__()
        self.original_assessment.__post_init__()
        for value in self.alpha_tilde:
            validate_decimal(value, field_name="initial coupling", minimum=Decimal(0))
        _artifact(self.array_artifact)
        _members(self.members, INITIAL_MEMBERS)

    @property
    def identity(self):
        return preparation_identity(self)


@dataclass(frozen=True, slots=True)
class MatrixPreparationInitialStateV2(CanonicalRecord):
    """Declared deterministic tick-zero initialization; no observed history claim."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/initial-state-v2"
    state_id: str
    original: ScheduledPublicSource
    root: ScheduledRoot
    producing_provenance: NumericalProducingProvenance
    cutoff: InformationCutoff
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    alpha_tilde: tuple[Decimal, Decimal]
    consumed_streams: tuple[ObjectIdentity, ...] = ()
    native_contact_count: int = 0
    semantics: str = "DECLARED_DETERMINISTIC_TICK_ZERO_INITIAL_CONDITION_NO_RNG_OR_TRAJECTORY"

    def __post_init__(self):
        validate_stable_id(self.state_id)
        for value, kind in ((self.original, ScheduledPublicSource), (self.root, ScheduledRoot),
                (self.producing_provenance, NumericalProducingProvenance), (self.cutoff, InformationCutoff)):
            if type(value) is not kind:
                raise TypeError("initialization requires exact original source/root/provenance/clock owners")
            value.__post_init__()
        c = self.original.coordinate
        from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import FOUR_FAMILY_PREPARATION_IDS
        alpha = c.decreasing_start if c.family_id == FOUR_FAMILY_PREPARATION_IDS[1] else Decimal(0)
        if (self.root.root != self.original.root or self.root.coordinate != coordinate_identity(c)
                or self.cutoff.clock_id != c.clock_id or self.cutoff.phase is not CausalPhase.PRE_ACTION
                or self.cutoff.coordinate != c.physical_time(0)
                or type(self.alpha_tilde) is not tuple or self.alpha_tilde != (alpha, alpha)
                or tuple(map(float, self.alpha_tilde)) != tuple(c.couplings(0))
                or self.consumed_streams != () or type(self.native_contact_count) is not int or self.native_contact_count != 0
                or self.semantics != "DECLARED_DETERMINISTIC_TICK_ZERO_INITIAL_CONDITION_NO_RNG_OR_TRAJECTORY"):
            raise ValueError("initialization changes its exact common initial rule, original clock/root or no-contact semantics")
        for value in self.alpha_tilde:
            validate_decimal(value, field_name="declared initial coupling", minimum=Decimal(0))
        _artifact(self.array_artifact)
        _members(self.members, INITIAL_MEMBERS)

    @property
    def identity(self):
        return preparation_identity(self)


def initial_state_types():
    return MatrixPreparationInitialState, MatrixPreparationInitialStateV2


def initial_state_identity(value):
    return type(value) is ObjectIdentity and (value.object_schema, value.object_version) in {
        (kind.SCHEMA, kind.VERSION) for kind in initial_state_types()}


@dataclass(frozen=True, slots=True)
class MatrixPreparationSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-source"
    source_id: str
    original: ScheduledPublicSource
    root: ScheduledRoot
    initial: MatrixPreparationInitialState | MatrixPreparationInitialStateV2
    recipe: MatrixCouplingRecipe | MatrixOriginalScheduleRecipe
    provenance: NumericalProducingProvenance
    numerical_design: MatrixParameterNumericalDesign
    applicability: str = APPLICABILITY

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if (type(self.original) is not ScheduledPublicSource or type(self.root) is not ScheduledRoot
                or type(self.initial) not in initial_state_types() or type(self.recipe) not in coupling_recipe_types()
                or type(self.provenance) is not NumericalProducingProvenance
                or type(self.numerical_design) is not MatrixParameterNumericalDesign or self.applicability != APPLICABILITY):
            raise ValueError("preparation source omits original source/root/state/recipe/producing provenance/design")
        for value in (self.original, self.root, self.initial, self.recipe, self.provenance, self.numerical_design):
            value.__post_init__()
        c = self.coordinate
        validate_original_schedule_recipe(self.recipe, c, self.original.policy.cutoff_tick)
        if type(self.initial) is MatrixPreparationInitialStateV2 and (self.initial.original != self.original or self.initial.root != self.root):
            raise ValueError("prepared source changes its actual declared initialization source or root streams")
        if (self.root.root != self.original.root or self.root.coordinate != coordinate_identity(c)
                or self.recipe.primary_steps != self.original.policy.cutoff_tick
                or self.recipe.half_tick_couplings[0] != self.initial.alpha_tilde
                or tuple(float(value) for value in self.recipe.half_tick_couplings[-1]) != tuple(c.couplings(self.total_ticks))
                or c.primary_view.rng_algorithm not in ("numpy.pcg64dxsm", "numpy-pcg64dxsm")):
            raise ValueError("prepared source changes original group, physical duration, matched initial coupling or restored handoff context")
        size = sum(prod(shape) * {"<c16": 16, "<f8": 8, "<i8": 8}[dtype]
            for dtype, shape in expected_members(self).values())
        if size + 11 * 10000 > MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError("preparation duration requires an explicit chunked transport before native entry")

    @property
    def identity(self):
        return preparation_identity(self)

    @property
    def coordinate(self):
        return self.original.coordinate

    @property
    def q(self):
        return self.coordinate.q

    @property
    def total_ticks(self):
        return self.recipe.primary_steps

    @property
    def member(self):
        return self.coordinate.member

    @property
    def primary_view(self):
        return self.coordinate.primary_view

    @property
    def fine_view(self):
        return self.coordinate.fine_view

    @property
    def duration(self):
        return exact_decimal(Fraction(self.primary_view.timestep) * self.total_ticks)

    def validate_allocation(self, allocation):
        if (type(allocation) is not ScheduledAllocation or scheduled_identity(allocation) != self.original.allocation
                or self.root not in allocation.roots or self.coordinate not in allocation.coordinates):
            raise ValueError("preparation source substitutes its actual original root/allocation/coordinate")
        allocation.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixPreparationArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-arrays"
    operand_id: str
    source: ObjectIdentity
    initial: ObjectIdentity
    recipe: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        for value, kind in ((self.source, MatrixPreparationSource),):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("prepared arrays substitute their exact original source/state/recipe type/revision")
        if not coupling_recipe_identity(self.recipe):
            raise ValueError("prepared arrays substitute their exact recipe edition")
        if not initial_state_identity(self.initial):
            raise ValueError("prepared arrays substitute their exact initial-state edition")
        _artifact(self.array_artifact)
        if (type(self.members) is not tuple or not self.members or any(type(row) is not MatrixArrayMember for row in self.members)
                or tuple(row.name for row in self.members) != tuple(sorted({row.name for row in self.members}))
                or sum(row.size_bytes for row in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError("prepared arrays lose their bounded complete member manifest")

    def validate_source(self, source):
        if (self.source != source.identity or self.initial != source.initial.identity or self.recipe != source.recipe.identity):
            raise ValueError("prepared arrays change selected source, matched initial state or fixed recipe")
        _members(self.members, expected_members(source))


@dataclass(frozen=True, slots=True)
class MatrixPreparationHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-history"
    history_id: str
    source: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    arrays: MatrixPreparationArrays
    native: MatrixParameterNativeHistory
    completed_primary_steps: int
    completed_fine_steps: int

    def __post_init__(self):
        for value in (self.history_id, self.root_id, self.independent_group_id, self.clock_id):
            validate_stable_id(value)
        if (type(self.arrays) is not MatrixPreparationArrays or type(self.native) is not MatrixParameterNativeHistory
                or self.source != self.arrays.source or type(self.completed_primary_steps) is not int
                or self.completed_primary_steps < 1 or self.completed_fine_steps != 2 * self.completed_primary_steps):
            raise ValueError("prepared history loses its complete native paired source/clock/custody")
        self.arrays.__post_init__()
        self.native.__post_init__()

    @property
    def identity(self):
        return preparation_identity(self)

    def validate_source(self, source, allocation):
        source.validate_allocation(allocation)
        self.arrays.validate_source(source)
        root = source.root.root
        definition, completion, receipt = self.native.definition, self.native.completion, self.native.receipt
        streams = tuple(sorted((source.root.stream_identity(row) for row in source.root.streams), key=lambda row: row.object_id))
        consumed = tuple(sorted((source.root.stream_identity(row) for row in source.root.streams
            if row.purpose.startswith("preparation")), key=lambda row: row.object_id))
        from .preparation_bindings import MatrixPreparationOperationConfig, MatrixPreparationOperationConfigV2, NAMESPACE, node_id, native_input_records
        direct = definition.operation_id == NAMESPACE + ".native.direct-inputs.v2"
        configuration_type = MatrixPreparationOperationConfigV2 if direct else MatrixPreparationOperationConfig
        if direct:
            streams = tuple(sorted((pin for name, pin, _ in native_input_records(source)
                if name.startswith("native-stream.")), key=lambda row: row.object_id))
        expected_sources = ({source.identity, source.original.allocation, source.provenance.identity} if direct else
            {source.identity, source.original.allocation, source.initial.identity, source.recipe.identity, source.provenance.identity})
        configuration = configuration_type("config." + node_id(source, "history"), "history", source,
            len(allocation.canonical_bytes()))
        task = "native-subwork." + sha256((definition.parent_contact.task_id + ":" + definition.subwork_id).encode()).hexdigest()
        attempt = definition.parent_contact.run_id + "." + task + ".attempt-001"
        native_ids = {task + ".output.arrays", task + ".completion"}
        if (self.source != source.identity or (self.root_id, self.independent_group_id, self.clock_id) !=
                (root.root_id, root.independent_group_id, root.clock_id)
                or definition.subwork_id != "subwork." + source.source_id + ".paired-preparation"
                or definition.operation_id != NAMESPACE + (".native.direct-inputs.v2" if direct else ".native.v1") or definition.configuration != preparation_identity(configuration)
                or definition.parent_contact.task_id != node_id(source, "history")
                or definition.parent_contact.implementation_commit != source.provenance.observed_git_head
                or (receipt.run_id, receipt.task_id, receipt.attempt_id, receipt.receipt_id) !=
                    (definition.parent_contact.run_id, task, attempt, "receipt." + attempt)
                or len(receipt.output_logical_artifacts) != 2 or len(receipt.output_materializations) != 2
                or {row.logical_artifact_id for row in receipt.output_logical_artifacts} != native_ids
                or {row.logical_artifact_id for row in receipt.output_materializations} != native_ids
                or self.completed_primary_steps != source.total_ticks or definition.streams != streams
                or completion.consumed_streams != consumed or completion.unconsumed_streams != tuple(row for row in streams if row not in consumed)
                or definition.code_sources_sha256 != source.provenance.code_sources_sha256
                or definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
                or set(definition.sources) != expected_sources):
            raise ValueError("prepared history changes actual native source/group/clock/provenance/stream census")
        outputs = tuple(row for row in receipt.output_logical_artifacts if row.payload_schema == MATRIX_ARRAY_SCHEMA)
        artifact = self.arrays.array_artifact
        if (len(outputs) != 1 or outputs[0].profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or outputs[0].content_sha256 != artifact.sha256 or outputs[0].media_type != artifact.media_type):
            raise ValueError("prepared history changes the original native receipted output")
        require_native_completion_receipt(completion, receipt, outcome_access=outputs[0].outcome_access,
            visibility_ceiling=outputs[0].visibility_ceiling)
        physical, = tuple(row for row in receipt.output_materializations if row.logical_artifact_id == outputs[0].logical_artifact_id)
        if physical.physical_sha256 != artifact.sha256 or physical.size_bytes != artifact.size_bytes:
            raise ValueError("prepared history changes original native physical custody")


@dataclass(frozen=True, slots=True)
class MatrixPreparationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-assessment"
    assessment_id: str
    source: ObjectIdentity
    arrays: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (type(self.source) is not ObjectIdentity or self.source.object_schema != MatrixPreparationSource.SCHEMA
                or type(self.arrays) is not ObjectIdentity or self.arrays.object_schema != MatrixPreparationArrays.SCHEMA
                or type(self.numerical_design) is not ObjectIdentity or self.numerical_design.object_schema != MatrixParameterNumericalDesign.SCHEMA
                or type(self.controls) is not tuple or any(type(row) is not MatrixParameterHistoryControl for row in self.controls)
                or tuple(row.control_id for row in self.controls) != METHODS
                or type(self.numerical_pass) is not bool or self.numerical_pass != all(row.disposition == "SATISFIED" for row in self.controls)
                or self.standing != STANDING):
            raise ValueError("prepared assessment loses complete independent controls or invents applicability/continuum standing")
        for row in self.controls:
            row.__post_init__()

    @property
    def identity(self):
        return preparation_identity(self)
