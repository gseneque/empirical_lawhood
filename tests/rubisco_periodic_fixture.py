"""Complete exposed atom-table fixture; no active enzyme or numerical evidence."""
from dataclasses import replace
from decimal import Decimal as D
from empirical_lawhood.domains.rubisco.rubisco_response import catalytic_path_selection as paths
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_force_contracts as operator


def make_periodic_fixture():
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import read_prmtop
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from tests.rubisco_response_molecular_fixture import pair, raw_identity
    from tests.test_rubisco_preparation_integrity import amber_text
    from tests.test_rubisco_physical_preparation_geometry import inpcrd

    _, (original_model, raw_top, raw_xyz), _ = pair()
    # A new disclosed control cell keeps context construction small. No coordinates
    # are supplied to a native energy kernel and no molecular state is qualified.
    sections = {k: list(v) for k, v in read_prmtop(raw_top.decode('ascii')).items()}
    sections['BOX_DIMENSIONS'] = list(map(D, (90, 20, 20, 20)))
    # This fixture is an exposed atom table, not an enzyme. Supply the parser's
    # empty unsupported-H-bond flags and one fully used LJ type. The literal
    # negative torsion and zero bond constant remain in the complete source.
    sections['HBOND_ACOEF'] = sections['HBOND_BCOEF'] = sections['HBCUT'] = []
    sections['POINTERS'][1] = 1
    sections['NONBONDED_PARM_INDEX'] = [1]
    sections['LENNARD_JONES_ACOEF'] = [D(64)]
    sections['LENNARD_JONES_BCOEF'] = [D(8)]
    raw_top = amber_text(sections).encode('ascii')
    points, _ = read_initial_coordinates(raw_xyz.decode('ascii'), len(original_model.atoms), periodic=True)
    raw_xyz = inpcrd(points, box=(20, 20, 20, 90, 90, 90)).encode('ascii')
    top, xyz = raw_identity('exposed.constructor.topology', raw_top), raw_identity('exposed.constructor.coordinates', raw_xyz)
    model = replace(original_model, raw_topology=top, raw_coordinates=xyz,
        arrays=replace(original_model.arrays, scientific_references=tuple(sorted((top, xyz), key=lambda r: r.object_id))),
        sources=tuple(sorted((set(original_model.sources)-{original_model.raw_topology, original_model.raw_coordinates})|{top, xyz},
                             key=lambda r: r.object_id)))
    cell = operator.read_amber_periodic_cell(model, raw_top, raw_xyz)
    assert cell.lengths_angstrom == (D(20),)*3 and cell.angles_degrees == (D(90),)*3
    assert decode_canonical_bytes(cell.canonical_bytes(), operator.AmberPeriodicCell, maximum_bytes=2**20) == cell
    site = model.sites[1]
    by_residue = {r.residue_id: r for r in model.residues}
    lsu = by_residue[site.catalytic_residue_id].chain_id
    protein = tuple(r for r in model.residues if r.chain_id == lsu)
    qm = tuple(i for i, a in enumerate(model.atoms)
               if by_residue[a.residue_id].chain_id == lsu or i in (*site.magnesium_atom_indices, *site.ligand_atom_indices))
    qset = set(qm)
    assert not [(b.first, b.second) for b in model.bonds if (b.first in qset) != (b.second in qset)]
    pin = model.material.sources[0]
    charge = sum(model.atoms[i].atomic_number for i in qm) % 2
    selection = paths.CatalyticPathSelection('path.exposed.constructor', model.identity, len(model.atoms), site.site_id,
        qm, tuple(i for i in range(len(model.atoms)) if i not in qset),
        tuple(paths.CatalyticProteinRegion(r.residue_id, 'COMPLETE_RESIDUE') for r in protein), (),
        'NONE', (), charge, 1, pin, None, pin, pin, 'MOVING_FULL_ASSEMBLY',
        tuple(sorted({model.identity, *model.sources}, key=lambda r: r.object_id)))
    settings = operator.PeriodicForceSettings('settings.exposed.constructor', 'wb97x', 'def2-svpd', 'RKS', 3,
        D('1e-12'), D('1e-9'), 200, 256, D(9), D(6), D('.25'), (41, 41, 41), D('1e-8'))
    return model,selection,cell,settings,raw_top,raw_xyz
