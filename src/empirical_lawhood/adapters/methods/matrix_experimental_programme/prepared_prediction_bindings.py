# SPDX-License-Identifier: MPL-2.0
"""A closed additive source-through-prediction development programme.

The original two-phase source checkpoint remains closed. Its genuine native
runner and custody are reused under a separate complete-root declaration.
Predictor ports contain no current source streams. Response-future custody,
protected prospective entry and functional programme reduction remain separate
unimplemented composition steps; this checkpoint grants none of them.
"""

from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks

from . import preparation_bindings as source_owner
from . import prepared_forecast, prepared_point, prepared_prefix
from .preparation_experiment import MatrixPreparationSourceBank
from .preparation_records import MatrixPreparationAssessment, MatrixPreparationHistory, MatrixPreparationSource


NAMESPACE = "matrix-prepared-prediction"
WORLD = "world.matrix-prepared-prediction.exposed-development"
QUESTION = "Retain selected coupling-only sources, independent causal frames and the unchanged frozen numerical predictions."
SCOPE = "EXPOSED_DEVELOPMENT_SOURCE_THROUGH_PREDICTION_NOT_COMPLETE_E5_OR_E6"
TAIL_PHASES = ("measure", "frames", "project", "point", "mechanical")
ALL_PHASES = ("history", "assess", *TAIL_PHASES)


@dataclass(frozen=True, slots=True)
class MatrixPreparedPredictionProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-prediction-programme"
    record_id: str
    sources: MatrixPreparationSourceBank
    point_design: prepared_point.MatrixPreparedPointDesign
    protocols: tuple[tuple[str, ScheduledResponseProtocol], ...]
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.sources) is not MatrixPreparationSourceBank or type(self.point_design) is not prepared_point.MatrixPreparedPointDesign
                or self.scope != SCOPE or type(self.protocols) is not tuple
                or tuple(key for key, _ in self.protocols) != tuple(row.source_id for row in self.sources.sources)
                or any(type(value) is not ScheduledResponseProtocol for _, value in self.protocols)
                or self.point_design.sources != tuple(prepared_point.MatrixPreparedPublicSource.from_source(row) for row in self.sources.sources)):
            raise ValueError("prepared prediction programme omits exact selected sources, frozen predictors or physical protocols")
        self.sources.__post_init__()
        self.sources.input_artifacts
        self.point_design.__post_init__()
        artifacts = {}
        for source in self.sources.sources:
            protocol = dict(self.protocols)[source.source_id]
            protocol.__post_init__()
            if (protocol.public_source != source.original or protocol.horizon_steps != (16, 64, 128)
                    or protocol.criterion != self.point_design.original_forecast.criterion
                    or protocol.receiver_count != 48
                    or protocol.receiver_gram_tolerance != self.point_design.original_forecast.criterion_record.receiver_gram_tolerance
                    or tuple(sorted((row.role, row.amplitude, row.force_norm, row.pulse_steps) for row in protocol.actions)) !=
                        tuple(sorted((row.role, row.amplitude, row.force_norm, row.pulse_steps) for row in self.point_design.original_forecast.criterion_record.action_scales))
                    or source.total_ticks < source.coordinate.ramp_ticks):
                raise ValueError("prepared prediction programme changes full selected physical horizons, frozen criterion or restored future")
            artifact = protocol.templates.array_artifact
            if artifacts.setdefault(artifact.sha256, artifact) != artifact:
                raise ValueError("prepared prediction programme aliases differing exact template identities")

    @property
    def identity(self):
        return prepared_prefix.identity(self)


@dataclass(frozen=True, slots=True)
class MatrixPreparedPredictionRootConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-prediction-root-config"
    config_id: str
    programme: MatrixPreparedPredictionProgramme

    def __post_init__(self):
        if type(self.programme) is not MatrixPreparedPredictionProgramme or self.config_id != "config." + root_node(self.programme):
            raise ValueError("prepared prediction root configuration changes the complete immutable selection")


@dataclass(frozen=True, slots=True)
class MatrixPreparedPredictionConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-prediction-config"
    config_id: str
    programme: ObjectIdentity
    public_source: prepared_point.MatrixPreparedPublicSource
    phase: str

    def __post_init__(self):
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixPreparedPredictionProgramme.SCHEMA
                or type(self.public_source) is not prepared_point.MatrixPreparedPublicSource or self.phase not in TAIL_PHASES
                or self.config_id != "config." + tail_node(self.public_source.source, self.phase)):
            raise ValueError("prepared prediction configuration changes its own source, whole selection or phase")


