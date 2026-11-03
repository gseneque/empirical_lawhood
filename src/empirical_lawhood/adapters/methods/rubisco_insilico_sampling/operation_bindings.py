# SPDX-License-Identifier: MPL-2.0
"""Installed current chemical and NVE declarations; historical plans stay exact."""

from dataclasses import dataclass, fields
from hashlib import sha256
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import GeometryReusePlan
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_preparation_assessment import (
    SerializedPreparationGeometry, SerializedPreparationIntegrity)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition)
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .closed_raw_model_admission import (
    ClosedRawModelHistory, ClosedRawModelInstance, ClosedRawModelSupply, InstanceChemicalForcePlan,
    KnownDerivedModelInstance, ModelInstanceInputs)
from .control_contracts import ChemicalForceCensus
from .control_preparation_admission import ReusedGeometryChemicalForcePlan, SerializedDurableChemicalForcePlan
from .derived_model_admission import DerivedChemicalForcePlan, DerivedModelSupply
from .nve_contracts import NVEControlCensus, RelaxedModelSupply
from .serialized_nve_custody import ChemicalForceCustodySupply, SerializedCustodyNVEControlPlan
from .unit_stream import MEDIA as STREAM_MEDIA, SAMPLING_STORAGE_CODECS, SamplingUnitStreamChunk

NAMESPACE = "rubisco-insilico-sampling"
OPERATIONS = ("chemical-force", "nve-control")
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
QUESTION = "Do the exactly supplied original molecular models return independently assessable numerical controls with complete adverse and unentered denominators?"


