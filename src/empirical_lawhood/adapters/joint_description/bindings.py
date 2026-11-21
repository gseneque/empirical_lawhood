# SPDX-License-Identifier: MPL-2.0
"""One set of shared recursive operation declarations for every scientific family."""
from dataclasses import replace
from functools import partial,lru_cache

from empirical_lawhood.adapters.joint_description import lowering as workflow
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition,AssessmentPhase,RequirementSupplyAssessment
from empirical_lawhood.science.joint_description import MAX_BYTES,Assessment
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.plans import OutputTemplate
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration,RecursiveScientificHooks,RecursiveExecutionProperties
from .records import NAMESPACE,NATIVE_PHASES,PHASES,OperationConfig,effect_slots,operands,phase_config,units
from .runner import INPUTS,OUTPUTS,KINDS,Runner,NativeRunner,prepare_native_work


def root_validator(config,context):
    selected=tuple(row.record for row in context.config_inputs)
    configs=tuple(phase_config(config,p) for p in PHASES)
    requirements,connections=workflow.contracts(config)
    if (tuple(sorted(selected,key=lambda r:r.node_id))!=configs or context.node_id!=config.node_id
            or context.root!=workflow.root_for(config) or context.requirements!=requirements
            or context.connections!=connections or context.links!=workflow.links(config)
            or context.external_inputs!=workflow.externals(config)
            or context.unit_ids!=units(config) or context.selected_unit_ids!=units(config)
            or context.complete_unit_census!=(config.phase in NATIVE_PHASES)
            or context.stage is not workflow.stage(config.phase)
            or context.outcome_access is not workflow.ACCESS or context.visibility_ceiling is not workflow.VISIBILITY):
        raise ValueError("joint-description changed its authored recursive graph, causal requirements or complete independent-root census")


def assessment_projector(record,requirement,connection):
    if type(record) is not Assessment:
        return ()
    # Completion of supplied scientific roles is separate from hypothesis truth.
    return (RequirementSupplyAssessment("assessment."+connection.connection_id,
        ObjectIdentity.from_record(requirement.requirement_id,requirement),
        ObjectIdentity.from_record(connection.connection_id,connection),AssessmentPhase.INSTANCE,
        AssessmentDisposition.SATISFIED,record.record_id.removesuffix(".assessment"),
        tuple(sorted((record.forecast,record.identity),key=lambda r:r.object_id)),()),)


@lru_cache(maxsize=1)
def operation_declarations():
    rows=[]
    # The compiler checks an edge against its supplier's whole publication
    # allowance. The worker separately enforces the selected record type's limit.
    native_input_bounds = {
        OUTPUTS[phase][1]: workflow.budget(phase, "cpu").output_bytes for phase in NATIVE_PHASES
    }
    for phase in PHASES:
        native=phase in NATIVE_PHASES
        for device in (("cpu","gpu") if native else ("cpu",)):
            output,kind=OUTPUTS[phase]
            declaration=RecursiveOperationDeclaration(capability_key=NAMESPACE+"."+phase+"."+device,
                capability_version="1.0.0",implementation_id=NAMESPACE+"."+phase+"."+device+".v1",
                kind=CapabilityKind.FALSIFIER if phase=="assess" else CapabilityKind.SIMULATOR if native else CapabilityKind.TRANSFORM,
                config_record_type=OperationConfig,stage=workflow.stage(phase),
                input_ports=tuple(sorted((RecursivePortContract(name,k.SCHEMA,"application/json",native_input_bounds.get(k,MAX_BYTES))
                    for name,k in INPUTS[phase]),key=lambda r:r.port_id)),
                outputs=(OutputTemplate(output,kind.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json"),),
                permissions=workflow.PERMISSIONS,evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
                outcome_access=workflow.ACCESS,visibility_ceiling=workflow.VISIBILITY,resources=workflow.budget(phase,device),
                conformance_check_ids=("joint-description.complete-census","joint-description.forecast-before-outcome"),
                runner_factory=NativeRunner if native else Runner,record_codecs={k.SCHEMA:k for k in KINDS},
                scientific_hooks=RecursiveScientificHooks(assessment_projector=assessment_projector,
                    scientific_operand_sha256s=operands,scientific_unit_ids=units,
                    native_effect_slot_ids=effect_slots if native else None,scientific_root_validator=root_validator),
                execution_properties=RecursiveExecutionProperties(native_effect=native,complete_unit_census=native,
                    native_work_preparer=prepare_native_work if native else None))
            rows.append(replace(declaration,runner_factory=partial(NativeRunner if native else Runner,manifest=declaration.manifest())))
    return tuple(rows)
