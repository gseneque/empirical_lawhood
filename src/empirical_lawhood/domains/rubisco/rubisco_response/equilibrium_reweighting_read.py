# SPDX-License-Identifier: MPL-2.0
"""Join selected windows to their original complete native custody and samples."""

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import math

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.input_contracts import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import independent_reference_bias_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import ReferenceEquilibriumResult, capability_for
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_read import read_reference_equilibrium
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import read_equilibrium_phase_space
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import EquilibriumReweightingSelection
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import cross_window_biases, joint_block_analysis


@dataclass(frozen=True, slots=True)
class RetainedEquilibriumTrace:
    """An original carrier, including an explicit absent-result member.

    A missing result means NOT_SUPPLIED. It is not evidence of nonentry.
    The supplied native-subwork reader owns actual custody and current access.
    """
    trace_id: str
    config: object
    representation: MolecularRepresentation
    phase_bytes: bytes
    original_result: ReferenceEquilibriumResult | None
    native_subwork: object


def recheck_reweighting_originals(sources):
    from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
    recheck_original_native_outputs(sources, description='equilibrium analysis')


def validate_reweighting_inputs(selection, sources):
    """Validate the whole prospective roster before opening any native result."""
    exact(selection, EquilibriumReweightingSelection)
    if type(sources) is not tuple or any(type(s) is not RetainedEquilibriumTrace for s in sources):
        raise TypeError('reweighting requires the complete tuple of original trace carriers')
    if tuple(s.trace_id for s in sources) != tuple(t.trace_id for t in selection.traces):
        raise ValueError('reweighting input carriers omit, repeat or reorder a selected trace')
    ensembles = {r.ensemble_id:r for r in selection.ensembles}
    schedules, streams, expected = {}, {}, {}
    workspace = 0
    projected_array_bytes = 0
    largest_atoms = 0
    for trace, source in zip(selection.traces, sources, strict=True):
        capability_for(source.config)
        exact(source.representation, MolecularRepresentation)
        if type(source.phase_bytes) is not bytes:
            raise TypeError('reweighting requires exact original phase bytes')
        if source.original_result is not None:
            exact(source.original_result, ReferenceEquilibriumResult)
        config, ensemble = source.config, ensembles[trace.ensemble_id]
        original = config.original.selection
        selected, settings = config.selection, config.selection.settings
        if (config.identity != trace.configuration or original.identity != ensemble.prototype
                or source.representation.identity != original.representation
                or settings.temperature_kelvin != ensemble.temperature_kelvin
                or ensemble.coordinate_window.model_id != source.representation.representation_id):
            raise ValueError('reweighting changes its exact configuration, common reference model or temperature')
        read_equilibrium_phase_space(selected, source.representation, source.phase_bytes)
        if selected.window is not None:
            if (selected.window.cv_atom_ids != ensemble.coordinate_window.cv_atom_ids
                    or selected.window.cv_kinds != ensemble.coordinate_window.cv_kinds
                    or any(getattr(selected.convention, key) != getattr(ensemble.coordinate_convention, key)
                        for key in ('center_units', 'force_constant_units', 'distance_difference', 'dihedral', 'periodic_images'))):
                raise ValueError('reweighting changes ordered coordinates or conventions between windows')
            if trace.bias_geometry_criteria is not None and trace.bias_geometry_criteria.convention != selected.convention.identity:
                raise ValueError('reweighting changes its selected independent bias geometry criteria')
        elif trace.bias_geometry_criteria is not None:
            raise ValueError('an unbiased window cannot supply bias geometry criteria')
        count = settings.expected_samples
        expected[trace.trace_id] = count
        clock = (count, Fraction(settings.dynamics.step_seconds)*settings.sample_interval_steps,
            Fraction(settings.dynamics.step_seconds)*(settings.discard_initial_steps+settings.sample_interval_steps),
            trace.block_samples)
        if schedules.setdefault(trace.resampling_group_id, clock) != clock:
            raise ValueError('one resampling group changes its original aligned sample clocks or block length')
        noise = (settings.random_generator, settings.random_seed)
        if streams.setdefault(noise, trace.resampling_group_id) != trace.resampling_group_id:
            raise ValueError('reused thermal random streams cannot be declared independent resampling groups')
        k = sum(t.ensemble_id == trace.ensemble_id for t in selection.traces)
        dimension = len(ensemble.coordinate_window.cv_kinds)
        workspace += count*(4096+512*k+256*dimension)
        projected_array_bytes += count*(8*dimension+40+32*k+len(ensemble.basins))
        largest_atoms = max(largest_atoms, selected.physical_atom_count)
    workspace += largest_atoms*3*8*64
    workspace += selection.criteria.bootstrap_replicates*(4096+256*len(selection.contrasts)
        +256*sum((clock[0]+clock[3]-1)//clock[3] for clock in schedules.values()))
    if workspace > selection.criteria.maximum_workspace_bytes:
        raise ValueError('complete reweighting census exceeds the selected analysis workspace allocation')
    if projected_array_bytes > MAXIMUM_MATRIX_ARRAY_BYTES or 6*len(selection.traces)+5*len(selection.ensembles) > 256:
        raise ValueError('complete reweighting projection exceeds its bounded named-array transport')
    return dict(expected_samples=expected, estimated_workspace_bytes=workspace,
        selected_workspace_bytes=selection.criteria.maximum_workspace_bytes,
        projected_array_bytes=projected_array_bytes, maximum_array_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)


def read_equilibrium_reweighting(*, selection, sources, assessor_source, sample_consumer=None):
    """Authenticate all bytes and project only checked original sample frames.

    Complete source failure refuses the read. An intact failed attempt retains
    its sample prefix and costs but supplies no complete-window estimate.
    The analysis never calls a force backend or producing bias evaluator.
    """
    import numpy as np
    capacity = validate_reweighting_inputs(selection, sources)
    exact(assessor_source, ObjectIdentity)
    if sample_consumer is not None and not callable(sample_consumer):
        raise TypeError('an equilibrium sample consumer must be callable')
    ensembles = {r.ensemble_id:r for r in selection.ensembles}
    tables, windows, trace_reports, projected = {}, {}, {}, {}
    for trace, source in zip(selection.traces, sources, strict=True):
        ensemble = ensembles[trace.ensemble_id]
        config, representation = source.config, source.representation
        dimension = len(ensemble.coordinate_window.cv_kinds)
        count = capacity['expected_samples'][trace.trace_id]
        coordinates = np.empty((count, dimension), dtype='<f8')
        energies = np.empty(count, dtype='<f8')
        energy_hartree = np.empty(count, dtype='<f8')
        original_bias = np.empty(count, dtype='<f8')
        evaluations = np.empty(count, dtype='<i8')
        coordinate_digests, used = [], 0
        atom_ids = tuple(atom.atom_id for atom in representation.atoms)
        cell = np.diag([float(v) for v in config.original.selection.cell.lengths_angstrom])

        def consume(frame):
            nonlocal used
            if used >= count or frame['sample_ordinal'] != used+1:
                raise ValueError('reweighting projection changes the complete original sample schedule')
            q = independent_reference_bias_coordinates(window=ensemble.coordinate_window,
                convention=ensemble.coordinate_convention, physical_model_id=representation.representation_id,
                physical_atom_ids=atom_ids, coordinates_angstrom=frame['coordinates_angstrom'], cell_vectors_angstrom=cell)
            converted = frame['reference_energy_hartree']*frame['hartree_kj_mol']
            if not math.isfinite(converted):
                raise ValueError('original energy cannot be represented in the selected kJ/mol analysis unit')
            coordinates[used] = q
            energy_hartree[used] = frame['reference_energy_hartree']
            energies[used] = converted
            original_bias[used] = frame['bias_energy_kj_mol']
            evaluations[used] = frame['evaluation']
            coordinate_digests.append(sha256(frame['coordinates_angstrom'].tobytes()).hexdigest())
            used += 1
            if sample_consumer is not None:
                # The original reader still owns all receipt, complete-frame
                # and closing byte checks. The callback adds no force call.
                sample_consumer(trace, source, frame, q)

        report, reasons, status = None, [], 'NOT_SUPPLIED'
        result = source.original_result
        if result is not None:
            report = read_reference_equilibrium(config=config, representation=representation, phase_bytes=source.phase_bytes,
                original_result=result, native_subwork=source.native_subwork, assessor_source=assessor_source,
                bias_geometry_criteria=trace.bias_geometry_criteria, sample_consumer=consume)
            status = 'ORIGINAL_FAILED' if report['native_error'] is not None else 'ORIGINAL_RETURNED'
            assessment = report['assessment']
            if report['assessment_error'] is not None or assessment is None:
                reasons.append('ORIGINAL_TRACE_ASSESSMENT_UNAVAILABLE')
            else:
                if assessment['selected_trace_criteria'] != 'SATISFIED':
                    reasons.append('ORIGINAL_TRACE_CRITERIA_'+assessment['selected_trace_criteria'])
                if config.selection.window is not None and assessment['bias_geometry_assessment']['selected_bias_geometry_criteria'] != 'SATISFIED':
                    reasons.append('ORIGINAL_BIAS_GEOMETRY_'+assessment['bias_geometry_assessment']['selected_bias_geometry_criteria'])
            if report['gpu_assessment_error'] is not None:
                reasons.append('ORIGINAL_GPU_OBSERVATIONS_UNAVAILABLE')
            if report['native_error'] is not None:
                reasons.append('ORIGINAL_NATIVE_FAILURE')
        else:
            reasons.append('ORIGINAL_RESULT_NOT_SUPPLIED')
        if used != count:
            reasons.append('COMPLETE_SELECTED_SAMPLE_HORIZON_UNAVAILABLE')
        if not np.isfinite(coordinates[:used]).all() or not np.isfinite(energies[:used]).all():
            reasons.append('SAMPLE_PROJECTION_NOT_FINITE')
        usable = not reasons
        prefix = dict(coordinates=coordinates[:used].copy(), reference_energy_kj_mol=energies[:used].copy(),
            reference_energy_hartree=energy_hartree[:used].copy(), original_bias_energy_kj_mol=original_bias[:used].copy(),
            evaluations=evaluations[:used].copy())
        projected[trace.trace_id] = prefix
        tables[trace.trace_id] = prefix if usable else dict(coordinates=np.empty((0, dimension), dtype='<f8'),
            reference_energy_kj_mol=np.empty(0, dtype='<f8'))
        windows[trace.trace_id] = config.selection.window
        trace_reports[trace.trace_id] = dict(ensemble_id=trace.ensemble_id, configuration=config.identity.to_document(),
            sampling_selection=config.selection.identity.to_document(), disposition=status, eligible_for_complete_window_fit=usable,
            reasons=tuple(reasons), expected_samples=count, retained_projected_samples=used,
            coordinate_sha256s=tuple(coordinate_digests), sample_interval_steps=config.selection.settings.sample_interval_steps,
            discard_initial_steps=config.selection.settings.discard_initial_steps,
            integration_step_seconds=str(config.selection.settings.dynamics.step_seconds),
            original_receipt=result.receipt.to_document() if result else None,
            original_completion=result.completion.to_document() if result else None,
            original_result=ObjectIdentity.from_record(result.result_id, result).to_document() if result else None,
            original_trace_assessment=report)
    for ensemble in selection.ensembles:
        traces = tuple(t for t in selection.traces if t.ensemble_id == ensemble.ensemble_id)
        selected_windows = tuple(windows[t.trace_id] for t in traces)
        for index, trace in enumerate(traces):
            projected[trace.trace_id]['all_window_bias_potentials_kj_mol'] = cross_window_biases(
                selected_windows, projected[trace.trace_id]['coordinates'])
            trace_reports[trace.trace_id]['cross_window_trace_order'] = tuple(t.trace_id for t in traces)
            diagonal = projected[trace.trace_id]['all_window_bias_potentials_kj_mol'][index]
            original = projected[trace.trace_id]['original_bias_energy_kj_mol']
            discrepancy = float(np.max(abs(diagonal-original))) if len(diagonal) else None
            trace_reports[trace.trace_id]['maximum_original_bias_diagonal_error_kj_mol'] = discrepancy
            limit = (trace.bias_geometry_criteria.maximum_energy_error_kj_mol if trace.bias_geometry_criteria
                else 0 if windows[trace.trace_id] is None else None)
            if discrepancy is not None and limit is not None and Fraction(discrepancy) > Fraction(limit):
                row = trace_reports[trace.trace_id]
                row['eligible_for_complete_window_fit'] = False
                row['reasons'] += ('CROSS_WINDOW_ORIGINAL_BIAS_DIAGONAL_FALSIFIED',)
                tables[trace.trace_id] = dict(coordinates=np.empty((0, len(ensemble.coordinate_window.cv_kinds)), dtype='<f8'),
                    reference_energy_kj_mol=np.empty(0, dtype='<f8'))
    statistics, fitted_arrays = joint_block_analysis(selection=selection, tables=tables, windows=windows)
    invalid = [(key, reason) for key, report in trace_reports.items() for reason in report['reasons']]
    if invalid and statistics['selected_numerical_sampling_criteria'] == 'SATISFIED':
        statistics['selected_numerical_sampling_criteria'] = 'UNEVALUABLE'
    if any('FALSIFIED' in reason for _, reason in invalid):
        statistics['selected_numerical_sampling_criteria'] = 'FALSIFIED'
    statistics['missing'] = tuple(sorted(set(statistics['missing']).union(invalid)))
    arrays = {trace+'.'+key:value for trace, table in projected.items() for key, value in table.items()}
    arrays.update({ensemble+'.'+key:value for ensemble, table in fitted_arrays.items() for key,value in table.items()})
    for value in arrays.values():
        value.setflags(write=False)
    report = dict(selection=selection.identity.to_document(), assessor_source=assessor_source.to_document(),
        capacity=capacity, trace_census=trace_reports, assigned_traces=len(selection.traces),
        supplied_results=sum(s.original_result is not None for s in sources),
        complete_window_traces=sum(t['eligible_for_complete_window_fit'] for t in trace_reports.values()),
        assigned_ensembles=len(selection.ensembles), declared_dependence_groups=len({t.resampling_group_id for t in selection.traces}),
        dependence_basis=selection.dependence_basis.to_document(), dependence_assumptions=selection.assumptions,
        statistics=statistics, new_native_calls=0, new_reference_evaluations=0,
        original_cost_scope='EACH_ORIGINAL_COMPLETION_AND_GPU_CALL_CENSUS_RETAINED_WITHOUT_DOUBLE_COUNTED_SUM',
        evidence_scope=selection.scope)
    recheck_reweighting_originals(sources)
    return report, arrays
