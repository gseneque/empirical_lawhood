# SPDX-License-Identifier: MPL-2.0
"""Prepare, retain and independently read the selected paired response investigation."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import prepare_response_design



def prepare_environmental_response_design_from_files(*, design_file, model_files,
        residue_keys=(), region='COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE', coordinate_tolerance_angstrom=None):
    """Freeze prospective common protein support using complete original inputs."""
    from decimal import Decimal
    from empirical_lawhood.api.application_contracts import absolute_path, exact_mapping
    from empirical_lawhood.api.configuration import load_configuration_record
    from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import MAX_PREPARATION
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import MAX_CONFIG, MAX_MODEL
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, PreparationResponseDesign
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import prepare_response_environment
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    absolute_path(design_file, 'design_file')
    exact_mapping(model_files, MODELS, required=MODELS)
    roles = ('preparation', 'prototype', 'representation')
    for name in MODELS:
        exact_mapping(model_files[name], (*roles, 'topology', 'coordinates'), required=roles)
        for role, path in model_files[name].items():
            absolute_path(path, 'model_files.' + name + '.' + role)
    base = load_configuration_record(Path(design_file), consumer='rubisco-preparation-response-design')
    if type(base) is not PreparationResponseDesign:
        raise TypeError('environment design requires the original local response design revision')
    def record(path, kind, maximum):
        return decode_canonical_bytes(read_bounded_bytes(Path(path), maximum_bytes=maximum), kind, maximum_bytes=maximum)
    models, preparations, prototypes = {}, {}, {}
    for name in MODELS:
        files = model_files[name]
        models[name] = record(files['representation'], MolecularRepresentation, MAX_MODEL)
        preparations[name] = record(files['preparation'], ActiveModelPreparation, MAX_PREPARATION)
        prototypes[name] = record(files['prototype'], PeriodicProbeSelection, MAX_CONFIG)
    environment = prepare_response_environment(models=models, preparations=preparations, prototypes=prototypes,
        formation_coordinates=base.formation_coordinates, region=region, residue_keys=residue_keys,
        coordinate_tolerance_angstrom=(Decimal('0.000001') if coordinate_tolerance_angstrom is None
            else coordinate_tolerance_angstrom))
    return prepare_response_design(prefix=base.prefix, root_assessment=base.root_assessment,
        formation_coordinates=base.formation_coordinates, steps_bohr=base.steps_bohr,
        challenge_amplitude_bohr=base.challenge_amplitude_bohr,
        reference_temperature_kelvin=base.reference_temperature_kelvin,
        useful_error_work_fraction_rt=base.useful_error_work_fraction_rt,
        numerical_allowance_fraction=base.numerical_allowance_fraction, environment=environment)


def apply_environmental_nomination(*, checkpoints, assessment):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import EnvironmentalPreparationResponseAssessment
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import prepare_environmental_frames
    design = checkpoints['design']
    if not is_environmental(design):
        return checkpoints
    if (type(assessment) is not EnvironmentalPreparationResponseAssessment or assessment.design != design
            or assessment.nomination is None):
        raise ValueError('environment response requires its original independently assessed nomination')
    frames = prepare_environmental_frames(design=design, frames=checkpoints['frames'], nomination=assessment.nomination)
    return dict(checkpoints, frames=frames)


def prepare_response_checkpoints(*, design, prefixes):
    """Reopen both original prefix packages and derive all four fixed-frame centers.

    Each tuple contains name, config, model, preparation, original coordinate
    bytes, original result and the ordinary native-subwork reader, in order.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import node_id
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import read_preparation_prefix
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import prepare_response_frame
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import prepare_response_center
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from threadpoolctl import threadpool_limits
    if type(prefixes) is not tuple or tuple(row[0] for row in prefixes) != ('m1-i95m', 'm1-wt'):
        raise ValueError('response centers require both original M1 preparation packages')
    centers, frames, raw, readouts = {}, {}, {}, {}
    for name, config, model, preparation, coordinates, result, custody in prefixes:
        implementation = config.original.implementation
        if config.original.model_name != name or config.prefix != design.prefix:
            raise ValueError('response centers change the selected original preparation purchase')
        # Center/frame construction also reconstructs optimizer state. Preserve
        # the original numerical setting through that complete scientific read.
        with threadpool_limits(limits=config.original.prototype.engine.numerical_threads):
            readout, arrays, _ = read_preparation_prefix(config=config, representation=model, prepared=preparation,
                coordinate_bytes=coordinates, original_result=result, native_subwork=custody,
                assessor_source=ObjectIdentity.from_record('source.active-preparation-assessor.' +
                    implementation.code_sources_sha256, implementation), readout_id=node_id(config) + '.assessment',
                include_operands=True)
            readouts[name] = readout
            if readout.assessment is None or any(p.disposition != 'AVAILABLE' for p in readout.assessment.positions):
                continue
            checkpoints = {r.checkpoint.identity: r.checkpoint for r in readout.assessment.checkpoints}
            for row in readout.assessment.positions:
                checkpoint = checkpoints[row.checkpoint]
                center, data = prepare_response_center(design=design, readout=readout, position=row.position,
                    checkpoint=checkpoint, checkpoint_arrays=arrays[checkpoint.identity])
                centers[name, row.position], raw[name, row.position] = center, data
                if row.position == 'initial':
                    frames[name] = prepare_response_frame(design=design, model_name=name, checkpoint=checkpoint,
                        arrays=arrays[checkpoint.identity], prototype=config.original.prototype)
    return dict(design=design, centers=centers, frames=frames, center_bytes=raw, original_readouts=readouts,
        checkpoint_status='AVAILABLE' if len(centers) == 4 else 'UNAVAILABLE_PAIRED_HANDOFF')


