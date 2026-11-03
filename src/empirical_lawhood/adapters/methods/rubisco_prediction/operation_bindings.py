# SPDX-License-Identifier: MPL-2.0
"""Three cold registered information stages on the shared recursive runtime."""

from empirical_lawhood.adapters.physical.rubisco_kinetics.iqbal2023 import IqbalTrainingTableV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import Mcdonald2026PanelV1
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from . import knn, records as r
from .operation_contracts import (
    ANALYSIS_UNIT_ID, SOURCE_IDS, PlantPredictionAnalysisSystemV1,
    PlantPredictionConstructConfigV1, PlantPredictionEvaluateConfigV1,
    PlantPredictionScienceV1, PlantPredictionSourceConfigV1,
)

NAMESPACE = "rubisco-plant-prediction.phases"
MEDIA_TYPE = "application/json"
MAX_BYTES = 64 * 1024**2
CONFIG_MAX_BYTES = 64 * 1024
NODE_IDS = {role: f"rubisco.plant-prediction.{role}" for role in ("source", "construct", "evaluate")}
BUDGETS = {
    "source": ResourceBudget(1, 1024**3, 0, 60, 7 * 1024**2, 8 * 1024**2),
    "construct": ResourceBudget(1, 1024**3, 0, 420, 25 * 1024**2, MAX_BYTES),
    "evaluate": ResourceBudget(1, 1024**3, 0, 120, 73 * 1024**2, 1024**2),
}
TOTAL_BUDGET = ResourceBudget(1, 1024**3, 0, 600, 105 * 1024**2, 128 * 1024**2)
SOURCE_OUTPUTS = (("anchors", r.PlantParentAnchorsV1), ("labels", r.PlantLabelsV1),
                  ("queries", r.PlantQueriesV1), ("training", r.NaturalTrainingV1))
PHASES = (
    ("source", PlantPredictionSourceConfigV1,
     (("natural", IqbalTrainingTableV1, 2 * 1024**2), ("plant", Mcdonald2026PanelV1, 4 * 1024**2)),
     SOURCE_OUTPUTS, CapabilityKind.OBSERVATION_OPERATOR, ScientificStage.TRANSFORM),
    ("construct", PlantPredictionConstructConfigV1,
     (("anchors", r.PlantParentAnchorsV1, 128 * 1024), ("queries", r.PlantQueriesV1, 128 * 1024),
      ("training", r.NaturalTrainingV1, 4 * 1024**2)),
     (("commitment", r.PlantCommitmentV1),), CapabilityKind.TRANSFORM, ScientificStage.FREEZE),
    ("evaluate", PlantPredictionEvaluateConfigV1,
     (("commitment", r.PlantCommitmentV1, MAX_BYTES), ("labels", r.PlantLabelsV1, 1024**2)),
     (("evaluation", r.PlantEvaluationV1),), CapabilityKind.FALSIFIER, ScientificStage.FALSIFY),
)


def scientific_design():
    return PlantPredictionScienceV1(r.PREFIX + ".scientific-design", r.natural_identity(),
                                    r.plant_identity(), r.PROTOCOL_SHA256)


def prepare_source(config, natural_table, plant_panel):
    """Authenticate native typed witnesses and project closed information roles."""
    if type(config) is not PlantPredictionSourceConfigV1 or config.science != scientific_design():
        raise ValueError("plant source changes its exact frozen design")
    if (type(natural_table) is not IqbalTrainingTableV1 or type(plant_panel) is not Mcdonald2026PanelV1
            or ObjectIdentity.from_record(SOURCE_IDS[0], natural_table) != config.science.natural_table
            or ObjectIdentity.from_record(SOURCE_IDS[1], plant_panel) != config.science.plant_panel):
        raise ValueError("plant source requires its exact sealed native table and panel")
    natural_table.__post_init__()
    plant_panel.__post_init__()
    training = knn.prepare_training(natural_table)
    queries, anchors, labels = knn.prepare_plant_roles(plant_panel)
    return (("anchors", anchors), ("labels", labels), ("queries", queries), ("training", training))


def scientific_operand_sha256s(config):
    return tuple(sorted({config.science.fingerprint(), config.science.natural_table.object_fingerprint,
                         config.science.plant_panel.object_fingerprint, config.science.protocol_sha256}))


def scientific_unit_ids(config):
    return (ANALYSIS_UNIT_ID,)


