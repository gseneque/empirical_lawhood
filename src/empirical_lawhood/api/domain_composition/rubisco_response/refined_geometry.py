# SPDX-License-Identifier: MPL-2.0
"""Publish and independently read a genuinely repaired common Gp parent."""

from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity, assess
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation_integrity import source_disulfide_partners
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import ORIGINALS, StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.independent_assessment import original_assembly
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import GEOMETRY_ID
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import read_repair_files
from empirical_lawhood.domains.rubisco.rubisco_response.gp_refined_geometry import GpRefinedGeometrySupply, require_repaired_endpoint
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.api.domain_composition.rubisco_response.geometry_repair import read_gp_geometry_repair


MAXIMUM_BYTES=64*2**20
MEMBERS=("supply.json","parent-assessment.json","gp-source.json","complete-heavy.pdb",
         "atom-origin-provenance.json","report.txt")


def _checked_parent(*,source,original_result,native_subwork,gp_source):
    exact(gp_source,StructuralSourceMember)
    if gp_source.sha256!=dict(ORIGINALS)["1bwv.cif"]:
        raise ValueError("refined Gp parent requires its exact original deposited full assembly")
    key=original_result.definition.identity.object_fingerprint
    result=read_gp_geometry_repair(source=source,original_result=original_result,native_subwork=native_subwork,
        result_id="read.refined-gp-parent."+key)
    require_repaired_endpoint(source,result)
    files=read_repair_files(native_subwork,result.definition,result.returned)
    atoms,chains,_,_,_=original_assembly("1BWV",gp_source.raw_utf8)
    # The retained origin producer emitted decoded canonical source tokens.
    atoms=tuple(decode_canonical_bytes(a.canonical_bytes(),type(a),maximum_bytes=4096) for a in atoms)
    census={row.relative_path:row for row in result.returned.files.files}
    old=source.parent_assessment
    integrity=assess(product_id="assessment.refined-gp-parent."+key,source=old.source,
        geometry_definition=result.definition.identity,
        geometry_completion=ObjectIdentity.from_record(result.receipt.task_id+".completion",result.completion),
        geometry_receipt=ObjectIdentity.from_record(result.receipt.receipt_id,result.receipt),
        construct=old.construct,joint_view_id=old.joint_view_id,
        heavy_file=census[GEOMETRY_ID+"/complete-heavy.pdb"],origin_file=census[GEOMETRY_ID+"/atom-origin-provenance.json"],
        heavy_bytes=files["complete-heavy.pdb"],origin_bytes=files["atom-origin-provenance.json"],
        source_atoms=atoms,source_chains=chains,
        expected_disulfides=source_disulfide_partners("1BWV",gp_source.raw_utf8,atoms,chains))
    supply=GpRefinedGeometrySupply("supply.refined-gp-parent."+key,source,result,integrity)
    return supply,files["complete-heavy.pdb"],files["atom-origin-provenance.json"]


