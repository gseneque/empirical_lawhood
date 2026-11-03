# SPDX-License-Identifier: MPL-2.0
"""Original experiment custody through the existing prospective author/loader.

The original fourteen-member handoff remains closed and unchanged. Its companion
retains one copy of the selected design and commits their association last.
"""

from contextlib import contextmanager, nullcontext
from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.source_closure import capture_target_closure
from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding, ExperimentPreparation
from empirical_lawhood.runtime.input_payloads import InputBytes
from empirical_lawhood.runtime.progress import report_progress
from empirical_lawhood.runtime.prospective_experiment import (
    ALLOCATION_FILENAME, ASSOCIATION_FILENAME, INSTANCE_FILENAME, SPECIFICATION_FILENAME,
    PreparedProspectiveExperimentHandoff, ProspectiveExperimentAssociation, instance_identity, source_filename,
)
from empirical_lawhood.runtime.recursive_compiler import derive_recursive_scientific_selection
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveDesignInputs
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

from .experiment_runtime_bindings import experiment_runtime_binding


_CONTROL_BYTES = 1024**2


def _directory(directory, writer):
    path = Path(directory)
    if ".." in path.parts or any(value.is_symlink() for value in (path, *path.parents)):
        raise ValueError("prospective experiment custody refuses traversal and symbolic links")
    path = path.resolve(strict=True)
    root = Path(writer.root.contract.canonical_path)
    if not path.is_dir() or not path.is_relative_to(root):
        raise ValueError("prospective experiment custody lies outside its selected guarded root")
    writer.root.verify(for_write=False)
    writer.root.resolve(path.relative_to(root).as_posix(), for_write=False)
    return path


def _read_prospective_locator(directory, name, writer, kind, *, expected=None):
    """Partial exact metadata proof; never hash publication siblings here."""
    from empirical_lawhood.runtime.artifacts import artifact_custody_limits
    path = directory / name
    if any(value.is_symlink() for value in (path, path.with_name(name + ".manifest.json"))):
        raise ValueError("prospective locator metadata refuses symbolic links")
    relative = path.relative_to(Path(writer.root.contract.canonical_path)).as_posix()
    manifest = writer.read_manifest(relative)
    logical, material = manifest.logical, manifest.materialization
    limits = artifact_custody_limits(writer)
    if (material.relative_path != relative or material.storage_root_id != writer.root.contract.storage_root_id
            or logical.payload_schema != kind.SCHEMA or logical.profile is not ArtifactProfile.CANONICAL_JSON
            or logical.media_type != "application/json" or logical.lineage_parents
            or logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or material.compression != "none" or material.partition_selector is not None
            or limits.exceeds("in_memory_payload_bytes", material.size_bytes)
            or limits.exceeds("control_record_bytes", material.size_bytes)):
        raise PermissionError("prospective bootstrap requires exact unprivileged locator metadata")
    if expected is not None and (expected.size_bytes != material.size_bytes
            or expected.identity.object_fingerprint != logical.content_sha256
            or (expected.identity.object_schema, expected.identity.object_version) != (kind.SCHEMA, kind.VERSION)):
        raise PermissionError("prospective bootstrap changes its exact companion-pinned locator")
    raw = read_bounded_bytes(path, maximum_bytes=material.size_bytes)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=material.size_bytes)
    if (record.canonical_bytes() != raw or len(raw) != material.size_bytes
            or sha256(raw).hexdigest() != logical.content_sha256
            or sha256(raw).hexdigest() != material.physical_sha256
            or expected is not None and ObjectIdentity.from_record(expected.identity.object_id, record) != expected.identity):
        raise PermissionError("prospective bootstrap changes its exact canonical locator bytes")
    # Exact physical verification only; complete sibling publication is deferred until access.
    writer.verify(material)
    return record


def _source_provenance_member_facts(*, writer, packet, directory):
    """Exact source controls; canonical scientific payloads gain no admission.

    The selected-source manifest has its independent closure pin. The source
    observation is an intrinsic operational disclosure at its deterministic
    committed role; the unchanged retained parser still decodes and joins its
    entire closure/manifest/observation body before returning any result.
    """
    from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
    from empirical_lawhood.runtime.artifacts import artifact_custody_limits, artifact_publication_member
    from empirical_lawhood.api.recursive_prospective_authoring import ProspectiveSourceObservation
    from empirical_lawhood.planning.study_issue import SelectedSourceManifest

    if type(packet) is not AuthoredRecursiveWave:
        raise TypeError("source provenance bootstrap requires its exact authenticated packet")
    packet.__post_init__()
    selected = _directory(directory, writer)
    prospective = _directory(selected / "prospective", writer)
    matches = tuple(member for member in packet.members if member.filename == "source-closure.json")
    if len(matches) != 1:
        raise PermissionError("source provenance bootstrap omits its exact closure member")
    member, = matches
    closure = _read_prospective_locator(prospective, member.filename, writer,
        ImplementationSourceClosure, expected=member)
    if packet.implementation != ObjectIdentity.from_record("recursive-member.implementation", closure):
        raise PermissionError("source provenance bootstrap substitutes its packet implementation closure")
    if closure.kind is SourceClosureKind.CLEAN_GIT_COMMIT:
        return frozenset()
    if closure.kind is not SourceClosureKind.EXACT_SOURCE_CLOSURE:
        raise PermissionError("source provenance bootstrap changes its supported closure kind")
    if (type(closure.exact_source_manifest) is not ObjectIdentity
            or (closure.exact_source_manifest.object_schema, closure.exact_source_manifest.object_version)
                != (SelectedSourceManifest.SCHEMA, SelectedSourceManifest.VERSION)):
        raise PermissionError("source provenance bootstrap changes its selected manifest codec")
    relative_root = (prospective / "provenance").relative_to(writer.root.contract.canonical_path).as_posix()
    scope_id = closure.source_closure_id + ".provenance"
    limits = artifact_custody_limits(writer)
    facts = []
    for name, kind in (("selected-source-manifest.json", SelectedSourceManifest),
            ("source-observation.json", ProspectiveSourceObservation)):
        relative = relative_root + "/" + name
        manifest = writer.read_manifest(relative)
        actual = read_publication_metadata(writer, manifest)
        logical, physical = actual.logical, actual.materialization
        if (physical.relative_path != relative or physical.storage_root_id != writer.root.contract.storage_root_id
                or physical.size_bytes <= 0 or limits.exceeds("control_record_bytes", physical.size_bytes)
                or limits.exceeds("in_memory_payload_bytes", physical.size_bytes)
                or logical.payload_schema != kind.SCHEMA or logical.profile is not ArtifactProfile.CANONICAL_JSON
                or logical.media_type != "application/json" or logical.lineage_parents or logical.parent_visibility_ceilings
                or logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or logical.content_sha256 != physical.physical_sha256
                or logical.logical_artifact_id != scope_id + "." + name.removesuffix(".json")
                or physical.compression != "none" or physical.partition_selector is not None
                or actual.publication is None
                or actual.publication.publication_scope.publication_scope_id != scope_id
                or actual.publication.publication_scope.relative_root != relative_root
                or actual.publication.members != (artifact_publication_member(logical, physical),)):
            raise PermissionError("source provenance bootstrap substitutes an exact closed publication role")
        if name == "selected-source-manifest.json" and (
                logical.payload_schema, logical.content_sha256) != (
                    closure.exact_source_manifest.object_schema, closure.exact_source_manifest.object_fingerprint):
            raise PermissionError("source provenance bootstrap changes its closure-pinned selected manifest")
        facts.append((logical, physical))
    return frozenset(facts)


