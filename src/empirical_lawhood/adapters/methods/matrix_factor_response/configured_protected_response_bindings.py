# SPDX-License-Identifier: MPL-2.0
"""Uninstalled current physical, paired-native and independent-score lifecycle.

The owning API must authenticate original publications and the complete
scientific root before composing these declarations. Workers retain exact
prepared input/receipt/array joins and use the original numerical/native owners.
No declaration, prepared work or consistency check grants scientific authority.
"""

from dataclasses import dataclass
import inspect
from functools import partial
import sys

import numpy as np

from empirical_lawhood.adapters.methods.matrix_dataset_readers import retained_array_mappings
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science as prefix_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledNativeEvidence
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_bindings import execute_paired_response_native_work
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import array_product
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore, branch_census
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from .configured_protected_methods import ConfiguredProtectedE3Calibration, ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3PairedOutcome
from .configured_protected_response_preparation import PUBLIC_RECORDS, RESPONSE_RECORDS, decode_response_inputs, prepare_response_work, response_native_work
from .configured_protected_response_records import ConfiguredProtectedE3NativeResponse, ConfiguredProtectedE3PhysicalForecast, ConfiguredProtectedE3PhysicalForecastConfig, ConfiguredProtectedE3ResponseConfig, _object
from .configured_protected_source_records import NAMESPACE, identity
from .configured_protected_statistical_bindings import statistical_task_id
from . import configured_protected_response_science as science

BUDGET = ResourceBudget(1, None, 0, None, None, None)
LIMITS = dict(maximum_chunk_bytes=65536, maximum_slice_bytes=1048576)
OPERATIONS = ("physical-forecast", "responses", "response-score")


def _config(config, operation, continued=False):
    from .configured_continued_response import ConfiguredE3ContinuedResponseConfig
    kind = ConfiguredProtectedE3PhysicalForecastConfig if operation == "physical-forecast" else (
        ConfiguredE3ContinuedResponseConfig if continued else ConfiguredProtectedE3ResponseConfig)
    if type(config) is not kind or operation != 'physical-forecast' and config.operation != operation:
        raise TypeError("protected E3 response declaration changes its exact current configuration")
    config.__post_init__()


def _global_hook(value):
    if type(value) is partial:
        _global_hook(value.func)
        canonical_json_bytes((value.args, value.keywords))
    elif (not inspect.isfunction(value) or value.__qualname__ != value.__name__
            or getattr(sys.modules.get(value.__module__), value.__name__, None) is not value):
        raise TypeError("protected E3 response composition requires actual module-global API hooks")


@dataclass(frozen=True, slots=True)
class _ScienceHooks:
    operation: str
    continued: bool = False

    def units(self, config):
        _config(config, self.operation, self.continued)
        # A seedless physical configuration deliberately contains no hidden
        # source/allocation; its root is authenticated by the supplied root hook.
        return () if self.operation == "physical-forecast" else (config.source.root.root.independent_group_id,)

    def operands(self, config):
        _config(config, self.operation, self.continued)
        refs = (config.specification, config.protocol, config.numerical_profile)
        if self.operation != "physical-forecast":
            refs += (config.source.identity, config.source_manifest, config.response_selection)
        if self.continued:
            refs += (config.continuation,)
        return tuple(sorted({row.object_fingerprint for row in refs}))

    def slots(self, config):
        _config(config, self.operation, self.continued)
        return ("responses." + config.source.root_id,)


def _records(operation, continued=False):
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
    if operation == "physical-forecast":
        return PUBLIC_RECORDS
    result = (*RESPONSE_RECORDS, ("panels", ScheduledResponsePanel), ("streams", MatrixHistorySeed),
        ("frozen", ConfiguredProtectedE3FrozenProducts), ("calibration", ConfiguredProtectedE3Calibration), ("model-freeze", ConfiguredProtectedE3FrozenProducts))
    config, product = ConfiguredProtectedE3ResponseConfig, ConfiguredProtectedE3NativeResponse
    if continued:
        from .configured_continued_response import ConfiguredE3ContinuedResponseConfig, ConfiguredE3ContinuedNativeResponse
        from .configured_retained_execution import ConfiguredE3RetainedExecution
        config, product = ConfiguredE3ContinuedResponseConfig, ConfiguredE3ContinuedNativeResponse
        result += (('retention', ConfiguredE3RetainedExecution),)
    return (*result, ("native-config", config), ("responses", product)) if operation == "response-score" else result


