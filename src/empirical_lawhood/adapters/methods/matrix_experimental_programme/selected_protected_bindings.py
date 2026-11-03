# SPDX-License-Identifier: MPL-2.0
"""One declaration and lowering owner for selected protected prepared phases."""

from dataclasses import dataclass, replace
from functools import lru_cache

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import _decimal_context_cache
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import SourceAccessDisposition, StudyDraft
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RecursiveScientificRootContext
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from .selected_produced_inputs import inherit_external_inputs, inherit_external_links

from . import preparation_bindings as preparation
from .selected_future import MatrixSelectedFutureConfigV2
from .preparation_records import MatrixPreparationHistory, MatrixPreparationAssessment, MatrixPreparationSource
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_point import MatrixPreparedPublicSource
from .prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedFactorWitness, MatrixPreparedFrameAssessment
from .prepared_response_science import MatrixPreparedResponseReadout
from .science import MatrixFunctionalAssessment
from .selected_future import MatrixSelectedFutureConfig, MatrixSelectedFutureHistory, NAMESPACE, node_id
from .selected_point import MatrixSelectedPointForecast
from .selected_public import MatrixSelectedPointPayload, package_identity
from .selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme, MatrixSelectedProtectedRootConfig, MatrixSelectedPreparedConfig, global_node
from .selected_protected_results import MatrixSelectedProtectedEntrySeal, MatrixSelectedProtectedManifest
from .selected_original_commitments import MatrixSelectedEntryEvidenceV3, MatrixSelectedProtectedRootConfigV3
from .e6_transport_records import MatrixE6EmpiricalTransportAssessment, MatrixE6TransportDecision, MatrixE6TransportManifest
from .selected_e6_transport_config import (ENTRY_TRANSPORT_KEY, MatrixSelectedTransportRootConfig,
    MatrixSelectedTransportPointConfig, MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig)


PHASES = ("entry", "history", "assess", "measure", "frames", "project", "point", "mechanical", "responses", "response-score", "assess-programme")
NATIVE = ("history", "responses")
ENTRY_ORIGINAL_COMMITMENTS_KEY = NAMESPACE + ".entry-original-commitments"
ARRAY_OUTPUTS = ("history", "measure", "project", "mechanical", "responses")
RECORDS = {"entry": MatrixSelectedProtectedEntrySeal, "source": MatrixPreparationSource, "allocation": ScheduledAllocation,
    "history": MatrixPreparationHistory, "numerical": MatrixPreparationAssessment, "witness": MatrixPreparedFactorWitness,
    "frames": MatrixPreparedFrameAssessment, "causal": MatrixPreparedCausalPrefix, "point-design": MatrixSelectedPointPayload,
    "point": MatrixSelectedPointForecast, "mechanical": MatrixPreparedMechanicalForecast, "protocol": ScheduledResponseProtocol,
    "responses": MatrixSelectedFutureHistory, "decision": MatrixE6TransportDecision}
OUTPUTS = {"entry": MatrixSelectedProtectedEntrySeal, "history": MatrixPreparationHistory, "assess": MatrixPreparationAssessment,
    "measure": MatrixPreparedFactorWitness, "frames": MatrixPreparedFrameAssessment, "project": MatrixPreparedCausalPrefix,
    "point": MatrixSelectedPointForecast, "mechanical": MatrixPreparedMechanicalForecast, "responses": MatrixSelectedFutureHistory,
    "response-score": MatrixPreparedResponseReadout}
BASE = ("source", "allocation", "initial-state", "history", "history-arrays", "causal", "point", "mechanical", "mechanical-arrays", "protocol")
INPUTS = {"entry": ("entry-evidence",), "history": ("source", "allocation", "initial-state", "entry"),
    "assess": ("source", "allocation", "initial-state", "history", "history-arrays", "entry"),
    "measure": ("source", "initial-state", "history", "history-arrays", "numerical", "entry"),
    "frames": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "entry"),
    "project": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "frames", "entry"),
    "point": ("point-design", "witness", "diagnostic-arrays", "frames", "causal", "causal-arrays", "entry"),
    "mechanical": ("protocol", "templates", "causal", "causal-arrays", "entry"),
    "responses": (*BASE, "entry"),
    "response-score": (*BASE, "causal-arrays", "templates", "responses", "response-arrays", "entry"),
    "assess-programme": ("entry", "points", "mechanicals", "readouts")}
