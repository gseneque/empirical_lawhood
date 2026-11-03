# SPDX-License-Identifier: MPL-2.0
"""Cold additive registration of source-bound physical preparation controls."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import AssemblyCoordinates, StructuralInventory
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import contracts as c
from .durable_contracts import DurablePreparationCensus, DurablePreparationPlan
from .durable_stream import DurableUnitStreamChunk, MEDIA as STREAM_MEDIA, DURABLE_STORAGE_CODECS

NAMESPACE = "rubisco-durable-preparation"
NODE = NAMESPACE + ".prepare"
QUESTION = "Does source-bound controlled molecular preparation return independently assessable complete physical models while preserving adverse and unentered work?"
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
OPERATIONS = ("prepare",)
INPUTS = tuple(sorted((("coordinates", AssemblyCoordinates), ("inventory", StructuralInventory),
    ("nomination", NominationDossier), ("plan", DurablePreparationPlan),
    ("producing-provenance", NumericalProducingProvenance), ("source", c.PreparationSelection))))
OUTPUTS = (("census", DurablePreparationCensus), ("units", DurableUnitStreamChunk))


@dataclass(frozen=True, slots=True)
class DurablePreparationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-operation-config"
    config_id: str
    plan: DurablePreparationPlan
    source: c.PreparationSelection
    producing_provenance: ObjectIdentity
    source_root: str
    invocation_path: str
    environment: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.config_id != "config." + NODE:
            raise ValueError("durable preparation changes its registered operation identity")
        self.plan.__post_init__()
        self.source.__post_init__()
        if (self.plan.source != c.identity(self.source) or self.plan.nomination != self.source.nomination
                or self.plan.inventory != self.source.structural_inventory
                or self.plan.coordinates != self.source.structural_coordinates
                or self.plan.workdir != self.source.native_workdir
                or self.plan.engine_inventory_sha256 != self.source.engine_inventory_sha256
                or self.producing_provenance.object_schema != NumericalProducingProvenance.SCHEMA):
            raise ValueError("durable preparation substitutes actual selected scientific operands")
        root, invocation = PurePosixPath(self.source_root), PurePosixPath(self.invocation_path)
        if (not root.is_absolute() or not invocation.is_absolute() or ".." in root.parts
                or ".." in invocation.parts or str(root) != self.source_root
                or str(invocation) != self.invocation_path or invocation.is_relative_to(self.plan.workdir)):
            raise ValueError("durable preparation requires exact selected source and fresh invocation outside workdir")
        if self.environment != tuple(sorted(set(self.environment))) or len(dict(self.environment)) != len(self.environment):
            raise ValueError("durable preparation changes complete selected process environment")
        allowed = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE",
            "OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "OPENBLAS_CORETYPE", "NPY_DISABLE_CPU_FEATURES"}
        environment = dict(self.environment)
        if (set(environment) - allowed or environment.get("PYTHONDONTWRITEBYTECODE") != "1"
                or environment.get("PYTHONPATH") != str(root / "src")
                or any(environment.get(name) != "1" for name in
                    ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                     "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"))):
            raise ValueError("durable preparation requires explicit single-thread environment without inherited secrets")

    @property
    def operands(self):
        return tuple(sorted((self.plan.source, self.plan.nomination, self.plan.inventory,
            self.plan.coordinates, self.plan.identity, self.producing_provenance), key=lambda row: row.object_id))


def media_for(name):
    return STREAM_MEDIA if name == "units" else MEDIA


def development_root(config, *, study_id):
    scope = c.scope(config.source)
    view = "view." + NAMESPACE + ".complete-12-24-census"
    claim = ClaimSpec("claim." + NAMESPACE, scope.world_id, "population.exposed-original-structures", QUESTION,
        "Complete twelve geometry and twenty-four parameter-model slots; attempted control subset is explicit and all other slots remain unentered.",
        c.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Exact model preparation custody is separate from independent physical assessment, dynamics, reactive chemistry and enzyme function.",
        ("preparation-only", "zero-fresh-biology"), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope.system_id, config.source),
        scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (c.UNIT,), (view,), (claim,), config.operands)


def scientific_root_validator(config, context):
    from .durable_recursive_translation import validate_graph
    if (context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != NODE or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (c.UNIT,) or context.selected_unit_ids != (c.UNIT,)
            or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("durable preparation changes source-bound scientific root/stage/census")
    validate_graph(context, config)


def output_codecs():
    return {record.SCHEMA: record for record in (DurablePreparationConfig,
        *(record for _, record in INPUTS), *(record for _, record in OUTPUTS))}


def operation_declarations():
    from functools import partial
    from empirical_lawhood.runtime.recursive_provider import (
        RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveInquiryHooks, RecursiveExecutionProperties)
    from .durable_recursive_translation import native_effect_slot_ids, scientific_work
    from .durable_runner import DurablePreparationWorker, prepare_native_work
    return (RecursiveOperationDeclaration(
        capability_key=NODE, capability_version="1.0.0",
        implementation_id="source-bound-isolated-original-preparation-full-custody-v1",
        kind=CapabilityKind.SIMULATOR, config_record_type=DurablePreparationConfig, stage=ScientificStage.ACQUIRE,
        input_ports=tuple(RecursivePortContract(name,record.SCHEMA,MEDIA,None) for name,record in INPUTS),
        outputs=tuple(OutputTemplate(name,record.SCHEMA,
            ArtifactProfile.JSONL_CHUNKS if name=="units" else ArtifactProfile.CANONICAL_JSON,
            media_for(name),".jsonl" if name=="units" else ".json") for name,record in OUTPUTS),
        permissions=tuple(sorted((CapabilityPermission.READ_DEVELOPMENT,CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET, conformance_check_ids=("actual-parent-source-bound-isolated-child","complete-12-24-denominator",
            "exact-completed-receipt-only-portable-returns","unknown-contact-no-replay"),
        runner_factory=partial(DurablePreparationWorker,"prepare"),record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda config:tuple(sorted({row.object_fingerprint for row in config.operands})),
            scientific_unit_ids=lambda config:(c.UNIT,),native_effect_slot_ids=native_effect_slot_ids,
            scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_work_projector=scientific_work),
        execution_properties=RecursiveExecutionProperties(native_effect=True,complete_unit_census=True,
            native_work_preparer=prepare_native_work),storage_codecs=DURABLE_STORAGE_CODECS),)


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())
