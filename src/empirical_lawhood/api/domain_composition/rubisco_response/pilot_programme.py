# SPDX-License-Identifier: MPL-2.0
"""Bind pilot recipes and assess stages through existing authenticated readers."""

from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation import PilotWorkEstimate
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_programme import PilotProgrammeRule, PilotRecipeBinding, PilotScientificGate, PilotStage, assess_pilot_progress
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import status
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.api.recursive_operations import operation_catalog_for_draft
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.execution import TaskBlockReason
from empirical_lawhood.execution.plans import DevelopmentExecutionPlan
from empirical_lawhood.api.domain_composition.rubisco_response.pilot_costs import analysis_owners, read_complete_pilot_allocation


def _recipe(work, directory, writer):
    exact(work, PilotWorkEstimate)
    packet, draft, _, payloads = load_authored_wave(directory=Path(directory), artifact_writer=writer)
    raw = payloads['execution-plan.json']
    plan = decode_canonical_bytes(raw, DevelopmentExecutionPlan, maximum_bytes=max(1, len(raw)))
    pins = set(draft.development_study.scientific_operands) | {draft.development_study.system}
    if work.scientific_selection not in pins:
        raise ValueError('pilot recipe lacks its exact selected scientific operand in the authored root')
    registrations, _, _ = operation_catalog_for_draft(draft)
    registrations = {r.selection:r for r in registrations}
    effects, native_ids = [], set()
    for operation in draft.operations:
        if operation.node_id not in draft.selected_operation_ids:
            continue
        registration = registrations[operation.selection]
        if registration.native_effect:
            native_ids.add(operation.node_id)
            raw = operation.config_payload.encode()
            config = decode_canonical_bytes(raw, registration.config_record_type, maximum_bytes=max(1, len(raw)))
            effects.extend((registration.selection, slot) for slot in registration.native_effect_slot_ids(config))
    tasks = tuple(ObjectIdentity.from_record(t.task_id, t) for t in sorted(plan.tasks, key=lambda t:t.task_id))
    return PilotRecipeBinding(work.work_id, work.scientific_selection,
        ObjectIdentity.from_record(packet.packet_id, packet), ObjectIdentity.from_record(plan.execution_plan_id, plan),
        tasks, tuple(t for t in tasks if t.object_id in native_ids)), tuple(effects)


def bind_pilot_recipe(*, work, authoring_directory, artifact_writer):
    """Bind a returned public authoring directory; create no roster or task."""
    with artifact_writer.read_context() as reader:
        return _recipe(work, authoring_directory, reader)[0]


@dataclass(frozen=True, slots=True)
class RetainedPilotRecipe:
    work_id: str
    authoring_directory: Path


@dataclass(frozen=True, slots=True)
class RetainedPilotGate:
    gate_id: str
    directory_relative_path: str | None
    sources: tuple


def _gate_status(kind, report):
    """Code-owned complete criteria; no caller-selected result JSON field."""
    if kind == 'REACTIVE_FLUX':
        findings = [r['conditional_flux_assessment'] for r in report['cases'].values()]
        findings.append('UNEVALUABLE' if report['joint_uncertainty']['failed_replicates'] else 'SATISFIED')
    elif kind == 'ELECTRONIC_ENSEMBLES':
        findings = [r['selected_golden_rule_criteria'] for r in report['pairs'].values()]
        findings.extend((report['joint']['status'], report['equilibrium']['statistics']['selected_numerical_sampling_criteria']))
    elif kind == 'PHYSICAL_SUPPLIERS':
        findings = [r['conditional_rate_assessment'] for r in report['original_rate_analysis']['cases'].values()]
        findings.extend(r['conditional_memoryless_reduction'] for r in report['networks'].values())
        findings.extend(r['status'] for r in report['encounter_reductions'].values())
        findings.append('UNEVALUABLE' if report['joint_network_realizations']['incomplete_replicates'] else 'SATISFIED')
    elif kind == 'PAIRED_FORECAST':
        findings = [r['conditional_forecast_status'] for r in report['cases'].values()]
        findings.append('SATISFIED' if report['joint']['assigned_replicates'] >= 2
            and not report['joint']['failed_replicates'] else 'UNEVALUABLE')
    else:
        raise ValueError('unsupported pilot scientific gate')
    return status(*findings) if findings else 'UNEVALUABLE'


