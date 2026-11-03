# SPDX-License-Identifier: MPL-2.0
"""Scientific selections; importing this module constructs no native model."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition as A,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    validate_nonempty,
    validate_sha256,
    validate_stable_id,
)

NAMESPACE = "rubisco-insilico-dynamics"
UNIT = "rubisco.exposed-gp-te-structural-family"
QUESTION = "Does a controlled full L8S8 donor/recipient comparison produce parameter-complete models and robust structural/dynamical contrasts under declared preparation and numerical sensitivities?"
JOINT_VIEWS = (("joint-01", 173, Decimal("-60")), ("joint-02", 419, Decimal("180")))
ENGINE_ROOT = (
    "/dev/shm/empirical-lawhood-applied-el-20261011-reopen01/rubisco-insilico-engine01"
)
ENGINE_INVENTORY_SHA256 = (
    "17725dcd46a7fd77f49f6a6b5512ee5e2739baec98ddb307c5eeb143bf08e8d5"
)
NATIVE_WORK_ROOT = "/media/chevre/SEMIOS/empirical-lawhood-applied-el/20261011/reopen01/rubisco-insilico01/working"
CHEMICAL_STATE = "ACTIVATED_KCX_MG_CABP_INHIBITED_NOT_REACTIVE_PRODUCT"
CONSTRUCTS = (
    "gp.i95m.m1",
    "gp.i95m.v1",
    "gp.wt.m1",
    "gp.wt.v1",
    "te.p415a.v98m",
    "te.p415a.wt-ssu",
)
PARAMETER_VIEWS = ("published-global-kcx-override", "scoped-kcx-aliases")
KCX_ALIASES = (
    ("C", "K2"),
    ("CT", "K1"),
    ("H", "K6"),
    ("H1", "K4"),
    ("HC", "K5"),
    ("N", "K0"),
    ("O", "K7"),
    ("O2", "K3"),
)


@dataclass(frozen=True, slots=True)
class SourceMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/source-member"
    member_id: str
    original_url: str
    sha256: str
    raw_utf8: str

    def __post_init__(self):
        validate_stable_id(self.member_id)
        validate_nonempty(self.original_url, field_name="original_url")
        validate_sha256(self.sha256)
        if sha256(self.raw_utf8.encode()).hexdigest() != self.sha256:
            raise ValueError("molecular source original-byte substitution")


@dataclass(frozen=True, slots=True)
class Construct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/construct"
    construct_id: str
    lsu_sequence: str
    ssu_sequence: str
    lsu_mutation_positions: tuple[int, ...]
    ssu_mutation_positions: tuple[int, ...]
    large_subunits: int = 8
    small_subunits: int = 8

    def __post_init__(self):
        if self.construct_id not in CONSTRUCTS:
            raise ValueError(
                "construct is outside the controlled donor/recipient roster"
            )
        expected = (493, 138) if self.construct_id.startswith("gp.") else (475, 118)
        if (len(self.lsu_sequence), len(self.ssu_sequence)) != expected or any(
            x not in "ACDEFGHIKLMNPQRSTVWY"
            for x in self.lsu_sequence + self.ssu_sequence
        ):
            raise ValueError("controlled assembly omits/substitutes complete sequence")
        if (self.large_subunits, self.small_subunits) != (8, 8):
            raise ValueError("the controlled comparison requires all L8S8 subunits")
        if self.construct_id.startswith("gp."):
            mutant = self.construct_id.startswith("gp.i95m.")
            expected_first = "M" if self.construct_id.endswith(".m1") else "V"
            if (
                self.lsu_mutation_positions
                or self.ssu_mutation_positions != ((95,) if mutant else ())
                or self.ssu_sequence[94] != ("M" if mutant else "I")
                or self.ssu_sequence[0] != expected_first
            ):
                raise ValueError("Gp intervention changes its selected identity")
        elif (
            self.lsu_mutation_positions != (415,)
            or self.lsu_sequence[414] != "A"
            or self.ssu_mutation_positions
            != ((98,) if self.construct_id.endswith(".v98m") else ())
            or self.ssu_sequence[97]
            != ("M" if self.construct_id.endswith(".v98m") else "V")
        ):
            raise ValueError("donor comparison substitutes the LSU-P415A background")


@dataclass(frozen=True, slots=True)
class PreparationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/preparation-selection"
    )
    selection_id: str
    structural_inventory: ObjectIdentity
    structural_coordinates: ObjectIdentity
    nomination: ObjectIdentity
    native_workdir: str
    engine_inventory_sha256: str
    constructs: tuple[Construct, ...]
    source_members: tuple[SourceMember, ...]
    joint_coordinate_views: tuple[tuple[str, int, Decimal], ...] = JOINT_VIEWS
    parameter_views: tuple[str, ...] = PARAMETER_VIEWS
    kcx_aliases: tuple[tuple[str, str], ...] = KCX_ALIASES
    chemical_state: str = CHEMICAL_STATE
    pH: Decimal = Decimal("8")
    temperature_kelvin: Decimal = Decimal("298")
    pressure_atmosphere: Decimal = Decimal("1")
    water_model: str = "TIP3P"
    nonbonded_method: str = "PME"
    cutoff_nanometer: Decimal = Decimal("1")
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        validate_sha256(self.engine_inventory_sha256)
        path = PurePosixPath(self.native_workdir)
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(NATIVE_WORK_ROOT)
            or str(path) == NATIVE_WORK_ROOT
        ):
            raise ValueError(
                "native preparation needs an explicitly selected fresh workdir"
            )
        if (
            tuple(x.construct_id for x in self.constructs) != CONSTRUCTS
            or self.parameter_views != PARAMETER_VIEWS
            or self.kcx_aliases != KCX_ALIASES
            or self.chemical_state != CHEMICAL_STATE
            or self.pH != Decimal("8")
            or self.temperature_kelvin != Decimal("298")
            or self.pressure_atmosphere != Decimal("1")
            or self.water_model != "TIP3P"
            or self.nonbonded_method != "PME"
            or self.cutoff_nanometer != Decimal("1")
            or self.physical_independent_units != 0
            or self.joint_coordinate_views != JOINT_VIEWS
            or self.engine_inventory_sha256 != ENGINE_INVENTORY_SHA256
        ):
            raise ValueError(
                "prospective preparation changes its closed scientific operands"
            )
        if self.structural_inventory.object_schema != (
            "empirical-lawhood/rubisco-insilico-structure/inventory"
        ):
            raise ValueError(
                "model preparation needs authentic assessed full-assembly inventory"
            )
        for row in self.constructs + self.source_members:
            row.__post_init__()
        if (
            self.structural_coordinates.object_schema
            != "empirical-lawhood/rubisco-insilico-structure/assembly-coordinates"
            or self.nomination.object_schema
            != "empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier"
            or self.nomination.object_fingerprint
            != "8121b9e941cbc66d0634dbc9f3047c6e22232fb1a783f2a313a17bf5f63f35fa"
        ):
            raise ValueError(
                "preparation substitutes actual observed coordinates/nomination"
            )
        ids = tuple(row.member_id for row in self.source_members)
        if not ids or ids != tuple(sorted(set(ids))):
            raise ValueError("source inventory is empty, duplicated or unordered")


@dataclass(frozen=True, slots=True)
class DerivedParameterStock(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/derived-parameter-stock"
    )
    source_prepi_sha256: str
    source_frcmod_sha256: str
    aliases: tuple[tuple[str, str], ...]
    scoped_prepi_utf8: str
    scoped_custom_frcmod_utf8: str
    # Original tokens, not a newly fitted charge assignment.
    atom_charge_tokens: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_sha256(self.source_prepi_sha256)
        validate_sha256(self.source_frcmod_sha256)
        if self.aliases != KCX_ALIASES or not self.atom_charge_tokens:
            raise ValueError(
                "scoped stock changes its exact atom-type/charge declaration"
            )


@dataclass(frozen=True, slots=True)
class BoundaryParameterStock(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/boundary-parameter-stock"
    )
    source_parm_dat_sha256: str
    source_ff14sb_sha256: str
    aliases: tuple[tuple[str, str], ...]
    scoped_boundary_frcmod_utf8: str
    term_line_census: tuple[tuple[str, int], ...]

    def __post_init__(self):
        validate_sha256(self.source_parm_dat_sha256)
        validate_sha256(self.source_ff14sb_sha256)
        if (
            self.aliases != KCX_ALIASES
            or tuple(section for section, _ in self.term_line_census)
            != ("MASS", "BOND", "ANGLE", "DIHE", "IMPROPER", "NONBON")
            or any(count <= 0 for _, count in self.term_line_census)
            or not self.scoped_boundary_frcmod_utf8
        ):
            raise ValueError("boundary stock changes its complete derivation census")


def identity(record):
    for name in ("input_id", "selection_id", "config_id", "product_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("unknown dynamics scientific record identity")


def scope(source):
    return ScientificConditionScope(
        "system.rubisco-insilico.gp-i95m",
        "world.rubisco-insilico.dynamics",
        source.selection_id,
        ("complete-model-preparation", "dynamic-contrast", "parameter-coverage"),
        ("dimensionless", "dimensionless", "dimensionless"),
        "receiver.full-l8s8-native-model-not-kinetics",
        "clock.rubisco-insilico.preparation",
        "Exact donor/recipient full materials, activated KCX/Mg/CABP inhibited state and declared source/model sensitivities; numerical preparation does not establish productive kinetics.",
        source_config_sha256=source.fingerprint(),
        instance_id="material.gp-i95m.m1.tag-free.v2",
    )


def model_roster():
    return tuple(
        (construct, view[0], parameters)
        for construct in CONSTRUCTS
        for view in JOINT_VIEWS
        for parameters in PARAMETER_VIEWS
    )


@dataclass(frozen=True, slots=True)
class FileEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/file-evidence"
    relative_path: str
    byte_count: int
    sha256: str

    def __post_init__(self):
        validate_sha256(self.sha256)
        if (
            not self.relative_path
            or self.relative_path.startswith("/")
            or ".." in self.relative_path.split("/")
            or self.byte_count < 0
        ):
            raise ValueError("model custody changes relative path/byte inventory")


@dataclass(frozen=True, slots=True)
class NativeTextFile(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/native-text-file"
    )
    evidence: FileEvidence
    raw_utf8: str

    def __post_init__(self):
        raw = self.raw_utf8.encode()
        self.evidence.__post_init__()
        if (
            len(raw) != self.evidence.byte_count
            or sha256(raw).hexdigest() != self.evidence.sha256
        ):
            raise ValueError("native model file substitutes retained bytes")


@dataclass(frozen=True, slots=True)
class ModelAssets(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/model-assets"
    product_id: str
    source: ObjectIdentity
    construct_id: str
    joint_view_id: str
    parameter_view: str
    files: tuple[NativeTextFile, ...]

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (
            self.construct_id,
            self.joint_view_id,
            self.parameter_view,
        ) not in model_roster():
            raise ValueError("native model assets change selected material/model view")
        paths = tuple(row.evidence.relative_path for row in self.files)
        if paths != tuple(sorted(set(paths))):
            raise ValueError(
                "native model assets duplicate/reorder complete file census"
            )
        for row in self.files:
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class NativeCall(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/native-call"
    call_id: str
    parent_call_id: str | None
    model_id: str
    role: str
    requested_json: str
    realized_json: str
    measured_wall_seconds: Decimal
    measured_cpu_seconds: Decimal
    termination: str
    error_text: str | None
    files: tuple[FileEvidence, ...]

    def __post_init__(self):
        validate_stable_id(self.call_id)
        if any(
            not x.is_finite() or x < 0
            for x in (self.measured_wall_seconds, self.measured_cpu_seconds)
        ) or self.termination not in ("COMPLETED", "TECHNICAL_FAILURE"):
            raise ValueError("native attempt changes actual measured cost/termination")


@dataclass(frozen=True, slots=True)
class PreparedModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/prepared-model"
    model_id: str
    construct: Construct
    joint_view_id: str
    parameter_view: str
    disposition: A
    reason_codes: tuple[str, ...]
    files: tuple[FileEvidence, ...]
    assets: ObjectIdentity
    atom_count: int
    complete_parameter_census: tuple[tuple[str, int], ...]
    provenance_manifest_path: str | None
    native_call_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.model_id)
        self.construct.__post_init__()
        if (
            self.joint_view_id not in tuple(row[0] for row in JOINT_VIEWS)
            or self.parameter_view not in PARAMETER_VIEWS
            or self.atom_count < 0
        ):
            raise ValueError("prepared model changes frozen material/model view")
        if self.disposition is A.SATISFIED and (
            not self.files
            or self.atom_count <= 0
            or not self.complete_parameter_census
            or self.provenance_manifest_path is None
            or not self.native_call_ids
        ):
            raise ValueError(
                "completed model omits actual parameter/provenance custody"
            )


@dataclass(frozen=True, slots=True)
class PreparationProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/preparation-product"
    )
    product_id: str
    source: ObjectIdentity
    structural_inventory: ObjectIdentity
    structural_coordinates: ObjectIdentity
    nomination: ObjectIdentity
    models: tuple[PreparedModel, ...]
    native_calls: tuple[NativeCall, ...]
    files: tuple[FileEvidence, ...]
    scientific_native_operations: int
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        actual = tuple(
            (row.construct.construct_id, row.joint_view_id, row.parameter_view)
            for row in self.models
        )
        if (
            actual != model_roster()
            or self.physical_independent_units != 0
            or self.scientific_native_operations != 1
            or len({row.call_id for row in self.native_calls}) != len(self.native_calls)
        ):
            raise ValueError(
                "preparation omits/duplicates full selected attempt census"
            )
        call_ids = {row.call_id for row in self.native_calls}
        if any(set(row.native_call_ids) - call_ids for row in self.models):
            raise ValueError("prepared model invents its native call custody")


@dataclass(frozen=True, slots=True)
class PreparationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/preparation-assessment"
    )
    product_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    structural_inventory: ObjectIdentity
    nomination: ObjectIdentity
    model_dispositions: tuple[tuple[str, A, tuple[str, ...]], ...]
    preparation_disposition: A
    prior_nomination_scope: ScientificConditionScope
    dynamics_disposition: A = A.UNEVALUABLE
    kinetic_disposition: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        if (
            len(self.model_dispositions) != len(model_roster())
            or self.dynamics_disposition is not A.UNEVALUABLE
            or self.kinetic_disposition is not A.UNEVALUABLE
            or self.physical_independent_units != 0
        ):
            raise ValueError(
                "preparation assessment drops denominator/promotes dynamics or biology"
            )


@dataclass(frozen=True, slots=True)
class PreparationOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-dynamics/preparation-operation-config"
    )
    config_id: str
    operation: str
    source: PreparationSelection
    prior_nomination_scope: ScientificConditionScope
    operands: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        self.source.__post_init__()
        if (
            self.operation not in ("prepare", "assess-preparation")
            or self.config_id != "config." + NAMESPACE + "." + self.operation
        ):
            raise ValueError("preparation config changes selected operation")
        expected = tuple(
            sorted(
                (
                    identity(self.source),
                    self.source.structural_inventory,
                    self.source.structural_coordinates,
                    self.source.nomination,
                ),
                key=lambda row: row.object_id,
            )
        )
        if self.operands != expected:
            raise ValueError(
                "preparation config changes actual source/history operands"
            )