FINAL_KINDS = {"points": MatrixSelectedPointForecast, "mechanicals": MatrixPreparedMechanicalForecast, "readouts": MatrixPreparedResponseReadout}
TRANSPORT_FINAL_KINDS = {**FINAL_KINDS, "decisions": MatrixE6TransportDecision}
ROOT_CONFIG_TYPES = (MatrixSelectedProtectedRootConfig, MatrixSelectedProtectedRootConfigV3, MatrixSelectedTransportRootConfig)


def config_capability_version(config):
    if type(config) is MatrixSelectedTransportRootConfig:
        return "4.0.0" if config.phase == "entry" else "2.0.0"
    if type(config) is MatrixSelectedTransportFutureConfig:
        return "3.0.0"
    if type(config) in (MatrixSelectedTransportPointConfig, MatrixSelectedTransportScoreConfig):
        return "2.0.0"
    return ("2.0.0" if type(config) in preparation.native_config_types() else
        "3.0.0" if type(config) is MatrixSelectedProtectedRootConfigV3 else "1.0.0")


def is_direct_native_config(config):
    return type(config) in (*preparation.native_config_types(), MatrixSelectedTransportFutureConfig)


def is_transport_config(config):
    return type(config) in (MatrixSelectedTransportRootConfig, MatrixSelectedTransportPointConfig,
        MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig)


def phase_inputs(phase, version="1.0.0"):
    if phase == "responses" and version == "3.0.0":
        return (*INPUTS[phase], "decision", "native-provenance", "native-stream")
    if phase == "response-score" and version == "2.0.0":
        return (*INPUTS[phase], "decision")
    if phase == "assess-programme" and version == "2.0.0":
        return (*INPUTS[phase], "decisions")
    if version == "2.0.0" and phase in NATIVE:
        return (*INPUTS[phase], "native-provenance", "native-stream")
    if phase in NATIVE:
        raise ValueError("selected native phase requires its current direct-input contract")
    return INPUTS[phase]


def phase_of(config):
    if type(config) not in (*ROOT_CONFIG_TYPES, MatrixSelectedPreparedConfig, MatrixSelectedFutureConfig,
            MatrixSelectedTransportPointConfig, MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig,
            preparation.MatrixPreparationOperationConfig, preparation.MatrixPreparationOperationConfigV2, MatrixSelectedFutureConfigV2):
        raise TypeError("selected protected phase requires its exact owning configuration")
    config.__post_init__()
    if config.phase in NATIVE and not is_direct_native_config(config):
        raise ValueError("selected native phase requires its current direct-input contract")
    return config.phase


def capability_key(phase, version):
    if phase == "entry" and version == "4.0.0":
        return ENTRY_TRANSPORT_KEY
    if (phase, version) in (("point", "2.0.0"), ("responses", "3.0.0"),
            ("response-score", "2.0.0"), ("assess-programme", "2.0.0")):
        return NAMESPACE + "." + phase + ".empirical-transport"
    if phase in NATIVE and version == "2.0.0":
        return NAMESPACE + "." + phase + ".direct-inputs"
    if phase == "entry" and version == "3.0.0":
        return ENTRY_ORIGINAL_COMMITMENTS_KEY
    if phase in PHASES and phase not in ("entry", *NATIVE) and version == "1.0.0":
        return NAMESPACE + "." + phase
    raise ValueError("selected protected worker changes its exact installed phase/version")


def task_id(config):
    return config.config_id.removeprefix("config.")


