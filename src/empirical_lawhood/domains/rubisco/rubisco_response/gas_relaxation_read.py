# SPDX-License-Identifier: MPL-2.0
"""Authenticated original gas-start results without native replay or state repair."""

from dataclasses import dataclass
import traceback
from typing import ClassVar

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_read import authenticate_relaxation_files
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_assessment import GasRelaxationAssessment, assess_gas_relaxation_endpoint
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_operation import GasRelaxationResult, GasRelaxationReturn, MAX_RETURN, capability_for, definition_for
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_selection import validate_gas_relaxation_model
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


ENDPOINT_MEMBERS = frozenset(('gas-selection.json', 'source-bindings.json', 'initial-coordinates-angstrom.npy',
    'final-coordinates-angstrom.npy', 'final-gradient-hartree-per-bohr.npy', 'final-energy-hartree.npy',
    'relaxation-summary.json', 'relaxation-evaluations.jsonl', 'native-observations.jsonl'))


@dataclass(frozen=True, slots=True)
class GasRelaxationReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-relaxation-readout'
    readout_id: str
    original_result: GasRelaxationResult
    authenticated_file_count: int
    authenticated_uncompressed_bytes: int
    assessment: GasRelaxationAssessment | None
    assessment_error: str | None
    interpretation: str = 'NUMERICAL_ENDPOINT_AND_GEOMETRY_WITHOUT_GAS_BASIN_ELECTRONIC_POPULATION_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        exact(self.original_result, GasRelaxationResult)
        returned = self.original_result.returned
        if (any(type(n) is not int or n < 0 for n in (self.authenticated_file_count, self.authenticated_uncompressed_bytes))
                or self.authenticated_file_count != len(returned.files.files)
                or self.authenticated_uncompressed_bytes != sum(row.byte_count for row in returned.files.files)
                or sum(x is not None for x in (returned.error, self.assessment, self.assessment_error)) != 1
                or self.assessment_error is not None and (type(self.assessment_error) is not str or not self.assessment_error)
                or self.interpretation != 'NUMERICAL_ENDPOINT_AND_GEOMETRY_WITHOUT_GAS_BASIN_ELECTRONIC_POPULATION_OR_RATE_ADMISSION'):
            raise ValueError('gas readout loses original files, failure or its independent assessment scope')
        if self.assessment is not None:
            exact(self.assessment, GasRelaxationAssessment)
            if self.assessment.selection != returned.selection:
                raise ValueError('gas readout substitutes the independently assessed original selection')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.readout_id, self)


def read_relaxation(*, config, representation, original_result, native_subwork, assessor_source, readout_id):
    """Authenticate every original member before reporting success, failure or findings."""
    capability_for(config)
    exact(original_result, GasRelaxationResult)
    exact(assessor_source, ObjectIdentity)
    validate_gas_relaxation_model(config.selection, representation)
    if (original_result.returned.configuration != config.identity
            or original_result.returned.selection != config.selection.identity):
        raise ValueError('gas relaxation read substitutes its original selected configuration')
    definition = original_result.definition
    if definition != definition_for(config, parent=definition.parent_contact, materialization_ids=definition.input_materialization_ids):
        raise ValueError('gas relaxation read changes its exact original native definition')
    completed = native_subwork.recover(definition)
    if (completed is None or completed.completion != original_result.completion or completed.receipt != original_result.receipt):
        raise ValueError('gas relaxation read loses original completion and receipt custody')
    returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'gas-relaxation.return')),
        GasRelaxationReturn, maximum_bytes=MAX_RETURN)
    if returned != original_result.returned:
        raise ValueError('gas relaxation read substitutes its original receipted return')
    files, census, exceeds = authenticate_relaxation_files(native_subwork, definition, returned, endpoint_members=ENDPOINT_MEMBERS)
    assessment, error = None, None
    if returned.error is None:
        try:
            if exceeds:
                raise ValueError('original gas endpoint exceeds the selected 256 MiB assessment envelope; complete archive authenticated and retained')
            if set(files) != ENDPOINT_MEMBERS:
                raise ValueError('original gas endpoint lacks complete operands: '+repr(sorted(ENDPOINT_MEMBERS-set(files))))
            assessment = assess_gas_relaxation_endpoint(selection=config.selection, representation=representation,
                files=files, assessor_source=assessor_source)
        except (ValueError, KeyError, TypeError, ArithmeticError, EOFError):
            error = traceback.format_exc()
    return GasRelaxationReadout(readout_id, original_result, len(census.files),
        sum(row.byte_count for row in census.files), assessment, error)
