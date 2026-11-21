# SPDX-License-Identifier: MPL-2.0
"""Reconstruct a complete weighted campaign from original native custody."""

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.input_contracts import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, FirstPassagePath, WeightedPathState
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_read import RetainedFirstPassagePath, validate_first_passage_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational, summarize_first_passages
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_history import original_identity, read_physical_history
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_protocol import physical_settings, read_physical_phase
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import independent_reference_bias_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_continuation import PreparedWeightedContinuation, RetainedWeightedHistory, WeightedContinuationRule, prepare_weighted_continuation


@dataclass(frozen=True, slots=True)
class WeightedPathCampaign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/weighted-path-campaign'
    VERSION: ClassVar[str] = '1.0.0'
    campaign_id: str
    initial_rule: WeightedContinuationRule
    continuations: tuple[PreparedWeightedContinuation, ...]
    scope: str = 'ORIGINAL_WEIGHTED_PATHS_WITHOUT_RATE_OR_ENSEMBLE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.campaign_id)
        exact(self.initial_rule, WeightedContinuationRule)
        if (type(self.continuations) is not tuple or any(type(c) is not PreparedWeightedContinuation for c in self.continuations)
                or self.scope != 'ORIGINAL_WEIGHTED_PATHS_WITHOUT_RATE_OR_ENSEMBLE_ADMISSION'):
            raise ValueError('weighted campaign needs the complete ordered continuation census')
        seeds, child_ids = set(), set()
        for wave in self.continuations:
            same_campaign(self.initial_rule, wave.rule)
            if wave.resampling.selection.seed in seeds or child_ids.intersection(c.path_id for c in wave.children):
                raise ValueError('weighted campaign repeats a resampling stream or descendant')
            seeds.add(wave.resampling.selection.seed)
            child_ids.update(c.path_id for c in wave.children)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.campaign_id, self)


@dataclass(frozen=True, slots=True)
class WeightedPathEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/weighted-path-evidence'
    SELECTION_KIND: ClassVar[type] = WeightedPathCampaign


def same_campaign(original, successor):
    for name in ('initial_passages', 'bins', 'target_physical_steps', 'maximum_boundary_energy_error_kj_mol',
                 'maximum_boundary_gradient_error_kj_mol_per_angstrom'):
        if getattr(original, name) != getattr(successor, name):
            raise ValueError('weighted campaign changes its frozen original ensemble, bins, horizon or numerical criteria')
    if original.next_dynamics.step_seconds != successor.next_dynamics.step_seconds:
        raise ValueError('weighted campaign changes its physical integration step')


