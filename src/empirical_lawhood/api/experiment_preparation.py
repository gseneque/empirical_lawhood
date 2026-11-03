# SPDX-License-Identifier: MPL-2.0
"""Public experiment preparation through installed domain declarations."""

from pathlib import Path
from hashlib import sha256
from dataclasses import replace
import json
from types import MappingProxyType

from .codecs import load_registered_authoring
from empirical_lawhood.runtime.progress import report_progress
from empirical_lawhood.runtime.experiment_preparation import (
    ExecutionSelection, ExperimentPreparation, ExperimentProtocolDeclaration, PreparedExperimentInputs,
    PreparedExperimentFile, DependencyKind, ExperimentDependency,
)

from .experiment_runtime_bindings import experiment_runtime_binding


def experiment_protocols() -> tuple[ExperimentProtocolDeclaration, ...]:
    """Static declarations only; never invoke preparation or build a runner."""
    from empirical_lawhood.adapters.composition.generated_extension_bundles import (
        EXPERIMENT_PROTOCOL_DECLARATIONS,
    )
    declarations = EXPERIMENT_PROTOCOL_DECLARATIONS
    if (any(type(value) is not ExperimentProtocolDeclaration for value in declarations)
            or len({value.protocol_id for value in declarations}) != len(declarations)
            or len({(value.specification_type.SCHEMA, value.specification_type.VERSION) for value in declarations}) != len(declarations)):
        raise ValueError("installed experiment protocols have inconsistent owning declarations")
    return declarations


def load_experiment_specification(path: Path):
    owners = {(value.specification_type.SCHEMA, value.specification_type.VERSION): value.specification_type
              for value in experiment_protocols()}
    return load_registered_authoring(Path(path), root_schemas=owners)


def _protocol(specification):
    declarations = tuple(value for value in experiment_protocols()
                         if type(specification) is value.specification_type)
    if len(declarations) != 1:
        raise ValueError("experiment specification lacks one installed domain protocol")
    return declarations[0]


def _input_member(directory, relative_path):
    member = directory / relative_path
    if any(parent.is_symlink() for parent in (member, *member.parents)):
        raise ValueError("experiment scientific input refuses symbolic links")
    member = member.resolve(strict=True)
    if not member.is_relative_to(directory):
        raise ValueError("experiment scientific input escapes its selected directory")
    return member


def _installed_file_record_types():
    """Resolve one current closed type roster; never retain it across calls."""
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.runtime.recursive_record_codecs import input_record_type_census

    registrations, _, legacy = operation_catalog()
    return input_record_type_census(registrations, legacy_codecs=legacy)


def _resolve_file_byte_limit(declaration, identity, record_version, installed, record_types):
    """Resolve an explicitly declared physical contract without decoding bytes."""
    from empirical_lawhood.runtime.artifacts import is_canonical_json_media_type
    from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec

    canonical = tuple(kind for kind in declaration.input_file_record_types
                      if kind.SCHEMA == identity.payload_schema)
    if canonical and is_canonical_json_media_type(identity.media_type):
        matches = tuple(kind for kind in canonical if kind.VERSION == record_version)
        if len(matches) != 1:
            raise ValueError("experiment canonical file lacks its exact declared schema/revision")
        if any(codec.payload_schema == identity.payload_schema and is_canonical_json_media_type(codec.media_type)
               for codec in (*declaration.input_storage_codecs, *installed)):
            raise ValueError("experiment canonical file conflicts with a raw JSON storage contract")
        records = record_types()
        if not any(kind is matches[0] for kind in records):
            raise ValueError("experiment canonical file lacks its identical installed schema/revision codec")
        # The exact selected size still bounds hashing and author publication.
        # Interpretation belongs to the existing registered owning decoder.
        return None
    codec = resolve_storage_codec(declaration.input_storage_codecs,
        payload_schema=identity.payload_schema, media_type=identity.media_type, record_version=record_version)
    if codec is None or codec not in installed:
        raise ValueError("experiment file lacks its exact declared and installed storage codec/revision")
    return codec.maximum_bytes