def _bootstrap_prospective_original_inputs(*, directory, artifact_writer, read_access=None):
    from .experiment_preparation import experiment_protocols
    selected = _directory(directory, artifact_writer)
    companion = _directory(selected / "experiment", artifact_writer)
    association = _read_prospective_locator(companion, ASSOCIATION_FILENAME, artifact_writer,
        ProspectiveExperimentAssociation)
    members = {member.filename: member for member in association.members}
    instance = _read_prospective_locator(companion, INSTANCE_FILENAME, artifact_writer,
        ExperimentInstanceBinding, expected=members[INSTANCE_FILENAME])
    if association.instance != instance_identity(instance):
        raise PermissionError("prospective bootstrap substitutes its original instance association")
    declarations = tuple(value for value in experiment_protocols()
        if (value.specification_type.SCHEMA, value.specification_type.VERSION) ==
            (instance.specification.object_schema, instance.specification.object_version))
    if len(declarations) != 1:
        raise ValueError("prospective bootstrap lacks one exact installed specification owner")
    declaration, = declarations
    binding = experiment_runtime_binding(declaration)
    callback = None if binding is None else binding.bootstrap_prospective_input_access
    if callback is None:
        if read_access is not None:
            raise ValueError("selected prospective experiment has no original-access bootstrap")
        return None
    specification = _read_prospective_locator(companion, SPECIFICATION_FILENAME, artifact_writer,
        declaration.specification_type, expected=members[SPECIFICATION_FILENAME])
    if specification.identity != instance.specification:
        raise PermissionError("prospective bootstrap substitutes its exact original specification")

    def read_member(reference, kind):
        if (type(reference) is not ObjectIdentity or reference not in instance.sources
                or kind not in binding.prospective_bootstrap_record_types
                or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION)):
            raise PermissionError("prospective bootstrap refuses an undeclared locator codec or identity")
        member = members.get(source_filename(reference))
        if member is None or member.identity != reference:
            raise PermissionError("prospective bootstrap changes its exact companion source roster")
        return _read_prospective_locator(companion, member.filename, artifact_writer, kind, expected=member)

    guard = callback(directory=selected, artifact_writer=artifact_writer, specification=specification,
        instance=instance, association=association, read_member=read_member, read_access=read_access)
    if (guard is None or type(getattr(guard, "parents", None)) is not tuple
            or not callable(getattr(guard, "require_current", None))
            or not callable(getattr(guard, "require_issued_member", None))
            or not callable(getattr(guard, "record_parents", None))):
        raise TypeError("prospective bootstrap requires its code-owned issued original-access context")
    if guard.require_current() is not None:
        raise ValueError("prospective original-access guard must return None or raise")
    if not callable(getattr(guard, "bind_issued_members", None)):
        raise TypeError("prospective original-access scope lacks its closed-member binder")
    prospective = _directory(selected / "prospective", artifact_writer)
    packet = _read_prospective_locator(prospective, "authored-wave.json", artifact_writer, AuthoredRecursiveWave)
    if ObjectIdentity.from_record(packet.packet_id, packet) != association.prospective_wave:
        raise PermissionError("prospective bootstrap substitutes its association-pinned authored packet")
    manifests = []
    for base, rows in ((companion, association.members), (prospective, packet.members)):
        for member in rows:
            path = base / member.filename
            relative = path.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
            manifest = artifact_writer.read_manifest(relative)
            logical, material = manifest.logical, manifest.materialization
            if (material.relative_path != relative
                    or material.storage_root_id != artifact_writer.root.contract.storage_root_id
                    or material.size_bytes != member.size_bytes
                    or logical.content_sha256 != member.identity.object_fingerprint
                    or material.physical_sha256 != member.identity.object_fingerprint
                    or logical.payload_schema != member.identity.object_schema
                    or logical.profile is not ArtifactProfile.CANONICAL_JSON
                    or logical.media_type != "application/json" or material.compression != "none"
                    or material.partition_selector is not None):
                raise PermissionError("prospective bootstrap changes an exact closed-member publication pin")
            manifests.append(manifest)
    for base, name, record in ((companion, ASSOCIATION_FILENAME, association),
            (prospective, "authored-wave.json", packet)):
        relative = (base / name).relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
        manifests.append(artifact_writer.read_manifest(relative))
    bound = guard.bind_issued_members(tuple(manifests), packet=packet, association=association)
    if (bound is None or bound.parents != guard.parents
            or not callable(getattr(bound, "require_issued_member", None))):
        raise TypeError("prospective closed-member binder changes its original scope")
    if bound.require_current() is not None:
        raise ValueError("prospective original-access guard must return None or raise")
    if not callable(getattr(bound, "bind_source_provenance", None)):
        raise TypeError("prospective original-access scope lacks its exact source-provenance binder")
    source_bound = bound.bind_source_provenance(packet=packet, directory=selected)
    if (source_bound is None or source_bound.parents != bound.parents
            or not callable(getattr(source_bound, "require_issued_member", None))):
        raise TypeError("prospective source-provenance binder changes its original scope")
    if source_bound.require_current() is not None:
        raise ValueError("prospective original-access guard must return None or raise")
    return source_bound


