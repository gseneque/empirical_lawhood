# SPDX-License-Identifier: MPL-2.0
"""Closed protected E3 preparation over original metadata and lazy data files."""

from collections import Counter
from collections.abc import Mapping
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar
from .configured_secondary_readout import MatrixE3SecondaryTarget, MatrixE3SecondaryReadoutSelection
from .configured_primary_amendment import MatrixE3PrimaryFamilyAmendmentBinding
from .configured_census import feature_counts

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage, validate_experiment_entry
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, MaterializationQualificationReceipt, StudyDraft
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit, ExecutionResourceTaskCellSpec
from .protected_preparation import ProtectedE3ResourceSelection, ProtectedE3ResourceCapacityError
from .protected_source_records import ProtectedE3ResponseSelection as OriginalProtectedE3ResponseSelection
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

from .configured_protected_methods import training_bank_types
from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_inputs import ConfiguredProtectedE3SourceInputs, project_protected_e3_allocation
from .configured_protected_protocol import ConfiguredProtectedE3ProtocolProjection, validate_protected_e3_response_selection
from .configured_protected_response_records import ConfiguredProtectedE3ResponseNumericalProfile, _object
from .configured_protected_source_records import ProtectedE3NativeSourceManifest, ConfiguredProtectedE3ResponseSelection, identity
from .configured_protected_statistical_bindings import ConfiguredProtectedE3FitConfig
from .response_frontier import MatrixResponseFrontierProtocol

RESOURCE_BINDING_DEPENDENCY = "matrix.e3.resource-projection"
RESOURCE_CLASSES = ("adjudicate", "assess", "calibrate", "calibration-freeze", "check", "feature", "fit",
    "forecast", "measure", "model-freeze", "numerical", "physical-forecast", "prefix", "project", "response-score", "responses")








