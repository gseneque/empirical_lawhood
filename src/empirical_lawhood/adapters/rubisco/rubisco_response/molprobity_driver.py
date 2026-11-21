# SPDX-License-Identifier: MPL-2.0
"""Run inside the independently selected CCTBX environment, without importing EL."""

from hashlib import file_digest, sha256
import inspect
import json
from pathlib import Path
import struct
import sys


def atom_census(hierarchy, table):
    """Rejoin every parsed H, water, ion and protein atom to the native array."""
    if len(hierarchy.models()) != 1:
        raise ValueError("CCTBX read multiple coordinate models")
    expected = {}
    for i, (ri, name, element) in enumerate(table["atoms"]):
        r = table["residues"][ri]
        key = (r["chain"], r["seq"], r["component"], name)
        if key in expected:
            raise ValueError("Duplicate atom locator in exchange table")
        expected[key] = (i, element)
    coordinates = bytearray(24 * len(expected))
    for a in hierarchy.atoms_with_labels():
        key = (a.chain_id.strip(), int(a.resseq.strip()), a.resname.strip(), a.name.strip())
        if a.altloc.strip() or a.icode.strip() or key not in expected:
            raise ValueError("CCTBX read a different complete atom population")
        i, element = expected.pop(key)
        if a.element.strip().upper() != element:
            raise ValueError("CCTBX substituted a reported atom's element")
        struct.pack_into("<ddd", coordinates, i * 24, *a.xyz)
    digest = sha256(coordinates).hexdigest()
    if expected or digest != table["coordinate_array_sha256"]:
        raise ValueError("CCTBX lost a native atom or changed exact relaxed coordinates")
    return {"atom_count": len(table["atoms"]), "coordinate_array_sha256": digest, "model_id": hierarchy.models()[0].id.strip()}


def restore_cartesian_roundoff(interpreted, original):
    """Use the submitted Cartesian doubles after CCTBX builds empirical restraints.

    Orthogonalization/fractionalization can disturb last bits. An atom change or a
    shift larger than 1e-10 Å refuses; the subsequent analysis receives exactly the original points.
    """
    def key(a):
        return (a.chain_id, a.resseq, a.icode, a.resname, a.altloc, a.name)
    original_points = {key(a): tuple(a.xyz) for a in original.atoms_with_labels()}
    assignments = []
    maximum = 0.0
    for atom in interpreted.atoms():
        wanted = original_points.pop(key(atom.fetch_labels()))
        error = max(abs(a-b) for a,b in zip(atom.xyz,wanted,strict=True))
        if error > 1e-10:
            raise ValueError("CCTBX interpretation moved an original atom beyond Cartesian roundoff")
        if error:
            assignments.append((atom, wanted))
            maximum = max(error, maximum)
    if original_points:
        raise ValueError("CCTBX interpretation omitted original atoms")
    for atom, wanted in assignments:
        atom.xyz = wanted
    return {"atoms_restored": len(assignments), "maximum_axis_roundoff_angstrom": maximum}


def data_manager(cif, restraints):
    from iotbx.data_manager import DataManager
    dm = DataManager(["model", "restraint"])
    for path in restraints:
        dm.process_restraint_file(str(path))
    dm.process_model_file(str(cif))
    return dm


def calculate(component, hierarchy, cif, restraints, table):
    if component == "ramalyze":
        from mmtbx.validation.ramalyze import ramalyze
        return ramalyze(pdb_hierarchy=hierarchy, outliers_only=False), {}
    if component == "rotalyze":
        from mmtbx.validation.rotalyze import rotalyze
        return rotalyze(pdb_hierarchy=hierarchy, outliers_only=False), {}
    if component == "cbetadev":
        from mmtbx.validation.cbetadev import cbetadev
        return cbetadev(pdb_hierarchy=hierarchy, outliers_only=False), {}
    if component == "omegalyze":
        from mmtbx.validation.omegalyze import omegalyze
        return omegalyze(pdb_hierarchy=hierarchy, nontrans_only=False), {}
    dm = data_manager(cif, restraints)
    if component == "clashscore":
        from libtbx import phil
        from mmtbx.probe import Helpers
        from mmtbx.validation.clashscore2 import clashscore2
        probe = phil.parse(Helpers.probe_phil_parameters).extract().probe
        options = dict(keep_hydrogens=True, do_flips=False, nuclear=True, fast=False, condensed_probe=False)
        if "ignore_missing_restraints" in inspect.signature(clashscore2).parameters:
            options["ignore_missing_restraints"] = False
        result = clashscore2(probe, data_manager=dm, **options)
        # Some CCTBX releases expose the actual hydrogenated structure used by Probe.
        # Older releases cannot certify used-H coverage from an input-file digest alone.
        used = getattr(result, "hydrogenated_model", None)
        manager = result.probe_clashscore_manager
        detail = dict(clashscore=result.get_clashscore(), native_nonwater_atoms=manager.n_atoms,
                      native_serious_clashes=manager.n_clashes, probe_options=options,
                      used_atom_census=atom_census(used.get_hierarchy(), table) if used is not None else None)
        return result, detail
    if component == "covalent_geometry":
        from mmtbx.model import manager
        from mmtbx.validation.mp_validate_bonds import mp_validate_bonds
        model = dm.get_model()
        settings = manager.get_default_pdb_interpretation_params()
        settings.pdb_interpretation.use_neutron_distances = True
        settings.pdb_interpretation.allow_polymer_cross_special_position = True
        settings.pdb_interpretation.flip_symmetric_amino_acids = False
        settings.pdb_interpretation.clash_guard.nonbonded_distance_threshold = None
        settings.pdb_interpretation.restraints_library.cdl = True
        model.process(make_restraints=True, pdb_interpretation_params=settings)
        used_hierarchy = model.get_hierarchy()
        rounding = restore_cartesian_roundoff(used_hierarchy, hierarchy)
        census = atom_census(used_hierarchy, table)
        result = mp_validate_bonds(pdb_hierarchy=used_hierarchy,
                                   geometry_restraints_manager=model.get_restraints_manager().geometry, outliers_only=False)
        return result, {"used_atom_census": census, "conformation_dependent_library": True, "cartesian_roundoff": rounding}
    raise ValueError("Unknown structural validator component")


