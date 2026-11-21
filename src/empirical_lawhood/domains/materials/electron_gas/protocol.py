"""Pure uniform-electron-gas scientific protocol and capability references."""

from __future__ import annotations
from hashlib import sha256
from typing import TypeVar
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.execution.plans import BarrierKind, OutputTemplate, ProtocolStepTemplate, ProtocolTemplate, ScientificStage
from empirical_lawhood.domains.materials.electron_gas.contracts import ADMISSION_CAPABILITY_KEY, ADJUDICATION_SCHEMA, CAPABILITY_VERSION, CONFIG_SCHEMA, EVALUATOR_CAPABILITY_KEY, METHOD_CAPABILITY_KEY, SOURCE_CAPABILITY_KEY, MethodConformanceResult, SourceStopResult, UniformElectronGasTransverseScreenConfig, TruthInputBatch, TruthLawBatch, TruthOracleBatch, TruthScreenBatch
from empirical_lawhood.domains.materials.electron_gas.system import task_budget

CONFIG_ARTIFACT_ID = "config-artifact.uniform-electron-gas-transverse-screen"

MEDIUM_ARTIFACT_ID = "prepared-medium.uniform-electron-gas-transverse-screen"

CONFIG_SOURCE_ID = "source.uniform-electron-gas-transverse-screen-config"

ADJUDICATION_SCOPE_ID = "uniform-electron-gas-transverse-screen-conformance"

TRUTH_INPUT_STEP = "truth-input-source"

TRUTH_ORACLE_STEP = "truth-oracle-custody"

METHOD_STEP = "method-identify"

ADMISSION_STEP = "admission-intersect"

EVALUATOR_STEP = "evaluator-reveal"

def config_ref(config: UniformElectronGasTransverseScreenConfig) -> CapabilityConfigRef:
    return CapabilityConfigRef(
        config_id="config.uniform-electron-gas-transverse-screen",
        config_schema=CONFIG_SCHEMA,
        config_schema_sha256=sha256(CONFIG_SCHEMA.encode()).hexdigest(),
        content_sha256=config.payload_sha256,
        artifact_id=CONFIG_ARTIFACT_ID,
    )

def uniform_electron_gas_transverse_screen_protocol(*, registry: CapabilityRegistry, config: UniformElectronGasTransverseScreenConfig) -> ProtocolTemplate:
    reference = config_ref(config)

    def step(
        *,
        step_id: str,
        stage: ScientificStage,
        capability_key: str,
        dependencies: tuple[str, ...],
        outputs: tuple[tuple[str, str], ...],
        outcome_access: OutcomeAccess,
        visibility: VisibilityCeiling,
        barrier: BarrierKind,
        obligations: tuple[str, ...],
    ) -> ProtocolStepTemplate:
        manifest = registry.resolve(capability_key, CAPABILITY_VERSION)
        return ProtocolStepTemplate(
            step_id=step_id,
            stage=stage,
            capability_key=capability_key,
            capability_version=CAPABILITY_VERSION,
            config=reference,
            dependency_step_ids=dependencies,
            outputs=tuple(
                sorted(
                    (
                        OutputTemplate(
                            output_id=output_id,
                            payload_schema=payload_schema,
                            profile=ArtifactProfile.CANONICAL_JSON,
                            media_type="application/json",
                            filename_suffix=".json",
                        )
                        for output_id, payload_schema in outputs
                    ),
                    key=lambda value: value.output_id,
                )
            ),
            required_permissions=manifest.permissions,
            requested_outcome_access=outcome_access,
            visibility_ceiling=visibility,
            resource_budget=task_budget(config),
            resource_lock_ids=(f"uniform-electron-gas-transverse-screen-{step_id}",),
            barrier=barrier,
            maximum_attempts=2,
            obligation_ids=tuple(sorted(obligations)),
        )

    steps = (
        step(
            step_id=ADMISSION_STEP,
            stage=ScientificStage.ADMISSION,
            capability_key=ADMISSION_CAPABILITY_KEY,
            dependencies=(METHOD_STEP, TRUTH_INPUT_STEP),
            outputs=(("truth-screens", TruthScreenBatch.SCHEMA),),
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
            barrier=BarrierKind.FREEZE,
            obligations=("transverse-screen-admission-nine-gate-contract",),
        ),
        step(
            step_id=EVALUATOR_STEP,
            stage=ScientificStage.EVALUATE,
            capability_key=EVALUATOR_CAPABILITY_KEY,
            dependencies=(ADMISSION_STEP, TRUTH_ORACLE_STEP),
            outputs=(
                ("method-conformance", MethodConformanceResult.SCHEMA),
                ("scientific-adjudication", ADJUDICATION_SCHEMA),
                ("source-stop", SourceStopResult.SCHEMA),
            ),
            outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
            visibility=VisibilityCeiling.PRIVILEGED_TRUTH,
            barrier=BarrierKind.REVEAL,
            obligations=(
                *(f"formal-obligation.{gap_id}" for gap_id in config.reference_conformance_gaps),
                "transverse-screen-evaluator-exact-classification-contract",
                "transverse-screen-source-stop-nonattempt-contract",
            ),
        ),
        step(
            step_id=METHOD_STEP,
            stage=ScientificStage.DEVELOP,
            capability_key=METHOD_CAPABILITY_KEY,
            dependencies=(TRUTH_INPUT_STEP,),
            outputs=(("truth-laws", TruthLawBatch.SCHEMA),),
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
            barrier=BarrierKind.FREEZE,
            obligations=("transverse-screen-method-measurement-through-law-freeze-contract",),
        ),
        step(
            step_id=TRUTH_INPUT_STEP,
            stage=ScientificStage.ACQUIRE,
            capability_key=SOURCE_CAPABILITY_KEY,
            dependencies=(),
            outputs=(("truth-inputs", TruthInputBatch.SCHEMA),),
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
            barrier=BarrierKind.NONE,
            obligations=("transverse-screen-truth-input-roster-contract",),
        ),
        step(
            step_id=TRUTH_ORACLE_STEP,
            stage=ScientificStage.ACQUIRE,
            capability_key=SOURCE_CAPABILITY_KEY,
            dependencies=(),
            outputs=(("truth-oracles", TruthOracleBatch.SCHEMA),),
            outcome_access=OutcomeAccess.PRIVILEGED_TRUTH,
            visibility=VisibilityCeiling.PRIVILEGED_TRUTH,
            barrier=BarrierKind.NONE,
            obligations=("transverse-screen-privileged-oracle-custody-contract",),
        ),
    )
    return ProtocolTemplate(
        template_id="protocol.uniform-electron-gas-transverse-screen-conformance",
        template_version=CAPABILITY_VERSION,
        steps=tuple(sorted(steps, key=lambda value: value.step_id)),
        requires_model_set=True,
        requests_controller=False,
        nonactuating=True,
    )

_RecordT = TypeVar("_RecordT", bound=CanonicalRecord)
