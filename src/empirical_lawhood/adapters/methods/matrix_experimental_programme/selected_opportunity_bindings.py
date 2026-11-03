# SPDX-License-Identifier: MPL-2.0
"""Closed selected opportunity graph over existing native scientific owners."""

from dataclasses import dataclass, replace
from functools import lru_cache, partial
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RecursiveScientificRootContext
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from .selected_produced_inputs import inherit_external_inputs, inherit_external_links

from . import preparation_bindings as preparation
from .selected_opportunity_future import MatrixSelectedOpportunityFutureConfigV2
from .preparation_records import MatrixPreparationHistory, MatrixPreparationAssessment, MatrixPreparationSource
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_point import MatrixPreparedPublicSource
from .prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedFactorWitness, MatrixPreparedFrameAssessment
from .prepared_response_science import MatrixPreparedResponseReadout
from .science import MatrixPreparationNomination
from .selected_original_commitments import MatrixSelectedOpportunityEvidenceV2, MatrixSelectedOpportunityRootConfigV2
from .selected_opportunity import (NAMESPACE, MatrixSelectedOpportunityEvidence, MatrixSelectedOpportunityPublicProgramme,
    MatrixSelectedOpportunitySeal, MatrixSelectedOpportunityManifest, public_programme, validate_opportunity_evidence)
from .selected_opportunity_future import MatrixSelectedOpportunityFutureConfig, MatrixSelectedOpportunityFutureHistory, node_id
from .selected_point import MatrixSelectedPointForecast
from .selected_public import MatrixSelectedPointPayload, package_identity


COMMITTED_DESIGN_KEY = NAMESPACE + ".design-original-commitments"


def capability_key(phase, version="1.0.0"):
    if phase in NATIVE and version == "2.0.0":
        return NAMESPACE + "." + phase + ".direct-inputs"
    if phase == "design" and version == "2.0.0":
        return COMMITTED_DESIGN_KEY
    if phase in PHASES and phase not in ("design", *NATIVE) and version == "1.0.0":
        return NAMESPACE + "." + phase
    raise ValueError("selected opportunity changes its exact installed phase/version")


PHASES = ("design", "history", "assess", "measure", "frames", "project", "point", "mechanical", "responses", "response-score", "nominate")
NATIVE = ("history", "responses")
ARRAY_OUTPUTS = ("history", "measure", "project", "mechanical", "responses")
WORLD = "world.matrix-selected-opportunity.development"
QUESTION = "Compare the complete matched opportunity menu using the unchanged selected response predictor and original independent assay."
RECORDS = {"evidence": MatrixSelectedOpportunityEvidence, "design": MatrixSelectedOpportunitySeal, "source": MatrixPreparationSource,
    "allocation": ScheduledAllocation, "history": MatrixPreparationHistory, "numerical": MatrixPreparationAssessment,
    "witness": MatrixPreparedFactorWitness, "frames": MatrixPreparedFrameAssessment, "causal": MatrixPreparedCausalPrefix,
    "point-design": MatrixSelectedPointPayload, "point": MatrixSelectedPointForecast, "mechanical": MatrixPreparedMechanicalForecast,
    "protocol": ScheduledResponseProtocol, "responses": MatrixSelectedOpportunityFutureHistory}
OUTPUTS = {"design": MatrixSelectedOpportunitySeal, "history": MatrixPreparationHistory, "assess": MatrixPreparationAssessment,
    "measure": MatrixPreparedFactorWitness, "frames": MatrixPreparedFrameAssessment, "project": MatrixPreparedCausalPrefix,
    "point": MatrixSelectedPointForecast, "mechanical": MatrixPreparedMechanicalForecast, "responses": MatrixSelectedOpportunityFutureHistory,
    "response-score": MatrixPreparedResponseReadout}
BASE = ("source", "allocation", "initial-state", "history", "history-arrays", "causal", "point", "mechanical", "mechanical-arrays", "protocol")
INPUTS = {"design": ("evidence",), "history": ("source", "allocation", "initial-state", "design"),
    "assess": ("source", "allocation", "initial-state", "history", "history-arrays", "design"),
    "measure": ("source", "initial-state", "history", "history-arrays", "numerical", "design"),
    "frames": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "design"),
    "project": ("source", "initial-state", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "frames", "design"),
    "point": ("point-design", "witness", "diagnostic-arrays", "frames", "causal", "causal-arrays", "design"),
    "mechanical": ("protocol", "templates", "causal", "causal-arrays", "design"),
    "responses": (*BASE, "design"), "response-score": (*BASE, "causal-arrays", "templates", "responses", "response-arrays", "design"),
    "nominate": ("design", "points", "mechanicals", "readouts")}
