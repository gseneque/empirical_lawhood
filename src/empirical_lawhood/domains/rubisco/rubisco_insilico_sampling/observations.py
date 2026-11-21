# SPDX-License-Identifier: MPL-2.0
"""Source-mapped eight-site geometry; none of these observables is a rate.

Contacts use the conserved CB anchor, count each other-chain residue once,
retain source indices and avoid a mutation's extra atom becoming extra contacts.
The site area is protein-interface burial, not a ligand binding free energy.
"""

import math

RADII_ANGSTROM={"C":1.70,"N":1.55,"O":1.52,"P":1.80,"S":1.80}


def minimum_image(displacements,box):
    import numpy as np
    cell=np.asarray(box,dtype=float)
    if cell.shape!=(3,3) or not np.isfinite(cell).all() or np.any(np.diag(cell)<=0) or not np.allclose(cell,np.diag(np.diag(cell)),rtol=0,atol=1e-8):
        raise ValueError("native isotropic orthorhombic receiver changes selected box geometry")
    values=np.asarray(displacements,dtype=float)
    return values-np.round(values/np.diag(cell))*np.diag(cell)


def build_plan(origin,reference_angstrom,construct_id):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    realized=origin["amber_realization"]
    atoms=realized["atoms"]
    reference=np.asarray(reference_angstrom,dtype=float)
    if len(atoms)!=len(reference) or tuple(row["amber_atom_index"] for row in atoms)!=tuple(range(len(atoms))) or not np.isfinite(reference).all():
        raise ValueError("observation plan omits complete authentic Amber atom origins")
    chains=realized["complete_chains"]
    small=[row for row in chains if row["subunit"]=="ssu"]
    large=[row for row in chains if row["subunit"]=="lsu"]
    if len(small)!=8 or len(large)!=8:
        raise ValueError("observation plan changes full L8S8 source assembly")
    position=95 if construct_id.startswith("gp.") else 98
    protein_chains={row["chain"] for row in chains}
    heavy=[row for row in atoms if row["chain"] in protein_chains and row["source_origin"] is not None and row["source_origin"]["element"].upper()!="H"]
    mg=[row["amber_atom_index"] for row in atoms if row["residue_name"].upper()=="MG" and row["atom"].upper()=="MG"]
    caps={}
    for row in atoms:
        if row["residue_name"]=="CAP" and row["source_origin"] is not None and row["source_origin"]["element"].upper()!="H":
            caps.setdefault(row["amber_residue_index"],[]).append(row["amber_atom_index"])
    if len(mg)!=8 or len(caps)!=8:
        raise ValueError("observation plan omits declared eight Mg/CABP active sites")
    ligands=list(caps.values())
    distances=np.array([[float(np.linalg.norm(reference[m]-reference[indices],axis=1).min()) for indices in ligands] for m in mg])
    rows,columns=linear_sum_assignment(distances)
    cap_for_mg={mg[i]:ligands[j] for i,j in zip(rows,columns,strict=True)}
    anchors=[]
    for chain in small:
        found=[row["amber_atom_index"] for row in heavy if row["chain"]==chain["chain"] and row["position"]==position and row["atom"]=="CB"]
        if len(found)!=1:
            raise ValueError("controlled SSU intervention lacks its unique conserved CB anchor")
        anchors.append(found[0])
    mapping=np.array([[float(np.linalg.norm(reference[anchor]-reference[m])) for m in mg] for anchor in anchors])
    rows,columns=linear_sum_assignment(mapping)
    sites=[]
    for i,j in zip(rows,columns,strict=True):
        chain=small[i]["chain"]
        metal=mg[j]
        ligand=cap_for_mg[metal]
        candidates=[]
        for lsu in large:
            ca=[row["amber_atom_index"] for row in heavy if row["chain"]==lsu["chain"] and row["atom"]=="CA"]
            distance=float(np.linalg.norm(reference[ca]-reference[ligand].mean(axis=0),axis=1).min())
            candidates.append((distance,lsu["chain"],ca))
        _,lsu,ca=min(candidates,key=lambda row:row[:2])
        region=[index for index in ca if np.linalg.norm(reference[index]-reference[ligand],axis=1).min()<=8.0]
        if len(region)<3 or np.linalg.matrix_rank(reference[region]-reference[region].mean(axis=0))<2:
            raise ValueError("source-defined8A active region cannot support a rigid alignment")
        site_indices=[row["amber_atom_index"] for row in heavy if row["chain"]==chain and row["position"]==position]
        sites.append(dict(site_id="site."+chain,ssu_chain=chain,ssu_position=position,anchor=anchors[i],site_heavy=site_indices,mg=metal,ligand_heavy=ligand,lsu_chain=lsu,active_region_ca=region,
                          reference_region_relative_mg=(reference[region]-reference[metal]).tolist(),reference_anchor_relative_mg=(reference[anchors[i]]-reference[metal]).tolist()))
    return dict(construct_id=construct_id,atom_count=len(atoms),sites=sites,
                protein_heavy=tuple(row["amber_atom_index"] for row in heavy),
                protein_chain=tuple(row["chain"] for row in heavy),
                protein_residue=tuple(row["amber_residue_index"] for row in heavy),
                protein_radii_angstrom=tuple(RADII_ANGSTROM[row["source_origin"]["element"].upper()] for row in heavy),
                mg_cap_assignment_distances_angstrom=distances.tolist(),ssu_mg_assignment_distances_angstrom=mapping.tolist(),
                definition="SOURCE_GEOMETRIC_PAIRING_NOT_A_KNOWN_ALLOSTERIC_ROUTE",physical_independent_units=0)


