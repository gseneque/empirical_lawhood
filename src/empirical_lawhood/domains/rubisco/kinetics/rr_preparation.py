# SPDX-License-Identifier: MPL-2.0
"""Exact Rr source admission and an incomplete, inherited heavy-atom scaffold.

Selected reconstruction semantics were reviewed from the legacy completion
commit aa9346547560abcb6500f2e97b53b96f456d9be3, preparation.py SHA256
1dcad5beaae85ae24333ee8f67ade798fbecebbb57f656306671c6e035c596d0.
This module does not invoke that code, complete atoms, parameterize chemistry,
build a native context or forecast kinetics. Records are ordinary immutable
development inputs, not registered scientific products or assay admissions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
import re
import shlex
from typing import ClassVar


SOURCE_PINS = (
    ("9RUB.cif", 774540, "33242f8e519c2e032c5a83de33a6350eb5c38cef42b5a14e1f8ecfb9230575dd"),
    ("9RUB.pdb", 634878, "80dcc3cfdcd12154f1d7c21e9438b9e6b0e9d887381aeeef6f2350b3e1b41fd5"),
    ("P04718.fasta", 581, "d7edfcdad62964ce96ec766ca4bd83e115c19ee257585c9014f07b7d325e48d0"),
)
SOURCE_MAXIMUM_BYTES = 1024 * 1024
PACKET_MAXIMUM_BYTES = 2 * 1024 * 1024
REFERENCE_CHOICES = ("deposited-D91", "modeled-H91")
VARIANTS = ("unedited-reference", "D263N", "H287N")
PROTON_VIEWS = ("enolate-proton-view-A", "enolate-proton-view-B")
LATER_CONTEXT_ROSTER = tuple((v, p) for v in VARIANTS for p in PROTON_VIEWS)
COMMON_AUTHOR_INTERVAL = (2, 459)
BACKBONE_AND_CB = frozenset(("N", "CA", "C", "O", "CB"))
AA = dict(zip(
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split(),
    "ARNDCQEGHILKMFPSTWYV", strict=True,
))
ATOM_COLUMNS = (
    "group_PDB", "id", "type_symbol", "label_atom_id", "label_alt_id",
    "label_comp_id", "label_asym_id", "label_entity_id", "label_seq_id",
    "pdbx_PDB_ins_code", "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
    "B_iso_or_equiv", "pdbx_formal_charge", "auth_seq_id", "auth_comp_id",
    "auth_asym_id", "auth_atom_id", "pdbx_PDB_model_num",
)
_COORDINATE = re.compile(r"-?[0-9]+\.[0-9]{3}\Z")
_ABSENT = frozenset((".", "?", ""))


def _decimal(token: str) -> Decimal:
    if type(token) is not str or len(token) > 32:
        raise ValueError("native numeric token is not bounded text")
    try:
        value = Decimal(token)
    except ArithmeticError as exc:
        raise ValueError("invalid native numeric token") from exc
    if not value.is_finite():
        raise ValueError("nonfinite native numeric token")
    return value


def _tokens(data: bytes) -> tuple[str, ...]:
    """Bounded lexical reader for the selected deposited CIF, not a library parser."""
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("native CIF is not ASCII") from exc
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(";"):
            block = [line[1:]]
            i += 1
            while i < len(lines) and not lines[i].startswith(";"):
                block.append(lines[i])
                i += 1
            if i == len(lines):
                raise ValueError("unterminated native CIF text block")
            result.append("\n".join(block))
        else:
            try:
                result.extend(shlex.split(line, comments=True, posix=True))
            except ValueError as exc:
                raise ValueError("invalid native CIF quoting") from exc
        i += 1
    if len(result) > 500000 or any(len(v) > 4096 for v in result):
        raise ValueError("native CIF token bound exceeded")
    return tuple(result)


def _tables(data: bytes) -> tuple[dict[str, tuple[tuple[tuple[str, str], ...], ...]], dict[str, str]]:
    tokens = _tokens(data)
    if not tokens or tokens[0] != "data_9RUB":
        raise ValueError("selected native CIF block differs")
    loops: dict[str, tuple[tuple[tuple[str, str], ...], ...]] = {}
    scalars: dict[str, str] = {}
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "loop_":
            i += 1
            headers = []
            while i < len(tokens) and tokens[i].startswith("_"):
                headers.append(tokens[i])
                i += 1
            if not headers or len(headers) > 64 or len(set(headers)) != len(headers):
                raise ValueError("native CIF loop has absent or duplicate columns")
            category = headers[0].split(".")[0]
            if category in loops or any(h.split(".")[0] != category for h in headers):
                raise ValueError("duplicate or mixed native CIF loop category")
            values = []
            while i < len(tokens):
                next_token = tokens[i]
                if len(values) % len(headers) == 0 and (
                    next_token.startswith("_") or next_token in ("loop_", "stop_")
                    or next_token.startswith("data_")
                ):
                    break
                values.append(next_token)
                i += 1
            if len(values) % len(headers) or len(values) // len(headers) > 20000:
                raise ValueError("native CIF loop shape or row bound differs")
            names = tuple(h.split(".", 1)[1] for h in headers)
            loops[category] = tuple(
                tuple(zip(names, values[k:k + len(headers)], strict=True))
                for k in range(0, len(values), len(headers))
            )
        elif token.startswith("_"):
            if token in scalars or i + 1 == len(tokens):
                raise ValueError("duplicate or incomplete native CIF scalar")
            scalars[token] = tokens[i + 1]
            i += 2
        else:
            raise ValueError("unexpected native CIF control token")
    return loops, scalars


@dataclass(frozen=True, slots=True)
class RrNativeAtomV1:
    """All original atom-site tokens and a distinct exact PDB line witness."""

    native_tokens: tuple[tuple[str, str], ...]
    pdb_line_number: int
    pdb_line: str

    def __post_init__(self) -> None:
        if (type(self.native_tokens) is not tuple
                or any(type(pair) is not tuple or len(pair) != 2
                       or any(type(v) is not str for v in pair) for pair in self.native_tokens)
                or tuple(k for k, _ in self.native_tokens) != ATOM_COLUMNS
                or any(type(v) is not str for _, v in self.native_tokens)
                or type(self.pdb_line_number) is not int or self.pdb_line_number < 1
                or type(self.pdb_line) is not str or len(self.pdb_line) < 78):
            raise ValueError("native atom projection shape differs")
        if self.token("pdbx_PDB_model_num") != "1":
            raise ValueError("multiple native models are not selected")
        if self.token("label_alt_id") not in _ABSENT or self.token("pdbx_PDB_ins_code") not in _ABSENT:
            raise ValueError("alternate or insertion mapping is not selected")
        if not self.source_id.isdecimal() or int(self.source_id) < 1:
            raise ValueError("native CIF atom ID differs")
        if self.token("group_PDB") not in ("ATOM", "HETATM"):
            raise ValueError("native atom group differs")
        if any(not _COORDINATE.fullmatch(v) for v in self.coordinate_tokens):
            raise ValueError("native coordinate lexical precision differs")
        for v in self.coordinate_tokens:
            _decimal(v)
        if self.occupancy not in (Decimal(0), Decimal(1)):
            raise ValueError("partial native occupancy is not selected")
        _decimal(self.token("B_iso_or_equiv"))
        if self.element not in ("C", "N", "O", "P", "S", "MG"):
            raise ValueError("native heavy-element census differs")

    def token(self, name: str) -> str:
        return dict(self.native_tokens)[name]

    @property
    def source_id(self) -> str:
        return self.token("id")

    @property
    def pdb_serial(self) -> str:
        return self.pdb_line[6:11].strip()

    @property
    def author_chain(self) -> str:
        return self.token("auth_asym_id")

    @property
    def author_position(self) -> int:
        return int(self.token("auth_seq_id"))

    @property
    def component(self) -> str:
        return self.token("auth_comp_id")

    @property
    def atom_name(self) -> str:
        return self.token("auth_atom_id")

    @property
    def element(self) -> str:
        return self.token("type_symbol")

    @property
    def coordinate_tokens(self) -> tuple[str, str, str]:
        return (self.token("Cartn_x"), self.token("Cartn_y"), self.token("Cartn_z"))

    @property
    def coordinates_angstrom(self) -> tuple[Decimal, Decimal, Decimal]:
        return tuple(Decimal(v) for v in self.coordinate_tokens)  # type: ignore[return-value]

    @property
    def occupancy(self) -> Decimal:
        return _decimal(self.token("occupancy"))


def _pdb(data: bytes) -> tuple[tuple[tuple[int, str], ...], dict[str, str]]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("native PDB is not ASCII") from exc
    atoms = []
    seqres: dict[str, list[str]] = {}
    declared: dict[str, int] = {}
    for number, line in enumerate(lines, 1):
        if line.startswith(("MODEL ", "ENDMDL")):
            raise ValueError("multiple PDB model grammar is not selected")
        if line.startswith(("ATOM  ", "HETATM")):
            if len(line) < 78:
                raise ValueError("truncated native PDB atom line")
            atoms.append((number, line))
        elif line.startswith("SEQRES"):
            chain = line[11]
            declared_count = int(line[13:17])
            if declared.setdefault(chain, declared_count) != declared_count:
                raise ValueError("inconsistent PDB sequence length")
            seqres.setdefault(chain, []).extend(line[19:70].split())
    if len({line[6:11].strip() for _, line in atoms}) != len(atoms):
        raise ValueError("duplicate native PDB atom serial")
    if set(seqres) != {"A", "B"} or any(len(v) != declared[k] for k, v in seqres.items()):
        raise ValueError("native PDB sequence census differs")
    try:
        sequences = {k: "".join(AA[v] for v in values) for k, values in seqres.items()}
    except KeyError as exc:
        raise ValueError("unknown native PDB sequence component") from exc
    return tuple(atoms), sequences


def _crossmap(
    rows: tuple[tuple[tuple[str, str], ...], ...],
    pdb_atoms: tuple[tuple[int, str], ...],
) -> tuple[RrNativeAtomV1, ...]:
    if len(rows) != len(pdb_atoms):
        raise ValueError("CIF/PDB atom census differs")
    atoms = tuple(RrNativeAtomV1(row, number, line)
                  for row, (number, line) in zip(rows, pdb_atoms, strict=True))
    if len({a.source_id for a in atoms}) != len(atoms):
        raise ValueError("duplicate native CIF atom ID")
    identities = set()
    for atom in atoms:
        line = atom.pdb_line
        identity = (atom.author_chain, atom.author_position, atom.component, atom.atom_name)
        if identity in identities:
            raise ValueError("duplicate native atom identity")
        identities.add(identity)
        pairs = (
            (atom.token("group_PDB"), line[:6].strip()),
            (atom.atom_name, line[12:16].strip()), (atom.component, line[17:20].strip()),
            (atom.author_chain, line[21]), (str(atom.author_position), line[22:26].strip()),
            (atom.element, line[76:78].strip()),
            ("", line[16].strip()), ("", line[26].strip()),
        )
        if any(a != b for a, b in pairs):
            raise ValueError("CIF/PDB native atom identity mismatch")
        if atom.coordinate_tokens != (line[30:38].strip(), line[38:46].strip(), line[46:54].strip()):
            raise ValueError("CIF/PDB exact coordinate tokens mismatch")
        for cif_token, pdb_token in ((atom.token("occupancy"), line[54:60].strip()),
                                     (atom.token("B_iso_or_equiv"), line[60:66].strip())):
            if _decimal(cif_token) != _decimal(pdb_token):
                raise ValueError("CIF/PDB numeric metadata mismatch")
    return atoms


@dataclass(frozen=True, slots=True)
class RrNativeBondV1:
    source_tokens: tuple[tuple[str, str], ...]
    first_source_id: str
    second_source_id: str

    @property
    def kind(self) -> str:
        return dict(self.source_tokens)["conn_type_id"]


@dataclass(frozen=True, slots=True)
class RrMissingHeavyAtomsV1:
    chain: str
    author_position: int
    component: str
    atom_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RrNativeSourceV1:
    """Derived fields cannot be supplied independently of exact original bytes."""

    cif_bytes: bytes = field(repr=False)
    pdb_bytes: bytes = field(repr=False)
    fasta_bytes: bytes = field(repr=False)
    atoms: tuple[RrNativeAtomV1, ...] = field(init=False, repr=False)
    bonds: tuple[RrNativeBondV1, ...] = field(init=False)
    native_sequence: str = field(init=False)
    reference_sequence: str = field(init=False)
    sequence_conflicts: tuple[tuple[int, str, str], ...] = field(init=False)
    native_conflict_rows: tuple[tuple[tuple[str, str], ...], ...] = field(init=False)
    polymer_mapping_rows: tuple[tuple[tuple[str, str], ...], ...] = field(init=False, repr=False)
    missing_residue_rows: tuple[tuple[tuple[str, str], ...], ...] = field(init=False)
    missing_or_zero_atom_rows: tuple[tuple[tuple[str, str], ...], ...] = field(init=False)
    missing_heavy_atoms: tuple[RrMissingHeavyAtomsV1, ...] = field(init=False)
    heavy_atom_templates: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = field(init=False, repr=False)
    source_bindings: tuple[tuple[str, int, str], ...] = field(init=False)
    CLAIM_SCOPE: ClassVar[str] = "EXPOSED_NATIVE_SOURCE_FACTS_NOT_ASSAY_PARENT_OR_PREPARED_QM"

    def __post_init__(self) -> None:
        supplied = (self.cif_bytes, self.pdb_bytes, self.fasta_bytes)
        if (any(type(v) is not bytes or len(v) > SOURCE_MAXIMUM_BYTES for v in supplied)
                or sum(len(v) for v in supplied) > PACKET_MAXIMUM_BYTES):
            raise ValueError("Rr original source byte bound or type differs")
        for value, (name, count, digest) in zip(supplied, SOURCE_PINS, strict=True):
            if len(value) != count or sha256(value).hexdigest() != digest:
                raise ValueError(f"Rr original source bytes differ: {name}")
        facts = _source_facts(self.cif_bytes, self.pdb_bytes, self.fasta_bytes)
        for name, value in facts.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "source_bindings", SOURCE_PINS)

    @property
    def zero_occupancy_atoms(self) -> tuple[RrNativeAtomV1, ...]:
        return tuple(a for a in self.atoms if a.occupancy == 0)

    @property
    def native_water_atoms(self) -> tuple[RrNativeAtomV1, ...]:
        return tuple(a for a in self.atoms if a.component == "HOH")

    @property
    def exact_assay_parent_admitted(self) -> bool:
        return False


def _source_facts(cif: bytes, pdb: bytes, fasta: bytes) -> dict[str, object]:
    tables, scalars = _tables(cif)
    if scalars.get("_entry.id") != "9RUB":
        raise ValueError("native structure identity differs")
    try:
        pdb_atoms, sequences = _pdb(pdb)
        atoms = _crossmap(tables["_atom_site"], pdb_atoms)
        native_sequence = "".join(scalars["_entity_poly.pdbx_seq_one_letter_code_can"].split())
        raw_native_sequence = "".join(scalars["_entity_poly.pdbx_seq_one_letter_code"].split())
        fasta_lines = fasta.decode("ascii").splitlines()
        reference = "".join(fasta_lines[1:])
    except (KeyError, UnicodeError) as exc:
        raise ValueError("missing native source category or sequence") from exc
    if (len(atoms) != 7044 or len(native_sequence) != 466 or native_sequence != raw_native_sequence
            or sequences != {"A": native_sequence, "B": native_sequence}
            or len(reference) != 466 or not fasta_lines[0].startswith(">sp|P04718|")):
        raise ValueError("native atom or protein census differs")
    differences = tuple((i, a, b) for i, (a, b) in enumerate(zip(reference, native_sequence, strict=True), 1)
                        if a != b)
    if differences != ((91, "H", "D"),):
        raise ValueError("native/reference sequence conflict differs")
    if Counter(a.component for a in atoms if a.token("group_PDB") == "HETATM") != {
        "FMT": 6, "MG": 2, "RUB": 36,
    }:
        raise ValueError("native Mg/RuBP/FMT atom census differs")
    by_key = {(a.author_chain, str(a.author_position), a.component, a.atom_name): a for a in atoms}
    by_polymer: dict[tuple[str, str], list[RrNativeAtomV1]] = defaultdict(list)
    for atom in atoms:
        if atom.token("label_entity_id") == "1":
            by_polymer[(atom.author_chain, str(atom.author_position))].append(atom)
    for chain in ("A", "B"):
        for position, comp in ((91, "ASP"), (111, "ASN"), (191, "LYS"), (193, "ASP"),
                               (194, "GLU"), (263, "ASP"), (287, "HIS")):
            selected = by_polymer[(chain, str(position))]
            if not selected or {a.component for a in selected} != {comp} or any(
                a.token("label_seq_id") != str(position) for a in selected
            ):
                raise ValueError("native active-site or author/label correspondence differs")
        rubp = tuple(a for a in atoms if a.author_chain == chain and a.component == "RUB")
        if Counter(a.element for a in rubp) != {"C": 5, "O": 11, "P": 2}:
            raise ValueError("native full RuBP composition differs")
    bonds = []
    for raw in tables.get("_struct_conn", ()):
        row = dict(raw)
        endpoints = []
        for n in (1, 2):
            prefix = f"ptnr{n}_"
            key = (row[prefix + "auth_asym_id"], row[prefix + "auth_seq_id"],
                   row[prefix + "auth_comp_id"], row[prefix + "label_atom_id"])
            if key not in by_key or row[prefix + "symmetry"] != "1_555":
                raise ValueError("native covalent/metal atom mapping missing or external")
            endpoints.append(by_key[key].source_id)
        bonds.append(RrNativeBondV1(raw, *endpoints))
    if len({dict(b.source_tokens)["id"] for b in bonds}) != len(bonds):
        raise ValueError("duplicate native connection ID")
    covalent = tuple(b for b in bonds if b.kind == "covale")
    activation_chains = []
    for bond in covalent:
        first, second = (next(a for a in atoms if a.source_id == n)
                         for n in (bond.first_source_id, bond.second_source_id))
        if first.component == "FMT":
            first, second = second, first
        if (first.component, first.author_position, first.atom_name, second.component,
                second.atom_name, first.author_chain == second.author_chain) != (
                "LYS", 191, "NZ", "FMT", "C", True):
            raise ValueError("native Lys191-NZ/FMT-C covalent activation join differs")
        activation_chains.append(first.author_chain)
    if sorted(activation_chains) != ["A", "B"]:
        raise ValueError("both unique native covalent activation joins are required")
    for chain in ("A", "B"):
        magnesium = tuple(a for a in atoms if a.component == "MG" and a.author_chain == chain)
        if len(magnesium) != 1:
            raise ValueError("native paired Mg census differs")
        connected = {n for b in bonds if b.kind == "metalc"
                     and magnesium[0].source_id in (b.first_source_id, b.second_source_id)
                     for n in (b.first_source_id, b.second_source_id)}
        comps = {a.component for a in atoms if a.source_id in connected}
        if not {"ASP", "RUB", "MG"} <= comps:
            raise ValueError("native Mg/protein/RuBP connection is incomplete")
    polymer_rows = tables.get("_pdbx_poly_seq_scheme", ())
    if len(polymer_rows) != 932:
        raise ValueError("native complete polymer mapping census differs")
    expected_residues = {(chain, str(pos)) for chain in ("A", "B") for pos in range(1, 467)}
    mapped = set()
    observed = set(by_polymer)
    for raw in polymer_rows:
        row = dict(raw)
        key = (row["asym_id"], row["seq_id"])
        if (key in mapped or key not in expected_residues or row["pdb_seq_num"] != row["seq_id"]
                or AA.get(row["mon_id"]) != native_sequence[int(row["seq_id"]) - 1]):
            raise ValueError("duplicate or inconsistent native polymer mapping")
        mapped.add(key)
        found = by_polymer.get(key, ())
        if any(a.component != row["mon_id"] or a.token("label_asym_id") != row["asym_id"]
               or a.token("label_seq_id") != row["seq_id"] for a in found):
            raise ValueError("native polymer/atom mapping mismatch")
    missing_rows = tables.get("_pdbx_unobs_or_zero_occ_residues", ())
    declared_missing = {(dict(r)["auth_asym_id"], dict(r)["auth_seq_id"]) for r in missing_rows
                        if dict(r)["occupancy_flag"] == "1"}
    if declared_missing != expected_residues - observed:
        raise ValueError("native missing residue census differs")
    conflicts = tables.get("_struct_ref_seq_dif", ())
    if (len(conflicts) != 2 or {
        (dict(r)["pdbx_pdb_strand_id"], dict(r)["pdbx_auth_seq_num"], dict(r)["mon_id"],
         dict(r)["db_mon_id"], dict(r)["details"]) for r in conflicts
    } != {("A", "91", "ASP", "HIS", "conflict"), ("B", "91", "ASP", "HIS", "conflict")}):
        raise ValueError("native sequence conflict annotation differs")
    templates: dict[str, dict[str, str]] = {}
    for raw in tables.get("_chem_comp_atom", ()):
        row = dict(raw)
        if row["type_symbol"] not in ("H", "D") and row["atom_id"] != "OXT":
            target = templates.setdefault(row["comp_id"], {})
            if row["atom_id"] in target:
                raise ValueError("duplicate native component atom template")
            target[row["atom_id"]] = row["type_symbol"]
    missing_heavy = []
    for chain, position in sorted(observed, key=lambda v: (v[0], int(v[1]))):
        found = by_polymer[(chain, position)]
        comp = found[0].component
        absent = tuple(sorted(set(templates[comp]) - {a.atom_name for a in found}))
        if absent:
            missing_heavy.append(RrMissingHeavyAtomsV1(chain, int(position), comp, absent))
    if tuple(missing_heavy) != (RrMissingHeavyAtomsV1("A", 460, "THR", ("CB", "CG2", "OG1")),):
        raise ValueError("native missing heavy-atom census differs")
    zero_atoms = tuple(a for a in atoms if a.occupancy == 0)
    if len(zero_atoms) != 9:
        raise ValueError("native zero-occupancy census differs")
    return {
        "atoms": atoms, "bonds": tuple(bonds), "native_sequence": native_sequence,
        "reference_sequence": reference, "sequence_conflicts": differences,
        "native_conflict_rows": conflicts, "polymer_mapping_rows": polymer_rows,
        "missing_residue_rows": missing_rows,
        "missing_or_zero_atom_rows": tables.get("_pdbx_unobs_or_zero_occ_atoms", ()),
        "missing_heavy_atoms": tuple(missing_heavy),
        "heavy_atom_templates": tuple((comp, tuple(sorted(v.items()))) for comp, v in sorted(templates.items())),
    }


def decode_rr_source(cif_bytes: bytes, pdb_bytes: bytes, fasta_bytes: bytes) -> RrNativeSourceV1:
    """Hash-first admission of three exact originals; no filesystem access."""
    return RrNativeSourceV1(cif_bytes, pdb_bytes, fasta_bytes)


@dataclass(frozen=True, slots=True)
class RrProjectedAtomV1:
    source_atom: RrNativeAtomV1
    chain: str
    author_position: int
    component: str
    atom_name: str

    @property
    def coordinate_tokens(self) -> tuple[str, str, str]:
        return self.source_atom.coordinate_tokens

    @property
    def coordinates_angstrom(self) -> tuple[Decimal, Decimal, Decimal]:
        return self.source_atom.coordinates_angstrom


@dataclass(frozen=True, slots=True)
class RrAtomExclusionV1:
    source_atom: RrNativeAtomV1
    reason: str


@dataclass(frozen=True, slots=True)
class RrSidechainConstructionV1:
    chain: str
    author_position: int
    source_component: str
    required_component: str
    purpose: str
    retained_source_ids: tuple[str, ...]
    removed_source_ids: tuple[str, ...]
    required_new_heavy_atoms: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class RrHeavyScaffoldV1:
    """Six-context precursor with actual removals, never completed mutant atoms."""

    source: RrNativeSourceV1 = field(repr=False)
    reference_choice: str
    variant: str
    atoms: tuple[RrProjectedAtomV1, ...] = field(init=False, repr=False)
    omitted_atoms: tuple[RrAtomExclusionV1, ...] = field(init=False, repr=False)
    removed_atoms: tuple[RrAtomExclusionV1, ...] = field(init=False, repr=False)
    sidechain_constructions: tuple[RrSidechainConstructionV1, ...] = field(init=False)
    renamed_source_ids: tuple[str, ...] = field(init=False)
    outside_boundary_polymer_positions: tuple[tuple[str, int], ...] = field(init=False)
    protein_residues: int = field(init=False, default=916)
    later_context_roster: tuple[tuple[str, str], ...] = field(init=False, default=LATER_CONTEXT_ROSTER)
    completed_qm_contexts: int = field(init=False, default=0)
    inferred_quantum_region_charge: None = field(init=False, default=None)
    inferred_spin: None = field(init=False, default=None)
    added_atom_coordinates: tuple[()] = field(init=False, default=())
    CLAIM_SCOPE: ClassVar[str] = "DEVELOPMENT_HEAVY_SCAFFOLD_ATOM_COMPLETION_REQUIRED"

    def __post_init__(self) -> None:
        if (type(self.source) is not RrNativeSourceV1 or type(self.reference_choice) is not str
                or type(self.variant) is not str or self.reference_choice not in REFERENCE_CHOICES
                or self.variant not in VARIANTS):
            raise ValueError("Rr scaffold source/reference/variant selection differs")
        templates = {comp: dict(rows) for comp, rows in self.source.heavy_atom_templates}
        replacements: dict[int, tuple[str, str]] = {}
        if self.reference_choice == "modeled-H91":
            replacements[91] = ("HIS", "modeled-reference-H91-requires-construction")
        if self.variant == "D263N":
            replacements[263] = ("ASN", "D263N-sidechain-requires-construction")
        elif self.variant == "H287N":
            replacements[287] = ("ASN", "H287N-sidechain-requires-construction")
        constructions = []
        for chain in ("A", "B"):
            for position, (target, purpose) in sorted(replacements.items()):
                original = tuple(a for a in self.source.atoms if a.author_chain == chain
                                 and a.author_position == position and a.token("label_entity_id") == "1")
                retained = tuple(a for a in original if a.atom_name in BACKBONE_AND_CB and a.occupancy == 1)
                if {a.atom_name for a in retained} != BACKBONE_AND_CB:
                    raise ValueError("required positive-occupancy backbone/CB mapping incomplete")
                removed = tuple(a for a in original if a.atom_name not in BACKBONE_AND_CB)
                required = tuple(sorted((name, element) for name, element in templates[target].items()
                                        if name not in BACKBONE_AND_CB))
                constructions.append(RrSidechainConstructionV1(
                    chain, position, original[0].component, target, purpose,
                    tuple(a.source_id for a in retained), tuple(a.source_id for a in removed), required,
                ))
        projected = []
        omitted = []
        removed = []
        for atom in self.source.atoms:
            if atom.occupancy == 0:
                omitted.append(RrAtomExclusionV1(atom, "native-zero-occupancy"))
                continue
            comp, name, position = atom.component, atom.atom_name, atom.author_position
            if atom.token("label_entity_id") == "1":
                if not COMMON_AUTHOR_INTERVAL[0] <= position <= COMMON_AUTHOR_INTERVAL[1]:
                    omitted.append(RrAtomExclusionV1(atom, "outside-common-author-interval-2-through-459"))
                    continue
                if position in replacements:
                    if name not in BACKBONE_AND_CB:
                        removed.append(RrAtomExclusionV1(atom, replacements[position][1]))
                        continue
                    comp = replacements[position][0]
                if position == 191:
                    comp = "KCX"
            elif comp == "FMT":
                comp, position, name = "KCX", 191, {"C": "CX", "O1": "OQ1", "O2": "OQ2"}[name]
            elif comp == "RUB":
                position = 600
            elif comp == "MG":
                position = 601
            else:
                raise ValueError("unmapped native scaffold component")
            projected.append(RrProjectedAtomV1(atom, atom.author_chain, position, comp, name))
        identities = {(a.chain, a.author_position, a.component, a.atom_name) for a in projected}
        if len(identities) != len(projected):
            raise ValueError("projected heavy-atom mapping is not unique")
        polymer = {(a.chain, a.author_position) for a in projected if 2 <= a.author_position <= 459}
        if polymer != {(c, n) for c in ("A", "B") for n in range(2, 460)}:
            raise ValueError("common inherited protein interval is incomplete")
        partition = [a.source_atom.source_id for a in projected]
        partition += [a.source_atom.source_id for a in omitted + removed]
        if len(partition) != len(self.source.atoms) or len(set(partition)) != len(partition):
            raise ValueError("source retained/removed/omitted partition is incomplete")
        renamed = tuple(a.source_atom.source_id for a in projected
                        if (a.author_position, a.component, a.atom_name) != (
                            a.source_atom.author_position, a.source_atom.component, a.source_atom.atom_name))
        object.__setattr__(self, "atoms", tuple(projected))
        object.__setattr__(self, "omitted_atoms", tuple(omitted))
        object.__setattr__(self, "removed_atoms", tuple(removed))
        object.__setattr__(self, "sidechain_constructions", tuple(constructions))
        object.__setattr__(self, "renamed_source_ids", renamed)
        object.__setattr__(self, "outside_boundary_polymer_positions", tuple(
            (c, n) for c in ("A", "B") for n in range(1, 467) if not 2 <= n <= 459
        ))

    @property
    def exact_assay_parent_admitted(self) -> bool:
        return False

    @property
    def missing_preparation_operations(self) -> tuple[str, ...]:
        return (
            "exact-assay-parent-and-tag-join-or-explicit-reference-applicability-limit",
            "required-sidechain-heavy-atom-construction-and-amide-orientation",
            "hydrogens-and-carbamate-protonation-and-parameterization",
            "declared-water-policy-and-matched-enolate-proton-views",
            "QM-boundary-link-atoms-and-exclusive-embedding-and-charge-spin-inventories",
            "declared-matched-reactive-states-and-geometric-validation-before-energetics",
        )


def project_rr_scaffold(
    source: RrNativeSourceV1, *, reference_choice: str, variant: str,
) -> RrHeavyScaffoldV1:
    """Create the shared heavy precursor; selection always remains explicit."""
    return RrHeavyScaffoldV1(source, reference_choice, variant)
