# SPDX-License-Identifier: MPL-2.0
"""Additive eligibility for the selected matrix factor response programme.

An allocation, exposure audit or frozen specification is a candidate input,
not acquisition, authority or qualification. Historical exposed contracts are
unchanged. Whole roots and transfer regimes are reserved before relevant fits.
The existing recursive provider, publication and authority owners retain their
normal responsibilities; this module supplies the matrix scientific joins.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from .exposure import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import (
    SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView,
)
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_decimal, validate_stable_id,
)
from empirical_lawhood.kernel.time import CausalPhase
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult


CANDIDATE = "ELIGIBLE_UNENTERED_CANDIDATE"
PHASES = ("origin", "forecast", "futures", "assess")
BUDGET = ResourceBudget(1, None, 0, None, None, None)


def identity(record):
    for name in ("source_id", "allocation_id", "census_id", "reservation_id", "fit_id",
                 "specification_id", "operand_id", "route_id", "readiness_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("matrix eligibility record lacks its named identity")


@dataclass(frozen=True, slots=True)
class MatrixFactorStream(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/stream"
    purpose_id: str
    panel_id: str
    seed: int
    role: str
    generator: str = "PCG64"

    def __post_init__(self):
        validate_stable_id(self.purpose_id)
        validate_stable_id(self.panel_id)
        if (type(self.seed) is not int or not 0 <= self.seed < 2**128
                or self.generator != "PCG64"
                or self.role not in {"PREFIX", "COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"}):
            raise ValueError("matrix response requires its declared full-width native stream")

    @property
    def effective_seed(self):
        return self.seed


@dataclass(frozen=True, slots=True)
class MatrixFactorRootAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/root-allocation"
    root_id: str
    independent_group_id: str
    regime_id: str
    coordinate_id: str
    clock_id: str
    role: MatrixProgrammeRole
    streams: tuple[MatrixFactorStream, ...]

    def __post_init__(self):
        for name in ("root_id", "independent_group_id", "regime_id", "coordinate_id", "clock_id"):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_ids(self.streams, attribute="purpose_id", field_name="streams")
        if (type(self.role) is not MatrixProgrammeRole or not self.streams
                or sum(s.role == "PREFIX" for s in self.streams) != 1
                or not any(s.role == "COMMON_NOISE_PANEL" for s in self.streams)
                or not any(s.role == "INDEPENDENT_FUTURE" for s in self.streams)
                or len({s.panel_id for s in self.streams}) != len(self.streams)):
            raise ValueError("matrix root needs prefix, paired and independent panel census")


@dataclass(frozen=True, slots=True)
class MatrixFactorRegime(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/regime"
    regime_id: str
    member: SixMatrixResponseModelFamilyMember
    view: SixMatrixResponseNumericalView
    alpha_x: Decimal
    alpha_y: Decimal

    def __post_init__(self):
        validate_stable_id(self.regime_id)
        for name in ("alpha_x", "alpha_y"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))

    @property
    def physical_parameters(self):
        # Numerical timestep/refinement, semantic IDs and stochastic labels
        # cannot reserve a new physical regime. Potential masses are retained
        # separately from the bath/friction and cross-sector coupling.
        return (self.member.mass_x, self.member.mass_y, self.member.cross_coupling_gamma,
                self.member.beta_rule, self.view.bath_temperature, self.view.friction_gamma,
                self.alpha_x, self.alpha_y)


@dataclass(frozen=True, slots=True)
class MatrixFactorAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/protected-allocation"
    allocation_id: str
    roots: tuple[MatrixFactorRootAllocation, ...]
    exposure: MatrixFactorExposureCensus
    regimes: tuple[MatrixFactorRegime, ...] = field(kw_only=True)
    evidence_role: str = CANDIDATE

    def __post_init__(self):
        validate_stable_id(self.allocation_id)
        require_sorted_unique_ids(self.roots, attribute="root_id", field_name="roots")
        require_sorted_unique_ids(self.regimes, attribute="regime_id", field_name="regimes")
        if not self.roots or self.evidence_role != CANDIDATE:
            raise ValueError("matrix protected allocation is an unentered candidate")
        if {r.regime_id for r in self.roots} != {r.regime_id for r in self.regimes}:
            raise ValueError("matrix allocation omits its actual complete physical-regime census")
        streams = tuple(s.effective_seed for r in self.roots for s in r.streams)
        if len(set(streams)) != len(streams) or set(streams).intersection(self.exposure.effective_seed_exclusions):
            raise ValueError("matrix effective streams collide with roots, panels or exposed history")
        roles = {}
        regimes = {}
        for root in self.roots:
            if roles.setdefault(root.independent_group_id, root.role) is not root.role:
                raise ValueError("one independent root cannot cross development/calibration/confirmation roles")
            regimes.setdefault(root.regime_id, set()).add(root.role)
            if (root.role in {MatrixProgrammeRole.CONFIRMATION, MatrixProgrammeRole.WITHHELD_TRANSFER}
                    and root.independent_group_id in self.exposure.exposed_independent_groups):
                raise ValueError("an exposed parent cannot become a fresh population root")
        for regime, role_set in regimes.items():
            if MatrixProgrammeRole.WITHHELD_TRANSFER in role_set and (
                    len(role_set) != 1 or regime in self.exposure.exposed_regimes):
                raise ValueError("withheld transfer reserves complete unexposed regimes")
        physical_roles = {}
        for regime in self.regimes:
            physical_roles.setdefault(regime.physical_parameters, set()).update(regimes[regime.regime_id])
        if any(MatrixProgrammeRole.WITHHELD_TRANSFER in roles and len(roles) != 1
               for roles in physical_roles.values()):
            raise ValueError("renamed or refined copies cannot withhold an already fitted physical regime")
        previously_exposed = {r.key for r in self.exposure.constant_physical_exclusions}
        if any(MatrixProgrammeRole.WITHHELD_TRANSFER in roles and parameters in previously_exposed
               for parameters, roles in physical_roles.items()):
            raise ValueError("renamed prior physical regimes remain exposed and cannot be withheld")
        if not any(r.role is MatrixProgrammeRole.CONFIRMATION for r in self.roots):
            raise ValueError("matrix confirmation allocation omits its confirmation population")
        if not any(r.role is MatrixProgrammeRole.WITHHELD_TRANSFER for r in self.roots):
            raise ValueError("matrix programme must reserve later whole transfer regimes")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixAllocationReservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/allocation-reservation"
    reservation_id: str
    allocation: MatrixFactorAllocation
    publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.reservation_id)
        if (self.publication.logical.payload_schema != self.allocation.SCHEMA
                or self.publication.logical.content_sha256 != self.allocation.fingerprint()
                or self.publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND):
            raise ValueError("protected roles require the actual prior outcome-blind allocation publication")


@dataclass(frozen=True, slots=True)
class MatrixFactorFitScope(CanonicalRecord):
    """Fit entry must consume an already published complete role reservation."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/fit-scope"
    fit_id: str
    reservation: ObjectIdentity
    root_ids: tuple[str, ...]
    regime_ids: tuple[str, ...]
    role: str

    def __post_init__(self):
        validate_stable_id(self.fit_id)
        require_sorted_unique_strings(self.root_ids, field_name="root_ids", allow_empty=False)
        require_sorted_unique_strings(self.regime_ids, field_name="regime_ids", allow_empty=False)
        if self.reservation.object_schema != MatrixAllocationReservation.SCHEMA or self.role not in {"DEVELOPMENT", "CALIBRATION"}:
            raise ValueError("matrix fit requires prior reserve and declared training/calibration role")

    def validate_reservation(self, reservation):
        if self.reservation != identity(reservation):
            raise ValueError("matrix fit substitutes its prior whole-programme reservation")
        roots = tuple(r for r in reservation.allocation.roots if r.root_id in self.root_ids)
        if (len(roots) != len(self.root_ids) or tuple(sorted({r.regime_id for r in roots})) != self.regime_ids
                or any(r.role.value != self.role for r in roots)):
            raise ValueError("matrix fit consumes confirmation roots or withheld regimes")