def units(config):
    if type(config) in ROOT_CONFIG_TYPES:
        return tuple(sorted({source.root.root.independent_group_id for _, source in config.programme.sources.source_arms()}))
    if type(config) in (MatrixSelectedPreparedConfig, MatrixSelectedTransportPointConfig):
        return (config.public_source.original.root.independent_group_id,)
    return (config.source.root.root.independent_group_id,)


def digests(config):
    if type(config) in ROOT_CONFIG_TYPES:
        return ((config.programme.fingerprint(), config.transport_policy.fingerprint(), config.transport_calibration.fingerprint())
            if is_transport_config(config) else (config.programme.fingerprint(),))
    if type(config) in (preparation.MatrixPreparationOperationConfig, preparation.MatrixPreparationOperationConfigV2):
        return preparation.operand_digests(config)
    return ((config.programme.object_fingerprint, config.transport_policy.fingerprint(), config.transport_calibration.fingerprint())
        if is_transport_config(config) else (config.programme.object_fingerprint,))


def slots(config):
    return preparation.slots(config) if phase_of(config) == "history" else ("responses." + config.source.source_id,)


def stage(phase):
    if phase in NATIVE:
        return ScientificStage.ACQUIRE
    if phase == "assess-programme":
        return ScientificStage.EVALUATE
    if phase in ("assess", "frames", "response-score"):
        return ScientificStage.FALSIFY
    return ScientificStage.FREEZE if phase in ("entry", "point", "mechanical") else ScientificStage.TRANSFORM


def access(phase):
    return OutcomeAccess.EVALUATOR_REVEAL if phase == "assess-programme" else OutcomeAccess.EVALUATION_SEALED if phase in ("responses", "response-score") else OutcomeAccess.OUTCOME_BLIND


@dataclass(frozen=True, slots=True)
class _Factory:
    phase: str
    version: str = "1.0.0"
    def __call__(self):
        from .selected_protected_workers import SelectedProtectedWorker
        declaration = next(row for row in operation_declarations() if row.capability_key == capability_key(self.phase, self.version) and row.capability_version == self.version)
        return SelectedProtectedWorker(self.phase, declaration.manifest())


