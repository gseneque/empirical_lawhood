# SPDX-License-Identifier: MPL-2.0
"""Shared prospective exports consumed by the existing public campaign API."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from functools import partial
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar
import json

from empirical_lawhood.api.authoring_handoff import create_authoring_api, preflight_authoring_output_directory, read_authoring_source_companion, resolve_authoring_directory
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher, ExternalContentAddressedInputResolver
from empirical_lawhood.infrastructure.recursive_prospective_inputs import RecursiveContentInputSupplier
from empirical_lawhood.infrastructure.source_closure import AdmittedTargetSource, CapturedTargetClosure, capture_target_closure
from empirical_lawhood.infrastructure.selected_candidate import canonical_source_metadata_bytes
from empirical_lawhood.infrastructure.source_policy import (
    CheckoutSourceAdmission, InstalledSourceAdmission, LocalPlanDisclosure, require_unchanged_source_admission,
)
from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_entry import ExecutableStudyDefinition, ProposedStudyExtensionSet, StudyDefinition
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SelectedSourceManifest, SourceClosureKind
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, canonical_json_document_bytes, validate_relative_locator, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, artifact_custody_limits
from empirical_lawhood.runtime.compiler import compile_preissue_run_plan, lower_run_plan
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort, LayeredCampaignRuntimeProviderResolver
from empirical_lawhood.runtime.input_payloads import InputBytes
from empirical_lawhood.runtime.progress import report_progress
from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_prospective import DRAFT128_RECURSIVE_SELECTION_DECODER_KEY, DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES, LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES, LARGE_RECURSIVE_RETAINED_MEMBER_MAXIMUM_BYTES, RecursiveCandidateContextProvider, RecursiveProspectiveAuthoringSpec, RecursiveProspectiveCandidatePreview, RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
from empirical_lawhood.runtime.recursive_prospective_envelope import (
    MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES, MAXIMUM_OPERATIONAL_ENVELOPE_BYTES, MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES,
    RecursiveProspectiveAuthoringEnvelope, RecursiveProspectiveAuthoringEnvelopeV3, RecursiveProspectiveAuthoringEnvelopeV4,
)
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort, recursive_input_port_key
from empirical_lawhood.runtime.recursive_record_codecs import validate_declared_recursive_input_payload
from empirical_lawhood.runtime.source_resolution import CandidateSourceResolutionService

MAXIMUM_SPEC_BYTES = 16 * 1024**2
SOURCE_PROVENANCE_MEMBERS = ('selected-source-manifest.json', 'source-observation.json')


@dataclass(frozen=True, slots=True)
class ProspectiveSourceObservation(CanonicalRecord):
    """Operational disclosure beside the unchanged closed scientific packet."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/operational/prospective-source-observation'
    record_id: str
    closure: ObjectIdentity
    selected_manifest: ObjectIdentity
    source_observation_json: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.closure) is not ObjectIdentity or self.closure.object_schema != ImplementationSourceClosure.SCHEMA
                or type(self.selected_manifest) is not ObjectIdentity or self.selected_manifest.object_schema != SelectedSourceManifest.SCHEMA
                or type(self.source_observation_json) is not str):
            raise ValueError('prospective source disclosure requires exact closure/manifest references and canonical operational JSON')
        value = json.loads(self.source_observation_json)
        if type(value) is not dict or canonical_json_document_bytes(value).decode() != self.source_observation_json:
            raise ValueError('prospective source disclosure is not its exact canonical operational JSON')
        if set(value) != {'implementation_commit', 'implementation_sha256', 'source_tree_sha256', 'tracked_files',
                'source_admission', 'final_source_admission'}:
            raise ValueError('prospective source disclosure changes its complete original operational observation')
        for key in ('source_admission', 'final_source_admission'):
            admission = value[key]
            if type(admission) is dict and admission.get('policy') == 'installed-candidate-v1':
                if (set(admission) != {'policy', 'source_metadata_sha256', 'selected_paths',
                        'checkout_observed', 'observed_checkout_clean'}
                        or admission['checkout_observed'] is not False
                        or admission['observed_checkout_clean'] is not False
                        or type(admission['selected_paths']) is not list):
                    raise ValueError('installed source disclosure cannot report Git observations or extra fields')
                InstalledSourceAdmission(admission['source_metadata_sha256'], tuple(admission['selected_paths']))
                continue
            if (type(admission) is not dict or set(admission) != {'policy', 'raw_status_sha256', 'observed_checkout_clean',
                    'changes', 'selected_paths', 'selected_path_changes', 'local_plan'}
                    or admission['policy'] != 'selected-source-identities-v1'
                    or type(admission.get('observed_checkout_clean')) is not bool
                    or type(admission['changes']) is not list or type(admission['selected_paths']) is not list
                    or type(admission['selected_path_changes']) is not list
                    or admission.get('observed_checkout_clean') != (not admission.get('changes'))):
                raise ValueError('prospective source disclosure falsely reports raw Git cleanliness')
            validate_sha256(admission['raw_status_sha256'])
            selected = tuple(admission['selected_paths'])
            if selected != tuple(sorted(set(selected))):
                raise ValueError('prospective source disclosure repeats or reorders its selected paths')
            for path in selected:
                validate_relative_locator(path)
            for row in admission['changes']:
                if (type(row) is not dict or set(row) != {'status', 'relative_path', 'original_path'}
                        or type(row['status']) is not str or len(row['status']) != 2):
                    raise ValueError('prospective source disclosure changes its original checkout change census')
                validate_relative_locator(row['relative_path'])
                if row['original_path'] is not None:
                    validate_relative_locator(row['original_path'])
            if admission['selected_path_changes'] != [row for row in admission['changes']
                    if row['relative_path'] in selected or row['original_path'] in selected]:
                raise ValueError('prospective source disclosure changes its selected-path diagnostics')
            if admission['local_plan'] is not None:
                LocalPlanDisclosure(**admission['local_plan'])
        initial, final = value['source_admission'], value['final_source_admission']
        if initial['policy'] != final['policy']:
            raise ValueError('prospective source disclosure mixes source-admission policies')
        if initial['policy'] == 'installed-candidate-v1' and initial != final:
            raise ValueError('installed source disclosure changes its admitted metadata or selected paths')
        files = value['tracked_files']
        if (type(files) is not list or not files or any(type(row) is not dict
                or set(row) != {'relative_path', 'mode', 'size_bytes', 'sha256'} for row in files)
                or tuple(row['relative_path'] for row in files) != tuple(sorted({row['relative_path'] for row in files}))):
            raise ValueError('prospective source disclosure changes its complete committed file census')
        for row in files:
            validate_relative_locator(row['relative_path'])
            validate_sha256(row['sha256'])
            if (row['mode'] not in ('100644', '100755', '120000')
                    or type(row['size_bytes']) is not int or row['size_bytes'] < 0):
                raise ValueError('prospective source disclosure changes an original committed file identity')
        if initial['policy'] == 'installed-candidate-v1':
            head = value['implementation_commit']
            if (type(head) is not str or len(head) != 40 or any(char not in '0123456789abcdef' for char in head)
                    or not {'pyproject.toml', 'uv.lock'} <= {row['relative_path'] for row in files}):
                raise ValueError('installed source disclosure omits its complete build-source identity')
            validate_sha256(value['implementation_sha256'])
            validate_sha256(value['source_tree_sha256'])
            if any(row['mode'] not in ('100644', '100755') for row in files):
                raise ValueError('installed source disclosure contains a nonregular build-source member')
            metadata = canonical_source_metadata_bytes(implementation_commit=value['implementation_commit'],
                implementation_sha256=value['implementation_sha256'], source_tree_sha256=value['source_tree_sha256'],
                tracked_files=files)
            if sha256(metadata).hexdigest() != initial['source_metadata_sha256']:
                raise ValueError('installed source disclosure substitutes its original build-source metadata')


def _source_reference(closure):
    return ObjectIdentity.from_record(closure.source_closure_id, closure)


