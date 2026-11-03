# SPDX-License-Identifier: MPL-2.0
"""Public selected E3 -> original scheduled E4 DEV32x9 preparation."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixE4StructuralChoices
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs, ExperimentProtocolDeclaration,
    ExperimentInputConfigurationDeclaration)

from . import selected_e3_e4_bindings as method, selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryReadoutSelection,
)

from .full_factor_followup_records import ScheduledFullFactorResources

PROTOCOL_ID = "matrix.selected-e3-e4.development"


@dataclass(frozen=True, slots=True)
class SelectedE3E4ExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/development-experiment"
    VERSION: ClassVar[str] = "3.0.0"
    specification_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    evidence: ObjectIdentity
    campaign: ObjectIdentity
    structure: MatrixE4StructuralChoices
    structural_resources: ScheduledFullFactorResources

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for value, kind in ((self.programme, r.SelectedE3E4DevelopmentProgramme), (self.bank, r.SelectedE3E4DevelopmentBank),
                (self.evidence, r.SelectedE3E4Evidence), (self.campaign, CampaignSpec)):
            r.exact_pin(value, kind)
        for value, kind in ((self.structure, MatrixE4StructuralChoices),
                (self.structural_resources, ScheduledFullFactorResources)):
            if type(value) is not kind:
                raise TypeError("ordinary E4 DEV requires explicit structural science and runtime reservations")
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class SelectedE3E4OperationalSelection(CanonicalRecord):
    """Explicit phase reservations; no resource estimate or scientific authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/operational-selection"
    record_id: str
    phase_budgets: tuple[tuple[str, ResourceBudget], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.phase_budgets) is not tuple
                or tuple(name for name, _ in self.phase_budgets) != tuple(sorted(method.PHASES))
                or any(type(value) is not ResourceBudget or not method.BUDGET.contains(value)
                    for _, value in self.phase_budgets)):
            raise ValueError("selected E4 resources require the complete exact phase census within registered ceilings")
        for _, value in self.phase_budgets:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def task_budgets(self, programme, bank, *, evidence):
        self.__post_init__()
        phases = dict(self.phase_budgets)
        tasks = method.operational_tasks(programme, bank, evidence=evidence)
        return {task: phases[phase] for task, phase in tasks}


