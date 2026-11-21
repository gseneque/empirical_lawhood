# SPDX-License-Identifier: MPL-2.0
"""Authenticate original scaffolds before preparing the initial Amber wave."""

from pathlib import Path
from decimal import Decimal

from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import MODEL_NAMES, prepare_initial_amber_input
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import GpAmberOperationConfig, authenticate_engine, native_input_records
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import AMBER_PLANARITY_BASIS
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_translation import initial_gp_amber_draft
from empirical_lawhood.api.domain_composition.rubisco_response.active_scaffolds import read_active_gp_scaffolds
from empirical_lawhood.api.domain_composition.rubisco_response.molecular_preparation import read_rubp_template


def prepare_initial_gp_amber(*, scaffold_relative_path, ligand_relative_path, component_sha256,
                             parameter_sources, engine, numeric_engine, artifact_writer, ligand_artifact_writer,
                             geometry_quality=None, maximum_minimization_iterations=2000,
                             maximum_minimization_gradient_kj_mol_nm=Decimal("1"),
                             minimization_nonbonded_cutoff_angstrom=Decimal("10"),
                             minimization_ewald_tolerance=Decimal("0.000001"), construction_seed=20261114,
                             minimum_stereocentre_volume_angstrom3=Decimal("0.01"),
                             construction_platform="CPU", construction_threads=8):
    """Pure complete original-custody read, returning the strict native operand."""
    retained = read_active_gp_scaffolds(directory_relative_path=scaffold_relative_path,artifact_writer=artifact_writer)
    parent_policy = retained["parent_geometry_quality"]
    if parent_policy.basis == AMBER_PLANARITY_BASIS:
        if geometry_quality is not None and geometry_quality != parent_policy:
            raise ValueError("the four Amber children must carry the selected fresh parent geometry policy")
        geometry_quality = parent_policy
    ligand = read_rubp_template(directory_relative_path=ligand_relative_path,component_sha256=component_sha256,
        artifact_writer=ligand_artifact_writer)["preparation"]
    manifests = tuple(artifact_writer.read_manifest(scaffold_relative_path+"/"+name+"/model.pdb") for name in MODEL_NAMES)
    authenticate_engine(engine)
    return prepare_initial_amber_input(scaffolds=retained["scaffolds"],assessments=retained["assessments"],
        manifests=manifests,ligand=ligand,parameter_sources=parameter_sources,engine=engine,
        numeric_engine=numeric_engine,geometry_quality=geometry_quality,
        maximum_minimization_iterations=maximum_minimization_iterations,
        maximum_minimization_gradient_kj_mol_nm=maximum_minimization_gradient_kj_mol_nm,
        minimization_nonbonded_cutoff_angstrom=minimization_nonbonded_cutoff_angstrom,
        minimization_ewald_tolerance=minimization_ewald_tolerance,construction_seed=construction_seed,
        minimum_stereocentre_volume_angstrom3=minimum_stereocentre_volume_angstrom3,
        construction_platform=construction_platform,construction_threads=construction_threads)


def author_initial_gp_amber(*, source, project_root, work_directory, artifact_writer, output_dir):
    """Freeze the installed single-attempt wave; execute no molecular code."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import require_initial_heavy_geometry
    require_initial_heavy_geometry(source)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),
        repo_root=Path(project_root),artifact_writer=artifact_writer)
    input_directory = destination.with_name(destination.name + "-native-inputs")
    if input_directory.exists() or input_directory.is_symlink():
        raise ValueError("initial Amber authoring requires fresh direct-input custody")
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256,expected_lock_sha256=implementation.dependency_lock_sha256)
    config = GpAmberOperationConfig("config.initial-gp-amber."+source.fingerprint(),source,
        implementation,str(work_directory),provenance)
    draft = initial_gp_amber_draft(config)
    relative = input_directory.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    scope = "initial-gp.native-inputs." + config.fingerprint()
    bindings = []
    for name, pin, record in native_input_records(config):
        path = relative + "/" + name + ".json"
        artifact_writer.write(ArtifactWriteRequest(pin.object_id,path,record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,"application/json",scope,relative,record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append(("external.initial-gp." + name,artifact_writer.root.resolve(path,for_write=False)))
    result = author_recursive_wave(draft=draft,project_root=project_root,artifact_writer=artifact_writer,
        output_dir=output_dir,input_bindings=tuple(bindings))
    return {**result,"native_input_paths":{key:str(path) for key,path in bindings}}


def read_initial_gp_amber(*, source, original_result, native_subwork, result_id):
    """Read exact native receipts and reassess raw bytes, with no construction."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import reassess_initial_amber_result
    return reassess_initial_amber_result(source,original_result,native_subwork,result_id=result_id)