def _require_original_inputs(access):
    if access is not None and access.require_current() is not None:
        raise ValueError("prospective original-access guard must return None or raise")


def _original_input_scope(writer, access):
    options = {} if access is None else {"before_member": access.require_issued_member}
    return nullcontext(writer) if access is None else writer.read_context(**options)


def _read(directory, name, writer, *, maximum, schema=None, original_input_access=None):
    """Reauthenticate one selected publication and its exact physical bytes."""
    path = directory / name
    if any(value.is_symlink() for value in (path, path.with_name(name + ".manifest.json"))):
        raise ValueError("prospective experiment member refuses symbolic links")
    manifest = decode_artifact_manifest(read_bounded_bytes(path.with_name(name + ".manifest.json"), maximum_bytes=_CONTROL_BYTES))
    material = manifest.materialization
    logical = manifest.logical
    if (material.relative_path != path.relative_to(Path(writer.root.contract.canonical_path)).as_posix()
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"
            or original_input_access is None and (logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE)
            or maximum is not None and material.size_bytes > maximum
            or schema is not None and logical.payload_schema != schema):
        raise ValueError("prospective experiment member changes its exact path, access, schema or allocation")
    options = {} if original_input_access is None else {"before_member": original_input_access.require_issued_member}
    writer.verify_manifest(manifest, **options)
    _require_original_inputs(original_input_access)
    raw = read_bounded_bytes(path, maximum_bytes=material.size_bytes)
    digest = sha256(raw).hexdigest()
    if (len(raw), digest, digest) != (material.size_bytes, material.physical_sha256, logical.content_sha256):
        raise ValueError("prospective experiment member changes its authenticated physical bytes")
    _require_original_inputs(original_input_access)
    return raw


def _prospective_roots(directory, writer, *, original_input_access=None, _retained=None):
    from .recursive_prospective_authoring import _AuthoredProspectiveRoots, _prospective_member_codec, _prospective_selection_decoder

    if _retained is not None and type(_retained) is not _AuthoredProspectiveRoots:
        raise TypeError("prospective roots require the owning author's immutable objects")
    packet_raw = _read(directory, "authored-wave.json", writer,
        maximum=_CONTROL_BYTES, schema=AuthoredRecursiveWave.SCHEMA, original_input_access=original_input_access)
    if _retained is None:
        packet = decode_canonical_bytes(packet_raw, AuthoredRecursiveWave, maximum_bytes=_CONTROL_BYTES)
    else:
        packet = _retained.packet
        if type(packet) is not AuthoredRecursiveWave or packet.canonical_bytes() != packet_raw:
            raise PermissionError("prospective authoring changes its freshly authenticated packet bytes")
    decoder, _ = _prospective_selection_decoder(packet,
        lambda name, maximum, expected_schema: _read(directory, name, writer, maximum=maximum, schema=expected_schema, original_input_access=original_input_access))
    values = {}
    for name, kind in (("implementation.json", ImplementationSourceClosure),
            ("candidate.json", ExecutableStudyCandidate), ("scientific-projection.json", None)):
        member = next(row for row in packet.members if row.filename == name)
        _, bound = _prospective_member_codec(member, decoder_registration=decoder)
        if kind is not None and (member.identity.object_schema, member.identity.object_version) != (kind.SCHEMA, kind.VERSION):
            raise ValueError("prospective experiment substitutes its exact source closure or outer candidate revision")
        raw = _read(directory, name, writer, maximum=bound, schema=member.identity.object_schema, original_input_access=original_input_access)
        if (len(raw), sha256(raw).hexdigest()) != (member.size_bytes, member.identity.object_fingerprint):
            raise ValueError("prospective experiment differs from its committed handoff member")
        values[name] = raw
    if _retained is None:
        candidate = decode_canonical_bytes(values["candidate.json"], ExecutableStudyCandidate, maximum_bytes=len(values["candidate.json"]))
        closure = decode_canonical_bytes(values["implementation.json"], ImplementationSourceClosure, maximum_bytes=len(values["implementation.json"]))
    else:
        candidate, closure = _retained.candidate, _retained.implementation
        if (type(candidate) is not ExecutableStudyCandidate or type(closure) is not ImplementationSourceClosure
                or candidate.canonical_bytes() != values["candidate.json"]
                or closure.canonical_bytes() != values["implementation.json"]
                or _retained.scientific_projection.canonical_bytes() != values["scientific-projection.json"]):
            raise PermissionError("prospective authoring changes its freshly authenticated root bytes")
    if packet.implementation != ObjectIdentity.from_record("recursive-member.implementation", closure):
        raise ValueError("prospective experiment changes its original implementation source-closure role or identity")
    return packet, candidate, values["scientific-projection.json"]