def _file_byte_limit(declaration, identity, record_version, installed):
    """Keep the standalone four-argument guard fresh on every invocation."""
    return _resolve_file_byte_limit(declaration, identity, record_version, installed,
        _installed_file_record_types)


_STOCK_FILE_BYTE_LIMIT = _file_byte_limit


def _file_byte_limit_for_pass(declaration, installed):
    """Share only immutable installed type metadata within this one pass.

    Resolution stays lazy at the original first canonical-file boundary. Each
    authoring pass starts afresh, including the pass after prepare_authoring.
    A replaced four-argument guard is still invoked for every selected file.
    """
    records = None

    def record_types():
        nonlocal records
        if records is None:
            records = _installed_file_record_types()
        return records

    def limit(identity, record_version):
        if _file_byte_limit is not _STOCK_FILE_BYTE_LIMIT:
            return _file_byte_limit(declaration, identity, record_version, installed)
        return _resolve_file_byte_limit(declaration, identity, record_version, installed,
            record_types)

    return limit


def _validate_prepared_input_files(preparation):
    if not preparation.input_files:
        return
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs

    declaration = _protocol(preparation.specification_record)
    installed = operation_storage_codecs()
    file_byte_limit = _file_byte_limit_for_pass(declaration, installed)
    for _, value in preparation.input_files:
        maximum = file_byte_limit(value.identity, value.record_version)
        if maximum is not None and value.identity.size_bytes > maximum:
            raise ValueError("prepared experiment file exceeds its registered physical byte contract")
        if any(parent.is_symlink() for parent in (value.path, *value.path.parents)):
            raise ValueError("prepared experiment file refuses symbolic links")


def _selected_input_access_guard(*, specification, selection, path, declaration,
        artifact_writer, read_access=None, before_read=None):
    """Authenticate exact declared locators without opening other input bodies."""
    from empirical_lawhood.api.experiment_runtime_bindings import bootstrap_selected_experiment_inputs
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    def read_record(binding, kind):
        if before_read is not None:
            before_read()
        member = _input_member(Path(path).parent, binding.relative_path)
        raw = read_bounded_bytes(member, maximum_bytes=binding.maximum_bytes)
        if sha256(raw).hexdigest() != binding.identity.object_fingerprint:
            raise PermissionError('selected input locator changes its exact canonical bytes')
        record = decode_canonical_bytes(raw, kind, maximum_bytes=binding.maximum_bytes)
        if ObjectIdentity.from_record(binding.identity.object_id, record) != binding.identity:
            raise PermissionError('selected input locator changes its exact canonical identity')
        return record

    return bootstrap_selected_experiment_inputs(declaration=declaration, specification=specification,
        selection=selection, read_record=read_record, artifact_writer=artifact_writer, read_access=read_access,
        selection_path=Path(path).resolve(strict=True))


