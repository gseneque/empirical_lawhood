# SPDX-License-Identifier: MPL-2.0
"""Guarded preparation and retained assessment of four Gp heavy scaffolds."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import GpActiveScaffold, prepare_gp_active_scaffolds, scaffold_pdb
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold_assessment import GpScaffoldAssessment, assess_gp_scaffold
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, exact
from empirical_lawhood.domains.rubisco.rubisco_response.gp_refined_geometry import GpRefinedGeometrySupply
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import RuBPTetraanionPreparation
from empirical_lawhood.storage.bounded_io import file_matches_bytes, read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest


MODEL_NAMES = ("m1-wt","m1-i95m","v1-wt","v1-i95m")
MEMBERS = ("case-set.json","original-supply.json","parent-assessment.json","parent-heavy.pdb","parent-origin.json",
           "gp-source.json","methionine-source.json","ligand-preparation.json",
           *(f"{model}/{name}" for model in MODEL_NAMES for name in ("scaffold.json","model.pdb","assessment.json")),
           "report.txt")
MAXIMUM_BYTES = 64 * 2**20


def _parent_join(supply, integrity):
    exact(supply, GpRefinedGeometrySupply)
    supply.__post_init__()
    exact(integrity, PreAmberGeometryIntegrity)
    if integrity.geometry_receipt != supply.geometry_receipt:
        raise ValueError("active scaffold preparation loses its actual original native receipt")
    receipt = supply.geometry_receipt
    identities = (receipt,)
    if supply.independent_integrity != ObjectIdentity.from_record(integrity.product_id, integrity):
        raise ValueError("active scaffold preparation loses its exact independent parent assessment")
    return receipt, tuple(ArtifactLineageParent(i, VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE) for i in identities)


def prepare_active_gp_scaffolds(*, cases, original_supply, parent_assessment, parent_heavy_path, parent_origin_path,
                               gp_source, ligand, methionine, output_relative_path, artifact_writer):
    """Construct new heavy-coordinate hypotheses from authenticated reuse operands.

    The caller must authenticate current access and original native custody.
    This route validates the typed original joins and exact supplied geometry.
    New authoring requires the independently assessed library construction.
    Unrelaxed original/template parents cannot bypass the native repair stage.
    It creates no native task, execution authority or physical admission.
    """
    validate_relative_locator(output_relative_path)
    exact(cases,RubiscoCaseSet)
    if type(original_supply) is not GpRefinedGeometrySupply:
        raise ValueError("new active scaffolds require assessed PDBFixer/Amber/OpenMM construction via refined_geometry")
    original_receipt, parents = _parent_join(original_supply, parent_assessment)
    for name in MEMBERS:
        artifact_writer.root.resolve(output_relative_path+"/"+name,for_write=True)
    original_heavy = read_bounded_bytes(Path(parent_heavy_path),maximum_bytes=MAXIMUM_BYTES)
    heavy = original_heavy
    origin = read_bounded_bytes(Path(parent_origin_path),maximum_bytes=MAXIMUM_BYTES)
    selection = sha256(cases.canonical_bytes()+original_supply.independent_integrity.canonical_bytes()
                       +ligand.identity.canonical_bytes()+gp_source.canonical_bytes()+methionine.canonical_bytes()).hexdigest()
    models = prepare_gp_active_scaffolds(cases=cases,retained_integrity=parent_assessment,heavy_bytes=heavy,origin_bytes=origin,
        gp_source=gp_source,ligand=ligand,methionine=methionine,preparation_id="preparation.gp-active-scaffold."+selection)
    assessments = tuple(assess_gp_scaffold(model,parent_heavy_bytes=heavy,ligand=ligand,gp_source=gp_source,methionine=methionine,
        assessment_id="assessment.gp-active-scaffold."+model.fingerprint()) for model in models)
    records = dict(zip(MEMBERS[:8],(cases,original_supply,parent_assessment,None,None,gp_source,methionine,ligand),strict=True))
    payloads = {name:record.canonical_bytes() for name,record in records.items() if record is not None}
    payloads.update({"parent-heavy.pdb":heavy,"parent-origin.json":origin})
    for name,model,assessment in zip(MODEL_NAMES,models,assessments,strict=True):
        for filename,record in (("scaffold.json",model),("assessment.json",assessment)):
            records[name+"/"+filename] = record
            payloads[name+"/"+filename] = record.canonical_bytes()
        records[name+"/model.pdb"] = None
        payloads[name+"/model.pdb"] = scaffold_pdb(model,ligand).encode("ascii")
    lines = ["Gp WT/I95M active-site starting geometries", "",
             "Scope: full heavy-coordinate hypotheses. Hydrogen completion, topology, parameters and relaxation are not admitted.",
             "All eight CABP molecules are replaced by newly placed keto RuBP heavy graphs.",
             "All sixteen protein chains, the constructed 168 LSU residues, eight Mg ions and 1084 source waters are retained.",
             "Ligand poses use a proper rigid fit of the 18 shared heavy-atom names to the inhibited source.",
             "Side-chain proposals retain inherited anchors; the mandatory native stage discards I95M CG/SD/CE and applies PDBFixer mutations in all eight SSUs.",
             "Fit and short-contact diagnostics are not kinetic evidence. New native calls: 0.", ""]
    for name,assessment in zip(MODEL_NAMES,assessments,strict=True):
        lines += [f"{name}: correspondence {assessment.correspondence_disposition.value}; heavy atoms {assessment.atom_count}; protein residues {assessment.protein_residue_count}.",
                  f"  New atoms {assessment.constructed_atoms}; removed parent atoms {assessment.removed_parent_atoms}; sites {assessment.site_count}.",
                  f"  Minimum ligand/environment heavy distance: {assessment.minimum_ligand_environment_distance_angstrom} angstrom; contacts below 1 angstrom: {len(assessment.short_contacts)}.",
                  "  Findings: "+(", ".join(assessment.findings) or "none within correspondence and rigid-geometry checks")]
    lines += ["", "Next: assess nonstandard parameters, add hydrogens and solvent/ions, assess full topology, then perform bounded native relaxation and coupled-force controls.",
              "The six proton-allocation/Mg-water alternatives, physical rate contrasts and joint forecast remain unprepared or unevaluable."]
    payloads["report.txt"] = ("\n".join(lines)+"\n").encode()
    records["report.txt"] = None
    if any(len(payload)>MAXIMUM_BYTES for payload in payloads.values()):
        raise ValueError("scaffold publication exceeds its explicit member ceiling")
    package_id = "package.gp-active-scaffold."+sha256(b"".join(sha256(payloads[name]).digest() for name in MEMBERS)).hexdigest()
    writes = tuple(ArtifactWriteRequest("gp-scaffold-member."+sha256(payloads[name]).hexdigest()+"."+name.replace("/","-").replace(".","-"),
        output_relative_path+"/"+name,records[name].SCHEMA if records[name] is not None else "empirical-lawhood/rubisco-response/active-scaffold-text",
        ArtifactProfile.CANONICAL_JSON if records[name] is not None else ArtifactProfile.TEXT_PARAMETERS,
        "application/json" if records[name] is not None else "text/plain",package_id,output_relative_path,payloads[name],
        VisibilityCeiling.DEVELOPMENT_ONLY,tuple(VisibilityCeiling.DEVELOPMENT_ONLY for _ in parents),
        OutcomeAccess.DEVELOPMENT_VISIBLE,lineage_parents=parents)
        for name in MEMBERS)
    if (not file_matches_bytes(Path(parent_heavy_path),original_heavy,maximum_bytes=MAXIMUM_BYTES)
            or not file_matches_bytes(Path(parent_origin_path),origin,maximum_bytes=MAXIMUM_BYTES)):
        raise ValueError("retained parent geometry changed before publication")
    publications = artifact_writer.write_batch(writes)
    return {"paths":{name:str(artifact_writer.root.resolve(output_relative_path+"/"+name,for_write=False)) for name in MEMBERS},
            "package_id":package_id,"original_geometry_receipt":original_receipt.to_document(),
            "correspondence_dispositions":{name:a.correspondence_disposition.value for name,a in zip(MODEL_NAMES,assessments,strict=True)},
            "active_ensemble_admission":"UNEVALUABLE","new_native_calls":0,"publications":[p.to_document() for p in publications]}


def read_active_gp_scaffolds(*, directory_relative_path, artifact_writer):
    """Authenticate and reassess all four retained models without construction."""
    validate_relative_locator(directory_relative_path)
    manifest = artifact_writer.read_manifest(directory_relative_path+"/report.txt")

    def exposed_only(member):
        if (member.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or member.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("active scaffold reader cannot open a different evidence lane")

    def consume(members):
        names = {directory_relative_path+"/"+name:name for name in MEMBERS}
        if set(members)!=set(names):
            raise ValueError("active scaffold package loses its complete member census")
        raw = {name:read_bounded_bytes(artifact_writer.root.resolve(path,for_write=False),maximum_bytes=MAXIMUM_BYTES)
               for path,name in names.items()}
        def decode(name,cls):
            return decode_canonical_bytes(raw[name],cls,maximum_bytes=MAXIMUM_BYTES)
        supply_schema = members[directory_relative_path+"/original-supply.json"].logical.payload_schema
        if supply_schema != GpRefinedGeometrySupply.SCHEMA:
            raise ValueError("active scaffold package changes its declared geometry supplier")
        supply = decode("original-supply.json",GpRefinedGeometrySupply)
        integrity = decode("parent-assessment.json",PreAmberGeometryIntegrity)
        cases = decode("case-set.json",RubiscoCaseSet)
        _, parents = _parent_join(supply, integrity)
        for name,evidence in (("parent-heavy.pdb",integrity.heavy_file),("parent-origin.json",integrity.origin_file)):
            if len(raw[name])!=evidence.byte_count or sha256(raw[name]).hexdigest()!=evidence.sha256:
                raise ValueError("active scaffold package changes original parent geometry bytes")
        ligand = decode("ligand-preparation.json",RuBPTetraanionPreparation)
        gp = decode("gp-source.json",StructuralSourceMember)
        met = decode("methionine-source.json",StructuralSourceMember)
        models,assessments = [],[]
        expected_materials = tuple(m for c in cases.cases if c.case_role=="CANDIDATE" for m in (c.parent,c.mutant))
        for name,material in zip(MODEL_NAMES,expected_materials,strict=True):
            model = decode(name+"/scaffold.json",GpActiveScaffold)
            assessment = decode(name+"/assessment.json",GpScaffoldAssessment)
            checked = assess_gp_scaffold(model,parent_heavy_bytes=raw["parent-heavy.pdb"],ligand=ligand,gp_source=gp,methionine=met,
                                          assessment_id=assessment.assessment_id)
            if checked!=assessment or model.material!=material or model.retained_geometry!=supply.independent_integrity:
                raise ValueError("retained scaffold or independent assessment differs from its original inputs")
            # This is a format projection from retained atoms, not coordinate construction.
            if raw[name+"/model.pdb"]!=scaffold_pdb(model,ligand).encode("ascii"):
                raise ValueError("retained PDB projection differs from complete retained coordinates")
            models.append(model)
            assessments.append(assessment)
        if any(m.logical.lineage_parents!=parents for m in members.values()):
            raise ValueError("active scaffold package loses its actual library-construction receipt")
        return {"scaffolds":tuple(models),"assessments":tuple(assessments),
                "parent_geometry_quality":supply.source.geometry_quality,"new_native_calls":0}

    return artifact_writer.verify_manifest_members(manifest,validate_members=consume,before_member=exposed_only)