def _authenticate_instance(payloads, draft, projection, *, artifact_writer):
    # One existing owner performs codec, exact design/projection and registered
    # scientific rederivation checks at both authoring and cold-load boundaries.
    from empirical_lawhood.api.recursive_authoring import _authenticate_experiment_instance

    return _authenticate_experiment_instance(payloads={**payloads, "scientific-projection.json": projection},
        draft=draft, artifact_writer=artifact_writer)


def _design(preparation, projection, *, artifact_writer):
    references = tuple(ObjectIdentity.from_record(key, record) for key, record in preparation.design_records)
    instance = ExperimentInstanceBinding(preparation.specification, preparation.allocation.identity,
        ObjectIdentity.from_record(preparation.draft.draft_id, preparation.draft),
        ObjectIdentity.from_record("recursive-member.scientific-projection", projection),
        ObjectIdentity.from_record(preparation.draft.campaign.campaign_id, preparation.draft.campaign), references)
    records = {SPECIFICATION_FILENAME: preparation.specification_record, ALLOCATION_FILENAME: preparation.allocation,
        INSTANCE_FILENAME: instance, **{source_filename(ref): record for ref, (_, record)
            in zip(references, preparation.design_records, strict=True)}}
    payloads = {name: record.canonical_bytes() for name, record in records.items()}
    _authenticate_instance(payloads, preparation.draft, projection.canonical_bytes(), artifact_writer=artifact_writer)
    identities = {SPECIFICATION_FILENAME: preparation.specification, ALLOCATION_FILENAME: preparation.allocation.identity,
        INSTANCE_FILENAME: instance_identity(instance),
        **{source_filename(ref): ref for ref in references}}
    members = tuple(RecursiveWaveMember(name, identities[name], len(payload)) for name, payload in sorted(payloads.items()))
    return instance, records, members


def _inputs(preparation, spec, source_configs):
    configs = {payload.sha256: payload for row in source_configs for payload in (InputBytes.from_record(row),)}
    projection = derive_recursive_scientific_selection(spec.draft)
    external = {row.input_id: row for row in projection.external_inputs if not row.parent_substitution}
    records, files = dict(preparation.input_records), dict(preparation.input_files)
    payloads = {}
    if set(records) | set(files) != set(external):
        raise ValueError("prospective experiment must bind every selected ordinary external input exactly once")
    operands = {row.logical_artifact_id: row for row in spec.external_operands}
    logical_ids = [row.logical_artifact_id for row in external.values()]
    if len(set(logical_ids)) != len(logical_ids) or set(logical_ids) != set(operands) or set(logical_ids) & set(configs):
        raise ValueError("prospective experiment aliases external IDs, logical artifacts or source-config SHA keys")
    for key, selected in external.items():
        operand = operands[selected.logical_artifact_id]
        if (operand.content_sha256 != selected.expected_content_sha256 or operand.payload_schema != selected.payload_schema
                or operand.media_type != selected.media_type or operand.outcome_access is not selected.outcome_access
                or operand.visibility_ceiling is not selected.visibility_ceiling
                or selected.maximum_size_bytes is not None and operand.size_bytes > selected.maximum_size_bytes):
            raise ValueError("prospective experiment physical operand differs from its exact selected external contract")
        if key in records:
            payload = InputBytes.from_record(records[key])
            if (payload.size_bytes, payload.sha256, records[key].SCHEMA) != (operand.size_bytes, operand.content_sha256, operand.payload_schema):
                raise ValueError("prospective experiment canonical source differs from its original exact operand")
            payloads[key] = payload
        else:
            value = files[key]
            if ((value.identity.artifact_id, value.identity.sha256, value.identity.size_bytes,
                    value.identity.payload_schema, value.identity.media_type)
                    != (operand.logical_artifact_id, operand.content_sha256, operand.size_bytes,
                        operand.payload_schema, operand.media_type)
                    or ".." in value.path.parts or any(path.is_symlink() for path in (value.path, *value.path.parents))):
                raise ValueError("prospective experiment file differs from its exact operand or safe selected path")
    return external, payloads, files, configs


@contextmanager
def _input_bindings(*, external, sources, files, configs, custody_root, draft):
    # The existing prospective owner supplies selected operation configuration
    # bytes by their exact digest. A scientific external may reference those
    # same immutable bytes (for example a prior phase's preparation contract).
    # Retain that external and its qualification, without a duplicate file
    # binding that the original owner's closed input census rightly refuses.
    automatic = {operation.config_identity.object_fingerprint: operation.config_payload.encode()
        for operation in draft.operations if operation.node_id in draft.selected_operation_ids}
    bindings = [(external[key].logical_artifact_id, value.path) for key, value in files.items()
        if value.identity.sha256 not in automatic]
    for key, record in sources.items():
        payload = record if type(record) is InputBytes else InputBytes.from_record(record)
        original = automatic.get(payload.sha256)
        if original is not None:
            if original != payload.payload:
                raise ValueError("prospective configuration alias changes exact selected canonical bytes")
            continue
        bindings.append((external[key].logical_artifact_id, payload))
    for digest, record in configs.items():
        payload = record if type(record) is InputBytes else InputBytes.from_record(record)
        bindings.append((digest, payload))
    yield tuple(bindings)


