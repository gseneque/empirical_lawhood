# SPDX-License-Identifier: MPL-2.0
"""Public bounded E4 programme preflight authoring and authenticated cold load.

These exports are effect-free engineering plans. They are not issued studies,
qualified parents, outcome grants, or a substitute for protected execution.
The explicitly declared four-family population still needs scientific selection
and genuine source, issue, execution and reveal operands before entry.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import (
    NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank, ScheduledCompactCommitmentConfig,
    authenticate_prior_publications, compact_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import (
    MAXIMUM_PROGRAMME_BYTES, ScheduledProgramme, validate_programme_bank,
)
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_relative_locator,
    validate_sha256, validate_stable_id,
)
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

MAXIMUM_PACKAGE_BYTES = 512*1024**2
MAXIMUM_MANIFEST_BYTES = 1024**2


@dataclass(frozen=True, slots=True)
class ScheduledProgrammePackageMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/package-member'
    filename: str
    identity: ObjectIdentity
    size_bytes: int
    sha256: str

    def __post_init__(self):
        validate_relative_locator(self.filename)
        validate_sha256(self.sha256)
        if '/' in self.filename or type(self.size_bytes) is not int or not 0 < self.size_bytes <= MAXIMUM_PROGRAMME_BYTES:
            raise ValueError('programme package member exceeds its closed flat 16MiB carrier')
        if self.identity.object_fingerprint != self.sha256:
            raise ValueError('programme member changes exact identity and content bytes')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeIntegrationProof(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/integration-proof'
    proof_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    wave_plans: tuple[ObjectIdentity, ...]
    logical_task_ids: tuple[str, ...]
    native_task_ids: tuple[str, ...]
    model_parents: tuple[ArtifactWriteResult, ...]
    source_census: tuple[ObjectIdentity, ...]
    effects_blocked: bool
    qualification_disposition: str
    issued_execution_disposition: str
    entry_requirements: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.proof_id)
        for values in (self.logical_task_ids, self.native_task_ids, self.entry_requirements):
            require_sorted_unique_strings(values, field_name='complete programme proof census', allow_empty=False)
        if (self.programme.object_schema != ScheduledProgramme.SCHEMA or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or self.effects_blocked is not True or self.qualification_disposition != 'UNENTERED'
                or self.issued_execution_disposition != 'UNENTERED'):
            raise ValueError('programme preflight proof cannot manufacture execution or scientific qualification')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.proof_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledProgrammePackageManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/package-manifest'
    package_id: str
    programme: ObjectIdentity
    members: tuple[ScheduledProgrammePackageMember, ...]
    aggregate_bytes: int

    def __post_init__(self):
        validate_stable_id(self.package_id)
        names = tuple(m.filename for m in self.members)
        if (self.programme.object_schema != ScheduledProgramme.SCHEMA or names != tuple(sorted(set(names)))
                or self.aggregate_bytes != sum(m.size_bytes for m in self.members)
                or self.aggregate_bytes > MAXIMUM_PACKAGE_BYTES or not {'bank.json', 'programme.json', 'proof.json'} <= set(names)):
            raise ValueError('programme package changes its bounded exact member census')


@dataclass(frozen=True, slots=True)
class LoadedScheduledProgramme:
    """Authenticated preflight; no protected outcome access or native entry."""
    manifest: ScheduledProgrammePackageManifest
    programme: ScheduledProgramme
    bank: ScheduledCompactBank
    proof: ScheduledProgrammeIntegrationProof
    directory: Path


def _authenticate_original_bank(plane, bank):
    # This uses the existing actual-plane hook, including original sidecar,
    # physical hash and canonical-byte checks, not a replacement qualification.
    config = ScheduledCompactCommitmentConfig('config.'+COMPACT_NAMESPACE+'.commit', bank)
    authenticate_prior_publications(plane, (SimpleNamespace(record=config),))


def _authenticate_blind_bank(plane, bank):
    """Authenticate original blind operands without opening a sealed parent."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_global import source_publications
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    for record, publication in source_publications(bank):
        if publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND or publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise PermissionError('programme source preparation requires original blind prospective operands')
        authenticate_publication(plane, publication, record)
    for publication in bank.response_selection.template_publications:
        if publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND or publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise PermissionError('programme source preparation requires original blind fixed instruments')
        authenticate_publication(plane, publication)


def _programme_codecs():
    from empirical_lawhood.adapters.methods.matrix_scheduled_programme.executable_binding import EXECUTABLE_BINDING_FACTORIES
    return {schema: cls for factory in EXECUTABLE_BINDING_FACTORIES for schema, cls in factory.output_codecs.items()}


