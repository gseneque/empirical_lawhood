# SPDX-License-Identifier: MPL-2.0
"""Reviewed FM23 geometry admission and explicitly new CO2 encounter guesses.

The PDF is admitted as an original byte witness. Coordinates are taken from
the separately pinned, reviewed PDF projection; no native XYZ release or PDF
parser is asserted. All 24 source geometries remain available. Preparation
uses the first unprotonated syn geometry and performs only bounded geometry
arithmetic. It supplies neither a quantum job nor a kinetic prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import itertools
import json
import re
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord

PDF_SHA256 = "0b8fdf27b307e8485f1ff65ef1c5b463b2789da6e6019ddc9dd66250bb0e9801"
PDF_BYTES = 1210102
PROJECTION_SHA256 = "b4365d9082c6d2894aff52d9034e8e3b701ee622bf0ff258c3d99292162d408f"
PROJECTION_BYTES = 1016807
MAXIMUM_INPUT_BYTES = 2 * 1024**2
MAXIMUM_CANDIDATE_TRIALS = 65536
SOURCE_ROLE = "REVIEWED_PDF_COORDINATE_PROJECTION_NOT_NATIVE_XYZ_RELEASE"
NEW_ROLE = "NEW_UNRELAXED_ENCOUNTER_GUESS_NOT_NATIVE_CARBON_GEOMETRY"
ORIENTATIONS = ("original-axis", "rotated-axis")
FIELDS = ("O-O", "gas_atom-C2", "C2-C3", "C3-O3", "C3-waterO")
# Exact metadata and native atom-token projection digests from the reviewed SI.
# These bind constructors as well as the raw-source decoder.
GEOMETRY_PINS = (
    ("Syn pathway", "Enediolate + O2", 248, "5c037c52f4197a5b0f0a2179674b80bd4466287754accfd1a54f4aa0cc0b6f04"),
    ("Syn pathway", "MECP", 248, "6989ea0346997f83183cd4b5fa58c3abf9eed4b4cd1c54dc0e93d49161395d68"),
    ("Syn pathway", "Peroxo product", 248, "02443a3da607d490ad21fc449ff48e5889b34d7799d8532297968372bbe64ccd"),
    ("Syn pathway", "Hydration TS", 248, "459ab4760f2a9478db43706fb46440916b11864ac4efe9e9f4d3bd38077e5a39"),
    ("Syn pathway", "Gemdiol intermediate", 248, "689660c11cbd8891cbd03488235c52aeeb4f646b908298093837bbdd115ee97f"),
    ("Syn pathway", "TS for scission", 248, "b94aeaa3b12527ff685d472756374f9ddb02af43e8e2259702e538cd2ce16d56"),
    ("Syn pathway", "Final products", 248, "f2e02beb941c1ddaffa3f0af0d28bd4510cbd03fe8e808909c17b10661e522ec"),
    ("Anti-pathway", "peroxo product", 251, "8c44232666aa826700e36121525f63e27b8d0b296dc627f4e3bd0553a5e613d1"),
    ("Anti-pathway", "hydration TS", 251, "8f07329f847de706264f63a8d7c92e99f28e3ad736471f2e838cec134f70dbdb"),
    ("Anti-pathway", "Gemdiol intermediate", 251, "66b0c214db366b8e164f24a0e3b8fb970613356906283525567de2f16864e3d5"),
    ("Anti-pathway", "TS for scission", 251, "790b243557f1b5975ec059507299c7a241fe54ecb5bed6014175e1ff6043cb43"),
    ("Anti-pathway", "Final products", 251, "ba99f1c3cc320d42a0ae3551e5651e1a6c2b075b56be56123a4ca301df4161e8"),
    ("H+-syn pathway", "enediolate+O2", 249, "3dc3c65965c85ac08d6a5fb4cfce195f8d30e11505ab594b5e9eed849487a101"),
    ("H+-syn pathway", "MECP", 249, "cb59b1b4b00652752591c992f297cb7c6bd0d62110ca5438b10a80b01009b175"),
    ("H+-syn pathway", "peroxo intermediate", 249, "04a78fb4caae579e3565343099a81e89274a556015eff2e19981fea5bc1b712e"),
    ("H+-syn pathway", "Hydration TS", 249, "9dfa5f1c730e4e52bd331d300c76e0241d9b9634dd3ce9265fd716b8ddcd142b"),
    ("H+-syn pathway", "gemdiol intermediate", 249, "70b3d5943a9ee0ff8bd3b1478f0b0d246bc0baf91012d68dec78f2cf5e39485c"),
    ("H+-syn pathway", "Scission TS", 249, "60ad202ccfc82fce05f6ca07d4cf887a6321705e2b7f7b9975b9c1bd2d3bb4fa"),
    ("H+-syn pathway", "Final products", 249, "dbda66e92bf1a0ef1bf157a46a8b53ab9be6512263fe1d3152c80e8a048e7359"),
    ("H+-anti pathway", "peroxo intermediate", 252, "a573cc62d797fa205487809af16150c0cb72e2bde10bbe8970a75a992a224aa5"),
    ("H+-anti pathway", "Hydration TS", 252, "11f1ebf090d8cee40416b4aaa03fd770d4967f8c69de995335b17cc8caf274ce"),
    ("H+-anti pathway", "gemdiol intermediate", 252, "03ea01eddebbd614e01eb21b7234ee55b26c3741f984d63f521ccd42f0bc7906"),
    ("H+-anti pathway", "Scission TS", 252, "04038c3387066d91fcfe3939c9c0af75309c04340e432a47642eab0642dc945f"),
    ("H+-anti pathway", "Final products", 252, "8ce31cfba0ff8a6471ac0c6c9b65fb6ba287f356ad45f0aca29731c4403c85d7"),
)
# Factual Table S2 distances, in angstrom; tokens retain printed precision.
OXYGEN_TARGETS = (
    ("1.24", "1.31", "1.46", "1.45", "1.45", "1.87", "3.4"),
    ("2.78", "2.12", "1.43", "1.42", "1.42", "1.28", "1.26"),
    ("1.37", "1.42", "1.54", "1.55", "1.59", "1.97", "3.4"),
    ("1.32", "1.28", "1.24", "1.24", "1.35", "1.3", "1.22"),
    ("3.19", "3.07", "3.08", "2.28", "1.49", "1.38", "1.34"),
)
CARBON_INITIAL = ("3.1", "1.17", "1.36", "1.33", "3.25")
LIMITATIONS = (
    "ALL24_GEOMETRIES_REVIEWED_PDF_PROJECTION_NOT_NATIVE_XYZ",
    "ONLY_SEVEN_UNPROTONATED_SYN_STATES_JOINED_TO_TABLE_S2",
    "NEW_CO2_POSES_FAIL_THREE_NATIVE_CARBON_SCAFFOLD_CHECKS",
    "TWO_ORIENTATIONS_DO_NOT_SAMPLE_FULL_APPROACH_TILT_OR_PROTONATION",
    "NO_AUTHENTICATED_CHARGE_SPIN_HAMILTONIAN_FIXED_ATOM_MASK_OR_JOB",
    "NO_STERIC_ENERGY_OR_STATIONARY_STATE_QUALIFICATION",
    "NO_SSU_OR_D263_MUTATION_ENVIRONMENT",
    "NO_SOLVER_FREE_ENERGY_REACTION_RATE_OR_KINETIC_ENDPOINT",
)
_TOKEN = re.compile(r"[-+]?\d{1,5}\.\d{1,10}\Z")


def _context() -> Context:
    return Context(prec=80, rounding=ROUND_HALF_EVEN)


def _token(value: str) -> Decimal:
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        raise ValueError("coordinates require bounded finite fixed-point native strings")
    number = Decimal(value)
    if number.copy_abs() > 10000:
        raise ValueError("coordinate exceeds the geometric contract")
    return number


def _tuple_of(values: tuple, kind: type, *, maximum: int = 512) -> None:
    if type(values) is not tuple or len(values) > maximum or any(type(x) is not kind for x in values):
        raise ValueError("geometry collections require bounded exact typed tuples")


@dataclass(frozen=True, slots=True)
class GeometryAtomV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/geometry-atom"
    element: str
    coordinate_tokens: tuple[str, str, str]

    def __post_init__(self) -> None:
        if self.element not in ("C", "H", "N", "O", "P", "Mg"):
            raise ValueError("unsupported FM23 atom element")
        _tuple_of(self.coordinate_tokens, str, maximum=3)
        if len(self.coordinate_tokens) != 3:
            raise ValueError("atom requires exactly three coordinate tokens")
        for value in self.coordinate_tokens:
            _token(value)


def native_atom_projection_sha256(atoms: tuple[GeometryAtomV1, ...]) -> str:
    """Identity of the reviewed plain projection, preserving every token."""
    _tuple_of(atoms, GeometryAtomV1)
    native = [{"element": a.element, "xyz_native_decimal_tokens": list(a.coordinate_tokens)} for a in atoms]
    return sha256((json.dumps(native, indent=2, sort_keys=True) + "\n").encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Fm23ReviewedGeometryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/reviewed-geometry"
    ordinal: int
    native_pathway: str
    native_state_label: str
    atoms: tuple[GeometryAtomV1, ...]
    original_pdf_sha256: str = PDF_SHA256
    reviewed_projection_sha256: str = PROJECTION_SHA256
    coordinate_role: str = SOURCE_ROLE

    def __post_init__(self) -> None:
        if type(self.ordinal) is not int or not 1 <= self.ordinal <= 24:
            raise ValueError("reviewed geometry ordinal must retain the complete source order")
        pathway, label, count, pin = GEOMETRY_PINS[self.ordinal - 1]
        _tuple_of(self.atoms, GeometryAtomV1)
        if ((self.original_pdf_sha256, self.reviewed_projection_sha256, self.coordinate_role)
                != (PDF_SHA256, PROJECTION_SHA256, SOURCE_ROLE)
                or (self.native_pathway, self.native_state_label, len(self.atoms)) != (pathway, label, count)
                or native_atom_projection_sha256(self.atoms) != pin):
            raise ValueError("reviewed geometry changes exact source metadata, atom tokens or projection")


@dataclass(frozen=True, slots=True)
class Fm23ReviewedSourceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/reviewed-source"
    geometries: tuple[Fm23ReviewedGeometryV1, ...]
    original_pdf_sha256: str = PDF_SHA256
    original_pdf_bytes: int = PDF_BYTES
    reviewed_projection_sha256: str = PROJECTION_SHA256
    reviewed_projection_bytes: int = PROJECTION_BYTES
    coordinate_role: str = SOURCE_ROLE

    def __post_init__(self) -> None:
        _tuple_of(self.geometries, Fm23ReviewedGeometryV1, maximum=24)
        if (tuple(g.ordinal for g in self.geometries) != tuple(range(1, 25))
                or sum(len(g.atoms) for g in self.geometries) != 5994):
            raise ValueError("reviewed source requires all24 geometries and all5994 atom rows")
        if ((self.original_pdf_sha256, self.original_pdf_bytes, self.reviewed_projection_sha256,
             self.reviewed_projection_bytes, self.coordinate_role)
                != (PDF_SHA256, PDF_BYTES, PROJECTION_SHA256, PROJECTION_BYTES, SOURCE_ROLE)
                or type(self.original_pdf_bytes) is not int or type(self.reviewed_projection_bytes) is not int):
            raise ValueError("reviewed source changes its exact byte witnesses or projection role")
        for geometry in self.geometries:
            geometry.__post_init__()


@dataclass(frozen=True, slots=True)
class Fm23PreparationProtocolV1(CanonicalRecord):
    """Code-owned construction choices, distinct from an original paper/job."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/preparation-protocol"
    protocol_id: str = "rubisco-fm23.encounter-preparation.v1"
    original_pdf_sha256: str = PDF_SHA256
    reviewed_projection_sha256: str = PROJECTION_SHA256
    carbon_initial_tokens: tuple[str, ...] = CARBON_INITIAL
    oxygen_distance_tokens: tuple[tuple[str, ...], ...] = OXYGEN_TARGETS
    orientations: tuple[str, ...] = ORIENTATIONS
    mg_cutoff_token: str = "2.5"
    output_fraction_digits: int = 10
    rounding_rule: str = "PRINTED_HALF_QUANTUM_BOXES_WITH_OUTWARD80_DIGIT_SQRT_BOUNDS"
    approach_rule: str = "CARBON_CENTER_ON_SOURCE_C2_TO_OS1_DIRECTION"
    orientation_rule: str = "ORIGINAL_OO_AXIS_AND_PLUS90_ROTATION_ABOUT_APPROACH"
    constructed_role: str = NEW_ROLE

    def __post_init__(self) -> None:
        if ((self.protocol_id, self.original_pdf_sha256, self.reviewed_projection_sha256,
             self.carbon_initial_tokens, self.oxygen_distance_tokens, self.orientations,
             self.mg_cutoff_token, self.output_fraction_digits, self.rounding_rule,
             self.approach_rule, self.orientation_rule, self.constructed_role)
                != ("rubisco-fm23.encounter-preparation.v1", PDF_SHA256, PROJECTION_SHA256,
                    CARBON_INITIAL, OXYGEN_TARGETS, ORIENTATIONS, "2.5", 10,
                    "PRINTED_HALF_QUANTUM_BOXES_WITH_OUTWARD80_DIGIT_SQRT_BOUNDS",
                    "CARBON_CENTER_ON_SOURCE_C2_TO_OS1_DIRECTION",
                    "ORIGINAL_OO_AXIS_AND_PLUS90_ROTATION_ABOUT_APPROACH", NEW_ROLE)
                or type(self.output_fraction_digits) is not int):
            raise ValueError("preparation changes its frozen source, rules or construction choices")
        _tuple_of(self.carbon_initial_tokens, str, maximum=5)
        _tuple_of(self.oxygen_distance_tokens, tuple, maximum=5)
        for row in self.oxygen_distance_tokens:
            _tuple_of(row, str, maximum=7)
        _tuple_of(self.orientations, str, maximum=2)


