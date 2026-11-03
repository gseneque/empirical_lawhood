# SPDX-License-Identifier: MPL-2.0
"""Pure copied-input preparation for current native TRAIN acquisition."""
from dataclasses import dataclass
from decimal import getcontext
from functools import lru_cache
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentInputs)
from . import native_training_records as r

PROTOCOL_ID = "matrix.response-error.native-training-acquisition"
QUESTION = "What are the complete native paired response-error TRAIN measurements under the declared fresh preparation and causal cutoff?"
WORLD = "world.matrix-native-training.current-paired-scheduled"


def _pin(value):
    return r.identity(value)


def entry_task_id(specification):
    key = specification.specification_id if type(specification) is r.NativeTrainingAcquisitionSpecification else specification.object_id
    return r.NAMESPACE + "." + key + ".entry"


def terminal_task_id(specification):
    return entry_task_id(specification).removesuffix("entry") + "terminal"


def task_id(root_id, operation):
    return r.NAMESPACE + "." + root_id + "." + operation


def development_root(specification, request, study_id):
    groups = tuple(sorted(value.root.independent_group_id for value in request.train_manifest.reservation.allocation.roots))
    views = tuple(sorted({view.view_id for value in request.train_manifest.reservation.allocation.coordinates
        for view in (value.primary_view, value.fine_view)}))
    claim = ClaimSpec("claim." + study_id, WORLD, request.record_id, QUESTION,
        "Every assigned whole TRAIN group, all declared response endpoints at both declared numerical views, including all nonuse and adverse outcomes.",
        "unit.original-whole-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Native training measurements only; no fit, IID/sampling, qualification, calibration, or future evaluation claim.",
        ("assumption.native-training.actual-declared-source",), numerical_view_ids=views)
    operands = tuple(sorted((specification.identity, request.identity, specification.candidate,
        specification.future_reservation, r.identity(request.train_manifest.reservation)), key=lambda value: value.object_id))
    if len({value.object_id for value in operands}) != len(operands):
        raise ValueError("native TRAIN source operands alias distinct scientific records")
    return DevelopmentStudySpec(study_id, QUESTION, request.identity, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        groups, views, (claim,), operands)


def contracts(specification, request):
    context = getcontext()
    signature = (context.prec, context.rounding, context.Emin, context.Emax, context.clamp, context.capitals,
        tuple(sorted((signal.__name__, enabled) for signal, enabled in context.traps.items())))
    return _contracts(signature, specification, request)


