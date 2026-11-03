# SPDX-License-Identifier: MPL-2.0
"""Editable protected E4 intent; generated plans remain owned by phase lowering.

Construction establishes no prior product, source qualification or authority.
The API derivation owner authenticates original operands before publication.
"""
from collections.abc import Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixE4StructuralChoices
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.kernel.time import CausalPhase, ClockSpec, InformationCutoff, SamplingSemantics
from empirical_lawhood.kernel.worlds import NumericalCoordinateKind, NumericalViewSpec
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.planning.formal_analysis import FormalMethodCatalog, FormalGapSourceCapabilityInventory, derive_formal_gap_applicability
from empirical_lawhood.planning.study_authoring import StudyDraft, DesignInputRecord, DesignInputRole
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactWriteResult
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentInputConfigurationDeclaration,
    ExperimentPreparation, ExperimentProtocolDeclaration, ExecutionSelection, PreparedExperimentInputs,
)
from . import selected_e4_choices as scientific_choices
from . import records as old, selected_e4_programme as p, selected_e4_methods as science
from . import selected_e4_native_records as native, selected_e4_native_preparation as existing
from . import selected_e4_method_bindings as methods
from . import programme_factorial as factorial
from .selected_e4_operational_resources import SelectedE4OperationalResources
from .selected_e4_bank_recipe import SelectedE4BankRecipe, SelectedE4BankRecipeSourceInputs, validate_selected_e4_recipe_bank
from .full_factor_followup_records import ScheduledFullFactorResources

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection

PROTOCOL_ID = "matrix.e4.selected-protected-declarative"


