# SPDX-License-Identifier: MPL-2.0
"""Authenticate a complete retained periodic return without native replay."""

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import periodic_geometry_policy
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import CHUNK_BYTES, RAW_MAGIC, _ChunkReader, uncompressed_archive_chunks
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledNumericalIntegrity, RawCoupledReturn, assess_native_return
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_native import force_probe_definition
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality_read import RetainedGeometryReader, RetainedMolecularGeometryAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import GRADIENT_UNIT, MAX_RETURN, PeriodicProbeNativeReturn, capability_for, definition_sources, is_restart, validate_force_selection, PeriodicProbeResult, probe_outputs, selected_request
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import OPEN_REQUIREMENTS
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class PeriodicProbeReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-probe-readout'
    VERSION: ClassVar[str] = '2.0.0'
    readout_id: str
    selection: ObjectIdentity
    original_result: PeriodicProbeResult
    numerical_integrity: CoupledNumericalIntegrity | None
    authenticated_file_count: int
    authenticated_uncompressed_file_bytes: int
    geometry_quality: RetainedMolecularGeometryAssessment
    remaining_requirement_ids: tuple[str, ...] = OPEN_REQUIREMENTS

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        exact(self.selection, ObjectIdentity)
        exact(self.original_result, PeriodicProbeResult)
        exact(self.geometry_quality, RetainedMolecularGeometryAssessment)
        result = self.original_result
        if (self.selection != result.returned.selection
                or self.geometry_quality.representation != result.request.prepared_material
                or self.geometry_quality.physical_atom_count != result.request.physical_atom_count
                or type(self.authenticated_file_count) is not int
                or self.authenticated_file_count != len(result.returned.files.files)
                or type(self.authenticated_uncompressed_file_bytes) is not int
                or self.authenticated_uncompressed_file_bytes != sum(r.byte_count for r in result.returned.files.files)
                or self.remaining_requirement_ids != OPEN_REQUIREMENTS):
            raise ValueError('periodic readout changes the original complete file census or physical limitations')
        raw = result.returned.returned
        if (raw is None) != (self.numerical_integrity is None):
            raise ValueError('periodic readout drops an actual captured return or invents one')
        if self.numerical_integrity is not None:
            exact(self.numerical_integrity, CoupledNumericalIntegrity)
            if (self.numerical_integrity.request != result.request.identity
                    or self.numerical_integrity.raw_return != ObjectIdentity.from_record(raw.return_id, raw)):
                raise ValueError('periodic readout substitutes the original raw operand assessment')


class _CompletedByteReader:
    """Bounded file interface over the existing authenticated output stream."""
    def __init__(self, chunks):
        self.chunks, self.pending, self.closed = iter(chunks), b'', False

    def read(self, size=-1):
        if self.closed:
            raise ValueError('completed periodic operand reader is closed')
        size = CHUNK_BYTES if size < 0 else min(size, CHUNK_BYTES)
        while len(self.pending) < size:
            block = next(self.chunks, None)
            if block is None:
                break
            self.pending += block
        result, self.pending = self.pending[:size], self.pending[size:]
        return result

    def close(self):
        self.closed = True
        close = getattr(self.chunks, 'close', None)
        if close is not None:
            close()


def authenticate_probe_files(native_subwork, definition, returned, *, member_validators=None):
    """Stream every original file, including diagnostics from known failures."""
    if sum(row.byte_count for row in returned.files.files) > 4*2**30:
        raise ValueError('periodic archive exceeds its selected complete output budget')
    chunks = native_subwork.iter_completed_output(definition, 'files.raw', maximum_chunk_bytes=CHUNK_BYTES)
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    validators = {} if member_validators is None else dict(member_validators)
    inspected = set()
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError('periodic archive changes its original framed-file format')
        size = int.from_bytes(reader.take(8), 'big')
        if not 0 < size <= 2**20:
            raise ValueError('periodic archive changes its bounded file-census metadata')
        header = reader.take(size)
        census = decode_canonical_bytes(header, DurableRawFileCensus, maximum_bytes=2**20)
        if (census != returned.files
                or header != b''.join(native_subwork.iter_completed_output(definition, 'files.census'))):
            raise ValueError('periodic archive substitutes the original complete file census')
        for row in census.files:
            path = PurePosixPath(row.relative_path)
            if path.parts != (definition.subwork_id, path.name):
                raise ValueError('periodic archive changes its original selected unit directory')
            validator = validators.get(path.name)
            if validator is not None and row.byte_count > validator[0]:
                raise ValueError('periodic inspected member exceeds its selected byte bound')
            retained = bytearray() if validator is not None else None
            remaining, digest = row.byte_count, sha256()
            while remaining:
                block = reader.take(min(remaining, CHUNK_BYTES))
                remaining -= len(block)
                digest.update(block)
                if retained is not None:
                    retained.extend(block)
            if digest.hexdigest() != row.sha256:
                raise ValueError('periodic archive changes an original complete file')
            if validator is not None:
                validator[1](bytes(retained))
                inspected.add(path.name)
        reader.finish()
        if inspected != set(validators):
            raise ValueError('periodic archive omits a selected original inspected member')
        return census
    finally:
        close = getattr(chunks, 'close', None)
        if close is not None:
            close()


