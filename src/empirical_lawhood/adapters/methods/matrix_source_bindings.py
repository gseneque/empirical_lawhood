# SPDX-License-Identifier: MPL-2.0
"""Real Matrix record qualifiers over existing runtime owners, without acquisition."""

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.kernel.authority import ResourceBudget
from functools import partial
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationResult
from empirical_lawhood.planning.source_pipelines import SourcePipelineQualificationReceipt
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import ExecutionTask, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from .matrix_source_evidence import MatrixSourcePipelineConfig, MatrixSourceQualificationConfig


PIPELINE_KEY = "matrix-source.pipeline-qualify"
QUALIFICATION_KEY = "matrix-source.scientific-qualify"


class MatrixSourceQualifierWorker:
    def __init__(self, phase):
        self.phase = phase
        self.manifest = source_declarations()[phase].manifest()

    def execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read
        kind = (MatrixSourcePipelineConfig, MatrixSourceQualificationConfig)[self.phase]
        if type(context) is not TaskContext:
            raise PermissionError("Matrix source qualifier requires the actual issued task context")
        try:
            context.__post_init__()
            prepared = context.prepared_invocation
            if (type(prepared) is not PreparedInvocationContract or prepared.manifest != self.manifest
                    or type(prepared.execution_task_record) is not ExecutionTask
                    or prepared.execution_task_record.stage is not ScientificStage.QUALIFY
                    or any(value.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                        or value.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                        for value in prepared.execution_task_record.outputs)
                    or prepared.native_effect or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or not self.manifest.resource_ceiling.contains(context.resource_budget)
                    or (context.config.config_schema, context.config.config_schema_sha256)
                        != (self.manifest.config_schema, self.manifest.config_schema_sha256)
                    or len(prepared.inputs) != 1):
                raise PermissionError("Matrix source qualifier loses its actual complete prepared input/permission/access contract")
            if len(context.input_ports) != 1 or context.dependency_receipts:
                raise ValueError("Matrix source qualifier requires its one complete original configuration")
            port, = context.input_ports
            contract, = prepared.inputs
            if (port.payload_schema != kind.SCHEMA or port.artifact_id != context.config.artifact_id
                    or port.kind is not WorkerInputKind.EXTERNAL or contract.artifact_id != port.artifact_id
                    or port.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
                raise ValueError("Matrix source qualifier substitutes its configured scientific inputs")
            config = _read(port, contract, kind)
            if (config.config_id, config.fingerprint()) != (context.config.config_id, context.config.content_sha256):
                raise ValueError("Matrix source qualifier changes exact original canonical inputs")
            product = config.assess()
            output, = context.output_ports
            if output.output_id != context.task_id + ".product" or output.payload_schema != product.SCHEMA:
                raise ValueError("Matrix source qualifier substitutes its original result output")
            return RunnerResult((TaskOutputPayload(output.output_id, product.canonical_bytes()),),
                (ReceiptCheck("matrix-original-source-owner-replay", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def _original_source_declarations():
    return tuple(RecursiveOperationDeclaration(key, "1.0.0", key + ".original-source-owner-v1",
        CapabilityKind.NUMERICAL_QUALIFIER, config, ScientificStage.QUALIFY, (),
        (OutputTemplate("product", result.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE,
        ResourceBudget(1, None, 0, None, None, None), ("matrix-original-source-owner-replay",),
        partial(MatrixSourceQualifierWorker, phase), {config.SCHEMA: config, result.SCHEMA: result},
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
        for phase, (key, config, result) in enumerate(((PIPELINE_KEY, MatrixSourcePipelineConfig, SourcePipelineQualificationReceipt),
            (QUALIFICATION_KEY, MatrixSourceQualificationConfig, ScientificSourceQualificationResult))))


def source_declarations():
    """Declare source pipeline replay and current numerical instrument gates."""
    from .matrix_finite_dt_source_bindings import closeout_declaration, gate_declarations
    from .matrix_prepared_source_bindings import gate_declarations as prepared_gate_declarations
    return (*_original_source_declarations(), *gate_declarations(), *prepared_gate_declarations(), closeout_declaration())
