# SPDX-License-Identifier: MPL-2.0
"""Additive E4 confirmation futures with actual original-CAL parent custody.

The original native method/configuration remains unchanged. Only this distinct
installed variant accepts the additional public calibration custody operand.
"""


from dataclasses import dataclass, replace
from functools import partial

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import operation_bindings as core, response_bindings as response, revision_future_bindings as original
from .revision_calibration_custody import ScheduledRevisionCalibrationCustody

NAMESPACE = "matrix-scheduled-revision-calibrated-future"


@dataclass(frozen=True, slots=True)
class PreparedCalibratedRevisionFuture:
    original: original.AuthenticatedRevisionFuture
    calibration_custody: ObjectIdentity


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())




def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def scientific_root_validator(config, context):
    from .compact_qualification import _qualification
    extra = tuple(value for value in context.links if value.consumer_node_id == context.node_id
        and value.consumer_input_id == "revision-calibration-custody")
    if len(extra) != 1 or extra[0].producer_node_id is not None or extra[0].external_input_id is None:
        raise ValueError("calibrated revision future omits its actual original-CAL prerequisite")
    external = tuple(value for value in context.external_inputs if value.input_id == extra[0].external_input_id)
    qualified = tuple(value for value in context.qualifications if value.source_id == extra[0].external_input_id)
    if (len(external) != 1 or len(qualified) != 1 or external[0].payload_schema != ScheduledRevisionCalibrationCustody.SCHEMA
            or external[0].expected_content_sha256 is None):
        raise ValueError("calibrated revision future loses the exact original-CAL source qualification")
    _qualification(context.root, context, qualified[0].materialization.object_id, ScheduledRevisionCalibrationCustody.SCHEMA,
        external[0].expected_content_sha256, original.BLIND, original.PROSPECTIVE, ScheduledRevisionCalibrationCustody.VERSION)
    original.scientific_root_validator(config, replace(context, links=tuple(value for value in context.links if value not in extra)))


def _decode(context, role, *, prepared, response_phase):
    if type(prepared) is not PreparedCalibratedRevisionFuture:
        raise PermissionError("calibrated revision future requires actual original-CAL parent preparation")
    contract = context.prepared_invocation
    if contract is None:
        raise PermissionError("calibrated revision future lacks its actual full issued invocation")
    contract.require_complete()
    contract.validate_context(context)
    ports = tuple(port for port in context.input_ports if port.payload_schema == ScheduledRevisionCalibrationCustody.SCHEMA)
    if (len(ports) != 1 or ports[0].kind is not WorkerInputKind.EXTERNAL
            or ports[0].outcome_access is not original.BLIND or ports[0].visibility_ceiling is not original.PROSPECTIVE):
        raise PermissionError("calibrated revision future loses its exact blind original-CAL custody port")
    custody = original._read_record(ports[0], ScheduledRevisionCalibrationCustody)
    if custody.identity != prepared.calibration_custody:
        raise PermissionError("calibrated revision future substitutes original-CAL parent custody")
    selected = next(value for value in operation_manifests() if value.capability_key == NAMESPACE + "." + role)
    scope, view = original.require_revision_future(context, role, prepared=prepared.original, expected_manifest=selected,
        additional_external_ports=ports)
    edges = tuple(value for value in contract.execution_task_record.scientific_inputs
        if value.consumer_input_id == "revision-calibration-custody")
    if (scope.calibration != custody.calibration or len(edges) != 1 or edges[0].producer_task_id is not None
            or edges[0].external_input_id is None or edges[0].operational_logical_artifact_id != ports[0].artifact_id):
        raise PermissionError("calibrated revision future changes its actual earlier original-CAL prerequisite")
    decoder = original.acquisition.decode_response if response_phase else original.acquisition.decode_core
    result = decoder(view, role)
    original._check_original_join(scope, result)
    return result


def decode_core(context, role, *, prepared=None):
    return _decode(context, role, prepared=prepared, response_phase=False)