def prepare_for_invocation(supplier, runner):
    from functools import partial
    from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
    callback = getattr(supplier, "prepare_selected_matrix", None)
    if not callable(callback):
        raise PermissionError("selected protected task requires actual current issued parent custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner), native_effect=runner.phase in NATIVE)


def prepare_native_work(*, runner, context, expected_parent):
    return runner.prepare_native_work(context, expected_parent=expected_parent)


def config_input_parents(config,all_config_records):
    from .selected_prepared_parent_projection import prepared_config_parents
    import sys
    return prepared_config_parents(config,all_config_records,owner=sys.modules[__name__],
        root_types=(MatrixSelectedProtectedRootConfigV3,MatrixSelectedTransportRootConfig),root_phase="entry")


@lru_cache(maxsize=1)
def operation_declarations():
    from .selected_entry import MatrixSelectedEntryEvidence
    record_types = {**RECORDS, "entry-evidence": MatrixSelectedEntryEvidence}
    codecs = {kind.SCHEMA: kind for kind in (*record_types.values(), *FINAL_KINDS.values(), *OUTPUTS.values(),
        preparation.MatrixPreparationOperationConfig, MatrixSelectedProtectedRootConfig, MatrixSelectedPreparedConfig,
        MatrixSelectedFutureConfig, MatrixSelectedProtectedManifest, MatrixFunctionalAssessment, ScientificAdjudicationRecord)}
    declarations = []
    for phase in PHASES:
        inputs = []
        for name in INPUTS[phase]:
            kind = MatrixSelectedEntryEvidenceV3 if phase == "entry" else FINAL_KINDS.get(name, record_types.get(name))
            inputs.append(RecursivePortContract(name, MATRIX_ARRAY_SCHEMA if kind is None else kind.SCHEMA,
                "application/x-npz" if kind is None else "application/json", MAXIMUM_MATRIX_ARRAY_BYTES if kind is None else None,
                minimum_count=1, maximum_count=None if name in FINAL_KINDS else 1))
        outputs = (OutputTemplate("product", OUTPUTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),) if phase != "assess-programme" else (
            OutputTemplate("manifest", MatrixSelectedProtectedManifest.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("product", MatrixFunctionalAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("adjudication", ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        if phase in ARRAY_OUTPUTS:
            outputs += (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),)
        permissions = [CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS]
        if access(phase) in (OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.EVALUATOR_REVEAL):
            permissions.append(CapabilityPermission.READ_SEALED_OUTCOMES)
        if phase == "assess-programme":
            permissions.append(CapabilityPermission.REVEAL_OUTCOMES)
        config = MatrixSelectedProtectedRootConfigV3 if phase == "entry" else MatrixSelectedProtectedRootConfig if phase == "assess-programme" else preparation.MatrixPreparationOperationConfig if phase in ("history", "assess") else MatrixSelectedFutureConfig if phase in ("responses", "response-score") else MatrixSelectedPreparedConfig
        version = "3.0.0" if phase == "entry" else "1.0.0"
        implementation = NAMESPACE + (".entry.original-commitments.v3" if phase == "entry" else "." + phase + ".original-native-selected-products.v1")
        selected_codecs = {**codecs, MatrixSelectedEntryEvidenceV3.SCHEMA: MatrixSelectedEntryEvidenceV3,
            MatrixSelectedProtectedRootConfigV3.SCHEMA: MatrixSelectedProtectedRootConfigV3} if phase == "entry" else codecs
        declarations.append(RecursiveOperationDeclaration(NAMESPACE + "." + phase if phase in NATIVE else capability_key(phase, version), version, implementation,
            CapabilityKind.EVALUATOR if phase == "assess-programme" else CapabilityKind.SIMULATOR if phase in NATIVE else CapabilityKind.FALSIFIER if stage(phase) is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
            config, stage(phase), tuple(sorted(inputs, key=lambda row: row.port_id)), tuple(sorted(outputs, key=lambda row: row.output_id)),
            tuple(sorted(permissions)), EvidenceCeiling.RESPONSE, access(phase), VisibilityCeiling.OUTCOME_VISIBLE if phase == "assess-programme" else VisibilityCeiling.PROSPECTIVE,
            preparation.BUDGET, ("actual-original-protected-source-custody", "complete-matched-root-native-and-reducer-census", "selected-points-before-paired-futures"),
            _Factory(phase, version), selected_codecs, scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=units, scientific_operand_sha256s=digests,
                native_effect_slot_ids=slots if phase in NATIVE else None, scientific_root_validator=scientific_root_validator,
                adjudication_output_id="adjudication" if phase == "assess-programme" else None),
            execution_properties=RecursiveExecutionProperties(native_effect=phase in NATIVE, complete_unit_census=phase in NATIVE,
                native_work_preparer=prepare_native_work if phase in NATIVE else None, runner_preparation_factory=prepare_for_invocation,
                barrier=BarrierKind.REVEAL if phase == "assess-programme" else BarrierKind.FREEZE if stage(phase) is ScientificStage.FREEZE else BarrierKind.NONE),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS))
    for index, base in enumerate(declarations):
        if base.capability_version == "1.0.0" and base.capability_key.endswith((".history", ".responses")):
            phase = "history" if base.capability_key.endswith(".history") else "responses"
            config_type = preparation.MatrixPreparationOperationConfigV2 if phase == "history" else MatrixSelectedFutureConfigV2
            factory = _Factory(phase, "2.0.0")
            declarations[index] = preparation.direct_native_declaration(base, config_type=config_type,
                runner_factory=factory)
    from . import e6_transport_records
    transport_codecs = {kind.SCHEMA: kind for kind in vars(e6_transport_records).values()
        if isinstance(kind, type) and hasattr(kind, "SCHEMA") and kind.__module__ == e6_transport_records.__name__}
    transport_codecs.update({kind.SCHEMA: kind for kind in (MatrixSelectedTransportRootConfig,
        MatrixSelectedTransportPointConfig, MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig)})
    versions = (("entry", "4.0.0", MatrixSelectedTransportRootConfig),
        ("point", "2.0.0", MatrixSelectedTransportPointConfig),
        ("responses", "3.0.0", MatrixSelectedTransportFutureConfig),
        ("response-score", "2.0.0", MatrixSelectedTransportScoreConfig),
        ("assess-programme", "2.0.0", MatrixSelectedTransportRootConfig))
    for phase, version, config_type in versions:
        base_version = "3.0.0" if phase == "entry" else "2.0.0" if phase == "responses" else "1.0.0"
        base = next(row for row in declarations if (row.capability_key, row.capability_version) ==
            (capability_key(phase, base_version), base_version))
        inputs, outputs = list(base.input_ports), list(base.outputs)
        if phase in ("responses", "response-score"):
            inputs.append(RecursivePortContract("decision", MatrixE6TransportDecision.SCHEMA, "application/json", None))
        elif phase == "assess-programme":
            inputs.append(RecursivePortContract("decisions", MatrixE6TransportDecision.SCHEMA, "application/json", None,
                minimum_count=1, maximum_count=None))
            outputs = [replace(row, payload_schema=MatrixE6EmpiricalTransportAssessment.SCHEMA) if row.output_id == "product"
                else replace(row, payload_schema=MatrixE6TransportManifest.SCHEMA) if row.output_id == "manifest" else row for row in outputs]
        elif phase == "point":
            outputs.append(OutputTemplate("decision", MatrixE6TransportDecision.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        declarations.append(replace(base, capability_key=capability_key(phase, version), capability_version=version,
            implementation_id=NAMESPACE + "." + phase + ".empirical-transport.v" + version.split(".")[0],
            config_record_type=config_type, input_ports=tuple(sorted(inputs, key=lambda row: row.port_id)),
            outputs=tuple(sorted(outputs, key=lambda row: row.output_id)), runner_factory=_Factory(phase, version),
            record_codecs={**base.record_codecs, **transport_codecs}))
    return tuple(replace(value,config_input_parents=config_input_parents) for value in
        sorted(declarations,key=lambda row:(row.capability_key,row.capability_version)))


@_decimal_context_cache
def contracts(programme, evidence_pin, evidence_size, *, transport_policy=None, transport_calibration=None, produced_input_parents=()):
    if type(programme) is MatrixSelectedProtectedProgramme:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    if type(programme) is not MatrixSelectedPublicProgramme:
        raise TypeError("selected protected graph requires its actual complete programme")
    programme.__post_init__()
    if evidence_pin.object_schema != MatrixSelectedEntryEvidenceV3.SCHEMA:
        raise ValueError("selected protected graph requires current commitment-bearing entry evidence")
    transport = transport_policy is not None or transport_calibration is not None
    if transport:
        from .e6_transport_science import validate_e6_transport_scope, validate_e6_public_calibration_projection
        validate_e6_transport_scope(transport_policy, programme)
        validate_e6_public_calibration_projection(transport_calibration, transport_policy, programme.point_design.package)
        if evidence_pin.object_schema != MatrixSelectedEntryEvidenceV3.SCHEMA:
            raise ValueError("expanded E6 requires actual committed original evidence and direct native operands")
    configs, external, records, arrays, links = {}, {}, {}, {}, []
    def add(name, value, object_id):
        raw = value.canonical_bytes()
        row = RecursiveExternalInput(name, object_id, value.SCHEMA, "application/json", len(raw),
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, value.fingerprint(), "SOURCE")
        if external.setdefault(name, row) != row or records.setdefault(name, value) != value:
            raise ValueError("selected graph aliases distinct original scientific records")
        return name
    def array(name, artifact):
        row = RecursiveExternalInput(name, artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes,
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, artifact.sha256, "SOURCE")
        if external.setdefault(name, row) != row or arrays.setdefault(name, artifact) != artifact:
            raise ValueError("selected graph aliases distinct original physical files")
        return name
    def edge(node, name, *, external_id=None, producer=None, output="product"):
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=external_id,
            producer_node_id=producer, producer_output_id=output if producer is not None else None, scientific_role="SOURCE" if producer is None else "HISTORY"))
    for phase in ("entry", "assess-programme"):
        node = global_node(programme, phase)
        if transport:
            configs[node] = MatrixSelectedTransportRootConfig("config." + node, programme, phase,
                transport_policy, transport_calibration, produced_input_parents, evidence_pin if phase == "entry" else None,
                evidence_size if phase == "entry" else None)
            continue
        kind = MatrixSelectedProtectedRootConfigV3 if phase == "entry" else MatrixSelectedProtectedRootConfig
        configs[node] = kind("config." + node, programme, phase,
            evidence_pin if phase == "entry" else None, evidence_size if phase == "entry" else None,
            **({"produced_input_parents": produced_input_parents} if kind is MatrixSelectedProtectedRootConfigV3 else {}))
    entry, final = (global_node(programme, phase) for phase in ("entry", "assess-programme"))
    evidence_id = "external.selected-entry-evidence." + evidence_pin.object_fingerprint
    external[evidence_id] = RecursiveExternalInput(evidence_id, evidence_pin.object_id, evidence_pin.object_schema, "application/json",
        evidence_size, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, evidence_pin.object_fingerprint, "SOURCE")
    edge(entry, "entry-evidence", external_id=evidence_id)
    design = add("external.selected-point-design." + programme.point_design.fingerprint(), programme.point_design, programme.point_design.record_id)
    allocation = programme.sources.closure.reservation.allocation
    allocation_id = add("external.selected-allocation." + allocation.fingerprint(), allocation, allocation.allocation_id)
    templates = array("external.selected-templates." + programme.assay.template_artifact.sha256, programme.assay.template_artifact)
    for _, source in programme.sources.source_arms():
        public = MatrixPreparedPublicSource.from_source(source)
        protocol = programme.protocol(source)
        source_id = add("external.selected-source." + source.source_id, source, source.source_id)
        protocol_id = add("external.selected-protocol." + protocol.fingerprint(), protocol, protocol.protocol_id)
        initial = array("external.selected-initial." + source.initial.array_artifact.fingerprint(), source.initial.array_artifact)
        nodes = {phase: preparation.node_id(source, phase) if phase in ("history", "assess") else node_id(source, phase) for phase in PHASES if phase not in ("entry", "assess-programme")}
        for phase, node in nodes.items():
            configs[node] = ((preparation.MatrixPreparationOperationConfigV2 if phase == "history" else preparation.MatrixPreparationOperationConfig)("config." + node, phase, source, len(allocation.canonical_bytes())) if phase in ("history", "assess") else
                (MatrixSelectedFutureConfigV2 if phase == "responses" else MatrixSelectedFutureConfig)("config." + node, programme.identity, source, protocol, dict(programme.panels)[source.root.root.independent_group_id],
                    programme.point_design.identity, package_identity(programme.point_design.package), phase) if phase in ("responses", "response-score") else
                MatrixSelectedPreparedConfig("config." + node, programme.identity, public, phase))
            if transport and phase in ("responses", "response-score"):
                kind = MatrixSelectedTransportFutureConfig if phase == "responses" else MatrixSelectedTransportScoreConfig
                configs[node] = kind("config." + node, programme.identity, source, protocol,
                    dict(programme.panels)[source.root.root.independent_group_id], programme.point_design.identity,
                    package_identity(programme.point_design.package), phase, transport_policy, transport_calibration)
            elif transport and phase == "point":
                configs[node] = MatrixSelectedTransportPointConfig("config." + node, programme.identity, public, phase,
                    transport_policy, transport_calibration)
            incoming = {"source": source_id, "allocation": allocation_id, "initial-state": initial,
                "point-design": design, "protocol": protocol_id, "templates": templates}
            produced = {"entry": (entry, "product"), "history": (nodes["history"], "product"), "history-arrays": (nodes["history"], "arrays"),
                "numerical": (nodes["assess"], "product"), "witness": (nodes["measure"], "product"), "diagnostic-arrays": (nodes["measure"], "arrays"),
                "frames": (nodes["frames"], "product"), "causal": (nodes["project"], "product"), "causal-arrays": (nodes["project"], "arrays"),
                "point": (nodes["point"], "product"), "decision": (nodes["point"], "decision"), "mechanical": (nodes["mechanical"], "product"), "mechanical-arrays": (nodes["mechanical"], "arrays"),
                "responses": (nodes["responses"], "product"), "response-arrays": (nodes["responses"], "arrays")}
            native_names = ()
            if phase in NATIVE:
                native_names = tuple(name for name, _, _ in preparation.native_input_records(source,
                    panels=dict(programme.panels)[source.root.root.independent_group_id] if phase == "responses" else None))
                for name, pin, value in preparation.native_input_records(source,
                        panels=dict(programme.panels)[source.root.root.independent_group_id] if phase == "responses" else None):
                    incoming[name] = add("external.native-input." + pin.object_fingerprint, value, pin.object_id)
            for name in (*INPUTS[phase], *(("decision",) if transport and phase in ("responses", "response-score") else ()), *native_names):
                if name in incoming:
                    edge(node, name, external_id=incoming[name])
                else:
                    producer, output = produced[name]
                    edge(node, name, producer=producer, output=output)
        for port, phase in (("points", "point"), ("mechanicals", "mechanical"), ("readouts", "response-score")):
            edge(final, port + "." + source.source_id, producer=nodes[phase])
        if transport:
            edge(final, "decisions." + source.source_id, producer=nodes["point"], output="decision")
    edge(final, "entry", producer=entry)
    external = inherit_external_inputs(tuple(sorted(external.values(), key=lambda row: row.input_id)),
        (*records.items(), (evidence_id, tuple(value.identity for value in produced_input_parents))), produced_input_parents,
        retained_history=True)
    links = inherit_external_links(links, external)
    return (tuple(sorted(configs.items())), external,
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(records.items())), tuple(sorted(arrays.items())))


def scientific_root_validator(config, context):
    if type(context) is not RecursiveScientificRootContext or type(context.root) is not StudyDraft:
        raise TypeError("selected protected graph requires the actual prospective compiler root context")
    roots = tuple(row.record for row in context.config_inputs if type(row.record) in ROOT_CONFIG_TYPES and row.record.phase == "entry")
    if len(roots) != 1:
        raise ValueError("selected protected graph requires one complete source-entry root")
    programme = roots[0].programme
    configs, external, links, _, _ = contracts(programme, roots[0].entry_evidence, roots[0].entry_evidence_size_bytes,
                transport_policy=getattr(roots[0], "transport_policy", None), transport_calibration=getattr(roots[0], "transport_calibration", None),
        produced_input_parents=roots[0].produced_input_parents if type(roots[0]) in (MatrixSelectedProtectedRootConfigV3, MatrixSelectedTransportRootConfig) else ())
    phase, node = phase_of(config), task_id(config)
    version = config_capability_version(config)
    declaration = next(row for row in operation_declarations()
        if (row.capability_key, row.capability_version) == (capability_key(phase, version), version))
    expected_configs = {name: record for name, record in configs}
    actual = {row.node_id: row.record for row in context.config_inputs}
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.sources.source_arms()}))
    root = context.root
    if (actual != expected_configs or expected_configs.get(node) != config or context.node_id != node
            or tuple(context.external_inputs) != external or tuple(context.links) != links
            or context.stage is not declaration.stage or context.outcome_access is not declaration.outcome_access
            or context.visibility_ceiling is not declaration.visibility_ceiling or context.unit_ids != units(config)
            or context.selected_unit_ids != groups or context.complete_unit_census != (phase in NATIVE)
            or root.evaluation_unit_ids != groups or set(root.development_unit_ids).intersection(groups)
            or root.system is None or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR):
        raise ValueError("selected protected graph changes its complete source/group/phase/link/access census")
    pins = {row.object_identity for row in root.design_inputs if row.materialization_sha256 == row.object_identity.object_fingerprint}
    if not {programme.original_programme, package_identity(programme.point_design.package), programme.sources.closure.identity} <= pins:
        raise ValueError("selected protected root lacks exact selected package/source design witnesses")
    materializations = {row.source_id: row for row in root.source_materializations}
    qualifications = {ObjectIdentity.from_record(row.receipt_id, row): row for row in context.qualifications}
    sources = tuple(item for item in external if item.scientific_role != "HISTORY")
    source_ids = {item.input_id for item in sources}
    if (set(materializations) != source_ids or len(root.source_materializations) != len(source_ids)
            or {row.source_id for row in context.qualifications} != source_ids
            or len(context.qualifications) != len(source_ids)):
        raise ValueError("selected physical source materialization/qualification roster differs from exact SOURCE inputs")
    for item in sources:
        supplied = materializations.get(item.input_id)
        qualification = qualifications.get(None if supplied is None else supplied.qualification_receipt)
        if (supplied is None or qualification is None or supplied.access_disposition is not SourceAccessDisposition.VERIFIED_ACCESS
                or item.parent_substitution or supplied.source_id != qualification.source_id
                or supplied.materialization != qualification.materialization
                or supplied.evidence_world_id != root.system.world.world_id or qualification.evidence_world_id != supplied.evidence_world_id
                or supplied.observation_operator != qualification.observation_operator or supplied.numerical_view_ids != qualification.numerical_view_ids
                or (supplied.materialization.object_id, supplied.materialization.object_schema, supplied.materialization.object_fingerprint,
                    supplied.content_sha256, qualification.content_sha256) != (item.logical_artifact_id, item.payload_schema,
                        item.expected_content_sha256, item.expected_content_sha256, item.expected_content_sha256)
                or (qualification.outcome_access, qualification.visibility_ceiling) != (item.outcome_access, item.visibility_ceiling)):
            raise ValueError("selected protected source lacks actual exact ordinary materialization qualification")