def read_periodic_probe(*, config, representation, original_result, native_subwork,
                        assessor_source, readout_id):
    """Recheck original custody and complete finite arrays; measure no new force.

    Known failures retain their original status and all available operands.
    Missing or altered custody refuses. An unknown contact has no completed
    result and must use the existing native-subwork inspection route.
    """
    capability_for(config)
    exact(original_result, PeriodicProbeResult)
    exact(assessor_source, ObjectIdentity)
    validate_force_selection(config.selection, representation, config.seed if is_restart(config) else None)
    definition = original_result.definition
    expected = force_probe_definition(config.selection.probe, representation, config.provenance,
        parent_contact=definition.parent_contact, input_materialization_ids=definition.input_materialization_ids,
        gradient_unit=GRADIENT_UNIT)
    expected = replace(expected, outputs=probe_outputs(), sources=definition_sources(config, representation))
    if (definition != expected or original_result.request != selected_request(config)
            or original_result.returned.selection != config.selection.identity):
        raise ValueError('periodic retained read substitutes the original complete selected native call')
    if is_restart(config):
        files = {PurePosixPath(row.relative_path).name:row for row in original_result.returned.files.files}
        for name, size, digest in (
                ('initial-density-seed.json', config.seed.canonical_size_bytes(), config.seed.fingerprint()),
                ('initial-density.bin', config.seed.arrays.size_bytes, config.seed.density_bytes.object_fingerprint)):
            row = files.get(name)
            if (row is None and original_result.returned.error is None
                    or row is not None and (row.byte_count, row.sha256) != (size, digest)):
                raise ValueError('periodic restart return omits or changes its exact original density seed files')
    validators = None
    if config.ACCELERATED:
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import assess_gpu_log
        # A failed constructor can precede any diagnostic stream. Successful
        # returns must contain the actual complete GPU apparatus and cost.
        names = {PurePosixPath(row.relative_path).name for row in original_result.returned.files.files}
        if 'native-observations.jsonl' in names or original_result.returned.error is None:
            validators = {'native-observations.jsonl': (64*2**20, lambda raw: assess_gpu_log(
                raw, engine=config.selection.engine, successful=original_result.returned.error is None,
                expected_evaluations=1, state=getattr(config.selection.electronic, 'state', None)))}
    geometry_reader = RetainedGeometryReader(representation=representation, policy=periodic_geometry_policy(config.selection.molecular),
        cell=config.selection.cell, qm_atoms=config.selection.path.qm_atom_indices,
        expected_coordinate_sha256=config.selection.coordinates.members[0].sha256)
    return read_original_periodic_return(original_result=original_result, native_subwork=native_subwork,
        assessor_source=assessor_source, readout_id=readout_id, member_validators=validators, geometry_reader=geometry_reader)


def read_original_periodic_return(*, original_result, native_subwork, assessor_source, readout_id, geometry_reader, member_validators=None):
    """Shared custody assessment after the domain validates the exact definition."""
    exact(original_result, PeriodicProbeResult)
    exact(assessor_source, ObjectIdentity)
    definition = original_result.definition
    completed = native_subwork.recover(definition)
    if (completed is None or completed.completion != original_result.completion
            or completed.receipt != original_result.receipt):
        raise ValueError('periodic retained read loses original native completion or receipt')
    returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'probe.return')),
        PeriodicProbeNativeReturn, maximum_bytes=MAX_RETURN)
    if returned != original_result.returned:
        raise ValueError('periodic retained read substitutes its original captured return')
    census = authenticate_probe_files(native_subwork, definition, returned,
        member_validators=geometry_reader.validators(returned, member_validators))
    geometry_quality = geometry_reader.assess()
    integrity = None
    if returned.returned is not None:
        raw = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'raw.return')),
            RawCoupledReturn, maximum_bytes=MAX_RETURN)
        if raw != returned.returned:
            raise ValueError('periodic retained read substitutes its separately receipted raw return')
        selected = {row.artifact_manifest.materialization.materialization_id: ('raw.'+row.operand, row.artifact_manifest)
            for row in (raw.energy, raw.gradient) if row is not None}

        def reader_for_manifest(manifest):
            item = selected.get(manifest.materialization.materialization_id)
            if item is None or item[1] != manifest or manifest not in completed.outputs:
                raise ValueError('periodic retained operand reader substitutes original array custody')
            return _CompletedByteReader(native_subwork.iter_completed_output(definition, item[0],
                maximum_chunk_bytes=CHUNK_BYTES))

        integrity = assess_native_return(original_result.request, raw, reader_for_manifest,
            assessor_source=assessor_source)
    return PeriodicProbeReadout(readout_id, original_result.returned.selection, original_result, integrity,
        len(census.files), sum(row.byte_count for row in census.files), geometry_quality)