def require_reserved_fit_input(scope, reservation, allocation_port):
    """Pre-fit consumer join to the actual earlier published allocation bytes.

    A fit may only consume its frozen development/calibration root census.
    Supplying a proposed record without the retained publication is refused.
    The caller must perform this join before reading data or fitting models.
    """
    from empirical_lawhood.runtime.experimental_matching import require_reserved_population
    scope.validate_reservation(reservation)
    allocation, binding = reservation_design_projection(reservation, consuming_role=scope.role)
    selected = tuple(root for root in reservation.allocation.roots if root.root_id in scope.root_ids)
    groups = tuple(sorted({root.independent_group_id for root in selected}))
    if set(scope.root_ids) != {root.root_id for root in reservation.allocation.roots
            if root.independent_group_id in groups}:
        raise ValueError("matrix fit omits nested members of its complete independent group")
    require_reserved_population(binding, allocation, reservation.allocation, allocation_port, fitting_unit_ids=groups)


def reservation_design_projection(reservation, *, consuming_role):
    """Reuse the actual original reserve publication without revising its bytes.

    Exposure and every full physical-regime/stream exclusion are validated by
    MatrixFactorAllocation before the generic whole-unit/byte join. Semantic IDs
    cannot create a new regime, and nested members cannot enlarge the denominator.
    This projection supplies no acquisition, qualification or chronology claim.
    """
    from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
    from empirical_lawhood.kernel.experimental_matching import PopulationReservationBinding
    from empirical_lawhood.kernel.serialization import canonical_json_bytes

    if type(reservation) is not MatrixAllocationReservation or consuming_role not in {"DEVELOPMENT", "CALIBRATION"}:
        raise ValueError("matrix reservation projection requires its original typed reserve and selected fit role")
    reservation.__post_init__()
    original = reservation.allocation
    original.__post_init__()
    by_group = {}
    for root in original.roots:
        by_group.setdefault(root.independent_group_id, []).append(root)
    regime_by_id = {regime.regime_id: regime for regime in original.regimes}
    units, roles = [], []
    for group_id, roots in sorted(by_group.items()):
        regimes = tuple(sorted({root.regime_id for root in roots}))
        family = regimes[0] if len(regimes) == 1 else "regime-set." + sha256(canonical_json_bytes(regimes)).hexdigest()
        units.append(IndependentUnit(group_id, original.allocation_id, family,
            tuple(sorted({regime_by_id[root.regime_id].view.view_id for root in roots})),
            group_id in original.exposure.exposed_independent_groups))
        roles.append(UnitRoleAssignment(group_id, roots[0].role.value.lower()))
    projected = UnitAllocation(original.allocation_id + ".whole-units", (original.identity,), tuple(units), tuple(roles))
    publication = reservation.publication
    protected_candidates = ("calibration", "confirmation", "withheld_transfer") if consuming_role == "DEVELOPMENT" else (
        "confirmation", "withheld_transfer")
    protected = tuple(role for role in protected_candidates if role in {row.role for row in projected.roles})
    binding = PopulationReservationBinding(reservation.reservation_id + ".original-publication", projected.identity,
        original.identity, "allocation_id", ArtifactIdentity(publication.logical.logical_artifact_id,
            "reserved-original-allocation", publication.logical.payload_schema, publication.logical.content_sha256,
            publication.logical.media_type, publication.materialization.size_bytes),
        publication.materialization.materialization_id, protected)
    return projected, binding


