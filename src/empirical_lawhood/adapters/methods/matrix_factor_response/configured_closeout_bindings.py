# SPDX-License-Identifier: MPL-2.0
"""PURE publication of authenticated CAL missingness, without native entry."""
from dataclasses import dataclass, replace

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from .configured_closeout_execution import ConfiguredE3ClosedExecution, ConfiguredE3MissingOutcomeConfig, ConfiguredE3MissingOutcomeProducts
from .configured_continued_response import original_config
from .configured_protected_methods import ConfiguredProtectedE3PairedOutcome
from .configured_protected_response_preparation import response_task_id
from .configured_retained_execution import source_binding
from .configured_protected_source_records import NAMESPACE
from .protected_input_custody import read_protected_e3_response_input


def _units(config):
    if type(config) is not ConfiguredE3MissingOutcomeConfig:
        raise TypeError('CAL closeout requires its distinct PURE assessment configuration')
    config.__post_init__()
    return (config.source.root.root.independent_group_id,)


def _operands(config):
    _units(config)
    return tuple(sorted({pin.object_fingerprint for pin in (config.closeout, config.products,
        config.continuation, config.specification, config.source.identity, config.source_manifest,
        config.response_selection, config.protocol, config.numerical_profile)}))


@dataclass(frozen=True, slots=True)
class _Factory:
    publication_requirement: object
    scientific_root_validator: object

    def __call__(self):
        return ConfiguredE3MissingOutcomeRunner(missing_outcome_declaration(
            publication_requirement=self.publication_requirement,
            scientific_root_validator=self.scientific_root_validator).manifest())


def missing_outcome_declaration(*, publication_requirement, scientific_root_validator):
    kinds = (ConfiguredE3MissingOutcomeConfig, ConfiguredE3ClosedExecution, ConfiguredE3MissingOutcomeProducts,
        ScheduledResponseScore, ConfiguredProtectedE3PairedOutcome)
    key = NAMESPACE + '.missing-response-score'
    return RecursiveOperationDeclaration(key, '1.0.0', key + '.authenticated-cal-missingness.v1',
        CapabilityKind.FALSIFIER, ConfiguredE3MissingOutcomeConfig, ScientificStage.FALSIFY,
        (RecursivePortContract('closeout', ConfiguredE3ClosedExecution.SCHEMA, 'application/json', None),
            RecursivePortContract('products', ConfiguredE3MissingOutcomeProducts.SCHEMA, 'application/json', None)),
        (OutputTemplate('outcome', ConfiguredProtectedE3PairedOutcome.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),
            OutputTemplate('score', ScheduledResponseScore.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json')),
        tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_SEALED_OUTCOMES, CapabilityPermission.READ_DEVELOPMENT))), EvidenceCeiling.RESPONSE,
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE, ResourceBudget(1, None, 0, None, None, None),
        ('actual-cal-contact-and-assessment-provenance', 'no-native-completion-or-reentry'),
        _Factory(publication_requirement, scientific_root_validator), {kind.SCHEMA: kind for kind in kinds},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=_units, scientific_operand_sha256s=_operands,
            scientific_root_validator=scientific_root_validator), execution_properties=RecursiveExecutionProperties(),
        publication_requirements=(publication_requirement,), provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))


class ConfiguredE3MissingOutcomeRunner:
    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, context):
        prepared = context.prepared_invocation
        try:
            if (type(prepared) is not PreparedInvocationContract or prepared.manifest != self.manifest
                    or prepared.native_effect or prepared.execution_task_record.stage is not ScientificStage.FALSIFY
                    or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                    or not self.manifest.resource_ceiling.contains(context.resource_budget)):
                raise PermissionError('CAL closeout publication requires its actual PURE prepared invocation')
            prepared.validate_context(context)
            ports = {port.artifact_id: port for port in context.input_ports}
            config_port = ports.get(context.config.artifact_id)
            if config_port is None or config_port.kind is not WorkerInputKind.EXTERNAL:
                raise PermissionError('CAL closeout publication loses its frozen configuration')
            config = read_protected_e3_response_input(config_port, prepared, ConfiguredE3MissingOutcomeConfig)
            if (context.task_id != response_task_id(config.source.root_id, 'response-score')
                    or context.config.content_sha256 != config.fingerprint()
                    or context.config.config_id != config.config_id):
                raise PermissionError('CAL closeout publication substitutes its issued configuration')
            edges = validated_scientific_input_edges(context, config_port=config_port)
            if ({edge.consumer_input_id for edge in edges} != {'closeout', 'products'} or len(edges) != 2
                    or len(context.input_ports) != 3 or len(ports) != 3):
                raise PermissionError('CAL closeout publication changes its exact input census')
            values = {}
            kinds = {'closeout': ConfiguredE3ClosedExecution, 'products': ConfiguredE3MissingOutcomeProducts}
            for edge in edges:
                port = ports[edge.operational_logical_artifact_id]
                if port.kind is not WorkerInputKind.EXTERNAL or edge.producer_task_id is not None:
                    raise PermissionError('CAL closeout publication changes its authenticated external products')
                values[edge.consumer_input_id] = read_protected_e3_response_input(port, prepared, kinds[edge.consumer_input_id])
            scope, products = values['closeout'], values['products']
            roots = tuple(row for row in scope.calibration_roots if row.outcome_task_id == context.task_id)
            if (scope.identity != config.closeout or products.identity != config.products
                    or scope.retention.identity != config.continuation or scope.retention.continued_run_id != context.run_id
                    or context.task_id not in scope.unfinished_task_ids or len(roots) != 1
                    or roots[0].missing_products != products.identity
                    or roots[0].outcome_visibility is not products.visibility_ceiling
                    or roots[0].native_configuration != ObjectIdentity.from_record(products.original_config.config_id, products.original_config)
                    or roots[0].contact != ObjectIdentity.from_record('native-contact.' + roots[0].native_task_id, products.availability.parent_contact)
                    or products.assessment_provenance != scope.retention.response_provenance
                    or prepared.implementation != source_binding(products.assessment_provenance)
                    or original_config(config) != replace(original_config(products.original_config),
                        config_id=config.config_id, operation='response-score')):
                raise PermissionError('CAL closeout publication changes original contact, frozen science or actual assessment source')
            product_port = ports[next(edge.operational_logical_artifact_id for edge in edges if edge.consumer_input_id == 'products')]
            if (product_port.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                    or product_port.visibility_ceiling is not products.visibility_ceiling):
                raise PermissionError('CAL closeout publication changes original outcome access or visibility')
            ceiling = inherited_visibility(tuple(port.visibility_ceiling for port in context.input_ports),
                OutcomeAccess.EVALUATION_SEALED)
            outputs = {row.output_id.rsplit('.', 1)[-1]: row for row in context.output_ports}
            records = {'score': products.score, 'outcome': products.outcome}
            if (len(context.output_ports) != 2 or set(outputs) != set(records)
                    or any((port.payload_schema, port.profile, port.media_type) != (
                        records[name].SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json') for name, port in outputs.items())
                    or any(row.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                        or row.visibility_ceiling is not ceiling for row in prepared.execution_task_record.outputs)):
                raise PermissionError('CAL closeout publication substitutes output types or outcome access')
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, records[name].canonical_bytes())
                for name, port in sorted(outputs.items())),
                (ReceiptCheck('cal-closeout-missingness-without-native-completion', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
