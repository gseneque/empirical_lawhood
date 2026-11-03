# SPDX-License-Identifier: MPL-2.0
"""One declaration and lowering owner for selected protected prepared phases."""

from dataclasses import dataclass, replace
from functools import lru_cache

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
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
from .selected_revision_future import MatrixRevisionFutureConfigV2
from .preparation_records import MatrixPreparationHistory, MatrixPreparationAssessment, MatrixPreparationSource
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_point import MatrixPreparedPublicSource
from .prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedFactorWitness, MatrixPreparedFrameAssessment
from .prepared_response_science import MatrixPreparedResponseReadout
from .selected_revision_future import MatrixRevisionFutureConfig, MatrixRevisionFutureHistory, NAMESPACE, node_id
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4RevisionPoint
from .selected_revision_programme import MatrixRevisionSelectedPackage
from .selected_revision_programme import MatrixRevisionPreparedProgramme, MatrixRevisionRootConfig, MatrixRevisionPreparedConfig, MatrixRevisionEntrySeal, global_node
from .selected_revision_results import MatrixRevisionManifest, MatrixRevisionProgrammeAssessment
from .selected_original_commitments import MatrixRevisionEntryEvidenceV2, MatrixRevisionRootConfigV2
from .selected_revision_entry import MatrixRevisionEntryEvidence


PHASES = ("entry", "history", "assess", "measure", "frames", "project", "mechanical", "point", "responses", "response-score", "assess-programme")
NATIVE = ("history", "responses")
MATCHED_PHASES = ("point", "response-score")
ARRAY_OUTPUTS = ("history", "measure", "project", "mechanical", "responses")
RECORDS = {"entry-evidence": MatrixRevisionEntryEvidence, "entry": MatrixRevisionEntrySeal, "original-allocation": UnitAllocation,
    "source": MatrixPreparationSource, "allocation": ScheduledAllocation,
    "history": MatrixPreparationHistory, "numerical": MatrixPreparationAssessment, "witness": MatrixPreparedFactorWitness,
    "frames": MatrixPreparedFrameAssessment, "causal": MatrixPreparedCausalPrefix, "point-package": MatrixRevisionSelectedPackage,
    "point": SelectedE4RevisionPoint, "mechanical": MatrixPreparedMechanicalForecast, "protocol": ScheduledResponseProtocol,
    "responses": MatrixRevisionFutureHistory}
OUTPUTS = {"entry": MatrixRevisionEntrySeal, "history": MatrixPreparationHistory, "assess": MatrixPreparationAssessment,
    "measure": MatrixPreparedFactorWitness, "frames": MatrixPreparedFrameAssessment, "project": MatrixPreparedCausalPrefix,
    "point": SelectedE4RevisionPoint, "mechanical": MatrixPreparedMechanicalForecast, "responses": MatrixRevisionFutureHistory,
    "response-score": MatrixPreparedResponseReadout}
BASE = ("source", "allocation", "initial-state", "history", "history-arrays", "causal", "point", "mechanical", "mechanical-arrays", "protocol")
INPUTS = {"entry": ("entry-evidence",), "history": ("source", "allocation", "initial-state", "entry"),
    "assess": ("source", "allocation", "initial-state", "history", "history-arrays", "entry"),
    "measure": ("source", "initial-state", "history", "history-arrays", "numerical", "entry"),
    "frames": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "entry"),
    "project": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "frames", "entry"),
    "point": ("point-package", "protocol", "causal", "witness", "causal-arrays", "diagnostic-arrays", "mechanical", "mechanical-arrays", "entry"),
    "mechanical": ("protocol", "templates", "causal", "causal-arrays", "entry"),
    "responses": (*BASE, "entry"),
    "response-score": (*BASE, "witness", "diagnostic-arrays", "causal-arrays", "templates", "responses", "response-arrays", "entry"),
    "assess-programme": ("entry", "original-allocation", "points", "mechanicals", "readouts")}
