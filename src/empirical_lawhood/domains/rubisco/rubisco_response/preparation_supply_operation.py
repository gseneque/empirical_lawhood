# SPDX-License-Identifier: MPL-2.0
"""Registered non-native admission of original local scientific contributions."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import PreparationResponseAssessment, EnvironmentalPreparationResponseAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import CAPABILITY, UNIT, PreparationSupplyResult, PreparationSupplySelection, assess_supply, project_supply_assessments

MAX_INPUT = 64 * 2**20
BUDGET = ResourceBudget(1, 2 * 2**30, 0, 300, 128 * 2**20, 512 * 2**20)


@dataclass(frozen=True, slots=True)
class PreparationSupplyConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-supply-config'
    selection: PreparationSupplySelection

    def __post_init__(self):
        exact(self.selection, PreparationSupplySelection)

    @property
    def config_id(self):
        return 'config.preparation-supply.' + self.selection.fingerprint()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


class PreparationSupplyRunner:
    def __init__(self):
        self.manifest = operation_declaration().manifest()

    def execute(self, context):
        try:
            if (context.task_id != CAPABILITY or context.resource_budget != BUDGET
                    or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                raise ValueError('local supply changes its selected non-native operation')
            config_port, = (p for p in context.input_ports if p.payload_schema == PreparationSupplyConfig.SCHEMA)
            config = decode_canonical_bytes(config_port.read(MAX_INPUT), PreparationSupplyConfig, maximum_bytes=MAX_INPUT)
            if ((config.config_id, config.fingerprint(), config_port.artifact_id) !=
                    (context.config.config_id, context.config.content_sha256, context.config.artifact_id)):
                raise ValueError('local supply substitutes its frozen destination selection')
            # Worker ports expose the authenticated artifact identity, not the
            # compiler's graph-link name. Match each original product directly.
            ports = {p.artifact_id: p for p in context.input_ports if p is not config_port}
            expected = {config.selection.product(r)[1].artifact.artifact_id for r in config.selection.records}
            if (len(context.input_ports) != len(expected) + 1 or set(ports) != expected
                    or any(p.kind is not WorkerInputKind.EXTERNAL
                        or p.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or p.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                        for p in context.input_ports)):
                raise ValueError('local supply omits an original selected contribution')
            for record in config.selection.records:
                _, product = config.selection.product(record)
                port = ports[product.artifact.artifact_id]
                if ((port.payload_schema, port.media_type, port.size_bytes) !=
                        (record.SCHEMA, product.artifact.media_type, product.artifact.size_bytes)
                        or port.read(MAX_INPUT) != record.canonical_bytes()):
                    raise ValueError('local supply changes the actual original contribution bytes')
            result = assess_supply(config.selection)
            output, = context.output_ports
            if output.output_id != CAPABILITY + '.assessment' or output.payload_schema != result.SCHEMA:
                raise ValueError('local supply changes its actual assessment output')
            return RunnerResult((TaskOutputPayload(output.output_id, result.canonical_bytes()),),
                (ReceiptCheck('original-local-supply-without-native-contact-or-kinetic-admission', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration():
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_translation import validate_root
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_inquiry import inquiry_hooks
    return RecursiveOperationDeclaration(capability_key=CAPABILITY, capability_version='1.0.0',
        implementation_id='original-local-preparation-response-admission-v1', kind=CapabilityKind.FALSIFIER,
        config_record_type=PreparationSupplyConfig, stage=ScientificStage.FALSIFY,
        input_ports=(RecursivePortContract('prefix', ActivePreparationPrefixReadout.SCHEMA, 'application/json', MAX_INPUT, 2, 2),
            RecursivePortContract('response', PreparationResponseAssessment.SCHEMA, 'application/json', MAX_INPUT, 0, 1),
            RecursivePortContract('response-environment', EnvironmentalPreparationResponseAssessment.SCHEMA, 'application/json', MAX_INPUT, 0, 1)),
        outputs=(OutputTemplate('assessment', PreparationSupplyResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET, conformance_check_ids=('actual-contribution-destination-supply', 'adverse-finding-is-not-positive-physics',
            'complete-paired-checkpoint-and-question-denominators', 'zero-new-native-effects'),
        runner_factory=PreparationSupplyRunner,
        record_codecs={kind.SCHEMA: kind for kind in (PreparationSupplyConfig, PreparationSupplySelection,
            PreparationSupplyResult, ActivePreparationPrefixReadout, PreparationResponseAssessment,
            EnvironmentalPreparationResponseAssessment)},
        scientific_hooks=RecursiveScientificHooks(scientific_root_validator=validate_root,
            assessment_projector=project_supply_assessments,
            scientific_operand_sha256s=lambda c: tuple(sorted({c.selection.design.fingerprint(),
                *(r.fingerprint() for r in c.selection.records)})),
            scientific_unit_ids=lambda c: (UNIT,), native_effect_slot_ids=lambda c: ()),
        inquiry_hooks=inquiry_hooks())