def load_experiment_inputs(specification, selection_path: Path, *, artifact_writer=None,
        read_access=None, _input_access_guard=None) -> PreparedExperimentInputs:
    """Read exact selected bytes through the domain's closed codec roster.

    Domain preparation still establishes role, frame and scientific compatibility.
    In particular these byte bindings cannot make exposed inputs prospective.
    """
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputSelection

    if _input_access_guard is not None and not callable(_input_access_guard):
        raise TypeError("experiment input access guard must be callable")
    guards = [] if _input_access_guard is None else [_input_access_guard]

    def check_access():
        for guard in guards:
            if guard() is not None:
                raise ValueError("experiment input access guard must return None or raise on refusal")

    declaration = _protocol(specification)
    if declaration.bind_inputs is None:
        raise ValueError("selected experiment has no installed scientific input binding")
    path = Path(selection_path)
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("experiment input selection refuses symbolic links")
    path = path.resolve(strict=True)
    check_access()
    raw = read_bounded_bytes(path, maximum_bytes=declaration.maximum_config_bytes)
    # This probe selects only between two code-owned roots. The entire original
    # payload still undergoes strict canonical decoding, including duplicate keys.
    document = json.loads(raw)
    roots = {record.SCHEMA: record for record in (ExperimentInputSelection, ExperimentFileInputSelection)}
    selection_type = roots.get(document.get("schema")) if type(document) is dict else None
    if selection_type is None:
        raise ValueError("experiment inputs lack a supported closed selection schema")
    selection = decode_canonical_bytes(raw, selection_type,
                                      maximum_bytes=declaration.maximum_config_bytes)
    if selection.protocol_id != declaration.protocol_id:
        raise ValueError("experiment source selection substitutes its installed domain protocol")
    selected_guard = _selected_input_access_guard(specification=specification, selection=selection,
        path=path, declaration=declaration, artifact_writer=artifact_writer, read_access=read_access,
        before_read=check_access)
    if selected_guard is not None:
        guards.append(selected_guard)
    codecs = {(record.SCHEMA, record.VERSION): record for record in declaration.input_record_types}
    records = {}
    record_paths = {}
    for binding in selection.bindings:
        check_access()
        member = _input_member(path.parent, binding.relative_path)
        codec = codecs.get((binding.identity.object_schema, binding.identity.object_version))
        if codec is None:
            raise ValueError("experiment scientific input lacks its registered exact codec/revision")
        payload = read_bounded_bytes(member, maximum_bytes=binding.maximum_bytes)
        if sha256(payload).hexdigest() != binding.identity.object_fingerprint:
            raise ValueError("experiment scientific input changes its selected bytes")
        record = decode_canonical_bytes(payload, codec, maximum_bytes=binding.maximum_bytes)
        if ObjectIdentity.from_record(binding.identity.object_id, record) != binding.identity:
            raise ValueError("experiment scientific input changes its selected canonical identity")
        records[binding.key] = record
        record_paths[binding.key] = member
    arguments = {}
    if type(selection) is ExperimentFileInputSelection:
        from empirical_lawhood.api.recursive_operations import operation_storage_codecs

        installed = operation_storage_codecs()
        file_byte_limit = _file_byte_limit_for_pass(declaration, installed)
        files = {}
        for binding in selection.files:
            check_access()
            maximum = file_byte_limit(binding.identity, binding.record_version)
            if maximum is not None and binding.identity.size_bytes > maximum:
                raise ValueError("experiment file exceeds its registered physical byte contract")
            member = _input_member(path.parent, binding.relative_path)
            # Its exact selected size is already known. Refuse a larger physical
            # file before hashing, even when the operational allowance is broad.
            size, digest = bounded_file_sha256(member, maximum_bytes=binding.identity.size_bytes)
            if (size, digest) != (binding.identity.size_bytes, binding.identity.sha256):
                raise ValueError("experiment file changes its selected exact bytes or size")
            files[binding.key] = PreparedExperimentFile(binding.identity, binding.record_version,
                                                       member, binding.maximum_bytes)
        arguments["files"] = files
    if declaration.bind_input_locations:
        arguments["record_paths"] = MappingProxyType(record_paths)
    check_access()
    resolved = declaration.bind_inputs(specification, records, **arguments)
    if type(resolved) is not PreparedExperimentInputs:
        raise TypeError("registered experiment input binding must return its typed handle")
    check_access()
    return resolved


