# SPDX-License-Identifier: MPL-2.0
"""Public preparation, shared authoring and original reading of periodic controls."""
from pathlib import Path


def prepare_periodic_numerical_controls(*, prototype, coordinate_bytes, required_refinement_kinds, directions=(), steps_bohr=(), refinements=(),
        maximum_directional_error_hartree_per_bohr=None, maximum_step_change_hartree_per_bohr=None):
    """Select every numerical point and required refinement before new returns.

    Refinements carry explicit, prospective sensitivity budgets. An empty
    required_refinement_kinds tuple explicitly limits the selection's coverage;
    directional conformance alone does not establish force accuracy.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import prepare_periodic_controls
    return prepare_periodic_controls(prototype=prototype, coordinate_bytes=coordinate_bytes, directions=directions,
        steps_bohr=steps_bohr, refinements=refinements, required_refinement_kinds=required_refinement_kinds,
        maximum_directional_error_hartree_per_bohr=maximum_directional_error_hartree_per_bohr,
        maximum_step_change_hartree_per_bohr=maximum_step_change_hartree_per_bohr)


def prepare_receiver_refinement_budget(*, budget_id, receiver, useful_error_hartree_per_bohr,
        numerical_allowance_fraction, receiver_l1_norm, justification):
    """Derive a declared one-force receiver sensitivity budget with physical units."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import refinement_budget_from_receiver
    return refinement_budget_from_receiver(budget_id=budget_id, receiver=receiver,
        useful_error_hartree_per_bohr=useful_error_hartree_per_bohr,
        numerical_allowance_fraction=numerical_allowance_fraction, receiver_l1_norm=receiver_l1_norm,
        justification=justification)


def read_periodic_molecular_precision(*, config, representation, coordinate_bytes, original_result, native_subwork,
        assessor_source, readout_id):
    """Compare authenticated same-geometry MM operands without new native calls."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_read import read_periodic_molecular_precision as read
    return read(config=config, representation=representation, coordinate_bytes=coordinate_bytes,
        original_result=original_result, native_subwork=native_subwork, assessor_source=assessor_source,
        readout_id=readout_id)


def prepare_formation_response_direction(*, coordinate, prototype, coordinate_bytes):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_physical_direction import prepare_formation_response_direction as prepare
    return prepare(coordinate=coordinate, prototype=prototype, coordinate_bytes=coordinate_bytes)


def prepare_periodic_force_actions(*, prototype, coordinate_bytes, directions, steps_bohr):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import prepare_periodic_force_actions as prepare
    return prepare(prototype=prototype, coordinate_bytes=coordinate_bytes, directions=directions, steps_bohr=steps_bohr)


def author_periodic_numerical_controls(*, protocol, prototype, representation, raw_topology, raw_coordinates,
        project_root, work_directory, artifact_writer, output_dir):
    """Derive and author the complete finite graph with one shared resource lock."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_operation import config_kind, native_input_records, selected_request
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import control_points, validate_control_prototype
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_translation import external_id, periodic_controls_draft
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import config_kind as probe_config_kind, prepare_raw_sources
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    validate_control_prototype(protocol, prototype)
    sources = prepare_raw_sources(prototype, raw_topology, raw_coordinates)
    raw = original_coordinates(prototype, representation, sources)
    points = control_points(protocol, raw)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name+'-native-inputs')
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError('periodic controls authoring requires fresh direct-input custody')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,
        expected_lock_sha256=implementation.dependency_lock_sha256)
    accelerated = accelerated_engine(prototype.engine)
    original = probe_config_kind(accelerated=accelerated)('config.periodic-controls.original.'+protocol.fingerprint(), prototype,
        sources.identity, representation.canonical_size_bytes(), sources.canonical_size_bytes(), implementation,
        str(work_directory), provenance)
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import PeriodicForceActionProtocol
    configs = tuple(config_kind(accelerated=accelerated, force_actions=type(protocol) is PeriodicForceActionProtocol)(
        'config.'+point.point_id, original, protocol, point) for point in points)
    draft = periodic_controls_draft(configs)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    scope = 'periodic-controls.native-inputs.'+protocol.fingerprint()
    records = {}
    shared = native_input_records(configs[0], representation, sources)
    for config in configs:
        for name, pin, record in shared:
            if name == 'native-point':
                record = config.point
                pin = record.identity
            elif name == 'native-request':
                record = selected_request(config)
                pin = record.identity
            key = external_id(config, name)
            if key in records and records[key][0] != pin:
                raise ValueError('periodic controls authoring changes an original shared input')
            records[key] = (pin, record)
    bindings = []
    for key in sorted(records):
        pin, record = records[key]
        path = relative+'/'+key+'.json'
        size = record.canonical_size_bytes()
        block_size = min(size, 2**20)
        chunks = (chunk[offset:offset+block_size] for chunk in record.canonical_chunks()
            for offset in range(0, len(chunk), block_size))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(pin.object_id, path, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', scope, relative, chunks,
            maximum_bytes=size, maximum_chunk_bytes=block_size, expected_size_bytes=size,
            expected_physical_sha256=pin.object_fingerprint,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((key, artifact_writer.root.resolve(path, for_write=False)))
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=tuple(bindings))
    return {**result, 'point_ids': tuple(p.point_id for p in points),
        'native_input_paths': {key:str(path) for key, path in bindings}}


def read_periodic_numerical_controls(*, configs, representation, coordinate_bytes, original_results,
        native_subwork_for_result, assessor_source, readout_id):
    """Authenticate retained returns and retain missing points without native replay."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_read import read_periodic_controls
    return read_periodic_controls(configs=configs, representation=representation, coordinate_bytes=coordinate_bytes,
        original_results=original_results, native_subwork_for_result=native_subwork_for_result,
        assessor_source=assessor_source, readout_id=readout_id)


def read_periodic_force_actions(*, configs, representation, coordinate_bytes, original_results,
        native_subwork_for_result, assessor_source, readout_id):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_action_read import read_periodic_force_actions as read
    return read(configs=configs, representation=representation, coordinate_bytes=coordinate_bytes,
        original_results=original_results, native_subwork_for_result=native_subwork_for_result,
        assessor_source=assessor_source, readout_id=readout_id)


def recover_periodic_control_publication(*, config, definition, native_subwork):
    """Finish a known returned point's publication from its original complete bytes."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_publication_recovery import assemble_returned_control_publication
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    if type(native_subwork) is not ExternalNativeSubworkStore:
        raise TypeError("periodic publication recovery requires its guarded native custody owner")
    outputs = assemble_returned_control_publication(config=config, definition=definition,
        read_output=native_subwork.iter_returned_output)
    return native_subwork.recover_returned_publication(definition, canonical_outputs=outputs)
