# SPDX-License-Identifier: MPL-2.0
"""Public authoring and authenticated retained reading of common Gp parent repair."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import GpGeometryRepairConfig, native_input_records
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_translation import gp_geometry_repair_draft
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import LEGACY_REPAIR_PROTOCOL, prepare_geometry_repair_input


def prepare_gp_geometry_repair(*,parent,parent_assessment,heavy_pdb,origin_json,amber_engine,numeric_engine,
                              geometry_quality=None,maximum_iterations=2000,construction_seed=20261114,
                              construction_platform="CPU",construction_threads=8,
                              parent_repair_protocol=LEGACY_REPAIR_PROTOCOL,maximum_refined_displacement_angstrom=None):
    """Use authenticated original supply bytes and derive one complete repair."""
    return prepare_geometry_repair_input(parent=parent,parent_assessment=parent_assessment,heavy_pdb=heavy_pdb,
        origin_json=origin_json,amber_engine=amber_engine,numeric_engine=numeric_engine,
        geometry_quality=geometry_quality,maximum_iterations=maximum_iterations,construction_seed=construction_seed,
        construction_platform=construction_platform,construction_threads=construction_threads,
        parent_repair_protocol=parent_repair_protocol,maximum_refined_displacement_angstrom=maximum_refined_displacement_angstrom)


def author_gp_geometry_repair(*, source, project_root, work_directory, artifact_writer, output_dir):
    """Freeze the installed single-attempt wave; execute no molecular code."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
    source.__post_init__()
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root),artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name + "-native-inputs")
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError("constructed geometry repair authoring requires fresh direct-input custody")
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,expected_lock_sha256=implementation.dependency_lock_sha256)
    config = GpGeometryRepairConfig("config.constructed-gp-repair."+source.fingerprint(),source,
        implementation,str(work_directory),provenance)
    draft = gp_geometry_repair_draft(config)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    scope = "constructed-gp-repair.native-inputs." + config.fingerprint()
    bindings = []
    for name, pin, record in native_input_records(config):
        path = relative + "/" + name + ".json"
        artifact_writer.write(ArtifactWriteRequest(pin.object_id,path,record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,"application/json",scope,relative,record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append(("external.constructed-gp-repair." + name,artifact_writer.root.resolve(path,for_write=False)))
    result = author_recursive_wave(draft=draft,project_root=project_root,artifact_writer=artifact_writer,
        output_dir=output_dir,input_bindings=tuple(bindings))
    return {**result,"native_input_paths":{key:str(path) for key,path in bindings}}


def read_gp_geometry_repair(*,source,original_result,native_subwork,result_id):
    """Read exact native custody and reassess without construction or replay."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import GpGeometryRepairResult, GpGeometryRepairReturn, MAX_INPUT, assess_return
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    exact(original_result,GpGeometryRepairResult)
    definition=original_result.definition
    if original_result.returned.source!=source.identity or definition.configuration!=source.identity:
        raise ValueError("repair retained read substitutes its selected original source")
    completed=native_subwork.recover(definition)
    if completed is None or completed.completion!=original_result.completion or completed.receipt!=original_result.receipt:
        raise ValueError("repair retained read loses its actual original completion/receipt")
    returned=decode_canonical_bytes(b"".join(native_subwork.iter_completed_output(definition,"repair.return")),
        GpGeometryRepairReturn,maximum_bytes=MAX_INPUT)
    if returned!=original_result.returned:raise ValueError("repair retained read substitutes its original native return")
    return assess_return(source,definition,returned,completed,native_subwork,result_id=result_id)