def preview_prepared_prospective_experiment_candidate(*, preparation, design_inputs, source_configs,
        project_root, artifact_writer, composition=None, api_factory=None, candidate_catalog=None,
        read_access=None, original_input_access=None):
    """Preview through the original owner without fabricating a bound specification."""
    from .experiment_preparation import _validate_prepared_input_files
    from .recursive_prospective_authoring import preview_recursive_prospective_candidate

    if type(preparation) is not ExperimentPreparation or type(design_inputs) is not RecursiveProspectiveDesignInputs:
        raise TypeError("prospective preview needs exact prepared inputs and resource-free design")
    preparation.__post_init__()
    design_inputs.__post_init__()
    _require_original_inputs(original_input_access)
    if read_access is not None and original_input_access is None:
        raise ValueError("prospective preview requires its registered original-access scope")
    _validate_prepared_input_files(preparation)
    _require_original_inputs(original_input_access)
    if (preparation.execution is None or preparation.draft != design_inputs.draft
            or preparation.execution.output_root is None
            or Path(preparation.execution.output_root).resolve() != Path(artifact_writer.root.contract.canonical_path)):
        raise ValueError("prospective preview changes its exact prepared draft or selected guarded custody")
    if (type(source_configs) is not tuple or any(type(row) is not SourceMaterializationConfig for row in source_configs)
            or tuple(row.fingerprint() for row in source_configs) != tuple(sorted({row.source_config_sha256
                for row in design_inputs.draft.prospective_draft.source_materializations}))):
        raise ValueError("prospective preview changes its exact selected SHA-keyed source configuration roster")
    captured = capture_target_closure(Path(project_root), design_inputs.spec_id + ".source-closure")
    closure = _selected_source_closure(captured.closure, preparation.execution.source_snapshot)
    if GitStudySourceClosureInspector(Path(project_root)).observe(closure) != closure:
        raise ValueError("prospective preview changes its selected producing source")
    external, sources, files, configs = _inputs(preparation, design_inputs, source_configs)
    with _input_bindings(external=external, sources=sources, files=files, configs=configs,
            custody_root=artifact_writer.root.contract.canonical_path, draft=design_inputs.draft) as bindings:
        preview = preview_recursive_prospective_candidate(design_inputs=design_inputs, project_root=project_root,
            artifact_writer=artifact_writer, input_bindings=bindings, composition=composition,
            api_factory=api_factory, candidate_catalog=candidate_catalog, retained_closure=closure,
            original_input_access=original_input_access)
    _require_original_inputs(original_input_access)
    if preparation.execution.source_snapshot != ObjectIdentity.from_record("recursive-member.implementation", preview.implementation):
        raise ValueError("prospective preview differs from the actual selected implementation source closure")
    return preview


def _selected_source_closure(closure, snapshot):
    """Recover only the already pinned canonical raw-clean observation bit."""
    if (type(closure) is not ImplementationSourceClosure or closure.kind is not SourceClosureKind.EXACT_SOURCE_CLOSURE
            or type(snapshot) is not ObjectIdentity):
        raise ValueError("prospective source selection requires its exact retained implementation identity")
    choices = (closure, replace(closure, clean_worktree=not closure.clean_worktree))
    matches = tuple(value for value in choices if ObjectIdentity.from_record("recursive-member.implementation", value) == snapshot)
    if len(matches) != 1:
        raise ValueError("prospective source snapshot differs from every exact retained selected-source closure")
    return matches[0]


