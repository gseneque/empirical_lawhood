# SPDX-License-Identifier: MPL-2.0
"""Prospective complete structural ensemble and native custody contracts."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_stable_id, validate_sha256,
)

NAMESPACE = "rubisco-insilico-sampling"
UNIT = p.UNIT
QUESTION = "Do the exact full L8S8 donor and recipient interventions produce reproducible structural ensemble contrasts after complete preparation, numerical and stochastic sensitivity checks?"
ENSEMBLES = (("ensemble-01", 17011, 27011), ("ensemble-02", 41017, 51017))
BAROSTAT_SEEDS = (("ensemble-01", 37013), ("ensemble-02", 61019))
INTEGRATION = (("primary", Decimal("0.002"), Decimal("0.000001")),
               ("refined", Decimal("0.001"), Decimal("0.0000001")))
METRICS = ("anchor-contact-count-3A", "anchor-contact-count-5A", "anchor-contact-count-8A",
           "buried-site-area-A2", "interface-active-correlation", "mg-inhibitor-distance-A",
           "other-chain-minimum-A", "source-active-region-rmsd-A")
PRECISION = (("anchor-contact-count-3A", Decimal("0.25")),
             ("anchor-contact-count-5A", Decimal("0.25")),
             ("anchor-contact-count-8A", Decimal("0.25")),
             ("buried-site-area-A2", Decimal("5")),
             ("interface-active-correlation", Decimal("0.1")),
             ("mg-inhibitor-distance-A", Decimal("0.1")),
             ("other-chain-minimum-A", Decimal("0.1")),
             ("source-active-region-rmsd-A", Decimal("0.1")))


def identity(record):
    for name in ("input_id", "config_id", "product_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("unknown structural sampling identity")


def trajectory_roster():
    return tuple((construct, joint, parameters, ensemble, resolution)
                 for construct, joint, parameters in p.model_roster()
                 for ensemble, _, _ in ENSEMBLES for resolution, _, _ in INTEGRATION)


@dataclass(frozen=True, slots=True)
class HardwareSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/hardware-selection"
    input_id: str
    query_stdout_utf8: str
    query_sha256: str
    device_uuid: str
    device_name: str
    driver_version: str
    pci_bus_id: str
    memory_total_mib: int
    compute_capability: str

    def __post_init__(self):
        from hashlib import sha256
        validate_stable_id(self.input_id)
        validate_sha256(self.query_sha256)
        if sha256(self.query_stdout_utf8.encode()).hexdigest() != self.query_sha256:
            raise ValueError("hardware selector changes original inspection bytes")
        fields = tuple(value.strip() for value in self.query_stdout_utf8.strip().split(","))
        expected = (self.device_uuid,self.device_name,self.driver_version,self.pci_bus_id,str(self.memory_total_mib),self.compute_capability)
        if fields != expected or self.memory_total_mib <= 0:
            raise ValueError("hardware allocation substitutes selected CUDA device")


@dataclass(frozen=True, slots=True)
class SamplingSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/source"
    input_id: str
    preparation_selection: p.PreparationSelection
    preparation_assessment: ObjectIdentity
    model_assets: tuple[ObjectIdentity, ...]
    hardware: HardwareSelection
    native_workdir: str
    engine_inventory_sha256: str = p.ENGINE_INVENTORY_SHA256
    ensembles: tuple[tuple[str,int,int], ...] = ENSEMBLES
    barostat_seeds: tuple[tuple[str,int], ...] = BAROSTAT_SEEDS
    integration: tuple[tuple[str,Decimal,Decimal], ...] = INTEGRATION
    temperature_kelvin: Decimal = Decimal("298")
    pressure_atmosphere: Decimal = Decimal("1")
    friction_per_picosecond: Decimal = Decimal("1")
    nonbonded_method: str = "PME"
    cutoff_nanometer: Decimal = Decimal("1")
    constraints: str = "HBonds"
    hydrogen_mass_repartitioning: bool = False
    platform: str = "CUDA"
    platform_precision: str = "mixed"
    device_index: str = "0"
    deterministic_forces: str = "true"
    use_cpu_pme: str = "false"
    native_cpu_threads: int = 1
    remove_center_of_mass_motion: bool = False
    npt_conditioning_picosecond: Decimal = Decimal("100")
    barostat_proposal_cadence_picosecond: Decimal = Decimal("0.05")
    reference_acquisition_ns: Decimal = Decimal("250")
    acquisition_chunk_ns: Decimal = Decimal("10")
    coordinate_cadence_ps: Decimal = Decimal("1000")
    observable_cadence_ps: Decimal = Decimal("10")
    checkpoint_cadence_ps: Decimal = Decimal("10000")
    source_reference_exclusion_ns: Decimal = Decimal("50")
    precision_targets: tuple[tuple[str,Decimal], ...] = PRECISION
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.input_id)
        self.preparation_selection.__post_init__()
        self.hardware.__post_init__()
        if len(self.model_assets) != 24 or len(set(self.model_assets)) != 24:
            raise ValueError("sampling omits/duplicates complete prepared model roster")
        if self.preparation_assessment.object_schema != p.PreparationAssessment.SCHEMA:
            raise ValueError("sampling substitutes actual preparation assessment")
        path = PurePosixPath(self.native_workdir)
        if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(p.NATIVE_WORK_ROOT) or str(path) == p.NATIVE_WORK_ROOT:
            raise ValueError("sampling needs explicitly selected fresh native workdir")
        fixed = (self.engine_inventory_sha256 == p.ENGINE_INVENTORY_SHA256,
                 self.ensembles == ENSEMBLES, self.barostat_seeds == BAROSTAT_SEEDS,
                 self.integration == INTEGRATION,
                 self.temperature_kelvin == 298, self.pressure_atmosphere == 1,
                 self.friction_per_picosecond == 1, self.nonbonded_method == "PME",
                 self.cutoff_nanometer == 1, self.constraints == "HBonds",
                 self.hydrogen_mass_repartitioning is False, self.platform == "CUDA",
                 self.platform_precision == "mixed", self.device_index == "0",
                 self.deterministic_forces == "true", self.use_cpu_pme == "false",
                 self.native_cpu_threads == 1, self.reference_acquisition_ns == 250,
                 self.remove_center_of_mass_motion is False,
                 self.npt_conditioning_picosecond == 100,
                 self.barostat_proposal_cadence_picosecond == Decimal("0.05"),
                 self.acquisition_chunk_ns == 10, self.coordinate_cadence_ps == 1000,
                 self.observable_cadence_ps == 10, self.checkpoint_cadence_ps == 10000,
                 self.source_reference_exclusion_ns == 50,
                 self.precision_targets == PRECISION, self.physical_independent_units == 0)
        if not all(fixed):
            raise ValueError("sampling changes frozen numerical/ensemble selector")


@dataclass(frozen=True, slots=True)
class NativeMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/native-member"
    member_id: str
    relative_path: str
    size_bytes: int
    sha256: str
    role: str

    def __post_init__(self):
        validate_stable_id(self.member_id)
        validate_sha256(self.sha256)
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts or not path.parts or self.size_bytes < 0 or not self.role:
            raise ValueError("invalid complete native member custody")


@dataclass(frozen=True, slots=True)
class PortableNativeView(CanonicalRecord):
    """Current authenticated parent view; original absolute paths have no role.

    API composition binds these identities to its authenticated actual parent
    closure. Domain readers subsequently verify every exact physical member.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/portable-native-view"
    view_id: str
    custody_root: str
    native_relative_prefix: str
    contribution: ObjectIdentity
    transport: ObjectIdentity
    owning_product: ObjectIdentity
    members: tuple[NativeMember, ...]

    def __post_init__(self):
        validate_stable_id(self.view_id)
        root = PurePosixPath(self.custody_root)
        prefix = PurePosixPath(self.native_relative_prefix)
        if not root.is_absolute() or ".." in root.parts or prefix.is_absolute() or ".." in prefix.parts or not prefix.parts:
            raise ValueError("portable native view omits its selected current root/prefix")
        if tuple(sorted(r.relative_path for r in self.members)) != tuple(r.relative_path for r in self.members) or len({r.relative_path for r in self.members}) != len(self.members):
            raise ValueError("portable native view changes complete ordered raw member census")
        for row in self.members:
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class ProductionSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/production-selection"
    input_id: str
    controls: SamplingSource
    calibration: ObjectIdentity
    calibration_assessment: ObjectIdentity
    calibration_view: PortableNativeView
    native_workdir: str
    acquisition_round: int = 1

    def __post_init__(self):
        validate_stable_id(self.input_id)
        self.controls.__post_init__()
        self.calibration_view.__post_init__()
        if self.calibration_view.owning_product!=self.calibration or self.calibration.object_schema!=CalibrationProduct.SCHEMA or self.calibration_assessment.object_schema!=CalibrationAssessment.SCHEMA:
            raise ValueError("production replaces assessed actual numerical parent")
        path=PurePosixPath(self.native_workdir)
        if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(p.NATIVE_WORK_ROOT) or str(path)==p.NATIVE_WORK_ROOT or self.native_workdir==self.controls.native_workdir:
            raise ValueError("production needs a separately selected authored native workdir")
        if self.acquisition_round!=1:
            raise ValueError("adaptive continuation needs a separately outcome-bound selector")


