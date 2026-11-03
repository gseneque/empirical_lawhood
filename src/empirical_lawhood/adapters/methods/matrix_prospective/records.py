# SPDX-License-Identifier: MPL-2.0
"""Additive matrix programme operands and causal products.

Historical history/array/allocation contracts are not widened. The executable
example is exposed development: no root label or completed receipt grants
confirmation, calibrated lifetime coverage or factor/preparation utility.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import (
    MatrixIntegratorKind, SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView,
)
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES, MatrixAllocation, MatrixPurposeSeed, SavedMatrixArrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_stable_id,
)
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff


EXPOSURE = "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
BRANCHES = ("future-1", "future-2")


def identity(record):
    for name in ("source_id", "protocol_id", "scope_id", "origin_id", "forecast_id",
                 "future_id", "assessment_id", "config_id", "allocation_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("matrix programme record has no declared identity owner")


class MatrixProgrammeRole(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    CALIBRATION = "CALIBRATION"
    CONFIRMATION = "CONFIRMATION"
    WITHHELD_TRANSFER = "WITHHELD_TRANSFER"


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/programme-root"
    root_id: str
    independent_group_id: str
    regime_id: str
    coordinate_id: str
    role: MatrixProgrammeRole
    clock_id: str

    def __post_init__(self):
        for name in ("root_id", "independent_group_id", "regime_id", "coordinate_id", "clock_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        if type(self.role) is not MatrixProgrammeRole:
            raise ValueError("matrix root needs its exact programme role")


@dataclass(frozen=True, slots=True)
class MatrixProgrammeAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/programme-allocation"
    allocation_id: str
    streams: MatrixAllocation
    roots: tuple[MatrixProgrammeRoot, ...]

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        require_sorted_unique_ids(self.roots, attribute="root_id", field_name="roots")
        if {r.root_id for r in self.roots} != {r.root_id for r in self.streams.roots}:
            raise ValueError("matrix programme changes the complete underlying root census")
        owners = {}
        for root in self.roots:
            prior = owners.setdefault(root.independent_group_id, root.role)
            if prior is not root.role:
                raise ValueError("nested views of one independent root cannot cross programme roles")
            stream_root = next(r for r in self.streams.roots if r.root_id == root.root_id)
            expected = {MatrixProgrammeRole.DEVELOPMENT: "DEVELOPMENT",
                        MatrixProgrammeRole.CALIBRATION: "CALIBRATION",
                        MatrixProgrammeRole.CONFIRMATION: "EVALUATION",
                        MatrixProgrammeRole.WITHHELD_TRANSFER: "EVALUATION"}[root.role]
            if stream_root.split_role != expected:
                raise ValueError("matrix programme/stream allocation role join differs")


@dataclass(frozen=True, slots=True)
class MatrixOperandScope(CanonicalRecord):
    """Exact source/model/menu/horizon and cutoff for one scientific operand.

