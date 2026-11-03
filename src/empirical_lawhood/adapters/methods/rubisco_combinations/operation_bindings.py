# SPDX-License-Identifier: MPL-2.0
"""Cold registered Wilson stages on the shared compiler/provider/custody route."""

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

from . import analysis
from .operation_contracts import (
    ANALYSIS_UNIT_ID, CombinationAnalysisSystemV1, CombinationCommitConfigV1, CombinationEvaluateConfigV1,
    CombinationPredictConfigV1, CombinationSourceConfigV1,
)
from .records import (
    CombinationCommitmentV1, CombinationEvaluationV1, CombinationFeaturesV1, CombinationForecastV1,
    CombinationLabelsV1, CombinationScienceV1, CombinationTrainingV1,
)
from .source_binding import (
    PROTOCOL_SHA256, SOURCE_OUTPUTS, TeParentGenbankInputV1, WilsonArticleInputV1, prepare_source,
)

NAMESPACE = "rubisco-combinations.phases"
MEDIA_TYPE = "application/json"
MAX_BYTES = 4 * 1024**2
BUDGET = ResourceBudget(1, 1024**3, 0, 600, 16 * 1024**2, MAX_BYTES)
NODE_IDS = {role: f"rubisco.combinations.{role}" for role in ("source", "predict", "commit", "evaluate")}
PHASES = (
    ("source", CombinationSourceConfigV1,
     (("article", WilsonArticleInputV1), ("genbank", TeParentGenbankInputV1)), SOURCE_OUTPUTS,
     CapabilityKind.OBSERVATION_OPERATOR, ScientificStage.TRANSFORM),
    ("predict", CombinationPredictConfigV1,
     (("features", CombinationFeaturesV1), ("training", CombinationTrainingV1)),
     (("forecast", CombinationForecastV1),), CapabilityKind.TRANSFORM, ScientificStage.DEVELOP),
    ("commit", CombinationCommitConfigV1, (("forecast", CombinationForecastV1),),
     (("commitment", CombinationCommitmentV1),), CapabilityKind.TRANSFORM, ScientificStage.FREEZE),
    ("evaluate", CombinationEvaluateConfigV1,
     (("commitment", CombinationCommitmentV1), ("labels", CombinationLabelsV1)),
     (("evaluation", CombinationEvaluationV1),), CapabilityKind.FALSIFIER, ScientificStage.FALSIFY),
)


def scientific_operand_sha256s(config):
    return tuple(sorted({config.science.fingerprint(), config.science.source_panel.object_fingerprint,
                         config.science.parent.object_fingerprint, config.science.protocol_sha256}))


def scientific_unit_ids(config):
    return (ANALYSIS_UNIT_ID,)


def combinations_development_root(science: CombinationScienceV1, *, study_id=None):
    if type(science) is not CombinationScienceV1 or science.protocol_sha256 != PROTOCOL_SHA256:
        raise ValueError("combination root requires its exact frozen exposed assessment design")
    identity = ObjectIdentity.from_record(science.science_id, science)
    system = CombinationAnalysisSystemV1(f"{science.science_id}.analysis-system", identity, science.source_panel, science.parent)
    world_id = f"{science.science_id}.analysis-world"
    view = f"{science.science_id}.exposed-point-means"
    claim = ClaimSpec(f"{science.science_id}.conventional-joint-point-decision", world_id,
        f"{science.science_id}.reported-combination",
        "The frozen conventional three-corner forecast's uncompensated joint point-improvement decision agrees with the source-bound combined target; continuous endpoint errors and parent contrasts remain reported.",
        "One exposed combined-target contrast from four declared source corners, with an additive forecast and parent baseline; nineteen source enzymes remain context, and independent biological n is unknown.",
        ANALYSIS_UNIT_ID, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Agreement of an exposed conventional point decision creates no calibrated accuracy, biological qualification, unseen-edit sensitivity, EL advantage or nomination readiness.",
        ("exposed-selected-source-quartet", "fixed-zero-log-interaction-rule", "unknown-cross-assay-pairing"),
        numerical_view_ids=(view,))
    protocol = ObjectIdentity("rubisco.assessment-protocol.wilson-combination-v1",
        "empirical-lawhood/rubisco/exposed-assessment-protocol", "1.0.0", science.protocol_sha256)
    operands = tuple(sorted((identity, science.source_panel, science.parent, protocol), key=lambda v: v.object_id))
    return DevelopmentStudySpec(study_id or f"{science.science_id}.development-study",
        "Does the conventional three-corner calculation preserve the exposed combined target's uncompensated joint point-improvement decision?",
        ObjectIdentity.from_record(system.system_id, system), world_id, WorldKind.ANALYTIC_REFERENCE,
        (ANALYSIS_UNIT_ID,), (view,), (claim,), operands)


