# SPDX-License-Identifier: MPL-2.0
"""One installed controlled forecast through the existing native lifecycle.

Historical HOLD and uncertain contact remain scientific operands. These cold
contracts introduce neither acquisition authority nor a second native runner.
"""

from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as original
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveExecutionProperties, RecursiveScientificHooks
from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec
from . import contracts as c, forecast_step_control as step, lossless_evidence_stream as stream
from . import lossless_segment_records as records, segmented_evidence as evidence
from .controlled_forecast_config import (CAPABILITY_KEY, ROLE_TYPES, ControlledForecastConfig, build_config,
    control_operands, native_effect_slot_ids, node_id, record_identity, require_config_records)
from .lossless_segment_runner import LosslessControlledRunner

STREAM_MEDIA = original.media_for("segments")

def artifact_id(config, role):
    """Operational roles stay unique even when original scientific labels alias."""
    return "input." + node_id(config.index) + "." + role


def input_links(config):
    node = node_id(config.index)
    return tuple(RecursiveInputLink("edge." + node + "." + role, node, role,
        external_input_id="external." + node + "." + role,
        scientific_role="HISTORY" if role in {"history", "uncertain-work"} else "SOURCE",
        requirement_id=config.history_requirement.requirement_id if role == "history" else None,
        connection_id=config.history_connection.connection_id if role == "history" else None)
        for role in sorted(ROLE_TYPES))


def scientific_root_validator(config, context):
    expected_node = node_id(config.index)
    if (context.root != config.development_root or context.node_id != expected_node
            or context.stage is not ScientificStage.ACQUIRE
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.unit_ids != (c.UNIT,) or context.selected_unit_ids != (c.UNIT,) or not context.complete_unit_census
            or context.requirements != (config.history_requirement,) or context.connections != (config.history_connection,)
            or context.qualifications or context.known_design_inputs
            or tuple((row.node_id, row.record) for row in context.config_inputs) != ((expected_node, config),)
            or context.links != input_links(config)):
        raise ValueError("controlled forecast changes its complete scientific root/stage/role/history graph")


def forecast_draft(records_by_role, *, draft_id, study_id):
    """Freeze one selected policy forecast; retain complete original rosters."""
    from .recursive_translation import _campaign
    config = build_config(records_by_role, study_id=study_id)
    node = node_id(config.index)
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=operation_declaration().registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node + ".original-custody",),
        resource_budget=original.BUDGET, resource_lock_ids=("battery-native-single-worker",), maximum_attempts=1)
    external = tuple(RecursiveExternalInput("external." + node + "." + role, artifact_id(config, role),
        ref.object_schema, original.MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        ref.object_fingerprint, "HISTORY" if role in {"history", "uncertain-work"} else "SOURCE") for role, ref in config.role_bindings)
    return RecursiveStudyDraft(draft_id, original.QUESTION, _campaign(config.development_root, draft_id),
        (config.history_requirement,), (config.history_connection,), (), (operation,), external, input_links(config), (node,),
        development_study=config.development_root, contribution_parents=(records_by_role["history-contribution"],))


def _decode_port(port, kind):
    cursor = port.cursor()
    try:
        raw = cursor.read()
        if len(raw) != port.size_bytes:
            raise ValueError("controlled forecast input size differs from its exact sealed materialization")
        return decode_canonical_bytes(raw, kind, maximum_bytes=None)
    finally:
        cursor.close()


