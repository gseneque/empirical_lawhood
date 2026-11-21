# SPDX-License-Identifier: MPL-2.0
"""Independent validator export of the original nonperiodic, CAP-liganded Gp parent."""

from collections import Counter
from hashlib import sha256
import json
import math

from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import COMPONENTS, ELEMENTS, protected, report_atom_name, write_projection
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import _array, assess_geometry_repair
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import read_repair_files
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import _residues, solvent_last_residues
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition


PARENT = "gp-common-parent"


def parent_sites(groups):
    """Join protected components by source-parent placement; never infer a metal bond."""
    kcxs, ligands, metals = ([key for key in groups if key[2] == comp] for comp in ("KCX", "CAP", "MG"))
    if any(len(keys) != 8 for keys in (kcxs, ligands, metals)):
        raise ValueError("Parent must retain all eight original KCX/CAP/Mg copies")
    def distance(left, right):
        return min(math.dist(a, b) for a in groups[left] for b in groups[right])
    def closest(key, candidates):
        distances = sorted((distance(key, candidate), candidate) for candidate in candidates)
        if distances[0][0] == distances[1][0]:
            raise ValueError("Ambiguous original parent site placement")
        return distances[0][1]
    assigned = {}
    for ligand in ligands:
        magnesium = closest(ligand, metals)
        kcx = closest(magnesium, kcxs)
        if magnesium in assigned or kcx in assigned:
            raise ValueError("Parent site assignment does not cover eight distinct original triples")
        for key in (kcx, ligand, magnesium):
            assigned[key] = f"parent.site.{kcx[0]}"
    return assigned


def project_parent(source, files, directory):
    census = assigned_census_supported_inactive14(read_prmtop(files["dry.prmtop"].decode("ascii")))
    count = census["term_census"]["atoms"]
    final = _array(files["final-coordinates-nm.npy"], count)
    coordinates = (final * 10.0).astype("<f8").tobytes(order="C")
    origin = json.loads(source.origin_json)
    chains = {c["chain"]: c for c in origin["complete_chains"]}
    if Counter(v["subunit"] for v in chains.values()) != {"lsu": 8, "ssu": 8}:
        raise ValueError("Retained parent is missing original L8S8 chains")
    original = {}
    for chain, pos, comp, name, _, xyz in heavy_pdb_rows(source.heavy_pdb):
        original.setdefault((chain, pos, comp), []).append(tuple(map(float, xyz)))
    sites = parent_sites(original)
    rows = solvent_last_residues(original)
    residues, atoms = [], [None] * count
    heavy_join = {tuple(k): i for k, i in json.loads(files["atom-selection.json"])["heavy_join"]}
    for key, (comp, named) in zip(rows, _residues(census), strict=True):
        chain, seq, initial_comp = key
        if comp.upper() != {"HIS": "HIE", "HID": "HIE", "HOH": "WAT"}.get(initial_comp, initial_comp).upper():
            raise ValueError("Parent raw topology changes an original component")
        source_chain = chains.get(chain)
        if source_chain:
            role, subunit, position = "PROTEIN", source_chain["subunit"].upper(), seq
        else:
            role, subunit, position = {"CAP": "LIGAND", "MG": "MAGNESIUM", "WAT": "WATER"}[comp.upper()], None, None
        site = sites.get(key)
        ri = len(residues)
        residues.append(dict(id=f"parent.{chain}.{seq}", chain=chain, seq=seq, component=COMPONENTS.get(comp, comp),
                             original_component=comp, original_chain=chain, original_number=seq,
                             role=role, chain_id=chain if source_chain else None, site=site,
                             critical=protected(chain, subunit, position, site), position=position,
                             chain_length=len(source_chain["sequence"]) if source_chain else None))
        for name, i in named.items():
            z = census["atomic_numbers"][i]
            if atoms[i] is not None or (z != 1 and heavy_join.get((chain,seq,name)) != i):
                raise ValueError("Parent atom index differs from its independently verified raw selection")
            atoms[i] = [ri, report_atom_name(comp, name), ELEMENTS[z]]
    if not all(atoms):
        raise ValueError("Parent projection omits a native atom")
    edges = [(a//3, b//3) for flag in ("BONDS_INC_HYDROGEN", "BONDS_WITHOUT_HYDROGEN")
             for a,b,_ in census["indexed_bonded_terms"][flag]]
    return write_projection(directory, residues, atoms, edges, coordinates, None, sorted(set(sites.values())),
                            native_names=list(census["atom_names"]))


def export_parent(source, original, native, directory):
    if original.returned.source != source.identity or original.definition.configuration != source.identity:
        raise ValueError("Parent source and original native configuration disagree")
    recovered = native.recover(original.definition)
    if (recovered is None or recovered.completion != original.completion or recovered.receipt != original.receipt
            or b"".join(native.iter_completed_output(original.definition,"repair.return")) != original.returned.canonical_bytes()):
        raise ValueError("Parent original complete return or receipt differs from its selected custody")
    assessment = original.assessment
    row = dict(name=PARENT, model=source.identity.to_document(), parent_integrity=source.parent.independent_integrity.to_document(),
               original_geometry_receipt=source.parent.geometry_receipt.to_document(), native_receipt_sha256=original.receipt.fingerprint(),
               completion_sha256=original.completion.fingerprint(), definition=original.definition.identity.to_document(),
               assessment_sha256=assessment.fingerprint() if assessment else None,
               construction_disposition=assessment.repair_disposition.value if assessment else None,
               construction_findings=list(assessment.findings) if assessment else None,
               validated_material_eligible=bool(assessment and assessment.repair_disposition is AssessmentDisposition.SATISFIED),
               status="CONSTRUCTION_UNAVAILABLE")
    if original.returned.error or original.assessment_error or not assessment:
        row.update(native_error=original.returned.error, assessment_error=original.assessment_error)
    else:
        files = read_repair_files(native, original.definition, original.returned)
        current = assess_geometry_repair(source, files, assessment_id=assessment.assessment_id)
        if current != assessment:
            raise ValueError("Independent original parent assessment changed")
        dest = directory / PARENT
        dest.mkdir()
        row.update(status="EXPORTED", raw_topology_sha256=sha256(files["dry.prmtop"]).hexdigest(),
                   raw_endpoint_nm_npy_sha256=sha256(files["final-coordinates-nm.npy"]).hexdigest(),
                   original_atom_origins_sha256=sha256(files["atom-origin-provenance.json"]).hexdigest(),
                   heavy_join_sha256=sha256(files["atom-selection.json"]).hexdigest(), physical_periodicity="NONPERIODIC",
                   original_ligand="CAP", **project_parent(source, files, dest))
    return dict(schema="el-molprobity-export-1", roster="COMMON_INHIBITED_PARENT", source=source.identity.to_document(),
                construction_sha256=original.fingerprint(), models=[row], independent_biological_units=0)
