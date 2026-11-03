# SPDX-License-Identifier: MPL-2.0
"""Publish prospective E1 membership and its actual criterion before D."""
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1HistoryRoot
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e1_allocation as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.matrix_programme_allocations import _body_size, _process_rss_bytes, _require_memory
from empirical_lawhood.api.selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def _admit_allocation(request, census, source_bytes):
    """Admit actual declared cardinality before proportional construction."""
    budget = request.metadata_budget
    count = sum(requirement.requested_roots for requirement in request.criterion_choices.family_requirements)
    coordinate = max(request.coordinates, key=_body_size)
    width = max(3, len(str(count - 1)))
    group = "group." + request.namespace + ".e1.3." + "9" * width
    root = MatrixProgrammeRoot("root." + group, group, "regime." + coordinate.coordinate_id,
        coordinate.coordinate_id, MatrixProgrammeRole.CONFIRMATION, coordinate.clock_id)
    sample = E1HistoryRoot(root, coordinate_identity(coordinate),
        domain.ordinary_streams(request.root_seed_material_sha256, group))
    # Count both the immutable root records and the maps used by their complete
    # validators; repeated coordinate/census charges are conservative.
    estimate = source_bytes + _body_size(request) + _body_size(census) + count * (
        4 * _body_size(sample) + _body_size(coordinate))
    if _process_rss_bytes() + estimate > budget.memory_bytes:
        raise ValueError("prospective E1 cardinality exceeds selected metadata memory")
    if count * len(sample.canonical_bytes()) > budget.output_bytes:
        raise ValueError("prospective E1 cardinality exceeds selected metadata output-byte lower bound")


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    source = Path(source_selection_path)
    if (not source.is_absolute() or source != source.resolve(strict=True)
            or any(path.is_symlink() for path in (source, *source.parents))):
        raise ValueError('prospective E1 requires its original guarded source selector')
    selector_raw = read_bounded_bytes(source, maximum_bytes=16 * 1024**2)
    loaded = load_experiment_inputs(specification, source, artifact_writer=artifact_writer, read_access=read_access)
    if read_bounded_bytes(source, maximum_bytes=len(selector_raw)) != selector_raw:
        raise ValueError('prospective E1 copied source selector changed while loading its operands')
    inputs = loaded.method_inputs
    if (type(inputs) is not domain.MatrixProgrammeE1AllocationInputs
            or inputs.request is None or inputs.census is None or inputs.allocation is not None):
        raise ValueError("prospective E1 derivation requires the original copied request and exposure census")
    request, census = inputs.request, inputs.census
    records = {"request": request, "exposure-census": census}
    domain.bind_inputs(specification, records)
    paths = dict(inputs.record_paths)
    if set(paths) != set(records):
        raise ValueError("prospective E1 derivation requires both original copied record paths")
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    directory, output = Path(metadata_directory), Path(output_selection_path)
    plane = Path(artifact_writer.root.contract.canonical_path)
    if (not directory.is_absolute() or directory != directory.resolve(strict=False)
            or directory == plane or not directory.is_relative_to(plane) or directory.is_relative_to(root)
            or output != directory / "inputs/sources.json"):
        raise ValueError("prospective E1 requires its guarded <metadata>/inputs/sources.json destination")
    prefix = directory.relative_to(plane).as_posix()
    artifact_writer.root.resolve(prefix + "/inputs/sources.json", for_write=True)
    originals = {source: selector_raw}
    for key, record in records.items():
        path = Path(paths[key])
        if (not path.is_absolute() or path != path.resolve(strict=True)
                or any(parent.is_symlink() for parent in (path, *path.parents))):
            raise ValueError("prospective E1 inputs require their exact original guarded paths")
        originals[path] = record.canonical_bytes()
    source_bytes = sum(len(raw) for raw in originals.values())
    budget = request.metadata_budget
    if source_bytes > budget.source_scan_bytes or source_bytes > budget.memory_bytes:
        raise ValueError("prospective E1 copied inputs exceed selected source or memory bytes")
    _require_memory(budget.memory_bytes)
    _admit_allocation(request, census, source_bytes)

    def require_originals():
        for path, raw in originals.items():
            if (path != path.resolve(strict=True) or any(parent.is_symlink() for parent in (path, *path.parents))
                    or read_bounded_bytes(path, maximum_bytes=len(raw)) != raw):
                raise ValueError("prospective E1 copied input changed during dependent publication")

    def require_source():
        require_admitted_target_source_current(root, admitted)

    require_originals()
    allocation = domain.e1_allocation(namespace=request.namespace, coordinates=request.coordinates,
        family_requirements=request.criterion_choices.family_requirements, census=census,
        root_material=request.root_seed_material_sha256)
    criterion = request.criterion_choices.bind_allocation(allocation, request.factor_rule)
    produced = dict(records, allocation=allocation, criterion=criterion)
    rebound = domain.bind_inputs(specification, produced)
    preparation = prepare_experiment(specification, scientific_inputs=rebound.scientific_inputs,
        method_inputs=rebound.method_inputs, execution=execution)
    pins = {"request": request.identity, "exposure-census": census.identity,
        "allocation": criterion.allocation, "criterion": criterion.identity}
    selector = ExperimentFileInputSelection("sources." + request.namespace + ".e1-allocation", domain.PROTOCOL_ID,
        tuple(ExperimentInputBinding(key, pins[key], key + ".json", len(record.canonical_bytes()))
            for key, record in sorted(produced.items())), ())
    # E1HistoryAllocation uses its domain identity owner, rather than defining
    # another mutable or caller-supplied allocation fingerprint.
    requirements = canonical_json_bytes({"schema": "empirical-lawhood/operational/experiment-input-requirements",
        "version": "1.0.0", "value": {"specification": specification.identity.to_document(),
            "request": request.identity.to_document(), "allocation": criterion.allocation.to_document(),
            "criterion": criterion.identity.to_document(), "exposure_census": census.identity.to_document(),
            "family_counts": tuple((value.family_id, value.requested_roots)
                for value in request.criterion_choices.family_requirements),
            "source_snapshot": execution.source_snapshot.to_document(), "environment_id": execution.environment_id,
            "native_contact": "NONE", "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED",
            "next_action": "Use the actual bound criterion in D, retaining this request's E1 mathematics, census, namespace and root material.",
            "dependencies": tuple({"code": value.code, "kind": value.kind.value, "detail": value.detail,
                "source_key": value.source_key} for value in preparation.dependencies)}})
    payloads = tuple((prefix + "/inputs/" + key + ".json", record.SCHEMA, record.canonical_bytes())
        for key, record in sorted(produced.items()))
    payloads += ((prefix + "/inputs/sources.json", selector.SCHEMA, selector.canonical_bytes()),
        (prefix + "/requirements." + sha256(requirements).hexdigest() + ".json",
            "empirical-lawhood/operational/experiment-input-requirements", requirements))
    output_bytes = sum(len(raw) for _, _, raw in payloads)
    if output_bytes > budget.output_bytes or source_bytes + output_bytes > budget.memory_bytes:
        raise ValueError("prospective E1 complete outputs exceed selected metadata byte or memory limits")
    _require_memory(budget.memory_bytes)
    requests = tuple(ArtifactWriteRequest("programme-e1-allocation." + sha256(raw).hexdigest(), relative, schema,
        ArtifactProfile.CANONICAL_JSON, "application/json", request.namespace, prefix, raw,
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND) for relative, schema, raw in payloads)
    for row in requests:
        _metadata_record_size(artifact_writer, len(row.payload))
    require_originals()
    require_source()
    results = artifact_writer.write_batch(requests)
    publications = tuple(_publication_from_manifest(artifact_writer,
        artifact_writer.read_manifest(result.materialization.relative_path)) for result in results)
    require_originals()
    require_source()
    return ExperimentInputDerivationResult(specification.identity, selector, output, preparation,
        publications, publications[-1])
