"""Receipt-first truth-known conformance protocol, runners and runtime provider for transverse receiver screen."""

from __future__ import annotations
from empirical_lawhood.domains.materials.electron_gas.protocol import ADJUDICATION_SCOPE_ID as _ueg_ADJUDICATION_SCOPE_ID, ADMISSION_STEP as _ueg_ADMISSION_STEP, CONFIG_ARTIFACT_ID as _ueg_CONFIG_ARTIFACT_ID, EVALUATOR_STEP as _ueg_EVALUATOR_STEP, MEDIUM_ARTIFACT_ID as _ueg_MEDIUM_ARTIFACT_ID, METHOD_STEP as _ueg_METHOD_STEP, TRUTH_INPUT_STEP as _ueg_TRUTH_INPUT_STEP, TRUTH_ORACLE_STEP as _ueg_TRUTH_ORACLE_STEP, _RecordT

from dataclasses import fields
from typing import Any, cast

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.design.study_issue import StudyOperationAuthority
from empirical_lawhood.execution.adjudication import AdjudicationEvaluability, ScientificAdjudicationOutputContract, ScientificAdjudicationRecord, encode_scientific_adjudication
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityManifest, CapabilityRegistry
from empirical_lawhood.execution.execution import RunnerResult, TaskContext, TaskOutputPayload, TaskRunner
from empirical_lawhood.execution.plans import ProtocolExecutionPlan
from empirical_lawhood.execution.providers import CapabilityOutputSemanticContract, CampaignRuntimeProvider, ExternalInputPayload

from empirical_lawhood.domains.materials.electron_gas.contracts import ADJUDICATION_SCHEMA, CAPABILITY_VERSION, CONFIG_SCHEMA, CONFIG_VERSION, EVALUATOR_CAPABILITY_KEY, MethodConformanceResult, SourceStopResult, UniformElectronGasTransverseScreenConfig, TruthInputBatch, TruthLawBatch, TruthOracleBatch, TruthScreenBatch
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.configuration import decode_config_bytes
from empirical_lawhood.domains.materials.electron_gas.reference_world import adjudicate_truth_batch, build_truth_batches, evaluate_truth_batches, identify_truth_batch











def _one(records: tuple[CanonicalRecord, ...], record_type: type[_RecordT]) -> _RecordT:
    values = {value.fingerprint(): value for value in records if isinstance(value, record_type)}
    if len(values) != 1:
        raise ValueError(f"uniform electron gas task requires exactly one {record_type.__name__}")
    return next(iter(values.values()))


_INPUT_TYPES: dict[str, type[CanonicalRecord]] = {
    TruthInputBatch.SCHEMA: TruthInputBatch,
    TruthLawBatch.SCHEMA: TruthLawBatch,
    TruthOracleBatch.SCHEMA: TruthOracleBatch,
    TruthScreenBatch.SCHEMA: TruthScreenBatch,
}