def _templates(bank, values):
    expected = {p.templates.array_artifact.artifact_id: p.templates.array_artifact for p in bank.response_selection.protocols}
    if set(values) != set(expected):
        raise ValueError('programme preflight changes original complete fixed template census')
    for key, artifact in expected.items():
        raw = values[key]
        if (type(raw) is not bytes or len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256
                or artifact.payload_schema != MATRIX_ARRAY_SCHEMA or len(raw) > MAXIMUM_PROGRAMME_BYTES):
            raise ValueError('programme preflight substitutes original template bytes or bounded array codec')
    return expected


def _proof(programme, bank, plans):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_composition import ScheduledProgrammeWavePlan
    if (tuple(p.wave.wave_id for p in plans) != tuple(w.wave_id for w in programme.waves)
            or any(type(p) is not ScheduledProgrammeWavePlan for p in plans)):
        raise ValueError('programme proof drops or reorders a frozen whole-group wave')
    logical = tuple(sorted({*(operation.node_id for plan in plans for operation in plan.operations),
        COMPACT_NAMESPACE+'.commit', COMPACT_NAMESPACE+'.calibrate', COMPACT_NAMESPACE+'.calibration-qualify'}))
    if len(logical) != len(programme.cases)*11+3:
        raise ValueError('programme proof changes the full original6339 logical stage census')
    native = tuple(sorted(contract.task_id for plan in plans for contract in plan.native_contracts))
    if len(set(native)) != 3*len(programme.cases):
        raise ValueError('programme proof drops or duplicates original native phase slots')
    design = bank.forecast_design
    parents = (design.model_publication, design.training_publication, design.criterion_publication)
    if any(plan.model_parents != parents for plan in plans):
        raise ValueError('programme waves refit or substitute original presealed model parents')
    return ScheduledProgrammeIntegrationProof(programme.programme_id+'.preflight-proof', programme.identity,
        compact_identity(bank), tuple(plan.identity for plan in plans), logical, native, parents,
        programme.source_census, True, 'UNENTERED', 'UNENTERED', tuple(sorted((
            'actual-global-commitment-receipt', 'actual-source-qualification-and-selected-population',
            'genuine-issue-execution-reveal-authority', 'issued-wave-decoder-provider-and-global-qualification'))))


