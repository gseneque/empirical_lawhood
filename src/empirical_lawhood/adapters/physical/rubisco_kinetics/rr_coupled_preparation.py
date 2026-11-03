# SPDX-License-Identifier: MPL-2.0
"""Source-bound, unrelaxed coupled Rr inventories; no solver or MM Hamiltonian.

The source admission and coordinate operations are cold standard-library CPU
work. A successful chemical inventory is separate from reactive geometry
readiness, exact biochemical parent identity and an enzyme response supplier.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field, fields, replace
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from math import acos, atan2, degrees, isfinite, sqrt
import re

from .rr_preparation import SOURCE_PINS


VARIANTS = ("unedited-reference", "D263N", "H287N")
PROTON_VIEWS = ("V2", "V3")
CONTEXT_ROSTER = tuple((v, p) for v in VARIANTS for p in PROTON_VIEWS)
PROTOCOL_SHA256 = "00db4578dc01e1e4f53b978f332e54f04e1c80b27493d7c5e3e24266d7ebcb69"
SOURCE_MAXIMUM_BYTES = 16 * 1024**2
SOURCE_TOTAL_MAXIMUM_BYTES = 16 * 1024**2
SOURCE_BINDINGS = (
    ("dry-core-source-projection-v1a.json", 3910957,
     "bfbaa57a1b9d466e311c23c37616cd54771ac170d7fc361ef7769a4004040c5f"),
    ("native-asn-templates-v1.json", 11467,
     "bd35c76940c4a727641a315208ef7cc1895c08184ba00dc7edfb1a80162e635e"),
    ("rr-amber-core-register-v1.json", 12703,
     "a6deb1386faa51e39669208fecb79a68a859888f60c6fcfaf689cfbc8c1c3ec1"),
    ("source-facts.json", 24049,
     "16d82dcf3e103965041ab9c0ce27dfed2108c47d9548fe2553104e12ef7a8909"),
    ("unedited-reference.json", 676129,
     "5be633243f7d7831501b35930c4fec5281bba852cbc0dcefbe7fb819ed708302"),
    ("d263n.json", 676662,
     "85e71834f5413161e3332b934c11cd280757c0250519eaff86e0bad2a35c75b8"),
    ("h287n.json", 676599,
     "4df7e5cfde3d50d2a7e53245871c846851b9e076648b78239c0e6af3ecaa9ffa"),
)
CORE_ATOM_COLUMNS = (
    "atom_index_1based", "residue_index_1based", "native_atom_name", "element",
    "atomic_number", "native_amber_atom_type", "native_atom_type_index_1based",
    "native_mass_token", "native_scaled_charge_token", "charge_e_decimal50",
    "native_x_12chars_angstrom", "native_y_12chars_angstrom", "native_z_12chars_angstrom",
    "geometry_origin", "native_9RUB_witness_CIF_id_author_chain_residue_atom",
)
CORE_RESIDUE_COLUMNS = (
    "residue_index_1based", "native_residue_label", "first_atom_1based", "last_atom_1based",
    "author_chain", "author_residue",
)
CORE_BOND_COLUMNS = (
    "atom_a_1based", "atom_b_1based", "parameter_index_1based", "source_flag",
    "native_atom_a_encoded_3x0based", "native_atom_b_encoded_3x0based",
    "native_parameter_index_token", "native_force_constant_token", "native_equilibrium_length_token",
)
ATOMIC_NUMBERS = {"H": 1, "C": 6, "N": 7, "O": 8, "P": 15, "S": 16, "Mg": 12}
ASN_NAMES = frozenset("N H CA HA CB HB2 HB3 CG OD1 ND2 HD21 HD22 C O".split())
BACKBONE = frozenset("N H HN1 CA HA C O OXT".split())
SIDECHAIN_POSITIONS = (191, 193, 194, 263, 287)
TRIGONAL_ANGLES = (
    ("C1", "C2", "C3"), ("C1", "C2", "O2"), ("C3", "C2", "O2"),
    ("C2", "C3", "C4"), ("C2", "C3", "O3"), ("C4", "C3", "O3"),
)
EXPECTED_INVENTORIES = {
    "unedited-reference": ((('C', 21), ('H', 35), ('Mg', 1), ('N', 3), ('O', 19), ('P', 2)), 81, -6, 382),
    "D263N": ((('C', 21), ('H', 37), ('Mg', 1), ('N', 4), ('O', 18), ('P', 2)), 83, -5, 382),
    "H287N": ((('C', 19), ('H', 34), ('Mg', 1), ('N', 2), ('O', 20), ('P', 2)), 78, -6, 370),
}
_NATIVE_COORDINATE = re.compile(r" *-?[0-9]+\.[0-9]{7}\Z")
Vec = tuple[float, float, float]


def _immutable_result(record) -> None:
    """Keep ordinary internal result records deeply immutable, without authority."""
    def check(value):
        if type(value) is tuple:
            for member in value:
                check(member)
        elif type(value) in (str, int, bool, type(None)):
            return
        elif type(value) is float and isfinite(value):
            return
        elif type(value) is Decimal and value.is_finite():
            return
        else:
            raise ValueError("ordinary result field must be finite and deeply immutable")
    for f in fields(record):
        check(getattr(record, f.name))


def _number(value: str) -> Decimal:
    if type(value) is not str or len(value) > 100:
        raise ValueError("numeric witness must be bounded text")
    try:
        n = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError("invalid numeric witness") from exc
    if not n.is_finite():
        raise ValueError("nonfinite numeric witness")
    return n


def _vec(value) -> Vec:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError("geometry needs an exact three-coordinate tuple")
    if any(type(v) not in (float, int, Decimal) for v in value):
        raise ValueError("geometry coordinate type differs")
    result = tuple(float(v) for v in value)
    if any(not isfinite(v) or abs(v) > 10000 for v in result):
        raise ValueError("nonfinite or out-of-bound geometry")
    return result


def _add(a: Vec, b: Vec) -> Vec:
    return tuple(x + y for x, y in zip(a, b, strict=True))


def _sub(a: Vec, b: Vec) -> Vec:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def _scale(a: Vec, s: float) -> Vec:
    return tuple(x * s for x in a)


def _dot(a: Vec, b: Vec) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a: Vec) -> float:
    return sqrt(_dot(a, a))


def _unit(a: Vec, *, threshold: float = 1e-12) -> Vec:
    n = _norm(a)
    if not isfinite(n) or n <= threshold:
        raise ValueError("degenerate geometry direction")
    return _scale(a, 1 / n)


def distance(a, b) -> float:
    return _norm(_sub(_vec(a), _vec(b)))


def angle_degrees(a, center, b) -> float:
    x = _unit(_sub(_vec(a), _vec(center)))
    y = _unit(_sub(_vec(b), _vec(center)))
    return degrees(acos(max(-1., min(1., _dot(x, y)))))


def proper_frame(center, toward_x, toward_y) -> tuple[Vec, Vec, Vec]:
    """Right-handed basis; no reflection, fallback axis or geometric idealization."""
    origin = _vec(center)
    x = _unit(_sub(_vec(toward_x), origin))
    d = _sub(_vec(toward_y), origin)
    y = _unit(_sub(d, _scale(x, _dot(d, x))))
    z = _unit(_cross(x, y))
    if abs(_dot(x, _cross(y, z)) - 1) > 1e-12:
        raise ValueError("amide frame is not a proper rotation")
    return x, y, z


def transplant_point(point, donor_center, donor_frame, target_center, target_frame) -> Vec:
    """Apply the unique declared frame-to-frame proper rotation and translation."""
    for frame in (donor_frame, target_frame):
        if type(frame) is not tuple or len(frame) != 3:
            raise ValueError("rotation frame shape differs")
        f = tuple(_vec(v) for v in frame)
        if (any(abs(_dot(v, v) - 1) > 1e-12 for v in f)
                or any(abs(_dot(f[i], f[j])) > 1e-12 for i in range(3) for j in range(i))
                or abs(_dot(f[0], _cross(f[1], f[2])) - 1) > 1e-12):
            raise ValueError("rotation frame is not right-handed orthonormal")
    d = _sub(_vec(point), _vec(donor_center))
    local = tuple(_dot(d, axis) for axis in donor_frame)
    return _add(_vec(target_center), tuple(sum(local[j] * target_frame[j][i] for j in range(3)) for i in range(3)))


def place_toward(acceptor, previous_donor, *, bond_length: float) -> Vec:
    if type(bond_length) is not float or not isfinite(bond_length) or not 0 < bond_length < 2:
        raise ValueError("modeled bond length differs")
    a = _vec(acceptor)
    return _add(a, _scale(_unit(_sub(_vec(previous_donor), a)), bond_length))


def place_histidine_proton(nd1, cg, ce1) -> Vec:
    n = _vec(nd1)
    inward = _add(_unit(_sub(_vec(cg), n)), _unit(_sub(_vec(ce1), n)))
    return _add(n, _scale(_unit(inward), -1.01))


@dataclass(frozen=True, slots=True)
class EnolateGeometryV1:
    c2_c3_angstrom: float
    trigonal_angles_degrees: tuple[tuple[str, float], ...]
    plane_displacements_angstrom: tuple[tuple[str, float], ...]
    signed_o2_c2_c3_o3_dihedral_degrees: float
    cis_projected_dot_angstrom_squared: float
    failures: tuple[str, ...]

    def __post_init__(self):
        _immutable_result(self)

    @property
    def passed(self) -> bool:
        return not self.failures


def enolate_geometry(named_points: tuple[tuple[str, tuple], ...]) -> EnolateGeometryV1:
    """Evaluate frozen heuristic screens, not source-validated reaction tolerances."""
    if (type(named_points) is not tuple or len(named_points) != 6
            or any(type(v) is not tuple or len(v) != 2 or type(v[0]) is not str for v in named_points)):
        raise ValueError("enolate needs the complete six-point roster")
    names = tuple(v[0] for v in named_points)
    if len(set(names)) != 6 or set(names) != {"C1", "C2", "C3", "C4", "O2", "O3"}:
        raise ValueError("enolate point names absent or duplicate")
    p = {name: _vec(point) for name, point in named_points}
    axis = _sub(p['C3'], p['C2'])
    normal = _unit(_cross(axis, _sub(p['O2'], p['C2'])))
    unit_axis = _unit(axis)
    u = _sub(p['O2'], p['C2']); v = _sub(p['O3'], p['C3'])
    u = _sub(u, _scale(unit_axis, _dot(u, unit_axis)))
    v = _sub(v, _scale(unit_axis, _dot(v, unit_axis)))
    _unit(u); _unit(v)
    cis = _dot(u, v)
    dihedral = degrees(atan2(_dot(_cross(u, v), unit_axis), cis))
    angles = tuple(('-'.join(names), angle_degrees(*(p[n] for n in names))) for names in TRIGONAL_ANGLES)
    planes = tuple((name, _dot(_sub(p[name], p['C2']), normal)) for name in ('C1', 'C2', 'C3', 'C4', 'O2', 'O3'))
    d = _norm(axis); failures = []
    if not 1.25 <= d <= 1.45:
        failures.append('C2-C3-outside-1.25-1.45-A')
    failures.extend(name + '-outside-100-140-deg' for name, value in angles if not 100 <= value <= 140)
    if max(abs(v) for _, v in planes) > .20:
        failures.append('local-plane-displacement-above-0.20-A')
    if cis <= 0:
        failures.append('not-cis-by-positive-projected-dot')
    return EnolateGeometryV1(d, angles, planes, dihedral, cis, tuple(failures))


def _json(raw: bytes):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError("duplicate source JSON member")
            result[k] = v
        return result
    def reject_constant(value):
        raise ValueError("nonfinite JSON source constant: " + value)
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_float=Decimal, parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid source JSON") from exc


@dataclass(frozen=True, slots=True)
class CoreAtomV1:
    native_tokens: tuple
    chain: str
    author_position: int
    component: str

    def __post_init__(self):
        r = self.native_tokens
        if (type(r) is not tuple or len(r) != 15 or type(r[0]) is not int or not 1 <= r[0] <= 13828
                or type(r[1]) is not int or not 1 <= r[1] <= 920
                or any(type(r[i]) is not str or not r[i] or len(r[i]) > 256 for i in (2, 3, 5, 7, 8, 9, 13))
                or type(r[6]) is not int or r[6] < 1
                or type(self.component) is not str or not self.component or len(self.component) > 8):
            raise ValueError("core atom row shape differs")
        if r[3] not in ATOMIC_NUMBERS or type(r[4]) is not int or r[4] != ATOMIC_NUMBERS[r[3]]:
            raise ValueError("core atom element/atomic number differs")
        if type(self.chain) is not str or self.chain not in ('A', 'B') or type(self.author_position) is not int:
            raise ValueError("core author identity differs")
        if any(type(v) is not str or len(v) != 12 or not _NATIVE_COORDINATE.fullmatch(v) for v in r[10:13]):
            raise ValueError("fixed-width native coordinate token differs")
        for token in r[10:13]:
            _number(token)
        if _number(r[7]) <= 0:
            raise ValueError("core native mass witness differs")
        _vec(self.coordinates)
        with localcontext() as ctx:
            ctx.prec = 50
            ctx.rounding = ROUND_HALF_EVEN
            if _number(r[9]) != _number(r[8]) / Decimal('18.2223'):
                raise ValueError("core scaled-charge source join differs")
        witness = r[14]
        if witness is not None and (type(witness) is not tuple or len(witness) != 4 or any(type(v) is not str for v in witness)):
            raise ValueError("native coordinate source witness differs")

    @property
    def index(self):
        return self.native_tokens[0]

    @property
    def name(self):
        return self.native_tokens[2]

    @property
    def element(self):
        return self.native_tokens[3]

    @property
    def coordinate_tokens(self):
        return self.native_tokens[10:13]

    @property
    def coordinates(self):
        return tuple(_number(v) for v in self.coordinate_tokens)

    @property
    def native_witness(self):
        return self.native_tokens[14]


@dataclass(frozen=True, slots=True)
class RrCoupledSourceV1:
    core_projection_bytes: bytes
    donor_template_bytes: bytes
    closed_core_register_bytes: bytes
    source_facts_bytes: bytes
    heavy_projection_bytes: tuple[bytes, bytes, bytes]
    atoms: tuple[CoreAtomV1, ...] = field(init=False)
    native_bond_rows: tuple[tuple, ...] = field(init=False)
    donor_census: tuple[tuple[str, int, int], ...] = field(init=False)
    donor_atom_indices: tuple[tuple[str, tuple[int, ...]], ...] = field(init=False)
    native_metal_contacts: tuple[tuple, ...] = field(init=False)
    source_bindings: tuple = field(init=False)

    def __post_init__(self):
        if type(self.heavy_projection_bytes) is not tuple or len(self.heavy_projection_bytes) != 3:
            raise ValueError("complete ordered heavy-projection roster required")
        payloads = (self.core_projection_bytes, self.donor_template_bytes, self.closed_core_register_bytes,
                    self.source_facts_bytes, *self.heavy_projection_bytes)
        if any(type(r) is not bytes or len(r) > SOURCE_MAXIMUM_BYTES for r in payloads):
            raise ValueError("coupled source byte type/bound differs")
        if sum(map(len, payloads)) > SOURCE_TOTAL_MAXIMUM_BYTES:
            raise ValueError("coupled aggregate source bound exceeded")
        for raw, (name, size, digest) in zip(payloads, SOURCE_BINDINGS, strict=True):
            if len(raw) != size or sha256(raw).hexdigest() != digest:
                raise ValueError("pinned coupled source bytes differ: " + name)
        c, donors, register, facts, *scaffolds = map(_json, payloads)
        if (register['source_packet_closed'] is not True
                or register['physical_member_count_including_register'] != 44
                or register['physical_bytes_including_register'] != 13788149):
            raise ValueError("closed parent-core source denominator differs")
        members = {r['name']: (r['bytes'], r['sha256']) for r in register['registered_members_excluding_self']}
        if len(members) != 43 or any(members[name] != (size, digest) for name, size, digest in SOURCE_BINDINGS[:2]):
            raise ValueError("closed register/core/template source join differs")
        if facts['source_bindings'] != [list(r) for r in SOURCE_PINS] or facts['sequence_conflicts'] != [[91, 'H', 'D']]:
            raise ValueError("native parent sequence conflict/source identity differs")
        if tuple(c['atom_columns']) != CORE_ATOM_COLUMNS or tuple(c['residue_columns']) != CORE_RESIDUE_COLUMNS or tuple(c['bond_columns']) != CORE_BOND_COLUMNS:
            raise ValueError("complete core source columns differ")
        if (len(c['atoms']), len(c['residues']), len(c['bonds'])) != (13828, 920, 13994):
            raise ValueError("complete core atom/residue/bond denominator differs")
        residues = {r[0]: r for r in c['residues']}
        if len(residues) != 920 or set(residues) != set(range(1, 921)):
            raise ValueError("core residue IDs duplicate or missing")
        atoms = []
        for expected, row in enumerate(c['atoms'], 1):
            if row[0] != expected or row[1] not in residues:
                raise ValueError("core atom index/residue join differs")
            rr = residues[row[1]]
            if not rr[2] <= expected <= rr[3]:
                raise ValueError("native residue range differs")
            r = tuple(tuple(v) if isinstance(v, list) else v for v in row)
            atoms.append(CoreAtomV1(r, rr[4], rr[5], rr[1]))
        if len({(a.chain, a.author_position, a.name) for a in atoms}) != 13828:
            raise ValueError("ambiguous core atom-name/author mapping")
        bonds = tuple(tuple(r) for r in c['bonds'])
        pairs = set()
        for r in bonds:
            pair = tuple(sorted(r[:2]))
            if (len(r) != 9 or any(type(v) is not int or not 1 <= v <= 13828 for v in r[:2])
                    or pair[0] == pair[1] or pair in pairs
                    or tuple(int(v) // 3 + 1 for v in r[4:6]) != r[:2]):
                raise ValueError("native core bond source join differs")
            pairs.add(pair)
        base = scaffolds[0]
        native = {r[0]: r for r in base['atoms']}
        inherited = [a for a in atoms if a.native_witness is not None]
        if len(inherited) != 7028 or {a.native_witness[0] for a in inherited} != set(native):
            raise ValueError("core/full heavy-scaffold atom membership differs")
        translation = tuple(_number(v) for v in c['inherited_coordinate_translation_angstrom'])
        with localcontext() as ctx:
            ctx.prec = 50
            ctx.rounding = ROUND_HALF_EVEN
            for a in inherited:
                r = native[a.native_witness[0]]
                if tuple(a.native_witness[1:]) != (r[3], str(r[4]), r[6]):
                    raise ValueError("core/native witness identity differs")
                if a.coordinates != tuple(_number(v) + t for v, t in zip(r[12:15], translation, strict=True)):
                    raise ValueError("core/native exact translated coordinates differ")
        for variant, s in zip(VARIANTS, scaffolds, strict=True):
            if (s['variant'] != variant or s['reference_choice'] != 'modeled-H91'
                    or s['protein_residues'] != 916 or s['completed_qm_contexts'] != 0):
                raise ValueError("inherited three-heavy-scaffold scope differs")
        by_res = defaultdict(list)
        for a in atoms:
            by_res[(a.chain, a.author_position)].append(a)
        census = []
        for (chain, position), group in sorted(by_res.items()):
            if group[0].component != 'ASN' or {a.name for a in group} != ASN_NAMES or len(group) != 14:
                continue
            if sum(a.native_witness is not None for a in group) != 8:
                continue
            census.append((chain, position, group[0].native_tokens[1]))
        declared = tuple((r['chain'], r['author_residue'], r['residue_index']) for r in donors['complete_eligible_roster'])
        if tuple(census) != declared or len(census) != 30:
            raise ValueError("complete label-free ASN donor census differs")
        selected = []
        for chain in ('A', 'B'):
            chosen = min(v for v in census if v[0] == chain)
            if chosen[1] != 9:
                raise ValueError("deterministic same-chain lowest ASN differs")
            declared_template = next(r for r in donors['selected_templates'] if r['residue'][4] == chain)
            group = by_res[(chain, 9)]
            if declared_template['atom_rows'] != [list(a.native_tokens[:-1]) + [list(a.native_witness) if a.native_witness else None] for a in group]:
                raise ValueError("ASN template/full core exact atom join differs")
            selected.append((chain, tuple(a.index for a in group)))
        if donors['source_projection_sha256'] != SOURCE_BINDINGS[0][2]:
            raise ValueError("template/core projection fingerprint differs")
        contacts = tuple((b['first_source_id'], b['second_source_id'], tuple(tuple(p) for p in b['source_tokens']))
                         for b in facts['native_bonds'] if dict(b['source_tokens'])['conn_type_id'] == 'metalc')
        object.__setattr__(self, 'atoms', tuple(atoms))
        object.__setattr__(self, 'native_bond_rows', bonds)
        object.__setattr__(self, 'donor_census', tuple(census))
        object.__setattr__(self, 'donor_atom_indices', tuple(selected))
        object.__setattr__(self, 'native_metal_contacts', contacts)
        object.__setattr__(self, 'source_bindings', SOURCE_BINDINGS)


def decode_rr_coupled_source(core_projection_bytes, donor_template_bytes, closed_core_register_bytes,
                             source_facts_bytes, heavy_projection_bytes) -> RrCoupledSourceV1:
    return RrCoupledSourceV1(core_projection_bytes, donor_template_bytes, closed_core_register_bytes,
                             source_facts_bytes, heavy_projection_bytes)


@dataclass(frozen=True, slots=True)
class PreparedAtomV1:
    atom_id: str
    chain: str
    author_position: int
    component: str
    name: str
    element: str
    coordinates: tuple[Decimal, Decimal, Decimal]
    parent_atom_index: int | None
    origin: str
    donor_atom_index: int | None = None

    def __post_init__(self):
        _immutable_result(self)
        if (type(self.atom_id) is not str or not self.atom_id or self.chain not in ('A', 'B')
                or type(self.author_position) is not int or self.element not in ATOMIC_NUMBERS
                or any(type(v) is not str or not v or len(v) > 256 for v in (self.component, self.name, self.origin))
                or type(self.coordinates) is not tuple or len(self.coordinates) != 3
                or any(type(v) is not Decimal or not v.is_finite() for v in self.coordinates)):
            raise ValueError("prepared atom identity/coordinate shape differs")
        _vec(self.coordinates)
        for index in (self.parent_atom_index, self.donor_atom_index):
            if index is not None and (type(index) is not int or not 1 <= index <= 13828):
                raise ValueError("prepared atom source-index witness differs")


@dataclass(frozen=True, slots=True)
class MutationAuditV1:
    chain: str
    author_position: int
    parent_component: str
    target_component: str
    donor_author_position: int
    removed_parent_atom_indices: tuple[int, ...]
    added_atom_ids: tuple[str, ...]
    reassigned_cg_parent_index: int
    donor_frame: tuple[Vec, Vec, Vec]
    target_frame: tuple[Vec, Vec, Vec]
    internal_distance_checks_angstrom: tuple[tuple[str, str, float, float], ...]
    donor_signed_plane_distances_angstrom: tuple[tuple[str, float], ...]

    def __post_init__(self):
        _immutable_result(self)


@dataclass(frozen=True, slots=True)
class ProtonTransferV1:
    identity: str
    atom_id: str
    previous_donor_id: str
    new_acceptor_id: str
    placement_direction_previous_donor_id: str
    original_coordinates: tuple[Decimal, Decimal, Decimal]
    new_coordinates: tuple[Decimal, Decimal, Decimal]

    def __post_init__(self):
        _immutable_result(self)


@dataclass(frozen=True, slots=True)
class BoundaryCapV1:
    author_position: int
    cap_atom_id: str
    quantum_cb_atom_id: str
    environment_ca_atom_id: str
    cap_cb_distance_angstrom: float
    cap_own_ca_distance_angstrom: float

    def __post_init__(self):
        _immutable_result(self)


@dataclass(frozen=True, slots=True)
class ContactV1:
    changed_atom_id: str
    other_atom_id: str
    distance_angstrom: float
    category: str

    def __post_init__(self):
        _immutable_result(self)


def validate_lewis_inventory(atoms: tuple[tuple[str, str], ...],
                             bonds: tuple[tuple[str, str, int], ...],
                             charges: tuple[tuple[str, int], ...]) -> tuple[tuple[tuple[str, int], ...], int, int]:
    """Independent full-QM Lewis valence and integer Q/electron bookkeeping."""
    if type(atoms) is not tuple or type(bonds) is not tuple or type(charges) is not tuple:
        raise ValueError("Lewis inventory requires immutable complete rosters")
    elements = dict(atoms)
    formal = dict(charges)
    if (len(elements) != len(atoms) or len(formal) != len(charges) or set(formal) != set(elements)
            or any(type(k) is not str or not k for k in elements)
            or any(v not in ATOMIC_NUMBERS for v in elements.values())
            or any(type(v) is not int for v in formal.values())):
        raise ValueError("Lewis atom/charge census absent or duplicate")
    valence = Counter(); seen = set()
    for a, b, order in bonds:
        pair = tuple(sorted((a, b)))
        if (a not in elements or b not in elements or a == b or pair in seen
                or type(order) is not int or not 1 <= order <= 3):
            raise ValueError("Lewis bond census absent, duplicate or invalid")
        seen.add(pair); valence[a] += order; valence[b] += order
    expected = {('H', 0): 1, ('C', 0): 4, ('N', 0): 3,
                ('O', 0): 2, ('O', -1): 1, ('P', 0): 5, ('Mg', 2): 0}
    for atom_id, element in atoms:
        key = (element, formal[atom_id])
        if key not in expected or valence[atom_id] != expected[key]:
            raise ValueError("invalid candidate QM Lewis valence: " + atom_id)
    formula = tuple(sorted(Counter(elements.values()).items()))
    q = sum(formal.values())
    electrons = sum(ATOMIC_NUMBERS[e] for e in elements.values()) - q
    return formula, q, electrons


def _modeled_coordinates(point: Vec) -> tuple[Decimal, Decimal, Decimal]:
    return tuple(Decimal(repr(v)) for v in _vec(point))


def _parent_atom(a: CoreAtomV1) -> PreparedAtomV1:
    return PreparedAtomV1('amber:' + str(a.index), a.chain, a.author_position, a.component,
                          a.name, a.element, a.coordinates, a.index,
                          'unchanged-parent-coordinate:' + a.native_tokens[13])


def _amide(source, atoms, bonds, chain, position):
    native = {a.name: a for a in source.atoms if a.chain == chain and a.author_position == position}
    donor = {a.name: a for a in source.atoms if a.index in dict(source.donor_atom_indices)[chain]}
    target_direction = 'OD1' if position == 263 else 'ND1'
    donor_frame = proper_frame(donor['CG'].coordinates, donor['CB'].coordinates, donor['OD1'].coordinates)
    target_frame = proper_frame(native['CG'].coordinates, native['CB'].coordinates, native[target_direction].coordinates)
    old_names = {'OD1', 'OD2'} if position == 263 else {'ND1', 'CE1', 'NE2', 'CD2', 'HE1', 'HD2', 'HE2'}
    removed = tuple(native[n].index for n in native if n in old_names)
    removed_ids = {'amber:' + str(i) for i in removed}
    for atom_id in removed_ids:
        del atoms[atom_id]
    bonds.difference_update({pair for pair in bonds if any(a in removed_ids for a in pair)})
    cg_id = 'amber:' + str(native['CG'].index)
    for atom_id, atom in tuple(atoms.items()):
        if atom.chain == chain and atom.author_position == position:
            origin = ('modeled-ASN-CG-assignment-with-unchanged-parent-coordinate' if atom.name == 'CG'
                      else 'unchanged-parent-coordinate-in-modeled-ASN-recipe')
            atoms[atom_id] = replace(atom, component='ASN', origin=origin)
    added = []
    for name in ('OD1', 'ND2', 'HD21', 'HD22'):
        d = donor[name]
        point = transplant_point(d.coordinates, donor['CG'].coordinates, donor_frame,
                                 native['CG'].coordinates, target_frame)
        atom_id = f'modeled:{chain}:{position}:{name}'
        atoms[atom_id] = PreparedAtomV1(atom_id, chain, position, 'ASN', name, d.element,
                                       _modeled_coordinates(point), None,
                                       'modeled-rigid-same-chain-ASN9-amide-transfer', d.index)
        added.append(atom_id)
    for a, b in (('CG', 'OD1'), ('CG', 'ND2'), ('ND2', 'HD21'), ('ND2', 'HD22')):
        ai = cg_id if a == 'CG' else f'modeled:{chain}:{position}:{a}'
        bi = f'modeled:{chain}:{position}:{b}'
        bonds.add(tuple(sorted((ai, bi))))
    group = {'CG': atoms[cg_id], **{a.name: a for a in atoms.values()
                                      if a.chain == chain and a.author_position == position and a.name in {'OD1', 'ND2', 'HD21', 'HD22'}}}
    checks = []
    names = ('CG', 'OD1', 'ND2', 'HD21', 'HD22')
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            old = distance(donor[a].coordinates, donor[b].coordinates)
            new = distance(group[a].coordinates, group[b].coordinates)
            if abs(old - new) > 1e-10:
                raise ValueError("rigid donor internal geometry changed")
            checks.append((a, b, old, new))
    planes = tuple((n, _dot(_sub(_vec(donor[n].coordinates), _vec(donor['CG'].coordinates)), donor_frame[2]))
                   for n in ('ND2', 'HD21', 'HD22'))
    return MutationAuditV1(chain, position, native['CG'].component, 'ASN', 9, removed,
                           tuple(added), native['CG'].index, donor_frame, target_frame, tuple(checks), planes)


def _tautomer(atoms, bonds, chain):
    group = {a.name: a for a in atoms.values() if a.chain == chain and a.author_position == 287}
    old, nd1 = group['HE2'], group['ND1']
    bonds.remove(tuple(sorted((old.atom_id, group['NE2'].atom_id))))
    bonds.add(tuple(sorted((old.atom_id, nd1.atom_id))))
    point = place_histidine_proton(nd1.coordinates, group['CG'].coordinates, group['CE1'].coordinates)
    for a in group.values():
        atoms[a.atom_id] = replace(a, component='HID', origin='unchanged-parent-coordinate-in-modeled-HID287-recipe')
    atoms[old.atom_id] = replace(old, name='HD1', component='HID', coordinates=_modeled_coordinates(point),
                                 origin='modeled-His287-HE2-nucleus-relocated-and-renamed-HD1')
    return ProtonTransferV1('His287-' + chain + '-source-HE2', old.atom_id, group['NE2'].atom_id,
                            nd1.atom_id, 'negative-ND1-neighbor-unit-bisector', old.coordinates, atoms[old.atom_id].coordinates)


def _relay(atoms, bonds, view):
    group = {(a.component, a.name): a for a in atoms.values() if a.chain == 'A' and a.component in ('RUB', 'KCX')}
    ha, hb = group['RUB', 'HC3'], group['RUB', 'HO3']
    old_c3, o3 = group['RUB', 'C3'], group['RUB', 'O3']
    oq1, o2 = group['KCX', 'OQ1'], group['RUB', 'O2']
    movements = ((ha, old_c3, oq1, old_c3),) if view == 'V2' else (
        (ha, old_c3, o2, oq1), (hb, o3, oq1, o3))
    result = []
    for h, old_donor, acceptor, placement_donor in movements:
        pair = tuple(sorted((h.atom_id, old_donor.atom_id)))
        if pair not in bonds:
            raise ValueError("proton attachment source identity differs")
        bonds.remove(pair); bonds.add(tuple(sorted((h.atom_id, acceptor.atom_id))))
        point = place_toward(acceptor.coordinates, placement_donor.coordinates, bond_length=.97)
        atoms[h.atom_id] = replace(h, author_position=acceptor.author_position, component=acceptor.component,
                                   name='H_a' if h.atom_id == ha.atom_id else 'H_b',
                                   coordinates=_modeled_coordinates(point), origin='modeled-conserved-nucleus-relay-' + view)
        result.append(ProtonTransferV1('H_a' if h.atom_id == ha.atom_id else 'H_b', h.atom_id,
                                      old_donor.atom_id, acceptor.atom_id, placement_donor.atom_id,
                                      h.coordinates, atoms[h.atom_id].coordinates))
    if ha.atom_id == hb.atom_id or any(len([pair for pair in bonds if t.atom_id in pair]) != 1 for t in result):
        raise ValueError("proton identity/bond bijection differs")
    return tuple(result), ha.atom_id, hb.atom_id


def _candidate_lewis(qm_atoms, bonds, view):
    ids = {a.atom_id for a in qm_atoms}
    keys = {(a.author_position, a.name): a.atom_id for a in qm_atoms if a.component != 'CAP'}
    ligand = {a.name: a.atom_id for a in qm_atoms if a.component == 'RUB'}
    orders = {pair: 1 for pair in bonds if pair[0] in ids and pair[1] in ids}
    charges = {a.atom_id: 0 for a in qm_atoms}
    def double(a, b):
        pair = tuple(sorted((a, b)))
        if pair not in orders:
            raise ValueError("declared double bond absent from candidate graph")
        orders[pair] = 2
    double(ligand['C2'], ligand['C3'])
    double(ligand['P1'], ligand['O1P']); double(ligand['P2'], ligand['O4P'])
    for name in ('O2P', 'O3P', 'O5P', 'O6P', 'O2' if view == 'V2' else 'O3'):
        charges[ligand[name]] = -1
    double(keys[191, 'CX'], keys[191, 'OQ2'])
    for position in (193, 263):
        double(keys[position, 'CG'], keys[position, 'OD1'])
        if (position, 'OD2') in keys:
            charges[keys[position, 'OD2']] = -1
    double(keys[194, 'CD'], keys[194, 'OE1']); charges[keys[194, 'OE2']] = -1
    if (287, 'ND2') in keys:
        double(keys[287, 'CG'], keys[287, 'OD1'])
    else:
        double(keys[287, 'CE1'], keys[287, 'NE2']); double(keys[287, 'CD2'], keys[287, 'CG'])
    charges[next(a.atom_id for a in qm_atoms if a.element == 'Mg')] = 2
    return tuple((a, b, order) for (a, b), order in sorted(orders.items())), tuple(sorted(charges.items()))


def local_contacts(atoms: tuple[PreparedAtomV1, ...], bonds: tuple[tuple[str, str], ...],
                   changed_ids: tuple[str, ...], cap_exemptions: tuple[tuple[str, str], ...]) -> tuple[ContactV1, ...]:
    """Complete changed-atom contacts within 3 A, with exact graph/exemption roles."""
    by_id = {a.atom_id: a for a in atoms}
    if (len(by_id) != len(atoms) or len(set(changed_ids)) != len(changed_ids)
            or any(i not in by_id for i in changed_ids)):
        raise ValueError("changed-atom/contact census differs")
    graph = defaultdict(set)
    for a, b in bonds:
        if a not in by_id or b not in by_id or a == b:
            raise ValueError("completed contact graph join differs")
        graph[a].add(b); graph[b].add(a)
    exemptions = {frozenset(pair) for pair in cap_exemptions}
    if len(exemptions) != len(cap_exemptions) or any(
            a not in by_id or b not in by_id or by_id[a].component != 'CAP' or by_id[b].name != 'CA'
            or (by_id[a].chain, by_id[a].author_position) != (by_id[b].chain, by_id[b].author_position)
            for a, b in cap_exemptions):
        raise ValueError("cap own-CA exemption census differs")
    coordinates = {k: _vec(a.coordinates) for k, a in by_id.items()}
    result = []
    for atom_id in changed_ids:
        first = graph[atom_id]
        second = set().union(*(graph[b] for b in first)) if first else set()
        point = coordinates[atom_id]
        for other, p in coordinates.items():
            if other == atom_id:
                continue
            # Coordinate-axis prefilter is exact for the selected spherical 3 A census.
            if any(abs(x - y) > 3 for x, y in zip(point, p, strict=True)):
                continue
            d = _norm(_sub(point, p))
            if d > 3:
                continue
            role = ('own-omitted-CA-cap-exemption' if frozenset((atom_id, other)) in exemptions
                    else 'one-bond-neighbor' if other in first else 'two-bond-neighbor' if other in second
                    else 'severe-nonbonded-overlap' if d < .70 else 'nonbonded-diagnostic')
            result.append(ContactV1(atom_id, other, d, role))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class RrInitialContextV1:
    source: RrCoupledSourceV1
    variant: str
    proton_view: str
    physical_atoms: tuple[PreparedAtomV1, ...] = field(init=False)
    quantum_atoms: tuple[PreparedAtomV1, ...] = field(init=False)
    environment_atoms: tuple[PreparedAtomV1, ...] = field(init=False)
    candidate_bonds: tuple[tuple[str, str], ...] = field(init=False)
    candidate_qm_lewis_bonds: tuple[tuple[str, str, int], ...] = field(init=False)
    candidate_qm_formal_charges: tuple[tuple[str, int], ...] = field(init=False)
    removed_parent_atom_indices: tuple[int, ...] = field(init=False)
    changed_atom_ids: tuple[str, ...] = field(init=False)
    mutation_audits: tuple[MutationAuditV1, ...] = field(init=False)
    proton_transfers: tuple[ProtonTransferV1, ...] = field(init=False)
    caps: tuple[BoundaryCapV1, ...] = field(init=False)
    formula: tuple[tuple[str, int], ...] = field(init=False)
    formal_quantum_charge: int = field(init=False)
    electron_count: int = field(init=False)
    enolate_geometry: EnolateGeometryV1 = field(init=False)
    changed_atom_contacts: tuple[ContactV1, ...] = field(init=False)
    nearest_quantum_environment_pair: tuple[str, str, float] = field(init=False)
    status: str = field(init=False)
    failures: tuple[str, ...] = field(init=False)
    inventory_passed: bool = field(init=False, default=True)
    executable_mm_hamiltonian: bool = field(init=False, default=False)
    exact_assay_parent_admitted: bool = field(init=False, default=False)
    ground_state_certified: bool = field(init=False, default=False)
    selected_singlet_hypothesis: bool = field(init=False, default=True)
    native_effects: int = field(init=False, default=0)
    protocol_sha256: str = field(init=False, default=PROTOCOL_SHA256)

    def __post_init__(self):
        if (type(self.source) is not RrCoupledSourceV1 or type(self.variant) is not str or type(self.proton_view) is not str
                or self.variant not in VARIANTS or self.proton_view not in PROTON_VIEWS):
            raise ValueError("fixed coupled context source/recipe differs")
        atoms = {a.atom_id: a for a in map(_parent_atom, self.source.atoms)}
        bonds = {tuple(sorted(('amber:' + str(r[0]), 'amber:' + str(r[1])))) for r in self.source.native_bond_rows}
        mutations = []
        if self.variant != 'unedited-reference':
            position = 263 if self.variant == 'D263N' else 287
            for chain in ('A', 'B'):
                mutations.append(_amide(self.source, atoms, bonds, chain, position))
        tautomer_transfers = tuple(_tautomer(atoms, bonds, c) for c in ('A', 'B')) if self.variant != 'H287N' else ()
        transfers, ha_id, hb_id = _relay(atoms, bonds, self.proton_view)
        physical = tuple(atoms.values())
        expected_physical = {'unedited-reference': 13828, 'D263N': 13832, 'H287N': 13822}[self.variant]
        if len(physical) != expected_physical or len({a.atom_id for a in physical}) != expected_physical:
            raise ValueError("completed paired physical atom denominator differs")
        # The pair conserves all nuclei under proton movements; no H ID is duplicated/lost.
        if any(i not in atoms for i in (ha_id, hb_id)) or atoms[ha_id].element != 'H' or atoms[hb_id].element != 'H':
            raise ValueError("physical relay hydrogen identity differs")
        real_qm = tuple(a for a in physical if a.chain == 'A' and (
            a.component in ('RUB', 'MG') or a.author_position in SIDECHAIN_POSITIONS and a.name not in BACKBONE))
        real_ids = {a.atom_id for a in real_qm}
        environment = tuple(a for a in physical if a.atom_id not in real_ids)
        if real_ids & {a.atom_id for a in environment} or len(real_ids) + len(environment) != len(physical):
            raise ValueError("quantum/environment physical membership double counting")
        caps = []; cap_atoms = []
        for position in SIDECHAIN_POSITIONS:
            group = {a.name: a for a in physical if a.chain == 'A' and a.author_position == position}
            cb, ca = group['CB'], group['CA']
            pair = tuple(sorted((cb.atom_id, ca.atom_id)))
            if pair not in bonds or cb.atom_id not in real_ids or ca.atom_id in real_ids:
                raise ValueError("common CA-CB cut absent or on wrong quantum side")
            bonds.remove(pair)
            atom_id = f'cap:A:{position}:CA-CB'
            point = _modeled_coordinates(place_toward(cb.coordinates, ca.coordinates, bond_length=1.09))
            atom = PreparedAtomV1(atom_id, 'A', position, 'CAP', 'HL' + str(position), 'H', point, None,
                                  'modeled-boundary-link-H-not-parent-nucleus')
            cap_atoms.append(atom); bonds.add(tuple(sorted((cb.atom_id, atom_id))))
            caps.append(BoundaryCapV1(position, atom_id, cb.atom_id, ca.atom_id,
                                      distance(point, cb.coordinates), distance(point, ca.coordinates)))
        qm = real_qm + tuple(cap_atoms)
        lewis, charges = _candidate_lewis(qm, bonds, self.proton_view)
        formula, q, electrons = validate_lewis_inventory(tuple((a.atom_id, a.element) for a in qm), lewis, charges)
        if (formula, len(qm), q, electrons) != EXPECTED_INVENTORIES[self.variant] or electrons % 2:
            raise ValueError("completed formula/charge/electron inventory differs")
        points = tuple((a.name, a.coordinates) for a in physical if a.chain == 'A' and a.component == 'RUB'
                       and a.name in {'C1', 'C2', 'C3', 'C4', 'O2', 'O3'})
        geometry = enolate_geometry(points)
        changed = tuple(a.atom_id for a in physical if not a.origin.startswith('unchanged-parent-coordinate:')) + tuple(a.atom_id for a in cap_atoms)
        all_atoms = physical + tuple(cap_atoms)
        contacts = local_contacts(all_atoms, tuple(sorted(bonds)), changed,
                                  tuple((c.cap_atom_id, c.environment_ca_atom_id) for c in caps))
        severe = tuple(c for c in contacts if c.category == 'severe-nonbonded-overlap')
        # Complete nearest pair census, not a radius-limited contact approximation.
        best = ('', '', float('inf'))
        env_points = tuple((a.atom_id, _vec(a.coordinates)) for a in environment)
        for a in qm:
            point = _vec(a.coordinates)
            for atom_id, other in env_points:
                squared = _dot(_sub(point, other), _sub(point, other))
                if squared < best[2] ** 2:
                    best = (a.atom_id, atom_id, sqrt(squared))
        removed = tuple(i for m in mutations for i in m.removed_parent_atom_indices)
        failures = tuple(f'severe-overlap:{c.changed_atom_id}:{c.other_atom_id}' for c in severe) + geometry.failures
        status = 'CONSTRUCTION_REFUSED' if severe else 'GEOMETRY_UNREADY' if not geometry.passed else 'INITIAL_GEOMETRY_SCREEN_PASSED'
        values = {
            'physical_atoms': physical, 'quantum_atoms': qm, 'environment_atoms': environment,
            'candidate_bonds': tuple(sorted(bonds)), 'candidate_qm_lewis_bonds': lewis,
            'candidate_qm_formal_charges': charges, 'removed_parent_atom_indices': removed,
            'changed_atom_ids': changed, 'mutation_audits': tuple(mutations),
            'proton_transfers': tautomer_transfers + transfers, 'caps': tuple(caps),
            'formula': formula, 'formal_quantum_charge': q, 'electron_count': electrons,
            'enolate_geometry': geometry, 'changed_atom_contacts': contacts,
            'nearest_quantum_environment_pair': best, 'status': status, 'failures': failures,
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)


def construct_rr_initial_context(source: RrCoupledSourceV1, *, variant: str, proton_view: str) -> RrInitialContextV1:
    return RrInitialContextV1(source, variant, proton_view)