@dataclass(frozen=True, slots=True)
class GeometricDistanceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/geometric-distance"
    indices_1based: tuple[int, int]
    center_angstrom: Decimal
    lower_angstrom: Decimal
    upper_angstrom: Decimal
    native_table_token: str | None = None

    def __post_init__(self) -> None:
        _tuple_of(self.indices_1based, int, maximum=2)
        if len(self.indices_1based) != 2 or any(not 1 <= i <= 512 for i in self.indices_1based):
            raise ValueError("distance requires bounded one-based atom indices")
        values = (self.center_angstrom, self.lower_angstrom, self.upper_angstrom)
        if (any(type(v) is not Decimal or not v.is_finite() for v in values)
                or not Decimal(0) <= self.lower_angstrom <= self.center_angstrom <= self.upper_angstrom):
            raise ValueError("distance values require finite ordered Decimal bounds")
        if self.native_table_token is not None:
            _token(self.native_table_token)

    @property
    def matches_native_rounding(self) -> bool | None:
        if self.native_table_token is None:
            return None
        with localcontext(_context()):
            value = Decimal(self.native_table_token)
            error = Decimal(10) ** value.as_tuple().exponent / 2
            return self.lower_angstrom <= value + error and self.upper_angstrom >= value - error


def distance_bounds(a: GeometryAtomV1, b: GeometryAtomV1) -> tuple[Decimal, Decimal, Decimal]:
    """Center, lower and upper norm, with outward printed-coordinate bounds."""
    if type(a) is not GeometryAtomV1 or type(b) is not GeometryAtomV1:
        raise ValueError("distance requires exact geometric atom records")
    with localcontext(_context()) as context:
        center2 = lower2 = upper2 = Decimal(0)
        for ta, tb in zip(a.coordinate_tokens, b.coordinate_tokens, strict=True):
            va, vb = Decimal(ta), Decimal(tb)
            delta = abs(va - vb)
            error = (Decimal(10) ** va.as_tuple().exponent + Decimal(10) ** vb.as_tuple().exponent) / 2
            center2 += delta * delta
            lower2 += max(Decimal(0), delta - error) ** 2
            upper2 += (delta + error) ** 2
        center = center2.sqrt()
        # sqrt is correctly rounded; expanding by one context ulp supplies
        # outward bounds, including when the exact root has infinitely many digits.
        lower = max(Decimal(0), lower2.sqrt().next_minus(context))
        upper = upper2.sqrt().next_plus(context)
        return center, lower, upper