def _task_states(report, binding):
    census = {r['task_id']:r for r in report['task_census']}
    if len(census) != len(report['task_census']) or set(census) != {t.object_id for t in binding.tasks}:
        raise ValueError('pilot recovery loses its complete original task census')
    result = {}
    for task_id, row in census.items():
        value = str(row['operational_status'])
        result[task_id] = ('COMPLETE' if value == 'SUCCEEDED' else 'FAILED' if value == 'FAILED' else
            'UNKNOWN' if value in {'UNKNOWN', 'UNKNOWN_COMPLETION', 'UNCERTAIN_CONTACT'} else 'UNASSESSED')
        if row.get('reason_code') == TaskBlockReason.UNKNOWN_COMPLETION.value:
            result[task_id] = 'UNKNOWN'
    for fact in report.get('current_native_facts', ()):
        if fact['uncertain_contact_definition_ids']:
            result[fact['task_id']] = 'UNKNOWN'
        elif fact['pending_publication_definition_ids']:
            result[fact['task_id']] = 'RETURNED_PENDING_PUBLICATION'
        elif fact['failed_return_definition_ids']:
            result[fact['task_id']] = 'FAILED'
    # An unavailable contact observation never proves that retry is safe.
    uncertain = {r['attempt_id'] for r in report.get('native_observation_unavailable', ())}
    for row in report['operational_census']:
        if row['attempt_id'] in uncertain:
            result[row['task_id']] = 'UNKNOWN'
    return result


def read_pilot_programme(*, selection, native_cost_sources, analysis_cost_sources, recipe_sources,
        gate_sources, artifact_writer, assessor_source, read_access=None):
    """Reconstruct costs, recipe custody and scientific stage gates without entry.

    Returned remote bytes use the ordinary guarded root and original readers.
    This service supplies no alternative scheduler, retry policy or authority.
    """
    exact(selection, PilotProgrammeRule)
    for sources, kind, expected, field in (
            (recipe_sources, RetainedPilotRecipe, {r.work_id for r in selection.recipes}, 'work_id'),
            (gate_sources, RetainedPilotGate, {g.gate_id for g in selection.gates}, 'gate_id')):
        if (type(sources) is not tuple or any(type(s) is not kind for s in sources)
                or len({getattr(s, field) for s in sources}) != len(sources)
                or {getattr(s, field) for s in sources} != expected):
            raise ValueError('pilot read omits or repeats its complete recipe or gate carrier census')
    recipes = {r.work_id:r for r in selection.recipes}
    work = {w.work_id:w for c in selection.allocation.candidates if c.candidate_id == selection.candidate_id for w in c.work}
    gates = {g.gate_id:g for g in selection.gates}
    observed, gate_findings, originals = {}, {}, {}
    with artifact_writer.read_context() as reader:
        effects = set()
        for source in recipe_sources:
            binding, current_effects = _recipe(work[source.work_id], source.authoring_directory, reader)
            if binding != recipes[source.work_id]:
                raise ValueError('pilot recipe changes its frozen authored packet, plan or tasks')
            if effects.intersection(current_effects):
                raise ValueError('pilot recipes repeat a native effect across separately labelled work')
            effects.update(current_effects)
        allocation = read_complete_pilot_allocation(selection=selection.allocation, native_sources=native_cost_sources,
            analysis_sources=analysis_cost_sources, artifact_writer=reader, assessor_source=assessor_source)
        for source in recipe_sources:
            report = read_recursive_wave(directory=source.authoring_directory, artifact_writer=reader,
                allow_partial=True, allow_unexecuted=True, terminal_product_format='compact', read_access=read_access)
            observed[source.work_id] = _task_states(report, recipes[source.work_id])
            originals[source.work_id] = report
        gate_originals = {}
        for source in gate_sources:
            gate = gates[source.gate_id]
            if source.directory_relative_path is None:
                gate_findings[gate.gate_id] = 'UNEVALUABLE'
                gate_originals[gate.gate_id] = None
                continue
            _, _, read = analysis_owners(gate.analysis_kind)
            original = read(directory_relative_path=source.directory_relative_path, sources=source.sources, artifact_writer=reader)
            if original['selection'].identity != gate.selection:
                raise ValueError('pilot scientific gate substitutes its original supplier selection')
            gate_findings[gate.gate_id] = _gate_status(gate.analysis_kind, original['report'])
            parents = {(s.original_result.definition.parent_contact.execution_plan,
                s.original_result.definition.parent_contact.execution_task) for s in source.sources if s.original_result is not None}
            expected = {(recipes[w].execution_plan, task) for w in gate.recipe_work_ids if w in recipes for task in recipes[w].native_tasks}
            complete_binding = (all(w in recipes for w in gate.recipe_work_ids) and expected <= parents)
            if not complete_binding:
                if gate_findings[gate.gate_id] == 'SATISFIED':
                    raise ValueError('pilot completion gate lacks original results from every declared authored recipe task')
                # An unrelated negative cannot stop or satisfy another recipe.
                gate_findings[gate.gate_id] = 'UNEVALUABLE'
            gate_originals[gate.gate_id] = dict(evidence=original['evidence'].to_document(), report=original['report'])
        result = assess_pilot_progress(selection, allocation=allocation, recipes=observed, gates=gate_findings)
        result.update(original_cost_analysis=allocation, original_recipe_reports=originals, original_gate_analyses=gate_originals)
    return result


__all__ = ('PilotProgrammeRule', 'PilotRecipeBinding', 'PilotScientificGate', 'PilotStage',
    'RetainedPilotRecipe', 'RetainedPilotGate', 'bind_pilot_recipe', 'read_pilot_programme')
