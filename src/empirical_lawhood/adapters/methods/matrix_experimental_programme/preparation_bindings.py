# SPDX-License-Identifier: MPL-2.0
"""Ordinary guarded native lifecycle for selected coupling-only preparations.

This additive development route cannot qualify prospective roots. Registration
and full E5 composition belong to their respective composition owners.
"""

from dataclasses import dataclass, replace
from functools import partial
from typing import ClassVar


from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from . import preparation_science as science
from .preparation_records import MatrixPreparationAssessment, MatrixPreparationHistory, MatrixPreparationSource, preparation_identity


NAMESPACE = "matrix-coupling-preparation"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
QUESTION = "Retain complete coupling-only matched preparations and independently check every original paired native equation."
WORLD = "world.matrix-coupling-preparation.development"


@dataclass(frozen=True, slots=True)
class MatrixPreparationOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-operation-config"
    config_id: str
    phase: str
    source: MatrixPreparationSource
    allocation_size_bytes: int

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (type(self.source) is not MatrixPreparationSource or self.phase not in ("history", "assess")
                or self.config_id != "config." + node_id(self.source, self.phase)
                or type(self.allocation_size_bytes) is not int or self.allocation_size_bytes < 1):
            raise ValueError("preparation operation changes its exact source/phase")
        self.source.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixPreparationOperationConfigV2(MatrixPreparationOperationConfig):
    """Actual direct native carriers; the scientific source is unchanged."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-operation-config-v2"

    def __post_init__(self):
        MatrixPreparationOperationConfig.__post_init__(self)
        if self.phase != "history":
            raise ValueError("direct native preparation config selects only history acquisition")


def native_input_records(source, *, panels=None):
    """Exact small direct operands for RNG actually used by this operation.

    Complete root/panel stream rosters remain allocation/exposure premises;
    initialization consumes none, preparation uses its pair, future each panel's
    autonomous pair. This projection grants no custody or execution authority.
    """
    from types import SimpleNamespace
    from .prepared_future_custody import stream_id
    values = [("native-provenance", source.provenance.identity, source.provenance)]
    if panels is None:
        streams = tuple((source.root.stream_identity(value), value) for value in source.root.streams
            if value.purpose.startswith("preparation"))
    else:
        config = SimpleNamespace(source=source, panels=panels)
        streams = tuple((stream_id(config, panel, value), value) for panel in panels for value in panel.streams
            if value.purpose.startswith("autonomous"))
    if len(streams) != (2 if panels is None else 4):
        raise ValueError("native operation loses its actual complete paired RNG purpose census")
    values.extend(("native-stream." + pin.object_fingerprint, pin, value) for pin, value in streams)
    return tuple(sorted(values, key=lambda row: row[0]))


def validate_native_input_records(config, received):
    expected = {name: value for name, _, value in native_input_records(config.source,
        panels=getattr(config, "panels", None))}
    observed = {name: value for name, value in received.items() if name == "native-provenance" or name.startswith("native-stream.")}
    if observed != expected:
        raise ValueError("native direct inputs substitute actual source provenance or used RNG purposes")


def native_config_types():
    from .selected_future import MatrixSelectedFutureConfigV2
    from .selected_opportunity_future import MatrixSelectedOpportunityFutureConfigV2
    from .selected_revision_future import MatrixRevisionFutureConfigV2
    return (MatrixPreparationOperationConfigV2, MatrixSelectedFutureConfigV2,
        MatrixSelectedOpportunityFutureConfigV2, MatrixRevisionFutureConfigV2)


def direct_native_declaration(declaration, *, config_type, runner_factory):
    from dataclasses import replace
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
    from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
    count = 2 if declaration.capability_key.endswith(".history") else 4
    inputs = (*declaration.input_ports,
        RecursivePortContract("native-provenance", NumericalProducingProvenance.SCHEMA, "application/json", None),
        RecursivePortContract("native-stream", MatrixHistorySeed.SCHEMA, "application/json", None,
            minimum_count=count, maximum_count=count))
    return replace(declaration, capability_key=declaration.capability_key + ".direct-inputs",
        capability_version="2.0.0", implementation_id=declaration.implementation_id + ".direct-inputs.v2",
        config_record_type=config_type, input_ports=tuple(sorted(inputs, key=lambda row: row.port_id)),
        runner_factory=runner_factory, record_codecs={**declaration.record_codecs,
            config_type.SCHEMA: config_type, NumericalProducingProvenance.SCHEMA: NumericalProducingProvenance,
            MatrixHistorySeed.SCHEMA: MatrixHistorySeed})


def node_id(source, phase):
    return NAMESPACE + "." + source.source_id + "." + phase


def external_id(source, key):
    if key == "allocation":
        return "external.allocation." + source.original.allocation.object_fingerprint
    if key == "initial-state":
        return "external.initial-state." + source.initial.array_artifact.sha256
    return "external." + source.source_id + ".source"


def operands(source):
    return tuple(sorted((source.identity, source.original.allocation, source.initial.identity,
        source.recipe.identity, source.provenance.identity), key=lambda row: row.object_id))


def operand_digests(config):
    return tuple(sorted({row.object_fingerprint for row in operands(config.source)}))


def units(config):
    return (config.source.root.root.independent_group_id,)


def slots(config):
    return (config.source.source_id + ".paired-preparation",)


def development_root(sources, study_id):
    sources = tuple(sorted(sources, key=lambda row: row.source_id))
    if (not sources or len({row.source_id for row in sources}) != len(sources)
            or any(row.root.root.role is not MatrixProgrammeRole.DEVELOPMENT for row in sources)):
        raise ValueError("prepared development root requires its complete distinct selected source census")
    groups = tuple(sorted({row.root.root.independent_group_id for row in sources}))
    views = tuple(sorted({view.view_id for row in sources for view in (row.primary_view, row.fine_view)}))
    claim = ClaimSpec("claim." + study_id, WORLD, "population.matrix-preparation.selected", QUESTION,
        "Every selected matched source, both numerical views and every integration state/innovation; one independent unit per original whole group.",
        "unit.original-whole-group", None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, "No functional benefit, cross-preparation applicability, freshness, prospective issue or qualification.",
        ("assumption.matrix-preparation.selected-original-source",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, sources[0].original.allocation, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        groups, views, (claim,), tuple(sorted({operand for source in sources for operand in operands(source)}, key=lambda row: row.object_id)))


def scientific_root_validator(config, context):
    selected = tuple(row.record for row in context.config_inputs)
    if any(type(row) is not MatrixPreparationOperationConfig for row in selected):
        raise ValueError("prepared native graph mixes foreign scientific configurations")
    sources = tuple(row.source for row in selected if row.phase == "history")
    if (len(selected) != 2 * len(sources) or not sources
            or {row.source.source_id for row in selected} != {row.source_id for row in sources}
            or any(tuple(row.phase for row in selected if row.source.source_id == source.source_id) not in
                (("history", "assess"), ("assess", "history")) for source in sources)
            or any(row.source != next(source for source in sources if source.source_id == row.source.source_id) for row in selected)
            or context.root != development_root(sources, context.root.study_id)
            or context.node_id != node_id(config.source, config.phase) or context.unit_ids != units(config)
            or context.selected_unit_ids != context.root.assigned_unit_ids
            or context.stage is not (ScientificStage.ACQUIRE if config.phase == "history" else ScientificStage.FALSIFY)
            or context.complete_unit_census != (config.phase == "history")
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("prepared native graph changes its complete selected source/group/phase/access census")
    external = {}
    for selected_config in selected:
        source = selected_config.source
        for row in (
                RecursiveExternalInput(external_id(source, "source"), source.source_id, source.SCHEMA, "application/json",
                    len(source.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, source.fingerprint(), "SOURCE"),
                RecursiveExternalInput(external_id(source, "allocation"), source.original.allocation.object_id, ScheduledAllocation.SCHEMA,
                    "application/json", selected_config.allocation_size_bytes, OutcomeAccess.DEVELOPMENT_VISIBLE,
                    VisibilityCeiling.DEVELOPMENT_ONLY, source.original.allocation.object_fingerprint, "SOURCE"),
                RecursiveExternalInput(external_id(source, "initial-state"), source.initial.array_artifact.artifact_id, MATRIX_ARRAY_SCHEMA,
                    "application/x-npz", source.initial.array_artifact.size_bytes, OutcomeAccess.DEVELOPMENT_VISIBLE,
                    VisibilityCeiling.DEVELOPMENT_ONLY, source.initial.array_artifact.sha256, "SOURCE")):
            if external.setdefault(row.input_id, row) != row:
                raise ValueError("prepared native configurations disagree on exact shared external contracts")
    if tuple(context.external_inputs) != tuple(sorted(external.values(), key=lambda row: row.input_id)):
        raise ValueError("prepared native graph substitutes original external identity/digest/size/access contracts")
    expected = {"source", "allocation", "initial-state"} | ({"history", "history-arrays"} if config.phase == "assess" else set())
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    if len(incoming) != len(expected) or {row.consumer_input_id for row in incoming} != expected:
        raise ValueError("prepared native graph omits an actual original source/initial/history operand")
    for link in incoming:
        if link.consumer_input_id in ("history", "history-arrays"):
            if (link.producer_node_id != node_id(config.source, "history") or link.external_input_id is not None
                    or link.producer_output_id != ("arrays" if link.consumer_input_id == "history-arrays" else "product")
                    or link.scientific_role != "HISTORY"):
                raise ValueError("prepared assessor substitutes its actual producer history/bytes")
        elif (link.external_input_id != external_id(config.source, link.consumer_input_id)
                or link.producer_node_id is not None or link.scientific_role != "SOURCE"):
            raise ValueError("prepared native source is not the exact declared external operand")


def _decode(context, phase):
    codecs = {kind.SCHEMA: kind for kind in (MatrixPreparationOperationConfig, MatrixPreparationSource, ScheduledAllocation)}
    if phase == "assess":
        codecs[MatrixPreparationHistory.SCHEMA] = MatrixPreparationHistory
    records, raw_ports = {}, []
    for port in context.input_ports:
        if port.payload_schema == MATRIX_ARRAY_SCHEMA:
            raw_ports.append(port)
        elif port.payload_schema in codecs and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(), codecs[port.payload_schema], maximum_bytes=port.size_bytes)
        else:
            raise ValueError("prepared worker receives an extra or repeated original input")
    if set(records) != set(codecs):
        raise ValueError("prepared worker omits an exact typed scientific operand")
    config, source, allocation = (records[kind.SCHEMA] for kind in (MatrixPreparationOperationConfig, MatrixPreparationSource, ScheduledAllocation))
    source.validate_allocation(allocation)
    artifacts = {"initial-state": source.initial.array_artifact}
    if phase == "assess":
        artifacts["history-arrays"] = records[MatrixPreparationHistory.SCHEMA].arrays.array_artifact
    arrays = {}
    for port in raw_ports:
        keys = tuple(key for key, artifact in artifacts.items() if (port.artifact_id, port.payload_schema, port.media_type, port.size_bytes) ==
            (artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes))
        if len(keys) != 1 or keys[0] in arrays:
            raise ValueError("prepared worker substitutes or duplicates its exact original raw array binding")
        arrays[keys[0]] = port
    expected_arrays = {"initial-state"} | ({"history-arrays"} if phase == "assess" else set())
    if (config.phase != phase or config.source != source or context.task_id != node_id(source, phase)
            or config.allocation_size_bytes != len(allocation.canonical_bytes())
            or context.config.config_id != config.config_id or context.config.content_sha256 != config.fingerprint()
            or context.permissions != next(row for row in operation_declarations() if row.capability_key.endswith("." + phase)).permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET
            or set(arrays) != expected_arrays):
        raise ValueError("prepared worker substitutes exact config/source/native array census")
    return config, source, records, arrays


def native_definition(context, config, source, expected_parent):
    direct = type(config) is MatrixPreparationOperationConfigV2
    sources = tuple(sorted((source.identity, source.original.allocation, source.provenance.identity),
        key=lambda row: row.object_id)) if direct else operands(source)
    streams = tuple(sorted((pin for name, pin, _ in native_input_records(source) if name.startswith("native-stream.")),
        key=lambda row: row.object_id)) if direct else tuple(sorted((source.root.stream_identity(row)
            for row in source.root.streams), key=lambda row: row.object_id))
    return NativeSubworkDefinition("subwork." + source.source_id + ".paired-preparation",
        NAMESPACE + (".native.direct-inputs.v2" if direct else ".native.v1"), expected_parent,
        preparation_identity(config), sources, source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256,
        tuple(sorted(port.materialization_id for port in context.input_ports)),
        streams,
        (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),))


def initial_native_work(context, config, source, expected_parent):
    definition = native_definition(context, config, source, expected_parent)
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, units(config), slots(config), (definition,), (roster,))


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not MatrixPreparationNativeRunner:
        raise ValueError("prepared native projection needs its installed native runner")
    config, source, _, arrays = _decode(context, "history")
    # Authenticate original finite initial bytes before any BEGIN/RNG/contact.
    science.initial_state(source.initial, arrays["initial-state"].read())
    return initial_native_work(context, config, source, expected_parent)


def _retained(source, initial_raw, raw):
    from .prepared_native_body import _retained as retained

    return retained(source, initial_raw, raw)


def _outputs(context, product, raw=None):
    payloads = {"product": product.canonical_bytes()}
    if raw is not None:
        payloads["arrays"] = raw
    expected = {context.task_id + "." + key for key in payloads}
    if {port.output_id for port in context.output_ports} != expected:
        raise ValueError("prepared worker changes its actual compiler-derived output census")
    return RunnerResult(tuple(TaskOutputPayload(context.task_id + "." + key, value) for key, value in sorted(payloads.items())),
        (ReceiptCheck("complete-preparation-native-source-and-independent-equations", True, ()),))


class MatrixPreparationAssessor:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            _, source, records, ports = _decode(context, "assess")
            history = records[MatrixPreparationHistory.SCHEMA]
            history.validate_source(source, records[ScheduledAllocation.SCHEMA])
            initial = ports["initial-state"].read()
            raw = ports["history-arrays"].read()
            arrays = science.consume_preparation_arrays(source, initial, history.arrays, raw)
            assessment = science.assess_preparation_arrays(source, initial, history.arrays, arrays,
                assessment_id="assessment." + source.source_id)
            return _outputs(context, assessment)
        finally:
            for port in context.input_ports:
                port.close()


class MatrixPreparationNativeRunner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        raise ValueError("prepared native source requires actual selected native lifecycle authority")

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, source, records, ports = _decode(context, "history")
            initial = ports["initial-state"].read()
            science.initial_state(source.initial, initial)
            work = initial_native_work(context, config, source, native_subwork.parent_contact)
            from .prepared_native_body import _execute_preparation_native

            product, raw = _execute_preparation_native(context, source, records[ScheduledAllocation.SCHEMA], initial, native_subwork, work, progress=progress)
            return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    codecs = {kind.SCHEMA: kind for kind in (MatrixPreparationOperationConfig, MatrixPreparationSource, ScheduledAllocation,
        MatrixPreparationHistory, MatrixPreparationAssessment)}
    declarations = tuple(RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + phase, capability_version="1.0.0", implementation_id=NAMESPACE + "." + phase + ".v1",
        kind=CapabilityKind.SIMULATOR if phase == "history" else CapabilityKind.FALSIFIER, config_record_type=MatrixPreparationOperationConfig,
        stage=ScientificStage.ACQUIRE if phase == "history" else ScientificStage.FALSIFY,
        input_ports=tuple(sorted((RecursivePortContract("source", MatrixPreparationSource.SCHEMA, "application/json", None),
            RecursivePortContract("allocation", ScheduledAllocation.SCHEMA, "application/json", None),
            RecursivePortContract("initial-state", MATRIX_ARRAY_SCHEMA, "application/x-npz", MAXIMUM_MATRIX_ARRAY_BYTES),
            *((RecursivePortContract("history", MatrixPreparationHistory.SCHEMA, "application/json", None),
               RecursivePortContract("history-arrays", MATRIX_ARRAY_SCHEMA, "application/x-npz", MAXIMUM_MATRIX_ARRAY_BYTES))
              if phase == "assess" else ())), key=lambda row: row.port_id)),
        outputs=tuple(sorted((OutputTemplate("product", MatrixPreparationHistory.SCHEMA if phase == "history" else MatrixPreparationAssessment.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
            *((OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"),)
                if phase == "history" else ())), key=lambda row: row.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=tuple(sorted(("complete-paired-preparation-census", "original-native-equations", "original-custody-no-replay"))),
        runner_factory=MatrixPreparationNativeRunner if phase == "history" else MatrixPreparationAssessor, record_codecs=codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operand_digests, scientific_unit_ids=units,
            native_effect_slot_ids=slots if phase == "history" else None, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=phase == "history", complete_unit_census=phase == "history",
            native_work_preparer=prepare_native_work if phase == "history" else None),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        for phase in ("assess", "history"))
    return tuple(replace(row, runner_factory=partial(row.runner_factory, manifest=row.manifest()))
        for row in declarations)


@dataclass(frozen=True, slots=True)
class LoweredPreparationSources:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]
    initial_artifacts: tuple[tuple[str, ArtifactIdentity], ...]


def lower_preparation_sources(sources, *, allocations, campaign, draft_id):
    sources = tuple(sorted(sources, key=lambda row: row.source_id))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity
    by_allocation = {original_identity(row): row for row in allocations}
    if set(by_allocation) != {source.original.allocation for source in sources}:
        raise ValueError("preparation lowering requires exactly the selected original allocation census")
    records, artifacts, external, links, operations = {}, {}, {}, [], []
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    for source in sources:
        source.validate_allocation(by_allocation[source.original.allocation])
        for key, record in (("source", source), ("allocation", by_allocation[source.original.allocation])):
            input_id = external_id(source, key)
            records[input_id] = record
            object_id = source.source_id if key == "source" else record.allocation_id
            external[input_id] = RecursiveExternalInput(input_id, object_id, record.SCHEMA, "application/json", len(record.canonical_bytes()),
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint(), "SOURCE")
        input_id = external_id(source, "initial-state")
        artifacts[input_id] = source.initial.array_artifact
        artifact = source.initial.array_artifact
        external[input_id] = RecursiveExternalInput(input_id, artifact.artifact_id, MATRIX_ARRAY_SCHEMA, "application/x-npz", artifact.size_bytes,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, artifact.sha256, "SOURCE")
        for phase in ("history", "assess"):
            node = node_id(source, phase)
            config = MatrixPreparationOperationConfig("config." + node, phase, source,
                len(by_allocation[source.original.allocation].canonical_bytes()))
            operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declarations[phase].registration().selection,
                config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=BUDGET))
            for key in ("source", "allocation", "initial-state"):
                links.append(RecursiveInputLink("edge." + node + "." + key, node, key,
                    external_input_id=external_id(source, key), scientific_role="SOURCE"))
            if phase == "assess":
                for key, output in (("history", "product"), ("history-arrays", "arrays")):
                    links.append(RecursiveInputLink("edge." + node + "." + key, node, key, producer_node_id=node_id(source, "history"),
                        producer_output_id=output, scientific_role="HISTORY"))
    study = development_root(sources, "study." + draft_id)
    selected_campaign = replace(campaign, objective=QUESTION, system_ids=(study.system.object_id,), world_ids=(WORLD,),
        target_claim_ids=tuple(row.claim_id for row in study.claims))
    draft = RecursiveStudyDraft(draft_id, QUESTION, selected_campaign, (), (), (), tuple(sorted(operations, key=lambda row: row.node_id)),
        tuple(sorted(external.values(), key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id)),
        tuple(sorted(row.node_id for row in operations)), development_study=study)
    return LoweredPreparationSources(draft, tuple(sorted(records.items())), tuple(sorted(artifacts.items())))
