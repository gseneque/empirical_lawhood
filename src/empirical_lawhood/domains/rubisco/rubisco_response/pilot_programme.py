# SPDX-License-Identifier: MPL-2.0
"""Finite pilot stage assessment over existing authored work and findings.

These records select scientific prerequisites and stopping conditions. They
neither schedule work nor replace original-result authentication or authority.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import roster
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation import PilotAllocationRule


ANALYSES = ('ELECTRONIC_ENSEMBLES', 'PAIRED_FORECAST', 'PHYSICAL_SUPPLIERS', 'REACTIVE_FLUX')


@dataclass(frozen=True, slots=True)
class PilotRecipeBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-recipe-binding'
    work_id: str
    scientific_selection: ObjectIdentity
    authored_wave: ObjectIdentity
    execution_plan: ObjectIdentity
    tasks: tuple[ObjectIdentity, ...]
    native_tasks: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.work_id)
        exact(self.scientific_selection, ObjectIdentity)
        for pin, schema in ((self.authored_wave, 'empirical-lawhood/runtime/authored-recursive-wave'),
                (self.execution_plan, 'empirical-lawhood/runtime/development-execution-plan')):
            exact(pin, ObjectIdentity)
            if pin.object_schema != schema:
                raise ValueError('pilot recipe requires its actual authored packet and execution plan')
        roster(self.tasks, ObjectIdentity, 'object_id')
        if any(p.object_schema != 'empirical-lawhood/runtime/execution-task' for p in self.tasks):
            raise ValueError('pilot recipe requires its complete actual task census')
        roster(self.native_tasks, ObjectIdentity, 'object_id')
        if not set(self.native_tasks) <= set(self.tasks):
            raise ValueError('pilot native tasks must retain their exact original execution-task identities')


@dataclass(frozen=True, slots=True)
class PilotScientificGate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-scientific-gate'
    gate_id: str
    analysis_kind: str
    selection: ObjectIdentity
    recipe_work_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.gate_id)
        exact(self.selection, ObjectIdentity)
        if self.analysis_kind not in ANALYSES:
            raise ValueError('pilot scientific gate needs a supported independent supplier reader')
        require_sorted_unique_strings(self.recipe_work_ids, field_name='recipe_work_ids')


@dataclass(frozen=True, slots=True)
class PilotStage(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-stage'
    stage_id: str
    work_ids: tuple[str, ...]
    entry_gate_ids: tuple[str, ...]
    completion_gate_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.stage_id)
        for field in ('work_ids', 'entry_gate_ids', 'completion_gate_ids'):
            require_sorted_unique_strings(getattr(self, field), field_name=field)
            for value in getattr(self, field):
                validate_stable_id(value)
        if not self.work_ids or not self.completion_gate_ids:
            raise ValueError('pilot stage requires finite work and independent scientific completion criteria')


@dataclass(frozen=True, slots=True)
class PilotProgrammeRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-programme-rule'
    rule_id: str
    allocation: PilotAllocationRule
    candidate_id: str
    stages: tuple[PilotStage, ...]
    recipes: tuple[PilotRecipeBinding, ...]
    gates: tuple[PilotScientificGate, ...]
    interpretation: str = 'FINITE_SCIENTIFIC_STAGE_ASSESSMENT_NOT_EXECUTION_SPEND_OR_PHYSICAL_AUTHORITY'

    def __post_init__(self):
        validate_stable_id(self.rule_id)
        exact(self.allocation, PilotAllocationRule)
        validate_stable_id(self.candidate_id)
        candidate = next((c for c in self.allocation.candidates if c.candidate_id == self.candidate_id), None)
        if candidate is None:
            raise ValueError('pilot stages change the prospectively selected complete candidate roster')
        # Stage tuple order is the declared causal order, not lexical ID order.
        if type(self.stages) is not tuple or not self.stages or len({s.stage_id for s in self.stages}) != len(self.stages):
            raise ValueError('pilot stages require one complete ordered finite stage census')
        for stage in self.stages:
            exact(stage, PilotStage)
        classes = {c.class_id:c for c in self.allocation.cost_classes}
        native = {w.work_id for w in candidate.work if classes[w.cost_class].unit == 'COMPLETE_COUPLED_FORCE_RETURN'}
        analysis = {w.scientific_selection for w in candidate.work if classes[w.cost_class].unit == 'COMPLETE_ANALYSIS_EXPORT'}
        work_ids = tuple(w for s in self.stages for w in s.work_ids)
        if len(work_ids) != len(set(work_ids)) or set(work_ids) != native:
            raise ValueError('pilot stages must cover every native candidate work item exactly once, including shared work')
        roster(self.recipes, PilotRecipeBinding, 'work_id', allow_empty=True)
        work = {w.work_id: w for w in candidate.work}
        if any(r.work_id not in native or r.scientific_selection != work[r.work_id].scientific_selection for r in self.recipes):
            raise ValueError('pilot recipe substitutes its exact selected scientific work')
        if len({r.authored_wave for r in self.recipes}) != len(self.recipes):
            raise ValueError('one authored recipe cannot become two separately charged pilot work items')
        roster(self.gates, PilotScientificGate, 'gate_id')
        selected = {g for s in self.stages for g in (*s.entry_gate_ids, *s.completion_gate_ids)}
        if selected != {g.gate_id for g in self.gates}:
            raise ValueError('pilot stages omit or add a scientific gate')
        if not analysis <= {g.selection for g in self.gates}:
            raise ValueError('pilot stages omit selected non-force analysis/export work')
        gates = {g.gate_id:g for g in self.gates}
        previous = set()
        for stage in self.stages:
            completed = {w for g in stage.completion_gate_ids for w in gates[g].recipe_work_ids}
            entered = {w for g in stage.entry_gate_ids for w in gates[g].recipe_work_ids}
            if not set(stage.work_ids) <= completed or not completed <= previous | set(stage.work_ids) or not entered <= previous:
                raise ValueError('pilot gates omit original recipe work or create a circular scientific prerequisite')
            previous.update(stage.work_ids)
        if self.interpretation != 'FINITE_SCIENTIFIC_STAGE_ASSESSMENT_NOT_EXECUTION_SPEND_OR_PHYSICAL_AUTHORITY':
            raise ValueError('pilot stage assessment grants no native, spending or physical authority')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.rule_id, self)


def assess_pilot_progress(rule, *, allocation, recipes, gates):
    """Project authenticated observations; actual reads belong to the API.

    No elapsed duration, mutation direction or unselected confidence threshold
    enters a scientific stop. Missing or uncertain work never becomes nonentry.
    """
    exact(rule, PilotProgrammeRule)
    if allocation['rule'] != rule.allocation.identity.to_document():
        raise ValueError('pilot progress substitutes its original cost rule')
    if set(recipes) != {r.work_id for r in rule.recipes} or set(gates) != {g.gate_id for g in rule.gates}:
        raise ValueError('pilot progress omits declared recipes or scientific gates')
    if any(v not in {'SATISFIED', 'FALSIFIED', 'UNEVALUABLE'} for v in gates.values()):
        raise ValueError('pilot gate has no independently assessed three-way result')
    expected = {r.work_id: {t.object_id for t in r.tasks} for r in rule.recipes}
    allowed = {'COMPLETE', 'FAILED', 'UNKNOWN', 'UNASSESSED', 'RETURNED_PENDING_PUBLICATION'}
    for key, observed in recipes.items():
        if set(observed) != expected[key] or any(v not in allowed for v in observed.values()):
            raise ValueError('pilot progress changes its complete task census or original contact state')
    rows, previous_complete = [], True
    selected_cost = allocation['selected_candidate'] == rule.candidate_id
    for stage in rule.stages:
        entry = tuple(gates[g] for g in stage.entry_gate_ids)
        completion = tuple(gates[g] for g in stage.completion_gate_ids)
        absent = tuple(w for w in stage.work_ids if w not in recipes)
        states = tuple(value for w in stage.work_ids if w in recipes for value in recipes[w].values())
        if 'UNKNOWN' in states:
            action = 'HOLD_UNCERTAIN_CONTACT'
        elif 'RETURNED_PENDING_PUBLICATION' in states:
            action = 'RECOVER_RETURNED_PUBLICATION_ONLY'
        elif 'FAILED' in states:
            action = 'STOP_RETAINED_OPERATIONAL_FAILURE'
        elif 'FALSIFIED' in (*entry, *completion):
            action = 'STOP_SCIENTIFIC_FALSIFICATION'
        elif not previous_complete:
            action = 'WAIT_FOR_PREDECESSOR'
        elif any(v != 'SATISFIED' for v in entry):
            action = 'WAIT_FOR_ENTRY_ASSESSMENT'
        elif absent:
            action = 'PREPARE_MISSING_RECIPES'
        elif any(v != 'COMPLETE' for v in states):
            action = 'USE_EXISTING_EXECUTION_PREFLIGHT' if selected_cost else 'HOLD_COST_SELECTION'
        elif all(v == 'SATISFIED' for v in completion):
            action = 'COMPLETE'
        else:
            action = 'WAIT_FOR_INDEPENDENT_ASSESSMENT'
        previous_complete = action == 'COMPLETE'
        rows.append(dict(stage_id=stage.stage_id, action=action, work_ids=stage.work_ids,
            missing_recipe_ids=absent, entry_gates={g:gates[g] for g in stage.entry_gate_ids},
            completion_gates={g:gates[g] for g in stage.completion_gate_ids}))
    return dict(rule=rule.identity.to_document(), stages=tuple(rows),
        disposition='COMPLETE_SELECTED_STAGE_CHECKS' if all(r['action']=='COMPLETE' for r in rows) else 'PILOT_REMAINS_OPEN',
        cost_selected=selected_cost, selected_material_role_cells=44,
        task_census=recipes, gate_census=gates, new_native_calls=0, native_entry_authority='NONE',
        physical_admission='UNEVALUABLE', biological_predictive_validity='UNEVALUABLE')