def _arrays(operation):
    return (("causal-arrays", "templates-arrays") if operation == "physical-forecast" else
        ("prefix-arrays", "physical-arrays") if operation == "responses" else
        ("prefix-arrays", "causal-arrays", "templates-arrays", "physical-arrays", "response-arrays"))


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not ConfiguredProtectedE3ResponseRunner or runner.operation != "responses":
        raise TypeError("protected E3 paired preparation requires its exact declaration-owned native runner")
    return prepare_response_work(context=context, expected_parent=expected_parent, capability=runner.manifest,
        statistical_task_id=statistical_task_id)


@dataclass(frozen=True, slots=True)
class _RunnerFactory:
    operation: str
    publication_requirement: RegisteredPublicationRequirement
    scientific_root_validator: object
    continued: bool = False

    def __call__(self):
        declaration = _declaration(self.operation, self.publication_requirement, self.scientific_root_validator, self.continued)
        return ConfiguredProtectedE3ResponseRunner(self.operation, declaration.manifest())


def _declaration(operation, publication_requirement, scientific_root_validator, continued=False):
    config = ConfiguredProtectedE3PhysicalForecastConfig if operation == "physical-forecast" else ConfiguredProtectedE3ResponseConfig
    records = _records(operation, continued)
    product = ConfiguredProtectedE3PhysicalForecast if operation == "physical-forecast" else ConfiguredProtectedE3NativeResponse
    if continued:
        from .configured_continued_response import ConfiguredE3ContinuedResponseConfig, ConfiguredE3ContinuedNativeResponse
        if operation == 'physical-forecast':
            raise ValueError('continued E3 retains its original physical forecast')
        config, product = ConfiguredE3ContinuedResponseConfig, ConfiguredE3ContinuedNativeResponse
    codecs = {kind.SCHEMA: kind for kind in (config, product, ScheduledResponseScore, ConfiguredProtectedE3PairedOutcome,
        *(kind for _, kind in records))}
    inputs = []
    if continued:
        from .configured_unfinished_execution import ConfiguredE3UnfinishedExecution, unfinished_port
        inputs.append(unfinished_port())
        codecs[ConfiguredE3UnfinishedExecution.SCHEMA] = ConfiguredE3UnfinishedExecution
        from .configured_closeout_execution import ConfiguredE3ClosedExecution, closeout_port
        inputs.append(closeout_port())
        codecs[ConfiguredE3ClosedExecution.SCHEMA] = ConfiguredE3ClosedExecution
    for name, kind in records:
        count = 2 if name == "panels" else 8 if name == "streams" else 1
        inputs.append(RecursivePortContract(name, kind.SCHEMA, "application/json", None,
            minimum_count=0 if name in ("calibration", "model-freeze") else count, maximum_count=count))
    inputs.extend(RecursivePortContract(name, MATRIX_ARRAY_SCHEMA, "application/x-npz", MAXIMUM_MATRIX_ARRAY_BYTES)
        for name in _arrays(operation))
    outputs = ((OutputTemplate("score", ScheduledResponseScore.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
        OutputTemplate("outcome", ConfiguredProtectedE3PairedOutcome.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        if operation == "response-score" else
        (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),
            OutputTemplate("product", product.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")))
    stage = ScientificStage.FREEZE if operation == "physical-forecast" else ScientificStage.ACQUIRE if operation == "responses" else ScientificStage.FALSIFY
    hooks = _ScienceHooks(operation, continued)
    permissions = [CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        CapabilityPermission.READ_FROZEN_MODELS, CapabilityPermission.READ_DEVELOPMENT]
    if operation != "physical-forecast":
        permissions.append(CapabilityPermission.READ_SEALED_OUTCOMES)
    key = NAMESPACE + '.' + ('continued-' if continued else '') + operation
    return RecursiveOperationDeclaration(key, "1.0.0", key + ".current-original-response-owner.v1",
        CapabilityKind.EXPERIMENT_DESIGNER if operation == "physical-forecast" else CapabilityKind.SIMULATOR if operation == "responses" else CapabilityKind.FALSIFIER,
        config, stage, tuple(sorted(inputs, key=lambda row: row.port_id)), tuple(sorted(outputs, key=lambda row: row.output_id)), tuple(sorted(permissions)), EvidenceCeiling.RESPONSE,
        OutcomeAccess.OUTCOME_BLIND if operation == "physical-forecast" else OutcomeAccess.EVALUATION_SEALED,
        VisibilityCeiling.PROSPECTIVE, BUDGET, tuple(sorted(("actual-current-producer-and-ordinary-alias-joins",
            "original-seedless-physical-and-complete-paired-native-owner", "single-retained-dataset-session-and-negative-preservation"))),
        _RunnerFactory(operation, publication_requirement, scientific_root_validator, continued), codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=hooks.units, scientific_operand_sha256s=hooks.operands,
            native_effect_slot_ids=hooks.slots if operation == "responses" else None, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=operation == "responses", complete_unit_census=operation == "responses",
            native_work_preparer=prepare_native_work if operation == "responses" else None,
            barrier=BarrierKind.FREEZE if stage is ScientificStage.FREEZE else BarrierKind.NONE),
        publication_requirements=(publication_requirement,), provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)


def response_declarations(*, publication_requirement, scientific_root_validator, continued=False):
    """Require owning authentication before these local components can install."""
    if type(publication_requirement) is not RegisteredPublicationRequirement:
        raise TypeError("protected E3 response needs its exact registered original-publication requirement")
    publication_requirement.__post_init__()
    _global_hook(publication_requirement.validate)
    _global_hook(scientific_root_validator)
    operations = ('responses', 'response-score') if continued else OPERATIONS
    return tuple(_declaration(operation, publication_requirement, scientific_root_validator, continued) for operation in operations)


class ConfiguredProtectedE3ResponseRunner:
    def __init__(self, operation, manifest):
        if operation not in OPERATIONS:
            raise ValueError("protected E3 response worker needs an exact current operation")
        self.operation, self.manifest = operation, manifest

    def execute(self, context):
        from .protected_pure_execution import execute_response_pure
        return execute_response_pure(self, context, decode_inputs=decode_response_inputs,
            statistical_task_id=statistical_task_id, array_roles=_arrays, science=science, limits=LIMITS, make_result=_result)

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        if type(getattr(context, "prepared_invocation", None)) is not PreparedInvocationContract:
            raise PermissionError("configured response requires its actual complete prepared native invocation")
        context.prepared_invocation.validate_context(context)
        try:
            if self.operation != "responses":
                raise ValueError("protected E3 PURE response operation cannot enter native effects")
            operands = decode_response_inputs(context, capability=self.manifest, operation=self.operation, statistical_task_id=statistical_task_id)
            records, source = operands.records, operands.source
            work = response_native_work(operands, context=context, expected_parent=native_subwork.parent_contact)
            native, raw = (), None
            if records["physical"].disposition != "AVAILABLE" or records["causal"].disposition != "AVAILABLE":
                arrays = {"unentered_branches": np.arange(48, dtype="<i8")}
                disposition = ("NO_ORIGIN" if records["causal"].disposition == "NO_ORIGIN" else
                    "INSTRUMENT_UNRESOLVED" if records["physical"].disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE")
            else:
                with retained_array_mappings((records["history"].arrays, records["physical"].arrays),
                        lambda artifact: operands.ports["prefix-arrays" if artifact == records["history"].arrays.array_artifact else "physical-arrays"], **LIMITS) as mappings:
                    prefix, frozen = mappings
                    prefix_science.validate_prefix_arrays(source, prefix)
                    raw, arrays, definition, completed = execute_paired_response_native_work(source, work, native_subwork,
                        protocol=records["protocol"], panels=records["panels"], history=records["history"], prefix=prefix,
                        frozen=frozen, selection=identity(records["selection"]), progress=progress)
                native, disposition = (ScheduledNativeEvidence(definition, completed.completion, completed.receipt),), "COMPLETED"
            array_port = next(port for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, operand = array_product(records["protocol"], arrays, role="RESPONSES", artifact_id=array_port.logical_artifact_id,
                producers=(operands.config.source.identity, identity(records["selection"]), _object(records["physical"]),
                    identity(records["error"]), identity(records["numerical-profile"])),
                access=operands.outcome_access, visibility=operands.visibility, **({"raw": raw} if raw is not None else {}))
            product_kind, continuation = ConfiguredProtectedE3NativeResponse, {}
            if 'retention' in records:
                from .configured_continued_response import ConfiguredE3ContinuedNativeResponse
                product_kind, continuation = ConfiguredE3ContinuedNativeResponse, {'continuation': records['retention'].identity}
            product = product_kind("responses." + context.task_id, _object(operands.config), operands.config.source.identity,
                identity(records["history"]), identity(records["causal"]), _object(records["physical"]), identity(records["error"]),
                _object(records["protocol"]), identity(records["numerical-profile"]), identity(records["selection"]), operand,
                tuple(row[0] for row in branch_census(records["protocol"], records["panels"])), native, disposition,
                () if native else ("complete48-pulse-slots-not-entered-" + disposition.lower(),), **continuation)
            product.validate_source(operands.config, **{key: value for key, value in operands.science_arguments().items() if key != "prefix_config"})
            return _result(context, {"arrays": raw, "product": product.canonical_bytes()})
        finally:
            for port in context.input_ports:
                port.close()


def _result(context, payloads):
    return RunnerResult(tuple(TaskOutputPayload(port.output_id, payloads[port.output_id.rsplit(".", 1)[-1]]) for port in context.output_ports),
        (ReceiptCheck("protected-e3-response-exact-current-custody-and-original-owner", True, ()),))