@dataclass(frozen=True, slots=True)
class SelectedE4DeclarativeSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/declarative-specification"
    specification_id: str
    bank: ObjectIdentity | None
    bank_recipe: ObjectIdentity | None
    population_phase: str
    independent_group_count: int
    cases_per_group: int
    question: str

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (self.bank is None) == (self.bank_recipe is None):
            raise ValueError("select one exact existing bank or explicit new bank recipe")
        if self.bank is not None:
            native.exact_pin(self.bank, p.SelectedE4PhaseBank)
        else:
            native.exact_pin(self.bank_recipe, SelectedE4BankRecipe)
        if (self.population_phase not in native.POPULATIONS or type(self.independent_group_count) is not int
                or self.independent_group_count < 1 or type(self.cases_per_group) is not int
                or self.cases_per_group != 9 or not self.question.strip()):
            raise ValueError("declarative E4 requires its explicit assigned whole-group supported factorial grid")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class SelectedE4RootSelection(CanonicalRecord):
    """Scientific templates plus explicit binding of source clocks/timesteps.

    No task roster, generated source identities or derived draft is authored.
    Other scientific fields and all authority ceilings are retained exactly.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/root-selection"
    record_id: str
    template: StudyDraft
    source_clock: ClockSpec
    primary_view: NumericalViewSpec
    fine_view: NumericalViewSpec
    timestep_coordinate_id: str
    design_cutoff: InformationCutoff
    operator_id: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.timestep_coordinate_id)
        validate_stable_id(self.operator_id)
        if (type(self.template) is not StudyDraft or self.template.system is None or self.template.experiment is None
                or self.template.campaign is None or type(self.source_clock) is not ClockSpec
                or type(self.primary_view) is not NumericalViewSpec or type(self.fine_view) is not NumericalViewSpec
                or type(self.design_cutoff) is not InformationCutoff):
            raise TypeError("E4 root selection needs exact original scientific and operational templates")
        for view in (self.primary_view, self.fine_view):
            if (view.world_id != self.template.system.world.world_id
                    or len(tuple(value for value in view.coordinates if value.coordinate_id == self.timestep_coordinate_id)) != 1):
                raise ValueError("E4 view selection must explicitly identify its source timestep coordinate")
        if self.design_cutoff.phase is not CausalPhase.PREPARATION:
            raise ValueError("E4 intent must freeze at an explicitly declared pre-entry preparation cutoff")
        for view in (self.primary_view, self.fine_view):
            coordinate, = (value for value in view.coordinates if value.coordinate_id == self.timestep_coordinate_id)
            if coordinate.kind is not NumericalCoordinateKind.TIMESTEP:
                raise ValueError("E4 timestep binding must identify an actual declared timestep coordinate")
        if self.template.unresolved_decisions:
            raise ValueError("resolve scientific choices before deriving a protected E4 plan")
        if (self.template.development_unit_ids or self.template.evaluation_unit_ids or self.template.development_seed_ids
                or self.template.evaluation_seed_ids or self.template.source_materializations
                or self.template.capability_selections or self.template.conditional_successor is not None):
            raise ValueError("E4 scientific template cannot preselect generated units, seeds, source/task rosters or a conditional successor")

    @property
    def identity(self):
        return native.pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4DeclarativeRequest(CanonicalRecord):
    """Component-aware entry lowering with explicit scientific choices."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/declarative-request"
    VERSION: ClassVar[str] = "6.0.0"
    record_id: str
    programme_id: str | None
    programme_directory: str
    bank_publication: ArtifactWriteResult | None
    source: native.SelectedE4SourceQualification | None
    upstream_products: tuple[MatrixSelectedOriginalProduct, ...]
    development_nomination: native.SelectedE4DevelopmentProduct
    development_freeze: native.SelectedE4DevelopmentProduct
    calibration_product: MatrixSelectedOriginalProduct | None
    calibration_programme_id: str | None
    root: SelectedE4RootSelection
    entry: ExperimentEntryPackage
    formal_methods: FormalMethodCatalog
    formal_source_inventory: FormalGapSourceCapabilityInventory
    native_budgets: native.SelectedE4NativeBudgets
    method_resources: methods.SelectedE4MethodResources
    resources: SelectedE4OperationalResources
    calibration_alpha: Decimal | None
    nomination_rule: science.SelectedE4NominationRule | science.SelectedE4MatchedRelationRule | None
    factorial: scientific_choices.SelectedE4FactorialChoices | None
    structure: MatrixE4StructuralChoices
    structural_resources: ScheduledFullFactorResources
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents
        validate_produced_input_parents(self.produced_input_parents)
        validate_stable_id(self.record_id)
        if self.programme_id is not None:
            validate_stable_id(self.programme_id)
        validate_relative_locator(self.programme_directory)
        if self.calibration_programme_id is not None:
            validate_stable_id(self.calibration_programme_id)
        for value, kind in (
                (self.development_nomination, native.SelectedE4DevelopmentProduct), (self.development_freeze, native.SelectedE4DevelopmentProduct),
                (self.root, SelectedE4RootSelection), (self.entry, ExperimentEntryPackage), (self.formal_methods, FormalMethodCatalog),
                (self.formal_source_inventory, FormalGapSourceCapabilityInventory), (self.native_budgets, native.SelectedE4NativeBudgets),
                (self.method_resources, methods.SelectedE4MethodResources), (self.resources, SelectedE4OperationalResources),
                (self.structure, MatrixE4StructuralChoices), (self.structural_resources, ScheduledFullFactorResources)):
            if type(value) is not kind:
                raise TypeError("declarative E4 requires each exact typed original/scientific/operational selection")
            value.__post_init__()
        for value, kind in ((self.bank_publication, ArtifactWriteResult), (self.source, native.SelectedE4SourceQualification)):
            if value is not None:
                if type(value) is not kind:
                    raise TypeError("E4 source prerequisites require actual original typed evidence")
                value.__post_init__()
        if (type(self.upstream_products) is not tuple or len(self.upstream_products) != 4
                or any(type(value) is not MatrixSelectedOriginalProduct for value in self.upstream_products)
                or self.calibration_product is not None and type(self.calibration_product) is not MatrixSelectedOriginalProduct):
            raise ValueError("declarative E4 needs four actual E3 producers and a distinct optional issued E4 CAL producer")
        expected={pin for value in self.upstream_products for pin in (value.record,value.prior_execution.receipt)}
        expected.update(pin for value in (self.development_nomination,self.development_freeze) for pin in (value.record,value.receipt))
        if self.calibration_product is not None:
            expected.update((self.calibration_product.record,self.calibration_product.prior_execution.receipt))
        if {value.identity for value in self.produced_input_parents}!=expected:
            raise ValueError("declarative E4 changes its complete exact produced-parent census")
        if self.calibration_alpha is not None and (type(self.calibration_alpha) is not Decimal
                or not self.calibration_alpha.is_finite() or not 0 < self.calibration_alpha < 1):
            raise ValueError("declarative E4 calibration alpha must be explicitly selected in (0,1)")
        if (self.nomination_rule is None) != (self.factorial is None):
            raise ValueError("declarative E4 CONF requires its complete nomination and factorial choices")
        if self.nomination_rule is not None:
            if type(self.nomination_rule) not in (science.SelectedE4NominationRule, science.SelectedE4MatchedRelationRule) or type(self.factorial) is not scientific_choices.SelectedE4FactorialChoices:
                raise TypeError("declarative E4 nomination and factorial choices require their exact typed scientific records")
            self.nomination_rule.__post_init__()
            self.factorial.__post_init__()

    @property
    def identity(self):
        return native.pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4DeclarativeInputs:
    request: SelectedE4DeclarativeRequest
    bank: p.SelectedE4PhaseBank | None
    calibration_bank: p.SelectedE4PhaseBank | None
    plan: existing.SelectedE4ProtectedProgrammePlan | None
    bank_recipe_inputs: SelectedE4BankRecipeSourceInputs | None = None
    secondary_readout: MatrixE4SecondaryReadoutSelection | None = None


