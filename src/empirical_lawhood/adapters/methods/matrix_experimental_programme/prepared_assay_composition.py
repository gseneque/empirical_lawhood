# SPDX-License-Identifier: MPL-2.0
"""Exact complete prepared development acquisition and independent assay root.

This additive owner closes its source, causal, prediction and future graph. It
does not relabel the exposed development route as protected confirmation or
transfer. A final functional programme consumer remains a separate composition
step; no scientific admission or qualification is supplied here.
"""

from dataclasses import dataclass, replace
from functools import partial
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.plans import ScientificStage

from . import prepared_future_bindings as future
from . import prepared_future_custody as custody
from . import prepared_prediction_bindings as prediction
from .prepared_prefix import identity
from .prepared_response_science import MatrixPreparedResponsePanel, validate_prepared_panels


SCOPE = "EXPOSED_COMPLETE_PREPARED_ASSAY_NOT_E5_CONFIRMATION_OR_E6_TRANSFER"


@dataclass(frozen=True, slots=True)
class MatrixPreparedAssayProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-assay-programme"
    record_id: str
    prediction: prediction.MatrixPreparedPredictionProgramme
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.scope != SCOPE or type(self.prediction) is not prediction.MatrixPreparedPredictionProgramme
                or type(self.panels) is not tuple or tuple(key for key, _ in self.panels) != tuple(row.source_id for row in self.prediction.sources.sources)):
            raise ValueError("prepared assay programme omits its exact source/prediction/future-panel census")
        self.prediction.__post_init__()
        consumed, definitions = {}, {}
        for source in self.prediction.sources.sources:
            panels = dict(self.panels)[source.source_id]
            validate_prepared_panels(source, panels)
            for panel in panels:
                if definitions.setdefault(panel.panel_id, panel) != panel:
                    raise ValueError("prepared assay aliases different original future panel definitions")
                for stream in panel.streams:
                    owner = source.root.root.independent_group_id, panel.role, stream.purpose
                    if consumed.setdefault(stream.effective_seed, owner) != owner:
                        raise ValueError("prepared assay crosses independent groups, panel roles or consumed purpose streams")

    @property
    def identity(self):
        return identity(self)


def _future_contracts(source, protocol, panels, *, programme_reference, point_reference, package_reference):
    """Exact future phases for one source; no programme-wide serialization."""
    configs, links = {}, []
    for phase in ("responses", "response-score"):
        node = custody.node_id(source, phase)
        configs[node] = custody.MatrixPreparedFutureConfig("config." + node, programme_reference, source, protocol, panels,
            point_reference, package_reference, phase)
        externals = {name: prediction.source_owner.external_id(source, name) for name in ("source", "allocation", "initial-state")}
        externals["protocol"] = "external.protocol." + protocol.fingerprint()
        if phase == "response-score":
            externals["templates"] = "external.templates." + protocol.templates.array_artifact.sha256
        for name, input_id in externals.items():
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=input_id, scientific_role="SOURCE"))
        dependencies = {"history": (prediction.source_owner.node_id(source, "history"), "product"),
            "history-arrays": (prediction.source_owner.node_id(source, "history"), "arrays"),
            "causal": (prediction.tail_node(source.identity, "project"), "product"),
            "point": (prediction.tail_node(source.identity, "point"), "product"),
            "mechanical": (prediction.tail_node(source.identity, "mechanical"), "product"),
            "mechanical-arrays": (prediction.tail_node(source.identity, "mechanical"), "arrays")}
        if phase == "response-score":
            dependencies.update({"causal-arrays": (prediction.tail_node(source.identity, "project"), "arrays"),
                "responses": (custody.node_id(source, "responses"), "product"), "response-arrays": (custody.node_id(source, "responses"), "arrays")})
        for name, (producer, output) in dependencies.items():
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name, producer_node_id=producer,
                producer_output_id=output, scientific_role="HISTORY"))
    return configs, links


def contracts(programme):
    configs, links, external, records, arrays = prediction.contracts(programme.prediction)
    configs, links = dict(configs), list(links)
    programme_reference = programme.identity
    point_reference = programme.prediction.point_design.identity
    package_reference = programme.prediction.point_design.package.identity
    protocols, selected_panels = dict(programme.prediction.protocols), dict(programme.panels)
    for source in programme.prediction.sources.sources:
        selected, edges = _future_contracts(source, protocols[source.source_id], selected_panels[source.source_id],
            programme_reference=programme_reference, point_reference=point_reference, package_reference=package_reference)
        configs.update(selected)
        links.extend(edges)
    return tuple(sorted(configs.items())), tuple(sorted(links, key=lambda row: row.edge_id)), external, records, arrays


