# SPDX-License-Identifier: MPL-2.0
"""Derive the protected E4 graph without reading confirmation outcomes.

Original source custody and current scientific authorities are replayed by the
existing Matrix API at handoff and worker entry. These pure projections cannot
replace that owner, qualify sampling assumptions or issue an experiment.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
from empirical_lawhood.planning.study_authoring import SourceAccessDisposition, SourceMaterializationRef, SourceMaterializationRole
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
    PreparedExperimentFile, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand

from .programme_factorial_confirmation import assess_node_id, input_seal_node_id
from .programme_factorial_confirmation_composition import lower_factorial_confirmation
from .programme_factorial_confirmation_custody import require_original_criteria_design
from .programme_reduction import ScheduledProgrammeReduction
from .programme_selection import ScheduledRevisionDataBank
from .protected_factorial_inputs import (ProtectedFactorialOriginalSource, ProtectedFactorialPreparationRequest,
    ProtectedFactorialPreparationSelection, validate_protected_factorial_request_binding)
from .protected_factorial_specification import ProtectedFactorialExperimentSpecification
from .records import identity


INPUT_TYPES = {"original": ProtectedFactorialOriginalSource, "preparation": ProtectedFactorialPreparationSelection}
PAIRED_TYPES = {"data": ScheduledRevisionDataBank, "reduction": ScheduledProgrammeReduction}


@dataclass(frozen=True, slots=True)
class ProtectedFactorialExperimentInputs:
    original: ProtectedFactorialOriginalSource | None = None
    preparation: ProtectedFactorialPreparationSelection | None = None
    files: tuple[tuple[str, PreparedExperimentFile], ...] = ()
    request: ProtectedFactorialPreparationRequest | None = None

    def __post_init__(self):
        if self.preparation is not None and self.request is not None:
            raise ValueError("protected inputs select one bound preparation or one unbound request")
        for name, kind in (*INPUT_TYPES.items(), ("request", ProtectedFactorialPreparationRequest)):
            row = getattr(self, name)
            if row is not None:
                if type(row) is not kind:
                    raise TypeError("protected factorial input has the wrong exact record role")
                row.__post_init__()
        if (type(self.files) is not tuple
                or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or set(key for key, _ in self.files) - {"bank", *PAIRED_TYPES}
                or any(type(row) is not PreparedExperimentFile for _, row in self.files)):
            raise ValueError("protected factorial files need their exact bank and optional paired-source roles")
        for _, row in self.files:
            row.__post_init__()


def input_record_types():
    return tuple(sorted((*INPUT_TYPES.values(), ProtectedFactorialPreparationRequest), key=lambda kind: kind.SCHEMA))


def protected_factorial_allocation(specification, original):
    """Project whole units from original allocation exposure and role checks."""
    if type(specification) is not ProtectedFactorialExperimentSpecification or type(original) is not ProtectedFactorialOriginalSource:
        raise TypeError("protected factorial allocation requires its exact specification and original source")
    specification.__post_init__()
    original.__post_init__()
    programme = original.criteria.record.configuration.programme
    root = original.study.draft
    from .programme_acquisition import ScheduledProgrammeAcquisitionScope
    # Reuse the original global-root owner, including every original source
    # readiness pin and the common pre-acquisition design cutoff. A coherently
    # republished entry must not erase those original scientific premises.
    ScheduledProgrammeAcquisitionScope("acquisition." + programme.waves[0].wave_id, programme, programme.bank,
        programme.waves[0], root, original.criteria.record.configuration.qualified_parent)
    if (specification.original_study != ObjectIdentity.from_record(original.study.package_id, original.study)
            or specification.criteria != original.criteria.identity or specification.acquisitions != original.acquisitions.identity
            or specification.question != root.question
            or programme.mode != "E4_CONFIRMATION" or len(programme.group_ids) != 64 or len(programme.cases) != 576
            or root.development_unit_ids or root.evaluation_unit_ids != programme.group_ids
            or root.experiment is None or root.system is None
            or root.experiment.information_cutoffs != tuple(case.information_cutoff for case in programme.cases)
            or programme.allocation != identity(original.allocation)
            or tuple(row.wave_id for row in original.acquisitions.acquisitions) != tuple(row.wave_id for row in programme.waves)):
        raise ValueError("protected experiment changes its exact original entry, full population, allocation or chronology selection")
    require_original_criteria_design(root, original.criteria)
    statistical = original.criteria.record.configuration.specification.identity
    if len(tuple(row for row in root.design_inputs if row.object_identity == statistical
            and row.materialization_sha256 == statistical.object_fingerprint
            and row.outcome_access is OutcomeAccess.OUTCOME_BLIND and row.visibility_ceiling is VisibilityCeiling.PROSPECTIVE)) != 1:
        raise ValueError("protected original entry omits its exact original statistical specification")
    roots = {row.root.root_id: row for row in original.allocation.roots}
    coordinates = {row.coordinate_id: row for row in original.allocation.coordinates}
    selected = {case.root_id for case in programme.cases}
    selected_groups = set(programme.group_ids)
    if {key for key, row in roots.items() if row.root.independent_group_id in selected_groups} != selected:
        raise ValueError("protected confirmation thins the original whole-group allocation")
    for case in programme.cases:
        row = roots.get(case.root_id)
        if row is None:
            raise ValueError("protected confirmation adds a case outside its original allocation")
        coordinate = coordinates[row.root.coordinate_id]
        if (row.root.role.value != "CONFIRMATION" or case.role != row.root.role.value
                or case.independent_group_id != row.root.independent_group_id or case.coordinate != row.coordinate
                or case.family_id != coordinate.family_id
                or case.factor_values != (coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma,
                    coordinate.member.cross_coupling_gamma)
                or case.streams_sha256 != sha256(canonical_json_bytes(row.streams)).hexdigest()
                or case.information_cutoff.clock_id != coordinate.clock_id):
            raise ValueError("protected confirmation relabels original role, physical case, family, clock or streams")
    refs = tuple(sorted((original.identity, identity(original.allocation), programme.identity), key=lambda row: row.object_id))
    units = tuple(IndependentUnit(group, original.allocation.allocation_id,
        next(case.family_id for case in programme.cases if case.independent_group_id == group), ("fine", "primary"), False)
        for group in programme.group_ids)
    return UnitAllocation("allocation.protected-factorial." + specification.fingerprint(), refs, units,
        tuple(UnitRoleAssignment(group, "confirmation") for group in programme.group_ids))


def bind_protected_factorial_experiment_inputs(specification, records, *, record_paths=None, files=None):
    if not isinstance(records, Mapping) or set(records) - {*INPUT_TYPES, "request"}:
        raise ValueError("protected factorial selection requires only original and preparation records")
    if record_paths is not None and (not isinstance(record_paths, Mapping) or set(record_paths) - set(records)):
        raise ValueError("protected factorial record locations add an unselected role")
    selected_files = {} if files is None else files
    if not isinstance(selected_files, Mapping):
        raise TypeError("protected factorial source files require their typed role mapping")
    inputs = ProtectedFactorialExperimentInputs(**records, files=tuple(sorted(selected_files.items())))
    allocation = None if inputs.original is None else protected_factorial_allocation(specification, inputs.original)
    return PreparedExperimentInputs({} if allocation is None else {"confirmation": allocation}, inputs)


def _source_projection(draft, selection, versions, *, retained_history_ids=()):
    qualifications = {row.source_id: row for row in selection.qualifications}
    configs = {row.source_id: row for row in selection.source_configs}
    retained = set(retained_history_ids)
    by_input = {row.input_id: row for row in draft.external_inputs}
    if (type(retained_history_ids) is not tuple or len(retained) != len(retained_history_ids)
            or not retained <= set(by_input)
            or any(by_input[key].scientific_role != "HISTORY" for key in retained)):
        raise ValueError("retained source exclusions require exact declared HISTORY input IDs")
    sources = tuple(row for row in draft.external_inputs if row.input_id not in retained)
    if (len(qualifications) != len(selection.qualifications) or len(configs) != len(selection.source_configs)
            or set(qualifications) != {row.input_id for row in sources} or set(configs) != set(qualifications)):
        raise ValueError("protected source qualification/configuration roster differs from selected physical source inputs")
    materials = []
    for external in sources:
        q, config = qualifications[external.input_id], configs[external.input_id]
        expected_role = (SourceMaterializationRole.RETAINED_HISTORY if external.scientific_role == "HISTORY"
            else SourceMaterializationRole.CALIBRATION if external.scientific_role == "QUALIFICATION"
            else SourceMaterializationRole.OBSERVATION_STREAM)
        if (q.materialization.object_id != external.logical_artifact_id or q.materialization.object_schema != external.payload_schema
                or q.materialization.object_version != versions[external.logical_artifact_id]
                or q.materialization.object_fingerprint != external.expected_content_sha256
                or q.content_sha256 != external.expected_content_sha256 or q.evidence_world_id != draft.prospective_draft.system.world.world_id
                or q.outcome_access is not external.outcome_access or q.visibility_ceiling is not external.visibility_ceiling
                or config.role is not expected_role
                or (config.content_sha256, config.payload_schema, config.media_type, config.expected_size_bytes)
                    != (external.expected_content_sha256, external.payload_schema, external.media_type, external.maximum_size_bytes)
                or config.outcome_access is not external.outcome_access or config.visibility_ceiling is not external.visibility_ceiling):
            raise ValueError("protected source projection substitutes exact qualified bytes, world, role or access")
        materials.append(SourceMaterializationRef(external.input_id, config.role, q.evidence_world_id, q.materialization,
            q.content_sha256, config.fingerprint(), q.observation_operator, q.numerical_view_ids,
            ObjectIdentity.from_record(q.receipt_id, q), SourceAccessDisposition.VERIFIED_ACCESS))
    # The complete design may retain historical operations. Entry binds the
    # same selected capabilities that the recursive compiler will issue.
    selected = set(draft.selected_operation_ids)
    root = replace(draft.prospective_draft, source_materializations=tuple(sorted(materials, key=lambda row: row.source_id)),
        dag_template_key="recursive." + draft.draft_id,
        capability_selections=tuple(sorted({row.selection for row in draft.operations if row.node_id in selected},
            key=lambda row: row.selection_id)))
    return replace(draft, prospective_draft=root)


def derive_protected_factorial_design_inputs(specification, original, selection):
    """Pure graph projection; actual qualifiers and envelope must be supplied."""
    allocation = protected_factorial_allocation(specification, original)
    if type(selection) not in (ProtectedFactorialPreparationSelection, ProtectedFactorialPreparationRequest):
        raise TypeError("protected factorial projection requires its exact preparation selection or request")
    selection.__post_init__()
    programme = original.criteria.record.configuration.programme
    if (selection.bank.artifact_id, selection.bank.payload_schema, selection.bank.sha256) != (
            programme.bank.object_id, programme.bank.object_schema, programme.bank.object_fingerprint):
        raise ValueError("protected preparation substitutes its original bank artifact")
    paired = {kind.SCHEMA: kind for kind in PAIRED_TYPES.values()}
    identities = tuple(ObjectIdentity(row.artifact_id, row.payload_schema, paired[row.payload_schema].VERSION, row.sha256)
        for row in selection.paired_inputs if row.payload_schema in paired)
    if identities != specification.paired_inputs or len(identities) != len(selection.paired_inputs):
        raise ValueError("protected preparation changes the exact paired sources selected by the scientific specification")
    by_schema = {row.payload_schema: row for row in selection.paired_inputs}
    lowered = lower_factorial_confirmation(root=original.study.draft, criteria=original.criteria,
        acquisitions=original.acquisitions.acquisitions, bank_artifact=selection.bank, operational_budget=selection.operational_budget,
        reduction=by_schema.get(ScheduledProgrammeReduction.SCHEMA), data=by_schema.get(ScheduledRevisionDataBank.SCHEMA))
    versions = {key: row.VERSION for key, row in lowered.input_records}
    versions[selection.bank.artifact_id] = programme.bank.object_version
    versions.update((row.artifact_id, paired[row.payload_schema].VERSION) for row in selection.paired_inputs)
    draft = _source_projection(lowered.draft, selection, versions)
    entry = replace(original.study.entry_package, checklist=replace(original.study.entry_package.checklist,
        draft=ObjectIdentity.from_record(draft.prospective_draft.draft_id, draft.prospective_draft)))
    validate_experiment_entry(draft.prospective_draft, entry, for_issue=False)
    resources = selection.resource_selection if type(selection) is ProtectedFactorialPreparationRequest else selection.resources
    task_ids = {assess_node_id(original.criteria.record.configuration.specification),
        input_seal_node_id(original.criteria.record.configuration.specification)}
    if resources is not None and ({row.task_id for row in resources.task_cells} != task_ids
            or len(resources.task_cells) != 2
            or any(row.native_simulator_launch or row.physical_execution_cost or row.retry_token_cost
                or row.physical_independent_unit_id is not None or row.preparation_unit_id is not None
                for row in resources.task_cells)):
        raise ValueError("protected resource envelope changes the exact two nonnative metadata/assessment tasks")
    operands = tuple(sorted((RecursiveProspectiveOperand(row.logical_artifact_id, row.expected_content_sha256,
        row.maximum_size_bytes, row.payload_schema, row.media_type, row.outcome_access, row.visibility_ceiling)
        for row in draft.external_inputs), key=lambda row: row.logical_artifact_id))
    design = RecursiveProspectiveDesignInputs(specification.specification_id + ".prospective", draft, entry,
        selection.formal_methods, selection.formal_source_inventories, selection.qualifications,
        draft.prospective_draft.design_inputs, operands, ())
    return allocation, draft, lowered.input_records, design


def derive_protected_factorial_experiment(specification, original, selection):
    if type(selection) is not ProtectedFactorialPreparationSelection:
        raise TypeError("protected bound projection requires its exact preparation selection")
    allocation, draft, records, design = derive_protected_factorial_design_inputs(specification, original, selection)
    return allocation, draft, records, None if selection.resources is None else design.bind_resources(selection.resources)


def prepare_protected_factorial_experiment(specification, *, scientific_inputs, execution, protocol_bytes=None, method_inputs=None):
    if type(specification) is not ProtectedFactorialExperimentSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("protected factorial preparation needs its exact specification and separate execution selection")
    specification.__post_init__()
    execution.__post_init__()
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("protected factorial preparation needs its immutable scientific allocation mapping")
    inputs = ProtectedFactorialExperimentInputs() if method_inputs is None else method_inputs
    if type(inputs) is not ProtectedFactorialExperimentInputs:
        raise TypeError("protected factorial preparation needs its exact typed original inputs")
    inputs.__post_init__()
    dependencies = []

    def dependency(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.protected-factorial." + code, kind, detail, key))

    if inputs.original is None:
        dependency("original.missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual exact original record.", "original")
    selection = inputs.preparation if inputs.preparation is not None else inputs.request
    if selection is None:
        dependency("preparation.missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual exact preparation record or unbound request.", "preparation")
    allocation = draft = prospective = None
    records = files = ()
    if inputs.original is not None and selection is not None:
        try:
            if type(selection) is ProtectedFactorialPreparationRequest:
                allocation, draft, logical_records, _ = derive_protected_factorial_design_inputs(specification, inputs.original, selection)
            else:
                allocation, draft, logical_records, prospective = derive_protected_factorial_experiment(specification, inputs.original, selection)
            if set(scientific_inputs) != {"confirmation"} or scientific_inputs["confirmation"] != allocation:
                raise ValueError("protected factorial selection changes the original complete whole-group allocation")
            available = dict(inputs.files)
            expected_files = {"bank": selection.bank}
            expected_files.update((name, row) for name, kind in PAIRED_TYPES.items()
                for row in selection.paired_inputs if row.payload_schema == kind.SCHEMA)
            if set(available) != set(expected_files) or any(available[key].identity != value
                    or available[key].maximum_bytes != value.size_bytes
                    or available[key].record_version != (inputs.original.criteria.record.configuration.bank.object_version
                        if key == "bank" else PAIRED_TYPES[key].VERSION) for key, value in expected_files.items()):
                raise ValueError("protected factorial files omit or substitute exact original bank/paired source identities")
            external = {row.logical_artifact_id: row.input_id for row in draft.external_inputs}
            records = tuple(sorted((external[key], row) for key, row in logical_records))
            files = tuple(sorted((external[row.identity.artifact_id], row) for _, row in inputs.files))
        except (ValueError, PermissionError) as error:
            dependency("scientific-selection", DependencyKind.SCIENTIFIC_EVIDENCE, str(error))
            draft = prospective = None
        if type(selection) is ProtectedFactorialPreparationSelection and selection.resources is None:
            dependency("resources.missing", DependencyKind.ENVIRONMENT, "Supply the actual mechanically bound two-task resource envelope.", "preparation")
    elif scientific_inputs:
        dependency("allocation.unresolved", DependencyKind.EXTERNAL_INPUT, "Resolve the actual original confirmation source before selecting its allocation.")
    if protocol_bytes is not None:
        dependency("protocol.override", DependencyKind.EXTERNAL_INPUT, "The exact original criteria own all statistical rules; replacement protocol bytes are unselected.")
    for name, field, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("output-root", "output_root", DependencyKind.STORAGE), ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT)):
        if getattr(execution, field) is None:
            dependency(name + ".missing", kind, "Select the actual " + name + " explicitly.")
    if execution.source_snapshot is not None and (execution.source_snapshot.object_id != "recursive-member.implementation"
            or (execution.source_snapshot.object_schema, execution.source_snapshot.object_version) != (
                ImplementationSourceClosure.SCHEMA, ImplementationSourceClosure.VERSION)):
        dependency("source-snapshot.role", DependencyKind.ENVIRONMENT, "Protected preparation requires the actual ImplementationSourceClosure in its original source-snapshot role.")
    dependency("owning-api-composition", DependencyKind.SOFTWARE,
        "Compose the existing Matrix API supplier/loader: authenticate original entry, original criteria-before-acquisition chronology and live qualified calibration authority at handoff and worker entry.")
    dependency("resource-projection", DependencyKind.SOFTWARE,
        "The API author must mechanically bind the actual candidate/source closure to the resource envelope; researcher-authored extension identities are insufficient.")
    # The original assessor reports this outcome limit even for an otherwise
    # admissible adverse assessment. It does not replace any entry requirement.
    limitations = (ExperimentDependency("matrix.protected-factorial.sampling-warrant", DependencyKind.SCIENTIFIC_EVIDENCE,
        "UNEVALUABLE: SAMPLING_ASSUMPTION_NOT_AUTHENTICATED. Conditional numerical results do not establish the required sampling warrant."),)
    roles = (("acquisition-waves", 16), ("comparison-family-slots", 12), ("independent-groups", 64), ("paired-cases", 576))
    census = ExperimentCensus(roles, tuple((key, count if allocation is not None else 0) for key, count in roles),
        (("confirmation-assessment", 1), ("outcome-blind-input-design-seal", 1)),
        (("confirmation-readout", 1), ("input-design-seal", 1)), 0)
    design_records = tuple(sorted((row.source_id if name == "original" else row.request_id if name == "request" else row.selection_id, row)
        for name in (*INPUT_TYPES, "request") if (row := getattr(inputs, name)) is not None))
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=draft, input_records=records, execution=execution, specification_record=specification,
        design_records=design_records, input_files=files, prospective_spec=prospective,
        source_configs=() if prospective is None else selection.source_configs,
        assessment_limitations=limitations)


def validate_protected_factorial_experiment_instance(*, specification, allocation, draft, source_records):
    if type(source_records) is not tuple or tuple(key for key, _ in source_records) != tuple(sorted({key for key, _ in source_records})):
        raise ValueError("protected instance changes its exact original source-record census")
    selected = {}
    for key, record in source_records:
        matches = tuple(name for name, kind in (*INPUT_TYPES.items(), ("request", ProtectedFactorialPreparationRequest)) if type(record) is kind)
        if len(matches) != 1:
            raise ValueError("protected instance adds an unselected original record type")
        role, = matches
        if role in selected or key != (record.source_id if role == "original" else record.request_id if role == "request" else record.selection_id):
            raise ValueError("protected instance aliases or duplicates its original source roles")
        selected[role] = record
    if not set(INPUT_TYPES) <= set(selected) or set(selected) - {*INPUT_TYPES, "request"}:
        raise ValueError("protected instance omits its actual original sources or preparation selection")
    if "request" in selected:
        validate_protected_factorial_request_binding(selected["request"], selected["preparation"])
    expected_allocation, expected_draft, _, prospective = derive_protected_factorial_experiment(
        specification, selected["original"], selected["preparation"])
    if prospective is None or allocation != expected_allocation or draft != expected_draft:
        raise ValueError("protected instance differs from its exact original sources, whole allocation or derived graph")


def validate_protected_experiment_handoff_selection(handoff, *, specification, allocation, source_records):
    """Pure selection join only; the API owner must still replay live authority."""
    validate_protected_factorial_experiment_instance(specification=specification, allocation=allocation,
        draft=handoff.compilation.draft, source_records=source_records)
    selected = {type(row): row for _, row in source_records}
    original, selection = selected[ProtectedFactorialOriginalSource], selected[ProtectedFactorialPreparationSelection]
    _, draft, records, prospective = derive_protected_factorial_experiment(specification, original, selection)
    if (handoff.authoring.base.entry_package != prospective.entry_package
            or handoff.authoring.base.draft != draft.prospective_draft
            or handoff.authoring.base.package_id != prospective.spec_id + ".standard"
            or handoff.authoring.package_id != prospective.spec_id + ".executable"
            or handoff.resources != prospective.resources
            or handoff.compilation.candidate_draft != draft.prospective_draft
            or handoff.compilation.candidate_context.qualifications != prospective.qualifications
            or handoff.compilation.candidate_context.known_design_inputs != prospective.known_design_inputs
            or handoff.context.formal_methods != prospective.formal_methods
            or handoff.context.formal_source_inventories != prospective.formal_source_inventories):
        raise ValueError("protected handoff substitutes its actual prospective source/resource/entry projections")
    return original, selection, records