FINAL_KINDS = {"points": MatrixSelectedPointForecast, "mechanicals": MatrixPreparedMechanicalForecast, "readouts": MatrixPreparedResponseReadout}


def global_node(programme, phase):
    return NAMESPACE + "." + phase + "." + public_programme(programme).fingerprint()


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityRootConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-root-config"
    config_id: str
    programme: MatrixSelectedOpportunityPublicProgramme
    phase: str
    evidence: ObjectIdentity | None = None
    evidence_size_bytes: int | None = None

    def __post_init__(self):
        if (type(self.programme) is not MatrixSelectedOpportunityPublicProgramme or self.phase != "nominate"
                or self.config_id != "config." + global_node(self.programme, self.phase)):
            raise ValueError("selected opportunity root changes its exact immutable programme or phase")
        if self.evidence is not None or self.evidence_size_bytes is not None:
            raise ValueError("selected nomination cannot replace original design evidence")


@dataclass(frozen=True, slots=True)
class MatrixSelectedOpportunityConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-opportunity-config"
    config_id: str
    programme: ObjectIdentity
    public_source: MatrixPreparedPublicSource
    phase: str

    def __post_init__(self):
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixSelectedOpportunityPublicProgramme.SCHEMA
                or type(self.public_source) is not MatrixPreparedPublicSource
                or self.phase not in ("measure", "frames", "project", "point", "mechanical")
                or self.config_id != "config." + NAMESPACE + "." + self.public_source.source.object_id + "." + self.phase):
            raise ValueError("selected opportunity leaf changes its exact seedless source and owning phase")


def phase_inputs(phase, version="1.0.0"):
    if version == "2.0.0" and phase in NATIVE:
        return (*INPUTS[phase], "native-provenance", "native-stream")
    if phase in NATIVE:
        raise ValueError("selected native phase requires its current direct-input contract")
    return INPUTS[phase]


def phase_of(config):
    if type(config) not in (MatrixSelectedOpportunityRootConfig, MatrixSelectedOpportunityRootConfigV2, MatrixSelectedOpportunityConfig,
            MatrixSelectedOpportunityFutureConfig, preparation.MatrixPreparationOperationConfig, preparation.MatrixPreparationOperationConfigV2, MatrixSelectedOpportunityFutureConfigV2):
        raise TypeError("selected opportunity requires an exact owning configuration")
    config.__post_init__()
    if config.phase in NATIVE and type(config) not in preparation.native_config_types():
        raise ValueError("selected native phase requires its current direct-input contract")
    return config.phase


def task_id(config):
    return config.config_id.removeprefix("config.")


def units(config):
    if type(config) in (MatrixSelectedOpportunityRootConfig, MatrixSelectedOpportunityRootConfigV2):
        return tuple(group for group, _ in config.programme.panels)
    return ((config.public_source.original.root.independent_group_id,) if type(config) is MatrixSelectedOpportunityConfig
        else (config.source.root.root.independent_group_id,))


def digests(config):
    if type(config) in (MatrixSelectedOpportunityRootConfig, MatrixSelectedOpportunityRootConfigV2):
        return (config.programme.fingerprint(),)
    return preparation.operand_digests(config) if type(config) in (preparation.MatrixPreparationOperationConfig,
        preparation.MatrixPreparationOperationConfigV2) else (config.programme.object_fingerprint,)


def stage(phase):
    return (ScientificStage.ACQUIRE if phase in NATIVE else ScientificStage.FALSIFY if phase in ("assess", "frames", "response-score", "nominate")
        else ScientificStage.FREEZE if phase in ("design", "point", "mechanical") else ScientificStage.TRANSFORM)


def slots(config):
    return preparation.slots(config) if phase_of(config) == "history" else ("responses." + config.source.source_id,)


@dataclass(frozen=True, slots=True)
class _Factory:
    phase: str
    version: str = "1.0.0"

    def __call__(self):
        from .selected_opportunity_workers import SelectedOpportunityWorker
        declaration = next(row for row in operation_declarations()
            if (row.capability_key, row.capability_version) == (capability_key(self.phase, self.version), self.version))
        return SelectedOpportunityWorker(self.phase, declaration.manifest())


