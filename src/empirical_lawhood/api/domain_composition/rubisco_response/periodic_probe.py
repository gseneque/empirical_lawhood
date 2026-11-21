# SPDX-License-Identifier: MPL-2.0
"""Public authoring and retained reading of one periodic coupled force probe."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import config_kind, native_input_records, prepare_raw_sources, restart_selection, validate_force_selection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection


def select_periodic_numeric_engine(*, site_packages, interpreter, numerical_threads=1,
        host_memory_bytes=None, device_memory_bytes=None, additional_package_roots=(), molecular_platform=None):
    """Bind the complete explicitly selected numerical stock without device contact."""
    from hashlib import sha256
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import NUMERIC_PACKAGES, GPU_NUMERIC_PACKAGES, PeriodicNumericEngine, AcceleratedPeriodicNumericEngine, GpuReferencePeriodicNumericEngine
    from empirical_lawhood.storage.bounded_io import bounded_file_sha256
    from empirical_lawhood.execution.operational_configuration import accelerated_compute_enabled
    accelerated = accelerated_compute_enabled()
    if molecular_platform not in (None, 'CUDA', 'Reference') or not accelerated and molecular_platform is not None:
        raise ValueError('an explicit molecular platform requires accelerated compute and CUDA or Reference')
    root, executable = Path(site_packages), Path(interpreter)
    if (not root.is_absolute() or root.is_symlink() or root.resolve() != root
            or not executable.is_absolute() or executable.resolve() != executable):
        raise ValueError('numerical stock and interpreter require exact selected absolute real paths')
    if not accelerated and any(value is not None for value in (host_memory_bytes, device_memory_bytes)):
        raise ValueError('GPU allocations require accelerated_compute: true')
    if not accelerated and additional_package_roots:
        raise ValueError('CPU engine retains its original closed package census')
    packages = tuple(sorted(set(GPU_NUMERIC_PACKAGES) | set(additional_package_roots))) if accelerated else NUMERIC_PACKAGES
    files = []
    for name in packages:
        if type(name) is not str or Path(name).name != name or name in ('.', '..'):
            raise ValueError('numerical package root must be one selected directory name')
        directory = root/name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('selected numerical package is unavailable: '+name)
        for path in sorted(directory.rglob('*')):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError('numerical stock contains a link or special file')
            if path.is_file():
                size, digest = bounded_file_sha256(path, maximum_bytes=None)
                files.append(FileEvidence(path.relative_to(root).as_posix(), size, digest))
    files = tuple(sorted(files, key=lambda row: row.relative_path))
    interpreter_sha = bounded_file_sha256(executable, maximum_bytes=None)[1]
    digest = sha256((''.join(row.fingerprint() for row in files)+interpreter_sha).encode()).hexdigest()
    owner = AcceleratedPeriodicNumericEngine if accelerated else PeriodicNumericEngine
    if accelerated and molecular_platform == 'Reference':
        owner = GpuReferencePeriodicNumericEngine
        digest = 'reference-mm.'+digest
    return owner('engine.periodic.'+digest, str(root), files, str(executable), interpreter_sha, numerical_threads,
        **(dict(host_memory_bytes=host_memory_bytes, device_memory_bytes=device_memory_bytes,
                package_roots=packages) if accelerated else {}))


def prepare_periodic_force_probe(*, representation, path, cell, electronic, molecular, engine):
    """Derive complete selected operands without importing a numerical engine."""
    return prepare_periodic_probe_selection(representation=representation, path=path, cell=cell,
        electronic=electronic, molecular=molecular, engine=engine)


def author_periodic_force_probe(*, selection, representation, raw_topology, raw_coordinates,
                               project_root, work_directory, artifact_writer, output_dir):
    """Freeze one actual complete force/cost question through the shared author."""
    return _author_periodic_force(selection=selection, representation=representation, raw_topology=raw_topology,
        raw_coordinates=raw_coordinates, project_root=project_root, work_directory=work_directory,
        artifact_writer=artifact_writer, output_dir=output_dir)


def prepare_periodic_checkpoint_density(*, source_config, source_definition, representation, raw_sources,
        checkpoint_path, checkpoint):
    """Authenticate a frozen checkpoint and derive its complete initial density."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_density_seed import prepare_checkpoint_density
    return prepare_checkpoint_density(source_config=source_config, source_definition=source_definition,
        representation=representation, raw_sources=raw_sources, checkpoint_path=checkpoint_path, checkpoint=checkpoint)