def author_scheduled_programme_preflight(*, programme, bank, wave_plans, template_bytes, artifact_plane, output_directory):
    """Validate and write one explicitly selected bounded public preflight package.

    All wave plans are checked before the first write. Shared scientific inputs
    occur once in the package. This function performs no issue or native call.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_composition import validate_programme_wave
    validate_programme_bank(programme, bank)
    expected_templates = _templates(bank, template_bytes)
    _authenticate_original_bank(artifact_plane, bank)
    plans = tuple(wave_plans)
    for plan in plans:
        validate_programme_wave(plan, programme, bank, template_bytes=template_bytes)
        if len(plan.canonical_bytes()) > MAXIMUM_PROGRAMME_BYTES:
            raise ValueError('bounded operational wave exceeds its closed16MiB carrier; select fewer whole groups')
    proof = _proof(programme, bank, plans)
    records = {'bank.json': (bank, compact_identity(bank)), 'programme.json': (programme, programme.identity),
        'proof.json': (proof, proof.identity)}
    records.update({f'wave.{index:03}.json': (plan, plan.identity) for index, plan in enumerate(plans)})
    payloads = {name: (record.canonical_bytes(), pin) for name, (record, pin) in records.items()}
    payloads.update({f'template.{index:03}.npz': (template_bytes[key], ObjectIdentity(key, artifact.payload_schema,
        '1.0.0', artifact.sha256)) for index, (key, artifact) in enumerate(sorted(expected_templates.items()))})
    members = tuple(ScheduledProgrammePackageMember(name, pin, len(raw), sha256(raw).hexdigest())
        for name, (raw, pin) in sorted(payloads.items()))
    manifest = ScheduledProgrammePackageManifest(programme.programme_id+'.preflight-package', programme.identity,
        members, sum(member.size_bytes for member in members))
    directory = Path(output_directory)
    if directory.exists() or directory.is_symlink():
        raise ValueError('programme preflight output must be a new explicitly selected directory')
    directory.mkdir(parents=True)
    for name, (raw, _) in sorted(payloads.items()):
        with (directory/name).open('xb') as stream:
            stream.write(raw)
    with (directory/'manifest.json').open('xb') as stream:
        stream.write(manifest.canonical_bytes())
    return LoadedScheduledProgramme(manifest, programme, bank, proof, directory)


def load_scheduled_programme_preflight(*, directory, artifact_plane):
    """Cold authenticate every closed member, original publication and wave join."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_composition import ScheduledProgrammeWavePlan, validate_programme_wave
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('programme preflight directory must be an actual selected directory')
    manifest_path = directory/'manifest.json'
    if manifest_path.is_symlink():
        raise ValueError('programme manifest cannot redirect custody')
    manifest = decode_canonical_bytes(read_bounded_bytes(manifest_path, maximum_bytes=MAXIMUM_MANIFEST_BYTES),
        ScheduledProgrammePackageManifest, maximum_bytes=MAXIMUM_MANIFEST_BYTES)
    if set(path.name for path in directory.iterdir()) != {'manifest.json', *(m.filename for m in manifest.members)}:
        raise ValueError('programme preflight has missing or foreign members')
    raw_by_name = {}
    for member in manifest.members:
        path = directory/member.filename
        if path.is_symlink() or not path.is_file():
            raise ValueError('programme member cannot redirect actual custody')
        raw = read_bounded_bytes(path, maximum_bytes=member.size_bytes)
        if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.sha256:
            raise ValueError('programme member changes exact actual bytes, size or hash')
        raw_by_name[member.filename] = raw
    types = {'bank.json': ScheduledCompactBank, 'programme.json': ScheduledProgramme,
        'proof.json': ScheduledProgrammeIntegrationProof}
    records, templates = {}, {}
    for member in manifest.members:
        cls = types.get(member.filename)
        if member.filename.startswith('wave.') and member.filename.endswith('.json'):
            cls = ScheduledProgrammeWavePlan
        if cls is not None:
            if (member.identity.object_schema, member.identity.object_version) != (cls.SCHEMA, cls.VERSION):
                raise ValueError('programme member substitutes an unsupported schema or revision')
            value = decode_canonical_bytes(raw_by_name[member.filename], cls, maximum_bytes=MAXIMUM_PROGRAMME_BYTES)
            pin = compact_identity(value) if cls is ScheduledCompactBank else value.identity
            if pin != member.identity or value.canonical_bytes() != raw_by_name[member.filename]:
                raise ValueError('programme member changes exact canonical record identity')
            records[member.filename] = value
        elif member.filename.startswith('template.') and member.filename.endswith('.npz'):
            if (member.identity.object_schema, member.identity.object_version) != (MATRIX_ARRAY_SCHEMA, '1.0.0'):
                raise ValueError('programme template changes its exact closed array codec')
            templates[member.identity.object_id] = raw_by_name[member.filename]
        else:
            raise ValueError('programme package member lies outside its closed codec allowlist')
    bank, programme, proof = records['bank.json'], records['programme.json'], records['proof.json']
    if manifest.programme != programme.identity:
        raise ValueError('programme package manifest substitutes its frozen whole programme')
    validate_programme_bank(programme, bank)
    expected_templates = _templates(bank, templates)
    expected_names = {'bank.json', 'programme.json', 'proof.json',
        *(f'wave.{i:03}.json' for i in range(len(programme.waves))),
        *(f'template.{i:03}.npz' for i in range(len(expected_templates)))}
    if {m.filename for m in manifest.members} != expected_names:
        raise ValueError('programme cold load changes its exact frozen wave/template member census')
    _authenticate_original_bank(artifact_plane, bank)
    plans = tuple(records[f'wave.{i:03}.json'] for i in range(len(programme.waves)))
    for plan in plans:
        validate_programme_wave(plan, programme, bank, template_bytes=templates)
    if _proof(programme, bank, plans) != proof:
        raise ValueError('programme cold load changes original task/native/model-parent closure')
    return LoadedScheduledProgramme(manifest, programme, bank, proof, directory)