@dataclass(frozen=True, slots=True)
class MatrixFactorScientificSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/scientific-selection"
    specification_id: str
    reservation: ObjectIdentity
    fits: tuple[MatrixFactorFitScope, ...]
    factor_rule: ObjectIdentity
    model: ObjectIdentity
    predictor: ObjectIdentity
    evaluator: ObjectIdentity
    response_design: ObjectIdentity
    statistical_design: ObjectIdentity
    action_chart: ObjectIdentity
    receiver: ObjectIdentity
    initial_state_rule: ObjectIdentity
    preparation_schedule: ObjectIdentity
    action_ids: tuple[str, ...]
    horizon_steps: tuple[int, ...]

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        require_sorted_unique_ids(self.fits, attribute="fit_id", field_name="fits")
        require_sorted_unique_strings(self.action_ids, field_name="action_ids", allow_empty=False)
        if (self.reservation.object_schema != MatrixAllocationReservation.SCHEMA
                or not self.horizon_steps or self.horizon_steps != tuple(sorted(set(self.horizon_steps)))
                or any(type(n) is not int or n < 1 for n in self.horizon_steps)
                or any(f.reservation != self.reservation for f in self.fits)):
            raise ValueError("matrix frozen method needs complete horizons and its prior role reserve")

    def validate_reservation(self, reservation):
        if self.reservation != identity(reservation):
            raise ValueError("matrix scientific freeze changes protected roots/regimes")
        for fit in self.fits:
            fit.validate_reservation(reservation)