def author_periodic_force_restart(*, prototype, seed, density_bytes, representation, raw_topology, raw_coordinates,
        project_root, work_directory, artifact_writer, output_dir):
    """Author a distinct force attempt with the authenticated checkpoint guess."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed import read_density_bytes
    selection = restart_selection(seed, prototype)
    read_density_bytes(seed, density_bytes)
    return _author_periodic_force(selection=selection, representation=representation, raw_topology=raw_topology,
        raw_coordinates=raw_coordinates, project_root=project_root, work_directory=work_directory,
        artifact_writer=artifact_writer, output_dir=output_dir, seed=seed, density_bytes=density_bytes)


def _author_periodic_force(*, selection, representation, raw_topology, raw_coordinates,
        project_root, work_directory, artifact_writer, output_dir, seed=None, density_bytes=None):
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_translation import periodic_probe_draft
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    from empirical_lawhood.execution.operational_configuration import accelerated_compute_enabled
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    accelerated = accelerated_compute_enabled()
    if accelerated != accelerated_engine(selection.engine):
        raise ValueError('periodic force engine differs from accelerated_compute; select its explicit numerical environment')
    validate_force_selection(selection, representation, seed)
    sources = prepare_raw_sources(selection, raw_topology, raw_coordinates)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name+'-native-inputs')
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError('periodic probe authoring requires fresh direct-input custody')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,
        expected_lock_sha256=implementation.dependency_lock_sha256)
    config_type = config_kind(restart=seed is not None, accelerated=accelerated)
    config = config_type('config.periodic-force.'+selection.fingerprint(), selection, sources.identity,
        representation.canonical_size_bytes(), sources.canonical_size_bytes(), implementation,
        str(work_directory), provenance, **({'seed':seed} if seed is not None else {}))
    draft = periodic_probe_draft(config)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    scope = 'periodic-force.native-inputs.'+config.fingerprint()
    bindings = []
    records = {name:record for name, _, record in native_input_records(config, representation, sources)}
    for row in draft.external_inputs:
        name = row.input_id.removeprefix('external.periodic-force.')
        binary = name == 'native-density'
        path = relative+'/'+name+('.bin' if binary else '.json')
        size = row.maximum_size_bytes
        block_size = min(size, 2**20)
        parts = (density_bytes,) if binary else records[name].canonical_chunks()
        chunks = (chunk[offset:offset+block_size] for chunk in parts
                  for offset in range(0, len(chunk), block_size))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(row.logical_artifact_id, path, row.payload_schema,
            ArtifactProfile.RAW_SOURCE_BYTES if binary else ArtifactProfile.CANONICAL_JSON,
            row.media_type, scope, relative, chunks,
            maximum_bytes=size, maximum_chunk_bytes=block_size, expected_size_bytes=size,
            expected_physical_sha256=row.expected_content_sha256,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append(('external.periodic-force.'+name, artifact_writer.root.resolve(path, for_write=False)))
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=tuple(bindings))
    return {**result, 'native_input_paths': {key:str(path) for key,path in bindings}}


def read_periodic_force_probe(*, config, representation, original_result, native_subwork,
                             assessor_source, readout_id):
    """Authenticate every original file and assess raw arrays without replay."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_read import read_periodic_probe
    return read_periodic_probe(config=config, representation=representation, original_result=original_result,
        native_subwork=native_subwork, assessor_source=assessor_source, readout_id=readout_id)
