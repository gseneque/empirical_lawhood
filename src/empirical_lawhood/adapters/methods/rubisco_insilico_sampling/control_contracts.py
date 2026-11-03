# SPDX-License-Identifier: MPL-2.0
"""Selected chemical/force prerequisites, without absent prepared operands.

This first stage enters only selected genuine models. All 24 model and 96
100 ps controls remain in its census; it does not admit production sampling.
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.native_subwork import NativeSubworkState

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import PreparationIntegrity
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import PhysicalPreparationGeometry

from . import contracts as c


def model_id(key):
    return "model." + ".".join(key)


def force_id(key):
    return "control.chemical-force." + model_id(key)


def nve_id(key):
    return "control.nve." + ".".join(key)


def control_ids():
    return tuple(sorted((*[force_id(key) for key in p.model_roster()],
                         *[nve_id(key) for key in c.trajectory_roster()])))


@dataclass(frozen=True, slots=True)
class ChemicalForcePlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/chemical-force-plan"
    plan_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    assignment_integrity: ObjectIdentity
    mathematical_geometry: ObjectIdentity
    # Model IDs with actual asset identities only. No empty positive placeholders.
    selected_assets: tuple[tuple[str, ObjectIdentity], ...]
    # Original definition, completion and full unit return for every selected model.
    preparation_custody: tuple[tuple[str, ObjectIdentity, ObjectIdentity, ObjectIdentity], ...]
    hardware: c.HardwareSelection
    workdir: str
    interpreter_path: str
    interpreter_sha256: str
    engine_inventory_sha256: str
    hardware_inspector_path: str
    hardware_inspector_sha256: str
    code_sources: tuple[tuple[str, str], ...]
    dependency_lock_sha256: str
    cutoff_nanometer: Decimal = Decimal("1")
    temperature_kelvin: Decimal = Decimal("298")
    platform_precision: str = "mixed"
    device_index: str = "0"
    deterministic_forces: str = "true"
    use_cpu_pme: str = "false"
    minimizer_tolerance_kj_mol_nm: Decimal = Decimal("10")
    minimizer_max_iterations: int = 0
    minimizer_reporter_early_stop: bool = False
    objective_rms_normalization: str = "SQRT_SUM_ALL_3N_OBJECTIVE_COMPONENTS_SQUARED_OVER_N_PARTICLES"
    # External OS driver bytes are separate from immutable selected engine stock.
    external_runtime_files: tuple[tuple[str, int, str], ...] = ()
    terminal_position_join: str = "FINITE_BINARY64_EXACT_BITS"
    model_census: tuple[tuple[str, str, str], ...] = p.model_roster()
    nve_census: tuple[tuple[str, str, str, str, str], ...] = c.trajectory_roster()
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        for row, schema in ((self.source, p.PreparationSelection.SCHEMA),
                            (self.preparation, p.PreparationProduct.SCHEMA),
                            (self.assignment_integrity, PreparationIntegrity.SCHEMA),
                            (self.mathematical_geometry, PhysicalPreparationGeometry.SCHEMA)):
            if type(row) is not ObjectIdentity or row.object_schema != schema:
                raise ValueError("chemical/force control substitutes its original independent operands")
            row.__post_init__()
        expected = {model_id(key) for key in p.model_roster()}
        ids = tuple(name for name, _ in self.selected_assets)
        if not ids or ids != tuple(sorted(set(ids))) or set(ids) - expected:
            raise ValueError("chemical/force control needs an explicit genuine model subset")
        for _, row in self.selected_assets:
            if type(row) is not ObjectIdentity or row.object_schema != p.ModelAssets.SCHEMA:
                raise ValueError("chemical/force control substitutes genuine model assets")
            row.__post_init__()
        if tuple(row[0] for row in self.preparation_custody) != ids:
            raise ValueError("chemical/force control omits original model custody")
        from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkCompletion
        from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn
        for _, definition, completion, returned in self.preparation_custody:
            for row, kind in ((definition, NativeSubworkDefinition), (completion, NativeSubworkCompletion), (returned, DurableUnitReturn)):
                if type(row) is not ObjectIdentity or row.object_schema != kind.SCHEMA:
                    raise ValueError("chemical/force control changes original preparation receipt owners")
                row.__post_init__()
        self.hardware.__post_init__()
        for name in ("interpreter_sha256", "engine_inventory_sha256", "hardware_inspector_sha256", "dependency_lock_sha256"):
            validate_sha256(getattr(self, name))
        for name in ("workdir", "interpreter_path", "hardware_inspector_path"):
            path = PurePosixPath(getattr(self, name))
            if not path.is_absolute() or ".." in path.parts:
                raise ValueError("chemical/force control needs exact selected absolute paths")
        if not PurePosixPath(self.workdir).is_relative_to(p.NATIVE_WORK_ROOT) or self.workdir == p.NATIVE_WORK_ROOT:
            raise ValueError("chemical/force control needs a fresh selected molecular workdir")
        if not self.code_sources or tuple(row[0] for row in self.code_sources) != tuple(sorted(set(row[0] for row in self.code_sources))):
            raise ValueError("chemical/force control omits exact producing source")
        for path, digest in self.code_sources:
            if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
                raise ValueError("chemical/force source escapes its selected root")
            validate_sha256(digest)
        if tuple(row[0] for row in self.external_runtime_files) != tuple(sorted(set(row[0] for row in self.external_runtime_files))):
            raise ValueError("chemical/force control duplicates selected external runtime files")
        for path,size,digest in self.external_runtime_files:
            if not PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or type(size) is not int or size <= 0:
                raise ValueError("chemical/force external runtime omits exact absolute full file bytes")
            validate_sha256(digest)
        if (self.model_census != p.model_roster() or self.nve_census != c.trajectory_roster()
                or self.physical_independent_units != 0 or self.cutoff_nanometer != 1 or self.temperature_kelvin != 298
                or self.platform_precision != "mixed" or self.device_index != "0"
                or self.deterministic_forces != "true" or self.use_cpu_pme != "false"
                or self.minimizer_tolerance_kj_mol_nm != Decimal("10")
                or type(self.minimizer_max_iterations) is not int or self.minimizer_max_iterations != 0
                or self.minimizer_reporter_early_stop is not False
                or self.objective_rms_normalization != "SQRT_SUM_ALL_3N_OBJECTIVE_COMPONENTS_SQUARED_OVER_N_PARTICLES"
                or self.terminal_position_join != "FINITE_BINARY64_EXACT_BITS"):
            raise ValueError("chemical/force control changes frozen numerical science or 24/96 denominator")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.plan_id, self)


@dataclass(frozen=True, slots=True)
class ChemicalForceReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/chemical-force-return"
    unit_id: str
    plan: ObjectIdentity
    assets: ObjectIdentity
    operators_completed: bool
    atom_count: int
    force_receiver_path: str | None
    files: tuple[p.FileEvidence, ...]
    native_calls: tuple[ObjectIdentity, ...]
    error_text: str | None = None
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if self.unit_id not in tuple(force_id(key) for key in p.model_roster()):
            raise ValueError("chemical/force return cannot manufacture an unentered NVE result")
        self.plan.__post_init__()
        self.assets.__post_init__()
        if self.plan.object_schema != ChemicalForcePlan.SCHEMA or self.assets.object_schema != p.ModelAssets.SCHEMA:
            raise ValueError("chemical/force return substitutes its actual source")
        if type(self.operators_completed) is not bool or type(self.atom_count) is not int or self.atom_count < 0 or self.physical_independent_units != 0:
            raise ValueError("chemical/force return manufactures physical preparation")
        paths = tuple(row.relative_path for row in self.files)
        if paths != tuple(sorted(set(paths))) or tuple(row.object_id for row in self.native_calls) != tuple(sorted(set(row.object_id for row in self.native_calls))):
            raise ValueError("chemical/force return omits complete original file/call census")
        for row in self.files:
            row.__post_init__()
        from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
        for row in self.native_calls:
            if type(row) is not ObjectIdentity or row.object_schema != NativeSubworkDefinition.SCHEMA:
                raise ValueError("control return changes its actual conditional native-call identities")
            row.__post_init__()
        required = {"minimized.xml", "cpu-force-reference.xml", "minimizer-termination.json",
            "minimizer-progress.jsonl", "declared-system-constraints.json", "minimizer-apparatus.json",
            "apparatus-cuda.json", "apparatus-cpu.json"}
        names = {PurePosixPath(path).name for path in paths}
        if self.operators_completed and (self.atom_count <= 0 or self.force_receiver_path not in paths
                or self.error_text is not None or not self.native_calls or not required.issubset(names)
                or not any(name.startswith("controlled-system-") for name in names)
                or not any(name.startswith("controlled-integrator-") for name in names)):
            raise ValueError("completed operators omit full actual force receivers")
        if not self.operators_completed and not self.error_text:
            raise ValueError("known adverse control omits its retained error")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.unit_id, self)


@dataclass(frozen=True, slots=True)
class ChemicalForceAssessment(CanonicalRecord):
    """Numerical prerequisites at their exact scope, never equilibrium or kinetics."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/chemical-force-assessment"
    product_id: str
    plan: ObjectIdentity
    returned: ObjectIdentity
    objective_precision_disposition: A
    force_agreement_disposition: A
    objective_gradient_rms_kj_mol_nm: Decimal | None
    maximum_constraint_relative_error: Decimal | None
    force_relative_error: Decimal | None
    energy_difference_kj_mol_per_atom: Decimal | None
    reason_codes: tuple[str, ...]
    physical_preparation_disposition: A = A.UNEVALUABLE
    ensemble_disposition: A = A.UNEVALUABLE
    kinetic_disposition: A = A.UNEVALUABLE
    native_optimizer_convergence_disposition: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if self.plan.object_schema != ChemicalForcePlan.SCHEMA or self.returned.object_schema != ChemicalForceReturn.SCHEMA:
            raise ValueError("control assessment changes the authentic plan/return")
        for row in (self.plan, self.returned):
            row.__post_init__()
        for verdict in (self.objective_precision_disposition, self.force_agreement_disposition):
            if type(verdict) is not A:
                raise ValueError("control assessment needs typed dispositions")
        for value in (self.objective_gradient_rms_kj_mol_nm, self.maximum_constraint_relative_error,
                      self.force_relative_error, self.energy_difference_kj_mol_per_atom):
            if value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0):
                raise ValueError("control assessment substitutes finite nonnegative numerical receivers")
        if self.objective_precision_disposition is A.SATISFIED and (
                self.objective_gradient_rms_kj_mol_nm is None or self.maximum_constraint_relative_error is None
                or self.objective_gradient_rms_kj_mol_nm > Decimal("10")
                or self.maximum_constraint_relative_error > c.INTEGRATION[0][2]):
            raise ValueError("positive objective precision omits terminal objective/constraint operands")
        if self.force_agreement_disposition is A.SATISFIED and (
                self.force_relative_error is None or self.energy_difference_kj_mol_per_atom is None
                or self.force_relative_error > Decimal("0.0001")
                or self.energy_difference_kj_mol_per_atom > Decimal("0.0001")):
            raise ValueError("positive force agreement omits independently reduced receivers")
        if any(row is not A.UNEVALUABLE for row in (self.physical_preparation_disposition,
                self.ensemble_disposition, self.kinetic_disposition,self.native_optimizer_convergence_disposition)) or self.physical_independent_units != 0:
            raise ValueError("numerical prerequisites cannot establish physical/ensemble/kinetic success")


@dataclass(frozen=True, slots=True)
class ChemicalForceCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/chemical-force-census"
    plan: ObjectIdentity
    states: tuple[tuple[str, NativeSubworkState], ...]
    physical_independent_units: int = 0

    def __post_init__(self):
        if self.plan.object_schema != ChemicalForcePlan.SCHEMA or tuple(row[0] for row in self.states) != control_ids() or self.physical_independent_units != 0:
            raise ValueError("chemical/force census drops unentered/adverse 24/96 controls")
        if any(type(state) is not NativeSubworkState for _, state in self.states):
            raise ValueError("chemical/force census substitutes actual contact state")
