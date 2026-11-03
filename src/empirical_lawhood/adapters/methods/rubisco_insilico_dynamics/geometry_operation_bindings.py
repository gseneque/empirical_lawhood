# SPDX-License-Identifier: MPL-2.0
"""Original assessed geometry as explicit inputs to fresh parameter models."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import AssemblyCoordinates, StructuralInventory
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import contracts as c
from .durable_operation_bindings import BUDGET, MEDIA
from .durable_contracts import DurablePreparationCensus
from .durable_stream import DURABLE_STORAGE_CODECS, DurableUnitStreamChunk, MEDIA as STREAM_MEDIA
from .geometry_reuse import GeometryReusePlan, GeometryReuseSupply, validate_reuse_assessment
from .preamber_geometry_integrity import PreAmberGeometryIntegrity

NODE = "rubisco-durable-preparation.reuse-geometry"
QUESTION = "Do exactly retained independently assessed geometry supplies produce independently assessable fresh parameter models while preserving the original native history?"


@dataclass(frozen=True, slots=True)
class GeometryReuseConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/geometry-reuse-operation-config"
    config_id: str
    plan: GeometryReusePlan
    source: c.PreparationSelection
    supplies: tuple[GeometryReuseSupply, ...]
    assessments: tuple[PreAmberGeometryIntegrity, ...]
    source_root: str
    invocation_path: str
    environment: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.config_id != "config." + NODE or type(self.plan) is not GeometryReusePlan:
            raise ValueError("geometry reuse changes its exact installed config/plan type")
        self.plan.__post_init__()
        self.source.__post_init__()
        if (self.plan.source != c.identity(self.source) or self.plan.workdir != self.source.native_workdir
                or (self.plan.nomination, self.plan.inventory, self.plan.coordinates) != (
                    self.source.nomination, self.source.structural_inventory, self.source.structural_coordinates)
                or self.plan.engine_inventory_sha256 != self.source.engine_inventory_sha256
                or tuple(row.identity for row in self.supplies) != self.plan.geometry_supplies
                or len(self.assessments) != len(self.supplies)):
            raise ValueError("geometry reuse substitutes original supplied source/assessments/census")
        for supply, assessment in zip(self.supplies, self.assessments, strict=True):
            if type(supply) is not GeometryReuseSupply or type(assessment) is not PreAmberGeometryIntegrity:
                raise ValueError("geometry reuse changes its exact original supplier/assessor types")
            validate_reuse_assessment(self.plan, self.source, supply, assessment)
        root, invocation = PurePosixPath(self.source_root), PurePosixPath(self.invocation_path)
        if (not root.is_absolute() or not invocation.is_absolute() or ".." in root.parts or ".." in invocation.parts
                or str(root) != self.source_root or str(invocation) != self.invocation_path
                or invocation.is_relative_to(self.plan.workdir)):
            raise ValueError("geometry reuse needs exact source and explicitly selected fresh invocation outside native work")
        if self.environment != tuple(sorted(set(self.environment))) or len(dict(self.environment)) != len(self.environment):
            raise ValueError("geometry reuse needs its complete selected environment")
        environment = dict(self.environment)
        if (environment.get("PYTHONDONTWRITEBYTECODE") != "1" or environment.get("PYTHONPATH") != str(root / "src")
                or any(environment.get(name) != "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS",
                    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"))):
            raise ValueError("geometry reuse changes its exact bytecode/source/single-thread selection")

    @property
    def operands(self):
        return tuple(sorted({self.plan.identity, self.plan.source, self.plan.nomination, self.plan.inventory,
            self.plan.coordinates, *(row.identity for row in self.supplies), *(row.independent_integrity for row in self.supplies)},
            key=lambda row: row.object_id))


INPUT_RECORD_TYPES = tuple(sorted((GeometryReusePlan, c.PreparationSelection, NominationDossier,
    StructuralInventory, AssemblyCoordinates, GeometryReuseSupply, PreAmberGeometryIntegrity), key=lambda row: (row.SCHEMA, row.VERSION)))


def port_id(schema):
    return "original." + schema.removeprefix("empirical-lawhood/").replace("/", ".")


def development_root(config, *, study_id):
    scope = c.scope(config.source)
    view = "view." + NODE + ".complete-12-24-census"
    claim = ClaimSpec("claim." + NODE, scope.world_id, "population.exposed-original-structures", QUESTION,
        "Original full twelve geometry/twenty-four model denominator; only explicitly selected fresh models execute, original geometry is never replayed.",
        c.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Original geometry custody and its independent assessment remain immutable; fresh parameter models create zero biological units.",
        ("assessed-geometry-reuse", "zero-fresh-biology"), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope.system_id, config.source),
        scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (c.UNIT,), (view,), (claim,), config.operands)


def scientific_root_validator(config, context):
    from .geometry_recursive_translation import input_links
    if (context.root != development_root(config, study_id=context.root.study_id) or context.node_id != NODE
            or context.stage is not ScientificStage.ACQUIRE or context.unit_ids != (c.UNIT,)
            or context.selected_unit_ids != (c.UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or tuple((row.node_id, row.record) for row in context.config_inputs) != ((NODE, config),)
            or context.links != input_links(config) or context.requirements or context.connections):
        raise ValueError("geometry reuse changes its exact scientific source/root/input/denominator contract")


def operation_declarations():
    from functools import partial
    from empirical_lawhood.runtime.recursive_provider import (
        RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveInquiryHooks, RecursiveExecutionProperties)
    from .geometry_runner import GeometryReuseWorker, prepare_native_work
    from .geometry_recursive_translation import native_effect_slot_ids, scientific_work
    codecs = {record.SCHEMA: record for record in (GeometryReuseConfig, DurablePreparationCensus, DurableUnitStreamChunk)}
    return (RecursiveOperationDeclaration(NODE, "1.0.0", "current-assessed-original-geometry-fresh-models-v1",
        CapabilityKind.SIMULATOR, GeometryReuseConfig, ScientificStage.ACQUIRE,
        tuple(RecursivePortContract(port_id(schema), schema, MEDIA, None, 0, None) for schema in sorted({row.SCHEMA for row in INPUT_RECORD_TYPES})),
        (OutputTemplate("census", DurablePreparationCensus.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),
            OutputTemplate("units", DurableUnitStreamChunk.SCHEMA, ArtifactProfile.JSONL_CHUNKS, STREAM_MEDIA, ".jsonl")),
        tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))), EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, BUDGET,
        ("actual-geometry-specialist-before-contact", "complete-12-24-census", "original-assessment-and-complete-archive", "unknown-no-replay"),
        partial(GeometryReuseWorker, "reuse-geometry"), codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in config.operands})),
            scientific_unit_ids=lambda config: (c.UNIT,), native_effect_slot_ids=native_effect_slot_ids, scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_work_projector=scientific_work),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True, native_work_preparer=prepare_native_work),
        storage_codecs=DURABLE_STORAGE_CODECS, input_record_types=INPUT_RECORD_TYPES),)