@lru_cache(maxsize=2)
def _contracts(_decimal_context, specification, request):
    """Two immutable pure layouts; no grants, receipts, reads or authority cached."""
    from . import native_training_bindings as b
    r.validate_request(specification, request)
    specification_pin, request_pin = specification.identity, request.identity
    configs, externals, links, records, files = {}, {}, [], {}, {}
    entry, terminal = entry_task_id(specification), terminal_task_id(specification)
    configs[entry] = b.NativeTrainingEntryConfig("config." + entry, specification, request)
    configs[terminal] = b.NativeTrainingOperationConfig("config." + terminal, "terminal", specification_pin,
        request_pin, None, None, None, (), request.resources.for_operation("terminal"), (),
        tuple(sorted(value.root.independent_group_id for value in request.train_manifest.reservation.allocation.roots)))

    def record(value, logical):
        key = "external." + logical
        item = RecursiveExternalInput(key, logical, value.SCHEMA, "application/json", len(value.canonical_bytes()),
            b.DEV, b.EXPOSED, value.fingerprint(), "SOURCE")
        if externals.setdefault(key, item) != item or records.setdefault(key, value) != value:
            raise ValueError("native TRAIN aliases distinct immutable source bytes")
        return key

    def file(artifact):
        key = "external." + artifact.artifact_id
        item = RecursiveExternalInput(key, artifact.artifact_id, artifact.payload_schema, artifact.media_type,
            artifact.size_bytes, b.DEV, b.EXPOSED, artifact.sha256, "SOURCE")
        if externals.setdefault(key, item) != item or files.setdefault(key, artifact) != artifact:
            raise ValueError("native TRAIN substitutes shared original template bytes")
        return key

    def edge(node, name, *, external=None, producer=None, output="product"):
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=external,
            producer_node_id=producer, producer_output_id=output if producer is not None else None,
            scientific_role="SOURCE" if external is not None else "HISTORY"))

    specification_input = record(specification, specification.specification_id)
    manifest_input = record(request.train_manifest, request.train_manifest.record_id)
    index = ScheduledSourceIndex.from_shared(reservation=request.train_manifest.reservation,
        specification=request.train_manifest.native_specification, provenances=request.train_manifest.provenances)
    index.require_roster(request.sources, expected_root_ids=index.root_ids)
    for descriptor, protocol in zip(request.sources, request.protocols, strict=True):
        source = r.source_for(request, descriptor.root_id, index=index)
        panels = r.panels_for(request, source)
        provenance = record(source.provenance, source.provenance.identity.object_id)
        for operation in r.PHASES:
            node = task_id(source.root_id, operation)
            public = operation in ("feature", "physical-forecast")
            selected_protocol = r.identity(protocol) if operation in ("feature", "physical-forecast", "responses", "response-score") else None
            curve_feature = operation == 'feature' and request.candidate_specification.is_curve_primary
            config_kind = b.NativeCurveTrainingFeatureConfig if curve_feature else b.NativeTrainingOperationConfig
            configs[node] = config_kind("config." + node, operation, specification_pin, request_pin,
                None if public else descriptor, protocol.public_source if public else None, selected_protocol,
                panels if operation in ("responses", "response-score") else (), request.resources.for_operation(operation),
                () if public or operation == "prefix" else tuple((phase, r.identity(configs[task_id(source.root_id, phase)]))
                    for phase in (("prefix", "responses") if operation == "response-score" else ("prefix",))),
                **({'candidate': request.candidate_specification} if curve_feature else {}))
            for name in b.INPUTS[operation]:
                if name == "specification":
                    edge(node, name, external=specification_input)
                elif name == "source":
                    edge(node, name, external=record(descriptor, descriptor.source_id))
                elif name == "coordinate":
                    edge(node, name, external=record(source.coordinate, source.coordinate.coordinate_id))
                elif name == "protocol":
                    edge(node, name, external=record(protocol, protocol.protocol_id))
                elif name == "manifest":
                    edge(node, name, external=manifest_input)
                elif name == "provenance":
                    edge(node, name, external=provenance)
                elif name == "templates":
                    edge(node, name, external=file(protocol.templates.array_artifact))
                elif name == "streams":
                    for stream in source.root.streams:
                        edge(node, "streams.source." + stream.purpose,
                            external=record(stream, source.root.stream_identity(stream).object_id))
                    if operation == "responses":
                        for panel in panels:
                            if panel.role == "INDEPENDENT_FUTURE":
                                for stream in panel.streams:
                                    edge(node, "streams.future." + panel.panel_id + "." + stream.purpose,
                                        external=record(stream, panel.stream_identity(stream).object_id))
                elif name == "acquisition":
                    edge(node, name, producer=entry)
                else:
                    owner, output = b.OWNERS[name]
                    edge(node, name, producer=task_id(source.root_id, owner), output=output)
        edge(terminal, "features." + source.root_id, producer=task_id(source.root_id, "feature"))
        edge(terminal, "outcomes." + source.root_id, producer=task_id(source.root_id, "response-score"))
    edge(terminal, "specification", external=specification_input)
    edge(terminal, "acquisition", producer=entry)
    return (tuple(sorted(configs.items())), tuple(sorted(externals.values(), key=lambda value: value.input_id)),
        tuple(sorted(links, key=lambda value: value.edge_id)), tuple(sorted(records.items())), tuple(sorted(files.items())))


def lower(specification, request):
    from .native_training_bindings import config_phase, config_capability_suffix, operation_declarations
    configs, external, links, records, files = contracts(specification, request)
    declarations = {value.capability_key.rsplit(".", 1)[-1]: value for value in operation_declarations()}
    root = development_root(specification, request, "study." + specification.specification_id)
    if (request.campaign.objective != root.question or request.campaign.system_ids != (root.system.object_id,)
            or request.campaign.world_ids != (root.world_id,) or request.campaign.target_claim_ids != tuple(value.claim_id for value in root.claims)):
        raise ValueError("native TRAIN campaign changes complete declared scientific question/claims")
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node,
        selection=declarations[config_capability_suffix(config)].registration().selection, config_id=config.record_id, config=config,
        obligation_ids=("obligation." + node + ".complete-selected-scope",),
        resource_budget=request.resources.for_operation(config_phase(config))) for node, config in configs)
    if not request.campaign.budget.contains(ResourceBudget.aggregate(tuple(value.resource_budget for value in operations))):
        raise ValueError("native TRAIN campaign does not cover its actual complete task-resource aggregate")
    draft = RecursiveStudyDraft("draft." + specification.specification_id, root.question, request.campaign, (), (), (),
        operations, external, links, tuple(node for node, _ in configs), development_study=root)
    return draft, records, files


@dataclass(frozen=True, slots=True)
class NativeTrainingAcquisitionInputs:
    request: r.NativeTrainingAcquisitionRequest | None = None
    files: tuple = ()