@dataclass(frozen=True, slots=True)
class NativeLedgerSegment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/native-ledger-segment"
    member: NativeMember
    call_count: int
    completed_count: int
    failed_count: int
    first_call_id: str | None
    last_call_id: str | None
    top_level_wall_seconds: Decimal
    top_level_cpu_seconds: Decimal

    def __post_init__(self):
        self.member.__post_init__()
        if min(self.call_count,self.completed_count,self.failed_count)<0 or self.call_count!=self.completed_count+self.failed_count:
            raise ValueError("streamed native ledger changes complete actual attempt counts")
        if (self.call_count==0)!=(self.first_call_id is None and self.last_call_id is None):
            raise ValueError("streamed native ledger omits its actual ordered cursor")
        if any(not value.is_finite() or value<0 for value in (self.top_level_wall_seconds,self.top_level_cpu_seconds)):
            raise ValueError("streamed native ledger invents measured expense")


@dataclass(frozen=True, slots=True)
class TrajectoryAttempt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/trajectory-attempt"
    trajectory_id: str
    roster: tuple[str,str,str,str,str]
    disposition: str
    elapsed_seconds: Decimal | None
    cpu_seconds: Decimal | None
    global_step_count: int
    global_time_picosecond: Decimal
    production_time_picosecond: Decimal
    coordinate_frames: int
    observable_frames: int
    checkpoints: int
    members: tuple[NativeMember, ...]
    native_ledger: tuple[NativeLedgerSegment, ...]
    error_text: str | None

    def __post_init__(self):
        validate_stable_id(self.trajectory_id)
        if self.roster not in trajectory_roster() or self.disposition not in (
            "ACQUIRED_PENDING_ENSEMBLE_ASSESSMENT", "TECHNICAL_FAILURE",
            "UNENTERED_CALIBRATION_UNEVALUABLE", "UNENTERED_CALIBRATION_REFUSED"):
            raise ValueError("trajectory changes complete roster/actual entry status")
        if min(self.global_step_count,self.coordinate_frames,self.observable_frames,self.checkpoints) < 0:
            raise ValueError("negative actual trajectory census")
        for value in (self.global_time_picosecond,self.production_time_picosecond):
            if not value.is_finite() or value < 0:
                raise ValueError("invalid actual native clock")
        for value in (self.elapsed_seconds,self.cpu_seconds):
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError("invalid actual attempt expense")
        if self.disposition.startswith("UNENTERED") and (self.global_step_count or self.native_ledger or self.production_time_picosecond or self.error_text):
            raise ValueError("unentered row invents native work/error")
        if self.disposition == "TECHNICAL_FAILURE" and not self.error_text:
            raise ValueError("technical failure omits its original error")
        if tuple(sorted(row.relative_path for row in self.members)) != tuple(row.relative_path for row in self.members):
            raise ValueError("native member census is not sorted")