@dataclass(frozen=True, slots=True)
class MatrixFactorFrozenSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/frozen-specification"
    specification_id: str
    selection: MatrixFactorScientificSelection
    publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (self.publication.logical.payload_schema != self.selection.SCHEMA
                or self.publication.logical.content_sha256 != self.selection.fingerprint()
                or self.publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND):
            raise ValueError("matrix selected rules/models/design/menu lack exact outcome-blind freeze publication")

    def validate_reservation(self, reservation):
        self.selection.validate_reservation(reservation)


@dataclass(frozen=True, slots=True)
class MatrixFactorSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/eligible-source"
    source_id: str
    reservation: MatrixAllocationReservation
    specification: MatrixFactorFrozenSpecification
    member: SixMatrixResponseModelFamilyMember
    view: SixMatrixResponseNumericalView
    provenance: NumericalProducingProvenance
    evidence_role: str = CANDIDATE

    def __post_init__(self):
        validate_stable_id(self.source_id)
        self.specification.validate_reservation(self.reservation)
        if (self.evidence_role != CANDIDATE
                or self.specification.selection.model != ObjectIdentity.from_record(self.member.member_id, self.member)):
            raise ValueError("matrix eligible source changes frozen native model or standing")

    @property
    def allocation(self):
        return self.reservation.allocation

    def validate_regime(self, root, *, member, view, alpha_x, alpha_y):
        regime = next((r for r in self.allocation.regimes if r.regime_id == root.regime_id), None)
        if (root not in self.allocation.roots or regime is None or regime.member != member
                or regime.view != view or regime.alpha_x != alpha_x or regime.alpha_y != alpha_y):
            raise ValueError("matrix native source substitutes protected physical regime or numerical view")


@dataclass(frozen=True, slots=True)
class EligibleMatrixArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/eligible-arrays"
    operand_id: str
    allocation: ObjectIdentity
    source: ObjectIdentity
    root_id: str
    role: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        validate_stable_id(self.root_id)
        require_sorted_unique_ids(self.members, attribute="name", field_name="members")
        require_sorted_unique_ids(self.producers, attribute="object_id", field_name="producers")
        if (self.allocation.object_schema != MatrixFactorAllocation.SCHEMA
                or self.source.object_schema != MatrixFactorSource.SCHEMA
                or self.role not in {"ORIGIN", "FORECAST", "NATIVE_RESPONSES", "ASSESSMENT"}
                or not 0 < len(self.members) <= 256 or not self.producers
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != "application/x-npz"
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or self.outcome_access is not (OutcomeAccess.EVALUATION_SEALED
                    if self.role in {"NATIVE_RESPONSES", "ASSESSMENT"} else OutcomeAccess.OUTCOME_BLIND)):
            raise ValueError("eligible matrix arrays change bounded census or prospective access")

    def validate_source(self, source):
        if (self.source != identity(source) or self.allocation != source.allocation.identity
                or self.root_id not in {r.root_id for r in source.allocation.roots}
                or self.array_artifact.sha256 in source.allocation.exposure.exposed_artifact_sha256s):
            raise ValueError("eligible arrays change source/root or relabel exposed raw bytes")


