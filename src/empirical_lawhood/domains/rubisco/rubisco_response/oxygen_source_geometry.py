# SPDX-License-Identifier: MPL-2.0
"""A new text extraction of the exact original oxygen SI, without job admission.

The original reviewed JSON and its custody are not reconstructed. Every atom
token is independently matched to the maintained source geometry pins.
"""

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.domains.rubisco.kinetics.fm23_preparation import GEOMETRY_PINS, GeometryAtomV1, PDF_BYTES, PDF_SHA256, native_atom_projection_sha256
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256


_ATOM = re.compile(r"(C|H|N|O|P|Mg)\s+([-+]?\d+\.\d+)\s+([-+]?\d+\.\d+)\s+([-+]?\d+\.\d+)\Z")
_PATHWAYS = {row[0] for row in GEOMETRY_PINS}
_ROLE = "NEW_EXACT_SI_TEXT_EXTRACTION_NOT_RECOVERED_REVIEWED_JSON_OR_ELECTRONIC_JOB"


@dataclass(frozen=True, slots=True)
class OxygenSourceGeometry(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/oxygen-source-geometry'
    ordinal: int
    native_pathway: str
    native_state_label: str
    atoms: tuple[GeometryAtomV1, ...]

    def __post_init__(self):
        if type(self.ordinal) is not int or not 1 <= self.ordinal <= len(GEOMETRY_PINS):
            raise ValueError('oxygen source requires its original geometry ordinal')
        pathway, label, count, digest = GEOMETRY_PINS[self.ordinal-1]
        if (type(self.atoms) is not tuple or any(type(a) is not GeometryAtomV1 for a in self.atoms)
                or (self.native_pathway, self.native_state_label, len(self.atoms)) != (pathway, label, count)
                or native_atom_projection_sha256(self.atoms) != digest):
            raise ValueError('oxygen geometry changes original metadata, atom count or exact native tokens')


@dataclass(frozen=True, slots=True)
class OxygenSourceProjection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/oxygen-source-projection'
    geometries: tuple[OxygenSourceGeometry, ...]
    extracted_text_sha256: str
    extracted_text_bytes: int
    original_pdf_sha256: str = PDF_SHA256
    original_pdf_bytes: int = PDF_BYTES
    role: str = _ROLE

    def __post_init__(self):
        validate_sha256(self.extracted_text_sha256)
        if (type(self.geometries) is not tuple
                or any(type(g) is not OxygenSourceGeometry for g in self.geometries)
                or tuple(g.ordinal for g in self.geometries) != tuple(range(1, 25))
                or sum(len(g.atoms) for g in self.geometries) != 5994
                or type(self.extracted_text_bytes) is not int or not 0 < self.extracted_text_bytes <= 2**20
                or (self.original_pdf_sha256, self.original_pdf_bytes, self.role) != (PDF_SHA256, PDF_BYTES, _ROLE)):
            raise ValueError('oxygen projection loses its exact original witness or complete source census')
        for geometry in self.geometries:
            geometry.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record('oxygen-source-projection.'+self.fingerprint(), self)


def _read_geometry_blocks(text):
    """Read the plain text grammar; source-specific token admission is separate."""
    lines = [line.strip() for line in text.splitlines()]
    if lines.count('Optimized coordinates') != 1:
        raise ValueError('oxygen text requires exactly one original coordinate section')
    lines = lines[lines.index('Optimized coordinates')+1:]
    pathway, result, index = None, [], 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line or re.fullmatch(r'S\d+', line):
            continue
        if line in _PATHWAYS:
            pathway = line
            continue
        if not line.isdigit() or pathway is None:
            raise ValueError('unexpected text in the original oxygen coordinate census')
        count = int(line)
        if not 1 <= count <= 512 or index >= len(lines):
            raise ValueError('oxygen geometry has an invalid atom denominator')
        label = lines[index]
        index += 1
        atoms = []
        while len(atoms) < count and index < len(lines):
            atom = lines[index]
            index += 1
            if not atom or re.fullmatch(r'S\d+', atom):
                continue
            matched = _ATOM.fullmatch(atom)
            if matched is None:
                raise ValueError('oxygen geometry contains an invalid or missing original atom row')
            element, *tokens = matched.groups()
            atoms.append(GeometryAtomV1(element, tuple(tokens)))
        if len(atoms) != count:
            raise ValueError('oxygen geometry is truncated')
        result.append((pathway, label, tuple(atoms)))
        if len(result) > 24:
            raise ValueError('oxygen text adds an unassigned geometry')
    return tuple(result)


def prepare_oxygen_source_projection(*, original_pdf_bytes, extracted_text_bytes):
    """Bind exact original bytes and all 24 independently pinned atom projections.

    Text extraction is explicit external preparation, not a native XYZ release.
    This function does not invoke a parser, download a source, or admit states.
    """
    if (type(original_pdf_bytes) is not bytes or len(original_pdf_bytes) != PDF_BYTES
            or sha256(original_pdf_bytes).hexdigest() != PDF_SHA256):
        raise ValueError('oxygen source differs from the exact original SI PDF')
    if type(extracted_text_bytes) is not bytes or not 0 < len(extracted_text_bytes) <= 2**20:
        raise ValueError('select bounded original text-extraction bytes')
    text = extracted_text_bytes.decode('utf-8', errors='strict')
    rows = _read_geometry_blocks(text)
    geometries = tuple(OxygenSourceGeometry(i, pathway, label, atoms)
        for i, (pathway, label, atoms) in enumerate(rows, 1))
    return OxygenSourceProjection(geometries, sha256(extracted_text_bytes).hexdigest(), len(extracted_text_bytes))
