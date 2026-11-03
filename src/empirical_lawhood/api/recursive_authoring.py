# SPDX-License-Identifier: MPL-2.0
"""Bounded public authoring over the shared recursive compiler and custody."""

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.infrastructure.numerical_provenance import observe_implementation_source
from empirical_lawhood.api.recursive_operations import operation_catalog
from empirical_lawhood.runtime.artifacts import artifact_custody_limits
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactStreamWriteRequest, ArtifactWriteRequest, is_canonical_json_media_type,
)
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec, storage_codec_census
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding, RecursiveWaveMember

MAX_DRAFT_BYTES = None
MAX_PACKET_BYTES = None


def _external_storage_contract(*, payload_schema, media_type, storage_codecs=None):
    if storage_codecs is None:
        storage_codecs = storage_codec_census(operation_catalog()[0])
    codec = resolve_storage_codec(storage_codecs, payload_schema=payload_schema, media_type=media_type)
    if codec is not None:
        return codec.profile, codec.filename_suffix
    if not is_canonical_json_media_type(media_type):
        raise ValueError("external scientific input lacks an exact registered storage codec")
    return ArtifactProfile.CANONICAL_JSON, ".json"


def _published_source_manifest_preflight(*, selected_inputs, bindings, artifact_writer,
        storage_codecs, source_records, original_input_access, check_access):
    """Join exact selected records and complete original batches before any hash.

    Canonical copies are transport, not original publication authority. The
    independently retained typed source census includes operational selections;
    body identity and actual committed publication metadata bind every sibling.
    """
    from empirical_lawhood.runtime.artifacts import ArtifactManifest, artifact_publication_member

    root = Path(artifact_writer.root.contract.canonical_path)
    known_records = {}
    for record in source_records:
        if not isinstance(record, CanonicalRecord):
            raise TypeError('selected source census requires actual canonical record owners')
        raw = record.canonical_bytes()
        key = record.SCHEMA, record.fingerprint()
        expected = original_input_access.record_parents(record), len(raw)
        previous = known_records.setdefault(key, expected)
        if previous != expected:
            raise PermissionError('selected source records disagree on their exact original-parent census')
    manifests = {}
    parentless_pairs = {
        (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
        (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY),
    }

    def require_source(manifest, expected_parents):
        check_access()
        logical = manifest.logical
        if expected_parents is not None and logical.lineage_parents != expected_parents:
            raise PermissionError('selected source changes its complete actual original-parent census')
        if (logical.lineage_parents
                or logical.profile is ArtifactProfile.CANONICAL_JSON and expected_parents is None):
            if original_input_access.require_member(manifest) is not None:
                raise ValueError('original source member guard must return None or raise')
        elif (logical.outcome_access, logical.visibility_ceiling) not in parentless_pairs:
            raise PermissionError('selected source has no exact intrinsic or original-parent custody')
        check_access()

    def known_canonical_sibling(manifest):
        logical, physical, publication = manifest.logical, manifest.materialization, manifest.publication
        expected = known_records.get((logical.payload_schema, logical.content_sha256))
        if expected is None:
            raise PermissionError('publication sibling is outside its exact selected source census')
        parents, width = expected
        path = root / physical.relative_path
        if (logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'
                or physical.logical_artifact_id != logical.logical_artifact_id
                or physical.storage_root_id != artifact_writer.root.contract.storage_root_id
                or physical.physical_sha256 != logical.content_sha256 or physical.size_bytes != width
                or physical.compression != 'none' or physical.partition_selector is not None
                or artifact_writer.root.resolve(physical.relative_path, for_write=False) != path
                or any(member.is_symlink() for member in (path, *path.parents))
                or publication is None
                or publication.publication_scope.storage_root_id != artifact_writer.root.contract.storage_root_id
                or publication.members.count(artifact_publication_member(logical, physical)) != 1):
            raise PermissionError('selected canonical sibling changes its exact original bytes or publication metadata')
        require_source(manifest, parents)
        return parents

    for external in selected_inputs:
        check_access()
        path = Path(bindings[external.input_id])
        if '..' in path.parts or any(member.is_symlink() for member in (path, *path.parents)):
            raise ValueError('selected source refuses symbolic links and parent traversal')
        path = path.resolve(strict=True)
        if not path.is_relative_to(root):
            continue
        sidecar = path.with_name(path.name + '.manifest.json')
        if sidecar.is_symlink():
            raise ValueError('selected source manifest refuses symbolic links')
        if not sidecar.exists():
            continue
        relative = path.relative_to(root).as_posix()
        manifest = artifact_writer.read_manifest(relative)
        logical, physical = manifest.logical, manifest.materialization
        profile, _ = _external_storage_contract(payload_schema=external.payload_schema,
            media_type=external.media_type, storage_codecs=storage_codecs)
        codec = resolve_storage_codec(storage_codecs, payload_schema=external.payload_schema,
            profile=profile, media_type=external.media_type)
        if ((logical.logical_artifact_id, logical.profile, logical.payload_schema, logical.media_type,
                logical.content_sha256, physical.logical_artifact_id, physical.relative_path,
                physical.storage_root_id, physical.physical_sha256, physical.compression,
                physical.partition_selector) !=
                (external.logical_artifact_id, profile, external.payload_schema, external.media_type,
                    external.expected_content_sha256, external.logical_artifact_id, relative,
                    artifact_writer.root.contract.storage_root_id, external.expected_content_sha256, 'none', None)
                or external.maximum_size_bytes is not None and physical.size_bytes > external.maximum_size_bytes
                or codec is not None and codec.maximum_bytes is not None and physical.size_bytes > codec.maximum_bytes):
            raise PermissionError('selected source changes its exact published bytes, path or storage contract')
        held = known_records.get((external.payload_schema, external.expected_content_sha256))
        expected_parents = None if held is None else held[0]
        require_source(manifest, expected_parents)
        key = physical.storage_root_id, physical.relative_path
        previous = manifests.setdefault(key, (manifest, expected_parents))
        if previous != (manifest, expected_parents):
            raise PermissionError('selected source aliases conflicting exact publication metadata')

    # Register the whole exact original publication closure BEFORE the writer
    # opens its first member. This is metadata only; no unknown sibling obtains
    # permission from BLIND labels, a schema, copied filenames or shared parents.
    batches = {}
    for manifest, _ in tuple(manifests.values()):
        if manifest.publication is None:
            raise PermissionError('selected source lacks its exact original publication')
        publication = manifest.publication
        marker = publication.commit_marker_relative_path
        previous = batches.setdefault(marker, publication)
        if previous != publication:
            raise PermissionError('selected source combines conflicting original publication metadata')
    for publication in batches.values():
        for member in publication.members:
            check_access()
            sibling = artifact_writer.read_manifest(member.relative_path)
            if sibling.publication != publication:
                raise PermissionError('selected source sibling changes its complete original publication')
            key = sibling.materialization.storage_root_id, sibling.materialization.relative_path
            selected = manifests.get(key)
            if selected is None:
                parents = known_canonical_sibling(sibling)
                manifests[key] = sibling, parents
            elif selected[0] != sibling:
                raise PermissionError('selected source sibling substitutes exact selected publication metadata')
            check_access()

    def before_source_member(manifest):
        check_access()
        if type(manifest) is not ArtifactManifest:
            raise TypeError('selected source requires its exact publication manifest')
        physical = manifest.materialization
        selected = manifests.get((physical.storage_root_id, physical.relative_path))
        if selected is None:
            raise PermissionError('publication sibling is outside its exact selected source census')
        original, expected_parents = selected
        if manifest != original:
            raise PermissionError('selected source publication changed after exact metadata preflight')
        require_source(manifest, expected_parents)
        check_access()

    return before_source_member


def load_recursive_draft(path):
    return decode_canonical_bytes(read_bounded_bytes(Path(path), maximum_bytes=MAX_DRAFT_BYTES),
                                  RecursiveStudyDraft, maximum_bytes=MAX_DRAFT_BYTES)


def explain_recursive_draft(draft):
    from empirical_lawhood.planning.recursive_authoring import explain_recursive_draft as explain

    return {**explain(draft), "native_contact": "none", "scientific_execution_performed": False,
            "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def implementation_binding(project_root, *, _admitted_source=None):
    rows, code, lock, head, clean = (observe_implementation_source(project_root) if _admitted_source is None else
        observe_implementation_source(project_root, _admitted_source=_admitted_source))
    return RecursiveImplementationBinding(rows, code, lock, head, clean)


def author_recursive_wave(*, draft, project_root, artifact_writer, output_dir, input_bindings=(), contribution_dir=None, contribution_dirs=None, origins=None,
                         experiment_specification=None, experiment_allocation=None, experiment_design_records=(),
                         _input_access_guard=None, _original_input_access=None, _source_custody_records=()):
    """Freeze a selected bounded wave; never acquire data or grant authority."""
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

    if _input_access_guard is not None and not callable(_input_access_guard):
        raise TypeError("authoring input access guard must be callable")
    if (type(_source_custody_records) is not tuple
            or any(type(row) is not tuple or len(row) != 2 for row in _source_custody_records)
            or tuple(key for key, _ in _source_custody_records) !=
                tuple(sorted({key for key, _ in _source_custody_records}))
            or any(not isinstance(record, CanonicalRecord) for _, record in _source_custody_records)):
        raise TypeError('authoring original source census requires actual uniquely keyed canonical records')
    def check_access():
        if (_input_access_guard is None and _original_input_access is not None
                and _original_input_access.require_current() is not None):
            raise ValueError('original input access guard must return None or raise on refusal')
        if _input_access_guard is not None and _input_access_guard() is not None:
            raise ValueError("authoring input access guard must return None or raise on refusal")
    check_access()
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    registrations, registry, codecs = operation_catalog()
    storage_codecs = storage_codec_census(registrations)
    source = implementation_binding(project_root)
    run_inputs = (draft.fingerprint(), source.code_sources_sha256, source.dependency_lock_sha256, registry.fingerprint())
    if origins is not None:
        origins.validate_draft(draft)
        run_inputs += (origins.fingerprint(),)
    run_id = "recursive." + sha256(canonical_json_bytes(run_inputs)).hexdigest()[:24]
    closure = None
    supplied_bindings = tuple(input_bindings)
    if draft.contribution_parents or contribution_dir is not None or contribution_dirs is not None:
        from empirical_lawhood.api.recursive_contributions import authenticate_recursive_parents, _contribution_input_bindings
        from empirical_lawhood.runtime.recursive_handoff import RecursiveParentClosureBinding, RecursiveParentClosuresBinding
        parents = authenticate_recursive_parents(draft=draft, artifact_writer=artifact_writer,
            directory=contribution_dir, directories=contribution_dirs)
        supplied_bindings += _contribution_input_bindings(authenticated=parents, draft=draft, origins=origins)
        closures = tuple(RecursiveParentClosureBinding(
            selected.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix(),
            ObjectIdentity.from_record(transport.transport_id, transport),
            ObjectIdentity.from_record(manifest.contribution_id, manifest))
            for selected, transport, manifest, _, _, _ in parents)
        closure = closures[0] if len(closures) == 1 else RecursiveParentClosuresBinding(closures)
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=source.observed_git_head, run_plan_id=run_id, output_codecs=codecs)
    if compilation.run_plan is None or compilation.execution_plan is None or compilation.proof is None:
        raise ValueError("selected wave has no closed development plan; use the prospective handoff or explain its unresolved premises")
    from empirical_lawhood.api.recursive_publications import authenticate_registered_publications
    authenticate_registered_publications(draft=draft, config_inputs=compilation.config_inputs,
        registrations=registrations, artifact_writer=artifact_writer)
    records = {"draft.json": draft, "implementation.json": source,
               "template.json": compilation.template,
               "scientific-projection.json": compilation.selected_scientific_projection,
               "run-plan.json": compilation.run_plan, "execution-plan.json": compilation.execution_plan,
               "graph-preservation.json": compilation.proof, "registry.json": compilation.registry,
               "resource-ceiling.json": draft.campaign.budget}
    if experiment_specification is not None or experiment_allocation is not None or experiment_design_records:
        from empirical_lawhood.kernel.experimental_design import UnitAllocation
        from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
        if not isinstance(experiment_specification, CanonicalRecord) or type(experiment_allocation) is not UnitAllocation:
            raise TypeError("experiment authoring must retain both selected specification and allocation")
        from empirical_lawhood.api.experiment_preparation import experiment_protocols
        declarations = experiment_protocols()
        owners = tuple(value for value in declarations if type(experiment_specification) is value.specification_type)
        if len(owners) != 1:
            raise ValueError("authored experiment has no installed specification declaration")
        if owners[0].validate_instance is None:
            raise ValueError("authored experiment lacks its registered scientific instance validator")
        if (type(experiment_design_records) is not tuple
                or tuple(key for key, _ in experiment_design_records) != tuple(sorted({key for key, _ in experiment_design_records}))):
            raise ValueError("authored experiment repeats or reorders original design bindings")
        references = []
        for key, record in experiment_design_records:
            from empirical_lawhood.kernel.serialization import validate_stable_id
            validate_stable_id(key)
            if type(record) not in owners[0].input_record_types:
                raise ValueError("authored experiment original source lacks its declared exact codec")
            name = "experiment-source-" + sha256(key.encode()).hexdigest() + ".json"
            records[name] = record
            references.append(ObjectIdentity.from_record(key, record))
        from .experiment_runtime_bindings import authenticate_experiment_instance
        authenticate_experiment_instance(declaration=owners[0], specification=experiment_specification,
            allocation=experiment_allocation, draft=draft, source_records=experiment_design_records,
            artifact_writer=artifact_writer)
        records["experiment-specification.json"] = experiment_specification
        records["experiment-allocation.json"] = experiment_allocation
        records["experiment-instance.json"] = ExperimentInstanceBinding(
            experiment_specification.identity, experiment_allocation.identity,
            ObjectIdentity.from_record(draft.draft_id, draft),
            ObjectIdentity.from_record("recursive-member.scientific-projection", compilation.selected_scientific_projection),
            ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign), tuple(references))
    config_parents = {}
    config_custody = {}
    graph_parents = {}
    for value in compilation.config_inputs:
        name = "config-" + sha256(value.node_id.encode()).hexdigest()[:24] + ".json"
        records[name] = value.record
        config_parents[name] = value.input_parents
        config_custody[name] = (value.input_spec.expected_outcome_access,
            value.input_spec.expected_visibility_ceiling)
        for parent in value.input_parents:
            previous = graph_parents.setdefault(parent.identity, parent)
            if previous != parent:
                raise ValueError('authored configuration graph changes one original parent custody')
    from empirical_lawhood.runtime.artifacts import lineage_parent_sort_key
    graph_parents = tuple(sorted(graph_parents.values(), key=lineage_parent_sort_key))
    if origins is not None:
        records["origins.json"] = origins
    if closure is not None:
        records["parent-closure.json" if len(draft.contribution_parents) == 1 else "parent-closures.json"] = closure
    bindings = dict(supplied_bindings)
    selected_inputs = compilation.selected_scientific_projection.external_inputs
    if len(bindings) != len(supplied_bindings) or set(bindings) != {value.input_id for value in selected_inputs}:
        raise ValueError("authoring must bind every selected external input exactly once")
    external_sources = {}
    source_member_guard = None
    if _original_input_access is not None:
        source_member_guard = _published_source_manifest_preflight(selected_inputs=selected_inputs,
            bindings=bindings, artifact_writer=artifact_writer, storage_codecs=storage_codecs,
            source_records=tuple(record for _, record in (*experiment_design_records, *_source_custody_records)),
            original_input_access=_original_input_access, check_access=check_access)
    for external in selected_inputs:
        check_access()
        if external.parent_substitution:
            raise ValueError("a future qualification parent binds only through the prospective lifecycle")
        pair = (external.outcome_access, external.visibility_ceiling)
        allowed = {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)}
        if draft.development_study.access_pair[0] is OutcomeAccess.EVALUATION_REVEALED:
            allowed.add(draft.development_study.access_pair)
        if _original_input_access is not None:
            from empirical_lawhood.runtime.plans import derived_development_custody
            allowed.add(derived_development_custody(OutcomeAccess.DEVELOPMENT_VISIBLE,
                VisibilityCeiling.DEVELOPMENT_ONLY,
                tuple(value.outcome_access for value in _original_input_access.parents),
                tuple(value.visibility_ceiling for value in _original_input_access.parents)))
        if pair not in allowed:
            raise ValueError("development authoring cannot consume sealed, privileged or mismatched external evidence")
        profile, suffix = _external_storage_contract(
            payload_schema=external.payload_schema, media_type=external.media_type, storage_codecs=storage_codecs)
        storage_codec = resolve_storage_codec(storage_codecs, payload_schema=external.payload_schema,
            profile=profile, media_type=external.media_type)
        binary = profile is not ArtifactProfile.CANONICAL_JSON
        from empirical_lawhood.runtime.recursive_record_codecs import requires_declared_input_record
        if binary and requires_declared_input_record(draft=draft, external=external, registrations=registrations):
            raise ValueError("declared canonical input record cannot substitute a binary storage contract")
        name = "external-" + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        object_id = "recursive-member." + name.removesuffix(".json")
        parents = ()
        if binary:
            path = Path(bindings[external.input_id])
            if any(value.is_symlink() for value in (path, *path.parents)):
                raise ValueError('external scientific input refuses symbolic links')
            path = path.resolve(strict=True)
            root = Path(artifact_writer.root.contract.canonical_path)
            protected = pair not in {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY),
                                     (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)}
            manifest = None
            if path.is_relative_to(root):
                relative = path.relative_to(root).as_posix()
                sidecar = path.with_name(path.name + '.manifest.json')
                if sidecar.exists() or sidecar.is_symlink():
                    manifest = artifact_writer.read_manifest(relative)
            if protected and manifest is None:
                raise PermissionError('protected external FILE requires its exact original publication')
            if manifest is not None:
                check_access()
                logical, material = manifest.logical, manifest.materialization
                actual_pair = (logical.outcome_access, logical.visibility_ceiling)
                original_protected = actual_pair not in {
                    (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE),
                    (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)}
                if original_protected or protected:
                    if _original_input_access is None and _input_access_guard is None:
                        raise PermissionError('protected external FILE lacks its owning current input access')
                    if (actual_pair != pair or logical.logical_artifact_id != external.logical_artifact_id
                            or logical.profile is not profile or logical.payload_schema != external.payload_schema
                            or logical.media_type != external.media_type
                            or logical.content_sha256 != external.expected_content_sha256
                            or material.physical_sha256 != external.expected_content_sha256
                            or material.size_bytes > external.maximum_size_bytes
                            or material.relative_path != relative
                            or material.storage_root_id != artifact_writer.root.contract.storage_root_id):
                        raise PermissionError('protected external FILE changes its exact original alias, bytes or custody')
                if _original_input_access is not None:
                    source_member_guard(manifest)
                    artifact_writer.verify_manifest(manifest, before_member=source_member_guard)
                    parents = logical.lineage_parents
                elif original_protected:
                    artifact_writer.verify_manifest(manifest, before_member=lambda _: check_access())
                    parents = logical.lineage_parents
            check_access()
            size, digest = bounded_file_sha256(path, maximum_bytes=external.maximum_size_bytes)
            check_access()
            if storage_codec.maximum_bytes is not None and size > storage_codec.maximum_bytes:
                raise ValueError("external scientific input exceeds its registered byte contract")
            if digest != external.expected_content_sha256:
                raise ValueError("external scientific input differs from its exact selected digest")
            key = ObjectIdentity(object_id, external.payload_schema, storage_codec.record_version, digest)
        else:
            raw = read_bounded_bytes(Path(bindings[external.input_id]), maximum_bytes=external.maximum_size_bytes)
            size, digest = len(raw), sha256(raw).hexdigest()
            if digest != external.expected_content_sha256:
                raise ValueError("external scientific input differs from its exact selected digest")
            from empirical_lawhood.runtime.recursive_record_codecs import resolve_recursive_input_codec
            codec = resolve_recursive_input_codec(draft=draft, external=external,
                registrations=registrations, fallback_codecs=codecs, payload=raw)
            operand = decode_canonical_bytes(raw, codec, maximum_bytes=external.maximum_size_bytes)
            key = ObjectIdentity.from_record(object_id, operand)
            if _original_input_access is not None:
                parents = _original_input_access.record_parents(operand)
            del operand
            del raw
        if _original_input_access is not None:
            declared_access, declared_visibility = (draft.development_study.access_pair if parents else
                (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
            expected = derived_development_custody(declared_access,
                declared_visibility, tuple(value.outcome_access for value in parents),
                tuple(value.visibility_ceiling for value in parents))
            if pair != expected:
                raise PermissionError('authored external input changes its actual original-parent custody projection')
        external_sources[name] = (Path(bindings[external.input_id]), RecursiveWaveMember(name, key, size), profile,
                                  external.media_type, external.outcome_access, external.visibility_ceiling, parents)
    from empirical_lawhood.infrastructure.recursive_control_read import CONTROL_VIEWS, normalized_plan_views
    views = normalized_plan_views(records, custody_limits=artifact_custody_limits(artifact_writer))
    view_sources = {view_name: name for name, view_name in CONTROL_VIEWS.items() if view_name in views}
    records.update(views)
    members = []
    for name, record in sorted(records.items()):
        object_id = draft.draft_id if name == "draft.json" else "recursive-member." + name.removesuffix(".json")
        members.append(RecursiveWaveMember(name, ObjectIdentity.from_record(object_id, record), record.canonical_size_bytes()))
    members.extend(value[1] for value in external_sources.values())
    members.sort(key=lambda value: value.filename)
    by_name = {value.filename: value.identity for value in members}
    packet = AuthoredRecursiveWave("recursive-authoring." + draft.fingerprint()[:24], by_name["draft.json"],
                                  by_name["implementation.json"], tuple(members))
    if implementation_binding(project_root) != source:
        raise ValueError("recursive source changed during authoring; preserve the draft and author again")
    check_access()
    destination.mkdir(parents=True)
    root = Path(artifact_writer.root.contract.canonical_path)
    relative = destination.relative_to(root).as_posix()
    from empirical_lawhood.infrastructure.recursive_custody import iter_exact_custody_file_chunks

    def guarded_chunks(path, member):
        chunks = iter(iter_exact_custody_file_chunks(path, size_bytes=member.size_bytes,
            expected_sha256=member.identity.object_fingerprint))
        while True:
            check_access()
            try:
                chunk = next(chunks)
            except StopIteration:
                break
            yield chunk
        check_access()

    def publication_requests():
        for name in (*sorted((*records, *external_sources)), "authored-wave.json"):
            check_access()
            if name in external_sources:
                path, member, profile, media_type, access, visibility, parents = external_sources[name]
                yield ArtifactStreamWriteRequest(
                    logical_artifact_id=packet.packet_id + "." + name.removesuffix(".json"),
                    relative_path=relative + "/" + name, payload_schema=member.identity.object_schema,
                    profile=profile,
                    media_type=media_type,
                    publication_scope_id=packet.packet_id, publication_scope_relative_root=relative,
                    chunks=guarded_chunks(path, member),
                    maximum_bytes=max(1, member.size_bytes), maximum_chunk_bytes=min(65536, max(1, member.size_bytes)),
                    expected_size_bytes=member.size_bytes, expected_physical_sha256=member.identity.object_fingerprint,
                    visibility_ceiling=visibility,
                    parent_visibility_ceilings=tuple(value.visibility_ceiling for value in parents),
                    outcome_access=access, lineage_parents=parents)
            else:
                record = packet if name == "authored-wave.json" else records[name]
                custody_record = records[view_sources[name]] if name in view_sources else record
                parents = (config_parents[name] if name in config_parents else
                    () if _original_input_access is None else _original_input_access.record_parents(custody_record))
                graph_container = name in ('draft.json', 'template.json', 'scientific-projection.json', 'run-plan.json',
                        'execution-plan.json', 'graph-preservation.json') or name in view_sources
                if graph_container:
                    inherited = {value.identity: value for value in parents}
                    for value in graph_parents:
                        previous = inherited.setdefault(value.identity, value)
                        if previous != value:
                            raise ValueError('authored scientific graph changes one original parent custody')
                    parents = tuple(sorted(inherited.values(), key=lineage_parent_sort_key))
                from empirical_lawhood.runtime.plans import derived_development_custody
                if name in config_custody:
                    # Publication uses the exact finalized compiler contract, including
                    # revealed analysis whose new effect still has its declared stage.
                    access, visibility = config_custody[name]
                else:
                    declared_access, declared_visibility = (draft.development_study.access_pair if parents else
                        (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
                    configuration_access = tuple(pair[0] for pair in config_custody.values()) if graph_container else ()
                    configuration_visibility = tuple(pair[1] for pair in config_custody.values()) if graph_container else ()
                    access, visibility = derived_development_custody(declared_access,
                        declared_visibility, (*configuration_access, *(value.outcome_access for value in parents)),
                        (*configuration_visibility, *(value.visibility_ceiling for value in parents)))
                yield ArtifactWriteRequest(
                    packet.packet_id + "." + name.removesuffix(".json"), relative + "/" + name,
                    record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", packet.packet_id,
                    relative, record.canonical_bytes(), visibility,
                    tuple(value.visibility_ceiling for value in parents), access, lineage_parents=parents)
    from empirical_lawhood.infrastructure.recursive_input_publication import publish_recursive_metadata
    configuration_ids = {packet.packet_id + '.' + name.removesuffix('.json') for name in config_custody}
    publish_recursive_metadata(artifact_writer, publication_requests(), require_current=check_access,
        before_member=source_member_guard,
        group_member=lambda request: request.logical_artifact_id in configuration_ids)
    check_access()
    return {"status": "AUTHORED", "authoring_dir": str(destination), "draft_sha256": draft.fingerprint(),
            "run_id": compilation.run_plan.run_plan_id, "task_count": len(compilation.execution_plan.tasks),
            "packet_sha256": packet.fingerprint(), "native_contact": "none",
            "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def load_authored_wave(*, directory, artifact_writer, lazy_payloads=False, require_initial_experiment=False,
        read_access=None):
    """Authenticate exact retained members before their typed consumer reads."""
    if type(require_initial_experiment) is not bool:
        raise TypeError("initial experiment scope requires an exact boolean")
    from empirical_lawhood.infrastructure.recursive_custody import read_exposed_recursive_payload

    directory = Path(directory)
    if any(path.is_symlink() for path in (directory, *directory.parents)) or ".." in directory.parts:
        raise ValueError("recursive authoring path refuses links or traversal")
    directory = directory.resolve(strict=True)
    if require_initial_experiment and ((directory / "inquiry-admission.json").exists()
            or (directory / "inquiry-admission.json").is_symlink()):
        raise ValueError("initial programme refuses an inquiry successor")
    root = Path(artifact_writer.root.contract.canonical_path)
    if not directory.is_relative_to(root):
        raise ValueError("recursive authoring lies outside the selected guarded root")
    manifests = {}
    def read(name, bound):
        relative = (directory / name).relative_to(root).as_posix()
        manifest = artifact_writer.read_manifest(relative,
            maximum_bytes=artifact_custody_limits(artifact_writer).manifest_bytes)
        if manifest.materialization.relative_path != relative:
            raise ValueError("recursive member manifest changes its exact selected path")
        manifests[name] = manifest
        return read_exposed_recursive_payload(artifact_writer, manifest, maximum_bytes=bound)
    from empirical_lawhood.infrastructure.recursive_custody import read_recursive_bootstrap_record
    packet_relative = (directory / 'authored-wave.json').relative_to(root).as_posix()
    packet = read_recursive_bootstrap_record(artifact_writer, packet_relative, AuthoredRecursiveWave)
    by_name = {member.filename: member for member in packet.members}
    def read_record(name, kind):
        member = by_name.get(name)
        if member is None:
            raise PermissionError('recursive bootstrap omits its exact packet member')
        relative = (directory / name).relative_to(root).as_posix()
        return read_recursive_bootstrap_record(artifact_writer, relative, kind,
            maximum_bytes=member.size_bytes, expected=member)
    from .experiment_runtime_bindings import bootstrap_authored_development_inputs
    original_input_access = bootstrap_authored_development_inputs(directory=directory,
        artifact_writer=artifact_writer, packet=packet, read_record=read_record, read_access=read_access)
    if lazy_payloads or original_input_access is not None:
        from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
        payloads = AuthenticatedRecursivePayloads(plane=artifact_writer, directory=directory,
            members=packet.members, original_input_access=original_input_access)
        lazy_payloads = True
    else:
        payloads = {}
        for member in packet.members:
            raw = read(member.filename, member.size_bytes)
            if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.identity.object_fingerprint:
                raise ValueError("authored wave member differs from its committed identity")
            storage = resolve_storage_codec(artifact_writer.validators.binary_codecs,
                payload_schema=member.identity.object_schema, profile=manifests[member.filename].logical.profile,
                media_type=manifests[member.filename].logical.media_type)
            if storage is not None and storage.record_version != member.identity.object_version:
                raise ValueError("authored binary member changes its exact registered revision")
            if storage is None:
                document = json.loads(raw)
                if (document.get("schema"), document.get("version")) != (member.identity.object_schema, member.identity.object_version):
                    raise ValueError("authored wave member changes its record schema or revision")
            payloads[member.filename] = raw
    draft = decode_canonical_bytes(payloads["draft.json"], RecursiveStudyDraft, maximum_bytes=MAX_DRAFT_BYTES)
    source = decode_canonical_bytes(payloads["implementation.json"], RecursiveImplementationBinding, maximum_bytes=None)
    if require_initial_experiment:
        if ("experiment-instance.json" not in payloads or "experiment-specification.json" not in payloads
                or type(draft) is not RecursiveStudyDraft or draft.development_study is None
                or draft.prospective_draft is not None):
            raise ValueError("initial programme requires its exact development experiment instance")
        from empirical_lawhood.api.experiment_preparation import experiment_protocols
        document = json.loads(payloads["experiment-specification.json"])
        selected = tuple(protocol for protocol in experiment_protocols()
            if (protocol.specification_type.SCHEMA, protocol.specification_type.VERSION) == (
                document.get("schema"), document.get("version")))
        if (len(selected) != 1 or selected[0].programme_record_type is not None
                or selected[0].requires_prospective_runtime_binding):
            raise ValueError("initial custody recovery refuses protected or composite experiment lifecycles")
    _authenticate_authored_wave_roots(packet=packet, draft=draft, source=source, payloads=payloads,
        artifact_writer=artifact_writer, lazy_payloads=lazy_payloads, manifests=manifests)
    if original_input_access is not None:
        original_input_access.require_current()
    return packet, draft, source, payloads


def _authenticate_authored_wave_roots(*, packet, draft, source, payloads, artifact_writer,
        lazy_payloads, manifests=None):
    """Refresh original retained premises; never reuse a prior admission verdict.

    Immediate same-read composition may retain already decoded roots, but must
    repeat every source/parent/origin/publication and direct FILE check before
    products. This helper accepts no cross-invocation verification token.
    """
    registrations, _, _ = operation_catalog()
    storage_codecs = storage_codec_census(registrations)
    external_roles = {}
    selected_external_ids = {link.external_input_id for link in draft.links
        if link.consumer_node_id in draft.selected_operation_ids and link.external_input_id is not None}
    for external in draft.external_inputs:
        if external.input_id not in selected_external_ids:
            continue
        _, suffix = _external_storage_contract(payload_schema=external.payload_schema,
            media_type=external.media_type, storage_codecs=storage_codecs)
        name = "external-" + sha256(external.input_id.encode()).hexdigest()[:24] + suffix
        external_roles[name] = (external.outcome_access, external.visibility_ceiling)
    allowed = {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)}
    if draft.development_study is not None and draft.development_study.access_pair[0] is OutcomeAccess.EVALUATION_REVEALED:
        allowed.add(draft.development_study.access_pair)
    original_input_access = getattr(payloads, 'original_input_access', None)
    for name in payloads:
        manifest = payloads.manifest(name) if lazy_payloads else manifests[name]
        expected = external_roles.get(name, (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
        if original_input_access is not None:
            original_input_access.require_member(manifest)
            if name not in external_roles:
                continue
        elif expected not in allowed:
            raise ValueError("authored wave member changes its exact exposed scientific role")
        if (manifest.logical.outcome_access, manifest.logical.visibility_ceiling) != expected:
            raise ValueError("authored wave member changes its exact exposed scientific role")
    if ObjectIdentity.from_record(draft.draft_id, draft) != packet.draft:
        raise ValueError("authored packet changes its exact scientific draft")
    if ObjectIdentity.from_record("recursive-member.implementation", source) != packet.implementation:
        raise ValueError("authored packet changes its selected source binding")
    _authenticate_experiment_instance(payloads=payloads, draft=draft, artifact_writer=artifact_writer)
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_parents, _contribution_input_bindings
    parents = authenticate_recursive_parents(draft=draft, artifact_writer=artifact_writer, payloads=payloads)
    if len(parents) > 1 and "origins.json" not in payloads:
        raise ValueError("multiple portable parents require retained exact input origins")
    if "origins.json" in payloads:
        from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
        origins = decode_canonical_bytes(payloads["origins.json"], RecursiveInputOrigins, maximum_bytes=MAX_DRAFT_BYTES)
        origins.validate_draft(draft)
        externals = {value.input_id: value for value in draft.external_inputs}
        def operand_name(input_id):
            external = externals[input_id]
            _, suffix = _external_storage_contract(
                payload_schema=external.payload_schema, media_type=external.media_type, storage_codecs=storage_codecs)
            return "external-" + sha256(input_id.encode()).hexdigest()[:24] + suffix
        for origin in origins.inputs:
            name = operand_name(origin.input_id)
            digest = (payloads.manifest(name).logical.content_sha256 if lazy_payloads and name in payloads
                      else sha256(payloads[name]).hexdigest() if name in payloads else None)
            if digest != origin.expected_content_sha256:
                raise ValueError("authored input origin omits or changes its exact external operand")
        if draft.contribution_parents:
            bindings = _contribution_input_bindings(authenticated=parents, draft=draft, origins=origins)
            for input_id, path in bindings:
                name = operand_name(input_id)
                exact = ((payloads.manifest(name).materialization.size_bytes,
                          payloads.manifest(name).logical.content_sha256) if lazy_payloads
                         else (len(payloads[name]), sha256(payloads[name]).hexdigest()))
                if bounded_file_sha256(path, maximum_bytes=MAX_PACKET_BYTES) != exact:
                    raise ValueError("authored contribution origin changes its actual product bytes")
    from empirical_lawhood.api.recursive_publications import authenticate_draft_publications
    authenticate_draft_publications(draft=draft, registrations=registrations,
        artifact_writer=artifact_writer)


def _authenticate_experiment_instance(*, payloads, draft, artifact_writer=None):
    """Preserve the exact authored design association at each retained boundary."""
    names = {"experiment-specification.json", "experiment-allocation.json", "experiment-instance.json"}
    present = names.intersection(payloads)
    if not present:
        return None
    if present != names:
        raise ValueError("authored experiment omits a selected design member")
    from empirical_lawhood.api.experiment_preparation import experiment_protocols
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    instance = decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)
    owners = {(value.specification_type.SCHEMA, value.specification_type.VERSION): value.specification_type for value in experiment_protocols()}
    codec = owners.get((instance.specification.object_schema, instance.specification.object_version))
    if codec is None:
        raise ValueError("authored experiment specification has no installed exact codec")
    specification = decode_canonical_bytes(payloads["experiment-specification.json"], codec, maximum_bytes=None)
    allocation = decode_canonical_bytes(payloads["experiment-allocation.json"], UnitAllocation, maximum_bytes=None)
    raw_projection = payloads["scientific-projection.json"]
    projection = json.loads(raw_projection)
    from empirical_lawhood.runtime.recursive_compiler import derive_recursive_scientific_selection
    expected_projection = derive_recursive_scientific_selection(draft)
    if (specification.identity != instance.specification or allocation.identity != instance.allocation
            or ObjectIdentity.from_record(draft.draft_id, draft) != instance.draft
            or ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign) != instance.campaign
            or instance.scientific_projection.object_id != "recursive-member.scientific-projection"
            or (projection.get("schema"), projection.get("version")) != (
                instance.scientific_projection.object_schema, instance.scientific_projection.object_version)
            or sha256(raw_projection).hexdigest() != instance.scientific_projection.object_fingerprint):
        raise ValueError("authored experiment changes its exact design/scientific projection association")
    if raw_projection != expected_projection.canonical_bytes():
        raise ValueError("authored experiment scientific projection differs from its actual selected draft")
    declaration = next(value for value in experiment_protocols() if value.specification_type is codec)
    if declaration.validate_instance is None:
        raise ValueError("authored experiment lacks its registered scientific instance validator")
    source_codecs = {(value.SCHEMA, value.VERSION): value for value in declaration.input_record_types}
    expected_names = {"experiment-source-" + sha256(value.object_id.encode()).hexdigest() + ".json" for value in instance.sources}
    actual_names = {name for name in payloads if name.startswith("experiment-source-")}
    if expected_names != actual_names:
        raise ValueError("authored experiment omits or adds an original source record")
    sources = []
    for reference in instance.sources:
        source_codec = source_codecs.get((reference.object_schema, reference.object_version))
        if source_codec is None:
            raise ValueError("authored experiment original source changes its registered codec/revision")
        name = "experiment-source-" + sha256(reference.object_id.encode()).hexdigest() + ".json"
        record = decode_canonical_bytes(payloads[name], source_codec, maximum_bytes=None)
        if ObjectIdentity.from_record(reference.object_id, record) != reference:
            raise ValueError("authored experiment original source changes its selected exact bytes")
        sources.append((reference.object_id, record))
    from .experiment_runtime_bindings import authenticate_experiment_instance
    authenticate_experiment_instance(declaration=declaration, specification=specification,
        allocation=allocation, draft=draft, source_records=tuple(sources), artifact_writer=artifact_writer)
    return instance