@dataclass(frozen=True, slots=True)
class SamplingProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/product"
    product_id: str
    source: ObjectIdentity
    preparation_assessment: ObjectIdentity
    trajectories: tuple[TrajectoryAttempt, ...]
    complete_members: tuple[NativeMember, ...]
    acquisition_round: int
    prior_sampling: ObjectIdentity | None = None
    biological_disposition: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if tuple(row.roster for row in self.trajectories) != trajectory_roster() or self.acquisition_round < 1:
            raise ValueError("sampling result omits/reorders complete96 denominator")
        if self.biological_disposition is not A.UNEVALUABLE or self.physical_independent_units != 0:
            raise ValueError("simulation promotes kinetic or biological authority")
        if (self.acquisition_round == 1) != (self.prior_sampling is None):
            raise ValueError("adaptive extension changes authentic prior trajectory lineage")


@dataclass(frozen=True, slots=True)
class ScalarDiagnostic(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/scalar-diagnostic"
    trajectory_id: str
    metric_id: str
    retained_frames: int
    equilibration_discard: int
    statistical_inefficiency: Decimal | None
    effective_samples: Decimal | None
    mean: Decimal | None
    confidence_halfwidth: Decimal | None
    half_run_drift: Decimal | None
    precision_target: Decimal
    converged: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.trajectory_id)
        if self.metric_id not in METRICS or self.precision_target!=dict(PRECISION)[self.metric_id] or min(self.retained_frames,self.equilibration_discard)<0:
            raise ValueError("scalar diagnostic changes selected metric/precision/census")
        for value in (self.statistical_inefficiency,self.effective_samples,self.mean,self.confidence_halfwidth,self.half_run_drift):
            if value is not None and not value.is_finite():
                raise ValueError("scalar diagnostic invents finite precision")
        if self.converged and (self.reason_codes or any(row is None for row in (self.mean,self.confidence_halfwidth,self.half_run_drift,self.statistical_inefficiency,self.effective_samples)) or self.confidence_halfwidth>self.precision_target or self.half_run_drift>self.precision_target):
            raise ValueError("scalar convergence hides unresolved uncertainty/drift")


