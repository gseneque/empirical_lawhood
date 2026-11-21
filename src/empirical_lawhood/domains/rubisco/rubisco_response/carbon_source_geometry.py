# SPDX-License-Identifier: MPL-2.0
"""Exact released carbon geometries and their original PDB correspondence.

Native R/TS/P are ordered for decarboxylation. The source product's literal
M1 element token survives; its separate Mg interpretation needs the original
PDB witness. No foreign electronic energy or protonation state is transferred.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from typing import ClassVar
from urllib.parse import quote
from zipfile import ZipFile

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.domains.rubisco.kinetics.fm23_preparation import GeometryAtomV1
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


ARCHIVE_BYTES = 10139036
ARCHIVE_SHA256 = '48e76a27e3cea2c49ab6a9685551ba311a898f357416f4f91b35fc28c4dcce8b'
ARCHIVE_URL = 'https://zenodo.org/records/6791151/files/SI_input_files.zip'
_BASE = 'B-Projector_Embedding_Calculations/'
# Native label, folder, PDB filename, XYZ digest, PDB digest.
PINS = (
    ('R', '1-Reactant_Prot.StateI', 'Reactant_StateI.pdb',
        '279d0fe7bc9b1076852755ca29a79092e6c880eb26e02ce41e7774f53aaf25d6',
        'a83e90a8ade95032e91ab43d2ad743a1f644b60c0967ae782bae0d1c546a9044'),
    ('TS', '2-TransitionState_Prot.StateI', 'TransitionState_StateI.pdb',
        '5f70a397de1082f7ff1097d3344bfbf8dcb0729ade8c9f21fab034dfd0385ee9',
        '3e1ec8a345f3e31b9e43e3e7e07633dd105f1a30767fbe763bc217743255e3af'),
    ('P', '3-Product_Prot.StateI', 'Product_StateI.pdb',
        'f249118055fe064756ee234772143899b4d416ea96363d9dc8c1ae41df9fb8f1',
        '35058c788ee1169f6183043bf7b455d1f4747d59502542c4a8b20b74a2dfffa9'),
)
_SCOPE = 'EXACT_RELEASED_CARBON_GEOMETRIES_WITH_NEW_SOURCE_JOIN_NOT_GP_STATE_OR_ELECTRONIC_JOB'


def _xyz_atoms(text):
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != '86':
        raise ValueError('carbon source requires its complete 86-atom geometry')
    rows = tuple(tuple(line.split()) for line in lines[2:] if line.strip())
    if len(rows) != 86:
        raise ValueError('carbon source changes its complete atom census')
    for row in rows:
        if len(row) != 4 or row[0] not in {'C', 'H', 'N', 'O', 'P', 'Mg', 'M1'}:
            raise ValueError('carbon source contains an unsupported original atom row')
        if any(not Decimal(v).is_finite() for v in row[1:]):
            raise ValueError('carbon source contains a nonfinite coordinate')
    return rows


def _join_pdb(atoms, pdb_text):
    """Join the 79 physical atoms; keep seven cap hydrogens separate."""
    lines = tuple(line for line in pdb_text.splitlines() if line.startswith(('ATOM  ', 'HETATM')))
    if len(lines) != 34142 or lines[7230][12:16].strip() != 'MG' or lines[7230][17:20].strip() != 'MG':
        raise ValueError('carbon source changes its original PDB census or magnesium witness')
    with localcontext() as context:
        context.prec = 60
        xyz = tuple(tuple(Decimal(line[i:i+8].strip()) for i in (30,38,46)) for line in lines)
        qm = tuple(tuple(Decimal(v) for v in row[1:]) for row in atoms)
        shift = tuple(a-b for a,b in zip(xyz[7230],qm[50],strict=True))
        original = {position:i+1 for i,position in enumerate(xyz)}
        if len(original) != len(xyz):
            raise ValueError('carbon PDB has ambiguous exact coordinate witnesses')
        joins = tuple(original.get(tuple(a+b for a,b in zip(point,shift,strict=True))) for point in qm[:79])
    if any(i is None for i in joins) or len(set(joins)) != 79:
        raise ValueError('carbon physical atoms do not join the exact original PDB')
    if any(row[0] != 'H' for row in atoms[79:]):
        raise ValueError('carbon boundary census changes its seven nonphysical link hydrogens')
    expected = ((51,7231,'MG'), (53,7233,'C2'), (54,7234,'C3'), (57,7237,'C'),
        (59,7239,'O2'), (60,7240,'O3'), (63,7243,'O6'), (64,7244,'O7'))
    if any(joins[q-1] != p or lines[p-1][12:16].strip() != name for q,p,name in expected):
        raise ValueError('carbon source changes a named metal, substrate or gas correspondence')
    return joins, shift


@dataclass(frozen=True, slots=True)
class CarbonSourceState(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/carbon-source-state'
    native_label: str
    xyz_source: SourceMember
    pdb_source: ObjectIdentity
    pdb_atom_ordinals_1based: tuple[int, ...]
    pdb_translation_angstrom: tuple[Decimal, ...]
    # A separate interpretation, never a modification of original XYZ bytes.
    element_corrections: tuple[tuple[int, str, str, int], ...]

    def __post_init__(self):
        exact(self.xyz_source, SourceMember)
        exact(self.pdb_source, ObjectIdentity)
        pin = next((row for row in PINS if row[0] == self.native_label), None)
        if pin is None or (self.xyz_source.sha256, self.pdb_source.object_fingerprint) != pin[3:]:
            raise ValueError('carbon state changes its exact released XYZ/PDB witnesses')
        label, folder, _, _, pdb_digest = pin
        expected_url = ARCHIVE_URL+'#'+quote(_BASE+folder+'/'+label+'-QM_Zone.xyz')
        expected_pdb = ObjectIdentity('source.carbon-pdb.'+label.lower(),
            'empirical-lawhood/rubisco-response/carbon-native-pdb-bytes', '1.0.0', pdb_digest)
        if ((self.xyz_source.member_id,self.xyz_source.original_url)
                != ('source.carbon-state.'+label.lower(),expected_url) or self.pdb_source != expected_pdb):
            raise ValueError('carbon state changes its original source identity or location')
        atoms = _xyz_atoms(self.xyz_source.raw_utf8)
        expected = ((51,'M1','Mg',7231),) if self.native_label == 'P' else ()
        if (self.element_corrections != expected
                or tuple(i for i,row in enumerate(atoms,1) if row[0] == 'M1') != ((51,) if expected else ())
                or type(self.pdb_atom_ordinals_1based) is not tuple or len(self.pdb_atom_ordinals_1based) != 79
                or len(set(self.pdb_atom_ordinals_1based)) != 79
                or any(type(i) is not int or not 1 <= i <= 34142 for i in self.pdb_atom_ordinals_1based)
                or type(self.pdb_translation_angstrom) is not tuple or len(self.pdb_translation_angstrom) != 3):
            raise ValueError('carbon state loses physical/cap correspondence or original element correction')
        for value in self.pdb_translation_angstrom:
            validate_decimal(value, field_name='source_pdb_translation')

    @property
    def gas_addition_role(self):
        return {'P':'SEPARATED_CO2_SOURCE', 'TS':'SOURCE_TRANSITION_GEOMETRY', 'R':'CARBOXYLATED_SOURCE'}[self.native_label]

    @property
    def successor_atoms(self):
        """Explicit Mg-corrected interpretation; original native tokens persist."""
        return tuple(GeometryAtomV1('Mg' if element == 'M1' else element, tuple(tokens))
            for element,*tokens in _xyz_atoms(self.xyz_source.raw_utf8))


@dataclass(frozen=True, slots=True)
class CarbonSourceProjection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/carbon-source-projection'
    states: tuple[CarbonSourceState, ...]
    original_archive_sha256: str = ARCHIVE_SHA256
    original_archive_bytes: int = ARCHIVE_BYTES
    scope: str = _SCOPE

    def __post_init__(self):
        if (type(self.states) is not tuple or any(type(s) is not CarbonSourceState for s in self.states)
                or tuple(s.native_label for s in self.states) != ('R','TS','P')
                or (self.original_archive_sha256,self.original_archive_bytes,self.scope)
                    != (ARCHIVE_SHA256,ARCHIVE_BYTES,_SCOPE)):
            raise ValueError('carbon projection changes the complete original state or archive census')
        for state in self.states:
            state.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record('carbon-source-projection.'+self.fingerprint(), self)


def prepare_carbon_source_projection(*, original_archive_bytes):
    """Decode a bounded exact archive in memory, without extracting or running it."""
    raw = original_archive_bytes
    if type(raw) is not bytes or len(raw) != ARCHIVE_BYTES or sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('carbon preparation differs from the exact original released archive')
    states = []
    with ZipFile(BytesIO(raw)) as archive:
        census = archive.infolist()
        if (len(census) != 112 or sum(not i.is_dir() for i in census) != 91
                or sum(i.file_size for i in census) != 70833317
                or len({i.filename for i in census}) != len(census)
                or any(PurePosixPath(i.filename).is_absolute() or '..' in PurePosixPath(i.filename).parts for i in census)
                or archive.testzip() is not None):
            raise ValueError('carbon archive changes its complete bounded path, size or CRC census')
        for label,folder,pdb_name,xyz_digest,pdb_digest in PINS:
            xyz_path, pdb_path = _BASE+folder+'/'+label+'-QM_Zone.xyz', _BASE+folder+'/'+pdb_name
            xyz_raw, pdb_raw = archive.read(xyz_path), archive.read(pdb_path)
            if (sha256(xyz_raw).hexdigest(),sha256(pdb_raw).hexdigest()) != (xyz_digest,pdb_digest):
                raise ValueError('carbon archive substitutes a native XYZ/PDB state')
            source = SourceMember('source.carbon-state.'+label.lower(), ARCHIVE_URL+'#'+quote(xyz_path), xyz_digest, xyz_raw.decode('ascii'))
            atoms = _xyz_atoms(source.raw_utf8)
            joins,shift = _join_pdb(atoms,pdb_raw.decode('ascii'))
            pdb = ObjectIdentity('source.carbon-pdb.'+label.lower(), 'empirical-lawhood/rubisco-response/carbon-native-pdb-bytes', '1.0.0', pdb_digest)
            correction = ((51,'M1','Mg',7231),) if label == 'P' else ()
            states.append(CarbonSourceState(label,source,pdb,joins,shift,correction))
    return CarbonSourceProjection(tuple(states))


def assess_carbon_source_projection(*, result, original_archive_bytes):
    """Reauthenticate and reconstruct the exact source join; no new native work."""
    exact(result, CarbonSourceProjection)
    if result != prepare_carbon_source_projection(original_archive_bytes=original_archive_bytes):
        raise ValueError('carbon projection differs from its original archive and PDB joins')
    return dict(status='CARBON_SOURCE_JOIN_RECONSTRUCTED', physical_atoms_per_state=79,
        nonphysical_caps_per_state=7, states=3, new_native_calls=0, physical_or_chemical_admission=False)