def prepare_experiment(specification, *, scientific_inputs=None,
                       execution: ExecutionSelection | None = None,
                       protocol_bytes: bytes | None = None, method_inputs=None
                       ) -> ExperimentPreparation:
    """Compile selected science; missing facts remain classified dependencies.

    Callers supply scientifically authenticated inputs through their owning custody
    services. Configuration decoding alone establishes no source eligibility.
    """
    report_progress(phase="prepare_specification", done=0, total=1)
    try:
        declaration = _protocol(specification)
        selection = execution if execution is not None else ExecutionSelection()
        if type(selection) is not ExecutionSelection:
            raise TypeError("experiment execution requires its typed operational selection")
        selection.__post_init__()
        arguments = dict(scientific_inputs=scientific_inputs if scientific_inputs is not None else {},
                         execution=selection, protocol_bytes=protocol_bytes)
        if method_inputs is not None:
            arguments["method_inputs"] = method_inputs
        preparation = declaration.prepare(specification, **arguments)
        if type(preparation) is not ExperimentPreparation or preparation.specification != specification.identity:
            raise ValueError("registered protocol substitutes its selected specification or preparation contract")
        dependencies = preparation.dependencies
        if selection.workers is None:
            dependencies = (*dependencies, ExperimentDependency("experiment.workers", DependencyKind.ENVIRONMENT,
                "Select worker concurrency explicitly or through the operator profile before authoring."))
        if preparation.programme is not None and (
                declaration.programme_record_type is None
                or type(preparation.programme) is not declaration.programme_record_type):
            raise ValueError("Registered protocol substitutes its exact full programme selection")
        result = replace(preparation, execution=selection, specification_record=specification,
            dependencies=tuple(sorted(dependencies, key=lambda row: row.code)))
    except Exception:
        report_progress(phase="prepare_specification", done=1, total=1, failed=1)
        raise
    report_progress(phase="prepare_specification", done=1, total=1)
    return result


def _authoring_access_guard(*, preparation, binding, artifact_writer, read_access, original_input_access=None):
    """Reload current permission at each actual authoring access; retain no verdict."""
    callback = None if binding is None else binding.validate_authoring_read_access
    prospective_supported = (binding is not None and callable(binding.bootstrap_prospective_input_access)
        and original_input_access is not None)
    if read_access is not None and (preparation.prospective_spec is not None and not prospective_supported
            or not callable(callback) and original_input_access is None):
        raise ValueError("selected experiment authoring does not support development read access")
    if callback is None and original_input_access is None:
        return None

    def guard():
        if original_input_access is not None and original_input_access.require_current() is not None:
            raise ValueError('original input access guard must return None or raise on refusal')
        if callback is not None and callback(preparation=preparation,
                artifact_writer=artifact_writer, read_access=read_access) is not None:
            raise ValueError("authoring access validator must return None or raise on refusal")
    return guard


def author_prepared_experiment(*, preparation: ExperimentPreparation, project_root,
                               artifact_writer, output_dir, read_access=None):
    """Freeze derived graph and bindings through existing recursive custody.

    Callers never reconstruct operation IDs or external binding projections.
    Source checks here and at recursive execution retain actual-worker identity.
    """
    from .recursive_prospective_authoring import _prospective_preparation_scope

    with _prospective_preparation_scope():
        return _author_prepared_experiment(preparation=preparation, project_root=project_root,
            artifact_writer=artifact_writer, output_dir=output_dir, read_access=read_access)


