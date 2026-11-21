# SPDX-License-Identifier: MPL-2.0
"""Complete initial Amber atom mapping, separate from physical admission.

The supported caller authenticates the original native archive and scaffold
publication. This pure mapper repeats the independent raw topology assessment
and retains complete atom/residue/edge populations in native order. It neither
constructs molecular coordinates nor runs a force backend.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import struct

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.rubisco.rubisco_response.amber_template import RUBP_NAMES
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import ActiveSiteSelection, ChemicalProtocol
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import GpActiveScaffold
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberModelInput, GpInitialAmberInput, heavy_pdb_rows
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import _residues, assess_initial_topology, read_initial_coordinates, solvent_last_residues, solvation_atom_correspondence
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import GpAmberUnitProduct
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularAtom, MolecularBond, MolecularRepresentation, MolecularResidue, MolecularSite, NativeTopologyBond
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import LigandChemicalGraph, SiteLigandBinding, validate_ligand_correspondence


def raw_amber_identity(kind, raw):
    if kind not in {"topology", "coordinates"} or type(raw) is not bytes or not raw:
        raise ValueError("initial molecular mapping needs exact original native bytes")
    digest = sha256(raw).hexdigest()
    return ObjectIdentity("native.initial-amber."+kind+"."+digest,
        "empirical-lawhood/rubisco-response/native-amber-"+kind+"-bytes", "1.0.0", digest)


def read_initial_molecular_coordinates(files, census, dry_census):
    """Separate atom-origin correspondence from the actual final coordinates.

    The caller must first admit the complete native construction. Solvation
    correspondence uses pre-minimization coordinates; the returned molecular
    array and source identity use only the exact retained relaxed endpoint.
    """
    final, box = read_initial_coordinates(files["relaxed.inpcrd"].decode("ascii"), census["term_census"]["atoms"], periodic=True)
    premin, _ = read_initial_coordinates(files["model.inpcrd"].decode("ascii"), census["term_census"]["atoms"], periodic=True)
    dry, _ = read_initial_coordinates(files["dry.inpcrd"].decode("ascii"), dry_census["term_census"]["atoms"], periodic=False)
    correspondence = solvation_atom_correspondence(dry_census, census, dry, premin)
    return raw_amber_identity("coordinates", files["relaxed.inpcrd"]), final, box, correspondence


def initial_ligand_graph(source):
    """Retain the selected keto graph while translating the six Amber H names."""
    exact(source, GpInitialAmberInput)
    aliases = dict(RUBP_NAMES)
    graph = source.ligand.chemical_graph
    return replace(graph, graph_id="graph.initial-amber-rubp."+source.ligand.fingerprint(),
        atoms=tuple(replace(atom, native_atom_name=aliases.get(atom.native_atom_name, atom.native_atom_name))
                    for atom in graph.atoms),
        sources=tuple(sorted({*graph.sources, source.ligand.identity, graph.identity}, key=lambda row: row.object_id)))


def _initial_native_tables(model, scaffold, graph, census, topology, original_residue_indices):
    """Join a parsed complete topology; private construction, no admission.

    Author labels here refer to the exact published prepared PDB, identified
    by scaffold.identity. They are not relabelled as original PDB/mmCIF author
    positions. Added solvent/ions have no invented structural author labels.
    Native atom source indices refer to the raw Amber topology.
    """
    exact(model, GpAmberModelInput)
    exact(scaffold, GpActiveScaffold)
    exact(graph, LigandChemicalGraph)
    exact(topology, ObjectIdentity)
    if (model.scaffold != scaffold.identity or model.material != scaffold.material
            or model.chain_map != scaffold.chain_map):
        raise ValueError("native atom mapping substitutes its original complete scaffold")
    original_rows = heavy_pdb_rows(model.heavy_pdb)
    expected_rows = tuple((atom.chain, atom.position, atom.component, atom.name, atom.element,
        tuple(D(f"{float(value):.3f}") for value in atom.xyz_angstrom)) for atom in scaffold.atoms)
    if original_rows != expected_rows:
        raise ValueError("native atom mapping substitutes the complete published heavy-coordinate table")
    original = {}
    for chain, position, component, name, element, _ in original_rows:
        original.setdefault((chain, position, component), {})[name] = element
    original = tuple(solvent_last_residues(original).items())
    native = _residues(census)
    if (len(native) < len(original) or len(original_residue_indices) != len(original)
            or len(set(original_residue_indices)) != len(original)
            or any(type(i) is not int or not 0 <= i < len(native) for i in original_residue_indices)):
        raise ValueError("native topology omits an original prepared residue")
    original_at_native = dict(zip(original_residue_indices, original, strict=True))
    chain_map = dict(model.chain_map)
    chains = {row.chain_id: row for row in model.material.chains}
    placements = {row.lsu_chain: row for row in scaffold.placements}
    site_ids = {physical: "site.gp."+chain_map[physical] for physical in placements}
    chemical_keys = {}
    for physical, placement in placements.items():
        for key, role in ((("Z", placement.ligand_position), "LIGAND"),
                          (("Z", placement.magnesium_position), "MAGNESIUM")):
            if key in chemical_keys:
                raise ValueError("native site mapping aliases two ligand or magnesium residues")
            chemical_keys[key] = role, site_ids[physical]
    elements = {"C": 6, "N": 7, "O": 8, "P": 15, "S": 16, "MG": 12}
    residues, atom_residues, catalytic = [], {}, {}
    for r, (component, names) in enumerate(native):
        source, author_chain, author_number = topology, None, None
        chain_id, position, letter, site_id = None, None, None, None
        if r in original_at_native:
            (physical, prepared_position, prepared_component), heavy = original_at_native[r]
            expected = {"HIS": "HIE", "HID": "HIE", "HOH": "WAT"}.get(prepared_component, prepared_component)
            actual_heavy = {name: census["atomic_numbers"][i] for name, i in names.items()
                            if census["atomic_numbers"][i] != 1}
            if component.upper() != expected.upper() or actual_heavy != {name: elements[z.upper()] for name, z in heavy.items()}:
                raise ValueError("native residue changes a complete prepared heavy name, element or component")
            source, author_chain, author_number = scaffold.identity, physical, prepared_position
            if physical in chain_map:
                role, chain_id, position = "PROTEIN", chain_map[physical], prepared_position
                letter = chains[chain_id].sequence[position-1]
                residue_id = f"residue.protein.{chain_id}.{position}"
                if component == "KCX":
                    if physical not in site_ids or site_ids[physical] in catalytic:
                        raise ValueError("native atom mapping changes the all-LSU catalytic residue census")
                    site_id = site_ids[physical]
                    catalytic[site_id] = residue_id, chain_id, position
            elif prepared_component in {"HOH", "WAT"}:
                role, residue_id = "WATER", f"residue.retained-water.{physical.lower()}.{prepared_position}"
            else:
                try:
                    role, site_id = chemical_keys[(physical, prepared_position)]
                except KeyError as error:
                    raise ValueError("native chemical residue has no exact original site assignment") from error
                residue_id = "residue."+site_id+"."+role.lower()
                if (role, component.upper()) not in {("LIGAND", "RUB"), ("MAGNESIUM", "MG")}:
                    raise ValueError("native site assignment changes its ligand or magnesium component")
        else:
            if component == "WAT":
                role = "WATER"
                if set(names) != {"O", "H1", "H2"} or tuple(census['atomic_numbers'][names[n]] for n in ("O", "H1", "H2")) != (8, 1, 1):
                    raise ValueError("added solvent lacks its complete three-site water population")
            elif component in {"Na+", "Cl-"}:
                role = "ION"
                if len(names) != 1 or census['atomic_numbers'][next(iter(names.values()))] != {"Na+": 11, "Cl-": 17}[component]:
                    raise ValueError("added counterion changes its exact element population")
            else:
                raise ValueError("native topology contains an undeclared added chemical residue")
            # Independent solvations do not acquire common water/ion identity
            # merely because their native residue indices happen to agree.
            residue_id = f"residue.native-{role.lower()}.{topology.object_fingerprint}.{r}"
        residues.append(MolecularResidue(residue_id, component, role, chain_id, position, letter,
            author_chain, author_number, "", source, site_id))
        for i in names.values():
            if i in atom_residues:
                raise ValueError("native residue mapping duplicates a physical atom")
            atom_residues[i] = residue_id
    count = census['term_census']['atoms']
    if set(atom_residues) != set(range(count)) or set(catalytic) != set(site_ids.values()):
        raise ValueError("native mapping omits complete atoms or an all-eight-site catalytic residue")
    atoms = tuple(MolecularAtom(f"atom.amber.{topology.object_fingerprint}.{i}", atom_residues[i],
        census['atom_names'][i], census['atomic_numbers'][i], census['masses'][i],
        census['charges_scaled'][i], D('18.2223'), census['atom_types'][i], topology, str(i+1))
        for i in range(count))
    edge_pairs = []
    for key in ('BONDS_INC_HYDROGEN', 'BONDS_WITHOUT_HYDROGEN'):
        edge_pairs.extend(tuple(sorted((a//3, b//3))) for a, b, _ in census['indexed_bonded_terms'][key])
    if len(edge_pairs) != len(set(edge_pairs)):
        raise ValueError("native topology repeats a force-topology edge")
    edges = {pair: NativeTopologyBond(*pair) for pair in edge_pairs}
    by_residue = {row.residue_id: row for row in residues}
    role_atoms = {(site, role): [] for site in site_ids.values() for role in ('LIGAND', 'MAGNESIUM')}
    for i, atom in enumerate(atoms):
        residue = by_residue[atom.residue_id]
        if (residue.site_id, residue.role) in role_atoms:
            role_atoms[residue.site_id, residue.role].append(i)
    sites, bindings, selected_sites = [], [], []
    for site_id in sorted(site_ids.values()):
        ligand = tuple(role_atoms[site_id, 'LIGAND'])
        magnesium = tuple(role_atoms[site_id, 'MAGNESIUM'])
        if len(magnesium) != 1 or atoms[magnesium[0]].atomic_number != 12:
            raise ValueError("native mapping lacks exactly one magnesium at an original site")
        named = {atoms[i].name: i for i in ligand}
        if set(named) != {a.native_atom_name for a in graph.atoms}:
            raise ValueError("native ligand changes its complete selected chemical atom population")
        joined = tuple(named[a.native_atom_name] for a in graph.atoms)
        if any(atoms[i].atomic_number != atom.atomic_number for i, atom in zip(joined, graph.atoms, strict=True)):
            raise ValueError("native ligand changes a selected chemical element")
        chemical_edges = {tuple(sorted((joined[b.first], joined[b.second]))): b.order for b in graph.bonds}
        members = set(ligand)
        if ({pair for pair in edges if set(pair).issubset(members)} != set(chemical_edges)
                or any((a in members) != (b in members) for a, b in edges)):
            raise ValueError("native ligand changes its selected adjacency or adds a cross-fragment bond")
        edges.update((pair, MolecularBond(*pair, order)) for pair, order in chemical_edges.items())
        residue_id, lsu, position = catalytic[site_id]
        sites.append(MolecularSite(site_id, residue_id, magnesium, ligand, (), (), graph.identity))
        bindings.append(SiteLigandBinding(site_id, graph.identity, joined))
        selected_sites.append((site_id, lsu, position))
    return (tuple(sorted(residues, key=lambda row: row.residue_id)), atoms,
            tuple(edges[pair] for pair in sorted(edges)), tuple(sites), tuple(bindings), tuple(selected_sites))


def map_initial_amber_representation(*, source, model, scaffold, unit, files):
    """Map an authenticated, construction-qualified endpoint; retain no physical admission."""
    return _checked_endpoint_mapping(source, model, scaffold, unit, files, allow_rejected=False)


class UnmappableDiagnosticEndpoint(ValueError):
    """Rejected original material has no exact diagnostic topology-to-coordinate join."""


def map_initial_amber_diagnostic(*, source, model, scaffold, unit, files):
    """Map a completed endpoint for independent geometry triage, retaining any rejection."""
    mapped = _checked_endpoint_mapping(source, model, scaffold, unit, files, allow_rejected=True)
    return dict(**mapped, original_construction_disposition=unit.assessment.construction_disposition.value,
                validated_material_eligible=unit.assessment.construction_disposition is A.SATISFIED)


def _checked_endpoint_mapping(source, model, scaffold, unit, files, *, allow_rejected):
    for value, kind in ((source, GpInitialAmberInput), (model, GpAmberModelInput),
                        (scaffold, GpActiveScaffold), (unit, GpAmberUnitProduct)):
        exact(value, kind)
    if (model not in source.models or unit.returned.model != model.identity
            or source.identity not in unit.definition.sources
            or unit.completion.operational_status is not OperationalStatus.SUCCEEDED
            or unit.returned.return_code != 0 or unit.returned.timed_out or unit.returned.error is not None
            or unit.assessment is None or unit.assessment_error is not None
            or (not allow_rejected and unit.assessment.construction_disposition is not A.SATISFIED)
            or scaffold.ligand_preparation != source.ligand.identity):
        raise ValueError("molecular mapping requires the selected known successful independently assessed native construction")
    checked = assess_initial_topology(source, model, files, assessment_id=unit.assessment.assessment_id)
    if checked != unit.assessment:
        raise ValueError("native molecular mapping differs from its independent current raw assessment")
    try:
        return _map_assessed_endpoint(source, model, scaffold, unit, files, checked)
    except (ValueError, ArithmeticError) as error:
        if allow_rejected and checked.construction_disposition is A.FALSIFIED:
            raise UnmappableDiagnosticEndpoint(str(error)) from error
        raise


def _map_assessed_endpoint(source, model, scaffold, unit, files, checked):
    top = raw_amber_identity('topology', files['model.prmtop'])
    graph = initial_ligand_graph(source)
    census = assigned_census_supported_inactive14(read_prmtop(files['model.prmtop'].decode('ascii')))
    dry_census = assigned_census_supported_inactive14(read_prmtop(files['dry.prmtop'].decode('ascii')))
    xyz, points, box, correspondence = read_initial_molecular_coordinates(files, census, dry_census)
    del dry_census
    residues, atoms, bonds, sites, bindings, selected = _initial_native_tables(model, scaffold, graph, census, top,
        correspondence.original_to_solvated_residues)
    protocol = source.identity
    chemistry = ChemicalProtocol('chemistry.gp-initial-amber.'+source.fingerprint(),
        tuple(ActiveSiteSelection(site, lsu, position, True, True, 'RUBP', protocol, protocol, graph.identity)
              for site, lsu, position in selected), 'FIXED_OCCUPANCY', protocol,
        tuple(sorted({protocol, graph.identity, *graph.sources}, key=lambda row: row.object_id)),
        ('requirement.molecular.active-protonation-ensemble', 'requirement.molecular.metal-coordination-ensemble',
         'requirement.molecular.solvent-and-ion-activity'))
    coordinate_bytes = b''.join(struct.pack('<ddd', *(float(v) for v in p)) for p in points)
    arrays = ArrayDatasetManifest('arrays.gp-initial-amber.'+xyz.object_fingerprint,
        (ArrayDatasetMember('coordinates-angstrom', '<f8', (len(atoms), 3), sha256(coordinate_bytes).hexdigest()),),
        tuple(sorted((top, xyz), key=lambda row: row.object_id)))
    receipt = ObjectIdentity.from_record(unit.receipt.receipt_id, unit.receipt)
    completion = ObjectIdentity.from_record(unit.receipt.task_id+'.completion', unit.completion)
    references = tuple(sorted({protocol, model.identity, scaffold.identity, checked.identity,
        unit.definition.identity, receipt, completion, top, xyz, graph.identity,
        *model.material.sources, *scaffold.sources, *chemistry.sources}, key=lambda row: row.object_id))
    identifier = 'molecular.gp-initial-amber.'+sha256((model.fingerprint()+top.object_fingerprint+xyz.object_fingerprint).encode()).hexdigest()
    representation = MolecularRepresentation(identifier, model.material, chemistry, D('298.15'), protocol, protocol,
        top, xyz, residues, atoms, bonds, sites, arrays, references)
    validate_ligand_correspondence(representation, (graph,), bindings)
    return dict(representation=representation, chemical_graph=graph, ligand_bindings=bindings,
        coordinate_bytes=coordinate_bytes, box_angstrom=box, independent_assessment=checked,
        original_atom_correspondence=correspondence,
        new_native_calls=0, active_ensemble_admission='UNEVALUABLE', force_accuracy_admission='UNEVALUABLE')
