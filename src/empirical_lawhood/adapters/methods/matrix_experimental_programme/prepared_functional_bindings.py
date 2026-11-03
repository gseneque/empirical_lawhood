# SPDX-License-Identifier: MPL-2.0
"""One closed prepared opportunity graph and its actual outcome consumer.

The original source/prediction/assay checkpoints remain closed. Their native
and numerical methods are reused under this separate complete owner. This
development route grants no protected confirmation, transfer or qualification.
"""

from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import _dependency
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks

from . import prepared_assay_composition as assay
from . import prepared_functional as functional
from . import prepared_future_custody as future
from . import prepared_prediction_bindings as prediction
from .prepared_assay_method import MatrixPreparedAssayMethod
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_point import MatrixPreparedPointSeal
from .prepared_response_science import MatrixPreparedResponseReadout
from .records import MatrixProgrammeRoster
from .science import MatrixPreparationNomination


NAMESPACE = "matrix-prepared-functional"
SCOPE = "EXPOSED_COMPLETE_PREPARED_OPPORTUNITY_NOT_PROTECTED_CONFIRMATION_TRANSFER_OR_QUALIFICATION"


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-functional-selection"
    record_id: str
    specification: functional.MatrixPreparedFunctionalSpecification
    roster: MatrixProgrammeRoster
    assay_method: MatrixPreparedAssayMethod

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.specification) is not functional.MatrixPreparedFunctionalSpecification or type(self.roster) is not MatrixProgrammeRoster
                or type(self.assay_method) is not MatrixPreparedAssayMethod):
            raise TypeError("prepared functional selection requires its exact own specification and original metadata owners")
        for value in (self.specification, self.roster, self.assay_method):
            value.__post_init__()
        if self.specification.roster != self.roster.identity or self.specification.assay_method != self.assay_method.identity:
            raise ValueError("prepared functional selection substitutes its exact original case roster or common fixed method")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-functional-config"
    config_id: str
    selection: MatrixPreparedFunctionalSelection

    def __post_init__(self):
        if type(self.selection) is not MatrixPreparedFunctionalSelection or self.config_id != "config." + node_id(self.selection):
            raise ValueError("prepared functional configuration changes its exact immutable selected metadata")


def node_id(selection):
    return NAMESPACE + ".nominate." + selection.fingerprint()


def _assay_external_id(selection):
    return "external.prepared-functional.assay." + selection.specification.assay.object_fingerprint


def validate_selection(selection, programme):
    if type(selection) is not MatrixPreparedFunctionalSelection or type(programme) is not assay.MatrixPreparedAssayProgramme:
        raise TypeError("prepared functional graph requires its exact complete selection and actual assay programme")
    selection.__post_init__()
    if selection.specification.phase != "E5_OPPORTUNITY":
        raise ValueError("prepared protected confirmation/transfer source and entry composition requires its separate implemented owner")
    return functional.validate_prepared_functional_selection(selection.specification, selection.roster,
        programme.prediction.point_design.package, programme, assay_method=selection.assay_method)


def _outcome_contracts(selection, programme):
    node = node_id(selection)
    config = MatrixPreparedFunctionalConfig("config." + node, selection)
    key = _assay_external_id(selection)
    external = prediction._record_external(key, programme, programme.record_id)
    links = [RecursiveInputLink("edge." + node + ".assay-programme", node, "assay-programme", external_input_id=key, scientific_role="SOURCE")]
    sources = {row.identity: row for row in programme.prediction.sources.sources}
    for case_id, reference in selection.specification.case_sources:
        source = sources[reference]
        for port, owner, phase in (("point", prediction.NAMESPACE, "point"), ("mechanical", prediction.NAMESPACE, "mechanical"),
                ("readout", future.NAMESPACE, "response-score")):
            producer = future.node_id(source, phase) if owner == future.NAMESPACE else prediction.tail_node(source.identity, phase)
            name = port + "." + case_id
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name, producer_node_id=producer,
                producer_output_id="product", scientific_role="HISTORY"))
    return (node, config), tuple(sorted(links, key=lambda row: row.edge_id)), external


def contracts(selection, programme):
    validate_selection(selection, programme)
    configs, links, external, records, arrays = assay.contracts(programme)
    operation, edges, operand = _outcome_contracts(selection, programme)
    return (tuple(sorted((*configs, operation))), tuple(sorted((*links, *edges), key=lambda row: row.edge_id)),
        tuple(sorted((*external, operand), key=lambda row: row.input_id)),
        tuple(sorted((*records, (_assay_external_id(selection), programme)))), arrays)