def _author_prepared_experiment(*, preparation, project_root, artifact_writer, output_dir, read_access):
    from tempfile import TemporaryDirectory
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    preparation.__post_init__()
    if preparation.programme is not None:
        raise ValueError("Composite authoring requires ExperimentProgrammeService with the selected storage profile")
    if preparation.execution is None or preparation.execution.workers is None:
        raise ValueError("experiment authoring requires explicitly selected worker concurrency")
    binding = (None if preparation.specification_record is None else
        experiment_runtime_binding(_protocol(preparation.specification_record)))
    original_input_access = (None if binding is None or binding.bootstrap_authoring_input_access is None else
        binding.bootstrap_authoring_input_access(preparation=preparation,
            artifact_writer=artifact_writer, read_access=read_access))
    if original_input_access is not None:
        original_input_access.require_current()
    access_guard = _authoring_access_guard(preparation=preparation, binding=binding,
        artifact_writer=artifact_writer, read_access=read_access, original_input_access=original_input_access)
    if access_guard is not None:
        access_guard()
    _validate_prepared_input_files(preparation)
    if preparation.specification_record is not None:

        if binding is not None and binding.prepare_authoring is not None:
            original = preparation
            preparation = binding.prepare_authoring(original, project_root=project_root,
                artifact_writer=artifact_writer, output_dir=output_dir,
                **({} if access_guard is None else {'read_access': read_access}),
                **({} if original_input_access is None or binding.bootstrap_prospective_input_access is None else
                    {'original_input_access': original_input_access}))
            if type(preparation) is not ExperimentPreparation:
                raise TypeError("registered authoring preparation must return its exact typed preparation")
            preparation.__post_init__()
            preserved = ("specification", "census", "allocation", "draft", "input_records", "input_files",
                "execution", "specification_record", "contribution_dirs", "origins", "assessment_limitations",
                "authoring_source_records")
            if any(getattr(preparation, name) != getattr(original, name) for name in preserved):
                raise ValueError("authoring preparation changed its original scientific selection or input bindings")
            records = dict(preparation.design_records)
            if any(records.get(key) != record for key, record in original.design_records):
                raise ValueError("authoring preparation dropped or replaced an original design record")
            from empirical_lawhood.runtime.experiment_preparation import DependencyKind

            if any(row not in preparation.dependencies for row in original.dependencies
                    if row.kind is not DependencyKind.SOFTWARE):
                raise ValueError("authoring preparation dropped an unresolved entry prerequisite")
    if (not preparation.executable or not (preparation.input_records or preparation.input_files or preparation.contribution_dirs) or preparation.execution is None
            or preparation.specification_record is None):
        if preparation.dependencies:
            raise ValueError("experiment authoring retains unresolved prerequisites: " + "; ".join(
                row.code + " (" + row.kind.value + "): " + row.detail for row in preparation.dependencies))
        raise ValueError("experiment authoring requires a complete executable preparation and derived inputs")
    _validate_prepared_input_files(preparation)
    if access_guard is not None:
        access_guard()
    if preparation.prospective_spec is not None:
        from .prospective_experiment import author_prepared_prospective_experiment

        return author_prepared_prospective_experiment(preparation=preparation,
            prospective_spec=preparation.prospective_spec, source_configs=preparation.source_configs,
            project_root=project_root, artifact_writer=artifact_writer, output_dir=output_dir,
            read_access=read_access, original_input_access=original_input_access)
    selection = preparation.execution
    selected_source = implementation_binding(project_root)
    if selection.source_snapshot != ObjectIdentity.from_record("recursive-member.implementation", selected_source):
        raise ValueError("prepared experiment source differs from the actual selected implementation")
    custody_root = Path(artifact_writer.root.contract.canonical_path)
    if selection.output_root is None or Path(selection.output_root).resolve() != custody_root:
        raise ValueError("prepared experiment output root differs from the selected guarded custody")
    with TemporaryDirectory(prefix=".experiment-inputs-", dir=custody_root) as scratch:
        bindings = [(key, value.path) for key, value in preparation.input_files]
        for key, record in preparation.input_records:
            if access_guard is not None:
                access_guard()
            path = Path(scratch) / (sha256(key.encode()).hexdigest() + ".json")
            path.write_bytes(record.canonical_bytes())
            bindings.append((key, path))
        report = author_recursive_wave(draft=preparation.draft, project_root=project_root,
            artifact_writer=artifact_writer, output_dir=output_dir, input_bindings=tuple(bindings),
            experiment_specification=preparation.specification_record,
            experiment_allocation=preparation.allocation,
            experiment_design_records=preparation.design_records,
            contribution_dirs=preparation.contribution_dirs or None, origins=preparation.origins,
            _original_input_access=original_input_access,
            _source_custody_records=preparation.authoring_source_records,
            **({} if access_guard is None else {'_input_access_guard': access_guard}))
    if access_guard is not None:
        access_guard()
    return {**report, "specification": preparation.specification.to_document(),
            "experiment_census": dict(preparation.census.role_counts)}