def geometric_distance(atoms: tuple[GeometryAtomV1, ...], i: int, j: int,
                       native_token: str | None = None) -> GeometricDistanceV1:
    _tuple_of(atoms, GeometryAtomV1)
    if any(type(k) is not int or not 1 <= k <= len(atoms) for k in (i, j)):
        raise ValueError("distance index outside complete atom roster")
    return GeometricDistanceV1((i, j), *distance_bounds(atoms[i - 1], atoms[j - 1]), native_token)


@dataclass(frozen=True, slots=True)
class Fm23RoleMapV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/role-map"
    c2: int
    c3: int
    o3: int
    os1: int
    os2: int
    water_o: int
    mg: int

    def __post_init__(self) -> None:
        values = (self.c2, self.c3, self.o3, self.os1, self.os2, self.water_o, self.mg)
        if any(type(v) is not int or not 1 <= v <= 512 for v in values) or len(set(values)) != 7:
            raise ValueError("roles require seven distinct bounded one-based indices")

    def pairs(self) -> tuple[tuple[int, int], ...]:
        return ((self.os1, self.os2), (self.os1, self.c2), (self.c2, self.c3),
                (self.c3, self.o3), (self.c3, self.water_o))


@dataclass(frozen=True, slots=True)
class RoleCandidateCensusV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/role-candidate-census"
    carbon_count: int
    oxygen_count: int
    oo_pairs_screened: int
    directed_cc_pairs_screened: int
    cco_trials_screened: int
    gas_trials_screened: int
    water_trials_screened: int
    matching_oo: tuple[tuple[int, ...], ...]
    matching_cc: tuple[tuple[int, ...], ...]
    matching_cco: tuple[tuple[int, ...], ...]
    matching_gas: tuple[tuple[int, ...], ...]
    matching_complete: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        numbers = (self.carbon_count, self.oxygen_count, self.oo_pairs_screened,
                   self.directed_cc_pairs_screened, self.cco_trials_screened,
                   self.gas_trials_screened, self.water_trials_screened)
        if any(type(v) is not int or not 0 <= v <= MAXIMUM_CANDIDATE_TRIALS for v in numbers):
            raise ValueError("candidate census requires nonnegative integer denominators")
        for roster, width in zip((self.matching_oo, self.matching_cc, self.matching_cco,
                                 self.matching_gas, self.matching_complete), (2, 2, 3, 5, 6), strict=True):
            _tuple_of(roster, tuple, maximum=MAXIMUM_CANDIDATE_TRIALS)
            for row in roster:
                _tuple_of(row, int, maximum=width)
                if len(row) != width or any(not 1 <= i <= 512 for i in row):
                    raise ValueError("candidate roster changes its tuple shape")
        if (self.oo_pairs_screened != self.oxygen_count * (self.oxygen_count - 1) // 2
                or self.directed_cc_pairs_screened != self.carbon_count * (self.carbon_count - 1)
                or self.cco_trials_screened != len(self.matching_cc) * self.oxygen_count
                or self.gas_trials_screened != len(self.matching_cco) * len(self.matching_oo) * 2
                or self.water_trials_screened != len(self.matching_gas) * self.oxygen_count):
            raise ValueError("candidate census changes its complete screening denominators")