FINAL_KINDS = {"points": SelectedE4RevisionPoint, "mechanicals": MatrixPreparedMechanicalForecast, "readouts": MatrixPreparedResponseReadout}


def phase_version(phase):
    return "2.0.0" if phase in ("entry", *NATIVE, *MATCHED_PHASES) else "1.0.0"


def phase_inputs(phase, version=None):
    version = phase_version(phase) if version is None and phase in MATCHED_PHASES else version
    if version == "2.0.0" and phase in NATIVE:
        return (*INPUTS[phase], "native-provenance", "native-stream")
    if phase in NATIVE:
        raise ValueError("selected native phase requires its current direct-input contract")
    if phase in MATCHED_PHASES and version != phase_version(phase):
        raise ValueError("selected matched point/score requires its original causal mechanical inputs")
    return INPUTS[phase]


def phase_of(config):
    if type(config) not in (MatrixRevisionRootConfig, MatrixRevisionRootConfigV2, MatrixRevisionPreparedConfig, MatrixRevisionFutureConfig,
            preparation.MatrixPreparationOperationConfig, preparation.MatrixPreparationOperationConfigV2, MatrixRevisionFutureConfigV2):
        raise TypeError("selected protected phase requires its exact owning configuration")
    config.__post_init__()
    if config.phase in NATIVE and type(config) not in preparation.native_config_types():
        raise ValueError("selected native phase requires its current direct-input contract")
    return config.phase


def capability_key(phase, lane, version=None):
    version = phase_version(phase) if version is None and phase in MATCHED_PHASES else "1.0.0" if version is None else version
    if phase in NATIVE and version == "2.0.0":
        return NAMESPACE + "." + lane.lower() + "." + phase + ".direct-inputs"
    if phase not in PHASES or lane not in ("DEVELOPMENT", "PROTECTED"):
        raise ValueError("revision worker requires its exact installed phase and custody lane")
    if phase == "entry" and version == "2.0.0":
        return NAMESPACE + "." + lane.lower() + ".entry-original-commitments"
    if phase in MATCHED_PHASES and version == phase_version(phase):
        return NAMESPACE + "." + lane.lower() + "." + phase
    if version != "1.0.0" or phase in ("entry", *NATIVE):
        raise ValueError("revision changes its exact installed original entry edition")
    return NAMESPACE + "." + lane.lower() + "." + phase


def lane_of(programme):
    return "DEVELOPMENT" if programme.phase == "E5_OPPORTUNITY" else "PROTECTED"


def task_id(config):
    return config.config_id.removeprefix("config.")


def units(config):
    if type(config) in (MatrixRevisionRootConfig, MatrixRevisionRootConfigV2):
        return tuple(sorted({source.root.root.independent_group_id for _, source in config.programme.source_arms()}))
    if type(config) is MatrixRevisionPreparedConfig:
        return (config.public_source.original.root.independent_group_id,)
    return (config.source.root.root.independent_group_id,)


def digests(config):
    if type(config) in (MatrixRevisionRootConfig, MatrixRevisionRootConfigV2):
        return (config.programme.fingerprint(),)
    if type(config) in (preparation.MatrixPreparationOperationConfig, preparation.MatrixPreparationOperationConfigV2):
        return preparation.operand_digests(config)
    return (config.programme.object_fingerprint,)


def slots(config):
    return preparation.slots(config) if phase_of(config) == "history" else ("responses." + config.source.source_id,)


def stage(phase, lane):
    if phase in NATIVE:
        return ScientificStage.ACQUIRE
    if phase == "assess-programme":
        return ScientificStage.TRANSFORM if lane == "DEVELOPMENT" else ScientificStage.EVALUATE
    if phase in ("assess", "frames", "response-score"):
        return ScientificStage.FALSIFY
    return ScientificStage.FREEZE if phase in ("entry", "point", "mechanical") else ScientificStage.TRANSFORM