def experiment_preparation_report(preparation: ExperimentPreparation) -> dict:
    preparation.__post_init__()
    census = preparation.census
    report = {
        "specification": preparation.specification.to_document(),
        "executable": preparation.executable,
        "census": {"roles": dict(census.role_counts),
                   "resolved_roles": dict(census.resolved_role_counts),
                   "operations": dict(census.operation_counts),
                   "outputs": dict(census.output_counts),
                   "native_effects": census.native_effect_count},
        "dependencies": [{"code": value.code, "kind": value.kind.value,
                          "detail": value.detail, "source_key": value.source_key}
                         for value in preparation.dependencies],
        "assessment_limitations": [{"code": value.code, "kind": value.kind.value,
                                    "detail": value.detail, "source_key": value.source_key}
                                   for value in preparation.assessment_limitations],
        "allocation": preparation.allocation.identity.to_document() if preparation.allocation else None,
        "draft": preparation.draft.to_document() if preparation.draft else None,
        "execution": None if preparation.execution is None else {
            "workers": preparation.execution.workers,
            "environment_id": preparation.execution.environment_id,
            "source_snapshot": (None if preparation.execution.source_snapshot is None
                else preparation.execution.source_snapshot.to_document()),
            "output_root": preparation.execution.output_root},
        "native_contact": "NONE", "scientific_execution_performed": False,
        "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED",
    }
    if preparation.programme is not None:
        report["programme_selection"] = preparation.programme.to_document()
    declarations = tuple(value for value in experiment_protocols()
        if (value.specification_type.SCHEMA, value.specification_type.VERSION)
            == (preparation.specification.object_schema, preparation.specification.object_version))
    if len(declarations) == 1 and declarations[0].configuration_capabilities:
        report["configuration_capabilities"] = [value.metadata() for value in declarations[0].configuration_capabilities]
    return report


def derive_experiment_inputs(*, specification_path, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Invoke only the exact installed protocol's current input deriver."""
    if type(execution) is not ExecutionSelection:
        raise TypeError("experiment input derivation requires explicit typed execution selections")
    execution.__post_init__()
    specification = load_experiment_specification(Path(specification_path))
    protocol = _protocol(specification)
    binding = experiment_runtime_binding(protocol)
    if binding is None or binding.derive_inputs is None:
        raise ValueError("selected experiment has no installed input derivation owner")
    result = binding.derive_inputs(specification=specification, source_selection_path=Path(source_selection_path),
        project_root=Path(project_root), artifact_writer=artifact_writer, metadata_directory=Path(metadata_directory),
        output_selection_path=Path(output_selection_path), execution=execution,
        **({} if read_access is None else {'read_access': read_access}))
    return _validate_experiment_input_derivation_result(specification=specification, protocol=protocol, binding=binding,
        result=result, artifact_writer=artifact_writer, output_selection_path=output_selection_path,
        execution=execution, read_access=read_access)


def _validate_experiment_input_derivation_result(*, specification, protocol, binding, result,
        artifact_writer, output_selection_path, execution, read_access=None):
    """One unchanged result/custody contract for ordinary and composed input derivation."""
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult
    if type(result) is not ExperimentInputDerivationResult:
        raise TypeError("registered experiment input deriver returned another result type")
    result.__post_init__()
    expected_protocol=protocol
    if result.target_specification is not None:
        expected_protocol=_protocol(result.target_specification)
        if expected_protocol.protocol_id not in binding.derivation_target_protocol_ids:
            raise PermissionError('input deriver has no declared exact preprocessing target protocol')
    if (result.specification != specification.identity or result.source_selection.protocol_id != expected_protocol.protocol_id
            or result.source_selection_path != Path(output_selection_path)
            or result.preparation.execution != execution):
        raise ValueError("registered input derivation changed selected specification, protocol, output or execution")
    if result.target_specification is not None:
        _authenticate_derived_target(result, artifact_writer, read_access=read_access)
    return result


def _authenticate_derived_target(result, writer, *, read_access=None):
    """Verify the ordinary committed target publication and reopen actual inputs."""
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, derived_outcome_access
    from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
    root=Path(writer.root.contract.canonical_path)
    selected_paths = []
    for path in (result.target_specification_path, result.source_selection_path):
        path = Path(path)
        if path != path.resolve(strict=True) or any(value.is_symlink() for value in (path, *path.parents)):
            raise ValueError('preprocessing target requires an exact canonical guarded path')
        selected_paths.append(writer.root.resolve(path.relative_to(root).as_posix(), for_write=False))
    declaration = _protocol(result.target_specification)
    # A committed selector can share its publication batch with protected
    # operands. Construct current access from locator-only metadata before
    # verification can hash any sibling in that batch.
    guard = _selected_input_access_guard(specification=result.target_specification,
        selection=result.source_selection, path=selected_paths[1], declaration=declaration,
        artifact_writer=writer, read_access=read_access)

    def check_access(*_):
        if guard is not None and guard() is not None:
            raise ValueError('selected input access guard must return None or raise on refusal')

    for record,path in ((result.target_specification,result.target_specification_path),
            (result.source_selection,result.source_selection_path)):
        check_access()
        relative=path.relative_to(root).as_posix()
        path=writer.root.resolve(relative,for_write=False)
        raw=record.canonical_bytes()
        manifest=writer.read_manifest(relative)
        parents = manifest.logical.lineage_parents
        expected_access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND,
            *(value.outcome_access for value in parents))
        expected_visibility = inherited_visibility(tuple(value.visibility_ceiling for value in parents), expected_access)
        if guard is None and expected_access not in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise PermissionError('protected preprocessing target requires its owning current input access')
        writer.verify_manifest(manifest, **({} if guard is None else {'before_member': check_access}))
        check_access()
        if (manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON or manifest.logical.media_type!='application/json'
                or manifest.logical.payload_schema!=record.SCHEMA or manifest.logical.content_sha256!=record.fingerprint()
                or manifest.materialization.physical_sha256!=record.fingerprint()
                or manifest.materialization.size_bytes!=len(raw) or manifest.materialization.relative_path!=relative
                or manifest.materialization.storage_root_id!=writer.root.contract.storage_root_id
                or manifest.logical.outcome_access is not expected_access
                or manifest.logical.visibility_ceiling is not expected_visibility
                or not any((value.logical,value.materialization)==(manifest.logical,manifest.materialization) for value in result.publications)
                or read_bounded_bytes(path,maximum_bytes=len(raw))!=raw):
            raise PermissionError('preprocessing target lacks its exact canonical committed publication')
    inputs=load_experiment_inputs(result.target_specification,result.source_selection_path,
        artifact_writer=writer, read_access=read_access, _input_access_guard=guard)
    check_access()
    reopened=prepare_experiment(result.target_specification,scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs,execution=result.preparation.execution)
    if reopened!=result.preparation:
        raise PermissionError('preprocessing target does not reproduce the actual public preparation')
    check_access()