def prepare_for_invocation(supplier, runner):
    callback = getattr(supplier, "prepare_selected_opportunity", None)
    if not callable(callback):
        raise PermissionError("selected opportunity requires current issued original-product custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner), native_effect=runner.phase in NATIVE)


def prepare_native_work(*, runner, context, expected_parent):
    return runner.prepare_native_work(context, expected_parent=expected_parent)


def config_input_parents(config,all_config_records):
    from .selected_prepared_parent_projection import prepared_config_parents
    import sys
    return prepared_config_parents(config,all_config_records,owner=sys.modules[__name__],
        root_types=(MatrixSelectedOpportunityRootConfigV2,),root_phase="design")


@lru_cache(maxsize=1)
def operation_declarations():
    codecs = {kind.SCHEMA: kind for kind in (*RECORDS.values(), *FINAL_KINDS.values(), *OUTPUTS.values(),
        preparation.MatrixPreparationOperationConfig, MatrixSelectedOpportunityRootConfig, MatrixSelectedOpportunityConfig,
        MatrixSelectedOpportunityFutureConfig, MatrixSelectedOpportunityManifest, MatrixPreparationNomination)}
    declarations = []
    for phase in PHASES:
        inputs = tuple(sorted((RecursivePortContract(name, MATRIX_ARRAY_SCHEMA if (kind := MatrixSelectedOpportunityEvidenceV2 if phase == "design" else FINAL_KINDS.get(name, RECORDS.get(name))) is None else kind.SCHEMA,
            "application/x-npz" if kind is None else "application/json", MAXIMUM_MATRIX_ARRAY_BYTES if kind is None else None,
            minimum_count=1, maximum_count=None if name in FINAL_KINDS else 1) for name in INPUTS[phase]), key=lambda row: row.port_id))
        outputs = ((OutputTemplate("manifest", MatrixSelectedOpportunityManifest.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("product", MatrixPreparationNomination.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")) if phase == "nominate" else
            (OutputTemplate("product", OUTPUTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),))
        if phase in ARRAY_OUTPUTS:
            outputs += (OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),)
        config = (MatrixSelectedOpportunityRootConfigV2 if phase == "design" else MatrixSelectedOpportunityRootConfig if phase == "nominate" else preparation.MatrixPreparationOperationConfig
            if phase in ("history", "assess") else MatrixSelectedOpportunityFutureConfig if phase in ("responses", "response-score") else MatrixSelectedOpportunityConfig)
        version = "2.0.0" if phase == "design" else "1.0.0"
        implementation = NAMESPACE + (".design.original-commitments.v2" if phase == "design" else "." + phase + ".selected-original-science.v1")
        selected_codecs = {**codecs, MatrixSelectedOpportunityEvidenceV2.SCHEMA: MatrixSelectedOpportunityEvidenceV2,
            MatrixSelectedOpportunityRootConfigV2.SCHEMA: MatrixSelectedOpportunityRootConfigV2} if phase == "design" else codecs
        declarations.append(RecursiveOperationDeclaration(NAMESPACE + "." + phase if phase in NATIVE else capability_key(phase, version), version, implementation,
            CapabilityKind.SIMULATOR if phase in NATIVE else CapabilityKind.FALSIFIER if stage(phase) is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
            config, stage(phase), inputs, tuple(sorted(outputs, key=lambda row: row.output_id)),
            tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_OUTCOME_VISIBLE, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_FROZEN_MODELS))),
            EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, preparation.BUDGET,
            ("actual-original-selected-product-custody", "complete16x3-matched-opportunity", "selected-point-before-native-future"), _Factory(phase, version), selected_codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=units, scientific_operand_sha256s=digests,
                native_effect_slot_ids=slots if phase in NATIVE else None, scientific_root_validator=scientific_root_validator),
            execution_properties=RecursiveExecutionProperties(native_effect=phase in NATIVE, complete_unit_census=phase in NATIVE,
                native_work_preparer=prepare_native_work if phase in NATIVE else None, runner_preparation_factory=prepare_for_invocation,
                barrier=BarrierKind.FREEZE if stage(phase) is ScientificStage.FREEZE else BarrierKind.NONE),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS))
    for index, base in enumerate(declarations):
        if base.capability_version == "1.0.0" and base.capability_key.endswith((".history", ".responses")):
            phase = "history" if base.capability_key.endswith(".history") else "responses"
            config_type = preparation.MatrixPreparationOperationConfigV2 if phase == "history" else MatrixSelectedOpportunityFutureConfigV2
            factory = _Factory(phase, "2.0.0")
            declarations[index] = preparation.direct_native_declaration(base, config_type=config_type,
                runner_factory=factory)
    return tuple(replace(value,config_input_parents=config_input_parents) for value in
        sorted(declarations,key=lambda row:(row.capability_key,row.capability_version)))