def access(phase, lane):
    if lane == "DEVELOPMENT":
        return OutcomeAccess.DEVELOPMENT_VISIBLE
    return OutcomeAccess.EVALUATOR_REVEAL if phase == "assess-programme" else OutcomeAccess.EVALUATION_SEALED if phase in ("responses", "response-score") else OutcomeAccess.OUTCOME_BLIND



@dataclass(frozen=True, slots=True)
class _Factory:
    phase: str
    lane: str = "PROTECTED"
    version: str = "1.0.0"
    def __call__(self):
        from .selected_revision_workers import SelectedRevisionWorker
        declaration = next(row for row in operation_declarations() if
            (row.capability_key, row.capability_version) == (capability_key(self.phase, self.lane, self.version), self.version))
        return SelectedRevisionWorker(self.phase, self.lane, declaration.manifest())


def prepare_for_invocation(supplier, runner):
    from functools import partial
    from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
    callback = getattr(supplier, "prepare_selected_revision", None)
    if not callable(callback):
        raise PermissionError("selected protected task requires actual current issued parent custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner), native_effect=runner.phase in NATIVE)


def prepare_native_work(*, runner, context, expected_parent):
    return runner.prepare_native_work(context, expected_parent=expected_parent)


def config_input_parents(config,all_config_records):
    from .selected_prepared_parent_projection import prepared_config_parents
    import sys
    return prepared_config_parents(config,all_config_records,owner=sys.modules[__name__],
        root_types=(MatrixRevisionRootConfigV2,),root_phase="entry")


@lru_cache(maxsize=1)
def operation_declarations():
    record_types = {**RECORDS, "entry-evidence": MatrixRevisionEntryEvidence}
    codecs = {kind.SCHEMA: kind for kind in (*record_types.values(), *FINAL_KINDS.values(), *OUTPUTS.values(),
        preparation.MatrixPreparationOperationConfig, MatrixRevisionRootConfig, MatrixRevisionPreparedConfig,
        MatrixRevisionFutureConfig, MatrixRevisionManifest, MatrixRevisionProgrammeAssessment, ScientificAdjudicationRecord)}
    declarations = []
    for lane, phase in ((lane, phase) for lane in ("DEVELOPMENT", "PROTECTED") for phase in PHASES):
        inputs = []
        for name in INPUTS[phase]:
            kind = MatrixRevisionEntryEvidenceV2 if phase == "entry" else FINAL_KINDS.get(name, record_types.get(name))
            inputs.append(RecursivePortContract(name, MATRIX_ARRAY_SCHEMA if kind is None else kind.SCHEMA,
                "application/x-npz" if kind is None else "application/json", MAXIMUM_MATRIX_ARRAY_BYTES if kind is None else None,
                minimum_count=1, maximum_count=None if name in FINAL_KINDS else 1))
        outputs = (OutputTemplate("product", OUTPUTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),) if phase != "assess-programme" else (
            OutputTemplate("manifest", MatrixRevisionManifest.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("product", MatrixRevisionProgrammeAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("adjudication", ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        if phase == "entry":
            outputs += (OutputTemplate("original-allocation", UnitAllocation.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),)
        if phase == "assess-programme" and lane == "DEVELOPMENT":
            outputs = tuple(value for value in outputs if value.output_id != "adjudication")
        if phase in ARRAY_OUTPUTS:
            outputs += (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),)
        permissions = [CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS]
        if access(phase, lane) in (OutcomeAccess.EVALUATION_SEALED, OutcomeAccess.EVALUATOR_REVEAL):
            permissions.append(CapabilityPermission.READ_SEALED_OUTCOMES)
        if phase == "assess-programme" and lane == "PROTECTED":
            permissions.append(CapabilityPermission.REVEAL_OUTCOMES)
        config = MatrixRevisionRootConfigV2 if phase == "entry" else MatrixRevisionRootConfig if phase == "assess-programme" else preparation.MatrixPreparationOperationConfig if phase in ("history", "assess") else MatrixRevisionFutureConfig if phase in ("responses", "response-score") else MatrixRevisionPreparedConfig
        version = phase_version(phase) if phase not in NATIVE else "1.0.0"
        implementation = NAMESPACE + "." + lane.lower() + (".entry.original-commitments.v2" if phase == "entry"
            else "." + phase + (".causal-matched-revision.v2" if phase in MATCHED_PHASES else ".original-prepared-native-revision.v1"))
        selected_codecs = {**codecs, MatrixRevisionEntryEvidenceV2.SCHEMA: MatrixRevisionEntryEvidenceV2,
            MatrixRevisionRootConfigV2.SCHEMA: MatrixRevisionRootConfigV2} if phase == "entry" else codecs
        declarations.append(RecursiveOperationDeclaration(NAMESPACE + "." + lane.lower() + "." + phase if phase in NATIVE else capability_key(phase, lane, version), version, implementation,
            CapabilityKind.EVALUATOR if stage(phase,lane) is ScientificStage.EVALUATE else CapabilityKind.SIMULATOR if phase in NATIVE else CapabilityKind.FALSIFIER if stage(phase,lane) is ScientificStage.FALSIFY else CapabilityKind.ANALYSIS if stage(phase,lane) is ScientificStage.DEVELOP else CapabilityKind.TRANSFORM,
            config, stage(phase, lane), tuple(sorted(inputs, key=lambda row: row.port_id)), tuple(sorted(outputs, key=lambda row: row.output_id)),
            tuple(sorted(permissions)), EvidenceCeiling.RESPONSE, access(phase, lane), VisibilityCeiling.DEVELOPMENT_ONLY if lane == "DEVELOPMENT" else VisibilityCeiling.OUTCOME_VISIBLE if phase == "assess-programme" else VisibilityCeiling.PROSPECTIVE,
            preparation.BUDGET, ("actual-original-protected-source-custody", "complete-matched-root-native-and-reducer-census", "selected-points-before-paired-futures"),
            _Factory(phase, lane, version), selected_codecs, scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=units, scientific_operand_sha256s=digests,
                native_effect_slot_ids=slots if phase in NATIVE else None, scientific_root_validator=scientific_root_validator,
                adjudication_output_id="adjudication" if phase == "assess-programme" and lane == "PROTECTED" else None),
            execution_properties=RecursiveExecutionProperties(native_effect=phase in NATIVE, complete_unit_census=phase in NATIVE,
                native_work_preparer=prepare_native_work if phase in NATIVE else None, runner_preparation_factory=prepare_for_invocation,
                barrier=BarrierKind.REVEAL if phase == "assess-programme" and lane == "PROTECTED" else BarrierKind.FREEZE if stage(phase, lane) is ScientificStage.FREEZE else BarrierKind.NONE),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS))
    for index, base in enumerate(declarations):
        if base.capability_version == "1.0.0" and base.capability_key.endswith((".history", ".responses")):
            phase = "history" if base.capability_key.endswith(".history") else "responses"
            config_type = preparation.MatrixPreparationOperationConfigV2 if phase == "history" else MatrixRevisionFutureConfigV2
            lane = "DEVELOPMENT" if ".development." in base.capability_key else "PROTECTED"
            factory = _Factory(phase, lane, "2.0.0")
            declarations[index] = preparation.direct_native_declaration(base, config_type=config_type,
                runner_factory=factory)
    return tuple(replace(value,config_input_parents=config_input_parents) for value in
        sorted(declarations,key=lambda row:(row.capability_key,row.capability_version)))


@lru_cache(maxsize=2)
def contracts(programme, evidence_pin, evidence_size, *, produced_input_parents=()):
    if evidence_pin.object_schema != MatrixRevisionEntryEvidenceV2.SCHEMA:
        raise ValueError("revision graph requires current commitment-bearing entry evidence")
    if type(programme) is not MatrixRevisionPreparedProgramme:
        raise TypeError("selected protected graph requires its actual complete programme")
    programme.__post_init__()
    configs, external, records, arrays, links = {}, {}, {}, {}, []
    def add(name, value, object_id):
        raw = value.canonical_bytes()
        row = RecursiveExternalInput(name, object_id, value.SCHEMA, "application/json", len(raw),
            OutcomeAccess.DEVELOPMENT_VISIBLE if lane_of(programme) == "DEVELOPMENT" else OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.DEVELOPMENT_ONLY if lane_of(programme) == "DEVELOPMENT" else VisibilityCeiling.PROSPECTIVE, value.fingerprint(), "SOURCE")
        if external.setdefault(name, row) != row or records.setdefault(name, value) != value:
            raise ValueError("selected graph aliases distinct original scientific records")
        return name
    def array(name, artifact):
        row = RecursiveExternalInput(name, artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes,
            OutcomeAccess.DEVELOPMENT_VISIBLE if lane_of(programme) == "DEVELOPMENT" else OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.DEVELOPMENT_ONLY if lane_of(programme) == "DEVELOPMENT" else VisibilityCeiling.PROSPECTIVE, artifact.sha256, "SOURCE")
        if external.setdefault(name, row) != row or arrays.setdefault(name, artifact) != artifact:
            raise ValueError("selected graph aliases distinct original physical files")
        return name
    def edge(node, name, *, external_id=None, producer=None, output="product"):
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=external_id,
            producer_node_id=producer, producer_output_id=output if producer is not None else None, scientific_role="SOURCE" if producer is None else "HISTORY"))
    for phase in ("entry", "assess-programme"):
        node = global_node(programme, phase)
        kind = MatrixRevisionRootConfigV2 if phase == "entry" else MatrixRevisionRootConfig
        configs[node] = kind("config." + node, programme, phase,
            evidence_pin if phase == "entry" else None, evidence_size if phase == "entry" else None,
            **({"produced_input_parents": produced_input_parents} if kind is MatrixRevisionRootConfigV2 else {}))
    entry, final = (global_node(programme, phase) for phase in ("entry", "assess-programme"))
    evidence_id = "external.selected-entry-evidence." + evidence_pin.object_fingerprint
    external[evidence_id] = RecursiveExternalInput(evidence_id, evidence_pin.object_id, evidence_pin.object_schema, "application/json",
        evidence_size, OutcomeAccess.DEVELOPMENT_VISIBLE if lane_of(programme) == "DEVELOPMENT" else OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.DEVELOPMENT_ONLY if lane_of(programme) == "DEVELOPMENT" else VisibilityCeiling.PROSPECTIVE, evidence_pin.object_fingerprint, "SOURCE")
    edge(entry, "entry-evidence", external_id=evidence_id)
    design = add("external.selected-point-design." + programme.selected_package.fingerprint(), programme.selected_package, programme.selected_package.record_id)
    allocation = programme.reservation.allocation
    templates = array("external.selected-templates." + programme.assay.template_artifact.sha256, programme.assay.template_artifact)
    for _, source in programme.source_arms():
        allocation = next(row for row in programme.allocations if ObjectIdentity.from_record(row.allocation_id, row) == source.original.allocation)
        allocation_id = add("external.revision-allocation." + allocation.fingerprint(), allocation, allocation.allocation_id)
        public = MatrixPreparedPublicSource.from_source(source)
        protocol = programme.protocol(source)
        source_id = add("external.selected-source." + source.source_id, source, source.source_id)
        protocol_id = add("external.selected-protocol." + protocol.fingerprint(), protocol, protocol.protocol_id)
        initial = array("external.selected-initial." + source.initial.array_artifact.fingerprint(), source.initial.array_artifact)
        nodes = {phase: preparation.node_id(source, phase) if phase in ("history", "assess") else node_id(source, phase) for phase in PHASES if phase not in ("entry", "assess-programme")}
        for phase, node in nodes.items():
            configs[node] = ((preparation.MatrixPreparationOperationConfigV2 if phase == "history" else preparation.MatrixPreparationOperationConfig)("config." + node, phase, source, len(allocation.canonical_bytes())) if phase in ("history", "assess") else
                (MatrixRevisionFutureConfigV2 if phase == "responses" else MatrixRevisionFutureConfig)("config." + node, programme.identity, source, protocol, dict(programme.panels)[source.root.root.independent_group_id],
                    programme.selected_package, phase) if phase in ("responses", "response-score") else
                MatrixRevisionPreparedConfig("config." + node, programme.identity, public, phase, programme.selected_package.identity))
            incoming = {"source": source_id, "allocation": allocation_id, "initial-state": initial,
                "point-package": design, "protocol": protocol_id, "templates": templates}
            produced = {"entry": (entry, "product"), "history": (nodes["history"], "product"), "history-arrays": (nodes["history"], "arrays"),
                "numerical": (nodes["assess"], "product"), "witness": (nodes["measure"], "product"), "diagnostic-arrays": (nodes["measure"], "arrays"),
                "frames": (nodes["frames"], "product"), "causal": (nodes["project"], "product"), "causal-arrays": (nodes["project"], "arrays"),
                "point": (nodes["point"], "product"), "mechanical": (nodes["mechanical"], "product"), "mechanical-arrays": (nodes["mechanical"], "arrays"),
                "responses": (nodes["responses"], "product"), "response-arrays": (nodes["responses"], "arrays")}
            native_names = ()
            if phase in NATIVE:
                native_names = tuple(name for name, _, _ in preparation.native_input_records(source,
                    panels=dict(programme.panels)[source.root.root.independent_group_id] if phase == "responses" else None))
                for name, pin, value in preparation.native_input_records(source,
                        panels=dict(programme.panels)[source.root.root.independent_group_id] if phase == "responses" else None):
                    incoming[name] = add("external.native-input." + pin.object_fingerprint, value, pin.object_id)
            for name in (*INPUTS[phase], *native_names):
                if name in incoming:
                    edge(node, name, external_id=incoming[name])
                else:
                    producer, output = produced[name]
                    edge(node, name, producer=producer, output=output)
        for port, phase in (("points", "point"), ("mechanicals", "mechanical"), ("readouts", "response-score")):
            edge(final, port + "." + source.source_id, producer=nodes[phase])
    edge(final, "entry", producer=entry)
    edge(final, "original-allocation", producer=entry, output="original-allocation")
    external = inherit_external_inputs(tuple(sorted(external.values(), key=lambda row: row.input_id)),
        (*records.items(), (evidence_id, tuple(value.identity for value in produced_input_parents))), produced_input_parents,
        retained_history=True)
    links = inherit_external_links(links, external)
    return (tuple(sorted(configs.items())), external,
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(records.items())), tuple(sorted(arrays.items())))