def validate_request(specification, request, bank, calibration_bank=None):
    if (type(specification) is not SelectedE4DeclarativeSpecification or type(request) is not SelectedE4DeclarativeRequest
            or type(bank) is not p.SelectedE4PhaseBank):
        raise TypeError("declarative E4 requires its exact copied specification/request/bank roles")
    specification.__post_init__()
    request.__post_init__()
    bank.__post_init__()
    if (specification.bank is not None and specification.bank != bank.identity
            or (specification.population_phase, specification.independent_group_count, specification.cases_per_group) != (
                bank.phase, bank.design.group_count, bank.design.cases_per_group)):
        raise ValueError("declarative E4 specification changes its complete actual bank population")
    if request.programme_id is None:
        raise ValueError("derive the actual protected programme from the selected bank recipe first")
    programme = p.SelectedE4PhaseProgramme.from_bank(bank, programme_id=request.programme_id)
    from .selected_e4_structure import structural_measurement
    structural_measurement(programme=programme, bank=bank, choices=request.structure)
    if request.bank_publication is not None:
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeProducedInput
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents
        MatrixProgrammeProducedInput(bank.identity,request.bank_publication).require_record(bank,bank.identity)
        validate_produced_input_parents(request.bank_publication.logical.lineage_parents)
        expected={pin for value in request.upstream_products for pin in (value.record,value.prior_execution.receipt)}
        actual={value for value in request.bank_publication.logical.lineage_parents if value.identity in expected}
        if actual!={value for value in request.produced_input_parents if value.identity in expected}:
            raise ValueError("declarative E4 bank changes exact original E3 produced-parent labels")
    if request.resources.controls.maximum_parallel_tasks is None:
        raise ValueError("declarative E4 requires an explicit worker selection")
    request.method_resources.for_operations(methods.operations_for_programme(programme))
    if bank.phase == "CALIBRATION":
        if (request.calibration_alpha is None or request.calibration_alpha != 1 - bank.design.confidence
                or calibration_bank is not None or request.calibration_programme_id is not None
                or request.calibration_product is not None or request.factorial is not None):
            raise ValueError("CAL request needs its exact explicit alpha and cannot consume future CONF choices")
    else:
        if (type(calibration_bank) is not p.SelectedE4PhaseBank or calibration_bank.phase != "CALIBRATION"
                or request.calibration_programme_id is None or request.calibration_alpha is not None
                or request.factorial is None or request.nomination_rule.confirmation_group_count != len(programme.group_ids)
                or request.factorial.target.criterion != programme.criterion):
            raise ValueError("CONF request needs its actual separate declared CAL bank and explicit complete inference choices")
        p.SelectedE4PhaseProgramme.from_bank(calibration_bank, programme_id=request.calibration_programme_id)
    return programme