@dataclass(frozen=True, slots=True)
class MatrixPreparedPredictionDesignReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-prediction-design-receipt"
    record_id: str
    programme: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    point_design: ObjectIdentity
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixPreparedPredictionProgramme.SCHEMA or self.scope != SCOPE
                or self.point_design.object_schema != prepared_point.MatrixPreparedPointDesign.SCHEMA
                or not self.sources or tuple(row.object_id for row in self.sources) != tuple(sorted({row.object_id for row in self.sources}))
                or any(row.object_schema != MatrixPreparationSource.SCHEMA for row in self.sources)):
            raise ValueError("prepared design receipt changes its exact selection or invents scientific authority")


def root_node(programme):
    return NAMESPACE + ".design." + programme.fingerprint()


def tail_node(source, phase):
    return NAMESPACE + "." + source.object_id + "." + phase


def _record_external(key, record, object_id):
    raw = record.canonical_bytes()
    return RecursiveExternalInput(key, object_id, record.SCHEMA, "application/json", len(raw),
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, sha256(raw).hexdigest(), "SOURCE")


def _array_external(key, artifact):
    return RecursiveExternalInput(key, artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, artifact.sha256, "SOURCE")


def _source_contracts(source, allocation, protocol, *, programme_reference, point_id):
    """One source projection, shared by full and local graph authentication."""
    records, arrays, configs, links = {}, {}, {}, []
    source_id, allocation_id, initial_id = (source_owner.external_id(source, name) for name in ("source", "allocation", "initial-state"))
    records[source_id], records[allocation_id], arrays[initial_id] = source, allocation, source.initial.array_artifact
    protocol_id = "external.protocol." + protocol.fingerprint()
    template_id = "external.templates." + protocol.templates.array_artifact.sha256
    records[protocol_id], arrays[template_id] = protocol, protocol.templates.array_artifact
    for phase in ("history", "assess"):
        node = source_owner.node_id(source, phase)
        configs[node] = source_owner.MatrixPreparationOperationConfig("config." + node, phase, source, len(allocation.canonical_bytes()))
        for name in ("source", "allocation", "initial-state"):
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name,
                external_input_id=source_owner.external_id(source, name), scientific_role="SOURCE"))
        if phase == "assess":
            for name, output in (("history", "product"), ("history-arrays", "arrays")):
                links.append(RecursiveInputLink("edge." + node + "." + name, node, name,
                    producer_node_id=source_owner.node_id(source, "history"), producer_output_id=output, scientific_role="HISTORY"))
    public = prepared_point.MatrixPreparedPublicSource.from_source(source)
    for phase in TAIL_PHASES:
        node = tail_node(source.identity, phase)
        configs[node] = MatrixPreparedPredictionConfig("config." + node, programme_reference, public, phase)
        external = {"source": source_id, "initial-state": initial_id} if phase in ("measure", "frames", "project") else {}
        if phase == "point":
            external["point-design"] = point_id
        if phase == "mechanical":
            external.update({"protocol": protocol_id, "templates": template_id})
        for name, input_id in external.items():
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=input_id, scientific_role="SOURCE"))
        dependencies = {}
        if phase in ("measure", "frames", "project"):
            dependencies.update({"history": ("history", "product"), "history-arrays": ("history", "arrays"), "numerical": ("assess", "product")})
        if phase in ("frames", "project", "point"):
            dependencies.update({"witness": ("measure", "product"), "diagnostic-arrays": ("measure", "arrays")})
        if phase in ("project", "point"):
            dependencies["frames"] = "frames", "product"
        if phase in ("point", "mechanical"):
            dependencies.update({"causal": ("project", "product"), "causal-arrays": ("project", "arrays")})
        for name, (producer_phase, output) in dependencies.items():
            producer = source_owner.node_id(source, producer_phase) if producer_phase in ("history", "assess") else tail_node(source.identity, producer_phase)
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name, producer_node_id=producer,
                producer_output_id=output, scientific_role="HISTORY"))
    return configs, links, records, arrays


