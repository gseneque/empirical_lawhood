# SPDX-License-Identifier: MPL-2.0
"""PURE lexical reader for the selected OpenMM complete-heavy PDB branch.

ATOM/HETATM and genuine TER records share the original serial denominator.
Every directed CONECT term, including repeated neighbors for bond order, is
retained. This validates serialization and references, not chemical topology.
Historical atom-only readers and their method evidence remain unchanged.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import re

from empirical_lawhood.kernel.provenance import ObjectIdentity


DESCRIPTION = (
    "Selected fixed-column ASCII complete-heavy PDB; exact consecutive original "
    "ATOM/HETATM/TER serial denominator, immediate preceding-residue TER join, "
    "unique ordered residue/atom identities, finite lexical coordinates, no "
    "alternate/insertion/model ambiguity; every directed CONECT term retained "
    "with genuine atom references. No renumbering, topology or physical claim."
)
METHOD = ObjectIdentity(
    "method.rubisco-dynamics.serialized-heavy-pdb",
    "empirical-lawhood/rubisco-insilico-dynamics/serialized-heavy-pdb-method",
    "1.0.0", sha256(DESCRIPTION.encode()).hexdigest(),
)
_INTEGER = re.compile(r"[0-9]+\Z")
_COORDINATE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")


@dataclass(frozen=True, slots=True)
class SerializedHeavyPDB:
    atoms: tuple[dict, ...]
    ters: tuple[dict, ...]
    conect_rows: tuple[tuple[int, ...], ...]

    @property
    def directed_bonds(self):
        return tuple((row[0], neighbor) for row in self.conect_rows for neighbor in row[1:])


def _integer(token):
    token = token.strip()
    if not _INTEGER.fullmatch(token):
        raise ValueError("complete-heavy PDB needs an unambiguous decimal integer")
    return int(token)


def _residue(line):
    if len(line) < 26 or line[16:17].strip() or line[26:27].strip():
        raise ValueError("complete-heavy PDB alternate/insertion or residue ambiguity")
    chain, component, position = line[21].strip(), line[17:20].strip(), _integer(line[22:26])
    if not chain or not component or position <= 0:
        raise ValueError("complete-heavy PDB omits its residue identity")
    return dict(chain=chain, component=component, position=position)


def read_serialized_heavy_pdb(text):
    """Retain exact atom serials; only actual scoped TER rows consume gaps."""
    if type(text) is not str or not text.isascii():
        raise ValueError("selected complete-heavy PDB must be ASCII text")
    atoms, ters, bonds = [], [], []
    serial, last_residue, pending_ter = 0, None, False
    residues, keys = set(), set()
    connective, ended = False, False
    for line in text.splitlines():
        if not line.strip():
            continue
        if ended:
            raise ValueError("complete-heavy PDB has records after END")
        kind = line[:6]
        if kind in ("ATOM  ", "HETATM", "TER   "):
            if connective:
                raise ValueError("complete-heavy PDB atom/TER follows CONECT")
            actual_serial = _integer(line[6:11])
            if actual_serial != serial + 1:
                raise ValueError("complete-heavy PDB has duplicate/reordered/unjustified serial gap")
            serial = actual_serial
            residue = _residue(line)
            residue_key = (residue["chain"], residue["position"])
            if kind == "TER   ":
                if not atoms or pending_ter or residue != last_residue:
                    raise ValueError("complete-heavy PDB TER does not terminate the preceding residue")
                if line[11:16].strip() or line[27:].strip():
                    raise ValueError("complete-heavy PDB TER has undeclared fields")
                ters.append(dict(serial=actual_serial, **residue))
                pending_ter = True
                continue
            if len(line) < 78 or line[11:12].strip():
                raise ValueError("complete-heavy PDB atom lacks fixed-column fields")
            if last_residue != residue:
                if residue_key in residues:
                    raise ValueError("complete-heavy PDB reorders/repeats a residue block")
                if last_residue is not None and (
                    residue["chain"] < last_residue["chain"]
                    or residue["chain"] == last_residue["chain"]
                    and residue["position"] <= last_residue["position"]
                ):
                    raise ValueError("complete-heavy PDB reorders selected chain/residue records")
                residues.add(residue_key)
            elif pending_ter:
                raise ValueError("complete-heavy PDB TER ambiguously divides one residue")
            atom, element = line[12:16].strip(), line[76:78].strip().upper()
            if not atom or not element.isalpha() or element in ("H", "D"):
                raise ValueError("complete-heavy PDB lacks an explicit heavy atom identity")
            coordinate_tokens = tuple(line[index:index+8].strip() for index in (30, 38, 46))
            if any(not _COORDINATE.fullmatch(token) for token in coordinate_tokens):
                raise ValueError("complete-heavy PDB has malformed/nonfinite coordinates")
            xyz = tuple(Decimal(token) for token in coordinate_tokens)
            if any(not value.is_finite() for value in xyz):
                raise ValueError("complete-heavy PDB has nonfinite coordinates")
            key = (*residue_key, atom)
            if key in keys:
                raise ValueError("complete-heavy PDB duplicates an atom identity")
            keys.add(key)
            atoms.append(dict(serial=actual_serial, **residue, atom=atom, element=element, xyz=xyz))
            last_residue, pending_ter = residue, False
        elif kind == "CONECT":
            connective = True
            payload = line[6:].rstrip()
            if not payload or len(payload) % 5:
                raise ValueError("complete-heavy PDB CONECT loses fixed-width references")
            row = tuple(_integer(payload[index:index+5]) for index in range(0, len(payload), 5))
            if len(row) < 2 or any(value == row[0] for value in row[1:]):
                raise ValueError("complete-heavy PDB CONECT has no neighbor or a self reference")
            bonds.append(row)
        elif kind == "REMARK":
            if atoms or connective:
                raise ValueError("complete-heavy PDB REMARK follows scientific rows")
        elif line == "END":
            ended = True
        else:
            raise ValueError("complete-heavy PDB contains an unsupported/ambiguous record")
    if not atoms:
        raise ValueError("complete-heavy PDB has no atom denominator")
    atom_serials = {row["serial"] for row in atoms}
    if any(value not in atom_serials for row in bonds for value in row):
        raise ValueError("complete-heavy PDB CONECT references a missing atom or TER")
    return SerializedHeavyPDB(tuple(atoms), tuple(ters), tuple(bonds))


def read_heavy_pdb(text):
    """Explicit successor interface, compatible atom rows without renumbering."""
    return read_serialized_heavy_pdb(text).atoms