def prediction_development_root(science, *, study_id=None):
    if type(science) is not PlantPredictionScienceV1 or science != scientific_design():
        raise ValueError("plant prediction root requires its exact frozen exposed design")
    identity = ObjectIdentity.from_record(science.science_id, science)
    system = PlantPredictionAnalysisSystemV1(science.science_id + ".analysis-system", identity,
                                           science.natural_table, science.plant_panel)
    world_id, view = science.science_id + ".analysis-world", science.science_id + ".exposed-point-means"
    claim = ClaimSpec(science.science_id + ".parent-anchored-point-assessment", world_id,
        science.science_id + ".complete-plant-panel",
        "Natural-only genus-tuned and fixed-1NN parent-anchored forecasts are compared with no change on both intrinsic endpoint point responses; adverse, equal and degenerate predictions remain retained.",
        "One exposed analytical assessment: nine focal rows nested within six sites, plus a separate A369V diagnostic; 183 natural source associations and unknown independent biological n.",
        ANALYSIS_UNIT_ID, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "The exposed finite point assessment supplies no calibrated uncertainty, unseen-edit qualification, SSU-edit response, EL advantage or nomination readiness.",
        ("already-exposed-natural-and-mutant-sources", "complete-distance-boundary-ties",
         "natural-only-leave-genus-out-tuning", "unknown-biological-n-and-endpoint-pairing"),
        numerical_view_ids=(view,))
    protocol = ObjectIdentity("rubisco.plant-prediction.protocol-v1",
        "empirical-lawhood/rubisco/exposed-plant-prediction-protocol", "1.0.0", science.protocol_sha256)
    operands = tuple(sorted((identity, science.natural_table, science.plant_panel, protocol), key=lambda v: v.object_id))
    return DevelopmentStudySpec(study_id or science.science_id + ".development-study",
        "Does the frozen natural-only LSU predictor improve both parent-anchored mutant point-response errors over no change in the complete exposed panel?",
        ObjectIdentity.from_record(system.system_id, system), world_id, WorldKind.ANALYTIC_REFERENCE,
        (ANALYSIS_UNIT_ID,), (view,), (claim,), operands)


def scientific_root_validator(config, context):
    row = next((row for row in PHASES if row[1] is type(config)), None)
    if row is None or type(context.root) is not DevelopmentStudySpec:
        raise ValueError("plant stage requires its genuine exposed analytical root")
    expected = prediction_development_root(config.science, study_id=context.root.study_id)
    if context.root.canonical_bytes() != expected.canonical_bytes():
        raise ValueError("plant stage substitutes its source, protocol, claim, root or analytical census")
    if (context.stage is not row[5] or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.unit_ids != (ANALYSIS_UNIT_ID,) or context.selected_unit_ids != (ANALYSIS_UNIT_ID,)
            or context.complete_unit_census):
        raise ValueError("plant stage changes its exact stage, access or analytical unit")
    configs = {value.node_id: value.record for value in context.config_inputs}
    kinds = {NODE_IDS[row[0]]: row[1] for row in PHASES}
    if (set(configs) != set(kinds) or len(context.config_inputs) != 3
            or any(type(configs[node]) is not kind or configs[node].config_id != f"config.{node}"
                   or configs[node].science != config.science for node, kind in kinds.items())
            or context.node_id != NODE_IDS[row[0]] or configs.get(context.node_id) != config):
        raise ValueError("plant stage changes its complete three-stage configuration census")
    links = {
        "source": {"natural": (None, None, "SOURCE"), "plant": (None, None, "SOURCE")},
        "construct": {"training": (NODE_IDS["source"], "training", "SOURCE"),
                      "queries": (NODE_IDS["source"], "queries", "SOURCE"),
                      "anchors": (NODE_IDS["source"], "anchors", "SOURCE")},
        "evaluate": {"commitment": (NODE_IDS["construct"], "commitment", "ACTION"),
                     "labels": (NODE_IDS["source"], "labels", "OUTCOME")},
    }[row[0]]
    incoming = tuple(link for link in context.links if link.consumer_node_id == context.node_id)
    if len(incoming) != len(links) or {link.consumer_input_id for link in incoming} != set(links):
        raise ValueError("plant stage changes its closed information-role or commitment dependency census")
    for link in incoming:
        producer, output, role = links[link.consumer_input_id]
        if (link.producer_node_id, link.producer_output_id, link.scientific_role) != (producer, output, role):
            raise ValueError("plant stage substitutes a source/commitment/label role")
        expected_external = "external." + SOURCE_IDS[0 if link.consumer_input_id == "natural" else 1] if producer is None else None
        if link.external_input_id != expected_external:
            raise ValueError("plant stage changes its exact external native source or dependency role")


def output_codecs():
    return {record.SCHEMA: record for record in (IqbalTrainingTableV1, Mcdonald2026PanelV1,
        *r.RECORD_TYPES, *(row[1] for row in PHASES))}