def validate_eligible_array_input(port, manifest, source, *, expected_members, expected_producers,
                                 allocation=None, root_id=None):
    """The original scientific source/access join, before any array decoding."""
    from empirical_lawhood.runtime.execution import WorkerInputPort
    if type(source) is ObjectIdentity:
        if (source.object_schema != MatrixFactorSource.SCHEMA or manifest.source != source
                or allocation is None or manifest.allocation != allocation
                or root_id is None or manifest.root_id != root_id):
            raise ValueError("matrix causal reader changes exact public source/allocation/root identities")
    elif type(source) is MatrixFactorSource:
        manifest.validate_source(source)
    else:
        raise TypeError("matrix eligible reader requires its exact source or future-free public identities")
    if (not isinstance(port, WorkerInputPort) or manifest.producers != expected_producers
            or tuple((m.name, m.dtype, m.shape) for m in manifest.members) != expected_members
            or port.artifact_id != manifest.array_artifact.artifact_id
            or port.payload_schema != MATRIX_ARRAY_SCHEMA or port.media_type != "application/x-npz"
            or port.size_bytes != manifest.array_artifact.size_bytes
            or port.outcome_access is not manifest.outcome_access
            or port.visibility_ceiling is not manifest.visibility_ceiling):
        raise ValueError("matrix eligible worker array/source/shape/access contract differs")


def consume_eligible_arrays(port, manifest, source, *, expected_members, expected_producers,
                            allocation=None, root_id=None):
    """Authenticate every NPZ member before delivering any scientific values."""
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    validate_eligible_array_input(port, manifest, source, expected_members=expected_members,
        expected_producers=expected_producers, allocation=allocation, root_id=root_id)
    return decode_matrix_arrays(port.read(), manifest)


def validate_origin_cutoff(source, root_id, cutoff, *, native_step, timestep):
    root = next((r for r in source.allocation.roots if r.root_id == root_id), None)
    if (root is None or root.role is not MatrixProgrammeRole.CONFIRMATION
            or type(native_step) is not int or native_step < 0 or timestep != source.view.timestep
            or cutoff.clock_id != root.clock_id or cutoff.phase is not CausalPhase.PRE_ACTION
            or cutoff.coordinate != timestep * native_step):
        raise ValueError("matrix confirmation changes native clock, causal cutoff or protected root")


def confirmation_authority_reasons(source, policy, *, scope_id, budget, passed_gate_ids,
                                  proposer_id, approver_id, at_utc):
    """Reuse the existing authority decision; eligible inputs grant no rights."""
    if type(policy) is not AuthorityPolicy:
        raise TypeError("matrix scientific execution requires the existing authority policy")
    source.__post_init__()
    return policy.refusal_reasons(action=AuthorityAction.SIMULATION_EXECUTION,
        world_kind=WorldKind.NUMERICAL_SIMULATOR, source_access=SourceAccessClass.NONE,
        passed_gate_ids=passed_gate_ids, requested_budget=budget,
        requested_outcome_access=OutcomeAccess.EVALUATION_SEALED, requested_scope_id=scope_id,
        proposer_id=proposer_id, approver_id=approver_id, at_utc=at_utc)








def refuse_completed_or_uncertain_branch(native_subwork, definition):
    """Use retained state: UNKNOWN contact and known completion never reacquire."""
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    state = native_subwork.inspect(definition).state
    if state is not NativeSubworkState.NOT_ENTERED:
        raise ValueError("matrix retained or uncertain branch requires receipt recovery, not replay")






def authenticate_eligibility_operands(source, records):
    """Original protected publication and exposure records are ordinary inputs."""
    expected = (source.allocation, source.allocation.exposure,
        source.reservation, source.specification, source.provenance)
    actual = {sha256(r.canonical_bytes()).hexdigest(): r for r in records}
    if len(actual) != len(records) or set(actual) != {r.fingerprint() for r in expected}:
        raise ValueError("matrix eligible source omits/substitutes ordinary exposure/reservation/freeze/provenance operands")
    if any(actual[r.fingerprint()].canonical_bytes() != r.canonical_bytes() for r in expected):
        raise ValueError("matrix eligible source changes authenticated scientific operand bytes")