def _capture_prospective_source(project_root, closure_id, *, retained_closure=None, artifact_writer=None):
    captured = capture_target_closure(Path(project_root), closure_id)
    if type(captured) is not CapturedTargetClosure:
        raise TypeError('prospective source capture requires its exact closure, manifest and operational observation')
    if (type(captured.source) is not AdmittedTargetSource or type(captured.closure) is not ImplementationSourceClosure
            or type(captured.manifest) is not SelectedSourceManifest
            or captured.closure.kind is not SourceClosureKind.EXACT_SOURCE_CLOSURE
            or captured.closure.source_closure_id != closure_id
            or captured.closure.exact_source_manifest != captured.manifest.identity
            or type(captured.source.source_admission) not in (CheckoutSourceAdmission, InstalledSourceAdmission)
            or type(captured.source.final_source_admission) is not type(captured.source.source_admission)
            or captured.closure.clean_worktree != captured.source.final_source_admission.observed_checkout_clean):
        raise ValueError('prospective source capture loses its exact typed source identity and truthful final observation')
    require_unchanged_source_admission(captured.source.source_admission, captured.source.final_source_admission)
    _validate_source_disclosure(captured.closure, captured.manifest, captured.source.to_mapping())
    if retained_closure is not None:
        if (type(retained_closure) is not ImplementationSourceClosure
                or retained_closure.kind is not SourceClosureKind.EXACT_SOURCE_CLOSURE
                or (retained_closure.source_closure_id, retained_closure.implementation_commit,
                    retained_closure.implementation_sha256, retained_closure.source_tree_sha256, retained_closure.exact_source_manifest)
                    != (captured.closure.source_closure_id, captured.closure.implementation_commit,
                        captured.closure.implementation_sha256, captured.closure.source_tree_sha256, captured.manifest.identity)):
            raise ValueError('prospective source capture changes its retained exact selected-source identity')
        # Keep the original closure's truthful raw-clean observation; today's
        # observation remains in the separate operational source disclosure.
        captured = replace(captured, closure=retained_closure)
    # Refuse before input publication, candidate compilation or packet writes.
    _source_provenance_members(captured, artifact_writer=artifact_writer)
    return captured


def _source_provenance_members(captured, *, artifact_writer=None):
    """Render unchanged companions and preflight any selected custody allowance."""
    closure = captured.closure
    observation = ProspectiveSourceObservation(closure.source_closure_id + '.source-observation',
        _source_reference(closure), captured.manifest.identity, canonical_json_bytes(captured.source.to_mapping()).decode())
    members = tuple((name, record, record.canonical_bytes()) for name, record in
        zip(SOURCE_PROVENANCE_MEMBERS, (captured.manifest, observation), strict=True))
    limits = artifact_custody_limits(artifact_writer)
    for name, _record, raw in members:
        for allowance in ('control_record_bytes', 'in_memory_payload_bytes'):
            if limits.exceeds(allowance, len(raw)):
                raise ValueError('prospective source companion ' + name + ' exceeds its selected custody byte allowance '
                    + allowance + ': ' + str(len(raw)) + ' > ' + str(getattr(limits, allowance)))
    return members


def _publish_source_provenance(*, captured, destination, artifact_writer):
    closure = captured.closure
    members = _source_provenance_members(captured, artifact_writer=artifact_writer)
    relative = destination.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix() + '/provenance'
    for name, record, raw in members:
        artifact_writer.write(ArtifactWriteRequest(closure.source_closure_id + '.provenance.' + name.removesuffix('.json'),
            relative + '/' + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
            closure.source_closure_id + '.provenance', relative, raw,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))


def _load_source_provenance(*, directory, closure, read):
    if closure.kind is SourceClosureKind.CLEAN_GIT_COMMIT:
        return
    if closure.kind is not SourceClosureKind.EXACT_SOURCE_CLOSURE:
        raise ValueError('prospective handoff has no supported producing-source closure kind')
    provenance = directory / 'provenance'
    expected = {*SOURCE_PROVENANCE_MEMBERS, *(name + '.manifest.json' for name in SOURCE_PROVENANCE_MEMBERS)}
    if provenance.is_symlink() or not provenance.is_dir():
        raise ValueError('prospective source provenance changes its exact separate companion census')
    actual = {member.name for member in provenance.iterdir()}
    locks = {'.artifact-pair.' + sha256((name + '\0' + name + '.manifest.json').encode()).hexdigest()[:24] + '.lock'
        for name in SOURCE_PROVENANCE_MEMBERS}
    if not expected <= actual or actual - expected - locks - {'.publication-batches'}:
        raise ValueError('prospective source provenance changes its exact separate companion census')
    for name in actual & locks:
        path = provenance / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != 0:
            raise ValueError('prospective source provenance substitutes an existing custody-control pair lock')
    batches = provenance / '.publication-batches'
    if '.publication-batches' in actual and (batches.is_symlink() or not batches.is_dir()):
        raise ValueError('prospective source provenance substitutes its existing publication-custody directory')
    manifest_raw = read('provenance/selected-source-manifest.json', expected_schema=SelectedSourceManifest.SCHEMA)
    observation_raw = read('provenance/source-observation.json', expected_schema=ProspectiveSourceObservation.SCHEMA)
    manifest = decode_canonical_bytes(manifest_raw, SelectedSourceManifest, maximum_bytes=len(manifest_raw))
    observation = decode_canonical_bytes(observation_raw, ProspectiveSourceObservation, maximum_bytes=len(observation_raw))
    value = json.loads(observation.source_observation_json)
    if (not manifest.canonical_equals(manifest_raw) or not observation.canonical_equals(observation_raw)
            or manifest.identity != closure.exact_source_manifest or observation.closure != _source_reference(closure)
            or observation.selected_manifest != manifest.identity
            or (manifest.implementation_commit, manifest.implementation_sha256, manifest.source_tree_sha256)
                != (closure.implementation_commit, closure.implementation_sha256, closure.source_tree_sha256)
            or (value['implementation_commit'], value['implementation_sha256'], value['source_tree_sha256'])
                != (closure.implementation_commit, closure.implementation_sha256, closure.source_tree_sha256)):
        raise ValueError('prospective source provenance substitutes original closure, manifest or operational source identities')
    _validate_source_disclosure(closure, manifest, value)


def _validate_source_disclosure(closure, manifest, value):
    # The complete committed tree remains an operational census. Only the exact
    # selected manifest members bind the executable/input closure.
    if ((manifest.implementation_commit, manifest.implementation_sha256, manifest.source_tree_sha256)
            != (closure.implementation_commit, closure.implementation_sha256, closure.source_tree_sha256)
            or (value['implementation_commit'], value['implementation_sha256'], value['source_tree_sha256'])
                != (closure.implementation_commit, closure.implementation_sha256, closure.source_tree_sha256)):
        raise ValueError('prospective source disclosure substitutes selected source identities')
    files = {row['relative_path']: row for row in value['tracked_files']}
    selected = tuple(row.relative_path for row in manifest.members)
    if (tuple(value['source_admission']['selected_paths']) != selected
            or tuple(value['final_source_admission']['selected_paths']) != selected
            or any(files.get(row.relative_path) != row.to_document()['value'] for row in manifest.members)):
        raise ValueError('prospective source disclosure substitutes the exact selected manifest member census')


def load_recursive_prospective_spec(path):
    return decode_canonical_bytes(read_bounded_bytes(Path(path), maximum_bytes=MAXIMUM_SPEC_BYTES),
                                  RecursiveProspectiveAuthoringSpec, maximum_bytes=MAXIMUM_SPEC_BYTES)


def load_recursive_prospective_envelope(path, *, version=RecursiveProspectiveAuthoringEnvelope.VERSION):
    """Read only the explicitly selected additive operational envelope codec."""
    codecs = {RecursiveProspectiveAuthoringEnvelope.VERSION:
        (RecursiveProspectiveAuthoringEnvelope, MAXIMUM_OPERATIONAL_ENVELOPE_BYTES),
        RecursiveProspectiveAuthoringEnvelopeV3.VERSION:
        (RecursiveProspectiveAuthoringEnvelopeV3, MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES),
        RecursiveProspectiveAuthoringEnvelopeV4.VERSION:
        (RecursiveProspectiveAuthoringEnvelopeV4, MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES)}
    if version not in codecs:
        raise ValueError('prospective operational envelope revision is not installed')
    kind, maximum = codecs[version]
    record = decode_canonical_bytes(read_bounded_bytes(Path(path), maximum_bytes=maximum),
        kind, maximum_bytes=maximum)
    return record.reconstruct()