def experiment_input_derivation_report(result):
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult
    if type(result) is not ExperimentInputDerivationResult:
        raise TypeError("input derivation report requires its exact typed result")
    result.__post_init__()
    from collections import Counter
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    preparation = result.preparation
    # Derivation reports retain bounded identities/counts. Complete dependency
    # rows are already preserved with a verified publication, never truncated.
    summary = {"executable": preparation.executable,
        "census": {"roles": dict(preparation.census.role_counts), "resolved_roles": dict(preparation.census.resolved_role_counts),
            "operations": dict(preparation.census.operation_counts), "outputs": dict(preparation.census.output_counts),
            "native_effects": preparation.census.native_effect_count},
        "dependency_count": len(preparation.dependencies),
        "dependency_kinds": dict(sorted(Counter(row.kind.value for row in preparation.dependencies).items())),
        "execution": None if preparation.execution is None else {
            "workers": preparation.execution.workers, "environment_id": preparation.execution.environment_id,
            "source_snapshot": None if preparation.execution.source_snapshot is None else preparation.execution.source_snapshot.to_document(),
            "output_root": preparation.execution.output_root},
        "draft_identity": None if preparation.draft is None else ObjectIdentity.from_record(preparation.draft.draft_id, preparation.draft).to_document()}
    report={"specification": result.specification.to_document(),
        "sources_path": str(result.source_selection_path), "source_selection": result.source_selection.to_document(),
        "preparation": summary, "requirements": result.requirements_publication.to_document(),
        "current_metadata_publications": [row.to_document() for row in result.publications],
        "scientific_authority": "NONE", "native_contact": "NONE"}
    if result.target_specification is not None:
        report.update(target_specification=result.target_specification.identity.to_document(),
            target_input_path=str(result.target_specification_path))
    return report
