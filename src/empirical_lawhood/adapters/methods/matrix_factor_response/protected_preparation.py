# SPDX-License-Identifier: MPL-2.0
"""Closed protected E3 preparation over original metadata and lazy data files."""

from collections import Counter
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage, validate_experiment_entry
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt, StudyDraft
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceTaskCellSpec, NonTimeResourceBudget, ProgressLivenessContract,
)
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

from .experiment_methods import MatrixE3FeatureBank, MatrixE3OutcomeBank
from .protected_experiment_inputs import ProtectedE3SourceInputs, project_protected_e3_allocation
from .protected_protocol import ProtectedE3ProtocolProjection, validate_protected_e3_response_selection
from .protected_response_records import ProtectedE3ResponseNumericalProfile, _object
from .protected_source_records import ProtectedE3NativeSourceManifest, ProtectedE3ResponseSelection, identity
from .protected_statistical_bindings import ProtectedE3FitConfig
from .response_frontier import MatrixResponseFrontierProtocol

RESOURCE_BINDING_DEPENDENCY = "matrix.e3.resource-projection"
RESOURCE_CLASSES = ("adjudicate", "assess", "calibrate", "calibration-freeze", "check", "feature", "fit",
    "forecast", "measure", "model-freeze", "numerical", "physical-forecast", "prefix", "project", "response-score", "responses")


class ProtectedE3ResourceCapacityError(ValueError):
    """Selected operational ceilings cannot contain the derived complete graph."""


@dataclass(frozen=True, slots=True)
class ProtectedE3OperationResources(CanonicalRecord):
    """An optional phase-wide operational choice, independent of task IDs."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-operation-resources"
    operation_class: str
    resource_budget: NonTimeResourceBudget
    progress_liveness: ProgressLivenessContract | None = None

    def __post_init__(self):
        if self.operation_class not in RESOURCE_CLASSES:
            raise ValueError("protected E3 resource override names an unknown operation class")
        if type(self.resource_budget) is not NonTimeResourceBudget:
            raise TypeError("protected E3 resource override requires its exact finite budget")
        self.resource_budget.__post_init__()
        if self.progress_liveness is not None:
            if type(self.progress_liveness) is not ProgressLivenessContract:
                raise TypeError("protected E3 resource override requires its exact progress contract")
            self.progress_liveness.__post_init__()
            if self.operation_class not in ("prefix", "responses"):
                raise ValueError("protected E3 pure operation cannot select native progress")


@dataclass(frozen=True, slots=True)
class ProtectedE3ResourceSelection(CanonicalRecord):
    """Caller ceilings and defaults; the lowerer derives the complete task census.

    The empty-cell shared selection supplies the envelope's ordinary controls.
    Its single child token limit is a capacity ceiling; the resolved shared
    selection freezes exact demand beneath that ceiling. Neither projection
    changes the selected scientific authority policy.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-resource-selection"
    resources: ExecutionResourceSelection
    default_budget: NonTimeResourceBudget
    native_progress: ProgressLivenessContract
    operation_overrides: tuple[ProtectedE3OperationResources, ...] = ()

    def __post_init__(self):
        for name, kind in (("resources", ExecutionResourceSelection), ("default_budget", NonTimeResourceBudget),
                ("native_progress", ProgressLivenessContract)):
            if type(getattr(self, name)) is not kind:
                raise TypeError("protected E3 resource rules require their exact " + name + " type")
            getattr(self, name).__post_init__()
        controls = self.resources
        if (controls.task_cells or len(controls.child_token_limits) != 1 or controls.roster_capacity_branches
                or controls.predevelopment_jit_signature_census is not None or controls.jit_graph_signature_manifest is not None):
            raise ValueError("protected E3 resource rules require empty task cells, one child capacity and no JIT/branch roster")
        if controls.child_token_limits[0].retry_token_limit != 0:
            raise ValueError("protected E3 native resource rules do not authorize repeated acquisition")
        if (type(self.operation_overrides) is not tuple or any(type(row) is not ProtectedE3OperationResources
                for row in self.operation_overrides) or tuple(row.operation_class for row in self.operation_overrides)
                != tuple(sorted({row.operation_class for row in self.operation_overrides}))):
            raise ValueError("protected E3 resource overrides require exact sorted unique operation classes")
        for row in self.operation_overrides:
            row.__post_init__()


