# SPDX-License-Identifier: MPL-2.0
"""Current prefix declaration and adapter over the original native lifecycle.

This component is not installed in the public extension aggregates yet. The
complete selected programme/root/custody composition remains required before
public protected entry. Local declarations and returned records grant no issue,
execution, source qualification or outcome access.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.parameter_native import execute_parameter_native_work
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import (
    ScheduledCheckpoint, ScheduledNativeEvidence, identity as scheduled_identity,
)
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from .experiment_specification import MatrixResponseErrorSpecification
from .protected_prefix_preparation import (
    _prefix_native_work, decode_protected_e3_prefix_inputs, prepare_protected_e3_prefix_work,
)
from .protected_prefix_records import ProtectedE3PrefixHistory
from .protected_source_records import (
    NAMESPACE, ProtectedE3NativeSourceManifest, ProtectedE3SourceConfig, ProtectedE3SourcePhase, identity,
)
from .protected_prefix_workers import PURE_PREFIX_PHASES, ProtectedE3PrefixPureRunner, prefix_worker_phase

from .protected_input_custody import protected_e3_source_operands as _source_operands

BUDGET = ResourceBudget(1, None, 0, None, None, None)
PREFIX_INPUTS = (("coordinate", MatrixParameterCoordinate), ("manifest", ProtectedE3NativeSourceManifest),
    ("provenance", NumericalProducingProvenance), ("source", ScheduledSource),
    ("specification", MatrixResponseErrorSpecification), ("streams", MatrixHistorySeed))


def _prefix_config(config):
    _phase_config(config, ProtectedE3SourcePhase.PREFIX)


def _phase_config(config, phase):
    if type(config) is not ProtectedE3SourceConfig or config.phase is not phase:
        raise ValueError("protected E3 prefix declaration requires its exact current phase")
    config.__post_init__()


def scientific_units(config):
    _prefix_config(config)
    return (config.source.root.root.independent_group_id,)


def native_slots(config):
    _prefix_config(config)
    return ("prefix." + config.source.root_id,)


def scientific_operands(config):
    _prefix_config(config)
    return _source_operands(config)




def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not ProtectedE3PrefixRunner:
        raise TypeError("protected E3 prefix preparation requires its declaration-owned runner")
    return prepare_protected_e3_prefix_work(context=context, expected_parent=expected_parent, capability=runner.manifest)


def prefix_declaration():
    """One cold owner for ports, outputs, codecs, effects and preparation."""
    codecs = {kind.SCHEMA: kind for kind in (ProtectedE3SourceConfig, ProtectedE3PrefixHistory, ScheduledCheckpoint,
        *(kind for _, kind in PREFIX_INPUTS))}
    return RecursiveOperationDeclaration(NAMESPACE + ".prefix", "1.0.0",
        NAMESPACE + ".prefix.original-parameter-native-controller.v1", CapabilityKind.SIMULATOR,
        ProtectedE3SourceConfig, ScientificStage.ACQUIRE,
        tuple(RecursivePortContract(name, kind.SCHEMA, "application/json", None,
            minimum_count=4 if name == "streams" else 1, maximum_count=4 if name == "streams" else 1)
            for name, kind in PREFIX_INPUTS),
        (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),
            OutputTemplate("checkpoint", ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("product", ProtectedE3PrefixHistory.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")),
        tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_FROZEN_MODELS))),
        EvidenceCeiling.RESPONSE, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BUDGET,
        ("compact-direct-source-and-four-stream-inputs", "ordinary-array-alias-and-exact-native-checkpoint",
            "original-parameter-controller-and-known-recovery"),
        lambda: ProtectedE3PrefixRunner(), codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=scientific_units,
            scientific_operand_sha256s=scientific_operands, native_effect_slot_ids=native_slots),
        execution_properties=RecursiveExecutionProperties(native_effect=True, native_work_preparer=prepare_native_work,
            complete_unit_census=True), provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS)


def prefix_pure_declaration(phase):
    """Derive each existing numerical reader from its owning phase contract."""
    selected = prefix_worker_phase(phase)
    codecs = {kind.SCHEMA: kind for kind in (ProtectedE3SourceConfig, selected.product_type,
        *(kind for _, kind, _ in selected.records))}
    inputs = tuple(sorted((
        *(RecursivePortContract(name, kind.SCHEMA, "application/json", None)
            for name, kind, _ in selected.records),
        *(RecursivePortContract(name, MATRIX_ARRAY_SCHEMA, "application/x-npz", None)
            for name, _ in selected.arrays)), key=lambda port: port.port_id))
    outputs = (OutputTemplate("product", selected.product_type.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", ".json"),)
    if selected.array_output:
        outputs = (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
            "application/x-npz", ".npz"), *outputs)

    def units(config):
        _phase_config(config, phase)
        return (config.source.root.root.independent_group_id,)

    def operands(config):
        _phase_config(config, phase)
        return _source_operands(config)

    return RecursiveOperationDeclaration(NAMESPACE + "." + phase.value, "1.0.0",
        NAMESPACE + "." + phase.value + ".original-prefix-numerical-owner.v1",
        CapabilityKind.FALSIFIER if selected.stage is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
        ProtectedE3SourceConfig, selected.stage, inputs, outputs,
        tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_FROZEN_MODELS))),
        EvidenceCeiling.RESPONSE, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BUDGET,
        ("actual-prepared-input-and-producer-port-joins", "complete-current-prefix-numerical-reads",
            "original-scientific-equations-and-nonuse"),
        lambda: ProtectedE3PrefixPureRunner(phase, manifest=prefix_pure_declaration(phase).manifest()), codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=units, scientific_operand_sha256s=operands),
        execution_properties=RecursiveExecutionProperties(),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)


def prefix_declarations():
    """Current native prefix and four PURE consumers; not globally installed."""
    return (prefix_declaration(), *(prefix_pure_declaration(row.phase) for row in PURE_PREFIX_PHASES))


class ProtectedE3PrefixRunner:
    def __init__(self):
        self.manifest = prefix_declaration().manifest()

    def execute(self, context):
        try:
            raise ValueError("protected E3 prefix requires the existing issued native-subwork authorization")
        finally:
            for port in context.input_ports:
                port.close()

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            operands = decode_protected_e3_prefix_inputs(context, self.manifest)
            source = operands.source
            work = _prefix_native_work(operands, context=context, expected_parent=native_subwork.parent_contact)
            raw, arrays, checkpoint, definition, completed = execute_parameter_native_work(
                source, work, native_subwork, prefix_only=True, start=0, stop=source.policy.cutoff_tick, progress=progress)
            by_schema = {port.payload_schema: port for port in context.output_ports}
            output = by_schema[MATRIX_ARRAY_SCHEMA]
            _, operand = science._array_product(source, arrays, role="PREFIX", artifact_id=output.logical_artifact_id,
                producers=(scheduled_identity(source), coordinate_identity(source.coordinate)), raw=raw)
            product = ProtectedE3PrefixHistory("history." + NAMESPACE + "." + source.root_id,
                scheduled_identity(source), identity(operands.config), operand, checkpoint,
                ScheduledNativeEvidence(definition, completed.completion, completed.receipt))
            product.validate_source(operands.config, operands.manifest, specification=operands.specification)
            payloads = {MATRIX_ARRAY_SCHEMA: raw, ScheduledCheckpoint.SCHEMA: checkpoint.canonical_bytes(),
                ProtectedE3PrefixHistory.SCHEMA: product.canonical_bytes()}
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, payloads[port.payload_schema])
                for port in context.output_ports),
                (ReceiptCheck("protected-e3-prefix-original-native-and-ordinary-custody", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