def scientific_root_validator(config, context):
    row = next((r for r in PHASES if r[1] is type(config)), None)
    if row is None or type(context.root) is not DevelopmentStudySpec:
        raise ValueError("combination stage requires its genuine exposed analytical root")
    expected = combinations_development_root(config.science, study_id=context.root.study_id)
    if context.root.canonical_bytes() != expected.canonical_bytes():
        raise ValueError("combination stage substitutes its exact root, protocol, claims, source or assigned census")
    if (context.stage is not row[5] or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.unit_ids != (ANALYSIS_UNIT_ID,) or context.selected_unit_ids != (ANALYSIS_UNIT_ID,)
            or context.complete_unit_census):
        raise ValueError("combination stage changes its exact stage, access or software contrast census")
    configs = {v.node_id: v.record for v in context.config_inputs}
    expected_types = {NODE_IDS[r[0]]: r[1] for r in PHASES}
    if (set(configs) != set(expected_types) or len(context.config_inputs) != 4
            or any(type(configs[node]) is not kind or configs[node].config_id != f"config.{node}"
                   or configs[node].science != config.science for node, kind in expected_types.items())
            or context.node_id != NODE_IDS[row[0]] or configs.get(context.node_id) != config):
        raise ValueError("combination stage changes its complete four-stage configuration/source census")
    expected_links = {
        "source": {"article": (None, None, "SOURCE"), "genbank": (None, None, "SOURCE")},
        "predict": {"features": (NODE_IDS["source"], "features", "SOURCE"),
                    "training": (NODE_IDS["source"], "training", "SOURCE")},
        "commit": {"forecast": (NODE_IDS["predict"], "forecast", "MODEL")},
        "evaluate": {"commitment": (NODE_IDS["commit"], "commitment", "ACTION"),
                     "labels": (NODE_IDS["source"], "labels", "OUTCOME")},
    }[row[0]]
    incoming = tuple(v for v in context.links if v.consumer_node_id == context.node_id)
    if len(incoming) != len(expected_links) or {v.consumer_input_id for v in incoming} != set(expected_links):
        raise ValueError("combination stage changes its closed information-role or commitment dependency census")
    for link in incoming:
        producer, output, role = expected_links[link.consumer_input_id]
        if (link.producer_node_id, link.producer_output_id, link.scientific_role) != (producer, output, role):
            raise ValueError("combination stage substitutes a source/model/label role or skips commitment")
        if (link.external_input_id is not None) is not (producer is None):
            raise ValueError("combination stage changes its exact external/dependency source role")


def output_codecs():
    records = (WilsonArticleInputV1, TeParentGenbankInputV1,
               *(record for row in PHASES for _, record in row[2]),
               *(record for row in PHASES for _, record in row[3]))
    return {record.SCHEMA: record for record in records}


