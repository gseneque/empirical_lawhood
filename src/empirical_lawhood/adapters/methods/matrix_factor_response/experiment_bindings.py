# SPDX-License-Identifier: MPL-2.0
"""One owning declaration per exposed E3 scientific operation."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

from . import experiment_methods as science
from .experiment_specification import MatrixResponseErrorSpecification


NAMESPACE = "matrix-response-experiment-exposed"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
MEDIA = "application/json"
COMMON = (("allocation", UnitAllocation), ("specification", MatrixResponseErrorSpecification))
PHASES = (
    ("fit", (*COMMON, ("features", science.MatrixE3FeatureBank), ("outcomes", science.MatrixE3OutcomeBank)), science.MatrixE3ModelSet, ScientificStage.DEVELOP),
    ("freeze", (*COMMON, ("models", science.MatrixE3ModelSet), ("prior-freeze", science.MatrixE3FrozenProducts), ("calibration", science.MatrixE3Calibration)), science.MatrixE3FrozenProducts, ScientificStage.FREEZE),
    ("forecast", (*COMMON, ("models", science.MatrixE3ModelSet), ("frozen", science.MatrixE3FrozenProducts), ("calibration", science.MatrixE3Calibration), ("feature", science.MatrixE3CausalFeature)), science.MatrixE3Forecast, ScientificStage.FREEZE),
    ("observe", (*COMMON, ("forecast", science.MatrixE3Forecast), ("outcome", science.MatrixE3PairedOutcome)), science.MatrixE3ObservedOutcome, ScientificStage.ACQUIRE),
    ("calibrate", (*COMMON, ("models", science.MatrixE3ModelSet), ("frozen", science.MatrixE3FrozenProducts), ("forecasts", science.MatrixE3Forecast), ("outcomes", science.MatrixE3ObservedOutcome)), science.MatrixE3Calibration, ScientificStage.FALSIFY),
    # These retained exposed outcomes are already development-visible. Their
    # nonpromotable assessment grants no protected reveal authorization.
    ("evaluate", (*COMMON, ("frozen", science.MatrixE3FrozenProducts), ("forecasts", science.MatrixE3Forecast), ("outcomes", science.MatrixE3ObservedOutcome)), science.MatrixE3Assessment, ScientificStage.FALSIFY),
)


def node_id(specification, operation, *, mode="", unit_id=None):
    # Full semantic operands remain in the configuration. A complete digest
    # bounds receipt/publication filenames even for long original unit labels.
    digest = sha256(canonical_json_bytes((specification, operation, mode, unit_id))).hexdigest()
    return NAMESPACE + "." + operation + "." + digest


@dataclass(frozen=True, slots=True)
class MatrixE3OperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/operation-config"
    config_id: str
    operation: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    query_census: tuple[tuple[str, int], ...]
    mode: str = ""
    unit_id: str | None = None

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (self.operation not in {phase[0] for phase in PHASES}
                or self.specification.object_schema != MatrixResponseErrorSpecification.SCHEMA
                or self.allocation.object_schema != UnitAllocation.SCHEMA
                or tuple(role for role, _ in self.query_census) != ("calibration", "evaluation")
                or any(type(count) is not int or count < 1 for _, count in self.query_census)):
            raise ValueError("E3 operation configuration changes scientific references or complete query census")
        if self.operation in ("forecast", "observe"):
            if self.mode not in ("calibration", "evaluation") or self.unit_id is None:
                raise ValueError("E3 query operation needs its exact role and whole-unit identity")
            validate_stable_id(self.unit_id)
        elif self.operation == "freeze":
            if self.mode not in ("model", "calibration") or self.unit_id is not None:
                raise ValueError("E3 freeze selects fitted or calibrated products explicitly")
        elif self.mode or self.unit_id is not None:
            raise ValueError("global E3 operations cannot select a query unit or alternate mode")
        if self.config_id != "config." + node_id(self.specification, self.operation, mode=self.mode, unit_id=self.unit_id):
            raise ValueError("E3 operation configuration changes its automatically derived identity")


def scientific_unit_ids(config):
    return () if config.unit_id is None else (config.unit_id,)


def scientific_operand_sha256s(config):
    return tuple(sorted({config.specification.object_fingerprint, config.allocation.object_fingerprint}))


def scientific_root_validator(config, context):
    from .experiment_lowering import development_root, expected_connections
    configs = tuple(row.record for row in context.config_inputs)
    if not configs or any(type(row) is not MatrixE3OperationConfig for row in configs):
        raise ValueError("E3 wave mixes another scientific configuration or lifecycle")
    if any((row.specification, row.allocation, row.query_census) !=
            (config.specification, config.allocation, config.query_census) for row in configs):
        raise ValueError("E3 wave changes a frozen experiment or selected population across phases")
    queries = {}
    for role, count in config.query_census:
        forecast_units = tuple(sorted(row.unit_id for row in configs if row.operation == "forecast" and row.mode == role))
        observe_units = tuple(sorted(row.unit_id for row in configs if row.operation == "observe" and row.mode == role))
        if len(forecast_units) != count or len(set(forecast_units)) != count or forecast_units != observe_units:
            raise ValueError("E3 wave drops complete assigned forecasts or paired outcome releases")
        queries[role] = forecast_units
    if set(queries["calibration"]) & set(queries["evaluation"]):
        raise ValueError("E3 wave reuses a whole unit across calibration and evaluation")
    expected_globals = {(role, mode) for role, mode in (("fit", ""), ("freeze", "model"),
        ("calibrate", ""), ("freeze", "calibration"), ("evaluate", ""))}
    actual_globals = tuple((row.operation, row.mode) for row in configs if row.unit_id is None)
    if len(actual_globals) != 5 or set(actual_globals) != expected_globals:
        raise ValueError("E3 wave omits fit, independent model/calibration freeze or complete evaluation")
    units = tuple(sorted(unit for values in queries.values() for unit in values))
    if context.root != development_root(config.specification, config.allocation, units, study_id=context.root.study_id):
        raise ValueError("E3 wave substitutes its source-bound exposed scientific question")
    phase = next(phase for phase in PHASES if phase[0] == config.operation)
    all_operation_units = tuple(sorted(row.unit_id for row in configs if row.operation == config.operation and row.unit_id is not None))
    if (context.node_id != node_id(config.specification, config.operation, mode=config.mode, unit_id=config.unit_id)
            or context.stage is not phase[3] or context.unit_ids != scientific_unit_ids(config)
            or context.selected_unit_ids != all_operation_units or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("E3 wave changes phase, whole-unit census, effect or exposed access")
    expected = expected_connections(config, queries)
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    if len(incoming) != len(expected) or {row.consumer_input_id for row in incoming} != set(expected):
        raise ValueError("E3 phase omits or adds causal/model/outcome input ports")
    for row in incoming:
        if (row.producer_node_id, row.producer_output_id, row.external_input_id, row.scientific_role) != expected[row.consumer_input_id]:
            raise ValueError("E3 phase bypasses its actual fit/calibrate/freeze/forecast dependency")


def output_codecs():
    kinds = {MatrixE3OperationConfig, MatrixResponseErrorSpecification, UnitAllocation,
        *(kind for _, inputs, output, _ in PHASES for kind in (*[kind for _, kind in inputs], output))}
    return {kind.SCHEMA: kind for kind in kinds}


def _optional(operation, name):
    return operation == "freeze" and name in ("prior-freeze", "calibration") or operation == "forecast" and name == "calibration"


def operation_declarations():
    permissions = tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        CapabilityPermission.READ_DEVELOPMENT)))
    return tuple(RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + operation, capability_version="1.0.0",
        implementation_id=NAMESPACE + "." + operation + ".whole-unit-source-bound-v1",
        kind=CapabilityKind.FALSIFIER if operation in ("calibrate", "evaluate") else CapabilityKind.ANALYSIS,
        config_record_type=MatrixE3OperationConfig, stage=stage,
        input_ports=tuple(sorted((RecursivePortContract(name, kind.SCHEMA, MEDIA, None,
            minimum_count=0 if _optional(operation, name) else 1,
            maximum_count=None if operation in ("calibrate", "evaluate") and name in ("forecasts", "outcomes") else 1)
            for name, kind in inputs), key=lambda port: port.port_id)),
        outputs=(OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),),
        permissions=permissions, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET, conformance_check_ids=("complete-both-view-all15-denominator", "exact-whole-root-paired-criterion", "freeze-before-dependent-outcomes"),
        runner_factory=lambda phase=operation: MatrixE3Runner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=science.identity),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if stage is ScientificStage.FREEZE
            else BarrierKind.REVEAL if stage is ScientificStage.EVALUATE else BarrierKind.NONE))
        for operation, inputs, output, stage in PHASES)


class MatrixE3Runner:
    def __init__(self, operation):
        self.operation = operation
        self.manifest = next(row.manifest() for row in operation_declarations() if row.capability_key.endswith("." + operation))

    def execute(self, context):
        try:
            records = {}
            codecs = output_codecs()
            for port in context.input_ports:
                if (port.payload_schema not in codecs or port.media_type != MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("E3 worker receives an undeclared or protected scientific operand")
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError("E3 worker source differs from its complete authenticated bytes")
                record = decode_canonical_bytes(raw, codecs[port.payload_schema], maximum_bytes=None)
                records.setdefault(port.payload_schema, []).append((record, port))

            def one(kind, optional=False):
                rows = records.get(kind.SCHEMA, [])
                if optional and not rows:
                    return None
                if len(rows) != 1:
                    raise ValueError("E3 worker omits or duplicates an exact single scientific operand")
                return rows[0][0]

            config = one(MatrixE3OperationConfig)
            if (config.operation != self.operation or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256 or context.task_id != node_id(config.specification,
                        config.operation, mode=config.mode, unit_id=config.unit_id)
                    or context.permissions != self.manifest.permissions or context.resource_budget != BUDGET):
                raise ValueError("E3 worker substitutes its immutable operation/configuration/permissions")
            specification, allocation = one(MatrixResponseErrorSpecification), one(UnitAllocation)
            if (specification.identity != config.specification or allocation.identity != config.allocation
                    or specification.evidence_scope != "EXPOSED_CONFORMANCE"
                    or config.query_census != tuple((role, len(allocation.unit_ids(role))) for role in ("calibration", "evaluation"))):
                raise ValueError("E3 worker substitutes its exact specification/allocation or protected lifecycle")
            from .experiment_lowering import expected_connections
            queries = {role: allocation.unit_ids(role) for role in ("calibration", "evaluation")}
            expected = expected_connections(config, queries)
            phase = next(row for row in PHASES if row[0] == config.operation)
            allowed_schemas = {MatrixE3OperationConfig.SCHEMA, *(kind.SCHEMA for _, kind in phase[1])}
            if set(records) - allowed_schemas or len(context.input_ports) != len(expected) + 1:
                raise ValueError("E3 worker receives future labels or another phase's undeclared inputs")
            for rows in records.values():
                for record, port in rows:
                    if port.kind is WorkerInputKind.DEPENDENCY:
                        receipts = tuple(receipt for receipt in context.dependency_receipts
                            if port.materialization_id in receipt.output_materialization_ids)
                        if len(receipts) != 1 or receipts[0].task_id not in {row[0] for row in expected.values() if row[0] is not None}:
                            raise ValueError("E3 worker dependency lacks its actual producing receipt")
                    elif record.SCHEMA not in {MatrixE3OperationConfig.SCHEMA, UnitAllocation.SCHEMA,
                            MatrixResponseErrorSpecification.SCHEMA, science.MatrixE3FeatureBank.SCHEMA,
                            science.MatrixE3OutcomeBank.SCHEMA, science.MatrixE3CausalFeature.SCHEMA, science.MatrixE3PairedOutcome.SCHEMA}:
                        raise ValueError("E3 fitted, frozen or observed products cannot substitute external sources")
            result_id = "result." + context.task_id
            if self.operation == "fit":
                product = science.fit_models(specification, allocation, one(science.MatrixE3FeatureBank),
                    one(science.MatrixE3OutcomeBank), record_id=result_id)
            elif self.operation == "freeze":
                product = science.freeze(specification, allocation, one(science.MatrixE3ModelSet), record_id=result_id,
                    model_freeze=one(science.MatrixE3FrozenProducts, optional=True), calibration=one(science.MatrixE3Calibration, optional=True))
            elif self.operation == "forecast":
                if one(science.MatrixE3CausalFeature).unit_id != config.unit_id:
                    raise ValueError("forecast changes the selected whole-unit feature")
                product = science.forecast(specification, allocation, one(science.MatrixE3ModelSet),
                    one(science.MatrixE3FrozenProducts), one(science.MatrixE3CausalFeature), role=config.mode,
                    record_id=result_id, calibration=one(science.MatrixE3Calibration, optional=True))
            elif self.operation == "observe":
                forecast = one(science.MatrixE3Forecast)
                if forecast.feature.unit_id != config.unit_id or forecast.role != config.mode:
                    raise ValueError("outcome release changes its actual pre-future unit/role seal")
                product = science.observe(one(science.MatrixE3Forecast), one(science.MatrixE3PairedOutcome), record_id=result_id)
            else:
                forecasts = tuple(row for row, _ in records[science.MatrixE3Forecast.SCHEMA])
                outcomes = tuple(row for row, _ in records[science.MatrixE3ObservedOutcome.SCHEMA])
                if self.operation == "calibrate":
                    product = science.calibrate(specification, allocation, one(science.MatrixE3ModelSet),
                        one(science.MatrixE3FrozenProducts), forecasts, outcomes, record_id=result_id)
                else:
                    product = science.evaluate(specification, allocation, one(science.MatrixE3FrozenProducts), forecasts, outcomes, record_id=result_id)
            output = context.output_ports
            if (len(output) != 1 or output[0].payload_schema != product.SCHEMA or output[0].profile is not ArtifactProfile.CANONICAL_JSON
                    or output[0].media_type != MEDIA):
                raise ValueError("E3 worker changes its complete scientific output contract")
            return RunnerResult((TaskOutputPayload(output[0].output_id, product.canonical_bytes()),),
                (ReceiptCheck("source-bound-whole-unit-e3-method", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
