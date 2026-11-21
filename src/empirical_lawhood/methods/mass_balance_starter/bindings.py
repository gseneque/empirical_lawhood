# SPDX-License-Identifier: MPL-2.0
"""Typed pure workers, original scientific scope and retained supply assessment."""

from dataclasses import replace
from functools import partial

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.methods.mass_balance_starter import design, science
from empirical_lawhood.methods.mass_balance_starter.records import MAX_BYTES, NAMESPACE, MassAssessment, MassEvidence, MassForecast, MassOperationConfig, MassOutcomes, MassPredictors, MassSpecification


def units(config):
    return config.independent_unit_ids


def operands(config):
    return tuple(sorted({p.object_fingerprint for p in (config.specification, config.predictors, config.outcomes) if p is not None}))


def root_validator(config, context):
    selected = tuple(v.record for v in context.config_inputs)
    assessors = tuple(c for c in selected if type(c) is MassOperationConfig and c.phase == "assess")
    if len(assessors) != 1:
        raise ValueError("starter requires its complete independent assessor")
    assessor, = assessors
    if (tuple(sorted(selected, key=lambda c: c.node_id)) != (assessor, science.prediction_config(assessor))
            or config not in selected or context.node_id != config.node_id
            or context.root != design.scientific_root(assessor)
            or context.requirements != (design.scientific_contract(assessor)[0],)
            or context.connections != (design.scientific_contract(assessor)[1],)
            or context.links != design.links_for(assessor) or context.external_inputs != design.external_contracts(assessor)
            or context.unit_ids != units(config) or context.selected_unit_ids != units(config)
            or context.stage is not design.stage(config.phase) or context.complete_unit_census
            or context.outcome_access is not design.ACCESS or context.visibility_ceiling is not design.VISIBILITY):
        raise ValueError("starter changes its original complete design, scientific consumer or exposure boundary")


def assessment_projector(record, requirement, connection):
    if type(record) is not MassAssessment:
        return ()
    record.__post_init__()
    if (requirement, connection) != design.scientific_contract(record.config):
        raise ValueError("starter supply assessment changes its exact scientific consumer")
    # Availability of the complete forecast is independent of claim truth.
    return (RequirementSupplyAssessment("assessment." + record.record_id,
        ObjectIdentity.from_record(requirement.requirement_id, requirement),
        ObjectIdentity.from_record(connection.connection_id, connection), AssessmentPhase.INSTANCE,
        AssessmentDisposition.SATISFIED, record.config.node_id,
        tuple(sorted((record.forecast, record.identity), key=lambda p: p.object_id)), ()),)


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            codecs = {c.SCHEMA: c for c in (MassOperationConfig, MassPredictors, MassOutcomes, MassForecast)}
            received = {}
            for port in context.input_ports:
                kind = codecs.get(port.payload_schema)
                if kind is None or kind in received or port.media_type != "application/json":
                    raise ValueError("starter changes the exact worker input role or census")
                received[kind] = decode_canonical_bytes(port.read(), kind, maximum_bytes=MAX_BYTES)
            config = received.pop(MassOperationConfig)
            if (config.node_id != context.task_id or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256 or context.resource_budget != design.BUDGET
                    or context.permissions != design.PERMISSIONS or context.outcome_access is not design.ACCESS):
                raise ValueError("starter changes its compiler-derived worker contract")
            if config.phase == "predict" and set(received) == {MassPredictors}:
                product = science.predict(config, received[MassPredictors])
            elif config.phase == "assess" and set(received) == {MassForecast, MassOutcomes}:
                product = science.assess(config, received[MassForecast], received[MassOutcomes])
            else:
                raise ValueError("starter substitutes the predictor or independent observation role")
            if tuple(p.output_id for p in context.output_ports) != (context.task_id + ".product",):
                raise ValueError("starter changes its single canonical result output")
            return RunnerResult((TaskOutputPayload(context.task_id + ".product", product.canonical_bytes()),),
                                (ReceiptCheck("mass-balance-original-input-census", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    codecs = {c.SCHEMA: c for c in (MassSpecification, MassEvidence, MassOperationConfig, MassPredictors,
                                   MassOutcomes, MassForecast, MassAssessment)}
    rows = []
    for phase in ("assess", "predict"):
        ports = (("forecast", MassForecast), ("outcomes", MassOutcomes)) if phase == "assess" else (("predictors", MassPredictors),)
        output = MassAssessment if phase == "assess" else MassForecast
        row = RecursiveOperationDeclaration(capability_key=NAMESPACE + "." + phase, capability_version="1.0.0",
            implementation_id=NAMESPACE + "." + phase + ".v1",
            kind=CapabilityKind.FALSIFIER if phase == "assess" else CapabilityKind.TRANSFORM,
            config_record_type=MassOperationConfig, stage=design.stage(phase),
            input_ports=tuple(RecursivePortContract(key, c.SCHEMA, "application/json", MAX_BYTES) for key, c in ports),
            outputs=(OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
            permissions=design.PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=design.ACCESS, visibility_ceiling=design.VISIBILITY, resources=design.BUDGET,
            conformance_check_ids=("mass-balance-complete-census", "mass-balance-independent-falsifier"),
            runner_factory=Runner, record_codecs=codecs,
            scientific_hooks=RecursiveScientificHooks(assessment_projector=assessment_projector,
                scientific_operand_sha256s=operands, scientific_unit_ids=units, scientific_root_validator=root_validator))
        rows.append(replace(row, runner_factory=partial(Runner, manifest=row.manifest())))
    return tuple(rows)