def prepare_preparation_response_stage(*, checkpoints, stage, models, project_root, preparation_parent, predictions=(),
                                      diagnostic=None, diagnostic_parent=None):
    """Return the complete code-derived stage for preview, commitment and authoring.

    Model rows contain name, prototype, representation, raw topology, raw
    coordinates and an explicit native work directory. This function does not
    execute or authorize the selected purchase.
    """
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import config_kind, prepare_raw_sources
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import response_effects
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import config_type, native_input_records
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import prepare_response_point
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import external_id, preparation_response_draft
    if (type(models) is not tuple or tuple(row[0] for row in models) != ('m1-i95m', 'm1-wt')
            or preparation_parent is None):
        raise ValueError('response preparation requires its actual paired originals and preparation contribution')
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, POSITIONS
    if (set(checkpoints['centers']) != set(POSITIONS) or set(checkpoints['center_bytes']) != set(POSITIONS)
            or set(checkpoints['frames']) != set(MODELS)):
        raise ValueError('response acquisition lacks four independently accepted checkpoint positions; retain and reassess the original prefix readout')
    design = checkpoints['design']
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
    if is_environmental(design):
        if stage == 'initial-primary':
            from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import environment_coordinate_discrepancy
            from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import read_response_center
            coordinates = {name: read_response_center(checkpoints['centers'][name, 'initial'],
                checkpoints['center_bytes'][name, 'initial'])[0] for name in MODELS}
            if environment_coordinate_discrepancy(design.environment, coordinates) > design.environment.coordinate_tolerance_angstrom:
                raise ValueError('environment coordinate correspondence is invalid; assess with empty response_directories to retain the outcome before native actions')
        else:
            checkpoints = apply_environmental_nomination(checkpoints=checkpoints, assessment=diagnostic)
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    originals = {}
    for name, prototype, model, raw_topology, raw_coordinates, work_directory in models:
        sources = prepare_raw_sources(prototype, raw_topology, raw_coordinates)
        accelerated = accelerated_engine(prototype.engine)
        original = config_kind(accelerated=accelerated)('config.response-base.' + name + '.' + design.fingerprint(),
            prototype, sources.identity, model.canonical_size_bytes(), sources.canonical_size_bytes(), implementation,
            str(work_directory), provenance)
        originals[name] = (original, model, sources)
    predictions = dict(predictions)
    configs, records = [], {}
    for effect in response_effects(design, stage):
        key = (effect.model_name, effect.position)
        original, model, sources = originals[effect.model_name]
        center, frame, raw = checkpoints['centers'][key], checkpoints['frames'][effect.model_name], checkpoints['center_bytes'][key]
        point = prepare_response_point(design=design, center=center, frame=frame, effect=effect,
            prototype=original.selection, center_bytes=raw, prediction=predictions.get(key))
        config = config_type(original.ACCELERATED)('config.' + point.point_id, original, design, center, frame, point,
            preparation_parent, diagnostic, diagnostic_parent)
        configs.append(config)
        for role, pin, record in (*native_input_records(config, model, sources), ('native-center-bytes', center.center_bytes, raw)):
            input_id = external_id(config, role)
            if input_id in records and records[input_id] != (pin, record):
                raise ValueError('response preparation substitutes an original shared input')
            records[input_id] = (pin, record)
    configs = tuple(configs)
    return dict(configs=configs, draft=preparation_response_draft(configs), checkpoints=checkpoints,
        external_records=tuple((key, *records[key]) for key in sorted(records)))


def retain_response_inputs(*, prepared, artifact_writer, output_dir):
    """Retain complete direct operands for the committed ordinary inquiry successor."""
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    destination = Path(output_dir)
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise ValueError('response inputs require a fresh absolute custody destination')
    relative = destination.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    history = {e.input_id for e in prepared['draft'].external_inputs if e.scientific_role == 'HISTORY'}
    bindings = []
    for key, pin, record in prepared['external_records']:
        if key in history:
            continue  # The ordinary contribution importer retains the original product.
        binary = type(record) is bytes
        path = relative + '/' + key + ('.bin' if binary else '.json')
        size = len(record) if binary else record.canonical_size_bytes()
        maximum = min(size, 2**20)
        if binary:
            chunks = (record[offset:offset + maximum] for offset in range(0, size, maximum))
        else:
            chunks = (chunk[offset:offset + maximum] for chunk in record.canonical_chunks()
                for offset in range(0, len(chunk), maximum))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(pin.object_id, path, pin.object_schema,
            ArtifactProfile.RAW_SOURCE_BYTES if binary else ArtifactProfile.CANONICAL_JSON,
            'application/octet-stream' if binary else 'application/json', 'preparation-response.inputs.' + prepared['draft'].fingerprint(),
            relative, chunks, maximum_bytes=size, maximum_chunk_bytes=maximum, expected_size_bytes=size,
            expected_physical_sha256=pin.object_fingerprint, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((key, artifact_writer.root.resolve(path, for_write=False)))
    return tuple(bindings)


def read_preparation_response(**kwargs):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import read_preparation_response as read
    return read(**kwargs)


def freeze_response_predictions(**kwargs):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import freeze_response_predictions as freeze
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import prepare_environmental_frames
    assessment = kwargs['assessment']
    if is_environmental(assessment.design):
        kwargs['frames'] = prepare_environmental_frames(design=assessment.design, frames=kwargs['frames'],
            nomination=assessment.nomination)
    return freeze(**kwargs)


__all__ = ['prepare_environmental_response_design_from_files', 'apply_environmental_nomination', 'prepare_response_design', 'prepare_response_checkpoints', 'prepare_preparation_response_stage',
           'retain_response_inputs', 'read_preparation_response', 'freeze_response_predictions']
