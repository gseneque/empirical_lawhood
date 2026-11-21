# SPDX-License-Identifier: MPL-2.0
"""Read heavy-atom distances from crystallographic biological assemblies."""

from collections import defaultdict
import gzip
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile


def contact_profile(protein, large, small):
    import numpy as np
    from scipy.spatial import cKDTree

    tree = cKDTree(large)
    if len(small) != 8:
        raise ValueError("The selected structure must expose eight SSUs")
    sites = defaultdict(list)
    coverage = {}
    for chain, entries in sorted(small.items()):
        coordinates = np.array([xyz for _, xyz in entries])
        distances = tree.query(coordinates)[0]
        by_site = defaultdict(list)
        for (position, _), distance in zip(entries, distances, strict=True):
            if not 1 <= position <= len(protein):
                raise ValueError("SSU site lies outside its sequence")
            by_site[position].append(distance)
        coverage[chain] = len(by_site)
        for position, values in by_site.items():
            sites[position].append(float(min(values)))
    return {
        "sequence": protein,
        "observed_sites_by_chain": coverage,
        "sites": {
            i: {
                "minimum_distances_A": d,
                "weight": sum(1 / (1 + (v / 5) ** 6) for v in d) / len(d),
            }
            for i, d in sorted(sites.items())
        },
    }


def cif_profile(path):
    from openmm.app.internal.pdbx.reader.PdbxReader import PdbxReader

    data = []
    with gzip.open(path, "rt") as stream:
        PdbxReader(stream).read(data)
    polymers = data[0].getObj("entity_poly")
    sequences = {
        row[polymers.getIndex("entity_id")]: "".join(
            row[polymers.getIndex("pdbx_seq_one_letter_code_can")].split()
        )
        for row in polymers.getRowList()
    }
    atom = data[0].getObj("atom_site")
    fields = (
        "label_entity_id",
        "label_asym_id",
        "label_seq_id",
        "type_symbol",
        "label_alt_id",
        "occupancy",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
    )
    cols = [atom.getIndex(k) for k in fields]
    large = []
    small = defaultdict(list)
    for row in atom.getRowList():
        entity, chain, seq_id, element, alt, occ, *xyz = [row[i] for i in cols]
        if (
            entity not in ("1", "2")
            or element in ("H", "D")
            or alt not in (".", "?", "A")
            or float(occ) <= 0
        ):
            continue
        point = tuple(map(float, xyz))
        if entity == "1":
            large.append(point)
        else:
            small[chain].append((int(seq_id), point))
    return contact_profile(sequences["2"], large, small)


def gp_profile(raw):
    from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_core import (
        LSU,
        SSU,
        observed_residues,
        xyz,
    )

    names = dict(
        zip(
            (
                "ALA",
                "CYS",
                "ASP",
                "GLU",
                "PHE",
                "GLY",
                "HIS",
                "ILE",
                "LYS",
                "LEU",
                "MET",
                "ASN",
                "PRO",
                "GLN",
                "ARG",
                "SER",
                "THR",
                "VAL",
                "TRP",
                "TYR",
            ),
            "ACDEFGHIKLMNPQRSTVWY",
            strict=True,
        )
    )
    names.update(HIE="H", HID="H", HIP="H", CYX="C")
    large = []
    small = defaultdict(list)
    sequences = defaultdict(list)
    for (chain, _number, _ins, name), rows in observed_residues(raw.decode("ascii")):
        points = [xyz(r) for r in rows if r[76:78].strip() not in ("H", "D")]
        if chain in LSU and (name in names or name == "KCX"):
            large.extend(points)
        if chain in SSU and name in names:
            sequences[chain].append(names[name])
            small[chain].extend((len(sequences[chain]), point) for point in points)
    sequences = {"".join(letters) for letters in sequences.values()}
    if len(sequences) != 1:
        raise ValueError("SSU sequences disagree between native copies")
    return contact_profile(sequences.pop(), large, small)


def all_profiles(sources: Path, reference: Path):
    result = {}
    for code in ("3ZXW", "4RUB", "1GK8"):
        path = sources / f"{code}-assembly1.cif.gz"
        result[code] = {
            **cif_profile(path),
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
    with ZipFile(reference) as archive:
        for label, member in (("M1", "observed-scoped-M1-WT"), ("V1", "scoped-V1-WT")):
            raw = archive.read(f"runs/{member}/input.pdb")
            result[label] = {**gp_profile(raw), "sha256": sha256(raw).hexdigest()}
    return result
