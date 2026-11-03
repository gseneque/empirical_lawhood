# SPDX-License-Identifier: MPL-2.0
"""Public declared selected-E4 DEV fitting and joint freeze preparation."""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExecutionSelection, ExperimentCensus,
    ExperimentDependency, ExperimentPreparation, ExperimentProtocolDeclaration, ExperimentInputConfigurationDeclaration, PreparedExperimentInputs)

from . import selected_e3_e4_records as r, selected_e4_programme as p, selected_e4_methods as science
from . import selected_e4_method_bindings as owner

PROTOCOL_ID = "matrix.selected-e4.declared-revision"
INPUT_TYPES = {"campaign": CampaignSpec, "programme": r.SelectedE3E4DevelopmentProgramme,
    "bank": r.SelectedE3E4DevelopmentBank, "acquisition": owner.SelectedE4DevelopmentAcquisition,
    "reduction": r.SelectedE3E4DevelopmentReduction, "data": p.SelectedE4ObservedData,
    "resources": owner.SelectedE4MethodResources}
ID_FIELDS = {"campaign": "campaign_id", "programme": "programme_id", "bank": "bank_id",
    "acquisition": "record_id", "reduction": "record_id", "data": "record_id", "resources": "record_id"}


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionInputs:
    campaign: CampaignSpec | None = None
    programme: r.SelectedE3E4DevelopmentProgramme | None = None
    bank: r.SelectedE3E4DevelopmentBank | None = None
    acquisition: owner.SelectedE4DevelopmentAcquisition | None = None
    reduction: r.SelectedE3E4DevelopmentReduction | None = None
    data: p.SelectedE4ObservedData | None = None
    resources: owner.SelectedE4MethodResources | None = None

    def __post_init__(self):
        for name, kind in INPUT_TYPES.items():
            value = getattr(self, name)
            if value is not None:
                if type(value) is not kind:
                    raise TypeError("selected E4 declaration has the wrong closed input role " + name)
                value.__post_init__()


def bind_inputs(specification, records):
    if (type(specification) is not science.SelectedE4RevisionExperimentSpecification or not isinstance(records, Mapping)
            or set(records) - set(INPUT_TYPES)):
        raise TypeError("selected E4 authoring accepts its explicit scientific/operational input roles only")
    specification.__post_init__()
    inputs = SelectedE4RevisionInputs(**records)
    return PreparedExperimentInputs({} if inputs.programme is None else {"development": science.selection_allocation(inputs.programme)}, inputs)


def development_root(programme, specification, bank, reduction, data, acquisition, *, study_id):
    question = "Does the explicitly declared selected E4 DEV trigger support a frozen revision and same-information baseline?"
    world = "world.matrix-selected-e4.declared-revision"
    claim = ClaimSpec("claim." + study_id, world, programme.programme_id, question,
        "All assigned whole groups, complete matched factorial cases and both paired target views.",
        "unit.matrix-selected-e4.whole-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Original acquisition receipts and source joins are required; DEV completion grants no issue, qualification or outcome access.",
        ("assumption.selected-e4.original-native-development",), numerical_view_ids=("fine", "primary"))
    operands = tuple(sorted((programme.identity, specification.identity, bank.identity, r.pin(reduction), data.identity, acquisition.identity),
        key=lambda value: value.object_id))
    return DevelopmentStudySpec(study_id, question, programme.identity, world, WorldKind.NUMERICAL_SIMULATOR,
        programme.group_ids, ("fine", "primary"), (claim,), operands)


