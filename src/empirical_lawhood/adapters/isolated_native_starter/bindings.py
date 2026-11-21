# SPDX-License-Identifier: MPL-2.0
"""A closed native declaration through the ordinary recursive provider."""

from dataclasses import replace
from functools import partial

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.adapters.isolated_native_starter import design
from empirical_lawhood.adapters.isolated_native_starter.records import MAX_SOURCE_BYTES, NAMESPACE, UNIT, ProcessLog, SquareConfig, SquareInput, SquareNativeResult, SquareResult, SquareSpecification
from empirical_lawhood.adapters.isolated_native_starter.runner import Runner
from empirical_lawhood.adapters.isolated_native_starter.work import effect_slots, prepare_native_work


def units(config):
    config.__post_init__()
    return (UNIT,)


def operands(config):
    spec = config.specification
    return tuple(sorted({value.object_fingerprint for value in (spec.identity, spec.operand, spec.provenance)}))


def root_validator(config, context):
    if (tuple(row.record for row in context.config_inputs) != (config,)
            or context.node_id != config.node_id or context.root != design.root_for(config)
            or context.requirements or context.connections or context.links != design.links_for(config)
            or context.external_inputs != design.input_contracts(config)
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,)
            or not context.complete_unit_census or context.stage is not ScientificStage.TRANSFORM
            or context.outcome_access is not design.ACCESS or context.visibility_ceiling is not design.VISIBILITY):
        raise ValueError("isolated starter changes its complete exposed design, inputs or native unit")


def operation_declaration():
    codecs = {kind.SCHEMA: kind for kind in (SquareSpecification, SquareConfig, SquareInput,
        SquareNativeResult, SquareResult, ProcessLog, NumericalProducingProvenance)}
    declaration = RecursiveOperationDeclaration(capability_key=NAMESPACE + ".calculate", capability_version="1.0.0",
        implementation_id=NAMESPACE + ".calculate.v1", kind=CapabilityKind.TRANSFORM,
        config_record_type=SquareConfig, stage=ScientificStage.TRANSFORM,
        input_ports=tuple(RecursivePortContract(name, kind.SCHEMA, "application/json", MAX_SOURCE_BYTES)
            for name, kind in (("operand", SquareInput), ("provenance", NumericalProducingProvenance))),
        outputs=(OutputTemplate("product", SquareResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        permissions=design.PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=design.ACCESS, visibility_ceiling=design.VISIBILITY, resources=design.BUDGET,
        conformance_check_ids=("isolated-starter-independent-formula", "isolated-starter-no-uncertain-replay"),
        runner_factory=Runner, record_codecs=codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operands,
            scientific_unit_ids=units, native_effect_slot_ids=effect_slots, scientific_root_validator=root_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work))
    return replace(declaration, runner_factory=partial(Runner, manifest=declaration.manifest()))
