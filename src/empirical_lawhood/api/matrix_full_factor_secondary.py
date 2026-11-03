# SPDX-License-Identifier: MPL-2.0
"""One pre-future E4 target publication and exact current retained custody."""
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryReadoutSelection, MatrixE4SecondaryTarget,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


def authenticate_e4_secondary_target(*, writer, selection, bank):
    """Authenticate the actual early carrier and every original response protocol."""
    if type(selection) is not MatrixE4SecondaryReadoutSelection:
        raise TypeError('E4 requires its exact pre-future target publication selection')
    selection.__post_init__()
    authenticate_published_materialization(writer, selection.publication)
    physical = selection.publication.materialization
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)
    target = decode_canonical_bytes(raw, MatrixE4SecondaryTarget, maximum_bytes=physical.size_bytes)
    selection.validate_target(target)
    if (target.canonical_bytes() != raw or target.mathematical_protocol != bank.forecast_design.criterion_record):
        raise PermissionError('E4 target changes exact early canonical bytes or original response-task mathematics')
    for protocol in bank.response_selection.protocols:
        target.validate_protocol(protocol)
    return target


def publish_e4_secondary_target(*, writer, directory, target, bank):
    """Publish only the declared blind convention, before the DEV entry seals it."""
    if type(target) is not MatrixE4SecondaryTarget:
        raise TypeError('E4 early publication requires its exact declared scientific target')
    target.__post_init__()
    if target.mathematical_protocol != bank.forecast_design.criterion_record:
        raise ValueError('E4 target changes original bank mathematics')
    for protocol in bank.response_selection.protocols:
        target.validate_protocol(protocol)
    directory = Path(directory)
    relative = directory.relative_to(writer.root.contract.canonical_path).as_posix()
    publication = writer.write(ArtifactWriteRequest(target.record_id, relative + '/secondary-target.json',
        target.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'e4.secondary.' + target.fingerprint(),
        relative, target.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    # Retain durable custody independent of whether this invocation created it.
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    publication = _publication_from_manifest(writer, writer.read_manifest(publication.materialization.relative_path))
    selected = MatrixE4SecondaryReadoutSelection(target.record_id + '.selection',
        target.mathematical_protocol.identity, target.identity, publication)
    if authenticate_e4_secondary_target(writer=writer, selection=selected, bank=bank) != target:
        raise PermissionError('E4 publication changes the declared pre-future target')
    return selected


def authenticate_full_factor_target(*, writer, request, bank):
    """Retained analysis selects the same target that actual acquisition sealed."""
    if type(request) not in (*domain.request_types(False), *domain.request_types(True)):
        raise TypeError('full factor secondary target requires its exact current lifecycle request')
    request.__post_init__()
    if request.bank != bank.identity:
        raise ValueError('full factor target substitutes its actual original bank')
    return authenticate_e4_secondary_target(writer=writer, selection=request.secondary_readout, bank=bank)


def derive_development_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Enrich copied DEV inputs through the ordinary derive-inputs command."""
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as development
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
    from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source, require_admitted_target_source_current
    from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult
    from empirical_lawhood.api.selected_e4_declarative import _write
    if type(specification) is not development.SelectedE3E4ExperimentSpecification:
        raise TypeError('E4 target derivation requires its exact current DEV specification')
    specification.__post_init__()
    source, metadata, destination = map(Path, (source_selection_path, metadata_directory, output_selection_path))
    if (not all(path.is_absolute() for path in (source, metadata, destination))
            or source.parent != destination.parent or source == destination
            or any(path.is_symlink() for value in (source, metadata, destination) for path in (value, *value.parents))):
        raise ValueError('E4 target derivation needs explicit unlinked sibling selectors and guarded metadata')
    root = Path(project_root).resolve(strict=True)
    require_selected_implementation(root)
    admitted = capture_admitted_target_source(root)
    plane = Path(artifact_writer.root.contract.canonical_path)
    metadata_relative = metadata.relative_to(plane).as_posix()
    metadata_to_inputs = metadata.relative_to(source.parent)
    if root == metadata or root in metadata.parents or metadata_relative in ('', '.'):
        raise ValueError('E4 target metadata requires a selected directory outside the checkout')
    original_raw = read_bounded_bytes(source, maximum_bytes=64 * 1024**2)
    selector = decode_canonical_bytes(original_raw, ExperimentFileInputSelection, maximum_bytes=len(original_raw))
    inputs = load_experiment_inputs(specification, source, artifact_writer=artifact_writer, read_access=read_access).method_inputs
    if type(inputs) is not development.SelectedE3E4Inputs or inputs.bank is None:
        raise ValueError('E4 target derivation requires the original declared DEV bank')
    def current():
        if read_bounded_bytes(source, maximum_bytes=len(original_raw)) != original_raw:
            raise PermissionError('E4 copied source selection changed during target derivation')
        require_admitted_target_source_current(root, admitted)
    current()
    target = specification.structure.secondary_target
    secondary = inputs.secondary_readout
    if secondary is None:
        secondary = publish_e4_secondary_target(writer=artifact_writer, directory=metadata, target=target, bank=inputs.bank)
    elif authenticate_e4_secondary_target(writer=artifact_writer, selection=secondary, bank=inputs.bank) != target:
        raise PermissionError('E4 cannot replace an already selected pre-future target')
    current()
    secondary_publication = _write(artifact_writer, metadata_relative + '/secondary-readout.json', secondary.record_id, secondary)
    records = {key: getattr(inputs, key) for key in ('programme', 'bank', 'evidence', 'campaign', 'resources')
        if getattr(inputs, key) is not None}
    records['secondary_readout'] = secondary
    prepared_inputs = development.bind_inputs(specification, records, files=dict(inputs.files))
    preparation = prepare_experiment(specification, scientific_inputs=prepared_inputs.scientific_inputs,
        method_inputs=prepared_inputs.method_inputs, execution=execution)
    bindings = {binding.key: binding for binding in selector.bindings if binding.key != 'secondary_readout'}
    bindings['secondary_readout'] = ExperimentInputBinding('secondary_readout', secondary.identity,
        (metadata_to_inputs / 'secondary-readout.json').as_posix(), len(secondary.canonical_bytes()))
    selected = ExperimentFileInputSelection(selector.selection_id + '.e4-target.' + target.fingerprint(),
        selector.protocol_id, tuple(bindings[key] for key in sorted(bindings)), selector.files)
    payload = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements', 'version': '1.0.0',
        'value': {'specification': specification.identity, 'secondary_target': target.identity,
            'secondary_readout': secondary.identity, 'authority': 'NONE', 'native_contact': 'NONE',
            'dependencies': tuple({'code': row.code, 'kind': row.kind.value, 'detail': row.detail,
                'source_key': row.source_key} for row in preparation.dependencies)}})
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    parents = () if inputs.evidence is None else inputs.evidence.produced_input_parents
    access, visibility = produced_access(declared_access=OutcomeAccess.OUTCOME_BLIND,
        declared_visibility=VisibilityCeiling.PROSPECTIVE, parents=parents)
    ceilings = tuple(parent.visibility_ceiling for parent in parents)
    current()
    requirements = artifact_writer.write(ArtifactWriteRequest('e4.requirements.' + sha256(payload).hexdigest(),
        metadata_relative + '/requirements.json', 'empirical-lawhood/operational/experiment-input-requirements',
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'e4.secondary.inputs', metadata_relative, payload,
        visibility, ceilings, access, lineage_parents=parents))
    current()
    selected_relative = destination.relative_to(plane).as_posix()
    publication = artifact_writer.write(ArtifactWriteRequest(selected.selection_id, selected_relative, selected.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'e4.secondary.inputs', str(Path(selected_relative).parent),
        selected.canonical_bytes(), visibility, ceilings, access, lineage_parents=parents))
    reopened = load_experiment_inputs(specification, destination, artifact_writer=artifact_writer, read_access=read_access)
    if reopened != prepared_inputs:
        raise PermissionError('E4 derived selector substitutes its early target or original scientific inputs')
    current()
    return ExperimentInputDerivationResult(specification.identity, selected, destination, preparation,
        (secondary.publication, secondary_publication, requirements, publication), requirements)
