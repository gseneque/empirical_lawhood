# SPDX-License-Identifier: MPL-2.0
"""Ordinary exact-byte target custody and configured selector enrichment."""
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE3SecondaryTarget, bind_secondary_selection
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


def authenticate_secondary_target(*, writer, selection):
    """Read the declared immutable carrier; never choose or default a tolerance."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import configured_preparation_types
    if type(selection) not in configured_preparation_types():
        raise TypeError("secondary readout requires the exact current configured preparation")
    if selection.secondary_readout is None:
        return None
    selection.__post_init__()
    current = selection.secondary_readout
    authenticate_published_materialization(writer, current.publication)
    physical = current.publication.materialization
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)
    document = decode_canonical_bytes(raw, MatrixE3SecondaryTarget, maximum_bytes=physical.size_bytes)
    if (document.canonical_bytes() != raw or document.identity != current.target
            or document.mathematical_protocol.identity != current.mathematical_protocol):
        raise PermissionError("secondary readout substitutes actual authenticated frozen target bytes")
    document.validate_selection(selection)
    return document.values(), document.identity


def derive_secondary_input_selection(*, specification, inputs, selector, source, destination,
        metadata, original_raw, artifact_writer, execution, project_root, read_access=None):
    """Enrich the actual selected source; retain its genuine native TRAIN operands."""
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
    from empirical_lawhood.infrastructure.source_closure import (
        capture_admitted_target_source, require_admitted_target_source_current,
    )
    from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult

    bound = inputs.method_inputs
    bound.__post_init__()
    if (bound.selection is None or bound.secondary_target is None
            or set(value.key for value in selector.bindings) != {"protected-selection", "secondary-target"}):
        raise ValueError("secondary derivation requires exactly current selection and direct scientific target")
    document = bound.secondary_target
    document.validate_selection(bound.selection)
    root = Path(project_root).resolve(strict=True)
    if metadata == root or root in metadata.parents:
        raise ValueError("secondary current metadata must be outside the selected checkout")
    require_selected_implementation(root)
    before = capture_admitted_target_source(root)
    plane = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    relative = metadata.relative_to(plane).as_posix()
    relative_inputs = metadata.relative_to(source.parent)
    if relative in ("", "."):
        raise ValueError("secondary metadata needs an explicitly separate guarded directory")
    payload = document.canonical_bytes()
    target_write = ArtifactWriteRequest("configured-secondary.target." + document.fingerprint(),
        relative + "/target." + document.fingerprint() + ".json", document.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "configured-secondary-inputs", relative, payload,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
    if getattr(bound.selection, "secondary_readout", None) is not None:
        if bound.selection.secondary_readout.target != document.identity:
            raise ValueError("an already frozen secondary target cannot be replaced")
        authenticate_secondary_target(writer=artifact_writer, selection=bound.selection)
        target_publication = bound.selection.secondary_readout.publication
    else:
        target_publication = artifact_writer.write(target_write)
    selected = bind_secondary_selection(bound.selection, document, target_publication)

    def selection_write(value):
        return ArtifactWriteRequest("configured-secondary.selection." + value.fingerprint(),
            relative + "/selection." + value.fingerprint() + ".json", value.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "configured-secondary-inputs", relative, value.canonical_bytes(),
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)

    # Retain the exact earlier write observation when this metadata transition
    # reopens. These are two exact candidate paths, never a directory scan.
    for created in (target_publication.created,) if getattr(bound.selection, "secondary_readout", None) is not None else (True, False):
        candidate = bind_secondary_selection(bound.selection, document, replace(target_publication, created=created))
        request = selection_write(candidate)
        preflight = artifact_writer._preflight_publication((request,))
        if artifact_writer._replay_committed_publication((request,), preflight) is not None:
            selected = candidate
            break
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import bind_protected_e3_experiment_inputs
    current = bind_protected_e3_experiment_inputs(specification, {"protected-selection": selected}, files=dict(bound.files))
    result = prepare_experiment(specification, scientific_inputs=current.scientific_inputs,
        method_inputs=current.method_inputs, execution=execution)
    binding = ExperimentInputBinding("protected-selection", ObjectIdentity.from_record(selected.selection_id, selected),
        (relative_inputs / ("selection." + selected.fingerprint() + ".json")).as_posix(), len(selected.canonical_bytes()))
    output = ExperimentFileInputSelection(selector.selection_id + ".secondary." + document.fingerprint(),
        selector.protocol_id, (binding,), selector.files)
    destination_relative = destination.relative_to(plane).as_posix()
    output_write = ArtifactWriteRequest("configured-secondary.sources." + output.fingerprint(), destination_relative,
        output.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "configured-secondary-inputs",
        destination_relative.rpartition("/")[0] or ".", output.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
    if read_bounded_bytes(source, maximum_bytes=len(original_raw)) != original_raw:
        raise PermissionError("secondary derivation original input selector changed before publication")
    require_admitted_target_source_current(root, before)
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from hashlib import sha256
    requirements = canonical_json_bytes({"schema": "empirical-lawhood/operational/experiment-input-requirements", "version": "1.0.0",
        "value": {"specification": specification.identity, "source_selection": ObjectIdentity.from_record(output.selection_id, output),
            "dependencies": tuple({"code": row.code, "kind": row.kind.value, "detail": row.detail, "source_key": row.source_key} for row in result.dependencies),
            "secondary_target": document.identity, "scientific_authority": "NONE", "native_contact": "NONE"}})
    requirements_write = ArtifactWriteRequest("configured-secondary.requirements." + sha256(requirements).hexdigest(),
        relative + "/requirements." + sha256(requirements).hexdigest() + ".json", "empirical-lawhood/operational/experiment-input-requirements",
        ArtifactProfile.CANONICAL_JSON, "application/json", "configured-secondary-inputs", relative, requirements,
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
    selection_publication = artifact_writer.write(selection_write(selected))
    requirements_publication = artifact_writer.write(requirements_write)
    output_publication = artifact_writer.write(output_write)
    reopened = load_experiment_inputs(specification, destination, artifact_writer=artifact_writer, read_access=read_access)
    if reopened != current:
        raise PermissionError("secondary selector changes its actual frozen target or original primary inputs")
    return ExperimentInputDerivationResult(specification.identity, output, destination, result,
        (target_publication, selection_publication, requirements_publication, output_publication), requirements_publication)



def selected_secondary_target(*, selected, writer):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import configured_preparation_types
    values = tuple(record for _, record in getattr(selected, "design_records", ()) if type(record) in configured_preparation_types())
    if not values:
        return None
    if len(values) != 1:
        raise PermissionError("configured secondary read loses its one exact frozen source selection")
    result = authenticate_secondary_target(writer=writer, selection=values[0])
    return None if result is None else (*result, values[0].secondary_readout.lineage_scope)