@dataclass(frozen=True, slots=True)
class SelectedE3E4Inputs:
    programme: r.SelectedE3E4DevelopmentProgramme | None = None
    bank: r.SelectedE3E4DevelopmentBank | None = None
    evidence: r.SelectedE3E4Evidence | None = None
    campaign: CampaignSpec | None = None
    files: tuple[tuple[str, PreparedExperimentFile], ...] = ()
    operational_budgets: tuple[tuple[str, ResourceBudget], ...] = ()
    resources: SelectedE3E4OperationalSelection | None = None
    secondary_readout: MatrixE4SecondaryReadoutSelection | None = None

    def __post_init__(self):
        for value, kind in ((self.programme, r.SelectedE3E4DevelopmentProgramme), (self.bank, r.SelectedE3E4DevelopmentBank),
                (self.evidence, r.SelectedE3E4Evidence), (self.campaign, CampaignSpec)):
            if value is not None and type(value) is not kind:
                raise TypeError("selected E4 preparation requires its exact actual scientific input owners")
        if (type(self.files) is not tuple or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or any(type(value) is not PreparedExperimentFile for _, value in self.files)):
            raise TypeError("selected E4 preparation requires separate immutable array file handles")
        if (type(self.operational_budgets) is not tuple
                or tuple(key for key, _ in self.operational_budgets) != tuple(sorted({key for key, _ in self.operational_budgets}))
                or any(type(key) is not str or type(value) is not ResourceBudget for key, value in self.operational_budgets)):
            raise TypeError("selected E4 requires separate sorted unique operational task budgets")
        if self.secondary_readout is not None:
            if type(self.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
                raise TypeError("E4 preparation requires its actual frozen target publication selection")
            self.secondary_readout.__post_init__()
        if self.resources is not None:
            if type(self.resources) is not SelectedE3E4OperationalSelection:
                raise TypeError("selected E4 resources require their exact declared operational selection")
            self.resources.__post_init__()
        for key, value in self.operational_budgets:
            validate_stable_id(key)
            value.__post_init__()


def select_operational_budgets(inputs, operational_budgets):
    """Bind operator reservations before preparation and authoring.

    After load_experiment_inputs(), derive task IDs and phases through
    method.operational_tasks(inputs.programme, inputs.bank,
    evidence=inputs.evidence). Map the operator's measured phase reservations
    onto that projection and pass the returned inputs as method_inputs to
    prepare_experiment(). No task roster or reservation size is invented here.

    This genuine DEV lane has no issued NonTime resource specification or
    sealed aggregate/max-parallel contract. Ordinary DEV admission and its
    explicit assurance limitations remain owned by run_recursive_wave().
    """
    if type(inputs) is not SelectedE3E4Inputs:
        raise TypeError("selected E4 operational selection requires its exact bound inputs")
    tasks = method.operational_tasks(inputs.programme, inputs.bank, evidence=inputs.evidence)
    selected = method._selected_operational_budgets(tasks, operational_budgets)
    if inputs.resources is not None and selected != inputs.resources.task_budgets(inputs.programme, inputs.bank, evidence=inputs.evidence):
        raise ValueError("selected E4 task reservations differ from their explicit phase selection")
    return replace(inputs, operational_budgets=tuple(sorted(selected.items())))


def _scientific_input_types():
    return r.SelectedE3E4DevelopmentProgramme, r.SelectedE3E4DevelopmentBank, r.SelectedE3E4Evidence, CampaignSpec


def input_record_types():
    return (*_scientific_input_types(), SelectedE3E4OperationalSelection, MatrixE4SecondaryReadoutSelection)


def allocation(programme):
    return UnitAllocation("allocation." + programme.programme_id, (programme.identity,),
        tuple(IndependentUnit(group, programme.programme_id, next(case.family_id for case in programme.cases if case.independent_group_id == group),
            ("fine", "primary"), True) for group in programme.group_ids),
        tuple(UnitRoleAssignment(group, "development") for group in programme.group_ids))


def bind_inputs(specification, records, *, files=None):
    files = {} if files is None else files
    if (type(specification) is not SelectedE3E4ExperimentSpecification or not isinstance(records, Mapping)
            or set(records) - {"programme", "bank", "evidence", "campaign", "resources", "secondary_readout"} or not isinstance(files, Mapping)):
        raise TypeError("selected E4 binding changes exact original scientific/operational input roles")
    inputs = SelectedE3E4Inputs(records.get("programme"), records.get("bank"), records.get("evidence"),
        records.get("campaign"), tuple(sorted(files.items())), resources=records.get("resources"), secondary_readout=records.get("secondary_readout"))
    if inputs.resources is not None and all(getattr(inputs, key) is not None for key in ("programme", "bank", "evidence")):
        inputs = select_operational_budgets(inputs,
            inputs.resources.task_budgets(inputs.programme, inputs.bank, evidence=inputs.evidence))
    return PreparedExperimentInputs({} if inputs.programme is None else {"programme": allocation(inputs.programme)}, inputs)


def _lower(specification, inputs):
    return method.lower_selected_e3_e4_development(inputs.programme, inputs.bank, evidence=inputs.evidence, campaign=inputs.campaign,
        draft_id="draft.selected-e4." + specification.fingerprint(), operational_budgets=dict(inputs.operational_budgets),
        secondary_target=specification.structure.secondary_target, secondary_readout=inputs.secondary_readout)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if type(specification) is not SelectedE3E4ExperimentSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("selected E4 preparation requires exact immutable science and operational selections")
    specification.__post_init__()
    execution.__post_init__()
    inputs = SelectedE3E4Inputs() if method_inputs is None else method_inputs
    if type(inputs) is not SelectedE3E4Inputs or not isinstance(scientific_inputs, Mapping):
        raise TypeError("selected E4 preparation requires its exact bound input record")
    inputs.__post_init__()
    if inputs.resources is not None and all(getattr(inputs, key) is not None for key in ("programme", "bank", "evidence")):
        inputs = select_operational_budgets(inputs, dict(inputs.operational_budgets))
    dependencies = []
    def missing(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.selected-e4." + code, kind, detail, key))
    for key in ("programme", "bank", "evidence", "campaign"):
        value = getattr(inputs, key)
        if value is None:
            missing(key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual original " + key + " record.", key)
            continue
        value.__post_init__()
        identifier = getattr(value, {"programme": "programme_id", "bank": "bank_id", "evidence": "record_id", "campaign": "campaign_id"}[key])
        if ObjectIdentity.from_record(identifier, value) != getattr(specification, key):
            missing(key + ".identity", DependencyKind.SCIENTIFIC_EVIDENCE, "The original " + key + " differs from its frozen identity.", key)
    if inputs.secondary_readout is None:
        missing("secondary-readout.missing", DependencyKind.EXTERNAL_INPUT,
            "Publish and select the frozen E4 secondary target before authoring and future acquisition.", "secondary_readout")
    else:
        inputs.secondary_readout.validate_target(specification.structure.secondary_target)
    selected_allocation = None if inputs.programme is None else allocation(inputs.programme)
    if (set(scientific_inputs) != (set() if selected_allocation is None else {"programme"})
            or selected_allocation is not None and scientific_inputs.get("programme") != selected_allocation):
        missing("allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain all32 complete nine-case independent groups.", "programme")
    if all(getattr(inputs, key) is not None for key in ("programme", "bank", "evidence")):
        r.validate_evidence(inputs.evidence, inputs.programme, inputs.bank)
    if inputs.programme is not None and inputs.bank is not None:
        from .selected_e4_structure import structural_measurement
        structural_measurement(programme=inputs.programme, bank=inputs.bank, choices=specification.structure)
    if not inputs.operational_budgets:
        missing("operational-budgets", DependencyKind.ENVIRONMENT,
            "Select the complete operational task budget mapping before authoring; native memory adequacy requires actual workload evidence.")
    lowered = None if dependencies else _lower(specification, inputs)
    artifacts = {} if lowered is None else dict(lowered.input_artifacts)
    files = dict(inputs.files)
    for name, artifact in artifacts.items():
        if name not in files:
            missing("file." + name + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply exact original fixed assay template bytes.", name)
        elif files[name].identity != artifact or files[name].record_version != "1.0.0" or files[name].maximum_bytes != artifact.size_bytes:
            missing("file." + name + ".identity", DependencyKind.EXTERNAL_INPUT, "The original file identity/revision/byte bound differs.", name)
    if set(files) - set(artifacts):
        missing("file.unselected", DependencyKind.EXTERNAL_INPUT, "Selected files add undeclared scientific roles.")
    for name, attribute, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, attribute) is None:
            missing(name, kind, "Select actual " + name + " before authoring.")
    if protocol_bytes is not None:
        missing("protocol", DependencyKind.SCIENTIFIC_EVIDENCE, "Frozen original physics, selected account and complete scope cannot be overridden.")
    executable = lowered is not None and not dependencies
    assigned = () if inputs.programme is None else (("groups", inputs.programme.design.group_count),
        ("sources", inputs.programme.design.group_count * inputs.programme.design.cases_per_group))
    resolved = () if inputs.programme is None else (("groups", len(inputs.programme.group_ids)), ("sources", len(inputs.programme.cases)))
    operations, outputs, native_count = Counter(), Counter(), 0
    if lowered is not None:
        declarations = {value.capability_key: value for value in method.operation_declarations()}
        from empirical_lawhood.runtime.artifacts import ArtifactProfile
        for operation in lowered.draft.operations:
            declaration = declarations[operation.selection.capability_key]
            operations[operation.selection.capability_key.rsplit(".", 1)[-1]] += 1
            native_count += int(declaration.execution_properties.native_effect)
            for output in declaration.outputs:
                outputs["array-products" if output.profile is ArtifactProfile.MATRIX_ARRAY_NPZ else "canonical-products"] += 1
    if inputs.programme is not None:
        from .selected_e4_structure import structural_stage_census
        future_operations, future_outputs = structural_stage_census(inputs.programme)
        operations.update(dict(future_operations))
        outputs.update(dict(future_outputs))
    census = ExperimentCensus(assigned, resolved, tuple(sorted(operations.items())), tuple(sorted(outputs.items())), native_count)
    designs = tuple(sorted(((inputs.programme.programme_id, inputs.programme), (inputs.bank.bank_id, inputs.bank),
        (inputs.evidence.record_id, inputs.evidence), (inputs.campaign.campaign_id, inputs.campaign),
        (inputs.secondary_readout.record_id, inputs.secondary_readout)))) if lowered is not None else ()
    limitations = (ExperimentDependency("matrix.selected-e4.cal-conf-nomination", DependencyKind.SCIENTIFIC_EVIDENCE,
        "Selected revision fitting/freezing, distinct64 CAL and64 CONF and downstream nomination remain separate required phases; point arithmetic grants no transport applicability."),)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda value: value.code)),
        selected_allocation, lowered.draft if executable else None, lowered.input_records if executable else (), execution,
        specification, designs, inputs.files if executable else (), assessment_limitations=limitations,
        authoring_source_records=tuple((key, record) for key, record in (
            ('bank', inputs.bank), ('campaign', inputs.campaign), ('evidence', inputs.evidence),
            ('programme', inputs.programme), ('resources', inputs.resources), ('secondary_readout', inputs.secondary_readout)) if record is not None))


