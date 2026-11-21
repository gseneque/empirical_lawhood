# SPDX-License-Identifier: MPL-2.0
"""Complete retained relaxation custody and independent endpoint assessment."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import CHUNK_BYTES, RAW_MAGIC, _ChunkReader, uncompressed_archive_chunks
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_assessment import ActiveRelaxationAssessment, assess_active_endpoint
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import ActiveRelaxationResult, ActiveRelaxationReturn, ConditionalActiveRelaxationResult, MAX_RETURN, conditional_configuration, definition_for, selected_seeds
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ConditionalActiveRelaxationSelection, MODEL_NAMES, MatchedActiveRelaxationPlan, validate_conditional_relaxation_selection, validate_relaxation_member
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import verified_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model


ENDPOINT_MEMBERS = frozenset(('seed.json', 'site.json', 'protocol.json', 'settings.json', 'source-bindings.json',
    'original.prmtop', 'initial-whole-molecule-quality.json',
    'initial-coordinates-angstrom.npy', 'final-coordinates-angstrom.npy', 'final-gradient-hartree-per-bohr.npy',
    'final-energy-hartree.npy', 'relaxation-summary.json', 'relaxation-evaluations.jsonl', 'native-observations.jsonl'))
MAX_ENDPOINT_MEMORY_BYTES = 256*2**20


@dataclass(frozen=True, slots=True)
class ActiveEndpointReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-endpoint-readout'
    seed: ObjectIdentity
    native_return: ObjectIdentity
    authenticated_file_count: int
    authenticated_uncompressed_bytes: int
    native_error: str | None
    assessment: ActiveRelaxationAssessment | None
    assessment_error: str | None

    def __post_init__(self):
        exact(self.seed, ObjectIdentity)
        exact(self.native_return, ObjectIdentity)
        if any(type(n) is not int or n < 0 for n in (self.authenticated_file_count, self.authenticated_uncompressed_bytes)):
            raise ValueError('endpoint readout loses its authenticated complete file census')
        for value in (self.native_error, self.assessment_error):
            if value is not None and (type(value) is not str or not value):
                raise ValueError('endpoint readout loses its actual failure diagnostic')
        if (sum(x is not None for x in (self.native_error, self.assessment, self.assessment_error)) != 1):
            raise ValueError('endpoint readout must retain one actual native failure or independent assessment outcome')
        if self.assessment is not None:
            exact(self.assessment, ActiveRelaxationAssessment)
            if self.assessment.seed != self.seed:
                raise ValueError('endpoint readout substitutes its independently assessed state')


@dataclass(frozen=True, slots=True)
class ActiveRelaxationReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-readout'
    readout_id: str
    original_result: ActiveRelaxationResult
    state_census: tuple[tuple[str, str, str], ...]
    endpoints: tuple[ActiveEndpointReadout, ...]
    interpretation: str = 'STATIONARY_ENDPOINTS_WITHOUT_EQUILIBRIUM_POPULATIONS_FORCE_ACCURACY_OR_PHYSICAL_RATES'

    def __post_init__(self):
        _validate_readout(self, ActiveRelaxationResult, 96,
            'STATIONARY_ENDPOINTS_WITHOUT_EQUILIBRIUM_POPULATIONS_FORCE_ACCURACY_OR_PHYSICAL_RATES')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.readout_id, self)


@dataclass(frozen=True, slots=True)
class ConditionalActiveRelaxationReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/conditional-active-relaxation-readout'
    readout_id: str
    original_result: ConditionalActiveRelaxationResult
    state_census: tuple[tuple[str, str, str], ...]
    endpoints: tuple[ActiveEndpointReadout, ...]
    interpretation: str = 'CONDITIONAL_STATIONARY_ENDPOINTS_UNSELECTED_STATES_UNMEASURED_NO_POPULATIONS_OR_RATES'

    def __post_init__(self):
        exact(self.original_result, ConditionalActiveRelaxationResult)
        _validate_readout(self, ConditionalActiveRelaxationResult, len(self.original_result.selection.state_census),
            'CONDITIONAL_STATIONARY_ENDPOINTS_UNSELECTED_STATES_UNMEASURED_NO_POPULATIONS_OR_RATES')
        if not set(self.original_result.selection.state_census).issubset(self.state_census):
            raise ValueError('conditional readout substitutes its selected state membership')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.readout_id, self)


def _validate_readout(record, result_kind, selected_count, interpretation):
    validate_stable_id(record.readout_id)
    exact(record.original_result, result_kind)
    if (type(record.endpoints) is not tuple or len(record.endpoints) != selected_count
            or type(record.state_census) is not tuple or len(record.state_census) != 96
            or record.state_census != tuple(sorted(set(record.state_census)))
            or record.interpretation != interpretation):
        raise ValueError('relaxation readout changes its complete denominator or scientific scope')
    for endpoint, unit in zip(record.endpoints, record.original_result.units, strict=True):
        exact(endpoint, ActiveEndpointReadout)
        expected = ObjectIdentity.from_record(unit.definition.subwork_id+'.return', unit.returned)
        if (endpoint.seed != unit.returned.seed or endpoint.native_return != expected
                or endpoint.native_error != unit.returned.error
                or endpoint.authenticated_file_count != len(unit.returned.files.files)
                or endpoint.authenticated_uncompressed_bytes != sum(r.byte_count for r in unit.returned.files.files)):
            raise ValueError('relaxation readout changes an original native attempt or authenticated file')


def authenticate_relaxation_files(native_subwork, definition, returned, *,
        endpoint_members=ENDPOINT_MEMBERS, maximum_endpoint_bytes=None,
        retain_failed_members=False):
    """Hash the entire original archive, even on native or endpoint failures."""
    chunks = native_subwork.iter_completed_output(definition, 'files.raw', maximum_chunk_bytes=CHUNK_BYTES)
    try:
        census_bytes = b''.join(native_subwork.iter_completed_output(definition, 'files.census'))
        return authenticate_relaxation_archive(chunks, definition, returned, census_bytes,
            endpoint_members=endpoint_members, maximum_endpoint_bytes=maximum_endpoint_bytes,
            retain_failed_members=retain_failed_members)
    finally:
        close = getattr(chunks, 'close', None)
        if close is not None:
            close()


def authenticate_relaxation_archive(chunks, definition, returned, census_bytes, *,
        endpoint_members=ENDPOINT_MEMBERS, maximum_endpoint_bytes=None,
        retain_failed_members=False):
    """Validate a complete archive already bound to its original receipt or input."""
    if (type(endpoint_members) is not frozenset or not endpoint_members
            or any(type(name) is not str or PurePosixPath(name).parts != (name,) for name in endpoint_members)
            or maximum_endpoint_bytes is not None and (type(maximum_endpoint_bytes) is not int or maximum_endpoint_bytes <= 0)
            or type(retain_failed_members) is not bool):
        raise ValueError('relaxation archive requires an explicit bounded endpoint member selection')
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError('relaxation archive changes its original framed-file format')
        size = int.from_bytes(reader.take(8), 'big')
        if size != len(census_bytes) or size <= 0:
            raise ValueError('relaxation archive changes its exact authenticated file-census size')
        header = reader.take(size)
        census = decode_canonical_bytes(header, DurableRawFileCensus, maximum_bytes=len(census_bytes))
        if census != returned.files or header != census_bytes:
            raise ValueError('relaxation archive substitutes its original complete file census')
        selected_bytes = sum(row.byte_count for row in census.files if PurePosixPath(row.relative_path).name in endpoint_members)
        exceeds = maximum_endpoint_bytes is not None and selected_bytes > maximum_endpoint_bytes
        files = {}
        for row in census.files:
            path = PurePosixPath(row.relative_path)
            if path.parts != (definition.subwork_id, path.name):
                raise ValueError('relaxation archive changes its original selected state directory')
            remaining, digest, parts = row.byte_count, sha256(), []
            keep = (returned.error is None or retain_failed_members) and not exceeds and path.name in endpoint_members
            while remaining:
                block = reader.take(min(remaining, CHUNK_BYTES))
                remaining -= len(block)
                digest.update(block)
                if keep:
                    parts.append(block)
            if digest.hexdigest() != row.sha256:
                raise ValueError('relaxation archive changes an original complete file')
            if keep:
                files[path.name] = b''.join(parts)
        reader.finish()
        return files, census, exceeds
    finally:
        close = getattr(chunks, 'close', None)
        if close is not None:
            close()


def read_relaxation(*, config, representation, prepared, coordinate_bytes, original_result,
                    native_subwork, assessor_source, readout_id):
    """Recheck all original receipts and bytes without constructing or relaxing states."""
    conditional = conditional_configuration(config)
    exact(original_result, ConditionalActiveRelaxationResult if conditional else ActiveRelaxationResult)
    if conditional and original_result.selection != config.selection:
        raise ValueError('conditional relaxation read changes its original selected scenario')
    exact(assessor_source, ObjectIdentity)
    validate_periodic_probe_model(config.prototype, representation)
    validate_relaxation_member(plan=config.plan, model_name=config.model_name, prepared=prepared,
        prototype=config.prototype, representation=representation)
    verified_coordinates(representation, coordinate_bytes)
    if (original_result.configuration != config.identity or original_result.plan != config.plan.identity
            or original_result.model_name != config.model_name):
        raise ValueError('relaxation read substitutes its original matched configuration')
    seeds = {s.identity:s for s in prepared.seeds}
    sites = {s.identity:s for s in prepared.sites}
    if {u.returned.seed for u in original_result.units} != {s.identity for s in selected_seeds(config, prepared)}:
        raise ValueError('relaxation read omits an original selected starting state')
    endpoints = []
    for unit in original_result.units:
        definition, seed = unit.definition, seeds[unit.returned.seed]
        expected = definition_for(config, prepared, seed, parent=definition.parent_contact,
            materialization_ids=definition.input_materialization_ids)
        if definition != expected:
            raise ValueError('relaxation read changes its exact original native definition')
        completed = native_subwork.recover(definition)
        if completed is None or completed.completion != unit.completion or completed.receipt != unit.receipt:
            raise ValueError('relaxation read loses original completion and receipt custody')
        returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'relaxation.return')),
            ActiveRelaxationReturn, maximum_bytes=MAX_RETURN)
        if returned != unit.returned:
            raise ValueError('relaxation read substitutes its original receipted return')
        files, census, exceeds = authenticate_relaxation_files(native_subwork, definition, returned)
        assessment, error = None, None
        if returned.error is None:
            try:
                if exceeds:
                    raise ValueError('original endpoint files exceed the selected 256 MiB in-memory assessment envelope; full archive authenticated and retained')
                if set(files) != ENDPOINT_MEMBERS:
                    raise ValueError('original native return lacks complete endpoint operands: '+repr(sorted(ENDPOINT_MEMBERS-set(files))))
                assessment = assess_active_endpoint(representation=representation, prototype=config.prototype,
                    prepared=prepared, site=sites[seed.site], seed=seed, settings=config.plan.settings,
                    coordinate_bytes=coordinate_bytes, files=files, assessor_source=assessor_source)
            except (ValueError, KeyError, TypeError, ArithmeticError, EOFError):
                error = traceback.format_exc()
        endpoints.append(ActiveEndpointReadout(seed.identity, ObjectIdentity.from_record(definition.subwork_id+'.return', returned),
            len(census.files), sum(row.byte_count for row in census.files), returned.error, assessment, error))
    census = next(m.state_census for m in config.plan.members if m.model_name == config.model_name)
    kind = ConditionalActiveRelaxationReadout if conditional else ActiveRelaxationReadout
    return kind(readout_id, original_result, census, tuple(endpoints))


@dataclass(frozen=True, slots=True)
class MatchedRelaxationMemberReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/matched-relaxation-member-readout'
    model_name: str
    readout: ObjectIdentity
    stationary_state_retained: int
    endpoint_rejected: int
    endpoint_unevaluable: int
    native_failed: int

    def __post_init__(self):
        exact(self.readout, ObjectIdentity)
        counts = (self.stationary_state_retained, self.endpoint_rejected, self.endpoint_unevaluable, self.native_failed)
        if self.model_name not in MODEL_NAMES or any(type(n) is not int or n < 0 for n in counts) or sum(counts) != 96:
            raise ValueError('matched readout drops a selected endpoint, failed attempt or missing assessment')


@dataclass(frozen=True, slots=True)
class MatchedActiveRelaxationReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/matched-active-relaxation-readout'
    plan: ObjectIdentity
    members: tuple[MatchedRelaxationMemberReadout, ...]
    original_biological_units: int = 1
    equilibrium_populations: str = 'UNEVALUABLE'
    turnover_contrast: str = 'UNEVALUABLE'
    specificity_contrast: str = 'UNEVALUABLE'

    def __post_init__(self):
        exact(self.plan, ObjectIdentity)
        if (type(self.members) is not tuple or tuple(m.model_name for m in self.members) != MODEL_NAMES
                or type(self.original_biological_units) is not int or self.original_biological_units != 1
                or any(getattr(self, n) != 'UNEVALUABLE' for n in ('equilibrium_populations', 'turnover_contrast', 'specificity_contrast'))):
            raise ValueError('matched relaxation cannot add replication, state weights or kinetic contrasts')
        for member in self.members:
            exact(member, MatchedRelaxationMemberReadout)


@dataclass(frozen=True, slots=True)
class ConditionalMatchedRelaxationMemberReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/conditional-matched-relaxation-member-readout'
    model_name: str
    readout: ObjectIdentity
    stationary_state_retained: int
    endpoint_rejected: int
    endpoint_unevaluable: int
    native_failed: int
    states_not_selected: int

    def __post_init__(self):
        exact(self.readout, ObjectIdentity)
        counts = (self.stationary_state_retained, self.endpoint_rejected, self.endpoint_unevaluable,
            self.native_failed, self.states_not_selected)
        if (self.model_name not in MODEL_NAMES or any(type(n) is not int or n < 0 for n in counts)
                or sum(counts) != 96 or self.states_not_selected >= 96
                or self.readout.object_schema != ConditionalActiveRelaxationReadout.SCHEMA):
            raise ValueError('conditional matched readout loses selected outcomes or unmeasured alternatives')


@dataclass(frozen=True, slots=True)
class ConditionalMatchedActiveRelaxationReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/conditional-matched-active-relaxation-readout'
    plan: ObjectIdentity
    selection: ConditionalActiveRelaxationSelection
    members: tuple[ConditionalMatchedRelaxationMemberReadout, ...]
    original_biological_units: int = 1
    equilibrium_populations: str = 'UNEVALUABLE'
    turnover_contrast: str = 'UNEVALUABLE'
    specificity_contrast: str = 'UNEVALUABLE'

    def __post_init__(self):
        exact(self.plan, ObjectIdentity)
        exact(self.selection, ConditionalActiveRelaxationSelection)
        if (self.selection.plan != self.plan or type(self.members) is not tuple
                or tuple(m.model_name for m in self.members) != MODEL_NAMES
                or type(self.original_biological_units) is not int or self.original_biological_units != 1
                or any(getattr(self, n) != 'UNEVALUABLE' for n in ('equilibrium_populations', 'turnover_contrast', 'specificity_contrast'))):
            raise ValueError('conditional matched relaxation cannot add replication, state weights or kinetic contrasts')
        for member in self.members:
            exact(member, ConditionalMatchedRelaxationMemberReadout)
            if member.states_not_selected != 96-len(self.selection.state_census):
                raise ValueError('conditional matched relaxation loses its complete unmeasured-state denominator')


def assess_matched_readouts(*, plan, readouts, conditional_selection=None):
    exact(plan, MatchedActiveRelaxationPlan)
    conditional = conditional_selection is not None
    if conditional:
        validate_conditional_relaxation_selection(plan, conditional_selection)
    if type(readouts) is not tuple or len(readouts) != 4:
        raise ValueError('matched relaxation assessment requires all four original member readouts')
    for report in readouts:
        exact(report, ConditionalActiveRelaxationReadout if conditional else ActiveRelaxationReadout)
        if conditional and report.original_result.selection != conditional_selection:
            raise ValueError('conditional matched readout changes its shared original selection')
    selected = tuple(sorted(readouts, key=lambda r:r.original_result.model_name))
    if tuple(r.original_result.model_name for r in selected) != MODEL_NAMES:
        raise ValueError('matched relaxation assessment duplicates or omits a model')
    members = []
    for report, member in zip(selected, plan.members, strict=True):
        pins = {plan.identity, member.preparation, member.prototype, member.representation,
            *((conditional_selection.identity,) if conditional else ())}
        if (report.original_result.plan != plan.identity or report.state_census != member.state_census
                or any(not pins.issubset(unit.definition.sources) for unit in report.original_result.units)):
            raise ValueError('matched relaxation assessment changes the shared original plan or state denominator')
        rows = report.endpoints
        kind = ConditionalMatchedRelaxationMemberReadout if conditional else MatchedRelaxationMemberReadout
        extra = {'states_not_selected':96-len(rows)} if conditional else {}
        members.append(kind(member.model_name, report.identity,
            sum(r.assessment is not None and r.assessment.disposition == 'SATISFIED' for r in rows),
            sum(r.assessment is not None and r.assessment.disposition == 'FALSIFIED' for r in rows),
            sum(r.assessment_error is not None for r in rows), sum(r.native_error is not None for r in rows), **extra))
    if conditional:
        return ConditionalMatchedActiveRelaxationReadout(plan.identity, conditional_selection, tuple(members))
    return MatchedActiveRelaxationReadout(plan.identity, tuple(members))
