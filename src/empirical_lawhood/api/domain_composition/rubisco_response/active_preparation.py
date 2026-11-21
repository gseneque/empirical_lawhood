# SPDX-License-Identifier: MPL-2.0
"""Prepare finite paired prefixes for the ordinary inquiry author/run/read route."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_selection import prepare_active_preparation_prefix


def validate_prefix_file_selection(*, model_files, native_work_directory):
    """Check the complete explicit locator selection before scientific reads."""
    from empirical_lawhood.api.application_contracts import absolute_path, exact_mapping
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS
    roles = ('preparation', 'prototype', 'representation', 'topology', 'coordinates')
    exact_mapping(model_files, MODELS, required=MODELS)
    for name in MODELS:
        exact_mapping(model_files[name], roles, required=roles)
        for role in roles:
            absolute_path(model_files[name][role], 'model_files.' + name + '.' + role)
    absolute_path(native_work_directory, 'native_work_directory')


def prepare_response_prefix_from_files(*, design_file, plan_file, model_files, native_work_directory,
        root_directory, root_contribution, project_root, artifact_writer):
    """Join bounded original files and the actual root through existing owners.

    File locators select original operands. The frozen plan and scientific
    context establish their identities. This function neither publishes nor
    acquires anything; ordinary inquiry commitment and authoring follow it.
    """
    from empirical_lawhood.api.application_contracts import absolute_path
    from empirical_lawhood.api.configuration import load_configuration_record
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution
    from empirical_lawhood.api.recursive_inquiry_read import inquiry_projection_read
    from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import MAX_PREPARATION
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import MatchedActiveRelaxationPlan
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import actual_assessment
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import MAX_CONFIG, MAX_MODEL, MAX_RAW_SOURCES
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, PreparationResponseContext
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    validate_prefix_file_selection(model_files=model_files, native_work_directory=native_work_directory)
    for field, path in (('design_file', design_file), ('plan_file', plan_file),
            ('root_directory', root_directory), ('root_contribution', root_contribution), ('project_root', project_root)):
        absolute_path(path, field)
    def record(path, kind, maximum):
        return decode_canonical_bytes(read_bounded_bytes(Path(path), maximum_bytes=maximum), kind, maximum_bytes=maximum)
    design = load_configuration_record(Path(design_file))
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import require_response_design
    require_response_design(design)
    plan = record(plan_file, MatchedActiveRelaxationPlan, MAX_CONFIG)
    if plan.identity != design.prefix.plan:
        raise ValueError('response design changes its original matched plan')
    with inquiry_projection_read(artifact_writer) as reading:
        root = reading.wave(directory=Path(root_directory), include_products=True)
        assessment = actual_assessment(root.draft, root.products)[3][0]
        parent = authenticate_recursive_contribution(directory=Path(root_contribution), artifact_writer=reading.writer)[2]
        context = PreparationResponseContext(design, assessment, parent)
    models = []
    for name in MODELS:
        files = model_files[name]
        models.append((name, record(files['preparation'], ActiveModelPreparation, MAX_PREPARATION),
            record(files['prototype'], PeriodicProbeSelection, MAX_CONFIG),
            record(files['representation'], MolecularRepresentation, MAX_MODEL),
            read_bounded_bytes(Path(files['topology']), maximum_bytes=MAX_RAW_SOURCES),
            read_bounded_bytes(Path(files['coordinates']), maximum_bytes=MAX_RAW_SOURCES),
            Path(native_work_directory) / name))
    return prepare_paired_active_preparation(plan=plan, prefix=design.prefix, models=tuple(models),
        project_root=project_root, scientific_context=context)


def prepare_paired_active_preparation(*, plan, prefix, models, project_root, scientific_context=None):
    """Return a code-derived paired draft and complete original direct inputs.

    Each model row supplies name, preparation, prototype, representation, raw
    topology, raw coordinates and explicit native work directory, in that order.
    The inquiry owner commits its intent before authoring this selected draft.
    """
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.domain_composition.rubisco_response.active_relaxation import prepare_active_relaxation_inputs
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_type, native_input_records
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_translation import active_preparation_prefix_draft, external_id
    if type(models) is not tuple or len(models) != 2 or tuple(row[0] for row in models) != ('m1-i95m', 'm1-wt'):
        raise ValueError('paired preparation requires the two original M1 members in canonical order')
    if scientific_context is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import validate_response_environment_sources
        if is_environmental(scientific_context.design):
            validate_response_environment_sources(environment=scientific_context.design.environment,
                models={row[0]: row[3] for row in models}, preparations={row[0]: row[1] for row in models},
                prototypes={row[0]: row[2] for row in models},
                formation_coordinates=scientific_context.design.formation_coordinates)
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    configs, records = [], {}
    for name, prepared, prototype, representation, raw_topology, raw_coordinates, work_directory in models:
        original, sources = prepare_active_relaxation_inputs(plan=plan, model_name=name, prepared=prepared,
            prototype=prototype, representation=representation, raw_topology=raw_topology, raw_coordinates=raw_coordinates,
            project_root=project_root, work_directory=work_directory, conditional_selection=prefix.conditional,
            implementation=implementation, provenance=provenance)
        config = config_type(original.ACCELERATED)('config.active-prefix.' + name + '.' + prefix.fingerprint(),
                                                  original, prefix, scientific_context)
        configs.append(config)
        for port, pin, record in native_input_records(config, representation, prepared, sources):
            key = external_id(config, port)
            if key in records and records[key] != (pin, record):
                raise ValueError('paired preparation substitutes a shared source input')
            records[key] = (pin, record)
    configs = tuple(configs)
    return {'configs': configs, 'draft': active_preparation_prefix_draft(configs),
            'external_records': tuple((key, *records[key]) for key in sorted(records))}


def retain_preparation_prefix_inputs(*, prepared, artifact_writer, output_dir):
    """Retain exact source inputs for a committed inquiry successor; do not author twice."""
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    root = Path(artifact_writer.root.contract.canonical_path)
    destination = Path(output_dir)
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise ValueError('preparation inputs require a fresh absolute custody destination')
    relative = destination.relative_to(root).as_posix()
    external = {row.input_id: row for row in prepared['draft'].external_inputs}
    bindings = []
    for key, pin, record in prepared['external_records']:
        if external[key].scientific_role == 'HISTORY':
            continue  # The ordinary contribution importer owns these original bytes.
        binary = type(record) is bytes
        path = relative + '/' + key + ('.gz' if binary else '.json')
        size = len(record) if binary else record.canonical_size_bytes()
        block_size = min(size, 2**20)
        chunks = ((record[offset:offset + block_size] for offset in range(0, size, block_size)) if binary else
            (chunk[offset:offset + block_size] for chunk in record.canonical_chunks()
             for offset in range(0, len(chunk), block_size)))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(pin.object_id, path, pin.object_schema,
            ArtifactProfile.RAW_SOURCE_BYTES if binary else ArtifactProfile.CANONICAL_JSON,
            external[key].media_type, 'active-prefix.native-inputs.' + prepared['draft'].fingerprint(),
            relative, chunks, maximum_bytes=size, maximum_chunk_bytes=block_size,
            expected_size_bytes=size, expected_physical_sha256=pin.object_fingerprint,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((key, artifact_writer.root.resolve(path, for_write=False)))
    return tuple(bindings)


def prepare_prefix_continuation(*, prefix_directory, prefix_contribution, native_work_directory,
                                project_root, artifact_writer):
    """Prepare the original paired remainder using authenticated completed custody.

    An unreceipted contact has no automatic continuation route. This preparer
    reopens the original publisher and every complete archive while their
    verification lifetime remains active. Ordinary inquiry commitment follows.
    """
    from dataclasses import replace
    from empirical_lawhood.api.application_contracts import absolute_path
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution
    from empirical_lawhood.api.recursive_inquiry_read import inquiry_projection_read
    from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import prepare_continuation, read_continuation_files
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import actual_products
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_type, native_input_records, node_id
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_translation import active_preparation_prefix_draft, external_id, selected_configs
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import checked_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeRawSources
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import _input, _native_result_reader
    for field, path in (('prefix_directory', prefix_directory), ('prefix_contribution', prefix_contribution),
            ('native_work_directory', native_work_directory), ('project_root', project_root)):
        absolute_path(path, field)
    implementation = implementation_binding(project_root)
    configs, records = [], {}
    with artifact_writer.read_context() as writer, inquiry_projection_read(writer) as reading:
        original = reading.wave(directory=Path(prefix_directory), include_products=True)
        previous_configs = selected_configs(original.draft)
        if any(c.original.implementation != implementation for c in previous_configs):
            raise ValueError('preparation continuation requires the exact original producing source and lock')
        if len(actual_products(original.draft, original.products)) != 4:
            raise ValueError('preparation continuation lacks completed original paired publications; preserve uncertain contact')
        parent = authenticate_recursive_contribution(directory=Path(prefix_contribution), artifact_writer=reading.writer)[2]
        external = {row.input_id: row for row in original.draft.external_inputs}
        failed = False
        for previous in previous_configs:
            name = previous.original.model_name
            model = _input(original.payloads, external[external_id(previous, 'native-model')], MolecularRepresentation)
            preparation = _input(original.payloads, external[external_id(previous, 'native-preparation')], ActiveModelPreparation)
            sources = _input(original.payloads, external[external_id(previous, 'native-source')], PeriodicProbeRawSources)
            coordinates = checked_coordinates(previous.original, model, preparation, sources)
            readout = original.products['records'][node_id(previous)][node_id(previous) + '.assessment']
            result = readout.original_result
            failed |= result.unit.returned.error is not None
            store = _native_result_reader(reading.writer, result)
            completed = store.recover(result.unit.definition)
            if (completed is None or completed.completion != result.unit.completion or completed.receipt != result.unit.receipt):
                raise ValueError('preparation continuation lacks original native completion custody')
            archive, = (m for m in completed.outputs if m.logical.logical_artifact_id.endswith('.output.files.raw'))
            continuation = prepare_continuation(previous=previous, readout=readout, archive=archive, parent=parent)
            raw = b''.join(store.iter_completed_output(result.unit.definition, 'files.raw'))
            read_continuation_files(continuation, raw, representation=model, prepared=preparation, coordinate_bytes=coordinates)
            config = config_type(previous.ACCELERATED, continuation=True)(
                'config.continued-prefix.' + name + '.' + continuation.fingerprint(),
                replace(previous.original, work_directory=str(Path(native_work_directory) / name)),
                previous.prefix, previous.scientific_context, continuation=continuation)
            configs.append(config)
            for role, pin, record in (*native_input_records(config, model, preparation, sources),
                    ('native-continuation-archive', continuation.archive_identity, raw)):
                key = external_id(config, role)
                if key in records and records[key] != (pin, record):
                    raise ValueError('preparation continuation substitutes a shared original input')
                records[key] = pin, record
        if not failed:
            raise ValueError('completed prefixes require original publication reuse, not a new continuation')
    configs = tuple(configs)
    return dict(configs=configs, draft=active_preparation_prefix_draft(configs),
        external_records=tuple((key, *records[key]) for key in sorted(records)))


def read_active_preparation_prefix(**kwargs):
    """Return independently checked original checkpoints, failures and full denominators."""
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import read_preparation_prefix
    return read_preparation_prefix(**kwargs)


__all__ = ['prepare_active_preparation_prefix', 'prepare_paired_active_preparation',
           'prepare_response_prefix_from_files', 'prepare_prefix_continuation', 'validate_prefix_file_selection',
           'retain_preparation_prefix_inputs', 'read_active_preparation_prefix']