class CombinationOperationRunner:
    """A stateless path-free worker reading only registered typed information roles."""

    def __init__(self, *, manifest, role):
        self.manifest, self.role = manifest, role
        self.row = next(r for r in PHASES if r[0] == role)

    def execute(self, context):
        role, config_type, input_specs, output_specs, _, _ = self.row
        try:
            allowed = {config_type.SCHEMA, *(record.SCHEMA for _, record in input_specs)}
            if (context.task_id != NODE_IDS[role] or context.config.config_schema != config_type.SCHEMA
                    or len(context.input_ports) != len(input_specs) + 1
                    or any(p.payload_schema not in allowed or p.media_type != MEDIA_TYPE or p.size_bytes > MAX_BYTES
                           for p in context.input_ports)):
                raise ValueError("combination worker receives undeclared, missing or unbounded information roles")
            ports = {schema: tuple(p for p in context.input_ports if p.payload_schema == schema) for schema in allowed}
            if any(len(v) != 1 for v in ports.values()) or ports[config_type.SCHEMA][0].kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("combination worker changes its exact one-per-role input cardinality")
            expected_kind = WorkerInputKind.EXTERNAL if role == "source" else WorkerInputKind.DEPENDENCY
            if any(ports[record.SCHEMA][0].kind is not expected_kind for _, record in input_specs):
                raise ValueError("combination worker requires its actual external sources or receipt-bound predecessors")
            predecessors = {"predict": {"features": "source", "training": "source"},
                            "commit": {"forecast": "predict"},
                            "evaluate": {"commitment": "commit", "labels": "source"}}.get(role, {})
            for name, record in input_specs:
                if name in predecessors:
                    port = ports[record.SCHEMA][0]
                    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
                    if len(receipts) != 1 or receipts[0].task_id != NODE_IDS[predecessors[name]]:
                        raise ValueError("combination worker substitutes an exact receipt-bound upstream stage")
            outputs = context.output_ports
            if (tuple((p.output_id, p.payload_schema) for p in outputs)
                    != tuple((f"{context.task_id}.{name}", record.SCHEMA) for name, record in output_specs)
                    or any(p.profile is not ArtifactProfile.CANONICAL_JSON or p.media_type != MEDIA_TYPE for p in outputs)):
                raise ValueError("combination worker changes its exact task-prefixed typed output census")

            def read(record_type):
                port = ports[record_type.SCHEMA][0]
                payload = port.read(MAX_BYTES + 1)
                if len(payload) != port.size_bytes:
                    raise ValueError("combination input differs from its bounded materialization")
                return decode_canonical_bytes(payload, record_type, maximum_bytes=MAX_BYTES)

            config = read(config_type)
            config_port = ports[config_type.SCHEMA][0]
            if (config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id
                    or config.config_id != f"config.{NODE_IDS[role]}" or config_port.artifact_id != context.config.artifact_id):
                raise ValueError("combination worker changes its immutable selected configuration")
            if role == "source":
                named = prepare_source(config, read(WilsonArticleInputV1), read(TeParentGenbankInputV1))
            elif role == "predict":
                product = analysis.predict(config.science, read(CombinationTrainingV1), read(CombinationFeaturesV1))
            elif role == "commit":
                product = analysis.commit(config.science, read(CombinationForecastV1))
            else:
                commitment = read(CombinationCommitmentV1)
                # Authenticate the complete forecast product before any label read.
                if analysis.commit(config.science, commitment.forecast_product) != commitment:
                    raise ValueError("combination evaluation changes its exact prior forecast commitment")
                product = analysis.evaluate(config.science, commitment, read(CombinationLabelsV1))
            if role != "source":
                named = ((output_specs[0][0], product),)
            if tuple((name, type(record)) for name, record in named) != output_specs:
                raise ValueError("combination worker changes its complete typed output record census")
            payloads = tuple(TaskOutputPayload(port.output_id, record.canonical_bytes())
                             for port, (_, record) in zip(outputs, named, strict=True))
            if any(len(v.payload) > MAX_BYTES for v in payloads) or sum(len(v.payload) for v in payloads) > context.resource_budget.output_bytes:
                raise ValueError("combination worker exceeds its frozen output byte budget")
            return RunnerResult(payloads, (ReceiptCheck("valid-complete-exposed-combination-stage", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    """Derive cold and executable projections from each scientific stage."""
    def declare(row):
        role, config, inputs, outputs, kind, stage = row

        def runner():
            return CombinationOperationRunner(manifest=declaration.manifest(), role=role)

        declaration = RecursiveOperationDeclaration(
            capability_key=f"{NAMESPACE}.{role}", capability_version="1.0.0",
            implementation_id="wilson-exposed-combination-stages-v1", kind=kind,
            config_record_type=config, stage=stage,
            input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA_TYPE, MAX_BYTES)
                for name, record in inputs),
            outputs=tuple(OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                MEDIA_TYPE, ".json") for name, record in outputs),
            permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
            conformance_check_ids=('commit-before-target-label-read', 'complete-four-corner-source-roles'),
            runner_factory=runner, record_codecs=output_codecs(),
            scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=scientific_operand_sha256s,
                scientific_unit_ids=scientific_unit_ids,
                scientific_root_validator=scientific_root_validator),
            execution_properties=RecursiveExecutionProperties(
                barrier=BarrierKind.FREEZE if role == "commit" else BarrierKind.NONE))
        return declaration

    return tuple(declare(row) for row in PHASES)
