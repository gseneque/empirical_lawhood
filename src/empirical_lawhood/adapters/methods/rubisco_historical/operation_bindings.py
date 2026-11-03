"""Cold registered historical stages, strict ports and stateless runners.

The shared compiler/provider/scheduler own execution and custody. This adapter
owns the fixed science, its information roles and global label-access stop.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
)
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
    HistoricalAnalysisSystemV1, HistoricalCommitConfigV1, HistoricalEvaluateConfigV1,
    HistoricalFitConfigV1, HistoricalPredictConfigV1, analysis_unit_id,
)
from .records import (
    HistoricalEvaluationV1, HistoricalFittedModelV1, HistoricalFoldForecastsV1,
    HistoricalForecastCommitmentV1, HistoricalScienceV1,
)
from .source_binding import HistoricalSourceConfigV1, Rr2018ArticleInputV1, SOURCE_OUTPUTS, prepare_source

NAMESPACE = "rubisco-historical.phases"
MEDIA_TYPE = "application/json"
MAX_BYTES = 4 * 1024**2
BUDGET = ResourceBudget(1, 1024**3, 0, 600, 16 * 1024**2, MAX_BYTES)
PHASES = (
    ("source", HistoricalSourceConfigV1, (("article", Rr2018ArticleInputV1, 1),), SOURCE_OUTPUTS,
     CapabilityKind.OBSERVATION_OPERATOR, ScientificStage.TRANSFORM),
    ("fit", HistoricalFitConfigV1, (("training", HistoricalTrainingSliceV1, 1),),
     (("model", HistoricalFittedModelV1),), CapabilityKind.TRANSFORM, ScientificStage.DEVELOP),
    ("predict", HistoricalPredictConfigV1,
     (("features", HistoricalFeatureSliceV1, 1), ("model", HistoricalFittedModelV1, 1)),
     (("forecasts", HistoricalFoldForecastsV1),), CapabilityKind.TRANSFORM, ScientificStage.DEVELOP),
    ("commit", HistoricalCommitConfigV1, (("forecasts", HistoricalFoldForecastsV1, 5),),
     (("commitment", HistoricalForecastCommitmentV1),), CapabilityKind.TRANSFORM, ScientificStage.FREEZE),
    ("evaluate", HistoricalEvaluateConfigV1,
     (("commitment", HistoricalForecastCommitmentV1, 1), ("labels", HistoricalLabelSliceV1, 5)),
     (("evaluation", HistoricalEvaluationV1),), CapabilityKind.FALSIFIER, ScientificStage.FALSIFY),
)


def scientific_operand_sha256s(config):
    return tuple(sorted({config.science.fingerprint(), config.science.source.object_fingerprint}))


def scientific_unit_ids(config):
    if type(config) in (HistoricalFitConfigV1, HistoricalPredictConfigV1):
        return (analysis_unit_id(config.fold_id),)
    return tuple(analysis_unit_id(fold.fold_id) for fold in config.science.folds)


def historical_development_root(science: HistoricalScienceV1, *, study_id: str | None = None) -> DevelopmentStudySpec:
    """Exact analytical root for this exposed historical diagnostic, no graph."""
    if not isinstance(science, HistoricalScienceV1):
        raise ValueError("historical root needs its typed frozen science")
    science_identity = ObjectIdentity.from_record(science.science_id, science)
    units = tuple(analysis_unit_id(fold.fold_id) for fold in science.folds)
    system = HistoricalAnalysisSystemV1(f"{science.science_id}.analysis-system", science_identity, science.source, units)
    world_id = f"{science.science_id}.analysis-world"
    view = f"{science.science_id}.float64-fit-decimal28-report"
    claims = tuple(ClaimSpec(
        f"{science.science_id}.{fold.fold_id}.point-diagnostic", world_id, f"{science.science_id}.reported-points",
        "Fixed classical methods produce inspectable point errors for previously exposed reported Rubisco endpoint means.",
        f"{3 * len(fold.target_sample_ids)} method-by-target forecasts nested in {len(fold.target_sample_ids)} shared-study table contrasts; independent biological n is unknown.",
        analysis_unit_id(fold.fold_id), None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Software analysis cases establish no fresh biology, construct validation, calibrated coverage, EL superiority or submission qualification.",
        ("exposed-historical-table", "shared-measured-parent", "unknown-biological-independence"),
        numerical_view_ids=(view,)) for fold in science.folds)
    return DevelopmentStudySpec(study_id or f"{science.science_id}.development-study",
        "How do three fixed classical methods predict the exposed historical Rubisco table contrasts under the frozen point gates?",
        ObjectIdentity.from_record(system.system_id, system), world_id, WorldKind.ANALYTIC_REFERENCE,
        units, (view,), claims, tuple(sorted((science_identity, science.source), key=lambda value: value.object_id)))


def scientific_root_validator(config, context):
    """Whole analytical root, selected design and mandatory role dependencies."""
    role_by_type = {row[1]: row[0] for row in PHASES}
    row = next((row for row in PHASES if row[1] is type(config)), None)
    if row is None or not isinstance(context.root, DevelopmentStudySpec):
        raise ValueError("historical stage requires its genuine exposed analytical development root")
    expected = historical_development_root(config.science, study_id=context.root.study_id)
    if context.root.canonical_bytes() != expected.canonical_bytes():
        raise ValueError("historical stage substitutes its exact analysis root, source, claims or case census")
    if (context.stage is not row[5] or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        or context.unit_ids != scientific_unit_ids(config)):
        raise ValueError("historical stage changes its registered stage, access, visibility or analysis unit")
    configs = {item.node_id: item.record for item in context.config_inputs if type(item.record) in role_by_type}
    if context.node_id not in configs or configs[context.node_id] != config:
        raise ValueError("historical stage lacks its exact selected configuration")
    if any(item.science != config.science for item in configs.values()):
        raise ValueError("selected historical stages substitute scientific source identities")
    incoming = tuple(link for link in context.links if link.consumer_node_id == context.node_id)
    role = row[0]
    def check_role_source(link, expected_output):
        if link.external_input_id is None:
            producer = configs.get(link.producer_node_id)
            if type(producer) is not HistoricalSourceConfigV1 or link.producer_output_id != expected_output:
                raise ValueError("historical data role lacks its exact source-preparation output")

    if role == "source":
        if (len(incoming) != 1 or incoming[0].consumer_input_id != "article"
            or incoming[0].external_input_id is None):
            raise ValueError("RR2018 source preparation needs its sole external raw-article role")
    elif role == "fit":
        if len(incoming) != 1 or incoming[0].consumer_input_id != "training":
            raise ValueError("historical fit changes its sole training information role")
        check_role_source(incoming[0], f"training.{config.fold_id}")
    elif role == "predict":
        if {link.consumer_input_id for link in incoming} != {"features", "model"} or len(incoming) != 2:
            raise ValueError("historical prediction changes its model/feature roles")
        link = next(link for link in incoming if link.consumer_input_id == "model")
        producer = configs.get(link.producer_node_id)
        if (type(producer) is not HistoricalFitConfigV1 or producer.fold_id != config.fold_id
            or link.producer_output_id != "model" or link.external_input_id is not None):
            raise ValueError("historical prediction model must come from its same-fold fit")
        check_role_source(next(link for link in incoming if link.consumer_input_id == "features"),
                           f"features.{config.fold_id}")
    elif role == "commit":
        if len(incoming) != len(config.science.folds):
            raise ValueError("historical global barrier omits a required forecast fold")
        seen = []
        for link in incoming:
            producer = configs.get(link.producer_node_id)
            if (type(producer) is not HistoricalPredictConfigV1
                or link.consumer_input_id != f"forecasts.{producer.fold_id}"
                or link.producer_output_id != "forecasts" or link.external_input_id is not None):
                raise ValueError("historical global barrier changes a typed prediction dependency")
            seen.append(producer.fold_id)
        if tuple(sorted(seen)) != tuple(fold.fold_id for fold in config.science.folds):
            raise ValueError("historical global barrier repeats or substitutes a forecast fold")
    else:
        expected_ports = {"commitment", *(f"labels.{fold.fold_id}" for fold in config.science.folds)}
        if len(incoming) != len(expected_ports) or {link.consumer_input_id for link in incoming} != expected_ports:
            raise ValueError("historical evaluation changes its global-commit/label census")
        link = next(link for link in incoming if link.consumer_input_id == "commitment")
        producer = configs.get(link.producer_node_id)
        if (type(producer) is not HistoricalCommitConfigV1 or link.producer_output_id != "commitment"
            or link.external_input_id is not None):
            raise ValueError("historical evaluation lacks its actual global commitment dependency")
        for label_link in incoming:
            if label_link.consumer_input_id.startswith("labels."):
                check_role_source(label_link, label_link.consumer_input_id)


def output_codecs():
    """Closed product and external-input codecs for recursive authoring.

    The shared API also uses this roster to decode exact external operands.
    These three source roles remain explicit; there is no generic fallback.
    """
    records = (HistoricalTrainingSliceV1, HistoricalFeatureSliceV1, HistoricalLabelSliceV1, Rr2018ArticleInputV1,
               *(record for row in PHASES for _, record in row[3]))
    return {record.SCHEMA: record for record in records}


class HistoricalOperationRunner:
    """One cold registered stage, using only its declared path-free ports."""

    def __init__(self, *, manifest, role):
        self.manifest = manifest
        self.role = role
        self.row = next(row for row in PHASES if row[0] == role)

    def execute(self, context):
        role, config_type, input_specs, output_specs, _, _ = self.row
        try:
            if context.config.config_schema != config_type.SCHEMA:
                raise ValueError("historical stage changes its registered configuration schema")
            allowed = {config_type.SCHEMA, *(record.SCHEMA for _, record, _ in input_specs)}
            if any(p.payload_schema not in allowed or p.media_type != MEDIA_TYPE or p.size_bytes > MAX_BYTES
                   for p in context.input_ports):
                raise ValueError("historical stage receives an undeclared label/oracle input or unbounded media")
            ports = {schema: tuple(p for p in context.input_ports if p.payload_schema == schema) for schema in allowed}
            if len(ports[config_type.SCHEMA]) != 1 or ports[config_type.SCHEMA][0].kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("historical stage needs one external exact configuration")
            for _, record, maximum in input_specs:
                if not 1 <= len(ports[record.SCHEMA]) <= maximum:
                    raise ValueError("historical stage changes a complete input cardinality")
            for record in (HistoricalFittedModelV1, HistoricalFoldForecastsV1, HistoricalForecastCommitmentV1):
                if any(p.kind is not WorkerInputKind.DEPENDENCY for p in ports.get(record.SCHEMA, ())):
                    raise ValueError("historical stage requires its actual receipt-bound predecessor")
            output = context.output_ports
            if (tuple((p.output_id, p.payload_schema) for p in output)
                != tuple((f"{context.task_id}.{name}", record.SCHEMA) for name, record in output_specs)
                or any(p.profile is not ArtifactProfile.CANONICAL_JSON or p.media_type != MEDIA_TYPE for p in output)):
                raise ValueError("historical stage changes its exact typed output contract")

            def read(port, record_type):
                payload = port.read(MAX_BYTES + 1)
                if len(payload) != port.size_bytes:
                    raise ValueError("historical port bytes differ from their bounded materialization")
                return decode_canonical_bytes(payload, record_type, maximum_bytes=MAX_BYTES)

            config_port = ports[config_type.SCHEMA][0]
            config = read(config_port, config_type)
            if (config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id
                or config_port.artifact_id != context.config.artifact_id):
                raise ValueError("historical stage changes its immutable selected configuration")
            if role == "source":
                article = read(ports[Rr2018ArticleInputV1.SCHEMA][0], Rr2018ArticleInputV1)
                named_products = prepare_source(config, article)
            elif role == "fit":
                training = read(ports[HistoricalTrainingSliceV1.SCHEMA][0], HistoricalTrainingSliceV1)
                if training.fold_id != config.fold_id:
                    raise ValueError("historical fit substitutes its assigned fold")
                product = analysis.fit(config.science, training)
            elif role == "predict":
                model = read(ports[HistoricalFittedModelV1.SCHEMA][0], HistoricalFittedModelV1)
                features = read(ports[HistoricalFeatureSliceV1.SCHEMA][0], HistoricalFeatureSliceV1)
                if features.fold_id != config.fold_id:
                    raise ValueError("historical prediction substitutes its assigned fold")
                product = HistoricalFoldForecastsV1(config.fold_id, analysis.predict(config.science, model, features))
            elif role == "commit":
                bundles = tuple(read(p, HistoricalFoldForecastsV1) for p in ports[HistoricalFoldForecastsV1.SCHEMA])
                product = analysis.commit_forecasts(config.science, tuple(sorted(bundles, key=lambda value: value.fold_id)))
            else:
                # This commitment is decoded and checked BEFORE any label-port
                # read, regardless of the canonical input artifact ordering.
                commitment = read(ports[HistoricalForecastCommitmentV1.SCHEMA][0], HistoricalForecastCommitmentV1)
                if analysis.commit_forecasts(config.science, commitment.fold_forecasts) != commitment:
                    raise ValueError("historical evaluation changes its exact global forecast commitment")
                if len(ports[HistoricalLabelSliceV1.SCHEMA]) != len(config.science.folds):
                    raise ValueError("historical evaluation lacks its complete label-port census")
                labels = tuple(read(p, HistoricalLabelSliceV1) for p in ports[HistoricalLabelSliceV1.SCHEMA])
                product = analysis.evaluate(config.science, commitment, tuple(sorted(labels, key=lambda value: value.fold_id)))
            if role != "source":
                named_products = ((output_specs[0][0], product),)
            if tuple((name, type(record)) for name, record in named_products) != output_specs:
                raise ValueError("historical stage changes its registered output record census")
            payloads = tuple(TaskOutputPayload(port.output_id, record.canonical_bytes())
                             for port, (_, record) in zip(output, named_products, strict=True))
            if (any(len(value.payload) > MAX_BYTES for value in payloads)
                or sum(len(value.payload) for value in payloads) > context.resource_budget.output_bytes):
                raise ValueError("historical stage exceeds its frozen output byte budget")
            return RunnerResult(payloads,
                (ReceiptCheck("valid-complete-historical-stage", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    """Derive cold and executable projections from each scientific stage."""
    def declare(row):
        role, config, inputs, outputs, kind, stage = row

        def runner():
            return HistoricalOperationRunner(manifest=declaration.manifest(), role=role)

        declaration = RecursiveOperationDeclaration(
            capability_key=f"{NAMESPACE}.{role}", capability_version="1.0.0",
            implementation_id="historical-information-stages-v1", kind=kind,
            config_record_type=config, stage=stage,
            input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA_TYPE, MAX_BYTES, 1, count)
                for name, record, count in inputs),
            outputs=tuple(OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                MEDIA_TYPE, ".json") for name, record in outputs),
            permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
            conformance_check_ids=('complete-historical-ports', 'global-commit-before-label-read'),
            runner_factory=runner, record_codecs=output_codecs(),
            scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=scientific_operand_sha256s,
                scientific_unit_ids=scientific_unit_ids,
                scientific_root_validator=scientific_root_validator),
            execution_properties=RecursiveExecutionProperties(
                barrier=BarrierKind.FREEZE if role == "commit" else BarrierKind.NONE))
        return declaration

    return tuple(declare(row) for row in PHASES)
