"""Narrow lossless MG000148.1 parent-CDS inspection and translation checks.

This reads an explicitly supplied deposited Te parent insert. It neither
authenticates a physical assay plasmid nor designs or invents mutant DNA.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256

MG000148_SOURCE_SHA256 = "62f8c50c51ba007b4d6b99273b9c397ceea85d97985449f6c0bcef376e51b305"
MAX_GENBANK_BYTES = 128 * 1024
MAX_LINES = 2000

# NCBI translation table 11 has the standard internal codon mapping. This
# selected source has ATG initiation, codon_start=1 and an explicit terminal
# stop in each uninterrupted CDS; alternate initiation is outside this profile.
_BASES = "TCAG"
_AMINO_ACIDS = (
    "FFLLSSSSYY**CC*W"
    "LLLLPPPPHHQQRRRR"
    "IIIMTTTTNNKKSSRR"
    "VVVVAAAADDEEGGGG"
)
_CODON_TABLE = {a + b + c: aa for (a, b, c), aa in zip(
    ((a, b, c) for a in _BASES for b in _BASES for c in _BASES), _AMINO_ACIDS, strict=True
)}


def _translate_complete_cds(dna: str) -> str:
    if len(dna) % 3 or not dna.startswith("ATG") or not re.fullmatch(r"[ACGT]+", dna):
        raise ValueError("selected source CDS must be complete ATG-initiated table-11 DNA")
    protein = "".join(_CODON_TABLE[dna[i:i+3]] for i in range(0, len(dna), 3))
    if not protein.endswith("*") or "*" in protein[:-1]:
        raise ValueError("selected source CDS must have exactly one terminal stop")
    return protein[:-1]


@dataclass(frozen=True, slots=True)
class NativeTeCDSV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-te-cds"
    gene: str
    native_location: str
    start_1based: int
    end_1based: int
    protein_accession: str
    protein_sequence: str
    native_feature_lines: tuple[str, ...]
    qualifiers: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        expected = {"rbcL": (1, 1428, "ATN39932.1", 475), "rbcS": (1494, 1850, "ATN39933.1", 118)}
        if self.gene not in expected or (self.start_1based, self.end_1based, self.protein_accession,
                                        len(self.protein_sequence)) != expected[self.gene]:
            raise ValueError("selected MG000148 CDS identity, boundaries or protein length differ")
        if self.native_location != f"{self.start_1based}..{self.end_1based}" or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", self.protein_sequence):
            raise ValueError("selected source CDS location/alphabet differs")
        if not self.native_feature_lines or self.native_feature_lines[0][21:].strip() != self.native_location:
            raise ValueError("CDS location differs from its retained native feature line")
        if self.qualifiers != tuple(sorted(self.qualifiers)) or len(dict(self.qualifiers)) != len(self.qualifiers):
            raise ValueError("CDS qualifiers must retain one unique order")
        fields = dict(self.qualifiers)
        if (fields.get("gene") != self.gene or fields.get("protein_id") != self.protein_accession
                or fields.get("translation") != self.protein_sequence or fields.get("codon_start") != "1"
                or fields.get("transl_table") != "11"):
            raise ValueError("CDS projection differs from exact native qualifiers")
        if _qualifiers(self.native_feature_lines) != self.qualifiers:
            raise ValueError("CDS qualifiers differ from retained native feature lines")


@dataclass(frozen=True, slots=True)
class NativeTeParentConstructV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-te-parent-construct"
    source_sha256: str
    accession_version: str
    native_header_lines: tuple[str, ...]
    native_origin_lines: tuple[str, ...]
    dna_sequence: str
    cds: tuple[NativeTeCDSV1, ...]
    custody_scope: str = "DEPOSITED_PARENT_INSERT_NOT_COMPLETE_ASSAY_PLASMID_AUTHENTICATION"

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256)
        if self.accession_version != "MG000148.1" or len(self.dna_sequence) != 1850 or not re.fullmatch(r"[ACGT]+", self.dna_sequence):
            raise ValueError("selected deposited parent accession/sequence dimensions differ")
        if tuple(c.gene for c in self.cds) != ("rbcL", "rbcS"):
            raise ValueError("selected parent requires both native LSU and SSU CDS records")
        if not self.native_header_lines or self.native_header_lines[0].split()[:4] != ["LOCUS", "MG000148", "1850", "bp"] or [
            line.split()[1] for line in self.native_header_lines if line.startswith("VERSION ")
        ] != ["MG000148.1"]:
            raise ValueError("deposited parent header differs from its native accession/length")
        if self.dna_sequence != _origin(self.native_origin_lines):
            raise ValueError("parent DNA differs from its retained native origin lines")
        for c in self.cds:
            dna = self.dna_sequence[c.start_1based - 1:c.end_1based]
            if _translate_complete_cds(dna) != c.protein_sequence:
                raise ValueError("native DNA translation differs from the reported protein qualifier")
        if self.custody_scope != "DEPOSITED_PARENT_INSERT_NOT_COMPLETE_ASSAY_PLASMID_AUTHENTICATION":
            raise ValueError("deposited sequence does not authenticate an experimental preparation")

    def coding_sequence(self, gene: str) -> NativeTeCDSV1:
        matches = [c for c in self.cds if c.gene == gene]
        if len(matches) != 1:
            raise ValueError("required parent CDS is not admitted exactly once")
        return matches[0]


def _qualifiers(lines: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    if not lines or not re.fullmatch(r"     CDS\s+[0-9]+\.\.[0-9]+", lines[0]):
        raise ValueError("selected feature is not a simple complete native CDS")
    fields = {}
    key = None
    fragments = []
    quoted = False
    for line in lines[1:]:
        value = line[21:]
        if value.startswith("/"):
            if key is not None:
                raise ValueError("native qualifier has an unterminated quoted value")
            match = re.fullmatch(r"/([a-z_]+)=(.*)", value)
            if match is None or match[1] in fields:
                raise ValueError("native CDS qualifier is unsupported or duplicated")
            key = match[1]
            initial = match[2]
            quoted = initial.startswith('"')
            fragments = [initial[1:] if quoted else initial]
        elif key is not None and quoted:
            fragments.append(value)
        else:
            raise ValueError("native CDS qualifier continuation is ambiguous")
        if not quoted or fragments[-1].endswith('"'):
            if quoted:
                fragments[-1] = fragments[-1][:-1]
            separator = "" if key == "translation" else " "
            joined = separator.join(f.strip() for f in fragments)
            if len(joined.encode()) > 8192:
                raise ValueError("native qualifier exceeds its text bound")
            fields[key] = joined
            key = None
    if key is not None:
        raise ValueError("native qualifier has an unterminated quoted value")
    return tuple(sorted(fields.items()))


def _origin(lines: tuple[str, ...]) -> str:
    fragments = []
    expected_position = 1
    for line in lines:
        match = re.fullmatch(r"\s*([1-9][0-9]*)\s+([acgtACGT ]+)", line)
        if match is None or int(match[1]) != expected_position:
            raise ValueError("native ORIGIN line numbering/alphabet differs")
        bases = match[2].replace(" ", "").upper()
        if not bases:
            raise ValueError("native ORIGIN line has no sequence")
        expected_position += len(bases)
        fragments.append(bases)
    return "".join(fragments)


def decode_te_parent_genbank(payload: bytes, *, expected_sha256: str) -> NativeTeParentConstructV1:
    """Hash-first decode of this exact source profile, with no file/network I/O."""
    validate_sha256(expected_sha256)
    if not 1 <= len(payload) <= MAX_GENBANK_BYTES or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("GenBank source exceeds its byte bound or differs from exact custody")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("selected GenBank source must be UTF-8") from error
    lines = text.splitlines()
    if len(lines) > MAX_LINES or any(len(line.encode()) > 8192 or "\x00" in line for line in lines):
        raise ValueError("selected GenBank source exceeds its line/text bounds")
    terminators = [i for i, line in enumerate(lines) if line == "//"]
    if (len([l for l in lines if l.startswith("LOCUS ")]) != 1
            or [l.split()[1] for l in lines if l.startswith("VERSION ")] != ["MG000148.1"]
            or [l.split()[1] for l in lines if l.startswith("ACCESSION ")] != ["MG000148"]
            or len(terminators) != 1 or any(line.strip() for line in lines[terminators[0] + 1:])):
        raise ValueError("selected GenBank record accession/version/terminator differs")
    locus = lines[0].split()
    if locus[:4] != ["LOCUS", "MG000148", "1850", "bp"]:
        raise ValueError("selected GenBank LOCUS differs from the complete parent insert")
    feature_positions = [i for i, line in enumerate(lines) if line.startswith("FEATURES ")]
    origins = [i for i, line in enumerate(lines) if line.startswith("ORIGIN")]
    if len(feature_positions) != 1 or len(origins) != 1 or not feature_positions[0] < origins[0] < terminators[0]:
        raise ValueError("selected GenBank feature/origin sections are ambiguous")
    cds = []
    feature_lines = lines[feature_positions[0] + 1:origins[0]]
    starts = [i for i, line in enumerate(feature_lines) if re.match(r"^     [A-Za-z]", line)]
    for i, start in enumerate(starts):
        block = tuple(feature_lines[start:starts[i+1] if i + 1 < len(starts) else len(feature_lines)])
        if not block[0].startswith("     CDS "):
            continue
        location = block[0][21:].strip()
        match = re.fullmatch(r"([1-9][0-9]*)\.\.([1-9][0-9]*)", location)
        if match is None:
            raise ValueError("selected parent has an unsupported split/complement CDS location")
        qualifiers = _qualifiers(block)
        fields = dict(qualifiers)
        cds.append(NativeTeCDSV1(fields.get("gene", ""), location, int(match[1]), int(match[2]),
            fields.get("protein_id", ""), fields.get("translation", ""), block, qualifiers))
    return NativeTeParentConstructV1(expected_sha256, "MG000148.1", tuple(lines[:feature_positions[0]]),
        tuple(lines[origins[0] + 1:terminators[0]]), _origin(tuple(lines[origins[0] + 1:terminators[0]])), tuple(cds))
