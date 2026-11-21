# SPDX-License-Identifier: MPL-2.0
"""Prepare, author and independently read diagnostic reference trajectories."""

from pathlib import Path


def prepare_reference_trajectory(*, prototype, representation, phase_source, initial_angstrom,
        initial_velocity_nm_per_ps, settings, criteria=None, density_guess_policy='COLD'):
    """Freeze supplied complete phase space without inventing an initial ensemble."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import prepare_reference_trajectory as prepare
    return prepare(prototype=prototype, representation=representation, phase_source=phase_source,
        initial_angstrom=initial_angstrom, initial_velocity_nm_per_ps=initial_velocity_nm_per_ps,
        settings=settings, criteria=criteria, density_guess_policy=density_guess_policy)


def author_reference_trajectory(*, selection, prototype, representation, raw_topology, raw_coordinates,
        phase_bytes, project_root, work_directory, artifact_writer, output_dir, lineage_parents=()):
    """Use shared authoring, exact direct inputs and the existing native resource lock."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import config_kind as probe_config_kind, prepare_raw_sources
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import config_kind, native_input_records
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import read_phase_space, validate_trajectory_prototype
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_translation import reference_trajectory_draft
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    validate_trajectory_prototype(selection, prototype)
    sources = prepare_raw_sources(prototype, raw_topology, raw_coordinates)
    original_coordinates(prototype, representation, sources)
    read_phase_space(selection, representation, phase_bytes)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name+'-native-inputs')
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError('trajectory authoring requires fresh direct-input custody')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,
        expected_lock_sha256=implementation.dependency_lock_sha256)
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    accelerated = accelerated_engine(prototype.engine)
    original = probe_config_kind(accelerated=accelerated)('config.reference-trajectory.original.'+selection.fingerprint(), prototype,
        sources.identity, representation.canonical_size_bytes(), sources.canonical_size_bytes(), implementation,
        str(work_directory), provenance)
    config = config_kind(accelerated=accelerated)('config.reference-trajectory.'+selection.fingerprint(), original, selection)
    draft = reference_trajectory_draft(config)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    scope = 'reference-trajectory.native-inputs.'+selection.fingerprint()
    records = {name:(pin, record) for name, pin, record in native_input_records(config, representation, sources)}
    bindings = []
    for row in draft.external_inputs:
        name = row.input_id.removeprefix('external.reference-trajectory.')
        is_phase = name == 'native-phase'
        path = relative+'/'+row.input_id+('.bin' if is_phase else '.json')
        size = row.maximum_size_bytes
        block_size = min(size, 2**20)
        parts = (phase_bytes,) if is_phase else records[name][1].canonical_chunks()
        chunks = (part[offset:offset+block_size] for part in parts for offset in range(0, len(part), block_size))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(row.logical_artifact_id, path, row.payload_schema,
            ArtifactProfile.RAW_SOURCE_BYTES if is_phase else ArtifactProfile.CANONICAL_JSON, row.media_type,
            scope, relative, chunks, maximum_bytes=size, maximum_chunk_bytes=block_size,
            expected_size_bytes=size, expected_physical_sha256=row.expected_content_sha256,
            lineage_parents=lineage_parents, parent_visibility_ceilings=tuple(p.visibility_ceiling for p in lineage_parents),
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((row.input_id, artifact_writer.root.resolve(path, for_write=False)))
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=tuple(bindings))
    return {**result, 'native_input_paths':{key:str(path) for key, path in bindings}}


def read_reference_trajectory(*, config, representation, phase_bytes, original_result, native_subwork, assessor_source):
    """Read a complete original attempt and its retained prefix without replay."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_read import read_reference_trajectory as read
    return read(config=config, representation=representation, phase_bytes=phase_bytes,
        original_result=original_result, native_subwork=native_subwork, assessor_source=assessor_source)