def development_root(selection, programme, study_id):
    original = assay.development_root(programme, study_id)
    claim = replace(original.claims[0], estimand="Every selected matched preparation, complete original functional endpoint and declared development nomination.")
    return replace(original, claims=(claim,), scientific_operands=tuple(sorted({*original.scientific_operands, selection.identity}, key=lambda row: row.object_id)))


def _selected_roots(context):
    allowed = (prediction.MatrixPreparedPredictionRootConfig, prediction.MatrixPreparedPredictionConfig,
        prediction.source_owner.MatrixPreparationOperationConfig, future.MatrixPreparedFutureConfig, MatrixPreparedFunctionalConfig)
    roots = tuple(row for row in context.config_inputs if type(row.record) is prediction.MatrixPreparedPredictionRootConfig)
    outcomes = tuple(row for row in context.config_inputs if type(row.record) is MatrixPreparedFunctionalConfig)
    ids = tuple(row.node_id for row in context.config_inputs)
    if (len(roots) != 1 or len(outcomes) != 1 or ids != tuple(sorted(set(ids)))
            or any(type(row.record) not in allowed for row in context.config_inputs) or type(context.root) is not DevelopmentStudySpec):
        raise ValueError("prepared functional graph omits or substitutes a mandatory complete design/outcome selection")
    root, = roots
    outcome, = outcomes
    prediction_prefix, outcome_prefix = prediction.NAMESPACE + ".design.", NAMESPACE + ".nominate."
    if (root.record.config_id != "config." + root.node_id or not root.node_id.startswith(prediction_prefix)
            or outcome.record.config_id != "config." + outcome.node_id or not outcome.node_id.startswith(outcome_prefix)):
        raise ValueError("prepared functional graph changes its immutable selected design/configuration pins")
    programme = root.record.programme
    prediction_reference = ObjectIdentity(programme.record_id, programme.SCHEMA, programme.VERSION, root.node_id.removeprefix(prediction_prefix))
    selection = outcome.record.selection
    selection_reference = ObjectIdentity(selection.record_id, selection.SCHEMA, selection.VERSION, outcome.node_id.removeprefix(outcome_prefix))
    if (context.root.system != selection.specification.assay or selection_reference not in context.root.scientific_operands
            or selection.specification.phase != "E5_OPPORTUNITY"):
        raise ValueError("prepared functional graph crosses its selected original assay/phase or complete immutable functional pin")
    return root, outcome, prediction_reference


def _rebuild_assay(context, root, outcome):
    responses = tuple(row.record for row in context.config_inputs if type(row.record) is future.MatrixPreparedFutureConfig and row.record.phase == "responses")
    selection = outcome.record.selection
    if not responses or any(row.programme != selection.specification.assay for row in responses):
        raise ValueError("prepared functional graph substitutes its exact selected complete future assay")
    programme = assay.MatrixPreparedAssayProgramme(selection.specification.assay.object_id, root.record.programme,
        tuple(sorted((row.source.source_id, row.panels) for row in responses)))
    validate_selection(selection, programme)
    return programme