def scientific_root_validator(config, context):
    from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
    if type(context) is not RecursiveScientificRootContext:
        raise TypeError("revision graph needs its actual compiler scientific root context")
    roots = tuple(row.record for row in context.config_inputs if type(row.record) in (MatrixRevisionRootConfig, MatrixRevisionRootConfigV2) and row.record.phase == "entry")
    if len(roots) != 1:
        raise ValueError("revision graph requires one complete actual entry root")
    selected, = roots
    programme, lane = selected.programme, lane_of(selected.programme)
    configs, external, links, _, _ = contracts(programme, selected.entry_evidence, selected.entry_evidence_size_bytes,
        produced_input_parents=selected.produced_input_parents if type(selected) is MatrixRevisionRootConfigV2 else ())
    expected = dict(configs)
    actual = {row.node_id: row.record for row in context.config_inputs}
    phase, node = phase_of(config), task_id(config)
    root = context.root
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.source_arms()}))
    if (actual != expected or expected.get(node) != config or context.node_id != node
            or tuple(context.external_inputs) != external or tuple(context.links) != links
            or context.stage is not stage(phase, lane) or context.outcome_access is not access(phase, lane)
            or context.visibility_ceiling is not (VisibilityCeiling.DEVELOPMENT_ONLY if lane == "DEVELOPMENT" else VisibilityCeiling.OUTCOME_VISIBLE if phase == "assess-programme" else VisibilityCeiling.PROSPECTIVE)
            or context.unit_ids != units(config) or context.selected_unit_ids != groups
            or context.complete_unit_census != (phase in NATIVE)):
        raise ValueError("revision graph substitutes its complete derived source/task/port/group census")
    if lane == "DEVELOPMENT":
        if type(root) is not DevelopmentStudySpec or root != development_root(programme, root.study_id):
            raise ValueError("revision development graph substitutes its actual nonpromotable source root")
        return
    if (type(root) is not StudyDraft or root.evaluation_unit_ids != groups
            or set(root.development_unit_ids).intersection(groups)
            or root.system is None or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR):
        raise ValueError("revision protected graph changes actual original independent-unit or numerical-world scope")
    pins = {row.object_identity for row in root.design_inputs if row.materialization_sha256 == row.object_identity.object_fingerprint}
    if not {programme.identity, programme.selected_package.identity, programme.sources.closure.identity} <= pins:
        raise ValueError("revision protected root lacks exact source and selected model witnesses")
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
            raise ValueError("revision protected source lacks its actual exact materialization qualification")