def bind_inputs(specification, records, *, files=None, record_paths=None):
    if set(records) - {"request"}:
        raise ValueError("native TRAIN accepts only its complete declared request")
    request = records.get("request")
    if request is not None:
        if type(request) is not r.NativeTrainingAcquisitionRequest:
            raise TypeError('native TRAIN acquisition requires its exact acquisition request, not an export selection')
        r.validate_request(specification, request)
    allocation = None if request is None else r.training_allocation(specification, request)
    return PreparedExperimentInputs({} if allocation is None else {"native-training": allocation},
        NativeTrainingAcquisitionInputs(request, tuple(sorted((files or {}).items()))))


def prepare(specification, *, execution, method_inputs=None, **_kwargs):
    from .native_training_bindings import NATIVE
    specification.__post_init__()
    inputs = method_inputs if type(method_inputs) is NativeTrainingAcquisitionInputs else NativeTrainingAcquisitionInputs()
    dependencies = []
    request, allocation, draft, records, files, design = inputs.request, None, None, (), (), ()
    for name, category in (("workers", DependencyKind.ENVIRONMENT), ("environment_id", DependencyKind.ENVIRONMENT),
            ("source_snapshot", DependencyKind.ENVIRONMENT), ("output_root", DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency("native-training.execution." + name.replace("_", "-"), category,
                "Select the explicit existing execution operand " + name + "."))
    if request is None:
        dependencies.append(ExperimentDependency("native-training.request", DependencyKind.EXTERNAL_INPUT,
            "Supply the exact pre-published TRAIN/future source, exposure, paired protocol and operational selections.", "request"))
    else:
        allocation = r.training_allocation(specification, request)
        if execution.workers is not None and execution.workers != request.resources.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency("native-training.worker-selection", DependencyKind.ENVIRONMENT,
                "Workers differ from the explicit declared task placement."))
        draft, records, identities = lower(specification, request)
        available, selected = dict(inputs.files), []
        for key, artifact in identities:
            value = available.get(artifact.artifact_id)
            if value is None:
                dependencies.append(ExperimentDependency("native-training.file." + artifact.artifact_id,
                    DependencyKind.EXTERNAL_INPUT, "Supply original exact template bytes.", artifact.artifact_id))
            elif value.identity != artifact:
                raise ValueError("native TRAIN source file changes original exact template identity")
            else:
                selected.append((key, value))
        files, design = tuple(selected), ((request.record_id, request),)
        if dependencies:
            # A dependency report cannot publish a partially bound executable graph.
            draft, records, files = None, (), ()
    count = len(specification.root_ids)
    census = ExperimentCensus((("train", count),), (("train", count if request is not None else 0),),
        tuple(sorted((operation, 1 if operation in ("entry", "terminal") else count) for operation in r.ALL_PHASES)),
        (("native-response-targets", specification.measurement.endpoint_count * len(specification.measurement.numerical_views) * count),
         ("selected-tasks", len(r.PHASES) * count + len(r.ALL_PHASES) - len(r.PHASES)), ("training-rows", count)),
        len(NATIVE) * count)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda value: value.code)),
        allocation=allocation, draft=draft, input_records=records, execution=execution,
        specification_record=specification, design_records=design, input_files=files)


def validate_instance(*, specification, allocation, draft, source_records):
    requests = tuple(value for _, value in source_records if type(value) is r.NativeTrainingAcquisitionRequest)
    if len(requests) != 1:
        raise ValueError("native TRAIN instance lacks its one exact original declared request")
    request, = requests
    expected, _, _ = lower(specification, request)
    if draft != expected or allocation != r.training_allocation(specification, request):
        raise ValueError("native TRAIN instance substitutes its exact declared graph/allocation")


def export_training_banks(specification, request, *, acquisition, features, outcomes, record_id):
    allocation = r.training_allocation(specification, request)
    if type(acquisition) is not r.NativeTrainingAcquisitionSeal or acquisition != r.acquisition_seal(specification, request):
        raise ValueError("native TRAIN export changes actual completed acquisition seal")
    features = tuple(sorted(features, key=lambda value: value.unit_id))
    outcomes = tuple(sorted(outcomes, key=lambda value: value.unit_id))
    feature_bank = r.NativeTrainingFeatureBank(record_id + ".features", allocation.identity, "train", features, acquisition.identity)
    outcome_bank = r.NativeTrainingOutcomeBank(record_id + ".outcomes", allocation.identity, "train", outcomes, acquisition.identity)
    r.validate_native_training_banks(request.candidate_specification, allocation, feature_bank, outcome_bank)
    expected = {protocol.public_source.root.independent_group_id: protocol.public_source for protocol in request.protocols}
    for feature, outcome in zip(features, outcomes, strict=True):
        public = expected[feature.unit_id]
        if (feature.native_source != public.source or feature.clock_id != public.root.clock_id
                or feature.source_manifest != request.identity or acquisition.identity not in outcome.evidence):
            raise ValueError("native TRAIN export changes exact current source or actual acquisition lineage")
    return allocation, feature_bank, outcome_bank