def _resolve_protected_e3_resources(selection, configs):
    from .protected_lowering import operation_class, task_id

    chosen = selection.resource_selection
    expected = {task_id(config): config for config in configs}
    if len(expected) != len(configs):
        raise ValueError("protected E3 resource projection aliases generated tasks")
    if type(chosen) is ExecutionResourceSelection:
        cells = {cell.task_id: cell for cell in chosen.task_cells}
        if set(cells) != set(expected) or len(cells) != len(chosen.task_cells):
            raise ValueError("protected E3 resources must cover exactly every selected task")
        return chosen
    if type(chosen) is not ProtectedE3ResourceSelection:
        raise TypeError("protected E3 resources require one exact supported selection")
    chosen.__post_init__()
    controls = chosen.resources
    capacity, = controls.child_token_limits
    overrides = {row.operation_class: row for row in chosen.operation_overrides}
    cells = []
    for node, config in sorted(expected.items()):
        phase = operation_class(config)
        override = overrides.get(phase)
        budget = chosen.default_budget if override is None else override.resource_budget
        native = phase in ("prefix", "responses")
        progress = (chosen.native_progress if override is None or override.progress_liveness is None
            else override.progress_liveness) if native else None
        unit = config.source.root.root.independent_group_id if native else None
        cells.append(ExecutionResourceTaskCellSpec("cell." + node, node, capacity.child_id,
            unit, "preparation." + node if native else None, 1, int(native), int(native), native,
            replace(budget, budget_id="budget." + node),
            replace(progress, contract_id="liveness." + node) if progress is not None else None, None, None))
    native_count = sum(cell.physical_execution_cost for cell in cells)
    if native_count > capacity.physical_execution_token_limit:
        raise ProtectedE3ResourceCapacityError("The complete selected E3 graph requires " + str(native_count)
            + " native execution tokens; the explicit caller ceiling is " + str(capacity.physical_execution_token_limit) + ".")
    if any(cell.resource_budget.memory_bytes > controls.aggregate_memory_ceiling_bytes for cell in cells):
        raise ProtectedE3ResourceCapacityError("An E3 operation budget exceeds the explicit aggregate memory ceiling.")
    return replace(controls, task_cells=tuple(cells), child_token_limits=(ChildResourceTokenLimit(
        capacity.child_id, native_count, 0),))


def derive_protected_e3_resource_selection(preparation):
    """Use the same exact lowering owner at the public authoring boundary."""
    from .protected_lowering import lower_protected_matrix_response_error

    selected, = (record for _, record in preparation.design_records if type(record) is ProtectedE3PreparationSelection)
    if preparation.specification_record is None or preparation.allocation is None or preparation.draft is None:
        raise ValueError("protected E3 resource binding needs its actual complete preparation")
    lowered = lower_protected_matrix_response_error(preparation.specification_record, preparation.allocation, selected)
    if lowered.draft.operations != preparation.draft.operations:
        raise ValueError("protected E3 resource binding changes its actual selected operation graph")
    return lowered.resource_selection