def _actual_programme_entry(programme, bank, artifact_plane, global_parent_binding, wave_custody=(), qualified_parent=None):
    """Validate entry and return its fresh authenticated confirmation parent."""
    validate_programme_bank(programme, bank)
    confirmation = programme.mode == 'E4_CONFIRMATION'
    authenticated_parent = None
    if confirmation:
        from empirical_lawhood.api.matrix_scheduled_programme_runtime import authenticate_programme_qualified_parent
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_qualified_parent import validate_qualified_parent_declaration
        validate_qualified_parent_declaration(bank, qualified_parent)
        _authenticate_blind_bank(artifact_plane, bank)
        authenticated_parent = authenticate_programme_qualified_parent(artifact_plane, bank, qualified_parent, _programme_codecs())
    elif qualified_parent is not None or bank.forecast_design.calibration is not None:
        raise ValueError('uncalibrated programme cannot alias a protected qualified parent')
    else:
        _authenticate_original_bank(artifact_plane, bank)
    if global_parent_binding is not None:
        if confirmation:
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import authenticate_confirmation_parent
            parent = authenticate_confirmation_parent(artifact_plane, global_parent_binding)
            if global_parent_binding.configuration.qualified_parent != qualified_parent:
                raise ValueError('programme entry changes its authenticated original qualified-parent declaration')
        else:
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_parent import authenticate_global_parent
            parent = authenticate_global_parent(artifact_plane, global_parent_binding)
        if parent.programme != programme.identity or parent.bank != programme.bank:
            raise ValueError('programme entry substitutes its actual global parent scientific scope')
    if wave_custody:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration import (
            ScheduledProgrammeWaveCustody, authenticate_wave_custody_metadata,
        )
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_custody import (
            ScheduledProgrammeAcquisitionWaveCustody, authenticate_acquisition_wave_custody_metadata,
        )
        if (type(wave_custody) is not tuple or len(wave_custody) != len(programme.waves)
                or any(type(value) not in (ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody) for value in wave_custody)
                or len({type(value) for value in wave_custody}) != 1
                or tuple(value.wave_id for value in wave_custody) != tuple(w.wave_id for w in programme.waves)
                or any(value.configuration.programme != programme.identity or value.configuration.bank != programme.bank
                    or value.configuration.wave != wave for value, wave in zip(wave_custody, programme.waves, strict=True))):
            raise ValueError('programme tail entry changes its complete frozen original wave custody corpus')
        for binding in wave_custody:
            if type(binding) is ScheduledProgrammeAcquisitionWaveCustody:
                authenticate_acquisition_wave_custody_metadata(artifact_plane, binding, programme=programme)
            else:
                authenticate_wave_custody_metadata(artifact_plane, binding, programme=programme)
    return authenticated_parent


