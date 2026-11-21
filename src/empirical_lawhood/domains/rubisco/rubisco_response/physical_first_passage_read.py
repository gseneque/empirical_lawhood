# SPDX-License-Identifier: MPL-2.0
"""Original-custody first passages from unbiased reference trajectory frames."""

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.input_contracts import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import independent_reference_bias_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_protocol import stochastic_path, physical_settings, original_result_kind, read_physical_phase, validate_path_model, read_physical_path, complete_horizon, mechanics_prefix_acceptable
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageSelection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import PassageObserver, summarize_first_passages
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs


@dataclass(frozen=True, slots=True)
class RetainedFirstPassagePath:
    """An original carrier; None means NOT_SUPPLIED, never proven nonentry."""
    path_id: str
    config: object
    representation: MolecularRepresentation
    phase_bytes: bytes
    original_result: object | None
    native_subwork: object


def validate_first_passage_inputs(selection, sources):
    exact(selection, FirstPassageSelection)
    if type(sources) is not tuple or any(type(s) is not RetainedFirstPassagePath for s in sources):
        raise TypeError('first-passage read requires its complete original carrier tuple')
    if tuple(s.path_id for s in sources) != tuple(p.path_id for p in selection.paths):
        raise ValueError('first-passage input carriers omit or reorder a selected path')
    ensembles = {e.ensemble_id:e for e in selection.ensembles}
    clocks, phases, streams, sizes = {}, {}, {}, {}
    bytes_needed, largest_atoms = 0, 0
    for path, source in zip(selection.paths, sources, strict=True):
        stochastic=stochastic_path(source.config)
        exact(source.representation, MolecularRepresentation)
        if source.original_result is not None:
            exact(source.original_result, original_result_kind(source.config))
        config, ensemble = source.config, ensembles[path.ensemble_id]
        prototype = config.original.selection
        if (path.configuration != config.identity or prototype.identity != ensemble.prototype
                or source.representation.identity != prototype.representation
                or ensemble.coordinate_window.model_id != source.representation.representation_id):
            raise ValueError('first-passage input changes its original model, configuration or coordinate definition')
        validate_path_model(config,ensemble)
        read_physical_phase(config,source.representation,source.phase_bytes)
        dynamics=physical_settings(config)
        clock = (Fraction(dynamics.step_seconds), dynamics.steps)
        if clocks.setdefault(path.ensemble_id, clock) != clock:
            raise ValueError('one passage ensemble changes its selected time step or physical horizon')
        phase = (path.ensemble_id, config.selection.phase_bytes.object_fingerprint)
        if not stochastic and phases.setdefault(phase, path.run_id) != path.run_id:
            raise ValueError('identical deterministic phase histories cannot be declared separate original runs')
        if stochastic:
            seed=(config.selection.settings.random_generator,config.selection.settings.random_seed)
            if streams.setdefault(seed,path.run_id)!=path.run_id:
                raise ValueError('reused stochastic path streams cannot be declared separate original runs')
        frames = dynamics.steps+1
        sizes[path.path_id] = frames
        bytes_needed += frames*(8*len(ensemble.coordinate_window.cv_kinds)+8)
        largest_atoms = max(largest_atoms, config.selection.physical_atom_count)
    # Coordinate digests, event transitions and original-read frames also use
    # space. This is a conservative selected workspace estimate, not RSS proof.
    workspace = bytes_needed*4+sum(sizes.values())*1024+largest_atoms*3*8*48
    if (workspace > selection.maximum_projection_bytes or bytes_needed > MAXIMUM_MATRIX_ARRAY_BYTES
            or 2*len(selection.paths) > 256):
        raise ValueError('complete first-passage census exceeds the selected projection allocation')
    return dict(expected_frames=sizes, projected_array_bytes=bytes_needed,
        estimated_workspace_bytes=workspace, selected_workspace_bytes=selection.maximum_projection_bytes)


def path_disposition(config, original, observer):
    """Classify the retained prefix without treating computational loss as censoring."""
    if original is None:
        return 'MISSING_ORIGINAL'
    assessment = original['assessment']
    disposition = 'MECHANICS_UNEVALUABLE'
    if assessment is not None and original['assessment_error'] is None:
        if assessment['selected_trace_criteria'] == 'FALSIFIED':
            disposition = 'MECHANICS_FALSIFIED'
        elif mechanics_prefix_acceptable(config, assessment):
            if observer.entry_valid is not True:
                disposition = 'ENTRY_OUTSIDE_SELECTED_REGION'
            elif observer.first_event is not None:
                disposition = 'OBSERVED_EVENT'
            elif complete_horizon(config, assessment):
                disposition = 'HORIZON_CENSORED'
            else:
                disposition = 'COMPUTATIONAL_TRUNCATION'
    if original['gpu_assessment_error'] is not None:
        disposition = 'GPU_OBSERVATIONS_UNAVAILABLE'
    return disposition