class UniformElectronGasTransverseScreenRunner:
    """Closed runner whose truth-blind tasks never decode privileged oracles."""

    def __init__(self, manifest: CapabilityManifest, config: UniformElectronGasTransverseScreenConfig, payload: bytes) -> None:
        if decode_config_bytes(payload) != config:
            raise ValueError("uniform electron gas runner config differs from frozen bytes")
        self.manifest = manifest
        self.config = config
        self.payload = payload
        self.execution_count = 0

    def _read(self, context: TaskContext) -> tuple[CanonicalRecord, ...]:
        records: list[CanonicalRecord] = []
        observed_config = False
        for port in context.input_ports:
            payload = port.read(port.size_bytes + 1)
            if len(payload) != port.size_bytes:
                raise ValueError("uniform electron gas task input size differs")
            if port.payload_schema == CONFIG_SCHEMA:
                if payload != self.payload or decode_config_bytes(payload) != self.config:
                    raise ValueError("uniform electron gas task config materialization differs")
                observed_config = True
                continue
            try:
                record_type = _INPUT_TYPES[port.payload_schema]
            except KeyError as error:
                raise ValueError("uniform electron gas task received an unknown input schema") from error
            records.append(
                decode_canonical_bytes(payload, record_type, maximum_bytes=port.size_bytes)
            )
        if not observed_config or context.config.content_sha256 != self.config.payload_sha256:
            raise ValueError("uniform electron gas task lacks its exact frozen config")
        return tuple(records)

    @staticmethod
    def _source_stop(config: UniformElectronGasTransverseScreenConfig, conformance: MethodConformanceResult) -> SourceStopResult:
        conformance_passed = conformance.passed
        return SourceStopResult(
            result_id="uniform-electron-gas-transverse-screen-source-stop",
            config_sha256=config.payload_sha256,
            source_dispositions=(
                ("paper_rpa", "CLOSURE_ONLY_SOURCE"),
                ("target_gauge_closed_roster", "EMPTY"),
                ("vertex_reference", "CLOSURE_ONLY_SOURCE"),
            ),
            task_dispositions=(
                (
                    "conformance-truth-known",
                    ("TRANSVERSE_SCREEN_METHOD_CONFORMANCE_PASS" if conformance_passed else "TRANSVERSE_SCREEN_METHOD_CONFORMANCE_FAIL"),
                ),
                (
                    "development-law-commitment",
                    (
                        "NOT_ATTEMPTED_PREREQUISITE_TARGET_SOURCE"
                        if conformance_passed
                        else "NOT_ATTEMPTED_PREREQUISITE_TRUTH_KNOWN_CONFORMANCE"
                    ),
                ),
                (
                    "evaluation-target-reveal",
                    (
                        "NOT_ATTEMPTED_PREREQUISITE_TARGET_SOURCE"
                        if conformance_passed
                        else "NOT_ATTEMPTED_PREREQUISITE_TRUTH_KNOWN_CONFORMANCE"
                    ),
                ),
                (
                    "qualification-target-source",
                    (
                        "NOT_ATTEMPTED_PREREQUISITE_TARGET_SOURCE"
                        if conformance_passed
                        else "NOT_ATTEMPTED_PREREQUISITE_TRUTH_KNOWN_CONFORMANCE"
                    ),
                ),
                (
                    "supplementary-closure-diagnostic",
                    (
                        "NOT_ATTEMPTED_PREREQUISITE_EXACT_CLOSURE_BINDING"
                        if conformance_passed
                        else "NOT_ATTEMPTED_PREREQUISITE_TRUTH_KNOWN_CONFORMANCE"
                    ),
                ),
                ("terminal-closeout", "READY_FOR_IMMUTABLE_CLOSEOUT"),
            ),
            target_contact_count=0,
            status=(
                "TRANSVERSE_SCREEN_SOURCE_NOT_READY_TRANSVERSE_CURRENT_OPERAND_REQUIRED"
                if conformance_passed
                else "TRANSVERSE_SCREEN_METHOD_CONFORMANCE_FAILED"
            ),
        )

    @staticmethod
    def _scientific_adjudication(
        context: TaskContext, conformance: MethodConformanceResult
    ) -> ScientificAdjudicationRecord:
        adjudication_context = context.scientific_adjudication_context
        if adjudication_context is None:
            raise ValueError("uniform electron gas evaluator lacks scientific adjudication context")
        output_ids = tuple(
            sorted(
                port.logical_artifact_id
                for port in context.output_ports
                if port.logical_artifact_id is not None
            )
        )
        if len(output_ids) != len(context.output_ports):
            raise ValueError("uniform electron gas evaluator output lacks logical identity")
        return ScientificAdjudicationRecord(
            adjudication_id=f"adjudication.{context.run_id}.{context.task_id}",
            run_id=context.run_id,
            adjudication_task_id=context.task_id,
            execution_plan=adjudication_context.execution_plan,
            input_materialization_ids=tuple(sorted(context.input_materialization_ids)),
            output_logical_artifact_ids=output_ids,
            required_receipt_ids=context.dependency_receipt_ids,
            evidence_world_id=adjudication_context.evidence_world_id,
            evidence_world_kind=adjudication_context.evidence_world_kind,
            relation=adjudication_context.relation,
            independent_unit_id=adjudication_context.independent_unit_id,
            information_cutoffs=adjudication_context.information_cutoffs,
            visibility_ceiling=adjudication_context.visibility_ceiling,
            outcome_access=adjudication_context.outcome_access,
            evaluability=AdjudicationEvaluability.EVALUABLE,
            scientific_status=(
                ScientificStatus.SUPPORTED if conformance.passed else ScientificStatus.NOT_SUPPORTED
            ),
            admission_status=AdmissionStatus.NOT_EVALUATED,
            reason_codes=(
                (
                    "CONFORMANCE_TRUTH_KNOWN_METHOD_PASSED",
                    "TARGET_SOURCE_TRANSVERSE_CURRENT_OPERAND_REQUIRED",
                    "TRUTH_KNOWN_NONPROMOTABLE",
                )
                if conformance.passed
                else (
                    "CONFORMANCE_TRUTH_KNOWN_METHOD_FAILED",
                    "TARGET_EXECUTION_BLOCKED_BY_TRUTH_KNOWN_CONFORMANCE",
                    "TRUTH_KNOWN_NONPROMOTABLE",
                )
            ),
            fixture_scope_id=adjudication_context.fixture_scope_id,
            plumbing_only=adjudication_context.plumbing_only,
        )

    def execute(self, context: TaskContext) -> RunnerResult:
        self.execution_count += 1
        records = self._read(context)
        outputs: dict[str, CanonicalRecord | bytes]
        if context.task_id == _ueg_TRUTH_INPUT_STEP:
            inputs, _oracles = build_truth_batches(self.config)
            outputs = {"truth-inputs": inputs}
        elif context.task_id == _ueg_TRUTH_ORACLE_STEP:
            _inputs, oracles = build_truth_batches(self.config)
            outputs = {"truth-oracles": oracles}
        elif context.task_id == _ueg_METHOD_STEP:
            outputs = {
                "truth-laws": identify_truth_batch(_one(records, TruthInputBatch), self.config)
            }
        elif context.task_id == _ueg_ADMISSION_STEP:
            outputs = {
                "truth-screens": adjudicate_truth_batch(
                    _one(records, TruthInputBatch),
                    _one(records, TruthLawBatch),
                    self.config,
                )
            }
        elif context.task_id == _ueg_EVALUATOR_STEP:
            conformance = evaluate_truth_batches(
                _one(records, TruthScreenBatch),
                _one(records, TruthOracleBatch),
                self.config,
            )
            outputs = {
                "method-conformance": conformance,
                "scientific-adjudication": encode_scientific_adjudication(
                    self._scientific_adjudication(context, conformance),
                    payload_schema=ADJUDICATION_SCHEMA,
                ),
                "source-stop": self._source_stop(self.config, conformance),
            }
        else:
            raise ValueError("unknown uniform electron gas task identity")

        return RunnerResult(
            outputs=tuple(
                TaskOutputPayload(
                    output_id=port.output_id,
                    payload=(
                        value
                        if isinstance(
                            value := outputs[port.output_id.removeprefix(f"{context.task_id}.")],
                            bytes,
                        )
                        else value.canonical_bytes()
                    ),
                )
                for port in context.output_ports
            ),
            checks=(
                ReceiptCheck("actual-computation-completed", True, ()),
                ReceiptCheck("exact-config-and-inputs-decoded", True, ()),
                ReceiptCheck("no-target-source-contact", True, ()),
                ReceiptCheck("privileged-oracle-edge-separated", True, ()),
            ),
        )