def _assert_actual_declaration(draft, programme, bank, global_parent_binding, wave_custody=(), qualified_parent=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_global import ScheduledProgrammeGlobalCommitConfig
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_bindings import ScheduledProgrammeWaveAdmissionConfig
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration import ScheduledProgrammeCalibrationConfig
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import ScheduledProgrammeConfirmationGlobalConfig
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import ScheduledProgrammeAcquisitionAdmissionConfig
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_tail_freeze import ScheduledProgrammeTailFreezeConfig, TASK_ID as TAIL_FREEZE_TASK_ID
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import (
        ScheduledFactorialCriteriaConfig, ScheduledFactorialConfirmationConfig, ScheduledFactorialConfirmationSealConfig,
    )
    factorial_types = (ScheduledFactorialCriteriaConfig, ScheduledFactorialConfirmationConfig, ScheduledFactorialConfirmationSealConfig)
    declarations = []
    for operation in draft.operations:
        schema = operation.config_identity.object_schema
        cls = {value.SCHEMA: value for value in (ScheduledProgrammeGlobalCommitConfig, ScheduledProgrammeWaveAdmissionConfig,
            ScheduledProgrammeCalibrationConfig, ScheduledProgrammeConfirmationGlobalConfig,
            ScheduledProgrammeAcquisitionAdmissionConfig, ScheduledProgrammeTailFreezeConfig, *factorial_types)}.get(schema)
        if cls is not None:
            declarations.append(decode_canonical_bytes(operation.config_payload.encode(), cls,
                maximum_bytes=(16 if cls in factorial_types else 4)*1024**2))
            if cls is ScheduledProgrammeTailFreezeConfig and operation.node_id != TAIL_FREEZE_TASK_ID:
                raise ValueError('programme tail changes its actual metadata freeze task identity')
    factorial = tuple(value for value in declarations if type(value) in factorial_types)
    if factorial:
        selected = tuple(value for value in factorial if type(value) is not ScheduledFactorialConfirmationSealConfig)
        count = 1 if len(selected) == 1 and type(selected[0]) is ScheduledFactorialCriteriaConfig else 2
        if (len(selected) != 1 or len(factorial) != count or len(declarations) != count or len(draft.operations) != count
                or global_parent_binding is not None or wave_custody
                or any(value.programme != programme or value.bank != programme.bank for value in factorial)):
            raise ValueError('protected factorial entry changes its exact criteria phase or sealed confirmation pair')
        config = selected[0]
        expected_parent = (config.qualified_parent if type(config) is ScheduledFactorialCriteriaConfig
            else config.criteria.record.configuration.qualified_parent)
        if qualified_parent != expected_parent:
            raise ValueError('protected factorial entry changes its original qualified calibration parent')
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation_composition import validate_factorial_prospective_draft
        from empirical_lawhood.kernel.references import ArtifactIdentity
        bank_artifact = ArtifactIdentity(programme.bank.object_id, 'original-compact-bank', bank.SCHEMA,
            bank.fingerprint(), 'application/json', len(bank.canonical_bytes()))
        validate_factorial_prospective_draft(config, draft, bank_artifact)
        return
    calibrations = tuple(value for value in declarations if type(value) is ScheduledProgrammeCalibrationConfig)
    freezes = tuple(value for value in declarations if type(value) is ScheduledProgrammeTailFreezeConfig)
    if calibrations:
        pins = tuple(value.identity for value in wave_custody)
        if (len(declarations) != 3 or len(calibrations) != 2 or len(freezes) != 1
                or {value.operation for value in calibrations} != {'calibrate', 'calibration-qualify'}
                or global_parent_binding is not None or not wave_custody
                or len({value.calibration_id for value in calibrations}) != 1
                or any(value.programme != programme or value.bank != programme.bank or value.wave_custody != pins for value in declarations)):
            raise ValueError('programme tail entry omits its exact actual global pair or original custody pins')
        return
    if wave_custody or len(declarations) != 1 or declarations[0].programme != programme or declarations[0].bank != programme.bank:
        raise ValueError('programme entry lacks its exact actual bounded global/wave declaration')
    if type(declarations[0]) is ScheduledProgrammeAcquisitionAdmissionConfig:
        if (global_parent_binding is None or declarations[0].global_parent_binding != global_parent_binding
                or declarations[0].scope.qualified_parent != qualified_parent):
            raise ValueError('programme acquisition changes its actual mode-specific parent or original qualification')
    elif type(declarations[0]) is ScheduledProgrammeWaveAdmissionConfig:
        if (global_parent_binding is None or declarations[0].required_global_parent != global_parent_binding.parent.identity
                or declarations[0].global_parent_binding != global_parent_binding
                or declarations[0].global_parent_publication != global_parent_binding.publication
                or declarations[0].global_parent_receipt != ObjectIdentity.from_record(global_parent_binding.receipt.receipt_id,
                    global_parent_binding.receipt)):
            raise ValueError('programme wave entry omits its actual successful global receipt/publication binding')
    elif global_parent_binding is not None:
        raise ValueError('global preparation entry cannot alias a wave parent requirement')
    elif type(declarations[0]) is ScheduledProgrammeConfirmationGlobalConfig and declarations[0].qualified_parent != qualified_parent:
        raise ValueError('confirmation global entry changes its actual original qualified-parent declaration')


def author_scheduled_programme_prospective(*, programme, bank, global_parent_binding=None, wave_custody=(), qualified_parent=None, **arguments):
    """Authenticate programme prerequisites then use the unchanged standard API.

    This still authors a candidate. Actual issue, native execution and reveal
    retain the standard authority boundaries and are not performed here.
    """
    from empirical_lawhood.api.recursive_prospective_authoring import author_recursive_prospective
    from empirical_lawhood.runtime.recursive_prospective_envelope import RecursiveProspectiveAuthoringEnvelope, RecursiveProspectiveAuthoringEnvelopeV3, RecursiveProspectiveAuthoringEnvelopeV4
    spec = arguments['spec'].reconstruct() if type(arguments['spec']) in (RecursiveProspectiveAuthoringEnvelope, RecursiveProspectiveAuthoringEnvelopeV3, RecursiveProspectiveAuthoringEnvelopeV4) else arguments['spec']
    _assert_actual_declaration(spec.draft, programme, bank, global_parent_binding, wave_custody, qualified_parent)
    _actual_programme_entry(programme, bank, arguments['artifact_writer'], global_parent_binding, wave_custody, qualified_parent)
    return author_recursive_prospective(**arguments)


def load_scheduled_programme_prospective(*, programme, bank, global_parent_binding=None, wave_custody=(), qualified_parent=None, runtime_reveal_authority_id=None, **arguments):
    """Cold authenticate the actual programme and standard retained handoff."""
    from empirical_lawhood.api.recursive_prospective_authoring import load_recursive_prospective_handoff
    _actual_programme_entry(programme, bank, arguments['artifact_writer'], global_parent_binding, wave_custody, qualified_parent)
    handoff = load_recursive_prospective_handoff(**arguments)
    _assert_actual_declaration(handoff.compilation.draft, programme, bank, global_parent_binding, wave_custody, qualified_parent)
    from empirical_lawhood.api.matrix_scheduled_programme_runtime import bind_programme_runtime_handoff
    return bind_programme_runtime_handoff(handoff, writer=arguments['artifact_writer'], reveal_authority_id=runtime_reveal_authority_id)