def contracts(programme):
    """Exact complete metadata projection, without any scientific reduction."""
    records, arrays, configs, links = {}, {}, {}, []
    programme_reference = programme.identity
    root_config = MatrixPreparedPredictionRootConfig("config." + root_node(programme), programme)
    configs[root_node(programme)] = root_config
    point_id = "external.point-design." + programme.point_design.fingerprint()
    records[point_id] = programme.point_design
    allocations = {row.fingerprint(): row for row in programme.sources.allocations}
    protocols = dict(programme.protocols)
    for source in programme.sources.sources:
        selected, edges, canonical, binary = _source_contracts(source,
            allocations[source.original.allocation.object_fingerprint], protocols[source.source_id],
            programme_reference=programme_reference, point_id=point_id)
        configs.update(selected)
        links.extend(edges)
        records.update(canonical)
        arrays.update(binary)
    externals = tuple(sorted((*(_record_external(key, record, _record_id(record)) for key, record in records.items()),
        *(_array_external(key, artifact) for key, artifact in arrays.items())), key=lambda row: row.input_id))
    return tuple(sorted(configs.items())), tuple(sorted(links, key=lambda row: row.edge_id)), externals, tuple(sorted(records.items())), tuple(sorted(arrays.items()))


def _record_id(record):
    for name in ("record_id", "source_id", "allocation_id", "protocol_id"):
        if hasattr(record, name):
            return getattr(record, name)
    raise ValueError("prepared prediction input lacks its exact owning record ID")


def units(config):
    if type(config) is MatrixPreparedPredictionRootConfig:
        return tuple(sorted({row.root.root.independent_group_id for row in config.programme.sources.sources}))
    return source_owner.units(config) if type(config) is source_owner.MatrixPreparationOperationConfig else (config.public_source.original.root.independent_group_id,)


def digests(config):
    if type(config) is MatrixPreparedPredictionRootConfig:
        return (config.programme.fingerprint(),)
    return source_owner.operand_digests(config) if type(config) is source_owner.MatrixPreparationOperationConfig else tuple(sorted((config.programme.object_fingerprint, config.public_source.source.object_fingerprint)))


def development_root(programme, study_id):
    groups = tuple(sorted({row.root.root.independent_group_id for row in programme.sources.sources}))
    views = tuple(sorted({view.view_id for row in programme.sources.sources for view in (row.primary_view, row.fine_view)}))
    claim = ClaimSpec("claim." + study_id, WORLD, "population.matrix-prepared-prediction.selected", QUESTION,
        "Every selected whole group, recipe, complete paired source, causal factor lattice and five mechanical prediction methods.",
        "unit.original-whole-group", None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, "No original applicability calibration, future response custody, functional benefit, protected entry or qualification.",
        ("assumption.matrix-prepared-prediction.coupling-only-original-physics",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, programme.identity, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        groups, views, (claim,), tuple(sorted({programme.identity, *(operand for source in programme.sources.sources
            for operand in source_owner.operands(source))}, key=lambda row: row.object_id)))


def scientific_root_validator(config, context):
    roots = tuple(row.record for row in context.config_inputs if type(row.record) is MatrixPreparedPredictionRootConfig)
    if len(roots) != 1:
        raise ValueError("prepared prediction requires exactly its own complete root declaration")
    programme = roots[0].programme
    configs, links, external, _, _ = contracts(programme)
    actual = tuple((row.node_id, row.record) for row in context.config_inputs)
    phase = "design" if type(config) is MatrixPreparedPredictionRootConfig else config.phase
    stage = ScientificStage.ACQUIRE if phase == "history" else ScientificStage.FALSIFY if phase in ("assess", "frames") else ScientificStage.DEVELOP
    if (actual != configs or tuple(context.links) != links or tuple(context.external_inputs) != external
            or context.root != development_root(programme, context.root.study_id) or context.stage is not stage
            or context.unit_ids != units(config) or context.selected_unit_ids != units(roots[0])
            or context.complete_unit_census != (phase == "history")
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or dict(configs).get(context.node_id) != config):
        raise ValueError("prepared prediction changes its complete exact graph, source/phase census or external identity/digest/size/access")


RECORD_PORTS = {"source": MatrixPreparationSource, "history": MatrixPreparationHistory, "numerical": MatrixPreparationAssessment,
    "witness": prepared_prefix.MatrixPreparedFactorWitness, "frames": prepared_prefix.MatrixPreparedFrameAssessment,
    "causal": prepared_prefix.MatrixPreparedCausalPrefix, "point-design": prepared_point.MatrixPreparedPointDesign,
    "protocol": ScheduledResponseProtocol}
INPUTS = {"design": (), "measure": ("source", "initial-state", "history", "history-arrays", "numerical"),
    "frames": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays"),
    "project": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "frames"),
    "point": ("point-design", "witness", "diagnostic-arrays", "frames", "causal", "causal-arrays"),
    "mechanical": ("protocol", "templates", "causal", "causal-arrays")}