class PlantPredictionOperationRunner:
    """Stateless, path-free worker with exact source roles and pre-label proof."""

    def __init__(self, *, manifest, role):
        self.manifest, self.role = manifest, role
        self.row = next(row for row in PHASES if row[0] == role)

    def execute(self, context):
        role, config_type, input_specs, output_specs, _, _ = self.row
        try:
            maxima = {config_type.SCHEMA: CONFIG_MAX_BYTES,
                      **{record.SCHEMA: maximum for _, record, maximum in input_specs}}
            if (context.task_id != NODE_IDS[role] or context.config.config_schema != config_type.SCHEMA
                    or len(context.input_ports) != len(input_specs) + 1
                    or not self.manifest.resource_ceiling.contains(context.resource_budget)
                    or any(port.payload_schema not in maxima or port.media_type != MEDIA_TYPE
                           or port.size_bytes > maxima.get(port.payload_schema, 0) for port in context.input_ports)):
                raise ValueError("plant worker receives undeclared, missing or unbounded information roles")
            ports = {schema: tuple(port for port in context.input_ports if port.payload_schema == schema) for schema in maxima}
            if any(len(value) != 1 for value in ports.values()) or ports[config_type.SCHEMA][0].kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("plant worker changes exact one-per-role input cardinality")
            kind = WorkerInputKind.EXTERNAL if role == "source" else WorkerInputKind.DEPENDENCY
            if any(ports[record.SCHEMA][0].kind is not kind for _, record, _ in input_specs):
                raise ValueError("plant worker requires exact external sources or receipt-bound predecessors")
            predecessors = {"construct": {"anchors": "source", "queries": "source", "training": "source"},
                            "evaluate": {"commitment": "construct", "labels": "source"}}.get(role, {})
            for name, record, _ in input_specs:
                if name in predecessors:
                    port = ports[record.SCHEMA][0]
                    receipts = tuple(receipt for receipt in context.dependency_receipts
                                     if port.materialization_id in receipt.output_materialization_ids)
                    if len(receipts) != 1 or receipts[0].task_id != NODE_IDS[predecessors[name]]:
                        raise ValueError("plant worker substitutes its exact receipt-bound upstream stage")
            outputs = context.output_ports
            if (tuple((port.output_id, port.payload_schema) for port in outputs)
                    != tuple((f"{context.task_id}.{name}", record.SCHEMA) for name, record in output_specs)
                    or any(port.profile is not ArtifactProfile.CANONICAL_JSON or port.media_type != MEDIA_TYPE for port in outputs)):
                raise ValueError("plant worker changes its exact task-prefixed typed output census")

            def read(record_type):
                port = ports[record_type.SCHEMA][0]
                payload = port.read(maxima[record_type.SCHEMA] + 1)
                if len(payload) != port.size_bytes:
                    raise ValueError("plant input differs from its bounded materialization")
                return decode_canonical_bytes(payload, record_type, maximum_bytes=maxima[record_type.SCHEMA])

            config = read(config_type)
            config_port = ports[config_type.SCHEMA][0]
            if (config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id
                    or config.config_id != f"config.{NODE_IDS[role]}" or config_port.artifact_id != context.config.artifact_id):
                raise ValueError("plant worker changes its immutable selected configuration")
            if role == "source":
                named = prepare_source(config, read(IqbalTrainingTableV1), read(Mcdonald2026PanelV1))
            elif role == "construct":
                training, queries, anchors = read(r.NaturalTrainingV1), read(r.PlantQueriesV1), read(r.PlantParentAnchorsV1)
                model = knn.fit(training)
                forecast = knn.predict(model, queries, anchors)
                named = (("commitment", knn.commit(forecast)),)
            else:
                commitment = read(r.PlantCommitmentV1)
                knn.validate_commitment(commitment)
                # This read occurs only after complete global source/distance proof.
                named = (("evaluation", knn.evaluate(commitment, read(r.PlantLabelsV1))),)
            if tuple((name, type(record)) for name, record in named) != output_specs:
                raise ValueError("plant worker changes its complete typed output record census")
            payloads = tuple(TaskOutputPayload(port.output_id, record.canonical_bytes())
                             for port, (_, record) in zip(outputs, named, strict=True))
            if any(len(value.payload) > MAX_BYTES for value in payloads) or sum(len(value.payload) for value in payloads) > context.resource_budget.output_bytes:
                raise ValueError("plant worker exceeds its frozen output byte budget")
            return RunnerResult(payloads, (ReceiptCheck("valid-complete-exposed-plant-prediction-stage", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    """Derive cold and executable projections from each scientific stage."""
    def declare(row):
        role, config, inputs, outputs, kind, stage = row

        def runner():
            return PlantPredictionOperationRunner(manifest=declaration.manifest(), role=role)

        declaration = RecursiveOperationDeclaration(
            capability_key=f"{NAMESPACE}.{role}", capability_version="1.0.0",
            implementation_id="parent-anchored-exposed-plant-prediction-three-stages-v1", kind=kind,
            config_record_type=config, stage=stage,
            # Dependency edges retain the supplier's task-total output ceiling;
            # workers retain the narrower role read bounds.
            input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA_TYPE,
                max(maximum, BUDGETS["source"].output_bytes)
                if role != "source" and name != "commitment" else maximum)
                for name, record, maximum in inputs),
            outputs=tuple(OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                MEDIA_TYPE, ".json") for name, record in outputs),
            permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGETS[role],
            conformance_check_ids=('global-commitment-before-mutant-label-read', 'natural-only-construction-information-roles'),
            runner_factory=runner, record_codecs=output_codecs(),
            scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=scientific_operand_sha256s,
                scientific_unit_ids=scientific_unit_ids,
                scientific_root_validator=scientific_root_validator),
            execution_properties=RecursiveExecutionProperties(
                barrier=BarrierKind.FREEZE if role == "construct" else BarrierKind.NONE))
        return declaration

    return tuple(declare(row) for row in PHASES)