def development_root(programme, study_id):
    original = prediction.development_root(programme.prediction, study_id)
    claim = replace(original.claims[0], estimand="Every selected source, both causal views, actual pre-future predictions and complete48-branch original pulse assay.")
    # Keep exact original nonpromotable access and qualification disclaimer.
    operands = {programme.identity, *original.scientific_operands,
        *(ObjectIdentity.from_record(protocol.protocol_id, protocol) for _, protocol in programme.prediction.protocols)}
    return replace(original, system=programme.identity, claims=(claim,), scientific_operands=tuple(sorted(operands, key=lambda row: row.object_id)))


def _selected_prediction_root(context):
    """Require the selected immutable root whose own hook checks the full graph.

    Its node digest was strictly decoded against the programme by RootConfig;
    the mandatory design hook independently rederives that entire selection.
    Other hooks therefore need no repeated programme-wide serialization.
    """
    allowed = (prediction.MatrixPreparedPredictionRootConfig, prediction.MatrixPreparedPredictionConfig,
        prediction.source_owner.MatrixPreparationOperationConfig, custody.MatrixPreparedFutureConfig)
    roots = tuple(row for row in context.config_inputs if type(row.record) is prediction.MatrixPreparedPredictionRootConfig)
    ids = tuple(row.node_id for row in context.config_inputs)
    if (len(roots) != 1 or ids != tuple(sorted(set(ids))) or any(type(row.record) not in allowed for row in context.config_inputs)
            or type(context.root) is not DevelopmentStudySpec or type(context.root.system) is not ObjectIdentity
            or context.root.system.object_schema != MatrixPreparedAssayProgramme.SCHEMA
            or context.root.system.object_version != MatrixPreparedAssayProgramme.VERSION):
        raise ValueError("prepared assay omits or substitutes its mandatory selected complete design root")
    root, = roots
    prefix = prediction.NAMESPACE + ".design."
    if root.record.config_id != "config." + root.node_id or not root.node_id.startswith(prefix):
        raise ValueError("prepared assay substitutes its immutable selected design-node identity")
    programme = root.record.programme
    reference = ObjectIdentity(programme.record_id, programme.SCHEMA, programme.VERSION, root.node_id.removeprefix(prefix))
    return root, reference