def prepare_refined_gp_parent(*,source,original_result,native_subwork,gp_source,output_relative_path,artifact_writer,
        include_records=False):
    """Authenticate actual repair custody and original source/origins before publication."""
    validate_relative_locator(output_relative_path)
    for name in MEMBERS:
        artifact_writer.root.resolve(output_relative_path+"/"+name,for_write=True)
    supply,heavy,origin=_checked_parent(source=source,original_result=original_result,native_subwork=native_subwork,gp_source=gp_source)
    a=supply.result.assessment
    scope = "Constructed-only geometry repair: SATISFIED."
    if a.refined_heavy_count:
        scope = (f"Construction and bounded Glu213 refinement passed. "
                 f"Refined inherited carboxylate atoms {a.refined_heavy_count}. "
                 f"Largest source displacement {a.largest_refined_displacement_angstrom} angstrom. "
                 f"Selected limit {supply.source.maximum_refined_displacement_angstrom} angstrom.")
    report=("Refined common Gp M1-WT parent\n\n"
        f"{scope} Original source/origin correspondence: SATISFIED.\n"
        f"Heavy atoms: {a.heavy_atoms}; observed and fixed: {a.fixed_heavy_atoms}; constructed: {a.constructed_heavy_atoms}.\n"
        f"Maximum movable-coordinate gradient: {a.maximum_mobile_gradient_kj_mol_nm} kJ/mol/nm.\n"
        f"Maximum movable-bond error: {a.maximum_mobile_bond_error_angstrom} angstrom.\n"
        f"Minimum nonbonded mobile-heavy distance: {a.minimum_mobile_nonbonded_heavy_distance_angstrom} angstrom.\n"
        "All original identities and atom origins are retained. No new molecular call occurred in this publication.\n"
        "This remains a CABP-bound common starting parent. Active chemistry, ensembles and rates are UNEVALUABLE.\n")
    records={"supply.json":supply,"parent-assessment.json":supply.integrity,"gp-source.json":gp_source}
    payloads={name:record.canonical_bytes() for name,record in records.items()}
    payloads.update({"complete-heavy.pdb":heavy,"atom-origin-provenance.json":origin,"report.txt":report.encode()})
    if any(len(raw)>MAXIMUM_BYTES for raw in payloads.values()):
        raise ValueError("refined-parent publication exceeds its declared member ceiling")
    package_id="package.refined-gp-parent."+sha256(b"".join(sha256(payloads[n]).digest() for n in MEMBERS)).hexdigest()
    parent=ArtifactLineageParent(supply.geometry_receipt,VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE)
    writes=tuple(ArtifactWriteRequest("refined-gp-parent-member."+sha256(payloads[n]).hexdigest()+"."+n.replace(".","-"),
        output_relative_path+"/"+n,records[n].SCHEMA if n in records else "empirical-lawhood/rubisco-response/refined-parent-text",
        ArtifactProfile.CANONICAL_JSON if n in records else ArtifactProfile.TEXT_PARAMETERS,
        "application/json" if n in records else "text/plain",package_id,output_relative_path,payloads[n],
        VisibilityCeiling.DEVELOPMENT_ONLY,(VisibilityCeiling.DEVELOPMENT_ONLY,),OutcomeAccess.DEVELOPMENT_VISIBLE,
        lineage_parents=(parent,)) for n in MEMBERS)
    published=artifact_writer.write_batch(writes)
    result = dict(paths={n:str(artifact_writer.root.resolve(output_relative_path+"/"+n,for_write=False)) for n in MEMBERS},
        package_id=package_id,geometry_receipt=supply.geometry_receipt.to_document(),new_native_calls=0,
        repair_disposition="SATISFIED",ensemble_admission="UNEVALUABLE",rate_admission="UNEVALUABLE",
        publications=[p.to_document() for p in published])
    if include_records:
        result.update(supply=supply, assessment=supply.integrity)
    return result


def read_refined_gp_parent(*,directory_relative_path,native_subwork,artifact_writer):
    """Authenticate the package and original archive; repeat no molecular construction."""
    validate_relative_locator(directory_relative_path)
    manifest=artifact_writer.read_manifest(directory_relative_path+"/report.txt")
    def exposed_only(member):
        if (member.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or member.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError("refined-parent read changes its original evidence lane")
    def consume(members):
        names={directory_relative_path+"/"+n:n for n in MEMBERS}
        if set(members)!=set(names):
            raise ValueError("refined-parent package loses its complete member census")
        raw={n:read_bounded_bytes(artifact_writer.root.resolve(path,for_write=False),maximum_bytes=MAXIMUM_BYTES) for path,n in names.items()}
        supply=decode_canonical_bytes(raw["supply.json"],GpRefinedGeometrySupply,maximum_bytes=MAXIMUM_BYTES)
        integrity=decode_canonical_bytes(raw["parent-assessment.json"],PreAmberGeometryIntegrity,maximum_bytes=MAXIMUM_BYTES)
        gp=decode_canonical_bytes(raw["gp-source.json"],StructuralSourceMember,maximum_bytes=MAXIMUM_BYTES)
        current,heavy,origin=_checked_parent(source=supply.source,original_result=supply.result,native_subwork=native_subwork,gp_source=gp)
        if current!=supply or integrity!=supply.integrity or heavy!=raw["complete-heavy.pdb"] or origin!=raw["atom-origin-provenance.json"]:
            raise ValueError("refined-parent package differs from its independently reread original custody")
        parent=ArtifactLineageParent(supply.geometry_receipt,VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE)
        if any(m.logical.lineage_parents!=(parent,) for m in members.values()):
            raise ValueError("refined-parent package changes its actual native receipt ancestry")
        return dict(supply=supply,assessment=integrity,new_native_calls=0,repair_disposition="SATISFIED")
    return artifact_writer.verify_manifest_members(manifest,validate_members=consume,before_member=exposed_only)
