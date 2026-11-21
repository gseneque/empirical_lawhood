# SPDX-License-Identifier: MPL-2.0
"""Authenticate original equilibrium custody and reduce its stochastic trace."""

import traceback

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import MAX_RETURN
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_read import TrajectoryCustodyError, authenticate_trajectory_files
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_recorded import assess_recorded_equilibrium, selected_equilibrium_member
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import capability_for, ReferenceEquilibriumResult, ReferenceEquilibriumReturn, definition_for
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import read_equilibrium_phase_space, validate_equilibrium_prototype


def read_reference_equilibrium(*, config, representation, phase_bytes, original_result, native_subwork, assessor_source,
                              bias_geometry_criteria=None, sample_consumer=None, frame_consumer=None, verify_random_stream=False):
    """Read original receipts and complete bytes without a new native evaluation."""
    capability_for(config)
    exact(original_result, ReferenceEquilibriumResult)
    exact(assessor_source, ObjectIdentity)
    if bias_geometry_criteria is not None:
        exact(bias_geometry_criteria, ReferenceBiasGeometryCriteria)
    validate_equilibrium_prototype(config.selection, config.original.selection)
    read_equilibrium_phase_space(config.selection, representation, phase_bytes)
    definition = original_result.definition
    if (definition != definition_for(config, parent=definition.parent_contact,
            materialization_ids=definition.input_materialization_ids)
            or original_result.returned.configuration != config.identity
            or original_result.returned.selection != config.selection.identity):
        raise ValueError('equilibrium read substitutes its exact original native definition or selection')
    completed = native_subwork.recover(definition)
    if completed is None or completed.completion != original_result.completion or completed.receipt != original_result.receipt:
        raise ValueError('equilibrium read loses original completion and receipt custody')
    returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'equilibrium.return')),
        ReferenceEquilibriumReturn, maximum_bytes=MAX_RETURN)
    if returned != original_result.returned:
        raise ValueError('equilibrium read substitutes its original receipted return')
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import GpuTraceAssessment, selected_gpu_member
    gpu = GpuTraceAssessment(config.original.selection.engine,
        state=getattr(config.original.selection.electronic, 'state', None)) if accelerated_engine(config.original.selection.engine) else None
    original_files = authenticate_trajectory_files(native_subwork, definition, returned, config.selection, config.original.selection,
        select_member=lambda n: selected_equilibrium_member(n) or gpu is not None and selected_gpu_member(n),
        large_json_members=frozenset(('prototype.json', 'equilibrium-selection.json')))
    gpu_error = None
    def selected_files():
        nonlocal gpu_error
        for name, raw in original_files:
            if gpu is not None and gpu_error is None:
                try:
                    gpu.consume(name, raw)
                except (ValueError, KeyError, TypeError, ArithmeticError):
                    gpu_error = traceback.format_exc()
            yield name, raw
    files = selected_files()
    assessment, error = None, None
    try:
        try:
            assessment = assess_recorded_equilibrium(selection=config.selection, prototype=config.original.selection,
                representation=representation, phase_bytes=phase_bytes, files=files, native_succeeded=returned.error is None,
                bias_geometry_criteria=bias_geometry_criteria, sample_consumer=sample_consumer,
                frame_consumer=frame_consumer, verify_random_stream=verify_random_stream)
        except TrajectoryCustodyError:
            raise
        except (ValueError, KeyError, TypeError, ArithmeticError, EOFError):
            error = traceback.format_exc()
    finally:
        # Even a rejected first frame cannot hide a later corrupted source,
        # failed attempt, full atom array, or undeclared archive trailer.
        for _ in files:
            pass
        files.close()
        original_files.close()
    gpu_assessment = None
    if gpu is not None and gpu_error is None:
        try:
            gpu_assessment = gpu.finish(successful=returned.error is None, expected_evaluations=config.selection.settings.dynamics.steps+1)
        except (ValueError, KeyError, TypeError, ArithmeticError):
            gpu_error = traceback.format_exc()
    return dict(gpu_assessment=gpu_assessment, gpu_assessment_error=gpu_error, configuration=config.identity.to_document(), selection=config.selection.identity.to_document(),
        original_result=ObjectIdentity.from_record(original_result.result_id, original_result).to_document(),
        assessor_source=assessor_source.to_document(), authenticated_file_count=len(returned.files.files),
        bias_geometry_criteria=bias_geometry_criteria.to_document() if bias_geometry_criteria is not None else None,
        authenticated_uncompressed_bytes=sum(r.byte_count for r in returned.files.files),
        native_error=returned.error, assessment_error=error, assessment=assessment,
        new_operator_evaluations=0, initial_ensemble_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