def _read_state(*, path_id, root, weight, history, rule, assessor_source):
    import numpy as np
    ensemble = next(e for e in rule.initial_passages.ensembles if e.ensemble_id == root.ensemble_id)
    bins = next(b for b in rule.bins if b.ensemble_id == root.ensemble_id)
    readout = read_physical_history(segments=history.segments, ensemble=ensemble, assessor_source=assessor_source,
        maximum_boundary_energy_error_kj_mol=rule.maximum_boundary_energy_error_kj_mol,
        maximum_boundary_gradient_error_kj_mol_per_angstrom=rule.maximum_boundary_gradient_error_kj_mol_per_angstrom)
    first, last = history.segments[0], history.segments[-1]
    if (first.config.identity != root.configuration or physical_settings(first.config).step_seconds != rule.next_dynamics.step_seconds
            or readout['selected_steps'] > rule.target_physical_steps):
        raise ValueError('weighted campaign substitutes its original root, clock or total physical horizon')
    if len(readout['arrays']['coordinates']):
        q = readout['arrays']['coordinates'][-1]
    else:
        xyz, _, _ = read_physical_phase(last.config, last.representation, last.phase_bytes)
        q = independent_reference_bias_coordinates(window=ensemble.coordinate_window, convention=ensemble.coordinate_convention,
            physical_model_id=last.representation.representation_id, physical_atom_ids=tuple(a.atom_id for a in last.representation.atoms),
            coordinates_angstrom=xyz, cell_vectors_angstrom=np.diag([float(v) for v in last.config.original.selection.cell.lengths_angstrom]))
    disposition = readout['path_disposition']
    status = ('ABSORBED' if disposition == 'OBSERVED_EVENT' else 'MISSING' if disposition == 'MISSING_ORIGINAL'
        else ('ACTIVE' if readout['physical_step'] < rule.target_physical_steps else 'CENSORED')
        if disposition == 'HORIZON_CENSORED' else 'FAILED')
    projected_disposition = disposition
    if status == 'ACTIVE':
        projected_disposition = 'SCHEDULED_CONTINUATION_UNOBSERVED'
    elif status == 'MISSING' and len(history.segments)>1:
        projected_disposition = 'UNOBSERVED_CONTINUATION'
    if disposition == 'HORIZON_CENSORED' and readout['original_reports'][-1]['native_error'] is not None:
        status, projected_disposition = 'FAILED', 'COMPUTATIONAL_TRUNCATION'
    state = WeightedPathState(path_id, root.ensemble_id, root.run_id, bins.bin_for(q), weight,
        readout['phase'], readout['history'], readout['physical_step'], status)
    report = dict(readout['passage'], path_disposition=projected_disposition,
        observed_segment_disposition=disposition, continuation_disposition=status,
        selected_horizon_seconds=rational(Fraction(rule.next_dynamics.step_seconds)*rule.target_physical_steps),
        original_cost=None, ensemble_id=root.ensemble_id, run_id=root.run_id, preparation_id=root.preparation_id,
        site_id=root.site_id, entry_history_id=root.entry_history_id, weight=weight.to_document(),
        boundaries=readout['boundaries'], whole_history_mechanics=readout['whole_history_mechanics'],
        original_history=[p.to_document() for p in readout['history']], original_trace_assessments=readout['original_reports'])
    return state, report, readout['arrays']


def validate_weighted_path_campaign_inputs(selection, sources):
    exact(selection, WeightedPathCampaign)
    if type(sources) is not tuple or any(type(s) is not RetainedFirstPassagePath for s in sources):
        raise TypeError('weighted campaign requires its complete original source tuple')
    by_id = {s.path_id:s for s in sources}
    if len(by_id) != len(sources) or tuple(by_id) != tuple(sorted(by_id)):
        raise ValueError('weighted campaign requires sorted unique original path carriers')
    initial = selection.initial_rule.initial_passages
    expected = {p.path_id for p in initial.paths}
    for wave in selection.continuations:
        if expected.intersection(c.path_id for c in wave.children):
            raise ValueError('weighted campaign repeats an original path identifier')
        expected.update(c.path_id for c in wave.children)
    if set(by_id) != expected:
        raise ValueError('weighted campaign omits or adds an assigned original path')
    initial_sources = tuple(by_id[p.path_id] for p in initial.paths)
    validate_first_passage_inputs(initial, initial_sources)
    # All histories may be revisited for independent reconstruction. Bound the
    # full retained coordinate projection and the live endpoint/child payloads.
    frames = sum(physical_settings(s.config).steps+1 for s in initial_sources)
    frames += sum(child.start_physical_step+physical_settings(by_id[child.path_id].config).steps+1
        for wave in selection.continuations for child in wave.children)
    dimensions = max(len(e.coordinate_window.cv_kinds) for e in initial.ensembles)
    workspace = frames*(4096+8*dimensions) + sum(s.config.selection.physical_atom_count*3*8*64 for s in sources)
    if (workspace > initial.maximum_projection_bytes or 2*len(sources)>256
            or frames*(8*dimensions+8)>MAXIMUM_MATRIX_ARRAY_BYTES):
        raise ValueError('complete weighted campaign exceeds its selected projection allocation')
    return by_id, initial, workspace