def read_first_passages(*, selection, sources, assessor_source):
    """Read every original byte; expose events, failures and censored weight."""
    import numpy as np
    capacity = validate_first_passage_inputs(selection, sources)
    exact(assessor_source, ObjectIdentity)
    ensembles = {e.ensemble_id:e for e in selection.ensembles}
    reports, arrays = {}, {}
    for path, source in zip(selection.paths, sources, strict=True):
        config, ensemble = source.config, ensembles[path.ensemble_id]
        dynamics=physical_settings(config)
        observer = PassageObserver(ensemble=ensemble, settings=dynamics)
        coordinates = np.empty((capacity['expected_frames'][path.path_id],len(ensemble.coordinate_window.cv_kinds)),dtype='<f8')
        steps = np.empty(capacity['expected_frames'][path.path_id], dtype='<i8')
        digests, used = [], 0
        atom_ids = tuple(a.atom_id for a in source.representation.atoms)
        cell = np.diag([float(v) for v in config.original.selection.cell.lengths_angstrom])

        def consume(frame):
            nonlocal used
            if used >= len(steps):
                raise ValueError('first-passage projection exceeds its original complete frame census')
            q = independent_reference_bias_coordinates(window=ensemble.coordinate_window,
                convention=ensemble.coordinate_convention, physical_model_id=source.representation.representation_id,
                physical_atom_ids=atom_ids, coordinates_angstrom=frame['coordinates_angstrom'], cell_vectors_angstrom=cell)
            clock_key='sampling_time_seconds' if stochastic_path(config) else 'physical_time_seconds'
            observer.consume(step=frame['step'], physical_time_seconds=frame[clock_key],coordinates=q)
            coordinates[used], steps[used] = q, frame['step']
            digests.append(sha256(frame['coordinates_angstrom'].tobytes()).hexdigest())
            used += 1

        result, original = source.original_result, None
        if result is not None:
            original = read_physical_path(config=config, representation=source.representation, phase_bytes=source.phase_bytes,
                original_result=result, native_subwork=source.native_subwork, assessor_source=assessor_source, frame_consumer=consume)
        disposition = path_disposition(config, original, observer)
        projected = observer.finish()
        reports[path.path_id] = dict(projected, path_disposition=disposition, ensemble_id=path.ensemble_id,
            run_id=path.run_id, preparation_id=path.preparation_id, site_id=path.site_id, entry_history_id=path.entry_history_id,
            weight=path.weight.to_document(), configuration=config.identity.to_document(),
            integration_step_seconds=str(dynamics.step_seconds), coordinate_sha256s=tuple(digests),
            dynamics_model=ensemble.dynamics_model, bath_transport_dependence='UNEVALUABLE' if stochastic_path(config) else 'NO_BATH',
            original_result=ObjectIdentity.from_record(result.result_id,result).to_document() if result else None,
            original_receipt=result.receipt.to_document() if result else None,
            original_completion=result.completion.to_document() if result else None,
            original_cost=result.completion.cost.to_document() if result else None,
            original_trace_assessment=original)
        arrays[path.path_id+'.coordinates'] = coordinates[:used].copy()
        arrays[path.path_id+'.physical_steps'] = steps[:used].copy()
    statistics = summarize_first_passages(selection=selection, path_reports=reports)
    recheck_original_native_outputs(sources, description='first-passage analysis')
    for array in arrays.values():
        array.setflags(write=False)
    return dict(selection=selection.identity.to_document(), assessor_source=assessor_source.to_document(), capacity=capacity,
        path_census=reports, assigned_paths=len(selection.paths), supplied_results=sum(s.original_result is not None for s in sources),
        observed_events=sum(row['path_disposition']=='OBSERVED_EVENT' for row in reports.values()),
        horizon_censored_paths=sum(row['path_disposition']=='HORIZON_CENSORED' for row in reports.values()),
        dependence_basis=selection.dependence_basis.to_document(), dependence_assumptions=selection.assumptions,
        statistics=statistics, original_cost_scope='EACH_ORIGINAL_COMPLETION_AND_GPU_CALL_CENSUS_NO_DOUBLE_COUNTED_SUM',
        new_native_calls=0, new_reference_evaluations=0, evidence_scope=selection.scope), arrays