def author_prepared_prospective_experiment(*, preparation: ExperimentPreparation,
        prospective_spec: RecursiveProspectiveAuthoringSpec, source_configs: tuple[SourceMaterializationConfig, ...],
        project_root, artifact_writer, output_dir, composition=None, api_factory=None, candidate_catalog=None,
        read_access=None, original_input_access=None):
    """Author candidate custody and original design; grant no execution authority."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from .recursive_prospective_authoring import author_recursive_prospective

    if type(preparation) is not ExperimentPreparation or type(prospective_spec) is not RecursiveProspectiveAuthoringSpec:
        raise TypeError("prospective experiment authoring requires its exact preparation and existing prospective specification")
    preparation.__post_init__()
    _require_original_inputs(original_input_access)
    if read_access is not None and original_input_access is None:
        raise ValueError("prospective authoring requires its registered original-access scope")
    if preparation.prospective_spec is not None and (preparation.prospective_spec != prospective_spec
            or preparation.source_configs != source_configs):
        raise ValueError("prospective experiment explicit arguments differ from its frozen preparation selection")
    preparation = replace(preparation, prospective_spec=prospective_spec, source_configs=source_configs)
    if (not preparation.executable or preparation.specification_record is None or preparation.execution is None
            or preparation.allocation is None or preparation.draft != prospective_spec.draft):
        raise ValueError("prospective experiment needs its complete original preparation and exact same scientific draft")
    if preparation.contribution_dirs or preparation.draft.contribution_parents:
        raise ValueError("development contribution transport is not a prospective experiment input owner")
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root), artifact_writer=artifact_writer)
    execution = preparation.execution
    custody_root = Path(artifact_writer.root.contract.canonical_path)
    if execution.output_root is None or Path(execution.output_root).resolve() != custody_root:
        raise ValueError("prospective experiment output root differs from its selected guarded custody")
    selected = execution.source_snapshot
    if (selected is None or (selected.object_schema, selected.object_version) != (ImplementationSourceClosure.SCHEMA, ImplementationSourceClosure.VERSION)):
        raise ValueError("prospective experiment requires its actual implementation source closure, never a development binding")
    preview = preparation.prospective_candidate_preview
    if preview is None:
        captured = capture_target_closure(Path(project_root), prospective_spec.spec_id + ".source-closure")
        closure = _selected_source_closure(captured.closure, selected)
    else:
        closure = preview.implementation
    if GitStudySourceClosureInspector(Path(project_root)).observe(closure) != closure:
        raise ValueError("prospective experiment changes its selected producing source")
    if selected != ObjectIdentity.from_record("recursive-member.implementation", closure):
        raise ValueError("prospective experiment source snapshot differs from its actual selected closure")
    external, sources, files, configs = _inputs(preparation, prospective_spec, source_configs)
    projection = derive_recursive_scientific_selection(preparation.draft)
    instance, records, members = _design(preparation, projection, artifact_writer=artifact_writer)
    authored_roots = []
    with _input_bindings(external=external, sources=sources, files=files, configs=configs, custody_root=custody_root,
            draft=prospective_spec.draft) as bindings:
        report = author_recursive_prospective(spec=prospective_spec, project_root=project_root, artifact_writer=artifact_writer,
            output_dir=destination / "prospective", input_bindings=bindings, composition=composition,
            api_factory=api_factory, candidate_catalog=candidate_catalog,
            expected_preview=preparation.prospective_candidate_preview, retained_closure=closure,
            original_input_access=original_input_access, _capture_roots=authored_roots.append)
    # An explicit custom author may not supply objects. It retains the ordinary
    # independent read. Reuse never skips current access, bytes or publication
    # authentication and is not retained after this call.
    retained_roots = authored_roots[0] if len(authored_roots) == 1 else None
    if original_input_access is None:
        packet, candidate, retained_projection = _prospective_roots(destination / "prospective", artifact_writer,
            _retained=retained_roots)
    else:
        # Actual protected candidate objects already passed the current authoring
        # owner. Read only the new locator packet before the companion association
        # exists; never hash its protected siblings to reconstruct these objects.
        if preview is None:
            raise PermissionError("protected prospective authoring requires its actual prepared candidate preview")
        packet = _read_prospective_locator(destination / "prospective", "authored-wave.json",
            artifact_writer, AuthoredRecursiveWave)
        candidate, retained_projection = preview.candidate, projection.canonical_bytes()
        pinned = {member.filename: member for member in packet.members}
        if (pinned["candidate.json"].identity != ObjectIdentity.from_record(candidate.candidate_id, candidate)
                or pinned["scientific-projection.json"].identity.object_fingerprint != projection.fingerprint()):
            raise PermissionError("protected authoring changes its exact prepared candidate or projection")
    if packet.implementation != execution.source_snapshot:
        raise ValueError("prospective authoring changed the selected implementation source closure")
    if packet.draft != instance.draft or retained_projection != projection.canonical_bytes():
        raise ValueError("prospective authoring changed the original experiment scientific projection")
    candidate_identity = ObjectIdentity.from_record(candidate.candidate_id, candidate)
    packet_identity = ObjectIdentity.from_record(packet.packet_id, packet)
    instance_identity = next(row.identity for row in members if row.filename == INSTANCE_FILENAME)
    digest = sha256(canonical_json_bytes((packet_identity, candidate_identity, instance_identity))).hexdigest()
    association = ProspectiveExperimentAssociation("prospective-experiment." + digest,
        packet_identity, candidate_identity, instance_identity, members)
    companion = destination / "experiment"
    companion.mkdir(exist_ok=False)
    relative = companion.relative_to(custody_root).as_posix()
    from .experiment_runtime_bindings import original_input_record_publication
    for name, record in (*sorted(records.items()), (ASSOCIATION_FILENAME, association)):
        _require_original_inputs(original_input_access)
        # Instance/association/specification and closed locator companions stay
        # unprivileged metadata; actual model-bearing source records inherit.
        parents, access, visibility = original_input_record_publication(record=record,
            original_input_access=original_input_access)
        artifact_writer.write(ArtifactWriteRequest(association.association_id + "." + name.removesuffix(".json"),
            relative + "/" + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            association.association_id, relative, record.canonical_bytes(), visibility,
            tuple(value.visibility_ceiling for value in parents), access, lineage_parents=parents))
        _require_original_inputs(original_input_access)
    if original_input_access is not None:
        bound = _bootstrap_prospective_original_inputs(directory=destination,
            artifact_writer=artifact_writer, read_access=read_access)
        if bound is None or bound.parents != original_input_access.parents:
            raise PermissionError("prospective authoring changes its actual original parent census")
        with _original_input_scope(artifact_writer, bound) as reading:
            actual_packet, actual_candidate, actual_projection = _prospective_roots(destination / "prospective",
                reading, original_input_access=bound, _retained=retained_roots)
            if (actual_packet != packet or actual_candidate != candidate or actual_projection != retained_projection):
                raise PermissionError("prospective authoring changes its actual published roots")
        _require_original_inputs(bound)
    return {**report, "authoring_dir": str(destination), "prospective_dir": str(destination / "prospective"),
        "experiment_dir": str(companion), "experiment_association": association.identity.to_document(),
        "specification": preparation.specification.to_document()}


def _companion_payloads(selected, packet, candidate, artifact_writer, *, original_input_access=None):
    """Authenticate the complete companion without consulting domain callbacks."""
    companion = _directory(selected / "experiment", artifact_writer)
    association = decode_canonical_bytes(_read(companion, ASSOCIATION_FILENAME, artifact_writer,
        maximum=_CONTROL_BYTES, schema=ProspectiveExperimentAssociation.SCHEMA, original_input_access=original_input_access), ProspectiveExperimentAssociation, maximum_bytes=_CONTROL_BYTES)
    if (association.prospective_wave != ObjectIdentity.from_record(packet.packet_id, packet)
            or association.candidate != ObjectIdentity.from_record(candidate.candidate_id, candidate)):
        raise ValueError("prospective experiment association names another wave or outer candidate")
    names = {ASSOCIATION_FILENAME, *(row.filename for row in association.members)}
    expected_files = names | {name + ".manifest.json" for name in names}
    # ExternalArtifactPlane retains zero-byte pair locks beside each exact
    # artifact/sidecar pair. Only those existing owner-control names may occur
    # outside the closed scientific member roster.
    pair_locks = {".artifact-pair." + sha256((name + "\0" + name + ".manifest.json").encode()).hexdigest()[:24] + ".lock"
        for name in names}
    actual_files = {path.name for path in companion.iterdir() if path.name != ".publication-batches"}
    if not expected_files <= actual_files or actual_files - expected_files - pair_locks:
        raise ValueError("prospective experiment companion changes its closed complete file census")
    if any((companion / name).is_symlink() or not (companion / name).is_file()
            or (companion / name).stat().st_size != 0 for name in actual_files & pair_locks):
        raise ValueError("prospective experiment substitutes an existing custody-control lock")
    payloads = {}
    for member in association.members:
        raw = _read(companion, member.filename, artifact_writer, maximum=member.size_bytes, schema=member.identity.object_schema, original_input_access=original_input_access)
        if (len(raw), sha256(raw).hexdigest()) != (member.size_bytes, member.identity.object_fingerprint):
            raise ValueError("prospective experiment companion differs from its exact committed member bytes")
        payloads[member.filename] = raw
    return association, payloads


@dataclass(frozen=True, slots=True)
class RetainedProspectiveExperiment:
    """Authenticated original read metadata; no runtime context or provider ports."""

    association: ProspectiveExperimentAssociation
    instance: ExperimentInstanceBinding
    candidate: ExecutableStudyCandidate
    projection: object
    implementation: ImplementationSourceClosure
    draft: object
    payloads: Mapping[str, bytes]
    original_input_access: object | None = None


def load_retained_prospective_experiment(*, directory, artifact_writer, project_root=None, storage_profile=None, read_access=None):
    access = _bootstrap_prospective_original_inputs(directory=directory, artifact_writer=artifact_writer,
        read_access=read_access)
    _require_original_inputs(access)
    with _original_input_scope(artifact_writer, access) as reading:
        result = _load_retained_prospective_experiment(directory=directory, project_root=project_root,
            storage_profile=storage_profile, artifact_writer=reading, original_input_access=access)
    _require_original_inputs(access)
    return result


def _load_retained_prospective_experiment(*, directory, project_root, storage_profile, artifact_writer,
        original_input_access=None):
    """Authenticate recorded source and design pins independently of current code.

    Domain readers may decode their own fixed scientific records from the
    immutable payload mapping. This generic custody read performs no scientific
    rederivation, current operation lookup, provider binding or source capture.
    """
    from .recursive_prospective_authoring import load_retained_recursive_prospective_handoff, _read_retained_recursive_prospective_handoff

    selected = _directory(directory, artifact_writer)
    if storage_profile is None:
        # Read-only consumers already hold the actual guarded artifact root.
        # They authenticate the same closed original packet without inventing
        # a current execution profile or requiring the producing checkout.
        retained = _read_retained_recursive_prospective_handoff(
            directory=_directory(selected / "prospective", artifact_writer), artifact_writer=artifact_writer,
            original_input_access=original_input_access)
    else:
        retained = load_retained_recursive_prospective_handoff(directory=_directory(selected / "prospective", artifact_writer),
            root=project_root, storage_profile=storage_profile, artifact_writer=artifact_writer,
            **({} if original_input_access is None else {"original_input_access": original_input_access}))
    return _retained_experiment_from_handoff(selected=selected, retained=retained,
        artifact_writer=artifact_writer, original_input_access=original_input_access)


def _read_retained_prospective_experiment(*, directory, artifact_writer, original_input_access):
    """Reuse the fixed retained parser after the actual original bootstrap."""
    from .recursive_prospective_authoring import _read_retained_recursive_prospective_handoff
    selected = _directory(directory, artifact_writer)
    if (original_input_access is None
            or getattr(original_input_access, "issued_directory", None) != selected):
        raise PermissionError("retained source parsing lacks its exact original directory bootstrap")
    _require_original_inputs(original_input_access)
    with _original_input_scope(artifact_writer, original_input_access) as reading:
        retained = _read_retained_recursive_prospective_handoff(
            directory=_directory(selected / "prospective", reading), artifact_writer=reading,
            original_input_access=original_input_access)
        result = _retained_experiment_from_handoff(selected=selected, retained=retained,
            artifact_writer=reading, original_input_access=original_input_access)
    _require_original_inputs(original_input_access)
    return result


def _retained_experiment_from_handoff(*, selected, retained, artifact_writer, original_input_access):
    association, payloads = _companion_payloads(selected, retained.packet, retained.candidate, artifact_writer,
        original_input_access=original_input_access)
    instance = decode_canonical_bytes(payloads[INSTANCE_FILENAME], ExperimentInstanceBinding, maximum_bytes=None)
    allocation = decode_canonical_bytes(payloads[ALLOCATION_FILENAME], UnitAllocation, maximum_bytes=None)
    draft = retained.draft
    expected_members = {SPECIFICATION_FILENAME: instance.specification, ALLOCATION_FILENAME: instance.allocation,
        INSTANCE_FILENAME: instance_identity(instance), **{source_filename(ref): ref for ref in instance.sources}}
    if (association.instance != instance_identity(instance)
            or {row.filename: row.identity for row in association.members} != expected_members
            or instance.allocation != allocation.identity
            or instance.draft != ObjectIdentity.from_record(draft.draft_id, draft)
            or instance.campaign != ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign)
            or instance.scientific_projection != ObjectIdentity.from_record('recursive-member.scientific-projection',
                retained.scientific_projection)):
        raise ValueError("prospective retained companion changes its exact original design association")
    for member in association.members:
        document = json.loads(payloads[member.filename])
        if (document.get("schema"), document.get("version")) != (member.identity.object_schema, member.identity.object_version):
            raise ValueError("prospective retained companion changes its exact committed schema or revision")
    return RetainedProspectiveExperiment(association, instance, retained.candidate, retained.projection,
        retained.implementation, draft, MappingProxyType(payloads), original_input_access)


def load_prepared_prospective_experiment(*, directory, project_root, storage_profile, artifact_writer,
        handoff_loader=None, composition=None, candidate_catalog=None, reveal_authority_id=None,
        require_current_source=True, read_access=None):
    if type(require_current_source) is not bool:
        raise TypeError("prospective experiment source validation requires an explicit boolean selection")
    access = _bootstrap_prospective_original_inputs(directory=directory, artifact_writer=artifact_writer,
        read_access=read_access)
    _require_original_inputs(access)
    with _original_input_scope(artifact_writer, access) as reading:
        result = _load_prepared_prospective_experiment(directory=directory, project_root=project_root,
            storage_profile=storage_profile, artifact_writer=reading, handoff_loader=handoff_loader,
            composition=composition, candidate_catalog=candidate_catalog, reveal_authority_id=reveal_authority_id,
            require_current_source=require_current_source, original_input_access=access, read_access=read_access)
    _require_original_inputs(access)
    return result


def _load_prepared_prospective_experiment(*, directory, project_root, storage_profile, artifact_writer,
        handoff_loader=None, composition=None, candidate_catalog=None, reveal_authority_id=None,
        require_current_source=True, original_input_access=None, read_access=None):
    """Authenticate original custody and its current executable handoff.

    Fresh execution requires its exact selected producing source by default. Recovery
    can authenticate original bytes before the campaign API checks its source
    amendment. Readout uses the separate retained metadata loader.
    """
    from .recursive_prospective_authoring import _load_recursive_prospective_handoff_with_roots
    from .experiment_preparation import experiment_protocols

    report_progress(phase="load_experiment", done=0, total=1)
    if type(require_current_source) is not bool:
        raise TypeError("prospective experiment source validation requires an explicit boolean selection")
    selected = _directory(directory, artifact_writer)
    prospective = _directory(selected / "prospective", artifact_writer)
    if handoff_loader is not None and not callable(handoff_loader):
        raise TypeError("prospective experiment needs its owning installed handoff loader")
    options = {key: value for key, value in (("composition", composition), ("candidate_catalog", candidate_catalog)) if value is not None}
    arguments = dict(directory=prospective, root=project_root, storage_profile=storage_profile,
        artifact_writer=artifact_writer, require_current_source=require_current_source,
        **({} if original_input_access is None else {"original_input_access": original_input_access}), **options)
    if handoff_loader is None:
        handoff, (packet, candidate, projection) = _load_recursive_prospective_handoff_with_roots(**arguments)
    else:
        handoff = handoff_loader(**arguments)
        # Custom loaders may return caller-held objects. Authenticate the current
        # original controls independently rather than accepting cached records.
        packet, candidate, projection = _prospective_roots(prospective, artifact_writer, original_input_access=original_input_access)
    draft = handoff.compilation.draft
    if (Path(handoff.directory) != prospective or candidate.authoring_package != handoff.authoring
            or packet.draft != ObjectIdentity.from_record(draft.draft_id, draft)
            or projection != handoff.compilation.selected_scientific_projection.canonical_bytes()):
        raise ValueError("prospective experiment owning handoff changes its exact candidate, directory or scientific graph")
    association, payloads = _companion_payloads(selected, packet, candidate, artifact_writer, original_input_access=original_input_access)
    instance = _authenticate_instance(payloads, draft, projection, artifact_writer=artifact_writer)
    codecs = {(row.specification_type.SCHEMA, row.specification_type.VERSION): row for row in experiment_protocols()}
    declaration = codecs[(instance.specification.object_schema, instance.specification.object_version)]
    specification = decode_canonical_bytes(payloads[SPECIFICATION_FILENAME], declaration.specification_type, maximum_bytes=None)
    allocation = decode_canonical_bytes(payloads[ALLOCATION_FILENAME], UnitAllocation, maximum_bytes=None)
    sources = {(kind.SCHEMA, kind.VERSION): kind for kind in declaration.input_record_types}
    design_records = tuple((ref.object_id, decode_canonical_bytes(payloads[source_filename(ref)], sources[(ref.object_schema, ref.object_version)], maximum_bytes=None))
        for ref in instance.sources)
    expected_members = {SPECIFICATION_FILENAME: instance.specification, ALLOCATION_FILENAME: instance.allocation,
        INSTANCE_FILENAME: association.instance, **{source_filename(ref): ref for ref in instance.sources}}
    if (association.instance != instance_identity(instance)
            or {row.filename: row.identity for row in association.members} != expected_members):
        raise ValueError("prospective experiment companion substitutes its exact original instance/specification/allocation")

    binding = experiment_runtime_binding(declaration)
    if binding is not None:
        bound = binding.bind_handoff(handoff, specification=specification,
            allocation=allocation, source_records=design_records, artifact_writer=artifact_writer,
            reveal_authority_id=reveal_authority_id,
            **({} if original_input_access is None else {"original_input_access": original_input_access}),
            **({} if read_access is None else {"read_access": read_access}))
        # A domain custody callback may bind its runtime ports; it cannot replace
        # the scientific design, source, resources or actual outer candidate.
        if (type(bound) is not type(handoff)
                or any(getattr(bound, name) != getattr(handoff, name) for name in
                    ("directory", "compilation", "authoring", "context", "projection", "resources"))):
            raise ValueError("registered prospective binding changes its authenticated owning handoff")
        handoff = bound
    result = PreparedProspectiveExperimentHandoff(handoff, association, instance, candidate, specification, allocation, design_records, original_input_access)
    report_progress(phase="load_experiment", done=1, total=1)
    return result
