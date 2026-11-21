# SPDX-License-Identifier: MPL-2.0
"""Complete heavy-coordinate catastrophe checks before native construction.

These deliberately broad bounds reject impossible starting coordinates. Passing
them does not admit force-field accuracy, equilibrium geometry or an ensemble.
All distance comparisons use the input Decimal coordinates, including contacts
across chains and negative-coordinate cell boundaries.
"""

from collections import defaultdict
from decimal import Decimal, ROUND_FLOOR
from itertools import product


CONTACT_CUTOFF = Decimal("1.0")
BACKBONE_RANGE = (Decimal("1.0"), Decimal("1.8"))
_NEIGHBOURS = tuple(product((-1, 0, 1), repeat=3))


def signed_volume(centre, first, second, third):
    a,b,c = (tuple(v-o for v,o in zip(point,centre,strict=True)) for point in (first,second,third))
    return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])


def heavy_stereochemistry(rows, *, minimum_volume=Decimal(0)):
    """Check standard L-amino-acid CA and Ile/Thr CB geometry by named bonds.

    The ordered N/C/CB volume at CA and CA/CG1/CG2 (Ile) or CA/OG1/CG2 (Thr)
    volume at CB are positive for the specified natural protein stereoisomers.
    This naming-based orientation avoids confusing cysteine's CIP R label with
    a D-amino acid. Missing atom completeness remains the topology owner's job.
    """
    if type(minimum_volume) is not Decimal or not minimum_volume.is_finite() or minimum_volume < 0:
        raise ValueError("heavy stereochemistry requires a finite nonnegative volume floor")
    residues = {}
    for chain,position,component,name,_,xyz in rows:
        if chain != "Z":
            residues.setdefault((chain,position,component),{})[name] = xyz
    count,anomalies = 0,[]
    for (chain,position,component),atoms in residues.items():
        centres = [("CA",("N","C","CB"))]
        if component == "ILE":centres.append(("CB",("CA","CG1","CG2")))
        elif component == "THR":centres.append(("CB",("CA","OG1","CG2")))
        for centre,ordered in centres:
            if {centre,*ordered} <= set(atoms):
                count += 1
                volume = signed_volume(atoms[centre],*(atoms[name] for name in ordered))
                if volume <= 0 or volume < minimum_volume:
                    anomalies.append(((chain,position,centre),volume))
    return count,tuple(sorted(anomalies))


def inspect_heavy_geometry(rows):
    """Read (chain, position, component, name, element, xyz) heavy rows.

    No pair is excluded from the sub-Angstrom screen: the supported C/N/O/P/S/Mg
    heavy covalent bonds also exceed that cutoff. Backbone bounds are a second
    gross-error diagnostic, not a substitute for parameter-derived bond checks.
    """
    rows = tuple(rows)
    if not rows:
        raise ValueError("heavy geometry requires the complete atom census")
    atoms, cells, contacts = {}, defaultdict(list), []
    cutoff2 = CONTACT_CUTOFF**2
    for row in rows:
        chain, position, component, name, element, xyz = row
        key = chain, position, name
        if (key in atoms or element.upper() not in {"C", "N", "O", "P", "S", "MG"}
                or len(xyz) != 3 or any(type(v) is not Decimal or not v.is_finite() for v in xyz)):
            raise ValueError("heavy geometry has duplicate, unsupported or nonfinite atoms")
        atoms[key] = row
        cell = tuple(int((v/CONTACT_CUTOFF).to_integral_value(rounding=ROUND_FLOOR)) for v in xyz)
        for offset in _NEIGHBOURS:
            for other in cells[tuple(a+b for a,b in zip(cell,offset,strict=True))]:
                d2 = sum((a-b)**2 for a,b in zip(xyz,other[-1],strict=True))
                if d2 < cutoff2:
                    pair = tuple(sorted((key,(other[0],other[1],other[3]))))
                    contacts.append((*pair,d2))
        cells[cell].append(row)
    backbone, anomalies = 0, []
    low2,high2 = (v*v for v in BACKBONE_RANGE)
    for key,row in atoms.items():
        chain, position, name = key
        if chain == "Z":
            continue
        partner = {"N":("CA",0), "CA":("C",0), "C":("N",1)}.get(name)
        if partner is None:
            continue
        other_key = chain,position+partner[1],partner[0]
        other = atoms.get(other_key)
        if other is None:
            continue
        backbone += 1
        d2 = sum((a-b)**2 for a,b in zip(row[-1],other[-1],strict=True))
        if not low2 <= d2 <= high2:
            anomalies.append((key,other_key,d2))
    stereo_count,stereo_anomalies = heavy_stereochemistry(rows)
    return {"atom_count":len(rows), "all_unordered_pair_count":len(rows)*(len(rows)-1)//2,
        "contact_cutoff_angstrom":CONTACT_CUTOFF, "short_contacts_squared_angstrom":tuple(sorted(contacts)),
        "backbone_bond_count":backbone, "backbone_range_angstrom":BACKBONE_RANGE,
        "backbone_anomalies_squared_angstrom":tuple(sorted(anomalies)),
        "stereocentre_count":stereo_count,"stereochemistry_anomalies_angstrom3":stereo_anomalies,
        "gross_geometry_disposition":"FALSIFIED" if contacts or anomalies or stereo_anomalies else "SATISFIED",
        "physical_geometry_admission":"UNEVALUABLE"}


def require_initial_heavy_geometry(source):
    """Assess every selected arm before authoring, worker preflight or BEGIN.

    The declared I95M replacement atoms are discarded by the native library.
    Their proposal coordinates cannot veto that new construction; every
    inherited anchor and protected chemical atom remains screened.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
    results = []
    for model in source.models:
        rows = heavy_pdb_rows(model.heavy_pdb)
        # I95M proposal CG/SD/CE coordinates are explicitly discarded by the
        # registered PDBFixer operation. They cannot veto their replacement.
        # Every inherited atom remains screened, including the mutation CB.
        small = {chain.chain_id for chain in model.material.chains if chain.subunit == "SSU"}
        mutation_chains = {physical for physical, sequence in model.chain_map if sequence in small} if model.name.endswith("i95m") else set()
        removed = tuple(row for row in rows if row[0] in mutation_chains and row[1] == 95 and row[3] in {"CG", "SD", "CE"})
        if mutation_chains and (len(mutation_chains) != 8 or len(removed) != 24 or any(row[2] != "MET" for row in removed)):
            raise ValueError("initial heavy proposal loses its complete declared I95M replacement census")
        retained = tuple(row for row in rows if not (row[0] in mutation_chains and row[1] == 95 and row[3] in {"CG", "SD", "CE"}))
        result = inspect_heavy_geometry(retained)
        result["native_reconstructed_i95m_sidechain_atoms"] = len(removed)
        result["input_proposal_atom_count"] = len(rows)
        results.append((model.name, result))
    results = tuple(results)
    failed = [(name,result) for name,result in results if result["gross_geometry_disposition"] == "FALSIFIED"]
    if failed:
        details = "; ".join(f"{name}: {len(result['short_contacts_squared_angstrom'])} sub-Angstrom pairs, "
            f"{len(result['backbone_anomalies_squared_angstrom'])} gross backbone anomalies, "
            f"{len(result['stereochemistry_anomalies_angstrom3'])} inverted or planar stereocentres" for name,result in failed)
        raise ValueError("initial heavy geometry requires correction before Amber entry: " + details)
    return results
