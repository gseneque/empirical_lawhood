# SPDX-License-Identifier: MPL-2.0
"""Public matched active-state relaxation through ordinary recursive author/run/read."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import prepare_conditional_relaxation_selection, prepare_matched_relaxation_plan, validate_conditional_relaxation_selection, validate_relaxation_member


def prepare_matched_active_relaxation(*, models, settings):
    """Derive one exact four-material, eight-site, complete-state plan without native work."""
    return prepare_matched_relaxation_plan(models=models, settings=settings)


def prepare_conditional_active_relaxation(*, plan, state_census, assumptions):
    """Bind an explicit matched subset before native work or candidate-effect selection."""
    return prepare_conditional_relaxation_selection(plan=plan, state_census=state_census, assumptions=assumptions)


def prepare_active_relaxation_inputs(*, plan, model_name, prepared, prototype, representation,
        raw_topology, raw_coordinates, project_root, work_directory, conditional_selection=None,
        implementation=None, provenance=None):
    """Prepare the existing typed member configuration without authoring a wave."""
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import configuration_type
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import prepare_raw_sources
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine, validate_periodic_probe_model
    validate_relaxation_member(plan=plan, model_name=model_name, prepared=prepared, prototype=prototype, representation=representation)
    if conditional_selection is not None:
        validate_conditional_relaxation_selection(plan, conditional_selection)
    validate_periodic_probe_model(prototype, representation)
    sources = prepare_raw_sources(prototype, raw_topology, raw_coordinates)
    implementation = implementation_binding(project_root) if implementation is None else implementation
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,
        expected_lock_sha256=implementation.dependency_lock_sha256) if provenance is None else provenance
    config_type = configuration_type(conditional=conditional_selection is not None, accelerated=accelerated_engine(prototype.engine))
    extra = {} if conditional_selection is None else {'selection': conditional_selection}
    config_id = ('config.active-relaxation.'+model_name+'.'+plan.fingerprint() if conditional_selection is None
        else 'config.conditional-active-relaxation.'+model_name+'.'+conditional_selection.fingerprint())
    config = config_type(config_id, plan,
        model_name, prototype, prepared.identity, prepared.canonical_size_bytes(), prepared.seeds, representation.canonical_size_bytes(),
        sources.identity, sources.canonical_size_bytes(), implementation, str(work_directory), provenance, **extra)
    return config, sources


def author_active_relaxation(*, plan, model_name, prepared, prototype, representation, raw_topology, raw_coordinates,
                            project_root, work_directory, artifact_writer, output_dir, conditional_selection=None):
    """Freeze the full member or an explicit conditional subset with all original inputs."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import native_input_records
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_translation import active_relaxation_draft
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    config, sources = prepare_active_relaxation_inputs(plan=plan, model_name=model_name, prepared=prepared,
        prototype=prototype, representation=representation, raw_topology=raw_topology, raw_coordinates=raw_coordinates,
        project_root=project_root, work_directory=work_directory, conditional_selection=conditional_selection)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name+'-native-inputs')
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError('active relaxation authoring requires fresh direct-input custody')
    draft = active_relaxation_draft(config)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    bindings = []
    for name, pin, record in native_input_records(config, representation, prepared, sources):
        path = relative+'/'+name+'.json'
        size = record.canonical_size_bytes()
        block_size = min(size, 2**20)
        chunks = (chunk[offset:offset+block_size] for chunk in record.canonical_chunks()
            for offset in range(0, len(chunk), block_size))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(pin.object_id, path, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'active-relaxation.native-inputs.'+config.fingerprint(),
            relative, chunks, maximum_bytes=size, maximum_chunk_bytes=block_size,
            expected_size_bytes=size, expected_physical_sha256=pin.object_fingerprint,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append(('external.active-relaxation.'+name, artifact_writer.root.resolve(path, for_write=False)))
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=tuple(bindings))
    return {**result, 'native_input_paths':{key:str(path) for key, path in bindings}}


def read_active_relaxation(*, config, representation, prepared, coordinate_bytes, original_result,
                          native_subwork, assessor_source, readout_id):
    """Authenticate and assess every original attempt; never run or reconstruct a state."""
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_read import read_relaxation
    return read_relaxation(config=config, representation=representation, prepared=prepared,
        coordinate_bytes=coordinate_bytes, original_result=original_result, native_subwork=native_subwork,
        assessor_source=assessor_source, readout_id=readout_id)


def assess_matched_active_relaxation(*, plan, readouts, conditional_selection=None):
    """Retain the complete four-member denominator without inventing basin populations."""
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_read import assess_matched_readouts
    return assess_matched_readouts(plan=plan, readouts=readouts, conditional_selection=conditional_selection)