def lower_development(specification, inputs):
    method_specification = science.derive_revision_specification(specification, inputs.programme)
    science.validate_observed_data(inputs.programme, inputs.bank, inputs.reduction, inputs.data,
        method_specification.target, allow_absent=False)
    tasks, links, records, external = owner.method_rows(inputs.programme,
        operands={"bank": inputs.bank, "acquisition": inputs.acquisition, "reduction": inputs.reduction,
            "data": inputs.data, "specification": method_specification},
        connections={}, resources=inputs.resources, entry_node_id=None)
    root = development_root(inputs.programme, method_specification, inputs.bank, inputs.reduction, inputs.data, inputs.acquisition,
        study_id="study.selected-e4." + specification.fingerprint())
    campaign = replace(inputs.campaign, objective=root.question, system_ids=(root.system.object_id,),
        world_ids=(root.world_id,), target_claim_ids=tuple(row.claim_id for row in root.claims))
    return RecursiveStudyDraft("draft.selected-e4." + specification.fingerprint(), root.question, campaign, (), (), (),
        tuple(sorted(tasks, key=lambda row: row.node_id)), external, tuple(sorted(links, key=lambda row: row.edge_id)),
        tuple(sorted(row.node_id for row in tasks)), development_study=root), records


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if type(specification) is not science.SelectedE4RevisionExperimentSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("selected E4 fitting requires separate exact scientific and execution declarations")
    specification.__post_init__()
    execution.__post_init__()
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("selected E4 fitting requires its complete typed allocation mapping")
    inputs = SelectedE4RevisionInputs() if method_inputs is None else method_inputs
    if type(inputs) is not SelectedE4RevisionInputs:
        raise TypeError("selected E4 fitting requires its actual bound method input roles")
    inputs.__post_init__()
    dependencies = []
    def missing(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.selected-e4.revision." + code, kind, detail, key))
    for name in INPUT_TYPES:
        if getattr(inputs, name) is None:
            missing(name, DependencyKind.ENVIRONMENT if name == "resources" else DependencyKind.EXTERNAL_INPUT,
                "Select the actual original " + name + " input; scientific and operational selections have no fallback.", name)
    allocation = None if inputs.programme is None else science.selection_allocation(inputs.programme)
    if (set(scientific_inputs) != (set() if allocation is None else {"development"})
            or allocation is not None and scientific_inputs.get("development") != allocation):
        missing("allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Preserve the exact complete independent DEV group allocation.")
    for name, attribute, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source", "source_snapshot", DependencyKind.ENVIRONMENT), ("output", "output_root", DependencyKind.STORAGE),
            ("workers", "workers", DependencyKind.ENVIRONMENT)):
        if getattr(execution, attribute) is None:
            missing(name, kind, "Select explicit operational " + name + " before authoring.")
    if protocol_bytes is not None:
        missing("protocol", DependencyKind.SCIENTIFIC_EVIDENCE, "The editable declaration owns every supported scientific choice; no second protocol override is selected.")
    draft, records = (None, ()) if dependencies else lower_development(specification, inputs)
    groups = len(specification.folds)
    census = ExperimentCensus((("development-groups", groups),),
        (("development-groups", 0 if allocation is None else len(allocation.units)),),
        () if draft is None else tuple((name, 1) for name in owner.operations_for_programme(inputs.programme)),
        () if draft is None else (("canonical-products", sum(len(owner.output_types(operation))
            for operation in owner.operations_for_programme(inputs.programme))),), 0)
    scientific = tuple(name for name in INPUT_TYPES if name != "resources")
    designs = () if any(getattr(inputs, name) is None for name in scientific) else tuple(sorted(
        (getattr(getattr(inputs, name), ID_FIELDS[name]), getattr(inputs, name)) for name in scientific))
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation, draft, records, execution, specification, designs)


def validate_instance(*, specification, allocation, draft, source_records):
    by_type = {}
    for key, record in source_records:
        names = tuple(name for name, kind in INPUT_TYPES.items() if name != "resources" and type(record) is kind)
        if len(names) != 1 or names[0] in by_type or key != getattr(record, ID_FIELDS[names[0]]):
            raise ValueError("selected E4 instance duplicates or substitutes an original scientific companion")
        by_type[names[0]] = record
    if set(by_type) != set(INPUT_TYPES) - {"resources"}:
        raise ValueError("selected E4 instance omits actual native DEV acquisition/evidence inputs")
    budgets = []
    declarations = {row.capability_key: row for row in owner.operation_declarations()}
    for task in draft.operations:
        declaration = declarations.get(task.selection.capability_key)
        if declaration is None:
            raise ValueError("selected E4 instance adds an undeclared method")
        from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
        config = decode_recursive_config_input(task, declaration.registration()).record
        if config.operational_budget != task.resource_budget:
            raise ValueError("selected E4 cold instance changes its exact frozen operational reservation")
        budgets.append((config.operation, task.resource_budget))
    resources = owner.SelectedE4MethodResources("resources.cold-replay", tuple(sorted(budgets)))
    bound = bind_inputs(specification, {**by_type, "resources": resources})
    expected, _ = lower_development(specification, bound.method_inputs)
    if allocation != bound.scientific_inputs["development"] or draft != expected:
        raise ValueError("selected E4 instance changes original science, native evidence or actual fit→freeze graph")


def protocol_declaration():
    return ExperimentProtocolDeclaration(PROTOCOL_ID, science.SelectedE4RevisionExperimentSpecification, prepare,
        "experiment.matrix-selected-e4-declared-revision", input_record_types=tuple(INPUT_TYPES.values()),
        bind_inputs=bind_inputs, validate_instance=validate_instance, requires_development_runtime_binding=True,
        configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-selected-e4-revision-resources",
            owner.SelectedE4MethodResources, maximum_config_bytes=128*1024**2),))