def bind_inputs(specification, records, **kwargs):
    if not isinstance(records, Mapping) or set(records) - {"request", "bank", "calibration_bank", "plan", "bank-recipe-inputs", "secondary_readout"} or "request" not in records:
        raise ValueError("declarative E4 sources require request/bank and only optional original CAL bank/derived plan")
    selected = SelectedE4DeclarativeInputs(records["request"], records.get("bank"), records.get("calibration_bank"),
        records.get("plan"), records.get("bank-recipe-inputs"), records.get("secondary_readout"))
    if type(selected.request) is not SelectedE4DeclarativeRequest:
        raise TypeError("declarative E4 request role requires its exact editable request record")
    selected.request.__post_init__()
    for value, kind in ((selected.bank, p.SelectedE4PhaseBank), (selected.calibration_bank, p.SelectedE4PhaseBank),
            (selected.plan, existing.SelectedE4ProtectedProgrammePlan)):
        if value is not None and type(value) is not kind:
            raise TypeError("declarative E4 optional scientific roles require their exact installed record types")
    if selected.secondary_readout is not None:
        if type(selected.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError('E4 requires its actual original pre-future target selection')
        selected.secondary_readout.validate_target(selected.request.structure.secondary_target)
    if specification.bank_recipe is not None:
        if (type(selected.bank_recipe_inputs) is not SelectedE4BankRecipeSourceInputs
                or selected.bank_recipe_inputs.recipe.identity != specification.bank_recipe):
            raise ValueError("declarative E4 requires the exact copied new-bank recipe source bundle")
        selected.bank_recipe_inputs.__post_init__()
        expected_design = dict(selected.bank_recipe_inputs.recipe.population_designs)[specification.population_phase]
        if (expected_design.group_count, expected_design.cases_per_group) != (
                specification.independent_group_count, specification.cases_per_group):
            raise ValueError("editable recipe and specification change the declared full group/design count")
    elif selected.bank_recipe_inputs is not None:
        raise ValueError("an immutable-bank specification cannot silently select a different recipe")
    if selected.bank is None:
        if selected.plan is not None or specification.bank_recipe is None:
            raise ValueError("declarative E4 requires its exact existing bank or owned recipe derivation")
        return PreparedExperimentInputs({}, selected)
    validate_request(specification, selected.request, selected.bank, selected.calibration_bank)
    if selected.bank_recipe_inputs is not None:
        validate_selected_e4_recipe_bank(selected.bank_recipe_inputs, selected.bank, selected.bank.phase)
        if selected.calibration_bank is not None:
            validate_selected_e4_recipe_bank(selected.bank_recipe_inputs, selected.calibration_bank, selected.calibration_bank.phase)
    scientific = {} if selected.plan is None else {selected.bank.phase.lower(): existing.programme_allocation(selected.plan)}
    if selected.plan is not None:
        validate_plan(specification, selected)
    return PreparedExperimentInputs(scientific, selected)


def derive_root(specification, request, bank, programme, evidence, revision, summary, calibration, *, recipe_inputs=None):
    selected, template = request.root, request.root.template
    cutoff = selected.design_cutoff
    if (cutoff.clock_id not in {value.clock_id for value in template.system.clocks}
            and cutoff.clock_id not in {value.information_cutoff.clock_id for value in programme.cases}):
        raise ValueError("selected pre-entry cutoff is outside actual declared source clocks")
    if any(case.information_cutoff.clock_id == cutoff.clock_id
            and cutoff.coordinate > case.information_cutoff.coordinate for case in programme.cases):
        raise ValueError("E4 intent cutoff is later than an assigned case forecast cutoff")
    clocks = {value.clock_id: value for value in template.system.clocks}
    views = {value.view_id: value for value in template.system.numerical_views}
    index=bank.source_index()
    for descriptor in bank.sources:
        coordinate = bank.source(descriptor.root_id,index=index).coordinate
        clock = replace(selected.source_clock, clock_id=coordinate.clock_id,
            nominal_period=coordinate.primary_view.timestep if selected.source_clock.sampling is SamplingSemantics.REGULAR else None)
        if clock.time_unit != coordinate.primary_view.time_unit:
            raise ValueError("root clock template cannot reinterpret the actual source physical time unit")
        previous = clocks.get(clock.clock_id)
        if previous is not None and previous != clock:
            raise ValueError("root clock selection conflicts with an existing scientific clock")
        clocks[clock.clock_id] = clock
        for prototype, native_view in ((selected.primary_view, coordinate.primary_view), (selected.fine_view, coordinate.fine_view)):
            timestep, = (value for value in prototype.coordinates if value.coordinate_id == selected.timestep_coordinate_id)
            if timestep.unit != native_view.time_unit:
                raise ValueError("root numerical timestep unit differs from the actual source time unit")
            if prototype.precision.upper() != native_view.precision.upper():
                raise ValueError("root numerical metadata changes the selected native precision")
            row = replace(prototype, view_id=native_view.view_id, coordinates=tuple(
                replace(value, value=native_view.timestep) if value.coordinate_id == selected.timestep_coordinate_id else value
                for value in prototype.coordinates))
            previous = views.get(row.view_id)
            if previous is not None and previous != row:
                raise ValueError("root view selection conflicts with an existing scientific numerical view")
            views[row.view_id] = row
    system = replace(template.system, clocks=tuple(clocks[key] for key in sorted(clocks)),
        numerical_views=tuple(views[key] for key in sorted(views)))
    experiment = replace(template.experiment, information_cutoffs=tuple(value.information_cutoff for value in programme.cases))
    substitutions = {native.pin(template.system, "system_id"): native.pin(system, "system_id"),
        native.pin(template.experiment, "experiment_id"): native.pin(experiment, "experiment_id")}
    campaign = replace(template.campaign, nodes=tuple(replace(value,
        object_identity=substitutions.get(value.object_identity, value.object_identity)) for value in template.campaign.nodes))
    pins = {specification.identity, request.identity, bank.identity, programme.identity, programme.reservation,
        programme.allocation, programme.specification, programme.forecast_design, programme.response_selection,
        programme.criterion, evidence.identity, revision.decision.identity, summary.identity, *programme.source_census}
    if recipe_inputs is not None:
        pins.update((recipe_inputs.identity, recipe_inputs.recipe.identity))
    for descriptor in bank.sources:
        source = native.SelectedE4ProtectedNativeSourceReference.from_bank(programme,bank,descriptor,index=index)
        pins.update((source.identity, source.reference.identity, source.provenance,
            ObjectIdentity.from_record("public." + source.root_id, source.public)))
    pins.update(ObjectIdentity.from_record(value.protocol_id, value) for value in bank.response_selection.protocols)
    pins.update(ObjectIdentity.from_record(value.panel_id, value) for _, rows in bank.response_selection.panels for value in rows)
    if revision.models is not None:
        pins.add(revision.models.identity)
    if calibration is not None:
        pins.add(calibration.identity)
    if len({value.object_id for value in pins}) != len(pins):
        raise ValueError("declarative E4 aliases distinct scientific operands under one object ID")
    originals = tuple(template.design_inputs)
    if any(value.information_cutoff != cutoff for value in originals):
        raise ValueError("scientific root premises must retain the same explicitly declared pre-entry cutoff")
    existing_pins = {value.object_identity for value in originals}
    additions = tuple(DesignInputRecord("design." + request.record_id + "." + sha256(value.canonical_bytes()).hexdigest(),
        value, value.object_fingerprint, cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, selected.operator_id) for value in sorted(pins - existing_pins, key=lambda value: value.object_id))
    designs = tuple(sorted((*originals, *additions), key=lambda value: value.input_id))
    return replace(template, draft_id="draft." + request.record_id, question=specification.question,
        system=system, experiment=experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(template.design_origin, declared_input_ids=tuple(value.input_id for value in designs)),
        development_unit_ids=(), evaluation_unit_ids=programme.group_ids, development_seed_ids=(), evaluation_seed_ids=(),
        source_materializations=(), capability_selections=())


def assemble_plan(specification, selected, *, evidence, revision, summary, calibration):
    request, bank = selected.request, selected.bank
    if type(selected.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
        raise ValueError('E4 protected plan requires its original pre-future target selection')
    selected.secondary_readout.validate_target(request.structure.secondary_target)
    programme = validate_request(specification, request, bank, selected.calibration_bank)
    root = derive_root(specification, request, bank, programme, evidence, revision, summary, calibration,
        recipe_inputs=selected.bank_recipe_inputs)
    declaration = native.SelectedE4NativeProgrammeDeclaration("declaration." + request.record_id, programme, bank.identity,
        request.bank_publication, root, evidence.identity, revision.decision, revision.models, calibration,
        request.native_budgets, request.resources.controls.maximum_parallel_tasks, summary, request.produced_input_parents)
    if bank.phase == "CALIBRATION":
        choice = p.SelectedE4CalibrationSpecification("calibration." + request.record_id, revision.decision.development,
            programme.identity, revision.decision.nomination, revision.decision.frozen, request.calibration_alpha,
            p.RELATION_SCORE_RULE if revision.models.relation_fit is not None else p.SCORE_RULE)
        tail = existing.SelectedE4ProtectedTailSelection("tail." + request.record_id, revision, request.method_resources, choice, None)
    else:
        cal = p.SelectedE4PhaseProgramme.from_bank(selected.calibration_bank, programme_id=request.calibration_programme_id)
        public = bank.forecast_design.package
        scientific = science.SelectedE4ProgrammeSpecification("scientific." + request.record_id,
            public.original_package, old.identity(public.models), revision.decision.development, cal.identity, programme.identity,
            request.nomination_rule, factorial.declared_family(request.factorial))
        scope = methods.SelectedE4ConfirmationScope("scope." + request.record_id, scientific, revision, calibration,
            request.factorial.bind(programme.identity))
        tail = existing.SelectedE4ProtectedTailSelection("tail." + request.record_id, revision, request.method_resources, None, scope)
    aggregate = ResourceBudget.aggregate((*dict(declaration.planned_task_budgets).values(),
        *(value for _, value in request.method_resources.phase_budgets)))
    for name, ceiling in (("root", root.resource_ceiling), ("authority", root.system.authority_policy.budget_ceiling), ("campaign", root.campaign.budget)):
        if not ceiling.contains(aggregate):
            raise ValueError("declared " + name + " ceiling does not contain complete frozen E4 phase reservations")
    inventory = replace(request.formal_source_inventory, denominator_id=root.system.system_id,
        evidence_world=request.entry.checklist.portfolio_world, independent_unit_ids=programme.group_ids,
        numerical_view_ids=tuple(value.view_id for value in root.system.numerical_views))
    coverage = replace(request.entry.coverage, candidate_act_id=root.draft_id, denominator_id=root.system.system_id,
        applicability=derive_formal_gap_applicability(request.entry.register, inventory))
    entry = replace(request.entry, coverage=coverage, checklist=replace(request.entry.checklist,
        draft=native.pin(root, "draft_id"), formal_gap_coverage=native.pin(coverage, "coverage_id")))
    existing.validate_component_formal_selection(root, entry, request.formal_methods, bank.phase)
    preparation = existing.SelectedE4ProgrammePreparationSelectionV2("preparation." + request.record_id, entry,
        request.formal_methods, (inventory,), (), (), request.resources)
    old_spec = existing.SelectedE4ProtectedProgrammeSpecification("experiment." + request.record_id, declaration.identity,
        bank.phase, len(programme.group_ids), programme.design.cases_per_group, specification.question)
    return existing.SelectedE4ProtectedProgrammePlan("plan." + request.record_id, old_spec, declaration, bank, evidence,
        preparation, tail, request.structure, selected.secondary_readout, request.structural_resources)


def with_access(plan, source_configs, qualifications):
    preparation = plan.preparation
    materials = tuple(sorted({value.materialization for value in qualifications}, key=lambda value: value.object_id))
    if len({value.object_id for value in materials}) != len(materials):
        raise ValueError("derived source materializations alias distinct input identities")
    inventory = replace(preparation.formal_source_inventories[0], source_materializations=materials)
    coverage = replace(preparation.entry.coverage, applicability=derive_formal_gap_applicability(preparation.entry.register, inventory))
    entry = replace(preparation.entry, coverage=coverage, checklist=replace(preparation.entry.checklist,
        formal_gap_coverage=native.pin(coverage, "coverage_id")))
    return replace(plan, preparation=replace(preparation, entry=entry, formal_source_inventories=(inventory,),
        source_configs=tuple(sorted(source_configs, key=lambda value: value.source_id)),
        qualifications=tuple(sorted(qualifications, key=lambda value: value.receipt_id))))


def validate_plan(specification, selected):
    plan = selected.plan
    if type(plan) is not existing.SelectedE4ProtectedProgrammePlan:
        raise TypeError("declarative E4 needs the exact generated full plan")
    expected = assemble_plan(specification, selected, evidence=plan.evidence, revision=plan.tail.revision,
        summary=plan.declaration.original_summary, calibration=plan.declaration.calibration)
    # Actual access records have their own I/O owner. Recompute all formal
    # selections from unchanged intent plus that exact materialization census.
    expected = with_access(expected, plan.preparation.source_configs, plan.preparation.qualifications)
    if expected != plan or plan.evidence != native.SelectedE4ProtectedEvidence("evidence." + selected.request.record_id,
            plan.declaration.programme.identity, selected.request.upstream_products, selected.request.development_nomination,
            selected.request.development_freeze, selected.request.source, selected.request.calibration_product,
            selected.request.produced_input_parents):
        raise ValueError("derived E4 plan changes copied scientific intent, original producers or selected operational controls")
    return plan


def prepare(specification, *, scientific_inputs, execution, protocol_bytes=None, method_inputs=None):
    if type(method_inputs) is not SelectedE4DeclarativeInputs or type(execution) is not ExecutionSelection:
        raise TypeError("declarative E4 preparation needs copied typed inputs and explicit execution")
    selected = method_inputs
    workers = selected.request.resources.controls.maximum_parallel_tasks
    if execution.workers is not None and execution.workers != workers:
        raise ValueError("explicit E4 execution workers differ from the copied resource selection")
    if selected.bank is None:
        return ExperimentPreparation(specification.identity,
            ExperimentCensus((("groups", specification.independent_group_count),),
                (("groups", specification.independent_group_count),), (), (), 0),
            (ExperimentDependency("matrix.selected-e4.derive-bank", DependencyKind.EXTERNAL_INPUT,
                "Run experiment-derive-inputs; derive the newly declared bank from original source/recipe inputs. New scientific source qualification remains required."),),
            execution=execution, specification_record=specification)
    programme = validate_request(specification, selected.request, selected.bank, selected.calibration_bank)
    if selected.plan is None:
        if scientific_inputs:
            raise ValueError("unbound E4 cannot substitute caller-derived allocations")
        dependencies = [ExperimentDependency("matrix.selected-e4.derive-inputs", DependencyKind.EXTERNAL_INPUT,
            "Run experiment-derive-inputs on the copied request/bank selection; actual original DEV/E3/source custody is required.")]
        if selected.request.bank_publication is None:
            dependencies.append(ExperimentDependency("matrix.selected-e4.bank-publication", DependencyKind.EXTERNAL_INPUT,
                "The exact derived bank requires its actual current guarded publication."))
        if selected.secondary_readout is None:
            dependencies.append(ExperimentDependency('matrix.selected-e4.secondary-readout', DependencyKind.EXTERNAL_INPUT,
                'Select the actual E4 target publication sealed by the original DEV entry; later phases cannot publish a replacement.'))
        source = selected.request.source
        if source is None or source.specification.source_identity != selected.bank.identity:
            dependencies.append(ExperimentDependency("matrix.selected-e4.source-qualification", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The newly declared bank requires matching independent source/preparation/assay/numerical/causal/completeness gates with actual original producer custody."))
        return ExperimentPreparation(specification.identity,
            ExperimentCensus((("cases", len(programme.cases)), ("groups", len(programme.group_ids))),
                (("cases", len(programme.cases)), ("groups", len(programme.group_ids))), (), (), 0),
            tuple(sorted(dependencies, key=lambda value: value.code)),
            execution=execution, specification_record=specification)
    plan = validate_plan(specification, selected)
    original = existing.prepare_programme(plan.specification, scientific_inputs=scientific_inputs,
        execution=execution, method_inputs=plan)
    records = [(selected.request.record_id, selected.request), (specification.specification_id, specification)]
    for value in (selected.calibration_bank, selected.bank_recipe_inputs, selected.secondary_readout):
        if value is not None:
            records.append((value.identity.object_id, value))
    return replace(original, specification=specification.identity, specification_record=specification,
        design_records=tuple(sorted(records)))


def protocol_declaration():
    return ExperimentProtocolDeclaration(PROTOCOL_ID, SelectedE4DeclarativeSpecification, prepare,
        "matrix-selected-e4-declarative",
        example_paths=("programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-calibration.example.json",
            "programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/declarative-confirmation.example.json"),
        maximum_config_bytes=64 * 1024**2,
        input_record_types=(SelectedE4DeclarativeRequest, p.SelectedE4PhaseBank, existing.SelectedE4ProtectedProgrammePlan,
            SelectedE4BankRecipeSourceInputs, MatrixE4SecondaryReadoutSelection),
        bind_inputs=bind_inputs, programme_record_type=existing.SelectedE4ProtectedProgrammePlan,
        configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-selected-e4-request",
            SelectedE4DeclarativeRequest, maximum_config_bytes=64 * 1024**2),))