@lru_cache(maxsize=2)
def contracts(programme, evidence_pin, evidence_size, *, produced_input_parents=()):
    programme = public_programme(programme)
    if evidence_pin.object_schema != MatrixSelectedOpportunityEvidenceV2.SCHEMA:
        raise ValueError("selected opportunity graph requires current commitment-bearing evidence")
    configs, external, records, arrays, links = {}, {}, {}, {}, []
    def add(name, value, object_id):
        row = RecursiveExternalInput(name, object_id, value.SCHEMA, "application/json", len(value.canonical_bytes()),
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, value.fingerprint(), "SOURCE")
        if external.setdefault(name, row) != row or records.setdefault(name, value) != value:
            raise ValueError("selected opportunity aliases distinct original record identities")
        return name
    def array(name, artifact):
        row = RecursiveExternalInput(name, artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, artifact.sha256, "SOURCE")
        if external.setdefault(name, row) != row or arrays.setdefault(name, artifact) != artifact:
            raise ValueError("selected opportunity aliases distinct original file identities")
        return name
    def edge(node, name, *, external_id=None, producer=None, output="product"):
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=external_id,
            producer_node_id=producer, producer_output_id=output if producer is not None else None, scientific_role="SOURCE" if producer is None else "HISTORY"))
    for phase in ("design", "nominate"):
        node = global_node(programme, phase)
        kind = MatrixSelectedOpportunityRootConfigV2 if phase == "design" else MatrixSelectedOpportunityRootConfig
        configs[node] = kind("config." + node, programme, phase,
            evidence_pin if phase == "design" else None, evidence_size if phase == "design" else None,
            **({"produced_input_parents": produced_input_parents} if kind is MatrixSelectedOpportunityRootConfigV2 else {}))
    design, final = (global_node(programme, phase) for phase in ("design", "nominate"))
    evidence_id = "external.selected-opportunity-evidence." + evidence_pin.object_fingerprint
    external[evidence_id] = RecursiveExternalInput(evidence_id, evidence_pin.object_id, evidence_pin.object_schema, "application/json", evidence_size,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, evidence_pin.object_fingerprint, "SOURCE")
    edge(design, "evidence", external_id=evidence_id)
    point_id = add("external.selected-opportunity-point." + programme.point_design.fingerprint(), programme.point_design, programme.point_design.record_id)
    templates = array("external.selected-opportunity-templates." + programme.assay.template_artifact.fingerprint(), programme.assay.template_artifact)
    allocations = {ObjectIdentity.from_record(row.allocation_id, row): row for row in programme.sources.allocations}
    for source in programme.sources.sources:
        allocation, protocol = allocations[source.original.allocation], programme.protocol(source)
        source_id = add("external.selected-opportunity-source." + source.source_id, source, source.source_id)
        allocation_id = add("external.selected-opportunity-allocation." + allocation.fingerprint(), allocation, allocation.allocation_id)
        protocol_id = add("external.selected-opportunity-protocol." + protocol.fingerprint(), protocol, protocol.protocol_id)
        initial = array("external.selected-opportunity-initial." + source.initial.array_artifact.fingerprint(), source.initial.array_artifact)
        public = MatrixPreparedPublicSource.from_source(source)
        nodes = {phase: preparation.node_id(source, phase) if phase in ("history", "assess") else node_id(source, phase)
            for phase in PHASES if phase not in ("design", "nominate")}
        for phase, node in nodes.items():
            configs[node] = ((preparation.MatrixPreparationOperationConfigV2 if phase == "history" else preparation.MatrixPreparationOperationConfig)("config." + node, phase, source, len(allocation.canonical_bytes()))
                if phase in ("history", "assess") else (MatrixSelectedOpportunityFutureConfigV2 if phase == "responses" else MatrixSelectedOpportunityFutureConfig)("config." + node, programme.identity, source, protocol,
                    dict(programme.panels)[source.root.root.independent_group_id], programme.point_design.identity, package_identity(programme.point_design.package), phase)
                if phase in ("responses", "response-score") else MatrixSelectedOpportunityConfig("config." + node, programme.identity, public, phase))
            incoming = {"source": source_id, "allocation": allocation_id, "initial-state": initial, "point-design": point_id, "protocol": protocol_id, "templates": templates}
            produced = {"design": (design, "product"), "history": (nodes["history"], "product"), "history-arrays": (nodes["history"], "arrays"),
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
    edge(final, "design", producer=design)
    external = inherit_external_inputs(tuple(sorted(external.values(), key=lambda row: row.input_id)),
        (*records.items(), (evidence_id, tuple(value.identity for value in produced_input_parents))), produced_input_parents,
        retained_history=True)
    links = inherit_external_links(links, external)
    return (tuple(sorted(configs.items())), external,
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(records.items())), tuple(sorted(arrays.items())))