def scientific_root_validator(config, context):
    root, outcome, prediction_reference = _selected_roots(context)
    if type(config) is prediction.MatrixPreparedPredictionRootConfig:
        programme = _rebuild_assay(context, root, outcome)
        selection = outcome.record.selection
        configs, links, external, _, _ = contracts(selection, programme)
        groups = tuple(sorted({row.unit_id for row in selection.roster.cases}))
        if (config != root.record or context.node_id != root.node_id
                or tuple((row.node_id, row.record) for row in context.config_inputs) != configs
                or tuple(context.links) != links or tuple(context.external_inputs) != external
                or context.root != development_root(selection, programme, context.root.study_id)
                or context.unit_ids != groups or context.selected_unit_ids != groups or context.stage is not ScientificStage.DEVELOP
                or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("prepared functional design changes its exact complete source/phase/outcome graph or selected contracts")
    elif type(config) is MatrixPreparedFunctionalConfig:
        programme = _rebuild_assay(context, root, outcome)
        operation, links, external = _outcome_contracts(config.selection, programme)
        groups = tuple(sorted({row.unit_id for row in config.selection.roster.cases}))
        if (config != outcome.record or (context.node_id, config) != operation
                or tuple(row for row in context.links if row.consumer_node_id == context.node_id) != links
                or tuple(row for row in context.external_inputs if row.input_id == external.input_id) != (external,)
                or context.unit_ids != groups or context.selected_unit_ids != groups or context.stage is not ScientificStage.FALSIFY
                or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("prepared functional outcome changes its exact assigned input/source/receipt graph or immutable configuration")
    elif type(config) in (prediction.MatrixPreparedPredictionConfig, prediction.source_owner.MatrixPreparationOperationConfig, future.MatrixPreparedFutureConfig):
        # The real composed context keeps the actual assay as its subject. No
        # fabricated ancestor, substituted study or checkpoint guard is used.
        assay._validate_local_projection(config, context, root, prediction_reference)
    else:
        raise TypeError("prepared functional operation has a foreign configuration owner")


def units(config):
    return tuple(sorted({row.unit_id for row in config.selection.roster.cases}))


def digests(config):
    return tuple(sorted({config.selection.fingerprint(), config.selection.specification.assay.object_fingerprint}))


def _received(context):
    kinds = {kind.SCHEMA: kind for kind in (MatrixPreparedFunctionalConfig, assay.MatrixPreparedAssayProgramme,
        MatrixPreparedPointSeal, MatrixPreparedMechanicalForecast, MatrixPreparedResponseReadout)}
    records = {}
    for port in context.input_ports:
        kind = kinds.get(port.payload_schema)
        if kind is None or port.media_type != "application/json":
            raise ValueError("prepared functional consumer receives a foreign scientific input port")
        raw = port.read()
        if len(raw) != port.size_bytes:
            raise ValueError("prepared functional consumer changes an exact received record byte bound")
        record = decode_canonical_bytes(raw, kind, maximum_bytes=port.size_bytes)
        if record.canonical_bytes() != raw:
            raise ValueError("prepared functional consumer changes original canonical scientific bytes")
        records.setdefault(kind, []).append((record, port, sha256(raw).hexdigest()))
    if len(records.get(MatrixPreparedFunctionalConfig, ())) != 1 or len(records.get(assay.MatrixPreparedAssayProgramme, ())) != 1:
        raise ValueError("prepared functional consumer lacks its exact single selected configuration/assay record")
    config, _, config_digest = records[MatrixPreparedFunctionalConfig][0]
    programme, programme_port, programme_digest = records[assay.MatrixPreparedAssayProgramme][0]
    selection = config.selection
    validate_selection(selection, programme)
    permissions = prediction.source_owner.operation_declarations()[0].permissions
    if (context.task_id != node_id(selection) or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
            or context.config.content_sha256 != config_digest or context.resource_budget != prediction.source_owner.BUDGET
            or context.permissions != permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or programme_digest != selection.specification.assay.object_fingerprint or programme_port.kind is not WorkerInputKind.EXTERNAL
            or programme_port.artifact_id != programme.record_id or programme_port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or programme_port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("prepared functional consumer changes its actual issued configuration, selected assay or operational scope")
    n = len(selection.roster.cases)
    if len(context.input_ports) != 2 + 3 * n:
        raise ValueError("prepared functional consumer drops complete assigned case/readout input denominators")
    by_source = {}
    for kind, key, phase, namespace in ((MatrixPreparedPointSeal, "point", "point", prediction.NAMESPACE),
            (MatrixPreparedMechanicalForecast, "mechanical", "mechanical", prediction.NAMESPACE),
            (MatrixPreparedResponseReadout, "readout", "response-score", future.NAMESPACE)):
        if len(records.get(kind, ())) != n:
            raise ValueError("prepared functional consumer omits a selected original numerical product")
        for record, port, _ in records[kind]:
            source = record.feature.source if kind is MatrixPreparedPointSeal else record.source
            values = by_source.setdefault(source, {})
            if key in values:
                raise ValueError("prepared functional consumer duplicates a source's original numerical product")
            _dependency(context, port, source.object_id, phase, namespace=namespace,
                access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY)
            values[key] = record
    selected_sources = dict(selection.specification.case_sources)
    if set(by_source) != set(selected_sources.values()) or any(set(value) != {"point", "mechanical", "readout"} for value in by_source.values()):
        raise ValueError("prepared functional consumer substitutes the exact assigned scientific source census")
    observations = {case_id: functional.MatrixPreparedFunctionalObservation(case_id, **by_source[source], comparator=None)
        for case_id, source in selected_sources.items()}
    return selection, programme, observations


class MatrixPreparedFunctionalRunner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            selection, programme, observations = _received(context)
            manifest, nomination = functional.nominate_prepared_opportunity(selection.specification, selection.roster,
                programme.prediction.point_design.package, programme, observations, assay_method=selection.assay_method,
                result_id="nomination." + selection.fingerprint())
            values = {context.task_id + ".manifest": manifest.canonical_bytes(), context.task_id + ".product": nomination.canonical_bytes()}
            if set(values) != {row.output_id for row in context.output_ports}:
                raise ValueError("prepared functional consumer changes its exact compiler-derived complete output census")
            return RunnerResult(tuple(TaskOutputPayload(key, value) for key, value in sorted(values.items())),
                (ReceiptCheck("complete-original-prepared-functional-opportunity-and-authenticated-inputs", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    base = tuple(replace(row, capability_key=NAMESPACE + "." + row.capability_key.rsplit(".", 1)[-1],
        implementation_id=NAMESPACE + "." + row.capability_key.rsplit(".", 1)[-1] + ".v1",
        scientific_hooks=replace(row.scientific_hooks, scientific_root_validator=scientific_root_validator)) for row in assay.operation_declarations())
    codecs = {kind.SCHEMA: kind for kind in (MatrixPreparedFunctionalConfig, MatrixPreparedFunctionalSelection,
        functional.MatrixPreparedFunctionalManifest, MatrixPreparationNomination, assay.MatrixPreparedAssayProgramme,
        MatrixPreparedPointSeal, MatrixPreparedMechanicalForecast, MatrixPreparedResponseReadout)}
    declaration = RecursiveOperationDeclaration(capability_key=NAMESPACE + ".nominate", capability_version="1.0.0",
        implementation_id=NAMESPACE + ".nominate.v1", kind=CapabilityKind.FALSIFIER, config_record_type=MatrixPreparedFunctionalConfig,
        stage=ScientificStage.FALSIFY, input_ports=tuple(sorted((RecursivePortContract("assay-programme", assay.MatrixPreparedAssayProgramme.SCHEMA, "application/json", None),
            *(RecursivePortContract(port, kind.SCHEMA, "application/json", None, minimum_count=1, maximum_count=None)
                for port, kind in (("point", MatrixPreparedPointSeal), ("mechanical", MatrixPreparedMechanicalForecast), ("readout", MatrixPreparedResponseReadout)))), key=lambda row: row.port_id)),
        outputs=tuple(sorted((OutputTemplate("manifest", functional.MatrixPreparedFunctionalManifest.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            OutputTemplate("product", MatrixPreparationNomination.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")), key=lambda row: row.output_id)),
        permissions=prediction.source_owner.operation_declarations()[0].permissions, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=prediction.source_owner.BUDGET, conformance_check_ids=("actual-prepared-input-receipt-custody", "complete-original-matched-opportunity"),
        runner_factory=MatrixPreparedFunctionalRunner, record_codecs=codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=digests, scientific_unit_ids=units, scientific_root_validator=scientific_root_validator))
    return tuple(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest()))
        for row in sorted((*base, declaration), key=lambda row: row.capability_key))


@dataclass(frozen=True, slots=True)
class LoweredPreparedFunctional:
    draft: RecursiveStudyDraft
    input_records: tuple
    input_artifacts: tuple


def lower_prepared_functional(selection, programme, *, campaign, draft_id):
    configs, links, external, records, arrays = contracts(selection, programme)
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    operations = []
    for node, config in configs:
        phase = "design" if type(config) is prediction.MatrixPreparedPredictionRootConfig else "nominate" if type(config) is MatrixPreparedFunctionalConfig else config.phase
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declarations[phase].registration().selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=prediction.source_owner.BUDGET))
    study = development_root(selection, programme, "study." + draft_id)
    selected_campaign = replace(campaign, objective=prediction.QUESTION, system_ids=(programme.identity.object_id,), world_ids=(prediction.WORLD,),
        target_claim_ids=tuple(row.claim_id for row in study.claims))
    draft = RecursiveStudyDraft(draft_id, prediction.QUESTION, selected_campaign, (), (), (), tuple(operations), external, links,
        tuple(node for node, _ in configs), development_study=study)
    return LoweredPreparedFunctional(draft, records, arrays)