def _bounded_selection_decoder(registration):
    """Match the entire installed descriptor before granting physical capacity."""
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32.executable_binding import REGISTRATION as BOUNDED
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded64.executable_binding import REGISTRATION as LARGE
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_draft128.executable_binding import REGISTRATION as EXTENDED
    from empirical_lawhood.runtime.study_issue import StudyExtensionDecoderRegistration

    if registration is None:
        return False
    if type(registration) is not StudyExtensionDecoderRegistration or registration not in (REGISTRATION, BOUNDED, LARGE, EXTENDED):
        raise ValueError('prospective selection decoder is outside its exact installed allowlist')
    return registration in (BOUNDED, LARGE, EXTENDED)


def _large_selection_decoder(registration):
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded64.executable_binding import REGISTRATION as LARGE
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_draft128.executable_binding import REGISTRATION as EXTENDED
    _bounded_selection_decoder(registration)
    return registration in (LARGE, EXTENDED)


def _selection_decoder_registration(selection, *, retained_records=()):
    """Select a new profile from actual science and retained carrier bytes."""
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32.executable_binding import REGISTRATION as BOUNDED
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded64.executable_binding import REGISTRATION as LARGE
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_draft128.executable_binding import REGISTRATION as EXTENDED
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection

    if type(selection) is not RecursiveScientificSelection:
        raise TypeError('prospective decoder selection requires its exact scientific projection')
    size = selection.canonical_size_bytes()
    members = []
    for name, record in retained_records:
        members.append(RecursiveWaveMember(name, ObjectIdentity('preflight.' + name.removesuffix('.json'),
            record.SCHEMA, record.VERSION, record.fingerprint()), record.canonical_size_bytes()))
    capacity_error = None
    for registration in (REGISTRATION, BOUNDED, LARGE, EXTENDED):
        if size > registration.maximum_payload_bytes:
            continue
        try:
            for member in members:
                _prospective_member_codec(member, decoder_registration=registration)
        except ValueError as error:
            capacity_error = error
            continue
        return registration
    if capacity_error is not None:
        raise capacity_error
    raise ValueError('prospective scientific selection exceeds its installed capacity allocation')


def _stored_prospective_spec(spec, *, decoder_registration):
    """Choose the smallest exact carrier without changing legacy allocations."""
    bounded = _bounded_selection_decoder(decoder_registration)
    if type(spec) is not RecursiveProspectiveAuthoringSpec:
        raise TypeError('prospective carrier requires its exact original specification')
    if spec.canonical_size_bytes() <= MAXIMUM_SPEC_BYTES:
        return spec
    try:
        return RecursiveProspectiveAuthoringEnvelope.from_spec(spec)
    except ValueError:
        if not bounded:
            raise
    try:
        return RecursiveProspectiveAuthoringEnvelopeV3.from_spec(spec)
    except ValueError:
        if not _large_selection_decoder(decoder_registration):
            raise
    return RecursiveProspectiveAuthoringEnvelopeV4.from_spec(spec)


def _prospective_member_codec(member, *, decoder_registration=None):
    """A closed physical carrier allocation, independent of semantic science."""
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft, RecursiveScientificSelection
    from empirical_lawhood.runtime.plans import CandidateExecutionPlan, CandidateRunPlan
    from empirical_lawhood.runtime.candidate_compiler import StudyTemplate
    from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCompilationReport, ExecutableStudyCandidate
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeSpec
    from empirical_lawhood.runtime.study_issue import StudyExtensionDecoderRegistration
    types = {'draft.json': RecursiveStudyDraft, 'implementation.json': ImplementationSourceClosure,
        'recursive-prospective.json': RecursiveProspectiveAuthoringSpec, 'authoring.json': ExecutableStudyDefinition,
        'scientific-projection.json': RecursiveScientificSelection, 'decoder.json': StudyExtensionDecoderRegistration,
        'source-closure.json': ImplementationSourceClosure, 'template.json': StudyTemplate, 'registry.json': CapabilityRegistry,
        'resources.json': ExecutionResourceEnvelopeSpec, 'candidate-report.json': ExecutableStudyCompilationReport,
        'candidate.json': ExecutableStudyCandidate, 'preissue-run-plan.json': CandidateRunPlan,
        'preissue-execution-plan.json': CandidateExecutionPlan}
    record_type = types.get(member.filename)
    if record_type is None:
        raise ValueError('prospective retained member is outside its closed allowlist')
    bounded = _bounded_selection_decoder(decoder_registration)
    maximum = 64*1024**2 if member.filename in ('candidate-report.json', 'candidate.json', 'preissue-run-plan.json', 'preissue-execution-plan.json') else MAXIMUM_SPEC_BYTES
    if bounded and member.filename in ('draft.json', 'scientific-projection.json', 'template.json'):
        maximum = 32*1024**2
    if bounded and member.filename == 'candidate-report.json':
        maximum = 128*1024**2
    large = _large_selection_decoder(decoder_registration)
    if large and member.filename in ('draft.json', 'scientific-projection.json', 'template.json'):
        maximum = LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES
    if large and decoder_registration.decoder_key == DRAFT128_RECURSIVE_SELECTION_DECODER_KEY and member.filename == 'draft.json':
        maximum = DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES
    if large and member.filename in ('authoring.json', 'candidate-report.json', 'candidate.json', 'preissue-run-plan.json', 'preissue-execution-plan.json'):
        maximum = LARGE_RECURSIVE_RETAINED_MEMBER_MAXIMUM_BYTES
    if member.filename == 'recursive-prospective.json' and member.identity.object_schema == RecursiveProspectiveAuthoringEnvelope.SCHEMA:
        if member.identity.object_version == RecursiveProspectiveAuthoringEnvelopeV4.VERSION and large:
            record_type, maximum = RecursiveProspectiveAuthoringEnvelopeV4, MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES
        elif member.identity.object_version == RecursiveProspectiveAuthoringEnvelopeV3.VERSION and bounded:
            record_type, maximum = RecursiveProspectiveAuthoringEnvelopeV3, MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES
        else:
            record_type, maximum = RecursiveProspectiveAuthoringEnvelope, MAXIMUM_OPERATIONAL_ENVELOPE_BYTES
    if (member.identity.object_schema != record_type.SCHEMA or member.identity.object_version != record_type.VERSION
            or member.size_bytes > maximum):
        raise ValueError('prospective retained member changes its allowlisted schema/version or byte allocation: '
            + member.filename + ' has ' + member.identity.object_schema + '@' + member.identity.object_version
            + ' and ' + str(member.size_bytes) + ' bytes; expected ' + record_type.SCHEMA + '@' + record_type.VERSION
            + ' within ' + str(maximum) + ' bytes')
    return record_type, maximum


@dataclass(frozen=True, slots=True)
class _ConfigDecoder:
    provider_key: str
    provider_version: str
    record_type: type

    def validate_config(self, payload, *, expected_schema):
        if expected_schema != self.record_type.SCHEMA:
            raise ValueError('prospective operation config schema differs from its installed codec')
        # The source resolver has already enforced the selected registration's
        # byte envelope. Do not impose the unrelated outer-specification limit.
        decode_canonical_bytes(payload, self.record_type, maximum_bytes=len(payload))