def _validate_local_projection(config, context, selected_root, programme_reference):
    """Authenticate this exact source/phase against the mandatory whole root."""
    programme = selected_root.record.programme
    source_id = config.public_source.source.object_id if type(config) is prediction.MatrixPreparedPredictionConfig else config.source.source_id
    selected = tuple(row for row in programme.sources.sources if row.source_id == source_id)
    if len(selected) != 1:
        raise ValueError("prepared assay local phase substitutes a source outside the complete selected root")
    source, = selected
    allocations = tuple(row for row in programme.sources.allocations if row.allocation_id == source.original.allocation.object_id)
    if len(allocations) != 1:
        raise ValueError("prepared assay local phase substitutes its selected original allocation")
    allocation, = allocations
    protocol = dict(programme.protocols)[source.source_id]
    point_reference = programme.point_design.identity
    point_id = "external.point-design." + point_reference.object_fingerprint
    configs, links, records, arrays = prediction._source_contracts(source, allocation, protocol,
        programme_reference=programme_reference, point_id=point_id)
    records[point_id] = programme.point_design
    if type(config) is custody.MatrixPreparedFutureConfig:
        responses = tuple(row.record for row in context.config_inputs if type(row.record) is custody.MatrixPreparedFutureConfig
            and row.record.source.source_id == source.source_id and row.record.phase == "responses")
        if len(responses) != 1 or responses[0].programme != context.root.system:
            raise ValueError("prepared assay local future omits its exact selected paired response definition")
        selected, edges = _future_contracts(source, protocol, responses[0].panels,
            programme_reference=context.root.system, point_reference=point_reference, package_reference=programme.point_design.package.identity)
        configs.update(selected)
        links.extend(edges)
    expected_links = tuple(sorted((row for row in links if row.consumer_node_id == context.node_id), key=lambda row: row.edge_id))
    external_ids = {row.external_input_id for row in expected_links if row.external_input_id is not None}
    expected_external = tuple(sorted((*(prediction._record_external(key, value, prediction._record_id(value))
        for key, value in records.items() if key in external_ids),
        *(prediction._array_external(key, value) for key, value in arrays.items() if key in external_ids)), key=lambda row: row.input_id))
    groups = tuple(sorted({row.root.root.independent_group_id for row in programme.sources.sources}))
    phase = config.phase
    stage = ScientificStage.ACQUIRE if phase in ("history", "responses") else ScientificStage.FALSIFY if phase in ("assess", "frames", "response-score") else ScientificStage.DEVELOP
    if (configs.get(context.node_id) != config
            or tuple(row.record for row in context.config_inputs if row.node_id == context.node_id) != (config,)
            or tuple(row for row in context.links if row.consumer_node_id == context.node_id) != expected_links
            or tuple(row for row in context.external_inputs if row.input_id in external_ids) != expected_external
            or context.unit_ids != (source.root.root.independent_group_id,) or context.selected_unit_ids != groups
            or context.stage is not stage or context.complete_unit_census != (phase in ("history", "responses"))
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("prepared assay changes its exact local source/phase/edge/external projection under the mandatory complete root")


def _validate_complete_root(config, context):
    roots = tuple(row.record for row in context.config_inputs if type(row.record) is prediction.MatrixPreparedPredictionRootConfig)
    futures = tuple(row.record for row in context.config_inputs if type(row.record) is custody.MatrixPreparedFutureConfig and row.record.phase == "responses")
    if len(roots) != 1 or not futures or len({row.programme for row in futures}) != 1:
        raise ValueError("prepared assay requires exactly its complete prediction root and complete future selection")
    selected, = {row.programme for row in futures}
    programme = MatrixPreparedAssayProgramme(selected.object_id, roots[0].programme,
        tuple(sorted((row.source.source_id, row.panels) for row in futures)))
    if programme.identity != selected:
        raise ValueError("prepared assay changes complete frozen source/future selection bytes")
    expected, links, external, _, _ = contracts(programme)
    phase = "design" if type(config) is prediction.MatrixPreparedPredictionRootConfig else config.phase
    stage = ScientificStage.ACQUIRE if phase in ("history", "responses") else ScientificStage.FALSIFY if phase in ("assess", "frames", "response-score") else ScientificStage.DEVELOP
    units = tuple(sorted({row.root.root.independent_group_id for row in programme.prediction.sources.sources}))
    projected = future.units(config) if type(config) is custody.MatrixPreparedFutureConfig else prediction.units(config)
    if (tuple((row.node_id, row.record) for row in context.config_inputs) != expected or tuple(context.links) != links
            or tuple(context.external_inputs) != external or context.root != development_root(programme, context.root.study_id)
            or context.unit_ids != projected or context.selected_unit_ids != units or context.stage is not stage
            or context.complete_unit_census != (phase in ("history", "responses"))
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or dict(expected).get(context.node_id) != config):
        raise ValueError("prepared assay changes its exact full graph, complete phase/source census or external contracts")


def scientific_root_validator(config, context):
    selected_root, programme_reference = _selected_prediction_root(context)
    if type(config) is prediction.MatrixPreparedPredictionRootConfig:
        if context.node_id != selected_root.node_id or config != selected_root.record:
            raise ValueError("prepared assay substitutes its selected complete design root configuration")
        _validate_complete_root(config, context)
    elif type(config) in (prediction.MatrixPreparedPredictionConfig, prediction.source_owner.MatrixPreparationOperationConfig, custody.MatrixPreparedFutureConfig):
        _validate_local_projection(config, context, selected_root, programme_reference)
    else:
        raise TypeError("prepared assay requires its exact complete-root or source-specific configuration owner")


def operation_declarations():
    base = tuple(replace(row, capability_key="matrix-prepared-assay." + row.capability_key.rsplit(".", 1)[-1],
        implementation_id="matrix-prepared-assay." + row.capability_key.rsplit(".", 1)[-1] + ".v1",
        scientific_hooks=replace(row.scientific_hooks, scientific_root_validator=scientific_root_validator)) for row in prediction.operation_declarations())
    return tuple(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest()))
        for row in sorted((*base, *future.operation_declarations()), key=lambda row: row.capability_key))


@dataclass(frozen=True, slots=True)
class LoweredPreparedAssay:
    draft: RecursiveStudyDraft
    input_records: tuple
    input_artifacts: tuple


def lower_prepared_assay(programme, *, campaign, draft_id):
    if type(programme) is not MatrixPreparedAssayProgramme:
        raise TypeError("prepared assay lowering requires its complete immutable typed programme")
    programme.__post_init__()
    configs, links, external, records, arrays = contracts(programme)
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    operations = []
    for node, config in configs:
        phase = "design" if type(config) is prediction.MatrixPreparedPredictionRootConfig else config.phase
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declarations[phase].registration().selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=prediction.source_owner.BUDGET))
    study = development_root(programme, "study." + draft_id)
    selected_campaign = replace(campaign, objective=prediction.QUESTION, system_ids=(programme.identity.object_id,), world_ids=(prediction.WORLD,),
        target_claim_ids=tuple(row.claim_id for row in study.claims))
    draft = RecursiveStudyDraft(draft_id, prediction.QUESTION, selected_campaign, (), (), (), tuple(operations), external, links,
        tuple(node for node, _ in configs), development_study=study)
    return LoweredPreparedAssay(draft, records, arrays)