def decode_response(context, role, *, prepared=None):
    return _decode(context, role, prepared=prepared, response_phase=True)


def prepared_runner(runner, prepared, calibration_custody):
    cls, decoder = (response.ScheduledPulseNativeRunner, decode_response) if runner.role == "responses" else (core.ScheduledNativeRunner, decode_core)
    if type(runner) is not cls or type(prepared) is not original.AuthenticatedRevisionFuture:
        raise PermissionError("calibrated revision future substitutes its actual original native worker")
    return cls(runner.role, decoder=partial(decoder, prepared=PreparedCalibratedRevisionFuture(prepared, calibration_custody)), manifest=runner.manifest)


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def add_calibrated_revision_future_dependencies(draft, scope, seal_custody, calibration_custody):
    """Derive the distinct CONF variant, retaining every original native ID."""
    if type(calibration_custody) is not ScheduledRevisionCalibrationCustody or scope.calibration != calibration_custody.calibration:
        raise ValueError("revision confirmation requires its exact original public calibration custody")
    calibration_custody.__post_init__()
    draft, operands = original.add_revision_future_dependencies(draft, scope, seal_custody)
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
    selections = {value.selection.capability_key.rsplit(".", 1)[-1]: value.selection for value in operation_registrations()}
    record = calibration_custody
    external = RecursiveExternalInput("external." + record.record_id, record.record_id, record.SCHEMA,
        "application/json", len(record.canonical_bytes()), original.BLIND, original.PROSPECTIVE, record.fingerprint(), "SOURCE")
    operations, links = [], list(draft.links)
    for operation in draft.operations:
        if operation.selection.capability_key.startswith(original.NAMESPACE + "."):
            role = operation.selection.capability_key.rsplit(".", 1)[-1]
            operation = replace(operation, selection=selections[role])
            links.append(RecursiveInputLink("edge." + operation.node_id + ".revision-calibration-custody", operation.node_id,
                "revision-calibration-custody", external_input_id=external.input_id, scientific_role="SOURCE"))
        operations.append(operation)
    if external.input_id in {value.input_id for value in draft.external_inputs} or record.record_id in operands:
        raise ValueError("revision confirmation aliases its additional original-CAL prerequisite")
    operands[record.record_id] = record
    return replace(draft, operations=tuple(operations), external_inputs=tuple(sorted((*draft.external_inputs, external), key=lambda value: value.input_id)),
        links=tuple(sorted(links, key=lambda value: value.edge_id))), operands


def _operation_declaration(base):
    role = base.capability_key.rsplit('.', 1)[-1]
    cls, decoder = (response.ScheduledPulseNativeRunner, decode_response) if role == 'responses' else (core.ScheduledNativeRunner, decode_core)
    selected = replace(base, capability_key=NAMESPACE+'.'+role,
        implementation_id=NAMESPACE+'.'+role+'.original-calibration-and-seal.v1',
        input_ports=tuple(sorted((*base.input_ports,
            RecursivePortContract('revision-calibration-custody', ScheduledRevisionCalibrationCustody.SCHEMA,
                'application/json', original.MAXIMUM_RECORD_BYTES)), key=lambda port: port.port_id)),
        input_record_types=tuple(sorted((*base.input_record_types, ScheduledRevisionCalibrationCustody),
            key=lambda kind: (kind.SCHEMA, kind.VERSION))),
        conformance_check_ids=tuple(sorted((*base.conformance_check_ids, 'original-revision-calibration-before-confirmation'))),
        scientific_hooks=replace(base.scientific_hooks, scientific_root_validator=scientific_root_validator),
        runner_factory=lambda: cls(role, decoder=decoder, manifest=selected.manifest()),
        execution_properties=replace(base.execution_properties, runner_preparation_factory=original.prepare_for_invocation))
    return selected


def operation_declarations():
    return tuple(_operation_declaration(base) for base in original.operation_declarations())