def _compile(spec, closure, *, composition=None):
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.runtime.recursive_prospective import recursive_selection_proposal

    registrations, registry, codecs = operation_catalog() if composition is None else composition
    selected_capabilities = {(operation.selection.capability_key, operation.selection.capability_version)
                            for operation in spec.draft.operations if operation.node_id in spec.draft.selected_operation_ids}
    registry = type(registry)(registry.registry_id, tuple(manifest for manifest in registry.capabilities
                    if (manifest.capability_key, manifest.capability_version) in selected_capabilities))
    compilation = compile_recursive_wave(draft=spec.draft, registrations=registrations, registry=registry,
        implementation_commit=closure.implementation_commit, qualifications=spec.qualifications,
        known_design_inputs=spec.known_design_inputs, output_codecs=codecs,
        implementation_sha256=closure.implementation_sha256)
    if compilation.candidate_draft is None or compilation.candidate_report.candidate is None:
        raise ValueError('prospective scientific root or closed candidate is not eligible: ' + repr(compilation.candidate_report.diagnostics))
    base = StudyDefinition(spec.spec_id + '.standard', compilation.candidate_draft, spec.entry_package)
    retained_records = (('draft.json', spec.draft), ('template.json', compilation.template),
        ('registry.json', compilation.registry))
    registration = _selection_decoder_registration(compilation.selected_scientific_projection,
        retained_records=retained_records)

    def with_decoder(selected):
        proposal = recursive_selection_proposal(selection=compilation.selected_scientific_projection, registration=selected)
        extensions = ProposedStudyExtensionSet(spec.spec_id + '.extensions', ObjectIdentity.from_record(base.package_id, base),
            (proposal.namespace_id,), (proposal,))
        return ExecutableStudyDefinition(spec.spec_id + '.executable', base, extensions)

    authoring = with_decoder(registration)
    selected = _selection_decoder_registration(compilation.selected_scientific_projection,
        retained_records=(*retained_records, ('authoring.json', authoring)))
    if selected != registration:
        registration, authoring = selected, with_decoder(selected)
    return compilation, authoring, registration, registrations


def _operands(spec, compilation):
    values = {value.logical_artifact_id: value for value in spec.external_operands}
    for row in compilation.config_inputs:
        operand = RecursiveProspectiveOperand(row.config_id, row.record.fingerprint(), len(row.payload), row.payload_schema,
                      'application/json', row.input_spec.expected_outcome_access,
                      row.input_spec.expected_visibility_ceiling, row.input_parents)
        if values.setdefault(row.config_id, operand) != operand:
            raise ValueError('prospective config source changes its exact frozen record')
    for external in compilation.selected_scientific_projection.external_inputs:
        if external.parent_substitution:
            continue
        operand = values.get(external.logical_artifact_id)
        if operand is None:
            raise ValueError('prospective selected input needs exact physical operand metadata and byte allocation')
        if (operand.content_sha256 != external.expected_content_sha256 or operand.payload_schema != external.payload_schema
            or operand.media_type != external.media_type
            or (external.maximum_size_bytes is not None and operand.size_bytes > external.maximum_size_bytes)
            or operand.outcome_access is not external.outcome_access or operand.visibility_ceiling is not external.visibility_ceiling):
            raise ValueError('prospective operand metadata changes the authored scientific input')
    return tuple(values[key] for key in sorted(values))


def _context(spec, compilation, registrations, root, candidate_catalog=None):
    if candidate_catalog is None:
        from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
        candidate_catalog = GENERATED_EXTENSION_BUNDLE_AGGREGATE.candidate_capability_catalog
    static = {row.registration_id: row for row in candidate_catalog.registrations}
    by_selection = {registration.selection.selection_id: registration for registration in registrations}
    decoders = {}
    for operation in compilation.operations:
        registration = by_selection[operation.selection.selection_id]
        discovery = static.get(operation.selection.selection_id)
        if discovery is None:
            raise ValueError('prospective operation lacks its installed static discovery registration')
        key = discovery.provider_key
        decoders[key] = _ConfigDecoder(key, discovery.provider_version, registration.config_record_type)
    source = CandidateSourceResolutionService(ExternalContentAddressedInputResolver(root),
                 tuple(decoders[key] for key in sorted(decoders)))
    return RecursiveCandidateContextProvider(compilation, source, spec.formal_methods, spec.formal_source_inventories,
                tuple(static[manifest.registry_id] for manifest in compilation.registry.capabilities))


@dataclass(frozen=True, slots=True)
class _PreparedProspectiveCandidate:
    preview: RecursiveProspectiveCandidatePreview
    compilation: object
    authoring: ExecutableStudyDefinition
    decoder: object
    registrations: tuple
    report: object
    source_capture: CapturedTargetClosure
    stored_spec: CanonicalRecord | None


@dataclass(frozen=True, slots=True)
class _AuthoredProspectiveRoots:
    """Immutable objects from this author; consuming reads still check custody."""
    packet: AuthoredRecursiveWave
    candidate: CanonicalRecord
    implementation: ImplementationSourceClosure
    scientific_projection: CanonicalRecord


@dataclass(frozen=True, slots=True)
class _ProspectivePreparationInputs:
    project_root: Path
    artifact_writer: object
    input_bindings: tuple
    composition: object
    api_factory: object
    candidate_catalog: object
    original_input_access: object

    def matches(self, other):
        return (self.project_root == other.project_root and self.input_bindings == other.input_bindings
            and all(getattr(self, name) is getattr(other, name) for name in (
                'artifact_writer', 'composition', 'api_factory', 'candidate_catalog', 'original_input_access')))


@dataclass(slots=True)
class _ProspectiveAuthoringInvocation:
    # At most one large compilation; no publication or permission verdict.
    prepared: tuple[_ProspectivePreparationInputs, _PreparedProspectiveCandidate] | None = None


_prospective_authoring_invocation: ContextVar[_ProspectiveAuthoringInvocation | None] = ContextVar(
    'prospective_authoring_invocation', default=None)


@contextmanager
def _prospective_preparation_scope():
    """Keep immutable preview work only through this one public authoring call."""
    current = _ProspectiveAuthoringInvocation()
    token = _prospective_authoring_invocation.set(current)
    try:
        yield
    finally:
        current.prepared = None
        _prospective_authoring_invocation.reset(token)


def _compile_outer_candidate(*, directory, authoring, compilation, decoder, context, project_root, api_factory):
    from empirical_lawhood.api.authoring_handoff import write_exclusive_record
    from empirical_lawhood.api.results import CompileCandidateRequest

    paths = {name: write_exclusive_record(directory, name, record) for name, record in
             (('authoring.json', authoring), ('scientific-projection.json', compilation.selected_scientific_projection),
              ('decoder.json', decoder))}
    api = (create_authoring_api if api_factory is None else api_factory)(repo_root=Path(project_root),
                candidate_context_provider=context, candidate_capability_catalog=context.catalog)
    compiled = api.compile_candidate(CompileCandidateRequest(paths['authoring.json'], (paths['scientific-projection.json'],), (paths['decoder.json'],)))
    if not compiled.succeeded or compiled.payload is None or compiled.payload.report.candidate is None:
        raise ValueError('prospective candidate compilation refused: ' + repr((compiled.reason_codes, compiled.errors)))
    return compiled.payload.report, compiled.payload.report.candidate


def _input_payload(binding, *, maximum_bytes, original_input_access=None):
    from .prospective_experiment import _require_original_inputs
    _require_original_inputs(original_input_access)
    raw = (binding.bounded_bytes(maximum_bytes=maximum_bytes) if type(binding) is InputBytes else
        read_bounded_bytes(Path(binding), maximum_bytes=maximum_bytes))
    _require_original_inputs(original_input_access)
    return raw


def _require_prospective_public_member_capacity(name, size_bytes, *, artifact_writer=None):
    """Preflight newly produced records against their next public consumer.

    Historical retained-member codec allocations stay unchanged. These checks
    concern newly rendered authoring/candidate/runtime controls, not referenced data.
    """
    from .codecs import MAX_EXECUTABLE_STUDY_AUTHORING_BYTES
    from empirical_lawhood.runtime.study_issue import MAX_COMPOSED_PROGRAMME_CONTROL_BYTES, MAX_ISSUE_PAYLOAD_BYTES
    maximum = {'authoring.base.json': MAX_ISSUE_PAYLOAD_BYTES,
        'authoring.json': MAX_EXECUTABLE_STUDY_AUTHORING_BYTES,
        'candidate.json': MAX_COMPOSED_PROGRAMME_CONTROL_BYTES}.get(name)
    if name in ('preissue-run-plan.json', 'preissue-execution-plan.json'):
        limits = artifact_custody_limits(artifact_writer)
        for allowance in ('control_record_bytes', 'in_memory_payload_bytes'):
            if limits.exceeds(allowance, size_bytes):
                raise ValueError('prospective ' + name + ' exceeds its selected custody runtime-plan byte allowance '
                    + allowance)
    if maximum is not None and size_bytes > maximum:
        role = 'standard-base-issue' if name == 'authoring.base.json' else 'composed-control'
        raise ValueError('prospective ' + name + ' exceeds its exact public ' + role + ' byte allocation')


