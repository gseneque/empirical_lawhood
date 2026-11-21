# SPDX-License-Identifier: MPL-2.0
"""Public gas-start selection, ordinary authoring and original endpoint reading."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_selection import GasRelaxationSelection, prepare_gas_relaxation_selection, validate_gas_relaxation_model


__all__ = ('GasRelaxationSelection', 'prepare_gas_relaxation_selection', 'author_gas_relaxation', 'read_gas_relaxation')


def author_gas_relaxation(*, selection, representation, raw_topology, raw_coordinates,
        project_root, work_directory, artifact_writer, output_dir):
    """Publish exact original inputs and author one task, without native execution."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_native import gas_relaxation_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_operation import AcceleratedGasRelaxationConfig, GasRelaxationConfig, native_input_records
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_translation import gas_relaxation_draft
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import prepare_raw_sources
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest

    validate_gas_relaxation_model(selection, representation)
    gas_relaxation_coordinates(selection=selection, representation=representation,
        raw_topology=raw_topology, raw_coordinates=raw_coordinates)
    sources = prepare_raw_sources(selection.prototype, raw_topology, raw_coordinates)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name+'-native-inputs')
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError('gas relaxation authoring requires fresh direct-input custody')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    config_type = AcceleratedGasRelaxationConfig if accelerated_engine(selection.prototype.engine) else GasRelaxationConfig
    config = config_type('config.gas-relaxation.'+selection.fingerprint(), selection, sources.identity,
        representation.canonical_size_bytes(), sources.canonical_size_bytes(), implementation, str(work_directory), provenance)
    draft = gas_relaxation_draft(config)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    bindings = []
    for name, pin, record in native_input_records(config, representation, sources):
        path = relative+'/'+name+'.json'
        size = record.canonical_size_bytes()
        block_size = min(size, 2**20)
        chunks = (chunk[offset:offset+block_size] for chunk in record.canonical_chunks()
            for offset in range(0, len(chunk), block_size))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(pin.object_id, path, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'gas-relaxation.native-inputs.'+config.fingerprint(),
            relative, chunks, maximum_bytes=size, maximum_chunk_bytes=block_size,
            expected_size_bytes=size, expected_physical_sha256=pin.object_fingerprint,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append(('external.gas-relaxation.'+name, artifact_writer.root.resolve(path, for_write=False)))
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=tuple(bindings))
    return {**result, 'native_input_paths': {key: str(path) for key, path in bindings}}


def read_gas_relaxation(*, config, representation, original_result, native_subwork, assessor_source, readout_id):
    """Authenticate the complete original attempt and independently inspect its endpoint."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_read import read_relaxation
    return read_relaxation(config=config, representation=representation, original_result=original_result,
        native_subwork=native_subwork, assessor_source=assessor_source, readout_id=readout_id)