def decode_role_input(config, role, input_ports):
    """Authenticate a declared role without flattening scientific object labels."""
    if role not in ROLE_TYPES:
        raise ValueError("controlled forecast names an undeclared input role")
    found = tuple(port for port in input_ports if port.artifact_id == artifact_id(config, role))
    if len(found) != 1:
        raise ValueError("controlled forecast loses its unique operational input role")
    port = found[0]
    if (port.kind is not WorkerInputKind.EXTERNAL or port.payload_schema != ROLE_TYPES[role].SCHEMA
            or port.media_type != original.MEDIA or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("controlled forecast substitutes an original role type or development access")
    record = _decode_port(port, ROLE_TYPES[role])
    if record_identity(role, record) != dict(config.role_bindings)[role]:
        raise ValueError("controlled forecast changes the exact original role identity/bytes")
    return record, port


def load_inputs(context, manifest):
    """Read independent cursors; preserve the full original context and ports."""
    config_ports = tuple(port for port in context.input_ports if port.payload_schema == ControlledForecastConfig.SCHEMA)
    if len(config_ports) != 1:
        raise ValueError("controlled forecast omits its exact wrapper configuration")
    config_port = config_ports[0]
    config = _decode_port(config_port, ControlledForecastConfig)
    if (context.task_id != node_id(config.index) or context.permissions != manifest.permissions
            or context.resource_budget != original.BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or config_port.kind is not WorkerInputKind.EXTERNAL or config_port.artifact_id != context.config.artifact_id
            or context.config.config_id != config.config_id or context.config.content_sha256 != config.fingerprint()
            or context.dependency_receipts):
        raise ValueError("controlled forecast substitutes its original full task/config/access/resources/receipt census")
    decoded, selected_ports = {}, {}
    for role, _ in config.role_bindings:
        record, port = decode_role_input(config, role, context.input_ports)
        decoded[role], selected_ports[role] = record, port
    if len(context.input_ports) != len(ROLE_TYPES) + 1:
        raise ValueError("controlled forecast has undeclared or aliased input roles")
    outputs = operation_declaration().outputs
    if tuple((port.output_id, port.payload_schema, port.profile, port.media_type) for port in context.output_ports) != tuple(
            (context.task_id + "." + output.output_id, output.payload_schema, output.profile, output.media_type) for output in outputs):
        raise ValueError("controlled forecast substitutes its complete original output contract")
    require_config_records(config, decoded)
    return config, decoded, selected_ports


class ControlledForecastWorker(LosslessControlledRunner):
    def __init__(self):
        self.operation = "forecast"
        self.manifest = operation_declaration().manifest()

    @staticmethod
    def require_retained_work_contract():
        raise ValueError("SOFTWARE: controlled forecast config1.0 lacks authenticated current unfinished-parent work; native entry requires the retained-work condition contract")

    def preflight(self, context):
        self.require_retained_work_contract()

    def project_forecast_scope(self, context, expected_parent):
        self.require_retained_work_contract()

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        self.require_retained_work_contract()

    def control_operands(self, context):
        _, decoded, _ = load_inputs(context, self.manifest)
        return control_operands(decoded)

    def forecast_operands(self, context):
        _, decoded, ports = load_inputs(context, self.manifest)
        return decoded["forecast-config"], decoded, ports

    def forecast_definition(self, config, decoded, expected_parent, materializations):
        from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import NativeSegmentedRunner
        base = NativeSegmentedRunner.forecast_definition(self, config, decoded, expected_parent, materializations)
        return step.controlled_forecast_definition(*control_operands(decoded)[:3], decoded["native-config"], base,
            additional_materialization_ids=materializations)


def prepare_native_work(*, runner, context, expected_parent):
    runner.require_retained_work_contract()
    config, _, _ = load_inputs(context, runner.manifest)
    _, _, _, definition = runner.project_forecast_scope(context, expected_parent)
    return PreparedNativeWork(expected_parent, (c.UNIT,), native_effect_slot_ids(config), (definition,),
        (NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,)),))


def validate_lossless_evidence(source, request, *, size):
    from empirical_lawhood.infrastructure.artifact_validation import validate_jsonl_stream
    return validate_jsonl_stream(source, request, size=size, record_version=stream.LosslessEvidenceLine.VERSION)


def validate_lossless_raw(source, request, *, size):
    from empirical_lawhood.infrastructure.artifact_validation import validate_jsonl_stream
    return validate_jsonl_stream(source, request, size=size, record_version=records.RawSegmentStreamLine.VERSION)


LOSSLESS_STORAGE_CODECS = (
    RecursiveStorageCodec("battery.segments.lossless-evidence-stream", stream.LosslessEvidenceLine.SCHEMA,
        stream.LosslessEvidenceLine.VERSION, ArtifactProfile.JSONL_CHUNKS, STREAM_MEDIA, ".jsonl", validate_lossless_evidence),
    RecursiveStorageCodec("battery.segments.lossless-raw-stream", records.RawSegmentStreamLine.SCHEMA,
        records.RawSegmentStreamLine.VERSION, ArtifactProfile.JSONL_CHUNKS, STREAM_MEDIA, ".jsonl", validate_lossless_raw),
)


def scientific_operand_sha256s(config):
    return tuple(sorted({row.object_fingerprint for row in config.operands}))


def scientific_unit_ids(config):
    return (c.UNIT,)


def operation_declaration():
    old_manifest = next(row for row in original.operation_manifests() if row.capability_key == original.NAMESPACE + ".forecast")
    return RecursiveOperationDeclaration(CAPABILITY_KEY, "1.0.0", "controlled-full54-exact-policy-lossless-custody-v1",
        CapabilityKind.SIMULATOR, ControlledForecastConfig, ScientificStage.ACQUIRE,
        tuple(RecursivePortContract(role, kind.SCHEMA, original.MEDIA, None) for role, kind in sorted(ROLE_TYPES.items())),
        (OutputTemplate("evidence", evidence.SegmentedNativeEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, original.MEDIA, ".json"),
         OutputTemplate("forecast-step-evidence", step.ForecastStepEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, original.MEDIA, ".json"),
         OutputTemplate("segments", stream.LosslessEvidenceLine.SCHEMA, ArtifactProfile.JSONL_CHUNKS, STREAM_MEDIA, ".jsonl")),
        old_manifest.permissions, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, original.BUDGET,
        ("complete-role-bound-original-operands", "old-unknown-hold-retained", "same-prepared-native-lifecycle"),
        ControlledForecastWorker,
        {kind.SCHEMA: kind for kind in (ControlledForecastConfig, evidence.SegmentedNativeEvidence, step.ForecastStepEvidence,
            records.RawSegmentIndex, records.FullSegmentIndex)},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, native_effect_slot_ids=native_effect_slot_ids,
            scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True, native_work_preparer=prepare_native_work),
        storage_codecs=LOSSLESS_STORAGE_CODECS,
        input_record_types=tuple(sorted(set(ROLE_TYPES.values()), key=lambda kind: (kind.SCHEMA, kind.VERSION))))