@dataclass(frozen=True, slots=True)
class SamplingOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/operation-config"
    config_id: str
    operation: str
    plan_payload: str
    source: p.PreparationSelection
    source_root: str
    invocation_path: str
    environment: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.operation not in OPERATIONS or self.config_id != "config." + NAMESPACE + "." + self.operation:
            raise ValueError("sampling changes its exact registered operation/config identity")
        plan = self.plan
        self.source.__post_init__()
        selected_source = plan.source if self.operation == "chemical-force" else plan.chemical_controls.source
        engine = plan.engine_inventory_sha256 if self.operation == "chemical-force" else plan.chemical_controls.engine_inventory_sha256
        if selected_source != p.identity(self.source) or engine != self.source.engine_inventory_sha256:
            raise ValueError("sampling substitutes its exact original source/engine inputs")
        root, invocation = PurePosixPath(self.source_root), PurePosixPath(self.invocation_path)
        if (not root.is_absolute() or not invocation.is_absolute() or ".." in root.parts or ".." in invocation.parts
                or str(root) != self.source_root or str(invocation) != self.invocation_path
                or invocation.is_relative_to(plan.workdir)):
            raise ValueError("sampling needs explicit exact source and fresh invocation outside native work")
        if (type(self.environment) is not tuple or self.environment != tuple(sorted(set(self.environment)))
                or len(dict(self.environment)) != len(self.environment)
                or any(type(key) is not str or type(value) is not str or not key or "=" in key or "\x00" in key + value
                    for key, value in self.environment)):
            raise ValueError("sampling requires its exact complete selected process environment")
        environment = dict(self.environment)
        if (environment.get("PYTHONDONTWRITEBYTECODE") != "1" or environment.get("PYTHONPATH") != str(root / "src")
                or not environment.get("OPENMM_PLUGIN_DIR") or not PurePosixPath(environment["OPENMM_PLUGIN_DIR"]).is_absolute()
                or any(environment.get(name) != "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS",
                    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"))):
            raise ValueError("sampling requires its explicitly selected plugin and single-thread environment")

    @property
    def plan(self):
        if self.operation == "chemical-force":
            from .control_preparation_admission import decode_plan
            plan = decode_plan(self.plan_payload)
            if type(plan) is not InstanceChemicalForcePlan:
                raise ValueError("current chemical route requires exact plan revision 1.4.0; historical readers remain separate")
        elif self.operation == "nve-control":
            from .nve_preparation_admission import decode_plan
            plan = decode_plan(self.plan_payload)
            if type(plan) is not SerializedCustodyNVEControlPlan:
                raise ValueError("current NVE route requires exact plan revision 1.2.0; historical readers remain separate")
        else:
            raise ValueError("sampling changes its installed operation")
        if plan.canonical_bytes().decode() != self.plan_payload:
            raise ValueError("sampling changes original complete immutable plan bytes")
        return plan

    @property
    def node_id(self):
        return NAMESPACE + "." + self.operation

    @property
    def operands(self):
        plan = self.plan
        identities = plan.instance_operands if self.operation == "chemical-force" else plan.custody_source_identities
        return tuple(sorted({plan.identity, *identities}, key=lambda row: row.object_id))


INPUT_RECORD_TYPES = tuple(sorted((
    p.PreparationSelection, p.ModelAssets, p.PreparationProduct, p.NativeTextFile,
    ModelInstanceInputs, InstanceChemicalForcePlan, ClosedRawModelInstance, KnownDerivedModelInstance,
    ClosedRawModelSupply, ClosedRawModelHistory, DerivedChemicalForcePlan, DerivedModelSupply,
    GeometryReusePlan, SerializedPreparationIntegrity, SerializedPreparationGeometry,
    NativeSubworkDefinition, NativeSubworkCompletion, NativeSubworkBegin, NativeSubworkContact, DurableUnitReturn,
    ReusedGeometryChemicalForcePlan, SerializedDurableChemicalForcePlan,
    SerializedCustodyNVEControlPlan, RelaxedModelSupply, ChemicalForceCustodySupply,
), key=lambda row: (row.SCHEMA, row.VERSION)))


def input_port_id(schema):
    return "original." + schema.removeprefix("empirical-lawhood/").replace("/", ".")


def development_root(config, *, study_id):
    scope = p.scope(config.source)
    view = "view." + config.node_id + ".complete-numerical-controls"
    claim = ClaimSpec("claim." + config.node_id, scope.world_id, "population.exposed-original-structures", QUESTION,
        "Complete original 24 chemical/96 future or 96 NVE numerical slots; actual supplied subset and every adverse/unknown/unentered slot survive.",
        p.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Numerical control custody needs separate independent physical assessment and creates no biological units or qualification.",
        ("exposed-numerical-controls", "zero-fresh-biology"), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope.system_id, config.source),
        scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (p.UNIT,), (view,), (claim,), config.operands)


def scientific_root_validator(config, context):
    from .recursive_translation import input_links
    if (context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != config.node_id or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (p.UNIT,) or context.selected_unit_ids != (p.UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or tuple((row.node_id, row.record) for row in context.config_inputs) != ((config.node_id, config),)
            or context.links != input_links(config) or context.requirements or context.connections):
        raise ValueError("sampling changes its original source/plan/root/unit/stage/input/denominator contract")


@dataclass(frozen=True, slots=True)
class SamplingWorkMeaning(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/work-meaning"
    operation: str
    scientific_plan_json: str
    source_science_json: str


def work_meaning(config):
    plan = config.plan
    # Editable output/source paths and fresh labels cannot create new science.
    ignored = {"plan_id", "workdir", "interpreter_path", "hardware_inspector_path", "source"}
    values = {row.name: getattr(plan, row.name) for row in fields(plan) if row.name not in ignored}
    source = {row.name: getattr(config.source, row.name) for row in fields(config.source)
        if row.name not in {"selection_id", "native_workdir"}}
    return SamplingWorkMeaning(config.operation, canonical_json_bytes(values).decode(), canonical_json_bytes(source).decode())


def native_effect_slot_ids(config):
    return ("native.rubisco-sampling." + sha256(work_meaning(config).canonical_bytes()).hexdigest(),)


def output_codecs():
    return {record.SCHEMA: record for record in (SamplingOperationConfig, ChemicalForceCensus, NVEControlCensus, SamplingUnitStreamChunk)}


def operation_declarations():
    from functools import partial
    from empirical_lawhood.runtime.recursive_provider import (
        RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveInquiryHooks, RecursiveExecutionProperties)
    from .operation_runner import SamplingOperationWorker, prepare_native_work
    from .recursive_translation import scientific_work
    ports = tuple(RecursivePortContract(input_port_id(schema), schema, MEDIA, None, 0, None)
        for schema in sorted({row.SCHEMA for row in INPUT_RECORD_TYPES}))
    return tuple(RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + operation, capability_version="1.0.0",
        implementation_id="prepared-isolated-original-current-" + operation + "-full-custody-v1",
        kind=CapabilityKind.SIMULATOR, config_record_type=SamplingOperationConfig, stage=ScientificStage.ACQUIRE,
        input_ports=ports, input_record_types=INPUT_RECORD_TYPES,
        outputs=(OutputTemplate("census", census.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),
            OutputTemplate("units", SamplingUnitStreamChunk.SCHEMA, ArtifactProfile.JSONL_CHUNKS, STREAM_MEDIA, ".jsonl")),
        permissions=tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET, conformance_check_ids=("actual-full-specialist-before-contact", "complete-original-unit-denominator",
            "exact-original-portable-custody", "unknown-contact-no-replay"),
        runner_factory=partial(SamplingOperationWorker, operation), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in config.operands})),
            scientific_unit_ids=lambda config: (p.UNIT,), native_effect_slot_ids=native_effect_slot_ids,
            scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_work_projector=scientific_work),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work), storage_codecs=SAMPLING_STORAGE_CODECS)
        for operation, census in zip(OPERATIONS, (ChemicalForceCensus, NVEControlCensus), strict=True))


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())
