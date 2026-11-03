# SPDX-License-Identifier: MPL-2.0
"""Compile actual prospective C from copied current inputs through the public API."""
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_researcher_programme import input_assembly as domain
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.api.matrix_programme_allocations import _require_memory, publish_matrix_programme_allocations
from empirical_lawhood.api.selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer,
        metadata_directory, output_selection_path, execution, read_access=None):
    """Publish metadata only; the ordinary scientific workflows consume C later."""
    loaded = load_experiment_inputs(specification, Path(source_selection_path), artifact_writer=artifact_writer, read_access=read_access)
    inputs = loaded.method_inputs
    if (type(inputs) is not domain.MatrixProgrammeInputAssemblyInputs
            or any(value is None for value in (inputs.request, inputs.design, inputs.census))):
        raise ValueError("programme input derivation requires its complete request, D and exposure census")
    request, design, census = inputs.request, inputs.design, inputs.census
    records = {"request": request, "scientific-design": design, "exposure-census": census}
    domain.bind_inputs(specification, records, files=dict(inputs.files))
    paths = dict(inputs.record_paths)
    if set(paths) != set(records) or set(dict(inputs.files)) != {row.key for row in request.files}:
        raise ValueError("programme input derivation requires the exact original copied record and FILE paths")
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    directory, output = Path(metadata_directory), Path(output_selection_path)
    plane = Path(artifact_writer.root.contract.canonical_path)
    if (not directory.is_absolute() or directory != directory.resolve(strict=False) or directory == plane
            or not directory.is_relative_to(plane) or directory.is_relative_to(root)
            or output != directory / "inputs/sources.json"):
        raise ValueError("programme input derivation requires its guarded <metadata>/inputs/sources.json destination")
    prefix = directory.relative_to(plane).as_posix()
    artifact_writer.root.resolve(prefix + "/inputs/sources.json", for_write=True)
    budget = request.metadata_budget
    originals = {}
    for key, record in records.items():
        raw = record.canonical_bytes()
        path = Path(paths[key])
        if not path.is_absolute() or path != path.resolve(strict=True) or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("programme input records require their exact guarded copied paths")
        originals[path] = raw
    files = dict(inputs.files)
    request_root = Path(paths["request"]).parent
    source_bytes = sum(len(raw) for raw in originals.values()) + sum(row.identity.size_bytes for row in request.files)
    if source_bytes > budget.source_scan_bytes or source_bytes > budget.memory_bytes:
        raise ValueError("programme copied input bodies exceed their selected source or memory budget")
    _require_memory(budget.memory_bytes)
    for binding in request.files:
        prepared = files[binding.key]
        path = request_root / binding.relative_path
        if (path != path.resolve(strict=True) or path != prepared.path
                or any(p.is_symlink() for p in (path, *path.parents))):
            raise ValueError("programme support FILE paths must retain their exact copied request-relative bindings")
        raw = read_bounded_bytes(path, maximum_bytes=binding.identity.size_bytes)
        if (len(raw), sha256(raw).hexdigest()) != (binding.identity.size_bytes, binding.identity.sha256):
            raise ValueError("programme input FILE differs from its declared original bytes")
        originals[path] = raw
    _require_memory(budget.memory_bytes)

    def require_originals():
        for path, raw in originals.items():
            if (path != path.resolve(strict=True) or any(p.is_symlink() for p in (path, *path.parents))
                    or read_bounded_bytes(path, maximum_bytes=len(raw)) != raw):
                raise ValueError("programme copied input changed during dependent publication")

    require_originals()
    provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    if provenance.observed_git_head != admitted.implementation_commit:
        raise ValueError("programme input derivation changes its selected source")
    published = publish_matrix_programme_allocations(design=design, census=census, namespace=request.namespace,
        root_seed_material_sha256=request.root_seed_material_sha256,
        future_seed_material_sha256=request.future_seed_material_sha256, e4_streams=request.e4_streams,
        e5_root_seed_material_sha256=request.e5_root_seed_material_sha256,
        e5_future_seed_material_sha256=request.e5_future_seed_material_sha256,
        provenance=provenance, support_publications=(), file_bindings=request.files,
        request_path=Path(paths["request"]), project_root=root, artifact_writer=artifact_writer,
        metadata_directory=directory / "commitments", execution=execution, metadata_budget=budget,
        validate_copied_inputs=require_originals, _admitted_source=admitted)
    commitment, compiler_output_bytes = published.commitment, published.output_bytes
    # The authenticated reader below owns the one live decoded C closure.
    # Do not retain the compiler's complete resolved phase bodies as well.
    del published
    # The new material has its own bounded custody admission. Keep that actual C
    # closure and the original copied bytes guarded through selector/requirements.
    with authenticated_programme_inputs(writer=artifact_writer, commitment=commitment,
            maximum_source_bytes=budget.source_scan_bytes) as actual:
        _require_memory(budget.memory_bytes)
        if (actual.scientific_design != design or actual.exposure_census != census
                or actual.commitments.namespace != request.namespace):
            raise PermissionError("programme input compiler changes its actual original design or census")
        wrapper_identity = ObjectIdentity.from_record("publication." + commitment.record.object_id,
            commitment)
        binding = ExperimentInputBinding("input-commitments", wrapper_identity,
            "input-commitments.json", len(commitment.canonical_bytes()))
        selector = ExperimentFileInputSelection("sources." + request.namespace + ".programme-inputs",
            domain.PROTOCOL_ID, (binding,), ())
        rebound = domain.bind_inputs(specification, {"input-commitments": commitment})
        preparation = prepare_experiment(specification, scientific_inputs=rebound.scientific_inputs,
            method_inputs=rebound.method_inputs, execution=execution)
        payload = canonical_json_bytes({"schema": "empirical-lawhood/operational/experiment-input-requirements",
            "version": "1.0.0", "value": {"specification": specification.identity.to_document(),
                "request": request.identity.to_document(), "input_commitments": commitment,
                "scientific_design": design.identity.to_document(), "exposure_census": census.identity.to_document(),
                "phase_group_counts": design.phase_group_counts, "native_contact": "NONE",
                "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED",
                "dependencies": tuple({"code": row.code, "kind": row.kind.value, "detail": row.detail,
                    "source_key": row.source_key} for row in preparation.dependencies)}})
        requests = []
        for name, record in (("input-commitments", commitment), ("sources", selector)):
            raw = record.canonical_bytes()
            requests.append(ArtifactWriteRequest("programme-inputs." + name + "." + sha256(raw).hexdigest(),
                prefix + "/inputs/" + name + ".json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                "application/json", request.namespace, prefix, raw,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        requests.append(ArtifactWriteRequest("programme-inputs.requirements." + sha256(payload).hexdigest(),
            prefix + "/requirements." + sha256(payload).hexdigest() + ".json",
            "empirical-lawhood/operational/experiment-input-requirements", ArtifactProfile.CANONICAL_JSON,
            "application/json", request.namespace, prefix, payload,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        extra_size = sum(len(row.payload) for row in requests)
        _require_memory(budget.memory_bytes)
        if source_bytes + extra_size > budget.memory_bytes:
            raise ValueError("programme final metadata exceeds selected materialized memory")
        # The compiler reports its exact canonical/raw payload count. Do not
        # walk a growing directory or give this wrapper a second allowance.
        if compiler_output_bytes + extra_size > budget.output_bytes:
            raise ValueError("programme complete metadata output exceeds its selected byte budget")
        for row in requests:
            _metadata_record_size(artifact_writer, len(row.payload))
        require_originals()
        require_admitted_target_source_current(root, admitted)
        if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
            raise ValueError("programme actual source changed before dependent metadata publication")
        results = artifact_writer.write_batch(tuple(requests))
        publications = tuple(_publication_from_manifest(artifact_writer,
            artifact_writer.read_manifest(row.materialization.relative_path)) for row in results)
        require_originals()
        require_admitted_target_source_current(root, admitted)
        if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
            raise ValueError("programme actual source changed during dependent metadata publication")
        return ExperimentInputDerivationResult(specification.identity, selector, output, preparation,
            (commitment.publication, *publications), publications[-1])