@dataclass(frozen=True, slots=True)
class ProtectedE3PreparationSelection(CanonicalRecord):
    """Original scientific inputs once, separate from current execution choices.

    Empty qualification/configuration tuples support a nonexecuting design
    preview. They remain explicit entry dependencies until actually supplied.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-preparation-selection"
    VERSION: ClassVar[str] = '2.0.0'
    selection_id: str
    root: StudyDraft
    entry_package: ExperimentEntryPackage
    fit_config: ProtectedE3FitConfig
    manifest: ProtectedE3NativeSourceManifest
    training_allocation: UnitAllocation
    sources: tuple[ScheduledSource, ...]
    projections: tuple[ProtectedE3ProtocolProjection, ...]
    mathematical_protocol: MatrixResponseFrontierProtocol
    response_selection: ProtectedE3ResponseSelection
    protocols: tuple[ScheduledResponseProtocol, ...]
    panels: tuple[ScheduledResponsePanel, ...]
    numerical_profiles: tuple[ProtectedE3ResponseNumericalProfile, ...]
    training_features: ArtifactIdentity
    training_outcomes: ArtifactIdentity
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    resource_selection: ExecutionResourceSelection | ProtectedE3ResourceSelection
    qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    source_configs: tuple[SourceMaterializationConfig, ...] = ()
    numerical_qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    numerical_containers: tuple[ScheduledResponseSelection | ProtectedE3ResponseSelection | ScheduledResponseProtocol, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        for name, kind in (("root", StudyDraft), ("entry_package", ExperimentEntryPackage), ("fit_config", ProtectedE3FitConfig),
                ("manifest", ProtectedE3NativeSourceManifest), ("training_allocation", UnitAllocation),
                ("mathematical_protocol", MatrixResponseFrontierProtocol), ("response_selection", ProtectedE3ResponseSelection),
                ("training_features", ArtifactIdentity), ("training_outcomes", ArtifactIdentity),
                ("formal_methods", FormalMethodCatalog)):
            value = getattr(self, name)
            if type(value) is not kind:
                raise TypeError("protected E3 preparation changes its exact " + name + " type")
            value.__post_init__()
        if type(self.resource_selection) not in (ExecutionResourceSelection, ProtectedE3ResourceSelection):
            raise TypeError("protected E3 preparation changes its exact resource selection type")
        self.resource_selection.__post_init__()
        for name, kind in (("sources", ScheduledSource), ("projections", ProtectedE3ProtocolProjection),
                ("protocols", ScheduledResponseProtocol), ("panels", ScheduledResponsePanel),
                ("numerical_profiles", ProtectedE3ResponseNumericalProfile),
                ("formal_source_inventories", FormalGapSourceCapabilityInventory),
                ("qualifications", MaterializationQualificationReceipt), ("source_configs", SourceMaterializationConfig),
                ("numerical_qualifications", MaterializationQualificationReceipt)):
            rows = getattr(self, name)
            if type(rows) is not tuple or any(type(row) is not kind for row in rows):
                raise TypeError("protected E3 preparation changes its exact " + name + " roster")
            for row in rows:
                row.__post_init__()
        if (type(self.numerical_containers) is not tuple or any(type(row) not in
                (ScheduledResponseSelection, ProtectedE3ResponseSelection, ScheduledResponseProtocol) for row in self.numerical_containers)):
            raise TypeError("protected E3 original numerical containers require their exact supported types")
        for row in self.numerical_containers:
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class ProtectedE3ExperimentInputs:
    selection: ProtectedE3PreparationSelection | None = None
    files: tuple[tuple[str, PreparedExperimentFile], ...] = ()

    def __post_init__(self):
        if self.selection is not None:
            if type(self.selection) is not ProtectedE3PreparationSelection:
                raise TypeError("protected E3 input requires its exact original selection")
            self.selection.__post_init__()
        if (type(self.files) is not tuple or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or any(type(row) is not PreparedExperimentFile or key != row.identity.artifact_id for key, row in self.files)):
            raise ValueError("protected E3 files require exact original logical IDs and typed locations")


def source_inputs(specification, selection):
    coordinates = {row.primary_view.bath_temperature: row for row in selection.manifest.reservation.allocation.coordinates}
    return ProtectedE3SourceInputs(specification, selection.training_allocation, selection.manifest.reservation,
        selection.manifest.native_specification, coordinates[Decimal(1)], coordinates[Decimal("1.25")], coordinates[Decimal(3)])


def validate_selection_science(specification, allocation, selection):
    if type(selection) is not ProtectedE3PreparationSelection:
        raise TypeError("protected E3 lowering requires its exact current preparation selection")
    selection.__post_init__()
    if (selection.root.question != specification.question or selection.root.system is None
            or selection.root.experiment is None or selection.root.campaign is None):
        raise ValueError("protected E3 preparation changes its selected scientific question or omits its complete prospective root")
    if project_protected_e3_allocation(source_inputs(specification, selection)) != allocation:
        raise ValueError("protected E3 preparation changes its complete original role allocation")
    validate_protected_e3_response_selection(selection.response_selection, specification=specification,
        manifest=selection.manifest, projections=selection.projections, mathematical_protocol=selection.mathematical_protocol,
        sources=selection.sources, protocols=selection.protocols, panels=selection.panels)
    if (len(selection.numerical_profiles) != len(selection.protocols)
            or {p.original_protocol for p in selection.numerical_profiles} != {_object(p) for p in selection.protocols}):
        raise ValueError("protected E3 preparation drops or substitutes original response numerical profiles")
    for container in selection.numerical_containers:
        if type(container) is ScheduledResponseSelection:
            container.validate_allocation(selection.manifest.reservation.allocation)
    profiles = {p.original_protocol: p for p in selection.numerical_profiles}
    numerical_qualifications = {ObjectIdentity.from_record(q.receipt_id, q): q for q in selection.numerical_qualifications}
    containers = {_object(row): row for row in (selection.response_selection, *selection.protocols, *selection.numerical_containers)}
    for protocol in selection.protocols:
        profile = profiles[_object(protocol)]
        profile.validate_protocol(protocol)
        if profile.qualification not in numerical_qualifications or profile.provenance_container not in containers:
            raise ValueError("protected E3 requires its actual original qualified numerical container")
        profile.validate_original(protocol, provenance=containers[profile.provenance_container],
            publication=profile.provenance_publication, qualification=numerical_qualifications[profile.qualification])
    for artifact, kind in ((selection.training_features, MatrixE3FeatureBank), (selection.training_outcomes, MatrixE3OutcomeBank)):
        if artifact.payload_schema != kind.SCHEMA or artifact.media_type != "application/json" or not artifact.size_bytes:
            raise ValueError("protected E3 preparation changes original lazy TRAIN bank type")
    fit = selection.fit_config
    if (fit.original_publications is None or fit.original_publications.specification != specification.identity
            or fit.original_publications.source_manifest != identity(selection.manifest)
            or fit.original_publications.training_allocation != selection.training_allocation.identity):
        raise ValueError("protected E3 preparation omits its exact global original-publication custody")
    for _, _, availability in fit.publications:
        fit.fit_cutoff.require_allows(availability)


def bind_protected_e3_experiment_inputs(specification, records, *, files=None, record_paths=None):
    if set(records) - {"protected-selection"}:
        raise ValueError("protected E3 inputs require only their closed protected-selection record")
    selection = records.get("protected-selection")
    inputs = ProtectedE3ExperimentInputs(selection, tuple(sorted((files or {}).items())))
    allocation = None if selection is None else project_protected_e3_allocation(source_inputs(specification, selection))
    return PreparedExperimentInputs({} if allocation is None else {p.source_key: allocation for p in specification.populations}, inputs)


def _source_projection(draft, selection, versions):
    # The existing domain-independent source record contracts are shared with
    # protected E4; this wrapper adds no source qualification or authority.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection as project

    return project(draft, selection, versions)


def derive_protected_e3_design_inputs(preparation):
    selection, = (row for _, row in preparation.design_records if type(row) is ProtectedE3PreparationSelection)
    entry = replace(selection.entry_package, checklist=replace(selection.entry_package.checklist,
        draft=ObjectIdentity.from_record(preparation.draft.prospective_draft.draft_id, preparation.draft.prospective_draft)))
    validate_experiment_entry(preparation.draft.prospective_draft, entry, for_issue=False)
    operands = tuple(RecursiveProspectiveOperand(row.logical_artifact_id, row.expected_content_sha256,
        row.maximum_size_bytes, row.payload_schema, row.media_type, row.outcome_access, row.visibility_ceiling)
        for row in sorted(preparation.draft.external_inputs, key=lambda row: row.logical_artifact_id))
    return RecursiveProspectiveDesignInputs(selection.selection_id + ".prospective", preparation.draft, entry,
        selection.formal_methods, selection.formal_source_inventories, selection.qualifications,
        preparation.draft.prospective_draft.design_inputs, operands, ())


def prepare_protected_e3(specification, *, execution, protocol_bytes, method_inputs=None, **_kwargs):
    from .experiment_preparation import _protocol_errors
    from .protected_lowering import lower_protected_matrix_response_error

    dependencies = [ExperimentDependency("matrix.e3.protocol." + str(i), DependencyKind.EXTERNAL_INPUT, reason, "prediction-protocol")
        for i, reason in enumerate(_protocol_errors(specification, protocol_bytes))]
    for name, kind in (("environment", DependencyKind.ENVIRONMENT), ("source-snapshot", DependencyKind.ENVIRONMENT), ("output-root", DependencyKind.STORAGE)):
        if getattr(execution, name.replace("-", "_") + ("_id" if name == "environment" else "")) is None:
            dependencies.append(ExperimentDependency("matrix.e3." + name, kind, "Select the existing route's explicit " + name + " before execution."))
    counts = tuple(sorted((p.role.lower(), p.expected_units) for p in specification.populations))
    selected_counts = dict(counts)
    query_count = selected_counts["calibration"] + selected_counts["evaluation"]
    if specification.calibration_target_view is None:
        dependencies.append(ExperimentDependency("matrix.e3.calibration-target-view", DependencyKind.SCIENTIFIC_EVIDENCE,
            "Select MAX_PAIRED_VIEWS calibration targets before calibration observations."))
    if specification.minimum_successes > selected_counts["evaluation"]:
        dependencies.append(ExperimentDependency("matrix.e3.evaluation-resolution", DependencyKind.SCIENTIFIC_EVIDENCE,
            "The complete evaluation census cannot reach the selected exact alpha even if every root succeeds."))
    allocation, draft, records, files, design = None, None, (), (), ()
    operations = tuple(sorted((name, query_count if name in ("prefix", "numerical", "measure", "check", "project",
        "feature", "forecast", "physical-forecast", "responses", "response-score") else 1)
        for name in ("fit", "model-freeze", "calibrate", "calibration-freeze", "assess", "adjudicate", "prefix", "numerical", "measure",
            "check", "project", "feature", "forecast", "physical-forecast", "responses", "response-score")))
    outputs = tuple(sorted((
        ("all-origin-features", next(m.feature_count for m in specification.methods if m.method_key == "ALL_ORIGIN_RIDGE")),
        ("calibration-rank", specification.calibration_rank), ("calibration-unit-scores", selected_counts["calibration"]),
        ("evaluation-unit-decisions", selected_counts["evaluation"]), ("fitted-models", len(specification.methods)),
        ("minimum-primary-successes", specification.minimum_successes),
        ("point-forecast-endpoints", query_count * specification.measurement.endpoint_count * len(specification.methods)),
        ("response-view-endpoints", (selected_counts["train"] + query_count) * specification.measurement.endpoint_count * len(specification.measurement.numerical_views)),
        ("selected-tasks", query_count * 10 + 6),
        ("spectral-features", next(m.feature_count for m in specification.methods if m.method_key == "SPECTRAL_RIDGE")),
    )))
    native = 2 * query_count
    inputs = method_inputs if type(method_inputs) is ProtectedE3ExperimentInputs else ProtectedE3ExperimentInputs()
    selection = inputs.selection
    if selection is None:
        dependencies.append(ExperimentDependency("matrix.e3.protected-selection", DependencyKind.EXTERNAL_INPUT,
            "Supply original source/reservation publications, selected TRAIN files, paired protocols and the current prospective entry selection.", "protected-selection"))
    else:
        allocation = project_protected_e3_allocation(source_inputs(specification, selection))
        try:
            lowered = lower_protected_matrix_response_error(specification, allocation, selection)
        except ProtectedE3ResourceCapacityError as error:
            dependencies.append(ExperimentDependency("matrix.e3.resource-capacity", DependencyKind.ENVIRONMENT, str(error)))
            census = ExperimentCensus(counts, counts, operations, outputs, native)
            return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
                allocation=allocation, execution=execution, specification_record=specification,
                design_records=((selection.selection_id, selection),))
        if execution.workers is not None and execution.workers != lowered.resource_selection.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency("matrix.e3.worker-resource-selection", DependencyKind.ENVIRONMENT,
                "Selected workers differ from the frozen protected resource selection; choose consistent inputs before authoring."))
        draft, records = lowered.draft, lowered.input_records
        policy_budget = draft.prospective_draft.system.authority_policy.budget_ceiling
        if not all(policy_budget.contains(value) for value in
                (draft.campaign.budget, draft.prospective_draft.resource_ceiling)):
            dependencies.append(ExperimentDependency("matrix.e3.authority-resource-budget", DependencyKind.AUTHORITY,
                "The selected authority policy does not cover both the complete task-resource aggregate and the candidate execution ceiling; preparation cannot broaden that policy."))
        versions = {row.logical_artifact_id: dict(records)[row.input_id].VERSION for row in draft.external_inputs if row.input_id in dict(records)}
        bound_files = dict(inputs.files)
        selected_files = []
        for key, artifact in lowered.file_identities:
            value = bound_files.get(artifact.artifact_id)
            if value is None:
                dependencies.append(ExperimentDependency("matrix.e3.file." + artifact.artifact_id, DependencyKind.EXTERNAL_INPUT,
                    "Supply the exact original lazy scientific file.", artifact.artifact_id))
            elif value.identity != artifact:
                raise ValueError("protected E3 file substitutes its exact declared original bytes")
            else:
                selected_files.append((key, value))
                versions[artifact.artifact_id] = value.record_version
        if set(bound_files) - {row.artifact_id for _, row in lowered.file_identities}:
            raise ValueError("protected E3 preparation adds an undeclared scientific file")
        files = tuple(sorted(selected_files))
        if selection.qualifications and selection.source_configs and len(files) == len(lowered.file_identities):
            draft = _source_projection(draft, selection, versions)
        else:
            dependencies.append(ExperimentDependency("matrix.e3.source-qualification", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Supply actual exact source qualification/configuration for every declared input; metadata and labels confer no eligibility."))
        # Incomplete file bindings must remain a preflight, not a partial wave.
        if len(files) != len(lowered.file_identities):
            records, files, draft = (), (), None
        design = ((selection.selection_id, selection),)
        operations = tuple(sorted(Counter(row.selection.capability_key.rsplit(".", 1)[-1] for row in lowered.draft.operations).items()))
        native = sum(count for name, count in operations if name in ("prefix", "responses"))
        dependencies.append(ExperimentDependency(RESOURCE_BINDING_DEPENDENCY, DependencyKind.SOFTWARE,
            "Bind the selected execution resources to the actual public candidate preview during authoring."))
    census = ExperimentCensus(counts, counts if allocation is not None else tuple((name, 0) for name, _ in counts), operations, outputs, native)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=draft, input_records=records, input_files=files, execution=execution,
        specification_record=specification, design_records=design)


def validate_protected_e3_experiment_instance(*, specification, allocation, draft, source_records):
    from .protected_lowering import lower_protected_matrix_response_error

    if (type(source_records) is not tuple or len(source_records) != 1
            or type(source_records[0][1]) is not ProtectedE3PreparationSelection):
        raise ValueError("protected E3 instance loses its one exact original preparation selection")
    key, selection = source_records[0]
    if key != selection.selection_id:
        raise ValueError("protected E3 instance substitutes its original selection identity")
    lowered = lower_protected_matrix_response_error(specification, allocation, selection)
    versions = {row.logical_artifact_id: dict(lowered.input_records)[row.input_id].VERSION
        for row in lowered.draft.external_inputs if row.input_id in dict(lowered.input_records)}
    versions.update((artifact.artifact_id, "1.0.0") for _, artifact in lowered.file_identities)
    expected = _source_projection(lowered.draft, selection, versions)
    if draft != expected:
        raise ValueError("protected E3 instance changes its complete specification-derived graph or original source inputs")