def _resolve_protected_e3_resources(selection, configs):
    from .configured_protected_lowering import operation_class, task_id
    from .configured_retained_execution import ConfiguredE3RetainedTaskConfig

    chosen = selection.resource_selection
    expected = {task_id(config): config for config in configs}
    if len(expected) != len(configs):
        raise ValueError("protected E3 resource projection aliases generated tasks")
    if type(chosen) is ExecutionResourceSelection:
        cells = {cell.task_id: cell for cell in chosen.task_cells}
        if set(cells) != set(expected) or len(cells) != len(chosen.task_cells):
            raise ValueError("protected E3 resources must cover exactly every selected task")
        if any(type(config) is ConfiguredE3RetainedTaskConfig and (
                cells[node].native_simulator_launch or cells[node].physical_execution_cost
                or cells[node].retry_token_cost or cells[node].progress_liveness is not None)
                for node, config in expected.items()):
            raise ValueError('retained E3 resources cannot reserve native work for an exact byte adoption')
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
        native = phase in ("prefix", "responses") and type(config) is not ConfiguredE3RetainedTaskConfig
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
    from .configured_protected_lowering import lower_protected_matrix_response_error

    selected, = (record for _, record in preparation.design_records if type(record) in configured_preparation_types())
    if preparation.specification_record is None or preparation.allocation is None or preparation.draft is None:
        raise ValueError("protected E3 resource binding needs its actual complete preparation")
    lowered = lower_protected_matrix_response_error(preparation.specification_record, preparation.allocation, selected)
    if lowered.draft.operations != preparation.draft.operations:
        raise ValueError("protected E3 resource binding changes its actual selected operation graph")
    return lowered.resource_selection


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3PreparationSelection(CanonicalRecord):
    """Original scientific inputs once, separate from current execution choices.

    Empty qualification/configuration tuples support a nonexecuting design
    preview. They remain explicit entry dependencies until actually supplied.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-preparation-selection"
    VERSION: ClassVar[str] = "4.0.0"
    selection_id: str
    root: StudyDraft
    entry_package: ExperimentEntryPackage
    fit_config: ConfiguredProtectedE3FitConfig
    manifest: ProtectedE3NativeSourceManifest
    training_allocation: UnitAllocation
    sources: tuple[ScheduledSource, ...]
    projections: tuple[ConfiguredProtectedE3ProtocolProjection, ...]
    mathematical_protocol: MatrixResponseFrontierProtocol
    response_selection: ConfiguredProtectedE3ResponseSelection
    protocols: tuple[ScheduledResponseProtocol, ...]
    panels: tuple[ScheduledResponsePanel, ...]
    numerical_profiles: tuple[ConfiguredProtectedE3ResponseNumericalProfile, ...]
    training_features: ArtifactIdentity
    training_outcomes: ArtifactIdentity
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    resource_selection: ExecutionResourceSelection | ProtectedE3ResourceSelection
    qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    source_configs: tuple[SourceMaterializationConfig, ...] = ()
    numerical_qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    numerical_containers: tuple[ScheduledResponseSelection | ConfiguredProtectedE3ResponseSelection | OriginalProtectedE3ResponseSelection | ScheduledResponseProtocol, ...] = ()
    secondary_readout: MatrixE3SecondaryReadoutSelection | None = None
    primary_amendment: MatrixE3PrimaryFamilyAmendmentBinding | None = None

    def __post_init__(self):
        _validate_scientific_inputs(self)
        for value, kind in ((self.entry_package, ExperimentEntryPackage), (self.formal_methods, FormalMethodCatalog)):
            if type(value) is not kind:
                raise TypeError("protected E3 preparation changes its exact current entry or formal catalog")
            value.__post_init__()
        if type(self.formal_source_inventories) is not tuple or any(
                type(row) is not FormalGapSourceCapabilityInventory for row in self.formal_source_inventories):
            raise TypeError("protected E3 preparation changes its exact formal inventory roster")
        for row in self.formal_source_inventories:
            row.__post_init__()
        if self.secondary_readout is not None:
            if type(self.secondary_readout) is not MatrixE3SecondaryReadoutSelection:
                raise TypeError("configured secondary selection changes its exact target owner")
            self.secondary_readout.__post_init__()
            if self.secondary_readout.mathematical_protocol != self.mathematical_protocol.identity:
                raise ValueError("secondary target changes the selected response-task mathematics")
            pin = self.secondary_readout.identity
            rows = tuple(row for row in self.root.design_inputs if row.object_identity == pin)
            expected = DesignInputRecord(self.selection_id + ".secondary-response-target", pin, pin.object_fingerprint,
                self.fit_config.fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
                VisibilityCeiling.PROSPECTIVE, self.root.system.authority_policy.delegate_id)
            if rows != (expected,):
                raise ValueError("configured secondary target is absent from the actual frozen scientific root")

        if self.primary_amendment is not None:
            if type(self.primary_amendment) is not MatrixE3PrimaryFamilyAmendmentBinding:
                raise TypeError("configured V3 requires its exact explicit primary amendment binding")
            self.primary_amendment.validate_selection(self)
            pin = self.primary_amendment.identity
            expected = DesignInputRecord(self.selection_id + ".primary-family-amendment", pin, pin.object_fingerprint,
                self.fit_config.fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
                VisibilityCeiling.PROSPECTIVE, self.root.system.authority_policy.delegate_id)
            if tuple(row for row in self.root.design_inputs if row.object_identity == pin) != (expected,):
                raise ValueError("primary amendment is absent from the actual frozen scientific root")


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3LoweringInputs:
    """Actual science before ordinary compilation constructs its current entry.

    This inward value is never a canonical preparation, issue or publication.
    """
    selection_id: str
    root: StudyDraft
    fit_config: ConfiguredProtectedE3FitConfig
    manifest: ProtectedE3NativeSourceManifest
    training_allocation: UnitAllocation
    sources: tuple[ScheduledSource, ...]
    projections: tuple[ConfiguredProtectedE3ProtocolProjection, ...]
    mathematical_protocol: MatrixResponseFrontierProtocol
    response_selection: ConfiguredProtectedE3ResponseSelection
    protocols: tuple[ScheduledResponseProtocol, ...]
    panels: tuple[ScheduledResponsePanel, ...]
    numerical_profiles: tuple[ConfiguredProtectedE3ResponseNumericalProfile, ...]
    training_features: ArtifactIdentity
    training_outcomes: ArtifactIdentity
    resource_selection: ExecutionResourceSelection | ProtectedE3ResourceSelection
    qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    source_configs: tuple[SourceMaterializationConfig, ...] = ()
    numerical_qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    numerical_containers: tuple[ScheduledResponseSelection | ConfiguredProtectedE3ResponseSelection | OriginalProtectedE3ResponseSelection | ScheduledResponseProtocol, ...] = ()
    primary_amendment: MatrixE3PrimaryFamilyAmendmentBinding | None = None

    def __post_init__(self):
        _validate_scientific_inputs(self)
        if self.primary_amendment is not None:
            if type(self.primary_amendment) is not MatrixE3PrimaryFamilyAmendmentBinding:
                raise TypeError("configured lowering requires its exact primary amendment binding")
            self.primary_amendment.validate_selection(self)
            pin = self.primary_amendment.identity
            expected = DesignInputRecord(self.selection_id + ".primary-family-amendment", pin, pin.object_fingerprint,
                self.fit_config.fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
                VisibilityCeiling.PROSPECTIVE, self.root.system.authority_policy.delegate_id)
            if tuple(row for row in self.root.design_inputs if row.object_identity == pin) != (expected,):
                raise ValueError("primary amendment is absent from the actual frozen scientific root")


def _validate_scientific_inputs(self):
    validate_stable_id(self.selection_id)
    for name, kind in (("root", StudyDraft), ("fit_config", ConfiguredProtectedE3FitConfig),
            ("manifest", ProtectedE3NativeSourceManifest), ("training_allocation", UnitAllocation),
            ("mathematical_protocol", MatrixResponseFrontierProtocol), ("response_selection", ConfiguredProtectedE3ResponseSelection),
            ("training_features", ArtifactIdentity), ("training_outcomes", ArtifactIdentity)):
        value = getattr(self, name)
        if type(value) is not kind:
            raise TypeError("protected E3 preparation changes its exact " + name + " type")
        value.__post_init__()
    if type(self.resource_selection) not in (ExecutionResourceSelection, ProtectedE3ResourceSelection):
        raise TypeError("protected E3 preparation changes its exact resource selection type")
    self.resource_selection.__post_init__()
    for name, kind in (("sources", ScheduledSource), ("projections", ConfiguredProtectedE3ProtocolProjection),
            ("protocols", ScheduledResponseProtocol), ("panels", ScheduledResponsePanel),
            ("numerical_profiles", ConfiguredProtectedE3ResponseNumericalProfile),
            ("qualifications", MaterializationQualificationReceipt), ("source_configs", SourceMaterializationConfig),
            ("numerical_qualifications", MaterializationQualificationReceipt)):
        rows = getattr(self, name)
        if type(rows) is not tuple or any(type(row) is not kind for row in rows):
            raise TypeError("protected E3 preparation changes its exact " + name + " roster")
        for row in rows:
            row.__post_init__()
    if (type(self.numerical_containers) is not tuple or any(type(row) not in
            (ScheduledResponseSelection, ConfiguredProtectedE3ResponseSelection, OriginalProtectedE3ResponseSelection, ScheduledResponseProtocol) for row in self.numerical_containers)):
        raise TypeError("protected E3 original numerical containers require their exact supported types")
    for row in self.numerical_containers:
        row.__post_init__()


def configured_preparation_types():
    from .configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection
    return ConfiguredProtectedE3PreparationSelection, ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3ExperimentInputs:
    selection: ConfiguredProtectedE3PreparationSelection | None = None
    files: tuple[tuple[str, PreparedExperimentFile], ...] = ()
    secondary_target: MatrixE3SecondaryTarget | None = None

    def __post_init__(self):
        if self.selection is not None:
            if type(self.selection) not in configured_preparation_types():
                raise TypeError("protected E3 input requires its exact current selection")
            self.selection.__post_init__()
        if self.secondary_target is not None:
            if self.selection is None or type(self.secondary_target) is not MatrixE3SecondaryTarget:
                raise TypeError("secondary binding requires a current selection and direct scientific target")
            self.secondary_target.validate_selection(self.selection)
        if (type(self.files) is not tuple or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or any(type(row) is not PreparedExperimentFile or key != row.identity.artifact_id for key, row in self.files)):
            raise ValueError("protected E3 files require exact original logical IDs and typed locations")


def source_inputs(specification, selection):
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    coordinates = {coordinate_identity(row): row for row in selection.manifest.reservation.allocation.coordinates}
    chosen = dict(specification.role_coordinates)
    return ConfiguredProtectedE3SourceInputs(specification, selection.training_allocation, selection.manifest.reservation,
        selection.manifest.native_specification, coordinates[chosen["CALIBRATION"]],
        coordinates[chosen["TRANSFER_NEARBY"]], coordinates[chosen["TRANSFER_SHIFTED"]], selection.fit_config.training_coordinates)


def validate_selection_science(specification, allocation, selection):
    if type(selection) not in (*configured_preparation_types(), ConfiguredProtectedE3LoweringInputs):
        raise TypeError("protected E3 lowering requires exact current science or a preparation selection")
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
    kinds = training_bank_types(selection.training_features.payload_schema, selection.training_outcomes.payload_schema)
    for artifact, kind in zip((selection.training_features, selection.training_outcomes), kinds, strict=True):
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
    if set(records) - {"protected-selection", "secondary-target"}:
        raise ValueError("configured E3 inputs require the current selection and optional direct secondary target")
    selection = records.get("protected-selection")
    inputs = ConfiguredProtectedE3ExperimentInputs(selection, tuple(sorted((files or {}).items())),
        records.get("secondary-target"))
    allocation = None if selection is None else project_protected_e3_allocation(source_inputs(specification, selection))
    return PreparedExperimentInputs({} if allocation is None else {p.source_key: allocation for p in specification.populations}, inputs)


def _source_projection(draft, selection, versions):
    # The existing domain-independent source record contracts are shared with
    # protected E4; this wrapper adds no source qualification or authority.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection as project

    return project(draft, selection, versions)


def derive_protected_e3_design_inputs(preparation):
    selection, = (row for _, row in preparation.design_records if type(row) in configured_preparation_types())
    entry = replace(selection.entry_package, checklist=replace(selection.entry_package.checklist,
        draft=ObjectIdentity.from_record(preparation.draft.prospective_draft.draft_id, preparation.draft.prospective_draft)))
    validate_experiment_entry(preparation.draft.prospective_draft, entry, for_issue=False)
    operands = tuple(RecursiveProspectiveOperand(row.logical_artifact_id, row.expected_content_sha256,
        row.maximum_size_bytes, row.payload_schema, row.media_type, row.outcome_access, row.visibility_ceiling)
        for row in sorted(preparation.draft.external_inputs, key=lambda row: row.logical_artifact_id))
    return RecursiveProspectiveDesignInputs(selection.selection_id + ".prospective", preparation.draft, entry,
        selection.formal_methods, selection.formal_source_inventories, selection.qualifications,
        preparation.draft.prospective_draft.design_inputs, operands, ())


def frozen_native_source_dependency(provenances, execution):
    """Pure preflight for an opaque selected development source snapshot.

    A source binding retains its observed raw clean bit. Either observed status
    is compatible with the identical scientific source tuple; neither is a
    cleanliness gate. Exact closure snapshots retain their existing separate
    prospective source inspector and native preflight owners.
    """
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding

    snapshot = execution.source_snapshot
    if snapshot is None or snapshot.object_schema != RecursiveImplementationBinding.SCHEMA:
        return None
    for value in provenances:
        possibilities = tuple(ObjectIdentity.from_record("recursive-member.implementation",
            RecursiveImplementationBinding(value.package_sources, value.code_sources_sha256,
                value.dependency_lock_sha256, value.observed_git_head, clean)) for clean in (False, True))
        if snapshot not in possibilities:
            return ExperimentDependency("configured-assembly.restore-frozen-source", DependencyKind.ENVIRONMENT,
                "Select the exact frozen native source " + value.observed_git_head
                + " before public authoring or execution; a historical metadata reader is not a native implementation.")
    return None


def required_source_bindings(draft, selection, versions=None):
    """Exact missing current bindings; no qualification receipt is copied."""
    from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentDependency
    qualifications = {row.source_id: row for row in selection.qualifications}
    configs = {row.source_id: row for row in selection.source_configs}
    external = {row.input_id: row for row in draft.external_inputs}
    if set(qualifications) - set(external) or set(configs) - set(external):
        raise ValueError("configured request supplies bindings outside the actual derived source census")
    if len(qualifications) != len(selection.qualifications) or len(configs) != len(selection.source_configs):
        raise ValueError("configured request duplicates current qualification/source configuration roles")
    dependencies = []
    for key, row in sorted(external.items()):
        q, config = qualifications.get(key), configs.get(key)
        if q is not None and ((q.materialization.object_id, q.materialization.object_schema,
                q.materialization.object_fingerprint, q.content_sha256, q.evidence_world_id,
                q.outcome_access, q.visibility_ceiling) != (row.logical_artifact_id, row.payload_schema,
                row.expected_content_sha256, row.expected_content_sha256, draft.prospective_draft.system.world.world_id,
                row.outcome_access, row.visibility_ceiling) or versions is not None
                and row.logical_artifact_id in versions and q.materialization.object_version != versions[row.logical_artifact_id]):
            raise ValueError("configured request substitutes a supplied current qualification identity or access")
        if config is not None and ((config.content_sha256, config.payload_schema, config.media_type,
                config.expected_size_bytes, config.outcome_access, config.visibility_ceiling) !=
                (row.expected_content_sha256, row.payload_schema, row.media_type, row.maximum_size_bytes,
                    row.outcome_access, row.visibility_ceiling)):
            raise ValueError("configured request substitutes a supplied bounded source configuration")
        token = sha256(key.encode()).hexdigest()
        detail = (key + "; logical=" + row.logical_artifact_id + "; schema=" + row.payload_schema
            + "; sha256=" + row.expected_content_sha256 + "; bytes=" + str(row.maximum_size_bytes)
            + "; access=" + row.outcome_access.value + "; visibility=" + row.visibility_ceiling.value)
        if key not in qualifications:
            dependencies.append(ExperimentDependency("matrix.configured-e3.qualification." + token,
                DependencyKind.SCIENTIFIC_EVIDENCE, detail, key))
        if key not in configs:
            dependencies.append(ExperimentDependency("matrix.configured-e3.source-config." + token,
                DependencyKind.EXTERNAL_INPUT, detail, key))
    return tuple(sorted(dependencies, key=lambda row: row.code))


def prepare_protected_e3(specification, *, scientific_inputs, execution, protocol_bytes=None, method_inputs=None):
    if type(specification) is not MatrixResponseErrorSpecification or not isinstance(scientific_inputs, Mapping):
        raise TypeError("configured protected preparation needs its exact typed specification/input selections")
    specification.__post_init__()
    execution.__post_init__()
    if protocol_bytes is not None:
        raise ValueError("configured protected parameters are selected once in the typed protocol")
    if method_inputs is not None and type(method_inputs) is not ConfiguredProtectedE3ExperimentInputs:
        raise TypeError("configured protected preparation needs its exact bound method input owner")
    from .configured_protected_lowering import lower_protected_matrix_response_error

    dependencies = []
    if method_inputs is not None and method_inputs.secondary_target is not None:
        dependencies.append(ExperimentDependency("matrix.configured-e3.secondary-target-publication", DependencyKind.EXTERNAL_INPUT,
            "Publish and freeze the exact selected secondary target through ordinary configured input derivation before authoring.", "secondary-target"))
    if execution.workers is None:
        dependencies.append(ExperimentDependency("matrix.configured-e3.workers", DependencyKind.ENVIRONMENT,
            "Select explicit profile-consistent workers before authoring."))
    for name, kind in (("environment", DependencyKind.ENVIRONMENT), ("source-snapshot", DependencyKind.ENVIRONMENT), ("output-root", DependencyKind.STORAGE)):
        if getattr(execution, name.replace("-", "_") + ("_id" if name == "environment" else "")) is None:
            dependencies.append(ExperimentDependency("matrix.e3." + name, kind, "Select the existing route's explicit " + name + " before execution."))
    counts = tuple(sorted((p.role.lower(), p.expected_units) for p in specification.populations))
    selected_counts = dict(counts)
    query_count = selected_counts["calibration"] + selected_counts["evaluation"]
    if specification.minimum_successes > selected_counts["evaluation"]:
        dependencies.append(ExperimentDependency("matrix.e3.evaluation-resolution", DependencyKind.SCIENTIFIC_EVIDENCE,
            "The complete evaluation census cannot reach the selected exact alpha even if every root succeeds."))
    allocation, draft, records, files, design = None, None, (), (), ()
    operations = tuple(sorted((name, query_count if name in ("prefix", "numerical", "measure", "check", "project",
        "feature", "forecast", "physical-forecast", "responses", "response-score") else 1)
        for name in ("fit", "model-freeze", "calibrate", "calibration-freeze", "assess", "adjudicate", "prefix", "numerical", "measure",
            "check", "project", "feature", "forecast", "physical-forecast", "responses", "response-score")))
    outputs = tuple(sorted((
        *feature_counts(specification.methods),
        ("calibration-rank", specification.calibration_rank), ("calibration-unit-scores", selected_counts["calibration"]),
        ("evaluation-unit-decisions", selected_counts["evaluation"]), ("fitted-models", len(specification.methods)),
        ("minimum-primary-successes", specification.minimum_successes),
        ("point-forecast-endpoints", query_count * specification.measurement.point_endpoint_count * len(specification.methods)),
        ("response-view-endpoints", (selected_counts["train"] + query_count) * specification.measurement.endpoint_count * len(specification.measurement.numerical_views)),
        ("selected-tasks", query_count * 10 + 6),
    )))
    native = 2 * query_count
    inputs = method_inputs if type(method_inputs) is ConfiguredProtectedE3ExperimentInputs else ConfiguredProtectedE3ExperimentInputs()
    selection = inputs.selection
    if selection is None:
        dependencies.append(ExperimentDependency("matrix.e3.protected-selection", DependencyKind.EXTERNAL_INPUT,
            "Supply original source/reservation publications, selected TRAIN files, paired protocols and the current prospective entry selection.", "protected-selection"))
    else:
        provenances = (selection.retention.response_provenance,) if hasattr(selection, 'retention') else selection.manifest.provenances
        source_dependency = frozen_native_source_dependency(provenances, execution)
        if source_dependency is not None:
            dependencies.append(source_dependency)
        allocation = project_protected_e3_allocation(source_inputs(specification, selection))
        if scientific_inputs != {population.source_key: allocation for population in specification.populations}:
            dependencies.append(ExperimentDependency("matrix.configured-e3.allocation", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Preserve the complete exact original selected whole-unit allocation."))
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
        missing_bindings = required_source_bindings(draft, selection, versions)
        dependencies.extend(missing_bindings)
        if not missing_bindings and len(files) == len(lowered.file_identities):
            draft = _source_projection(draft, selection, versions)
        # Incomplete file bindings must remain a preflight, not a partial wave.
        if len(files) != len(lowered.file_identities):
            records, files, draft = (), (), None
        design = ((selection.selection_id, selection),)
        operations = tuple(sorted(Counter(row.selection.capability_key.rsplit(".", 1)[-1] for row in lowered.draft.operations
            if row.node_id in lowered.draft.selected_operation_ids).items()))
        native = sum(count for name, count in operations if name in ("prefix", "responses", 'continued-responses'))
        if hasattr(selection, 'unfinished'):
            outputs = tuple(sorted((*((key, value) for key, value in outputs if key != 'selected-tasks'),
                ('selected-tasks', len(lowered.draft.selected_operation_ids)), ('retained-task-copies', 0),
                ('retained-completed-tasks', len(selection.unfinished.completed_receipts)))))
        elif hasattr(selection, 'retention'):
            outputs = tuple(sorted((*outputs, ('retained-task-copies', len(selection.retained_tasks)))))
        dependencies.append(ExperimentDependency(RESOURCE_BINDING_DEPENDENCY, DependencyKind.SOFTWARE,
            "Bind the selected execution resources to the actual public candidate preview during authoring."))
    census = ExperimentCensus(counts, counts if allocation is not None else tuple((name, 0) for name, _ in counts), operations, outputs, native)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=draft, input_records=records, input_files=files, execution=execution,
        specification_record=specification, design_records=design)


def validate_protected_e3_experiment_instance(*, specification, allocation, draft, source_records):
    from .configured_protected_lowering import lower_protected_matrix_response_error

    if (type(source_records) is not tuple or len(source_records) != 1
            or type(source_records[0][1]) not in configured_preparation_types()):
        raise ValueError("protected E3 instance loses its one exact original preparation selection")
    key, selection = source_records[0]
    if key != selection.selection_id:
        raise ValueError("protected E3 instance substitutes its original selection identity")
    lowered = lower_protected_matrix_response_error(specification, allocation, selection)
    versions = {row.logical_artifact_id: dict(lowered.input_records)[row.input_id].VERSION
        for row in lowered.draft.external_inputs if row.input_id in dict(lowered.input_records)}
    versions.update((artifact.artifact_id, "1.0.0") for _, artifact in lowered.file_identities)
    if hasattr(selection, 'retention'):
        from .configured_retained_preparation import retained_file_versions
        versions.update(retained_file_versions(selection))
    for artifact, kind in zip((selection.training_features, selection.training_outcomes),
            training_bank_types(selection.training_features.payload_schema, selection.training_outcomes.payload_schema), strict=True):
        versions[artifact.artifact_id] = kind.VERSION
    expected = _source_projection(lowered.draft, selection, versions)
    if draft != expected:
        raise ValueError("protected E3 instance changes its complete specification-derived graph or original source inputs")