def store_rows(directory, component, result):
    # Individual CCTBX result.as_JSON records, retained in full. Avoid redundant, very large trees.
    digest, count, size = sha256(), 0, 0
    with (directory / (component + ".jsonl")).open("xb") as stream:
        for item in result.results:
            raw = (json.dumps(json.loads(item.as_JSON()), allow_nan=False, separators=(",", ":")) + "\n").encode()
            stream.write(raw)
            digest.update(raw)
            count += 1
            size += len(raw)
    return dict(status="RETURNED", rows=count, bytes=size, sha256=digest.hexdigest())


def overall_score(components):
    from mmtbx.validation.utils import molprobity_score
    names = ("ramalyze", "rotalyze", "clashscore")
    if any(components.get(name, {}).get("status") != "RETURNED" for name in names):
        return None
    rama, rota, probe = (components[name] for name in names)
    if not rama["native_total"] or not rota["native_total"]:
        return None
    return molprobity_score(probe["clashscore"], 100 * rota["native_outliers"] / rota["native_total"],
                            100 * rama["native_favored"] / rama["native_total"])


def main():
    cif, mapping, destination, *restraints = map(Path, sys.argv[1:])
    map_raw = mapping.read_bytes()
    table = json.loads(map_raw)
    map_sha = sha256(map_raw).hexdigest()
    del map_raw
    with cif.open("rb") as stream:
        cif_sha = file_digest(stream, "sha256").hexdigest()
    from iotbx import pdb
    input_model = pdb.input(file_name=str(cif))
    import math
    expected = table["reader_cell_angstrom_degrees"]
    cell = input_model.crystal_symmetry().unit_cell().parameters()
    if not all(math.isclose(float(a), b, rel_tol=1e-14, abs_tol=1e-12) for a,b in zip(expected, cell, strict=True)):
        raise ValueError("CCTBX changed the supplied reader unit cell")
    hierarchy = input_model.construct_hierarchy()
    census = atom_census(hierarchy, table)
    results = {}
    for name in ("ramalyze", "rotalyze", "cbetadev", "omegalyze", "covalent_geometry", "clashscore"):
        try:
            result, details = calculate(name, hierarchy, cif, restraints, table)
            if name == "ramalyze":
                details.update(native_total=result.n_total, native_favored=result.n_favored)
            elif name == "rotalyze":
                details.update(native_total=result.n_total, native_outliers=result.n_outliers)
            subresults = {"bonds": result.bonds, "angles": result.angles} if name == "covalent_geometry" else {name: result}
            for key, obj in subresults.items():
                results[key] = {**store_rows(destination, key, obj), **details}
            del subresults, result, obj
        except Exception as error:
            for key in ("bonds", "angles") if name == "covalent_geometry" else (name,):
                results[key] = dict(status="COMPONENT_UNAVAILABLE", error_type=type(error).__name__, error=str(error))
        # Flush each component separately so a timeout preserves its completed predecessors.
        payload = dict(input_census=census, input_mmcif_sha256=cif_sha, input_atom_map_sha256=map_sha,
                       components=results, cctbx_molprobity_score=overall_score(results))
        temporary = destination / "in-progress.tmp"
        temporary.write_text(json.dumps(payload, sort_keys=True, allow_nan=False))
        temporary.replace(destination / "components.json")


if __name__ == "__main__":
    main()