def read_weighted_path_campaign(*, selection, sources, assessor_source):
    """Independently rebuild every population, including zero-offspring parents.

    Sources include every assigned root and descendant, even an absent return.
    Every resampling uses its complete preceding population. Every preparation
    is derived again from the original full histories before reading children.
    """
    exact(assessor_source, ObjectIdentity)
    by_id, initial, workspace = validate_weighted_path_campaign_inputs(selection, sources)
    histories, roots, paths, reports, arrays = {}, {}, {}, {}, {}
    def read(path_id, root, weight, history, rule):
        state, report, data = _read_state(path_id=path_id, root=root, weight=weight, history=history,
            rule=rule, assessor_source=assessor_source)
        paths[path_id], reports[path_id], histories[path_id], roots[path_id] = state, report, history, root
        arrays[path_id+'.coordinates'], arrays[path_id+'.physical_steps'] = data['coordinates'], data['physical_steps']
    for root in initial.paths:
        read(root.path_id, root, root.weight, RetainedWeightedHistory(root.path_id, (by_id[root.path_id],)), selection.initial_rule)
    populations = [tuple(paths[p] for p in sorted(paths))]
    for prepared in selection.continuations:
        current = tuple(paths[p] for p in sorted(paths))
        if prepared.resampling.original_paths != current:
            raise ValueError('weighted continuation changes its complete independently read preceding population')
        active_histories = tuple(histories[p.path_id] for p in current if p.disposition == 'ACTIVE')
        reproduced = prepare_weighted_continuation(rule=prepared.rule, resampling=prepared.resampling,
            histories=active_histories, assessor_source=prepared.assessor_source)
        if reproduced['prepared'] != prepared:
            raise ValueError('weighted continuation changes its independently derived selections')
        parents, old_roots = histories.copy(), roots.copy()
        terminal = {p.path_id for p in prepared.resampling.retained_terminal_paths}
        paths = {p:paths[p] for p in terminal}
        for child in prepared.children:
            source = by_id[child.path_id]
            if source.config.selection != child.selection:
                raise ValueError('weighted descendant substitutes its prepared exact phase or dynamical selection')
            history = RetainedWeightedHistory(child.path_id, (*parents[child.parent_path_id].segments, source))
            row = next(r for r in prepared.resampling.offspring if r.path.path_id == child.path_id)
            read(child.path_id, old_roots[child.parent_path_id], row.path.weight, history, prepared.rule)
        populations.append(tuple(paths[p] for p in sorted(paths)))
    final = tuple(paths[p] for p in sorted(paths))
    statistic_paths = tuple(FirstPassagePath(p.path_id, p.ensemble_id, histories[p.path_id].segments[-1].config.identity,
        p.run_id, roots[p.path_id].preparation_id, roots[p.path_id].site_id, roots[p.path_id].entry_history_id, p.weight) for p in final)
    projected_selection = replace(initial, paths=statistic_paths)
    statistics = summarize_first_passages(selection=projected_selection, path_reports={p.path_id:reports[p.path_id] for p in final})
    originals = {original_identity(s):s for s in sources}
    if len(originals) != len(sources):
        raise ValueError('weighted campaign repeats an original completion as a distinct assigned path')
    cost_census = tuple(dict(path_id=s.path_id, original=pin.to_document(), result_supplied=s.original_result is not None,
        completion=s.original_result.completion.to_document() if s.original_result else None,
        cost=s.original_result.completion.cost.to_document() if s.original_result else None)
        for pin, s in sorted(originals.items(), key=lambda row:row[0].object_id))
    recheck_original_native_outputs(sources, description='weighted path campaign')
    report = dict(selection=selection.identity.to_document(), assessor_source=assessor_source.to_document(),
        populations=[[p.to_document() for p in pop] for pop in populations], path_census=reports, statistics=statistics,
        original_cost_census=cost_census, original_cost_scope='EVERY_UNIQUE_ASSIGNED_ORIGINAL_INCLUDING_ZERO_OFFSPRING_PARENTS',
        independent_units_added=0, new_native_calls=0, rate_admission='UNEVALUABLE',
        covariance_basis='ORIGINAL_RUNS_WITH_ALL_DESCENDANTS_NESTED', estimated_workspace_bytes=workspace)
    return dict(report=report, arrays=arrays, paths=final, histories=tuple(histories[p.path_id] for p in final))
