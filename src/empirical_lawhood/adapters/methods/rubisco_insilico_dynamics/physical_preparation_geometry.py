# SPDX-License-Identifier: MPL-2.0
"""Independent retained-input geometry diagnostics, never physical admission.

The caller authenticates original records/receipts. This PURE owner reads raw
Amber coordinates and tables, without producer enumeration or native imports.
All arithmetic uses exact lexical values. No returned native state or force is
inferred from an input file, source LJ diagnostic, or completed preparation.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
import re
from typing import ClassVar
from types import FunctionType

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, validate_sha256, validate_stable_id,
)

from . import contracts as c
from .amber_parameters import assigned_census, assigned_census_supported_inactive14, read_prmtop
from .preparation_integrity import PreparationIntegrity, read_heavy_pdb


SOURCE_PINS = (
    ("openmm/app/internal/amber_file_parser.py", "73525b039d6ee4d83978445902dfab7059160fc541403481e65e23b34520e9a3"),
    ("parmed/amber/_amberparm.py", "be23837b91fdda1c12165ea5a29000a157ef2a56086ca92e334540ddd5adc70d"),
    ("parmed/amber/asciicrd.py", "f024643a2b9b89755d2a60604a2a84b91a3cad4c899469a4e632cb59afd34496"),
)
DESCRIPTION = (
    "Exact lexical ASCII coordinates/orthorhombic box and full raw atom origins; "
    "complete logical unordered pair and bonded-row census; raw directed exclusions "
    "union, zero placeholders, selected OpenMM k>0/l>0 active1-4 policy without "
    "deduplicating active rows; exact Fraction source A/r12-B/r6 sign diagnostics; "
    "source-derived cell search bound, periodic ordinary/unwrapped1-4 distances; "
    "mathematical singularities separate from finite contacts; no geometry admission, "
    "PME total/force, relaxation, protonation/chemistry adequacy or native coverage."
)
METHOD = ObjectIdentity("method.rubisco-dynamics.physical-preparation-geometry",
    "empirical-lawhood/rubisco-insilico-dynamics/physical-preparation-geometry-method",
    "1.0.0", sha256(canonical_json_bytes((DESCRIPTION, SOURCE_PINS))).hexdigest())
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[EeDd][+-]?[0-9]+)?\Z")
PAIR_CLASSES = ("ordinary", "excluded-non14", "active14")
BONDED_COUNTS = ("bonds","angles","dihedrals","bonds-zero-leg","angles-zero-leg",
                 "dihedrals-zero-leg","dihedrals-undefined-plane")


class UnsupportedGeometry(ValueError):
    """A retained format or operand needs a separately assessed interpretation."""


def _fraction(token):
    if type(token) is not str or not _NUMBER.fullmatch(token):
        raise ValueError("malformed/nonfinite retained coordinate token")
    value = Decimal(token.replace("D", "E").replace("d", "e"))
    if not value.is_finite() or abs(value.as_tuple().exponent) > 1000:
        raise ValueError("unsupported coordinate exponent")
    return Fraction(value)


def _rational(value):
    return (value.numerator, value.denominator)


def _integer(value):
    return type(value) is int and value >= 0


def _validate_rational(value):
    if type(value) is not tuple or len(value) != 2 or any(type(number) is not int for number in value) or value[1] <= 0 or _rational(Fraction(*value)) != value:
        raise ValueError("geometry rational must retain exact reduced integer operands")
    return Fraction(*value)


def read_inpcrd(text, atom_count):
    """Strict teLeap coordinate-only ASCII branch; preserve lexical text upstream.

    The selected readers use six fixed-width 12-character fields per row.
    Velocities, NetCDF, ambiguous tiny systems and triclinic boxes are outside
    this successor's prospective interpretation, rather than guessed.
    """
    if type(text) is not str or not text.isascii():
        raise UnsupportedGeometry("ASCII inpcrd required")
    if not _integer(atom_count) or atom_count < 3:
        raise UnsupportedGeometry("tiny/ambiguous coordinate branch unsupported")
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) < 2:
        raise ValueError("missing inpcrd header")
    header = lines[1].split()
    if not 1 <= len(header) <= 2 or not re.fullmatch(r"[0-9]+", header[0]) or int(header[0]) != atom_count:
        raise ValueError("inpcrd full atom count differs")
    time = None if len(header) == 1 else _fraction(header[1])
    rows = (atom_count+1)//2
    if len(lines) in (2*rows+2, 2*rows+3):
        raise UnsupportedGeometry("velocity restart requires separate interpretation")
    if len(lines) != rows+3:
        raise ValueError("complete coordinate-only periodic inpcrd rows required")
    values = []
    for ordinal, line in enumerate(lines[2:2+rows]):
        count = min(6, 3*atom_count-6*ordinal)
        if len(line) < 12*count or line[12*count:].strip():
            raise ValueError("inpcrd coordinate row omitted/extra fields")
        values.extend(_fraction(line[index:index+12].strip()) for index in range(0, 12*count, 12))
    line = lines[-1]
    if len(line) < 72 or line[72:].strip():
        raise ValueError("inpcrd complete six-field box required")
    box = tuple(_fraction(line[index:index+12].strip()) for index in range(0,72,12))
    if any(value <= 0 for value in box[:3]) or any(not 0 < value < 180 for value in box[3:]):
        raise ValueError("nonpositive/singular periodic box")
    if box[3:] != (90,90,90):
        raise UnsupportedGeometry("nonorthorhombic box requires separate interpretation")
    return tuple(tuple(values[index:index+3]) for index in range(0,len(values),3)), box[:3], time


def interaction_partition(sections, census):
    """Retain every slot/row; unique mathematical pairs do not erase raw rows."""
    n = census["term_census"]["atoms"]
    excluded, directed, offset = set(), set(), 0
    sentinel_count = 0
    for first, count in enumerate(census["exclusion_counts"]):
        for value in census["exclusions"][offset:offset+count]:
            if value == 0:
                sentinel_count += 1
                continue
            second = value-1
            if first == second or (first,second) in directed:
                raise ValueError("self/duplicate directed source exclusion")
            directed.add((first,second))
            excluded.add(tuple(sorted((first,second))))
        offset += count
    active = {}
    ignored = improper = zero_index = 0
    for name in ("DIHEDRALS_INC_HYDROGEN", "DIHEDRALS_WITHOUT_HYDROGEN"):
        for row in census["indexed_bonded_terms"][name]:
            ignored += row[2] < 0
            improper += row[3] < 0
            zero_index += row[2] == 0 or row[3] == 0
            # Exact selected OpenMM app parser condition, including zero-index.
            if row[2] <= 0 or row[3] <= 0:
                continue
            pair = tuple(sorted((row[0]//3,row[3]//3)))
            if pair[0] == pair[1] or pair in active:
                raise ValueError("self/duplicate active1-4 source exception")
            parameter = row[-1]-1
            active[pair] = (Fraction(sections["SCEE_SCALE_FACTOR"][parameter]),
                            Fraction(sections["SCNB_SCALE_FACTOR"][parameter]))
    counts = (n*(n-1)//2-len(excluded|active.keys()),len(excluded-active.keys()),len(active))
    return excluded, active, counts, (len(census["exclusions"]),sentinel_count,len(directed),ignored,improper,zero_index)


def _sub(left,right):
    return tuple(a-b for a,b in zip(left,right,strict=True))


def _norm2(vector):
    return sum(value*value for value in vector)


def _cross(left,right):
    return (left[1]*right[2]-left[2]*right[1],left[2]*right[0]-left[0]*right[2],left[0]*right[1]-left[1]*right[0])


def _distance2(left,right,box=None):
    difference = _sub(left,right)
    if box is not None:
        difference = tuple(value-length*((value/length+Fraction(1,2))//1) for value,length in zip(difference,box,strict=True))
    return _norm2(difference)


def bonded_geometry(census,coordinates):
    counts = Counter()
    for name,rows in census["indexed_bonded_terms"].items():
        category = name.split("_")[0].lower()
        for row in rows:
            points = tuple(coordinates[abs(index)//3] for index in row[:-1])
            counts[category] += 1
            vectors = tuple(_sub(right,left) for left,right in zip(points,points[1:]))
            if any(_norm2(vector) == 0 for vector in vectors):
                counts[category+"-zero-leg"] += 1
            if len(points) == 4 and any(_norm2(_cross(left,right)) == 0 for left,right in zip(vectors,vectors[1:])):
                counts["dihedrals-undefined-plane"] += 1
    return tuple((name,counts[name]) for name in BONDED_COUNTS)


def _box_join(sections,box):
    raw = sections.get("BOX_DIMENSIONS",())
    if sections["POINTERS"][27] != 1 or len(raw) != 4:
        raise UnsupportedGeometry("explicit orthorhombic Amber topology box required")
    if raw[0] != 90:
        raise UnsupportedGeometry("Amber topology nonorthorhombic beta")
    # Different fixed-width serializations enclose a shared pre-rounding value.
    for wanted,got in zip(raw[1:],box,strict=True):
        quantum = Fraction(Decimal((0,(1,),wanted.as_tuple().exponent)))
        if abs(Fraction(wanted)-got) > quantum/2+Fraction(1,20_000_000):
            raise ValueError("topology/restart box serialization cells do not join")


def _origin_join(census,coordinates,pdb,origin):
    heavy = read_heavy_pdb(pdb)
    by_key = {(row["chain"],row["position"],row["atom"]):row for row in heavy}
    realization = origin.get("amber_realization") if type(origin) is dict else None
    rows = realization.get("atoms") if type(realization) is dict else None
    n = len(coordinates)
    if type(rows) is not list or len(rows) != n:
        raise ValueError("full original Amber atom mapping missing")
    joined, residue, intervals = set(), 0, [None]*3
    for index,row in enumerate(rows):
        while residue+1 < len(census["residue_starts"]) and index+1 >= census["residue_starts"][residue+1]:
            residue += 1
        if type(row) is not dict or type(row.get("amber_atom_index")) is not int or row["amber_atom_index"] != index or row.get("amber_residue_index") != residue or row.get("atom") != census["atom_names"][index] or row.get("residue_name") != census["residue_names"][residue]:
            raise ValueError("original full atom order/residue identity differs")
        key = (row.get("chain"),row.get("position"),row.get("atom"))
        if key not in by_key:
            if row.get("status") not in ("DECLARED_AMBER_ADDED_HYDROGEN","DECLARED_ADDED_SOLVENT_OR_NEUTRALIZING_ION"):
                raise ValueError("unmapped original/constructed heavy atom")
            if row.get("status") == "DECLARED_AMBER_ADDED_HYDROGEN" and census["atomic_numbers"][index] != 1:
                raise ValueError("declared hydrogen has another element")
            continue
        actual = by_key[key]
        if key in joined or row.get("status") != "REALIZED_COMPLETE_PREPARATION_ATOM" or row.get("source_origin") is None:
            raise ValueError("duplicate/missing complete-heavy origin")
        element = dict(C=6,N=7,O=8,P=15,S=16,MG=12,NA=11,CL=17).get(actual["element"])
        if census["atomic_numbers"][index] != element or actual["component"] != row["residue_name"] and (actual["component"],row["residue_name"]) != ("HOH","WAT"):
            raise ValueError("complete-heavy component/element differs")
        joined.add(key)
        for axis in range(3):
            delta = coordinates[index][axis]-Fraction(actual["xyz"][axis])
            # PDB printed value is the actual teLeap input. Restart7 decimals
            # add only its own half quantum; no physical movement tolerance.
            low,high = delta-Fraction(1,20_000_000),delta+Fraction(1,20_000_000)
            if intervals[axis] is not None:
                low,high = max(low,intervals[axis][0]),min(high,intervals[axis][1])
            if low > high:
                raise ValueError("heavy coordinates have no shared serialization translation")
            intervals[axis] = (low,high)
    if joined != set(by_key):
        raise ValueError("inpcrd drops complete original heavy/PDB denominator")
    return len(joined),tuple((_rational(low),_rational(high)) for low,high in intervals)


def _cell_radius(census,sections):
    occupied = set(sections["ATOM_TYPE_INDEX"])
    ratios = []
    ntype = sections["POINTERS"][1]
    for first in occupied:
        for second in occupied:
            slot = census["nonbonded_matrix"][(first-1)*ntype+second-1]-1
            a,b = Fraction(census["lj_a"][slot]),Fraction(census["lj_b"][slot])
            if bool(a) != bool(b):
                raise UnsupportedGeometry("mixed-zero LJ coefficient pair needs separate interpretation")
            if a:
                ratios.append(a/b)
    maximum = max(ratios,default=Fraction(0))
    radius = 1
    while radius**6 < maximum:
        radius *= 2
    low,high = radius//2,radius
    while high-low > 1:
        middle = (low+high)//2
        if middle**6 >= maximum: high = middle
        else: low = middle
    return high


@dataclass(frozen=True,slots=True)
class GeometryDiagnostic(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/geometry-diagnostic"
    atom_count: int
    box_lengths_angstrom: tuple[tuple[int,int], ...]
    time_picosecond: tuple[int,int] | None
    heavy_atom_count: int
    common_translation_intervals: tuple[tuple[tuple[int,int],tuple[int,int]], ...]
    pair_counts: tuple[tuple[str,int], ...]
    raw_interaction_counts: tuple[int, ...]
    bonded_counts: tuple[tuple[str,int], ...]
    search_radius_angstrom: int
    ordinary_candidate_count: int
    positive_lj_counts: tuple[tuple[str,int], ...]
    positive_lj_census_sha256: str
    coincident_unwrapped_pair_count: int
    singular_interacting_pair_count: int
    maximum_lj_pair: tuple[int,int,str,int,tuple[int,int],tuple[int,int]] | None
    hard_geometry_disposition: A
    geometry_adequacy: A = A.UNEVALUABLE
    force_adequacy: A = A.UNEVALUABLE
    relaxation_adequacy: A = A.UNEVALUABLE
    chemical_adequacy: A = A.UNEVALUABLE
    interpretation: str = "DERIVED_RETAINED_LEXICAL_INPUT_NOT_OBSERVED_NATIVE_STATE_OR_TOTAL_ENERGY"

    def __post_init__(self):
        values = (self.atom_count,self.heavy_atom_count,self.search_radius_angstrom,self.ordinary_candidate_count,
                  self.coincident_unwrapped_pair_count,self.singular_interacting_pair_count)+self.raw_interaction_counts
        if any(not _integer(value) for value in values) or self.atom_count < 3 or self.heavy_atom_count <= 0 or self.search_radius_angstrom <= 0:
            raise ValueError("geometry diagnostics require exact nonnegative full counts")
        if self.heavy_atom_count > self.atom_count or len(self.raw_interaction_counts) != 6:
            raise ValueError("geometry full atom/interaction census differs")
        if type(self.box_lengths_angstrom) is not tuple or len(self.box_lengths_angstrom) != 3 or any(_validate_rational(value) <= 0 for value in self.box_lengths_angstrom):
            raise ValueError("geometry exact positive box required")
        if self.time_picosecond is not None: _validate_rational(self.time_picosecond)
        if type(self.common_translation_intervals) is not tuple or len(self.common_translation_intervals) != 3 or any(_validate_rational(low) > _validate_rational(high) for low,high in self.common_translation_intervals):
            raise ValueError("geometry full serialization translation intervals differ")
        if tuple(name for name,_ in self.bonded_counts) != BONDED_COUNTS or any(not _integer(count) for _,count in self.bonded_counts):
            raise ValueError("geometry full bonded row census differs")
        bonded = dict(self.bonded_counts)
        if any(bonded[name+"-zero-leg"] > bonded[name] for name in ("bonds","angles","dihedrals")) or bonded["dihedrals-undefined-plane"] > bonded["dihedrals"]:
            raise ValueError("geometry singular rows exceed original bonded census")
        if tuple(name for name,_ in self.pair_counts) != PAIR_CLASSES or any(not _integer(number) for _,number in self.pair_counts) or sum(number for _,number in self.pair_counts) != self.atom_count*(self.atom_count-1)//2:
            raise ValueError("geometry complete logical pair partition differs")
        if tuple(name for name,_ in self.positive_lj_counts) != ("ordinary","active14") or any(not _integer(number) or number > dict(self.pair_counts)[name] for name,number in self.positive_lj_counts):
            raise ValueError("source-positive pair census differs")
        validate_sha256(self.positive_lj_census_sha256)
        if self.ordinary_candidate_count > dict(self.pair_counts)["ordinary"] or dict(self.positive_lj_counts)["ordinary"] > self.ordinary_candidate_count or self.singular_interacting_pair_count > dict(self.pair_counts)["ordinary"]+dict(self.pair_counts)["active14"] or self.coincident_unwrapped_pair_count > self.atom_count*(self.atom_count-1)//2:
            raise ValueError("geometry evaluated/singular pairs exceed complete denominator")
        if bool(sum(count for _,count in self.positive_lj_counts)) != (self.maximum_lj_pair is not None):
            raise ValueError("geometry maximum omits or invents positive pair")
        if self.maximum_lj_pair is not None:
            first,second,category,slot,distance2,energy = self.maximum_lj_pair
            if not _integer(first) or not _integer(second) or not first < second < self.atom_count or category not in ("ordinary","active14") or not _integer(slot) or slot == 0 or _validate_rational(distance2) <= 0 or _validate_rational(energy) <= 0:
                raise ValueError("geometry maximum pair operands differ")
        hard = self.coincident_unwrapped_pair_count or self.singular_interacting_pair_count or dict(self.bonded_counts)["bonds-zero-leg"]
        if self.hard_geometry_disposition is not (A.FALSIFIED if hard else A.SATISFIED):
            raise ValueError("hard singularity disposition differs from complete counts")
        if any(value is not A.UNEVALUABLE for value in (self.geometry_adequacy,self.force_adequacy,self.relaxation_adequacy,self.chemical_adequacy)) or self.interpretation != "DERIVED_RETAINED_LEXICAL_INPUT_NOT_OBSERVED_NATIVE_STATE_OR_TOTAL_ENERGY":
            raise ValueError("input geometry diagnostic cannot establish physical adequacy")


def diagnose_geometry(raw_prmtop,raw_inpcrd,heavy_pdb,origins):
    sections = read_prmtop(raw_prmtop)
    census = assigned_census(sections)
    coordinates,box,time = read_inpcrd(raw_inpcrd,census["term_census"]["atoms"])
    _box_join(sections,box)
    heavy_count,translation = _origin_join(census,coordinates,heavy_pdb,origins)
    excluded,active,pair_counts,raw_counts = interaction_partition(sections,census)
    bonded = bonded_geometry(census,coordinates)
    radius = _cell_radius(census,sections)
    cells = tuple(max(1,int(length//radius)) for length in box)
    widths = tuple(length/count for length,count in zip(box,cells,strict=True))
    grid = defaultdict(list)
    positive = Counter()
    digest = sha256()
    candidates = singular = 0
    maximum = None
    ntype = sections["POINTERS"][1]
    types = sections["ATOM_TYPE_INDEX"]

    def assess_pair(first,second,distance2,category,scale=Fraction(1)):
        nonlocal singular,maximum
        slot = census["nonbonded_matrix"][(types[first]-1)*ntype+types[second]-1]-1
        a,b = Fraction(census["lj_a"][slot]),Fraction(census["lj_b"][slot])
        if distance2 == 0:
            if a or b or census["charges_scaled"][first]*census["charges_scaled"][second]:
                singular += 1
            return
        if not a or a <= b*distance2**3:
            return
        energy = (a/distance2**6-b/distance2**3)/scale
        row = (first,second,category,slot+1,_rational(distance2),_rational(energy))
        encoded = canonical_json_bytes(row)
        digest.update(len(encoded).to_bytes(8,"big")); digest.update(encoded)
        positive[category] += 1
        if maximum is None or energy > Fraction(*maximum[-1]):
            maximum = row

    for second,xyz in enumerate(coordinates):
        key = tuple(int((value%length)//width) for value,length,width in zip(xyz,box,widths,strict=True))
        neighbors = {tuple((k+d)%count for k,d,count in zip(key,delta,cells,strict=True)) for delta in product((-1,0,1),repeat=3)}
        # Sorting the finite neighbor census makes diagnostic bytes independent
        # of hash/set traversal. There is no all-pair array or accumulated rows.
        for first in sorted(first for neighbor in neighbors for first in grid.get(neighbor,())):
            pair = (first,second)
            if pair in excluded or pair in active:
                continue
            candidates += 1
            assess_pair(first,second,_distance2(coordinates[first],xyz,box),"ordinary")
        grid[key].append(second)
    for (first,second),(_,scnb) in sorted(active.items()):
        assess_pair(first,second,_distance2(coordinates[first],coordinates[second]),"active14",scnb)
    occurrences = Counter(coordinates)
    coincident = sum(count*(count-1)//2 for count in occurrences.values())
    hard = coincident or singular or dict(bonded)["bonds-zero-leg"]
    return GeometryDiagnostic(len(coordinates),tuple(_rational(value) for value in box),None if time is None else _rational(time),
        heavy_count,translation,tuple(zip(PAIR_CLASSES,pair_counts,strict=True)),raw_counts,bonded,radius,candidates,
        tuple((name,positive[name]) for name in ("ordinary","active14")),digest.hexdigest(),coincident,singular,maximum,
        A.FALSIFIED if hard else A.SATISFIED)


SUPPORTED_INACTIVE14_DESCRIPTION = DESCRIPTION + (
    " Additive raw-inactive14-support/1.0.0 complete scale-slot/term checks: "
    "inactive/unused zero factors permitted, every active factor positive, "
    "all negatives and selected ParmEd/OpenMM endpoint activation differences refused."
)
SUPPORTED_INACTIVE14_SOURCE_PINS = SOURCE_PINS + (
    ("parmed/topologyobjects.py", "6ffac900b2f177ca64e2cf701a0b0bcf6301c42e3d2a98bc3d4995eee12250b8"),
    ("parmed/structure.py", "29bd54bb808e5b5c610240f329718c87f7e16d17bd2516924de629e44433cac0"),
)
SUPPORTED_INACTIVE14_METHOD = ObjectIdentity(METHOD.object_id,METHOD.object_schema,"1.1.0",
    sha256(canonical_json_bytes((SUPPORTED_INACTIVE14_DESCRIPTION,SUPPORTED_INACTIVE14_SOURCE_PINS))).hexdigest())


@dataclass(frozen=True, slots=True)
class SupportedInactive14Geometry:
    """Explicit successor method beside unchanged legacy diagnostic bytes."""

    method: ObjectIdentity
    diagnostic: GeometryDiagnostic

    def __post_init__(self):
        if self.method != SUPPORTED_INACTIVE14_METHOD or type(self.diagnostic) is not GeometryDiagnostic:
            raise ValueError("supported geometry requires its explicit method and complete diagnostic")
        self.diagnostic.__post_init__()


def diagnose_geometry_supported_inactive14(raw_prmtop,raw_inpcrd,heavy_pdb,origins):
    """Run unchanged complete geometry math with the supported raw census.

    The private namespace substitutes only the named additive census. It does
    not mutate module globals, original tables, origins or diagnostic fields.
    The explicit successor method prevents relabelling this as legacy method
    evidence. Original parameter/audit/origin custody belongs to the caller.
    """
    namespace = dict(diagnose_geometry.__globals__)
    namespace["assigned_census"] = assigned_census_supported_inactive14
    selected = FunctionType(diagnose_geometry.__code__,namespace,"diagnose_geometry_supported_inactive14")
    result = SupportedInactive14Geometry(SUPPORTED_INACTIVE14_METHOD,
        selected(raw_prmtop,raw_inpcrd,heavy_pdb,origins))
    result.__post_init__()
    return result


@dataclass(frozen=True,slots=True)
class ModelGeometry(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/model-geometry-diagnostic"
    model_id: str
    assets: ObjectIdentity
    assignment_disposition: A
    diagnostic_disposition: A
    reasons: tuple[str, ...]
    raw_inputs: tuple[c.FileEvidence, ...]
    diagnostic: GeometryDiagnostic | None

    def __post_init__(self):
        validate_stable_id(self.model_id)
        if type(self.assets) is not ObjectIdentity or type(self.assignment_disposition) is not A or type(self.diagnostic_disposition) is not A:
            raise ValueError("typed geometry source/dispositions required")
        self.assets.__post_init__()
        if type(self.raw_inputs) is not tuple or len(set(row.relative_path for row in self.raw_inputs)) != len(self.raw_inputs):
            raise ValueError("geometry raw input census duplicates or changes type")
        for evidence in self.raw_inputs:
            if type(evidence) is not c.FileEvidence or not _integer(evidence.byte_count):
                raise ValueError("geometry raw input requires exact typed byte counts")
            evidence.__post_init__()
        if self.diagnostic is not None:
            self.diagnostic.__post_init__()
            if self.diagnostic_disposition is not self.diagnostic.hard_geometry_disposition or len(self.raw_inputs) != 4:
                raise ValueError("complete geometry operands/disposition differ")
        elif self.diagnostic_disposition is A.SATISFIED:
            raise ValueError("positive mathematical diagnostic omits operands")


@dataclass(frozen=True,slots=True)
class PhysicalPreparationGeometry(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/physical-preparation-geometry"
    product_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    assignment_integrity: ObjectIdentity
    models: tuple[ModelGeometry, ...]
    method: ObjectIdentity = METHOD
    operator_source_pins: tuple[tuple[str,str], ...] = SOURCE_PINS
    geometry_adequacy: A = A.UNEVALUABLE
    native_coverage: A = A.UNEVALUABLE
    force_adequacy: A = A.UNEVALUABLE
    relaxation_adequacy: A = A.UNEVALUABLE
    actual_native_attempt_count: int | None = None
    actual_native_completion_count: int | None = None
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        expected = tuple("model."+".".join(row) for row in c.model_roster())
        if type(self.models) is not tuple or tuple(row.model_id for row in self.models) != expected:
            raise ValueError("physical preparation requires complete original24 model denominator")
        for identity in (self.source,self.preparation,self.assignment_integrity,self.method): identity.__post_init__()
        for row in self.models: row.__post_init__()
        if self.method != METHOD or self.operator_source_pins != SOURCE_PINS or any(value is not A.UNEVALUABLE for value in (self.geometry_adequacy,self.native_coverage,self.force_adequacy,self.relaxation_adequacy)) or self.actual_native_attempt_count is not None or self.actual_native_completion_count is not None or type(self.physical_independent_units) is not int or self.physical_independent_units != 0:
            raise ValueError("PURE geometry cannot supply native/physical admission")


def assess_geometry(source,preparation,assets,integrity):
    """Caller-authenticated complete24 custody; one model/pair workspace at a time."""
    source.__post_init__(); preparation.__post_init__(); integrity.__post_init__()
    if type(integrity) is not PreparationIntegrity or integrity.source != c.identity(source) or integrity.preparation != c.identity(preparation):
        raise ValueError("geometry substitutes original independent assignment/source")
    if len(assets) != 24 or tuple((row.construct_id,row.joint_view_id,row.parameter_view) for row in assets) != c.model_roster():
        raise ValueError("geometry substitutes complete24 assets")
    files = {row.relative_path:row for row in preparation.files}
    if len(files) != len(preparation.files):
        raise ValueError("geometry complete original file census duplicates paths")
    models = []
    for model,bundle,assignment in zip(preparation.models,assets,integrity.model_dispositions,strict=True):
        bundle.__post_init__(); model.__post_init__()
        if assignment[0] != model.model_id or assignment[1] is not model.disposition or model.assets != c.identity(bundle) or bundle.source != c.identity(source) or model.files != tuple(row.evidence for row in bundle.files) or any(files.get(row.evidence.relative_path) != row.evidence for row in bundle.files):
            raise ValueError("geometry original model/asset/assignment custody differs")
        available = {row.evidence.relative_path:row for row in bundle.files}
        required = tuple(model.model_id+"/"+name for name in ("model.prmtop","model.inpcrd","complete-heavy.pdb"))+(model.provenance_manifest_path,)
        raw = tuple(available[name].evidence for name in required if name in available)
        diagnostic = None
        if len(raw) != 4:
            disposition = A.NOT_ATTEMPTED if model.disposition is A.NOT_ATTEMPTED else A.UNEVALUABLE
            reasons = ("COMPLETE_RETAINED_GEOMETRY_INPUTS_UNAVAILABLE",)
        else:
            try:
                diagnostic = diagnose_geometry(*(available[name].raw_utf8 for name in required[:3]),json.loads(available[required[3]].raw_utf8))
                disposition = diagnostic.hard_geometry_disposition
                reasons = ("MATHEMATICAL_INPUT_DIAGNOSTIC_ONLY_PHYSICAL_ADEQUACY_UNASSESSED",)
            except UnsupportedGeometry as error:
                disposition,reasons = A.UNSUPPORTED,(str(error),)
            except (ValueError,ArithmeticError,TypeError,KeyError) as error:
                disposition,reasons = A.REFUSED,(str(error),)
        models.append(ModelGeometry(model.model_id,c.identity(bundle),assignment[1],disposition,reasons,raw,diagnostic))
    return PhysicalPreparationGeometry("product.rubisco-dynamics.physical-preparation-geometry",c.identity(source),c.identity(preparation),c.identity(integrity),tuple(models))
