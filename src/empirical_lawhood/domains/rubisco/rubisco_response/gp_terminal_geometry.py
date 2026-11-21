# SPDX-License-Identifier: MPL-2.0
"""Read the actual initialized heavy coordinates before full Amber assignment."""

from hashlib import sha256
import json
from math import degrees

import numpy as np

from .constructed_geometry_domain import domain_from_heavy_rows
from .gp_constructed_geometry import _omega, origin_mobility
from .gp_heavy_geometry import signed_volume


TERMINAL_GEOMETRY_FILE = "initial-terminal-geometry.json"
INITIAL_REJECTION = "Initialized geometry rejected before full Amber assignment and minimization"


def initial_terminal_geometry(heavy_pdb, origin, *, origin_sha256):
    """Measure all protein chiral centres and construction-affected non-Pro peptides.

    Use the serialized coordinates actually passed to Amber. Quartet membership
    comes from the same named protein definitions as the construction domain.
    Positive signed determinant and |omega| >= 150 degrees are the existing
    parent endpoint screens. A degenerate peptide has no measurable omega.
    """
    atoms, constructed = origin_mobility(heavy_pdb, origin)
    keys = [(a["chain"], a["position"], a["atom"]) for a in atoms]
    joined = dict(zip(keys, range(len(keys)), strict=True))
    moving = {joined[key] for key in constructed}
    rows = [(a["chain"], a["position"], a["component"], a["atom"], a["element"], a["xyz"]) for a in atoms]
    domain, labels = domain_from_heavy_rows(rows, tuple(joined.items()), keys, len(keys))
    affected_centres = 0
    stereo_failures = []
    for quartet, label in zip(domain.stereocentres, labels["stereocentre_labels"], strict=True):
        affected = bool(moving.intersection(quartet))
        affected_centres += affected
        volume = signed_volume(*(atoms[i]["xyz"] for i in quartet))
        if volume <= 0:
            stereo_failures.append(dict(
                centre=list(label), component=atoms[quartet[0]]["component"],
                atoms=[list(keys[i]) for i in quartet], construction_affected=affected,
                signed_volume_angstrom3=str(volume),
            ))

    affected_peptides = 0
    peptide_failures = []
    for quartet, label in zip(domain.peptides, labels["peptide_labels"], strict=True):
        if moving.isdisjoint(quartet):
            continue
        affected_peptides += 1
        try:
            omega = degrees(_omega([np.asarray(atoms[i]["xyz"], dtype=float) for i in quartet]))
        except ValueError:
            omega = None
        if omega is None or abs(omega) < 150:
            peptide_failures.append(dict(
                peptide=list(label), atoms=[list(keys[i]) for i in quartet],
                omega_degrees=round(omega, 8) if omega is not None else None,
                reason="undefined-dihedral" if omega is None else "outside-trans-range",
            ))

    return dict(
        basis="gp-initialized-heavy-chirality-and-construction-affected-nonpro-omega-v1",
        initialized_pdb_sha256=sha256(heavy_pdb.encode("ascii")).hexdigest(),
        atom_origin_sha256=origin_sha256,
        heavy_atoms=len(atoms), constructed_heavy_atoms=len(constructed),
        residues_with_constructed_atoms=len({(chain, pos) for chain, pos, _ in constructed}),
        protein_stereocentres=len(domain.stereocentres), construction_affected_stereocentres=affected_centres,
        construction_affected_nonpro_peptides=affected_peptides, minimum_absolute_omega_degrees=150,
        required_signed_determinant="positive (angstrom cubed)",
        stereocentre_violations=stereo_failures, peptide_violations=peptide_failures,
        disposition="REJECTED" if stereo_failures or peptide_failures else "SCREEN_PASSED",
    )


def terminal_geometry_bytes(report):
    return (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("ascii")


def require_initial_terminal_geometry(report):
    if report["disposition"] != "SCREEN_PASSED":
        raise ValueError(
            f"{INITIAL_REJECTION}: "
            f"{len(report['stereocentre_violations'])}/{report['protein_stereocentres']} protein stereocentres, "
            f"{len(report['peptide_violations'])}/{report['construction_affected_nonpro_peptides']} "
            f"construction-affected non-Pro peptides; see {TERMINAL_GEOMETRY_FILE}"
        )