@dataclass(frozen=True, slots=True)
class LoweredSelectedProtectedProgramme:
    draft: RecursiveStudyDraft
    input_records: tuple
    input_artifacts: tuple


def lower_selected_protected_programme(programme, *, root, campaign, draft_id, entry_evidence, resources=None,
        transport_policy=None, transport_calibration=None, produced_input_parents=()):
    from .selected_operational_resources import selected_phase_budgets

    budgets = selected_phase_budgets(resources, family="PROTECTED")
    if type(entry_evidence) is not MatrixSelectedEntryEvidenceV3:
        raise TypeError("selected lowering requires actual explicit commitment-bearing entry evidence")
    entry_evidence.__post_init__()
    raw = entry_evidence.canonical_bytes()
    configs, external, links, records, arrays = contracts(programme, entry_evidence.identity, len(raw),
        transport_policy=transport_policy, transport_calibration=transport_calibration, produced_input_parents=produced_input_parents)
    evidence_id = "external.selected-entry-evidence." + entry_evidence.fingerprint()
    records = tuple(sorted((*records, (evidence_id, entry_evidence))))
    declarations = {(row.capability_key, row.capability_version): row for row in operation_declarations()}
    def selected(config):
        version = config_capability_version(config)
        return declarations[(capability_key(phase_of(config), version), version)]
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node, selection=selected(config).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=budgets[phase_of(config)]) for node, config in configs)
    return LoweredSelectedProtectedProgramme(RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), operations, external, links,
        tuple(node for node, _ in configs), prospective_draft=root), records, arrays)