def infer_role_candidates(atoms: tuple[GeometryAtomV1, ...], targets: tuple[str, ...]
                          ) -> tuple[Fm23RoleMapV1, RoleCandidateCensusV1]:
    """Pure exhaustive geometric identification; refuses absent/nonunique maps.

    Target order is O-O, OS1-C2, C2-C3, C3-O3, C3-waterO. It is meaningful on
    synthetic atoms without admitting them as the reviewed scientific source.
    """
    _tuple_of(atoms, GeometryAtomV1)
    _tuple_of(targets, str, maximum=5)
    if len(targets) != 5:
        raise ValueError("five native distance constraints are required")
    for target in targets:
        _token(target)
    carbon = tuple(i + 1 for i, a in enumerate(atoms) if a.element == "C")
    oxygen = tuple(i + 1 for i, a in enumerate(atoms) if a.element == "O")
    magnesium = tuple(i + 1 for i, a in enumerate(atoms) if a.element == "Mg")
    if len(magnesium) != 1:
        raise ValueError("role map requires exactly one Mg")

    def bounded(trials: int) -> None:
        if trials > MAXIMUM_CANDIDATE_TRIALS:
            raise ValueError("geometric candidate stage exceeds its declared finite trial bound")

    bounded(len(oxygen) * (len(oxygen) - 1) // 2)
    bounded(len(carbon) * (len(carbon) - 1))

    def matches(i: int, j: int, target: str) -> bool:
        return geometric_distance(atoms, i, j, target).matches_native_rounding is True

    oo = tuple((i, j) for i, j in itertools.combinations(oxygen, 2) if matches(i, j, targets[0]))
    cc = tuple((i, j) for i in carbon for j in carbon if i != j and matches(i, j, targets[2]))
    bounded(len(cc) * len(oxygen))
    cco = tuple((i, j, k) for i, j in cc for k in oxygen if matches(j, k, targets[3]))
    bounded(len(cco) * len(oo) * 2)
    gas = tuple((i, j, k, g1, g2) for i, j, k in cco for left, right in oo
                for g1, g2 in ((left, right), (right, left))
                if k not in (g1, g2) and matches(g1, i, targets[1]))
    bounded(len(gas) * len(oxygen))
    complete = tuple((i, j, k, g1, g2, w) for i, j, k, g1, g2 in gas for w in oxygen
                     if w not in (k, g1, g2) and matches(j, w, targets[4]))
    census = RoleCandidateCensusV1(len(carbon), len(oxygen), len(oxygen) * (len(oxygen) - 1) // 2,
                                   len(carbon) * (len(carbon) - 1), len(cc) * len(oxygen),
                                   len(cco) * len(oo) * 2, len(gas) * len(oxygen), oo, cc, cco, gas, complete)
    if len(complete) != 1:
        raise ValueError(f"absent or ambiguous role map: {len(complete)} complete candidates; "
                         f"{len(oo)} gas pairs, {len(cc)} directed carbon pairs; "
                         f"complete tuples={complete}")
    return Fm23RoleMapV1(*complete[0], magnesium[0]), census


def _point(atom: GeometryAtomV1) -> tuple[Decimal, ...]:
    return tuple(Decimal(x) for x in atom.coordinate_tokens)


def _unit(values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    length = sum(v * v for v in values).sqrt()
    if length < Decimal("1e-20"):
        raise ValueError("degenerate encounter direction or molecular axis")
    return tuple(v / length for v in values)


def construct_encounter_atoms(atoms: tuple[GeometryAtomV1, ...], roles: Fm23RoleMapV1,
                             orientation: str, *, gas_distance: str = "3.1", gas_bond: str = "1.17"
                             ) -> tuple[GeometryAtomV1, ...]:
    """Generic source-coordinate copy and two declared linear CO2 orientations."""
    _tuple_of(atoms, GeometryAtomV1, maximum=509)
    if type(roles) is not Fm23RoleMapV1 or orientation not in ORIENTATIONS:
        raise ValueError("encounter construction requires a typed role map and declared orientation")
    expected = ((roles.c2, "C"), (roles.c3, "C"), (roles.o3, "O"), (roles.os1, "O"),
                (roles.os2, "O"), (roles.water_o, "O"), (roles.mg, "Mg"))
    if any(index > len(atoms) or atoms[index - 1].element != element for index, element in expected):
        raise ValueError("role map does not match the input atom roster")
    dist, bond = _token(gas_distance), _token(gas_bond)
    if dist <= 0 or bond <= 0:
        raise ValueError("gas distance and bond must be positive")
    with localcontext(_context()):
        c2, os1, os2 = (_point(atoms[i - 1]) for i in (roles.c2, roles.os1, roles.os2))
        approach = _unit(tuple(a - b for a, b in zip(os1, c2, strict=True)))
        axis = _unit(tuple(a - b for a, b in zip(os2, os1, strict=True)))
        if orientation == "rotated-axis":
            cross = (approach[1] * axis[2] - approach[2] * axis[1],
                     approach[2] * axis[0] - approach[0] * axis[2],
                     approach[0] * axis[1] - approach[1] * axis[0])
            dot = sum(a * b for a, b in zip(approach, axis, strict=True))
            axis = _unit(tuple(a + dot * b for a, b in zip(cross, approach, strict=True)))
        center = tuple(a + dist * b for a, b in zip(c2, approach, strict=True))
        points = (center,) + tuple(tuple(a + sign * bond * b for a, b in zip(center, axis, strict=True))
                                   for sign in (1, -1))
        gas = tuple(GeometryAtomV1(element, tuple(format(v, ".10f") for v in point))
                    for element, point in zip(("C", "O", "O"), points, strict=True))
    return tuple(a for i, a in enumerate(atoms, 1) if i not in (roles.os1, roles.os2)) + gas


@dataclass(frozen=True, slots=True)
class NativeDistanceCheckV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/native-distance-check"
    state_ordinal: int
    role: str
    distance: GeometricDistanceV1

    def __post_init__(self) -> None:
        if (type(self.state_ordinal) is not int or not 1 <= self.state_ordinal <= 7
                or self.role not in (*FIELDS, "C-O_left", "C-O_right")
                or type(self.distance) is not GeometricDistanceV1 or self.distance.native_table_token is None):
            raise ValueError("native distance check changes its declared state/role")


def _initial(source: Fm23ReviewedGeometryV1) -> Fm23RoleMapV1:
    if type(source) is not Fm23ReviewedGeometryV1 or source.ordinal != 1:
        raise ValueError("encounter preparation requires the exact first reviewed FM23 state")
    source.__post_init__()
    roles, _ = infer_role_candidates(source.atoms, tuple(row[0] for row in OXYGEN_TARGETS))
    if roles != Fm23RoleMapV1(158, 159, 165, 162, 168, 209, 156):
        raise ValueError("reviewed initial geometry changes the source-identified atom roles")
    return roles


@dataclass(frozen=True, slots=True)
class Fm23ScaffoldV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/gas-free-scaffold"
    parent: Fm23ReviewedGeometryV1
    source_indices_1based: tuple[int, ...]
    atoms: tuple[GeometryAtomV1, ...]
    coordinate_role: str = "UNCHANGED246_ATOM_SOURCE_SCAFFOLD_NOT_ISOLATED_STATIONARY_STATE"

    def __post_init__(self) -> None:
        roles = _initial(self.parent)
        indices = tuple(i for i in range(1, 249) if i not in (roles.os1, roles.os2))
        _tuple_of(self.source_indices_1based, int)
        _tuple_of(self.atoms, GeometryAtomV1)
        if (self.source_indices_1based != indices or self.atoms != tuple(self.parent.atoms[i - 1] for i in indices)
                or self.coordinate_role != "UNCHANGED246_ATOM_SOURCE_SCAFFOLD_NOT_ISOLATED_STATIONARY_STATE"):
            raise ValueError("scaffold changes unchanged native tokens, source mapping or role")


def _carbon_checks(atoms: tuple[GeometryAtomV1, ...], roles: Fm23RoleMapV1
                   ) -> tuple[NativeDistanceCheckV1, ...]:
    kept = tuple(i for i in range(1, 249) if i not in (roles.os1, roles.os2))
    remap = {old: new for new, old in enumerate(kept, 1)}
    definitions = (("gas_atom-C2", (247, remap[roles.c2]), CARBON_INITIAL[0]),
                   ("C-O_left", (247, 248), CARBON_INITIAL[1]),
                   ("C-O_right", (247, 249), CARBON_INITIAL[1]),
                   ("C2-C3", (remap[roles.c2], remap[roles.c3]), CARBON_INITIAL[2]),
                   ("C3-O3", (remap[roles.c3], remap[roles.o3]), CARBON_INITIAL[3]),
                   ("C3-waterO", (remap[roles.c3], remap[roles.water_o]), CARBON_INITIAL[4]))
    return tuple(NativeDistanceCheckV1(1, role, geometric_distance(atoms, *pair, token))
                 for role, pair, token in definitions)


@dataclass(frozen=True, slots=True)
class Fm23ConstructedPoseV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/constructed-encounter-pose"
    parent: Fm23ReviewedGeometryV1
    protocol: Fm23PreparationProtocolV1
    orientation: str
    atoms: tuple[GeometryAtomV1, ...]
    carbon_checks: tuple[NativeDistanceCheckV1, ...]
    gas_scaffold_distances: tuple[GeometricDistanceV1, ...]
    coordinate_role: str = NEW_ROLE
    native_carbon_reproduction: bool = False

    def __post_init__(self) -> None:
        if type(self.protocol) is not Fm23PreparationProtocolV1:
            raise ValueError("pose requires the exact typed preparation protocol")
        self.protocol.__post_init__()
        roles = _initial(self.parent)
        _tuple_of(self.atoms, GeometryAtomV1)
        _tuple_of(self.carbon_checks, NativeDistanceCheckV1, maximum=6)
        _tuple_of(self.gas_scaffold_distances, GeometricDistanceV1, maximum=738)
        if (self.orientation not in ORIENTATIONS or self.coordinate_role != NEW_ROLE
                or self.native_carbon_reproduction is not False
                or self.atoms != construct_encounter_atoms(self.parent.atoms, roles, self.orientation)
                or self.carbon_checks != _carbon_checks(self.atoms, roles)):
            raise ValueError("constructed pose changes exact source, new atom tokens, orientation or carbon checks")
        failed = tuple(check.role for check in self.carbon_checks if check.distance.matches_native_rounding is False)
        if failed != ("C2-C3", "C3-O3", "C3-waterO"):
            raise ValueError("constructed pose must preserve the three native carbon reproduction failures")
        expected = tuple(geometric_distance(self.atoms, gas, support)
                         for gas in (247, 248, 249) for support in range(1, 247))
        if self.gas_scaffold_distances != expected:
            raise ValueError("pose changes complete738 gas/scaffold geometric observations")


@dataclass(frozen=True, slots=True)
class Fm23PreparationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/fm23/encounter-preparation"
    source: Fm23ReviewedSourceV1
    protocol: Fm23PreparationProtocolV1
    source_identity: ObjectIdentity
    protocol_identity: ObjectIdentity
    roles: Fm23RoleMapV1
    candidate_census: RoleCandidateCensusV1
    oxygen_checks: tuple[NativeDistanceCheckV1, ...]
    mg_oxygen_distances: tuple[GeometricDistanceV1, ...]
    mg_neighbors_under_cutoff: tuple[int, ...]
    scaffold: Fm23ScaffoldV1
    poses: tuple[Fm23ConstructedPoseV1, ...]
    limitations: tuple[str, ...] = LIMITATIONS

    def __post_init__(self) -> None:
        if type(self.source) is not Fm23ReviewedSourceV1 or type(self.protocol) is not Fm23PreparationProtocolV1:
            raise ValueError("preparation requires closed source and protocol records")
        self.source.__post_init__()
        self.protocol.__post_init__()
        if (type(self.source_identity) is not ObjectIdentity or type(self.protocol_identity) is not ObjectIdentity
                or self.source_identity != ObjectIdentity.from_record("rubisco-fm23.reviewed-source", self.source)
                or self.protocol_identity != ObjectIdentity.from_record(self.protocol.protocol_id, self.protocol)):
            raise ValueError("preparation changes source or protocol canonical identities")
        roles, census, checks, mg_distances, neighbors = _assessment(self.source, self.protocol)
        if ((self.roles, self.candidate_census, self.oxygen_checks, self.mg_oxygen_distances,
             self.mg_neighbors_under_cutoff) != (roles, census, checks, mg_distances, neighbors)
                or self.limitations != LIMITATIONS):
            raise ValueError("preparation changes its source-bound census, checks, Mg roles or limits")
        _tuple_of(self.oxygen_checks, NativeDistanceCheckV1, maximum=35)
        _tuple_of(self.mg_oxygen_distances, GeometricDistanceV1, maximum=40)
        _tuple_of(self.mg_neighbors_under_cutoff, int, maximum=40)
        _tuple_of(self.poses, Fm23ConstructedPoseV1, maximum=2)
        if (type(self.scaffold) is not Fm23ScaffoldV1 or self.scaffold.parent != self.source.geometries[0]
                or tuple(p.orientation for p in self.poses) != ORIENTATIONS
                or any(p.parent != self.source.geometries[0] or p.protocol != self.protocol for p in self.poses)):
            raise ValueError("preparation omits, reorders or changes its source-bound scaffold/pose roster")
        self.scaffold.__post_init__()
        for pose in self.poses:
            pose.__post_init__()


def _assessment(source: Fm23ReviewedSourceV1, protocol: Fm23PreparationProtocolV1
                ) -> tuple[Fm23RoleMapV1, RoleCandidateCensusV1, tuple[NativeDistanceCheckV1, ...],
                           tuple[GeometricDistanceV1, ...], tuple[int, ...]]:
    initial = source.geometries[0]
    roles, census = infer_role_candidates(initial.atoms, tuple(row[0] for row in protocol.oxygen_distance_tokens))
    if roles != _initial(initial):
        raise ValueError("source role inference differs")
    checks = tuple(NativeDistanceCheckV1(g.ordinal, role, geometric_distance(g.atoms, *pair, tokens[n]))
                   for n, g in enumerate(source.geometries[:7])
                   for role, pair, tokens in zip(FIELDS, roles.pairs(), protocol.oxygen_distance_tokens, strict=True))
    if not all(c.distance.matches_native_rounding for c in checks):
        raise ValueError("source fails one of35 seven-state native oxygen checks")
    mg = tuple(geometric_distance(initial.atoms, roles.mg, i) for i, atom in enumerate(initial.atoms, 1)
               if atom.element == "O" and i not in (roles.os1, roles.os2))
    neighbors = tuple(d.indices_1based[1] for d in mg if d.center_angstrom < Decimal(protocol.mg_cutoff_token))
    return roles, census, checks, mg, neighbors


def decode_fm23_projection(oxygen_si_pdf: bytes, reviewed_inspection_json: bytes) -> Fm23ReviewedSourceV1:
    """Hash-first admit two exact originals; no filesystem, PDF parser or I/O.

    The second input is a reviewed derivative, not a second original source.
    Both bytes are mandatory; the source record constructors additionally seal
    all individual projections so coherent manual token substitutions refuse.
    """
    for data, size, pin in ((oxygen_si_pdf, PDF_BYTES, PDF_SHA256),
                            (reviewed_inspection_json, PROJECTION_BYTES, PROJECTION_SHA256)):
        if type(data) is not bytes or len(data) > MAXIMUM_INPUT_BYTES or len(data) != size or sha256(data).hexdigest() != pin:
            raise ValueError("FM23 exact bounded original PDF/reviewed projection bytes differ")

    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate reviewed projection key")
            result[key] = value
        return result

    projection = json.loads(reviewed_inspection_json, object_pairs_hook=pairs,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite projection")))
    raw = projection.get("geometries")
    if type(raw) is not list or len(raw) != 24:
        raise ValueError("reviewed projection requires complete24 geometry census")
    geometries = []
    for row in raw:
        if type(row) is not dict or type(row.get("atoms")) is not list:
            raise ValueError("reviewed geometry has invalid native row shape")
        atoms = []
        for atom in row["atoms"]:
            if (type(atom) is not dict or set(atom) != {"element", "xyz_native_decimal_tokens"}
                    or type(atom["xyz_native_decimal_tokens"]) is not list):
                raise ValueError("reviewed atom changes native projection fields")
            atoms.append(GeometryAtomV1(atom["element"], tuple(atom["xyz_native_decimal_tokens"])))
        geometry = Fm23ReviewedGeometryV1(row["ordinal"], row["native_pathway"], row["native_state_label"],
                                         tuple(atoms), PDF_SHA256, PROJECTION_SHA256)
        if (row.get("native_header_atom_count") != len(atoms)
                or row.get("projected_atom_count") != len(atoms)
                or row.get("atom_projection_sha256") != native_atom_projection_sha256(geometry.atoms)):
            raise ValueError("reviewed geometry differs from its full native projection binding")
        geometries.append(geometry)
    return Fm23ReviewedSourceV1(tuple(geometries), PDF_SHA256, PDF_BYTES,
                               PROJECTION_SHA256, PROJECTION_BYTES)


def prepare_fm23_encounters(source: Fm23ReviewedSourceV1,
                           protocol: Fm23PreparationProtocolV1 | None = None) -> Fm23PreparationV1:
    """Produce the complete exposed geometry preparation, with failed checks."""
    if type(source) is not Fm23ReviewedSourceV1:
        raise ValueError("preparation requires the exact reviewed source")
    source.__post_init__()
    protocol = Fm23PreparationProtocolV1() if protocol is None else protocol
    if type(protocol) is not Fm23PreparationProtocolV1:
        raise ValueError("preparation requires the exact typed protocol")
    protocol.__post_init__()
    roles, census, checks, mg, neighbors = _assessment(source, protocol)
    initial = source.geometries[0]
    indices = tuple(i for i in range(1, 249) if i not in (roles.os1, roles.os2))
    scaffold = Fm23ScaffoldV1(initial, indices, tuple(initial.atoms[i - 1] for i in indices))
    poses = []
    for orientation in ORIENTATIONS:
        atoms = construct_encounter_atoms(initial.atoms, roles, orientation)
        distances = tuple(geometric_distance(atoms, gas, support)
                          for gas in (247, 248, 249) for support in range(1, 247))
        poses.append(Fm23ConstructedPoseV1(initial, protocol, orientation, atoms, _carbon_checks(atoms, roles), distances))
    return Fm23PreparationV1(source, protocol,
                            ObjectIdentity.from_record("rubisco-fm23.reviewed-source", source),
                            ObjectIdentity.from_record(protocol.protocol_id, protocol), roles, census,
                            checks, mg, neighbors, scaffold, tuple(poses))