_OUTPUT_TYPES: dict[str, type[CanonicalRecord]] = {
    MethodConformanceResult.SCHEMA: MethodConformanceResult,
    SourceStopResult.SCHEMA: SourceStopResult,
    TruthInputBatch.SCHEMA: TruthInputBatch,
    TruthLawBatch.SCHEMA: TruthLawBatch,
    TruthOracleBatch.SCHEMA: TruthOracleBatch,
    TruthScreenBatch.SCHEMA: TruthScreenBatch,
}


class UniformElectronGasTransverseScreenRuntimeProvider(CampaignRuntimeProvider):
    """Bind the exact registry, frozen config and raw config materialization."""

    issued_source_schema_ids: tuple[str, ...] = (StudyOperationAuthority.SCHEMA,)

    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
        config: UniformElectronGasTransverseScreenConfig,
        config_payload: bytes,
    ) -> None:
        if any(
            manifest.implementation_sha256 != registry.capabilities[0].implementation_sha256
            for manifest in registry.capabilities
        ):
            raise ValueError("uniform electron gas registry mixes implementation identities")
        if decode_config_bytes(config_payload) != config:
            raise ValueError("uniform electron gas provider config differs from frozen bytes")
        self.registry = registry
        self.config = config
        self.config_payload = config_payload
        self.registry_sha256 = registry.fingerprint()
        self.capability_count = len(registry.capabilities)
        self._runners: tuple[UniformElectronGasTransverseScreenRunner, ...] = ()

    def runners(
        self,
        registry: CapabilityRegistry,
        source_records: tuple[CanonicalRecord, ...] = (),
    ) -> tuple[TaskRunner, ...]:
        del source_records
        if registry != self.registry:
            raise ValueError("uniform electron gas runner registry differs")
        self._runners = tuple(
            UniformElectronGasTransverseScreenRunner(manifest, self.config, self.config_payload)
            for manifest in registry.capabilities
        )
        return cast(tuple[TaskRunner, ...], self._runners)

    def external_inputs(
        self,
        plan: ProtocolExecutionPlan,
        source_records: tuple[CanonicalRecord, ...] = (),
    ) -> tuple[ExternalInputPayload, ...]:
        del source_records
        if plan.registry_sha256 != self.registry_sha256:
            raise ValueError("uniform electron gas execution plan registry differs")
        specs = {
            value.logical_artifact_id: value
            for task in plan.tasks
            for value in task.external_inputs
        }
        expected_ids = {_ueg_CONFIG_ARTIFACT_ID, _ueg_MEDIUM_ARTIFACT_ID}
        unknown = set(specs) - expected_ids
        if unknown:
            raise ValueError(f"uniform electron gas plan requests unknown external inputs: {sorted(unknown)}")
        if set(specs) != expected_ids:
            raise ValueError("uniform electron gas plan omits an exact config or medium materialization")

        def payload(logical_artifact_id: str) -> ExternalInputPayload:
            spec = specs[logical_artifact_id]
            parent = ArtifactLineageParent(
                identity=ObjectIdentity(
                    object_id=logical_artifact_id,
                    object_schema=CONFIG_SCHEMA,
                    object_version=CONFIG_VERSION,
                    object_fingerprint=self.config.payload_sha256,
                ),
                visibility_ceiling=(
                    spec.expected_visibility_ceiling or VisibilityCeiling.PROSPECTIVE
                ),
                outcome_access=(spec.expected_outcome_access or OutcomeAccess.OUTCOME_BLIND),
            )
            return ExternalInputPayload.from_bytes(
                logical_artifact_id=logical_artifact_id,
                payload_schema=CONFIG_SCHEMA,
                profile=ArtifactProfile.TEXT_PARAMETERS,
                media_type="application/json",
                payload=self.config_payload,
                visibility_ceiling=parent.visibility_ceiling,
                outcome_access=parent.outcome_access,
                parent_visibility_ceilings=(parent.visibility_ceiling,),
                lineage_parents=(parent,),
                logical_content_sha256=self.config.payload_sha256,
            )

        return (
            payload(_ueg_CONFIG_ARTIFACT_ID),
            payload(_ueg_MEDIUM_ARTIFACT_ID),
        )

    def output_semantic_contracts(
        self,
        registry: CapabilityRegistry,
        execution_plan: ProtocolExecutionPlan | None = None,
    ) -> tuple[CapabilityOutputSemanticContract, ...]:
        del execution_plan
        if registry != self.registry:
            raise ValueError("uniform electron gas semantic registry differs")
        contracts = []
        for manifest in registry.capabilities:
            for schema in manifest.output_schema_ids:
                record_type = (
                    ScientificAdjudicationRecord
                    if schema == ADJUDICATION_SCHEMA
                    else _OUTPUT_TYPES[schema]
                )
                contracts.append(
                    CapabilityOutputSemanticContract.from_manifest(
                        manifest,
                        payload_schema=schema,
                        profile=ArtifactProfile.CANONICAL_JSON,
                        top_level_keys=("schema", "value", "version"),
                        value_keys=tuple(
                            sorted(value.name for value in fields(cast(Any, record_type)))
                        ),
                    )
                )
        return tuple(sorted(contracts, key=lambda value: value.key))

    def scientific_adjudication_contract(
        self,
        registry: CapabilityRegistry,
        execution_plan: ProtocolExecutionPlan | None = None,
    ) -> ScientificAdjudicationOutputContract:
        del execution_plan
        if registry != self.registry:
            raise ValueError("uniform electron gas adjudication registry differs")
        return ScientificAdjudicationOutputContract(
            capability_key=EVALUATOR_CAPABILITY_KEY,
            capability_version=CAPABILITY_VERSION,
            output_id=f"{_ueg_EVALUATOR_STEP}.scientific-adjudication",
            payload_schema=ADJUDICATION_SCHEMA,
            maximum_bytes=128 * 1024,
            fixture_scope_id=_ueg_ADJUDICATION_SCOPE_ID,
            plumbing_only=True,
        )


__all__ = [
    "UniformElectronGasTransverseScreenRunner",
    "UniformElectronGasTransverseScreenRuntimeProvider",
]
