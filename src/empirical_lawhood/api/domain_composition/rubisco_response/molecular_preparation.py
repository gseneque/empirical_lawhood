# SPDX-License-Identifier: MPL-2.0
"""Bounded public-component preparation through the guarded artifact owner."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation, component_source_identity, prepare_rubp_tetraanion
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation_assessment import RuBPTetraanionAssessment, assess_rubp_tetraanion
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import LigandChemicalGraph
from empirical_lawhood.storage.bounded_io import file_matches_bytes, read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_sha256
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest


COMPONENT_MAXIMUM_BYTES = 64 * 1024
COMPONENT_URL = "https://files.rcsb.org/ligands/download/RUB.cif"
PREPARATION_MEMBERS = ("source.cif", "preparation.json", "chemical-graph.json", "assessment.json", "report.txt")


def prepare_rubp_template(*, component_path, component_sha256, output_relative_path, artifact_writer):
    """Prepare an explicitly selected public RUB dictionary, with no native entry.

    The supplied digest pins the caller's retained public component. This route
    supplies no source qualification or access to protected molecular results.
    """
    validate_relative_locator(output_relative_path)
    validate_sha256(component_sha256)
    for name in PREPARATION_MEMBERS:
        artifact_writer.root.resolve(output_relative_path + "/" + name, for_write=True)
    path = Path(component_path)
    raw = read_bounded_bytes(path, maximum_bytes=COMPONENT_MAXIMUM_BYTES)
    if sha256(raw).hexdigest() != component_sha256:
        raise ValueError("selected public RUB component differs from its retained digest")
    source = StructuralSourceMember("RUB.cif", COMPONENT_URL, component_sha256, raw.decode("utf-8"))
    prepared = prepare_rubp_tetraanion(source, preparation_id="preparation.rubp-tetraanion." + source.sha256)
    assessment = assess_rubp_tetraanion(prepared, assessment_id="assessment.rubp-tetraanion." + prepared.fingerprint())
    text = ("Selected keto RuBP(4-) ligand template\n"
            f"Graph assessment: {assessment.graph_disposition.value}\n"
            f"Atoms: {assessment.atom_count}; bonds: {assessment.bond_count}; "
            f"formal charge: {assessment.graph_formal_charge}; electrons: {assessment.electron_count}\n"
            "Selected spin multiplicity: 1. D-ribulose stereocentres: C3 R, C4 R.\n"
            "Four phosphate protons are removed; all other source atoms and bond orders are retained.\n"
            "Coordinates are the unrelaxed CCD ideal template. They are not Gp/Mg site coordinates.\n"
            "Enzyme preparation and parameter admission: UNEVALUABLE. New native calls: 0.\n"
            "Findings: " + (", ".join(assessment.findings) or "none within the selected graph checks") + "\n"
            "Remaining requirements:\n" + "".join("  " + name + "\n" for name in prepared.unresolved_requirement_ids))
    records = (None, prepared, prepared.chemical_graph, assessment, None)
    payloads = (raw, prepared.canonical_bytes(), prepared.chemical_graph.canonical_bytes(),
                assessment.canonical_bytes(), text.encode("utf-8"))
    package_id = "preparation-package.rubp-tetraanion." + sha256(
        b"".join(sha256(payload).digest() for payload in payloads)).hexdigest()
    parent = ArtifactLineageParent(component_source_identity(source), VisibilityCeiling.DEVELOPMENT_ONLY,
                                   OutcomeAccess.DEVELOPMENT_VISIBLE)
    writes = tuple(ArtifactWriteRequest(
        "rubp-template-member." + sha256(payload).hexdigest() + "." + name.replace(".", "-"),
        output_relative_path + "/" + name,
        record.SCHEMA if record is not None else "empirical-lawhood/rubisco-response/rubp-template-" + name.replace(".", "-"),
        ArtifactProfile.CANONICAL_JSON if record is not None else ArtifactProfile.TEXT_PARAMETERS,
        "application/json" if record is not None else "text/plain", package_id, output_relative_path, payload,
        VisibilityCeiling.DEVELOPMENT_ONLY, (parent.visibility_ceiling,), OutcomeAccess.DEVELOPMENT_VISIBLE,
        lineage_parents=(parent,)) for name, record, payload in zip(PREPARATION_MEMBERS, records, payloads, strict=True))
    if not file_matches_bytes(path, raw, maximum_bytes=COMPONENT_MAXIMUM_BYTES):
        raise ValueError("original public component changed before preparation publication")
    publications = artifact_writer.write_batch(writes)
    return {"preparation": prepared.identity.to_document(), "assessment": assessment.identity.to_document(),
        "graph_disposition": assessment.graph_disposition.value, "enzyme_preparation_admission": "UNEVALUABLE",
        "parameter_admission": "UNEVALUABLE", "new_native_calls": 0, "package_id": package_id,
        "paths": {name: str(artifact_writer.root.resolve(output_relative_path + "/" + name, for_write=False))
                  for name in PREPARATION_MEMBERS}, "publications": [row.to_document() for row in publications]}


def read_rubp_template(*, directory_relative_path, component_sha256, artifact_writer):
    """Authenticate every original member, then reassess without construction.

    The shared owner verifies complete publication bytes before and after the
    consumer. A later call repeats current custody checks, never preparation.
    """
    validate_relative_locator(directory_relative_path)
    validate_sha256(component_sha256)
    relative = {name: directory_relative_path + "/" + name for name in PREPARATION_MEMBERS}
    manifest = artifact_writer.read_manifest(relative["preparation.json"])

    def exposed_only(member):
        if (member.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or member.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("public ligand preparation reader cannot open a different evidence lane")

    def consume(members):
        if set(members) != set(relative.values()):
            raise ValueError("ligand preparation publication changes its complete member census")
        raw = {name: read_bounded_bytes(artifact_writer.root.resolve(path, for_write=False),
                                       maximum_bytes=4 * COMPONENT_MAXIMUM_BYTES)
               for name, path in relative.items()}
        prepared = decode_canonical_bytes(raw["preparation.json"], RuBPTetraanionPreparation,
                                          maximum_bytes=4 * COMPONENT_MAXIMUM_BYTES)
        graph = decode_canonical_bytes(raw["chemical-graph.json"], LigandChemicalGraph,
                                       maximum_bytes=4 * COMPONENT_MAXIMUM_BYTES)
        checked = decode_canonical_bytes(raw["assessment.json"], RuBPTetraanionAssessment,
                                         maximum_bytes=4 * COMPONENT_MAXIMUM_BYTES)
        if (sha256(raw["source.cif"]).hexdigest() != component_sha256
                or raw["source.cif"] != prepared.original_component.raw_utf8.encode("utf-8")
                or prepared.original_component.original_url != COMPONENT_URL or graph != prepared.chemical_graph
                or checked != assess_rubp_tetraanion(prepared, assessment_id=checked.assessment_id)):
            raise ValueError("ligand preparation changes its original source, graph or independent assessment")
        parent = ArtifactLineageParent(component_source_identity(prepared.original_component),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
        if any(member.logical.lineage_parents != (parent,) for member in members.values()):
            raise ValueError("ligand preparation loses its exact public-source lineage")
        return {"preparation": prepared, "assessment": checked,
                "publications": tuple(members[path] for path in relative.values()), "new_native_calls": 0}

    return artifact_writer.verify_manifest_members(manifest, validate_members=consume, before_member=exposed_only)
