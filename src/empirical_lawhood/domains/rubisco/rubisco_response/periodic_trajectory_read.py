# SPDX-License-Identifier: MPL-2.0
"""Authenticate every original trajectory file, then report independent trace checks."""

from hashlib import sha256
from pathlib import PurePosixPath
import traceback

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import CHUNK_BYTES, RAW_MAGIC, _ChunkReader, uncompressed_archive_chunks
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import MAX_CONFIG, MAX_RETURN
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_assessment import assess_recorded_trajectory, selected_trajectory_member
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import capability_for, ReferenceTrajectoryResult, ReferenceTrajectoryReturn, definition_for
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import read_phase_space, validate_trajectory_prototype


class TrajectoryCustodyError(ValueError):
    """An incomplete or changed original archive cannot produce a readout."""


def authenticate_trajectory_files(native_subwork, definition, returned, selection, prototype, *,
        select_member=selected_trajectory_member,
        large_json_members=frozenset(('prototype.json', 'trajectory-selection.json')),
        maximum_array_bytes=None):
    """Stream the complete original archive with at most one frame in memory.

    Every unselected byte is hashed too. The consumer must exhaust this iterator
    in a finally block, so an assessment error cannot omit later custody checks.
    """
    if maximum_array_bytes is not None and (type(maximum_array_bytes) is not int or maximum_array_bytes <= 0):
        raise ValueError('selected original arrays require an explicit positive read allocation')
    chunks = native_subwork.iter_completed_output(definition, 'files.raw', maximum_chunk_bytes=CHUNK_BYTES)
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    exceeded = []
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError('trajectory archive changes its original framed-file format')
        size = int.from_bytes(reader.take(8), 'big')
        if not 0 < size <= MAX_RETURN:
            raise ValueError('trajectory archive exceeds its selected metadata read envelope')
        header = reader.take(size)
        census = decode_canonical_bytes(header, DurableRawFileCensus, maximum_bytes=MAX_RETURN)
        if census != returned.files or header != b''.join(native_subwork.iter_completed_output(definition, 'files.census')):
            raise ValueError('trajectory archive substitutes its original complete file census')
        for row in census.files:
            path = PurePosixPath(row.relative_path)
            if path.parts != (definition.subwork_id, path.name):
                raise ValueError('trajectory archive changes its original selected native directory')
            keep = select_member(path.name)
            bound = (selection.arrays.size_bytes if maximum_array_bytes is None else maximum_array_bytes) + 1024
            if path.name.endswith('.json'):
                bound = MAX_CONFIG if path.name in large_json_members else 2**20
            if keep and row.byte_count > bound:
                exceeded.append(path.name)
                keep = False
            remaining, digest, parts = row.byte_count, sha256(), []
            while remaining:
                block = reader.take(min(remaining, CHUNK_BYTES))
                remaining -= len(block)
                digest.update(block)
                if keep:
                    parts.append(block)
            if digest.hexdigest() != row.sha256:
                raise ValueError('trajectory archive changes an original complete file')
            expected = {'original.prmtop':prototype.cell.raw_topology.object_fingerprint,
                'original.inpcrd':prototype.cell.raw_coordinates.object_fingerprint}.get(path.name)
            if expected is not None and row.sha256 != expected:
                raise ValueError('trajectory archive substitutes original Amber source bytes')
            yield path.name, b''.join(parts) if keep else None
        reader.finish()
        if exceeded:
            raise ValueError('original trajectory operands exceed the selected read-memory envelope: '+repr(exceeded))
    except (ValueError, OSError, EOFError) as error:
        raise TrajectoryCustodyError(str(error)) from error
    finally:
        close = getattr(chunks, 'close', None)
        if close is not None:
            close()


def read_reference_trajectory(*, config, representation, phase_bytes, original_result, native_subwork, assessor_source,
                              frame_consumer=None):
    """Read original receipts and complete bytes without a new native evaluation."""
    capability_for(config)
    exact(original_result, ReferenceTrajectoryResult)
    exact(assessor_source, ObjectIdentity)
    validate_trajectory_prototype(config.selection, config.original.selection)
    read_phase_space(config.selection, representation, phase_bytes)
    definition = original_result.definition
    if (definition != definition_for(config, parent=definition.parent_contact,
            materialization_ids=definition.input_materialization_ids)
            or original_result.returned.configuration != config.identity
            or original_result.returned.selection != config.selection.identity):
        raise ValueError('trajectory read substitutes its exact original native definition or selection')
    completed = native_subwork.recover(definition)
    if completed is None or completed.completion != original_result.completion or completed.receipt != original_result.receipt:
        raise ValueError('trajectory read loses original completion and receipt custody')
    returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'trajectory.return')),
        ReferenceTrajectoryReturn, maximum_bytes=MAX_RETURN)
    if returned != original_result.returned:
        raise ValueError('trajectory read substitutes its original receipted return')
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import GpuTraceAssessment, selected_gpu_member
    gpu = GpuTraceAssessment(config.original.selection.engine,
        state=getattr(config.original.selection.electronic, 'state', None)) if accelerated_engine(config.original.selection.engine) else None
    original_files = authenticate_trajectory_files(native_subwork, definition, returned, config.selection, config.original.selection,
        select_member=lambda n: selected_trajectory_member(n) or gpu is not None and selected_gpu_member(n))
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
            assessment = assess_recorded_trajectory(selection=config.selection, prototype=config.original.selection,
                representation=representation, phase_bytes=phase_bytes, files=files, native_succeeded=returned.error is None,
                frame_consumer=frame_consumer)
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
            gpu_assessment = gpu.finish(successful=returned.error is None, expected_evaluations=config.selection.settings.steps+1)
        except (ValueError, KeyError, TypeError, ArithmeticError):
            gpu_error = traceback.format_exc()
    return dict(gpu_assessment=gpu_assessment, gpu_assessment_error=gpu_error, configuration=config.identity.to_document(), selection=config.selection.identity.to_document(),
        original_result=ObjectIdentity.from_record(original_result.result_id, original_result).to_document(),
        assessor_source=assessor_source.to_document(), authenticated_file_count=len(returned.files.files),
        authenticated_uncompressed_bytes=sum(r.byte_count for r in returned.files.files),
        native_error=returned.error, assessment_error=error, assessment=assessment,
        new_operator_evaluations=0, initial_ensemble_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
