# SPDX-License-Identifier: MPL-2.0
"""Freeze direct secondary mathematics on an existing current preparation."""
from pathlib import Path


def derive_input_selection(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Publish the selected target without reconstructing an old preparation."""
    from empirical_lawhood.api.experiment_preparation import _protocol, load_experiment_inputs
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
    from empirical_lawhood.api.configured_e3_secondary_target import derive_secondary_input_selection

    source, destination = Path(source_selection_path), Path(output_selection_path)
    metadata = Path(metadata_directory)
    if (not source.is_absolute() or not destination.is_absolute() or not metadata.is_absolute()
            or source.parent != destination.parent or source == destination):
        raise ValueError("derived selector needs an explicit distinct output under the selected input root")
    if any(path.is_symlink() for path in (source, *source.parents, destination, *destination.parents,
            metadata, *metadata.parents)):
        raise ValueError("configured selector derivation refuses symbolic links")
    plane = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    try:
        destination_relative = destination.relative_to(plane).as_posix()
        metadata.relative_to(source.parent)
        metadata.relative_to(plane)
    except ValueError as error:
        raise ValueError("derived selector and metadata must remain within the selected guarded input plane/root") from error
    artifact_writer.root.resolve(destination_relative, for_write=True)
    original_raw = read_bounded_bytes(source, maximum_bytes=_protocol(specification).maximum_config_bytes)
    selector = decode_canonical_bytes(original_raw, ExperimentFileInputSelection, maximum_bytes=len(original_raw))
    if (selector.protocol_id != _protocol(specification).protocol_id
            or set(row.key for row in selector.bindings) != {"protected-selection", "secondary-target"}):
        raise ValueError("configured derivation requires exactly the current selection and direct scientific target")
    inputs = load_experiment_inputs(specification, source, artifact_writer=artifact_writer, read_access=read_access)
    return derive_secondary_input_selection(specification=specification, inputs=inputs, selector=selector,
        source=source, destination=destination, metadata=metadata, original_raw=original_raw,
        artifact_writer=artifact_writer, execution=execution, project_root=project_root, read_access=read_access)