CALIBRATION here names an independently checked numerical method tolerance,
not statistical lifetime coverage. Preparation and measured handoff retain
distinct cutoffs even if their numerical state happens to agree.
"""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/operand-scope"
    scope_id: str
    role: str
    model: ObjectIdentity
    numerical_view: ObjectIdentity
    root_ids: tuple[str, ...]
    horizon_steps: int
    action_menu: tuple[str, ...]
    information_cutoff: InformationCutoff

    def __post_init__(self):
        validate_stable_id(self.scope_id)
        if self.role not in {"CALIBRATION", "PRE_PREPARATION", "MEASURED_HANDOFF"}:
            raise ValueError("matrix operand changes its declared scientific product role")
        if (self.model.object_schema != SixMatrixResponseModelFamilyMember.SCHEMA
                or self.numerical_view.object_schema != SixMatrixResponseNumericalView.SCHEMA):
            raise ValueError("matrix operand changes physical model or numerical view")
        require_sorted_unique_strings(self.root_ids, field_name="root_ids", allow_empty=False)
        require_sorted_unique_strings(self.action_menu, field_name="action_menu", allow_empty=False)
        if type(self.horizon_steps) is not int or self.horizon_steps < 1:
            raise ValueError("matrix operand needs its complete positive horizon")


@dataclass(frozen=True, slots=True)
class MatrixPublicProtocol(CanonicalRecord):
    """Predictor-visible conditions, with no future driver seeds or realised path."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/public-protocol"
    protocol_id: str
    root: MatrixProgrammeRoot
    allocation: ObjectIdentity
    member: SixMatrixResponseModelFamilyMember
    view: SixMatrixResponseNumericalView
    alpha_x: Decimal
    alpha_y: Decimal
    prefix_steps: int
    horizon_steps: int
    calibration_scope: MatrixOperandScope
    preparation_scope: MatrixOperandScope
    native_reference_tolerance: Decimal
    forecast_precision: Decimal
    exposure: str = EXPOSURE

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        if self.exposure != EXPOSURE or self.root.role is not MatrixProgrammeRole.DEVELOPMENT:
            raise ValueError("exposed matrix provider cannot acquire confirmation or transfer")
        if self.allocation.object_schema != MatrixAllocation.SCHEMA:
            raise ValueError("matrix protocol requires the exact existing stream allocation identity")
        if (self.view.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN
                or self.view.rng_algorithm != "PCG64" or self.view.rng_version != "1.0.0"):
            raise ValueError("matrix selected native method requires its exact integrator and RNG semantics")
        for name in ("prefix_steps", "horizon_steps"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError("matrix protocol needs an explicit full prefix/horizon census")
        for name in ("alpha_x", "alpha_y", "native_reference_tolerance", "forecast_precision"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if self.native_reference_tolerance == 0 or self.forecast_precision == 0:
            raise ValueError("matrix precision gates must be positive")
        # The selected complete scientific package uses the existing closed
        # NPZ contract. Refuse a different package before effect entry; do not
        # shorten its horizon or omit scientific states to fit the transport.
        prefix_bytes = 2 * (self.prefix_steps + 1) * 2 * 3 * 4 * 4 * 16 + 4096
        future_bytes = (4 * (self.horizon_steps + 1) + 2 * self.horizon_steps) * 2 * 3 * 4 * 4 * 16 + 12288
        if max(prefix_bytes, future_bytes) > MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError("complete matrix package exceeds its unchanged closed NPZ contract")
        if self.calibration_scope.role != "CALIBRATION" or self.preparation_scope.role != "PRE_PREPARATION":
            raise ValueError("matrix protocol substitutes calibration/preparation scope")
        for scope in (self.calibration_scope, self.preparation_scope):
            if (scope.model != ObjectIdentity.from_record(self.member.member_id, self.member)
                    or scope.numerical_view != ObjectIdentity.from_record(self.view.view_id, self.view)
                    or scope.horizon_steps != self.horizon_steps or scope.action_menu != BRANCHES):
                raise ValueError("matrix scope changes model, view, horizon or action menu")
        if self.root.root_id not in self.preparation_scope.root_ids:
            raise ValueError("matrix preparation omits its actual native root")
        if set(self.calibration_scope.root_ids) & set(self.preparation_scope.root_ids):
            raise ValueError("matrix calibration/preparation populations must remain distinct")
        # This exposed route consumes a frozen analytic method reference, not
        # a calibration outcome acquired on the forecast's target trajectory.
        # Its independent clock starts before any reference observation.
        reference_cutoff = self.calibration_scope.information_cutoff
        if (reference_cutoff.clock_id == self.root.clock_id
                or reference_cutoff.coordinate != Decimal(0)
                or reference_cutoff.phase is not CausalPhase.PRE_ACTION):
            raise ValueError("matrix numerical reference changes its independent pre-observation cutoff")
        if (self.preparation_scope.information_cutoff.clock_id != self.root.clock_id
                or self.preparation_scope.information_cutoff.coordinate != Decimal(0)
                or self.preparation_scope.information_cutoff.phase is not CausalPhase.PRE_ACTION):
            raise ValueError("matrix preparation changes its pre-acquisition cutoff")

    @property
    def cutoff(self):
        return InformationCutoff("cutoff." + self.protocol_id, self.root.clock_id,
            CausalPhase.PRE_ACTION, self.view.timestep * self.prefix_steps)


@dataclass(frozen=True, slots=True)
class MatrixProspectiveSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/source"
    source_id: str
    protocol: MatrixPublicProtocol
    allocation: MatrixProgrammeAllocation

    def __post_init__(self):
        validate_stable_id(self.source_id)
        if (self.protocol.allocation != self.allocation.streams.identity
                or self.allocation.roots != (self.protocol.root,)
                or self.allocation.streams.exposure != EXPOSURE):
            raise ValueError("selected exposed source requires its complete one-root roster")
        stream_root = self.allocation.streams.roots[0]
        if stream_root.cohort != "q2":
            raise ValueError("selected native example has its declared q2 matrix geometry")


@dataclass(frozen=True, slots=True)
class MatrixCausalOrigin(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/causal-origin"
    origin_id: str
    source: ObjectIdentity
    protocol: MatrixPublicProtocol
    prefix_stream: MatrixPurposeSeed
    arrays: SavedMatrixArrays

    def __post_init__(self):
        validate_stable_id(self.origin_id)
        if (self.source.object_schema != MatrixProspectiveSource.SCHEMA
                or self.prefix_stream.purpose_id != "prefix"
                or self.arrays.allocation != self.protocol.allocation
                or identity(self.protocol) not in self.arrays.producers):
            raise ValueError("matrix origin source, past stream or array producer join differs")
        expected = (self.protocol.prefix_steps + 1, 2, 3, 4, 4)
        if tuple((m.name, m.dtype, m.shape) for m in self.arrays.members) != (
                ("momenta", "<c16", expected), ("positions", "<c16", expected)):
            raise ValueError("matrix origin omits full native complex prefix census")


@dataclass(frozen=True, slots=True)
class MatrixCausalForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/causal-forecast"
    forecast_id: str
    origin: ObjectIdentity
    protocol: ObjectIdentity
    information_cutoff: InformationCutoff
    calibration_scope: ObjectIdentity
    preparation_scope: ObjectIdentity
    arrays: SavedMatrixArrays
    predictor: str = "origin-inertial-extrapolation-v1"

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        if (self.origin.object_schema != MatrixCausalOrigin.SCHEMA
                or self.protocol.object_schema != MatrixPublicProtocol.SCHEMA
                or self.calibration_scope.object_schema != MatrixOperandScope.SCHEMA
                or self.preparation_scope.object_schema != MatrixOperandScope.SCHEMA
                or self.predictor != "origin-inertial-extrapolation-v1"
                or self.origin not in self.arrays.producers):
            raise ValueError("matrix causal forecast changes origin, method or scientific operands")
        if tuple((m.name, m.dtype, m.shape) for m in self.arrays.members) != tuple(
                (b, "<c16", (2, 3, 4, 4)) for b in BRANCHES):
            raise ValueError("matrix forecast changes the complete selected branch census")

    def validate_origin(self, origin):
        p = origin.protocol
        if (self.origin != identity(origin) or self.protocol != identity(p)
                or self.information_cutoff != p.cutoff or self.arrays.allocation != p.allocation
                or self.calibration_scope != identity(p.calibration_scope)
                or self.preparation_scope != identity(p.preparation_scope)):
            raise ValueError("matrix commitment changes origin/model/cutoff/calibration/preparation")


@dataclass(frozen=True, slots=True)
class MatrixNativeBranch(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/native-branch"
    branch_id: str
    stream: MatrixPurposeSeed
    alpha_x: Decimal
    alpha_y: Decimal

    def __post_init__(self):
        if self.branch_id not in BRANCHES or self.stream.purpose_id != self.branch_id:
            raise ValueError("matrix branch root/stream role differs")
        for name in ("alpha_x", "alpha_y"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class MatrixNativeFutures(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/native-futures"
    future_id: str
    origin: ObjectIdentity
    forecast: ObjectIdentity
    protocol: ObjectIdentity
    branches: tuple[MatrixNativeBranch, ...]
    arrays: SavedMatrixArrays

    def __post_init__(self):
        validate_stable_id(self.future_id)
        if (self.origin.object_schema != MatrixCausalOrigin.SCHEMA
                or self.forecast.object_schema != MatrixCausalForecast.SCHEMA
                or self.protocol.object_schema != MatrixPublicProtocol.SCHEMA
                or tuple(b.branch_id for b in self.branches) != BRANCHES
                or self.forecast not in self.arrays.producers):
            raise ValueError("matrix futures change their committed forecast or complete branch census")


@dataclass(frozen=True, slots=True)
class MatrixBranchAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/branch-assessment"
    branch_id: str
    native_reference_error: Decimal
    forecast_error: Decimal
    native_disposition: AssessmentDisposition
    forecast_disposition: AssessmentDisposition

    def __post_init__(self):
        if self.branch_id not in BRANCHES:
            raise ValueError("matrix independent assessment has an unselected branch")
        for name in ("native_reference_error", "forecast_error"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if any(type(getattr(self, n)) is not AssessmentDisposition
               for n in ("native_disposition", "forecast_disposition")):
            raise ValueError("matrix native and forecast dispositions remain separate")


@dataclass(frozen=True, slots=True)
class MatrixIndependentAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/independent-assessment"
    assessment_id: str
    origin: ObjectIdentity
    forecast: ObjectIdentity
    futures: ObjectIdentity
    branches: tuple[MatrixBranchAssessment, ...]
    assessment_method: str = "independent-potential-difference-baoab-v1"
    exposure: str = EXPOSURE

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.origin.object_schema != MatrixCausalOrigin.SCHEMA
                or self.forecast.object_schema != MatrixCausalForecast.SCHEMA
                or self.futures.object_schema != MatrixNativeFutures.SCHEMA
                or tuple(b.branch_id for b in self.branches) != BRANCHES
                or self.assessment_method != "independent-potential-difference-baoab-v1"
                or self.exposure != EXPOSURE):
            raise ValueError("matrix independent assessment changes the frozen full denominator")