OUTPUTS = {"design": MatrixPreparedPredictionDesignReceipt, "measure": prepared_prefix.MatrixPreparedFactorWitness,
    "frames": prepared_prefix.MatrixPreparedFrameAssessment, "project": prepared_prefix.MatrixPreparedCausalPrefix,
    "point": prepared_point.MatrixPreparedPointSeal, "mechanical": prepared_forecast.MatrixPreparedMechanicalForecast}


class MatrixPreparedPredictionRunner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            config_port, = tuple(row for row in context.input_ports if row.payload_schema in
                (MatrixPreparedPredictionRootConfig.SCHEMA, MatrixPreparedPredictionConfig.SCHEMA))
            kind = MatrixPreparedPredictionRootConfig if config_port.payload_schema == MatrixPreparedPredictionRootConfig.SCHEMA else MatrixPreparedPredictionConfig
            config = decode_canonical_bytes(config_port.read(), kind, maximum_bytes=config_port.size_bytes)
            phase = "design" if kind is MatrixPreparedPredictionRootConfig else config.phase
            expected_task = root_node(config.programme) if phase == "design" else tail_node(config.public_source.source, phase)
            if (context.config.content_sha256 != config.fingerprint() or context.config.config_id != config.config_id
                    or context.task_id != expected_task or context.resource_budget != source_owner.BUDGET
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or context.permissions != source_owner.operation_declarations()[0].permissions):
                raise ValueError("prepared prediction worker substitutes its exact frozen configuration")
            ports = {row.artifact_id: row for row in context.input_ports if row is not config_port}
            if len(ports) != len(context.input_ports) - 1:
                raise ValueError("prepared prediction worker repeats an exact original input identity")
            records = {}
            for name in INPUTS[phase]:
                if name not in RECORD_PORTS:
                    continue
                matches = tuple(row for row in ports.values() if row.payload_schema == RECORD_PORTS[name].SCHEMA)
                if len(matches) != 1:
                    raise ValueError("prepared prediction worker omits or duplicates its exact typed record")
                port, = matches
                records[name] = decode_canonical_bytes(port.read(), RECORD_PORTS[name], maximum_bytes=port.size_bytes)
                del ports[port.artifact_id]
            expected = {}
            if "source" in records:
                source = records["source"]
                if prepared_point.MatrixPreparedPublicSource.from_source(source) != config.public_source:
                    raise ValueError("prepared prediction worker crosses its original selected source")
                records["history"].arrays.validate_source(source)
                expected.update({"initial-state": source.initial.array_artifact, "history-arrays": records["history"].arrays.array_artifact})
            for name, owner in (("diagnostic-arrays", "witness"), ("causal-arrays", "causal")):
                if owner in records:
                    expected[name] = records[owner].arrays.array_artifact
            if phase == "mechanical":
                expected["templates"] = records["protocol"].templates.array_artifact
            arrays = {}
            for name, artifact in expected.items():
                matches = tuple(row for row in ports.values() if (row.artifact_id, row.payload_schema, row.media_type, row.size_bytes) ==
                    (artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes))
                if len(matches) != 1:
                    raise ValueError("prepared prediction worker substitutes exact bounded original array identity")
                port, = matches
                arrays[name] = port.read()
                del ports[port.artifact_id]
            if ports or set(records) | set(arrays) != set(INPUTS[phase]):
                raise ValueError("prepared prediction worker changes complete source/record/array input census")
            raw = None
            if phase == "design":
                programme = config.programme
                product = MatrixPreparedPredictionDesignReceipt("design-receipt." + programme.record_id, programme.identity,
                    tuple(row.identity for row in programme.sources.sources), programme.point_design.identity)
            elif phase in ("measure", "frames", "project"):
                source, history, numerical = (records[name] for name in ("source", "history", "numerical"))
                args = source, arrays["initial-state"], history.arrays, numerical
                if phase == "measure":
                    raw, product = prepared_prefix.measure_prepared_prefix(*args, arrays["history-arrays"], artifact_id=_array_id(context))
                elif phase == "frames":
                    product = prepared_prefix.check_prepared_frames(*args, records["witness"], arrays["history-arrays"], arrays["diagnostic-arrays"])
                else:
                    raw, product = prepared_prefix.project_prepared_prefix(*args, records["witness"], records["frames"],
                        arrays["history-arrays"], arrays["diagnostic-arrays"], artifact_id=_array_id(context))
            elif phase == "point":
                feature = prepared_point.causal_feature(records["point-design"], config.public_source, records["causal"], records["witness"],
                    records["frames"], arrays["causal-arrays"], arrays["diagnostic-arrays"], record_id="feature." + context.task_id)
                product = prepared_point.forecast(records["point-design"], config.public_source, records["causal"], feature, record_id="point." + context.task_id)
            else:
                raw, product = prepared_forecast.forecast_public(config.public_source, records["protocol"], records["causal"],
                    arrays["causal-arrays"], arrays["templates"], artifact_id=_array_id(context))
            payloads = {context.task_id + ".product": product.canonical_bytes()}
            if raw is not None:
                payloads[context.task_id + ".arrays"] = raw
            if set(payloads) != {row.output_id for row in context.output_ports}:
                raise ValueError("prepared prediction worker changes compiler-derived exact output census")
            return RunnerResult(tuple(TaskOutputPayload(key, value) for key, value in sorted(payloads.items())),
                (ReceiptCheck("prepared-prediction-complete-numerical-checkpoint-no-qualification", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def _array_id(context):
    return next(row.logical_artifact_id for row in context.output_ports if row.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)


def operation_declarations():
    codecs = {kind.SCHEMA: kind for kind in (MatrixPreparedPredictionProgramme, MatrixPreparedPredictionRootConfig,
        MatrixPreparedPredictionConfig, MatrixPreparedPredictionDesignReceipt, *RECORD_PORTS.values(), *OUTPUTS.values())}
    original = source_owner.operation_declarations()
    permissions = original[0].permissions
    declarations = [replace(row, capability_key=NAMESPACE + "." + row.capability_key.rsplit(".", 1)[-1],
        implementation_id=NAMESPACE + "." + row.capability_key.rsplit(".", 1)[-1] + ".v1",
        scientific_hooks=replace(row.scientific_hooks, scientific_root_validator=scientific_root_validator),
        record_codecs={**row.record_codecs, **codecs}) for row in original]
    for phase in ("design", *TAIL_PHASES):
        falsifier = phase == "frames"
        declarations.append(RecursiveOperationDeclaration(capability_key=NAMESPACE + "." + phase, capability_version="1.0.0",
            implementation_id=NAMESPACE + "." + phase + ".v1", kind=CapabilityKind.FALSIFIER if falsifier else CapabilityKind.ANALYSIS,
            config_record_type=MatrixPreparedPredictionRootConfig if phase == "design" else MatrixPreparedPredictionConfig,
            stage=ScientificStage.FALSIFY if falsifier else ScientificStage.DEVELOP,
            input_ports=tuple(sorted((RecursivePortContract(name, RECORD_PORTS[name].SCHEMA if name in RECORD_PORTS else MATRIX_ARRAY_SCHEMA,
                "application/json" if name in RECORD_PORTS else "application/x-npz", None if name in RECORD_PORTS else MAXIMUM_MATRIX_ARRAY_BYTES)
                for name in INPUTS[phase]), key=lambda row: row.port_id)),
            outputs=tuple(sorted((OutputTemplate("product", OUTPUTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
                *((OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),)
                    if phase in ("measure", "project", "mechanical") else ())), key=lambda row: row.output_id)),
            permissions=permissions, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=source_owner.BUDGET,
            conformance_check_ids=("complete-prepared-source-and-prediction-census", "independent-original-equations"),
            runner_factory=MatrixPreparedPredictionRunner, record_codecs=codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=digests, scientific_unit_ids=units,
                scientific_root_validator=scientific_root_validator), provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS))
    return tuple(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest()))
        for row in sorted(declarations, key=lambda row: row.capability_key))


@dataclass(frozen=True, slots=True)
class LoweredPreparedPrediction:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]
    input_artifacts: tuple


def lower_prepared_prediction(programme, *, campaign, draft_id):
    if type(programme) is not MatrixPreparedPredictionProgramme:
        raise TypeError("prepared prediction lowering requires its complete immutable typed selection")
    programme.__post_init__()
    configs, links, external, records, artifacts = contracts(programme)
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    operations = []
    for node, config in configs:
        phase = "design" if type(config) is MatrixPreparedPredictionRootConfig else config.phase
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declarations[phase].registration().selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=source_owner.BUDGET))
    study = development_root(programme, "study." + draft_id)
    selected_campaign = replace(campaign, objective=QUESTION, system_ids=(study.system.object_id,), world_ids=(WORLD,),
        target_claim_ids=tuple(row.claim_id for row in study.claims))
    draft = RecursiveStudyDraft(draft_id, QUESTION, selected_campaign, (), (), (), tuple(operations), external, links,
        tuple(node for node, _ in configs), development_study=study)
    return LoweredPreparedPrediction(draft, records, artifacts)