def validate_instance(*, specification, allocation, draft, source_records):
    if type(specification) is not SelectedE3E4ExperimentSpecification:
        raise TypeError("selected E4 instance changes its immutable specification owner")
    specification.__post_init__()
    records = dict(source_records)
    kinds = _scientific_input_types()
    if len(records) != 5 or {type(value) for value in records.values()} != {*kinds, MatrixE4SecondaryReadoutSelection}:
        raise ValueError("selected E4 instance changes complete companion record owners")
    programme, bank, evidence, campaign = (next(value for value in records.values() if type(value) is kind) for kind in kinds)
    secondary_readout, = (value for value in records.values() if type(value) is MatrixE4SecondaryReadoutSelection)
    secondary_readout.validate_target(specification.structure.secondary_target)
    from .selected_e4_structure import structural_measurement
    structural_measurement(programme=programme, bank=bank, choices=specification.structure)
    inputs = SelectedE3E4Inputs(programme, bank, evidence, campaign,
        operational_budgets=tuple(sorted((value.node_id, value.resource_budget) for value in draft.operations)), secondary_readout=secondary_readout)
    expected = bind_inputs(specification, {"programme": programme, "bank": bank, "evidence": evidence, "campaign": campaign, "secondary_readout": secondary_readout})
    if (set(records) != {programme.programme_id, bank.bank_id, evidence.record_id, campaign.campaign_id, secondary_readout.record_id}
            or programme.identity != specification.programme or bank.identity != specification.bank or evidence.identity != specification.evidence
            or ObjectIdentity.from_record(campaign.campaign_id, campaign) != specification.campaign
            or allocation != expected.scientific_inputs["programme"] or draft != _lower(specification, inputs).draft):
        raise ValueError("selected E4 instance changes actual selected account, complete census or native dependency graph")


def protocol_declaration():
    return ExperimentProtocolDeclaration(PROTOCOL_ID, SelectedE3E4ExperimentSpecification, prepare,
        "experiment.matrix-selected-e3-e4-development", input_record_types=input_record_types(), bind_inputs=bind_inputs,
        validate_instance=validate_instance, requires_development_runtime_binding=True, input_storage_codecs=MATRIX_STORAGE_CODECS,
        configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-selected-e3-e4-resources",
            SelectedE3E4OperationalSelection, maximum_config_bytes=128 * 1024**2),))