def _fit(mobile,reference):
    import numpy as np
    left,right=np.asarray(mobile),np.asarray(reference)
    lm,rm=left.mean(axis=0),right.mean(axis=0)
    u,_,vt=np.linalg.svd((left-lm).T@(right-rm))
    sign=np.eye(3);sign[2,2]=1 if np.linalg.det(u@vt)>0 else -1
    rotation=u@sign@vt
    fitted=(left-lm)@rotation+rm
    return float(np.sqrt(np.mean(np.sum((fitted-right)**2,axis=1)))),rotation,lm,rm


def _sphere(points):
    import numpy as np
    indices=np.arange(points,dtype=float)+0.5
    z=1-2*indices/points
    radius=np.sqrt(1-z*z)
    phi=indices*(math.pi*(3-math.sqrt(5)))
    return np.column_stack((radius*np.cos(phi),radius*np.sin(phi),z))


def _burial(site,plan,coordinates,tree,box,points):
    import numpy as np
    heavy=np.array(plan["protein_heavy"],dtype=int)
    chains=np.array(plan["protein_chain"])
    radii=np.array(plan["protein_radii_angstrom"])+1.4
    offsets=_sphere(points)
    by_index={int(index):number for number,index in enumerate(heavy)}
    area=0.0
    # All candidate blockers within the mathematical sphere overlap distance
    # are included. The radius is a surface definition, never an output cap.
    for atom in site["site_heavy"]:
        position=by_index[atom]
        radius=radii[position]
        neighbors=tree.query_ball_point(coordinates[atom]%np.diag(box),radius+float(radii.max()),eps=0)
        neighbors=[index for index in neighbors if heavy[index]!=atom]
        relative=minimum_image(coordinates[heavy[neighbors]]-coordinates[atom],box)
        test=offsets*radius
        occluded=np.sum((test[:,None,:]-relative[None,:,:])**2,axis=2)<radii[neighbors][None,:]**2
        own=np.array([chains[index]==site["ssu_chain"] for index in neighbors])
        free_monomer=~occluded[:,own].any(axis=1)
        free_assembly=~occluded.any(axis=1)
        area+=4*math.pi*radius*radius*float(np.sum(free_monomer&~free_assembly))/points
    return area


def observe(plan,positions_angstrom,box_angstrom,*,sasa_points=None):
    import numpy as np
    from scipy.spatial import cKDTree
    positions=np.asarray(positions_angstrom,dtype=float)
    box=np.asarray(box_angstrom,dtype=float)
    minimum_image(np.zeros((1,3)),box)
    if positions.shape!=(plan["atom_count"],3) or not np.isfinite(positions).all() or len(plan["sites"])!=8:
        raise ValueError("native observation omits full finite source-mapped receiver")
    heavy=np.array(plan["protein_heavy"],dtype=int)
    chains=np.array(plan["protein_chain"])
    residues=np.array(plan["protein_residue"])
    tree=cKDTree(positions[heavy]%np.diag(box),boxsize=np.diag(box))
    result=[]
    for site in plan["sites"]:
        anchor=positions[site["anchor"]]%np.diag(box)
        neighbors=tree.query_ball_point(anchor,8.0,eps=0)
        residue_minima={}
        for index in neighbors:
            if chains[index]==site["ssu_chain"]:
                continue
            distance=float(np.linalg.norm(minimum_image(positions[heavy[index]]-positions[site["anchor"]],box)))
            residue=int(residues[index])
            residue_minima[residue]=min(residue_minima.get(residue,float("inf")),distance)
        count=min(16,len(heavy))
        while True:
            distances,indices=tree.query(anchor,k=count,eps=0)
            actual=[float(distance) for distance,index in zip(np.atleast_1d(distances),np.atleast_1d(indices),strict=True) if chains[int(index)]!=site["ssu_chain"]]
            if actual:
                other_min=min(actual);break
            if count==len(heavy):
                raise ValueError("complete source assembly lacks another protein chain")
            count=min(len(heavy),count*2)
        local=minimum_image(positions[site["active_region_ca"]]-positions[site["mg"]],box)
        rmsd,rotation,lm,rm=_fit(local,site["reference_region_relative_mg"])
        current=minimum_image(positions[site["anchor"]]-positions[site["mg"]],box)
        aligned=(current-lm)@rotation+rm
        interface=float(np.linalg.norm(aligned-np.asarray(site["reference_anchor_relative_mg"])))
        mg_distance=float(np.linalg.norm(minimum_image(positions[site["ligand_heavy"]]-positions[site["mg"]],box),axis=1).min())
        result.append(dict(site_id=site["site_id"],anchor_contact_counts=tuple(sum(value<=cutoff for value in residue_minima.values()) for cutoff in (3.0,5.0,8.0)),
                           complete_other_chain_residue_minima_within_8A=tuple(sorted(residue_minima.items())),other_chain_minimum_angstrom=other_min,
                           active_region_rmsd_angstrom=rmsd,interface_displacement_angstrom=interface,mg_inhibitor_minimum_angstrom=mg_distance,
                           buried_site_area_angstrom2=None if sasa_points is None else _burial(site,plan,positions,tree,box,sasa_points)))
    return tuple(result)
