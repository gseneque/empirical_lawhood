# SPDX-License-Identifier: MPL-2.0
"""Bind installed construction tools and authenticate the original common parent."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.rubisco.rubisco_response.initial_amber_native import select_gp_amber_parameters as select_gp_amber_parameters
from empirical_lawhood.api.domain_composition.rubisco_response.geometry_repair import prepare_gp_geometry_repair
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import native_result_reader
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.geometry_reuse import GeometryReuseSupply, materialize_geometry_inputs
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity, assess
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation_integrity import source_disulfide_partners
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import ORIGINALS, StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.independent_assessment import original_assembly
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import CONSTRUCTION_PACKAGES, GpRepairNumericEngine
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import LEGACY_REPAIR_PROTOCOL
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberEngine
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import authenticate_engine
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.bounded_io import bounded_file_sha256, file_matches_bytes, read_bounded_bytes


MAXIMUM_PARENT_BYTES = 64 * 2**20


def select_gp_amber_engine(*, directory, files):
    """Bind a verified repository-selected native closure to its new installation."""
    directory = Path(directory)
    digest = sha256((str(directory) + "".join(row.fingerprint() for row in files)).encode()).hexdigest()
    engine = GpAmberEngine("engine.gp-amber." + digest, str(directory), files)
    authenticate_engine(engine)
    return engine


def select_gp_construction_engine(*, site_packages, interpreter):
    """Bind the complete existing environment; do not install or import native tools."""
    root, executable = Path(site_packages), Path(interpreter)
    if (not root.is_absolute() or root.resolve() != root or root.is_symlink()
            or not executable.is_absolute() or executable.resolve() != executable):
        raise ValueError("construction environment requires its selected real paths")
    rows = []
    for package in CONSTRUCTION_PACKAGES:
        directory = root / package
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("construction environment lacks a selected package: " + package)
        for path in sorted(directory.rglob("*")):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError("construction environment contains a link or special member")
            if path.is_file():
                size, digest = bounded_file_sha256(path, maximum_bytes=None)
                rows.append(FileEvidence(path.relative_to(root).as_posix(), size, digest))
    files = tuple(sorted(rows, key=lambda row: row.relative_path))
    interpreter_sha = bounded_file_sha256(executable, maximum_bytes=None)[1]
    digest = sha256((str(root) + str(executable) + interpreter_sha
        + "".join(row.fingerprint() for row in files)).encode()).hexdigest()
    return GpRepairNumericEngine("engine.gp-construction." + digest, str(root), files,
        str(executable), interpreter_sha)


def prepare_gp_repair_from_original(*, parent_file, assessment_file, gp_source,
        original_artifact_writer, destination_relative_path, artifact_writer,
        amber_engine, numeric_engine, maximum_iterations=2000,
        construction_seed=20261114, construction_threads=8,
        parent_repair_protocol=LEGACY_REPAIR_PROTOCOL, maximum_refined_displacement_angstrom=None):
    """Authenticate original native custody and all archive members before preparation.

    The original writer carries its frozen storage identity and selected current
    access. The destination contains new copies of only the two declared operands.
    No original contact is resumed and no molecular calculation occurs here.
    """
    exact(gp_source, StructuralSourceMember)
    if gp_source.sha256 != dict(ORIGINALS)["1bwv.cif"]:
        raise ValueError("common-parent preparation requires the exact original assembly")
    parent_file, assessment_file = Path(parent_file), Path(assessment_file)
    parent_raw = read_bounded_bytes(parent_file, maximum_bytes=MAXIMUM_PARENT_BYTES)
    assessment_raw = read_bounded_bytes(assessment_file, maximum_bytes=MAXIMUM_PARENT_BYTES)
    parent = decode_canonical_bytes(parent_raw, GeometryReuseSupply, maximum_bytes=MAXIMUM_PARENT_BYTES)
    previous = decode_canonical_bytes(assessment_raw, PreAmberGeometryIntegrity, maximum_bytes=MAXIMUM_PARENT_BYTES)
    destination = artifact_writer.root.resolve(destination_relative_path, for_write=True,
        operation_minimum_free_bytes=sum(row.byte_count for row in parent.census.files))
    if destination.exists() or destination.is_symlink():
        raise ValueError("original-parent materialization requires a fresh selected directory")
    with native_result_reader(original_artifact_writer, parent) as native:
        completed = native.recover(parent.definition)
        if completed is None or completed.completion != parent.completion or completed.receipt != parent.receipt:
            raise ValueError("common parent loses its actual original completion and receipt")
        archive = original_artifact_writer.root.resolve(parent.archive_evidence.relative_path, for_write=False)
        destination.mkdir(parents=True, exist_ok=False)
        materialize_geometry_inputs(archive, parent.definition, parent.census, parent.archive_evidence, destination)
        heavy = read_bounded_bytes(destination / "complete-heavy.pdb", maximum_bytes=MAXIMUM_PARENT_BYTES)
        origin = read_bounded_bytes(destination / "atom-origin-provenance.json", maximum_bytes=MAXIMUM_PARENT_BYTES)
        atoms, chains, _, _, _ = original_assembly("1BWV", gp_source.raw_utf8)
        atoms = tuple(decode_canonical_bytes(a.canonical_bytes(), type(a), maximum_bytes=4096) for a in atoms)
        current = assess(product_id=previous.product_id, source=previous.source,
            geometry_definition=previous.geometry_definition, geometry_completion=previous.geometry_completion,
            geometry_receipt=previous.geometry_receipt, construct=previous.construct,
            joint_view_id=previous.joint_view_id, heavy_file=previous.heavy_file, origin_file=previous.origin_file,
            heavy_bytes=heavy, origin_bytes=origin, source_atoms=atoms, source_chains=chains,
            expected_disulfides=source_disulfide_partners("1BWV", gp_source.raw_utf8, atoms, chains))
        if current != previous:
            raise ValueError("common-parent source/origin assessment differs from its original result")
        source = prepare_gp_geometry_repair(parent=parent, parent_assessment=current,
            heavy_pdb=heavy.decode("ascii"), origin_json=origin.decode("utf-8"), amber_engine=amber_engine,
            numeric_engine=numeric_engine, maximum_iterations=maximum_iterations,
            construction_seed=construction_seed, construction_threads=construction_threads,
            parent_repair_protocol=parent_repair_protocol, maximum_refined_displacement_angstrom=maximum_refined_displacement_angstrom)
        if (not file_matches_bytes(parent_file, parent_raw, maximum_bytes=MAXIMUM_PARENT_BYTES)
                or not file_matches_bytes(assessment_file, assessment_raw, maximum_bytes=MAXIMUM_PARENT_BYTES)):
            raise ValueError("original-parent selection changed during preparation")
        artifact_writer.root.resolve(destination_relative_path, for_write=False)
    return source
