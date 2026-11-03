# SPDX-License-Identifier: MPL-2.0
"""Exact original keto Amber nonbonded witnesses, not a reactive Hamiltonian.

Only the hash-first source wrapper authenticates the original topology. The
canonical projection records preserve lexical operands and their native order;
standalone record construction supplies no source or scientific authority.
No optional native library, file I/O or effectful process is selected here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
import re
from typing import ClassVar, Iterator

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256


SOURCE_ID = "rubisco-rr.amber-wt-hid91-keto-original"
SOURCE_MEMBER = "WT-HID91/prepared.prmtop"
SOURCE_BYTES = 22365456
SOURCE_SHA256 = "87b5ed6e40ea77afde056312f923fca44f8b6ee164d8dd973e6deb3b79b2b902"
SELECTED_DRY_ATOMS = 13828
CHUNK_MAXIMUM_BYTES = 8 * 1024**2
SOURCE_MAXIMUM_BYTES = 32 * 1024**2
MAXIMUM_CHUNKS = 64
MAXIMUM_ATOMS = 200000
MAXIMUM_TYPES = 256
MAXIMUM_TOKENS = 4000000
MAXIMUM_LINE_BYTES = 1024

_FORMAT = re.compile(r"%FORMAT\(([1-9][0-9]*)\s*([aAiIeEfF])([1-9][0-9]*)(?:\.([0-9]+))?\)\Z")
_INT = re.compile(r"[+-]?[0-9]+\Z")
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[EeDd][+-]?[0-9]+)?\Z")
_FLAG = re.compile(r"[A-Z][A-Z0-9_]*\Z")
_DIHEDRAL_FLAGS = ("DIHEDRALS_INC_HYDROGEN", "DIHEDRALS_WITHOUT_HYDROGEN")
_PARAMETER_FLAGS = (
    "POINTERS", "NONBONDED_PARM_INDEX", "LENNARD_JONES_ACOEF",
    "LENNARD_JONES_BCOEF", "SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR",
)
_REQUIRED_FLAGS = frozenset(_PARAMETER_FLAGS + _DIHEDRAL_FLAGS + (
    "ATOM_NAME", "AMBER_ATOM_TYPE", "ATOM_TYPE_INDEX", "NUMBER_EXCLUDED_ATOMS",
    "EXCLUDED_ATOMS_LIST",
))
_UNSUPPORTED_FLAGS = frozenset((
    "LENNARD_JONES_DCOEF", "LENNARD_JONES_14_ACOEF", "LENNARD_JONES_14_BCOEF",
))


def _integer(token: str) -> int:
    if type(token) is not str or len(token) > 32 or not _INT.fullmatch(token):
        raise ValueError("invalid native integer token")
    return int(token)


def _decimal(token: str) -> Decimal:
    if type(token) is not str or len(token) > 64 or not _NUMBER.fullmatch(token):
        raise ValueError("invalid native Decimal token")
    value = Decimal(token.replace("D", "E").replace("d", "e"))
    if not value.is_finite() or abs(value.as_tuple().exponent) > 1000:
        raise ValueError("nonfinite or overbound native Decimal")
    return value


def _tuple(value: object, label: str) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be an immutable tuple")


def _lines(chunks: tuple[bytes, ...]) -> Iterator[str]:
    """Bound a native line even when a chunk ends within a field or CRLF."""
    pending = b""
    for chunk in chunks:
        start = 0
        while True:
            end = chunk.find(b"\n", start)
            if end < 0:
                pending += chunk[start:]
                if len(pending) > MAXIMUM_LINE_BYTES:
                    raise ValueError("native line byte bound exceeded")
                break
            line = pending + chunk[start:end]
            pending = b""
            if len(line) > MAXIMUM_LINE_BYTES:
                raise ValueError("native line byte bound exceeded")
            try:
                yield line.removesuffix(b"\r").decode("ascii")
            except UnicodeError as exc:
                raise ValueError("native topology must be ASCII") from exc
            start = end + 1
    if pending:
        try:
            yield pending.removesuffix(b"\r").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("native topology must be ASCII") from exc


@dataclass(frozen=True, slots=True)
class AmberNativeFlagV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/amber-native-flag"
    name: str
    native_format: str
    native_tokens: tuple[str, ...]
    native_flag_ordinal_1based: int

    def __post_init__(self) -> None:
        _tuple(self.native_tokens, "native_tokens")
        if type(self.native_flag_ordinal_1based) is not int or not 1 <= self.native_flag_ordinal_1based <= 256:
            raise ValueError("native flag ordinal differs")
        if type(self.name) is not str or not _FLAG.fullmatch(self.name):
            raise ValueError("invalid native flag name")
        match = _FORMAT.fullmatch(self.native_format) if type(self.native_format) is str else None
        if match is None or int(match[1])*int(match[3]) > MAXIMUM_LINE_BYTES:
            raise ValueError("unsupported native fixed-width format")
        kind = match[2].upper()
        for token in self.native_tokens:
            if type(token) is not str or not token or len(token) > int(match[3]):
                raise ValueError("native token width or type differs")
            if kind == "I":
                _integer(token)
            elif kind != "A":
                _decimal(token)


def _read_flags(chunks: tuple[bytes, ...]) -> tuple[AmberNativeFlagV1, ...]:
    """Selected standard Amber fixed-width syntax; no general Fortran reader."""
    parsed = []
    seen = set()
    name = None
    fmt = None
    tokens: list[str] = []
    count = 0
    first = True

    def finish() -> None:
        if name is not None:
            if fmt is None:
                raise ValueError("native flag has no format")
            if name in _REQUIRED_FLAGS or name in _UNSUPPORTED_FLAGS:
                parsed.append(AmberNativeFlagV1(name, fmt, tuple(tokens), len(seen)))

    for line in _lines(chunks):
        if first:
            first = False
            if re.fullmatch(r"%VERSION\s+VERSION_STAMP\s*=\s*V0001\.000(?:\s.*)?", line) is None:
                raise ValueError("unsupported native topology version")
            continue
        if line.startswith("%COMMENT"):
            continue
        if line.startswith("%FLAG "):
            finish()
            name = line[6:].strip()
            if not _FLAG.fullmatch(name) or name in seen:
                raise ValueError("duplicate or invalid native flag")
            seen.add(name)
            if len(seen) > 256:
                raise ValueError("native flag census exceeds bound")
            fmt = None
            tokens = []
            continue
        if line.startswith("%FORMAT"):
            if name is None or fmt is not None:
                raise ValueError("duplicate or orphan native format")
            fmt = line.rstrip()
            if _FORMAT.fullmatch(fmt) is None:
                raise ValueError("unsupported native fixed-width format")
            continue
        if line.startswith("%") or name is None or fmt is None:
            raise ValueError("unexpected native topology control line")
        match = _FORMAT.fullmatch(fmt)
        assert match is not None
        width, per_line = int(match[3]), int(match[1])
        if width*per_line > MAXIMUM_LINE_BYTES or len(line.rstrip()) > width*per_line:
            raise ValueError("native data line exceeds declared format")
        fields = tuple(line[i:i+width].strip() for i in range(0, len(line), width))
        # Native padding may follow the final field, but cannot omit an interior value.
        while fields and not fields[-1]:
            fields = fields[:-1]
        if any(not token for token in fields):
            raise ValueError("blank interior native field")
        count += len(fields)
        if count > MAXIMUM_TOKENS:
            raise ValueError("native token census exceeds bound")
        if name in _REQUIRED_FLAGS or name in _UNSUPPORTED_FLAGS:
            tokens.extend(fields)
    finish()
    if not _REQUIRED_FLAGS.issubset(seen):
        raise ValueError("required original native flags are missing")
    if _UNSUPPORTED_FLAGS.intersection(seen):
        raise ValueError("extended native LJ model is not supported")
    return tuple(parsed)


@dataclass(frozen=True, slots=True)
class AmberAtomNonbondedV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/amber-atom-nonbonded"
    atom_index_1based: int
    native_name: str
    native_amber_type: str
    native_type_index_token: str
    native_exclusion_count_token: str
    native_exclusion_tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.atom_index_1based) is not int or not 1 <= self.atom_index_1based <= MAXIMUM_ATOMS:
            raise ValueError("original atom index differs")
        for value in (self.native_name, self.native_amber_type):
            if type(value) is not str or not 1 <= len(value) <= 4 or not value.isascii() or any(v.isspace() for v in value):
                raise ValueError("original native atom name/type differs")
        if not 1 <= _integer(self.native_type_index_token) <= MAXIMUM_TYPES:
            raise ValueError("original atom type index differs")
        _tuple(self.native_exclusion_tokens, "native_exclusion_tokens")
        if _integer(self.native_exclusion_count_token) != len(self.native_exclusion_tokens):
            raise ValueError("original exclusion count differs")
        for token in self.native_exclusion_tokens:
            if not 0 <= _integer(token) <= MAXIMUM_ATOMS:
                raise ValueError("original exclusion atom index differs")

    @property
    def type_index_1based(self) -> int:
        return int(self.native_type_index_token)


@dataclass(frozen=True, slots=True)
class AmberDihedral14V1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/amber-original-dihedral-14"
    native_flag: str
    native_row_1based: int
    native_tokens: tuple[str, str, str, str, str]
    native_scee_token: str
    native_scnb_token: str

    def __post_init__(self) -> None:
        _tuple(self.native_tokens, "native_tokens")
        if self.native_flag not in _DIHEDRAL_FLAGS or type(self.native_row_1based) is not int or self.native_row_1based < 1 or len(self.native_tokens) != 5:
            raise ValueError("native dihedral row identity differs")
        indices = tuple(_integer(token) for token in self.native_tokens)
        if any(abs(v) % 3 or abs(v)//3 >= MAXIMUM_ATOMS for v in indices[:4]) or any(v < 0 for v in indices[:2]) or indices[4] < 1:
            raise ValueError("native signed dihedral indices differ")
        scales = (_decimal(self.native_scee_token), _decimal(self.native_scnb_token))
        if any(value < 0 for value in scales):
            raise ValueError("native 1-4 scaling divisors must be nonnegative")
        # Native Amber permits explicit zero scales on ignored/improper rows.
        # These are source witnesses, not denominators for an active 1-4 pair.
        if self.source_14_enabled and any(value == 0 for value in scales):
            raise ValueError("native 1-4 scaling divisors must be positive")

    @property
    def atom_indices_1based(self) -> tuple[int, int, int, int]:
        return tuple(abs(int(v))//3+1 for v in self.native_tokens[:4])  # type: ignore[return-value]

    @property
    def is_improper(self) -> bool:
        return int(self.native_tokens[3]) < 0

    @property
    def source_14_enabled(self) -> bool:
        # Match standard Amber/OpenMM handling: both ignore-end and improper flags matter.
        return int(self.native_tokens[2]) >= 0 and not self.is_improper

    @property
    def electrostatic_divisor(self) -> Decimal:
        return _decimal(self.native_scee_token)

    @property
    def vdw_divisor(self) -> Decimal:
        return _decimal(self.native_scnb_token)


@dataclass(frozen=True, slots=True)
class AmberOriginalLJPairV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/amber-original-lj-pair"
    first_atom_1based: int
    second_atom_1based: int
    parameter_index_1based: int
    native_a_token: str
    native_b_token: str
    source_excluded: bool

    def __post_init__(self) -> None:
        if any(type(v) is not int or not 1 <= v <= MAXIMUM_ATOMS for v in (self.first_atom_1based, self.second_atom_1based)) or type(self.parameter_index_1based) is not int or self.parameter_index_1based < 1 or type(self.source_excluded) is not bool:
            raise ValueError("original LJ pair identity differs")
        if _decimal(self.native_a_token) < 0 or _decimal(self.native_b_token) < 0:
            raise ValueError("negative original LJ coefficient")

    @property
    def a_kcal_mol_angstrom12(self) -> Decimal:
        return _decimal(self.native_a_token)

    @property
    def b_kcal_mol_angstrom6(self) -> Decimal:
        return _decimal(self.native_b_token)


@dataclass(frozen=True, slots=True)
class AmberKetoNonbondedProjectionV1(CanonicalRecord):
    """Source-shaped witnesses. Source authentication requires the wrapper below."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/amber-keto-nonbonded-projection"
    source_id: str
    source_member: str
    source_sha256: str
    source_bytes: int
    full_atom_count: int
    type_count: int
    full_exclusion_token_count: int
    full_dihedral_counts: tuple[int, int]
    parameter_flags: tuple[AmberNativeFlagV1, ...]
    selected_atoms: tuple[AmberAtomNonbondedV1, ...]
    selected_dihedrals: tuple[AmberDihedral14V1, ...]

    def __post_init__(self) -> None:
        if self.source_id != SOURCE_ID or self.source_member != SOURCE_MEMBER:
            raise ValueError("original keto source role differs")
        validate_sha256(self.source_sha256)
        if type(self.source_bytes) is not int or not 1 <= self.source_bytes <= SOURCE_MAXIMUM_BYTES or type(self.full_atom_count) is not int or not 1 <= self.full_atom_count <= MAXIMUM_ATOMS or type(self.type_count) is not int or not 1 <= self.type_count <= MAXIMUM_TYPES:
            raise ValueError("original source count or byte bound differs")
        for value, name in ((self.parameter_flags, "parameter_flags"), (self.selected_atoms, "selected_atoms"), (self.selected_dihedrals, "selected_dihedrals"), (self.full_dihedral_counts, "full_dihedral_counts")):
            _tuple(value, name)
        if len(self.full_dihedral_counts) != 2 or any(type(v) is not int or not 0 <= v <= MAXIMUM_TOKENS//5 for v in self.full_dihedral_counts) or type(self.full_exclusion_token_count) is not int or not 0 <= self.full_exclusion_token_count <= MAXIMUM_TOKENS:
            raise ValueError("original full census differs")
        if any(type(v) is not AmberNativeFlagV1 for v in self.parameter_flags) or tuple(v.name for v in self.parameter_flags) != _PARAMETER_FLAGS:
            raise ValueError("original parameter flag census differs")
        if len({v.native_flag_ordinal_1based for v in self.parameter_flags}) != len(self.parameter_flags):
            raise ValueError("original native flag ordinals differ")
        if not self.selected_atoms or any(type(v) is not AmberAtomNonbondedV1 for v in self.selected_atoms) or tuple(v.atom_index_1based for v in self.selected_atoms) != tuple(range(1, len(self.selected_atoms)+1)) or len(self.selected_atoms) > self.full_atom_count:
            raise ValueError("selected original atom roster differs")
        pointers = tuple(_integer(v) for v in self.flag("POINTERS").native_tokens)
        if len(pointers) < 31 or pointers[0] != self.full_atom_count or pointers[1] != self.type_count or pointers[10] != self.full_exclusion_token_count or (pointers[6], pointers[14]) != self.full_dihedral_counts:
            raise ValueError("original POINTERS census mismatch")
        pair_count = self.type_count*(self.type_count+1)//2
        indices = tuple(_integer(v) for v in self.flag("NONBONDED_PARM_INDEX").native_tokens)
        if len(indices) != self.type_count**2 or any(v <= 0 for v in indices):
            raise ValueError("unsupported 10-12 or absent native LJ index")
        if any(v > pair_count for v in indices) or any(indices[self.type_count*i+j] != indices[self.type_count*j+i] for i in range(self.type_count) for j in range(i)):
            raise ValueError("asymmetric or out-of-range native LJ table")
        for name in ("LENNARD_JONES_ACOEF", "LENNARD_JONES_BCOEF"):
            tokens = self.flag(name).native_tokens
            if len(tokens) != pair_count or any(_decimal(v) < 0 for v in tokens):
                raise ValueError("original LJ coefficient census differs")
        nptra = pointers[17]
        for name in ("SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR"):
            tokens = self.flag(name).native_tokens
            if len(tokens) != nptra or any(_decimal(v) < 0 for v in tokens):
                raise ValueError("explicit original 1-4 scale census differs")
        if any(a.type_index_1based > self.type_count or any(int(v) > self.full_atom_count for v in a.native_exclusion_tokens) for a in self.selected_atoms):
            raise ValueError("original selected atom index exceeds source")
        for row in self.selected_dihedrals:
            if type(row) is not AmberDihedral14V1 or max(row.atom_indices_1based) > len(self.selected_atoms):
                raise ValueError("selected original dihedral membership differs")
            parameter = int(row.native_tokens[4])
            if parameter > nptra or row.native_scee_token != self.flag("SCEE_SCALE_FACTOR").native_tokens[parameter-1] or row.native_scnb_token != self.flag("SCNB_SCALE_FACTOR").native_tokens[parameter-1]:
                raise ValueError("original dihedral parameter join differs")
        identities = tuple((_DIHEDRAL_FLAGS.index(d.native_flag), d.native_row_1based) for d in self.selected_dihedrals)
        if tuple(sorted(set(identities))) != identities or any(row > self.full_dihedral_counts[flag] for flag, row in identities):
            raise ValueError("native selected dihedral order or denominator differs")

    def flag(self, name: str) -> AmberNativeFlagV1:
        return next(v for v in self.parameter_flags if v.name == name)

    @property
    def native_parameter_flag_order(self) -> tuple[AmberNativeFlagV1, ...]:
        return tuple(sorted(self.parameter_flags, key=lambda v: v.native_flag_ordinal_1based))

    @property
    def selected_dihedral_counts(self) -> tuple[int, int]:
        return tuple(sum(v.native_flag == name for v in self.selected_dihedrals) for name in _DIHEDRAL_FLAGS)  # type: ignore[return-value]

    @property
    def omitted_dihedral_counts(self) -> tuple[int, int]:
        return tuple(a-b for a, b in zip(self.full_dihedral_counts, self.selected_dihedral_counts, strict=True))  # type: ignore[return-value]

    @property
    def source_14_terms(self) -> tuple[AmberDihedral14V1, ...]:
        """Keep native row order and multiplicity; never silently deduplicate pairs."""
        return tuple(d for d in self.selected_dihedrals if d.source_14_enabled)

    def original_lj_pair(self, first: int, second: int) -> AmberOriginalLJPairV1:
        if any(type(v) is not int or not 1 <= v <= len(self.selected_atoms) for v in (first, second)):
            raise ValueError("original LJ query is outside selected native atoms")
        a, b = self.selected_atoms[first-1], self.selected_atoms[second-1]
        pointer = int(self.flag("NONBONDED_PARM_INDEX").native_tokens[self.type_count*(a.type_index_1based-1)+b.type_index_1based-1])
        excluded = str(second) in a.native_exclusion_tokens or str(first) in b.native_exclusion_tokens
        # Compare numerical native indices; lexical +/leading-zero spelling remains retained.
        excluded = excluded or second in tuple(map(int, a.native_exclusion_tokens)) or first in tuple(map(int, b.native_exclusion_tokens))
        return AmberOriginalLJPairV1(first, second, pointer, self.flag("LENNARD_JONES_ACOEF").native_tokens[pointer-1], self.flag("LENNARD_JONES_BCOEF").native_tokens[pointer-1], excluded)


def _project(chunks: tuple[bytes, ...], digest: str, byte_count: int, selected_count: int) -> AmberKetoNonbondedProjectionV1:
    flags = {v.name: v for v in _read_flags(chunks)}
    pointers = tuple(_integer(v) for v in flags["POINTERS"].native_tokens)
    if len(pointers) < 31 or any(v < 0 for v in pointers):
        raise ValueError("native POINTERS shape differs")
    natom, ntypes = pointers[:2]
    if not 1 <= natom <= MAXIMUM_ATOMS or not 1 <= ntypes <= MAXIMUM_TYPES or type(selected_count) is not int or not 1 <= selected_count <= natom:
        raise ValueError("original atom/type/selection bound differs")
    for name in ("SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR"):
        if len(flags[name].native_tokens) != pointers[17]:
            raise ValueError("explicit original 1-4 scale census differs")
    for name in ("ATOM_NAME", "AMBER_ATOM_TYPE", "ATOM_TYPE_INDEX", "NUMBER_EXCLUDED_ATOMS"):
        if len(flags[name].native_tokens) != natom:
            raise ValueError("full native atom-array census differs")
    counts = tuple(_integer(v) for v in flags["NUMBER_EXCLUDED_ATOMS"].native_tokens)
    exclusions = flags["EXCLUDED_ATOMS_LIST"].native_tokens
    if any(v < 0 for v in counts) or sum(counts) != len(exclusions) or len(exclusions) != pointers[10]:
        raise ValueError("full native exclusion census differs")
    if any(not 0 <= _integer(v) <= natom for v in exclusions) or any(not 1 <= _integer(v) <= ntypes for v in flags["ATOM_TYPE_INDEX"].native_tokens):
        raise ValueError("full native atom/exclusion index differs")
    selected_atoms = []
    offset = 0
    for i in range(selected_count):
        selected_atoms.append(AmberAtomNonbondedV1(i+1, flags["ATOM_NAME"].native_tokens[i], flags["AMBER_ATOM_TYPE"].native_tokens[i], flags["ATOM_TYPE_INDEX"].native_tokens[i], flags["NUMBER_EXCLUDED_ATOMS"].native_tokens[i], exclusions[offset:offset+counts[i]]))
        offset += counts[i]
    selected_dihedrals = []
    for name, count in zip(_DIHEDRAL_FLAGS, (pointers[6], pointers[14]), strict=True):
        tokens = flags[name].native_tokens
        if len(tokens) != count*5:
            raise ValueError("full native dihedral census differs")
        for i in range(count):
            row = tokens[i*5:i*5+5]
            parameter = _integer(row[4])
            if not 1 <= parameter <= pointers[17]:
                raise ValueError("full native dihedral parameter index differs")
            record = AmberDihedral14V1(name, i+1, row, flags["SCEE_SCALE_FACTOR"].native_tokens[parameter-1], flags["SCNB_SCALE_FACTOR"].native_tokens[parameter-1])
            if max(record.atom_indices_1based) > natom:
                raise ValueError("full native dihedral atom index differs")
            if max(record.atom_indices_1based) <= selected_count:
                selected_dihedrals.append(record)
    return AmberKetoNonbondedProjectionV1(SOURCE_ID, SOURCE_MEMBER, digest, byte_count, natom, ntypes, len(exclusions), (pointers[6], pointers[14]), tuple(flags[n] for n in _PARAMETER_FLAGS), tuple(selected_atoms), tuple(selected_dihedrals))


@dataclass(frozen=True, slots=True)
class RrAmberNonbondedSourceV1:
    """All projection fields derive from exact ordered authentic source chunks."""

    original_chunks: tuple[bytes, ...] = field(repr=False)
    projection: AmberKetoNonbondedProjectionV1 = field(init=False)
    chunk_bindings: tuple[tuple[int, int, str], ...] = field(init=False)
    CLAIM_SCOPE: ClassVar[str] = "ORIGINAL_KETO_SOURCE_ONLY_NOT_REACTIVE_TOPOLOGY_OR_MM_HAMILTONIAN"

    def __post_init__(self) -> None:
        _tuple(self.original_chunks, "original_chunks")
        if not 1 <= len(self.original_chunks) <= MAXIMUM_CHUNKS or any(type(v) is not bytes or not 1 <= len(v) <= CHUNK_MAXIMUM_BYTES for v in self.original_chunks):
            raise ValueError("original source chunk byte bound or type differs")
        count = sum(map(len, self.original_chunks))
        if count > SOURCE_MAXIMUM_BYTES:
            raise ValueError("original source total byte bound exceeded")
        digest = sha256()
        for chunk in self.original_chunks:
            digest.update(chunk)
        if count != SOURCE_BYTES or digest.hexdigest() != SOURCE_SHA256:
            raise ValueError("original keto topology bytes differ before parsing")
        object.__setattr__(self, "chunk_bindings", tuple((i+1, len(v), sha256(v).hexdigest()) for i, v in enumerate(self.original_chunks)))
        object.__setattr__(self, "projection", _project(self.original_chunks, SOURCE_SHA256, count, SELECTED_DRY_ATOMS))


def decode_rr_amber_nonbonded(original_chunks: tuple[bytes, ...]) -> RrAmberNonbondedSourceV1:
    """Authenticate ordered bounded chunks before any native-format interpretation."""
    return RrAmberNonbondedSourceV1(original_chunks)