def _prepare_prospective_candidate(*, design_inputs, project_root, artifact_writer, input_bindings=(),
        composition=None, api_factory=None, candidate_catalog=None, compilation_directory=None, prospective_spec=None, retained_closure=None,
        original_input_access=None, _prepared=None):
    """One owner for exact input publication and actual outer compilation."""
    from empirical_lawhood.runtime.study_issue import project_standard_study_extensions

    if type(design_inputs) is not RecursiveProspectiveDesignInputs:
        raise TypeError('prospective candidate preparation requires exact resource-free design inputs')
    design_inputs.__post_init__()
    from .prospective_experiment import _require_original_inputs
    _require_original_inputs(original_input_access)
    if design_inputs.draft.canonical_size_bytes() > DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES:
        raise ValueError('prospective scientific draft exceeds its maximum installed capacity allocation')
    artifact_writer.root.verify(for_write=True)
    source_capture = _capture_prospective_source(project_root, design_inputs.spec_id + '.source-closure',
        retained_closure=retained_closure, artifact_writer=artifact_writer)
    closure = source_capture.closure
    if _prepared is None:
        compilation, authoring, decoder, registrations = _compile(design_inputs, closure, composition=composition)
    else:
        if (_prepared.preview.design_inputs != design_inputs or _prepared.preview.implementation != closure):
            raise ValueError('prospective preparation changes its live preview design or source')
        compilation, authoring, decoder, registrations = (
            _prepared.compilation, _prepared.authoring, _prepared.decoder, _prepared.registrations)
    stored_spec, retained_records = None, ()
    if prospective_spec is not None:
        if RecursiveProspectiveDesignInputs.from_spec(prospective_spec) != design_inputs:
            raise ValueError('prospective carrier changes its original candidate design inputs')
        stored_spec = _stored_prospective_spec(prospective_spec, decoder_registration=decoder)
        retained_records = (('recursive-prospective.json', stored_spec), ('resources.json', prospective_spec.resources))
    _require_prospective_public_member_capacity('authoring.base.json', authoring.base.canonical_size_bytes())
    for name, record in (*retained_records, ('draft.json', design_inputs.draft),
            ('authoring.json', authoring), ('scientific-projection.json', compilation.selected_scientific_projection),
            ('decoder.json', decoder), ('source-closure.json', closure), ('template.json', compilation.template),
            ('registry.json', compilation.registry)):
        size_bytes = record.canonical_size_bytes()
        _prospective_member_codec(RecursiveWaveMember(name, ObjectIdentity.from_record('preflight.'+name.removesuffix('.json'), record),
            size_bytes), decoder_registration=decoder)
        _require_prospective_public_member_capacity(name, size_bytes)
    from empirical_lawhood.api.recursive_publications import authenticate_registered_publications
    authenticate_registered_publications(draft=design_inputs.draft, config_inputs=compilation.config_inputs,
        registrations=registrations, artifact_writer=artifact_writer)
    from .recursive_qualified_parents import authenticate_recursive_qualified_parents
    authenticate_recursive_qualified_parents(spec_bindings=design_inputs.qualified_parent_bindings, draft=design_inputs.draft,
                artifact_writer=artifact_writer, registrations=registrations, output_codecs=compilation.output_codecs)
    operands = _operands(design_inputs, compilation)
    bindings = dict(input_bindings)
    config_payloads = {row.record.fingerprint(): row.payload for row in compilation.config_inputs}
    control_payloads = {qualification.fingerprint(): qualification.canonical_bytes() for qualification in design_inputs.qualifications}
    required_paths = {operand.logical_artifact_id for operand in operands if operand.content_sha256 not in config_payloads}
    required_config_hashes = {value.source_config_sha256 for value in design_inputs.draft.prospective_draft.source_materializations}
    if len(bindings) != len(tuple(input_bindings)) or set(bindings) != required_paths | required_config_hashes:
        raise ValueError('prospective authoring binds every selected source and source config exactly once')
    pending = dict(config_payloads)
    pending.update(control_payloads)
    validated_inputs = 0
    input_total = len(operands) + len(required_config_hashes)
    report_progress(phase='validate_inputs', done=0, total=input_total)
    for operand in operands:
        raw = pending.get(operand.content_sha256)
        if raw is None:
            raw = _input_payload(bindings[operand.logical_artifact_id], maximum_bytes=operand.size_bytes, original_input_access=original_input_access)
        if len(raw) != operand.size_bytes or sha256(raw).hexdigest() != operand.content_sha256:
            raise ValueError('prospective external source bytes differ from the selected exact operand')
        if _prepared is None:
            validate_declared_recursive_input_payload(draft=design_inputs.draft, registrations=registrations,
                fallback_codecs=compilation.output_codecs, logical_artifact_id=operand.logical_artifact_id, payload=raw)
        # Reuse only the same immutable consumer/operand validation. Original
        # input bytes, publication custody and current access are checked anew.
        pending[operand.content_sha256] = raw
        validated_inputs += 1
        report_progress(phase='validate_inputs', done=validated_inputs, total=input_total)
    for digest in required_config_hashes:
        raw = _input_payload(bindings[digest], maximum_bytes=1024**2, original_input_access=original_input_access)
        if sha256(raw).hexdigest() != digest:
            raise ValueError('prospective source config changes its declared exact bytes')
        pending[digest] = raw
        validated_inputs += 1
        report_progress(phase='validate_inputs', done=validated_inputs, total=input_total)
    # All local inputs pass their bounds before the first publication.
    publisher = ExternalCandidateInputPublisher(artifact_writer.root)
    # Each source already passed its exact size/digest and consumer codec. The
    # publisher's durability windows add no replacement data-size allocation.
    def guarded_payloads():
        for digest in sorted(pending):
            _require_original_inputs(original_input_access)
            yield pending[digest]
            _require_original_inputs(original_input_access)
    publisher.publish_many(guarded_payloads())
    if _prepared is not None:
        report, candidate = _prepared.report, _prepared.preview.candidate
        if compilation_directory is not None:
            compilation_directory.mkdir(parents=True, exist_ok=False)
    else:
        context = _context(design_inputs, compilation, registrations, artifact_writer.root, candidate_catalog)
        resolution = context.resolve_standard(authoring.base)
        if resolution.diagnostics:
            first = resolution.diagnostics[0]
            raise ValueError('prospective source resolution or standard formal context is not ready: '
                + str(len(resolution.diagnostics)) + ' diagnostic(s); '
                + first.code.value + ' at ' + first.field_path + ': ' + first.message)
        if compilation_directory is None:
            with TemporaryDirectory(prefix='.prospective-candidate-', dir=artifact_writer.root.contract.canonical_path) as scratch:
                report, candidate = _compile_outer_candidate(directory=Path(scratch), authoring=authoring,
                    compilation=compilation, decoder=decoder, context=context, project_root=project_root, api_factory=api_factory)
        else:
            compilation_directory.mkdir(parents=True, exist_ok=False)
            report, candidate = _compile_outer_candidate(directory=compilation_directory, authoring=authoring,
                compilation=compilation, decoder=decoder, context=context, project_root=project_root, api_factory=api_factory)
    for name, record in (('candidate-report.json', report), ('candidate.json', candidate)):
        size_bytes = record.canonical_size_bytes()
        _prospective_member_codec(RecursiveWaveMember(name, ObjectIdentity.from_record('preflight.'+name.removesuffix('.json'), record),
            size_bytes), decoder_registration=decoder)
        _require_prospective_public_member_capacity(name, size_bytes)
    if _prepared is None:
        extensions, _, _ = project_standard_study_extensions(candidate=candidate,
            extension_payload_bytes=(compilation.selected_scientific_projection.canonical_bytes(),), decoder_registrations=(decoder,),
            extension_materializations=report.extension_materializations)
    else:
        extensions = _prepared.preview.issued_extensions
    if GitStudySourceClosureInspector(Path(project_root)).observe(closure) != closure:
        raise ValueError('prospective producing source changed during candidate preparation')
    preview = RecursiveProspectiveCandidatePreview(design_inputs, closure, candidate, extensions)
    return _PreparedProspectiveCandidate(preview, compilation, authoring, decoder, registrations, report, source_capture, stored_spec)