def development_root(programme, study_id):
    programme = public_programme(programme)
    groups = tuple(group for group, _ in programme.panels)
    views = tuple(sorted({view.view_id for source in programme.sources.sources for view in (source.primary_view, source.fine_view)}))
    claim = ClaimSpec("claim." + study_id, WORLD, "population.matrix-selected-opportunity", QUESTION,
        "Every selected whole group and all three matched recipes, including missing/nonuse outcomes and the frozen nomination rule.",
        "unit.original-whole-group", None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Exposed functional opportunity only; no protected entry, downstream applicability or scientific qualification.",
        ("assumption.matrix-selected-opportunity.original-coupling-only-physics",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, programme.original_programme, WORLD, WorldKind.NUMERICAL_SIMULATOR, groups, views,
        (claim,), tuple(sorted({programme.identity, programme.original_programme, package_identity(programme.point_design.package), programme.sources.identity,
            *(operand for source in programme.sources.sources for operand in preparation.operands(source))}, key=lambda row: row.object_id)))


def scientific_root_validator(config, context):
    if type(context) is not RecursiveScientificRootContext or type(context.root) is not DevelopmentStudySpec:
        raise TypeError("selected opportunity requires its actual exposed development compiler root")
    roots = tuple(row.record for row in context.config_inputs if type(row.record) in (MatrixSelectedOpportunityRootConfig, MatrixSelectedOpportunityRootConfigV2) and row.record.phase == "design")
    if len(roots) != 1:
        raise ValueError("selected opportunity requires one complete original-product design root")
    root, = roots
    configs, external, links, _, _ = contracts(root.programme, root.evidence, root.evidence_size_bytes,
        produced_input_parents=root.produced_input_parents if type(root) is MatrixSelectedOpportunityRootConfigV2 else ())
    phase, node = phase_of(config), task_id(config)
    if (tuple((row.node_id, row.record) for row in context.config_inputs) != configs or dict(configs).get(node) != config or context.node_id != node
            or tuple(context.external_inputs) != external or tuple(context.links) != links
            or context.root != development_root(root.programme, context.root.study_id) or context.stage is not stage(phase)
            or context.unit_ids != units(config) or context.selected_unit_ids != units(root) or context.complete_unit_census != (phase in NATIVE)
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("selected opportunity changes complete original graph, source/case census, access or frozen nomination")


@dataclass(frozen=True, slots=True)
class LoweredSelectedOpportunity:
    draft: RecursiveStudyDraft
    input_records: tuple
    input_artifacts: tuple


def lower_selected_opportunity(programme, *, evidence, campaign, draft_id, resources=None, produced_input_parents=()):
    from .selected_operational_resources import selected_phase_budgets

    budgets = selected_phase_budgets(resources, family="OPPORTUNITY")
    programme = public_programme(programme)
    validate_opportunity_evidence(evidence, programme)
    configs, external, links, records, arrays = contracts(programme, evidence.identity, len(evidence.canonical_bytes()), produced_input_parents=produced_input_parents)
    records = tuple(sorted((*records, ("external.selected-opportunity-evidence." + evidence.fingerprint(), evidence))))
    declarations = {(row.capability_key, row.capability_version): row for row in operation_declarations()}
    def selected(config):
        version = "2.0.0" if type(config) in (*preparation.native_config_types(), MatrixSelectedOpportunityRootConfigV2) else "1.0.0"
        return declarations[(capability_key(phase_of(config), version), version)]
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node, selection=selected(config).registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=budgets[phase_of(config)]) for node, config in configs)
    study = development_root(programme, "study." + draft_id)
    selected_campaign = replace(campaign, objective=QUESTION, system_ids=(programme.original_programme.object_id,), world_ids=(WORLD,),
        target_claim_ids=tuple(row.claim_id for row in study.claims))
    draft = RecursiveStudyDraft(draft_id, QUESTION, selected_campaign, (), (), (), operations, external, links,
        tuple(node for node, _ in configs), development_study=study)
    return LoweredSelectedOpportunity(draft, records, arrays)