@dataclass(frozen=True, slots=True)
class SamplingAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/assessment"
    product_id: str
    source: ObjectIdentity
    sampling: ObjectIdentity
    preparation_assessment: ObjectIdentity
    diagnostics: tuple[ScalarDiagnostic, ...]
    complete_custody: A
    numerical_conformance: A
    ensemble_convergence: A
    donor_structural_contrast: A
    gp_m1_structural_contrast: A
    gp_v1_structural_contrast: A
    kinetic_transport: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if self.kinetic_transport is not A.UNEVALUABLE or self.physical_independent_units != 0:
            raise ValueError("structural contrast invents kinetic transport/physical units")


@dataclass(frozen=True, slots=True)
class CalibrationCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/calibration-case"
    case_id: str
    roster: tuple[str,str,str,str,str]
    disposition: A
    entry_status: str
    atom_count: int
    force_rms_relative_error: Decimal | None
    energy_error_kj_mol_per_atom: Decimal | None
    nve_time_picosecond: Decimal
    nve_max_energy_excursion_kj_mol_per_atom: Decimal | None
    native_steps: int
    measured_integration_wall_seconds: Decimal | None
    members: tuple[NativeMember, ...]
    native_calls: tuple[p.NativeCall, ...]
    error_text: str | None
    force_control_relative_path: str | None
    nve_control_relative_path: str | None

    def __post_init__(self):
        validate_stable_id(self.case_id)
        if self.roster not in trajectory_roster() or self.atom_count < 0 or self.native_steps < 0 or self.nve_time_picosecond < 0:
            raise ValueError("calibration changes actual full-model/control census")
        if self.entry_status not in ("ENTERED", "UNENTERED_PREPARATION_UNEVALUABLE", "UNENTERED_PREPARATION_REFUSED", "UNENTERED_SHARED_CONTROL_FAILURE"):
            raise ValueError("calibration conceals whether native control actually entered")
        if self.entry_status != "ENTERED" and (self.native_steps or self.nve_time_picosecond or self.measured_integration_wall_seconds is not None):
            raise ValueError("unentered numerical row invents actual integration")
        if self.disposition is A.SATISFIED and (self.atom_count == 0 or abs(self.nve_time_picosecond-100) > Decimal("0.0000001") or self.native_steps == 0 or self.error_text is not None or not self.force_control_relative_path or not self.nve_control_relative_path):
            raise ValueError("successful calibration omits actual complete numerical window")


@dataclass(frozen=True, slots=True)
class CalibrationProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/calibration-product"
    product_id: str
    source: ObjectIdentity
    preparation_assessment: ObjectIdentity
    cases: tuple[CalibrationCase, ...]
    complete_members: tuple[NativeMember, ...]
    native_calls: tuple[p.NativeCall, ...]
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if tuple(row.roster for row in self.cases) != trajectory_roster() or self.physical_independent_units != 0:
            raise ValueError("calibration omits complete96 numerical controls or promotes physical units")
        actual = {r.call_id: r for r in self.native_calls}
        if len(actual) != len(self.native_calls) or any(actual.get(r.call_id) != r for case in self.cases for r in case.native_calls):
            raise ValueError("numerical controls substitute the unique inclusive native call ledger")


@dataclass(frozen=True, slots=True)
class CalibrationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/calibration-assessment"
    product_id: str
    source: ObjectIdentity
    calibration: ObjectIdentity
    preparation_assessment: ObjectIdentity
    numerical_cases: tuple[tuple[str,A,tuple[str,...]], ...]
    paired_step_checks: tuple[tuple[str,A,Decimal | None,Decimal | None], ...]
    numerical_conformance: A
    raw_initial_coordinate_bytes_forecast: int | None
    raw_checkpoint_bytes_forecast: int | None
    production_wall_seconds_forecast: Decimal | None
    biological_disposition: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if self.biological_disposition is not A.UNEVALUABLE or self.physical_independent_units != 0:
            raise ValueError("numerical calibration invents biological validation")