def preview_recursive_prospective_candidate(*, design_inputs, project_root, artifact_writer, input_bindings=(),
        composition=None, api_factory=None, candidate_catalog=None, retained_closure=None, original_input_access=None):
    """Compile comparison facts only; publish no completed handoff or authority."""
    prepared = _prepare_prospective_candidate(design_inputs=design_inputs, project_root=project_root,
        artifact_writer=artifact_writer, input_bindings=input_bindings, composition=composition,
        api_factory=api_factory, candidate_catalog=candidate_catalog, retained_closure=retained_closure,
        original_input_access=original_input_access)
    invocation = _prospective_authoring_invocation.get()
    if invocation is not None:
        invocation.prepared = (_ProspectivePreparationInputs(Path(project_root), artifact_writer,
            tuple(input_bindings), composition, api_factory, candidate_catalog, original_input_access), prepared)
    return prepared.preview


def author_recursive_prospective(*, spec, project_root, artifact_writer, output_dir, input_bindings=(),
                                 composition=None, api_factory=None, candidate_catalog=None, expected_preview=None,
                                 retained_closure=None, original_input_access=None, _capture_roots=None):
    """Publish a frozen candidate handoff; issue and execution retain their authorities."""
    if _capture_roots is not None and not callable(_capture_roots):
        raise TypeError('prospective root retention requires an operation-local callback')
    if type(spec) in (RecursiveProspectiveAuthoringEnvelope, RecursiveProspectiveAuthoringEnvelopeV3, RecursiveProspectiveAuthoringEnvelopeV4):
        spec = spec.reconstruct()
    if type(spec) is not RecursiveProspectiveAuthoringSpec:
        raise ValueError('prospective authoring requires its exact legacy semantic specification')
    spec.__post_init__()
    design_inputs = RecursiveProspectiveDesignInputs.from_spec(spec)
    if expected_preview is not None:
        if type(expected_preview) is not RecursiveProspectiveCandidatePreview:
            raise TypeError('prospective authoring preview has the wrong exact type')
        expected_preview.__post_init__()
        if expected_preview.design_inputs != design_inputs:
            raise ValueError('prospective authoring changes its preview scientific design inputs')
        if retained_closure is not None and retained_closure != expected_preview.implementation:
            raise ValueError('prospective authoring changes its original selected source closure')
        retained_closure = expected_preview.implementation
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root), artifact_writer=artifact_writer)
    invocation = _prospective_authoring_invocation.get()
    reused = None
    if invocation is not None and invocation.prepared is not None:
        original, prepared = invocation.prepared
        current = _ProspectivePreparationInputs(Path(project_root), artifact_writer, tuple(input_bindings),
            composition, api_factory, candidate_catalog, original_input_access)
        if expected_preview is prepared.preview and original.matches(current):
            reused = prepared
        # One preview can serve only its immediately associated author.
        invocation.prepared = None
    prepared = _prepare_prospective_candidate(design_inputs=design_inputs, project_root=project_root,
        artifact_writer=artifact_writer, input_bindings=input_bindings, composition=composition,
        api_factory=api_factory, candidate_catalog=candidate_catalog, compilation_directory=destination,
        prospective_spec=spec,
        retained_closure=retained_closure, original_input_access=original_input_access, _prepared=reused)
    if expected_preview is not None and prepared.preview != expected_preview:
        raise ValueError('prospective authoring changes its fresh source, outer candidate or issued-extension preview')
    compilation, authoring, decoder, report = prepared.compilation, prepared.authoring, prepared.decoder, prepared.report
    stored_spec = prepared.stored_spec
    closure, candidate, extensions = prepared.preview.implementation, prepared.preview.candidate, prepared.preview.issued_extensions
    run_plan = compile_preissue_run_plan(run_plan_id=spec.spec_id + '.preissue', candidate_record=candidate.base_candidate.base_candidate,
        candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate), registry=compilation.registry,
        implementation_commit=closure.implementation_commit, issued_extension_set=extensions,
        resource_envelope=spec.resources, jit_census=None, jit_manifest=None)
    projection = lower_run_plan(run_plan, compilation.registry)
    records = {'draft.json': spec.draft, 'implementation.json': closure, 'recursive-prospective.json': stored_spec,
               'authoring.json': authoring, 'scientific-projection.json': compilation.selected_scientific_projection,
               'decoder.json': decoder, 'source-closure.json': closure, 'template.json': compilation.template,
               'registry.json': compilation.registry, 'resources.json': spec.resources, 'candidate-report.json': report,
               'candidate.json': candidate, 'preissue-run-plan.json': run_plan, 'preissue-execution-plan.json': projection}
    members = tuple(RecursiveWaveMember(name, ObjectIdentity.from_record(spec.draft.draft_id if name == 'draft.json'
                    else 'recursive-member.' + name.removesuffix('.json'), record), record.canonical_size_bytes())
                    for name, record in sorted(records.items()))
    for member in members:
        _require_prospective_public_member_capacity(member.filename, member.size_bytes, artifact_writer=artifact_writer)
        _prospective_member_codec(member, decoder_registration=decoder)
    by_name = {member.filename: member.identity for member in members}
    packet = AuthoredRecursiveWave(spec.spec_id + '.authoring', by_name['draft.json'], by_name['implementation.json'], members)
    if GitStudySourceClosureInspector(Path(project_root)).observe(closure) != closure:
        raise ValueError('prospective producing source changed during authoring')
    relative = destination.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    # The custody plane authenticates identical temporary compilation members too.
    if reused is None:
        for name in ('authoring.json', 'scientific-projection.json', 'decoder.json'):
            (destination / name).unlink()
    from .experiment_runtime_bindings import original_input_record_publication
    from .prospective_experiment import _require_original_inputs
    from empirical_lawhood.runtime.artifacts import lineage_parent_sort_key
    # Graph containers embed canonical config strings. Derive their exact
    # ancestry from actual typed config rows, not an opaque string scan.
    graph_parents = (() if original_input_access is None else tuple(sorted({
        parent for row in compilation.config_inputs
        for parent in original_input_access.record_parents(row.record)}, key=lineage_parent_sort_key)))
    graph_names = {'draft.json', 'recursive-prospective.json', 'authoring.json',
        'scientific-projection.json', 'template.json', 'candidate-report.json', 'candidate.json',
        'preissue-run-plan.json', 'preissue-execution-plan.json'}
    for name, record in (*sorted(records.items()), ('authored-wave.json', packet)):
        _require_original_inputs(original_input_access)
        parents, access, visibility = original_input_record_publication(record=record,
            original_input_access=original_input_access,
            inherited_parents=graph_parents if name in graph_names else ())
        artifact_writer.write(ArtifactWriteRequest(packet.packet_id + '.' + name.removesuffix('.json'), relative + '/' + name,
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', packet.packet_id, relative, record.canonical_bytes(),
            visibility, tuple(value.visibility_ceiling for value in parents), access, lineage_parents=parents))
        _require_original_inputs(original_input_access)
    _publish_source_provenance(captured=prepared.source_capture, destination=destination, artifact_writer=artifact_writer)
    if _capture_roots is not None:
        _capture_roots(_AuthoredProspectiveRoots(packet, candidate, closure, compilation.selected_scientific_projection))
    return {'status': 'AUTHORED_PROSPECTIVE', 'authoring_dir': str(destination), 'candidate_sha256': candidate.fingerprint(),
            'task_count': len(projection.tasks), 'native_contact': 'none', 'scientific_authority': 'NONE', 'qualification': 'NOT_ESTABLISHED'}


@dataclass(frozen=True, slots=True)
class RecursiveProspectiveApplicationHandoff:
    directory: Path
    compilation: object
    authoring: ExecutableStudyDefinition
    context: RecursiveCandidateContextProvider
    projection: object
    resources: object
    platform_ports: tuple[ExecutablePlatformPort, ...]