def development_root(programme, study_id):
    from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
    from empirical_lawhood.kernel.evidence import ClaimSpec
    programme.__post_init__()
    world = "world.matrix-selected-revision.development"
    question = "Assess the complete matched opportunity using the authentically selected E4 revision and original paired assay."
    groups = tuple(sorted({source.root.root.independent_group_id for _, source in programme.source_arms()}))
    claim = ClaimSpec("claim." + study_id, world, programme.identity.object_id, question,
        "Complete original matched groups and explicit functional criterion; exposed development only.",
        "unit.matrix-response.whole-group", None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, "No protected issue, source qualification, sampling or downstream uncertainty is established.",
        ("assumption.matrix-revision.exposed-development",), numerical_view_ids=("fine", "primary"))
    return DevelopmentStudySpec(study_id, question, programme.identity, world, WorldKind.NUMERICAL_SIMULATOR,
        groups, ("fine", "primary"), (claim,), tuple(sorted((programme.identity, programme.selected_package.identity), key=lambda row: row.object_id)))



@dataclass(frozen=True, slots=True)
class LoweredSelectedProtectedProgramme:
    draft: RecursiveStudyDraft
    input_records: tuple
    input_artifacts: tuple


def lower_revision_prepared_programme(programme, *, root, campaign, draft_id, entry_evidence, resources, produced_input_parents=()):
    from .selected_revision_entry import validate_entry_evidence
    from .selected_operational_resources import MatrixSelectedOperationalResources
    if type(resources) is not MatrixSelectedOperationalResources:
        raise TypeError("revision public lowering requires explicit complete phase resources")
    lane = lane_of(programme)
    budgets = resources.for_family("OPPORTUNITY" if lane == "DEVELOPMENT" else "PROTECTED")
    validate_entry_evidence(entry_evidence, programme)
    raw = entry_evidence.canonical_bytes()
    configs, external, links, records, arrays = contracts(programme, entry_evidence.identity, len(raw), produced_input_parents=produced_input_parents)
    evidence_id = "external.selected-entry-evidence." + entry_evidence.fingerprint()
    records = tuple(sorted((*records, (evidence_id, entry_evidence))))
    declarations = {(row.capability_key, row.capability_version): row for row in operation_declarations()}
    def selected(config):
        version = phase_version(phase_of(config))
        return declarations[(capability_key(phase_of(config), lane, version), version)]
    def budget(config):
        phase = phase_of(config)
        key = "design" if lane == "DEVELOPMENT" and phase == "entry" else "nominate" if lane == "DEVELOPMENT" and phase == "assess-programme" else phase
        return budgets[key]
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node, selection=selected(config).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=budget(config)) for node, config in configs)
    return LoweredSelectedProtectedProgramme(RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), operations, external, links,
        tuple(node for node, _ in configs), development_study=root if lane == "DEVELOPMENT" else None,
        prospective_draft=root if lane == "PROTECTED" else None), records, arrays)