def _prospective_selection_decoder(packet, read):
    """Authenticate the small pinned descriptor before reading larger members."""
    from empirical_lawhood.runtime.study_issue import StudyExtensionDecoderRegistration

    member, = (row for row in packet.members if row.filename == 'decoder.json')
    kind, maximum = _prospective_member_codec(member)
    raw = read(member.filename, maximum, expected_schema=kind.SCHEMA)
    if (len(raw), sha256(raw).hexdigest()) != (member.size_bytes, member.identity.object_fingerprint):
        raise ValueError('prospective decoder differs from its exact packet member')
    decoder = decode_canonical_bytes(raw, StudyExtensionDecoderRegistration, maximum_bytes=maximum)
    _bounded_selection_decoder(decoder)
    return decoder, raw


def _load_recursive_prospective_members(*, directory, root, storage_profile, artifact_writer, original_input_access=None):
    """Authenticate the original closed packet without consulting current science."""
    directory, _ = resolve_authoring_directory(Path(directory), repo_root=Path(root), storage_profile=storage_profile,
                            escape_message='recursive prospective authoring lies outside its selected guarded root', for_write=False)
    return _read_recursive_prospective_members(directory=directory, artifact_writer=artifact_writer,
        original_input_access=original_input_access)


def _read_recursive_prospective_members(*, directory, artifact_writer, original_input_access=None):
    """Use the same closed parser after actual writer-root read admission."""
    from .prospective_experiment import _directory
    directory = _directory(directory, artifact_writer)
    # Both paths authenticate the same member receipts; prospective exports use
    # a genuine closure rather than the development producing-source record.
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    def read(name, maximum=MAXIMUM_SPEC_BYTES, *, expected_schema=None):
        manifest = decode_artifact_manifest(read_bounded_bytes(directory / (name + '.manifest.json'), maximum_bytes=1024**2))
        if manifest.materialization.relative_path != (directory / name).relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix():
            raise ValueError('prospective retained member changes its exact path')
        if ((original_input_access is None and (
                manifest.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE))
            or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or manifest.logical.media_type != 'application/json'
            or manifest.materialization.size_bytes > maximum
            or expected_schema is not None and manifest.logical.payload_schema != expected_schema):
            raise ValueError('prospective handoff member changes its access role or allocation')
        if name in ('preissue-run-plan.json', 'preissue-execution-plan.json'):
            _require_prospective_public_member_capacity(name, manifest.materialization.size_bytes,
                artifact_writer=artifact_writer)
        from .prospective_experiment import _require_original_inputs
        options = {} if original_input_access is None else {"before_member": original_input_access.require_issued_member}
        artifact_writer.verify_manifest(manifest, **options)
        _require_original_inputs(original_input_access)
        raw = read_bounded_bytes(artifact_writer.root.resolve(manifest.materialization.relative_path, for_write=False), maximum_bytes=maximum)
        if (len(raw) != manifest.materialization.size_bytes or sha256(raw).hexdigest() != manifest.logical.content_sha256
            or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
            raise ValueError('prospective member bytes changed after exact manifest authentication')
        _require_original_inputs(original_input_access)
        return raw
    packet = decode_canonical_bytes(read('authored-wave.json', 1024**2, expected_schema=AuthoredRecursiveWave.SCHEMA), AuthoredRecursiveWave, maximum_bytes=1024**2)
    expected_names = {'draft.json', 'implementation.json', 'recursive-prospective.json', 'authoring.json',
        'scientific-projection.json', 'decoder.json', 'source-closure.json', 'template.json', 'registry.json', 'resources.json',
        'candidate-report.json', 'candidate.json', 'preissue-run-plan.json', 'preissue-execution-plan.json'}
    if {member.filename for member in packet.members} != expected_names:
        raise ValueError('prospective retained handoff changes its closed complete member census')
    decoder, decoder_raw = _prospective_selection_decoder(packet, read)
    payloads = {'decoder.json': decoder_raw}
    for member in packet.members:
        record_type, maximum = _prospective_member_codec(member, decoder_registration=decoder)
        if member.filename == 'decoder.json':
            continue
        raw = read(member.filename, maximum, expected_schema=record_type.SCHEMA)
        if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.identity.object_fingerprint:
            raise ValueError('prospective retained member changes its committed bytes')
        payloads[member.filename] = raw
    spec_member = next(member for member in packet.members if member.filename == 'recursive-prospective.json')
    kind, maximum = _prospective_member_codec(spec_member, decoder_registration=decoder)
    if kind in (RecursiveProspectiveAuthoringEnvelope, RecursiveProspectiveAuthoringEnvelopeV3, RecursiveProspectiveAuthoringEnvelopeV4):
        envelope = decode_canonical_bytes(payloads['recursive-prospective.json'], kind, maximum_bytes=maximum)
        spec = envelope.reconstruct()
    else:
        spec = decode_canonical_bytes(payloads['recursive-prospective.json'], RecursiveProspectiveAuthoringSpec, maximum_bytes=MAXIMUM_SPEC_BYTES)
    closure = decode_canonical_bytes(payloads['source-closure.json'], ImplementationSourceClosure, maximum_bytes=MAXIMUM_SPEC_BYTES)
    if (not spec.draft.canonical_equals(payloads['draft.json'])
        or not closure.canonical_equals(payloads['implementation.json'])
        or packet.draft != ObjectIdentity.from_record(spec.draft.draft_id, spec.draft)
        or packet.implementation.object_fingerprint != closure.fingerprint()):
        raise ValueError('prospective handoff changes its exact scientific or producing implementation root')
    if packet.implementation != ObjectIdentity.from_record('recursive-member.implementation', closure):
        raise ValueError('prospective handoff changes its original implementation source-closure role or identity')
    _load_source_provenance(directory=directory, closure=closure,
        read=lambda name, *, expected_schema: read_authoring_source_companion(writer=artifact_writer,
            directory=directory, name=name, expected_schema=expected_schema))
    return directory, packet, payloads, spec, closure, decoder


@dataclass(frozen=True, slots=True)
class RetainedRecursiveProspectiveHandoff:
    """Original authenticated read metadata, with no executable provider ports."""

    directory: Path
    packet: AuthoredRecursiveWave
    draft: object
    implementation: ImplementationSourceClosure
    candidate: object
    projection: object
    scientific_projection: object


def load_retained_recursive_prospective_handoff(*, directory, root, storage_profile, artifact_writer, original_input_access=None):
    """Read original custody without requiring current operation declarations.

    This path authenticates recorded identities and bytes. It does not compile
    a current candidate, decode domain products, bind providers or permit work.
    """
    directory, packet, payloads, spec, closure, decoder = _load_recursive_prospective_members(
        directory=directory, root=root, storage_profile=storage_profile, artifact_writer=artifact_writer,
        original_input_access=original_input_access)
    return _retained_recursive_prospective_from_members(directory=directory, packet=packet,
        payloads=payloads, spec=spec, closure=closure, decoder=decoder)


def _read_retained_recursive_prospective_handoff(*, directory, artifact_writer, original_input_access=None):
    """Read exact retained metadata with no checkout/profile or executable binding."""
    directory, packet, payloads, spec, closure, decoder = _read_recursive_prospective_members(
        directory=directory, artifact_writer=artifact_writer, original_input_access=original_input_access)
    return _retained_recursive_prospective_from_members(directory=directory, packet=packet,
        payloads=payloads, spec=spec, closure=closure, decoder=decoder)


def _retained_recursive_prospective_from_members(*, directory, packet, payloads, spec, closure, decoder):
    # Consume this reader's owned payload mapping. The closed-packet owner has
    # authenticated every member, including the reconstructed draft and source.
    # Keeping all raw members and all decoded duplicates together can exceed a
    # bounded metadata reader's memory even when each member fits its contract.
    metadata_names = {'candidate.json', 'candidate-report.json', 'authoring.json', 'template.json',
        'preissue-run-plan.json', 'preissue-execution-plan.json', 'scientific-projection.json',
        'registry.json', 'resources.json'}
    for name in tuple(payloads):
        if name not in metadata_names:
            del payloads[name]
    members = {member.filename: member for member in packet.members}

    def decode_member(name):
        kind, maximum = _prospective_member_codec(members[name], decoder_registration=decoder)
        return decode_canonical_bytes(payloads.pop(name), kind, maximum_bytes=maximum)

    report = decode_member('candidate-report.json')
    candidate = report.candidate
    if candidate is None or not candidate.canonical_equals(payloads.pop('candidate.json')):
        raise ValueError('prospective retained candidate differs from its original compilation report')
    del report
    authoring = candidate.authoring_package
    if (not authoring.canonical_equals(payloads.pop('authoring.json'))
            or authoring.base.draft != spec.draft.prospective_draft
            or not spec.resources.canonical_equals(payloads.pop('resources.json'))):
        raise ValueError('prospective retained metadata changes its original authoring or resources')
    base = candidate.base_candidate.base_candidate
    template = decode_member('template.json')
    if (template.protocol, template.graph, template.coverage) != (
            base.protocol, base.scientific_graph, base.obligation_coverage):
        raise ValueError('prospective retained template changes its original candidate')
    del template
    selected = decode_member('scientific-projection.json')
    plan = decode_member('preissue-run-plan.json')
    projection = decode_member('preissue-execution-plan.json')
    registry = decode_member('registry.json')
    from empirical_lawhood.runtime.recursive_compiler import derive_recursive_scientific_selection

    if (base.implementation_sha256 != closure.implementation_sha256
            or selected != derive_recursive_scientific_selection(spec.draft)
            or plan.candidate != ObjectIdentity.from_record(candidate.candidate_id, candidate)
            or projection.candidate != plan.candidate
            or projection.source_plan != ObjectIdentity.from_record(plan.run_plan_id, plan)
            or (plan.registry_sha256, projection.registry_sha256) != (registry.fingerprint(),) * 2
            or (plan.implementation_commit, projection.implementation_commit) != (closure.implementation_commit,) * 2
            or {row.step_id for row in plan.steps} != {row.task_id for row in projection.tasks}):
        raise ValueError('prospective retained metadata changes its original candidate, source or plan association')
    return RetainedRecursiveProspectiveHandoff(directory, packet, spec.draft, closure, candidate, projection, selected)


def load_recursive_prospective_handoff(*, directory, root, storage_profile, artifact_writer, composition=None, candidate_catalog=None,
        require_current_source=True, original_input_access=None):
    """Authenticate original custody and rederive an executable current handoff.

    Fresh execution retains the default source check. Recovery may load the
    original pinned closure without requiring that checkout to remain clean;
    its execution owner still authenticates the executing source and any
    separately supplied source amendment before continuing work.
    """
    handoff, _ = _load_recursive_prospective_handoff_with_roots(directory=directory, root=root,
        storage_profile=storage_profile, artifact_writer=artifact_writer, composition=composition,
        candidate_catalog=candidate_catalog, require_current_source=require_current_source,
        **({} if original_input_access is None else {"original_input_access": original_input_access}))
    return handoff


def _load_recursive_prospective_handoff_with_roots(*, directory, root, storage_profile, artifact_writer,
        composition=None, candidate_catalog=None, require_current_source=True, original_input_access=None):
    """Return owning records for immediate composition within this invocation.

    The public wrapper discards the extra records. No retained handoff field or
    caller-supplied cache can carry authentication into another invocation.
    """
    from empirical_lawhood.runtime.plans import CandidateExecutionPlan, CandidateRunPlan
    from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCompilationReport
    from empirical_lawhood.runtime.study_issue import project_standard_study_extensions

    if type(require_current_source) is not bool:
        raise TypeError('prospective handoff source validation requires an explicit boolean selection')
    directory, packet, payloads, spec, closure, decoder = _load_recursive_prospective_members(
        directory=directory, root=root, storage_profile=storage_profile, artifact_writer=artifact_writer,
        original_input_access=original_input_access)
    if require_current_source and GitStudySourceClosureInspector(Path(root)).observe(closure) != closure:
        raise ValueError('prospective handoff producing implementation differs from the selected source checkout')
    compilation, authoring, current_decoder, registrations = _compile(spec, closure, composition=composition)
    _require_prospective_public_member_capacity('authoring.base.json', authoring.base.canonical_size_bytes())
    if current_decoder != decoder:
        raise ValueError('prospective handoff changes its exact selected scientific decoder')
    from empirical_lawhood.api.recursive_publications import authenticate_registered_publications
    authenticate_registered_publications(draft=spec.draft, config_inputs=compilation.config_inputs,
        registrations=registrations, artifact_writer=artifact_writer)
    from .recursive_qualified_parents import authenticate_recursive_qualified_parents
    authenticate_recursive_qualified_parents(spec_bindings=spec.qualified_parent_bindings, draft=spec.draft,
                artifact_writer=artifact_writer, registrations=registrations, output_codecs=compilation.output_codecs)
    if (not authoring.canonical_equals(payloads['authoring.json'])
        or not compilation.template.canonical_equals(payloads['template.json'])
        or not compilation.selected_scientific_projection.canonical_equals(payloads['scientific-projection.json'])
        or not compilation.registry.canonical_equals(payloads['registry.json'])
        or not spec.resources.canonical_equals(payloads['resources.json'])):
        raise ValueError('prospective retained source graph differs from its installed static materialization')
    limits={member.filename:_prospective_member_codec(member,decoder_registration=decoder)[1]
        for member in packet.members if member.filename in ('preissue-execution-plan.json','preissue-run-plan.json')}
    projection = decode_canonical_bytes(payloads['preissue-execution-plan.json'], CandidateExecutionPlan,
        maximum_bytes=limits['preissue-execution-plan.json'])
    retained_plan = decode_canonical_bytes(payloads['preissue-run-plan.json'], CandidateRunPlan,
        maximum_bytes=limits['preissue-run-plan.json'])
    report_member, = (row for row in packet.members if row.filename == 'candidate-report.json')
    _, report_maximum = _prospective_member_codec(report_member, decoder_registration=decoder)
    report = decode_canonical_bytes(payloads['candidate-report.json'], ExecutableStudyCompilationReport, maximum_bytes=report_maximum)
    if (report.candidate is None or not report.candidate.canonical_equals(payloads['candidate.json'])
        or report.candidate.authoring_package != authoring):
        raise ValueError('prospective handoff changes its actual compiled candidate')
    extensions, _, _ = project_standard_study_extensions(candidate=report.candidate,
        extension_payload_bytes=(payloads['scientific-projection.json'],), decoder_registrations=(decoder,),
        extension_materializations=report.extension_materializations)
    expected_plan = compile_preissue_run_plan(run_plan_id=spec.spec_id + '.preissue',
        candidate_record=report.candidate.base_candidate.base_candidate,
        candidate=ObjectIdentity.from_record(report.candidate.candidate_id, report.candidate),
        registry=compilation.registry, implementation_commit=closure.implementation_commit,
        issued_extension_set=extensions, resource_envelope=spec.resources, jit_census=None, jit_manifest=None)
    if retained_plan != expected_plan or projection != lower_run_plan(expected_plan, compilation.registry):
        raise ValueError('prospective retained executable projection changes its actual authored scientific graph')
    context = _context(spec, compilation, registrations, artifact_writer.root, candidate_catalog)
    from empirical_lawhood.runtime.recursive_storage_codecs import storage_codec_census
    supplier = RecursiveContentInputSupplier(root=artifact_writer.root, operands=_operands(spec, compilation),
        storage_codecs=storage_codec_census(registrations),
        validate_payload=partial(validate_declared_recursive_input_payload, draft=spec.draft,
            registrations=registrations, fallback_codecs=compilation.output_codecs))
    selections = {operation.selection for operation in compilation.operations}
    ports = tuple(sorted((ExecutablePlatformPort(recursive_input_port_key(selection), RecursiveOperationInputPort(supplier))
                          for selection in selections), key=lambda value: value.port_key))
    if projection.registry_sha256 != compilation.registry.fingerprint():
        raise ValueError('prospective projection changes its frozen registry')
    handoff = RecursiveProspectiveApplicationHandoff(directory, compilation, authoring, context, projection, spec.resources, ports)
    return handoff, (packet, report.candidate, payloads['scientific-projection.json'])


def prove_recursive_prospective_handoff(handoff, *, factory_registry=None):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.api.integration_proof import prove_provider_projection
    resolver = LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()),
                factories=EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY if factory_registry is None else factory_registry)
    provider = resolver.resolve(handoff.compilation.registry, platform_ports=handoff.platform_ports)
    return prove_provider_projection(provider=provider, registry=handoff.compilation.registry, projection=handoff.projection,
                resources=handoff.resources, proof_id=handoff.projection.source_plan.object_id + '.integration-proof')
